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
	var _t2221 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2221
	var _t2222 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2222
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2223 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2223
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2224 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2224
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2225 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2225
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2226 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2226
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2227 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2227
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2228 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2228
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2229 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2229
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2230 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2230
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2231 := &pb.PlainTargets{Targets: targets}
	_t2232 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2232.Body = &pb.TargetRelations_Plain{Plain: _t2231}
	return _t2232
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2233 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2234 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2234.Body = &pb.TargetRelations_Cdc{Cdc: _t2233}
	return _t2234
}

func (p *Parser) construct_relations(keys []interface{}, body *pb.TargetRelations) *pb.TargetRelations {
	var _t2235 interface{}
	if hasProtoField(body, "plain") {
		_t2236 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool)}
		_t2236.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2236
	}
	_ = _t2235
	_t2237 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool)}
	_t2237.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2237
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2238 := columns_opt
	if columns_opt == nil {
		_t2238 = []*pb.GNFColumn{}
	}
	_t2239 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2238, Asof: asof, Relations: relations_opt}
	return _t2239
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2240 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2240
	_t2241 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2241
	_t2242 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2242
	_t2243 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2243
	_t2244 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2244
	_t2245 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2245
	_t2246 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2246
	_t2247 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2247
	_t2248 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2248
	_t2249 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2249
	_t2250 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2250
	_t2251 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2251
	_t2252 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2252
	_t2253 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2253
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2254 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2254
	config := dictFromList(storage_integration_opt)
	_t2255 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2256 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2257 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2258 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2259 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2260 := &pb.StorageIntegration{Provider: _t2255, AzureSasToken: _t2256, S3Region: _t2257, S3AccessKeyId: _t2258, S3SecretAccessKey: _t2259}
	return _t2260
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2261 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2261
	_t2262 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2262
	_t2263 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2263
	_t2264 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2264
	_t2265 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2265
	_t2266 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2266
	_t2267 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2267
	_t2268 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2268
	_t2269 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2269
	_t2270 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2270.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2270.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2270
	_t2271 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2271
}

func (p *Parser) default_configure() *pb.Configure {
	_t2272 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2272
	_t2273 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2273
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
	_t2274 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2274
	_t2275 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2275
	_t2276 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2276
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2277 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2277
	_t2278 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2278
	_t2279 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2279
	_t2280 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2280
	_t2281 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2281
	_t2282 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2282
	_t2283 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2283
	_t2284 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2284
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2285 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2285
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2286 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2286
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2287 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2287
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2288 := config_dict
	if config_dict == nil {
		_t2288 = [][]interface{}{}
	}
	cfg := dictFromList(_t2288)
	_t2289 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2289
	_t2290 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2290
	_t2291 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2291
	table_props := stringMapFromPairs(table_property_pairs)
	_t2292 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2292
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start714 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1416 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1417 := p.parse_configure()
		_t1416 = _t1417
	}
	configure708 := _t1416
	var _t1418 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1419 := p.parse_sync()
		_t1418 = _t1419
	}
	sync709 := _t1418
	xs710 := []*pb.Epoch{}
	cond711 := p.matchLookaheadLiteral("(", 0)
	for cond711 {
		_t1420 := p.parse_epoch()
		item712 := _t1420
		xs710 = append(xs710, item712)
		cond711 = p.matchLookaheadLiteral("(", 0)
	}
	epochs713 := xs710
	p.consumeLiteral(")")
	_t1421 := p.default_configure()
	_t1422 := configure708
	if configure708 == nil {
		_t1422 = _t1421
	}
	_t1423 := &pb.Transaction{Epochs: epochs713, Configure: _t1422, Sync: sync709}
	result715 := _t1423
	p.recordSpan(int(span_start714), "Transaction")
	return result715
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1424 := p.parse_config_dict()
	config_dict716 := _t1424
	p.consumeLiteral(")")
	_t1425 := p.construct_configure(config_dict716)
	result718 := _t1425
	p.recordSpan(int(span_start717), "Configure")
	return result718
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs719 := [][]interface{}{}
	cond720 := p.matchLookaheadLiteral(":", 0)
	for cond720 {
		_t1426 := p.parse_config_key_value()
		item721 := _t1426
		xs719 = append(xs719, item721)
		cond720 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values722 := xs719
	p.consumeLiteral("}")
	return config_key_values722
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol723 := p.consumeTerminal("SYMBOL").Value.str
	_t1427 := p.parse_raw_value()
	raw_value724 := _t1427
	return []interface{}{symbol723, raw_value724}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start738 := int64(p.spanStart())
	var _t1428 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1428 = 12
	} else {
		var _t1429 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1429 = 11
		} else {
			var _t1430 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1430 = 12
			} else {
				var _t1431 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1432 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1432 = 1
					} else {
						var _t1433 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1433 = 0
						} else {
							_t1433 = -1
						}
						_t1432 = _t1433
					}
					_t1431 = _t1432
				} else {
					var _t1434 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1434 = 7
					} else {
						var _t1435 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1435 = 8
						} else {
							var _t1436 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1436 = 2
							} else {
								var _t1437 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1437 = 3
								} else {
									var _t1438 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1438 = 9
									} else {
										var _t1439 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1439 = 4
										} else {
											var _t1440 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1440 = 5
											} else {
												var _t1441 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1441 = 6
												} else {
													var _t1442 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1442 = 10
													} else {
														_t1442 = -1
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
					_t1431 = _t1434
				}
				_t1430 = _t1431
			}
			_t1429 = _t1430
		}
		_t1428 = _t1429
	}
	prediction725 := _t1428
	var _t1443 *pb.Value
	if prediction725 == 12 {
		_t1444 := p.parse_boolean_value()
		boolean_value737 := _t1444
		_t1445 := &pb.Value{}
		_t1445.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value737}
		_t1443 = _t1445
	} else {
		var _t1446 *pb.Value
		if prediction725 == 11 {
			p.consumeLiteral("missing")
			_t1447 := &pb.MissingValue{}
			_t1448 := &pb.Value{}
			_t1448.Value = &pb.Value_MissingValue{MissingValue: _t1447}
			_t1446 = _t1448
		} else {
			var _t1449 *pb.Value
			if prediction725 == 10 {
				decimal736 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1450 := &pb.Value{}
				_t1450.Value = &pb.Value_DecimalValue{DecimalValue: decimal736}
				_t1449 = _t1450
			} else {
				var _t1451 *pb.Value
				if prediction725 == 9 {
					int128735 := p.consumeTerminal("INT128").Value.int128
					_t1452 := &pb.Value{}
					_t1452.Value = &pb.Value_Int128Value{Int128Value: int128735}
					_t1451 = _t1452
				} else {
					var _t1453 *pb.Value
					if prediction725 == 8 {
						uint128734 := p.consumeTerminal("UINT128").Value.uint128
						_t1454 := &pb.Value{}
						_t1454.Value = &pb.Value_Uint128Value{Uint128Value: uint128734}
						_t1453 = _t1454
					} else {
						var _t1455 *pb.Value
						if prediction725 == 7 {
							uint32733 := p.consumeTerminal("UINT32").Value.u32
							_t1456 := &pb.Value{}
							_t1456.Value = &pb.Value_Uint32Value{Uint32Value: uint32733}
							_t1455 = _t1456
						} else {
							var _t1457 *pb.Value
							if prediction725 == 6 {
								float732 := p.consumeTerminal("FLOAT").Value.f64
								_t1458 := &pb.Value{}
								_t1458.Value = &pb.Value_FloatValue{FloatValue: float732}
								_t1457 = _t1458
							} else {
								var _t1459 *pb.Value
								if prediction725 == 5 {
									float32731 := p.consumeTerminal("FLOAT32").Value.f32
									_t1460 := &pb.Value{}
									_t1460.Value = &pb.Value_Float32Value{Float32Value: float32731}
									_t1459 = _t1460
								} else {
									var _t1461 *pb.Value
									if prediction725 == 4 {
										int730 := p.consumeTerminal("INT").Value.i64
										_t1462 := &pb.Value{}
										_t1462.Value = &pb.Value_IntValue{IntValue: int730}
										_t1461 = _t1462
									} else {
										var _t1463 *pb.Value
										if prediction725 == 3 {
											int32729 := p.consumeTerminal("INT32").Value.i32
											_t1464 := &pb.Value{}
											_t1464.Value = &pb.Value_Int32Value{Int32Value: int32729}
											_t1463 = _t1464
										} else {
											var _t1465 *pb.Value
											if prediction725 == 2 {
												string728 := p.consumeTerminal("STRING").Value.str
												_t1466 := &pb.Value{}
												_t1466.Value = &pb.Value_StringValue{StringValue: string728}
												_t1465 = _t1466
											} else {
												var _t1467 *pb.Value
												if prediction725 == 1 {
													_t1468 := p.parse_raw_datetime()
													raw_datetime727 := _t1468
													_t1469 := &pb.Value{}
													_t1469.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime727}
													_t1467 = _t1469
												} else {
													var _t1470 *pb.Value
													if prediction725 == 0 {
														_t1471 := p.parse_raw_date()
														raw_date726 := _t1471
														_t1472 := &pb.Value{}
														_t1472.Value = &pb.Value_DateValue{DateValue: raw_date726}
														_t1470 = _t1472
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1467 = _t1470
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
							_t1455 = _t1457
						}
						_t1453 = _t1455
					}
					_t1451 = _t1453
				}
				_t1449 = _t1451
			}
			_t1446 = _t1449
		}
		_t1443 = _t1446
	}
	result739 := _t1443
	p.recordSpan(int(span_start738), "Value")
	return result739
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int740 := p.consumeTerminal("INT").Value.i64
	int_3741 := p.consumeTerminal("INT").Value.i64
	int_4742 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1473 := &pb.DateValue{Year: int32(int740), Month: int32(int_3741), Day: int32(int_4742)}
	result744 := _t1473
	p.recordSpan(int(span_start743), "DateValue")
	return result744
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int745 := p.consumeTerminal("INT").Value.i64
	int_3746 := p.consumeTerminal("INT").Value.i64
	int_4747 := p.consumeTerminal("INT").Value.i64
	int_5748 := p.consumeTerminal("INT").Value.i64
	int_6749 := p.consumeTerminal("INT").Value.i64
	int_7750 := p.consumeTerminal("INT").Value.i64
	var _t1474 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1474 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8751 := _t1474
	p.consumeLiteral(")")
	_t1475 := &pb.DateTimeValue{Year: int32(int745), Month: int32(int_3746), Day: int32(int_4747), Hour: int32(int_5748), Minute: int32(int_6749), Second: int32(int_7750), Microsecond: int32(deref(int_8751, 0))}
	result753 := _t1475
	p.recordSpan(int(span_start752), "DateTimeValue")
	return result753
}

func (p *Parser) parse_boolean_value() bool {
	var _t1476 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1476 = 0
	} else {
		var _t1477 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1477 = 1
		} else {
			_t1477 = -1
		}
		_t1476 = _t1477
	}
	prediction754 := _t1476
	var _t1478 bool
	if prediction754 == 1 {
		p.consumeLiteral("false")
		_t1478 = false
	} else {
		var _t1479 bool
		if prediction754 == 0 {
			p.consumeLiteral("true")
			_t1479 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1478 = _t1479
	}
	return _t1478
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs755 := []*pb.FragmentId{}
	cond756 := p.matchLookaheadLiteral(":", 0)
	for cond756 {
		_t1480 := p.parse_fragment_id()
		item757 := _t1480
		xs755 = append(xs755, item757)
		cond756 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids758 := xs755
	p.consumeLiteral(")")
	_t1481 := &pb.Sync{Fragments: fragment_ids758}
	result760 := _t1481
	p.recordSpan(int(span_start759), "Sync")
	return result760
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start762 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol761 := p.consumeTerminal("SYMBOL").Value.str
	result763 := &pb.FragmentId{Id: []byte(symbol761)}
	p.recordSpan(int(span_start762), "FragmentId")
	return result763
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start766 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1482 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1483 := p.parse_epoch_writes()
		_t1482 = _t1483
	}
	epoch_writes764 := _t1482
	var _t1484 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1485 := p.parse_epoch_reads()
		_t1484 = _t1485
	}
	epoch_reads765 := _t1484
	p.consumeLiteral(")")
	_t1486 := epoch_writes764
	if epoch_writes764 == nil {
		_t1486 = []*pb.Write{}
	}
	_t1487 := epoch_reads765
	if epoch_reads765 == nil {
		_t1487 = []*pb.Read{}
	}
	_t1488 := &pb.Epoch{Writes: _t1486, Reads: _t1487}
	result767 := _t1488
	p.recordSpan(int(span_start766), "Epoch")
	return result767
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs768 := []*pb.Write{}
	cond769 := p.matchLookaheadLiteral("(", 0)
	for cond769 {
		_t1489 := p.parse_write()
		item770 := _t1489
		xs768 = append(xs768, item770)
		cond769 = p.matchLookaheadLiteral("(", 0)
	}
	writes771 := xs768
	p.consumeLiteral(")")
	return writes771
}

func (p *Parser) parse_write() *pb.Write {
	span_start777 := int64(p.spanStart())
	var _t1490 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1491 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1491 = 1
		} else {
			var _t1492 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1492 = 3
			} else {
				var _t1493 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1493 = 0
				} else {
					var _t1494 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1494 = 2
					} else {
						_t1494 = -1
					}
					_t1493 = _t1494
				}
				_t1492 = _t1493
			}
			_t1491 = _t1492
		}
		_t1490 = _t1491
	} else {
		_t1490 = -1
	}
	prediction772 := _t1490
	var _t1495 *pb.Write
	if prediction772 == 3 {
		_t1496 := p.parse_snapshot()
		snapshot776 := _t1496
		_t1497 := &pb.Write{}
		_t1497.WriteType = &pb.Write_Snapshot{Snapshot: snapshot776}
		_t1495 = _t1497
	} else {
		var _t1498 *pb.Write
		if prediction772 == 2 {
			_t1499 := p.parse_context()
			context775 := _t1499
			_t1500 := &pb.Write{}
			_t1500.WriteType = &pb.Write_Context{Context: context775}
			_t1498 = _t1500
		} else {
			var _t1501 *pb.Write
			if prediction772 == 1 {
				_t1502 := p.parse_undefine()
				undefine774 := _t1502
				_t1503 := &pb.Write{}
				_t1503.WriteType = &pb.Write_Undefine{Undefine: undefine774}
				_t1501 = _t1503
			} else {
				var _t1504 *pb.Write
				if prediction772 == 0 {
					_t1505 := p.parse_define()
					define773 := _t1505
					_t1506 := &pb.Write{}
					_t1506.WriteType = &pb.Write_Define{Define: define773}
					_t1504 = _t1506
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1501 = _t1504
			}
			_t1498 = _t1501
		}
		_t1495 = _t1498
	}
	result778 := _t1495
	p.recordSpan(int(span_start777), "Write")
	return result778
}

func (p *Parser) parse_define() *pb.Define {
	span_start780 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1507 := p.parse_fragment()
	fragment779 := _t1507
	p.consumeLiteral(")")
	_t1508 := &pb.Define{Fragment: fragment779}
	result781 := _t1508
	p.recordSpan(int(span_start780), "Define")
	return result781
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start787 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1509 := p.parse_new_fragment_id()
	new_fragment_id782 := _t1509
	xs783 := []*pb.Declaration{}
	cond784 := p.matchLookaheadLiteral("(", 0)
	for cond784 {
		_t1510 := p.parse_declaration()
		item785 := _t1510
		xs783 = append(xs783, item785)
		cond784 = p.matchLookaheadLiteral("(", 0)
	}
	declarations786 := xs783
	p.consumeLiteral(")")
	result788 := p.constructFragment(new_fragment_id782, declarations786)
	p.recordSpan(int(span_start787), "Fragment")
	return result788
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start790 := int64(p.spanStart())
	_t1511 := p.parse_fragment_id()
	fragment_id789 := _t1511
	p.startFragment(fragment_id789)
	result791 := fragment_id789
	p.recordSpan(int(span_start790), "FragmentId")
	return result791
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start797 := int64(p.spanStart())
	var _t1512 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1513 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1513 = 3
		} else {
			var _t1514 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1514 = 2
			} else {
				var _t1515 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1515 = 3
				} else {
					var _t1516 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1516 = 0
					} else {
						var _t1517 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1517 = 3
						} else {
							var _t1518 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1518 = 3
							} else {
								var _t1519 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1519 = 1
								} else {
									_t1519 = -1
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
			_t1513 = _t1514
		}
		_t1512 = _t1513
	} else {
		_t1512 = -1
	}
	prediction792 := _t1512
	var _t1520 *pb.Declaration
	if prediction792 == 3 {
		_t1521 := p.parse_data()
		data796 := _t1521
		_t1522 := &pb.Declaration{}
		_t1522.DeclarationType = &pb.Declaration_Data{Data: data796}
		_t1520 = _t1522
	} else {
		var _t1523 *pb.Declaration
		if prediction792 == 2 {
			_t1524 := p.parse_constraint()
			constraint795 := _t1524
			_t1525 := &pb.Declaration{}
			_t1525.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint795}
			_t1523 = _t1525
		} else {
			var _t1526 *pb.Declaration
			if prediction792 == 1 {
				_t1527 := p.parse_algorithm()
				algorithm794 := _t1527
				_t1528 := &pb.Declaration{}
				_t1528.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm794}
				_t1526 = _t1528
			} else {
				var _t1529 *pb.Declaration
				if prediction792 == 0 {
					_t1530 := p.parse_def()
					def793 := _t1530
					_t1531 := &pb.Declaration{}
					_t1531.DeclarationType = &pb.Declaration_Def{Def: def793}
					_t1529 = _t1531
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1526 = _t1529
			}
			_t1523 = _t1526
		}
		_t1520 = _t1523
	}
	result798 := _t1520
	p.recordSpan(int(span_start797), "Declaration")
	return result798
}

func (p *Parser) parse_def() *pb.Def {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1532 := p.parse_relation_id()
	relation_id799 := _t1532
	_t1533 := p.parse_abstraction()
	abstraction800 := _t1533
	var _t1534 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1535 := p.parse_attrs()
		_t1534 = _t1535
	}
	attrs801 := _t1534
	p.consumeLiteral(")")
	_t1536 := attrs801
	if attrs801 == nil {
		_t1536 = []*pb.Attribute{}
	}
	_t1537 := &pb.Def{Name: relation_id799, Body: abstraction800, Attrs: _t1536}
	result803 := _t1537
	p.recordSpan(int(span_start802), "Def")
	return result803
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start807 := int64(p.spanStart())
	var _t1538 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1538 = 0
	} else {
		var _t1539 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1539 = 1
		} else {
			_t1539 = -1
		}
		_t1538 = _t1539
	}
	prediction804 := _t1538
	var _t1540 *pb.RelationId
	if prediction804 == 1 {
		uint128806 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128806
		_t1540 = &pb.RelationId{IdLow: uint128806.Low, IdHigh: uint128806.High}
	} else {
		var _t1541 *pb.RelationId
		if prediction804 == 0 {
			p.consumeLiteral(":")
			symbol805 := p.consumeTerminal("SYMBOL").Value.str
			_t1541 = p.relationIdFromString(symbol805)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1540 = _t1541
	}
	result808 := _t1540
	p.recordSpan(int(span_start807), "RelationId")
	return result808
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1542 := p.parse_bindings()
	bindings809 := _t1542
	_t1543 := p.parse_formula()
	formula810 := _t1543
	p.consumeLiteral(")")
	_t1544 := &pb.Abstraction{Vars: listConcat(bindings809[0].([]*pb.Binding), bindings809[1].([]*pb.Binding)), Value: formula810}
	result812 := _t1544
	p.recordSpan(int(span_start811), "Abstraction")
	return result812
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs813 := []*pb.Binding{}
	cond814 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond814 {
		_t1545 := p.parse_binding()
		item815 := _t1545
		xs813 = append(xs813, item815)
		cond814 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings816 := xs813
	var _t1546 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1547 := p.parse_value_bindings()
		_t1546 = _t1547
	}
	value_bindings817 := _t1546
	p.consumeLiteral("]")
	_t1548 := value_bindings817
	if value_bindings817 == nil {
		_t1548 = []*pb.Binding{}
	}
	return []interface{}{bindings816, _t1548}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start820 := int64(p.spanStart())
	symbol818 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1549 := p.parse_type()
	type819 := _t1549
	_t1550 := &pb.Var{Name: symbol818}
	_t1551 := &pb.Binding{Var: _t1550, Type: type819}
	result821 := _t1551
	p.recordSpan(int(span_start820), "Binding")
	return result821
}

func (p *Parser) parse_type() *pb.Type {
	span_start837 := int64(p.spanStart())
	var _t1552 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1552 = 0
	} else {
		var _t1553 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1553 = 13
		} else {
			var _t1554 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1554 = 4
			} else {
				var _t1555 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1555 = 1
				} else {
					var _t1556 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1556 = 8
					} else {
						var _t1557 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1557 = 11
						} else {
							var _t1558 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1558 = 5
							} else {
								var _t1559 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1559 = 2
								} else {
									var _t1560 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1560 = 12
									} else {
										var _t1561 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1561 = 3
										} else {
											var _t1562 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1562 = 7
											} else {
												var _t1563 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1563 = 6
												} else {
													var _t1564 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1564 = 10
													} else {
														var _t1565 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1565 = 9
														} else {
															_t1565 = -1
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
	prediction822 := _t1552
	var _t1566 *pb.Type
	if prediction822 == 13 {
		_t1567 := p.parse_uint32_type()
		uint32_type836 := _t1567
		_t1568 := &pb.Type{}
		_t1568.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type836}
		_t1566 = _t1568
	} else {
		var _t1569 *pb.Type
		if prediction822 == 12 {
			_t1570 := p.parse_float32_type()
			float32_type835 := _t1570
			_t1571 := &pb.Type{}
			_t1571.Type = &pb.Type_Float32Type{Float32Type: float32_type835}
			_t1569 = _t1571
		} else {
			var _t1572 *pb.Type
			if prediction822 == 11 {
				_t1573 := p.parse_int32_type()
				int32_type834 := _t1573
				_t1574 := &pb.Type{}
				_t1574.Type = &pb.Type_Int32Type{Int32Type: int32_type834}
				_t1572 = _t1574
			} else {
				var _t1575 *pb.Type
				if prediction822 == 10 {
					_t1576 := p.parse_boolean_type()
					boolean_type833 := _t1576
					_t1577 := &pb.Type{}
					_t1577.Type = &pb.Type_BooleanType{BooleanType: boolean_type833}
					_t1575 = _t1577
				} else {
					var _t1578 *pb.Type
					if prediction822 == 9 {
						_t1579 := p.parse_decimal_type()
						decimal_type832 := _t1579
						_t1580 := &pb.Type{}
						_t1580.Type = &pb.Type_DecimalType{DecimalType: decimal_type832}
						_t1578 = _t1580
					} else {
						var _t1581 *pb.Type
						if prediction822 == 8 {
							_t1582 := p.parse_missing_type()
							missing_type831 := _t1582
							_t1583 := &pb.Type{}
							_t1583.Type = &pb.Type_MissingType{MissingType: missing_type831}
							_t1581 = _t1583
						} else {
							var _t1584 *pb.Type
							if prediction822 == 7 {
								_t1585 := p.parse_datetime_type()
								datetime_type830 := _t1585
								_t1586 := &pb.Type{}
								_t1586.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type830}
								_t1584 = _t1586
							} else {
								var _t1587 *pb.Type
								if prediction822 == 6 {
									_t1588 := p.parse_date_type()
									date_type829 := _t1588
									_t1589 := &pb.Type{}
									_t1589.Type = &pb.Type_DateType{DateType: date_type829}
									_t1587 = _t1589
								} else {
									var _t1590 *pb.Type
									if prediction822 == 5 {
										_t1591 := p.parse_int128_type()
										int128_type828 := _t1591
										_t1592 := &pb.Type{}
										_t1592.Type = &pb.Type_Int128Type{Int128Type: int128_type828}
										_t1590 = _t1592
									} else {
										var _t1593 *pb.Type
										if prediction822 == 4 {
											_t1594 := p.parse_uint128_type()
											uint128_type827 := _t1594
											_t1595 := &pb.Type{}
											_t1595.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type827}
											_t1593 = _t1595
										} else {
											var _t1596 *pb.Type
											if prediction822 == 3 {
												_t1597 := p.parse_float_type()
												float_type826 := _t1597
												_t1598 := &pb.Type{}
												_t1598.Type = &pb.Type_FloatType{FloatType: float_type826}
												_t1596 = _t1598
											} else {
												var _t1599 *pb.Type
												if prediction822 == 2 {
													_t1600 := p.parse_int_type()
													int_type825 := _t1600
													_t1601 := &pb.Type{}
													_t1601.Type = &pb.Type_IntType{IntType: int_type825}
													_t1599 = _t1601
												} else {
													var _t1602 *pb.Type
													if prediction822 == 1 {
														_t1603 := p.parse_string_type()
														string_type824 := _t1603
														_t1604 := &pb.Type{}
														_t1604.Type = &pb.Type_StringType{StringType: string_type824}
														_t1602 = _t1604
													} else {
														var _t1605 *pb.Type
														if prediction822 == 0 {
															_t1606 := p.parse_unspecified_type()
															unspecified_type823 := _t1606
															_t1607 := &pb.Type{}
															_t1607.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type823}
															_t1605 = _t1607
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
							_t1581 = _t1584
						}
						_t1578 = _t1581
					}
					_t1575 = _t1578
				}
				_t1572 = _t1575
			}
			_t1569 = _t1572
		}
		_t1566 = _t1569
	}
	result838 := _t1566
	p.recordSpan(int(span_start837), "Type")
	return result838
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1608 := &pb.UnspecifiedType{}
	result840 := _t1608
	p.recordSpan(int(span_start839), "UnspecifiedType")
	return result840
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1609 := &pb.StringType{}
	result842 := _t1609
	p.recordSpan(int(span_start841), "StringType")
	return result842
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1610 := &pb.IntType{}
	result844 := _t1610
	p.recordSpan(int(span_start843), "IntType")
	return result844
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1611 := &pb.FloatType{}
	result846 := _t1611
	p.recordSpan(int(span_start845), "FloatType")
	return result846
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1612 := &pb.UInt128Type{}
	result848 := _t1612
	p.recordSpan(int(span_start847), "UInt128Type")
	return result848
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1613 := &pb.Int128Type{}
	result850 := _t1613
	p.recordSpan(int(span_start849), "Int128Type")
	return result850
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1614 := &pb.DateType{}
	result852 := _t1614
	p.recordSpan(int(span_start851), "DateType")
	return result852
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1615 := &pb.DateTimeType{}
	result854 := _t1615
	p.recordSpan(int(span_start853), "DateTimeType")
	return result854
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1616 := &pb.MissingType{}
	result856 := _t1616
	p.recordSpan(int(span_start855), "MissingType")
	return result856
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int857 := p.consumeTerminal("INT").Value.i64
	int_3858 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1617 := &pb.DecimalType{Precision: int32(int857), Scale: int32(int_3858)}
	result860 := _t1617
	p.recordSpan(int(span_start859), "DecimalType")
	return result860
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1618 := &pb.BooleanType{}
	result862 := _t1618
	p.recordSpan(int(span_start861), "BooleanType")
	return result862
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1619 := &pb.Int32Type{}
	result864 := _t1619
	p.recordSpan(int(span_start863), "Int32Type")
	return result864
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1620 := &pb.Float32Type{}
	result866 := _t1620
	p.recordSpan(int(span_start865), "Float32Type")
	return result866
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start867 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1621 := &pb.UInt32Type{}
	result868 := _t1621
	p.recordSpan(int(span_start867), "UInt32Type")
	return result868
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs869 := []*pb.Binding{}
	cond870 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond870 {
		_t1622 := p.parse_binding()
		item871 := _t1622
		xs869 = append(xs869, item871)
		cond870 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings872 := xs869
	return bindings872
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start887 := int64(p.spanStart())
	var _t1623 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1624 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1624 = 0
		} else {
			var _t1625 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1625 = 11
			} else {
				var _t1626 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1626 = 3
				} else {
					var _t1627 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1627 = 10
					} else {
						var _t1628 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1628 = 9
						} else {
							var _t1629 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1629 = 5
							} else {
								var _t1630 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1630 = 6
								} else {
									var _t1631 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1631 = 7
									} else {
										var _t1632 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1632 = 1
										} else {
											var _t1633 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1633 = 2
											} else {
												var _t1634 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1634 = 12
												} else {
													var _t1635 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1635 = 8
													} else {
														var _t1636 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1636 = 4
														} else {
															var _t1637 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1637 = 10
															} else {
																var _t1638 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1638 = 10
																} else {
																	var _t1639 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1639 = 10
																	} else {
																		var _t1640 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1640 = 10
																		} else {
																			var _t1641 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1641 = 10
																			} else {
																				var _t1642 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1642 = 10
																				} else {
																					var _t1643 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1643 = 10
																					} else {
																						var _t1644 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1644 = 10
																						} else {
																							var _t1645 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1645 = 10
																							} else {
																								_t1645 = -1
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
	} else {
		_t1623 = -1
	}
	prediction873 := _t1623
	var _t1646 *pb.Formula
	if prediction873 == 12 {
		_t1647 := p.parse_cast()
		cast886 := _t1647
		_t1648 := &pb.Formula{}
		_t1648.FormulaType = &pb.Formula_Cast{Cast: cast886}
		_t1646 = _t1648
	} else {
		var _t1649 *pb.Formula
		if prediction873 == 11 {
			_t1650 := p.parse_rel_atom()
			rel_atom885 := _t1650
			_t1651 := &pb.Formula{}
			_t1651.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom885}
			_t1649 = _t1651
		} else {
			var _t1652 *pb.Formula
			if prediction873 == 10 {
				_t1653 := p.parse_primitive()
				primitive884 := _t1653
				_t1654 := &pb.Formula{}
				_t1654.FormulaType = &pb.Formula_Primitive{Primitive: primitive884}
				_t1652 = _t1654
			} else {
				var _t1655 *pb.Formula
				if prediction873 == 9 {
					_t1656 := p.parse_pragma()
					pragma883 := _t1656
					_t1657 := &pb.Formula{}
					_t1657.FormulaType = &pb.Formula_Pragma{Pragma: pragma883}
					_t1655 = _t1657
				} else {
					var _t1658 *pb.Formula
					if prediction873 == 8 {
						_t1659 := p.parse_atom()
						atom882 := _t1659
						_t1660 := &pb.Formula{}
						_t1660.FormulaType = &pb.Formula_Atom{Atom: atom882}
						_t1658 = _t1660
					} else {
						var _t1661 *pb.Formula
						if prediction873 == 7 {
							_t1662 := p.parse_ffi()
							ffi881 := _t1662
							_t1663 := &pb.Formula{}
							_t1663.FormulaType = &pb.Formula_Ffi{Ffi: ffi881}
							_t1661 = _t1663
						} else {
							var _t1664 *pb.Formula
							if prediction873 == 6 {
								_t1665 := p.parse_not()
								not880 := _t1665
								_t1666 := &pb.Formula{}
								_t1666.FormulaType = &pb.Formula_Not{Not: not880}
								_t1664 = _t1666
							} else {
								var _t1667 *pb.Formula
								if prediction873 == 5 {
									_t1668 := p.parse_disjunction()
									disjunction879 := _t1668
									_t1669 := &pb.Formula{}
									_t1669.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction879}
									_t1667 = _t1669
								} else {
									var _t1670 *pb.Formula
									if prediction873 == 4 {
										_t1671 := p.parse_conjunction()
										conjunction878 := _t1671
										_t1672 := &pb.Formula{}
										_t1672.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction878}
										_t1670 = _t1672
									} else {
										var _t1673 *pb.Formula
										if prediction873 == 3 {
											_t1674 := p.parse_reduce()
											reduce877 := _t1674
											_t1675 := &pb.Formula{}
											_t1675.FormulaType = &pb.Formula_Reduce{Reduce: reduce877}
											_t1673 = _t1675
										} else {
											var _t1676 *pb.Formula
											if prediction873 == 2 {
												_t1677 := p.parse_exists()
												exists876 := _t1677
												_t1678 := &pb.Formula{}
												_t1678.FormulaType = &pb.Formula_Exists{Exists: exists876}
												_t1676 = _t1678
											} else {
												var _t1679 *pb.Formula
												if prediction873 == 1 {
													_t1680 := p.parse_false()
													false875 := _t1680
													_t1681 := &pb.Formula{}
													_t1681.FormulaType = &pb.Formula_Disjunction{Disjunction: false875}
													_t1679 = _t1681
												} else {
													var _t1682 *pb.Formula
													if prediction873 == 0 {
														_t1683 := p.parse_true()
														true874 := _t1683
														_t1684 := &pb.Formula{}
														_t1684.FormulaType = &pb.Formula_Conjunction{Conjunction: true874}
														_t1682 = _t1684
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1679 = _t1682
												}
												_t1676 = _t1679
											}
											_t1673 = _t1676
										}
										_t1670 = _t1673
									}
									_t1667 = _t1670
								}
								_t1664 = _t1667
							}
							_t1661 = _t1664
						}
						_t1658 = _t1661
					}
					_t1655 = _t1658
				}
				_t1652 = _t1655
			}
			_t1649 = _t1652
		}
		_t1646 = _t1649
	}
	result888 := _t1646
	p.recordSpan(int(span_start887), "Formula")
	return result888
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start889 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1685 := &pb.Conjunction{Args: []*pb.Formula{}}
	result890 := _t1685
	p.recordSpan(int(span_start889), "Conjunction")
	return result890
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1686 := &pb.Disjunction{Args: []*pb.Formula{}}
	result892 := _t1686
	p.recordSpan(int(span_start891), "Disjunction")
	return result892
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1687 := p.parse_bindings()
	bindings893 := _t1687
	_t1688 := p.parse_formula()
	formula894 := _t1688
	p.consumeLiteral(")")
	_t1689 := &pb.Abstraction{Vars: listConcat(bindings893[0].([]*pb.Binding), bindings893[1].([]*pb.Binding)), Value: formula894}
	_t1690 := &pb.Exists{Body: _t1689}
	result896 := _t1690
	p.recordSpan(int(span_start895), "Exists")
	return result896
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1691 := p.parse_abstraction()
	abstraction897 := _t1691
	_t1692 := p.parse_abstraction()
	abstraction_3898 := _t1692
	_t1693 := p.parse_terms()
	terms899 := _t1693
	p.consumeLiteral(")")
	_t1694 := &pb.Reduce{Op: abstraction897, Body: abstraction_3898, Terms: terms899}
	result901 := _t1694
	p.recordSpan(int(span_start900), "Reduce")
	return result901
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs902 := []*pb.Term{}
	cond903 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond903 {
		_t1695 := p.parse_term()
		item904 := _t1695
		xs902 = append(xs902, item904)
		cond903 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms905 := xs902
	p.consumeLiteral(")")
	return terms905
}

func (p *Parser) parse_term() *pb.Term {
	span_start909 := int64(p.spanStart())
	var _t1696 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1696 = 1
	} else {
		var _t1697 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1697 = 1
		} else {
			var _t1698 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1698 = 1
			} else {
				var _t1699 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1699 = 1
				} else {
					var _t1700 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1700 = 0
					} else {
						var _t1701 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1701 = 1
						} else {
							var _t1702 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1702 = 1
							} else {
								var _t1703 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1703 = 1
								} else {
									var _t1704 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1704 = 1
									} else {
										var _t1705 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1705 = 1
										} else {
											var _t1706 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1706 = 1
											} else {
												var _t1707 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1707 = 1
												} else {
													var _t1708 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1708 = 1
													} else {
														var _t1709 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1709 = 1
														} else {
															_t1709 = -1
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
	prediction906 := _t1696
	var _t1710 *pb.Term
	if prediction906 == 1 {
		_t1711 := p.parse_value()
		value908 := _t1711
		_t1712 := &pb.Term{}
		_t1712.TermType = &pb.Term_Constant{Constant: value908}
		_t1710 = _t1712
	} else {
		var _t1713 *pb.Term
		if prediction906 == 0 {
			_t1714 := p.parse_var()
			var907 := _t1714
			_t1715 := &pb.Term{}
			_t1715.TermType = &pb.Term_Var{Var: var907}
			_t1713 = _t1715
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1710 = _t1713
	}
	result910 := _t1710
	p.recordSpan(int(span_start909), "Term")
	return result910
}

func (p *Parser) parse_var() *pb.Var {
	span_start912 := int64(p.spanStart())
	symbol911 := p.consumeTerminal("SYMBOL").Value.str
	_t1716 := &pb.Var{Name: symbol911}
	result913 := _t1716
	p.recordSpan(int(span_start912), "Var")
	return result913
}

func (p *Parser) parse_value() *pb.Value {
	span_start927 := int64(p.spanStart())
	var _t1717 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1717 = 12
	} else {
		var _t1718 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1718 = 11
		} else {
			var _t1719 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1719 = 12
			} else {
				var _t1720 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1721 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1721 = 1
					} else {
						var _t1722 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1722 = 0
						} else {
							_t1722 = -1
						}
						_t1721 = _t1722
					}
					_t1720 = _t1721
				} else {
					var _t1723 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1723 = 7
					} else {
						var _t1724 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1724 = 8
						} else {
							var _t1725 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1725 = 2
							} else {
								var _t1726 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1726 = 3
								} else {
									var _t1727 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1727 = 9
									} else {
										var _t1728 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1728 = 4
										} else {
											var _t1729 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1729 = 5
											} else {
												var _t1730 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1730 = 6
												} else {
													var _t1731 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1731 = 10
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
					_t1720 = _t1723
				}
				_t1719 = _t1720
			}
			_t1718 = _t1719
		}
		_t1717 = _t1718
	}
	prediction914 := _t1717
	var _t1732 *pb.Value
	if prediction914 == 12 {
		_t1733 := p.parse_boolean_value()
		boolean_value926 := _t1733
		_t1734 := &pb.Value{}
		_t1734.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value926}
		_t1732 = _t1734
	} else {
		var _t1735 *pb.Value
		if prediction914 == 11 {
			p.consumeLiteral("missing")
			_t1736 := &pb.MissingValue{}
			_t1737 := &pb.Value{}
			_t1737.Value = &pb.Value_MissingValue{MissingValue: _t1736}
			_t1735 = _t1737
		} else {
			var _t1738 *pb.Value
			if prediction914 == 10 {
				formatted_decimal925 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1739 := &pb.Value{}
				_t1739.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal925}
				_t1738 = _t1739
			} else {
				var _t1740 *pb.Value
				if prediction914 == 9 {
					formatted_int128924 := p.consumeTerminal("INT128").Value.int128
					_t1741 := &pb.Value{}
					_t1741.Value = &pb.Value_Int128Value{Int128Value: formatted_int128924}
					_t1740 = _t1741
				} else {
					var _t1742 *pb.Value
					if prediction914 == 8 {
						formatted_uint128923 := p.consumeTerminal("UINT128").Value.uint128
						_t1743 := &pb.Value{}
						_t1743.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128923}
						_t1742 = _t1743
					} else {
						var _t1744 *pb.Value
						if prediction914 == 7 {
							formatted_uint32922 := p.consumeTerminal("UINT32").Value.u32
							_t1745 := &pb.Value{}
							_t1745.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32922}
							_t1744 = _t1745
						} else {
							var _t1746 *pb.Value
							if prediction914 == 6 {
								formatted_float921 := p.consumeTerminal("FLOAT").Value.f64
								_t1747 := &pb.Value{}
								_t1747.Value = &pb.Value_FloatValue{FloatValue: formatted_float921}
								_t1746 = _t1747
							} else {
								var _t1748 *pb.Value
								if prediction914 == 5 {
									formatted_float32920 := p.consumeTerminal("FLOAT32").Value.f32
									_t1749 := &pb.Value{}
									_t1749.Value = &pb.Value_Float32Value{Float32Value: formatted_float32920}
									_t1748 = _t1749
								} else {
									var _t1750 *pb.Value
									if prediction914 == 4 {
										formatted_int919 := p.consumeTerminal("INT").Value.i64
										_t1751 := &pb.Value{}
										_t1751.Value = &pb.Value_IntValue{IntValue: formatted_int919}
										_t1750 = _t1751
									} else {
										var _t1752 *pb.Value
										if prediction914 == 3 {
											formatted_int32918 := p.consumeTerminal("INT32").Value.i32
											_t1753 := &pb.Value{}
											_t1753.Value = &pb.Value_Int32Value{Int32Value: formatted_int32918}
											_t1752 = _t1753
										} else {
											var _t1754 *pb.Value
											if prediction914 == 2 {
												formatted_string917 := p.consumeTerminal("STRING").Value.str
												_t1755 := &pb.Value{}
												_t1755.Value = &pb.Value_StringValue{StringValue: formatted_string917}
												_t1754 = _t1755
											} else {
												var _t1756 *pb.Value
												if prediction914 == 1 {
													_t1757 := p.parse_datetime()
													datetime916 := _t1757
													_t1758 := &pb.Value{}
													_t1758.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime916}
													_t1756 = _t1758
												} else {
													var _t1759 *pb.Value
													if prediction914 == 0 {
														_t1760 := p.parse_date()
														date915 := _t1760
														_t1761 := &pb.Value{}
														_t1761.Value = &pb.Value_DateValue{DateValue: date915}
														_t1759 = _t1761
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1756 = _t1759
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
							_t1744 = _t1746
						}
						_t1742 = _t1744
					}
					_t1740 = _t1742
				}
				_t1738 = _t1740
			}
			_t1735 = _t1738
		}
		_t1732 = _t1735
	}
	result928 := _t1732
	p.recordSpan(int(span_start927), "Value")
	return result928
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start932 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int929 := p.consumeTerminal("INT").Value.i64
	formatted_int_3930 := p.consumeTerminal("INT").Value.i64
	formatted_int_4931 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1762 := &pb.DateValue{Year: int32(formatted_int929), Month: int32(formatted_int_3930), Day: int32(formatted_int_4931)}
	result933 := _t1762
	p.recordSpan(int(span_start932), "DateValue")
	return result933
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start941 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int934 := p.consumeTerminal("INT").Value.i64
	formatted_int_3935 := p.consumeTerminal("INT").Value.i64
	formatted_int_4936 := p.consumeTerminal("INT").Value.i64
	formatted_int_5937 := p.consumeTerminal("INT").Value.i64
	formatted_int_6938 := p.consumeTerminal("INT").Value.i64
	formatted_int_7939 := p.consumeTerminal("INT").Value.i64
	var _t1763 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1763 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8940 := _t1763
	p.consumeLiteral(")")
	_t1764 := &pb.DateTimeValue{Year: int32(formatted_int934), Month: int32(formatted_int_3935), Day: int32(formatted_int_4936), Hour: int32(formatted_int_5937), Minute: int32(formatted_int_6938), Second: int32(formatted_int_7939), Microsecond: int32(deref(formatted_int_8940, 0))}
	result942 := _t1764
	p.recordSpan(int(span_start941), "DateTimeValue")
	return result942
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start947 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs943 := []*pb.Formula{}
	cond944 := p.matchLookaheadLiteral("(", 0)
	for cond944 {
		_t1765 := p.parse_formula()
		item945 := _t1765
		xs943 = append(xs943, item945)
		cond944 = p.matchLookaheadLiteral("(", 0)
	}
	formulas946 := xs943
	p.consumeLiteral(")")
	_t1766 := &pb.Conjunction{Args: formulas946}
	result948 := _t1766
	p.recordSpan(int(span_start947), "Conjunction")
	return result948
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs949 := []*pb.Formula{}
	cond950 := p.matchLookaheadLiteral("(", 0)
	for cond950 {
		_t1767 := p.parse_formula()
		item951 := _t1767
		xs949 = append(xs949, item951)
		cond950 = p.matchLookaheadLiteral("(", 0)
	}
	formulas952 := xs949
	p.consumeLiteral(")")
	_t1768 := &pb.Disjunction{Args: formulas952}
	result954 := _t1768
	p.recordSpan(int(span_start953), "Disjunction")
	return result954
}

func (p *Parser) parse_not() *pb.Not {
	span_start956 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1769 := p.parse_formula()
	formula955 := _t1769
	p.consumeLiteral(")")
	_t1770 := &pb.Not{Arg: formula955}
	result957 := _t1770
	p.recordSpan(int(span_start956), "Not")
	return result957
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start961 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1771 := p.parse_name()
	name958 := _t1771
	_t1772 := p.parse_ffi_args()
	ffi_args959 := _t1772
	_t1773 := p.parse_terms()
	terms960 := _t1773
	p.consumeLiteral(")")
	_t1774 := &pb.FFI{Name: name958, Args: ffi_args959, Terms: terms960}
	result962 := _t1774
	p.recordSpan(int(span_start961), "FFI")
	return result962
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol963 := p.consumeTerminal("SYMBOL").Value.str
	return symbol963
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs964 := []*pb.Abstraction{}
	cond965 := p.matchLookaheadLiteral("(", 0)
	for cond965 {
		_t1775 := p.parse_abstraction()
		item966 := _t1775
		xs964 = append(xs964, item966)
		cond965 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions967 := xs964
	p.consumeLiteral(")")
	return abstractions967
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start973 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1776 := p.parse_relation_id()
	relation_id968 := _t1776
	xs969 := []*pb.Term{}
	cond970 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond970 {
		_t1777 := p.parse_term()
		item971 := _t1777
		xs969 = append(xs969, item971)
		cond970 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms972 := xs969
	p.consumeLiteral(")")
	_t1778 := &pb.Atom{Name: relation_id968, Terms: terms972}
	result974 := _t1778
	p.recordSpan(int(span_start973), "Atom")
	return result974
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1779 := p.parse_name()
	name975 := _t1779
	xs976 := []*pb.Term{}
	cond977 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond977 {
		_t1780 := p.parse_term()
		item978 := _t1780
		xs976 = append(xs976, item978)
		cond977 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms979 := xs976
	p.consumeLiteral(")")
	_t1781 := &pb.Pragma{Name: name975, Terms: terms979}
	result981 := _t1781
	p.recordSpan(int(span_start980), "Pragma")
	return result981
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start997 := int64(p.spanStart())
	var _t1782 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1783 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1783 = 9
		} else {
			var _t1784 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1784 = 4
			} else {
				var _t1785 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1785 = 3
				} else {
					var _t1786 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1786 = 0
					} else {
						var _t1787 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1787 = 2
						} else {
							var _t1788 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1788 = 1
							} else {
								var _t1789 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1789 = 8
								} else {
									var _t1790 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1790 = 6
									} else {
										var _t1791 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1791 = 5
										} else {
											var _t1792 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1792 = 7
											} else {
												_t1792 = -1
											}
											_t1791 = _t1792
										}
										_t1790 = _t1791
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
	} else {
		_t1782 = -1
	}
	prediction982 := _t1782
	var _t1793 *pb.Primitive
	if prediction982 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1794 := p.parse_name()
		name992 := _t1794
		xs993 := []*pb.RelTerm{}
		cond994 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond994 {
			_t1795 := p.parse_rel_term()
			item995 := _t1795
			xs993 = append(xs993, item995)
			cond994 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms996 := xs993
		p.consumeLiteral(")")
		_t1796 := &pb.Primitive{Name: name992, Terms: rel_terms996}
		_t1793 = _t1796
	} else {
		var _t1797 *pb.Primitive
		if prediction982 == 8 {
			_t1798 := p.parse_divide()
			divide991 := _t1798
			_t1797 = divide991
		} else {
			var _t1799 *pb.Primitive
			if prediction982 == 7 {
				_t1800 := p.parse_multiply()
				multiply990 := _t1800
				_t1799 = multiply990
			} else {
				var _t1801 *pb.Primitive
				if prediction982 == 6 {
					_t1802 := p.parse_minus()
					minus989 := _t1802
					_t1801 = minus989
				} else {
					var _t1803 *pb.Primitive
					if prediction982 == 5 {
						_t1804 := p.parse_add()
						add988 := _t1804
						_t1803 = add988
					} else {
						var _t1805 *pb.Primitive
						if prediction982 == 4 {
							_t1806 := p.parse_gt_eq()
							gt_eq987 := _t1806
							_t1805 = gt_eq987
						} else {
							var _t1807 *pb.Primitive
							if prediction982 == 3 {
								_t1808 := p.parse_gt()
								gt986 := _t1808
								_t1807 = gt986
							} else {
								var _t1809 *pb.Primitive
								if prediction982 == 2 {
									_t1810 := p.parse_lt_eq()
									lt_eq985 := _t1810
									_t1809 = lt_eq985
								} else {
									var _t1811 *pb.Primitive
									if prediction982 == 1 {
										_t1812 := p.parse_lt()
										lt984 := _t1812
										_t1811 = lt984
									} else {
										var _t1813 *pb.Primitive
										if prediction982 == 0 {
											_t1814 := p.parse_eq()
											eq983 := _t1814
											_t1813 = eq983
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1811 = _t1813
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
		_t1793 = _t1797
	}
	result998 := _t1793
	p.recordSpan(int(span_start997), "Primitive")
	return result998
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1001 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1815 := p.parse_term()
	term999 := _t1815
	_t1816 := p.parse_term()
	term_31000 := _t1816
	p.consumeLiteral(")")
	_t1817 := &pb.RelTerm{}
	_t1817.RelTermType = &pb.RelTerm_Term{Term: term999}
	_t1818 := &pb.RelTerm{}
	_t1818.RelTermType = &pb.RelTerm_Term{Term: term_31000}
	_t1819 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1817, _t1818}}
	result1002 := _t1819
	p.recordSpan(int(span_start1001), "Primitive")
	return result1002
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1820 := p.parse_term()
	term1003 := _t1820
	_t1821 := p.parse_term()
	term_31004 := _t1821
	p.consumeLiteral(")")
	_t1822 := &pb.RelTerm{}
	_t1822.RelTermType = &pb.RelTerm_Term{Term: term1003}
	_t1823 := &pb.RelTerm{}
	_t1823.RelTermType = &pb.RelTerm_Term{Term: term_31004}
	_t1824 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1822, _t1823}}
	result1006 := _t1824
	p.recordSpan(int(span_start1005), "Primitive")
	return result1006
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1825 := p.parse_term()
	term1007 := _t1825
	_t1826 := p.parse_term()
	term_31008 := _t1826
	p.consumeLiteral(")")
	_t1827 := &pb.RelTerm{}
	_t1827.RelTermType = &pb.RelTerm_Term{Term: term1007}
	_t1828 := &pb.RelTerm{}
	_t1828.RelTermType = &pb.RelTerm_Term{Term: term_31008}
	_t1829 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1827, _t1828}}
	result1010 := _t1829
	p.recordSpan(int(span_start1009), "Primitive")
	return result1010
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1830 := p.parse_term()
	term1011 := _t1830
	_t1831 := p.parse_term()
	term_31012 := _t1831
	p.consumeLiteral(")")
	_t1832 := &pb.RelTerm{}
	_t1832.RelTermType = &pb.RelTerm_Term{Term: term1011}
	_t1833 := &pb.RelTerm{}
	_t1833.RelTermType = &pb.RelTerm_Term{Term: term_31012}
	_t1834 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1832, _t1833}}
	result1014 := _t1834
	p.recordSpan(int(span_start1013), "Primitive")
	return result1014
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1835 := p.parse_term()
	term1015 := _t1835
	_t1836 := p.parse_term()
	term_31016 := _t1836
	p.consumeLiteral(")")
	_t1837 := &pb.RelTerm{}
	_t1837.RelTermType = &pb.RelTerm_Term{Term: term1015}
	_t1838 := &pb.RelTerm{}
	_t1838.RelTermType = &pb.RelTerm_Term{Term: term_31016}
	_t1839 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1837, _t1838}}
	result1018 := _t1839
	p.recordSpan(int(span_start1017), "Primitive")
	return result1018
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1840 := p.parse_term()
	term1019 := _t1840
	_t1841 := p.parse_term()
	term_31020 := _t1841
	_t1842 := p.parse_term()
	term_41021 := _t1842
	p.consumeLiteral(")")
	_t1843 := &pb.RelTerm{}
	_t1843.RelTermType = &pb.RelTerm_Term{Term: term1019}
	_t1844 := &pb.RelTerm{}
	_t1844.RelTermType = &pb.RelTerm_Term{Term: term_31020}
	_t1845 := &pb.RelTerm{}
	_t1845.RelTermType = &pb.RelTerm_Term{Term: term_41021}
	_t1846 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1843, _t1844, _t1845}}
	result1023 := _t1846
	p.recordSpan(int(span_start1022), "Primitive")
	return result1023
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1027 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1847 := p.parse_term()
	term1024 := _t1847
	_t1848 := p.parse_term()
	term_31025 := _t1848
	_t1849 := p.parse_term()
	term_41026 := _t1849
	p.consumeLiteral(")")
	_t1850 := &pb.RelTerm{}
	_t1850.RelTermType = &pb.RelTerm_Term{Term: term1024}
	_t1851 := &pb.RelTerm{}
	_t1851.RelTermType = &pb.RelTerm_Term{Term: term_31025}
	_t1852 := &pb.RelTerm{}
	_t1852.RelTermType = &pb.RelTerm_Term{Term: term_41026}
	_t1853 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1850, _t1851, _t1852}}
	result1028 := _t1853
	p.recordSpan(int(span_start1027), "Primitive")
	return result1028
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1854 := p.parse_term()
	term1029 := _t1854
	_t1855 := p.parse_term()
	term_31030 := _t1855
	_t1856 := p.parse_term()
	term_41031 := _t1856
	p.consumeLiteral(")")
	_t1857 := &pb.RelTerm{}
	_t1857.RelTermType = &pb.RelTerm_Term{Term: term1029}
	_t1858 := &pb.RelTerm{}
	_t1858.RelTermType = &pb.RelTerm_Term{Term: term_31030}
	_t1859 := &pb.RelTerm{}
	_t1859.RelTermType = &pb.RelTerm_Term{Term: term_41031}
	_t1860 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1857, _t1858, _t1859}}
	result1033 := _t1860
	p.recordSpan(int(span_start1032), "Primitive")
	return result1033
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1037 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1861 := p.parse_term()
	term1034 := _t1861
	_t1862 := p.parse_term()
	term_31035 := _t1862
	_t1863 := p.parse_term()
	term_41036 := _t1863
	p.consumeLiteral(")")
	_t1864 := &pb.RelTerm{}
	_t1864.RelTermType = &pb.RelTerm_Term{Term: term1034}
	_t1865 := &pb.RelTerm{}
	_t1865.RelTermType = &pb.RelTerm_Term{Term: term_31035}
	_t1866 := &pb.RelTerm{}
	_t1866.RelTermType = &pb.RelTerm_Term{Term: term_41036}
	_t1867 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1864, _t1865, _t1866}}
	result1038 := _t1867
	p.recordSpan(int(span_start1037), "Primitive")
	return result1038
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1042 := int64(p.spanStart())
	var _t1868 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1868 = 1
	} else {
		var _t1869 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1869 = 1
		} else {
			var _t1870 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1870 = 1
			} else {
				var _t1871 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1871 = 1
				} else {
					var _t1872 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1872 = 0
					} else {
						var _t1873 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1873 = 1
						} else {
							var _t1874 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1874 = 1
							} else {
								var _t1875 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1875 = 1
								} else {
									var _t1876 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1876 = 1
									} else {
										var _t1877 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1877 = 1
										} else {
											var _t1878 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1878 = 1
											} else {
												var _t1879 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1879 = 1
												} else {
													var _t1880 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1880 = 1
													} else {
														var _t1881 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1881 = 1
														} else {
															var _t1882 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1882 = 1
															} else {
																_t1882 = -1
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
	prediction1039 := _t1868
	var _t1883 *pb.RelTerm
	if prediction1039 == 1 {
		_t1884 := p.parse_term()
		term1041 := _t1884
		_t1885 := &pb.RelTerm{}
		_t1885.RelTermType = &pb.RelTerm_Term{Term: term1041}
		_t1883 = _t1885
	} else {
		var _t1886 *pb.RelTerm
		if prediction1039 == 0 {
			_t1887 := p.parse_specialized_value()
			specialized_value1040 := _t1887
			_t1888 := &pb.RelTerm{}
			_t1888.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1040}
			_t1886 = _t1888
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1883 = _t1886
	}
	result1043 := _t1883
	p.recordSpan(int(span_start1042), "RelTerm")
	return result1043
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1045 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1889 := p.parse_raw_value()
	raw_value1044 := _t1889
	result1046 := raw_value1044
	p.recordSpan(int(span_start1045), "Value")
	return result1046
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1890 := p.parse_name()
	name1047 := _t1890
	xs1048 := []*pb.RelTerm{}
	cond1049 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1049 {
		_t1891 := p.parse_rel_term()
		item1050 := _t1891
		xs1048 = append(xs1048, item1050)
		cond1049 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1051 := xs1048
	p.consumeLiteral(")")
	_t1892 := &pb.RelAtom{Name: name1047, Terms: rel_terms1051}
	result1053 := _t1892
	p.recordSpan(int(span_start1052), "RelAtom")
	return result1053
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1056 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1893 := p.parse_term()
	term1054 := _t1893
	_t1894 := p.parse_term()
	term_31055 := _t1894
	p.consumeLiteral(")")
	_t1895 := &pb.Cast{Input: term1054, Result: term_31055}
	result1057 := _t1895
	p.recordSpan(int(span_start1056), "Cast")
	return result1057
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1058 := []*pb.Attribute{}
	cond1059 := p.matchLookaheadLiteral("(", 0)
	for cond1059 {
		_t1896 := p.parse_attribute()
		item1060 := _t1896
		xs1058 = append(xs1058, item1060)
		cond1059 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1061 := xs1058
	p.consumeLiteral(")")
	return attributes1061
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1067 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1897 := p.parse_name()
	name1062 := _t1897
	xs1063 := []*pb.Value{}
	cond1064 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1064 {
		_t1898 := p.parse_raw_value()
		item1065 := _t1898
		xs1063 = append(xs1063, item1065)
		cond1064 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1066 := xs1063
	p.consumeLiteral(")")
	_t1899 := &pb.Attribute{Name: name1062, Args: raw_values1066}
	result1068 := _t1899
	p.recordSpan(int(span_start1067), "Attribute")
	return result1068
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1075 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1069 := []*pb.RelationId{}
	cond1070 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1070 {
		_t1900 := p.parse_relation_id()
		item1071 := _t1900
		xs1069 = append(xs1069, item1071)
		cond1070 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1072 := xs1069
	_t1901 := p.parse_script()
	script1073 := _t1901
	var _t1902 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1903 := p.parse_attrs()
		_t1902 = _t1903
	}
	attrs1074 := _t1902
	p.consumeLiteral(")")
	_t1904 := attrs1074
	if attrs1074 == nil {
		_t1904 = []*pb.Attribute{}
	}
	_t1905 := &pb.Algorithm{Global: relation_ids1072, Body: script1073, Attrs: _t1904}
	result1076 := _t1905
	p.recordSpan(int(span_start1075), "Algorithm")
	return result1076
}

func (p *Parser) parse_script() *pb.Script {
	span_start1081 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1077 := []*pb.Construct{}
	cond1078 := p.matchLookaheadLiteral("(", 0)
	for cond1078 {
		_t1906 := p.parse_construct()
		item1079 := _t1906
		xs1077 = append(xs1077, item1079)
		cond1078 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1080 := xs1077
	p.consumeLiteral(")")
	_t1907 := &pb.Script{Constructs: constructs1080}
	result1082 := _t1907
	p.recordSpan(int(span_start1081), "Script")
	return result1082
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1086 := int64(p.spanStart())
	var _t1908 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1909 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1909 = 1
		} else {
			var _t1910 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1910 = 1
			} else {
				var _t1911 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1911 = 1
				} else {
					var _t1912 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1912 = 0
					} else {
						var _t1913 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1913 = 1
						} else {
							var _t1914 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1914 = 1
							} else {
								_t1914 = -1
							}
							_t1913 = _t1914
						}
						_t1912 = _t1913
					}
					_t1911 = _t1912
				}
				_t1910 = _t1911
			}
			_t1909 = _t1910
		}
		_t1908 = _t1909
	} else {
		_t1908 = -1
	}
	prediction1083 := _t1908
	var _t1915 *pb.Construct
	if prediction1083 == 1 {
		_t1916 := p.parse_instruction()
		instruction1085 := _t1916
		_t1917 := &pb.Construct{}
		_t1917.ConstructType = &pb.Construct_Instruction{Instruction: instruction1085}
		_t1915 = _t1917
	} else {
		var _t1918 *pb.Construct
		if prediction1083 == 0 {
			_t1919 := p.parse_loop()
			loop1084 := _t1919
			_t1920 := &pb.Construct{}
			_t1920.ConstructType = &pb.Construct_Loop{Loop: loop1084}
			_t1918 = _t1920
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1915 = _t1918
	}
	result1087 := _t1915
	p.recordSpan(int(span_start1086), "Construct")
	return result1087
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1091 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1921 := p.parse_init()
	init1088 := _t1921
	_t1922 := p.parse_script()
	script1089 := _t1922
	var _t1923 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1924 := p.parse_attrs()
		_t1923 = _t1924
	}
	attrs1090 := _t1923
	p.consumeLiteral(")")
	_t1925 := attrs1090
	if attrs1090 == nil {
		_t1925 = []*pb.Attribute{}
	}
	_t1926 := &pb.Loop{Init: init1088, Body: script1089, Attrs: _t1925}
	result1092 := _t1926
	p.recordSpan(int(span_start1091), "Loop")
	return result1092
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1093 := []*pb.Instruction{}
	cond1094 := p.matchLookaheadLiteral("(", 0)
	for cond1094 {
		_t1927 := p.parse_instruction()
		item1095 := _t1927
		xs1093 = append(xs1093, item1095)
		cond1094 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1096 := xs1093
	p.consumeLiteral(")")
	return instructions1096
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1103 := int64(p.spanStart())
	var _t1928 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1929 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1929 = 1
		} else {
			var _t1930 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1930 = 4
			} else {
				var _t1931 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1931 = 3
				} else {
					var _t1932 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1932 = 2
					} else {
						var _t1933 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1933 = 0
						} else {
							_t1933 = -1
						}
						_t1932 = _t1933
					}
					_t1931 = _t1932
				}
				_t1930 = _t1931
			}
			_t1929 = _t1930
		}
		_t1928 = _t1929
	} else {
		_t1928 = -1
	}
	prediction1097 := _t1928
	var _t1934 *pb.Instruction
	if prediction1097 == 4 {
		_t1935 := p.parse_monus_def()
		monus_def1102 := _t1935
		_t1936 := &pb.Instruction{}
		_t1936.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1102}
		_t1934 = _t1936
	} else {
		var _t1937 *pb.Instruction
		if prediction1097 == 3 {
			_t1938 := p.parse_monoid_def()
			monoid_def1101 := _t1938
			_t1939 := &pb.Instruction{}
			_t1939.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1101}
			_t1937 = _t1939
		} else {
			var _t1940 *pb.Instruction
			if prediction1097 == 2 {
				_t1941 := p.parse_break()
				break1100 := _t1941
				_t1942 := &pb.Instruction{}
				_t1942.InstrType = &pb.Instruction_Break{Break: break1100}
				_t1940 = _t1942
			} else {
				var _t1943 *pb.Instruction
				if prediction1097 == 1 {
					_t1944 := p.parse_upsert()
					upsert1099 := _t1944
					_t1945 := &pb.Instruction{}
					_t1945.InstrType = &pb.Instruction_Upsert{Upsert: upsert1099}
					_t1943 = _t1945
				} else {
					var _t1946 *pb.Instruction
					if prediction1097 == 0 {
						_t1947 := p.parse_assign()
						assign1098 := _t1947
						_t1948 := &pb.Instruction{}
						_t1948.InstrType = &pb.Instruction_Assign{Assign: assign1098}
						_t1946 = _t1948
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1943 = _t1946
				}
				_t1940 = _t1943
			}
			_t1937 = _t1940
		}
		_t1934 = _t1937
	}
	result1104 := _t1934
	p.recordSpan(int(span_start1103), "Instruction")
	return result1104
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1108 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1949 := p.parse_relation_id()
	relation_id1105 := _t1949
	_t1950 := p.parse_abstraction()
	abstraction1106 := _t1950
	var _t1951 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1952 := p.parse_attrs()
		_t1951 = _t1952
	}
	attrs1107 := _t1951
	p.consumeLiteral(")")
	_t1953 := attrs1107
	if attrs1107 == nil {
		_t1953 = []*pb.Attribute{}
	}
	_t1954 := &pb.Assign{Name: relation_id1105, Body: abstraction1106, Attrs: _t1953}
	result1109 := _t1954
	p.recordSpan(int(span_start1108), "Assign")
	return result1109
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1113 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1955 := p.parse_relation_id()
	relation_id1110 := _t1955
	_t1956 := p.parse_abstraction_with_arity()
	abstraction_with_arity1111 := _t1956
	var _t1957 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1958 := p.parse_attrs()
		_t1957 = _t1958
	}
	attrs1112 := _t1957
	p.consumeLiteral(")")
	_t1959 := attrs1112
	if attrs1112 == nil {
		_t1959 = []*pb.Attribute{}
	}
	_t1960 := &pb.Upsert{Name: relation_id1110, Body: abstraction_with_arity1111[0].(*pb.Abstraction), Attrs: _t1959, ValueArity: abstraction_with_arity1111[1].(int64)}
	result1114 := _t1960
	p.recordSpan(int(span_start1113), "Upsert")
	return result1114
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1961 := p.parse_bindings()
	bindings1115 := _t1961
	_t1962 := p.parse_formula()
	formula1116 := _t1962
	p.consumeLiteral(")")
	_t1963 := &pb.Abstraction{Vars: listConcat(bindings1115[0].([]*pb.Binding), bindings1115[1].([]*pb.Binding)), Value: formula1116}
	return []interface{}{_t1963, int64(len(bindings1115[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1120 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1964 := p.parse_relation_id()
	relation_id1117 := _t1964
	_t1965 := p.parse_abstraction()
	abstraction1118 := _t1965
	var _t1966 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1967 := p.parse_attrs()
		_t1966 = _t1967
	}
	attrs1119 := _t1966
	p.consumeLiteral(")")
	_t1968 := attrs1119
	if attrs1119 == nil {
		_t1968 = []*pb.Attribute{}
	}
	_t1969 := &pb.Break{Name: relation_id1117, Body: abstraction1118, Attrs: _t1968}
	result1121 := _t1969
	p.recordSpan(int(span_start1120), "Break")
	return result1121
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1126 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1970 := p.parse_monoid()
	monoid1122 := _t1970
	_t1971 := p.parse_relation_id()
	relation_id1123 := _t1971
	_t1972 := p.parse_abstraction_with_arity()
	abstraction_with_arity1124 := _t1972
	var _t1973 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1974 := p.parse_attrs()
		_t1973 = _t1974
	}
	attrs1125 := _t1973
	p.consumeLiteral(")")
	_t1975 := attrs1125
	if attrs1125 == nil {
		_t1975 = []*pb.Attribute{}
	}
	_t1976 := &pb.MonoidDef{Monoid: monoid1122, Name: relation_id1123, Body: abstraction_with_arity1124[0].(*pb.Abstraction), Attrs: _t1975, ValueArity: abstraction_with_arity1124[1].(int64)}
	result1127 := _t1976
	p.recordSpan(int(span_start1126), "MonoidDef")
	return result1127
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1133 := int64(p.spanStart())
	var _t1977 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1978 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1978 = 3
		} else {
			var _t1979 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1979 = 0
			} else {
				var _t1980 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1980 = 1
				} else {
					var _t1981 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1981 = 2
					} else {
						_t1981 = -1
					}
					_t1980 = _t1981
				}
				_t1979 = _t1980
			}
			_t1978 = _t1979
		}
		_t1977 = _t1978
	} else {
		_t1977 = -1
	}
	prediction1128 := _t1977
	var _t1982 *pb.Monoid
	if prediction1128 == 3 {
		_t1983 := p.parse_sum_monoid()
		sum_monoid1132 := _t1983
		_t1984 := &pb.Monoid{}
		_t1984.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1132}
		_t1982 = _t1984
	} else {
		var _t1985 *pb.Monoid
		if prediction1128 == 2 {
			_t1986 := p.parse_max_monoid()
			max_monoid1131 := _t1986
			_t1987 := &pb.Monoid{}
			_t1987.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1131}
			_t1985 = _t1987
		} else {
			var _t1988 *pb.Monoid
			if prediction1128 == 1 {
				_t1989 := p.parse_min_monoid()
				min_monoid1130 := _t1989
				_t1990 := &pb.Monoid{}
				_t1990.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1130}
				_t1988 = _t1990
			} else {
				var _t1991 *pb.Monoid
				if prediction1128 == 0 {
					_t1992 := p.parse_or_monoid()
					or_monoid1129 := _t1992
					_t1993 := &pb.Monoid{}
					_t1993.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1129}
					_t1991 = _t1993
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1988 = _t1991
			}
			_t1985 = _t1988
		}
		_t1982 = _t1985
	}
	result1134 := _t1982
	p.recordSpan(int(span_start1133), "Monoid")
	return result1134
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1135 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1994 := &pb.OrMonoid{}
	result1136 := _t1994
	p.recordSpan(int(span_start1135), "OrMonoid")
	return result1136
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1995 := p.parse_type()
	type1137 := _t1995
	p.consumeLiteral(")")
	_t1996 := &pb.MinMonoid{Type: type1137}
	result1139 := _t1996
	p.recordSpan(int(span_start1138), "MinMonoid")
	return result1139
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1141 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1997 := p.parse_type()
	type1140 := _t1997
	p.consumeLiteral(")")
	_t1998 := &pb.MaxMonoid{Type: type1140}
	result1142 := _t1998
	p.recordSpan(int(span_start1141), "MaxMonoid")
	return result1142
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1144 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1999 := p.parse_type()
	type1143 := _t1999
	p.consumeLiteral(")")
	_t2000 := &pb.SumMonoid{Type: type1143}
	result1145 := _t2000
	p.recordSpan(int(span_start1144), "SumMonoid")
	return result1145
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t2001 := p.parse_monoid()
	monoid1146 := _t2001
	_t2002 := p.parse_relation_id()
	relation_id1147 := _t2002
	_t2003 := p.parse_abstraction_with_arity()
	abstraction_with_arity1148 := _t2003
	var _t2004 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2005 := p.parse_attrs()
		_t2004 = _t2005
	}
	attrs1149 := _t2004
	p.consumeLiteral(")")
	_t2006 := attrs1149
	if attrs1149 == nil {
		_t2006 = []*pb.Attribute{}
	}
	_t2007 := &pb.MonusDef{Monoid: monoid1146, Name: relation_id1147, Body: abstraction_with_arity1148[0].(*pb.Abstraction), Attrs: _t2006, ValueArity: abstraction_with_arity1148[1].(int64)}
	result1151 := _t2007
	p.recordSpan(int(span_start1150), "MonusDef")
	return result1151
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2008 := p.parse_relation_id()
	relation_id1152 := _t2008
	_t2009 := p.parse_abstraction()
	abstraction1153 := _t2009
	_t2010 := p.parse_functional_dependency_keys()
	functional_dependency_keys1154 := _t2010
	_t2011 := p.parse_functional_dependency_values()
	functional_dependency_values1155 := _t2011
	p.consumeLiteral(")")
	_t2012 := &pb.FunctionalDependency{Guard: abstraction1153, Keys: functional_dependency_keys1154, Values: functional_dependency_values1155}
	_t2013 := &pb.Constraint{Name: relation_id1152}
	_t2013.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2012}
	result1157 := _t2013
	p.recordSpan(int(span_start1156), "Constraint")
	return result1157
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1158 := []*pb.Var{}
	cond1159 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1159 {
		_t2014 := p.parse_var()
		item1160 := _t2014
		xs1158 = append(xs1158, item1160)
		cond1159 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1161 := xs1158
	p.consumeLiteral(")")
	return vars1161
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1162 := []*pb.Var{}
	cond1163 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1163 {
		_t2015 := p.parse_var()
		item1164 := _t2015
		xs1162 = append(xs1162, item1164)
		cond1163 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1165 := xs1162
	p.consumeLiteral(")")
	return vars1165
}

func (p *Parser) parse_data() *pb.Data {
	span_start1171 := int64(p.spanStart())
	var _t2016 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2017 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2017 = 3
		} else {
			var _t2018 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2018 = 0
			} else {
				var _t2019 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2019 = 2
				} else {
					var _t2020 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2020 = 1
					} else {
						_t2020 = -1
					}
					_t2019 = _t2020
				}
				_t2018 = _t2019
			}
			_t2017 = _t2018
		}
		_t2016 = _t2017
	} else {
		_t2016 = -1
	}
	prediction1166 := _t2016
	var _t2021 *pb.Data
	if prediction1166 == 3 {
		_t2022 := p.parse_iceberg_data()
		iceberg_data1170 := _t2022
		_t2023 := &pb.Data{}
		_t2023.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1170}
		_t2021 = _t2023
	} else {
		var _t2024 *pb.Data
		if prediction1166 == 2 {
			_t2025 := p.parse_csv_data()
			csv_data1169 := _t2025
			_t2026 := &pb.Data{}
			_t2026.DataType = &pb.Data_CsvData{CsvData: csv_data1169}
			_t2024 = _t2026
		} else {
			var _t2027 *pb.Data
			if prediction1166 == 1 {
				_t2028 := p.parse_betree_relation()
				betree_relation1168 := _t2028
				_t2029 := &pb.Data{}
				_t2029.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1168}
				_t2027 = _t2029
			} else {
				var _t2030 *pb.Data
				if prediction1166 == 0 {
					_t2031 := p.parse_edb()
					edb1167 := _t2031
					_t2032 := &pb.Data{}
					_t2032.DataType = &pb.Data_Edb{Edb: edb1167}
					_t2030 = _t2032
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2027 = _t2030
			}
			_t2024 = _t2027
		}
		_t2021 = _t2024
	}
	result1172 := _t2021
	p.recordSpan(int(span_start1171), "Data")
	return result1172
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1176 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2033 := p.parse_relation_id()
	relation_id1173 := _t2033
	_t2034 := p.parse_edb_path()
	edb_path1174 := _t2034
	_t2035 := p.parse_edb_types()
	edb_types1175 := _t2035
	p.consumeLiteral(")")
	_t2036 := &pb.EDB{TargetId: relation_id1173, Path: edb_path1174, Types: edb_types1175}
	result1177 := _t2036
	p.recordSpan(int(span_start1176), "EDB")
	return result1177
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1178 := []string{}
	cond1179 := p.matchLookaheadTerminal("STRING", 0)
	for cond1179 {
		item1180 := p.consumeTerminal("STRING").Value.str
		xs1178 = append(xs1178, item1180)
		cond1179 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1181 := xs1178
	p.consumeLiteral("]")
	return strings1181
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1182 := []*pb.Type{}
	cond1183 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1183 {
		_t2037 := p.parse_type()
		item1184 := _t2037
		xs1182 = append(xs1182, item1184)
		cond1183 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1185 := xs1182
	p.consumeLiteral("]")
	return types1185
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1188 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2038 := p.parse_relation_id()
	relation_id1186 := _t2038
	_t2039 := p.parse_betree_info()
	betree_info1187 := _t2039
	p.consumeLiteral(")")
	_t2040 := &pb.BeTreeRelation{Name: relation_id1186, RelationInfo: betree_info1187}
	result1189 := _t2040
	p.recordSpan(int(span_start1188), "BeTreeRelation")
	return result1189
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1193 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2041 := p.parse_betree_info_key_types()
	betree_info_key_types1190 := _t2041
	_t2042 := p.parse_betree_info_value_types()
	betree_info_value_types1191 := _t2042
	_t2043 := p.parse_config_dict()
	config_dict1192 := _t2043
	p.consumeLiteral(")")
	_t2044 := p.construct_betree_info(betree_info_key_types1190, betree_info_value_types1191, config_dict1192)
	result1194 := _t2044
	p.recordSpan(int(span_start1193), "BeTreeInfo")
	return result1194
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1195 := []*pb.Type{}
	cond1196 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1196 {
		_t2045 := p.parse_type()
		item1197 := _t2045
		xs1195 = append(xs1195, item1197)
		cond1196 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1198 := xs1195
	p.consumeLiteral(")")
	return types1198
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1199 := []*pb.Type{}
	cond1200 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1200 {
		_t2046 := p.parse_type()
		item1201 := _t2046
		xs1199 = append(xs1199, item1201)
		cond1200 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1202 := xs1199
	p.consumeLiteral(")")
	return types1202
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1208 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2047 := p.parse_csvlocator()
	csvlocator1203 := _t2047
	_t2048 := p.parse_csv_config()
	csv_config1204 := _t2048
	var _t2049 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2050 := p.parse_gnf_columns()
		_t2049 = _t2050
	}
	gnf_columns1205 := _t2049
	var _t2051 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2052 := p.parse_target_relations()
		_t2051 = _t2052
	}
	target_relations1206 := _t2051
	_t2053 := p.parse_csv_asof()
	csv_asof1207 := _t2053
	p.consumeLiteral(")")
	_t2054 := p.construct_csv_data(csvlocator1203, csv_config1204, gnf_columns1205, target_relations1206, csv_asof1207)
	result1209 := _t2054
	p.recordSpan(int(span_start1208), "CSVData")
	return result1209
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2055 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2056 := p.parse_csv_locator_paths()
		_t2055 = _t2056
	}
	csv_locator_paths1210 := _t2055
	var _t2057 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2058 := p.parse_csv_locator_inline_data()
		_t2057 = ptr(_t2058)
	}
	csv_locator_inline_data1211 := _t2057
	p.consumeLiteral(")")
	_t2059 := csv_locator_paths1210
	if csv_locator_paths1210 == nil {
		_t2059 = []string{}
	}
	_t2060 := &pb.CSVLocator{Paths: _t2059, InlineData: []byte(deref(csv_locator_inline_data1211, ""))}
	result1213 := _t2060
	p.recordSpan(int(span_start1212), "CSVLocator")
	return result1213
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1214 := []string{}
	cond1215 := p.matchLookaheadTerminal("STRING", 0)
	for cond1215 {
		item1216 := p.consumeTerminal("STRING").Value.str
		xs1214 = append(xs1214, item1216)
		cond1215 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1217 := xs1214
	p.consumeLiteral(")")
	return strings1217
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1218 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1218
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1221 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2061 := p.parse_config_dict()
	config_dict1219 := _t2061
	var _t2062 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2063 := p.parse__storage_integration()
		_t2062 = _t2063
	}
	_storage_integration1220 := _t2062
	p.consumeLiteral(")")
	_t2064 := p.construct_csv_config(config_dict1219, _storage_integration1220)
	result1222 := _t2064
	p.recordSpan(int(span_start1221), "CSVConfig")
	return result1222
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2065 := p.parse_config_dict()
	config_dict1223 := _t2065
	p.consumeLiteral(")")
	return config_dict1223
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1224 := []*pb.GNFColumn{}
	cond1225 := p.matchLookaheadLiteral("(", 0)
	for cond1225 {
		_t2066 := p.parse_gnf_column()
		item1226 := _t2066
		xs1224 = append(xs1224, item1226)
		cond1225 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1227 := xs1224
	p.consumeLiteral(")")
	return gnf_columns1227
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1234 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2067 := p.parse_gnf_column_path()
	gnf_column_path1228 := _t2067
	var _t2068 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2069 := p.parse_relation_id()
		_t2068 = _t2069
	}
	relation_id1229 := _t2068
	p.consumeLiteral("[")
	xs1230 := []*pb.Type{}
	cond1231 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1231 {
		_t2070 := p.parse_type()
		item1232 := _t2070
		xs1230 = append(xs1230, item1232)
		cond1231 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1233 := xs1230
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2071 := &pb.GNFColumn{ColumnPath: gnf_column_path1228, TargetId: relation_id1229, Types: types1233}
	result1235 := _t2071
	p.recordSpan(int(span_start1234), "GNFColumn")
	return result1235
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2072 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2072 = 1
	} else {
		var _t2073 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2073 = 0
		} else {
			_t2073 = -1
		}
		_t2072 = _t2073
	}
	prediction1236 := _t2072
	var _t2074 []string
	if prediction1236 == 1 {
		p.consumeLiteral("[")
		xs1238 := []string{}
		cond1239 := p.matchLookaheadTerminal("STRING", 0)
		for cond1239 {
			item1240 := p.consumeTerminal("STRING").Value.str
			xs1238 = append(xs1238, item1240)
			cond1239 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1241 := xs1238
		p.consumeLiteral("]")
		_t2074 = strings1241
	} else {
		var _t2075 []string
		if prediction1236 == 0 {
			string1237 := p.consumeTerminal("STRING").Value.str
			_ = string1237
			_t2075 = []string{string1237}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2074 = _t2075
	}
	return _t2074
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1244 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2076 := p.parse_relation_keys()
	relation_keys1242 := _t2076
	_t2077 := p.parse_relation_body()
	relation_body1243 := _t2077
	p.consumeLiteral(")")
	_t2078 := p.construct_relations(relation_keys1242, relation_body1243)
	result1245 := _t2078
	p.recordSpan(int(span_start1244), "TargetRelations")
	return result1245
}

func (p *Parser) parse_relation_keys() []interface{} {
	var _t2079 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2080 int64
		if p.matchLookaheadLiteral("keys", 1) {
			var _t2081 int64
			if p.matchLookaheadLiteral("synthetic", 2) {
				_t2081 = 1
			} else {
				var _t2082 int64
				if p.matchLookaheadLiteral(")", 2) {
					_t2082 = 0
				} else {
					var _t2083 int64
					if p.matchLookaheadLiteral("(", 2) {
						_t2083 = 0
					} else {
						_t2083 = -1
					}
					_t2082 = _t2083
				}
				_t2081 = _t2082
			}
			_t2080 = _t2081
		} else {
			_t2080 = -1
		}
		_t2079 = _t2080
	} else {
		_t2079 = -1
	}
	prediction1246 := _t2079
	var _t2084 []interface{}
	if prediction1246 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("keys")
		p.consumeLiteral("synthetic")
		p.consumeLiteral(")")
		_t2084 = []interface{}{[]*pb.NamedColumn{}, true}
	} else {
		var _t2085 []interface{}
		if prediction1246 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("keys")
			xs1247 := []*pb.NamedColumn{}
			cond1248 := p.matchLookaheadLiteral("(", 0)
			for cond1248 {
				_t2086 := p.parse_named_column()
				item1249 := _t2086
				xs1247 = append(xs1247, item1249)
				cond1248 = p.matchLookaheadLiteral("(", 0)
			}
			named_columns1250 := xs1247
			p.consumeLiteral(")")
			_t2085 = []interface{}{named_columns1250, false}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_keys", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2084 = _t2085
	}
	return _t2084
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1253 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1251 := p.consumeTerminal("STRING").Value.str
	_t2087 := p.parse_type()
	type1252 := _t2087
	p.consumeLiteral(")")
	_t2088 := &pb.NamedColumn{Name: string1251, Type: type1252}
	result1254 := _t2088
	p.recordSpan(int(span_start1253), "NamedColumn")
	return result1254
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1259 := int64(p.spanStart())
	var _t2089 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2090 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2090 = 0
		} else {
			var _t2091 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2091 = 1
			} else {
				_t2091 = 0
			}
			_t2090 = _t2091
		}
		_t2089 = _t2090
	} else {
		_t2089 = 0
	}
	prediction1255 := _t2089
	var _t2092 *pb.TargetRelations
	if prediction1255 == 1 {
		_t2093 := p.parse_cdc_inserts()
		cdc_inserts1257 := _t2093
		_t2094 := p.parse_cdc_deletes()
		cdc_deletes1258 := _t2094
		_t2095 := p.construct_cdc_relations(cdc_inserts1257, cdc_deletes1258)
		_t2092 = _t2095
	} else {
		var _t2096 *pb.TargetRelations
		if prediction1255 == 0 {
			_t2097 := p.parse_non_cdc_relations()
			non_cdc_relations1256 := _t2097
			_t2098 := p.construct_non_cdc_relations(non_cdc_relations1256)
			_t2096 = _t2098
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2092 = _t2096
	}
	result1260 := _t2092
	p.recordSpan(int(span_start1259), "TargetRelations")
	return result1260
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1261 := []*pb.TargetRelation{}
	cond1262 := p.matchLookaheadLiteral("(", 0)
	for cond1262 {
		_t2099 := p.parse_target_relation()
		item1263 := _t2099
		xs1261 = append(xs1261, item1263)
		cond1262 = p.matchLookaheadLiteral("(", 0)
	}
	return xs1261
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1269 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2100 := p.parse_relation_id()
	relation_id1264 := _t2100
	xs1265 := []*pb.NamedColumn{}
	cond1266 := p.matchLookaheadLiteral("(", 0)
	for cond1266 {
		_t2101 := p.parse_named_column()
		item1267 := _t2101
		xs1265 = append(xs1265, item1267)
		cond1266 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1268 := xs1265
	p.consumeLiteral(")")
	_t2102 := &pb.TargetRelation{TargetId: relation_id1264, Values: named_columns1268}
	result1270 := _t2102
	p.recordSpan(int(span_start1269), "TargetRelation")
	return result1270
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1271 := []*pb.TargetRelation{}
	cond1272 := p.matchLookaheadLiteral("(", 0)
	for cond1272 {
		_t2103 := p.parse_target_relation()
		item1273 := _t2103
		xs1271 = append(xs1271, item1273)
		cond1272 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1274 := xs1271
	p.consumeLiteral(")")
	return target_relations1274
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1275 := []*pb.TargetRelation{}
	cond1276 := p.matchLookaheadLiteral("(", 0)
	for cond1276 {
		_t2104 := p.parse_target_relation()
		item1277 := _t2104
		xs1275 = append(xs1275, item1277)
		cond1276 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1278 := xs1275
	p.consumeLiteral(")")
	return target_relations1278
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1279 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1279
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1286 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2105 := p.parse_iceberg_locator()
	iceberg_locator1280 := _t2105
	_t2106 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1281 := _t2106
	_t2107 := p.parse_gnf_columns()
	gnf_columns1282 := _t2107
	var _t2108 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2109 := p.parse_iceberg_from_snapshot()
		_t2108 = ptr(_t2109)
	}
	iceberg_from_snapshot1283 := _t2108
	var _t2110 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2111 := p.parse_iceberg_to_snapshot()
		_t2110 = ptr(_t2111)
	}
	iceberg_to_snapshot1284 := _t2110
	_t2112 := p.parse_boolean_value()
	boolean_value1285 := _t2112
	p.consumeLiteral(")")
	_t2113 := p.construct_iceberg_data(iceberg_locator1280, iceberg_catalog_config1281, gnf_columns1282, iceberg_from_snapshot1283, iceberg_to_snapshot1284, boolean_value1285)
	result1287 := _t2113
	p.recordSpan(int(span_start1286), "IcebergData")
	return result1287
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1291 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2114 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1288 := _t2114
	_t2115 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1289 := _t2115
	_t2116 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1290 := _t2116
	p.consumeLiteral(")")
	_t2117 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1288, Namespace: iceberg_locator_namespace1289, Warehouse: iceberg_locator_warehouse1290}
	result1292 := _t2117
	p.recordSpan(int(span_start1291), "IcebergLocator")
	return result1292
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1293 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1293
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1294 := []string{}
	cond1295 := p.matchLookaheadTerminal("STRING", 0)
	for cond1295 {
		item1296 := p.consumeTerminal("STRING").Value.str
		xs1294 = append(xs1294, item1296)
		cond1295 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1297 := xs1294
	p.consumeLiteral(")")
	return strings1297
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1298 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1298
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1303 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2118 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1299 := _t2118
	var _t2119 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2120 := p.parse_iceberg_catalog_config_scope()
		_t2119 = ptr(_t2120)
	}
	iceberg_catalog_config_scope1300 := _t2119
	_t2121 := p.parse_iceberg_properties()
	iceberg_properties1301 := _t2121
	_t2122 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1302 := _t2122
	p.consumeLiteral(")")
	_t2123 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1299, iceberg_catalog_config_scope1300, iceberg_properties1301, iceberg_auth_properties1302)
	result1304 := _t2123
	p.recordSpan(int(span_start1303), "IcebergCatalogConfig")
	return result1304
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1305 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1305
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1306 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1306
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1307 := [][]interface{}{}
	cond1308 := p.matchLookaheadLiteral("(", 0)
	for cond1308 {
		_t2124 := p.parse_iceberg_property_entry()
		item1309 := _t2124
		xs1307 = append(xs1307, item1309)
		cond1308 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1310 := xs1307
	p.consumeLiteral(")")
	return iceberg_property_entrys1310
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1311 := p.consumeTerminal("STRING").Value.str
	string_31312 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1311, string_31312}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1313 := [][]interface{}{}
	cond1314 := p.matchLookaheadLiteral("(", 0)
	for cond1314 {
		_t2125 := p.parse_iceberg_masked_property_entry()
		item1315 := _t2125
		xs1313 = append(xs1313, item1315)
		cond1314 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1316 := xs1313
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1316
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1317 := p.consumeTerminal("STRING").Value.str
	string_31318 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1317, string_31318}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1319 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1319
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1320 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1320
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1322 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2126 := p.parse_fragment_id()
	fragment_id1321 := _t2126
	p.consumeLiteral(")")
	_t2127 := &pb.Undefine{FragmentId: fragment_id1321}
	result1323 := _t2127
	p.recordSpan(int(span_start1322), "Undefine")
	return result1323
}

func (p *Parser) parse_context() *pb.Context {
	span_start1328 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1324 := []*pb.RelationId{}
	cond1325 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1325 {
		_t2128 := p.parse_relation_id()
		item1326 := _t2128
		xs1324 = append(xs1324, item1326)
		cond1325 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1327 := xs1324
	p.consumeLiteral(")")
	_t2129 := &pb.Context{Relations: relation_ids1327}
	result1329 := _t2129
	p.recordSpan(int(span_start1328), "Context")
	return result1329
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1335 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2130 := p.parse_edb_path()
	edb_path1330 := _t2130
	xs1331 := []*pb.SnapshotMapping{}
	cond1332 := p.matchLookaheadLiteral("[", 0)
	for cond1332 {
		_t2131 := p.parse_snapshot_mapping()
		item1333 := _t2131
		xs1331 = append(xs1331, item1333)
		cond1332 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1334 := xs1331
	p.consumeLiteral(")")
	_t2132 := &pb.Snapshot{Prefix: edb_path1330, Mappings: snapshot_mappings1334}
	result1336 := _t2132
	p.recordSpan(int(span_start1335), "Snapshot")
	return result1336
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1339 := int64(p.spanStart())
	_t2133 := p.parse_edb_path()
	edb_path1337 := _t2133
	_t2134 := p.parse_relation_id()
	relation_id1338 := _t2134
	_t2135 := &pb.SnapshotMapping{DestinationPath: edb_path1337, SourceRelation: relation_id1338}
	result1340 := _t2135
	p.recordSpan(int(span_start1339), "SnapshotMapping")
	return result1340
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1341 := []*pb.Read{}
	cond1342 := p.matchLookaheadLiteral("(", 0)
	for cond1342 {
		_t2136 := p.parse_read()
		item1343 := _t2136
		xs1341 = append(xs1341, item1343)
		cond1342 = p.matchLookaheadLiteral("(", 0)
	}
	reads1344 := xs1341
	p.consumeLiteral(")")
	return reads1344
}

func (p *Parser) parse_read() *pb.Read {
	span_start1351 := int64(p.spanStart())
	var _t2137 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2138 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2138 = 2
		} else {
			var _t2139 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2139 = 1
			} else {
				var _t2140 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2140 = 4
				} else {
					var _t2141 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2141 = 4
					} else {
						var _t2142 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2142 = 0
						} else {
							var _t2143 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2143 = 3
							} else {
								_t2143 = -1
							}
							_t2142 = _t2143
						}
						_t2141 = _t2142
					}
					_t2140 = _t2141
				}
				_t2139 = _t2140
			}
			_t2138 = _t2139
		}
		_t2137 = _t2138
	} else {
		_t2137 = -1
	}
	prediction1345 := _t2137
	var _t2144 *pb.Read
	if prediction1345 == 4 {
		_t2145 := p.parse_export()
		export1350 := _t2145
		_t2146 := &pb.Read{}
		_t2146.ReadType = &pb.Read_Export{Export: export1350}
		_t2144 = _t2146
	} else {
		var _t2147 *pb.Read
		if prediction1345 == 3 {
			_t2148 := p.parse_abort()
			abort1349 := _t2148
			_t2149 := &pb.Read{}
			_t2149.ReadType = &pb.Read_Abort{Abort: abort1349}
			_t2147 = _t2149
		} else {
			var _t2150 *pb.Read
			if prediction1345 == 2 {
				_t2151 := p.parse_what_if()
				what_if1348 := _t2151
				_t2152 := &pb.Read{}
				_t2152.ReadType = &pb.Read_WhatIf{WhatIf: what_if1348}
				_t2150 = _t2152
			} else {
				var _t2153 *pb.Read
				if prediction1345 == 1 {
					_t2154 := p.parse_output()
					output1347 := _t2154
					_t2155 := &pb.Read{}
					_t2155.ReadType = &pb.Read_Output{Output: output1347}
					_t2153 = _t2155
				} else {
					var _t2156 *pb.Read
					if prediction1345 == 0 {
						_t2157 := p.parse_demand()
						demand1346 := _t2157
						_t2158 := &pb.Read{}
						_t2158.ReadType = &pb.Read_Demand{Demand: demand1346}
						_t2156 = _t2158
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2153 = _t2156
				}
				_t2150 = _t2153
			}
			_t2147 = _t2150
		}
		_t2144 = _t2147
	}
	result1352 := _t2144
	p.recordSpan(int(span_start1351), "Read")
	return result1352
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1354 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2159 := p.parse_relation_id()
	relation_id1353 := _t2159
	p.consumeLiteral(")")
	_t2160 := &pb.Demand{RelationId: relation_id1353}
	result1355 := _t2160
	p.recordSpan(int(span_start1354), "Demand")
	return result1355
}

func (p *Parser) parse_output() *pb.Output {
	span_start1358 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2161 := p.parse_name()
	name1356 := _t2161
	_t2162 := p.parse_relation_id()
	relation_id1357 := _t2162
	p.consumeLiteral(")")
	_t2163 := &pb.Output{Name: name1356, RelationId: relation_id1357}
	result1359 := _t2163
	p.recordSpan(int(span_start1358), "Output")
	return result1359
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1362 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2164 := p.parse_name()
	name1360 := _t2164
	_t2165 := p.parse_epoch()
	epoch1361 := _t2165
	p.consumeLiteral(")")
	_t2166 := &pb.WhatIf{Branch: name1360, Epoch: epoch1361}
	result1363 := _t2166
	p.recordSpan(int(span_start1362), "WhatIf")
	return result1363
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1366 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2167 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2168 := p.parse_name()
		_t2167 = ptr(_t2168)
	}
	name1364 := _t2167
	_t2169 := p.parse_relation_id()
	relation_id1365 := _t2169
	p.consumeLiteral(")")
	_t2170 := &pb.Abort{Name: deref(name1364, "abort"), RelationId: relation_id1365}
	result1367 := _t2170
	p.recordSpan(int(span_start1366), "Abort")
	return result1367
}

func (p *Parser) parse_export() *pb.Export {
	span_start1371 := int64(p.spanStart())
	var _t2171 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2172 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2172 = 1
		} else {
			var _t2173 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2173 = 0
			} else {
				_t2173 = -1
			}
			_t2172 = _t2173
		}
		_t2171 = _t2172
	} else {
		_t2171 = -1
	}
	prediction1368 := _t2171
	var _t2174 *pb.Export
	if prediction1368 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2175 := p.parse_export_iceberg_config()
		export_iceberg_config1370 := _t2175
		p.consumeLiteral(")")
		_t2176 := &pb.Export{}
		_t2176.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1370}
		_t2174 = _t2176
	} else {
		var _t2177 *pb.Export
		if prediction1368 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2178 := p.parse_export_csv_config()
			export_csv_config1369 := _t2178
			p.consumeLiteral(")")
			_t2179 := &pb.Export{}
			_t2179.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1369}
			_t2177 = _t2179
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2174 = _t2177
	}
	result1372 := _t2174
	p.recordSpan(int(span_start1371), "Export")
	return result1372
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1380 := int64(p.spanStart())
	var _t2180 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2181 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2181 = 0
		} else {
			var _t2182 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2182 = 1
			} else {
				_t2182 = -1
			}
			_t2181 = _t2182
		}
		_t2180 = _t2181
	} else {
		_t2180 = -1
	}
	prediction1373 := _t2180
	var _t2183 *pb.ExportCSVConfig
	if prediction1373 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2184 := p.parse_export_csv_path()
		export_csv_path1377 := _t2184
		_t2185 := p.parse_export_csv_columns_list()
		export_csv_columns_list1378 := _t2185
		_t2186 := p.parse_config_dict()
		config_dict1379 := _t2186
		p.consumeLiteral(")")
		_t2187 := p.construct_export_csv_config(export_csv_path1377, export_csv_columns_list1378, config_dict1379)
		_t2183 = _t2187
	} else {
		var _t2188 *pb.ExportCSVConfig
		if prediction1373 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2189 := p.parse_export_csv_output_location()
			export_csv_output_location1374 := _t2189
			_t2190 := p.parse_export_csv_source()
			export_csv_source1375 := _t2190
			_t2191 := p.parse_csv_config()
			csv_config1376 := _t2191
			p.consumeLiteral(")")
			_t2192 := p.construct_export_csv_config_with_location(export_csv_output_location1374, export_csv_source1375, csv_config1376)
			_t2188 = _t2192
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2183 = _t2188
	}
	result1381 := _t2183
	p.recordSpan(int(span_start1380), "ExportCSVConfig")
	return result1381
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2193 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2194 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2194 = 1
		} else {
			var _t2195 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2195 = 0
			} else {
				_t2195 = -1
			}
			_t2194 = _t2195
		}
		_t2193 = _t2194
	} else {
		_t2193 = -1
	}
	prediction1382 := _t2193
	var _t2196 []interface{}
	if prediction1382 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2197 := p.parse_name()
		name1384 := _t2197
		p.consumeLiteral(")")
		_t2196 = []interface{}{"", name1384}
	} else {
		var _t2198 []interface{}
		if prediction1382 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1383 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2198 = []interface{}{string1383, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2196 = _t2198
	}
	return _t2196
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1391 := int64(p.spanStart())
	var _t2199 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2200 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2200 = 1
		} else {
			var _t2201 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2201 = 0
			} else {
				_t2201 = -1
			}
			_t2200 = _t2201
		}
		_t2199 = _t2200
	} else {
		_t2199 = -1
	}
	prediction1385 := _t2199
	var _t2202 *pb.ExportCSVSource
	if prediction1385 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2203 := p.parse_relation_id()
		relation_id1390 := _t2203
		p.consumeLiteral(")")
		_t2204 := &pb.ExportCSVSource{}
		_t2204.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1390}
		_t2202 = _t2204
	} else {
		var _t2205 *pb.ExportCSVSource
		if prediction1385 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1386 := []*pb.ExportCSVColumn{}
			cond1387 := p.matchLookaheadLiteral("(", 0)
			for cond1387 {
				_t2206 := p.parse_export_csv_column()
				item1388 := _t2206
				xs1386 = append(xs1386, item1388)
				cond1387 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1389 := xs1386
			p.consumeLiteral(")")
			_t2207 := &pb.ExportCSVColumns{Columns: export_csv_columns1389}
			_t2208 := &pb.ExportCSVSource{}
			_t2208.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2207}
			_t2205 = _t2208
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2202 = _t2205
	}
	result1392 := _t2202
	p.recordSpan(int(span_start1391), "ExportCSVSource")
	return result1392
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1395 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1393 := p.consumeTerminal("STRING").Value.str
	_t2209 := p.parse_relation_id()
	relation_id1394 := _t2209
	p.consumeLiteral(")")
	_t2210 := &pb.ExportCSVColumn{ColumnName: string1393, ColumnData: relation_id1394}
	result1396 := _t2210
	p.recordSpan(int(span_start1395), "ExportCSVColumn")
	return result1396
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1397 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1397
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1398 := []*pb.ExportCSVColumn{}
	cond1399 := p.matchLookaheadLiteral("(", 0)
	for cond1399 {
		_t2211 := p.parse_export_csv_column()
		item1400 := _t2211
		xs1398 = append(xs1398, item1400)
		cond1399 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1401 := xs1398
	p.consumeLiteral(")")
	return export_csv_columns1401
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1407 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2212 := p.parse_iceberg_locator()
	iceberg_locator1402 := _t2212
	_t2213 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1403 := _t2213
	_t2214 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1404 := _t2214
	_t2215 := p.parse_iceberg_table_properties()
	iceberg_table_properties1405 := _t2215
	var _t2216 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2217 := p.parse_config_dict()
		_t2216 = _t2217
	}
	config_dict1406 := _t2216
	p.consumeLiteral(")")
	_t2218 := p.construct_export_iceberg_config_full(iceberg_locator1402, iceberg_catalog_config1403, export_iceberg_table_def1404, iceberg_table_properties1405, config_dict1406)
	result1408 := _t2218
	p.recordSpan(int(span_start1407), "ExportIcebergConfig")
	return result1408
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1410 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2219 := p.parse_relation_id()
	relation_id1409 := _t2219
	p.consumeLiteral(")")
	result1411 := relation_id1409
	p.recordSpan(int(span_start1410), "RelationId")
	return result1411
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1412 := [][]interface{}{}
	cond1413 := p.matchLookaheadLiteral("(", 0)
	for cond1413 {
		_t2220 := p.parse_iceberg_property_entry()
		item1414 := _t2220
		xs1412 = append(xs1412, item1414)
		cond1413 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1415 := xs1412
	p.consumeLiteral(")")
	return iceberg_property_entrys1415
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
