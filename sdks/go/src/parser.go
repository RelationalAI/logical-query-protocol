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
	var _t2101 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2101
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2102 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2102
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2103 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2103
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2104 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2104
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2105 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2105
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2106 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2106
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2107 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2107
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2108 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2108
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2109 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2109
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}, storage_integration_opt [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2110 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2110
	_t2111 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2111
	_t2112 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2112
	_t2113 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2113
	_t2114 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2114
	_t2115 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2115
	_t2116 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2116
	_t2117 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2117
	_t2118 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2118
	_t2119 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2119
	_t2120 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2120
	_t2121 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2121
	_t2122 := p.construct_csv_storage_integration(storage_integration_opt)
	storage_integration := _t2122
	_t2123 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb, StorageIntegration: storage_integration}
	return _t2123
}

func (p *Parser) construct_csv_storage_integration(storage_integration_opt [][]interface{}) *pb.CSVStorageIntegration {
	var _t2124 interface{}
	if storage_integration_opt == nil {
		return nil
	}
	_ = _t2124
	config := dictFromList(storage_integration_opt)
	_t2125 := p._extract_value_string(dictGetValue(config, "provider"), "")
	_t2126 := p._extract_value_string(dictGetValue(config, "azure_sas_token"), "")
	_t2127 := p._extract_value_string(dictGetValue(config, "s3_region"), "")
	_t2128 := p._extract_value_string(dictGetValue(config, "s3_access_key_id"), "")
	_t2129 := p._extract_value_string(dictGetValue(config, "s3_secret_access_key"), "")
	_t2130 := &pb.CSVStorageIntegration{Provider: _t2125, AzureSasToken: _t2126, S3Region: _t2127, S3AccessKeyId: _t2128, S3SecretAccessKey: _t2129}
	return _t2130
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2131 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2131
	_t2132 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2132
	_t2133 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2133
	_t2134 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2134
	_t2135 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2135
	_t2136 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2136
	_t2137 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2137
	_t2138 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2138
	_t2139 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2139
	_t2140 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2140.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2140.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2140
	_t2141 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2141
}

func (p *Parser) default_configure() *pb.Configure {
	_t2142 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2142
	_t2143 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2143
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
	_t2144 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2144
	_t2145 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2145
	_t2146 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2146
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2147 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2147
	_t2148 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2148
	_t2149 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2149
	_t2150 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2150
	_t2151 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2151
	_t2152 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2152
	_t2153 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2153
	_t2154 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2154
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2155 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2155
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2156 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2156
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2157 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2157
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2158 := config_dict
	if config_dict == nil {
		_t2158 = [][]interface{}{}
	}
	cfg := dictFromList(_t2158)
	_t2159 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2159
	_t2160 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2160
	_t2161 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2161
	table_props := stringMapFromPairs(table_property_pairs)
	_t2162 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2162
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start673 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1334 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1335 := p.parse_configure()
		_t1334 = _t1335
	}
	configure667 := _t1334
	var _t1336 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1337 := p.parse_sync()
		_t1336 = _t1337
	}
	sync668 := _t1336
	xs669 := []*pb.Epoch{}
	cond670 := p.matchLookaheadLiteral("(", 0)
	for cond670 {
		_t1338 := p.parse_epoch()
		item671 := _t1338
		xs669 = append(xs669, item671)
		cond670 = p.matchLookaheadLiteral("(", 0)
	}
	epochs672 := xs669
	p.consumeLiteral(")")
	_t1339 := p.default_configure()
	_t1340 := configure667
	if configure667 == nil {
		_t1340 = _t1339
	}
	_t1341 := &pb.Transaction{Epochs: epochs672, Configure: _t1340, Sync: sync668}
	result674 := _t1341
	p.recordSpan(int(span_start673), "Transaction")
	return result674
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start676 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1342 := p.parse_config_dict()
	config_dict675 := _t1342
	p.consumeLiteral(")")
	_t1343 := p.construct_configure(config_dict675)
	result677 := _t1343
	p.recordSpan(int(span_start676), "Configure")
	return result677
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs678 := [][]interface{}{}
	cond679 := p.matchLookaheadLiteral(":", 0)
	for cond679 {
		_t1344 := p.parse_config_key_value()
		item680 := _t1344
		xs678 = append(xs678, item680)
		cond679 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values681 := xs678
	p.consumeLiteral("}")
	return config_key_values681
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol682 := p.consumeTerminal("SYMBOL").Value.str
	_t1345 := p.parse_raw_value()
	raw_value683 := _t1345
	return []interface{}{symbol682, raw_value683}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start697 := int64(p.spanStart())
	var _t1346 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1346 = 12
	} else {
		var _t1347 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1347 = 11
		} else {
			var _t1348 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1348 = 12
			} else {
				var _t1349 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1350 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1350 = 1
					} else {
						var _t1351 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1351 = 0
						} else {
							_t1351 = -1
						}
						_t1350 = _t1351
					}
					_t1349 = _t1350
				} else {
					var _t1352 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1352 = 7
					} else {
						var _t1353 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1353 = 8
						} else {
							var _t1354 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1354 = 2
							} else {
								var _t1355 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1355 = 3
								} else {
									var _t1356 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1356 = 9
									} else {
										var _t1357 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1357 = 4
										} else {
											var _t1358 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1358 = 5
											} else {
												var _t1359 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1359 = 6
												} else {
													var _t1360 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1360 = 10
													} else {
														_t1360 = -1
													}
													_t1359 = _t1360
												}
												_t1358 = _t1359
											}
											_t1357 = _t1358
										}
										_t1356 = _t1357
									}
									_t1355 = _t1356
								}
								_t1354 = _t1355
							}
							_t1353 = _t1354
						}
						_t1352 = _t1353
					}
					_t1349 = _t1352
				}
				_t1348 = _t1349
			}
			_t1347 = _t1348
		}
		_t1346 = _t1347
	}
	prediction684 := _t1346
	var _t1361 *pb.Value
	if prediction684 == 12 {
		_t1362 := p.parse_boolean_value()
		boolean_value696 := _t1362
		_t1363 := &pb.Value{}
		_t1363.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value696}
		_t1361 = _t1363
	} else {
		var _t1364 *pb.Value
		if prediction684 == 11 {
			p.consumeLiteral("missing")
			_t1365 := &pb.MissingValue{}
			_t1366 := &pb.Value{}
			_t1366.Value = &pb.Value_MissingValue{MissingValue: _t1365}
			_t1364 = _t1366
		} else {
			var _t1367 *pb.Value
			if prediction684 == 10 {
				decimal695 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1368 := &pb.Value{}
				_t1368.Value = &pb.Value_DecimalValue{DecimalValue: decimal695}
				_t1367 = _t1368
			} else {
				var _t1369 *pb.Value
				if prediction684 == 9 {
					int128694 := p.consumeTerminal("INT128").Value.int128
					_t1370 := &pb.Value{}
					_t1370.Value = &pb.Value_Int128Value{Int128Value: int128694}
					_t1369 = _t1370
				} else {
					var _t1371 *pb.Value
					if prediction684 == 8 {
						uint128693 := p.consumeTerminal("UINT128").Value.uint128
						_t1372 := &pb.Value{}
						_t1372.Value = &pb.Value_Uint128Value{Uint128Value: uint128693}
						_t1371 = _t1372
					} else {
						var _t1373 *pb.Value
						if prediction684 == 7 {
							uint32692 := p.consumeTerminal("UINT32").Value.u32
							_t1374 := &pb.Value{}
							_t1374.Value = &pb.Value_Uint32Value{Uint32Value: uint32692}
							_t1373 = _t1374
						} else {
							var _t1375 *pb.Value
							if prediction684 == 6 {
								float691 := p.consumeTerminal("FLOAT").Value.f64
								_t1376 := &pb.Value{}
								_t1376.Value = &pb.Value_FloatValue{FloatValue: float691}
								_t1375 = _t1376
							} else {
								var _t1377 *pb.Value
								if prediction684 == 5 {
									float32690 := p.consumeTerminal("FLOAT32").Value.f32
									_t1378 := &pb.Value{}
									_t1378.Value = &pb.Value_Float32Value{Float32Value: float32690}
									_t1377 = _t1378
								} else {
									var _t1379 *pb.Value
									if prediction684 == 4 {
										int689 := p.consumeTerminal("INT").Value.i64
										_t1380 := &pb.Value{}
										_t1380.Value = &pb.Value_IntValue{IntValue: int689}
										_t1379 = _t1380
									} else {
										var _t1381 *pb.Value
										if prediction684 == 3 {
											int32688 := p.consumeTerminal("INT32").Value.i32
											_t1382 := &pb.Value{}
											_t1382.Value = &pb.Value_Int32Value{Int32Value: int32688}
											_t1381 = _t1382
										} else {
											var _t1383 *pb.Value
											if prediction684 == 2 {
												string687 := p.consumeTerminal("STRING").Value.str
												_t1384 := &pb.Value{}
												_t1384.Value = &pb.Value_StringValue{StringValue: string687}
												_t1383 = _t1384
											} else {
												var _t1385 *pb.Value
												if prediction684 == 1 {
													_t1386 := p.parse_raw_datetime()
													raw_datetime686 := _t1386
													_t1387 := &pb.Value{}
													_t1387.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime686}
													_t1385 = _t1387
												} else {
													var _t1388 *pb.Value
													if prediction684 == 0 {
														_t1389 := p.parse_raw_date()
														raw_date685 := _t1389
														_t1390 := &pb.Value{}
														_t1390.Value = &pb.Value_DateValue{DateValue: raw_date685}
														_t1388 = _t1390
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1385 = _t1388
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
						_t1371 = _t1373
					}
					_t1369 = _t1371
				}
				_t1367 = _t1369
			}
			_t1364 = _t1367
		}
		_t1361 = _t1364
	}
	result698 := _t1361
	p.recordSpan(int(span_start697), "Value")
	return result698
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start702 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int699 := p.consumeTerminal("INT").Value.i64
	int_3700 := p.consumeTerminal("INT").Value.i64
	int_4701 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1391 := &pb.DateValue{Year: int32(int699), Month: int32(int_3700), Day: int32(int_4701)}
	result703 := _t1391
	p.recordSpan(int(span_start702), "DateValue")
	return result703
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int704 := p.consumeTerminal("INT").Value.i64
	int_3705 := p.consumeTerminal("INT").Value.i64
	int_4706 := p.consumeTerminal("INT").Value.i64
	int_5707 := p.consumeTerminal("INT").Value.i64
	int_6708 := p.consumeTerminal("INT").Value.i64
	int_7709 := p.consumeTerminal("INT").Value.i64
	var _t1392 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1392 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8710 := _t1392
	p.consumeLiteral(")")
	_t1393 := &pb.DateTimeValue{Year: int32(int704), Month: int32(int_3705), Day: int32(int_4706), Hour: int32(int_5707), Minute: int32(int_6708), Second: int32(int_7709), Microsecond: int32(deref(int_8710, 0))}
	result712 := _t1393
	p.recordSpan(int(span_start711), "DateTimeValue")
	return result712
}

func (p *Parser) parse_boolean_value() bool {
	var _t1394 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1394 = 0
	} else {
		var _t1395 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1395 = 1
		} else {
			_t1395 = -1
		}
		_t1394 = _t1395
	}
	prediction713 := _t1394
	var _t1396 bool
	if prediction713 == 1 {
		p.consumeLiteral("false")
		_t1396 = false
	} else {
		var _t1397 bool
		if prediction713 == 0 {
			p.consumeLiteral("true")
			_t1397 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1396 = _t1397
	}
	return _t1396
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start718 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs714 := []*pb.FragmentId{}
	cond715 := p.matchLookaheadLiteral(":", 0)
	for cond715 {
		_t1398 := p.parse_fragment_id()
		item716 := _t1398
		xs714 = append(xs714, item716)
		cond715 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids717 := xs714
	p.consumeLiteral(")")
	_t1399 := &pb.Sync{Fragments: fragment_ids717}
	result719 := _t1399
	p.recordSpan(int(span_start718), "Sync")
	return result719
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start721 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol720 := p.consumeTerminal("SYMBOL").Value.str
	result722 := &pb.FragmentId{Id: []byte(symbol720)}
	p.recordSpan(int(span_start721), "FragmentId")
	return result722
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1400 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1401 := p.parse_epoch_writes()
		_t1400 = _t1401
	}
	epoch_writes723 := _t1400
	var _t1402 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1403 := p.parse_epoch_reads()
		_t1402 = _t1403
	}
	epoch_reads724 := _t1402
	p.consumeLiteral(")")
	_t1404 := epoch_writes723
	if epoch_writes723 == nil {
		_t1404 = []*pb.Write{}
	}
	_t1405 := epoch_reads724
	if epoch_reads724 == nil {
		_t1405 = []*pb.Read{}
	}
	_t1406 := &pb.Epoch{Writes: _t1404, Reads: _t1405}
	result726 := _t1406
	p.recordSpan(int(span_start725), "Epoch")
	return result726
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs727 := []*pb.Write{}
	cond728 := p.matchLookaheadLiteral("(", 0)
	for cond728 {
		_t1407 := p.parse_write()
		item729 := _t1407
		xs727 = append(xs727, item729)
		cond728 = p.matchLookaheadLiteral("(", 0)
	}
	writes730 := xs727
	p.consumeLiteral(")")
	return writes730
}

func (p *Parser) parse_write() *pb.Write {
	span_start736 := int64(p.spanStart())
	var _t1408 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1409 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1409 = 1
		} else {
			var _t1410 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1410 = 3
			} else {
				var _t1411 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1411 = 0
				} else {
					var _t1412 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1412 = 2
					} else {
						_t1412 = -1
					}
					_t1411 = _t1412
				}
				_t1410 = _t1411
			}
			_t1409 = _t1410
		}
		_t1408 = _t1409
	} else {
		_t1408 = -1
	}
	prediction731 := _t1408
	var _t1413 *pb.Write
	if prediction731 == 3 {
		_t1414 := p.parse_snapshot()
		snapshot735 := _t1414
		_t1415 := &pb.Write{}
		_t1415.WriteType = &pb.Write_Snapshot{Snapshot: snapshot735}
		_t1413 = _t1415
	} else {
		var _t1416 *pb.Write
		if prediction731 == 2 {
			_t1417 := p.parse_context()
			context734 := _t1417
			_t1418 := &pb.Write{}
			_t1418.WriteType = &pb.Write_Context{Context: context734}
			_t1416 = _t1418
		} else {
			var _t1419 *pb.Write
			if prediction731 == 1 {
				_t1420 := p.parse_undefine()
				undefine733 := _t1420
				_t1421 := &pb.Write{}
				_t1421.WriteType = &pb.Write_Undefine{Undefine: undefine733}
				_t1419 = _t1421
			} else {
				var _t1422 *pb.Write
				if prediction731 == 0 {
					_t1423 := p.parse_define()
					define732 := _t1423
					_t1424 := &pb.Write{}
					_t1424.WriteType = &pb.Write_Define{Define: define732}
					_t1422 = _t1424
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1419 = _t1422
			}
			_t1416 = _t1419
		}
		_t1413 = _t1416
	}
	result737 := _t1413
	p.recordSpan(int(span_start736), "Write")
	return result737
}

func (p *Parser) parse_define() *pb.Define {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1425 := p.parse_fragment()
	fragment738 := _t1425
	p.consumeLiteral(")")
	_t1426 := &pb.Define{Fragment: fragment738}
	result740 := _t1426
	p.recordSpan(int(span_start739), "Define")
	return result740
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start746 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1427 := p.parse_new_fragment_id()
	new_fragment_id741 := _t1427
	xs742 := []*pb.Declaration{}
	cond743 := p.matchLookaheadLiteral("(", 0)
	for cond743 {
		_t1428 := p.parse_declaration()
		item744 := _t1428
		xs742 = append(xs742, item744)
		cond743 = p.matchLookaheadLiteral("(", 0)
	}
	declarations745 := xs742
	p.consumeLiteral(")")
	result747 := p.constructFragment(new_fragment_id741, declarations745)
	p.recordSpan(int(span_start746), "Fragment")
	return result747
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start749 := int64(p.spanStart())
	_t1429 := p.parse_fragment_id()
	fragment_id748 := _t1429
	p.startFragment(fragment_id748)
	result750 := fragment_id748
	p.recordSpan(int(span_start749), "FragmentId")
	return result750
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start756 := int64(p.spanStart())
	var _t1430 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1431 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1431 = 3
		} else {
			var _t1432 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1432 = 2
			} else {
				var _t1433 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1433 = 3
				} else {
					var _t1434 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1434 = 0
					} else {
						var _t1435 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1435 = 3
						} else {
							var _t1436 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1436 = 3
							} else {
								var _t1437 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1437 = 1
								} else {
									_t1437 = -1
								}
								_t1436 = _t1437
							}
							_t1435 = _t1436
						}
						_t1434 = _t1435
					}
					_t1433 = _t1434
				}
				_t1432 = _t1433
			}
			_t1431 = _t1432
		}
		_t1430 = _t1431
	} else {
		_t1430 = -1
	}
	prediction751 := _t1430
	var _t1438 *pb.Declaration
	if prediction751 == 3 {
		_t1439 := p.parse_data()
		data755 := _t1439
		_t1440 := &pb.Declaration{}
		_t1440.DeclarationType = &pb.Declaration_Data{Data: data755}
		_t1438 = _t1440
	} else {
		var _t1441 *pb.Declaration
		if prediction751 == 2 {
			_t1442 := p.parse_constraint()
			constraint754 := _t1442
			_t1443 := &pb.Declaration{}
			_t1443.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint754}
			_t1441 = _t1443
		} else {
			var _t1444 *pb.Declaration
			if prediction751 == 1 {
				_t1445 := p.parse_algorithm()
				algorithm753 := _t1445
				_t1446 := &pb.Declaration{}
				_t1446.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm753}
				_t1444 = _t1446
			} else {
				var _t1447 *pb.Declaration
				if prediction751 == 0 {
					_t1448 := p.parse_def()
					def752 := _t1448
					_t1449 := &pb.Declaration{}
					_t1449.DeclarationType = &pb.Declaration_Def{Def: def752}
					_t1447 = _t1449
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1444 = _t1447
			}
			_t1441 = _t1444
		}
		_t1438 = _t1441
	}
	result757 := _t1438
	p.recordSpan(int(span_start756), "Declaration")
	return result757
}

func (p *Parser) parse_def() *pb.Def {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1450 := p.parse_relation_id()
	relation_id758 := _t1450
	_t1451 := p.parse_abstraction()
	abstraction759 := _t1451
	var _t1452 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1453 := p.parse_attrs()
		_t1452 = _t1453
	}
	attrs760 := _t1452
	p.consumeLiteral(")")
	_t1454 := attrs760
	if attrs760 == nil {
		_t1454 = []*pb.Attribute{}
	}
	_t1455 := &pb.Def{Name: relation_id758, Body: abstraction759, Attrs: _t1454}
	result762 := _t1455
	p.recordSpan(int(span_start761), "Def")
	return result762
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start766 := int64(p.spanStart())
	var _t1456 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1456 = 0
	} else {
		var _t1457 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1457 = 1
		} else {
			_t1457 = -1
		}
		_t1456 = _t1457
	}
	prediction763 := _t1456
	var _t1458 *pb.RelationId
	if prediction763 == 1 {
		uint128765 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128765
		_t1458 = &pb.RelationId{IdLow: uint128765.Low, IdHigh: uint128765.High}
	} else {
		var _t1459 *pb.RelationId
		if prediction763 == 0 {
			p.consumeLiteral(":")
			symbol764 := p.consumeTerminal("SYMBOL").Value.str
			_t1459 = p.relationIdFromString(symbol764)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1458 = _t1459
	}
	result767 := _t1458
	p.recordSpan(int(span_start766), "RelationId")
	return result767
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start770 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1460 := p.parse_bindings()
	bindings768 := _t1460
	_t1461 := p.parse_formula()
	formula769 := _t1461
	p.consumeLiteral(")")
	_t1462 := &pb.Abstraction{Vars: listConcat(bindings768[0].([]*pb.Binding), bindings768[1].([]*pb.Binding)), Value: formula769}
	result771 := _t1462
	p.recordSpan(int(span_start770), "Abstraction")
	return result771
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs772 := []*pb.Binding{}
	cond773 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond773 {
		_t1463 := p.parse_binding()
		item774 := _t1463
		xs772 = append(xs772, item774)
		cond773 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings775 := xs772
	var _t1464 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1465 := p.parse_value_bindings()
		_t1464 = _t1465
	}
	value_bindings776 := _t1464
	p.consumeLiteral("]")
	_t1466 := value_bindings776
	if value_bindings776 == nil {
		_t1466 = []*pb.Binding{}
	}
	return []interface{}{bindings775, _t1466}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start779 := int64(p.spanStart())
	symbol777 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1467 := p.parse_type()
	type778 := _t1467
	_t1468 := &pb.Var{Name: symbol777}
	_t1469 := &pb.Binding{Var: _t1468, Type: type778}
	result780 := _t1469
	p.recordSpan(int(span_start779), "Binding")
	return result780
}

func (p *Parser) parse_type() *pb.Type {
	span_start796 := int64(p.spanStart())
	var _t1470 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1470 = 0
	} else {
		var _t1471 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1471 = 13
		} else {
			var _t1472 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1472 = 4
			} else {
				var _t1473 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1473 = 1
				} else {
					var _t1474 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1474 = 8
					} else {
						var _t1475 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1475 = 11
						} else {
							var _t1476 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1476 = 5
							} else {
								var _t1477 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1477 = 2
								} else {
									var _t1478 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1478 = 12
									} else {
										var _t1479 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1479 = 3
										} else {
											var _t1480 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1480 = 7
											} else {
												var _t1481 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1481 = 6
												} else {
													var _t1482 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1482 = 10
													} else {
														var _t1483 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1483 = 9
														} else {
															_t1483 = -1
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
							_t1475 = _t1476
						}
						_t1474 = _t1475
					}
					_t1473 = _t1474
				}
				_t1472 = _t1473
			}
			_t1471 = _t1472
		}
		_t1470 = _t1471
	}
	prediction781 := _t1470
	var _t1484 *pb.Type
	if prediction781 == 13 {
		_t1485 := p.parse_uint32_type()
		uint32_type795 := _t1485
		_t1486 := &pb.Type{}
		_t1486.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type795}
		_t1484 = _t1486
	} else {
		var _t1487 *pb.Type
		if prediction781 == 12 {
			_t1488 := p.parse_float32_type()
			float32_type794 := _t1488
			_t1489 := &pb.Type{}
			_t1489.Type = &pb.Type_Float32Type{Float32Type: float32_type794}
			_t1487 = _t1489
		} else {
			var _t1490 *pb.Type
			if prediction781 == 11 {
				_t1491 := p.parse_int32_type()
				int32_type793 := _t1491
				_t1492 := &pb.Type{}
				_t1492.Type = &pb.Type_Int32Type{Int32Type: int32_type793}
				_t1490 = _t1492
			} else {
				var _t1493 *pb.Type
				if prediction781 == 10 {
					_t1494 := p.parse_boolean_type()
					boolean_type792 := _t1494
					_t1495 := &pb.Type{}
					_t1495.Type = &pb.Type_BooleanType{BooleanType: boolean_type792}
					_t1493 = _t1495
				} else {
					var _t1496 *pb.Type
					if prediction781 == 9 {
						_t1497 := p.parse_decimal_type()
						decimal_type791 := _t1497
						_t1498 := &pb.Type{}
						_t1498.Type = &pb.Type_DecimalType{DecimalType: decimal_type791}
						_t1496 = _t1498
					} else {
						var _t1499 *pb.Type
						if prediction781 == 8 {
							_t1500 := p.parse_missing_type()
							missing_type790 := _t1500
							_t1501 := &pb.Type{}
							_t1501.Type = &pb.Type_MissingType{MissingType: missing_type790}
							_t1499 = _t1501
						} else {
							var _t1502 *pb.Type
							if prediction781 == 7 {
								_t1503 := p.parse_datetime_type()
								datetime_type789 := _t1503
								_t1504 := &pb.Type{}
								_t1504.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type789}
								_t1502 = _t1504
							} else {
								var _t1505 *pb.Type
								if prediction781 == 6 {
									_t1506 := p.parse_date_type()
									date_type788 := _t1506
									_t1507 := &pb.Type{}
									_t1507.Type = &pb.Type_DateType{DateType: date_type788}
									_t1505 = _t1507
								} else {
									var _t1508 *pb.Type
									if prediction781 == 5 {
										_t1509 := p.parse_int128_type()
										int128_type787 := _t1509
										_t1510 := &pb.Type{}
										_t1510.Type = &pb.Type_Int128Type{Int128Type: int128_type787}
										_t1508 = _t1510
									} else {
										var _t1511 *pb.Type
										if prediction781 == 4 {
											_t1512 := p.parse_uint128_type()
											uint128_type786 := _t1512
											_t1513 := &pb.Type{}
											_t1513.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type786}
											_t1511 = _t1513
										} else {
											var _t1514 *pb.Type
											if prediction781 == 3 {
												_t1515 := p.parse_float_type()
												float_type785 := _t1515
												_t1516 := &pb.Type{}
												_t1516.Type = &pb.Type_FloatType{FloatType: float_type785}
												_t1514 = _t1516
											} else {
												var _t1517 *pb.Type
												if prediction781 == 2 {
													_t1518 := p.parse_int_type()
													int_type784 := _t1518
													_t1519 := &pb.Type{}
													_t1519.Type = &pb.Type_IntType{IntType: int_type784}
													_t1517 = _t1519
												} else {
													var _t1520 *pb.Type
													if prediction781 == 1 {
														_t1521 := p.parse_string_type()
														string_type783 := _t1521
														_t1522 := &pb.Type{}
														_t1522.Type = &pb.Type_StringType{StringType: string_type783}
														_t1520 = _t1522
													} else {
														var _t1523 *pb.Type
														if prediction781 == 0 {
															_t1524 := p.parse_unspecified_type()
															unspecified_type782 := _t1524
															_t1525 := &pb.Type{}
															_t1525.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type782}
															_t1523 = _t1525
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1487 = _t1490
		}
		_t1484 = _t1487
	}
	result797 := _t1484
	p.recordSpan(int(span_start796), "Type")
	return result797
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1526 := &pb.UnspecifiedType{}
	result799 := _t1526
	p.recordSpan(int(span_start798), "UnspecifiedType")
	return result799
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1527 := &pb.StringType{}
	result801 := _t1527
	p.recordSpan(int(span_start800), "StringType")
	return result801
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1528 := &pb.IntType{}
	result803 := _t1528
	p.recordSpan(int(span_start802), "IntType")
	return result803
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1529 := &pb.FloatType{}
	result805 := _t1529
	p.recordSpan(int(span_start804), "FloatType")
	return result805
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1530 := &pb.UInt128Type{}
	result807 := _t1530
	p.recordSpan(int(span_start806), "UInt128Type")
	return result807
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1531 := &pb.Int128Type{}
	result809 := _t1531
	p.recordSpan(int(span_start808), "Int128Type")
	return result809
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1532 := &pb.DateType{}
	result811 := _t1532
	p.recordSpan(int(span_start810), "DateType")
	return result811
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1533 := &pb.DateTimeType{}
	result813 := _t1533
	p.recordSpan(int(span_start812), "DateTimeType")
	return result813
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1534 := &pb.MissingType{}
	result815 := _t1534
	p.recordSpan(int(span_start814), "MissingType")
	return result815
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int816 := p.consumeTerminal("INT").Value.i64
	int_3817 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1535 := &pb.DecimalType{Precision: int32(int816), Scale: int32(int_3817)}
	result819 := _t1535
	p.recordSpan(int(span_start818), "DecimalType")
	return result819
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1536 := &pb.BooleanType{}
	result821 := _t1536
	p.recordSpan(int(span_start820), "BooleanType")
	return result821
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1537 := &pb.Int32Type{}
	result823 := _t1537
	p.recordSpan(int(span_start822), "Int32Type")
	return result823
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1538 := &pb.Float32Type{}
	result825 := _t1538
	p.recordSpan(int(span_start824), "Float32Type")
	return result825
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start826 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1539 := &pb.UInt32Type{}
	result827 := _t1539
	p.recordSpan(int(span_start826), "UInt32Type")
	return result827
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs828 := []*pb.Binding{}
	cond829 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond829 {
		_t1540 := p.parse_binding()
		item830 := _t1540
		xs828 = append(xs828, item830)
		cond829 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings831 := xs828
	return bindings831
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start846 := int64(p.spanStart())
	var _t1541 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1542 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1542 = 0
		} else {
			var _t1543 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1543 = 11
			} else {
				var _t1544 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1544 = 3
				} else {
					var _t1545 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1545 = 10
					} else {
						var _t1546 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1546 = 9
						} else {
							var _t1547 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1547 = 5
							} else {
								var _t1548 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1548 = 6
								} else {
									var _t1549 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1549 = 7
									} else {
										var _t1550 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1550 = 1
										} else {
											var _t1551 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1551 = 2
											} else {
												var _t1552 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1552 = 12
												} else {
													var _t1553 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1553 = 8
													} else {
														var _t1554 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1554 = 4
														} else {
															var _t1555 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1555 = 10
															} else {
																var _t1556 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1556 = 10
																} else {
																	var _t1557 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1557 = 10
																	} else {
																		var _t1558 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1558 = 10
																		} else {
																			var _t1559 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1559 = 10
																			} else {
																				var _t1560 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1560 = 10
																				} else {
																					var _t1561 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1561 = 10
																					} else {
																						var _t1562 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1562 = 10
																						} else {
																							var _t1563 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1563 = 10
																							} else {
																								_t1563 = -1
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
							}
							_t1546 = _t1547
						}
						_t1545 = _t1546
					}
					_t1544 = _t1545
				}
				_t1543 = _t1544
			}
			_t1542 = _t1543
		}
		_t1541 = _t1542
	} else {
		_t1541 = -1
	}
	prediction832 := _t1541
	var _t1564 *pb.Formula
	if prediction832 == 12 {
		_t1565 := p.parse_cast()
		cast845 := _t1565
		_t1566 := &pb.Formula{}
		_t1566.FormulaType = &pb.Formula_Cast{Cast: cast845}
		_t1564 = _t1566
	} else {
		var _t1567 *pb.Formula
		if prediction832 == 11 {
			_t1568 := p.parse_rel_atom()
			rel_atom844 := _t1568
			_t1569 := &pb.Formula{}
			_t1569.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom844}
			_t1567 = _t1569
		} else {
			var _t1570 *pb.Formula
			if prediction832 == 10 {
				_t1571 := p.parse_primitive()
				primitive843 := _t1571
				_t1572 := &pb.Formula{}
				_t1572.FormulaType = &pb.Formula_Primitive{Primitive: primitive843}
				_t1570 = _t1572
			} else {
				var _t1573 *pb.Formula
				if prediction832 == 9 {
					_t1574 := p.parse_pragma()
					pragma842 := _t1574
					_t1575 := &pb.Formula{}
					_t1575.FormulaType = &pb.Formula_Pragma{Pragma: pragma842}
					_t1573 = _t1575
				} else {
					var _t1576 *pb.Formula
					if prediction832 == 8 {
						_t1577 := p.parse_atom()
						atom841 := _t1577
						_t1578 := &pb.Formula{}
						_t1578.FormulaType = &pb.Formula_Atom{Atom: atom841}
						_t1576 = _t1578
					} else {
						var _t1579 *pb.Formula
						if prediction832 == 7 {
							_t1580 := p.parse_ffi()
							ffi840 := _t1580
							_t1581 := &pb.Formula{}
							_t1581.FormulaType = &pb.Formula_Ffi{Ffi: ffi840}
							_t1579 = _t1581
						} else {
							var _t1582 *pb.Formula
							if prediction832 == 6 {
								_t1583 := p.parse_not()
								not839 := _t1583
								_t1584 := &pb.Formula{}
								_t1584.FormulaType = &pb.Formula_Not{Not: not839}
								_t1582 = _t1584
							} else {
								var _t1585 *pb.Formula
								if prediction832 == 5 {
									_t1586 := p.parse_disjunction()
									disjunction838 := _t1586
									_t1587 := &pb.Formula{}
									_t1587.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction838}
									_t1585 = _t1587
								} else {
									var _t1588 *pb.Formula
									if prediction832 == 4 {
										_t1589 := p.parse_conjunction()
										conjunction837 := _t1589
										_t1590 := &pb.Formula{}
										_t1590.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction837}
										_t1588 = _t1590
									} else {
										var _t1591 *pb.Formula
										if prediction832 == 3 {
											_t1592 := p.parse_reduce()
											reduce836 := _t1592
											_t1593 := &pb.Formula{}
											_t1593.FormulaType = &pb.Formula_Reduce{Reduce: reduce836}
											_t1591 = _t1593
										} else {
											var _t1594 *pb.Formula
											if prediction832 == 2 {
												_t1595 := p.parse_exists()
												exists835 := _t1595
												_t1596 := &pb.Formula{}
												_t1596.FormulaType = &pb.Formula_Exists{Exists: exists835}
												_t1594 = _t1596
											} else {
												var _t1597 *pb.Formula
												if prediction832 == 1 {
													_t1598 := p.parse_false()
													false834 := _t1598
													_t1599 := &pb.Formula{}
													_t1599.FormulaType = &pb.Formula_Disjunction{Disjunction: false834}
													_t1597 = _t1599
												} else {
													var _t1600 *pb.Formula
													if prediction832 == 0 {
														_t1601 := p.parse_true()
														true833 := _t1601
														_t1602 := &pb.Formula{}
														_t1602.FormulaType = &pb.Formula_Conjunction{Conjunction: true833}
														_t1600 = _t1602
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1567 = _t1570
		}
		_t1564 = _t1567
	}
	result847 := _t1564
	p.recordSpan(int(span_start846), "Formula")
	return result847
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1603 := &pb.Conjunction{Args: []*pb.Formula{}}
	result849 := _t1603
	p.recordSpan(int(span_start848), "Conjunction")
	return result849
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start850 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1604 := &pb.Disjunction{Args: []*pb.Formula{}}
	result851 := _t1604
	p.recordSpan(int(span_start850), "Disjunction")
	return result851
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1605 := p.parse_bindings()
	bindings852 := _t1605
	_t1606 := p.parse_formula()
	formula853 := _t1606
	p.consumeLiteral(")")
	_t1607 := &pb.Abstraction{Vars: listConcat(bindings852[0].([]*pb.Binding), bindings852[1].([]*pb.Binding)), Value: formula853}
	_t1608 := &pb.Exists{Body: _t1607}
	result855 := _t1608
	p.recordSpan(int(span_start854), "Exists")
	return result855
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1609 := p.parse_abstraction()
	abstraction856 := _t1609
	_t1610 := p.parse_abstraction()
	abstraction_3857 := _t1610
	_t1611 := p.parse_terms()
	terms858 := _t1611
	p.consumeLiteral(")")
	_t1612 := &pb.Reduce{Op: abstraction856, Body: abstraction_3857, Terms: terms858}
	result860 := _t1612
	p.recordSpan(int(span_start859), "Reduce")
	return result860
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs861 := []*pb.Term{}
	cond862 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond862 {
		_t1613 := p.parse_term()
		item863 := _t1613
		xs861 = append(xs861, item863)
		cond862 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms864 := xs861
	p.consumeLiteral(")")
	return terms864
}

func (p *Parser) parse_term() *pb.Term {
	span_start868 := int64(p.spanStart())
	var _t1614 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1614 = 1
	} else {
		var _t1615 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1615 = 1
		} else {
			var _t1616 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1616 = 1
			} else {
				var _t1617 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1617 = 1
				} else {
					var _t1618 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1618 = 0
					} else {
						var _t1619 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1619 = 1
						} else {
							var _t1620 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1620 = 1
							} else {
								var _t1621 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1621 = 1
								} else {
									var _t1622 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1622 = 1
									} else {
										var _t1623 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1623 = 1
										} else {
											var _t1624 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1624 = 1
											} else {
												var _t1625 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1625 = 1
												} else {
													var _t1626 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1626 = 1
													} else {
														var _t1627 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1627 = 1
														} else {
															_t1627 = -1
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
		}
		_t1614 = _t1615
	}
	prediction865 := _t1614
	var _t1628 *pb.Term
	if prediction865 == 1 {
		_t1629 := p.parse_value()
		value867 := _t1629
		_t1630 := &pb.Term{}
		_t1630.TermType = &pb.Term_Constant{Constant: value867}
		_t1628 = _t1630
	} else {
		var _t1631 *pb.Term
		if prediction865 == 0 {
			_t1632 := p.parse_var()
			var866 := _t1632
			_t1633 := &pb.Term{}
			_t1633.TermType = &pb.Term_Var{Var: var866}
			_t1631 = _t1633
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1628 = _t1631
	}
	result869 := _t1628
	p.recordSpan(int(span_start868), "Term")
	return result869
}

func (p *Parser) parse_var() *pb.Var {
	span_start871 := int64(p.spanStart())
	symbol870 := p.consumeTerminal("SYMBOL").Value.str
	_t1634 := &pb.Var{Name: symbol870}
	result872 := _t1634
	p.recordSpan(int(span_start871), "Var")
	return result872
}

func (p *Parser) parse_value() *pb.Value {
	span_start886 := int64(p.spanStart())
	var _t1635 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1635 = 12
	} else {
		var _t1636 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1636 = 11
		} else {
			var _t1637 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1637 = 12
			} else {
				var _t1638 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1639 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1639 = 1
					} else {
						var _t1640 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1640 = 0
						} else {
							_t1640 = -1
						}
						_t1639 = _t1640
					}
					_t1638 = _t1639
				} else {
					var _t1641 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1641 = 7
					} else {
						var _t1642 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1642 = 8
						} else {
							var _t1643 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1643 = 2
							} else {
								var _t1644 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1644 = 3
								} else {
									var _t1645 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1645 = 9
									} else {
										var _t1646 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1646 = 4
										} else {
											var _t1647 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1647 = 5
											} else {
												var _t1648 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1648 = 6
												} else {
													var _t1649 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1649 = 10
													} else {
														_t1649 = -1
													}
													_t1648 = _t1649
												}
												_t1647 = _t1648
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
					_t1638 = _t1641
				}
				_t1637 = _t1638
			}
			_t1636 = _t1637
		}
		_t1635 = _t1636
	}
	prediction873 := _t1635
	var _t1650 *pb.Value
	if prediction873 == 12 {
		_t1651 := p.parse_boolean_value()
		boolean_value885 := _t1651
		_t1652 := &pb.Value{}
		_t1652.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value885}
		_t1650 = _t1652
	} else {
		var _t1653 *pb.Value
		if prediction873 == 11 {
			p.consumeLiteral("missing")
			_t1654 := &pb.MissingValue{}
			_t1655 := &pb.Value{}
			_t1655.Value = &pb.Value_MissingValue{MissingValue: _t1654}
			_t1653 = _t1655
		} else {
			var _t1656 *pb.Value
			if prediction873 == 10 {
				formatted_decimal884 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1657 := &pb.Value{}
				_t1657.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal884}
				_t1656 = _t1657
			} else {
				var _t1658 *pb.Value
				if prediction873 == 9 {
					formatted_int128883 := p.consumeTerminal("INT128").Value.int128
					_t1659 := &pb.Value{}
					_t1659.Value = &pb.Value_Int128Value{Int128Value: formatted_int128883}
					_t1658 = _t1659
				} else {
					var _t1660 *pb.Value
					if prediction873 == 8 {
						formatted_uint128882 := p.consumeTerminal("UINT128").Value.uint128
						_t1661 := &pb.Value{}
						_t1661.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128882}
						_t1660 = _t1661
					} else {
						var _t1662 *pb.Value
						if prediction873 == 7 {
							formatted_uint32881 := p.consumeTerminal("UINT32").Value.u32
							_t1663 := &pb.Value{}
							_t1663.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32881}
							_t1662 = _t1663
						} else {
							var _t1664 *pb.Value
							if prediction873 == 6 {
								formatted_float880 := p.consumeTerminal("FLOAT").Value.f64
								_t1665 := &pb.Value{}
								_t1665.Value = &pb.Value_FloatValue{FloatValue: formatted_float880}
								_t1664 = _t1665
							} else {
								var _t1666 *pb.Value
								if prediction873 == 5 {
									formatted_float32879 := p.consumeTerminal("FLOAT32").Value.f32
									_t1667 := &pb.Value{}
									_t1667.Value = &pb.Value_Float32Value{Float32Value: formatted_float32879}
									_t1666 = _t1667
								} else {
									var _t1668 *pb.Value
									if prediction873 == 4 {
										formatted_int878 := p.consumeTerminal("INT").Value.i64
										_t1669 := &pb.Value{}
										_t1669.Value = &pb.Value_IntValue{IntValue: formatted_int878}
										_t1668 = _t1669
									} else {
										var _t1670 *pb.Value
										if prediction873 == 3 {
											formatted_int32877 := p.consumeTerminal("INT32").Value.i32
											_t1671 := &pb.Value{}
											_t1671.Value = &pb.Value_Int32Value{Int32Value: formatted_int32877}
											_t1670 = _t1671
										} else {
											var _t1672 *pb.Value
											if prediction873 == 2 {
												formatted_string876 := p.consumeTerminal("STRING").Value.str
												_t1673 := &pb.Value{}
												_t1673.Value = &pb.Value_StringValue{StringValue: formatted_string876}
												_t1672 = _t1673
											} else {
												var _t1674 *pb.Value
												if prediction873 == 1 {
													_t1675 := p.parse_datetime()
													datetime875 := _t1675
													_t1676 := &pb.Value{}
													_t1676.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime875}
													_t1674 = _t1676
												} else {
													var _t1677 *pb.Value
													if prediction873 == 0 {
														_t1678 := p.parse_date()
														date874 := _t1678
														_t1679 := &pb.Value{}
														_t1679.Value = &pb.Value_DateValue{DateValue: date874}
														_t1677 = _t1679
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1674 = _t1677
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
						_t1660 = _t1662
					}
					_t1658 = _t1660
				}
				_t1656 = _t1658
			}
			_t1653 = _t1656
		}
		_t1650 = _t1653
	}
	result887 := _t1650
	p.recordSpan(int(span_start886), "Value")
	return result887
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int888 := p.consumeTerminal("INT").Value.i64
	formatted_int_3889 := p.consumeTerminal("INT").Value.i64
	formatted_int_4890 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1680 := &pb.DateValue{Year: int32(formatted_int888), Month: int32(formatted_int_3889), Day: int32(formatted_int_4890)}
	result892 := _t1680
	p.recordSpan(int(span_start891), "DateValue")
	return result892
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int893 := p.consumeTerminal("INT").Value.i64
	formatted_int_3894 := p.consumeTerminal("INT").Value.i64
	formatted_int_4895 := p.consumeTerminal("INT").Value.i64
	formatted_int_5896 := p.consumeTerminal("INT").Value.i64
	formatted_int_6897 := p.consumeTerminal("INT").Value.i64
	formatted_int_7898 := p.consumeTerminal("INT").Value.i64
	var _t1681 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1681 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8899 := _t1681
	p.consumeLiteral(")")
	_t1682 := &pb.DateTimeValue{Year: int32(formatted_int893), Month: int32(formatted_int_3894), Day: int32(formatted_int_4895), Hour: int32(formatted_int_5896), Minute: int32(formatted_int_6897), Second: int32(formatted_int_7898), Microsecond: int32(deref(formatted_int_8899, 0))}
	result901 := _t1682
	p.recordSpan(int(span_start900), "DateTimeValue")
	return result901
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start906 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs902 := []*pb.Formula{}
	cond903 := p.matchLookaheadLiteral("(", 0)
	for cond903 {
		_t1683 := p.parse_formula()
		item904 := _t1683
		xs902 = append(xs902, item904)
		cond903 = p.matchLookaheadLiteral("(", 0)
	}
	formulas905 := xs902
	p.consumeLiteral(")")
	_t1684 := &pb.Conjunction{Args: formulas905}
	result907 := _t1684
	p.recordSpan(int(span_start906), "Conjunction")
	return result907
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start912 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs908 := []*pb.Formula{}
	cond909 := p.matchLookaheadLiteral("(", 0)
	for cond909 {
		_t1685 := p.parse_formula()
		item910 := _t1685
		xs908 = append(xs908, item910)
		cond909 = p.matchLookaheadLiteral("(", 0)
	}
	formulas911 := xs908
	p.consumeLiteral(")")
	_t1686 := &pb.Disjunction{Args: formulas911}
	result913 := _t1686
	p.recordSpan(int(span_start912), "Disjunction")
	return result913
}

func (p *Parser) parse_not() *pb.Not {
	span_start915 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1687 := p.parse_formula()
	formula914 := _t1687
	p.consumeLiteral(")")
	_t1688 := &pb.Not{Arg: formula914}
	result916 := _t1688
	p.recordSpan(int(span_start915), "Not")
	return result916
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1689 := p.parse_name()
	name917 := _t1689
	_t1690 := p.parse_ffi_args()
	ffi_args918 := _t1690
	_t1691 := p.parse_terms()
	terms919 := _t1691
	p.consumeLiteral(")")
	_t1692 := &pb.FFI{Name: name917, Args: ffi_args918, Terms: terms919}
	result921 := _t1692
	p.recordSpan(int(span_start920), "FFI")
	return result921
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol922 := p.consumeTerminal("SYMBOL").Value.str
	return symbol922
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs923 := []*pb.Abstraction{}
	cond924 := p.matchLookaheadLiteral("(", 0)
	for cond924 {
		_t1693 := p.parse_abstraction()
		item925 := _t1693
		xs923 = append(xs923, item925)
		cond924 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions926 := xs923
	p.consumeLiteral(")")
	return abstractions926
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start932 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1694 := p.parse_relation_id()
	relation_id927 := _t1694
	xs928 := []*pb.Term{}
	cond929 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond929 {
		_t1695 := p.parse_term()
		item930 := _t1695
		xs928 = append(xs928, item930)
		cond929 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms931 := xs928
	p.consumeLiteral(")")
	_t1696 := &pb.Atom{Name: relation_id927, Terms: terms931}
	result933 := _t1696
	p.recordSpan(int(span_start932), "Atom")
	return result933
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start939 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1697 := p.parse_name()
	name934 := _t1697
	xs935 := []*pb.Term{}
	cond936 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond936 {
		_t1698 := p.parse_term()
		item937 := _t1698
		xs935 = append(xs935, item937)
		cond936 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms938 := xs935
	p.consumeLiteral(")")
	_t1699 := &pb.Pragma{Name: name934, Terms: terms938}
	result940 := _t1699
	p.recordSpan(int(span_start939), "Pragma")
	return result940
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start956 := int64(p.spanStart())
	var _t1700 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1701 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1701 = 9
		} else {
			var _t1702 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1702 = 4
			} else {
				var _t1703 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1703 = 3
				} else {
					var _t1704 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1704 = 0
					} else {
						var _t1705 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1705 = 2
						} else {
							var _t1706 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1706 = 1
							} else {
								var _t1707 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1707 = 8
								} else {
									var _t1708 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1708 = 6
									} else {
										var _t1709 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1709 = 5
										} else {
											var _t1710 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1710 = 7
											} else {
												_t1710 = -1
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
	} else {
		_t1700 = -1
	}
	prediction941 := _t1700
	var _t1711 *pb.Primitive
	if prediction941 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1712 := p.parse_name()
		name951 := _t1712
		xs952 := []*pb.RelTerm{}
		cond953 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond953 {
			_t1713 := p.parse_rel_term()
			item954 := _t1713
			xs952 = append(xs952, item954)
			cond953 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms955 := xs952
		p.consumeLiteral(")")
		_t1714 := &pb.Primitive{Name: name951, Terms: rel_terms955}
		_t1711 = _t1714
	} else {
		var _t1715 *pb.Primitive
		if prediction941 == 8 {
			_t1716 := p.parse_divide()
			divide950 := _t1716
			_t1715 = divide950
		} else {
			var _t1717 *pb.Primitive
			if prediction941 == 7 {
				_t1718 := p.parse_multiply()
				multiply949 := _t1718
				_t1717 = multiply949
			} else {
				var _t1719 *pb.Primitive
				if prediction941 == 6 {
					_t1720 := p.parse_minus()
					minus948 := _t1720
					_t1719 = minus948
				} else {
					var _t1721 *pb.Primitive
					if prediction941 == 5 {
						_t1722 := p.parse_add()
						add947 := _t1722
						_t1721 = add947
					} else {
						var _t1723 *pb.Primitive
						if prediction941 == 4 {
							_t1724 := p.parse_gt_eq()
							gt_eq946 := _t1724
							_t1723 = gt_eq946
						} else {
							var _t1725 *pb.Primitive
							if prediction941 == 3 {
								_t1726 := p.parse_gt()
								gt945 := _t1726
								_t1725 = gt945
							} else {
								var _t1727 *pb.Primitive
								if prediction941 == 2 {
									_t1728 := p.parse_lt_eq()
									lt_eq944 := _t1728
									_t1727 = lt_eq944
								} else {
									var _t1729 *pb.Primitive
									if prediction941 == 1 {
										_t1730 := p.parse_lt()
										lt943 := _t1730
										_t1729 = lt943
									} else {
										var _t1731 *pb.Primitive
										if prediction941 == 0 {
											_t1732 := p.parse_eq()
											eq942 := _t1732
											_t1731 = eq942
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1719 = _t1721
				}
				_t1717 = _t1719
			}
			_t1715 = _t1717
		}
		_t1711 = _t1715
	}
	result957 := _t1711
	p.recordSpan(int(span_start956), "Primitive")
	return result957
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1733 := p.parse_term()
	term958 := _t1733
	_t1734 := p.parse_term()
	term_3959 := _t1734
	p.consumeLiteral(")")
	_t1735 := &pb.RelTerm{}
	_t1735.RelTermType = &pb.RelTerm_Term{Term: term958}
	_t1736 := &pb.RelTerm{}
	_t1736.RelTermType = &pb.RelTerm_Term{Term: term_3959}
	_t1737 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1735, _t1736}}
	result961 := _t1737
	p.recordSpan(int(span_start960), "Primitive")
	return result961
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start964 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1738 := p.parse_term()
	term962 := _t1738
	_t1739 := p.parse_term()
	term_3963 := _t1739
	p.consumeLiteral(")")
	_t1740 := &pb.RelTerm{}
	_t1740.RelTermType = &pb.RelTerm_Term{Term: term962}
	_t1741 := &pb.RelTerm{}
	_t1741.RelTermType = &pb.RelTerm_Term{Term: term_3963}
	_t1742 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1740, _t1741}}
	result965 := _t1742
	p.recordSpan(int(span_start964), "Primitive")
	return result965
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1743 := p.parse_term()
	term966 := _t1743
	_t1744 := p.parse_term()
	term_3967 := _t1744
	p.consumeLiteral(")")
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term966}
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term_3967}
	_t1747 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1745, _t1746}}
	result969 := _t1747
	p.recordSpan(int(span_start968), "Primitive")
	return result969
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1748 := p.parse_term()
	term970 := _t1748
	_t1749 := p.parse_term()
	term_3971 := _t1749
	p.consumeLiteral(")")
	_t1750 := &pb.RelTerm{}
	_t1750.RelTermType = &pb.RelTerm_Term{Term: term970}
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term_3971}
	_t1752 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1750, _t1751}}
	result973 := _t1752
	p.recordSpan(int(span_start972), "Primitive")
	return result973
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1753 := p.parse_term()
	term974 := _t1753
	_t1754 := p.parse_term()
	term_3975 := _t1754
	p.consumeLiteral(")")
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term974}
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term_3975}
	_t1757 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1755, _t1756}}
	result977 := _t1757
	p.recordSpan(int(span_start976), "Primitive")
	return result977
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start981 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1758 := p.parse_term()
	term978 := _t1758
	_t1759 := p.parse_term()
	term_3979 := _t1759
	_t1760 := p.parse_term()
	term_4980 := _t1760
	p.consumeLiteral(")")
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term978}
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term_3979}
	_t1763 := &pb.RelTerm{}
	_t1763.RelTermType = &pb.RelTerm_Term{Term: term_4980}
	_t1764 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1761, _t1762, _t1763}}
	result982 := _t1764
	p.recordSpan(int(span_start981), "Primitive")
	return result982
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1765 := p.parse_term()
	term983 := _t1765
	_t1766 := p.parse_term()
	term_3984 := _t1766
	_t1767 := p.parse_term()
	term_4985 := _t1767
	p.consumeLiteral(")")
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term983}
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term_3984}
	_t1770 := &pb.RelTerm{}
	_t1770.RelTermType = &pb.RelTerm_Term{Term: term_4985}
	_t1771 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1768, _t1769, _t1770}}
	result987 := _t1771
	p.recordSpan(int(span_start986), "Primitive")
	return result987
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start991 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1772 := p.parse_term()
	term988 := _t1772
	_t1773 := p.parse_term()
	term_3989 := _t1773
	_t1774 := p.parse_term()
	term_4990 := _t1774
	p.consumeLiteral(")")
	_t1775 := &pb.RelTerm{}
	_t1775.RelTermType = &pb.RelTerm_Term{Term: term988}
	_t1776 := &pb.RelTerm{}
	_t1776.RelTermType = &pb.RelTerm_Term{Term: term_3989}
	_t1777 := &pb.RelTerm{}
	_t1777.RelTermType = &pb.RelTerm_Term{Term: term_4990}
	_t1778 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1775, _t1776, _t1777}}
	result992 := _t1778
	p.recordSpan(int(span_start991), "Primitive")
	return result992
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start996 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1779 := p.parse_term()
	term993 := _t1779
	_t1780 := p.parse_term()
	term_3994 := _t1780
	_t1781 := p.parse_term()
	term_4995 := _t1781
	p.consumeLiteral(")")
	_t1782 := &pb.RelTerm{}
	_t1782.RelTermType = &pb.RelTerm_Term{Term: term993}
	_t1783 := &pb.RelTerm{}
	_t1783.RelTermType = &pb.RelTerm_Term{Term: term_3994}
	_t1784 := &pb.RelTerm{}
	_t1784.RelTermType = &pb.RelTerm_Term{Term: term_4995}
	_t1785 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1782, _t1783, _t1784}}
	result997 := _t1785
	p.recordSpan(int(span_start996), "Primitive")
	return result997
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1001 := int64(p.spanStart())
	var _t1786 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1786 = 1
	} else {
		var _t1787 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1787 = 1
		} else {
			var _t1788 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1788 = 1
			} else {
				var _t1789 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1789 = 1
				} else {
					var _t1790 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1790 = 0
					} else {
						var _t1791 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1791 = 1
						} else {
							var _t1792 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1792 = 1
							} else {
								var _t1793 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1793 = 1
								} else {
									var _t1794 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1794 = 1
									} else {
										var _t1795 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1795 = 1
										} else {
											var _t1796 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1796 = 1
											} else {
												var _t1797 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1797 = 1
												} else {
													var _t1798 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1798 = 1
													} else {
														var _t1799 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1799 = 1
														} else {
															var _t1800 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1800 = 1
															} else {
																_t1800 = -1
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
	prediction998 := _t1786
	var _t1801 *pb.RelTerm
	if prediction998 == 1 {
		_t1802 := p.parse_term()
		term1000 := _t1802
		_t1803 := &pb.RelTerm{}
		_t1803.RelTermType = &pb.RelTerm_Term{Term: term1000}
		_t1801 = _t1803
	} else {
		var _t1804 *pb.RelTerm
		if prediction998 == 0 {
			_t1805 := p.parse_specialized_value()
			specialized_value999 := _t1805
			_t1806 := &pb.RelTerm{}
			_t1806.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value999}
			_t1804 = _t1806
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1801 = _t1804
	}
	result1002 := _t1801
	p.recordSpan(int(span_start1001), "RelTerm")
	return result1002
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1807 := p.parse_raw_value()
	raw_value1003 := _t1807
	result1005 := raw_value1003
	p.recordSpan(int(span_start1004), "Value")
	return result1005
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1011 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1808 := p.parse_name()
	name1006 := _t1808
	xs1007 := []*pb.RelTerm{}
	cond1008 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1008 {
		_t1809 := p.parse_rel_term()
		item1009 := _t1809
		xs1007 = append(xs1007, item1009)
		cond1008 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1010 := xs1007
	p.consumeLiteral(")")
	_t1810 := &pb.RelAtom{Name: name1006, Terms: rel_terms1010}
	result1012 := _t1810
	p.recordSpan(int(span_start1011), "RelAtom")
	return result1012
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1015 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1811 := p.parse_term()
	term1013 := _t1811
	_t1812 := p.parse_term()
	term_31014 := _t1812
	p.consumeLiteral(")")
	_t1813 := &pb.Cast{Input: term1013, Result: term_31014}
	result1016 := _t1813
	p.recordSpan(int(span_start1015), "Cast")
	return result1016
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1017 := []*pb.Attribute{}
	cond1018 := p.matchLookaheadLiteral("(", 0)
	for cond1018 {
		_t1814 := p.parse_attribute()
		item1019 := _t1814
		xs1017 = append(xs1017, item1019)
		cond1018 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1020 := xs1017
	p.consumeLiteral(")")
	return attributes1020
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1815 := p.parse_name()
	name1021 := _t1815
	xs1022 := []*pb.Value{}
	cond1023 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1023 {
		_t1816 := p.parse_raw_value()
		item1024 := _t1816
		xs1022 = append(xs1022, item1024)
		cond1023 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1025 := xs1022
	p.consumeLiteral(")")
	_t1817 := &pb.Attribute{Name: name1021, Args: raw_values1025}
	result1027 := _t1817
	p.recordSpan(int(span_start1026), "Attribute")
	return result1027
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1028 := []*pb.RelationId{}
	cond1029 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1029 {
		_t1818 := p.parse_relation_id()
		item1030 := _t1818
		xs1028 = append(xs1028, item1030)
		cond1029 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1031 := xs1028
	_t1819 := p.parse_script()
	script1032 := _t1819
	var _t1820 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1821 := p.parse_attrs()
		_t1820 = _t1821
	}
	attrs1033 := _t1820
	p.consumeLiteral(")")
	_t1822 := attrs1033
	if attrs1033 == nil {
		_t1822 = []*pb.Attribute{}
	}
	_t1823 := &pb.Algorithm{Global: relation_ids1031, Body: script1032, Attrs: _t1822}
	result1035 := _t1823
	p.recordSpan(int(span_start1034), "Algorithm")
	return result1035
}

func (p *Parser) parse_script() *pb.Script {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1036 := []*pb.Construct{}
	cond1037 := p.matchLookaheadLiteral("(", 0)
	for cond1037 {
		_t1824 := p.parse_construct()
		item1038 := _t1824
		xs1036 = append(xs1036, item1038)
		cond1037 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1039 := xs1036
	p.consumeLiteral(")")
	_t1825 := &pb.Script{Constructs: constructs1039}
	result1041 := _t1825
	p.recordSpan(int(span_start1040), "Script")
	return result1041
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1045 := int64(p.spanStart())
	var _t1826 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1827 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1827 = 1
		} else {
			var _t1828 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1828 = 1
			} else {
				var _t1829 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1829 = 1
				} else {
					var _t1830 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1830 = 0
					} else {
						var _t1831 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1831 = 1
						} else {
							var _t1832 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1832 = 1
							} else {
								_t1832 = -1
							}
							_t1831 = _t1832
						}
						_t1830 = _t1831
					}
					_t1829 = _t1830
				}
				_t1828 = _t1829
			}
			_t1827 = _t1828
		}
		_t1826 = _t1827
	} else {
		_t1826 = -1
	}
	prediction1042 := _t1826
	var _t1833 *pb.Construct
	if prediction1042 == 1 {
		_t1834 := p.parse_instruction()
		instruction1044 := _t1834
		_t1835 := &pb.Construct{}
		_t1835.ConstructType = &pb.Construct_Instruction{Instruction: instruction1044}
		_t1833 = _t1835
	} else {
		var _t1836 *pb.Construct
		if prediction1042 == 0 {
			_t1837 := p.parse_loop()
			loop1043 := _t1837
			_t1838 := &pb.Construct{}
			_t1838.ConstructType = &pb.Construct_Loop{Loop: loop1043}
			_t1836 = _t1838
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1833 = _t1836
	}
	result1046 := _t1833
	p.recordSpan(int(span_start1045), "Construct")
	return result1046
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1050 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1839 := p.parse_init()
	init1047 := _t1839
	_t1840 := p.parse_script()
	script1048 := _t1840
	var _t1841 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1842 := p.parse_attrs()
		_t1841 = _t1842
	}
	attrs1049 := _t1841
	p.consumeLiteral(")")
	_t1843 := attrs1049
	if attrs1049 == nil {
		_t1843 = []*pb.Attribute{}
	}
	_t1844 := &pb.Loop{Init: init1047, Body: script1048, Attrs: _t1843}
	result1051 := _t1844
	p.recordSpan(int(span_start1050), "Loop")
	return result1051
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1052 := []*pb.Instruction{}
	cond1053 := p.matchLookaheadLiteral("(", 0)
	for cond1053 {
		_t1845 := p.parse_instruction()
		item1054 := _t1845
		xs1052 = append(xs1052, item1054)
		cond1053 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1055 := xs1052
	p.consumeLiteral(")")
	return instructions1055
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1062 := int64(p.spanStart())
	var _t1846 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1847 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1847 = 1
		} else {
			var _t1848 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1848 = 4
			} else {
				var _t1849 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1849 = 3
				} else {
					var _t1850 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1850 = 2
					} else {
						var _t1851 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1851 = 0
						} else {
							_t1851 = -1
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
	prediction1056 := _t1846
	var _t1852 *pb.Instruction
	if prediction1056 == 4 {
		_t1853 := p.parse_monus_def()
		monus_def1061 := _t1853
		_t1854 := &pb.Instruction{}
		_t1854.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1061}
		_t1852 = _t1854
	} else {
		var _t1855 *pb.Instruction
		if prediction1056 == 3 {
			_t1856 := p.parse_monoid_def()
			monoid_def1060 := _t1856
			_t1857 := &pb.Instruction{}
			_t1857.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1060}
			_t1855 = _t1857
		} else {
			var _t1858 *pb.Instruction
			if prediction1056 == 2 {
				_t1859 := p.parse_break()
				break1059 := _t1859
				_t1860 := &pb.Instruction{}
				_t1860.InstrType = &pb.Instruction_Break{Break: break1059}
				_t1858 = _t1860
			} else {
				var _t1861 *pb.Instruction
				if prediction1056 == 1 {
					_t1862 := p.parse_upsert()
					upsert1058 := _t1862
					_t1863 := &pb.Instruction{}
					_t1863.InstrType = &pb.Instruction_Upsert{Upsert: upsert1058}
					_t1861 = _t1863
				} else {
					var _t1864 *pb.Instruction
					if prediction1056 == 0 {
						_t1865 := p.parse_assign()
						assign1057 := _t1865
						_t1866 := &pb.Instruction{}
						_t1866.InstrType = &pb.Instruction_Assign{Assign: assign1057}
						_t1864 = _t1866
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1861 = _t1864
				}
				_t1858 = _t1861
			}
			_t1855 = _t1858
		}
		_t1852 = _t1855
	}
	result1063 := _t1852
	p.recordSpan(int(span_start1062), "Instruction")
	return result1063
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1067 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1867 := p.parse_relation_id()
	relation_id1064 := _t1867
	_t1868 := p.parse_abstraction()
	abstraction1065 := _t1868
	var _t1869 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1870 := p.parse_attrs()
		_t1869 = _t1870
	}
	attrs1066 := _t1869
	p.consumeLiteral(")")
	_t1871 := attrs1066
	if attrs1066 == nil {
		_t1871 = []*pb.Attribute{}
	}
	_t1872 := &pb.Assign{Name: relation_id1064, Body: abstraction1065, Attrs: _t1871}
	result1068 := _t1872
	p.recordSpan(int(span_start1067), "Assign")
	return result1068
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1072 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1873 := p.parse_relation_id()
	relation_id1069 := _t1873
	_t1874 := p.parse_abstraction_with_arity()
	abstraction_with_arity1070 := _t1874
	var _t1875 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1876 := p.parse_attrs()
		_t1875 = _t1876
	}
	attrs1071 := _t1875
	p.consumeLiteral(")")
	_t1877 := attrs1071
	if attrs1071 == nil {
		_t1877 = []*pb.Attribute{}
	}
	_t1878 := &pb.Upsert{Name: relation_id1069, Body: abstraction_with_arity1070[0].(*pb.Abstraction), Attrs: _t1877, ValueArity: abstraction_with_arity1070[1].(int64)}
	result1073 := _t1878
	p.recordSpan(int(span_start1072), "Upsert")
	return result1073
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1879 := p.parse_bindings()
	bindings1074 := _t1879
	_t1880 := p.parse_formula()
	formula1075 := _t1880
	p.consumeLiteral(")")
	_t1881 := &pb.Abstraction{Vars: listConcat(bindings1074[0].([]*pb.Binding), bindings1074[1].([]*pb.Binding)), Value: formula1075}
	return []interface{}{_t1881, int64(len(bindings1074[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1079 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1882 := p.parse_relation_id()
	relation_id1076 := _t1882
	_t1883 := p.parse_abstraction()
	abstraction1077 := _t1883
	var _t1884 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1885 := p.parse_attrs()
		_t1884 = _t1885
	}
	attrs1078 := _t1884
	p.consumeLiteral(")")
	_t1886 := attrs1078
	if attrs1078 == nil {
		_t1886 = []*pb.Attribute{}
	}
	_t1887 := &pb.Break{Name: relation_id1076, Body: abstraction1077, Attrs: _t1886}
	result1080 := _t1887
	p.recordSpan(int(span_start1079), "Break")
	return result1080
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1085 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1888 := p.parse_monoid()
	monoid1081 := _t1888
	_t1889 := p.parse_relation_id()
	relation_id1082 := _t1889
	_t1890 := p.parse_abstraction_with_arity()
	abstraction_with_arity1083 := _t1890
	var _t1891 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1892 := p.parse_attrs()
		_t1891 = _t1892
	}
	attrs1084 := _t1891
	p.consumeLiteral(")")
	_t1893 := attrs1084
	if attrs1084 == nil {
		_t1893 = []*pb.Attribute{}
	}
	_t1894 := &pb.MonoidDef{Monoid: monoid1081, Name: relation_id1082, Body: abstraction_with_arity1083[0].(*pb.Abstraction), Attrs: _t1893, ValueArity: abstraction_with_arity1083[1].(int64)}
	result1086 := _t1894
	p.recordSpan(int(span_start1085), "MonoidDef")
	return result1086
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1092 := int64(p.spanStart())
	var _t1895 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1896 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1896 = 3
		} else {
			var _t1897 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1897 = 0
			} else {
				var _t1898 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1898 = 1
				} else {
					var _t1899 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1899 = 2
					} else {
						_t1899 = -1
					}
					_t1898 = _t1899
				}
				_t1897 = _t1898
			}
			_t1896 = _t1897
		}
		_t1895 = _t1896
	} else {
		_t1895 = -1
	}
	prediction1087 := _t1895
	var _t1900 *pb.Monoid
	if prediction1087 == 3 {
		_t1901 := p.parse_sum_monoid()
		sum_monoid1091 := _t1901
		_t1902 := &pb.Monoid{}
		_t1902.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1091}
		_t1900 = _t1902
	} else {
		var _t1903 *pb.Monoid
		if prediction1087 == 2 {
			_t1904 := p.parse_max_monoid()
			max_monoid1090 := _t1904
			_t1905 := &pb.Monoid{}
			_t1905.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1090}
			_t1903 = _t1905
		} else {
			var _t1906 *pb.Monoid
			if prediction1087 == 1 {
				_t1907 := p.parse_min_monoid()
				min_monoid1089 := _t1907
				_t1908 := &pb.Monoid{}
				_t1908.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1089}
				_t1906 = _t1908
			} else {
				var _t1909 *pb.Monoid
				if prediction1087 == 0 {
					_t1910 := p.parse_or_monoid()
					or_monoid1088 := _t1910
					_t1911 := &pb.Monoid{}
					_t1911.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1088}
					_t1909 = _t1911
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1906 = _t1909
			}
			_t1903 = _t1906
		}
		_t1900 = _t1903
	}
	result1093 := _t1900
	p.recordSpan(int(span_start1092), "Monoid")
	return result1093
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1912 := &pb.OrMonoid{}
	result1095 := _t1912
	p.recordSpan(int(span_start1094), "OrMonoid")
	return result1095
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1913 := p.parse_type()
	type1096 := _t1913
	p.consumeLiteral(")")
	_t1914 := &pb.MinMonoid{Type: type1096}
	result1098 := _t1914
	p.recordSpan(int(span_start1097), "MinMonoid")
	return result1098
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1915 := p.parse_type()
	type1099 := _t1915
	p.consumeLiteral(")")
	_t1916 := &pb.MaxMonoid{Type: type1099}
	result1101 := _t1916
	p.recordSpan(int(span_start1100), "MaxMonoid")
	return result1101
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1917 := p.parse_type()
	type1102 := _t1917
	p.consumeLiteral(")")
	_t1918 := &pb.SumMonoid{Type: type1102}
	result1104 := _t1918
	p.recordSpan(int(span_start1103), "SumMonoid")
	return result1104
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1919 := p.parse_monoid()
	monoid1105 := _t1919
	_t1920 := p.parse_relation_id()
	relation_id1106 := _t1920
	_t1921 := p.parse_abstraction_with_arity()
	abstraction_with_arity1107 := _t1921
	var _t1922 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1923 := p.parse_attrs()
		_t1922 = _t1923
	}
	attrs1108 := _t1922
	p.consumeLiteral(")")
	_t1924 := attrs1108
	if attrs1108 == nil {
		_t1924 = []*pb.Attribute{}
	}
	_t1925 := &pb.MonusDef{Monoid: monoid1105, Name: relation_id1106, Body: abstraction_with_arity1107[0].(*pb.Abstraction), Attrs: _t1924, ValueArity: abstraction_with_arity1107[1].(int64)}
	result1110 := _t1925
	p.recordSpan(int(span_start1109), "MonusDef")
	return result1110
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1115 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1926 := p.parse_relation_id()
	relation_id1111 := _t1926
	_t1927 := p.parse_abstraction()
	abstraction1112 := _t1927
	_t1928 := p.parse_functional_dependency_keys()
	functional_dependency_keys1113 := _t1928
	_t1929 := p.parse_functional_dependency_values()
	functional_dependency_values1114 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.FunctionalDependency{Guard: abstraction1112, Keys: functional_dependency_keys1113, Values: functional_dependency_values1114}
	_t1931 := &pb.Constraint{Name: relation_id1111}
	_t1931.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1930}
	result1116 := _t1931
	p.recordSpan(int(span_start1115), "Constraint")
	return result1116
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1117 := []*pb.Var{}
	cond1118 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1118 {
		_t1932 := p.parse_var()
		item1119 := _t1932
		xs1117 = append(xs1117, item1119)
		cond1118 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1120 := xs1117
	p.consumeLiteral(")")
	return vars1120
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1121 := []*pb.Var{}
	cond1122 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1122 {
		_t1933 := p.parse_var()
		item1123 := _t1933
		xs1121 = append(xs1121, item1123)
		cond1122 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1124 := xs1121
	p.consumeLiteral(")")
	return vars1124
}

func (p *Parser) parse_data() *pb.Data {
	span_start1130 := int64(p.spanStart())
	var _t1934 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1935 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1935 = 3
		} else {
			var _t1936 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1936 = 0
			} else {
				var _t1937 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1937 = 2
				} else {
					var _t1938 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1938 = 1
					} else {
						_t1938 = -1
					}
					_t1937 = _t1938
				}
				_t1936 = _t1937
			}
			_t1935 = _t1936
		}
		_t1934 = _t1935
	} else {
		_t1934 = -1
	}
	prediction1125 := _t1934
	var _t1939 *pb.Data
	if prediction1125 == 3 {
		_t1940 := p.parse_iceberg_data()
		iceberg_data1129 := _t1940
		_t1941 := &pb.Data{}
		_t1941.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1129}
		_t1939 = _t1941
	} else {
		var _t1942 *pb.Data
		if prediction1125 == 2 {
			_t1943 := p.parse_csv_data()
			csv_data1128 := _t1943
			_t1944 := &pb.Data{}
			_t1944.DataType = &pb.Data_CsvData{CsvData: csv_data1128}
			_t1942 = _t1944
		} else {
			var _t1945 *pb.Data
			if prediction1125 == 1 {
				_t1946 := p.parse_betree_relation()
				betree_relation1127 := _t1946
				_t1947 := &pb.Data{}
				_t1947.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1127}
				_t1945 = _t1947
			} else {
				var _t1948 *pb.Data
				if prediction1125 == 0 {
					_t1949 := p.parse_edb()
					edb1126 := _t1949
					_t1950 := &pb.Data{}
					_t1950.DataType = &pb.Data_Edb{Edb: edb1126}
					_t1948 = _t1950
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1945 = _t1948
			}
			_t1942 = _t1945
		}
		_t1939 = _t1942
	}
	result1131 := _t1939
	p.recordSpan(int(span_start1130), "Data")
	return result1131
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1135 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1951 := p.parse_relation_id()
	relation_id1132 := _t1951
	_t1952 := p.parse_edb_path()
	edb_path1133 := _t1952
	_t1953 := p.parse_edb_types()
	edb_types1134 := _t1953
	p.consumeLiteral(")")
	_t1954 := &pb.EDB{TargetId: relation_id1132, Path: edb_path1133, Types: edb_types1134}
	result1136 := _t1954
	p.recordSpan(int(span_start1135), "EDB")
	return result1136
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1137 := []string{}
	cond1138 := p.matchLookaheadTerminal("STRING", 0)
	for cond1138 {
		item1139 := p.consumeTerminal("STRING").Value.str
		xs1137 = append(xs1137, item1139)
		cond1138 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1140 := xs1137
	p.consumeLiteral("]")
	return strings1140
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1141 := []*pb.Type{}
	cond1142 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1142 {
		_t1955 := p.parse_type()
		item1143 := _t1955
		xs1141 = append(xs1141, item1143)
		cond1142 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1144 := xs1141
	p.consumeLiteral("]")
	return types1144
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1147 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1956 := p.parse_relation_id()
	relation_id1145 := _t1956
	_t1957 := p.parse_betree_info()
	betree_info1146 := _t1957
	p.consumeLiteral(")")
	_t1958 := &pb.BeTreeRelation{Name: relation_id1145, RelationInfo: betree_info1146}
	result1148 := _t1958
	p.recordSpan(int(span_start1147), "BeTreeRelation")
	return result1148
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1152 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1959 := p.parse_betree_info_key_types()
	betree_info_key_types1149 := _t1959
	_t1960 := p.parse_betree_info_value_types()
	betree_info_value_types1150 := _t1960
	_t1961 := p.parse_config_dict()
	config_dict1151 := _t1961
	p.consumeLiteral(")")
	_t1962 := p.construct_betree_info(betree_info_key_types1149, betree_info_value_types1150, config_dict1151)
	result1153 := _t1962
	p.recordSpan(int(span_start1152), "BeTreeInfo")
	return result1153
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1154 := []*pb.Type{}
	cond1155 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1155 {
		_t1963 := p.parse_type()
		item1156 := _t1963
		xs1154 = append(xs1154, item1156)
		cond1155 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1157 := xs1154
	p.consumeLiteral(")")
	return types1157
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1158 := []*pb.Type{}
	cond1159 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1159 {
		_t1964 := p.parse_type()
		item1160 := _t1964
		xs1158 = append(xs1158, item1160)
		cond1159 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1161 := xs1158
	p.consumeLiteral(")")
	return types1161
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1166 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1965 := p.parse_csvlocator()
	csvlocator1162 := _t1965
	_t1966 := p.parse_csv_config()
	csv_config1163 := _t1966
	_t1967 := p.parse_gnf_columns()
	gnf_columns1164 := _t1967
	_t1968 := p.parse_csv_asof()
	csv_asof1165 := _t1968
	p.consumeLiteral(")")
	_t1969 := &pb.CSVData{Locator: csvlocator1162, Config: csv_config1163, Columns: gnf_columns1164, Asof: csv_asof1165}
	result1167 := _t1969
	p.recordSpan(int(span_start1166), "CSVData")
	return result1167
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1170 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1970 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1971 := p.parse_csv_locator_paths()
		_t1970 = _t1971
	}
	csv_locator_paths1168 := _t1970
	var _t1972 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1973 := p.parse_csv_locator_inline_data()
		_t1972 = ptr(_t1973)
	}
	csv_locator_inline_data1169 := _t1972
	p.consumeLiteral(")")
	_t1974 := csv_locator_paths1168
	if csv_locator_paths1168 == nil {
		_t1974 = []string{}
	}
	_t1975 := &pb.CSVLocator{Paths: _t1974, InlineData: []byte(deref(csv_locator_inline_data1169, ""))}
	result1171 := _t1975
	p.recordSpan(int(span_start1170), "CSVLocator")
	return result1171
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1172 := []string{}
	cond1173 := p.matchLookaheadTerminal("STRING", 0)
	for cond1173 {
		item1174 := p.consumeTerminal("STRING").Value.str
		xs1172 = append(xs1172, item1174)
		cond1173 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1175 := xs1172
	p.consumeLiteral(")")
	return strings1175
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	formatted_string1176 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return formatted_string1176
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1179 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1976 := p.parse_config_dict()
	config_dict1177 := _t1976
	var _t1977 [][]interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1978 := p.parse_csv_storage_integration()
		_t1977 = _t1978
	}
	csv_storage_integration1178 := _t1977
	p.consumeLiteral(")")
	_t1979 := p.construct_csv_config(config_dict1177, csv_storage_integration1178)
	result1180 := _t1979
	p.recordSpan(int(span_start1179), "CSVConfig")
	return result1180
}

func (p *Parser) parse_csv_storage_integration() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("storage_integration")
	_t1980 := p.parse_config_dict()
	config_dict1181 := _t1980
	p.consumeLiteral(")")
	return config_dict1181
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1182 := []*pb.GNFColumn{}
	cond1183 := p.matchLookaheadLiteral("(", 0)
	for cond1183 {
		_t1981 := p.parse_gnf_column()
		item1184 := _t1981
		xs1182 = append(xs1182, item1184)
		cond1183 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1185 := xs1182
	p.consumeLiteral(")")
	return gnf_columns1185
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1192 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1982 := p.parse_gnf_column_path()
	gnf_column_path1186 := _t1982
	var _t1983 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1984 := p.parse_relation_id()
		_t1983 = _t1984
	}
	relation_id1187 := _t1983
	p.consumeLiteral("[")
	xs1188 := []*pb.Type{}
	cond1189 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1189 {
		_t1985 := p.parse_type()
		item1190 := _t1985
		xs1188 = append(xs1188, item1190)
		cond1189 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1191 := xs1188
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1986 := &pb.GNFColumn{ColumnPath: gnf_column_path1186, TargetId: relation_id1187, Types: types1191}
	result1193 := _t1986
	p.recordSpan(int(span_start1192), "GNFColumn")
	return result1193
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1987 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1987 = 1
	} else {
		var _t1988 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1988 = 0
		} else {
			_t1988 = -1
		}
		_t1987 = _t1988
	}
	prediction1194 := _t1987
	var _t1989 []string
	if prediction1194 == 1 {
		p.consumeLiteral("[")
		xs1196 := []string{}
		cond1197 := p.matchLookaheadTerminal("STRING", 0)
		for cond1197 {
			item1198 := p.consumeTerminal("STRING").Value.str
			xs1196 = append(xs1196, item1198)
			cond1197 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1199 := xs1196
		p.consumeLiteral("]")
		_t1989 = strings1199
	} else {
		var _t1990 []string
		if prediction1194 == 0 {
			string1195 := p.consumeTerminal("STRING").Value.str
			_ = string1195
			_t1990 = []string{string1195}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1989 = _t1990
	}
	return _t1989
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1200 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1200
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1207 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1991 := p.parse_iceberg_locator()
	iceberg_locator1201 := _t1991
	_t1992 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1202 := _t1992
	_t1993 := p.parse_gnf_columns()
	gnf_columns1203 := _t1993
	var _t1994 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1995 := p.parse_iceberg_from_snapshot()
		_t1994 = ptr(_t1995)
	}
	iceberg_from_snapshot1204 := _t1994
	var _t1996 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1997 := p.parse_iceberg_to_snapshot()
		_t1996 = ptr(_t1997)
	}
	iceberg_to_snapshot1205 := _t1996
	_t1998 := p.parse_boolean_value()
	boolean_value1206 := _t1998
	p.consumeLiteral(")")
	_t1999 := p.construct_iceberg_data(iceberg_locator1201, iceberg_catalog_config1202, gnf_columns1203, iceberg_from_snapshot1204, iceberg_to_snapshot1205, boolean_value1206)
	result1208 := _t1999
	p.recordSpan(int(span_start1207), "IcebergData")
	return result1208
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t2000 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1209 := _t2000
	_t2001 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1210 := _t2001
	_t2002 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1211 := _t2002
	p.consumeLiteral(")")
	_t2003 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1209, Namespace: iceberg_locator_namespace1210, Warehouse: iceberg_locator_warehouse1211}
	result1213 := _t2003
	p.recordSpan(int(span_start1212), "IcebergLocator")
	return result1213
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1214 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1214
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
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

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1219 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1219
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1224 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2004 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1220 := _t2004
	var _t2005 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2006 := p.parse_iceberg_catalog_config_scope()
		_t2005 = ptr(_t2006)
	}
	iceberg_catalog_config_scope1221 := _t2005
	_t2007 := p.parse_iceberg_properties()
	iceberg_properties1222 := _t2007
	_t2008 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1223 := _t2008
	p.consumeLiteral(")")
	_t2009 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1220, iceberg_catalog_config_scope1221, iceberg_properties1222, iceberg_auth_properties1223)
	result1225 := _t2009
	p.recordSpan(int(span_start1224), "IcebergCatalogConfig")
	return result1225
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1226 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1226
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1227 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1227
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1228 := [][]interface{}{}
	cond1229 := p.matchLookaheadLiteral("(", 0)
	for cond1229 {
		_t2010 := p.parse_iceberg_property_entry()
		item1230 := _t2010
		xs1228 = append(xs1228, item1230)
		cond1229 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1231 := xs1228
	p.consumeLiteral(")")
	return iceberg_property_entrys1231
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1232 := p.consumeTerminal("STRING").Value.str
	string_31233 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1232, string_31233}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1234 := [][]interface{}{}
	cond1235 := p.matchLookaheadLiteral("(", 0)
	for cond1235 {
		_t2011 := p.parse_iceberg_masked_property_entry()
		item1236 := _t2011
		xs1234 = append(xs1234, item1236)
		cond1235 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1237 := xs1234
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1237
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1238 := p.consumeTerminal("STRING").Value.str
	string_31239 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1238, string_31239}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1240 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1240
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1241 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1241
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1243 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2012 := p.parse_fragment_id()
	fragment_id1242 := _t2012
	p.consumeLiteral(")")
	_t2013 := &pb.Undefine{FragmentId: fragment_id1242}
	result1244 := _t2013
	p.recordSpan(int(span_start1243), "Undefine")
	return result1244
}

func (p *Parser) parse_context() *pb.Context {
	span_start1249 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1245 := []*pb.RelationId{}
	cond1246 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1246 {
		_t2014 := p.parse_relation_id()
		item1247 := _t2014
		xs1245 = append(xs1245, item1247)
		cond1246 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1248 := xs1245
	p.consumeLiteral(")")
	_t2015 := &pb.Context{Relations: relation_ids1248}
	result1250 := _t2015
	p.recordSpan(int(span_start1249), "Context")
	return result1250
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1256 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2016 := p.parse_edb_path()
	edb_path1251 := _t2016
	xs1252 := []*pb.SnapshotMapping{}
	cond1253 := p.matchLookaheadLiteral("[", 0)
	for cond1253 {
		_t2017 := p.parse_snapshot_mapping()
		item1254 := _t2017
		xs1252 = append(xs1252, item1254)
		cond1253 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1255 := xs1252
	p.consumeLiteral(")")
	_t2018 := &pb.Snapshot{Prefix: edb_path1251, Mappings: snapshot_mappings1255}
	result1257 := _t2018
	p.recordSpan(int(span_start1256), "Snapshot")
	return result1257
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1260 := int64(p.spanStart())
	_t2019 := p.parse_edb_path()
	edb_path1258 := _t2019
	_t2020 := p.parse_relation_id()
	relation_id1259 := _t2020
	_t2021 := &pb.SnapshotMapping{DestinationPath: edb_path1258, SourceRelation: relation_id1259}
	result1261 := _t2021
	p.recordSpan(int(span_start1260), "SnapshotMapping")
	return result1261
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1262 := []*pb.Read{}
	cond1263 := p.matchLookaheadLiteral("(", 0)
	for cond1263 {
		_t2022 := p.parse_read()
		item1264 := _t2022
		xs1262 = append(xs1262, item1264)
		cond1263 = p.matchLookaheadLiteral("(", 0)
	}
	reads1265 := xs1262
	p.consumeLiteral(")")
	return reads1265
}

func (p *Parser) parse_read() *pb.Read {
	span_start1272 := int64(p.spanStart())
	var _t2023 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2024 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2024 = 2
		} else {
			var _t2025 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2025 = 1
			} else {
				var _t2026 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2026 = 4
				} else {
					var _t2027 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2027 = 4
					} else {
						var _t2028 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2028 = 0
						} else {
							var _t2029 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2029 = 3
							} else {
								_t2029 = -1
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
		}
		_t2023 = _t2024
	} else {
		_t2023 = -1
	}
	prediction1266 := _t2023
	var _t2030 *pb.Read
	if prediction1266 == 4 {
		_t2031 := p.parse_export()
		export1271 := _t2031
		_t2032 := &pb.Read{}
		_t2032.ReadType = &pb.Read_Export{Export: export1271}
		_t2030 = _t2032
	} else {
		var _t2033 *pb.Read
		if prediction1266 == 3 {
			_t2034 := p.parse_abort()
			abort1270 := _t2034
			_t2035 := &pb.Read{}
			_t2035.ReadType = &pb.Read_Abort{Abort: abort1270}
			_t2033 = _t2035
		} else {
			var _t2036 *pb.Read
			if prediction1266 == 2 {
				_t2037 := p.parse_what_if()
				what_if1269 := _t2037
				_t2038 := &pb.Read{}
				_t2038.ReadType = &pb.Read_WhatIf{WhatIf: what_if1269}
				_t2036 = _t2038
			} else {
				var _t2039 *pb.Read
				if prediction1266 == 1 {
					_t2040 := p.parse_output()
					output1268 := _t2040
					_t2041 := &pb.Read{}
					_t2041.ReadType = &pb.Read_Output{Output: output1268}
					_t2039 = _t2041
				} else {
					var _t2042 *pb.Read
					if prediction1266 == 0 {
						_t2043 := p.parse_demand()
						demand1267 := _t2043
						_t2044 := &pb.Read{}
						_t2044.ReadType = &pb.Read_Demand{Demand: demand1267}
						_t2042 = _t2044
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2039 = _t2042
				}
				_t2036 = _t2039
			}
			_t2033 = _t2036
		}
		_t2030 = _t2033
	}
	result1273 := _t2030
	p.recordSpan(int(span_start1272), "Read")
	return result1273
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1275 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2045 := p.parse_relation_id()
	relation_id1274 := _t2045
	p.consumeLiteral(")")
	_t2046 := &pb.Demand{RelationId: relation_id1274}
	result1276 := _t2046
	p.recordSpan(int(span_start1275), "Demand")
	return result1276
}

func (p *Parser) parse_output() *pb.Output {
	span_start1279 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2047 := p.parse_name()
	name1277 := _t2047
	_t2048 := p.parse_relation_id()
	relation_id1278 := _t2048
	p.consumeLiteral(")")
	_t2049 := &pb.Output{Name: name1277, RelationId: relation_id1278}
	result1280 := _t2049
	p.recordSpan(int(span_start1279), "Output")
	return result1280
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1283 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2050 := p.parse_name()
	name1281 := _t2050
	_t2051 := p.parse_epoch()
	epoch1282 := _t2051
	p.consumeLiteral(")")
	_t2052 := &pb.WhatIf{Branch: name1281, Epoch: epoch1282}
	result1284 := _t2052
	p.recordSpan(int(span_start1283), "WhatIf")
	return result1284
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1287 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2053 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2054 := p.parse_name()
		_t2053 = ptr(_t2054)
	}
	name1285 := _t2053
	_t2055 := p.parse_relation_id()
	relation_id1286 := _t2055
	p.consumeLiteral(")")
	_t2056 := &pb.Abort{Name: deref(name1285, "abort"), RelationId: relation_id1286}
	result1288 := _t2056
	p.recordSpan(int(span_start1287), "Abort")
	return result1288
}

func (p *Parser) parse_export() *pb.Export {
	span_start1292 := int64(p.spanStart())
	var _t2057 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2058 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2058 = 1
		} else {
			var _t2059 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2059 = 0
			} else {
				_t2059 = -1
			}
			_t2058 = _t2059
		}
		_t2057 = _t2058
	} else {
		_t2057 = -1
	}
	prediction1289 := _t2057
	var _t2060 *pb.Export
	if prediction1289 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2061 := p.parse_export_iceberg_config()
		export_iceberg_config1291 := _t2061
		p.consumeLiteral(")")
		_t2062 := &pb.Export{}
		_t2062.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1291}
		_t2060 = _t2062
	} else {
		var _t2063 *pb.Export
		if prediction1289 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2064 := p.parse_export_csv_config()
			export_csv_config1290 := _t2064
			p.consumeLiteral(")")
			_t2065 := &pb.Export{}
			_t2065.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1290}
			_t2063 = _t2065
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2060 = _t2063
	}
	result1293 := _t2060
	p.recordSpan(int(span_start1292), "Export")
	return result1293
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1301 := int64(p.spanStart())
	var _t2066 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2067 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2067 = 0
		} else {
			var _t2068 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2068 = 1
			} else {
				_t2068 = -1
			}
			_t2067 = _t2068
		}
		_t2066 = _t2067
	} else {
		_t2066 = -1
	}
	prediction1294 := _t2066
	var _t2069 *pb.ExportCSVConfig
	if prediction1294 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2070 := p.parse_export_csv_path()
		export_csv_path1298 := _t2070
		_t2071 := p.parse_export_csv_columns_list()
		export_csv_columns_list1299 := _t2071
		_t2072 := p.parse_config_dict()
		config_dict1300 := _t2072
		p.consumeLiteral(")")
		_t2073 := p.construct_export_csv_config(export_csv_path1298, export_csv_columns_list1299, config_dict1300)
		_t2069 = _t2073
	} else {
		var _t2074 *pb.ExportCSVConfig
		if prediction1294 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2075 := p.parse_export_csv_path()
			export_csv_path1295 := _t2075
			_t2076 := p.parse_export_csv_source()
			export_csv_source1296 := _t2076
			_t2077 := p.parse_csv_config()
			csv_config1297 := _t2077
			p.consumeLiteral(")")
			_t2078 := p.construct_export_csv_config_with_source(export_csv_path1295, export_csv_source1296, csv_config1297)
			_t2074 = _t2078
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2069 = _t2074
	}
	result1302 := _t2069
	p.recordSpan(int(span_start1301), "ExportCSVConfig")
	return result1302
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1303 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1303
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1310 := int64(p.spanStart())
	var _t2079 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2080 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2080 = 1
		} else {
			var _t2081 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
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
	prediction1304 := _t2079
	var _t2082 *pb.ExportCSVSource
	if prediction1304 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2083 := p.parse_relation_id()
		relation_id1309 := _t2083
		p.consumeLiteral(")")
		_t2084 := &pb.ExportCSVSource{}
		_t2084.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1309}
		_t2082 = _t2084
	} else {
		var _t2085 *pb.ExportCSVSource
		if prediction1304 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1305 := []*pb.ExportCSVColumn{}
			cond1306 := p.matchLookaheadLiteral("(", 0)
			for cond1306 {
				_t2086 := p.parse_export_csv_column()
				item1307 := _t2086
				xs1305 = append(xs1305, item1307)
				cond1306 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1308 := xs1305
			p.consumeLiteral(")")
			_t2087 := &pb.ExportCSVColumns{Columns: export_csv_columns1308}
			_t2088 := &pb.ExportCSVSource{}
			_t2088.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2087}
			_t2085 = _t2088
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2082 = _t2085
	}
	result1311 := _t2082
	p.recordSpan(int(span_start1310), "ExportCSVSource")
	return result1311
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1314 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1312 := p.consumeTerminal("STRING").Value.str
	_t2089 := p.parse_relation_id()
	relation_id1313 := _t2089
	p.consumeLiteral(")")
	_t2090 := &pb.ExportCSVColumn{ColumnName: string1312, ColumnData: relation_id1313}
	result1315 := _t2090
	p.recordSpan(int(span_start1314), "ExportCSVColumn")
	return result1315
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1316 := []*pb.ExportCSVColumn{}
	cond1317 := p.matchLookaheadLiteral("(", 0)
	for cond1317 {
		_t2091 := p.parse_export_csv_column()
		item1318 := _t2091
		xs1316 = append(xs1316, item1318)
		cond1317 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1319 := xs1316
	p.consumeLiteral(")")
	return export_csv_columns1319
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1325 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2092 := p.parse_iceberg_locator()
	iceberg_locator1320 := _t2092
	_t2093 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1321 := _t2093
	_t2094 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1322 := _t2094
	_t2095 := p.parse_iceberg_table_properties()
	iceberg_table_properties1323 := _t2095
	var _t2096 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2097 := p.parse_config_dict()
		_t2096 = _t2097
	}
	config_dict1324 := _t2096
	p.consumeLiteral(")")
	_t2098 := p.construct_export_iceberg_config_full(iceberg_locator1320, iceberg_catalog_config1321, export_iceberg_table_def1322, iceberg_table_properties1323, config_dict1324)
	result1326 := _t2098
	p.recordSpan(int(span_start1325), "ExportIcebergConfig")
	return result1326
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1328 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2099 := p.parse_relation_id()
	relation_id1327 := _t2099
	p.consumeLiteral(")")
	result1329 := relation_id1327
	p.recordSpan(int(span_start1328), "RelationId")
	return result1329
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1330 := [][]interface{}{}
	cond1331 := p.matchLookaheadLiteral("(", 0)
	for cond1331 {
		_t2100 := p.parse_iceberg_property_entry()
		item1332 := _t2100
		xs1330 = append(xs1330, item1332)
		cond1331 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1333 := xs1330
	p.consumeLiteral(")")
	return iceberg_property_entrys1333
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
