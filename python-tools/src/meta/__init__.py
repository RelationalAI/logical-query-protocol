"""Meta-language tools for translating protobuf specification into parsers and pretty printers.

This package provides tools for:
- Parsing protobuf specifications
- Generating context-free grammars with semantic actions
- Generating parsers from the grammar
- Generating pretty printers from the grammar
"""

# Target language AST
from .target import (
    TargetNode,
    TargetExpr,
    Var,
    Lit,
    Symbol,
    Builtin,
    Call,
    Lambda,
    Let,
    IfElse,
    Seq,
    While,
    Assign,
    TargetType,
    BaseType,
    TupleType,
    ListType,
    FunDef,
)

# Grammar data structures
from .grammar import (
    Grammar,
    Rule,
    Token,
    Rhs,
    Terminal,
    LitTerminal,
    NamedTerminal,
    Nonterminal,
    Star,
    Option,
)

# Protobuf AST
from .proto_ast import (
    ProtoField,
    ProtoOneof,
    ProtoEnum,
    ProtoMessage,
)

# Protobuf parser
from .proto_parser import ProtoParser

# Grammar generation
from .grammar_gen import (
    GrammarGenerator,
    generate_grammar,
)

# Python code generation
from .codegen_python import (
    generate_python,
    generate_python_lines,
    escape_identifier as escape_python_identifier,
)

# Julia code generation
from .codegen_julia import (
    generate_julia,
    generate_julia_lines,
    generate_julia_def,
    escape_identifier as escape_julia_identifier,
)

__all__ = [
    # Target language AST
    'TargetNode',
    'TargetExpr',
    'Var',
    'Lit',
    'Symbol',
    'Builtin',
    'Call',
    'Lambda',
    'Let',
    'IfElse',
    'Seq',
    'While',
    'Assign',
    'TargetType',
    'BaseType',
    'TupleType',
    'ListType',
    'FunDef',
    # Grammar
    'Grammar',
    'Rule',
    'Token',
    'Rhs',
    'Terminal',
    'LitTerminal',
    'NamedTerminal',
    'Nonterminal',
    'Star',
    'Option',
    # Protobuf AST
    'ProtoField',
    'ProtoOneof',
    'ProtoEnum',
    'ProtoMessage',
    # Protobuf parser
    'ProtoParser',
    # Grammar generation
    'GrammarGenerator',
    'generate_grammar',
    # Python code generation
    'generate_python',
    'generate_python_lines',
    'escape_python_identifier',
    # Julia code generation
    'generate_julia',
    'generate_julia_lines',
    'generate_julia_def',
    'escape_julia_identifier',
]
