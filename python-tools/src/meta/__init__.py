"""Meta-language tools for grammar generation.

This package provides tools for:
- Parsing protobuf specifications
- Generating context-free grammars with semantic actions
- Grammar normalization and left-factoring
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
    generate_grammar,
    generate_semantic_actions,
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
    'generate_grammar',
    'generate_semantic_actions',
]
