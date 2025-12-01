# Meta-Language Tooling

This package provides tools for generating parsers and pretty-printers from protobuf specifications.

## Overview

The meta-language tooling converts protobuf message definitions into:
- **Lark grammars** for parsing S-expression representations
- **Recursive-descent parsers** in Python, Julia, and Go
- **Pretty-printers** for converting protobuf bytes back to S-expressions

## Architecture

### Core Modules

#### Grammar Representation (`grammar.py`)
- **Data structures**: `Grammar`, `Rule`, `Token`, `Rhs` types (`Literal`, `Terminal`, `Nonterminal`, `Sequence`, `Star`, `Plus`, `Option`)
- **Semantic actions**: `ActionExpr` types (`Function`, `Var`, `Call`, `Symbol`, `Wildcard`)
- **Public API**: Grammar construction and manipulation

#### Grammar Transformations

**`normalize.py`** - EBNF Operator Elimination
- Converts `A*` → `A_star -> A A_star | ε`
- Converts `A+` → `A_plus -> A A_star`
- Converts `A?` → `A_opt -> A | ε`

**`left_factor.py`** - Common Prefix Extraction
- Transforms `A -> α β₁ | α β₂` into `A -> α A'` and `A' -> β₁ | β₂`
- Stores metadata for semantic action reconstruction
- Enables LL(k) parsing of grammars with common prefixes

**`analysis.py`** - Grammar Analysis
- Reachability analysis
- Nullable set computation
- FIRST and FIRST_k sets
- FOLLOW sets
- LL(k) conflict detection

#### Protobuf Processing

**`proto_ast.py`** - Protobuf AST Types
- `ProtoField`, `ProtoOneof`, `ProtoEnum`, `ProtoMessage`
- `PRIMITIVE_TYPES` mapping

**`proto_parser.py`** - Protobuf Parser
- `ProtoParser` class for extracting message/enum definitions from .proto files
- Handles nested messages, oneofs, and enums

**`grammar_gen.py`** - Grammar Generator
- `GrammarGenerator` class converts protobuf specifications to Lark grammars
- Generates prepopulated rules for transactions, bindings, operators
- Maps protobuf types to grammar rules

#### Code Generation

**`parser_python.py`** - Python Parser Generator
- Generates LL(k) recursive-descent parser with backtracking
- Lexer generation with token patterns and literals
- Decision tree generation for multiple alternatives
- Support for left-factored rules with continuation methods
- Semantic action threading through prefix/suffix combinations

**`parser_julia.py`** - Julia Parser Generator (stub)
**`parser_go.py`** - Go Parser Generator (stub)

**`printer_python.py`** - Python Pretty Printer (stub)
**`printer_julia.py`** - Julia Pretty Printer (stub)
**`printer_go.py`** - Go Pretty Printer (stub)

#### CLI Tool

**`proto_tool.py`** - Command-Line Interface
- Parse protobuf files
- Generate grammars, parsers, and pretty-printers
- Multiple output format support

## Usage

### Command Line

```bash
# Generate Lark grammar
python -m src.meta.proto_tool --grammar file.proto -o output.lark

# Generate Python parser
python -m src.meta.proto_tool --parser python file.proto -o parser.py

# Generate semantic actions
python -m src.meta.proto_tool --actions file.proto -o visitor.py
```

### Programmatic API

```python
from meta import Grammar, ProtoParser, GrammarGenerator
from meta.parser_python import generate_parser_python

# Parse protobuf files
parser = ProtoParser()
parser.parse_file('messages.proto')

# Generate grammar
generator = GrammarGenerator(parser, verbose=True)
grammar = generator.generate(start_message='Transaction')

# Apply transformations
normalized = grammar.normalize()
factored = normalized.left_factor()

# Generate parser
parser_code = generate_parser_python(factored, reachable=None)

with open('parser.py', 'w') as f:
    f.write(parser_code)
```

## Grammar Transformation Pipeline

The parser generation applies two key transformations:

### 1. Normalization

Eliminates EBNF operators to produce a pure context-free grammar:

**Before:**
```
list -> "(" "list" item* ")"
```

**After:**
```
list -> "(" "list" item_star_0 ")"
item_star_0 -> item item_star_0
item_star_0 -> ε
```

### 2. Left-Factoring

Extracts common prefixes to enable LL(k) parsing:

**Before:**
```
expr -> "(" "add" term term ")"
expr -> "(" "sub" term term ")"
```

**After:**
```
expr -> "(" expr_cont_0
expr_cont_0 -> "add" term term ")"
expr_cont_0 -> "sub" term term ")"
```

The generated parser threads parsed prefix results through continuation methods:

```python
def parse_expr(self):
    # Parse common prefix
    prefix_results = []
    self.consume('(')
    prefix_results.append(None)
    
    # Parse continuation with prefix context
    suffix_result = self.parse_expr_cont_0(prefix_results)
    return suffix_result

def parse_expr_cont_0(self, prefix_results):
    if self.match_literal('add'):
        # Parse 'add' alternative
        suffix_results = []
        # ... parse suffix elements ...
        all_results = prefix_results + suffix_results
        return all_results
    elif self.match_literal('sub'):
        # Parse 'sub' alternative
        ...
```

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/meta/

# Individual test modules
python tests/meta/test_normalize.py
python tests/meta/test_left_factor.py
python tests/meta/test_parser_gen.py
```

## Module Dependencies

```
proto_tool.py
  ├── proto_parser.py
  │   └── proto_ast.py
  ├── grammar_gen.py
  │   ├── proto_ast.py
  │   ├── proto_parser.py
  │   └── grammar.py
  └── parser_python.py
      ├── grammar.py
      │   ├── normalize.py
      │   ├── left_factor.py
      │   └── analysis.py
      └── analysis.py
```

## Implementation Notes

### Left-Factoring and Semantic Actions

Continuation rules store metadata to reconstruct semantic actions:
- `original_rules` - References to pre-factored rules
- `original_action` - Original semantic action
- `original_rule_index` - Index of corresponding original rule
- `prefix_length` - Length of factored prefix

Parser generation combines prefix and suffix parse results to match the parameters expected by original semantic actions.

### LL(k) Conflict Detection

The parser generator computes FIRST_k sets and detects conflicts:
- LL(2) checking by default
- Decision trees up to depth k=7 for complex cases
- Backtracking as fallback for remaining ambiguities

### Parser Features

Generated parsers include:
- Lexer with regex-based tokenization
- Lookahead methods for k-token predictions
- Position save/restore for backtracking
- Error reporting with position information
- Support for left-factored continuation nonterminals

## Future Work

- Complete Julia and Go parser generators
- Implement pretty-printer generators
- Add incremental parsing support
- Optimize decision tree generation
- Generate parser tables for table-driven parsing
