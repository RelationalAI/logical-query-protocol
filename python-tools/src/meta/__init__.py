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
]
