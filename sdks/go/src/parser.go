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
	var _t2129 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2129
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2130 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2130
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2131 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2131
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2132 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2132
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2133 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2133
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2134 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2134
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2135 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2135
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2136 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2136
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2137 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2137
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2138 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2138
	_t2139 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2139
	_t2140 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2140
	_t2141 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2141
	_t2142 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2142
	_t2143 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2143
	_t2144 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2144
	_t2145 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2145
	_t2146 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2146
	_t2147 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2147
	_t2148 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2148
	_t2149 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2149
	_t2150 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2150
	_t2151 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2151
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2152 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2152
	config := dictFromList(storage_integration_opt)
	_t2153 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2154 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2155 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2156 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2157 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2158 := &pb.StorageIntegration{Provider: _t2153, AzureSasToken: _t2154, S3Region: _t2155, S3AccessKeyId: _t2156, S3SecretAccessKey: _t2157}
	return _t2158
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2159 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2159
	_t2160 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2160
	_t2161 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2161
	_t2162 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2162
	_t2163 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2163
	_t2164 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2164
	_t2165 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2165
	_t2166 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2166
	_t2167 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2167
	_t2168 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2168.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2168.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2168
	_t2169 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2169
}

func (p *Parser) default_configure() *pb.Configure {
	_t2170 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2170
	_t2171 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2171
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
	_t2172 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2172
	_t2173 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2173
	_t2174 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2174
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2175 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2175
	_t2176 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2176
	_t2177 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2177
	_t2178 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2178
	_t2179 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2179
	_t2180 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2180
	_t2181 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2181
	_t2182 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2182
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2183 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2183
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2184 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2184
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2185 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2185
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2186 := config_dict
	if config_dict == nil {
		_t2186 = [][]interface{}{}
	}
	cfg := dictFromList(_t2186)
	_t2187 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2187
	_t2188 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2188
	_t2189 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2189
	table_props := stringMapFromPairs(table_property_pairs)
	_t2190 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2190
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start682 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1352 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1353 := p.parse_configure()
		_t1352 = _t1353
	}
	configure676 := _t1352
	var _t1354 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1355 := p.parse_sync()
		_t1354 = _t1355
	}
	sync677 := _t1354
	xs678 := []*pb.Epoch{}
	cond679 := p.matchLookaheadLiteral("(", 0)
	for cond679 {
		_t1356 := p.parse_epoch()
		item680 := _t1356
		xs678 = append(xs678, item680)
		cond679 = p.matchLookaheadLiteral("(", 0)
	}
	epochs681 := xs678
	p.consumeLiteral(")")
	_t1357 := p.default_configure()
	_t1358 := configure676
	if configure676 == nil {
		_t1358 = _t1357
	}
	_t1359 := &pb.Transaction{Epochs: epochs681, Configure: _t1358, Sync: sync677}
	result683 := _t1359
	p.recordSpan(int(span_start682), "Transaction")
	return result683
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start685 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1360 := p.parse_config_dict()
	config_dict684 := _t1360
	p.consumeLiteral(")")
	_t1361 := p.construct_configure(config_dict684)
	result686 := _t1361
	p.recordSpan(int(span_start685), "Configure")
	return result686
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs687 := [][]interface{}{}
	cond688 := p.matchLookaheadLiteral(":", 0)
	for cond688 {
		_t1362 := p.parse_config_key_value()
		item689 := _t1362
		xs687 = append(xs687, item689)
		cond688 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values690 := xs687
	p.consumeLiteral("}")
	return config_key_values690
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol691 := p.consumeTerminal("SYMBOL").Value.str
	_t1363 := p.parse_raw_value()
	raw_value692 := _t1363
	return []interface{}{symbol691, raw_value692}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start706 := int64(p.spanStart())
	var _t1364 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1364 = 12
	} else {
		var _t1365 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1365 = 11
		} else {
			var _t1366 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1366 = 12
			} else {
				var _t1367 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1368 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1368 = 1
					} else {
						var _t1369 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1369 = 0
						} else {
							_t1369 = -1
						}
						_t1368 = _t1369
					}
					_t1367 = _t1368
				} else {
					var _t1370 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1370 = 7
					} else {
						var _t1371 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1371 = 8
						} else {
							var _t1372 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1372 = 2
							} else {
								var _t1373 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1373 = 3
								} else {
									var _t1374 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1374 = 9
									} else {
										var _t1375 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1375 = 4
										} else {
											var _t1376 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1376 = 5
											} else {
												var _t1377 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1377 = 6
												} else {
													var _t1378 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1378 = 10
													} else {
														_t1378 = -1
													}
													_t1377 = _t1378
												}
												_t1376 = _t1377
											}
											_t1375 = _t1376
										}
										_t1374 = _t1375
									}
									_t1373 = _t1374
								}
								_t1372 = _t1373
							}
							_t1371 = _t1372
						}
						_t1370 = _t1371
					}
					_t1367 = _t1370
				}
				_t1366 = _t1367
			}
			_t1365 = _t1366
		}
		_t1364 = _t1365
	}
	prediction693 := _t1364
	var _t1379 *pb.Value
	if prediction693 == 12 {
		_t1380 := p.parse_boolean_value()
		boolean_value705 := _t1380
		_t1381 := &pb.Value{}
		_t1381.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value705}
		_t1379 = _t1381
	} else {
		var _t1382 *pb.Value
		if prediction693 == 11 {
			p.consumeLiteral("missing")
			_t1383 := &pb.MissingValue{}
			_t1384 := &pb.Value{}
			_t1384.Value = &pb.Value_MissingValue{MissingValue: _t1383}
			_t1382 = _t1384
		} else {
			var _t1385 *pb.Value
			if prediction693 == 10 {
				decimal704 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1386 := &pb.Value{}
				_t1386.Value = &pb.Value_DecimalValue{DecimalValue: decimal704}
				_t1385 = _t1386
			} else {
				var _t1387 *pb.Value
				if prediction693 == 9 {
					int128703 := p.consumeTerminal("INT128").Value.int128
					_t1388 := &pb.Value{}
					_t1388.Value = &pb.Value_Int128Value{Int128Value: int128703}
					_t1387 = _t1388
				} else {
					var _t1389 *pb.Value
					if prediction693 == 8 {
						uint128702 := p.consumeTerminal("UINT128").Value.uint128
						_t1390 := &pb.Value{}
						_t1390.Value = &pb.Value_Uint128Value{Uint128Value: uint128702}
						_t1389 = _t1390
					} else {
						var _t1391 *pb.Value
						if prediction693 == 7 {
							uint32701 := p.consumeTerminal("UINT32").Value.u32
							_t1392 := &pb.Value{}
							_t1392.Value = &pb.Value_Uint32Value{Uint32Value: uint32701}
							_t1391 = _t1392
						} else {
							var _t1393 *pb.Value
							if prediction693 == 6 {
								float700 := p.consumeTerminal("FLOAT").Value.f64
								_t1394 := &pb.Value{}
								_t1394.Value = &pb.Value_FloatValue{FloatValue: float700}
								_t1393 = _t1394
							} else {
								var _t1395 *pb.Value
								if prediction693 == 5 {
									float32699 := p.consumeTerminal("FLOAT32").Value.f32
									_t1396 := &pb.Value{}
									_t1396.Value = &pb.Value_Float32Value{Float32Value: float32699}
									_t1395 = _t1396
								} else {
									var _t1397 *pb.Value
									if prediction693 == 4 {
										int698 := p.consumeTerminal("INT").Value.i64
										_t1398 := &pb.Value{}
										_t1398.Value = &pb.Value_IntValue{IntValue: int698}
										_t1397 = _t1398
									} else {
										var _t1399 *pb.Value
										if prediction693 == 3 {
											int32697 := p.consumeTerminal("INT32").Value.i32
											_t1400 := &pb.Value{}
											_t1400.Value = &pb.Value_Int32Value{Int32Value: int32697}
											_t1399 = _t1400
										} else {
											var _t1401 *pb.Value
											if prediction693 == 2 {
												string696 := p.consumeTerminal("STRING").Value.str
												_t1402 := &pb.Value{}
												_t1402.Value = &pb.Value_StringValue{StringValue: string696}
												_t1401 = _t1402
											} else {
												var _t1403 *pb.Value
												if prediction693 == 1 {
													_t1404 := p.parse_raw_datetime()
													raw_datetime695 := _t1404
													_t1405 := &pb.Value{}
													_t1405.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime695}
													_t1403 = _t1405
												} else {
													var _t1406 *pb.Value
													if prediction693 == 0 {
														_t1407 := p.parse_raw_date()
														raw_date694 := _t1407
														_t1408 := &pb.Value{}
														_t1408.Value = &pb.Value_DateValue{DateValue: raw_date694}
														_t1406 = _t1408
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1403 = _t1406
												}
												_t1401 = _t1403
											}
											_t1399 = _t1401
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
			_t1382 = _t1385
		}
		_t1379 = _t1382
	}
	result707 := _t1379
	p.recordSpan(int(span_start706), "Value")
	return result707
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int708 := p.consumeTerminal("INT").Value.i64
	int_3709 := p.consumeTerminal("INT").Value.i64
	int_4710 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1409 := &pb.DateValue{Year: int32(int708), Month: int32(int_3709), Day: int32(int_4710)}
	result712 := _t1409
	p.recordSpan(int(span_start711), "DateValue")
	return result712
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start720 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int713 := p.consumeTerminal("INT").Value.i64
	int_3714 := p.consumeTerminal("INT").Value.i64
	int_4715 := p.consumeTerminal("INT").Value.i64
	int_5716 := p.consumeTerminal("INT").Value.i64
	int_6717 := p.consumeTerminal("INT").Value.i64
	int_7718 := p.consumeTerminal("INT").Value.i64
	var _t1410 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1410 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8719 := _t1410
	p.consumeLiteral(")")
	_t1411 := &pb.DateTimeValue{Year: int32(int713), Month: int32(int_3714), Day: int32(int_4715), Hour: int32(int_5716), Minute: int32(int_6717), Second: int32(int_7718), Microsecond: int32(deref(int_8719, 0))}
	result721 := _t1411
	p.recordSpan(int(span_start720), "DateTimeValue")
	return result721
}

func (p *Parser) parse_boolean_value() bool {
	var _t1412 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1412 = 0
	} else {
		var _t1413 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1413 = 1
		} else {
			_t1413 = -1
		}
		_t1412 = _t1413
	}
	prediction722 := _t1412
	var _t1414 bool
	if prediction722 == 1 {
		p.consumeLiteral("false")
		_t1414 = false
	} else {
		var _t1415 bool
		if prediction722 == 0 {
			p.consumeLiteral("true")
			_t1415 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1414 = _t1415
	}
	return _t1414
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start727 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs723 := []*pb.FragmentId{}
	cond724 := p.matchLookaheadLiteral(":", 0)
	for cond724 {
		_t1416 := p.parse_fragment_id()
		item725 := _t1416
		xs723 = append(xs723, item725)
		cond724 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids726 := xs723
	p.consumeLiteral(")")
	_t1417 := &pb.Sync{Fragments: fragment_ids726}
	result728 := _t1417
	p.recordSpan(int(span_start727), "Sync")
	return result728
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start730 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol729 := p.consumeTerminal("SYMBOL").Value.str
	result731 := &pb.FragmentId{Id: []byte(symbol729)}
	p.recordSpan(int(span_start730), "FragmentId")
	return result731
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start734 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1418 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1419 := p.parse_epoch_writes()
		_t1418 = _t1419
	}
	epoch_writes732 := _t1418
	var _t1420 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1421 := p.parse_epoch_reads()
		_t1420 = _t1421
	}
	epoch_reads733 := _t1420
	p.consumeLiteral(")")
	_t1422 := epoch_writes732
	if epoch_writes732 == nil {
		_t1422 = []*pb.Write{}
	}
	_t1423 := epoch_reads733
	if epoch_reads733 == nil {
		_t1423 = []*pb.Read{}
	}
	_t1424 := &pb.Epoch{Writes: _t1422, Reads: _t1423}
	result735 := _t1424
	p.recordSpan(int(span_start734), "Epoch")
	return result735
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs736 := []*pb.Write{}
	cond737 := p.matchLookaheadLiteral("(", 0)
	for cond737 {
		_t1425 := p.parse_write()
		item738 := _t1425
		xs736 = append(xs736, item738)
		cond737 = p.matchLookaheadLiteral("(", 0)
	}
	writes739 := xs736
	p.consumeLiteral(")")
	return writes739
}

func (p *Parser) parse_write() *pb.Write {
	span_start745 := int64(p.spanStart())
	var _t1426 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1427 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1427 = 1
		} else {
			var _t1428 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1428 = 3
			} else {
				var _t1429 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1429 = 0
				} else {
					var _t1430 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1430 = 2
					} else {
						_t1430 = -1
					}
					_t1429 = _t1430
				}
				_t1428 = _t1429
			}
			_t1427 = _t1428
		}
		_t1426 = _t1427
	} else {
		_t1426 = -1
	}
	prediction740 := _t1426
	var _t1431 *pb.Write
	if prediction740 == 3 {
		_t1432 := p.parse_snapshot()
		snapshot744 := _t1432
		_t1433 := &pb.Write{}
		_t1433.WriteType = &pb.Write_Snapshot{Snapshot: snapshot744}
		_t1431 = _t1433
	} else {
		var _t1434 *pb.Write
		if prediction740 == 2 {
			_t1435 := p.parse_context()
			context743 := _t1435
			_t1436 := &pb.Write{}
			_t1436.WriteType = &pb.Write_Context{Context: context743}
			_t1434 = _t1436
		} else {
			var _t1437 *pb.Write
			if prediction740 == 1 {
				_t1438 := p.parse_undefine()
				undefine742 := _t1438
				_t1439 := &pb.Write{}
				_t1439.WriteType = &pb.Write_Undefine{Undefine: undefine742}
				_t1437 = _t1439
			} else {
				var _t1440 *pb.Write
				if prediction740 == 0 {
					_t1441 := p.parse_define()
					define741 := _t1441
					_t1442 := &pb.Write{}
					_t1442.WriteType = &pb.Write_Define{Define: define741}
					_t1440 = _t1442
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1437 = _t1440
			}
			_t1434 = _t1437
		}
		_t1431 = _t1434
	}
	result746 := _t1431
	p.recordSpan(int(span_start745), "Write")
	return result746
}

func (p *Parser) parse_define() *pb.Define {
	span_start748 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1443 := p.parse_fragment()
	fragment747 := _t1443
	p.consumeLiteral(")")
	_t1444 := &pb.Define{Fragment: fragment747}
	result749 := _t1444
	p.recordSpan(int(span_start748), "Define")
	return result749
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1445 := p.parse_new_fragment_id()
	new_fragment_id750 := _t1445
	xs751 := []*pb.Declaration{}
	cond752 := p.matchLookaheadLiteral("(", 0)
	for cond752 {
		_t1446 := p.parse_declaration()
		item753 := _t1446
		xs751 = append(xs751, item753)
		cond752 = p.matchLookaheadLiteral("(", 0)
	}
	declarations754 := xs751
	p.consumeLiteral(")")
	result756 := p.constructFragment(new_fragment_id750, declarations754)
	p.recordSpan(int(span_start755), "Fragment")
	return result756
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start758 := int64(p.spanStart())
	_t1447 := p.parse_fragment_id()
	fragment_id757 := _t1447
	p.startFragment(fragment_id757)
	result759 := fragment_id757
	p.recordSpan(int(span_start758), "FragmentId")
	return result759
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start765 := int64(p.spanStart())
	var _t1448 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1449 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1449 = 3
		} else {
			var _t1450 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1450 = 2
			} else {
				var _t1451 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1451 = 3
				} else {
					var _t1452 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1452 = 0
					} else {
						var _t1453 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1453 = 3
						} else {
							var _t1454 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1454 = 3
							} else {
								var _t1455 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1455 = 1
								} else {
									_t1455 = -1
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
			_t1449 = _t1450
		}
		_t1448 = _t1449
	} else {
		_t1448 = -1
	}
	prediction760 := _t1448
	var _t1456 *pb.Declaration
	if prediction760 == 3 {
		_t1457 := p.parse_data()
		data764 := _t1457
		_t1458 := &pb.Declaration{}
		_t1458.DeclarationType = &pb.Declaration_Data{Data: data764}
		_t1456 = _t1458
	} else {
		var _t1459 *pb.Declaration
		if prediction760 == 2 {
			_t1460 := p.parse_constraint()
			constraint763 := _t1460
			_t1461 := &pb.Declaration{}
			_t1461.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint763}
			_t1459 = _t1461
		} else {
			var _t1462 *pb.Declaration
			if prediction760 == 1 {
				_t1463 := p.parse_algorithm()
				algorithm762 := _t1463
				_t1464 := &pb.Declaration{}
				_t1464.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm762}
				_t1462 = _t1464
			} else {
				var _t1465 *pb.Declaration
				if prediction760 == 0 {
					_t1466 := p.parse_def()
					def761 := _t1466
					_t1467 := &pb.Declaration{}
					_t1467.DeclarationType = &pb.Declaration_Def{Def: def761}
					_t1465 = _t1467
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1462 = _t1465
			}
			_t1459 = _t1462
		}
		_t1456 = _t1459
	}
	result766 := _t1456
	p.recordSpan(int(span_start765), "Declaration")
	return result766
}

func (p *Parser) parse_def() *pb.Def {
	span_start770 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1468 := p.parse_relation_id()
	relation_id767 := _t1468
	_t1469 := p.parse_abstraction()
	abstraction768 := _t1469
	var _t1470 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1471 := p.parse_attrs()
		_t1470 = _t1471
	}
	attrs769 := _t1470
	p.consumeLiteral(")")
	_t1472 := attrs769
	if attrs769 == nil {
		_t1472 = []*pb.Attribute{}
	}
	_t1473 := &pb.Def{Name: relation_id767, Body: abstraction768, Attrs: _t1472}
	result771 := _t1473
	p.recordSpan(int(span_start770), "Def")
	return result771
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start775 := int64(p.spanStart())
	var _t1474 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1474 = 0
	} else {
		var _t1475 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1475 = 1
		} else {
			_t1475 = -1
		}
		_t1474 = _t1475
	}
	prediction772 := _t1474
	var _t1476 *pb.RelationId
	if prediction772 == 1 {
		uint128774 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128774
		_t1476 = &pb.RelationId{IdLow: uint128774.Low, IdHigh: uint128774.High}
	} else {
		var _t1477 *pb.RelationId
		if prediction772 == 0 {
			p.consumeLiteral(":")
			symbol773 := p.consumeTerminal("SYMBOL").Value.str
			_t1477 = p.relationIdFromString(symbol773)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1476 = _t1477
	}
	result776 := _t1476
	p.recordSpan(int(span_start775), "RelationId")
	return result776
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start779 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1478 := p.parse_bindings()
	bindings777 := _t1478
	_t1479 := p.parse_formula()
	formula778 := _t1479
	p.consumeLiteral(")")
	_t1480 := &pb.Abstraction{Vars: listConcat(bindings777[0].([]*pb.Binding), bindings777[1].([]*pb.Binding)), Value: formula778}
	result780 := _t1480
	p.recordSpan(int(span_start779), "Abstraction")
	return result780
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs781 := []*pb.Binding{}
	cond782 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond782 {
		_t1481 := p.parse_binding()
		item783 := _t1481
		xs781 = append(xs781, item783)
		cond782 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings784 := xs781
	var _t1482 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1483 := p.parse_value_bindings()
		_t1482 = _t1483
	}
	value_bindings785 := _t1482
	p.consumeLiteral("]")
	_t1484 := value_bindings785
	if value_bindings785 == nil {
		_t1484 = []*pb.Binding{}
	}
	return []interface{}{bindings784, _t1484}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start788 := int64(p.spanStart())
	symbol786 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1485 := p.parse_type()
	type787 := _t1485
	_t1486 := &pb.Var{Name: symbol786}
	_t1487 := &pb.Binding{Var: _t1486, Type: type787}
	result789 := _t1487
	p.recordSpan(int(span_start788), "Binding")
	return result789
}

func (p *Parser) parse_type() *pb.Type {
	span_start805 := int64(p.spanStart())
	var _t1488 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1488 = 0
	} else {
		var _t1489 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1489 = 13
		} else {
			var _t1490 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1490 = 4
			} else {
				var _t1491 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1491 = 1
				} else {
					var _t1492 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1492 = 8
					} else {
						var _t1493 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1493 = 11
						} else {
							var _t1494 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1494 = 5
							} else {
								var _t1495 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1495 = 2
								} else {
									var _t1496 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1496 = 12
									} else {
										var _t1497 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1497 = 3
										} else {
											var _t1498 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1498 = 7
											} else {
												var _t1499 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1499 = 6
												} else {
													var _t1500 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1500 = 10
													} else {
														var _t1501 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1501 = 9
														} else {
															_t1501 = -1
														}
														_t1500 = _t1501
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
	prediction790 := _t1488
	var _t1502 *pb.Type
	if prediction790 == 13 {
		_t1503 := p.parse_uint32_type()
		uint32_type804 := _t1503
		_t1504 := &pb.Type{}
		_t1504.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type804}
		_t1502 = _t1504
	} else {
		var _t1505 *pb.Type
		if prediction790 == 12 {
			_t1506 := p.parse_float32_type()
			float32_type803 := _t1506
			_t1507 := &pb.Type{}
			_t1507.Type = &pb.Type_Float32Type{Float32Type: float32_type803}
			_t1505 = _t1507
		} else {
			var _t1508 *pb.Type
			if prediction790 == 11 {
				_t1509 := p.parse_int32_type()
				int32_type802 := _t1509
				_t1510 := &pb.Type{}
				_t1510.Type = &pb.Type_Int32Type{Int32Type: int32_type802}
				_t1508 = _t1510
			} else {
				var _t1511 *pb.Type
				if prediction790 == 10 {
					_t1512 := p.parse_boolean_type()
					boolean_type801 := _t1512
					_t1513 := &pb.Type{}
					_t1513.Type = &pb.Type_BooleanType{BooleanType: boolean_type801}
					_t1511 = _t1513
				} else {
					var _t1514 *pb.Type
					if prediction790 == 9 {
						_t1515 := p.parse_decimal_type()
						decimal_type800 := _t1515
						_t1516 := &pb.Type{}
						_t1516.Type = &pb.Type_DecimalType{DecimalType: decimal_type800}
						_t1514 = _t1516
					} else {
						var _t1517 *pb.Type
						if prediction790 == 8 {
							_t1518 := p.parse_missing_type()
							missing_type799 := _t1518
							_t1519 := &pb.Type{}
							_t1519.Type = &pb.Type_MissingType{MissingType: missing_type799}
							_t1517 = _t1519
						} else {
							var _t1520 *pb.Type
							if prediction790 == 7 {
								_t1521 := p.parse_datetime_type()
								datetime_type798 := _t1521
								_t1522 := &pb.Type{}
								_t1522.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type798}
								_t1520 = _t1522
							} else {
								var _t1523 *pb.Type
								if prediction790 == 6 {
									_t1524 := p.parse_date_type()
									date_type797 := _t1524
									_t1525 := &pb.Type{}
									_t1525.Type = &pb.Type_DateType{DateType: date_type797}
									_t1523 = _t1525
								} else {
									var _t1526 *pb.Type
									if prediction790 == 5 {
										_t1527 := p.parse_int128_type()
										int128_type796 := _t1527
										_t1528 := &pb.Type{}
										_t1528.Type = &pb.Type_Int128Type{Int128Type: int128_type796}
										_t1526 = _t1528
									} else {
										var _t1529 *pb.Type
										if prediction790 == 4 {
											_t1530 := p.parse_uint128_type()
											uint128_type795 := _t1530
											_t1531 := &pb.Type{}
											_t1531.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type795}
											_t1529 = _t1531
										} else {
											var _t1532 *pb.Type
											if prediction790 == 3 {
												_t1533 := p.parse_float_type()
												float_type794 := _t1533
												_t1534 := &pb.Type{}
												_t1534.Type = &pb.Type_FloatType{FloatType: float_type794}
												_t1532 = _t1534
											} else {
												var _t1535 *pb.Type
												if prediction790 == 2 {
													_t1536 := p.parse_int_type()
													int_type793 := _t1536
													_t1537 := &pb.Type{}
													_t1537.Type = &pb.Type_IntType{IntType: int_type793}
													_t1535 = _t1537
												} else {
													var _t1538 *pb.Type
													if prediction790 == 1 {
														_t1539 := p.parse_string_type()
														string_type792 := _t1539
														_t1540 := &pb.Type{}
														_t1540.Type = &pb.Type_StringType{StringType: string_type792}
														_t1538 = _t1540
													} else {
														var _t1541 *pb.Type
														if prediction790 == 0 {
															_t1542 := p.parse_unspecified_type()
															unspecified_type791 := _t1542
															_t1543 := &pb.Type{}
															_t1543.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type791}
															_t1541 = _t1543
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1538 = _t1541
													}
													_t1535 = _t1538
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
	result806 := _t1502
	p.recordSpan(int(span_start805), "Type")
	return result806
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1544 := &pb.UnspecifiedType{}
	result808 := _t1544
	p.recordSpan(int(span_start807), "UnspecifiedType")
	return result808
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1545 := &pb.StringType{}
	result810 := _t1545
	p.recordSpan(int(span_start809), "StringType")
	return result810
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1546 := &pb.IntType{}
	result812 := _t1546
	p.recordSpan(int(span_start811), "IntType")
	return result812
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1547 := &pb.FloatType{}
	result814 := _t1547
	p.recordSpan(int(span_start813), "FloatType")
	return result814
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1548 := &pb.UInt128Type{}
	result816 := _t1548
	p.recordSpan(int(span_start815), "UInt128Type")
	return result816
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1549 := &pb.Int128Type{}
	result818 := _t1549
	p.recordSpan(int(span_start817), "Int128Type")
	return result818
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1550 := &pb.DateType{}
	result820 := _t1550
	p.recordSpan(int(span_start819), "DateType")
	return result820
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start821 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1551 := &pb.DateTimeType{}
	result822 := _t1551
	p.recordSpan(int(span_start821), "DateTimeType")
	return result822
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start823 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1552 := &pb.MissingType{}
	result824 := _t1552
	p.recordSpan(int(span_start823), "MissingType")
	return result824
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start827 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int825 := p.consumeTerminal("INT").Value.i64
	int_3826 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1553 := &pb.DecimalType{Precision: int32(int825), Scale: int32(int_3826)}
	result828 := _t1553
	p.recordSpan(int(span_start827), "DecimalType")
	return result828
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1554 := &pb.BooleanType{}
	result830 := _t1554
	p.recordSpan(int(span_start829), "BooleanType")
	return result830
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start831 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1555 := &pb.Int32Type{}
	result832 := _t1555
	p.recordSpan(int(span_start831), "Int32Type")
	return result832
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start833 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1556 := &pb.Float32Type{}
	result834 := _t1556
	p.recordSpan(int(span_start833), "Float32Type")
	return result834
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start835 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1557 := &pb.UInt32Type{}
	result836 := _t1557
	p.recordSpan(int(span_start835), "UInt32Type")
	return result836
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs837 := []*pb.Binding{}
	cond838 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond838 {
		_t1558 := p.parse_binding()
		item839 := _t1558
		xs837 = append(xs837, item839)
		cond838 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings840 := xs837
	return bindings840
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start855 := int64(p.spanStart())
	var _t1559 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1560 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1560 = 0
		} else {
			var _t1561 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1561 = 11
			} else {
				var _t1562 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1562 = 3
				} else {
					var _t1563 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1563 = 10
					} else {
						var _t1564 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1564 = 9
						} else {
							var _t1565 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1565 = 5
							} else {
								var _t1566 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1566 = 6
								} else {
									var _t1567 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1567 = 7
									} else {
										var _t1568 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1568 = 1
										} else {
											var _t1569 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1569 = 2
											} else {
												var _t1570 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1570 = 12
												} else {
													var _t1571 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1571 = 8
													} else {
														var _t1572 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1572 = 4
														} else {
															var _t1573 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1573 = 10
															} else {
																var _t1574 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1574 = 10
																} else {
																	var _t1575 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1575 = 10
																	} else {
																		var _t1576 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1576 = 10
																		} else {
																			var _t1577 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1577 = 10
																			} else {
																				var _t1578 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1578 = 10
																				} else {
																					var _t1579 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1579 = 10
																					} else {
																						var _t1580 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1580 = 10
																						} else {
																							var _t1581 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1581 = 10
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
	} else {
		_t1559 = -1
	}
	prediction841 := _t1559
	var _t1582 *pb.Formula
	if prediction841 == 12 {
		_t1583 := p.parse_cast()
		cast854 := _t1583
		_t1584 := &pb.Formula{}
		_t1584.FormulaType = &pb.Formula_Cast{Cast: cast854}
		_t1582 = _t1584
	} else {
		var _t1585 *pb.Formula
		if prediction841 == 11 {
			_t1586 := p.parse_rel_atom()
			rel_atom853 := _t1586
			_t1587 := &pb.Formula{}
			_t1587.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom853}
			_t1585 = _t1587
		} else {
			var _t1588 *pb.Formula
			if prediction841 == 10 {
				_t1589 := p.parse_primitive()
				primitive852 := _t1589
				_t1590 := &pb.Formula{}
				_t1590.FormulaType = &pb.Formula_Primitive{Primitive: primitive852}
				_t1588 = _t1590
			} else {
				var _t1591 *pb.Formula
				if prediction841 == 9 {
					_t1592 := p.parse_pragma()
					pragma851 := _t1592
					_t1593 := &pb.Formula{}
					_t1593.FormulaType = &pb.Formula_Pragma{Pragma: pragma851}
					_t1591 = _t1593
				} else {
					var _t1594 *pb.Formula
					if prediction841 == 8 {
						_t1595 := p.parse_atom()
						atom850 := _t1595
						_t1596 := &pb.Formula{}
						_t1596.FormulaType = &pb.Formula_Atom{Atom: atom850}
						_t1594 = _t1596
					} else {
						var _t1597 *pb.Formula
						if prediction841 == 7 {
							_t1598 := p.parse_ffi()
							ffi849 := _t1598
							_t1599 := &pb.Formula{}
							_t1599.FormulaType = &pb.Formula_Ffi{Ffi: ffi849}
							_t1597 = _t1599
						} else {
							var _t1600 *pb.Formula
							if prediction841 == 6 {
								_t1601 := p.parse_not()
								not848 := _t1601
								_t1602 := &pb.Formula{}
								_t1602.FormulaType = &pb.Formula_Not{Not: not848}
								_t1600 = _t1602
							} else {
								var _t1603 *pb.Formula
								if prediction841 == 5 {
									_t1604 := p.parse_disjunction()
									disjunction847 := _t1604
									_t1605 := &pb.Formula{}
									_t1605.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction847}
									_t1603 = _t1605
								} else {
									var _t1606 *pb.Formula
									if prediction841 == 4 {
										_t1607 := p.parse_conjunction()
										conjunction846 := _t1607
										_t1608 := &pb.Formula{}
										_t1608.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction846}
										_t1606 = _t1608
									} else {
										var _t1609 *pb.Formula
										if prediction841 == 3 {
											_t1610 := p.parse_reduce()
											reduce845 := _t1610
											_t1611 := &pb.Formula{}
											_t1611.FormulaType = &pb.Formula_Reduce{Reduce: reduce845}
											_t1609 = _t1611
										} else {
											var _t1612 *pb.Formula
											if prediction841 == 2 {
												_t1613 := p.parse_exists()
												exists844 := _t1613
												_t1614 := &pb.Formula{}
												_t1614.FormulaType = &pb.Formula_Exists{Exists: exists844}
												_t1612 = _t1614
											} else {
												var _t1615 *pb.Formula
												if prediction841 == 1 {
													_t1616 := p.parse_false()
													false843 := _t1616
													_t1617 := &pb.Formula{}
													_t1617.FormulaType = &pb.Formula_Disjunction{Disjunction: false843}
													_t1615 = _t1617
												} else {
													var _t1618 *pb.Formula
													if prediction841 == 0 {
														_t1619 := p.parse_true()
														true842 := _t1619
														_t1620 := &pb.Formula{}
														_t1620.FormulaType = &pb.Formula_Conjunction{Conjunction: true842}
														_t1618 = _t1620
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1615 = _t1618
												}
												_t1612 = _t1615
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
	result856 := _t1582
	p.recordSpan(int(span_start855), "Formula")
	return result856
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1621 := &pb.Conjunction{Args: []*pb.Formula{}}
	result858 := _t1621
	p.recordSpan(int(span_start857), "Conjunction")
	return result858
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1622 := &pb.Disjunction{Args: []*pb.Formula{}}
	result860 := _t1622
	p.recordSpan(int(span_start859), "Disjunction")
	return result860
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1623 := p.parse_bindings()
	bindings861 := _t1623
	_t1624 := p.parse_formula()
	formula862 := _t1624
	p.consumeLiteral(")")
	_t1625 := &pb.Abstraction{Vars: listConcat(bindings861[0].([]*pb.Binding), bindings861[1].([]*pb.Binding)), Value: formula862}
	_t1626 := &pb.Exists{Body: _t1625}
	result864 := _t1626
	p.recordSpan(int(span_start863), "Exists")
	return result864
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start868 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1627 := p.parse_abstraction()
	abstraction865 := _t1627
	_t1628 := p.parse_abstraction()
	abstraction_3866 := _t1628
	_t1629 := p.parse_terms()
	terms867 := _t1629
	p.consumeLiteral(")")
	_t1630 := &pb.Reduce{Op: abstraction865, Body: abstraction_3866, Terms: terms867}
	result869 := _t1630
	p.recordSpan(int(span_start868), "Reduce")
	return result869
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs870 := []*pb.Term{}
	cond871 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond871 {
		_t1631 := p.parse_term()
		item872 := _t1631
		xs870 = append(xs870, item872)
		cond871 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms873 := xs870
	p.consumeLiteral(")")
	return terms873
}

func (p *Parser) parse_term() *pb.Term {
	span_start877 := int64(p.spanStart())
	var _t1632 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1632 = 1
	} else {
		var _t1633 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1633 = 1
		} else {
			var _t1634 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1634 = 1
			} else {
				var _t1635 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1635 = 1
				} else {
					var _t1636 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1636 = 0
					} else {
						var _t1637 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1637 = 1
						} else {
							var _t1638 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1638 = 1
							} else {
								var _t1639 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1639 = 1
								} else {
									var _t1640 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1640 = 1
									} else {
										var _t1641 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1641 = 1
										} else {
											var _t1642 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1642 = 1
											} else {
												var _t1643 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1643 = 1
												} else {
													var _t1644 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1644 = 1
													} else {
														var _t1645 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1645 = 1
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
	prediction874 := _t1632
	var _t1646 *pb.Term
	if prediction874 == 1 {
		_t1647 := p.parse_value()
		value876 := _t1647
		_t1648 := &pb.Term{}
		_t1648.TermType = &pb.Term_Constant{Constant: value876}
		_t1646 = _t1648
	} else {
		var _t1649 *pb.Term
		if prediction874 == 0 {
			_t1650 := p.parse_var()
			var875 := _t1650
			_t1651 := &pb.Term{}
			_t1651.TermType = &pb.Term_Var{Var: var875}
			_t1649 = _t1651
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1646 = _t1649
	}
	result878 := _t1646
	p.recordSpan(int(span_start877), "Term")
	return result878
}

func (p *Parser) parse_var() *pb.Var {
	span_start880 := int64(p.spanStart())
	symbol879 := p.consumeTerminal("SYMBOL").Value.str
	_t1652 := &pb.Var{Name: symbol879}
	result881 := _t1652
	p.recordSpan(int(span_start880), "Var")
	return result881
}

func (p *Parser) parse_value() *pb.Value {
	span_start895 := int64(p.spanStart())
	var _t1653 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1653 = 12
	} else {
		var _t1654 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1654 = 11
		} else {
			var _t1655 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1655 = 12
			} else {
				var _t1656 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1657 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1657 = 1
					} else {
						var _t1658 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1658 = 0
						} else {
							_t1658 = -1
						}
						_t1657 = _t1658
					}
					_t1656 = _t1657
				} else {
					var _t1659 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1659 = 7
					} else {
						var _t1660 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1660 = 8
						} else {
							var _t1661 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1661 = 2
							} else {
								var _t1662 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1662 = 3
								} else {
									var _t1663 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1663 = 9
									} else {
										var _t1664 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1664 = 4
										} else {
											var _t1665 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1665 = 5
											} else {
												var _t1666 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1666 = 6
												} else {
													var _t1667 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
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
					_t1656 = _t1659
				}
				_t1655 = _t1656
			}
			_t1654 = _t1655
		}
		_t1653 = _t1654
	}
	prediction882 := _t1653
	var _t1668 *pb.Value
	if prediction882 == 12 {
		_t1669 := p.parse_boolean_value()
		boolean_value894 := _t1669
		_t1670 := &pb.Value{}
		_t1670.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value894}
		_t1668 = _t1670
	} else {
		var _t1671 *pb.Value
		if prediction882 == 11 {
			p.consumeLiteral("missing")
			_t1672 := &pb.MissingValue{}
			_t1673 := &pb.Value{}
			_t1673.Value = &pb.Value_MissingValue{MissingValue: _t1672}
			_t1671 = _t1673
		} else {
			var _t1674 *pb.Value
			if prediction882 == 10 {
				formatted_decimal893 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1675 := &pb.Value{}
				_t1675.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal893}
				_t1674 = _t1675
			} else {
				var _t1676 *pb.Value
				if prediction882 == 9 {
					formatted_int128892 := p.consumeTerminal("INT128").Value.int128
					_t1677 := &pb.Value{}
					_t1677.Value = &pb.Value_Int128Value{Int128Value: formatted_int128892}
					_t1676 = _t1677
				} else {
					var _t1678 *pb.Value
					if prediction882 == 8 {
						formatted_uint128891 := p.consumeTerminal("UINT128").Value.uint128
						_t1679 := &pb.Value{}
						_t1679.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128891}
						_t1678 = _t1679
					} else {
						var _t1680 *pb.Value
						if prediction882 == 7 {
							formatted_uint32890 := p.consumeTerminal("UINT32").Value.u32
							_t1681 := &pb.Value{}
							_t1681.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32890}
							_t1680 = _t1681
						} else {
							var _t1682 *pb.Value
							if prediction882 == 6 {
								formatted_float889 := p.consumeTerminal("FLOAT").Value.f64
								_t1683 := &pb.Value{}
								_t1683.Value = &pb.Value_FloatValue{FloatValue: formatted_float889}
								_t1682 = _t1683
							} else {
								var _t1684 *pb.Value
								if prediction882 == 5 {
									formatted_float32888 := p.consumeTerminal("FLOAT32").Value.f32
									_t1685 := &pb.Value{}
									_t1685.Value = &pb.Value_Float32Value{Float32Value: formatted_float32888}
									_t1684 = _t1685
								} else {
									var _t1686 *pb.Value
									if prediction882 == 4 {
										formatted_int887 := p.consumeTerminal("INT").Value.i64
										_t1687 := &pb.Value{}
										_t1687.Value = &pb.Value_IntValue{IntValue: formatted_int887}
										_t1686 = _t1687
									} else {
										var _t1688 *pb.Value
										if prediction882 == 3 {
											formatted_int32886 := p.consumeTerminal("INT32").Value.i32
											_t1689 := &pb.Value{}
											_t1689.Value = &pb.Value_Int32Value{Int32Value: formatted_int32886}
											_t1688 = _t1689
										} else {
											var _t1690 *pb.Value
											if prediction882 == 2 {
												formatted_string885 := p.consumeTerminal("STRING").Value.str
												_t1691 := &pb.Value{}
												_t1691.Value = &pb.Value_StringValue{StringValue: formatted_string885}
												_t1690 = _t1691
											} else {
												var _t1692 *pb.Value
												if prediction882 == 1 {
													_t1693 := p.parse_datetime()
													datetime884 := _t1693
													_t1694 := &pb.Value{}
													_t1694.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime884}
													_t1692 = _t1694
												} else {
													var _t1695 *pb.Value
													if prediction882 == 0 {
														_t1696 := p.parse_date()
														date883 := _t1696
														_t1697 := &pb.Value{}
														_t1697.Value = &pb.Value_DateValue{DateValue: date883}
														_t1695 = _t1697
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1692 = _t1695
												}
												_t1690 = _t1692
											}
											_t1688 = _t1690
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
			_t1671 = _t1674
		}
		_t1668 = _t1671
	}
	result896 := _t1668
	p.recordSpan(int(span_start895), "Value")
	return result896
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int897 := p.consumeTerminal("INT").Value.i64
	formatted_int_3898 := p.consumeTerminal("INT").Value.i64
	formatted_int_4899 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1698 := &pb.DateValue{Year: int32(formatted_int897), Month: int32(formatted_int_3898), Day: int32(formatted_int_4899)}
	result901 := _t1698
	p.recordSpan(int(span_start900), "DateValue")
	return result901
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int902 := p.consumeTerminal("INT").Value.i64
	formatted_int_3903 := p.consumeTerminal("INT").Value.i64
	formatted_int_4904 := p.consumeTerminal("INT").Value.i64
	formatted_int_5905 := p.consumeTerminal("INT").Value.i64
	formatted_int_6906 := p.consumeTerminal("INT").Value.i64
	formatted_int_7907 := p.consumeTerminal("INT").Value.i64
	var _t1699 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1699 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8908 := _t1699
	p.consumeLiteral(")")
	_t1700 := &pb.DateTimeValue{Year: int32(formatted_int902), Month: int32(formatted_int_3903), Day: int32(formatted_int_4904), Hour: int32(formatted_int_5905), Minute: int32(formatted_int_6906), Second: int32(formatted_int_7907), Microsecond: int32(deref(formatted_int_8908, 0))}
	result910 := _t1700
	p.recordSpan(int(span_start909), "DateTimeValue")
	return result910
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start915 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs911 := []*pb.Formula{}
	cond912 := p.matchLookaheadLiteral("(", 0)
	for cond912 {
		_t1701 := p.parse_formula()
		item913 := _t1701
		xs911 = append(xs911, item913)
		cond912 = p.matchLookaheadLiteral("(", 0)
	}
	formulas914 := xs911
	p.consumeLiteral(")")
	_t1702 := &pb.Conjunction{Args: formulas914}
	result916 := _t1702
	p.recordSpan(int(span_start915), "Conjunction")
	return result916
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start921 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs917 := []*pb.Formula{}
	cond918 := p.matchLookaheadLiteral("(", 0)
	for cond918 {
		_t1703 := p.parse_formula()
		item919 := _t1703
		xs917 = append(xs917, item919)
		cond918 = p.matchLookaheadLiteral("(", 0)
	}
	formulas920 := xs917
	p.consumeLiteral(")")
	_t1704 := &pb.Disjunction{Args: formulas920}
	result922 := _t1704
	p.recordSpan(int(span_start921), "Disjunction")
	return result922
}

func (p *Parser) parse_not() *pb.Not {
	span_start924 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1705 := p.parse_formula()
	formula923 := _t1705
	p.consumeLiteral(")")
	_t1706 := &pb.Not{Arg: formula923}
	result925 := _t1706
	p.recordSpan(int(span_start924), "Not")
	return result925
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start929 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1707 := p.parse_name()
	name926 := _t1707
	_t1708 := p.parse_ffi_args()
	ffi_args927 := _t1708
	_t1709 := p.parse_terms()
	terms928 := _t1709
	p.consumeLiteral(")")
	_t1710 := &pb.FFI{Name: name926, Args: ffi_args927, Terms: terms928}
	result930 := _t1710
	p.recordSpan(int(span_start929), "FFI")
	return result930
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol931 := p.consumeTerminal("SYMBOL").Value.str
	return symbol931
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs932 := []*pb.Abstraction{}
	cond933 := p.matchLookaheadLiteral("(", 0)
	for cond933 {
		_t1711 := p.parse_abstraction()
		item934 := _t1711
		xs932 = append(xs932, item934)
		cond933 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions935 := xs932
	p.consumeLiteral(")")
	return abstractions935
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start941 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1712 := p.parse_relation_id()
	relation_id936 := _t1712
	xs937 := []*pb.Term{}
	cond938 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond938 {
		_t1713 := p.parse_term()
		item939 := _t1713
		xs937 = append(xs937, item939)
		cond938 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms940 := xs937
	p.consumeLiteral(")")
	_t1714 := &pb.Atom{Name: relation_id936, Terms: terms940}
	result942 := _t1714
	p.recordSpan(int(span_start941), "Atom")
	return result942
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1715 := p.parse_name()
	name943 := _t1715
	xs944 := []*pb.Term{}
	cond945 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond945 {
		_t1716 := p.parse_term()
		item946 := _t1716
		xs944 = append(xs944, item946)
		cond945 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms947 := xs944
	p.consumeLiteral(")")
	_t1717 := &pb.Pragma{Name: name943, Terms: terms947}
	result949 := _t1717
	p.recordSpan(int(span_start948), "Pragma")
	return result949
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start965 := int64(p.spanStart())
	var _t1718 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1719 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1719 = 9
		} else {
			var _t1720 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1720 = 4
			} else {
				var _t1721 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1721 = 3
				} else {
					var _t1722 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1722 = 0
					} else {
						var _t1723 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1723 = 2
						} else {
							var _t1724 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1724 = 1
							} else {
								var _t1725 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1725 = 8
								} else {
									var _t1726 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1726 = 6
									} else {
										var _t1727 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1727 = 5
										} else {
											var _t1728 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1728 = 7
											} else {
												_t1728 = -1
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
	} else {
		_t1718 = -1
	}
	prediction950 := _t1718
	var _t1729 *pb.Primitive
	if prediction950 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1730 := p.parse_name()
		name960 := _t1730
		xs961 := []*pb.RelTerm{}
		cond962 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond962 {
			_t1731 := p.parse_rel_term()
			item963 := _t1731
			xs961 = append(xs961, item963)
			cond962 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms964 := xs961
		p.consumeLiteral(")")
		_t1732 := &pb.Primitive{Name: name960, Terms: rel_terms964}
		_t1729 = _t1732
	} else {
		var _t1733 *pb.Primitive
		if prediction950 == 8 {
			_t1734 := p.parse_divide()
			divide959 := _t1734
			_t1733 = divide959
		} else {
			var _t1735 *pb.Primitive
			if prediction950 == 7 {
				_t1736 := p.parse_multiply()
				multiply958 := _t1736
				_t1735 = multiply958
			} else {
				var _t1737 *pb.Primitive
				if prediction950 == 6 {
					_t1738 := p.parse_minus()
					minus957 := _t1738
					_t1737 = minus957
				} else {
					var _t1739 *pb.Primitive
					if prediction950 == 5 {
						_t1740 := p.parse_add()
						add956 := _t1740
						_t1739 = add956
					} else {
						var _t1741 *pb.Primitive
						if prediction950 == 4 {
							_t1742 := p.parse_gt_eq()
							gt_eq955 := _t1742
							_t1741 = gt_eq955
						} else {
							var _t1743 *pb.Primitive
							if prediction950 == 3 {
								_t1744 := p.parse_gt()
								gt954 := _t1744
								_t1743 = gt954
							} else {
								var _t1745 *pb.Primitive
								if prediction950 == 2 {
									_t1746 := p.parse_lt_eq()
									lt_eq953 := _t1746
									_t1745 = lt_eq953
								} else {
									var _t1747 *pb.Primitive
									if prediction950 == 1 {
										_t1748 := p.parse_lt()
										lt952 := _t1748
										_t1747 = lt952
									} else {
										var _t1749 *pb.Primitive
										if prediction950 == 0 {
											_t1750 := p.parse_eq()
											eq951 := _t1750
											_t1749 = eq951
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1747 = _t1749
									}
									_t1745 = _t1747
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
		_t1729 = _t1733
	}
	result966 := _t1729
	p.recordSpan(int(span_start965), "Primitive")
	return result966
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1751 := p.parse_term()
	term967 := _t1751
	_t1752 := p.parse_term()
	term_3968 := _t1752
	p.consumeLiteral(")")
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term967}
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term_3968}
	_t1755 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1753, _t1754}}
	result970 := _t1755
	p.recordSpan(int(span_start969), "Primitive")
	return result970
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start973 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1756 := p.parse_term()
	term971 := _t1756
	_t1757 := p.parse_term()
	term_3972 := _t1757
	p.consumeLiteral(")")
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term971}
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term_3972}
	_t1760 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1758, _t1759}}
	result974 := _t1760
	p.recordSpan(int(span_start973), "Primitive")
	return result974
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start977 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1761 := p.parse_term()
	term975 := _t1761
	_t1762 := p.parse_term()
	term_3976 := _t1762
	p.consumeLiteral(")")
	_t1763 := &pb.RelTerm{}
	_t1763.RelTermType = &pb.RelTerm_Term{Term: term975}
	_t1764 := &pb.RelTerm{}
	_t1764.RelTermType = &pb.RelTerm_Term{Term: term_3976}
	_t1765 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1763, _t1764}}
	result978 := _t1765
	p.recordSpan(int(span_start977), "Primitive")
	return result978
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start981 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1766 := p.parse_term()
	term979 := _t1766
	_t1767 := p.parse_term()
	term_3980 := _t1767
	p.consumeLiteral(")")
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term979}
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term_3980}
	_t1770 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1768, _t1769}}
	result982 := _t1770
	p.recordSpan(int(span_start981), "Primitive")
	return result982
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start985 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1771 := p.parse_term()
	term983 := _t1771
	_t1772 := p.parse_term()
	term_3984 := _t1772
	p.consumeLiteral(")")
	_t1773 := &pb.RelTerm{}
	_t1773.RelTermType = &pb.RelTerm_Term{Term: term983}
	_t1774 := &pb.RelTerm{}
	_t1774.RelTermType = &pb.RelTerm_Term{Term: term_3984}
	_t1775 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1773, _t1774}}
	result986 := _t1775
	p.recordSpan(int(span_start985), "Primitive")
	return result986
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start990 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1776 := p.parse_term()
	term987 := _t1776
	_t1777 := p.parse_term()
	term_3988 := _t1777
	_t1778 := p.parse_term()
	term_4989 := _t1778
	p.consumeLiteral(")")
	_t1779 := &pb.RelTerm{}
	_t1779.RelTermType = &pb.RelTerm_Term{Term: term987}
	_t1780 := &pb.RelTerm{}
	_t1780.RelTermType = &pb.RelTerm_Term{Term: term_3988}
	_t1781 := &pb.RelTerm{}
	_t1781.RelTermType = &pb.RelTerm_Term{Term: term_4989}
	_t1782 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1779, _t1780, _t1781}}
	result991 := _t1782
	p.recordSpan(int(span_start990), "Primitive")
	return result991
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start995 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1783 := p.parse_term()
	term992 := _t1783
	_t1784 := p.parse_term()
	term_3993 := _t1784
	_t1785 := p.parse_term()
	term_4994 := _t1785
	p.consumeLiteral(")")
	_t1786 := &pb.RelTerm{}
	_t1786.RelTermType = &pb.RelTerm_Term{Term: term992}
	_t1787 := &pb.RelTerm{}
	_t1787.RelTermType = &pb.RelTerm_Term{Term: term_3993}
	_t1788 := &pb.RelTerm{}
	_t1788.RelTermType = &pb.RelTerm_Term{Term: term_4994}
	_t1789 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1786, _t1787, _t1788}}
	result996 := _t1789
	p.recordSpan(int(span_start995), "Primitive")
	return result996
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1000 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1790 := p.parse_term()
	term997 := _t1790
	_t1791 := p.parse_term()
	term_3998 := _t1791
	_t1792 := p.parse_term()
	term_4999 := _t1792
	p.consumeLiteral(")")
	_t1793 := &pb.RelTerm{}
	_t1793.RelTermType = &pb.RelTerm_Term{Term: term997}
	_t1794 := &pb.RelTerm{}
	_t1794.RelTermType = &pb.RelTerm_Term{Term: term_3998}
	_t1795 := &pb.RelTerm{}
	_t1795.RelTermType = &pb.RelTerm_Term{Term: term_4999}
	_t1796 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1793, _t1794, _t1795}}
	result1001 := _t1796
	p.recordSpan(int(span_start1000), "Primitive")
	return result1001
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1797 := p.parse_term()
	term1002 := _t1797
	_t1798 := p.parse_term()
	term_31003 := _t1798
	_t1799 := p.parse_term()
	term_41004 := _t1799
	p.consumeLiteral(")")
	_t1800 := &pb.RelTerm{}
	_t1800.RelTermType = &pb.RelTerm_Term{Term: term1002}
	_t1801 := &pb.RelTerm{}
	_t1801.RelTermType = &pb.RelTerm_Term{Term: term_31003}
	_t1802 := &pb.RelTerm{}
	_t1802.RelTermType = &pb.RelTerm_Term{Term: term_41004}
	_t1803 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1800, _t1801, _t1802}}
	result1006 := _t1803
	p.recordSpan(int(span_start1005), "Primitive")
	return result1006
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1010 := int64(p.spanStart())
	var _t1804 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1804 = 1
	} else {
		var _t1805 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1805 = 1
		} else {
			var _t1806 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1806 = 1
			} else {
				var _t1807 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1807 = 1
				} else {
					var _t1808 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1808 = 0
					} else {
						var _t1809 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1809 = 1
						} else {
							var _t1810 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1810 = 1
							} else {
								var _t1811 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1811 = 1
								} else {
									var _t1812 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1812 = 1
									} else {
										var _t1813 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1813 = 1
										} else {
											var _t1814 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1814 = 1
											} else {
												var _t1815 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1815 = 1
												} else {
													var _t1816 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1816 = 1
													} else {
														var _t1817 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1817 = 1
														} else {
															var _t1818 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1818 = 1
															} else {
																_t1818 = -1
															}
															_t1817 = _t1818
														}
														_t1816 = _t1817
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
			}
			_t1805 = _t1806
		}
		_t1804 = _t1805
	}
	prediction1007 := _t1804
	var _t1819 *pb.RelTerm
	if prediction1007 == 1 {
		_t1820 := p.parse_term()
		term1009 := _t1820
		_t1821 := &pb.RelTerm{}
		_t1821.RelTermType = &pb.RelTerm_Term{Term: term1009}
		_t1819 = _t1821
	} else {
		var _t1822 *pb.RelTerm
		if prediction1007 == 0 {
			_t1823 := p.parse_specialized_value()
			specialized_value1008 := _t1823
			_t1824 := &pb.RelTerm{}
			_t1824.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1008}
			_t1822 = _t1824
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1819 = _t1822
	}
	result1011 := _t1819
	p.recordSpan(int(span_start1010), "RelTerm")
	return result1011
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1825 := p.parse_raw_value()
	raw_value1012 := _t1825
	result1014 := raw_value1012
	p.recordSpan(int(span_start1013), "Value")
	return result1014
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1020 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1826 := p.parse_name()
	name1015 := _t1826
	xs1016 := []*pb.RelTerm{}
	cond1017 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1017 {
		_t1827 := p.parse_rel_term()
		item1018 := _t1827
		xs1016 = append(xs1016, item1018)
		cond1017 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1019 := xs1016
	p.consumeLiteral(")")
	_t1828 := &pb.RelAtom{Name: name1015, Terms: rel_terms1019}
	result1021 := _t1828
	p.recordSpan(int(span_start1020), "RelAtom")
	return result1021
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1829 := p.parse_term()
	term1022 := _t1829
	_t1830 := p.parse_term()
	term_31023 := _t1830
	p.consumeLiteral(")")
	_t1831 := &pb.Cast{Input: term1022, Result: term_31023}
	result1025 := _t1831
	p.recordSpan(int(span_start1024), "Cast")
	return result1025
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1026 := []*pb.Attribute{}
	cond1027 := p.matchLookaheadLiteral("(", 0)
	for cond1027 {
		_t1832 := p.parse_attribute()
		item1028 := _t1832
		xs1026 = append(xs1026, item1028)
		cond1027 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1029 := xs1026
	p.consumeLiteral(")")
	return attributes1029
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1035 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1833 := p.parse_name()
	name1030 := _t1833
	xs1031 := []*pb.Value{}
	cond1032 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1032 {
		_t1834 := p.parse_raw_value()
		item1033 := _t1834
		xs1031 = append(xs1031, item1033)
		cond1032 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1034 := xs1031
	p.consumeLiteral(")")
	_t1835 := &pb.Attribute{Name: name1030, Args: raw_values1034}
	result1036 := _t1835
	p.recordSpan(int(span_start1035), "Attribute")
	return result1036
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1043 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1037 := []*pb.RelationId{}
	cond1038 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1038 {
		_t1836 := p.parse_relation_id()
		item1039 := _t1836
		xs1037 = append(xs1037, item1039)
		cond1038 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1040 := xs1037
	_t1837 := p.parse_script()
	script1041 := _t1837
	var _t1838 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1839 := p.parse_attrs()
		_t1838 = _t1839
	}
	attrs1042 := _t1838
	p.consumeLiteral(")")
	_t1840 := attrs1042
	if attrs1042 == nil {
		_t1840 = []*pb.Attribute{}
	}
	_t1841 := &pb.Algorithm{Global: relation_ids1040, Body: script1041, Attrs: _t1840}
	result1044 := _t1841
	p.recordSpan(int(span_start1043), "Algorithm")
	return result1044
}

func (p *Parser) parse_script() *pb.Script {
	span_start1049 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1045 := []*pb.Construct{}
	cond1046 := p.matchLookaheadLiteral("(", 0)
	for cond1046 {
		_t1842 := p.parse_construct()
		item1047 := _t1842
		xs1045 = append(xs1045, item1047)
		cond1046 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1048 := xs1045
	p.consumeLiteral(")")
	_t1843 := &pb.Script{Constructs: constructs1048}
	result1050 := _t1843
	p.recordSpan(int(span_start1049), "Script")
	return result1050
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1054 := int64(p.spanStart())
	var _t1844 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1845 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1845 = 1
		} else {
			var _t1846 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1846 = 1
			} else {
				var _t1847 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1847 = 1
				} else {
					var _t1848 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1848 = 0
					} else {
						var _t1849 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1849 = 1
						} else {
							var _t1850 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1850 = 1
							} else {
								_t1850 = -1
							}
							_t1849 = _t1850
						}
						_t1848 = _t1849
					}
					_t1847 = _t1848
				}
				_t1846 = _t1847
			}
			_t1845 = _t1846
		}
		_t1844 = _t1845
	} else {
		_t1844 = -1
	}
	prediction1051 := _t1844
	var _t1851 *pb.Construct
	if prediction1051 == 1 {
		_t1852 := p.parse_instruction()
		instruction1053 := _t1852
		_t1853 := &pb.Construct{}
		_t1853.ConstructType = &pb.Construct_Instruction{Instruction: instruction1053}
		_t1851 = _t1853
	} else {
		var _t1854 *pb.Construct
		if prediction1051 == 0 {
			_t1855 := p.parse_loop()
			loop1052 := _t1855
			_t1856 := &pb.Construct{}
			_t1856.ConstructType = &pb.Construct_Loop{Loop: loop1052}
			_t1854 = _t1856
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1851 = _t1854
	}
	result1055 := _t1851
	p.recordSpan(int(span_start1054), "Construct")
	return result1055
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1059 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1857 := p.parse_init()
	init1056 := _t1857
	_t1858 := p.parse_script()
	script1057 := _t1858
	var _t1859 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1860 := p.parse_attrs()
		_t1859 = _t1860
	}
	attrs1058 := _t1859
	p.consumeLiteral(")")
	_t1861 := attrs1058
	if attrs1058 == nil {
		_t1861 = []*pb.Attribute{}
	}
	_t1862 := &pb.Loop{Init: init1056, Body: script1057, Attrs: _t1861}
	result1060 := _t1862
	p.recordSpan(int(span_start1059), "Loop")
	return result1060
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1061 := []*pb.Instruction{}
	cond1062 := p.matchLookaheadLiteral("(", 0)
	for cond1062 {
		_t1863 := p.parse_instruction()
		item1063 := _t1863
		xs1061 = append(xs1061, item1063)
		cond1062 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1064 := xs1061
	p.consumeLiteral(")")
	return instructions1064
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1071 := int64(p.spanStart())
	var _t1864 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1865 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1865 = 1
		} else {
			var _t1866 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1866 = 4
			} else {
				var _t1867 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1867 = 3
				} else {
					var _t1868 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1868 = 2
					} else {
						var _t1869 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1869 = 0
						} else {
							_t1869 = -1
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
	} else {
		_t1864 = -1
	}
	prediction1065 := _t1864
	var _t1870 *pb.Instruction
	if prediction1065 == 4 {
		_t1871 := p.parse_monus_def()
		monus_def1070 := _t1871
		_t1872 := &pb.Instruction{}
		_t1872.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1070}
		_t1870 = _t1872
	} else {
		var _t1873 *pb.Instruction
		if prediction1065 == 3 {
			_t1874 := p.parse_monoid_def()
			monoid_def1069 := _t1874
			_t1875 := &pb.Instruction{}
			_t1875.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1069}
			_t1873 = _t1875
		} else {
			var _t1876 *pb.Instruction
			if prediction1065 == 2 {
				_t1877 := p.parse_break()
				break1068 := _t1877
				_t1878 := &pb.Instruction{}
				_t1878.InstrType = &pb.Instruction_Break{Break: break1068}
				_t1876 = _t1878
			} else {
				var _t1879 *pb.Instruction
				if prediction1065 == 1 {
					_t1880 := p.parse_upsert()
					upsert1067 := _t1880
					_t1881 := &pb.Instruction{}
					_t1881.InstrType = &pb.Instruction_Upsert{Upsert: upsert1067}
					_t1879 = _t1881
				} else {
					var _t1882 *pb.Instruction
					if prediction1065 == 0 {
						_t1883 := p.parse_assign()
						assign1066 := _t1883
						_t1884 := &pb.Instruction{}
						_t1884.InstrType = &pb.Instruction_Assign{Assign: assign1066}
						_t1882 = _t1884
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1879 = _t1882
				}
				_t1876 = _t1879
			}
			_t1873 = _t1876
		}
		_t1870 = _t1873
	}
	result1072 := _t1870
	p.recordSpan(int(span_start1071), "Instruction")
	return result1072
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1076 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1885 := p.parse_relation_id()
	relation_id1073 := _t1885
	_t1886 := p.parse_abstraction()
	abstraction1074 := _t1886
	var _t1887 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1888 := p.parse_attrs()
		_t1887 = _t1888
	}
	attrs1075 := _t1887
	p.consumeLiteral(")")
	_t1889 := attrs1075
	if attrs1075 == nil {
		_t1889 = []*pb.Attribute{}
	}
	_t1890 := &pb.Assign{Name: relation_id1073, Body: abstraction1074, Attrs: _t1889}
	result1077 := _t1890
	p.recordSpan(int(span_start1076), "Assign")
	return result1077
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1081 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1891 := p.parse_relation_id()
	relation_id1078 := _t1891
	_t1892 := p.parse_abstraction_with_arity()
	abstraction_with_arity1079 := _t1892
	var _t1893 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1894 := p.parse_attrs()
		_t1893 = _t1894
	}
	attrs1080 := _t1893
	p.consumeLiteral(")")
	_t1895 := attrs1080
	if attrs1080 == nil {
		_t1895 = []*pb.Attribute{}
	}
	_t1896 := &pb.Upsert{Name: relation_id1078, Body: abstraction_with_arity1079[0].(*pb.Abstraction), Attrs: _t1895, ValueArity: abstraction_with_arity1079[1].(int64)}
	result1082 := _t1896
	p.recordSpan(int(span_start1081), "Upsert")
	return result1082
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1897 := p.parse_bindings()
	bindings1083 := _t1897
	_t1898 := p.parse_formula()
	formula1084 := _t1898
	p.consumeLiteral(")")
	_t1899 := &pb.Abstraction{Vars: listConcat(bindings1083[0].([]*pb.Binding), bindings1083[1].([]*pb.Binding)), Value: formula1084}
	return []interface{}{_t1899, int64(len(bindings1083[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1900 := p.parse_relation_id()
	relation_id1085 := _t1900
	_t1901 := p.parse_abstraction()
	abstraction1086 := _t1901
	var _t1902 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1903 := p.parse_attrs()
		_t1902 = _t1903
	}
	attrs1087 := _t1902
	p.consumeLiteral(")")
	_t1904 := attrs1087
	if attrs1087 == nil {
		_t1904 = []*pb.Attribute{}
	}
	_t1905 := &pb.Break{Name: relation_id1085, Body: abstraction1086, Attrs: _t1904}
	result1089 := _t1905
	p.recordSpan(int(span_start1088), "Break")
	return result1089
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1906 := p.parse_monoid()
	monoid1090 := _t1906
	_t1907 := p.parse_relation_id()
	relation_id1091 := _t1907
	_t1908 := p.parse_abstraction_with_arity()
	abstraction_with_arity1092 := _t1908
	var _t1909 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1910 := p.parse_attrs()
		_t1909 = _t1910
	}
	attrs1093 := _t1909
	p.consumeLiteral(")")
	_t1911 := attrs1093
	if attrs1093 == nil {
		_t1911 = []*pb.Attribute{}
	}
	_t1912 := &pb.MonoidDef{Monoid: monoid1090, Name: relation_id1091, Body: abstraction_with_arity1092[0].(*pb.Abstraction), Attrs: _t1911, ValueArity: abstraction_with_arity1092[1].(int64)}
	result1095 := _t1912
	p.recordSpan(int(span_start1094), "MonoidDef")
	return result1095
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1101 := int64(p.spanStart())
	var _t1913 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1914 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1914 = 3
		} else {
			var _t1915 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1915 = 0
			} else {
				var _t1916 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1916 = 1
				} else {
					var _t1917 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1917 = 2
					} else {
						_t1917 = -1
					}
					_t1916 = _t1917
				}
				_t1915 = _t1916
			}
			_t1914 = _t1915
		}
		_t1913 = _t1914
	} else {
		_t1913 = -1
	}
	prediction1096 := _t1913
	var _t1918 *pb.Monoid
	if prediction1096 == 3 {
		_t1919 := p.parse_sum_monoid()
		sum_monoid1100 := _t1919
		_t1920 := &pb.Monoid{}
		_t1920.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1100}
		_t1918 = _t1920
	} else {
		var _t1921 *pb.Monoid
		if prediction1096 == 2 {
			_t1922 := p.parse_max_monoid()
			max_monoid1099 := _t1922
			_t1923 := &pb.Monoid{}
			_t1923.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1099}
			_t1921 = _t1923
		} else {
			var _t1924 *pb.Monoid
			if prediction1096 == 1 {
				_t1925 := p.parse_min_monoid()
				min_monoid1098 := _t1925
				_t1926 := &pb.Monoid{}
				_t1926.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1098}
				_t1924 = _t1926
			} else {
				var _t1927 *pb.Monoid
				if prediction1096 == 0 {
					_t1928 := p.parse_or_monoid()
					or_monoid1097 := _t1928
					_t1929 := &pb.Monoid{}
					_t1929.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1097}
					_t1927 = _t1929
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1924 = _t1927
			}
			_t1921 = _t1924
		}
		_t1918 = _t1921
	}
	result1102 := _t1918
	p.recordSpan(int(span_start1101), "Monoid")
	return result1102
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1930 := &pb.OrMonoid{}
	result1104 := _t1930
	p.recordSpan(int(span_start1103), "OrMonoid")
	return result1104
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1106 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1931 := p.parse_type()
	type1105 := _t1931
	p.consumeLiteral(")")
	_t1932 := &pb.MinMonoid{Type: type1105}
	result1107 := _t1932
	p.recordSpan(int(span_start1106), "MinMonoid")
	return result1107
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1933 := p.parse_type()
	type1108 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.MaxMonoid{Type: type1108}
	result1110 := _t1934
	p.recordSpan(int(span_start1109), "MaxMonoid")
	return result1110
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1935 := p.parse_type()
	type1111 := _t1935
	p.consumeLiteral(")")
	_t1936 := &pb.SumMonoid{Type: type1111}
	result1113 := _t1936
	p.recordSpan(int(span_start1112), "SumMonoid")
	return result1113
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1118 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1937 := p.parse_monoid()
	monoid1114 := _t1937
	_t1938 := p.parse_relation_id()
	relation_id1115 := _t1938
	_t1939 := p.parse_abstraction_with_arity()
	abstraction_with_arity1116 := _t1939
	var _t1940 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1941 := p.parse_attrs()
		_t1940 = _t1941
	}
	attrs1117 := _t1940
	p.consumeLiteral(")")
	_t1942 := attrs1117
	if attrs1117 == nil {
		_t1942 = []*pb.Attribute{}
	}
	_t1943 := &pb.MonusDef{Monoid: monoid1114, Name: relation_id1115, Body: abstraction_with_arity1116[0].(*pb.Abstraction), Attrs: _t1942, ValueArity: abstraction_with_arity1116[1].(int64)}
	result1119 := _t1943
	p.recordSpan(int(span_start1118), "MonusDef")
	return result1119
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1944 := p.parse_relation_id()
	relation_id1120 := _t1944
	_t1945 := p.parse_abstraction()
	abstraction1121 := _t1945
	_t1946 := p.parse_functional_dependency_keys()
	functional_dependency_keys1122 := _t1946
	_t1947 := p.parse_functional_dependency_values()
	functional_dependency_values1123 := _t1947
	p.consumeLiteral(")")
	_t1948 := &pb.FunctionalDependency{Guard: abstraction1121, Keys: functional_dependency_keys1122, Values: functional_dependency_values1123}
	_t1949 := &pb.Constraint{Name: relation_id1120}
	_t1949.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1948}
	result1125 := _t1949
	p.recordSpan(int(span_start1124), "Constraint")
	return result1125
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1126 := []*pb.Var{}
	cond1127 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1127 {
		_t1950 := p.parse_var()
		item1128 := _t1950
		xs1126 = append(xs1126, item1128)
		cond1127 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1129 := xs1126
	p.consumeLiteral(")")
	return vars1129
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1130 := []*pb.Var{}
	cond1131 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1131 {
		_t1951 := p.parse_var()
		item1132 := _t1951
		xs1130 = append(xs1130, item1132)
		cond1131 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1133 := xs1130
	p.consumeLiteral(")")
	return vars1133
}

func (p *Parser) parse_data() *pb.Data {
	span_start1139 := int64(p.spanStart())
	var _t1952 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1953 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1953 = 3
		} else {
			var _t1954 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1954 = 0
			} else {
				var _t1955 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1955 = 2
				} else {
					var _t1956 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1956 = 1
					} else {
						_t1956 = -1
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
	prediction1134 := _t1952
	var _t1957 *pb.Data
	if prediction1134 == 3 {
		_t1958 := p.parse_iceberg_data()
		iceberg_data1138 := _t1958
		_t1959 := &pb.Data{}
		_t1959.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1138}
		_t1957 = _t1959
	} else {
		var _t1960 *pb.Data
		if prediction1134 == 2 {
			_t1961 := p.parse_csv_data()
			csv_data1137 := _t1961
			_t1962 := &pb.Data{}
			_t1962.DataType = &pb.Data_CsvData{CsvData: csv_data1137}
			_t1960 = _t1962
		} else {
			var _t1963 *pb.Data
			if prediction1134 == 1 {
				_t1964 := p.parse_betree_relation()
				betree_relation1136 := _t1964
				_t1965 := &pb.Data{}
				_t1965.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1136}
				_t1963 = _t1965
			} else {
				var _t1966 *pb.Data
				if prediction1134 == 0 {
					_t1967 := p.parse_edb()
					edb1135 := _t1967
					_t1968 := &pb.Data{}
					_t1968.DataType = &pb.Data_Edb{Edb: edb1135}
					_t1966 = _t1968
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1963 = _t1966
			}
			_t1960 = _t1963
		}
		_t1957 = _t1960
	}
	result1140 := _t1957
	p.recordSpan(int(span_start1139), "Data")
	return result1140
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1144 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1969 := p.parse_relation_id()
	relation_id1141 := _t1969
	_t1970 := p.parse_edb_path()
	edb_path1142 := _t1970
	_t1971 := p.parse_edb_types()
	edb_types1143 := _t1971
	p.consumeLiteral(")")
	_t1972 := &pb.EDB{TargetId: relation_id1141, Path: edb_path1142, Types: edb_types1143}
	result1145 := _t1972
	p.recordSpan(int(span_start1144), "EDB")
	return result1145
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1146 := []string{}
	cond1147 := p.matchLookaheadTerminal("STRING", 0)
	for cond1147 {
		item1148 := p.consumeTerminal("STRING").Value.str
		xs1146 = append(xs1146, item1148)
		cond1147 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1149 := xs1146
	p.consumeLiteral("]")
	return strings1149
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1150 := []*pb.Type{}
	cond1151 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1151 {
		_t1973 := p.parse_type()
		item1152 := _t1973
		xs1150 = append(xs1150, item1152)
		cond1151 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1153 := xs1150
	p.consumeLiteral("]")
	return types1153
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1974 := p.parse_relation_id()
	relation_id1154 := _t1974
	_t1975 := p.parse_betree_info()
	betree_info1155 := _t1975
	p.consumeLiteral(")")
	_t1976 := &pb.BeTreeRelation{Name: relation_id1154, RelationInfo: betree_info1155}
	result1157 := _t1976
	p.recordSpan(int(span_start1156), "BeTreeRelation")
	return result1157
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1161 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1977 := p.parse_betree_info_key_types()
	betree_info_key_types1158 := _t1977
	_t1978 := p.parse_betree_info_value_types()
	betree_info_value_types1159 := _t1978
	_t1979 := p.parse_config_dict()
	config_dict1160 := _t1979
	p.consumeLiteral(")")
	_t1980 := p.construct_betree_info(betree_info_key_types1158, betree_info_value_types1159, config_dict1160)
	result1162 := _t1980
	p.recordSpan(int(span_start1161), "BeTreeInfo")
	return result1162
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1163 := []*pb.Type{}
	cond1164 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1164 {
		_t1981 := p.parse_type()
		item1165 := _t1981
		xs1163 = append(xs1163, item1165)
		cond1164 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1166 := xs1163
	p.consumeLiteral(")")
	return types1166
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1167 := []*pb.Type{}
	cond1168 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1168 {
		_t1982 := p.parse_type()
		item1169 := _t1982
		xs1167 = append(xs1167, item1169)
		cond1168 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1170 := xs1167
	p.consumeLiteral(")")
	return types1170
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1175 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1983 := p.parse_csvlocator()
	csvlocator1171 := _t1983
	_t1984 := p.parse_csv_config()
	csv_config1172 := _t1984
	_t1985 := p.parse_gnf_columns()
	gnf_columns1173 := _t1985
	_t1986 := p.parse_csv_asof()
	csv_asof1174 := _t1986
	p.consumeLiteral(")")
	_t1987 := &pb.CSVData{Locator: csvlocator1171, Config: csv_config1172, Columns: gnf_columns1173, Asof: csv_asof1174}
	result1176 := _t1987
	p.recordSpan(int(span_start1175), "CSVData")
	return result1176
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1179 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1988 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1989 := p.parse_csv_locator_paths()
		_t1988 = _t1989
	}
	csv_locator_paths1177 := _t1988
	var _t1990 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1991 := p.parse_csv_locator_inline_data()
		_t1990 = ptr(_t1991)
	}
	csv_locator_inline_data1178 := _t1990
	p.consumeLiteral(")")
	_t1992 := csv_locator_paths1177
	if csv_locator_paths1177 == nil {
		_t1992 = []string{}
	}
	_t1993 := &pb.CSVLocator{Paths: _t1992, InlineData: []byte(deref(csv_locator_inline_data1178, ""))}
	result1180 := _t1993
	p.recordSpan(int(span_start1179), "CSVLocator")
	return result1180
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1181 := []string{}
	cond1182 := p.matchLookaheadTerminal("STRING", 0)
	for cond1182 {
		item1183 := p.consumeTerminal("STRING").Value.str
		xs1181 = append(xs1181, item1183)
		cond1182 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1184 := xs1181
	p.consumeLiteral(")")
	return strings1184
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1185 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1185
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1188 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1994 := p.parse_config_dict()
	config_dict1186 := _t1994
	var _t1995 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1996 := p.parse__storage_integration()
		_t1995 = _t1996
	}
	_storage_integration1187 := _t1995
	p.consumeLiteral(")")
	_t1997 := p.construct_csv_config(config_dict1186, _storage_integration1187)
	result1189 := _t1997
	p.recordSpan(int(span_start1188), "CSVConfig")
	return result1189
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t1998 := p.parse_config_dict()
	config_dict1190 := _t1998
	p.consumeLiteral(")")
	return config_dict1190
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1191 := []*pb.GNFColumn{}
	cond1192 := p.matchLookaheadLiteral("(", 0)
	for cond1192 {
		_t1999 := p.parse_gnf_column()
		item1193 := _t1999
		xs1191 = append(xs1191, item1193)
		cond1192 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1194 := xs1191
	p.consumeLiteral(")")
	return gnf_columns1194
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1201 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t2000 := p.parse_gnf_column_path()
	gnf_column_path1195 := _t2000
	var _t2001 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2002 := p.parse_relation_id()
		_t2001 = _t2002
	}
	relation_id1196 := _t2001
	p.consumeLiteral("[")
	xs1197 := []*pb.Type{}
	cond1198 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1198 {
		_t2003 := p.parse_type()
		item1199 := _t2003
		xs1197 = append(xs1197, item1199)
		cond1198 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1200 := xs1197
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2004 := &pb.GNFColumn{ColumnPath: gnf_column_path1195, TargetId: relation_id1196, Types: types1200}
	result1202 := _t2004
	p.recordSpan(int(span_start1201), "GNFColumn")
	return result1202
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2005 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2005 = 1
	} else {
		var _t2006 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2006 = 0
		} else {
			_t2006 = -1
		}
		_t2005 = _t2006
	}
	prediction1203 := _t2005
	var _t2007 []string
	if prediction1203 == 1 {
		p.consumeLiteral("[")
		xs1205 := []string{}
		cond1206 := p.matchLookaheadTerminal("STRING", 0)
		for cond1206 {
			item1207 := p.consumeTerminal("STRING").Value.str
			xs1205 = append(xs1205, item1207)
			cond1206 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1208 := xs1205
		p.consumeLiteral("]")
		_t2007 = strings1208
	} else {
		var _t2008 []string
		if prediction1203 == 0 {
			string1204 := p.consumeTerminal("STRING").Value.str
			_ = string1204
			_t2008 = []string{string1204}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2007 = _t2008
	}
	return _t2007
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1209 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1209
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1216 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2009 := p.parse_iceberg_locator()
	iceberg_locator1210 := _t2009
	_t2010 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1211 := _t2010
	_t2011 := p.parse_gnf_columns()
	gnf_columns1212 := _t2011
	var _t2012 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2013 := p.parse_iceberg_from_snapshot()
		_t2012 = ptr(_t2013)
	}
	iceberg_from_snapshot1213 := _t2012
	var _t2014 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2015 := p.parse_iceberg_to_snapshot()
		_t2014 = ptr(_t2015)
	}
	iceberg_to_snapshot1214 := _t2014
	_t2016 := p.parse_boolean_value()
	boolean_value1215 := _t2016
	p.consumeLiteral(")")
	_t2017 := p.construct_iceberg_data(iceberg_locator1210, iceberg_catalog_config1211, gnf_columns1212, iceberg_from_snapshot1213, iceberg_to_snapshot1214, boolean_value1215)
	result1217 := _t2017
	p.recordSpan(int(span_start1216), "IcebergData")
	return result1217
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1221 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2018 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1218 := _t2018
	_t2019 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1219 := _t2019
	_t2020 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1220 := _t2020
	p.consumeLiteral(")")
	_t2021 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1218, Namespace: iceberg_locator_namespace1219, Warehouse: iceberg_locator_warehouse1220}
	result1222 := _t2021
	p.recordSpan(int(span_start1221), "IcebergLocator")
	return result1222
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1223 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1223
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1224 := []string{}
	cond1225 := p.matchLookaheadTerminal("STRING", 0)
	for cond1225 {
		item1226 := p.consumeTerminal("STRING").Value.str
		xs1224 = append(xs1224, item1226)
		cond1225 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1227 := xs1224
	p.consumeLiteral(")")
	return strings1227
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1228 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1228
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1233 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2022 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1229 := _t2022
	var _t2023 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2024 := p.parse_iceberg_catalog_config_scope()
		_t2023 = ptr(_t2024)
	}
	iceberg_catalog_config_scope1230 := _t2023
	_t2025 := p.parse_iceberg_properties()
	iceberg_properties1231 := _t2025
	_t2026 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1232 := _t2026
	p.consumeLiteral(")")
	_t2027 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1229, iceberg_catalog_config_scope1230, iceberg_properties1231, iceberg_auth_properties1232)
	result1234 := _t2027
	p.recordSpan(int(span_start1233), "IcebergCatalogConfig")
	return result1234
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1235 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1235
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1236 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1236
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1237 := [][]interface{}{}
	cond1238 := p.matchLookaheadLiteral("(", 0)
	for cond1238 {
		_t2028 := p.parse_iceberg_property_entry()
		item1239 := _t2028
		xs1237 = append(xs1237, item1239)
		cond1238 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1240 := xs1237
	p.consumeLiteral(")")
	return iceberg_property_entrys1240
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1241 := p.consumeTerminal("STRING").Value.str
	string_31242 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1241, string_31242}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1243 := [][]interface{}{}
	cond1244 := p.matchLookaheadLiteral("(", 0)
	for cond1244 {
		_t2029 := p.parse_iceberg_masked_property_entry()
		item1245 := _t2029
		xs1243 = append(xs1243, item1245)
		cond1244 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1246 := xs1243
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1246
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1247 := p.consumeTerminal("STRING").Value.str
	string_31248 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1247, string_31248}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1249 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1249
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1250 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1250
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1252 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2030 := p.parse_fragment_id()
	fragment_id1251 := _t2030
	p.consumeLiteral(")")
	_t2031 := &pb.Undefine{FragmentId: fragment_id1251}
	result1253 := _t2031
	p.recordSpan(int(span_start1252), "Undefine")
	return result1253
}

func (p *Parser) parse_context() *pb.Context {
	span_start1258 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1254 := []*pb.RelationId{}
	cond1255 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1255 {
		_t2032 := p.parse_relation_id()
		item1256 := _t2032
		xs1254 = append(xs1254, item1256)
		cond1255 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1257 := xs1254
	p.consumeLiteral(")")
	_t2033 := &pb.Context{Relations: relation_ids1257}
	result1259 := _t2033
	p.recordSpan(int(span_start1258), "Context")
	return result1259
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1265 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2034 := p.parse_edb_path()
	edb_path1260 := _t2034
	xs1261 := []*pb.SnapshotMapping{}
	cond1262 := p.matchLookaheadLiteral("[", 0)
	for cond1262 {
		_t2035 := p.parse_snapshot_mapping()
		item1263 := _t2035
		xs1261 = append(xs1261, item1263)
		cond1262 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1264 := xs1261
	p.consumeLiteral(")")
	_t2036 := &pb.Snapshot{Prefix: edb_path1260, Mappings: snapshot_mappings1264}
	result1266 := _t2036
	p.recordSpan(int(span_start1265), "Snapshot")
	return result1266
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1269 := int64(p.spanStart())
	_t2037 := p.parse_edb_path()
	edb_path1267 := _t2037
	_t2038 := p.parse_relation_id()
	relation_id1268 := _t2038
	_t2039 := &pb.SnapshotMapping{DestinationPath: edb_path1267, SourceRelation: relation_id1268}
	result1270 := _t2039
	p.recordSpan(int(span_start1269), "SnapshotMapping")
	return result1270
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1271 := []*pb.Read{}
	cond1272 := p.matchLookaheadLiteral("(", 0)
	for cond1272 {
		_t2040 := p.parse_read()
		item1273 := _t2040
		xs1271 = append(xs1271, item1273)
		cond1272 = p.matchLookaheadLiteral("(", 0)
	}
	reads1274 := xs1271
	p.consumeLiteral(")")
	return reads1274
}

func (p *Parser) parse_read() *pb.Read {
	span_start1282 := int64(p.spanStart())
	var _t2041 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2042 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2042 = 2
		} else {
			var _t2043 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2043 = 1
			} else {
				var _t2044 int64
				if p.matchLookaheadLiteral("export_output", 1) {
					_t2044 = 5
				} else {
					var _t2045 int64
					if p.matchLookaheadLiteral("export_iceberg", 1) {
						_t2045 = 4
					} else {
						var _t2046 int64
						if p.matchLookaheadLiteral("export", 1) {
							_t2046 = 4
						} else {
							var _t2047 int64
							if p.matchLookaheadLiteral("demand", 1) {
								_t2047 = 0
							} else {
								var _t2048 int64
								if p.matchLookaheadLiteral("abort", 1) {
									_t2048 = 3
								} else {
									_t2048 = -1
								}
								_t2047 = _t2048
							}
							_t2046 = _t2047
						}
						_t2045 = _t2046
					}
					_t2044 = _t2045
				}
				_t2043 = _t2044
			}
			_t2042 = _t2043
		}
		_t2041 = _t2042
	} else {
		_t2041 = -1
	}
	prediction1275 := _t2041
	var _t2049 *pb.Read
	if prediction1275 == 5 {
		_t2050 := p.parse_export_output()
		export_output1281 := _t2050
		_t2051 := &pb.Read{}
		_t2051.ReadType = &pb.Read_ExportOutput{ExportOutput: export_output1281}
		_t2049 = _t2051
	} else {
		var _t2052 *pb.Read
		if prediction1275 == 4 {
			_t2053 := p.parse_export()
			export1280 := _t2053
			_t2054 := &pb.Read{}
			_t2054.ReadType = &pb.Read_Export{Export: export1280}
			_t2052 = _t2054
		} else {
			var _t2055 *pb.Read
			if prediction1275 == 3 {
				_t2056 := p.parse_abort()
				abort1279 := _t2056
				_t2057 := &pb.Read{}
				_t2057.ReadType = &pb.Read_Abort{Abort: abort1279}
				_t2055 = _t2057
			} else {
				var _t2058 *pb.Read
				if prediction1275 == 2 {
					_t2059 := p.parse_what_if()
					what_if1278 := _t2059
					_t2060 := &pb.Read{}
					_t2060.ReadType = &pb.Read_WhatIf{WhatIf: what_if1278}
					_t2058 = _t2060
				} else {
					var _t2061 *pb.Read
					if prediction1275 == 1 {
						_t2062 := p.parse_output()
						output1277 := _t2062
						_t2063 := &pb.Read{}
						_t2063.ReadType = &pb.Read_Output{Output: output1277}
						_t2061 = _t2063
					} else {
						var _t2064 *pb.Read
						if prediction1275 == 0 {
							_t2065 := p.parse_demand()
							demand1276 := _t2065
							_t2066 := &pb.Read{}
							_t2066.ReadType = &pb.Read_Demand{Demand: demand1276}
							_t2064 = _t2066
						} else {
							panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
						}
						_t2061 = _t2064
					}
					_t2058 = _t2061
				}
				_t2055 = _t2058
			}
			_t2052 = _t2055
		}
		_t2049 = _t2052
	}
	result1283 := _t2049
	p.recordSpan(int(span_start1282), "Read")
	return result1283
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1285 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2067 := p.parse_relation_id()
	relation_id1284 := _t2067
	p.consumeLiteral(")")
	_t2068 := &pb.Demand{RelationId: relation_id1284}
	result1286 := _t2068
	p.recordSpan(int(span_start1285), "Demand")
	return result1286
}

func (p *Parser) parse_output() *pb.Output {
	span_start1289 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2069 := p.parse_name()
	name1287 := _t2069
	_t2070 := p.parse_relation_id()
	relation_id1288 := _t2070
	p.consumeLiteral(")")
	_t2071 := &pb.Output{Name: name1287, RelationId: relation_id1288}
	result1290 := _t2071
	p.recordSpan(int(span_start1289), "Output")
	return result1290
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1293 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2072 := p.parse_name()
	name1291 := _t2072
	_t2073 := p.parse_epoch()
	epoch1292 := _t2073
	p.consumeLiteral(")")
	_t2074 := &pb.WhatIf{Branch: name1291, Epoch: epoch1292}
	result1294 := _t2074
	p.recordSpan(int(span_start1293), "WhatIf")
	return result1294
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1297 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2075 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2076 := p.parse_name()
		_t2075 = ptr(_t2076)
	}
	name1295 := _t2075
	_t2077 := p.parse_relation_id()
	relation_id1296 := _t2077
	p.consumeLiteral(")")
	_t2078 := &pb.Abort{Name: deref(name1295, "abort"), RelationId: relation_id1296}
	result1298 := _t2078
	p.recordSpan(int(span_start1297), "Abort")
	return result1298
}

func (p *Parser) parse_export() *pb.Export {
	span_start1302 := int64(p.spanStart())
	var _t2079 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2080 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2080 = 1
		} else {
			var _t2081 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2081 = 0
			} else {
				_t2081 = -1
			}
			_t2080 = _t2081
		}
		_t2079 = _t2080
	} else {
		_t2079 = -1
	}
	prediction1299 := _t2079
	var _t2082 *pb.Export
	if prediction1299 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2083 := p.parse_export_iceberg_config()
		export_iceberg_config1301 := _t2083
		p.consumeLiteral(")")
		_t2084 := &pb.Export{}
		_t2084.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1301}
		_t2082 = _t2084
	} else {
		var _t2085 *pb.Export
		if prediction1299 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2086 := p.parse_export_csv_config()
			export_csv_config1300 := _t2086
			p.consumeLiteral(")")
			_t2087 := &pb.Export{}
			_t2087.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1300}
			_t2085 = _t2087
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2082 = _t2085
	}
	result1303 := _t2082
	p.recordSpan(int(span_start1302), "Export")
	return result1303
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1311 := int64(p.spanStart())
	var _t2088 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2089 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2089 = 0
		} else {
			var _t2090 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2090 = 1
			} else {
				_t2090 = -1
			}
			_t2089 = _t2090
		}
		_t2088 = _t2089
	} else {
		_t2088 = -1
	}
	prediction1304 := _t2088
	var _t2091 *pb.ExportCSVConfig
	if prediction1304 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2092 := p.parse_export_csv_path()
		export_csv_path1308 := _t2092
		_t2093 := p.parse_export_csv_columns_list()
		export_csv_columns_list1309 := _t2093
		_t2094 := p.parse_config_dict()
		config_dict1310 := _t2094
		p.consumeLiteral(")")
		_t2095 := p.construct_export_csv_config(export_csv_path1308, export_csv_columns_list1309, config_dict1310)
		_t2091 = _t2095
	} else {
		var _t2096 *pb.ExportCSVConfig
		if prediction1304 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2097 := p.parse_export_csv_path()
			export_csv_path1305 := _t2097
			_t2098 := p.parse_export_csv_source()
			export_csv_source1306 := _t2098
			_t2099 := p.parse_csv_config()
			csv_config1307 := _t2099
			p.consumeLiteral(")")
			_t2100 := p.construct_export_csv_config_with_source(export_csv_path1305, export_csv_source1306, csv_config1307)
			_t2096 = _t2100
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2091 = _t2096
	}
	result1312 := _t2091
	p.recordSpan(int(span_start1311), "ExportCSVConfig")
	return result1312
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1313 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1313
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1320 := int64(p.spanStart())
	var _t2101 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2102 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2102 = 1
		} else {
			var _t2103 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2103 = 0
			} else {
				_t2103 = -1
			}
			_t2102 = _t2103
		}
		_t2101 = _t2102
	} else {
		_t2101 = -1
	}
	prediction1314 := _t2101
	var _t2104 *pb.ExportCSVSource
	if prediction1314 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2105 := p.parse_relation_id()
		relation_id1319 := _t2105
		p.consumeLiteral(")")
		_t2106 := &pb.ExportCSVSource{}
		_t2106.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1319}
		_t2104 = _t2106
	} else {
		var _t2107 *pb.ExportCSVSource
		if prediction1314 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1315 := []*pb.ExportCSVColumn{}
			cond1316 := p.matchLookaheadLiteral("(", 0)
			for cond1316 {
				_t2108 := p.parse_export_csv_column()
				item1317 := _t2108
				xs1315 = append(xs1315, item1317)
				cond1316 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1318 := xs1315
			p.consumeLiteral(")")
			_t2109 := &pb.ExportCSVColumns{Columns: export_csv_columns1318}
			_t2110 := &pb.ExportCSVSource{}
			_t2110.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2109}
			_t2107 = _t2110
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2104 = _t2107
	}
	result1321 := _t2104
	p.recordSpan(int(span_start1320), "ExportCSVSource")
	return result1321
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1324 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1322 := p.consumeTerminal("STRING").Value.str
	_t2111 := p.parse_relation_id()
	relation_id1323 := _t2111
	p.consumeLiteral(")")
	_t2112 := &pb.ExportCSVColumn{ColumnName: string1322, ColumnData: relation_id1323}
	result1325 := _t2112
	p.recordSpan(int(span_start1324), "ExportCSVColumn")
	return result1325
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1326 := []*pb.ExportCSVColumn{}
	cond1327 := p.matchLookaheadLiteral("(", 0)
	for cond1327 {
		_t2113 := p.parse_export_csv_column()
		item1328 := _t2113
		xs1326 = append(xs1326, item1328)
		cond1327 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1329 := xs1326
	p.consumeLiteral(")")
	return export_csv_columns1329
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1335 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2114 := p.parse_iceberg_locator()
	iceberg_locator1330 := _t2114
	_t2115 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1331 := _t2115
	_t2116 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1332 := _t2116
	_t2117 := p.parse_iceberg_table_properties()
	iceberg_table_properties1333 := _t2117
	var _t2118 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2119 := p.parse_config_dict()
		_t2118 = _t2119
	}
	config_dict1334 := _t2118
	p.consumeLiteral(")")
	_t2120 := p.construct_export_iceberg_config_full(iceberg_locator1330, iceberg_catalog_config1331, export_iceberg_table_def1332, iceberg_table_properties1333, config_dict1334)
	result1336 := _t2120
	p.recordSpan(int(span_start1335), "ExportIcebergConfig")
	return result1336
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1338 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2121 := p.parse_relation_id()
	relation_id1337 := _t2121
	p.consumeLiteral(")")
	result1339 := relation_id1337
	p.recordSpan(int(span_start1338), "RelationId")
	return result1339
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1340 := [][]interface{}{}
	cond1341 := p.matchLookaheadLiteral("(", 0)
	for cond1341 {
		_t2122 := p.parse_iceberg_property_entry()
		item1342 := _t2122
		xs1340 = append(xs1340, item1342)
		cond1341 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1343 := xs1340
	p.consumeLiteral(")")
	return iceberg_property_entrys1343
}

func (p *Parser) parse_export_output() *pb.ExportOutput {
	span_start1346 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_output")
	_t2123 := p.parse_name()
	name1344 := _t2123
	_t2124 := p.parse_export_csv_output()
	export_csv_output1345 := _t2124
	p.consumeLiteral(")")
	_t2125 := &pb.ExportOutput{Name: name1344}
	_t2125.ExportOutput = &pb.ExportOutput_Csv{Csv: export_csv_output1345}
	result1347 := _t2125
	p.recordSpan(int(span_start1346), "ExportOutput")
	return result1347
}

func (p *Parser) parse_export_csv_output() *pb.ExportCSVOutput {
	span_start1350 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv")
	_t2126 := p.parse_export_csv_source()
	export_csv_source1348 := _t2126
	_t2127 := p.parse_csv_config()
	csv_config1349 := _t2127
	p.consumeLiteral(")")
	_t2128 := &pb.ExportCSVOutput{CsvSource: export_csv_source1348, CsvConfig: csv_config1349}
	result1351 := _t2128
	p.recordSpan(int(span_start1350), "ExportCSVOutput")
	return result1351
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
