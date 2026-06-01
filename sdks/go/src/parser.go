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

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns_opt []*pb.GNFColumn, target_opt *pb.IcebergTarget, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2164 := columns_opt
	if columns_opt == nil {
		_t2164 = []*pb.GNFColumn{}
	}
	_t2165 := &pb.IcebergData{Locator: locator, Config: config, Columns: _t2164, Target: target_opt, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2165
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2166 := config_dict
	if config_dict == nil {
		_t2166 = [][]interface{}{}
	}
	cfg := dictFromList(_t2166)
	_t2167 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2167
	_t2168 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2168
	_t2169 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2169
	table_props := stringMapFromPairs(table_property_pairs)
	_t2170 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2170
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start679 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1346 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1347 := p.parse_configure()
		_t1346 = _t1347
	}
	configure673 := _t1346
	var _t1348 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1349 := p.parse_sync()
		_t1348 = _t1349
	}
	sync674 := _t1348
	xs675 := []*pb.Epoch{}
	cond676 := p.matchLookaheadLiteral("(", 0)
	for cond676 {
		_t1350 := p.parse_epoch()
		item677 := _t1350
		xs675 = append(xs675, item677)
		cond676 = p.matchLookaheadLiteral("(", 0)
	}
	epochs678 := xs675
	p.consumeLiteral(")")
	_t1351 := p.default_configure()
	_t1352 := configure673
	if configure673 == nil {
		_t1352 = _t1351
	}
	_t1353 := &pb.Transaction{Epochs: epochs678, Configure: _t1352, Sync: sync674}
	result680 := _t1353
	p.recordSpan(int(span_start679), "Transaction")
	return result680
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start682 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1354 := p.parse_config_dict()
	config_dict681 := _t1354
	p.consumeLiteral(")")
	_t1355 := p.construct_configure(config_dict681)
	result683 := _t1355
	p.recordSpan(int(span_start682), "Configure")
	return result683
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs684 := [][]interface{}{}
	cond685 := p.matchLookaheadLiteral(":", 0)
	for cond685 {
		_t1356 := p.parse_config_key_value()
		item686 := _t1356
		xs684 = append(xs684, item686)
		cond685 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values687 := xs684
	p.consumeLiteral("}")
	return config_key_values687
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol688 := p.consumeTerminal("SYMBOL").Value.str
	_t1357 := p.parse_raw_value()
	raw_value689 := _t1357
	return []interface{}{symbol688, raw_value689}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start703 := int64(p.spanStart())
	var _t1358 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1358 = 12
	} else {
		var _t1359 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1359 = 11
		} else {
			var _t1360 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1360 = 12
			} else {
				var _t1361 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1362 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1362 = 1
					} else {
						var _t1363 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1363 = 0
						} else {
							_t1363 = -1
						}
						_t1362 = _t1363
					}
					_t1361 = _t1362
				} else {
					var _t1364 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1364 = 7
					} else {
						var _t1365 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1365 = 8
						} else {
							var _t1366 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1366 = 2
							} else {
								var _t1367 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1367 = 3
								} else {
									var _t1368 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1368 = 9
									} else {
										var _t1369 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1369 = 4
										} else {
											var _t1370 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1370 = 5
											} else {
												var _t1371 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1371 = 6
												} else {
													var _t1372 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1372 = 10
													} else {
														_t1372 = -1
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
					_t1361 = _t1364
				}
				_t1360 = _t1361
			}
			_t1359 = _t1360
		}
		_t1358 = _t1359
	}
	prediction690 := _t1358
	var _t1373 *pb.Value
	if prediction690 == 12 {
		_t1374 := p.parse_boolean_value()
		boolean_value702 := _t1374
		_t1375 := &pb.Value{}
		_t1375.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value702}
		_t1373 = _t1375
	} else {
		var _t1376 *pb.Value
		if prediction690 == 11 {
			p.consumeLiteral("missing")
			_t1377 := &pb.MissingValue{}
			_t1378 := &pb.Value{}
			_t1378.Value = &pb.Value_MissingValue{MissingValue: _t1377}
			_t1376 = _t1378
		} else {
			var _t1379 *pb.Value
			if prediction690 == 10 {
				decimal701 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1380 := &pb.Value{}
				_t1380.Value = &pb.Value_DecimalValue{DecimalValue: decimal701}
				_t1379 = _t1380
			} else {
				var _t1381 *pb.Value
				if prediction690 == 9 {
					int128700 := p.consumeTerminal("INT128").Value.int128
					_t1382 := &pb.Value{}
					_t1382.Value = &pb.Value_Int128Value{Int128Value: int128700}
					_t1381 = _t1382
				} else {
					var _t1383 *pb.Value
					if prediction690 == 8 {
						uint128699 := p.consumeTerminal("UINT128").Value.uint128
						_t1384 := &pb.Value{}
						_t1384.Value = &pb.Value_Uint128Value{Uint128Value: uint128699}
						_t1383 = _t1384
					} else {
						var _t1385 *pb.Value
						if prediction690 == 7 {
							uint32698 := p.consumeTerminal("UINT32").Value.u32
							_t1386 := &pb.Value{}
							_t1386.Value = &pb.Value_Uint32Value{Uint32Value: uint32698}
							_t1385 = _t1386
						} else {
							var _t1387 *pb.Value
							if prediction690 == 6 {
								float697 := p.consumeTerminal("FLOAT").Value.f64
								_t1388 := &pb.Value{}
								_t1388.Value = &pb.Value_FloatValue{FloatValue: float697}
								_t1387 = _t1388
							} else {
								var _t1389 *pb.Value
								if prediction690 == 5 {
									float32696 := p.consumeTerminal("FLOAT32").Value.f32
									_t1390 := &pb.Value{}
									_t1390.Value = &pb.Value_Float32Value{Float32Value: float32696}
									_t1389 = _t1390
								} else {
									var _t1391 *pb.Value
									if prediction690 == 4 {
										int695 := p.consumeTerminal("INT").Value.i64
										_t1392 := &pb.Value{}
										_t1392.Value = &pb.Value_IntValue{IntValue: int695}
										_t1391 = _t1392
									} else {
										var _t1393 *pb.Value
										if prediction690 == 3 {
											int32694 := p.consumeTerminal("INT32").Value.i32
											_t1394 := &pb.Value{}
											_t1394.Value = &pb.Value_Int32Value{Int32Value: int32694}
											_t1393 = _t1394
										} else {
											var _t1395 *pb.Value
											if prediction690 == 2 {
												string693 := p.consumeTerminal("STRING").Value.str
												_t1396 := &pb.Value{}
												_t1396.Value = &pb.Value_StringValue{StringValue: string693}
												_t1395 = _t1396
											} else {
												var _t1397 *pb.Value
												if prediction690 == 1 {
													_t1398 := p.parse_raw_datetime()
													raw_datetime692 := _t1398
													_t1399 := &pb.Value{}
													_t1399.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime692}
													_t1397 = _t1399
												} else {
													var _t1400 *pb.Value
													if prediction690 == 0 {
														_t1401 := p.parse_raw_date()
														raw_date691 := _t1401
														_t1402 := &pb.Value{}
														_t1402.Value = &pb.Value_DateValue{DateValue: raw_date691}
														_t1400 = _t1402
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1397 = _t1400
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
				_t1379 = _t1381
			}
			_t1376 = _t1379
		}
		_t1373 = _t1376
	}
	result704 := _t1373
	p.recordSpan(int(span_start703), "Value")
	return result704
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start708 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int705 := p.consumeTerminal("INT").Value.i64
	int_3706 := p.consumeTerminal("INT").Value.i64
	int_4707 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1403 := &pb.DateValue{Year: int32(int705), Month: int32(int_3706), Day: int32(int_4707)}
	result709 := _t1403
	p.recordSpan(int(span_start708), "DateValue")
	return result709
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int710 := p.consumeTerminal("INT").Value.i64
	int_3711 := p.consumeTerminal("INT").Value.i64
	int_4712 := p.consumeTerminal("INT").Value.i64
	int_5713 := p.consumeTerminal("INT").Value.i64
	int_6714 := p.consumeTerminal("INT").Value.i64
	int_7715 := p.consumeTerminal("INT").Value.i64
	var _t1404 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1404 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8716 := _t1404
	p.consumeLiteral(")")
	_t1405 := &pb.DateTimeValue{Year: int32(int710), Month: int32(int_3711), Day: int32(int_4712), Hour: int32(int_5713), Minute: int32(int_6714), Second: int32(int_7715), Microsecond: int32(deref(int_8716, 0))}
	result718 := _t1405
	p.recordSpan(int(span_start717), "DateTimeValue")
	return result718
}

func (p *Parser) parse_boolean_value() bool {
	var _t1406 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1406 = 0
	} else {
		var _t1407 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1407 = 1
		} else {
			_t1407 = -1
		}
		_t1406 = _t1407
	}
	prediction719 := _t1406
	var _t1408 bool
	if prediction719 == 1 {
		p.consumeLiteral("false")
		_t1408 = false
	} else {
		var _t1409 bool
		if prediction719 == 0 {
			p.consumeLiteral("true")
			_t1409 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1408 = _t1409
	}
	return _t1408
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start724 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs720 := []*pb.FragmentId{}
	cond721 := p.matchLookaheadLiteral(":", 0)
	for cond721 {
		_t1410 := p.parse_fragment_id()
		item722 := _t1410
		xs720 = append(xs720, item722)
		cond721 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids723 := xs720
	p.consumeLiteral(")")
	_t1411 := &pb.Sync{Fragments: fragment_ids723}
	result725 := _t1411
	p.recordSpan(int(span_start724), "Sync")
	return result725
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start727 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol726 := p.consumeTerminal("SYMBOL").Value.str
	result728 := &pb.FragmentId{Id: []byte(symbol726)}
	p.recordSpan(int(span_start727), "FragmentId")
	return result728
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1412 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1413 := p.parse_epoch_writes()
		_t1412 = _t1413
	}
	epoch_writes729 := _t1412
	var _t1414 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1415 := p.parse_epoch_reads()
		_t1414 = _t1415
	}
	epoch_reads730 := _t1414
	p.consumeLiteral(")")
	_t1416 := epoch_writes729
	if epoch_writes729 == nil {
		_t1416 = []*pb.Write{}
	}
	_t1417 := epoch_reads730
	if epoch_reads730 == nil {
		_t1417 = []*pb.Read{}
	}
	_t1418 := &pb.Epoch{Writes: _t1416, Reads: _t1417}
	result732 := _t1418
	p.recordSpan(int(span_start731), "Epoch")
	return result732
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs733 := []*pb.Write{}
	cond734 := p.matchLookaheadLiteral("(", 0)
	for cond734 {
		_t1419 := p.parse_write()
		item735 := _t1419
		xs733 = append(xs733, item735)
		cond734 = p.matchLookaheadLiteral("(", 0)
	}
	writes736 := xs733
	p.consumeLiteral(")")
	return writes736
}

func (p *Parser) parse_write() *pb.Write {
	span_start742 := int64(p.spanStart())
	var _t1420 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1421 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1421 = 1
		} else {
			var _t1422 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1422 = 3
			} else {
				var _t1423 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1423 = 0
				} else {
					var _t1424 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1424 = 2
					} else {
						_t1424 = -1
					}
					_t1423 = _t1424
				}
				_t1422 = _t1423
			}
			_t1421 = _t1422
		}
		_t1420 = _t1421
	} else {
		_t1420 = -1
	}
	prediction737 := _t1420
	var _t1425 *pb.Write
	if prediction737 == 3 {
		_t1426 := p.parse_snapshot()
		snapshot741 := _t1426
		_t1427 := &pb.Write{}
		_t1427.WriteType = &pb.Write_Snapshot{Snapshot: snapshot741}
		_t1425 = _t1427
	} else {
		var _t1428 *pb.Write
		if prediction737 == 2 {
			_t1429 := p.parse_context()
			context740 := _t1429
			_t1430 := &pb.Write{}
			_t1430.WriteType = &pb.Write_Context{Context: context740}
			_t1428 = _t1430
		} else {
			var _t1431 *pb.Write
			if prediction737 == 1 {
				_t1432 := p.parse_undefine()
				undefine739 := _t1432
				_t1433 := &pb.Write{}
				_t1433.WriteType = &pb.Write_Undefine{Undefine: undefine739}
				_t1431 = _t1433
			} else {
				var _t1434 *pb.Write
				if prediction737 == 0 {
					_t1435 := p.parse_define()
					define738 := _t1435
					_t1436 := &pb.Write{}
					_t1436.WriteType = &pb.Write_Define{Define: define738}
					_t1434 = _t1436
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1431 = _t1434
			}
			_t1428 = _t1431
		}
		_t1425 = _t1428
	}
	result743 := _t1425
	p.recordSpan(int(span_start742), "Write")
	return result743
}

func (p *Parser) parse_define() *pb.Define {
	span_start745 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1437 := p.parse_fragment()
	fragment744 := _t1437
	p.consumeLiteral(")")
	_t1438 := &pb.Define{Fragment: fragment744}
	result746 := _t1438
	p.recordSpan(int(span_start745), "Define")
	return result746
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1439 := p.parse_new_fragment_id()
	new_fragment_id747 := _t1439
	xs748 := []*pb.Declaration{}
	cond749 := p.matchLookaheadLiteral("(", 0)
	for cond749 {
		_t1440 := p.parse_declaration()
		item750 := _t1440
		xs748 = append(xs748, item750)
		cond749 = p.matchLookaheadLiteral("(", 0)
	}
	declarations751 := xs748
	p.consumeLiteral(")")
	result753 := p.constructFragment(new_fragment_id747, declarations751)
	p.recordSpan(int(span_start752), "Fragment")
	return result753
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start755 := int64(p.spanStart())
	_t1441 := p.parse_fragment_id()
	fragment_id754 := _t1441
	p.startFragment(fragment_id754)
	result756 := fragment_id754
	p.recordSpan(int(span_start755), "FragmentId")
	return result756
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start762 := int64(p.spanStart())
	var _t1442 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1443 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1443 = 3
		} else {
			var _t1444 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1444 = 2
			} else {
				var _t1445 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1445 = 3
				} else {
					var _t1446 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1446 = 0
					} else {
						var _t1447 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1447 = 3
						} else {
							var _t1448 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1448 = 3
							} else {
								var _t1449 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1449 = 1
								} else {
									_t1449 = -1
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
	} else {
		_t1442 = -1
	}
	prediction757 := _t1442
	var _t1450 *pb.Declaration
	if prediction757 == 3 {
		_t1451 := p.parse_data()
		data761 := _t1451
		_t1452 := &pb.Declaration{}
		_t1452.DeclarationType = &pb.Declaration_Data{Data: data761}
		_t1450 = _t1452
	} else {
		var _t1453 *pb.Declaration
		if prediction757 == 2 {
			_t1454 := p.parse_constraint()
			constraint760 := _t1454
			_t1455 := &pb.Declaration{}
			_t1455.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint760}
			_t1453 = _t1455
		} else {
			var _t1456 *pb.Declaration
			if prediction757 == 1 {
				_t1457 := p.parse_algorithm()
				algorithm759 := _t1457
				_t1458 := &pb.Declaration{}
				_t1458.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm759}
				_t1456 = _t1458
			} else {
				var _t1459 *pb.Declaration
				if prediction757 == 0 {
					_t1460 := p.parse_def()
					def758 := _t1460
					_t1461 := &pb.Declaration{}
					_t1461.DeclarationType = &pb.Declaration_Def{Def: def758}
					_t1459 = _t1461
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1456 = _t1459
			}
			_t1453 = _t1456
		}
		_t1450 = _t1453
	}
	result763 := _t1450
	p.recordSpan(int(span_start762), "Declaration")
	return result763
}

func (p *Parser) parse_def() *pb.Def {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1462 := p.parse_relation_id()
	relation_id764 := _t1462
	_t1463 := p.parse_abstraction()
	abstraction765 := _t1463
	var _t1464 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1465 := p.parse_attrs()
		_t1464 = _t1465
	}
	attrs766 := _t1464
	p.consumeLiteral(")")
	_t1466 := attrs766
	if attrs766 == nil {
		_t1466 = []*pb.Attribute{}
	}
	_t1467 := &pb.Def{Name: relation_id764, Body: abstraction765, Attrs: _t1466}
	result768 := _t1467
	p.recordSpan(int(span_start767), "Def")
	return result768
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start772 := int64(p.spanStart())
	var _t1468 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1468 = 0
	} else {
		var _t1469 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1469 = 1
		} else {
			_t1469 = -1
		}
		_t1468 = _t1469
	}
	prediction769 := _t1468
	var _t1470 *pb.RelationId
	if prediction769 == 1 {
		uint128771 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128771
		_t1470 = &pb.RelationId{IdLow: uint128771.Low, IdHigh: uint128771.High}
	} else {
		var _t1471 *pb.RelationId
		if prediction769 == 0 {
			p.consumeLiteral(":")
			symbol770 := p.consumeTerminal("SYMBOL").Value.str
			_t1471 = p.relationIdFromString(symbol770)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1470 = _t1471
	}
	result773 := _t1470
	p.recordSpan(int(span_start772), "RelationId")
	return result773
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1472 := p.parse_bindings()
	bindings774 := _t1472
	_t1473 := p.parse_formula()
	formula775 := _t1473
	p.consumeLiteral(")")
	_t1474 := &pb.Abstraction{Vars: listConcat(bindings774[0].([]*pb.Binding), bindings774[1].([]*pb.Binding)), Value: formula775}
	result777 := _t1474
	p.recordSpan(int(span_start776), "Abstraction")
	return result777
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs778 := []*pb.Binding{}
	cond779 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond779 {
		_t1475 := p.parse_binding()
		item780 := _t1475
		xs778 = append(xs778, item780)
		cond779 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings781 := xs778
	var _t1476 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1477 := p.parse_value_bindings()
		_t1476 = _t1477
	}
	value_bindings782 := _t1476
	p.consumeLiteral("]")
	_t1478 := value_bindings782
	if value_bindings782 == nil {
		_t1478 = []*pb.Binding{}
	}
	return []interface{}{bindings781, _t1478}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start785 := int64(p.spanStart())
	symbol783 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1479 := p.parse_type()
	type784 := _t1479
	_t1480 := &pb.Var{Name: symbol783}
	_t1481 := &pb.Binding{Var: _t1480, Type: type784}
	result786 := _t1481
	p.recordSpan(int(span_start785), "Binding")
	return result786
}

func (p *Parser) parse_type() *pb.Type {
	span_start802 := int64(p.spanStart())
	var _t1482 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1482 = 0
	} else {
		var _t1483 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1483 = 13
		} else {
			var _t1484 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1484 = 4
			} else {
				var _t1485 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1485 = 1
				} else {
					var _t1486 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1486 = 8
					} else {
						var _t1487 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1487 = 11
						} else {
							var _t1488 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1488 = 5
							} else {
								var _t1489 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1489 = 2
								} else {
									var _t1490 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1490 = 12
									} else {
										var _t1491 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1491 = 3
										} else {
											var _t1492 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1492 = 7
											} else {
												var _t1493 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1493 = 6
												} else {
													var _t1494 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1494 = 10
													} else {
														var _t1495 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1495 = 9
														} else {
															_t1495 = -1
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
			_t1483 = _t1484
		}
		_t1482 = _t1483
	}
	prediction787 := _t1482
	var _t1496 *pb.Type
	if prediction787 == 13 {
		_t1497 := p.parse_uint32_type()
		uint32_type801 := _t1497
		_t1498 := &pb.Type{}
		_t1498.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type801}
		_t1496 = _t1498
	} else {
		var _t1499 *pb.Type
		if prediction787 == 12 {
			_t1500 := p.parse_float32_type()
			float32_type800 := _t1500
			_t1501 := &pb.Type{}
			_t1501.Type = &pb.Type_Float32Type{Float32Type: float32_type800}
			_t1499 = _t1501
		} else {
			var _t1502 *pb.Type
			if prediction787 == 11 {
				_t1503 := p.parse_int32_type()
				int32_type799 := _t1503
				_t1504 := &pb.Type{}
				_t1504.Type = &pb.Type_Int32Type{Int32Type: int32_type799}
				_t1502 = _t1504
			} else {
				var _t1505 *pb.Type
				if prediction787 == 10 {
					_t1506 := p.parse_boolean_type()
					boolean_type798 := _t1506
					_t1507 := &pb.Type{}
					_t1507.Type = &pb.Type_BooleanType{BooleanType: boolean_type798}
					_t1505 = _t1507
				} else {
					var _t1508 *pb.Type
					if prediction787 == 9 {
						_t1509 := p.parse_decimal_type()
						decimal_type797 := _t1509
						_t1510 := &pb.Type{}
						_t1510.Type = &pb.Type_DecimalType{DecimalType: decimal_type797}
						_t1508 = _t1510
					} else {
						var _t1511 *pb.Type
						if prediction787 == 8 {
							_t1512 := p.parse_missing_type()
							missing_type796 := _t1512
							_t1513 := &pb.Type{}
							_t1513.Type = &pb.Type_MissingType{MissingType: missing_type796}
							_t1511 = _t1513
						} else {
							var _t1514 *pb.Type
							if prediction787 == 7 {
								_t1515 := p.parse_datetime_type()
								datetime_type795 := _t1515
								_t1516 := &pb.Type{}
								_t1516.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type795}
								_t1514 = _t1516
							} else {
								var _t1517 *pb.Type
								if prediction787 == 6 {
									_t1518 := p.parse_date_type()
									date_type794 := _t1518
									_t1519 := &pb.Type{}
									_t1519.Type = &pb.Type_DateType{DateType: date_type794}
									_t1517 = _t1519
								} else {
									var _t1520 *pb.Type
									if prediction787 == 5 {
										_t1521 := p.parse_int128_type()
										int128_type793 := _t1521
										_t1522 := &pb.Type{}
										_t1522.Type = &pb.Type_Int128Type{Int128Type: int128_type793}
										_t1520 = _t1522
									} else {
										var _t1523 *pb.Type
										if prediction787 == 4 {
											_t1524 := p.parse_uint128_type()
											uint128_type792 := _t1524
											_t1525 := &pb.Type{}
											_t1525.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type792}
											_t1523 = _t1525
										} else {
											var _t1526 *pb.Type
											if prediction787 == 3 {
												_t1527 := p.parse_float_type()
												float_type791 := _t1527
												_t1528 := &pb.Type{}
												_t1528.Type = &pb.Type_FloatType{FloatType: float_type791}
												_t1526 = _t1528
											} else {
												var _t1529 *pb.Type
												if prediction787 == 2 {
													_t1530 := p.parse_int_type()
													int_type790 := _t1530
													_t1531 := &pb.Type{}
													_t1531.Type = &pb.Type_IntType{IntType: int_type790}
													_t1529 = _t1531
												} else {
													var _t1532 *pb.Type
													if prediction787 == 1 {
														_t1533 := p.parse_string_type()
														string_type789 := _t1533
														_t1534 := &pb.Type{}
														_t1534.Type = &pb.Type_StringType{StringType: string_type789}
														_t1532 = _t1534
													} else {
														var _t1535 *pb.Type
														if prediction787 == 0 {
															_t1536 := p.parse_unspecified_type()
															unspecified_type788 := _t1536
															_t1537 := &pb.Type{}
															_t1537.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type788}
															_t1535 = _t1537
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1532 = _t1535
													}
													_t1529 = _t1532
												}
												_t1526 = _t1529
											}
											_t1523 = _t1526
										}
										_t1520 = _t1523
									}
									_t1517 = _t1520
								}
								_t1514 = _t1517
							}
							_t1511 = _t1514
						}
						_t1508 = _t1511
					}
					_t1505 = _t1508
				}
				_t1502 = _t1505
			}
			_t1499 = _t1502
		}
		_t1496 = _t1499
	}
	result803 := _t1496
	p.recordSpan(int(span_start802), "Type")
	return result803
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1538 := &pb.UnspecifiedType{}
	result805 := _t1538
	p.recordSpan(int(span_start804), "UnspecifiedType")
	return result805
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1539 := &pb.StringType{}
	result807 := _t1539
	p.recordSpan(int(span_start806), "StringType")
	return result807
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1540 := &pb.IntType{}
	result809 := _t1540
	p.recordSpan(int(span_start808), "IntType")
	return result809
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1541 := &pb.FloatType{}
	result811 := _t1541
	p.recordSpan(int(span_start810), "FloatType")
	return result811
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1542 := &pb.UInt128Type{}
	result813 := _t1542
	p.recordSpan(int(span_start812), "UInt128Type")
	return result813
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1543 := &pb.Int128Type{}
	result815 := _t1543
	p.recordSpan(int(span_start814), "Int128Type")
	return result815
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1544 := &pb.DateType{}
	result817 := _t1544
	p.recordSpan(int(span_start816), "DateType")
	return result817
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1545 := &pb.DateTimeType{}
	result819 := _t1545
	p.recordSpan(int(span_start818), "DateTimeType")
	return result819
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1546 := &pb.MissingType{}
	result821 := _t1546
	p.recordSpan(int(span_start820), "MissingType")
	return result821
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int822 := p.consumeTerminal("INT").Value.i64
	int_3823 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1547 := &pb.DecimalType{Precision: int32(int822), Scale: int32(int_3823)}
	result825 := _t1547
	p.recordSpan(int(span_start824), "DecimalType")
	return result825
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start826 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1548 := &pb.BooleanType{}
	result827 := _t1548
	p.recordSpan(int(span_start826), "BooleanType")
	return result827
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1549 := &pb.Int32Type{}
	result829 := _t1549
	p.recordSpan(int(span_start828), "Int32Type")
	return result829
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start830 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1550 := &pb.Float32Type{}
	result831 := _t1550
	p.recordSpan(int(span_start830), "Float32Type")
	return result831
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start832 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1551 := &pb.UInt32Type{}
	result833 := _t1551
	p.recordSpan(int(span_start832), "UInt32Type")
	return result833
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs834 := []*pb.Binding{}
	cond835 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond835 {
		_t1552 := p.parse_binding()
		item836 := _t1552
		xs834 = append(xs834, item836)
		cond835 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings837 := xs834
	return bindings837
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start852 := int64(p.spanStart())
	var _t1553 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1554 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1554 = 0
		} else {
			var _t1555 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1555 = 11
			} else {
				var _t1556 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1556 = 3
				} else {
					var _t1557 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1557 = 10
					} else {
						var _t1558 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1558 = 9
						} else {
							var _t1559 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1559 = 5
							} else {
								var _t1560 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1560 = 6
								} else {
									var _t1561 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1561 = 7
									} else {
										var _t1562 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1562 = 1
										} else {
											var _t1563 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1563 = 2
											} else {
												var _t1564 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1564 = 12
												} else {
													var _t1565 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1565 = 8
													} else {
														var _t1566 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1566 = 4
														} else {
															var _t1567 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1567 = 10
															} else {
																var _t1568 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1568 = 10
																} else {
																	var _t1569 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1569 = 10
																	} else {
																		var _t1570 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1570 = 10
																		} else {
																			var _t1571 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1571 = 10
																			} else {
																				var _t1572 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1572 = 10
																				} else {
																					var _t1573 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1573 = 10
																					} else {
																						var _t1574 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1574 = 10
																						} else {
																							var _t1575 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1575 = 10
																							} else {
																								_t1575 = -1
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
			}
			_t1554 = _t1555
		}
		_t1553 = _t1554
	} else {
		_t1553 = -1
	}
	prediction838 := _t1553
	var _t1576 *pb.Formula
	if prediction838 == 12 {
		_t1577 := p.parse_cast()
		cast851 := _t1577
		_t1578 := &pb.Formula{}
		_t1578.FormulaType = &pb.Formula_Cast{Cast: cast851}
		_t1576 = _t1578
	} else {
		var _t1579 *pb.Formula
		if prediction838 == 11 {
			_t1580 := p.parse_rel_atom()
			rel_atom850 := _t1580
			_t1581 := &pb.Formula{}
			_t1581.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom850}
			_t1579 = _t1581
		} else {
			var _t1582 *pb.Formula
			if prediction838 == 10 {
				_t1583 := p.parse_primitive()
				primitive849 := _t1583
				_t1584 := &pb.Formula{}
				_t1584.FormulaType = &pb.Formula_Primitive{Primitive: primitive849}
				_t1582 = _t1584
			} else {
				var _t1585 *pb.Formula
				if prediction838 == 9 {
					_t1586 := p.parse_pragma()
					pragma848 := _t1586
					_t1587 := &pb.Formula{}
					_t1587.FormulaType = &pb.Formula_Pragma{Pragma: pragma848}
					_t1585 = _t1587
				} else {
					var _t1588 *pb.Formula
					if prediction838 == 8 {
						_t1589 := p.parse_atom()
						atom847 := _t1589
						_t1590 := &pb.Formula{}
						_t1590.FormulaType = &pb.Formula_Atom{Atom: atom847}
						_t1588 = _t1590
					} else {
						var _t1591 *pb.Formula
						if prediction838 == 7 {
							_t1592 := p.parse_ffi()
							ffi846 := _t1592
							_t1593 := &pb.Formula{}
							_t1593.FormulaType = &pb.Formula_Ffi{Ffi: ffi846}
							_t1591 = _t1593
						} else {
							var _t1594 *pb.Formula
							if prediction838 == 6 {
								_t1595 := p.parse_not()
								not845 := _t1595
								_t1596 := &pb.Formula{}
								_t1596.FormulaType = &pb.Formula_Not{Not: not845}
								_t1594 = _t1596
							} else {
								var _t1597 *pb.Formula
								if prediction838 == 5 {
									_t1598 := p.parse_disjunction()
									disjunction844 := _t1598
									_t1599 := &pb.Formula{}
									_t1599.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction844}
									_t1597 = _t1599
								} else {
									var _t1600 *pb.Formula
									if prediction838 == 4 {
										_t1601 := p.parse_conjunction()
										conjunction843 := _t1601
										_t1602 := &pb.Formula{}
										_t1602.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction843}
										_t1600 = _t1602
									} else {
										var _t1603 *pb.Formula
										if prediction838 == 3 {
											_t1604 := p.parse_reduce()
											reduce842 := _t1604
											_t1605 := &pb.Formula{}
											_t1605.FormulaType = &pb.Formula_Reduce{Reduce: reduce842}
											_t1603 = _t1605
										} else {
											var _t1606 *pb.Formula
											if prediction838 == 2 {
												_t1607 := p.parse_exists()
												exists841 := _t1607
												_t1608 := &pb.Formula{}
												_t1608.FormulaType = &pb.Formula_Exists{Exists: exists841}
												_t1606 = _t1608
											} else {
												var _t1609 *pb.Formula
												if prediction838 == 1 {
													_t1610 := p.parse_false()
													false840 := _t1610
													_t1611 := &pb.Formula{}
													_t1611.FormulaType = &pb.Formula_Disjunction{Disjunction: false840}
													_t1609 = _t1611
												} else {
													var _t1612 *pb.Formula
													if prediction838 == 0 {
														_t1613 := p.parse_true()
														true839 := _t1613
														_t1614 := &pb.Formula{}
														_t1614.FormulaType = &pb.Formula_Conjunction{Conjunction: true839}
														_t1612 = _t1614
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1609 = _t1612
												}
												_t1606 = _t1609
											}
											_t1603 = _t1606
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
	result853 := _t1576
	p.recordSpan(int(span_start852), "Formula")
	return result853
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1615 := &pb.Conjunction{Args: []*pb.Formula{}}
	result855 := _t1615
	p.recordSpan(int(span_start854), "Conjunction")
	return result855
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start856 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1616 := &pb.Disjunction{Args: []*pb.Formula{}}
	result857 := _t1616
	p.recordSpan(int(span_start856), "Disjunction")
	return result857
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1617 := p.parse_bindings()
	bindings858 := _t1617
	_t1618 := p.parse_formula()
	formula859 := _t1618
	p.consumeLiteral(")")
	_t1619 := &pb.Abstraction{Vars: listConcat(bindings858[0].([]*pb.Binding), bindings858[1].([]*pb.Binding)), Value: formula859}
	_t1620 := &pb.Exists{Body: _t1619}
	result861 := _t1620
	p.recordSpan(int(span_start860), "Exists")
	return result861
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1621 := p.parse_abstraction()
	abstraction862 := _t1621
	_t1622 := p.parse_abstraction()
	abstraction_3863 := _t1622
	_t1623 := p.parse_terms()
	terms864 := _t1623
	p.consumeLiteral(")")
	_t1624 := &pb.Reduce{Op: abstraction862, Body: abstraction_3863, Terms: terms864}
	result866 := _t1624
	p.recordSpan(int(span_start865), "Reduce")
	return result866
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs867 := []*pb.Term{}
	cond868 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond868 {
		_t1625 := p.parse_term()
		item869 := _t1625
		xs867 = append(xs867, item869)
		cond868 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms870 := xs867
	p.consumeLiteral(")")
	return terms870
}

func (p *Parser) parse_term() *pb.Term {
	span_start874 := int64(p.spanStart())
	var _t1626 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1626 = 1
	} else {
		var _t1627 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1627 = 1
		} else {
			var _t1628 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1628 = 1
			} else {
				var _t1629 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1629 = 1
				} else {
					var _t1630 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1630 = 0
					} else {
						var _t1631 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1631 = 1
						} else {
							var _t1632 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1632 = 1
							} else {
								var _t1633 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1633 = 1
								} else {
									var _t1634 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1634 = 1
									} else {
										var _t1635 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1635 = 1
										} else {
											var _t1636 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1636 = 1
											} else {
												var _t1637 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1637 = 1
												} else {
													var _t1638 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1638 = 1
													} else {
														var _t1639 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1639 = 1
														} else {
															_t1639 = -1
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
	prediction871 := _t1626
	var _t1640 *pb.Term
	if prediction871 == 1 {
		_t1641 := p.parse_value()
		value873 := _t1641
		_t1642 := &pb.Term{}
		_t1642.TermType = &pb.Term_Constant{Constant: value873}
		_t1640 = _t1642
	} else {
		var _t1643 *pb.Term
		if prediction871 == 0 {
			_t1644 := p.parse_var()
			var872 := _t1644
			_t1645 := &pb.Term{}
			_t1645.TermType = &pb.Term_Var{Var: var872}
			_t1643 = _t1645
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1640 = _t1643
	}
	result875 := _t1640
	p.recordSpan(int(span_start874), "Term")
	return result875
}

func (p *Parser) parse_var() *pb.Var {
	span_start877 := int64(p.spanStart())
	symbol876 := p.consumeTerminal("SYMBOL").Value.str
	_t1646 := &pb.Var{Name: symbol876}
	result878 := _t1646
	p.recordSpan(int(span_start877), "Var")
	return result878
}

func (p *Parser) parse_value() *pb.Value {
	span_start892 := int64(p.spanStart())
	var _t1647 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1647 = 12
	} else {
		var _t1648 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1648 = 11
		} else {
			var _t1649 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1649 = 12
			} else {
				var _t1650 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1651 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1651 = 1
					} else {
						var _t1652 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1652 = 0
						} else {
							_t1652 = -1
						}
						_t1651 = _t1652
					}
					_t1650 = _t1651
				} else {
					var _t1653 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1653 = 7
					} else {
						var _t1654 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1654 = 8
						} else {
							var _t1655 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1655 = 2
							} else {
								var _t1656 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1656 = 3
								} else {
									var _t1657 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1657 = 9
									} else {
										var _t1658 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1658 = 4
										} else {
											var _t1659 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1659 = 5
											} else {
												var _t1660 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1660 = 6
												} else {
													var _t1661 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1661 = 10
													} else {
														_t1661 = -1
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
					_t1650 = _t1653
				}
				_t1649 = _t1650
			}
			_t1648 = _t1649
		}
		_t1647 = _t1648
	}
	prediction879 := _t1647
	var _t1662 *pb.Value
	if prediction879 == 12 {
		_t1663 := p.parse_boolean_value()
		boolean_value891 := _t1663
		_t1664 := &pb.Value{}
		_t1664.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value891}
		_t1662 = _t1664
	} else {
		var _t1665 *pb.Value
		if prediction879 == 11 {
			p.consumeLiteral("missing")
			_t1666 := &pb.MissingValue{}
			_t1667 := &pb.Value{}
			_t1667.Value = &pb.Value_MissingValue{MissingValue: _t1666}
			_t1665 = _t1667
		} else {
			var _t1668 *pb.Value
			if prediction879 == 10 {
				formatted_decimal890 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1669 := &pb.Value{}
				_t1669.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal890}
				_t1668 = _t1669
			} else {
				var _t1670 *pb.Value
				if prediction879 == 9 {
					formatted_int128889 := p.consumeTerminal("INT128").Value.int128
					_t1671 := &pb.Value{}
					_t1671.Value = &pb.Value_Int128Value{Int128Value: formatted_int128889}
					_t1670 = _t1671
				} else {
					var _t1672 *pb.Value
					if prediction879 == 8 {
						formatted_uint128888 := p.consumeTerminal("UINT128").Value.uint128
						_t1673 := &pb.Value{}
						_t1673.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128888}
						_t1672 = _t1673
					} else {
						var _t1674 *pb.Value
						if prediction879 == 7 {
							formatted_uint32887 := p.consumeTerminal("UINT32").Value.u32
							_t1675 := &pb.Value{}
							_t1675.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32887}
							_t1674 = _t1675
						} else {
							var _t1676 *pb.Value
							if prediction879 == 6 {
								formatted_float886 := p.consumeTerminal("FLOAT").Value.f64
								_t1677 := &pb.Value{}
								_t1677.Value = &pb.Value_FloatValue{FloatValue: formatted_float886}
								_t1676 = _t1677
							} else {
								var _t1678 *pb.Value
								if prediction879 == 5 {
									formatted_float32885 := p.consumeTerminal("FLOAT32").Value.f32
									_t1679 := &pb.Value{}
									_t1679.Value = &pb.Value_Float32Value{Float32Value: formatted_float32885}
									_t1678 = _t1679
								} else {
									var _t1680 *pb.Value
									if prediction879 == 4 {
										formatted_int884 := p.consumeTerminal("INT").Value.i64
										_t1681 := &pb.Value{}
										_t1681.Value = &pb.Value_IntValue{IntValue: formatted_int884}
										_t1680 = _t1681
									} else {
										var _t1682 *pb.Value
										if prediction879 == 3 {
											formatted_int32883 := p.consumeTerminal("INT32").Value.i32
											_t1683 := &pb.Value{}
											_t1683.Value = &pb.Value_Int32Value{Int32Value: formatted_int32883}
											_t1682 = _t1683
										} else {
											var _t1684 *pb.Value
											if prediction879 == 2 {
												formatted_string882 := p.consumeTerminal("STRING").Value.str
												_t1685 := &pb.Value{}
												_t1685.Value = &pb.Value_StringValue{StringValue: formatted_string882}
												_t1684 = _t1685
											} else {
												var _t1686 *pb.Value
												if prediction879 == 1 {
													_t1687 := p.parse_datetime()
													datetime881 := _t1687
													_t1688 := &pb.Value{}
													_t1688.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime881}
													_t1686 = _t1688
												} else {
													var _t1689 *pb.Value
													if prediction879 == 0 {
														_t1690 := p.parse_date()
														date880 := _t1690
														_t1691 := &pb.Value{}
														_t1691.Value = &pb.Value_DateValue{DateValue: date880}
														_t1689 = _t1691
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1686 = _t1689
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
				_t1668 = _t1670
			}
			_t1665 = _t1668
		}
		_t1662 = _t1665
	}
	result893 := _t1662
	p.recordSpan(int(span_start892), "Value")
	return result893
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start897 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int894 := p.consumeTerminal("INT").Value.i64
	formatted_int_3895 := p.consumeTerminal("INT").Value.i64
	formatted_int_4896 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1692 := &pb.DateValue{Year: int32(formatted_int894), Month: int32(formatted_int_3895), Day: int32(formatted_int_4896)}
	result898 := _t1692
	p.recordSpan(int(span_start897), "DateValue")
	return result898
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start906 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int899 := p.consumeTerminal("INT").Value.i64
	formatted_int_3900 := p.consumeTerminal("INT").Value.i64
	formatted_int_4901 := p.consumeTerminal("INT").Value.i64
	formatted_int_5902 := p.consumeTerminal("INT").Value.i64
	formatted_int_6903 := p.consumeTerminal("INT").Value.i64
	formatted_int_7904 := p.consumeTerminal("INT").Value.i64
	var _t1693 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1693 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8905 := _t1693
	p.consumeLiteral(")")
	_t1694 := &pb.DateTimeValue{Year: int32(formatted_int899), Month: int32(formatted_int_3900), Day: int32(formatted_int_4901), Hour: int32(formatted_int_5902), Minute: int32(formatted_int_6903), Second: int32(formatted_int_7904), Microsecond: int32(deref(formatted_int_8905, 0))}
	result907 := _t1694
	p.recordSpan(int(span_start906), "DateTimeValue")
	return result907
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start912 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs908 := []*pb.Formula{}
	cond909 := p.matchLookaheadLiteral("(", 0)
	for cond909 {
		_t1695 := p.parse_formula()
		item910 := _t1695
		xs908 = append(xs908, item910)
		cond909 = p.matchLookaheadLiteral("(", 0)
	}
	formulas911 := xs908
	p.consumeLiteral(")")
	_t1696 := &pb.Conjunction{Args: formulas911}
	result913 := _t1696
	p.recordSpan(int(span_start912), "Conjunction")
	return result913
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs914 := []*pb.Formula{}
	cond915 := p.matchLookaheadLiteral("(", 0)
	for cond915 {
		_t1697 := p.parse_formula()
		item916 := _t1697
		xs914 = append(xs914, item916)
		cond915 = p.matchLookaheadLiteral("(", 0)
	}
	formulas917 := xs914
	p.consumeLiteral(")")
	_t1698 := &pb.Disjunction{Args: formulas917}
	result919 := _t1698
	p.recordSpan(int(span_start918), "Disjunction")
	return result919
}

func (p *Parser) parse_not() *pb.Not {
	span_start921 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1699 := p.parse_formula()
	formula920 := _t1699
	p.consumeLiteral(")")
	_t1700 := &pb.Not{Arg: formula920}
	result922 := _t1700
	p.recordSpan(int(span_start921), "Not")
	return result922
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start926 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1701 := p.parse_name()
	name923 := _t1701
	_t1702 := p.parse_ffi_args()
	ffi_args924 := _t1702
	_t1703 := p.parse_terms()
	terms925 := _t1703
	p.consumeLiteral(")")
	_t1704 := &pb.FFI{Name: name923, Args: ffi_args924, Terms: terms925}
	result927 := _t1704
	p.recordSpan(int(span_start926), "FFI")
	return result927
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol928 := p.consumeTerminal("SYMBOL").Value.str
	return symbol928
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs929 := []*pb.Abstraction{}
	cond930 := p.matchLookaheadLiteral("(", 0)
	for cond930 {
		_t1705 := p.parse_abstraction()
		item931 := _t1705
		xs929 = append(xs929, item931)
		cond930 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions932 := xs929
	p.consumeLiteral(")")
	return abstractions932
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start938 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1706 := p.parse_relation_id()
	relation_id933 := _t1706
	xs934 := []*pb.Term{}
	cond935 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond935 {
		_t1707 := p.parse_term()
		item936 := _t1707
		xs934 = append(xs934, item936)
		cond935 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms937 := xs934
	p.consumeLiteral(")")
	_t1708 := &pb.Atom{Name: relation_id933, Terms: terms937}
	result939 := _t1708
	p.recordSpan(int(span_start938), "Atom")
	return result939
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start945 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1709 := p.parse_name()
	name940 := _t1709
	xs941 := []*pb.Term{}
	cond942 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond942 {
		_t1710 := p.parse_term()
		item943 := _t1710
		xs941 = append(xs941, item943)
		cond942 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms944 := xs941
	p.consumeLiteral(")")
	_t1711 := &pb.Pragma{Name: name940, Terms: terms944}
	result946 := _t1711
	p.recordSpan(int(span_start945), "Pragma")
	return result946
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start962 := int64(p.spanStart())
	var _t1712 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1713 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1713 = 9
		} else {
			var _t1714 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1714 = 4
			} else {
				var _t1715 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1715 = 3
				} else {
					var _t1716 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1716 = 0
					} else {
						var _t1717 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1717 = 2
						} else {
							var _t1718 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1718 = 1
							} else {
								var _t1719 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1719 = 8
								} else {
									var _t1720 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1720 = 6
									} else {
										var _t1721 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1721 = 5
										} else {
											var _t1722 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1722 = 7
											} else {
												_t1722 = -1
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
			}
			_t1713 = _t1714
		}
		_t1712 = _t1713
	} else {
		_t1712 = -1
	}
	prediction947 := _t1712
	var _t1723 *pb.Primitive
	if prediction947 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1724 := p.parse_name()
		name957 := _t1724
		xs958 := []*pb.RelTerm{}
		cond959 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond959 {
			_t1725 := p.parse_rel_term()
			item960 := _t1725
			xs958 = append(xs958, item960)
			cond959 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms961 := xs958
		p.consumeLiteral(")")
		_t1726 := &pb.Primitive{Name: name957, Terms: rel_terms961}
		_t1723 = _t1726
	} else {
		var _t1727 *pb.Primitive
		if prediction947 == 8 {
			_t1728 := p.parse_divide()
			divide956 := _t1728
			_t1727 = divide956
		} else {
			var _t1729 *pb.Primitive
			if prediction947 == 7 {
				_t1730 := p.parse_multiply()
				multiply955 := _t1730
				_t1729 = multiply955
			} else {
				var _t1731 *pb.Primitive
				if prediction947 == 6 {
					_t1732 := p.parse_minus()
					minus954 := _t1732
					_t1731 = minus954
				} else {
					var _t1733 *pb.Primitive
					if prediction947 == 5 {
						_t1734 := p.parse_add()
						add953 := _t1734
						_t1733 = add953
					} else {
						var _t1735 *pb.Primitive
						if prediction947 == 4 {
							_t1736 := p.parse_gt_eq()
							gt_eq952 := _t1736
							_t1735 = gt_eq952
						} else {
							var _t1737 *pb.Primitive
							if prediction947 == 3 {
								_t1738 := p.parse_gt()
								gt951 := _t1738
								_t1737 = gt951
							} else {
								var _t1739 *pb.Primitive
								if prediction947 == 2 {
									_t1740 := p.parse_lt_eq()
									lt_eq950 := _t1740
									_t1739 = lt_eq950
								} else {
									var _t1741 *pb.Primitive
									if prediction947 == 1 {
										_t1742 := p.parse_lt()
										lt949 := _t1742
										_t1741 = lt949
									} else {
										var _t1743 *pb.Primitive
										if prediction947 == 0 {
											_t1744 := p.parse_eq()
											eq948 := _t1744
											_t1743 = eq948
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1727 = _t1729
		}
		_t1723 = _t1727
	}
	result963 := _t1723
	p.recordSpan(int(span_start962), "Primitive")
	return result963
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start966 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1745 := p.parse_term()
	term964 := _t1745
	_t1746 := p.parse_term()
	term_3965 := _t1746
	p.consumeLiteral(")")
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term964}
	_t1748 := &pb.RelTerm{}
	_t1748.RelTermType = &pb.RelTerm_Term{Term: term_3965}
	_t1749 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1747, _t1748}}
	result967 := _t1749
	p.recordSpan(int(span_start966), "Primitive")
	return result967
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1750 := p.parse_term()
	term968 := _t1750
	_t1751 := p.parse_term()
	term_3969 := _t1751
	p.consumeLiteral(")")
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term968}
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term_3969}
	_t1754 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1752, _t1753}}
	result971 := _t1754
	p.recordSpan(int(span_start970), "Primitive")
	return result971
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1755 := p.parse_term()
	term972 := _t1755
	_t1756 := p.parse_term()
	term_3973 := _t1756
	p.consumeLiteral(")")
	_t1757 := &pb.RelTerm{}
	_t1757.RelTermType = &pb.RelTerm_Term{Term: term972}
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term_3973}
	_t1759 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1757, _t1758}}
	result975 := _t1759
	p.recordSpan(int(span_start974), "Primitive")
	return result975
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start978 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1760 := p.parse_term()
	term976 := _t1760
	_t1761 := p.parse_term()
	term_3977 := _t1761
	p.consumeLiteral(")")
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term976}
	_t1763 := &pb.RelTerm{}
	_t1763.RelTermType = &pb.RelTerm_Term{Term: term_3977}
	_t1764 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1762, _t1763}}
	result979 := _t1764
	p.recordSpan(int(span_start978), "Primitive")
	return result979
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start982 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1765 := p.parse_term()
	term980 := _t1765
	_t1766 := p.parse_term()
	term_3981 := _t1766
	p.consumeLiteral(")")
	_t1767 := &pb.RelTerm{}
	_t1767.RelTermType = &pb.RelTerm_Term{Term: term980}
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term_3981}
	_t1769 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1767, _t1768}}
	result983 := _t1769
	p.recordSpan(int(span_start982), "Primitive")
	return result983
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start987 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1770 := p.parse_term()
	term984 := _t1770
	_t1771 := p.parse_term()
	term_3985 := _t1771
	_t1772 := p.parse_term()
	term_4986 := _t1772
	p.consumeLiteral(")")
	_t1773 := &pb.RelTerm{}
	_t1773.RelTermType = &pb.RelTerm_Term{Term: term984}
	_t1774 := &pb.RelTerm{}
	_t1774.RelTermType = &pb.RelTerm_Term{Term: term_3985}
	_t1775 := &pb.RelTerm{}
	_t1775.RelTermType = &pb.RelTerm_Term{Term: term_4986}
	_t1776 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1773, _t1774, _t1775}}
	result988 := _t1776
	p.recordSpan(int(span_start987), "Primitive")
	return result988
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start992 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1777 := p.parse_term()
	term989 := _t1777
	_t1778 := p.parse_term()
	term_3990 := _t1778
	_t1779 := p.parse_term()
	term_4991 := _t1779
	p.consumeLiteral(")")
	_t1780 := &pb.RelTerm{}
	_t1780.RelTermType = &pb.RelTerm_Term{Term: term989}
	_t1781 := &pb.RelTerm{}
	_t1781.RelTermType = &pb.RelTerm_Term{Term: term_3990}
	_t1782 := &pb.RelTerm{}
	_t1782.RelTermType = &pb.RelTerm_Term{Term: term_4991}
	_t1783 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1780, _t1781, _t1782}}
	result993 := _t1783
	p.recordSpan(int(span_start992), "Primitive")
	return result993
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start997 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1784 := p.parse_term()
	term994 := _t1784
	_t1785 := p.parse_term()
	term_3995 := _t1785
	_t1786 := p.parse_term()
	term_4996 := _t1786
	p.consumeLiteral(")")
	_t1787 := &pb.RelTerm{}
	_t1787.RelTermType = &pb.RelTerm_Term{Term: term994}
	_t1788 := &pb.RelTerm{}
	_t1788.RelTermType = &pb.RelTerm_Term{Term: term_3995}
	_t1789 := &pb.RelTerm{}
	_t1789.RelTermType = &pb.RelTerm_Term{Term: term_4996}
	_t1790 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1787, _t1788, _t1789}}
	result998 := _t1790
	p.recordSpan(int(span_start997), "Primitive")
	return result998
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1791 := p.parse_term()
	term999 := _t1791
	_t1792 := p.parse_term()
	term_31000 := _t1792
	_t1793 := p.parse_term()
	term_41001 := _t1793
	p.consumeLiteral(")")
	_t1794 := &pb.RelTerm{}
	_t1794.RelTermType = &pb.RelTerm_Term{Term: term999}
	_t1795 := &pb.RelTerm{}
	_t1795.RelTermType = &pb.RelTerm_Term{Term: term_31000}
	_t1796 := &pb.RelTerm{}
	_t1796.RelTermType = &pb.RelTerm_Term{Term: term_41001}
	_t1797 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1794, _t1795, _t1796}}
	result1003 := _t1797
	p.recordSpan(int(span_start1002), "Primitive")
	return result1003
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1007 := int64(p.spanStart())
	var _t1798 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1798 = 1
	} else {
		var _t1799 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1799 = 1
		} else {
			var _t1800 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1800 = 1
			} else {
				var _t1801 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1801 = 1
				} else {
					var _t1802 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1802 = 0
					} else {
						var _t1803 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1803 = 1
						} else {
							var _t1804 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1804 = 1
							} else {
								var _t1805 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1805 = 1
								} else {
									var _t1806 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1806 = 1
									} else {
										var _t1807 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1807 = 1
										} else {
											var _t1808 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1808 = 1
											} else {
												var _t1809 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1809 = 1
												} else {
													var _t1810 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1810 = 1
													} else {
														var _t1811 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1811 = 1
														} else {
															var _t1812 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1812 = 1
															} else {
																_t1812 = -1
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
			_t1799 = _t1800
		}
		_t1798 = _t1799
	}
	prediction1004 := _t1798
	var _t1813 *pb.RelTerm
	if prediction1004 == 1 {
		_t1814 := p.parse_term()
		term1006 := _t1814
		_t1815 := &pb.RelTerm{}
		_t1815.RelTermType = &pb.RelTerm_Term{Term: term1006}
		_t1813 = _t1815
	} else {
		var _t1816 *pb.RelTerm
		if prediction1004 == 0 {
			_t1817 := p.parse_specialized_value()
			specialized_value1005 := _t1817
			_t1818 := &pb.RelTerm{}
			_t1818.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1005}
			_t1816 = _t1818
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1813 = _t1816
	}
	result1008 := _t1813
	p.recordSpan(int(span_start1007), "RelTerm")
	return result1008
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1010 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1819 := p.parse_raw_value()
	raw_value1009 := _t1819
	result1011 := raw_value1009
	p.recordSpan(int(span_start1010), "Value")
	return result1011
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1820 := p.parse_name()
	name1012 := _t1820
	xs1013 := []*pb.RelTerm{}
	cond1014 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1014 {
		_t1821 := p.parse_rel_term()
		item1015 := _t1821
		xs1013 = append(xs1013, item1015)
		cond1014 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1016 := xs1013
	p.consumeLiteral(")")
	_t1822 := &pb.RelAtom{Name: name1012, Terms: rel_terms1016}
	result1018 := _t1822
	p.recordSpan(int(span_start1017), "RelAtom")
	return result1018
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1823 := p.parse_term()
	term1019 := _t1823
	_t1824 := p.parse_term()
	term_31020 := _t1824
	p.consumeLiteral(")")
	_t1825 := &pb.Cast{Input: term1019, Result: term_31020}
	result1022 := _t1825
	p.recordSpan(int(span_start1021), "Cast")
	return result1022
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1023 := []*pb.Attribute{}
	cond1024 := p.matchLookaheadLiteral("(", 0)
	for cond1024 {
		_t1826 := p.parse_attribute()
		item1025 := _t1826
		xs1023 = append(xs1023, item1025)
		cond1024 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1026 := xs1023
	p.consumeLiteral(")")
	return attributes1026
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1827 := p.parse_name()
	name1027 := _t1827
	xs1028 := []*pb.Value{}
	cond1029 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1029 {
		_t1828 := p.parse_raw_value()
		item1030 := _t1828
		xs1028 = append(xs1028, item1030)
		cond1029 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1031 := xs1028
	p.consumeLiteral(")")
	_t1829 := &pb.Attribute{Name: name1027, Args: raw_values1031}
	result1033 := _t1829
	p.recordSpan(int(span_start1032), "Attribute")
	return result1033
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1034 := []*pb.RelationId{}
	cond1035 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1035 {
		_t1830 := p.parse_relation_id()
		item1036 := _t1830
		xs1034 = append(xs1034, item1036)
		cond1035 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1037 := xs1034
	_t1831 := p.parse_script()
	script1038 := _t1831
	var _t1832 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1833 := p.parse_attrs()
		_t1832 = _t1833
	}
	attrs1039 := _t1832
	p.consumeLiteral(")")
	_t1834 := attrs1039
	if attrs1039 == nil {
		_t1834 = []*pb.Attribute{}
	}
	_t1835 := &pb.Algorithm{Global: relation_ids1037, Body: script1038, Attrs: _t1834}
	result1041 := _t1835
	p.recordSpan(int(span_start1040), "Algorithm")
	return result1041
}

func (p *Parser) parse_script() *pb.Script {
	span_start1046 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1042 := []*pb.Construct{}
	cond1043 := p.matchLookaheadLiteral("(", 0)
	for cond1043 {
		_t1836 := p.parse_construct()
		item1044 := _t1836
		xs1042 = append(xs1042, item1044)
		cond1043 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1045 := xs1042
	p.consumeLiteral(")")
	_t1837 := &pb.Script{Constructs: constructs1045}
	result1047 := _t1837
	p.recordSpan(int(span_start1046), "Script")
	return result1047
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1051 := int64(p.spanStart())
	var _t1838 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1839 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1839 = 1
		} else {
			var _t1840 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1840 = 1
			} else {
				var _t1841 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1841 = 1
				} else {
					var _t1842 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1842 = 0
					} else {
						var _t1843 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1843 = 1
						} else {
							var _t1844 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1844 = 1
							} else {
								_t1844 = -1
							}
							_t1843 = _t1844
						}
						_t1842 = _t1843
					}
					_t1841 = _t1842
				}
				_t1840 = _t1841
			}
			_t1839 = _t1840
		}
		_t1838 = _t1839
	} else {
		_t1838 = -1
	}
	prediction1048 := _t1838
	var _t1845 *pb.Construct
	if prediction1048 == 1 {
		_t1846 := p.parse_instruction()
		instruction1050 := _t1846
		_t1847 := &pb.Construct{}
		_t1847.ConstructType = &pb.Construct_Instruction{Instruction: instruction1050}
		_t1845 = _t1847
	} else {
		var _t1848 *pb.Construct
		if prediction1048 == 0 {
			_t1849 := p.parse_loop()
			loop1049 := _t1849
			_t1850 := &pb.Construct{}
			_t1850.ConstructType = &pb.Construct_Loop{Loop: loop1049}
			_t1848 = _t1850
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1845 = _t1848
	}
	result1052 := _t1845
	p.recordSpan(int(span_start1051), "Construct")
	return result1052
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1056 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1851 := p.parse_init()
	init1053 := _t1851
	_t1852 := p.parse_script()
	script1054 := _t1852
	var _t1853 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1854 := p.parse_attrs()
		_t1853 = _t1854
	}
	attrs1055 := _t1853
	p.consumeLiteral(")")
	_t1855 := attrs1055
	if attrs1055 == nil {
		_t1855 = []*pb.Attribute{}
	}
	_t1856 := &pb.Loop{Init: init1053, Body: script1054, Attrs: _t1855}
	result1057 := _t1856
	p.recordSpan(int(span_start1056), "Loop")
	return result1057
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1058 := []*pb.Instruction{}
	cond1059 := p.matchLookaheadLiteral("(", 0)
	for cond1059 {
		_t1857 := p.parse_instruction()
		item1060 := _t1857
		xs1058 = append(xs1058, item1060)
		cond1059 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1061 := xs1058
	p.consumeLiteral(")")
	return instructions1061
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1068 := int64(p.spanStart())
	var _t1858 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1859 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1859 = 1
		} else {
			var _t1860 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1860 = 4
			} else {
				var _t1861 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1861 = 3
				} else {
					var _t1862 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1862 = 2
					} else {
						var _t1863 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1863 = 0
						} else {
							_t1863 = -1
						}
						_t1862 = _t1863
					}
					_t1861 = _t1862
				}
				_t1860 = _t1861
			}
			_t1859 = _t1860
		}
		_t1858 = _t1859
	} else {
		_t1858 = -1
	}
	prediction1062 := _t1858
	var _t1864 *pb.Instruction
	if prediction1062 == 4 {
		_t1865 := p.parse_monus_def()
		monus_def1067 := _t1865
		_t1866 := &pb.Instruction{}
		_t1866.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1067}
		_t1864 = _t1866
	} else {
		var _t1867 *pb.Instruction
		if prediction1062 == 3 {
			_t1868 := p.parse_monoid_def()
			monoid_def1066 := _t1868
			_t1869 := &pb.Instruction{}
			_t1869.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1066}
			_t1867 = _t1869
		} else {
			var _t1870 *pb.Instruction
			if prediction1062 == 2 {
				_t1871 := p.parse_break()
				break1065 := _t1871
				_t1872 := &pb.Instruction{}
				_t1872.InstrType = &pb.Instruction_Break{Break: break1065}
				_t1870 = _t1872
			} else {
				var _t1873 *pb.Instruction
				if prediction1062 == 1 {
					_t1874 := p.parse_upsert()
					upsert1064 := _t1874
					_t1875 := &pb.Instruction{}
					_t1875.InstrType = &pb.Instruction_Upsert{Upsert: upsert1064}
					_t1873 = _t1875
				} else {
					var _t1876 *pb.Instruction
					if prediction1062 == 0 {
						_t1877 := p.parse_assign()
						assign1063 := _t1877
						_t1878 := &pb.Instruction{}
						_t1878.InstrType = &pb.Instruction_Assign{Assign: assign1063}
						_t1876 = _t1878
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1873 = _t1876
				}
				_t1870 = _t1873
			}
			_t1867 = _t1870
		}
		_t1864 = _t1867
	}
	result1069 := _t1864
	p.recordSpan(int(span_start1068), "Instruction")
	return result1069
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1073 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1879 := p.parse_relation_id()
	relation_id1070 := _t1879
	_t1880 := p.parse_abstraction()
	abstraction1071 := _t1880
	var _t1881 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1882 := p.parse_attrs()
		_t1881 = _t1882
	}
	attrs1072 := _t1881
	p.consumeLiteral(")")
	_t1883 := attrs1072
	if attrs1072 == nil {
		_t1883 = []*pb.Attribute{}
	}
	_t1884 := &pb.Assign{Name: relation_id1070, Body: abstraction1071, Attrs: _t1883}
	result1074 := _t1884
	p.recordSpan(int(span_start1073), "Assign")
	return result1074
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1078 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1885 := p.parse_relation_id()
	relation_id1075 := _t1885
	_t1886 := p.parse_abstraction_with_arity()
	abstraction_with_arity1076 := _t1886
	var _t1887 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1888 := p.parse_attrs()
		_t1887 = _t1888
	}
	attrs1077 := _t1887
	p.consumeLiteral(")")
	_t1889 := attrs1077
	if attrs1077 == nil {
		_t1889 = []*pb.Attribute{}
	}
	_t1890 := &pb.Upsert{Name: relation_id1075, Body: abstraction_with_arity1076[0].(*pb.Abstraction), Attrs: _t1889, ValueArity: abstraction_with_arity1076[1].(int64)}
	result1079 := _t1890
	p.recordSpan(int(span_start1078), "Upsert")
	return result1079
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1891 := p.parse_bindings()
	bindings1080 := _t1891
	_t1892 := p.parse_formula()
	formula1081 := _t1892
	p.consumeLiteral(")")
	_t1893 := &pb.Abstraction{Vars: listConcat(bindings1080[0].([]*pb.Binding), bindings1080[1].([]*pb.Binding)), Value: formula1081}
	return []interface{}{_t1893, int64(len(bindings1080[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1085 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1894 := p.parse_relation_id()
	relation_id1082 := _t1894
	_t1895 := p.parse_abstraction()
	abstraction1083 := _t1895
	var _t1896 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1897 := p.parse_attrs()
		_t1896 = _t1897
	}
	attrs1084 := _t1896
	p.consumeLiteral(")")
	_t1898 := attrs1084
	if attrs1084 == nil {
		_t1898 = []*pb.Attribute{}
	}
	_t1899 := &pb.Break{Name: relation_id1082, Body: abstraction1083, Attrs: _t1898}
	result1086 := _t1899
	p.recordSpan(int(span_start1085), "Break")
	return result1086
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1091 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1900 := p.parse_monoid()
	monoid1087 := _t1900
	_t1901 := p.parse_relation_id()
	relation_id1088 := _t1901
	_t1902 := p.parse_abstraction_with_arity()
	abstraction_with_arity1089 := _t1902
	var _t1903 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1904 := p.parse_attrs()
		_t1903 = _t1904
	}
	attrs1090 := _t1903
	p.consumeLiteral(")")
	_t1905 := attrs1090
	if attrs1090 == nil {
		_t1905 = []*pb.Attribute{}
	}
	_t1906 := &pb.MonoidDef{Monoid: monoid1087, Name: relation_id1088, Body: abstraction_with_arity1089[0].(*pb.Abstraction), Attrs: _t1905, ValueArity: abstraction_with_arity1089[1].(int64)}
	result1092 := _t1906
	p.recordSpan(int(span_start1091), "MonoidDef")
	return result1092
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1098 := int64(p.spanStart())
	var _t1907 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1908 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1908 = 3
		} else {
			var _t1909 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1909 = 0
			} else {
				var _t1910 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1910 = 1
				} else {
					var _t1911 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1911 = 2
					} else {
						_t1911 = -1
					}
					_t1910 = _t1911
				}
				_t1909 = _t1910
			}
			_t1908 = _t1909
		}
		_t1907 = _t1908
	} else {
		_t1907 = -1
	}
	prediction1093 := _t1907
	var _t1912 *pb.Monoid
	if prediction1093 == 3 {
		_t1913 := p.parse_sum_monoid()
		sum_monoid1097 := _t1913
		_t1914 := &pb.Monoid{}
		_t1914.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1097}
		_t1912 = _t1914
	} else {
		var _t1915 *pb.Monoid
		if prediction1093 == 2 {
			_t1916 := p.parse_max_monoid()
			max_monoid1096 := _t1916
			_t1917 := &pb.Monoid{}
			_t1917.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1096}
			_t1915 = _t1917
		} else {
			var _t1918 *pb.Monoid
			if prediction1093 == 1 {
				_t1919 := p.parse_min_monoid()
				min_monoid1095 := _t1919
				_t1920 := &pb.Monoid{}
				_t1920.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1095}
				_t1918 = _t1920
			} else {
				var _t1921 *pb.Monoid
				if prediction1093 == 0 {
					_t1922 := p.parse_or_monoid()
					or_monoid1094 := _t1922
					_t1923 := &pb.Monoid{}
					_t1923.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1094}
					_t1921 = _t1923
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1918 = _t1921
			}
			_t1915 = _t1918
		}
		_t1912 = _t1915
	}
	result1099 := _t1912
	p.recordSpan(int(span_start1098), "Monoid")
	return result1099
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1924 := &pb.OrMonoid{}
	result1101 := _t1924
	p.recordSpan(int(span_start1100), "OrMonoid")
	return result1101
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1925 := p.parse_type()
	type1102 := _t1925
	p.consumeLiteral(")")
	_t1926 := &pb.MinMonoid{Type: type1102}
	result1104 := _t1926
	p.recordSpan(int(span_start1103), "MinMonoid")
	return result1104
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1106 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1927 := p.parse_type()
	type1105 := _t1927
	p.consumeLiteral(")")
	_t1928 := &pb.MaxMonoid{Type: type1105}
	result1107 := _t1928
	p.recordSpan(int(span_start1106), "MaxMonoid")
	return result1107
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1929 := p.parse_type()
	type1108 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.SumMonoid{Type: type1108}
	result1110 := _t1930
	p.recordSpan(int(span_start1109), "SumMonoid")
	return result1110
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1115 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1931 := p.parse_monoid()
	monoid1111 := _t1931
	_t1932 := p.parse_relation_id()
	relation_id1112 := _t1932
	_t1933 := p.parse_abstraction_with_arity()
	abstraction_with_arity1113 := _t1933
	var _t1934 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1935 := p.parse_attrs()
		_t1934 = _t1935
	}
	attrs1114 := _t1934
	p.consumeLiteral(")")
	_t1936 := attrs1114
	if attrs1114 == nil {
		_t1936 = []*pb.Attribute{}
	}
	_t1937 := &pb.MonusDef{Monoid: monoid1111, Name: relation_id1112, Body: abstraction_with_arity1113[0].(*pb.Abstraction), Attrs: _t1936, ValueArity: abstraction_with_arity1113[1].(int64)}
	result1116 := _t1937
	p.recordSpan(int(span_start1115), "MonusDef")
	return result1116
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1938 := p.parse_relation_id()
	relation_id1117 := _t1938
	_t1939 := p.parse_abstraction()
	abstraction1118 := _t1939
	_t1940 := p.parse_functional_dependency_keys()
	functional_dependency_keys1119 := _t1940
	_t1941 := p.parse_functional_dependency_values()
	functional_dependency_values1120 := _t1941
	p.consumeLiteral(")")
	_t1942 := &pb.FunctionalDependency{Guard: abstraction1118, Keys: functional_dependency_keys1119, Values: functional_dependency_values1120}
	_t1943 := &pb.Constraint{Name: relation_id1117}
	_t1943.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1942}
	result1122 := _t1943
	p.recordSpan(int(span_start1121), "Constraint")
	return result1122
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1123 := []*pb.Var{}
	cond1124 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1124 {
		_t1944 := p.parse_var()
		item1125 := _t1944
		xs1123 = append(xs1123, item1125)
		cond1124 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1126 := xs1123
	p.consumeLiteral(")")
	return vars1126
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1127 := []*pb.Var{}
	cond1128 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1128 {
		_t1945 := p.parse_var()
		item1129 := _t1945
		xs1127 = append(xs1127, item1129)
		cond1128 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1130 := xs1127
	p.consumeLiteral(")")
	return vars1130
}

func (p *Parser) parse_data() *pb.Data {
	span_start1136 := int64(p.spanStart())
	var _t1946 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1947 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1947 = 3
		} else {
			var _t1948 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1948 = 0
			} else {
				var _t1949 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1949 = 2
				} else {
					var _t1950 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1950 = 1
					} else {
						_t1950 = -1
					}
					_t1949 = _t1950
				}
				_t1948 = _t1949
			}
			_t1947 = _t1948
		}
		_t1946 = _t1947
	} else {
		_t1946 = -1
	}
	prediction1131 := _t1946
	var _t1951 *pb.Data
	if prediction1131 == 3 {
		_t1952 := p.parse_iceberg_data()
		iceberg_data1135 := _t1952
		_t1953 := &pb.Data{}
		_t1953.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1135}
		_t1951 = _t1953
	} else {
		var _t1954 *pb.Data
		if prediction1131 == 2 {
			_t1955 := p.parse_csv_data()
			csv_data1134 := _t1955
			_t1956 := &pb.Data{}
			_t1956.DataType = &pb.Data_CsvData{CsvData: csv_data1134}
			_t1954 = _t1956
		} else {
			var _t1957 *pb.Data
			if prediction1131 == 1 {
				_t1958 := p.parse_betree_relation()
				betree_relation1133 := _t1958
				_t1959 := &pb.Data{}
				_t1959.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1133}
				_t1957 = _t1959
			} else {
				var _t1960 *pb.Data
				if prediction1131 == 0 {
					_t1961 := p.parse_edb()
					edb1132 := _t1961
					_t1962 := &pb.Data{}
					_t1962.DataType = &pb.Data_Edb{Edb: edb1132}
					_t1960 = _t1962
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1957 = _t1960
			}
			_t1954 = _t1957
		}
		_t1951 = _t1954
	}
	result1137 := _t1951
	p.recordSpan(int(span_start1136), "Data")
	return result1137
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1141 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1963 := p.parse_relation_id()
	relation_id1138 := _t1963
	_t1964 := p.parse_edb_path()
	edb_path1139 := _t1964
	_t1965 := p.parse_edb_types()
	edb_types1140 := _t1965
	p.consumeLiteral(")")
	_t1966 := &pb.EDB{TargetId: relation_id1138, Path: edb_path1139, Types: edb_types1140}
	result1142 := _t1966
	p.recordSpan(int(span_start1141), "EDB")
	return result1142
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1143 := []string{}
	cond1144 := p.matchLookaheadTerminal("STRING", 0)
	for cond1144 {
		item1145 := p.consumeTerminal("STRING").Value.str
		xs1143 = append(xs1143, item1145)
		cond1144 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1146 := xs1143
	p.consumeLiteral("]")
	return strings1146
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1147 := []*pb.Type{}
	cond1148 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1148 {
		_t1967 := p.parse_type()
		item1149 := _t1967
		xs1147 = append(xs1147, item1149)
		cond1148 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1150 := xs1147
	p.consumeLiteral("]")
	return types1150
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1153 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1968 := p.parse_relation_id()
	relation_id1151 := _t1968
	_t1969 := p.parse_betree_info()
	betree_info1152 := _t1969
	p.consumeLiteral(")")
	_t1970 := &pb.BeTreeRelation{Name: relation_id1151, RelationInfo: betree_info1152}
	result1154 := _t1970
	p.recordSpan(int(span_start1153), "BeTreeRelation")
	return result1154
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1158 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1971 := p.parse_betree_info_key_types()
	betree_info_key_types1155 := _t1971
	_t1972 := p.parse_betree_info_value_types()
	betree_info_value_types1156 := _t1972
	_t1973 := p.parse_config_dict()
	config_dict1157 := _t1973
	p.consumeLiteral(")")
	_t1974 := p.construct_betree_info(betree_info_key_types1155, betree_info_value_types1156, config_dict1157)
	result1159 := _t1974
	p.recordSpan(int(span_start1158), "BeTreeInfo")
	return result1159
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1160 := []*pb.Type{}
	cond1161 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1161 {
		_t1975 := p.parse_type()
		item1162 := _t1975
		xs1160 = append(xs1160, item1162)
		cond1161 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1163 := xs1160
	p.consumeLiteral(")")
	return types1163
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1164 := []*pb.Type{}
	cond1165 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1165 {
		_t1976 := p.parse_type()
		item1166 := _t1976
		xs1164 = append(xs1164, item1166)
		cond1165 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1167 := xs1164
	p.consumeLiteral(")")
	return types1167
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1172 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1977 := p.parse_csvlocator()
	csvlocator1168 := _t1977
	_t1978 := p.parse_csv_config()
	csv_config1169 := _t1978
	_t1979 := p.parse_gnf_columns()
	gnf_columns1170 := _t1979
	_t1980 := p.parse_csv_asof()
	csv_asof1171 := _t1980
	p.consumeLiteral(")")
	_t1981 := &pb.CSVData{Locator: csvlocator1168, Config: csv_config1169, Columns: gnf_columns1170, Asof: csv_asof1171}
	result1173 := _t1981
	p.recordSpan(int(span_start1172), "CSVData")
	return result1173
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1176 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1982 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1983 := p.parse_csv_locator_paths()
		_t1982 = _t1983
	}
	csv_locator_paths1174 := _t1982
	var _t1984 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1985 := p.parse_csv_locator_inline_data()
		_t1984 = ptr(_t1985)
	}
	csv_locator_inline_data1175 := _t1984
	p.consumeLiteral(")")
	_t1986 := csv_locator_paths1174
	if csv_locator_paths1174 == nil {
		_t1986 = []string{}
	}
	_t1987 := &pb.CSVLocator{Paths: _t1986, InlineData: []byte(deref(csv_locator_inline_data1175, ""))}
	result1177 := _t1987
	p.recordSpan(int(span_start1176), "CSVLocator")
	return result1177
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1178 := []string{}
	cond1179 := p.matchLookaheadTerminal("STRING", 0)
	for cond1179 {
		item1180 := p.consumeTerminal("STRING").Value.str
		xs1178 = append(xs1178, item1180)
		cond1179 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1181 := xs1178
	p.consumeLiteral(")")
	return strings1181
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1182 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1182
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1184 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1988 := p.parse_config_dict()
	config_dict1183 := _t1988
	p.consumeLiteral(")")
	_t1989 := p.construct_csv_config(config_dict1183)
	result1185 := _t1989
	p.recordSpan(int(span_start1184), "CSVConfig")
	return result1185
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1186 := []*pb.GNFColumn{}
	cond1187 := p.matchLookaheadLiteral("(", 0)
	for cond1187 {
		_t1990 := p.parse_gnf_column()
		item1188 := _t1990
		xs1186 = append(xs1186, item1188)
		cond1187 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1189 := xs1186
	p.consumeLiteral(")")
	return gnf_columns1189
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1196 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1991 := p.parse_gnf_column_path()
	gnf_column_path1190 := _t1991
	var _t1992 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1993 := p.parse_relation_id()
		_t1992 = _t1993
	}
	relation_id1191 := _t1992
	p.consumeLiteral("[")
	xs1192 := []*pb.Type{}
	cond1193 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1193 {
		_t1994 := p.parse_type()
		item1194 := _t1994
		xs1192 = append(xs1192, item1194)
		cond1193 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1195 := xs1192
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1995 := &pb.GNFColumn{ColumnPath: gnf_column_path1190, TargetId: relation_id1191, Types: types1195}
	result1197 := _t1995
	p.recordSpan(int(span_start1196), "GNFColumn")
	return result1197
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1996 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1996 = 1
	} else {
		var _t1997 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1997 = 0
		} else {
			_t1997 = -1
		}
		_t1996 = _t1997
	}
	prediction1198 := _t1996
	var _t1998 []string
	if prediction1198 == 1 {
		p.consumeLiteral("[")
		xs1200 := []string{}
		cond1201 := p.matchLookaheadTerminal("STRING", 0)
		for cond1201 {
			item1202 := p.consumeTerminal("STRING").Value.str
			xs1200 = append(xs1200, item1202)
			cond1201 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1203 := xs1200
		p.consumeLiteral("]")
		_t1998 = strings1203
	} else {
		var _t1999 []string
		if prediction1198 == 0 {
			string1199 := p.consumeTerminal("STRING").Value.str
			_ = string1199
			_t1999 = []string{string1199}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1998 = _t1999
	}
	return _t1998
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1204 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1204
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2000 := p.parse_iceberg_locator()
	iceberg_locator1205 := _t2000
	_t2001 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1206 := _t2001
	var _t2002 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t2003 := p.parse_gnf_columns()
		_t2002 = _t2003
	}
	gnf_columns1207 := _t2002
	var _t2004 *pb.IcebergTarget
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("full_table", 1)) {
		_t2005 := p.parse_full_table()
		_t2004 = _t2005
	}
	full_table1208 := _t2004
	var _t2006 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2007 := p.parse_iceberg_from_snapshot()
		_t2006 = ptr(_t2007)
	}
	iceberg_from_snapshot1209 := _t2006
	var _t2008 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2009 := p.parse_iceberg_to_snapshot()
		_t2008 = ptr(_t2009)
	}
	iceberg_to_snapshot1210 := _t2008
	_t2010 := p.parse_boolean_value()
	boolean_value1211 := _t2010
	p.consumeLiteral(")")
	_t2011 := p.construct_iceberg_data(iceberg_locator1205, iceberg_catalog_config1206, gnf_columns1207, full_table1208, iceberg_from_snapshot1209, iceberg_to_snapshot1210, boolean_value1211)
	result1213 := _t2011
	p.recordSpan(int(span_start1212), "IcebergData")
	return result1213
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1217 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2012 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1214 := _t2012
	_t2013 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1215 := _t2013
	_t2014 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1216 := _t2014
	p.consumeLiteral(")")
	_t2015 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1214, Namespace: iceberg_locator_namespace1215, Warehouse: iceberg_locator_warehouse1216}
	result1218 := _t2015
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
	_t2016 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1225 := _t2016
	var _t2017 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2018 := p.parse_iceberg_catalog_config_scope()
		_t2017 = ptr(_t2018)
	}
	iceberg_catalog_config_scope1226 := _t2017
	_t2019 := p.parse_iceberg_properties()
	iceberg_properties1227 := _t2019
	_t2020 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1228 := _t2020
	p.consumeLiteral(")")
	_t2021 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1225, iceberg_catalog_config_scope1226, iceberg_properties1227, iceberg_auth_properties1228)
	result1230 := _t2021
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
		_t2022 := p.parse_iceberg_property_entry()
		item1235 := _t2022
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
		_t2023 := p.parse_iceberg_masked_property_entry()
		item1241 := _t2023
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

func (p *Parser) parse_full_table() *pb.IcebergTarget {
	span_start1250 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("full_table")
	_t2024 := p.parse_relation_id()
	relation_id1245 := _t2024
	p.consumeLiteral("[")
	xs1246 := []*pb.Type{}
	cond1247 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1247 {
		_t2025 := p.parse_type()
		item1248 := _t2025
		xs1246 = append(xs1246, item1248)
		cond1247 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1249 := xs1246
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2026 := &pb.IcebergTarget{TargetId: relation_id1245, Types: types1249}
	result1251 := _t2026
	p.recordSpan(int(span_start1250), "IcebergTarget")
	return result1251
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1252 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1252
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1253 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1253
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2027 := p.parse_fragment_id()
	fragment_id1254 := _t2027
	p.consumeLiteral(")")
	_t2028 := &pb.Undefine{FragmentId: fragment_id1254}
	result1256 := _t2028
	p.recordSpan(int(span_start1255), "Undefine")
	return result1256
}

func (p *Parser) parse_context() *pb.Context {
	span_start1261 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1257 := []*pb.RelationId{}
	cond1258 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1258 {
		_t2029 := p.parse_relation_id()
		item1259 := _t2029
		xs1257 = append(xs1257, item1259)
		cond1258 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1260 := xs1257
	p.consumeLiteral(")")
	_t2030 := &pb.Context{Relations: relation_ids1260}
	result1262 := _t2030
	p.recordSpan(int(span_start1261), "Context")
	return result1262
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1268 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2031 := p.parse_edb_path()
	edb_path1263 := _t2031
	xs1264 := []*pb.SnapshotMapping{}
	cond1265 := p.matchLookaheadLiteral("[", 0)
	for cond1265 {
		_t2032 := p.parse_snapshot_mapping()
		item1266 := _t2032
		xs1264 = append(xs1264, item1266)
		cond1265 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1267 := xs1264
	p.consumeLiteral(")")
	_t2033 := &pb.Snapshot{Prefix: edb_path1263, Mappings: snapshot_mappings1267}
	result1269 := _t2033
	p.recordSpan(int(span_start1268), "Snapshot")
	return result1269
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1272 := int64(p.spanStart())
	_t2034 := p.parse_edb_path()
	edb_path1270 := _t2034
	_t2035 := p.parse_relation_id()
	relation_id1271 := _t2035
	_t2036 := &pb.SnapshotMapping{DestinationPath: edb_path1270, SourceRelation: relation_id1271}
	result1273 := _t2036
	p.recordSpan(int(span_start1272), "SnapshotMapping")
	return result1273
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1274 := []*pb.Read{}
	cond1275 := p.matchLookaheadLiteral("(", 0)
	for cond1275 {
		_t2037 := p.parse_read()
		item1276 := _t2037
		xs1274 = append(xs1274, item1276)
		cond1275 = p.matchLookaheadLiteral("(", 0)
	}
	reads1277 := xs1274
	p.consumeLiteral(")")
	return reads1277
}

func (p *Parser) parse_read() *pb.Read {
	span_start1284 := int64(p.spanStart())
	var _t2038 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2039 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2039 = 2
		} else {
			var _t2040 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2040 = 1
			} else {
				var _t2041 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2041 = 4
				} else {
					var _t2042 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2042 = 4
					} else {
						var _t2043 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2043 = 0
						} else {
							var _t2044 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2044 = 3
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
			}
			_t2039 = _t2040
		}
		_t2038 = _t2039
	} else {
		_t2038 = -1
	}
	prediction1278 := _t2038
	var _t2045 *pb.Read
	if prediction1278 == 4 {
		_t2046 := p.parse_export()
		export1283 := _t2046
		_t2047 := &pb.Read{}
		_t2047.ReadType = &pb.Read_Export{Export: export1283}
		_t2045 = _t2047
	} else {
		var _t2048 *pb.Read
		if prediction1278 == 3 {
			_t2049 := p.parse_abort()
			abort1282 := _t2049
			_t2050 := &pb.Read{}
			_t2050.ReadType = &pb.Read_Abort{Abort: abort1282}
			_t2048 = _t2050
		} else {
			var _t2051 *pb.Read
			if prediction1278 == 2 {
				_t2052 := p.parse_what_if()
				what_if1281 := _t2052
				_t2053 := &pb.Read{}
				_t2053.ReadType = &pb.Read_WhatIf{WhatIf: what_if1281}
				_t2051 = _t2053
			} else {
				var _t2054 *pb.Read
				if prediction1278 == 1 {
					_t2055 := p.parse_output()
					output1280 := _t2055
					_t2056 := &pb.Read{}
					_t2056.ReadType = &pb.Read_Output{Output: output1280}
					_t2054 = _t2056
				} else {
					var _t2057 *pb.Read
					if prediction1278 == 0 {
						_t2058 := p.parse_demand()
						demand1279 := _t2058
						_t2059 := &pb.Read{}
						_t2059.ReadType = &pb.Read_Demand{Demand: demand1279}
						_t2057 = _t2059
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2054 = _t2057
				}
				_t2051 = _t2054
			}
			_t2048 = _t2051
		}
		_t2045 = _t2048
	}
	result1285 := _t2045
	p.recordSpan(int(span_start1284), "Read")
	return result1285
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1287 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2060 := p.parse_relation_id()
	relation_id1286 := _t2060
	p.consumeLiteral(")")
	_t2061 := &pb.Demand{RelationId: relation_id1286}
	result1288 := _t2061
	p.recordSpan(int(span_start1287), "Demand")
	return result1288
}

func (p *Parser) parse_output() *pb.Output {
	span_start1291 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2062 := p.parse_name()
	name1289 := _t2062
	_t2063 := p.parse_relation_id()
	relation_id1290 := _t2063
	p.consumeLiteral(")")
	_t2064 := &pb.Output{Name: name1289, RelationId: relation_id1290}
	result1292 := _t2064
	p.recordSpan(int(span_start1291), "Output")
	return result1292
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1295 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2065 := p.parse_name()
	name1293 := _t2065
	_t2066 := p.parse_epoch()
	epoch1294 := _t2066
	p.consumeLiteral(")")
	_t2067 := &pb.WhatIf{Branch: name1293, Epoch: epoch1294}
	result1296 := _t2067
	p.recordSpan(int(span_start1295), "WhatIf")
	return result1296
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1299 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2068 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2069 := p.parse_name()
		_t2068 = ptr(_t2069)
	}
	name1297 := _t2068
	_t2070 := p.parse_relation_id()
	relation_id1298 := _t2070
	p.consumeLiteral(")")
	_t2071 := &pb.Abort{Name: deref(name1297, "abort"), RelationId: relation_id1298}
	result1300 := _t2071
	p.recordSpan(int(span_start1299), "Abort")
	return result1300
}

func (p *Parser) parse_export() *pb.Export {
	span_start1304 := int64(p.spanStart())
	var _t2072 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2073 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2073 = 1
		} else {
			var _t2074 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2074 = 0
			} else {
				_t2074 = -1
			}
			_t2073 = _t2074
		}
		_t2072 = _t2073
	} else {
		_t2072 = -1
	}
	prediction1301 := _t2072
	var _t2075 *pb.Export
	if prediction1301 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2076 := p.parse_export_iceberg_config()
		export_iceberg_config1303 := _t2076
		p.consumeLiteral(")")
		_t2077 := &pb.Export{}
		_t2077.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1303}
		_t2075 = _t2077
	} else {
		var _t2078 *pb.Export
		if prediction1301 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2079 := p.parse_export_csv_config()
			export_csv_config1302 := _t2079
			p.consumeLiteral(")")
			_t2080 := &pb.Export{}
			_t2080.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1302}
			_t2078 = _t2080
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2075 = _t2078
	}
	result1305 := _t2075
	p.recordSpan(int(span_start1304), "Export")
	return result1305
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1313 := int64(p.spanStart())
	var _t2081 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2082 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2082 = 0
		} else {
			var _t2083 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2083 = 1
			} else {
				_t2083 = -1
			}
			_t2082 = _t2083
		}
		_t2081 = _t2082
	} else {
		_t2081 = -1
	}
	prediction1306 := _t2081
	var _t2084 *pb.ExportCSVConfig
	if prediction1306 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2085 := p.parse_export_csv_path()
		export_csv_path1310 := _t2085
		_t2086 := p.parse_export_csv_columns_list()
		export_csv_columns_list1311 := _t2086
		_t2087 := p.parse_config_dict()
		config_dict1312 := _t2087
		p.consumeLiteral(")")
		_t2088 := p.construct_export_csv_config(export_csv_path1310, export_csv_columns_list1311, config_dict1312)
		_t2084 = _t2088
	} else {
		var _t2089 *pb.ExportCSVConfig
		if prediction1306 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2090 := p.parse_export_csv_path()
			export_csv_path1307 := _t2090
			_t2091 := p.parse_export_csv_source()
			export_csv_source1308 := _t2091
			_t2092 := p.parse_csv_config()
			csv_config1309 := _t2092
			p.consumeLiteral(")")
			_t2093 := p.construct_export_csv_config_with_source(export_csv_path1307, export_csv_source1308, csv_config1309)
			_t2089 = _t2093
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2084 = _t2089
	}
	result1314 := _t2084
	p.recordSpan(int(span_start1313), "ExportCSVConfig")
	return result1314
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1315 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1315
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1322 := int64(p.spanStart())
	var _t2094 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2095 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2095 = 1
		} else {
			var _t2096 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2096 = 0
			} else {
				_t2096 = -1
			}
			_t2095 = _t2096
		}
		_t2094 = _t2095
	} else {
		_t2094 = -1
	}
	prediction1316 := _t2094
	var _t2097 *pb.ExportCSVSource
	if prediction1316 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2098 := p.parse_relation_id()
		relation_id1321 := _t2098
		p.consumeLiteral(")")
		_t2099 := &pb.ExportCSVSource{}
		_t2099.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1321}
		_t2097 = _t2099
	} else {
		var _t2100 *pb.ExportCSVSource
		if prediction1316 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1317 := []*pb.ExportCSVColumn{}
			cond1318 := p.matchLookaheadLiteral("(", 0)
			for cond1318 {
				_t2101 := p.parse_export_csv_column()
				item1319 := _t2101
				xs1317 = append(xs1317, item1319)
				cond1318 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1320 := xs1317
			p.consumeLiteral(")")
			_t2102 := &pb.ExportCSVColumns{Columns: export_csv_columns1320}
			_t2103 := &pb.ExportCSVSource{}
			_t2103.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2102}
			_t2100 = _t2103
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2097 = _t2100
	}
	result1323 := _t2097
	p.recordSpan(int(span_start1322), "ExportCSVSource")
	return result1323
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1326 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1324 := p.consumeTerminal("STRING").Value.str
	_t2104 := p.parse_relation_id()
	relation_id1325 := _t2104
	p.consumeLiteral(")")
	_t2105 := &pb.ExportCSVColumn{ColumnName: string1324, ColumnData: relation_id1325}
	result1327 := _t2105
	p.recordSpan(int(span_start1326), "ExportCSVColumn")
	return result1327
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1328 := []*pb.ExportCSVColumn{}
	cond1329 := p.matchLookaheadLiteral("(", 0)
	for cond1329 {
		_t2106 := p.parse_export_csv_column()
		item1330 := _t2106
		xs1328 = append(xs1328, item1330)
		cond1329 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1331 := xs1328
	p.consumeLiteral(")")
	return export_csv_columns1331
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1337 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2107 := p.parse_iceberg_locator()
	iceberg_locator1332 := _t2107
	_t2108 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1333 := _t2108
	_t2109 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1334 := _t2109
	_t2110 := p.parse_iceberg_table_properties()
	iceberg_table_properties1335 := _t2110
	var _t2111 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2112 := p.parse_config_dict()
		_t2111 = _t2112
	}
	config_dict1336 := _t2111
	p.consumeLiteral(")")
	_t2113 := p.construct_export_iceberg_config_full(iceberg_locator1332, iceberg_catalog_config1333, export_iceberg_table_def1334, iceberg_table_properties1335, config_dict1336)
	result1338 := _t2113
	p.recordSpan(int(span_start1337), "ExportIcebergConfig")
	return result1338
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1340 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2114 := p.parse_relation_id()
	relation_id1339 := _t2114
	p.consumeLiteral(")")
	result1341 := relation_id1339
	p.recordSpan(int(span_start1340), "RelationId")
	return result1341
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1342 := [][]interface{}{}
	cond1343 := p.matchLookaheadLiteral("(", 0)
	for cond1343 {
		_t2115 := p.parse_iceberg_property_entry()
		item1344 := _t2115
		xs1342 = append(xs1342, item1344)
		cond1343 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1345 := xs1342
	p.consumeLiteral(")")
	return iceberg_property_entrys1345
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
