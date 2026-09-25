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
	var _t2246 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2246
	var _t2247 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2247
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2248 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2248
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2249 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2249
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2250 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2250
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2251 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2251
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2252 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2252
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2253 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2253
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2254 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2254
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2255 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2255
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2256 := &pb.PlainTargets{Targets: targets}
	_t2257 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2257.Body = &pb.TargetRelations_Plain{Plain: _t2256}
	return _t2257
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2258 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2259 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2259.Body = &pb.TargetRelations_Cdc{Cdc: _t2258}
	return _t2259
}

func (p *Parser) construct_relations(keys []interface{}, body *pb.TargetRelations, load_errors_opt *pb.RelationId) *pb.TargetRelations {
	var _t2260 interface{}
	if hasProtoField(body, "plain") {
		_t2261 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
		_t2261.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2261
	}
	_ = _t2260
	_t2262 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool), LoadErrors: load_errors_opt}
	_t2262.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2262
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2263 := columns_opt
	if columns_opt == nil {
		_t2263 = []*pb.GNFColumn{}
	}
	_t2264 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2263, Asof: asof, Relations: relations_opt}
	return _t2264
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2265 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2265
	_t2266 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2266
	_t2267 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2267
	_t2268 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2268
	_t2269 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2269
	_t2270 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2270
	_t2271 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2271
	_t2272 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2272
	_t2273 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2273
	_t2274 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2274
	_t2275 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2275
	_t2276 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2276
	_t2277 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2277
	_t2278 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2278
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2279 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2279
	config := dictFromList(storage_integration_opt)
	_t2280 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2281 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2282 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2283 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2284 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2285 := &pb.StorageIntegration{Provider: _t2280, AzureSasToken: _t2281, S3Region: _t2282, S3AccessKeyId: _t2283, S3SecretAccessKey: _t2284}
	return _t2285
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2286 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2286
	_t2287 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2287
	_t2288 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2288
	_t2289 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2289
	_t2290 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2290
	_t2291 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2291
	_t2292 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2292
	_t2293 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2293
	_t2294 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2294
	_t2295 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2295.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2295.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2295
	_t2296 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2296
}

func (p *Parser) default_configure() *pb.Configure {
	_t2297 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2297
	_t2298 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2298
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
	_t2299 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2299
	_t2300 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2300
	config_values_pairs := [][]interface{}{}
	for _, pair := range config_dict {
		if (pair[0].(string) != "semantics_version" && pair[0].(string) != "ivm.maintenance_level") {
			config_values_pairs = append(config_values_pairs, pair)
		}
	}
	configuration_values := valueMapFromPairs(config_values_pairs)
	_t2301 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config, ConfigurationValues: configuration_values}
	return _t2301
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2302 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2302
	_t2303 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2303
	_t2304 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2304
	_t2305 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2305
	_t2306 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2306
	_t2307 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2307
	_t2308 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2308
	_t2309 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2309
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2310 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2310
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2311 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2311
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2312 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2312
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2313 := config_dict
	if config_dict == nil {
		_t2313 = [][]interface{}{}
	}
	cfg := dictFromList(_t2313)
	_t2314 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2314
	_t2315 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2315
	_t2316 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2316
	table_props := stringMapFromPairs(table_property_pairs)
	_t2317 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2317
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start722 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1432 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1433 := p.parse_configure()
		_t1432 = _t1433
	}
	configure716 := _t1432
	var _t1434 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1435 := p.parse_sync()
		_t1434 = _t1435
	}
	sync717 := _t1434
	xs718 := []*pb.Epoch{}
	cond719 := p.matchLookaheadLiteral("(", 0)
	for cond719 {
		_t1436 := p.parse_epoch()
		item720 := _t1436
		xs718 = append(xs718, item720)
		cond719 = p.matchLookaheadLiteral("(", 0)
	}
	epochs721 := xs718
	p.consumeLiteral(")")
	_t1437 := p.default_configure()
	_t1438 := configure716
	if configure716 == nil {
		_t1438 = _t1437
	}
	_t1439 := &pb.Transaction{Epochs: epochs721, Configure: _t1438, Sync: sync717}
	result723 := _t1439
	p.recordSpan(int(span_start722), "Transaction")
	return result723
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1440 := p.parse_config_dict()
	config_dict724 := _t1440
	p.consumeLiteral(")")
	_t1441 := p.construct_configure(config_dict724)
	result726 := _t1441
	p.recordSpan(int(span_start725), "Configure")
	return result726
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs727 := [][]interface{}{}
	cond728 := p.matchLookaheadLiteral(":", 0)
	for cond728 {
		_t1442 := p.parse_config_key_value()
		item729 := _t1442
		xs727 = append(xs727, item729)
		cond728 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values730 := xs727
	p.consumeLiteral("}")
	return config_key_values730
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol731 := p.consumeTerminal("SYMBOL").Value.str
	_t1443 := p.parse_raw_value()
	raw_value732 := _t1443
	return []interface{}{symbol731, raw_value732}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start746 := int64(p.spanStart())
	var _t1444 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1444 = 12
	} else {
		var _t1445 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1445 = 11
		} else {
			var _t1446 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1446 = 12
			} else {
				var _t1447 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1448 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1448 = 1
					} else {
						var _t1449 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1449 = 0
						} else {
							_t1449 = -1
						}
						_t1448 = _t1449
					}
					_t1447 = _t1448
				} else {
					var _t1450 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1450 = 7
					} else {
						var _t1451 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1451 = 8
						} else {
							var _t1452 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1452 = 2
							} else {
								var _t1453 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1453 = 3
								} else {
									var _t1454 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1454 = 9
									} else {
										var _t1455 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1455 = 4
										} else {
											var _t1456 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1456 = 5
											} else {
												var _t1457 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1457 = 6
												} else {
													var _t1458 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1458 = 10
													} else {
														_t1458 = -1
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
							_t1451 = _t1452
						}
						_t1450 = _t1451
					}
					_t1447 = _t1450
				}
				_t1446 = _t1447
			}
			_t1445 = _t1446
		}
		_t1444 = _t1445
	}
	prediction733 := _t1444
	var _t1459 *pb.Value
	if prediction733 == 12 {
		_t1460 := p.parse_boolean_value()
		boolean_value745 := _t1460
		_t1461 := &pb.Value{}
		_t1461.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value745}
		_t1459 = _t1461
	} else {
		var _t1462 *pb.Value
		if prediction733 == 11 {
			p.consumeLiteral("missing")
			_t1463 := &pb.MissingValue{}
			_t1464 := &pb.Value{}
			_t1464.Value = &pb.Value_MissingValue{MissingValue: _t1463}
			_t1462 = _t1464
		} else {
			var _t1465 *pb.Value
			if prediction733 == 10 {
				decimal744 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1466 := &pb.Value{}
				_t1466.Value = &pb.Value_DecimalValue{DecimalValue: decimal744}
				_t1465 = _t1466
			} else {
				var _t1467 *pb.Value
				if prediction733 == 9 {
					int128743 := p.consumeTerminal("INT128").Value.int128
					_t1468 := &pb.Value{}
					_t1468.Value = &pb.Value_Int128Value{Int128Value: int128743}
					_t1467 = _t1468
				} else {
					var _t1469 *pb.Value
					if prediction733 == 8 {
						uint128742 := p.consumeTerminal("UINT128").Value.uint128
						_t1470 := &pb.Value{}
						_t1470.Value = &pb.Value_Uint128Value{Uint128Value: uint128742}
						_t1469 = _t1470
					} else {
						var _t1471 *pb.Value
						if prediction733 == 7 {
							uint32741 := p.consumeTerminal("UINT32").Value.u32
							_t1472 := &pb.Value{}
							_t1472.Value = &pb.Value_Uint32Value{Uint32Value: uint32741}
							_t1471 = _t1472
						} else {
							var _t1473 *pb.Value
							if prediction733 == 6 {
								float740 := p.consumeTerminal("FLOAT").Value.f64
								_t1474 := &pb.Value{}
								_t1474.Value = &pb.Value_FloatValue{FloatValue: float740}
								_t1473 = _t1474
							} else {
								var _t1475 *pb.Value
								if prediction733 == 5 {
									float32739 := p.consumeTerminal("FLOAT32").Value.f32
									_t1476 := &pb.Value{}
									_t1476.Value = &pb.Value_Float32Value{Float32Value: float32739}
									_t1475 = _t1476
								} else {
									var _t1477 *pb.Value
									if prediction733 == 4 {
										int738 := p.consumeTerminal("INT").Value.i64
										_t1478 := &pb.Value{}
										_t1478.Value = &pb.Value_IntValue{IntValue: int738}
										_t1477 = _t1478
									} else {
										var _t1479 *pb.Value
										if prediction733 == 3 {
											int32737 := p.consumeTerminal("INT32").Value.i32
											_t1480 := &pb.Value{}
											_t1480.Value = &pb.Value_Int32Value{Int32Value: int32737}
											_t1479 = _t1480
										} else {
											var _t1481 *pb.Value
											if prediction733 == 2 {
												string736 := p.consumeTerminal("STRING").Value.str
												_t1482 := &pb.Value{}
												_t1482.Value = &pb.Value_StringValue{StringValue: string736}
												_t1481 = _t1482
											} else {
												var _t1483 *pb.Value
												if prediction733 == 1 {
													_t1484 := p.parse_raw_datetime()
													raw_datetime735 := _t1484
													_t1485 := &pb.Value{}
													_t1485.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime735}
													_t1483 = _t1485
												} else {
													var _t1486 *pb.Value
													if prediction733 == 0 {
														_t1487 := p.parse_raw_date()
														raw_date734 := _t1487
														_t1488 := &pb.Value{}
														_t1488.Value = &pb.Value_DateValue{DateValue: raw_date734}
														_t1486 = _t1488
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1483 = _t1486
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
				_t1465 = _t1467
			}
			_t1462 = _t1465
		}
		_t1459 = _t1462
	}
	result747 := _t1459
	p.recordSpan(int(span_start746), "Value")
	return result747
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int748 := p.consumeTerminal("INT").Value.i64
	int_3749 := p.consumeTerminal("INT").Value.i64
	int_4750 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1489 := &pb.DateValue{Year: int32(int748), Month: int32(int_3749), Day: int32(int_4750)}
	result752 := _t1489
	p.recordSpan(int(span_start751), "DateValue")
	return result752
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start760 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int753 := p.consumeTerminal("INT").Value.i64
	int_3754 := p.consumeTerminal("INT").Value.i64
	int_4755 := p.consumeTerminal("INT").Value.i64
	int_5756 := p.consumeTerminal("INT").Value.i64
	int_6757 := p.consumeTerminal("INT").Value.i64
	int_7758 := p.consumeTerminal("INT").Value.i64
	var _t1490 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1490 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8759 := _t1490
	p.consumeLiteral(")")
	_t1491 := &pb.DateTimeValue{Year: int32(int753), Month: int32(int_3754), Day: int32(int_4755), Hour: int32(int_5756), Minute: int32(int_6757), Second: int32(int_7758), Microsecond: int32(deref(int_8759, 0))}
	result761 := _t1491
	p.recordSpan(int(span_start760), "DateTimeValue")
	return result761
}

func (p *Parser) parse_boolean_value() bool {
	var _t1492 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1492 = 0
	} else {
		var _t1493 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1493 = 1
		} else {
			_t1493 = -1
		}
		_t1492 = _t1493
	}
	prediction762 := _t1492
	var _t1494 bool
	if prediction762 == 1 {
		p.consumeLiteral("false")
		_t1494 = false
	} else {
		var _t1495 bool
		if prediction762 == 0 {
			p.consumeLiteral("true")
			_t1495 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1494 = _t1495
	}
	return _t1494
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs763 := []*pb.FragmentId{}
	cond764 := p.matchLookaheadLiteral(":", 0)
	for cond764 {
		_t1496 := p.parse_fragment_id()
		item765 := _t1496
		xs763 = append(xs763, item765)
		cond764 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids766 := xs763
	p.consumeLiteral(")")
	_t1497 := &pb.Sync{Fragments: fragment_ids766}
	result768 := _t1497
	p.recordSpan(int(span_start767), "Sync")
	return result768
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start770 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol769 := p.consumeTerminal("SYMBOL").Value.str
	result771 := &pb.FragmentId{Id: []byte(symbol769)}
	p.recordSpan(int(span_start770), "FragmentId")
	return result771
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start774 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1498 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1499 := p.parse_epoch_writes()
		_t1498 = _t1499
	}
	epoch_writes772 := _t1498
	var _t1500 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1501 := p.parse_epoch_reads()
		_t1500 = _t1501
	}
	epoch_reads773 := _t1500
	p.consumeLiteral(")")
	_t1502 := epoch_writes772
	if epoch_writes772 == nil {
		_t1502 = []*pb.Write{}
	}
	_t1503 := epoch_reads773
	if epoch_reads773 == nil {
		_t1503 = []*pb.Read{}
	}
	_t1504 := &pb.Epoch{Writes: _t1502, Reads: _t1503}
	result775 := _t1504
	p.recordSpan(int(span_start774), "Epoch")
	return result775
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs776 := []*pb.Write{}
	cond777 := p.matchLookaheadLiteral("(", 0)
	for cond777 {
		_t1505 := p.parse_write()
		item778 := _t1505
		xs776 = append(xs776, item778)
		cond777 = p.matchLookaheadLiteral("(", 0)
	}
	writes779 := xs776
	p.consumeLiteral(")")
	return writes779
}

func (p *Parser) parse_write() *pb.Write {
	span_start785 := int64(p.spanStart())
	var _t1506 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1507 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1507 = 1
		} else {
			var _t1508 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1508 = 3
			} else {
				var _t1509 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1509 = 0
				} else {
					var _t1510 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1510 = 2
					} else {
						_t1510 = -1
					}
					_t1509 = _t1510
				}
				_t1508 = _t1509
			}
			_t1507 = _t1508
		}
		_t1506 = _t1507
	} else {
		_t1506 = -1
	}
	prediction780 := _t1506
	var _t1511 *pb.Write
	if prediction780 == 3 {
		_t1512 := p.parse_snapshot()
		snapshot784 := _t1512
		_t1513 := &pb.Write{}
		_t1513.WriteType = &pb.Write_Snapshot{Snapshot: snapshot784}
		_t1511 = _t1513
	} else {
		var _t1514 *pb.Write
		if prediction780 == 2 {
			_t1515 := p.parse_context()
			context783 := _t1515
			_t1516 := &pb.Write{}
			_t1516.WriteType = &pb.Write_Context{Context: context783}
			_t1514 = _t1516
		} else {
			var _t1517 *pb.Write
			if prediction780 == 1 {
				_t1518 := p.parse_undefine()
				undefine782 := _t1518
				_t1519 := &pb.Write{}
				_t1519.WriteType = &pb.Write_Undefine{Undefine: undefine782}
				_t1517 = _t1519
			} else {
				var _t1520 *pb.Write
				if prediction780 == 0 {
					_t1521 := p.parse_define()
					define781 := _t1521
					_t1522 := &pb.Write{}
					_t1522.WriteType = &pb.Write_Define{Define: define781}
					_t1520 = _t1522
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1517 = _t1520
			}
			_t1514 = _t1517
		}
		_t1511 = _t1514
	}
	result786 := _t1511
	p.recordSpan(int(span_start785), "Write")
	return result786
}

func (p *Parser) parse_define() *pb.Define {
	span_start788 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1523 := p.parse_fragment()
	fragment787 := _t1523
	p.consumeLiteral(")")
	_t1524 := &pb.Define{Fragment: fragment787}
	result789 := _t1524
	p.recordSpan(int(span_start788), "Define")
	return result789
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start795 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1525 := p.parse_new_fragment_id()
	new_fragment_id790 := _t1525
	xs791 := []*pb.Declaration{}
	cond792 := p.matchLookaheadLiteral("(", 0)
	for cond792 {
		_t1526 := p.parse_declaration()
		item793 := _t1526
		xs791 = append(xs791, item793)
		cond792 = p.matchLookaheadLiteral("(", 0)
	}
	declarations794 := xs791
	p.consumeLiteral(")")
	result796 := p.constructFragment(new_fragment_id790, declarations794)
	p.recordSpan(int(span_start795), "Fragment")
	return result796
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start798 := int64(p.spanStart())
	_t1527 := p.parse_fragment_id()
	fragment_id797 := _t1527
	p.startFragment(fragment_id797)
	result799 := fragment_id797
	p.recordSpan(int(span_start798), "FragmentId")
	return result799
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start805 := int64(p.spanStart())
	var _t1528 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1529 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1529 = 3
		} else {
			var _t1530 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1530 = 2
			} else {
				var _t1531 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1531 = 3
				} else {
					var _t1532 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1532 = 0
					} else {
						var _t1533 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1533 = 3
						} else {
							var _t1534 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1534 = 3
							} else {
								var _t1535 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1535 = 1
								} else {
									_t1535 = -1
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
			}
			_t1529 = _t1530
		}
		_t1528 = _t1529
	} else {
		_t1528 = -1
	}
	prediction800 := _t1528
	var _t1536 *pb.Declaration
	if prediction800 == 3 {
		_t1537 := p.parse_data()
		data804 := _t1537
		_t1538 := &pb.Declaration{}
		_t1538.DeclarationType = &pb.Declaration_Data{Data: data804}
		_t1536 = _t1538
	} else {
		var _t1539 *pb.Declaration
		if prediction800 == 2 {
			_t1540 := p.parse_constraint()
			constraint803 := _t1540
			_t1541 := &pb.Declaration{}
			_t1541.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint803}
			_t1539 = _t1541
		} else {
			var _t1542 *pb.Declaration
			if prediction800 == 1 {
				_t1543 := p.parse_algorithm()
				algorithm802 := _t1543
				_t1544 := &pb.Declaration{}
				_t1544.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm802}
				_t1542 = _t1544
			} else {
				var _t1545 *pb.Declaration
				if prediction800 == 0 {
					_t1546 := p.parse_def()
					def801 := _t1546
					_t1547 := &pb.Declaration{}
					_t1547.DeclarationType = &pb.Declaration_Def{Def: def801}
					_t1545 = _t1547
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1542 = _t1545
			}
			_t1539 = _t1542
		}
		_t1536 = _t1539
	}
	result806 := _t1536
	p.recordSpan(int(span_start805), "Declaration")
	return result806
}

func (p *Parser) parse_def() *pb.Def {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1548 := p.parse_relation_id()
	relation_id807 := _t1548
	_t1549 := p.parse_abstraction()
	abstraction808 := _t1549
	var _t1550 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1551 := p.parse_attrs()
		_t1550 = _t1551
	}
	attrs809 := _t1550
	p.consumeLiteral(")")
	_t1552 := attrs809
	if attrs809 == nil {
		_t1552 = []*pb.Attribute{}
	}
	_t1553 := &pb.Def{Name: relation_id807, Body: abstraction808, Attrs: _t1552}
	result811 := _t1553
	p.recordSpan(int(span_start810), "Def")
	return result811
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start815 := int64(p.spanStart())
	var _t1554 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1554 = 0
	} else {
		var _t1555 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1555 = 1
		} else {
			_t1555 = -1
		}
		_t1554 = _t1555
	}
	prediction812 := _t1554
	var _t1556 *pb.RelationId
	if prediction812 == 1 {
		uint128814 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128814
		_t1556 = &pb.RelationId{IdLow: uint128814.Low, IdHigh: uint128814.High}
	} else {
		var _t1557 *pb.RelationId
		if prediction812 == 0 {
			p.consumeLiteral(":")
			symbol813 := p.consumeTerminal("SYMBOL").Value.str
			_t1557 = p.relationIdFromString(symbol813)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1556 = _t1557
	}
	result816 := _t1556
	p.recordSpan(int(span_start815), "RelationId")
	return result816
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1558 := p.parse_bindings()
	bindings817 := _t1558
	_t1559 := p.parse_formula()
	formula818 := _t1559
	p.consumeLiteral(")")
	_t1560 := &pb.Abstraction{Vars: listConcat(bindings817[0].([]*pb.Binding), bindings817[1].([]*pb.Binding)), Value: formula818}
	result820 := _t1560
	p.recordSpan(int(span_start819), "Abstraction")
	return result820
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs821 := []*pb.Binding{}
	cond822 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond822 {
		_t1561 := p.parse_binding()
		item823 := _t1561
		xs821 = append(xs821, item823)
		cond822 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings824 := xs821
	var _t1562 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1563 := p.parse_value_bindings()
		_t1562 = _t1563
	}
	value_bindings825 := _t1562
	p.consumeLiteral("]")
	_t1564 := value_bindings825
	if value_bindings825 == nil {
		_t1564 = []*pb.Binding{}
	}
	return []interface{}{bindings824, _t1564}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start828 := int64(p.spanStart())
	symbol826 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1565 := p.parse_type()
	type827 := _t1565
	_t1566 := &pb.Var{Name: symbol826}
	_t1567 := &pb.Binding{Var: _t1566, Type: type827}
	result829 := _t1567
	p.recordSpan(int(span_start828), "Binding")
	return result829
}

func (p *Parser) parse_type() *pb.Type {
	span_start846 := int64(p.spanStart())
	var _t1568 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1568 = 0
	} else {
		var _t1569 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1569 = 13
		} else {
			var _t1570 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1570 = 4
			} else {
				var _t1571 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1571 = 1
				} else {
					var _t1572 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1572 = 8
					} else {
						var _t1573 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1573 = 11
						} else {
							var _t1574 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1574 = 5
							} else {
								var _t1575 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1575 = 2
								} else {
									var _t1576 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1576 = 12
									} else {
										var _t1577 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1577 = 3
										} else {
											var _t1578 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1578 = 7
											} else {
												var _t1579 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1579 = 6
												} else {
													var _t1580 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1580 = 10
													} else {
														var _t1581 int64
														if p.matchLookaheadLiteral("(", 0) {
															var _t1582 int64
															if p.matchLookaheadLiteral("FIXED", 1) {
																_t1582 = 14
															} else {
																var _t1583 int64
																if p.matchLookaheadLiteral("DECIMAL", 1) {
																	_t1583 = 9
																} else {
																	_t1583 = -1
																}
																_t1582 = _t1583
															}
															_t1581 = _t1582
														} else {
															_t1581 = -1
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
			_t1569 = _t1570
		}
		_t1568 = _t1569
	}
	prediction830 := _t1568
	var _t1584 *pb.Type
	if prediction830 == 14 {
		_t1585 := p.parse_fixed_type()
		fixed_type845 := _t1585
		_t1586 := &pb.Type{}
		_t1586.Type = &pb.Type_FixedType{FixedType: fixed_type845}
		_t1584 = _t1586
	} else {
		var _t1587 *pb.Type
		if prediction830 == 13 {
			_t1588 := p.parse_uint32_type()
			uint32_type844 := _t1588
			_t1589 := &pb.Type{}
			_t1589.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type844}
			_t1587 = _t1589
		} else {
			var _t1590 *pb.Type
			if prediction830 == 12 {
				_t1591 := p.parse_float32_type()
				float32_type843 := _t1591
				_t1592 := &pb.Type{}
				_t1592.Type = &pb.Type_Float32Type{Float32Type: float32_type843}
				_t1590 = _t1592
			} else {
				var _t1593 *pb.Type
				if prediction830 == 11 {
					_t1594 := p.parse_int32_type()
					int32_type842 := _t1594
					_t1595 := &pb.Type{}
					_t1595.Type = &pb.Type_Int32Type{Int32Type: int32_type842}
					_t1593 = _t1595
				} else {
					var _t1596 *pb.Type
					if prediction830 == 10 {
						_t1597 := p.parse_boolean_type()
						boolean_type841 := _t1597
						_t1598 := &pb.Type{}
						_t1598.Type = &pb.Type_BooleanType{BooleanType: boolean_type841}
						_t1596 = _t1598
					} else {
						var _t1599 *pb.Type
						if prediction830 == 9 {
							_t1600 := p.parse_decimal_type()
							decimal_type840 := _t1600
							_t1601 := &pb.Type{}
							_t1601.Type = &pb.Type_DecimalType{DecimalType: decimal_type840}
							_t1599 = _t1601
						} else {
							var _t1602 *pb.Type
							if prediction830 == 8 {
								_t1603 := p.parse_missing_type()
								missing_type839 := _t1603
								_t1604 := &pb.Type{}
								_t1604.Type = &pb.Type_MissingType{MissingType: missing_type839}
								_t1602 = _t1604
							} else {
								var _t1605 *pb.Type
								if prediction830 == 7 {
									_t1606 := p.parse_datetime_type()
									datetime_type838 := _t1606
									_t1607 := &pb.Type{}
									_t1607.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type838}
									_t1605 = _t1607
								} else {
									var _t1608 *pb.Type
									if prediction830 == 6 {
										_t1609 := p.parse_date_type()
										date_type837 := _t1609
										_t1610 := &pb.Type{}
										_t1610.Type = &pb.Type_DateType{DateType: date_type837}
										_t1608 = _t1610
									} else {
										var _t1611 *pb.Type
										if prediction830 == 5 {
											_t1612 := p.parse_int128_type()
											int128_type836 := _t1612
											_t1613 := &pb.Type{}
											_t1613.Type = &pb.Type_Int128Type{Int128Type: int128_type836}
											_t1611 = _t1613
										} else {
											var _t1614 *pb.Type
											if prediction830 == 4 {
												_t1615 := p.parse_uint128_type()
												uint128_type835 := _t1615
												_t1616 := &pb.Type{}
												_t1616.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type835}
												_t1614 = _t1616
											} else {
												var _t1617 *pb.Type
												if prediction830 == 3 {
													_t1618 := p.parse_float_type()
													float_type834 := _t1618
													_t1619 := &pb.Type{}
													_t1619.Type = &pb.Type_FloatType{FloatType: float_type834}
													_t1617 = _t1619
												} else {
													var _t1620 *pb.Type
													if prediction830 == 2 {
														_t1621 := p.parse_int_type()
														int_type833 := _t1621
														_t1622 := &pb.Type{}
														_t1622.Type = &pb.Type_IntType{IntType: int_type833}
														_t1620 = _t1622
													} else {
														var _t1623 *pb.Type
														if prediction830 == 1 {
															_t1624 := p.parse_string_type()
															string_type832 := _t1624
															_t1625 := &pb.Type{}
															_t1625.Type = &pb.Type_StringType{StringType: string_type832}
															_t1623 = _t1625
														} else {
															var _t1626 *pb.Type
															if prediction830 == 0 {
																_t1627 := p.parse_unspecified_type()
																unspecified_type831 := _t1627
																_t1628 := &pb.Type{}
																_t1628.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type831}
																_t1626 = _t1628
															} else {
																panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
															}
															_t1623 = _t1626
														}
														_t1620 = _t1623
													}
													_t1617 = _t1620
												}
												_t1614 = _t1617
											}
											_t1611 = _t1614
										}
										_t1608 = _t1611
									}
									_t1605 = _t1608
								}
								_t1602 = _t1605
							}
							_t1599 = _t1602
						}
						_t1596 = _t1599
					}
					_t1593 = _t1596
				}
				_t1590 = _t1593
			}
			_t1587 = _t1590
		}
		_t1584 = _t1587
	}
	result847 := _t1584
	p.recordSpan(int(span_start846), "Type")
	return result847
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1629 := &pb.UnspecifiedType{}
	result849 := _t1629
	p.recordSpan(int(span_start848), "UnspecifiedType")
	return result849
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start850 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1630 := &pb.StringType{}
	result851 := _t1630
	p.recordSpan(int(span_start850), "StringType")
	return result851
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1631 := &pb.IntType{}
	result853 := _t1631
	p.recordSpan(int(span_start852), "IntType")
	return result853
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1632 := &pb.FloatType{}
	result855 := _t1632
	p.recordSpan(int(span_start854), "FloatType")
	return result855
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start856 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1633 := &pb.UInt128Type{}
	result857 := _t1633
	p.recordSpan(int(span_start856), "UInt128Type")
	return result857
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1634 := &pb.Int128Type{}
	result859 := _t1634
	p.recordSpan(int(span_start858), "Int128Type")
	return result859
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1635 := &pb.DateType{}
	result861 := _t1635
	p.recordSpan(int(span_start860), "DateType")
	return result861
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start862 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1636 := &pb.DateTimeType{}
	result863 := _t1636
	p.recordSpan(int(span_start862), "DateTimeType")
	return result863
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1637 := &pb.MissingType{}
	result865 := _t1637
	p.recordSpan(int(span_start864), "MissingType")
	return result865
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start868 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int866 := p.consumeTerminal("INT").Value.i64
	int_3867 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1638 := &pb.DecimalType{Precision: int32(int866), Scale: int32(int_3867)}
	result869 := _t1638
	p.recordSpan(int(span_start868), "DecimalType")
	return result869
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start870 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1639 := &pb.BooleanType{}
	result871 := _t1639
	p.recordSpan(int(span_start870), "BooleanType")
	return result871
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start872 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1640 := &pb.Int32Type{}
	result873 := _t1640
	p.recordSpan(int(span_start872), "Int32Type")
	return result873
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start874 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1641 := &pb.Float32Type{}
	result875 := _t1641
	p.recordSpan(int(span_start874), "Float32Type")
	return result875
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start876 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1642 := &pb.UInt32Type{}
	result877 := _t1642
	p.recordSpan(int(span_start876), "UInt32Type")
	return result877
}

func (p *Parser) parse_fixed_type() *pb.FixedType {
	span_start879 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("FIXED")
	int878 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1643 := &pb.FixedType{Length: int32(int878)}
	result880 := _t1643
	p.recordSpan(int(span_start879), "FixedType")
	return result880
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs881 := []*pb.Binding{}
	cond882 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond882 {
		_t1644 := p.parse_binding()
		item883 := _t1644
		xs881 = append(xs881, item883)
		cond882 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings884 := xs881
	return bindings884
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start899 := int64(p.spanStart())
	var _t1645 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1646 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1646 = 0
		} else {
			var _t1647 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1647 = 11
			} else {
				var _t1648 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1648 = 3
				} else {
					var _t1649 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1649 = 10
					} else {
						var _t1650 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1650 = 9
						} else {
							var _t1651 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1651 = 5
							} else {
								var _t1652 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1652 = 6
								} else {
									var _t1653 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1653 = 7
									} else {
										var _t1654 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1654 = 1
										} else {
											var _t1655 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1655 = 2
											} else {
												var _t1656 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1656 = 12
												} else {
													var _t1657 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1657 = 8
													} else {
														var _t1658 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1658 = 4
														} else {
															var _t1659 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1659 = 10
															} else {
																var _t1660 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1660 = 10
																} else {
																	var _t1661 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1661 = 10
																	} else {
																		var _t1662 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1662 = 10
																		} else {
																			var _t1663 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1663 = 10
																			} else {
																				var _t1664 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1664 = 10
																				} else {
																					var _t1665 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1665 = 10
																					} else {
																						var _t1666 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1666 = 10
																						} else {
																							var _t1667 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1667 = 10
																							} else {
																								_t1667 = -1
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
			}
			_t1646 = _t1647
		}
		_t1645 = _t1646
	} else {
		_t1645 = -1
	}
	prediction885 := _t1645
	var _t1668 *pb.Formula
	if prediction885 == 12 {
		_t1669 := p.parse_cast()
		cast898 := _t1669
		_t1670 := &pb.Formula{}
		_t1670.FormulaType = &pb.Formula_Cast{Cast: cast898}
		_t1668 = _t1670
	} else {
		var _t1671 *pb.Formula
		if prediction885 == 11 {
			_t1672 := p.parse_rel_atom()
			rel_atom897 := _t1672
			_t1673 := &pb.Formula{}
			_t1673.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom897}
			_t1671 = _t1673
		} else {
			var _t1674 *pb.Formula
			if prediction885 == 10 {
				_t1675 := p.parse_primitive()
				primitive896 := _t1675
				_t1676 := &pb.Formula{}
				_t1676.FormulaType = &pb.Formula_Primitive{Primitive: primitive896}
				_t1674 = _t1676
			} else {
				var _t1677 *pb.Formula
				if prediction885 == 9 {
					_t1678 := p.parse_pragma()
					pragma895 := _t1678
					_t1679 := &pb.Formula{}
					_t1679.FormulaType = &pb.Formula_Pragma{Pragma: pragma895}
					_t1677 = _t1679
				} else {
					var _t1680 *pb.Formula
					if prediction885 == 8 {
						_t1681 := p.parse_atom()
						atom894 := _t1681
						_t1682 := &pb.Formula{}
						_t1682.FormulaType = &pb.Formula_Atom{Atom: atom894}
						_t1680 = _t1682
					} else {
						var _t1683 *pb.Formula
						if prediction885 == 7 {
							_t1684 := p.parse_ffi()
							ffi893 := _t1684
							_t1685 := &pb.Formula{}
							_t1685.FormulaType = &pb.Formula_Ffi{Ffi: ffi893}
							_t1683 = _t1685
						} else {
							var _t1686 *pb.Formula
							if prediction885 == 6 {
								_t1687 := p.parse_not()
								not892 := _t1687
								_t1688 := &pb.Formula{}
								_t1688.FormulaType = &pb.Formula_Not{Not: not892}
								_t1686 = _t1688
							} else {
								var _t1689 *pb.Formula
								if prediction885 == 5 {
									_t1690 := p.parse_disjunction()
									disjunction891 := _t1690
									_t1691 := &pb.Formula{}
									_t1691.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction891}
									_t1689 = _t1691
								} else {
									var _t1692 *pb.Formula
									if prediction885 == 4 {
										_t1693 := p.parse_conjunction()
										conjunction890 := _t1693
										_t1694 := &pb.Formula{}
										_t1694.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction890}
										_t1692 = _t1694
									} else {
										var _t1695 *pb.Formula
										if prediction885 == 3 {
											_t1696 := p.parse_reduce()
											reduce889 := _t1696
											_t1697 := &pb.Formula{}
											_t1697.FormulaType = &pb.Formula_Reduce{Reduce: reduce889}
											_t1695 = _t1697
										} else {
											var _t1698 *pb.Formula
											if prediction885 == 2 {
												_t1699 := p.parse_exists()
												exists888 := _t1699
												_t1700 := &pb.Formula{}
												_t1700.FormulaType = &pb.Formula_Exists{Exists: exists888}
												_t1698 = _t1700
											} else {
												var _t1701 *pb.Formula
												if prediction885 == 1 {
													_t1702 := p.parse_false()
													false887 := _t1702
													_t1703 := &pb.Formula{}
													_t1703.FormulaType = &pb.Formula_Disjunction{Disjunction: false887}
													_t1701 = _t1703
												} else {
													var _t1704 *pb.Formula
													if prediction885 == 0 {
														_t1705 := p.parse_true()
														true886 := _t1705
														_t1706 := &pb.Formula{}
														_t1706.FormulaType = &pb.Formula_Conjunction{Conjunction: true886}
														_t1704 = _t1706
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1701 = _t1704
												}
												_t1698 = _t1701
											}
											_t1695 = _t1698
										}
										_t1692 = _t1695
									}
									_t1689 = _t1692
								}
								_t1686 = _t1689
							}
							_t1683 = _t1686
						}
						_t1680 = _t1683
					}
					_t1677 = _t1680
				}
				_t1674 = _t1677
			}
			_t1671 = _t1674
		}
		_t1668 = _t1671
	}
	result900 := _t1668
	p.recordSpan(int(span_start899), "Formula")
	return result900
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1707 := &pb.Conjunction{Args: []*pb.Formula{}}
	result902 := _t1707
	p.recordSpan(int(span_start901), "Conjunction")
	return result902
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1708 := &pb.Disjunction{Args: []*pb.Formula{}}
	result904 := _t1708
	p.recordSpan(int(span_start903), "Disjunction")
	return result904
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start907 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1709 := p.parse_bindings()
	bindings905 := _t1709
	_t1710 := p.parse_formula()
	formula906 := _t1710
	p.consumeLiteral(")")
	_t1711 := &pb.Abstraction{Vars: listConcat(bindings905[0].([]*pb.Binding), bindings905[1].([]*pb.Binding)), Value: formula906}
	_t1712 := &pb.Exists{Body: _t1711}
	result908 := _t1712
	p.recordSpan(int(span_start907), "Exists")
	return result908
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start912 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1713 := p.parse_abstraction()
	abstraction909 := _t1713
	_t1714 := p.parse_abstraction()
	abstraction_3910 := _t1714
	_t1715 := p.parse_terms()
	terms911 := _t1715
	p.consumeLiteral(")")
	_t1716 := &pb.Reduce{Op: abstraction909, Body: abstraction_3910, Terms: terms911}
	result913 := _t1716
	p.recordSpan(int(span_start912), "Reduce")
	return result913
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs914 := []*pb.Term{}
	cond915 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond915 {
		_t1717 := p.parse_term()
		item916 := _t1717
		xs914 = append(xs914, item916)
		cond915 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms917 := xs914
	p.consumeLiteral(")")
	return terms917
}

func (p *Parser) parse_term() *pb.Term {
	span_start921 := int64(p.spanStart())
	var _t1718 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1718 = 1
	} else {
		var _t1719 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1719 = 1
		} else {
			var _t1720 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1720 = 1
			} else {
				var _t1721 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1721 = 1
				} else {
					var _t1722 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1722 = 0
					} else {
						var _t1723 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1723 = 1
						} else {
							var _t1724 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1724 = 1
							} else {
								var _t1725 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1725 = 1
								} else {
									var _t1726 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1726 = 1
									} else {
										var _t1727 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1727 = 1
										} else {
											var _t1728 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1728 = 1
											} else {
												var _t1729 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1729 = 1
												} else {
													var _t1730 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1730 = 1
													} else {
														var _t1731 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1731 = 1
														} else {
															_t1731 = -1
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
			_t1719 = _t1720
		}
		_t1718 = _t1719
	}
	prediction918 := _t1718
	var _t1732 *pb.Term
	if prediction918 == 1 {
		_t1733 := p.parse_value()
		value920 := _t1733
		_t1734 := &pb.Term{}
		_t1734.TermType = &pb.Term_Constant{Constant: value920}
		_t1732 = _t1734
	} else {
		var _t1735 *pb.Term
		if prediction918 == 0 {
			_t1736 := p.parse_var()
			var919 := _t1736
			_t1737 := &pb.Term{}
			_t1737.TermType = &pb.Term_Var{Var: var919}
			_t1735 = _t1737
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1732 = _t1735
	}
	result922 := _t1732
	p.recordSpan(int(span_start921), "Term")
	return result922
}

func (p *Parser) parse_var() *pb.Var {
	span_start924 := int64(p.spanStart())
	symbol923 := p.consumeTerminal("SYMBOL").Value.str
	_t1738 := &pb.Var{Name: symbol923}
	result925 := _t1738
	p.recordSpan(int(span_start924), "Var")
	return result925
}

func (p *Parser) parse_value() *pb.Value {
	span_start939 := int64(p.spanStart())
	var _t1739 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1739 = 12
	} else {
		var _t1740 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1740 = 11
		} else {
			var _t1741 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1741 = 12
			} else {
				var _t1742 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1743 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1743 = 1
					} else {
						var _t1744 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1744 = 0
						} else {
							_t1744 = -1
						}
						_t1743 = _t1744
					}
					_t1742 = _t1743
				} else {
					var _t1745 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1745 = 7
					} else {
						var _t1746 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1746 = 8
						} else {
							var _t1747 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1747 = 2
							} else {
								var _t1748 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1748 = 3
								} else {
									var _t1749 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1749 = 9
									} else {
										var _t1750 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1750 = 4
										} else {
											var _t1751 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1751 = 5
											} else {
												var _t1752 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1752 = 6
												} else {
													var _t1753 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1753 = 10
													} else {
														_t1753 = -1
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
							_t1746 = _t1747
						}
						_t1745 = _t1746
					}
					_t1742 = _t1745
				}
				_t1741 = _t1742
			}
			_t1740 = _t1741
		}
		_t1739 = _t1740
	}
	prediction926 := _t1739
	var _t1754 *pb.Value
	if prediction926 == 12 {
		_t1755 := p.parse_boolean_value()
		boolean_value938 := _t1755
		_t1756 := &pb.Value{}
		_t1756.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value938}
		_t1754 = _t1756
	} else {
		var _t1757 *pb.Value
		if prediction926 == 11 {
			p.consumeLiteral("missing")
			_t1758 := &pb.MissingValue{}
			_t1759 := &pb.Value{}
			_t1759.Value = &pb.Value_MissingValue{MissingValue: _t1758}
			_t1757 = _t1759
		} else {
			var _t1760 *pb.Value
			if prediction926 == 10 {
				formatted_decimal937 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1761 := &pb.Value{}
				_t1761.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal937}
				_t1760 = _t1761
			} else {
				var _t1762 *pb.Value
				if prediction926 == 9 {
					formatted_int128936 := p.consumeTerminal("INT128").Value.int128
					_t1763 := &pb.Value{}
					_t1763.Value = &pb.Value_Int128Value{Int128Value: formatted_int128936}
					_t1762 = _t1763
				} else {
					var _t1764 *pb.Value
					if prediction926 == 8 {
						formatted_uint128935 := p.consumeTerminal("UINT128").Value.uint128
						_t1765 := &pb.Value{}
						_t1765.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128935}
						_t1764 = _t1765
					} else {
						var _t1766 *pb.Value
						if prediction926 == 7 {
							formatted_uint32934 := p.consumeTerminal("UINT32").Value.u32
							_t1767 := &pb.Value{}
							_t1767.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32934}
							_t1766 = _t1767
						} else {
							var _t1768 *pb.Value
							if prediction926 == 6 {
								formatted_float933 := p.consumeTerminal("FLOAT").Value.f64
								_t1769 := &pb.Value{}
								_t1769.Value = &pb.Value_FloatValue{FloatValue: formatted_float933}
								_t1768 = _t1769
							} else {
								var _t1770 *pb.Value
								if prediction926 == 5 {
									formatted_float32932 := p.consumeTerminal("FLOAT32").Value.f32
									_t1771 := &pb.Value{}
									_t1771.Value = &pb.Value_Float32Value{Float32Value: formatted_float32932}
									_t1770 = _t1771
								} else {
									var _t1772 *pb.Value
									if prediction926 == 4 {
										formatted_int931 := p.consumeTerminal("INT").Value.i64
										_t1773 := &pb.Value{}
										_t1773.Value = &pb.Value_IntValue{IntValue: formatted_int931}
										_t1772 = _t1773
									} else {
										var _t1774 *pb.Value
										if prediction926 == 3 {
											formatted_int32930 := p.consumeTerminal("INT32").Value.i32
											_t1775 := &pb.Value{}
											_t1775.Value = &pb.Value_Int32Value{Int32Value: formatted_int32930}
											_t1774 = _t1775
										} else {
											var _t1776 *pb.Value
											if prediction926 == 2 {
												formatted_string929 := p.consumeTerminal("STRING").Value.str
												_t1777 := &pb.Value{}
												_t1777.Value = &pb.Value_StringValue{StringValue: formatted_string929}
												_t1776 = _t1777
											} else {
												var _t1778 *pb.Value
												if prediction926 == 1 {
													_t1779 := p.parse_datetime()
													datetime928 := _t1779
													_t1780 := &pb.Value{}
													_t1780.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime928}
													_t1778 = _t1780
												} else {
													var _t1781 *pb.Value
													if prediction926 == 0 {
														_t1782 := p.parse_date()
														date927 := _t1782
														_t1783 := &pb.Value{}
														_t1783.Value = &pb.Value_DateValue{DateValue: date927}
														_t1781 = _t1783
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1778 = _t1781
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
				_t1760 = _t1762
			}
			_t1757 = _t1760
		}
		_t1754 = _t1757
	}
	result940 := _t1754
	p.recordSpan(int(span_start939), "Value")
	return result940
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start944 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int941 := p.consumeTerminal("INT").Value.i64
	formatted_int_3942 := p.consumeTerminal("INT").Value.i64
	formatted_int_4943 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1784 := &pb.DateValue{Year: int32(formatted_int941), Month: int32(formatted_int_3942), Day: int32(formatted_int_4943)}
	result945 := _t1784
	p.recordSpan(int(span_start944), "DateValue")
	return result945
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int946 := p.consumeTerminal("INT").Value.i64
	formatted_int_3947 := p.consumeTerminal("INT").Value.i64
	formatted_int_4948 := p.consumeTerminal("INT").Value.i64
	formatted_int_5949 := p.consumeTerminal("INT").Value.i64
	formatted_int_6950 := p.consumeTerminal("INT").Value.i64
	formatted_int_7951 := p.consumeTerminal("INT").Value.i64
	var _t1785 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1785 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8952 := _t1785
	p.consumeLiteral(")")
	_t1786 := &pb.DateTimeValue{Year: int32(formatted_int946), Month: int32(formatted_int_3947), Day: int32(formatted_int_4948), Hour: int32(formatted_int_5949), Minute: int32(formatted_int_6950), Second: int32(formatted_int_7951), Microsecond: int32(deref(formatted_int_8952, 0))}
	result954 := _t1786
	p.recordSpan(int(span_start953), "DateTimeValue")
	return result954
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start959 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs955 := []*pb.Formula{}
	cond956 := p.matchLookaheadLiteral("(", 0)
	for cond956 {
		_t1787 := p.parse_formula()
		item957 := _t1787
		xs955 = append(xs955, item957)
		cond956 = p.matchLookaheadLiteral("(", 0)
	}
	formulas958 := xs955
	p.consumeLiteral(")")
	_t1788 := &pb.Conjunction{Args: formulas958}
	result960 := _t1788
	p.recordSpan(int(span_start959), "Conjunction")
	return result960
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs961 := []*pb.Formula{}
	cond962 := p.matchLookaheadLiteral("(", 0)
	for cond962 {
		_t1789 := p.parse_formula()
		item963 := _t1789
		xs961 = append(xs961, item963)
		cond962 = p.matchLookaheadLiteral("(", 0)
	}
	formulas964 := xs961
	p.consumeLiteral(")")
	_t1790 := &pb.Disjunction{Args: formulas964}
	result966 := _t1790
	p.recordSpan(int(span_start965), "Disjunction")
	return result966
}

func (p *Parser) parse_not() *pb.Not {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1791 := p.parse_formula()
	formula967 := _t1791
	p.consumeLiteral(")")
	_t1792 := &pb.Not{Arg: formula967}
	result969 := _t1792
	p.recordSpan(int(span_start968), "Not")
	return result969
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start973 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1793 := p.parse_name()
	name970 := _t1793
	_t1794 := p.parse_ffi_args()
	ffi_args971 := _t1794
	_t1795 := p.parse_terms()
	terms972 := _t1795
	p.consumeLiteral(")")
	_t1796 := &pb.FFI{Name: name970, Args: ffi_args971, Terms: terms972}
	result974 := _t1796
	p.recordSpan(int(span_start973), "FFI")
	return result974
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol975 := p.consumeTerminal("SYMBOL").Value.str
	return symbol975
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs976 := []*pb.Abstraction{}
	cond977 := p.matchLookaheadLiteral("(", 0)
	for cond977 {
		_t1797 := p.parse_abstraction()
		item978 := _t1797
		xs976 = append(xs976, item978)
		cond977 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions979 := xs976
	p.consumeLiteral(")")
	return abstractions979
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start985 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1798 := p.parse_relation_id()
	relation_id980 := _t1798
	xs981 := []*pb.Term{}
	cond982 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond982 {
		_t1799 := p.parse_term()
		item983 := _t1799
		xs981 = append(xs981, item983)
		cond982 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms984 := xs981
	p.consumeLiteral(")")
	_t1800 := &pb.Atom{Name: relation_id980, Terms: terms984}
	result986 := _t1800
	p.recordSpan(int(span_start985), "Atom")
	return result986
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start992 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1801 := p.parse_name()
	name987 := _t1801
	xs988 := []*pb.Term{}
	cond989 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond989 {
		_t1802 := p.parse_term()
		item990 := _t1802
		xs988 = append(xs988, item990)
		cond989 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms991 := xs988
	p.consumeLiteral(")")
	_t1803 := &pb.Pragma{Name: name987, Terms: terms991}
	result993 := _t1803
	p.recordSpan(int(span_start992), "Pragma")
	return result993
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start1009 := int64(p.spanStart())
	var _t1804 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1805 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1805 = 9
		} else {
			var _t1806 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1806 = 4
			} else {
				var _t1807 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1807 = 3
				} else {
					var _t1808 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1808 = 0
					} else {
						var _t1809 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1809 = 2
						} else {
							var _t1810 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1810 = 1
							} else {
								var _t1811 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1811 = 8
								} else {
									var _t1812 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1812 = 6
									} else {
										var _t1813 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1813 = 5
										} else {
											var _t1814 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1814 = 7
											} else {
												_t1814 = -1
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
			}
			_t1805 = _t1806
		}
		_t1804 = _t1805
	} else {
		_t1804 = -1
	}
	prediction994 := _t1804
	var _t1815 *pb.Primitive
	if prediction994 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1816 := p.parse_name()
		name1004 := _t1816
		xs1005 := []*pb.RelTerm{}
		cond1006 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond1006 {
			_t1817 := p.parse_rel_term()
			item1007 := _t1817
			xs1005 = append(xs1005, item1007)
			cond1006 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms1008 := xs1005
		p.consumeLiteral(")")
		_t1818 := &pb.Primitive{Name: name1004, Terms: rel_terms1008}
		_t1815 = _t1818
	} else {
		var _t1819 *pb.Primitive
		if prediction994 == 8 {
			_t1820 := p.parse_divide()
			divide1003 := _t1820
			_t1819 = divide1003
		} else {
			var _t1821 *pb.Primitive
			if prediction994 == 7 {
				_t1822 := p.parse_multiply()
				multiply1002 := _t1822
				_t1821 = multiply1002
			} else {
				var _t1823 *pb.Primitive
				if prediction994 == 6 {
					_t1824 := p.parse_minus()
					minus1001 := _t1824
					_t1823 = minus1001
				} else {
					var _t1825 *pb.Primitive
					if prediction994 == 5 {
						_t1826 := p.parse_add()
						add1000 := _t1826
						_t1825 = add1000
					} else {
						var _t1827 *pb.Primitive
						if prediction994 == 4 {
							_t1828 := p.parse_gt_eq()
							gt_eq999 := _t1828
							_t1827 = gt_eq999
						} else {
							var _t1829 *pb.Primitive
							if prediction994 == 3 {
								_t1830 := p.parse_gt()
								gt998 := _t1830
								_t1829 = gt998
							} else {
								var _t1831 *pb.Primitive
								if prediction994 == 2 {
									_t1832 := p.parse_lt_eq()
									lt_eq997 := _t1832
									_t1831 = lt_eq997
								} else {
									var _t1833 *pb.Primitive
									if prediction994 == 1 {
										_t1834 := p.parse_lt()
										lt996 := _t1834
										_t1833 = lt996
									} else {
										var _t1835 *pb.Primitive
										if prediction994 == 0 {
											_t1836 := p.parse_eq()
											eq995 := _t1836
											_t1835 = eq995
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1819 = _t1821
		}
		_t1815 = _t1819
	}
	result1010 := _t1815
	p.recordSpan(int(span_start1009), "Primitive")
	return result1010
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1837 := p.parse_term()
	term1011 := _t1837
	_t1838 := p.parse_term()
	term_31012 := _t1838
	p.consumeLiteral(")")
	_t1839 := &pb.RelTerm{}
	_t1839.RelTermType = &pb.RelTerm_Term{Term: term1011}
	_t1840 := &pb.RelTerm{}
	_t1840.RelTermType = &pb.RelTerm_Term{Term: term_31012}
	_t1841 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1839, _t1840}}
	result1014 := _t1841
	p.recordSpan(int(span_start1013), "Primitive")
	return result1014
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1842 := p.parse_term()
	term1015 := _t1842
	_t1843 := p.parse_term()
	term_31016 := _t1843
	p.consumeLiteral(")")
	_t1844 := &pb.RelTerm{}
	_t1844.RelTermType = &pb.RelTerm_Term{Term: term1015}
	_t1845 := &pb.RelTerm{}
	_t1845.RelTermType = &pb.RelTerm_Term{Term: term_31016}
	_t1846 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1844, _t1845}}
	result1018 := _t1846
	p.recordSpan(int(span_start1017), "Primitive")
	return result1018
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1847 := p.parse_term()
	term1019 := _t1847
	_t1848 := p.parse_term()
	term_31020 := _t1848
	p.consumeLiteral(")")
	_t1849 := &pb.RelTerm{}
	_t1849.RelTermType = &pb.RelTerm_Term{Term: term1019}
	_t1850 := &pb.RelTerm{}
	_t1850.RelTermType = &pb.RelTerm_Term{Term: term_31020}
	_t1851 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1849, _t1850}}
	result1022 := _t1851
	p.recordSpan(int(span_start1021), "Primitive")
	return result1022
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1025 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1852 := p.parse_term()
	term1023 := _t1852
	_t1853 := p.parse_term()
	term_31024 := _t1853
	p.consumeLiteral(")")
	_t1854 := &pb.RelTerm{}
	_t1854.RelTermType = &pb.RelTerm_Term{Term: term1023}
	_t1855 := &pb.RelTerm{}
	_t1855.RelTermType = &pb.RelTerm_Term{Term: term_31024}
	_t1856 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1854, _t1855}}
	result1026 := _t1856
	p.recordSpan(int(span_start1025), "Primitive")
	return result1026
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1029 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1857 := p.parse_term()
	term1027 := _t1857
	_t1858 := p.parse_term()
	term_31028 := _t1858
	p.consumeLiteral(")")
	_t1859 := &pb.RelTerm{}
	_t1859.RelTermType = &pb.RelTerm_Term{Term: term1027}
	_t1860 := &pb.RelTerm{}
	_t1860.RelTermType = &pb.RelTerm_Term{Term: term_31028}
	_t1861 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1859, _t1860}}
	result1030 := _t1861
	p.recordSpan(int(span_start1029), "Primitive")
	return result1030
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1862 := p.parse_term()
	term1031 := _t1862
	_t1863 := p.parse_term()
	term_31032 := _t1863
	_t1864 := p.parse_term()
	term_41033 := _t1864
	p.consumeLiteral(")")
	_t1865 := &pb.RelTerm{}
	_t1865.RelTermType = &pb.RelTerm_Term{Term: term1031}
	_t1866 := &pb.RelTerm{}
	_t1866.RelTermType = &pb.RelTerm_Term{Term: term_31032}
	_t1867 := &pb.RelTerm{}
	_t1867.RelTermType = &pb.RelTerm_Term{Term: term_41033}
	_t1868 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1865, _t1866, _t1867}}
	result1035 := _t1868
	p.recordSpan(int(span_start1034), "Primitive")
	return result1035
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1039 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1869 := p.parse_term()
	term1036 := _t1869
	_t1870 := p.parse_term()
	term_31037 := _t1870
	_t1871 := p.parse_term()
	term_41038 := _t1871
	p.consumeLiteral(")")
	_t1872 := &pb.RelTerm{}
	_t1872.RelTermType = &pb.RelTerm_Term{Term: term1036}
	_t1873 := &pb.RelTerm{}
	_t1873.RelTermType = &pb.RelTerm_Term{Term: term_31037}
	_t1874 := &pb.RelTerm{}
	_t1874.RelTermType = &pb.RelTerm_Term{Term: term_41038}
	_t1875 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1872, _t1873, _t1874}}
	result1040 := _t1875
	p.recordSpan(int(span_start1039), "Primitive")
	return result1040
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1876 := p.parse_term()
	term1041 := _t1876
	_t1877 := p.parse_term()
	term_31042 := _t1877
	_t1878 := p.parse_term()
	term_41043 := _t1878
	p.consumeLiteral(")")
	_t1879 := &pb.RelTerm{}
	_t1879.RelTermType = &pb.RelTerm_Term{Term: term1041}
	_t1880 := &pb.RelTerm{}
	_t1880.RelTermType = &pb.RelTerm_Term{Term: term_31042}
	_t1881 := &pb.RelTerm{}
	_t1881.RelTermType = &pb.RelTerm_Term{Term: term_41043}
	_t1882 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1879, _t1880, _t1881}}
	result1045 := _t1882
	p.recordSpan(int(span_start1044), "Primitive")
	return result1045
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1049 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1883 := p.parse_term()
	term1046 := _t1883
	_t1884 := p.parse_term()
	term_31047 := _t1884
	_t1885 := p.parse_term()
	term_41048 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.RelTerm{}
	_t1886.RelTermType = &pb.RelTerm_Term{Term: term1046}
	_t1887 := &pb.RelTerm{}
	_t1887.RelTermType = &pb.RelTerm_Term{Term: term_31047}
	_t1888 := &pb.RelTerm{}
	_t1888.RelTermType = &pb.RelTerm_Term{Term: term_41048}
	_t1889 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1886, _t1887, _t1888}}
	result1050 := _t1889
	p.recordSpan(int(span_start1049), "Primitive")
	return result1050
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1054 := int64(p.spanStart())
	var _t1890 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1890 = 1
	} else {
		var _t1891 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1891 = 1
		} else {
			var _t1892 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1892 = 1
			} else {
				var _t1893 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1893 = 1
				} else {
					var _t1894 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1894 = 0
					} else {
						var _t1895 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1895 = 1
						} else {
							var _t1896 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1896 = 1
							} else {
								var _t1897 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1897 = 1
								} else {
									var _t1898 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1898 = 1
									} else {
										var _t1899 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1899 = 1
										} else {
											var _t1900 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1900 = 1
											} else {
												var _t1901 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1901 = 1
												} else {
													var _t1902 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1902 = 1
													} else {
														var _t1903 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1903 = 1
														} else {
															var _t1904 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1904 = 1
															} else {
																_t1904 = -1
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
			_t1891 = _t1892
		}
		_t1890 = _t1891
	}
	prediction1051 := _t1890
	var _t1905 *pb.RelTerm
	if prediction1051 == 1 {
		_t1906 := p.parse_term()
		term1053 := _t1906
		_t1907 := &pb.RelTerm{}
		_t1907.RelTermType = &pb.RelTerm_Term{Term: term1053}
		_t1905 = _t1907
	} else {
		var _t1908 *pb.RelTerm
		if prediction1051 == 0 {
			_t1909 := p.parse_specialized_value()
			specialized_value1052 := _t1909
			_t1910 := &pb.RelTerm{}
			_t1910.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1052}
			_t1908 = _t1910
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1905 = _t1908
	}
	result1055 := _t1905
	p.recordSpan(int(span_start1054), "RelTerm")
	return result1055
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1057 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1911 := p.parse_raw_value()
	raw_value1056 := _t1911
	result1058 := raw_value1056
	p.recordSpan(int(span_start1057), "Value")
	return result1058
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1064 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1912 := p.parse_name()
	name1059 := _t1912
	xs1060 := []*pb.RelTerm{}
	cond1061 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1061 {
		_t1913 := p.parse_rel_term()
		item1062 := _t1913
		xs1060 = append(xs1060, item1062)
		cond1061 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1063 := xs1060
	p.consumeLiteral(")")
	_t1914 := &pb.RelAtom{Name: name1059, Terms: rel_terms1063}
	result1065 := _t1914
	p.recordSpan(int(span_start1064), "RelAtom")
	return result1065
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1915 := p.parse_term()
	term1066 := _t1915
	_t1916 := p.parse_term()
	term_31067 := _t1916
	p.consumeLiteral(")")
	_t1917 := &pb.Cast{Input: term1066, Result: term_31067}
	result1069 := _t1917
	p.recordSpan(int(span_start1068), "Cast")
	return result1069
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1070 := []*pb.Attribute{}
	cond1071 := p.matchLookaheadLiteral("(", 0)
	for cond1071 {
		_t1918 := p.parse_attribute()
		item1072 := _t1918
		xs1070 = append(xs1070, item1072)
		cond1071 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1073 := xs1070
	p.consumeLiteral(")")
	return attributes1073
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1079 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1919 := p.parse_name()
	name1074 := _t1919
	xs1075 := []*pb.Value{}
	cond1076 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1076 {
		_t1920 := p.parse_raw_value()
		item1077 := _t1920
		xs1075 = append(xs1075, item1077)
		cond1076 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1078 := xs1075
	p.consumeLiteral(")")
	_t1921 := &pb.Attribute{Name: name1074, Args: raw_values1078}
	result1080 := _t1921
	p.recordSpan(int(span_start1079), "Attribute")
	return result1080
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1081 := []*pb.RelationId{}
	cond1082 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1082 {
		_t1922 := p.parse_relation_id()
		item1083 := _t1922
		xs1081 = append(xs1081, item1083)
		cond1082 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1084 := xs1081
	_t1923 := p.parse_script()
	script1085 := _t1923
	var _t1924 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1925 := p.parse_attrs()
		_t1924 = _t1925
	}
	attrs1086 := _t1924
	p.consumeLiteral(")")
	_t1926 := attrs1086
	if attrs1086 == nil {
		_t1926 = []*pb.Attribute{}
	}
	_t1927 := &pb.Algorithm{Global: relation_ids1084, Body: script1085, Attrs: _t1926}
	result1088 := _t1927
	p.recordSpan(int(span_start1087), "Algorithm")
	return result1088
}

func (p *Parser) parse_script() *pb.Script {
	span_start1093 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1089 := []*pb.Construct{}
	cond1090 := p.matchLookaheadLiteral("(", 0)
	for cond1090 {
		_t1928 := p.parse_construct()
		item1091 := _t1928
		xs1089 = append(xs1089, item1091)
		cond1090 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1092 := xs1089
	p.consumeLiteral(")")
	_t1929 := &pb.Script{Constructs: constructs1092}
	result1094 := _t1929
	p.recordSpan(int(span_start1093), "Script")
	return result1094
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1098 := int64(p.spanStart())
	var _t1930 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1931 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1931 = 1
		} else {
			var _t1932 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1932 = 1
			} else {
				var _t1933 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1933 = 1
				} else {
					var _t1934 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1934 = 0
					} else {
						var _t1935 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1935 = 1
						} else {
							var _t1936 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1936 = 1
							} else {
								_t1936 = -1
							}
							_t1935 = _t1936
						}
						_t1934 = _t1935
					}
					_t1933 = _t1934
				}
				_t1932 = _t1933
			}
			_t1931 = _t1932
		}
		_t1930 = _t1931
	} else {
		_t1930 = -1
	}
	prediction1095 := _t1930
	var _t1937 *pb.Construct
	if prediction1095 == 1 {
		_t1938 := p.parse_instruction()
		instruction1097 := _t1938
		_t1939 := &pb.Construct{}
		_t1939.ConstructType = &pb.Construct_Instruction{Instruction: instruction1097}
		_t1937 = _t1939
	} else {
		var _t1940 *pb.Construct
		if prediction1095 == 0 {
			_t1941 := p.parse_loop()
			loop1096 := _t1941
			_t1942 := &pb.Construct{}
			_t1942.ConstructType = &pb.Construct_Loop{Loop: loop1096}
			_t1940 = _t1942
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1937 = _t1940
	}
	result1099 := _t1937
	p.recordSpan(int(span_start1098), "Construct")
	return result1099
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1943 := p.parse_init()
	init1100 := _t1943
	_t1944 := p.parse_script()
	script1101 := _t1944
	var _t1945 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1946 := p.parse_attrs()
		_t1945 = _t1946
	}
	attrs1102 := _t1945
	p.consumeLiteral(")")
	_t1947 := attrs1102
	if attrs1102 == nil {
		_t1947 = []*pb.Attribute{}
	}
	_t1948 := &pb.Loop{Init: init1100, Body: script1101, Attrs: _t1947}
	result1104 := _t1948
	p.recordSpan(int(span_start1103), "Loop")
	return result1104
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1105 := []*pb.Instruction{}
	cond1106 := p.matchLookaheadLiteral("(", 0)
	for cond1106 {
		_t1949 := p.parse_instruction()
		item1107 := _t1949
		xs1105 = append(xs1105, item1107)
		cond1106 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1108 := xs1105
	p.consumeLiteral(")")
	return instructions1108
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1115 := int64(p.spanStart())
	var _t1950 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1951 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1951 = 1
		} else {
			var _t1952 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1952 = 4
			} else {
				var _t1953 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1953 = 3
				} else {
					var _t1954 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1954 = 2
					} else {
						var _t1955 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1955 = 0
						} else {
							_t1955 = -1
						}
						_t1954 = _t1955
					}
					_t1953 = _t1954
				}
				_t1952 = _t1953
			}
			_t1951 = _t1952
		}
		_t1950 = _t1951
	} else {
		_t1950 = -1
	}
	prediction1109 := _t1950
	var _t1956 *pb.Instruction
	if prediction1109 == 4 {
		_t1957 := p.parse_monus_def()
		monus_def1114 := _t1957
		_t1958 := &pb.Instruction{}
		_t1958.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1114}
		_t1956 = _t1958
	} else {
		var _t1959 *pb.Instruction
		if prediction1109 == 3 {
			_t1960 := p.parse_monoid_def()
			monoid_def1113 := _t1960
			_t1961 := &pb.Instruction{}
			_t1961.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1113}
			_t1959 = _t1961
		} else {
			var _t1962 *pb.Instruction
			if prediction1109 == 2 {
				_t1963 := p.parse_break()
				break1112 := _t1963
				_t1964 := &pb.Instruction{}
				_t1964.InstrType = &pb.Instruction_Break{Break: break1112}
				_t1962 = _t1964
			} else {
				var _t1965 *pb.Instruction
				if prediction1109 == 1 {
					_t1966 := p.parse_upsert()
					upsert1111 := _t1966
					_t1967 := &pb.Instruction{}
					_t1967.InstrType = &pb.Instruction_Upsert{Upsert: upsert1111}
					_t1965 = _t1967
				} else {
					var _t1968 *pb.Instruction
					if prediction1109 == 0 {
						_t1969 := p.parse_assign()
						assign1110 := _t1969
						_t1970 := &pb.Instruction{}
						_t1970.InstrType = &pb.Instruction_Assign{Assign: assign1110}
						_t1968 = _t1970
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1965 = _t1968
				}
				_t1962 = _t1965
			}
			_t1959 = _t1962
		}
		_t1956 = _t1959
	}
	result1116 := _t1956
	p.recordSpan(int(span_start1115), "Instruction")
	return result1116
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1120 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1971 := p.parse_relation_id()
	relation_id1117 := _t1971
	_t1972 := p.parse_abstraction()
	abstraction1118 := _t1972
	var _t1973 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1974 := p.parse_attrs()
		_t1973 = _t1974
	}
	attrs1119 := _t1973
	p.consumeLiteral(")")
	_t1975 := attrs1119
	if attrs1119 == nil {
		_t1975 = []*pb.Attribute{}
	}
	_t1976 := &pb.Assign{Name: relation_id1117, Body: abstraction1118, Attrs: _t1975}
	result1121 := _t1976
	p.recordSpan(int(span_start1120), "Assign")
	return result1121
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1977 := p.parse_relation_id()
	relation_id1122 := _t1977
	_t1978 := p.parse_abstraction_with_arity()
	abstraction_with_arity1123 := _t1978
	var _t1979 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1980 := p.parse_attrs()
		_t1979 = _t1980
	}
	attrs1124 := _t1979
	p.consumeLiteral(")")
	_t1981 := attrs1124
	if attrs1124 == nil {
		_t1981 = []*pb.Attribute{}
	}
	_t1982 := &pb.Upsert{Name: relation_id1122, Body: abstraction_with_arity1123[0].(*pb.Abstraction), Attrs: _t1981, ValueArity: abstraction_with_arity1123[1].(int64)}
	result1126 := _t1982
	p.recordSpan(int(span_start1125), "Upsert")
	return result1126
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1983 := p.parse_bindings()
	bindings1127 := _t1983
	_t1984 := p.parse_formula()
	formula1128 := _t1984
	p.consumeLiteral(")")
	_t1985 := &pb.Abstraction{Vars: listConcat(bindings1127[0].([]*pb.Binding), bindings1127[1].([]*pb.Binding)), Value: formula1128}
	return []interface{}{_t1985, int64(len(bindings1127[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1132 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1986 := p.parse_relation_id()
	relation_id1129 := _t1986
	_t1987 := p.parse_abstraction()
	abstraction1130 := _t1987
	var _t1988 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1989 := p.parse_attrs()
		_t1988 = _t1989
	}
	attrs1131 := _t1988
	p.consumeLiteral(")")
	_t1990 := attrs1131
	if attrs1131 == nil {
		_t1990 = []*pb.Attribute{}
	}
	_t1991 := &pb.Break{Name: relation_id1129, Body: abstraction1130, Attrs: _t1990}
	result1133 := _t1991
	p.recordSpan(int(span_start1132), "Break")
	return result1133
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1992 := p.parse_monoid()
	monoid1134 := _t1992
	_t1993 := p.parse_relation_id()
	relation_id1135 := _t1993
	_t1994 := p.parse_abstraction_with_arity()
	abstraction_with_arity1136 := _t1994
	var _t1995 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1996 := p.parse_attrs()
		_t1995 = _t1996
	}
	attrs1137 := _t1995
	p.consumeLiteral(")")
	_t1997 := attrs1137
	if attrs1137 == nil {
		_t1997 = []*pb.Attribute{}
	}
	_t1998 := &pb.MonoidDef{Monoid: monoid1134, Name: relation_id1135, Body: abstraction_with_arity1136[0].(*pb.Abstraction), Attrs: _t1997, ValueArity: abstraction_with_arity1136[1].(int64)}
	result1139 := _t1998
	p.recordSpan(int(span_start1138), "MonoidDef")
	return result1139
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1145 := int64(p.spanStart())
	var _t1999 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2000 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t2000 = 3
		} else {
			var _t2001 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t2001 = 0
			} else {
				var _t2002 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t2002 = 1
				} else {
					var _t2003 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t2003 = 2
					} else {
						_t2003 = -1
					}
					_t2002 = _t2003
				}
				_t2001 = _t2002
			}
			_t2000 = _t2001
		}
		_t1999 = _t2000
	} else {
		_t1999 = -1
	}
	prediction1140 := _t1999
	var _t2004 *pb.Monoid
	if prediction1140 == 3 {
		_t2005 := p.parse_sum_monoid()
		sum_monoid1144 := _t2005
		_t2006 := &pb.Monoid{}
		_t2006.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1144}
		_t2004 = _t2006
	} else {
		var _t2007 *pb.Monoid
		if prediction1140 == 2 {
			_t2008 := p.parse_max_monoid()
			max_monoid1143 := _t2008
			_t2009 := &pb.Monoid{}
			_t2009.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1143}
			_t2007 = _t2009
		} else {
			var _t2010 *pb.Monoid
			if prediction1140 == 1 {
				_t2011 := p.parse_min_monoid()
				min_monoid1142 := _t2011
				_t2012 := &pb.Monoid{}
				_t2012.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1142}
				_t2010 = _t2012
			} else {
				var _t2013 *pb.Monoid
				if prediction1140 == 0 {
					_t2014 := p.parse_or_monoid()
					or_monoid1141 := _t2014
					_t2015 := &pb.Monoid{}
					_t2015.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1141}
					_t2013 = _t2015
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2010 = _t2013
			}
			_t2007 = _t2010
		}
		_t2004 = _t2007
	}
	result1146 := _t2004
	p.recordSpan(int(span_start1145), "Monoid")
	return result1146
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1147 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t2016 := &pb.OrMonoid{}
	result1148 := _t2016
	p.recordSpan(int(span_start1147), "OrMonoid")
	return result1148
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t2017 := p.parse_type()
	type1149 := _t2017
	p.consumeLiteral(")")
	_t2018 := &pb.MinMonoid{Type: type1149}
	result1151 := _t2018
	p.recordSpan(int(span_start1150), "MinMonoid")
	return result1151
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1153 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t2019 := p.parse_type()
	type1152 := _t2019
	p.consumeLiteral(")")
	_t2020 := &pb.MaxMonoid{Type: type1152}
	result1154 := _t2020
	p.recordSpan(int(span_start1153), "MaxMonoid")
	return result1154
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t2021 := p.parse_type()
	type1155 := _t2021
	p.consumeLiteral(")")
	_t2022 := &pb.SumMonoid{Type: type1155}
	result1157 := _t2022
	p.recordSpan(int(span_start1156), "SumMonoid")
	return result1157
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1162 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t2023 := p.parse_monoid()
	monoid1158 := _t2023
	_t2024 := p.parse_relation_id()
	relation_id1159 := _t2024
	_t2025 := p.parse_abstraction_with_arity()
	abstraction_with_arity1160 := _t2025
	var _t2026 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2027 := p.parse_attrs()
		_t2026 = _t2027
	}
	attrs1161 := _t2026
	p.consumeLiteral(")")
	_t2028 := attrs1161
	if attrs1161 == nil {
		_t2028 = []*pb.Attribute{}
	}
	_t2029 := &pb.MonusDef{Monoid: monoid1158, Name: relation_id1159, Body: abstraction_with_arity1160[0].(*pb.Abstraction), Attrs: _t2028, ValueArity: abstraction_with_arity1160[1].(int64)}
	result1163 := _t2029
	p.recordSpan(int(span_start1162), "MonusDef")
	return result1163
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1168 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2030 := p.parse_relation_id()
	relation_id1164 := _t2030
	_t2031 := p.parse_abstraction()
	abstraction1165 := _t2031
	_t2032 := p.parse_functional_dependency_keys()
	functional_dependency_keys1166 := _t2032
	_t2033 := p.parse_functional_dependency_values()
	functional_dependency_values1167 := _t2033
	p.consumeLiteral(")")
	_t2034 := &pb.FunctionalDependency{Guard: abstraction1165, Keys: functional_dependency_keys1166, Values: functional_dependency_values1167}
	_t2035 := &pb.Constraint{Name: relation_id1164}
	_t2035.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2034}
	result1169 := _t2035
	p.recordSpan(int(span_start1168), "Constraint")
	return result1169
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1170 := []*pb.Var{}
	cond1171 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1171 {
		_t2036 := p.parse_var()
		item1172 := _t2036
		xs1170 = append(xs1170, item1172)
		cond1171 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1173 := xs1170
	p.consumeLiteral(")")
	return vars1173
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1174 := []*pb.Var{}
	cond1175 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1175 {
		_t2037 := p.parse_var()
		item1176 := _t2037
		xs1174 = append(xs1174, item1176)
		cond1175 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1177 := xs1174
	p.consumeLiteral(")")
	return vars1177
}

func (p *Parser) parse_data() *pb.Data {
	span_start1183 := int64(p.spanStart())
	var _t2038 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2039 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2039 = 3
		} else {
			var _t2040 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2040 = 0
			} else {
				var _t2041 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2041 = 2
				} else {
					var _t2042 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2042 = 1
					} else {
						_t2042 = -1
					}
					_t2041 = _t2042
				}
				_t2040 = _t2041
			}
			_t2039 = _t2040
		}
		_t2038 = _t2039
	} else {
		_t2038 = -1
	}
	prediction1178 := _t2038
	var _t2043 *pb.Data
	if prediction1178 == 3 {
		_t2044 := p.parse_iceberg_data()
		iceberg_data1182 := _t2044
		_t2045 := &pb.Data{}
		_t2045.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1182}
		_t2043 = _t2045
	} else {
		var _t2046 *pb.Data
		if prediction1178 == 2 {
			_t2047 := p.parse_csv_data()
			csv_data1181 := _t2047
			_t2048 := &pb.Data{}
			_t2048.DataType = &pb.Data_CsvData{CsvData: csv_data1181}
			_t2046 = _t2048
		} else {
			var _t2049 *pb.Data
			if prediction1178 == 1 {
				_t2050 := p.parse_betree_relation()
				betree_relation1180 := _t2050
				_t2051 := &pb.Data{}
				_t2051.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1180}
				_t2049 = _t2051
			} else {
				var _t2052 *pb.Data
				if prediction1178 == 0 {
					_t2053 := p.parse_edb()
					edb1179 := _t2053
					_t2054 := &pb.Data{}
					_t2054.DataType = &pb.Data_Edb{Edb: edb1179}
					_t2052 = _t2054
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2049 = _t2052
			}
			_t2046 = _t2049
		}
		_t2043 = _t2046
	}
	result1184 := _t2043
	p.recordSpan(int(span_start1183), "Data")
	return result1184
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1188 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2055 := p.parse_relation_id()
	relation_id1185 := _t2055
	_t2056 := p.parse_edb_path()
	edb_path1186 := _t2056
	_t2057 := p.parse_edb_types()
	edb_types1187 := _t2057
	p.consumeLiteral(")")
	_t2058 := &pb.EDB{TargetId: relation_id1185, Path: edb_path1186, Types: edb_types1187}
	result1189 := _t2058
	p.recordSpan(int(span_start1188), "EDB")
	return result1189
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1190 := []string{}
	cond1191 := p.matchLookaheadTerminal("STRING", 0)
	for cond1191 {
		item1192 := p.consumeTerminal("STRING").Value.str
		xs1190 = append(xs1190, item1192)
		cond1191 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1193 := xs1190
	p.consumeLiteral("]")
	return strings1193
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1194 := []*pb.Type{}
	cond1195 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1195 {
		_t2059 := p.parse_type()
		item1196 := _t2059
		xs1194 = append(xs1194, item1196)
		cond1195 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1197 := xs1194
	p.consumeLiteral("]")
	return types1197
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1200 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2060 := p.parse_relation_id()
	relation_id1198 := _t2060
	_t2061 := p.parse_betree_info()
	betree_info1199 := _t2061
	p.consumeLiteral(")")
	_t2062 := &pb.BeTreeRelation{Name: relation_id1198, RelationInfo: betree_info1199}
	result1201 := _t2062
	p.recordSpan(int(span_start1200), "BeTreeRelation")
	return result1201
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1205 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2063 := p.parse_betree_info_key_types()
	betree_info_key_types1202 := _t2063
	_t2064 := p.parse_betree_info_value_types()
	betree_info_value_types1203 := _t2064
	_t2065 := p.parse_config_dict()
	config_dict1204 := _t2065
	p.consumeLiteral(")")
	_t2066 := p.construct_betree_info(betree_info_key_types1202, betree_info_value_types1203, config_dict1204)
	result1206 := _t2066
	p.recordSpan(int(span_start1205), "BeTreeInfo")
	return result1206
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1207 := []*pb.Type{}
	cond1208 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1208 {
		_t2067 := p.parse_type()
		item1209 := _t2067
		xs1207 = append(xs1207, item1209)
		cond1208 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1210 := xs1207
	p.consumeLiteral(")")
	return types1210
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1211 := []*pb.Type{}
	cond1212 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1212 {
		_t2068 := p.parse_type()
		item1213 := _t2068
		xs1211 = append(xs1211, item1213)
		cond1212 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1214 := xs1211
	p.consumeLiteral(")")
	return types1214
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2069 := p.parse_csvlocator()
	csvlocator1215 := _t2069
	_t2070 := p.parse_csv_config()
	csv_config1216 := _t2070
	var _t2071 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2072 := p.parse_gnf_columns()
		_t2071 = _t2072
	}
	gnf_columns1217 := _t2071
	var _t2073 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2074 := p.parse_target_relations()
		_t2073 = _t2074
	}
	target_relations1218 := _t2073
	_t2075 := p.parse_csv_asof()
	csv_asof1219 := _t2075
	p.consumeLiteral(")")
	_t2076 := p.construct_csv_data(csvlocator1215, csv_config1216, gnf_columns1217, target_relations1218, csv_asof1219)
	result1221 := _t2076
	p.recordSpan(int(span_start1220), "CSVData")
	return result1221
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1224 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2077 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2078 := p.parse_csv_locator_paths()
		_t2077 = _t2078
	}
	csv_locator_paths1222 := _t2077
	var _t2079 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2080 := p.parse_csv_locator_inline_data()
		_t2079 = ptr(_t2080)
	}
	csv_locator_inline_data1223 := _t2079
	p.consumeLiteral(")")
	_t2081 := csv_locator_paths1222
	if csv_locator_paths1222 == nil {
		_t2081 = []string{}
	}
	_t2082 := &pb.CSVLocator{Paths: _t2081, InlineData: []byte(deref(csv_locator_inline_data1223, ""))}
	result1225 := _t2082
	p.recordSpan(int(span_start1224), "CSVLocator")
	return result1225
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1226 := []string{}
	cond1227 := p.matchLookaheadTerminal("STRING", 0)
	for cond1227 {
		item1228 := p.consumeTerminal("STRING").Value.str
		xs1226 = append(xs1226, item1228)
		cond1227 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1229 := xs1226
	p.consumeLiteral(")")
	return strings1229
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1230 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1230
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1233 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2083 := p.parse_config_dict()
	config_dict1231 := _t2083
	var _t2084 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2085 := p.parse__storage_integration()
		_t2084 = _t2085
	}
	_storage_integration1232 := _t2084
	p.consumeLiteral(")")
	_t2086 := p.construct_csv_config(config_dict1231, _storage_integration1232)
	result1234 := _t2086
	p.recordSpan(int(span_start1233), "CSVConfig")
	return result1234
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2087 := p.parse_config_dict()
	config_dict1235 := _t2087
	p.consumeLiteral(")")
	return config_dict1235
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1236 := []*pb.GNFColumn{}
	cond1237 := p.matchLookaheadLiteral("(", 0)
	for cond1237 {
		_t2088 := p.parse_gnf_column()
		item1238 := _t2088
		xs1236 = append(xs1236, item1238)
		cond1237 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1239 := xs1236
	p.consumeLiteral(")")
	return gnf_columns1239
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1246 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2089 := p.parse_gnf_column_path()
	gnf_column_path1240 := _t2089
	var _t2090 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2091 := p.parse_relation_id()
		_t2090 = _t2091
	}
	relation_id1241 := _t2090
	p.consumeLiteral("[")
	xs1242 := []*pb.Type{}
	cond1243 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1243 {
		_t2092 := p.parse_type()
		item1244 := _t2092
		xs1242 = append(xs1242, item1244)
		cond1243 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1245 := xs1242
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2093 := &pb.GNFColumn{ColumnPath: gnf_column_path1240, TargetId: relation_id1241, Types: types1245}
	result1247 := _t2093
	p.recordSpan(int(span_start1246), "GNFColumn")
	return result1247
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2094 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2094 = 1
	} else {
		var _t2095 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2095 = 0
		} else {
			_t2095 = -1
		}
		_t2094 = _t2095
	}
	prediction1248 := _t2094
	var _t2096 []string
	if prediction1248 == 1 {
		p.consumeLiteral("[")
		xs1250 := []string{}
		cond1251 := p.matchLookaheadTerminal("STRING", 0)
		for cond1251 {
			item1252 := p.consumeTerminal("STRING").Value.str
			xs1250 = append(xs1250, item1252)
			cond1251 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1253 := xs1250
		p.consumeLiteral("]")
		_t2096 = strings1253
	} else {
		var _t2097 []string
		if prediction1248 == 0 {
			string1249 := p.consumeTerminal("STRING").Value.str
			_ = string1249
			_t2097 = []string{string1249}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2096 = _t2097
	}
	return _t2096
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1257 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2098 := p.parse_relation_keys()
	relation_keys1254 := _t2098
	_t2099 := p.parse_relation_body()
	relation_body1255 := _t2099
	var _t2100 *pb.RelationId
	if p.matchLookaheadLiteral("(", 0) {
		_t2101 := p.parse_load_errors()
		_t2100 = _t2101
	}
	load_errors1256 := _t2100
	p.consumeLiteral(")")
	_t2102 := p.construct_relations(relation_keys1254, relation_body1255, load_errors1256)
	result1258 := _t2102
	p.recordSpan(int(span_start1257), "TargetRelations")
	return result1258
}

func (p *Parser) parse_relation_keys() []interface{} {
	var _t2103 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2104 int64
		if p.matchLookaheadLiteral("keys", 1) {
			var _t2105 int64
			if p.matchLookaheadLiteral("synthetic", 2) {
				_t2105 = 1
			} else {
				var _t2106 int64
				if p.matchLookaheadLiteral(")", 2) {
					_t2106 = 0
				} else {
					var _t2107 int64
					if p.matchLookaheadLiteral("(", 2) {
						_t2107 = 0
					} else {
						_t2107 = -1
					}
					_t2106 = _t2107
				}
				_t2105 = _t2106
			}
			_t2104 = _t2105
		} else {
			_t2104 = -1
		}
		_t2103 = _t2104
	} else {
		_t2103 = -1
	}
	prediction1259 := _t2103
	var _t2108 []interface{}
	if prediction1259 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("keys")
		p.consumeLiteral("synthetic")
		p.consumeLiteral(")")
		_t2108 = []interface{}{[]*pb.NamedColumn{}, true}
	} else {
		var _t2109 []interface{}
		if prediction1259 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("keys")
			xs1260 := []*pb.NamedColumn{}
			cond1261 := p.matchLookaheadLiteral("(", 0)
			for cond1261 {
				_t2110 := p.parse_named_column()
				item1262 := _t2110
				xs1260 = append(xs1260, item1262)
				cond1261 = p.matchLookaheadLiteral("(", 0)
			}
			named_columns1263 := xs1260
			p.consumeLiteral(")")
			_t2109 = []interface{}{named_columns1263, false}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_keys", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2108 = _t2109
	}
	return _t2108
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1266 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1264 := p.consumeTerminal("STRING").Value.str
	_t2111 := p.parse_type()
	type1265 := _t2111
	p.consumeLiteral(")")
	_t2112 := &pb.NamedColumn{Name: string1264, Type: type1265}
	result1267 := _t2112
	p.recordSpan(int(span_start1266), "NamedColumn")
	return result1267
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1272 := int64(p.spanStart())
	var _t2113 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2114 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2114 = 0
		} else {
			var _t2115 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2115 = 1
			} else {
				_t2115 = 0
			}
			_t2114 = _t2115
		}
		_t2113 = _t2114
	} else {
		_t2113 = 0
	}
	prediction1268 := _t2113
	var _t2116 *pb.TargetRelations
	if prediction1268 == 1 {
		_t2117 := p.parse_cdc_inserts()
		cdc_inserts1270 := _t2117
		_t2118 := p.parse_cdc_deletes()
		cdc_deletes1271 := _t2118
		_t2119 := p.construct_cdc_relations(cdc_inserts1270, cdc_deletes1271)
		_t2116 = _t2119
	} else {
		var _t2120 *pb.TargetRelations
		if prediction1268 == 0 {
			_t2121 := p.parse_non_cdc_relations()
			non_cdc_relations1269 := _t2121
			_t2122 := p.construct_non_cdc_relations(non_cdc_relations1269)
			_t2120 = _t2122
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2116 = _t2120
	}
	result1273 := _t2116
	p.recordSpan(int(span_start1272), "TargetRelations")
	return result1273
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1274 := []*pb.TargetRelation{}
	cond1275 := (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	for cond1275 {
		_t2123 := p.parse_target_relation()
		item1276 := _t2123
		xs1274 = append(xs1274, item1276)
		cond1275 = (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relation", 1))
	}
	return xs1274
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1282 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2124 := p.parse_relation_id()
	relation_id1277 := _t2124
	xs1278 := []*pb.NamedColumn{}
	cond1279 := p.matchLookaheadLiteral("(", 0)
	for cond1279 {
		_t2125 := p.parse_named_column()
		item1280 := _t2125
		xs1278 = append(xs1278, item1280)
		cond1279 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1281 := xs1278
	p.consumeLiteral(")")
	_t2126 := &pb.TargetRelation{TargetId: relation_id1277, Values: named_columns1281}
	result1283 := _t2126
	p.recordSpan(int(span_start1282), "TargetRelation")
	return result1283
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1284 := []*pb.TargetRelation{}
	cond1285 := p.matchLookaheadLiteral("(", 0)
	for cond1285 {
		_t2127 := p.parse_target_relation()
		item1286 := _t2127
		xs1284 = append(xs1284, item1286)
		cond1285 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1287 := xs1284
	p.consumeLiteral(")")
	return target_relations1287
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1288 := []*pb.TargetRelation{}
	cond1289 := p.matchLookaheadLiteral("(", 0)
	for cond1289 {
		_t2128 := p.parse_target_relation()
		item1290 := _t2128
		xs1288 = append(xs1288, item1290)
		cond1289 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1291 := xs1288
	p.consumeLiteral(")")
	return target_relations1291
}

func (p *Parser) parse_load_errors() *pb.RelationId {
	span_start1293 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("load_errors")
	_t2129 := p.parse_relation_id()
	relation_id1292 := _t2129
	p.consumeLiteral(")")
	result1294 := relation_id1292
	p.recordSpan(int(span_start1293), "RelationId")
	return result1294
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1295 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1295
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1302 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2130 := p.parse_iceberg_locator()
	iceberg_locator1296 := _t2130
	_t2131 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1297 := _t2131
	_t2132 := p.parse_gnf_columns()
	gnf_columns1298 := _t2132
	var _t2133 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2134 := p.parse_iceberg_from_snapshot()
		_t2133 = ptr(_t2134)
	}
	iceberg_from_snapshot1299 := _t2133
	var _t2135 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2136 := p.parse_iceberg_to_snapshot()
		_t2135 = ptr(_t2136)
	}
	iceberg_to_snapshot1300 := _t2135
	_t2137 := p.parse_boolean_value()
	boolean_value1301 := _t2137
	p.consumeLiteral(")")
	_t2138 := p.construct_iceberg_data(iceberg_locator1296, iceberg_catalog_config1297, gnf_columns1298, iceberg_from_snapshot1299, iceberg_to_snapshot1300, boolean_value1301)
	result1303 := _t2138
	p.recordSpan(int(span_start1302), "IcebergData")
	return result1303
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1307 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2139 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1304 := _t2139
	_t2140 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1305 := _t2140
	_t2141 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1306 := _t2141
	p.consumeLiteral(")")
	_t2142 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1304, Namespace: iceberg_locator_namespace1305, Warehouse: iceberg_locator_warehouse1306}
	result1308 := _t2142
	p.recordSpan(int(span_start1307), "IcebergLocator")
	return result1308
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1309 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1309
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1310 := []string{}
	cond1311 := p.matchLookaheadTerminal("STRING", 0)
	for cond1311 {
		item1312 := p.consumeTerminal("STRING").Value.str
		xs1310 = append(xs1310, item1312)
		cond1311 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1313 := xs1310
	p.consumeLiteral(")")
	return strings1313
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1314 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1314
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1319 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2143 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1315 := _t2143
	var _t2144 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2145 := p.parse_iceberg_catalog_config_scope()
		_t2144 = ptr(_t2145)
	}
	iceberg_catalog_config_scope1316 := _t2144
	_t2146 := p.parse_iceberg_properties()
	iceberg_properties1317 := _t2146
	_t2147 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1318 := _t2147
	p.consumeLiteral(")")
	_t2148 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1315, iceberg_catalog_config_scope1316, iceberg_properties1317, iceberg_auth_properties1318)
	result1320 := _t2148
	p.recordSpan(int(span_start1319), "IcebergCatalogConfig")
	return result1320
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1321 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1321
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1322 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1322
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1323 := [][]interface{}{}
	cond1324 := p.matchLookaheadLiteral("(", 0)
	for cond1324 {
		_t2149 := p.parse_iceberg_property_entry()
		item1325 := _t2149
		xs1323 = append(xs1323, item1325)
		cond1324 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1326 := xs1323
	p.consumeLiteral(")")
	return iceberg_property_entrys1326
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1327 := p.consumeTerminal("STRING").Value.str
	string_31328 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1327, string_31328}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1329 := [][]interface{}{}
	cond1330 := p.matchLookaheadLiteral("(", 0)
	for cond1330 {
		_t2150 := p.parse_iceberg_masked_property_entry()
		item1331 := _t2150
		xs1329 = append(xs1329, item1331)
		cond1330 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1332 := xs1329
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1332
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1333 := p.consumeTerminal("STRING").Value.str
	string_31334 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1333, string_31334}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1335 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1335
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1336 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1336
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1338 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2151 := p.parse_fragment_id()
	fragment_id1337 := _t2151
	p.consumeLiteral(")")
	_t2152 := &pb.Undefine{FragmentId: fragment_id1337}
	result1339 := _t2152
	p.recordSpan(int(span_start1338), "Undefine")
	return result1339
}

func (p *Parser) parse_context() *pb.Context {
	span_start1344 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1340 := []*pb.RelationId{}
	cond1341 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1341 {
		_t2153 := p.parse_relation_id()
		item1342 := _t2153
		xs1340 = append(xs1340, item1342)
		cond1341 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1343 := xs1340
	p.consumeLiteral(")")
	_t2154 := &pb.Context{Relations: relation_ids1343}
	result1345 := _t2154
	p.recordSpan(int(span_start1344), "Context")
	return result1345
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1351 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2155 := p.parse_edb_path()
	edb_path1346 := _t2155
	xs1347 := []*pb.SnapshotMapping{}
	cond1348 := p.matchLookaheadLiteral("[", 0)
	for cond1348 {
		_t2156 := p.parse_snapshot_mapping()
		item1349 := _t2156
		xs1347 = append(xs1347, item1349)
		cond1348 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1350 := xs1347
	p.consumeLiteral(")")
	_t2157 := &pb.Snapshot{Prefix: edb_path1346, Mappings: snapshot_mappings1350}
	result1352 := _t2157
	p.recordSpan(int(span_start1351), "Snapshot")
	return result1352
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1355 := int64(p.spanStart())
	_t2158 := p.parse_edb_path()
	edb_path1353 := _t2158
	_t2159 := p.parse_relation_id()
	relation_id1354 := _t2159
	_t2160 := &pb.SnapshotMapping{DestinationPath: edb_path1353, SourceRelation: relation_id1354}
	result1356 := _t2160
	p.recordSpan(int(span_start1355), "SnapshotMapping")
	return result1356
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1357 := []*pb.Read{}
	cond1358 := p.matchLookaheadLiteral("(", 0)
	for cond1358 {
		_t2161 := p.parse_read()
		item1359 := _t2161
		xs1357 = append(xs1357, item1359)
		cond1358 = p.matchLookaheadLiteral("(", 0)
	}
	reads1360 := xs1357
	p.consumeLiteral(")")
	return reads1360
}

func (p *Parser) parse_read() *pb.Read {
	span_start1367 := int64(p.spanStart())
	var _t2162 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2163 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2163 = 2
		} else {
			var _t2164 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2164 = 1
			} else {
				var _t2165 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2165 = 4
				} else {
					var _t2166 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2166 = 4
					} else {
						var _t2167 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2167 = 0
						} else {
							var _t2168 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2168 = 3
							} else {
								_t2168 = -1
							}
							_t2167 = _t2168
						}
						_t2166 = _t2167
					}
					_t2165 = _t2166
				}
				_t2164 = _t2165
			}
			_t2163 = _t2164
		}
		_t2162 = _t2163
	} else {
		_t2162 = -1
	}
	prediction1361 := _t2162
	var _t2169 *pb.Read
	if prediction1361 == 4 {
		_t2170 := p.parse_export()
		export1366 := _t2170
		_t2171 := &pb.Read{}
		_t2171.ReadType = &pb.Read_Export{Export: export1366}
		_t2169 = _t2171
	} else {
		var _t2172 *pb.Read
		if prediction1361 == 3 {
			_t2173 := p.parse_abort()
			abort1365 := _t2173
			_t2174 := &pb.Read{}
			_t2174.ReadType = &pb.Read_Abort{Abort: abort1365}
			_t2172 = _t2174
		} else {
			var _t2175 *pb.Read
			if prediction1361 == 2 {
				_t2176 := p.parse_what_if()
				what_if1364 := _t2176
				_t2177 := &pb.Read{}
				_t2177.ReadType = &pb.Read_WhatIf{WhatIf: what_if1364}
				_t2175 = _t2177
			} else {
				var _t2178 *pb.Read
				if prediction1361 == 1 {
					_t2179 := p.parse_output()
					output1363 := _t2179
					_t2180 := &pb.Read{}
					_t2180.ReadType = &pb.Read_Output{Output: output1363}
					_t2178 = _t2180
				} else {
					var _t2181 *pb.Read
					if prediction1361 == 0 {
						_t2182 := p.parse_demand()
						demand1362 := _t2182
						_t2183 := &pb.Read{}
						_t2183.ReadType = &pb.Read_Demand{Demand: demand1362}
						_t2181 = _t2183
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2178 = _t2181
				}
				_t2175 = _t2178
			}
			_t2172 = _t2175
		}
		_t2169 = _t2172
	}
	result1368 := _t2169
	p.recordSpan(int(span_start1367), "Read")
	return result1368
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1370 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2184 := p.parse_relation_id()
	relation_id1369 := _t2184
	p.consumeLiteral(")")
	_t2185 := &pb.Demand{RelationId: relation_id1369}
	result1371 := _t2185
	p.recordSpan(int(span_start1370), "Demand")
	return result1371
}

func (p *Parser) parse_output() *pb.Output {
	span_start1374 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2186 := p.parse_name()
	name1372 := _t2186
	_t2187 := p.parse_relation_id()
	relation_id1373 := _t2187
	p.consumeLiteral(")")
	_t2188 := &pb.Output{Name: name1372, RelationId: relation_id1373}
	result1375 := _t2188
	p.recordSpan(int(span_start1374), "Output")
	return result1375
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1378 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2189 := p.parse_name()
	name1376 := _t2189
	_t2190 := p.parse_epoch()
	epoch1377 := _t2190
	p.consumeLiteral(")")
	_t2191 := &pb.WhatIf{Branch: name1376, Epoch: epoch1377}
	result1379 := _t2191
	p.recordSpan(int(span_start1378), "WhatIf")
	return result1379
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1382 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2192 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2193 := p.parse_name()
		_t2192 = ptr(_t2193)
	}
	name1380 := _t2192
	_t2194 := p.parse_relation_id()
	relation_id1381 := _t2194
	p.consumeLiteral(")")
	_t2195 := &pb.Abort{Name: deref(name1380, "abort"), RelationId: relation_id1381}
	result1383 := _t2195
	p.recordSpan(int(span_start1382), "Abort")
	return result1383
}

func (p *Parser) parse_export() *pb.Export {
	span_start1387 := int64(p.spanStart())
	var _t2196 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2197 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2197 = 1
		} else {
			var _t2198 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2198 = 0
			} else {
				_t2198 = -1
			}
			_t2197 = _t2198
		}
		_t2196 = _t2197
	} else {
		_t2196 = -1
	}
	prediction1384 := _t2196
	var _t2199 *pb.Export
	if prediction1384 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2200 := p.parse_export_iceberg_config()
		export_iceberg_config1386 := _t2200
		p.consumeLiteral(")")
		_t2201 := &pb.Export{}
		_t2201.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1386}
		_t2199 = _t2201
	} else {
		var _t2202 *pb.Export
		if prediction1384 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2203 := p.parse_export_csv_config()
			export_csv_config1385 := _t2203
			p.consumeLiteral(")")
			_t2204 := &pb.Export{}
			_t2204.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1385}
			_t2202 = _t2204
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2199 = _t2202
	}
	result1388 := _t2199
	p.recordSpan(int(span_start1387), "Export")
	return result1388
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1396 := int64(p.spanStart())
	var _t2205 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2206 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2206 = 0
		} else {
			var _t2207 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2207 = 1
			} else {
				_t2207 = -1
			}
			_t2206 = _t2207
		}
		_t2205 = _t2206
	} else {
		_t2205 = -1
	}
	prediction1389 := _t2205
	var _t2208 *pb.ExportCSVConfig
	if prediction1389 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2209 := p.parse_export_csv_path()
		export_csv_path1393 := _t2209
		_t2210 := p.parse_export_csv_columns_list()
		export_csv_columns_list1394 := _t2210
		_t2211 := p.parse_config_dict()
		config_dict1395 := _t2211
		p.consumeLiteral(")")
		_t2212 := p.construct_export_csv_config(export_csv_path1393, export_csv_columns_list1394, config_dict1395)
		_t2208 = _t2212
	} else {
		var _t2213 *pb.ExportCSVConfig
		if prediction1389 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2214 := p.parse_export_csv_output_location()
			export_csv_output_location1390 := _t2214
			_t2215 := p.parse_export_csv_source()
			export_csv_source1391 := _t2215
			_t2216 := p.parse_csv_config()
			csv_config1392 := _t2216
			p.consumeLiteral(")")
			_t2217 := p.construct_export_csv_config_with_location(export_csv_output_location1390, export_csv_source1391, csv_config1392)
			_t2213 = _t2217
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2208 = _t2213
	}
	result1397 := _t2208
	p.recordSpan(int(span_start1396), "ExportCSVConfig")
	return result1397
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2218 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2219 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2219 = 1
		} else {
			var _t2220 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2220 = 0
			} else {
				_t2220 = -1
			}
			_t2219 = _t2220
		}
		_t2218 = _t2219
	} else {
		_t2218 = -1
	}
	prediction1398 := _t2218
	var _t2221 []interface{}
	if prediction1398 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2222 := p.parse_name()
		name1400 := _t2222
		p.consumeLiteral(")")
		_t2221 = []interface{}{"", name1400}
	} else {
		var _t2223 []interface{}
		if prediction1398 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1399 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2223 = []interface{}{string1399, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2221 = _t2223
	}
	return _t2221
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1407 := int64(p.spanStart())
	var _t2224 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2225 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2225 = 1
		} else {
			var _t2226 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2226 = 0
			} else {
				_t2226 = -1
			}
			_t2225 = _t2226
		}
		_t2224 = _t2225
	} else {
		_t2224 = -1
	}
	prediction1401 := _t2224
	var _t2227 *pb.ExportCSVSource
	if prediction1401 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2228 := p.parse_relation_id()
		relation_id1406 := _t2228
		p.consumeLiteral(")")
		_t2229 := &pb.ExportCSVSource{}
		_t2229.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1406}
		_t2227 = _t2229
	} else {
		var _t2230 *pb.ExportCSVSource
		if prediction1401 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1402 := []*pb.ExportCSVColumn{}
			cond1403 := p.matchLookaheadLiteral("(", 0)
			for cond1403 {
				_t2231 := p.parse_export_csv_column()
				item1404 := _t2231
				xs1402 = append(xs1402, item1404)
				cond1403 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1405 := xs1402
			p.consumeLiteral(")")
			_t2232 := &pb.ExportCSVColumns{Columns: export_csv_columns1405}
			_t2233 := &pb.ExportCSVSource{}
			_t2233.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2232}
			_t2230 = _t2233
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2227 = _t2230
	}
	result1408 := _t2227
	p.recordSpan(int(span_start1407), "ExportCSVSource")
	return result1408
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1411 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1409 := p.consumeTerminal("STRING").Value.str
	_t2234 := p.parse_relation_id()
	relation_id1410 := _t2234
	p.consumeLiteral(")")
	_t2235 := &pb.ExportCSVColumn{ColumnName: string1409, ColumnData: relation_id1410}
	result1412 := _t2235
	p.recordSpan(int(span_start1411), "ExportCSVColumn")
	return result1412
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1413 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1413
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1414 := []*pb.ExportCSVColumn{}
	cond1415 := p.matchLookaheadLiteral("(", 0)
	for cond1415 {
		_t2236 := p.parse_export_csv_column()
		item1416 := _t2236
		xs1414 = append(xs1414, item1416)
		cond1415 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1417 := xs1414
	p.consumeLiteral(")")
	return export_csv_columns1417
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1423 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2237 := p.parse_iceberg_locator()
	iceberg_locator1418 := _t2237
	_t2238 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1419 := _t2238
	_t2239 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1420 := _t2239
	_t2240 := p.parse_iceberg_table_properties()
	iceberg_table_properties1421 := _t2240
	var _t2241 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2242 := p.parse_config_dict()
		_t2241 = _t2242
	}
	config_dict1422 := _t2241
	p.consumeLiteral(")")
	_t2243 := p.construct_export_iceberg_config_full(iceberg_locator1418, iceberg_catalog_config1419, export_iceberg_table_def1420, iceberg_table_properties1421, config_dict1422)
	result1424 := _t2243
	p.recordSpan(int(span_start1423), "ExportIcebergConfig")
	return result1424
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1426 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2244 := p.parse_relation_id()
	relation_id1425 := _t2244
	p.consumeLiteral(")")
	result1427 := relation_id1425
	p.recordSpan(int(span_start1426), "RelationId")
	return result1427
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1428 := [][]interface{}{}
	cond1429 := p.matchLookaheadLiteral("(", 0)
	for cond1429 {
		_t2245 := p.parse_iceberg_property_entry()
		item1430 := _t2245
		xs1428 = append(xs1428, item1430)
		cond1429 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1431 := xs1428
	p.consumeLiteral(")")
	return iceberg_property_entrys1431
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
