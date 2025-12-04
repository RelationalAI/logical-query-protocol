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
    TryCatch,
    Assign,
    Type,
    BaseType,
    TupleType,
    ListType,
    FunDef,
    ParseNonterminalDef,
    ParseNonterminal,
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
    Plus,
    Option,
)

# Protobuf AST
from .proto_ast import (
    PRIMITIVE_TYPES,
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
    parse_action,
    generate_grammar,
    generate_semantic_actions,
)

# Code generation from actions
from .codegen_python import generate_python_lines, escape_identifier as escape_python_identifier
from .codegen_julia import generate_julia, escape_identifier as escape_julia_identifier
from .codegen_go import generate_go, escape_identifier as escape_go_identifier

# Parser and printer generation
from .parser_gen_python import generate_parser_python
from .printer_python import generate_pretty_printer_python

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
    'TryCatch',
    'Assign',
    'Type',
    'BaseType',
    'TupleType',
    'ListType',
    'FunDef',
    'ParseNonterminalDef',
    'ParseNonterminal',
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
    'Plus',
    'Option',
    # Protobuf AST
    'PRIMITIVE_TYPES',
    'ProtoField',
    'ProtoOneof',
    'ProtoEnum',
    'ProtoMessage',
    # Protobuf parser
    'ProtoParser',
    # Grammar generation
    'GrammarGenerator',
    'parse_action',
    'generate_grammar',
    'generate_semantic_actions',
    # Code generation from actions
    'generate_python',
    'escape_python_identifier',
    'generate_julia',
    'escape_julia_identifier',
    'generate_go',
    'escape_go_identifier',
    # Parser and printer generation
    'generate_parser_python',
    'generate_pretty_printer_python',
]
