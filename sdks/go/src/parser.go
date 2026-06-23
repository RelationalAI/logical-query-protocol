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
	var _t2113 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2113
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2114 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2114
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2115 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2115
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2116 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2116
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2117 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2117
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2118 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2118
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2119 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2119
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2120 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2120
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2121 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2121
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2122 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2122
	_t2123 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2123
	_t2124 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2124
	_t2125 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2125
	_t2126 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2126
	_t2127 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2127
	_t2128 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2128
	_t2129 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2129
	_t2130 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2130
	_t2131 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2131
	_t2132 := p._extract_value_string(dictGetValue(config, "csv_compression"), "")
	compression := _t2132
	_t2133 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2133
	_t2134 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2134
	_t2135 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2135
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.StorageIntegration {
	var _t2136 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2136
	config := dictFromList(storage_integration_opt)
	_t2137 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2138 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2139 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2140 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2141 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2142 := &pb.StorageIntegration{Provider: _t2137, AzureSasToken: _t2138, S3Region: _t2139, S3AccessKeyId: _t2140, S3SecretAccessKey: _t2141}
	return _t2142
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2143 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2143
	_t2144 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2144
	_t2145 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2145
	_t2146 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2146
	_t2147 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2147
	_t2148 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2148
	_t2149 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2149
	_t2150 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2150
	_t2151 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2151
	_t2152 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2152.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2152.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2152
	_t2153 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2153
}

func (p *Parser) default_configure() *pb.Configure {
	_t2154 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2154
	_t2155 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2155
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
	_t2156 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2156
	_t2157 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2157
	_t2158 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2158
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2159 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2159
	_t2160 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2160
	_t2161 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2161
	_t2162 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2162
	_t2163 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2163
	_t2164 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2164
	_t2165 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2165
	_t2166 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2166
}

func (p *Parser) construct_export_csv_config_with_location(location []interface{}, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2167 := &pb.ExportCSVConfig{Path: location[0].(string), TransactionOutputName: location[1].(string), CsvSource: csv_source, CsvConfig: csv_config}
	return _t2167
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2168 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2168
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2169 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2169
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2170 := config_dict
	if config_dict == nil {
		_t2170 = [][]interface{}{}
	}
	cfg := dictFromList(_t2170)
	_t2171 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2171
	_t2172 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2172
	_t2173 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2173
	table_props := stringMapFromPairs(table_property_pairs)
	_t2174 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2174
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start676 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1340 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1341 := p.parse_configure()
		_t1340 = _t1341
	}
	configure670 := _t1340
	var _t1342 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1343 := p.parse_sync()
		_t1342 = _t1343
	}
	sync671 := _t1342
	xs672 := []*pb.Epoch{}
	cond673 := p.matchLookaheadLiteral("(", 0)
	for cond673 {
		_t1344 := p.parse_epoch()
		item674 := _t1344
		xs672 = append(xs672, item674)
		cond673 = p.matchLookaheadLiteral("(", 0)
	}
	epochs675 := xs672
	p.consumeLiteral(")")
	_t1345 := p.default_configure()
	_t1346 := configure670
	if configure670 == nil {
		_t1346 = _t1345
	}
	_t1347 := &pb.Transaction{Epochs: epochs675, Configure: _t1346, Sync: sync671}
	result677 := _t1347
	p.recordSpan(int(span_start676), "Transaction")
	return result677
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start679 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1348 := p.parse_config_dict()
	config_dict678 := _t1348
	p.consumeLiteral(")")
	_t1349 := p.construct_configure(config_dict678)
	result680 := _t1349
	p.recordSpan(int(span_start679), "Configure")
	return result680
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs681 := [][]interface{}{}
	cond682 := p.matchLookaheadLiteral(":", 0)
	for cond682 {
		_t1350 := p.parse_config_key_value()
		item683 := _t1350
		xs681 = append(xs681, item683)
		cond682 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values684 := xs681
	p.consumeLiteral("}")
	return config_key_values684
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol685 := p.consumeTerminal("SYMBOL").Value.str
	_t1351 := p.parse_raw_value()
	raw_value686 := _t1351
	return []interface{}{symbol685, raw_value686}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start700 := int64(p.spanStart())
	var _t1352 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1352 = 12
	} else {
		var _t1353 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1353 = 11
		} else {
			var _t1354 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1354 = 12
			} else {
				var _t1355 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1356 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1356 = 1
					} else {
						var _t1357 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1357 = 0
						} else {
							_t1357 = -1
						}
						_t1356 = _t1357
					}
					_t1355 = _t1356
				} else {
					var _t1358 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1358 = 7
					} else {
						var _t1359 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1359 = 8
						} else {
							var _t1360 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1360 = 2
							} else {
								var _t1361 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1361 = 3
								} else {
									var _t1362 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1362 = 9
									} else {
										var _t1363 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1363 = 4
										} else {
											var _t1364 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1364 = 5
											} else {
												var _t1365 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1365 = 6
												} else {
													var _t1366 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1366 = 10
													} else {
														_t1366 = -1
													}
													_t1365 = _t1366
												}
												_t1364 = _t1365
											}
											_t1363 = _t1364
										}
										_t1362 = _t1363
									}
									_t1361 = _t1362
								}
								_t1360 = _t1361
							}
							_t1359 = _t1360
						}
						_t1358 = _t1359
					}
					_t1355 = _t1358
				}
				_t1354 = _t1355
			}
			_t1353 = _t1354
		}
		_t1352 = _t1353
	}
	prediction687 := _t1352
	var _t1367 *pb.Value
	if prediction687 == 12 {
		_t1368 := p.parse_boolean_value()
		boolean_value699 := _t1368
		_t1369 := &pb.Value{}
		_t1369.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value699}
		_t1367 = _t1369
	} else {
		var _t1370 *pb.Value
		if prediction687 == 11 {
			p.consumeLiteral("missing")
			_t1371 := &pb.MissingValue{}
			_t1372 := &pb.Value{}
			_t1372.Value = &pb.Value_MissingValue{MissingValue: _t1371}
			_t1370 = _t1372
		} else {
			var _t1373 *pb.Value
			if prediction687 == 10 {
				decimal698 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1374 := &pb.Value{}
				_t1374.Value = &pb.Value_DecimalValue{DecimalValue: decimal698}
				_t1373 = _t1374
			} else {
				var _t1375 *pb.Value
				if prediction687 == 9 {
					int128697 := p.consumeTerminal("INT128").Value.int128
					_t1376 := &pb.Value{}
					_t1376.Value = &pb.Value_Int128Value{Int128Value: int128697}
					_t1375 = _t1376
				} else {
					var _t1377 *pb.Value
					if prediction687 == 8 {
						uint128696 := p.consumeTerminal("UINT128").Value.uint128
						_t1378 := &pb.Value{}
						_t1378.Value = &pb.Value_Uint128Value{Uint128Value: uint128696}
						_t1377 = _t1378
					} else {
						var _t1379 *pb.Value
						if prediction687 == 7 {
							uint32695 := p.consumeTerminal("UINT32").Value.u32
							_t1380 := &pb.Value{}
							_t1380.Value = &pb.Value_Uint32Value{Uint32Value: uint32695}
							_t1379 = _t1380
						} else {
							var _t1381 *pb.Value
							if prediction687 == 6 {
								float694 := p.consumeTerminal("FLOAT").Value.f64
								_t1382 := &pb.Value{}
								_t1382.Value = &pb.Value_FloatValue{FloatValue: float694}
								_t1381 = _t1382
							} else {
								var _t1383 *pb.Value
								if prediction687 == 5 {
									float32693 := p.consumeTerminal("FLOAT32").Value.f32
									_t1384 := &pb.Value{}
									_t1384.Value = &pb.Value_Float32Value{Float32Value: float32693}
									_t1383 = _t1384
								} else {
									var _t1385 *pb.Value
									if prediction687 == 4 {
										int692 := p.consumeTerminal("INT").Value.i64
										_t1386 := &pb.Value{}
										_t1386.Value = &pb.Value_IntValue{IntValue: int692}
										_t1385 = _t1386
									} else {
										var _t1387 *pb.Value
										if prediction687 == 3 {
											int32691 := p.consumeTerminal("INT32").Value.i32
											_t1388 := &pb.Value{}
											_t1388.Value = &pb.Value_Int32Value{Int32Value: int32691}
											_t1387 = _t1388
										} else {
											var _t1389 *pb.Value
											if prediction687 == 2 {
												string690 := p.consumeTerminal("STRING").Value.str
												_t1390 := &pb.Value{}
												_t1390.Value = &pb.Value_StringValue{StringValue: string690}
												_t1389 = _t1390
											} else {
												var _t1391 *pb.Value
												if prediction687 == 1 {
													_t1392 := p.parse_raw_datetime()
													raw_datetime689 := _t1392
													_t1393 := &pb.Value{}
													_t1393.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime689}
													_t1391 = _t1393
												} else {
													var _t1394 *pb.Value
													if prediction687 == 0 {
														_t1395 := p.parse_raw_date()
														raw_date688 := _t1395
														_t1396 := &pb.Value{}
														_t1396.Value = &pb.Value_DateValue{DateValue: raw_date688}
														_t1394 = _t1396
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1391 = _t1394
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
						_t1377 = _t1379
					}
					_t1375 = _t1377
				}
				_t1373 = _t1375
			}
			_t1370 = _t1373
		}
		_t1367 = _t1370
	}
	result701 := _t1367
	p.recordSpan(int(span_start700), "Value")
	return result701
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start705 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int702 := p.consumeTerminal("INT").Value.i64
	int_3703 := p.consumeTerminal("INT").Value.i64
	int_4704 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1397 := &pb.DateValue{Year: int32(int702), Month: int32(int_3703), Day: int32(int_4704)}
	result706 := _t1397
	p.recordSpan(int(span_start705), "DateValue")
	return result706
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start714 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int707 := p.consumeTerminal("INT").Value.i64
	int_3708 := p.consumeTerminal("INT").Value.i64
	int_4709 := p.consumeTerminal("INT").Value.i64
	int_5710 := p.consumeTerminal("INT").Value.i64
	int_6711 := p.consumeTerminal("INT").Value.i64
	int_7712 := p.consumeTerminal("INT").Value.i64
	var _t1398 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1398 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8713 := _t1398
	p.consumeLiteral(")")
	_t1399 := &pb.DateTimeValue{Year: int32(int707), Month: int32(int_3708), Day: int32(int_4709), Hour: int32(int_5710), Minute: int32(int_6711), Second: int32(int_7712), Microsecond: int32(deref(int_8713, 0))}
	result715 := _t1399
	p.recordSpan(int(span_start714), "DateTimeValue")
	return result715
}

func (p *Parser) parse_boolean_value() bool {
	var _t1400 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1400 = 0
	} else {
		var _t1401 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1401 = 1
		} else {
			_t1401 = -1
		}
		_t1400 = _t1401
	}
	prediction716 := _t1400
	var _t1402 bool
	if prediction716 == 1 {
		p.consumeLiteral("false")
		_t1402 = false
	} else {
		var _t1403 bool
		if prediction716 == 0 {
			p.consumeLiteral("true")
			_t1403 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1402 = _t1403
	}
	return _t1402
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start721 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs717 := []*pb.FragmentId{}
	cond718 := p.matchLookaheadLiteral(":", 0)
	for cond718 {
		_t1404 := p.parse_fragment_id()
		item719 := _t1404
		xs717 = append(xs717, item719)
		cond718 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids720 := xs717
	p.consumeLiteral(")")
	_t1405 := &pb.Sync{Fragments: fragment_ids720}
	result722 := _t1405
	p.recordSpan(int(span_start721), "Sync")
	return result722
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start724 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol723 := p.consumeTerminal("SYMBOL").Value.str
	result725 := &pb.FragmentId{Id: []byte(symbol723)}
	p.recordSpan(int(span_start724), "FragmentId")
	return result725
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start728 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1406 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1407 := p.parse_epoch_writes()
		_t1406 = _t1407
	}
	epoch_writes726 := _t1406
	var _t1408 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1409 := p.parse_epoch_reads()
		_t1408 = _t1409
	}
	epoch_reads727 := _t1408
	p.consumeLiteral(")")
	_t1410 := epoch_writes726
	if epoch_writes726 == nil {
		_t1410 = []*pb.Write{}
	}
	_t1411 := epoch_reads727
	if epoch_reads727 == nil {
		_t1411 = []*pb.Read{}
	}
	_t1412 := &pb.Epoch{Writes: _t1410, Reads: _t1411}
	result729 := _t1412
	p.recordSpan(int(span_start728), "Epoch")
	return result729
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs730 := []*pb.Write{}
	cond731 := p.matchLookaheadLiteral("(", 0)
	for cond731 {
		_t1413 := p.parse_write()
		item732 := _t1413
		xs730 = append(xs730, item732)
		cond731 = p.matchLookaheadLiteral("(", 0)
	}
	writes733 := xs730
	p.consumeLiteral(")")
	return writes733
}

func (p *Parser) parse_write() *pb.Write {
	span_start739 := int64(p.spanStart())
	var _t1414 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1415 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1415 = 1
		} else {
			var _t1416 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1416 = 3
			} else {
				var _t1417 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1417 = 0
				} else {
					var _t1418 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1418 = 2
					} else {
						_t1418 = -1
					}
					_t1417 = _t1418
				}
				_t1416 = _t1417
			}
			_t1415 = _t1416
		}
		_t1414 = _t1415
	} else {
		_t1414 = -1
	}
	prediction734 := _t1414
	var _t1419 *pb.Write
	if prediction734 == 3 {
		_t1420 := p.parse_snapshot()
		snapshot738 := _t1420
		_t1421 := &pb.Write{}
		_t1421.WriteType = &pb.Write_Snapshot{Snapshot: snapshot738}
		_t1419 = _t1421
	} else {
		var _t1422 *pb.Write
		if prediction734 == 2 {
			_t1423 := p.parse_context()
			context737 := _t1423
			_t1424 := &pb.Write{}
			_t1424.WriteType = &pb.Write_Context{Context: context737}
			_t1422 = _t1424
		} else {
			var _t1425 *pb.Write
			if prediction734 == 1 {
				_t1426 := p.parse_undefine()
				undefine736 := _t1426
				_t1427 := &pb.Write{}
				_t1427.WriteType = &pb.Write_Undefine{Undefine: undefine736}
				_t1425 = _t1427
			} else {
				var _t1428 *pb.Write
				if prediction734 == 0 {
					_t1429 := p.parse_define()
					define735 := _t1429
					_t1430 := &pb.Write{}
					_t1430.WriteType = &pb.Write_Define{Define: define735}
					_t1428 = _t1430
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1425 = _t1428
			}
			_t1422 = _t1425
		}
		_t1419 = _t1422
	}
	result740 := _t1419
	p.recordSpan(int(span_start739), "Write")
	return result740
}

func (p *Parser) parse_define() *pb.Define {
	span_start742 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1431 := p.parse_fragment()
	fragment741 := _t1431
	p.consumeLiteral(")")
	_t1432 := &pb.Define{Fragment: fragment741}
	result743 := _t1432
	p.recordSpan(int(span_start742), "Define")
	return result743
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1433 := p.parse_new_fragment_id()
	new_fragment_id744 := _t1433
	xs745 := []*pb.Declaration{}
	cond746 := p.matchLookaheadLiteral("(", 0)
	for cond746 {
		_t1434 := p.parse_declaration()
		item747 := _t1434
		xs745 = append(xs745, item747)
		cond746 = p.matchLookaheadLiteral("(", 0)
	}
	declarations748 := xs745
	p.consumeLiteral(")")
	result750 := p.constructFragment(new_fragment_id744, declarations748)
	p.recordSpan(int(span_start749), "Fragment")
	return result750
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start752 := int64(p.spanStart())
	_t1435 := p.parse_fragment_id()
	fragment_id751 := _t1435
	p.startFragment(fragment_id751)
	result753 := fragment_id751
	p.recordSpan(int(span_start752), "FragmentId")
	return result753
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start759 := int64(p.spanStart())
	var _t1436 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1437 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1437 = 3
		} else {
			var _t1438 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1438 = 2
			} else {
				var _t1439 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1439 = 3
				} else {
					var _t1440 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1440 = 0
					} else {
						var _t1441 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1441 = 3
						} else {
							var _t1442 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1442 = 3
							} else {
								var _t1443 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1443 = 1
								} else {
									_t1443 = -1
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
	} else {
		_t1436 = -1
	}
	prediction754 := _t1436
	var _t1444 *pb.Declaration
	if prediction754 == 3 {
		_t1445 := p.parse_data()
		data758 := _t1445
		_t1446 := &pb.Declaration{}
		_t1446.DeclarationType = &pb.Declaration_Data{Data: data758}
		_t1444 = _t1446
	} else {
		var _t1447 *pb.Declaration
		if prediction754 == 2 {
			_t1448 := p.parse_constraint()
			constraint757 := _t1448
			_t1449 := &pb.Declaration{}
			_t1449.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint757}
			_t1447 = _t1449
		} else {
			var _t1450 *pb.Declaration
			if prediction754 == 1 {
				_t1451 := p.parse_algorithm()
				algorithm756 := _t1451
				_t1452 := &pb.Declaration{}
				_t1452.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm756}
				_t1450 = _t1452
			} else {
				var _t1453 *pb.Declaration
				if prediction754 == 0 {
					_t1454 := p.parse_def()
					def755 := _t1454
					_t1455 := &pb.Declaration{}
					_t1455.DeclarationType = &pb.Declaration_Def{Def: def755}
					_t1453 = _t1455
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1450 = _t1453
			}
			_t1447 = _t1450
		}
		_t1444 = _t1447
	}
	result760 := _t1444
	p.recordSpan(int(span_start759), "Declaration")
	return result760
}

func (p *Parser) parse_def() *pb.Def {
	span_start764 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1456 := p.parse_relation_id()
	relation_id761 := _t1456
	_t1457 := p.parse_abstraction()
	abstraction762 := _t1457
	var _t1458 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1459 := p.parse_attrs()
		_t1458 = _t1459
	}
	attrs763 := _t1458
	p.consumeLiteral(")")
	_t1460 := attrs763
	if attrs763 == nil {
		_t1460 = []*pb.Attribute{}
	}
	_t1461 := &pb.Def{Name: relation_id761, Body: abstraction762, Attrs: _t1460}
	result765 := _t1461
	p.recordSpan(int(span_start764), "Def")
	return result765
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start769 := int64(p.spanStart())
	var _t1462 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1462 = 0
	} else {
		var _t1463 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1463 = 1
		} else {
			_t1463 = -1
		}
		_t1462 = _t1463
	}
	prediction766 := _t1462
	var _t1464 *pb.RelationId
	if prediction766 == 1 {
		uint128768 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128768
		_t1464 = &pb.RelationId{IdLow: uint128768.Low, IdHigh: uint128768.High}
	} else {
		var _t1465 *pb.RelationId
		if prediction766 == 0 {
			p.consumeLiteral(":")
			symbol767 := p.consumeTerminal("SYMBOL").Value.str
			_t1465 = p.relationIdFromString(symbol767)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1464 = _t1465
	}
	result770 := _t1464
	p.recordSpan(int(span_start769), "RelationId")
	return result770
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start773 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1466 := p.parse_bindings()
	bindings771 := _t1466
	_t1467 := p.parse_formula()
	formula772 := _t1467
	p.consumeLiteral(")")
	_t1468 := &pb.Abstraction{Vars: listConcat(bindings771[0].([]*pb.Binding), bindings771[1].([]*pb.Binding)), Value: formula772}
	result774 := _t1468
	p.recordSpan(int(span_start773), "Abstraction")
	return result774
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs775 := []*pb.Binding{}
	cond776 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond776 {
		_t1469 := p.parse_binding()
		item777 := _t1469
		xs775 = append(xs775, item777)
		cond776 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings778 := xs775
	var _t1470 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1471 := p.parse_value_bindings()
		_t1470 = _t1471
	}
	value_bindings779 := _t1470
	p.consumeLiteral("]")
	_t1472 := value_bindings779
	if value_bindings779 == nil {
		_t1472 = []*pb.Binding{}
	}
	return []interface{}{bindings778, _t1472}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start782 := int64(p.spanStart())
	symbol780 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1473 := p.parse_type()
	type781 := _t1473
	_t1474 := &pb.Var{Name: symbol780}
	_t1475 := &pb.Binding{Var: _t1474, Type: type781}
	result783 := _t1475
	p.recordSpan(int(span_start782), "Binding")
	return result783
}

func (p *Parser) parse_type() *pb.Type {
	span_start799 := int64(p.spanStart())
	var _t1476 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1476 = 0
	} else {
		var _t1477 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1477 = 13
		} else {
			var _t1478 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1478 = 4
			} else {
				var _t1479 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1479 = 1
				} else {
					var _t1480 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1480 = 8
					} else {
						var _t1481 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1481 = 11
						} else {
							var _t1482 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1482 = 5
							} else {
								var _t1483 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1483 = 2
								} else {
									var _t1484 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1484 = 12
									} else {
										var _t1485 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1485 = 3
										} else {
											var _t1486 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1486 = 7
											} else {
												var _t1487 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1487 = 6
												} else {
													var _t1488 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1488 = 10
													} else {
														var _t1489 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1489 = 9
														} else {
															_t1489 = -1
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
							_t1481 = _t1482
						}
						_t1480 = _t1481
					}
					_t1479 = _t1480
				}
				_t1478 = _t1479
			}
			_t1477 = _t1478
		}
		_t1476 = _t1477
	}
	prediction784 := _t1476
	var _t1490 *pb.Type
	if prediction784 == 13 {
		_t1491 := p.parse_uint32_type()
		uint32_type798 := _t1491
		_t1492 := &pb.Type{}
		_t1492.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type798}
		_t1490 = _t1492
	} else {
		var _t1493 *pb.Type
		if prediction784 == 12 {
			_t1494 := p.parse_float32_type()
			float32_type797 := _t1494
			_t1495 := &pb.Type{}
			_t1495.Type = &pb.Type_Float32Type{Float32Type: float32_type797}
			_t1493 = _t1495
		} else {
			var _t1496 *pb.Type
			if prediction784 == 11 {
				_t1497 := p.parse_int32_type()
				int32_type796 := _t1497
				_t1498 := &pb.Type{}
				_t1498.Type = &pb.Type_Int32Type{Int32Type: int32_type796}
				_t1496 = _t1498
			} else {
				var _t1499 *pb.Type
				if prediction784 == 10 {
					_t1500 := p.parse_boolean_type()
					boolean_type795 := _t1500
					_t1501 := &pb.Type{}
					_t1501.Type = &pb.Type_BooleanType{BooleanType: boolean_type795}
					_t1499 = _t1501
				} else {
					var _t1502 *pb.Type
					if prediction784 == 9 {
						_t1503 := p.parse_decimal_type()
						decimal_type794 := _t1503
						_t1504 := &pb.Type{}
						_t1504.Type = &pb.Type_DecimalType{DecimalType: decimal_type794}
						_t1502 = _t1504
					} else {
						var _t1505 *pb.Type
						if prediction784 == 8 {
							_t1506 := p.parse_missing_type()
							missing_type793 := _t1506
							_t1507 := &pb.Type{}
							_t1507.Type = &pb.Type_MissingType{MissingType: missing_type793}
							_t1505 = _t1507
						} else {
							var _t1508 *pb.Type
							if prediction784 == 7 {
								_t1509 := p.parse_datetime_type()
								datetime_type792 := _t1509
								_t1510 := &pb.Type{}
								_t1510.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type792}
								_t1508 = _t1510
							} else {
								var _t1511 *pb.Type
								if prediction784 == 6 {
									_t1512 := p.parse_date_type()
									date_type791 := _t1512
									_t1513 := &pb.Type{}
									_t1513.Type = &pb.Type_DateType{DateType: date_type791}
									_t1511 = _t1513
								} else {
									var _t1514 *pb.Type
									if prediction784 == 5 {
										_t1515 := p.parse_int128_type()
										int128_type790 := _t1515
										_t1516 := &pb.Type{}
										_t1516.Type = &pb.Type_Int128Type{Int128Type: int128_type790}
										_t1514 = _t1516
									} else {
										var _t1517 *pb.Type
										if prediction784 == 4 {
											_t1518 := p.parse_uint128_type()
											uint128_type789 := _t1518
											_t1519 := &pb.Type{}
											_t1519.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type789}
											_t1517 = _t1519
										} else {
											var _t1520 *pb.Type
											if prediction784 == 3 {
												_t1521 := p.parse_float_type()
												float_type788 := _t1521
												_t1522 := &pb.Type{}
												_t1522.Type = &pb.Type_FloatType{FloatType: float_type788}
												_t1520 = _t1522
											} else {
												var _t1523 *pb.Type
												if prediction784 == 2 {
													_t1524 := p.parse_int_type()
													int_type787 := _t1524
													_t1525 := &pb.Type{}
													_t1525.Type = &pb.Type_IntType{IntType: int_type787}
													_t1523 = _t1525
												} else {
													var _t1526 *pb.Type
													if prediction784 == 1 {
														_t1527 := p.parse_string_type()
														string_type786 := _t1527
														_t1528 := &pb.Type{}
														_t1528.Type = &pb.Type_StringType{StringType: string_type786}
														_t1526 = _t1528
													} else {
														var _t1529 *pb.Type
														if prediction784 == 0 {
															_t1530 := p.parse_unspecified_type()
															unspecified_type785 := _t1530
															_t1531 := &pb.Type{}
															_t1531.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type785}
															_t1529 = _t1531
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1493 = _t1496
		}
		_t1490 = _t1493
	}
	result800 := _t1490
	p.recordSpan(int(span_start799), "Type")
	return result800
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1532 := &pb.UnspecifiedType{}
	result802 := _t1532
	p.recordSpan(int(span_start801), "UnspecifiedType")
	return result802
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1533 := &pb.StringType{}
	result804 := _t1533
	p.recordSpan(int(span_start803), "StringType")
	return result804
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1534 := &pb.IntType{}
	result806 := _t1534
	p.recordSpan(int(span_start805), "IntType")
	return result806
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1535 := &pb.FloatType{}
	result808 := _t1535
	p.recordSpan(int(span_start807), "FloatType")
	return result808
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1536 := &pb.UInt128Type{}
	result810 := _t1536
	p.recordSpan(int(span_start809), "UInt128Type")
	return result810
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1537 := &pb.Int128Type{}
	result812 := _t1537
	p.recordSpan(int(span_start811), "Int128Type")
	return result812
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1538 := &pb.DateType{}
	result814 := _t1538
	p.recordSpan(int(span_start813), "DateType")
	return result814
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1539 := &pb.DateTimeType{}
	result816 := _t1539
	p.recordSpan(int(span_start815), "DateTimeType")
	return result816
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1540 := &pb.MissingType{}
	result818 := _t1540
	p.recordSpan(int(span_start817), "MissingType")
	return result818
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start821 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int819 := p.consumeTerminal("INT").Value.i64
	int_3820 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1541 := &pb.DecimalType{Precision: int32(int819), Scale: int32(int_3820)}
	result822 := _t1541
	p.recordSpan(int(span_start821), "DecimalType")
	return result822
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start823 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1542 := &pb.BooleanType{}
	result824 := _t1542
	p.recordSpan(int(span_start823), "BooleanType")
	return result824
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start825 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1543 := &pb.Int32Type{}
	result826 := _t1543
	p.recordSpan(int(span_start825), "Int32Type")
	return result826
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start827 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1544 := &pb.Float32Type{}
	result828 := _t1544
	p.recordSpan(int(span_start827), "Float32Type")
	return result828
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1545 := &pb.UInt32Type{}
	result830 := _t1545
	p.recordSpan(int(span_start829), "UInt32Type")
	return result830
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs831 := []*pb.Binding{}
	cond832 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond832 {
		_t1546 := p.parse_binding()
		item833 := _t1546
		xs831 = append(xs831, item833)
		cond832 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings834 := xs831
	return bindings834
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start849 := int64(p.spanStart())
	var _t1547 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1548 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1548 = 0
		} else {
			var _t1549 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1549 = 11
			} else {
				var _t1550 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1550 = 3
				} else {
					var _t1551 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1551 = 10
					} else {
						var _t1552 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1552 = 9
						} else {
							var _t1553 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1553 = 5
							} else {
								var _t1554 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1554 = 6
								} else {
									var _t1555 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1555 = 7
									} else {
										var _t1556 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1556 = 1
										} else {
											var _t1557 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1557 = 2
											} else {
												var _t1558 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1558 = 12
												} else {
													var _t1559 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1559 = 8
													} else {
														var _t1560 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1560 = 4
														} else {
															var _t1561 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1561 = 10
															} else {
																var _t1562 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1562 = 10
																} else {
																	var _t1563 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1563 = 10
																	} else {
																		var _t1564 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1564 = 10
																		} else {
																			var _t1565 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1565 = 10
																			} else {
																				var _t1566 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1566 = 10
																				} else {
																					var _t1567 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1567 = 10
																					} else {
																						var _t1568 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1568 = 10
																						} else {
																							var _t1569 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1569 = 10
																							} else {
																								_t1569 = -1
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
	} else {
		_t1547 = -1
	}
	prediction835 := _t1547
	var _t1570 *pb.Formula
	if prediction835 == 12 {
		_t1571 := p.parse_cast()
		cast848 := _t1571
		_t1572 := &pb.Formula{}
		_t1572.FormulaType = &pb.Formula_Cast{Cast: cast848}
		_t1570 = _t1572
	} else {
		var _t1573 *pb.Formula
		if prediction835 == 11 {
			_t1574 := p.parse_rel_atom()
			rel_atom847 := _t1574
			_t1575 := &pb.Formula{}
			_t1575.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom847}
			_t1573 = _t1575
		} else {
			var _t1576 *pb.Formula
			if prediction835 == 10 {
				_t1577 := p.parse_primitive()
				primitive846 := _t1577
				_t1578 := &pb.Formula{}
				_t1578.FormulaType = &pb.Formula_Primitive{Primitive: primitive846}
				_t1576 = _t1578
			} else {
				var _t1579 *pb.Formula
				if prediction835 == 9 {
					_t1580 := p.parse_pragma()
					pragma845 := _t1580
					_t1581 := &pb.Formula{}
					_t1581.FormulaType = &pb.Formula_Pragma{Pragma: pragma845}
					_t1579 = _t1581
				} else {
					var _t1582 *pb.Formula
					if prediction835 == 8 {
						_t1583 := p.parse_atom()
						atom844 := _t1583
						_t1584 := &pb.Formula{}
						_t1584.FormulaType = &pb.Formula_Atom{Atom: atom844}
						_t1582 = _t1584
					} else {
						var _t1585 *pb.Formula
						if prediction835 == 7 {
							_t1586 := p.parse_ffi()
							ffi843 := _t1586
							_t1587 := &pb.Formula{}
							_t1587.FormulaType = &pb.Formula_Ffi{Ffi: ffi843}
							_t1585 = _t1587
						} else {
							var _t1588 *pb.Formula
							if prediction835 == 6 {
								_t1589 := p.parse_not()
								not842 := _t1589
								_t1590 := &pb.Formula{}
								_t1590.FormulaType = &pb.Formula_Not{Not: not842}
								_t1588 = _t1590
							} else {
								var _t1591 *pb.Formula
								if prediction835 == 5 {
									_t1592 := p.parse_disjunction()
									disjunction841 := _t1592
									_t1593 := &pb.Formula{}
									_t1593.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction841}
									_t1591 = _t1593
								} else {
									var _t1594 *pb.Formula
									if prediction835 == 4 {
										_t1595 := p.parse_conjunction()
										conjunction840 := _t1595
										_t1596 := &pb.Formula{}
										_t1596.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction840}
										_t1594 = _t1596
									} else {
										var _t1597 *pb.Formula
										if prediction835 == 3 {
											_t1598 := p.parse_reduce()
											reduce839 := _t1598
											_t1599 := &pb.Formula{}
											_t1599.FormulaType = &pb.Formula_Reduce{Reduce: reduce839}
											_t1597 = _t1599
										} else {
											var _t1600 *pb.Formula
											if prediction835 == 2 {
												_t1601 := p.parse_exists()
												exists838 := _t1601
												_t1602 := &pb.Formula{}
												_t1602.FormulaType = &pb.Formula_Exists{Exists: exists838}
												_t1600 = _t1602
											} else {
												var _t1603 *pb.Formula
												if prediction835 == 1 {
													_t1604 := p.parse_false()
													false837 := _t1604
													_t1605 := &pb.Formula{}
													_t1605.FormulaType = &pb.Formula_Disjunction{Disjunction: false837}
													_t1603 = _t1605
												} else {
													var _t1606 *pb.Formula
													if prediction835 == 0 {
														_t1607 := p.parse_true()
														true836 := _t1607
														_t1608 := &pb.Formula{}
														_t1608.FormulaType = &pb.Formula_Conjunction{Conjunction: true836}
														_t1606 = _t1608
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1573 = _t1576
		}
		_t1570 = _t1573
	}
	result850 := _t1570
	p.recordSpan(int(span_start849), "Formula")
	return result850
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1609 := &pb.Conjunction{Args: []*pb.Formula{}}
	result852 := _t1609
	p.recordSpan(int(span_start851), "Conjunction")
	return result852
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1610 := &pb.Disjunction{Args: []*pb.Formula{}}
	result854 := _t1610
	p.recordSpan(int(span_start853), "Disjunction")
	return result854
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1611 := p.parse_bindings()
	bindings855 := _t1611
	_t1612 := p.parse_formula()
	formula856 := _t1612
	p.consumeLiteral(")")
	_t1613 := &pb.Abstraction{Vars: listConcat(bindings855[0].([]*pb.Binding), bindings855[1].([]*pb.Binding)), Value: formula856}
	_t1614 := &pb.Exists{Body: _t1613}
	result858 := _t1614
	p.recordSpan(int(span_start857), "Exists")
	return result858
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start862 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1615 := p.parse_abstraction()
	abstraction859 := _t1615
	_t1616 := p.parse_abstraction()
	abstraction_3860 := _t1616
	_t1617 := p.parse_terms()
	terms861 := _t1617
	p.consumeLiteral(")")
	_t1618 := &pb.Reduce{Op: abstraction859, Body: abstraction_3860, Terms: terms861}
	result863 := _t1618
	p.recordSpan(int(span_start862), "Reduce")
	return result863
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs864 := []*pb.Term{}
	cond865 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond865 {
		_t1619 := p.parse_term()
		item866 := _t1619
		xs864 = append(xs864, item866)
		cond865 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms867 := xs864
	p.consumeLiteral(")")
	return terms867
}

func (p *Parser) parse_term() *pb.Term {
	span_start871 := int64(p.spanStart())
	var _t1620 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1620 = 1
	} else {
		var _t1621 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1621 = 1
		} else {
			var _t1622 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1622 = 1
			} else {
				var _t1623 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1623 = 1
				} else {
					var _t1624 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1624 = 0
					} else {
						var _t1625 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1625 = 1
						} else {
							var _t1626 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1626 = 1
							} else {
								var _t1627 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1627 = 1
								} else {
									var _t1628 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1628 = 1
									} else {
										var _t1629 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1629 = 1
										} else {
											var _t1630 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1630 = 1
											} else {
												var _t1631 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1631 = 1
												} else {
													var _t1632 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1632 = 1
													} else {
														var _t1633 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1633 = 1
														} else {
															_t1633 = -1
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
	prediction868 := _t1620
	var _t1634 *pb.Term
	if prediction868 == 1 {
		_t1635 := p.parse_value()
		value870 := _t1635
		_t1636 := &pb.Term{}
		_t1636.TermType = &pb.Term_Constant{Constant: value870}
		_t1634 = _t1636
	} else {
		var _t1637 *pb.Term
		if prediction868 == 0 {
			_t1638 := p.parse_var()
			var869 := _t1638
			_t1639 := &pb.Term{}
			_t1639.TermType = &pb.Term_Var{Var: var869}
			_t1637 = _t1639
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1634 = _t1637
	}
	result872 := _t1634
	p.recordSpan(int(span_start871), "Term")
	return result872
}

func (p *Parser) parse_var() *pb.Var {
	span_start874 := int64(p.spanStart())
	symbol873 := p.consumeTerminal("SYMBOL").Value.str
	_t1640 := &pb.Var{Name: symbol873}
	result875 := _t1640
	p.recordSpan(int(span_start874), "Var")
	return result875
}

func (p *Parser) parse_value() *pb.Value {
	span_start889 := int64(p.spanStart())
	var _t1641 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1641 = 12
	} else {
		var _t1642 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1642 = 11
		} else {
			var _t1643 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1643 = 12
			} else {
				var _t1644 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1645 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1645 = 1
					} else {
						var _t1646 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1646 = 0
						} else {
							_t1646 = -1
						}
						_t1645 = _t1646
					}
					_t1644 = _t1645
				} else {
					var _t1647 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1647 = 7
					} else {
						var _t1648 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1648 = 8
						} else {
							var _t1649 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1649 = 2
							} else {
								var _t1650 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1650 = 3
								} else {
									var _t1651 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1651 = 9
									} else {
										var _t1652 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1652 = 4
										} else {
											var _t1653 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1653 = 5
											} else {
												var _t1654 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1654 = 6
												} else {
													var _t1655 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1655 = 10
													} else {
														_t1655 = -1
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
					_t1644 = _t1647
				}
				_t1643 = _t1644
			}
			_t1642 = _t1643
		}
		_t1641 = _t1642
	}
	prediction876 := _t1641
	var _t1656 *pb.Value
	if prediction876 == 12 {
		_t1657 := p.parse_boolean_value()
		boolean_value888 := _t1657
		_t1658 := &pb.Value{}
		_t1658.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value888}
		_t1656 = _t1658
	} else {
		var _t1659 *pb.Value
		if prediction876 == 11 {
			p.consumeLiteral("missing")
			_t1660 := &pb.MissingValue{}
			_t1661 := &pb.Value{}
			_t1661.Value = &pb.Value_MissingValue{MissingValue: _t1660}
			_t1659 = _t1661
		} else {
			var _t1662 *pb.Value
			if prediction876 == 10 {
				formatted_decimal887 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1663 := &pb.Value{}
				_t1663.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal887}
				_t1662 = _t1663
			} else {
				var _t1664 *pb.Value
				if prediction876 == 9 {
					formatted_int128886 := p.consumeTerminal("INT128").Value.int128
					_t1665 := &pb.Value{}
					_t1665.Value = &pb.Value_Int128Value{Int128Value: formatted_int128886}
					_t1664 = _t1665
				} else {
					var _t1666 *pb.Value
					if prediction876 == 8 {
						formatted_uint128885 := p.consumeTerminal("UINT128").Value.uint128
						_t1667 := &pb.Value{}
						_t1667.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128885}
						_t1666 = _t1667
					} else {
						var _t1668 *pb.Value
						if prediction876 == 7 {
							formatted_uint32884 := p.consumeTerminal("UINT32").Value.u32
							_t1669 := &pb.Value{}
							_t1669.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32884}
							_t1668 = _t1669
						} else {
							var _t1670 *pb.Value
							if prediction876 == 6 {
								formatted_float883 := p.consumeTerminal("FLOAT").Value.f64
								_t1671 := &pb.Value{}
								_t1671.Value = &pb.Value_FloatValue{FloatValue: formatted_float883}
								_t1670 = _t1671
							} else {
								var _t1672 *pb.Value
								if prediction876 == 5 {
									formatted_float32882 := p.consumeTerminal("FLOAT32").Value.f32
									_t1673 := &pb.Value{}
									_t1673.Value = &pb.Value_Float32Value{Float32Value: formatted_float32882}
									_t1672 = _t1673
								} else {
									var _t1674 *pb.Value
									if prediction876 == 4 {
										formatted_int881 := p.consumeTerminal("INT").Value.i64
										_t1675 := &pb.Value{}
										_t1675.Value = &pb.Value_IntValue{IntValue: formatted_int881}
										_t1674 = _t1675
									} else {
										var _t1676 *pb.Value
										if prediction876 == 3 {
											formatted_int32880 := p.consumeTerminal("INT32").Value.i32
											_t1677 := &pb.Value{}
											_t1677.Value = &pb.Value_Int32Value{Int32Value: formatted_int32880}
											_t1676 = _t1677
										} else {
											var _t1678 *pb.Value
											if prediction876 == 2 {
												formatted_string879 := p.consumeTerminal("STRING").Value.str
												_t1679 := &pb.Value{}
												_t1679.Value = &pb.Value_StringValue{StringValue: formatted_string879}
												_t1678 = _t1679
											} else {
												var _t1680 *pb.Value
												if prediction876 == 1 {
													_t1681 := p.parse_datetime()
													datetime878 := _t1681
													_t1682 := &pb.Value{}
													_t1682.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime878}
													_t1680 = _t1682
												} else {
													var _t1683 *pb.Value
													if prediction876 == 0 {
														_t1684 := p.parse_date()
														date877 := _t1684
														_t1685 := &pb.Value{}
														_t1685.Value = &pb.Value_DateValue{DateValue: date877}
														_t1683 = _t1685
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1680 = _t1683
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
						_t1666 = _t1668
					}
					_t1664 = _t1666
				}
				_t1662 = _t1664
			}
			_t1659 = _t1662
		}
		_t1656 = _t1659
	}
	result890 := _t1656
	p.recordSpan(int(span_start889), "Value")
	return result890
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start894 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int891 := p.consumeTerminal("INT").Value.i64
	formatted_int_3892 := p.consumeTerminal("INT").Value.i64
	formatted_int_4893 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1686 := &pb.DateValue{Year: int32(formatted_int891), Month: int32(formatted_int_3892), Day: int32(formatted_int_4893)}
	result895 := _t1686
	p.recordSpan(int(span_start894), "DateValue")
	return result895
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int896 := p.consumeTerminal("INT").Value.i64
	formatted_int_3897 := p.consumeTerminal("INT").Value.i64
	formatted_int_4898 := p.consumeTerminal("INT").Value.i64
	formatted_int_5899 := p.consumeTerminal("INT").Value.i64
	formatted_int_6900 := p.consumeTerminal("INT").Value.i64
	formatted_int_7901 := p.consumeTerminal("INT").Value.i64
	var _t1687 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1687 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8902 := _t1687
	p.consumeLiteral(")")
	_t1688 := &pb.DateTimeValue{Year: int32(formatted_int896), Month: int32(formatted_int_3897), Day: int32(formatted_int_4898), Hour: int32(formatted_int_5899), Minute: int32(formatted_int_6900), Second: int32(formatted_int_7901), Microsecond: int32(deref(formatted_int_8902, 0))}
	result904 := _t1688
	p.recordSpan(int(span_start903), "DateTimeValue")
	return result904
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs905 := []*pb.Formula{}
	cond906 := p.matchLookaheadLiteral("(", 0)
	for cond906 {
		_t1689 := p.parse_formula()
		item907 := _t1689
		xs905 = append(xs905, item907)
		cond906 = p.matchLookaheadLiteral("(", 0)
	}
	formulas908 := xs905
	p.consumeLiteral(")")
	_t1690 := &pb.Conjunction{Args: formulas908}
	result910 := _t1690
	p.recordSpan(int(span_start909), "Conjunction")
	return result910
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start915 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs911 := []*pb.Formula{}
	cond912 := p.matchLookaheadLiteral("(", 0)
	for cond912 {
		_t1691 := p.parse_formula()
		item913 := _t1691
		xs911 = append(xs911, item913)
		cond912 = p.matchLookaheadLiteral("(", 0)
	}
	formulas914 := xs911
	p.consumeLiteral(")")
	_t1692 := &pb.Disjunction{Args: formulas914}
	result916 := _t1692
	p.recordSpan(int(span_start915), "Disjunction")
	return result916
}

func (p *Parser) parse_not() *pb.Not {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1693 := p.parse_formula()
	formula917 := _t1693
	p.consumeLiteral(")")
	_t1694 := &pb.Not{Arg: formula917}
	result919 := _t1694
	p.recordSpan(int(span_start918), "Not")
	return result919
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1695 := p.parse_name()
	name920 := _t1695
	_t1696 := p.parse_ffi_args()
	ffi_args921 := _t1696
	_t1697 := p.parse_terms()
	terms922 := _t1697
	p.consumeLiteral(")")
	_t1698 := &pb.FFI{Name: name920, Args: ffi_args921, Terms: terms922}
	result924 := _t1698
	p.recordSpan(int(span_start923), "FFI")
	return result924
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol925 := p.consumeTerminal("SYMBOL").Value.str
	return symbol925
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs926 := []*pb.Abstraction{}
	cond927 := p.matchLookaheadLiteral("(", 0)
	for cond927 {
		_t1699 := p.parse_abstraction()
		item928 := _t1699
		xs926 = append(xs926, item928)
		cond927 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions929 := xs926
	p.consumeLiteral(")")
	return abstractions929
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start935 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1700 := p.parse_relation_id()
	relation_id930 := _t1700
	xs931 := []*pb.Term{}
	cond932 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond932 {
		_t1701 := p.parse_term()
		item933 := _t1701
		xs931 = append(xs931, item933)
		cond932 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms934 := xs931
	p.consumeLiteral(")")
	_t1702 := &pb.Atom{Name: relation_id930, Terms: terms934}
	result936 := _t1702
	p.recordSpan(int(span_start935), "Atom")
	return result936
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1703 := p.parse_name()
	name937 := _t1703
	xs938 := []*pb.Term{}
	cond939 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond939 {
		_t1704 := p.parse_term()
		item940 := _t1704
		xs938 = append(xs938, item940)
		cond939 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms941 := xs938
	p.consumeLiteral(")")
	_t1705 := &pb.Pragma{Name: name937, Terms: terms941}
	result943 := _t1705
	p.recordSpan(int(span_start942), "Pragma")
	return result943
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start959 := int64(p.spanStart())
	var _t1706 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1707 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1707 = 9
		} else {
			var _t1708 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1708 = 4
			} else {
				var _t1709 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1709 = 3
				} else {
					var _t1710 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1710 = 0
					} else {
						var _t1711 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1711 = 2
						} else {
							var _t1712 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1712 = 1
							} else {
								var _t1713 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1713 = 8
								} else {
									var _t1714 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1714 = 6
									} else {
										var _t1715 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1715 = 5
										} else {
											var _t1716 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1716 = 7
											} else {
												_t1716 = -1
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
	} else {
		_t1706 = -1
	}
	prediction944 := _t1706
	var _t1717 *pb.Primitive
	if prediction944 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1718 := p.parse_name()
		name954 := _t1718
		xs955 := []*pb.RelTerm{}
		cond956 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond956 {
			_t1719 := p.parse_rel_term()
			item957 := _t1719
			xs955 = append(xs955, item957)
			cond956 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms958 := xs955
		p.consumeLiteral(")")
		_t1720 := &pb.Primitive{Name: name954, Terms: rel_terms958}
		_t1717 = _t1720
	} else {
		var _t1721 *pb.Primitive
		if prediction944 == 8 {
			_t1722 := p.parse_divide()
			divide953 := _t1722
			_t1721 = divide953
		} else {
			var _t1723 *pb.Primitive
			if prediction944 == 7 {
				_t1724 := p.parse_multiply()
				multiply952 := _t1724
				_t1723 = multiply952
			} else {
				var _t1725 *pb.Primitive
				if prediction944 == 6 {
					_t1726 := p.parse_minus()
					minus951 := _t1726
					_t1725 = minus951
				} else {
					var _t1727 *pb.Primitive
					if prediction944 == 5 {
						_t1728 := p.parse_add()
						add950 := _t1728
						_t1727 = add950
					} else {
						var _t1729 *pb.Primitive
						if prediction944 == 4 {
							_t1730 := p.parse_gt_eq()
							gt_eq949 := _t1730
							_t1729 = gt_eq949
						} else {
							var _t1731 *pb.Primitive
							if prediction944 == 3 {
								_t1732 := p.parse_gt()
								gt948 := _t1732
								_t1731 = gt948
							} else {
								var _t1733 *pb.Primitive
								if prediction944 == 2 {
									_t1734 := p.parse_lt_eq()
									lt_eq947 := _t1734
									_t1733 = lt_eq947
								} else {
									var _t1735 *pb.Primitive
									if prediction944 == 1 {
										_t1736 := p.parse_lt()
										lt946 := _t1736
										_t1735 = lt946
									} else {
										var _t1737 *pb.Primitive
										if prediction944 == 0 {
											_t1738 := p.parse_eq()
											eq945 := _t1738
											_t1737 = eq945
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1725 = _t1727
				}
				_t1723 = _t1725
			}
			_t1721 = _t1723
		}
		_t1717 = _t1721
	}
	result960 := _t1717
	p.recordSpan(int(span_start959), "Primitive")
	return result960
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start963 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1739 := p.parse_term()
	term961 := _t1739
	_t1740 := p.parse_term()
	term_3962 := _t1740
	p.consumeLiteral(")")
	_t1741 := &pb.RelTerm{}
	_t1741.RelTermType = &pb.RelTerm_Term{Term: term961}
	_t1742 := &pb.RelTerm{}
	_t1742.RelTermType = &pb.RelTerm_Term{Term: term_3962}
	_t1743 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1741, _t1742}}
	result964 := _t1743
	p.recordSpan(int(span_start963), "Primitive")
	return result964
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start967 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1744 := p.parse_term()
	term965 := _t1744
	_t1745 := p.parse_term()
	term_3966 := _t1745
	p.consumeLiteral(")")
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term965}
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term_3966}
	_t1748 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1746, _t1747}}
	result968 := _t1748
	p.recordSpan(int(span_start967), "Primitive")
	return result968
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start971 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1749 := p.parse_term()
	term969 := _t1749
	_t1750 := p.parse_term()
	term_3970 := _t1750
	p.consumeLiteral(")")
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term969}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_3970}
	_t1753 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1751, _t1752}}
	result972 := _t1753
	p.recordSpan(int(span_start971), "Primitive")
	return result972
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1754 := p.parse_term()
	term973 := _t1754
	_t1755 := p.parse_term()
	term_3974 := _t1755
	p.consumeLiteral(")")
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term973}
	_t1757 := &pb.RelTerm{}
	_t1757.RelTermType = &pb.RelTerm_Term{Term: term_3974}
	_t1758 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1756, _t1757}}
	result976 := _t1758
	p.recordSpan(int(span_start975), "Primitive")
	return result976
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1759 := p.parse_term()
	term977 := _t1759
	_t1760 := p.parse_term()
	term_3978 := _t1760
	p.consumeLiteral(")")
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term977}
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term_3978}
	_t1763 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1761, _t1762}}
	result980 := _t1763
	p.recordSpan(int(span_start979), "Primitive")
	return result980
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1764 := p.parse_term()
	term981 := _t1764
	_t1765 := p.parse_term()
	term_3982 := _t1765
	_t1766 := p.parse_term()
	term_4983 := _t1766
	p.consumeLiteral(")")
	_t1767 := &pb.RelTerm{}
	_t1767.RelTermType = &pb.RelTerm_Term{Term: term981}
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term_3982}
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term_4983}
	_t1770 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1767, _t1768, _t1769}}
	result985 := _t1770
	p.recordSpan(int(span_start984), "Primitive")
	return result985
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start989 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1771 := p.parse_term()
	term986 := _t1771
	_t1772 := p.parse_term()
	term_3987 := _t1772
	_t1773 := p.parse_term()
	term_4988 := _t1773
	p.consumeLiteral(")")
	_t1774 := &pb.RelTerm{}
	_t1774.RelTermType = &pb.RelTerm_Term{Term: term986}
	_t1775 := &pb.RelTerm{}
	_t1775.RelTermType = &pb.RelTerm_Term{Term: term_3987}
	_t1776 := &pb.RelTerm{}
	_t1776.RelTermType = &pb.RelTerm_Term{Term: term_4988}
	_t1777 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1774, _t1775, _t1776}}
	result990 := _t1777
	p.recordSpan(int(span_start989), "Primitive")
	return result990
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start994 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1778 := p.parse_term()
	term991 := _t1778
	_t1779 := p.parse_term()
	term_3992 := _t1779
	_t1780 := p.parse_term()
	term_4993 := _t1780
	p.consumeLiteral(")")
	_t1781 := &pb.RelTerm{}
	_t1781.RelTermType = &pb.RelTerm_Term{Term: term991}
	_t1782 := &pb.RelTerm{}
	_t1782.RelTermType = &pb.RelTerm_Term{Term: term_3992}
	_t1783 := &pb.RelTerm{}
	_t1783.RelTermType = &pb.RelTerm_Term{Term: term_4993}
	_t1784 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1781, _t1782, _t1783}}
	result995 := _t1784
	p.recordSpan(int(span_start994), "Primitive")
	return result995
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start999 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1785 := p.parse_term()
	term996 := _t1785
	_t1786 := p.parse_term()
	term_3997 := _t1786
	_t1787 := p.parse_term()
	term_4998 := _t1787
	p.consumeLiteral(")")
	_t1788 := &pb.RelTerm{}
	_t1788.RelTermType = &pb.RelTerm_Term{Term: term996}
	_t1789 := &pb.RelTerm{}
	_t1789.RelTermType = &pb.RelTerm_Term{Term: term_3997}
	_t1790 := &pb.RelTerm{}
	_t1790.RelTermType = &pb.RelTerm_Term{Term: term_4998}
	_t1791 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1788, _t1789, _t1790}}
	result1000 := _t1791
	p.recordSpan(int(span_start999), "Primitive")
	return result1000
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1004 := int64(p.spanStart())
	var _t1792 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1792 = 1
	} else {
		var _t1793 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1793 = 1
		} else {
			var _t1794 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1794 = 1
			} else {
				var _t1795 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1795 = 1
				} else {
					var _t1796 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1796 = 0
					} else {
						var _t1797 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1797 = 1
						} else {
							var _t1798 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1798 = 1
							} else {
								var _t1799 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1799 = 1
								} else {
									var _t1800 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1800 = 1
									} else {
										var _t1801 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1801 = 1
										} else {
											var _t1802 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1802 = 1
											} else {
												var _t1803 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1803 = 1
												} else {
													var _t1804 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1804 = 1
													} else {
														var _t1805 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1805 = 1
														} else {
															var _t1806 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1806 = 1
															} else {
																_t1806 = -1
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
	prediction1001 := _t1792
	var _t1807 *pb.RelTerm
	if prediction1001 == 1 {
		_t1808 := p.parse_term()
		term1003 := _t1808
		_t1809 := &pb.RelTerm{}
		_t1809.RelTermType = &pb.RelTerm_Term{Term: term1003}
		_t1807 = _t1809
	} else {
		var _t1810 *pb.RelTerm
		if prediction1001 == 0 {
			_t1811 := p.parse_specialized_value()
			specialized_value1002 := _t1811
			_t1812 := &pb.RelTerm{}
			_t1812.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1002}
			_t1810 = _t1812
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1807 = _t1810
	}
	result1005 := _t1807
	p.recordSpan(int(span_start1004), "RelTerm")
	return result1005
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1007 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1813 := p.parse_raw_value()
	raw_value1006 := _t1813
	result1008 := raw_value1006
	p.recordSpan(int(span_start1007), "Value")
	return result1008
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1814 := p.parse_name()
	name1009 := _t1814
	xs1010 := []*pb.RelTerm{}
	cond1011 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1011 {
		_t1815 := p.parse_rel_term()
		item1012 := _t1815
		xs1010 = append(xs1010, item1012)
		cond1011 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1013 := xs1010
	p.consumeLiteral(")")
	_t1816 := &pb.RelAtom{Name: name1009, Terms: rel_terms1013}
	result1015 := _t1816
	p.recordSpan(int(span_start1014), "RelAtom")
	return result1015
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1817 := p.parse_term()
	term1016 := _t1817
	_t1818 := p.parse_term()
	term_31017 := _t1818
	p.consumeLiteral(")")
	_t1819 := &pb.Cast{Input: term1016, Result: term_31017}
	result1019 := _t1819
	p.recordSpan(int(span_start1018), "Cast")
	return result1019
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1020 := []*pb.Attribute{}
	cond1021 := p.matchLookaheadLiteral("(", 0)
	for cond1021 {
		_t1820 := p.parse_attribute()
		item1022 := _t1820
		xs1020 = append(xs1020, item1022)
		cond1021 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1023 := xs1020
	p.consumeLiteral(")")
	return attributes1023
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1029 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1821 := p.parse_name()
	name1024 := _t1821
	xs1025 := []*pb.Value{}
	cond1026 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1026 {
		_t1822 := p.parse_raw_value()
		item1027 := _t1822
		xs1025 = append(xs1025, item1027)
		cond1026 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1028 := xs1025
	p.consumeLiteral(")")
	_t1823 := &pb.Attribute{Name: name1024, Args: raw_values1028}
	result1030 := _t1823
	p.recordSpan(int(span_start1029), "Attribute")
	return result1030
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1037 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1031 := []*pb.RelationId{}
	cond1032 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1032 {
		_t1824 := p.parse_relation_id()
		item1033 := _t1824
		xs1031 = append(xs1031, item1033)
		cond1032 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1034 := xs1031
	_t1825 := p.parse_script()
	script1035 := _t1825
	var _t1826 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1827 := p.parse_attrs()
		_t1826 = _t1827
	}
	attrs1036 := _t1826
	p.consumeLiteral(")")
	_t1828 := attrs1036
	if attrs1036 == nil {
		_t1828 = []*pb.Attribute{}
	}
	_t1829 := &pb.Algorithm{Global: relation_ids1034, Body: script1035, Attrs: _t1828}
	result1038 := _t1829
	p.recordSpan(int(span_start1037), "Algorithm")
	return result1038
}

func (p *Parser) parse_script() *pb.Script {
	span_start1043 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1039 := []*pb.Construct{}
	cond1040 := p.matchLookaheadLiteral("(", 0)
	for cond1040 {
		_t1830 := p.parse_construct()
		item1041 := _t1830
		xs1039 = append(xs1039, item1041)
		cond1040 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1042 := xs1039
	p.consumeLiteral(")")
	_t1831 := &pb.Script{Constructs: constructs1042}
	result1044 := _t1831
	p.recordSpan(int(span_start1043), "Script")
	return result1044
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1048 := int64(p.spanStart())
	var _t1832 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1833 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1833 = 1
		} else {
			var _t1834 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1834 = 1
			} else {
				var _t1835 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1835 = 1
				} else {
					var _t1836 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1836 = 0
					} else {
						var _t1837 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1837 = 1
						} else {
							var _t1838 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1838 = 1
							} else {
								_t1838 = -1
							}
							_t1837 = _t1838
						}
						_t1836 = _t1837
					}
					_t1835 = _t1836
				}
				_t1834 = _t1835
			}
			_t1833 = _t1834
		}
		_t1832 = _t1833
	} else {
		_t1832 = -1
	}
	prediction1045 := _t1832
	var _t1839 *pb.Construct
	if prediction1045 == 1 {
		_t1840 := p.parse_instruction()
		instruction1047 := _t1840
		_t1841 := &pb.Construct{}
		_t1841.ConstructType = &pb.Construct_Instruction{Instruction: instruction1047}
		_t1839 = _t1841
	} else {
		var _t1842 *pb.Construct
		if prediction1045 == 0 {
			_t1843 := p.parse_loop()
			loop1046 := _t1843
			_t1844 := &pb.Construct{}
			_t1844.ConstructType = &pb.Construct_Loop{Loop: loop1046}
			_t1842 = _t1844
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1839 = _t1842
	}
	result1049 := _t1839
	p.recordSpan(int(span_start1048), "Construct")
	return result1049
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1845 := p.parse_init()
	init1050 := _t1845
	_t1846 := p.parse_script()
	script1051 := _t1846
	var _t1847 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1848 := p.parse_attrs()
		_t1847 = _t1848
	}
	attrs1052 := _t1847
	p.consumeLiteral(")")
	_t1849 := attrs1052
	if attrs1052 == nil {
		_t1849 = []*pb.Attribute{}
	}
	_t1850 := &pb.Loop{Init: init1050, Body: script1051, Attrs: _t1849}
	result1054 := _t1850
	p.recordSpan(int(span_start1053), "Loop")
	return result1054
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1055 := []*pb.Instruction{}
	cond1056 := p.matchLookaheadLiteral("(", 0)
	for cond1056 {
		_t1851 := p.parse_instruction()
		item1057 := _t1851
		xs1055 = append(xs1055, item1057)
		cond1056 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1058 := xs1055
	p.consumeLiteral(")")
	return instructions1058
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1065 := int64(p.spanStart())
	var _t1852 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1853 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1853 = 1
		} else {
			var _t1854 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1854 = 4
			} else {
				var _t1855 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1855 = 3
				} else {
					var _t1856 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1856 = 2
					} else {
						var _t1857 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1857 = 0
						} else {
							_t1857 = -1
						}
						_t1856 = _t1857
					}
					_t1855 = _t1856
				}
				_t1854 = _t1855
			}
			_t1853 = _t1854
		}
		_t1852 = _t1853
	} else {
		_t1852 = -1
	}
	prediction1059 := _t1852
	var _t1858 *pb.Instruction
	if prediction1059 == 4 {
		_t1859 := p.parse_monus_def()
		monus_def1064 := _t1859
		_t1860 := &pb.Instruction{}
		_t1860.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1064}
		_t1858 = _t1860
	} else {
		var _t1861 *pb.Instruction
		if prediction1059 == 3 {
			_t1862 := p.parse_monoid_def()
			monoid_def1063 := _t1862
			_t1863 := &pb.Instruction{}
			_t1863.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1063}
			_t1861 = _t1863
		} else {
			var _t1864 *pb.Instruction
			if prediction1059 == 2 {
				_t1865 := p.parse_break()
				break1062 := _t1865
				_t1866 := &pb.Instruction{}
				_t1866.InstrType = &pb.Instruction_Break{Break: break1062}
				_t1864 = _t1866
			} else {
				var _t1867 *pb.Instruction
				if prediction1059 == 1 {
					_t1868 := p.parse_upsert()
					upsert1061 := _t1868
					_t1869 := &pb.Instruction{}
					_t1869.InstrType = &pb.Instruction_Upsert{Upsert: upsert1061}
					_t1867 = _t1869
				} else {
					var _t1870 *pb.Instruction
					if prediction1059 == 0 {
						_t1871 := p.parse_assign()
						assign1060 := _t1871
						_t1872 := &pb.Instruction{}
						_t1872.InstrType = &pb.Instruction_Assign{Assign: assign1060}
						_t1870 = _t1872
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1867 = _t1870
				}
				_t1864 = _t1867
			}
			_t1861 = _t1864
		}
		_t1858 = _t1861
	}
	result1066 := _t1858
	p.recordSpan(int(span_start1065), "Instruction")
	return result1066
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1070 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1873 := p.parse_relation_id()
	relation_id1067 := _t1873
	_t1874 := p.parse_abstraction()
	abstraction1068 := _t1874
	var _t1875 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1876 := p.parse_attrs()
		_t1875 = _t1876
	}
	attrs1069 := _t1875
	p.consumeLiteral(")")
	_t1877 := attrs1069
	if attrs1069 == nil {
		_t1877 = []*pb.Attribute{}
	}
	_t1878 := &pb.Assign{Name: relation_id1067, Body: abstraction1068, Attrs: _t1877}
	result1071 := _t1878
	p.recordSpan(int(span_start1070), "Assign")
	return result1071
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1075 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1879 := p.parse_relation_id()
	relation_id1072 := _t1879
	_t1880 := p.parse_abstraction_with_arity()
	abstraction_with_arity1073 := _t1880
	var _t1881 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1882 := p.parse_attrs()
		_t1881 = _t1882
	}
	attrs1074 := _t1881
	p.consumeLiteral(")")
	_t1883 := attrs1074
	if attrs1074 == nil {
		_t1883 = []*pb.Attribute{}
	}
	_t1884 := &pb.Upsert{Name: relation_id1072, Body: abstraction_with_arity1073[0].(*pb.Abstraction), Attrs: _t1883, ValueArity: abstraction_with_arity1073[1].(int64)}
	result1076 := _t1884
	p.recordSpan(int(span_start1075), "Upsert")
	return result1076
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1885 := p.parse_bindings()
	bindings1077 := _t1885
	_t1886 := p.parse_formula()
	formula1078 := _t1886
	p.consumeLiteral(")")
	_t1887 := &pb.Abstraction{Vars: listConcat(bindings1077[0].([]*pb.Binding), bindings1077[1].([]*pb.Binding)), Value: formula1078}
	return []interface{}{_t1887, int64(len(bindings1077[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1888 := p.parse_relation_id()
	relation_id1079 := _t1888
	_t1889 := p.parse_abstraction()
	abstraction1080 := _t1889
	var _t1890 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1891 := p.parse_attrs()
		_t1890 = _t1891
	}
	attrs1081 := _t1890
	p.consumeLiteral(")")
	_t1892 := attrs1081
	if attrs1081 == nil {
		_t1892 = []*pb.Attribute{}
	}
	_t1893 := &pb.Break{Name: relation_id1079, Body: abstraction1080, Attrs: _t1892}
	result1083 := _t1893
	p.recordSpan(int(span_start1082), "Break")
	return result1083
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1894 := p.parse_monoid()
	monoid1084 := _t1894
	_t1895 := p.parse_relation_id()
	relation_id1085 := _t1895
	_t1896 := p.parse_abstraction_with_arity()
	abstraction_with_arity1086 := _t1896
	var _t1897 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1898 := p.parse_attrs()
		_t1897 = _t1898
	}
	attrs1087 := _t1897
	p.consumeLiteral(")")
	_t1899 := attrs1087
	if attrs1087 == nil {
		_t1899 = []*pb.Attribute{}
	}
	_t1900 := &pb.MonoidDef{Monoid: monoid1084, Name: relation_id1085, Body: abstraction_with_arity1086[0].(*pb.Abstraction), Attrs: _t1899, ValueArity: abstraction_with_arity1086[1].(int64)}
	result1089 := _t1900
	p.recordSpan(int(span_start1088), "MonoidDef")
	return result1089
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1095 := int64(p.spanStart())
	var _t1901 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1902 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1902 = 3
		} else {
			var _t1903 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1903 = 0
			} else {
				var _t1904 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1904 = 1
				} else {
					var _t1905 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1905 = 2
					} else {
						_t1905 = -1
					}
					_t1904 = _t1905
				}
				_t1903 = _t1904
			}
			_t1902 = _t1903
		}
		_t1901 = _t1902
	} else {
		_t1901 = -1
	}
	prediction1090 := _t1901
	var _t1906 *pb.Monoid
	if prediction1090 == 3 {
		_t1907 := p.parse_sum_monoid()
		sum_monoid1094 := _t1907
		_t1908 := &pb.Monoid{}
		_t1908.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1094}
		_t1906 = _t1908
	} else {
		var _t1909 *pb.Monoid
		if prediction1090 == 2 {
			_t1910 := p.parse_max_monoid()
			max_monoid1093 := _t1910
			_t1911 := &pb.Monoid{}
			_t1911.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1093}
			_t1909 = _t1911
		} else {
			var _t1912 *pb.Monoid
			if prediction1090 == 1 {
				_t1913 := p.parse_min_monoid()
				min_monoid1092 := _t1913
				_t1914 := &pb.Monoid{}
				_t1914.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1092}
				_t1912 = _t1914
			} else {
				var _t1915 *pb.Monoid
				if prediction1090 == 0 {
					_t1916 := p.parse_or_monoid()
					or_monoid1091 := _t1916
					_t1917 := &pb.Monoid{}
					_t1917.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1091}
					_t1915 = _t1917
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1912 = _t1915
			}
			_t1909 = _t1912
		}
		_t1906 = _t1909
	}
	result1096 := _t1906
	p.recordSpan(int(span_start1095), "Monoid")
	return result1096
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1918 := &pb.OrMonoid{}
	result1098 := _t1918
	p.recordSpan(int(span_start1097), "OrMonoid")
	return result1098
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1919 := p.parse_type()
	type1099 := _t1919
	p.consumeLiteral(")")
	_t1920 := &pb.MinMonoid{Type: type1099}
	result1101 := _t1920
	p.recordSpan(int(span_start1100), "MinMonoid")
	return result1101
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1921 := p.parse_type()
	type1102 := _t1921
	p.consumeLiteral(")")
	_t1922 := &pb.MaxMonoid{Type: type1102}
	result1104 := _t1922
	p.recordSpan(int(span_start1103), "MaxMonoid")
	return result1104
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1106 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1923 := p.parse_type()
	type1105 := _t1923
	p.consumeLiteral(")")
	_t1924 := &pb.SumMonoid{Type: type1105}
	result1107 := _t1924
	p.recordSpan(int(span_start1106), "SumMonoid")
	return result1107
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1925 := p.parse_monoid()
	monoid1108 := _t1925
	_t1926 := p.parse_relation_id()
	relation_id1109 := _t1926
	_t1927 := p.parse_abstraction_with_arity()
	abstraction_with_arity1110 := _t1927
	var _t1928 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1929 := p.parse_attrs()
		_t1928 = _t1929
	}
	attrs1111 := _t1928
	p.consumeLiteral(")")
	_t1930 := attrs1111
	if attrs1111 == nil {
		_t1930 = []*pb.Attribute{}
	}
	_t1931 := &pb.MonusDef{Monoid: monoid1108, Name: relation_id1109, Body: abstraction_with_arity1110[0].(*pb.Abstraction), Attrs: _t1930, ValueArity: abstraction_with_arity1110[1].(int64)}
	result1113 := _t1931
	p.recordSpan(int(span_start1112), "MonusDef")
	return result1113
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1118 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1932 := p.parse_relation_id()
	relation_id1114 := _t1932
	_t1933 := p.parse_abstraction()
	abstraction1115 := _t1933
	_t1934 := p.parse_functional_dependency_keys()
	functional_dependency_keys1116 := _t1934
	_t1935 := p.parse_functional_dependency_values()
	functional_dependency_values1117 := _t1935
	p.consumeLiteral(")")
	_t1936 := &pb.FunctionalDependency{Guard: abstraction1115, Keys: functional_dependency_keys1116, Values: functional_dependency_values1117}
	_t1937 := &pb.Constraint{Name: relation_id1114}
	_t1937.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1936}
	result1119 := _t1937
	p.recordSpan(int(span_start1118), "Constraint")
	return result1119
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1120 := []*pb.Var{}
	cond1121 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1121 {
		_t1938 := p.parse_var()
		item1122 := _t1938
		xs1120 = append(xs1120, item1122)
		cond1121 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1123 := xs1120
	p.consumeLiteral(")")
	return vars1123
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1124 := []*pb.Var{}
	cond1125 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1125 {
		_t1939 := p.parse_var()
		item1126 := _t1939
		xs1124 = append(xs1124, item1126)
		cond1125 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1127 := xs1124
	p.consumeLiteral(")")
	return vars1127
}

func (p *Parser) parse_data() *pb.Data {
	span_start1133 := int64(p.spanStart())
	var _t1940 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1941 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1941 = 3
		} else {
			var _t1942 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1942 = 0
			} else {
				var _t1943 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1943 = 2
				} else {
					var _t1944 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1944 = 1
					} else {
						_t1944 = -1
					}
					_t1943 = _t1944
				}
				_t1942 = _t1943
			}
			_t1941 = _t1942
		}
		_t1940 = _t1941
	} else {
		_t1940 = -1
	}
	prediction1128 := _t1940
	var _t1945 *pb.Data
	if prediction1128 == 3 {
		_t1946 := p.parse_iceberg_data()
		iceberg_data1132 := _t1946
		_t1947 := &pb.Data{}
		_t1947.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1132}
		_t1945 = _t1947
	} else {
		var _t1948 *pb.Data
		if prediction1128 == 2 {
			_t1949 := p.parse_csv_data()
			csv_data1131 := _t1949
			_t1950 := &pb.Data{}
			_t1950.DataType = &pb.Data_CsvData{CsvData: csv_data1131}
			_t1948 = _t1950
		} else {
			var _t1951 *pb.Data
			if prediction1128 == 1 {
				_t1952 := p.parse_betree_relation()
				betree_relation1130 := _t1952
				_t1953 := &pb.Data{}
				_t1953.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1130}
				_t1951 = _t1953
			} else {
				var _t1954 *pb.Data
				if prediction1128 == 0 {
					_t1955 := p.parse_edb()
					edb1129 := _t1955
					_t1956 := &pb.Data{}
					_t1956.DataType = &pb.Data_Edb{Edb: edb1129}
					_t1954 = _t1956
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1951 = _t1954
			}
			_t1948 = _t1951
		}
		_t1945 = _t1948
	}
	result1134 := _t1945
	p.recordSpan(int(span_start1133), "Data")
	return result1134
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1957 := p.parse_relation_id()
	relation_id1135 := _t1957
	_t1958 := p.parse_edb_path()
	edb_path1136 := _t1958
	_t1959 := p.parse_edb_types()
	edb_types1137 := _t1959
	p.consumeLiteral(")")
	_t1960 := &pb.EDB{TargetId: relation_id1135, Path: edb_path1136, Types: edb_types1137}
	result1139 := _t1960
	p.recordSpan(int(span_start1138), "EDB")
	return result1139
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1140 := []string{}
	cond1141 := p.matchLookaheadTerminal("STRING", 0)
	for cond1141 {
		item1142 := p.consumeTerminal("STRING").Value.str
		xs1140 = append(xs1140, item1142)
		cond1141 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1143 := xs1140
	p.consumeLiteral("]")
	return strings1143
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1144 := []*pb.Type{}
	cond1145 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1145 {
		_t1961 := p.parse_type()
		item1146 := _t1961
		xs1144 = append(xs1144, item1146)
		cond1145 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1147 := xs1144
	p.consumeLiteral("]")
	return types1147
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1962 := p.parse_relation_id()
	relation_id1148 := _t1962
	_t1963 := p.parse_betree_info()
	betree_info1149 := _t1963
	p.consumeLiteral(")")
	_t1964 := &pb.BeTreeRelation{Name: relation_id1148, RelationInfo: betree_info1149}
	result1151 := _t1964
	p.recordSpan(int(span_start1150), "BeTreeRelation")
	return result1151
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1965 := p.parse_betree_info_key_types()
	betree_info_key_types1152 := _t1965
	_t1966 := p.parse_betree_info_value_types()
	betree_info_value_types1153 := _t1966
	_t1967 := p.parse_config_dict()
	config_dict1154 := _t1967
	p.consumeLiteral(")")
	_t1968 := p.construct_betree_info(betree_info_key_types1152, betree_info_value_types1153, config_dict1154)
	result1156 := _t1968
	p.recordSpan(int(span_start1155), "BeTreeInfo")
	return result1156
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1157 := []*pb.Type{}
	cond1158 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1158 {
		_t1969 := p.parse_type()
		item1159 := _t1969
		xs1157 = append(xs1157, item1159)
		cond1158 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1160 := xs1157
	p.consumeLiteral(")")
	return types1160
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1161 := []*pb.Type{}
	cond1162 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1162 {
		_t1970 := p.parse_type()
		item1163 := _t1970
		xs1161 = append(xs1161, item1163)
		cond1162 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1164 := xs1161
	p.consumeLiteral(")")
	return types1164
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1169 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1971 := p.parse_csvlocator()
	csvlocator1165 := _t1971
	_t1972 := p.parse_csv_config()
	csv_config1166 := _t1972
	_t1973 := p.parse_gnf_columns()
	gnf_columns1167 := _t1973
	_t1974 := p.parse_csv_asof()
	csv_asof1168 := _t1974
	p.consumeLiteral(")")
	_t1975 := &pb.CSVData{Locator: csvlocator1165, Config: csv_config1166, Columns: gnf_columns1167, Asof: csv_asof1168}
	result1170 := _t1975
	p.recordSpan(int(span_start1169), "CSVData")
	return result1170
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1173 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1976 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1977 := p.parse_csv_locator_paths()
		_t1976 = _t1977
	}
	csv_locator_paths1171 := _t1976
	var _t1978 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1979 := p.parse_csv_locator_inline_data()
		_t1978 = ptr(_t1979)
	}
	csv_locator_inline_data1172 := _t1978
	p.consumeLiteral(")")
	_t1980 := csv_locator_paths1171
	if csv_locator_paths1171 == nil {
		_t1980 = []string{}
	}
	_t1981 := &pb.CSVLocator{Paths: _t1980, InlineData: []byte(deref(csv_locator_inline_data1172, ""))}
	result1174 := _t1981
	p.recordSpan(int(span_start1173), "CSVLocator")
	return result1174
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1175 := []string{}
	cond1176 := p.matchLookaheadTerminal("STRING", 0)
	for cond1176 {
		item1177 := p.consumeTerminal("STRING").Value.str
		xs1175 = append(xs1175, item1177)
		cond1176 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1178 := xs1175
	p.consumeLiteral(")")
	return strings1178
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1179 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1179
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1182 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1982 := p.parse_config_dict()
	config_dict1180 := _t1982
	var _t1983 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1984 := p.parse__storage_integration()
		_t1983 = _t1984
	}
	_storage_integration1181 := _t1983
	p.consumeLiteral(")")
	_t1985 := p.construct_csv_config(config_dict1180, _storage_integration1181)
	result1183 := _t1985
	p.recordSpan(int(span_start1182), "CSVConfig")
	return result1183
}

func (p *Parser) parse__storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t1986 := p.parse_config_dict()
	config_dict1184 := _t1986
	p.consumeLiteral(")")
	return config_dict1184
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1185 := []*pb.GNFColumn{}
	cond1186 := p.matchLookaheadLiteral("(", 0)
	for cond1186 {
		_t1987 := p.parse_gnf_column()
		item1187 := _t1987
		xs1185 = append(xs1185, item1187)
		cond1186 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1188 := xs1185
	p.consumeLiteral(")")
	return gnf_columns1188
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1195 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1988 := p.parse_gnf_column_path()
	gnf_column_path1189 := _t1988
	var _t1989 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1990 := p.parse_relation_id()
		_t1989 = _t1990
	}
	relation_id1190 := _t1989
	p.consumeLiteral("[")
	xs1191 := []*pb.Type{}
	cond1192 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1192 {
		_t1991 := p.parse_type()
		item1193 := _t1991
		xs1191 = append(xs1191, item1193)
		cond1192 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1194 := xs1191
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1992 := &pb.GNFColumn{ColumnPath: gnf_column_path1189, TargetId: relation_id1190, Types: types1194}
	result1196 := _t1992
	p.recordSpan(int(span_start1195), "GNFColumn")
	return result1196
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1993 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1993 = 1
	} else {
		var _t1994 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1994 = 0
		} else {
			_t1994 = -1
		}
		_t1993 = _t1994
	}
	prediction1197 := _t1993
	var _t1995 []string
	if prediction1197 == 1 {
		p.consumeLiteral("[")
		xs1199 := []string{}
		cond1200 := p.matchLookaheadTerminal("STRING", 0)
		for cond1200 {
			item1201 := p.consumeTerminal("STRING").Value.str
			xs1199 = append(xs1199, item1201)
			cond1200 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1202 := xs1199
		p.consumeLiteral("]")
		_t1995 = strings1202
	} else {
		var _t1996 []string
		if prediction1197 == 0 {
			string1198 := p.consumeTerminal("STRING").Value.str
			_ = string1198
			_t1996 = []string{string1198}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1995 = _t1996
	}
	return _t1995
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1203 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1203
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1210 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1997 := p.parse_iceberg_locator()
	iceberg_locator1204 := _t1997
	_t1998 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1205 := _t1998
	_t1999 := p.parse_gnf_columns()
	gnf_columns1206 := _t1999
	var _t2000 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2001 := p.parse_iceberg_from_snapshot()
		_t2000 = ptr(_t2001)
	}
	iceberg_from_snapshot1207 := _t2000
	var _t2002 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2003 := p.parse_iceberg_to_snapshot()
		_t2002 = ptr(_t2003)
	}
	iceberg_to_snapshot1208 := _t2002
	_t2004 := p.parse_boolean_value()
	boolean_value1209 := _t2004
	p.consumeLiteral(")")
	_t2005 := p.construct_iceberg_data(iceberg_locator1204, iceberg_catalog_config1205, gnf_columns1206, iceberg_from_snapshot1207, iceberg_to_snapshot1208, boolean_value1209)
	result1211 := _t2005
	p.recordSpan(int(span_start1210), "IcebergData")
	return result1211
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1215 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2006 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1212 := _t2006
	_t2007 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1213 := _t2007
	_t2008 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1214 := _t2008
	p.consumeLiteral(")")
	_t2009 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1212, Namespace: iceberg_locator_namespace1213, Warehouse: iceberg_locator_warehouse1214}
	result1216 := _t2009
	p.recordSpan(int(span_start1215), "IcebergLocator")
	return result1216
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1217 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1217
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
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

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1222 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1222
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1227 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2010 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1223 := _t2010
	var _t2011 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2012 := p.parse_iceberg_catalog_config_scope()
		_t2011 = ptr(_t2012)
	}
	iceberg_catalog_config_scope1224 := _t2011
	_t2013 := p.parse_iceberg_properties()
	iceberg_properties1225 := _t2013
	_t2014 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1226 := _t2014
	p.consumeLiteral(")")
	_t2015 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1223, iceberg_catalog_config_scope1224, iceberg_properties1225, iceberg_auth_properties1226)
	result1228 := _t2015
	p.recordSpan(int(span_start1227), "IcebergCatalogConfig")
	return result1228
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1229 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1229
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1230 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1230
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1231 := [][]interface{}{}
	cond1232 := p.matchLookaheadLiteral("(", 0)
	for cond1232 {
		_t2016 := p.parse_iceberg_property_entry()
		item1233 := _t2016
		xs1231 = append(xs1231, item1233)
		cond1232 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1234 := xs1231
	p.consumeLiteral(")")
	return iceberg_property_entrys1234
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1235 := p.consumeTerminal("STRING").Value.str
	string_31236 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1235, string_31236}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1237 := [][]interface{}{}
	cond1238 := p.matchLookaheadLiteral("(", 0)
	for cond1238 {
		_t2017 := p.parse_iceberg_masked_property_entry()
		item1239 := _t2017
		xs1237 = append(xs1237, item1239)
		cond1238 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1240 := xs1237
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1240
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1241 := p.consumeTerminal("STRING").Value.str
	string_31242 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1241, string_31242}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1243 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1243
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1244 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1244
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1246 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2018 := p.parse_fragment_id()
	fragment_id1245 := _t2018
	p.consumeLiteral(")")
	_t2019 := &pb.Undefine{FragmentId: fragment_id1245}
	result1247 := _t2019
	p.recordSpan(int(span_start1246), "Undefine")
	return result1247
}

func (p *Parser) parse_context() *pb.Context {
	span_start1252 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1248 := []*pb.RelationId{}
	cond1249 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1249 {
		_t2020 := p.parse_relation_id()
		item1250 := _t2020
		xs1248 = append(xs1248, item1250)
		cond1249 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1251 := xs1248
	p.consumeLiteral(")")
	_t2021 := &pb.Context{Relations: relation_ids1251}
	result1253 := _t2021
	p.recordSpan(int(span_start1252), "Context")
	return result1253
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1259 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2022 := p.parse_edb_path()
	edb_path1254 := _t2022
	xs1255 := []*pb.SnapshotMapping{}
	cond1256 := p.matchLookaheadLiteral("[", 0)
	for cond1256 {
		_t2023 := p.parse_snapshot_mapping()
		item1257 := _t2023
		xs1255 = append(xs1255, item1257)
		cond1256 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1258 := xs1255
	p.consumeLiteral(")")
	_t2024 := &pb.Snapshot{Prefix: edb_path1254, Mappings: snapshot_mappings1258}
	result1260 := _t2024
	p.recordSpan(int(span_start1259), "Snapshot")
	return result1260
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1263 := int64(p.spanStart())
	_t2025 := p.parse_edb_path()
	edb_path1261 := _t2025
	_t2026 := p.parse_relation_id()
	relation_id1262 := _t2026
	_t2027 := &pb.SnapshotMapping{DestinationPath: edb_path1261, SourceRelation: relation_id1262}
	result1264 := _t2027
	p.recordSpan(int(span_start1263), "SnapshotMapping")
	return result1264
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1265 := []*pb.Read{}
	cond1266 := p.matchLookaheadLiteral("(", 0)
	for cond1266 {
		_t2028 := p.parse_read()
		item1267 := _t2028
		xs1265 = append(xs1265, item1267)
		cond1266 = p.matchLookaheadLiteral("(", 0)
	}
	reads1268 := xs1265
	p.consumeLiteral(")")
	return reads1268
}

func (p *Parser) parse_read() *pb.Read {
	span_start1275 := int64(p.spanStart())
	var _t2029 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2030 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2030 = 2
		} else {
			var _t2031 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2031 = 1
			} else {
				var _t2032 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2032 = 4
				} else {
					var _t2033 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2033 = 4
					} else {
						var _t2034 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2034 = 0
						} else {
							var _t2035 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2035 = 3
							} else {
								_t2035 = -1
							}
							_t2034 = _t2035
						}
						_t2033 = _t2034
					}
					_t2032 = _t2033
				}
				_t2031 = _t2032
			}
			_t2030 = _t2031
		}
		_t2029 = _t2030
	} else {
		_t2029 = -1
	}
	prediction1269 := _t2029
	var _t2036 *pb.Read
	if prediction1269 == 4 {
		_t2037 := p.parse_export()
		export1274 := _t2037
		_t2038 := &pb.Read{}
		_t2038.ReadType = &pb.Read_Export{Export: export1274}
		_t2036 = _t2038
	} else {
		var _t2039 *pb.Read
		if prediction1269 == 3 {
			_t2040 := p.parse_abort()
			abort1273 := _t2040
			_t2041 := &pb.Read{}
			_t2041.ReadType = &pb.Read_Abort{Abort: abort1273}
			_t2039 = _t2041
		} else {
			var _t2042 *pb.Read
			if prediction1269 == 2 {
				_t2043 := p.parse_what_if()
				what_if1272 := _t2043
				_t2044 := &pb.Read{}
				_t2044.ReadType = &pb.Read_WhatIf{WhatIf: what_if1272}
				_t2042 = _t2044
			} else {
				var _t2045 *pb.Read
				if prediction1269 == 1 {
					_t2046 := p.parse_output()
					output1271 := _t2046
					_t2047 := &pb.Read{}
					_t2047.ReadType = &pb.Read_Output{Output: output1271}
					_t2045 = _t2047
				} else {
					var _t2048 *pb.Read
					if prediction1269 == 0 {
						_t2049 := p.parse_demand()
						demand1270 := _t2049
						_t2050 := &pb.Read{}
						_t2050.ReadType = &pb.Read_Demand{Demand: demand1270}
						_t2048 = _t2050
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2045 = _t2048
				}
				_t2042 = _t2045
			}
			_t2039 = _t2042
		}
		_t2036 = _t2039
	}
	result1276 := _t2036
	p.recordSpan(int(span_start1275), "Read")
	return result1276
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1278 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2051 := p.parse_relation_id()
	relation_id1277 := _t2051
	p.consumeLiteral(")")
	_t2052 := &pb.Demand{RelationId: relation_id1277}
	result1279 := _t2052
	p.recordSpan(int(span_start1278), "Demand")
	return result1279
}

func (p *Parser) parse_output() *pb.Output {
	span_start1282 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2053 := p.parse_name()
	name1280 := _t2053
	_t2054 := p.parse_relation_id()
	relation_id1281 := _t2054
	p.consumeLiteral(")")
	_t2055 := &pb.Output{Name: name1280, RelationId: relation_id1281}
	result1283 := _t2055
	p.recordSpan(int(span_start1282), "Output")
	return result1283
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1286 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2056 := p.parse_name()
	name1284 := _t2056
	_t2057 := p.parse_epoch()
	epoch1285 := _t2057
	p.consumeLiteral(")")
	_t2058 := &pb.WhatIf{Branch: name1284, Epoch: epoch1285}
	result1287 := _t2058
	p.recordSpan(int(span_start1286), "WhatIf")
	return result1287
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1290 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2059 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2060 := p.parse_name()
		_t2059 = ptr(_t2060)
	}
	name1288 := _t2059
	_t2061 := p.parse_relation_id()
	relation_id1289 := _t2061
	p.consumeLiteral(")")
	_t2062 := &pb.Abort{Name: deref(name1288, "abort"), RelationId: relation_id1289}
	result1291 := _t2062
	p.recordSpan(int(span_start1290), "Abort")
	return result1291
}

func (p *Parser) parse_export() *pb.Export {
	span_start1295 := int64(p.spanStart())
	var _t2063 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2064 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2064 = 1
		} else {
			var _t2065 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2065 = 0
			} else {
				_t2065 = -1
			}
			_t2064 = _t2065
		}
		_t2063 = _t2064
	} else {
		_t2063 = -1
	}
	prediction1292 := _t2063
	var _t2066 *pb.Export
	if prediction1292 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2067 := p.parse_export_iceberg_config()
		export_iceberg_config1294 := _t2067
		p.consumeLiteral(")")
		_t2068 := &pb.Export{}
		_t2068.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1294}
		_t2066 = _t2068
	} else {
		var _t2069 *pb.Export
		if prediction1292 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2070 := p.parse_export_csv_config()
			export_csv_config1293 := _t2070
			p.consumeLiteral(")")
			_t2071 := &pb.Export{}
			_t2071.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1293}
			_t2069 = _t2071
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2066 = _t2069
	}
	result1296 := _t2066
	p.recordSpan(int(span_start1295), "Export")
	return result1296
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1304 := int64(p.spanStart())
	var _t2072 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2073 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2073 = 0
		} else {
			var _t2074 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2074 = 1
			} else {
				_t2074 = -1
			}
			_t2073 = _t2074
		}
		_t2072 = _t2073
	} else {
		_t2072 = -1
	}
	prediction1297 := _t2072
	var _t2075 *pb.ExportCSVConfig
	if prediction1297 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2076 := p.parse_export_csv_path()
		export_csv_path1301 := _t2076
		_t2077 := p.parse_export_csv_columns_list()
		export_csv_columns_list1302 := _t2077
		_t2078 := p.parse_config_dict()
		config_dict1303 := _t2078
		p.consumeLiteral(")")
		_t2079 := p.construct_export_csv_config(export_csv_path1301, export_csv_columns_list1302, config_dict1303)
		_t2075 = _t2079
	} else {
		var _t2080 *pb.ExportCSVConfig
		if prediction1297 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2081 := p.parse_export_csv_output_location()
			export_csv_output_location1298 := _t2081
			_t2082 := p.parse_export_csv_source()
			export_csv_source1299 := _t2082
			_t2083 := p.parse_csv_config()
			csv_config1300 := _t2083
			p.consumeLiteral(")")
			_t2084 := p.construct_export_csv_config_with_location(export_csv_output_location1298, export_csv_source1299, csv_config1300)
			_t2080 = _t2084
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2075 = _t2080
	}
	result1305 := _t2075
	p.recordSpan(int(span_start1304), "ExportCSVConfig")
	return result1305
}

func (p *Parser) parse_export_csv_output_location() []interface{} {
	var _t2085 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2086 int64
		if p.matchLookaheadLiteral("transaction_output_name", 1) {
			_t2086 = 1
		} else {
			var _t2087 int64
			if p.matchLookaheadLiteral("path", 1) {
				_t2087 = 0
			} else {
				_t2087 = -1
			}
			_t2086 = _t2087
		}
		_t2085 = _t2086
	} else {
		_t2085 = -1
	}
	prediction1306 := _t2085
	var _t2088 []interface{}
	if prediction1306 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("transaction_output_name")
		_t2089 := p.parse_name()
		name1308 := _t2089
		p.consumeLiteral(")")
		_t2088 = []interface{}{"", name1308}
	} else {
		var _t2090 []interface{}
		if prediction1306 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("path")
			string1307 := p.consumeTerminal("STRING").Value.str
			p.consumeLiteral(")")
			_t2090 = []interface{}{string1307, ""}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_output_location", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2088 = _t2090
	}
	return _t2088
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1315 := int64(p.spanStart())
	var _t2091 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2092 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2092 = 1
		} else {
			var _t2093 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2093 = 0
			} else {
				_t2093 = -1
			}
			_t2092 = _t2093
		}
		_t2091 = _t2092
	} else {
		_t2091 = -1
	}
	prediction1309 := _t2091
	var _t2094 *pb.ExportCSVSource
	if prediction1309 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2095 := p.parse_relation_id()
		relation_id1314 := _t2095
		p.consumeLiteral(")")
		_t2096 := &pb.ExportCSVSource{}
		_t2096.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1314}
		_t2094 = _t2096
	} else {
		var _t2097 *pb.ExportCSVSource
		if prediction1309 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1310 := []*pb.ExportCSVColumn{}
			cond1311 := p.matchLookaheadLiteral("(", 0)
			for cond1311 {
				_t2098 := p.parse_export_csv_column()
				item1312 := _t2098
				xs1310 = append(xs1310, item1312)
				cond1311 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1313 := xs1310
			p.consumeLiteral(")")
			_t2099 := &pb.ExportCSVColumns{Columns: export_csv_columns1313}
			_t2100 := &pb.ExportCSVSource{}
			_t2100.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2099}
			_t2097 = _t2100
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2094 = _t2097
	}
	result1316 := _t2094
	p.recordSpan(int(span_start1315), "ExportCSVSource")
	return result1316
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1319 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1317 := p.consumeTerminal("STRING").Value.str
	_t2101 := p.parse_relation_id()
	relation_id1318 := _t2101
	p.consumeLiteral(")")
	_t2102 := &pb.ExportCSVColumn{ColumnName: string1317, ColumnData: relation_id1318}
	result1320 := _t2102
	p.recordSpan(int(span_start1319), "ExportCSVColumn")
	return result1320
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1321 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1321
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1322 := []*pb.ExportCSVColumn{}
	cond1323 := p.matchLookaheadLiteral("(", 0)
	for cond1323 {
		_t2103 := p.parse_export_csv_column()
		item1324 := _t2103
		xs1322 = append(xs1322, item1324)
		cond1323 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1325 := xs1322
	p.consumeLiteral(")")
	return export_csv_columns1325
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1331 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2104 := p.parse_iceberg_locator()
	iceberg_locator1326 := _t2104
	_t2105 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1327 := _t2105
	_t2106 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1328 := _t2106
	_t2107 := p.parse_iceberg_table_properties()
	iceberg_table_properties1329 := _t2107
	var _t2108 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2109 := p.parse_config_dict()
		_t2108 = _t2109
	}
	config_dict1330 := _t2108
	p.consumeLiteral(")")
	_t2110 := p.construct_export_iceberg_config_full(iceberg_locator1326, iceberg_catalog_config1327, export_iceberg_table_def1328, iceberg_table_properties1329, config_dict1330)
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

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1336 := [][]interface{}{}
	cond1337 := p.matchLookaheadLiteral("(", 0)
	for cond1337 {
		_t2112 := p.parse_iceberg_property_entry()
		item1338 := _t2112
		xs1336 = append(xs1336, item1338)
		cond1337 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1339 := xs1336
	p.consumeLiteral(")")
	return iceberg_property_entrys1339
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
