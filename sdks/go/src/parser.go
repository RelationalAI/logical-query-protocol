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
	var _t2212 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2212
	var _t2213 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2213
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2214 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2214
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2215 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2215
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2216 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2216
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2217 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2217
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2218 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2218
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2219 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2219
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2220 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2220
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2221 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2221
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2222 := &pb.PlainTargets{Targets: targets}
	_t2223 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2223.Body = &pb.TargetRelations_Plain{Plain: _t2222}
	return _t2223
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2224 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2225 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2225.Body = &pb.TargetRelations_Cdc{Cdc: _t2224}
	return _t2225
}

func (p *Parser) construct_relations(keys []*pb.NamedColumn, body *pb.TargetRelations) *pb.TargetRelations {
	var _t2226 interface{}
	if hasProtoField(body, "plain") {
		_t2227 := &pb.TargetRelations{Keys: keys}
		_t2227.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2227
	}
	_ = _t2226
	_t2228 := &pb.TargetRelations{Keys: keys}
	_t2228.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2228
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2229 := columns_opt
	if columns_opt == nil {
		_t2229 = []*pb.GNFColumn{}
	}
	_t2230 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2229, Asof: asof, Relations: relations_opt}
	return _t2230
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2231 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2231
	_t2232 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2232
	_t2233 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2233
	_t2234 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2234
	_t2235 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2235
	_t2236 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2236
	_t2237 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2237
	_t2238 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2238
	_t2239 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2239
	_t2240 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2240
	_t2241 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2241
	_t2242 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2242
	_t2243 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2243
	_t2244 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2244
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2245 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2245
	config := dictFromList(storage_integration_opt)
	_t2246 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2247 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2248 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2249 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2250 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2251 := &pb.StorageIntegration{Provider: _t2246, AzureSasToken: _t2247, S3Region: _t2248, S3AccessKeyId: _t2249, S3SecretAccessKey: _t2250}
	return _t2251
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2252 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2252
	_t2253 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2253
	_t2254 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2254
	_t2255 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2255
	_t2256 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2256
	_t2257 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2257
	_t2258 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2258
	_t2259 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2259
	_t2260 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2260
	_t2261 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2261.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2261.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2261
	_t2262 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2262
}

func (p *Parser) default_configure() *pb.Configure {
	_t2263 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2263
	_t2264 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2264
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
	_t2265 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2265
	_t2266 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2266
	_t2267 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2267
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2268 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2268
	_t2269 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2269
	_t2270 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2270
	_t2271 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2271
	_t2272 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2272
	_t2273 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2273
	_t2274 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2274
	_t2275 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2275
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2276 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2276
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2277 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2277
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2278 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2278
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2279 := config_dict
	if config_dict == nil {
		_t2279 = [][]interface{}{}
	}
	cfg := dictFromList(_t2279)
	_t2280 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2280
	_t2281 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2281
	_t2282 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2282
	table_props := stringMapFromPairs(table_property_pairs)
	_t2283 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2283
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1414 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1415 := p.parse_configure()
		_t1414 = _t1415
	}
	configure707 := _t1414
	var _t1416 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1417 := p.parse_sync()
		_t1416 = _t1417
	}
	sync708 := _t1416
	xs709 := []*pb.Epoch{}
	cond710 := p.matchLookaheadLiteral("(", 0)
	for cond710 {
		_t1418 := p.parse_epoch()
		item711 := _t1418
		xs709 = append(xs709, item711)
		cond710 = p.matchLookaheadLiteral("(", 0)
	}
	epochs712 := xs709
	p.consumeLiteral(")")
	_t1419 := p.default_configure()
	_t1420 := configure707
	if configure707 == nil {
		_t1420 = _t1419
	}
	_t1421 := &pb.Transaction{Epochs: epochs712, Configure: _t1420, Sync: sync708}
	result714 := _t1421
	p.recordSpan(int(span_start713), "Transaction")
	return result714
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start716 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1422 := p.parse_config_dict()
	config_dict715 := _t1422
	p.consumeLiteral(")")
	_t1423 := p.construct_configure(config_dict715)
	result717 := _t1423
	p.recordSpan(int(span_start716), "Configure")
	return result717
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs718 := [][]interface{}{}
	cond719 := p.matchLookaheadLiteral(":", 0)
	for cond719 {
		_t1424 := p.parse_config_key_value()
		item720 := _t1424
		xs718 = append(xs718, item720)
		cond719 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values721 := xs718
	p.consumeLiteral("}")
	return config_key_values721
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol722 := p.consumeTerminal("SYMBOL").Value.str
	_t1425 := p.parse_raw_value()
	raw_value723 := _t1425
	return []interface{}{symbol722, raw_value723}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start737 := int64(p.spanStart())
	var _t1426 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1426 = 12
	} else {
		var _t1427 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1427 = 11
		} else {
			var _t1428 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1428 = 12
			} else {
				var _t1429 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1430 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1430 = 1
					} else {
						var _t1431 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1431 = 0
						} else {
							_t1431 = -1
						}
						_t1430 = _t1431
					}
					_t1429 = _t1430
				} else {
					var _t1432 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1432 = 7
					} else {
						var _t1433 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1433 = 8
						} else {
							var _t1434 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1434 = 2
							} else {
								var _t1435 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1435 = 3
								} else {
									var _t1436 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1436 = 9
									} else {
										var _t1437 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1437 = 4
										} else {
											var _t1438 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1438 = 5
											} else {
												var _t1439 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1439 = 6
												} else {
													var _t1440 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1440 = 10
													} else {
														_t1440 = -1
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
					_t1429 = _t1432
				}
				_t1428 = _t1429
			}
			_t1427 = _t1428
		}
		_t1426 = _t1427
	}
	prediction724 := _t1426
	var _t1441 *pb.Value
	if prediction724 == 12 {
		_t1442 := p.parse_boolean_value()
		boolean_value736 := _t1442
		_t1443 := &pb.Value{}
		_t1443.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value736}
		_t1441 = _t1443
	} else {
		var _t1444 *pb.Value
		if prediction724 == 11 {
			p.consumeLiteral("missing")
			_t1445 := &pb.MissingValue{}
			_t1446 := &pb.Value{}
			_t1446.Value = &pb.Value_MissingValue{MissingValue: _t1445}
			_t1444 = _t1446
		} else {
			var _t1447 *pb.Value
			if prediction724 == 10 {
				decimal735 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1448 := &pb.Value{}
				_t1448.Value = &pb.Value_DecimalValue{DecimalValue: decimal735}
				_t1447 = _t1448
			} else {
				var _t1449 *pb.Value
				if prediction724 == 9 {
					int128734 := p.consumeTerminal("INT128").Value.int128
					_t1450 := &pb.Value{}
					_t1450.Value = &pb.Value_Int128Value{Int128Value: int128734}
					_t1449 = _t1450
				} else {
					var _t1451 *pb.Value
					if prediction724 == 8 {
						uint128733 := p.consumeTerminal("UINT128").Value.uint128
						_t1452 := &pb.Value{}
						_t1452.Value = &pb.Value_Uint128Value{Uint128Value: uint128733}
						_t1451 = _t1452
					} else {
						var _t1453 *pb.Value
						if prediction724 == 7 {
							uint32732 := p.consumeTerminal("UINT32").Value.u32
							_t1454 := &pb.Value{}
							_t1454.Value = &pb.Value_Uint32Value{Uint32Value: uint32732}
							_t1453 = _t1454
						} else {
							var _t1455 *pb.Value
							if prediction724 == 6 {
								float731 := p.consumeTerminal("FLOAT").Value.f64
								_t1456 := &pb.Value{}
								_t1456.Value = &pb.Value_FloatValue{FloatValue: float731}
								_t1455 = _t1456
							} else {
								var _t1457 *pb.Value
								if prediction724 == 5 {
									float32730 := p.consumeTerminal("FLOAT32").Value.f32
									_t1458 := &pb.Value{}
									_t1458.Value = &pb.Value_Float32Value{Float32Value: float32730}
									_t1457 = _t1458
								} else {
									var _t1459 *pb.Value
									if prediction724 == 4 {
										int729 := p.consumeTerminal("INT").Value.i64
										_t1460 := &pb.Value{}
										_t1460.Value = &pb.Value_IntValue{IntValue: int729}
										_t1459 = _t1460
									} else {
										var _t1461 *pb.Value
										if prediction724 == 3 {
											int32728 := p.consumeTerminal("INT32").Value.i32
											_t1462 := &pb.Value{}
											_t1462.Value = &pb.Value_Int32Value{Int32Value: int32728}
											_t1461 = _t1462
										} else {
											var _t1463 *pb.Value
											if prediction724 == 2 {
												string727 := p.consumeTerminal("STRING").Value.str
												_t1464 := &pb.Value{}
												_t1464.Value = &pb.Value_StringValue{StringValue: string727}
												_t1463 = _t1464
											} else {
												var _t1465 *pb.Value
												if prediction724 == 1 {
													_t1466 := p.parse_raw_datetime()
													raw_datetime726 := _t1466
													_t1467 := &pb.Value{}
													_t1467.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime726}
													_t1465 = _t1467
												} else {
													var _t1468 *pb.Value
													if prediction724 == 0 {
														_t1469 := p.parse_raw_date()
														raw_date725 := _t1469
														_t1470 := &pb.Value{}
														_t1470.Value = &pb.Value_DateValue{DateValue: raw_date725}
														_t1468 = _t1470
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1465 = _t1468
												}
												_t1463 = _t1465
											}
											_t1461 = _t1463
										}
										_t1459 = _t1461
									}
									_t1457 = _t1459
								}
								_t1455 = _t1457
							}
							_t1453 = _t1455
						}
						_t1451 = _t1453
					}
					_t1449 = _t1451
				}
				_t1447 = _t1449
			}
			_t1444 = _t1447
		}
		_t1441 = _t1444
	}
	result738 := _t1441
	p.recordSpan(int(span_start737), "Value")
	return result738
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start742 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int739 := p.consumeTerminal("INT").Value.i64
	int_3740 := p.consumeTerminal("INT").Value.i64
	int_4741 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1471 := &pb.DateValue{Year: int32(int739), Month: int32(int_3740), Day: int32(int_4741)}
	result743 := _t1471
	p.recordSpan(int(span_start742), "DateValue")
	return result743
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int744 := p.consumeTerminal("INT").Value.i64
	int_3745 := p.consumeTerminal("INT").Value.i64
	int_4746 := p.consumeTerminal("INT").Value.i64
	int_5747 := p.consumeTerminal("INT").Value.i64
	int_6748 := p.consumeTerminal("INT").Value.i64
	int_7749 := p.consumeTerminal("INT").Value.i64
	var _t1472 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1472 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8750 := _t1472
	p.consumeLiteral(")")
	_t1473 := &pb.DateTimeValue{Year: int32(int744), Month: int32(int_3745), Day: int32(int_4746), Hour: int32(int_5747), Minute: int32(int_6748), Second: int32(int_7749), Microsecond: int32(deref(int_8750, 0))}
	result752 := _t1473
	p.recordSpan(int(span_start751), "DateTimeValue")
	return result752
}

func (p *Parser) parse_boolean_value() bool {
	var _t1474 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1474 = 0
	} else {
		var _t1475 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1475 = 1
		} else {
			_t1475 = -1
		}
		_t1474 = _t1475
	}
	prediction753 := _t1474
	var _t1476 bool
	if prediction753 == 1 {
		p.consumeLiteral("false")
		_t1476 = false
	} else {
		var _t1477 bool
		if prediction753 == 0 {
			p.consumeLiteral("true")
			_t1477 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1476 = _t1477
	}
	return _t1476
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start758 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs754 := []*pb.FragmentId{}
	cond755 := p.matchLookaheadLiteral(":", 0)
	for cond755 {
		_t1478 := p.parse_fragment_id()
		item756 := _t1478
		xs754 = append(xs754, item756)
		cond755 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids757 := xs754
	p.consumeLiteral(")")
	_t1479 := &pb.Sync{Fragments: fragment_ids757}
	result759 := _t1479
	p.recordSpan(int(span_start758), "Sync")
	return result759
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol760 := p.consumeTerminal("SYMBOL").Value.str
	result762 := &pb.FragmentId{Id: []byte(symbol760)}
	p.recordSpan(int(span_start761), "FragmentId")
	return result762
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start765 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1480 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1481 := p.parse_epoch_writes()
		_t1480 = _t1481
	}
	epoch_writes763 := _t1480
	var _t1482 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1483 := p.parse_epoch_reads()
		_t1482 = _t1483
	}
	epoch_reads764 := _t1482
	p.consumeLiteral(")")
	_t1484 := epoch_writes763
	if epoch_writes763 == nil {
		_t1484 = []*pb.Write{}
	}
	_t1485 := epoch_reads764
	if epoch_reads764 == nil {
		_t1485 = []*pb.Read{}
	}
	_t1486 := &pb.Epoch{Writes: _t1484, Reads: _t1485}
	result766 := _t1486
	p.recordSpan(int(span_start765), "Epoch")
	return result766
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs767 := []*pb.Write{}
	cond768 := p.matchLookaheadLiteral("(", 0)
	for cond768 {
		_t1487 := p.parse_write()
		item769 := _t1487
		xs767 = append(xs767, item769)
		cond768 = p.matchLookaheadLiteral("(", 0)
	}
	writes770 := xs767
	p.consumeLiteral(")")
	return writes770
}

func (p *Parser) parse_write() *pb.Write {
	span_start776 := int64(p.spanStart())
	var _t1488 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1489 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1489 = 1
		} else {
			var _t1490 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1490 = 3
			} else {
				var _t1491 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1491 = 0
				} else {
					var _t1492 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1492 = 2
					} else {
						_t1492 = -1
					}
					_t1491 = _t1492
				}
				_t1490 = _t1491
			}
			_t1489 = _t1490
		}
		_t1488 = _t1489
	} else {
		_t1488 = -1
	}
	prediction771 := _t1488
	var _t1493 *pb.Write
	if prediction771 == 3 {
		_t1494 := p.parse_snapshot()
		snapshot775 := _t1494
		_t1495 := &pb.Write{}
		_t1495.WriteType = &pb.Write_Snapshot{Snapshot: snapshot775}
		_t1493 = _t1495
	} else {
		var _t1496 *pb.Write
		if prediction771 == 2 {
			_t1497 := p.parse_context()
			context774 := _t1497
			_t1498 := &pb.Write{}
			_t1498.WriteType = &pb.Write_Context{Context: context774}
			_t1496 = _t1498
		} else {
			var _t1499 *pb.Write
			if prediction771 == 1 {
				_t1500 := p.parse_undefine()
				undefine773 := _t1500
				_t1501 := &pb.Write{}
				_t1501.WriteType = &pb.Write_Undefine{Undefine: undefine773}
				_t1499 = _t1501
			} else {
				var _t1502 *pb.Write
				if prediction771 == 0 {
					_t1503 := p.parse_define()
					define772 := _t1503
					_t1504 := &pb.Write{}
					_t1504.WriteType = &pb.Write_Define{Define: define772}
					_t1502 = _t1504
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1499 = _t1502
			}
			_t1496 = _t1499
		}
		_t1493 = _t1496
	}
	result777 := _t1493
	p.recordSpan(int(span_start776), "Write")
	return result777
}

func (p *Parser) parse_define() *pb.Define {
	span_start779 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1505 := p.parse_fragment()
	fragment778 := _t1505
	p.consumeLiteral(")")
	_t1506 := &pb.Define{Fragment: fragment778}
	result780 := _t1506
	p.recordSpan(int(span_start779), "Define")
	return result780
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start786 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1507 := p.parse_new_fragment_id()
	new_fragment_id781 := _t1507
	xs782 := []*pb.Declaration{}
	cond783 := p.matchLookaheadLiteral("(", 0)
	for cond783 {
		_t1508 := p.parse_declaration()
		item784 := _t1508
		xs782 = append(xs782, item784)
		cond783 = p.matchLookaheadLiteral("(", 0)
	}
	declarations785 := xs782
	p.consumeLiteral(")")
	result787 := p.constructFragment(new_fragment_id781, declarations785)
	p.recordSpan(int(span_start786), "Fragment")
	return result787
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start789 := int64(p.spanStart())
	_t1509 := p.parse_fragment_id()
	fragment_id788 := _t1509
	p.startFragment(fragment_id788)
	result790 := fragment_id788
	p.recordSpan(int(span_start789), "FragmentId")
	return result790
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start796 := int64(p.spanStart())
	var _t1510 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1511 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1511 = 3
		} else {
			var _t1512 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1512 = 2
			} else {
				var _t1513 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1513 = 3
				} else {
					var _t1514 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1514 = 0
					} else {
						var _t1515 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1515 = 3
						} else {
							var _t1516 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1516 = 3
							} else {
								var _t1517 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
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
	} else {
		_t1510 = -1
	}
	prediction791 := _t1510
	var _t1518 *pb.Declaration
	if prediction791 == 3 {
		_t1519 := p.parse_data()
		data795 := _t1519
		_t1520 := &pb.Declaration{}
		_t1520.DeclarationType = &pb.Declaration_Data{Data: data795}
		_t1518 = _t1520
	} else {
		var _t1521 *pb.Declaration
		if prediction791 == 2 {
			_t1522 := p.parse_constraint()
			constraint794 := _t1522
			_t1523 := &pb.Declaration{}
			_t1523.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint794}
			_t1521 = _t1523
		} else {
			var _t1524 *pb.Declaration
			if prediction791 == 1 {
				_t1525 := p.parse_algorithm()
				algorithm793 := _t1525
				_t1526 := &pb.Declaration{}
				_t1526.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm793}
				_t1524 = _t1526
			} else {
				var _t1527 *pb.Declaration
				if prediction791 == 0 {
					_t1528 := p.parse_def()
					def792 := _t1528
					_t1529 := &pb.Declaration{}
					_t1529.DeclarationType = &pb.Declaration_Def{Def: def792}
					_t1527 = _t1529
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1524 = _t1527
			}
			_t1521 = _t1524
		}
		_t1518 = _t1521
	}
	result797 := _t1518
	p.recordSpan(int(span_start796), "Declaration")
	return result797
}

func (p *Parser) parse_def() *pb.Def {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1530 := p.parse_relation_id()
	relation_id798 := _t1530
	_t1531 := p.parse_abstraction()
	abstraction799 := _t1531
	var _t1532 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1533 := p.parse_attrs()
		_t1532 = _t1533
	}
	attrs800 := _t1532
	p.consumeLiteral(")")
	_t1534 := attrs800
	if attrs800 == nil {
		_t1534 = []*pb.Attribute{}
	}
	_t1535 := &pb.Def{Name: relation_id798, Body: abstraction799, Attrs: _t1534}
	result802 := _t1535
	p.recordSpan(int(span_start801), "Def")
	return result802
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start806 := int64(p.spanStart())
	var _t1536 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1536 = 0
	} else {
		var _t1537 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1537 = 1
		} else {
			_t1537 = -1
		}
		_t1536 = _t1537
	}
	prediction803 := _t1536
	var _t1538 *pb.RelationId
	if prediction803 == 1 {
		uint128805 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128805
		_t1538 = &pb.RelationId{IdLow: uint128805.Low, IdHigh: uint128805.High}
	} else {
		var _t1539 *pb.RelationId
		if prediction803 == 0 {
			p.consumeLiteral(":")
			symbol804 := p.consumeTerminal("SYMBOL").Value.str
			_t1539 = p.relationIdFromString(symbol804)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1538 = _t1539
	}
	result807 := _t1538
	p.recordSpan(int(span_start806), "RelationId")
	return result807
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1540 := p.parse_bindings()
	bindings808 := _t1540
	_t1541 := p.parse_formula()
	formula809 := _t1541
	p.consumeLiteral(")")
	_t1542 := &pb.Abstraction{Vars: listConcat(bindings808[0].([]*pb.Binding), bindings808[1].([]*pb.Binding)), Value: formula809}
	result811 := _t1542
	p.recordSpan(int(span_start810), "Abstraction")
	return result811
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs812 := []*pb.Binding{}
	cond813 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond813 {
		_t1543 := p.parse_binding()
		item814 := _t1543
		xs812 = append(xs812, item814)
		cond813 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings815 := xs812
	var _t1544 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1545 := p.parse_value_bindings()
		_t1544 = _t1545
	}
	value_bindings816 := _t1544
	p.consumeLiteral("]")
	_t1546 := value_bindings816
	if value_bindings816 == nil {
		_t1546 = []*pb.Binding{}
	}
	return []interface{}{bindings815, _t1546}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start819 := int64(p.spanStart())
	symbol817 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1547 := p.parse_type()
	type818 := _t1547
	_t1548 := &pb.Var{Name: symbol817}
	_t1549 := &pb.Binding{Var: _t1548, Type: type818}
	result820 := _t1549
	p.recordSpan(int(span_start819), "Binding")
	return result820
}

func (p *Parser) parse_type() *pb.Type {
	span_start836 := int64(p.spanStart())
	var _t1550 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1550 = 0
	} else {
		var _t1551 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1551 = 13
		} else {
			var _t1552 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1552 = 4
			} else {
				var _t1553 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1553 = 1
				} else {
					var _t1554 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1554 = 8
					} else {
						var _t1555 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1555 = 11
						} else {
							var _t1556 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1556 = 5
							} else {
								var _t1557 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1557 = 2
								} else {
									var _t1558 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1558 = 12
									} else {
										var _t1559 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1559 = 3
										} else {
											var _t1560 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1560 = 7
											} else {
												var _t1561 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1561 = 6
												} else {
													var _t1562 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1562 = 10
													} else {
														var _t1563 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1563 = 9
														} else {
															_t1563 = -1
														}
														_t1562 = _t1563
													}
													_t1561 = _t1562
												}
												_t1560 = _t1561
											}
											_t1559 = _t1560
										}
										_t1558 = _t1559
									}
									_t1557 = _t1558
								}
								_t1556 = _t1557
							}
							_t1555 = _t1556
						}
						_t1554 = _t1555
					}
					_t1553 = _t1554
				}
				_t1552 = _t1553
			}
			_t1551 = _t1552
		}
		_t1550 = _t1551
	}
	prediction821 := _t1550
	var _t1564 *pb.Type
	if prediction821 == 13 {
		_t1565 := p.parse_uint32_type()
		uint32_type835 := _t1565
		_t1566 := &pb.Type{}
		_t1566.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type835}
		_t1564 = _t1566
	} else {
		var _t1567 *pb.Type
		if prediction821 == 12 {
			_t1568 := p.parse_float32_type()
			float32_type834 := _t1568
			_t1569 := &pb.Type{}
			_t1569.Type = &pb.Type_Float32Type{Float32Type: float32_type834}
			_t1567 = _t1569
		} else {
			var _t1570 *pb.Type
			if prediction821 == 11 {
				_t1571 := p.parse_int32_type()
				int32_type833 := _t1571
				_t1572 := &pb.Type{}
				_t1572.Type = &pb.Type_Int32Type{Int32Type: int32_type833}
				_t1570 = _t1572
			} else {
				var _t1573 *pb.Type
				if prediction821 == 10 {
					_t1574 := p.parse_boolean_type()
					boolean_type832 := _t1574
					_t1575 := &pb.Type{}
					_t1575.Type = &pb.Type_BooleanType{BooleanType: boolean_type832}
					_t1573 = _t1575
				} else {
					var _t1576 *pb.Type
					if prediction821 == 9 {
						_t1577 := p.parse_decimal_type()
						decimal_type831 := _t1577
						_t1578 := &pb.Type{}
						_t1578.Type = &pb.Type_DecimalType{DecimalType: decimal_type831}
						_t1576 = _t1578
					} else {
						var _t1579 *pb.Type
						if prediction821 == 8 {
							_t1580 := p.parse_missing_type()
							missing_type830 := _t1580
							_t1581 := &pb.Type{}
							_t1581.Type = &pb.Type_MissingType{MissingType: missing_type830}
							_t1579 = _t1581
						} else {
							var _t1582 *pb.Type
							if prediction821 == 7 {
								_t1583 := p.parse_datetime_type()
								datetime_type829 := _t1583
								_t1584 := &pb.Type{}
								_t1584.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type829}
								_t1582 = _t1584
							} else {
								var _t1585 *pb.Type
								if prediction821 == 6 {
									_t1586 := p.parse_date_type()
									date_type828 := _t1586
									_t1587 := &pb.Type{}
									_t1587.Type = &pb.Type_DateType{DateType: date_type828}
									_t1585 = _t1587
								} else {
									var _t1588 *pb.Type
									if prediction821 == 5 {
										_t1589 := p.parse_int128_type()
										int128_type827 := _t1589
										_t1590 := &pb.Type{}
										_t1590.Type = &pb.Type_Int128Type{Int128Type: int128_type827}
										_t1588 = _t1590
									} else {
										var _t1591 *pb.Type
										if prediction821 == 4 {
											_t1592 := p.parse_uint128_type()
											uint128_type826 := _t1592
											_t1593 := &pb.Type{}
											_t1593.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type826}
											_t1591 = _t1593
										} else {
											var _t1594 *pb.Type
											if prediction821 == 3 {
												_t1595 := p.parse_float_type()
												float_type825 := _t1595
												_t1596 := &pb.Type{}
												_t1596.Type = &pb.Type_FloatType{FloatType: float_type825}
												_t1594 = _t1596
											} else {
												var _t1597 *pb.Type
												if prediction821 == 2 {
													_t1598 := p.parse_int_type()
													int_type824 := _t1598
													_t1599 := &pb.Type{}
													_t1599.Type = &pb.Type_IntType{IntType: int_type824}
													_t1597 = _t1599
												} else {
													var _t1600 *pb.Type
													if prediction821 == 1 {
														_t1601 := p.parse_string_type()
														string_type823 := _t1601
														_t1602 := &pb.Type{}
														_t1602.Type = &pb.Type_StringType{StringType: string_type823}
														_t1600 = _t1602
													} else {
														var _t1603 *pb.Type
														if prediction821 == 0 {
															_t1604 := p.parse_unspecified_type()
															unspecified_type822 := _t1604
															_t1605 := &pb.Type{}
															_t1605.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type822}
															_t1603 = _t1605
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1600 = _t1603
													}
													_t1597 = _t1600
												}
												_t1594 = _t1597
											}
											_t1591 = _t1594
										}
										_t1588 = _t1591
									}
									_t1585 = _t1588
								}
								_t1582 = _t1585
							}
							_t1579 = _t1582
						}
						_t1576 = _t1579
					}
					_t1573 = _t1576
				}
				_t1570 = _t1573
			}
			_t1567 = _t1570
		}
		_t1564 = _t1567
	}
	result837 := _t1564
	p.recordSpan(int(span_start836), "Type")
	return result837
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start838 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1606 := &pb.UnspecifiedType{}
	result839 := _t1606
	p.recordSpan(int(span_start838), "UnspecifiedType")
	return result839
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start840 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1607 := &pb.StringType{}
	result841 := _t1607
	p.recordSpan(int(span_start840), "StringType")
	return result841
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1608 := &pb.IntType{}
	result843 := _t1608
	p.recordSpan(int(span_start842), "IntType")
	return result843
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start844 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1609 := &pb.FloatType{}
	result845 := _t1609
	p.recordSpan(int(span_start844), "FloatType")
	return result845
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start846 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1610 := &pb.UInt128Type{}
	result847 := _t1610
	p.recordSpan(int(span_start846), "UInt128Type")
	return result847
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1611 := &pb.Int128Type{}
	result849 := _t1611
	p.recordSpan(int(span_start848), "Int128Type")
	return result849
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start850 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1612 := &pb.DateType{}
	result851 := _t1612
	p.recordSpan(int(span_start850), "DateType")
	return result851
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1613 := &pb.DateTimeType{}
	result853 := _t1613
	p.recordSpan(int(span_start852), "DateTimeType")
	return result853
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1614 := &pb.MissingType{}
	result855 := _t1614
	p.recordSpan(int(span_start854), "MissingType")
	return result855
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int856 := p.consumeTerminal("INT").Value.i64
	int_3857 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1615 := &pb.DecimalType{Precision: int32(int856), Scale: int32(int_3857)}
	result859 := _t1615
	p.recordSpan(int(span_start858), "DecimalType")
	return result859
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1616 := &pb.BooleanType{}
	result861 := _t1616
	p.recordSpan(int(span_start860), "BooleanType")
	return result861
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start862 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1617 := &pb.Int32Type{}
	result863 := _t1617
	p.recordSpan(int(span_start862), "Int32Type")
	return result863
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1618 := &pb.Float32Type{}
	result865 := _t1618
	p.recordSpan(int(span_start864), "Float32Type")
	return result865
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1619 := &pb.UInt32Type{}
	result867 := _t1619
	p.recordSpan(int(span_start866), "UInt32Type")
	return result867
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs868 := []*pb.Binding{}
	cond869 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond869 {
		_t1620 := p.parse_binding()
		item870 := _t1620
		xs868 = append(xs868, item870)
		cond869 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings871 := xs868
	return bindings871
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start886 := int64(p.spanStart())
	var _t1621 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1622 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1622 = 0
		} else {
			var _t1623 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1623 = 11
			} else {
				var _t1624 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1624 = 3
				} else {
					var _t1625 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1625 = 10
					} else {
						var _t1626 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1626 = 9
						} else {
							var _t1627 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1627 = 5
							} else {
								var _t1628 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1628 = 6
								} else {
									var _t1629 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1629 = 7
									} else {
										var _t1630 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1630 = 1
										} else {
											var _t1631 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1631 = 2
											} else {
												var _t1632 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1632 = 12
												} else {
													var _t1633 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1633 = 8
													} else {
														var _t1634 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1634 = 4
														} else {
															var _t1635 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1635 = 10
															} else {
																var _t1636 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1636 = 10
																} else {
																	var _t1637 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1637 = 10
																	} else {
																		var _t1638 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1638 = 10
																		} else {
																			var _t1639 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1639 = 10
																			} else {
																				var _t1640 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1640 = 10
																				} else {
																					var _t1641 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1641 = 10
																					} else {
																						var _t1642 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1642 = 10
																						} else {
																							var _t1643 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1643 = 10
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
									_t1628 = _t1629
								}
								_t1627 = _t1628
							}
							_t1626 = _t1627
						}
						_t1625 = _t1626
					}
					_t1624 = _t1625
				}
				_t1623 = _t1624
			}
			_t1622 = _t1623
		}
		_t1621 = _t1622
	} else {
		_t1621 = -1
	}
	prediction872 := _t1621
	var _t1644 *pb.Formula
	if prediction872 == 12 {
		_t1645 := p.parse_cast()
		cast885 := _t1645
		_t1646 := &pb.Formula{}
		_t1646.FormulaType = &pb.Formula_Cast{Cast: cast885}
		_t1644 = _t1646
	} else {
		var _t1647 *pb.Formula
		if prediction872 == 11 {
			_t1648 := p.parse_rel_atom()
			rel_atom884 := _t1648
			_t1649 := &pb.Formula{}
			_t1649.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom884}
			_t1647 = _t1649
		} else {
			var _t1650 *pb.Formula
			if prediction872 == 10 {
				_t1651 := p.parse_primitive()
				primitive883 := _t1651
				_t1652 := &pb.Formula{}
				_t1652.FormulaType = &pb.Formula_Primitive{Primitive: primitive883}
				_t1650 = _t1652
			} else {
				var _t1653 *pb.Formula
				if prediction872 == 9 {
					_t1654 := p.parse_pragma()
					pragma882 := _t1654
					_t1655 := &pb.Formula{}
					_t1655.FormulaType = &pb.Formula_Pragma{Pragma: pragma882}
					_t1653 = _t1655
				} else {
					var _t1656 *pb.Formula
					if prediction872 == 8 {
						_t1657 := p.parse_atom()
						atom881 := _t1657
						_t1658 := &pb.Formula{}
						_t1658.FormulaType = &pb.Formula_Atom{Atom: atom881}
						_t1656 = _t1658
					} else {
						var _t1659 *pb.Formula
						if prediction872 == 7 {
							_t1660 := p.parse_ffi()
							ffi880 := _t1660
							_t1661 := &pb.Formula{}
							_t1661.FormulaType = &pb.Formula_Ffi{Ffi: ffi880}
							_t1659 = _t1661
						} else {
							var _t1662 *pb.Formula
							if prediction872 == 6 {
								_t1663 := p.parse_not()
								not879 := _t1663
								_t1664 := &pb.Formula{}
								_t1664.FormulaType = &pb.Formula_Not{Not: not879}
								_t1662 = _t1664
							} else {
								var _t1665 *pb.Formula
								if prediction872 == 5 {
									_t1666 := p.parse_disjunction()
									disjunction878 := _t1666
									_t1667 := &pb.Formula{}
									_t1667.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction878}
									_t1665 = _t1667
								} else {
									var _t1668 *pb.Formula
									if prediction872 == 4 {
										_t1669 := p.parse_conjunction()
										conjunction877 := _t1669
										_t1670 := &pb.Formula{}
										_t1670.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction877}
										_t1668 = _t1670
									} else {
										var _t1671 *pb.Formula
										if prediction872 == 3 {
											_t1672 := p.parse_reduce()
											reduce876 := _t1672
											_t1673 := &pb.Formula{}
											_t1673.FormulaType = &pb.Formula_Reduce{Reduce: reduce876}
											_t1671 = _t1673
										} else {
											var _t1674 *pb.Formula
											if prediction872 == 2 {
												_t1675 := p.parse_exists()
												exists875 := _t1675
												_t1676 := &pb.Formula{}
												_t1676.FormulaType = &pb.Formula_Exists{Exists: exists875}
												_t1674 = _t1676
											} else {
												var _t1677 *pb.Formula
												if prediction872 == 1 {
													_t1678 := p.parse_false()
													false874 := _t1678
													_t1679 := &pb.Formula{}
													_t1679.FormulaType = &pb.Formula_Disjunction{Disjunction: false874}
													_t1677 = _t1679
												} else {
													var _t1680 *pb.Formula
													if prediction872 == 0 {
														_t1681 := p.parse_true()
														true873 := _t1681
														_t1682 := &pb.Formula{}
														_t1682.FormulaType = &pb.Formula_Conjunction{Conjunction: true873}
														_t1680 = _t1682
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1677 = _t1680
												}
												_t1674 = _t1677
											}
											_t1671 = _t1674
										}
										_t1668 = _t1671
									}
									_t1665 = _t1668
								}
								_t1662 = _t1665
							}
							_t1659 = _t1662
						}
						_t1656 = _t1659
					}
					_t1653 = _t1656
				}
				_t1650 = _t1653
			}
			_t1647 = _t1650
		}
		_t1644 = _t1647
	}
	result887 := _t1644
	p.recordSpan(int(span_start886), "Formula")
	return result887
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start888 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1683 := &pb.Conjunction{Args: []*pb.Formula{}}
	result889 := _t1683
	p.recordSpan(int(span_start888), "Conjunction")
	return result889
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start890 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1684 := &pb.Disjunction{Args: []*pb.Formula{}}
	result891 := _t1684
	p.recordSpan(int(span_start890), "Disjunction")
	return result891
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start894 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1685 := p.parse_bindings()
	bindings892 := _t1685
	_t1686 := p.parse_formula()
	formula893 := _t1686
	p.consumeLiteral(")")
	_t1687 := &pb.Abstraction{Vars: listConcat(bindings892[0].([]*pb.Binding), bindings892[1].([]*pb.Binding)), Value: formula893}
	_t1688 := &pb.Exists{Body: _t1687}
	result895 := _t1688
	p.recordSpan(int(span_start894), "Exists")
	return result895
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1689 := p.parse_abstraction()
	abstraction896 := _t1689
	_t1690 := p.parse_abstraction()
	abstraction_3897 := _t1690
	_t1691 := p.parse_terms()
	terms898 := _t1691
	p.consumeLiteral(")")
	_t1692 := &pb.Reduce{Op: abstraction896, Body: abstraction_3897, Terms: terms898}
	result900 := _t1692
	p.recordSpan(int(span_start899), "Reduce")
	return result900
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs901 := []*pb.Term{}
	cond902 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond902 {
		_t1693 := p.parse_term()
		item903 := _t1693
		xs901 = append(xs901, item903)
		cond902 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms904 := xs901
	p.consumeLiteral(")")
	return terms904
}

func (p *Parser) parse_term() *pb.Term {
	span_start908 := int64(p.spanStart())
	var _t1694 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1694 = 1
	} else {
		var _t1695 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1695 = 1
		} else {
			var _t1696 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1696 = 1
			} else {
				var _t1697 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1697 = 1
				} else {
					var _t1698 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1698 = 0
					} else {
						var _t1699 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1699 = 1
						} else {
							var _t1700 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1700 = 1
							} else {
								var _t1701 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1701 = 1
								} else {
									var _t1702 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1702 = 1
									} else {
										var _t1703 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1703 = 1
										} else {
											var _t1704 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1704 = 1
											} else {
												var _t1705 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1705 = 1
												} else {
													var _t1706 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1706 = 1
													} else {
														var _t1707 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1707 = 1
														} else {
															_t1707 = -1
														}
														_t1706 = _t1707
													}
													_t1705 = _t1706
												}
												_t1704 = _t1705
											}
											_t1703 = _t1704
										}
										_t1702 = _t1703
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
			}
			_t1695 = _t1696
		}
		_t1694 = _t1695
	}
	prediction905 := _t1694
	var _t1708 *pb.Term
	if prediction905 == 1 {
		_t1709 := p.parse_value()
		value907 := _t1709
		_t1710 := &pb.Term{}
		_t1710.TermType = &pb.Term_Constant{Constant: value907}
		_t1708 = _t1710
	} else {
		var _t1711 *pb.Term
		if prediction905 == 0 {
			_t1712 := p.parse_var()
			var906 := _t1712
			_t1713 := &pb.Term{}
			_t1713.TermType = &pb.Term_Var{Var: var906}
			_t1711 = _t1713
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1708 = _t1711
	}
	result909 := _t1708
	p.recordSpan(int(span_start908), "Term")
	return result909
}

func (p *Parser) parse_var() *pb.Var {
	span_start911 := int64(p.spanStart())
	symbol910 := p.consumeTerminal("SYMBOL").Value.str
	_t1714 := &pb.Var{Name: symbol910}
	result912 := _t1714
	p.recordSpan(int(span_start911), "Var")
	return result912
}

func (p *Parser) parse_value() *pb.Value {
	span_start926 := int64(p.spanStart())
	var _t1715 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1715 = 12
	} else {
		var _t1716 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1716 = 11
		} else {
			var _t1717 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1717 = 12
			} else {
				var _t1718 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1719 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1719 = 1
					} else {
						var _t1720 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1720 = 0
						} else {
							_t1720 = -1
						}
						_t1719 = _t1720
					}
					_t1718 = _t1719
				} else {
					var _t1721 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1721 = 7
					} else {
						var _t1722 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1722 = 8
						} else {
							var _t1723 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1723 = 2
							} else {
								var _t1724 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1724 = 3
								} else {
									var _t1725 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1725 = 9
									} else {
										var _t1726 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1726 = 4
										} else {
											var _t1727 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1727 = 5
											} else {
												var _t1728 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1728 = 6
												} else {
													var _t1729 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1729 = 10
													} else {
														_t1729 = -1
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
					_t1718 = _t1721
				}
				_t1717 = _t1718
			}
			_t1716 = _t1717
		}
		_t1715 = _t1716
	}
	prediction913 := _t1715
	var _t1730 *pb.Value
	if prediction913 == 12 {
		_t1731 := p.parse_boolean_value()
		boolean_value925 := _t1731
		_t1732 := &pb.Value{}
		_t1732.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value925}
		_t1730 = _t1732
	} else {
		var _t1733 *pb.Value
		if prediction913 == 11 {
			p.consumeLiteral("missing")
			_t1734 := &pb.MissingValue{}
			_t1735 := &pb.Value{}
			_t1735.Value = &pb.Value_MissingValue{MissingValue: _t1734}
			_t1733 = _t1735
		} else {
			var _t1736 *pb.Value
			if prediction913 == 10 {
				formatted_decimal924 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1737 := &pb.Value{}
				_t1737.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal924}
				_t1736 = _t1737
			} else {
				var _t1738 *pb.Value
				if prediction913 == 9 {
					formatted_int128923 := p.consumeTerminal("INT128").Value.int128
					_t1739 := &pb.Value{}
					_t1739.Value = &pb.Value_Int128Value{Int128Value: formatted_int128923}
					_t1738 = _t1739
				} else {
					var _t1740 *pb.Value
					if prediction913 == 8 {
						formatted_uint128922 := p.consumeTerminal("UINT128").Value.uint128
						_t1741 := &pb.Value{}
						_t1741.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128922}
						_t1740 = _t1741
					} else {
						var _t1742 *pb.Value
						if prediction913 == 7 {
							formatted_uint32921 := p.consumeTerminal("UINT32").Value.u32
							_t1743 := &pb.Value{}
							_t1743.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32921}
							_t1742 = _t1743
						} else {
							var _t1744 *pb.Value
							if prediction913 == 6 {
								formatted_float920 := p.consumeTerminal("FLOAT").Value.f64
								_t1745 := &pb.Value{}
								_t1745.Value = &pb.Value_FloatValue{FloatValue: formatted_float920}
								_t1744 = _t1745
							} else {
								var _t1746 *pb.Value
								if prediction913 == 5 {
									formatted_float32919 := p.consumeTerminal("FLOAT32").Value.f32
									_t1747 := &pb.Value{}
									_t1747.Value = &pb.Value_Float32Value{Float32Value: formatted_float32919}
									_t1746 = _t1747
								} else {
									var _t1748 *pb.Value
									if prediction913 == 4 {
										formatted_int918 := p.consumeTerminal("INT").Value.i64
										_t1749 := &pb.Value{}
										_t1749.Value = &pb.Value_IntValue{IntValue: formatted_int918}
										_t1748 = _t1749
									} else {
										var _t1750 *pb.Value
										if prediction913 == 3 {
											formatted_int32917 := p.consumeTerminal("INT32").Value.i32
											_t1751 := &pb.Value{}
											_t1751.Value = &pb.Value_Int32Value{Int32Value: formatted_int32917}
											_t1750 = _t1751
										} else {
											var _t1752 *pb.Value
											if prediction913 == 2 {
												formatted_string916 := p.consumeTerminal("STRING").Value.str
												_t1753 := &pb.Value{}
												_t1753.Value = &pb.Value_StringValue{StringValue: formatted_string916}
												_t1752 = _t1753
											} else {
												var _t1754 *pb.Value
												if prediction913 == 1 {
													_t1755 := p.parse_datetime()
													datetime915 := _t1755
													_t1756 := &pb.Value{}
													_t1756.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime915}
													_t1754 = _t1756
												} else {
													var _t1757 *pb.Value
													if prediction913 == 0 {
														_t1758 := p.parse_date()
														date914 := _t1758
														_t1759 := &pb.Value{}
														_t1759.Value = &pb.Value_DateValue{DateValue: date914}
														_t1757 = _t1759
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1754 = _t1757
												}
												_t1752 = _t1754
											}
											_t1750 = _t1752
										}
										_t1748 = _t1750
									}
									_t1746 = _t1748
								}
								_t1744 = _t1746
							}
							_t1742 = _t1744
						}
						_t1740 = _t1742
					}
					_t1738 = _t1740
				}
				_t1736 = _t1738
			}
			_t1733 = _t1736
		}
		_t1730 = _t1733
	}
	result927 := _t1730
	p.recordSpan(int(span_start926), "Value")
	return result927
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start931 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int928 := p.consumeTerminal("INT").Value.i64
	formatted_int_3929 := p.consumeTerminal("INT").Value.i64
	formatted_int_4930 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1760 := &pb.DateValue{Year: int32(formatted_int928), Month: int32(formatted_int_3929), Day: int32(formatted_int_4930)}
	result932 := _t1760
	p.recordSpan(int(span_start931), "DateValue")
	return result932
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start940 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int933 := p.consumeTerminal("INT").Value.i64
	formatted_int_3934 := p.consumeTerminal("INT").Value.i64
	formatted_int_4935 := p.consumeTerminal("INT").Value.i64
	formatted_int_5936 := p.consumeTerminal("INT").Value.i64
	formatted_int_6937 := p.consumeTerminal("INT").Value.i64
	formatted_int_7938 := p.consumeTerminal("INT").Value.i64
	var _t1761 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1761 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8939 := _t1761
	p.consumeLiteral(")")
	_t1762 := &pb.DateTimeValue{Year: int32(formatted_int933), Month: int32(formatted_int_3934), Day: int32(formatted_int_4935), Hour: int32(formatted_int_5936), Minute: int32(formatted_int_6937), Second: int32(formatted_int_7938), Microsecond: int32(deref(formatted_int_8939, 0))}
	result941 := _t1762
	p.recordSpan(int(span_start940), "DateTimeValue")
	return result941
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start946 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs942 := []*pb.Formula{}
	cond943 := p.matchLookaheadLiteral("(", 0)
	for cond943 {
		_t1763 := p.parse_formula()
		item944 := _t1763
		xs942 = append(xs942, item944)
		cond943 = p.matchLookaheadLiteral("(", 0)
	}
	formulas945 := xs942
	p.consumeLiteral(")")
	_t1764 := &pb.Conjunction{Args: formulas945}
	result947 := _t1764
	p.recordSpan(int(span_start946), "Conjunction")
	return result947
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs948 := []*pb.Formula{}
	cond949 := p.matchLookaheadLiteral("(", 0)
	for cond949 {
		_t1765 := p.parse_formula()
		item950 := _t1765
		xs948 = append(xs948, item950)
		cond949 = p.matchLookaheadLiteral("(", 0)
	}
	formulas951 := xs948
	p.consumeLiteral(")")
	_t1766 := &pb.Disjunction{Args: formulas951}
	result953 := _t1766
	p.recordSpan(int(span_start952), "Disjunction")
	return result953
}

func (p *Parser) parse_not() *pb.Not {
	span_start955 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1767 := p.parse_formula()
	formula954 := _t1767
	p.consumeLiteral(")")
	_t1768 := &pb.Not{Arg: formula954}
	result956 := _t1768
	p.recordSpan(int(span_start955), "Not")
	return result956
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1769 := p.parse_name()
	name957 := _t1769
	_t1770 := p.parse_ffi_args()
	ffi_args958 := _t1770
	_t1771 := p.parse_terms()
	terms959 := _t1771
	p.consumeLiteral(")")
	_t1772 := &pb.FFI{Name: name957, Args: ffi_args958, Terms: terms959}
	result961 := _t1772
	p.recordSpan(int(span_start960), "FFI")
	return result961
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol962 := p.consumeTerminal("SYMBOL").Value.str
	return symbol962
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs963 := []*pb.Abstraction{}
	cond964 := p.matchLookaheadLiteral("(", 0)
	for cond964 {
		_t1773 := p.parse_abstraction()
		item965 := _t1773
		xs963 = append(xs963, item965)
		cond964 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions966 := xs963
	p.consumeLiteral(")")
	return abstractions966
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1774 := p.parse_relation_id()
	relation_id967 := _t1774
	xs968 := []*pb.Term{}
	cond969 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond969 {
		_t1775 := p.parse_term()
		item970 := _t1775
		xs968 = append(xs968, item970)
		cond969 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms971 := xs968
	p.consumeLiteral(")")
	_t1776 := &pb.Atom{Name: relation_id967, Terms: terms971}
	result973 := _t1776
	p.recordSpan(int(span_start972), "Atom")
	return result973
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1777 := p.parse_name()
	name974 := _t1777
	xs975 := []*pb.Term{}
	cond976 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond976 {
		_t1778 := p.parse_term()
		item977 := _t1778
		xs975 = append(xs975, item977)
		cond976 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms978 := xs975
	p.consumeLiteral(")")
	_t1779 := &pb.Pragma{Name: name974, Terms: terms978}
	result980 := _t1779
	p.recordSpan(int(span_start979), "Pragma")
	return result980
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start996 := int64(p.spanStart())
	var _t1780 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1781 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1781 = 9
		} else {
			var _t1782 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1782 = 4
			} else {
				var _t1783 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1783 = 3
				} else {
					var _t1784 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1784 = 0
					} else {
						var _t1785 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1785 = 2
						} else {
							var _t1786 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1786 = 1
							} else {
								var _t1787 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1787 = 8
								} else {
									var _t1788 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1788 = 6
									} else {
										var _t1789 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1789 = 5
										} else {
											var _t1790 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1790 = 7
											} else {
												_t1790 = -1
											}
											_t1789 = _t1790
										}
										_t1788 = _t1789
									}
									_t1787 = _t1788
								}
								_t1786 = _t1787
							}
							_t1785 = _t1786
						}
						_t1784 = _t1785
					}
					_t1783 = _t1784
				}
				_t1782 = _t1783
			}
			_t1781 = _t1782
		}
		_t1780 = _t1781
	} else {
		_t1780 = -1
	}
	prediction981 := _t1780
	var _t1791 *pb.Primitive
	if prediction981 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1792 := p.parse_name()
		name991 := _t1792
		xs992 := []*pb.RelTerm{}
		cond993 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond993 {
			_t1793 := p.parse_rel_term()
			item994 := _t1793
			xs992 = append(xs992, item994)
			cond993 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms995 := xs992
		p.consumeLiteral(")")
		_t1794 := &pb.Primitive{Name: name991, Terms: rel_terms995}
		_t1791 = _t1794
	} else {
		var _t1795 *pb.Primitive
		if prediction981 == 8 {
			_t1796 := p.parse_divide()
			divide990 := _t1796
			_t1795 = divide990
		} else {
			var _t1797 *pb.Primitive
			if prediction981 == 7 {
				_t1798 := p.parse_multiply()
				multiply989 := _t1798
				_t1797 = multiply989
			} else {
				var _t1799 *pb.Primitive
				if prediction981 == 6 {
					_t1800 := p.parse_minus()
					minus988 := _t1800
					_t1799 = minus988
				} else {
					var _t1801 *pb.Primitive
					if prediction981 == 5 {
						_t1802 := p.parse_add()
						add987 := _t1802
						_t1801 = add987
					} else {
						var _t1803 *pb.Primitive
						if prediction981 == 4 {
							_t1804 := p.parse_gt_eq()
							gt_eq986 := _t1804
							_t1803 = gt_eq986
						} else {
							var _t1805 *pb.Primitive
							if prediction981 == 3 {
								_t1806 := p.parse_gt()
								gt985 := _t1806
								_t1805 = gt985
							} else {
								var _t1807 *pb.Primitive
								if prediction981 == 2 {
									_t1808 := p.parse_lt_eq()
									lt_eq984 := _t1808
									_t1807 = lt_eq984
								} else {
									var _t1809 *pb.Primitive
									if prediction981 == 1 {
										_t1810 := p.parse_lt()
										lt983 := _t1810
										_t1809 = lt983
									} else {
										var _t1811 *pb.Primitive
										if prediction981 == 0 {
											_t1812 := p.parse_eq()
											eq982 := _t1812
											_t1811 = eq982
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1809 = _t1811
									}
									_t1807 = _t1809
								}
								_t1805 = _t1807
							}
							_t1803 = _t1805
						}
						_t1801 = _t1803
					}
					_t1799 = _t1801
				}
				_t1797 = _t1799
			}
			_t1795 = _t1797
		}
		_t1791 = _t1795
	}
	result997 := _t1791
	p.recordSpan(int(span_start996), "Primitive")
	return result997
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1000 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1813 := p.parse_term()
	term998 := _t1813
	_t1814 := p.parse_term()
	term_3999 := _t1814
	p.consumeLiteral(")")
	_t1815 := &pb.RelTerm{}
	_t1815.RelTermType = &pb.RelTerm_Term{Term: term998}
	_t1816 := &pb.RelTerm{}
	_t1816.RelTermType = &pb.RelTerm_Term{Term: term_3999}
	_t1817 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1815, _t1816}}
	result1001 := _t1817
	p.recordSpan(int(span_start1000), "Primitive")
	return result1001
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1818 := p.parse_term()
	term1002 := _t1818
	_t1819 := p.parse_term()
	term_31003 := _t1819
	p.consumeLiteral(")")
	_t1820 := &pb.RelTerm{}
	_t1820.RelTermType = &pb.RelTerm_Term{Term: term1002}
	_t1821 := &pb.RelTerm{}
	_t1821.RelTermType = &pb.RelTerm_Term{Term: term_31003}
	_t1822 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1820, _t1821}}
	result1005 := _t1822
	p.recordSpan(int(span_start1004), "Primitive")
	return result1005
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1008 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1823 := p.parse_term()
	term1006 := _t1823
	_t1824 := p.parse_term()
	term_31007 := _t1824
	p.consumeLiteral(")")
	_t1825 := &pb.RelTerm{}
	_t1825.RelTermType = &pb.RelTerm_Term{Term: term1006}
	_t1826 := &pb.RelTerm{}
	_t1826.RelTermType = &pb.RelTerm_Term{Term: term_31007}
	_t1827 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1825, _t1826}}
	result1009 := _t1827
	p.recordSpan(int(span_start1008), "Primitive")
	return result1009
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1012 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1828 := p.parse_term()
	term1010 := _t1828
	_t1829 := p.parse_term()
	term_31011 := _t1829
	p.consumeLiteral(")")
	_t1830 := &pb.RelTerm{}
	_t1830.RelTermType = &pb.RelTerm_Term{Term: term1010}
	_t1831 := &pb.RelTerm{}
	_t1831.RelTermType = &pb.RelTerm_Term{Term: term_31011}
	_t1832 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1830, _t1831}}
	result1013 := _t1832
	p.recordSpan(int(span_start1012), "Primitive")
	return result1013
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1016 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1833 := p.parse_term()
	term1014 := _t1833
	_t1834 := p.parse_term()
	term_31015 := _t1834
	p.consumeLiteral(")")
	_t1835 := &pb.RelTerm{}
	_t1835.RelTermType = &pb.RelTerm_Term{Term: term1014}
	_t1836 := &pb.RelTerm{}
	_t1836.RelTermType = &pb.RelTerm_Term{Term: term_31015}
	_t1837 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1835, _t1836}}
	result1017 := _t1837
	p.recordSpan(int(span_start1016), "Primitive")
	return result1017
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1838 := p.parse_term()
	term1018 := _t1838
	_t1839 := p.parse_term()
	term_31019 := _t1839
	_t1840 := p.parse_term()
	term_41020 := _t1840
	p.consumeLiteral(")")
	_t1841 := &pb.RelTerm{}
	_t1841.RelTermType = &pb.RelTerm_Term{Term: term1018}
	_t1842 := &pb.RelTerm{}
	_t1842.RelTermType = &pb.RelTerm_Term{Term: term_31019}
	_t1843 := &pb.RelTerm{}
	_t1843.RelTermType = &pb.RelTerm_Term{Term: term_41020}
	_t1844 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1841, _t1842, _t1843}}
	result1022 := _t1844
	p.recordSpan(int(span_start1021), "Primitive")
	return result1022
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1845 := p.parse_term()
	term1023 := _t1845
	_t1846 := p.parse_term()
	term_31024 := _t1846
	_t1847 := p.parse_term()
	term_41025 := _t1847
	p.consumeLiteral(")")
	_t1848 := &pb.RelTerm{}
	_t1848.RelTermType = &pb.RelTerm_Term{Term: term1023}
	_t1849 := &pb.RelTerm{}
	_t1849.RelTermType = &pb.RelTerm_Term{Term: term_31024}
	_t1850 := &pb.RelTerm{}
	_t1850.RelTermType = &pb.RelTerm_Term{Term: term_41025}
	_t1851 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1848, _t1849, _t1850}}
	result1027 := _t1851
	p.recordSpan(int(span_start1026), "Primitive")
	return result1027
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1852 := p.parse_term()
	term1028 := _t1852
	_t1853 := p.parse_term()
	term_31029 := _t1853
	_t1854 := p.parse_term()
	term_41030 := _t1854
	p.consumeLiteral(")")
	_t1855 := &pb.RelTerm{}
	_t1855.RelTermType = &pb.RelTerm_Term{Term: term1028}
	_t1856 := &pb.RelTerm{}
	_t1856.RelTermType = &pb.RelTerm_Term{Term: term_31029}
	_t1857 := &pb.RelTerm{}
	_t1857.RelTermType = &pb.RelTerm_Term{Term: term_41030}
	_t1858 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1855, _t1856, _t1857}}
	result1032 := _t1858
	p.recordSpan(int(span_start1031), "Primitive")
	return result1032
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1859 := p.parse_term()
	term1033 := _t1859
	_t1860 := p.parse_term()
	term_31034 := _t1860
	_t1861 := p.parse_term()
	term_41035 := _t1861
	p.consumeLiteral(")")
	_t1862 := &pb.RelTerm{}
	_t1862.RelTermType = &pb.RelTerm_Term{Term: term1033}
	_t1863 := &pb.RelTerm{}
	_t1863.RelTermType = &pb.RelTerm_Term{Term: term_31034}
	_t1864 := &pb.RelTerm{}
	_t1864.RelTermType = &pb.RelTerm_Term{Term: term_41035}
	_t1865 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1862, _t1863, _t1864}}
	result1037 := _t1865
	p.recordSpan(int(span_start1036), "Primitive")
	return result1037
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1041 := int64(p.spanStart())
	var _t1866 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1866 = 1
	} else {
		var _t1867 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1867 = 1
		} else {
			var _t1868 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1868 = 1
			} else {
				var _t1869 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1869 = 1
				} else {
					var _t1870 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1870 = 0
					} else {
						var _t1871 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1871 = 1
						} else {
							var _t1872 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1872 = 1
							} else {
								var _t1873 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1873 = 1
								} else {
									var _t1874 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1874 = 1
									} else {
										var _t1875 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1875 = 1
										} else {
											var _t1876 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1876 = 1
											} else {
												var _t1877 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1877 = 1
												} else {
													var _t1878 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1878 = 1
													} else {
														var _t1879 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1879 = 1
														} else {
															var _t1880 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1880 = 1
															} else {
																_t1880 = -1
															}
															_t1879 = _t1880
														}
														_t1878 = _t1879
													}
													_t1877 = _t1878
												}
												_t1876 = _t1877
											}
											_t1875 = _t1876
										}
										_t1874 = _t1875
									}
									_t1873 = _t1874
								}
								_t1872 = _t1873
							}
							_t1871 = _t1872
						}
						_t1870 = _t1871
					}
					_t1869 = _t1870
				}
				_t1868 = _t1869
			}
			_t1867 = _t1868
		}
		_t1866 = _t1867
	}
	prediction1038 := _t1866
	var _t1881 *pb.RelTerm
	if prediction1038 == 1 {
		_t1882 := p.parse_term()
		term1040 := _t1882
		_t1883 := &pb.RelTerm{}
		_t1883.RelTermType = &pb.RelTerm_Term{Term: term1040}
		_t1881 = _t1883
	} else {
		var _t1884 *pb.RelTerm
		if prediction1038 == 0 {
			_t1885 := p.parse_specialized_value()
			specialized_value1039 := _t1885
			_t1886 := &pb.RelTerm{}
			_t1886.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1039}
			_t1884 = _t1886
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1881 = _t1884
	}
	result1042 := _t1881
	p.recordSpan(int(span_start1041), "RelTerm")
	return result1042
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1887 := p.parse_raw_value()
	raw_value1043 := _t1887
	result1045 := raw_value1043
	p.recordSpan(int(span_start1044), "Value")
	return result1045
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1051 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1888 := p.parse_name()
	name1046 := _t1888
	xs1047 := []*pb.RelTerm{}
	cond1048 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1048 {
		_t1889 := p.parse_rel_term()
		item1049 := _t1889
		xs1047 = append(xs1047, item1049)
		cond1048 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1050 := xs1047
	p.consumeLiteral(")")
	_t1890 := &pb.RelAtom{Name: name1046, Terms: rel_terms1050}
	result1052 := _t1890
	p.recordSpan(int(span_start1051), "RelAtom")
	return result1052
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1055 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1891 := p.parse_term()
	term1053 := _t1891
	_t1892 := p.parse_term()
	term_31054 := _t1892
	p.consumeLiteral(")")
	_t1893 := &pb.Cast{Input: term1053, Result: term_31054}
	result1056 := _t1893
	p.recordSpan(int(span_start1055), "Cast")
	return result1056
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1057 := []*pb.Attribute{}
	cond1058 := p.matchLookaheadLiteral("(", 0)
	for cond1058 {
		_t1894 := p.parse_attribute()
		item1059 := _t1894
		xs1057 = append(xs1057, item1059)
		cond1058 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1060 := xs1057
	p.consumeLiteral(")")
	return attributes1060
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1066 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1895 := p.parse_name()
	name1061 := _t1895
	xs1062 := []*pb.Value{}
	cond1063 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1063 {
		_t1896 := p.parse_raw_value()
		item1064 := _t1896
		xs1062 = append(xs1062, item1064)
		cond1063 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1065 := xs1062
	p.consumeLiteral(")")
	_t1897 := &pb.Attribute{Name: name1061, Args: raw_values1065}
	result1067 := _t1897
	p.recordSpan(int(span_start1066), "Attribute")
	return result1067
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1068 := []*pb.RelationId{}
	cond1069 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1069 {
		_t1898 := p.parse_relation_id()
		item1070 := _t1898
		xs1068 = append(xs1068, item1070)
		cond1069 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1071 := xs1068
	_t1899 := p.parse_script()
	script1072 := _t1899
	var _t1900 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1901 := p.parse_attrs()
		_t1900 = _t1901
	}
	attrs1073 := _t1900
	p.consumeLiteral(")")
	_t1902 := attrs1073
	if attrs1073 == nil {
		_t1902 = []*pb.Attribute{}
	}
	_t1903 := &pb.Algorithm{Global: relation_ids1071, Body: script1072, Attrs: _t1902}
	result1075 := _t1903
	p.recordSpan(int(span_start1074), "Algorithm")
	return result1075
}

func (p *Parser) parse_script() *pb.Script {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1076 := []*pb.Construct{}
	cond1077 := p.matchLookaheadLiteral("(", 0)
	for cond1077 {
		_t1904 := p.parse_construct()
		item1078 := _t1904
		xs1076 = append(xs1076, item1078)
		cond1077 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1079 := xs1076
	p.consumeLiteral(")")
	_t1905 := &pb.Script{Constructs: constructs1079}
	result1081 := _t1905
	p.recordSpan(int(span_start1080), "Script")
	return result1081
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1085 := int64(p.spanStart())
	var _t1906 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1907 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1907 = 1
		} else {
			var _t1908 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1908 = 1
			} else {
				var _t1909 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1909 = 1
				} else {
					var _t1910 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1910 = 0
					} else {
						var _t1911 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1911 = 1
						} else {
							var _t1912 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1912 = 1
							} else {
								_t1912 = -1
							}
							_t1911 = _t1912
						}
						_t1910 = _t1911
					}
					_t1909 = _t1910
				}
				_t1908 = _t1909
			}
			_t1907 = _t1908
		}
		_t1906 = _t1907
	} else {
		_t1906 = -1
	}
	prediction1082 := _t1906
	var _t1913 *pb.Construct
	if prediction1082 == 1 {
		_t1914 := p.parse_instruction()
		instruction1084 := _t1914
		_t1915 := &pb.Construct{}
		_t1915.ConstructType = &pb.Construct_Instruction{Instruction: instruction1084}
		_t1913 = _t1915
	} else {
		var _t1916 *pb.Construct
		if prediction1082 == 0 {
			_t1917 := p.parse_loop()
			loop1083 := _t1917
			_t1918 := &pb.Construct{}
			_t1918.ConstructType = &pb.Construct_Loop{Loop: loop1083}
			_t1916 = _t1918
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1913 = _t1916
	}
	result1086 := _t1913
	p.recordSpan(int(span_start1085), "Construct")
	return result1086
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1090 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1919 := p.parse_init()
	init1087 := _t1919
	_t1920 := p.parse_script()
	script1088 := _t1920
	var _t1921 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1922 := p.parse_attrs()
		_t1921 = _t1922
	}
	attrs1089 := _t1921
	p.consumeLiteral(")")
	_t1923 := attrs1089
	if attrs1089 == nil {
		_t1923 = []*pb.Attribute{}
	}
	_t1924 := &pb.Loop{Init: init1087, Body: script1088, Attrs: _t1923}
	result1091 := _t1924
	p.recordSpan(int(span_start1090), "Loop")
	return result1091
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1092 := []*pb.Instruction{}
	cond1093 := p.matchLookaheadLiteral("(", 0)
	for cond1093 {
		_t1925 := p.parse_instruction()
		item1094 := _t1925
		xs1092 = append(xs1092, item1094)
		cond1093 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1095 := xs1092
	p.consumeLiteral(")")
	return instructions1095
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1102 := int64(p.spanStart())
	var _t1926 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1927 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1927 = 1
		} else {
			var _t1928 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1928 = 4
			} else {
				var _t1929 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1929 = 3
				} else {
					var _t1930 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1930 = 2
					} else {
						var _t1931 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1931 = 0
						} else {
							_t1931 = -1
						}
						_t1930 = _t1931
					}
					_t1929 = _t1930
				}
				_t1928 = _t1929
			}
			_t1927 = _t1928
		}
		_t1926 = _t1927
	} else {
		_t1926 = -1
	}
	prediction1096 := _t1926
	var _t1932 *pb.Instruction
	if prediction1096 == 4 {
		_t1933 := p.parse_monus_def()
		monus_def1101 := _t1933
		_t1934 := &pb.Instruction{}
		_t1934.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1101}
		_t1932 = _t1934
	} else {
		var _t1935 *pb.Instruction
		if prediction1096 == 3 {
			_t1936 := p.parse_monoid_def()
			monoid_def1100 := _t1936
			_t1937 := &pb.Instruction{}
			_t1937.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1100}
			_t1935 = _t1937
		} else {
			var _t1938 *pb.Instruction
			if prediction1096 == 2 {
				_t1939 := p.parse_break()
				break1099 := _t1939
				_t1940 := &pb.Instruction{}
				_t1940.InstrType = &pb.Instruction_Break{Break: break1099}
				_t1938 = _t1940
			} else {
				var _t1941 *pb.Instruction
				if prediction1096 == 1 {
					_t1942 := p.parse_upsert()
					upsert1098 := _t1942
					_t1943 := &pb.Instruction{}
					_t1943.InstrType = &pb.Instruction_Upsert{Upsert: upsert1098}
					_t1941 = _t1943
				} else {
					var _t1944 *pb.Instruction
					if prediction1096 == 0 {
						_t1945 := p.parse_assign()
						assign1097 := _t1945
						_t1946 := &pb.Instruction{}
						_t1946.InstrType = &pb.Instruction_Assign{Assign: assign1097}
						_t1944 = _t1946
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1941 = _t1944
				}
				_t1938 = _t1941
			}
			_t1935 = _t1938
		}
		_t1932 = _t1935
	}
	result1103 := _t1932
	p.recordSpan(int(span_start1102), "Instruction")
	return result1103
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1947 := p.parse_relation_id()
	relation_id1104 := _t1947
	_t1948 := p.parse_abstraction()
	abstraction1105 := _t1948
	var _t1949 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1950 := p.parse_attrs()
		_t1949 = _t1950
	}
	attrs1106 := _t1949
	p.consumeLiteral(")")
	_t1951 := attrs1106
	if attrs1106 == nil {
		_t1951 = []*pb.Attribute{}
	}
	_t1952 := &pb.Assign{Name: relation_id1104, Body: abstraction1105, Attrs: _t1951}
	result1108 := _t1952
	p.recordSpan(int(span_start1107), "Assign")
	return result1108
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1953 := p.parse_relation_id()
	relation_id1109 := _t1953
	_t1954 := p.parse_abstraction_with_arity()
	abstraction_with_arity1110 := _t1954
	var _t1955 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1956 := p.parse_attrs()
		_t1955 = _t1956
	}
	attrs1111 := _t1955
	p.consumeLiteral(")")
	_t1957 := attrs1111
	if attrs1111 == nil {
		_t1957 = []*pb.Attribute{}
	}
	_t1958 := &pb.Upsert{Name: relation_id1109, Body: abstraction_with_arity1110[0].(*pb.Abstraction), Attrs: _t1957, ValueArity: abstraction_with_arity1110[1].(int64)}
	result1113 := _t1958
	p.recordSpan(int(span_start1112), "Upsert")
	return result1113
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1959 := p.parse_bindings()
	bindings1114 := _t1959
	_t1960 := p.parse_formula()
	formula1115 := _t1960
	p.consumeLiteral(")")
	_t1961 := &pb.Abstraction{Vars: listConcat(bindings1114[0].([]*pb.Binding), bindings1114[1].([]*pb.Binding)), Value: formula1115}
	return []interface{}{_t1961, int64(len(bindings1114[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1119 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1962 := p.parse_relation_id()
	relation_id1116 := _t1962
	_t1963 := p.parse_abstraction()
	abstraction1117 := _t1963
	var _t1964 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1965 := p.parse_attrs()
		_t1964 = _t1965
	}
	attrs1118 := _t1964
	p.consumeLiteral(")")
	_t1966 := attrs1118
	if attrs1118 == nil {
		_t1966 = []*pb.Attribute{}
	}
	_t1967 := &pb.Break{Name: relation_id1116, Body: abstraction1117, Attrs: _t1966}
	result1120 := _t1967
	p.recordSpan(int(span_start1119), "Break")
	return result1120
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1968 := p.parse_monoid()
	monoid1121 := _t1968
	_t1969 := p.parse_relation_id()
	relation_id1122 := _t1969
	_t1970 := p.parse_abstraction_with_arity()
	abstraction_with_arity1123 := _t1970
	var _t1971 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1972 := p.parse_attrs()
		_t1971 = _t1972
	}
	attrs1124 := _t1971
	p.consumeLiteral(")")
	_t1973 := attrs1124
	if attrs1124 == nil {
		_t1973 = []*pb.Attribute{}
	}
	_t1974 := &pb.MonoidDef{Monoid: monoid1121, Name: relation_id1122, Body: abstraction_with_arity1123[0].(*pb.Abstraction), Attrs: _t1973, ValueArity: abstraction_with_arity1123[1].(int64)}
	result1126 := _t1974
	p.recordSpan(int(span_start1125), "MonoidDef")
	return result1126
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1132 := int64(p.spanStart())
	var _t1975 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1976 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1976 = 3
		} else {
			var _t1977 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1977 = 0
			} else {
				var _t1978 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1978 = 1
				} else {
					var _t1979 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1979 = 2
					} else {
						_t1979 = -1
					}
					_t1978 = _t1979
				}
				_t1977 = _t1978
			}
			_t1976 = _t1977
		}
		_t1975 = _t1976
	} else {
		_t1975 = -1
	}
	prediction1127 := _t1975
	var _t1980 *pb.Monoid
	if prediction1127 == 3 {
		_t1981 := p.parse_sum_monoid()
		sum_monoid1131 := _t1981
		_t1982 := &pb.Monoid{}
		_t1982.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1131}
		_t1980 = _t1982
	} else {
		var _t1983 *pb.Monoid
		if prediction1127 == 2 {
			_t1984 := p.parse_max_monoid()
			max_monoid1130 := _t1984
			_t1985 := &pb.Monoid{}
			_t1985.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1130}
			_t1983 = _t1985
		} else {
			var _t1986 *pb.Monoid
			if prediction1127 == 1 {
				_t1987 := p.parse_min_monoid()
				min_monoid1129 := _t1987
				_t1988 := &pb.Monoid{}
				_t1988.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1129}
				_t1986 = _t1988
			} else {
				var _t1989 *pb.Monoid
				if prediction1127 == 0 {
					_t1990 := p.parse_or_monoid()
					or_monoid1128 := _t1990
					_t1991 := &pb.Monoid{}
					_t1991.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1128}
					_t1989 = _t1991
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1986 = _t1989
			}
			_t1983 = _t1986
		}
		_t1980 = _t1983
	}
	result1133 := _t1980
	p.recordSpan(int(span_start1132), "Monoid")
	return result1133
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1992 := &pb.OrMonoid{}
	result1135 := _t1992
	p.recordSpan(int(span_start1134), "OrMonoid")
	return result1135
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1137 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1993 := p.parse_type()
	type1136 := _t1993
	p.consumeLiteral(")")
	_t1994 := &pb.MinMonoid{Type: type1136}
	result1138 := _t1994
	p.recordSpan(int(span_start1137), "MinMonoid")
	return result1138
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1140 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1995 := p.parse_type()
	type1139 := _t1995
	p.consumeLiteral(")")
	_t1996 := &pb.MaxMonoid{Type: type1139}
	result1141 := _t1996
	p.recordSpan(int(span_start1140), "MaxMonoid")
	return result1141
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1143 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1997 := p.parse_type()
	type1142 := _t1997
	p.consumeLiteral(")")
	_t1998 := &pb.SumMonoid{Type: type1142}
	result1144 := _t1998
	p.recordSpan(int(span_start1143), "SumMonoid")
	return result1144
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1149 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1999 := p.parse_monoid()
	monoid1145 := _t1999
	_t2000 := p.parse_relation_id()
	relation_id1146 := _t2000
	_t2001 := p.parse_abstraction_with_arity()
	abstraction_with_arity1147 := _t2001
	var _t2002 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2003 := p.parse_attrs()
		_t2002 = _t2003
	}
	attrs1148 := _t2002
	p.consumeLiteral(")")
	_t2004 := attrs1148
	if attrs1148 == nil {
		_t2004 = []*pb.Attribute{}
	}
	_t2005 := &pb.MonusDef{Monoid: monoid1145, Name: relation_id1146, Body: abstraction_with_arity1147[0].(*pb.Abstraction), Attrs: _t2004, ValueArity: abstraction_with_arity1147[1].(int64)}
	result1150 := _t2005
	p.recordSpan(int(span_start1149), "MonusDef")
	return result1150
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2006 := p.parse_relation_id()
	relation_id1151 := _t2006
	_t2007 := p.parse_abstraction()
	abstraction1152 := _t2007
	_t2008 := p.parse_functional_dependency_keys()
	functional_dependency_keys1153 := _t2008
	_t2009 := p.parse_functional_dependency_values()
	functional_dependency_values1154 := _t2009
	p.consumeLiteral(")")
	_t2010 := &pb.FunctionalDependency{Guard: abstraction1152, Keys: functional_dependency_keys1153, Values: functional_dependency_values1154}
	_t2011 := &pb.Constraint{Name: relation_id1151}
	_t2011.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2010}
	result1156 := _t2011
	p.recordSpan(int(span_start1155), "Constraint")
	return result1156
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1157 := []*pb.Var{}
	cond1158 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1158 {
		_t2012 := p.parse_var()
		item1159 := _t2012
		xs1157 = append(xs1157, item1159)
		cond1158 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1160 := xs1157
	p.consumeLiteral(")")
	return vars1160
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1161 := []*pb.Var{}
	cond1162 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1162 {
		_t2013 := p.parse_var()
		item1163 := _t2013
		xs1161 = append(xs1161, item1163)
		cond1162 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1164 := xs1161
	p.consumeLiteral(")")
	return vars1164
}

func (p *Parser) parse_data() *pb.Data {
	span_start1170 := int64(p.spanStart())
	var _t2014 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2015 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2015 = 3
		} else {
			var _t2016 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2016 = 0
			} else {
				var _t2017 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2017 = 2
				} else {
					var _t2018 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2018 = 1
					} else {
						_t2018 = -1
					}
					_t2017 = _t2018
				}
				_t2016 = _t2017
			}
			_t2015 = _t2016
		}
		_t2014 = _t2015
	} else {
		_t2014 = -1
	}
	prediction1165 := _t2014
	var _t2019 *pb.Data
	if prediction1165 == 3 {
		_t2020 := p.parse_iceberg_data()
		iceberg_data1169 := _t2020
		_t2021 := &pb.Data{}
		_t2021.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1169}
		_t2019 = _t2021
	} else {
		var _t2022 *pb.Data
		if prediction1165 == 2 {
			_t2023 := p.parse_csv_data()
			csv_data1168 := _t2023
			_t2024 := &pb.Data{}
			_t2024.DataType = &pb.Data_CsvData{CsvData: csv_data1168}
			_t2022 = _t2024
		} else {
			var _t2025 *pb.Data
			if prediction1165 == 1 {
				_t2026 := p.parse_betree_relation()
				betree_relation1167 := _t2026
				_t2027 := &pb.Data{}
				_t2027.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1167}
				_t2025 = _t2027
			} else {
				var _t2028 *pb.Data
				if prediction1165 == 0 {
					_t2029 := p.parse_edb()
					edb1166 := _t2029
					_t2030 := &pb.Data{}
					_t2030.DataType = &pb.Data_Edb{Edb: edb1166}
					_t2028 = _t2030
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2025 = _t2028
			}
			_t2022 = _t2025
		}
		_t2019 = _t2022
	}
	result1171 := _t2019
	p.recordSpan(int(span_start1170), "Data")
	return result1171
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1175 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2031 := p.parse_relation_id()
	relation_id1172 := _t2031
	_t2032 := p.parse_edb_path()
	edb_path1173 := _t2032
	_t2033 := p.parse_edb_types()
	edb_types1174 := _t2033
	p.consumeLiteral(")")
	_t2034 := &pb.EDB{TargetId: relation_id1172, Path: edb_path1173, Types: edb_types1174}
	result1176 := _t2034
	p.recordSpan(int(span_start1175), "EDB")
	return result1176
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1177 := []string{}
	cond1178 := p.matchLookaheadTerminal("STRING", 0)
	for cond1178 {
		item1179 := p.consumeTerminal("STRING").Value.str
		xs1177 = append(xs1177, item1179)
		cond1178 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1180 := xs1177
	p.consumeLiteral("]")
	return strings1180
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1181 := []*pb.Type{}
	cond1182 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1182 {
		_t2035 := p.parse_type()
		item1183 := _t2035
		xs1181 = append(xs1181, item1183)
		cond1182 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1184 := xs1181
	p.consumeLiteral("]")
	return types1184
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1187 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2036 := p.parse_relation_id()
	relation_id1185 := _t2036
	_t2037 := p.parse_betree_info()
	betree_info1186 := _t2037
	p.consumeLiteral(")")
	_t2038 := &pb.BeTreeRelation{Name: relation_id1185, RelationInfo: betree_info1186}
	result1188 := _t2038
	p.recordSpan(int(span_start1187), "BeTreeRelation")
	return result1188
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1192 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2039 := p.parse_betree_info_key_types()
	betree_info_key_types1189 := _t2039
	_t2040 := p.parse_betree_info_value_types()
	betree_info_value_types1190 := _t2040
	_t2041 := p.parse_config_dict()
	config_dict1191 := _t2041
	p.consumeLiteral(")")
	_t2042 := p.construct_betree_info(betree_info_key_types1189, betree_info_value_types1190, config_dict1191)
	result1193 := _t2042
	p.recordSpan(int(span_start1192), "BeTreeInfo")
	return result1193
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1194 := []*pb.Type{}
	cond1195 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1195 {
		_t2043 := p.parse_type()
		item1196 := _t2043
		xs1194 = append(xs1194, item1196)
		cond1195 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1197 := xs1194
	p.consumeLiteral(")")
	return types1197
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1198 := []*pb.Type{}
	cond1199 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1199 {
		_t2044 := p.parse_type()
		item1200 := _t2044
		xs1198 = append(xs1198, item1200)
		cond1199 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1201 := xs1198
	p.consumeLiteral(")")
	return types1201
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1207 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2045 := p.parse_csvlocator()
	csvlocator1202 := _t2045
	_t2046 := p.parse_csv_config()
	csv_config1203 := _t2046
	var _t2047 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2048 := p.parse_gnf_columns()
		_t2047 = _t2048
	}
	gnf_columns1204 := _t2047
	var _t2049 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2050 := p.parse_target_relations()
		_t2049 = _t2050
	}
	target_relations1205 := _t2049
	_t2051 := p.parse_csv_asof()
	csv_asof1206 := _t2051
	p.consumeLiteral(")")
	_t2052 := p.construct_csv_data(csvlocator1202, csv_config1203, gnf_columns1204, target_relations1205, csv_asof1206)
	result1208 := _t2052
	p.recordSpan(int(span_start1207), "CSVData")
	return result1208
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1211 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2053 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2054 := p.parse_csv_locator_paths()
		_t2053 = _t2054
	}
	csv_locator_paths1209 := _t2053
	var _t2055 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2056 := p.parse_csv_locator_inline_data()
		_t2055 = ptr(_t2056)
	}
	csv_locator_inline_data1210 := _t2055
	p.consumeLiteral(")")
	_t2057 := csv_locator_paths1209
	if csv_locator_paths1209 == nil {
		_t2057 = []string{}
	}
	_t2058 := &pb.CSVLocator{Paths: _t2057, InlineData: []byte(deref(csv_locator_inline_data1210, ""))}
	result1212 := _t2058
	p.recordSpan(int(span_start1211), "CSVLocator")
	return result1212
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1213 := []string{}
	cond1214 := p.matchLookaheadTerminal("STRING", 0)
	for cond1214 {
		item1215 := p.consumeTerminal("STRING").Value.str
		xs1213 = append(xs1213, item1215)
		cond1214 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1216 := xs1213
	p.consumeLiteral(")")
	return strings1216
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1217 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1217
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2059 := p.parse_config_dict()
	config_dict1218 := _t2059
	var _t2060 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2061 := p.parse__storage_integration()
		_t2060 = _t2061
	}
	_storage_integration1219 := _t2060
	p.consumeLiteral(")")
	_t2062 := p.construct_csv_config(config_dict1218, _storage_integration1219)
	result1221 := _t2062
	p.recordSpan(int(span_start1220), "CSVConfig")
	return result1221
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2063 := p.parse_config_dict()
	config_dict1222 := _t2063
	p.consumeLiteral(")")
	return config_dict1222
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1223 := []*pb.GNFColumn{}
	cond1224 := p.matchLookaheadLiteral("(", 0)
	for cond1224 {
		_t2064 := p.parse_gnf_column()
		item1225 := _t2064
		xs1223 = append(xs1223, item1225)
		cond1224 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1226 := xs1223
	p.consumeLiteral(")")
	return gnf_columns1226
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1233 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2065 := p.parse_gnf_column_path()
	gnf_column_path1227 := _t2065
	var _t2066 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2067 := p.parse_relation_id()
		_t2066 = _t2067
	}
	relation_id1228 := _t2066
	p.consumeLiteral("[")
	xs1229 := []*pb.Type{}
	cond1230 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1230 {
		_t2068 := p.parse_type()
		item1231 := _t2068
		xs1229 = append(xs1229, item1231)
		cond1230 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1232 := xs1229
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2069 := &pb.GNFColumn{ColumnPath: gnf_column_path1227, TargetId: relation_id1228, Types: types1232}
	result1234 := _t2069
	p.recordSpan(int(span_start1233), "GNFColumn")
	return result1234
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2070 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2070 = 1
	} else {
		var _t2071 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2071 = 0
		} else {
			_t2071 = -1
		}
		_t2070 = _t2071
	}
	prediction1235 := _t2070
	var _t2072 []string
	if prediction1235 == 1 {
		p.consumeLiteral("[")
		xs1237 := []string{}
		cond1238 := p.matchLookaheadTerminal("STRING", 0)
		for cond1238 {
			item1239 := p.consumeTerminal("STRING").Value.str
			xs1237 = append(xs1237, item1239)
			cond1238 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1240 := xs1237
		p.consumeLiteral("]")
		_t2072 = strings1240
	} else {
		var _t2073 []string
		if prediction1235 == 0 {
			string1236 := p.consumeTerminal("STRING").Value.str
			_ = string1236
			_t2073 = []string{string1236}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2072 = _t2073
	}
	return _t2072
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1243 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2074 := p.parse_relation_keys()
	relation_keys1241 := _t2074
	_t2075 := p.parse_relation_body()
	relation_body1242 := _t2075
	p.consumeLiteral(")")
	_t2076 := p.construct_relations(relation_keys1241, relation_body1242)
	result1244 := _t2076
	p.recordSpan(int(span_start1243), "TargetRelations")
	return result1244
}

func (p *Parser) parse_relation_keys() []*pb.NamedColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1245 := []*pb.NamedColumn{}
	cond1246 := p.matchLookaheadLiteral("(", 0)
	for cond1246 {
		_t2077 := p.parse_named_column()
		item1247 := _t2077
		xs1245 = append(xs1245, item1247)
		cond1246 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1248 := xs1245
	p.consumeLiteral(")")
	return named_columns1248
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1251 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1249 := p.consumeTerminal("STRING").Value.str
	_t2078 := p.parse_type()
	type1250 := _t2078
	p.consumeLiteral(")")
	_t2079 := &pb.NamedColumn{Name: string1249, Type: type1250}
	result1252 := _t2079
	p.recordSpan(int(span_start1251), "NamedColumn")
	return result1252
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1257 := int64(p.spanStart())
	var _t2080 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2081 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2081 = 0
		} else {
			var _t2082 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2082 = 1
			} else {
				_t2082 = 0
			}
			_t2081 = _t2082
		}
		_t2080 = _t2081
	} else {
		_t2080 = 0
	}
	prediction1253 := _t2080
	var _t2083 *pb.TargetRelations
	if prediction1253 == 1 {
		_t2084 := p.parse_cdc_inserts()
		cdc_inserts1255 := _t2084
		_t2085 := p.parse_cdc_deletes()
		cdc_deletes1256 := _t2085
		_t2086 := p.construct_cdc_relations(cdc_inserts1255, cdc_deletes1256)
		_t2083 = _t2086
	} else {
		var _t2087 *pb.TargetRelations
		if prediction1253 == 0 {
			_t2088 := p.parse_non_cdc_relations()
			non_cdc_relations1254 := _t2088
			_t2089 := p.construct_non_cdc_relations(non_cdc_relations1254)
			_t2087 = _t2089
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2083 = _t2087
	}
	result1258 := _t2083
	p.recordSpan(int(span_start1257), "TargetRelations")
	return result1258
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1259 := []*pb.TargetRelation{}
	cond1260 := p.matchLookaheadLiteral("(", 0)
	for cond1260 {
		_t2090 := p.parse_target_relation()
		item1261 := _t2090
		xs1259 = append(xs1259, item1261)
		cond1260 = p.matchLookaheadLiteral("(", 0)
	}
	return xs1259
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1267 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2091 := p.parse_relation_id()
	relation_id1262 := _t2091
	xs1263 := []*pb.NamedColumn{}
	cond1264 := p.matchLookaheadLiteral("(", 0)
	for cond1264 {
		_t2092 := p.parse_named_column()
		item1265 := _t2092
		xs1263 = append(xs1263, item1265)
		cond1264 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1266 := xs1263
	p.consumeLiteral(")")
	_t2093 := &pb.TargetRelation{TargetId: relation_id1262, Values: named_columns1266}
	result1268 := _t2093
	p.recordSpan(int(span_start1267), "TargetRelation")
	return result1268
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1269 := []*pb.TargetRelation{}
	cond1270 := p.matchLookaheadLiteral("(", 0)
	for cond1270 {
		_t2094 := p.parse_target_relation()
		item1271 := _t2094
		xs1269 = append(xs1269, item1271)
		cond1270 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1272 := xs1269
	p.consumeLiteral(")")
	return target_relations1272
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1273 := []*pb.TargetRelation{}
	cond1274 := p.matchLookaheadLiteral("(", 0)
	for cond1274 {
		_t2095 := p.parse_target_relation()
		item1275 := _t2095
		xs1273 = append(xs1273, item1275)
		cond1274 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1276 := xs1273
	p.consumeLiteral(")")
	return target_relations1276
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1277 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1277
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1284 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2096 := p.parse_iceberg_locator()
	iceberg_locator1278 := _t2096
	_t2097 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1279 := _t2097
	_t2098 := p.parse_gnf_columns()
	gnf_columns1280 := _t2098
	var _t2099 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2100 := p.parse_iceberg_from_snapshot()
		_t2099 = ptr(_t2100)
	}
	iceberg_from_snapshot1281 := _t2099
	var _t2101 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2102 := p.parse_iceberg_to_snapshot()
		_t2101 = ptr(_t2102)
	}
	iceberg_to_snapshot1282 := _t2101
	_t2103 := p.parse_boolean_value()
	boolean_value1283 := _t2103
	p.consumeLiteral(")")
	_t2104 := p.construct_iceberg_data(iceberg_locator1278, iceberg_catalog_config1279, gnf_columns1280, iceberg_from_snapshot1281, iceberg_to_snapshot1282, boolean_value1283)
	result1285 := _t2104
	p.recordSpan(int(span_start1284), "IcebergData")
	return result1285
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1289 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2105 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1286 := _t2105
	_t2106 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1287 := _t2106
	_t2107 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1288 := _t2107
	p.consumeLiteral(")")
	_t2108 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1286, Namespace: iceberg_locator_namespace1287, Warehouse: iceberg_locator_warehouse1288}
	result1290 := _t2108
	p.recordSpan(int(span_start1289), "IcebergLocator")
	return result1290
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1291 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1291
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1292 := []string{}
	cond1293 := p.matchLookaheadTerminal("STRING", 0)
	for cond1293 {
		item1294 := p.consumeTerminal("STRING").Value.str
		xs1292 = append(xs1292, item1294)
		cond1293 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1295 := xs1292
	p.consumeLiteral(")")
	return strings1295
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1296 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1296
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1301 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2109 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1297 := _t2109
	var _t2110 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2111 := p.parse_iceberg_catalog_config_scope()
		_t2110 = ptr(_t2111)
	}
	iceberg_catalog_config_scope1298 := _t2110
	_t2112 := p.parse_iceberg_properties()
	iceberg_properties1299 := _t2112
	_t2113 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1300 := _t2113
	p.consumeLiteral(")")
	_t2114 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1297, iceberg_catalog_config_scope1298, iceberg_properties1299, iceberg_auth_properties1300)
	result1302 := _t2114
	p.recordSpan(int(span_start1301), "IcebergCatalogConfig")
	return result1302
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1303 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1303
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1304 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1304
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1305 := [][]interface{}{}
	cond1306 := p.matchLookaheadLiteral("(", 0)
	for cond1306 {
		_t2115 := p.parse_iceberg_property_entry()
		item1307 := _t2115
		xs1305 = append(xs1305, item1307)
		cond1306 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1308 := xs1305
	p.consumeLiteral(")")
	return iceberg_property_entrys1308
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1309 := p.consumeTerminal("STRING").Value.str
	string_31310 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1309, string_31310}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1311 := [][]interface{}{}
	cond1312 := p.matchLookaheadLiteral("(", 0)
	for cond1312 {
		_t2116 := p.parse_iceberg_masked_property_entry()
		item1313 := _t2116
		xs1311 = append(xs1311, item1313)
		cond1312 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1314 := xs1311
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1314
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1315 := p.consumeTerminal("STRING").Value.str
	string_31316 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1315, string_31316}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1317 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1317
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1318 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1318
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1320 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2117 := p.parse_fragment_id()
	fragment_id1319 := _t2117
	p.consumeLiteral(")")
	_t2118 := &pb.Undefine{FragmentId: fragment_id1319}
	result1321 := _t2118
	p.recordSpan(int(span_start1320), "Undefine")
	return result1321
}

func (p *Parser) parse_context() *pb.Context {
	span_start1326 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1322 := []*pb.RelationId{}
	cond1323 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1323 {
		_t2119 := p.parse_relation_id()
		item1324 := _t2119
		xs1322 = append(xs1322, item1324)
		cond1323 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1325 := xs1322
	p.consumeLiteral(")")
	_t2120 := &pb.Context{Relations: relation_ids1325}
	result1327 := _t2120
	p.recordSpan(int(span_start1326), "Context")
	return result1327
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1333 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2121 := p.parse_edb_path()
	edb_path1328 := _t2121
	xs1329 := []*pb.SnapshotMapping{}
	cond1330 := p.matchLookaheadLiteral("[", 0)
	for cond1330 {
		_t2122 := p.parse_snapshot_mapping()
		item1331 := _t2122
		xs1329 = append(xs1329, item1331)
		cond1330 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1332 := xs1329
	p.consumeLiteral(")")
	_t2123 := &pb.Snapshot{Prefix: edb_path1328, Mappings: snapshot_mappings1332}
	result1334 := _t2123
	p.recordSpan(int(span_start1333), "Snapshot")
	return result1334
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1337 := int64(p.spanStart())
	_t2124 := p.parse_edb_path()
	edb_path1335 := _t2124
	_t2125 := p.parse_relation_id()
	relation_id1336 := _t2125
	_t2126 := &pb.SnapshotMapping{DestinationPath: edb_path1335, SourceRelation: relation_id1336}
	result1338 := _t2126
	p.recordSpan(int(span_start1337), "SnapshotMapping")
	return result1338
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1339 := []*pb.Read{}
	cond1340 := p.matchLookaheadLiteral("(", 0)
	for cond1340 {
		_t2127 := p.parse_read()
		item1341 := _t2127
		xs1339 = append(xs1339, item1341)
		cond1340 = p.matchLookaheadLiteral("(", 0)
	}
	reads1342 := xs1339
	p.consumeLiteral(")")
	return reads1342
}

func (p *Parser) parse_read() *pb.Read {
	span_start1349 := int64(p.spanStart())
	var _t2128 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2129 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2129 = 2
		} else {
			var _t2130 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2130 = 1
			} else {
				var _t2131 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2131 = 4
				} else {
					var _t2132 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2132 = 4
					} else {
						var _t2133 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2133 = 0
						} else {
							var _t2134 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2134 = 3
							} else {
								_t2134 = -1
							}
							_t2133 = _t2134
						}
						_t2132 = _t2133
					}
					_t2131 = _t2132
				}
				_t2130 = _t2131
			}
			_t2129 = _t2130
		}
		_t2128 = _t2129
	} else {
		_t2128 = -1
	}
	prediction1343 := _t2128
	var _t2135 *pb.Read
	if prediction1343 == 4 {
		_t2136 := p.parse_export()
		export1348 := _t2136
		_t2137 := &pb.Read{}
		_t2137.ReadType = &pb.Read_Export{Export: export1348}
		_t2135 = _t2137
	} else {
		var _t2138 *pb.Read
		if prediction1343 == 3 {
			_t2139 := p.parse_abort()
			abort1347 := _t2139
			_t2140 := &pb.Read{}
			_t2140.ReadType = &pb.Read_Abort{Abort: abort1347}
			_t2138 = _t2140
		} else {
			var _t2141 *pb.Read
			if prediction1343 == 2 {
				_t2142 := p.parse_what_if()
				what_if1346 := _t2142
				_t2143 := &pb.Read{}
				_t2143.ReadType = &pb.Read_WhatIf{WhatIf: what_if1346}
				_t2141 = _t2143
			} else {
				var _t2144 *pb.Read
				if prediction1343 == 1 {
					_t2145 := p.parse_output()
					output1345 := _t2145
					_t2146 := &pb.Read{}
					_t2146.ReadType = &pb.Read_Output{Output: output1345}
					_t2144 = _t2146
				} else {
					var _t2147 *pb.Read
					if prediction1343 == 0 {
						_t2148 := p.parse_demand()
						demand1344 := _t2148
						_t2149 := &pb.Read{}
						_t2149.ReadType = &pb.Read_Demand{Demand: demand1344}
						_t2147 = _t2149
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2144 = _t2147
				}
				_t2141 = _t2144
			}
			_t2138 = _t2141
		}
		_t2135 = _t2138
	}
	result1350 := _t2135
	p.recordSpan(int(span_start1349), "Read")
	return result1350
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1352 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2150 := p.parse_relation_id()
	relation_id1351 := _t2150
	p.consumeLiteral(")")
	_t2151 := &pb.Demand{RelationId: relation_id1351}
	result1353 := _t2151
	p.recordSpan(int(span_start1352), "Demand")
	return result1353
}

func (p *Parser) parse_output() *pb.Output {
	span_start1356 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2152 := p.parse_name()
	name1354 := _t2152
	_t2153 := p.parse_relation_id()
	relation_id1355 := _t2153
	p.consumeLiteral(")")
	_t2154 := &pb.Output{Name: name1354, RelationId: relation_id1355}
	result1357 := _t2154
	p.recordSpan(int(span_start1356), "Output")
	return result1357
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1360 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2155 := p.parse_name()
	name1358 := _t2155
	_t2156 := p.parse_epoch()
	epoch1359 := _t2156
	p.consumeLiteral(")")
	_t2157 := &pb.WhatIf{Branch: name1358, Epoch: epoch1359}
	result1361 := _t2157
	p.recordSpan(int(span_start1360), "WhatIf")
	return result1361
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1364 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2158 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2159 := p.parse_name()
		_t2158 = ptr(_t2159)
	}
	name1362 := _t2158
	_t2160 := p.parse_relation_id()
	relation_id1363 := _t2160
	p.consumeLiteral(")")
	_t2161 := &pb.Abort{Name: deref(name1362, "abort"), RelationId: relation_id1363}
	result1365 := _t2161
	p.recordSpan(int(span_start1364), "Abort")
	return result1365
}

func (p *Parser) parse_export() *pb.Export {
	span_start1369 := int64(p.spanStart())
	var _t2162 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2163 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2163 = 1
		} else {
			var _t2164 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2164 = 0
			} else {
				_t2164 = -1
			}
			_t2163 = _t2164
		}
		_t2162 = _t2163
	} else {
		_t2162 = -1
	}
	prediction1366 := _t2162
	var _t2165 *pb.Export
	if prediction1366 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2166 := p.parse_export_iceberg_config()
		export_iceberg_config1368 := _t2166
		p.consumeLiteral(")")
		_t2167 := &pb.Export{}
		_t2167.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1368}
		_t2165 = _t2167
	} else {
		var _t2168 *pb.Export
		if prediction1366 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2169 := p.parse_export_csv_config()
			export_csv_config1367 := _t2169
			p.consumeLiteral(")")
			_t2170 := &pb.Export{}
			_t2170.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1367}
			_t2168 = _t2170
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2165 = _t2168
	}
	result1370 := _t2165
	p.recordSpan(int(span_start1369), "Export")
	return result1370
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1378 := int64(p.spanStart())
	var _t2171 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2172 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2172 = 0
		} else {
			var _t2173 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2173 = 1
			} else {
				_t2173 = -1
			}
			_t2172 = _t2173
		}
		_t2171 = _t2172
	} else {
		_t2171 = -1
	}
	prediction1371 := _t2171
	var _t2174 *pb.ExportCSVConfig
	if prediction1371 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2175 := p.parse_export_csv_path()
		export_csv_path1375 := _t2175
		_t2176 := p.parse_export_csv_columns_list()
		export_csv_columns_list1376 := _t2176
		_t2177 := p.parse_config_dict()
		config_dict1377 := _t2177
		p.consumeLiteral(")")
		_t2178 := p.construct_export_csv_config(export_csv_path1375, export_csv_columns_list1376, config_dict1377)
		_t2174 = _t2178
	} else {
		var _t2179 *pb.ExportCSVConfig
		if prediction1371 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2180 := p.parse_export_csv_output_location()
			export_csv_output_location1372 := _t2180
			_t2181 := p.parse_export_csv_source()
			export_csv_source1373 := _t2181
			_t2182 := p.parse_csv_config()
			csv_config1374 := _t2182
			p.consumeLiteral(")")
			_t2183 := p.construct_export_csv_config_with_location(export_csv_output_location1372, export_csv_source1373, csv_config1374)
			_t2179 = _t2183
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2174 = _t2179
	}
	result1379 := _t2174
	p.recordSpan(int(span_start1378), "ExportCSVConfig")
	return result1379
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2184 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2185 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2185 = 1
		} else {
			var _t2186 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2186 = 0
			} else {
				_t2186 = -1
			}
			_t2185 = _t2186
		}
		_t2184 = _t2185
	} else {
		_t2184 = -1
	}
	prediction1380 := _t2184
	var _t2187 []interface{}
	if prediction1380 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2188 := p.parse_name()
		name1382 := _t2188
		p.consumeLiteral(")")
		_t2187 = []interface{}{"", name1382}
	} else {
		var _t2189 []interface{}
		if prediction1380 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1381 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2189 = []interface{}{string1381, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2187 = _t2189
	}
	return _t2187
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1389 := int64(p.spanStart())
	var _t2190 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2191 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2191 = 1
		} else {
			var _t2192 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2192 = 0
			} else {
				_t2192 = -1
			}
			_t2191 = _t2192
		}
		_t2190 = _t2191
	} else {
		_t2190 = -1
	}
	prediction1383 := _t2190
	var _t2193 *pb.ExportCSVSource
	if prediction1383 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2194 := p.parse_relation_id()
		relation_id1388 := _t2194
		p.consumeLiteral(")")
		_t2195 := &pb.ExportCSVSource{}
		_t2195.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1388}
		_t2193 = _t2195
	} else {
		var _t2196 *pb.ExportCSVSource
		if prediction1383 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1384 := []*pb.ExportCSVColumn{}
			cond1385 := p.matchLookaheadLiteral("(", 0)
			for cond1385 {
				_t2197 := p.parse_export_csv_column()
				item1386 := _t2197
				xs1384 = append(xs1384, item1386)
				cond1385 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1387 := xs1384
			p.consumeLiteral(")")
			_t2198 := &pb.ExportCSVColumns{Columns: export_csv_columns1387}
			_t2199 := &pb.ExportCSVSource{}
			_t2199.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2198}
			_t2196 = _t2199
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2193 = _t2196
	}
	result1390 := _t2193
	p.recordSpan(int(span_start1389), "ExportCSVSource")
	return result1390
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1393 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1391 := p.consumeTerminal("STRING").Value.str
	_t2200 := p.parse_relation_id()
	relation_id1392 := _t2200
	p.consumeLiteral(")")
	_t2201 := &pb.ExportCSVColumn{ColumnName: string1391, ColumnData: relation_id1392}
	result1394 := _t2201
	p.recordSpan(int(span_start1393), "ExportCSVColumn")
	return result1394
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1395 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1395
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1396 := []*pb.ExportCSVColumn{}
	cond1397 := p.matchLookaheadLiteral("(", 0)
	for cond1397 {
		_t2202 := p.parse_export_csv_column()
		item1398 := _t2202
		xs1396 = append(xs1396, item1398)
		cond1397 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1399 := xs1396
	p.consumeLiteral(")")
	return export_csv_columns1399
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1405 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2203 := p.parse_iceberg_locator()
	iceberg_locator1400 := _t2203
	_t2204 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1401 := _t2204
	_t2205 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1402 := _t2205
	_t2206 := p.parse_iceberg_table_properties()
	iceberg_table_properties1403 := _t2206
	var _t2207 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2208 := p.parse_config_dict()
		_t2207 = _t2208
	}
	config_dict1404 := _t2207
	p.consumeLiteral(")")
	_t2209 := p.construct_export_iceberg_config_full(iceberg_locator1400, iceberg_catalog_config1401, export_iceberg_table_def1402, iceberg_table_properties1403, config_dict1404)
	result1406 := _t2209
	p.recordSpan(int(span_start1405), "ExportIcebergConfig")
	return result1406
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1408 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2210 := p.parse_relation_id()
	relation_id1407 := _t2210
	p.consumeLiteral(")")
	result1409 := relation_id1407
	p.recordSpan(int(span_start1408), "RelationId")
	return result1409
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1410 := [][]interface{}{}
	cond1411 := p.matchLookaheadLiteral("(", 0)
	for cond1411 {
		_t2211 := p.parse_iceberg_property_entry()
		item1412 := _t2211
		xs1410 = append(xs1410, item1412)
		cond1411 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1413 := xs1410
	p.consumeLiteral(")")
	return iceberg_property_entrys1413
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
