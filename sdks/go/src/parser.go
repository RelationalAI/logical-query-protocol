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
	var _t2124 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2124
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2125 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2125
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2126 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2126
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2127 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2127
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2128 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2128
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2129 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2129
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2130 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2130
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2131 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2131
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2132 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2132
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2133 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2133
	_t2134 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2134
	_t2135 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2135
	_t2136 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2136
	_t2137 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2137
	_t2138 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2138
	_t2139 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2139
	_t2140 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2140
	_t2141 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2141
	_t2142 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2142
	_t2143 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2143
	_t2144 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2144
	_t2145 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2145
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2146 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2146
	_t2147 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2147
	_t2148 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2148
	_t2149 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2149
	_t2150 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2150
	_t2151 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2151
	_t2152 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2152
	_t2153 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2153
	_t2154 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2154
	_t2155 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2155.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2155.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2155
	_t2156 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2156
}

func (p *Parser) default_configure() *pb.Configure {
	_t2157 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2157
	_t2158 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2158
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
	_t2159 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2159
	_t2160 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2160
	_t2161 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2161
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2162 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2162
	_t2163 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2163
	_t2164 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2164
	_t2165 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2165
	_t2166 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2166
	_t2167 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2167
	_t2168 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2168
	_t2169 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2169
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2170 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2170
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2171 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2171
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2172 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2172
}

func (p *Parser) construct_csv_data(locator *pb.CSVLocator, config *pb.CSVConfig, columns_opt []*pb.GNFColumn, target_opt *pb.CSVTarget, asof string) *pb.CSVData {
	_t2173 := columns_opt
	if columns_opt == nil {
		_t2173 = []*pb.GNFColumn{}
	}
	_t2174 := &pb.CSVData{Locator: locator, Config: config, Columns: _t2173, Asof: asof, Target: target_opt}
	return _t2174
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2175 := config_dict
	if config_dict == nil {
		_t2175 = [][]interface{}{}
	}
	cfg := dictFromList(_t2175)
	_t2176 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2176
	_t2177 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2177
	_t2178 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2178
	table_props := stringMapFromPairs(table_property_pairs)
	_t2179 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2179
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start683 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1354 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1355 := p.parse_configure()
		_t1354 = _t1355
	}
	configure677 := _t1354
	var _t1356 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1357 := p.parse_sync()
		_t1356 = _t1357
	}
	sync678 := _t1356
	xs679 := []*pb.Epoch{}
	cond680 := p.matchLookaheadLiteral("(", 0)
	for cond680 {
		_t1358 := p.parse_epoch()
		item681 := _t1358
		xs679 = append(xs679, item681)
		cond680 = p.matchLookaheadLiteral("(", 0)
	}
	epochs682 := xs679
	p.consumeLiteral(")")
	_t1359 := p.default_configure()
	_t1360 := configure677
	if configure677 == nil {
		_t1360 = _t1359
	}
	_t1361 := &pb.Transaction{Epochs: epochs682, Configure: _t1360, Sync: sync678}
	result684 := _t1361
	p.recordSpan(int(span_start683), "Transaction")
	return result684
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start686 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1362 := p.parse_config_dict()
	config_dict685 := _t1362
	p.consumeLiteral(")")
	_t1363 := p.construct_configure(config_dict685)
	result687 := _t1363
	p.recordSpan(int(span_start686), "Configure")
	return result687
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs688 := [][]interface{}{}
	cond689 := p.matchLookaheadLiteral(":", 0)
	for cond689 {
		_t1364 := p.parse_config_key_value()
		item690 := _t1364
		xs688 = append(xs688, item690)
		cond689 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values691 := xs688
	p.consumeLiteral("}")
	return config_key_values691
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol692 := p.consumeTerminal("SYMBOL").Value.str
	_t1365 := p.parse_raw_value()
	raw_value693 := _t1365
	return []interface{}{symbol692, raw_value693}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start707 := int64(p.spanStart())
	var _t1366 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1366 = 12
	} else {
		var _t1367 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1367 = 11
		} else {
			var _t1368 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1368 = 12
			} else {
				var _t1369 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1370 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1370 = 1
					} else {
						var _t1371 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1371 = 0
						} else {
							_t1371 = -1
						}
						_t1370 = _t1371
					}
					_t1369 = _t1370
				} else {
					var _t1372 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1372 = 7
					} else {
						var _t1373 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1373 = 8
						} else {
							var _t1374 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1374 = 2
							} else {
								var _t1375 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1375 = 3
								} else {
									var _t1376 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1376 = 9
									} else {
										var _t1377 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1377 = 4
										} else {
											var _t1378 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1378 = 5
											} else {
												var _t1379 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1379 = 6
												} else {
													var _t1380 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1380 = 10
													} else {
														_t1380 = -1
													}
													_t1379 = _t1380
												}
												_t1378 = _t1379
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
					_t1369 = _t1372
				}
				_t1368 = _t1369
			}
			_t1367 = _t1368
		}
		_t1366 = _t1367
	}
	prediction694 := _t1366
	var _t1381 *pb.Value
	if prediction694 == 12 {
		_t1382 := p.parse_boolean_value()
		boolean_value706 := _t1382
		_t1383 := &pb.Value{}
		_t1383.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value706}
		_t1381 = _t1383
	} else {
		var _t1384 *pb.Value
		if prediction694 == 11 {
			p.consumeLiteral("missing")
			_t1385 := &pb.MissingValue{}
			_t1386 := &pb.Value{}
			_t1386.Value = &pb.Value_MissingValue{MissingValue: _t1385}
			_t1384 = _t1386
		} else {
			var _t1387 *pb.Value
			if prediction694 == 10 {
				decimal705 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1388 := &pb.Value{}
				_t1388.Value = &pb.Value_DecimalValue{DecimalValue: decimal705}
				_t1387 = _t1388
			} else {
				var _t1389 *pb.Value
				if prediction694 == 9 {
					int128704 := p.consumeTerminal("INT128").Value.int128
					_t1390 := &pb.Value{}
					_t1390.Value = &pb.Value_Int128Value{Int128Value: int128704}
					_t1389 = _t1390
				} else {
					var _t1391 *pb.Value
					if prediction694 == 8 {
						uint128703 := p.consumeTerminal("UINT128").Value.uint128
						_t1392 := &pb.Value{}
						_t1392.Value = &pb.Value_Uint128Value{Uint128Value: uint128703}
						_t1391 = _t1392
					} else {
						var _t1393 *pb.Value
						if prediction694 == 7 {
							uint32702 := p.consumeTerminal("UINT32").Value.u32
							_t1394 := &pb.Value{}
							_t1394.Value = &pb.Value_Uint32Value{Uint32Value: uint32702}
							_t1393 = _t1394
						} else {
							var _t1395 *pb.Value
							if prediction694 == 6 {
								float701 := p.consumeTerminal("FLOAT").Value.f64
								_t1396 := &pb.Value{}
								_t1396.Value = &pb.Value_FloatValue{FloatValue: float701}
								_t1395 = _t1396
							} else {
								var _t1397 *pb.Value
								if prediction694 == 5 {
									float32700 := p.consumeTerminal("FLOAT32").Value.f32
									_t1398 := &pb.Value{}
									_t1398.Value = &pb.Value_Float32Value{Float32Value: float32700}
									_t1397 = _t1398
								} else {
									var _t1399 *pb.Value
									if prediction694 == 4 {
										int699 := p.consumeTerminal("INT").Value.i64
										_t1400 := &pb.Value{}
										_t1400.Value = &pb.Value_IntValue{IntValue: int699}
										_t1399 = _t1400
									} else {
										var _t1401 *pb.Value
										if prediction694 == 3 {
											int32698 := p.consumeTerminal("INT32").Value.i32
											_t1402 := &pb.Value{}
											_t1402.Value = &pb.Value_Int32Value{Int32Value: int32698}
											_t1401 = _t1402
										} else {
											var _t1403 *pb.Value
											if prediction694 == 2 {
												string697 := p.consumeTerminal("STRING").Value.str
												_t1404 := &pb.Value{}
												_t1404.Value = &pb.Value_StringValue{StringValue: string697}
												_t1403 = _t1404
											} else {
												var _t1405 *pb.Value
												if prediction694 == 1 {
													_t1406 := p.parse_raw_datetime()
													raw_datetime696 := _t1406
													_t1407 := &pb.Value{}
													_t1407.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime696}
													_t1405 = _t1407
												} else {
													var _t1408 *pb.Value
													if prediction694 == 0 {
														_t1409 := p.parse_raw_date()
														raw_date695 := _t1409
														_t1410 := &pb.Value{}
														_t1410.Value = &pb.Value_DateValue{DateValue: raw_date695}
														_t1408 = _t1410
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1405 = _t1408
												}
												_t1403 = _t1405
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
			_t1384 = _t1387
		}
		_t1381 = _t1384
	}
	result708 := _t1381
	p.recordSpan(int(span_start707), "Value")
	return result708
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start712 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int709 := p.consumeTerminal("INT").Value.i64
	int_3710 := p.consumeTerminal("INT").Value.i64
	int_4711 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1411 := &pb.DateValue{Year: int32(int709), Month: int32(int_3710), Day: int32(int_4711)}
	result713 := _t1411
	p.recordSpan(int(span_start712), "DateValue")
	return result713
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start721 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int714 := p.consumeTerminal("INT").Value.i64
	int_3715 := p.consumeTerminal("INT").Value.i64
	int_4716 := p.consumeTerminal("INT").Value.i64
	int_5717 := p.consumeTerminal("INT").Value.i64
	int_6718 := p.consumeTerminal("INT").Value.i64
	int_7719 := p.consumeTerminal("INT").Value.i64
	var _t1412 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1412 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8720 := _t1412
	p.consumeLiteral(")")
	_t1413 := &pb.DateTimeValue{Year: int32(int714), Month: int32(int_3715), Day: int32(int_4716), Hour: int32(int_5717), Minute: int32(int_6718), Second: int32(int_7719), Microsecond: int32(deref(int_8720, 0))}
	result722 := _t1413
	p.recordSpan(int(span_start721), "DateTimeValue")
	return result722
}

func (p *Parser) parse_boolean_value() bool {
	var _t1414 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1414 = 0
	} else {
		var _t1415 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1415 = 1
		} else {
			_t1415 = -1
		}
		_t1414 = _t1415
	}
	prediction723 := _t1414
	var _t1416 bool
	if prediction723 == 1 {
		p.consumeLiteral("false")
		_t1416 = false
	} else {
		var _t1417 bool
		if prediction723 == 0 {
			p.consumeLiteral("true")
			_t1417 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1416 = _t1417
	}
	return _t1416
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start728 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs724 := []*pb.FragmentId{}
	cond725 := p.matchLookaheadLiteral(":", 0)
	for cond725 {
		_t1418 := p.parse_fragment_id()
		item726 := _t1418
		xs724 = append(xs724, item726)
		cond725 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids727 := xs724
	p.consumeLiteral(")")
	_t1419 := &pb.Sync{Fragments: fragment_ids727}
	result729 := _t1419
	p.recordSpan(int(span_start728), "Sync")
	return result729
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol730 := p.consumeTerminal("SYMBOL").Value.str
	result732 := &pb.FragmentId{Id: []byte(symbol730)}
	p.recordSpan(int(span_start731), "FragmentId")
	return result732
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1420 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1421 := p.parse_epoch_writes()
		_t1420 = _t1421
	}
	epoch_writes733 := _t1420
	var _t1422 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1423 := p.parse_epoch_reads()
		_t1422 = _t1423
	}
	epoch_reads734 := _t1422
	p.consumeLiteral(")")
	_t1424 := epoch_writes733
	if epoch_writes733 == nil {
		_t1424 = []*pb.Write{}
	}
	_t1425 := epoch_reads734
	if epoch_reads734 == nil {
		_t1425 = []*pb.Read{}
	}
	_t1426 := &pb.Epoch{Writes: _t1424, Reads: _t1425}
	result736 := _t1426
	p.recordSpan(int(span_start735), "Epoch")
	return result736
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs737 := []*pb.Write{}
	cond738 := p.matchLookaheadLiteral("(", 0)
	for cond738 {
		_t1427 := p.parse_write()
		item739 := _t1427
		xs737 = append(xs737, item739)
		cond738 = p.matchLookaheadLiteral("(", 0)
	}
	writes740 := xs737
	p.consumeLiteral(")")
	return writes740
}

func (p *Parser) parse_write() *pb.Write {
	span_start746 := int64(p.spanStart())
	var _t1428 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1429 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1429 = 1
		} else {
			var _t1430 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1430 = 3
			} else {
				var _t1431 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1431 = 0
				} else {
					var _t1432 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1432 = 2
					} else {
						_t1432 = -1
					}
					_t1431 = _t1432
				}
				_t1430 = _t1431
			}
			_t1429 = _t1430
		}
		_t1428 = _t1429
	} else {
		_t1428 = -1
	}
	prediction741 := _t1428
	var _t1433 *pb.Write
	if prediction741 == 3 {
		_t1434 := p.parse_snapshot()
		snapshot745 := _t1434
		_t1435 := &pb.Write{}
		_t1435.WriteType = &pb.Write_Snapshot{Snapshot: snapshot745}
		_t1433 = _t1435
	} else {
		var _t1436 *pb.Write
		if prediction741 == 2 {
			_t1437 := p.parse_context()
			context744 := _t1437
			_t1438 := &pb.Write{}
			_t1438.WriteType = &pb.Write_Context{Context: context744}
			_t1436 = _t1438
		} else {
			var _t1439 *pb.Write
			if prediction741 == 1 {
				_t1440 := p.parse_undefine()
				undefine743 := _t1440
				_t1441 := &pb.Write{}
				_t1441.WriteType = &pb.Write_Undefine{Undefine: undefine743}
				_t1439 = _t1441
			} else {
				var _t1442 *pb.Write
				if prediction741 == 0 {
					_t1443 := p.parse_define()
					define742 := _t1443
					_t1444 := &pb.Write{}
					_t1444.WriteType = &pb.Write_Define{Define: define742}
					_t1442 = _t1444
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1439 = _t1442
			}
			_t1436 = _t1439
		}
		_t1433 = _t1436
	}
	result747 := _t1433
	p.recordSpan(int(span_start746), "Write")
	return result747
}

func (p *Parser) parse_define() *pb.Define {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1445 := p.parse_fragment()
	fragment748 := _t1445
	p.consumeLiteral(")")
	_t1446 := &pb.Define{Fragment: fragment748}
	result750 := _t1446
	p.recordSpan(int(span_start749), "Define")
	return result750
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start756 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1447 := p.parse_new_fragment_id()
	new_fragment_id751 := _t1447
	xs752 := []*pb.Declaration{}
	cond753 := p.matchLookaheadLiteral("(", 0)
	for cond753 {
		_t1448 := p.parse_declaration()
		item754 := _t1448
		xs752 = append(xs752, item754)
		cond753 = p.matchLookaheadLiteral("(", 0)
	}
	declarations755 := xs752
	p.consumeLiteral(")")
	result757 := p.constructFragment(new_fragment_id751, declarations755)
	p.recordSpan(int(span_start756), "Fragment")
	return result757
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start759 := int64(p.spanStart())
	_t1449 := p.parse_fragment_id()
	fragment_id758 := _t1449
	p.startFragment(fragment_id758)
	result760 := fragment_id758
	p.recordSpan(int(span_start759), "FragmentId")
	return result760
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start766 := int64(p.spanStart())
	var _t1450 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1451 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1451 = 3
		} else {
			var _t1452 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1452 = 2
			} else {
				var _t1453 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1453 = 3
				} else {
					var _t1454 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1454 = 0
					} else {
						var _t1455 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1455 = 3
						} else {
							var _t1456 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1456 = 3
							} else {
								var _t1457 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1457 = 1
								} else {
									_t1457 = -1
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
	} else {
		_t1450 = -1
	}
	prediction761 := _t1450
	var _t1458 *pb.Declaration
	if prediction761 == 3 {
		_t1459 := p.parse_data()
		data765 := _t1459
		_t1460 := &pb.Declaration{}
		_t1460.DeclarationType = &pb.Declaration_Data{Data: data765}
		_t1458 = _t1460
	} else {
		var _t1461 *pb.Declaration
		if prediction761 == 2 {
			_t1462 := p.parse_constraint()
			constraint764 := _t1462
			_t1463 := &pb.Declaration{}
			_t1463.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint764}
			_t1461 = _t1463
		} else {
			var _t1464 *pb.Declaration
			if prediction761 == 1 {
				_t1465 := p.parse_algorithm()
				algorithm763 := _t1465
				_t1466 := &pb.Declaration{}
				_t1466.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm763}
				_t1464 = _t1466
			} else {
				var _t1467 *pb.Declaration
				if prediction761 == 0 {
					_t1468 := p.parse_def()
					def762 := _t1468
					_t1469 := &pb.Declaration{}
					_t1469.DeclarationType = &pb.Declaration_Def{Def: def762}
					_t1467 = _t1469
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1464 = _t1467
			}
			_t1461 = _t1464
		}
		_t1458 = _t1461
	}
	result767 := _t1458
	p.recordSpan(int(span_start766), "Declaration")
	return result767
}

func (p *Parser) parse_def() *pb.Def {
	span_start771 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1470 := p.parse_relation_id()
	relation_id768 := _t1470
	_t1471 := p.parse_abstraction()
	abstraction769 := _t1471
	var _t1472 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1473 := p.parse_attrs()
		_t1472 = _t1473
	}
	attrs770 := _t1472
	p.consumeLiteral(")")
	_t1474 := attrs770
	if attrs770 == nil {
		_t1474 = []*pb.Attribute{}
	}
	_t1475 := &pb.Def{Name: relation_id768, Body: abstraction769, Attrs: _t1474}
	result772 := _t1475
	p.recordSpan(int(span_start771), "Def")
	return result772
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start776 := int64(p.spanStart())
	var _t1476 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1476 = 0
	} else {
		var _t1477 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1477 = 1
		} else {
			_t1477 = -1
		}
		_t1476 = _t1477
	}
	prediction773 := _t1476
	var _t1478 *pb.RelationId
	if prediction773 == 1 {
		uint128775 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128775
		_t1478 = &pb.RelationId{IdLow: uint128775.Low, IdHigh: uint128775.High}
	} else {
		var _t1479 *pb.RelationId
		if prediction773 == 0 {
			p.consumeLiteral(":")
			symbol774 := p.consumeTerminal("SYMBOL").Value.str
			_t1479 = p.relationIdFromString(symbol774)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1478 = _t1479
	}
	result777 := _t1478
	p.recordSpan(int(span_start776), "RelationId")
	return result777
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start780 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1480 := p.parse_bindings()
	bindings778 := _t1480
	_t1481 := p.parse_formula()
	formula779 := _t1481
	p.consumeLiteral(")")
	_t1482 := &pb.Abstraction{Vars: listConcat(bindings778[0].([]*pb.Binding), bindings778[1].([]*pb.Binding)), Value: formula779}
	result781 := _t1482
	p.recordSpan(int(span_start780), "Abstraction")
	return result781
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs782 := []*pb.Binding{}
	cond783 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond783 {
		_t1483 := p.parse_binding()
		item784 := _t1483
		xs782 = append(xs782, item784)
		cond783 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings785 := xs782
	var _t1484 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1485 := p.parse_value_bindings()
		_t1484 = _t1485
	}
	value_bindings786 := _t1484
	p.consumeLiteral("]")
	_t1486 := value_bindings786
	if value_bindings786 == nil {
		_t1486 = []*pb.Binding{}
	}
	return []interface{}{bindings785, _t1486}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start789 := int64(p.spanStart())
	symbol787 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1487 := p.parse_type()
	type788 := _t1487
	_t1488 := &pb.Var{Name: symbol787}
	_t1489 := &pb.Binding{Var: _t1488, Type: type788}
	result790 := _t1489
	p.recordSpan(int(span_start789), "Binding")
	return result790
}

func (p *Parser) parse_type() *pb.Type {
	span_start806 := int64(p.spanStart())
	var _t1490 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1490 = 0
	} else {
		var _t1491 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1491 = 13
		} else {
			var _t1492 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1492 = 4
			} else {
				var _t1493 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1493 = 1
				} else {
					var _t1494 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1494 = 8
					} else {
						var _t1495 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1495 = 11
						} else {
							var _t1496 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1496 = 5
							} else {
								var _t1497 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1497 = 2
								} else {
									var _t1498 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1498 = 12
									} else {
										var _t1499 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1499 = 3
										} else {
											var _t1500 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1500 = 7
											} else {
												var _t1501 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1501 = 6
												} else {
													var _t1502 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1502 = 10
													} else {
														var _t1503 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1503 = 9
														} else {
															_t1503 = -1
														}
														_t1502 = _t1503
													}
													_t1501 = _t1502
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
	prediction791 := _t1490
	var _t1504 *pb.Type
	if prediction791 == 13 {
		_t1505 := p.parse_uint32_type()
		uint32_type805 := _t1505
		_t1506 := &pb.Type{}
		_t1506.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type805}
		_t1504 = _t1506
	} else {
		var _t1507 *pb.Type
		if prediction791 == 12 {
			_t1508 := p.parse_float32_type()
			float32_type804 := _t1508
			_t1509 := &pb.Type{}
			_t1509.Type = &pb.Type_Float32Type{Float32Type: float32_type804}
			_t1507 = _t1509
		} else {
			var _t1510 *pb.Type
			if prediction791 == 11 {
				_t1511 := p.parse_int32_type()
				int32_type803 := _t1511
				_t1512 := &pb.Type{}
				_t1512.Type = &pb.Type_Int32Type{Int32Type: int32_type803}
				_t1510 = _t1512
			} else {
				var _t1513 *pb.Type
				if prediction791 == 10 {
					_t1514 := p.parse_boolean_type()
					boolean_type802 := _t1514
					_t1515 := &pb.Type{}
					_t1515.Type = &pb.Type_BooleanType{BooleanType: boolean_type802}
					_t1513 = _t1515
				} else {
					var _t1516 *pb.Type
					if prediction791 == 9 {
						_t1517 := p.parse_decimal_type()
						decimal_type801 := _t1517
						_t1518 := &pb.Type{}
						_t1518.Type = &pb.Type_DecimalType{DecimalType: decimal_type801}
						_t1516 = _t1518
					} else {
						var _t1519 *pb.Type
						if prediction791 == 8 {
							_t1520 := p.parse_missing_type()
							missing_type800 := _t1520
							_t1521 := &pb.Type{}
							_t1521.Type = &pb.Type_MissingType{MissingType: missing_type800}
							_t1519 = _t1521
						} else {
							var _t1522 *pb.Type
							if prediction791 == 7 {
								_t1523 := p.parse_datetime_type()
								datetime_type799 := _t1523
								_t1524 := &pb.Type{}
								_t1524.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type799}
								_t1522 = _t1524
							} else {
								var _t1525 *pb.Type
								if prediction791 == 6 {
									_t1526 := p.parse_date_type()
									date_type798 := _t1526
									_t1527 := &pb.Type{}
									_t1527.Type = &pb.Type_DateType{DateType: date_type798}
									_t1525 = _t1527
								} else {
									var _t1528 *pb.Type
									if prediction791 == 5 {
										_t1529 := p.parse_int128_type()
										int128_type797 := _t1529
										_t1530 := &pb.Type{}
										_t1530.Type = &pb.Type_Int128Type{Int128Type: int128_type797}
										_t1528 = _t1530
									} else {
										var _t1531 *pb.Type
										if prediction791 == 4 {
											_t1532 := p.parse_uint128_type()
											uint128_type796 := _t1532
											_t1533 := &pb.Type{}
											_t1533.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type796}
											_t1531 = _t1533
										} else {
											var _t1534 *pb.Type
											if prediction791 == 3 {
												_t1535 := p.parse_float_type()
												float_type795 := _t1535
												_t1536 := &pb.Type{}
												_t1536.Type = &pb.Type_FloatType{FloatType: float_type795}
												_t1534 = _t1536
											} else {
												var _t1537 *pb.Type
												if prediction791 == 2 {
													_t1538 := p.parse_int_type()
													int_type794 := _t1538
													_t1539 := &pb.Type{}
													_t1539.Type = &pb.Type_IntType{IntType: int_type794}
													_t1537 = _t1539
												} else {
													var _t1540 *pb.Type
													if prediction791 == 1 {
														_t1541 := p.parse_string_type()
														string_type793 := _t1541
														_t1542 := &pb.Type{}
														_t1542.Type = &pb.Type_StringType{StringType: string_type793}
														_t1540 = _t1542
													} else {
														var _t1543 *pb.Type
														if prediction791 == 0 {
															_t1544 := p.parse_unspecified_type()
															unspecified_type792 := _t1544
															_t1545 := &pb.Type{}
															_t1545.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type792}
															_t1543 = _t1545
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1540 = _t1543
													}
													_t1537 = _t1540
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
	result807 := _t1504
	p.recordSpan(int(span_start806), "Type")
	return result807
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1546 := &pb.UnspecifiedType{}
	result809 := _t1546
	p.recordSpan(int(span_start808), "UnspecifiedType")
	return result809
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1547 := &pb.StringType{}
	result811 := _t1547
	p.recordSpan(int(span_start810), "StringType")
	return result811
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1548 := &pb.IntType{}
	result813 := _t1548
	p.recordSpan(int(span_start812), "IntType")
	return result813
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1549 := &pb.FloatType{}
	result815 := _t1549
	p.recordSpan(int(span_start814), "FloatType")
	return result815
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1550 := &pb.UInt128Type{}
	result817 := _t1550
	p.recordSpan(int(span_start816), "UInt128Type")
	return result817
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1551 := &pb.Int128Type{}
	result819 := _t1551
	p.recordSpan(int(span_start818), "Int128Type")
	return result819
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1552 := &pb.DateType{}
	result821 := _t1552
	p.recordSpan(int(span_start820), "DateType")
	return result821
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1553 := &pb.DateTimeType{}
	result823 := _t1553
	p.recordSpan(int(span_start822), "DateTimeType")
	return result823
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1554 := &pb.MissingType{}
	result825 := _t1554
	p.recordSpan(int(span_start824), "MissingType")
	return result825
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int826 := p.consumeTerminal("INT").Value.i64
	int_3827 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1555 := &pb.DecimalType{Precision: int32(int826), Scale: int32(int_3827)}
	result829 := _t1555
	p.recordSpan(int(span_start828), "DecimalType")
	return result829
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start830 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1556 := &pb.BooleanType{}
	result831 := _t1556
	p.recordSpan(int(span_start830), "BooleanType")
	return result831
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start832 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1557 := &pb.Int32Type{}
	result833 := _t1557
	p.recordSpan(int(span_start832), "Int32Type")
	return result833
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start834 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1558 := &pb.Float32Type{}
	result835 := _t1558
	p.recordSpan(int(span_start834), "Float32Type")
	return result835
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start836 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1559 := &pb.UInt32Type{}
	result837 := _t1559
	p.recordSpan(int(span_start836), "UInt32Type")
	return result837
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs838 := []*pb.Binding{}
	cond839 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond839 {
		_t1560 := p.parse_binding()
		item840 := _t1560
		xs838 = append(xs838, item840)
		cond839 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings841 := xs838
	return bindings841
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start856 := int64(p.spanStart())
	var _t1561 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1562 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1562 = 0
		} else {
			var _t1563 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1563 = 11
			} else {
				var _t1564 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1564 = 3
				} else {
					var _t1565 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1565 = 10
					} else {
						var _t1566 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1566 = 9
						} else {
							var _t1567 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1567 = 5
							} else {
								var _t1568 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1568 = 6
								} else {
									var _t1569 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1569 = 7
									} else {
										var _t1570 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1570 = 1
										} else {
											var _t1571 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1571 = 2
											} else {
												var _t1572 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1572 = 12
												} else {
													var _t1573 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1573 = 8
													} else {
														var _t1574 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1574 = 4
														} else {
															var _t1575 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1575 = 10
															} else {
																var _t1576 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1576 = 10
																} else {
																	var _t1577 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1577 = 10
																	} else {
																		var _t1578 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1578 = 10
																		} else {
																			var _t1579 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1579 = 10
																			} else {
																				var _t1580 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1580 = 10
																				} else {
																					var _t1581 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1581 = 10
																					} else {
																						var _t1582 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1582 = 10
																						} else {
																							var _t1583 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1583 = 10
																							} else {
																								_t1583 = -1
																							}
																							_t1582 = _t1583
																						}
																						_t1581 = _t1582
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
	} else {
		_t1561 = -1
	}
	prediction842 := _t1561
	var _t1584 *pb.Formula
	if prediction842 == 12 {
		_t1585 := p.parse_cast()
		cast855 := _t1585
		_t1586 := &pb.Formula{}
		_t1586.FormulaType = &pb.Formula_Cast{Cast: cast855}
		_t1584 = _t1586
	} else {
		var _t1587 *pb.Formula
		if prediction842 == 11 {
			_t1588 := p.parse_rel_atom()
			rel_atom854 := _t1588
			_t1589 := &pb.Formula{}
			_t1589.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom854}
			_t1587 = _t1589
		} else {
			var _t1590 *pb.Formula
			if prediction842 == 10 {
				_t1591 := p.parse_primitive()
				primitive853 := _t1591
				_t1592 := &pb.Formula{}
				_t1592.FormulaType = &pb.Formula_Primitive{Primitive: primitive853}
				_t1590 = _t1592
			} else {
				var _t1593 *pb.Formula
				if prediction842 == 9 {
					_t1594 := p.parse_pragma()
					pragma852 := _t1594
					_t1595 := &pb.Formula{}
					_t1595.FormulaType = &pb.Formula_Pragma{Pragma: pragma852}
					_t1593 = _t1595
				} else {
					var _t1596 *pb.Formula
					if prediction842 == 8 {
						_t1597 := p.parse_atom()
						atom851 := _t1597
						_t1598 := &pb.Formula{}
						_t1598.FormulaType = &pb.Formula_Atom{Atom: atom851}
						_t1596 = _t1598
					} else {
						var _t1599 *pb.Formula
						if prediction842 == 7 {
							_t1600 := p.parse_ffi()
							ffi850 := _t1600
							_t1601 := &pb.Formula{}
							_t1601.FormulaType = &pb.Formula_Ffi{Ffi: ffi850}
							_t1599 = _t1601
						} else {
							var _t1602 *pb.Formula
							if prediction842 == 6 {
								_t1603 := p.parse_not()
								not849 := _t1603
								_t1604 := &pb.Formula{}
								_t1604.FormulaType = &pb.Formula_Not{Not: not849}
								_t1602 = _t1604
							} else {
								var _t1605 *pb.Formula
								if prediction842 == 5 {
									_t1606 := p.parse_disjunction()
									disjunction848 := _t1606
									_t1607 := &pb.Formula{}
									_t1607.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction848}
									_t1605 = _t1607
								} else {
									var _t1608 *pb.Formula
									if prediction842 == 4 {
										_t1609 := p.parse_conjunction()
										conjunction847 := _t1609
										_t1610 := &pb.Formula{}
										_t1610.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction847}
										_t1608 = _t1610
									} else {
										var _t1611 *pb.Formula
										if prediction842 == 3 {
											_t1612 := p.parse_reduce()
											reduce846 := _t1612
											_t1613 := &pb.Formula{}
											_t1613.FormulaType = &pb.Formula_Reduce{Reduce: reduce846}
											_t1611 = _t1613
										} else {
											var _t1614 *pb.Formula
											if prediction842 == 2 {
												_t1615 := p.parse_exists()
												exists845 := _t1615
												_t1616 := &pb.Formula{}
												_t1616.FormulaType = &pb.Formula_Exists{Exists: exists845}
												_t1614 = _t1616
											} else {
												var _t1617 *pb.Formula
												if prediction842 == 1 {
													_t1618 := p.parse_false()
													false844 := _t1618
													_t1619 := &pb.Formula{}
													_t1619.FormulaType = &pb.Formula_Disjunction{Disjunction: false844}
													_t1617 = _t1619
												} else {
													var _t1620 *pb.Formula
													if prediction842 == 0 {
														_t1621 := p.parse_true()
														true843 := _t1621
														_t1622 := &pb.Formula{}
														_t1622.FormulaType = &pb.Formula_Conjunction{Conjunction: true843}
														_t1620 = _t1622
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
	result857 := _t1584
	p.recordSpan(int(span_start856), "Formula")
	return result857
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1623 := &pb.Conjunction{Args: []*pb.Formula{}}
	result859 := _t1623
	p.recordSpan(int(span_start858), "Conjunction")
	return result859
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1624 := &pb.Disjunction{Args: []*pb.Formula{}}
	result861 := _t1624
	p.recordSpan(int(span_start860), "Disjunction")
	return result861
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1625 := p.parse_bindings()
	bindings862 := _t1625
	_t1626 := p.parse_formula()
	formula863 := _t1626
	p.consumeLiteral(")")
	_t1627 := &pb.Abstraction{Vars: listConcat(bindings862[0].([]*pb.Binding), bindings862[1].([]*pb.Binding)), Value: formula863}
	_t1628 := &pb.Exists{Body: _t1627}
	result865 := _t1628
	p.recordSpan(int(span_start864), "Exists")
	return result865
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1629 := p.parse_abstraction()
	abstraction866 := _t1629
	_t1630 := p.parse_abstraction()
	abstraction_3867 := _t1630
	_t1631 := p.parse_terms()
	terms868 := _t1631
	p.consumeLiteral(")")
	_t1632 := &pb.Reduce{Op: abstraction866, Body: abstraction_3867, Terms: terms868}
	result870 := _t1632
	p.recordSpan(int(span_start869), "Reduce")
	return result870
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs871 := []*pb.Term{}
	cond872 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond872 {
		_t1633 := p.parse_term()
		item873 := _t1633
		xs871 = append(xs871, item873)
		cond872 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms874 := xs871
	p.consumeLiteral(")")
	return terms874
}

func (p *Parser) parse_term() *pb.Term {
	span_start878 := int64(p.spanStart())
	var _t1634 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1634 = 1
	} else {
		var _t1635 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1635 = 1
		} else {
			var _t1636 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1636 = 1
			} else {
				var _t1637 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1637 = 1
				} else {
					var _t1638 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1638 = 0
					} else {
						var _t1639 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1639 = 1
						} else {
							var _t1640 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1640 = 1
							} else {
								var _t1641 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1641 = 1
								} else {
									var _t1642 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1642 = 1
									} else {
										var _t1643 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1643 = 1
										} else {
											var _t1644 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1644 = 1
											} else {
												var _t1645 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1645 = 1
												} else {
													var _t1646 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1646 = 1
													} else {
														var _t1647 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1647 = 1
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
	prediction875 := _t1634
	var _t1648 *pb.Term
	if prediction875 == 1 {
		_t1649 := p.parse_value()
		value877 := _t1649
		_t1650 := &pb.Term{}
		_t1650.TermType = &pb.Term_Constant{Constant: value877}
		_t1648 = _t1650
	} else {
		var _t1651 *pb.Term
		if prediction875 == 0 {
			_t1652 := p.parse_var()
			var876 := _t1652
			_t1653 := &pb.Term{}
			_t1653.TermType = &pb.Term_Var{Var: var876}
			_t1651 = _t1653
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1648 = _t1651
	}
	result879 := _t1648
	p.recordSpan(int(span_start878), "Term")
	return result879
}

func (p *Parser) parse_var() *pb.Var {
	span_start881 := int64(p.spanStart())
	symbol880 := p.consumeTerminal("SYMBOL").Value.str
	_t1654 := &pb.Var{Name: symbol880}
	result882 := _t1654
	p.recordSpan(int(span_start881), "Var")
	return result882
}

func (p *Parser) parse_value() *pb.Value {
	span_start896 := int64(p.spanStart())
	var _t1655 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1655 = 12
	} else {
		var _t1656 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1656 = 11
		} else {
			var _t1657 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1657 = 12
			} else {
				var _t1658 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1659 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1659 = 1
					} else {
						var _t1660 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1660 = 0
						} else {
							_t1660 = -1
						}
						_t1659 = _t1660
					}
					_t1658 = _t1659
				} else {
					var _t1661 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1661 = 7
					} else {
						var _t1662 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1662 = 8
						} else {
							var _t1663 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1663 = 2
							} else {
								var _t1664 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1664 = 3
								} else {
									var _t1665 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1665 = 9
									} else {
										var _t1666 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1666 = 4
										} else {
											var _t1667 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1667 = 5
											} else {
												var _t1668 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1668 = 6
												} else {
													var _t1669 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1669 = 10
													} else {
														_t1669 = -1
													}
													_t1668 = _t1669
												}
												_t1667 = _t1668
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
					_t1658 = _t1661
				}
				_t1657 = _t1658
			}
			_t1656 = _t1657
		}
		_t1655 = _t1656
	}
	prediction883 := _t1655
	var _t1670 *pb.Value
	if prediction883 == 12 {
		_t1671 := p.parse_boolean_value()
		boolean_value895 := _t1671
		_t1672 := &pb.Value{}
		_t1672.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value895}
		_t1670 = _t1672
	} else {
		var _t1673 *pb.Value
		if prediction883 == 11 {
			p.consumeLiteral("missing")
			_t1674 := &pb.MissingValue{}
			_t1675 := &pb.Value{}
			_t1675.Value = &pb.Value_MissingValue{MissingValue: _t1674}
			_t1673 = _t1675
		} else {
			var _t1676 *pb.Value
			if prediction883 == 10 {
				formatted_decimal894 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1677 := &pb.Value{}
				_t1677.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal894}
				_t1676 = _t1677
			} else {
				var _t1678 *pb.Value
				if prediction883 == 9 {
					formatted_int128893 := p.consumeTerminal("INT128").Value.int128
					_t1679 := &pb.Value{}
					_t1679.Value = &pb.Value_Int128Value{Int128Value: formatted_int128893}
					_t1678 = _t1679
				} else {
					var _t1680 *pb.Value
					if prediction883 == 8 {
						formatted_uint128892 := p.consumeTerminal("UINT128").Value.uint128
						_t1681 := &pb.Value{}
						_t1681.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128892}
						_t1680 = _t1681
					} else {
						var _t1682 *pb.Value
						if prediction883 == 7 {
							formatted_uint32891 := p.consumeTerminal("UINT32").Value.u32
							_t1683 := &pb.Value{}
							_t1683.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32891}
							_t1682 = _t1683
						} else {
							var _t1684 *pb.Value
							if prediction883 == 6 {
								formatted_float890 := p.consumeTerminal("FLOAT").Value.f64
								_t1685 := &pb.Value{}
								_t1685.Value = &pb.Value_FloatValue{FloatValue: formatted_float890}
								_t1684 = _t1685
							} else {
								var _t1686 *pb.Value
								if prediction883 == 5 {
									formatted_float32889 := p.consumeTerminal("FLOAT32").Value.f32
									_t1687 := &pb.Value{}
									_t1687.Value = &pb.Value_Float32Value{Float32Value: formatted_float32889}
									_t1686 = _t1687
								} else {
									var _t1688 *pb.Value
									if prediction883 == 4 {
										formatted_int888 := p.consumeTerminal("INT").Value.i64
										_t1689 := &pb.Value{}
										_t1689.Value = &pb.Value_IntValue{IntValue: formatted_int888}
										_t1688 = _t1689
									} else {
										var _t1690 *pb.Value
										if prediction883 == 3 {
											formatted_int32887 := p.consumeTerminal("INT32").Value.i32
											_t1691 := &pb.Value{}
											_t1691.Value = &pb.Value_Int32Value{Int32Value: formatted_int32887}
											_t1690 = _t1691
										} else {
											var _t1692 *pb.Value
											if prediction883 == 2 {
												formatted_string886 := p.consumeTerminal("STRING").Value.str
												_t1693 := &pb.Value{}
												_t1693.Value = &pb.Value_StringValue{StringValue: formatted_string886}
												_t1692 = _t1693
											} else {
												var _t1694 *pb.Value
												if prediction883 == 1 {
													_t1695 := p.parse_datetime()
													datetime885 := _t1695
													_t1696 := &pb.Value{}
													_t1696.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime885}
													_t1694 = _t1696
												} else {
													var _t1697 *pb.Value
													if prediction883 == 0 {
														_t1698 := p.parse_date()
														date884 := _t1698
														_t1699 := &pb.Value{}
														_t1699.Value = &pb.Value_DateValue{DateValue: date884}
														_t1697 = _t1699
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1694 = _t1697
												}
												_t1692 = _t1694
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
			_t1673 = _t1676
		}
		_t1670 = _t1673
	}
	result897 := _t1670
	p.recordSpan(int(span_start896), "Value")
	return result897
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int898 := p.consumeTerminal("INT").Value.i64
	formatted_int_3899 := p.consumeTerminal("INT").Value.i64
	formatted_int_4900 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1700 := &pb.DateValue{Year: int32(formatted_int898), Month: int32(formatted_int_3899), Day: int32(formatted_int_4900)}
	result902 := _t1700
	p.recordSpan(int(span_start901), "DateValue")
	return result902
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start910 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int903 := p.consumeTerminal("INT").Value.i64
	formatted_int_3904 := p.consumeTerminal("INT").Value.i64
	formatted_int_4905 := p.consumeTerminal("INT").Value.i64
	formatted_int_5906 := p.consumeTerminal("INT").Value.i64
	formatted_int_6907 := p.consumeTerminal("INT").Value.i64
	formatted_int_7908 := p.consumeTerminal("INT").Value.i64
	var _t1701 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1701 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8909 := _t1701
	p.consumeLiteral(")")
	_t1702 := &pb.DateTimeValue{Year: int32(formatted_int903), Month: int32(formatted_int_3904), Day: int32(formatted_int_4905), Hour: int32(formatted_int_5906), Minute: int32(formatted_int_6907), Second: int32(formatted_int_7908), Microsecond: int32(deref(formatted_int_8909, 0))}
	result911 := _t1702
	p.recordSpan(int(span_start910), "DateTimeValue")
	return result911
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start916 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs912 := []*pb.Formula{}
	cond913 := p.matchLookaheadLiteral("(", 0)
	for cond913 {
		_t1703 := p.parse_formula()
		item914 := _t1703
		xs912 = append(xs912, item914)
		cond913 = p.matchLookaheadLiteral("(", 0)
	}
	formulas915 := xs912
	p.consumeLiteral(")")
	_t1704 := &pb.Conjunction{Args: formulas915}
	result917 := _t1704
	p.recordSpan(int(span_start916), "Conjunction")
	return result917
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start922 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs918 := []*pb.Formula{}
	cond919 := p.matchLookaheadLiteral("(", 0)
	for cond919 {
		_t1705 := p.parse_formula()
		item920 := _t1705
		xs918 = append(xs918, item920)
		cond919 = p.matchLookaheadLiteral("(", 0)
	}
	formulas921 := xs918
	p.consumeLiteral(")")
	_t1706 := &pb.Disjunction{Args: formulas921}
	result923 := _t1706
	p.recordSpan(int(span_start922), "Disjunction")
	return result923
}

func (p *Parser) parse_not() *pb.Not {
	span_start925 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1707 := p.parse_formula()
	formula924 := _t1707
	p.consumeLiteral(")")
	_t1708 := &pb.Not{Arg: formula924}
	result926 := _t1708
	p.recordSpan(int(span_start925), "Not")
	return result926
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start930 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1709 := p.parse_name()
	name927 := _t1709
	_t1710 := p.parse_ffi_args()
	ffi_args928 := _t1710
	_t1711 := p.parse_terms()
	terms929 := _t1711
	p.consumeLiteral(")")
	_t1712 := &pb.FFI{Name: name927, Args: ffi_args928, Terms: terms929}
	result931 := _t1712
	p.recordSpan(int(span_start930), "FFI")
	return result931
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol932 := p.consumeTerminal("SYMBOL").Value.str
	return symbol932
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs933 := []*pb.Abstraction{}
	cond934 := p.matchLookaheadLiteral("(", 0)
	for cond934 {
		_t1713 := p.parse_abstraction()
		item935 := _t1713
		xs933 = append(xs933, item935)
		cond934 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions936 := xs933
	p.consumeLiteral(")")
	return abstractions936
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1714 := p.parse_relation_id()
	relation_id937 := _t1714
	xs938 := []*pb.Term{}
	cond939 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond939 {
		_t1715 := p.parse_term()
		item940 := _t1715
		xs938 = append(xs938, item940)
		cond939 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms941 := xs938
	p.consumeLiteral(")")
	_t1716 := &pb.Atom{Name: relation_id937, Terms: terms941}
	result943 := _t1716
	p.recordSpan(int(span_start942), "Atom")
	return result943
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start949 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1717 := p.parse_name()
	name944 := _t1717
	xs945 := []*pb.Term{}
	cond946 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond946 {
		_t1718 := p.parse_term()
		item947 := _t1718
		xs945 = append(xs945, item947)
		cond946 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms948 := xs945
	p.consumeLiteral(")")
	_t1719 := &pb.Pragma{Name: name944, Terms: terms948}
	result950 := _t1719
	p.recordSpan(int(span_start949), "Pragma")
	return result950
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start966 := int64(p.spanStart())
	var _t1720 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1721 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1721 = 9
		} else {
			var _t1722 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1722 = 4
			} else {
				var _t1723 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1723 = 3
				} else {
					var _t1724 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1724 = 0
					} else {
						var _t1725 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1725 = 2
						} else {
							var _t1726 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1726 = 1
							} else {
								var _t1727 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1727 = 8
								} else {
									var _t1728 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1728 = 6
									} else {
										var _t1729 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1729 = 5
										} else {
											var _t1730 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1730 = 7
											} else {
												_t1730 = -1
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
	} else {
		_t1720 = -1
	}
	prediction951 := _t1720
	var _t1731 *pb.Primitive
	if prediction951 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1732 := p.parse_name()
		name961 := _t1732
		xs962 := []*pb.RelTerm{}
		cond963 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond963 {
			_t1733 := p.parse_rel_term()
			item964 := _t1733
			xs962 = append(xs962, item964)
			cond963 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms965 := xs962
		p.consumeLiteral(")")
		_t1734 := &pb.Primitive{Name: name961, Terms: rel_terms965}
		_t1731 = _t1734
	} else {
		var _t1735 *pb.Primitive
		if prediction951 == 8 {
			_t1736 := p.parse_divide()
			divide960 := _t1736
			_t1735 = divide960
		} else {
			var _t1737 *pb.Primitive
			if prediction951 == 7 {
				_t1738 := p.parse_multiply()
				multiply959 := _t1738
				_t1737 = multiply959
			} else {
				var _t1739 *pb.Primitive
				if prediction951 == 6 {
					_t1740 := p.parse_minus()
					minus958 := _t1740
					_t1739 = minus958
				} else {
					var _t1741 *pb.Primitive
					if prediction951 == 5 {
						_t1742 := p.parse_add()
						add957 := _t1742
						_t1741 = add957
					} else {
						var _t1743 *pb.Primitive
						if prediction951 == 4 {
							_t1744 := p.parse_gt_eq()
							gt_eq956 := _t1744
							_t1743 = gt_eq956
						} else {
							var _t1745 *pb.Primitive
							if prediction951 == 3 {
								_t1746 := p.parse_gt()
								gt955 := _t1746
								_t1745 = gt955
							} else {
								var _t1747 *pb.Primitive
								if prediction951 == 2 {
									_t1748 := p.parse_lt_eq()
									lt_eq954 := _t1748
									_t1747 = lt_eq954
								} else {
									var _t1749 *pb.Primitive
									if prediction951 == 1 {
										_t1750 := p.parse_lt()
										lt953 := _t1750
										_t1749 = lt953
									} else {
										var _t1751 *pb.Primitive
										if prediction951 == 0 {
											_t1752 := p.parse_eq()
											eq952 := _t1752
											_t1751 = eq952
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1749 = _t1751
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
		_t1731 = _t1735
	}
	result967 := _t1731
	p.recordSpan(int(span_start966), "Primitive")
	return result967
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1753 := p.parse_term()
	term968 := _t1753
	_t1754 := p.parse_term()
	term_3969 := _t1754
	p.consumeLiteral(")")
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term968}
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term_3969}
	_t1757 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1755, _t1756}}
	result971 := _t1757
	p.recordSpan(int(span_start970), "Primitive")
	return result971
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1758 := p.parse_term()
	term972 := _t1758
	_t1759 := p.parse_term()
	term_3973 := _t1759
	p.consumeLiteral(")")
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term972}
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term_3973}
	_t1762 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1760, _t1761}}
	result975 := _t1762
	p.recordSpan(int(span_start974), "Primitive")
	return result975
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start978 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1763 := p.parse_term()
	term976 := _t1763
	_t1764 := p.parse_term()
	term_3977 := _t1764
	p.consumeLiteral(")")
	_t1765 := &pb.RelTerm{}
	_t1765.RelTermType = &pb.RelTerm_Term{Term: term976}
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term_3977}
	_t1767 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1765, _t1766}}
	result979 := _t1767
	p.recordSpan(int(span_start978), "Primitive")
	return result979
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start982 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1768 := p.parse_term()
	term980 := _t1768
	_t1769 := p.parse_term()
	term_3981 := _t1769
	p.consumeLiteral(")")
	_t1770 := &pb.RelTerm{}
	_t1770.RelTermType = &pb.RelTerm_Term{Term: term980}
	_t1771 := &pb.RelTerm{}
	_t1771.RelTermType = &pb.RelTerm_Term{Term: term_3981}
	_t1772 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1770, _t1771}}
	result983 := _t1772
	p.recordSpan(int(span_start982), "Primitive")
	return result983
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1773 := p.parse_term()
	term984 := _t1773
	_t1774 := p.parse_term()
	term_3985 := _t1774
	p.consumeLiteral(")")
	_t1775 := &pb.RelTerm{}
	_t1775.RelTermType = &pb.RelTerm_Term{Term: term984}
	_t1776 := &pb.RelTerm{}
	_t1776.RelTermType = &pb.RelTerm_Term{Term: term_3985}
	_t1777 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1775, _t1776}}
	result987 := _t1777
	p.recordSpan(int(span_start986), "Primitive")
	return result987
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start991 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1778 := p.parse_term()
	term988 := _t1778
	_t1779 := p.parse_term()
	term_3989 := _t1779
	_t1780 := p.parse_term()
	term_4990 := _t1780
	p.consumeLiteral(")")
	_t1781 := &pb.RelTerm{}
	_t1781.RelTermType = &pb.RelTerm_Term{Term: term988}
	_t1782 := &pb.RelTerm{}
	_t1782.RelTermType = &pb.RelTerm_Term{Term: term_3989}
	_t1783 := &pb.RelTerm{}
	_t1783.RelTermType = &pb.RelTerm_Term{Term: term_4990}
	_t1784 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1781, _t1782, _t1783}}
	result992 := _t1784
	p.recordSpan(int(span_start991), "Primitive")
	return result992
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start996 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1785 := p.parse_term()
	term993 := _t1785
	_t1786 := p.parse_term()
	term_3994 := _t1786
	_t1787 := p.parse_term()
	term_4995 := _t1787
	p.consumeLiteral(")")
	_t1788 := &pb.RelTerm{}
	_t1788.RelTermType = &pb.RelTerm_Term{Term: term993}
	_t1789 := &pb.RelTerm{}
	_t1789.RelTermType = &pb.RelTerm_Term{Term: term_3994}
	_t1790 := &pb.RelTerm{}
	_t1790.RelTermType = &pb.RelTerm_Term{Term: term_4995}
	_t1791 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1788, _t1789, _t1790}}
	result997 := _t1791
	p.recordSpan(int(span_start996), "Primitive")
	return result997
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start1001 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1792 := p.parse_term()
	term998 := _t1792
	_t1793 := p.parse_term()
	term_3999 := _t1793
	_t1794 := p.parse_term()
	term_41000 := _t1794
	p.consumeLiteral(")")
	_t1795 := &pb.RelTerm{}
	_t1795.RelTermType = &pb.RelTerm_Term{Term: term998}
	_t1796 := &pb.RelTerm{}
	_t1796.RelTermType = &pb.RelTerm_Term{Term: term_3999}
	_t1797 := &pb.RelTerm{}
	_t1797.RelTermType = &pb.RelTerm_Term{Term: term_41000}
	_t1798 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1795, _t1796, _t1797}}
	result1002 := _t1798
	p.recordSpan(int(span_start1001), "Primitive")
	return result1002
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1006 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1799 := p.parse_term()
	term1003 := _t1799
	_t1800 := p.parse_term()
	term_31004 := _t1800
	_t1801 := p.parse_term()
	term_41005 := _t1801
	p.consumeLiteral(")")
	_t1802 := &pb.RelTerm{}
	_t1802.RelTermType = &pb.RelTerm_Term{Term: term1003}
	_t1803 := &pb.RelTerm{}
	_t1803.RelTermType = &pb.RelTerm_Term{Term: term_31004}
	_t1804 := &pb.RelTerm{}
	_t1804.RelTermType = &pb.RelTerm_Term{Term: term_41005}
	_t1805 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1802, _t1803, _t1804}}
	result1007 := _t1805
	p.recordSpan(int(span_start1006), "Primitive")
	return result1007
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1011 := int64(p.spanStart())
	var _t1806 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1806 = 1
	} else {
		var _t1807 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1807 = 1
		} else {
			var _t1808 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1808 = 1
			} else {
				var _t1809 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1809 = 1
				} else {
					var _t1810 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1810 = 0
					} else {
						var _t1811 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1811 = 1
						} else {
							var _t1812 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1812 = 1
							} else {
								var _t1813 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1813 = 1
								} else {
									var _t1814 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1814 = 1
									} else {
										var _t1815 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1815 = 1
										} else {
											var _t1816 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1816 = 1
											} else {
												var _t1817 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1817 = 1
												} else {
													var _t1818 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1818 = 1
													} else {
														var _t1819 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1819 = 1
														} else {
															var _t1820 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1820 = 1
															} else {
																_t1820 = -1
															}
															_t1819 = _t1820
														}
														_t1818 = _t1819
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
	prediction1008 := _t1806
	var _t1821 *pb.RelTerm
	if prediction1008 == 1 {
		_t1822 := p.parse_term()
		term1010 := _t1822
		_t1823 := &pb.RelTerm{}
		_t1823.RelTermType = &pb.RelTerm_Term{Term: term1010}
		_t1821 = _t1823
	} else {
		var _t1824 *pb.RelTerm
		if prediction1008 == 0 {
			_t1825 := p.parse_specialized_value()
			specialized_value1009 := _t1825
			_t1826 := &pb.RelTerm{}
			_t1826.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1009}
			_t1824 = _t1826
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1821 = _t1824
	}
	result1012 := _t1821
	p.recordSpan(int(span_start1011), "RelTerm")
	return result1012
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1827 := p.parse_raw_value()
	raw_value1013 := _t1827
	result1015 := raw_value1013
	p.recordSpan(int(span_start1014), "Value")
	return result1015
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1828 := p.parse_name()
	name1016 := _t1828
	xs1017 := []*pb.RelTerm{}
	cond1018 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1018 {
		_t1829 := p.parse_rel_term()
		item1019 := _t1829
		xs1017 = append(xs1017, item1019)
		cond1018 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1020 := xs1017
	p.consumeLiteral(")")
	_t1830 := &pb.RelAtom{Name: name1016, Terms: rel_terms1020}
	result1022 := _t1830
	p.recordSpan(int(span_start1021), "RelAtom")
	return result1022
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1025 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1831 := p.parse_term()
	term1023 := _t1831
	_t1832 := p.parse_term()
	term_31024 := _t1832
	p.consumeLiteral(")")
	_t1833 := &pb.Cast{Input: term1023, Result: term_31024}
	result1026 := _t1833
	p.recordSpan(int(span_start1025), "Cast")
	return result1026
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1027 := []*pb.Attribute{}
	cond1028 := p.matchLookaheadLiteral("(", 0)
	for cond1028 {
		_t1834 := p.parse_attribute()
		item1029 := _t1834
		xs1027 = append(xs1027, item1029)
		cond1028 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1030 := xs1027
	p.consumeLiteral(")")
	return attributes1030
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1835 := p.parse_name()
	name1031 := _t1835
	xs1032 := []*pb.Value{}
	cond1033 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1033 {
		_t1836 := p.parse_raw_value()
		item1034 := _t1836
		xs1032 = append(xs1032, item1034)
		cond1033 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1035 := xs1032
	p.consumeLiteral(")")
	_t1837 := &pb.Attribute{Name: name1031, Args: raw_values1035}
	result1037 := _t1837
	p.recordSpan(int(span_start1036), "Attribute")
	return result1037
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1038 := []*pb.RelationId{}
	cond1039 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1039 {
		_t1838 := p.parse_relation_id()
		item1040 := _t1838
		xs1038 = append(xs1038, item1040)
		cond1039 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1041 := xs1038
	_t1839 := p.parse_script()
	script1042 := _t1839
	var _t1840 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1841 := p.parse_attrs()
		_t1840 = _t1841
	}
	attrs1043 := _t1840
	p.consumeLiteral(")")
	_t1842 := attrs1043
	if attrs1043 == nil {
		_t1842 = []*pb.Attribute{}
	}
	_t1843 := &pb.Algorithm{Global: relation_ids1041, Body: script1042, Attrs: _t1842}
	result1045 := _t1843
	p.recordSpan(int(span_start1044), "Algorithm")
	return result1045
}

func (p *Parser) parse_script() *pb.Script {
	span_start1050 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1046 := []*pb.Construct{}
	cond1047 := p.matchLookaheadLiteral("(", 0)
	for cond1047 {
		_t1844 := p.parse_construct()
		item1048 := _t1844
		xs1046 = append(xs1046, item1048)
		cond1047 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1049 := xs1046
	p.consumeLiteral(")")
	_t1845 := &pb.Script{Constructs: constructs1049}
	result1051 := _t1845
	p.recordSpan(int(span_start1050), "Script")
	return result1051
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1055 := int64(p.spanStart())
	var _t1846 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1847 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1847 = 1
		} else {
			var _t1848 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1848 = 1
			} else {
				var _t1849 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1849 = 1
				} else {
					var _t1850 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1850 = 0
					} else {
						var _t1851 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1851 = 1
						} else {
							var _t1852 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1852 = 1
							} else {
								_t1852 = -1
							}
							_t1851 = _t1852
						}
						_t1850 = _t1851
					}
					_t1849 = _t1850
				}
				_t1848 = _t1849
			}
			_t1847 = _t1848
		}
		_t1846 = _t1847
	} else {
		_t1846 = -1
	}
	prediction1052 := _t1846
	var _t1853 *pb.Construct
	if prediction1052 == 1 {
		_t1854 := p.parse_instruction()
		instruction1054 := _t1854
		_t1855 := &pb.Construct{}
		_t1855.ConstructType = &pb.Construct_Instruction{Instruction: instruction1054}
		_t1853 = _t1855
	} else {
		var _t1856 *pb.Construct
		if prediction1052 == 0 {
			_t1857 := p.parse_loop()
			loop1053 := _t1857
			_t1858 := &pb.Construct{}
			_t1858.ConstructType = &pb.Construct_Loop{Loop: loop1053}
			_t1856 = _t1858
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1853 = _t1856
	}
	result1056 := _t1853
	p.recordSpan(int(span_start1055), "Construct")
	return result1056
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1060 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1859 := p.parse_init()
	init1057 := _t1859
	_t1860 := p.parse_script()
	script1058 := _t1860
	var _t1861 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1862 := p.parse_attrs()
		_t1861 = _t1862
	}
	attrs1059 := _t1861
	p.consumeLiteral(")")
	_t1863 := attrs1059
	if attrs1059 == nil {
		_t1863 = []*pb.Attribute{}
	}
	_t1864 := &pb.Loop{Init: init1057, Body: script1058, Attrs: _t1863}
	result1061 := _t1864
	p.recordSpan(int(span_start1060), "Loop")
	return result1061
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1062 := []*pb.Instruction{}
	cond1063 := p.matchLookaheadLiteral("(", 0)
	for cond1063 {
		_t1865 := p.parse_instruction()
		item1064 := _t1865
		xs1062 = append(xs1062, item1064)
		cond1063 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1065 := xs1062
	p.consumeLiteral(")")
	return instructions1065
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1072 := int64(p.spanStart())
	var _t1866 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1867 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1867 = 1
		} else {
			var _t1868 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1868 = 4
			} else {
				var _t1869 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1869 = 3
				} else {
					var _t1870 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1870 = 2
					} else {
						var _t1871 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1871 = 0
						} else {
							_t1871 = -1
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
	} else {
		_t1866 = -1
	}
	prediction1066 := _t1866
	var _t1872 *pb.Instruction
	if prediction1066 == 4 {
		_t1873 := p.parse_monus_def()
		monus_def1071 := _t1873
		_t1874 := &pb.Instruction{}
		_t1874.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1071}
		_t1872 = _t1874
	} else {
		var _t1875 *pb.Instruction
		if prediction1066 == 3 {
			_t1876 := p.parse_monoid_def()
			monoid_def1070 := _t1876
			_t1877 := &pb.Instruction{}
			_t1877.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1070}
			_t1875 = _t1877
		} else {
			var _t1878 *pb.Instruction
			if prediction1066 == 2 {
				_t1879 := p.parse_break()
				break1069 := _t1879
				_t1880 := &pb.Instruction{}
				_t1880.InstrType = &pb.Instruction_Break{Break: break1069}
				_t1878 = _t1880
			} else {
				var _t1881 *pb.Instruction
				if prediction1066 == 1 {
					_t1882 := p.parse_upsert()
					upsert1068 := _t1882
					_t1883 := &pb.Instruction{}
					_t1883.InstrType = &pb.Instruction_Upsert{Upsert: upsert1068}
					_t1881 = _t1883
				} else {
					var _t1884 *pb.Instruction
					if prediction1066 == 0 {
						_t1885 := p.parse_assign()
						assign1067 := _t1885
						_t1886 := &pb.Instruction{}
						_t1886.InstrType = &pb.Instruction_Assign{Assign: assign1067}
						_t1884 = _t1886
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1881 = _t1884
				}
				_t1878 = _t1881
			}
			_t1875 = _t1878
		}
		_t1872 = _t1875
	}
	result1073 := _t1872
	p.recordSpan(int(span_start1072), "Instruction")
	return result1073
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1077 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1887 := p.parse_relation_id()
	relation_id1074 := _t1887
	_t1888 := p.parse_abstraction()
	abstraction1075 := _t1888
	var _t1889 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1890 := p.parse_attrs()
		_t1889 = _t1890
	}
	attrs1076 := _t1889
	p.consumeLiteral(")")
	_t1891 := attrs1076
	if attrs1076 == nil {
		_t1891 = []*pb.Attribute{}
	}
	_t1892 := &pb.Assign{Name: relation_id1074, Body: abstraction1075, Attrs: _t1891}
	result1078 := _t1892
	p.recordSpan(int(span_start1077), "Assign")
	return result1078
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1893 := p.parse_relation_id()
	relation_id1079 := _t1893
	_t1894 := p.parse_abstraction_with_arity()
	abstraction_with_arity1080 := _t1894
	var _t1895 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1896 := p.parse_attrs()
		_t1895 = _t1896
	}
	attrs1081 := _t1895
	p.consumeLiteral(")")
	_t1897 := attrs1081
	if attrs1081 == nil {
		_t1897 = []*pb.Attribute{}
	}
	_t1898 := &pb.Upsert{Name: relation_id1079, Body: abstraction_with_arity1080[0].(*pb.Abstraction), Attrs: _t1897, ValueArity: abstraction_with_arity1080[1].(int64)}
	result1083 := _t1898
	p.recordSpan(int(span_start1082), "Upsert")
	return result1083
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1899 := p.parse_bindings()
	bindings1084 := _t1899
	_t1900 := p.parse_formula()
	formula1085 := _t1900
	p.consumeLiteral(")")
	_t1901 := &pb.Abstraction{Vars: listConcat(bindings1084[0].([]*pb.Binding), bindings1084[1].([]*pb.Binding)), Value: formula1085}
	return []interface{}{_t1901, int64(len(bindings1084[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1089 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1902 := p.parse_relation_id()
	relation_id1086 := _t1902
	_t1903 := p.parse_abstraction()
	abstraction1087 := _t1903
	var _t1904 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1905 := p.parse_attrs()
		_t1904 = _t1905
	}
	attrs1088 := _t1904
	p.consumeLiteral(")")
	_t1906 := attrs1088
	if attrs1088 == nil {
		_t1906 = []*pb.Attribute{}
	}
	_t1907 := &pb.Break{Name: relation_id1086, Body: abstraction1087, Attrs: _t1906}
	result1090 := _t1907
	p.recordSpan(int(span_start1089), "Break")
	return result1090
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1095 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1908 := p.parse_monoid()
	monoid1091 := _t1908
	_t1909 := p.parse_relation_id()
	relation_id1092 := _t1909
	_t1910 := p.parse_abstraction_with_arity()
	abstraction_with_arity1093 := _t1910
	var _t1911 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1912 := p.parse_attrs()
		_t1911 = _t1912
	}
	attrs1094 := _t1911
	p.consumeLiteral(")")
	_t1913 := attrs1094
	if attrs1094 == nil {
		_t1913 = []*pb.Attribute{}
	}
	_t1914 := &pb.MonoidDef{Monoid: monoid1091, Name: relation_id1092, Body: abstraction_with_arity1093[0].(*pb.Abstraction), Attrs: _t1913, ValueArity: abstraction_with_arity1093[1].(int64)}
	result1096 := _t1914
	p.recordSpan(int(span_start1095), "MonoidDef")
	return result1096
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1102 := int64(p.spanStart())
	var _t1915 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1916 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1916 = 3
		} else {
			var _t1917 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1917 = 0
			} else {
				var _t1918 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1918 = 1
				} else {
					var _t1919 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1919 = 2
					} else {
						_t1919 = -1
					}
					_t1918 = _t1919
				}
				_t1917 = _t1918
			}
			_t1916 = _t1917
		}
		_t1915 = _t1916
	} else {
		_t1915 = -1
	}
	prediction1097 := _t1915
	var _t1920 *pb.Monoid
	if prediction1097 == 3 {
		_t1921 := p.parse_sum_monoid()
		sum_monoid1101 := _t1921
		_t1922 := &pb.Monoid{}
		_t1922.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1101}
		_t1920 = _t1922
	} else {
		var _t1923 *pb.Monoid
		if prediction1097 == 2 {
			_t1924 := p.parse_max_monoid()
			max_monoid1100 := _t1924
			_t1925 := &pb.Monoid{}
			_t1925.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1100}
			_t1923 = _t1925
		} else {
			var _t1926 *pb.Monoid
			if prediction1097 == 1 {
				_t1927 := p.parse_min_monoid()
				min_monoid1099 := _t1927
				_t1928 := &pb.Monoid{}
				_t1928.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1099}
				_t1926 = _t1928
			} else {
				var _t1929 *pb.Monoid
				if prediction1097 == 0 {
					_t1930 := p.parse_or_monoid()
					or_monoid1098 := _t1930
					_t1931 := &pb.Monoid{}
					_t1931.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1098}
					_t1929 = _t1931
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1926 = _t1929
			}
			_t1923 = _t1926
		}
		_t1920 = _t1923
	}
	result1103 := _t1920
	p.recordSpan(int(span_start1102), "Monoid")
	return result1103
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1932 := &pb.OrMonoid{}
	result1105 := _t1932
	p.recordSpan(int(span_start1104), "OrMonoid")
	return result1105
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1933 := p.parse_type()
	type1106 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.MinMonoid{Type: type1106}
	result1108 := _t1934
	p.recordSpan(int(span_start1107), "MinMonoid")
	return result1108
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1110 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1935 := p.parse_type()
	type1109 := _t1935
	p.consumeLiteral(")")
	_t1936 := &pb.MaxMonoid{Type: type1109}
	result1111 := _t1936
	p.recordSpan(int(span_start1110), "MaxMonoid")
	return result1111
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1113 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1937 := p.parse_type()
	type1112 := _t1937
	p.consumeLiteral(")")
	_t1938 := &pb.SumMonoid{Type: type1112}
	result1114 := _t1938
	p.recordSpan(int(span_start1113), "SumMonoid")
	return result1114
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1119 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1939 := p.parse_monoid()
	monoid1115 := _t1939
	_t1940 := p.parse_relation_id()
	relation_id1116 := _t1940
	_t1941 := p.parse_abstraction_with_arity()
	abstraction_with_arity1117 := _t1941
	var _t1942 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1943 := p.parse_attrs()
		_t1942 = _t1943
	}
	attrs1118 := _t1942
	p.consumeLiteral(")")
	_t1944 := attrs1118
	if attrs1118 == nil {
		_t1944 = []*pb.Attribute{}
	}
	_t1945 := &pb.MonusDef{Monoid: monoid1115, Name: relation_id1116, Body: abstraction_with_arity1117[0].(*pb.Abstraction), Attrs: _t1944, ValueArity: abstraction_with_arity1117[1].(int64)}
	result1120 := _t1945
	p.recordSpan(int(span_start1119), "MonusDef")
	return result1120
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1946 := p.parse_relation_id()
	relation_id1121 := _t1946
	_t1947 := p.parse_abstraction()
	abstraction1122 := _t1947
	_t1948 := p.parse_functional_dependency_keys()
	functional_dependency_keys1123 := _t1948
	_t1949 := p.parse_functional_dependency_values()
	functional_dependency_values1124 := _t1949
	p.consumeLiteral(")")
	_t1950 := &pb.FunctionalDependency{Guard: abstraction1122, Keys: functional_dependency_keys1123, Values: functional_dependency_values1124}
	_t1951 := &pb.Constraint{Name: relation_id1121}
	_t1951.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1950}
	result1126 := _t1951
	p.recordSpan(int(span_start1125), "Constraint")
	return result1126
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1127 := []*pb.Var{}
	cond1128 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1128 {
		_t1952 := p.parse_var()
		item1129 := _t1952
		xs1127 = append(xs1127, item1129)
		cond1128 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1130 := xs1127
	p.consumeLiteral(")")
	return vars1130
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1131 := []*pb.Var{}
	cond1132 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1132 {
		_t1953 := p.parse_var()
		item1133 := _t1953
		xs1131 = append(xs1131, item1133)
		cond1132 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1134 := xs1131
	p.consumeLiteral(")")
	return vars1134
}

func (p *Parser) parse_data() *pb.Data {
	span_start1140 := int64(p.spanStart())
	var _t1954 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1955 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1955 = 3
		} else {
			var _t1956 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1956 = 0
			} else {
				var _t1957 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1957 = 2
				} else {
					var _t1958 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1958 = 1
					} else {
						_t1958 = -1
					}
					_t1957 = _t1958
				}
				_t1956 = _t1957
			}
			_t1955 = _t1956
		}
		_t1954 = _t1955
	} else {
		_t1954 = -1
	}
	prediction1135 := _t1954
	var _t1959 *pb.Data
	if prediction1135 == 3 {
		_t1960 := p.parse_iceberg_data()
		iceberg_data1139 := _t1960
		_t1961 := &pb.Data{}
		_t1961.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1139}
		_t1959 = _t1961
	} else {
		var _t1962 *pb.Data
		if prediction1135 == 2 {
			_t1963 := p.parse_csv_data()
			csv_data1138 := _t1963
			_t1964 := &pb.Data{}
			_t1964.DataType = &pb.Data_CsvData{CsvData: csv_data1138}
			_t1962 = _t1964
		} else {
			var _t1965 *pb.Data
			if prediction1135 == 1 {
				_t1966 := p.parse_betree_relation()
				betree_relation1137 := _t1966
				_t1967 := &pb.Data{}
				_t1967.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1137}
				_t1965 = _t1967
			} else {
				var _t1968 *pb.Data
				if prediction1135 == 0 {
					_t1969 := p.parse_edb()
					edb1136 := _t1969
					_t1970 := &pb.Data{}
					_t1970.DataType = &pb.Data_Edb{Edb: edb1136}
					_t1968 = _t1970
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1965 = _t1968
			}
			_t1962 = _t1965
		}
		_t1959 = _t1962
	}
	result1141 := _t1959
	p.recordSpan(int(span_start1140), "Data")
	return result1141
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1145 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1971 := p.parse_relation_id()
	relation_id1142 := _t1971
	_t1972 := p.parse_edb_path()
	edb_path1143 := _t1972
	_t1973 := p.parse_edb_types()
	edb_types1144 := _t1973
	p.consumeLiteral(")")
	_t1974 := &pb.EDB{TargetId: relation_id1142, Path: edb_path1143, Types: edb_types1144}
	result1146 := _t1974
	p.recordSpan(int(span_start1145), "EDB")
	return result1146
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1147 := []string{}
	cond1148 := p.matchLookaheadTerminal("STRING", 0)
	for cond1148 {
		item1149 := p.consumeTerminal("STRING").Value.str
		xs1147 = append(xs1147, item1149)
		cond1148 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1150 := xs1147
	p.consumeLiteral("]")
	return strings1150
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1151 := []*pb.Type{}
	cond1152 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1152 {
		_t1975 := p.parse_type()
		item1153 := _t1975
		xs1151 = append(xs1151, item1153)
		cond1152 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1154 := xs1151
	p.consumeLiteral("]")
	return types1154
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1976 := p.parse_relation_id()
	relation_id1155 := _t1976
	_t1977 := p.parse_betree_info()
	betree_info1156 := _t1977
	p.consumeLiteral(")")
	_t1978 := &pb.BeTreeRelation{Name: relation_id1155, RelationInfo: betree_info1156}
	result1158 := _t1978
	p.recordSpan(int(span_start1157), "BeTreeRelation")
	return result1158
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1162 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1979 := p.parse_betree_info_key_types()
	betree_info_key_types1159 := _t1979
	_t1980 := p.parse_betree_info_value_types()
	betree_info_value_types1160 := _t1980
	_t1981 := p.parse_config_dict()
	config_dict1161 := _t1981
	p.consumeLiteral(")")
	_t1982 := p.construct_betree_info(betree_info_key_types1159, betree_info_value_types1160, config_dict1161)
	result1163 := _t1982
	p.recordSpan(int(span_start1162), "BeTreeInfo")
	return result1163
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1164 := []*pb.Type{}
	cond1165 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1165 {
		_t1983 := p.parse_type()
		item1166 := _t1983
		xs1164 = append(xs1164, item1166)
		cond1165 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1167 := xs1164
	p.consumeLiteral(")")
	return types1167
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1168 := []*pb.Type{}
	cond1169 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1169 {
		_t1984 := p.parse_type()
		item1170 := _t1984
		xs1168 = append(xs1168, item1170)
		cond1169 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1171 := xs1168
	p.consumeLiteral(")")
	return types1171
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1177 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1985 := p.parse_csvlocator()
	csvlocator1172 := _t1985
	_t1986 := p.parse_csv_config()
	csv_config1173 := _t1986
	var _t1987 []*pb.GNFColumn
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("columns", 1)) {
		_t1988 := p.parse_gnf_columns()
		_t1987 = _t1988
	}
	gnf_columns1174 := _t1987
	var _t1989 *pb.CSVTarget
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("table", 1)) {
		_t1990 := p.parse_csv_table()
		_t1989 = _t1990
	}
	csv_table1175 := _t1989
	_t1991 := p.parse_csv_asof()
	csv_asof1176 := _t1991
	p.consumeLiteral(")")
	_t1992 := p.construct_csv_data(csvlocator1172, csv_config1173, gnf_columns1174, csv_table1175, csv_asof1176)
	result1178 := _t1992
	p.recordSpan(int(span_start1177), "CSVData")
	return result1178
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1181 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1993 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1994 := p.parse_csv_locator_paths()
		_t1993 = _t1994
	}
	csv_locator_paths1179 := _t1993
	var _t1995 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1996 := p.parse_csv_locator_inline_data()
		_t1995 = ptr(_t1996)
	}
	csv_locator_inline_data1180 := _t1995
	p.consumeLiteral(")")
	_t1997 := csv_locator_paths1179
	if csv_locator_paths1179 == nil {
		_t1997 = []string{}
	}
	_t1998 := &pb.CSVLocator{Paths: _t1997, InlineData: []byte(deref(csv_locator_inline_data1180, ""))}
	result1182 := _t1998
	p.recordSpan(int(span_start1181), "CSVLocator")
	return result1182
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1183 := []string{}
	cond1184 := p.matchLookaheadTerminal("STRING", 0)
	for cond1184 {
		item1185 := p.consumeTerminal("STRING").Value.str
		xs1183 = append(xs1183, item1185)
		cond1184 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1186 := xs1183
	p.consumeLiteral(")")
	return strings1186
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1187 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1187
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1999 := p.parse_config_dict()
	config_dict1188 := _t1999
	p.consumeLiteral(")")
	_t2000 := p.construct_csv_config(config_dict1188)
	result1190 := _t2000
	p.recordSpan(int(span_start1189), "CSVConfig")
	return result1190
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1191 := []*pb.GNFColumn{}
	cond1192 := p.matchLookaheadLiteral("(", 0)
	for cond1192 {
		_t2001 := p.parse_gnf_column()
		item1193 := _t2001
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
	_t2002 := p.parse_gnf_column_path()
	gnf_column_path1195 := _t2002
	var _t2003 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t2004 := p.parse_relation_id()
		_t2003 = _t2004
	}
	relation_id1196 := _t2003
	p.consumeLiteral("[")
	xs1197 := []*pb.Type{}
	cond1198 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1198 {
		_t2005 := p.parse_type()
		item1199 := _t2005
		xs1197 = append(xs1197, item1199)
		cond1198 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1200 := xs1197
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2006 := &pb.GNFColumn{ColumnPath: gnf_column_path1195, TargetId: relation_id1196, Types: types1200}
	result1202 := _t2006
	p.recordSpan(int(span_start1201), "GNFColumn")
	return result1202
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t2007 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t2007 = 1
	} else {
		var _t2008 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t2008 = 0
		} else {
			_t2008 = -1
		}
		_t2007 = _t2008
	}
	prediction1203 := _t2007
	var _t2009 []string
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
		_t2009 = strings1208
	} else {
		var _t2010 []string
		if prediction1203 == 0 {
			string1204 := p.consumeTerminal("STRING").Value.str
			_ = string1204
			_t2010 = []string{string1204}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2009 = _t2010
	}
	return _t2009
}

func (p *Parser) parse_csv_table() *pb.CSVTarget {
	span_start1218 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table")
	_t2011 := p.parse_relation_id()
	relation_id1209 := _t2011
	p.consumeLiteral("[")
	xs1210 := []string{}
	cond1211 := p.matchLookaheadTerminal("STRING", 0)
	for cond1211 {
		item1212 := p.consumeTerminal("STRING").Value.str
		xs1210 = append(xs1210, item1212)
		cond1211 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1213 := xs1210
	p.consumeLiteral("]")
	p.consumeLiteral("[")
	xs1214 := []*pb.Type{}
	cond1215 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1215 {
		_t2012 := p.parse_type()
		item1216 := _t2012
		xs1214 = append(xs1214, item1216)
		cond1215 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1217 := xs1214
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t2013 := &pb.CSVTarget{TargetId: relation_id1209, ColumnNames: strings1213, Types: types1217}
	result1219 := _t2013
	p.recordSpan(int(span_start1218), "CSVTarget")
	return result1219
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1220 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1220
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1227 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t2014 := p.parse_iceberg_locator()
	iceberg_locator1221 := _t2014
	_t2015 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1222 := _t2015
	_t2016 := p.parse_gnf_columns()
	gnf_columns1223 := _t2016
	var _t2017 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t2018 := p.parse_iceberg_from_snapshot()
		_t2017 = ptr(_t2018)
	}
	iceberg_from_snapshot1224 := _t2017
	var _t2019 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2020 := p.parse_iceberg_to_snapshot()
		_t2019 = ptr(_t2020)
	}
	iceberg_to_snapshot1225 := _t2019
	_t2021 := p.parse_boolean_value()
	boolean_value1226 := _t2021
	p.consumeLiteral(")")
	_t2022 := p.construct_iceberg_data(iceberg_locator1221, iceberg_catalog_config1222, gnf_columns1223, iceberg_from_snapshot1224, iceberg_to_snapshot1225, boolean_value1226)
	result1228 := _t2022
	p.recordSpan(int(span_start1227), "IcebergData")
	return result1228
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1232 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2023 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1229 := _t2023
	_t2024 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1230 := _t2024
	_t2025 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1231 := _t2025
	p.consumeLiteral(")")
	_t2026 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1229, Namespace: iceberg_locator_namespace1230, Warehouse: iceberg_locator_warehouse1231}
	result1233 := _t2026
	p.recordSpan(int(span_start1232), "IcebergLocator")
	return result1233
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1234 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1234
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1235 := []string{}
	cond1236 := p.matchLookaheadTerminal("STRING", 0)
	for cond1236 {
		item1237 := p.consumeTerminal("STRING").Value.str
		xs1235 = append(xs1235, item1237)
		cond1236 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1238 := xs1235
	p.consumeLiteral(")")
	return strings1238
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1239 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1239
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1244 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2027 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1240 := _t2027
	var _t2028 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2029 := p.parse_iceberg_catalog_config_scope()
		_t2028 = ptr(_t2029)
	}
	iceberg_catalog_config_scope1241 := _t2028
	_t2030 := p.parse_iceberg_properties()
	iceberg_properties1242 := _t2030
	_t2031 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1243 := _t2031
	p.consumeLiteral(")")
	_t2032 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1240, iceberg_catalog_config_scope1241, iceberg_properties1242, iceberg_auth_properties1243)
	result1245 := _t2032
	p.recordSpan(int(span_start1244), "IcebergCatalogConfig")
	return result1245
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1246 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1246
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1247 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1247
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1248 := [][]interface{}{}
	cond1249 := p.matchLookaheadLiteral("(", 0)
	for cond1249 {
		_t2033 := p.parse_iceberg_property_entry()
		item1250 := _t2033
		xs1248 = append(xs1248, item1250)
		cond1249 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1251 := xs1248
	p.consumeLiteral(")")
	return iceberg_property_entrys1251
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1252 := p.consumeTerminal("STRING").Value.str
	string_31253 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1252, string_31253}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1254 := [][]interface{}{}
	cond1255 := p.matchLookaheadLiteral("(", 0)
	for cond1255 {
		_t2034 := p.parse_iceberg_masked_property_entry()
		item1256 := _t2034
		xs1254 = append(xs1254, item1256)
		cond1255 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1257 := xs1254
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1257
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1258 := p.consumeTerminal("STRING").Value.str
	string_31259 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1258, string_31259}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1260 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1260
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1261 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1261
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1263 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2035 := p.parse_fragment_id()
	fragment_id1262 := _t2035
	p.consumeLiteral(")")
	_t2036 := &pb.Undefine{FragmentId: fragment_id1262}
	result1264 := _t2036
	p.recordSpan(int(span_start1263), "Undefine")
	return result1264
}

func (p *Parser) parse_context() *pb.Context {
	span_start1269 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1265 := []*pb.RelationId{}
	cond1266 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1266 {
		_t2037 := p.parse_relation_id()
		item1267 := _t2037
		xs1265 = append(xs1265, item1267)
		cond1266 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1268 := xs1265
	p.consumeLiteral(")")
	_t2038 := &pb.Context{Relations: relation_ids1268}
	result1270 := _t2038
	p.recordSpan(int(span_start1269), "Context")
	return result1270
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1276 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2039 := p.parse_edb_path()
	edb_path1271 := _t2039
	xs1272 := []*pb.SnapshotMapping{}
	cond1273 := p.matchLookaheadLiteral("[", 0)
	for cond1273 {
		_t2040 := p.parse_snapshot_mapping()
		item1274 := _t2040
		xs1272 = append(xs1272, item1274)
		cond1273 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1275 := xs1272
	p.consumeLiteral(")")
	_t2041 := &pb.Snapshot{Prefix: edb_path1271, Mappings: snapshot_mappings1275}
	result1277 := _t2041
	p.recordSpan(int(span_start1276), "Snapshot")
	return result1277
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1280 := int64(p.spanStart())
	_t2042 := p.parse_edb_path()
	edb_path1278 := _t2042
	_t2043 := p.parse_relation_id()
	relation_id1279 := _t2043
	_t2044 := &pb.SnapshotMapping{DestinationPath: edb_path1278, SourceRelation: relation_id1279}
	result1281 := _t2044
	p.recordSpan(int(span_start1280), "SnapshotMapping")
	return result1281
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1282 := []*pb.Read{}
	cond1283 := p.matchLookaheadLiteral("(", 0)
	for cond1283 {
		_t2045 := p.parse_read()
		item1284 := _t2045
		xs1282 = append(xs1282, item1284)
		cond1283 = p.matchLookaheadLiteral("(", 0)
	}
	reads1285 := xs1282
	p.consumeLiteral(")")
	return reads1285
}

func (p *Parser) parse_read() *pb.Read {
	span_start1292 := int64(p.spanStart())
	var _t2046 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2047 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2047 = 2
		} else {
			var _t2048 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2048 = 1
			} else {
				var _t2049 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2049 = 4
				} else {
					var _t2050 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2050 = 4
					} else {
						var _t2051 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2051 = 0
						} else {
							var _t2052 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2052 = 3
							} else {
								_t2052 = -1
							}
							_t2051 = _t2052
						}
						_t2050 = _t2051
					}
					_t2049 = _t2050
				}
				_t2048 = _t2049
			}
			_t2047 = _t2048
		}
		_t2046 = _t2047
	} else {
		_t2046 = -1
	}
	prediction1286 := _t2046
	var _t2053 *pb.Read
	if prediction1286 == 4 {
		_t2054 := p.parse_export()
		export1291 := _t2054
		_t2055 := &pb.Read{}
		_t2055.ReadType = &pb.Read_Export{Export: export1291}
		_t2053 = _t2055
	} else {
		var _t2056 *pb.Read
		if prediction1286 == 3 {
			_t2057 := p.parse_abort()
			abort1290 := _t2057
			_t2058 := &pb.Read{}
			_t2058.ReadType = &pb.Read_Abort{Abort: abort1290}
			_t2056 = _t2058
		} else {
			var _t2059 *pb.Read
			if prediction1286 == 2 {
				_t2060 := p.parse_what_if()
				what_if1289 := _t2060
				_t2061 := &pb.Read{}
				_t2061.ReadType = &pb.Read_WhatIf{WhatIf: what_if1289}
				_t2059 = _t2061
			} else {
				var _t2062 *pb.Read
				if prediction1286 == 1 {
					_t2063 := p.parse_output()
					output1288 := _t2063
					_t2064 := &pb.Read{}
					_t2064.ReadType = &pb.Read_Output{Output: output1288}
					_t2062 = _t2064
				} else {
					var _t2065 *pb.Read
					if prediction1286 == 0 {
						_t2066 := p.parse_demand()
						demand1287 := _t2066
						_t2067 := &pb.Read{}
						_t2067.ReadType = &pb.Read_Demand{Demand: demand1287}
						_t2065 = _t2067
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2062 = _t2065
				}
				_t2059 = _t2062
			}
			_t2056 = _t2059
		}
		_t2053 = _t2056
	}
	result1293 := _t2053
	p.recordSpan(int(span_start1292), "Read")
	return result1293
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1295 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2068 := p.parse_relation_id()
	relation_id1294 := _t2068
	p.consumeLiteral(")")
	_t2069 := &pb.Demand{RelationId: relation_id1294}
	result1296 := _t2069
	p.recordSpan(int(span_start1295), "Demand")
	return result1296
}

func (p *Parser) parse_output() *pb.Output {
	span_start1299 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2070 := p.parse_name()
	name1297 := _t2070
	_t2071 := p.parse_relation_id()
	relation_id1298 := _t2071
	p.consumeLiteral(")")
	_t2072 := &pb.Output{Name: name1297, RelationId: relation_id1298}
	result1300 := _t2072
	p.recordSpan(int(span_start1299), "Output")
	return result1300
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1303 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2073 := p.parse_name()
	name1301 := _t2073
	_t2074 := p.parse_epoch()
	epoch1302 := _t2074
	p.consumeLiteral(")")
	_t2075 := &pb.WhatIf{Branch: name1301, Epoch: epoch1302}
	result1304 := _t2075
	p.recordSpan(int(span_start1303), "WhatIf")
	return result1304
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1307 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2076 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2077 := p.parse_name()
		_t2076 = ptr(_t2077)
	}
	name1305 := _t2076
	_t2078 := p.parse_relation_id()
	relation_id1306 := _t2078
	p.consumeLiteral(")")
	_t2079 := &pb.Abort{Name: deref(name1305, "abort"), RelationId: relation_id1306}
	result1308 := _t2079
	p.recordSpan(int(span_start1307), "Abort")
	return result1308
}

func (p *Parser) parse_export() *pb.Export {
	span_start1312 := int64(p.spanStart())
	var _t2080 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2081 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2081 = 1
		} else {
			var _t2082 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2082 = 0
			} else {
				_t2082 = -1
			}
			_t2081 = _t2082
		}
		_t2080 = _t2081
	} else {
		_t2080 = -1
	}
	prediction1309 := _t2080
	var _t2083 *pb.Export
	if prediction1309 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2084 := p.parse_export_iceberg_config()
		export_iceberg_config1311 := _t2084
		p.consumeLiteral(")")
		_t2085 := &pb.Export{}
		_t2085.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1311}
		_t2083 = _t2085
	} else {
		var _t2086 *pb.Export
		if prediction1309 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2087 := p.parse_export_csv_config()
			export_csv_config1310 := _t2087
			p.consumeLiteral(")")
			_t2088 := &pb.Export{}
			_t2088.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1310}
			_t2086 = _t2088
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2083 = _t2086
	}
	result1313 := _t2083
	p.recordSpan(int(span_start1312), "Export")
	return result1313
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1321 := int64(p.spanStart())
	var _t2089 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2090 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2090 = 0
		} else {
			var _t2091 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2091 = 1
			} else {
				_t2091 = -1
			}
			_t2090 = _t2091
		}
		_t2089 = _t2090
	} else {
		_t2089 = -1
	}
	prediction1314 := _t2089
	var _t2092 *pb.ExportCSVConfig
	if prediction1314 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2093 := p.parse_export_csv_path()
		export_csv_path1318 := _t2093
		_t2094 := p.parse_export_csv_columns_list()
		export_csv_columns_list1319 := _t2094
		_t2095 := p.parse_config_dict()
		config_dict1320 := _t2095
		p.consumeLiteral(")")
		_t2096 := p.construct_export_csv_config(export_csv_path1318, export_csv_columns_list1319, config_dict1320)
		_t2092 = _t2096
	} else {
		var _t2097 *pb.ExportCSVConfig
		if prediction1314 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2098 := p.parse_export_csv_path()
			export_csv_path1315 := _t2098
			_t2099 := p.parse_export_csv_source()
			export_csv_source1316 := _t2099
			_t2100 := p.parse_csv_config()
			csv_config1317 := _t2100
			p.consumeLiteral(")")
			_t2101 := p.construct_export_csv_config_with_source(export_csv_path1315, export_csv_source1316, csv_config1317)
			_t2097 = _t2101
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2092 = _t2097
	}
	result1322 := _t2092
	p.recordSpan(int(span_start1321), "ExportCSVConfig")
	return result1322
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1323 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1323
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1330 := int64(p.spanStart())
	var _t2102 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2103 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2103 = 1
		} else {
			var _t2104 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2104 = 0
			} else {
				_t2104 = -1
			}
			_t2103 = _t2104
		}
		_t2102 = _t2103
	} else {
		_t2102 = -1
	}
	prediction1324 := _t2102
	var _t2105 *pb.ExportCSVSource
	if prediction1324 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2106 := p.parse_relation_id()
		relation_id1329 := _t2106
		p.consumeLiteral(")")
		_t2107 := &pb.ExportCSVSource{}
		_t2107.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1329}
		_t2105 = _t2107
	} else {
		var _t2108 *pb.ExportCSVSource
		if prediction1324 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1325 := []*pb.ExportCSVColumn{}
			cond1326 := p.matchLookaheadLiteral("(", 0)
			for cond1326 {
				_t2109 := p.parse_export_csv_column()
				item1327 := _t2109
				xs1325 = append(xs1325, item1327)
				cond1326 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1328 := xs1325
			p.consumeLiteral(")")
			_t2110 := &pb.ExportCSVColumns{Columns: export_csv_columns1328}
			_t2111 := &pb.ExportCSVSource{}
			_t2111.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2110}
			_t2108 = _t2111
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2105 = _t2108
	}
	result1331 := _t2105
	p.recordSpan(int(span_start1330), "ExportCSVSource")
	return result1331
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1334 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1332 := p.consumeTerminal("STRING").Value.str
	_t2112 := p.parse_relation_id()
	relation_id1333 := _t2112
	p.consumeLiteral(")")
	_t2113 := &pb.ExportCSVColumn{ColumnName: string1332, ColumnData: relation_id1333}
	result1335 := _t2113
	p.recordSpan(int(span_start1334), "ExportCSVColumn")
	return result1335
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1336 := []*pb.ExportCSVColumn{}
	cond1337 := p.matchLookaheadLiteral("(", 0)
	for cond1337 {
		_t2114 := p.parse_export_csv_column()
		item1338 := _t2114
		xs1336 = append(xs1336, item1338)
		cond1337 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1339 := xs1336
	p.consumeLiteral(")")
	return export_csv_columns1339
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1345 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2115 := p.parse_iceberg_locator()
	iceberg_locator1340 := _t2115
	_t2116 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1341 := _t2116
	_t2117 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1342 := _t2117
	_t2118 := p.parse_iceberg_table_properties()
	iceberg_table_properties1343 := _t2118
	var _t2119 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2120 := p.parse_config_dict()
		_t2119 = _t2120
	}
	config_dict1344 := _t2119
	p.consumeLiteral(")")
	_t2121 := p.construct_export_iceberg_config_full(iceberg_locator1340, iceberg_catalog_config1341, export_iceberg_table_def1342, iceberg_table_properties1343, config_dict1344)
	result1346 := _t2121
	p.recordSpan(int(span_start1345), "ExportIcebergConfig")
	return result1346
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1348 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2122 := p.parse_relation_id()
	relation_id1347 := _t2122
	p.consumeLiteral(")")
	result1349 := relation_id1347
	p.recordSpan(int(span_start1348), "RelationId")
	return result1349
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1350 := [][]interface{}{}
	cond1351 := p.matchLookaheadLiteral("(", 0)
	for cond1351 {
		_t2123 := p.parse_iceberg_property_entry()
		item1352 := _t2123
		xs1350 = append(xs1350, item1352)
		cond1351 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1353 := xs1350
	p.consumeLiteral(")")
	return iceberg_property_entrys1353
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
