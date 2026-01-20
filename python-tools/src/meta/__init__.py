"""Meta-language tools for grammar generation and code synthesis.

This package provides tools for:
- Parsing protobuf specifications
- Generating context-free grammars with semantic actions
- Grammar normalization and left-factoring
- Code generation for parsers and pretty printers
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
    VisitNonterminalDef,
    VisitNonterminal,
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

# Code generation from actions
from .codegen_python import generate_python_lines, generate_python, escape_identifier as escape_python_identifier
from .codegen_julia import generate_julia, generate_julia_lines, generate_julia_def, escape_identifier as escape_julia_identifier

# Parser generation
from .parser_gen_python import generate_parser_python
from .parser_gen_julia import generate_parser_julia

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
    'VisitNonterminalDef',
    'VisitNonterminal',
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
    # Code generation from actions
    'generate_python_lines',
    'generate_python',
    'escape_python_identifier',
    'generate_julia',
    'generate_julia_lines',
    'generate_julia_def',
    'escape_julia_identifier',
    # Parser generation
    'generate_parser_python',
    'generate_parser_julia',
]
