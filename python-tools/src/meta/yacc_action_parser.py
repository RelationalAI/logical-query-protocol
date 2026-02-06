"""Parser for semantic actions in yacc-like grammar files.

This module converts Python AST nodes to target IR expressions. It handles
the restricted subset of Python that can be translated to multiple target
languages (Python, Julia, Go).

Supported constructs:
- Literals: int, float, string, bool, None
- Variables and parameter references ($N)
- Function calls: builtins and user-defined
- Message constructors: module.Message(field=value)
- List literals: [a, b, c]
- Conditional expressions: x if cond else y
- Tuple indexing: x[0]
"""

import ast
import re
from typing import Dict, List, Optional, Tuple, Set

from .grammar import Rhs, LitTerminal, NamedTerminal, Nonterminal, Star, Option, Sequence
from .target import (
    TargetType, BaseType, MessageType, EnumType, ListType, OptionType, TupleType, DictType, FunctionType,
    TargetExpr, Var, Lit, NamedFun, NewMessage, EnumValue, Call, Lambda,
    Let, IfElse, Seq, ListExpr, GetElement, GetField, FunDef, OneOf, Assign, Return
)
from .target_builtins import make_builtin


class YaccGrammarError(Exception):
    """Error during yacc grammar parsing."""
    def __init__(self, message: str, line: Optional[int] = None):
        if line is not None:
            message = f"line {line}: {message}"
        super().__init__(message)
        self.line = line


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


def _make_named_fun(name: str, func_type: FunctionType) -> NamedFun:
    """Create a NamedFun with the given name and type."""
    return NamedFun(name, func_type)


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
            return OptionType(BaseType("Never"))
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
        # GetField has field_type from proto schema lookup (or Unknown if not found)
        return expr.field_type
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
        # Call.target_type() handles getting return type from FunctionType
        try:
            return expr.target_type()
        except ValueError:
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
                            params: List[Var], ctx: 'TypeContext',
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
        if name == 'True':
            return Lit(True)
        elif name == 'False':
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
            return _make_named_fun(name, ctx.functions[name])
        else:
            # Check builtins
            from .target_builtins import is_builtin
            if is_builtin(name):
                return make_builtin(name)
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

        # Handle builtin.foo(...) syntax for builtins
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "builtin":
                return Call(make_builtin(func.attr), args)

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
                if len(args) == 1:
                    arg_type = _infer_type(args[0], line, ctx)
                    oneof_type = FunctionType([arg_type], arg_type)
                else:
                    oneof_type = FunctionType([BaseType("Any")], BaseType("Any"))
                return Call(OneOf(variant_name, oneof_type), args)
            # has_field(msg, field_name) -> has_proto_field builtin
            if func_name == 'has_field':
                return Call(make_builtin('has_proto_field'), args)
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(make_builtin(func_name), args)
            if func_name in ctx.functions:
                return Call(_make_named_fun(func_name, ctx.functions[func_name]), args)
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
            elem_type = BaseType("Never")
        return ListExpr(elements, elem_type)

    elif isinstance(node, ast.IfExp):
        cond = convert(node.test)
        then_branch = convert(node.body)
        else_branch = convert(node.orelse)
        return IfElse(cond, then_branch, else_branch)

    elif isinstance(node, ast.Compare):
        # Handle comparisons: x is None, x is not None
        if len(node.ops) == 1 and len(node.comparators) == 1:
            left = convert(node.left)
            op = node.ops[0]
            if isinstance(op, ast.Is):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    return Call(make_builtin("is_none"), [left])
            elif isinstance(op, ast.IsNot):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    return Call(make_builtin("is_some"), [left])
        raise YaccGrammarError(
            f"Unsupported comparison. Only 'x is None' and 'x is not None' are supported in actions.",
            line)

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


def parse_action(text: str, rhs: Rhs, ctx: 'TypeContext', line: Optional[int] = None,
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
                      params: List[Var], ctx: 'TypeContext',
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

    # Try parsing as a single Python expression first
    try:
        tree = ast.parse(text, mode='eval')
        return _convert_node_with_vars(tree.body, param_info, params, ctx, line, extra_vars)
    except SyntaxError:
        pass

    # If that fails, try parsing as multiple statements (for multi-line actions)
    try:
        tree = ast.parse(text, mode='exec')
    except SyntaxError as e:
        raise YaccGrammarError(f"Syntax error in action: {e}", line)

    # Convert each statement to a target expression
    exprs = []
    for stmt in tree.body:
        if isinstance(stmt, ast.Expr):
            exprs.append(_convert_node_with_vars(stmt.value, param_info, params, ctx, line, extra_vars))
        else:
            raise YaccGrammarError(f"Unsupported statement in action block: {type(stmt).__name__}", line)

    if len(exprs) == 1:
        return exprs[0]
    return Seq(tuple(exprs))


# Helper function parsing

def prescan_helper_function_names(lines: List[str], start_line: int, ctx: 'TypeContext') -> None:
    """Pre-scan helper functions section to register function signatures.

    This allows rules to reference helper functions before they are fully parsed.
    """
    text = '\n'.join(lines)
    if not text.strip():
        return

    try:
        tree = ast.parse(text)
    except SyntaxError:
        # Ignore syntax errors here - they'll be reported during full parsing
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            try:
                params, return_type = _extract_function_signature(node, start_line)
                func_type = FunctionType([p.type for p in params], return_type)
                ctx.functions[node.name] = func_type
            except YaccGrammarError:
                # Ignore errors here - they'll be reported during full parsing
                pass


def parse_helper_functions(lines: List[str], start_line: int, ctx: 'TypeContext') -> Dict[str, FunDef]:
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

    # Two-pass approach:
    # Pass 1: Extract function signatures (if not already done by prescan)
    # Pass 2: Convert function bodies using the complete type environment

    # Pass 1: Extract function signatures and register types in ctx.functions
    func_nodes: List[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_nodes.append(node)
            if node.name not in ctx.functions:
                params, return_type = _extract_function_signature(node, start_line)
                func_type = FunctionType([p.type for p in params], return_type)
                ctx.functions[node.name] = func_type

    # Pass 2: Convert function bodies with complete type environment
    functions: Dict[str, FunDef] = {}
    for node in func_nodes:
        func_def = _convert_function_def(node, ctx, start_line)
        functions[func_def.name] = func_def

    return functions


def _extract_function_signature(node: ast.FunctionDef, base_line: int) -> Tuple[Tuple[Var, ...], TargetType]:
    """Extract function signature (params, return type) without converting body.

    Returns (params, return_type). The function name is available from node.name.
    """
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

    return tuple(params), return_type


def _convert_function_def(node: ast.FunctionDef, ctx: 'TypeContext', base_line: int) -> FunDef:
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


def _convert_function_body(stmts: List[ast.stmt], ctx: 'TypeContext', line: int,
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


def _convert_stmt(stmt: ast.stmt, ctx: 'TypeContext', line: int,
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
        # Simple assignment without type annotation: x = expr
        # Only allowed if re-assigning to an already-declared variable
        if len(stmt.targets) != 1:
            raise YaccGrammarError(f"Multiple assignment targets not supported", line)
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            raise YaccGrammarError(f"Only simple variable assignment supported", line)
        var_name = target.id
        if var_name not in local_vars:
            raise YaccGrammarError(
                f"Local variable '{var_name}' must have a type annotation. "
                f"Use '{var_name}: Type = ...' instead of '{var_name} = ...'",
                line)
        # Re-assignment to already-declared variable
        var_type = local_vars[var_name]
        value = _convert_func_expr(stmt.value, ctx, line, local_vars)
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


def _make_get_field(obj: TargetExpr, field_name: str, ctx: 'TypeContext', line: Optional[int] = None) -> GetField:
    """Create a GetField expression, looking up field type if possible."""
    obj_type = obj.target_type()
    # Unwrap OptionType - we assume caller has checked for None
    if isinstance(obj_type, OptionType):
        obj_type = obj_type.element_type
    if not isinstance(obj_type, MessageType):
        raise YaccGrammarError(f"Cannot access field '{field_name}' on non-message type {obj_type}", line)
    message_type = obj_type
    # Try to look up field type
    field_type: TargetType = BaseType("Unknown")
    if ctx.field_type_lookup is not None:
        looked_up = ctx.field_type_lookup(message_type, field_name)
        if looked_up is not None:
            field_type = looked_up
    return GetField(obj, field_name, message_type, field_type)


def _convert_func_expr(node: ast.expr, ctx: 'TypeContext', line: int,
                       local_vars: Dict[str, TargetType]) -> TargetExpr:
    """Convert a Python expression in a function body to target IR."""
    if isinstance(node, ast.Constant):
        return Lit(node.value)

    elif isinstance(node, ast.Name):
        name = node.id
        if name == 'True':
            return Lit(True)
        elif name == 'False':
            return Lit(False)
        elif name == 'None':
            return Lit(None)
        elif name in local_vars:
            return Var(name, local_vars[name])
        elif name in ctx.functions:
            return _make_named_fun(name, ctx.functions[name])
        else:
            from .target_builtins import is_builtin
            if is_builtin(name):
                return make_builtin(name)
            raise YaccGrammarError(f"Unknown variable: {name}", line)

    elif isinstance(node, ast.Attribute):
        # Check for module.Enum.VALUE pattern (three levels)
        if (isinstance(node.value, ast.Attribute) and
            isinstance(node.value.value, ast.Name)):
            module_name = node.value.value.id
            possible_enum = node.value.attr
            value_name = node.attr

            # Check if this is an enum value reference
            if ctx.enum_lookup is not None:
                enum_values = ctx.enum_lookup(module_name, possible_enum)
                if enum_values is not None:
                    valid = [n for n, _ in enum_values]
                    if value_name not in valid:
                        raise YaccGrammarError(
                            f"Unknown enum value '{value_name}' for enum {module_name}.{possible_enum}. "
                            f"Valid values: {valid}", line)
                    return EnumValue(module_name, possible_enum, value_name)

            # Not an enum, could be nested field access
            obj = _convert_func_expr(node.value, ctx, line, local_vars)
            return _make_get_field(obj, node.attr, ctx, line)

        # Handle module.Message or obj.field (two levels)
        if isinstance(node.value, ast.Name):
            # Could be module.Message constructor or local_var.field
            if node.value.id in local_vars:
                # Field access on a variable
                obj = Var(node.value.id, local_vars[node.value.id])
                return _make_get_field(obj, node.attr, ctx, line)
            else:
                # Assume it's a message constructor reference
                return NewMessage(node.value.id, node.attr, ())
        else:
            # Field access on a more complex expression
            obj = _convert_func_expr(node.value, ctx, line, local_vars)
            return _make_get_field(obj, node.attr, ctx, line)

    elif isinstance(node, ast.Call):
        func = node.func
        args = [_convert_func_expr(a, ctx, line, local_vars) for a in node.args]

        # Handle builtin.foo(...) syntax for builtins
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id == "builtin":
                return Call(make_builtin(func.attr), args)

        # Handle message constructor or method call: module.Message(field=value, ...) or obj.method(args)
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            obj_name = func.value.id
            method_name = func.attr
            # Check if obj_name is a local variable (method call)
            if obj_name in local_vars:
                # Method call: obj.method(args)
                obj = Var(obj_name, local_vars[obj_name])
                method_ref = _make_get_field(obj, method_name, ctx, line)
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
                if len(args) == 1:
                    return Call(make_builtin('dict_from_list'), args)
                raise YaccGrammarError(f"dict() requires exactly one argument", line)
            # User-defined functions take precedence over builtins
            if func_name in ctx.functions:
                return Call(_make_named_fun(func_name, ctx.functions[func_name]), args)
            # has_field(msg, field_name) -> has_proto_field builtin
            if func_name == 'has_field':
                return Call(make_builtin('has_proto_field'), args)
            from .target_builtins import is_builtin
            if is_builtin(func_name):
                return Call(make_builtin(func_name), args)
            raise YaccGrammarError(f"Unknown function: {func_name}", line)

        # Handle method calls on expressions: expr.method(args)
        if isinstance(func, ast.Attribute):
            obj = _convert_func_expr(func.value, ctx, line, local_vars)
            method_name = func.attr
            # String methods
            if method_name == "upper":
                return Call(make_builtin("string_to_upper"), [obj] + args)
            elif method_name == "lower":
                return Call(make_builtin("string_to_lower"), [obj] + args)
            # For message types, treat as field access (method reference)
            obj_type = obj.target_type()
            if isinstance(obj_type, OptionType):
                obj_type = obj_type.element_type
            if isinstance(obj_type, MessageType):
                method_ref = _make_get_field(obj, method_name, ctx, line)
                return Call(method_ref, args)
            raise YaccGrammarError(f"Cannot call method '{method_name}' on type {obj_type}", line)

        func_expr = _convert_func_expr(func, ctx, line, local_vars)
        return Call(func_expr, args)

    elif isinstance(node, ast.List):
        elements = [_convert_func_expr(e, ctx, line, local_vars) for e in node.elts]
        if elements:
            elem_type = _infer_type(elements[0], line, ctx)
        else:
            # Empty list has type List[Bottom]
            # With covariance: List[Bottom] <: List[T] for any T
            elem_type = BaseType("Never")
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
                    return Call(make_builtin("is_none"), [left])
                return Call(make_builtin("equal"), [left, right])
            elif isinstance(op, ast.IsNot):
                if isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value is None:
                    return Call(make_builtin("is_some"), [left])
                return Call(make_builtin("not_equal"), [left, right])
            elif isinstance(op, ast.Eq):
                return Call(make_builtin("equal"), [left, right])
            elif isinstance(op, ast.NotEq):
                return Call(make_builtin("not_equal"), [left, right])
            elif isinstance(op, ast.In):
                return Call(make_builtin("string_in_list"), [left, right])
            elif isinstance(op, ast.NotIn):
                return Call(make_builtin("not"), [Call(make_builtin("string_in_list"), [left, right])])
        raise YaccGrammarError(f"Unsupported comparison: {ast.dump(node)}", line)

    elif isinstance(node, ast.BoolOp):
        # Handle 'and' and 'or'
        if isinstance(node.op, ast.And):
            result = _convert_func_expr(node.values[0], ctx, line, local_vars)
            for val in node.values[1:]:
                result = Call(make_builtin("and"), [result, _convert_func_expr(val, ctx, line, local_vars)])
            return result
        elif isinstance(node.op, ast.Or):
            result = _convert_func_expr(node.values[0], ctx, line, local_vars)
            for val in node.values[1:]:
                result = Call(make_builtin("or"), [result, _convert_func_expr(val, ctx, line, local_vars)])
            return result
        raise YaccGrammarError(f"Unsupported boolean operation", line)

    elif isinstance(node, ast.BinOp):
        left = _convert_func_expr(node.left, ctx, line, local_vars)
        right = _convert_func_expr(node.right, ctx, line, local_vars)
        if isinstance(node.op, ast.Add):
            # Could be numeric add or string concat - use string_concat for strings
            return Call(make_builtin("string_concat"), [left, right])
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


# TypeContext is defined here to avoid circular imports, but it's also
# re-exported from yacc_parser for convenience.
from dataclasses import dataclass, field

from typing import Callable

@dataclass
class TypeContext:
    """Context for looking up types of terminals and nonterminals."""
    terminals: Dict[str, TargetType] = field(default_factory=dict)
    terminal_info: Dict[str, 'TerminalInfo'] = field(default_factory=dict)
    nonterminals: Dict[str, TargetType] = field(default_factory=dict)
    functions: Dict[str, FunctionType] = field(default_factory=dict)
    start_symbol: Optional[str] = None
    # Callback to look up field type: (message_type, field_name) -> field_type
    # If None, field types cannot be resolved (use Unknown placeholder)
    field_type_lookup: Optional[Callable[[MessageType, str], Optional[TargetType]]] = None
    # Callback to look up enum values: (module, enum_name) -> [(value_name, value_num), ...]
    # If None, enum values cannot be validated
    enum_lookup: Optional[Callable[[str, str], Optional[List[Tuple[str, int]]]]] = None
    # Callback to check if (module, name) is a message type
    message_lookup: Optional[Callable[[str, str], bool]] = None


@dataclass
class TerminalInfo:
    """Information about a terminal symbol."""
    type: TargetType
    pattern: Optional[str] = None
    is_regex: bool = True  # True for r'...' patterns, False for '...' literals


__all__ = [
    'YaccGrammarError',
    'TypeContext',
    'TerminalInfo',
    'parse_action',
    'parse_action_expr',
    'parse_helper_functions',
    'prescan_helper_function_names',
    'preprocess_action',
    '_get_rhs_param_info',
    '_get_rhs_param_types',
    '_build_params',
    '_infer_type',
    '_convert_node_with_vars',
]
