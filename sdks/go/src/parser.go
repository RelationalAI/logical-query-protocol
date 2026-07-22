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
	var _t2224 interface{}
	if value == nil {
		return int32(default_)
	}
	_ = _t2224
	var _t2225 interface{}
	if hasProtoField(value, "int32_value") {
		return value.GetInt32Value()
	}
	_ = _t2225
	panic(ParseError{msg: "expected an int32 value (e.g. `1i32`) for this config field"})
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2226 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2226
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2227 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2227
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2228 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2228
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2229 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2229
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2230 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2230
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2231 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2231
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2232 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2232
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2233 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2233
	return nil
}

func (p *Parser) construct_non_cdc_relations(targets []*pb.TargetRelation) *pb.TargetRelations {
	_t2234 := &pb.PlainTargets{Targets: targets}
	_t2235 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2235.Body = &pb.TargetRelations_Plain{Plain: _t2234}
	return _t2235
}

func (p *Parser) construct_cdc_relations(inserts []*pb.TargetRelation, deletes []*pb.TargetRelation) *pb.TargetRelations {
	_t2236 := &pb.CDCTargets{Inserts: inserts, Deletes: deletes}
	_t2237 := &pb.TargetRelations{Keys: []*pb.NamedColumn{}}
	_t2237.Body = &pb.TargetRelations_Cdc{Cdc: _t2236}
	return _t2237
}

func (p *Parser) construct_synthetic_keys(marker string) []interface{} {
	var _t2238 interface{}
	if marker != "synthetic_key" {
		panic(ParseError{msg: "expected the `:synthetic_key` marker in the relation keys clause"})
	}
	_ = _t2238
	return []interface{}{[]*pb.NamedColumn{}, true}
}

func (p *Parser) construct_relations(keys []interface{}, body *pb.TargetRelations) *pb.TargetRelations {
	var _t2239 interface{}
	if hasProtoField(body, "plain") {
		_t2240 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool)}
		_t2240.Body = &pb.TargetRelations_Plain{Plain: body.GetPlain()}
		return _t2240
	}
	_ = _t2239
	_t2241 := &pb.TargetRelations{Keys: keys[0].([]*pb.NamedColumn), SyntheticKey: keys[1].(bool)}
	_t2241.Body = &pb.TargetRelations_Cdc{Cdc: body.GetCdc()}
	return _t2241
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.TargetRelations, asof string) *pb.CSVData {
	_t2242 := columns_opt
	if columns_opt == nil {
		_t2242 = []*pb.GNFColumn{}
	}
	_t2243 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2242, Asof: asof, Relations: relations_opt}
	return _t2243
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2244 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2244
	_t2245 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2245
	_t2246 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2246
	_t2247 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2247
	_t2248 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2248
	_t2249 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2249
	_t2250 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2250
	_t2251 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2251
	_t2252 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2252
	_t2253 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2253
	_t2254 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2254
	_t2255 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2255
	_t2256 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2256
	_t2257 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2257
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2258 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2258
	config := dictFromList(storage_integration_opt)
	_t2259 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2260 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2261 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2262 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2263 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2264 := &pb.StorageIntegration{Provider: _t2259, AzureSasToken: _t2260, S3Region: _t2261, S3AccessKeyId: _t2262, S3SecretAccessKey: _t2263}
	return _t2264
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2265 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2265
	_t2266 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2266
	_t2267 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2267
	_t2268 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2268
	_t2269 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2269
	_t2270 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2270
	_t2271 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2271
	_t2272 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2272
	_t2273 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2273
	_t2274 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2274.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2274.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2274
	_t2275 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2275
}

func (p *Parser) default_configure() *pb.Configure {
	_t2276 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2276
	_t2277 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2277
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
	_t2278 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2278
	_t2279 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2279
	_t2280 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2280
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2281 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2281
	_t2282 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2282
	_t2283 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2283
	_t2284 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2284
	_t2285 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2285
	_t2286 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2286
	_t2287 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2287
	_t2288 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2288
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2289 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2289
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2290 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2290
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2291 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2291
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2292 := config_dict
	if config_dict == nil {
		_t2292 = [][]interface{}{}
	}
	cfg := dictFromList(_t2292)
	_t2293 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2293
	_t2294 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2294
	_t2295 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2295
	table_props := stringMapFromPairs(table_property_pairs)
	_t2296 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2296
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1418 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1419 := p.parse_configure()
		_t1418 = _t1419
	}
	configure709 := _t1418
	var _t1420 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1421 := p.parse_sync()
		_t1420 = _t1421
	}
	sync710 := _t1420
	xs711 := []*pb.Epoch{}
	cond712 := p.matchLookaheadLiteral("(", 0)
	for cond712 {
		_t1422 := p.parse_epoch()
		item713 := _t1422
		xs711 = append(xs711, item713)
		cond712 = p.matchLookaheadLiteral("(", 0)
	}
	epochs714 := xs711
	p.consumeLiteral(")")
	_t1423 := p.default_configure()
	_t1424 := configure709
	if configure709 == nil {
		_t1424 = _t1423
	}
	_t1425 := &pb.Transaction{Epochs: epochs714, Configure: _t1424, Sync: sync710}
	result716 := _t1425
	p.recordSpan(int(span_start715), "Transaction")
	return result716
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start718 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1426 := p.parse_config_dict()
	config_dict717 := _t1426
	p.consumeLiteral(")")
	_t1427 := p.construct_configure(config_dict717)
	result719 := _t1427
	p.recordSpan(int(span_start718), "Configure")
	return result719
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs720 := [][]interface{}{}
	cond721 := p.matchLookaheadLiteral(":", 0)
	for cond721 {
		_t1428 := p.parse_config_key_value()
		item722 := _t1428
		xs720 = append(xs720, item722)
		cond721 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values723 := xs720
	p.consumeLiteral("}")
	return config_key_values723
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol724 := p.consumeTerminal("SYMBOL").Value.str
	_t1429 := p.parse_raw_value()
	raw_value725 := _t1429
	return []interface{}{symbol724, raw_value725}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start739 := int64(p.spanStart())
	var _t1430 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1430 = 12
	} else {
		var _t1431 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1431 = 11
		} else {
			var _t1432 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1432 = 12
			} else {
				var _t1433 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1434 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1434 = 1
					} else {
						var _t1435 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1435 = 0
						} else {
							_t1435 = -1
						}
						_t1434 = _t1435
					}
					_t1433 = _t1434
				} else {
					var _t1436 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1436 = 7
					} else {
						var _t1437 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1437 = 8
						} else {
							var _t1438 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1438 = 2
							} else {
								var _t1439 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1439 = 3
								} else {
									var _t1440 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1440 = 9
									} else {
										var _t1441 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1441 = 4
										} else {
											var _t1442 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1442 = 5
											} else {
												var _t1443 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1443 = 6
												} else {
													var _t1444 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1444 = 10
													} else {
														_t1444 = -1
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
					_t1433 = _t1436
				}
				_t1432 = _t1433
			}
			_t1431 = _t1432
		}
		_t1430 = _t1431
	}
	prediction726 := _t1430
	var _t1445 *pb.Value
	if prediction726 == 12 {
		_t1446 := p.parse_boolean_value()
		boolean_value738 := _t1446
		_t1447 := &pb.Value{}
		_t1447.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value738}
		_t1445 = _t1447
	} else {
		var _t1448 *pb.Value
		if prediction726 == 11 {
			p.consumeLiteral("missing")
			_t1449 := &pb.MissingValue{}
			_t1450 := &pb.Value{}
			_t1450.Value = &pb.Value_MissingValue{MissingValue: _t1449}
			_t1448 = _t1450
		} else {
			var _t1451 *pb.Value
			if prediction726 == 10 {
				decimal737 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1452 := &pb.Value{}
				_t1452.Value = &pb.Value_DecimalValue{DecimalValue: decimal737}
				_t1451 = _t1452
			} else {
				var _t1453 *pb.Value
				if prediction726 == 9 {
					int128736 := p.consumeTerminal("INT128").Value.int128
					_t1454 := &pb.Value{}
					_t1454.Value = &pb.Value_Int128Value{Int128Value: int128736}
					_t1453 = _t1454
				} else {
					var _t1455 *pb.Value
					if prediction726 == 8 {
						uint128735 := p.consumeTerminal("UINT128").Value.uint128
						_t1456 := &pb.Value{}
						_t1456.Value = &pb.Value_Uint128Value{Uint128Value: uint128735}
						_t1455 = _t1456
					} else {
						var _t1457 *pb.Value
						if prediction726 == 7 {
							uint32734 := p.consumeTerminal("UINT32").Value.u32
							_t1458 := &pb.Value{}
							_t1458.Value = &pb.Value_Uint32Value{Uint32Value: uint32734}
							_t1457 = _t1458
						} else {
							var _t1459 *pb.Value
							if prediction726 == 6 {
								float733 := p.consumeTerminal("FLOAT").Value.f64
								_t1460 := &pb.Value{}
								_t1460.Value = &pb.Value_FloatValue{FloatValue: float733}
								_t1459 = _t1460
							} else {
								var _t1461 *pb.Value
								if prediction726 == 5 {
									float32732 := p.consumeTerminal("FLOAT32").Value.f32
									_t1462 := &pb.Value{}
									_t1462.Value = &pb.Value_Float32Value{Float32Value: float32732}
									_t1461 = _t1462
								} else {
									var _t1463 *pb.Value
									if prediction726 == 4 {
										int731 := p.consumeTerminal("INT").Value.i64
										_t1464 := &pb.Value{}
										_t1464.Value = &pb.Value_IntValue{IntValue: int731}
										_t1463 = _t1464
									} else {
										var _t1465 *pb.Value
										if prediction726 == 3 {
											int32730 := p.consumeTerminal("INT32").Value.i32
											_t1466 := &pb.Value{}
											_t1466.Value = &pb.Value_Int32Value{Int32Value: int32730}
											_t1465 = _t1466
										} else {
											var _t1467 *pb.Value
											if prediction726 == 2 {
												string729 := p.consumeTerminal("STRING").Value.str
												_t1468 := &pb.Value{}
												_t1468.Value = &pb.Value_StringValue{StringValue: string729}
												_t1467 = _t1468
											} else {
												var _t1469 *pb.Value
												if prediction726 == 1 {
													_t1470 := p.parse_raw_datetime()
													raw_datetime728 := _t1470
													_t1471 := &pb.Value{}
													_t1471.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime728}
													_t1469 = _t1471
												} else {
													var _t1472 *pb.Value
													if prediction726 == 0 {
														_t1473 := p.parse_raw_date()
														raw_date727 := _t1473
														_t1474 := &pb.Value{}
														_t1474.Value = &pb.Value_DateValue{DateValue: raw_date727}
														_t1472 = _t1474
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1469 = _t1472
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
						_t1455 = _t1457
					}
					_t1453 = _t1455
				}
				_t1451 = _t1453
			}
			_t1448 = _t1451
		}
		_t1445 = _t1448
	}
	result740 := _t1445
	p.recordSpan(int(span_start739), "Value")
	return result740
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start744 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int741 := p.consumeTerminal("INT").Value.i64
	int_3742 := p.consumeTerminal("INT").Value.i64
	int_4743 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1475 := &pb.DateValue{Year: int32(int741), Month: int32(int_3742), Day: int32(int_4743)}
	result745 := _t1475
	p.recordSpan(int(span_start744), "DateValue")
	return result745
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int746 := p.consumeTerminal("INT").Value.i64
	int_3747 := p.consumeTerminal("INT").Value.i64
	int_4748 := p.consumeTerminal("INT").Value.i64
	int_5749 := p.consumeTerminal("INT").Value.i64
	int_6750 := p.consumeTerminal("INT").Value.i64
	int_7751 := p.consumeTerminal("INT").Value.i64
	var _t1476 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1476 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8752 := _t1476
	p.consumeLiteral(")")
	_t1477 := &pb.DateTimeValue{Year: int32(int746), Month: int32(int_3747), Day: int32(int_4748), Hour: int32(int_5749), Minute: int32(int_6750), Second: int32(int_7751), Microsecond: int32(deref(int_8752, 0))}
	result754 := _t1477
	p.recordSpan(int(span_start753), "DateTimeValue")
	return result754
}

func (p *Parser) parse_boolean_value() bool {
	var _t1478 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1478 = 0
	} else {
		var _t1479 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1479 = 1
		} else {
			_t1479 = -1
		}
		_t1478 = _t1479
	}
	prediction755 := _t1478
	var _t1480 bool
	if prediction755 == 1 {
		p.consumeLiteral("false")
		_t1480 = false
	} else {
		var _t1481 bool
		if prediction755 == 0 {
			p.consumeLiteral("true")
			_t1481 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1480 = _t1481
	}
	return _t1480
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start760 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs756 := []*pb.FragmentId{}
	cond757 := p.matchLookaheadLiteral(":", 0)
	for cond757 {
		_t1482 := p.parse_fragment_id()
		item758 := _t1482
		xs756 = append(xs756, item758)
		cond757 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids759 := xs756
	p.consumeLiteral(")")
	_t1483 := &pb.Sync{Fragments: fragment_ids759}
	result761 := _t1483
	p.recordSpan(int(span_start760), "Sync")
	return result761
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol762 := p.consumeTerminal("SYMBOL").Value.str
	result764 := &pb.FragmentId{Id: []byte(symbol762)}
	p.recordSpan(int(span_start763), "FragmentId")
	return result764
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1484 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1485 := p.parse_epoch_writes()
		_t1484 = _t1485
	}
	epoch_writes765 := _t1484
	var _t1486 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1487 := p.parse_epoch_reads()
		_t1486 = _t1487
	}
	epoch_reads766 := _t1486
	p.consumeLiteral(")")
	_t1488 := epoch_writes765
	if epoch_writes765 == nil {
		_t1488 = []*pb.Write{}
	}
	_t1489 := epoch_reads766
	if epoch_reads766 == nil {
		_t1489 = []*pb.Read{}
	}
	_t1490 := &pb.Epoch{Writes: _t1488, Reads: _t1489}
	result768 := _t1490
	p.recordSpan(int(span_start767), "Epoch")
	return result768
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs769 := []*pb.Write{}
	cond770 := p.matchLookaheadLiteral("(", 0)
	for cond770 {
		_t1491 := p.parse_write()
		item771 := _t1491
		xs769 = append(xs769, item771)
		cond770 = p.matchLookaheadLiteral("(", 0)
	}
	writes772 := xs769
	p.consumeLiteral(")")
	return writes772
}

func (p *Parser) parse_write() *pb.Write {
	span_start778 := int64(p.spanStart())
	var _t1492 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1493 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1493 = 1
		} else {
			var _t1494 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1494 = 3
			} else {
				var _t1495 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1495 = 0
				} else {
					var _t1496 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1496 = 2
					} else {
						_t1496 = -1
					}
					_t1495 = _t1496
				}
				_t1494 = _t1495
			}
			_t1493 = _t1494
		}
		_t1492 = _t1493
	} else {
		_t1492 = -1
	}
	prediction773 := _t1492
	var _t1497 *pb.Write
	if prediction773 == 3 {
		_t1498 := p.parse_snapshot()
		snapshot777 := _t1498
		_t1499 := &pb.Write{}
		_t1499.WriteType = &pb.Write_Snapshot{Snapshot: snapshot777}
		_t1497 = _t1499
	} else {
		var _t1500 *pb.Write
		if prediction773 == 2 {
			_t1501 := p.parse_context()
			context776 := _t1501
			_t1502 := &pb.Write{}
			_t1502.WriteType = &pb.Write_Context{Context: context776}
			_t1500 = _t1502
		} else {
			var _t1503 *pb.Write
			if prediction773 == 1 {
				_t1504 := p.parse_undefine()
				undefine775 := _t1504
				_t1505 := &pb.Write{}
				_t1505.WriteType = &pb.Write_Undefine{Undefine: undefine775}
				_t1503 = _t1505
			} else {
				var _t1506 *pb.Write
				if prediction773 == 0 {
					_t1507 := p.parse_define()
					define774 := _t1507
					_t1508 := &pb.Write{}
					_t1508.WriteType = &pb.Write_Define{Define: define774}
					_t1506 = _t1508
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1503 = _t1506
			}
			_t1500 = _t1503
		}
		_t1497 = _t1500
	}
	result779 := _t1497
	p.recordSpan(int(span_start778), "Write")
	return result779
}

func (p *Parser) parse_define() *pb.Define {
	span_start781 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1509 := p.parse_fragment()
	fragment780 := _t1509
	p.consumeLiteral(")")
	_t1510 := &pb.Define{Fragment: fragment780}
	result782 := _t1510
	p.recordSpan(int(span_start781), "Define")
	return result782
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start788 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1511 := p.parse_new_fragment_id()
	new_fragment_id783 := _t1511
	xs784 := []*pb.Declaration{}
	cond785 := p.matchLookaheadLiteral("(", 0)
	for cond785 {
		_t1512 := p.parse_declaration()
		item786 := _t1512
		xs784 = append(xs784, item786)
		cond785 = p.matchLookaheadLiteral("(", 0)
	}
	declarations787 := xs784
	p.consumeLiteral(")")
	result789 := p.constructFragment(new_fragment_id783, declarations787)
	p.recordSpan(int(span_start788), "Fragment")
	return result789
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start791 := int64(p.spanStart())
	_t1513 := p.parse_fragment_id()
	fragment_id790 := _t1513
	p.startFragment(fragment_id790)
	result792 := fragment_id790
	p.recordSpan(int(span_start791), "FragmentId")
	return result792
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start798 := int64(p.spanStart())
	var _t1514 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1515 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1515 = 3
		} else {
			var _t1516 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1516 = 2
			} else {
				var _t1517 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1517 = 3
				} else {
					var _t1518 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1518 = 0
					} else {
						var _t1519 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1519 = 3
						} else {
							var _t1520 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1520 = 3
							} else {
								var _t1521 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1521 = 1
								} else {
									_t1521 = -1
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
	} else {
		_t1514 = -1
	}
	prediction793 := _t1514
	var _t1522 *pb.Declaration
	if prediction793 == 3 {
		_t1523 := p.parse_data()
		data797 := _t1523
		_t1524 := &pb.Declaration{}
		_t1524.DeclarationType = &pb.Declaration_Data{Data: data797}
		_t1522 = _t1524
	} else {
		var _t1525 *pb.Declaration
		if prediction793 == 2 {
			_t1526 := p.parse_constraint()
			constraint796 := _t1526
			_t1527 := &pb.Declaration{}
			_t1527.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint796}
			_t1525 = _t1527
		} else {
			var _t1528 *pb.Declaration
			if prediction793 == 1 {
				_t1529 := p.parse_algorithm()
				algorithm795 := _t1529
				_t1530 := &pb.Declaration{}
				_t1530.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm795}
				_t1528 = _t1530
			} else {
				var _t1531 *pb.Declaration
				if prediction793 == 0 {
					_t1532 := p.parse_def()
					def794 := _t1532
					_t1533 := &pb.Declaration{}
					_t1533.DeclarationType = &pb.Declaration_Def{Def: def794}
					_t1531 = _t1533
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1528 = _t1531
			}
			_t1525 = _t1528
		}
		_t1522 = _t1525
	}
	result799 := _t1522
	p.recordSpan(int(span_start798), "Declaration")
	return result799
}

func (p *Parser) parse_def() *pb.Def {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1534 := p.parse_relation_id()
	relation_id800 := _t1534
	_t1535 := p.parse_abstraction()
	abstraction801 := _t1535
	var _t1536 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1537 := p.parse_attrs()
		_t1536 = _t1537
	}
	attrs802 := _t1536
	p.consumeLiteral(")")
	_t1538 := attrs802
	if attrs802 == nil {
		_t1538 = []*pb.Attribute{}
	}
	_t1539 := &pb.Def{Name: relation_id800, Body: abstraction801, Attrs: _t1538}
	result804 := _t1539
	p.recordSpan(int(span_start803), "Def")
	return result804
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start808 := int64(p.spanStart())
	var _t1540 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1540 = 0
	} else {
		var _t1541 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1541 = 1
		} else {
			_t1541 = -1
		}
		_t1540 = _t1541
	}
	prediction805 := _t1540
	var _t1542 *pb.RelationId
	if prediction805 == 1 {
		uint128807 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128807
		_t1542 = &pb.RelationId{IdLow: uint128807.Low, IdHigh: uint128807.High}
	} else {
		var _t1543 *pb.RelationId
		if prediction805 == 0 {
			p.consumeLiteral(":")
			symbol806 := p.consumeTerminal("SYMBOL").Value.str
			_t1543 = p.relationIdFromString(symbol806)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1542 = _t1543
	}
	result809 := _t1542
	p.recordSpan(int(span_start808), "RelationId")
	return result809
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1544 := p.parse_bindings()
	bindings810 := _t1544
	_t1545 := p.parse_formula()
	formula811 := _t1545
	p.consumeLiteral(")")
	_t1546 := &pb.Abstraction{Vars: listConcat(bindings810[0].([]*pb.Binding), bindings810[1].([]*pb.Binding)), Value: formula811}
	result813 := _t1546
	p.recordSpan(int(span_start812), "Abstraction")
	return result813
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs814 := []*pb.Binding{}
	cond815 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond815 {
		_t1547 := p.parse_binding()
		item816 := _t1547
		xs814 = append(xs814, item816)
		cond815 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings817 := xs814
	var _t1548 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1549 := p.parse_value_bindings()
		_t1548 = _t1549
	}
	value_bindings818 := _t1548
	p.consumeLiteral("]")
	_t1550 := value_bindings818
	if value_bindings818 == nil {
		_t1550 = []*pb.Binding{}
	}
	return []interface{}{bindings817, _t1550}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start821 := int64(p.spanStart())
	symbol819 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1551 := p.parse_type()
	type820 := _t1551
	_t1552 := &pb.Var{Name: symbol819}
	_t1553 := &pb.Binding{Var: _t1552, Type: type820}
	result822 := _t1553
	p.recordSpan(int(span_start821), "Binding")
	return result822
}

func (p *Parser) parse_type() *pb.Type {
	span_start838 := int64(p.spanStart())
	var _t1554 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1554 = 0
	} else {
		var _t1555 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1555 = 13
		} else {
			var _t1556 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1556 = 4
			} else {
				var _t1557 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1557 = 1
				} else {
					var _t1558 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1558 = 8
					} else {
						var _t1559 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1559 = 11
						} else {
							var _t1560 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1560 = 5
							} else {
								var _t1561 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1561 = 2
								} else {
									var _t1562 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1562 = 12
									} else {
										var _t1563 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1563 = 3
										} else {
											var _t1564 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1564 = 7
											} else {
												var _t1565 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1565 = 6
												} else {
													var _t1566 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1566 = 10
													} else {
														var _t1567 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1567 = 9
														} else {
															_t1567 = -1
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
	prediction823 := _t1554
	var _t1568 *pb.Type
	if prediction823 == 13 {
		_t1569 := p.parse_uint32_type()
		uint32_type837 := _t1569
		_t1570 := &pb.Type{}
		_t1570.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type837}
		_t1568 = _t1570
	} else {
		var _t1571 *pb.Type
		if prediction823 == 12 {
			_t1572 := p.parse_float32_type()
			float32_type836 := _t1572
			_t1573 := &pb.Type{}
			_t1573.Type = &pb.Type_Float32Type{Float32Type: float32_type836}
			_t1571 = _t1573
		} else {
			var _t1574 *pb.Type
			if prediction823 == 11 {
				_t1575 := p.parse_int32_type()
				int32_type835 := _t1575
				_t1576 := &pb.Type{}
				_t1576.Type = &pb.Type_Int32Type{Int32Type: int32_type835}
				_t1574 = _t1576
			} else {
				var _t1577 *pb.Type
				if prediction823 == 10 {
					_t1578 := p.parse_boolean_type()
					boolean_type834 := _t1578
					_t1579 := &pb.Type{}
					_t1579.Type = &pb.Type_BooleanType{BooleanType: boolean_type834}
					_t1577 = _t1579
				} else {
					var _t1580 *pb.Type
					if prediction823 == 9 {
						_t1581 := p.parse_decimal_type()
						decimal_type833 := _t1581
						_t1582 := &pb.Type{}
						_t1582.Type = &pb.Type_DecimalType{DecimalType: decimal_type833}
						_t1580 = _t1582
					} else {
						var _t1583 *pb.Type
						if prediction823 == 8 {
							_t1584 := p.parse_missing_type()
							missing_type832 := _t1584
							_t1585 := &pb.Type{}
							_t1585.Type = &pb.Type_MissingType{MissingType: missing_type832}
							_t1583 = _t1585
						} else {
							var _t1586 *pb.Type
							if prediction823 == 7 {
								_t1587 := p.parse_datetime_type()
								datetime_type831 := _t1587
								_t1588 := &pb.Type{}
								_t1588.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type831}
								_t1586 = _t1588
							} else {
								var _t1589 *pb.Type
								if prediction823 == 6 {
									_t1590 := p.parse_date_type()
									date_type830 := _t1590
									_t1591 := &pb.Type{}
									_t1591.Type = &pb.Type_DateType{DateType: date_type830}
									_t1589 = _t1591
								} else {
									var _t1592 *pb.Type
									if prediction823 == 5 {
										_t1593 := p.parse_int128_type()
										int128_type829 := _t1593
										_t1594 := &pb.Type{}
										_t1594.Type = &pb.Type_Int128Type{Int128Type: int128_type829}
										_t1592 = _t1594
									} else {
										var _t1595 *pb.Type
										if prediction823 == 4 {
											_t1596 := p.parse_uint128_type()
											uint128_type828 := _t1596
											_t1597 := &pb.Type{}
											_t1597.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type828}
											_t1595 = _t1597
										} else {
											var _t1598 *pb.Type
											if prediction823 == 3 {
												_t1599 := p.parse_float_type()
												float_type827 := _t1599
												_t1600 := &pb.Type{}
												_t1600.Type = &pb.Type_FloatType{FloatType: float_type827}
												_t1598 = _t1600
											} else {
												var _t1601 *pb.Type
												if prediction823 == 2 {
													_t1602 := p.parse_int_type()
													int_type826 := _t1602
													_t1603 := &pb.Type{}
													_t1603.Type = &pb.Type_IntType{IntType: int_type826}
													_t1601 = _t1603
												} else {
													var _t1604 *pb.Type
													if prediction823 == 1 {
														_t1605 := p.parse_string_type()
														string_type825 := _t1605
														_t1606 := &pb.Type{}
														_t1606.Type = &pb.Type_StringType{StringType: string_type825}
														_t1604 = _t1606
													} else {
														var _t1607 *pb.Type
														if prediction823 == 0 {
															_t1608 := p.parse_unspecified_type()
															unspecified_type824 := _t1608
															_t1609 := &pb.Type{}
															_t1609.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type824}
															_t1607 = _t1609
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1571 = _t1574
		}
		_t1568 = _t1571
	}
	result839 := _t1568
	p.recordSpan(int(span_start838), "Type")
	return result839
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start840 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1610 := &pb.UnspecifiedType{}
	result841 := _t1610
	p.recordSpan(int(span_start840), "UnspecifiedType")
	return result841
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1611 := &pb.StringType{}
	result843 := _t1611
	p.recordSpan(int(span_start842), "StringType")
	return result843
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start844 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1612 := &pb.IntType{}
	result845 := _t1612
	p.recordSpan(int(span_start844), "IntType")
	return result845
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start846 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1613 := &pb.FloatType{}
	result847 := _t1613
	p.recordSpan(int(span_start846), "FloatType")
	return result847
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1614 := &pb.UInt128Type{}
	result849 := _t1614
	p.recordSpan(int(span_start848), "UInt128Type")
	return result849
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start850 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1615 := &pb.Int128Type{}
	result851 := _t1615
	p.recordSpan(int(span_start850), "Int128Type")
	return result851
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1616 := &pb.DateType{}
	result853 := _t1616
	p.recordSpan(int(span_start852), "DateType")
	return result853
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1617 := &pb.DateTimeType{}
	result855 := _t1617
	p.recordSpan(int(span_start854), "DateTimeType")
	return result855
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start856 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1618 := &pb.MissingType{}
	result857 := _t1618
	p.recordSpan(int(span_start856), "MissingType")
	return result857
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int858 := p.consumeTerminal("INT").Value.i64
	int_3859 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1619 := &pb.DecimalType{Precision: int32(int858), Scale: int32(int_3859)}
	result861 := _t1619
	p.recordSpan(int(span_start860), "DecimalType")
	return result861
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start862 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1620 := &pb.BooleanType{}
	result863 := _t1620
	p.recordSpan(int(span_start862), "BooleanType")
	return result863
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1621 := &pb.Int32Type{}
	result865 := _t1621
	p.recordSpan(int(span_start864), "Int32Type")
	return result865
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1622 := &pb.Float32Type{}
	result867 := _t1622
	p.recordSpan(int(span_start866), "Float32Type")
	return result867
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start868 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1623 := &pb.UInt32Type{}
	result869 := _t1623
	p.recordSpan(int(span_start868), "UInt32Type")
	return result869
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs870 := []*pb.Binding{}
	cond871 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond871 {
		_t1624 := p.parse_binding()
		item872 := _t1624
		xs870 = append(xs870, item872)
		cond871 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings873 := xs870
	return bindings873
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start888 := int64(p.spanStart())
	var _t1625 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1626 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1626 = 0
		} else {
			var _t1627 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1627 = 11
			} else {
				var _t1628 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1628 = 3
				} else {
					var _t1629 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1629 = 10
					} else {
						var _t1630 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1630 = 9
						} else {
							var _t1631 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1631 = 5
							} else {
								var _t1632 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1632 = 6
								} else {
									var _t1633 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1633 = 7
									} else {
										var _t1634 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1634 = 1
										} else {
											var _t1635 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1635 = 2
											} else {
												var _t1636 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1636 = 12
												} else {
													var _t1637 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1637 = 8
													} else {
														var _t1638 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1638 = 4
														} else {
															var _t1639 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1639 = 10
															} else {
																var _t1640 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1640 = 10
																} else {
																	var _t1641 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1641 = 10
																	} else {
																		var _t1642 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1642 = 10
																		} else {
																			var _t1643 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1643 = 10
																			} else {
																				var _t1644 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1644 = 10
																				} else {
																					var _t1645 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1645 = 10
																					} else {
																						var _t1646 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1646 = 10
																						} else {
																							var _t1647 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1647 = 10
																							} else {
																								_t1647 = -1
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
	} else {
		_t1625 = -1
	}
	prediction874 := _t1625
	var _t1648 *pb.Formula
	if prediction874 == 12 {
		_t1649 := p.parse_cast()
		cast887 := _t1649
		_t1650 := &pb.Formula{}
		_t1650.FormulaType = &pb.Formula_Cast{Cast: cast887}
		_t1648 = _t1650
	} else {
		var _t1651 *pb.Formula
		if prediction874 == 11 {
			_t1652 := p.parse_rel_atom()
			rel_atom886 := _t1652
			_t1653 := &pb.Formula{}
			_t1653.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom886}
			_t1651 = _t1653
		} else {
			var _t1654 *pb.Formula
			if prediction874 == 10 {
				_t1655 := p.parse_primitive()
				primitive885 := _t1655
				_t1656 := &pb.Formula{}
				_t1656.FormulaType = &pb.Formula_Primitive{Primitive: primitive885}
				_t1654 = _t1656
			} else {
				var _t1657 *pb.Formula
				if prediction874 == 9 {
					_t1658 := p.parse_pragma()
					pragma884 := _t1658
					_t1659 := &pb.Formula{}
					_t1659.FormulaType = &pb.Formula_Pragma{Pragma: pragma884}
					_t1657 = _t1659
				} else {
					var _t1660 *pb.Formula
					if prediction874 == 8 {
						_t1661 := p.parse_atom()
						atom883 := _t1661
						_t1662 := &pb.Formula{}
						_t1662.FormulaType = &pb.Formula_Atom{Atom: atom883}
						_t1660 = _t1662
					} else {
						var _t1663 *pb.Formula
						if prediction874 == 7 {
							_t1664 := p.parse_ffi()
							ffi882 := _t1664
							_t1665 := &pb.Formula{}
							_t1665.FormulaType = &pb.Formula_Ffi{Ffi: ffi882}
							_t1663 = _t1665
						} else {
							var _t1666 *pb.Formula
							if prediction874 == 6 {
								_t1667 := p.parse_not()
								not881 := _t1667
								_t1668 := &pb.Formula{}
								_t1668.FormulaType = &pb.Formula_Not{Not: not881}
								_t1666 = _t1668
							} else {
								var _t1669 *pb.Formula
								if prediction874 == 5 {
									_t1670 := p.parse_disjunction()
									disjunction880 := _t1670
									_t1671 := &pb.Formula{}
									_t1671.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction880}
									_t1669 = _t1671
								} else {
									var _t1672 *pb.Formula
									if prediction874 == 4 {
										_t1673 := p.parse_conjunction()
										conjunction879 := _t1673
										_t1674 := &pb.Formula{}
										_t1674.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction879}
										_t1672 = _t1674
									} else {
										var _t1675 *pb.Formula
										if prediction874 == 3 {
											_t1676 := p.parse_reduce()
											reduce878 := _t1676
											_t1677 := &pb.Formula{}
											_t1677.FormulaType = &pb.Formula_Reduce{Reduce: reduce878}
											_t1675 = _t1677
										} else {
											var _t1678 *pb.Formula
											if prediction874 == 2 {
												_t1679 := p.parse_exists()
												exists877 := _t1679
												_t1680 := &pb.Formula{}
												_t1680.FormulaType = &pb.Formula_Exists{Exists: exists877}
												_t1678 = _t1680
											} else {
												var _t1681 *pb.Formula
												if prediction874 == 1 {
													_t1682 := p.parse_false()
													false876 := _t1682
													_t1683 := &pb.Formula{}
													_t1683.FormulaType = &pb.Formula_Disjunction{Disjunction: false876}
													_t1681 = _t1683
												} else {
													var _t1684 *pb.Formula
													if prediction874 == 0 {
														_t1685 := p.parse_true()
														true875 := _t1685
														_t1686 := &pb.Formula{}
														_t1686.FormulaType = &pb.Formula_Conjunction{Conjunction: true875}
														_t1684 = _t1686
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1651 = _t1654
		}
		_t1648 = _t1651
	}
	result889 := _t1648
	p.recordSpan(int(span_start888), "Formula")
	return result889
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start890 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1687 := &pb.Conjunction{Args: []*pb.Formula{}}
	result891 := _t1687
	p.recordSpan(int(span_start890), "Conjunction")
	return result891
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start892 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1688 := &pb.Disjunction{Args: []*pb.Formula{}}
	result893 := _t1688
	p.recordSpan(int(span_start892), "Disjunction")
	return result893
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1689 := p.parse_bindings()
	bindings894 := _t1689
	_t1690 := p.parse_formula()
	formula895 := _t1690
	p.consumeLiteral(")")
	_t1691 := &pb.Abstraction{Vars: listConcat(bindings894[0].([]*pb.Binding), bindings894[1].([]*pb.Binding)), Value: formula895}
	_t1692 := &pb.Exists{Body: _t1691}
	result897 := _t1692
	p.recordSpan(int(span_start896), "Exists")
	return result897
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1693 := p.parse_abstraction()
	abstraction898 := _t1693
	_t1694 := p.parse_abstraction()
	abstraction_3899 := _t1694
	_t1695 := p.parse_terms()
	terms900 := _t1695
	p.consumeLiteral(")")
	_t1696 := &pb.Reduce{Op: abstraction898, Body: abstraction_3899, Terms: terms900}
	result902 := _t1696
	p.recordSpan(int(span_start901), "Reduce")
	return result902
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs903 := []*pb.Term{}
	cond904 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond904 {
		_t1697 := p.parse_term()
		item905 := _t1697
		xs903 = append(xs903, item905)
		cond904 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms906 := xs903
	p.consumeLiteral(")")
	return terms906
}

func (p *Parser) parse_term() *pb.Term {
	span_start910 := int64(p.spanStart())
	var _t1698 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1698 = 1
	} else {
		var _t1699 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1699 = 1
		} else {
			var _t1700 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1700 = 1
			} else {
				var _t1701 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1701 = 1
				} else {
					var _t1702 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1702 = 0
					} else {
						var _t1703 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1703 = 1
						} else {
							var _t1704 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1704 = 1
							} else {
								var _t1705 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1705 = 1
								} else {
									var _t1706 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1706 = 1
									} else {
										var _t1707 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1707 = 1
										} else {
											var _t1708 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1708 = 1
											} else {
												var _t1709 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1709 = 1
												} else {
													var _t1710 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1710 = 1
													} else {
														var _t1711 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1711 = 1
														} else {
															_t1711 = -1
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
	prediction907 := _t1698
	var _t1712 *pb.Term
	if prediction907 == 1 {
		_t1713 := p.parse_value()
		value909 := _t1713
		_t1714 := &pb.Term{}
		_t1714.TermType = &pb.Term_Constant{Constant: value909}
		_t1712 = _t1714
	} else {
		var _t1715 *pb.Term
		if prediction907 == 0 {
			_t1716 := p.parse_var()
			var908 := _t1716
			_t1717 := &pb.Term{}
			_t1717.TermType = &pb.Term_Var{Var: var908}
			_t1715 = _t1717
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1712 = _t1715
	}
	result911 := _t1712
	p.recordSpan(int(span_start910), "Term")
	return result911
}

func (p *Parser) parse_var() *pb.Var {
	span_start913 := int64(p.spanStart())
	symbol912 := p.consumeTerminal("SYMBOL").Value.str
	_t1718 := &pb.Var{Name: symbol912}
	result914 := _t1718
	p.recordSpan(int(span_start913), "Var")
	return result914
}

func (p *Parser) parse_value() *pb.Value {
	span_start928 := int64(p.spanStart())
	var _t1719 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1719 = 12
	} else {
		var _t1720 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1720 = 11
		} else {
			var _t1721 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1721 = 12
			} else {
				var _t1722 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1723 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1723 = 1
					} else {
						var _t1724 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1724 = 0
						} else {
							_t1724 = -1
						}
						_t1723 = _t1724
					}
					_t1722 = _t1723
				} else {
					var _t1725 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1725 = 7
					} else {
						var _t1726 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1726 = 8
						} else {
							var _t1727 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1727 = 2
							} else {
								var _t1728 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1728 = 3
								} else {
									var _t1729 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1729 = 9
									} else {
										var _t1730 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1730 = 4
										} else {
											var _t1731 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1731 = 5
											} else {
												var _t1732 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1732 = 6
												} else {
													var _t1733 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1733 = 10
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
					_t1722 = _t1725
				}
				_t1721 = _t1722
			}
			_t1720 = _t1721
		}
		_t1719 = _t1720
	}
	prediction915 := _t1719
	var _t1734 *pb.Value
	if prediction915 == 12 {
		_t1735 := p.parse_boolean_value()
		boolean_value927 := _t1735
		_t1736 := &pb.Value{}
		_t1736.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value927}
		_t1734 = _t1736
	} else {
		var _t1737 *pb.Value
		if prediction915 == 11 {
			p.consumeLiteral("missing")
			_t1738 := &pb.MissingValue{}
			_t1739 := &pb.Value{}
			_t1739.Value = &pb.Value_MissingValue{MissingValue: _t1738}
			_t1737 = _t1739
		} else {
			var _t1740 *pb.Value
			if prediction915 == 10 {
				formatted_decimal926 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1741 := &pb.Value{}
				_t1741.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal926}
				_t1740 = _t1741
			} else {
				var _t1742 *pb.Value
				if prediction915 == 9 {
					formatted_int128925 := p.consumeTerminal("INT128").Value.int128
					_t1743 := &pb.Value{}
					_t1743.Value = &pb.Value_Int128Value{Int128Value: formatted_int128925}
					_t1742 = _t1743
				} else {
					var _t1744 *pb.Value
					if prediction915 == 8 {
						formatted_uint128924 := p.consumeTerminal("UINT128").Value.uint128
						_t1745 := &pb.Value{}
						_t1745.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128924}
						_t1744 = _t1745
					} else {
						var _t1746 *pb.Value
						if prediction915 == 7 {
							formatted_uint32923 := p.consumeTerminal("UINT32").Value.u32
							_t1747 := &pb.Value{}
							_t1747.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32923}
							_t1746 = _t1747
						} else {
							var _t1748 *pb.Value
							if prediction915 == 6 {
								formatted_float922 := p.consumeTerminal("FLOAT").Value.f64
								_t1749 := &pb.Value{}
								_t1749.Value = &pb.Value_FloatValue{FloatValue: formatted_float922}
								_t1748 = _t1749
							} else {
								var _t1750 *pb.Value
								if prediction915 == 5 {
									formatted_float32921 := p.consumeTerminal("FLOAT32").Value.f32
									_t1751 := &pb.Value{}
									_t1751.Value = &pb.Value_Float32Value{Float32Value: formatted_float32921}
									_t1750 = _t1751
								} else {
									var _t1752 *pb.Value
									if prediction915 == 4 {
										formatted_int920 := p.consumeTerminal("INT").Value.i64
										_t1753 := &pb.Value{}
										_t1753.Value = &pb.Value_IntValue{IntValue: formatted_int920}
										_t1752 = _t1753
									} else {
										var _t1754 *pb.Value
										if prediction915 == 3 {
											formatted_int32919 := p.consumeTerminal("INT32").Value.i32
											_t1755 := &pb.Value{}
											_t1755.Value = &pb.Value_Int32Value{Int32Value: formatted_int32919}
											_t1754 = _t1755
										} else {
											var _t1756 *pb.Value
											if prediction915 == 2 {
												formatted_string918 := p.consumeTerminal("STRING").Value.str
												_t1757 := &pb.Value{}
												_t1757.Value = &pb.Value_StringValue{StringValue: formatted_string918}
												_t1756 = _t1757
											} else {
												var _t1758 *pb.Value
												if prediction915 == 1 {
													_t1759 := p.parse_datetime()
													datetime917 := _t1759
													_t1760 := &pb.Value{}
													_t1760.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime917}
													_t1758 = _t1760
												} else {
													var _t1761 *pb.Value
													if prediction915 == 0 {
														_t1762 := p.parse_date()
														date916 := _t1762
														_t1763 := &pb.Value{}
														_t1763.Value = &pb.Value_DateValue{DateValue: date916}
														_t1761 = _t1763
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1758 = _t1761
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
						_t1744 = _t1746
					}
					_t1742 = _t1744
				}
				_t1740 = _t1742
			}
			_t1737 = _t1740
		}
		_t1734 = _t1737
	}
	result929 := _t1734
	p.recordSpan(int(span_start928), "Value")
	return result929
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start933 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int930 := p.consumeTerminal("INT").Value.i64
	formatted_int_3931 := p.consumeTerminal("INT").Value.i64
	formatted_int_4932 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1764 := &pb.DateValue{Year: int32(formatted_int930), Month: int32(formatted_int_3931), Day: int32(formatted_int_4932)}
	result934 := _t1764
	p.recordSpan(int(span_start933), "DateValue")
	return result934
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int935 := p.consumeTerminal("INT").Value.i64
	formatted_int_3936 := p.consumeTerminal("INT").Value.i64
	formatted_int_4937 := p.consumeTerminal("INT").Value.i64
	formatted_int_5938 := p.consumeTerminal("INT").Value.i64
	formatted_int_6939 := p.consumeTerminal("INT").Value.i64
	formatted_int_7940 := p.consumeTerminal("INT").Value.i64
	var _t1765 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1765 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8941 := _t1765
	p.consumeLiteral(")")
	_t1766 := &pb.DateTimeValue{Year: int32(formatted_int935), Month: int32(formatted_int_3936), Day: int32(formatted_int_4937), Hour: int32(formatted_int_5938), Minute: int32(formatted_int_6939), Second: int32(formatted_int_7940), Microsecond: int32(deref(formatted_int_8941, 0))}
	result943 := _t1766
	p.recordSpan(int(span_start942), "DateTimeValue")
	return result943
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs944 := []*pb.Formula{}
	cond945 := p.matchLookaheadLiteral("(", 0)
	for cond945 {
		_t1767 := p.parse_formula()
		item946 := _t1767
		xs944 = append(xs944, item946)
		cond945 = p.matchLookaheadLiteral("(", 0)
	}
	formulas947 := xs944
	p.consumeLiteral(")")
	_t1768 := &pb.Conjunction{Args: formulas947}
	result949 := _t1768
	p.recordSpan(int(span_start948), "Conjunction")
	return result949
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start954 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs950 := []*pb.Formula{}
	cond951 := p.matchLookaheadLiteral("(", 0)
	for cond951 {
		_t1769 := p.parse_formula()
		item952 := _t1769
		xs950 = append(xs950, item952)
		cond951 = p.matchLookaheadLiteral("(", 0)
	}
	formulas953 := xs950
	p.consumeLiteral(")")
	_t1770 := &pb.Disjunction{Args: formulas953}
	result955 := _t1770
	p.recordSpan(int(span_start954), "Disjunction")
	return result955
}

func (p *Parser) parse_not() *pb.Not {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1771 := p.parse_formula()
	formula956 := _t1771
	p.consumeLiteral(")")
	_t1772 := &pb.Not{Arg: formula956}
	result958 := _t1772
	p.recordSpan(int(span_start957), "Not")
	return result958
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start962 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1773 := p.parse_name()
	name959 := _t1773
	_t1774 := p.parse_ffi_args()
	ffi_args960 := _t1774
	_t1775 := p.parse_terms()
	terms961 := _t1775
	p.consumeLiteral(")")
	_t1776 := &pb.FFI{Name: name959, Args: ffi_args960, Terms: terms961}
	result963 := _t1776
	p.recordSpan(int(span_start962), "FFI")
	return result963
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol964 := p.consumeTerminal("SYMBOL").Value.str
	return symbol964
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs965 := []*pb.Abstraction{}
	cond966 := p.matchLookaheadLiteral("(", 0)
	for cond966 {
		_t1777 := p.parse_abstraction()
		item967 := _t1777
		xs965 = append(xs965, item967)
		cond966 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions968 := xs965
	p.consumeLiteral(")")
	return abstractions968
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1778 := p.parse_relation_id()
	relation_id969 := _t1778
	xs970 := []*pb.Term{}
	cond971 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond971 {
		_t1779 := p.parse_term()
		item972 := _t1779
		xs970 = append(xs970, item972)
		cond971 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms973 := xs970
	p.consumeLiteral(")")
	_t1780 := &pb.Atom{Name: relation_id969, Terms: terms973}
	result975 := _t1780
	p.recordSpan(int(span_start974), "Atom")
	return result975
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start981 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1781 := p.parse_name()
	name976 := _t1781
	xs977 := []*pb.Term{}
	cond978 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond978 {
		_t1782 := p.parse_term()
		item979 := _t1782
		xs977 = append(xs977, item979)
		cond978 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms980 := xs977
	p.consumeLiteral(")")
	_t1783 := &pb.Pragma{Name: name976, Terms: terms980}
	result982 := _t1783
	p.recordSpan(int(span_start981), "Pragma")
	return result982
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start998 := int64(p.spanStart())
	var _t1784 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1785 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1785 = 9
		} else {
			var _t1786 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1786 = 4
			} else {
				var _t1787 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1787 = 3
				} else {
					var _t1788 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1788 = 0
					} else {
						var _t1789 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1789 = 2
						} else {
							var _t1790 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1790 = 1
							} else {
								var _t1791 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1791 = 8
								} else {
									var _t1792 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1792 = 6
									} else {
										var _t1793 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1793 = 5
										} else {
											var _t1794 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1794 = 7
											} else {
												_t1794 = -1
											}
											_t1793 = _t1794
										}
										_t1792 = _t1793
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
	} else {
		_t1784 = -1
	}
	prediction983 := _t1784
	var _t1795 *pb.Primitive
	if prediction983 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1796 := p.parse_name()
		name993 := _t1796
		xs994 := []*pb.RelTerm{}
		cond995 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond995 {
			_t1797 := p.parse_rel_term()
			item996 := _t1797
			xs994 = append(xs994, item996)
			cond995 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms997 := xs994
		p.consumeLiteral(")")
		_t1798 := &pb.Primitive{Name: name993, Terms: rel_terms997}
		_t1795 = _t1798
	} else {
		var _t1799 *pb.Primitive
		if prediction983 == 8 {
			_t1800 := p.parse_divide()
			divide992 := _t1800
			_t1799 = divide992
		} else {
			var _t1801 *pb.Primitive
			if prediction983 == 7 {
				_t1802 := p.parse_multiply()
				multiply991 := _t1802
				_t1801 = multiply991
			} else {
				var _t1803 *pb.Primitive
				if prediction983 == 6 {
					_t1804 := p.parse_minus()
					minus990 := _t1804
					_t1803 = minus990
				} else {
					var _t1805 *pb.Primitive
					if prediction983 == 5 {
						_t1806 := p.parse_add()
						add989 := _t1806
						_t1805 = add989
					} else {
						var _t1807 *pb.Primitive
						if prediction983 == 4 {
							_t1808 := p.parse_gt_eq()
							gt_eq988 := _t1808
							_t1807 = gt_eq988
						} else {
							var _t1809 *pb.Primitive
							if prediction983 == 3 {
								_t1810 := p.parse_gt()
								gt987 := _t1810
								_t1809 = gt987
							} else {
								var _t1811 *pb.Primitive
								if prediction983 == 2 {
									_t1812 := p.parse_lt_eq()
									lt_eq986 := _t1812
									_t1811 = lt_eq986
								} else {
									var _t1813 *pb.Primitive
									if prediction983 == 1 {
										_t1814 := p.parse_lt()
										lt985 := _t1814
										_t1813 = lt985
									} else {
										var _t1815 *pb.Primitive
										if prediction983 == 0 {
											_t1816 := p.parse_eq()
											eq984 := _t1816
											_t1815 = eq984
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1803 = _t1805
				}
				_t1801 = _t1803
			}
			_t1799 = _t1801
		}
		_t1795 = _t1799
	}
	result999 := _t1795
	p.recordSpan(int(span_start998), "Primitive")
	return result999
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1817 := p.parse_term()
	term1000 := _t1817
	_t1818 := p.parse_term()
	term_31001 := _t1818
	p.consumeLiteral(")")
	_t1819 := &pb.RelTerm{}
	_t1819.RelTermType = &pb.RelTerm_Term{Term: term1000}
	_t1820 := &pb.RelTerm{}
	_t1820.RelTermType = &pb.RelTerm_Term{Term: term_31001}
	_t1821 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1819, _t1820}}
	result1003 := _t1821
	p.recordSpan(int(span_start1002), "Primitive")
	return result1003
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1006 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1822 := p.parse_term()
	term1004 := _t1822
	_t1823 := p.parse_term()
	term_31005 := _t1823
	p.consumeLiteral(")")
	_t1824 := &pb.RelTerm{}
	_t1824.RelTermType = &pb.RelTerm_Term{Term: term1004}
	_t1825 := &pb.RelTerm{}
	_t1825.RelTermType = &pb.RelTerm_Term{Term: term_31005}
	_t1826 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1824, _t1825}}
	result1007 := _t1826
	p.recordSpan(int(span_start1006), "Primitive")
	return result1007
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1010 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1827 := p.parse_term()
	term1008 := _t1827
	_t1828 := p.parse_term()
	term_31009 := _t1828
	p.consumeLiteral(")")
	_t1829 := &pb.RelTerm{}
	_t1829.RelTermType = &pb.RelTerm_Term{Term: term1008}
	_t1830 := &pb.RelTerm{}
	_t1830.RelTermType = &pb.RelTerm_Term{Term: term_31009}
	_t1831 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1829, _t1830}}
	result1011 := _t1831
	p.recordSpan(int(span_start1010), "Primitive")
	return result1011
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1832 := p.parse_term()
	term1012 := _t1832
	_t1833 := p.parse_term()
	term_31013 := _t1833
	p.consumeLiteral(")")
	_t1834 := &pb.RelTerm{}
	_t1834.RelTermType = &pb.RelTerm_Term{Term: term1012}
	_t1835 := &pb.RelTerm{}
	_t1835.RelTermType = &pb.RelTerm_Term{Term: term_31013}
	_t1836 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1834, _t1835}}
	result1015 := _t1836
	p.recordSpan(int(span_start1014), "Primitive")
	return result1015
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1837 := p.parse_term()
	term1016 := _t1837
	_t1838 := p.parse_term()
	term_31017 := _t1838
	p.consumeLiteral(")")
	_t1839 := &pb.RelTerm{}
	_t1839.RelTermType = &pb.RelTerm_Term{Term: term1016}
	_t1840 := &pb.RelTerm{}
	_t1840.RelTermType = &pb.RelTerm_Term{Term: term_31017}
	_t1841 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1839, _t1840}}
	result1019 := _t1841
	p.recordSpan(int(span_start1018), "Primitive")
	return result1019
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1023 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1842 := p.parse_term()
	term1020 := _t1842
	_t1843 := p.parse_term()
	term_31021 := _t1843
	_t1844 := p.parse_term()
	term_41022 := _t1844
	p.consumeLiteral(")")
	_t1845 := &pb.RelTerm{}
	_t1845.RelTermType = &pb.RelTerm_Term{Term: term1020}
	_t1846 := &pb.RelTerm{}
	_t1846.RelTermType = &pb.RelTerm_Term{Term: term_31021}
	_t1847 := &pb.RelTerm{}
	_t1847.RelTermType = &pb.RelTerm_Term{Term: term_41022}
	_t1848 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1845, _t1846, _t1847}}
	result1024 := _t1848
	p.recordSpan(int(span_start1023), "Primitive")
	return result1024
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1849 := p.parse_term()
	term1025 := _t1849
	_t1850 := p.parse_term()
	term_31026 := _t1850
	_t1851 := p.parse_term()
	term_41027 := _t1851
	p.consumeLiteral(")")
	_t1852 := &pb.RelTerm{}
	_t1852.RelTermType = &pb.RelTerm_Term{Term: term1025}
	_t1853 := &pb.RelTerm{}
	_t1853.RelTermType = &pb.RelTerm_Term{Term: term_31026}
	_t1854 := &pb.RelTerm{}
	_t1854.RelTermType = &pb.RelTerm_Term{Term: term_41027}
	_t1855 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1852, _t1853, _t1854}}
	result1029 := _t1855
	p.recordSpan(int(span_start1028), "Primitive")
	return result1029
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1033 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1856 := p.parse_term()
	term1030 := _t1856
	_t1857 := p.parse_term()
	term_31031 := _t1857
	_t1858 := p.parse_term()
	term_41032 := _t1858
	p.consumeLiteral(")")
	_t1859 := &pb.RelTerm{}
	_t1859.RelTermType = &pb.RelTerm_Term{Term: term1030}
	_t1860 := &pb.RelTerm{}
	_t1860.RelTermType = &pb.RelTerm_Term{Term: term_31031}
	_t1861 := &pb.RelTerm{}
	_t1861.RelTermType = &pb.RelTerm_Term{Term: term_41032}
	_t1862 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1859, _t1860, _t1861}}
	result1034 := _t1862
	p.recordSpan(int(span_start1033), "Primitive")
	return result1034
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1863 := p.parse_term()
	term1035 := _t1863
	_t1864 := p.parse_term()
	term_31036 := _t1864
	_t1865 := p.parse_term()
	term_41037 := _t1865
	p.consumeLiteral(")")
	_t1866 := &pb.RelTerm{}
	_t1866.RelTermType = &pb.RelTerm_Term{Term: term1035}
	_t1867 := &pb.RelTerm{}
	_t1867.RelTermType = &pb.RelTerm_Term{Term: term_31036}
	_t1868 := &pb.RelTerm{}
	_t1868.RelTermType = &pb.RelTerm_Term{Term: term_41037}
	_t1869 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1866, _t1867, _t1868}}
	result1039 := _t1869
	p.recordSpan(int(span_start1038), "Primitive")
	return result1039
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1043 := int64(p.spanStart())
	var _t1870 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1870 = 1
	} else {
		var _t1871 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1871 = 1
		} else {
			var _t1872 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1872 = 1
			} else {
				var _t1873 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1873 = 1
				} else {
					var _t1874 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1874 = 0
					} else {
						var _t1875 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1875 = 1
						} else {
							var _t1876 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1876 = 1
							} else {
								var _t1877 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1877 = 1
								} else {
									var _t1878 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1878 = 1
									} else {
										var _t1879 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1879 = 1
										} else {
											var _t1880 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1880 = 1
											} else {
												var _t1881 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1881 = 1
												} else {
													var _t1882 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1882 = 1
													} else {
														var _t1883 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1883 = 1
														} else {
															var _t1884 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1884 = 1
															} else {
																_t1884 = -1
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
	prediction1040 := _t1870
	var _t1885 *pb.RelTerm
	if prediction1040 == 1 {
		_t1886 := p.parse_term()
		term1042 := _t1886
		_t1887 := &pb.RelTerm{}
		_t1887.RelTermType = &pb.RelTerm_Term{Term: term1042}
		_t1885 = _t1887
	} else {
		var _t1888 *pb.RelTerm
		if prediction1040 == 0 {
			_t1889 := p.parse_specialized_value()
			specialized_value1041 := _t1889
			_t1890 := &pb.RelTerm{}
			_t1890.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1041}
			_t1888 = _t1890
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1885 = _t1888
	}
	result1044 := _t1885
	p.recordSpan(int(span_start1043), "RelTerm")
	return result1044
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1046 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1891 := p.parse_raw_value()
	raw_value1045 := _t1891
	result1047 := raw_value1045
	p.recordSpan(int(span_start1046), "Value")
	return result1047
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1892 := p.parse_name()
	name1048 := _t1892
	xs1049 := []*pb.RelTerm{}
	cond1050 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1050 {
		_t1893 := p.parse_rel_term()
		item1051 := _t1893
		xs1049 = append(xs1049, item1051)
		cond1050 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1052 := xs1049
	p.consumeLiteral(")")
	_t1894 := &pb.RelAtom{Name: name1048, Terms: rel_terms1052}
	result1054 := _t1894
	p.recordSpan(int(span_start1053), "RelAtom")
	return result1054
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1057 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1895 := p.parse_term()
	term1055 := _t1895
	_t1896 := p.parse_term()
	term_31056 := _t1896
	p.consumeLiteral(")")
	_t1897 := &pb.Cast{Input: term1055, Result: term_31056}
	result1058 := _t1897
	p.recordSpan(int(span_start1057), "Cast")
	return result1058
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1059 := []*pb.Attribute{}
	cond1060 := p.matchLookaheadLiteral("(", 0)
	for cond1060 {
		_t1898 := p.parse_attribute()
		item1061 := _t1898
		xs1059 = append(xs1059, item1061)
		cond1060 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1062 := xs1059
	p.consumeLiteral(")")
	return attributes1062
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1899 := p.parse_name()
	name1063 := _t1899
	xs1064 := []*pb.Value{}
	cond1065 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1065 {
		_t1900 := p.parse_raw_value()
		item1066 := _t1900
		xs1064 = append(xs1064, item1066)
		cond1065 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1067 := xs1064
	p.consumeLiteral(")")
	_t1901 := &pb.Attribute{Name: name1063, Args: raw_values1067}
	result1069 := _t1901
	p.recordSpan(int(span_start1068), "Attribute")
	return result1069
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1076 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1070 := []*pb.RelationId{}
	cond1071 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1071 {
		_t1902 := p.parse_relation_id()
		item1072 := _t1902
		xs1070 = append(xs1070, item1072)
		cond1071 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1073 := xs1070
	_t1903 := p.parse_script()
	script1074 := _t1903
	var _t1904 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1905 := p.parse_attrs()
		_t1904 = _t1905
	}
	attrs1075 := _t1904
	p.consumeLiteral(")")
	_t1906 := attrs1075
	if attrs1075 == nil {
		_t1906 = []*pb.Attribute{}
	}
	_t1907 := &pb.Algorithm{Global: relation_ids1073, Body: script1074, Attrs: _t1906}
	result1077 := _t1907
	p.recordSpan(int(span_start1076), "Algorithm")
	return result1077
}

func (p *Parser) parse_script() *pb.Script {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1078 := []*pb.Construct{}
	cond1079 := p.matchLookaheadLiteral("(", 0)
	for cond1079 {
		_t1908 := p.parse_construct()
		item1080 := _t1908
		xs1078 = append(xs1078, item1080)
		cond1079 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1081 := xs1078
	p.consumeLiteral(")")
	_t1909 := &pb.Script{Constructs: constructs1081}
	result1083 := _t1909
	p.recordSpan(int(span_start1082), "Script")
	return result1083
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1087 := int64(p.spanStart())
	var _t1910 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1911 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1911 = 1
		} else {
			var _t1912 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1912 = 1
			} else {
				var _t1913 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1913 = 1
				} else {
					var _t1914 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1914 = 0
					} else {
						var _t1915 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1915 = 1
						} else {
							var _t1916 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1916 = 1
							} else {
								_t1916 = -1
							}
							_t1915 = _t1916
						}
						_t1914 = _t1915
					}
					_t1913 = _t1914
				}
				_t1912 = _t1913
			}
			_t1911 = _t1912
		}
		_t1910 = _t1911
	} else {
		_t1910 = -1
	}
	prediction1084 := _t1910
	var _t1917 *pb.Construct
	if prediction1084 == 1 {
		_t1918 := p.parse_instruction()
		instruction1086 := _t1918
		_t1919 := &pb.Construct{}
		_t1919.ConstructType = &pb.Construct_Instruction{Instruction: instruction1086}
		_t1917 = _t1919
	} else {
		var _t1920 *pb.Construct
		if prediction1084 == 0 {
			_t1921 := p.parse_loop()
			loop1085 := _t1921
			_t1922 := &pb.Construct{}
			_t1922.ConstructType = &pb.Construct_Loop{Loop: loop1085}
			_t1920 = _t1922
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1917 = _t1920
	}
	result1088 := _t1917
	p.recordSpan(int(span_start1087), "Construct")
	return result1088
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1092 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1923 := p.parse_init()
	init1089 := _t1923
	_t1924 := p.parse_script()
	script1090 := _t1924
	var _t1925 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1926 := p.parse_attrs()
		_t1925 = _t1926
	}
	attrs1091 := _t1925
	p.consumeLiteral(")")
	_t1927 := attrs1091
	if attrs1091 == nil {
		_t1927 = []*pb.Attribute{}
	}
	_t1928 := &pb.Loop{Init: init1089, Body: script1090, Attrs: _t1927}
	result1093 := _t1928
	p.recordSpan(int(span_start1092), "Loop")
	return result1093
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1094 := []*pb.Instruction{}
	cond1095 := p.matchLookaheadLiteral("(", 0)
	for cond1095 {
		_t1929 := p.parse_instruction()
		item1096 := _t1929
		xs1094 = append(xs1094, item1096)
		cond1095 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1097 := xs1094
	p.consumeLiteral(")")
	return instructions1097
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1104 := int64(p.spanStart())
	var _t1930 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1931 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1931 = 1
		} else {
			var _t1932 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1932 = 4
			} else {
				var _t1933 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1933 = 3
				} else {
					var _t1934 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1934 = 2
					} else {
						var _t1935 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1935 = 0
						} else {
							_t1935 = -1
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
	prediction1098 := _t1930
	var _t1936 *pb.Instruction
	if prediction1098 == 4 {
		_t1937 := p.parse_monus_def()
		monus_def1103 := _t1937
		_t1938 := &pb.Instruction{}
		_t1938.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1103}
		_t1936 = _t1938
	} else {
		var _t1939 *pb.Instruction
		if prediction1098 == 3 {
			_t1940 := p.parse_monoid_def()
			monoid_def1102 := _t1940
			_t1941 := &pb.Instruction{}
			_t1941.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1102}
			_t1939 = _t1941
		} else {
			var _t1942 *pb.Instruction
			if prediction1098 == 2 {
				_t1943 := p.parse_break()
				break1101 := _t1943
				_t1944 := &pb.Instruction{}
				_t1944.InstrType = &pb.Instruction_Break{Break: break1101}
				_t1942 = _t1944
			} else {
				var _t1945 *pb.Instruction
				if prediction1098 == 1 {
					_t1946 := p.parse_upsert()
					upsert1100 := _t1946
					_t1947 := &pb.Instruction{}
					_t1947.InstrType = &pb.Instruction_Upsert{Upsert: upsert1100}
					_t1945 = _t1947
				} else {
					var _t1948 *pb.Instruction
					if prediction1098 == 0 {
						_t1949 := p.parse_assign()
						assign1099 := _t1949
						_t1950 := &pb.Instruction{}
						_t1950.InstrType = &pb.Instruction_Assign{Assign: assign1099}
						_t1948 = _t1950
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1945 = _t1948
				}
				_t1942 = _t1945
			}
			_t1939 = _t1942
		}
		_t1936 = _t1939
	}
	result1105 := _t1936
	p.recordSpan(int(span_start1104), "Instruction")
	return result1105
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1951 := p.parse_relation_id()
	relation_id1106 := _t1951
	_t1952 := p.parse_abstraction()
	abstraction1107 := _t1952
	var _t1953 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1954 := p.parse_attrs()
		_t1953 = _t1954
	}
	attrs1108 := _t1953
	p.consumeLiteral(")")
	_t1955 := attrs1108
	if attrs1108 == nil {
		_t1955 = []*pb.Attribute{}
	}
	_t1956 := &pb.Assign{Name: relation_id1106, Body: abstraction1107, Attrs: _t1955}
	result1110 := _t1956
	p.recordSpan(int(span_start1109), "Assign")
	return result1110
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1114 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1957 := p.parse_relation_id()
	relation_id1111 := _t1957
	_t1958 := p.parse_abstraction_with_arity()
	abstraction_with_arity1112 := _t1958
	var _t1959 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1960 := p.parse_attrs()
		_t1959 = _t1960
	}
	attrs1113 := _t1959
	p.consumeLiteral(")")
	_t1961 := attrs1113
	if attrs1113 == nil {
		_t1961 = []*pb.Attribute{}
	}
	_t1962 := &pb.Upsert{Name: relation_id1111, Body: abstraction_with_arity1112[0].(*pb.Abstraction), Attrs: _t1961, ValueArity: abstraction_with_arity1112[1].(int64)}
	result1115 := _t1962
	p.recordSpan(int(span_start1114), "Upsert")
	return result1115
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1963 := p.parse_bindings()
	bindings1116 := _t1963
	_t1964 := p.parse_formula()
	formula1117 := _t1964
	p.consumeLiteral(")")
	_t1965 := &pb.Abstraction{Vars: listConcat(bindings1116[0].([]*pb.Binding), bindings1116[1].([]*pb.Binding)), Value: formula1117}
	return []interface{}{_t1965, int64(len(bindings1116[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1966 := p.parse_relation_id()
	relation_id1118 := _t1966
	_t1967 := p.parse_abstraction()
	abstraction1119 := _t1967
	var _t1968 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1969 := p.parse_attrs()
		_t1968 = _t1969
	}
	attrs1120 := _t1968
	p.consumeLiteral(")")
	_t1970 := attrs1120
	if attrs1120 == nil {
		_t1970 = []*pb.Attribute{}
	}
	_t1971 := &pb.Break{Name: relation_id1118, Body: abstraction1119, Attrs: _t1970}
	result1122 := _t1971
	p.recordSpan(int(span_start1121), "Break")
	return result1122
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1127 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1972 := p.parse_monoid()
	monoid1123 := _t1972
	_t1973 := p.parse_relation_id()
	relation_id1124 := _t1973
	_t1974 := p.parse_abstraction_with_arity()
	abstraction_with_arity1125 := _t1974
	var _t1975 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1976 := p.parse_attrs()
		_t1975 = _t1976
	}
	attrs1126 := _t1975
	p.consumeLiteral(")")
	_t1977 := attrs1126
	if attrs1126 == nil {
		_t1977 = []*pb.Attribute{}
	}
	_t1978 := &pb.MonoidDef{Monoid: monoid1123, Name: relation_id1124, Body: abstraction_with_arity1125[0].(*pb.Abstraction), Attrs: _t1977, ValueArity: abstraction_with_arity1125[1].(int64)}
	result1128 := _t1978
	p.recordSpan(int(span_start1127), "MonoidDef")
	return result1128
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1134 := int64(p.spanStart())
	var _t1979 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1980 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1980 = 3
		} else {
			var _t1981 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1981 = 0
			} else {
				var _t1982 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1982 = 1
				} else {
					var _t1983 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1983 = 2
					} else {
						_t1983 = -1
					}
					_t1982 = _t1983
				}
				_t1981 = _t1982
			}
			_t1980 = _t1981
		}
		_t1979 = _t1980
	} else {
		_t1979 = -1
	}
	prediction1129 := _t1979
	var _t1984 *pb.Monoid
	if prediction1129 == 3 {
		_t1985 := p.parse_sum_monoid()
		sum_monoid1133 := _t1985
		_t1986 := &pb.Monoid{}
		_t1986.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1133}
		_t1984 = _t1986
	} else {
		var _t1987 *pb.Monoid
		if prediction1129 == 2 {
			_t1988 := p.parse_max_monoid()
			max_monoid1132 := _t1988
			_t1989 := &pb.Monoid{}
			_t1989.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1132}
			_t1987 = _t1989
		} else {
			var _t1990 *pb.Monoid
			if prediction1129 == 1 {
				_t1991 := p.parse_min_monoid()
				min_monoid1131 := _t1991
				_t1992 := &pb.Monoid{}
				_t1992.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1131}
				_t1990 = _t1992
			} else {
				var _t1993 *pb.Monoid
				if prediction1129 == 0 {
					_t1994 := p.parse_or_monoid()
					or_monoid1130 := _t1994
					_t1995 := &pb.Monoid{}
					_t1995.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1130}
					_t1993 = _t1995
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1990 = _t1993
			}
			_t1987 = _t1990
		}
		_t1984 = _t1987
	}
	result1135 := _t1984
	p.recordSpan(int(span_start1134), "Monoid")
	return result1135
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1136 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1996 := &pb.OrMonoid{}
	result1137 := _t1996
	p.recordSpan(int(span_start1136), "OrMonoid")
	return result1137
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1139 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1997 := p.parse_type()
	type1138 := _t1997
	p.consumeLiteral(")")
	_t1998 := &pb.MinMonoid{Type: type1138}
	result1140 := _t1998
	p.recordSpan(int(span_start1139), "MinMonoid")
	return result1140
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1142 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1999 := p.parse_type()
	type1141 := _t1999
	p.consumeLiteral(")")
	_t2000 := &pb.MaxMonoid{Type: type1141}
	result1143 := _t2000
	p.recordSpan(int(span_start1142), "MaxMonoid")
	return result1143
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1145 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t2001 := p.parse_type()
	type1144 := _t2001
	p.consumeLiteral(")")
	_t2002 := &pb.SumMonoid{Type: type1144}
	result1146 := _t2002
	p.recordSpan(int(span_start1145), "SumMonoid")
	return result1146
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1151 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t2003 := p.parse_monoid()
	monoid1147 := _t2003
	_t2004 := p.parse_relation_id()
	relation_id1148 := _t2004
	_t2005 := p.parse_abstraction_with_arity()
	abstraction_with_arity1149 := _t2005
	var _t2006 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t2007 := p.parse_attrs()
		_t2006 = _t2007
	}
	attrs1150 := _t2006
	p.consumeLiteral(")")
	_t2008 := attrs1150
	if attrs1150 == nil {
		_t2008 = []*pb.Attribute{}
	}
	_t2009 := &pb.MonusDef{Monoid: monoid1147, Name: relation_id1148, Body: abstraction_with_arity1149[0].(*pb.Abstraction), Attrs: _t2008, ValueArity: abstraction_with_arity1149[1].(int64)}
	result1152 := _t2009
	p.recordSpan(int(span_start1151), "MonusDef")
	return result1152
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2010 := p.parse_relation_id()
	relation_id1153 := _t2010
	_t2011 := p.parse_abstraction()
	abstraction1154 := _t2011
	_t2012 := p.parse_functional_dependency_keys()
	functional_dependency_keys1155 := _t2012
	_t2013 := p.parse_functional_dependency_values()
	functional_dependency_values1156 := _t2013
	p.consumeLiteral(")")
	_t2014 := &pb.FunctionalDependency{Guard: abstraction1154, Keys: functional_dependency_keys1155, Values: functional_dependency_values1156}
	_t2015 := &pb.Constraint{Name: relation_id1153}
	_t2015.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2014}
	result1158 := _t2015
	p.recordSpan(int(span_start1157), "Constraint")
	return result1158
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1159 := []*pb.Var{}
	cond1160 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1160 {
		_t2016 := p.parse_var()
		item1161 := _t2016
		xs1159 = append(xs1159, item1161)
		cond1160 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1162 := xs1159
	p.consumeLiteral(")")
	return vars1162
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1163 := []*pb.Var{}
	cond1164 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1164 {
		_t2017 := p.parse_var()
		item1165 := _t2017
		xs1163 = append(xs1163, item1165)
		cond1164 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1166 := xs1163
	p.consumeLiteral(")")
	return vars1166
}

func (p *Parser) parse_data() *pb.Data {
	span_start1172 := int64(p.spanStart())
	var _t2018 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2019 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2019 = 3
		} else {
			var _t2020 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2020 = 0
			} else {
				var _t2021 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2021 = 2
				} else {
					var _t2022 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2022 = 1
					} else {
						_t2022 = -1
					}
					_t2021 = _t2022
				}
				_t2020 = _t2021
			}
			_t2019 = _t2020
		}
		_t2018 = _t2019
	} else {
		_t2018 = -1
	}
	prediction1167 := _t2018
	var _t2023 *pb.Data
	if prediction1167 == 3 {
		_t2024 := p.parse_iceberg_data()
		iceberg_data1171 := _t2024
		_t2025 := &pb.Data{}
		_t2025.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1171}
		_t2023 = _t2025
	} else {
		var _t2026 *pb.Data
		if prediction1167 == 2 {
			_t2027 := p.parse_csv_data()
			csv_data1170 := _t2027
			_t2028 := &pb.Data{}
			_t2028.DataType = &pb.Data_CsvData{CsvData: csv_data1170}
			_t2026 = _t2028
		} else {
			var _t2029 *pb.Data
			if prediction1167 == 1 {
				_t2030 := p.parse_betree_relation()
				betree_relation1169 := _t2030
				_t2031 := &pb.Data{}
				_t2031.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1169}
				_t2029 = _t2031
			} else {
				var _t2032 *pb.Data
				if prediction1167 == 0 {
					_t2033 := p.parse_edb()
					edb1168 := _t2033
					_t2034 := &pb.Data{}
					_t2034.DataType = &pb.Data_Edb{Edb: edb1168}
					_t2032 = _t2034
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2029 = _t2032
			}
			_t2026 = _t2029
		}
		_t2023 = _t2026
	}
	result1173 := _t2023
	p.recordSpan(int(span_start1172), "Data")
	return result1173
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1177 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2035 := p.parse_relation_id()
	relation_id1174 := _t2035
	_t2036 := p.parse_edb_path()
	edb_path1175 := _t2036
	_t2037 := p.parse_edb_types()
	edb_types1176 := _t2037
	p.consumeLiteral(")")
	_t2038 := &pb.EDB{TargetId: relation_id1174, Path: edb_path1175, Types: edb_types1176}
	result1178 := _t2038
	p.recordSpan(int(span_start1177), "EDB")
	return result1178
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1179 := []string{}
	cond1180 := p.matchLookaheadTerminal("STRING", 0)
	for cond1180 {
		item1181 := p.consumeTerminal("STRING").Value.str
		xs1179 = append(xs1179, item1181)
		cond1180 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1182 := xs1179
	p.consumeLiteral("]")
	return strings1182
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1183 := []*pb.Type{}
	cond1184 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1184 {
		_t2039 := p.parse_type()
		item1185 := _t2039
		xs1183 = append(xs1183, item1185)
		cond1184 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1186 := xs1183
	p.consumeLiteral("]")
	return types1186
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2040 := p.parse_relation_id()
	relation_id1187 := _t2040
	_t2041 := p.parse_betree_info()
	betree_info1188 := _t2041
	p.consumeLiteral(")")
	_t2042 := &pb.BeTreeRelation{Name: relation_id1187, RelationInfo: betree_info1188}
	result1190 := _t2042
	p.recordSpan(int(span_start1189), "BeTreeRelation")
	return result1190
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1194 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2043 := p.parse_betree_info_key_types()
	betree_info_key_types1191 := _t2043
	_t2044 := p.parse_betree_info_value_types()
	betree_info_value_types1192 := _t2044
	_t2045 := p.parse_config_dict()
	config_dict1193 := _t2045
	p.consumeLiteral(")")
	_t2046 := p.construct_betree_info(betree_info_key_types1191, betree_info_value_types1192, config_dict1193)
	result1195 := _t2046
	p.recordSpan(int(span_start1194), "BeTreeInfo")
	return result1195
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1196 := []*pb.Type{}
	cond1197 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1197 {
		_t2047 := p.parse_type()
		item1198 := _t2047
		xs1196 = append(xs1196, item1198)
		cond1197 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1199 := xs1196
	p.consumeLiteral(")")
	return types1199
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1200 := []*pb.Type{}
	cond1201 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1201 {
		_t2048 := p.parse_type()
		item1202 := _t2048
		xs1200 = append(xs1200, item1202)
		cond1201 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1203 := xs1200
	p.consumeLiteral(")")
	return types1203
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1209 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2049 := p.parse_csvlocator()
	csvlocator1204 := _t2049
	_t2050 := p.parse_csv_config()
	csv_config1205 := _t2050
	var _t2051 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2052 := p.parse_gnf_columns()
		_t2051 = _t2052
	}
	gnf_columns1206 := _t2051
	var _t2053 *pb.TargetRelations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2054 := p.parse_target_relations()
		_t2053 = _t2054
	}
	target_relations1207 := _t2053
	_t2055 := p.parse_csv_asof()
	csv_asof1208 := _t2055
	p.consumeLiteral(")")
	_t2056 := p.construct_csv_data(csvlocator1204, csv_config1205, gnf_columns1206, target_relations1207, csv_asof1208)
	result1210 := _t2056
	p.recordSpan(int(span_start1209), "CSVData")
	return result1210
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1213 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2057 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2058 := p.parse_csv_locator_paths()
		_t2057 = _t2058
	}
	csv_locator_paths1211 := _t2057
	var _t2059 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2060 := p.parse_csv_locator_inline_data()
		_t2059 = ptr(_t2060)
	}
	csv_locator_inline_data1212 := _t2059
	p.consumeLiteral(")")
	_t2061 := csv_locator_paths1211
	if csv_locator_paths1211 == nil {
		_t2061 = []string{}
	}
	_t2062 := &pb.CSVLocator{Paths: _t2061, InlineData: []byte(deref(csv_locator_inline_data1212, ""))}
	result1214 := _t2062
	p.recordSpan(int(span_start1213), "CSVLocator")
	return result1214
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1215 := []string{}
	cond1216 := p.matchLookaheadTerminal("STRING", 0)
	for cond1216 {
		item1217 := p.consumeTerminal("STRING").Value.str
		xs1215 = append(xs1215, item1217)
		cond1216 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1218 := xs1215
	p.consumeLiteral(")")
	return strings1218
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1219 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1219
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1222 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2063 := p.parse_config_dict()
	config_dict1220 := _t2063
	var _t2064 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2065 := p.parse__storage_integration()
		_t2064 = _t2065
	}
	_storage_integration1221 := _t2064
	p.consumeLiteral(")")
	_t2066 := p.construct_csv_config(config_dict1220, _storage_integration1221)
	result1223 := _t2066
	p.recordSpan(int(span_start1222), "CSVConfig")
	return result1223
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2067 := p.parse_config_dict()
	config_dict1224 := _t2067
	p.consumeLiteral(")")
	return config_dict1224
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1225 := []*pb.GNFColumn{}
	cond1226 := p.matchLookaheadLiteral("(", 0)
	for cond1226 {
		_t2068 := p.parse_gnf_column()
		item1227 := _t2068
		xs1225 = append(xs1225, item1227)
		cond1226 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1228 := xs1225
	p.consumeLiteral(")")
	return gnf_columns1228
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1235 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2069 := p.parse_gnf_column_path()
	gnf_column_path1229 := _t2069
	var _t2070 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2071 := p.parse_relation_id()
		_t2070 = _t2071
	}
	relation_id1230 := _t2070
	p.consumeLiteral("[")
	xs1231 := []*pb.Type{}
	cond1232 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1232 {
		_t2072 := p.parse_type()
		item1233 := _t2072
		xs1231 = append(xs1231, item1233)
		cond1232 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1234 := xs1231
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2073 := &pb.GNFColumn{ColumnPath: gnf_column_path1229, TargetId: relation_id1230, Types: types1234}
	result1236 := _t2073
	p.recordSpan(int(span_start1235), "GNFColumn")
	return result1236
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2074 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2074 = 1
	} else {
		var _t2075 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2075 = 0
		} else {
			_t2075 = -1
		}
		_t2074 = _t2075
	}
	prediction1237 := _t2074
	var _t2076 []string
	if prediction1237 == 1 {
		p.consumeLiteral("[")
		xs1239 := []string{}
		cond1240 := p.matchLookaheadTerminal("STRING", 0)
		for cond1240 {
			item1241 := p.consumeTerminal("STRING").Value.str
			xs1239 = append(xs1239, item1241)
			cond1240 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1242 := xs1239
		p.consumeLiteral("]")
		_t2076 = strings1242
	} else {
		var _t2077 []string
		if prediction1237 == 0 {
			string1238 := p.consumeTerminal("STRING").Value.str
			_ = string1238
			_t2077 = []string{string1238}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2076 = _t2077
	}
	return _t2076
}

func (p *Parser) parse_target_relations() *pb.TargetRelations {
	span_start1245 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2078 := p.parse_relation_keys()
	relation_keys1243 := _t2078
	_t2079 := p.parse_relation_body()
	relation_body1244 := _t2079
	p.consumeLiteral(")")
	_t2080 := p.construct_relations(relation_keys1243, relation_body1244)
	result1246 := _t2080
	p.recordSpan(int(span_start1245), "TargetRelations")
	return result1246
}

func (p *Parser) parse_relation_keys() []interface{} {
	var _t2081 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2082 int64
		if p.matchLookaheadLiteral("keys", 1) {
			var _t2083 int64
			if p.matchLookaheadLiteral(":", 2) {
				_t2083 = 1
			} else {
				var _t2084 int64
				if p.matchLookaheadLiteral(")", 2) {
					_t2084 = 0
				} else {
					var _t2085 int64
					if p.matchLookaheadLiteral("(", 2) {
						_t2085 = 0
					} else {
						_t2085 = -1
					}
					_t2084 = _t2085
				}
				_t2083 = _t2084
			}
			_t2082 = _t2083
		} else {
			_t2082 = -1
		}
		_t2081 = _t2082
	} else {
		_t2081 = -1
	}
	prediction1247 := _t2081
	var _t2086 []interface{}
	if prediction1247 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("keys")
		p.consumeLiteral(":")
		symbol1252 := p.consumeTerminal("SYMBOL").Value.str
		p.consumeLiteral(")")
		_t2087 := p.construct_synthetic_keys(symbol1252)
		_t2086 = _t2087
	} else {
		var _t2088 []interface{}
		if prediction1247 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("keys")
			xs1248 := []*pb.NamedColumn{}
			cond1249 := p.matchLookaheadLiteral("(", 0)
			for cond1249 {
				_t2089 := p.parse_named_column()
				item1250 := _t2089
				xs1248 = append(xs1248, item1250)
				cond1249 = p.matchLookaheadLiteral("(", 0)
			}
			named_columns1251 := xs1248
			p.consumeLiteral(")")
			_t2088 = []interface{}{named_columns1251, false}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_keys", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2086 = _t2088
	}
	return _t2086
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1253 := p.consumeTerminal("STRING").Value.str
	_t2090 := p.parse_type()
	type1254 := _t2090
	p.consumeLiteral(")")
	_t2091 := &pb.NamedColumn{Name: string1253, Type: type1254}
	result1256 := _t2091
	p.recordSpan(int(span_start1255), "NamedColumn")
	return result1256
}

func (p *Parser) parse_relation_body() *pb.TargetRelations {
	span_start1261 := int64(p.spanStart())
	var _t2092 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2093 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2093 = 0
		} else {
			var _t2094 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2094 = 1
			} else {
				_t2094 = 0
			}
			_t2093 = _t2094
		}
		_t2092 = _t2093
	} else {
		_t2092 = 0
	}
	prediction1257 := _t2092
	var _t2095 *pb.TargetRelations
	if prediction1257 == 1 {
		_t2096 := p.parse_cdc_inserts()
		cdc_inserts1259 := _t2096
		_t2097 := p.parse_cdc_deletes()
		cdc_deletes1260 := _t2097
		_t2098 := p.construct_cdc_relations(cdc_inserts1259, cdc_deletes1260)
		_t2095 = _t2098
	} else {
		var _t2099 *pb.TargetRelations
		if prediction1257 == 0 {
			_t2100 := p.parse_non_cdc_relations()
			non_cdc_relations1258 := _t2100
			_t2101 := p.construct_non_cdc_relations(non_cdc_relations1258)
			_t2099 = _t2101
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2095 = _t2099
	}
	result1262 := _t2095
	p.recordSpan(int(span_start1261), "TargetRelations")
	return result1262
}

func (p *Parser) parse_non_cdc_relations() []*pb.TargetRelation {
	xs1263 := []*pb.TargetRelation{}
	cond1264 := p.matchLookaheadLiteral("(", 0)
	for cond1264 {
		_t2102 := p.parse_target_relation()
		item1265 := _t2102
		xs1263 = append(xs1263, item1265)
		cond1264 = p.matchLookaheadLiteral("(", 0)
	}
	return xs1263
}

func (p *Parser) parse_target_relation() *pb.TargetRelation {
	span_start1271 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2103 := p.parse_relation_id()
	relation_id1266 := _t2103
	xs1267 := []*pb.NamedColumn{}
	cond1268 := p.matchLookaheadLiteral("(", 0)
	for cond1268 {
		_t2104 := p.parse_named_column()
		item1269 := _t2104
		xs1267 = append(xs1267, item1269)
		cond1268 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1270 := xs1267
	p.consumeLiteral(")")
	_t2105 := &pb.TargetRelation{TargetId: relation_id1266, Values: named_columns1270}
	result1272 := _t2105
	p.recordSpan(int(span_start1271), "TargetRelation")
	return result1272
}

func (p *Parser) parse_cdc_inserts() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1273 := []*pb.TargetRelation{}
	cond1274 := p.matchLookaheadLiteral("(", 0)
	for cond1274 {
		_t2106 := p.parse_target_relation()
		item1275 := _t2106
		xs1273 = append(xs1273, item1275)
		cond1274 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1276 := xs1273
	p.consumeLiteral(")")
	return target_relations1276
}

func (p *Parser) parse_cdc_deletes() []*pb.TargetRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1277 := []*pb.TargetRelation{}
	cond1278 := p.matchLookaheadLiteral("(", 0)
	for cond1278 {
		_t2107 := p.parse_target_relation()
		item1279 := _t2107
		xs1277 = append(xs1277, item1279)
		cond1278 = p.matchLookaheadLiteral("(", 0)
	}
	target_relations1280 := xs1277
	p.consumeLiteral(")")
	return target_relations1280
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1281 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1281
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1288 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2108 := p.parse_iceberg_locator()
	iceberg_locator1282 := _t2108
	_t2109 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1283 := _t2109
	_t2110 := p.parse_gnf_columns()
	gnf_columns1284 := _t2110
	var _t2111 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2112 := p.parse_iceberg_from_snapshot()
		_t2111 = ptr(_t2112)
	}
	iceberg_from_snapshot1285 := _t2111
	var _t2113 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2114 := p.parse_iceberg_to_snapshot()
		_t2113 = ptr(_t2114)
	}
	iceberg_to_snapshot1286 := _t2113
	_t2115 := p.parse_boolean_value()
	boolean_value1287 := _t2115
	p.consumeLiteral(")")
	_t2116 := p.construct_iceberg_data(iceberg_locator1282, iceberg_catalog_config1283, gnf_columns1284, iceberg_from_snapshot1285, iceberg_to_snapshot1286, boolean_value1287)
	result1289 := _t2116
	p.recordSpan(int(span_start1288), "IcebergData")
	return result1289
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1293 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2117 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1290 := _t2117
	_t2118 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1291 := _t2118
	_t2119 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1292 := _t2119
	p.consumeLiteral(")")
	_t2120 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1290, Namespace: iceberg_locator_namespace1291, Warehouse: iceberg_locator_warehouse1292}
	result1294 := _t2120
	p.recordSpan(int(span_start1293), "IcebergLocator")
	return result1294
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1295 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1295
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1296 := []string{}
	cond1297 := p.matchLookaheadTerminal("STRING", 0)
	for cond1297 {
		item1298 := p.consumeTerminal("STRING").Value.str
		xs1296 = append(xs1296, item1298)
		cond1297 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1299 := xs1296
	p.consumeLiteral(")")
	return strings1299
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1300 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1300
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1305 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2121 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1301 := _t2121
	var _t2122 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2123 := p.parse_iceberg_catalog_config_scope()
		_t2122 = ptr(_t2123)
	}
	iceberg_catalog_config_scope1302 := _t2122
	_t2124 := p.parse_iceberg_properties()
	iceberg_properties1303 := _t2124
	_t2125 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1304 := _t2125
	p.consumeLiteral(")")
	_t2126 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1301, iceberg_catalog_config_scope1302, iceberg_properties1303, iceberg_auth_properties1304)
	result1306 := _t2126
	p.recordSpan(int(span_start1305), "IcebergCatalogConfig")
	return result1306
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1307 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1307
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1308 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1308
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1309 := [][]interface{}{}
	cond1310 := p.matchLookaheadLiteral("(", 0)
	for cond1310 {
		_t2127 := p.parse_iceberg_property_entry()
		item1311 := _t2127
		xs1309 = append(xs1309, item1311)
		cond1310 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1312 := xs1309
	p.consumeLiteral(")")
	return iceberg_property_entrys1312
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1313 := p.consumeTerminal("STRING").Value.str
	string_31314 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1313, string_31314}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1315 := [][]interface{}{}
	cond1316 := p.matchLookaheadLiteral("(", 0)
	for cond1316 {
		_t2128 := p.parse_iceberg_masked_property_entry()
		item1317 := _t2128
		xs1315 = append(xs1315, item1317)
		cond1316 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1318 := xs1315
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1318
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1319 := p.consumeTerminal("STRING").Value.str
	string_31320 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1319, string_31320}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1321 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1321
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1322 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1322
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1324 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2129 := p.parse_fragment_id()
	fragment_id1323 := _t2129
	p.consumeLiteral(")")
	_t2130 := &pb.Undefine{FragmentId: fragment_id1323}
	result1325 := _t2130
	p.recordSpan(int(span_start1324), "Undefine")
	return result1325
}

func (p *Parser) parse_context() *pb.Context {
	span_start1330 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1326 := []*pb.RelationId{}
	cond1327 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1327 {
		_t2131 := p.parse_relation_id()
		item1328 := _t2131
		xs1326 = append(xs1326, item1328)
		cond1327 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1329 := xs1326
	p.consumeLiteral(")")
	_t2132 := &pb.Context{Relations: relation_ids1329}
	result1331 := _t2132
	p.recordSpan(int(span_start1330), "Context")
	return result1331
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1337 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2133 := p.parse_edb_path()
	edb_path1332 := _t2133
	xs1333 := []*pb.SnapshotMapping{}
	cond1334 := p.matchLookaheadLiteral("[", 0)
	for cond1334 {
		_t2134 := p.parse_snapshot_mapping()
		item1335 := _t2134
		xs1333 = append(xs1333, item1335)
		cond1334 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1336 := xs1333
	p.consumeLiteral(")")
	_t2135 := &pb.Snapshot{Prefix: edb_path1332, Mappings: snapshot_mappings1336}
	result1338 := _t2135
	p.recordSpan(int(span_start1337), "Snapshot")
	return result1338
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1341 := int64(p.spanStart())
	_t2136 := p.parse_edb_path()
	edb_path1339 := _t2136
	_t2137 := p.parse_relation_id()
	relation_id1340 := _t2137
	_t2138 := &pb.SnapshotMapping{DestinationPath: edb_path1339, SourceRelation: relation_id1340}
	result1342 := _t2138
	p.recordSpan(int(span_start1341), "SnapshotMapping")
	return result1342
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1343 := []*pb.Read{}
	cond1344 := p.matchLookaheadLiteral("(", 0)
	for cond1344 {
		_t2139 := p.parse_read()
		item1345 := _t2139
		xs1343 = append(xs1343, item1345)
		cond1344 = p.matchLookaheadLiteral("(", 0)
	}
	reads1346 := xs1343
	p.consumeLiteral(")")
	return reads1346
}

func (p *Parser) parse_read() *pb.Read {
	span_start1353 := int64(p.spanStart())
	var _t2140 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2141 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2141 = 2
		} else {
			var _t2142 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2142 = 1
			} else {
				var _t2143 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2143 = 4
				} else {
					var _t2144 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2144 = 4
					} else {
						var _t2145 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2145 = 0
						} else {
							var _t2146 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2146 = 3
							} else {
								_t2146 = -1
							}
							_t2145 = _t2146
						}
						_t2144 = _t2145
					}
					_t2143 = _t2144
				}
				_t2142 = _t2143
			}
			_t2141 = _t2142
		}
		_t2140 = _t2141
	} else {
		_t2140 = -1
	}
	prediction1347 := _t2140
	var _t2147 *pb.Read
	if prediction1347 == 4 {
		_t2148 := p.parse_export()
		export1352 := _t2148
		_t2149 := &pb.Read{}
		_t2149.ReadType = &pb.Read_Export{Export: export1352}
		_t2147 = _t2149
	} else {
		var _t2150 *pb.Read
		if prediction1347 == 3 {
			_t2151 := p.parse_abort()
			abort1351 := _t2151
			_t2152 := &pb.Read{}
			_t2152.ReadType = &pb.Read_Abort{Abort: abort1351}
			_t2150 = _t2152
		} else {
			var _t2153 *pb.Read
			if prediction1347 == 2 {
				_t2154 := p.parse_what_if()
				what_if1350 := _t2154
				_t2155 := &pb.Read{}
				_t2155.ReadType = &pb.Read_WhatIf{WhatIf: what_if1350}
				_t2153 = _t2155
			} else {
				var _t2156 *pb.Read
				if prediction1347 == 1 {
					_t2157 := p.parse_output()
					output1349 := _t2157
					_t2158 := &pb.Read{}
					_t2158.ReadType = &pb.Read_Output{Output: output1349}
					_t2156 = _t2158
				} else {
					var _t2159 *pb.Read
					if prediction1347 == 0 {
						_t2160 := p.parse_demand()
						demand1348 := _t2160
						_t2161 := &pb.Read{}
						_t2161.ReadType = &pb.Read_Demand{Demand: demand1348}
						_t2159 = _t2161
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2156 = _t2159
				}
				_t2153 = _t2156
			}
			_t2150 = _t2153
		}
		_t2147 = _t2150
	}
	result1354 := _t2147
	p.recordSpan(int(span_start1353), "Read")
	return result1354
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1356 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2162 := p.parse_relation_id()
	relation_id1355 := _t2162
	p.consumeLiteral(")")
	_t2163 := &pb.Demand{RelationId: relation_id1355}
	result1357 := _t2163
	p.recordSpan(int(span_start1356), "Demand")
	return result1357
}

func (p *Parser) parse_output() *pb.Output {
	span_start1360 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2164 := p.parse_name()
	name1358 := _t2164
	_t2165 := p.parse_relation_id()
	relation_id1359 := _t2165
	p.consumeLiteral(")")
	_t2166 := &pb.Output{Name: name1358, RelationId: relation_id1359}
	result1361 := _t2166
	p.recordSpan(int(span_start1360), "Output")
	return result1361
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1364 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2167 := p.parse_name()
	name1362 := _t2167
	_t2168 := p.parse_epoch()
	epoch1363 := _t2168
	p.consumeLiteral(")")
	_t2169 := &pb.WhatIf{Branch: name1362, Epoch: epoch1363}
	result1365 := _t2169
	p.recordSpan(int(span_start1364), "WhatIf")
	return result1365
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1368 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2170 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2171 := p.parse_name()
		_t2170 = ptr(_t2171)
	}
	name1366 := _t2170
	_t2172 := p.parse_relation_id()
	relation_id1367 := _t2172
	p.consumeLiteral(")")
	_t2173 := &pb.Abort{Name: deref(name1366, "abort"), RelationId: relation_id1367}
	result1369 := _t2173
	p.recordSpan(int(span_start1368), "Abort")
	return result1369
}

func (p *Parser) parse_export() *pb.Export {
	span_start1373 := int64(p.spanStart())
	var _t2174 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2175 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2175 = 1
		} else {
			var _t2176 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2176 = 0
			} else {
				_t2176 = -1
			}
			_t2175 = _t2176
		}
		_t2174 = _t2175
	} else {
		_t2174 = -1
	}
	prediction1370 := _t2174
	var _t2177 *pb.Export
	if prediction1370 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2178 := p.parse_export_iceberg_config()
		export_iceberg_config1372 := _t2178
		p.consumeLiteral(")")
		_t2179 := &pb.Export{}
		_t2179.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1372}
		_t2177 = _t2179
	} else {
		var _t2180 *pb.Export
		if prediction1370 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2181 := p.parse_export_csv_config()
			export_csv_config1371 := _t2181
			p.consumeLiteral(")")
			_t2182 := &pb.Export{}
			_t2182.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1371}
			_t2180 = _t2182
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2177 = _t2180
	}
	result1374 := _t2177
	p.recordSpan(int(span_start1373), "Export")
	return result1374
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1382 := int64(p.spanStart())
	var _t2183 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2184 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2184 = 0
		} else {
			var _t2185 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2185 = 1
			} else {
				_t2185 = -1
			}
			_t2184 = _t2185
		}
		_t2183 = _t2184
	} else {
		_t2183 = -1
	}
	prediction1375 := _t2183
	var _t2186 *pb.ExportCSVConfig
	if prediction1375 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2187 := p.parse_export_csv_path()
		export_csv_path1379 := _t2187
		_t2188 := p.parse_export_csv_columns_list()
		export_csv_columns_list1380 := _t2188
		_t2189 := p.parse_config_dict()
		config_dict1381 := _t2189
		p.consumeLiteral(")")
		_t2190 := p.construct_export_csv_config(export_csv_path1379, export_csv_columns_list1380, config_dict1381)
		_t2186 = _t2190
	} else {
		var _t2191 *pb.ExportCSVConfig
		if prediction1375 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2192 := p.parse_export_csv_output_location()
			export_csv_output_location1376 := _t2192
			_t2193 := p.parse_export_csv_source()
			export_csv_source1377 := _t2193
			_t2194 := p.parse_csv_config()
			csv_config1378 := _t2194
			p.consumeLiteral(")")
			_t2195 := p.construct_export_csv_config_with_location(export_csv_output_location1376, export_csv_source1377, csv_config1378)
			_t2191 = _t2195
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2186 = _t2191
	}
	result1383 := _t2186
	p.recordSpan(int(span_start1382), "ExportCSVConfig")
	return result1383
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2196 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2197 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2197 = 1
		} else {
			var _t2198 int64
			if p.matchLookaheadLiteral("path", 1) {
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
	var _t2199 []interface{}
	if prediction1384 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2200 := p.parse_name()
		name1386 := _t2200
		p.consumeLiteral(")")
		_t2199 = []interface{}{"", name1386}
	} else {
		var _t2201 []interface{}
		if prediction1384 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1385 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2201 = []interface{}{string1385, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2199 = _t2201
	}
	return _t2199
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1393 := int64(p.spanStart())
	var _t2202 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2203 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2203 = 1
		} else {
			var _t2204 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2204 = 0
			} else {
				_t2204 = -1
			}
			_t2203 = _t2204
		}
		_t2202 = _t2203
	} else {
		_t2202 = -1
	}
	prediction1387 := _t2202
	var _t2205 *pb.ExportCSVSource
	if prediction1387 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2206 := p.parse_relation_id()
		relation_id1392 := _t2206
		p.consumeLiteral(")")
		_t2207 := &pb.ExportCSVSource{}
		_t2207.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1392}
		_t2205 = _t2207
	} else {
		var _t2208 *pb.ExportCSVSource
		if prediction1387 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1388 := []*pb.ExportCSVColumn{}
			cond1389 := p.matchLookaheadLiteral("(", 0)
			for cond1389 {
				_t2209 := p.parse_export_csv_column()
				item1390 := _t2209
				xs1388 = append(xs1388, item1390)
				cond1389 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1391 := xs1388
			p.consumeLiteral(")")
			_t2210 := &pb.ExportCSVColumns{Columns: export_csv_columns1391}
			_t2211 := &pb.ExportCSVSource{}
			_t2211.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2210}
			_t2208 = _t2211
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2205 = _t2208
	}
	result1394 := _t2205
	p.recordSpan(int(span_start1393), "ExportCSVSource")
	return result1394
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1397 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1395 := p.consumeTerminal("STRING").Value.str
	_t2212 := p.parse_relation_id()
	relation_id1396 := _t2212
	p.consumeLiteral(")")
	_t2213 := &pb.ExportCSVColumn{ColumnName: string1395, ColumnData: relation_id1396}
	result1398 := _t2213
	p.recordSpan(int(span_start1397), "ExportCSVColumn")
	return result1398
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1399 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1399
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1400 := []*pb.ExportCSVColumn{}
	cond1401 := p.matchLookaheadLiteral("(", 0)
	for cond1401 {
		_t2214 := p.parse_export_csv_column()
		item1402 := _t2214
		xs1400 = append(xs1400, item1402)
		cond1401 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1403 := xs1400
	p.consumeLiteral(")")
	return export_csv_columns1403
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1409 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2215 := p.parse_iceberg_locator()
	iceberg_locator1404 := _t2215
	_t2216 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1405 := _t2216
	_t2217 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1406 := _t2217
	_t2218 := p.parse_iceberg_table_properties()
	iceberg_table_properties1407 := _t2218
	var _t2219 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2220 := p.parse_config_dict()
		_t2219 = _t2220
	}
	config_dict1408 := _t2219
	p.consumeLiteral(")")
	_t2221 := p.construct_export_iceberg_config_full(iceberg_locator1404, iceberg_catalog_config1405, export_iceberg_table_def1406, iceberg_table_properties1407, config_dict1408)
	result1410 := _t2221
	p.recordSpan(int(span_start1409), "ExportIcebergConfig")
	return result1410
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1412 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2222 := p.parse_relation_id()
	relation_id1411 := _t2222
	p.consumeLiteral(")")
	result1413 := relation_id1411
	p.recordSpan(int(span_start1412), "RelationId")
	return result1413
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1414 := [][]interface{}{}
	cond1415 := p.matchLookaheadLiteral("(", 0)
	for cond1415 {
		_t2223 := p.parse_iceberg_property_entry()
		item1416 := _t2223
		xs1414 = append(xs1414, item1416)
		cond1415 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1417 := xs1414
	p.consumeLiteral(")")
	return iceberg_property_entrys1417
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
