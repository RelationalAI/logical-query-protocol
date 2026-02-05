# Plan: Factor Out Code Generator Common Structure

## Goal
Refactor Julia and Python code generators to use a template-based system for both builtins AND IR node handling.

## Part 1: Builtin Templates

### Data Structures (in `codegen_templates.py`)

```python
@dataclass
class BuiltinTemplate:
    value_template: str  # e.g., "!{0}"
    statement_templates: List[str] = field(default_factory=list)

@dataclass
class VariadicBuiltinTemplate:
    templates_by_arity: Dict[int, BuiltinTemplate]
```

### Builtin Template Dictionaries

```python
PYTHON_TEMPLATES = {
    "not": BuiltinTemplate("not {0}"),
    "and": BuiltinTemplate("({0} and {1})"),
    "or": BuiltinTemplate("({0} or {1})"),
    "is_none": BuiltinTemplate("{0} is None"),
    "none": BuiltinTemplate("None"),
    "string_concat": BuiltinTemplate("({0} + {1})"),
    "length": BuiltinTemplate("len({0})"),
    # ... ~30 entries
}

JULIA_TEMPLATES = {
    "not": BuiltinTemplate("!{0}"),
    "and": BuiltinTemplate("({0} && {1})"),
    "or": BuiltinTemplate("({0} || {1})"),
    "is_none": BuiltinTemplate("isnothing({0})"),
    "none": BuiltinTemplate("nothing"),
    "string_concat": BuiltinTemplate("({0} * {1})"),
    "length": BuiltinTemplate("length({0})"),
    # ... ~30 entries
}
```

## Part 2: IR Node Templates

### Control Flow Templates

Add structural templates for control flow. `\n ` (newline + space) indicates indentation increase:

```python
@dataclass
class ControlFlowTemplates:
    if_else: str  # Template for if-else structure
    while_loop: str  # Template for while loop
    # ... other control structures

PYTHON_CONTROL_FLOW = ControlFlowTemplates(
    if_else="if {cond}:\n {then}\nelse:\n {else}",
    while_loop="while {cond}:\n {body}",
)

JULIA_CONTROL_FLOW = ControlFlowTemplates(
    if_else="if {cond}\n {then}\nelse\n {else}\nend",
    while_loop="while {cond}\n {body}\nend",
)
```

### Short-Circuit Optimization via Builtins

For the if-else short-circuit optimization, delegate to the `and`/`or` builtins:

```python
def _generate_if_else(self, expr: IfElse, lines: List[str], indent: str) -> Optional[str]:
    cond_code = self.generate_lines(expr.condition, lines, indent)

    # Short-circuit: `if cond then True else x` → `cond or x`
    if expr.then_branch == Lit(True):
        tmp_lines: List[str] = []
        else_code = self.generate_lines(expr.else_branch, tmp_lines, indent)
        if not tmp_lines and else_code is not None:
            # Delegate to the "or" builtin template
            result = self.gen_builtin_call("or", [cond_code, else_code], [], indent)
            return result.value

    # Short-circuit: `if cond then x else False` → `cond and x`
    if expr.else_branch == Lit(False):
        tmp_lines = []
        then_code = self.generate_lines(expr.then_branch, tmp_lines, indent)
        if not tmp_lines and then_code is not None:
            # Delegate to the "and" builtin template
            result = self.gen_builtin_call("and", [cond_code, then_code], [], indent)
            return result.value

    # Full if-else using structural template...
```

### VisitNonterminal Templates

Templates for parse method calls:

```python
# {name} = nonterminal name, {args} = comma-separated arguments
PYTHON_VISIT_NONTERMINAL = "self.parse_{name}({args})"
JULIA_VISIT_NONTERMINAL = "parse_{name}(parser, {args})"  # Note: handle empty args → "parse_{name}(parser)"
```

When `{args}` is empty:
- Python: `self.parse_foo()`
- Julia: `parse_foo(parser)`

### Config Properties

```python
class CodeGenerator(ABC):
    # Array indexing offset (0 for Python, 1 for Julia)
    array_index_offset: int = 0
```

## Part 3: Language-Specific Config

### Python

```python
class PythonCodeGenerator(CodeGenerator):
    array_index_offset = 0
    prepend_parser_to_parse_calls = False
```

### Julia

```python
class JuliaCodeGenerator(CodeGenerator):
    array_index_offset = 1
    prepend_parser_to_parse_calls = True
    parser_arg_name = "parser"
```

## Summary of Template/Config Items

| Item | Python | Julia |
|------|--------|-------|
| `array_index_offset` | 0 | 1 |
| VisitNonterminal | `self.parse_{name}({args})` | `parse_{name}(parser, {args})` |
| if-else template | `if {cond}:\n {then}\nelse:\n {else}` | `if {cond}\n {then}\nelse\n {else}\nend` |
| while template | `while {cond}:\n {body}` | `while {cond}\n {body}\nend` |
| Builtin `not` | `not {0}` | `!{0}` |
| Builtin `and` | `({0} and {1})` | `({0} && {1})` |
| Builtin `or` | `({0} or {1})` | `({0} \|\| {1})` |
| Builtin `is_none` | `{0} is None` | `isnothing({0})` |
| Builtin `none` | `None` | `nothing` |
| Builtin `string_concat` | `({0} + {1})` | `({0} * {1})` |
| Builtin `length` | `len({0})` | `length({0})` |
| Builtin `consume_terminal` | `self.consume_terminal({0})` | `consume_terminal!(parser, {0})` |

## Files to Modify

1. **NEW** `/python-tools/src/meta/codegen_templates.py`
   - `BuiltinTemplate`, `VariadicBuiltinTemplate`, `ControlFlowTemplates` dataclasses
   - `PYTHON_TEMPLATES`, `JULIA_TEMPLATES` builtin dictionaries
   - `PYTHON_CONTROL_FLOW`, `JULIA_CONTROL_FLOW` structural templates
   - `PYTHON_VISIT_NONTERMINAL`, `JULIA_VISIT_NONTERMINAL` call templates

2. `/python-tools/src/meta/codegen_base.py`
   - Add `array_index_offset` property
   - Add template registration methods
   - Update `_generate_if_else` to use builtin delegation for short-circuit
   - Update `generate_lines` for GetElement to use index offset
   - Update `_generate_call` for VisitNonterminal to use template

3. `/python-tools/src/meta/codegen_python.py`
   - Set config properties
   - Replace `_register_builtins()` to use templates
   - Remove `_generate_if_else` override

4. `/python-tools/src/meta/codegen_julia.py`
   - Set config properties
   - Replace `_register_builtins()` to use templates
   - Remove `_generate_if_else` override
   - Remove `generate_lines` GetElement override

## What Stays Language-Specific

These have complex logic not worth templatizing:
- `_generate_newmessage` (Python): keyword field handling
- `_generate_call` for NewMessage/OneOf (Julia): positional args, OneOf wrapping
- `_generate_parse_def`: different method signatures

## Verification

1. Run: `cd python-tools && uv run pytest tests/meta/test_codegen_*.py`
2. Compare generated output before/after
3. Add test that builtin template keys match between languages
