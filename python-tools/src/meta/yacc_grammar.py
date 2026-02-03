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
    (List Type)                        -> ListType
    (Tuple Type1 Type2 ...)            -> TupleType
    (Option Type)                      -> OptionType

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
    let x = e1 in e2    -> let binding
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
    GrammarConfig
)
from .target import (
    TargetType, BaseType, MessageType, ListType, OptionType, TupleType,
    TargetExpr, Var, Lit, Symbol, Builtin, NamedFun, NewMessage, Call, Lambda,
    Let, IfElse, Seq, ListExpr, GetElement, FunDef
)


class YaccGrammarError(Exception):
    """Error during yacc grammar parsing."""
    def __init__(self, message: str, line: Optional[int] = None):
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
        self.line = line


@dataclass
class TypeContext:
    """Context for looking up types of terminals and nonterminals."""
    terminals: Dict[str, TargetType] = field(default_factory=dict)
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
            parts = line[6:].strip().split(None, 1)
            if len(parts) != 2:
                raise YaccGrammarError(f"Invalid %token directive: {line}", i)
            name, type_str = parts
            ctx.terminals[name] = parse_type(type_str)

        elif line.startswith('%type'):
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
        TERMINAL_NAME       -> NamedTerminal (uppercase or in terminals)
        nonterminal_name    -> Nonterminal (lowercase or in nonterminals)
        element*            -> Star(element)
        element?            -> Option(element)
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

    # Look up in context
    if text in ctx.terminals:
        return NamedTerminal(text, ctx.terminals[text])
    if text in ctx.nonterminals:
        return Nonterminal(text, ctx.nonterminals[text])

    # Heuristic: uppercase = terminal, lowercase = nonterminal
    if text.isupper():
        raise YaccGrammarError(f"Unknown terminal: {text}")
    else:
        raise YaccGrammarError(f"Unknown nonterminal: {text}")


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


def _get_rhs_param_types(rhs: Rhs) -> List[Optional[TargetType]]:
    """Get the types of parameters from an RHS (including literals as None).

    Returns a list with one entry per RHS element. Literals are represented
    as None since they cannot be meaningfully referenced in actions.
    """
    if isinstance(rhs, Sequence):
        types: List[Optional[TargetType]] = []
        for elem in rhs.elements:
            if isinstance(elem, LitTerminal):
                types.append(None)  # Literals have no meaningful type
            else:
                types.append(elem.target_type())
        return types
    elif isinstance(rhs, LitTerminal):
        return [None]
    else:
        return [rhs.target_type()]


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
            func_name = func.name if hasattr(func, 'name') else func.id
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
        # Infer element type from first element (simplified)
        # In practice, we'd need proper type inference
        return ListExpr(elements, _infer_type(elements[0]))

    elif isinstance(node, ast.BinOp):
        # Handle let expressions parsed as comparison: let x = e1 in e2
        # This would be preprocessed
        raise YaccGrammarError(f"Binary operations not supported: {ast.dump(node)}", line)

    elif isinstance(node, ast.Compare):
        # Handle let binding: let x = e1 in e2
        # Preprocessed as: (x, e1, e2) with op being special
        raise YaccGrammarError(f"Comparison not supported: {ast.dump(node)}", line)

    elif isinstance(node, ast.IfExp):
        cond = _convert_node(node.test, param_types, ctx, line)
        then_branch = _convert_node(node.body, param_types, ctx, line)
        else_branch = _convert_node(node.orelse, param_types, ctx, line)
        return IfElse(cond, then_branch, else_branch)

    else:
        raise YaccGrammarError(f"Unsupported Python AST node: {type(node).__name__}: {ast.dump(node)}", line)


def _infer_type(expr: TargetExpr) -> TargetType:
    """Infer the type of an expression (simplified)."""
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
    elif isinstance(expr, NewMessage):
        return MessageType(expr.module, expr.name)
    elif isinstance(expr, ListExpr):
        return ListType(expr.element_type)
    elif isinstance(expr, GetElement):
        # Infer tuple element type
        tuple_type = _infer_type(expr.tuple_expr)
        if isinstance(tuple_type, TupleType) and 0 <= expr.index < len(tuple_type.elements):
            return tuple_type.elements[expr.index]
    elif isinstance(expr, Let):
        # Let expression has the type of its body
        return _infer_type(expr.body)
    elif isinstance(expr, IfElse):
        # Conditional has the type of its branches (assume they're the same)
        return _infer_type(expr.then_branch)
    elif isinstance(expr, Seq):
        # Sequence has the type of its last expression
        if expr.exprs:
            return _infer_type(expr.exprs[-1])
    elif isinstance(expr, Call):
        # For builtins and named functions, we'd need type signatures
        # For now, return Unknown
        pass
    # Default fallback
    return BaseType("Unknown")


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

    # Parse the expression (handles let expressions recursively)
    param_types = _get_rhs_param_types(rhs)
    body = parse_action_expr(preprocessed, param_types, ctx, line)

    # Build the lambda
    params = _build_params(rhs)
    # Use expected return type from %type declaration if provided, otherwise infer
    return_type = expected_return_type if expected_return_type is not None else _infer_type(body)
    return Lambda(params, return_type, body)


def parse_action_expr(text: str, param_types: List[Optional[TargetType]], ctx: TypeContext,
                      line: Optional[int], extra_vars: Optional[Dict[str, TargetType]] = None) -> TargetExpr:
    """Parse an action expression, handling let expressions recursively."""
    text = text.strip()
    extra_vars = extra_vars or {}

    # Handle let expressions: let VAR = EXPR in BODY
    let_match = re.match(r'let\s+(\w+)\s*=\s*(.+?)\s+in\s+(.+)$', text, re.DOTALL)
    if let_match:
        var_name = let_match.group(1)
        init_text = let_match.group(2)
        body_text = let_match.group(3)

        # Parse init expression
        init_expr = parse_action_expr(init_text, param_types, ctx, line, extra_vars)
        init_type = _infer_type(init_expr)

        # Parse body with the let-bound variable in scope
        new_extra_vars = dict(extra_vars)
        new_extra_vars[var_name] = init_type
        body_expr = parse_action_expr(body_text, param_types, ctx, line, new_extra_vars)

        return Let(Var(var_name, init_type), init_expr, body_expr)

    # Parse as regular Python expression
    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError as e:
        raise YaccGrammarError(f"Syntax error in action: {e}", line)

    return _convert_node_with_vars(tree.body, param_types, ctx, line, extra_vars)


def _convert_node_with_vars(node: ast.AST, param_types: List[Optional[TargetType]], ctx: TypeContext,
                            line: Optional[int], extra_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert AST node with extra variable bindings."""

    if isinstance(node, ast.Constant):
        return Lit(node.value)

    elif isinstance(node, ast.Name):
        name = node.id
        if name == 'true':
            return Lit(True)
        elif name == 'false':
            return Lit(False)
        elif name.startswith('_dollar_'):
            idx = int(name[8:]) - 1
            if idx < 0 or idx >= len(param_types):
                raise YaccGrammarError(f"Invalid parameter reference ${idx+1}", line)
            param_type = param_types[idx]
            if param_type is None:
                raise YaccGrammarError(f"Cannot reference literal at position ${idx+1}", line)
            return Var(f"_{idx}", param_type)
        elif name in extra_vars:
            return Var(name, extra_vars[name])
        elif name in ctx.functions:
            return NamedFun(name)
        else:
            # Check builtins
            from .target_builtins import is_builtin
            if is_builtin(name):
                return Builtin(name)
            raise YaccGrammarError(f"Unknown variable or function: {name}", line)

    elif isinstance(node, ast.Subscript):
        value = _convert_node_with_vars(node.value, param_types, ctx, line, extra_vars)
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            return GetElement(value, node.slice.value)
        raise YaccGrammarError(f"Subscript must use integer literal index", line)

    elif isinstance(node, ast.Attribute):
        if isinstance(node.value, ast.Name):
            # module.Message reference
            return NewMessage(node.value.id, node.attr, ())
        obj = _convert_node_with_vars(node.value, param_types, ctx, line, extra_vars)
        raise YaccGrammarError(f"Field access not supported", line)

    elif isinstance(node, ast.Call):
        func = node.func
        args = [_convert_node_with_vars(a, param_types, ctx, line, extra_vars) for a in node.args]

        # Message constructor
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            module_name = func.value.id
            msg_name = func.attr
            fields = []
            for kw in node.keywords:
                if kw.arg is None:
                    raise YaccGrammarError(f"**kwargs not supported", line)
                field_name = kw.arg
                # Restore original field name if it was escaped
                if field_name.startswith('_kw_') and field_name.endswith('_'):
                    field_name = field_name[4:-1]
                field_expr = _convert_node_with_vars(kw.value, param_types, ctx, line, extra_vars)
                fields.append((field_name, field_expr))
            return NewMessage(module_name, msg_name, tuple(fields))

        # Function call
        if isinstance(func, ast.Name):
            func_name = func.id
            # Handle special forms
            if func_name == 'seq':
                return Seq(args)
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(Builtin(func_name), args)
            if func_name in ctx.functions:
                return Call(NamedFun(func_name), args)
            raise YaccGrammarError(f"Unknown function: {func_name}", line)

        func_expr = _convert_node_with_vars(func, param_types, ctx, line, extra_vars)
        return Call(func_expr, args)

    elif isinstance(node, ast.List):
        elements = [_convert_node_with_vars(e, param_types, ctx, line, extra_vars) for e in node.elts]
        if elements:
            elem_type = _infer_type(elements[0])
        else:
            elem_type = BaseType("Unknown")
        return ListExpr(elements, elem_type)

    elif isinstance(node, ast.IfExp):
        cond = _convert_node_with_vars(node.test, param_types, ctx, line, extra_vars)
        then_branch = _convert_node_with_vars(node.body, param_types, ctx, line, extra_vars)
        else_branch = _convert_node_with_vars(node.orelse, param_types, ctx, line, extra_vars)
        return IfElse(cond, then_branch, else_branch)

    else:
        raise YaccGrammarError(f"Unsupported AST node: {type(node).__name__}", line)


def _build_params(rhs: Rhs) -> List[Var]:
    """Build parameter list from RHS (non-literal elements only)."""
    param_types = _get_rhs_param_types(rhs)
    params = []
    param_idx = 0
    for i, t in enumerate(param_types):
        if t is not None:
            params.append(Var(f"_{i}", t))
            param_idx += 1
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
        if current_alt_lines and current_lhs is not None:
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

    functions: Dict[str, FunDef] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_def = _convert_function_def(node, ctx, start_line)
            functions[func_def.name] = func_def

    return functions


def _convert_function_def(node: ast.FunctionDef, ctx: TypeContext, base_line: int) -> FunDef:
    """Convert a Python function definition to FunDef."""
    name = node.name

    # Parse parameters with type annotations
    params = []
    for arg in node.args.args:
        param_name = arg.arg
        if arg.annotation is None:
            raise YaccGrammarError(f"Parameter {param_name} in {name} missing type annotation",
                                   base_line + node.lineno)
        param_type = _annotation_to_type(arg.annotation, base_line + node.lineno)
        params.append(Var(param_name, param_type))

    # Parse return type
    if node.returns is None:
        raise YaccGrammarError(f"Function {name} missing return type annotation",
                               base_line + node.lineno)
    return_type = _annotation_to_type(node.returns, base_line + node.lineno)

    # For now, we'll store the body as None and handle it separately
    # Full conversion of function bodies is complex
    # TODO: Convert function body to target IR
    body = None

    return FunDef(name, tuple(params), return_type, body)


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

    return GrammarConfig(
        terminals=ctx.terminals,
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
