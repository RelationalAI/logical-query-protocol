package lqp

import (
	"io"
	"strconv"
	"strings"
	"text/scanner"
	"unicode"
)

// Lexer for LQP files.

type Token struct {
	Type   TokenType
	Value  string
	Line   int
	Column int
}

type TokenType int

const (
	TokenEOF TokenType = iota
	TokenLParen
	TokenRParen
	TokenLBracket
	TokenRBracket
	TokenLBrace
	TokenRBrace
	TokenColon
	TokenBinding
	TokenPipe
	TokenSpecialized
	TokenSymbol
	TokenString
	TokenNumber
	TokenFloat
	TokenUInt128
	TokenInt128
	TokenDecimal
	TokenBoolean
	TokenMissing
	TokenComment
)

func (t TokenType) String() string {
	switch t {
	case TokenEOF:
		return "EOF"
	case TokenLParen:
		return "("
	case TokenRParen:
		return ")"
	case TokenLBracket:
		return "["
	case TokenRBracket:
		return "]"
	case TokenLBrace:
		return "{"
	case TokenRBrace:
		return "}"
	case TokenColon:
		return ":"
	case TokenBinding:
		return "::"
	case TokenPipe:
		return "|"
	case TokenSpecialized:
		return "#"
	case TokenSymbol:
		return "SYMBOL"
	case TokenString:
		return "STRING"
	case TokenNumber:
		return "NUMBER"
	case TokenFloat:
		return "FLOAT"
	case TokenUInt128:
		return "UINT128"
	case TokenInt128:
		return "INT128"
	case TokenDecimal:
		return "DECIMAL"
	case TokenBoolean:
		return "BOOLEAN"
	case TokenMissing:
		return "MISSING"
	case TokenComment:
		return "COMMENT"
	default:
		return "Unknown"
	}
}

type Lexer struct {
	scanner scanner.Scanner
	file    string
}

func NewLexer(r io.Reader, file string) *Lexer {
	var s scanner.Scanner
	s.Init(r)
	s.Mode = scanner.ScanIdents | scanner.ScanFloats | scanner.ScanStrings | scanner.ScanComments
	s.Whitespace = 1<<'\t' | 1<<'\n' | 1<<'\r' | 1<<' '
	s.IsIdentRune = func(ch rune, i int) bool {
		return ch == '_' || ch == '-' || ch == '.' || unicode.IsLetter(ch) || (unicode.IsDigit(ch) && i > 0)
	}

	return &Lexer{
		scanner: s,
		file:    file,
	}
}

func (l *Lexer) Next() Token {
	for {
		tok := l.scanner.Scan()
		line := l.scanner.Position.Line
		col := l.scanner.Position.Column
		text := l.scanner.TokenText()

		switch tok {
		case scanner.EOF:
			return Token{Type: TokenEOF, Line: line, Column: col}

		case scanner.Comment: // scanner internal comment
			continue

		case '(':
			return Token{Type: TokenLParen, Value: text, Line: line, Column: col}
		case ')':
			return Token{Type: TokenRParen, Value: text, Line: line, Column: col}
		case '[':
			return Token{Type: TokenLBracket, Value: text, Line: line, Column: col}
		case ']':
			return Token{Type: TokenRBracket, Value: text, Line: line, Column: col}
		case '{':
			return Token{Type: TokenLBrace, Value: text, Line: line, Column: col}
		case '}':
			return Token{Type: TokenRBrace, Value: text, Line: line, Column: col}
		case '|':
			return Token{Type: TokenPipe, Value: text, Line: line, Column: col}
		case '#':
			return Token{Type: TokenSpecialized, Value: text, Line: line, Column: col}

		case ':':
			next := l.scanner.Peek()
			if next == ':' {
				l.scanner.Next()
				return Token{Type: TokenBinding, Value: "::", Line: line, Column: col}
			}
			return Token{Type: TokenColon, Value: text, Line: line, Column: col}

		case scanner.String:
			// Remove quotes and process escape sequences
			unquoted, err := strconv.Unquote(text)
			if err != nil {
				unquoted = text[1 : len(text)-1]
			}
			return Token{Type: TokenString, Value: unquoted, Line: line, Column: col}

		case scanner.Int, scanner.Float:
			return l.classifyNumber(text, line, col)

		case scanner.Ident:
			return l.classifyIdent(text, line, col)

		case ';':
			// Handle ;; comments manually
			next := l.scanner.Peek()
			if next == ';' {
				// Skip rest of line
				for {
					ch := l.scanner.Next()
					if ch == '\n' || ch == scanner.EOF {
						break
					}
				}
				continue
			}
			fallthrough

		// Checks for < or <= syntactic sugar
		case '<':
			if l.scanner.Peek() == '=' {
				l.scanner.Next()
				return Token{Type: TokenSymbol, Value: "<=", Line: line, Column: col}
			}
			return Token{Type: TokenSymbol, Value: text, Line: line, Column: col}

		// Checks for > or >= syntactic sugar
		case '>':
			if l.scanner.Peek() == '=' {
				l.scanner.Next()
				return Token{Type: TokenSymbol, Value: ">=", Line: line, Column: col}
			}
			return Token{Type: TokenSymbol, Value: text, Line: line, Column: col}

		// Includes ops such as +, -, =, etc.
		default:
			return Token{Type: TokenSymbol, Value: text, Line: line, Column: col}
		}
	}
}

func (l *Lexer) classifyNumber(text string, line, col int) Token {
	// Check for int128
	if strings.HasPrefix(text, "0x") {
		return Token{Type: TokenUInt128, Value: text, Line: line, Column: col}
	}

	// Check for i128 suffix - need to read ahead
	if ch := l.scanner.Peek(); ch == 'i' {
		l.scanner.Next()
		if l.scanner.Peek() == '1' {
			l.scanner.Next()
			if l.scanner.Peek() == '2' {
				l.scanner.Next()
				if l.scanner.Peek() == '8' {
					l.scanner.Next()
					text = text + "i128"
					return Token{Type: TokenInt128, Value: text, Line: line, Column: col}
				}
			}
		}
	}

	// Check for decimal format (e.g., "123.456d12") or float
	if strings.Contains(text, ".") {
		if ch := l.scanner.Peek(); ch == 'd' {
			l.scanner.Next()
			// Read the precision digits
			precText := ""
			for {
				ch := l.scanner.Peek()
				if ch >= '0' && ch <= '9' {
					precText += string(l.scanner.Next())
				} else {
					break
				}
			}
			if precText != "" {
				text = text + "d" + precText
				return Token{Type: TokenDecimal, Value: text, Line: line, Column: col}
			}
		}
		return Token{Type: TokenFloat, Value: text, Line: line, Column: col}
	}
	return Token{Type: TokenNumber, Value: text, Line: line, Column: col}
}

func (l *Lexer) classifyIdent(text string, line, col int) Token {
	switch text {
	case "true", "false":
		return Token{Type: TokenBoolean, Value: text, Line: line, Column: col}
	case "missing":
		return Token{Type: TokenMissing, Value: text, Line: line, Column: col}
	case "inf", "nan":
		return Token{Type: TokenFloat, Value: text, Line: line, Column: col}
	default:
		return Token{Type: TokenSymbol, Value: text, Line: line, Column: col}
	}
}
