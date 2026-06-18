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
	var _t2126 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2126
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2127 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2127
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2128 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2128
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2129 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2129
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2130 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2130
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2131 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2131
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2132 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2132
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2133 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2133
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2134 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2134
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2135 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2135
	_t2136 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2136
	_t2137 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2137
	_t2138 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2138
	_t2139 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2139
	_t2140 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2140
	_t2141 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2141
	_t2142 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2142
	_t2143 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2143
	_t2144 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2144
	_t2145 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2145
	_t2146 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2146
	_t2147 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2147
	_t2148 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2148
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2149 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2149
	config := dictFromList(storage_integration_opt)
	_t2150 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2151 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2152 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2153 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2154 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2155 := &pb.StorageIntegration{Provider: _t2150, AzureSasToken: _t2151, S3Region: _t2152, S3AccessKeyId: _t2153, S3SecretAccessKey: _t2154}
	return _t2155
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2156 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2156
	_t2157 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2157
	_t2158 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2158
	_t2159 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2159
	_t2160 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2160
	_t2161 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2161
	_t2162 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2162
	_t2163 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2163
	_t2164 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2164
	_t2165 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2165.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2165.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2165
	_t2166 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2166
}

func (p *Parser) default_configure() *pb.Configure {
	_t2167 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2167
	_t2168 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2168
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
	_t2169 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2169
	_t2170 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2170
	_t2171 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2171
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2172 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2172
	_t2173 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2173
	_t2174 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2174
	_t2175 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2175
	_t2176 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2176
	_t2177 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2177
	_t2178 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2178
	_t2179 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2179
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2180 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2180
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2181 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2181
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2182 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2182
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2183 := config_dict
	if config_dict == nil {
		_t2183 = [][]interface{}{}
	}
	cfg := dictFromList(_t2183)
	_t2184 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2184
	_t2185 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2185
	_t2186 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2186
	table_props := stringMapFromPairs(table_property_pairs)
	_t2187 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2187
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start681 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1350 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1351 := p.parse_configure()
		_t1350 = _t1351
	}
	configure675 := _t1350
	var _t1352 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1353 := p.parse_sync()
		_t1352 = _t1353
	}
	sync676 := _t1352
	xs677 := []*pb.Epoch{}
	cond678 := p.matchLookaheadLiteral("(", 0)
	for cond678 {
		_t1354 := p.parse_epoch()
		item679 := _t1354
		xs677 = append(xs677, item679)
		cond678 = p.matchLookaheadLiteral("(", 0)
	}
	epochs680 := xs677
	p.consumeLiteral(")")
	_t1355 := p.default_configure()
	_t1356 := configure675
	if configure675 == nil {
		_t1356 = _t1355
	}
	_t1357 := &pb.Transaction{Epochs: epochs680, Configure: _t1356, Sync: sync676}
	result682 := _t1357
	p.recordSpan(int(span_start681), "Transaction")
	return result682
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start684 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1358 := p.parse_config_dict()
	config_dict683 := _t1358
	p.consumeLiteral(")")
	_t1359 := p.construct_configure(config_dict683)
	result685 := _t1359
	p.recordSpan(int(span_start684), "Configure")
	return result685
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs686 := [][]interface{}{}
	cond687 := p.matchLookaheadLiteral(":", 0)
	for cond687 {
		_t1360 := p.parse_config_key_value()
		item688 := _t1360
		xs686 = append(xs686, item688)
		cond687 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values689 := xs686
	p.consumeLiteral("}")
	return config_key_values689
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol690 := p.consumeTerminal("SYMBOL").Value.str
	_t1361 := p.parse_raw_value()
	raw_value691 := _t1361
	return []interface{}{symbol690, raw_value691}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start705 := int64(p.spanStart())
	var _t1362 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1362 = 12
	} else {
		var _t1363 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1363 = 11
		} else {
			var _t1364 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1364 = 12
			} else {
				var _t1365 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1366 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1366 = 1
					} else {
						var _t1367 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1367 = 0
						} else {
							_t1367 = -1
						}
						_t1366 = _t1367
					}
					_t1365 = _t1366
				} else {
					var _t1368 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1368 = 7
					} else {
						var _t1369 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1369 = 8
						} else {
							var _t1370 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1370 = 2
							} else {
								var _t1371 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1371 = 3
								} else {
									var _t1372 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1372 = 9
									} else {
										var _t1373 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1373 = 4
										} else {
											var _t1374 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1374 = 5
											} else {
												var _t1375 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1375 = 6
												} else {
													var _t1376 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1376 = 10
													} else {
														_t1376 = -1
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
							_t1369 = _t1370
						}
						_t1368 = _t1369
					}
					_t1365 = _t1368
				}
				_t1364 = _t1365
			}
			_t1363 = _t1364
		}
		_t1362 = _t1363
	}
	prediction692 := _t1362
	var _t1377 *pb.Value
	if prediction692 == 12 {
		_t1378 := p.parse_boolean_value()
		boolean_value704 := _t1378
		_t1379 := &pb.Value{}
		_t1379.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value704}
		_t1377 = _t1379
	} else {
		var _t1380 *pb.Value
		if prediction692 == 11 {
			p.consumeLiteral("missing")
			_t1381 := &pb.MissingValue{}
			_t1382 := &pb.Value{}
			_t1382.Value = &pb.Value_MissingValue{MissingValue: _t1381}
			_t1380 = _t1382
		} else {
			var _t1383 *pb.Value
			if prediction692 == 10 {
				decimal703 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1384 := &pb.Value{}
				_t1384.Value = &pb.Value_DecimalValue{DecimalValue: decimal703}
				_t1383 = _t1384
			} else {
				var _t1385 *pb.Value
				if prediction692 == 9 {
					int128702 := p.consumeTerminal("INT128").Value.int128
					_t1386 := &pb.Value{}
					_t1386.Value = &pb.Value_Int128Value{Int128Value: int128702}
					_t1385 = _t1386
				} else {
					var _t1387 *pb.Value
					if prediction692 == 8 {
						uint128701 := p.consumeTerminal("UINT128").Value.uint128
						_t1388 := &pb.Value{}
						_t1388.Value = &pb.Value_Uint128Value{Uint128Value: uint128701}
						_t1387 = _t1388
					} else {
						var _t1389 *pb.Value
						if prediction692 == 7 {
							uint32700 := p.consumeTerminal("UINT32").Value.u32
							_t1390 := &pb.Value{}
							_t1390.Value = &pb.Value_Uint32Value{Uint32Value: uint32700}
							_t1389 = _t1390
						} else {
							var _t1391 *pb.Value
							if prediction692 == 6 {
								float699 := p.consumeTerminal("FLOAT").Value.f64
								_t1392 := &pb.Value{}
								_t1392.Value = &pb.Value_FloatValue{FloatValue: float699}
								_t1391 = _t1392
							} else {
								var _t1393 *pb.Value
								if prediction692 == 5 {
									float32698 := p.consumeTerminal("FLOAT32").Value.f32
									_t1394 := &pb.Value{}
									_t1394.Value = &pb.Value_Float32Value{Float32Value: float32698}
									_t1393 = _t1394
								} else {
									var _t1395 *pb.Value
									if prediction692 == 4 {
										int697 := p.consumeTerminal("INT").Value.i64
										_t1396 := &pb.Value{}
										_t1396.Value = &pb.Value_IntValue{IntValue: int697}
										_t1395 = _t1396
									} else {
										var _t1397 *pb.Value
										if prediction692 == 3 {
											int32696 := p.consumeTerminal("INT32").Value.i32
											_t1398 := &pb.Value{}
											_t1398.Value = &pb.Value_Int32Value{Int32Value: int32696}
											_t1397 = _t1398
										} else {
											var _t1399 *pb.Value
											if prediction692 == 2 {
												string695 := p.consumeTerminal("STRING").Value.str
												_t1400 := &pb.Value{}
												_t1400.Value = &pb.Value_StringValue{StringValue: string695}
												_t1399 = _t1400
											} else {
												var _t1401 *pb.Value
												if prediction692 == 1 {
													_t1402 := p.parse_raw_datetime()
													raw_datetime694 := _t1402
													_t1403 := &pb.Value{}
													_t1403.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime694}
													_t1401 = _t1403
												} else {
													var _t1404 *pb.Value
													if prediction692 == 0 {
														_t1405 := p.parse_raw_date()
														raw_date693 := _t1405
														_t1406 := &pb.Value{}
														_t1406.Value = &pb.Value_DateValue{DateValue: raw_date693}
														_t1404 = _t1406
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1401 = _t1404
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
				_t1383 = _t1385
			}
			_t1380 = _t1383
		}
		_t1377 = _t1380
	}
	result706 := _t1377
	p.recordSpan(int(span_start705), "Value")
	return result706
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start710 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int707 := p.consumeTerminal("INT").Value.i64
	int_3708 := p.consumeTerminal("INT").Value.i64
	int_4709 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1407 := &pb.DateValue{Year: int32(int707), Month: int32(int_3708), Day: int32(int_4709)}
	result711 := _t1407
	p.recordSpan(int(span_start710), "DateValue")
	return result711
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start719 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int712 := p.consumeTerminal("INT").Value.i64
	int_3713 := p.consumeTerminal("INT").Value.i64
	int_4714 := p.consumeTerminal("INT").Value.i64
	int_5715 := p.consumeTerminal("INT").Value.i64
	int_6716 := p.consumeTerminal("INT").Value.i64
	int_7717 := p.consumeTerminal("INT").Value.i64
	var _t1408 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1408 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8718 := _t1408
	p.consumeLiteral(")")
	_t1409 := &pb.DateTimeValue{Year: int32(int712), Month: int32(int_3713), Day: int32(int_4714), Hour: int32(int_5715), Minute: int32(int_6716), Second: int32(int_7717), Microsecond: int32(deref(int_8718, 0))}
	result720 := _t1409
	p.recordSpan(int(span_start719), "DateTimeValue")
	return result720
}

func (p *Parser) parse_boolean_value() bool {
	var _t1410 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1410 = 0
	} else {
		var _t1411 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1411 = 1
		} else {
			_t1411 = -1
		}
		_t1410 = _t1411
	}
	prediction721 := _t1410
	var _t1412 bool
	if prediction721 == 1 {
		p.consumeLiteral("false")
		_t1412 = false
	} else {
		var _t1413 bool
		if prediction721 == 0 {
			p.consumeLiteral("true")
			_t1413 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1412 = _t1413
	}
	return _t1412
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start726 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs722 := []*pb.FragmentId{}
	cond723 := p.matchLookaheadLiteral(":", 0)
	for cond723 {
		_t1414 := p.parse_fragment_id()
		item724 := _t1414
		xs722 = append(xs722, item724)
		cond723 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids725 := xs722
	p.consumeLiteral(")")
	_t1415 := &pb.Sync{Fragments: fragment_ids725}
	result727 := _t1415
	p.recordSpan(int(span_start726), "Sync")
	return result727
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start729 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol728 := p.consumeTerminal("SYMBOL").Value.str
	result730 := &pb.FragmentId{Id: []byte(symbol728)}
	p.recordSpan(int(span_start729), "FragmentId")
	return result730
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start733 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1416 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1417 := p.parse_epoch_writes()
		_t1416 = _t1417
	}
	epoch_writes731 := _t1416
	var _t1418 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1419 := p.parse_epoch_reads()
		_t1418 = _t1419
	}
	epoch_reads732 := _t1418
	p.consumeLiteral(")")
	_t1420 := epoch_writes731
	if epoch_writes731 == nil {
		_t1420 = []*pb.Write{}
	}
	_t1421 := epoch_reads732
	if epoch_reads732 == nil {
		_t1421 = []*pb.Read{}
	}
	_t1422 := &pb.Epoch{Writes: _t1420, Reads: _t1421}
	result734 := _t1422
	p.recordSpan(int(span_start733), "Epoch")
	return result734
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs735 := []*pb.Write{}
	cond736 := p.matchLookaheadLiteral("(", 0)
	for cond736 {
		_t1423 := p.parse_write()
		item737 := _t1423
		xs735 = append(xs735, item737)
		cond736 = p.matchLookaheadLiteral("(", 0)
	}
	writes738 := xs735
	p.consumeLiteral(")")
	return writes738
}

func (p *Parser) parse_write() *pb.Write {
	span_start744 := int64(p.spanStart())
	var _t1424 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1425 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1425 = 1
		} else {
			var _t1426 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1426 = 3
			} else {
				var _t1427 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1427 = 0
				} else {
					var _t1428 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1428 = 2
					} else {
						_t1428 = -1
					}
					_t1427 = _t1428
				}
				_t1426 = _t1427
			}
			_t1425 = _t1426
		}
		_t1424 = _t1425
	} else {
		_t1424 = -1
	}
	prediction739 := _t1424
	var _t1429 *pb.Write
	if prediction739 == 3 {
		_t1430 := p.parse_snapshot()
		snapshot743 := _t1430
		_t1431 := &pb.Write{}
		_t1431.WriteType = &pb.Write_Snapshot{Snapshot: snapshot743}
		_t1429 = _t1431
	} else {
		var _t1432 *pb.Write
		if prediction739 == 2 {
			_t1433 := p.parse_context()
			context742 := _t1433
			_t1434 := &pb.Write{}
			_t1434.WriteType = &pb.Write_Context{Context: context742}
			_t1432 = _t1434
		} else {
			var _t1435 *pb.Write
			if prediction739 == 1 {
				_t1436 := p.parse_undefine()
				undefine741 := _t1436
				_t1437 := &pb.Write{}
				_t1437.WriteType = &pb.Write_Undefine{Undefine: undefine741}
				_t1435 = _t1437
			} else {
				var _t1438 *pb.Write
				if prediction739 == 0 {
					_t1439 := p.parse_define()
					define740 := _t1439
					_t1440 := &pb.Write{}
					_t1440.WriteType = &pb.Write_Define{Define: define740}
					_t1438 = _t1440
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1435 = _t1438
			}
			_t1432 = _t1435
		}
		_t1429 = _t1432
	}
	result745 := _t1429
	p.recordSpan(int(span_start744), "Write")
	return result745
}

func (p *Parser) parse_define() *pb.Define {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1441 := p.parse_fragment()
	fragment746 := _t1441
	p.consumeLiteral(")")
	_t1442 := &pb.Define{Fragment: fragment746}
	result748 := _t1442
	p.recordSpan(int(span_start747), "Define")
	return result748
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start754 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1443 := p.parse_new_fragment_id()
	new_fragment_id749 := _t1443
	xs750 := []*pb.Declaration{}
	cond751 := p.matchLookaheadLiteral("(", 0)
	for cond751 {
		_t1444 := p.parse_declaration()
		item752 := _t1444
		xs750 = append(xs750, item752)
		cond751 = p.matchLookaheadLiteral("(", 0)
	}
	declarations753 := xs750
	p.consumeLiteral(")")
	result755 := p.constructFragment(new_fragment_id749, declarations753)
	p.recordSpan(int(span_start754), "Fragment")
	return result755
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start757 := int64(p.spanStart())
	_t1445 := p.parse_fragment_id()
	fragment_id756 := _t1445
	p.startFragment(fragment_id756)
	result758 := fragment_id756
	p.recordSpan(int(span_start757), "FragmentId")
	return result758
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start764 := int64(p.spanStart())
	var _t1446 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1447 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1447 = 3
		} else {
			var _t1448 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1448 = 2
			} else {
				var _t1449 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1449 = 3
				} else {
					var _t1450 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1450 = 0
					} else {
						var _t1451 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1451 = 3
						} else {
							var _t1452 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1452 = 3
							} else {
								var _t1453 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1453 = 1
								} else {
									_t1453 = -1
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
			}
			_t1447 = _t1448
		}
		_t1446 = _t1447
	} else {
		_t1446 = -1
	}
	prediction759 := _t1446
	var _t1454 *pb.Declaration
	if prediction759 == 3 {
		_t1455 := p.parse_data()
		data763 := _t1455
		_t1456 := &pb.Declaration{}
		_t1456.DeclarationType = &pb.Declaration_Data{Data: data763}
		_t1454 = _t1456
	} else {
		var _t1457 *pb.Declaration
		if prediction759 == 2 {
			_t1458 := p.parse_constraint()
			constraint762 := _t1458
			_t1459 := &pb.Declaration{}
			_t1459.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint762}
			_t1457 = _t1459
		} else {
			var _t1460 *pb.Declaration
			if prediction759 == 1 {
				_t1461 := p.parse_algorithm()
				algorithm761 := _t1461
				_t1462 := &pb.Declaration{}
				_t1462.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm761}
				_t1460 = _t1462
			} else {
				var _t1463 *pb.Declaration
				if prediction759 == 0 {
					_t1464 := p.parse_def()
					def760 := _t1464
					_t1465 := &pb.Declaration{}
					_t1465.DeclarationType = &pb.Declaration_Def{Def: def760}
					_t1463 = _t1465
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1460 = _t1463
			}
			_t1457 = _t1460
		}
		_t1454 = _t1457
	}
	result765 := _t1454
	p.recordSpan(int(span_start764), "Declaration")
	return result765
}

func (p *Parser) parse_def() *pb.Def {
	span_start769 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1466 := p.parse_relation_id()
	relation_id766 := _t1466
	_t1467 := p.parse_abstraction()
	abstraction767 := _t1467
	var _t1468 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1469 := p.parse_attrs()
		_t1468 = _t1469
	}
	attrs768 := _t1468
	p.consumeLiteral(")")
	_t1470 := attrs768
	if attrs768 == nil {
		_t1470 = []*pb.Attribute{}
	}
	_t1471 := &pb.Def{Name: relation_id766, Body: abstraction767, Attrs: _t1470}
	result770 := _t1471
	p.recordSpan(int(span_start769), "Def")
	return result770
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start774 := int64(p.spanStart())
	var _t1472 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1472 = 0
	} else {
		var _t1473 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1473 = 1
		} else {
			_t1473 = -1
		}
		_t1472 = _t1473
	}
	prediction771 := _t1472
	var _t1474 *pb.RelationId
	if prediction771 == 1 {
		uint128773 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128773
		_t1474 = &pb.RelationId{IdLow: uint128773.Low, IdHigh: uint128773.High}
	} else {
		var _t1475 *pb.RelationId
		if prediction771 == 0 {
			p.consumeLiteral(":")
			symbol772 := p.consumeTerminal("SYMBOL").Value.str
			_t1475 = p.relationIdFromString(symbol772)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1474 = _t1475
	}
	result775 := _t1474
	p.recordSpan(int(span_start774), "RelationId")
	return result775
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start778 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1476 := p.parse_bindings()
	bindings776 := _t1476
	_t1477 := p.parse_formula()
	formula777 := _t1477
	p.consumeLiteral(")")
	_t1478 := &pb.Abstraction{Vars: listConcat(bindings776[0].([]*pb.Binding), bindings776[1].([]*pb.Binding)), Value: formula777}
	result779 := _t1478
	p.recordSpan(int(span_start778), "Abstraction")
	return result779
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs780 := []*pb.Binding{}
	cond781 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond781 {
		_t1479 := p.parse_binding()
		item782 := _t1479
		xs780 = append(xs780, item782)
		cond781 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings783 := xs780
	var _t1480 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1481 := p.parse_value_bindings()
		_t1480 = _t1481
	}
	value_bindings784 := _t1480
	p.consumeLiteral("]")
	_t1482 := value_bindings784
	if value_bindings784 == nil {
		_t1482 = []*pb.Binding{}
	}
	return []interface{}{bindings783, _t1482}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start787 := int64(p.spanStart())
	symbol785 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1483 := p.parse_type()
	type786 := _t1483
	_t1484 := &pb.Var{Name: symbol785}
	_t1485 := &pb.Binding{Var: _t1484, Type: type786}
	result788 := _t1485
	p.recordSpan(int(span_start787), "Binding")
	return result788
}

func (p *Parser) parse_type() *pb.Type {
	span_start804 := int64(p.spanStart())
	var _t1486 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1486 = 0
	} else {
		var _t1487 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1487 = 13
		} else {
			var _t1488 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1488 = 4
			} else {
				var _t1489 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1489 = 1
				} else {
					var _t1490 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1490 = 8
					} else {
						var _t1491 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1491 = 11
						} else {
							var _t1492 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1492 = 5
							} else {
								var _t1493 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1493 = 2
								} else {
									var _t1494 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1494 = 12
									} else {
										var _t1495 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1495 = 3
										} else {
											var _t1496 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1496 = 7
											} else {
												var _t1497 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1497 = 6
												} else {
													var _t1498 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1498 = 10
													} else {
														var _t1499 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1499 = 9
														} else {
															_t1499 = -1
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
			_t1487 = _t1488
		}
		_t1486 = _t1487
	}
	prediction789 := _t1486
	var _t1500 *pb.Type
	if prediction789 == 13 {
		_t1501 := p.parse_uint32_type()
		uint32_type803 := _t1501
		_t1502 := &pb.Type{}
		_t1502.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type803}
		_t1500 = _t1502
	} else {
		var _t1503 *pb.Type
		if prediction789 == 12 {
			_t1504 := p.parse_float32_type()
			float32_type802 := _t1504
			_t1505 := &pb.Type{}
			_t1505.Type = &pb.Type_Float32Type{Float32Type: float32_type802}
			_t1503 = _t1505
		} else {
			var _t1506 *pb.Type
			if prediction789 == 11 {
				_t1507 := p.parse_int32_type()
				int32_type801 := _t1507
				_t1508 := &pb.Type{}
				_t1508.Type = &pb.Type_Int32Type{Int32Type: int32_type801}
				_t1506 = _t1508
			} else {
				var _t1509 *pb.Type
				if prediction789 == 10 {
					_t1510 := p.parse_boolean_type()
					boolean_type800 := _t1510
					_t1511 := &pb.Type{}
					_t1511.Type = &pb.Type_BooleanType{BooleanType: boolean_type800}
					_t1509 = _t1511
				} else {
					var _t1512 *pb.Type
					if prediction789 == 9 {
						_t1513 := p.parse_decimal_type()
						decimal_type799 := _t1513
						_t1514 := &pb.Type{}
						_t1514.Type = &pb.Type_DecimalType{DecimalType: decimal_type799}
						_t1512 = _t1514
					} else {
						var _t1515 *pb.Type
						if prediction789 == 8 {
							_t1516 := p.parse_missing_type()
							missing_type798 := _t1516
							_t1517 := &pb.Type{}
							_t1517.Type = &pb.Type_MissingType{MissingType: missing_type798}
							_t1515 = _t1517
						} else {
							var _t1518 *pb.Type
							if prediction789 == 7 {
								_t1519 := p.parse_datetime_type()
								datetime_type797 := _t1519
								_t1520 := &pb.Type{}
								_t1520.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type797}
								_t1518 = _t1520
							} else {
								var _t1521 *pb.Type
								if prediction789 == 6 {
									_t1522 := p.parse_date_type()
									date_type796 := _t1522
									_t1523 := &pb.Type{}
									_t1523.Type = &pb.Type_DateType{DateType: date_type796}
									_t1521 = _t1523
								} else {
									var _t1524 *pb.Type
									if prediction789 == 5 {
										_t1525 := p.parse_int128_type()
										int128_type795 := _t1525
										_t1526 := &pb.Type{}
										_t1526.Type = &pb.Type_Int128Type{Int128Type: int128_type795}
										_t1524 = _t1526
									} else {
										var _t1527 *pb.Type
										if prediction789 == 4 {
											_t1528 := p.parse_uint128_type()
											uint128_type794 := _t1528
											_t1529 := &pb.Type{}
											_t1529.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type794}
											_t1527 = _t1529
										} else {
											var _t1530 *pb.Type
											if prediction789 == 3 {
												_t1531 := p.parse_float_type()
												float_type793 := _t1531
												_t1532 := &pb.Type{}
												_t1532.Type = &pb.Type_FloatType{FloatType: float_type793}
												_t1530 = _t1532
											} else {
												var _t1533 *pb.Type
												if prediction789 == 2 {
													_t1534 := p.parse_int_type()
													int_type792 := _t1534
													_t1535 := &pb.Type{}
													_t1535.Type = &pb.Type_IntType{IntType: int_type792}
													_t1533 = _t1535
												} else {
													var _t1536 *pb.Type
													if prediction789 == 1 {
														_t1537 := p.parse_string_type()
														string_type791 := _t1537
														_t1538 := &pb.Type{}
														_t1538.Type = &pb.Type_StringType{StringType: string_type791}
														_t1536 = _t1538
													} else {
														var _t1539 *pb.Type
														if prediction789 == 0 {
															_t1540 := p.parse_unspecified_type()
															unspecified_type790 := _t1540
															_t1541 := &pb.Type{}
															_t1541.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type790}
															_t1539 = _t1541
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1536 = _t1539
													}
													_t1533 = _t1536
												}
												_t1530 = _t1533
											}
											_t1527 = _t1530
										}
										_t1524 = _t1527
									}
									_t1521 = _t1524
								}
								_t1518 = _t1521
							}
							_t1515 = _t1518
						}
						_t1512 = _t1515
					}
					_t1509 = _t1512
				}
				_t1506 = _t1509
			}
			_t1503 = _t1506
		}
		_t1500 = _t1503
	}
	result805 := _t1500
	p.recordSpan(int(span_start804), "Type")
	return result805
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1542 := &pb.UnspecifiedType{}
	result807 := _t1542
	p.recordSpan(int(span_start806), "UnspecifiedType")
	return result807
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1543 := &pb.StringType{}
	result809 := _t1543
	p.recordSpan(int(span_start808), "StringType")
	return result809
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1544 := &pb.IntType{}
	result811 := _t1544
	p.recordSpan(int(span_start810), "IntType")
	return result811
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1545 := &pb.FloatType{}
	result813 := _t1545
	p.recordSpan(int(span_start812), "FloatType")
	return result813
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1546 := &pb.UInt128Type{}
	result815 := _t1546
	p.recordSpan(int(span_start814), "UInt128Type")
	return result815
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1547 := &pb.Int128Type{}
	result817 := _t1547
	p.recordSpan(int(span_start816), "Int128Type")
	return result817
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1548 := &pb.DateType{}
	result819 := _t1548
	p.recordSpan(int(span_start818), "DateType")
	return result819
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1549 := &pb.DateTimeType{}
	result821 := _t1549
	p.recordSpan(int(span_start820), "DateTimeType")
	return result821
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1550 := &pb.MissingType{}
	result823 := _t1550
	p.recordSpan(int(span_start822), "MissingType")
	return result823
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start826 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int824 := p.consumeTerminal("INT").Value.i64
	int_3825 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1551 := &pb.DecimalType{Precision: int32(int824), Scale: int32(int_3825)}
	result827 := _t1551
	p.recordSpan(int(span_start826), "DecimalType")
	return result827
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1552 := &pb.BooleanType{}
	result829 := _t1552
	p.recordSpan(int(span_start828), "BooleanType")
	return result829
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start830 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1553 := &pb.Int32Type{}
	result831 := _t1553
	p.recordSpan(int(span_start830), "Int32Type")
	return result831
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start832 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1554 := &pb.Float32Type{}
	result833 := _t1554
	p.recordSpan(int(span_start832), "Float32Type")
	return result833
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start834 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1555 := &pb.UInt32Type{}
	result835 := _t1555
	p.recordSpan(int(span_start834), "UInt32Type")
	return result835
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs836 := []*pb.Binding{}
	cond837 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond837 {
		_t1556 := p.parse_binding()
		item838 := _t1556
		xs836 = append(xs836, item838)
		cond837 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings839 := xs836
	return bindings839
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start854 := int64(p.spanStart())
	var _t1557 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1558 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1558 = 0
		} else {
			var _t1559 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1559 = 11
			} else {
				var _t1560 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1560 = 3
				} else {
					var _t1561 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1561 = 10
					} else {
						var _t1562 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1562 = 9
						} else {
							var _t1563 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1563 = 5
							} else {
								var _t1564 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1564 = 6
								} else {
									var _t1565 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1565 = 7
									} else {
										var _t1566 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1566 = 1
										} else {
											var _t1567 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1567 = 2
											} else {
												var _t1568 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1568 = 12
												} else {
													var _t1569 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1569 = 8
													} else {
														var _t1570 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1570 = 4
														} else {
															var _t1571 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1571 = 10
															} else {
																var _t1572 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1572 = 10
																} else {
																	var _t1573 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1573 = 10
																	} else {
																		var _t1574 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1574 = 10
																		} else {
																			var _t1575 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1575 = 10
																			} else {
																				var _t1576 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1576 = 10
																				} else {
																					var _t1577 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1577 = 10
																					} else {
																						var _t1578 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1578 = 10
																						} else {
																							var _t1579 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1579 = 10
																							} else {
																								_t1579 = -1
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
			}
			_t1558 = _t1559
		}
		_t1557 = _t1558
	} else {
		_t1557 = -1
	}
	prediction840 := _t1557
	var _t1580 *pb.Formula
	if prediction840 == 12 {
		_t1581 := p.parse_cast()
		cast853 := _t1581
		_t1582 := &pb.Formula{}
		_t1582.FormulaType = &pb.Formula_Cast{Cast: cast853}
		_t1580 = _t1582
	} else {
		var _t1583 *pb.Formula
		if prediction840 == 11 {
			_t1584 := p.parse_rel_atom()
			rel_atom852 := _t1584
			_t1585 := &pb.Formula{}
			_t1585.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom852}
			_t1583 = _t1585
		} else {
			var _t1586 *pb.Formula
			if prediction840 == 10 {
				_t1587 := p.parse_primitive()
				primitive851 := _t1587
				_t1588 := &pb.Formula{}
				_t1588.FormulaType = &pb.Formula_Primitive{Primitive: primitive851}
				_t1586 = _t1588
			} else {
				var _t1589 *pb.Formula
				if prediction840 == 9 {
					_t1590 := p.parse_pragma()
					pragma850 := _t1590
					_t1591 := &pb.Formula{}
					_t1591.FormulaType = &pb.Formula_Pragma{Pragma: pragma850}
					_t1589 = _t1591
				} else {
					var _t1592 *pb.Formula
					if prediction840 == 8 {
						_t1593 := p.parse_atom()
						atom849 := _t1593
						_t1594 := &pb.Formula{}
						_t1594.FormulaType = &pb.Formula_Atom{Atom: atom849}
						_t1592 = _t1594
					} else {
						var _t1595 *pb.Formula
						if prediction840 == 7 {
							_t1596 := p.parse_ffi()
							ffi848 := _t1596
							_t1597 := &pb.Formula{}
							_t1597.FormulaType = &pb.Formula_Ffi{Ffi: ffi848}
							_t1595 = _t1597
						} else {
							var _t1598 *pb.Formula
							if prediction840 == 6 {
								_t1599 := p.parse_not()
								not847 := _t1599
								_t1600 := &pb.Formula{}
								_t1600.FormulaType = &pb.Formula_Not{Not: not847}
								_t1598 = _t1600
							} else {
								var _t1601 *pb.Formula
								if prediction840 == 5 {
									_t1602 := p.parse_disjunction()
									disjunction846 := _t1602
									_t1603 := &pb.Formula{}
									_t1603.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction846}
									_t1601 = _t1603
								} else {
									var _t1604 *pb.Formula
									if prediction840 == 4 {
										_t1605 := p.parse_conjunction()
										conjunction845 := _t1605
										_t1606 := &pb.Formula{}
										_t1606.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction845}
										_t1604 = _t1606
									} else {
										var _t1607 *pb.Formula
										if prediction840 == 3 {
											_t1608 := p.parse_reduce()
											reduce844 := _t1608
											_t1609 := &pb.Formula{}
											_t1609.FormulaType = &pb.Formula_Reduce{Reduce: reduce844}
											_t1607 = _t1609
										} else {
											var _t1610 *pb.Formula
											if prediction840 == 2 {
												_t1611 := p.parse_exists()
												exists843 := _t1611
												_t1612 := &pb.Formula{}
												_t1612.FormulaType = &pb.Formula_Exists{Exists: exists843}
												_t1610 = _t1612
											} else {
												var _t1613 *pb.Formula
												if prediction840 == 1 {
													_t1614 := p.parse_false()
													false842 := _t1614
													_t1615 := &pb.Formula{}
													_t1615.FormulaType = &pb.Formula_Disjunction{Disjunction: false842}
													_t1613 = _t1615
												} else {
													var _t1616 *pb.Formula
													if prediction840 == 0 {
														_t1617 := p.parse_true()
														true841 := _t1617
														_t1618 := &pb.Formula{}
														_t1618.FormulaType = &pb.Formula_Conjunction{Conjunction: true841}
														_t1616 = _t1618
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1583 = _t1586
		}
		_t1580 = _t1583
	}
	result855 := _t1580
	p.recordSpan(int(span_start854), "Formula")
	return result855
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start856 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1619 := &pb.Conjunction{Args: []*pb.Formula{}}
	result857 := _t1619
	p.recordSpan(int(span_start856), "Conjunction")
	return result857
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1620 := &pb.Disjunction{Args: []*pb.Formula{}}
	result859 := _t1620
	p.recordSpan(int(span_start858), "Disjunction")
	return result859
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start862 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1621 := p.parse_bindings()
	bindings860 := _t1621
	_t1622 := p.parse_formula()
	formula861 := _t1622
	p.consumeLiteral(")")
	_t1623 := &pb.Abstraction{Vars: listConcat(bindings860[0].([]*pb.Binding), bindings860[1].([]*pb.Binding)), Value: formula861}
	_t1624 := &pb.Exists{Body: _t1623}
	result863 := _t1624
	p.recordSpan(int(span_start862), "Exists")
	return result863
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start867 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1625 := p.parse_abstraction()
	abstraction864 := _t1625
	_t1626 := p.parse_abstraction()
	abstraction_3865 := _t1626
	_t1627 := p.parse_terms()
	terms866 := _t1627
	p.consumeLiteral(")")
	_t1628 := &pb.Reduce{Op: abstraction864, Body: abstraction_3865, Terms: terms866}
	result868 := _t1628
	p.recordSpan(int(span_start867), "Reduce")
	return result868
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs869 := []*pb.Term{}
	cond870 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond870 {
		_t1629 := p.parse_term()
		item871 := _t1629
		xs869 = append(xs869, item871)
		cond870 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms872 := xs869
	p.consumeLiteral(")")
	return terms872
}

func (p *Parser) parse_term() *pb.Term {
	span_start876 := int64(p.spanStart())
	var _t1630 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1630 = 1
	} else {
		var _t1631 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1631 = 1
		} else {
			var _t1632 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1632 = 1
			} else {
				var _t1633 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1633 = 1
				} else {
					var _t1634 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1634 = 0
					} else {
						var _t1635 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1635 = 1
						} else {
							var _t1636 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1636 = 1
							} else {
								var _t1637 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1637 = 1
								} else {
									var _t1638 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1638 = 1
									} else {
										var _t1639 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1639 = 1
										} else {
											var _t1640 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1640 = 1
											} else {
												var _t1641 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1641 = 1
												} else {
													var _t1642 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1642 = 1
													} else {
														var _t1643 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1643 = 1
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
	prediction873 := _t1630
	var _t1644 *pb.Term
	if prediction873 == 1 {
		_t1645 := p.parse_value()
		value875 := _t1645
		_t1646 := &pb.Term{}
		_t1646.TermType = &pb.Term_Constant{Constant: value875}
		_t1644 = _t1646
	} else {
		var _t1647 *pb.Term
		if prediction873 == 0 {
			_t1648 := p.parse_var()
			var874 := _t1648
			_t1649 := &pb.Term{}
			_t1649.TermType = &pb.Term_Var{Var: var874}
			_t1647 = _t1649
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1644 = _t1647
	}
	result877 := _t1644
	p.recordSpan(int(span_start876), "Term")
	return result877
}

func (p *Parser) parse_var() *pb.Var {
	span_start879 := int64(p.spanStart())
	symbol878 := p.consumeTerminal("SYMBOL").Value.str
	_t1650 := &pb.Var{Name: symbol878}
	result880 := _t1650
	p.recordSpan(int(span_start879), "Var")
	return result880
}

func (p *Parser) parse_value() *pb.Value {
	span_start894 := int64(p.spanStart())
	var _t1651 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1651 = 12
	} else {
		var _t1652 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1652 = 11
		} else {
			var _t1653 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1653 = 12
			} else {
				var _t1654 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1655 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1655 = 1
					} else {
						var _t1656 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1656 = 0
						} else {
							_t1656 = -1
						}
						_t1655 = _t1656
					}
					_t1654 = _t1655
				} else {
					var _t1657 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1657 = 7
					} else {
						var _t1658 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1658 = 8
						} else {
							var _t1659 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1659 = 2
							} else {
								var _t1660 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1660 = 3
								} else {
									var _t1661 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1661 = 9
									} else {
										var _t1662 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1662 = 4
										} else {
											var _t1663 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1663 = 5
											} else {
												var _t1664 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1664 = 6
												} else {
													var _t1665 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1665 = 10
													} else {
														_t1665 = -1
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
					_t1654 = _t1657
				}
				_t1653 = _t1654
			}
			_t1652 = _t1653
		}
		_t1651 = _t1652
	}
	prediction881 := _t1651
	var _t1666 *pb.Value
	if prediction881 == 12 {
		_t1667 := p.parse_boolean_value()
		boolean_value893 := _t1667
		_t1668 := &pb.Value{}
		_t1668.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value893}
		_t1666 = _t1668
	} else {
		var _t1669 *pb.Value
		if prediction881 == 11 {
			p.consumeLiteral("missing")
			_t1670 := &pb.MissingValue{}
			_t1671 := &pb.Value{}
			_t1671.Value = &pb.Value_MissingValue{MissingValue: _t1670}
			_t1669 = _t1671
		} else {
			var _t1672 *pb.Value
			if prediction881 == 10 {
				formatted_decimal892 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1673 := &pb.Value{}
				_t1673.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal892}
				_t1672 = _t1673
			} else {
				var _t1674 *pb.Value
				if prediction881 == 9 {
					formatted_int128891 := p.consumeTerminal("INT128").Value.int128
					_t1675 := &pb.Value{}
					_t1675.Value = &pb.Value_Int128Value{Int128Value: formatted_int128891}
					_t1674 = _t1675
				} else {
					var _t1676 *pb.Value
					if prediction881 == 8 {
						formatted_uint128890 := p.consumeTerminal("UINT128").Value.uint128
						_t1677 := &pb.Value{}
						_t1677.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128890}
						_t1676 = _t1677
					} else {
						var _t1678 *pb.Value
						if prediction881 == 7 {
							formatted_uint32889 := p.consumeTerminal("UINT32").Value.u32
							_t1679 := &pb.Value{}
							_t1679.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32889}
							_t1678 = _t1679
						} else {
							var _t1680 *pb.Value
							if prediction881 == 6 {
								formatted_float888 := p.consumeTerminal("FLOAT").Value.f64
								_t1681 := &pb.Value{}
								_t1681.Value = &pb.Value_FloatValue{FloatValue: formatted_float888}
								_t1680 = _t1681
							} else {
								var _t1682 *pb.Value
								if prediction881 == 5 {
									formatted_float32887 := p.consumeTerminal("FLOAT32").Value.f32
									_t1683 := &pb.Value{}
									_t1683.Value = &pb.Value_Float32Value{Float32Value: formatted_float32887}
									_t1682 = _t1683
								} else {
									var _t1684 *pb.Value
									if prediction881 == 4 {
										formatted_int886 := p.consumeTerminal("INT").Value.i64
										_t1685 := &pb.Value{}
										_t1685.Value = &pb.Value_IntValue{IntValue: formatted_int886}
										_t1684 = _t1685
									} else {
										var _t1686 *pb.Value
										if prediction881 == 3 {
											formatted_int32885 := p.consumeTerminal("INT32").Value.i32
											_t1687 := &pb.Value{}
											_t1687.Value = &pb.Value_Int32Value{Int32Value: formatted_int32885}
											_t1686 = _t1687
										} else {
											var _t1688 *pb.Value
											if prediction881 == 2 {
												formatted_string884 := p.consumeTerminal("STRING").Value.str
												_t1689 := &pb.Value{}
												_t1689.Value = &pb.Value_StringValue{StringValue: formatted_string884}
												_t1688 = _t1689
											} else {
												var _t1690 *pb.Value
												if prediction881 == 1 {
													_t1691 := p.parse_datetime()
													datetime883 := _t1691
													_t1692 := &pb.Value{}
													_t1692.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime883}
													_t1690 = _t1692
												} else {
													var _t1693 *pb.Value
													if prediction881 == 0 {
														_t1694 := p.parse_date()
														date882 := _t1694
														_t1695 := &pb.Value{}
														_t1695.Value = &pb.Value_DateValue{DateValue: date882}
														_t1693 = _t1695
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1690 = _t1693
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
				_t1672 = _t1674
			}
			_t1669 = _t1672
		}
		_t1666 = _t1669
	}
	result895 := _t1666
	p.recordSpan(int(span_start894), "Value")
	return result895
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int896 := p.consumeTerminal("INT").Value.i64
	formatted_int_3897 := p.consumeTerminal("INT").Value.i64
	formatted_int_4898 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1696 := &pb.DateValue{Year: int32(formatted_int896), Month: int32(formatted_int_3897), Day: int32(formatted_int_4898)}
	result900 := _t1696
	p.recordSpan(int(span_start899), "DateValue")
	return result900
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start908 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int901 := p.consumeTerminal("INT").Value.i64
	formatted_int_3902 := p.consumeTerminal("INT").Value.i64
	formatted_int_4903 := p.consumeTerminal("INT").Value.i64
	formatted_int_5904 := p.consumeTerminal("INT").Value.i64
	formatted_int_6905 := p.consumeTerminal("INT").Value.i64
	formatted_int_7906 := p.consumeTerminal("INT").Value.i64
	var _t1697 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1697 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8907 := _t1697
	p.consumeLiteral(")")
	_t1698 := &pb.DateTimeValue{Year: int32(formatted_int901), Month: int32(formatted_int_3902), Day: int32(formatted_int_4903), Hour: int32(formatted_int_5904), Minute: int32(formatted_int_6905), Second: int32(formatted_int_7906), Microsecond: int32(deref(formatted_int_8907, 0))}
	result909 := _t1698
	p.recordSpan(int(span_start908), "DateTimeValue")
	return result909
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start914 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs910 := []*pb.Formula{}
	cond911 := p.matchLookaheadLiteral("(", 0)
	for cond911 {
		_t1699 := p.parse_formula()
		item912 := _t1699
		xs910 = append(xs910, item912)
		cond911 = p.matchLookaheadLiteral("(", 0)
	}
	formulas913 := xs910
	p.consumeLiteral(")")
	_t1700 := &pb.Conjunction{Args: formulas913}
	result915 := _t1700
	p.recordSpan(int(span_start914), "Conjunction")
	return result915
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs916 := []*pb.Formula{}
	cond917 := p.matchLookaheadLiteral("(", 0)
	for cond917 {
		_t1701 := p.parse_formula()
		item918 := _t1701
		xs916 = append(xs916, item918)
		cond917 = p.matchLookaheadLiteral("(", 0)
	}
	formulas919 := xs916
	p.consumeLiteral(")")
	_t1702 := &pb.Disjunction{Args: formulas919}
	result921 := _t1702
	p.recordSpan(int(span_start920), "Disjunction")
	return result921
}

func (p *Parser) parse_not() *pb.Not {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1703 := p.parse_formula()
	formula922 := _t1703
	p.consumeLiteral(")")
	_t1704 := &pb.Not{Arg: formula922}
	result924 := _t1704
	p.recordSpan(int(span_start923), "Not")
	return result924
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start928 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1705 := p.parse_name()
	name925 := _t1705
	_t1706 := p.parse_ffi_args()
	ffi_args926 := _t1706
	_t1707 := p.parse_terms()
	terms927 := _t1707
	p.consumeLiteral(")")
	_t1708 := &pb.FFI{Name: name925, Args: ffi_args926, Terms: terms927}
	result929 := _t1708
	p.recordSpan(int(span_start928), "FFI")
	return result929
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol930 := p.consumeTerminal("SYMBOL").Value.str
	return symbol930
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs931 := []*pb.Abstraction{}
	cond932 := p.matchLookaheadLiteral("(", 0)
	for cond932 {
		_t1709 := p.parse_abstraction()
		item933 := _t1709
		xs931 = append(xs931, item933)
		cond932 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions934 := xs931
	p.consumeLiteral(")")
	return abstractions934
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start940 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1710 := p.parse_relation_id()
	relation_id935 := _t1710
	xs936 := []*pb.Term{}
	cond937 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond937 {
		_t1711 := p.parse_term()
		item938 := _t1711
		xs936 = append(xs936, item938)
		cond937 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms939 := xs936
	p.consumeLiteral(")")
	_t1712 := &pb.Atom{Name: relation_id935, Terms: terms939}
	result941 := _t1712
	p.recordSpan(int(span_start940), "Atom")
	return result941
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start947 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1713 := p.parse_name()
	name942 := _t1713
	xs943 := []*pb.Term{}
	cond944 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond944 {
		_t1714 := p.parse_term()
		item945 := _t1714
		xs943 = append(xs943, item945)
		cond944 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms946 := xs943
	p.consumeLiteral(")")
	_t1715 := &pb.Pragma{Name: name942, Terms: terms946}
	result948 := _t1715
	p.recordSpan(int(span_start947), "Pragma")
	return result948
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start964 := int64(p.spanStart())
	var _t1716 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1717 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1717 = 9
		} else {
			var _t1718 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1718 = 4
			} else {
				var _t1719 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1719 = 3
				} else {
					var _t1720 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1720 = 0
					} else {
						var _t1721 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1721 = 2
						} else {
							var _t1722 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1722 = 1
							} else {
								var _t1723 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1723 = 8
								} else {
									var _t1724 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1724 = 6
									} else {
										var _t1725 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1725 = 5
										} else {
											var _t1726 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1726 = 7
											} else {
												_t1726 = -1
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
			_t1717 = _t1718
		}
		_t1716 = _t1717
	} else {
		_t1716 = -1
	}
	prediction949 := _t1716
	var _t1727 *pb.Primitive
	if prediction949 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1728 := p.parse_name()
		name959 := _t1728
		xs960 := []*pb.RelTerm{}
		cond961 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond961 {
			_t1729 := p.parse_rel_term()
			item962 := _t1729
			xs960 = append(xs960, item962)
			cond961 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms963 := xs960
		p.consumeLiteral(")")
		_t1730 := &pb.Primitive{Name: name959, Terms: rel_terms963}
		_t1727 = _t1730
	} else {
		var _t1731 *pb.Primitive
		if prediction949 == 8 {
			_t1732 := p.parse_divide()
			divide958 := _t1732
			_t1731 = divide958
		} else {
			var _t1733 *pb.Primitive
			if prediction949 == 7 {
				_t1734 := p.parse_multiply()
				multiply957 := _t1734
				_t1733 = multiply957
			} else {
				var _t1735 *pb.Primitive
				if prediction949 == 6 {
					_t1736 := p.parse_minus()
					minus956 := _t1736
					_t1735 = minus956
				} else {
					var _t1737 *pb.Primitive
					if prediction949 == 5 {
						_t1738 := p.parse_add()
						add955 := _t1738
						_t1737 = add955
					} else {
						var _t1739 *pb.Primitive
						if prediction949 == 4 {
							_t1740 := p.parse_gt_eq()
							gt_eq954 := _t1740
							_t1739 = gt_eq954
						} else {
							var _t1741 *pb.Primitive
							if prediction949 == 3 {
								_t1742 := p.parse_gt()
								gt953 := _t1742
								_t1741 = gt953
							} else {
								var _t1743 *pb.Primitive
								if prediction949 == 2 {
									_t1744 := p.parse_lt_eq()
									lt_eq952 := _t1744
									_t1743 = lt_eq952
								} else {
									var _t1745 *pb.Primitive
									if prediction949 == 1 {
										_t1746 := p.parse_lt()
										lt951 := _t1746
										_t1745 = lt951
									} else {
										var _t1747 *pb.Primitive
										if prediction949 == 0 {
											_t1748 := p.parse_eq()
											eq950 := _t1748
											_t1747 = eq950
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1731 = _t1733
		}
		_t1727 = _t1731
	}
	result965 := _t1727
	p.recordSpan(int(span_start964), "Primitive")
	return result965
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1749 := p.parse_term()
	term966 := _t1749
	_t1750 := p.parse_term()
	term_3967 := _t1750
	p.consumeLiteral(")")
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term966}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_3967}
	_t1753 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1751, _t1752}}
	result969 := _t1753
	p.recordSpan(int(span_start968), "Primitive")
	return result969
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1754 := p.parse_term()
	term970 := _t1754
	_t1755 := p.parse_term()
	term_3971 := _t1755
	p.consumeLiteral(")")
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term970}
	_t1757 := &pb.RelTerm{}
	_t1757.RelTermType = &pb.RelTerm_Term{Term: term_3971}
	_t1758 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1756, _t1757}}
	result973 := _t1758
	p.recordSpan(int(span_start972), "Primitive")
	return result973
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1759 := p.parse_term()
	term974 := _t1759
	_t1760 := p.parse_term()
	term_3975 := _t1760
	p.consumeLiteral(")")
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term974}
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term_3975}
	_t1763 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1761, _t1762}}
	result977 := _t1763
	p.recordSpan(int(span_start976), "Primitive")
	return result977
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1764 := p.parse_term()
	term978 := _t1764
	_t1765 := p.parse_term()
	term_3979 := _t1765
	p.consumeLiteral(")")
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term978}
	_t1767 := &pb.RelTerm{}
	_t1767.RelTermType = &pb.RelTerm_Term{Term: term_3979}
	_t1768 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1766, _t1767}}
	result981 := _t1768
	p.recordSpan(int(span_start980), "Primitive")
	return result981
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1769 := p.parse_term()
	term982 := _t1769
	_t1770 := p.parse_term()
	term_3983 := _t1770
	p.consumeLiteral(")")
	_t1771 := &pb.RelTerm{}
	_t1771.RelTermType = &pb.RelTerm_Term{Term: term982}
	_t1772 := &pb.RelTerm{}
	_t1772.RelTermType = &pb.RelTerm_Term{Term: term_3983}
	_t1773 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1771, _t1772}}
	result985 := _t1773
	p.recordSpan(int(span_start984), "Primitive")
	return result985
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start989 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1774 := p.parse_term()
	term986 := _t1774
	_t1775 := p.parse_term()
	term_3987 := _t1775
	_t1776 := p.parse_term()
	term_4988 := _t1776
	p.consumeLiteral(")")
	_t1777 := &pb.RelTerm{}
	_t1777.RelTermType = &pb.RelTerm_Term{Term: term986}
	_t1778 := &pb.RelTerm{}
	_t1778.RelTermType = &pb.RelTerm_Term{Term: term_3987}
	_t1779 := &pb.RelTerm{}
	_t1779.RelTermType = &pb.RelTerm_Term{Term: term_4988}
	_t1780 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1777, _t1778, _t1779}}
	result990 := _t1780
	p.recordSpan(int(span_start989), "Primitive")
	return result990
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start994 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1781 := p.parse_term()
	term991 := _t1781
	_t1782 := p.parse_term()
	term_3992 := _t1782
	_t1783 := p.parse_term()
	term_4993 := _t1783
	p.consumeLiteral(")")
	_t1784 := &pb.RelTerm{}
	_t1784.RelTermType = &pb.RelTerm_Term{Term: term991}
	_t1785 := &pb.RelTerm{}
	_t1785.RelTermType = &pb.RelTerm_Term{Term: term_3992}
	_t1786 := &pb.RelTerm{}
	_t1786.RelTermType = &pb.RelTerm_Term{Term: term_4993}
	_t1787 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1784, _t1785, _t1786}}
	result995 := _t1787
	p.recordSpan(int(span_start994), "Primitive")
	return result995
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start999 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1788 := p.parse_term()
	term996 := _t1788
	_t1789 := p.parse_term()
	term_3997 := _t1789
	_t1790 := p.parse_term()
	term_4998 := _t1790
	p.consumeLiteral(")")
	_t1791 := &pb.RelTerm{}
	_t1791.RelTermType = &pb.RelTerm_Term{Term: term996}
	_t1792 := &pb.RelTerm{}
	_t1792.RelTermType = &pb.RelTerm_Term{Term: term_3997}
	_t1793 := &pb.RelTerm{}
	_t1793.RelTermType = &pb.RelTerm_Term{Term: term_4998}
	_t1794 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1791, _t1792, _t1793}}
	result1000 := _t1794
	p.recordSpan(int(span_start999), "Primitive")
	return result1000
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1795 := p.parse_term()
	term1001 := _t1795
	_t1796 := p.parse_term()
	term_31002 := _t1796
	_t1797 := p.parse_term()
	term_41003 := _t1797
	p.consumeLiteral(")")
	_t1798 := &pb.RelTerm{}
	_t1798.RelTermType = &pb.RelTerm_Term{Term: term1001}
	_t1799 := &pb.RelTerm{}
	_t1799.RelTermType = &pb.RelTerm_Term{Term: term_31002}
	_t1800 := &pb.RelTerm{}
	_t1800.RelTermType = &pb.RelTerm_Term{Term: term_41003}
	_t1801 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1798, _t1799, _t1800}}
	result1005 := _t1801
	p.recordSpan(int(span_start1004), "Primitive")
	return result1005
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1009 := int64(p.spanStart())
	var _t1802 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1802 = 1
	} else {
		var _t1803 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1803 = 1
		} else {
			var _t1804 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1804 = 1
			} else {
				var _t1805 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1805 = 1
				} else {
					var _t1806 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1806 = 0
					} else {
						var _t1807 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1807 = 1
						} else {
							var _t1808 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1808 = 1
							} else {
								var _t1809 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1809 = 1
								} else {
									var _t1810 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1810 = 1
									} else {
										var _t1811 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1811 = 1
										} else {
											var _t1812 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1812 = 1
											} else {
												var _t1813 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1813 = 1
												} else {
													var _t1814 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1814 = 1
													} else {
														var _t1815 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1815 = 1
														} else {
															var _t1816 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1816 = 1
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
					}
					_t1805 = _t1806
				}
				_t1804 = _t1805
			}
			_t1803 = _t1804
		}
		_t1802 = _t1803
	}
	prediction1006 := _t1802
	var _t1817 *pb.RelTerm
	if prediction1006 == 1 {
		_t1818 := p.parse_term()
		term1008 := _t1818
		_t1819 := &pb.RelTerm{}
		_t1819.RelTermType = &pb.RelTerm_Term{Term: term1008}
		_t1817 = _t1819
	} else {
		var _t1820 *pb.RelTerm
		if prediction1006 == 0 {
			_t1821 := p.parse_specialized_value()
			specialized_value1007 := _t1821
			_t1822 := &pb.RelTerm{}
			_t1822.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1007}
			_t1820 = _t1822
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1817 = _t1820
	}
	result1010 := _t1817
	p.recordSpan(int(span_start1009), "RelTerm")
	return result1010
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1012 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1823 := p.parse_raw_value()
	raw_value1011 := _t1823
	result1013 := raw_value1011
	p.recordSpan(int(span_start1012), "Value")
	return result1013
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1019 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1824 := p.parse_name()
	name1014 := _t1824
	xs1015 := []*pb.RelTerm{}
	cond1016 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1016 {
		_t1825 := p.parse_rel_term()
		item1017 := _t1825
		xs1015 = append(xs1015, item1017)
		cond1016 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1018 := xs1015
	p.consumeLiteral(")")
	_t1826 := &pb.RelAtom{Name: name1014, Terms: rel_terms1018}
	result1020 := _t1826
	p.recordSpan(int(span_start1019), "RelAtom")
	return result1020
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1023 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1827 := p.parse_term()
	term1021 := _t1827
	_t1828 := p.parse_term()
	term_31022 := _t1828
	p.consumeLiteral(")")
	_t1829 := &pb.Cast{Input: term1021, Result: term_31022}
	result1024 := _t1829
	p.recordSpan(int(span_start1023), "Cast")
	return result1024
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1025 := []*pb.Attribute{}
	cond1026 := p.matchLookaheadLiteral("(", 0)
	for cond1026 {
		_t1830 := p.parse_attribute()
		item1027 := _t1830
		xs1025 = append(xs1025, item1027)
		cond1026 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1028 := xs1025
	p.consumeLiteral(")")
	return attributes1028
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1831 := p.parse_name()
	name1029 := _t1831
	xs1030 := []*pb.Value{}
	cond1031 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1031 {
		_t1832 := p.parse_raw_value()
		item1032 := _t1832
		xs1030 = append(xs1030, item1032)
		cond1031 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1033 := xs1030
	p.consumeLiteral(")")
	_t1833 := &pb.Attribute{Name: name1029, Args: raw_values1033}
	result1035 := _t1833
	p.recordSpan(int(span_start1034), "Attribute")
	return result1035
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1042 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1036 := []*pb.RelationId{}
	cond1037 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1037 {
		_t1834 := p.parse_relation_id()
		item1038 := _t1834
		xs1036 = append(xs1036, item1038)
		cond1037 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1039 := xs1036
	_t1835 := p.parse_script()
	script1040 := _t1835
	var _t1836 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1837 := p.parse_attrs()
		_t1836 = _t1837
	}
	attrs1041 := _t1836
	p.consumeLiteral(")")
	_t1838 := attrs1041
	if attrs1041 == nil {
		_t1838 = []*pb.Attribute{}
	}
	_t1839 := &pb.Algorithm{Global: relation_ids1039, Body: script1040, Attrs: _t1838}
	result1043 := _t1839
	p.recordSpan(int(span_start1042), "Algorithm")
	return result1043
}

func (p *Parser) parse_script() *pb.Script {
	span_start1048 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1044 := []*pb.Construct{}
	cond1045 := p.matchLookaheadLiteral("(", 0)
	for cond1045 {
		_t1840 := p.parse_construct()
		item1046 := _t1840
		xs1044 = append(xs1044, item1046)
		cond1045 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1047 := xs1044
	p.consumeLiteral(")")
	_t1841 := &pb.Script{Constructs: constructs1047}
	result1049 := _t1841
	p.recordSpan(int(span_start1048), "Script")
	return result1049
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1053 := int64(p.spanStart())
	var _t1842 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1843 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1843 = 1
		} else {
			var _t1844 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1844 = 1
			} else {
				var _t1845 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1845 = 1
				} else {
					var _t1846 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1846 = 0
					} else {
						var _t1847 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1847 = 1
						} else {
							var _t1848 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1848 = 1
							} else {
								_t1848 = -1
							}
							_t1847 = _t1848
						}
						_t1846 = _t1847
					}
					_t1845 = _t1846
				}
				_t1844 = _t1845
			}
			_t1843 = _t1844
		}
		_t1842 = _t1843
	} else {
		_t1842 = -1
	}
	prediction1050 := _t1842
	var _t1849 *pb.Construct
	if prediction1050 == 1 {
		_t1850 := p.parse_instruction()
		instruction1052 := _t1850
		_t1851 := &pb.Construct{}
		_t1851.ConstructType = &pb.Construct_Instruction{Instruction: instruction1052}
		_t1849 = _t1851
	} else {
		var _t1852 *pb.Construct
		if prediction1050 == 0 {
			_t1853 := p.parse_loop()
			loop1051 := _t1853
			_t1854 := &pb.Construct{}
			_t1854.ConstructType = &pb.Construct_Loop{Loop: loop1051}
			_t1852 = _t1854
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1849 = _t1852
	}
	result1054 := _t1849
	p.recordSpan(int(span_start1053), "Construct")
	return result1054
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1058 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1855 := p.parse_init()
	init1055 := _t1855
	_t1856 := p.parse_script()
	script1056 := _t1856
	var _t1857 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1858 := p.parse_attrs()
		_t1857 = _t1858
	}
	attrs1057 := _t1857
	p.consumeLiteral(")")
	_t1859 := attrs1057
	if attrs1057 == nil {
		_t1859 = []*pb.Attribute{}
	}
	_t1860 := &pb.Loop{Init: init1055, Body: script1056, Attrs: _t1859}
	result1059 := _t1860
	p.recordSpan(int(span_start1058), "Loop")
	return result1059
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1060 := []*pb.Instruction{}
	cond1061 := p.matchLookaheadLiteral("(", 0)
	for cond1061 {
		_t1861 := p.parse_instruction()
		item1062 := _t1861
		xs1060 = append(xs1060, item1062)
		cond1061 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1063 := xs1060
	p.consumeLiteral(")")
	return instructions1063
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1070 := int64(p.spanStart())
	var _t1862 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1863 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1863 = 1
		} else {
			var _t1864 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1864 = 4
			} else {
				var _t1865 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1865 = 3
				} else {
					var _t1866 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1866 = 2
					} else {
						var _t1867 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1867 = 0
						} else {
							_t1867 = -1
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
	} else {
		_t1862 = -1
	}
	prediction1064 := _t1862
	var _t1868 *pb.Instruction
	if prediction1064 == 4 {
		_t1869 := p.parse_monus_def()
		monus_def1069 := _t1869
		_t1870 := &pb.Instruction{}
		_t1870.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1069}
		_t1868 = _t1870
	} else {
		var _t1871 *pb.Instruction
		if prediction1064 == 3 {
			_t1872 := p.parse_monoid_def()
			monoid_def1068 := _t1872
			_t1873 := &pb.Instruction{}
			_t1873.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1068}
			_t1871 = _t1873
		} else {
			var _t1874 *pb.Instruction
			if prediction1064 == 2 {
				_t1875 := p.parse_break()
				break1067 := _t1875
				_t1876 := &pb.Instruction{}
				_t1876.InstrType = &pb.Instruction_Break{Break: break1067}
				_t1874 = _t1876
			} else {
				var _t1877 *pb.Instruction
				if prediction1064 == 1 {
					_t1878 := p.parse_upsert()
					upsert1066 := _t1878
					_t1879 := &pb.Instruction{}
					_t1879.InstrType = &pb.Instruction_Upsert{Upsert: upsert1066}
					_t1877 = _t1879
				} else {
					var _t1880 *pb.Instruction
					if prediction1064 == 0 {
						_t1881 := p.parse_assign()
						assign1065 := _t1881
						_t1882 := &pb.Instruction{}
						_t1882.InstrType = &pb.Instruction_Assign{Assign: assign1065}
						_t1880 = _t1882
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1877 = _t1880
				}
				_t1874 = _t1877
			}
			_t1871 = _t1874
		}
		_t1868 = _t1871
	}
	result1071 := _t1868
	p.recordSpan(int(span_start1070), "Instruction")
	return result1071
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1075 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1883 := p.parse_relation_id()
	relation_id1072 := _t1883
	_t1884 := p.parse_abstraction()
	abstraction1073 := _t1884
	var _t1885 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1886 := p.parse_attrs()
		_t1885 = _t1886
	}
	attrs1074 := _t1885
	p.consumeLiteral(")")
	_t1887 := attrs1074
	if attrs1074 == nil {
		_t1887 = []*pb.Attribute{}
	}
	_t1888 := &pb.Assign{Name: relation_id1072, Body: abstraction1073, Attrs: _t1887}
	result1076 := _t1888
	p.recordSpan(int(span_start1075), "Assign")
	return result1076
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1889 := p.parse_relation_id()
	relation_id1077 := _t1889
	_t1890 := p.parse_abstraction_with_arity()
	abstraction_with_arity1078 := _t1890
	var _t1891 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1892 := p.parse_attrs()
		_t1891 = _t1892
	}
	attrs1079 := _t1891
	p.consumeLiteral(")")
	_t1893 := attrs1079
	if attrs1079 == nil {
		_t1893 = []*pb.Attribute{}
	}
	_t1894 := &pb.Upsert{Name: relation_id1077, Body: abstraction_with_arity1078[0].(*pb.Abstraction), Attrs: _t1893, ValueArity: abstraction_with_arity1078[1].(int64)}
	result1081 := _t1894
	p.recordSpan(int(span_start1080), "Upsert")
	return result1081
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1895 := p.parse_bindings()
	bindings1082 := _t1895
	_t1896 := p.parse_formula()
	formula1083 := _t1896
	p.consumeLiteral(")")
	_t1897 := &pb.Abstraction{Vars: listConcat(bindings1082[0].([]*pb.Binding), bindings1082[1].([]*pb.Binding)), Value: formula1083}
	return []interface{}{_t1897, int64(len(bindings1082[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1898 := p.parse_relation_id()
	relation_id1084 := _t1898
	_t1899 := p.parse_abstraction()
	abstraction1085 := _t1899
	var _t1900 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1901 := p.parse_attrs()
		_t1900 = _t1901
	}
	attrs1086 := _t1900
	p.consumeLiteral(")")
	_t1902 := attrs1086
	if attrs1086 == nil {
		_t1902 = []*pb.Attribute{}
	}
	_t1903 := &pb.Break{Name: relation_id1084, Body: abstraction1085, Attrs: _t1902}
	result1088 := _t1903
	p.recordSpan(int(span_start1087), "Break")
	return result1088
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1093 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1904 := p.parse_monoid()
	monoid1089 := _t1904
	_t1905 := p.parse_relation_id()
	relation_id1090 := _t1905
	_t1906 := p.parse_abstraction_with_arity()
	abstraction_with_arity1091 := _t1906
	var _t1907 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1908 := p.parse_attrs()
		_t1907 = _t1908
	}
	attrs1092 := _t1907
	p.consumeLiteral(")")
	_t1909 := attrs1092
	if attrs1092 == nil {
		_t1909 = []*pb.Attribute{}
	}
	_t1910 := &pb.MonoidDef{Monoid: monoid1089, Name: relation_id1090, Body: abstraction_with_arity1091[0].(*pb.Abstraction), Attrs: _t1909, ValueArity: abstraction_with_arity1091[1].(int64)}
	result1094 := _t1910
	p.recordSpan(int(span_start1093), "MonoidDef")
	return result1094
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1100 := int64(p.spanStart())
	var _t1911 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1912 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1912 = 3
		} else {
			var _t1913 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1913 = 0
			} else {
				var _t1914 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1914 = 1
				} else {
					var _t1915 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1915 = 2
					} else {
						_t1915 = -1
					}
					_t1914 = _t1915
				}
				_t1913 = _t1914
			}
			_t1912 = _t1913
		}
		_t1911 = _t1912
	} else {
		_t1911 = -1
	}
	prediction1095 := _t1911
	var _t1916 *pb.Monoid
	if prediction1095 == 3 {
		_t1917 := p.parse_sum_monoid()
		sum_monoid1099 := _t1917
		_t1918 := &pb.Monoid{}
		_t1918.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1099}
		_t1916 = _t1918
	} else {
		var _t1919 *pb.Monoid
		if prediction1095 == 2 {
			_t1920 := p.parse_max_monoid()
			max_monoid1098 := _t1920
			_t1921 := &pb.Monoid{}
			_t1921.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1098}
			_t1919 = _t1921
		} else {
			var _t1922 *pb.Monoid
			if prediction1095 == 1 {
				_t1923 := p.parse_min_monoid()
				min_monoid1097 := _t1923
				_t1924 := &pb.Monoid{}
				_t1924.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1097}
				_t1922 = _t1924
			} else {
				var _t1925 *pb.Monoid
				if prediction1095 == 0 {
					_t1926 := p.parse_or_monoid()
					or_monoid1096 := _t1926
					_t1927 := &pb.Monoid{}
					_t1927.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1096}
					_t1925 = _t1927
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1922 = _t1925
			}
			_t1919 = _t1922
		}
		_t1916 = _t1919
	}
	result1101 := _t1916
	p.recordSpan(int(span_start1100), "Monoid")
	return result1101
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1102 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1928 := &pb.OrMonoid{}
	result1103 := _t1928
	p.recordSpan(int(span_start1102), "OrMonoid")
	return result1103
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1105 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1929 := p.parse_type()
	type1104 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.MinMonoid{Type: type1104}
	result1106 := _t1930
	p.recordSpan(int(span_start1105), "MinMonoid")
	return result1106
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1108 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1931 := p.parse_type()
	type1107 := _t1931
	p.consumeLiteral(")")
	_t1932 := &pb.MaxMonoid{Type: type1107}
	result1109 := _t1932
	p.recordSpan(int(span_start1108), "MaxMonoid")
	return result1109
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1111 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1933 := p.parse_type()
	type1110 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.SumMonoid{Type: type1110}
	result1112 := _t1934
	p.recordSpan(int(span_start1111), "SumMonoid")
	return result1112
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1935 := p.parse_monoid()
	monoid1113 := _t1935
	_t1936 := p.parse_relation_id()
	relation_id1114 := _t1936
	_t1937 := p.parse_abstraction_with_arity()
	abstraction_with_arity1115 := _t1937
	var _t1938 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1939 := p.parse_attrs()
		_t1938 = _t1939
	}
	attrs1116 := _t1938
	p.consumeLiteral(")")
	_t1940 := attrs1116
	if attrs1116 == nil {
		_t1940 = []*pb.Attribute{}
	}
	_t1941 := &pb.MonusDef{Monoid: monoid1113, Name: relation_id1114, Body: abstraction_with_arity1115[0].(*pb.Abstraction), Attrs: _t1940, ValueArity: abstraction_with_arity1115[1].(int64)}
	result1118 := _t1941
	p.recordSpan(int(span_start1117), "MonusDef")
	return result1118
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1123 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1942 := p.parse_relation_id()
	relation_id1119 := _t1942
	_t1943 := p.parse_abstraction()
	abstraction1120 := _t1943
	_t1944 := p.parse_functional_dependency_keys()
	functional_dependency_keys1121 := _t1944
	_t1945 := p.parse_functional_dependency_values()
	functional_dependency_values1122 := _t1945
	p.consumeLiteral(")")
	_t1946 := &pb.FunctionalDependency{Guard: abstraction1120, Keys: functional_dependency_keys1121, Values: functional_dependency_values1122}
	_t1947 := &pb.Constraint{Name: relation_id1119}
	_t1947.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1946}
	result1124 := _t1947
	p.recordSpan(int(span_start1123), "Constraint")
	return result1124
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1125 := []*pb.Var{}
	cond1126 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1126 {
		_t1948 := p.parse_var()
		item1127 := _t1948
		xs1125 = append(xs1125, item1127)
		cond1126 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1128 := xs1125
	p.consumeLiteral(")")
	return vars1128
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1129 := []*pb.Var{}
	cond1130 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1130 {
		_t1949 := p.parse_var()
		item1131 := _t1949
		xs1129 = append(xs1129, item1131)
		cond1130 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1132 := xs1129
	p.consumeLiteral(")")
	return vars1132
}

func (p *Parser) parse_data() *pb.Data {
	span_start1138 := int64(p.spanStart())
	var _t1950 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1951 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1951 = 3
		} else {
			var _t1952 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1952 = 0
			} else {
				var _t1953 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1953 = 2
				} else {
					var _t1954 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1954 = 1
					} else {
						_t1954 = -1
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
	prediction1133 := _t1950
	var _t1955 *pb.Data
	if prediction1133 == 3 {
		_t1956 := p.parse_iceberg_data()
		iceberg_data1137 := _t1956
		_t1957 := &pb.Data{}
		_t1957.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1137}
		_t1955 = _t1957
	} else {
		var _t1958 *pb.Data
		if prediction1133 == 2 {
			_t1959 := p.parse_csv_data()
			csv_data1136 := _t1959
			_t1960 := &pb.Data{}
			_t1960.DataType = &pb.Data_CsvData{CsvData: csv_data1136}
			_t1958 = _t1960
		} else {
			var _t1961 *pb.Data
			if prediction1133 == 1 {
				_t1962 := p.parse_betree_relation()
				betree_relation1135 := _t1962
				_t1963 := &pb.Data{}
				_t1963.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1135}
				_t1961 = _t1963
			} else {
				var _t1964 *pb.Data
				if prediction1133 == 0 {
					_t1965 := p.parse_edb()
					edb1134 := _t1965
					_t1966 := &pb.Data{}
					_t1966.DataType = &pb.Data_Edb{Edb: edb1134}
					_t1964 = _t1966
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1961 = _t1964
			}
			_t1958 = _t1961
		}
		_t1955 = _t1958
	}
	result1139 := _t1955
	p.recordSpan(int(span_start1138), "Data")
	return result1139
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1143 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1967 := p.parse_relation_id()
	relation_id1140 := _t1967
	_t1968 := p.parse_edb_path()
	edb_path1141 := _t1968
	_t1969 := p.parse_edb_types()
	edb_types1142 := _t1969
	p.consumeLiteral(")")
	_t1970 := &pb.EDB{TargetId: relation_id1140, Path: edb_path1141, Types: edb_types1142}
	result1144 := _t1970
	p.recordSpan(int(span_start1143), "EDB")
	return result1144
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1145 := []string{}
	cond1146 := p.matchLookaheadTerminal("STRING", 0)
	for cond1146 {
		item1147 := p.consumeTerminal("STRING").Value.str
		xs1145 = append(xs1145, item1147)
		cond1146 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1148 := xs1145
	p.consumeLiteral("]")
	return strings1148
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1149 := []*pb.Type{}
	cond1150 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1150 {
		_t1971 := p.parse_type()
		item1151 := _t1971
		xs1149 = append(xs1149, item1151)
		cond1150 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1152 := xs1149
	p.consumeLiteral("]")
	return types1152
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1972 := p.parse_relation_id()
	relation_id1153 := _t1972
	_t1973 := p.parse_betree_info()
	betree_info1154 := _t1973
	p.consumeLiteral(")")
	_t1974 := &pb.BeTreeRelation{Name: relation_id1153, RelationInfo: betree_info1154}
	result1156 := _t1974
	p.recordSpan(int(span_start1155), "BeTreeRelation")
	return result1156
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1160 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1975 := p.parse_betree_info_key_types()
	betree_info_key_types1157 := _t1975
	_t1976 := p.parse_betree_info_value_types()
	betree_info_value_types1158 := _t1976
	_t1977 := p.parse_config_dict()
	config_dict1159 := _t1977
	p.consumeLiteral(")")
	_t1978 := p.construct_betree_info(betree_info_key_types1157, betree_info_value_types1158, config_dict1159)
	result1161 := _t1978
	p.recordSpan(int(span_start1160), "BeTreeInfo")
	return result1161
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1162 := []*pb.Type{}
	cond1163 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1163 {
		_t1979 := p.parse_type()
		item1164 := _t1979
		xs1162 = append(xs1162, item1164)
		cond1163 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1165 := xs1162
	p.consumeLiteral(")")
	return types1165
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1166 := []*pb.Type{}
	cond1167 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1167 {
		_t1980 := p.parse_type()
		item1168 := _t1980
		xs1166 = append(xs1166, item1168)
		cond1167 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1169 := xs1166
	p.consumeLiteral(")")
	return types1169
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1174 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1981 := p.parse_csvlocator()
	csvlocator1170 := _t1981
	_t1982 := p.parse_csv_config()
	csv_config1171 := _t1982
	_t1983 := p.parse_gnf_columns()
	gnf_columns1172 := _t1983
	_t1984 := p.parse_csv_asof()
	csv_asof1173 := _t1984
	p.consumeLiteral(")")
	_t1985 := &pb.CSVData{Locator: csvlocator1170, Config: csv_config1171, Columns: gnf_columns1172, Asof: csv_asof1173}
	result1175 := _t1985
	p.recordSpan(int(span_start1174), "CSVData")
	return result1175
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1178 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1986 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1987 := p.parse_csv_locator_paths()
		_t1986 = _t1987
	}
	csv_locator_paths1176 := _t1986
	var _t1988 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1989 := p.parse_csv_locator_inline_data()
		_t1988 = ptr(_t1989)
	}
	csv_locator_inline_data1177 := _t1988
	p.consumeLiteral(")")
	_t1990 := csv_locator_paths1176
	if csv_locator_paths1176 == nil {
		_t1990 = []string{}
	}
	_t1991 := &pb.CSVLocator{Paths: _t1990, InlineData: []byte(deref(csv_locator_inline_data1177, ""))}
	result1179 := _t1991
	p.recordSpan(int(span_start1178), "CSVLocator")
	return result1179
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1180 := []string{}
	cond1181 := p.matchLookaheadTerminal("STRING", 0)
	for cond1181 {
		item1182 := p.consumeTerminal("STRING").Value.str
		xs1180 = append(xs1180, item1182)
		cond1181 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1183 := xs1180
	p.consumeLiteral(")")
	return strings1183
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1184 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1184
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1187 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1992 := p.parse_config_dict()
	config_dict1185 := _t1992
	var _t1993 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1994 := p.parse__storage_integration()
		_t1993 = _t1994
	}
	_storage_integration1186 := _t1993
	p.consumeLiteral(")")
	_t1995 := p.construct_csv_config(config_dict1185, _storage_integration1186)
	result1188 := _t1995
	p.recordSpan(int(span_start1187), "CSVConfig")
	return result1188
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t1996 := p.parse_config_dict()
	config_dict1189 := _t1996
	p.consumeLiteral(")")
	return config_dict1189
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1190 := []*pb.GNFColumn{}
	cond1191 := p.matchLookaheadLiteral("(", 0)
	for cond1191 {
		_t1997 := p.parse_gnf_column()
		item1192 := _t1997
		xs1190 = append(xs1190, item1192)
		cond1191 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1193 := xs1190
	p.consumeLiteral(")")
	return gnf_columns1193
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1200 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1998 := p.parse_gnf_column_path()
	gnf_column_path1194 := _t1998
	var _t1999 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2000 := p.parse_relation_id()
		_t1999 = _t2000
	}
	relation_id1195 := _t1999
	p.consumeLiteral("[")
	xs1196 := []*pb.Type{}
	cond1197 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1197 {
		_t2001 := p.parse_type()
		item1198 := _t2001
		xs1196 = append(xs1196, item1198)
		cond1197 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1199 := xs1196
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2002 := &pb.GNFColumn{ColumnPath: gnf_column_path1194, TargetId: relation_id1195, Types: types1199}
	result1201 := _t2002
	p.recordSpan(int(span_start1200), "GNFColumn")
	return result1201
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2003 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2003 = 1
	} else {
		var _t2004 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2004 = 0
		} else {
			_t2004 = -1
		}
		_t2003 = _t2004
	}
	prediction1202 := _t2003
	var _t2005 []string
	if prediction1202 == 1 {
		p.consumeLiteral("[")
		xs1204 := []string{}
		cond1205 := p.matchLookaheadTerminal("STRING", 0)
		for cond1205 {
			item1206 := p.consumeTerminal("STRING").Value.str
			xs1204 = append(xs1204, item1206)
			cond1205 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1207 := xs1204
		p.consumeLiteral("]")
		_t2005 = strings1207
	} else {
		var _t2006 []string
		if prediction1202 == 0 {
			string1203 := p.consumeTerminal("STRING").Value.str
			_ = string1203
			_t2006 = []string{string1203}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2005 = _t2006
	}
	return _t2005
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1208 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1208
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1215 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2007 := p.parse_iceberg_locator()
	iceberg_locator1209 := _t2007
	_t2008 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1210 := _t2008
	_t2009 := p.parse_gnf_columns()
	gnf_columns1211 := _t2009
	var _t2010 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2011 := p.parse_iceberg_from_snapshot()
		_t2010 = ptr(_t2011)
	}
	iceberg_from_snapshot1212 := _t2010
	var _t2012 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2013 := p.parse_iceberg_to_snapshot()
		_t2012 = ptr(_t2013)
	}
	iceberg_to_snapshot1213 := _t2012
	_t2014 := p.parse_boolean_value()
	boolean_value1214 := _t2014
	p.consumeLiteral(")")
	_t2015 := p.construct_iceberg_data(iceberg_locator1209, iceberg_catalog_config1210, gnf_columns1211, iceberg_from_snapshot1212, iceberg_to_snapshot1213, boolean_value1214)
	result1216 := _t2015
	p.recordSpan(int(span_start1215), "IcebergData")
	return result1216
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2016 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1217 := _t2016
	_t2017 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1218 := _t2017
	_t2018 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1219 := _t2018
	p.consumeLiteral(")")
	_t2019 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1217, Namespace: iceberg_locator_namespace1218, Warehouse: iceberg_locator_warehouse1219}
	result1221 := _t2019
	p.recordSpan(int(span_start1220), "IcebergLocator")
	return result1221
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1222 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1222
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1223 := []string{}
	cond1224 := p.matchLookaheadTerminal("STRING", 0)
	for cond1224 {
		item1225 := p.consumeTerminal("STRING").Value.str
		xs1223 = append(xs1223, item1225)
		cond1224 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1226 := xs1223
	p.consumeLiteral(")")
	return strings1226
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1227 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1227
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1232 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2020 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1228 := _t2020
	var _t2021 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2022 := p.parse_iceberg_catalog_config_scope()
		_t2021 = ptr(_t2022)
	}
	iceberg_catalog_config_scope1229 := _t2021
	_t2023 := p.parse_iceberg_properties()
	iceberg_properties1230 := _t2023
	_t2024 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1231 := _t2024
	p.consumeLiteral(")")
	_t2025 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1228, iceberg_catalog_config_scope1229, iceberg_properties1230, iceberg_auth_properties1231)
	result1233 := _t2025
	p.recordSpan(int(span_start1232), "IcebergCatalogConfig")
	return result1233
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1234 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1234
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1235 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1235
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1236 := [][]interface{}{}
	cond1237 := p.matchLookaheadLiteral("(", 0)
	for cond1237 {
		_t2026 := p.parse_iceberg_property_entry()
		item1238 := _t2026
		xs1236 = append(xs1236, item1238)
		cond1237 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1239 := xs1236
	p.consumeLiteral(")")
	return iceberg_property_entrys1239
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1240 := p.consumeTerminal("STRING").Value.str
	string_31241 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1240, string_31241}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1242 := [][]interface{}{}
	cond1243 := p.matchLookaheadLiteral("(", 0)
	for cond1243 {
		_t2027 := p.parse_iceberg_masked_property_entry()
		item1244 := _t2027
		xs1242 = append(xs1242, item1244)
		cond1243 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1245 := xs1242
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1245
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1246 := p.consumeTerminal("STRING").Value.str
	string_31247 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1246, string_31247}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1248 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1248
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1249 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1249
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1251 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2028 := p.parse_fragment_id()
	fragment_id1250 := _t2028
	p.consumeLiteral(")")
	_t2029 := &pb.Undefine{FragmentId: fragment_id1250}
	result1252 := _t2029
	p.recordSpan(int(span_start1251), "Undefine")
	return result1252
}

func (p *Parser) parse_context() *pb.Context {
	span_start1257 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1253 := []*pb.RelationId{}
	cond1254 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1254 {
		_t2030 := p.parse_relation_id()
		item1255 := _t2030
		xs1253 = append(xs1253, item1255)
		cond1254 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1256 := xs1253
	p.consumeLiteral(")")
	_t2031 := &pb.Context{Relations: relation_ids1256}
	result1258 := _t2031
	p.recordSpan(int(span_start1257), "Context")
	return result1258
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1264 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2032 := p.parse_edb_path()
	edb_path1259 := _t2032
	xs1260 := []*pb.SnapshotMapping{}
	cond1261 := p.matchLookaheadLiteral("[", 0)
	for cond1261 {
		_t2033 := p.parse_snapshot_mapping()
		item1262 := _t2033
		xs1260 = append(xs1260, item1262)
		cond1261 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1263 := xs1260
	p.consumeLiteral(")")
	_t2034 := &pb.Snapshot{Prefix: edb_path1259, Mappings: snapshot_mappings1263}
	result1265 := _t2034
	p.recordSpan(int(span_start1264), "Snapshot")
	return result1265
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1268 := int64(p.spanStart())
	_t2035 := p.parse_edb_path()
	edb_path1266 := _t2035
	_t2036 := p.parse_relation_id()
	relation_id1267 := _t2036
	_t2037 := &pb.SnapshotMapping{DestinationPath: edb_path1266, SourceRelation: relation_id1267}
	result1269 := _t2037
	p.recordSpan(int(span_start1268), "SnapshotMapping")
	return result1269
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1270 := []*pb.Read{}
	cond1271 := p.matchLookaheadLiteral("(", 0)
	for cond1271 {
		_t2038 := p.parse_read()
		item1272 := _t2038
		xs1270 = append(xs1270, item1272)
		cond1271 = p.matchLookaheadLiteral("(", 0)
	}
	reads1273 := xs1270
	p.consumeLiteral(")")
	return reads1273
}

func (p *Parser) parse_read() *pb.Read {
	span_start1281 := int64(p.spanStart())
	var _t2039 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2040 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2040 = 2
		} else {
			var _t2041 int64
			if p.matchLookaheadLiteral("output_export", 1) {
				_t2041 = 5
			} else {
				var _t2042 int64
				if p.matchLookaheadLiteral("output", 1) {
					_t2042 = 1
				} else {
					var _t2043 int64
					if p.matchLookaheadLiteral("export_iceberg", 1) {
						_t2043 = 4
					} else {
						var _t2044 int64
						if p.matchLookaheadLiteral("export", 1) {
							_t2044 = 4
						} else {
							var _t2045 int64
							if p.matchLookaheadLiteral("demand", 1) {
								_t2045 = 0
							} else {
								var _t2046 int64
								if p.matchLookaheadLiteral("abort", 1) {
									_t2046 = 3
								} else {
									_t2046 = -1
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
			}
			_t2040 = _t2041
		}
		_t2039 = _t2040
	} else {
		_t2039 = -1
	}
	prediction1274 := _t2039
	var _t2047 *pb.Read
	if prediction1274 == 5 {
		_t2048 := p.parse_export_output()
		export_output1280 := _t2048
		_t2049 := &pb.Read{}
		_t2049.ReadType = &pb.Read_ExportOutput{ExportOutput: export_output1280}
		_t2047 = _t2049
	} else {
		var _t2050 *pb.Read
		if prediction1274 == 4 {
			_t2051 := p.parse_export()
			export1279 := _t2051
			_t2052 := &pb.Read{}
			_t2052.ReadType = &pb.Read_Export{Export: export1279}
			_t2050 = _t2052
		} else {
			var _t2053 *pb.Read
			if prediction1274 == 3 {
				_t2054 := p.parse_abort()
				abort1278 := _t2054
				_t2055 := &pb.Read{}
				_t2055.ReadType = &pb.Read_Abort{Abort: abort1278}
				_t2053 = _t2055
			} else {
				var _t2056 *pb.Read
				if prediction1274 == 2 {
					_t2057 := p.parse_what_if()
					what_if1277 := _t2057
					_t2058 := &pb.Read{}
					_t2058.ReadType = &pb.Read_WhatIf{WhatIf: what_if1277}
					_t2056 = _t2058
				} else {
					var _t2059 *pb.Read
					if prediction1274 == 1 {
						_t2060 := p.parse_output()
						output1276 := _t2060
						_t2061 := &pb.Read{}
						_t2061.ReadType = &pb.Read_Output{Output: output1276}
						_t2059 = _t2061
					} else {
						var _t2062 *pb.Read
						if prediction1274 == 0 {
							_t2063 := p.parse_demand()
							demand1275 := _t2063
							_t2064 := &pb.Read{}
							_t2064.ReadType = &pb.Read_Demand{Demand: demand1275}
							_t2062 = _t2064
						} else {
							panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
						}
						_t2059 = _t2062
					}
					_t2056 = _t2059
				}
				_t2053 = _t2056
			}
			_t2050 = _t2053
		}
		_t2047 = _t2050
	}
	result1282 := _t2047
	p.recordSpan(int(span_start1281), "Read")
	return result1282
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1284 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2065 := p.parse_relation_id()
	relation_id1283 := _t2065
	p.consumeLiteral(")")
	_t2066 := &pb.Demand{RelationId: relation_id1283}
	result1285 := _t2066
	p.recordSpan(int(span_start1284), "Demand")
	return result1285
}

func (p *Parser) parse_output() *pb.Output {
	span_start1288 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2067 := p.parse_name()
	name1286 := _t2067
	_t2068 := p.parse_relation_id()
	relation_id1287 := _t2068
	p.consumeLiteral(")")
	_t2069 := &pb.Output{Name: name1286, RelationId: relation_id1287}
	result1289 := _t2069
	p.recordSpan(int(span_start1288), "Output")
	return result1289
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1292 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2070 := p.parse_name()
	name1290 := _t2070
	_t2071 := p.parse_epoch()
	epoch1291 := _t2071
	p.consumeLiteral(")")
	_t2072 := &pb.WhatIf{Branch: name1290, Epoch: epoch1291}
	result1293 := _t2072
	p.recordSpan(int(span_start1292), "WhatIf")
	return result1293
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1296 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2073 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2074 := p.parse_name()
		_t2073 = ptr(_t2074)
	}
	name1294 := _t2073
	_t2075 := p.parse_relation_id()
	relation_id1295 := _t2075
	p.consumeLiteral(")")
	_t2076 := &pb.Abort{Name: deref(name1294, "abort"), RelationId: relation_id1295}
	result1297 := _t2076
	p.recordSpan(int(span_start1296), "Abort")
	return result1297
}

func (p *Parser) parse_export() *pb.Export {
	span_start1301 := int64(p.spanStart())
	var _t2077 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2078 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2078 = 1
		} else {
			var _t2079 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2079 = 0
			} else {
				_t2079 = -1
			}
			_t2078 = _t2079
		}
		_t2077 = _t2078
	} else {
		_t2077 = -1
	}
	prediction1298 := _t2077
	var _t2080 *pb.Export
	if prediction1298 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2081 := p.parse_export_iceberg_config()
		export_iceberg_config1300 := _t2081
		p.consumeLiteral(")")
		_t2082 := &pb.Export{}
		_t2082.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1300}
		_t2080 = _t2082
	} else {
		var _t2083 *pb.Export
		if prediction1298 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2084 := p.parse_export_csv_config()
			export_csv_config1299 := _t2084
			p.consumeLiteral(")")
			_t2085 := &pb.Export{}
			_t2085.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1299}
			_t2083 = _t2085
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2080 = _t2083
	}
	result1302 := _t2080
	p.recordSpan(int(span_start1301), "Export")
	return result1302
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1310 := int64(p.spanStart())
	var _t2086 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2087 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2087 = 0
		} else {
			var _t2088 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2088 = 1
			} else {
				_t2088 = -1
			}
			_t2087 = _t2088
		}
		_t2086 = _t2087
	} else {
		_t2086 = -1
	}
	prediction1303 := _t2086
	var _t2089 *pb.ExportCSVConfig
	if prediction1303 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2090 := p.parse_export_csv_path()
		export_csv_path1307 := _t2090
		_t2091 := p.parse_export_csv_columns_list()
		export_csv_columns_list1308 := _t2091
		_t2092 := p.parse_config_dict()
		config_dict1309 := _t2092
		p.consumeLiteral(")")
		_t2093 := p.construct_export_csv_config(export_csv_path1307, export_csv_columns_list1308, config_dict1309)
		_t2089 = _t2093
	} else {
		var _t2094 *pb.ExportCSVConfig
		if prediction1303 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2095 := p.parse_export_csv_path()
			export_csv_path1304 := _t2095
			_t2096 := p.parse_export_csv_source()
			export_csv_source1305 := _t2096
			_t2097 := p.parse_csv_config()
			csv_config1306 := _t2097
			p.consumeLiteral(")")
			_t2098 := p.construct_export_csv_config_with_source(export_csv_path1304, export_csv_source1305, csv_config1306)
			_t2094 = _t2098
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2089 = _t2094
	}
	result1311 := _t2089
	p.recordSpan(int(span_start1310), "ExportCSVConfig")
	return result1311
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1312 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1312
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1319 := int64(p.spanStart())
	var _t2099 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2100 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2100 = 1
		} else {
			var _t2101 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2101 = 0
			} else {
				_t2101 = -1
			}
			_t2100 = _t2101
		}
		_t2099 = _t2100
	} else {
		_t2099 = -1
	}
	prediction1313 := _t2099
	var _t2102 *pb.ExportCSVSource
	if prediction1313 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2103 := p.parse_relation_id()
		relation_id1318 := _t2103
		p.consumeLiteral(")")
		_t2104 := &pb.ExportCSVSource{}
		_t2104.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1318}
		_t2102 = _t2104
	} else {
		var _t2105 *pb.ExportCSVSource
		if prediction1313 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1314 := []*pb.ExportCSVColumn{}
			cond1315 := p.matchLookaheadLiteral("(", 0)
			for cond1315 {
				_t2106 := p.parse_export_csv_column()
				item1316 := _t2106
				xs1314 = append(xs1314, item1316)
				cond1315 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1317 := xs1314
			p.consumeLiteral(")")
			_t2107 := &pb.ExportCSVColumns{Columns: export_csv_columns1317}
			_t2108 := &pb.ExportCSVSource{}
			_t2108.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2107}
			_t2105 = _t2108
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2102 = _t2105
	}
	result1320 := _t2102
	p.recordSpan(int(span_start1319), "ExportCSVSource")
	return result1320
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1323 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1321 := p.consumeTerminal("STRING").Value.str
	_t2109 := p.parse_relation_id()
	relation_id1322 := _t2109
	p.consumeLiteral(")")
	_t2110 := &pb.ExportCSVColumn{ColumnName: string1321, ColumnData: relation_id1322}
	result1324 := _t2110
	p.recordSpan(int(span_start1323), "ExportCSVColumn")
	return result1324
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1325 := []*pb.ExportCSVColumn{}
	cond1326 := p.matchLookaheadLiteral("(", 0)
	for cond1326 {
		_t2111 := p.parse_export_csv_column()
		item1327 := _t2111
		xs1325 = append(xs1325, item1327)
		cond1326 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1328 := xs1325
	p.consumeLiteral(")")
	return export_csv_columns1328
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1334 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2112 := p.parse_iceberg_locator()
	iceberg_locator1329 := _t2112
	_t2113 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1330 := _t2113
	_t2114 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1331 := _t2114
	_t2115 := p.parse_iceberg_table_properties()
	iceberg_table_properties1332 := _t2115
	var _t2116 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2117 := p.parse_config_dict()
		_t2116 = _t2117
	}
	config_dict1333 := _t2116
	p.consumeLiteral(")")
	_t2118 := p.construct_export_iceberg_config_full(iceberg_locator1329, iceberg_catalog_config1330, export_iceberg_table_def1331, iceberg_table_properties1332, config_dict1333)
	result1335 := _t2118
	p.recordSpan(int(span_start1334), "ExportIcebergConfig")
	return result1335
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1337 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2119 := p.parse_relation_id()
	relation_id1336 := _t2119
	p.consumeLiteral(")")
	result1338 := relation_id1336
	p.recordSpan(int(span_start1337), "RelationId")
	return result1338
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1339 := [][]interface{}{}
	cond1340 := p.matchLookaheadLiteral("(", 0)
	for cond1340 {
		_t2120 := p.parse_iceberg_property_entry()
		item1341 := _t2120
		xs1339 = append(xs1339, item1341)
		cond1340 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1342 := xs1339
	p.consumeLiteral(")")
	return iceberg_property_entrys1342
}

func (p *Parser) parse_export_output() *pb.ExportOutput {
	span_start1344 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output_export")
	_t2121 := p.parse_export_csv_output()
	export_csv_output1343 := _t2121
	p.consumeLiteral(")")
	_t2122 := &pb.ExportOutput{}
	_t2122.ExportOutput = &pb.ExportOutput_Csv{Csv: export_csv_output1343}
	result1345 := _t2122
	p.recordSpan(int(span_start1344), "ExportOutput")
	return result1345
}

func (p *Parser) parse_export_csv_output() *pb.ExportCSVOutput {
	span_start1348 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv")
	_t2123 := p.parse_export_csv_source()
	export_csv_source1346 := _t2123
	_t2124 := p.parse_csv_config()
	csv_config1347 := _t2124
	p.consumeLiteral(")")
	_t2125 := &pb.ExportCSVOutput{CsvSource: export_csv_source1346, CsvConfig: csv_config1347}
	result1349 := _t2125
	p.recordSpan(int(span_start1348), "ExportCSVOutput")
	return result1349
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
