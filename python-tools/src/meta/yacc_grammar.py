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
    true, false         -> boolean literals
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from .grammar import (
    Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence, Rule,
    GrammarConfig, TerminalDef
)
from .target import (
    TargetType, BaseType, BottomType, MessageType, ListType, OptionType, TupleType, DictType,
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, NewMessage, Call, Lambda,
    Let, IfElse, Seq, ListExpr, GetElement, GetField, FunDef, OneOf, Assign, Return, HasField
)


class YaccGrammarError(Exception):
    """Error during yacc grammar parsing."""
    def __init__(self, message: str, line: Optional[int] = None):
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
        self.line = line


@dataclass
class TerminalInfo:
    """Information about a terminal symbol."""
    type: TargetType
    pattern: Optional[str] = None
    is_regex: bool = True  # True for r'...' patterns, False for '...' literals


@dataclass
class TypeContext:
    """Context for looking up types of terminals and nonterminals."""
    terminals: Dict[str, TargetType] = field(default_factory=dict)
    terminal_info: Dict[str, TerminalInfo] = field(default_factory=dict)
    nonterminals: Dict[str, TargetType] = field(default_factory=dict)
    functions: Dict[str, FunDef] = field(default_factory=dict)


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


def _parse_token_pattern(rest: str) -> Tuple[str, Optional[str], bool]:
    """Parse type and optional pattern from %token directive.

    Args:
        rest: The part after '%token NAME', e.g. "Type r'pattern'" or "Type"

    Returns:
        (type_str, pattern, is_regex)
        pattern is None if not specified
        is_regex is True for r'...' patterns, False for '...' literals
    """
    rest = rest.strip()

    # Check for r'...' pattern (regex)
    regex_match = re.search(r"\s+r'([^']*)'$", rest)
    if regex_match:
        type_str = rest[:regex_match.start()].strip()
        pattern = regex_match.group(1)
        return type_str, pattern, True

    # Check for '...' pattern (fixed string)
    literal_match = re.search(r"\s+'([^']*)'$", rest)
    if literal_match:
        type_str = rest[:literal_match.start()].strip()
        pattern = literal_match.group(1)
        return type_str, pattern, False

    # No pattern
    return rest, None, True


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
            return ctx, ignored_completeness, i

        # Parse directive
        if line.startswith('%token'):
            rest = line[6:].strip()
            # Split name from type+pattern
            space_idx = rest.find(' ')
            if space_idx == -1:
                raise YaccGrammarError(f"Invalid %token directive: {line}", i)
            name = rest[:space_idx]
            type_and_pattern = rest[space_idx+1:]
            type_str, pattern, is_regex = _parse_token_pattern(type_and_pattern)
            ctx.terminals[name] = parse_type(type_str)
            ctx.terminal_info[name] = TerminalInfo(parse_type(type_str), pattern, is_regex)

        elif line.startswith('%nonterm'):
            parts = line[8:].strip().split(None, 1)
            if len(parts) != 2:
                raise YaccGrammarError(f"Invalid %nonterm directive: {line}", i)
            name, type_str = parts
            ctx.nonterminals[name] = parse_type(type_str)

        elif line.startswith('%type'):
            # Support %type as alias for %nonterm for backwards compatibility
            parts = line[5:].strip().split(None, 1)
            if len(parts) != 2:
                raise YaccGrammarError(f"Invalid %type directive: {line}", i)
            name, type_str = parts
            ctx.nonterminals[name] = parse_type(type_str)

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


def python_ast_to_target(node: ast.AST, rhs: Rhs, ctx: TypeContext, line: Optional[int] = None) -> TargetExpr:
    """Convert a Python AST node to a target expression.

    Args:
        node: Python AST node
        rhs: The RHS of the rule (for $N references)
        ctx: Type context
        line: Line number for error messages
    """
    # Build parameter types from RHS
    param_types = _get_rhs_param_types(rhs)

    def convert(n: ast.AST) -> TargetExpr:
        return _convert_node(n, param_types, ctx, line)

    return convert(node)


def _get_rhs_element_name(elem: Rhs) -> Optional[str]:
    """Get the name of an RHS element for use as a parameter name.

    Returns the symbol name for terminals and nonterminals, unwrapping
    Star and Option wrappers. Returns None for literals.
    """
    if isinstance(elem, LitTerminal):
        return None
    elif isinstance(elem, NamedTerminal):
        return elem.name.lower()  # e.g., SYMBOL -> symbol
    elif isinstance(elem, Nonterminal):
        return elem.name
    elif isinstance(elem, Star):
        # Use plural form of the inner element name
        inner_name = _get_rhs_element_name(elem.rhs)
        if inner_name:
            return inner_name + "s" if not inner_name.endswith("s") else inner_name
        return None
    elif isinstance(elem, Option):
        return _get_rhs_element_name(elem.rhs)
    else:
        return None


def _get_rhs_param_info(rhs: Rhs) -> List[Tuple[Optional[str], Optional[TargetType]]]:
    """Get parameter names and types from an RHS.

    Returns a list of (name, type) tuples, one per RHS element.
    Literals are represented as (None, None).
    """
    if isinstance(rhs, Sequence):
        result: List[Tuple[Optional[str], Optional[TargetType]]] = []
        for elem in rhs.elements:
            if isinstance(elem, LitTerminal):
                result.append((None, None))
            else:
                result.append((_get_rhs_element_name(elem), elem.target_type()))
        return result
    elif isinstance(rhs, LitTerminal):
        return [(None, None)]
    else:
        return [(_get_rhs_element_name(rhs), rhs.target_type())]


def _get_rhs_param_types(rhs: Rhs) -> List[Optional[TargetType]]:
    """Get the types of parameters from an RHS (including literals as None).

    Returns a list with one entry per RHS element. Literals are represented
    as None since they cannot be meaningfully referenced in actions.
    """
    return [t for _, t in _get_rhs_param_info(rhs)]


def _convert_node(node: ast.AST, param_types: List[Optional[TargetType]], ctx: TypeContext, line: Optional[int]) -> TargetExpr:
    """Convert a single AST node."""

    if isinstance(node, ast.Constant):
        return Lit(node.value)

    elif isinstance(node, ast.Name):
        name = node.id
        # Handle special names
        if name == 'true':
            return Lit(True)
        elif name == 'false':
            return Lit(False)
        # Handle $N references (stored as _dollar_N during preprocessing)
        if name.startswith('_dollar_'):
            idx = int(name[8:]) - 1  # Convert 1-indexed to 0-indexed
            if idx < 0 or idx >= len(param_types):
                raise YaccGrammarError(f"Invalid parameter reference ${idx+1}, only {len(param_types)} parameters", line)
            param_type = param_types[idx]
            if param_type is None:
                raise YaccGrammarError(f"Cannot reference literal at position ${idx+1}", line)
            return Var(f"_{idx}", param_type)
        # Check if it's a known function
        if name in ctx.functions:
            return NamedFun(name)
        # Otherwise it's a variable reference - we need to determine its type from context
        # For now, treat as unknown
        raise YaccGrammarError(f"Unknown variable: {name}", line)

    elif isinstance(node, ast.Subscript):
        # Handle $N[i] for tuple access
        value = _convert_node(node.value, param_types, ctx, line)
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return GetElement(value, node.slice.value)
        raise YaccGrammarError(f"Subscript must use integer literal index", line)

    elif isinstance(node, ast.Attribute):
        # Handle module.Message or obj.field
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            attr_name = node.attr
            # Check if it's a message type constructor
            msg_type = MessageType(module_name, attr_name)
            # Return a reference that will be used in Call
            return NewMessage(module_name, attr_name, ())
        else:
            # Field access
            obj = _convert_node(node.value, param_types, ctx, line)
            raise YaccGrammarError(f"Field access not yet supported: {ast.dump(node)}", line)

    elif isinstance(node, ast.Call):
        func = node.func
        args = [_convert_node(a, param_types, ctx, line) for a in node.args]

        # Handle message constructor: module.Message(field=value, ...)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_name = func.value.id
            msg_name = func.attr
            # Extract keyword arguments
            fields = []
            for kw in node.keywords:
                if kw.arg is None:
                    raise YaccGrammarError(f"**kwargs not supported in message constructor", line)
                field_name = kw.arg
                # Restore original field name if it was escaped
                if field_name.startswith('_kw_') and field_name.endswith('_'):
                    field_name = field_name[4:-1]
                field_expr = _convert_node(kw.value, param_types, ctx, line)
                fields.append((field_name, field_expr))
            return NewMessage(module_name, msg_name, tuple(fields))

        # Handle regular function call
        if isinstance(func, ast.Name):
            func_name = func.id
            # Check for oneof_VARIANT pattern
            if func_name.startswith('oneof_'):
                variant_name = func_name[6:]  # Remove 'oneof_' prefix
                return Call(OneOf(variant_name), args)
            # has_field(msg, field_name) -> HasField node
            if func_name == 'has_field':
                if len(args) != 2:
                    raise YaccGrammarError(f"has_field requires exactly 2 arguments", line)
                if not isinstance(args[1], Lit) or not isinstance(args[1].value, str):
                    raise YaccGrammarError(f"has_field second argument must be a string literal", line)
                return HasField(args[0], args[1].value)
            # Check if it's a builtin
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(Builtin(func_name), args)
            # Check if it's a user-defined function
            if func_name in ctx.functions:
                return Call(NamedFun(func_name), args)
            raise YaccGrammarError(f"Unknown function: {func_name}", line)

        func_expr = _convert_node(func, param_types, ctx, line)
        return Call(func_expr, args)

    elif isinstance(node, ast.List):
        if not node.elts:
            # Empty list - need element type from context
            raise YaccGrammarError(f"Empty list literal needs type annotation", line)
        elements = [_convert_node(e, param_types, ctx, line) for e in node.elts]
        # Infer element type from first element
        return ListExpr(elements, _infer_type(elements[0], line, ctx))

    elif isinstance(node, ast.BinOp):
        raise YaccGrammarError(f"Binary operations not supported: {ast.dump(node)}", line)

    elif isinstance(node, ast.Compare):
        raise YaccGrammarError(f"Comparison not supported: {ast.dump(node)}", line)

    elif isinstance(node, ast.IfExp):
        cond = _convert_node(node.test, param_types, ctx, line)
        then_branch = _convert_node(node.body, param_types, ctx, line)
        else_branch = _convert_node(node.orelse, param_types, ctx, line)
        return IfElse(cond, then_branch, else_branch)

    else:
        raise YaccGrammarError(f"Unsupported Python AST node: {type(node).__name__}: {ast.dump(node)}", line)


def _infer_type(expr: TargetExpr, line: Optional[int] = None,
                ctx: Optional['TypeContext'] = None) -> TargetType:
    """Infer the type of an expression.

    Args:
        expr: The expression to infer the type of
        line: Line number for error messages
        ctx: Type context for looking up function return types

    Raises YaccGrammarError if type cannot be inferred.
    """
    if isinstance(expr, Var):
        return expr.type
    elif isinstance(expr, Lit):
        if isinstance(expr.value, int):
            return BaseType("Int64")
        elif isinstance(expr.value, float):
            return BaseType("Float64")
        elif isinstance(expr.value, str):
            return BaseType("String")
        elif isinstance(expr.value, bool):
            return BaseType("Boolean")
        elif expr.value is None:
            # None literal has type Optional[Bottom]
            # With covariance: Optional[Bottom] <: Optional[T] for any T
            return OptionType(BottomType())
        raise YaccGrammarError(f"Cannot infer type of literal: {expr.value!r}", line)
    elif isinstance(expr, NewMessage):
        return MessageType(expr.module, expr.name)
    elif isinstance(expr, ListExpr):
        return ListType(expr.element_type)
    elif isinstance(expr, GetElement):
        # Infer tuple element type
        tuple_type = _infer_type(expr.tuple_expr, line, ctx)
        if isinstance(tuple_type, TupleType) and 0 <= expr.index < len(tuple_type.elements):
            return tuple_type.elements[expr.index]
        raise YaccGrammarError(f"Cannot infer type of tuple element access: {expr}", line)
    elif isinstance(expr, GetField):
        # GetField accesses a field from a message - we can't know the type without proto schema
        # Return Any since the context (function return type) will provide the actual type
        return BaseType("Any")
    elif isinstance(expr, Let):
        # Let expression has the type of its body
        return _infer_type(expr.body, line, ctx)
    elif isinstance(expr, IfElse):
        # Conditional has the type of its branches (assume they're the same)
        return _infer_type(expr.then_branch, line, ctx)
    elif isinstance(expr, Seq):
        # Sequence has the type of its last expression
        if expr.exprs:
            return _infer_type(expr.exprs[-1], line, ctx)
        raise YaccGrammarError("Cannot infer type of empty sequence", line)
    elif isinstance(expr, Call):
        # Try to infer return type from the called function
        if isinstance(expr.func, NamedFun):
            # User-defined function - look up return type
            if ctx is not None and expr.func.name in ctx.functions:
                func_def = ctx.functions[expr.func.name]
                if func_def is not None:
                    return func_def.return_type
        # For builtins or unknown functions, return Any
        return BaseType("Any")
    raise YaccGrammarError(f"Cannot infer type of expression: {type(expr).__name__}", line)


# Python keywords that might be used as field names in the grammar
PYTHON_KEYWORDS = {'def', 'class', 'return', 'if', 'else', 'for', 'while', 'with',
                   'try', 'except', 'finally', 'import', 'from', 'as', 'pass',
                   'break', 'continue', 'raise', 'yield', 'global', 'nonlocal',
                   'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None'}


def preprocess_action(text: str) -> str:
    """Preprocess action text to make it valid Python.

    Transforms:
        $1, $2, ... -> _dollar_1, _dollar_2, ...
        keyword=expr -> _kw_keyword_=expr (for Python keywords used as field names)
    """
    # Replace $N with _dollar_N
    result = re.sub(r'\$(\d+)', r'_dollar_\1', text)
    # Replace keyword= with _kw_keyword_= for Python keywords used as kwargs
    for kw in PYTHON_KEYWORDS:
        result = re.sub(rf'\b{kw}=', f'_kw_{kw}_=', result)
    return result


def parse_action(text: str, rhs: Rhs, ctx: TypeContext, line: Optional[int] = None,
                 expected_return_type: Optional[TargetType] = None) -> Lambda:
    """Parse a semantic action and return a Lambda.

    Args:
        text: Action text (Python expression)
        rhs: The RHS of the rule
        ctx: Type context
        line: Line number for error messages
        expected_return_type: The expected return type from the LHS %type declaration

    Returns:
        Lambda expression representing the action
    """
    # Preprocess to handle $N references and Python keyword escaping
    preprocessed = preprocess_action(text.strip())

    # Build parameter list with names from RHS symbols
    params = _build_params(rhs)

    # Parse the expression
    # Pass param info so $N references can be resolved to named parameters
    param_info = _get_rhs_param_info(rhs)
    body = parse_action_expr(preprocessed, param_info, params, ctx, line)

    # Use expected return type from %type declaration if provided, otherwise infer
    return_type = expected_return_type if expected_return_type is not None else _infer_type(body, line, ctx)
    return Lambda(params, return_type, body)


def parse_action_expr(text: str, param_info: List[Tuple[Optional[str], Optional[TargetType]]],
                      params: List[Var], ctx: TypeContext,
                      line: Optional[int], extra_vars: Optional[Dict[str, TargetType]] = None) -> TargetExpr:
    """Parse an action expression.

    Args:
        text: The expression text to parse
        param_info: List of (name, type) for each RHS element (None for literals)
        params: The actual parameter Vars (non-literal elements only)
        ctx: Type context for looking up functions
        line: Line number for error messages
        extra_vars: Additional variables in scope
    """
    text = text.strip()
    extra_vars = extra_vars or {}

    # Parse as Python expression
    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError as e:
        raise YaccGrammarError(f"Syntax error in action: {e}", line)

    return _convert_node_with_vars(tree.body, param_info, params, ctx, line, extra_vars)


def _unsupported_node_error(node: ast.AST, line: Optional[int], reason: str = "") -> YaccGrammarError:
    """Create an error for unsupported Python syntax with helpful diagnostics."""
    node_type = type(node).__name__

    # Map AST node types to user-friendly descriptions and suggestions
    node_explanations = {
        'UnaryOp': "Unary operators (like -x, +x, ~x, not x) are not supported. "
                   "Use builtin functions instead (e.g., 'subtract(0, x)' for negation).",
        'BinOp': "Binary operators (+, -, *, /, etc.) are not supported. "
                 "Use builtin functions instead (e.g., 'add(x, y)', 'multiply(x, y)').",
        'BoolOp': "Boolean operators (and, or) are not supported directly. "
                  "Use builtin functions instead (e.g., 'and(x, y)', 'or(x, y)').",
        'Compare': "Comparison operators (==, !=, <, >, etc.) are not supported. "
                   "Use builtin functions instead (e.g., 'equal(x, y)', 'less_than(x, y)').",
        'Lambda': "Python lambda expressions are not supported in actions. "
                  "Define named functions in the %functions section instead.",
        'Dict': "Dictionary literals are not supported. "
                "Use 'dict(pairs)' with a list of tuples instead.",
        'Set': "Set literals are not supported.",
        'ListComp': "List comprehensions are not supported. "
                    "Use explicit loops or map() instead.",
        'DictComp': "Dictionary comprehensions are not supported.",
        'SetComp': "Set comprehensions are not supported.",
        'GeneratorExp': "Generator expressions are not supported.",
        'Await': "Async/await is not supported.",
        'Yield': "Yield expressions are not supported.",
        'YieldFrom': "Yield from expressions are not supported.",
        'FormattedValue': "F-string formatting is not supported. "
                          "Use string_concat() for string building.",
        'JoinedStr': "F-strings are not supported. Use string_concat() instead.",
        'Starred': "Starred expressions (*args) are not supported.",
        'Slice': "Slice expressions (x[a:b]) are not supported. "
                 "Only constant integer indexing is allowed.",
        'NamedExpr': "Walrus operator (:=) is not supported.",
        'Tuple': "Tuple literals are not directly supported. "
                 "Use tuple(a, b, ...) builtin instead.",
    }

    base_msg = f"Cannot convert Python '{node_type}' to target IR"
    if reason:
        base_msg += f": {reason}"

    explanation = node_explanations.get(node_type, "")
    if explanation:
        base_msg += f"\n  {explanation}"

    base_msg += ("\n\n  Note: Action expressions use a restricted subset of Python that can be "
                 "translated to Julia and Go.\n  Supported constructs: literals, variables, "
                 "function calls, message constructors,\n  list literals, conditional expressions "
                 "(x if cond else y), and tuple indexing (x[0]).")

    return YaccGrammarError(base_msg, line)


def _convert_node_with_vars(node: ast.AST, param_info: List[Tuple[Optional[str], Optional[TargetType]]],
                            params: List[Var], ctx: TypeContext,
                            line: Optional[int], extra_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert AST node with extra variable bindings.

    This function translates Python AST nodes into target IR expressions.
    Only a restricted subset of Python is supported because the IR must be
    translatable to multiple target languages (Python, Julia, Go).

    Args:
        node: The AST node to convert
        param_info: List of (name, type) for each RHS element (None for literals)
        params: The actual parameter Vars (non-literal elements only)
        ctx: Type context for looking up functions
        line: Line number for error messages
        extra_vars: Additional variables in scope
    """

    def convert(n: ast.AST) -> TargetExpr:
        return _convert_node_with_vars(n, param_info, params, ctx, line, extra_vars)

    if isinstance(node, ast.Constant):
        return Lit(node.value)

    elif isinstance(node, ast.Name):
        name = node.id
        if name == 'true':
            return Lit(True)
        elif name == 'false':
            return Lit(False)
        elif name.startswith('_dollar_'):
            # $N reference - map to the corresponding parameter
            idx = int(name[8:]) - 1  # Convert 1-indexed to 0-indexed
            if idx < 0 or idx >= len(param_info):
                raise YaccGrammarError(f"Invalid parameter reference ${idx+1}", line)
            _, param_type = param_info[idx]
            if param_type is None:
                raise YaccGrammarError(f"Cannot reference literal at position ${idx+1}", line)
            # Find the parameter for this position (skipping literals)
            param_idx = sum(1 for _, t in param_info[:idx] if t is not None)
            return params[param_idx]
        elif name in extra_vars:
            return Var(name, extra_vars[name])
        elif name in ctx.functions:
            return NamedFun(name)
        else:
            # Check builtins
            from .target_builtins import is_builtin
            if is_builtin(name):
                return Builtin(name)
            raise YaccGrammarError(
                f"Unknown variable or function: '{name}'\n"
                f"  Functions must be defined in the helper functions section or be builtins.",
                line)

    elif isinstance(node, ast.Subscript):
        value = convert(node.value)
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return GetElement(value, node.slice.value)
        raise YaccGrammarError(
            f"Subscript must use integer literal index (e.g., x[0], x[1]).\n"
            f"  Dynamic indexing and slices are not supported.",
            line)

    elif isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            # module.Message reference
            return NewMessage(node.value.id, node.attr, ())
        raise YaccGrammarError(
            f"Field access on expressions is not supported.\n"
            f"  Only 'module.MessageName' for message constructors is allowed.\n"
            f"  Use GetField in target IR for field access on messages.",
            line)

    elif isinstance(node, ast.Call):
        func = node.func
        args = [convert(a) for a in node.args]

        # Message constructor
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_name = func.value.id
            msg_name = func.attr
            fields = []
            for kw in node.keywords:
                if kw.arg is None:
                    raise YaccGrammarError(
                        f"**kwargs syntax is not supported in message constructors.\n"
                        f"  Use explicit keyword arguments: module.Msg(field1=val1, field2=val2)",
                        line)
                field_name = kw.arg
                # Restore original field name if it was escaped
                if field_name.startswith('_kw_') and field_name.endswith('_'):
                    field_name = field_name[4:-1]
                field_expr = convert(kw.value)
                fields.append((field_name, field_expr))
            return NewMessage(module_name, msg_name, tuple(fields))

        # Function call
        if isinstance(func, ast.Name):
            func_name = func.id
            # Handle special forms
            if func_name == 'seq':
                return Seq(args)
            # Check for oneof_VARIANT pattern
            if func_name.startswith('oneof_'):
                variant_name = func_name[6:]  # Remove 'oneof_' prefix
                return Call(OneOf(variant_name), args)
            # has_field(msg, field_name) -> HasField node
            if func_name == 'has_field':
                if len(args) != 2:
                    raise YaccGrammarError(f"has_field requires exactly 2 arguments", line)
                if not isinstance(args[1], Lit) or not isinstance(args[1].value, str):
                    raise YaccGrammarError(f"has_field second argument must be a string literal", line)
                return HasField(args[0], args[1].value)
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(Builtin(func_name), args)
            if func_name in ctx.functions:
                return Call(NamedFun(func_name), args)
            raise YaccGrammarError(
                f"Unknown function: '{func_name}'\n"
                f"  Functions must be either:\n"
                f"    - Builtins (see target_builtins.py for available builtins)\n"
                f"    - Defined in the %functions section of the grammar\n"
                f"  Note: Python standard library functions are not available.",
                line)

        func_expr = convert(func)
        return Call(func_expr, args)

    elif isinstance(node, ast.List):
        elements = [convert(e) for e in node.elts]
        if elements:
            elem_type = _infer_type(elements[0], line, ctx)
        else:
            # Empty list has type List[Bottom]
            # With covariance: List[Bottom] <: List[T] for any T
            elem_type = BottomType()
        return ListExpr(elements, elem_type)

    elif isinstance(node, ast.IfExp):
        cond = convert(node.test)
        then_branch = convert(node.body)
        else_branch = convert(node.orelse)
        return IfElse(cond, then_branch, else_branch)

    else:
        raise _unsupported_node_error(node, line)


def _build_params(rhs: Rhs) -> List[Var]:
    """Build parameter list from RHS (non-literal elements only).

    Uses the symbol name from the RHS element as the parameter name.
    For example, a rule like:
        transaction : "(" "transaction" configure? sync? epoch* ")"
    will produce parameters named: configure, sync, epochs
    with types: Optional[...], Optional[...], List[...]
    """
    param_info = _get_rhs_param_info(rhs)
    params = []
    used_names: Set[str] = set()
    for i, (name, t) in enumerate(param_info):
        if t is not None:
            # Use the element name, or fall back to positional name
            param_name = name if name else f"_{i}"
            # Handle duplicate names by appending index
            if param_name in used_names:
                param_name = f"{param_name}_{i}"
            used_names.add(param_name)
            params.append(Var(param_name, t))
    return params


def parse_rules(lines: List[str], start_line: int, ctx: TypeContext) -> Tuple[List[Rule], int]:
    """Parse rules section until %%.

    Returns:
        (rules, end_line_index)
    """
    rules: List[Rule] = []
    i = 0
    current_lhs: Optional[str] = None
    current_lhs_type: Optional[TargetType] = None
    current_alt_lines: List[str] = []  # Accumulate lines for current alternative
    current_alt_start_line: int = 0

    def flush_alternative():
        """Process accumulated alternative lines."""
        nonlocal current_alt_lines
        if current_alt_lines and current_lhs is not None and current_lhs_type is not None:
            text = ' '.join(current_alt_lines)
            rule = _parse_alternative(current_lhs, current_lhs_type, text, ctx, current_alt_start_line)
            rules.append(rule)
        current_alt_lines = []

    while i < len(lines):
        line = lines[i]
        line_num = start_line + i
        stripped = line.strip()
        i += 1

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        # Check for section separator
        if stripped == '%%':
            flush_alternative()
            return rules, i

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
                    current_alt_lines = [rest]
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
                current_alt_lines = [rest]
                current_alt_start_line = line_num

        elif line and line[0].isspace() and current_alt_lines:
            # Continuation of current alternative (indented line)
            current_alt_lines.append(stripped)

        else:
            raise YaccGrammarError(f"Unexpected line in rules section: {stripped}", line_num)

    raise YaccGrammarError("Unexpected end of file, expected %%")


def _find_action_braces(text: str) -> Tuple[int, int]:
    """Find the action braces in rule text, ignoring braces inside string literals.

    Returns (brace_start, brace_end) indices, or (-1, -1) if not found.
    """
    i = 0
    while i < len(text):
        c = text[i]
        if c == '"':
            # Skip string literal
            i += 1
            while i < len(text) and text[i] != '"':
                if text[i] == '\\':
                    i += 2
                else:
                    i += 1
            i += 1  # Skip closing quote
        elif c == '{':
            # Found the action start
            brace_start = i
            # Find matching close brace
            depth = 1
            i += 1
            while i < len(text) and depth > 0:
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                elif text[i] == '"':
                    # Skip string literal inside action
                    i += 1
                    while i < len(text) and text[i] != '"':
                        if text[i] == '\\':
                            i += 2
                        else:
                            i += 1
                i += 1
            if depth == 0:
                return brace_start, i - 1
            return brace_start, -1
        else:
            i += 1
    return -1, -1


def _parse_alternative(lhs_name: str, lhs_type: TargetType, text: str,
                       ctx: TypeContext, line: int) -> Rule:
    """Parse a single rule alternative.

    Format: rhs { action }
    """
    # Find the action in braces, skipping string literals
    brace_start, brace_end = _find_action_braces(text)
    if brace_start == -1:
        raise YaccGrammarError(f"Missing action in rule: {text}", line)
    if brace_end == -1:
        raise YaccGrammarError(f"Unbalanced braces in rule: {text}", line)

    rhs_text = text[:brace_start].strip()
    action_text = text[brace_start+1:brace_end].strip()

    # Parse RHS
    rhs = parse_rhs(rhs_text, ctx)

    # Parse action, using LHS type as expected return type
    constructor = parse_action(action_text, rhs, ctx, line, expected_return_type=lhs_type)

    lhs = Nonterminal(lhs_name, lhs_type)
    return Rule(lhs=lhs, rhs=rhs, constructor=constructor)


def parse_helper_functions(lines: List[str], start_line: int, ctx: TypeContext) -> Dict[str, FunDef]:
    """Parse helper functions section (Python code).

    Returns:
        Dictionary of function name -> FunDef
    """
    # Join lines into text
    text = '\n'.join(lines)

    if not text.strip():
        return {}

    # Parse as Python module
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise YaccGrammarError(f"Syntax error in helper functions: {e}", start_line + (e.lineno or 1))

    # Two-pass approach: first collect all function signatures, then convert bodies
    # This allows functions to call each other without forward declaration issues

    # Pass 1: Collect function signatures
    func_nodes: List[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_nodes.append(node)
            # Add function name to context so other functions can reference it
            ctx.functions[node.name] = None  # type: ignore

    # Pass 2: Convert function bodies
    functions: Dict[str, FunDef] = {}
    for node in func_nodes:
        func_def = _convert_function_def(node, ctx, start_line)
        functions[func_def.name] = func_def

    return functions


def _convert_function_def(node: ast.FunctionDef, ctx: TypeContext, base_line: int) -> FunDef:
    """Convert a Python function definition to FunDef."""
    name = node.name

    # Parse parameters with type annotations
    params = []
    param_vars: Dict[str, TargetType] = {}
    for arg in node.args.args:
        param_name = arg.arg
        if arg.annotation is None:
            raise YaccGrammarError(f"Parameter {param_name} in {name} missing type annotation",
                                   base_line + node.lineno)
        param_type = _annotation_to_type(arg.annotation, base_line + node.lineno)
        params.append(Var(param_name, param_type))
        param_vars[param_name] = param_type

    # Parse return type
    if node.returns is None:
        raise YaccGrammarError(f"Function {name} missing return type annotation",
                               base_line + node.lineno)
    return_type = _annotation_to_type(node.returns, base_line + node.lineno)

    # Convert function body statements to target IR
    body = _convert_function_body(node.body, ctx, base_line + node.lineno, param_vars)

    return FunDef(name, tuple(params), return_type, body)


def _convert_function_body(stmts: List[ast.stmt], ctx: TypeContext, line: int,
                           local_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert a list of Python statements to target IR.

    Returns a Seq of converted statements.
    """
    converted = []
    for stmt in stmts:
        converted.append(_convert_stmt(stmt, ctx, line, local_vars))
    if len(converted) == 1:
        return converted[0]
    return Seq(tuple(converted))


def _convert_stmt(stmt: ast.stmt, ctx: TypeContext, line: int,
                  local_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert a single Python statement to target IR."""
    if isinstance(stmt, ast.Return):
        if stmt.value is None:
            return Return(Lit(None))
        return Return(_convert_func_expr(stmt.value, ctx, line, local_vars))

    elif isinstance(stmt, ast.If):
        cond = _convert_func_expr(stmt.test, ctx, line, local_vars)
        then_body = _convert_function_body(stmt.body, ctx, line, local_vars)
        if stmt.orelse:
            else_body = _convert_function_body(stmt.orelse, ctx, line, local_vars)
        else:
            else_body = Lit(None)
        return IfElse(cond, then_body, else_body)

    elif isinstance(stmt, ast.Assign):
        # Simple assignment: x = expr
        if len(stmt.targets) != 1:
            raise YaccGrammarError(f"Multiple assignment targets not supported", line)
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            raise YaccGrammarError(f"Only simple variable assignment supported", line)
        var_name = target.id
        value = _convert_func_expr(stmt.value, ctx, line, local_vars)
        var_type = _infer_type(value, line, ctx)
        local_vars[var_name] = var_type
        return Assign(Var(var_name, var_type), value)

    elif isinstance(stmt, ast.AnnAssign):
        # Annotated assignment: x: Type = expr
        if not isinstance(stmt.target, ast.Name):
            raise YaccGrammarError(f"Only simple variable assignment supported", line)
        var_name = stmt.target.id
        var_type = _annotation_to_type(stmt.annotation, line)
        local_vars[var_name] = var_type
        if stmt.value is None:
            # Declaration without initialization - use None
            return Assign(Var(var_name, var_type), Lit(None))
        value = _convert_func_expr(stmt.value, ctx, line, local_vars)
        return Assign(Var(var_name, var_type), value)

    elif isinstance(stmt, ast.Expr):
        # Expression statement (e.g., function call with side effects)
        return _convert_func_expr(stmt.value, ctx, line, local_vars)

    else:
        raise YaccGrammarError(f"Unsupported statement type: {type(stmt).__name__}", line)


def _convert_func_expr(node: ast.expr, ctx: TypeContext, line: int,
                       local_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert a Python expression in a function body to target IR."""
    if isinstance(node, ast.Constant):
        return Lit(node.value)

    elif isinstance(node, ast.Name):
        name = node.id
        if name == 'true':
            return Lit(True)
        elif name == 'false':
            return Lit(False)
        elif name == 'None':
            return Lit(None)
        elif name in local_vars:
            return Var(name, local_vars[name])
        elif name in ctx.functions:
            return NamedFun(name)
        else:
            from .target_builtins import is_builtin
            if is_builtin(name):
                return Builtin(name)
            raise YaccGrammarError(f"Unknown variable: {name}", line)

    elif isinstance(node, ast.Attribute):
        # Handle module.Message or obj.field
        if isinstance(node.value, ast.Name):
            # Could be module.Message constructor or local_var.field
            if node.value.id in local_vars:
                # Field access on a variable
                obj = Var(node.value.id, local_vars[node.value.id])
                from .target import GetField
                return GetField(obj, node.attr)
            else:
                # Assume it's a message constructor reference
                return NewMessage(node.value.id, node.attr, ())
        else:
            # Field access on a more complex expression
            obj = _convert_func_expr(node.value, ctx, line, local_vars)
            from .target import GetField
            return GetField(obj, node.attr)

    elif isinstance(node, ast.Call):
        func = node.func
        args = [_convert_func_expr(a, ctx, line, local_vars) for a in node.args]

        # Handle message constructor or method call: module.Message(field=value, ...) or obj.method(args)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            obj_name = func.value.id
            method_name = func.attr
            # Check if obj_name is a local variable (method call)
            if obj_name in local_vars:
                # Method call: obj.method(args)
                obj = Var(obj_name, local_vars[obj_name])
                from .target import GetField
                method_ref = GetField(obj, method_name)
                return Call(method_ref, args)
            else:
                # Message constructor
                fields = []
                for kw in node.keywords:
                    if kw.arg is None:
                        raise YaccGrammarError(f"**kwargs not supported", line)
                    field_expr = _convert_func_expr(kw.value, ctx, line, local_vars)
                    fields.append((kw.arg, field_expr))
                return NewMessage(obj_name, method_name, tuple(fields))

        # Handle regular function call
        if isinstance(func, ast.Name):
            func_name = func.id
            # Check for dict() builtin
            if func_name == 'dict':
                from .target import DictFromList
                if len(args) == 1:
                    # Infer key/value types from argument type
                    arg_type = _infer_type(args[0], line, ctx)
                    if isinstance(arg_type, ListType) and isinstance(arg_type.element_type, TupleType):
                        tuple_elems = arg_type.element_type.elements
                        if len(tuple_elems) >= 2:
                            return DictFromList(args[0], tuple_elems[0], tuple_elems[1])
                    # Fall back to Any types when we can't determine precise types
                    return DictFromList(args[0], BaseType("Any"), BaseType("Any"))
                raise YaccGrammarError(f"dict() requires exactly one argument", line)
            # User-defined functions take precedence over builtins
            if func_name in ctx.functions:
                return Call(NamedFun(func_name), args)
            # has_field(msg, field_name) -> HasField node
            if func_name == 'has_field':
                if len(args) != 2:
                    raise YaccGrammarError(f"has_field requires exactly 2 arguments", line)
                if not isinstance(args[1], Lit) or not isinstance(args[1].value, str):
                    raise YaccGrammarError(f"has_field second argument must be a string literal", line)
                return HasField(args[0], args[1].value)
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(Builtin(func_name), args)
            raise YaccGrammarError(f"Unknown function: {func_name}", line)

        func_expr = _convert_func_expr(func, ctx, line, local_vars)
        return Call(func_expr, args)

    elif isinstance(node, ast.List):
        elements = [_convert_func_expr(e, ctx, line, local_vars) for e in node.elts]
        if elements:
            elem_type = _infer_type(elements[0], line, ctx)
        else:
            # Empty list has type List[Bottom]
            # With covariance: List[Bottom] <: List[T] for any T
            elem_type = BottomType()
        return ListExpr(elements, elem_type)

    elif isinstance(node, ast.IfExp):
        cond = _convert_func_expr(node.test, ctx, line, local_vars)
        then_branch = _convert_func_expr(node.body, ctx, line, local_vars)
        else_branch = _convert_func_expr(node.orelse, ctx, line, local_vars)
        return IfElse(cond, then_branch, else_branch)

    elif isinstance(node, ast.Compare):
        # Handle comparisons: x is None, x is not None, x == y, x in y
        if len(node.ops) == 1 and len(node.comparators) == 1:
            left = _convert_func_expr(node.left, ctx, line, local_vars)
            right = _convert_func_expr(node.comparators[0], ctx, line, local_vars)
            op = node.ops[0]
            if isinstance(op, ast.Is):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    return Call(Builtin("is_none"), [left])
                return Call(Builtin("equal"), [left, right])
            elif isinstance(op, ast.IsNot):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    return Call(Builtin("is_some"), [left])
                return Call(Builtin("not_equal"), [left, right])
            elif isinstance(op, ast.Eq):
                return Call(Builtin("equal"), [left, right])
            elif isinstance(op, ast.NotEq):
                return Call(Builtin("not_equal"), [left, right])
            elif isinstance(op, ast.In):
                return Call(Builtin("string_in_list"), [left, right])
            elif isinstance(op, ast.NotIn):
                return Call(Builtin("not"), [Call(Builtin("string_in_list"), [left, right])])
        raise YaccGrammarError(f"Unsupported comparison: {ast.dump(node)}", line)

    elif isinstance(node, ast.BoolOp):
        # Handle 'and' and 'or'
        if isinstance(node.op, ast.And):
            result = _convert_func_expr(node.values[0], ctx, line, local_vars)
            for val in node.values[1:]:
                result = Call(Builtin("and"), [result, _convert_func_expr(val, ctx, line, local_vars)])
            return result
        elif isinstance(node.op, ast.Or):
            result = _convert_func_expr(node.values[0], ctx, line, local_vars)
            for val in node.values[1:]:
                result = Call(Builtin("or"), [result, _convert_func_expr(val, ctx, line, local_vars)])
            return result
        raise YaccGrammarError(f"Unsupported boolean operation", line)

    elif isinstance(node, ast.BinOp):
        left = _convert_func_expr(node.left, ctx, line, local_vars)
        right = _convert_func_expr(node.right, ctx, line, local_vars)
        if isinstance(node.op, ast.Add):
            # Could be numeric add or string concat - use string_concat for strings
            return Call(Builtin("string_concat"), [left, right])
        raise YaccGrammarError(f"Unsupported binary operation: {type(node.op).__name__}", line)

    elif isinstance(node, ast.Subscript):
        # Handle dict.get() result or tuple indexing
        value = _convert_func_expr(node.value, ctx, line, local_vars)
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return GetElement(value, node.slice.value)
        raise YaccGrammarError(f"Only constant integer subscripts supported", line)

    else:
        raise YaccGrammarError(f"Unsupported expression type: {type(node).__name__}: {ast.dump(node)}", line)


def _annotation_to_type(node: ast.AST, line: int) -> TargetType:
    """Convert a Python type annotation AST to TargetType."""
    if isinstance(node, ast.Name):
        return BaseType(node.id)
    elif isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            return MessageType(node.value.id, node.attr)
        raise YaccGrammarError(f"Invalid type annotation: {ast.dump(node)}", line)
    elif isinstance(node, ast.Subscript):
        if isinstance(node.value, ast.Name):
            container = node.value.id
            if container == 'List' or container == 'list':
                elem_type = _annotation_to_type(node.slice, line)
                return ListType(elem_type)
            elif container == 'Optional':
                elem_type = _annotation_to_type(node.slice, line)
                return OptionType(elem_type)
            elif container == 'Tuple' or container == 'tuple':
                if isinstance(node.slice, ast.Tuple):
                    elem_types = [_annotation_to_type(e, line) for e in node.slice.elts]
                else:
                    elem_types = [_annotation_to_type(node.slice, line)]
                return TupleType(tuple(elem_types))
            elif container == 'Dict' or container == 'dict':
                if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                    key_type = _annotation_to_type(node.slice.elts[0], line)
                    value_type = _annotation_to_type(node.slice.elts[1], line)
                    return DictType(key_type, value_type)
                raise YaccGrammarError(f"dict type requires exactly 2 type arguments", line)
        raise YaccGrammarError(f"Invalid type annotation: {ast.dump(node)}", line)
    else:
        raise YaccGrammarError(f"Invalid type annotation: {ast.dump(node)}", line)


def load_yacc_grammar(text: str) -> GrammarConfig:
    """Load grammar from yacc-like format.

    Args:
        text: Grammar file content

    Returns:
        GrammarConfig with terminals, rules, and function definitions
    """
    lines = text.split('\n')

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

    return GrammarConfig(
        terminals=ctx.terminals,
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
    'parse_type',
    'parse_rhs',
    'parse_action',
    'parse_directives',
    'parse_rules',
    'parse_helper_functions',
    'load_yacc_grammar',
    'load_yacc_grammar_file',
]
