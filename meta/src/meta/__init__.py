"""Meta-language tools for translating protobuf specification into parsers and pretty printers.

This package provides tools for:
- Parsing protobuf specifications
- Generating context-free grammars with semantic actions
- Generating parsers from the grammar
- Generating pretty printers from the grammar
"""

# Target language AST
from .codegen_julia import (
    escape_identifier as escape_julia_identifier,
)

# Julia code generation
from .codegen_julia import (
    generate_julia,
    generate_julia_def,
    generate_julia_lines,
)
from .codegen_python import (
    escape_identifier as escape_python_identifier,
)

# Python code generation
from .codegen_python import (
    generate_python,
    generate_python_lines,
)

# Grammar data structures
from .grammar import (
    Grammar,
    LitTerminal,
    NamedTerminal,
    Nonterminal,
    Option,
    Rhs,
    Rule,
    Star,
    Terminal,
    Token,
)

# Parser generation
from .parser_gen import (
    AmbiguousGrammarError,
    GrammarConflictError,
    generate_parse_functions,
)
from .parser_gen_julia import generate_parser_julia
from .parser_gen_python import generate_parser_python

# Protobuf AST
from .proto_ast import (
    ProtoEnum,
    ProtoField,
    ProtoMessage,
    ProtoOneof,
)

# Protobuf parser
from .proto_parser import ProtoParser
from .target import (
    Assign,
    BaseType,
    Builtin,
    Call,
    FunDef,
    IfElse,
    Lambda,
    Let,
    ListType,
    Lit,
    ParseNonterminal,
    ParseNonterminalDef,
    PrintNonterminal,
    PrintNonterminalDef,
    Seq,
    SequenceType,
    Symbol,
    TargetExpr,
    TargetNode,
    TargetType,
    TupleType,
    Var,
    While,
)

__all__ = [
    # Target language AST
    "TargetNode",
    "TargetExpr",
    "Var",
    "Lit",
    "Symbol",
    "Builtin",
    "Call",
    "Lambda",
    "Let",
    "IfElse",
    "Seq",
    "While",
    "Assign",
    "TargetType",
    "BaseType",
    "TupleType",
    "SequenceType",
    "ListType",
    "FunDef",
    "ParseNonterminalDef",
    "PrintNonterminalDef",
    "ParseNonterminal",
    "PrintNonterminal",
    # Grammar
    "Grammar",
    "Rule",
    "Token",
    "Rhs",
    "Terminal",
    "LitTerminal",
    "NamedTerminal",
    "Nonterminal",
    "Star",
    "Option",
    # Protobuf AST
    "ProtoField",
    "ProtoOneof",
    "ProtoEnum",
    "ProtoMessage",
    # Protobuf parser
    "ProtoParser",
    # Parser generation
    "generate_parse_functions",
    "GrammarConflictError",
    "AmbiguousGrammarError",
    "generate_parser_python",
    "generate_parser_julia",
    # Python code generation
    "generate_python",
    "generate_python_lines",
    "escape_python_identifier",
    # Julia code generation
    "generate_julia",
    "generate_julia_lines",
    "generate_julia_def",
    "escape_julia_identifier",
]
