# Meta-Language Tooling

This package provides tools for generating parsers from protobuf specifications.

## Overview

The meta-language tooling converts protobuf message definitions into:
- **Grammars** for parsing S-expression representations
- **Recursive-descent parsers** in Python and Julia

## Architecture

### Core Modules

#### Grammar Representation (`grammar.py`)
- **Data structures**: `Grammar`, `Rule`, `Rhs` types (`LitTerminal`, `NamedTerminal`, `Nonterminal`, `Star`, `Option`, `Sequence`)
- **Semantic actions**: `Lambda` for result construction
- **Public API**: Grammar construction and manipulation

#### Grammar Analysis

**`grammar_analysis.py`** - Grammar Analysis
- `GrammarAnalysis` class with cached analysis results
- Reachability analysis
- Nullable set computation
- FIRST and FIRST_k sets
- FOLLOW and FOLLOW_k sets
- LL(k) conflict detection

**`grammar_utils.py`** - Grammar Utilities
- Helper functions for extracting nonterminals and terminals
- Sequence manipulation utilities

**`terminal_sequence_set.py`** - Terminal Sequence Sets
- Lazy computation of FIRST_k and FOLLOW_k sets
- Incremental k-depth expansion for LL(k) analysis

#### Protobuf Processing

**`proto_ast.py`** - Protobuf AST Types
- `ProtoField`, `ProtoOneof`, `ProtoEnum`, `ProtoMessage`
- `PRIMITIVE_TYPES` mapping

**`proto_parser.py`** - Protobuf Parser
- `ProtoParser` class for extracting message/enum definitions from .proto files
- Handles nested messages, oneofs, and enums

**`proto_print.py`** - Protobuf Formatting
- Format parsed protobuf specifications for display

**`grammar_gen.py`** - Grammar Generator
- `GrammarGenerator` class converts protobuf specifications to context-free grammars
- Maps protobuf types to grammar rules

**`grammar_gen_builtins.py`** - Built-in Grammar Rules
- Prepopulated rules for transactions, bindings, operators
- S-expression structure rules

**`grammar_gen_rewrites.py`** - Grammar Rule Rewrites
- Transform protobuf-generated rules for better parsing
- Symbol replacement, abstraction rewrites

#### Target IR (Intermediate Representation)

**`target.py`** - IR Type Definitions
- Expression types: `Var`, `Lit`, `Symbol`, `Builtin`, `Call`, `Lambda`, `Let`, `IfElse`, `Seq`, `While`, `Assign`, `Return`
- Data structure types: `Message`, `OneOf`, `ListExpr`
- Type system: `BaseType`, `TupleType`, `ListType`, `OptionType`, `MessageType`, `FunctionType`
- Function definitions: `FunDef`, `VisitNonterminalDef`, `VisitNonterminal`

**`target_utils.py`** - IR Utilities
- Helper functions for IR manipulation and construction

#### Parser Generation

**`parser_gen.py`** - Language-Independent Parser Generation
- Generates LL(k) recursive-descent parser IR
- Decision tree generation for alternative selection
- Handles EBNF operators (Star, Option)
- Semantic action integration

**`parser_gen_python.py`** - Python Parser Generator
- Translates IR to Python code via `codegen_python.py`
- Generates complete parser with lexer

**`parser_gen_julia.py`** - Julia Parser Generator
- Translates IR to Julia code via `codegen_julia.py`
- Generates complete parser with lexer

#### Code Generation

**`codegen_base.py`** - Base Code Generator
- Abstract base class for language-specific code generators
- Shared logic for IR-to-code translation

**`codegen_python.py`** - Python Code Generator
- Translates target IR to Python
- Implements language-specific builtins and syntax

**`codegen_julia.py`** - Julia Code Generator
- Translates target IR to Julia
- Implements language-specific builtins and syntax

#### Utilities

**`gensym.py`** - Symbol Generation
- Generate unique variable and function names

#### CLI Tool

**`cli.py`** - Command-Line Interface
- Parse protobuf files
- Generate grammars and parsers
- Multiple output format support

## Usage

### Command Line

```bash
# Display parsed protobuf specification
python -m meta.cli file.proto

# Generate and display grammar
python -m meta.cli file.proto --grammar

# Generate Python parser
python -m meta.cli file.proto --parser python -o parser.py

# Generate Julia parser
python -m meta.cli file.proto --parser julia -o parser.jl

# Specify start message
python -m meta.cli file.proto --grammar --start Transaction
```

### Programmatic API

```python
from meta.proto_parser import ProtoParser
from meta.grammar_gen import GrammarGenerator
from meta.parser_gen import generate_parse_functions
from meta.parser_gen_python import generate_parser_python

# Parse protobuf files
parser = ProtoParser()
parser.parse_file('messages.proto')

# Generate grammar
generator = GrammarGenerator(parser, verbose=True)
grammar = generator.generate()

# Generate parser IR
parse_functions = generate_parse_functions(grammar)

# Generate Python code
parser_code = generate_parser_python(parse_functions)

with open('parser.py', 'w') as f:
    f.write(parser_code)
```

## Parser Generation Pipeline

The parser generator produces LL(k) recursive-descent parsers:

### 1. IR Generation (`parser_gen.py`)

Generates target-independent intermediate representation:
- Computes FIRST_k and FOLLOW_k sets for LL(k) analysis
- Builds decision trees to select production alternatives
- Handles EBNF operators (Star, Option) with loops and conditionals
- Integrates semantic actions (Lambda expressions)

### 2. Code Generation

Language-specific generators translate IR to code:
- `codegen_python.py` - Python code generation
- `codegen_julia.py` - Julia code generation

### EBNF Operators

Star and Option are handled directly without grammar transformation:

**Star (A*)**: Generated as a while loop collecting results into a list

**Option (A?)**: Generated as an if statement with lookahead check

### LL(k) Prediction

When multiple productions exist, decision trees use lookahead:

```python
# Grammar: expr -> "(" "add" term term ")" | "(" "sub" term term ")"
# Generated decision logic:

if lookahead(0) == "(":
    if lookahead(1) == "add":
        # Parse first alternative
    elif lookahead(1) == "sub":
        # Parse second alternative
```

The value of k increases incrementally until alternatives can be distinguished.

## Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/meta/

# Grammar generation tests
python -m pytest tests/meta/test_grammar.py
python -m pytest tests/meta/test_grammar_gen.py

# Parser generation tests
python -m pytest tests/meta/test_parser_gen.py
```

## Module Dependencies

```
cli.py
  ├── proto_parser.py
  │   └── proto_ast.py
  ├── proto_print.py
  ├── grammar_gen.py
  │   ├── proto_parser.py
  │   ├── proto_ast.py
  │   ├── grammar.py
  │   ├── grammar_gen_builtins.py
  │   └── grammar_gen_rewrites.py
  ├── parser_gen.py
  │   ├── grammar.py
  │   ├── grammar_analysis.py
  │   ├── grammar_utils.py
  │   ├── terminal_sequence_set.py
  │   ├── target.py
  │   └── gensym.py
  ├── parser_gen_python.py
  │   ├── parser_gen.py
  │   └── codegen_python.py
  └── parser_gen_julia.py
      ├── parser_gen.py
      └── codegen_julia.py
```

## Implementation Notes

### Target IR

Parser generation uses a two-stage approach:
1. Generate language-independent IR (target.py)
2. Translate IR to target language (codegen_*.py)

This enables:
- Shared parser generation logic
- Easier addition of new target languages
- Language-specific optimization opportunities

### LL(k) Analysis

The `terminal_sequence_set.py` module provides lazy LL(k) computation:
- Starts with k=1
- Incrementally expands to higher k when needed
- Avoids expensive computation when simple lookahead suffices

### Grammar Analysis

The `grammar_analysis.py` module uses `@cached_property` for lazy evaluation:
- Reachability, nullable, FIRST, and FOLLOW computed on demand
- Results cached for efficiency
- Static methods available for testing

## Future Work

- Complete Julia parser generator testing
- Implement pretty-printer generators
- Add error recovery mechanisms
- Optimize decision tree generation
