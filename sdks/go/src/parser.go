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
		if math.IsInf(float64(tv.f32), 0) {
			return "inf32"
		}
		if math.IsNaN(float64(tv.f32)) {
			return "nan32"
		}
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
		{"FLOAT32", regexp.MustCompile(`^([-]?\d+\.\d+f32|inf32|nan32)`), func(s string) TokenValue { return TokenValue{kind: kindFloat32, f32: scanFloat32(s)} }},
		{"FLOAT", regexp.MustCompile(`^([-]?\d+\.\d+|inf|nan)`), func(s string) TokenValue { return TokenValue{kind: kindFloat64, f64: scanFloat(s)} }},
		{"INT32", regexp.MustCompile(`^[-]?\d+i32`), func(s string) TokenValue { return TokenValue{kind: kindInt32, i32: scanInt32(s)} }},
		{"INT", regexp.MustCompile(`^[-]?\d+`), func(s string) TokenValue { return TokenValue{kind: kindInt64, i64: scanInt(s)} }},
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
	if s == "inf32" {
		return float32(math.Inf(1))
	} else if s == "nan32" {
		return float32(math.NaN())
	}
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
	var _t1922 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1922
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1923 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1923
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1924 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1924
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1925 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1925
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1926 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1926
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1927 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1927
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1928 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1928
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1929 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1929
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1930 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1930
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1931 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1931
	_t1932 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1932
	_t1933 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1933
	_t1934 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1934
	_t1935 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1935
	_t1936 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1936
	_t1937 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1937
	_t1938 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1938
	_t1939 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1939
	_t1940 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1940
	_t1941 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1941
	_t1942 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1942
	_t1943 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1943
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1944 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1944
	_t1945 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1945
	_t1946 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1946
	_t1947 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1947
	_t1948 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1948
	_t1949 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1949
	_t1950 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1950
	_t1951 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1951
	_t1952 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1952
	_t1953 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1953.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1953.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1953
	_t1954 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1954
}

func (p *Parser) default_configure() *pb.Configure {
	_t1955 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1955
	_t1956 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1956
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
	_t1957 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1957
	_t1958 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1958
	_t1959 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1959
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1960 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1960
	_t1961 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1961
	_t1962 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1962
	_t1963 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1963
	_t1964 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1964
	_t1965 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1965
	_t1966 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1966
	_t1967 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1967
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1968 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1968
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start610 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1208 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1209 := p.parse_configure()
		_t1208 = _t1209
	}
	configure604 := _t1208
	var _t1210 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1211 := p.parse_sync()
		_t1210 = _t1211
	}
	sync605 := _t1210
	xs606 := []*pb.Epoch{}
	cond607 := p.matchLookaheadLiteral("(", 0)
	for cond607 {
		_t1212 := p.parse_epoch()
		item608 := _t1212
		xs606 = append(xs606, item608)
		cond607 = p.matchLookaheadLiteral("(", 0)
	}
	epochs609 := xs606
	p.consumeLiteral(")")
	_t1213 := p.default_configure()
	_t1214 := configure604
	if configure604 == nil {
		_t1214 = _t1213
	}
	_t1215 := &pb.Transaction{Epochs: epochs609, Configure: _t1214, Sync: sync605}
	result611 := _t1215
	p.recordSpan(int(span_start610), "Transaction")
	return result611
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start613 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1216 := p.parse_config_dict()
	config_dict612 := _t1216
	p.consumeLiteral(")")
	_t1217 := p.construct_configure(config_dict612)
	result614 := _t1217
	p.recordSpan(int(span_start613), "Configure")
	return result614
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs615 := [][]interface{}{}
	cond616 := p.matchLookaheadLiteral(":", 0)
	for cond616 {
		_t1218 := p.parse_config_key_value()
		item617 := _t1218
		xs615 = append(xs615, item617)
		cond616 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values618 := xs615
	p.consumeLiteral("}")
	return config_key_values618
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol619 := p.consumeTerminal("SYMBOL").Value.str
	_t1219 := p.parse_raw_value()
	raw_value620 := _t1219
	return []interface{}{symbol619, raw_value620}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start634 := int64(p.spanStart())
	var _t1220 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1220 = 12
	} else {
		var _t1221 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1221 = 11
		} else {
			var _t1222 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1222 = 12
			} else {
				var _t1223 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1224 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1224 = 1
					} else {
						var _t1225 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1225 = 0
						} else {
							_t1225 = -1
						}
						_t1224 = _t1225
					}
					_t1223 = _t1224
				} else {
					var _t1226 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1226 = 7
					} else {
						var _t1227 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1227 = 8
						} else {
							var _t1228 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1228 = 2
							} else {
								var _t1229 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1229 = 3
								} else {
									var _t1230 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1230 = 9
									} else {
										var _t1231 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1231 = 4
										} else {
											var _t1232 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1232 = 5
											} else {
												var _t1233 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1233 = 6
												} else {
													var _t1234 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1234 = 10
													} else {
														_t1234 = -1
													}
													_t1233 = _t1234
												}
												_t1232 = _t1233
											}
											_t1231 = _t1232
										}
										_t1230 = _t1231
									}
									_t1229 = _t1230
								}
								_t1228 = _t1229
							}
							_t1227 = _t1228
						}
						_t1226 = _t1227
					}
					_t1223 = _t1226
				}
				_t1222 = _t1223
			}
			_t1221 = _t1222
		}
		_t1220 = _t1221
	}
	prediction621 := _t1220
	var _t1235 *pb.Value
	if prediction621 == 12 {
		_t1236 := p.parse_boolean_value()
		boolean_value633 := _t1236
		_t1237 := &pb.Value{}
		_t1237.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value633}
		_t1235 = _t1237
	} else {
		var _t1238 *pb.Value
		if prediction621 == 11 {
			p.consumeLiteral("missing")
			_t1239 := &pb.MissingValue{}
			_t1240 := &pb.Value{}
			_t1240.Value = &pb.Value_MissingValue{MissingValue: _t1239}
			_t1238 = _t1240
		} else {
			var _t1241 *pb.Value
			if prediction621 == 10 {
				decimal632 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1242 := &pb.Value{}
				_t1242.Value = &pb.Value_DecimalValue{DecimalValue: decimal632}
				_t1241 = _t1242
			} else {
				var _t1243 *pb.Value
				if prediction621 == 9 {
					int128631 := p.consumeTerminal("INT128").Value.int128
					_t1244 := &pb.Value{}
					_t1244.Value = &pb.Value_Int128Value{Int128Value: int128631}
					_t1243 = _t1244
				} else {
					var _t1245 *pb.Value
					if prediction621 == 8 {
						uint128630 := p.consumeTerminal("UINT128").Value.uint128
						_t1246 := &pb.Value{}
						_t1246.Value = &pb.Value_Uint128Value{Uint128Value: uint128630}
						_t1245 = _t1246
					} else {
						var _t1247 *pb.Value
						if prediction621 == 7 {
							uint32629 := p.consumeTerminal("UINT32").Value.u32
							_t1248 := &pb.Value{}
							_t1248.Value = &pb.Value_Uint32Value{Uint32Value: uint32629}
							_t1247 = _t1248
						} else {
							var _t1249 *pb.Value
							if prediction621 == 6 {
								float628 := p.consumeTerminal("FLOAT").Value.f64
								_t1250 := &pb.Value{}
								_t1250.Value = &pb.Value_FloatValue{FloatValue: float628}
								_t1249 = _t1250
							} else {
								var _t1251 *pb.Value
								if prediction621 == 5 {
									float32627 := p.consumeTerminal("FLOAT32").Value.f32
									_t1252 := &pb.Value{}
									_t1252.Value = &pb.Value_Float32Value{Float32Value: float32627}
									_t1251 = _t1252
								} else {
									var _t1253 *pb.Value
									if prediction621 == 4 {
										int626 := p.consumeTerminal("INT").Value.i64
										_t1254 := &pb.Value{}
										_t1254.Value = &pb.Value_IntValue{IntValue: int626}
										_t1253 = _t1254
									} else {
										var _t1255 *pb.Value
										if prediction621 == 3 {
											int32625 := p.consumeTerminal("INT32").Value.i32
											_t1256 := &pb.Value{}
											_t1256.Value = &pb.Value_Int32Value{Int32Value: int32625}
											_t1255 = _t1256
										} else {
											var _t1257 *pb.Value
											if prediction621 == 2 {
												string624 := p.consumeTerminal("STRING").Value.str
												_t1258 := &pb.Value{}
												_t1258.Value = &pb.Value_StringValue{StringValue: string624}
												_t1257 = _t1258
											} else {
												var _t1259 *pb.Value
												if prediction621 == 1 {
													_t1260 := p.parse_raw_datetime()
													raw_datetime623 := _t1260
													_t1261 := &pb.Value{}
													_t1261.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime623}
													_t1259 = _t1261
												} else {
													var _t1262 *pb.Value
													if prediction621 == 0 {
														_t1263 := p.parse_raw_date()
														raw_date622 := _t1263
														_t1264 := &pb.Value{}
														_t1264.Value = &pb.Value_DateValue{DateValue: raw_date622}
														_t1262 = _t1264
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1259 = _t1262
												}
												_t1257 = _t1259
											}
											_t1255 = _t1257
										}
										_t1253 = _t1255
									}
									_t1251 = _t1253
								}
								_t1249 = _t1251
							}
							_t1247 = _t1249
						}
						_t1245 = _t1247
					}
					_t1243 = _t1245
				}
				_t1241 = _t1243
			}
			_t1238 = _t1241
		}
		_t1235 = _t1238
	}
	result635 := _t1235
	p.recordSpan(int(span_start634), "Value")
	return result635
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start639 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int636 := p.consumeTerminal("INT").Value.i64
	int_3637 := p.consumeTerminal("INT").Value.i64
	int_4638 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1265 := &pb.DateValue{Year: int32(int636), Month: int32(int_3637), Day: int32(int_4638)}
	result640 := _t1265
	p.recordSpan(int(span_start639), "DateValue")
	return result640
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start648 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int641 := p.consumeTerminal("INT").Value.i64
	int_3642 := p.consumeTerminal("INT").Value.i64
	int_4643 := p.consumeTerminal("INT").Value.i64
	int_5644 := p.consumeTerminal("INT").Value.i64
	int_6645 := p.consumeTerminal("INT").Value.i64
	int_7646 := p.consumeTerminal("INT").Value.i64
	var _t1266 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1266 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8647 := _t1266
	p.consumeLiteral(")")
	_t1267 := &pb.DateTimeValue{Year: int32(int641), Month: int32(int_3642), Day: int32(int_4643), Hour: int32(int_5644), Minute: int32(int_6645), Second: int32(int_7646), Microsecond: int32(deref(int_8647, 0))}
	result649 := _t1267
	p.recordSpan(int(span_start648), "DateTimeValue")
	return result649
}

func (p *Parser) parse_boolean_value() bool {
	var _t1268 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1268 = 0
	} else {
		var _t1269 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1269 = 1
		} else {
			_t1269 = -1
		}
		_t1268 = _t1269
	}
	prediction650 := _t1268
	var _t1270 bool
	if prediction650 == 1 {
		p.consumeLiteral("false")
		_t1270 = false
	} else {
		var _t1271 bool
		if prediction650 == 0 {
			p.consumeLiteral("true")
			_t1271 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1270 = _t1271
	}
	return _t1270
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start655 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs651 := []*pb.FragmentId{}
	cond652 := p.matchLookaheadLiteral(":", 0)
	for cond652 {
		_t1272 := p.parse_fragment_id()
		item653 := _t1272
		xs651 = append(xs651, item653)
		cond652 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids654 := xs651
	p.consumeLiteral(")")
	_t1273 := &pb.Sync{Fragments: fragment_ids654}
	result656 := _t1273
	p.recordSpan(int(span_start655), "Sync")
	return result656
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start658 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol657 := p.consumeTerminal("SYMBOL").Value.str
	result659 := &pb.FragmentId{Id: []byte(symbol657)}
	p.recordSpan(int(span_start658), "FragmentId")
	return result659
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start662 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1274 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1275 := p.parse_epoch_writes()
		_t1274 = _t1275
	}
	epoch_writes660 := _t1274
	var _t1276 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1277 := p.parse_epoch_reads()
		_t1276 = _t1277
	}
	epoch_reads661 := _t1276
	p.consumeLiteral(")")
	_t1278 := epoch_writes660
	if epoch_writes660 == nil {
		_t1278 = []*pb.Write{}
	}
	_t1279 := epoch_reads661
	if epoch_reads661 == nil {
		_t1279 = []*pb.Read{}
	}
	_t1280 := &pb.Epoch{Writes: _t1278, Reads: _t1279}
	result663 := _t1280
	p.recordSpan(int(span_start662), "Epoch")
	return result663
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs664 := []*pb.Write{}
	cond665 := p.matchLookaheadLiteral("(", 0)
	for cond665 {
		_t1281 := p.parse_write()
		item666 := _t1281
		xs664 = append(xs664, item666)
		cond665 = p.matchLookaheadLiteral("(", 0)
	}
	writes667 := xs664
	p.consumeLiteral(")")
	return writes667
}

func (p *Parser) parse_write() *pb.Write {
	span_start673 := int64(p.spanStart())
	var _t1282 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1283 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1283 = 1
		} else {
			var _t1284 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1284 = 3
			} else {
				var _t1285 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1285 = 0
				} else {
					var _t1286 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1286 = 2
					} else {
						_t1286 = -1
					}
					_t1285 = _t1286
				}
				_t1284 = _t1285
			}
			_t1283 = _t1284
		}
		_t1282 = _t1283
	} else {
		_t1282 = -1
	}
	prediction668 := _t1282
	var _t1287 *pb.Write
	if prediction668 == 3 {
		_t1288 := p.parse_snapshot()
		snapshot672 := _t1288
		_t1289 := &pb.Write{}
		_t1289.WriteType = &pb.Write_Snapshot{Snapshot: snapshot672}
		_t1287 = _t1289
	} else {
		var _t1290 *pb.Write
		if prediction668 == 2 {
			_t1291 := p.parse_context()
			context671 := _t1291
			_t1292 := &pb.Write{}
			_t1292.WriteType = &pb.Write_Context{Context: context671}
			_t1290 = _t1292
		} else {
			var _t1293 *pb.Write
			if prediction668 == 1 {
				_t1294 := p.parse_undefine()
				undefine670 := _t1294
				_t1295 := &pb.Write{}
				_t1295.WriteType = &pb.Write_Undefine{Undefine: undefine670}
				_t1293 = _t1295
			} else {
				var _t1296 *pb.Write
				if prediction668 == 0 {
					_t1297 := p.parse_define()
					define669 := _t1297
					_t1298 := &pb.Write{}
					_t1298.WriteType = &pb.Write_Define{Define: define669}
					_t1296 = _t1298
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1293 = _t1296
			}
			_t1290 = _t1293
		}
		_t1287 = _t1290
	}
	result674 := _t1287
	p.recordSpan(int(span_start673), "Write")
	return result674
}

func (p *Parser) parse_define() *pb.Define {
	span_start676 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1299 := p.parse_fragment()
	fragment675 := _t1299
	p.consumeLiteral(")")
	_t1300 := &pb.Define{Fragment: fragment675}
	result677 := _t1300
	p.recordSpan(int(span_start676), "Define")
	return result677
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start683 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1301 := p.parse_new_fragment_id()
	new_fragment_id678 := _t1301
	xs679 := []*pb.Declaration{}
	cond680 := p.matchLookaheadLiteral("(", 0)
	for cond680 {
		_t1302 := p.parse_declaration()
		item681 := _t1302
		xs679 = append(xs679, item681)
		cond680 = p.matchLookaheadLiteral("(", 0)
	}
	declarations682 := xs679
	p.consumeLiteral(")")
	result684 := p.constructFragment(new_fragment_id678, declarations682)
	p.recordSpan(int(span_start683), "Fragment")
	return result684
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start686 := int64(p.spanStart())
	_t1303 := p.parse_fragment_id()
	fragment_id685 := _t1303
	p.startFragment(fragment_id685)
	result687 := fragment_id685
	p.recordSpan(int(span_start686), "FragmentId")
	return result687
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start693 := int64(p.spanStart())
	var _t1304 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1305 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1305 = 2
		} else {
			var _t1306 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1306 = 3
			} else {
				var _t1307 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1307 = 0
				} else {
					var _t1308 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1308 = 3
					} else {
						var _t1309 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1309 = 3
						} else {
							var _t1310 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1310 = 1
							} else {
								_t1310 = -1
							}
							_t1309 = _t1310
						}
						_t1308 = _t1309
					}
					_t1307 = _t1308
				}
				_t1306 = _t1307
			}
			_t1305 = _t1306
		}
		_t1304 = _t1305
	} else {
		_t1304 = -1
	}
	prediction688 := _t1304
	var _t1311 *pb.Declaration
	if prediction688 == 3 {
		_t1312 := p.parse_data()
		data692 := _t1312
		_t1313 := &pb.Declaration{}
		_t1313.DeclarationType = &pb.Declaration_Data{Data: data692}
		_t1311 = _t1313
	} else {
		var _t1314 *pb.Declaration
		if prediction688 == 2 {
			_t1315 := p.parse_constraint()
			constraint691 := _t1315
			_t1316 := &pb.Declaration{}
			_t1316.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint691}
			_t1314 = _t1316
		} else {
			var _t1317 *pb.Declaration
			if prediction688 == 1 {
				_t1318 := p.parse_algorithm()
				algorithm690 := _t1318
				_t1319 := &pb.Declaration{}
				_t1319.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm690}
				_t1317 = _t1319
			} else {
				var _t1320 *pb.Declaration
				if prediction688 == 0 {
					_t1321 := p.parse_def()
					def689 := _t1321
					_t1322 := &pb.Declaration{}
					_t1322.DeclarationType = &pb.Declaration_Def{Def: def689}
					_t1320 = _t1322
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1317 = _t1320
			}
			_t1314 = _t1317
		}
		_t1311 = _t1314
	}
	result694 := _t1311
	p.recordSpan(int(span_start693), "Declaration")
	return result694
}

func (p *Parser) parse_def() *pb.Def {
	span_start698 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1323 := p.parse_relation_id()
	relation_id695 := _t1323
	_t1324 := p.parse_abstraction()
	abstraction696 := _t1324
	var _t1325 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1326 := p.parse_attrs()
		_t1325 = _t1326
	}
	attrs697 := _t1325
	p.consumeLiteral(")")
	_t1327 := attrs697
	if attrs697 == nil {
		_t1327 = []*pb.Attribute{}
	}
	_t1328 := &pb.Def{Name: relation_id695, Body: abstraction696, Attrs: _t1327}
	result699 := _t1328
	p.recordSpan(int(span_start698), "Def")
	return result699
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start703 := int64(p.spanStart())
	var _t1329 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1329 = 0
	} else {
		var _t1330 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1330 = 1
		} else {
			_t1330 = -1
		}
		_t1329 = _t1330
	}
	prediction700 := _t1329
	var _t1331 *pb.RelationId
	if prediction700 == 1 {
		uint128702 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128702
		_t1331 = &pb.RelationId{IdLow: uint128702.Low, IdHigh: uint128702.High}
	} else {
		var _t1332 *pb.RelationId
		if prediction700 == 0 {
			p.consumeLiteral(":")
			symbol701 := p.consumeTerminal("SYMBOL").Value.str
			_t1332 = p.relationIdFromString(symbol701)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1331 = _t1332
	}
	result704 := _t1331
	p.recordSpan(int(span_start703), "RelationId")
	return result704
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1333 := p.parse_bindings()
	bindings705 := _t1333
	_t1334 := p.parse_formula()
	formula706 := _t1334
	p.consumeLiteral(")")
	_t1335 := &pb.Abstraction{Vars: listConcat(bindings705[0].([]*pb.Binding), bindings705[1].([]*pb.Binding)), Value: formula706}
	result708 := _t1335
	p.recordSpan(int(span_start707), "Abstraction")
	return result708
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs709 := []*pb.Binding{}
	cond710 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond710 {
		_t1336 := p.parse_binding()
		item711 := _t1336
		xs709 = append(xs709, item711)
		cond710 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings712 := xs709
	var _t1337 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1338 := p.parse_value_bindings()
		_t1337 = _t1338
	}
	value_bindings713 := _t1337
	p.consumeLiteral("]")
	_t1339 := value_bindings713
	if value_bindings713 == nil {
		_t1339 = []*pb.Binding{}
	}
	return []interface{}{bindings712, _t1339}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start716 := int64(p.spanStart())
	symbol714 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1340 := p.parse_type()
	type715 := _t1340
	_t1341 := &pb.Var{Name: symbol714}
	_t1342 := &pb.Binding{Var: _t1341, Type: type715}
	result717 := _t1342
	p.recordSpan(int(span_start716), "Binding")
	return result717
}

func (p *Parser) parse_type() *pb.Type {
	span_start733 := int64(p.spanStart())
	var _t1343 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1343 = 0
	} else {
		var _t1344 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1344 = 13
		} else {
			var _t1345 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1345 = 4
			} else {
				var _t1346 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1346 = 1
				} else {
					var _t1347 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1347 = 8
					} else {
						var _t1348 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1348 = 11
						} else {
							var _t1349 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1349 = 5
							} else {
								var _t1350 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1350 = 2
								} else {
									var _t1351 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1351 = 12
									} else {
										var _t1352 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1352 = 3
										} else {
											var _t1353 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1353 = 7
											} else {
												var _t1354 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1354 = 6
												} else {
													var _t1355 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1355 = 10
													} else {
														var _t1356 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1356 = 9
														} else {
															_t1356 = -1
														}
														_t1355 = _t1356
													}
													_t1354 = _t1355
												}
												_t1353 = _t1354
											}
											_t1352 = _t1353
										}
										_t1351 = _t1352
									}
									_t1350 = _t1351
								}
								_t1349 = _t1350
							}
							_t1348 = _t1349
						}
						_t1347 = _t1348
					}
					_t1346 = _t1347
				}
				_t1345 = _t1346
			}
			_t1344 = _t1345
		}
		_t1343 = _t1344
	}
	prediction718 := _t1343
	var _t1357 *pb.Type
	if prediction718 == 13 {
		_t1358 := p.parse_uint32_type()
		uint32_type732 := _t1358
		_t1359 := &pb.Type{}
		_t1359.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type732}
		_t1357 = _t1359
	} else {
		var _t1360 *pb.Type
		if prediction718 == 12 {
			_t1361 := p.parse_float32_type()
			float32_type731 := _t1361
			_t1362 := &pb.Type{}
			_t1362.Type = &pb.Type_Float32Type{Float32Type: float32_type731}
			_t1360 = _t1362
		} else {
			var _t1363 *pb.Type
			if prediction718 == 11 {
				_t1364 := p.parse_int32_type()
				int32_type730 := _t1364
				_t1365 := &pb.Type{}
				_t1365.Type = &pb.Type_Int32Type{Int32Type: int32_type730}
				_t1363 = _t1365
			} else {
				var _t1366 *pb.Type
				if prediction718 == 10 {
					_t1367 := p.parse_boolean_type()
					boolean_type729 := _t1367
					_t1368 := &pb.Type{}
					_t1368.Type = &pb.Type_BooleanType{BooleanType: boolean_type729}
					_t1366 = _t1368
				} else {
					var _t1369 *pb.Type
					if prediction718 == 9 {
						_t1370 := p.parse_decimal_type()
						decimal_type728 := _t1370
						_t1371 := &pb.Type{}
						_t1371.Type = &pb.Type_DecimalType{DecimalType: decimal_type728}
						_t1369 = _t1371
					} else {
						var _t1372 *pb.Type
						if prediction718 == 8 {
							_t1373 := p.parse_missing_type()
							missing_type727 := _t1373
							_t1374 := &pb.Type{}
							_t1374.Type = &pb.Type_MissingType{MissingType: missing_type727}
							_t1372 = _t1374
						} else {
							var _t1375 *pb.Type
							if prediction718 == 7 {
								_t1376 := p.parse_datetime_type()
								datetime_type726 := _t1376
								_t1377 := &pb.Type{}
								_t1377.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type726}
								_t1375 = _t1377
							} else {
								var _t1378 *pb.Type
								if prediction718 == 6 {
									_t1379 := p.parse_date_type()
									date_type725 := _t1379
									_t1380 := &pb.Type{}
									_t1380.Type = &pb.Type_DateType{DateType: date_type725}
									_t1378 = _t1380
								} else {
									var _t1381 *pb.Type
									if prediction718 == 5 {
										_t1382 := p.parse_int128_type()
										int128_type724 := _t1382
										_t1383 := &pb.Type{}
										_t1383.Type = &pb.Type_Int128Type{Int128Type: int128_type724}
										_t1381 = _t1383
									} else {
										var _t1384 *pb.Type
										if prediction718 == 4 {
											_t1385 := p.parse_uint128_type()
											uint128_type723 := _t1385
											_t1386 := &pb.Type{}
											_t1386.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type723}
											_t1384 = _t1386
										} else {
											var _t1387 *pb.Type
											if prediction718 == 3 {
												_t1388 := p.parse_float_type()
												float_type722 := _t1388
												_t1389 := &pb.Type{}
												_t1389.Type = &pb.Type_FloatType{FloatType: float_type722}
												_t1387 = _t1389
											} else {
												var _t1390 *pb.Type
												if prediction718 == 2 {
													_t1391 := p.parse_int_type()
													int_type721 := _t1391
													_t1392 := &pb.Type{}
													_t1392.Type = &pb.Type_IntType{IntType: int_type721}
													_t1390 = _t1392
												} else {
													var _t1393 *pb.Type
													if prediction718 == 1 {
														_t1394 := p.parse_string_type()
														string_type720 := _t1394
														_t1395 := &pb.Type{}
														_t1395.Type = &pb.Type_StringType{StringType: string_type720}
														_t1393 = _t1395
													} else {
														var _t1396 *pb.Type
														if prediction718 == 0 {
															_t1397 := p.parse_unspecified_type()
															unspecified_type719 := _t1397
															_t1398 := &pb.Type{}
															_t1398.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type719}
															_t1396 = _t1398
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1393 = _t1396
													}
													_t1390 = _t1393
												}
												_t1387 = _t1390
											}
											_t1384 = _t1387
										}
										_t1381 = _t1384
									}
									_t1378 = _t1381
								}
								_t1375 = _t1378
							}
							_t1372 = _t1375
						}
						_t1369 = _t1372
					}
					_t1366 = _t1369
				}
				_t1363 = _t1366
			}
			_t1360 = _t1363
		}
		_t1357 = _t1360
	}
	result734 := _t1357
	p.recordSpan(int(span_start733), "Type")
	return result734
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1399 := &pb.UnspecifiedType{}
	result736 := _t1399
	p.recordSpan(int(span_start735), "UnspecifiedType")
	return result736
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1400 := &pb.StringType{}
	result738 := _t1400
	p.recordSpan(int(span_start737), "StringType")
	return result738
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1401 := &pb.IntType{}
	result740 := _t1401
	p.recordSpan(int(span_start739), "IntType")
	return result740
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start741 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1402 := &pb.FloatType{}
	result742 := _t1402
	p.recordSpan(int(span_start741), "FloatType")
	return result742
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1403 := &pb.UInt128Type{}
	result744 := _t1403
	p.recordSpan(int(span_start743), "UInt128Type")
	return result744
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start745 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1404 := &pb.Int128Type{}
	result746 := _t1404
	p.recordSpan(int(span_start745), "Int128Type")
	return result746
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1405 := &pb.DateType{}
	result748 := _t1405
	p.recordSpan(int(span_start747), "DateType")
	return result748
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1406 := &pb.DateTimeType{}
	result750 := _t1406
	p.recordSpan(int(span_start749), "DateTimeType")
	return result750
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1407 := &pb.MissingType{}
	result752 := _t1407
	p.recordSpan(int(span_start751), "MissingType")
	return result752
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int753 := p.consumeTerminal("INT").Value.i64
	int_3754 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1408 := &pb.DecimalType{Precision: int32(int753), Scale: int32(int_3754)}
	result756 := _t1408
	p.recordSpan(int(span_start755), "DecimalType")
	return result756
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1409 := &pb.BooleanType{}
	result758 := _t1409
	p.recordSpan(int(span_start757), "BooleanType")
	return result758
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1410 := &pb.Int32Type{}
	result760 := _t1410
	p.recordSpan(int(span_start759), "Int32Type")
	return result760
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1411 := &pb.Float32Type{}
	result762 := _t1411
	p.recordSpan(int(span_start761), "Float32Type")
	return result762
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1412 := &pb.UInt32Type{}
	result764 := _t1412
	p.recordSpan(int(span_start763), "UInt32Type")
	return result764
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs765 := []*pb.Binding{}
	cond766 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond766 {
		_t1413 := p.parse_binding()
		item767 := _t1413
		xs765 = append(xs765, item767)
		cond766 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings768 := xs765
	return bindings768
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start783 := int64(p.spanStart())
	var _t1414 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1415 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1415 = 0
		} else {
			var _t1416 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1416 = 11
			} else {
				var _t1417 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1417 = 3
				} else {
					var _t1418 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1418 = 10
					} else {
						var _t1419 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1419 = 9
						} else {
							var _t1420 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1420 = 5
							} else {
								var _t1421 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1421 = 6
								} else {
									var _t1422 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1422 = 7
									} else {
										var _t1423 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1423 = 1
										} else {
											var _t1424 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1424 = 2
											} else {
												var _t1425 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1425 = 12
												} else {
													var _t1426 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1426 = 8
													} else {
														var _t1427 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1427 = 4
														} else {
															var _t1428 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1428 = 10
															} else {
																var _t1429 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1429 = 10
																} else {
																	var _t1430 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1430 = 10
																	} else {
																		var _t1431 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1431 = 10
																		} else {
																			var _t1432 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1432 = 10
																			} else {
																				var _t1433 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1433 = 10
																				} else {
																					var _t1434 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1434 = 10
																					} else {
																						var _t1435 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1435 = 10
																						} else {
																							var _t1436 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1436 = 10
																							} else {
																								_t1436 = -1
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
																		}
																		_t1430 = _t1431
																	}
																	_t1429 = _t1430
																}
																_t1428 = _t1429
															}
															_t1427 = _t1428
														}
														_t1426 = _t1427
													}
													_t1425 = _t1426
												}
												_t1424 = _t1425
											}
											_t1423 = _t1424
										}
										_t1422 = _t1423
									}
									_t1421 = _t1422
								}
								_t1420 = _t1421
							}
							_t1419 = _t1420
						}
						_t1418 = _t1419
					}
					_t1417 = _t1418
				}
				_t1416 = _t1417
			}
			_t1415 = _t1416
		}
		_t1414 = _t1415
	} else {
		_t1414 = -1
	}
	prediction769 := _t1414
	var _t1437 *pb.Formula
	if prediction769 == 12 {
		_t1438 := p.parse_cast()
		cast782 := _t1438
		_t1439 := &pb.Formula{}
		_t1439.FormulaType = &pb.Formula_Cast{Cast: cast782}
		_t1437 = _t1439
	} else {
		var _t1440 *pb.Formula
		if prediction769 == 11 {
			_t1441 := p.parse_rel_atom()
			rel_atom781 := _t1441
			_t1442 := &pb.Formula{}
			_t1442.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom781}
			_t1440 = _t1442
		} else {
			var _t1443 *pb.Formula
			if prediction769 == 10 {
				_t1444 := p.parse_primitive()
				primitive780 := _t1444
				_t1445 := &pb.Formula{}
				_t1445.FormulaType = &pb.Formula_Primitive{Primitive: primitive780}
				_t1443 = _t1445
			} else {
				var _t1446 *pb.Formula
				if prediction769 == 9 {
					_t1447 := p.parse_pragma()
					pragma779 := _t1447
					_t1448 := &pb.Formula{}
					_t1448.FormulaType = &pb.Formula_Pragma{Pragma: pragma779}
					_t1446 = _t1448
				} else {
					var _t1449 *pb.Formula
					if prediction769 == 8 {
						_t1450 := p.parse_atom()
						atom778 := _t1450
						_t1451 := &pb.Formula{}
						_t1451.FormulaType = &pb.Formula_Atom{Atom: atom778}
						_t1449 = _t1451
					} else {
						var _t1452 *pb.Formula
						if prediction769 == 7 {
							_t1453 := p.parse_ffi()
							ffi777 := _t1453
							_t1454 := &pb.Formula{}
							_t1454.FormulaType = &pb.Formula_Ffi{Ffi: ffi777}
							_t1452 = _t1454
						} else {
							var _t1455 *pb.Formula
							if prediction769 == 6 {
								_t1456 := p.parse_not()
								not776 := _t1456
								_t1457 := &pb.Formula{}
								_t1457.FormulaType = &pb.Formula_Not{Not: not776}
								_t1455 = _t1457
							} else {
								var _t1458 *pb.Formula
								if prediction769 == 5 {
									_t1459 := p.parse_disjunction()
									disjunction775 := _t1459
									_t1460 := &pb.Formula{}
									_t1460.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction775}
									_t1458 = _t1460
								} else {
									var _t1461 *pb.Formula
									if prediction769 == 4 {
										_t1462 := p.parse_conjunction()
										conjunction774 := _t1462
										_t1463 := &pb.Formula{}
										_t1463.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction774}
										_t1461 = _t1463
									} else {
										var _t1464 *pb.Formula
										if prediction769 == 3 {
											_t1465 := p.parse_reduce()
											reduce773 := _t1465
											_t1466 := &pb.Formula{}
											_t1466.FormulaType = &pb.Formula_Reduce{Reduce: reduce773}
											_t1464 = _t1466
										} else {
											var _t1467 *pb.Formula
											if prediction769 == 2 {
												_t1468 := p.parse_exists()
												exists772 := _t1468
												_t1469 := &pb.Formula{}
												_t1469.FormulaType = &pb.Formula_Exists{Exists: exists772}
												_t1467 = _t1469
											} else {
												var _t1470 *pb.Formula
												if prediction769 == 1 {
													_t1471 := p.parse_false()
													false771 := _t1471
													_t1472 := &pb.Formula{}
													_t1472.FormulaType = &pb.Formula_Disjunction{Disjunction: false771}
													_t1470 = _t1472
												} else {
													var _t1473 *pb.Formula
													if prediction769 == 0 {
														_t1474 := p.parse_true()
														true770 := _t1474
														_t1475 := &pb.Formula{}
														_t1475.FormulaType = &pb.Formula_Conjunction{Conjunction: true770}
														_t1473 = _t1475
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1470 = _t1473
												}
												_t1467 = _t1470
											}
											_t1464 = _t1467
										}
										_t1461 = _t1464
									}
									_t1458 = _t1461
								}
								_t1455 = _t1458
							}
							_t1452 = _t1455
						}
						_t1449 = _t1452
					}
					_t1446 = _t1449
				}
				_t1443 = _t1446
			}
			_t1440 = _t1443
		}
		_t1437 = _t1440
	}
	result784 := _t1437
	p.recordSpan(int(span_start783), "Formula")
	return result784
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start785 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1476 := &pb.Conjunction{Args: []*pb.Formula{}}
	result786 := _t1476
	p.recordSpan(int(span_start785), "Conjunction")
	return result786
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start787 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1477 := &pb.Disjunction{Args: []*pb.Formula{}}
	result788 := _t1477
	p.recordSpan(int(span_start787), "Disjunction")
	return result788
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1478 := p.parse_bindings()
	bindings789 := _t1478
	_t1479 := p.parse_formula()
	formula790 := _t1479
	p.consumeLiteral(")")
	_t1480 := &pb.Abstraction{Vars: listConcat(bindings789[0].([]*pb.Binding), bindings789[1].([]*pb.Binding)), Value: formula790}
	_t1481 := &pb.Exists{Body: _t1480}
	result792 := _t1481
	p.recordSpan(int(span_start791), "Exists")
	return result792
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1482 := p.parse_abstraction()
	abstraction793 := _t1482
	_t1483 := p.parse_abstraction()
	abstraction_3794 := _t1483
	_t1484 := p.parse_terms()
	terms795 := _t1484
	p.consumeLiteral(")")
	_t1485 := &pb.Reduce{Op: abstraction793, Body: abstraction_3794, Terms: terms795}
	result797 := _t1485
	p.recordSpan(int(span_start796), "Reduce")
	return result797
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs798 := []*pb.Term{}
	cond799 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond799 {
		_t1486 := p.parse_term()
		item800 := _t1486
		xs798 = append(xs798, item800)
		cond799 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms801 := xs798
	p.consumeLiteral(")")
	return terms801
}

func (p *Parser) parse_term() *pb.Term {
	span_start805 := int64(p.spanStart())
	var _t1487 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1487 = 1
	} else {
		var _t1488 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1488 = 1
		} else {
			var _t1489 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1489 = 1
			} else {
				var _t1490 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1490 = 1
				} else {
					var _t1491 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1491 = 0
					} else {
						var _t1492 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1492 = 1
						} else {
							var _t1493 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1493 = 1
							} else {
								var _t1494 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1494 = 1
								} else {
									var _t1495 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1495 = 1
									} else {
										var _t1496 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1496 = 1
										} else {
											var _t1497 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1497 = 1
											} else {
												var _t1498 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1498 = 1
												} else {
													var _t1499 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1499 = 1
													} else {
														var _t1500 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1500 = 1
														} else {
															_t1500 = -1
														}
														_t1499 = _t1500
													}
													_t1498 = _t1499
												}
												_t1497 = _t1498
											}
											_t1496 = _t1497
										}
										_t1495 = _t1496
									}
									_t1494 = _t1495
								}
								_t1493 = _t1494
							}
							_t1492 = _t1493
						}
						_t1491 = _t1492
					}
					_t1490 = _t1491
				}
				_t1489 = _t1490
			}
			_t1488 = _t1489
		}
		_t1487 = _t1488
	}
	prediction802 := _t1487
	var _t1501 *pb.Term
	if prediction802 == 1 {
		_t1502 := p.parse_value()
		value804 := _t1502
		_t1503 := &pb.Term{}
		_t1503.TermType = &pb.Term_Constant{Constant: value804}
		_t1501 = _t1503
	} else {
		var _t1504 *pb.Term
		if prediction802 == 0 {
			_t1505 := p.parse_var()
			var803 := _t1505
			_t1506 := &pb.Term{}
			_t1506.TermType = &pb.Term_Var{Var: var803}
			_t1504 = _t1506
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1501 = _t1504
	}
	result806 := _t1501
	p.recordSpan(int(span_start805), "Term")
	return result806
}

func (p *Parser) parse_var() *pb.Var {
	span_start808 := int64(p.spanStart())
	symbol807 := p.consumeTerminal("SYMBOL").Value.str
	_t1507 := &pb.Var{Name: symbol807}
	result809 := _t1507
	p.recordSpan(int(span_start808), "Var")
	return result809
}

func (p *Parser) parse_value() *pb.Value {
	span_start823 := int64(p.spanStart())
	var _t1508 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1508 = 12
	} else {
		var _t1509 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1509 = 11
		} else {
			var _t1510 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1510 = 12
			} else {
				var _t1511 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1512 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1512 = 1
					} else {
						var _t1513 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1513 = 0
						} else {
							_t1513 = -1
						}
						_t1512 = _t1513
					}
					_t1511 = _t1512
				} else {
					var _t1514 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1514 = 7
					} else {
						var _t1515 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1515 = 8
						} else {
							var _t1516 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1516 = 2
							} else {
								var _t1517 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1517 = 3
								} else {
									var _t1518 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1518 = 9
									} else {
										var _t1519 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1519 = 4
										} else {
											var _t1520 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1520 = 5
											} else {
												var _t1521 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1521 = 6
												} else {
													var _t1522 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1522 = 10
													} else {
														_t1522 = -1
													}
													_t1521 = _t1522
												}
												_t1520 = _t1521
											}
											_t1519 = _t1520
										}
										_t1518 = _t1519
									}
									_t1517 = _t1518
								}
								_t1516 = _t1517
							}
							_t1515 = _t1516
						}
						_t1514 = _t1515
					}
					_t1511 = _t1514
				}
				_t1510 = _t1511
			}
			_t1509 = _t1510
		}
		_t1508 = _t1509
	}
	prediction810 := _t1508
	var _t1523 *pb.Value
	if prediction810 == 12 {
		_t1524 := p.parse_boolean_value()
		boolean_value822 := _t1524
		_t1525 := &pb.Value{}
		_t1525.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value822}
		_t1523 = _t1525
	} else {
		var _t1526 *pb.Value
		if prediction810 == 11 {
			p.consumeLiteral("missing")
			_t1527 := &pb.MissingValue{}
			_t1528 := &pb.Value{}
			_t1528.Value = &pb.Value_MissingValue{MissingValue: _t1527}
			_t1526 = _t1528
		} else {
			var _t1529 *pb.Value
			if prediction810 == 10 {
				formatted_decimal821 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1530 := &pb.Value{}
				_t1530.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal821}
				_t1529 = _t1530
			} else {
				var _t1531 *pb.Value
				if prediction810 == 9 {
					formatted_int128820 := p.consumeTerminal("INT128").Value.int128
					_t1532 := &pb.Value{}
					_t1532.Value = &pb.Value_Int128Value{Int128Value: formatted_int128820}
					_t1531 = _t1532
				} else {
					var _t1533 *pb.Value
					if prediction810 == 8 {
						formatted_uint128819 := p.consumeTerminal("UINT128").Value.uint128
						_t1534 := &pb.Value{}
						_t1534.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128819}
						_t1533 = _t1534
					} else {
						var _t1535 *pb.Value
						if prediction810 == 7 {
							formatted_uint32818 := p.consumeTerminal("UINT32").Value.u32
							_t1536 := &pb.Value{}
							_t1536.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32818}
							_t1535 = _t1536
						} else {
							var _t1537 *pb.Value
							if prediction810 == 6 {
								formatted_float817 := p.consumeTerminal("FLOAT").Value.f64
								_t1538 := &pb.Value{}
								_t1538.Value = &pb.Value_FloatValue{FloatValue: formatted_float817}
								_t1537 = _t1538
							} else {
								var _t1539 *pb.Value
								if prediction810 == 5 {
									formatted_float32816 := p.consumeTerminal("FLOAT32").Value.f32
									_t1540 := &pb.Value{}
									_t1540.Value = &pb.Value_Float32Value{Float32Value: formatted_float32816}
									_t1539 = _t1540
								} else {
									var _t1541 *pb.Value
									if prediction810 == 4 {
										formatted_int815 := p.consumeTerminal("INT").Value.i64
										_t1542 := &pb.Value{}
										_t1542.Value = &pb.Value_IntValue{IntValue: formatted_int815}
										_t1541 = _t1542
									} else {
										var _t1543 *pb.Value
										if prediction810 == 3 {
											formatted_int32814 := p.consumeTerminal("INT32").Value.i32
											_t1544 := &pb.Value{}
											_t1544.Value = &pb.Value_Int32Value{Int32Value: formatted_int32814}
											_t1543 = _t1544
										} else {
											var _t1545 *pb.Value
											if prediction810 == 2 {
												formatted_string813 := p.consumeTerminal("STRING").Value.str
												_t1546 := &pb.Value{}
												_t1546.Value = &pb.Value_StringValue{StringValue: formatted_string813}
												_t1545 = _t1546
											} else {
												var _t1547 *pb.Value
												if prediction810 == 1 {
													_t1548 := p.parse_datetime()
													datetime812 := _t1548
													_t1549 := &pb.Value{}
													_t1549.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime812}
													_t1547 = _t1549
												} else {
													var _t1550 *pb.Value
													if prediction810 == 0 {
														_t1551 := p.parse_date()
														date811 := _t1551
														_t1552 := &pb.Value{}
														_t1552.Value = &pb.Value_DateValue{DateValue: date811}
														_t1550 = _t1552
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1547 = _t1550
												}
												_t1545 = _t1547
											}
											_t1543 = _t1545
										}
										_t1541 = _t1543
									}
									_t1539 = _t1541
								}
								_t1537 = _t1539
							}
							_t1535 = _t1537
						}
						_t1533 = _t1535
					}
					_t1531 = _t1533
				}
				_t1529 = _t1531
			}
			_t1526 = _t1529
		}
		_t1523 = _t1526
	}
	result824 := _t1523
	p.recordSpan(int(span_start823), "Value")
	return result824
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int825 := p.consumeTerminal("INT").Value.i64
	formatted_int_3826 := p.consumeTerminal("INT").Value.i64
	formatted_int_4827 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1553 := &pb.DateValue{Year: int32(formatted_int825), Month: int32(formatted_int_3826), Day: int32(formatted_int_4827)}
	result829 := _t1553
	p.recordSpan(int(span_start828), "DateValue")
	return result829
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int830 := p.consumeTerminal("INT").Value.i64
	formatted_int_3831 := p.consumeTerminal("INT").Value.i64
	formatted_int_4832 := p.consumeTerminal("INT").Value.i64
	formatted_int_5833 := p.consumeTerminal("INT").Value.i64
	formatted_int_6834 := p.consumeTerminal("INT").Value.i64
	formatted_int_7835 := p.consumeTerminal("INT").Value.i64
	var _t1554 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1554 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8836 := _t1554
	p.consumeLiteral(")")
	_t1555 := &pb.DateTimeValue{Year: int32(formatted_int830), Month: int32(formatted_int_3831), Day: int32(formatted_int_4832), Hour: int32(formatted_int_5833), Minute: int32(formatted_int_6834), Second: int32(formatted_int_7835), Microsecond: int32(deref(formatted_int_8836, 0))}
	result838 := _t1555
	p.recordSpan(int(span_start837), "DateTimeValue")
	return result838
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs839 := []*pb.Formula{}
	cond840 := p.matchLookaheadLiteral("(", 0)
	for cond840 {
		_t1556 := p.parse_formula()
		item841 := _t1556
		xs839 = append(xs839, item841)
		cond840 = p.matchLookaheadLiteral("(", 0)
	}
	formulas842 := xs839
	p.consumeLiteral(")")
	_t1557 := &pb.Conjunction{Args: formulas842}
	result844 := _t1557
	p.recordSpan(int(span_start843), "Conjunction")
	return result844
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs845 := []*pb.Formula{}
	cond846 := p.matchLookaheadLiteral("(", 0)
	for cond846 {
		_t1558 := p.parse_formula()
		item847 := _t1558
		xs845 = append(xs845, item847)
		cond846 = p.matchLookaheadLiteral("(", 0)
	}
	formulas848 := xs845
	p.consumeLiteral(")")
	_t1559 := &pb.Disjunction{Args: formulas848}
	result850 := _t1559
	p.recordSpan(int(span_start849), "Disjunction")
	return result850
}

func (p *Parser) parse_not() *pb.Not {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1560 := p.parse_formula()
	formula851 := _t1560
	p.consumeLiteral(")")
	_t1561 := &pb.Not{Arg: formula851}
	result853 := _t1561
	p.recordSpan(int(span_start852), "Not")
	return result853
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1562 := p.parse_name()
	name854 := _t1562
	_t1563 := p.parse_ffi_args()
	ffi_args855 := _t1563
	_t1564 := p.parse_terms()
	terms856 := _t1564
	p.consumeLiteral(")")
	_t1565 := &pb.FFI{Name: name854, Args: ffi_args855, Terms: terms856}
	result858 := _t1565
	p.recordSpan(int(span_start857), "FFI")
	return result858
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol859 := p.consumeTerminal("SYMBOL").Value.str
	return symbol859
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs860 := []*pb.Abstraction{}
	cond861 := p.matchLookaheadLiteral("(", 0)
	for cond861 {
		_t1566 := p.parse_abstraction()
		item862 := _t1566
		xs860 = append(xs860, item862)
		cond861 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions863 := xs860
	p.consumeLiteral(")")
	return abstractions863
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1567 := p.parse_relation_id()
	relation_id864 := _t1567
	xs865 := []*pb.Term{}
	cond866 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond866 {
		_t1568 := p.parse_term()
		item867 := _t1568
		xs865 = append(xs865, item867)
		cond866 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms868 := xs865
	p.consumeLiteral(")")
	_t1569 := &pb.Atom{Name: relation_id864, Terms: terms868}
	result870 := _t1569
	p.recordSpan(int(span_start869), "Atom")
	return result870
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start876 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1570 := p.parse_name()
	name871 := _t1570
	xs872 := []*pb.Term{}
	cond873 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond873 {
		_t1571 := p.parse_term()
		item874 := _t1571
		xs872 = append(xs872, item874)
		cond873 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms875 := xs872
	p.consumeLiteral(")")
	_t1572 := &pb.Pragma{Name: name871, Terms: terms875}
	result877 := _t1572
	p.recordSpan(int(span_start876), "Pragma")
	return result877
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start893 := int64(p.spanStart())
	var _t1573 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1574 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1574 = 9
		} else {
			var _t1575 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1575 = 4
			} else {
				var _t1576 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1576 = 3
				} else {
					var _t1577 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1577 = 0
					} else {
						var _t1578 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1578 = 2
						} else {
							var _t1579 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1579 = 1
							} else {
								var _t1580 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1580 = 8
								} else {
									var _t1581 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1581 = 6
									} else {
										var _t1582 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1582 = 5
										} else {
											var _t1583 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1583 = 7
											} else {
												_t1583 = -1
											}
											_t1582 = _t1583
										}
										_t1581 = _t1582
									}
									_t1580 = _t1581
								}
								_t1579 = _t1580
							}
							_t1578 = _t1579
						}
						_t1577 = _t1578
					}
					_t1576 = _t1577
				}
				_t1575 = _t1576
			}
			_t1574 = _t1575
		}
		_t1573 = _t1574
	} else {
		_t1573 = -1
	}
	prediction878 := _t1573
	var _t1584 *pb.Primitive
	if prediction878 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1585 := p.parse_name()
		name888 := _t1585
		xs889 := []*pb.RelTerm{}
		cond890 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond890 {
			_t1586 := p.parse_rel_term()
			item891 := _t1586
			xs889 = append(xs889, item891)
			cond890 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms892 := xs889
		p.consumeLiteral(")")
		_t1587 := &pb.Primitive{Name: name888, Terms: rel_terms892}
		_t1584 = _t1587
	} else {
		var _t1588 *pb.Primitive
		if prediction878 == 8 {
			_t1589 := p.parse_divide()
			divide887 := _t1589
			_t1588 = divide887
		} else {
			var _t1590 *pb.Primitive
			if prediction878 == 7 {
				_t1591 := p.parse_multiply()
				multiply886 := _t1591
				_t1590 = multiply886
			} else {
				var _t1592 *pb.Primitive
				if prediction878 == 6 {
					_t1593 := p.parse_minus()
					minus885 := _t1593
					_t1592 = minus885
				} else {
					var _t1594 *pb.Primitive
					if prediction878 == 5 {
						_t1595 := p.parse_add()
						add884 := _t1595
						_t1594 = add884
					} else {
						var _t1596 *pb.Primitive
						if prediction878 == 4 {
							_t1597 := p.parse_gt_eq()
							gt_eq883 := _t1597
							_t1596 = gt_eq883
						} else {
							var _t1598 *pb.Primitive
							if prediction878 == 3 {
								_t1599 := p.parse_gt()
								gt882 := _t1599
								_t1598 = gt882
							} else {
								var _t1600 *pb.Primitive
								if prediction878 == 2 {
									_t1601 := p.parse_lt_eq()
									lt_eq881 := _t1601
									_t1600 = lt_eq881
								} else {
									var _t1602 *pb.Primitive
									if prediction878 == 1 {
										_t1603 := p.parse_lt()
										lt880 := _t1603
										_t1602 = lt880
									} else {
										var _t1604 *pb.Primitive
										if prediction878 == 0 {
											_t1605 := p.parse_eq()
											eq879 := _t1605
											_t1604 = eq879
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1602 = _t1604
									}
									_t1600 = _t1602
								}
								_t1598 = _t1600
							}
							_t1596 = _t1598
						}
						_t1594 = _t1596
					}
					_t1592 = _t1594
				}
				_t1590 = _t1592
			}
			_t1588 = _t1590
		}
		_t1584 = _t1588
	}
	result894 := _t1584
	p.recordSpan(int(span_start893), "Primitive")
	return result894
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start897 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1606 := p.parse_term()
	term895 := _t1606
	_t1607 := p.parse_term()
	term_3896 := _t1607
	p.consumeLiteral(")")
	_t1608 := &pb.RelTerm{}
	_t1608.RelTermType = &pb.RelTerm_Term{Term: term895}
	_t1609 := &pb.RelTerm{}
	_t1609.RelTermType = &pb.RelTerm_Term{Term: term_3896}
	_t1610 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1608, _t1609}}
	result898 := _t1610
	p.recordSpan(int(span_start897), "Primitive")
	return result898
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1611 := p.parse_term()
	term899 := _t1611
	_t1612 := p.parse_term()
	term_3900 := _t1612
	p.consumeLiteral(")")
	_t1613 := &pb.RelTerm{}
	_t1613.RelTermType = &pb.RelTerm_Term{Term: term899}
	_t1614 := &pb.RelTerm{}
	_t1614.RelTermType = &pb.RelTerm_Term{Term: term_3900}
	_t1615 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1613, _t1614}}
	result902 := _t1615
	p.recordSpan(int(span_start901), "Primitive")
	return result902
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start905 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1616 := p.parse_term()
	term903 := _t1616
	_t1617 := p.parse_term()
	term_3904 := _t1617
	p.consumeLiteral(")")
	_t1618 := &pb.RelTerm{}
	_t1618.RelTermType = &pb.RelTerm_Term{Term: term903}
	_t1619 := &pb.RelTerm{}
	_t1619.RelTermType = &pb.RelTerm_Term{Term: term_3904}
	_t1620 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1618, _t1619}}
	result906 := _t1620
	p.recordSpan(int(span_start905), "Primitive")
	return result906
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1621 := p.parse_term()
	term907 := _t1621
	_t1622 := p.parse_term()
	term_3908 := _t1622
	p.consumeLiteral(")")
	_t1623 := &pb.RelTerm{}
	_t1623.RelTermType = &pb.RelTerm_Term{Term: term907}
	_t1624 := &pb.RelTerm{}
	_t1624.RelTermType = &pb.RelTerm_Term{Term: term_3908}
	_t1625 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1623, _t1624}}
	result910 := _t1625
	p.recordSpan(int(span_start909), "Primitive")
	return result910
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1626 := p.parse_term()
	term911 := _t1626
	_t1627 := p.parse_term()
	term_3912 := _t1627
	p.consumeLiteral(")")
	_t1628 := &pb.RelTerm{}
	_t1628.RelTermType = &pb.RelTerm_Term{Term: term911}
	_t1629 := &pb.RelTerm{}
	_t1629.RelTermType = &pb.RelTerm_Term{Term: term_3912}
	_t1630 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1628, _t1629}}
	result914 := _t1630
	p.recordSpan(int(span_start913), "Primitive")
	return result914
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1631 := p.parse_term()
	term915 := _t1631
	_t1632 := p.parse_term()
	term_3916 := _t1632
	_t1633 := p.parse_term()
	term_4917 := _t1633
	p.consumeLiteral(")")
	_t1634 := &pb.RelTerm{}
	_t1634.RelTermType = &pb.RelTerm_Term{Term: term915}
	_t1635 := &pb.RelTerm{}
	_t1635.RelTermType = &pb.RelTerm_Term{Term: term_3916}
	_t1636 := &pb.RelTerm{}
	_t1636.RelTermType = &pb.RelTerm_Term{Term: term_4917}
	_t1637 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1634, _t1635, _t1636}}
	result919 := _t1637
	p.recordSpan(int(span_start918), "Primitive")
	return result919
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1638 := p.parse_term()
	term920 := _t1638
	_t1639 := p.parse_term()
	term_3921 := _t1639
	_t1640 := p.parse_term()
	term_4922 := _t1640
	p.consumeLiteral(")")
	_t1641 := &pb.RelTerm{}
	_t1641.RelTermType = &pb.RelTerm_Term{Term: term920}
	_t1642 := &pb.RelTerm{}
	_t1642.RelTermType = &pb.RelTerm_Term{Term: term_3921}
	_t1643 := &pb.RelTerm{}
	_t1643.RelTermType = &pb.RelTerm_Term{Term: term_4922}
	_t1644 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1641, _t1642, _t1643}}
	result924 := _t1644
	p.recordSpan(int(span_start923), "Primitive")
	return result924
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start928 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1645 := p.parse_term()
	term925 := _t1645
	_t1646 := p.parse_term()
	term_3926 := _t1646
	_t1647 := p.parse_term()
	term_4927 := _t1647
	p.consumeLiteral(")")
	_t1648 := &pb.RelTerm{}
	_t1648.RelTermType = &pb.RelTerm_Term{Term: term925}
	_t1649 := &pb.RelTerm{}
	_t1649.RelTermType = &pb.RelTerm_Term{Term: term_3926}
	_t1650 := &pb.RelTerm{}
	_t1650.RelTermType = &pb.RelTerm_Term{Term: term_4927}
	_t1651 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1648, _t1649, _t1650}}
	result929 := _t1651
	p.recordSpan(int(span_start928), "Primitive")
	return result929
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start933 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1652 := p.parse_term()
	term930 := _t1652
	_t1653 := p.parse_term()
	term_3931 := _t1653
	_t1654 := p.parse_term()
	term_4932 := _t1654
	p.consumeLiteral(")")
	_t1655 := &pb.RelTerm{}
	_t1655.RelTermType = &pb.RelTerm_Term{Term: term930}
	_t1656 := &pb.RelTerm{}
	_t1656.RelTermType = &pb.RelTerm_Term{Term: term_3931}
	_t1657 := &pb.RelTerm{}
	_t1657.RelTermType = &pb.RelTerm_Term{Term: term_4932}
	_t1658 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1655, _t1656, _t1657}}
	result934 := _t1658
	p.recordSpan(int(span_start933), "Primitive")
	return result934
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start938 := int64(p.spanStart())
	var _t1659 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1659 = 1
	} else {
		var _t1660 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1660 = 1
		} else {
			var _t1661 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1661 = 1
			} else {
				var _t1662 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1662 = 1
				} else {
					var _t1663 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1663 = 0
					} else {
						var _t1664 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1664 = 1
						} else {
							var _t1665 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1665 = 1
							} else {
								var _t1666 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1666 = 1
								} else {
									var _t1667 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1667 = 1
									} else {
										var _t1668 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1668 = 1
										} else {
											var _t1669 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1669 = 1
											} else {
												var _t1670 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1670 = 1
												} else {
													var _t1671 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1671 = 1
													} else {
														var _t1672 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1672 = 1
														} else {
															var _t1673 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1673 = 1
															} else {
																_t1673 = -1
															}
															_t1672 = _t1673
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
								}
								_t1665 = _t1666
							}
							_t1664 = _t1665
						}
						_t1663 = _t1664
					}
					_t1662 = _t1663
				}
				_t1661 = _t1662
			}
			_t1660 = _t1661
		}
		_t1659 = _t1660
	}
	prediction935 := _t1659
	var _t1674 *pb.RelTerm
	if prediction935 == 1 {
		_t1675 := p.parse_term()
		term937 := _t1675
		_t1676 := &pb.RelTerm{}
		_t1676.RelTermType = &pb.RelTerm_Term{Term: term937}
		_t1674 = _t1676
	} else {
		var _t1677 *pb.RelTerm
		if prediction935 == 0 {
			_t1678 := p.parse_specialized_value()
			specialized_value936 := _t1678
			_t1679 := &pb.RelTerm{}
			_t1679.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value936}
			_t1677 = _t1679
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1674 = _t1677
	}
	result939 := _t1674
	p.recordSpan(int(span_start938), "RelTerm")
	return result939
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start941 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1680 := p.parse_raw_value()
	raw_value940 := _t1680
	result942 := raw_value940
	p.recordSpan(int(span_start941), "Value")
	return result942
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1681 := p.parse_name()
	name943 := _t1681
	xs944 := []*pb.RelTerm{}
	cond945 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond945 {
		_t1682 := p.parse_rel_term()
		item946 := _t1682
		xs944 = append(xs944, item946)
		cond945 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms947 := xs944
	p.consumeLiteral(")")
	_t1683 := &pb.RelAtom{Name: name943, Terms: rel_terms947}
	result949 := _t1683
	p.recordSpan(int(span_start948), "RelAtom")
	return result949
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1684 := p.parse_term()
	term950 := _t1684
	_t1685 := p.parse_term()
	term_3951 := _t1685
	p.consumeLiteral(")")
	_t1686 := &pb.Cast{Input: term950, Result: term_3951}
	result953 := _t1686
	p.recordSpan(int(span_start952), "Cast")
	return result953
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs954 := []*pb.Attribute{}
	cond955 := p.matchLookaheadLiteral("(", 0)
	for cond955 {
		_t1687 := p.parse_attribute()
		item956 := _t1687
		xs954 = append(xs954, item956)
		cond955 = p.matchLookaheadLiteral("(", 0)
	}
	attributes957 := xs954
	p.consumeLiteral(")")
	return attributes957
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start963 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1688 := p.parse_name()
	name958 := _t1688
	xs959 := []*pb.Value{}
	cond960 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond960 {
		_t1689 := p.parse_raw_value()
		item961 := _t1689
		xs959 = append(xs959, item961)
		cond960 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values962 := xs959
	p.consumeLiteral(")")
	_t1690 := &pb.Attribute{Name: name958, Args: raw_values962}
	result964 := _t1690
	p.recordSpan(int(span_start963), "Attribute")
	return result964
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs965 := []*pb.RelationId{}
	cond966 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond966 {
		_t1691 := p.parse_relation_id()
		item967 := _t1691
		xs965 = append(xs965, item967)
		cond966 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids968 := xs965
	_t1692 := p.parse_script()
	script969 := _t1692
	p.consumeLiteral(")")
	_t1693 := &pb.Algorithm{Global: relation_ids968, Body: script969}
	result971 := _t1693
	p.recordSpan(int(span_start970), "Algorithm")
	return result971
}

func (p *Parser) parse_script() *pb.Script {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs972 := []*pb.Construct{}
	cond973 := p.matchLookaheadLiteral("(", 0)
	for cond973 {
		_t1694 := p.parse_construct()
		item974 := _t1694
		xs972 = append(xs972, item974)
		cond973 = p.matchLookaheadLiteral("(", 0)
	}
	constructs975 := xs972
	p.consumeLiteral(")")
	_t1695 := &pb.Script{Constructs: constructs975}
	result977 := _t1695
	p.recordSpan(int(span_start976), "Script")
	return result977
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start981 := int64(p.spanStart())
	var _t1696 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1697 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1697 = 1
		} else {
			var _t1698 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1698 = 1
			} else {
				var _t1699 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1699 = 1
				} else {
					var _t1700 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1700 = 0
					} else {
						var _t1701 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1701 = 1
						} else {
							var _t1702 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1702 = 1
							} else {
								_t1702 = -1
							}
							_t1701 = _t1702
						}
						_t1700 = _t1701
					}
					_t1699 = _t1700
				}
				_t1698 = _t1699
			}
			_t1697 = _t1698
		}
		_t1696 = _t1697
	} else {
		_t1696 = -1
	}
	prediction978 := _t1696
	var _t1703 *pb.Construct
	if prediction978 == 1 {
		_t1704 := p.parse_instruction()
		instruction980 := _t1704
		_t1705 := &pb.Construct{}
		_t1705.ConstructType = &pb.Construct_Instruction{Instruction: instruction980}
		_t1703 = _t1705
	} else {
		var _t1706 *pb.Construct
		if prediction978 == 0 {
			_t1707 := p.parse_loop()
			loop979 := _t1707
			_t1708 := &pb.Construct{}
			_t1708.ConstructType = &pb.Construct_Loop{Loop: loop979}
			_t1706 = _t1708
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1703 = _t1706
	}
	result982 := _t1703
	p.recordSpan(int(span_start981), "Construct")
	return result982
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start985 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1709 := p.parse_init()
	init983 := _t1709
	_t1710 := p.parse_script()
	script984 := _t1710
	p.consumeLiteral(")")
	_t1711 := &pb.Loop{Init: init983, Body: script984}
	result986 := _t1711
	p.recordSpan(int(span_start985), "Loop")
	return result986
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs987 := []*pb.Instruction{}
	cond988 := p.matchLookaheadLiteral("(", 0)
	for cond988 {
		_t1712 := p.parse_instruction()
		item989 := _t1712
		xs987 = append(xs987, item989)
		cond988 = p.matchLookaheadLiteral("(", 0)
	}
	instructions990 := xs987
	p.consumeLiteral(")")
	return instructions990
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start997 := int64(p.spanStart())
	var _t1713 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1714 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1714 = 1
		} else {
			var _t1715 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1715 = 4
			} else {
				var _t1716 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1716 = 3
				} else {
					var _t1717 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1717 = 2
					} else {
						var _t1718 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1718 = 0
						} else {
							_t1718 = -1
						}
						_t1717 = _t1718
					}
					_t1716 = _t1717
				}
				_t1715 = _t1716
			}
			_t1714 = _t1715
		}
		_t1713 = _t1714
	} else {
		_t1713 = -1
	}
	prediction991 := _t1713
	var _t1719 *pb.Instruction
	if prediction991 == 4 {
		_t1720 := p.parse_monus_def()
		monus_def996 := _t1720
		_t1721 := &pb.Instruction{}
		_t1721.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def996}
		_t1719 = _t1721
	} else {
		var _t1722 *pb.Instruction
		if prediction991 == 3 {
			_t1723 := p.parse_monoid_def()
			monoid_def995 := _t1723
			_t1724 := &pb.Instruction{}
			_t1724.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def995}
			_t1722 = _t1724
		} else {
			var _t1725 *pb.Instruction
			if prediction991 == 2 {
				_t1726 := p.parse_break()
				break994 := _t1726
				_t1727 := &pb.Instruction{}
				_t1727.InstrType = &pb.Instruction_Break{Break: break994}
				_t1725 = _t1727
			} else {
				var _t1728 *pb.Instruction
				if prediction991 == 1 {
					_t1729 := p.parse_upsert()
					upsert993 := _t1729
					_t1730 := &pb.Instruction{}
					_t1730.InstrType = &pb.Instruction_Upsert{Upsert: upsert993}
					_t1728 = _t1730
				} else {
					var _t1731 *pb.Instruction
					if prediction991 == 0 {
						_t1732 := p.parse_assign()
						assign992 := _t1732
						_t1733 := &pb.Instruction{}
						_t1733.InstrType = &pb.Instruction_Assign{Assign: assign992}
						_t1731 = _t1733
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1728 = _t1731
				}
				_t1725 = _t1728
			}
			_t1722 = _t1725
		}
		_t1719 = _t1722
	}
	result998 := _t1719
	p.recordSpan(int(span_start997), "Instruction")
	return result998
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1734 := p.parse_relation_id()
	relation_id999 := _t1734
	_t1735 := p.parse_abstraction()
	abstraction1000 := _t1735
	var _t1736 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1737 := p.parse_attrs()
		_t1736 = _t1737
	}
	attrs1001 := _t1736
	p.consumeLiteral(")")
	_t1738 := attrs1001
	if attrs1001 == nil {
		_t1738 = []*pb.Attribute{}
	}
	_t1739 := &pb.Assign{Name: relation_id999, Body: abstraction1000, Attrs: _t1738}
	result1003 := _t1739
	p.recordSpan(int(span_start1002), "Assign")
	return result1003
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1007 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1740 := p.parse_relation_id()
	relation_id1004 := _t1740
	_t1741 := p.parse_abstraction_with_arity()
	abstraction_with_arity1005 := _t1741
	var _t1742 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1743 := p.parse_attrs()
		_t1742 = _t1743
	}
	attrs1006 := _t1742
	p.consumeLiteral(")")
	_t1744 := attrs1006
	if attrs1006 == nil {
		_t1744 = []*pb.Attribute{}
	}
	_t1745 := &pb.Upsert{Name: relation_id1004, Body: abstraction_with_arity1005[0].(*pb.Abstraction), Attrs: _t1744, ValueArity: abstraction_with_arity1005[1].(int64)}
	result1008 := _t1745
	p.recordSpan(int(span_start1007), "Upsert")
	return result1008
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1746 := p.parse_bindings()
	bindings1009 := _t1746
	_t1747 := p.parse_formula()
	formula1010 := _t1747
	p.consumeLiteral(")")
	_t1748 := &pb.Abstraction{Vars: listConcat(bindings1009[0].([]*pb.Binding), bindings1009[1].([]*pb.Binding)), Value: formula1010}
	return []interface{}{_t1748, int64(len(bindings1009[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1749 := p.parse_relation_id()
	relation_id1011 := _t1749
	_t1750 := p.parse_abstraction()
	abstraction1012 := _t1750
	var _t1751 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1752 := p.parse_attrs()
		_t1751 = _t1752
	}
	attrs1013 := _t1751
	p.consumeLiteral(")")
	_t1753 := attrs1013
	if attrs1013 == nil {
		_t1753 = []*pb.Attribute{}
	}
	_t1754 := &pb.Break{Name: relation_id1011, Body: abstraction1012, Attrs: _t1753}
	result1015 := _t1754
	p.recordSpan(int(span_start1014), "Break")
	return result1015
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1020 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1755 := p.parse_monoid()
	monoid1016 := _t1755
	_t1756 := p.parse_relation_id()
	relation_id1017 := _t1756
	_t1757 := p.parse_abstraction_with_arity()
	abstraction_with_arity1018 := _t1757
	var _t1758 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1759 := p.parse_attrs()
		_t1758 = _t1759
	}
	attrs1019 := _t1758
	p.consumeLiteral(")")
	_t1760 := attrs1019
	if attrs1019 == nil {
		_t1760 = []*pb.Attribute{}
	}
	_t1761 := &pb.MonoidDef{Monoid: monoid1016, Name: relation_id1017, Body: abstraction_with_arity1018[0].(*pb.Abstraction), Attrs: _t1760, ValueArity: abstraction_with_arity1018[1].(int64)}
	result1021 := _t1761
	p.recordSpan(int(span_start1020), "MonoidDef")
	return result1021
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1027 := int64(p.spanStart())
	var _t1762 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1763 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1763 = 3
		} else {
			var _t1764 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1764 = 0
			} else {
				var _t1765 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1765 = 1
				} else {
					var _t1766 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1766 = 2
					} else {
						_t1766 = -1
					}
					_t1765 = _t1766
				}
				_t1764 = _t1765
			}
			_t1763 = _t1764
		}
		_t1762 = _t1763
	} else {
		_t1762 = -1
	}
	prediction1022 := _t1762
	var _t1767 *pb.Monoid
	if prediction1022 == 3 {
		_t1768 := p.parse_sum_monoid()
		sum_monoid1026 := _t1768
		_t1769 := &pb.Monoid{}
		_t1769.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1026}
		_t1767 = _t1769
	} else {
		var _t1770 *pb.Monoid
		if prediction1022 == 2 {
			_t1771 := p.parse_max_monoid()
			max_monoid1025 := _t1771
			_t1772 := &pb.Monoid{}
			_t1772.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1025}
			_t1770 = _t1772
		} else {
			var _t1773 *pb.Monoid
			if prediction1022 == 1 {
				_t1774 := p.parse_min_monoid()
				min_monoid1024 := _t1774
				_t1775 := &pb.Monoid{}
				_t1775.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1024}
				_t1773 = _t1775
			} else {
				var _t1776 *pb.Monoid
				if prediction1022 == 0 {
					_t1777 := p.parse_or_monoid()
					or_monoid1023 := _t1777
					_t1778 := &pb.Monoid{}
					_t1778.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1023}
					_t1776 = _t1778
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1773 = _t1776
			}
			_t1770 = _t1773
		}
		_t1767 = _t1770
	}
	result1028 := _t1767
	p.recordSpan(int(span_start1027), "Monoid")
	return result1028
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1029 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1779 := &pb.OrMonoid{}
	result1030 := _t1779
	p.recordSpan(int(span_start1029), "OrMonoid")
	return result1030
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1780 := p.parse_type()
	type1031 := _t1780
	p.consumeLiteral(")")
	_t1781 := &pb.MinMonoid{Type: type1031}
	result1033 := _t1781
	p.recordSpan(int(span_start1032), "MinMonoid")
	return result1033
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1035 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1782 := p.parse_type()
	type1034 := _t1782
	p.consumeLiteral(")")
	_t1783 := &pb.MaxMonoid{Type: type1034}
	result1036 := _t1783
	p.recordSpan(int(span_start1035), "MaxMonoid")
	return result1036
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1784 := p.parse_type()
	type1037 := _t1784
	p.consumeLiteral(")")
	_t1785 := &pb.SumMonoid{Type: type1037}
	result1039 := _t1785
	p.recordSpan(int(span_start1038), "SumMonoid")
	return result1039
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1786 := p.parse_monoid()
	monoid1040 := _t1786
	_t1787 := p.parse_relation_id()
	relation_id1041 := _t1787
	_t1788 := p.parse_abstraction_with_arity()
	abstraction_with_arity1042 := _t1788
	var _t1789 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1790 := p.parse_attrs()
		_t1789 = _t1790
	}
	attrs1043 := _t1789
	p.consumeLiteral(")")
	_t1791 := attrs1043
	if attrs1043 == nil {
		_t1791 = []*pb.Attribute{}
	}
	_t1792 := &pb.MonusDef{Monoid: monoid1040, Name: relation_id1041, Body: abstraction_with_arity1042[0].(*pb.Abstraction), Attrs: _t1791, ValueArity: abstraction_with_arity1042[1].(int64)}
	result1045 := _t1792
	p.recordSpan(int(span_start1044), "MonusDef")
	return result1045
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1050 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1793 := p.parse_relation_id()
	relation_id1046 := _t1793
	_t1794 := p.parse_abstraction()
	abstraction1047 := _t1794
	_t1795 := p.parse_functional_dependency_keys()
	functional_dependency_keys1048 := _t1795
	_t1796 := p.parse_functional_dependency_values()
	functional_dependency_values1049 := _t1796
	p.consumeLiteral(")")
	_t1797 := &pb.FunctionalDependency{Guard: abstraction1047, Keys: functional_dependency_keys1048, Values: functional_dependency_values1049}
	_t1798 := &pb.Constraint{Name: relation_id1046}
	_t1798.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1797}
	result1051 := _t1798
	p.recordSpan(int(span_start1050), "Constraint")
	return result1051
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1052 := []*pb.Var{}
	cond1053 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1053 {
		_t1799 := p.parse_var()
		item1054 := _t1799
		xs1052 = append(xs1052, item1054)
		cond1053 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1055 := xs1052
	p.consumeLiteral(")")
	return vars1055
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1056 := []*pb.Var{}
	cond1057 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1057 {
		_t1800 := p.parse_var()
		item1058 := _t1800
		xs1056 = append(xs1056, item1058)
		cond1057 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1059 := xs1056
	p.consumeLiteral(")")
	return vars1059
}

func (p *Parser) parse_data() *pb.Data {
	span_start1064 := int64(p.spanStart())
	var _t1801 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1802 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1802 = 0
		} else {
			var _t1803 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1803 = 2
			} else {
				var _t1804 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1804 = 1
				} else {
					_t1804 = -1
				}
				_t1803 = _t1804
			}
			_t1802 = _t1803
		}
		_t1801 = _t1802
	} else {
		_t1801 = -1
	}
	prediction1060 := _t1801
	var _t1805 *pb.Data
	if prediction1060 == 2 {
		_t1806 := p.parse_csv_data()
		csv_data1063 := _t1806
		_t1807 := &pb.Data{}
		_t1807.DataType = &pb.Data_CsvData{CsvData: csv_data1063}
		_t1805 = _t1807
	} else {
		var _t1808 *pb.Data
		if prediction1060 == 1 {
			_t1809 := p.parse_betree_relation()
			betree_relation1062 := _t1809
			_t1810 := &pb.Data{}
			_t1810.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1062}
			_t1808 = _t1810
		} else {
			var _t1811 *pb.Data
			if prediction1060 == 0 {
				_t1812 := p.parse_edb()
				edb1061 := _t1812
				_t1813 := &pb.Data{}
				_t1813.DataType = &pb.Data_Edb{Edb: edb1061}
				_t1811 = _t1813
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1808 = _t1811
		}
		_t1805 = _t1808
	}
	result1065 := _t1805
	p.recordSpan(int(span_start1064), "Data")
	return result1065
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1069 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1814 := p.parse_relation_id()
	relation_id1066 := _t1814
	_t1815 := p.parse_edb_path()
	edb_path1067 := _t1815
	_t1816 := p.parse_edb_types()
	edb_types1068 := _t1816
	p.consumeLiteral(")")
	_t1817 := &pb.EDB{TargetId: relation_id1066, Path: edb_path1067, Types: edb_types1068}
	result1070 := _t1817
	p.recordSpan(int(span_start1069), "EDB")
	return result1070
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1071 := []string{}
	cond1072 := p.matchLookaheadTerminal("STRING", 0)
	for cond1072 {
		item1073 := p.consumeTerminal("STRING").Value.str
		xs1071 = append(xs1071, item1073)
		cond1072 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1074 := xs1071
	p.consumeLiteral("]")
	return strings1074
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1075 := []*pb.Type{}
	cond1076 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1076 {
		_t1818 := p.parse_type()
		item1077 := _t1818
		xs1075 = append(xs1075, item1077)
		cond1076 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1078 := xs1075
	p.consumeLiteral("]")
	return types1078
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1081 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1819 := p.parse_relation_id()
	relation_id1079 := _t1819
	_t1820 := p.parse_betree_info()
	betree_info1080 := _t1820
	p.consumeLiteral(")")
	_t1821 := &pb.BeTreeRelation{Name: relation_id1079, RelationInfo: betree_info1080}
	result1082 := _t1821
	p.recordSpan(int(span_start1081), "BeTreeRelation")
	return result1082
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1822 := p.parse_betree_info_key_types()
	betree_info_key_types1083 := _t1822
	_t1823 := p.parse_betree_info_value_types()
	betree_info_value_types1084 := _t1823
	_t1824 := p.parse_config_dict()
	config_dict1085 := _t1824
	p.consumeLiteral(")")
	_t1825 := p.construct_betree_info(betree_info_key_types1083, betree_info_value_types1084, config_dict1085)
	result1087 := _t1825
	p.recordSpan(int(span_start1086), "BeTreeInfo")
	return result1087
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1088 := []*pb.Type{}
	cond1089 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1089 {
		_t1826 := p.parse_type()
		item1090 := _t1826
		xs1088 = append(xs1088, item1090)
		cond1089 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1091 := xs1088
	p.consumeLiteral(")")
	return types1091
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1092 := []*pb.Type{}
	cond1093 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1093 {
		_t1827 := p.parse_type()
		item1094 := _t1827
		xs1092 = append(xs1092, item1094)
		cond1093 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1095 := xs1092
	p.consumeLiteral(")")
	return types1095
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1828 := p.parse_csvlocator()
	csvlocator1096 := _t1828
	_t1829 := p.parse_csv_config()
	csv_config1097 := _t1829
	_t1830 := p.parse_gnf_columns()
	gnf_columns1098 := _t1830
	_t1831 := p.parse_csv_asof()
	csv_asof1099 := _t1831
	p.consumeLiteral(")")
	_t1832 := &pb.CSVData{Locator: csvlocator1096, Config: csv_config1097, Columns: gnf_columns1098, Asof: csv_asof1099}
	result1101 := _t1832
	p.recordSpan(int(span_start1100), "CSVData")
	return result1101
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1833 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1834 := p.parse_csv_locator_paths()
		_t1833 = _t1834
	}
	csv_locator_paths1102 := _t1833
	var _t1835 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1836 := p.parse_csv_locator_inline_data()
		_t1835 = ptr(_t1836)
	}
	csv_locator_inline_data1103 := _t1835
	p.consumeLiteral(")")
	_t1837 := csv_locator_paths1102
	if csv_locator_paths1102 == nil {
		_t1837 = []string{}
	}
	_t1838 := &pb.CSVLocator{Paths: _t1837, InlineData: []byte(deref(csv_locator_inline_data1103, ""))}
	result1105 := _t1838
	p.recordSpan(int(span_start1104), "CSVLocator")
	return result1105
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1106 := []string{}
	cond1107 := p.matchLookaheadTerminal("STRING", 0)
	for cond1107 {
		item1108 := p.consumeTerminal("STRING").Value.str
		xs1106 = append(xs1106, item1108)
		cond1107 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1109 := xs1106
	p.consumeLiteral(")")
	return strings1109
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1110 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1110
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1839 := p.parse_config_dict()
	config_dict1111 := _t1839
	p.consumeLiteral(")")
	_t1840 := p.construct_csv_config(config_dict1111)
	result1113 := _t1840
	p.recordSpan(int(span_start1112), "CSVConfig")
	return result1113
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1114 := []*pb.GNFColumn{}
	cond1115 := p.matchLookaheadLiteral("(", 0)
	for cond1115 {
		_t1841 := p.parse_gnf_column()
		item1116 := _t1841
		xs1114 = append(xs1114, item1116)
		cond1115 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1117 := xs1114
	p.consumeLiteral(")")
	return gnf_columns1117
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1842 := p.parse_gnf_column_path()
	gnf_column_path1118 := _t1842
	var _t1843 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1844 := p.parse_relation_id()
		_t1843 = _t1844
	}
	relation_id1119 := _t1843
	p.consumeLiteral("[")
	xs1120 := []*pb.Type{}
	cond1121 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1121 {
		_t1845 := p.parse_type()
		item1122 := _t1845
		xs1120 = append(xs1120, item1122)
		cond1121 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1123 := xs1120
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1846 := &pb.GNFColumn{ColumnPath: gnf_column_path1118, TargetId: relation_id1119, Types: types1123}
	result1125 := _t1846
	p.recordSpan(int(span_start1124), "GNFColumn")
	return result1125
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1847 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1847 = 1
	} else {
		var _t1848 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1848 = 0
		} else {
			_t1848 = -1
		}
		_t1847 = _t1848
	}
	prediction1126 := _t1847
	var _t1849 []string
	if prediction1126 == 1 {
		p.consumeLiteral("[")
		xs1128 := []string{}
		cond1129 := p.matchLookaheadTerminal("STRING", 0)
		for cond1129 {
			item1130 := p.consumeTerminal("STRING").Value.str
			xs1128 = append(xs1128, item1130)
			cond1129 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1131 := xs1128
		p.consumeLiteral("]")
		_t1849 = strings1131
	} else {
		var _t1850 []string
		if prediction1126 == 0 {
			string1127 := p.consumeTerminal("STRING").Value.str
			_ = string1127
			_t1850 = []string{string1127}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1849 = _t1850
	}
	return _t1849
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1132 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1132
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1851 := p.parse_fragment_id()
	fragment_id1133 := _t1851
	p.consumeLiteral(")")
	_t1852 := &pb.Undefine{FragmentId: fragment_id1133}
	result1135 := _t1852
	p.recordSpan(int(span_start1134), "Undefine")
	return result1135
}

func (p *Parser) parse_context() *pb.Context {
	span_start1140 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1136 := []*pb.RelationId{}
	cond1137 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1137 {
		_t1853 := p.parse_relation_id()
		item1138 := _t1853
		xs1136 = append(xs1136, item1138)
		cond1137 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1139 := xs1136
	p.consumeLiteral(")")
	_t1854 := &pb.Context{Relations: relation_ids1139}
	result1141 := _t1854
	p.recordSpan(int(span_start1140), "Context")
	return result1141
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1146 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1142 := []*pb.SnapshotMapping{}
	cond1143 := p.matchLookaheadLiteral("[", 0)
	for cond1143 {
		_t1855 := p.parse_snapshot_mapping()
		item1144 := _t1855
		xs1142 = append(xs1142, item1144)
		cond1143 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1145 := xs1142
	p.consumeLiteral(")")
	_t1856 := &pb.Snapshot{Mappings: snapshot_mappings1145}
	result1147 := _t1856
	p.recordSpan(int(span_start1146), "Snapshot")
	return result1147
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1150 := int64(p.spanStart())
	_t1857 := p.parse_edb_path()
	edb_path1148 := _t1857
	_t1858 := p.parse_relation_id()
	relation_id1149 := _t1858
	_t1859 := &pb.SnapshotMapping{DestinationPath: edb_path1148, SourceRelation: relation_id1149}
	result1151 := _t1859
	p.recordSpan(int(span_start1150), "SnapshotMapping")
	return result1151
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1152 := []*pb.Read{}
	cond1153 := p.matchLookaheadLiteral("(", 0)
	for cond1153 {
		_t1860 := p.parse_read()
		item1154 := _t1860
		xs1152 = append(xs1152, item1154)
		cond1153 = p.matchLookaheadLiteral("(", 0)
	}
	reads1155 := xs1152
	p.consumeLiteral(")")
	return reads1155
}

func (p *Parser) parse_read() *pb.Read {
	span_start1162 := int64(p.spanStart())
	var _t1861 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1862 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1862 = 2
		} else {
			var _t1863 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1863 = 1
			} else {
				var _t1864 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1864 = 4
				} else {
					var _t1865 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1865 = 0
					} else {
						var _t1866 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1866 = 3
						} else {
							_t1866 = -1
						}
						_t1865 = _t1866
					}
					_t1864 = _t1865
				}
				_t1863 = _t1864
			}
			_t1862 = _t1863
		}
		_t1861 = _t1862
	} else {
		_t1861 = -1
	}
	prediction1156 := _t1861
	var _t1867 *pb.Read
	if prediction1156 == 4 {
		_t1868 := p.parse_export()
		export1161 := _t1868
		_t1869 := &pb.Read{}
		_t1869.ReadType = &pb.Read_Export{Export: export1161}
		_t1867 = _t1869
	} else {
		var _t1870 *pb.Read
		if prediction1156 == 3 {
			_t1871 := p.parse_abort()
			abort1160 := _t1871
			_t1872 := &pb.Read{}
			_t1872.ReadType = &pb.Read_Abort{Abort: abort1160}
			_t1870 = _t1872
		} else {
			var _t1873 *pb.Read
			if prediction1156 == 2 {
				_t1874 := p.parse_what_if()
				what_if1159 := _t1874
				_t1875 := &pb.Read{}
				_t1875.ReadType = &pb.Read_WhatIf{WhatIf: what_if1159}
				_t1873 = _t1875
			} else {
				var _t1876 *pb.Read
				if prediction1156 == 1 {
					_t1877 := p.parse_output()
					output1158 := _t1877
					_t1878 := &pb.Read{}
					_t1878.ReadType = &pb.Read_Output{Output: output1158}
					_t1876 = _t1878
				} else {
					var _t1879 *pb.Read
					if prediction1156 == 0 {
						_t1880 := p.parse_demand()
						demand1157 := _t1880
						_t1881 := &pb.Read{}
						_t1881.ReadType = &pb.Read_Demand{Demand: demand1157}
						_t1879 = _t1881
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1876 = _t1879
				}
				_t1873 = _t1876
			}
			_t1870 = _t1873
		}
		_t1867 = _t1870
	}
	result1163 := _t1867
	p.recordSpan(int(span_start1162), "Read")
	return result1163
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1165 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1882 := p.parse_relation_id()
	relation_id1164 := _t1882
	p.consumeLiteral(")")
	_t1883 := &pb.Demand{RelationId: relation_id1164}
	result1166 := _t1883
	p.recordSpan(int(span_start1165), "Demand")
	return result1166
}

func (p *Parser) parse_output() *pb.Output {
	span_start1169 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1884 := p.parse_name()
	name1167 := _t1884
	_t1885 := p.parse_relation_id()
	relation_id1168 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.Output{Name: name1167, RelationId: relation_id1168}
	result1170 := _t1886
	p.recordSpan(int(span_start1169), "Output")
	return result1170
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1173 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1887 := p.parse_name()
	name1171 := _t1887
	_t1888 := p.parse_epoch()
	epoch1172 := _t1888
	p.consumeLiteral(")")
	_t1889 := &pb.WhatIf{Branch: name1171, Epoch: epoch1172}
	result1174 := _t1889
	p.recordSpan(int(span_start1173), "WhatIf")
	return result1174
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1177 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1890 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1891 := p.parse_name()
		_t1890 = ptr(_t1891)
	}
	name1175 := _t1890
	_t1892 := p.parse_relation_id()
	relation_id1176 := _t1892
	p.consumeLiteral(")")
	_t1893 := &pb.Abort{Name: deref(name1175, "abort"), RelationId: relation_id1176}
	result1178 := _t1893
	p.recordSpan(int(span_start1177), "Abort")
	return result1178
}

func (p *Parser) parse_export() *pb.Export {
	span_start1180 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1894 := p.parse_export_csv_config()
	export_csv_config1179 := _t1894
	p.consumeLiteral(")")
	_t1895 := &pb.Export{}
	_t1895.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1179}
	result1181 := _t1895
	p.recordSpan(int(span_start1180), "Export")
	return result1181
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1189 := int64(p.spanStart())
	var _t1896 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1897 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1897 = 0
		} else {
			var _t1898 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1898 = 1
			} else {
				_t1898 = -1
			}
			_t1897 = _t1898
		}
		_t1896 = _t1897
	} else {
		_t1896 = -1
	}
	prediction1182 := _t1896
	var _t1899 *pb.ExportCSVConfig
	if prediction1182 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1900 := p.parse_export_csv_path()
		export_csv_path1186 := _t1900
		_t1901 := p.parse_export_csv_columns_list()
		export_csv_columns_list1187 := _t1901
		_t1902 := p.parse_config_dict()
		config_dict1188 := _t1902
		p.consumeLiteral(")")
		_t1903 := p.construct_export_csv_config(export_csv_path1186, export_csv_columns_list1187, config_dict1188)
		_t1899 = _t1903
	} else {
		var _t1904 *pb.ExportCSVConfig
		if prediction1182 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1905 := p.parse_export_csv_path()
			export_csv_path1183 := _t1905
			_t1906 := p.parse_export_csv_source()
			export_csv_source1184 := _t1906
			_t1907 := p.parse_csv_config()
			csv_config1185 := _t1907
			p.consumeLiteral(")")
			_t1908 := p.construct_export_csv_config_with_source(export_csv_path1183, export_csv_source1184, csv_config1185)
			_t1904 = _t1908
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1899 = _t1904
	}
	result1190 := _t1899
	p.recordSpan(int(span_start1189), "ExportCSVConfig")
	return result1190
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1191 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1191
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1198 := int64(p.spanStart())
	var _t1909 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1910 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1910 = 1
		} else {
			var _t1911 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1911 = 0
			} else {
				_t1911 = -1
			}
			_t1910 = _t1911
		}
		_t1909 = _t1910
	} else {
		_t1909 = -1
	}
	prediction1192 := _t1909
	var _t1912 *pb.ExportCSVSource
	if prediction1192 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1913 := p.parse_relation_id()
		relation_id1197 := _t1913
		p.consumeLiteral(")")
		_t1914 := &pb.ExportCSVSource{}
		_t1914.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1197}
		_t1912 = _t1914
	} else {
		var _t1915 *pb.ExportCSVSource
		if prediction1192 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1193 := []*pb.ExportCSVColumn{}
			cond1194 := p.matchLookaheadLiteral("(", 0)
			for cond1194 {
				_t1916 := p.parse_export_csv_column()
				item1195 := _t1916
				xs1193 = append(xs1193, item1195)
				cond1194 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1196 := xs1193
			p.consumeLiteral(")")
			_t1917 := &pb.ExportCSVColumns{Columns: export_csv_columns1196}
			_t1918 := &pb.ExportCSVSource{}
			_t1918.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1917}
			_t1915 = _t1918
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1912 = _t1915
	}
	result1199 := _t1912
	p.recordSpan(int(span_start1198), "ExportCSVSource")
	return result1199
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1202 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1200 := p.consumeTerminal("STRING").Value.str
	_t1919 := p.parse_relation_id()
	relation_id1201 := _t1919
	p.consumeLiteral(")")
	_t1920 := &pb.ExportCSVColumn{ColumnName: string1200, ColumnData: relation_id1201}
	result1203 := _t1920
	p.recordSpan(int(span_start1202), "ExportCSVColumn")
	return result1203
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1204 := []*pb.ExportCSVColumn{}
	cond1205 := p.matchLookaheadLiteral("(", 0)
	for cond1205 {
		_t1921 := p.parse_export_csv_column()
		item1206 := _t1921
		xs1204 = append(xs1204, item1206)
		cond1205 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1207 := xs1204
	p.consumeLiteral(")")
	return export_csv_columns1207
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
