@testsetup module ParserSetup

using LogicalQueryProtocol: Proto
using LogicalQueryProtocol: Parser

# NOTE: We do NOT export `parse` because it conflicts with `Base.parse`.
# Tests should use `Parser.parse(...)` instead.
using LogicalQueryProtocol.Parser:
    ParseError, Lexer,
    scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal

export Proto, Parser,
    ParseError, Lexer,
    scan_string, scan_int, scan_float, scan_int128, scan_uint128, scan_decimal

end
