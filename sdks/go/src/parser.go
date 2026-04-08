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
	var _t2106 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2106
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2107 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2107
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2108 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2108
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2109 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2109
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2110 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2110
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2111 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2111
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2112 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2112
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2113 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2113
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2114 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2114
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2115 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2115
	_t2116 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2116
	_t2117 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2117
	_t2118 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2118
	_t2119 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2119
	_t2120 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2120
	_t2121 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2121
	_t2122 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2122
	_t2123 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2123
	_t2124 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2124
	_t2125 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2125
	_t2126 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2126
	_t2127 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2127
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2128 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2128
	_t2129 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2129
	_t2130 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2130
	_t2131 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2131
	_t2132 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2132
	_t2133 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2133
	_t2134 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2134
	_t2135 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2135
	_t2136 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2136
	_t2137 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2137.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2137.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2137
	_t2138 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2138
}

func (p *Parser) default_configure() *pb.Configure {
	_t2139 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2139
	_t2140 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2140
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
	_t2141 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2141
	_t2142 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2142
	_t2143 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2143
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2144 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2144
	_t2145 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2145
	_t2146 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2146
	_t2147 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2147
	_t2148 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2148
	_t2149 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2149
	_t2150 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2150
	_t2151 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2151
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2152 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2152
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2153 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2153
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2154 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2154
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2155 := config_dict
	if config_dict == nil {
		_t2155 = [][]interface{}{}
	}
	cfg := dictFromList(_t2155)
	_t2156 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2156
	_t2157 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2157
	_t2158 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2158
	table_props := stringMapFromPairs(table_property_pairs)
	_t2159 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2159
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start678 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1344 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1345 := p.parse_configure()
		_t1344 = _t1345
	}
	configure672 := _t1344
	var _t1346 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1347 := p.parse_sync()
		_t1346 = _t1347
	}
	sync673 := _t1346
	xs674 := []*pb.Epoch{}
	cond675 := p.matchLookaheadLiteral("(", 0)
	for cond675 {
		_t1348 := p.parse_epoch()
		item676 := _t1348
		xs674 = append(xs674, item676)
		cond675 = p.matchLookaheadLiteral("(", 0)
	}
	epochs677 := xs674
	p.consumeLiteral(")")
	_t1349 := p.default_configure()
	_t1350 := configure672
	if configure672 == nil {
		_t1350 = _t1349
	}
	_t1351 := &pb.Transaction{Epochs: epochs677, Configure: _t1350, Sync: sync673}
	result679 := _t1351
	p.recordSpan(int(span_start678), "Transaction")
	return result679
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start681 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1352 := p.parse_config_dict()
	config_dict680 := _t1352
	p.consumeLiteral(")")
	_t1353 := p.construct_configure(config_dict680)
	result682 := _t1353
	p.recordSpan(int(span_start681), "Configure")
	return result682
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs683 := [][]interface{}{}
	cond684 := p.matchLookaheadLiteral(":", 0)
	for cond684 {
		_t1354 := p.parse_config_key_value()
		item685 := _t1354
		xs683 = append(xs683, item685)
		cond684 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values686 := xs683
	p.consumeLiteral("}")
	return config_key_values686
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol687 := p.consumeTerminal("SYMBOL").Value.str
	_t1355 := p.parse_raw_value()
	raw_value688 := _t1355
	return []interface{}{symbol687, raw_value688}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start702 := int64(p.spanStart())
	var _t1356 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1356 = 12
	} else {
		var _t1357 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1357 = 11
		} else {
			var _t1358 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1358 = 12
			} else {
				var _t1359 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1360 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1360 = 1
					} else {
						var _t1361 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1361 = 0
						} else {
							_t1361 = -1
						}
						_t1360 = _t1361
					}
					_t1359 = _t1360
				} else {
					var _t1362 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1362 = 7
					} else {
						var _t1363 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1363 = 8
						} else {
							var _t1364 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1364 = 2
							} else {
								var _t1365 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1365 = 3
								} else {
									var _t1366 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1366 = 9
									} else {
										var _t1367 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1367 = 4
										} else {
											var _t1368 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1368 = 5
											} else {
												var _t1369 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1369 = 6
												} else {
													var _t1370 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1370 = 10
													} else {
														_t1370 = -1
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
							_t1363 = _t1364
						}
						_t1362 = _t1363
					}
					_t1359 = _t1362
				}
				_t1358 = _t1359
			}
			_t1357 = _t1358
		}
		_t1356 = _t1357
	}
	prediction689 := _t1356
	var _t1371 *pb.Value
	if prediction689 == 12 {
		_t1372 := p.parse_boolean_value()
		boolean_value701 := _t1372
		_t1373 := &pb.Value{}
		_t1373.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value701}
		_t1371 = _t1373
	} else {
		var _t1374 *pb.Value
		if prediction689 == 11 {
			p.consumeLiteral("missing")
			_t1375 := &pb.MissingValue{}
			_t1376 := &pb.Value{}
			_t1376.Value = &pb.Value_MissingValue{MissingValue: _t1375}
			_t1374 = _t1376
		} else {
			var _t1377 *pb.Value
			if prediction689 == 10 {
				decimal700 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1378 := &pb.Value{}
				_t1378.Value = &pb.Value_DecimalValue{DecimalValue: decimal700}
				_t1377 = _t1378
			} else {
				var _t1379 *pb.Value
				if prediction689 == 9 {
					int128699 := p.consumeTerminal("INT128").Value.int128
					_t1380 := &pb.Value{}
					_t1380.Value = &pb.Value_Int128Value{Int128Value: int128699}
					_t1379 = _t1380
				} else {
					var _t1381 *pb.Value
					if prediction689 == 8 {
						uint128698 := p.consumeTerminal("UINT128").Value.uint128
						_t1382 := &pb.Value{}
						_t1382.Value = &pb.Value_Uint128Value{Uint128Value: uint128698}
						_t1381 = _t1382
					} else {
						var _t1383 *pb.Value
						if prediction689 == 7 {
							uint32697 := p.consumeTerminal("UINT32").Value.u32
							_t1384 := &pb.Value{}
							_t1384.Value = &pb.Value_Uint32Value{Uint32Value: uint32697}
							_t1383 = _t1384
						} else {
							var _t1385 *pb.Value
							if prediction689 == 6 {
								float696 := p.consumeTerminal("FLOAT").Value.f64
								_t1386 := &pb.Value{}
								_t1386.Value = &pb.Value_FloatValue{FloatValue: float696}
								_t1385 = _t1386
							} else {
								var _t1387 *pb.Value
								if prediction689 == 5 {
									float32695 := p.consumeTerminal("FLOAT32").Value.f32
									_t1388 := &pb.Value{}
									_t1388.Value = &pb.Value_Float32Value{Float32Value: float32695}
									_t1387 = _t1388
								} else {
									var _t1389 *pb.Value
									if prediction689 == 4 {
										int694 := p.consumeTerminal("INT").Value.i64
										_t1390 := &pb.Value{}
										_t1390.Value = &pb.Value_IntValue{IntValue: int694}
										_t1389 = _t1390
									} else {
										var _t1391 *pb.Value
										if prediction689 == 3 {
											int32693 := p.consumeTerminal("INT32").Value.i32
											_t1392 := &pb.Value{}
											_t1392.Value = &pb.Value_Int32Value{Int32Value: int32693}
											_t1391 = _t1392
										} else {
											var _t1393 *pb.Value
											if prediction689 == 2 {
												string692 := p.consumeTerminal("STRING").Value.str
												_t1394 := &pb.Value{}
												_t1394.Value = &pb.Value_StringValue{StringValue: string692}
												_t1393 = _t1394
											} else {
												var _t1395 *pb.Value
												if prediction689 == 1 {
													_t1396 := p.parse_raw_datetime()
													raw_datetime691 := _t1396
													_t1397 := &pb.Value{}
													_t1397.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime691}
													_t1395 = _t1397
												} else {
													var _t1398 *pb.Value
													if prediction689 == 0 {
														_t1399 := p.parse_raw_date()
														raw_date690 := _t1399
														_t1400 := &pb.Value{}
														_t1400.Value = &pb.Value_DateValue{DateValue: raw_date690}
														_t1398 = _t1400
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1395 = _t1398
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
				_t1377 = _t1379
			}
			_t1374 = _t1377
		}
		_t1371 = _t1374
	}
	result703 := _t1371
	p.recordSpan(int(span_start702), "Value")
	return result703
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int704 := p.consumeTerminal("INT").Value.i64
	int_3705 := p.consumeTerminal("INT").Value.i64
	int_4706 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1401 := &pb.DateValue{Year: int32(int704), Month: int32(int_3705), Day: int32(int_4706)}
	result708 := _t1401
	p.recordSpan(int(span_start707), "DateValue")
	return result708
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start716 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int709 := p.consumeTerminal("INT").Value.i64
	int_3710 := p.consumeTerminal("INT").Value.i64
	int_4711 := p.consumeTerminal("INT").Value.i64
	int_5712 := p.consumeTerminal("INT").Value.i64
	int_6713 := p.consumeTerminal("INT").Value.i64
	int_7714 := p.consumeTerminal("INT").Value.i64
	var _t1402 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1402 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8715 := _t1402
	p.consumeLiteral(")")
	_t1403 := &pb.DateTimeValue{Year: int32(int709), Month: int32(int_3710), Day: int32(int_4711), Hour: int32(int_5712), Minute: int32(int_6713), Second: int32(int_7714), Microsecond: int32(deref(int_8715, 0))}
	result717 := _t1403
	p.recordSpan(int(span_start716), "DateTimeValue")
	return result717
}

func (p *Parser) parse_boolean_value() bool {
	var _t1404 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1404 = 0
	} else {
		var _t1405 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1405 = 1
		} else {
			_t1405 = -1
		}
		_t1404 = _t1405
	}
	prediction718 := _t1404
	var _t1406 bool
	if prediction718 == 1 {
		p.consumeLiteral("false")
		_t1406 = false
	} else {
		var _t1407 bool
		if prediction718 == 0 {
			p.consumeLiteral("true")
			_t1407 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1406 = _t1407
	}
	return _t1406
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs719 := []*pb.FragmentId{}
	cond720 := p.matchLookaheadLiteral(":", 0)
	for cond720 {
		_t1408 := p.parse_fragment_id()
		item721 := _t1408
		xs719 = append(xs719, item721)
		cond720 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids722 := xs719
	p.consumeLiteral(")")
	_t1409 := &pb.Sync{Fragments: fragment_ids722}
	result724 := _t1409
	p.recordSpan(int(span_start723), "Sync")
	return result724
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start726 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol725 := p.consumeTerminal("SYMBOL").Value.str
	result727 := &pb.FragmentId{Id: []byte(symbol725)}
	p.recordSpan(int(span_start726), "FragmentId")
	return result727
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start730 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1410 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1411 := p.parse_epoch_writes()
		_t1410 = _t1411
	}
	epoch_writes728 := _t1410
	var _t1412 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1413 := p.parse_epoch_reads()
		_t1412 = _t1413
	}
	epoch_reads729 := _t1412
	p.consumeLiteral(")")
	_t1414 := epoch_writes728
	if epoch_writes728 == nil {
		_t1414 = []*pb.Write{}
	}
	_t1415 := epoch_reads729
	if epoch_reads729 == nil {
		_t1415 = []*pb.Read{}
	}
	_t1416 := &pb.Epoch{Writes: _t1414, Reads: _t1415}
	result731 := _t1416
	p.recordSpan(int(span_start730), "Epoch")
	return result731
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs732 := []*pb.Write{}
	cond733 := p.matchLookaheadLiteral("(", 0)
	for cond733 {
		_t1417 := p.parse_write()
		item734 := _t1417
		xs732 = append(xs732, item734)
		cond733 = p.matchLookaheadLiteral("(", 0)
	}
	writes735 := xs732
	p.consumeLiteral(")")
	return writes735
}

func (p *Parser) parse_write() *pb.Write {
	span_start741 := int64(p.spanStart())
	var _t1418 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1419 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1419 = 1
		} else {
			var _t1420 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1420 = 3
			} else {
				var _t1421 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1421 = 0
				} else {
					var _t1422 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1422 = 2
					} else {
						_t1422 = -1
					}
					_t1421 = _t1422
				}
				_t1420 = _t1421
			}
			_t1419 = _t1420
		}
		_t1418 = _t1419
	} else {
		_t1418 = -1
	}
	prediction736 := _t1418
	var _t1423 *pb.Write
	if prediction736 == 3 {
		_t1424 := p.parse_snapshot()
		snapshot740 := _t1424
		_t1425 := &pb.Write{}
		_t1425.WriteType = &pb.Write_Snapshot{Snapshot: snapshot740}
		_t1423 = _t1425
	} else {
		var _t1426 *pb.Write
		if prediction736 == 2 {
			_t1427 := p.parse_context()
			context739 := _t1427
			_t1428 := &pb.Write{}
			_t1428.WriteType = &pb.Write_Context{Context: context739}
			_t1426 = _t1428
		} else {
			var _t1429 *pb.Write
			if prediction736 == 1 {
				_t1430 := p.parse_undefine()
				undefine738 := _t1430
				_t1431 := &pb.Write{}
				_t1431.WriteType = &pb.Write_Undefine{Undefine: undefine738}
				_t1429 = _t1431
			} else {
				var _t1432 *pb.Write
				if prediction736 == 0 {
					_t1433 := p.parse_define()
					define737 := _t1433
					_t1434 := &pb.Write{}
					_t1434.WriteType = &pb.Write_Define{Define: define737}
					_t1432 = _t1434
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1429 = _t1432
			}
			_t1426 = _t1429
		}
		_t1423 = _t1426
	}
	result742 := _t1423
	p.recordSpan(int(span_start741), "Write")
	return result742
}

func (p *Parser) parse_define() *pb.Define {
	span_start744 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1435 := p.parse_fragment()
	fragment743 := _t1435
	p.consumeLiteral(")")
	_t1436 := &pb.Define{Fragment: fragment743}
	result745 := _t1436
	p.recordSpan(int(span_start744), "Define")
	return result745
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1437 := p.parse_new_fragment_id()
	new_fragment_id746 := _t1437
	xs747 := []*pb.Declaration{}
	cond748 := p.matchLookaheadLiteral("(", 0)
	for cond748 {
		_t1438 := p.parse_declaration()
		item749 := _t1438
		xs747 = append(xs747, item749)
		cond748 = p.matchLookaheadLiteral("(", 0)
	}
	declarations750 := xs747
	p.consumeLiteral(")")
	result752 := p.constructFragment(new_fragment_id746, declarations750)
	p.recordSpan(int(span_start751), "Fragment")
	return result752
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start754 := int64(p.spanStart())
	_t1439 := p.parse_fragment_id()
	fragment_id753 := _t1439
	p.startFragment(fragment_id753)
	result755 := fragment_id753
	p.recordSpan(int(span_start754), "FragmentId")
	return result755
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start761 := int64(p.spanStart())
	var _t1440 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1441 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1441 = 3
		} else {
			var _t1442 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1442 = 2
			} else {
				var _t1443 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1443 = 3
				} else {
					var _t1444 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1444 = 0
					} else {
						var _t1445 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1445 = 3
						} else {
							var _t1446 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1446 = 3
							} else {
								var _t1447 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1447 = 1
								} else {
									_t1447 = -1
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
			}
			_t1441 = _t1442
		}
		_t1440 = _t1441
	} else {
		_t1440 = -1
	}
	prediction756 := _t1440
	var _t1448 *pb.Declaration
	if prediction756 == 3 {
		_t1449 := p.parse_data()
		data760 := _t1449
		_t1450 := &pb.Declaration{}
		_t1450.DeclarationType = &pb.Declaration_Data{Data: data760}
		_t1448 = _t1450
	} else {
		var _t1451 *pb.Declaration
		if prediction756 == 2 {
			_t1452 := p.parse_constraint()
			constraint759 := _t1452
			_t1453 := &pb.Declaration{}
			_t1453.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint759}
			_t1451 = _t1453
		} else {
			var _t1454 *pb.Declaration
			if prediction756 == 1 {
				_t1455 := p.parse_algorithm()
				algorithm758 := _t1455
				_t1456 := &pb.Declaration{}
				_t1456.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm758}
				_t1454 = _t1456
			} else {
				var _t1457 *pb.Declaration
				if prediction756 == 0 {
					_t1458 := p.parse_def()
					def757 := _t1458
					_t1459 := &pb.Declaration{}
					_t1459.DeclarationType = &pb.Declaration_Def{Def: def757}
					_t1457 = _t1459
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1454 = _t1457
			}
			_t1451 = _t1454
		}
		_t1448 = _t1451
	}
	result762 := _t1448
	p.recordSpan(int(span_start761), "Declaration")
	return result762
}

func (p *Parser) parse_def() *pb.Def {
	span_start766 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1460 := p.parse_relation_id()
	relation_id763 := _t1460
	_t1461 := p.parse_abstraction()
	abstraction764 := _t1461
	var _t1462 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1463 := p.parse_attrs()
		_t1462 = _t1463
	}
	attrs765 := _t1462
	p.consumeLiteral(")")
	_t1464 := attrs765
	if attrs765 == nil {
		_t1464 = []*pb.Attribute{}
	}
	_t1465 := &pb.Def{Name: relation_id763, Body: abstraction764, Attrs: _t1464}
	result767 := _t1465
	p.recordSpan(int(span_start766), "Def")
	return result767
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start771 := int64(p.spanStart())
	var _t1466 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1466 = 0
	} else {
		var _t1467 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1467 = 1
		} else {
			_t1467 = -1
		}
		_t1466 = _t1467
	}
	prediction768 := _t1466
	var _t1468 *pb.RelationId
	if prediction768 == 1 {
		uint128770 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128770
		_t1468 = &pb.RelationId{IdLow: uint128770.Low, IdHigh: uint128770.High}
	} else {
		var _t1469 *pb.RelationId
		if prediction768 == 0 {
			p.consumeLiteral(":")
			symbol769 := p.consumeTerminal("SYMBOL").Value.str
			_t1469 = p.relationIdFromString(symbol769)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1468 = _t1469
	}
	result772 := _t1468
	p.recordSpan(int(span_start771), "RelationId")
	return result772
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start775 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1470 := p.parse_bindings()
	bindings773 := _t1470
	_t1471 := p.parse_formula()
	formula774 := _t1471
	p.consumeLiteral(")")
	_t1472 := &pb.Abstraction{Vars: listConcat(bindings773[0].([]*pb.Binding), bindings773[1].([]*pb.Binding)), Value: formula774}
	result776 := _t1472
	p.recordSpan(int(span_start775), "Abstraction")
	return result776
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs777 := []*pb.Binding{}
	cond778 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond778 {
		_t1473 := p.parse_binding()
		item779 := _t1473
		xs777 = append(xs777, item779)
		cond778 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings780 := xs777
	var _t1474 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1475 := p.parse_value_bindings()
		_t1474 = _t1475
	}
	value_bindings781 := _t1474
	p.consumeLiteral("]")
	_t1476 := value_bindings781
	if value_bindings781 == nil {
		_t1476 = []*pb.Binding{}
	}
	return []interface{}{bindings780, _t1476}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start784 := int64(p.spanStart())
	symbol782 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1477 := p.parse_type()
	type783 := _t1477
	_t1478 := &pb.Var{Name: symbol782}
	_t1479 := &pb.Binding{Var: _t1478, Type: type783}
	result785 := _t1479
	p.recordSpan(int(span_start784), "Binding")
	return result785
}

func (p *Parser) parse_type() *pb.Type {
	span_start801 := int64(p.spanStart())
	var _t1480 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1480 = 0
	} else {
		var _t1481 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1481 = 13
		} else {
			var _t1482 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1482 = 4
			} else {
				var _t1483 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1483 = 1
				} else {
					var _t1484 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1484 = 8
					} else {
						var _t1485 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1485 = 11
						} else {
							var _t1486 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1486 = 5
							} else {
								var _t1487 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1487 = 2
								} else {
									var _t1488 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1488 = 12
									} else {
										var _t1489 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1489 = 3
										} else {
											var _t1490 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1490 = 7
											} else {
												var _t1491 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1491 = 6
												} else {
													var _t1492 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1492 = 10
													} else {
														var _t1493 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1493 = 9
														} else {
															_t1493 = -1
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
			_t1481 = _t1482
		}
		_t1480 = _t1481
	}
	prediction786 := _t1480
	var _t1494 *pb.Type
	if prediction786 == 13 {
		_t1495 := p.parse_uint32_type()
		uint32_type800 := _t1495
		_t1496 := &pb.Type{}
		_t1496.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type800}
		_t1494 = _t1496
	} else {
		var _t1497 *pb.Type
		if prediction786 == 12 {
			_t1498 := p.parse_float32_type()
			float32_type799 := _t1498
			_t1499 := &pb.Type{}
			_t1499.Type = &pb.Type_Float32Type{Float32Type: float32_type799}
			_t1497 = _t1499
		} else {
			var _t1500 *pb.Type
			if prediction786 == 11 {
				_t1501 := p.parse_int32_type()
				int32_type798 := _t1501
				_t1502 := &pb.Type{}
				_t1502.Type = &pb.Type_Int32Type{Int32Type: int32_type798}
				_t1500 = _t1502
			} else {
				var _t1503 *pb.Type
				if prediction786 == 10 {
					_t1504 := p.parse_boolean_type()
					boolean_type797 := _t1504
					_t1505 := &pb.Type{}
					_t1505.Type = &pb.Type_BooleanType{BooleanType: boolean_type797}
					_t1503 = _t1505
				} else {
					var _t1506 *pb.Type
					if prediction786 == 9 {
						_t1507 := p.parse_decimal_type()
						decimal_type796 := _t1507
						_t1508 := &pb.Type{}
						_t1508.Type = &pb.Type_DecimalType{DecimalType: decimal_type796}
						_t1506 = _t1508
					} else {
						var _t1509 *pb.Type
						if prediction786 == 8 {
							_t1510 := p.parse_missing_type()
							missing_type795 := _t1510
							_t1511 := &pb.Type{}
							_t1511.Type = &pb.Type_MissingType{MissingType: missing_type795}
							_t1509 = _t1511
						} else {
							var _t1512 *pb.Type
							if prediction786 == 7 {
								_t1513 := p.parse_datetime_type()
								datetime_type794 := _t1513
								_t1514 := &pb.Type{}
								_t1514.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type794}
								_t1512 = _t1514
							} else {
								var _t1515 *pb.Type
								if prediction786 == 6 {
									_t1516 := p.parse_date_type()
									date_type793 := _t1516
									_t1517 := &pb.Type{}
									_t1517.Type = &pb.Type_DateType{DateType: date_type793}
									_t1515 = _t1517
								} else {
									var _t1518 *pb.Type
									if prediction786 == 5 {
										_t1519 := p.parse_int128_type()
										int128_type792 := _t1519
										_t1520 := &pb.Type{}
										_t1520.Type = &pb.Type_Int128Type{Int128Type: int128_type792}
										_t1518 = _t1520
									} else {
										var _t1521 *pb.Type
										if prediction786 == 4 {
											_t1522 := p.parse_uint128_type()
											uint128_type791 := _t1522
											_t1523 := &pb.Type{}
											_t1523.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type791}
											_t1521 = _t1523
										} else {
											var _t1524 *pb.Type
											if prediction786 == 3 {
												_t1525 := p.parse_float_type()
												float_type790 := _t1525
												_t1526 := &pb.Type{}
												_t1526.Type = &pb.Type_FloatType{FloatType: float_type790}
												_t1524 = _t1526
											} else {
												var _t1527 *pb.Type
												if prediction786 == 2 {
													_t1528 := p.parse_int_type()
													int_type789 := _t1528
													_t1529 := &pb.Type{}
													_t1529.Type = &pb.Type_IntType{IntType: int_type789}
													_t1527 = _t1529
												} else {
													var _t1530 *pb.Type
													if prediction786 == 1 {
														_t1531 := p.parse_string_type()
														string_type788 := _t1531
														_t1532 := &pb.Type{}
														_t1532.Type = &pb.Type_StringType{StringType: string_type788}
														_t1530 = _t1532
													} else {
														var _t1533 *pb.Type
														if prediction786 == 0 {
															_t1534 := p.parse_unspecified_type()
															unspecified_type787 := _t1534
															_t1535 := &pb.Type{}
															_t1535.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type787}
															_t1533 = _t1535
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1497 = _t1500
		}
		_t1494 = _t1497
	}
	result802 := _t1494
	p.recordSpan(int(span_start801), "Type")
	return result802
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1536 := &pb.UnspecifiedType{}
	result804 := _t1536
	p.recordSpan(int(span_start803), "UnspecifiedType")
	return result804
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1537 := &pb.StringType{}
	result806 := _t1537
	p.recordSpan(int(span_start805), "StringType")
	return result806
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1538 := &pb.IntType{}
	result808 := _t1538
	p.recordSpan(int(span_start807), "IntType")
	return result808
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1539 := &pb.FloatType{}
	result810 := _t1539
	p.recordSpan(int(span_start809), "FloatType")
	return result810
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1540 := &pb.UInt128Type{}
	result812 := _t1540
	p.recordSpan(int(span_start811), "UInt128Type")
	return result812
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1541 := &pb.Int128Type{}
	result814 := _t1541
	p.recordSpan(int(span_start813), "Int128Type")
	return result814
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1542 := &pb.DateType{}
	result816 := _t1542
	p.recordSpan(int(span_start815), "DateType")
	return result816
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1543 := &pb.DateTimeType{}
	result818 := _t1543
	p.recordSpan(int(span_start817), "DateTimeType")
	return result818
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1544 := &pb.MissingType{}
	result820 := _t1544
	p.recordSpan(int(span_start819), "MissingType")
	return result820
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start823 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int821 := p.consumeTerminal("INT").Value.i64
	int_3822 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1545 := &pb.DecimalType{Precision: int32(int821), Scale: int32(int_3822)}
	result824 := _t1545
	p.recordSpan(int(span_start823), "DecimalType")
	return result824
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start825 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1546 := &pb.BooleanType{}
	result826 := _t1546
	p.recordSpan(int(span_start825), "BooleanType")
	return result826
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start827 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1547 := &pb.Int32Type{}
	result828 := _t1547
	p.recordSpan(int(span_start827), "Int32Type")
	return result828
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1548 := &pb.Float32Type{}
	result830 := _t1548
	p.recordSpan(int(span_start829), "Float32Type")
	return result830
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start831 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1549 := &pb.UInt32Type{}
	result832 := _t1549
	p.recordSpan(int(span_start831), "UInt32Type")
	return result832
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs833 := []*pb.Binding{}
	cond834 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond834 {
		_t1550 := p.parse_binding()
		item835 := _t1550
		xs833 = append(xs833, item835)
		cond834 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings836 := xs833
	return bindings836
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start851 := int64(p.spanStart())
	var _t1551 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1552 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1552 = 0
		} else {
			var _t1553 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1553 = 11
			} else {
				var _t1554 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1554 = 3
				} else {
					var _t1555 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1555 = 10
					} else {
						var _t1556 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1556 = 9
						} else {
							var _t1557 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1557 = 5
							} else {
								var _t1558 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1558 = 6
								} else {
									var _t1559 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1559 = 7
									} else {
										var _t1560 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1560 = 1
										} else {
											var _t1561 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1561 = 2
											} else {
												var _t1562 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1562 = 12
												} else {
													var _t1563 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1563 = 8
													} else {
														var _t1564 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1564 = 4
														} else {
															var _t1565 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1565 = 10
															} else {
																var _t1566 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1566 = 10
																} else {
																	var _t1567 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1567 = 10
																	} else {
																		var _t1568 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1568 = 10
																		} else {
																			var _t1569 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1569 = 10
																			} else {
																				var _t1570 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1570 = 10
																				} else {
																					var _t1571 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1571 = 10
																					} else {
																						var _t1572 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1572 = 10
																						} else {
																							var _t1573 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1573 = 10
																							} else {
																								_t1573 = -1
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
			}
			_t1552 = _t1553
		}
		_t1551 = _t1552
	} else {
		_t1551 = -1
	}
	prediction837 := _t1551
	var _t1574 *pb.Formula
	if prediction837 == 12 {
		_t1575 := p.parse_cast()
		cast850 := _t1575
		_t1576 := &pb.Formula{}
		_t1576.FormulaType = &pb.Formula_Cast{Cast: cast850}
		_t1574 = _t1576
	} else {
		var _t1577 *pb.Formula
		if prediction837 == 11 {
			_t1578 := p.parse_rel_atom()
			rel_atom849 := _t1578
			_t1579 := &pb.Formula{}
			_t1579.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom849}
			_t1577 = _t1579
		} else {
			var _t1580 *pb.Formula
			if prediction837 == 10 {
				_t1581 := p.parse_primitive()
				primitive848 := _t1581
				_t1582 := &pb.Formula{}
				_t1582.FormulaType = &pb.Formula_Primitive{Primitive: primitive848}
				_t1580 = _t1582
			} else {
				var _t1583 *pb.Formula
				if prediction837 == 9 {
					_t1584 := p.parse_pragma()
					pragma847 := _t1584
					_t1585 := &pb.Formula{}
					_t1585.FormulaType = &pb.Formula_Pragma{Pragma: pragma847}
					_t1583 = _t1585
				} else {
					var _t1586 *pb.Formula
					if prediction837 == 8 {
						_t1587 := p.parse_atom()
						atom846 := _t1587
						_t1588 := &pb.Formula{}
						_t1588.FormulaType = &pb.Formula_Atom{Atom: atom846}
						_t1586 = _t1588
					} else {
						var _t1589 *pb.Formula
						if prediction837 == 7 {
							_t1590 := p.parse_ffi()
							ffi845 := _t1590
							_t1591 := &pb.Formula{}
							_t1591.FormulaType = &pb.Formula_Ffi{Ffi: ffi845}
							_t1589 = _t1591
						} else {
							var _t1592 *pb.Formula
							if prediction837 == 6 {
								_t1593 := p.parse_not()
								not844 := _t1593
								_t1594 := &pb.Formula{}
								_t1594.FormulaType = &pb.Formula_Not{Not: not844}
								_t1592 = _t1594
							} else {
								var _t1595 *pb.Formula
								if prediction837 == 5 {
									_t1596 := p.parse_disjunction()
									disjunction843 := _t1596
									_t1597 := &pb.Formula{}
									_t1597.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction843}
									_t1595 = _t1597
								} else {
									var _t1598 *pb.Formula
									if prediction837 == 4 {
										_t1599 := p.parse_conjunction()
										conjunction842 := _t1599
										_t1600 := &pb.Formula{}
										_t1600.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction842}
										_t1598 = _t1600
									} else {
										var _t1601 *pb.Formula
										if prediction837 == 3 {
											_t1602 := p.parse_reduce()
											reduce841 := _t1602
											_t1603 := &pb.Formula{}
											_t1603.FormulaType = &pb.Formula_Reduce{Reduce: reduce841}
											_t1601 = _t1603
										} else {
											var _t1604 *pb.Formula
											if prediction837 == 2 {
												_t1605 := p.parse_exists()
												exists840 := _t1605
												_t1606 := &pb.Formula{}
												_t1606.FormulaType = &pb.Formula_Exists{Exists: exists840}
												_t1604 = _t1606
											} else {
												var _t1607 *pb.Formula
												if prediction837 == 1 {
													_t1608 := p.parse_false()
													false839 := _t1608
													_t1609 := &pb.Formula{}
													_t1609.FormulaType = &pb.Formula_Disjunction{Disjunction: false839}
													_t1607 = _t1609
												} else {
													var _t1610 *pb.Formula
													if prediction837 == 0 {
														_t1611 := p.parse_true()
														true838 := _t1611
														_t1612 := &pb.Formula{}
														_t1612.FormulaType = &pb.Formula_Conjunction{Conjunction: true838}
														_t1610 = _t1612
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1577 = _t1580
		}
		_t1574 = _t1577
	}
	result852 := _t1574
	p.recordSpan(int(span_start851), "Formula")
	return result852
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1613 := &pb.Conjunction{Args: []*pb.Formula{}}
	result854 := _t1613
	p.recordSpan(int(span_start853), "Conjunction")
	return result854
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start855 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1614 := &pb.Disjunction{Args: []*pb.Formula{}}
	result856 := _t1614
	p.recordSpan(int(span_start855), "Disjunction")
	return result856
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1615 := p.parse_bindings()
	bindings857 := _t1615
	_t1616 := p.parse_formula()
	formula858 := _t1616
	p.consumeLiteral(")")
	_t1617 := &pb.Abstraction{Vars: listConcat(bindings857[0].([]*pb.Binding), bindings857[1].([]*pb.Binding)), Value: formula858}
	_t1618 := &pb.Exists{Body: _t1617}
	result860 := _t1618
	p.recordSpan(int(span_start859), "Exists")
	return result860
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1619 := p.parse_abstraction()
	abstraction861 := _t1619
	_t1620 := p.parse_abstraction()
	abstraction_3862 := _t1620
	_t1621 := p.parse_terms()
	terms863 := _t1621
	p.consumeLiteral(")")
	_t1622 := &pb.Reduce{Op: abstraction861, Body: abstraction_3862, Terms: terms863}
	result865 := _t1622
	p.recordSpan(int(span_start864), "Reduce")
	return result865
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs866 := []*pb.Term{}
	cond867 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond867 {
		_t1623 := p.parse_term()
		item868 := _t1623
		xs866 = append(xs866, item868)
		cond867 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms869 := xs866
	p.consumeLiteral(")")
	return terms869
}

func (p *Parser) parse_term() *pb.Term {
	span_start873 := int64(p.spanStart())
	var _t1624 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1624 = 1
	} else {
		var _t1625 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1625 = 1
		} else {
			var _t1626 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1626 = 1
			} else {
				var _t1627 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1627 = 1
				} else {
					var _t1628 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1628 = 0
					} else {
						var _t1629 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1629 = 1
						} else {
							var _t1630 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1630 = 1
							} else {
								var _t1631 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1631 = 1
								} else {
									var _t1632 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1632 = 1
									} else {
										var _t1633 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1633 = 1
										} else {
											var _t1634 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1634 = 1
											} else {
												var _t1635 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1635 = 1
												} else {
													var _t1636 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1636 = 1
													} else {
														var _t1637 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1637 = 1
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
	prediction870 := _t1624
	var _t1638 *pb.Term
	if prediction870 == 1 {
		_t1639 := p.parse_value()
		value872 := _t1639
		_t1640 := &pb.Term{}
		_t1640.TermType = &pb.Term_Constant{Constant: value872}
		_t1638 = _t1640
	} else {
		var _t1641 *pb.Term
		if prediction870 == 0 {
			_t1642 := p.parse_var()
			var871 := _t1642
			_t1643 := &pb.Term{}
			_t1643.TermType = &pb.Term_Var{Var: var871}
			_t1641 = _t1643
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1638 = _t1641
	}
	result874 := _t1638
	p.recordSpan(int(span_start873), "Term")
	return result874
}

func (p *Parser) parse_var() *pb.Var {
	span_start876 := int64(p.spanStart())
	symbol875 := p.consumeTerminal("SYMBOL").Value.str
	_t1644 := &pb.Var{Name: symbol875}
	result877 := _t1644
	p.recordSpan(int(span_start876), "Var")
	return result877
}

func (p *Parser) parse_value() *pb.Value {
	span_start891 := int64(p.spanStart())
	var _t1645 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1645 = 12
	} else {
		var _t1646 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1646 = 11
		} else {
			var _t1647 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1647 = 12
			} else {
				var _t1648 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1649 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1649 = 1
					} else {
						var _t1650 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1650 = 0
						} else {
							_t1650 = -1
						}
						_t1649 = _t1650
					}
					_t1648 = _t1649
				} else {
					var _t1651 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1651 = 7
					} else {
						var _t1652 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1652 = 8
						} else {
							var _t1653 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1653 = 2
							} else {
								var _t1654 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1654 = 3
								} else {
									var _t1655 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1655 = 9
									} else {
										var _t1656 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1656 = 4
										} else {
											var _t1657 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1657 = 5
											} else {
												var _t1658 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1658 = 6
												} else {
													var _t1659 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1659 = 10
													} else {
														_t1659 = -1
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
							_t1652 = _t1653
						}
						_t1651 = _t1652
					}
					_t1648 = _t1651
				}
				_t1647 = _t1648
			}
			_t1646 = _t1647
		}
		_t1645 = _t1646
	}
	prediction878 := _t1645
	var _t1660 *pb.Value
	if prediction878 == 12 {
		_t1661 := p.parse_boolean_value()
		boolean_value890 := _t1661
		_t1662 := &pb.Value{}
		_t1662.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value890}
		_t1660 = _t1662
	} else {
		var _t1663 *pb.Value
		if prediction878 == 11 {
			p.consumeLiteral("missing")
			_t1664 := &pb.MissingValue{}
			_t1665 := &pb.Value{}
			_t1665.Value = &pb.Value_MissingValue{MissingValue: _t1664}
			_t1663 = _t1665
		} else {
			var _t1666 *pb.Value
			if prediction878 == 10 {
				formatted_decimal889 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1667 := &pb.Value{}
				_t1667.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal889}
				_t1666 = _t1667
			} else {
				var _t1668 *pb.Value
				if prediction878 == 9 {
					formatted_int128888 := p.consumeTerminal("INT128").Value.int128
					_t1669 := &pb.Value{}
					_t1669.Value = &pb.Value_Int128Value{Int128Value: formatted_int128888}
					_t1668 = _t1669
				} else {
					var _t1670 *pb.Value
					if prediction878 == 8 {
						formatted_uint128887 := p.consumeTerminal("UINT128").Value.uint128
						_t1671 := &pb.Value{}
						_t1671.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128887}
						_t1670 = _t1671
					} else {
						var _t1672 *pb.Value
						if prediction878 == 7 {
							formatted_uint32886 := p.consumeTerminal("UINT32").Value.u32
							_t1673 := &pb.Value{}
							_t1673.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32886}
							_t1672 = _t1673
						} else {
							var _t1674 *pb.Value
							if prediction878 == 6 {
								formatted_float885 := p.consumeTerminal("FLOAT").Value.f64
								_t1675 := &pb.Value{}
								_t1675.Value = &pb.Value_FloatValue{FloatValue: formatted_float885}
								_t1674 = _t1675
							} else {
								var _t1676 *pb.Value
								if prediction878 == 5 {
									formatted_float32884 := p.consumeTerminal("FLOAT32").Value.f32
									_t1677 := &pb.Value{}
									_t1677.Value = &pb.Value_Float32Value{Float32Value: formatted_float32884}
									_t1676 = _t1677
								} else {
									var _t1678 *pb.Value
									if prediction878 == 4 {
										formatted_int883 := p.consumeTerminal("INT").Value.i64
										_t1679 := &pb.Value{}
										_t1679.Value = &pb.Value_IntValue{IntValue: formatted_int883}
										_t1678 = _t1679
									} else {
										var _t1680 *pb.Value
										if prediction878 == 3 {
											formatted_int32882 := p.consumeTerminal("INT32").Value.i32
											_t1681 := &pb.Value{}
											_t1681.Value = &pb.Value_Int32Value{Int32Value: formatted_int32882}
											_t1680 = _t1681
										} else {
											var _t1682 *pb.Value
											if prediction878 == 2 {
												formatted_string881 := p.consumeTerminal("STRING").Value.str
												_t1683 := &pb.Value{}
												_t1683.Value = &pb.Value_StringValue{StringValue: formatted_string881}
												_t1682 = _t1683
											} else {
												var _t1684 *pb.Value
												if prediction878 == 1 {
													_t1685 := p.parse_datetime()
													datetime880 := _t1685
													_t1686 := &pb.Value{}
													_t1686.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime880}
													_t1684 = _t1686
												} else {
													var _t1687 *pb.Value
													if prediction878 == 0 {
														_t1688 := p.parse_date()
														date879 := _t1688
														_t1689 := &pb.Value{}
														_t1689.Value = &pb.Value_DateValue{DateValue: date879}
														_t1687 = _t1689
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1684 = _t1687
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
				_t1666 = _t1668
			}
			_t1663 = _t1666
		}
		_t1660 = _t1663
	}
	result892 := _t1660
	p.recordSpan(int(span_start891), "Value")
	return result892
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int893 := p.consumeTerminal("INT").Value.i64
	formatted_int_3894 := p.consumeTerminal("INT").Value.i64
	formatted_int_4895 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1690 := &pb.DateValue{Year: int32(formatted_int893), Month: int32(formatted_int_3894), Day: int32(formatted_int_4895)}
	result897 := _t1690
	p.recordSpan(int(span_start896), "DateValue")
	return result897
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start905 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int898 := p.consumeTerminal("INT").Value.i64
	formatted_int_3899 := p.consumeTerminal("INT").Value.i64
	formatted_int_4900 := p.consumeTerminal("INT").Value.i64
	formatted_int_5901 := p.consumeTerminal("INT").Value.i64
	formatted_int_6902 := p.consumeTerminal("INT").Value.i64
	formatted_int_7903 := p.consumeTerminal("INT").Value.i64
	var _t1691 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1691 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8904 := _t1691
	p.consumeLiteral(")")
	_t1692 := &pb.DateTimeValue{Year: int32(formatted_int898), Month: int32(formatted_int_3899), Day: int32(formatted_int_4900), Hour: int32(formatted_int_5901), Minute: int32(formatted_int_6902), Second: int32(formatted_int_7903), Microsecond: int32(deref(formatted_int_8904, 0))}
	result906 := _t1692
	p.recordSpan(int(span_start905), "DateTimeValue")
	return result906
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start911 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs907 := []*pb.Formula{}
	cond908 := p.matchLookaheadLiteral("(", 0)
	for cond908 {
		_t1693 := p.parse_formula()
		item909 := _t1693
		xs907 = append(xs907, item909)
		cond908 = p.matchLookaheadLiteral("(", 0)
	}
	formulas910 := xs907
	p.consumeLiteral(")")
	_t1694 := &pb.Conjunction{Args: formulas910}
	result912 := _t1694
	p.recordSpan(int(span_start911), "Conjunction")
	return result912
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start917 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs913 := []*pb.Formula{}
	cond914 := p.matchLookaheadLiteral("(", 0)
	for cond914 {
		_t1695 := p.parse_formula()
		item915 := _t1695
		xs913 = append(xs913, item915)
		cond914 = p.matchLookaheadLiteral("(", 0)
	}
	formulas916 := xs913
	p.consumeLiteral(")")
	_t1696 := &pb.Disjunction{Args: formulas916}
	result918 := _t1696
	p.recordSpan(int(span_start917), "Disjunction")
	return result918
}

func (p *Parser) parse_not() *pb.Not {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1697 := p.parse_formula()
	formula919 := _t1697
	p.consumeLiteral(")")
	_t1698 := &pb.Not{Arg: formula919}
	result921 := _t1698
	p.recordSpan(int(span_start920), "Not")
	return result921
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start925 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1699 := p.parse_name()
	name922 := _t1699
	_t1700 := p.parse_ffi_args()
	ffi_args923 := _t1700
	_t1701 := p.parse_terms()
	terms924 := _t1701
	p.consumeLiteral(")")
	_t1702 := &pb.FFI{Name: name922, Args: ffi_args923, Terms: terms924}
	result926 := _t1702
	p.recordSpan(int(span_start925), "FFI")
	return result926
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol927 := p.consumeTerminal("SYMBOL").Value.str
	return symbol927
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs928 := []*pb.Abstraction{}
	cond929 := p.matchLookaheadLiteral("(", 0)
	for cond929 {
		_t1703 := p.parse_abstraction()
		item930 := _t1703
		xs928 = append(xs928, item930)
		cond929 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions931 := xs928
	p.consumeLiteral(")")
	return abstractions931
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start937 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1704 := p.parse_relation_id()
	relation_id932 := _t1704
	xs933 := []*pb.Term{}
	cond934 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond934 {
		_t1705 := p.parse_term()
		item935 := _t1705
		xs933 = append(xs933, item935)
		cond934 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms936 := xs933
	p.consumeLiteral(")")
	_t1706 := &pb.Atom{Name: relation_id932, Terms: terms936}
	result938 := _t1706
	p.recordSpan(int(span_start937), "Atom")
	return result938
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start944 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1707 := p.parse_name()
	name939 := _t1707
	xs940 := []*pb.Term{}
	cond941 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond941 {
		_t1708 := p.parse_term()
		item942 := _t1708
		xs940 = append(xs940, item942)
		cond941 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms943 := xs940
	p.consumeLiteral(")")
	_t1709 := &pb.Pragma{Name: name939, Terms: terms943}
	result945 := _t1709
	p.recordSpan(int(span_start944), "Pragma")
	return result945
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start961 := int64(p.spanStart())
	var _t1710 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1711 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1711 = 9
		} else {
			var _t1712 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1712 = 4
			} else {
				var _t1713 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1713 = 3
				} else {
					var _t1714 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1714 = 0
					} else {
						var _t1715 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1715 = 2
						} else {
							var _t1716 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1716 = 1
							} else {
								var _t1717 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1717 = 8
								} else {
									var _t1718 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1718 = 6
									} else {
										var _t1719 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1719 = 5
										} else {
											var _t1720 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1720 = 7
											} else {
												_t1720 = -1
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
			}
			_t1711 = _t1712
		}
		_t1710 = _t1711
	} else {
		_t1710 = -1
	}
	prediction946 := _t1710
	var _t1721 *pb.Primitive
	if prediction946 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1722 := p.parse_name()
		name956 := _t1722
		xs957 := []*pb.RelTerm{}
		cond958 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond958 {
			_t1723 := p.parse_rel_term()
			item959 := _t1723
			xs957 = append(xs957, item959)
			cond958 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms960 := xs957
		p.consumeLiteral(")")
		_t1724 := &pb.Primitive{Name: name956, Terms: rel_terms960}
		_t1721 = _t1724
	} else {
		var _t1725 *pb.Primitive
		if prediction946 == 8 {
			_t1726 := p.parse_divide()
			divide955 := _t1726
			_t1725 = divide955
		} else {
			var _t1727 *pb.Primitive
			if prediction946 == 7 {
				_t1728 := p.parse_multiply()
				multiply954 := _t1728
				_t1727 = multiply954
			} else {
				var _t1729 *pb.Primitive
				if prediction946 == 6 {
					_t1730 := p.parse_minus()
					minus953 := _t1730
					_t1729 = minus953
				} else {
					var _t1731 *pb.Primitive
					if prediction946 == 5 {
						_t1732 := p.parse_add()
						add952 := _t1732
						_t1731 = add952
					} else {
						var _t1733 *pb.Primitive
						if prediction946 == 4 {
							_t1734 := p.parse_gt_eq()
							gt_eq951 := _t1734
							_t1733 = gt_eq951
						} else {
							var _t1735 *pb.Primitive
							if prediction946 == 3 {
								_t1736 := p.parse_gt()
								gt950 := _t1736
								_t1735 = gt950
							} else {
								var _t1737 *pb.Primitive
								if prediction946 == 2 {
									_t1738 := p.parse_lt_eq()
									lt_eq949 := _t1738
									_t1737 = lt_eq949
								} else {
									var _t1739 *pb.Primitive
									if prediction946 == 1 {
										_t1740 := p.parse_lt()
										lt948 := _t1740
										_t1739 = lt948
									} else {
										var _t1741 *pb.Primitive
										if prediction946 == 0 {
											_t1742 := p.parse_eq()
											eq947 := _t1742
											_t1741 = eq947
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1725 = _t1727
		}
		_t1721 = _t1725
	}
	result962 := _t1721
	p.recordSpan(int(span_start961), "Primitive")
	return result962
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1743 := p.parse_term()
	term963 := _t1743
	_t1744 := p.parse_term()
	term_3964 := _t1744
	p.consumeLiteral(")")
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term963}
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term_3964}
	_t1747 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1745, _t1746}}
	result966 := _t1747
	p.recordSpan(int(span_start965), "Primitive")
	return result966
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1748 := p.parse_term()
	term967 := _t1748
	_t1749 := p.parse_term()
	term_3968 := _t1749
	p.consumeLiteral(")")
	_t1750 := &pb.RelTerm{}
	_t1750.RelTermType = &pb.RelTerm_Term{Term: term967}
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term_3968}
	_t1752 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1750, _t1751}}
	result970 := _t1752
	p.recordSpan(int(span_start969), "Primitive")
	return result970
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start973 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1753 := p.parse_term()
	term971 := _t1753
	_t1754 := p.parse_term()
	term_3972 := _t1754
	p.consumeLiteral(")")
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term971}
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term_3972}
	_t1757 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1755, _t1756}}
	result974 := _t1757
	p.recordSpan(int(span_start973), "Primitive")
	return result974
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start977 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1758 := p.parse_term()
	term975 := _t1758
	_t1759 := p.parse_term()
	term_3976 := _t1759
	p.consumeLiteral(")")
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term975}
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term_3976}
	_t1762 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1760, _t1761}}
	result978 := _t1762
	p.recordSpan(int(span_start977), "Primitive")
	return result978
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start981 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1763 := p.parse_term()
	term979 := _t1763
	_t1764 := p.parse_term()
	term_3980 := _t1764
	p.consumeLiteral(")")
	_t1765 := &pb.RelTerm{}
	_t1765.RelTermType = &pb.RelTerm_Term{Term: term979}
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term_3980}
	_t1767 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1765, _t1766}}
	result982 := _t1767
	p.recordSpan(int(span_start981), "Primitive")
	return result982
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1768 := p.parse_term()
	term983 := _t1768
	_t1769 := p.parse_term()
	term_3984 := _t1769
	_t1770 := p.parse_term()
	term_4985 := _t1770
	p.consumeLiteral(")")
	_t1771 := &pb.RelTerm{}
	_t1771.RelTermType = &pb.RelTerm_Term{Term: term983}
	_t1772 := &pb.RelTerm{}
	_t1772.RelTermType = &pb.RelTerm_Term{Term: term_3984}
	_t1773 := &pb.RelTerm{}
	_t1773.RelTermType = &pb.RelTerm_Term{Term: term_4985}
	_t1774 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1771, _t1772, _t1773}}
	result987 := _t1774
	p.recordSpan(int(span_start986), "Primitive")
	return result987
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start991 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1775 := p.parse_term()
	term988 := _t1775
	_t1776 := p.parse_term()
	term_3989 := _t1776
	_t1777 := p.parse_term()
	term_4990 := _t1777
	p.consumeLiteral(")")
	_t1778 := &pb.RelTerm{}
	_t1778.RelTermType = &pb.RelTerm_Term{Term: term988}
	_t1779 := &pb.RelTerm{}
	_t1779.RelTermType = &pb.RelTerm_Term{Term: term_3989}
	_t1780 := &pb.RelTerm{}
	_t1780.RelTermType = &pb.RelTerm_Term{Term: term_4990}
	_t1781 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1778, _t1779, _t1780}}
	result992 := _t1781
	p.recordSpan(int(span_start991), "Primitive")
	return result992
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start996 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1782 := p.parse_term()
	term993 := _t1782
	_t1783 := p.parse_term()
	term_3994 := _t1783
	_t1784 := p.parse_term()
	term_4995 := _t1784
	p.consumeLiteral(")")
	_t1785 := &pb.RelTerm{}
	_t1785.RelTermType = &pb.RelTerm_Term{Term: term993}
	_t1786 := &pb.RelTerm{}
	_t1786.RelTermType = &pb.RelTerm_Term{Term: term_3994}
	_t1787 := &pb.RelTerm{}
	_t1787.RelTermType = &pb.RelTerm_Term{Term: term_4995}
	_t1788 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1785, _t1786, _t1787}}
	result997 := _t1788
	p.recordSpan(int(span_start996), "Primitive")
	return result997
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1001 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1789 := p.parse_term()
	term998 := _t1789
	_t1790 := p.parse_term()
	term_3999 := _t1790
	_t1791 := p.parse_term()
	term_41000 := _t1791
	p.consumeLiteral(")")
	_t1792 := &pb.RelTerm{}
	_t1792.RelTermType = &pb.RelTerm_Term{Term: term998}
	_t1793 := &pb.RelTerm{}
	_t1793.RelTermType = &pb.RelTerm_Term{Term: term_3999}
	_t1794 := &pb.RelTerm{}
	_t1794.RelTermType = &pb.RelTerm_Term{Term: term_41000}
	_t1795 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1792, _t1793, _t1794}}
	result1002 := _t1795
	p.recordSpan(int(span_start1001), "Primitive")
	return result1002
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1006 := int64(p.spanStart())
	var _t1796 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1796 = 1
	} else {
		var _t1797 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1797 = 1
		} else {
			var _t1798 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1798 = 1
			} else {
				var _t1799 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1799 = 1
				} else {
					var _t1800 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1800 = 0
					} else {
						var _t1801 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1801 = 1
						} else {
							var _t1802 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1802 = 1
							} else {
								var _t1803 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1803 = 1
								} else {
									var _t1804 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1804 = 1
									} else {
										var _t1805 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1805 = 1
										} else {
											var _t1806 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1806 = 1
											} else {
												var _t1807 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1807 = 1
												} else {
													var _t1808 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1808 = 1
													} else {
														var _t1809 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1809 = 1
														} else {
															var _t1810 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1810 = 1
															} else {
																_t1810 = -1
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
			_t1797 = _t1798
		}
		_t1796 = _t1797
	}
	prediction1003 := _t1796
	var _t1811 *pb.RelTerm
	if prediction1003 == 1 {
		_t1812 := p.parse_term()
		term1005 := _t1812
		_t1813 := &pb.RelTerm{}
		_t1813.RelTermType = &pb.RelTerm_Term{Term: term1005}
		_t1811 = _t1813
	} else {
		var _t1814 *pb.RelTerm
		if prediction1003 == 0 {
			_t1815 := p.parse_specialized_value()
			specialized_value1004 := _t1815
			_t1816 := &pb.RelTerm{}
			_t1816.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1004}
			_t1814 = _t1816
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1811 = _t1814
	}
	result1007 := _t1811
	p.recordSpan(int(span_start1006), "RelTerm")
	return result1007
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1817 := p.parse_raw_value()
	raw_value1008 := _t1817
	result1010 := raw_value1008
	p.recordSpan(int(span_start1009), "Value")
	return result1010
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1016 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1818 := p.parse_name()
	name1011 := _t1818
	xs1012 := []*pb.RelTerm{}
	cond1013 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1013 {
		_t1819 := p.parse_rel_term()
		item1014 := _t1819
		xs1012 = append(xs1012, item1014)
		cond1013 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1015 := xs1012
	p.consumeLiteral(")")
	_t1820 := &pb.RelAtom{Name: name1011, Terms: rel_terms1015}
	result1017 := _t1820
	p.recordSpan(int(span_start1016), "RelAtom")
	return result1017
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1020 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1821 := p.parse_term()
	term1018 := _t1821
	_t1822 := p.parse_term()
	term_31019 := _t1822
	p.consumeLiteral(")")
	_t1823 := &pb.Cast{Input: term1018, Result: term_31019}
	result1021 := _t1823
	p.recordSpan(int(span_start1020), "Cast")
	return result1021
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1022 := []*pb.Attribute{}
	cond1023 := p.matchLookaheadLiteral("(", 0)
	for cond1023 {
		_t1824 := p.parse_attribute()
		item1024 := _t1824
		xs1022 = append(xs1022, item1024)
		cond1023 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1025 := xs1022
	p.consumeLiteral(")")
	return attributes1025
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1825 := p.parse_name()
	name1026 := _t1825
	xs1027 := []*pb.Value{}
	cond1028 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1028 {
		_t1826 := p.parse_raw_value()
		item1029 := _t1826
		xs1027 = append(xs1027, item1029)
		cond1028 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1030 := xs1027
	p.consumeLiteral(")")
	_t1827 := &pb.Attribute{Name: name1026, Args: raw_values1030}
	result1032 := _t1827
	p.recordSpan(int(span_start1031), "Attribute")
	return result1032
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1033 := []*pb.RelationId{}
	cond1034 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1034 {
		_t1828 := p.parse_relation_id()
		item1035 := _t1828
		xs1033 = append(xs1033, item1035)
		cond1034 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1036 := xs1033
	_t1829 := p.parse_script()
	script1037 := _t1829
	p.consumeLiteral(")")
	_t1830 := &pb.Algorithm{Global: relation_ids1036, Body: script1037}
	result1039 := _t1830
	p.recordSpan(int(span_start1038), "Algorithm")
	return result1039
}

func (p *Parser) parse_script() *pb.Script {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1040 := []*pb.Construct{}
	cond1041 := p.matchLookaheadLiteral("(", 0)
	for cond1041 {
		_t1831 := p.parse_construct()
		item1042 := _t1831
		xs1040 = append(xs1040, item1042)
		cond1041 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1043 := xs1040
	p.consumeLiteral(")")
	_t1832 := &pb.Script{Constructs: constructs1043}
	result1045 := _t1832
	p.recordSpan(int(span_start1044), "Script")
	return result1045
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1049 := int64(p.spanStart())
	var _t1833 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1834 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1834 = 1
		} else {
			var _t1835 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1835 = 1
			} else {
				var _t1836 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1836 = 1
				} else {
					var _t1837 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1837 = 0
					} else {
						var _t1838 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1838 = 1
						} else {
							var _t1839 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1839 = 1
							} else {
								_t1839 = -1
							}
							_t1838 = _t1839
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
	} else {
		_t1833 = -1
	}
	prediction1046 := _t1833
	var _t1840 *pb.Construct
	if prediction1046 == 1 {
		_t1841 := p.parse_instruction()
		instruction1048 := _t1841
		_t1842 := &pb.Construct{}
		_t1842.ConstructType = &pb.Construct_Instruction{Instruction: instruction1048}
		_t1840 = _t1842
	} else {
		var _t1843 *pb.Construct
		if prediction1046 == 0 {
			_t1844 := p.parse_loop()
			loop1047 := _t1844
			_t1845 := &pb.Construct{}
			_t1845.ConstructType = &pb.Construct_Loop{Loop: loop1047}
			_t1843 = _t1845
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1840 = _t1843
	}
	result1050 := _t1840
	p.recordSpan(int(span_start1049), "Construct")
	return result1050
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1846 := p.parse_init()
	init1051 := _t1846
	_t1847 := p.parse_script()
	script1052 := _t1847
	p.consumeLiteral(")")
	_t1848 := &pb.Loop{Init: init1051, Body: script1052}
	result1054 := _t1848
	p.recordSpan(int(span_start1053), "Loop")
	return result1054
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1055 := []*pb.Instruction{}
	cond1056 := p.matchLookaheadLiteral("(", 0)
	for cond1056 {
		_t1849 := p.parse_instruction()
		item1057 := _t1849
		xs1055 = append(xs1055, item1057)
		cond1056 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1058 := xs1055
	p.consumeLiteral(")")
	return instructions1058
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1065 := int64(p.spanStart())
	var _t1850 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1851 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1851 = 1
		} else {
			var _t1852 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1852 = 4
			} else {
				var _t1853 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1853 = 3
				} else {
					var _t1854 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1854 = 2
					} else {
						var _t1855 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1855 = 0
						} else {
							_t1855 = -1
						}
						_t1854 = _t1855
					}
					_t1853 = _t1854
				}
				_t1852 = _t1853
			}
			_t1851 = _t1852
		}
		_t1850 = _t1851
	} else {
		_t1850 = -1
	}
	prediction1059 := _t1850
	var _t1856 *pb.Instruction
	if prediction1059 == 4 {
		_t1857 := p.parse_monus_def()
		monus_def1064 := _t1857
		_t1858 := &pb.Instruction{}
		_t1858.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1064}
		_t1856 = _t1858
	} else {
		var _t1859 *pb.Instruction
		if prediction1059 == 3 {
			_t1860 := p.parse_monoid_def()
			monoid_def1063 := _t1860
			_t1861 := &pb.Instruction{}
			_t1861.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1063}
			_t1859 = _t1861
		} else {
			var _t1862 *pb.Instruction
			if prediction1059 == 2 {
				_t1863 := p.parse_break()
				break1062 := _t1863
				_t1864 := &pb.Instruction{}
				_t1864.InstrType = &pb.Instruction_Break{Break: break1062}
				_t1862 = _t1864
			} else {
				var _t1865 *pb.Instruction
				if prediction1059 == 1 {
					_t1866 := p.parse_upsert()
					upsert1061 := _t1866
					_t1867 := &pb.Instruction{}
					_t1867.InstrType = &pb.Instruction_Upsert{Upsert: upsert1061}
					_t1865 = _t1867
				} else {
					var _t1868 *pb.Instruction
					if prediction1059 == 0 {
						_t1869 := p.parse_assign()
						assign1060 := _t1869
						_t1870 := &pb.Instruction{}
						_t1870.InstrType = &pb.Instruction_Assign{Assign: assign1060}
						_t1868 = _t1870
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1865 = _t1868
				}
				_t1862 = _t1865
			}
			_t1859 = _t1862
		}
		_t1856 = _t1859
	}
	result1066 := _t1856
	p.recordSpan(int(span_start1065), "Instruction")
	return result1066
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1070 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1871 := p.parse_relation_id()
	relation_id1067 := _t1871
	_t1872 := p.parse_abstraction()
	abstraction1068 := _t1872
	var _t1873 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1874 := p.parse_attrs()
		_t1873 = _t1874
	}
	attrs1069 := _t1873
	p.consumeLiteral(")")
	_t1875 := attrs1069
	if attrs1069 == nil {
		_t1875 = []*pb.Attribute{}
	}
	_t1876 := &pb.Assign{Name: relation_id1067, Body: abstraction1068, Attrs: _t1875}
	result1071 := _t1876
	p.recordSpan(int(span_start1070), "Assign")
	return result1071
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1075 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1877 := p.parse_relation_id()
	relation_id1072 := _t1877
	_t1878 := p.parse_abstraction_with_arity()
	abstraction_with_arity1073 := _t1878
	var _t1879 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1880 := p.parse_attrs()
		_t1879 = _t1880
	}
	attrs1074 := _t1879
	p.consumeLiteral(")")
	_t1881 := attrs1074
	if attrs1074 == nil {
		_t1881 = []*pb.Attribute{}
	}
	_t1882 := &pb.Upsert{Name: relation_id1072, Body: abstraction_with_arity1073[0].(*pb.Abstraction), Attrs: _t1881, ValueArity: abstraction_with_arity1073[1].(int64)}
	result1076 := _t1882
	p.recordSpan(int(span_start1075), "Upsert")
	return result1076
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1883 := p.parse_bindings()
	bindings1077 := _t1883
	_t1884 := p.parse_formula()
	formula1078 := _t1884
	p.consumeLiteral(")")
	_t1885 := &pb.Abstraction{Vars: listConcat(bindings1077[0].([]*pb.Binding), bindings1077[1].([]*pb.Binding)), Value: formula1078}
	return []interface{}{_t1885, int64(len(bindings1077[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1886 := p.parse_relation_id()
	relation_id1079 := _t1886
	_t1887 := p.parse_abstraction()
	abstraction1080 := _t1887
	var _t1888 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1889 := p.parse_attrs()
		_t1888 = _t1889
	}
	attrs1081 := _t1888
	p.consumeLiteral(")")
	_t1890 := attrs1081
	if attrs1081 == nil {
		_t1890 = []*pb.Attribute{}
	}
	_t1891 := &pb.Break{Name: relation_id1079, Body: abstraction1080, Attrs: _t1890}
	result1083 := _t1891
	p.recordSpan(int(span_start1082), "Break")
	return result1083
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1892 := p.parse_monoid()
	monoid1084 := _t1892
	_t1893 := p.parse_relation_id()
	relation_id1085 := _t1893
	_t1894 := p.parse_abstraction_with_arity()
	abstraction_with_arity1086 := _t1894
	var _t1895 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1896 := p.parse_attrs()
		_t1895 = _t1896
	}
	attrs1087 := _t1895
	p.consumeLiteral(")")
	_t1897 := attrs1087
	if attrs1087 == nil {
		_t1897 = []*pb.Attribute{}
	}
	_t1898 := &pb.MonoidDef{Monoid: monoid1084, Name: relation_id1085, Body: abstraction_with_arity1086[0].(*pb.Abstraction), Attrs: _t1897, ValueArity: abstraction_with_arity1086[1].(int64)}
	result1089 := _t1898
	p.recordSpan(int(span_start1088), "MonoidDef")
	return result1089
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1095 := int64(p.spanStart())
	var _t1899 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1900 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1900 = 3
		} else {
			var _t1901 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1901 = 0
			} else {
				var _t1902 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1902 = 1
				} else {
					var _t1903 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1903 = 2
					} else {
						_t1903 = -1
					}
					_t1902 = _t1903
				}
				_t1901 = _t1902
			}
			_t1900 = _t1901
		}
		_t1899 = _t1900
	} else {
		_t1899 = -1
	}
	prediction1090 := _t1899
	var _t1904 *pb.Monoid
	if prediction1090 == 3 {
		_t1905 := p.parse_sum_monoid()
		sum_monoid1094 := _t1905
		_t1906 := &pb.Monoid{}
		_t1906.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1094}
		_t1904 = _t1906
	} else {
		var _t1907 *pb.Monoid
		if prediction1090 == 2 {
			_t1908 := p.parse_max_monoid()
			max_monoid1093 := _t1908
			_t1909 := &pb.Monoid{}
			_t1909.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1093}
			_t1907 = _t1909
		} else {
			var _t1910 *pb.Monoid
			if prediction1090 == 1 {
				_t1911 := p.parse_min_monoid()
				min_monoid1092 := _t1911
				_t1912 := &pb.Monoid{}
				_t1912.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1092}
				_t1910 = _t1912
			} else {
				var _t1913 *pb.Monoid
				if prediction1090 == 0 {
					_t1914 := p.parse_or_monoid()
					or_monoid1091 := _t1914
					_t1915 := &pb.Monoid{}
					_t1915.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1091}
					_t1913 = _t1915
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1910 = _t1913
			}
			_t1907 = _t1910
		}
		_t1904 = _t1907
	}
	result1096 := _t1904
	p.recordSpan(int(span_start1095), "Monoid")
	return result1096
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1916 := &pb.OrMonoid{}
	result1098 := _t1916
	p.recordSpan(int(span_start1097), "OrMonoid")
	return result1098
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1917 := p.parse_type()
	type1099 := _t1917
	p.consumeLiteral(")")
	_t1918 := &pb.MinMonoid{Type: type1099}
	result1101 := _t1918
	p.recordSpan(int(span_start1100), "MinMonoid")
	return result1101
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1919 := p.parse_type()
	type1102 := _t1919
	p.consumeLiteral(")")
	_t1920 := &pb.MaxMonoid{Type: type1102}
	result1104 := _t1920
	p.recordSpan(int(span_start1103), "MaxMonoid")
	return result1104
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1106 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1921 := p.parse_type()
	type1105 := _t1921
	p.consumeLiteral(")")
	_t1922 := &pb.SumMonoid{Type: type1105}
	result1107 := _t1922
	p.recordSpan(int(span_start1106), "SumMonoid")
	return result1107
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1923 := p.parse_monoid()
	monoid1108 := _t1923
	_t1924 := p.parse_relation_id()
	relation_id1109 := _t1924
	_t1925 := p.parse_abstraction_with_arity()
	abstraction_with_arity1110 := _t1925
	var _t1926 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1927 := p.parse_attrs()
		_t1926 = _t1927
	}
	attrs1111 := _t1926
	p.consumeLiteral(")")
	_t1928 := attrs1111
	if attrs1111 == nil {
		_t1928 = []*pb.Attribute{}
	}
	_t1929 := &pb.MonusDef{Monoid: monoid1108, Name: relation_id1109, Body: abstraction_with_arity1110[0].(*pb.Abstraction), Attrs: _t1928, ValueArity: abstraction_with_arity1110[1].(int64)}
	result1113 := _t1929
	p.recordSpan(int(span_start1112), "MonusDef")
	return result1113
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1118 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1930 := p.parse_relation_id()
	relation_id1114 := _t1930
	_t1931 := p.parse_abstraction()
	abstraction1115 := _t1931
	_t1932 := p.parse_functional_dependency_keys()
	functional_dependency_keys1116 := _t1932
	_t1933 := p.parse_functional_dependency_values()
	functional_dependency_values1117 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.FunctionalDependency{Guard: abstraction1115, Keys: functional_dependency_keys1116, Values: functional_dependency_values1117}
	_t1935 := &pb.Constraint{Name: relation_id1114}
	_t1935.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1934}
	result1119 := _t1935
	p.recordSpan(int(span_start1118), "Constraint")
	return result1119
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1120 := []*pb.Var{}
	cond1121 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1121 {
		_t1936 := p.parse_var()
		item1122 := _t1936
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
		_t1937 := p.parse_var()
		item1126 := _t1937
		xs1124 = append(xs1124, item1126)
		cond1125 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1127 := xs1124
	p.consumeLiteral(")")
	return vars1127
}

func (p *Parser) parse_data() *pb.Data {
	span_start1133 := int64(p.spanStart())
	var _t1938 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1939 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1939 = 3
		} else {
			var _t1940 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1940 = 0
			} else {
				var _t1941 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1941 = 2
				} else {
					var _t1942 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1942 = 1
					} else {
						_t1942 = -1
					}
					_t1941 = _t1942
				}
				_t1940 = _t1941
			}
			_t1939 = _t1940
		}
		_t1938 = _t1939
	} else {
		_t1938 = -1
	}
	prediction1128 := _t1938
	var _t1943 *pb.Data
	if prediction1128 == 3 {
		_t1944 := p.parse_iceberg_data()
		iceberg_data1132 := _t1944
		_t1945 := &pb.Data{}
		_t1945.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1132}
		_t1943 = _t1945
	} else {
		var _t1946 *pb.Data
		if prediction1128 == 2 {
			_t1947 := p.parse_csv_data()
			csv_data1131 := _t1947
			_t1948 := &pb.Data{}
			_t1948.DataType = &pb.Data_CsvData{CsvData: csv_data1131}
			_t1946 = _t1948
		} else {
			var _t1949 *pb.Data
			if prediction1128 == 1 {
				_t1950 := p.parse_betree_relation()
				betree_relation1130 := _t1950
				_t1951 := &pb.Data{}
				_t1951.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1130}
				_t1949 = _t1951
			} else {
				var _t1952 *pb.Data
				if prediction1128 == 0 {
					_t1953 := p.parse_edb()
					edb1129 := _t1953
					_t1954 := &pb.Data{}
					_t1954.DataType = &pb.Data_Edb{Edb: edb1129}
					_t1952 = _t1954
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1949 = _t1952
			}
			_t1946 = _t1949
		}
		_t1943 = _t1946
	}
	result1134 := _t1943
	p.recordSpan(int(span_start1133), "Data")
	return result1134
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1955 := p.parse_relation_id()
	relation_id1135 := _t1955
	_t1956 := p.parse_edb_path()
	edb_path1136 := _t1956
	_t1957 := p.parse_edb_types()
	edb_types1137 := _t1957
	p.consumeLiteral(")")
	_t1958 := &pb.EDB{TargetId: relation_id1135, Path: edb_path1136, Types: edb_types1137}
	result1139 := _t1958
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
		_t1959 := p.parse_type()
		item1146 := _t1959
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
	_t1960 := p.parse_relation_id()
	relation_id1148 := _t1960
	_t1961 := p.parse_betree_info()
	betree_info1149 := _t1961
	p.consumeLiteral(")")
	_t1962 := &pb.BeTreeRelation{Name: relation_id1148, RelationInfo: betree_info1149}
	result1151 := _t1962
	p.recordSpan(int(span_start1150), "BeTreeRelation")
	return result1151
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1963 := p.parse_betree_info_key_types()
	betree_info_key_types1152 := _t1963
	_t1964 := p.parse_betree_info_value_types()
	betree_info_value_types1153 := _t1964
	_t1965 := p.parse_config_dict()
	config_dict1154 := _t1965
	p.consumeLiteral(")")
	_t1966 := p.construct_betree_info(betree_info_key_types1152, betree_info_value_types1153, config_dict1154)
	result1156 := _t1966
	p.recordSpan(int(span_start1155), "BeTreeInfo")
	return result1156
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1157 := []*pb.Type{}
	cond1158 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1158 {
		_t1967 := p.parse_type()
		item1159 := _t1967
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
		_t1968 := p.parse_type()
		item1163 := _t1968
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
	_t1969 := p.parse_csvlocator()
	csvlocator1165 := _t1969
	_t1970 := p.parse_csv_config()
	csv_config1166 := _t1970
	_t1971 := p.parse_gnf_columns()
	gnf_columns1167 := _t1971
	_t1972 := p.parse_csv_asof()
	csv_asof1168 := _t1972
	p.consumeLiteral(")")
	_t1973 := &pb.CSVData{Locator: csvlocator1165, Config: csv_config1166, Columns: gnf_columns1167, Asof: csv_asof1168}
	result1170 := _t1973
	p.recordSpan(int(span_start1169), "CSVData")
	return result1170
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1173 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1974 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1975 := p.parse_csv_locator_paths()
		_t1974 = _t1975
	}
	csv_locator_paths1171 := _t1974
	var _t1976 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1977 := p.parse_csv_locator_inline_data()
		_t1976 = ptr(_t1977)
	}
	csv_locator_inline_data1172 := _t1976
	p.consumeLiteral(")")
	_t1978 := csv_locator_paths1171
	if csv_locator_paths1171 == nil {
		_t1978 = []string{}
	}
	_t1979 := &pb.CSVLocator{Paths: _t1978, InlineData: []byte(deref(csv_locator_inline_data1172, ""))}
	result1174 := _t1979
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
	string1179 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1179
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1181 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1980 := p.parse_config_dict()
	config_dict1180 := _t1980
	p.consumeLiteral(")")
	_t1981 := p.construct_csv_config(config_dict1180)
	result1182 := _t1981
	p.recordSpan(int(span_start1181), "CSVConfig")
	return result1182
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1183 := []*pb.GNFColumn{}
	cond1184 := p.matchLookaheadLiteral("(", 0)
	for cond1184 {
		_t1982 := p.parse_gnf_column()
		item1185 := _t1982
		xs1183 = append(xs1183, item1185)
		cond1184 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1186 := xs1183
	p.consumeLiteral(")")
	return gnf_columns1186
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1193 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1983 := p.parse_gnf_column_path()
	gnf_column_path1187 := _t1983
	var _t1984 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1985 := p.parse_relation_id()
		_t1984 = _t1985
	}
	relation_id1188 := _t1984
	p.consumeLiteral("[")
	xs1189 := []*pb.Type{}
	cond1190 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1190 {
		_t1986 := p.parse_type()
		item1191 := _t1986
		xs1189 = append(xs1189, item1191)
		cond1190 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1192 := xs1189
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1987 := &pb.GNFColumn{ColumnPath: gnf_column_path1187, TargetId: relation_id1188, Types: types1192}
	result1194 := _t1987
	p.recordSpan(int(span_start1193), "GNFColumn")
	return result1194
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1988 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1988 = 1
	} else {
		var _t1989 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1989 = 0
		} else {
			_t1989 = -1
		}
		_t1988 = _t1989
	}
	prediction1195 := _t1988
	var _t1990 []string
	if prediction1195 == 1 {
		p.consumeLiteral("[")
		xs1197 := []string{}
		cond1198 := p.matchLookaheadTerminal("STRING", 0)
		for cond1198 {
			item1199 := p.consumeTerminal("STRING").Value.str
			xs1197 = append(xs1197, item1199)
			cond1198 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1200 := xs1197
		p.consumeLiteral("]")
		_t1990 = strings1200
	} else {
		var _t1991 []string
		if prediction1195 == 0 {
			string1196 := p.consumeTerminal("STRING").Value.str
			_ = string1196
			_t1991 = []string{string1196}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1990 = _t1991
	}
	return _t1990
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1201 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1201
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1208 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1992 := p.parse_iceberg_locator()
	iceberg_locator1202 := _t1992
	_t1993 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1203 := _t1993
	_t1994 := p.parse_gnf_columns()
	gnf_columns1204 := _t1994
	var _t1995 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1996 := p.parse_iceberg_from_snapshot()
		_t1995 = ptr(_t1996)
	}
	iceberg_from_snapshot1205 := _t1995
	var _t1997 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1998 := p.parse_iceberg_to_snapshot()
		_t1997 = ptr(_t1998)
	}
	iceberg_to_snapshot1206 := _t1997
	_t1999 := p.parse_boolean_value()
	boolean_value1207 := _t1999
	p.consumeLiteral(")")
	_t2000 := p.construct_iceberg_data(iceberg_locator1202, iceberg_catalog_config1203, gnf_columns1204, iceberg_from_snapshot1205, iceberg_to_snapshot1206, boolean_value1207)
	result1209 := _t2000
	p.recordSpan(int(span_start1208), "IcebergData")
	return result1209
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1213 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2001 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1210 := _t2001
	_t2002 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1211 := _t2002
	_t2003 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1212 := _t2003
	p.consumeLiteral(")")
	_t2004 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1210, Namespace: iceberg_locator_namespace1211, Warehouse: iceberg_locator_warehouse1212}
	result1214 := _t2004
	p.recordSpan(int(span_start1213), "IcebergLocator")
	return result1214
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1215 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1215
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1216 := []string{}
	cond1217 := p.matchLookaheadTerminal("STRING", 0)
	for cond1217 {
		item1218 := p.consumeTerminal("STRING").Value.str
		xs1216 = append(xs1216, item1218)
		cond1217 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1219 := xs1216
	p.consumeLiteral(")")
	return strings1219
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1220 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1220
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1225 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2005 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1221 := _t2005
	var _t2006 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2007 := p.parse_iceberg_catalog_config_scope()
		_t2006 = ptr(_t2007)
	}
	iceberg_catalog_config_scope1222 := _t2006
	_t2008 := p.parse_iceberg_properties()
	iceberg_properties1223 := _t2008
	_t2009 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1224 := _t2009
	p.consumeLiteral(")")
	_t2010 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1221, iceberg_catalog_config_scope1222, iceberg_properties1223, iceberg_auth_properties1224)
	result1226 := _t2010
	p.recordSpan(int(span_start1225), "IcebergCatalogConfig")
	return result1226
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1227 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1227
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1228 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1228
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1229 := [][]interface{}{}
	cond1230 := p.matchLookaheadLiteral("(", 0)
	for cond1230 {
		_t2011 := p.parse_iceberg_property_entry()
		item1231 := _t2011
		xs1229 = append(xs1229, item1231)
		cond1230 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1232 := xs1229
	p.consumeLiteral(")")
	return iceberg_property_entrys1232
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1233 := p.consumeTerminal("STRING").Value.str
	string_31234 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1233, string_31234}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1235 := [][]interface{}{}
	cond1236 := p.matchLookaheadLiteral("(", 0)
	for cond1236 {
		_t2012 := p.parse_iceberg_masked_property_entry()
		item1237 := _t2012
		xs1235 = append(xs1235, item1237)
		cond1236 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1238 := xs1235
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1238
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1239 := p.consumeTerminal("STRING").Value.str
	string_31240 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1239, string_31240}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1241 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1241
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1242 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1242
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1244 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2013 := p.parse_fragment_id()
	fragment_id1243 := _t2013
	p.consumeLiteral(")")
	_t2014 := &pb.Undefine{FragmentId: fragment_id1243}
	result1245 := _t2014
	p.recordSpan(int(span_start1244), "Undefine")
	return result1245
}

func (p *Parser) parse_context() *pb.Context {
	span_start1250 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1246 := []*pb.RelationId{}
	cond1247 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1247 {
		_t2015 := p.parse_relation_id()
		item1248 := _t2015
		xs1246 = append(xs1246, item1248)
		cond1247 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1249 := xs1246
	p.consumeLiteral(")")
	_t2016 := &pb.Context{Relations: relation_ids1249}
	result1251 := _t2016
	p.recordSpan(int(span_start1250), "Context")
	return result1251
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1257 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2017 := p.parse_edb_path()
	edb_path1252 := _t2017
	xs1253 := []*pb.SnapshotMapping{}
	cond1254 := p.matchLookaheadLiteral("[", 0)
	for cond1254 {
		_t2018 := p.parse_snapshot_mapping()
		item1255 := _t2018
		xs1253 = append(xs1253, item1255)
		cond1254 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1256 := xs1253
	p.consumeLiteral(")")
	_t2019 := &pb.Snapshot{Prefix: edb_path1252, Mappings: snapshot_mappings1256}
	result1258 := _t2019
	p.recordSpan(int(span_start1257), "Snapshot")
	return result1258
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1261 := int64(p.spanStart())
	_t2020 := p.parse_edb_path()
	edb_path1259 := _t2020
	_t2021 := p.parse_relation_id()
	relation_id1260 := _t2021
	_t2022 := &pb.SnapshotMapping{DestinationPath: edb_path1259, SourceRelation: relation_id1260}
	result1262 := _t2022
	p.recordSpan(int(span_start1261), "SnapshotMapping")
	return result1262
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1263 := []*pb.Read{}
	cond1264 := p.matchLookaheadLiteral("(", 0)
	for cond1264 {
		_t2023 := p.parse_read()
		item1265 := _t2023
		xs1263 = append(xs1263, item1265)
		cond1264 = p.matchLookaheadLiteral("(", 0)
	}
	reads1266 := xs1263
	p.consumeLiteral(")")
	return reads1266
}

func (p *Parser) parse_read() *pb.Read {
	span_start1273 := int64(p.spanStart())
	var _t2024 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2025 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2025 = 2
		} else {
			var _t2026 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2026 = 1
			} else {
				var _t2027 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2027 = 4
				} else {
					var _t2028 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2028 = 4
					} else {
						var _t2029 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2029 = 0
						} else {
							var _t2030 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2030 = 3
							} else {
								_t2030 = -1
							}
							_t2029 = _t2030
						}
						_t2028 = _t2029
					}
					_t2027 = _t2028
				}
				_t2026 = _t2027
			}
			_t2025 = _t2026
		}
		_t2024 = _t2025
	} else {
		_t2024 = -1
	}
	prediction1267 := _t2024
	var _t2031 *pb.Read
	if prediction1267 == 4 {
		_t2032 := p.parse_export()
		export1272 := _t2032
		_t2033 := &pb.Read{}
		_t2033.ReadType = &pb.Read_Export{Export: export1272}
		_t2031 = _t2033
	} else {
		var _t2034 *pb.Read
		if prediction1267 == 3 {
			_t2035 := p.parse_abort()
			abort1271 := _t2035
			_t2036 := &pb.Read{}
			_t2036.ReadType = &pb.Read_Abort{Abort: abort1271}
			_t2034 = _t2036
		} else {
			var _t2037 *pb.Read
			if prediction1267 == 2 {
				_t2038 := p.parse_what_if()
				what_if1270 := _t2038
				_t2039 := &pb.Read{}
				_t2039.ReadType = &pb.Read_WhatIf{WhatIf: what_if1270}
				_t2037 = _t2039
			} else {
				var _t2040 *pb.Read
				if prediction1267 == 1 {
					_t2041 := p.parse_output()
					output1269 := _t2041
					_t2042 := &pb.Read{}
					_t2042.ReadType = &pb.Read_Output{Output: output1269}
					_t2040 = _t2042
				} else {
					var _t2043 *pb.Read
					if prediction1267 == 0 {
						_t2044 := p.parse_demand()
						demand1268 := _t2044
						_t2045 := &pb.Read{}
						_t2045.ReadType = &pb.Read_Demand{Demand: demand1268}
						_t2043 = _t2045
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2040 = _t2043
				}
				_t2037 = _t2040
			}
			_t2034 = _t2037
		}
		_t2031 = _t2034
	}
	result1274 := _t2031
	p.recordSpan(int(span_start1273), "Read")
	return result1274
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1276 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2046 := p.parse_relation_id()
	relation_id1275 := _t2046
	p.consumeLiteral(")")
	_t2047 := &pb.Demand{RelationId: relation_id1275}
	result1277 := _t2047
	p.recordSpan(int(span_start1276), "Demand")
	return result1277
}

func (p *Parser) parse_output() *pb.Output {
	span_start1280 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2048 := p.parse_name()
	name1278 := _t2048
	_t2049 := p.parse_relation_id()
	relation_id1279 := _t2049
	p.consumeLiteral(")")
	_t2050 := &pb.Output{Name: name1278, RelationId: relation_id1279}
	result1281 := _t2050
	p.recordSpan(int(span_start1280), "Output")
	return result1281
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1284 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2051 := p.parse_name()
	name1282 := _t2051
	_t2052 := p.parse_epoch()
	epoch1283 := _t2052
	p.consumeLiteral(")")
	_t2053 := &pb.WhatIf{Branch: name1282, Epoch: epoch1283}
	result1285 := _t2053
	p.recordSpan(int(span_start1284), "WhatIf")
	return result1285
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1288 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2054 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2055 := p.parse_name()
		_t2054 = ptr(_t2055)
	}
	name1286 := _t2054
	_t2056 := p.parse_relation_id()
	relation_id1287 := _t2056
	p.consumeLiteral(")")
	_t2057 := &pb.Abort{Name: deref(name1286, "abort"), RelationId: relation_id1287}
	result1289 := _t2057
	p.recordSpan(int(span_start1288), "Abort")
	return result1289
}

func (p *Parser) parse_export() *pb.Export {
	span_start1293 := int64(p.spanStart())
	var _t2058 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2059 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2059 = 1
		} else {
			var _t2060 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2060 = 0
			} else {
				_t2060 = -1
			}
			_t2059 = _t2060
		}
		_t2058 = _t2059
	} else {
		_t2058 = -1
	}
	prediction1290 := _t2058
	var _t2061 *pb.Export
	if prediction1290 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2062 := p.parse_export_iceberg_config()
		export_iceberg_config1292 := _t2062
		p.consumeLiteral(")")
		_t2063 := &pb.Export{}
		_t2063.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1292}
		_t2061 = _t2063
	} else {
		var _t2064 *pb.Export
		if prediction1290 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2065 := p.parse_export_csv_config()
			export_csv_config1291 := _t2065
			p.consumeLiteral(")")
			_t2066 := &pb.Export{}
			_t2066.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1291}
			_t2064 = _t2066
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2061 = _t2064
	}
	result1294 := _t2061
	p.recordSpan(int(span_start1293), "Export")
	return result1294
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1302 := int64(p.spanStart())
	var _t2067 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2068 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2068 = 0
		} else {
			var _t2069 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2069 = 1
			} else {
				_t2069 = -1
			}
			_t2068 = _t2069
		}
		_t2067 = _t2068
	} else {
		_t2067 = -1
	}
	prediction1295 := _t2067
	var _t2070 *pb.ExportCSVConfig
	if prediction1295 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2071 := p.parse_export_csv_path()
		export_csv_path1299 := _t2071
		_t2072 := p.parse_export_csv_columns_list()
		export_csv_columns_list1300 := _t2072
		_t2073 := p.parse_config_dict()
		config_dict1301 := _t2073
		p.consumeLiteral(")")
		_t2074 := p.construct_export_csv_config(export_csv_path1299, export_csv_columns_list1300, config_dict1301)
		_t2070 = _t2074
	} else {
		var _t2075 *pb.ExportCSVConfig
		if prediction1295 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2076 := p.parse_export_csv_path()
			export_csv_path1296 := _t2076
			_t2077 := p.parse_export_csv_source()
			export_csv_source1297 := _t2077
			_t2078 := p.parse_csv_config()
			csv_config1298 := _t2078
			p.consumeLiteral(")")
			_t2079 := p.construct_export_csv_config_with_source(export_csv_path1296, export_csv_source1297, csv_config1298)
			_t2075 = _t2079
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2070 = _t2075
	}
	result1303 := _t2070
	p.recordSpan(int(span_start1302), "ExportCSVConfig")
	return result1303
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1304 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1304
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1311 := int64(p.spanStart())
	var _t2080 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2081 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2081 = 1
		} else {
			var _t2082 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
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
	prediction1305 := _t2080
	var _t2083 *pb.ExportCSVSource
	if prediction1305 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2084 := p.parse_relation_id()
		relation_id1310 := _t2084
		p.consumeLiteral(")")
		_t2085 := &pb.ExportCSVSource{}
		_t2085.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1310}
		_t2083 = _t2085
	} else {
		var _t2086 *pb.ExportCSVSource
		if prediction1305 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1306 := []*pb.ExportCSVColumn{}
			cond1307 := p.matchLookaheadLiteral("(", 0)
			for cond1307 {
				_t2087 := p.parse_export_csv_column()
				item1308 := _t2087
				xs1306 = append(xs1306, item1308)
				cond1307 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1309 := xs1306
			p.consumeLiteral(")")
			_t2088 := &pb.ExportCSVColumns{Columns: export_csv_columns1309}
			_t2089 := &pb.ExportCSVSource{}
			_t2089.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2088}
			_t2086 = _t2089
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2083 = _t2086
	}
	result1312 := _t2083
	p.recordSpan(int(span_start1311), "ExportCSVSource")
	return result1312
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1315 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1313 := p.consumeTerminal("STRING").Value.str
	_t2090 := p.parse_relation_id()
	relation_id1314 := _t2090
	p.consumeLiteral(")")
	_t2091 := &pb.ExportCSVColumn{ColumnName: string1313, ColumnData: relation_id1314}
	result1316 := _t2091
	p.recordSpan(int(span_start1315), "ExportCSVColumn")
	return result1316
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1317 := []*pb.ExportCSVColumn{}
	cond1318 := p.matchLookaheadLiteral("(", 0)
	for cond1318 {
		_t2092 := p.parse_export_csv_column()
		item1319 := _t2092
		xs1317 = append(xs1317, item1319)
		cond1318 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1320 := xs1317
	p.consumeLiteral(")")
	return export_csv_columns1320
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1327 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2093 := p.parse_iceberg_locator()
	iceberg_locator1321 := _t2093
	_t2094 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1322 := _t2094
	_t2095 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1323 := _t2095
	_t2096 := p.parse_export_iceberg_columns()
	export_iceberg_columns1324 := _t2096
	_t2097 := p.parse_iceberg_table_properties()
	iceberg_table_properties1325 := _t2097
	var _t2098 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2099 := p.parse_config_dict()
		_t2098 = _t2099
	}
	config_dict1326 := _t2098
	p.consumeLiteral(")")
	_t2100 := p.construct_export_iceberg_config_full(iceberg_locator1321, iceberg_catalog_config1322, export_iceberg_table_def1323, export_iceberg_columns1324, iceberg_table_properties1325, config_dict1326)
	result1328 := _t2100
	p.recordSpan(int(span_start1327), "ExportIcebergConfig")
	return result1328
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1330 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2101 := p.parse_relation_id()
	relation_id1329 := _t2101
	p.consumeLiteral(")")
	result1331 := relation_id1329
	p.recordSpan(int(span_start1330), "RelationId")
	return result1331
}

func (p *Parser) parse_export_iceberg_columns() []*pb.ExportColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1332 := []*pb.ExportColumn{}
	cond1333 := p.matchLookaheadLiteral("(", 0)
	for cond1333 {
		_t2102 := p.parse_export_iceberg_column()
		item1334 := _t2102
		xs1332 = append(xs1332, item1334)
		cond1333 = p.matchLookaheadLiteral("(", 0)
	}
	export_iceberg_columns1335 := xs1332
	p.consumeLiteral(")")
	return export_iceberg_columns1335
}

func (p *Parser) parse_export_iceberg_column() *pb.ExportColumn {
	span_start1338 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1336 := p.consumeTerminal("STRING").Value.str
	_t2103 := p.parse_boolean_value()
	boolean_value1337 := _t2103
	p.consumeLiteral(")")
	_t2104 := &pb.ExportColumn{Name: string1336, Nullable: boolean_value1337}
	result1339 := _t2104
	p.recordSpan(int(span_start1338), "ExportColumn")
	return result1339
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1340 := [][]interface{}{}
	cond1341 := p.matchLookaheadLiteral("(", 0)
	for cond1341 {
		_t2105 := p.parse_iceberg_property_entry()
		item1342 := _t2105
		xs1340 = append(xs1340, item1342)
		cond1341 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1343 := xs1340
	p.consumeLiteral(")")
	return iceberg_property_entrys1343
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
