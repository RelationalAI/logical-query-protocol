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
	var _t2116 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2116
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2117 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2117
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2118 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2118
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2119 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2119
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2120 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2120
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2121 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2121
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2122 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2122
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2123 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2123
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2124 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2124
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2125 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2125
	_t2126 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2126
	_t2127 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2127
	_t2128 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2128
	_t2129 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2129
	_t2130 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2130
	_t2131 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2131
	_t2132 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2132
	_t2133 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2133
	_t2134 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2134
	_t2135 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2135
	_t2136 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2136
	_t2137 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2137
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2138 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2138
	_t2139 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2139
	_t2140 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2140
	_t2141 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2141
	_t2142 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2142
	_t2143 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2143
	_t2144 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2144
	_t2145 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2145
	_t2146 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2146
	_t2147 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2147.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2147.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2147
	_t2148 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2148
}

func (p *Parser) default_configure() *pb.Configure {
	_t2149 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2149
	_t2150 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2150
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
	_t2151 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2151
	_t2152 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2152
	_t2153 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2153
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2154 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2154
	_t2155 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2155
	_t2156 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2156
	_t2157 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2157
	_t2158 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2158
	_t2159 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2159
	_t2160 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2160
	_t2161 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2161
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2162 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2162
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2163 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2163
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2164 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2164
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2165 := config_dict
	if config_dict == nil {
		_t2165 = [][]interface{}{}
	}
	cfg := dictFromList(_t2165)
	_t2166 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2166
	_t2167 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2167
	_t2168 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2168
	table_props := stringMapFromPairs(table_property_pairs)
	_t2169 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2169
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start680 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1348 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1349 := p.parse_configure()
		_t1348 = _t1349
	}
	configure674 := _t1348
	var _t1350 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1351 := p.parse_sync()
		_t1350 = _t1351
	}
	sync675 := _t1350
	xs676 := []*pb.Epoch{}
	cond677 := p.matchLookaheadLiteral("(", 0)
	for cond677 {
		_t1352 := p.parse_epoch()
		item678 := _t1352
		xs676 = append(xs676, item678)
		cond677 = p.matchLookaheadLiteral("(", 0)
	}
	epochs679 := xs676
	p.consumeLiteral(")")
	_t1353 := p.default_configure()
	_t1354 := configure674
	if configure674 == nil {
		_t1354 = _t1353
	}
	_t1355 := &pb.Transaction{Epochs: epochs679, Configure: _t1354, Sync: sync675}
	result681 := _t1355
	p.recordSpan(int(span_start680), "Transaction")
	return result681
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start683 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1356 := p.parse_config_dict()
	config_dict682 := _t1356
	p.consumeLiteral(")")
	_t1357 := p.construct_configure(config_dict682)
	result684 := _t1357
	p.recordSpan(int(span_start683), "Configure")
	return result684
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs685 := [][]interface{}{}
	cond686 := p.matchLookaheadLiteral(":", 0)
	for cond686 {
		_t1358 := p.parse_config_key_value()
		item687 := _t1358
		xs685 = append(xs685, item687)
		cond686 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values688 := xs685
	p.consumeLiteral("}")
	return config_key_values688
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol689 := p.consumeTerminal("SYMBOL").Value.str
	_t1359 := p.parse_raw_value()
	raw_value690 := _t1359
	return []interface{}{symbol689, raw_value690}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start704 := int64(p.spanStart())
	var _t1360 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1360 = 12
	} else {
		var _t1361 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1361 = 11
		} else {
			var _t1362 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1362 = 12
			} else {
				var _t1363 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1364 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1364 = 1
					} else {
						var _t1365 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1365 = 0
						} else {
							_t1365 = -1
						}
						_t1364 = _t1365
					}
					_t1363 = _t1364
				} else {
					var _t1366 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1366 = 7
					} else {
						var _t1367 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1367 = 8
						} else {
							var _t1368 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1368 = 2
							} else {
								var _t1369 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1369 = 3
								} else {
									var _t1370 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1370 = 9
									} else {
										var _t1371 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1371 = 4
										} else {
											var _t1372 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1372 = 5
											} else {
												var _t1373 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1373 = 6
												} else {
													var _t1374 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1374 = 10
													} else {
														_t1374 = -1
													}
													_t1373 = _t1374
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
					_t1363 = _t1366
				}
				_t1362 = _t1363
			}
			_t1361 = _t1362
		}
		_t1360 = _t1361
	}
	prediction691 := _t1360
	var _t1375 *pb.Value
	if prediction691 == 12 {
		_t1376 := p.parse_boolean_value()
		boolean_value703 := _t1376
		_t1377 := &pb.Value{}
		_t1377.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value703}
		_t1375 = _t1377
	} else {
		var _t1378 *pb.Value
		if prediction691 == 11 {
			p.consumeLiteral("missing")
			_t1379 := &pb.MissingValue{}
			_t1380 := &pb.Value{}
			_t1380.Value = &pb.Value_MissingValue{MissingValue: _t1379}
			_t1378 = _t1380
		} else {
			var _t1381 *pb.Value
			if prediction691 == 10 {
				decimal702 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1382 := &pb.Value{}
				_t1382.Value = &pb.Value_DecimalValue{DecimalValue: decimal702}
				_t1381 = _t1382
			} else {
				var _t1383 *pb.Value
				if prediction691 == 9 {
					int128701 := p.consumeTerminal("INT128").Value.int128
					_t1384 := &pb.Value{}
					_t1384.Value = &pb.Value_Int128Value{Int128Value: int128701}
					_t1383 = _t1384
				} else {
					var _t1385 *pb.Value
					if prediction691 == 8 {
						uint128700 := p.consumeTerminal("UINT128").Value.uint128
						_t1386 := &pb.Value{}
						_t1386.Value = &pb.Value_Uint128Value{Uint128Value: uint128700}
						_t1385 = _t1386
					} else {
						var _t1387 *pb.Value
						if prediction691 == 7 {
							uint32699 := p.consumeTerminal("UINT32").Value.u32
							_t1388 := &pb.Value{}
							_t1388.Value = &pb.Value_Uint32Value{Uint32Value: uint32699}
							_t1387 = _t1388
						} else {
							var _t1389 *pb.Value
							if prediction691 == 6 {
								float698 := p.consumeTerminal("FLOAT").Value.f64
								_t1390 := &pb.Value{}
								_t1390.Value = &pb.Value_FloatValue{FloatValue: float698}
								_t1389 = _t1390
							} else {
								var _t1391 *pb.Value
								if prediction691 == 5 {
									float32697 := p.consumeTerminal("FLOAT32").Value.f32
									_t1392 := &pb.Value{}
									_t1392.Value = &pb.Value_Float32Value{Float32Value: float32697}
									_t1391 = _t1392
								} else {
									var _t1393 *pb.Value
									if prediction691 == 4 {
										int696 := p.consumeTerminal("INT").Value.i64
										_t1394 := &pb.Value{}
										_t1394.Value = &pb.Value_IntValue{IntValue: int696}
										_t1393 = _t1394
									} else {
										var _t1395 *pb.Value
										if prediction691 == 3 {
											int32695 := p.consumeTerminal("INT32").Value.i32
											_t1396 := &pb.Value{}
											_t1396.Value = &pb.Value_Int32Value{Int32Value: int32695}
											_t1395 = _t1396
										} else {
											var _t1397 *pb.Value
											if prediction691 == 2 {
												string694 := p.consumeTerminal("STRING").Value.str
												_t1398 := &pb.Value{}
												_t1398.Value = &pb.Value_StringValue{StringValue: string694}
												_t1397 = _t1398
											} else {
												var _t1399 *pb.Value
												if prediction691 == 1 {
													_t1400 := p.parse_raw_datetime()
													raw_datetime693 := _t1400
													_t1401 := &pb.Value{}
													_t1401.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime693}
													_t1399 = _t1401
												} else {
													var _t1402 *pb.Value
													if prediction691 == 0 {
														_t1403 := p.parse_raw_date()
														raw_date692 := _t1403
														_t1404 := &pb.Value{}
														_t1404.Value = &pb.Value_DateValue{DateValue: raw_date692}
														_t1402 = _t1404
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1399 = _t1402
												}
												_t1397 = _t1399
											}
											_t1395 = _t1397
										}
										_t1393 = _t1395
									}
									_t1391 = _t1393
								}
								_t1389 = _t1391
							}
							_t1387 = _t1389
						}
						_t1385 = _t1387
					}
					_t1383 = _t1385
				}
				_t1381 = _t1383
			}
			_t1378 = _t1381
		}
		_t1375 = _t1378
	}
	result705 := _t1375
	p.recordSpan(int(span_start704), "Value")
	return result705
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int706 := p.consumeTerminal("INT").Value.i64
	int_3707 := p.consumeTerminal("INT").Value.i64
	int_4708 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1405 := &pb.DateValue{Year: int32(int706), Month: int32(int_3707), Day: int32(int_4708)}
	result710 := _t1405
	p.recordSpan(int(span_start709), "DateValue")
	return result710
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start718 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int711 := p.consumeTerminal("INT").Value.i64
	int_3712 := p.consumeTerminal("INT").Value.i64
	int_4713 := p.consumeTerminal("INT").Value.i64
	int_5714 := p.consumeTerminal("INT").Value.i64
	int_6715 := p.consumeTerminal("INT").Value.i64
	int_7716 := p.consumeTerminal("INT").Value.i64
	var _t1406 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1406 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8717 := _t1406
	p.consumeLiteral(")")
	_t1407 := &pb.DateTimeValue{Year: int32(int711), Month: int32(int_3712), Day: int32(int_4713), Hour: int32(int_5714), Minute: int32(int_6715), Second: int32(int_7716), Microsecond: int32(deref(int_8717, 0))}
	result719 := _t1407
	p.recordSpan(int(span_start718), "DateTimeValue")
	return result719
}

func (p *Parser) parse_boolean_value() bool {
	var _t1408 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1408 = 0
	} else {
		var _t1409 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1409 = 1
		} else {
			_t1409 = -1
		}
		_t1408 = _t1409
	}
	prediction720 := _t1408
	var _t1410 bool
	if prediction720 == 1 {
		p.consumeLiteral("false")
		_t1410 = false
	} else {
		var _t1411 bool
		if prediction720 == 0 {
			p.consumeLiteral("true")
			_t1411 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1410 = _t1411
	}
	return _t1410
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs721 := []*pb.FragmentId{}
	cond722 := p.matchLookaheadLiteral(":", 0)
	for cond722 {
		_t1412 := p.parse_fragment_id()
		item723 := _t1412
		xs721 = append(xs721, item723)
		cond722 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids724 := xs721
	p.consumeLiteral(")")
	_t1413 := &pb.Sync{Fragments: fragment_ids724}
	result726 := _t1413
	p.recordSpan(int(span_start725), "Sync")
	return result726
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start728 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol727 := p.consumeTerminal("SYMBOL").Value.str
	result729 := &pb.FragmentId{Id: []byte(symbol727)}
	p.recordSpan(int(span_start728), "FragmentId")
	return result729
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start732 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1414 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1415 := p.parse_epoch_writes()
		_t1414 = _t1415
	}
	epoch_writes730 := _t1414
	var _t1416 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1417 := p.parse_epoch_reads()
		_t1416 = _t1417
	}
	epoch_reads731 := _t1416
	p.consumeLiteral(")")
	_t1418 := epoch_writes730
	if epoch_writes730 == nil {
		_t1418 = []*pb.Write{}
	}
	_t1419 := epoch_reads731
	if epoch_reads731 == nil {
		_t1419 = []*pb.Read{}
	}
	_t1420 := &pb.Epoch{Writes: _t1418, Reads: _t1419}
	result733 := _t1420
	p.recordSpan(int(span_start732), "Epoch")
	return result733
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs734 := []*pb.Write{}
	cond735 := p.matchLookaheadLiteral("(", 0)
	for cond735 {
		_t1421 := p.parse_write()
		item736 := _t1421
		xs734 = append(xs734, item736)
		cond735 = p.matchLookaheadLiteral("(", 0)
	}
	writes737 := xs734
	p.consumeLiteral(")")
	return writes737
}

func (p *Parser) parse_write() *pb.Write {
	span_start743 := int64(p.spanStart())
	var _t1422 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1423 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1423 = 1
		} else {
			var _t1424 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1424 = 3
			} else {
				var _t1425 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1425 = 0
				} else {
					var _t1426 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1426 = 2
					} else {
						_t1426 = -1
					}
					_t1425 = _t1426
				}
				_t1424 = _t1425
			}
			_t1423 = _t1424
		}
		_t1422 = _t1423
	} else {
		_t1422 = -1
	}
	prediction738 := _t1422
	var _t1427 *pb.Write
	if prediction738 == 3 {
		_t1428 := p.parse_snapshot()
		snapshot742 := _t1428
		_t1429 := &pb.Write{}
		_t1429.WriteType = &pb.Write_Snapshot{Snapshot: snapshot742}
		_t1427 = _t1429
	} else {
		var _t1430 *pb.Write
		if prediction738 == 2 {
			_t1431 := p.parse_context()
			context741 := _t1431
			_t1432 := &pb.Write{}
			_t1432.WriteType = &pb.Write_Context{Context: context741}
			_t1430 = _t1432
		} else {
			var _t1433 *pb.Write
			if prediction738 == 1 {
				_t1434 := p.parse_undefine()
				undefine740 := _t1434
				_t1435 := &pb.Write{}
				_t1435.WriteType = &pb.Write_Undefine{Undefine: undefine740}
				_t1433 = _t1435
			} else {
				var _t1436 *pb.Write
				if prediction738 == 0 {
					_t1437 := p.parse_define()
					define739 := _t1437
					_t1438 := &pb.Write{}
					_t1438.WriteType = &pb.Write_Define{Define: define739}
					_t1436 = _t1438
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1433 = _t1436
			}
			_t1430 = _t1433
		}
		_t1427 = _t1430
	}
	result744 := _t1427
	p.recordSpan(int(span_start743), "Write")
	return result744
}

func (p *Parser) parse_define() *pb.Define {
	span_start746 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1439 := p.parse_fragment()
	fragment745 := _t1439
	p.consumeLiteral(")")
	_t1440 := &pb.Define{Fragment: fragment745}
	result747 := _t1440
	p.recordSpan(int(span_start746), "Define")
	return result747
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1441 := p.parse_new_fragment_id()
	new_fragment_id748 := _t1441
	xs749 := []*pb.Declaration{}
	cond750 := p.matchLookaheadLiteral("(", 0)
	for cond750 {
		_t1442 := p.parse_declaration()
		item751 := _t1442
		xs749 = append(xs749, item751)
		cond750 = p.matchLookaheadLiteral("(", 0)
	}
	declarations752 := xs749
	p.consumeLiteral(")")
	result754 := p.constructFragment(new_fragment_id748, declarations752)
	p.recordSpan(int(span_start753), "Fragment")
	return result754
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start756 := int64(p.spanStart())
	_t1443 := p.parse_fragment_id()
	fragment_id755 := _t1443
	p.startFragment(fragment_id755)
	result757 := fragment_id755
	p.recordSpan(int(span_start756), "FragmentId")
	return result757
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start763 := int64(p.spanStart())
	var _t1444 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1445 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1445 = 3
		} else {
			var _t1446 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1446 = 2
			} else {
				var _t1447 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1447 = 3
				} else {
					var _t1448 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1448 = 0
					} else {
						var _t1449 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1449 = 3
						} else {
							var _t1450 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1450 = 3
							} else {
								var _t1451 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1451 = 1
								} else {
									_t1451 = -1
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
	} else {
		_t1444 = -1
	}
	prediction758 := _t1444
	var _t1452 *pb.Declaration
	if prediction758 == 3 {
		_t1453 := p.parse_data()
		data762 := _t1453
		_t1454 := &pb.Declaration{}
		_t1454.DeclarationType = &pb.Declaration_Data{Data: data762}
		_t1452 = _t1454
	} else {
		var _t1455 *pb.Declaration
		if prediction758 == 2 {
			_t1456 := p.parse_constraint()
			constraint761 := _t1456
			_t1457 := &pb.Declaration{}
			_t1457.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint761}
			_t1455 = _t1457
		} else {
			var _t1458 *pb.Declaration
			if prediction758 == 1 {
				_t1459 := p.parse_algorithm()
				algorithm760 := _t1459
				_t1460 := &pb.Declaration{}
				_t1460.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm760}
				_t1458 = _t1460
			} else {
				var _t1461 *pb.Declaration
				if prediction758 == 0 {
					_t1462 := p.parse_def()
					def759 := _t1462
					_t1463 := &pb.Declaration{}
					_t1463.DeclarationType = &pb.Declaration_Def{Def: def759}
					_t1461 = _t1463
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1458 = _t1461
			}
			_t1455 = _t1458
		}
		_t1452 = _t1455
	}
	result764 := _t1452
	p.recordSpan(int(span_start763), "Declaration")
	return result764
}

func (p *Parser) parse_def() *pb.Def {
	span_start768 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1464 := p.parse_relation_id()
	relation_id765 := _t1464
	_t1465 := p.parse_abstraction()
	abstraction766 := _t1465
	var _t1466 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1467 := p.parse_attrs()
		_t1466 = _t1467
	}
	attrs767 := _t1466
	p.consumeLiteral(")")
	_t1468 := attrs767
	if attrs767 == nil {
		_t1468 = []*pb.Attribute{}
	}
	_t1469 := &pb.Def{Name: relation_id765, Body: abstraction766, Attrs: _t1468}
	result769 := _t1469
	p.recordSpan(int(span_start768), "Def")
	return result769
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start773 := int64(p.spanStart())
	var _t1470 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1470 = 0
	} else {
		var _t1471 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1471 = 1
		} else {
			_t1471 = -1
		}
		_t1470 = _t1471
	}
	prediction770 := _t1470
	var _t1472 *pb.RelationId
	if prediction770 == 1 {
		uint128772 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128772
		_t1472 = &pb.RelationId{IdLow: uint128772.Low, IdHigh: uint128772.High}
	} else {
		var _t1473 *pb.RelationId
		if prediction770 == 0 {
			p.consumeLiteral(":")
			symbol771 := p.consumeTerminal("SYMBOL").Value.str
			_t1473 = p.relationIdFromString(symbol771)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1472 = _t1473
	}
	result774 := _t1472
	p.recordSpan(int(span_start773), "RelationId")
	return result774
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start777 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1474 := p.parse_bindings()
	bindings775 := _t1474
	_t1475 := p.parse_formula()
	formula776 := _t1475
	p.consumeLiteral(")")
	_t1476 := &pb.Abstraction{Vars: listConcat(bindings775[0].([]*pb.Binding), bindings775[1].([]*pb.Binding)), Value: formula776}
	result778 := _t1476
	p.recordSpan(int(span_start777), "Abstraction")
	return result778
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs779 := []*pb.Binding{}
	cond780 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond780 {
		_t1477 := p.parse_binding()
		item781 := _t1477
		xs779 = append(xs779, item781)
		cond780 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings782 := xs779
	var _t1478 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1479 := p.parse_value_bindings()
		_t1478 = _t1479
	}
	value_bindings783 := _t1478
	p.consumeLiteral("]")
	_t1480 := value_bindings783
	if value_bindings783 == nil {
		_t1480 = []*pb.Binding{}
	}
	return []interface{}{bindings782, _t1480}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start786 := int64(p.spanStart())
	symbol784 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1481 := p.parse_type()
	type785 := _t1481
	_t1482 := &pb.Var{Name: symbol784}
	_t1483 := &pb.Binding{Var: _t1482, Type: type785}
	result787 := _t1483
	p.recordSpan(int(span_start786), "Binding")
	return result787
}

func (p *Parser) parse_type() *pb.Type {
	span_start803 := int64(p.spanStart())
	var _t1484 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1484 = 0
	} else {
		var _t1485 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1485 = 13
		} else {
			var _t1486 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1486 = 4
			} else {
				var _t1487 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1487 = 1
				} else {
					var _t1488 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1488 = 8
					} else {
						var _t1489 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1489 = 11
						} else {
							var _t1490 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1490 = 5
							} else {
								var _t1491 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1491 = 2
								} else {
									var _t1492 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1492 = 12
									} else {
										var _t1493 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1493 = 3
										} else {
											var _t1494 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1494 = 7
											} else {
												var _t1495 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1495 = 6
												} else {
													var _t1496 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1496 = 10
													} else {
														var _t1497 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1497 = 9
														} else {
															_t1497 = -1
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
				_t1486 = _t1487
			}
			_t1485 = _t1486
		}
		_t1484 = _t1485
	}
	prediction788 := _t1484
	var _t1498 *pb.Type
	if prediction788 == 13 {
		_t1499 := p.parse_uint32_type()
		uint32_type802 := _t1499
		_t1500 := &pb.Type{}
		_t1500.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type802}
		_t1498 = _t1500
	} else {
		var _t1501 *pb.Type
		if prediction788 == 12 {
			_t1502 := p.parse_float32_type()
			float32_type801 := _t1502
			_t1503 := &pb.Type{}
			_t1503.Type = &pb.Type_Float32Type{Float32Type: float32_type801}
			_t1501 = _t1503
		} else {
			var _t1504 *pb.Type
			if prediction788 == 11 {
				_t1505 := p.parse_int32_type()
				int32_type800 := _t1505
				_t1506 := &pb.Type{}
				_t1506.Type = &pb.Type_Int32Type{Int32Type: int32_type800}
				_t1504 = _t1506
			} else {
				var _t1507 *pb.Type
				if prediction788 == 10 {
					_t1508 := p.parse_boolean_type()
					boolean_type799 := _t1508
					_t1509 := &pb.Type{}
					_t1509.Type = &pb.Type_BooleanType{BooleanType: boolean_type799}
					_t1507 = _t1509
				} else {
					var _t1510 *pb.Type
					if prediction788 == 9 {
						_t1511 := p.parse_decimal_type()
						decimal_type798 := _t1511
						_t1512 := &pb.Type{}
						_t1512.Type = &pb.Type_DecimalType{DecimalType: decimal_type798}
						_t1510 = _t1512
					} else {
						var _t1513 *pb.Type
						if prediction788 == 8 {
							_t1514 := p.parse_missing_type()
							missing_type797 := _t1514
							_t1515 := &pb.Type{}
							_t1515.Type = &pb.Type_MissingType{MissingType: missing_type797}
							_t1513 = _t1515
						} else {
							var _t1516 *pb.Type
							if prediction788 == 7 {
								_t1517 := p.parse_datetime_type()
								datetime_type796 := _t1517
								_t1518 := &pb.Type{}
								_t1518.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type796}
								_t1516 = _t1518
							} else {
								var _t1519 *pb.Type
								if prediction788 == 6 {
									_t1520 := p.parse_date_type()
									date_type795 := _t1520
									_t1521 := &pb.Type{}
									_t1521.Type = &pb.Type_DateType{DateType: date_type795}
									_t1519 = _t1521
								} else {
									var _t1522 *pb.Type
									if prediction788 == 5 {
										_t1523 := p.parse_int128_type()
										int128_type794 := _t1523
										_t1524 := &pb.Type{}
										_t1524.Type = &pb.Type_Int128Type{Int128Type: int128_type794}
										_t1522 = _t1524
									} else {
										var _t1525 *pb.Type
										if prediction788 == 4 {
											_t1526 := p.parse_uint128_type()
											uint128_type793 := _t1526
											_t1527 := &pb.Type{}
											_t1527.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type793}
											_t1525 = _t1527
										} else {
											var _t1528 *pb.Type
											if prediction788 == 3 {
												_t1529 := p.parse_float_type()
												float_type792 := _t1529
												_t1530 := &pb.Type{}
												_t1530.Type = &pb.Type_FloatType{FloatType: float_type792}
												_t1528 = _t1530
											} else {
												var _t1531 *pb.Type
												if prediction788 == 2 {
													_t1532 := p.parse_int_type()
													int_type791 := _t1532
													_t1533 := &pb.Type{}
													_t1533.Type = &pb.Type_IntType{IntType: int_type791}
													_t1531 = _t1533
												} else {
													var _t1534 *pb.Type
													if prediction788 == 1 {
														_t1535 := p.parse_string_type()
														string_type790 := _t1535
														_t1536 := &pb.Type{}
														_t1536.Type = &pb.Type_StringType{StringType: string_type790}
														_t1534 = _t1536
													} else {
														var _t1537 *pb.Type
														if prediction788 == 0 {
															_t1538 := p.parse_unspecified_type()
															unspecified_type789 := _t1538
															_t1539 := &pb.Type{}
															_t1539.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type789}
															_t1537 = _t1539
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1534 = _t1537
													}
													_t1531 = _t1534
												}
												_t1528 = _t1531
											}
											_t1525 = _t1528
										}
										_t1522 = _t1525
									}
									_t1519 = _t1522
								}
								_t1516 = _t1519
							}
							_t1513 = _t1516
						}
						_t1510 = _t1513
					}
					_t1507 = _t1510
				}
				_t1504 = _t1507
			}
			_t1501 = _t1504
		}
		_t1498 = _t1501
	}
	result804 := _t1498
	p.recordSpan(int(span_start803), "Type")
	return result804
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1540 := &pb.UnspecifiedType{}
	result806 := _t1540
	p.recordSpan(int(span_start805), "UnspecifiedType")
	return result806
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1541 := &pb.StringType{}
	result808 := _t1541
	p.recordSpan(int(span_start807), "StringType")
	return result808
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1542 := &pb.IntType{}
	result810 := _t1542
	p.recordSpan(int(span_start809), "IntType")
	return result810
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1543 := &pb.FloatType{}
	result812 := _t1543
	p.recordSpan(int(span_start811), "FloatType")
	return result812
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1544 := &pb.UInt128Type{}
	result814 := _t1544
	p.recordSpan(int(span_start813), "UInt128Type")
	return result814
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1545 := &pb.Int128Type{}
	result816 := _t1545
	p.recordSpan(int(span_start815), "Int128Type")
	return result816
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1546 := &pb.DateType{}
	result818 := _t1546
	p.recordSpan(int(span_start817), "DateType")
	return result818
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1547 := &pb.DateTimeType{}
	result820 := _t1547
	p.recordSpan(int(span_start819), "DateTimeType")
	return result820
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start821 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1548 := &pb.MissingType{}
	result822 := _t1548
	p.recordSpan(int(span_start821), "MissingType")
	return result822
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start825 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int823 := p.consumeTerminal("INT").Value.i64
	int_3824 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1549 := &pb.DecimalType{Precision: int32(int823), Scale: int32(int_3824)}
	result826 := _t1549
	p.recordSpan(int(span_start825), "DecimalType")
	return result826
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start827 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1550 := &pb.BooleanType{}
	result828 := _t1550
	p.recordSpan(int(span_start827), "BooleanType")
	return result828
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1551 := &pb.Int32Type{}
	result830 := _t1551
	p.recordSpan(int(span_start829), "Int32Type")
	return result830
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start831 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1552 := &pb.Float32Type{}
	result832 := _t1552
	p.recordSpan(int(span_start831), "Float32Type")
	return result832
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start833 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1553 := &pb.UInt32Type{}
	result834 := _t1553
	p.recordSpan(int(span_start833), "UInt32Type")
	return result834
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs835 := []*pb.Binding{}
	cond836 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond836 {
		_t1554 := p.parse_binding()
		item837 := _t1554
		xs835 = append(xs835, item837)
		cond836 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings838 := xs835
	return bindings838
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start853 := int64(p.spanStart())
	var _t1555 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1556 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1556 = 0
		} else {
			var _t1557 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1557 = 11
			} else {
				var _t1558 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1558 = 3
				} else {
					var _t1559 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1559 = 10
					} else {
						var _t1560 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1560 = 9
						} else {
							var _t1561 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1561 = 5
							} else {
								var _t1562 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1562 = 6
								} else {
									var _t1563 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1563 = 7
									} else {
										var _t1564 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1564 = 1
										} else {
											var _t1565 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1565 = 2
											} else {
												var _t1566 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1566 = 12
												} else {
													var _t1567 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1567 = 8
													} else {
														var _t1568 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1568 = 4
														} else {
															var _t1569 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1569 = 10
															} else {
																var _t1570 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1570 = 10
																} else {
																	var _t1571 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1571 = 10
																	} else {
																		var _t1572 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1572 = 10
																		} else {
																			var _t1573 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1573 = 10
																			} else {
																				var _t1574 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1574 = 10
																				} else {
																					var _t1575 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1575 = 10
																					} else {
																						var _t1576 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1576 = 10
																						} else {
																							var _t1577 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1577 = 10
																							} else {
																								_t1577 = -1
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
						_t1559 = _t1560
					}
					_t1558 = _t1559
				}
				_t1557 = _t1558
			}
			_t1556 = _t1557
		}
		_t1555 = _t1556
	} else {
		_t1555 = -1
	}
	prediction839 := _t1555
	var _t1578 *pb.Formula
	if prediction839 == 12 {
		_t1579 := p.parse_cast()
		cast852 := _t1579
		_t1580 := &pb.Formula{}
		_t1580.FormulaType = &pb.Formula_Cast{Cast: cast852}
		_t1578 = _t1580
	} else {
		var _t1581 *pb.Formula
		if prediction839 == 11 {
			_t1582 := p.parse_rel_atom()
			rel_atom851 := _t1582
			_t1583 := &pb.Formula{}
			_t1583.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom851}
			_t1581 = _t1583
		} else {
			var _t1584 *pb.Formula
			if prediction839 == 10 {
				_t1585 := p.parse_primitive()
				primitive850 := _t1585
				_t1586 := &pb.Formula{}
				_t1586.FormulaType = &pb.Formula_Primitive{Primitive: primitive850}
				_t1584 = _t1586
			} else {
				var _t1587 *pb.Formula
				if prediction839 == 9 {
					_t1588 := p.parse_pragma()
					pragma849 := _t1588
					_t1589 := &pb.Formula{}
					_t1589.FormulaType = &pb.Formula_Pragma{Pragma: pragma849}
					_t1587 = _t1589
				} else {
					var _t1590 *pb.Formula
					if prediction839 == 8 {
						_t1591 := p.parse_atom()
						atom848 := _t1591
						_t1592 := &pb.Formula{}
						_t1592.FormulaType = &pb.Formula_Atom{Atom: atom848}
						_t1590 = _t1592
					} else {
						var _t1593 *pb.Formula
						if prediction839 == 7 {
							_t1594 := p.parse_ffi()
							ffi847 := _t1594
							_t1595 := &pb.Formula{}
							_t1595.FormulaType = &pb.Formula_Ffi{Ffi: ffi847}
							_t1593 = _t1595
						} else {
							var _t1596 *pb.Formula
							if prediction839 == 6 {
								_t1597 := p.parse_not()
								not846 := _t1597
								_t1598 := &pb.Formula{}
								_t1598.FormulaType = &pb.Formula_Not{Not: not846}
								_t1596 = _t1598
							} else {
								var _t1599 *pb.Formula
								if prediction839 == 5 {
									_t1600 := p.parse_disjunction()
									disjunction845 := _t1600
									_t1601 := &pb.Formula{}
									_t1601.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction845}
									_t1599 = _t1601
								} else {
									var _t1602 *pb.Formula
									if prediction839 == 4 {
										_t1603 := p.parse_conjunction()
										conjunction844 := _t1603
										_t1604 := &pb.Formula{}
										_t1604.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction844}
										_t1602 = _t1604
									} else {
										var _t1605 *pb.Formula
										if prediction839 == 3 {
											_t1606 := p.parse_reduce()
											reduce843 := _t1606
											_t1607 := &pb.Formula{}
											_t1607.FormulaType = &pb.Formula_Reduce{Reduce: reduce843}
											_t1605 = _t1607
										} else {
											var _t1608 *pb.Formula
											if prediction839 == 2 {
												_t1609 := p.parse_exists()
												exists842 := _t1609
												_t1610 := &pb.Formula{}
												_t1610.FormulaType = &pb.Formula_Exists{Exists: exists842}
												_t1608 = _t1610
											} else {
												var _t1611 *pb.Formula
												if prediction839 == 1 {
													_t1612 := p.parse_false()
													false841 := _t1612
													_t1613 := &pb.Formula{}
													_t1613.FormulaType = &pb.Formula_Disjunction{Disjunction: false841}
													_t1611 = _t1613
												} else {
													var _t1614 *pb.Formula
													if prediction839 == 0 {
														_t1615 := p.parse_true()
														true840 := _t1615
														_t1616 := &pb.Formula{}
														_t1616.FormulaType = &pb.Formula_Conjunction{Conjunction: true840}
														_t1614 = _t1616
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1581 = _t1584
		}
		_t1578 = _t1581
	}
	result854 := _t1578
	p.recordSpan(int(span_start853), "Formula")
	return result854
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1617 := &pb.Conjunction{Args: []*pb.Formula{}}
	result856 := _t1617
	p.recordSpan(int(span_start855), "Conjunction")
	return result856
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1618 := &pb.Disjunction{Args: []*pb.Formula{}}
	result858 := _t1618
	p.recordSpan(int(span_start857), "Disjunction")
	return result858
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1619 := p.parse_bindings()
	bindings859 := _t1619
	_t1620 := p.parse_formula()
	formula860 := _t1620
	p.consumeLiteral(")")
	_t1621 := &pb.Abstraction{Vars: listConcat(bindings859[0].([]*pb.Binding), bindings859[1].([]*pb.Binding)), Value: formula860}
	_t1622 := &pb.Exists{Body: _t1621}
	result862 := _t1622
	p.recordSpan(int(span_start861), "Exists")
	return result862
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1623 := p.parse_abstraction()
	abstraction863 := _t1623
	_t1624 := p.parse_abstraction()
	abstraction_3864 := _t1624
	_t1625 := p.parse_terms()
	terms865 := _t1625
	p.consumeLiteral(")")
	_t1626 := &pb.Reduce{Op: abstraction863, Body: abstraction_3864, Terms: terms865}
	result867 := _t1626
	p.recordSpan(int(span_start866), "Reduce")
	return result867
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs868 := []*pb.Term{}
	cond869 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond869 {
		_t1627 := p.parse_term()
		item870 := _t1627
		xs868 = append(xs868, item870)
		cond869 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms871 := xs868
	p.consumeLiteral(")")
	return terms871
}

func (p *Parser) parse_term() *pb.Term {
	span_start875 := int64(p.spanStart())
	var _t1628 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1628 = 1
	} else {
		var _t1629 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1629 = 1
		} else {
			var _t1630 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1630 = 1
			} else {
				var _t1631 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1631 = 1
				} else {
					var _t1632 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1632 = 0
					} else {
						var _t1633 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1633 = 1
						} else {
							var _t1634 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1634 = 1
							} else {
								var _t1635 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1635 = 1
								} else {
									var _t1636 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1636 = 1
									} else {
										var _t1637 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1637 = 1
										} else {
											var _t1638 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1638 = 1
											} else {
												var _t1639 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1639 = 1
												} else {
													var _t1640 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1640 = 1
													} else {
														var _t1641 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1641 = 1
														} else {
															_t1641 = -1
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
	prediction872 := _t1628
	var _t1642 *pb.Term
	if prediction872 == 1 {
		_t1643 := p.parse_value()
		value874 := _t1643
		_t1644 := &pb.Term{}
		_t1644.TermType = &pb.Term_Constant{Constant: value874}
		_t1642 = _t1644
	} else {
		var _t1645 *pb.Term
		if prediction872 == 0 {
			_t1646 := p.parse_var()
			var873 := _t1646
			_t1647 := &pb.Term{}
			_t1647.TermType = &pb.Term_Var{Var: var873}
			_t1645 = _t1647
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1642 = _t1645
	}
	result876 := _t1642
	p.recordSpan(int(span_start875), "Term")
	return result876
}

func (p *Parser) parse_var() *pb.Var {
	span_start878 := int64(p.spanStart())
	symbol877 := p.consumeTerminal("SYMBOL").Value.str
	_t1648 := &pb.Var{Name: symbol877}
	result879 := _t1648
	p.recordSpan(int(span_start878), "Var")
	return result879
}

func (p *Parser) parse_value() *pb.Value {
	span_start893 := int64(p.spanStart())
	var _t1649 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1649 = 12
	} else {
		var _t1650 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1650 = 11
		} else {
			var _t1651 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1651 = 12
			} else {
				var _t1652 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1653 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1653 = 1
					} else {
						var _t1654 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1654 = 0
						} else {
							_t1654 = -1
						}
						_t1653 = _t1654
					}
					_t1652 = _t1653
				} else {
					var _t1655 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1655 = 7
					} else {
						var _t1656 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1656 = 8
						} else {
							var _t1657 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1657 = 2
							} else {
								var _t1658 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1658 = 3
								} else {
									var _t1659 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1659 = 9
									} else {
										var _t1660 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1660 = 4
										} else {
											var _t1661 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1661 = 5
											} else {
												var _t1662 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1662 = 6
												} else {
													var _t1663 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1663 = 10
													} else {
														_t1663 = -1
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
					_t1652 = _t1655
				}
				_t1651 = _t1652
			}
			_t1650 = _t1651
		}
		_t1649 = _t1650
	}
	prediction880 := _t1649
	var _t1664 *pb.Value
	if prediction880 == 12 {
		_t1665 := p.parse_boolean_value()
		boolean_value892 := _t1665
		_t1666 := &pb.Value{}
		_t1666.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value892}
		_t1664 = _t1666
	} else {
		var _t1667 *pb.Value
		if prediction880 == 11 {
			p.consumeLiteral("missing")
			_t1668 := &pb.MissingValue{}
			_t1669 := &pb.Value{}
			_t1669.Value = &pb.Value_MissingValue{MissingValue: _t1668}
			_t1667 = _t1669
		} else {
			var _t1670 *pb.Value
			if prediction880 == 10 {
				formatted_decimal891 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1671 := &pb.Value{}
				_t1671.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal891}
				_t1670 = _t1671
			} else {
				var _t1672 *pb.Value
				if prediction880 == 9 {
					formatted_int128890 := p.consumeTerminal("INT128").Value.int128
					_t1673 := &pb.Value{}
					_t1673.Value = &pb.Value_Int128Value{Int128Value: formatted_int128890}
					_t1672 = _t1673
				} else {
					var _t1674 *pb.Value
					if prediction880 == 8 {
						formatted_uint128889 := p.consumeTerminal("UINT128").Value.uint128
						_t1675 := &pb.Value{}
						_t1675.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128889}
						_t1674 = _t1675
					} else {
						var _t1676 *pb.Value
						if prediction880 == 7 {
							formatted_uint32888 := p.consumeTerminal("UINT32").Value.u32
							_t1677 := &pb.Value{}
							_t1677.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32888}
							_t1676 = _t1677
						} else {
							var _t1678 *pb.Value
							if prediction880 == 6 {
								formatted_float887 := p.consumeTerminal("FLOAT").Value.f64
								_t1679 := &pb.Value{}
								_t1679.Value = &pb.Value_FloatValue{FloatValue: formatted_float887}
								_t1678 = _t1679
							} else {
								var _t1680 *pb.Value
								if prediction880 == 5 {
									formatted_float32886 := p.consumeTerminal("FLOAT32").Value.f32
									_t1681 := &pb.Value{}
									_t1681.Value = &pb.Value_Float32Value{Float32Value: formatted_float32886}
									_t1680 = _t1681
								} else {
									var _t1682 *pb.Value
									if prediction880 == 4 {
										formatted_int885 := p.consumeTerminal("INT").Value.i64
										_t1683 := &pb.Value{}
										_t1683.Value = &pb.Value_IntValue{IntValue: formatted_int885}
										_t1682 = _t1683
									} else {
										var _t1684 *pb.Value
										if prediction880 == 3 {
											formatted_int32884 := p.consumeTerminal("INT32").Value.i32
											_t1685 := &pb.Value{}
											_t1685.Value = &pb.Value_Int32Value{Int32Value: formatted_int32884}
											_t1684 = _t1685
										} else {
											var _t1686 *pb.Value
											if prediction880 == 2 {
												formatted_string883 := p.consumeTerminal("STRING").Value.str
												_t1687 := &pb.Value{}
												_t1687.Value = &pb.Value_StringValue{StringValue: formatted_string883}
												_t1686 = _t1687
											} else {
												var _t1688 *pb.Value
												if prediction880 == 1 {
													_t1689 := p.parse_datetime()
													datetime882 := _t1689
													_t1690 := &pb.Value{}
													_t1690.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime882}
													_t1688 = _t1690
												} else {
													var _t1691 *pb.Value
													if prediction880 == 0 {
														_t1692 := p.parse_date()
														date881 := _t1692
														_t1693 := &pb.Value{}
														_t1693.Value = &pb.Value_DateValue{DateValue: date881}
														_t1691 = _t1693
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1688 = _t1691
												}
												_t1686 = _t1688
											}
											_t1684 = _t1686
										}
										_t1682 = _t1684
									}
									_t1680 = _t1682
								}
								_t1678 = _t1680
							}
							_t1676 = _t1678
						}
						_t1674 = _t1676
					}
					_t1672 = _t1674
				}
				_t1670 = _t1672
			}
			_t1667 = _t1670
		}
		_t1664 = _t1667
	}
	result894 := _t1664
	p.recordSpan(int(span_start893), "Value")
	return result894
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start898 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int895 := p.consumeTerminal("INT").Value.i64
	formatted_int_3896 := p.consumeTerminal("INT").Value.i64
	formatted_int_4897 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1694 := &pb.DateValue{Year: int32(formatted_int895), Month: int32(formatted_int_3896), Day: int32(formatted_int_4897)}
	result899 := _t1694
	p.recordSpan(int(span_start898), "DateValue")
	return result899
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start907 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int900 := p.consumeTerminal("INT").Value.i64
	formatted_int_3901 := p.consumeTerminal("INT").Value.i64
	formatted_int_4902 := p.consumeTerminal("INT").Value.i64
	formatted_int_5903 := p.consumeTerminal("INT").Value.i64
	formatted_int_6904 := p.consumeTerminal("INT").Value.i64
	formatted_int_7905 := p.consumeTerminal("INT").Value.i64
	var _t1695 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1695 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8906 := _t1695
	p.consumeLiteral(")")
	_t1696 := &pb.DateTimeValue{Year: int32(formatted_int900), Month: int32(formatted_int_3901), Day: int32(formatted_int_4902), Hour: int32(formatted_int_5903), Minute: int32(formatted_int_6904), Second: int32(formatted_int_7905), Microsecond: int32(deref(formatted_int_8906, 0))}
	result908 := _t1696
	p.recordSpan(int(span_start907), "DateTimeValue")
	return result908
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs909 := []*pb.Formula{}
	cond910 := p.matchLookaheadLiteral("(", 0)
	for cond910 {
		_t1697 := p.parse_formula()
		item911 := _t1697
		xs909 = append(xs909, item911)
		cond910 = p.matchLookaheadLiteral("(", 0)
	}
	formulas912 := xs909
	p.consumeLiteral(")")
	_t1698 := &pb.Conjunction{Args: formulas912}
	result914 := _t1698
	p.recordSpan(int(span_start913), "Conjunction")
	return result914
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start919 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs915 := []*pb.Formula{}
	cond916 := p.matchLookaheadLiteral("(", 0)
	for cond916 {
		_t1699 := p.parse_formula()
		item917 := _t1699
		xs915 = append(xs915, item917)
		cond916 = p.matchLookaheadLiteral("(", 0)
	}
	formulas918 := xs915
	p.consumeLiteral(")")
	_t1700 := &pb.Disjunction{Args: formulas918}
	result920 := _t1700
	p.recordSpan(int(span_start919), "Disjunction")
	return result920
}

func (p *Parser) parse_not() *pb.Not {
	span_start922 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1701 := p.parse_formula()
	formula921 := _t1701
	p.consumeLiteral(")")
	_t1702 := &pb.Not{Arg: formula921}
	result923 := _t1702
	p.recordSpan(int(span_start922), "Not")
	return result923
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start927 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1703 := p.parse_name()
	name924 := _t1703
	_t1704 := p.parse_ffi_args()
	ffi_args925 := _t1704
	_t1705 := p.parse_terms()
	terms926 := _t1705
	p.consumeLiteral(")")
	_t1706 := &pb.FFI{Name: name924, Args: ffi_args925, Terms: terms926}
	result928 := _t1706
	p.recordSpan(int(span_start927), "FFI")
	return result928
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol929 := p.consumeTerminal("SYMBOL").Value.str
	return symbol929
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs930 := []*pb.Abstraction{}
	cond931 := p.matchLookaheadLiteral("(", 0)
	for cond931 {
		_t1707 := p.parse_abstraction()
		item932 := _t1707
		xs930 = append(xs930, item932)
		cond931 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions933 := xs930
	p.consumeLiteral(")")
	return abstractions933
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start939 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1708 := p.parse_relation_id()
	relation_id934 := _t1708
	xs935 := []*pb.Term{}
	cond936 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond936 {
		_t1709 := p.parse_term()
		item937 := _t1709
		xs935 = append(xs935, item937)
		cond936 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms938 := xs935
	p.consumeLiteral(")")
	_t1710 := &pb.Atom{Name: relation_id934, Terms: terms938}
	result940 := _t1710
	p.recordSpan(int(span_start939), "Atom")
	return result940
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start946 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1711 := p.parse_name()
	name941 := _t1711
	xs942 := []*pb.Term{}
	cond943 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond943 {
		_t1712 := p.parse_term()
		item944 := _t1712
		xs942 = append(xs942, item944)
		cond943 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms945 := xs942
	p.consumeLiteral(")")
	_t1713 := &pb.Pragma{Name: name941, Terms: terms945}
	result947 := _t1713
	p.recordSpan(int(span_start946), "Pragma")
	return result947
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start963 := int64(p.spanStart())
	var _t1714 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1715 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1715 = 9
		} else {
			var _t1716 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1716 = 4
			} else {
				var _t1717 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1717 = 3
				} else {
					var _t1718 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1718 = 0
					} else {
						var _t1719 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1719 = 2
						} else {
							var _t1720 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1720 = 1
							} else {
								var _t1721 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1721 = 8
								} else {
									var _t1722 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1722 = 6
									} else {
										var _t1723 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1723 = 5
										} else {
											var _t1724 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1724 = 7
											} else {
												_t1724 = -1
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
					_t1717 = _t1718
				}
				_t1716 = _t1717
			}
			_t1715 = _t1716
		}
		_t1714 = _t1715
	} else {
		_t1714 = -1
	}
	prediction948 := _t1714
	var _t1725 *pb.Primitive
	if prediction948 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1726 := p.parse_name()
		name958 := _t1726
		xs959 := []*pb.RelTerm{}
		cond960 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond960 {
			_t1727 := p.parse_rel_term()
			item961 := _t1727
			xs959 = append(xs959, item961)
			cond960 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms962 := xs959
		p.consumeLiteral(")")
		_t1728 := &pb.Primitive{Name: name958, Terms: rel_terms962}
		_t1725 = _t1728
	} else {
		var _t1729 *pb.Primitive
		if prediction948 == 8 {
			_t1730 := p.parse_divide()
			divide957 := _t1730
			_t1729 = divide957
		} else {
			var _t1731 *pb.Primitive
			if prediction948 == 7 {
				_t1732 := p.parse_multiply()
				multiply956 := _t1732
				_t1731 = multiply956
			} else {
				var _t1733 *pb.Primitive
				if prediction948 == 6 {
					_t1734 := p.parse_minus()
					minus955 := _t1734
					_t1733 = minus955
				} else {
					var _t1735 *pb.Primitive
					if prediction948 == 5 {
						_t1736 := p.parse_add()
						add954 := _t1736
						_t1735 = add954
					} else {
						var _t1737 *pb.Primitive
						if prediction948 == 4 {
							_t1738 := p.parse_gt_eq()
							gt_eq953 := _t1738
							_t1737 = gt_eq953
						} else {
							var _t1739 *pb.Primitive
							if prediction948 == 3 {
								_t1740 := p.parse_gt()
								gt952 := _t1740
								_t1739 = gt952
							} else {
								var _t1741 *pb.Primitive
								if prediction948 == 2 {
									_t1742 := p.parse_lt_eq()
									lt_eq951 := _t1742
									_t1741 = lt_eq951
								} else {
									var _t1743 *pb.Primitive
									if prediction948 == 1 {
										_t1744 := p.parse_lt()
										lt950 := _t1744
										_t1743 = lt950
									} else {
										var _t1745 *pb.Primitive
										if prediction948 == 0 {
											_t1746 := p.parse_eq()
											eq949 := _t1746
											_t1745 = eq949
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1743 = _t1745
									}
									_t1741 = _t1743
								}
								_t1739 = _t1741
							}
							_t1737 = _t1739
						}
						_t1735 = _t1737
					}
					_t1733 = _t1735
				}
				_t1731 = _t1733
			}
			_t1729 = _t1731
		}
		_t1725 = _t1729
	}
	result964 := _t1725
	p.recordSpan(int(span_start963), "Primitive")
	return result964
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start967 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1747 := p.parse_term()
	term965 := _t1747
	_t1748 := p.parse_term()
	term_3966 := _t1748
	p.consumeLiteral(")")
	_t1749 := &pb.RelTerm{}
	_t1749.RelTermType = &pb.RelTerm_Term{Term: term965}
	_t1750 := &pb.RelTerm{}
	_t1750.RelTermType = &pb.RelTerm_Term{Term: term_3966}
	_t1751 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1749, _t1750}}
	result968 := _t1751
	p.recordSpan(int(span_start967), "Primitive")
	return result968
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start971 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1752 := p.parse_term()
	term969 := _t1752
	_t1753 := p.parse_term()
	term_3970 := _t1753
	p.consumeLiteral(")")
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term969}
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term_3970}
	_t1756 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1754, _t1755}}
	result972 := _t1756
	p.recordSpan(int(span_start971), "Primitive")
	return result972
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1757 := p.parse_term()
	term973 := _t1757
	_t1758 := p.parse_term()
	term_3974 := _t1758
	p.consumeLiteral(")")
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term973}
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term_3974}
	_t1761 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1759, _t1760}}
	result976 := _t1761
	p.recordSpan(int(span_start975), "Primitive")
	return result976
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1762 := p.parse_term()
	term977 := _t1762
	_t1763 := p.parse_term()
	term_3978 := _t1763
	p.consumeLiteral(")")
	_t1764 := &pb.RelTerm{}
	_t1764.RelTermType = &pb.RelTerm_Term{Term: term977}
	_t1765 := &pb.RelTerm{}
	_t1765.RelTermType = &pb.RelTerm_Term{Term: term_3978}
	_t1766 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1764, _t1765}}
	result980 := _t1766
	p.recordSpan(int(span_start979), "Primitive")
	return result980
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start983 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1767 := p.parse_term()
	term981 := _t1767
	_t1768 := p.parse_term()
	term_3982 := _t1768
	p.consumeLiteral(")")
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term981}
	_t1770 := &pb.RelTerm{}
	_t1770.RelTermType = &pb.RelTerm_Term{Term: term_3982}
	_t1771 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1769, _t1770}}
	result984 := _t1771
	p.recordSpan(int(span_start983), "Primitive")
	return result984
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start988 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1772 := p.parse_term()
	term985 := _t1772
	_t1773 := p.parse_term()
	term_3986 := _t1773
	_t1774 := p.parse_term()
	term_4987 := _t1774
	p.consumeLiteral(")")
	_t1775 := &pb.RelTerm{}
	_t1775.RelTermType = &pb.RelTerm_Term{Term: term985}
	_t1776 := &pb.RelTerm{}
	_t1776.RelTermType = &pb.RelTerm_Term{Term: term_3986}
	_t1777 := &pb.RelTerm{}
	_t1777.RelTermType = &pb.RelTerm_Term{Term: term_4987}
	_t1778 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1775, _t1776, _t1777}}
	result989 := _t1778
	p.recordSpan(int(span_start988), "Primitive")
	return result989
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start993 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1779 := p.parse_term()
	term990 := _t1779
	_t1780 := p.parse_term()
	term_3991 := _t1780
	_t1781 := p.parse_term()
	term_4992 := _t1781
	p.consumeLiteral(")")
	_t1782 := &pb.RelTerm{}
	_t1782.RelTermType = &pb.RelTerm_Term{Term: term990}
	_t1783 := &pb.RelTerm{}
	_t1783.RelTermType = &pb.RelTerm_Term{Term: term_3991}
	_t1784 := &pb.RelTerm{}
	_t1784.RelTermType = &pb.RelTerm_Term{Term: term_4992}
	_t1785 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1782, _t1783, _t1784}}
	result994 := _t1785
	p.recordSpan(int(span_start993), "Primitive")
	return result994
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start998 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1786 := p.parse_term()
	term995 := _t1786
	_t1787 := p.parse_term()
	term_3996 := _t1787
	_t1788 := p.parse_term()
	term_4997 := _t1788
	p.consumeLiteral(")")
	_t1789 := &pb.RelTerm{}
	_t1789.RelTermType = &pb.RelTerm_Term{Term: term995}
	_t1790 := &pb.RelTerm{}
	_t1790.RelTermType = &pb.RelTerm_Term{Term: term_3996}
	_t1791 := &pb.RelTerm{}
	_t1791.RelTermType = &pb.RelTerm_Term{Term: term_4997}
	_t1792 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1789, _t1790, _t1791}}
	result999 := _t1792
	p.recordSpan(int(span_start998), "Primitive")
	return result999
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1003 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1793 := p.parse_term()
	term1000 := _t1793
	_t1794 := p.parse_term()
	term_31001 := _t1794
	_t1795 := p.parse_term()
	term_41002 := _t1795
	p.consumeLiteral(")")
	_t1796 := &pb.RelTerm{}
	_t1796.RelTermType = &pb.RelTerm_Term{Term: term1000}
	_t1797 := &pb.RelTerm{}
	_t1797.RelTermType = &pb.RelTerm_Term{Term: term_31001}
	_t1798 := &pb.RelTerm{}
	_t1798.RelTermType = &pb.RelTerm_Term{Term: term_41002}
	_t1799 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1796, _t1797, _t1798}}
	result1004 := _t1799
	p.recordSpan(int(span_start1003), "Primitive")
	return result1004
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1008 := int64(p.spanStart())
	var _t1800 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1800 = 1
	} else {
		var _t1801 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1801 = 1
		} else {
			var _t1802 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1802 = 1
			} else {
				var _t1803 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1803 = 1
				} else {
					var _t1804 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1804 = 0
					} else {
						var _t1805 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1805 = 1
						} else {
							var _t1806 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1806 = 1
							} else {
								var _t1807 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1807 = 1
								} else {
									var _t1808 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1808 = 1
									} else {
										var _t1809 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1809 = 1
										} else {
											var _t1810 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1810 = 1
											} else {
												var _t1811 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1811 = 1
												} else {
													var _t1812 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1812 = 1
													} else {
														var _t1813 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1813 = 1
														} else {
															var _t1814 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1814 = 1
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
					}
					_t1803 = _t1804
				}
				_t1802 = _t1803
			}
			_t1801 = _t1802
		}
		_t1800 = _t1801
	}
	prediction1005 := _t1800
	var _t1815 *pb.RelTerm
	if prediction1005 == 1 {
		_t1816 := p.parse_term()
		term1007 := _t1816
		_t1817 := &pb.RelTerm{}
		_t1817.RelTermType = &pb.RelTerm_Term{Term: term1007}
		_t1815 = _t1817
	} else {
		var _t1818 *pb.RelTerm
		if prediction1005 == 0 {
			_t1819 := p.parse_specialized_value()
			specialized_value1006 := _t1819
			_t1820 := &pb.RelTerm{}
			_t1820.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1006}
			_t1818 = _t1820
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1815 = _t1818
	}
	result1009 := _t1815
	p.recordSpan(int(span_start1008), "RelTerm")
	return result1009
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1011 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1821 := p.parse_raw_value()
	raw_value1010 := _t1821
	result1012 := raw_value1010
	p.recordSpan(int(span_start1011), "Value")
	return result1012
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1822 := p.parse_name()
	name1013 := _t1822
	xs1014 := []*pb.RelTerm{}
	cond1015 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1015 {
		_t1823 := p.parse_rel_term()
		item1016 := _t1823
		xs1014 = append(xs1014, item1016)
		cond1015 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1017 := xs1014
	p.consumeLiteral(")")
	_t1824 := &pb.RelAtom{Name: name1013, Terms: rel_terms1017}
	result1019 := _t1824
	p.recordSpan(int(span_start1018), "RelAtom")
	return result1019
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1825 := p.parse_term()
	term1020 := _t1825
	_t1826 := p.parse_term()
	term_31021 := _t1826
	p.consumeLiteral(")")
	_t1827 := &pb.Cast{Input: term1020, Result: term_31021}
	result1023 := _t1827
	p.recordSpan(int(span_start1022), "Cast")
	return result1023
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1024 := []*pb.Attribute{}
	cond1025 := p.matchLookaheadLiteral("(", 0)
	for cond1025 {
		_t1828 := p.parse_attribute()
		item1026 := _t1828
		xs1024 = append(xs1024, item1026)
		cond1025 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1027 := xs1024
	p.consumeLiteral(")")
	return attributes1027
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1033 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1829 := p.parse_name()
	name1028 := _t1829
	xs1029 := []*pb.Value{}
	cond1030 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1030 {
		_t1830 := p.parse_raw_value()
		item1031 := _t1830
		xs1029 = append(xs1029, item1031)
		cond1030 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1032 := xs1029
	p.consumeLiteral(")")
	_t1831 := &pb.Attribute{Name: name1028, Args: raw_values1032}
	result1034 := _t1831
	p.recordSpan(int(span_start1033), "Attribute")
	return result1034
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1041 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1035 := []*pb.RelationId{}
	cond1036 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1036 {
		_t1832 := p.parse_relation_id()
		item1037 := _t1832
		xs1035 = append(xs1035, item1037)
		cond1036 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1038 := xs1035
	_t1833 := p.parse_script()
	script1039 := _t1833
	var _t1834 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1835 := p.parse_attrs()
		_t1834 = _t1835
	}
	attrs1040 := _t1834
	p.consumeLiteral(")")
	_t1836 := attrs1040
	if attrs1040 == nil {
		_t1836 = []*pb.Attribute{}
	}
	_t1837 := &pb.Algorithm{Global: relation_ids1038, Body: script1039, Attrs: _t1836}
	result1042 := _t1837
	p.recordSpan(int(span_start1041), "Algorithm")
	return result1042
}

func (p *Parser) parse_script() *pb.Script {
	span_start1047 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1043 := []*pb.Construct{}
	cond1044 := p.matchLookaheadLiteral("(", 0)
	for cond1044 {
		_t1838 := p.parse_construct()
		item1045 := _t1838
		xs1043 = append(xs1043, item1045)
		cond1044 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1046 := xs1043
	p.consumeLiteral(")")
	_t1839 := &pb.Script{Constructs: constructs1046}
	result1048 := _t1839
	p.recordSpan(int(span_start1047), "Script")
	return result1048
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1052 := int64(p.spanStart())
	var _t1840 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1841 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1841 = 1
		} else {
			var _t1842 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1842 = 1
			} else {
				var _t1843 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1843 = 1
				} else {
					var _t1844 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1844 = 0
					} else {
						var _t1845 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1845 = 1
						} else {
							var _t1846 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1846 = 1
							} else {
								_t1846 = -1
							}
							_t1845 = _t1846
						}
						_t1844 = _t1845
					}
					_t1843 = _t1844
				}
				_t1842 = _t1843
			}
			_t1841 = _t1842
		}
		_t1840 = _t1841
	} else {
		_t1840 = -1
	}
	prediction1049 := _t1840
	var _t1847 *pb.Construct
	if prediction1049 == 1 {
		_t1848 := p.parse_instruction()
		instruction1051 := _t1848
		_t1849 := &pb.Construct{}
		_t1849.ConstructType = &pb.Construct_Instruction{Instruction: instruction1051}
		_t1847 = _t1849
	} else {
		var _t1850 *pb.Construct
		if prediction1049 == 0 {
			_t1851 := p.parse_loop()
			loop1050 := _t1851
			_t1852 := &pb.Construct{}
			_t1852.ConstructType = &pb.Construct_Loop{Loop: loop1050}
			_t1850 = _t1852
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1847 = _t1850
	}
	result1053 := _t1847
	p.recordSpan(int(span_start1052), "Construct")
	return result1053
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1057 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1853 := p.parse_init()
	init1054 := _t1853
	_t1854 := p.parse_script()
	script1055 := _t1854
	var _t1855 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1856 := p.parse_attrs()
		_t1855 = _t1856
	}
	attrs1056 := _t1855
	p.consumeLiteral(")")
	_t1857 := attrs1056
	if attrs1056 == nil {
		_t1857 = []*pb.Attribute{}
	}
	_t1858 := &pb.Loop{Init: init1054, Body: script1055, Attrs: _t1857}
	result1058 := _t1858
	p.recordSpan(int(span_start1057), "Loop")
	return result1058
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1059 := []*pb.Instruction{}
	cond1060 := p.matchLookaheadLiteral("(", 0)
	for cond1060 {
		_t1859 := p.parse_instruction()
		item1061 := _t1859
		xs1059 = append(xs1059, item1061)
		cond1060 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1062 := xs1059
	p.consumeLiteral(")")
	return instructions1062
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1069 := int64(p.spanStart())
	var _t1860 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1861 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1861 = 1
		} else {
			var _t1862 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1862 = 4
			} else {
				var _t1863 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1863 = 3
				} else {
					var _t1864 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1864 = 2
					} else {
						var _t1865 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1865 = 0
						} else {
							_t1865 = -1
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
	} else {
		_t1860 = -1
	}
	prediction1063 := _t1860
	var _t1866 *pb.Instruction
	if prediction1063 == 4 {
		_t1867 := p.parse_monus_def()
		monus_def1068 := _t1867
		_t1868 := &pb.Instruction{}
		_t1868.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1068}
		_t1866 = _t1868
	} else {
		var _t1869 *pb.Instruction
		if prediction1063 == 3 {
			_t1870 := p.parse_monoid_def()
			monoid_def1067 := _t1870
			_t1871 := &pb.Instruction{}
			_t1871.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1067}
			_t1869 = _t1871
		} else {
			var _t1872 *pb.Instruction
			if prediction1063 == 2 {
				_t1873 := p.parse_break()
				break1066 := _t1873
				_t1874 := &pb.Instruction{}
				_t1874.InstrType = &pb.Instruction_Break{Break: break1066}
				_t1872 = _t1874
			} else {
				var _t1875 *pb.Instruction
				if prediction1063 == 1 {
					_t1876 := p.parse_upsert()
					upsert1065 := _t1876
					_t1877 := &pb.Instruction{}
					_t1877.InstrType = &pb.Instruction_Upsert{Upsert: upsert1065}
					_t1875 = _t1877
				} else {
					var _t1878 *pb.Instruction
					if prediction1063 == 0 {
						_t1879 := p.parse_assign()
						assign1064 := _t1879
						_t1880 := &pb.Instruction{}
						_t1880.InstrType = &pb.Instruction_Assign{Assign: assign1064}
						_t1878 = _t1880
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1875 = _t1878
				}
				_t1872 = _t1875
			}
			_t1869 = _t1872
		}
		_t1866 = _t1869
	}
	result1070 := _t1866
	p.recordSpan(int(span_start1069), "Instruction")
	return result1070
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1881 := p.parse_relation_id()
	relation_id1071 := _t1881
	_t1882 := p.parse_abstraction()
	abstraction1072 := _t1882
	var _t1883 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1884 := p.parse_attrs()
		_t1883 = _t1884
	}
	attrs1073 := _t1883
	p.consumeLiteral(")")
	_t1885 := attrs1073
	if attrs1073 == nil {
		_t1885 = []*pb.Attribute{}
	}
	_t1886 := &pb.Assign{Name: relation_id1071, Body: abstraction1072, Attrs: _t1885}
	result1075 := _t1886
	p.recordSpan(int(span_start1074), "Assign")
	return result1075
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1079 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1887 := p.parse_relation_id()
	relation_id1076 := _t1887
	_t1888 := p.parse_abstraction_with_arity()
	abstraction_with_arity1077 := _t1888
	var _t1889 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1890 := p.parse_attrs()
		_t1889 = _t1890
	}
	attrs1078 := _t1889
	p.consumeLiteral(")")
	_t1891 := attrs1078
	if attrs1078 == nil {
		_t1891 = []*pb.Attribute{}
	}
	_t1892 := &pb.Upsert{Name: relation_id1076, Body: abstraction_with_arity1077[0].(*pb.Abstraction), Attrs: _t1891, ValueArity: abstraction_with_arity1077[1].(int64)}
	result1080 := _t1892
	p.recordSpan(int(span_start1079), "Upsert")
	return result1080
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1893 := p.parse_bindings()
	bindings1081 := _t1893
	_t1894 := p.parse_formula()
	formula1082 := _t1894
	p.consumeLiteral(")")
	_t1895 := &pb.Abstraction{Vars: listConcat(bindings1081[0].([]*pb.Binding), bindings1081[1].([]*pb.Binding)), Value: formula1082}
	return []interface{}{_t1895, int64(len(bindings1081[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1896 := p.parse_relation_id()
	relation_id1083 := _t1896
	_t1897 := p.parse_abstraction()
	abstraction1084 := _t1897
	var _t1898 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1899 := p.parse_attrs()
		_t1898 = _t1899
	}
	attrs1085 := _t1898
	p.consumeLiteral(")")
	_t1900 := attrs1085
	if attrs1085 == nil {
		_t1900 = []*pb.Attribute{}
	}
	_t1901 := &pb.Break{Name: relation_id1083, Body: abstraction1084, Attrs: _t1900}
	result1087 := _t1901
	p.recordSpan(int(span_start1086), "Break")
	return result1087
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1092 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1902 := p.parse_monoid()
	monoid1088 := _t1902
	_t1903 := p.parse_relation_id()
	relation_id1089 := _t1903
	_t1904 := p.parse_abstraction_with_arity()
	abstraction_with_arity1090 := _t1904
	var _t1905 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1906 := p.parse_attrs()
		_t1905 = _t1906
	}
	attrs1091 := _t1905
	p.consumeLiteral(")")
	_t1907 := attrs1091
	if attrs1091 == nil {
		_t1907 = []*pb.Attribute{}
	}
	_t1908 := &pb.MonoidDef{Monoid: monoid1088, Name: relation_id1089, Body: abstraction_with_arity1090[0].(*pb.Abstraction), Attrs: _t1907, ValueArity: abstraction_with_arity1090[1].(int64)}
	result1093 := _t1908
	p.recordSpan(int(span_start1092), "MonoidDef")
	return result1093
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1099 := int64(p.spanStart())
	var _t1909 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1910 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1910 = 3
		} else {
			var _t1911 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1911 = 0
			} else {
				var _t1912 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1912 = 1
				} else {
					var _t1913 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1913 = 2
					} else {
						_t1913 = -1
					}
					_t1912 = _t1913
				}
				_t1911 = _t1912
			}
			_t1910 = _t1911
		}
		_t1909 = _t1910
	} else {
		_t1909 = -1
	}
	prediction1094 := _t1909
	var _t1914 *pb.Monoid
	if prediction1094 == 3 {
		_t1915 := p.parse_sum_monoid()
		sum_monoid1098 := _t1915
		_t1916 := &pb.Monoid{}
		_t1916.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1098}
		_t1914 = _t1916
	} else {
		var _t1917 *pb.Monoid
		if prediction1094 == 2 {
			_t1918 := p.parse_max_monoid()
			max_monoid1097 := _t1918
			_t1919 := &pb.Monoid{}
			_t1919.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1097}
			_t1917 = _t1919
		} else {
			var _t1920 *pb.Monoid
			if prediction1094 == 1 {
				_t1921 := p.parse_min_monoid()
				min_monoid1096 := _t1921
				_t1922 := &pb.Monoid{}
				_t1922.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1096}
				_t1920 = _t1922
			} else {
				var _t1923 *pb.Monoid
				if prediction1094 == 0 {
					_t1924 := p.parse_or_monoid()
					or_monoid1095 := _t1924
					_t1925 := &pb.Monoid{}
					_t1925.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1095}
					_t1923 = _t1925
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1920 = _t1923
			}
			_t1917 = _t1920
		}
		_t1914 = _t1917
	}
	result1100 := _t1914
	p.recordSpan(int(span_start1099), "Monoid")
	return result1100
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1101 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1926 := &pb.OrMonoid{}
	result1102 := _t1926
	p.recordSpan(int(span_start1101), "OrMonoid")
	return result1102
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1927 := p.parse_type()
	type1103 := _t1927
	p.consumeLiteral(")")
	_t1928 := &pb.MinMonoid{Type: type1103}
	result1105 := _t1928
	p.recordSpan(int(span_start1104), "MinMonoid")
	return result1105
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1929 := p.parse_type()
	type1106 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.MaxMonoid{Type: type1106}
	result1108 := _t1930
	p.recordSpan(int(span_start1107), "MaxMonoid")
	return result1108
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1110 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1931 := p.parse_type()
	type1109 := _t1931
	p.consumeLiteral(")")
	_t1932 := &pb.SumMonoid{Type: type1109}
	result1111 := _t1932
	p.recordSpan(int(span_start1110), "SumMonoid")
	return result1111
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1116 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1933 := p.parse_monoid()
	monoid1112 := _t1933
	_t1934 := p.parse_relation_id()
	relation_id1113 := _t1934
	_t1935 := p.parse_abstraction_with_arity()
	abstraction_with_arity1114 := _t1935
	var _t1936 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1937 := p.parse_attrs()
		_t1936 = _t1937
	}
	attrs1115 := _t1936
	p.consumeLiteral(")")
	_t1938 := attrs1115
	if attrs1115 == nil {
		_t1938 = []*pb.Attribute{}
	}
	_t1939 := &pb.MonusDef{Monoid: monoid1112, Name: relation_id1113, Body: abstraction_with_arity1114[0].(*pb.Abstraction), Attrs: _t1938, ValueArity: abstraction_with_arity1114[1].(int64)}
	result1117 := _t1939
	p.recordSpan(int(span_start1116), "MonusDef")
	return result1117
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1122 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1940 := p.parse_relation_id()
	relation_id1118 := _t1940
	_t1941 := p.parse_abstraction()
	abstraction1119 := _t1941
	_t1942 := p.parse_functional_dependency_keys()
	functional_dependency_keys1120 := _t1942
	_t1943 := p.parse_functional_dependency_values()
	functional_dependency_values1121 := _t1943
	p.consumeLiteral(")")
	_t1944 := &pb.FunctionalDependency{Guard: abstraction1119, Keys: functional_dependency_keys1120, Values: functional_dependency_values1121}
	_t1945 := &pb.Constraint{Name: relation_id1118}
	_t1945.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1944}
	result1123 := _t1945
	p.recordSpan(int(span_start1122), "Constraint")
	return result1123
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1124 := []*pb.Var{}
	cond1125 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1125 {
		_t1946 := p.parse_var()
		item1126 := _t1946
		xs1124 = append(xs1124, item1126)
		cond1125 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1127 := xs1124
	p.consumeLiteral(")")
	return vars1127
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1128 := []*pb.Var{}
	cond1129 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1129 {
		_t1947 := p.parse_var()
		item1130 := _t1947
		xs1128 = append(xs1128, item1130)
		cond1129 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1131 := xs1128
	p.consumeLiteral(")")
	return vars1131
}

func (p *Parser) parse_data() *pb.Data {
	span_start1137 := int64(p.spanStart())
	var _t1948 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1949 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1949 = 3
		} else {
			var _t1950 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1950 = 0
			} else {
				var _t1951 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1951 = 2
				} else {
					var _t1952 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1952 = 1
					} else {
						_t1952 = -1
					}
					_t1951 = _t1952
				}
				_t1950 = _t1951
			}
			_t1949 = _t1950
		}
		_t1948 = _t1949
	} else {
		_t1948 = -1
	}
	prediction1132 := _t1948
	var _t1953 *pb.Data
	if prediction1132 == 3 {
		_t1954 := p.parse_iceberg_data()
		iceberg_data1136 := _t1954
		_t1955 := &pb.Data{}
		_t1955.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1136}
		_t1953 = _t1955
	} else {
		var _t1956 *pb.Data
		if prediction1132 == 2 {
			_t1957 := p.parse_csv_data()
			csv_data1135 := _t1957
			_t1958 := &pb.Data{}
			_t1958.DataType = &pb.Data_CsvData{CsvData: csv_data1135}
			_t1956 = _t1958
		} else {
			var _t1959 *pb.Data
			if prediction1132 == 1 {
				_t1960 := p.parse_betree_relation()
				betree_relation1134 := _t1960
				_t1961 := &pb.Data{}
				_t1961.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1134}
				_t1959 = _t1961
			} else {
				var _t1962 *pb.Data
				if prediction1132 == 0 {
					_t1963 := p.parse_edb()
					edb1133 := _t1963
					_t1964 := &pb.Data{}
					_t1964.DataType = &pb.Data_Edb{Edb: edb1133}
					_t1962 = _t1964
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1959 = _t1962
			}
			_t1956 = _t1959
		}
		_t1953 = _t1956
	}
	result1138 := _t1953
	p.recordSpan(int(span_start1137), "Data")
	return result1138
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1142 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1965 := p.parse_relation_id()
	relation_id1139 := _t1965
	_t1966 := p.parse_edb_path()
	edb_path1140 := _t1966
	_t1967 := p.parse_edb_types()
	edb_types1141 := _t1967
	p.consumeLiteral(")")
	_t1968 := &pb.EDB{TargetId: relation_id1139, Path: edb_path1140, Types: edb_types1141}
	result1143 := _t1968
	p.recordSpan(int(span_start1142), "EDB")
	return result1143
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1144 := []string{}
	cond1145 := p.matchLookaheadTerminal("STRING", 0)
	for cond1145 {
		item1146 := p.consumeTerminal("STRING").Value.str
		xs1144 = append(xs1144, item1146)
		cond1145 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1147 := xs1144
	p.consumeLiteral("]")
	return strings1147
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1148 := []*pb.Type{}
	cond1149 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1149 {
		_t1969 := p.parse_type()
		item1150 := _t1969
		xs1148 = append(xs1148, item1150)
		cond1149 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1151 := xs1148
	p.consumeLiteral("]")
	return types1151
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1154 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1970 := p.parse_relation_id()
	relation_id1152 := _t1970
	_t1971 := p.parse_betree_info()
	betree_info1153 := _t1971
	p.consumeLiteral(")")
	_t1972 := &pb.BeTreeRelation{Name: relation_id1152, RelationInfo: betree_info1153}
	result1155 := _t1972
	p.recordSpan(int(span_start1154), "BeTreeRelation")
	return result1155
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1159 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1973 := p.parse_betree_info_key_types()
	betree_info_key_types1156 := _t1973
	_t1974 := p.parse_betree_info_value_types()
	betree_info_value_types1157 := _t1974
	_t1975 := p.parse_config_dict()
	config_dict1158 := _t1975
	p.consumeLiteral(")")
	_t1976 := p.construct_betree_info(betree_info_key_types1156, betree_info_value_types1157, config_dict1158)
	result1160 := _t1976
	p.recordSpan(int(span_start1159), "BeTreeInfo")
	return result1160
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1161 := []*pb.Type{}
	cond1162 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1162 {
		_t1977 := p.parse_type()
		item1163 := _t1977
		xs1161 = append(xs1161, item1163)
		cond1162 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1164 := xs1161
	p.consumeLiteral(")")
	return types1164
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1165 := []*pb.Type{}
	cond1166 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1166 {
		_t1978 := p.parse_type()
		item1167 := _t1978
		xs1165 = append(xs1165, item1167)
		cond1166 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1168 := xs1165
	p.consumeLiteral(")")
	return types1168
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1173 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1979 := p.parse_csvlocator()
	csvlocator1169 := _t1979
	_t1980 := p.parse_csv_config()
	csv_config1170 := _t1980
	_t1981 := p.parse_gnf_columns()
	gnf_columns1171 := _t1981
	_t1982 := p.parse_csv_asof()
	csv_asof1172 := _t1982
	p.consumeLiteral(")")
	_t1983 := &pb.CSVData{Locator: csvlocator1169, Config: csv_config1170, Columns: gnf_columns1171, Asof: csv_asof1172}
	result1174 := _t1983
	p.recordSpan(int(span_start1173), "CSVData")
	return result1174
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1177 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1984 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1985 := p.parse_csv_locator_paths()
		_t1984 = _t1985
	}
	csv_locator_paths1175 := _t1984
	var _t1986 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1987 := p.parse_csv_locator_inline_data()
		_t1986 = ptr(_t1987)
	}
	csv_locator_inline_data1176 := _t1986
	p.consumeLiteral(")")
	_t1988 := csv_locator_paths1175
	if csv_locator_paths1175 == nil {
		_t1988 = []string{}
	}
	_t1989 := &pb.CSVLocator{Paths: _t1988, InlineData: []byte(deref(csv_locator_inline_data1176, ""))}
	result1178 := _t1989
	p.recordSpan(int(span_start1177), "CSVLocator")
	return result1178
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1179 := []string{}
	cond1180 := p.matchLookaheadTerminal("STRING", 0)
	for cond1180 {
		item1181 := p.consumeTerminal("STRING").Value.str
		xs1179 = append(xs1179, item1181)
		cond1180 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1182 := xs1179
	p.consumeLiteral(")")
	return strings1182
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1183 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1183
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1185 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1990 := p.parse_config_dict()
	config_dict1184 := _t1990
	p.consumeLiteral(")")
	_t1991 := p.construct_csv_config(config_dict1184)
	result1186 := _t1991
	p.recordSpan(int(span_start1185), "CSVConfig")
	return result1186
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1187 := []*pb.GNFColumn{}
	cond1188 := p.matchLookaheadLiteral("(", 0)
	for cond1188 {
		_t1992 := p.parse_gnf_column()
		item1189 := _t1992
		xs1187 = append(xs1187, item1189)
		cond1188 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1190 := xs1187
	p.consumeLiteral(")")
	return gnf_columns1190
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1197 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1993 := p.parse_gnf_column_path()
	gnf_column_path1191 := _t1993
	var _t1994 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1995 := p.parse_relation_id()
		_t1994 = _t1995
	}
	relation_id1192 := _t1994
	p.consumeLiteral("[")
	xs1193 := []*pb.Type{}
	cond1194 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1194 {
		_t1996 := p.parse_type()
		item1195 := _t1996
		xs1193 = append(xs1193, item1195)
		cond1194 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1196 := xs1193
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1997 := &pb.GNFColumn{ColumnPath: gnf_column_path1191, TargetId: relation_id1192, Types: types1196}
	result1198 := _t1997
	p.recordSpan(int(span_start1197), "GNFColumn")
	return result1198
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1998 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1998 = 1
	} else {
		var _t1999 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1999 = 0
		} else {
			_t1999 = -1
		}
		_t1998 = _t1999
	}
	prediction1199 := _t1998
	var _t2000 []string
	if prediction1199 == 1 {
		p.consumeLiteral("[")
		xs1201 := []string{}
		cond1202 := p.matchLookaheadTerminal("STRING", 0)
		for cond1202 {
			item1203 := p.consumeTerminal("STRING").Value.str
			xs1201 = append(xs1201, item1203)
			cond1202 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1204 := xs1201
		p.consumeLiteral("]")
		_t2000 = strings1204
	} else {
		var _t2001 []string
		if prediction1199 == 0 {
			string1200 := p.consumeTerminal("STRING").Value.str
			_ = string1200
			_t2001 = []string{string1200}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2000 = _t2001
	}
	return _t2000
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1205 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1205
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2002 := p.parse_iceberg_locator()
	iceberg_locator1206 := _t2002
	_t2003 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1207 := _t2003
	_t2004 := p.parse_gnf_columns()
	gnf_columns1208 := _t2004
	var _t2005 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2006 := p.parse_iceberg_from_snapshot()
		_t2005 = ptr(_t2006)
	}
	iceberg_from_snapshot1209 := _t2005
	var _t2007 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2008 := p.parse_iceberg_to_snapshot()
		_t2007 = ptr(_t2008)
	}
	iceberg_to_snapshot1210 := _t2007
	_t2009 := p.parse_boolean_value()
	boolean_value1211 := _t2009
	p.consumeLiteral(")")
	_t2010 := p.construct_iceberg_data(iceberg_locator1206, iceberg_catalog_config1207, gnf_columns1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
	result1213 := _t2010
	p.recordSpan(int(span_start1212), "IcebergData")
	return result1213
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1217 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2011 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1214 := _t2011
	_t2012 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1215 := _t2012
	_t2013 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1216 := _t2013
	p.consumeLiteral(")")
	_t2014 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1214, Namespace: iceberg_locator_namespace1215, Warehouse: iceberg_locator_warehouse1216}
	result1218 := _t2014
	p.recordSpan(int(span_start1217), "IcebergLocator")
	return result1218
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1219 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1219
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1220 := []string{}
	cond1221 := p.matchLookaheadTerminal("STRING", 0)
	for cond1221 {
		item1222 := p.consumeTerminal("STRING").Value.str
		xs1220 = append(xs1220, item1222)
		cond1221 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1223 := xs1220
	p.consumeLiteral(")")
	return strings1223
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1224 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1224
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1229 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2015 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1225 := _t2015
	var _t2016 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2017 := p.parse_iceberg_catalog_config_scope()
		_t2016 = ptr(_t2017)
	}
	iceberg_catalog_config_scope1226 := _t2016
	_t2018 := p.parse_iceberg_properties()
	iceberg_properties1227 := _t2018
	_t2019 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1228 := _t2019
	p.consumeLiteral(")")
	_t2020 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
	result1230 := _t2020
	p.recordSpan(int(span_start1229), "IcebergCatalogConfig")
	return result1230
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1231 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1231
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1232 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1232
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1233 := [][]interface{}{}
	cond1234 := p.matchLookaheadLiteral("(", 0)
	for cond1234 {
		_t2021 := p.parse_iceberg_property_entry()
		item1235 := _t2021
		xs1233 = append(xs1233, item1235)
		cond1234 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1236 := xs1233
	p.consumeLiteral(")")
	return iceberg_property_entrys1236
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1237 := p.consumeTerminal("STRING").Value.str
	string_31238 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1237, string_31238}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1239 := [][]interface{}{}
	cond1240 := p.matchLookaheadLiteral("(", 0)
	for cond1240 {
		_t2022 := p.parse_iceberg_masked_property_entry()
		item1241 := _t2022
		xs1239 = append(xs1239, item1241)
		cond1240 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1242 := xs1239
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1242
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1243 := p.consumeTerminal("STRING").Value.str
	string_31244 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1243, string_31244}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1245 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1245
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1246 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1246
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1248 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2023 := p.parse_fragment_id()
	fragment_id1247 := _t2023
	p.consumeLiteral(")")
	_t2024 := &pb.Undefine{FragmentId: fragment_id1247}
	result1249 := _t2024
	p.recordSpan(int(span_start1248), "Undefine")
	return result1249
}

func (p *Parser) parse_context() *pb.Context {
	span_start1254 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1250 := []*pb.RelationId{}
	cond1251 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1251 {
		_t2025 := p.parse_relation_id()
		item1252 := _t2025
		xs1250 = append(xs1250, item1252)
		cond1251 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1253 := xs1250
	p.consumeLiteral(")")
	_t2026 := &pb.Context{Relations: relation_ids1253}
	result1255 := _t2026
	p.recordSpan(int(span_start1254), "Context")
	return result1255
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1261 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2027 := p.parse_edb_path()
	edb_path1256 := _t2027
	xs1257 := []*pb.SnapshotMapping{}
	cond1258 := p.matchLookaheadLiteral("[", 0)
	for cond1258 {
		_t2028 := p.parse_snapshot_mapping()
		item1259 := _t2028
		xs1257 = append(xs1257, item1259)
		cond1258 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1260 := xs1257
	p.consumeLiteral(")")
	_t2029 := &pb.Snapshot{Prefix: edb_path1256, Mappings: snapshot_mappings1260}
	result1262 := _t2029
	p.recordSpan(int(span_start1261), "Snapshot")
	return result1262
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1265 := int64(p.spanStart())
	_t2030 := p.parse_edb_path()
	edb_path1263 := _t2030
	_t2031 := p.parse_relation_id()
	relation_id1264 := _t2031
	_t2032 := &pb.SnapshotMapping{DestinationPath: edb_path1263, SourceRelation: relation_id1264}
	result1266 := _t2032
	p.recordSpan(int(span_start1265), "SnapshotMapping")
	return result1266
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1267 := []*pb.Read{}
	cond1268 := p.matchLookaheadLiteral("(", 0)
	for cond1268 {
		_t2033 := p.parse_read()
		item1269 := _t2033
		xs1267 = append(xs1267, item1269)
		cond1268 = p.matchLookaheadLiteral("(", 0)
	}
	reads1270 := xs1267
	p.consumeLiteral(")")
	return reads1270
}

func (p *Parser) parse_read() *pb.Read {
	span_start1277 := int64(p.spanStart())
	var _t2034 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2035 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2035 = 2
		} else {
			var _t2036 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2036 = 1
			} else {
				var _t2037 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2037 = 4
				} else {
					var _t2038 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2038 = 4
					} else {
						var _t2039 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2039 = 0
						} else {
							var _t2040 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2040 = 3
							} else {
								_t2040 = -1
							}
							_t2039 = _t2040
						}
						_t2038 = _t2039
					}
					_t2037 = _t2038
				}
				_t2036 = _t2037
			}
			_t2035 = _t2036
		}
		_t2034 = _t2035
	} else {
		_t2034 = -1
	}
	prediction1271 := _t2034
	var _t2041 *pb.Read
	if prediction1271 == 4 {
		_t2042 := p.parse_export()
		export1276 := _t2042
		_t2043 := &pb.Read{}
		_t2043.ReadType = &pb.Read_Export{Export: export1276}
		_t2041 = _t2043
	} else {
		var _t2044 *pb.Read
		if prediction1271 == 3 {
			_t2045 := p.parse_abort()
			abort1275 := _t2045
			_t2046 := &pb.Read{}
			_t2046.ReadType = &pb.Read_Abort{Abort: abort1275}
			_t2044 = _t2046
		} else {
			var _t2047 *pb.Read
			if prediction1271 == 2 {
				_t2048 := p.parse_what_if()
				what_if1274 := _t2048
				_t2049 := &pb.Read{}
				_t2049.ReadType = &pb.Read_WhatIf{WhatIf: what_if1274}
				_t2047 = _t2049
			} else {
				var _t2050 *pb.Read
				if prediction1271 == 1 {
					_t2051 := p.parse_output()
					output1273 := _t2051
					_t2052 := &pb.Read{}
					_t2052.ReadType = &pb.Read_Output{Output: output1273}
					_t2050 = _t2052
				} else {
					var _t2053 *pb.Read
					if prediction1271 == 0 {
						_t2054 := p.parse_demand()
						demand1272 := _t2054
						_t2055 := &pb.Read{}
						_t2055.ReadType = &pb.Read_Demand{Demand: demand1272}
						_t2053 = _t2055
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2050 = _t2053
				}
				_t2047 = _t2050
			}
			_t2044 = _t2047
		}
		_t2041 = _t2044
	}
	result1278 := _t2041
	p.recordSpan(int(span_start1277), "Read")
	return result1278
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1280 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2056 := p.parse_relation_id()
	relation_id1279 := _t2056
	p.consumeLiteral(")")
	_t2057 := &pb.Demand{RelationId: relation_id1279}
	result1281 := _t2057
	p.recordSpan(int(span_start1280), "Demand")
	return result1281
}

func (p *Parser) parse_output() *pb.Output {
	span_start1284 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2058 := p.parse_name()
	name1282 := _t2058
	_t2059 := p.parse_relation_id()
	relation_id1283 := _t2059
	p.consumeLiteral(")")
	_t2060 := &pb.Output{Name: name1282, RelationId: relation_id1283}
	result1285 := _t2060
	p.recordSpan(int(span_start1284), "Output")
	return result1285
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1288 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2061 := p.parse_name()
	name1286 := _t2061
	_t2062 := p.parse_epoch()
	epoch1287 := _t2062
	p.consumeLiteral(")")
	_t2063 := &pb.WhatIf{Branch: name1286, Epoch: epoch1287}
	result1289 := _t2063
	p.recordSpan(int(span_start1288), "WhatIf")
	return result1289
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1292 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2064 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2065 := p.parse_name()
		_t2064 = ptr(_t2065)
	}
	name1290 := _t2064
	_t2066 := p.parse_relation_id()
	relation_id1291 := _t2066
	p.consumeLiteral(")")
	_t2067 := &pb.Abort{Name: deref(name1290, "abort"), RelationId: relation_id1291}
	result1293 := _t2067
	p.recordSpan(int(span_start1292), "Abort")
	return result1293
}

func (p *Parser) parse_export() *pb.Export {
	span_start1297 := int64(p.spanStart())
	var _t2068 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2069 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2069 = 1
		} else {
			var _t2070 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2070 = 0
			} else {
				_t2070 = -1
			}
			_t2069 = _t2070
		}
		_t2068 = _t2069
	} else {
		_t2068 = -1
	}
	prediction1294 := _t2068
	var _t2071 *pb.Export
	if prediction1294 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2072 := p.parse_export_iceberg_config()
		export_iceberg_config1296 := _t2072
		p.consumeLiteral(")")
		_t2073 := &pb.Export{}
		_t2073.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1296}
		_t2071 = _t2073
	} else {
		var _t2074 *pb.Export
		if prediction1294 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2075 := p.parse_export_csv_config()
			export_csv_config1295 := _t2075
			p.consumeLiteral(")")
			_t2076 := &pb.Export{}
			_t2076.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1295}
			_t2074 = _t2076
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2071 = _t2074
	}
	result1298 := _t2071
	p.recordSpan(int(span_start1297), "Export")
	return result1298
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1306 := int64(p.spanStart())
	var _t2077 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2078 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2078 = 0
		} else {
			var _t2079 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2079 = 1
			} else {
				_t2079 = -1
			}
			_t2078 = _t2079
		}
		_t2077 = _t2078
	} else {
		_t2077 = -1
	}
	prediction1299 := _t2077
	var _t2080 *pb.ExportCSVConfig
	if prediction1299 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2081 := p.parse_export_csv_path()
		export_csv_path1303 := _t2081
		_t2082 := p.parse_export_csv_columns_list()
		export_csv_columns_list1304 := _t2082
		_t2083 := p.parse_config_dict()
		config_dict1305 := _t2083
		p.consumeLiteral(")")
		_t2084 := p.construct_export_csv_config(export_csv_path1303, export_csv_columns_list1304, config_dict1305)
		_t2080 = _t2084
	} else {
		var _t2085 *pb.ExportCSVConfig
		if prediction1299 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2086 := p.parse_export_csv_path()
			export_csv_path1300 := _t2086
			_t2087 := p.parse_export_csv_source()
			export_csv_source1301 := _t2087
			_t2088 := p.parse_csv_config()
			csv_config1302 := _t2088
			p.consumeLiteral(")")
			_t2089 := p.construct_export_csv_config_with_source(export_csv_path1300, export_csv_source1301, csv_config1302)
			_t2085 = _t2089
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2080 = _t2085
	}
	result1307 := _t2080
	p.recordSpan(int(span_start1306), "ExportCSVConfig")
	return result1307
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1308 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1308
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1315 := int64(p.spanStart())
	var _t2090 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2091 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2091 = 1
		} else {
			var _t2092 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2092 = 0
			} else {
				_t2092 = -1
			}
			_t2091 = _t2092
		}
		_t2090 = _t2091
	} else {
		_t2090 = -1
	}
	prediction1309 := _t2090
	var _t2093 *pb.ExportCSVSource
	if prediction1309 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2094 := p.parse_relation_id()
		relation_id1314 := _t2094
		p.consumeLiteral(")")
		_t2095 := &pb.ExportCSVSource{}
		_t2095.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1314}
		_t2093 = _t2095
	} else {
		var _t2096 *pb.ExportCSVSource
		if prediction1309 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1310 := []*pb.ExportCSVColumn{}
			cond1311 := p.matchLookaheadLiteral("(", 0)
			for cond1311 {
				_t2097 := p.parse_export_csv_column()
				item1312 := _t2097
				xs1310 = append(xs1310, item1312)
				cond1311 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1313 := xs1310
			p.consumeLiteral(")")
			_t2098 := &pb.ExportCSVColumns{Columns: export_csv_columns1313}
			_t2099 := &pb.ExportCSVSource{}
			_t2099.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2098}
			_t2096 = _t2099
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2093 = _t2096
	}
	result1316 := _t2093
	p.recordSpan(int(span_start1315), "ExportCSVSource")
	return result1316
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1319 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1317 := p.consumeTerminal("STRING").Value.str
	_t2100 := p.parse_relation_id()
	relation_id1318 := _t2100
	p.consumeLiteral(")")
	_t2101 := &pb.ExportCSVColumn{ColumnName: string1317, ColumnData: relation_id1318}
	result1320 := _t2101
	p.recordSpan(int(span_start1319), "ExportCSVColumn")
	return result1320
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1321 := []*pb.ExportCSVColumn{}
	cond1322 := p.matchLookaheadLiteral("(", 0)
	for cond1322 {
		_t2102 := p.parse_export_csv_column()
		item1323 := _t2102
		xs1321 = append(xs1321, item1323)
		cond1322 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1324 := xs1321
	p.consumeLiteral(")")
	return export_csv_columns1324
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1331 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2103 := p.parse_iceberg_locator()
	iceberg_locator1325 := _t2103
	_t2104 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1326 := _t2104
	_t2105 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1327 := _t2105
	_t2106 := p.parse_export_iceberg_columns()
	export_iceberg_columns1328 := _t2106
	_t2107 := p.parse_iceberg_table_properties()
	iceberg_table_properties1329 := _t2107
	var _t2108 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2109 := p.parse_config_dict()
		_t2108 = _t2109
	}
	config_dict1330 := _t2108
	p.consumeLiteral(")")
	_t2110 := p.construct_export_iceberg_config_full(iceberg_locator1325, iceberg_catalog_config1326, export_iceberg_table_def1327, export_iceberg_columns1328, iceberg_table_properties1329, config_dict1330)
	result1332 := _t2110
	p.recordSpan(int(span_start1331), "ExportIcebergConfig")
	return result1332
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1334 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2111 := p.parse_relation_id()
	relation_id1333 := _t2111
	p.consumeLiteral(")")
	result1335 := relation_id1333
	p.recordSpan(int(span_start1334), "RelationId")
	return result1335
}

func (p *Parser) parse_export_iceberg_columns() []*pb.ExportColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1336 := []*pb.ExportColumn{}
	cond1337 := p.matchLookaheadLiteral("(", 0)
	for cond1337 {
		_t2112 := p.parse_export_iceberg_column()
		item1338 := _t2112
		xs1336 = append(xs1336, item1338)
		cond1337 = p.matchLookaheadLiteral("(", 0)
	}
	export_iceberg_columns1339 := xs1336
	p.consumeLiteral(")")
	return export_iceberg_columns1339
}

func (p *Parser) parse_export_iceberg_column() *pb.ExportColumn {
	span_start1342 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1340 := p.consumeTerminal("STRING").Value.str
	_t2113 := p.parse_boolean_value()
	boolean_value1341 := _t2113
	p.consumeLiteral(")")
	_t2114 := &pb.ExportColumn{Name: string1340, Nullable: boolean_value1341}
	result1343 := _t2114
	p.recordSpan(int(span_start1342), "ExportColumn")
	return result1343
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1344 := [][]interface{}{}
	cond1345 := p.matchLookaheadLiteral("(", 0)
	for cond1345 {
		_t2115 := p.parse_iceberg_property_entry()
		item1346 := _t2115
		xs1344 = append(xs1344, item1346)
		cond1345 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1347 := xs1344
	p.consumeLiteral(")")
	return iceberg_property_entrys1347
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
