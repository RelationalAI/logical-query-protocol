// Auto-generated LL(k) recursive-descent parser.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the parser, edit the generator code
// in `meta/` or edit the protobuf specification in `proto/v1`.
//
// Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --parser go

package lqp

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"math"
	"math/big"
	"reflect"
	"regexp"
	"strconv"
	"strings"

	pb "github.com/RelationalAI/logical-query-protocol/sdks/go/src/lqp/v1"
	"google.golang.org/protobuf/reflect/protoreflect"
)

// Location represents a source location (1-based line/column, 0-based byte offset).
type Location struct {
	Line   int
	Column int
	Offset int
}

// Span represents a source span from start to stop location.
type Span struct {
	Start    Location
	Stop     Location
	TypeName string
}

// ParseError represents a parse error
type ParseError struct {
	msg string
}

func (e ParseError) Error() string {
	return e.msg
}

func ptr[T any](v T) *T { return &v }

func deref[T any](p *T, d T) T {
	if p != nil {
		return *p
	}
	return d
}

// tokenKind discriminates which field of TokenValue is active.
type tokenKind int

const (
	kindString tokenKind = iota
	kindInt64
	kindInt32
	kindUint32
	kindFloat64
	kindFloat32
	kindUint128
	kindInt128
	kindDecimal
)

// TokenValue holds a typed token value.
type TokenValue struct {
	kind    tokenKind
	str     string
	i64     int64
	i32     int32
	u32     uint32
	f64     float64
	f32     float32
	uint128 *pb.UInt128Value
	int128  *pb.Int128Value
	decimal *pb.DecimalValue
}

func (tv TokenValue) String() string {
	switch tv.kind {
	case kindInt64:
		return strconv.FormatInt(tv.i64, 10)
	case kindInt32:
		return fmt.Sprintf("%di32", tv.i32)
	case kindUint32:
		return fmt.Sprintf("%du32", tv.u32)
	case kindFloat64:
		return strconv.FormatFloat(tv.f64, 'g', -1, 64)
	case kindFloat32:
		return fmt.Sprintf("%sf32", strconv.FormatFloat(float64(tv.f32), 'g', -1, 32))
	case kindUint128:
		return fmt.Sprintf("0x%016x%016x", tv.uint128.High, tv.uint128.Low)
	case kindInt128:
		return fmt.Sprintf("%v", tv.int128)
	case kindDecimal:
		return fmt.Sprintf("%v", tv.decimal)
	default:
		return tv.str
	}
}

// Token represents a lexer token
type Token struct {
	Type     string
	Value    TokenValue
	StartPos int
	EndPos   int
}

// Pos returns the start position for backwards compatibility.
func (t Token) Pos() int { return t.StartPos }

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, %v, %d)", t.Type, t.Value, t.StartPos)
}

// tokenSpec represents a token specification for the lexer
type tokenSpec struct {
	name   string
	regex  *regexp.Regexp
	action func(string) TokenValue
}

var (
	whitespaceRe = regexp.MustCompile(`^\s+`)
	commentRe    = regexp.MustCompile(`^;;.*`)
	tokenSpecs   = []tokenSpec{
		{"LITERAL", regexp.MustCompile(`^::`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^<=`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^>=`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\#`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\(`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\)`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\*`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\+`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\-`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^/`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^:`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^<`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^=`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^>`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\[`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\]`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\{`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\|`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"LITERAL", regexp.MustCompile(`^\}`), func(s string) TokenValue { return TokenValue{kind: kindString, str: s} }},
		{"DECIMAL", regexp.MustCompile(`^[-]?\d+\.\d+d\d+`), func(s string) TokenValue { return TokenValue{kind: kindDecimal, decimal: scanDecimal(s)} }},
		{"FLOAT", regexp.MustCompile(`^([-]?\d+\.\d+|inf|nan)`), func(s string) TokenValue { return TokenValue{kind: kindFloat64, f64: scanFloat(s)} }},
		{"FLOAT32", regexp.MustCompile(`^[-]?\d+\.\d+f32`), func(s string) TokenValue { return TokenValue{kind: kindFloat32, f32: scanFloat32(s)} }},
		{"INT", regexp.MustCompile(`^[-]?\d+`), func(s string) TokenValue { return TokenValue{kind: kindInt64, i64: scanInt(s)} }},
		{"INT32", regexp.MustCompile(`^[-]?\d+i32`), func(s string) TokenValue { return TokenValue{kind: kindInt32, i32: scanInt32(s)} }},
		{"UINT32", regexp.MustCompile(`^\d+u32`), func(s string) TokenValue { return TokenValue{kind: kindUint32, u32: scanUint32(s)} }},
		{"INT128", regexp.MustCompile(`^[-]?\d+i128`), func(s string) TokenValue { return TokenValue{kind: kindInt128, int128: scanInt128(s)} }},
		{"STRING", regexp.MustCompile(`^"(?:[^"\\]|\\.)*"`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanString(s)} }},
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_./#-]*`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanSymbol(s)} }},
		{"UINT128", regexp.MustCompile(`^0x[0-9a-fA-F]+`), func(s string) TokenValue { return TokenValue{kind: kindUint128, uint128: scanUint128(s)} }},
	}
)

// Lexer tokenizes input
type Lexer struct {
	input  string
	pos    int
	tokens []Token
}

// NewLexer creates a new lexer and tokenizes the input
func NewLexer(input string) *Lexer {
	l := &Lexer{
		input:  input,
		pos:    0,
		tokens: make([]Token, 0),
	}
	l.tokenize()
	return l
}

func (l *Lexer) tokenize() {
	for l.pos < len(l.input) {
		remaining := l.input[l.pos:]

		// Skip whitespace
		if m := whitespaceRe.FindString(remaining); m != "" {
			l.pos += len(m)
			continue
		}

		// Skip comments
		if m := commentRe.FindString(remaining); m != "" {
			l.pos += len(m)
			continue
		}

		// Collect all matching tokens
		type candidate struct {
			tokenType string
			value     string
			action    func(string) TokenValue
			endPos    int
		}
		var candidates []candidate

		for _, spec := range tokenSpecs {
			if loc := spec.regex.FindStringIndex(remaining); loc != nil && loc[0] == 0 {
				value := remaining[:loc[1]]
				candidates = append(candidates, candidate{
					tokenType: spec.name,
					value:     value,
					action:    spec.action,
					endPos:    l.pos + loc[1],
				})
			}
		}

		if len(candidates) == 0 {
			panic(ParseError{msg: fmt.Sprintf("Unexpected character at position %d: %q", l.pos, string(l.input[l.pos]))})
		}

		// Pick the longest match
		best := candidates[0]
		for _, c := range candidates[1:] {
			if c.endPos > best.endPos {
				best = c
			}
		}

		l.tokens = append(l.tokens, Token{
			Type:     best.tokenType,
			Value:    best.action(best.value),
			StartPos: l.pos,
			EndPos:   best.endPos,
		})
		l.pos = best.endPos
	}

	l.tokens = append(l.tokens, Token{Type: "$", Value: TokenValue{}, StartPos: l.pos, EndPos: l.pos})
}

// Scanner functions for each token type

func scanSymbol(s string) string {
	return s
}

func scanString(s string) string {
	unquoted, err := strconv.Unquote(s)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid string literal: %s", s)})
	}
	return unquoted
}

func scanInt(s string) int64 {
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid integer: %s", s)})
	}
	return n
}

func scanInt32(s string) int32 {
	numStr := s[:len(s)-3] // Remove "i32" suffix
	n, err := strconv.ParseInt(numStr, 10, 32)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid int32: %s", s)})
	}
	return int32(n)
}

func scanUint32(s string) uint32 {
	numStr := s[:len(s)-3] // Remove "u32" suffix
	n, err := strconv.ParseUint(numStr, 10, 32)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid uint32: %s", s)})
	}
	return uint32(n)
}

func scanFloat32(s string) float32 {
	numStr := s[:len(s)-3] // Remove "f32" suffix
	f, err := strconv.ParseFloat(numStr, 32)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid float32: %s", s)})
	}
	return float32(f)
}

func scanFloat(s string) float64 {
	if s == "inf" {
		return math.Inf(1)
	} else if s == "nan" {
		return math.NaN()
	}
	f, err := strconv.ParseFloat(s, 64)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid float: %s", s)})
	}
	return f
}

func scanUint128(s string) *pb.UInt128Value {
	hexStr := s[2:]
	n := new(big.Int)
	if _, ok := n.SetString(hexStr, 16); !ok {
		panic(ParseError{msg: fmt.Sprintf("Invalid uint128: %s", s)})
	}
	mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
	low := new(big.Int).And(n, mask).Uint64()
	high := new(big.Int).Rsh(n, 64).Uint64()
	return &pb.UInt128Value{Low: low, High: high}
}

func scanInt128(s string) *pb.Int128Value {
	numStr := s[:len(s)-4]
	n := new(big.Int)
	if _, ok := n.SetString(numStr, 10); !ok {
		panic(ParseError{msg: fmt.Sprintf("Invalid int128: %s", s)})
	}

	var low, high uint64
	if n.Sign() >= 0 {
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(n, mask).Uint64()
		high = new(big.Int).Rsh(n, 64).Uint64()
	} else {
		twoTo128 := new(big.Int).Lsh(big.NewInt(1), 128)
		unsigned := new(big.Int).Add(n, twoTo128)
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(unsigned, mask).Uint64()
		high = new(big.Int).Rsh(unsigned, 64).Uint64()
	}
	return &pb.Int128Value{Low: low, High: high}
}

func scanDecimal(s string) *pb.DecimalValue {
	parts := strings.Split(s, "d")
	if len(parts) != 2 {
		panic(ParseError{msg: fmt.Sprintf("Invalid decimal format: %s", s)})
	}
	decParts := strings.Split(parts[0], ".")
	scale := int32(0)
	if len(decParts) == 2 {
		scale = int32(len(decParts[1]))
	}
	precision, err := strconv.ParseInt(parts[1], 10, 32)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid decimal precision: %s", s)})
	}

	intStr := strings.ReplaceAll(parts[0], ".", "")
	n := new(big.Int)
	if _, ok := n.SetString(intStr, 10); !ok {
		panic(ParseError{msg: fmt.Sprintf("Invalid decimal value: %s", s)})
	}

	var low, high uint64
	if n.Sign() >= 0 {
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(n, mask).Uint64()
		high = new(big.Int).Rsh(n, 64).Uint64()
	} else {
		twoTo128 := new(big.Int).Lsh(big.NewInt(1), 128)
		unsigned := new(big.Int).Add(n, twoTo128)
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(unsigned, mask).Uint64()
		high = new(big.Int).Rsh(unsigned, 64).Uint64()
	}
	value := &pb.Int128Value{Low: low, High: high}
	return &pb.DecimalValue{Precision: int32(precision), Scale: scale, Value: value}
}

// relationIdKey is used as a map key for RelationIds
type relationIdKey struct {
	Low  uint64
	High uint64
}

func computeLineStarts(text string) []int {
	starts := []int{0}
	for i, ch := range text {
		if ch == '\n' {
			starts = append(starts, i+1)
		}
	}
	return starts
}

// Parser is an LL(k) recursive-descent parser
type Parser struct {
	tokens            []Token
	pos               int
	idToDebugInfo     map[string]map[relationIdKey]string
	currentFragmentID []byte
	Provenance        map[int]Span
	lineStarts        []int
}

// NewParser creates a new parser
func NewParser(tokens []Token, input string) *Parser {
	return &Parser{
		tokens:            tokens,
		pos:               0,
		idToDebugInfo:     make(map[string]map[relationIdKey]string),
		currentFragmentID: nil,
		Provenance:        make(map[int]Span),
		lineStarts:        computeLineStarts(input),
	}
}

func (p *Parser) makeLocation(offset int) Location {
	lo, hi := 0, len(p.lineStarts)
	for lo < hi {
		mid := (lo + hi) / 2
		if p.lineStarts[mid] <= offset {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	lineIdx := lo - 1
	col := offset - p.lineStarts[lineIdx]
	return Location{Line: lineIdx + 1, Column: col + 1, Offset: offset}
}

func (p *Parser) spanStart() int {
	return p.lookahead(0).StartPos
}

func (p *Parser) recordSpan(startOffset int, typeName string) {
	// First-wins: innermost parse function records first; outer wrappers
	// that share the same offset do not overwrite.
	if _, exists := p.Provenance[startOffset]; exists {
		return
	}
	endOffset := startOffset
	if p.pos > 0 {
		endOffset = p.tokens[p.pos-1].EndPos
	}
	s := Span{
		Start:    p.makeLocation(startOffset),
		Stop:     p.makeLocation(endOffset),
		TypeName: typeName,
	}
	p.Provenance[startOffset] = s
}

func (p *Parser) lookahead(k int) Token {
	idx := p.pos + k
	if idx < len(p.tokens) {
		return p.tokens[idx]
	}
	return Token{Type: "$", Value: TokenValue{}, StartPos: -1, EndPos: -1}
}

func (p *Parser) consumeLiteral(expected string) {
	if !p.matchLookaheadLiteral(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected literal %q but got %s=`%v` at position %d", expected, token.Type, token.Value, token.StartPos)})
	}
	p.pos++
}

func (p *Parser) consumeTerminal(expected string) Token {
	if !p.matchLookaheadTerminal(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected terminal %s but got %s=`%v` at position %d", expected, token.Type, token.Value, token.StartPos)})
	}
	token := p.lookahead(0)
	p.pos++
	return token
}

func (p *Parser) matchLookaheadLiteral(literal string, k int) bool {
	token := p.lookahead(k)
	// Support soft keywords: alphanumeric literals are lexed as SYMBOL tokens
	if token.Type == "LITERAL" && token.Value.str == literal {
		return true
	}
	if token.Type == "SYMBOL" && token.Value.str == literal {
		return true
	}
	return false
}

func (p *Parser) matchLookaheadTerminal(terminal string, k int) bool {
	token := p.lookahead(k)
	return token.Type == terminal
}

func (p *Parser) startFragment(fragmentID *pb.FragmentId) *pb.FragmentId {
	p.currentFragmentID = fragmentID.Id
	return fragmentID
}

func (p *Parser) relationIdFromString(name string) *pb.RelationId {
	hash := sha256.Sum256([]byte(name))
	// Use big-endian and the lower 128 bits of the hash, consistent with pyrel.
	high := binary.BigEndian.Uint64(hash[16:24])
	low := binary.BigEndian.Uint64(hash[24:32])
	relationId := &pb.RelationId{IdLow: low, IdHigh: high}

	// Store the mapping for the current fragment if we're inside one
	if p.currentFragmentID != nil {
		fragKey := string(p.currentFragmentID)
		if _, ok := p.idToDebugInfo[fragKey]; !ok {
			p.idToDebugInfo[fragKey] = make(map[relationIdKey]string)
		}
		idKey := relationIdKey{Low: low, High: high}
		p.idToDebugInfo[fragKey][idKey] = name
	}

	return relationId
}

func (p *Parser) constructFragment(fragmentID *pb.FragmentId, declarations []*pb.Declaration) *pb.Fragment {
	fragKey := string(fragmentID.Id)
	debugInfoMap := p.idToDebugInfo[fragKey]

	var ids []*pb.RelationId
	var origNames []string
	for idKey, name := range debugInfoMap {
		ids = append(ids, &pb.RelationId{IdLow: idKey.Low, IdHigh: idKey.High})
		origNames = append(origNames, name)
	}

	debugInfo := &pb.DebugInfo{Ids: ids, OrigNames: origNames}
	p.currentFragmentID = nil
	return &pb.Fragment{Id: fragmentID, Declarations: declarations, DebugInfo: debugInfo}
}

func (p *Parser) relationIdToString(msg *pb.RelationId) string {
	key := relationIdKey{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
	for _, debugInfoMap := range p.idToDebugInfo {
		if name, ok := debugInfoMap[key]; ok {
			return name
		}
	}
	return ""
}

func (p *Parser) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
}

// Helper functions
func dictFromList(pairs [][]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for _, pair := range pairs {
		if len(pair) >= 2 {
			result[pair[0].(string)] = pair[1]
		}
	}
	return result
}

// dictGetValue retrieves a Value from the config dict with type assertion
func dictGetValue(m map[string]interface{}, key string) *pb.Value {
	if v, ok := m[key]; ok {
		if val, ok := v.(*pb.Value); ok {
			return val
		}
	}
	return nil
}

func listConcat[T any](a []T, b []T) []T {
	if b == nil {
		return a
	}
	result := make([]T, len(a)+len(b))
	copy(result, a)
	copy(result[len(a):], b)
	return result
}

// hasProtoField checks if a proto message field is populated.
// Uses the proto reflection API for correct oneof detection.
func hasProtoField(msg interface{}, fieldName string) bool {
	if msg == nil {
		return false
	}
	if pm, ok := msg.(protoreflect.ProtoMessage); ok {
		m := pm.ProtoReflect()
		fd := m.Descriptor().Fields().ByName(protoreflect.Name(fieldName))
		if fd != nil {
			return m.Has(fd)
		}
	}
	// Fallback: getter-based reflection for non-proto types.
	val := reflect.ValueOf(msg)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}
	if val.Kind() != reflect.Struct {
		return false
	}
	methodName := "Get" + toPascalCase(fieldName)
	method := reflect.ValueOf(msg).MethodByName(methodName)
	if !method.IsValid() {
		return false
	}
	results := method.Call(nil)
	if len(results) == 0 {
		return false
	}
	result := results[0]
	if result.Kind() == reflect.Ptr || result.Kind() == reflect.Interface {
		return !result.IsNil()
	}
	return true
}

func toPascalCase(s string) string {
	parts := strings.Split(s, "_")
	for i, part := range parts {
		if len(part) > 0 {
			parts[i] = strings.ToUpper(part[:1]) + part[1:]
		}
	}
	return strings.Join(parts, "")
}

// --- Helper functions ---

func (p *Parser) _extract_value_int32(value *pb.Value, default_ int64) int32 {
	var _t1913 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1913
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1914 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1914
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1915 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1915
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1916 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1916
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1917 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1917
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1918 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1918
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1919 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1919
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1920 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1920
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1921 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1921
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1922 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1922
	_t1923 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1923
	_t1924 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1924
	_t1925 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1925
	_t1926 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1926
	_t1927 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1927
	_t1928 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1928
	_t1929 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1929
	_t1930 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1930
	_t1931 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1931
	_t1932 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1932
	_t1933 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1933
	_t1934 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1934
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1935 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1935
	_t1936 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1936
	_t1937 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1937
	_t1938 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1938
	_t1939 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1939
	_t1940 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1940
	_t1941 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1941
	_t1942 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1942
	_t1943 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1943
	_t1944 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1944.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1944.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1944
	_t1945 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1945
}

func (p *Parser) default_configure() *pb.Configure {
	_t1946 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1946
	_t1947 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1947
}

func (p *Parser) construct_configure(config_dict [][]interface{}) *pb.Configure {
	config := dictFromList(config_dict)
	maintenance_level_val := dictGetValue(config, "ivm.maintenance_level")
	maintenance_level := pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
	if (maintenance_level_val != nil && hasProtoField(maintenance_level_val, "string_value")) {
		if maintenance_level_val.GetStringValue() == "off" {
			maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
		} else {
			if maintenance_level_val.GetStringValue() == "auto" {
				maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO
			} else {
				if maintenance_level_val.GetStringValue() == "all" {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL
				} else {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
				}
			}
		}
	}
	_t1948 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1948
	_t1949 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1949
	_t1950 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1950
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1951 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1951
	_t1952 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1952
	_t1953 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1953
	_t1954 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1954
	_t1955 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1955
	_t1956 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1956
	_t1957 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1957
	_t1958 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1958
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1959 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1959
}

func (p *Parser) construct_iceberg_config(catalog_uri string, scope *string, properties [][]interface{}, credentials [][]interface{}) *pb.IcebergConfig {
	_t1960 := properties
	if properties == nil {
		_t1960 = [][]interface{}{}
	}
	props := dictFromList(_t1960)
	_t1961 := credentials
	if credentials == nil {
		_t1961 = [][]interface{}{}
	}
	creds := dictFromList(_t1961)
	_t1962 := &pb.IcebergConfig{CatalogUri: catalog_uri, Scope: deref(scope, ""), Properties: props, Credentials: creds}
	return _t1962
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start618 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1224 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1225 := p.parse_configure()
		_t1224 = _t1225
	}
	configure612 := _t1224
	var _t1226 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1227 := p.parse_sync()
		_t1226 = _t1227
	}
	sync613 := _t1226
	xs614 := []*pb.Epoch{}
	cond615 := p.matchLookaheadLiteral("(", 0)
	for cond615 {
		_t1228 := p.parse_epoch()
		item616 := _t1228
		xs614 = append(xs614, item616)
		cond615 = p.matchLookaheadLiteral("(", 0)
	}
	epochs617 := xs614
	p.consumeLiteral(")")
	_t1229 := p.default_configure()
	_t1230 := configure612
	if configure612 == nil {
		_t1230 = _t1229
	}
	_t1231 := &pb.Transaction{Epochs: epochs617, Configure: _t1230, Sync: sync613}
	result619 := _t1231
	p.recordSpan(int(span_start618), "Transaction")
	return result619
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start621 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1232 := p.parse_config_dict()
	config_dict620 := _t1232
	p.consumeLiteral(")")
	_t1233 := p.construct_configure(config_dict620)
	result622 := _t1233
	p.recordSpan(int(span_start621), "Configure")
	return result622
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs623 := [][]interface{}{}
	cond624 := p.matchLookaheadLiteral(":", 0)
	for cond624 {
		_t1234 := p.parse_config_key_value()
		item625 := _t1234
		xs623 = append(xs623, item625)
		cond624 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values626 := xs623
	p.consumeLiteral("}")
	return config_key_values626
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol627 := p.consumeTerminal("SYMBOL").Value.str
	_t1235 := p.parse_value()
	value628 := _t1235
	return []interface{}{symbol627, value628}
}

func (p *Parser) parse_value() *pb.Value {
	span_start642 := int64(p.spanStart())
	var _t1236 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1236 = 9
	} else {
		var _t1237 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1237 = 8
		} else {
			var _t1238 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1238 = 9
			} else {
				var _t1239 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1240 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1240 = 1
					} else {
						var _t1241 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1241 = 0
						} else {
							_t1241 = -1
						}
						_t1240 = _t1241
					}
					_t1239 = _t1240
				} else {
					var _t1242 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1242 = 12
					} else {
						var _t1243 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1243 = 5
						} else {
							var _t1244 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1244 = 2
							} else {
								var _t1245 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1245 = 10
								} else {
									var _t1246 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1246 = 6
									} else {
										var _t1247 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1247 = 3
										} else {
											var _t1248 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1248 = 11
											} else {
												var _t1249 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1249 = 4
												} else {
													var _t1250 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1250 = 7
													} else {
														_t1250 = -1
													}
													_t1249 = _t1250
												}
												_t1248 = _t1249
											}
											_t1247 = _t1248
										}
										_t1246 = _t1247
									}
									_t1245 = _t1246
								}
								_t1244 = _t1245
							}
							_t1243 = _t1244
						}
						_t1242 = _t1243
					}
					_t1239 = _t1242
				}
				_t1238 = _t1239
			}
			_t1237 = _t1238
		}
		_t1236 = _t1237
	}
	prediction629 := _t1236
	var _t1251 *pb.Value
	if prediction629 == 12 {
		uint32641 := p.consumeTerminal("UINT32").Value.u32
		_t1252 := &pb.Value{}
		_t1252.Value = &pb.Value_Uint32Value{Uint32Value: uint32641}
		_t1251 = _t1252
	} else {
		var _t1253 *pb.Value
		if prediction629 == 11 {
			float32640 := p.consumeTerminal("FLOAT32").Value.f32
			_t1254 := &pb.Value{}
			_t1254.Value = &pb.Value_Float32Value{Float32Value: float32640}
			_t1253 = _t1254
		} else {
			var _t1255 *pb.Value
			if prediction629 == 10 {
				int32639 := p.consumeTerminal("INT32").Value.i32
				_t1256 := &pb.Value{}
				_t1256.Value = &pb.Value_Int32Value{Int32Value: int32639}
				_t1255 = _t1256
			} else {
				var _t1257 *pb.Value
				if prediction629 == 9 {
					_t1258 := p.parse_boolean_value()
					boolean_value638 := _t1258
					_t1259 := &pb.Value{}
					_t1259.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value638}
					_t1257 = _t1259
				} else {
					var _t1260 *pb.Value
					if prediction629 == 8 {
						p.consumeLiteral("missing")
						_t1261 := &pb.MissingValue{}
						_t1262 := &pb.Value{}
						_t1262.Value = &pb.Value_MissingValue{MissingValue: _t1261}
						_t1260 = _t1262
					} else {
						var _t1263 *pb.Value
						if prediction629 == 7 {
							decimal637 := p.consumeTerminal("DECIMAL").Value.decimal
							_t1264 := &pb.Value{}
							_t1264.Value = &pb.Value_DecimalValue{DecimalValue: decimal637}
							_t1263 = _t1264
						} else {
							var _t1265 *pb.Value
							if prediction629 == 6 {
								int128636 := p.consumeTerminal("INT128").Value.int128
								_t1266 := &pb.Value{}
								_t1266.Value = &pb.Value_Int128Value{Int128Value: int128636}
								_t1265 = _t1266
							} else {
								var _t1267 *pb.Value
								if prediction629 == 5 {
									uint128635 := p.consumeTerminal("UINT128").Value.uint128
									_t1268 := &pb.Value{}
									_t1268.Value = &pb.Value_Uint128Value{Uint128Value: uint128635}
									_t1267 = _t1268
								} else {
									var _t1269 *pb.Value
									if prediction629 == 4 {
										float634 := p.consumeTerminal("FLOAT").Value.f64
										_t1270 := &pb.Value{}
										_t1270.Value = &pb.Value_FloatValue{FloatValue: float634}
										_t1269 = _t1270
									} else {
										var _t1271 *pb.Value
										if prediction629 == 3 {
											int633 := p.consumeTerminal("INT").Value.i64
											_t1272 := &pb.Value{}
											_t1272.Value = &pb.Value_IntValue{IntValue: int633}
											_t1271 = _t1272
										} else {
											var _t1273 *pb.Value
											if prediction629 == 2 {
												string632 := p.consumeTerminal("STRING").Value.str
												_t1274 := &pb.Value{}
												_t1274.Value = &pb.Value_StringValue{StringValue: string632}
												_t1273 = _t1274
											} else {
												var _t1275 *pb.Value
												if prediction629 == 1 {
													_t1276 := p.parse_datetime()
													datetime631 := _t1276
													_t1277 := &pb.Value{}
													_t1277.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime631}
													_t1275 = _t1277
												} else {
													var _t1278 *pb.Value
													if prediction629 == 0 {
														_t1279 := p.parse_date()
														date630 := _t1279
														_t1280 := &pb.Value{}
														_t1280.Value = &pb.Value_DateValue{DateValue: date630}
														_t1278 = _t1280
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1275 = _t1278
												}
												_t1273 = _t1275
											}
											_t1271 = _t1273
										}
										_t1269 = _t1271
									}
									_t1267 = _t1269
								}
								_t1265 = _t1267
							}
							_t1263 = _t1265
						}
						_t1260 = _t1263
					}
					_t1257 = _t1260
				}
				_t1255 = _t1257
			}
			_t1253 = _t1255
		}
		_t1251 = _t1253
	}
	result643 := _t1251
	p.recordSpan(int(span_start642), "Value")
	return result643
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start647 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int644 := p.consumeTerminal("INT").Value.i64
	int_3645 := p.consumeTerminal("INT").Value.i64
	int_4646 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1281 := &pb.DateValue{Year: int32(int644), Month: int32(int_3645), Day: int32(int_4646)}
	result648 := _t1281
	p.recordSpan(int(span_start647), "DateValue")
	return result648
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start656 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int649 := p.consumeTerminal("INT").Value.i64
	int_3650 := p.consumeTerminal("INT").Value.i64
	int_4651 := p.consumeTerminal("INT").Value.i64
	int_5652 := p.consumeTerminal("INT").Value.i64
	int_6653 := p.consumeTerminal("INT").Value.i64
	int_7654 := p.consumeTerminal("INT").Value.i64
	var _t1282 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1282 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8655 := _t1282
	p.consumeLiteral(")")
	_t1283 := &pb.DateTimeValue{Year: int32(int649), Month: int32(int_3650), Day: int32(int_4651), Hour: int32(int_5652), Minute: int32(int_6653), Second: int32(int_7654), Microsecond: int32(deref(int_8655, 0))}
	result657 := _t1283
	p.recordSpan(int(span_start656), "DateTimeValue")
	return result657
}

func (p *Parser) parse_boolean_value() bool {
	var _t1284 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1284 = 0
	} else {
		var _t1285 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1285 = 1
		} else {
			_t1285 = -1
		}
		_t1284 = _t1285
	}
	prediction658 := _t1284
	var _t1286 bool
	if prediction658 == 1 {
		p.consumeLiteral("false")
		_t1286 = false
	} else {
		var _t1287 bool
		if prediction658 == 0 {
			p.consumeLiteral("true")
			_t1287 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1286 = _t1287
	}
	return _t1286
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start663 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs659 := []*pb.FragmentId{}
	cond660 := p.matchLookaheadLiteral(":", 0)
	for cond660 {
		_t1288 := p.parse_fragment_id()
		item661 := _t1288
		xs659 = append(xs659, item661)
		cond660 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids662 := xs659
	p.consumeLiteral(")")
	_t1289 := &pb.Sync{Fragments: fragment_ids662}
	result664 := _t1289
	p.recordSpan(int(span_start663), "Sync")
	return result664
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start666 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol665 := p.consumeTerminal("SYMBOL").Value.str
	result667 := &pb.FragmentId{Id: []byte(symbol665)}
	p.recordSpan(int(span_start666), "FragmentId")
	return result667
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start670 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1290 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1291 := p.parse_epoch_writes()
		_t1290 = _t1291
	}
	epoch_writes668 := _t1290
	var _t1292 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1293 := p.parse_epoch_reads()
		_t1292 = _t1293
	}
	epoch_reads669 := _t1292
	p.consumeLiteral(")")
	_t1294 := epoch_writes668
	if epoch_writes668 == nil {
		_t1294 = []*pb.Write{}
	}
	_t1295 := epoch_reads669
	if epoch_reads669 == nil {
		_t1295 = []*pb.Read{}
	}
	_t1296 := &pb.Epoch{Writes: _t1294, Reads: _t1295}
	result671 := _t1296
	p.recordSpan(int(span_start670), "Epoch")
	return result671
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs672 := []*pb.Write{}
	cond673 := p.matchLookaheadLiteral("(", 0)
	for cond673 {
		_t1297 := p.parse_write()
		item674 := _t1297
		xs672 = append(xs672, item674)
		cond673 = p.matchLookaheadLiteral("(", 0)
	}
	writes675 := xs672
	p.consumeLiteral(")")
	return writes675
}

func (p *Parser) parse_write() *pb.Write {
	span_start681 := int64(p.spanStart())
	var _t1298 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1299 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1299 = 1
		} else {
			var _t1300 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1300 = 3
			} else {
				var _t1301 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1301 = 0
				} else {
					var _t1302 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1302 = 2
					} else {
						_t1302 = -1
					}
					_t1301 = _t1302
				}
				_t1300 = _t1301
			}
			_t1299 = _t1300
		}
		_t1298 = _t1299
	} else {
		_t1298 = -1
	}
	prediction676 := _t1298
	var _t1303 *pb.Write
	if prediction676 == 3 {
		_t1304 := p.parse_snapshot()
		snapshot680 := _t1304
		_t1305 := &pb.Write{}
		_t1305.WriteType = &pb.Write_Snapshot{Snapshot: snapshot680}
		_t1303 = _t1305
	} else {
		var _t1306 *pb.Write
		if prediction676 == 2 {
			_t1307 := p.parse_context()
			context679 := _t1307
			_t1308 := &pb.Write{}
			_t1308.WriteType = &pb.Write_Context{Context: context679}
			_t1306 = _t1308
		} else {
			var _t1309 *pb.Write
			if prediction676 == 1 {
				_t1310 := p.parse_undefine()
				undefine678 := _t1310
				_t1311 := &pb.Write{}
				_t1311.WriteType = &pb.Write_Undefine{Undefine: undefine678}
				_t1309 = _t1311
			} else {
				var _t1312 *pb.Write
				if prediction676 == 0 {
					_t1313 := p.parse_define()
					define677 := _t1313
					_t1314 := &pb.Write{}
					_t1314.WriteType = &pb.Write_Define{Define: define677}
					_t1312 = _t1314
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1309 = _t1312
			}
			_t1306 = _t1309
		}
		_t1303 = _t1306
	}
	result682 := _t1303
	p.recordSpan(int(span_start681), "Write")
	return result682
}

func (p *Parser) parse_define() *pb.Define {
	span_start684 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1315 := p.parse_fragment()
	fragment683 := _t1315
	p.consumeLiteral(")")
	_t1316 := &pb.Define{Fragment: fragment683}
	result685 := _t1316
	p.recordSpan(int(span_start684), "Define")
	return result685
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start691 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1317 := p.parse_new_fragment_id()
	new_fragment_id686 := _t1317
	xs687 := []*pb.Declaration{}
	cond688 := p.matchLookaheadLiteral("(", 0)
	for cond688 {
		_t1318 := p.parse_declaration()
		item689 := _t1318
		xs687 = append(xs687, item689)
		cond688 = p.matchLookaheadLiteral("(", 0)
	}
	declarations690 := xs687
	p.consumeLiteral(")")
	result692 := p.constructFragment(new_fragment_id686, declarations690)
	p.recordSpan(int(span_start691), "Fragment")
	return result692
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start694 := int64(p.spanStart())
	_t1319 := p.parse_fragment_id()
	fragment_id693 := _t1319
	p.startFragment(fragment_id693)
	result695 := fragment_id693
	p.recordSpan(int(span_start694), "FragmentId")
	return result695
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start701 := int64(p.spanStart())
	var _t1320 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1321 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1321 = 3
		} else {
			var _t1322 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1322 = 2
			} else {
				var _t1323 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1323 = 3
				} else {
					var _t1324 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1324 = 0
					} else {
						var _t1325 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1325 = 3
						} else {
							var _t1326 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1326 = 3
							} else {
								var _t1327 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1327 = 1
								} else {
									_t1327 = -1
								}
								_t1326 = _t1327
							}
							_t1325 = _t1326
						}
						_t1324 = _t1325
					}
					_t1323 = _t1324
				}
				_t1322 = _t1323
			}
			_t1321 = _t1322
		}
		_t1320 = _t1321
	} else {
		_t1320 = -1
	}
	prediction696 := _t1320
	var _t1328 *pb.Declaration
	if prediction696 == 3 {
		_t1329 := p.parse_data()
		data700 := _t1329
		_t1330 := &pb.Declaration{}
		_t1330.DeclarationType = &pb.Declaration_Data{Data: data700}
		_t1328 = _t1330
	} else {
		var _t1331 *pb.Declaration
		if prediction696 == 2 {
			_t1332 := p.parse_constraint()
			constraint699 := _t1332
			_t1333 := &pb.Declaration{}
			_t1333.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint699}
			_t1331 = _t1333
		} else {
			var _t1334 *pb.Declaration
			if prediction696 == 1 {
				_t1335 := p.parse_algorithm()
				algorithm698 := _t1335
				_t1336 := &pb.Declaration{}
				_t1336.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm698}
				_t1334 = _t1336
			} else {
				var _t1337 *pb.Declaration
				if prediction696 == 0 {
					_t1338 := p.parse_def()
					def697 := _t1338
					_t1339 := &pb.Declaration{}
					_t1339.DeclarationType = &pb.Declaration_Def{Def: def697}
					_t1337 = _t1339
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1334 = _t1337
			}
			_t1331 = _t1334
		}
		_t1328 = _t1331
	}
	result702 := _t1328
	p.recordSpan(int(span_start701), "Declaration")
	return result702
}

func (p *Parser) parse_def() *pb.Def {
	span_start706 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1340 := p.parse_relation_id()
	relation_id703 := _t1340
	_t1341 := p.parse_abstraction()
	abstraction704 := _t1341
	var _t1342 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1343 := p.parse_attrs()
		_t1342 = _t1343
	}
	attrs705 := _t1342
	p.consumeLiteral(")")
	_t1344 := attrs705
	if attrs705 == nil {
		_t1344 = []*pb.Attribute{}
	}
	_t1345 := &pb.Def{Name: relation_id703, Body: abstraction704, Attrs: _t1344}
	result707 := _t1345
	p.recordSpan(int(span_start706), "Def")
	return result707
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start711 := int64(p.spanStart())
	var _t1346 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1346 = 0
	} else {
		var _t1347 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1347 = 1
		} else {
			_t1347 = -1
		}
		_t1346 = _t1347
	}
	prediction708 := _t1346
	var _t1348 *pb.RelationId
	if prediction708 == 1 {
		uint128710 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128710
		_t1348 = &pb.RelationId{IdLow: uint128710.Low, IdHigh: uint128710.High}
	} else {
		var _t1349 *pb.RelationId
		if prediction708 == 0 {
			p.consumeLiteral(":")
			symbol709 := p.consumeTerminal("SYMBOL").Value.str
			_t1349 = p.relationIdFromString(symbol709)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1348 = _t1349
	}
	result712 := _t1348
	p.recordSpan(int(span_start711), "RelationId")
	return result712
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1350 := p.parse_bindings()
	bindings713 := _t1350
	_t1351 := p.parse_formula()
	formula714 := _t1351
	p.consumeLiteral(")")
	_t1352 := &pb.Abstraction{Vars: listConcat(bindings713[0].([]*pb.Binding), bindings713[1].([]*pb.Binding)), Value: formula714}
	result716 := _t1352
	p.recordSpan(int(span_start715), "Abstraction")
	return result716
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs717 := []*pb.Binding{}
	cond718 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond718 {
		_t1353 := p.parse_binding()
		item719 := _t1353
		xs717 = append(xs717, item719)
		cond718 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings720 := xs717
	var _t1354 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1355 := p.parse_value_bindings()
		_t1354 = _t1355
	}
	value_bindings721 := _t1354
	p.consumeLiteral("]")
	_t1356 := value_bindings721
	if value_bindings721 == nil {
		_t1356 = []*pb.Binding{}
	}
	return []interface{}{bindings720, _t1356}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start724 := int64(p.spanStart())
	symbol722 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1357 := p.parse_type()
	type723 := _t1357
	_t1358 := &pb.Var{Name: symbol722}
	_t1359 := &pb.Binding{Var: _t1358, Type: type723}
	result725 := _t1359
	p.recordSpan(int(span_start724), "Binding")
	return result725
}

func (p *Parser) parse_type() *pb.Type {
	span_start741 := int64(p.spanStart())
	var _t1360 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1360 = 0
	} else {
		var _t1361 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1361 = 13
		} else {
			var _t1362 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1362 = 4
			} else {
				var _t1363 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1363 = 1
				} else {
					var _t1364 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1364 = 8
					} else {
						var _t1365 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1365 = 11
						} else {
							var _t1366 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1366 = 5
							} else {
								var _t1367 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1367 = 2
								} else {
									var _t1368 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1368 = 12
									} else {
										var _t1369 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1369 = 3
										} else {
											var _t1370 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1370 = 7
											} else {
												var _t1371 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1371 = 6
												} else {
													var _t1372 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1372 = 10
													} else {
														var _t1373 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1373 = 9
														} else {
															_t1373 = -1
														}
														_t1372 = _t1373
													}
													_t1371 = _t1372
												}
												_t1370 = _t1371
											}
											_t1369 = _t1370
										}
										_t1368 = _t1369
									}
									_t1367 = _t1368
								}
								_t1366 = _t1367
							}
							_t1365 = _t1366
						}
						_t1364 = _t1365
					}
					_t1363 = _t1364
				}
				_t1362 = _t1363
			}
			_t1361 = _t1362
		}
		_t1360 = _t1361
	}
	prediction726 := _t1360
	var _t1374 *pb.Type
	if prediction726 == 13 {
		_t1375 := p.parse_uint32_type()
		uint32_type740 := _t1375
		_t1376 := &pb.Type{}
		_t1376.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type740}
		_t1374 = _t1376
	} else {
		var _t1377 *pb.Type
		if prediction726 == 12 {
			_t1378 := p.parse_float32_type()
			float32_type739 := _t1378
			_t1379 := &pb.Type{}
			_t1379.Type = &pb.Type_Float32Type{Float32Type: float32_type739}
			_t1377 = _t1379
		} else {
			var _t1380 *pb.Type
			if prediction726 == 11 {
				_t1381 := p.parse_int32_type()
				int32_type738 := _t1381
				_t1382 := &pb.Type{}
				_t1382.Type = &pb.Type_Int32Type{Int32Type: int32_type738}
				_t1380 = _t1382
			} else {
				var _t1383 *pb.Type
				if prediction726 == 10 {
					_t1384 := p.parse_boolean_type()
					boolean_type737 := _t1384
					_t1385 := &pb.Type{}
					_t1385.Type = &pb.Type_BooleanType{BooleanType: boolean_type737}
					_t1383 = _t1385
				} else {
					var _t1386 *pb.Type
					if prediction726 == 9 {
						_t1387 := p.parse_decimal_type()
						decimal_type736 := _t1387
						_t1388 := &pb.Type{}
						_t1388.Type = &pb.Type_DecimalType{DecimalType: decimal_type736}
						_t1386 = _t1388
					} else {
						var _t1389 *pb.Type
						if prediction726 == 8 {
							_t1390 := p.parse_missing_type()
							missing_type735 := _t1390
							_t1391 := &pb.Type{}
							_t1391.Type = &pb.Type_MissingType{MissingType: missing_type735}
							_t1389 = _t1391
						} else {
							var _t1392 *pb.Type
							if prediction726 == 7 {
								_t1393 := p.parse_datetime_type()
								datetime_type734 := _t1393
								_t1394 := &pb.Type{}
								_t1394.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type734}
								_t1392 = _t1394
							} else {
								var _t1395 *pb.Type
								if prediction726 == 6 {
									_t1396 := p.parse_date_type()
									date_type733 := _t1396
									_t1397 := &pb.Type{}
									_t1397.Type = &pb.Type_DateType{DateType: date_type733}
									_t1395 = _t1397
								} else {
									var _t1398 *pb.Type
									if prediction726 == 5 {
										_t1399 := p.parse_int128_type()
										int128_type732 := _t1399
										_t1400 := &pb.Type{}
										_t1400.Type = &pb.Type_Int128Type{Int128Type: int128_type732}
										_t1398 = _t1400
									} else {
										var _t1401 *pb.Type
										if prediction726 == 4 {
											_t1402 := p.parse_uint128_type()
											uint128_type731 := _t1402
											_t1403 := &pb.Type{}
											_t1403.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type731}
											_t1401 = _t1403
										} else {
											var _t1404 *pb.Type
											if prediction726 == 3 {
												_t1405 := p.parse_float_type()
												float_type730 := _t1405
												_t1406 := &pb.Type{}
												_t1406.Type = &pb.Type_FloatType{FloatType: float_type730}
												_t1404 = _t1406
											} else {
												var _t1407 *pb.Type
												if prediction726 == 2 {
													_t1408 := p.parse_int_type()
													int_type729 := _t1408
													_t1409 := &pb.Type{}
													_t1409.Type = &pb.Type_IntType{IntType: int_type729}
													_t1407 = _t1409
												} else {
													var _t1410 *pb.Type
													if prediction726 == 1 {
														_t1411 := p.parse_string_type()
														string_type728 := _t1411
														_t1412 := &pb.Type{}
														_t1412.Type = &pb.Type_StringType{StringType: string_type728}
														_t1410 = _t1412
													} else {
														var _t1413 *pb.Type
														if prediction726 == 0 {
															_t1414 := p.parse_unspecified_type()
															unspecified_type727 := _t1414
															_t1415 := &pb.Type{}
															_t1415.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type727}
															_t1413 = _t1415
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1410 = _t1413
													}
													_t1407 = _t1410
												}
												_t1404 = _t1407
											}
											_t1401 = _t1404
										}
										_t1398 = _t1401
									}
									_t1395 = _t1398
								}
								_t1392 = _t1395
							}
							_t1389 = _t1392
						}
						_t1386 = _t1389
					}
					_t1383 = _t1386
				}
				_t1380 = _t1383
			}
			_t1377 = _t1380
		}
		_t1374 = _t1377
	}
	result742 := _t1374
	p.recordSpan(int(span_start741), "Type")
	return result742
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1416 := &pb.UnspecifiedType{}
	result744 := _t1416
	p.recordSpan(int(span_start743), "UnspecifiedType")
	return result744
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start745 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1417 := &pb.StringType{}
	result746 := _t1417
	p.recordSpan(int(span_start745), "StringType")
	return result746
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1418 := &pb.IntType{}
	result748 := _t1418
	p.recordSpan(int(span_start747), "IntType")
	return result748
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1419 := &pb.FloatType{}
	result750 := _t1419
	p.recordSpan(int(span_start749), "FloatType")
	return result750
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1420 := &pb.UInt128Type{}
	result752 := _t1420
	p.recordSpan(int(span_start751), "UInt128Type")
	return result752
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1421 := &pb.Int128Type{}
	result754 := _t1421
	p.recordSpan(int(span_start753), "Int128Type")
	return result754
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1422 := &pb.DateType{}
	result756 := _t1422
	p.recordSpan(int(span_start755), "DateType")
	return result756
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1423 := &pb.DateTimeType{}
	result758 := _t1423
	p.recordSpan(int(span_start757), "DateTimeType")
	return result758
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1424 := &pb.MissingType{}
	result760 := _t1424
	p.recordSpan(int(span_start759), "MissingType")
	return result760
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int761 := p.consumeTerminal("INT").Value.i64
	int_3762 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1425 := &pb.DecimalType{Precision: int32(int761), Scale: int32(int_3762)}
	result764 := _t1425
	p.recordSpan(int(span_start763), "DecimalType")
	return result764
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start765 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1426 := &pb.BooleanType{}
	result766 := _t1426
	p.recordSpan(int(span_start765), "BooleanType")
	return result766
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1427 := &pb.Int32Type{}
	result768 := _t1427
	p.recordSpan(int(span_start767), "Int32Type")
	return result768
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start769 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1428 := &pb.Float32Type{}
	result770 := _t1428
	p.recordSpan(int(span_start769), "Float32Type")
	return result770
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start771 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1429 := &pb.UInt32Type{}
	result772 := _t1429
	p.recordSpan(int(span_start771), "UInt32Type")
	return result772
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs773 := []*pb.Binding{}
	cond774 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond774 {
		_t1430 := p.parse_binding()
		item775 := _t1430
		xs773 = append(xs773, item775)
		cond774 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings776 := xs773
	return bindings776
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start791 := int64(p.spanStart())
	var _t1431 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1432 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1432 = 0
		} else {
			var _t1433 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1433 = 11
			} else {
				var _t1434 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1434 = 3
				} else {
					var _t1435 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1435 = 10
					} else {
						var _t1436 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1436 = 9
						} else {
							var _t1437 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1437 = 5
							} else {
								var _t1438 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1438 = 6
								} else {
									var _t1439 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1439 = 7
									} else {
										var _t1440 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1440 = 1
										} else {
											var _t1441 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1441 = 2
											} else {
												var _t1442 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1442 = 12
												} else {
													var _t1443 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1443 = 8
													} else {
														var _t1444 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1444 = 4
														} else {
															var _t1445 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1445 = 10
															} else {
																var _t1446 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1446 = 10
																} else {
																	var _t1447 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1447 = 10
																	} else {
																		var _t1448 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1448 = 10
																		} else {
																			var _t1449 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1449 = 10
																			} else {
																				var _t1450 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1450 = 10
																				} else {
																					var _t1451 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1451 = 10
																					} else {
																						var _t1452 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1452 = 10
																						} else {
																							var _t1453 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1453 = 10
																							} else {
																								_t1453 = -1
																							}
																							_t1452 = _t1453
																						}
																						_t1451 = _t1452
																					}
																					_t1450 = _t1451
																				}
																				_t1449 = _t1450
																			}
																			_t1448 = _t1449
																		}
																		_t1447 = _t1448
																	}
																	_t1446 = _t1447
																}
																_t1445 = _t1446
															}
															_t1444 = _t1445
														}
														_t1443 = _t1444
													}
													_t1442 = _t1443
												}
												_t1441 = _t1442
											}
											_t1440 = _t1441
										}
										_t1439 = _t1440
									}
									_t1438 = _t1439
								}
								_t1437 = _t1438
							}
							_t1436 = _t1437
						}
						_t1435 = _t1436
					}
					_t1434 = _t1435
				}
				_t1433 = _t1434
			}
			_t1432 = _t1433
		}
		_t1431 = _t1432
	} else {
		_t1431 = -1
	}
	prediction777 := _t1431
	var _t1454 *pb.Formula
	if prediction777 == 12 {
		_t1455 := p.parse_cast()
		cast790 := _t1455
		_t1456 := &pb.Formula{}
		_t1456.FormulaType = &pb.Formula_Cast{Cast: cast790}
		_t1454 = _t1456
	} else {
		var _t1457 *pb.Formula
		if prediction777 == 11 {
			_t1458 := p.parse_rel_atom()
			rel_atom789 := _t1458
			_t1459 := &pb.Formula{}
			_t1459.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom789}
			_t1457 = _t1459
		} else {
			var _t1460 *pb.Formula
			if prediction777 == 10 {
				_t1461 := p.parse_primitive()
				primitive788 := _t1461
				_t1462 := &pb.Formula{}
				_t1462.FormulaType = &pb.Formula_Primitive{Primitive: primitive788}
				_t1460 = _t1462
			} else {
				var _t1463 *pb.Formula
				if prediction777 == 9 {
					_t1464 := p.parse_pragma()
					pragma787 := _t1464
					_t1465 := &pb.Formula{}
					_t1465.FormulaType = &pb.Formula_Pragma{Pragma: pragma787}
					_t1463 = _t1465
				} else {
					var _t1466 *pb.Formula
					if prediction777 == 8 {
						_t1467 := p.parse_atom()
						atom786 := _t1467
						_t1468 := &pb.Formula{}
						_t1468.FormulaType = &pb.Formula_Atom{Atom: atom786}
						_t1466 = _t1468
					} else {
						var _t1469 *pb.Formula
						if prediction777 == 7 {
							_t1470 := p.parse_ffi()
							ffi785 := _t1470
							_t1471 := &pb.Formula{}
							_t1471.FormulaType = &pb.Formula_Ffi{Ffi: ffi785}
							_t1469 = _t1471
						} else {
							var _t1472 *pb.Formula
							if prediction777 == 6 {
								_t1473 := p.parse_not()
								not784 := _t1473
								_t1474 := &pb.Formula{}
								_t1474.FormulaType = &pb.Formula_Not{Not: not784}
								_t1472 = _t1474
							} else {
								var _t1475 *pb.Formula
								if prediction777 == 5 {
									_t1476 := p.parse_disjunction()
									disjunction783 := _t1476
									_t1477 := &pb.Formula{}
									_t1477.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction783}
									_t1475 = _t1477
								} else {
									var _t1478 *pb.Formula
									if prediction777 == 4 {
										_t1479 := p.parse_conjunction()
										conjunction782 := _t1479
										_t1480 := &pb.Formula{}
										_t1480.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction782}
										_t1478 = _t1480
									} else {
										var _t1481 *pb.Formula
										if prediction777 == 3 {
											_t1482 := p.parse_reduce()
											reduce781 := _t1482
											_t1483 := &pb.Formula{}
											_t1483.FormulaType = &pb.Formula_Reduce{Reduce: reduce781}
											_t1481 = _t1483
										} else {
											var _t1484 *pb.Formula
											if prediction777 == 2 {
												_t1485 := p.parse_exists()
												exists780 := _t1485
												_t1486 := &pb.Formula{}
												_t1486.FormulaType = &pb.Formula_Exists{Exists: exists780}
												_t1484 = _t1486
											} else {
												var _t1487 *pb.Formula
												if prediction777 == 1 {
													_t1488 := p.parse_false()
													false779 := _t1488
													_t1489 := &pb.Formula{}
													_t1489.FormulaType = &pb.Formula_Disjunction{Disjunction: false779}
													_t1487 = _t1489
												} else {
													var _t1490 *pb.Formula
													if prediction777 == 0 {
														_t1491 := p.parse_true()
														true778 := _t1491
														_t1492 := &pb.Formula{}
														_t1492.FormulaType = &pb.Formula_Conjunction{Conjunction: true778}
														_t1490 = _t1492
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1487 = _t1490
												}
												_t1484 = _t1487
											}
											_t1481 = _t1484
										}
										_t1478 = _t1481
									}
									_t1475 = _t1478
								}
								_t1472 = _t1475
							}
							_t1469 = _t1472
						}
						_t1466 = _t1469
					}
					_t1463 = _t1466
				}
				_t1460 = _t1463
			}
			_t1457 = _t1460
		}
		_t1454 = _t1457
	}
	result792 := _t1454
	p.recordSpan(int(span_start791), "Formula")
	return result792
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start793 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1493 := &pb.Conjunction{Args: []*pb.Formula{}}
	result794 := _t1493
	p.recordSpan(int(span_start793), "Conjunction")
	return result794
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start795 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1494 := &pb.Disjunction{Args: []*pb.Formula{}}
	result796 := _t1494
	p.recordSpan(int(span_start795), "Disjunction")
	return result796
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start799 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1495 := p.parse_bindings()
	bindings797 := _t1495
	_t1496 := p.parse_formula()
	formula798 := _t1496
	p.consumeLiteral(")")
	_t1497 := &pb.Abstraction{Vars: listConcat(bindings797[0].([]*pb.Binding), bindings797[1].([]*pb.Binding)), Value: formula798}
	_t1498 := &pb.Exists{Body: _t1497}
	result800 := _t1498
	p.recordSpan(int(span_start799), "Exists")
	return result800
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1499 := p.parse_abstraction()
	abstraction801 := _t1499
	_t1500 := p.parse_abstraction()
	abstraction_3802 := _t1500
	_t1501 := p.parse_terms()
	terms803 := _t1501
	p.consumeLiteral(")")
	_t1502 := &pb.Reduce{Op: abstraction801, Body: abstraction_3802, Terms: terms803}
	result805 := _t1502
	p.recordSpan(int(span_start804), "Reduce")
	return result805
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs806 := []*pb.Term{}
	cond807 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond807 {
		_t1503 := p.parse_term()
		item808 := _t1503
		xs806 = append(xs806, item808)
		cond807 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms809 := xs806
	p.consumeLiteral(")")
	return terms809
}

func (p *Parser) parse_term() *pb.Term {
	span_start813 := int64(p.spanStart())
	var _t1504 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1504 = 1
	} else {
		var _t1505 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1505 = 1
		} else {
			var _t1506 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1506 = 1
			} else {
				var _t1507 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1507 = 1
				} else {
					var _t1508 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1508 = 1
					} else {
						var _t1509 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1509 = 1
						} else {
							var _t1510 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1510 = 0
							} else {
								var _t1511 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1511 = 1
								} else {
									var _t1512 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1512 = 1
									} else {
										var _t1513 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1513 = 1
										} else {
											var _t1514 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1514 = 1
											} else {
												var _t1515 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1515 = 1
												} else {
													var _t1516 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1516 = 1
													} else {
														var _t1517 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1517 = 1
														} else {
															_t1517 = -1
														}
														_t1516 = _t1517
													}
													_t1515 = _t1516
												}
												_t1514 = _t1515
											}
											_t1513 = _t1514
										}
										_t1512 = _t1513
									}
									_t1511 = _t1512
								}
								_t1510 = _t1511
							}
							_t1509 = _t1510
						}
						_t1508 = _t1509
					}
					_t1507 = _t1508
				}
				_t1506 = _t1507
			}
			_t1505 = _t1506
		}
		_t1504 = _t1505
	}
	prediction810 := _t1504
	var _t1518 *pb.Term
	if prediction810 == 1 {
		_t1519 := p.parse_constant()
		constant812 := _t1519
		_t1520 := &pb.Term{}
		_t1520.TermType = &pb.Term_Constant{Constant: constant812}
		_t1518 = _t1520
	} else {
		var _t1521 *pb.Term
		if prediction810 == 0 {
			_t1522 := p.parse_var()
			var811 := _t1522
			_t1523 := &pb.Term{}
			_t1523.TermType = &pb.Term_Var{Var: var811}
			_t1521 = _t1523
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1518 = _t1521
	}
	result814 := _t1518
	p.recordSpan(int(span_start813), "Term")
	return result814
}

func (p *Parser) parse_var() *pb.Var {
	span_start816 := int64(p.spanStart())
	symbol815 := p.consumeTerminal("SYMBOL").Value.str
	_t1524 := &pb.Var{Name: symbol815}
	result817 := _t1524
	p.recordSpan(int(span_start816), "Var")
	return result817
}

func (p *Parser) parse_constant() *pb.Value {
	span_start819 := int64(p.spanStart())
	_t1525 := p.parse_value()
	value818 := _t1525
	result820 := value818
	p.recordSpan(int(span_start819), "Value")
	return result820
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start825 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs821 := []*pb.Formula{}
	cond822 := p.matchLookaheadLiteral("(", 0)
	for cond822 {
		_t1526 := p.parse_formula()
		item823 := _t1526
		xs821 = append(xs821, item823)
		cond822 = p.matchLookaheadLiteral("(", 0)
	}
	formulas824 := xs821
	p.consumeLiteral(")")
	_t1527 := &pb.Conjunction{Args: formulas824}
	result826 := _t1527
	p.recordSpan(int(span_start825), "Conjunction")
	return result826
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start831 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs827 := []*pb.Formula{}
	cond828 := p.matchLookaheadLiteral("(", 0)
	for cond828 {
		_t1528 := p.parse_formula()
		item829 := _t1528
		xs827 = append(xs827, item829)
		cond828 = p.matchLookaheadLiteral("(", 0)
	}
	formulas830 := xs827
	p.consumeLiteral(")")
	_t1529 := &pb.Disjunction{Args: formulas830}
	result832 := _t1529
	p.recordSpan(int(span_start831), "Disjunction")
	return result832
}

func (p *Parser) parse_not() *pb.Not {
	span_start834 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1530 := p.parse_formula()
	formula833 := _t1530
	p.consumeLiteral(")")
	_t1531 := &pb.Not{Arg: formula833}
	result835 := _t1531
	p.recordSpan(int(span_start834), "Not")
	return result835
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1532 := p.parse_name()
	name836 := _t1532
	_t1533 := p.parse_ffi_args()
	ffi_args837 := _t1533
	_t1534 := p.parse_terms()
	terms838 := _t1534
	p.consumeLiteral(")")
	_t1535 := &pb.FFI{Name: name836, Args: ffi_args837, Terms: terms838}
	result840 := _t1535
	p.recordSpan(int(span_start839), "FFI")
	return result840
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol841 := p.consumeTerminal("SYMBOL").Value.str
	return symbol841
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs842 := []*pb.Abstraction{}
	cond843 := p.matchLookaheadLiteral("(", 0)
	for cond843 {
		_t1536 := p.parse_abstraction()
		item844 := _t1536
		xs842 = append(xs842, item844)
		cond843 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions845 := xs842
	p.consumeLiteral(")")
	return abstractions845
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1537 := p.parse_relation_id()
	relation_id846 := _t1537
	xs847 := []*pb.Term{}
	cond848 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond848 {
		_t1538 := p.parse_term()
		item849 := _t1538
		xs847 = append(xs847, item849)
		cond848 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms850 := xs847
	p.consumeLiteral(")")
	_t1539 := &pb.Atom{Name: relation_id846, Terms: terms850}
	result852 := _t1539
	p.recordSpan(int(span_start851), "Atom")
	return result852
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1540 := p.parse_name()
	name853 := _t1540
	xs854 := []*pb.Term{}
	cond855 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond855 {
		_t1541 := p.parse_term()
		item856 := _t1541
		xs854 = append(xs854, item856)
		cond855 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms857 := xs854
	p.consumeLiteral(")")
	_t1542 := &pb.Pragma{Name: name853, Terms: terms857}
	result859 := _t1542
	p.recordSpan(int(span_start858), "Pragma")
	return result859
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start875 := int64(p.spanStart())
	var _t1543 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1544 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1544 = 9
		} else {
			var _t1545 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1545 = 4
			} else {
				var _t1546 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1546 = 3
				} else {
					var _t1547 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1547 = 0
					} else {
						var _t1548 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1548 = 2
						} else {
							var _t1549 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1549 = 1
							} else {
								var _t1550 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1550 = 8
								} else {
									var _t1551 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1551 = 6
									} else {
										var _t1552 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1552 = 5
										} else {
											var _t1553 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1553 = 7
											} else {
												_t1553 = -1
											}
											_t1552 = _t1553
										}
										_t1551 = _t1552
									}
									_t1550 = _t1551
								}
								_t1549 = _t1550
							}
							_t1548 = _t1549
						}
						_t1547 = _t1548
					}
					_t1546 = _t1547
				}
				_t1545 = _t1546
			}
			_t1544 = _t1545
		}
		_t1543 = _t1544
	} else {
		_t1543 = -1
	}
	prediction860 := _t1543
	var _t1554 *pb.Primitive
	if prediction860 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1555 := p.parse_name()
		name870 := _t1555
		xs871 := []*pb.RelTerm{}
		cond872 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
		for cond872 {
			_t1556 := p.parse_rel_term()
			item873 := _t1556
			xs871 = append(xs871, item873)
			cond872 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
		}
		rel_terms874 := xs871
		p.consumeLiteral(")")
		_t1557 := &pb.Primitive{Name: name870, Terms: rel_terms874}
		_t1554 = _t1557
	} else {
		var _t1558 *pb.Primitive
		if prediction860 == 8 {
			_t1559 := p.parse_divide()
			divide869 := _t1559
			_t1558 = divide869
		} else {
			var _t1560 *pb.Primitive
			if prediction860 == 7 {
				_t1561 := p.parse_multiply()
				multiply868 := _t1561
				_t1560 = multiply868
			} else {
				var _t1562 *pb.Primitive
				if prediction860 == 6 {
					_t1563 := p.parse_minus()
					minus867 := _t1563
					_t1562 = minus867
				} else {
					var _t1564 *pb.Primitive
					if prediction860 == 5 {
						_t1565 := p.parse_add()
						add866 := _t1565
						_t1564 = add866
					} else {
						var _t1566 *pb.Primitive
						if prediction860 == 4 {
							_t1567 := p.parse_gt_eq()
							gt_eq865 := _t1567
							_t1566 = gt_eq865
						} else {
							var _t1568 *pb.Primitive
							if prediction860 == 3 {
								_t1569 := p.parse_gt()
								gt864 := _t1569
								_t1568 = gt864
							} else {
								var _t1570 *pb.Primitive
								if prediction860 == 2 {
									_t1571 := p.parse_lt_eq()
									lt_eq863 := _t1571
									_t1570 = lt_eq863
								} else {
									var _t1572 *pb.Primitive
									if prediction860 == 1 {
										_t1573 := p.parse_lt()
										lt862 := _t1573
										_t1572 = lt862
									} else {
										var _t1574 *pb.Primitive
										if prediction860 == 0 {
											_t1575 := p.parse_eq()
											eq861 := _t1575
											_t1574 = eq861
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1572 = _t1574
									}
									_t1570 = _t1572
								}
								_t1568 = _t1570
							}
							_t1566 = _t1568
						}
						_t1564 = _t1566
					}
					_t1562 = _t1564
				}
				_t1560 = _t1562
			}
			_t1558 = _t1560
		}
		_t1554 = _t1558
	}
	result876 := _t1554
	p.recordSpan(int(span_start875), "Primitive")
	return result876
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start879 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1576 := p.parse_term()
	term877 := _t1576
	_t1577 := p.parse_term()
	term_3878 := _t1577
	p.consumeLiteral(")")
	_t1578 := &pb.RelTerm{}
	_t1578.RelTermType = &pb.RelTerm_Term{Term: term877}
	_t1579 := &pb.RelTerm{}
	_t1579.RelTermType = &pb.RelTerm_Term{Term: term_3878}
	_t1580 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1578, _t1579}}
	result880 := _t1580
	p.recordSpan(int(span_start879), "Primitive")
	return result880
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start883 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1581 := p.parse_term()
	term881 := _t1581
	_t1582 := p.parse_term()
	term_3882 := _t1582
	p.consumeLiteral(")")
	_t1583 := &pb.RelTerm{}
	_t1583.RelTermType = &pb.RelTerm_Term{Term: term881}
	_t1584 := &pb.RelTerm{}
	_t1584.RelTermType = &pb.RelTerm_Term{Term: term_3882}
	_t1585 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1583, _t1584}}
	result884 := _t1585
	p.recordSpan(int(span_start883), "Primitive")
	return result884
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start887 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1586 := p.parse_term()
	term885 := _t1586
	_t1587 := p.parse_term()
	term_3886 := _t1587
	p.consumeLiteral(")")
	_t1588 := &pb.RelTerm{}
	_t1588.RelTermType = &pb.RelTerm_Term{Term: term885}
	_t1589 := &pb.RelTerm{}
	_t1589.RelTermType = &pb.RelTerm_Term{Term: term_3886}
	_t1590 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1588, _t1589}}
	result888 := _t1590
	p.recordSpan(int(span_start887), "Primitive")
	return result888
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1591 := p.parse_term()
	term889 := _t1591
	_t1592 := p.parse_term()
	term_3890 := _t1592
	p.consumeLiteral(")")
	_t1593 := &pb.RelTerm{}
	_t1593.RelTermType = &pb.RelTerm_Term{Term: term889}
	_t1594 := &pb.RelTerm{}
	_t1594.RelTermType = &pb.RelTerm_Term{Term: term_3890}
	_t1595 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1593, _t1594}}
	result892 := _t1595
	p.recordSpan(int(span_start891), "Primitive")
	return result892
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1596 := p.parse_term()
	term893 := _t1596
	_t1597 := p.parse_term()
	term_3894 := _t1597
	p.consumeLiteral(")")
	_t1598 := &pb.RelTerm{}
	_t1598.RelTermType = &pb.RelTerm_Term{Term: term893}
	_t1599 := &pb.RelTerm{}
	_t1599.RelTermType = &pb.RelTerm_Term{Term: term_3894}
	_t1600 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1598, _t1599}}
	result896 := _t1600
	p.recordSpan(int(span_start895), "Primitive")
	return result896
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1601 := p.parse_term()
	term897 := _t1601
	_t1602 := p.parse_term()
	term_3898 := _t1602
	_t1603 := p.parse_term()
	term_4899 := _t1603
	p.consumeLiteral(")")
	_t1604 := &pb.RelTerm{}
	_t1604.RelTermType = &pb.RelTerm_Term{Term: term897}
	_t1605 := &pb.RelTerm{}
	_t1605.RelTermType = &pb.RelTerm_Term{Term: term_3898}
	_t1606 := &pb.RelTerm{}
	_t1606.RelTermType = &pb.RelTerm_Term{Term: term_4899}
	_t1607 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1604, _t1605, _t1606}}
	result901 := _t1607
	p.recordSpan(int(span_start900), "Primitive")
	return result901
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start905 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1608 := p.parse_term()
	term902 := _t1608
	_t1609 := p.parse_term()
	term_3903 := _t1609
	_t1610 := p.parse_term()
	term_4904 := _t1610
	p.consumeLiteral(")")
	_t1611 := &pb.RelTerm{}
	_t1611.RelTermType = &pb.RelTerm_Term{Term: term902}
	_t1612 := &pb.RelTerm{}
	_t1612.RelTermType = &pb.RelTerm_Term{Term: term_3903}
	_t1613 := &pb.RelTerm{}
	_t1613.RelTermType = &pb.RelTerm_Term{Term: term_4904}
	_t1614 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1611, _t1612, _t1613}}
	result906 := _t1614
	p.recordSpan(int(span_start905), "Primitive")
	return result906
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start910 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1615 := p.parse_term()
	term907 := _t1615
	_t1616 := p.parse_term()
	term_3908 := _t1616
	_t1617 := p.parse_term()
	term_4909 := _t1617
	p.consumeLiteral(")")
	_t1618 := &pb.RelTerm{}
	_t1618.RelTermType = &pb.RelTerm_Term{Term: term907}
	_t1619 := &pb.RelTerm{}
	_t1619.RelTermType = &pb.RelTerm_Term{Term: term_3908}
	_t1620 := &pb.RelTerm{}
	_t1620.RelTermType = &pb.RelTerm_Term{Term: term_4909}
	_t1621 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1618, _t1619, _t1620}}
	result911 := _t1621
	p.recordSpan(int(span_start910), "Primitive")
	return result911
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start915 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1622 := p.parse_term()
	term912 := _t1622
	_t1623 := p.parse_term()
	term_3913 := _t1623
	_t1624 := p.parse_term()
	term_4914 := _t1624
	p.consumeLiteral(")")
	_t1625 := &pb.RelTerm{}
	_t1625.RelTermType = &pb.RelTerm_Term{Term: term912}
	_t1626 := &pb.RelTerm{}
	_t1626.RelTermType = &pb.RelTerm_Term{Term: term_3913}
	_t1627 := &pb.RelTerm{}
	_t1627.RelTermType = &pb.RelTerm_Term{Term: term_4914}
	_t1628 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1625, _t1626, _t1627}}
	result916 := _t1628
	p.recordSpan(int(span_start915), "Primitive")
	return result916
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start920 := int64(p.spanStart())
	var _t1629 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1629 = 1
	} else {
		var _t1630 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1630 = 1
		} else {
			var _t1631 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1631 = 1
			} else {
				var _t1632 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1632 = 1
				} else {
					var _t1633 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1633 = 0
					} else {
						var _t1634 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1634 = 1
						} else {
							var _t1635 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1635 = 1
							} else {
								var _t1636 int64
								if p.matchLookaheadTerminal("SYMBOL", 0) {
									_t1636 = 1
								} else {
									var _t1637 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1637 = 1
									} else {
										var _t1638 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1638 = 1
										} else {
											var _t1639 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1639 = 1
											} else {
												var _t1640 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1640 = 1
												} else {
													var _t1641 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1641 = 1
													} else {
														var _t1642 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1642 = 1
														} else {
															var _t1643 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1643 = 1
															} else {
																_t1643 = -1
															}
															_t1642 = _t1643
														}
														_t1641 = _t1642
													}
													_t1640 = _t1641
												}
												_t1639 = _t1640
											}
											_t1638 = _t1639
										}
										_t1637 = _t1638
									}
									_t1636 = _t1637
								}
								_t1635 = _t1636
							}
							_t1634 = _t1635
						}
						_t1633 = _t1634
					}
					_t1632 = _t1633
				}
				_t1631 = _t1632
			}
			_t1630 = _t1631
		}
		_t1629 = _t1630
	}
	prediction917 := _t1629
	var _t1644 *pb.RelTerm
	if prediction917 == 1 {
		_t1645 := p.parse_term()
		term919 := _t1645
		_t1646 := &pb.RelTerm{}
		_t1646.RelTermType = &pb.RelTerm_Term{Term: term919}
		_t1644 = _t1646
	} else {
		var _t1647 *pb.RelTerm
		if prediction917 == 0 {
			_t1648 := p.parse_specialized_value()
			specialized_value918 := _t1648
			_t1649 := &pb.RelTerm{}
			_t1649.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value918}
			_t1647 = _t1649
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1644 = _t1647
	}
	result921 := _t1644
	p.recordSpan(int(span_start920), "RelTerm")
	return result921
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1650 := p.parse_value()
	value922 := _t1650
	result924 := value922
	p.recordSpan(int(span_start923), "Value")
	return result924
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start930 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1651 := p.parse_name()
	name925 := _t1651
	xs926 := []*pb.RelTerm{}
	cond927 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond927 {
		_t1652 := p.parse_rel_term()
		item928 := _t1652
		xs926 = append(xs926, item928)
		cond927 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	rel_terms929 := xs926
	p.consumeLiteral(")")
	_t1653 := &pb.RelAtom{Name: name925, Terms: rel_terms929}
	result931 := _t1653
	p.recordSpan(int(span_start930), "RelAtom")
	return result931
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start934 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1654 := p.parse_term()
	term932 := _t1654
	_t1655 := p.parse_term()
	term_3933 := _t1655
	p.consumeLiteral(")")
	_t1656 := &pb.Cast{Input: term932, Result: term_3933}
	result935 := _t1656
	p.recordSpan(int(span_start934), "Cast")
	return result935
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs936 := []*pb.Attribute{}
	cond937 := p.matchLookaheadLiteral("(", 0)
	for cond937 {
		_t1657 := p.parse_attribute()
		item938 := _t1657
		xs936 = append(xs936, item938)
		cond937 = p.matchLookaheadLiteral("(", 0)
	}
	attributes939 := xs936
	p.consumeLiteral(")")
	return attributes939
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start945 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1658 := p.parse_name()
	name940 := _t1658
	xs941 := []*pb.Value{}
	cond942 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond942 {
		_t1659 := p.parse_value()
		item943 := _t1659
		xs941 = append(xs941, item943)
		cond942 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	values944 := xs941
	p.consumeLiteral(")")
	_t1660 := &pb.Attribute{Name: name940, Args: values944}
	result946 := _t1660
	p.recordSpan(int(span_start945), "Attribute")
	return result946
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs947 := []*pb.RelationId{}
	cond948 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond948 {
		_t1661 := p.parse_relation_id()
		item949 := _t1661
		xs947 = append(xs947, item949)
		cond948 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids950 := xs947
	_t1662 := p.parse_script()
	script951 := _t1662
	p.consumeLiteral(")")
	_t1663 := &pb.Algorithm{Global: relation_ids950, Body: script951}
	result953 := _t1663
	p.recordSpan(int(span_start952), "Algorithm")
	return result953
}

func (p *Parser) parse_script() *pb.Script {
	span_start958 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs954 := []*pb.Construct{}
	cond955 := p.matchLookaheadLiteral("(", 0)
	for cond955 {
		_t1664 := p.parse_construct()
		item956 := _t1664
		xs954 = append(xs954, item956)
		cond955 = p.matchLookaheadLiteral("(", 0)
	}
	constructs957 := xs954
	p.consumeLiteral(")")
	_t1665 := &pb.Script{Constructs: constructs957}
	result959 := _t1665
	p.recordSpan(int(span_start958), "Script")
	return result959
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start963 := int64(p.spanStart())
	var _t1666 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1667 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1667 = 1
		} else {
			var _t1668 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1668 = 1
			} else {
				var _t1669 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1669 = 1
				} else {
					var _t1670 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1670 = 0
					} else {
						var _t1671 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1671 = 1
						} else {
							var _t1672 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1672 = 1
							} else {
								_t1672 = -1
							}
							_t1671 = _t1672
						}
						_t1670 = _t1671
					}
					_t1669 = _t1670
				}
				_t1668 = _t1669
			}
			_t1667 = _t1668
		}
		_t1666 = _t1667
	} else {
		_t1666 = -1
	}
	prediction960 := _t1666
	var _t1673 *pb.Construct
	if prediction960 == 1 {
		_t1674 := p.parse_instruction()
		instruction962 := _t1674
		_t1675 := &pb.Construct{}
		_t1675.ConstructType = &pb.Construct_Instruction{Instruction: instruction962}
		_t1673 = _t1675
	} else {
		var _t1676 *pb.Construct
		if prediction960 == 0 {
			_t1677 := p.parse_loop()
			loop961 := _t1677
			_t1678 := &pb.Construct{}
			_t1678.ConstructType = &pb.Construct_Loop{Loop: loop961}
			_t1676 = _t1678
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1673 = _t1676
	}
	result964 := _t1673
	p.recordSpan(int(span_start963), "Construct")
	return result964
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start967 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1679 := p.parse_init()
	init965 := _t1679
	_t1680 := p.parse_script()
	script966 := _t1680
	p.consumeLiteral(")")
	_t1681 := &pb.Loop{Init: init965, Body: script966}
	result968 := _t1681
	p.recordSpan(int(span_start967), "Loop")
	return result968
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs969 := []*pb.Instruction{}
	cond970 := p.matchLookaheadLiteral("(", 0)
	for cond970 {
		_t1682 := p.parse_instruction()
		item971 := _t1682
		xs969 = append(xs969, item971)
		cond970 = p.matchLookaheadLiteral("(", 0)
	}
	instructions972 := xs969
	p.consumeLiteral(")")
	return instructions972
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start979 := int64(p.spanStart())
	var _t1683 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1684 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1684 = 1
		} else {
			var _t1685 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1685 = 4
			} else {
				var _t1686 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1686 = 3
				} else {
					var _t1687 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1687 = 2
					} else {
						var _t1688 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1688 = 0
						} else {
							_t1688 = -1
						}
						_t1687 = _t1688
					}
					_t1686 = _t1687
				}
				_t1685 = _t1686
			}
			_t1684 = _t1685
		}
		_t1683 = _t1684
	} else {
		_t1683 = -1
	}
	prediction973 := _t1683
	var _t1689 *pb.Instruction
	if prediction973 == 4 {
		_t1690 := p.parse_monus_def()
		monus_def978 := _t1690
		_t1691 := &pb.Instruction{}
		_t1691.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def978}
		_t1689 = _t1691
	} else {
		var _t1692 *pb.Instruction
		if prediction973 == 3 {
			_t1693 := p.parse_monoid_def()
			monoid_def977 := _t1693
			_t1694 := &pb.Instruction{}
			_t1694.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def977}
			_t1692 = _t1694
		} else {
			var _t1695 *pb.Instruction
			if prediction973 == 2 {
				_t1696 := p.parse_break()
				break976 := _t1696
				_t1697 := &pb.Instruction{}
				_t1697.InstrType = &pb.Instruction_Break{Break: break976}
				_t1695 = _t1697
			} else {
				var _t1698 *pb.Instruction
				if prediction973 == 1 {
					_t1699 := p.parse_upsert()
					upsert975 := _t1699
					_t1700 := &pb.Instruction{}
					_t1700.InstrType = &pb.Instruction_Upsert{Upsert: upsert975}
					_t1698 = _t1700
				} else {
					var _t1701 *pb.Instruction
					if prediction973 == 0 {
						_t1702 := p.parse_assign()
						assign974 := _t1702
						_t1703 := &pb.Instruction{}
						_t1703.InstrType = &pb.Instruction_Assign{Assign: assign974}
						_t1701 = _t1703
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1698 = _t1701
				}
				_t1695 = _t1698
			}
			_t1692 = _t1695
		}
		_t1689 = _t1692
	}
	result980 := _t1689
	p.recordSpan(int(span_start979), "Instruction")
	return result980
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1704 := p.parse_relation_id()
	relation_id981 := _t1704
	_t1705 := p.parse_abstraction()
	abstraction982 := _t1705
	var _t1706 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1707 := p.parse_attrs()
		_t1706 = _t1707
	}
	attrs983 := _t1706
	p.consumeLiteral(")")
	_t1708 := attrs983
	if attrs983 == nil {
		_t1708 = []*pb.Attribute{}
	}
	_t1709 := &pb.Assign{Name: relation_id981, Body: abstraction982, Attrs: _t1708}
	result985 := _t1709
	p.recordSpan(int(span_start984), "Assign")
	return result985
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start989 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1710 := p.parse_relation_id()
	relation_id986 := _t1710
	_t1711 := p.parse_abstraction_with_arity()
	abstraction_with_arity987 := _t1711
	var _t1712 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1713 := p.parse_attrs()
		_t1712 = _t1713
	}
	attrs988 := _t1712
	p.consumeLiteral(")")
	_t1714 := attrs988
	if attrs988 == nil {
		_t1714 = []*pb.Attribute{}
	}
	_t1715 := &pb.Upsert{Name: relation_id986, Body: abstraction_with_arity987[0].(*pb.Abstraction), Attrs: _t1714, ValueArity: abstraction_with_arity987[1].(int64)}
	result990 := _t1715
	p.recordSpan(int(span_start989), "Upsert")
	return result990
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1716 := p.parse_bindings()
	bindings991 := _t1716
	_t1717 := p.parse_formula()
	formula992 := _t1717
	p.consumeLiteral(")")
	_t1718 := &pb.Abstraction{Vars: listConcat(bindings991[0].([]*pb.Binding), bindings991[1].([]*pb.Binding)), Value: formula992}
	return []interface{}{_t1718, int64(len(bindings991[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start996 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1719 := p.parse_relation_id()
	relation_id993 := _t1719
	_t1720 := p.parse_abstraction()
	abstraction994 := _t1720
	var _t1721 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1722 := p.parse_attrs()
		_t1721 = _t1722
	}
	attrs995 := _t1721
	p.consumeLiteral(")")
	_t1723 := attrs995
	if attrs995 == nil {
		_t1723 = []*pb.Attribute{}
	}
	_t1724 := &pb.Break{Name: relation_id993, Body: abstraction994, Attrs: _t1723}
	result997 := _t1724
	p.recordSpan(int(span_start996), "Break")
	return result997
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1725 := p.parse_monoid()
	monoid998 := _t1725
	_t1726 := p.parse_relation_id()
	relation_id999 := _t1726
	_t1727 := p.parse_abstraction_with_arity()
	abstraction_with_arity1000 := _t1727
	var _t1728 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1729 := p.parse_attrs()
		_t1728 = _t1729
	}
	attrs1001 := _t1728
	p.consumeLiteral(")")
	_t1730 := attrs1001
	if attrs1001 == nil {
		_t1730 = []*pb.Attribute{}
	}
	_t1731 := &pb.MonoidDef{Monoid: monoid998, Name: relation_id999, Body: abstraction_with_arity1000[0].(*pb.Abstraction), Attrs: _t1730, ValueArity: abstraction_with_arity1000[1].(int64)}
	result1003 := _t1731
	p.recordSpan(int(span_start1002), "MonoidDef")
	return result1003
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1009 := int64(p.spanStart())
	var _t1732 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1733 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1733 = 3
		} else {
			var _t1734 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1734 = 0
			} else {
				var _t1735 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1735 = 1
				} else {
					var _t1736 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1736 = 2
					} else {
						_t1736 = -1
					}
					_t1735 = _t1736
				}
				_t1734 = _t1735
			}
			_t1733 = _t1734
		}
		_t1732 = _t1733
	} else {
		_t1732 = -1
	}
	prediction1004 := _t1732
	var _t1737 *pb.Monoid
	if prediction1004 == 3 {
		_t1738 := p.parse_sum_monoid()
		sum_monoid1008 := _t1738
		_t1739 := &pb.Monoid{}
		_t1739.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1008}
		_t1737 = _t1739
	} else {
		var _t1740 *pb.Monoid
		if prediction1004 == 2 {
			_t1741 := p.parse_max_monoid()
			max_monoid1007 := _t1741
			_t1742 := &pb.Monoid{}
			_t1742.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1007}
			_t1740 = _t1742
		} else {
			var _t1743 *pb.Monoid
			if prediction1004 == 1 {
				_t1744 := p.parse_min_monoid()
				min_monoid1006 := _t1744
				_t1745 := &pb.Monoid{}
				_t1745.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1006}
				_t1743 = _t1745
			} else {
				var _t1746 *pb.Monoid
				if prediction1004 == 0 {
					_t1747 := p.parse_or_monoid()
					or_monoid1005 := _t1747
					_t1748 := &pb.Monoid{}
					_t1748.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1005}
					_t1746 = _t1748
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1743 = _t1746
			}
			_t1740 = _t1743
		}
		_t1737 = _t1740
	}
	result1010 := _t1737
	p.recordSpan(int(span_start1009), "Monoid")
	return result1010
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1011 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1749 := &pb.OrMonoid{}
	result1012 := _t1749
	p.recordSpan(int(span_start1011), "OrMonoid")
	return result1012
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1750 := p.parse_type()
	type1013 := _t1750
	p.consumeLiteral(")")
	_t1751 := &pb.MinMonoid{Type: type1013}
	result1015 := _t1751
	p.recordSpan(int(span_start1014), "MinMonoid")
	return result1015
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1752 := p.parse_type()
	type1016 := _t1752
	p.consumeLiteral(")")
	_t1753 := &pb.MaxMonoid{Type: type1016}
	result1018 := _t1753
	p.recordSpan(int(span_start1017), "MaxMonoid")
	return result1018
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1020 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1754 := p.parse_type()
	type1019 := _t1754
	p.consumeLiteral(")")
	_t1755 := &pb.SumMonoid{Type: type1019}
	result1021 := _t1755
	p.recordSpan(int(span_start1020), "SumMonoid")
	return result1021
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1756 := p.parse_monoid()
	monoid1022 := _t1756
	_t1757 := p.parse_relation_id()
	relation_id1023 := _t1757
	_t1758 := p.parse_abstraction_with_arity()
	abstraction_with_arity1024 := _t1758
	var _t1759 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1760 := p.parse_attrs()
		_t1759 = _t1760
	}
	attrs1025 := _t1759
	p.consumeLiteral(")")
	_t1761 := attrs1025
	if attrs1025 == nil {
		_t1761 = []*pb.Attribute{}
	}
	_t1762 := &pb.MonusDef{Monoid: monoid1022, Name: relation_id1023, Body: abstraction_with_arity1024[0].(*pb.Abstraction), Attrs: _t1761, ValueArity: abstraction_with_arity1024[1].(int64)}
	result1027 := _t1762
	p.recordSpan(int(span_start1026), "MonusDef")
	return result1027
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1763 := p.parse_relation_id()
	relation_id1028 := _t1763
	_t1764 := p.parse_abstraction()
	abstraction1029 := _t1764
	_t1765 := p.parse_functional_dependency_keys()
	functional_dependency_keys1030 := _t1765
	_t1766 := p.parse_functional_dependency_values()
	functional_dependency_values1031 := _t1766
	p.consumeLiteral(")")
	_t1767 := &pb.FunctionalDependency{Guard: abstraction1029, Keys: functional_dependency_keys1030, Values: functional_dependency_values1031}
	_t1768 := &pb.Constraint{Name: relation_id1028}
	_t1768.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1767}
	result1033 := _t1768
	p.recordSpan(int(span_start1032), "Constraint")
	return result1033
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1034 := []*pb.Var{}
	cond1035 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1035 {
		_t1769 := p.parse_var()
		item1036 := _t1769
		xs1034 = append(xs1034, item1036)
		cond1035 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1037 := xs1034
	p.consumeLiteral(")")
	return vars1037
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1038 := []*pb.Var{}
	cond1039 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1039 {
		_t1770 := p.parse_var()
		item1040 := _t1770
		xs1038 = append(xs1038, item1040)
		cond1039 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1041 := xs1038
	p.consumeLiteral(")")
	return vars1041
}

func (p *Parser) parse_data() *pb.Data {
	span_start1047 := int64(p.spanStart())
	var _t1771 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1772 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1772 = 3
		} else {
			var _t1773 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1773 = 0
			} else {
				var _t1774 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1774 = 2
				} else {
					var _t1775 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1775 = 1
					} else {
						_t1775 = -1
					}
					_t1774 = _t1775
				}
				_t1773 = _t1774
			}
			_t1772 = _t1773
		}
		_t1771 = _t1772
	} else {
		_t1771 = -1
	}
	prediction1042 := _t1771
	var _t1776 *pb.Data
	if prediction1042 == 3 {
		_t1777 := p.parse_iceberg_data()
		iceberg_data1046 := _t1777
		_t1778 := &pb.Data{}
		_t1778.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1046}
		_t1776 = _t1778
	} else {
		var _t1779 *pb.Data
		if prediction1042 == 2 {
			_t1780 := p.parse_csv_data()
			csv_data1045 := _t1780
			_t1781 := &pb.Data{}
			_t1781.DataType = &pb.Data_CsvData{CsvData: csv_data1045}
			_t1779 = _t1781
		} else {
			var _t1782 *pb.Data
			if prediction1042 == 1 {
				_t1783 := p.parse_betree_relation()
				betree_relation1044 := _t1783
				_t1784 := &pb.Data{}
				_t1784.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1044}
				_t1782 = _t1784
			} else {
				var _t1785 *pb.Data
				if prediction1042 == 0 {
					_t1786 := p.parse_edb()
					edb1043 := _t1786
					_t1787 := &pb.Data{}
					_t1787.DataType = &pb.Data_Edb{Edb: edb1043}
					_t1785 = _t1787
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1782 = _t1785
			}
			_t1779 = _t1782
		}
		_t1776 = _t1779
	}
	result1048 := _t1776
	p.recordSpan(int(span_start1047), "Data")
	return result1048
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1788 := p.parse_relation_id()
	relation_id1049 := _t1788
	_t1789 := p.parse_edb_path()
	edb_path1050 := _t1789
	_t1790 := p.parse_edb_types()
	edb_types1051 := _t1790
	p.consumeLiteral(")")
	_t1791 := &pb.EDB{TargetId: relation_id1049, Path: edb_path1050, Types: edb_types1051}
	result1053 := _t1791
	p.recordSpan(int(span_start1052), "EDB")
	return result1053
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1054 := []string{}
	cond1055 := p.matchLookaheadTerminal("STRING", 0)
	for cond1055 {
		item1056 := p.consumeTerminal("STRING").Value.str
		xs1054 = append(xs1054, item1056)
		cond1055 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1057 := xs1054
	p.consumeLiteral("]")
	return strings1057
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1058 := []*pb.Type{}
	cond1059 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1059 {
		_t1792 := p.parse_type()
		item1060 := _t1792
		xs1058 = append(xs1058, item1060)
		cond1059 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1061 := xs1058
	p.consumeLiteral("]")
	return types1061
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1064 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1793 := p.parse_relation_id()
	relation_id1062 := _t1793
	_t1794 := p.parse_betree_info()
	betree_info1063 := _t1794
	p.consumeLiteral(")")
	_t1795 := &pb.BeTreeRelation{Name: relation_id1062, RelationInfo: betree_info1063}
	result1065 := _t1795
	p.recordSpan(int(span_start1064), "BeTreeRelation")
	return result1065
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1069 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1796 := p.parse_betree_info_key_types()
	betree_info_key_types1066 := _t1796
	_t1797 := p.parse_betree_info_value_types()
	betree_info_value_types1067 := _t1797
	_t1798 := p.parse_config_dict()
	config_dict1068 := _t1798
	p.consumeLiteral(")")
	_t1799 := p.construct_betree_info(betree_info_key_types1066, betree_info_value_types1067, config_dict1068)
	result1070 := _t1799
	p.recordSpan(int(span_start1069), "BeTreeInfo")
	return result1070
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1071 := []*pb.Type{}
	cond1072 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1072 {
		_t1800 := p.parse_type()
		item1073 := _t1800
		xs1071 = append(xs1071, item1073)
		cond1072 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1074 := xs1071
	p.consumeLiteral(")")
	return types1074
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1075 := []*pb.Type{}
	cond1076 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1076 {
		_t1801 := p.parse_type()
		item1077 := _t1801
		xs1075 = append(xs1075, item1077)
		cond1076 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1078 := xs1075
	p.consumeLiteral(")")
	return types1078
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1083 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1802 := p.parse_csvlocator()
	csvlocator1079 := _t1802
	_t1803 := p.parse_csv_config()
	csv_config1080 := _t1803
	_t1804 := p.parse_gnf_columns()
	gnf_columns1081 := _t1804
	_t1805 := p.parse_csv_asof()
	csv_asof1082 := _t1805
	p.consumeLiteral(")")
	_t1806 := &pb.CSVData{Locator: csvlocator1079, Config: csv_config1080, Columns: gnf_columns1081, Asof: csv_asof1082}
	result1084 := _t1806
	p.recordSpan(int(span_start1083), "CSVData")
	return result1084
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1807 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1808 := p.parse_csv_locator_paths()
		_t1807 = _t1808
	}
	csv_locator_paths1085 := _t1807
	var _t1809 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1810 := p.parse_csv_locator_inline_data()
		_t1809 = ptr(_t1810)
	}
	csv_locator_inline_data1086 := _t1809
	p.consumeLiteral(")")
	_t1811 := csv_locator_paths1085
	if csv_locator_paths1085 == nil {
		_t1811 = []string{}
	}
	_t1812 := &pb.CSVLocator{Paths: _t1811, InlineData: []byte(deref(csv_locator_inline_data1086, ""))}
	result1088 := _t1812
	p.recordSpan(int(span_start1087), "CSVLocator")
	return result1088
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1089 := []string{}
	cond1090 := p.matchLookaheadTerminal("STRING", 0)
	for cond1090 {
		item1091 := p.consumeTerminal("STRING").Value.str
		xs1089 = append(xs1089, item1091)
		cond1090 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1092 := xs1089
	p.consumeLiteral(")")
	return strings1092
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1093 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1093
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1095 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1813 := p.parse_config_dict()
	config_dict1094 := _t1813
	p.consumeLiteral(")")
	_t1814 := p.construct_csv_config(config_dict1094)
	result1096 := _t1814
	p.recordSpan(int(span_start1095), "CSVConfig")
	return result1096
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1097 := []*pb.GNFColumn{}
	cond1098 := p.matchLookaheadLiteral("(", 0)
	for cond1098 {
		_t1815 := p.parse_gnf_column()
		item1099 := _t1815
		xs1097 = append(xs1097, item1099)
		cond1098 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1100 := xs1097
	p.consumeLiteral(")")
	return gnf_columns1100
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1816 := p.parse_gnf_column_path()
	gnf_column_path1101 := _t1816
	var _t1817 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1818 := p.parse_relation_id()
		_t1817 = _t1818
	}
	relation_id1102 := _t1817
	p.consumeLiteral("[")
	xs1103 := []*pb.Type{}
	cond1104 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1104 {
		_t1819 := p.parse_type()
		item1105 := _t1819
		xs1103 = append(xs1103, item1105)
		cond1104 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1106 := xs1103
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1820 := &pb.GNFColumn{ColumnPath: gnf_column_path1101, TargetId: relation_id1102, Types: types1106}
	result1108 := _t1820
	p.recordSpan(int(span_start1107), "GNFColumn")
	return result1108
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1821 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1821 = 1
	} else {
		var _t1822 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1822 = 0
		} else {
			_t1822 = -1
		}
		_t1821 = _t1822
	}
	prediction1109 := _t1821
	var _t1823 []string
	if prediction1109 == 1 {
		p.consumeLiteral("[")
		xs1111 := []string{}
		cond1112 := p.matchLookaheadTerminal("STRING", 0)
		for cond1112 {
			item1113 := p.consumeTerminal("STRING").Value.str
			xs1111 = append(xs1111, item1113)
			cond1112 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1114 := xs1111
		p.consumeLiteral("]")
		_t1823 = strings1114
	} else {
		var _t1824 []string
		if prediction1109 == 0 {
			string1110 := p.consumeTerminal("STRING").Value.str
			_ = string1110
			_t1824 = []string{string1110}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1823 = _t1824
	}
	return _t1823
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1115 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1115
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1120 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1825 := p.parse_iceberg_locator()
	iceberg_locator1116 := _t1825
	_t1826 := p.parse_iceberg_config()
	iceberg_config1117 := _t1826
	_t1827 := p.parse_gnf_columns()
	gnf_columns1118 := _t1827
	var _t1828 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1829 := p.parse_iceberg_to_snapshot()
		_t1828 = ptr(_t1829)
	}
	iceberg_to_snapshot1119 := _t1828
	p.consumeLiteral(")")
	_t1830 := &pb.IcebergData{Locator: iceberg_locator1116, Config: iceberg_config1117, Columns: gnf_columns1118, ToSnapshot: deref(iceberg_to_snapshot1119, "")}
	result1121 := _t1830
	p.recordSpan(int(span_start1120), "IcebergData")
	return result1121
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	string1122 := p.consumeTerminal("STRING").Value.str
	_t1831 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1123 := _t1831
	string_41124 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	_t1832 := &pb.IcebergLocator{TableName: string1122, Namespace: iceberg_locator_namespace1123, Warehouse: string_41124}
	result1126 := _t1832
	p.recordSpan(int(span_start1125), "IcebergLocator")
	return result1126
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1127 := []string{}
	cond1128 := p.matchLookaheadTerminal("STRING", 0)
	for cond1128 {
		item1129 := p.consumeTerminal("STRING").Value.str
		xs1127 = append(xs1127, item1129)
		cond1128 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1130 := xs1127
	p.consumeLiteral(")")
	return strings1130
}

func (p *Parser) parse_iceberg_config() *pb.IcebergConfig {
	span_start1135 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_config")
	string1131 := p.consumeTerminal("STRING").Value.str
	var _t1833 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1834 := p.parse_iceberg_config_scope()
		_t1833 = ptr(_t1834)
	}
	iceberg_config_scope1132 := _t1833
	var _t1835 [][]interface{}
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("properties", 1)) {
		_t1836 := p.parse_iceberg_config_properties()
		_t1835 = _t1836
	}
	iceberg_config_properties1133 := _t1835
	var _t1837 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1838 := p.parse_iceberg_config_credentials()
		_t1837 = _t1838
	}
	iceberg_config_credentials1134 := _t1837
	p.consumeLiteral(")")
	_t1839 := p.construct_iceberg_config(string1131, iceberg_config_scope1132, iceberg_config_properties1133, iceberg_config_credentials1134)
	result1136 := _t1839
	p.recordSpan(int(span_start1135), "IcebergConfig")
	return result1136
}

func (p *Parser) parse_iceberg_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1137 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1137
}

func (p *Parser) parse_iceberg_config_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1138 := [][]interface{}{}
	cond1139 := p.matchLookaheadLiteral("(", 0)
	for cond1139 {
		_t1840 := p.parse_iceberg_kv_pair()
		item1140 := _t1840
		xs1138 = append(xs1138, item1140)
		cond1139 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_kv_pairs1141 := xs1138
	p.consumeLiteral(")")
	return iceberg_kv_pairs1141
}

func (p *Parser) parse_iceberg_kv_pair() []interface{} {
	p.consumeLiteral("(")
	string1142 := p.consumeTerminal("STRING").Value.str
	string_21143 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1142, string_21143}
}

func (p *Parser) parse_iceberg_config_credentials() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("credentials")
	xs1144 := [][]interface{}{}
	cond1145 := p.matchLookaheadLiteral("(", 0)
	for cond1145 {
		_t1841 := p.parse_iceberg_kv_pair()
		item1146 := _t1841
		xs1144 = append(xs1144, item1146)
		cond1145 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_kv_pairs1147 := xs1144
	p.consumeLiteral(")")
	return iceberg_kv_pairs1147
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1148 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1148
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1842 := p.parse_fragment_id()
	fragment_id1149 := _t1842
	p.consumeLiteral(")")
	_t1843 := &pb.Undefine{FragmentId: fragment_id1149}
	result1151 := _t1843
	p.recordSpan(int(span_start1150), "Undefine")
	return result1151
}

func (p *Parser) parse_context() *pb.Context {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1152 := []*pb.RelationId{}
	cond1153 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1153 {
		_t1844 := p.parse_relation_id()
		item1154 := _t1844
		xs1152 = append(xs1152, item1154)
		cond1153 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1155 := xs1152
	p.consumeLiteral(")")
	_t1845 := &pb.Context{Relations: relation_ids1155}
	result1157 := _t1845
	p.recordSpan(int(span_start1156), "Context")
	return result1157
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1162 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1158 := []*pb.SnapshotMapping{}
	cond1159 := p.matchLookaheadLiteral("[", 0)
	for cond1159 {
		_t1846 := p.parse_snapshot_mapping()
		item1160 := _t1846
		xs1158 = append(xs1158, item1160)
		cond1159 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1161 := xs1158
	p.consumeLiteral(")")
	_t1847 := &pb.Snapshot{Mappings: snapshot_mappings1161}
	result1163 := _t1847
	p.recordSpan(int(span_start1162), "Snapshot")
	return result1163
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1166 := int64(p.spanStart())
	_t1848 := p.parse_edb_path()
	edb_path1164 := _t1848
	_t1849 := p.parse_relation_id()
	relation_id1165 := _t1849
	_t1850 := &pb.SnapshotMapping{DestinationPath: edb_path1164, SourceRelation: relation_id1165}
	result1167 := _t1850
	p.recordSpan(int(span_start1166), "SnapshotMapping")
	return result1167
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1168 := []*pb.Read{}
	cond1169 := p.matchLookaheadLiteral("(", 0)
	for cond1169 {
		_t1851 := p.parse_read()
		item1170 := _t1851
		xs1168 = append(xs1168, item1170)
		cond1169 = p.matchLookaheadLiteral("(", 0)
	}
	reads1171 := xs1168
	p.consumeLiteral(")")
	return reads1171
}

func (p *Parser) parse_read() *pb.Read {
	span_start1178 := int64(p.spanStart())
	var _t1852 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1853 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1853 = 2
		} else {
			var _t1854 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1854 = 1
			} else {
				var _t1855 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1855 = 4
				} else {
					var _t1856 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1856 = 0
					} else {
						var _t1857 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1857 = 3
						} else {
							_t1857 = -1
						}
						_t1856 = _t1857
					}
					_t1855 = _t1856
				}
				_t1854 = _t1855
			}
			_t1853 = _t1854
		}
		_t1852 = _t1853
	} else {
		_t1852 = -1
	}
	prediction1172 := _t1852
	var _t1858 *pb.Read
	if prediction1172 == 4 {
		_t1859 := p.parse_export()
		export1177 := _t1859
		_t1860 := &pb.Read{}
		_t1860.ReadType = &pb.Read_Export{Export: export1177}
		_t1858 = _t1860
	} else {
		var _t1861 *pb.Read
		if prediction1172 == 3 {
			_t1862 := p.parse_abort()
			abort1176 := _t1862
			_t1863 := &pb.Read{}
			_t1863.ReadType = &pb.Read_Abort{Abort: abort1176}
			_t1861 = _t1863
		} else {
			var _t1864 *pb.Read
			if prediction1172 == 2 {
				_t1865 := p.parse_what_if()
				what_if1175 := _t1865
				_t1866 := &pb.Read{}
				_t1866.ReadType = &pb.Read_WhatIf{WhatIf: what_if1175}
				_t1864 = _t1866
			} else {
				var _t1867 *pb.Read
				if prediction1172 == 1 {
					_t1868 := p.parse_output()
					output1174 := _t1868
					_t1869 := &pb.Read{}
					_t1869.ReadType = &pb.Read_Output{Output: output1174}
					_t1867 = _t1869
				} else {
					var _t1870 *pb.Read
					if prediction1172 == 0 {
						_t1871 := p.parse_demand()
						demand1173 := _t1871
						_t1872 := &pb.Read{}
						_t1872.ReadType = &pb.Read_Demand{Demand: demand1173}
						_t1870 = _t1872
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1867 = _t1870
				}
				_t1864 = _t1867
			}
			_t1861 = _t1864
		}
		_t1858 = _t1861
	}
	result1179 := _t1858
	p.recordSpan(int(span_start1178), "Read")
	return result1179
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1181 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1873 := p.parse_relation_id()
	relation_id1180 := _t1873
	p.consumeLiteral(")")
	_t1874 := &pb.Demand{RelationId: relation_id1180}
	result1182 := _t1874
	p.recordSpan(int(span_start1181), "Demand")
	return result1182
}

func (p *Parser) parse_output() *pb.Output {
	span_start1185 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1875 := p.parse_name()
	name1183 := _t1875
	_t1876 := p.parse_relation_id()
	relation_id1184 := _t1876
	p.consumeLiteral(")")
	_t1877 := &pb.Output{Name: name1183, RelationId: relation_id1184}
	result1186 := _t1877
	p.recordSpan(int(span_start1185), "Output")
	return result1186
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1878 := p.parse_name()
	name1187 := _t1878
	_t1879 := p.parse_epoch()
	epoch1188 := _t1879
	p.consumeLiteral(")")
	_t1880 := &pb.WhatIf{Branch: name1187, Epoch: epoch1188}
	result1190 := _t1880
	p.recordSpan(int(span_start1189), "WhatIf")
	return result1190
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1193 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1881 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1882 := p.parse_name()
		_t1881 = ptr(_t1882)
	}
	name1191 := _t1881
	_t1883 := p.parse_relation_id()
	relation_id1192 := _t1883
	p.consumeLiteral(")")
	_t1884 := &pb.Abort{Name: deref(name1191, "abort"), RelationId: relation_id1192}
	result1194 := _t1884
	p.recordSpan(int(span_start1193), "Abort")
	return result1194
}

func (p *Parser) parse_export() *pb.Export {
	span_start1196 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1885 := p.parse_export_csv_config()
	export_csv_config1195 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.Export{}
	_t1886.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1195}
	result1197 := _t1886
	p.recordSpan(int(span_start1196), "Export")
	return result1197
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1205 := int64(p.spanStart())
	var _t1887 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1888 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1888 = 0
		} else {
			var _t1889 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1889 = 1
			} else {
				_t1889 = -1
			}
			_t1888 = _t1889
		}
		_t1887 = _t1888
	} else {
		_t1887 = -1
	}
	prediction1198 := _t1887
	var _t1890 *pb.ExportCSVConfig
	if prediction1198 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1891 := p.parse_export_csv_path()
		export_csv_path1202 := _t1891
		_t1892 := p.parse_export_csv_columns_list()
		export_csv_columns_list1203 := _t1892
		_t1893 := p.parse_config_dict()
		config_dict1204 := _t1893
		p.consumeLiteral(")")
		_t1894 := p.construct_export_csv_config(export_csv_path1202, export_csv_columns_list1203, config_dict1204)
		_t1890 = _t1894
	} else {
		var _t1895 *pb.ExportCSVConfig
		if prediction1198 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1896 := p.parse_export_csv_path()
			export_csv_path1199 := _t1896
			_t1897 := p.parse_export_csv_source()
			export_csv_source1200 := _t1897
			_t1898 := p.parse_csv_config()
			csv_config1201 := _t1898
			p.consumeLiteral(")")
			_t1899 := p.construct_export_csv_config_with_source(export_csv_path1199, export_csv_source1200, csv_config1201)
			_t1895 = _t1899
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1890 = _t1895
	}
	result1206 := _t1890
	p.recordSpan(int(span_start1205), "ExportCSVConfig")
	return result1206
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1207 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1207
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1214 := int64(p.spanStart())
	var _t1900 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1901 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1901 = 1
		} else {
			var _t1902 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1902 = 0
			} else {
				_t1902 = -1
			}
			_t1901 = _t1902
		}
		_t1900 = _t1901
	} else {
		_t1900 = -1
	}
	prediction1208 := _t1900
	var _t1903 *pb.ExportCSVSource
	if prediction1208 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1904 := p.parse_relation_id()
		relation_id1213 := _t1904
		p.consumeLiteral(")")
		_t1905 := &pb.ExportCSVSource{}
		_t1905.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1213}
		_t1903 = _t1905
	} else {
		var _t1906 *pb.ExportCSVSource
		if prediction1208 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1209 := []*pb.ExportCSVColumn{}
			cond1210 := p.matchLookaheadLiteral("(", 0)
			for cond1210 {
				_t1907 := p.parse_export_csv_column()
				item1211 := _t1907
				xs1209 = append(xs1209, item1211)
				cond1210 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1212 := xs1209
			p.consumeLiteral(")")
			_t1908 := &pb.ExportCSVColumns{Columns: export_csv_columns1212}
			_t1909 := &pb.ExportCSVSource{}
			_t1909.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1908}
			_t1906 = _t1909
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1903 = _t1906
	}
	result1215 := _t1903
	p.recordSpan(int(span_start1214), "ExportCSVSource")
	return result1215
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1218 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1216 := p.consumeTerminal("STRING").Value.str
	_t1910 := p.parse_relation_id()
	relation_id1217 := _t1910
	p.consumeLiteral(")")
	_t1911 := &pb.ExportCSVColumn{ColumnName: string1216, ColumnData: relation_id1217}
	result1219 := _t1911
	p.recordSpan(int(span_start1218), "ExportCSVColumn")
	return result1219
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1220 := []*pb.ExportCSVColumn{}
	cond1221 := p.matchLookaheadLiteral("(", 0)
	for cond1221 {
		_t1912 := p.parse_export_csv_column()
		item1222 := _t1912
		xs1220 = append(xs1220, item1222)
		cond1221 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1223 := xs1220
	p.consumeLiteral(")")
	return export_csv_columns1223
}


// ParseTransaction parses the input string and returns (result, provenance, error).
func ParseTransaction(input string) (result *pb.Transaction, provenance map[int]Span, err error) {
	defer func() {
		if r := recover(); r != nil {
			if pe, ok := r.(ParseError); ok {
				err = pe
				return
			}
			panic(r)
		}
	}()

	lexer := NewLexer(input)
	parser := NewParser(lexer.tokens, input)
	result = parser.parse_transaction()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, parser.Provenance, nil
}

// ParseFragment parses the input string and returns (result, provenance, error).
func ParseFragment(input string) (result *pb.Fragment, provenance map[int]Span, err error) {
	defer func() {
		if r := recover(); r != nil {
			if pe, ok := r.(ParseError); ok {
				err = pe
				return
			}
			panic(r)
		}
	}()

	lexer := NewLexer(input)
	parser := NewParser(lexer.tokens, input)
	result = parser.parse_fragment()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, parser.Provenance, nil
}

// Parse parses the input string and returns (result, provenance, error).
func Parse(input string) (result *pb.Transaction, provenance map[int]Span, err error) {
	return ParseTransaction(input)
}
