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
	var _t2200 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2200
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2201 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2201
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2202 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2202
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2203 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2203
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2204 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2204
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2205 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2205
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2206 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2206
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2207 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2207
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2208 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2208
	return nil
}

func (p *Parser) construct_non_cdc_relations(relations []*pb.OutputRelation) *pb.Relations {
	_t2209 := &pb.Relations{Keys: []*pb.NamedColumn{}, Relations: relations, Inserts: []*pb.OutputRelation{}, Deletes: []*pb.OutputRelation{}}
	return _t2209
}

func (p *Parser) construct_cdc_relations(inserts []*pb.OutputRelation, deletes []*pb.OutputRelation) *pb.Relations {
	_t2210 := &pb.Relations{Keys: []*pb.NamedColumn{}, Relations: []*pb.OutputRelation{}, Inserts: inserts, Deletes: deletes}
	return _t2210
}

func (p *Parser) construct_relations(keys []*pb.NamedColumn, body *pb.Relations) *pb.Relations {
	_t2211 := &pb.Relations{Keys: keys, Relations: body.GetRelations(), Inserts: body.GetInserts(), Deletes: body.GetDeletes()}
	return _t2211
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, relations_opt *pb.Relations, asof string) *pb.CSVData {
	_t2212 := columns_opt
	if columns_opt == nil {
		_t2212 = []*pb.GNFColumn{}
	}
	_t2213 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2212, Asof: asof, Relations: relations_opt}
	return _t2213
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2214 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2214
	_t2215 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2215
	_t2216 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2216
	_t2217 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2217
	_t2218 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2218
	_t2219 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2219
	_t2220 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2220
	_t2221 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2221
	_t2222 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2222
	_t2223 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2223
	_t2224 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2224
	_t2225 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2225
	_t2226 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2226
	_t2227 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2227
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2228 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2228
	config := dictFromList(storage_integration_opt)
	_t2229 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2230 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2231 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2232 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2233 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2234 := &pb.StorageIntegration{Provider: _t2229, AzureSasToken: _t2230, S3Region: _t2231, S3AccessKeyId: _t2232, S3SecretAccessKey: _t2233}
	return _t2234
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2235 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2235
	_t2236 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2236
	_t2237 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2237
	_t2238 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2238
	_t2239 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2239
	_t2240 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2240
	_t2241 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2241
	_t2242 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2242
	_t2243 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2243
	_t2244 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2244.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2244.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2244
	_t2245 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2245
}

func (p *Parser) default_configure() *pb.Configure {
	_t2246 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2246
	_t2247 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2247
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
	_t2248 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2248
	_t2249 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2249
	_t2250 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2250
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2251 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2251
	_t2252 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2252
	_t2253 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2253
	_t2254 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2254
	_t2255 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2255
	_t2256 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2256
	_t2257 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2257
	_t2258 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2258
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2259 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2259
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2260 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2260
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2261 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2261
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2262 := config_dict
	if config_dict == nil {
		_t2262 = [][]interface{}{}
	}
	cfg := dictFromList(_t2262)
	_t2263 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2263
	_t2264 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2264
	_t2265 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2265
	table_props := stringMapFromPairs(table_property_pairs)
	_t2266 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2266
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start710 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1408 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1409 := p.parse_configure()
		_t1408 = _t1409
	}
	configure704 := _t1408
	var _t1410 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1411 := p.parse_sync()
		_t1410 = _t1411
	}
	sync705 := _t1410
	xs706 := []*pb.Epoch{}
	cond707 := p.matchLookaheadLiteral("(", 0)
	for cond707 {
		_t1412 := p.parse_epoch()
		item708 := _t1412
		xs706 = append(xs706, item708)
		cond707 = p.matchLookaheadLiteral("(", 0)
	}
	epochs709 := xs706
	p.consumeLiteral(")")
	_t1413 := p.default_configure()
	_t1414 := configure704
	if configure704 == nil {
		_t1414 = _t1413
	}
	_t1415 := &pb.Transaction{Epochs: epochs709, Configure: _t1414, Sync: sync705}
	result711 := _t1415
	p.recordSpan(int(span_start710), "Transaction")
	return result711
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1416 := p.parse_config_dict()
	config_dict712 := _t1416
	p.consumeLiteral(")")
	_t1417 := p.construct_configure(config_dict712)
	result714 := _t1417
	p.recordSpan(int(span_start713), "Configure")
	return result714
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs715 := [][]interface{}{}
	cond716 := p.matchLookaheadLiteral(":", 0)
	for cond716 {
		_t1418 := p.parse_config_key_value()
		item717 := _t1418
		xs715 = append(xs715, item717)
		cond716 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values718 := xs715
	p.consumeLiteral("}")
	return config_key_values718
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol719 := p.consumeTerminal("SYMBOL").Value.str
	_t1419 := p.parse_raw_value()
	raw_value720 := _t1419
	return []interface{}{symbol719, raw_value720}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start734 := int64(p.spanStart())
	var _t1420 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1420 = 12
	} else {
		var _t1421 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1421 = 11
		} else {
			var _t1422 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1422 = 12
			} else {
				var _t1423 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1424 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1424 = 1
					} else {
						var _t1425 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1425 = 0
						} else {
							_t1425 = -1
						}
						_t1424 = _t1425
					}
					_t1423 = _t1424
				} else {
					var _t1426 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1426 = 7
					} else {
						var _t1427 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1427 = 8
						} else {
							var _t1428 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1428 = 2
							} else {
								var _t1429 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1429 = 3
								} else {
									var _t1430 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1430 = 9
									} else {
										var _t1431 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1431 = 4
										} else {
											var _t1432 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1432 = 5
											} else {
												var _t1433 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1433 = 6
												} else {
													var _t1434 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1434 = 10
													} else {
														_t1434 = -1
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
					_t1423 = _t1426
				}
				_t1422 = _t1423
			}
			_t1421 = _t1422
		}
		_t1420 = _t1421
	}
	prediction721 := _t1420
	var _t1435 *pb.Value
	if prediction721 == 12 {
		_t1436 := p.parse_boolean_value()
		boolean_value733 := _t1436
		_t1437 := &pb.Value{}
		_t1437.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value733}
		_t1435 = _t1437
	} else {
		var _t1438 *pb.Value
		if prediction721 == 11 {
			p.consumeLiteral("missing")
			_t1439 := &pb.MissingValue{}
			_t1440 := &pb.Value{}
			_t1440.Value = &pb.Value_MissingValue{MissingValue: _t1439}
			_t1438 = _t1440
		} else {
			var _t1441 *pb.Value
			if prediction721 == 10 {
				decimal732 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1442 := &pb.Value{}
				_t1442.Value = &pb.Value_DecimalValue{DecimalValue: decimal732}
				_t1441 = _t1442
			} else {
				var _t1443 *pb.Value
				if prediction721 == 9 {
					int128731 := p.consumeTerminal("INT128").Value.int128
					_t1444 := &pb.Value{}
					_t1444.Value = &pb.Value_Int128Value{Int128Value: int128731}
					_t1443 = _t1444
				} else {
					var _t1445 *pb.Value
					if prediction721 == 8 {
						uint128730 := p.consumeTerminal("UINT128").Value.uint128
						_t1446 := &pb.Value{}
						_t1446.Value = &pb.Value_Uint128Value{Uint128Value: uint128730}
						_t1445 = _t1446
					} else {
						var _t1447 *pb.Value
						if prediction721 == 7 {
							uint32729 := p.consumeTerminal("UINT32").Value.u32
							_t1448 := &pb.Value{}
							_t1448.Value = &pb.Value_Uint32Value{Uint32Value: uint32729}
							_t1447 = _t1448
						} else {
							var _t1449 *pb.Value
							if prediction721 == 6 {
								float728 := p.consumeTerminal("FLOAT").Value.f64
								_t1450 := &pb.Value{}
								_t1450.Value = &pb.Value_FloatValue{FloatValue: float728}
								_t1449 = _t1450
							} else {
								var _t1451 *pb.Value
								if prediction721 == 5 {
									float32727 := p.consumeTerminal("FLOAT32").Value.f32
									_t1452 := &pb.Value{}
									_t1452.Value = &pb.Value_Float32Value{Float32Value: float32727}
									_t1451 = _t1452
								} else {
									var _t1453 *pb.Value
									if prediction721 == 4 {
										int726 := p.consumeTerminal("INT").Value.i64
										_t1454 := &pb.Value{}
										_t1454.Value = &pb.Value_IntValue{IntValue: int726}
										_t1453 = _t1454
									} else {
										var _t1455 *pb.Value
										if prediction721 == 3 {
											int32725 := p.consumeTerminal("INT32").Value.i32
											_t1456 := &pb.Value{}
											_t1456.Value = &pb.Value_Int32Value{Int32Value: int32725}
											_t1455 = _t1456
										} else {
											var _t1457 *pb.Value
											if prediction721 == 2 {
												string724 := p.consumeTerminal("STRING").Value.str
												_t1458 := &pb.Value{}
												_t1458.Value = &pb.Value_StringValue{StringValue: string724}
												_t1457 = _t1458
											} else {
												var _t1459 *pb.Value
												if prediction721 == 1 {
													_t1460 := p.parse_raw_datetime()
													raw_datetime723 := _t1460
													_t1461 := &pb.Value{}
													_t1461.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime723}
													_t1459 = _t1461
												} else {
													var _t1462 *pb.Value
													if prediction721 == 0 {
														_t1463 := p.parse_raw_date()
														raw_date722 := _t1463
														_t1464 := &pb.Value{}
														_t1464.Value = &pb.Value_DateValue{DateValue: raw_date722}
														_t1462 = _t1464
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1459 = _t1462
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
						_t1445 = _t1447
					}
					_t1443 = _t1445
				}
				_t1441 = _t1443
			}
			_t1438 = _t1441
		}
		_t1435 = _t1438
	}
	result735 := _t1435
	p.recordSpan(int(span_start734), "Value")
	return result735
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int736 := p.consumeTerminal("INT").Value.i64
	int_3737 := p.consumeTerminal("INT").Value.i64
	int_4738 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1465 := &pb.DateValue{Year: int32(int736), Month: int32(int_3737), Day: int32(int_4738)}
	result740 := _t1465
	p.recordSpan(int(span_start739), "DateValue")
	return result740
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start748 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int741 := p.consumeTerminal("INT").Value.i64
	int_3742 := p.consumeTerminal("INT").Value.i64
	int_4743 := p.consumeTerminal("INT").Value.i64
	int_5744 := p.consumeTerminal("INT").Value.i64
	int_6745 := p.consumeTerminal("INT").Value.i64
	int_7746 := p.consumeTerminal("INT").Value.i64
	var _t1466 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1466 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8747 := _t1466
	p.consumeLiteral(")")
	_t1467 := &pb.DateTimeValue{Year: int32(int741), Month: int32(int_3742), Day: int32(int_4743), Hour: int32(int_5744), Minute: int32(int_6745), Second: int32(int_7746), Microsecond: int32(deref(int_8747, 0))}
	result749 := _t1467
	p.recordSpan(int(span_start748), "DateTimeValue")
	return result749
}

func (p *Parser) parse_boolean_value() bool {
	var _t1468 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1468 = 0
	} else {
		var _t1469 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1469 = 1
		} else {
			_t1469 = -1
		}
		_t1468 = _t1469
	}
	prediction750 := _t1468
	var _t1470 bool
	if prediction750 == 1 {
		p.consumeLiteral("false")
		_t1470 = false
	} else {
		var _t1471 bool
		if prediction750 == 0 {
			p.consumeLiteral("true")
			_t1471 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1470 = _t1471
	}
	return _t1470
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs751 := []*pb.FragmentId{}
	cond752 := p.matchLookaheadLiteral(":", 0)
	for cond752 {
		_t1472 := p.parse_fragment_id()
		item753 := _t1472
		xs751 = append(xs751, item753)
		cond752 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids754 := xs751
	p.consumeLiteral(")")
	_t1473 := &pb.Sync{Fragments: fragment_ids754}
	result756 := _t1473
	p.recordSpan(int(span_start755), "Sync")
	return result756
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start758 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol757 := p.consumeTerminal("SYMBOL").Value.str
	result759 := &pb.FragmentId{Id: []byte(symbol757)}
	p.recordSpan(int(span_start758), "FragmentId")
	return result759
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start762 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1474 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1475 := p.parse_epoch_writes()
		_t1474 = _t1475
	}
	epoch_writes760 := _t1474
	var _t1476 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1477 := p.parse_epoch_reads()
		_t1476 = _t1477
	}
	epoch_reads761 := _t1476
	p.consumeLiteral(")")
	_t1478 := epoch_writes760
	if epoch_writes760 == nil {
		_t1478 = []*pb.Write{}
	}
	_t1479 := epoch_reads761
	if epoch_reads761 == nil {
		_t1479 = []*pb.Read{}
	}
	_t1480 := &pb.Epoch{Writes: _t1478, Reads: _t1479}
	result763 := _t1480
	p.recordSpan(int(span_start762), "Epoch")
	return result763
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs764 := []*pb.Write{}
	cond765 := p.matchLookaheadLiteral("(", 0)
	for cond765 {
		_t1481 := p.parse_write()
		item766 := _t1481
		xs764 = append(xs764, item766)
		cond765 = p.matchLookaheadLiteral("(", 0)
	}
	writes767 := xs764
	p.consumeLiteral(")")
	return writes767
}

func (p *Parser) parse_write() *pb.Write {
	span_start773 := int64(p.spanStart())
	var _t1482 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1483 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1483 = 1
		} else {
			var _t1484 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1484 = 3
			} else {
				var _t1485 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1485 = 0
				} else {
					var _t1486 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1486 = 2
					} else {
						_t1486 = -1
					}
					_t1485 = _t1486
				}
				_t1484 = _t1485
			}
			_t1483 = _t1484
		}
		_t1482 = _t1483
	} else {
		_t1482 = -1
	}
	prediction768 := _t1482
	var _t1487 *pb.Write
	if prediction768 == 3 {
		_t1488 := p.parse_snapshot()
		snapshot772 := _t1488
		_t1489 := &pb.Write{}
		_t1489.WriteType = &pb.Write_Snapshot{Snapshot: snapshot772}
		_t1487 = _t1489
	} else {
		var _t1490 *pb.Write
		if prediction768 == 2 {
			_t1491 := p.parse_context()
			context771 := _t1491
			_t1492 := &pb.Write{}
			_t1492.WriteType = &pb.Write_Context{Context: context771}
			_t1490 = _t1492
		} else {
			var _t1493 *pb.Write
			if prediction768 == 1 {
				_t1494 := p.parse_undefine()
				undefine770 := _t1494
				_t1495 := &pb.Write{}
				_t1495.WriteType = &pb.Write_Undefine{Undefine: undefine770}
				_t1493 = _t1495
			} else {
				var _t1496 *pb.Write
				if prediction768 == 0 {
					_t1497 := p.parse_define()
					define769 := _t1497
					_t1498 := &pb.Write{}
					_t1498.WriteType = &pb.Write_Define{Define: define769}
					_t1496 = _t1498
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1493 = _t1496
			}
			_t1490 = _t1493
		}
		_t1487 = _t1490
	}
	result774 := _t1487
	p.recordSpan(int(span_start773), "Write")
	return result774
}

func (p *Parser) parse_define() *pb.Define {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1499 := p.parse_fragment()
	fragment775 := _t1499
	p.consumeLiteral(")")
	_t1500 := &pb.Define{Fragment: fragment775}
	result777 := _t1500
	p.recordSpan(int(span_start776), "Define")
	return result777
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start783 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1501 := p.parse_new_fragment_id()
	new_fragment_id778 := _t1501
	xs779 := []*pb.Declaration{}
	cond780 := p.matchLookaheadLiteral("(", 0)
	for cond780 {
		_t1502 := p.parse_declaration()
		item781 := _t1502
		xs779 = append(xs779, item781)
		cond780 = p.matchLookaheadLiteral("(", 0)
	}
	declarations782 := xs779
	p.consumeLiteral(")")
	result784 := p.constructFragment(new_fragment_id778, declarations782)
	p.recordSpan(int(span_start783), "Fragment")
	return result784
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start786 := int64(p.spanStart())
	_t1503 := p.parse_fragment_id()
	fragment_id785 := _t1503
	p.startFragment(fragment_id785)
	result787 := fragment_id785
	p.recordSpan(int(span_start786), "FragmentId")
	return result787
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start793 := int64(p.spanStart())
	var _t1504 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1505 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1505 = 3
		} else {
			var _t1506 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1506 = 2
			} else {
				var _t1507 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1507 = 3
				} else {
					var _t1508 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1508 = 0
					} else {
						var _t1509 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1509 = 3
						} else {
							var _t1510 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1510 = 3
							} else {
								var _t1511 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1511 = 1
								} else {
									_t1511 = -1
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
	} else {
		_t1504 = -1
	}
	prediction788 := _t1504
	var _t1512 *pb.Declaration
	if prediction788 == 3 {
		_t1513 := p.parse_data()
		data792 := _t1513
		_t1514 := &pb.Declaration{}
		_t1514.DeclarationType = &pb.Declaration_Data{Data: data792}
		_t1512 = _t1514
	} else {
		var _t1515 *pb.Declaration
		if prediction788 == 2 {
			_t1516 := p.parse_constraint()
			constraint791 := _t1516
			_t1517 := &pb.Declaration{}
			_t1517.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint791}
			_t1515 = _t1517
		} else {
			var _t1518 *pb.Declaration
			if prediction788 == 1 {
				_t1519 := p.parse_algorithm()
				algorithm790 := _t1519
				_t1520 := &pb.Declaration{}
				_t1520.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm790}
				_t1518 = _t1520
			} else {
				var _t1521 *pb.Declaration
				if prediction788 == 0 {
					_t1522 := p.parse_def()
					def789 := _t1522
					_t1523 := &pb.Declaration{}
					_t1523.DeclarationType = &pb.Declaration_Def{Def: def789}
					_t1521 = _t1523
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1518 = _t1521
			}
			_t1515 = _t1518
		}
		_t1512 = _t1515
	}
	result794 := _t1512
	p.recordSpan(int(span_start793), "Declaration")
	return result794
}

func (p *Parser) parse_def() *pb.Def {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1524 := p.parse_relation_id()
	relation_id795 := _t1524
	_t1525 := p.parse_abstraction()
	abstraction796 := _t1525
	var _t1526 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1527 := p.parse_attrs()
		_t1526 = _t1527
	}
	attrs797 := _t1526
	p.consumeLiteral(")")
	_t1528 := attrs797
	if attrs797 == nil {
		_t1528 = []*pb.Attribute{}
	}
	_t1529 := &pb.Def{Name: relation_id795, Body: abstraction796, Attrs: _t1528}
	result799 := _t1529
	p.recordSpan(int(span_start798), "Def")
	return result799
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start803 := int64(p.spanStart())
	var _t1530 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1530 = 0
	} else {
		var _t1531 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1531 = 1
		} else {
			_t1531 = -1
		}
		_t1530 = _t1531
	}
	prediction800 := _t1530
	var _t1532 *pb.RelationId
	if prediction800 == 1 {
		uint128802 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128802
		_t1532 = &pb.RelationId{IdLow: uint128802.Low, IdHigh: uint128802.High}
	} else {
		var _t1533 *pb.RelationId
		if prediction800 == 0 {
			p.consumeLiteral(":")
			symbol801 := p.consumeTerminal("SYMBOL").Value.str
			_t1533 = p.relationIdFromString(symbol801)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1532 = _t1533
	}
	result804 := _t1532
	p.recordSpan(int(span_start803), "RelationId")
	return result804
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1534 := p.parse_bindings()
	bindings805 := _t1534
	_t1535 := p.parse_formula()
	formula806 := _t1535
	p.consumeLiteral(")")
	_t1536 := &pb.Abstraction{Vars: listConcat(bindings805[0].([]*pb.Binding), bindings805[1].([]*pb.Binding)), Value: formula806}
	result808 := _t1536
	p.recordSpan(int(span_start807), "Abstraction")
	return result808
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs809 := []*pb.Binding{}
	cond810 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond810 {
		_t1537 := p.parse_binding()
		item811 := _t1537
		xs809 = append(xs809, item811)
		cond810 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings812 := xs809
	var _t1538 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1539 := p.parse_value_bindings()
		_t1538 = _t1539
	}
	value_bindings813 := _t1538
	p.consumeLiteral("]")
	_t1540 := value_bindings813
	if value_bindings813 == nil {
		_t1540 = []*pb.Binding{}
	}
	return []interface{}{bindings812, _t1540}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start816 := int64(p.spanStart())
	symbol814 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1541 := p.parse_type()
	type815 := _t1541
	_t1542 := &pb.Var{Name: symbol814}
	_t1543 := &pb.Binding{Var: _t1542, Type: type815}
	result817 := _t1543
	p.recordSpan(int(span_start816), "Binding")
	return result817
}

func (p *Parser) parse_type() *pb.Type {
	span_start833 := int64(p.spanStart())
	var _t1544 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1544 = 0
	} else {
		var _t1545 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1545 = 13
		} else {
			var _t1546 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1546 = 4
			} else {
				var _t1547 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1547 = 1
				} else {
					var _t1548 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1548 = 8
					} else {
						var _t1549 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1549 = 11
						} else {
							var _t1550 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1550 = 5
							} else {
								var _t1551 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1551 = 2
								} else {
									var _t1552 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1552 = 12
									} else {
										var _t1553 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1553 = 3
										} else {
											var _t1554 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1554 = 7
											} else {
												var _t1555 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1555 = 6
												} else {
													var _t1556 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1556 = 10
													} else {
														var _t1557 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1557 = 9
														} else {
															_t1557 = -1
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
	prediction818 := _t1544
	var _t1558 *pb.Type
	if prediction818 == 13 {
		_t1559 := p.parse_uint32_type()
		uint32_type832 := _t1559
		_t1560 := &pb.Type{}
		_t1560.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type832}
		_t1558 = _t1560
	} else {
		var _t1561 *pb.Type
		if prediction818 == 12 {
			_t1562 := p.parse_float32_type()
			float32_type831 := _t1562
			_t1563 := &pb.Type{}
			_t1563.Type = &pb.Type_Float32Type{Float32Type: float32_type831}
			_t1561 = _t1563
		} else {
			var _t1564 *pb.Type
			if prediction818 == 11 {
				_t1565 := p.parse_int32_type()
				int32_type830 := _t1565
				_t1566 := &pb.Type{}
				_t1566.Type = &pb.Type_Int32Type{Int32Type: int32_type830}
				_t1564 = _t1566
			} else {
				var _t1567 *pb.Type
				if prediction818 == 10 {
					_t1568 := p.parse_boolean_type()
					boolean_type829 := _t1568
					_t1569 := &pb.Type{}
					_t1569.Type = &pb.Type_BooleanType{BooleanType: boolean_type829}
					_t1567 = _t1569
				} else {
					var _t1570 *pb.Type
					if prediction818 == 9 {
						_t1571 := p.parse_decimal_type()
						decimal_type828 := _t1571
						_t1572 := &pb.Type{}
						_t1572.Type = &pb.Type_DecimalType{DecimalType: decimal_type828}
						_t1570 = _t1572
					} else {
						var _t1573 *pb.Type
						if prediction818 == 8 {
							_t1574 := p.parse_missing_type()
							missing_type827 := _t1574
							_t1575 := &pb.Type{}
							_t1575.Type = &pb.Type_MissingType{MissingType: missing_type827}
							_t1573 = _t1575
						} else {
							var _t1576 *pb.Type
							if prediction818 == 7 {
								_t1577 := p.parse_datetime_type()
								datetime_type826 := _t1577
								_t1578 := &pb.Type{}
								_t1578.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type826}
								_t1576 = _t1578
							} else {
								var _t1579 *pb.Type
								if prediction818 == 6 {
									_t1580 := p.parse_date_type()
									date_type825 := _t1580
									_t1581 := &pb.Type{}
									_t1581.Type = &pb.Type_DateType{DateType: date_type825}
									_t1579 = _t1581
								} else {
									var _t1582 *pb.Type
									if prediction818 == 5 {
										_t1583 := p.parse_int128_type()
										int128_type824 := _t1583
										_t1584 := &pb.Type{}
										_t1584.Type = &pb.Type_Int128Type{Int128Type: int128_type824}
										_t1582 = _t1584
									} else {
										var _t1585 *pb.Type
										if prediction818 == 4 {
											_t1586 := p.parse_uint128_type()
											uint128_type823 := _t1586
											_t1587 := &pb.Type{}
											_t1587.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type823}
											_t1585 = _t1587
										} else {
											var _t1588 *pb.Type
											if prediction818 == 3 {
												_t1589 := p.parse_float_type()
												float_type822 := _t1589
												_t1590 := &pb.Type{}
												_t1590.Type = &pb.Type_FloatType{FloatType: float_type822}
												_t1588 = _t1590
											} else {
												var _t1591 *pb.Type
												if prediction818 == 2 {
													_t1592 := p.parse_int_type()
													int_type821 := _t1592
													_t1593 := &pb.Type{}
													_t1593.Type = &pb.Type_IntType{IntType: int_type821}
													_t1591 = _t1593
												} else {
													var _t1594 *pb.Type
													if prediction818 == 1 {
														_t1595 := p.parse_string_type()
														string_type820 := _t1595
														_t1596 := &pb.Type{}
														_t1596.Type = &pb.Type_StringType{StringType: string_type820}
														_t1594 = _t1596
													} else {
														var _t1597 *pb.Type
														if prediction818 == 0 {
															_t1598 := p.parse_unspecified_type()
															unspecified_type819 := _t1598
															_t1599 := &pb.Type{}
															_t1599.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type819}
															_t1597 = _t1599
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1561 = _t1564
		}
		_t1558 = _t1561
	}
	result834 := _t1558
	p.recordSpan(int(span_start833), "Type")
	return result834
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start835 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1600 := &pb.UnspecifiedType{}
	result836 := _t1600
	p.recordSpan(int(span_start835), "UnspecifiedType")
	return result836
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1601 := &pb.StringType{}
	result838 := _t1601
	p.recordSpan(int(span_start837), "StringType")
	return result838
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1602 := &pb.IntType{}
	result840 := _t1602
	p.recordSpan(int(span_start839), "IntType")
	return result840
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1603 := &pb.FloatType{}
	result842 := _t1603
	p.recordSpan(int(span_start841), "FloatType")
	return result842
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1604 := &pb.UInt128Type{}
	result844 := _t1604
	p.recordSpan(int(span_start843), "UInt128Type")
	return result844
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1605 := &pb.Int128Type{}
	result846 := _t1605
	p.recordSpan(int(span_start845), "Int128Type")
	return result846
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1606 := &pb.DateType{}
	result848 := _t1606
	p.recordSpan(int(span_start847), "DateType")
	return result848
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1607 := &pb.DateTimeType{}
	result850 := _t1607
	p.recordSpan(int(span_start849), "DateTimeType")
	return result850
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1608 := &pb.MissingType{}
	result852 := _t1608
	p.recordSpan(int(span_start851), "MissingType")
	return result852
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int853 := p.consumeTerminal("INT").Value.i64
	int_3854 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1609 := &pb.DecimalType{Precision: int32(int853), Scale: int32(int_3854)}
	result856 := _t1609
	p.recordSpan(int(span_start855), "DecimalType")
	return result856
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1610 := &pb.BooleanType{}
	result858 := _t1610
	p.recordSpan(int(span_start857), "BooleanType")
	return result858
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1611 := &pb.Int32Type{}
	result860 := _t1611
	p.recordSpan(int(span_start859), "Int32Type")
	return result860
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1612 := &pb.Float32Type{}
	result862 := _t1612
	p.recordSpan(int(span_start861), "Float32Type")
	return result862
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1613 := &pb.UInt32Type{}
	result864 := _t1613
	p.recordSpan(int(span_start863), "UInt32Type")
	return result864
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs865 := []*pb.Binding{}
	cond866 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond866 {
		_t1614 := p.parse_binding()
		item867 := _t1614
		xs865 = append(xs865, item867)
		cond866 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings868 := xs865
	return bindings868
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start883 := int64(p.spanStart())
	var _t1615 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1616 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1616 = 0
		} else {
			var _t1617 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1617 = 11
			} else {
				var _t1618 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1618 = 3
				} else {
					var _t1619 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1619 = 10
					} else {
						var _t1620 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1620 = 9
						} else {
							var _t1621 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1621 = 5
							} else {
								var _t1622 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1622 = 6
								} else {
									var _t1623 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1623 = 7
									} else {
										var _t1624 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1624 = 1
										} else {
											var _t1625 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1625 = 2
											} else {
												var _t1626 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1626 = 12
												} else {
													var _t1627 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1627 = 8
													} else {
														var _t1628 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1628 = 4
														} else {
															var _t1629 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1629 = 10
															} else {
																var _t1630 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1630 = 10
																} else {
																	var _t1631 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1631 = 10
																	} else {
																		var _t1632 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1632 = 10
																		} else {
																			var _t1633 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1633 = 10
																			} else {
																				var _t1634 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1634 = 10
																				} else {
																					var _t1635 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1635 = 10
																					} else {
																						var _t1636 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1636 = 10
																						} else {
																							var _t1637 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1637 = 10
																							} else {
																								_t1637 = -1
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
							}
							_t1620 = _t1621
						}
						_t1619 = _t1620
					}
					_t1618 = _t1619
				}
				_t1617 = _t1618
			}
			_t1616 = _t1617
		}
		_t1615 = _t1616
	} else {
		_t1615 = -1
	}
	prediction869 := _t1615
	var _t1638 *pb.Formula
	if prediction869 == 12 {
		_t1639 := p.parse_cast()
		cast882 := _t1639
		_t1640 := &pb.Formula{}
		_t1640.FormulaType = &pb.Formula_Cast{Cast: cast882}
		_t1638 = _t1640
	} else {
		var _t1641 *pb.Formula
		if prediction869 == 11 {
			_t1642 := p.parse_rel_atom()
			rel_atom881 := _t1642
			_t1643 := &pb.Formula{}
			_t1643.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom881}
			_t1641 = _t1643
		} else {
			var _t1644 *pb.Formula
			if prediction869 == 10 {
				_t1645 := p.parse_primitive()
				primitive880 := _t1645
				_t1646 := &pb.Formula{}
				_t1646.FormulaType = &pb.Formula_Primitive{Primitive: primitive880}
				_t1644 = _t1646
			} else {
				var _t1647 *pb.Formula
				if prediction869 == 9 {
					_t1648 := p.parse_pragma()
					pragma879 := _t1648
					_t1649 := &pb.Formula{}
					_t1649.FormulaType = &pb.Formula_Pragma{Pragma: pragma879}
					_t1647 = _t1649
				} else {
					var _t1650 *pb.Formula
					if prediction869 == 8 {
						_t1651 := p.parse_atom()
						atom878 := _t1651
						_t1652 := &pb.Formula{}
						_t1652.FormulaType = &pb.Formula_Atom{Atom: atom878}
						_t1650 = _t1652
					} else {
						var _t1653 *pb.Formula
						if prediction869 == 7 {
							_t1654 := p.parse_ffi()
							ffi877 := _t1654
							_t1655 := &pb.Formula{}
							_t1655.FormulaType = &pb.Formula_Ffi{Ffi: ffi877}
							_t1653 = _t1655
						} else {
							var _t1656 *pb.Formula
							if prediction869 == 6 {
								_t1657 := p.parse_not()
								not876 := _t1657
								_t1658 := &pb.Formula{}
								_t1658.FormulaType = &pb.Formula_Not{Not: not876}
								_t1656 = _t1658
							} else {
								var _t1659 *pb.Formula
								if prediction869 == 5 {
									_t1660 := p.parse_disjunction()
									disjunction875 := _t1660
									_t1661 := &pb.Formula{}
									_t1661.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction875}
									_t1659 = _t1661
								} else {
									var _t1662 *pb.Formula
									if prediction869 == 4 {
										_t1663 := p.parse_conjunction()
										conjunction874 := _t1663
										_t1664 := &pb.Formula{}
										_t1664.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction874}
										_t1662 = _t1664
									} else {
										var _t1665 *pb.Formula
										if prediction869 == 3 {
											_t1666 := p.parse_reduce()
											reduce873 := _t1666
											_t1667 := &pb.Formula{}
											_t1667.FormulaType = &pb.Formula_Reduce{Reduce: reduce873}
											_t1665 = _t1667
										} else {
											var _t1668 *pb.Formula
											if prediction869 == 2 {
												_t1669 := p.parse_exists()
												exists872 := _t1669
												_t1670 := &pb.Formula{}
												_t1670.FormulaType = &pb.Formula_Exists{Exists: exists872}
												_t1668 = _t1670
											} else {
												var _t1671 *pb.Formula
												if prediction869 == 1 {
													_t1672 := p.parse_false()
													false871 := _t1672
													_t1673 := &pb.Formula{}
													_t1673.FormulaType = &pb.Formula_Disjunction{Disjunction: false871}
													_t1671 = _t1673
												} else {
													var _t1674 *pb.Formula
													if prediction869 == 0 {
														_t1675 := p.parse_true()
														true870 := _t1675
														_t1676 := &pb.Formula{}
														_t1676.FormulaType = &pb.Formula_Conjunction{Conjunction: true870}
														_t1674 = _t1676
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1641 = _t1644
		}
		_t1638 = _t1641
	}
	result884 := _t1638
	p.recordSpan(int(span_start883), "Formula")
	return result884
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start885 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1677 := &pb.Conjunction{Args: []*pb.Formula{}}
	result886 := _t1677
	p.recordSpan(int(span_start885), "Conjunction")
	return result886
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start887 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1678 := &pb.Disjunction{Args: []*pb.Formula{}}
	result888 := _t1678
	p.recordSpan(int(span_start887), "Disjunction")
	return result888
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1679 := p.parse_bindings()
	bindings889 := _t1679
	_t1680 := p.parse_formula()
	formula890 := _t1680
	p.consumeLiteral(")")
	_t1681 := &pb.Abstraction{Vars: listConcat(bindings889[0].([]*pb.Binding), bindings889[1].([]*pb.Binding)), Value: formula890}
	_t1682 := &pb.Exists{Body: _t1681}
	result892 := _t1682
	p.recordSpan(int(span_start891), "Exists")
	return result892
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1683 := p.parse_abstraction()
	abstraction893 := _t1683
	_t1684 := p.parse_abstraction()
	abstraction_3894 := _t1684
	_t1685 := p.parse_terms()
	terms895 := _t1685
	p.consumeLiteral(")")
	_t1686 := &pb.Reduce{Op: abstraction893, Body: abstraction_3894, Terms: terms895}
	result897 := _t1686
	p.recordSpan(int(span_start896), "Reduce")
	return result897
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs898 := []*pb.Term{}
	cond899 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond899 {
		_t1687 := p.parse_term()
		item900 := _t1687
		xs898 = append(xs898, item900)
		cond899 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms901 := xs898
	p.consumeLiteral(")")
	return terms901
}

func (p *Parser) parse_term() *pb.Term {
	span_start905 := int64(p.spanStart())
	var _t1688 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1688 = 1
	} else {
		var _t1689 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1689 = 1
		} else {
			var _t1690 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1690 = 1
			} else {
				var _t1691 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1691 = 1
				} else {
					var _t1692 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1692 = 0
					} else {
						var _t1693 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1693 = 1
						} else {
							var _t1694 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1694 = 1
							} else {
								var _t1695 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1695 = 1
								} else {
									var _t1696 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1696 = 1
									} else {
										var _t1697 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1697 = 1
										} else {
											var _t1698 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1698 = 1
											} else {
												var _t1699 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1699 = 1
												} else {
													var _t1700 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1700 = 1
													} else {
														var _t1701 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1701 = 1
														} else {
															_t1701 = -1
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
							_t1693 = _t1694
						}
						_t1692 = _t1693
					}
					_t1691 = _t1692
				}
				_t1690 = _t1691
			}
			_t1689 = _t1690
		}
		_t1688 = _t1689
	}
	prediction902 := _t1688
	var _t1702 *pb.Term
	if prediction902 == 1 {
		_t1703 := p.parse_value()
		value904 := _t1703
		_t1704 := &pb.Term{}
		_t1704.TermType = &pb.Term_Constant{Constant: value904}
		_t1702 = _t1704
	} else {
		var _t1705 *pb.Term
		if prediction902 == 0 {
			_t1706 := p.parse_var()
			var903 := _t1706
			_t1707 := &pb.Term{}
			_t1707.TermType = &pb.Term_Var{Var: var903}
			_t1705 = _t1707
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1702 = _t1705
	}
	result906 := _t1702
	p.recordSpan(int(span_start905), "Term")
	return result906
}

func (p *Parser) parse_var() *pb.Var {
	span_start908 := int64(p.spanStart())
	symbol907 := p.consumeTerminal("SYMBOL").Value.str
	_t1708 := &pb.Var{Name: symbol907}
	result909 := _t1708
	p.recordSpan(int(span_start908), "Var")
	return result909
}

func (p *Parser) parse_value() *pb.Value {
	span_start923 := int64(p.spanStart())
	var _t1709 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1709 = 12
	} else {
		var _t1710 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1710 = 11
		} else {
			var _t1711 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1711 = 12
			} else {
				var _t1712 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1713 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1713 = 1
					} else {
						var _t1714 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1714 = 0
						} else {
							_t1714 = -1
						}
						_t1713 = _t1714
					}
					_t1712 = _t1713
				} else {
					var _t1715 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1715 = 7
					} else {
						var _t1716 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1716 = 8
						} else {
							var _t1717 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1717 = 2
							} else {
								var _t1718 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1718 = 3
								} else {
									var _t1719 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1719 = 9
									} else {
										var _t1720 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1720 = 4
										} else {
											var _t1721 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1721 = 5
											} else {
												var _t1722 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1722 = 6
												} else {
													var _t1723 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1723 = 10
													} else {
														_t1723 = -1
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
								_t1717 = _t1718
							}
							_t1716 = _t1717
						}
						_t1715 = _t1716
					}
					_t1712 = _t1715
				}
				_t1711 = _t1712
			}
			_t1710 = _t1711
		}
		_t1709 = _t1710
	}
	prediction910 := _t1709
	var _t1724 *pb.Value
	if prediction910 == 12 {
		_t1725 := p.parse_boolean_value()
		boolean_value922 := _t1725
		_t1726 := &pb.Value{}
		_t1726.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value922}
		_t1724 = _t1726
	} else {
		var _t1727 *pb.Value
		if prediction910 == 11 {
			p.consumeLiteral("missing")
			_t1728 := &pb.MissingValue{}
			_t1729 := &pb.Value{}
			_t1729.Value = &pb.Value_MissingValue{MissingValue: _t1728}
			_t1727 = _t1729
		} else {
			var _t1730 *pb.Value
			if prediction910 == 10 {
				formatted_decimal921 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1731 := &pb.Value{}
				_t1731.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal921}
				_t1730 = _t1731
			} else {
				var _t1732 *pb.Value
				if prediction910 == 9 {
					formatted_int128920 := p.consumeTerminal("INT128").Value.int128
					_t1733 := &pb.Value{}
					_t1733.Value = &pb.Value_Int128Value{Int128Value: formatted_int128920}
					_t1732 = _t1733
				} else {
					var _t1734 *pb.Value
					if prediction910 == 8 {
						formatted_uint128919 := p.consumeTerminal("UINT128").Value.uint128
						_t1735 := &pb.Value{}
						_t1735.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128919}
						_t1734 = _t1735
					} else {
						var _t1736 *pb.Value
						if prediction910 == 7 {
							formatted_uint32918 := p.consumeTerminal("UINT32").Value.u32
							_t1737 := &pb.Value{}
							_t1737.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32918}
							_t1736 = _t1737
						} else {
							var _t1738 *pb.Value
							if prediction910 == 6 {
								formatted_float917 := p.consumeTerminal("FLOAT").Value.f64
								_t1739 := &pb.Value{}
								_t1739.Value = &pb.Value_FloatValue{FloatValue: formatted_float917}
								_t1738 = _t1739
							} else {
								var _t1740 *pb.Value
								if prediction910 == 5 {
									formatted_float32916 := p.consumeTerminal("FLOAT32").Value.f32
									_t1741 := &pb.Value{}
									_t1741.Value = &pb.Value_Float32Value{Float32Value: formatted_float32916}
									_t1740 = _t1741
								} else {
									var _t1742 *pb.Value
									if prediction910 == 4 {
										formatted_int915 := p.consumeTerminal("INT").Value.i64
										_t1743 := &pb.Value{}
										_t1743.Value = &pb.Value_IntValue{IntValue: formatted_int915}
										_t1742 = _t1743
									} else {
										var _t1744 *pb.Value
										if prediction910 == 3 {
											formatted_int32914 := p.consumeTerminal("INT32").Value.i32
											_t1745 := &pb.Value{}
											_t1745.Value = &pb.Value_Int32Value{Int32Value: formatted_int32914}
											_t1744 = _t1745
										} else {
											var _t1746 *pb.Value
											if prediction910 == 2 {
												formatted_string913 := p.consumeTerminal("STRING").Value.str
												_t1747 := &pb.Value{}
												_t1747.Value = &pb.Value_StringValue{StringValue: formatted_string913}
												_t1746 = _t1747
											} else {
												var _t1748 *pb.Value
												if prediction910 == 1 {
													_t1749 := p.parse_datetime()
													datetime912 := _t1749
													_t1750 := &pb.Value{}
													_t1750.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime912}
													_t1748 = _t1750
												} else {
													var _t1751 *pb.Value
													if prediction910 == 0 {
														_t1752 := p.parse_date()
														date911 := _t1752
														_t1753 := &pb.Value{}
														_t1753.Value = &pb.Value_DateValue{DateValue: date911}
														_t1751 = _t1753
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1748 = _t1751
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
						_t1734 = _t1736
					}
					_t1732 = _t1734
				}
				_t1730 = _t1732
			}
			_t1727 = _t1730
		}
		_t1724 = _t1727
	}
	result924 := _t1724
	p.recordSpan(int(span_start923), "Value")
	return result924
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start928 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int925 := p.consumeTerminal("INT").Value.i64
	formatted_int_3926 := p.consumeTerminal("INT").Value.i64
	formatted_int_4927 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1754 := &pb.DateValue{Year: int32(formatted_int925), Month: int32(formatted_int_3926), Day: int32(formatted_int_4927)}
	result929 := _t1754
	p.recordSpan(int(span_start928), "DateValue")
	return result929
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start937 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int930 := p.consumeTerminal("INT").Value.i64
	formatted_int_3931 := p.consumeTerminal("INT").Value.i64
	formatted_int_4932 := p.consumeTerminal("INT").Value.i64
	formatted_int_5933 := p.consumeTerminal("INT").Value.i64
	formatted_int_6934 := p.consumeTerminal("INT").Value.i64
	formatted_int_7935 := p.consumeTerminal("INT").Value.i64
	var _t1755 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1755 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8936 := _t1755
	p.consumeLiteral(")")
	_t1756 := &pb.DateTimeValue{Year: int32(formatted_int930), Month: int32(formatted_int_3931), Day: int32(formatted_int_4932), Hour: int32(formatted_int_5933), Minute: int32(formatted_int_6934), Second: int32(formatted_int_7935), Microsecond: int32(deref(formatted_int_8936, 0))}
	result938 := _t1756
	p.recordSpan(int(span_start937), "DateTimeValue")
	return result938
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start943 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs939 := []*pb.Formula{}
	cond940 := p.matchLookaheadLiteral("(", 0)
	for cond940 {
		_t1757 := p.parse_formula()
		item941 := _t1757
		xs939 = append(xs939, item941)
		cond940 = p.matchLookaheadLiteral("(", 0)
	}
	formulas942 := xs939
	p.consumeLiteral(")")
	_t1758 := &pb.Conjunction{Args: formulas942}
	result944 := _t1758
	p.recordSpan(int(span_start943), "Conjunction")
	return result944
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start949 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs945 := []*pb.Formula{}
	cond946 := p.matchLookaheadLiteral("(", 0)
	for cond946 {
		_t1759 := p.parse_formula()
		item947 := _t1759
		xs945 = append(xs945, item947)
		cond946 = p.matchLookaheadLiteral("(", 0)
	}
	formulas948 := xs945
	p.consumeLiteral(")")
	_t1760 := &pb.Disjunction{Args: formulas948}
	result950 := _t1760
	p.recordSpan(int(span_start949), "Disjunction")
	return result950
}

func (p *Parser) parse_not() *pb.Not {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1761 := p.parse_formula()
	formula951 := _t1761
	p.consumeLiteral(")")
	_t1762 := &pb.Not{Arg: formula951}
	result953 := _t1762
	p.recordSpan(int(span_start952), "Not")
	return result953
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1763 := p.parse_name()
	name954 := _t1763
	_t1764 := p.parse_ffi_args()
	ffi_args955 := _t1764
	_t1765 := p.parse_terms()
	terms956 := _t1765
	p.consumeLiteral(")")
	_t1766 := &pb.FFI{Name: name954, Args: ffi_args955, Terms: terms956}
	result958 := _t1766
	p.recordSpan(int(span_start957), "FFI")
	return result958
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol959 := p.consumeTerminal("SYMBOL").Value.str
	return symbol959
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs960 := []*pb.Abstraction{}
	cond961 := p.matchLookaheadLiteral("(", 0)
	for cond961 {
		_t1767 := p.parse_abstraction()
		item962 := _t1767
		xs960 = append(xs960, item962)
		cond961 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions963 := xs960
	p.consumeLiteral(")")
	return abstractions963
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1768 := p.parse_relation_id()
	relation_id964 := _t1768
	xs965 := []*pb.Term{}
	cond966 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond966 {
		_t1769 := p.parse_term()
		item967 := _t1769
		xs965 = append(xs965, item967)
		cond966 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms968 := xs965
	p.consumeLiteral(")")
	_t1770 := &pb.Atom{Name: relation_id964, Terms: terms968}
	result970 := _t1770
	p.recordSpan(int(span_start969), "Atom")
	return result970
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1771 := p.parse_name()
	name971 := _t1771
	xs972 := []*pb.Term{}
	cond973 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond973 {
		_t1772 := p.parse_term()
		item974 := _t1772
		xs972 = append(xs972, item974)
		cond973 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms975 := xs972
	p.consumeLiteral(")")
	_t1773 := &pb.Pragma{Name: name971, Terms: terms975}
	result977 := _t1773
	p.recordSpan(int(span_start976), "Pragma")
	return result977
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start993 := int64(p.spanStart())
	var _t1774 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1775 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1775 = 9
		} else {
			var _t1776 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1776 = 4
			} else {
				var _t1777 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1777 = 3
				} else {
					var _t1778 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1778 = 0
					} else {
						var _t1779 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1779 = 2
						} else {
							var _t1780 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1780 = 1
							} else {
								var _t1781 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1781 = 8
								} else {
									var _t1782 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1782 = 6
									} else {
										var _t1783 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1783 = 5
										} else {
											var _t1784 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1784 = 7
											} else {
												_t1784 = -1
											}
											_t1783 = _t1784
										}
										_t1782 = _t1783
									}
									_t1781 = _t1782
								}
								_t1780 = _t1781
							}
							_t1779 = _t1780
						}
						_t1778 = _t1779
					}
					_t1777 = _t1778
				}
				_t1776 = _t1777
			}
			_t1775 = _t1776
		}
		_t1774 = _t1775
	} else {
		_t1774 = -1
	}
	prediction978 := _t1774
	var _t1785 *pb.Primitive
	if prediction978 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1786 := p.parse_name()
		name988 := _t1786
		xs989 := []*pb.RelTerm{}
		cond990 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond990 {
			_t1787 := p.parse_rel_term()
			item991 := _t1787
			xs989 = append(xs989, item991)
			cond990 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms992 := xs989
		p.consumeLiteral(")")
		_t1788 := &pb.Primitive{Name: name988, Terms: rel_terms992}
		_t1785 = _t1788
	} else {
		var _t1789 *pb.Primitive
		if prediction978 == 8 {
			_t1790 := p.parse_divide()
			divide987 := _t1790
			_t1789 = divide987
		} else {
			var _t1791 *pb.Primitive
			if prediction978 == 7 {
				_t1792 := p.parse_multiply()
				multiply986 := _t1792
				_t1791 = multiply986
			} else {
				var _t1793 *pb.Primitive
				if prediction978 == 6 {
					_t1794 := p.parse_minus()
					minus985 := _t1794
					_t1793 = minus985
				} else {
					var _t1795 *pb.Primitive
					if prediction978 == 5 {
						_t1796 := p.parse_add()
						add984 := _t1796
						_t1795 = add984
					} else {
						var _t1797 *pb.Primitive
						if prediction978 == 4 {
							_t1798 := p.parse_gt_eq()
							gt_eq983 := _t1798
							_t1797 = gt_eq983
						} else {
							var _t1799 *pb.Primitive
							if prediction978 == 3 {
								_t1800 := p.parse_gt()
								gt982 := _t1800
								_t1799 = gt982
							} else {
								var _t1801 *pb.Primitive
								if prediction978 == 2 {
									_t1802 := p.parse_lt_eq()
									lt_eq981 := _t1802
									_t1801 = lt_eq981
								} else {
									var _t1803 *pb.Primitive
									if prediction978 == 1 {
										_t1804 := p.parse_lt()
										lt980 := _t1804
										_t1803 = lt980
									} else {
										var _t1805 *pb.Primitive
										if prediction978 == 0 {
											_t1806 := p.parse_eq()
											eq979 := _t1806
											_t1805 = eq979
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1793 = _t1795
				}
				_t1791 = _t1793
			}
			_t1789 = _t1791
		}
		_t1785 = _t1789
	}
	result994 := _t1785
	p.recordSpan(int(span_start993), "Primitive")
	return result994
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start997 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1807 := p.parse_term()
	term995 := _t1807
	_t1808 := p.parse_term()
	term_3996 := _t1808
	p.consumeLiteral(")")
	_t1809 := &pb.RelTerm{}
	_t1809.RelTermType = &pb.RelTerm_Term{Term: term995}
	_t1810 := &pb.RelTerm{}
	_t1810.RelTermType = &pb.RelTerm_Term{Term: term_3996}
	_t1811 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1809, _t1810}}
	result998 := _t1811
	p.recordSpan(int(span_start997), "Primitive")
	return result998
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start1001 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1812 := p.parse_term()
	term999 := _t1812
	_t1813 := p.parse_term()
	term_31000 := _t1813
	p.consumeLiteral(")")
	_t1814 := &pb.RelTerm{}
	_t1814.RelTermType = &pb.RelTerm_Term{Term: term999}
	_t1815 := &pb.RelTerm{}
	_t1815.RelTermType = &pb.RelTerm_Term{Term: term_31000}
	_t1816 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1814, _t1815}}
	result1002 := _t1816
	p.recordSpan(int(span_start1001), "Primitive")
	return result1002
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1817 := p.parse_term()
	term1003 := _t1817
	_t1818 := p.parse_term()
	term_31004 := _t1818
	p.consumeLiteral(")")
	_t1819 := &pb.RelTerm{}
	_t1819.RelTermType = &pb.RelTerm_Term{Term: term1003}
	_t1820 := &pb.RelTerm{}
	_t1820.RelTermType = &pb.RelTerm_Term{Term: term_31004}
	_t1821 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1819, _t1820}}
	result1006 := _t1821
	p.recordSpan(int(span_start1005), "Primitive")
	return result1006
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1822 := p.parse_term()
	term1007 := _t1822
	_t1823 := p.parse_term()
	term_31008 := _t1823
	p.consumeLiteral(")")
	_t1824 := &pb.RelTerm{}
	_t1824.RelTermType = &pb.RelTerm_Term{Term: term1007}
	_t1825 := &pb.RelTerm{}
	_t1825.RelTermType = &pb.RelTerm_Term{Term: term_31008}
	_t1826 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1824, _t1825}}
	result1010 := _t1826
	p.recordSpan(int(span_start1009), "Primitive")
	return result1010
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1827 := p.parse_term()
	term1011 := _t1827
	_t1828 := p.parse_term()
	term_31012 := _t1828
	p.consumeLiteral(")")
	_t1829 := &pb.RelTerm{}
	_t1829.RelTermType = &pb.RelTerm_Term{Term: term1011}
	_t1830 := &pb.RelTerm{}
	_t1830.RelTermType = &pb.RelTerm_Term{Term: term_31012}
	_t1831 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1829, _t1830}}
	result1014 := _t1831
	p.recordSpan(int(span_start1013), "Primitive")
	return result1014
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1832 := p.parse_term()
	term1015 := _t1832
	_t1833 := p.parse_term()
	term_31016 := _t1833
	_t1834 := p.parse_term()
	term_41017 := _t1834
	p.consumeLiteral(")")
	_t1835 := &pb.RelTerm{}
	_t1835.RelTermType = &pb.RelTerm_Term{Term: term1015}
	_t1836 := &pb.RelTerm{}
	_t1836.RelTermType = &pb.RelTerm_Term{Term: term_31016}
	_t1837 := &pb.RelTerm{}
	_t1837.RelTermType = &pb.RelTerm_Term{Term: term_41017}
	_t1838 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1835, _t1836, _t1837}}
	result1019 := _t1838
	p.recordSpan(int(span_start1018), "Primitive")
	return result1019
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start1023 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1839 := p.parse_term()
	term1020 := _t1839
	_t1840 := p.parse_term()
	term_31021 := _t1840
	_t1841 := p.parse_term()
	term_41022 := _t1841
	p.consumeLiteral(")")
	_t1842 := &pb.RelTerm{}
	_t1842.RelTermType = &pb.RelTerm_Term{Term: term1020}
	_t1843 := &pb.RelTerm{}
	_t1843.RelTermType = &pb.RelTerm_Term{Term: term_31021}
	_t1844 := &pb.RelTerm{}
	_t1844.RelTermType = &pb.RelTerm_Term{Term: term_41022}
	_t1845 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1842, _t1843, _t1844}}
	result1024 := _t1845
	p.recordSpan(int(span_start1023), "Primitive")
	return result1024
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1846 := p.parse_term()
	term1025 := _t1846
	_t1847 := p.parse_term()
	term_31026 := _t1847
	_t1848 := p.parse_term()
	term_41027 := _t1848
	p.consumeLiteral(")")
	_t1849 := &pb.RelTerm{}
	_t1849.RelTermType = &pb.RelTerm_Term{Term: term1025}
	_t1850 := &pb.RelTerm{}
	_t1850.RelTermType = &pb.RelTerm_Term{Term: term_31026}
	_t1851 := &pb.RelTerm{}
	_t1851.RelTermType = &pb.RelTerm_Term{Term: term_41027}
	_t1852 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1849, _t1850, _t1851}}
	result1029 := _t1852
	p.recordSpan(int(span_start1028), "Primitive")
	return result1029
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1033 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1853 := p.parse_term()
	term1030 := _t1853
	_t1854 := p.parse_term()
	term_31031 := _t1854
	_t1855 := p.parse_term()
	term_41032 := _t1855
	p.consumeLiteral(")")
	_t1856 := &pb.RelTerm{}
	_t1856.RelTermType = &pb.RelTerm_Term{Term: term1030}
	_t1857 := &pb.RelTerm{}
	_t1857.RelTermType = &pb.RelTerm_Term{Term: term_31031}
	_t1858 := &pb.RelTerm{}
	_t1858.RelTermType = &pb.RelTerm_Term{Term: term_41032}
	_t1859 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1856, _t1857, _t1858}}
	result1034 := _t1859
	p.recordSpan(int(span_start1033), "Primitive")
	return result1034
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1038 := int64(p.spanStart())
	var _t1860 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1860 = 1
	} else {
		var _t1861 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1861 = 1
		} else {
			var _t1862 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1862 = 1
			} else {
				var _t1863 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1863 = 1
				} else {
					var _t1864 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1864 = 0
					} else {
						var _t1865 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1865 = 1
						} else {
							var _t1866 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1866 = 1
							} else {
								var _t1867 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1867 = 1
								} else {
									var _t1868 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1868 = 1
									} else {
										var _t1869 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1869 = 1
										} else {
											var _t1870 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1870 = 1
											} else {
												var _t1871 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1871 = 1
												} else {
													var _t1872 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1872 = 1
													} else {
														var _t1873 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1873 = 1
														} else {
															var _t1874 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1874 = 1
															} else {
																_t1874 = -1
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
							_t1865 = _t1866
						}
						_t1864 = _t1865
					}
					_t1863 = _t1864
				}
				_t1862 = _t1863
			}
			_t1861 = _t1862
		}
		_t1860 = _t1861
	}
	prediction1035 := _t1860
	var _t1875 *pb.RelTerm
	if prediction1035 == 1 {
		_t1876 := p.parse_term()
		term1037 := _t1876
		_t1877 := &pb.RelTerm{}
		_t1877.RelTermType = &pb.RelTerm_Term{Term: term1037}
		_t1875 = _t1877
	} else {
		var _t1878 *pb.RelTerm
		if prediction1035 == 0 {
			_t1879 := p.parse_specialized_value()
			specialized_value1036 := _t1879
			_t1880 := &pb.RelTerm{}
			_t1880.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1036}
			_t1878 = _t1880
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1875 = _t1878
	}
	result1039 := _t1875
	p.recordSpan(int(span_start1038), "RelTerm")
	return result1039
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1041 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1881 := p.parse_raw_value()
	raw_value1040 := _t1881
	result1042 := raw_value1040
	p.recordSpan(int(span_start1041), "Value")
	return result1042
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1048 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1882 := p.parse_name()
	name1043 := _t1882
	xs1044 := []*pb.RelTerm{}
	cond1045 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1045 {
		_t1883 := p.parse_rel_term()
		item1046 := _t1883
		xs1044 = append(xs1044, item1046)
		cond1045 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1047 := xs1044
	p.consumeLiteral(")")
	_t1884 := &pb.RelAtom{Name: name1043, Terms: rel_terms1047}
	result1049 := _t1884
	p.recordSpan(int(span_start1048), "RelAtom")
	return result1049
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1885 := p.parse_term()
	term1050 := _t1885
	_t1886 := p.parse_term()
	term_31051 := _t1886
	p.consumeLiteral(")")
	_t1887 := &pb.Cast{Input: term1050, Result: term_31051}
	result1053 := _t1887
	p.recordSpan(int(span_start1052), "Cast")
	return result1053
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1054 := []*pb.Attribute{}
	cond1055 := p.matchLookaheadLiteral("(", 0)
	for cond1055 {
		_t1888 := p.parse_attribute()
		item1056 := _t1888
		xs1054 = append(xs1054, item1056)
		cond1055 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1057 := xs1054
	p.consumeLiteral(")")
	return attributes1057
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1063 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1889 := p.parse_name()
	name1058 := _t1889
	xs1059 := []*pb.Value{}
	cond1060 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1060 {
		_t1890 := p.parse_raw_value()
		item1061 := _t1890
		xs1059 = append(xs1059, item1061)
		cond1060 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1062 := xs1059
	p.consumeLiteral(")")
	_t1891 := &pb.Attribute{Name: name1058, Args: raw_values1062}
	result1064 := _t1891
	p.recordSpan(int(span_start1063), "Attribute")
	return result1064
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1071 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1065 := []*pb.RelationId{}
	cond1066 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1066 {
		_t1892 := p.parse_relation_id()
		item1067 := _t1892
		xs1065 = append(xs1065, item1067)
		cond1066 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1068 := xs1065
	_t1893 := p.parse_script()
	script1069 := _t1893
	var _t1894 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1895 := p.parse_attrs()
		_t1894 = _t1895
	}
	attrs1070 := _t1894
	p.consumeLiteral(")")
	_t1896 := attrs1070
	if attrs1070 == nil {
		_t1896 = []*pb.Attribute{}
	}
	_t1897 := &pb.Algorithm{Global: relation_ids1068, Body: script1069, Attrs: _t1896}
	result1072 := _t1897
	p.recordSpan(int(span_start1071), "Algorithm")
	return result1072
}

func (p *Parser) parse_script() *pb.Script {
	span_start1077 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1073 := []*pb.Construct{}
	cond1074 := p.matchLookaheadLiteral("(", 0)
	for cond1074 {
		_t1898 := p.parse_construct()
		item1075 := _t1898
		xs1073 = append(xs1073, item1075)
		cond1074 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1076 := xs1073
	p.consumeLiteral(")")
	_t1899 := &pb.Script{Constructs: constructs1076}
	result1078 := _t1899
	p.recordSpan(int(span_start1077), "Script")
	return result1078
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1082 := int64(p.spanStart())
	var _t1900 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1901 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1901 = 1
		} else {
			var _t1902 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1902 = 1
			} else {
				var _t1903 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1903 = 1
				} else {
					var _t1904 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1904 = 0
					} else {
						var _t1905 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1905 = 1
						} else {
							var _t1906 int64
							if p.matchLookaheadLiteral("assign", 1) {
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
	} else {
		_t1900 = -1
	}
	prediction1079 := _t1900
	var _t1907 *pb.Construct
	if prediction1079 == 1 {
		_t1908 := p.parse_instruction()
		instruction1081 := _t1908
		_t1909 := &pb.Construct{}
		_t1909.ConstructType = &pb.Construct_Instruction{Instruction: instruction1081}
		_t1907 = _t1909
	} else {
		var _t1910 *pb.Construct
		if prediction1079 == 0 {
			_t1911 := p.parse_loop()
			loop1080 := _t1911
			_t1912 := &pb.Construct{}
			_t1912.ConstructType = &pb.Construct_Loop{Loop: loop1080}
			_t1910 = _t1912
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1907 = _t1910
	}
	result1083 := _t1907
	p.recordSpan(int(span_start1082), "Construct")
	return result1083
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1913 := p.parse_init()
	init1084 := _t1913
	_t1914 := p.parse_script()
	script1085 := _t1914
	var _t1915 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1916 := p.parse_attrs()
		_t1915 = _t1916
	}
	attrs1086 := _t1915
	p.consumeLiteral(")")
	_t1917 := attrs1086
	if attrs1086 == nil {
		_t1917 = []*pb.Attribute{}
	}
	_t1918 := &pb.Loop{Init: init1084, Body: script1085, Attrs: _t1917}
	result1088 := _t1918
	p.recordSpan(int(span_start1087), "Loop")
	return result1088
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1089 := []*pb.Instruction{}
	cond1090 := p.matchLookaheadLiteral("(", 0)
	for cond1090 {
		_t1919 := p.parse_instruction()
		item1091 := _t1919
		xs1089 = append(xs1089, item1091)
		cond1090 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1092 := xs1089
	p.consumeLiteral(")")
	return instructions1092
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1099 := int64(p.spanStart())
	var _t1920 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1921 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1921 = 1
		} else {
			var _t1922 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1922 = 4
			} else {
				var _t1923 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1923 = 3
				} else {
					var _t1924 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1924 = 2
					} else {
						var _t1925 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1925 = 0
						} else {
							_t1925 = -1
						}
						_t1924 = _t1925
					}
					_t1923 = _t1924
				}
				_t1922 = _t1923
			}
			_t1921 = _t1922
		}
		_t1920 = _t1921
	} else {
		_t1920 = -1
	}
	prediction1093 := _t1920
	var _t1926 *pb.Instruction
	if prediction1093 == 4 {
		_t1927 := p.parse_monus_def()
		monus_def1098 := _t1927
		_t1928 := &pb.Instruction{}
		_t1928.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1098}
		_t1926 = _t1928
	} else {
		var _t1929 *pb.Instruction
		if prediction1093 == 3 {
			_t1930 := p.parse_monoid_def()
			monoid_def1097 := _t1930
			_t1931 := &pb.Instruction{}
			_t1931.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1097}
			_t1929 = _t1931
		} else {
			var _t1932 *pb.Instruction
			if prediction1093 == 2 {
				_t1933 := p.parse_break()
				break1096 := _t1933
				_t1934 := &pb.Instruction{}
				_t1934.InstrType = &pb.Instruction_Break{Break: break1096}
				_t1932 = _t1934
			} else {
				var _t1935 *pb.Instruction
				if prediction1093 == 1 {
					_t1936 := p.parse_upsert()
					upsert1095 := _t1936
					_t1937 := &pb.Instruction{}
					_t1937.InstrType = &pb.Instruction_Upsert{Upsert: upsert1095}
					_t1935 = _t1937
				} else {
					var _t1938 *pb.Instruction
					if prediction1093 == 0 {
						_t1939 := p.parse_assign()
						assign1094 := _t1939
						_t1940 := &pb.Instruction{}
						_t1940.InstrType = &pb.Instruction_Assign{Assign: assign1094}
						_t1938 = _t1940
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1935 = _t1938
				}
				_t1932 = _t1935
			}
			_t1929 = _t1932
		}
		_t1926 = _t1929
	}
	result1100 := _t1926
	p.recordSpan(int(span_start1099), "Instruction")
	return result1100
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1941 := p.parse_relation_id()
	relation_id1101 := _t1941
	_t1942 := p.parse_abstraction()
	abstraction1102 := _t1942
	var _t1943 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1944 := p.parse_attrs()
		_t1943 = _t1944
	}
	attrs1103 := _t1943
	p.consumeLiteral(")")
	_t1945 := attrs1103
	if attrs1103 == nil {
		_t1945 = []*pb.Attribute{}
	}
	_t1946 := &pb.Assign{Name: relation_id1101, Body: abstraction1102, Attrs: _t1945}
	result1105 := _t1946
	p.recordSpan(int(span_start1104), "Assign")
	return result1105
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1947 := p.parse_relation_id()
	relation_id1106 := _t1947
	_t1948 := p.parse_abstraction_with_arity()
	abstraction_with_arity1107 := _t1948
	var _t1949 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1950 := p.parse_attrs()
		_t1949 = _t1950
	}
	attrs1108 := _t1949
	p.consumeLiteral(")")
	_t1951 := attrs1108
	if attrs1108 == nil {
		_t1951 = []*pb.Attribute{}
	}
	_t1952 := &pb.Upsert{Name: relation_id1106, Body: abstraction_with_arity1107[0].(*pb.Abstraction), Attrs: _t1951, ValueArity: abstraction_with_arity1107[1].(int64)}
	result1110 := _t1952
	p.recordSpan(int(span_start1109), "Upsert")
	return result1110
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1953 := p.parse_bindings()
	bindings1111 := _t1953
	_t1954 := p.parse_formula()
	formula1112 := _t1954
	p.consumeLiteral(")")
	_t1955 := &pb.Abstraction{Vars: listConcat(bindings1111[0].([]*pb.Binding), bindings1111[1].([]*pb.Binding)), Value: formula1112}
	return []interface{}{_t1955, int64(len(bindings1111[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1116 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1956 := p.parse_relation_id()
	relation_id1113 := _t1956
	_t1957 := p.parse_abstraction()
	abstraction1114 := _t1957
	var _t1958 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1959 := p.parse_attrs()
		_t1958 = _t1959
	}
	attrs1115 := _t1958
	p.consumeLiteral(")")
	_t1960 := attrs1115
	if attrs1115 == nil {
		_t1960 = []*pb.Attribute{}
	}
	_t1961 := &pb.Break{Name: relation_id1113, Body: abstraction1114, Attrs: _t1960}
	result1117 := _t1961
	p.recordSpan(int(span_start1116), "Break")
	return result1117
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1122 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1962 := p.parse_monoid()
	monoid1118 := _t1962
	_t1963 := p.parse_relation_id()
	relation_id1119 := _t1963
	_t1964 := p.parse_abstraction_with_arity()
	abstraction_with_arity1120 := _t1964
	var _t1965 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1966 := p.parse_attrs()
		_t1965 = _t1966
	}
	attrs1121 := _t1965
	p.consumeLiteral(")")
	_t1967 := attrs1121
	if attrs1121 == nil {
		_t1967 = []*pb.Attribute{}
	}
	_t1968 := &pb.MonoidDef{Monoid: monoid1118, Name: relation_id1119, Body: abstraction_with_arity1120[0].(*pb.Abstraction), Attrs: _t1967, ValueArity: abstraction_with_arity1120[1].(int64)}
	result1123 := _t1968
	p.recordSpan(int(span_start1122), "MonoidDef")
	return result1123
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1129 := int64(p.spanStart())
	var _t1969 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1970 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1970 = 3
		} else {
			var _t1971 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1971 = 0
			} else {
				var _t1972 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1972 = 1
				} else {
					var _t1973 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1973 = 2
					} else {
						_t1973 = -1
					}
					_t1972 = _t1973
				}
				_t1971 = _t1972
			}
			_t1970 = _t1971
		}
		_t1969 = _t1970
	} else {
		_t1969 = -1
	}
	prediction1124 := _t1969
	var _t1974 *pb.Monoid
	if prediction1124 == 3 {
		_t1975 := p.parse_sum_monoid()
		sum_monoid1128 := _t1975
		_t1976 := &pb.Monoid{}
		_t1976.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1128}
		_t1974 = _t1976
	} else {
		var _t1977 *pb.Monoid
		if prediction1124 == 2 {
			_t1978 := p.parse_max_monoid()
			max_monoid1127 := _t1978
			_t1979 := &pb.Monoid{}
			_t1979.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1127}
			_t1977 = _t1979
		} else {
			var _t1980 *pb.Monoid
			if prediction1124 == 1 {
				_t1981 := p.parse_min_monoid()
				min_monoid1126 := _t1981
				_t1982 := &pb.Monoid{}
				_t1982.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1126}
				_t1980 = _t1982
			} else {
				var _t1983 *pb.Monoid
				if prediction1124 == 0 {
					_t1984 := p.parse_or_monoid()
					or_monoid1125 := _t1984
					_t1985 := &pb.Monoid{}
					_t1985.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1125}
					_t1983 = _t1985
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1980 = _t1983
			}
			_t1977 = _t1980
		}
		_t1974 = _t1977
	}
	result1130 := _t1974
	p.recordSpan(int(span_start1129), "Monoid")
	return result1130
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1131 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1986 := &pb.OrMonoid{}
	result1132 := _t1986
	p.recordSpan(int(span_start1131), "OrMonoid")
	return result1132
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1987 := p.parse_type()
	type1133 := _t1987
	p.consumeLiteral(")")
	_t1988 := &pb.MinMonoid{Type: type1133}
	result1135 := _t1988
	p.recordSpan(int(span_start1134), "MinMonoid")
	return result1135
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1137 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1989 := p.parse_type()
	type1136 := _t1989
	p.consumeLiteral(")")
	_t1990 := &pb.MaxMonoid{Type: type1136}
	result1138 := _t1990
	p.recordSpan(int(span_start1137), "MaxMonoid")
	return result1138
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1140 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1991 := p.parse_type()
	type1139 := _t1991
	p.consumeLiteral(")")
	_t1992 := &pb.SumMonoid{Type: type1139}
	result1141 := _t1992
	p.recordSpan(int(span_start1140), "SumMonoid")
	return result1141
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1146 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1993 := p.parse_monoid()
	monoid1142 := _t1993
	_t1994 := p.parse_relation_id()
	relation_id1143 := _t1994
	_t1995 := p.parse_abstraction_with_arity()
	abstraction_with_arity1144 := _t1995
	var _t1996 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1997 := p.parse_attrs()
		_t1996 = _t1997
	}
	attrs1145 := _t1996
	p.consumeLiteral(")")
	_t1998 := attrs1145
	if attrs1145 == nil {
		_t1998 = []*pb.Attribute{}
	}
	_t1999 := &pb.MonusDef{Monoid: monoid1142, Name: relation_id1143, Body: abstraction_with_arity1144[0].(*pb.Abstraction), Attrs: _t1998, ValueArity: abstraction_with_arity1144[1].(int64)}
	result1147 := _t1999
	p.recordSpan(int(span_start1146), "MonusDef")
	return result1147
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1152 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t2000 := p.parse_relation_id()
	relation_id1148 := _t2000
	_t2001 := p.parse_abstraction()
	abstraction1149 := _t2001
	_t2002 := p.parse_functional_dependency_keys()
	functional_dependency_keys1150 := _t2002
	_t2003 := p.parse_functional_dependency_values()
	functional_dependency_values1151 := _t2003
	p.consumeLiteral(")")
	_t2004 := &pb.FunctionalDependency{Guard: abstraction1149, Keys: functional_dependency_keys1150, Values: functional_dependency_values1151}
	_t2005 := &pb.Constraint{Name: relation_id1148}
	_t2005.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t2004}
	result1153 := _t2005
	p.recordSpan(int(span_start1152), "Constraint")
	return result1153
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1154 := []*pb.Var{}
	cond1155 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1155 {
		_t2006 := p.parse_var()
		item1156 := _t2006
		xs1154 = append(xs1154, item1156)
		cond1155 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1157 := xs1154
	p.consumeLiteral(")")
	return vars1157
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1158 := []*pb.Var{}
	cond1159 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1159 {
		_t2007 := p.parse_var()
		item1160 := _t2007
		xs1158 = append(xs1158, item1160)
		cond1159 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1161 := xs1158
	p.consumeLiteral(")")
	return vars1161
}

func (p *Parser) parse_data() *pb.Data {
	span_start1167 := int64(p.spanStart())
	var _t2008 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2009 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t2009 = 3
		} else {
			var _t2010 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t2010 = 0
			} else {
				var _t2011 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t2011 = 2
				} else {
					var _t2012 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t2012 = 1
					} else {
						_t2012 = -1
					}
					_t2011 = _t2012
				}
				_t2010 = _t2011
			}
			_t2009 = _t2010
		}
		_t2008 = _t2009
	} else {
		_t2008 = -1
	}
	prediction1162 := _t2008
	var _t2013 *pb.Data
	if prediction1162 == 3 {
		_t2014 := p.parse_iceberg_data()
		iceberg_data1166 := _t2014
		_t2015 := &pb.Data{}
		_t2015.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1166}
		_t2013 = _t2015
	} else {
		var _t2016 *pb.Data
		if prediction1162 == 2 {
			_t2017 := p.parse_csv_data()
			csv_data1165 := _t2017
			_t2018 := &pb.Data{}
			_t2018.DataType = &pb.Data_CsvData{CsvData: csv_data1165}
			_t2016 = _t2018
		} else {
			var _t2019 *pb.Data
			if prediction1162 == 1 {
				_t2020 := p.parse_betree_relation()
				betree_relation1164 := _t2020
				_t2021 := &pb.Data{}
				_t2021.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1164}
				_t2019 = _t2021
			} else {
				var _t2022 *pb.Data
				if prediction1162 == 0 {
					_t2023 := p.parse_edb()
					edb1163 := _t2023
					_t2024 := &pb.Data{}
					_t2024.DataType = &pb.Data_Edb{Edb: edb1163}
					_t2022 = _t2024
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t2019 = _t2022
			}
			_t2016 = _t2019
		}
		_t2013 = _t2016
	}
	result1168 := _t2013
	p.recordSpan(int(span_start1167), "Data")
	return result1168
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1172 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t2025 := p.parse_relation_id()
	relation_id1169 := _t2025
	_t2026 := p.parse_edb_path()
	edb_path1170 := _t2026
	_t2027 := p.parse_edb_types()
	edb_types1171 := _t2027
	p.consumeLiteral(")")
	_t2028 := &pb.EDB{TargetId: relation_id1169, Path: edb_path1170, Types: edb_types1171}
	result1173 := _t2028
	p.recordSpan(int(span_start1172), "EDB")
	return result1173
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1174 := []string{}
	cond1175 := p.matchLookaheadTerminal("STRING", 0)
	for cond1175 {
		item1176 := p.consumeTerminal("STRING").Value.str
		xs1174 = append(xs1174, item1176)
		cond1175 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1177 := xs1174
	p.consumeLiteral("]")
	return strings1177
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1178 := []*pb.Type{}
	cond1179 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1179 {
		_t2029 := p.parse_type()
		item1180 := _t2029
		xs1178 = append(xs1178, item1180)
		cond1179 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1181 := xs1178
	p.consumeLiteral("]")
	return types1181
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1184 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t2030 := p.parse_relation_id()
	relation_id1182 := _t2030
	_t2031 := p.parse_betree_info()
	betree_info1183 := _t2031
	p.consumeLiteral(")")
	_t2032 := &pb.BeTreeRelation{Name: relation_id1182, RelationInfo: betree_info1183}
	result1185 := _t2032
	p.recordSpan(int(span_start1184), "BeTreeRelation")
	return result1185
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t2033 := p.parse_betree_info_key_types()
	betree_info_key_types1186 := _t2033
	_t2034 := p.parse_betree_info_value_types()
	betree_info_value_types1187 := _t2034
	_t2035 := p.parse_config_dict()
	config_dict1188 := _t2035
	p.consumeLiteral(")")
	_t2036 := p.construct_betree_info(betree_info_key_types1186, betree_info_value_types1187, config_dict1188)
	result1190 := _t2036
	p.recordSpan(int(span_start1189), "BeTreeInfo")
	return result1190
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1191 := []*pb.Type{}
	cond1192 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1192 {
		_t2037 := p.parse_type()
		item1193 := _t2037
		xs1191 = append(xs1191, item1193)
		cond1192 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1194 := xs1191
	p.consumeLiteral(")")
	return types1194
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1195 := []*pb.Type{}
	cond1196 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1196 {
		_t2038 := p.parse_type()
		item1197 := _t2038
		xs1195 = append(xs1195, item1197)
		cond1196 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1198 := xs1195
	p.consumeLiteral(")")
	return types1198
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1204 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t2039 := p.parse_csvlocator()
	csvlocator1199 := _t2039
	_t2040 := p.parse_csv_config()
	csv_config1200 := _t2040
	var _t2041 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2042 := p.parse_gnf_columns()
		_t2041 = _t2042
	}
	gnf_columns1201 := _t2041
	var _t2043 *pb.Relations
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("relations", 1)) {
		_t2044 := p.parse_relations()
		_t2043 = _t2044
	}
	relations1202 := _t2043
	_t2045 := p.parse_csv_asof()
	csv_asof1203 := _t2045
	p.consumeLiteral(")")
	_t2046 := p.construct_csv_data(csvlocator1199, csv_config1200, gnf_columns1201, relations1202, csv_asof1203)
	result1205 := _t2046
	p.recordSpan(int(span_start1204), "CSVData")
	return result1205
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1208 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t2047 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t2048 := p.parse_csv_locator_paths()
		_t2047 = _t2048
	}
	csv_locator_paths1206 := _t2047
	var _t2049 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2050 := p.parse_csv_locator_inline_data()
		_t2049 = ptr(_t2050)
	}
	csv_locator_inline_data1207 := _t2049
	p.consumeLiteral(")")
	_t2051 := csv_locator_paths1206
	if csv_locator_paths1206 == nil {
		_t2051 = []string{}
	}
	_t2052 := &pb.CSVLocator{Paths: _t2051, InlineData: []byte(deref(csv_locator_inline_data1207, ""))}
	result1209 := _t2052
	p.recordSpan(int(span_start1208), "CSVLocator")
	return result1209
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1210 := []string{}
	cond1211 := p.matchLookaheadTerminal("STRING", 0)
	for cond1211 {
		item1212 := p.consumeTerminal("STRING").Value.str
		xs1210 = append(xs1210, item1212)
		cond1211 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1213 := xs1210
	p.consumeLiteral(")")
	return strings1213
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1214 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1214
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1217 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t2053 := p.parse_config_dict()
	config_dict1215 := _t2053
	var _t2054 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t2055 := p.parse__storage_integration()
		_t2054 = _t2055
	}
	_storage_integration1216 := _t2054
	p.consumeLiteral(")")
	_t2056 := p.construct_csv_config(config_dict1215, _storage_integration1216)
	result1218 := _t2056
	p.recordSpan(int(span_start1217), "CSVConfig")
	return result1218
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t2057 := p.parse_config_dict()
	config_dict1219 := _t2057
	p.consumeLiteral(")")
	return config_dict1219
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1220 := []*pb.GNFColumn{}
	cond1221 := p.matchLookaheadLiteral("(", 0)
	for cond1221 {
		_t2058 := p.parse_gnf_column()
		item1222 := _t2058
		xs1220 = append(xs1220, item1222)
		cond1221 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1223 := xs1220
	p.consumeLiteral(")")
	return gnf_columns1223
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1230 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2059 := p.parse_gnf_column_path()
	gnf_column_path1224 := _t2059
	var _t2060 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2061 := p.parse_relation_id()
		_t2060 = _t2061
	}
	relation_id1225 := _t2060
	p.consumeLiteral("[")
	xs1226 := []*pb.Type{}
	cond1227 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1227 {
		_t2062 := p.parse_type()
		item1228 := _t2062
		xs1226 = append(xs1226, item1228)
		cond1227 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1229 := xs1226
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2063 := &pb.GNFColumn{ColumnPath: gnf_column_path1224, TargetId: relation_id1225, Types: types1229}
	result1231 := _t2063
	p.recordSpan(int(span_start1230), "GNFColumn")
	return result1231
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2064 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2064 = 1
	} else {
		var _t2065 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2065 = 0
		} else {
			_t2065 = -1
		}
		_t2064 = _t2065
	}
	prediction1232 := _t2064
	var _t2066 []string
	if prediction1232 == 1 {
		p.consumeLiteral("[")
		xs1234 := []string{}
		cond1235 := p.matchLookaheadTerminal("STRING", 0)
		for cond1235 {
			item1236 := p.consumeTerminal("STRING").Value.str
			xs1234 = append(xs1234, item1236)
			cond1235 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1237 := xs1234
		p.consumeLiteral("]")
		_t2066 = strings1237
	} else {
		var _t2067 []string
		if prediction1232 == 0 {
			string1233 := p.consumeTerminal("STRING").Value.str
			_ = string1233
			_t2067 = []string{string1233}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2066 = _t2067
	}
	return _t2066
}

func (p *Parser) parse_relations() *pb.Relations {
	span_start1240 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relations")
	_t2068 := p.parse_relation_keys()
	relation_keys1238 := _t2068
	_t2069 := p.parse_relation_body()
	relation_body1239 := _t2069
	p.consumeLiteral(")")
	_t2070 := p.construct_relations(relation_keys1238, relation_body1239)
	result1241 := _t2070
	p.recordSpan(int(span_start1240), "Relations")
	return result1241
}

func (p *Parser) parse_relation_keys() []*pb.NamedColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1242 := []*pb.NamedColumn{}
	cond1243 := p.matchLookaheadLiteral("(", 0)
	for cond1243 {
		_t2071 := p.parse_named_column()
		item1244 := _t2071
		xs1242 = append(xs1242, item1244)
		cond1243 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1245 := xs1242
	p.consumeLiteral(")")
	return named_columns1245
}

func (p *Parser) parse_named_column() *pb.NamedColumn {
	span_start1248 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1246 := p.consumeTerminal("STRING").Value.str
	_t2072 := p.parse_type()
	type1247 := _t2072
	p.consumeLiteral(")")
	_t2073 := &pb.NamedColumn{Name: string1246, Type: type1247}
	result1249 := _t2073
	p.recordSpan(int(span_start1248), "NamedColumn")
	return result1249
}

func (p *Parser) parse_relation_body() *pb.Relations {
	span_start1254 := int64(p.spanStart())
	var _t2074 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2075 int64
		if p.matchLookaheadLiteral("relation", 1) {
			_t2075 = 0
		} else {
			var _t2076 int64
			if p.matchLookaheadLiteral("inserts", 1) {
				_t2076 = 1
			} else {
				_t2076 = 0
			}
			_t2075 = _t2076
		}
		_t2074 = _t2075
	} else {
		_t2074 = 0
	}
	prediction1250 := _t2074
	var _t2077 *pb.Relations
	if prediction1250 == 1 {
		_t2078 := p.parse_cdc_inserts()
		cdc_inserts1252 := _t2078
		_t2079 := p.parse_cdc_deletes()
		cdc_deletes1253 := _t2079
		_t2080 := p.construct_cdc_relations(cdc_inserts1252, cdc_deletes1253)
		_t2077 = _t2080
	} else {
		var _t2081 *pb.Relations
		if prediction1250 == 0 {
			_t2082 := p.parse_non_cdc_relations()
			non_cdc_relations1251 := _t2082
			_t2083 := p.construct_non_cdc_relations(non_cdc_relations1251)
			_t2081 = _t2083
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_body", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2077 = _t2081
	}
	result1255 := _t2077
	p.recordSpan(int(span_start1254), "Relations")
	return result1255
}

func (p *Parser) parse_non_cdc_relations() []*pb.OutputRelation {
	xs1256 := []*pb.OutputRelation{}
	cond1257 := p.matchLookaheadLiteral("(", 0)
	for cond1257 {
		_t2084 := p.parse_output_relation()
		item1258 := _t2084
		xs1256 = append(xs1256, item1258)
		cond1257 = p.matchLookaheadLiteral("(", 0)
	}
	return xs1256
}

func (p *Parser) parse_output_relation() *pb.OutputRelation {
	span_start1264 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relation")
	_t2085 := p.parse_relation_id()
	relation_id1259 := _t2085
	xs1260 := []*pb.NamedColumn{}
	cond1261 := p.matchLookaheadLiteral("(", 0)
	for cond1261 {
		_t2086 := p.parse_named_column()
		item1262 := _t2086
		xs1260 = append(xs1260, item1262)
		cond1261 = p.matchLookaheadLiteral("(", 0)
	}
	named_columns1263 := xs1260
	p.consumeLiteral(")")
	_t2087 := &pb.OutputRelation{TargetId: relation_id1259, Values: named_columns1263}
	result1265 := _t2087
	p.recordSpan(int(span_start1264), "OutputRelation")
	return result1265
}

func (p *Parser) parse_cdc_inserts() []*pb.OutputRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("inserts")
	xs1266 := []*pb.OutputRelation{}
	cond1267 := p.matchLookaheadLiteral("(", 0)
	for cond1267 {
		_t2088 := p.parse_output_relation()
		item1268 := _t2088
		xs1266 = append(xs1266, item1268)
		cond1267 = p.matchLookaheadLiteral("(", 0)
	}
	output_relations1269 := xs1266
	p.consumeLiteral(")")
	return output_relations1269
}

func (p *Parser) parse_cdc_deletes() []*pb.OutputRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("deletes")
	xs1270 := []*pb.OutputRelation{}
	cond1271 := p.matchLookaheadLiteral("(", 0)
	for cond1271 {
		_t2089 := p.parse_output_relation()
		item1272 := _t2089
		xs1270 = append(xs1270, item1272)
		cond1271 = p.matchLookaheadLiteral("(", 0)
	}
	output_relations1273 := xs1270
	p.consumeLiteral(")")
	return output_relations1273
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1274 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1274
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1281 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2090 := p.parse_iceberg_locator()
	iceberg_locator1275 := _t2090
	_t2091 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1276 := _t2091
	_t2092 := p.parse_gnf_columns()
	gnf_columns1277 := _t2092
	var _t2093 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2094 := p.parse_iceberg_from_snapshot()
		_t2093 = ptr(_t2094)
	}
	iceberg_from_snapshot1278 := _t2093
	var _t2095 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2096 := p.parse_iceberg_to_snapshot()
		_t2095 = ptr(_t2096)
	}
	iceberg_to_snapshot1279 := _t2095
	_t2097 := p.parse_boolean_value()
	boolean_value1280 := _t2097
	p.consumeLiteral(")")
	_t2098 := p.construct_iceberg_data(iceberg_locator1275, iceberg_catalog_config1276, gnf_columns1277, iceberg_from_snapshot1278, iceberg_to_snapshot1279, boolean_value1280)
	result1282 := _t2098
	p.recordSpan(int(span_start1281), "IcebergData")
	return result1282
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1286 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2099 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1283 := _t2099
	_t2100 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1284 := _t2100
	_t2101 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1285 := _t2101
	p.consumeLiteral(")")
	_t2102 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1283, Namespace: iceberg_locator_namespace1284, Warehouse: iceberg_locator_warehouse1285}
	result1287 := _t2102
	p.recordSpan(int(span_start1286), "IcebergLocator")
	return result1287
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1288 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1288
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1289 := []string{}
	cond1290 := p.matchLookaheadTerminal("STRING", 0)
	for cond1290 {
		item1291 := p.consumeTerminal("STRING").Value.str
		xs1289 = append(xs1289, item1291)
		cond1290 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1292 := xs1289
	p.consumeLiteral(")")
	return strings1292
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1293 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1293
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1298 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2103 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1294 := _t2103
	var _t2104 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2105 := p.parse_iceberg_catalog_config_scope()
		_t2104 = ptr(_t2105)
	}
	iceberg_catalog_config_scope1295 := _t2104
	_t2106 := p.parse_iceberg_properties()
	iceberg_properties1296 := _t2106
	_t2107 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1297 := _t2107
	p.consumeLiteral(")")
	_t2108 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1294, iceberg_catalog_config_scope1295, iceberg_properties1296, iceberg_auth_properties1297)
	result1299 := _t2108
	p.recordSpan(int(span_start1298), "IcebergCatalogConfig")
	return result1299
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1300 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1300
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1301 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1301
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1302 := [][]interface{}{}
	cond1303 := p.matchLookaheadLiteral("(", 0)
	for cond1303 {
		_t2109 := p.parse_iceberg_property_entry()
		item1304 := _t2109
		xs1302 = append(xs1302, item1304)
		cond1303 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1305 := xs1302
	p.consumeLiteral(")")
	return iceberg_property_entrys1305
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1306 := p.consumeTerminal("STRING").Value.str
	string_31307 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1306, string_31307}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1308 := [][]interface{}{}
	cond1309 := p.matchLookaheadLiteral("(", 0)
	for cond1309 {
		_t2110 := p.parse_iceberg_masked_property_entry()
		item1310 := _t2110
		xs1308 = append(xs1308, item1310)
		cond1309 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1311 := xs1308
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1311
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1312 := p.consumeTerminal("STRING").Value.str
	string_31313 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1312, string_31313}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1314 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1314
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1315 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1315
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1317 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2111 := p.parse_fragment_id()
	fragment_id1316 := _t2111
	p.consumeLiteral(")")
	_t2112 := &pb.Undefine{FragmentId: fragment_id1316}
	result1318 := _t2112
	p.recordSpan(int(span_start1317), "Undefine")
	return result1318
}

func (p *Parser) parse_context() *pb.Context {
	span_start1323 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1319 := []*pb.RelationId{}
	cond1320 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1320 {
		_t2113 := p.parse_relation_id()
		item1321 := _t2113
		xs1319 = append(xs1319, item1321)
		cond1320 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1322 := xs1319
	p.consumeLiteral(")")
	_t2114 := &pb.Context{Relations: relation_ids1322}
	result1324 := _t2114
	p.recordSpan(int(span_start1323), "Context")
	return result1324
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1330 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2115 := p.parse_edb_path()
	edb_path1325 := _t2115
	xs1326 := []*pb.SnapshotMapping{}
	cond1327 := p.matchLookaheadLiteral("[", 0)
	for cond1327 {
		_t2116 := p.parse_snapshot_mapping()
		item1328 := _t2116
		xs1326 = append(xs1326, item1328)
		cond1327 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1329 := xs1326
	p.consumeLiteral(")")
	_t2117 := &pb.Snapshot{Prefix: edb_path1325, Mappings: snapshot_mappings1329}
	result1331 := _t2117
	p.recordSpan(int(span_start1330), "Snapshot")
	return result1331
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1334 := int64(p.spanStart())
	_t2118 := p.parse_edb_path()
	edb_path1332 := _t2118
	_t2119 := p.parse_relation_id()
	relation_id1333 := _t2119
	_t2120 := &pb.SnapshotMapping{DestinationPath: edb_path1332, SourceRelation: relation_id1333}
	result1335 := _t2120
	p.recordSpan(int(span_start1334), "SnapshotMapping")
	return result1335
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1336 := []*pb.Read{}
	cond1337 := p.matchLookaheadLiteral("(", 0)
	for cond1337 {
		_t2121 := p.parse_read()
		item1338 := _t2121
		xs1336 = append(xs1336, item1338)
		cond1337 = p.matchLookaheadLiteral("(", 0)
	}
	reads1339 := xs1336
	p.consumeLiteral(")")
	return reads1339
}

func (p *Parser) parse_read() *pb.Read {
	span_start1346 := int64(p.spanStart())
	var _t2122 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2123 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2123 = 2
		} else {
			var _t2124 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2124 = 1
			} else {
				var _t2125 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2125 = 4
				} else {
					var _t2126 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2126 = 4
					} else {
						var _t2127 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2127 = 0
						} else {
							var _t2128 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2128 = 3
							} else {
								_t2128 = -1
							}
							_t2127 = _t2128
						}
						_t2126 = _t2127
					}
					_t2125 = _t2126
				}
				_t2124 = _t2125
			}
			_t2123 = _t2124
		}
		_t2122 = _t2123
	} else {
		_t2122 = -1
	}
	prediction1340 := _t2122
	var _t2129 *pb.Read
	if prediction1340 == 4 {
		_t2130 := p.parse_export()
		export1345 := _t2130
		_t2131 := &pb.Read{}
		_t2131.ReadType = &pb.Read_Export{Export: export1345}
		_t2129 = _t2131
	} else {
		var _t2132 *pb.Read
		if prediction1340 == 3 {
			_t2133 := p.parse_abort()
			abort1344 := _t2133
			_t2134 := &pb.Read{}
			_t2134.ReadType = &pb.Read_Abort{Abort: abort1344}
			_t2132 = _t2134
		} else {
			var _t2135 *pb.Read
			if prediction1340 == 2 {
				_t2136 := p.parse_what_if()
				what_if1343 := _t2136
				_t2137 := &pb.Read{}
				_t2137.ReadType = &pb.Read_WhatIf{WhatIf: what_if1343}
				_t2135 = _t2137
			} else {
				var _t2138 *pb.Read
				if prediction1340 == 1 {
					_t2139 := p.parse_output()
					output1342 := _t2139
					_t2140 := &pb.Read{}
					_t2140.ReadType = &pb.Read_Output{Output: output1342}
					_t2138 = _t2140
				} else {
					var _t2141 *pb.Read
					if prediction1340 == 0 {
						_t2142 := p.parse_demand()
						demand1341 := _t2142
						_t2143 := &pb.Read{}
						_t2143.ReadType = &pb.Read_Demand{Demand: demand1341}
						_t2141 = _t2143
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2138 = _t2141
				}
				_t2135 = _t2138
			}
			_t2132 = _t2135
		}
		_t2129 = _t2132
	}
	result1347 := _t2129
	p.recordSpan(int(span_start1346), "Read")
	return result1347
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1349 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2144 := p.parse_relation_id()
	relation_id1348 := _t2144
	p.consumeLiteral(")")
	_t2145 := &pb.Demand{RelationId: relation_id1348}
	result1350 := _t2145
	p.recordSpan(int(span_start1349), "Demand")
	return result1350
}

func (p *Parser) parse_output() *pb.Output {
	span_start1353 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2146 := p.parse_name()
	name1351 := _t2146
	_t2147 := p.parse_relation_id()
	relation_id1352 := _t2147
	p.consumeLiteral(")")
	_t2148 := &pb.Output{Name: name1351, RelationId: relation_id1352}
	result1354 := _t2148
	p.recordSpan(int(span_start1353), "Output")
	return result1354
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1357 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2149 := p.parse_name()
	name1355 := _t2149
	_t2150 := p.parse_epoch()
	epoch1356 := _t2150
	p.consumeLiteral(")")
	_t2151 := &pb.WhatIf{Branch: name1355, Epoch: epoch1356}
	result1358 := _t2151
	p.recordSpan(int(span_start1357), "WhatIf")
	return result1358
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1361 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2152 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2153 := p.parse_name()
		_t2152 = ptr(_t2153)
	}
	name1359 := _t2152
	_t2154 := p.parse_relation_id()
	relation_id1360 := _t2154
	p.consumeLiteral(")")
	_t2155 := &pb.Abort{Name: deref(name1359, "abort"), RelationId: relation_id1360}
	result1362 := _t2155
	p.recordSpan(int(span_start1361), "Abort")
	return result1362
}

func (p *Parser) parse_export() *pb.Export {
	span_start1366 := int64(p.spanStart())
	var _t2156 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2157 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2157 = 1
		} else {
			var _t2158 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2158 = 0
			} else {
				_t2158 = -1
			}
			_t2157 = _t2158
		}
		_t2156 = _t2157
	} else {
		_t2156 = -1
	}
	prediction1363 := _t2156
	var _t2159 *pb.Export
	if prediction1363 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2160 := p.parse_export_iceberg_config()
		export_iceberg_config1365 := _t2160
		p.consumeLiteral(")")
		_t2161 := &pb.Export{}
		_t2161.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1365}
		_t2159 = _t2161
	} else {
		var _t2162 *pb.Export
		if prediction1363 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2163 := p.parse_export_csv_config()
			export_csv_config1364 := _t2163
			p.consumeLiteral(")")
			_t2164 := &pb.Export{}
			_t2164.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1364}
			_t2162 = _t2164
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2159 = _t2162
	}
	result1367 := _t2159
	p.recordSpan(int(span_start1366), "Export")
	return result1367
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1375 := int64(p.spanStart())
	var _t2165 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2166 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2166 = 0
		} else {
			var _t2167 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2167 = 1
			} else {
				_t2167 = -1
			}
			_t2166 = _t2167
		}
		_t2165 = _t2166
	} else {
		_t2165 = -1
	}
	prediction1368 := _t2165
	var _t2168 *pb.ExportCSVConfig
	if prediction1368 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2169 := p.parse_export_csv_path()
		export_csv_path1372 := _t2169
		_t2170 := p.parse_export_csv_columns_list()
		export_csv_columns_list1373 := _t2170
		_t2171 := p.parse_config_dict()
		config_dict1374 := _t2171
		p.consumeLiteral(")")
		_t2172 := p.construct_export_csv_config(export_csv_path1372, export_csv_columns_list1373, config_dict1374)
		_t2168 = _t2172
	} else {
		var _t2173 *pb.ExportCSVConfig
		if prediction1368 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2174 := p.parse_export_csv_path()
			export_csv_path1369 := _t2174
			_t2175 := p.parse_export_csv_source()
			export_csv_source1370 := _t2175
			_t2176 := p.parse_csv_config()
			csv_config1371 := _t2176
			p.consumeLiteral(")")
			_t2177 := p.construct_export_csv_config_with_source(export_csv_path1369, export_csv_source1370, csv_config1371)
			_t2173 = _t2177
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2168 = _t2173
	}
	result1376 := _t2168
	p.recordSpan(int(span_start1375), "ExportCSVConfig")
	return result1376
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1377 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1377
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1384 := int64(p.spanStart())
	var _t2178 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2179 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2179 = 1
		} else {
			var _t2180 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2180 = 0
			} else {
				_t2180 = -1
			}
			_t2179 = _t2180
		}
		_t2178 = _t2179
	} else {
		_t2178 = -1
	}
	prediction1378 := _t2178
	var _t2181 *pb.ExportCSVSource
	if prediction1378 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2182 := p.parse_relation_id()
		relation_id1383 := _t2182
		p.consumeLiteral(")")
		_t2183 := &pb.ExportCSVSource{}
		_t2183.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1383}
		_t2181 = _t2183
	} else {
		var _t2184 *pb.ExportCSVSource
		if prediction1378 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1379 := []*pb.ExportCSVColumn{}
			cond1380 := p.matchLookaheadLiteral("(", 0)
			for cond1380 {
				_t2185 := p.parse_export_csv_column()
				item1381 := _t2185
				xs1379 = append(xs1379, item1381)
				cond1380 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1382 := xs1379
			p.consumeLiteral(")")
			_t2186 := &pb.ExportCSVColumns{Columns: export_csv_columns1382}
			_t2187 := &pb.ExportCSVSource{}
			_t2187.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2186}
			_t2184 = _t2187
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2181 = _t2184
	}
	result1385 := _t2181
	p.recordSpan(int(span_start1384), "ExportCSVSource")
	return result1385
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1388 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1386 := p.consumeTerminal("STRING").Value.str
	_t2188 := p.parse_relation_id()
	relation_id1387 := _t2188
	p.consumeLiteral(")")
	_t2189 := &pb.ExportCSVColumn{ColumnName: string1386, ColumnData: relation_id1387}
	result1389 := _t2189
	p.recordSpan(int(span_start1388), "ExportCSVColumn")
	return result1389
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1390 := []*pb.ExportCSVColumn{}
	cond1391 := p.matchLookaheadLiteral("(", 0)
	for cond1391 {
		_t2190 := p.parse_export_csv_column()
		item1392 := _t2190
		xs1390 = append(xs1390, item1392)
		cond1391 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1393 := xs1390
	p.consumeLiteral(")")
	return export_csv_columns1393
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1399 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2191 := p.parse_iceberg_locator()
	iceberg_locator1394 := _t2191
	_t2192 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1395 := _t2192
	_t2193 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1396 := _t2193
	_t2194 := p.parse_iceberg_table_properties()
	iceberg_table_properties1397 := _t2194
	var _t2195 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2196 := p.parse_config_dict()
		_t2195 = _t2196
	}
	config_dict1398 := _t2195
	p.consumeLiteral(")")
	_t2197 := p.construct_export_iceberg_config_full(iceberg_locator1394, iceberg_catalog_config1395, export_iceberg_table_def1396, iceberg_table_properties1397, config_dict1398)
	result1400 := _t2197
	p.recordSpan(int(span_start1399), "ExportIcebergConfig")
	return result1400
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1402 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2198 := p.parse_relation_id()
	relation_id1401 := _t2198
	p.consumeLiteral(")")
	result1403 := relation_id1401
	p.recordSpan(int(span_start1402), "RelationId")
	return result1403
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1404 := [][]interface{}{}
	cond1405 := p.matchLookaheadLiteral("(", 0)
	for cond1405 {
		_t2199 := p.parse_iceberg_property_entry()
		item1406 := _t2199
		xs1404 = append(xs1404, item1406)
		cond1405 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1407 := xs1404
	p.consumeLiteral(")")
	return iceberg_property_entrys1407
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
