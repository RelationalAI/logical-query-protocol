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
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_.#/-]*`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanSymbol(s)} }},
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

// valueMapFromPairs builds map[string]*pb.Value from (key, *pb.Value) pair rows.
func valueMapFromPairs(pairs [][]interface{}) map[string]*pb.Value {
	out := make(map[string]*pb.Value)
	for _, pair := range pairs {
		if len(pair) >= 2 {
			k, _ := pair[0].(string)
			v, _ := pair[1].(*pb.Value)
			out[k] = v
		}
	}
	return out
}

// stringMapFromPairs builds map[string]string from (prop key value) pair rows.
func stringMapFromPairs(pairs [][]interface{}) map[string]string {
	out := make(map[string]string)
	for _, pair := range pairs {
		if len(pair) >= 2 {
			k, _ := pair[0].(string)
			v, _ := pair[1].(string)
			out[k] = v
		}
	}
	return out
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
	var _t2251 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2251
	var _t2252 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2252
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2253 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2253
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2254 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2254
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2255 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2255
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2256 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2256
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2257 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2257
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2258 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2258
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2259 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2259
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2260 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2260
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2261 := &pb.PlainTargets{Targets: targets}
	_t2262 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2262.Body = &pb.TargetRelations_Plain{Plain: _t2261}
	return _t2262
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2263 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2264 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2264.Body = &pb.TargetRelations_Cdc{Cdc: _t2263}
	return _t2264
}

func (p *Parser) construct_relations(keys []interface{}, body *pb.TargetRelations, load_errors_opt *pb.RelationId) *pb.TargetRelations {
	var _t2265 interface{}
	if hasProtoField(body, "plain") {
		_t2266 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
		_t2266.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2266
	}
	_ = _t2265
	_t2267 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
	_t2267.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2267
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2268 := columns_opt
	if columns_opt == nil {
		_t2268 = []*pb.GNFColumn{}
	}
	_t2269 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2268, Asof: asof, Relations: relations_opt}
	return _t2269
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2270 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2270
	_t2271 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2271
	_t2272 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2272
	_t2273 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2273
	_t2274 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2274
	_t2275 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2275
	_t2276 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2276
	_t2277 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2277
	_t2278 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2278
	_t2279 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2279
	_t2280 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2280
	_t2281 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2281
	_t2282 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2282
	_t2283 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2283
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2284 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2284
	config := dictFromList(storage_integration_opt)
	_t2285 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2286 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2287 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2288 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2289 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2290 := &pb.StorageIntegration{Provider: _t2285, AzureSasToken: _t2286, S3Region: _t2287, S3AccessKeyId: _t2288, S3SecretAccessKey: _t2289}
	return _t2290
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2291 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2291
	_t2292 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2292
	_t2293 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2293
	_t2294 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2294
	_t2295 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2295
	_t2296 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2296
	_t2297 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2297
	_t2298 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2298
	_t2299 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2299
	_t2300 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2300.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2300.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2300
	_t2301 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2301
}

func (p *Parser) default_configure() *pb.Configure {
	_t2302 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2302
	_t2303 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2303
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
	_t2304 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2304
	_t2305 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2305
	config_values_pairs := [][]interface{}{}
	for _, pair := range config_dict {
		if (pair[0].(string) != "semantics_version" && pair[0].(string) != "ivm.maintenance_level") {
			config_values_pairs = append(config_values_pairs, pair)
		}
	}
	configuration_values := valueMapFromPairs(config_values_pairs)
	_t2306 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config, ConfigurationValues: configuration_values}
	return _t2306
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2307 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2307
	_t2308 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2308
	_t2309 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2309
	_t2310 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2310
	_t2311 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2311
	_t2312 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2312
	_t2313 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2313
	_t2314 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2314
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2315 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2315
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2316 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2316
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	var _t2317 interface{}
	if (columns_opt != nil && relations_opt != nil) {
		panic(ParseError{msg: "iceberg_data takes either `(columns ...)` or `(relations ...)`, not both"})
	}
	_ = _t2317
	_t2318 := columns_opt
	if columns_opt == nil {
		_t2318 = []*pb.GNFColumn{}
	}
	_t2319 := &pb.IcebergData{Locator: locator, Config: config, Columns: _t2318, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta, Relations: relations_opt}
	return _t2319
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2320 := config_dict
	if config_dict == nil {
		_t2320 = [][]interface{}{}
	}
	cfg := dictFromList(_t2320)
	_t2321 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2321
	_t2322 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2322
	_t2323 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2323
	table_props := stringMapFromPairs(table_property_pairs)
	_t2324 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2324
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1434 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1435 := p.parse_configure()
		_t1434 = _t1435
	}
	configure717 := _t1434
	var _t1436 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1437 := p.parse_sync()
		_t1436 = _t1437
	}
	sync718 := _t1436
	xs719 := []*pb.Epoch{}
	cond720 := p.matchLookaheadLiteral("(", 0)
	for cond720 {
		_t1438 := p.parse_epoch()
		item721 := _t1438
		xs719 = append(xs719, item721)
		cond720 = p.matchLookaheadLiteral("(", 0)
	}
	epochs722 := xs719
	p.consumeLiteral(")")
	_t1439 := p.default_configure()
	_t1440 := configure717
	if configure717 == nil {
		_t1440 = _t1439
	}
	_t1441 := &pb.Transaction{Epochs: epochs722, Configure: _t1440, Sync: sync718}
	result724 := _t1441
	p.recordSpan(int(span_start723), "Transaction")
	return result724
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start726 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1442 := p.parse_config_dict()
	config_dict725 := _t1442
	p.consumeLiteral(")")
	_t1443 := p.construct_configure(config_dict725)
	result727 := _t1443
	p.recordSpan(int(span_start726), "Configure")
	return result727
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs728 := [][]interface{}{}
	cond729 := p.matchLookaheadLiteral(":", 0)
	for cond729 {
		_t1444 := p.parse_config_key_value()
		item730 := _t1444
		xs728 = append(xs728, item730)
		cond729 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values731 := xs728
	p.consumeLiteral("}")
	return config_key_values731
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol732 := p.consumeTerminal("SYMBOL").Value.str
	_t1445 := p.parse_raw_value()
	raw_value733 := _t1445
	return []interface{}{symbol732, raw_value733}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start747 := int64(p.spanStart())
	var _t1446 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1446 = 12
	} else {
		var _t1447 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1447 = 11
		} else {
			var _t1448 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1448 = 12
			} else {
				var _t1449 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1450 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1450 = 1
					} else {
						var _t1451 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1451 = 0
						} else {
							_t1451 = -1
						}
						_t1450 = _t1451
					}
					_t1449 = _t1450
				} else {
					var _t1452 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1452 = 7
					} else {
						var _t1453 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1453 = 8
						} else {
							var _t1454 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1454 = 2
							} else {
								var _t1455 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1455 = 3
								} else {
									var _t1456 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1456 = 9
									} else {
										var _t1457 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1457 = 4
										} else {
											var _t1458 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1458 = 5
											} else {
												var _t1459 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1459 = 6
												} else {
													var _t1460 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1460 = 10
													} else {
														_t1460 = -1
													}
													_t1459 = _t1460
												}
												_t1458 = _t1459
											}
											_t1457 = _t1458
										}
										_t1456 = _t1457
									}
									_t1455 = _t1456
								}
								_t1454 = _t1455
							}
							_t1453 = _t1454
						}
						_t1452 = _t1453
					}
					_t1449 = _t1452
				}
				_t1448 = _t1449
			}
			_t1447 = _t1448
		}
		_t1446 = _t1447
	}
	prediction734 := _t1446
	var _t1461 *pb.Value
	if prediction734 == 12 {
		_t1462 := p.parse_boolean_value()
		boolean_value746 := _t1462
		_t1463 := &pb.Value{}
		_t1463.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value746}
		_t1461 = _t1463
	} else {
		var _t1464 *pb.Value
		if prediction734 == 11 {
			p.consumeLiteral("missing")
			_t1465 := &pb.MissingValue{}
			_t1466 := &pb.Value{}
			_t1466.Value = &pb.Value_MissingValue{MissingValue: _t1465}
			_t1464 = _t1466
		} else {
			var _t1467 *pb.Value
			if prediction734 == 10 {
				decimal745 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1468 := &pb.Value{}
				_t1468.Value = &pb.Value_DecimalValue{DecimalValue: decimal745}
				_t1467 = _t1468
			} else {
				var _t1469 *pb.Value
				if prediction734 == 9 {
					int128744 := p.consumeTerminal("INT128").Value.int128
					_t1470 := &pb.Value{}
					_t1470.Value = &pb.Value_Int128Value{Int128Value: int128744}
					_t1469 = _t1470
				} else {
					var _t1471 *pb.Value
					if prediction734 == 8 {
						uint128743 := p.consumeTerminal("UINT128").Value.uint128
						_t1472 := &pb.Value{}
						_t1472.Value = &pb.Value_Uint128Value{Uint128Value: uint128743}
						_t1471 = _t1472
					} else {
						var _t1473 *pb.Value
						if prediction734 == 7 {
							uint32742 := p.consumeTerminal("UINT32").Value.u32
							_t1474 := &pb.Value{}
							_t1474.Value = &pb.Value_Uint32Value{Uint32Value: uint32742}
							_t1473 = _t1474
						} else {
							var _t1475 *pb.Value
							if prediction734 == 6 {
								float741 := p.consumeTerminal("FLOAT").Value.f64
								_t1476 := &pb.Value{}
								_t1476.Value = &pb.Value_FloatValue{FloatValue: float741}
								_t1475 = _t1476
							} else {
								var _t1477 *pb.Value
								if prediction734 == 5 {
									float32740 := p.consumeTerminal("FLOAT32").Value.f32
									_t1478 := &pb.Value{}
									_t1478.Value = &pb.Value_Float32Value{Float32Value: float32740}
									_t1477 = _t1478
								} else {
									var _t1479 *pb.Value
									if prediction734 == 4 {
										int739 := p.consumeTerminal("INT").Value.i64
										_t1480 := &pb.Value{}
										_t1480.Value = &pb.Value_IntValue{IntValue: int739}
										_t1479 = _t1480
									} else {
										var _t1481 *pb.Value
										if prediction734 == 3 {
											int32738 := p.consumeTerminal("INT32").Value.i32
											_t1482 := &pb.Value{}
											_t1482.Value = &pb.Value_Int32Value{Int32Value: int32738}
											_t1481 = _t1482
										} else {
											var _t1483 *pb.Value
											if prediction734 == 2 {
												string737 := p.consumeTerminal("STRING").Value.str
												_t1484 := &pb.Value{}
												_t1484.Value = &pb.Value_StringValue{StringValue: string737}
												_t1483 = _t1484
											} else {
												var _t1485 *pb.Value
												if prediction734 == 1 {
													_t1486 := p.parse_raw_datetime()
													raw_datetime736 := _t1486
													_t1487 := &pb.Value{}
													_t1487.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime736}
													_t1485 = _t1487
												} else {
													var _t1488 *pb.Value
													if prediction734 == 0 {
														_t1489 := p.parse_raw_date()
														raw_date735 := _t1489
														_t1490 := &pb.Value{}
														_t1490.Value = &pb.Value_DateValue{DateValue: raw_date735}
														_t1488 = _t1490
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1485 = _t1488
												}
												_t1483 = _t1485
											}
											_t1481 = _t1483
										}
										_t1479 = _t1481
									}
									_t1477 = _t1479
								}
								_t1475 = _t1477
							}
							_t1473 = _t1475
						}
						_t1471 = _t1473
					}
					_t1469 = _t1471
				}
				_t1467 = _t1469
			}
			_t1464 = _t1467
		}
		_t1461 = _t1464
	}
	result748 := _t1461
	p.recordSpan(int(span_start747), "Value")
	return result748
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int749 := p.consumeTerminal("INT").Value.i64
	int_3750 := p.consumeTerminal("INT").Value.i64
	int_4751 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1491 := &pb.DateValue{Year: int32(int749), Month: int32(int_3750), Day: int32(int_4751)}
	result753 := _t1491
	p.recordSpan(int(span_start752), "DateValue")
	return result753
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int754 := p.consumeTerminal("INT").Value.i64
	int_3755 := p.consumeTerminal("INT").Value.i64
	int_4756 := p.consumeTerminal("INT").Value.i64
	int_5757 := p.consumeTerminal("INT").Value.i64
	int_6758 := p.consumeTerminal("INT").Value.i64
	int_7759 := p.consumeTerminal("INT").Value.i64
	var _t1492 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1492 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8760 := _t1492
	p.consumeLiteral(")")
	_t1493 := &pb.DateTimeValue{Year: int32(int754), Month: int32(int_3755), Day: int32(int_4756), Hour: int32(int_5757), Minute: int32(int_6758), Second: int32(int_7759), Microsecond: int32(deref(int_8760, 0))}
	result762 := _t1493
	p.recordSpan(int(span_start761), "DateTimeValue")
	return result762
}

func (p *Parser) parse_boolean_value() bool {
	var _t1494 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1494 = 0
	} else {
		var _t1495 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1495 = 1
		} else {
			_t1495 = -1
		}
		_t1494 = _t1495
	}
	prediction763 := _t1494
	var _t1496 bool
	if prediction763 == 1 {
		p.consumeLiteral("false")
		_t1496 = false
	} else {
		var _t1497 bool
		if prediction763 == 0 {
			p.consumeLiteral("true")
			_t1497 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1496 = _t1497
	}
	return _t1496
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start768 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs764 := []*pb.FragmentId{}
	cond765 := p.matchLookaheadLiteral(":", 0)
	for cond765 {
		_t1498 := p.parse_fragment_id()
		item766 := _t1498
		xs764 = append(xs764, item766)
		cond765 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids767 := xs764
	p.consumeLiteral(")")
	_t1499 := &pb.Sync{Fragments: fragment_ids767}
	result769 := _t1499
	p.recordSpan(int(span_start768), "Sync")
	return result769
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start771 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol770 := p.consumeTerminal("SYMBOL").Value.str
	result772 := &pb.FragmentId{Id: []byte(symbol770)}
	p.recordSpan(int(span_start771), "FragmentId")
	return result772
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start775 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1500 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1501 := p.parse_epoch_writes()
		_t1500 = _t1501
	}
	epoch_writes773 := _t1500
	var _t1502 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1503 := p.parse_epoch_reads()
		_t1502 = _t1503
	}
	epoch_reads774 := _t1502
	p.consumeLiteral(")")
	_t1504 := epoch_writes773
	if epoch_writes773 == nil {
		_t1504 = []*pb.Write{}
	}
	_t1505 := epoch_reads774
	if epoch_reads774 == nil {
		_t1505 = []*pb.Read{}
	}
	_t1506 := &pb.Epoch{Writes: _t1504, Reads: _t1505}
	result776 := _t1506
	p.recordSpan(int(span_start775), "Epoch")
	return result776
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs777 := []*pb.Write{}
	cond778 := p.matchLookaheadLiteral("(", 0)
	for cond778 {
		_t1507 := p.parse_write()
		item779 := _t1507
		xs777 = append(xs777, item779)
		cond778 = p.matchLookaheadLiteral("(", 0)
	}
	writes780 := xs777
	p.consumeLiteral(")")
	return writes780
}

func (p *Parser) parse_write() *pb.Write {
	span_start786 := int64(p.spanStart())
	var _t1508 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1509 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1509 = 1
		} else {
			var _t1510 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1510 = 3
			} else {
				var _t1511 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1511 = 0
				} else {
					var _t1512 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1512 = 2
					} else {
						_t1512 = -1
					}
					_t1511 = _t1512
				}
				_t1510 = _t1511
			}
			_t1509 = _t1510
		}
		_t1508 = _t1509
	} else {
		_t1508 = -1
	}
	prediction781 := _t1508
	var _t1513 *pb.Write
	if prediction781 == 3 {
		_t1514 := p.parse_snapshot()
		snapshot785 := _t1514
		_t1515 := &pb.Write{}
		_t1515.WriteType = &pb.Write_Snapshot{Snapshot: snapshot785}
		_t1513 = _t1515
	} else {
		var _t1516 *pb.Write
		if prediction781 == 2 {
			_t1517 := p.parse_context()
			context784 := _t1517
			_t1518 := &pb.Write{}
			_t1518.WriteType = &pb.Write_Context{Context: context784}
			_t1516 = _t1518
		} else {
			var _t1519 *pb.Write
			if prediction781 == 1 {
				_t1520 := p.parse_undefine()
				undefine783 := _t1520
				_t1521 := &pb.Write{}
				_t1521.WriteType = &pb.Write_Undefine{Undefine: undefine783}
				_t1519 = _t1521
			} else {
				var _t1522 *pb.Write
				if prediction781 == 0 {
					_t1523 := p.parse_define()
					define782 := _t1523
					_t1524 := &pb.Write{}
					_t1524.WriteType = &pb.Write_Define{Define: define782}
					_t1522 = _t1524
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1519 = _t1522
			}
			_t1516 = _t1519
		}
		_t1513 = _t1516
	}
	result787 := _t1513
	p.recordSpan(int(span_start786), "Write")
	return result787
}

func (p *Parser) parse_define() *pb.Define {
	span_start789 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1525 := p.parse_fragment()
	fragment788 := _t1525
	p.consumeLiteral(")")
	_t1526 := &pb.Define{Fragment: fragment788}
	result790 := _t1526
	p.recordSpan(int(span_start789), "Define")
	return result790
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1527 := p.parse_new_fragment_id()
	new_fragment_id791 := _t1527
	xs792 := []*pb.Declaration{}
	cond793 := p.matchLookaheadLiteral("(", 0)
	for cond793 {
		_t1528 := p.parse_declaration()
		item794 := _t1528
		xs792 = append(xs792, item794)
		cond793 = p.matchLookaheadLiteral("(", 0)
	}
	declarations795 := xs792
	p.consumeLiteral(")")
	result797 := p.constructFragment(new_fragment_id791, declarations795)
	p.recordSpan(int(span_start796), "Fragment")
	return result797
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start799 := int64(p.spanStart())
	_t1529 := p.parse_fragment_id()
	fragment_id798 := _t1529
	p.startFragment(fragment_id798)
	result800 := fragment_id798
	p.recordSpan(int(span_start799), "FragmentId")
	return result800
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start806 := int64(p.spanStart())
	var _t1530 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1531 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1531 = 3
		} else {
			var _t1532 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1532 = 2
			} else {
				var _t1533 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1533 = 3
				} else {
					var _t1534 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1534 = 0
					} else {
						var _t1535 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1535 = 3
						} else {
							var _t1536 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1536 = 3
							} else {
								var _t1537 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1537 = 1
								} else {
									_t1537 = -1
								}
								_t1536 = _t1537
							}
							_t1535 = _t1536
						}
						_t1534 = _t1535
					}
					_t1533 = _t1534
				}
				_t1532 = _t1533
			}
			_t1531 = _t1532
		}
		_t1530 = _t1531
	} else {
		_t1530 = -1
	}
	prediction801 := _t1530
	var _t1538 *pb.Declaration
	if prediction801 == 3 {
		_t1539 := p.parse_data()
		data805 := _t1539
		_t1540 := &pb.Declaration{}
		_t1540.DeclarationType = &pb.Declaration_Data{Data: data805}
		_t1538 = _t1540
	} else {
		var _t1541 *pb.Declaration
		if prediction801 == 2 {
			_t1542 := p.parse_constraint()
			constraint804 := _t1542
			_t1543 := &pb.Declaration{}
			_t1543.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint804}
			_t1541 = _t1543
		} else {
			var _t1544 *pb.Declaration
			if prediction801 == 1 {
				_t1545 := p.parse_algorithm()
				algorithm803 := _t1545
				_t1546 := &pb.Declaration{}
				_t1546.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm803}
				_t1544 = _t1546
			} else {
				var _t1547 *pb.Declaration
				if prediction801 == 0 {
					_t1548 := p.parse_def()
					def802 := _t1548
					_t1549 := &pb.Declaration{}
					_t1549.DeclarationType = &pb.Declaration_Def{Def: def802}
					_t1547 = _t1549
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1544 = _t1547
			}
			_t1541 = _t1544
		}
		_t1538 = _t1541
	}
	result807 := _t1538
	p.recordSpan(int(span_start806), "Declaration")
	return result807
}

func (p *Parser) parse_def() *pb.Def {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1550 := p.parse_relation_id()
	relation_id808 := _t1550
	_t1551 := p.parse_abstraction()
	abstraction809 := _t1551
	var _t1552 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1553 := p.parse_attrs()
		_t1552 = _t1553
	}
	attrs810 := _t1552
	p.consumeLiteral(")")
	_t1554 := attrs810
	if attrs810 == nil {
		_t1554 = []*pb.Attribute{}
	}
	_t1555 := &pb.Def{Name: relation_id808, Body: abstraction809, Attrs: _t1554}
	result812 := _t1555
	p.recordSpan(int(span_start811), "Def")
	return result812
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start816 := int64(p.spanStart())
	var _t1556 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1556 = 0
	} else {
		var _t1557 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1557 = 1
		} else {
			_t1557 = -1
		}
		_t1556 = _t1557
	}
	prediction813 := _t1556
	var _t1558 *pb.RelationId
	if prediction813 == 1 {
		uint128815 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128815
		_t1558 = &pb.RelationId{IdLow: uint128815.Low, IdHigh: uint128815.High}
	} else {
		var _t1559 *pb.RelationId
		if prediction813 == 0 {
			p.consumeLiteral(":")
			symbol814 := p.consumeTerminal("SYMBOL").Value.str
			_t1559 = p.relationIdFromString(symbol814)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1558 = _t1559
	}
	result817 := _t1558
	p.recordSpan(int(span_start816), "RelationId")
	return result817
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1560 := p.parse_bindings()
	bindings818 := _t1560
	_t1561 := p.parse_formula()
	formula819 := _t1561
	p.consumeLiteral(")")
	_t1562 := &pb.Abstraction{Vars: listConcat(bindings818[0].([]*pb.Binding), bindings818[1].([]*pb.Binding)), Value: formula819}
	result821 := _t1562
	p.recordSpan(int(span_start820), "Abstraction")
	return result821
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs822 := []*pb.Binding{}
	cond823 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond823 {
		_t1563 := p.parse_binding()
		item824 := _t1563
		xs822 = append(xs822, item824)
		cond823 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings825 := xs822
	var _t1564 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1565 := p.parse_value_bindings()
		_t1564 = _t1565
	}
	value_bindings826 := _t1564
	p.consumeLiteral("]")
	_t1566 := value_bindings826
	if value_bindings826 == nil {
		_t1566 = []*pb.Binding{}
	}
	return []interface{}{bindings825, _t1566}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start829 := int64(p.spanStart())
	symbol827 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1567 := p.parse_type()
	type828 := _t1567
	_t1568 := &pb.Var{Name: symbol827}
	_t1569 := &pb.Binding{Var: _t1568, Type: type828}
	result830 := _t1569
	p.recordSpan(int(span_start829), "Binding")
	return result830
}

func (p *Parser) parse_type() *pb.Type {
	span_start847 := int64(p.spanStart())
	var _t1570 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1570 = 0
	} else {
		var _t1571 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1571 = 13
		} else {
			var _t1572 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1572 = 4
			} else {
				var _t1573 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1573 = 1
				} else {
					var _t1574 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1574 = 8
					} else {
						var _t1575 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1575 = 11
						} else {
							var _t1576 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1576 = 5
							} else {
								var _t1577 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1577 = 2
								} else {
									var _t1578 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1578 = 12
									} else {
										var _t1579 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1579 = 3
										} else {
											var _t1580 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1580 = 7
											} else {
												var _t1581 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1581 = 6
												} else {
													var _t1582 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1582 = 10
													} else {
														var _t1583 int64
														if p.matchLookaheadLiteral("(", 0) {
															var _t1584 int64
															if p.matchLookaheadLiteral("FIXED", 1) {
																_t1584 = 14
															} else {
																var _t1585 int64
																if p.matchLookaheadLiteral("DECIMAL", 1) {
																	_t1585 = 9
																} else {
																	_t1585 = -1
																}
																_t1584 = _t1585
															}
															_t1583 = _t1584
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
				}
				_t1572 = _t1573
			}
			_t1571 = _t1572
		}
		_t1570 = _t1571
	}
	prediction831 := _t1570
	var _t1586 *pb.Type
	if prediction831 == 14 {
		_t1587 := p.parse_fixed_type()
		fixed_type846 := _t1587
		_t1588 := &pb.Type{}
		_t1588.Type = &pb.Type_FixedType{FixedType: fixed_type846}
		_t1586 = _t1588
	} else {
		var _t1589 *pb.Type
		if prediction831 == 13 {
			_t1590 := p.parse_uint32_type()
			uint32_type845 := _t1590
			_t1591 := &pb.Type{}
			_t1591.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type845}
			_t1589 = _t1591
		} else {
			var _t1592 *pb.Type
			if prediction831 == 12 {
				_t1593 := p.parse_float32_type()
				float32_type844 := _t1593
				_t1594 := &pb.Type{}
				_t1594.Type = &pb.Type_Float32Type{Float32Type: float32_type844}
				_t1592 = _t1594
			} else {
				var _t1595 *pb.Type
				if prediction831 == 11 {
					_t1596 := p.parse_int32_type()
					int32_type843 := _t1596
					_t1597 := &pb.Type{}
					_t1597.Type = &pb.Type_Int32Type{Int32Type: int32_type843}
					_t1595 = _t1597
				} else {
					var _t1598 *pb.Type
					if prediction831 == 10 {
						_t1599 := p.parse_boolean_type()
						boolean_type842 := _t1599
						_t1600 := &pb.Type{}
						_t1600.Type = &pb.Type_BooleanType{BooleanType: boolean_type842}
						_t1598 = _t1600
					} else {
						var _t1601 *pb.Type
						if prediction831 == 9 {
							_t1602 := p.parse_decimal_type()
							decimal_type841 := _t1602
							_t1603 := &pb.Type{}
							_t1603.Type = &pb.Type_DecimalType{DecimalType: decimal_type841}
							_t1601 = _t1603
						} else {
							var _t1604 *pb.Type
							if prediction831 == 8 {
								_t1605 := p.parse_missing_type()
								missing_type840 := _t1605
								_t1606 := &pb.Type{}
								_t1606.Type = &pb.Type_MissingType{MissingType: missing_type840}
								_t1604 = _t1606
							} else {
								var _t1607 *pb.Type
								if prediction831 == 7 {
									_t1608 := p.parse_datetime_type()
									datetime_type839 := _t1608
									_t1609 := &pb.Type{}
									_t1609.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type839}
									_t1607 = _t1609
								} else {
									var _t1610 *pb.Type
									if prediction831 == 6 {
										_t1611 := p.parse_date_type()
										date_type838 := _t1611
										_t1612 := &pb.Type{}
										_t1612.Type = &pb.Type_DateType{DateType: date_type838}
										_t1610 = _t1612
									} else {
										var _t1613 *pb.Type
										if prediction831 == 5 {
											_t1614 := p.parse_int128_type()
											int128_type837 := _t1614
											_t1615 := &pb.Type{}
											_t1615.Type = &pb.Type_Int128Type{Int128Type: int128_type837}
											_t1613 = _t1615
										} else {
											var _t1616 *pb.Type
											if prediction831 == 4 {
												_t1617 := p.parse_uint128_type()
												uint128_type836 := _t1617
												_t1618 := &pb.Type{}
												_t1618.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type836}
												_t1616 = _t1618
											} else {
												var _t1619 *pb.Type
												if prediction831 == 3 {
													_t1620 := p.parse_float_type()
													float_type835 := _t1620
													_t1621 := &pb.Type{}
													_t1621.Type = &pb.Type_FloatType{FloatType: float_type835}
													_t1619 = _t1621
												} else {
													var _t1622 *pb.Type
													if prediction831 == 2 {
														_t1623 := p.parse_int_type()
														int_type834 := _t1623
														_t1624 := &pb.Type{}
														_t1624.Type = &pb.Type_IntType{IntType: int_type834}
														_t1622 = _t1624
													} else {
														var _t1625 *pb.Type
														if prediction831 == 1 {
															_t1626 := p.parse_string_type()
															string_type833 := _t1626
															_t1627 := &pb.Type{}
															_t1627.Type = &pb.Type_StringType{StringType: string_type833}
															_t1625 = _t1627
														} else {
															var _t1628 *pb.Type
															if prediction831 == 0 {
																_t1629 := p.parse_unspecified_type()
																unspecified_type832 := _t1629
																_t1630 := &pb.Type{}
																_t1630.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type832}
																_t1628 = _t1630
															} else {
																panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
															}
															_t1625 = _t1628
														}
														_t1622 = _t1625
													}
													_t1619 = _t1622
												}
												_t1616 = _t1619
											}
											_t1613 = _t1616
										}
										_t1610 = _t1613
									}
									_t1607 = _t1610
								}
								_t1604 = _t1607
							}
							_t1601 = _t1604
						}
						_t1598 = _t1601
					}
					_t1595 = _t1598
				}
				_t1592 = _t1595
			}
			_t1589 = _t1592
		}
		_t1586 = _t1589
	}
	result848 := _t1586
	p.recordSpan(int(span_start847), "Type")
	return result848
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1631 := &pb.UnspecifiedType{}
	result850 := _t1631
	p.recordSpan(int(span_start849), "UnspecifiedType")
	return result850
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1632 := &pb.StringType{}
	result852 := _t1632
	p.recordSpan(int(span_start851), "StringType")
	return result852
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1633 := &pb.IntType{}
	result854 := _t1633
	p.recordSpan(int(span_start853), "IntType")
	return result854
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1634 := &pb.FloatType{}
	result856 := _t1634
	p.recordSpan(int(span_start855), "FloatType")
	return result856
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1635 := &pb.UInt128Type{}
	result858 := _t1635
	p.recordSpan(int(span_start857), "UInt128Type")
	return result858
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1636 := &pb.Int128Type{}
	result860 := _t1636
	p.recordSpan(int(span_start859), "Int128Type")
	return result860
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1637 := &pb.DateType{}
	result862 := _t1637
	p.recordSpan(int(span_start861), "DateType")
	return result862
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1638 := &pb.DateTimeType{}
	result864 := _t1638
	p.recordSpan(int(span_start863), "DateTimeType")
	return result864
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1639 := &pb.MissingType{}
	result866 := _t1639
	p.recordSpan(int(span_start865), "MissingType")
	return result866
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int867 := p.consumeTerminal("INT").Value.i64
	int_3868 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1640 := &pb.DecimalType{Precision: int32(int867), Scale: int32(int_3868)}
	result870 := _t1640
	p.recordSpan(int(span_start869), "DecimalType")
	return result870
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start871 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1641 := &pb.BooleanType{}
	result872 := _t1641
	p.recordSpan(int(span_start871), "BooleanType")
	return result872
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start873 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1642 := &pb.Int32Type{}
	result874 := _t1642
	p.recordSpan(int(span_start873), "Int32Type")
	return result874
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start875 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1643 := &pb.Float32Type{}
	result876 := _t1643
	p.recordSpan(int(span_start875), "Float32Type")
	return result876
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start877 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1644 := &pb.UInt32Type{}
	result878 := _t1644
	p.recordSpan(int(span_start877), "UInt32Type")
	return result878
}

func (p *Parser) parse_fixed_type() *pb.FixedType {
	span_start880 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("FIXED")
	int879 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1645 := &pb.FixedType{Length: int32(int879)}
	result881 := _t1645
	p.recordSpan(int(span_start880), "FixedType")
	return result881
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs882 := []*pb.Binding{}
	cond883 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond883 {
		_t1646 := p.parse_binding()
		item884 := _t1646
		xs882 = append(xs882, item884)
		cond883 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings885 := xs882
	return bindings885
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start900 := int64(p.spanStart())
	var _t1647 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1648 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1648 = 0
		} else {
			var _t1649 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1649 = 11
			} else {
				var _t1650 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1650 = 3
				} else {
					var _t1651 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1651 = 10
					} else {
						var _t1652 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1652 = 9
						} else {
							var _t1653 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1653 = 5
							} else {
								var _t1654 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1654 = 6
								} else {
									var _t1655 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1655 = 7
									} else {
										var _t1656 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1656 = 1
										} else {
											var _t1657 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1657 = 2
											} else {
												var _t1658 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1658 = 12
												} else {
													var _t1659 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1659 = 8
													} else {
														var _t1660 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1660 = 4
														} else {
															var _t1661 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1661 = 10
															} else {
																var _t1662 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1662 = 10
																} else {
																	var _t1663 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1663 = 10
																	} else {
																		var _t1664 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1664 = 10
																		} else {
																			var _t1665 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1665 = 10
																			} else {
																				var _t1666 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1666 = 10
																				} else {
																					var _t1667 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1667 = 10
																					} else {
																						var _t1668 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1668 = 10
																						} else {
																							var _t1669 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1669 = 10
																							} else {
																								_t1669 = -1
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
													_t1658 = _t1659
												}
												_t1657 = _t1658
											}
											_t1656 = _t1657
										}
										_t1655 = _t1656
									}
									_t1654 = _t1655
								}
								_t1653 = _t1654
							}
							_t1652 = _t1653
						}
						_t1651 = _t1652
					}
					_t1650 = _t1651
				}
				_t1649 = _t1650
			}
			_t1648 = _t1649
		}
		_t1647 = _t1648
	} else {
		_t1647 = -1
	}
	prediction886 := _t1647
	var _t1670 *pb.Formula
	if prediction886 == 12 {
		_t1671 := p.parse_cast()
		cast899 := _t1671
		_t1672 := &pb.Formula{}
		_t1672.FormulaType = &pb.Formula_Cast{Cast: cast899}
		_t1670 = _t1672
	} else {
		var _t1673 *pb.Formula
		if prediction886 == 11 {
			_t1674 := p.parse_rel_atom()
			rel_atom898 := _t1674
			_t1675 := &pb.Formula{}
			_t1675.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom898}
			_t1673 = _t1675
		} else {
			var _t1676 *pb.Formula
			if prediction886 == 10 {
				_t1677 := p.parse_primitive()
				primitive897 := _t1677
				_t1678 := &pb.Formula{}
				_t1678.FormulaType = &pb.Formula_Primitive{Primitive: primitive897}
				_t1676 = _t1678
			} else {
				var _t1679 *pb.Formula
				if prediction886 == 9 {
					_t1680 := p.parse_pragma()
					pragma896 := _t1680
					_t1681 := &pb.Formula{}
					_t1681.FormulaType = &pb.Formula_Pragma{Pragma: pragma896}
					_t1679 = _t1681
				} else {
					var _t1682 *pb.Formula
					if prediction886 == 8 {
						_t1683 := p.parse_atom()
						atom895 := _t1683
						_t1684 := &pb.Formula{}
						_t1684.FormulaType = &pb.Formula_Atom{Atom: atom895}
						_t1682 = _t1684
					} else {
						var _t1685 *pb.Formula
						if prediction886 == 7 {
							_t1686 := p.parse_ffi()
							ffi894 := _t1686
							_t1687 := &pb.Formula{}
							_t1687.FormulaType = &pb.Formula_Ffi{Ffi: ffi894}
							_t1685 = _t1687
						} else {
							var _t1688 *pb.Formula
							if prediction886 == 6 {
								_t1689 := p.parse_not()
								not893 := _t1689
								_t1690 := &pb.Formula{}
								_t1690.FormulaType = &pb.Formula_Not{Not: not893}
								_t1688 = _t1690
							} else {
								var _t1691 *pb.Formula
								if prediction886 == 5 {
									_t1692 := p.parse_disjunction()
									disjunction892 := _t1692
									_t1693 := &pb.Formula{}
									_t1693.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction892}
									_t1691 = _t1693
								} else {
									var _t1694 *pb.Formula
									if prediction886 == 4 {
										_t1695 := p.parse_conjunction()
										conjunction891 := _t1695
										_t1696 := &pb.Formula{}
										_t1696.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction891}
										_t1694 = _t1696
									} else {
										var _t1697 *pb.Formula
										if prediction886 == 3 {
											_t1698 := p.parse_reduce()
											reduce890 := _t1698
											_t1699 := &pb.Formula{}
											_t1699.FormulaType = &pb.Formula_Reduce{Reduce: reduce890}
											_t1697 = _t1699
										} else {
											var _t1700 *pb.Formula
											if prediction886 == 2 {
												_t1701 := p.parse_exists()
												exists889 := _t1701
												_t1702 := &pb.Formula{}
												_t1702.FormulaType = &pb.Formula_Exists{Exists: exists889}
												_t1700 = _t1702
											} else {
												var _t1703 *pb.Formula
												if prediction886 == 1 {
													_t1704 := p.parse_false()
													false888 := _t1704
													_t1705 := &pb.Formula{}
													_t1705.FormulaType = &pb.Formula_Disjunction{Disjunction: false888}
													_t1703 = _t1705
												} else {
													var _t1706 *pb.Formula
													if prediction886 == 0 {
														_t1707 := p.parse_true()
														true887 := _t1707
														_t1708 := &pb.Formula{}
														_t1708.FormulaType = &pb.Formula_Conjunction{Conjunction: true887}
														_t1706 = _t1708
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1703 = _t1706
												}
												_t1700 = _t1703
											}
											_t1697 = _t1700
										}
										_t1694 = _t1697
									}
									_t1691 = _t1694
								}
								_t1688 = _t1691
							}
							_t1685 = _t1688
						}
						_t1682 = _t1685
					}
					_t1679 = _t1682
				}
				_t1676 = _t1679
			}
			_t1673 = _t1676
		}
		_t1670 = _t1673
	}
	result901 := _t1670
	p.recordSpan(int(span_start900), "Formula")
	return result901
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start902 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1709 := &pb.Conjunction{Args: []*pb.Formula{}}
	result903 := _t1709
	p.recordSpan(int(span_start902), "Conjunction")
	return result903
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1710 := &pb.Disjunction{Args: []*pb.Formula{}}
	result905 := _t1710
	p.recordSpan(int(span_start904), "Disjunction")
	return result905
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start908 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1711 := p.parse_bindings()
	bindings906 := _t1711
	_t1712 := p.parse_formula()
	formula907 := _t1712
	p.consumeLiteral(")")
	_t1713 := &pb.Abstraction{Vars: listConcat(bindings906[0].([]*pb.Binding), bindings906[1].([]*pb.Binding)), Value: formula907}
	_t1714 := &pb.Exists{Body: _t1713}
	result909 := _t1714
	p.recordSpan(int(span_start908), "Exists")
	return result909
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1715 := p.parse_abstraction()
	abstraction910 := _t1715
	_t1716 := p.parse_abstraction()
	abstraction_3911 := _t1716
	_t1717 := p.parse_terms()
	terms912 := _t1717
	p.consumeLiteral(")")
	_t1718 := &pb.Reduce{Op: abstraction910, Body: abstraction_3911, Terms: terms912}
	result914 := _t1718
	p.recordSpan(int(span_start913), "Reduce")
	return result914
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs915 := []*pb.Term{}
	cond916 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond916 {
		_t1719 := p.parse_term()
		item917 := _t1719
		xs915 = append(xs915, item917)
		cond916 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms918 := xs915
	p.consumeLiteral(")")
	return terms918
}

func (p *Parser) parse_term() *pb.Term {
	span_start922 := int64(p.spanStart())
	var _t1720 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1720 = 1
	} else {
		var _t1721 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1721 = 1
		} else {
			var _t1722 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1722 = 1
			} else {
				var _t1723 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1723 = 1
				} else {
					var _t1724 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1724 = 0
					} else {
						var _t1725 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1725 = 1
						} else {
							var _t1726 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1726 = 1
							} else {
								var _t1727 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1727 = 1
								} else {
									var _t1728 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1728 = 1
									} else {
										var _t1729 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1729 = 1
										} else {
											var _t1730 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1730 = 1
											} else {
												var _t1731 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1731 = 1
												} else {
													var _t1732 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1732 = 1
													} else {
														var _t1733 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1733 = 1
														} else {
															_t1733 = -1
														}
														_t1732 = _t1733
													}
													_t1731 = _t1732
												}
												_t1730 = _t1731
											}
											_t1729 = _t1730
										}
										_t1728 = _t1729
									}
									_t1727 = _t1728
								}
								_t1726 = _t1727
							}
							_t1725 = _t1726
						}
						_t1724 = _t1725
					}
					_t1723 = _t1724
				}
				_t1722 = _t1723
			}
			_t1721 = _t1722
		}
		_t1720 = _t1721
	}
	prediction919 := _t1720
	var _t1734 *pb.Term
	if prediction919 == 1 {
		_t1735 := p.parse_value()
		value921 := _t1735
		_t1736 := &pb.Term{}
		_t1736.TermType = &pb.Term_Constant{Constant: value921}
		_t1734 = _t1736
	} else {
		var _t1737 *pb.Term
		if prediction919 == 0 {
			_t1738 := p.parse_var()
			var920 := _t1738
			_t1739 := &pb.Term{}
			_t1739.TermType = &pb.Term_Var{Var: var920}
			_t1737 = _t1739
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1734 = _t1737
	}
	result923 := _t1734
	p.recordSpan(int(span_start922), "Term")
	return result923
}

func (p *Parser) parse_var() *pb.Var {
	span_start925 := int64(p.spanStart())
	symbol924 := p.consumeTerminal("SYMBOL").Value.str
	_t1740 := &pb.Var{Name: symbol924}
	result926 := _t1740
	p.recordSpan(int(span_start925), "Var")
	return result926
}

func (p *Parser) parse_value() *pb.Value {
	span_start940 := int64(p.spanStart())
	var _t1741 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1741 = 12
	} else {
		var _t1742 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1742 = 11
		} else {
			var _t1743 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1743 = 12
			} else {
				var _t1744 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1745 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1745 = 1
					} else {
						var _t1746 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1746 = 0
						} else {
							_t1746 = -1
						}
						_t1745 = _t1746
					}
					_t1744 = _t1745
				} else {
					var _t1747 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1747 = 7
					} else {
						var _t1748 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1748 = 8
						} else {
							var _t1749 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1749 = 2
							} else {
								var _t1750 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1750 = 3
								} else {
									var _t1751 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1751 = 9
									} else {
										var _t1752 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1752 = 4
										} else {
											var _t1753 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1753 = 5
											} else {
												var _t1754 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1754 = 6
												} else {
													var _t1755 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1755 = 10
													} else {
														_t1755 = -1
													}
													_t1754 = _t1755
												}
												_t1753 = _t1754
											}
											_t1752 = _t1753
										}
										_t1751 = _t1752
									}
									_t1750 = _t1751
								}
								_t1749 = _t1750
							}
							_t1748 = _t1749
						}
						_t1747 = _t1748
					}
					_t1744 = _t1747
				}
				_t1743 = _t1744
			}
			_t1742 = _t1743
		}
		_t1741 = _t1742
	}
	prediction927 := _t1741
	var _t1756 *pb.Value
	if prediction927 == 12 {
		_t1757 := p.parse_boolean_value()
		boolean_value939 := _t1757
		_t1758 := &pb.Value{}
		_t1758.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value939}
		_t1756 = _t1758
	} else {
		var _t1759 *pb.Value
		if prediction927 == 11 {
			p.consumeLiteral("missing")
			_t1760 := &pb.MissingValue{}
			_t1761 := &pb.Value{}
			_t1761.Value = &pb.Value_MissingValue{MissingValue: _t1760}
			_t1759 = _t1761
		} else {
			var _t1762 *pb.Value
			if prediction927 == 10 {
				formatted_decimal938 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1763 := &pb.Value{}
				_t1763.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal938}
				_t1762 = _t1763
			} else {
				var _t1764 *pb.Value
				if prediction927 == 9 {
					formatted_int128937 := p.consumeTerminal("INT128").Value.int128
					_t1765 := &pb.Value{}
					_t1765.Value = &pb.Value_Int128Value{Int128Value: formatted_int128937}
					_t1764 = _t1765
				} else {
					var _t1766 *pb.Value
					if prediction927 == 8 {
						formatted_uint128936 := p.consumeTerminal("UINT128").Value.uint128
						_t1767 := &pb.Value{}
						_t1767.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128936}
						_t1766 = _t1767
					} else {
						var _t1768 *pb.Value
						if prediction927 == 7 {
							formatted_uint32935 := p.consumeTerminal("UINT32").Value.u32
							_t1769 := &pb.Value{}
							_t1769.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32935}
							_t1768 = _t1769
						} else {
							var _t1770 *pb.Value
							if prediction927 == 6 {
								formatted_float934 := p.consumeTerminal("FLOAT").Value.f64
								_t1771 := &pb.Value{}
								_t1771.Value = &pb.Value_FloatValue{FloatValue: formatted_float934}
								_t1770 = _t1771
							} else {
								var _t1772 *pb.Value
								if prediction927 == 5 {
									formatted_float32933 := p.consumeTerminal("FLOAT32").Value.f32
									_t1773 := &pb.Value{}
									_t1773.Value = &pb.Value_Float32Value{Float32Value: formatted_float32933}
									_t1772 = _t1773
								} else {
									var _t1774 *pb.Value
									if prediction927 == 4 {
										formatted_int932 := p.consumeTerminal("INT").Value.i64
										_t1775 := &pb.Value{}
										_t1775.Value = &pb.Value_IntValue{IntValue: formatted_int932}
										_t1774 = _t1775
									} else {
										var _t1776 *pb.Value
										if prediction927 == 3 {
											formatted_int32931 := p.consumeTerminal("INT32").Value.i32
											_t1777 := &pb.Value{}
											_t1777.Value = &pb.Value_Int32Value{Int32Value: formatted_int32931}
											_t1776 = _t1777
										} else {
											var _t1778 *pb.Value
											if prediction927 == 2 {
												formatted_string930 := p.consumeTerminal("STRING").Value.str
												_t1779 := &pb.Value{}
												_t1779.Value = &pb.Value_StringValue{StringValue: formatted_string930}
												_t1778 = _t1779
											} else {
												var _t1780 *pb.Value
												if prediction927 == 1 {
													_t1781 := p.parse_datetime()
													datetime929 := _t1781
													_t1782 := &pb.Value{}
													_t1782.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime929}
													_t1780 = _t1782
												} else {
													var _t1783 *pb.Value
													if prediction927 == 0 {
														_t1784 := p.parse_date()
														date928 := _t1784
														_t1785 := &pb.Value{}
														_t1785.Value = &pb.Value_DateValue{DateValue: date928}
														_t1783 = _t1785
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1780 = _t1783
												}
												_t1778 = _t1780
											}
											_t1776 = _t1778
										}
										_t1774 = _t1776
									}
									_t1772 = _t1774
								}
								_t1770 = _t1772
							}
							_t1768 = _t1770
						}
						_t1766 = _t1768
					}
					_t1764 = _t1766
				}
				_t1762 = _t1764
			}
			_t1759 = _t1762
		}
		_t1756 = _t1759
	}
	result941 := _t1756
	p.recordSpan(int(span_start940), "Value")
	return result941
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start945 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int942 := p.consumeTerminal("INT").Value.i64
	formatted_int_3943 := p.consumeTerminal("INT").Value.i64
	formatted_int_4944 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1786 := &pb.DateValue{Year: int32(formatted_int942), Month: int32(formatted_int_3943), Day: int32(formatted_int_4944)}
	result946 := _t1786
	p.recordSpan(int(span_start945), "DateValue")
	return result946
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start954 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int947 := p.consumeTerminal("INT").Value.i64
	formatted_int_3948 := p.consumeTerminal("INT").Value.i64
	formatted_int_4949 := p.consumeTerminal("INT").Value.i64
	formatted_int_5950 := p.consumeTerminal("INT").Value.i64
	formatted_int_6951 := p.consumeTerminal("INT").Value.i64
	formatted_int_7952 := p.consumeTerminal("INT").Value.i64
	var _t1787 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1787 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8953 := _t1787
	p.consumeLiteral(")")
	_t1788 := &pb.DateTimeValue{Year: int32(formatted_int947), Month: int32(formatted_int_3948), Day: int32(formatted_int_4949), Hour: int32(formatted_int_5950), Minute: int32(formatted_int_6951), Second: int32(formatted_int_7952), Microsecond: int32(deref(formatted_int_8953, 0))}
	result955 := _t1788
	p.recordSpan(int(span_start954), "DateTimeValue")
	return result955
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs956 := []*pb.Formula{}
	cond957 := p.matchLookaheadLiteral("(", 0)
	for cond957 {
		_t1789 := p.parse_formula()
		item958 := _t1789
		xs956 = append(xs956, item958)
		cond957 = p.matchLookaheadLiteral("(", 0)
	}
	formulas959 := xs956
	p.consumeLiteral(")")
	_t1790 := &pb.Conjunction{Args: formulas959}
	result961 := _t1790
	p.recordSpan(int(span_start960), "Conjunction")
	return result961
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start966 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs962 := []*pb.Formula{}
	cond963 := p.matchLookaheadLiteral("(", 0)
	for cond963 {
		_t1791 := p.parse_formula()
		item964 := _t1791
		xs962 = append(xs962, item964)
		cond963 = p.matchLookaheadLiteral("(", 0)
	}
	formulas965 := xs962
	p.consumeLiteral(")")
	_t1792 := &pb.Disjunction{Args: formulas965}
	result967 := _t1792
	p.recordSpan(int(span_start966), "Disjunction")
	return result967
}

func (p *Parser) parse_not() *pb.Not {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1793 := p.parse_formula()
	formula968 := _t1793
	p.consumeLiteral(")")
	_t1794 := &pb.Not{Arg: formula968}
	result970 := _t1794
	p.recordSpan(int(span_start969), "Not")
	return result970
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1795 := p.parse_name()
	name971 := _t1795
	_t1796 := p.parse_ffi_args()
	ffi_args972 := _t1796
	_t1797 := p.parse_terms()
	terms973 := _t1797
	p.consumeLiteral(")")
	_t1798 := &pb.FFI{Name: name971, Args: ffi_args972, Terms: terms973}
	result975 := _t1798
	p.recordSpan(int(span_start974), "FFI")
	return result975
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol976 := p.consumeTerminal("SYMBOL").Value.str
	return symbol976
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs977 := []*pb.Abstraction{}
	cond978 := p.matchLookaheadLiteral("(", 0)
	for cond978 {
		_t1799 := p.parse_abstraction()
		item979 := _t1799
		xs977 = append(xs977, item979)
		cond978 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions980 := xs977
	p.consumeLiteral(")")
	return abstractions980
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1800 := p.parse_relation_id()
	relation_id981 := _t1800
	xs982 := []*pb.Term{}
	cond983 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond983 {
		_t1801 := p.parse_term()
		item984 := _t1801
		xs982 = append(xs982, item984)
		cond983 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms985 := xs982
	p.consumeLiteral(")")
	_t1802 := &pb.Atom{Name: relation_id981, Terms: terms985}
	result987 := _t1802
	p.recordSpan(int(span_start986), "Atom")
	return result987
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start993 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1803 := p.parse_name()
	name988 := _t1803
	xs989 := []*pb.Term{}
	cond990 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond990 {
		_t1804 := p.parse_term()
		item991 := _t1804
		xs989 = append(xs989, item991)
		cond990 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms992 := xs989
	p.consumeLiteral(")")
	_t1805 := &pb.Pragma{Name: name988, Terms: terms992}
	result994 := _t1805
	p.recordSpan(int(span_start993), "Pragma")
	return result994
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start1010 := int64(p.spanStart())
	var _t1806 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1807 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1807 = 9
		} else {
			var _t1808 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1808 = 4
			} else {
				var _t1809 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1809 = 3
				} else {
					var _t1810 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1810 = 0
					} else {
						var _t1811 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1811 = 2
						} else {
							var _t1812 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1812 = 1
							} else {
								var _t1813 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1813 = 8
								} else {
									var _t1814 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1814 = 6
									} else {
										var _t1815 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1815 = 5
										} else {
											var _t1816 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1816 = 7
											} else {
												_t1816 = -1
											}
											_t1815 = _t1816
										}
										_t1814 = _t1815
									}
									_t1813 = _t1814
								}
								_t1812 = _t1813
							}
							_t1811 = _t1812
						}
						_t1810 = _t1811
					}
					_t1809 = _t1810
				}
				_t1808 = _t1809
			}
			_t1807 = _t1808
		}
		_t1806 = _t1807
	} else {
		_t1806 = -1
	}
	prediction995 := _t1806
	var _t1817 *pb.Primitive
	if prediction995 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1818 := p.parse_name()
		name1005 := _t1818
		xs1006 := []*pb.RelTerm{}
		cond1007 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond1007 {
			_t1819 := p.parse_rel_term()
			item1008 := _t1819
			xs1006 = append(xs1006, item1008)
			cond1007 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms1009 := xs1006
		p.consumeLiteral(")")
		_t1820 := &pb.Primitive{Name: name1005, Terms: rel_terms1009}
		_t1817 = _t1820
	} else {
		var _t1821 *pb.Primitive
		if prediction995 == 8 {
			_t1822 := p.parse_divide()
			divide1004 := _t1822
			_t1821 = divide1004
		} else {
			var _t1823 *pb.Primitive
			if prediction995 == 7 {
				_t1824 := p.parse_multiply()
				multiply1003 := _t1824
				_t1823 = multiply1003
			} else {
				var _t1825 *pb.Primitive
				if prediction995 == 6 {
					_t1826 := p.parse_minus()
					minus1002 := _t1826
					_t1825 = minus1002
				} else {
					var _t1827 *pb.Primitive
					if prediction995 == 5 {
						_t1828 := p.parse_add()
						add1001 := _t1828
						_t1827 = add1001
					} else {
						var _t1829 *pb.Primitive
						if prediction995 == 4 {
							_t1830 := p.parse_gt_eq()
							gt_eq1000 := _t1830
							_t1829 = gt_eq1000
						} else {
							var _t1831 *pb.Primitive
							if prediction995 == 3 {
								_t1832 := p.parse_gt()
								gt999 := _t1832
								_t1831 = gt999
							} else {
								var _t1833 *pb.Primitive
								if prediction995 == 2 {
									_t1834 := p.parse_lt_eq()
									lt_eq998 := _t1834
									_t1833 = lt_eq998
								} else {
									var _t1835 *pb.Primitive
									if prediction995 == 1 {
										_t1836 := p.parse_lt()
										lt997 := _t1836
										_t1835 = lt997
									} else {
										var _t1837 *pb.Primitive
										if prediction995 == 0 {
											_t1838 := p.parse_eq()
											eq996 := _t1838
											_t1837 = eq996
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1835 = _t1837
									}
									_t1833 = _t1835
								}
								_t1831 = _t1833
							}
							_t1829 = _t1831
						}
						_t1827 = _t1829
					}
					_t1825 = _t1827
				}
				_t1823 = _t1825
			}
			_t1821 = _t1823
		}
		_t1817 = _t1821
	}
	result1011 := _t1817
	p.recordSpan(int(span_start1010), "Primitive")
	return result1011
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1839 := p.parse_term()
	term1012 := _t1839
	_t1840 := p.parse_term()
	term_31013 := _t1840
	p.consumeLiteral(")")
	_t1841 := &pb.RelTerm{}
	_t1841.RelTermType = &pb.RelTerm_Term{Term: term1012}
	_t1842 := &pb.RelTerm{}
	_t1842.RelTermType = &pb.RelTerm_Term{Term: term_31013}
	_t1843 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1841, _t1842}}
	result1015 := _t1843
	p.recordSpan(int(span_start1014), "Primitive")
	return result1015
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1844 := p.parse_term()
	term1016 := _t1844
	_t1845 := p.parse_term()
	term_31017 := _t1845
	p.consumeLiteral(")")
	_t1846 := &pb.RelTerm{}
	_t1846.RelTermType = &pb.RelTerm_Term{Term: term1016}
	_t1847 := &pb.RelTerm{}
	_t1847.RelTermType = &pb.RelTerm_Term{Term: term_31017}
	_t1848 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1846, _t1847}}
	result1019 := _t1848
	p.recordSpan(int(span_start1018), "Primitive")
	return result1019
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1849 := p.parse_term()
	term1020 := _t1849
	_t1850 := p.parse_term()
	term_31021 := _t1850
	p.consumeLiteral(")")
	_t1851 := &pb.RelTerm{}
	_t1851.RelTermType = &pb.RelTerm_Term{Term: term1020}
	_t1852 := &pb.RelTerm{}
	_t1852.RelTermType = &pb.RelTerm_Term{Term: term_31021}
	_t1853 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1851, _t1852}}
	result1023 := _t1853
	p.recordSpan(int(span_start1022), "Primitive")
	return result1023
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1854 := p.parse_term()
	term1024 := _t1854
	_t1855 := p.parse_term()
	term_31025 := _t1855
	p.consumeLiteral(")")
	_t1856 := &pb.RelTerm{}
	_t1856.RelTermType = &pb.RelTerm_Term{Term: term1024}
	_t1857 := &pb.RelTerm{}
	_t1857.RelTermType = &pb.RelTerm_Term{Term: term_31025}
	_t1858 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1856, _t1857}}
	result1027 := _t1858
	p.recordSpan(int(span_start1026), "Primitive")
	return result1027
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1030 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1859 := p.parse_term()
	term1028 := _t1859
	_t1860 := p.parse_term()
	term_31029 := _t1860
	p.consumeLiteral(")")
	_t1861 := &pb.RelTerm{}
	_t1861.RelTermType = &pb.RelTerm_Term{Term: term1028}
	_t1862 := &pb.RelTerm{}
	_t1862.RelTermType = &pb.RelTerm_Term{Term: term_31029}
	_t1863 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1861, _t1862}}
	result1031 := _t1863
	p.recordSpan(int(span_start1030), "Primitive")
	return result1031
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1035 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1864 := p.parse_term()
	term1032 := _t1864
	_t1865 := p.parse_term()
	term_31033 := _t1865
	_t1866 := p.parse_term()
	term_41034 := _t1866
	p.consumeLiteral(")")
	_t1867 := &pb.RelTerm{}
	_t1867.RelTermType = &pb.RelTerm_Term{Term: term1032}
	_t1868 := &pb.RelTerm{}
	_t1868.RelTermType = &pb.RelTerm_Term{Term: term_31033}
	_t1869 := &pb.RelTerm{}
	_t1869.RelTermType = &pb.RelTerm_Term{Term: term_41034}
	_t1870 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1867, _t1868, _t1869}}
	result1036 := _t1870
	p.recordSpan(int(span_start1035), "Primitive")
	return result1036
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1871 := p.parse_term()
	term1037 := _t1871
	_t1872 := p.parse_term()
	term_31038 := _t1872
	_t1873 := p.parse_term()
	term_41039 := _t1873
	p.consumeLiteral(")")
	_t1874 := &pb.RelTerm{}
	_t1874.RelTermType = &pb.RelTerm_Term{Term: term1037}
	_t1875 := &pb.RelTerm{}
	_t1875.RelTermType = &pb.RelTerm_Term{Term: term_31038}
	_t1876 := &pb.RelTerm{}
	_t1876.RelTermType = &pb.RelTerm_Term{Term: term_41039}
	_t1877 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1874, _t1875, _t1876}}
	result1041 := _t1877
	p.recordSpan(int(span_start1040), "Primitive")
	return result1041
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1045 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1878 := p.parse_term()
	term1042 := _t1878
	_t1879 := p.parse_term()
	term_31043 := _t1879
	_t1880 := p.parse_term()
	term_41044 := _t1880
	p.consumeLiteral(")")
	_t1881 := &pb.RelTerm{}
	_t1881.RelTermType = &pb.RelTerm_Term{Term: term1042}
	_t1882 := &pb.RelTerm{}
	_t1882.RelTermType = &pb.RelTerm_Term{Term: term_31043}
	_t1883 := &pb.RelTerm{}
	_t1883.RelTermType = &pb.RelTerm_Term{Term: term_41044}
	_t1884 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1881, _t1882, _t1883}}
	result1046 := _t1884
	p.recordSpan(int(span_start1045), "Primitive")
	return result1046
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1050 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1885 := p.parse_term()
	term1047 := _t1885
	_t1886 := p.parse_term()
	term_31048 := _t1886
	_t1887 := p.parse_term()
	term_41049 := _t1887
	p.consumeLiteral(")")
	_t1888 := &pb.RelTerm{}
	_t1888.RelTermType = &pb.RelTerm_Term{Term: term1047}
	_t1889 := &pb.RelTerm{}
	_t1889.RelTermType = &pb.RelTerm_Term{Term: term_31048}
	_t1890 := &pb.RelTerm{}
	_t1890.RelTermType = &pb.RelTerm_Term{Term: term_41049}
	_t1891 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1888, _t1889, _t1890}}
	result1051 := _t1891
	p.recordSpan(int(span_start1050), "Primitive")
	return result1051
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1055 := int64(p.spanStart())
	var _t1892 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1892 = 1
	} else {
		var _t1893 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1893 = 1
		} else {
			var _t1894 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1894 = 1
			} else {
				var _t1895 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1895 = 1
				} else {
					var _t1896 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1896 = 0
					} else {
						var _t1897 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1897 = 1
						} else {
							var _t1898 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1898 = 1
							} else {
								var _t1899 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1899 = 1
								} else {
									var _t1900 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1900 = 1
									} else {
										var _t1901 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1901 = 1
										} else {
											var _t1902 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1902 = 1
											} else {
												var _t1903 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1903 = 1
												} else {
													var _t1904 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1904 = 1
													} else {
														var _t1905 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1905 = 1
														} else {
															var _t1906 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1906 = 1
															} else {
																_t1906 = -1
															}
															_t1905 = _t1906
														}
														_t1904 = _t1905
													}
													_t1903 = _t1904
												}
												_t1902 = _t1903
											}
											_t1901 = _t1902
										}
										_t1900 = _t1901
									}
									_t1899 = _t1900
								}
								_t1898 = _t1899
							}
							_t1897 = _t1898
						}
						_t1896 = _t1897
					}
					_t1895 = _t1896
				}
				_t1894 = _t1895
			}
			_t1893 = _t1894
		}
		_t1892 = _t1893
	}
	prediction1052 := _t1892
	var _t1907 *pb.RelTerm
	if prediction1052 == 1 {
		_t1908 := p.parse_term()
		term1054 := _t1908
		_t1909 := &pb.RelTerm{}
		_t1909.RelTermType = &pb.RelTerm_Term{Term: term1054}
		_t1907 = _t1909
	} else {
		var _t1910 *pb.RelTerm
		if prediction1052 == 0 {
			_t1911 := p.parse_specialized_value()
			specialized_value1053 := _t1911
			_t1912 := &pb.RelTerm{}
			_t1912.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1053}
			_t1910 = _t1912
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1907 = _t1910
	}
	result1056 := _t1907
	p.recordSpan(int(span_start1055), "RelTerm")
	return result1056
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1058 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1913 := p.parse_raw_value()
	raw_value1057 := _t1913
	result1059 := raw_value1057
	p.recordSpan(int(span_start1058), "Value")
	return result1059
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1065 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1914 := p.parse_name()
	name1060 := _t1914
	xs1061 := []*pb.RelTerm{}
	cond1062 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1062 {
		_t1915 := p.parse_rel_term()
		item1063 := _t1915
		xs1061 = append(xs1061, item1063)
		cond1062 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1064 := xs1061
	p.consumeLiteral(")")
	_t1916 := &pb.RelAtom{Name: name1060, Terms: rel_terms1064}
	result1066 := _t1916
	p.recordSpan(int(span_start1065), "RelAtom")
	return result1066
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1069 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1917 := p.parse_term()
	term1067 := _t1917
	_t1918 := p.parse_term()
	term_31068 := _t1918
	p.consumeLiteral(")")
	_t1919 := &pb.Cast{Input: term1067, Result: term_31068}
	result1070 := _t1919
	p.recordSpan(int(span_start1069), "Cast")
	return result1070
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1071 := []*pb.Attribute{}
	cond1072 := p.matchLookaheadLiteral("(", 0)
	for cond1072 {
		_t1920 := p.parse_attribute()
		item1073 := _t1920
		xs1071 = append(xs1071, item1073)
		cond1072 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1074 := xs1071
	p.consumeLiteral(")")
	return attributes1074
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1921 := p.parse_name()
	name1075 := _t1921
	xs1076 := []*pb.Value{}
	cond1077 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1077 {
		_t1922 := p.parse_raw_value()
		item1078 := _t1922
		xs1076 = append(xs1076, item1078)
		cond1077 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1079 := xs1076
	p.consumeLiteral(")")
	_t1923 := &pb.Attribute{Name: name1075, Args: raw_values1079}
	result1081 := _t1923
	p.recordSpan(int(span_start1080), "Attribute")
	return result1081
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1082 := []*pb.RelationId{}
	cond1083 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1083 {
		_t1924 := p.parse_relation_id()
		item1084 := _t1924
		xs1082 = append(xs1082, item1084)
		cond1083 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1085 := xs1082
	_t1925 := p.parse_script()
	script1086 := _t1925
	var _t1926 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1927 := p.parse_attrs()
		_t1926 = _t1927
	}
	attrs1087 := _t1926
	p.consumeLiteral(")")
	_t1928 := attrs1087
	if attrs1087 == nil {
		_t1928 = []*pb.Attribute{}
	}
	_t1929 := &pb.Algorithm{Global: relation_ids1085, Body: script1086, Attrs: _t1928}
	result1089 := _t1929
	p.recordSpan(int(span_start1088), "Algorithm")
	return result1089
}

func (p *Parser) parse_script() *pb.Script {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1090 := []*pb.Construct{}
	cond1091 := p.matchLookaheadLiteral("(", 0)
	for cond1091 {
		_t1930 := p.parse_construct()
		item1092 := _t1930
		xs1090 = append(xs1090, item1092)
		cond1091 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1093 := xs1090
	p.consumeLiteral(")")
	_t1931 := &pb.Script{Constructs: constructs1093}
	result1095 := _t1931
	p.recordSpan(int(span_start1094), "Script")
	return result1095
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1099 := int64(p.spanStart())
	var _t1932 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1933 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1933 = 1
		} else {
			var _t1934 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1934 = 1
			} else {
				var _t1935 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1935 = 1
				} else {
					var _t1936 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1936 = 0
					} else {
						var _t1937 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1937 = 1
						} else {
							var _t1938 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1938 = 1
							} else {
								_t1938 = -1
							}
							_t1937 = _t1938
						}
						_t1936 = _t1937
					}
					_t1935 = _t1936
				}
				_t1934 = _t1935
			}
			_t1933 = _t1934
		}
		_t1932 = _t1933
	} else {
		_t1932 = -1
	}
	prediction1096 := _t1932
	var _t1939 *pb.Construct
	if prediction1096 == 1 {
		_t1940 := p.parse_instruction()
		instruction1098 := _t1940
		_t1941 := &pb.Construct{}
		_t1941.ConstructType = &pb.Construct_Instruction{Instruction: instruction1098}
		_t1939 = _t1941
	} else {
		var _t1942 *pb.Construct
		if prediction1096 == 0 {
			_t1943 := p.parse_loop()
			loop1097 := _t1943
			_t1944 := &pb.Construct{}
			_t1944.ConstructType = &pb.Construct_Loop{Loop: loop1097}
			_t1942 = _t1944
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1939 = _t1942
	}
	result1100 := _t1939
	p.recordSpan(int(span_start1099), "Construct")
	return result1100
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1945 := p.parse_init()
	init1101 := _t1945
	_t1946 := p.parse_script()
	script1102 := _t1946
	var _t1947 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1948 := p.parse_attrs()
		_t1947 = _t1948
	}
	attrs1103 := _t1947
	p.consumeLiteral(")")
	_t1949 := attrs1103
	if attrs1103 == nil {
		_t1949 = []*pb.Attribute{}
	}
	_t1950 := &pb.Loop{Init: init1101, Body: script1102, Attrs: _t1949}
	result1105 := _t1950
	p.recordSpan(int(span_start1104), "Loop")
	return result1105
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1106 := []*pb.Instruction{}
	cond1107 := p.matchLookaheadLiteral("(", 0)
	for cond1107 {
		_t1951 := p.parse_instruction()
		item1108 := _t1951
		xs1106 = append(xs1106, item1108)
		cond1107 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1109 := xs1106
	p.consumeLiteral(")")
	return instructions1109
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1116 := int64(p.spanStart())
	var _t1952 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1953 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1953 = 1
		} else {
			var _t1954 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1954 = 4
			} else {
				var _t1955 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1955 = 3
				} else {
					var _t1956 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1956 = 2
					} else {
						var _t1957 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1957 = 0
						} else {
							_t1957 = -1
						}
						_t1956 = _t1957
					}
					_t1955 = _t1956
				}
				_t1954 = _t1955
			}
			_t1953 = _t1954
		}
		_t1952 = _t1953
	} else {
		_t1952 = -1
	}
	prediction1110 := _t1952
	var _t1958 *pb.Instruction
	if prediction1110 == 4 {
		_t1959 := p.parse_monus_def()
		monus_def1115 := _t1959
		_t1960 := &pb.Instruction{}
		_t1960.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1115}
		_t1958 = _t1960
	} else {
		var _t1961 *pb.Instruction
		if prediction1110 == 3 {
			_t1962 := p.parse_monoid_def()
			monoid_def1114 := _t1962
			_t1963 := &pb.Instruction{}
			_t1963.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1114}
			_t1961 = _t1963
		} else {
			var _t1964 *pb.Instruction
			if prediction1110 == 2 {
				_t1965 := p.parse_break()
				break1113 := _t1965
				_t1966 := &pb.Instruction{}
				_t1966.InstrType = &pb.Instruction_Break{Break: break1113}
				_t1964 = _t1966
			} else {
				var _t1967 *pb.Instruction
				if prediction1110 == 1 {
					_t1968 := p.parse_upsert()
					upsert1112 := _t1968
					_t1969 := &pb.Instruction{}
					_t1969.InstrType = &pb.Instruction_Upsert{Upsert: upsert1112}
					_t1967 = _t1969
				} else {
					var _t1970 *pb.Instruction
					if prediction1110 == 0 {
						_t1971 := p.parse_assign()
						assign1111 := _t1971
						_t1972 := &pb.Instruction{}
						_t1972.InstrType = &pb.Instruction_Assign{Assign: assign1111}
						_t1970 = _t1972
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1967 = _t1970
				}
				_t1964 = _t1967
			}
			_t1961 = _t1964
		}
		_t1958 = _t1961
	}
	result1117 := _t1958
	p.recordSpan(int(span_start1116), "Instruction")
	return result1117
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1973 := p.parse_relation_id()
	relation_id1118 := _t1973
	_t1974 := p.parse_abstraction()
	abstraction1119 := _t1974
	var _t1975 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1976 := p.parse_attrs()
		_t1975 = _t1976
	}
	attrs1120 := _t1975
	p.consumeLiteral(")")
	_t1977 := attrs1120
	if attrs1120 == nil {
		_t1977 = []*pb.Attribute{}
	}
	_t1978 := &pb.Assign{Name: relation_id1118, Body: abstraction1119, Attrs: _t1977}
	result1122 := _t1978
	p.recordSpan(int(span_start1121), "Assign")
	return result1122
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1126 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1979 := p.parse_relation_id()
	relation_id1123 := _t1979
	_t1980 := p.parse_abstraction_with_arity()
	abstraction_with_arity1124 := _t1980
	var _t1981 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1982 := p.parse_attrs()
		_t1981 = _t1982
	}
	attrs1125 := _t1981
	p.consumeLiteral(")")
	_t1983 := attrs1125
	if attrs1125 == nil {
		_t1983 = []*pb.Attribute{}
	}
	_t1984 := &pb.Upsert{Name: relation_id1123, Body: abstraction_with_arity1124[0].(*pb.Abstraction), Attrs: _t1983, ValueArity: abstraction_with_arity1124[1].(int64)}
	result1127 := _t1984
	p.recordSpan(int(span_start1126), "Upsert")
	return result1127
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1985 := p.parse_bindings()
	bindings1128 := _t1985
	_t1986 := p.parse_formula()
	formula1129 := _t1986
	p.consumeLiteral(")")
	_t1987 := &pb.Abstraction{Vars: listConcat(bindings1128[0].([]*pb.Binding), bindings1128[1].([]*pb.Binding)), Value: formula1129}
	return []interface{}{_t1987, int64(len(bindings1128[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1133 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1988 := p.parse_relation_id()
	relation_id1130 := _t1988
	_t1989 := p.parse_abstraction()
	abstraction1131 := _t1989
	var _t1990 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1991 := p.parse_attrs()
		_t1990 = _t1991
	}
	attrs1132 := _t1990
	p.consumeLiteral(")")
	_t1992 := attrs1132
	if attrs1132 == nil {
		_t1992 = []*pb.Attribute{}
	}
	_t1993 := &pb.Break{Name: relation_id1130, Body: abstraction1131, Attrs: _t1992}
	result1134 := _t1993
	p.recordSpan(int(span_start1133), "Break")
	return result1134
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1139 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1994 := p.parse_monoid()
	monoid1135 := _t1994
	_t1995 := p.parse_relation_id()
	relation_id1136 := _t1995
	_t1996 := p.parse_abstraction_with_arity()
	abstraction_with_arity1137 := _t1996
	var _t1997 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1998 := p.parse_attrs()
		_t1997 = _t1998
	}
	attrs1138 := _t1997
	p.consumeLiteral(")")
	_t1999 := attrs1138
	if attrs1138 == nil {
		_t1999 = []*pb.Attribute{}
	}
	_t2000 := &pb.MonoidDef{Monoid: monoid1135, Name: relation_id1136, Body: abstraction_with_arity1137[0].(*pb.Abstraction), Attrs: _t1999, ValueArity: abstraction_with_arity1137[1].(int64)}
	result1140 := _t2000
	p.recordSpan(int(span_start1139), "MonoidDef")
	return result1140
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1146 := int64(p.spanStart())
	var _t2001 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2002 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t2002 = 3
		} else {
			var _t2003 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t2003 = 0
			} else {
				var _t2004 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t2004 = 1
				} else {
					var _t2005 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t2005 = 2
					} else {
						_t2005 = -1
					}
					_t2004 = _t2005
				}
				_t2003 = _t2004
			}
			_t2002 = _t2003
		}
		_t2001 = _t2002
	} else {
		_t2001 = -1
	}
	prediction1141 := _t2001
	var _t2006 *pb.Monoid
	if prediction1141 == 3 {
		_t2007 := p.parse_sum_monoid()
		sum_monoid1145 := _t2007
		_t2008 := &pb.Monoid{}
		_t2008.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1145}
		_t2006 = _t2008
	} else {
		var _t2009 *pb.Monoid
		if prediction1141 == 2 {
			_t2010 := p.parse_max_monoid()
			max_monoid1144 := _t2010
			_t2011 := &pb.Monoid{}
			_t2011.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1144}
			_t2009 = _t2011
		} else {
			var _t2012 *pb.Monoid
			if prediction1141 == 1 {
				_t2013 := p.parse_min_monoid()
				min_monoid1143 := _t2013
				_t2014 := &pb.Monoid{}
				_t2014.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1143}
				_t2012 = _t2014
			} else {
				var _t2015 *pb.Monoid
				if prediction1141 == 0 {
					_t2016 := p.parse_or_monoid()
					or_monoid1142 := _t2016
					_t2017 := &pb.Monoid{}
					_t2017.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1142}
					_t2015 = _t2017
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2012 = _t2015
			}
			_t2009 = _t2012
		}
		_t2006 = _t2009
	}
	result1147 := _t2006
	p.recordSpan(int(span_start1146), "Monoid")
	return result1147
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1148 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t2018 := &pb.OrMonoid{}
	result1149 := _t2018
	p.recordSpan(int(span_start1148), "OrMonoid")
	return result1149
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1151 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t2019 := p.parse_type()
	type1150 := _t2019
	p.consumeLiteral(")")
	_t2020 := &pb.MinMonoid{Type: type1150}
	result1152 := _t2020
	p.recordSpan(int(span_start1151), "MinMonoid")
	return result1152
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1154 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t2021 := p.parse_type()
	type1153 := _t2021
	p.consumeLiteral(")")
	_t2022 := &pb.MaxMonoid{Type: type1153}
	result1155 := _t2022
	p.recordSpan(int(span_start1154), "MaxMonoid")
	return result1155
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t2023 := p.parse_type()
	type1156 := _t2023
	p.consumeLiteral(")")
	_t2024 := &pb.SumMonoid{Type: type1156}
	result1158 := _t2024
	p.recordSpan(int(span_start1157), "SumMonoid")
	return result1158
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1163 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t2025 := p.parse_monoid()
	monoid1159 := _t2025
	_t2026 := p.parse_relation_id()
	relation_id1160 := _t2026
	_t2027 := p.parse_abstraction_with_arity()
	abstraction_with_arity1161 := _t2027
	var _t2028 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2029 := p.parse_attrs()
		_t2028 = _t2029
	}
	attrs1162 := _t2028
	p.consumeLiteral(")")
	_t2030 := attrs1162
	if attrs1162 == nil {
		_t2030 = []*pb.Attribute{}
	}
	_t2031 := &pb.MonusDef{Monoid: monoid1159, Name: relation_id1160, Body: abstraction_with_arity1161[0].(*pb.Abstraction), Attrs: _t2030, ValueArity: abstraction_with_arity1161[1].(int64)}
	result1164 := _t2031
	p.recordSpan(int(span_start1163), "MonusDef")
	return result1164
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1169 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2032 := p.parse_relation_id()
	relation_id1165 := _t2032
	_t2033 := p.parse_abstraction()
	abstraction1166 := _t2033
	_t2034 := p.parse_functional_dependency_keys()
	functional_dependency_keys1167 := _t2034
	_t2035 := p.parse_functional_dependency_values()
	functional_dependency_values1168 := _t2035
	p.consumeLiteral(")")
	_t2036 := &pb.FunctionalDependency{Guard: abstraction1166, Keys: functional_dependency_keys1167, Values: functional_dependency_values1168}
	_t2037 := &pb.Constraint{Name: relation_id1165}
	_t2037.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2036}
	result1170 := _t2037
	p.recordSpan(int(span_start1169), "Constraint")
	return result1170
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1171 := []*pb.Var{}
	cond1172 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1172 {
		_t2038 := p.parse_var()
		item1173 := _t2038
		xs1171 = append(xs1171, item1173)
		cond1172 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1174 := xs1171
	p.consumeLiteral(")")
	return vars1174
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1175 := []*pb.Var{}
	cond1176 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1176 {
		_t2039 := p.parse_var()
		item1177 := _t2039
		xs1175 = append(xs1175, item1177)
		cond1176 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1178 := xs1175
	p.consumeLiteral(")")
	return vars1178
}

func (p *Parser) parse_data() *pb.Data {
	span_start1184 := int64(p.spanStart())
	var _t2040 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2041 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2041 = 3
		} else {
			var _t2042 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2042 = 0
			} else {
				var _t2043 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2043 = 2
				} else {
					var _t2044 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2044 = 1
					} else {
						_t2044 = -1
					}
					_t2043 = _t2044
				}
				_t2042 = _t2043
			}
			_t2041 = _t2042
		}
		_t2040 = _t2041
	} else {
		_t2040 = -1
	}
	prediction1179 := _t2040
	var _t2045 *pb.Data
	if prediction1179 == 3 {
		_t2046 := p.parse_iceberg_data()
		iceberg_data1183 := _t2046
		_t2047 := &pb.Data{}
		_t2047.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1183}
		_t2045 = _t2047
	} else {
		var _t2048 *pb.Data
		if prediction1179 == 2 {
			_t2049 := p.parse_csv_data()
			csv_data1182 := _t2049
			_t2050 := &pb.Data{}
			_t2050.DataType = &pb.Data_CsvData{CsvData: csv_data1182}
			_t2048 = _t2050
		} else {
			var _t2051 *pb.Data
			if prediction1179 == 1 {
				_t2052 := p.parse_betree_relation()
				betree_relation1181 := _t2052
				_t2053 := &pb.Data{}
				_t2053.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1181}
				_t2051 = _t2053
			} else {
				var _t2054 *pb.Data
				if prediction1179 == 0 {
					_t2055 := p.parse_edb()
					edb1180 := _t2055
					_t2056 := &pb.Data{}
					_t2056.DataType = &pb.Data_Edb{Edb: edb1180}
					_t2054 = _t2056
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2051 = _t2054
			}
			_t2048 = _t2051
		}
		_t2045 = _t2048
	}
	result1185 := _t2045
	p.recordSpan(int(span_start1184), "Data")
	return result1185
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2057 := p.parse_relation_id()
	relation_id1186 := _t2057
	_t2058 := p.parse_edb_path()
	edb_path1187 := _t2058
	_t2059 := p.parse_edb_types()
	edb_types1188 := _t2059
	p.consumeLiteral(")")
	_t2060 := &pb.EDB{TargetId: relation_id1186, Path: edb_path1187, Types: edb_types1188}
	result1190 := _t2060
	p.recordSpan(int(span_start1189), "EDB")
	return result1190
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1191 := []string{}
	cond1192 := p.matchLookaheadTerminal("STRING", 0)
	for cond1192 {
		item1193 := p.consumeTerminal("STRING").Value.str
		xs1191 = append(xs1191, item1193)
		cond1192 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1194 := xs1191
	p.consumeLiteral("]")
	return strings1194
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1195 := []*pb.Type{}
	cond1196 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1196 {
		_t2061 := p.parse_type()
		item1197 := _t2061
		xs1195 = append(xs1195, item1197)
		cond1196 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1198 := xs1195
	p.consumeLiteral("]")
	return types1198
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1201 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2062 := p.parse_relation_id()
	relation_id1199 := _t2062
	_t2063 := p.parse_betree_info()
	betree_info1200 := _t2063
	p.consumeLiteral(")")
	_t2064 := &pb.BeTreeRelation{Name: relation_id1199, RelationInfo: betree_info1200}
	result1202 := _t2064
	p.recordSpan(int(span_start1201), "BeTreeRelation")
	return result1202
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1206 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2065 := p.parse_betree_info_key_types()
	betree_info_key_types1203 := _t2065
	_t2066 := p.parse_betree_info_value_types()
	betree_info_value_types1204 := _t2066
	_t2067 := p.parse_config_dict()
	config_dict1205 := _t2067
	p.consumeLiteral(")")
	_t2068 := p.construct_betree_info(betree_info_key_types1203, betree_info_value_types1204, config_dict1205)
	result1207 := _t2068
	p.recordSpan(int(span_start1206), "BeTreeInfo")
	return result1207
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1208 := []*pb.Type{}
	cond1209 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1209 {
		_t2069 := p.parse_type()
		item1210 := _t2069
		xs1208 = append(xs1208, item1210)
		cond1209 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1211 := xs1208
	p.consumeLiteral(")")
	return types1211
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1212 := []*pb.Type{}
	cond1213 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1213 {
		_t2070 := p.parse_type()
		item1214 := _t2070
		xs1212 = append(xs1212, item1214)
		cond1213 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1215 := xs1212
	p.consumeLiteral(")")
	return types1215
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1221 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2071 := p.parse_csvlocator()
	csvlocator1216 := _t2071
	_t2072 := p.parse_csv_config()
	csv_config1217 := _t2072
	var _t2073 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2074 := p.parse_gnf_columns()
		_t2073 = _t2074
	}
	gnf_columns1218 := _t2073
	var _t2075 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2076 := p.parse_target_relations()
		_t2075 = _t2076
	}
	target_relations1219 := _t2075
	_t2077 := p.parse_csv_asof()
	csv_asof1220 := _t2077
	p.consumeLiteral(")")
	_t2078 := p.construct_csv_data(csvlocator1216, csv_config1217, gnf_columns1218, target_relations1219, csv_asof1220)
	result1222 := _t2078
	p.recordSpan(int(span_start1221), "CSVData")
	return result1222
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1225 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2079 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2080 := p.parse_csv_locator_paths()
		_t2079 = _t2080
	}
	csv_locator_paths1223 := _t2079
	var _t2081 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2082 := p.parse_csv_locator_inline_data()
		_t2081 = ptr(_t2082)
	}
	csv_locator_inline_data1224 := _t2081
	p.consumeLiteral(")")
	_t2083 := csv_locator_paths1223
	if csv_locator_paths1223 == nil {
		_t2083 = []string{}
	}
	_t2084 := &pb.CSVLocator{Paths: _t2083, InlineData: []byte(deref(csv_locator_inline_data1224, ""))}
	result1226 := _t2084
	p.recordSpan(int(span_start1225), "CSVLocator")
	return result1226
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1227 := []string{}
	cond1228 := p.matchLookaheadTerminal("STRING", 0)
	for cond1228 {
		item1229 := p.consumeTerminal("STRING").Value.str
		xs1227 = append(xs1227, item1229)
		cond1228 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1230 := xs1227
	p.consumeLiteral(")")
	return strings1230
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1231 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1231
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1234 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2085 := p.parse_config_dict()
	config_dict1232 := _t2085
	var _t2086 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2087 := p.parse__storage_integration()
		_t2086 = _t2087
	}
	_storage_integration1233 := _t2086
	p.consumeLiteral(")")
	_t2088 := p.construct_csv_config(config_dict1232, _storage_integration1233)
	result1235 := _t2088
	p.recordSpan(int(span_start1234), "CSVConfig")
	return result1235
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2089 := p.parse_config_dict()
	config_dict1236 := _t2089
	p.consumeLiteral(")")
	return config_dict1236
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1237 := []*pb.GNFColumn{}
	cond1238 := p.matchLookaheadLiteral("(", 0)
	for cond1238 {
		_t2090 := p.parse_gnf_column()
		item1239 := _t2090
		xs1237 = append(xs1237, item1239)
		cond1238 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1240 := xs1237
	p.consumeLiteral(")")
	return gnf_columns1240
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1247 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2091 := p.parse_gnf_column_path()
	gnf_column_path1241 := _t2091
	var _t2092 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2093 := p.parse_relation_id()
		_t2092 = _t2093
	}
	relation_id1242 := _t2092
	p.consumeLiteral("[")
	xs1243 := []*pb.Type{}
	cond1244 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1244 {
		_t2094 := p.parse_type()
		item1245 := _t2094
		xs1243 = append(xs1243, item1245)
		cond1244 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1246 := xs1243
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2095 := &pb.GNFColumn{ColumnPath: gnf_column_path1241, TargetId: relation_id1242, Types: types1246}
	result1248 := _t2095
	p.recordSpan(int(span_start1247), "GNFColumn")
	return result1248
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2096 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2096 = 1
	} else {
		var _t2097 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2097 = 0
		} else {
			_t2097 = -1
		}
		_t2096 = _t2097
	}
	prediction1249 := _t2096
	var _t2098 []string
	if prediction1249 == 1 {
		p.consumeLiteral("[")
		xs1251 := []string{}
		cond1252 := p.matchLookaheadTerminal("STRING", 0)
		for cond1252 {
			item1253 := p.consumeTerminal("STRING").Value.str
			xs1251 = append(xs1251, item1253)
			cond1252 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1254 := xs1251
		p.consumeLiteral("]")
		_t2098 = strings1254
	} else {
		var _t2099 []string
		if prediction1249 == 0 {
			string1250 := p.consumeTerminal("STRING").Value.str
			_ = string1250
			_t2099 = []string{string1250}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2098 = _t2099
	}
	return _t2098
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1258 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2100 := p.parse_relation_keys()
	relation_keys1255 := _t2100
	_t2101 := p.parse_relation_body()
	relation_body1256 := _t2101
	var _t2102 *pb.RelationId
	if p.matchLookaheadLiteral("(", 0) {
		_t2103 := p.parse_load_errors()
		_t2102 = _t2103
	}
	load_errors1257 := _t2102
	p.consumeLiteral(")")
	_t2104 := p.construct_relations(relation_keys1255, relation_body1256, load_errors1257)
	result1259 := _t2104
	p.recordSpan(int(span_start1258), "TargetRelations")
	return result1259
}

func (p *Parser) parse_relation_keys() []interface{} {
	var _t2105 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2106 int64
		if p.matchLookaheadLiteral("keys", 1) {
			var _t2107 int64
			if p.matchLookaheadLiteral("synthetic", 2) {
				_t2107 = 1
			} else {
				var _t2108 int64
				if p.matchLookaheadLiteral(")", 2) {
					_t2108 = 0
				} else {
					var _t2109 int64
					if p.matchLookaheadLiteral("(", 2) {
						_t2109 = 0
					} else {
						_t2109 = -1
					}
					_t2108 = _t2109
				}
				_t2107 = _t2108
			}
			_t2106 = _t2107
		} else {
			_t2106 = -1
		}
		_t2105 = _t2106
	} else {
		_t2105 = -1
	}
	prediction1260 := _t2105
	var _t2110 []interface{}
	if prediction1260 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("keys")
		p.consumeLiteral("synthetic")
		p.consumeLiteral(")")
		_t2110 = []interface{}{[]*pb.NamedColumn{}, true}
	} else {
		var _t2111 []interface{}
		if prediction1260 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("keys")
			xs1261 := []*pb.NamedColumn{}
			cond1262 := p.matchLookaheadLiteral("(", 0)
			for cond1262 {
				_t2112 := p.parse_named_column()
				item1263 := _t2112
				xs1261 = append(xs1261, item1263)
				cond1262 = p.matchLookaheadLiteral("(", 0)
			}
			named_columns1264 := xs1261
			p.consumeLiteral(")")
			_t2111 = []interface{}{named_columns1264, false}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_keys", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2110 = _t2111
	}
	return _t2110
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1267 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1265 := p.consumeTerminal("STRING").Value.str
	_t2113 := p.parse_type()
	type1266 := _t2113
	p.consumeLiteral(")")
	_t2114 := &pb.NamedColumn{Name: string1265, Type: type1266}
	result1268 := _t2114
	p.recordSpan(int(span_start1267), "NamedColumn")
	return result1268
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1273 := int64(p.spanStart())
	var _t2115 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2116 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2116 = 0
		} else {
			var _t2117 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2117 = 1
			} else {
				_t2117 = 0
			}
			_t2116 = _t2117
		}
		_t2115 = _t2116
	} else {
		_t2115 = 0
	}
	prediction1269 := _t2115
	var _t2118 *pb.TargetRelations
	if prediction1269 == 1 {
		_t2119 := p.parse_cdc_inserts()
		cdc_inserts1271 := _t2119
		_t2120 := p.parse_cdc_deletes()
		cdc_deletes1272 := _t2120
		_t2121 := p.construct_cdc_relations(cdc_inserts1271, cdc_deletes1272)
		_t2118 = _t2121
	} else {
		var _t2122 *pb.TargetRelations
		if prediction1269 == 0 {
			_t2123 := p.parse_non_cdc_relations()
			non_cdc_relations1270 := _t2123
			_t2124 := p.construct_non_cdc_relations(non_cdc_relations1270)
			_t2122 = _t2124
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2118 = _t2122
	}
	result1274 := _t2118
	p.recordSpan(int(span_start1273), "TargetRelations")
	return result1274
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1275 := []*pb.TargetRelation{}
	cond1276 := (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	for cond1276 {
		_t2125 := p.parse_target_relation()
		item1277 := _t2125
		xs1275 = append(xs1275, item1277)
		cond1276 = (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	}
	return xs1275
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1283 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2126 := p.parse_relation_id()
	relation_id1278 := _t2126
	xs1279 := []*pb.NamedColumn{}
	cond1280 := p.matchLookaheadLiteral("(", 0)
	for cond1280 {
		_t2127 := p.parse_named_column()
		item1281 := _t2127
		xs1279 = append(xs1279, item1281)
		cond1280 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1282 := xs1279
	p.consumeLiteral(")")
	_t2128 := &pb.TargetRelation{TargetId: relation_id1278, Values: named_columns1282}
	result1284 := _t2128
	p.recordSpan(int(span_start1283), "TargetRelation")
	return result1284
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1285 := []*pb.TargetRelation{}
	cond1286 := p.matchLookaheadLiteral("(", 0)
	for cond1286 {
		_t2129 := p.parse_target_relation()
		item1287 := _t2129
		xs1285 = append(xs1285, item1287)
		cond1286 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1288 := xs1285
	p.consumeLiteral(")")
	return target_relations1288
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1289 := []*pb.TargetRelation{}
	cond1290 := p.matchLookaheadLiteral("(", 0)
	for cond1290 {
		_t2130 := p.parse_target_relation()
		item1291 := _t2130
		xs1289 = append(xs1289, item1291)
		cond1290 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1292 := xs1289
	p.consumeLiteral(")")
	return target_relations1292
}

func (p *Parser) parse_load_errors() *pb.RelationId {
	span_start1294 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("load_errors")
	_t2131 := p.parse_relation_id()
	relation_id1293 := _t2131
	p.consumeLiteral(")")
	result1295 := relation_id1293
	p.recordSpan(int(span_start1294), "RelationId")
	return result1295
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1296 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1296
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1304 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2132 := p.parse_iceberg_locator()
	iceberg_locator1297 := _t2132
	_t2133 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1298 := _t2133
	var _t2134 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2135 := p.parse_gnf_columns()
		_t2134 = _t2135
	}
	gnf_columns1299 := _t2134
	var _t2136 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2137 := p.parse_target_relations()
		_t2136 = _t2137
	}
	target_relations1300 := _t2136
	var _t2138 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2139 := p.parse_iceberg_from_snapshot()
		_t2138 = ptr(_t2139)
	}
	iceberg_from_snapshot1301 := _t2138
	var _t2140 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2141 := p.parse_iceberg_to_snapshot()
		_t2140 = ptr(_t2141)
	}
	iceberg_to_snapshot1302 := _t2140
	_t2142 := p.parse_boolean_value()
	boolean_value1303 := _t2142
	p.consumeLiteral(")")
	_t2143 := p.construct_iceberg_data(iceberg_locator1297, iceberg_catalog_config1298, gnf_columns1299, target_relations1300, iceberg_from_snapshot1301, iceberg_to_snapshot1302, boolean_value1303)
	result1305 := _t2143
	p.recordSpan(int(span_start1304), "IcebergData")
	return result1305
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1309 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2144 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1306 := _t2144
	_t2145 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1307 := _t2145
	_t2146 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1308 := _t2146
	p.consumeLiteral(")")
	_t2147 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1306, Namespace: iceberg_locator_namespace1307, Warehouse: iceberg_locator_warehouse1308}
	result1310 := _t2147
	p.recordSpan(int(span_start1309), "IcebergLocator")
	return result1310
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1311 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1311
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1312 := []string{}
	cond1313 := p.matchLookaheadTerminal("STRING", 0)
	for cond1313 {
		item1314 := p.consumeTerminal("STRING").Value.str
		xs1312 = append(xs1312, item1314)
		cond1313 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1315 := xs1312
	p.consumeLiteral(")")
	return strings1315
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1316 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1316
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1321 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2148 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1317 := _t2148
	var _t2149 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2150 := p.parse_iceberg_catalog_config_scope()
		_t2149 = ptr(_t2150)
	}
	iceberg_catalog_config_scope1318 := _t2149
	_t2151 := p.parse_iceberg_properties()
	iceberg_properties1319 := _t2151
	_t2152 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1320 := _t2152
	p.consumeLiteral(")")
	_t2153 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1317, iceberg_catalog_config_scope1318, iceberg_properties1319, iceberg_auth_properties1320)
	result1322 := _t2153
	p.recordSpan(int(span_start1321), "IcebergCatalogConfig")
	return result1322
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1323 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1323
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1324 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1324
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1325 := [][]interface{}{}
	cond1326 := p.matchLookaheadLiteral("(", 0)
	for cond1326 {
		_t2154 := p.parse_iceberg_property_entry()
		item1327 := _t2154
		xs1325 = append(xs1325, item1327)
		cond1326 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1328 := xs1325
	p.consumeLiteral(")")
	return iceberg_property_entrys1328
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1329 := p.consumeTerminal("STRING").Value.str
	string_31330 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1329, string_31330}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1331 := [][]interface{}{}
	cond1332 := p.matchLookaheadLiteral("(", 0)
	for cond1332 {
		_t2155 := p.parse_iceberg_masked_property_entry()
		item1333 := _t2155
		xs1331 = append(xs1331, item1333)
		cond1332 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1334 := xs1331
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1334
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1335 := p.consumeTerminal("STRING").Value.str
	string_31336 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1335, string_31336}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1337 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1337
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1338 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1338
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1340 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2156 := p.parse_fragment_id()
	fragment_id1339 := _t2156
	p.consumeLiteral(")")
	_t2157 := &pb.Undefine{FragmentId: fragment_id1339}
	result1341 := _t2157
	p.recordSpan(int(span_start1340), "Undefine")
	return result1341
}

func (p *Parser) parse_context() *pb.Context {
	span_start1346 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1342 := []*pb.RelationId{}
	cond1343 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1343 {
		_t2158 := p.parse_relation_id()
		item1344 := _t2158
		xs1342 = append(xs1342, item1344)
		cond1343 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1345 := xs1342
	p.consumeLiteral(")")
	_t2159 := &pb.Context{Relations: relation_ids1345}
	result1347 := _t2159
	p.recordSpan(int(span_start1346), "Context")
	return result1347
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1353 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2160 := p.parse_edb_path()
	edb_path1348 := _t2160
	xs1349 := []*pb.SnapshotMapping{}
	cond1350 := p.matchLookaheadLiteral("[", 0)
	for cond1350 {
		_t2161 := p.parse_snapshot_mapping()
		item1351 := _t2161
		xs1349 = append(xs1349, item1351)
		cond1350 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1352 := xs1349
	p.consumeLiteral(")")
	_t2162 := &pb.Snapshot{Prefix: edb_path1348, Mappings: snapshot_mappings1352}
	result1354 := _t2162
	p.recordSpan(int(span_start1353), "Snapshot")
	return result1354
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1357 := int64(p.spanStart())
	_t2163 := p.parse_edb_path()
	edb_path1355 := _t2163
	_t2164 := p.parse_relation_id()
	relation_id1356 := _t2164
	_t2165 := &pb.SnapshotMapping{DestinationPath: edb_path1355, SourceRelation: relation_id1356}
	result1358 := _t2165
	p.recordSpan(int(span_start1357), "SnapshotMapping")
	return result1358
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1359 := []*pb.Read{}
	cond1360 := p.matchLookaheadLiteral("(", 0)
	for cond1360 {
		_t2166 := p.parse_read()
		item1361 := _t2166
		xs1359 = append(xs1359, item1361)
		cond1360 = p.matchLookaheadLiteral("(", 0)
	}
	reads1362 := xs1359
	p.consumeLiteral(")")
	return reads1362
}

func (p *Parser) parse_read() *pb.Read {
	span_start1369 := int64(p.spanStart())
	var _t2167 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2168 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2168 = 2
		} else {
			var _t2169 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2169 = 1
			} else {
				var _t2170 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2170 = 4
				} else {
					var _t2171 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2171 = 4
					} else {
						var _t2172 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2172 = 0
						} else {
							var _t2173 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2173 = 3
							} else {
								_t2173 = -1
							}
							_t2172 = _t2173
						}
						_t2171 = _t2172
					}
					_t2170 = _t2171
				}
				_t2169 = _t2170
			}
			_t2168 = _t2169
		}
		_t2167 = _t2168
	} else {
		_t2167 = -1
	}
	prediction1363 := _t2167
	var _t2174 *pb.Read
	if prediction1363 == 4 {
		_t2175 := p.parse_export()
		export1368 := _t2175
		_t2176 := &pb.Read{}
		_t2176.ReadType = &pb.Read_Export{Export: export1368}
		_t2174 = _t2176
	} else {
		var _t2177 *pb.Read
		if prediction1363 == 3 {
			_t2178 := p.parse_abort()
			abort1367 := _t2178
			_t2179 := &pb.Read{}
			_t2179.ReadType = &pb.Read_Abort{Abort: abort1367}
			_t2177 = _t2179
		} else {
			var _t2180 *pb.Read
			if prediction1363 == 2 {
				_t2181 := p.parse_what_if()
				what_if1366 := _t2181
				_t2182 := &pb.Read{}
				_t2182.ReadType = &pb.Read_WhatIf{WhatIf: what_if1366}
				_t2180 = _t2182
			} else {
				var _t2183 *pb.Read
				if prediction1363 == 1 {
					_t2184 := p.parse_output()
					output1365 := _t2184
					_t2185 := &pb.Read{}
					_t2185.ReadType = &pb.Read_Output{Output: output1365}
					_t2183 = _t2185
				} else {
					var _t2186 *pb.Read
					if prediction1363 == 0 {
						_t2187 := p.parse_demand()
						demand1364 := _t2187
						_t2188 := &pb.Read{}
						_t2188.ReadType = &pb.Read_Demand{Demand: demand1364}
						_t2186 = _t2188
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2183 = _t2186
				}
				_t2180 = _t2183
			}
			_t2177 = _t2180
		}
		_t2174 = _t2177
	}
	result1370 := _t2174
	p.recordSpan(int(span_start1369), "Read")
	return result1370
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1372 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2189 := p.parse_relation_id()
	relation_id1371 := _t2189
	p.consumeLiteral(")")
	_t2190 := &pb.Demand{RelationId: relation_id1371}
	result1373 := _t2190
	p.recordSpan(int(span_start1372), "Demand")
	return result1373
}

func (p *Parser) parse_output() *pb.Output {
	span_start1376 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2191 := p.parse_name()
	name1374 := _t2191
	_t2192 := p.parse_relation_id()
	relation_id1375 := _t2192
	p.consumeLiteral(")")
	_t2193 := &pb.Output{Name: name1374, RelationId: relation_id1375}
	result1377 := _t2193
	p.recordSpan(int(span_start1376), "Output")
	return result1377
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1380 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2194 := p.parse_name()
	name1378 := _t2194
	_t2195 := p.parse_epoch()
	epoch1379 := _t2195
	p.consumeLiteral(")")
	_t2196 := &pb.WhatIf{Branch: name1378, Epoch: epoch1379}
	result1381 := _t2196
	p.recordSpan(int(span_start1380), "WhatIf")
	return result1381
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1384 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2197 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2198 := p.parse_name()
		_t2197 = ptr(_t2198)
	}
	name1382 := _t2197
	_t2199 := p.parse_relation_id()
	relation_id1383 := _t2199
	p.consumeLiteral(")")
	_t2200 := &pb.Abort{Name: deref(name1382, "abort"), RelationId: relation_id1383}
	result1385 := _t2200
	p.recordSpan(int(span_start1384), "Abort")
	return result1385
}

func (p *Parser) parse_export() *pb.Export {
	span_start1389 := int64(p.spanStart())
	var _t2201 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2202 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2202 = 1
		} else {
			var _t2203 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2203 = 0
			} else {
				_t2203 = -1
			}
			_t2202 = _t2203
		}
		_t2201 = _t2202
	} else {
		_t2201 = -1
	}
	prediction1386 := _t2201
	var _t2204 *pb.Export
	if prediction1386 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2205 := p.parse_export_iceberg_config()
		export_iceberg_config1388 := _t2205
		p.consumeLiteral(")")
		_t2206 := &pb.Export{}
		_t2206.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1388}
		_t2204 = _t2206
	} else {
		var _t2207 *pb.Export
		if prediction1386 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2208 := p.parse_export_csv_config()
			export_csv_config1387 := _t2208
			p.consumeLiteral(")")
			_t2209 := &pb.Export{}
			_t2209.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1387}
			_t2207 = _t2209
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2204 = _t2207
	}
	result1390 := _t2204
	p.recordSpan(int(span_start1389), "Export")
	return result1390
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1398 := int64(p.spanStart())
	var _t2210 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2211 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2211 = 0
		} else {
			var _t2212 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2212 = 1
			} else {
				_t2212 = -1
			}
			_t2211 = _t2212
		}
		_t2210 = _t2211
	} else {
		_t2210 = -1
	}
	prediction1391 := _t2210
	var _t2213 *pb.ExportCSVConfig
	if prediction1391 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2214 := p.parse_export_csv_path()
		export_csv_path1395 := _t2214
		_t2215 := p.parse_export_csv_columns_list()
		export_csv_columns_list1396 := _t2215
		_t2216 := p.parse_config_dict()
		config_dict1397 := _t2216
		p.consumeLiteral(")")
		_t2217 := p.construct_export_csv_config(export_csv_path1395, export_csv_columns_list1396, config_dict1397)
		_t2213 = _t2217
	} else {
		var _t2218 *pb.ExportCSVConfig
		if prediction1391 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2219 := p.parse_export_csv_output_location()
			export_csv_output_location1392 := _t2219
			_t2220 := p.parse_export_csv_source()
			export_csv_source1393 := _t2220
			_t2221 := p.parse_csv_config()
			csv_config1394 := _t2221
			p.consumeLiteral(")")
			_t2222 := p.construct_export_csv_config_with_location(export_csv_output_location1392, export_csv_source1393, csv_config1394)
			_t2218 = _t2222
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2213 = _t2218
	}
	result1399 := _t2213
	p.recordSpan(int(span_start1398), "ExportCSVConfig")
	return result1399
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2223 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2224 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2224 = 1
		} else {
			var _t2225 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2225 = 0
			} else {
				_t2225 = -1
			}
			_t2224 = _t2225
		}
		_t2223 = _t2224
	} else {
		_t2223 = -1
	}
	prediction1400 := _t2223
	var _t2226 []interface{}
	if prediction1400 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2227 := p.parse_name()
		name1402 := _t2227
		p.consumeLiteral(")")
		_t2226 = []interface{}{"", name1402}
	} else {
		var _t2228 []interface{}
		if prediction1400 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1401 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2228 = []interface{}{string1401, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2226 = _t2228
	}
	return _t2226
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1409 := int64(p.spanStart())
	var _t2229 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2230 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2230 = 1
		} else {
			var _t2231 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2231 = 0
			} else {
				_t2231 = -1
			}
			_t2230 = _t2231
		}
		_t2229 = _t2230
	} else {
		_t2229 = -1
	}
	prediction1403 := _t2229
	var _t2232 *pb.ExportCSVSource
	if prediction1403 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2233 := p.parse_relation_id()
		relation_id1408 := _t2233
		p.consumeLiteral(")")
		_t2234 := &pb.ExportCSVSource{}
		_t2234.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1408}
		_t2232 = _t2234
	} else {
		var _t2235 *pb.ExportCSVSource
		if prediction1403 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1404 := []*pb.ExportCSVColumn{}
			cond1405 := p.matchLookaheadLiteral("(", 0)
			for cond1405 {
				_t2236 := p.parse_export_csv_column()
				item1406 := _t2236
				xs1404 = append(xs1404, item1406)
				cond1405 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1407 := xs1404
			p.consumeLiteral(")")
			_t2237 := &pb.ExportCSVColumns{Columns: export_csv_columns1407}
			_t2238 := &pb.ExportCSVSource{}
			_t2238.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2237}
			_t2235 = _t2238
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2232 = _t2235
	}
	result1410 := _t2232
	p.recordSpan(int(span_start1409), "ExportCSVSource")
	return result1410
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1413 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1411 := p.consumeTerminal("STRING").Value.str
	_t2239 := p.parse_relation_id()
	relation_id1412 := _t2239
	p.consumeLiteral(")")
	_t2240 := &pb.ExportCSVColumn{ColumnName: string1411, ColumnData: relation_id1412}
	result1414 := _t2240
	p.recordSpan(int(span_start1413), "ExportCSVColumn")
	return result1414
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1415 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1415
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1416 := []*pb.ExportCSVColumn{}
	cond1417 := p.matchLookaheadLiteral("(", 0)
	for cond1417 {
		_t2241 := p.parse_export_csv_column()
		item1418 := _t2241
		xs1416 = append(xs1416, item1418)
		cond1417 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1419 := xs1416
	p.consumeLiteral(")")
	return export_csv_columns1419
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1425 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2242 := p.parse_iceberg_locator()
	iceberg_locator1420 := _t2242
	_t2243 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1421 := _t2243
	_t2244 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1422 := _t2244
	_t2245 := p.parse_iceberg_table_properties()
	iceberg_table_properties1423 := _t2245
	var _t2246 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2247 := p.parse_config_dict()
		_t2246 = _t2247
	}
	config_dict1424 := _t2246
	p.consumeLiteral(")")
	_t2248 := p.construct_export_iceberg_config_full(iceberg_locator1420, iceberg_catalog_config1421, export_iceberg_table_def1422, iceberg_table_properties1423, config_dict1424)
	result1426 := _t2248
	p.recordSpan(int(span_start1425), "ExportIcebergConfig")
	return result1426
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1428 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2249 := p.parse_relation_id()
	relation_id1427 := _t2249
	p.consumeLiteral(")")
	result1429 := relation_id1427
	p.recordSpan(int(span_start1428), "RelationId")
	return result1429
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1430 := [][]interface{}{}
	cond1431 := p.matchLookaheadLiteral("(", 0)
	for cond1431 {
		_t2250 := p.parse_iceberg_property_entry()
		item1432 := _t2250
		xs1430 = append(xs1430, item1432)
		cond1431 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1433 := xs1430
	p.consumeLiteral(")")
	return iceberg_property_entrys1433
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
