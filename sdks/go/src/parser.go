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
	var _t2232 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2232
	var _t2233 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2233
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2234 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2234
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2235 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2235
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2236 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2236
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2237 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2237
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2238 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2238
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2239 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2239
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2240 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2240
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2241 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2241
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2242 := &pb.PlainTargets{Targets: targets}
	_t2243 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2243.Body = &pb.TargetRelations_Plain{Plain: _t2242}
	return _t2243
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2244 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2245 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2245.Body = &pb.TargetRelations_Cdc{Cdc: _t2244}
	return _t2245
}

func (p *Parser) construct_relations(keys []interface{}, body *pb.TargetRelations, load_errors_opt *pb.RelationId) *pb.TargetRelations {
	var _t2246 interface{}
	if hasProtoField(body, "plain") {
		_t2247 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
		_t2247.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2247
	}
	_ = _t2246
	_t2248 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
	_t2248.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2248
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2249 := columns_opt
	if columns_opt == nil {
		_t2249 = []*pb.GNFColumn{}
	}
	_t2250 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2249, Asof: asof, Relations: relations_opt}
	return _t2250
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2251 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2251
	_t2252 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2252
	_t2253 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2253
	_t2254 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2254
	_t2255 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2255
	_t2256 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2256
	_t2257 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2257
	_t2258 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2258
	_t2259 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2259
	_t2260 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2260
	_t2261 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2261
	_t2262 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2262
	_t2263 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2263
	_t2264 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2264
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2265 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2265
	config := dictFromList(storage_integration_opt)
	_t2266 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2267 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2268 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2269 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2270 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2271 := &pb.StorageIntegration{Provider: _t2266, AzureSasToken: _t2267, S3Region: _t2268, S3AccessKeyId: _t2269, S3SecretAccessKey: _t2270}
	return _t2271
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2272 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2272
	_t2273 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2273
	_t2274 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2274
	_t2275 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2275
	_t2276 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2276
	_t2277 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2277
	_t2278 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2278
	_t2279 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2279
	_t2280 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2280
	_t2281 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2281.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2281.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2281
	_t2282 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2282
}

func (p *Parser) default_configure() *pb.Configure {
	_t2283 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2283
	_t2284 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2284
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
	_t2285 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2285
	_t2286 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2286
	config_values_pairs := [][]interface{}{}
	for _, pair := range config_dict {
		if (pair[0].(string) != "semantics_version" && pair[0].(string) != "ivm.maintenance_level") {
			config_values_pairs = append(config_values_pairs, pair)
		}
	}
	configuration_values := valueMapFromPairs(config_values_pairs)
	_t2287 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config, ConfigurationValues: configuration_values}
	return _t2287
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2288 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2288
	_t2289 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2289
	_t2290 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2290
	_t2291 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2291
	_t2292 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2292
	_t2293 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2293
	_t2294 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2294
	_t2295 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2295
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2296 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2296
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2297 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2297
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2298 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2298
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2299 := config_dict
	if config_dict == nil {
		_t2299 = [][]interface{}{}
	}
	cfg := dictFromList(_t2299)
	_t2300 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2300
	_t2301 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2301
	_t2302 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2302
	table_props := stringMapFromPairs(table_property_pairs)
	_t2303 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2303
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start718 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1424 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1425 := p.parse_configure()
		_t1424 = _t1425
	}
	configure712 := _t1424
	var _t1426 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1427 := p.parse_sync()
		_t1426 = _t1427
	}
	sync713 := _t1426
	xs714 := []*pb.Epoch{}
	cond715 := p.matchLookaheadLiteral("(", 0)
	for cond715 {
		_t1428 := p.parse_epoch()
		item716 := _t1428
		xs714 = append(xs714, item716)
		cond715 = p.matchLookaheadLiteral("(", 0)
	}
	epochs717 := xs714
	p.consumeLiteral(")")
	_t1429 := p.default_configure()
	_t1430 := configure712
	if configure712 == nil {
		_t1430 = _t1429
	}
	_t1431 := &pb.Transaction{Epochs: epochs717, Configure: _t1430, Sync: sync713}
	result719 := _t1431
	p.recordSpan(int(span_start718), "Transaction")
	return result719
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start721 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1432 := p.parse_config_dict()
	config_dict720 := _t1432
	p.consumeLiteral(")")
	_t1433 := p.construct_configure(config_dict720)
	result722 := _t1433
	p.recordSpan(int(span_start721), "Configure")
	return result722
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs723 := [][]interface{}{}
	cond724 := p.matchLookaheadLiteral(":", 0)
	for cond724 {
		_t1434 := p.parse_config_key_value()
		item725 := _t1434
		xs723 = append(xs723, item725)
		cond724 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values726 := xs723
	p.consumeLiteral("}")
	return config_key_values726
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol727 := p.consumeTerminal("SYMBOL").Value.str
	_t1435 := p.parse_raw_value()
	raw_value728 := _t1435
	return []interface{}{symbol727, raw_value728}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start742 := int64(p.spanStart())
	var _t1436 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1436 = 12
	} else {
		var _t1437 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1437 = 11
		} else {
			var _t1438 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1438 = 12
			} else {
				var _t1439 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1440 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1440 = 1
					} else {
						var _t1441 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1441 = 0
						} else {
							_t1441 = -1
						}
						_t1440 = _t1441
					}
					_t1439 = _t1440
				} else {
					var _t1442 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1442 = 7
					} else {
						var _t1443 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1443 = 8
						} else {
							var _t1444 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1444 = 2
							} else {
								var _t1445 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1445 = 3
								} else {
									var _t1446 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1446 = 9
									} else {
										var _t1447 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1447 = 4
										} else {
											var _t1448 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1448 = 5
											} else {
												var _t1449 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1449 = 6
												} else {
													var _t1450 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1450 = 10
													} else {
														_t1450 = -1
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
					_t1439 = _t1442
				}
				_t1438 = _t1439
			}
			_t1437 = _t1438
		}
		_t1436 = _t1437
	}
	prediction729 := _t1436
	var _t1451 *pb.Value
	if prediction729 == 12 {
		_t1452 := p.parse_boolean_value()
		boolean_value741 := _t1452
		_t1453 := &pb.Value{}
		_t1453.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value741}
		_t1451 = _t1453
	} else {
		var _t1454 *pb.Value
		if prediction729 == 11 {
			p.consumeLiteral("missing")
			_t1455 := &pb.MissingValue{}
			_t1456 := &pb.Value{}
			_t1456.Value = &pb.Value_MissingValue{MissingValue: _t1455}
			_t1454 = _t1456
		} else {
			var _t1457 *pb.Value
			if prediction729 == 10 {
				decimal740 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1458 := &pb.Value{}
				_t1458.Value = &pb.Value_DecimalValue{DecimalValue: decimal740}
				_t1457 = _t1458
			} else {
				var _t1459 *pb.Value
				if prediction729 == 9 {
					int128739 := p.consumeTerminal("INT128").Value.int128
					_t1460 := &pb.Value{}
					_t1460.Value = &pb.Value_Int128Value{Int128Value: int128739}
					_t1459 = _t1460
				} else {
					var _t1461 *pb.Value
					if prediction729 == 8 {
						uint128738 := p.consumeTerminal("UINT128").Value.uint128
						_t1462 := &pb.Value{}
						_t1462.Value = &pb.Value_Uint128Value{Uint128Value: uint128738}
						_t1461 = _t1462
					} else {
						var _t1463 *pb.Value
						if prediction729 == 7 {
							uint32737 := p.consumeTerminal("UINT32").Value.u32
							_t1464 := &pb.Value{}
							_t1464.Value = &pb.Value_Uint32Value{Uint32Value: uint32737}
							_t1463 = _t1464
						} else {
							var _t1465 *pb.Value
							if prediction729 == 6 {
								float736 := p.consumeTerminal("FLOAT").Value.f64
								_t1466 := &pb.Value{}
								_t1466.Value = &pb.Value_FloatValue{FloatValue: float736}
								_t1465 = _t1466
							} else {
								var _t1467 *pb.Value
								if prediction729 == 5 {
									float32735 := p.consumeTerminal("FLOAT32").Value.f32
									_t1468 := &pb.Value{}
									_t1468.Value = &pb.Value_Float32Value{Float32Value: float32735}
									_t1467 = _t1468
								} else {
									var _t1469 *pb.Value
									if prediction729 == 4 {
										int734 := p.consumeTerminal("INT").Value.i64
										_t1470 := &pb.Value{}
										_t1470.Value = &pb.Value_IntValue{IntValue: int734}
										_t1469 = _t1470
									} else {
										var _t1471 *pb.Value
										if prediction729 == 3 {
											int32733 := p.consumeTerminal("INT32").Value.i32
											_t1472 := &pb.Value{}
											_t1472.Value = &pb.Value_Int32Value{Int32Value: int32733}
											_t1471 = _t1472
										} else {
											var _t1473 *pb.Value
											if prediction729 == 2 {
												string732 := p.consumeTerminal("STRING").Value.str
												_t1474 := &pb.Value{}
												_t1474.Value = &pb.Value_StringValue{StringValue: string732}
												_t1473 = _t1474
											} else {
												var _t1475 *pb.Value
												if prediction729 == 1 {
													_t1476 := p.parse_raw_datetime()
													raw_datetime731 := _t1476
													_t1477 := &pb.Value{}
													_t1477.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime731}
													_t1475 = _t1477
												} else {
													var _t1478 *pb.Value
													if prediction729 == 0 {
														_t1479 := p.parse_raw_date()
														raw_date730 := _t1479
														_t1480 := &pb.Value{}
														_t1480.Value = &pb.Value_DateValue{DateValue: raw_date730}
														_t1478 = _t1480
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1475 = _t1478
												}
												_t1473 = _t1475
											}
											_t1471 = _t1473
										}
										_t1469 = _t1471
									}
									_t1467 = _t1469
								}
								_t1465 = _t1467
							}
							_t1463 = _t1465
						}
						_t1461 = _t1463
					}
					_t1459 = _t1461
				}
				_t1457 = _t1459
			}
			_t1454 = _t1457
		}
		_t1451 = _t1454
	}
	result743 := _t1451
	p.recordSpan(int(span_start742), "Value")
	return result743
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int744 := p.consumeTerminal("INT").Value.i64
	int_3745 := p.consumeTerminal("INT").Value.i64
	int_4746 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1481 := &pb.DateValue{Year: int32(int744), Month: int32(int_3745), Day: int32(int_4746)}
	result748 := _t1481
	p.recordSpan(int(span_start747), "DateValue")
	return result748
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start756 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int749 := p.consumeTerminal("INT").Value.i64
	int_3750 := p.consumeTerminal("INT").Value.i64
	int_4751 := p.consumeTerminal("INT").Value.i64
	int_5752 := p.consumeTerminal("INT").Value.i64
	int_6753 := p.consumeTerminal("INT").Value.i64
	int_7754 := p.consumeTerminal("INT").Value.i64
	var _t1482 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1482 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8755 := _t1482
	p.consumeLiteral(")")
	_t1483 := &pb.DateTimeValue{Year: int32(int749), Month: int32(int_3750), Day: int32(int_4751), Hour: int32(int_5752), Minute: int32(int_6753), Second: int32(int_7754), Microsecond: int32(deref(int_8755, 0))}
	result757 := _t1483
	p.recordSpan(int(span_start756), "DateTimeValue")
	return result757
}

func (p *Parser) parse_boolean_value() bool {
	var _t1484 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1484 = 0
	} else {
		var _t1485 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1485 = 1
		} else {
			_t1485 = -1
		}
		_t1484 = _t1485
	}
	prediction758 := _t1484
	var _t1486 bool
	if prediction758 == 1 {
		p.consumeLiteral("false")
		_t1486 = false
	} else {
		var _t1487 bool
		if prediction758 == 0 {
			p.consumeLiteral("true")
			_t1487 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1486 = _t1487
	}
	return _t1486
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs759 := []*pb.FragmentId{}
	cond760 := p.matchLookaheadLiteral(":", 0)
	for cond760 {
		_t1488 := p.parse_fragment_id()
		item761 := _t1488
		xs759 = append(xs759, item761)
		cond760 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids762 := xs759
	p.consumeLiteral(")")
	_t1489 := &pb.Sync{Fragments: fragment_ids762}
	result764 := _t1489
	p.recordSpan(int(span_start763), "Sync")
	return result764
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start766 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol765 := p.consumeTerminal("SYMBOL").Value.str
	result767 := &pb.FragmentId{Id: []byte(symbol765)}
	p.recordSpan(int(span_start766), "FragmentId")
	return result767
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start770 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1490 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1491 := p.parse_epoch_writes()
		_t1490 = _t1491
	}
	epoch_writes768 := _t1490
	var _t1492 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1493 := p.parse_epoch_reads()
		_t1492 = _t1493
	}
	epoch_reads769 := _t1492
	p.consumeLiteral(")")
	_t1494 := epoch_writes768
	if epoch_writes768 == nil {
		_t1494 = []*pb.Write{}
	}
	_t1495 := epoch_reads769
	if epoch_reads769 == nil {
		_t1495 = []*pb.Read{}
	}
	_t1496 := &pb.Epoch{Writes: _t1494, Reads: _t1495}
	result771 := _t1496
	p.recordSpan(int(span_start770), "Epoch")
	return result771
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs772 := []*pb.Write{}
	cond773 := p.matchLookaheadLiteral("(", 0)
	for cond773 {
		_t1497 := p.parse_write()
		item774 := _t1497
		xs772 = append(xs772, item774)
		cond773 = p.matchLookaheadLiteral("(", 0)
	}
	writes775 := xs772
	p.consumeLiteral(")")
	return writes775
}

func (p *Parser) parse_write() *pb.Write {
	span_start781 := int64(p.spanStart())
	var _t1498 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1499 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1499 = 1
		} else {
			var _t1500 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1500 = 3
			} else {
				var _t1501 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1501 = 0
				} else {
					var _t1502 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1502 = 2
					} else {
						_t1502 = -1
					}
					_t1501 = _t1502
				}
				_t1500 = _t1501
			}
			_t1499 = _t1500
		}
		_t1498 = _t1499
	} else {
		_t1498 = -1
	}
	prediction776 := _t1498
	var _t1503 *pb.Write
	if prediction776 == 3 {
		_t1504 := p.parse_snapshot()
		snapshot780 := _t1504
		_t1505 := &pb.Write{}
		_t1505.WriteType = &pb.Write_Snapshot{Snapshot: snapshot780}
		_t1503 = _t1505
	} else {
		var _t1506 *pb.Write
		if prediction776 == 2 {
			_t1507 := p.parse_context()
			context779 := _t1507
			_t1508 := &pb.Write{}
			_t1508.WriteType = &pb.Write_Context{Context: context779}
			_t1506 = _t1508
		} else {
			var _t1509 *pb.Write
			if prediction776 == 1 {
				_t1510 := p.parse_undefine()
				undefine778 := _t1510
				_t1511 := &pb.Write{}
				_t1511.WriteType = &pb.Write_Undefine{Undefine: undefine778}
				_t1509 = _t1511
			} else {
				var _t1512 *pb.Write
				if prediction776 == 0 {
					_t1513 := p.parse_define()
					define777 := _t1513
					_t1514 := &pb.Write{}
					_t1514.WriteType = &pb.Write_Define{Define: define777}
					_t1512 = _t1514
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1509 = _t1512
			}
			_t1506 = _t1509
		}
		_t1503 = _t1506
	}
	result782 := _t1503
	p.recordSpan(int(span_start781), "Write")
	return result782
}

func (p *Parser) parse_define() *pb.Define {
	span_start784 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1515 := p.parse_fragment()
	fragment783 := _t1515
	p.consumeLiteral(")")
	_t1516 := &pb.Define{Fragment: fragment783}
	result785 := _t1516
	p.recordSpan(int(span_start784), "Define")
	return result785
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1517 := p.parse_new_fragment_id()
	new_fragment_id786 := _t1517
	xs787 := []*pb.Declaration{}
	cond788 := p.matchLookaheadLiteral("(", 0)
	for cond788 {
		_t1518 := p.parse_declaration()
		item789 := _t1518
		xs787 = append(xs787, item789)
		cond788 = p.matchLookaheadLiteral("(", 0)
	}
	declarations790 := xs787
	p.consumeLiteral(")")
	result792 := p.constructFragment(new_fragment_id786, declarations790)
	p.recordSpan(int(span_start791), "Fragment")
	return result792
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start794 := int64(p.spanStart())
	_t1519 := p.parse_fragment_id()
	fragment_id793 := _t1519
	p.startFragment(fragment_id793)
	result795 := fragment_id793
	p.recordSpan(int(span_start794), "FragmentId")
	return result795
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start801 := int64(p.spanStart())
	var _t1520 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1521 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1521 = 3
		} else {
			var _t1522 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1522 = 2
			} else {
				var _t1523 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1523 = 3
				} else {
					var _t1524 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1524 = 0
					} else {
						var _t1525 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1525 = 3
						} else {
							var _t1526 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1526 = 3
							} else {
								var _t1527 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1527 = 1
								} else {
									_t1527 = -1
								}
								_t1526 = _t1527
							}
							_t1525 = _t1526
						}
						_t1524 = _t1525
					}
					_t1523 = _t1524
				}
				_t1522 = _t1523
			}
			_t1521 = _t1522
		}
		_t1520 = _t1521
	} else {
		_t1520 = -1
	}
	prediction796 := _t1520
	var _t1528 *pb.Declaration
	if prediction796 == 3 {
		_t1529 := p.parse_data()
		data800 := _t1529
		_t1530 := &pb.Declaration{}
		_t1530.DeclarationType = &pb.Declaration_Data{Data: data800}
		_t1528 = _t1530
	} else {
		var _t1531 *pb.Declaration
		if prediction796 == 2 {
			_t1532 := p.parse_constraint()
			constraint799 := _t1532
			_t1533 := &pb.Declaration{}
			_t1533.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint799}
			_t1531 = _t1533
		} else {
			var _t1534 *pb.Declaration
			if prediction796 == 1 {
				_t1535 := p.parse_algorithm()
				algorithm798 := _t1535
				_t1536 := &pb.Declaration{}
				_t1536.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm798}
				_t1534 = _t1536
			} else {
				var _t1537 *pb.Declaration
				if prediction796 == 0 {
					_t1538 := p.parse_def()
					def797 := _t1538
					_t1539 := &pb.Declaration{}
					_t1539.DeclarationType = &pb.Declaration_Def{Def: def797}
					_t1537 = _t1539
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1534 = _t1537
			}
			_t1531 = _t1534
		}
		_t1528 = _t1531
	}
	result802 := _t1528
	p.recordSpan(int(span_start801), "Declaration")
	return result802
}

func (p *Parser) parse_def() *pb.Def {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1540 := p.parse_relation_id()
	relation_id803 := _t1540
	_t1541 := p.parse_abstraction()
	abstraction804 := _t1541
	var _t1542 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1543 := p.parse_attrs()
		_t1542 = _t1543
	}
	attrs805 := _t1542
	p.consumeLiteral(")")
	_t1544 := attrs805
	if attrs805 == nil {
		_t1544 = []*pb.Attribute{}
	}
	_t1545 := &pb.Def{Name: relation_id803, Body: abstraction804, Attrs: _t1544}
	result807 := _t1545
	p.recordSpan(int(span_start806), "Def")
	return result807
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start811 := int64(p.spanStart())
	var _t1546 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1546 = 0
	} else {
		var _t1547 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1547 = 1
		} else {
			_t1547 = -1
		}
		_t1546 = _t1547
	}
	prediction808 := _t1546
	var _t1548 *pb.RelationId
	if prediction808 == 1 {
		uint128810 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128810
		_t1548 = &pb.RelationId{IdLow: uint128810.Low, IdHigh: uint128810.High}
	} else {
		var _t1549 *pb.RelationId
		if prediction808 == 0 {
			p.consumeLiteral(":")
			symbol809 := p.consumeTerminal("SYMBOL").Value.str
			_t1549 = p.relationIdFromString(symbol809)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1548 = _t1549
	}
	result812 := _t1548
	p.recordSpan(int(span_start811), "RelationId")
	return result812
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1550 := p.parse_bindings()
	bindings813 := _t1550
	_t1551 := p.parse_formula()
	formula814 := _t1551
	p.consumeLiteral(")")
	_t1552 := &pb.Abstraction{Vars: listConcat(bindings813[0].([]*pb.Binding), bindings813[1].([]*pb.Binding)), Value: formula814}
	result816 := _t1552
	p.recordSpan(int(span_start815), "Abstraction")
	return result816
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs817 := []*pb.Binding{}
	cond818 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond818 {
		_t1553 := p.parse_binding()
		item819 := _t1553
		xs817 = append(xs817, item819)
		cond818 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings820 := xs817
	var _t1554 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1555 := p.parse_value_bindings()
		_t1554 = _t1555
	}
	value_bindings821 := _t1554
	p.consumeLiteral("]")
	_t1556 := value_bindings821
	if value_bindings821 == nil {
		_t1556 = []*pb.Binding{}
	}
	return []interface{}{bindings820, _t1556}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start824 := int64(p.spanStart())
	symbol822 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1557 := p.parse_type()
	type823 := _t1557
	_t1558 := &pb.Var{Name: symbol822}
	_t1559 := &pb.Binding{Var: _t1558, Type: type823}
	result825 := _t1559
	p.recordSpan(int(span_start824), "Binding")
	return result825
}

func (p *Parser) parse_type() *pb.Type {
	span_start841 := int64(p.spanStart())
	var _t1560 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1560 = 0
	} else {
		var _t1561 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1561 = 13
		} else {
			var _t1562 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1562 = 4
			} else {
				var _t1563 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1563 = 1
				} else {
					var _t1564 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1564 = 8
					} else {
						var _t1565 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1565 = 11
						} else {
							var _t1566 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1566 = 5
							} else {
								var _t1567 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1567 = 2
								} else {
									var _t1568 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1568 = 12
									} else {
										var _t1569 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1569 = 3
										} else {
											var _t1570 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1570 = 7
											} else {
												var _t1571 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1571 = 6
												} else {
													var _t1572 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1572 = 10
													} else {
														var _t1573 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1573 = 9
														} else {
															_t1573 = -1
														}
														_t1572 = _t1573
													}
													_t1571 = _t1572
												}
												_t1570 = _t1571
											}
											_t1569 = _t1570
										}
										_t1568 = _t1569
									}
									_t1567 = _t1568
								}
								_t1566 = _t1567
							}
							_t1565 = _t1566
						}
						_t1564 = _t1565
					}
					_t1563 = _t1564
				}
				_t1562 = _t1563
			}
			_t1561 = _t1562
		}
		_t1560 = _t1561
	}
	prediction826 := _t1560
	var _t1574 *pb.Type
	if prediction826 == 13 {
		_t1575 := p.parse_uint32_type()
		uint32_type840 := _t1575
		_t1576 := &pb.Type{}
		_t1576.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type840}
		_t1574 = _t1576
	} else {
		var _t1577 *pb.Type
		if prediction826 == 12 {
			_t1578 := p.parse_float32_type()
			float32_type839 := _t1578
			_t1579 := &pb.Type{}
			_t1579.Type = &pb.Type_Float32Type{Float32Type: float32_type839}
			_t1577 = _t1579
		} else {
			var _t1580 *pb.Type
			if prediction826 == 11 {
				_t1581 := p.parse_int32_type()
				int32_type838 := _t1581
				_t1582 := &pb.Type{}
				_t1582.Type = &pb.Type_Int32Type{Int32Type: int32_type838}
				_t1580 = _t1582
			} else {
				var _t1583 *pb.Type
				if prediction826 == 10 {
					_t1584 := p.parse_boolean_type()
					boolean_type837 := _t1584
					_t1585 := &pb.Type{}
					_t1585.Type = &pb.Type_BooleanType{BooleanType: boolean_type837}
					_t1583 = _t1585
				} else {
					var _t1586 *pb.Type
					if prediction826 == 9 {
						_t1587 := p.parse_decimal_type()
						decimal_type836 := _t1587
						_t1588 := &pb.Type{}
						_t1588.Type = &pb.Type_DecimalType{DecimalType: decimal_type836}
						_t1586 = _t1588
					} else {
						var _t1589 *pb.Type
						if prediction826 == 8 {
							_t1590 := p.parse_missing_type()
							missing_type835 := _t1590
							_t1591 := &pb.Type{}
							_t1591.Type = &pb.Type_MissingType{MissingType: missing_type835}
							_t1589 = _t1591
						} else {
							var _t1592 *pb.Type
							if prediction826 == 7 {
								_t1593 := p.parse_datetime_type()
								datetime_type834 := _t1593
								_t1594 := &pb.Type{}
								_t1594.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type834}
								_t1592 = _t1594
							} else {
								var _t1595 *pb.Type
								if prediction826 == 6 {
									_t1596 := p.parse_date_type()
									date_type833 := _t1596
									_t1597 := &pb.Type{}
									_t1597.Type = &pb.Type_DateType{DateType: date_type833}
									_t1595 = _t1597
								} else {
									var _t1598 *pb.Type
									if prediction826 == 5 {
										_t1599 := p.parse_int128_type()
										int128_type832 := _t1599
										_t1600 := &pb.Type{}
										_t1600.Type = &pb.Type_Int128Type{Int128Type: int128_type832}
										_t1598 = _t1600
									} else {
										var _t1601 *pb.Type
										if prediction826 == 4 {
											_t1602 := p.parse_uint128_type()
											uint128_type831 := _t1602
											_t1603 := &pb.Type{}
											_t1603.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type831}
											_t1601 = _t1603
										} else {
											var _t1604 *pb.Type
											if prediction826 == 3 {
												_t1605 := p.parse_float_type()
												float_type830 := _t1605
												_t1606 := &pb.Type{}
												_t1606.Type = &pb.Type_FloatType{FloatType: float_type830}
												_t1604 = _t1606
											} else {
												var _t1607 *pb.Type
												if prediction826 == 2 {
													_t1608 := p.parse_int_type()
													int_type829 := _t1608
													_t1609 := &pb.Type{}
													_t1609.Type = &pb.Type_IntType{IntType: int_type829}
													_t1607 = _t1609
												} else {
													var _t1610 *pb.Type
													if prediction826 == 1 {
														_t1611 := p.parse_string_type()
														string_type828 := _t1611
														_t1612 := &pb.Type{}
														_t1612.Type = &pb.Type_StringType{StringType: string_type828}
														_t1610 = _t1612
													} else {
														var _t1613 *pb.Type
														if prediction826 == 0 {
															_t1614 := p.parse_unspecified_type()
															unspecified_type827 := _t1614
															_t1615 := &pb.Type{}
															_t1615.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type827}
															_t1613 = _t1615
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1583 = _t1586
				}
				_t1580 = _t1583
			}
			_t1577 = _t1580
		}
		_t1574 = _t1577
	}
	result842 := _t1574
	p.recordSpan(int(span_start841), "Type")
	return result842
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1616 := &pb.UnspecifiedType{}
	result844 := _t1616
	p.recordSpan(int(span_start843), "UnspecifiedType")
	return result844
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1617 := &pb.StringType{}
	result846 := _t1617
	p.recordSpan(int(span_start845), "StringType")
	return result846
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1618 := &pb.IntType{}
	result848 := _t1618
	p.recordSpan(int(span_start847), "IntType")
	return result848
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1619 := &pb.FloatType{}
	result850 := _t1619
	p.recordSpan(int(span_start849), "FloatType")
	return result850
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1620 := &pb.UInt128Type{}
	result852 := _t1620
	p.recordSpan(int(span_start851), "UInt128Type")
	return result852
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1621 := &pb.Int128Type{}
	result854 := _t1621
	p.recordSpan(int(span_start853), "Int128Type")
	return result854
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1622 := &pb.DateType{}
	result856 := _t1622
	p.recordSpan(int(span_start855), "DateType")
	return result856
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1623 := &pb.DateTimeType{}
	result858 := _t1623
	p.recordSpan(int(span_start857), "DateTimeType")
	return result858
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1624 := &pb.MissingType{}
	result860 := _t1624
	p.recordSpan(int(span_start859), "MissingType")
	return result860
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int861 := p.consumeTerminal("INT").Value.i64
	int_3862 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1625 := &pb.DecimalType{Precision: int32(int861), Scale: int32(int_3862)}
	result864 := _t1625
	p.recordSpan(int(span_start863), "DecimalType")
	return result864
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1626 := &pb.BooleanType{}
	result866 := _t1626
	p.recordSpan(int(span_start865), "BooleanType")
	return result866
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start867 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1627 := &pb.Int32Type{}
	result868 := _t1627
	p.recordSpan(int(span_start867), "Int32Type")
	return result868
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1628 := &pb.Float32Type{}
	result870 := _t1628
	p.recordSpan(int(span_start869), "Float32Type")
	return result870
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start871 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1629 := &pb.UInt32Type{}
	result872 := _t1629
	p.recordSpan(int(span_start871), "UInt32Type")
	return result872
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs873 := []*pb.Binding{}
	cond874 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond874 {
		_t1630 := p.parse_binding()
		item875 := _t1630
		xs873 = append(xs873, item875)
		cond874 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings876 := xs873
	return bindings876
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start891 := int64(p.spanStart())
	var _t1631 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1632 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1632 = 0
		} else {
			var _t1633 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1633 = 11
			} else {
				var _t1634 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1634 = 3
				} else {
					var _t1635 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1635 = 10
					} else {
						var _t1636 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1636 = 9
						} else {
							var _t1637 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1637 = 5
							} else {
								var _t1638 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1638 = 6
								} else {
									var _t1639 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1639 = 7
									} else {
										var _t1640 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1640 = 1
										} else {
											var _t1641 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1641 = 2
											} else {
												var _t1642 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1642 = 12
												} else {
													var _t1643 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1643 = 8
													} else {
														var _t1644 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1644 = 4
														} else {
															var _t1645 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1645 = 10
															} else {
																var _t1646 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1646 = 10
																} else {
																	var _t1647 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1647 = 10
																	} else {
																		var _t1648 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1648 = 10
																		} else {
																			var _t1649 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1649 = 10
																			} else {
																				var _t1650 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1650 = 10
																				} else {
																					var _t1651 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1651 = 10
																					} else {
																						var _t1652 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1652 = 10
																						} else {
																							var _t1653 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1653 = 10
																							} else {
																								_t1653 = -1
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
																	}
																	_t1646 = _t1647
																}
																_t1645 = _t1646
															}
															_t1644 = _t1645
														}
														_t1643 = _t1644
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
	} else {
		_t1631 = -1
	}
	prediction877 := _t1631
	var _t1654 *pb.Formula
	if prediction877 == 12 {
		_t1655 := p.parse_cast()
		cast890 := _t1655
		_t1656 := &pb.Formula{}
		_t1656.FormulaType = &pb.Formula_Cast{Cast: cast890}
		_t1654 = _t1656
	} else {
		var _t1657 *pb.Formula
		if prediction877 == 11 {
			_t1658 := p.parse_rel_atom()
			rel_atom889 := _t1658
			_t1659 := &pb.Formula{}
			_t1659.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom889}
			_t1657 = _t1659
		} else {
			var _t1660 *pb.Formula
			if prediction877 == 10 {
				_t1661 := p.parse_primitive()
				primitive888 := _t1661
				_t1662 := &pb.Formula{}
				_t1662.FormulaType = &pb.Formula_Primitive{Primitive: primitive888}
				_t1660 = _t1662
			} else {
				var _t1663 *pb.Formula
				if prediction877 == 9 {
					_t1664 := p.parse_pragma()
					pragma887 := _t1664
					_t1665 := &pb.Formula{}
					_t1665.FormulaType = &pb.Formula_Pragma{Pragma: pragma887}
					_t1663 = _t1665
				} else {
					var _t1666 *pb.Formula
					if prediction877 == 8 {
						_t1667 := p.parse_atom()
						atom886 := _t1667
						_t1668 := &pb.Formula{}
						_t1668.FormulaType = &pb.Formula_Atom{Atom: atom886}
						_t1666 = _t1668
					} else {
						var _t1669 *pb.Formula
						if prediction877 == 7 {
							_t1670 := p.parse_ffi()
							ffi885 := _t1670
							_t1671 := &pb.Formula{}
							_t1671.FormulaType = &pb.Formula_Ffi{Ffi: ffi885}
							_t1669 = _t1671
						} else {
							var _t1672 *pb.Formula
							if prediction877 == 6 {
								_t1673 := p.parse_not()
								not884 := _t1673
								_t1674 := &pb.Formula{}
								_t1674.FormulaType = &pb.Formula_Not{Not: not884}
								_t1672 = _t1674
							} else {
								var _t1675 *pb.Formula
								if prediction877 == 5 {
									_t1676 := p.parse_disjunction()
									disjunction883 := _t1676
									_t1677 := &pb.Formula{}
									_t1677.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction883}
									_t1675 = _t1677
								} else {
									var _t1678 *pb.Formula
									if prediction877 == 4 {
										_t1679 := p.parse_conjunction()
										conjunction882 := _t1679
										_t1680 := &pb.Formula{}
										_t1680.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction882}
										_t1678 = _t1680
									} else {
										var _t1681 *pb.Formula
										if prediction877 == 3 {
											_t1682 := p.parse_reduce()
											reduce881 := _t1682
											_t1683 := &pb.Formula{}
											_t1683.FormulaType = &pb.Formula_Reduce{Reduce: reduce881}
											_t1681 = _t1683
										} else {
											var _t1684 *pb.Formula
											if prediction877 == 2 {
												_t1685 := p.parse_exists()
												exists880 := _t1685
												_t1686 := &pb.Formula{}
												_t1686.FormulaType = &pb.Formula_Exists{Exists: exists880}
												_t1684 = _t1686
											} else {
												var _t1687 *pb.Formula
												if prediction877 == 1 {
													_t1688 := p.parse_false()
													false879 := _t1688
													_t1689 := &pb.Formula{}
													_t1689.FormulaType = &pb.Formula_Disjunction{Disjunction: false879}
													_t1687 = _t1689
												} else {
													var _t1690 *pb.Formula
													if prediction877 == 0 {
														_t1691 := p.parse_true()
														true878 := _t1691
														_t1692 := &pb.Formula{}
														_t1692.FormulaType = &pb.Formula_Conjunction{Conjunction: true878}
														_t1690 = _t1692
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1687 = _t1690
												}
												_t1684 = _t1687
											}
											_t1681 = _t1684
										}
										_t1678 = _t1681
									}
									_t1675 = _t1678
								}
								_t1672 = _t1675
							}
							_t1669 = _t1672
						}
						_t1666 = _t1669
					}
					_t1663 = _t1666
				}
				_t1660 = _t1663
			}
			_t1657 = _t1660
		}
		_t1654 = _t1657
	}
	result892 := _t1654
	p.recordSpan(int(span_start891), "Formula")
	return result892
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start893 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1693 := &pb.Conjunction{Args: []*pb.Formula{}}
	result894 := _t1693
	p.recordSpan(int(span_start893), "Conjunction")
	return result894
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1694 := &pb.Disjunction{Args: []*pb.Formula{}}
	result896 := _t1694
	p.recordSpan(int(span_start895), "Disjunction")
	return result896
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1695 := p.parse_bindings()
	bindings897 := _t1695
	_t1696 := p.parse_formula()
	formula898 := _t1696
	p.consumeLiteral(")")
	_t1697 := &pb.Abstraction{Vars: listConcat(bindings897[0].([]*pb.Binding), bindings897[1].([]*pb.Binding)), Value: formula898}
	_t1698 := &pb.Exists{Body: _t1697}
	result900 := _t1698
	p.recordSpan(int(span_start899), "Exists")
	return result900
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1699 := p.parse_abstraction()
	abstraction901 := _t1699
	_t1700 := p.parse_abstraction()
	abstraction_3902 := _t1700
	_t1701 := p.parse_terms()
	terms903 := _t1701
	p.consumeLiteral(")")
	_t1702 := &pb.Reduce{Op: abstraction901, Body: abstraction_3902, Terms: terms903}
	result905 := _t1702
	p.recordSpan(int(span_start904), "Reduce")
	return result905
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs906 := []*pb.Term{}
	cond907 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond907 {
		_t1703 := p.parse_term()
		item908 := _t1703
		xs906 = append(xs906, item908)
		cond907 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms909 := xs906
	p.consumeLiteral(")")
	return terms909
}

func (p *Parser) parse_term() *pb.Term {
	span_start913 := int64(p.spanStart())
	var _t1704 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1704 = 1
	} else {
		var _t1705 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1705 = 1
		} else {
			var _t1706 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1706 = 1
			} else {
				var _t1707 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1707 = 1
				} else {
					var _t1708 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1708 = 0
					} else {
						var _t1709 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1709 = 1
						} else {
							var _t1710 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1710 = 1
							} else {
								var _t1711 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1711 = 1
								} else {
									var _t1712 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1712 = 1
									} else {
										var _t1713 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1713 = 1
										} else {
											var _t1714 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1714 = 1
											} else {
												var _t1715 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1715 = 1
												} else {
													var _t1716 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1716 = 1
													} else {
														var _t1717 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1717 = 1
														} else {
															_t1717 = -1
														}
														_t1716 = _t1717
													}
													_t1715 = _t1716
												}
												_t1714 = _t1715
											}
											_t1713 = _t1714
										}
										_t1712 = _t1713
									}
									_t1711 = _t1712
								}
								_t1710 = _t1711
							}
							_t1709 = _t1710
						}
						_t1708 = _t1709
					}
					_t1707 = _t1708
				}
				_t1706 = _t1707
			}
			_t1705 = _t1706
		}
		_t1704 = _t1705
	}
	prediction910 := _t1704
	var _t1718 *pb.Term
	if prediction910 == 1 {
		_t1719 := p.parse_value()
		value912 := _t1719
		_t1720 := &pb.Term{}
		_t1720.TermType = &pb.Term_Constant{Constant: value912}
		_t1718 = _t1720
	} else {
		var _t1721 *pb.Term
		if prediction910 == 0 {
			_t1722 := p.parse_var()
			var911 := _t1722
			_t1723 := &pb.Term{}
			_t1723.TermType = &pb.Term_Var{Var: var911}
			_t1721 = _t1723
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1718 = _t1721
	}
	result914 := _t1718
	p.recordSpan(int(span_start913), "Term")
	return result914
}

func (p *Parser) parse_var() *pb.Var {
	span_start916 := int64(p.spanStart())
	symbol915 := p.consumeTerminal("SYMBOL").Value.str
	_t1724 := &pb.Var{Name: symbol915}
	result917 := _t1724
	p.recordSpan(int(span_start916), "Var")
	return result917
}

func (p *Parser) parse_value() *pb.Value {
	span_start931 := int64(p.spanStart())
	var _t1725 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1725 = 12
	} else {
		var _t1726 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1726 = 11
		} else {
			var _t1727 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1727 = 12
			} else {
				var _t1728 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1729 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1729 = 1
					} else {
						var _t1730 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1730 = 0
						} else {
							_t1730 = -1
						}
						_t1729 = _t1730
					}
					_t1728 = _t1729
				} else {
					var _t1731 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1731 = 7
					} else {
						var _t1732 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1732 = 8
						} else {
							var _t1733 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1733 = 2
							} else {
								var _t1734 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1734 = 3
								} else {
									var _t1735 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1735 = 9
									} else {
										var _t1736 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1736 = 4
										} else {
											var _t1737 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1737 = 5
											} else {
												var _t1738 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1738 = 6
												} else {
													var _t1739 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1739 = 10
													} else {
														_t1739 = -1
													}
													_t1738 = _t1739
												}
												_t1737 = _t1738
											}
											_t1736 = _t1737
										}
										_t1735 = _t1736
									}
									_t1734 = _t1735
								}
								_t1733 = _t1734
							}
							_t1732 = _t1733
						}
						_t1731 = _t1732
					}
					_t1728 = _t1731
				}
				_t1727 = _t1728
			}
			_t1726 = _t1727
		}
		_t1725 = _t1726
	}
	prediction918 := _t1725
	var _t1740 *pb.Value
	if prediction918 == 12 {
		_t1741 := p.parse_boolean_value()
		boolean_value930 := _t1741
		_t1742 := &pb.Value{}
		_t1742.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value930}
		_t1740 = _t1742
	} else {
		var _t1743 *pb.Value
		if prediction918 == 11 {
			p.consumeLiteral("missing")
			_t1744 := &pb.MissingValue{}
			_t1745 := &pb.Value{}
			_t1745.Value = &pb.Value_MissingValue{MissingValue: _t1744}
			_t1743 = _t1745
		} else {
			var _t1746 *pb.Value
			if prediction918 == 10 {
				formatted_decimal929 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1747 := &pb.Value{}
				_t1747.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal929}
				_t1746 = _t1747
			} else {
				var _t1748 *pb.Value
				if prediction918 == 9 {
					formatted_int128928 := p.consumeTerminal("INT128").Value.int128
					_t1749 := &pb.Value{}
					_t1749.Value = &pb.Value_Int128Value{Int128Value: formatted_int128928}
					_t1748 = _t1749
				} else {
					var _t1750 *pb.Value
					if prediction918 == 8 {
						formatted_uint128927 := p.consumeTerminal("UINT128").Value.uint128
						_t1751 := &pb.Value{}
						_t1751.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128927}
						_t1750 = _t1751
					} else {
						var _t1752 *pb.Value
						if prediction918 == 7 {
							formatted_uint32926 := p.consumeTerminal("UINT32").Value.u32
							_t1753 := &pb.Value{}
							_t1753.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32926}
							_t1752 = _t1753
						} else {
							var _t1754 *pb.Value
							if prediction918 == 6 {
								formatted_float925 := p.consumeTerminal("FLOAT").Value.f64
								_t1755 := &pb.Value{}
								_t1755.Value = &pb.Value_FloatValue{FloatValue: formatted_float925}
								_t1754 = _t1755
							} else {
								var _t1756 *pb.Value
								if prediction918 == 5 {
									formatted_float32924 := p.consumeTerminal("FLOAT32").Value.f32
									_t1757 := &pb.Value{}
									_t1757.Value = &pb.Value_Float32Value{Float32Value: formatted_float32924}
									_t1756 = _t1757
								} else {
									var _t1758 *pb.Value
									if prediction918 == 4 {
										formatted_int923 := p.consumeTerminal("INT").Value.i64
										_t1759 := &pb.Value{}
										_t1759.Value = &pb.Value_IntValue{IntValue: formatted_int923}
										_t1758 = _t1759
									} else {
										var _t1760 *pb.Value
										if prediction918 == 3 {
											formatted_int32922 := p.consumeTerminal("INT32").Value.i32
											_t1761 := &pb.Value{}
											_t1761.Value = &pb.Value_Int32Value{Int32Value: formatted_int32922}
											_t1760 = _t1761
										} else {
											var _t1762 *pb.Value
											if prediction918 == 2 {
												formatted_string921 := p.consumeTerminal("STRING").Value.str
												_t1763 := &pb.Value{}
												_t1763.Value = &pb.Value_StringValue{StringValue: formatted_string921}
												_t1762 = _t1763
											} else {
												var _t1764 *pb.Value
												if prediction918 == 1 {
													_t1765 := p.parse_datetime()
													datetime920 := _t1765
													_t1766 := &pb.Value{}
													_t1766.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime920}
													_t1764 = _t1766
												} else {
													var _t1767 *pb.Value
													if prediction918 == 0 {
														_t1768 := p.parse_date()
														date919 := _t1768
														_t1769 := &pb.Value{}
														_t1769.Value = &pb.Value_DateValue{DateValue: date919}
														_t1767 = _t1769
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1764 = _t1767
												}
												_t1762 = _t1764
											}
											_t1760 = _t1762
										}
										_t1758 = _t1760
									}
									_t1756 = _t1758
								}
								_t1754 = _t1756
							}
							_t1752 = _t1754
						}
						_t1750 = _t1752
					}
					_t1748 = _t1750
				}
				_t1746 = _t1748
			}
			_t1743 = _t1746
		}
		_t1740 = _t1743
	}
	result932 := _t1740
	p.recordSpan(int(span_start931), "Value")
	return result932
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start936 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int933 := p.consumeTerminal("INT").Value.i64
	formatted_int_3934 := p.consumeTerminal("INT").Value.i64
	formatted_int_4935 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1770 := &pb.DateValue{Year: int32(formatted_int933), Month: int32(formatted_int_3934), Day: int32(formatted_int_4935)}
	result937 := _t1770
	p.recordSpan(int(span_start936), "DateValue")
	return result937
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start945 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int938 := p.consumeTerminal("INT").Value.i64
	formatted_int_3939 := p.consumeTerminal("INT").Value.i64
	formatted_int_4940 := p.consumeTerminal("INT").Value.i64
	formatted_int_5941 := p.consumeTerminal("INT").Value.i64
	formatted_int_6942 := p.consumeTerminal("INT").Value.i64
	formatted_int_7943 := p.consumeTerminal("INT").Value.i64
	var _t1771 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1771 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8944 := _t1771
	p.consumeLiteral(")")
	_t1772 := &pb.DateTimeValue{Year: int32(formatted_int938), Month: int32(formatted_int_3939), Day: int32(formatted_int_4940), Hour: int32(formatted_int_5941), Minute: int32(formatted_int_6942), Second: int32(formatted_int_7943), Microsecond: int32(deref(formatted_int_8944, 0))}
	result946 := _t1772
	p.recordSpan(int(span_start945), "DateTimeValue")
	return result946
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start951 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs947 := []*pb.Formula{}
	cond948 := p.matchLookaheadLiteral("(", 0)
	for cond948 {
		_t1773 := p.parse_formula()
		item949 := _t1773
		xs947 = append(xs947, item949)
		cond948 = p.matchLookaheadLiteral("(", 0)
	}
	formulas950 := xs947
	p.consumeLiteral(")")
	_t1774 := &pb.Conjunction{Args: formulas950}
	result952 := _t1774
	p.recordSpan(int(span_start951), "Conjunction")
	return result952
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs953 := []*pb.Formula{}
	cond954 := p.matchLookaheadLiteral("(", 0)
	for cond954 {
		_t1775 := p.parse_formula()
		item955 := _t1775
		xs953 = append(xs953, item955)
		cond954 = p.matchLookaheadLiteral("(", 0)
	}
	formulas956 := xs953
	p.consumeLiteral(")")
	_t1776 := &pb.Disjunction{Args: formulas956}
	result958 := _t1776
	p.recordSpan(int(span_start957), "Disjunction")
	return result958
}

func (p *Parser) parse_not() *pb.Not {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1777 := p.parse_formula()
	formula959 := _t1777
	p.consumeLiteral(")")
	_t1778 := &pb.Not{Arg: formula959}
	result961 := _t1778
	p.recordSpan(int(span_start960), "Not")
	return result961
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1779 := p.parse_name()
	name962 := _t1779
	_t1780 := p.parse_ffi_args()
	ffi_args963 := _t1780
	_t1781 := p.parse_terms()
	terms964 := _t1781
	p.consumeLiteral(")")
	_t1782 := &pb.FFI{Name: name962, Args: ffi_args963, Terms: terms964}
	result966 := _t1782
	p.recordSpan(int(span_start965), "FFI")
	return result966
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol967 := p.consumeTerminal("SYMBOL").Value.str
	return symbol967
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs968 := []*pb.Abstraction{}
	cond969 := p.matchLookaheadLiteral("(", 0)
	for cond969 {
		_t1783 := p.parse_abstraction()
		item970 := _t1783
		xs968 = append(xs968, item970)
		cond969 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions971 := xs968
	p.consumeLiteral(")")
	return abstractions971
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start977 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1784 := p.parse_relation_id()
	relation_id972 := _t1784
	xs973 := []*pb.Term{}
	cond974 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond974 {
		_t1785 := p.parse_term()
		item975 := _t1785
		xs973 = append(xs973, item975)
		cond974 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms976 := xs973
	p.consumeLiteral(")")
	_t1786 := &pb.Atom{Name: relation_id972, Terms: terms976}
	result978 := _t1786
	p.recordSpan(int(span_start977), "Atom")
	return result978
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1787 := p.parse_name()
	name979 := _t1787
	xs980 := []*pb.Term{}
	cond981 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond981 {
		_t1788 := p.parse_term()
		item982 := _t1788
		xs980 = append(xs980, item982)
		cond981 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms983 := xs980
	p.consumeLiteral(")")
	_t1789 := &pb.Pragma{Name: name979, Terms: terms983}
	result985 := _t1789
	p.recordSpan(int(span_start984), "Pragma")
	return result985
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start1001 := int64(p.spanStart())
	var _t1790 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1791 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1791 = 9
		} else {
			var _t1792 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1792 = 4
			} else {
				var _t1793 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1793 = 3
				} else {
					var _t1794 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1794 = 0
					} else {
						var _t1795 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1795 = 2
						} else {
							var _t1796 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1796 = 1
							} else {
								var _t1797 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1797 = 8
								} else {
									var _t1798 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1798 = 6
									} else {
										var _t1799 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1799 = 5
										} else {
											var _t1800 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1800 = 7
											} else {
												_t1800 = -1
											}
											_t1799 = _t1800
										}
										_t1798 = _t1799
									}
									_t1797 = _t1798
								}
								_t1796 = _t1797
							}
							_t1795 = _t1796
						}
						_t1794 = _t1795
					}
					_t1793 = _t1794
				}
				_t1792 = _t1793
			}
			_t1791 = _t1792
		}
		_t1790 = _t1791
	} else {
		_t1790 = -1
	}
	prediction986 := _t1790
	var _t1801 *pb.Primitive
	if prediction986 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1802 := p.parse_name()
		name996 := _t1802
		xs997 := []*pb.RelTerm{}
		cond998 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond998 {
			_t1803 := p.parse_rel_term()
			item999 := _t1803
			xs997 = append(xs997, item999)
			cond998 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms1000 := xs997
		p.consumeLiteral(")")
		_t1804 := &pb.Primitive{Name: name996, Terms: rel_terms1000}
		_t1801 = _t1804
	} else {
		var _t1805 *pb.Primitive
		if prediction986 == 8 {
			_t1806 := p.parse_divide()
			divide995 := _t1806
			_t1805 = divide995
		} else {
			var _t1807 *pb.Primitive
			if prediction986 == 7 {
				_t1808 := p.parse_multiply()
				multiply994 := _t1808
				_t1807 = multiply994
			} else {
				var _t1809 *pb.Primitive
				if prediction986 == 6 {
					_t1810 := p.parse_minus()
					minus993 := _t1810
					_t1809 = minus993
				} else {
					var _t1811 *pb.Primitive
					if prediction986 == 5 {
						_t1812 := p.parse_add()
						add992 := _t1812
						_t1811 = add992
					} else {
						var _t1813 *pb.Primitive
						if prediction986 == 4 {
							_t1814 := p.parse_gt_eq()
							gt_eq991 := _t1814
							_t1813 = gt_eq991
						} else {
							var _t1815 *pb.Primitive
							if prediction986 == 3 {
								_t1816 := p.parse_gt()
								gt990 := _t1816
								_t1815 = gt990
							} else {
								var _t1817 *pb.Primitive
								if prediction986 == 2 {
									_t1818 := p.parse_lt_eq()
									lt_eq989 := _t1818
									_t1817 = lt_eq989
								} else {
									var _t1819 *pb.Primitive
									if prediction986 == 1 {
										_t1820 := p.parse_lt()
										lt988 := _t1820
										_t1819 = lt988
									} else {
										var _t1821 *pb.Primitive
										if prediction986 == 0 {
											_t1822 := p.parse_eq()
											eq987 := _t1822
											_t1821 = eq987
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1819 = _t1821
									}
									_t1817 = _t1819
								}
								_t1815 = _t1817
							}
							_t1813 = _t1815
						}
						_t1811 = _t1813
					}
					_t1809 = _t1811
				}
				_t1807 = _t1809
			}
			_t1805 = _t1807
		}
		_t1801 = _t1805
	}
	result1002 := _t1801
	p.recordSpan(int(span_start1001), "Primitive")
	return result1002
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1823 := p.parse_term()
	term1003 := _t1823
	_t1824 := p.parse_term()
	term_31004 := _t1824
	p.consumeLiteral(")")
	_t1825 := &pb.RelTerm{}
	_t1825.RelTermType = &pb.RelTerm_Term{Term: term1003}
	_t1826 := &pb.RelTerm{}
	_t1826.RelTermType = &pb.RelTerm_Term{Term: term_31004}
	_t1827 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1825, _t1826}}
	result1006 := _t1827
	p.recordSpan(int(span_start1005), "Primitive")
	return result1006
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1828 := p.parse_term()
	term1007 := _t1828
	_t1829 := p.parse_term()
	term_31008 := _t1829
	p.consumeLiteral(")")
	_t1830 := &pb.RelTerm{}
	_t1830.RelTermType = &pb.RelTerm_Term{Term: term1007}
	_t1831 := &pb.RelTerm{}
	_t1831.RelTermType = &pb.RelTerm_Term{Term: term_31008}
	_t1832 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1830, _t1831}}
	result1010 := _t1832
	p.recordSpan(int(span_start1009), "Primitive")
	return result1010
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1833 := p.parse_term()
	term1011 := _t1833
	_t1834 := p.parse_term()
	term_31012 := _t1834
	p.consumeLiteral(")")
	_t1835 := &pb.RelTerm{}
	_t1835.RelTermType = &pb.RelTerm_Term{Term: term1011}
	_t1836 := &pb.RelTerm{}
	_t1836.RelTermType = &pb.RelTerm_Term{Term: term_31012}
	_t1837 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1835, _t1836}}
	result1014 := _t1837
	p.recordSpan(int(span_start1013), "Primitive")
	return result1014
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1838 := p.parse_term()
	term1015 := _t1838
	_t1839 := p.parse_term()
	term_31016 := _t1839
	p.consumeLiteral(")")
	_t1840 := &pb.RelTerm{}
	_t1840.RelTermType = &pb.RelTerm_Term{Term: term1015}
	_t1841 := &pb.RelTerm{}
	_t1841.RelTermType = &pb.RelTerm_Term{Term: term_31016}
	_t1842 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1840, _t1841}}
	result1018 := _t1842
	p.recordSpan(int(span_start1017), "Primitive")
	return result1018
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1843 := p.parse_term()
	term1019 := _t1843
	_t1844 := p.parse_term()
	term_31020 := _t1844
	p.consumeLiteral(")")
	_t1845 := &pb.RelTerm{}
	_t1845.RelTermType = &pb.RelTerm_Term{Term: term1019}
	_t1846 := &pb.RelTerm{}
	_t1846.RelTermType = &pb.RelTerm_Term{Term: term_31020}
	_t1847 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1845, _t1846}}
	result1022 := _t1847
	p.recordSpan(int(span_start1021), "Primitive")
	return result1022
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1848 := p.parse_term()
	term1023 := _t1848
	_t1849 := p.parse_term()
	term_31024 := _t1849
	_t1850 := p.parse_term()
	term_41025 := _t1850
	p.consumeLiteral(")")
	_t1851 := &pb.RelTerm{}
	_t1851.RelTermType = &pb.RelTerm_Term{Term: term1023}
	_t1852 := &pb.RelTerm{}
	_t1852.RelTermType = &pb.RelTerm_Term{Term: term_31024}
	_t1853 := &pb.RelTerm{}
	_t1853.RelTermType = &pb.RelTerm_Term{Term: term_41025}
	_t1854 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1851, _t1852, _t1853}}
	result1027 := _t1854
	p.recordSpan(int(span_start1026), "Primitive")
	return result1027
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1855 := p.parse_term()
	term1028 := _t1855
	_t1856 := p.parse_term()
	term_31029 := _t1856
	_t1857 := p.parse_term()
	term_41030 := _t1857
	p.consumeLiteral(")")
	_t1858 := &pb.RelTerm{}
	_t1858.RelTermType = &pb.RelTerm_Term{Term: term1028}
	_t1859 := &pb.RelTerm{}
	_t1859.RelTermType = &pb.RelTerm_Term{Term: term_31029}
	_t1860 := &pb.RelTerm{}
	_t1860.RelTermType = &pb.RelTerm_Term{Term: term_41030}
	_t1861 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1858, _t1859, _t1860}}
	result1032 := _t1861
	p.recordSpan(int(span_start1031), "Primitive")
	return result1032
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1862 := p.parse_term()
	term1033 := _t1862
	_t1863 := p.parse_term()
	term_31034 := _t1863
	_t1864 := p.parse_term()
	term_41035 := _t1864
	p.consumeLiteral(")")
	_t1865 := &pb.RelTerm{}
	_t1865.RelTermType = &pb.RelTerm_Term{Term: term1033}
	_t1866 := &pb.RelTerm{}
	_t1866.RelTermType = &pb.RelTerm_Term{Term: term_31034}
	_t1867 := &pb.RelTerm{}
	_t1867.RelTermType = &pb.RelTerm_Term{Term: term_41035}
	_t1868 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1865, _t1866, _t1867}}
	result1037 := _t1868
	p.recordSpan(int(span_start1036), "Primitive")
	return result1037
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1041 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1869 := p.parse_term()
	term1038 := _t1869
	_t1870 := p.parse_term()
	term_31039 := _t1870
	_t1871 := p.parse_term()
	term_41040 := _t1871
	p.consumeLiteral(")")
	_t1872 := &pb.RelTerm{}
	_t1872.RelTermType = &pb.RelTerm_Term{Term: term1038}
	_t1873 := &pb.RelTerm{}
	_t1873.RelTermType = &pb.RelTerm_Term{Term: term_31039}
	_t1874 := &pb.RelTerm{}
	_t1874.RelTermType = &pb.RelTerm_Term{Term: term_41040}
	_t1875 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1872, _t1873, _t1874}}
	result1042 := _t1875
	p.recordSpan(int(span_start1041), "Primitive")
	return result1042
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1046 := int64(p.spanStart())
	var _t1876 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1876 = 1
	} else {
		var _t1877 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1877 = 1
		} else {
			var _t1878 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1878 = 1
			} else {
				var _t1879 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1879 = 1
				} else {
					var _t1880 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1880 = 0
					} else {
						var _t1881 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1881 = 1
						} else {
							var _t1882 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1882 = 1
							} else {
								var _t1883 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1883 = 1
								} else {
									var _t1884 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1884 = 1
									} else {
										var _t1885 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1885 = 1
										} else {
											var _t1886 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1886 = 1
											} else {
												var _t1887 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1887 = 1
												} else {
													var _t1888 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1888 = 1
													} else {
														var _t1889 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1889 = 1
														} else {
															var _t1890 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1890 = 1
															} else {
																_t1890 = -1
															}
															_t1889 = _t1890
														}
														_t1888 = _t1889
													}
													_t1887 = _t1888
												}
												_t1886 = _t1887
											}
											_t1885 = _t1886
										}
										_t1884 = _t1885
									}
									_t1883 = _t1884
								}
								_t1882 = _t1883
							}
							_t1881 = _t1882
						}
						_t1880 = _t1881
					}
					_t1879 = _t1880
				}
				_t1878 = _t1879
			}
			_t1877 = _t1878
		}
		_t1876 = _t1877
	}
	prediction1043 := _t1876
	var _t1891 *pb.RelTerm
	if prediction1043 == 1 {
		_t1892 := p.parse_term()
		term1045 := _t1892
		_t1893 := &pb.RelTerm{}
		_t1893.RelTermType = &pb.RelTerm_Term{Term: term1045}
		_t1891 = _t1893
	} else {
		var _t1894 *pb.RelTerm
		if prediction1043 == 0 {
			_t1895 := p.parse_specialized_value()
			specialized_value1044 := _t1895
			_t1896 := &pb.RelTerm{}
			_t1896.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1044}
			_t1894 = _t1896
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1891 = _t1894
	}
	result1047 := _t1891
	p.recordSpan(int(span_start1046), "RelTerm")
	return result1047
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1049 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1897 := p.parse_raw_value()
	raw_value1048 := _t1897
	result1050 := raw_value1048
	p.recordSpan(int(span_start1049), "Value")
	return result1050
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1056 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1898 := p.parse_name()
	name1051 := _t1898
	xs1052 := []*pb.RelTerm{}
	cond1053 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1053 {
		_t1899 := p.parse_rel_term()
		item1054 := _t1899
		xs1052 = append(xs1052, item1054)
		cond1053 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1055 := xs1052
	p.consumeLiteral(")")
	_t1900 := &pb.RelAtom{Name: name1051, Terms: rel_terms1055}
	result1057 := _t1900
	p.recordSpan(int(span_start1056), "RelAtom")
	return result1057
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1060 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1901 := p.parse_term()
	term1058 := _t1901
	_t1902 := p.parse_term()
	term_31059 := _t1902
	p.consumeLiteral(")")
	_t1903 := &pb.Cast{Input: term1058, Result: term_31059}
	result1061 := _t1903
	p.recordSpan(int(span_start1060), "Cast")
	return result1061
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1062 := []*pb.Attribute{}
	cond1063 := p.matchLookaheadLiteral("(", 0)
	for cond1063 {
		_t1904 := p.parse_attribute()
		item1064 := _t1904
		xs1062 = append(xs1062, item1064)
		cond1063 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1065 := xs1062
	p.consumeLiteral(")")
	return attributes1065
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1071 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1905 := p.parse_name()
	name1066 := _t1905
	xs1067 := []*pb.Value{}
	cond1068 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1068 {
		_t1906 := p.parse_raw_value()
		item1069 := _t1906
		xs1067 = append(xs1067, item1069)
		cond1068 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1070 := xs1067
	p.consumeLiteral(")")
	_t1907 := &pb.Attribute{Name: name1066, Args: raw_values1070}
	result1072 := _t1907
	p.recordSpan(int(span_start1071), "Attribute")
	return result1072
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1079 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1073 := []*pb.RelationId{}
	cond1074 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1074 {
		_t1908 := p.parse_relation_id()
		item1075 := _t1908
		xs1073 = append(xs1073, item1075)
		cond1074 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1076 := xs1073
	_t1909 := p.parse_script()
	script1077 := _t1909
	var _t1910 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1911 := p.parse_attrs()
		_t1910 = _t1911
	}
	attrs1078 := _t1910
	p.consumeLiteral(")")
	_t1912 := attrs1078
	if attrs1078 == nil {
		_t1912 = []*pb.Attribute{}
	}
	_t1913 := &pb.Algorithm{Global: relation_ids1076, Body: script1077, Attrs: _t1912}
	result1080 := _t1913
	p.recordSpan(int(span_start1079), "Algorithm")
	return result1080
}

func (p *Parser) parse_script() *pb.Script {
	span_start1085 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1081 := []*pb.Construct{}
	cond1082 := p.matchLookaheadLiteral("(", 0)
	for cond1082 {
		_t1914 := p.parse_construct()
		item1083 := _t1914
		xs1081 = append(xs1081, item1083)
		cond1082 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1084 := xs1081
	p.consumeLiteral(")")
	_t1915 := &pb.Script{Constructs: constructs1084}
	result1086 := _t1915
	p.recordSpan(int(span_start1085), "Script")
	return result1086
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1090 := int64(p.spanStart())
	var _t1916 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1917 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1917 = 1
		} else {
			var _t1918 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1918 = 1
			} else {
				var _t1919 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1919 = 1
				} else {
					var _t1920 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1920 = 0
					} else {
						var _t1921 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1921 = 1
						} else {
							var _t1922 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1922 = 1
							} else {
								_t1922 = -1
							}
							_t1921 = _t1922
						}
						_t1920 = _t1921
					}
					_t1919 = _t1920
				}
				_t1918 = _t1919
			}
			_t1917 = _t1918
		}
		_t1916 = _t1917
	} else {
		_t1916 = -1
	}
	prediction1087 := _t1916
	var _t1923 *pb.Construct
	if prediction1087 == 1 {
		_t1924 := p.parse_instruction()
		instruction1089 := _t1924
		_t1925 := &pb.Construct{}
		_t1925.ConstructType = &pb.Construct_Instruction{Instruction: instruction1089}
		_t1923 = _t1925
	} else {
		var _t1926 *pb.Construct
		if prediction1087 == 0 {
			_t1927 := p.parse_loop()
			loop1088 := _t1927
			_t1928 := &pb.Construct{}
			_t1928.ConstructType = &pb.Construct_Loop{Loop: loop1088}
			_t1926 = _t1928
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1923 = _t1926
	}
	result1091 := _t1923
	p.recordSpan(int(span_start1090), "Construct")
	return result1091
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1095 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1929 := p.parse_init()
	init1092 := _t1929
	_t1930 := p.parse_script()
	script1093 := _t1930
	var _t1931 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1932 := p.parse_attrs()
		_t1931 = _t1932
	}
	attrs1094 := _t1931
	p.consumeLiteral(")")
	_t1933 := attrs1094
	if attrs1094 == nil {
		_t1933 = []*pb.Attribute{}
	}
	_t1934 := &pb.Loop{Init: init1092, Body: script1093, Attrs: _t1933}
	result1096 := _t1934
	p.recordSpan(int(span_start1095), "Loop")
	return result1096
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1097 := []*pb.Instruction{}
	cond1098 := p.matchLookaheadLiteral("(", 0)
	for cond1098 {
		_t1935 := p.parse_instruction()
		item1099 := _t1935
		xs1097 = append(xs1097, item1099)
		cond1098 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1100 := xs1097
	p.consumeLiteral(")")
	return instructions1100
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1107 := int64(p.spanStart())
	var _t1936 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1937 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1937 = 1
		} else {
			var _t1938 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1938 = 4
			} else {
				var _t1939 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1939 = 3
				} else {
					var _t1940 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1940 = 2
					} else {
						var _t1941 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1941 = 0
						} else {
							_t1941 = -1
						}
						_t1940 = _t1941
					}
					_t1939 = _t1940
				}
				_t1938 = _t1939
			}
			_t1937 = _t1938
		}
		_t1936 = _t1937
	} else {
		_t1936 = -1
	}
	prediction1101 := _t1936
	var _t1942 *pb.Instruction
	if prediction1101 == 4 {
		_t1943 := p.parse_monus_def()
		monus_def1106 := _t1943
		_t1944 := &pb.Instruction{}
		_t1944.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1106}
		_t1942 = _t1944
	} else {
		var _t1945 *pb.Instruction
		if prediction1101 == 3 {
			_t1946 := p.parse_monoid_def()
			monoid_def1105 := _t1946
			_t1947 := &pb.Instruction{}
			_t1947.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1105}
			_t1945 = _t1947
		} else {
			var _t1948 *pb.Instruction
			if prediction1101 == 2 {
				_t1949 := p.parse_break()
				break1104 := _t1949
				_t1950 := &pb.Instruction{}
				_t1950.InstrType = &pb.Instruction_Break{Break: break1104}
				_t1948 = _t1950
			} else {
				var _t1951 *pb.Instruction
				if prediction1101 == 1 {
					_t1952 := p.parse_upsert()
					upsert1103 := _t1952
					_t1953 := &pb.Instruction{}
					_t1953.InstrType = &pb.Instruction_Upsert{Upsert: upsert1103}
					_t1951 = _t1953
				} else {
					var _t1954 *pb.Instruction
					if prediction1101 == 0 {
						_t1955 := p.parse_assign()
						assign1102 := _t1955
						_t1956 := &pb.Instruction{}
						_t1956.InstrType = &pb.Instruction_Assign{Assign: assign1102}
						_t1954 = _t1956
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1951 = _t1954
				}
				_t1948 = _t1951
			}
			_t1945 = _t1948
		}
		_t1942 = _t1945
	}
	result1108 := _t1942
	p.recordSpan(int(span_start1107), "Instruction")
	return result1108
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1957 := p.parse_relation_id()
	relation_id1109 := _t1957
	_t1958 := p.parse_abstraction()
	abstraction1110 := _t1958
	var _t1959 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1960 := p.parse_attrs()
		_t1959 = _t1960
	}
	attrs1111 := _t1959
	p.consumeLiteral(")")
	_t1961 := attrs1111
	if attrs1111 == nil {
		_t1961 = []*pb.Attribute{}
	}
	_t1962 := &pb.Assign{Name: relation_id1109, Body: abstraction1110, Attrs: _t1961}
	result1113 := _t1962
	p.recordSpan(int(span_start1112), "Assign")
	return result1113
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1963 := p.parse_relation_id()
	relation_id1114 := _t1963
	_t1964 := p.parse_abstraction_with_arity()
	abstraction_with_arity1115 := _t1964
	var _t1965 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1966 := p.parse_attrs()
		_t1965 = _t1966
	}
	attrs1116 := _t1965
	p.consumeLiteral(")")
	_t1967 := attrs1116
	if attrs1116 == nil {
		_t1967 = []*pb.Attribute{}
	}
	_t1968 := &pb.Upsert{Name: relation_id1114, Body: abstraction_with_arity1115[0].(*pb.Abstraction), Attrs: _t1967, ValueArity: abstraction_with_arity1115[1].(int64)}
	result1118 := _t1968
	p.recordSpan(int(span_start1117), "Upsert")
	return result1118
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1969 := p.parse_bindings()
	bindings1119 := _t1969
	_t1970 := p.parse_formula()
	formula1120 := _t1970
	p.consumeLiteral(")")
	_t1971 := &pb.Abstraction{Vars: listConcat(bindings1119[0].([]*pb.Binding), bindings1119[1].([]*pb.Binding)), Value: formula1120}
	return []interface{}{_t1971, int64(len(bindings1119[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1972 := p.parse_relation_id()
	relation_id1121 := _t1972
	_t1973 := p.parse_abstraction()
	abstraction1122 := _t1973
	var _t1974 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1975 := p.parse_attrs()
		_t1974 = _t1975
	}
	attrs1123 := _t1974
	p.consumeLiteral(")")
	_t1976 := attrs1123
	if attrs1123 == nil {
		_t1976 = []*pb.Attribute{}
	}
	_t1977 := &pb.Break{Name: relation_id1121, Body: abstraction1122, Attrs: _t1976}
	result1125 := _t1977
	p.recordSpan(int(span_start1124), "Break")
	return result1125
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1130 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1978 := p.parse_monoid()
	monoid1126 := _t1978
	_t1979 := p.parse_relation_id()
	relation_id1127 := _t1979
	_t1980 := p.parse_abstraction_with_arity()
	abstraction_with_arity1128 := _t1980
	var _t1981 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1982 := p.parse_attrs()
		_t1981 = _t1982
	}
	attrs1129 := _t1981
	p.consumeLiteral(")")
	_t1983 := attrs1129
	if attrs1129 == nil {
		_t1983 = []*pb.Attribute{}
	}
	_t1984 := &pb.MonoidDef{Monoid: monoid1126, Name: relation_id1127, Body: abstraction_with_arity1128[0].(*pb.Abstraction), Attrs: _t1983, ValueArity: abstraction_with_arity1128[1].(int64)}
	result1131 := _t1984
	p.recordSpan(int(span_start1130), "MonoidDef")
	return result1131
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1137 := int64(p.spanStart())
	var _t1985 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1986 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1986 = 3
		} else {
			var _t1987 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1987 = 0
			} else {
				var _t1988 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1988 = 1
				} else {
					var _t1989 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1989 = 2
					} else {
						_t1989 = -1
					}
					_t1988 = _t1989
				}
				_t1987 = _t1988
			}
			_t1986 = _t1987
		}
		_t1985 = _t1986
	} else {
		_t1985 = -1
	}
	prediction1132 := _t1985
	var _t1990 *pb.Monoid
	if prediction1132 == 3 {
		_t1991 := p.parse_sum_monoid()
		sum_monoid1136 := _t1991
		_t1992 := &pb.Monoid{}
		_t1992.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1136}
		_t1990 = _t1992
	} else {
		var _t1993 *pb.Monoid
		if prediction1132 == 2 {
			_t1994 := p.parse_max_monoid()
			max_monoid1135 := _t1994
			_t1995 := &pb.Monoid{}
			_t1995.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1135}
			_t1993 = _t1995
		} else {
			var _t1996 *pb.Monoid
			if prediction1132 == 1 {
				_t1997 := p.parse_min_monoid()
				min_monoid1134 := _t1997
				_t1998 := &pb.Monoid{}
				_t1998.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1134}
				_t1996 = _t1998
			} else {
				var _t1999 *pb.Monoid
				if prediction1132 == 0 {
					_t2000 := p.parse_or_monoid()
					or_monoid1133 := _t2000
					_t2001 := &pb.Monoid{}
					_t2001.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1133}
					_t1999 = _t2001
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1996 = _t1999
			}
			_t1993 = _t1996
		}
		_t1990 = _t1993
	}
	result1138 := _t1990
	p.recordSpan(int(span_start1137), "Monoid")
	return result1138
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1139 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t2002 := &pb.OrMonoid{}
	result1140 := _t2002
	p.recordSpan(int(span_start1139), "OrMonoid")
	return result1140
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1142 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t2003 := p.parse_type()
	type1141 := _t2003
	p.consumeLiteral(")")
	_t2004 := &pb.MinMonoid{Type: type1141}
	result1143 := _t2004
	p.recordSpan(int(span_start1142), "MinMonoid")
	return result1143
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1145 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t2005 := p.parse_type()
	type1144 := _t2005
	p.consumeLiteral(")")
	_t2006 := &pb.MaxMonoid{Type: type1144}
	result1146 := _t2006
	p.recordSpan(int(span_start1145), "MaxMonoid")
	return result1146
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1148 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t2007 := p.parse_type()
	type1147 := _t2007
	p.consumeLiteral(")")
	_t2008 := &pb.SumMonoid{Type: type1147}
	result1149 := _t2008
	p.recordSpan(int(span_start1148), "SumMonoid")
	return result1149
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1154 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t2009 := p.parse_monoid()
	monoid1150 := _t2009
	_t2010 := p.parse_relation_id()
	relation_id1151 := _t2010
	_t2011 := p.parse_abstraction_with_arity()
	abstraction_with_arity1152 := _t2011
	var _t2012 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2013 := p.parse_attrs()
		_t2012 = _t2013
	}
	attrs1153 := _t2012
	p.consumeLiteral(")")
	_t2014 := attrs1153
	if attrs1153 == nil {
		_t2014 = []*pb.Attribute{}
	}
	_t2015 := &pb.MonusDef{Monoid: monoid1150, Name: relation_id1151, Body: abstraction_with_arity1152[0].(*pb.Abstraction), Attrs: _t2014, ValueArity: abstraction_with_arity1152[1].(int64)}
	result1155 := _t2015
	p.recordSpan(int(span_start1154), "MonusDef")
	return result1155
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1160 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2016 := p.parse_relation_id()
	relation_id1156 := _t2016
	_t2017 := p.parse_abstraction()
	abstraction1157 := _t2017
	_t2018 := p.parse_functional_dependency_keys()
	functional_dependency_keys1158 := _t2018
	_t2019 := p.parse_functional_dependency_values()
	functional_dependency_values1159 := _t2019
	p.consumeLiteral(")")
	_t2020 := &pb.FunctionalDependency{Guard: abstraction1157, Keys: functional_dependency_keys1158, Values: functional_dependency_values1159}
	_t2021 := &pb.Constraint{Name: relation_id1156}
	_t2021.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2020}
	result1161 := _t2021
	p.recordSpan(int(span_start1160), "Constraint")
	return result1161
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1162 := []*pb.Var{}
	cond1163 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1163 {
		_t2022 := p.parse_var()
		item1164 := _t2022
		xs1162 = append(xs1162, item1164)
		cond1163 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1165 := xs1162
	p.consumeLiteral(")")
	return vars1165
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1166 := []*pb.Var{}
	cond1167 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1167 {
		_t2023 := p.parse_var()
		item1168 := _t2023
		xs1166 = append(xs1166, item1168)
		cond1167 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1169 := xs1166
	p.consumeLiteral(")")
	return vars1169
}

func (p *Parser) parse_data() *pb.Data {
	span_start1175 := int64(p.spanStart())
	var _t2024 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2025 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2025 = 3
		} else {
			var _t2026 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2026 = 0
			} else {
				var _t2027 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2027 = 2
				} else {
					var _t2028 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2028 = 1
					} else {
						_t2028 = -1
					}
					_t2027 = _t2028
				}
				_t2026 = _t2027
			}
			_t2025 = _t2026
		}
		_t2024 = _t2025
	} else {
		_t2024 = -1
	}
	prediction1170 := _t2024
	var _t2029 *pb.Data
	if prediction1170 == 3 {
		_t2030 := p.parse_iceberg_data()
		iceberg_data1174 := _t2030
		_t2031 := &pb.Data{}
		_t2031.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1174}
		_t2029 = _t2031
	} else {
		var _t2032 *pb.Data
		if prediction1170 == 2 {
			_t2033 := p.parse_csv_data()
			csv_data1173 := _t2033
			_t2034 := &pb.Data{}
			_t2034.DataType = &pb.Data_CsvData{CsvData: csv_data1173}
			_t2032 = _t2034
		} else {
			var _t2035 *pb.Data
			if prediction1170 == 1 {
				_t2036 := p.parse_betree_relation()
				betree_relation1172 := _t2036
				_t2037 := &pb.Data{}
				_t2037.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1172}
				_t2035 = _t2037
			} else {
				var _t2038 *pb.Data
				if prediction1170 == 0 {
					_t2039 := p.parse_edb()
					edb1171 := _t2039
					_t2040 := &pb.Data{}
					_t2040.DataType = &pb.Data_Edb{Edb: edb1171}
					_t2038 = _t2040
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2035 = _t2038
			}
			_t2032 = _t2035
		}
		_t2029 = _t2032
	}
	result1176 := _t2029
	p.recordSpan(int(span_start1175), "Data")
	return result1176
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1180 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2041 := p.parse_relation_id()
	relation_id1177 := _t2041
	_t2042 := p.parse_edb_path()
	edb_path1178 := _t2042
	_t2043 := p.parse_edb_types()
	edb_types1179 := _t2043
	p.consumeLiteral(")")
	_t2044 := &pb.EDB{TargetId: relation_id1177, Path: edb_path1178, Types: edb_types1179}
	result1181 := _t2044
	p.recordSpan(int(span_start1180), "EDB")
	return result1181
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1182 := []string{}
	cond1183 := p.matchLookaheadTerminal("STRING", 0)
	for cond1183 {
		item1184 := p.consumeTerminal("STRING").Value.str
		xs1182 = append(xs1182, item1184)
		cond1183 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1185 := xs1182
	p.consumeLiteral("]")
	return strings1185
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1186 := []*pb.Type{}
	cond1187 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1187 {
		_t2045 := p.parse_type()
		item1188 := _t2045
		xs1186 = append(xs1186, item1188)
		cond1187 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1189 := xs1186
	p.consumeLiteral("]")
	return types1189
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1192 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2046 := p.parse_relation_id()
	relation_id1190 := _t2046
	_t2047 := p.parse_betree_info()
	betree_info1191 := _t2047
	p.consumeLiteral(")")
	_t2048 := &pb.BeTreeRelation{Name: relation_id1190, RelationInfo: betree_info1191}
	result1193 := _t2048
	p.recordSpan(int(span_start1192), "BeTreeRelation")
	return result1193
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1197 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2049 := p.parse_betree_info_key_types()
	betree_info_key_types1194 := _t2049
	_t2050 := p.parse_betree_info_value_types()
	betree_info_value_types1195 := _t2050
	_t2051 := p.parse_config_dict()
	config_dict1196 := _t2051
	p.consumeLiteral(")")
	_t2052 := p.construct_betree_info(betree_info_key_types1194, betree_info_value_types1195, config_dict1196)
	result1198 := _t2052
	p.recordSpan(int(span_start1197), "BeTreeInfo")
	return result1198
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1199 := []*pb.Type{}
	cond1200 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1200 {
		_t2053 := p.parse_type()
		item1201 := _t2053
		xs1199 = append(xs1199, item1201)
		cond1200 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1202 := xs1199
	p.consumeLiteral(")")
	return types1202
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1203 := []*pb.Type{}
	cond1204 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1204 {
		_t2054 := p.parse_type()
		item1205 := _t2054
		xs1203 = append(xs1203, item1205)
		cond1204 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1206 := xs1203
	p.consumeLiteral(")")
	return types1206
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2055 := p.parse_csvlocator()
	csvlocator1207 := _t2055
	_t2056 := p.parse_csv_config()
	csv_config1208 := _t2056
	var _t2057 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2058 := p.parse_gnf_columns()
		_t2057 = _t2058
	}
	gnf_columns1209 := _t2057
	var _t2059 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2060 := p.parse_target_relations()
		_t2059 = _t2060
	}
	target_relations1210 := _t2059
	_t2061 := p.parse_csv_asof()
	csv_asof1211 := _t2061
	p.consumeLiteral(")")
	_t2062 := p.construct_csv_data(csvlocator1207, csv_config1208, gnf_columns1209, target_relations1210, csv_asof1211)
	result1213 := _t2062
	p.recordSpan(int(span_start1212), "CSVData")
	return result1213
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1216 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2063 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2064 := p.parse_csv_locator_paths()
		_t2063 = _t2064
	}
	csv_locator_paths1214 := _t2063
	var _t2065 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2066 := p.parse_csv_locator_inline_data()
		_t2065 = ptr(_t2066)
	}
	csv_locator_inline_data1215 := _t2065
	p.consumeLiteral(")")
	_t2067 := csv_locator_paths1214
	if csv_locator_paths1214 == nil {
		_t2067 = []string{}
	}
	_t2068 := &pb.CSVLocator{Paths: _t2067, InlineData: []byte(deref(csv_locator_inline_data1215, ""))}
	result1217 := _t2068
	p.recordSpan(int(span_start1216), "CSVLocator")
	return result1217
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1218 := []string{}
	cond1219 := p.matchLookaheadTerminal("STRING", 0)
	for cond1219 {
		item1220 := p.consumeTerminal("STRING").Value.str
		xs1218 = append(xs1218, item1220)
		cond1219 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1221 := xs1218
	p.consumeLiteral(")")
	return strings1221
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1222 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1222
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1225 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2069 := p.parse_config_dict()
	config_dict1223 := _t2069
	var _t2070 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2071 := p.parse__storage_integration()
		_t2070 = _t2071
	}
	_storage_integration1224 := _t2070
	p.consumeLiteral(")")
	_t2072 := p.construct_csv_config(config_dict1223, _storage_integration1224)
	result1226 := _t2072
	p.recordSpan(int(span_start1225), "CSVConfig")
	return result1226
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2073 := p.parse_config_dict()
	config_dict1227 := _t2073
	p.consumeLiteral(")")
	return config_dict1227
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1228 := []*pb.GNFColumn{}
	cond1229 := p.matchLookaheadLiteral("(", 0)
	for cond1229 {
		_t2074 := p.parse_gnf_column()
		item1230 := _t2074
		xs1228 = append(xs1228, item1230)
		cond1229 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1231 := xs1228
	p.consumeLiteral(")")
	return gnf_columns1231
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1238 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2075 := p.parse_gnf_column_path()
	gnf_column_path1232 := _t2075
	var _t2076 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2077 := p.parse_relation_id()
		_t2076 = _t2077
	}
	relation_id1233 := _t2076
	p.consumeLiteral("[")
	xs1234 := []*pb.Type{}
	cond1235 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1235 {
		_t2078 := p.parse_type()
		item1236 := _t2078
		xs1234 = append(xs1234, item1236)
		cond1235 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1237 := xs1234
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2079 := &pb.GNFColumn{ColumnPath: gnf_column_path1232, TargetId: relation_id1233, Types: types1237}
	result1239 := _t2079
	p.recordSpan(int(span_start1238), "GNFColumn")
	return result1239
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2080 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2080 = 1
	} else {
		var _t2081 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2081 = 0
		} else {
			_t2081 = -1
		}
		_t2080 = _t2081
	}
	prediction1240 := _t2080
	var _t2082 []string
	if prediction1240 == 1 {
		p.consumeLiteral("[")
		xs1242 := []string{}
		cond1243 := p.matchLookaheadTerminal("STRING", 0)
		for cond1243 {
			item1244 := p.consumeTerminal("STRING").Value.str
			xs1242 = append(xs1242, item1244)
			cond1243 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1245 := xs1242
		p.consumeLiteral("]")
		_t2082 = strings1245
	} else {
		var _t2083 []string
		if prediction1240 == 0 {
			string1241 := p.consumeTerminal("STRING").Value.str
			_ = string1241
			_t2083 = []string{string1241}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2082 = _t2083
	}
	return _t2082
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1249 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2084 := p.parse_relation_keys()
	relation_keys1246 := _t2084
	_t2085 := p.parse_relation_body()
	relation_body1247 := _t2085
	var _t2086 *pb.RelationId
	if p.matchLookaheadLiteral("(", 0) {
		_t2087 := p.parse_load_errors()
		_t2086 = _t2087
	}
	load_errors1248 := _t2086
	p.consumeLiteral(")")
	_t2088 := p.construct_relations(relation_keys1246, relation_body1247, load_errors1248)
	result1250 := _t2088
	p.recordSpan(int(span_start1249), "TargetRelations")
	return result1250
}

func (p *Parser) parse_relation_keys() []interface{} {
	var _t2089 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2090 int64
		if p.matchLookaheadLiteral("keys", 1) {
			var _t2091 int64
			if p.matchLookaheadLiteral("synthetic", 2) {
				_t2091 = 1
			} else {
				var _t2092 int64
				if p.matchLookaheadLiteral(")", 2) {
					_t2092 = 0
				} else {
					var _t2093 int64
					if p.matchLookaheadLiteral("(", 2) {
						_t2093 = 0
					} else {
						_t2093 = -1
					}
					_t2092 = _t2093
				}
				_t2091 = _t2092
			}
			_t2090 = _t2091
		} else {
			_t2090 = -1
		}
		_t2089 = _t2090
	} else {
		_t2089 = -1
	}
	prediction1251 := _t2089
	var _t2094 []interface{}
	if prediction1251 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("keys")
		p.consumeLiteral("synthetic")
		p.consumeLiteral(")")
		_t2094 = []interface{}{[]*pb.NamedColumn{}, true}
	} else {
		var _t2095 []interface{}
		if prediction1251 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("keys")
			xs1252 := []*pb.NamedColumn{}
			cond1253 := p.matchLookaheadLiteral("(", 0)
			for cond1253 {
				_t2096 := p.parse_named_column()
				item1254 := _t2096
				xs1252 = append(xs1252, item1254)
				cond1253 = p.matchLookaheadLiteral("(", 0)
			}
			named_columns1255 := xs1252
			p.consumeLiteral(")")
			_t2095 = []interface{}{named_columns1255, false}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_keys", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2094 = _t2095
	}
	return _t2094
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1258 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1256 := p.consumeTerminal("STRING").Value.str
	_t2097 := p.parse_type()
	type1257 := _t2097
	p.consumeLiteral(")")
	_t2098 := &pb.NamedColumn{Name: string1256, Type: type1257}
	result1259 := _t2098
	p.recordSpan(int(span_start1258), "NamedColumn")
	return result1259
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1264 := int64(p.spanStart())
	var _t2099 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2100 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2100 = 0
		} else {
			var _t2101 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2101 = 1
			} else {
				_t2101 = 0
			}
			_t2100 = _t2101
		}
		_t2099 = _t2100
	} else {
		_t2099 = 0
	}
	prediction1260 := _t2099
	var _t2102 *pb.TargetRelations
	if prediction1260 == 1 {
		_t2103 := p.parse_cdc_inserts()
		cdc_inserts1262 := _t2103
		_t2104 := p.parse_cdc_deletes()
		cdc_deletes1263 := _t2104
		_t2105 := p.construct_cdc_relations(cdc_inserts1262, cdc_deletes1263)
		_t2102 = _t2105
	} else {
		var _t2106 *pb.TargetRelations
		if prediction1260 == 0 {
			_t2107 := p.parse_non_cdc_relations()
			non_cdc_relations1261 := _t2107
			_t2108 := p.construct_non_cdc_relations(non_cdc_relations1261)
			_t2106 = _t2108
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2102 = _t2106
	}
	result1265 := _t2102
	p.recordSpan(int(span_start1264), "TargetRelations")
	return result1265
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1266 := []*pb.TargetRelation{}
	cond1267 := (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	for cond1267 {
		_t2109 := p.parse_target_relation()
		item1268 := _t2109
		xs1266 = append(xs1266, item1268)
		cond1267 = (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	}
	return xs1266
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1274 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2110 := p.parse_relation_id()
	relation_id1269 := _t2110
	xs1270 := []*pb.NamedColumn{}
	cond1271 := p.matchLookaheadLiteral("(", 0)
	for cond1271 {
		_t2111 := p.parse_named_column()
		item1272 := _t2111
		xs1270 = append(xs1270, item1272)
		cond1271 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1273 := xs1270
	p.consumeLiteral(")")
	_t2112 := &pb.TargetRelation{TargetId: relation_id1269, Values: named_columns1273}
	result1275 := _t2112
	p.recordSpan(int(span_start1274), "TargetRelation")
	return result1275
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1276 := []*pb.TargetRelation{}
	cond1277 := p.matchLookaheadLiteral("(", 0)
	for cond1277 {
		_t2113 := p.parse_target_relation()
		item1278 := _t2113
		xs1276 = append(xs1276, item1278)
		cond1277 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1279 := xs1276
	p.consumeLiteral(")")
	return target_relations1279
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1280 := []*pb.TargetRelation{}
	cond1281 := p.matchLookaheadLiteral("(", 0)
	for cond1281 {
		_t2114 := p.parse_target_relation()
		item1282 := _t2114
		xs1280 = append(xs1280, item1282)
		cond1281 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1283 := xs1280
	p.consumeLiteral(")")
	return target_relations1283
}

func (p *Parser) parse_load_errors() *pb.RelationId {
	span_start1285 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("load_errors")
	_t2115 := p.parse_relation_id()
	relation_id1284 := _t2115
	p.consumeLiteral(")")
	result1286 := relation_id1284
	p.recordSpan(int(span_start1285), "RelationId")
	return result1286
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1287 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1287
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1294 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2116 := p.parse_iceberg_locator()
	iceberg_locator1288 := _t2116
	_t2117 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1289 := _t2117
	_t2118 := p.parse_gnf_columns()
	gnf_columns1290 := _t2118
	var _t2119 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2120 := p.parse_iceberg_from_snapshot()
		_t2119 = ptr(_t2120)
	}
	iceberg_from_snapshot1291 := _t2119
	var _t2121 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2122 := p.parse_iceberg_to_snapshot()
		_t2121 = ptr(_t2122)
	}
	iceberg_to_snapshot1292 := _t2121
	_t2123 := p.parse_boolean_value()
	boolean_value1293 := _t2123
	p.consumeLiteral(")")
	_t2124 := p.construct_iceberg_data(iceberg_locator1288, iceberg_catalog_config1289, gnf_columns1290, iceberg_from_snapshot1291, iceberg_to_snapshot1292, boolean_value1293)
	result1295 := _t2124
	p.recordSpan(int(span_start1294), "IcebergData")
	return result1295
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1299 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2125 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1296 := _t2125
	_t2126 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1297 := _t2126
	_t2127 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1298 := _t2127
	p.consumeLiteral(")")
	_t2128 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1296, Namespace: iceberg_locator_namespace1297, Warehouse: iceberg_locator_warehouse1298}
	result1300 := _t2128
	p.recordSpan(int(span_start1299), "IcebergLocator")
	return result1300
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1301 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1301
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1302 := []string{}
	cond1303 := p.matchLookaheadTerminal("STRING", 0)
	for cond1303 {
		item1304 := p.consumeTerminal("STRING").Value.str
		xs1302 = append(xs1302, item1304)
		cond1303 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1305 := xs1302
	p.consumeLiteral(")")
	return strings1305
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1306 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1306
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1311 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2129 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1307 := _t2129
	var _t2130 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2131 := p.parse_iceberg_catalog_config_scope()
		_t2130 = ptr(_t2131)
	}
	iceberg_catalog_config_scope1308 := _t2130
	_t2132 := p.parse_iceberg_properties()
	iceberg_properties1309 := _t2132
	_t2133 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1310 := _t2133
	p.consumeLiteral(")")
	_t2134 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1307, iceberg_catalog_config_scope1308, iceberg_properties1309, iceberg_auth_properties1310)
	result1312 := _t2134
	p.recordSpan(int(span_start1311), "IcebergCatalogConfig")
	return result1312
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1313 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1313
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1314 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1314
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1315 := [][]interface{}{}
	cond1316 := p.matchLookaheadLiteral("(", 0)
	for cond1316 {
		_t2135 := p.parse_iceberg_property_entry()
		item1317 := _t2135
		xs1315 = append(xs1315, item1317)
		cond1316 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1318 := xs1315
	p.consumeLiteral(")")
	return iceberg_property_entrys1318
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1319 := p.consumeTerminal("STRING").Value.str
	string_31320 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1319, string_31320}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1321 := [][]interface{}{}
	cond1322 := p.matchLookaheadLiteral("(", 0)
	for cond1322 {
		_t2136 := p.parse_iceberg_masked_property_entry()
		item1323 := _t2136
		xs1321 = append(xs1321, item1323)
		cond1322 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1324 := xs1321
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1324
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1325 := p.consumeTerminal("STRING").Value.str
	string_31326 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1325, string_31326}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1327 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1327
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1328 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1328
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1330 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2137 := p.parse_fragment_id()
	fragment_id1329 := _t2137
	p.consumeLiteral(")")
	_t2138 := &pb.Undefine{FragmentId: fragment_id1329}
	result1331 := _t2138
	p.recordSpan(int(span_start1330), "Undefine")
	return result1331
}

func (p *Parser) parse_context() *pb.Context {
	span_start1336 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1332 := []*pb.RelationId{}
	cond1333 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1333 {
		_t2139 := p.parse_relation_id()
		item1334 := _t2139
		xs1332 = append(xs1332, item1334)
		cond1333 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1335 := xs1332
	p.consumeLiteral(")")
	_t2140 := &pb.Context{Relations: relation_ids1335}
	result1337 := _t2140
	p.recordSpan(int(span_start1336), "Context")
	return result1337
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1343 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2141 := p.parse_edb_path()
	edb_path1338 := _t2141
	xs1339 := []*pb.SnapshotMapping{}
	cond1340 := p.matchLookaheadLiteral("[", 0)
	for cond1340 {
		_t2142 := p.parse_snapshot_mapping()
		item1341 := _t2142
		xs1339 = append(xs1339, item1341)
		cond1340 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1342 := xs1339
	p.consumeLiteral(")")
	_t2143 := &pb.Snapshot{Prefix: edb_path1338, Mappings: snapshot_mappings1342}
	result1344 := _t2143
	p.recordSpan(int(span_start1343), "Snapshot")
	return result1344
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1347 := int64(p.spanStart())
	_t2144 := p.parse_edb_path()
	edb_path1345 := _t2144
	_t2145 := p.parse_relation_id()
	relation_id1346 := _t2145
	_t2146 := &pb.SnapshotMapping{DestinationPath: edb_path1345, SourceRelation: relation_id1346}
	result1348 := _t2146
	p.recordSpan(int(span_start1347), "SnapshotMapping")
	return result1348
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1349 := []*pb.Read{}
	cond1350 := p.matchLookaheadLiteral("(", 0)
	for cond1350 {
		_t2147 := p.parse_read()
		item1351 := _t2147
		xs1349 = append(xs1349, item1351)
		cond1350 = p.matchLookaheadLiteral("(", 0)
	}
	reads1352 := xs1349
	p.consumeLiteral(")")
	return reads1352
}

func (p *Parser) parse_read() *pb.Read {
	span_start1359 := int64(p.spanStart())
	var _t2148 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2149 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2149 = 2
		} else {
			var _t2150 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2150 = 1
			} else {
				var _t2151 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2151 = 4
				} else {
					var _t2152 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2152 = 4
					} else {
						var _t2153 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2153 = 0
						} else {
							var _t2154 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2154 = 3
							} else {
								_t2154 = -1
							}
							_t2153 = _t2154
						}
						_t2152 = _t2153
					}
					_t2151 = _t2152
				}
				_t2150 = _t2151
			}
			_t2149 = _t2150
		}
		_t2148 = _t2149
	} else {
		_t2148 = -1
	}
	prediction1353 := _t2148
	var _t2155 *pb.Read
	if prediction1353 == 4 {
		_t2156 := p.parse_export()
		export1358 := _t2156
		_t2157 := &pb.Read{}
		_t2157.ReadType = &pb.Read_Export{Export: export1358}
		_t2155 = _t2157
	} else {
		var _t2158 *pb.Read
		if prediction1353 == 3 {
			_t2159 := p.parse_abort()
			abort1357 := _t2159
			_t2160 := &pb.Read{}
			_t2160.ReadType = &pb.Read_Abort{Abort: abort1357}
			_t2158 = _t2160
		} else {
			var _t2161 *pb.Read
			if prediction1353 == 2 {
				_t2162 := p.parse_what_if()
				what_if1356 := _t2162
				_t2163 := &pb.Read{}
				_t2163.ReadType = &pb.Read_WhatIf{WhatIf: what_if1356}
				_t2161 = _t2163
			} else {
				var _t2164 *pb.Read
				if prediction1353 == 1 {
					_t2165 := p.parse_output()
					output1355 := _t2165
					_t2166 := &pb.Read{}
					_t2166.ReadType = &pb.Read_Output{Output: output1355}
					_t2164 = _t2166
				} else {
					var _t2167 *pb.Read
					if prediction1353 == 0 {
						_t2168 := p.parse_demand()
						demand1354 := _t2168
						_t2169 := &pb.Read{}
						_t2169.ReadType = &pb.Read_Demand{Demand: demand1354}
						_t2167 = _t2169
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2164 = _t2167
				}
				_t2161 = _t2164
			}
			_t2158 = _t2161
		}
		_t2155 = _t2158
	}
	result1360 := _t2155
	p.recordSpan(int(span_start1359), "Read")
	return result1360
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1362 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2170 := p.parse_relation_id()
	relation_id1361 := _t2170
	p.consumeLiteral(")")
	_t2171 := &pb.Demand{RelationId: relation_id1361}
	result1363 := _t2171
	p.recordSpan(int(span_start1362), "Demand")
	return result1363
}

func (p *Parser) parse_output() *pb.Output {
	span_start1366 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2172 := p.parse_name()
	name1364 := _t2172
	_t2173 := p.parse_relation_id()
	relation_id1365 := _t2173
	p.consumeLiteral(")")
	_t2174 := &pb.Output{Name: name1364, RelationId: relation_id1365}
	result1367 := _t2174
	p.recordSpan(int(span_start1366), "Output")
	return result1367
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1370 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2175 := p.parse_name()
	name1368 := _t2175
	_t2176 := p.parse_epoch()
	epoch1369 := _t2176
	p.consumeLiteral(")")
	_t2177 := &pb.WhatIf{Branch: name1368, Epoch: epoch1369}
	result1371 := _t2177
	p.recordSpan(int(span_start1370), "WhatIf")
	return result1371
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1374 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2178 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2179 := p.parse_name()
		_t2178 = ptr(_t2179)
	}
	name1372 := _t2178
	_t2180 := p.parse_relation_id()
	relation_id1373 := _t2180
	p.consumeLiteral(")")
	_t2181 := &pb.Abort{Name: deref(name1372, "abort"), RelationId: relation_id1373}
	result1375 := _t2181
	p.recordSpan(int(span_start1374), "Abort")
	return result1375
}

func (p *Parser) parse_export() *pb.Export {
	span_start1379 := int64(p.spanStart())
	var _t2182 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2183 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2183 = 1
		} else {
			var _t2184 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2184 = 0
			} else {
				_t2184 = -1
			}
			_t2183 = _t2184
		}
		_t2182 = _t2183
	} else {
		_t2182 = -1
	}
	prediction1376 := _t2182
	var _t2185 *pb.Export
	if prediction1376 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2186 := p.parse_export_iceberg_config()
		export_iceberg_config1378 := _t2186
		p.consumeLiteral(")")
		_t2187 := &pb.Export{}
		_t2187.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1378}
		_t2185 = _t2187
	} else {
		var _t2188 *pb.Export
		if prediction1376 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2189 := p.parse_export_csv_config()
			export_csv_config1377 := _t2189
			p.consumeLiteral(")")
			_t2190 := &pb.Export{}
			_t2190.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1377}
			_t2188 = _t2190
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2185 = _t2188
	}
	result1380 := _t2185
	p.recordSpan(int(span_start1379), "Export")
	return result1380
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1388 := int64(p.spanStart())
	var _t2191 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2192 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2192 = 0
		} else {
			var _t2193 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2193 = 1
			} else {
				_t2193 = -1
			}
			_t2192 = _t2193
		}
		_t2191 = _t2192
	} else {
		_t2191 = -1
	}
	prediction1381 := _t2191
	var _t2194 *pb.ExportCSVConfig
	if prediction1381 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2195 := p.parse_export_csv_path()
		export_csv_path1385 := _t2195
		_t2196 := p.parse_export_csv_columns_list()
		export_csv_columns_list1386 := _t2196
		_t2197 := p.parse_config_dict()
		config_dict1387 := _t2197
		p.consumeLiteral(")")
		_t2198 := p.construct_export_csv_config(export_csv_path1385, export_csv_columns_list1386, config_dict1387)
		_t2194 = _t2198
	} else {
		var _t2199 *pb.ExportCSVConfig
		if prediction1381 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2200 := p.parse_export_csv_output_location()
			export_csv_output_location1382 := _t2200
			_t2201 := p.parse_export_csv_source()
			export_csv_source1383 := _t2201
			_t2202 := p.parse_csv_config()
			csv_config1384 := _t2202
			p.consumeLiteral(")")
			_t2203 := p.construct_export_csv_config_with_location(export_csv_output_location1382, export_csv_source1383, csv_config1384)
			_t2199 = _t2203
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2194 = _t2199
	}
	result1389 := _t2194
	p.recordSpan(int(span_start1388), "ExportCSVConfig")
	return result1389
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2204 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2205 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2205 = 1
		} else {
			var _t2206 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2206 = 0
			} else {
				_t2206 = -1
			}
			_t2205 = _t2206
		}
		_t2204 = _t2205
	} else {
		_t2204 = -1
	}
	prediction1390 := _t2204
	var _t2207 []interface{}
	if prediction1390 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2208 := p.parse_name()
		name1392 := _t2208
		p.consumeLiteral(")")
		_t2207 = []interface{}{"", name1392}
	} else {
		var _t2209 []interface{}
		if prediction1390 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1391 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2209 = []interface{}{string1391, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2207 = _t2209
	}
	return _t2207
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1399 := int64(p.spanStart())
	var _t2210 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2211 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2211 = 1
		} else {
			var _t2212 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2212 = 0
			} else {
				_t2212 = -1
			}
			_t2211 = _t2212
		}
		_t2210 = _t2211
	} else {
		_t2210 = -1
	}
	prediction1393 := _t2210
	var _t2213 *pb.ExportCSVSource
	if prediction1393 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2214 := p.parse_relation_id()
		relation_id1398 := _t2214
		p.consumeLiteral(")")
		_t2215 := &pb.ExportCSVSource{}
		_t2215.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1398}
		_t2213 = _t2215
	} else {
		var _t2216 *pb.ExportCSVSource
		if prediction1393 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1394 := []*pb.ExportCSVColumn{}
			cond1395 := p.matchLookaheadLiteral("(", 0)
			for cond1395 {
				_t2217 := p.parse_export_csv_column()
				item1396 := _t2217
				xs1394 = append(xs1394, item1396)
				cond1395 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1397 := xs1394
			p.consumeLiteral(")")
			_t2218 := &pb.ExportCSVColumns{Columns: export_csv_columns1397}
			_t2219 := &pb.ExportCSVSource{}
			_t2219.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2218}
			_t2216 = _t2219
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2213 = _t2216
	}
	result1400 := _t2213
	p.recordSpan(int(span_start1399), "ExportCSVSource")
	return result1400
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1403 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1401 := p.consumeTerminal("STRING").Value.str
	_t2220 := p.parse_relation_id()
	relation_id1402 := _t2220
	p.consumeLiteral(")")
	_t2221 := &pb.ExportCSVColumn{ColumnName: string1401, ColumnData: relation_id1402}
	result1404 := _t2221
	p.recordSpan(int(span_start1403), "ExportCSVColumn")
	return result1404
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1405 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1405
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1406 := []*pb.ExportCSVColumn{}
	cond1407 := p.matchLookaheadLiteral("(", 0)
	for cond1407 {
		_t2222 := p.parse_export_csv_column()
		item1408 := _t2222
		xs1406 = append(xs1406, item1408)
		cond1407 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1409 := xs1406
	p.consumeLiteral(")")
	return export_csv_columns1409
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1415 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2223 := p.parse_iceberg_locator()
	iceberg_locator1410 := _t2223
	_t2224 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1411 := _t2224
	_t2225 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1412 := _t2225
	_t2226 := p.parse_iceberg_table_properties()
	iceberg_table_properties1413 := _t2226
	var _t2227 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2228 := p.parse_config_dict()
		_t2227 = _t2228
	}
	config_dict1414 := _t2227
	p.consumeLiteral(")")
	_t2229 := p.construct_export_iceberg_config_full(iceberg_locator1410, iceberg_catalog_config1411, export_iceberg_table_def1412, iceberg_table_properties1413, config_dict1414)
	result1416 := _t2229
	p.recordSpan(int(span_start1415), "ExportIcebergConfig")
	return result1416
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1418 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2230 := p.parse_relation_id()
	relation_id1417 := _t2230
	p.consumeLiteral(")")
	result1419 := relation_id1417
	p.recordSpan(int(span_start1418), "RelationId")
	return result1419
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1420 := [][]interface{}{}
	cond1421 := p.matchLookaheadLiteral("(", 0)
	for cond1421 {
		_t2231 := p.parse_iceberg_property_entry()
		item1422 := _t2231
		xs1420 = append(xs1420, item1422)
		cond1421 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1423 := xs1420
	p.consumeLiteral(")")
	return iceberg_property_entrys1423
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
