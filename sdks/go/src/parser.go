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
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_./#-]*`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanSymbol(s)} }},
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
	var _t2050 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2050
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2051 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2051
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2052 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2052
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2053 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2053
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2054 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2054
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2055 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2055
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2056 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2056
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2057 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2057
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2058 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2058
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2059 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2059
	_t2060 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2060
	_t2061 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2061
	_t2062 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2062
	_t2063 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2063
	_t2064 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2064
	_t2065 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2065
	_t2066 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2066
	_t2067 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2067
	_t2068 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2068
	_t2069 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2069
	_t2070 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2070
	_t2071 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2071
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2072 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2072
	_t2073 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2073
	_t2074 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2074
	_t2075 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2075
	_t2076 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2076
	_t2077 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2077
	_t2078 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2078
	_t2079 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2079
	_t2080 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2080
	_t2081 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2081.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2081.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2081
	_t2082 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2082
}

func (p *Parser) default_configure() *pb.Configure {
	_t2083 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2083
	_t2084 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2084
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
	_t2085 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2085
	_t2086 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2086
	_t2087 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2087
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2088 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2088
	_t2089 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2089
	_t2090 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2090
	_t2091 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2091
	_t2092 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2092
	_t2093 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2093
	_t2094 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2094
	_t2095 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2095
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2096 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2096
}

func (p *Parser) construct_iceberg_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	scope_pb := deref(scope_opt, "")
	_t2097 := &pb.IcebergConfig{CatalogUri: catalog_uri, Scope: scope_pb, Properties: props, AuthProperties: auth_props}
	return _t2097
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergConfig, columns []*pb.IcebergExportColumn, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	prefix := ""
	target_file_size_bytes := int64(0)
	compression := ""
	if config_dict != nil {
		cfg := dictFromList(config_dict)
		_t2098 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
		prefix = _t2098
		_t2099 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
		target_file_size_bytes = _t2099
		_t2100 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
		compression = _t2100
	}
	_t2101 := &pb.ExportIcebergConfig{Locator: locator, Config: config, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression}
	return _t2101
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start657 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1302 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1303 := p.parse_configure()
		_t1302 = _t1303
	}
	configure651 := _t1302
	var _t1304 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1305 := p.parse_sync()
		_t1304 = _t1305
	}
	sync652 := _t1304
	xs653 := []*pb.Epoch{}
	cond654 := p.matchLookaheadLiteral("(", 0)
	for cond654 {
		_t1306 := p.parse_epoch()
		item655 := _t1306
		xs653 = append(xs653, item655)
		cond654 = p.matchLookaheadLiteral("(", 0)
	}
	epochs656 := xs653
	p.consumeLiteral(")")
	_t1307 := p.default_configure()
	_t1308 := configure651
	if configure651 == nil {
		_t1308 = _t1307
	}
	_t1309 := &pb.Transaction{Epochs: epochs656, Configure: _t1308, Sync: sync652}
	result658 := _t1309
	p.recordSpan(int(span_start657), "Transaction")
	return result658
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start660 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1310 := p.parse_config_dict()
	config_dict659 := _t1310
	p.consumeLiteral(")")
	_t1311 := p.construct_configure(config_dict659)
	result661 := _t1311
	p.recordSpan(int(span_start660), "Configure")
	return result661
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs662 := [][]interface{}{}
	cond663 := p.matchLookaheadLiteral(":", 0)
	for cond663 {
		_t1312 := p.parse_config_key_value()
		item664 := _t1312
		xs662 = append(xs662, item664)
		cond663 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values665 := xs662
	p.consumeLiteral("}")
	return config_key_values665
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol666 := p.consumeTerminal("SYMBOL").Value.str
	_t1313 := p.parse_raw_value()
	raw_value667 := _t1313
	return []interface{}{symbol666, raw_value667}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start681 := int64(p.spanStart())
	var _t1314 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1314 = 12
	} else {
		var _t1315 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1315 = 11
		} else {
			var _t1316 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1316 = 12
			} else {
				var _t1317 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1318 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1318 = 1
					} else {
						var _t1319 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1319 = 0
						} else {
							_t1319 = -1
						}
						_t1318 = _t1319
					}
					_t1317 = _t1318
				} else {
					var _t1320 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1320 = 7
					} else {
						var _t1321 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1321 = 8
						} else {
							var _t1322 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1322 = 2
							} else {
								var _t1323 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1323 = 3
								} else {
									var _t1324 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1324 = 9
									} else {
										var _t1325 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1325 = 4
										} else {
											var _t1326 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1326 = 5
											} else {
												var _t1327 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1327 = 6
												} else {
													var _t1328 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1328 = 10
													} else {
														_t1328 = -1
													}
													_t1327 = _t1328
												}
												_t1326 = _t1327
											}
											_t1325 = _t1326
										}
										_t1324 = _t1325
									}
									_t1323 = _t1324
								}
								_t1322 = _t1323
							}
							_t1321 = _t1322
						}
						_t1320 = _t1321
					}
					_t1317 = _t1320
				}
				_t1316 = _t1317
			}
			_t1315 = _t1316
		}
		_t1314 = _t1315
	}
	prediction668 := _t1314
	var _t1329 *pb.Value
	if prediction668 == 12 {
		_t1330 := p.parse_boolean_value()
		boolean_value680 := _t1330
		_t1331 := &pb.Value{}
		_t1331.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value680}
		_t1329 = _t1331
	} else {
		var _t1332 *pb.Value
		if prediction668 == 11 {
			p.consumeLiteral("missing")
			_t1333 := &pb.MissingValue{}
			_t1334 := &pb.Value{}
			_t1334.Value = &pb.Value_MissingValue{MissingValue: _t1333}
			_t1332 = _t1334
		} else {
			var _t1335 *pb.Value
			if prediction668 == 10 {
				decimal679 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1336 := &pb.Value{}
				_t1336.Value = &pb.Value_DecimalValue{DecimalValue: decimal679}
				_t1335 = _t1336
			} else {
				var _t1337 *pb.Value
				if prediction668 == 9 {
					int128678 := p.consumeTerminal("INT128").Value.int128
					_t1338 := &pb.Value{}
					_t1338.Value = &pb.Value_Int128Value{Int128Value: int128678}
					_t1337 = _t1338
				} else {
					var _t1339 *pb.Value
					if prediction668 == 8 {
						uint128677 := p.consumeTerminal("UINT128").Value.uint128
						_t1340 := &pb.Value{}
						_t1340.Value = &pb.Value_Uint128Value{Uint128Value: uint128677}
						_t1339 = _t1340
					} else {
						var _t1341 *pb.Value
						if prediction668 == 7 {
							uint32676 := p.consumeTerminal("UINT32").Value.u32
							_t1342 := &pb.Value{}
							_t1342.Value = &pb.Value_Uint32Value{Uint32Value: uint32676}
							_t1341 = _t1342
						} else {
							var _t1343 *pb.Value
							if prediction668 == 6 {
								float675 := p.consumeTerminal("FLOAT").Value.f64
								_t1344 := &pb.Value{}
								_t1344.Value = &pb.Value_FloatValue{FloatValue: float675}
								_t1343 = _t1344
							} else {
								var _t1345 *pb.Value
								if prediction668 == 5 {
									float32674 := p.consumeTerminal("FLOAT32").Value.f32
									_t1346 := &pb.Value{}
									_t1346.Value = &pb.Value_Float32Value{Float32Value: float32674}
									_t1345 = _t1346
								} else {
									var _t1347 *pb.Value
									if prediction668 == 4 {
										int673 := p.consumeTerminal("INT").Value.i64
										_t1348 := &pb.Value{}
										_t1348.Value = &pb.Value_IntValue{IntValue: int673}
										_t1347 = _t1348
									} else {
										var _t1349 *pb.Value
										if prediction668 == 3 {
											int32672 := p.consumeTerminal("INT32").Value.i32
											_t1350 := &pb.Value{}
											_t1350.Value = &pb.Value_Int32Value{Int32Value: int32672}
											_t1349 = _t1350
										} else {
											var _t1351 *pb.Value
											if prediction668 == 2 {
												string671 := p.consumeTerminal("STRING").Value.str
												_t1352 := &pb.Value{}
												_t1352.Value = &pb.Value_StringValue{StringValue: string671}
												_t1351 = _t1352
											} else {
												var _t1353 *pb.Value
												if prediction668 == 1 {
													_t1354 := p.parse_raw_datetime()
													raw_datetime670 := _t1354
													_t1355 := &pb.Value{}
													_t1355.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime670}
													_t1353 = _t1355
												} else {
													var _t1356 *pb.Value
													if prediction668 == 0 {
														_t1357 := p.parse_raw_date()
														raw_date669 := _t1357
														_t1358 := &pb.Value{}
														_t1358.Value = &pb.Value_DateValue{DateValue: raw_date669}
														_t1356 = _t1358
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1353 = _t1356
												}
												_t1351 = _t1353
											}
											_t1349 = _t1351
										}
										_t1347 = _t1349
									}
									_t1345 = _t1347
								}
								_t1343 = _t1345
							}
							_t1341 = _t1343
						}
						_t1339 = _t1341
					}
					_t1337 = _t1339
				}
				_t1335 = _t1337
			}
			_t1332 = _t1335
		}
		_t1329 = _t1332
	}
	result682 := _t1329
	p.recordSpan(int(span_start681), "Value")
	return result682
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start686 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int683 := p.consumeTerminal("INT").Value.i64
	int_3684 := p.consumeTerminal("INT").Value.i64
	int_4685 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1359 := &pb.DateValue{Year: int32(int683), Month: int32(int_3684), Day: int32(int_4685)}
	result687 := _t1359
	p.recordSpan(int(span_start686), "DateValue")
	return result687
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start695 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int688 := p.consumeTerminal("INT").Value.i64
	int_3689 := p.consumeTerminal("INT").Value.i64
	int_4690 := p.consumeTerminal("INT").Value.i64
	int_5691 := p.consumeTerminal("INT").Value.i64
	int_6692 := p.consumeTerminal("INT").Value.i64
	int_7693 := p.consumeTerminal("INT").Value.i64
	var _t1360 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1360 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8694 := _t1360
	p.consumeLiteral(")")
	_t1361 := &pb.DateTimeValue{Year: int32(int688), Month: int32(int_3689), Day: int32(int_4690), Hour: int32(int_5691), Minute: int32(int_6692), Second: int32(int_7693), Microsecond: int32(deref(int_8694, 0))}
	result696 := _t1361
	p.recordSpan(int(span_start695), "DateTimeValue")
	return result696
}

func (p *Parser) parse_boolean_value() bool {
	var _t1362 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1362 = 0
	} else {
		var _t1363 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1363 = 1
		} else {
			_t1363 = -1
		}
		_t1362 = _t1363
	}
	prediction697 := _t1362
	var _t1364 bool
	if prediction697 == 1 {
		p.consumeLiteral("false")
		_t1364 = false
	} else {
		var _t1365 bool
		if prediction697 == 0 {
			p.consumeLiteral("true")
			_t1365 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1364 = _t1365
	}
	return _t1364
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start702 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs698 := []*pb.FragmentId{}
	cond699 := p.matchLookaheadLiteral(":", 0)
	for cond699 {
		_t1366 := p.parse_fragment_id()
		item700 := _t1366
		xs698 = append(xs698, item700)
		cond699 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids701 := xs698
	p.consumeLiteral(")")
	_t1367 := &pb.Sync{Fragments: fragment_ids701}
	result703 := _t1367
	p.recordSpan(int(span_start702), "Sync")
	return result703
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start705 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol704 := p.consumeTerminal("SYMBOL").Value.str
	result706 := &pb.FragmentId{Id: []byte(symbol704)}
	p.recordSpan(int(span_start705), "FragmentId")
	return result706
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1368 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1369 := p.parse_epoch_writes()
		_t1368 = _t1369
	}
	epoch_writes707 := _t1368
	var _t1370 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1371 := p.parse_epoch_reads()
		_t1370 = _t1371
	}
	epoch_reads708 := _t1370
	p.consumeLiteral(")")
	_t1372 := epoch_writes707
	if epoch_writes707 == nil {
		_t1372 = []*pb.Write{}
	}
	_t1373 := epoch_reads708
	if epoch_reads708 == nil {
		_t1373 = []*pb.Read{}
	}
	_t1374 := &pb.Epoch{Writes: _t1372, Reads: _t1373}
	result710 := _t1374
	p.recordSpan(int(span_start709), "Epoch")
	return result710
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs711 := []*pb.Write{}
	cond712 := p.matchLookaheadLiteral("(", 0)
	for cond712 {
		_t1375 := p.parse_write()
		item713 := _t1375
		xs711 = append(xs711, item713)
		cond712 = p.matchLookaheadLiteral("(", 0)
	}
	writes714 := xs711
	p.consumeLiteral(")")
	return writes714
}

func (p *Parser) parse_write() *pb.Write {
	span_start720 := int64(p.spanStart())
	var _t1376 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1377 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1377 = 1
		} else {
			var _t1378 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1378 = 3
			} else {
				var _t1379 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1379 = 0
				} else {
					var _t1380 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1380 = 2
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
	} else {
		_t1376 = -1
	}
	prediction715 := _t1376
	var _t1381 *pb.Write
	if prediction715 == 3 {
		_t1382 := p.parse_snapshot()
		snapshot719 := _t1382
		_t1383 := &pb.Write{}
		_t1383.WriteType = &pb.Write_Snapshot{Snapshot: snapshot719}
		_t1381 = _t1383
	} else {
		var _t1384 *pb.Write
		if prediction715 == 2 {
			_t1385 := p.parse_context()
			context718 := _t1385
			_t1386 := &pb.Write{}
			_t1386.WriteType = &pb.Write_Context{Context: context718}
			_t1384 = _t1386
		} else {
			var _t1387 *pb.Write
			if prediction715 == 1 {
				_t1388 := p.parse_undefine()
				undefine717 := _t1388
				_t1389 := &pb.Write{}
				_t1389.WriteType = &pb.Write_Undefine{Undefine: undefine717}
				_t1387 = _t1389
			} else {
				var _t1390 *pb.Write
				if prediction715 == 0 {
					_t1391 := p.parse_define()
					define716 := _t1391
					_t1392 := &pb.Write{}
					_t1392.WriteType = &pb.Write_Define{Define: define716}
					_t1390 = _t1392
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1387 = _t1390
			}
			_t1384 = _t1387
		}
		_t1381 = _t1384
	}
	result721 := _t1381
	p.recordSpan(int(span_start720), "Write")
	return result721
}

func (p *Parser) parse_define() *pb.Define {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1393 := p.parse_fragment()
	fragment722 := _t1393
	p.consumeLiteral(")")
	_t1394 := &pb.Define{Fragment: fragment722}
	result724 := _t1394
	p.recordSpan(int(span_start723), "Define")
	return result724
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start730 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1395 := p.parse_new_fragment_id()
	new_fragment_id725 := _t1395
	xs726 := []*pb.Declaration{}
	cond727 := p.matchLookaheadLiteral("(", 0)
	for cond727 {
		_t1396 := p.parse_declaration()
		item728 := _t1396
		xs726 = append(xs726, item728)
		cond727 = p.matchLookaheadLiteral("(", 0)
	}
	declarations729 := xs726
	p.consumeLiteral(")")
	result731 := p.constructFragment(new_fragment_id725, declarations729)
	p.recordSpan(int(span_start730), "Fragment")
	return result731
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start733 := int64(p.spanStart())
	_t1397 := p.parse_fragment_id()
	fragment_id732 := _t1397
	p.startFragment(fragment_id732)
	result734 := fragment_id732
	p.recordSpan(int(span_start733), "FragmentId")
	return result734
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start740 := int64(p.spanStart())
	var _t1398 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1399 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1399 = 3
		} else {
			var _t1400 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1400 = 2
			} else {
				var _t1401 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1401 = 3
				} else {
					var _t1402 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1402 = 0
					} else {
						var _t1403 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1403 = 3
						} else {
							var _t1404 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1404 = 3
							} else {
								var _t1405 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1405 = 1
								} else {
									_t1405 = -1
								}
								_t1404 = _t1405
							}
							_t1403 = _t1404
						}
						_t1402 = _t1403
					}
					_t1401 = _t1402
				}
				_t1400 = _t1401
			}
			_t1399 = _t1400
		}
		_t1398 = _t1399
	} else {
		_t1398 = -1
	}
	prediction735 := _t1398
	var _t1406 *pb.Declaration
	if prediction735 == 3 {
		_t1407 := p.parse_data()
		data739 := _t1407
		_t1408 := &pb.Declaration{}
		_t1408.DeclarationType = &pb.Declaration_Data{Data: data739}
		_t1406 = _t1408
	} else {
		var _t1409 *pb.Declaration
		if prediction735 == 2 {
			_t1410 := p.parse_constraint()
			constraint738 := _t1410
			_t1411 := &pb.Declaration{}
			_t1411.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint738}
			_t1409 = _t1411
		} else {
			var _t1412 *pb.Declaration
			if prediction735 == 1 {
				_t1413 := p.parse_algorithm()
				algorithm737 := _t1413
				_t1414 := &pb.Declaration{}
				_t1414.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm737}
				_t1412 = _t1414
			} else {
				var _t1415 *pb.Declaration
				if prediction735 == 0 {
					_t1416 := p.parse_def()
					def736 := _t1416
					_t1417 := &pb.Declaration{}
					_t1417.DeclarationType = &pb.Declaration_Def{Def: def736}
					_t1415 = _t1417
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1412 = _t1415
			}
			_t1409 = _t1412
		}
		_t1406 = _t1409
	}
	result741 := _t1406
	p.recordSpan(int(span_start740), "Declaration")
	return result741
}

func (p *Parser) parse_def() *pb.Def {
	span_start745 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1418 := p.parse_relation_id()
	relation_id742 := _t1418
	_t1419 := p.parse_abstraction()
	abstraction743 := _t1419
	var _t1420 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1421 := p.parse_attrs()
		_t1420 = _t1421
	}
	attrs744 := _t1420
	p.consumeLiteral(")")
	_t1422 := attrs744
	if attrs744 == nil {
		_t1422 = []*pb.Attribute{}
	}
	_t1423 := &pb.Def{Name: relation_id742, Body: abstraction743, Attrs: _t1422}
	result746 := _t1423
	p.recordSpan(int(span_start745), "Def")
	return result746
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start750 := int64(p.spanStart())
	var _t1424 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1424 = 0
	} else {
		var _t1425 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1425 = 1
		} else {
			_t1425 = -1
		}
		_t1424 = _t1425
	}
	prediction747 := _t1424
	var _t1426 *pb.RelationId
	if prediction747 == 1 {
		uint128749 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128749
		_t1426 = &pb.RelationId{IdLow: uint128749.Low, IdHigh: uint128749.High}
	} else {
		var _t1427 *pb.RelationId
		if prediction747 == 0 {
			p.consumeLiteral(":")
			symbol748 := p.consumeTerminal("SYMBOL").Value.str
			_t1427 = p.relationIdFromString(symbol748)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1426 = _t1427
	}
	result751 := _t1426
	p.recordSpan(int(span_start750), "RelationId")
	return result751
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start754 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1428 := p.parse_bindings()
	bindings752 := _t1428
	_t1429 := p.parse_formula()
	formula753 := _t1429
	p.consumeLiteral(")")
	_t1430 := &pb.Abstraction{Vars: listConcat(bindings752[0].([]*pb.Binding), bindings752[1].([]*pb.Binding)), Value: formula753}
	result755 := _t1430
	p.recordSpan(int(span_start754), "Abstraction")
	return result755
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs756 := []*pb.Binding{}
	cond757 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond757 {
		_t1431 := p.parse_binding()
		item758 := _t1431
		xs756 = append(xs756, item758)
		cond757 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings759 := xs756
	var _t1432 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1433 := p.parse_value_bindings()
		_t1432 = _t1433
	}
	value_bindings760 := _t1432
	p.consumeLiteral("]")
	_t1434 := value_bindings760
	if value_bindings760 == nil {
		_t1434 = []*pb.Binding{}
	}
	return []interface{}{bindings759, _t1434}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start763 := int64(p.spanStart())
	symbol761 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1435 := p.parse_type()
	type762 := _t1435
	_t1436 := &pb.Var{Name: symbol761}
	_t1437 := &pb.Binding{Var: _t1436, Type: type762}
	result764 := _t1437
	p.recordSpan(int(span_start763), "Binding")
	return result764
}

func (p *Parser) parse_type() *pb.Type {
	span_start780 := int64(p.spanStart())
	var _t1438 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1438 = 0
	} else {
		var _t1439 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1439 = 13
		} else {
			var _t1440 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1440 = 4
			} else {
				var _t1441 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1441 = 1
				} else {
					var _t1442 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1442 = 8
					} else {
						var _t1443 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1443 = 11
						} else {
							var _t1444 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1444 = 5
							} else {
								var _t1445 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1445 = 2
								} else {
									var _t1446 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1446 = 12
									} else {
										var _t1447 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1447 = 3
										} else {
											var _t1448 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1448 = 7
											} else {
												var _t1449 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1449 = 6
												} else {
													var _t1450 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1450 = 10
													} else {
														var _t1451 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1451 = 9
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
	prediction765 := _t1438
	var _t1452 *pb.Type
	if prediction765 == 13 {
		_t1453 := p.parse_uint32_type()
		uint32_type779 := _t1453
		_t1454 := &pb.Type{}
		_t1454.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type779}
		_t1452 = _t1454
	} else {
		var _t1455 *pb.Type
		if prediction765 == 12 {
			_t1456 := p.parse_float32_type()
			float32_type778 := _t1456
			_t1457 := &pb.Type{}
			_t1457.Type = &pb.Type_Float32Type{Float32Type: float32_type778}
			_t1455 = _t1457
		} else {
			var _t1458 *pb.Type
			if prediction765 == 11 {
				_t1459 := p.parse_int32_type()
				int32_type777 := _t1459
				_t1460 := &pb.Type{}
				_t1460.Type = &pb.Type_Int32Type{Int32Type: int32_type777}
				_t1458 = _t1460
			} else {
				var _t1461 *pb.Type
				if prediction765 == 10 {
					_t1462 := p.parse_boolean_type()
					boolean_type776 := _t1462
					_t1463 := &pb.Type{}
					_t1463.Type = &pb.Type_BooleanType{BooleanType: boolean_type776}
					_t1461 = _t1463
				} else {
					var _t1464 *pb.Type
					if prediction765 == 9 {
						_t1465 := p.parse_decimal_type()
						decimal_type775 := _t1465
						_t1466 := &pb.Type{}
						_t1466.Type = &pb.Type_DecimalType{DecimalType: decimal_type775}
						_t1464 = _t1466
					} else {
						var _t1467 *pb.Type
						if prediction765 == 8 {
							_t1468 := p.parse_missing_type()
							missing_type774 := _t1468
							_t1469 := &pb.Type{}
							_t1469.Type = &pb.Type_MissingType{MissingType: missing_type774}
							_t1467 = _t1469
						} else {
							var _t1470 *pb.Type
							if prediction765 == 7 {
								_t1471 := p.parse_datetime_type()
								datetime_type773 := _t1471
								_t1472 := &pb.Type{}
								_t1472.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type773}
								_t1470 = _t1472
							} else {
								var _t1473 *pb.Type
								if prediction765 == 6 {
									_t1474 := p.parse_date_type()
									date_type772 := _t1474
									_t1475 := &pb.Type{}
									_t1475.Type = &pb.Type_DateType{DateType: date_type772}
									_t1473 = _t1475
								} else {
									var _t1476 *pb.Type
									if prediction765 == 5 {
										_t1477 := p.parse_int128_type()
										int128_type771 := _t1477
										_t1478 := &pb.Type{}
										_t1478.Type = &pb.Type_Int128Type{Int128Type: int128_type771}
										_t1476 = _t1478
									} else {
										var _t1479 *pb.Type
										if prediction765 == 4 {
											_t1480 := p.parse_uint128_type()
											uint128_type770 := _t1480
											_t1481 := &pb.Type{}
											_t1481.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type770}
											_t1479 = _t1481
										} else {
											var _t1482 *pb.Type
											if prediction765 == 3 {
												_t1483 := p.parse_float_type()
												float_type769 := _t1483
												_t1484 := &pb.Type{}
												_t1484.Type = &pb.Type_FloatType{FloatType: float_type769}
												_t1482 = _t1484
											} else {
												var _t1485 *pb.Type
												if prediction765 == 2 {
													_t1486 := p.parse_int_type()
													int_type768 := _t1486
													_t1487 := &pb.Type{}
													_t1487.Type = &pb.Type_IntType{IntType: int_type768}
													_t1485 = _t1487
												} else {
													var _t1488 *pb.Type
													if prediction765 == 1 {
														_t1489 := p.parse_string_type()
														string_type767 := _t1489
														_t1490 := &pb.Type{}
														_t1490.Type = &pb.Type_StringType{StringType: string_type767}
														_t1488 = _t1490
													} else {
														var _t1491 *pb.Type
														if prediction765 == 0 {
															_t1492 := p.parse_unspecified_type()
															unspecified_type766 := _t1492
															_t1493 := &pb.Type{}
															_t1493.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type766}
															_t1491 = _t1493
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1488 = _t1491
													}
													_t1485 = _t1488
												}
												_t1482 = _t1485
											}
											_t1479 = _t1482
										}
										_t1476 = _t1479
									}
									_t1473 = _t1476
								}
								_t1470 = _t1473
							}
							_t1467 = _t1470
						}
						_t1464 = _t1467
					}
					_t1461 = _t1464
				}
				_t1458 = _t1461
			}
			_t1455 = _t1458
		}
		_t1452 = _t1455
	}
	result781 := _t1452
	p.recordSpan(int(span_start780), "Type")
	return result781
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start782 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1494 := &pb.UnspecifiedType{}
	result783 := _t1494
	p.recordSpan(int(span_start782), "UnspecifiedType")
	return result783
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start784 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1495 := &pb.StringType{}
	result785 := _t1495
	p.recordSpan(int(span_start784), "StringType")
	return result785
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start786 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1496 := &pb.IntType{}
	result787 := _t1496
	p.recordSpan(int(span_start786), "IntType")
	return result787
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start788 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1497 := &pb.FloatType{}
	result789 := _t1497
	p.recordSpan(int(span_start788), "FloatType")
	return result789
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start790 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1498 := &pb.UInt128Type{}
	result791 := _t1498
	p.recordSpan(int(span_start790), "UInt128Type")
	return result791
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start792 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1499 := &pb.Int128Type{}
	result793 := _t1499
	p.recordSpan(int(span_start792), "Int128Type")
	return result793
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start794 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1500 := &pb.DateType{}
	result795 := _t1500
	p.recordSpan(int(span_start794), "DateType")
	return result795
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1501 := &pb.DateTimeType{}
	result797 := _t1501
	p.recordSpan(int(span_start796), "DateTimeType")
	return result797
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1502 := &pb.MissingType{}
	result799 := _t1502
	p.recordSpan(int(span_start798), "MissingType")
	return result799
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int800 := p.consumeTerminal("INT").Value.i64
	int_3801 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1503 := &pb.DecimalType{Precision: int32(int800), Scale: int32(int_3801)}
	result803 := _t1503
	p.recordSpan(int(span_start802), "DecimalType")
	return result803
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1504 := &pb.BooleanType{}
	result805 := _t1504
	p.recordSpan(int(span_start804), "BooleanType")
	return result805
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1505 := &pb.Int32Type{}
	result807 := _t1505
	p.recordSpan(int(span_start806), "Int32Type")
	return result807
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1506 := &pb.Float32Type{}
	result809 := _t1506
	p.recordSpan(int(span_start808), "Float32Type")
	return result809
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1507 := &pb.UInt32Type{}
	result811 := _t1507
	p.recordSpan(int(span_start810), "UInt32Type")
	return result811
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs812 := []*pb.Binding{}
	cond813 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond813 {
		_t1508 := p.parse_binding()
		item814 := _t1508
		xs812 = append(xs812, item814)
		cond813 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings815 := xs812
	return bindings815
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start830 := int64(p.spanStart())
	var _t1509 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1510 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1510 = 0
		} else {
			var _t1511 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1511 = 11
			} else {
				var _t1512 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1512 = 3
				} else {
					var _t1513 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1513 = 10
					} else {
						var _t1514 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1514 = 9
						} else {
							var _t1515 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1515 = 5
							} else {
								var _t1516 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1516 = 6
								} else {
									var _t1517 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1517 = 7
									} else {
										var _t1518 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1518 = 1
										} else {
											var _t1519 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1519 = 2
											} else {
												var _t1520 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1520 = 12
												} else {
													var _t1521 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1521 = 8
													} else {
														var _t1522 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1522 = 4
														} else {
															var _t1523 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1523 = 10
															} else {
																var _t1524 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1524 = 10
																} else {
																	var _t1525 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1525 = 10
																	} else {
																		var _t1526 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1526 = 10
																		} else {
																			var _t1527 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1527 = 10
																			} else {
																				var _t1528 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1528 = 10
																				} else {
																					var _t1529 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1529 = 10
																					} else {
																						var _t1530 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1530 = 10
																						} else {
																							var _t1531 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1531 = 10
																							} else {
																								_t1531 = -1
																							}
																							_t1530 = _t1531
																						}
																						_t1529 = _t1530
																					}
																					_t1528 = _t1529
																				}
																				_t1527 = _t1528
																			}
																			_t1526 = _t1527
																		}
																		_t1525 = _t1526
																	}
																	_t1524 = _t1525
																}
																_t1523 = _t1524
															}
															_t1522 = _t1523
														}
														_t1521 = _t1522
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
						}
						_t1513 = _t1514
					}
					_t1512 = _t1513
				}
				_t1511 = _t1512
			}
			_t1510 = _t1511
		}
		_t1509 = _t1510
	} else {
		_t1509 = -1
	}
	prediction816 := _t1509
	var _t1532 *pb.Formula
	if prediction816 == 12 {
		_t1533 := p.parse_cast()
		cast829 := _t1533
		_t1534 := &pb.Formula{}
		_t1534.FormulaType = &pb.Formula_Cast{Cast: cast829}
		_t1532 = _t1534
	} else {
		var _t1535 *pb.Formula
		if prediction816 == 11 {
			_t1536 := p.parse_rel_atom()
			rel_atom828 := _t1536
			_t1537 := &pb.Formula{}
			_t1537.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom828}
			_t1535 = _t1537
		} else {
			var _t1538 *pb.Formula
			if prediction816 == 10 {
				_t1539 := p.parse_primitive()
				primitive827 := _t1539
				_t1540 := &pb.Formula{}
				_t1540.FormulaType = &pb.Formula_Primitive{Primitive: primitive827}
				_t1538 = _t1540
			} else {
				var _t1541 *pb.Formula
				if prediction816 == 9 {
					_t1542 := p.parse_pragma()
					pragma826 := _t1542
					_t1543 := &pb.Formula{}
					_t1543.FormulaType = &pb.Formula_Pragma{Pragma: pragma826}
					_t1541 = _t1543
				} else {
					var _t1544 *pb.Formula
					if prediction816 == 8 {
						_t1545 := p.parse_atom()
						atom825 := _t1545
						_t1546 := &pb.Formula{}
						_t1546.FormulaType = &pb.Formula_Atom{Atom: atom825}
						_t1544 = _t1546
					} else {
						var _t1547 *pb.Formula
						if prediction816 == 7 {
							_t1548 := p.parse_ffi()
							ffi824 := _t1548
							_t1549 := &pb.Formula{}
							_t1549.FormulaType = &pb.Formula_Ffi{Ffi: ffi824}
							_t1547 = _t1549
						} else {
							var _t1550 *pb.Formula
							if prediction816 == 6 {
								_t1551 := p.parse_not()
								not823 := _t1551
								_t1552 := &pb.Formula{}
								_t1552.FormulaType = &pb.Formula_Not{Not: not823}
								_t1550 = _t1552
							} else {
								var _t1553 *pb.Formula
								if prediction816 == 5 {
									_t1554 := p.parse_disjunction()
									disjunction822 := _t1554
									_t1555 := &pb.Formula{}
									_t1555.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction822}
									_t1553 = _t1555
								} else {
									var _t1556 *pb.Formula
									if prediction816 == 4 {
										_t1557 := p.parse_conjunction()
										conjunction821 := _t1557
										_t1558 := &pb.Formula{}
										_t1558.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction821}
										_t1556 = _t1558
									} else {
										var _t1559 *pb.Formula
										if prediction816 == 3 {
											_t1560 := p.parse_reduce()
											reduce820 := _t1560
											_t1561 := &pb.Formula{}
											_t1561.FormulaType = &pb.Formula_Reduce{Reduce: reduce820}
											_t1559 = _t1561
										} else {
											var _t1562 *pb.Formula
											if prediction816 == 2 {
												_t1563 := p.parse_exists()
												exists819 := _t1563
												_t1564 := &pb.Formula{}
												_t1564.FormulaType = &pb.Formula_Exists{Exists: exists819}
												_t1562 = _t1564
											} else {
												var _t1565 *pb.Formula
												if prediction816 == 1 {
													_t1566 := p.parse_false()
													false818 := _t1566
													_t1567 := &pb.Formula{}
													_t1567.FormulaType = &pb.Formula_Disjunction{Disjunction: false818}
													_t1565 = _t1567
												} else {
													var _t1568 *pb.Formula
													if prediction816 == 0 {
														_t1569 := p.parse_true()
														true817 := _t1569
														_t1570 := &pb.Formula{}
														_t1570.FormulaType = &pb.Formula_Conjunction{Conjunction: true817}
														_t1568 = _t1570
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1565 = _t1568
												}
												_t1562 = _t1565
											}
											_t1559 = _t1562
										}
										_t1556 = _t1559
									}
									_t1553 = _t1556
								}
								_t1550 = _t1553
							}
							_t1547 = _t1550
						}
						_t1544 = _t1547
					}
					_t1541 = _t1544
				}
				_t1538 = _t1541
			}
			_t1535 = _t1538
		}
		_t1532 = _t1535
	}
	result831 := _t1532
	p.recordSpan(int(span_start830), "Formula")
	return result831
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start832 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1571 := &pb.Conjunction{Args: []*pb.Formula{}}
	result833 := _t1571
	p.recordSpan(int(span_start832), "Conjunction")
	return result833
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start834 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1572 := &pb.Disjunction{Args: []*pb.Formula{}}
	result835 := _t1572
	p.recordSpan(int(span_start834), "Disjunction")
	return result835
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start838 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1573 := p.parse_bindings()
	bindings836 := _t1573
	_t1574 := p.parse_formula()
	formula837 := _t1574
	p.consumeLiteral(")")
	_t1575 := &pb.Abstraction{Vars: listConcat(bindings836[0].([]*pb.Binding), bindings836[1].([]*pb.Binding)), Value: formula837}
	_t1576 := &pb.Exists{Body: _t1575}
	result839 := _t1576
	p.recordSpan(int(span_start838), "Exists")
	return result839
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1577 := p.parse_abstraction()
	abstraction840 := _t1577
	_t1578 := p.parse_abstraction()
	abstraction_3841 := _t1578
	_t1579 := p.parse_terms()
	terms842 := _t1579
	p.consumeLiteral(")")
	_t1580 := &pb.Reduce{Op: abstraction840, Body: abstraction_3841, Terms: terms842}
	result844 := _t1580
	p.recordSpan(int(span_start843), "Reduce")
	return result844
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs845 := []*pb.Term{}
	cond846 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond846 {
		_t1581 := p.parse_term()
		item847 := _t1581
		xs845 = append(xs845, item847)
		cond846 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms848 := xs845
	p.consumeLiteral(")")
	return terms848
}

func (p *Parser) parse_term() *pb.Term {
	span_start852 := int64(p.spanStart())
	var _t1582 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1582 = 1
	} else {
		var _t1583 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1583 = 1
		} else {
			var _t1584 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1584 = 1
			} else {
				var _t1585 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1585 = 1
				} else {
					var _t1586 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1586 = 0
					} else {
						var _t1587 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1587 = 1
						} else {
							var _t1588 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1588 = 1
							} else {
								var _t1589 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1589 = 1
								} else {
									var _t1590 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1590 = 1
									} else {
										var _t1591 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1591 = 1
										} else {
											var _t1592 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1592 = 1
											} else {
												var _t1593 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1593 = 1
												} else {
													var _t1594 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1594 = 1
													} else {
														var _t1595 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1595 = 1
														} else {
															_t1595 = -1
														}
														_t1594 = _t1595
													}
													_t1593 = _t1594
												}
												_t1592 = _t1593
											}
											_t1591 = _t1592
										}
										_t1590 = _t1591
									}
									_t1589 = _t1590
								}
								_t1588 = _t1589
							}
							_t1587 = _t1588
						}
						_t1586 = _t1587
					}
					_t1585 = _t1586
				}
				_t1584 = _t1585
			}
			_t1583 = _t1584
		}
		_t1582 = _t1583
	}
	prediction849 := _t1582
	var _t1596 *pb.Term
	if prediction849 == 1 {
		_t1597 := p.parse_value()
		value851 := _t1597
		_t1598 := &pb.Term{}
		_t1598.TermType = &pb.Term_Constant{Constant: value851}
		_t1596 = _t1598
	} else {
		var _t1599 *pb.Term
		if prediction849 == 0 {
			_t1600 := p.parse_var()
			var850 := _t1600
			_t1601 := &pb.Term{}
			_t1601.TermType = &pb.Term_Var{Var: var850}
			_t1599 = _t1601
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1596 = _t1599
	}
	result853 := _t1596
	p.recordSpan(int(span_start852), "Term")
	return result853
}

func (p *Parser) parse_var() *pb.Var {
	span_start855 := int64(p.spanStart())
	symbol854 := p.consumeTerminal("SYMBOL").Value.str
	_t1602 := &pb.Var{Name: symbol854}
	result856 := _t1602
	p.recordSpan(int(span_start855), "Var")
	return result856
}

func (p *Parser) parse_value() *pb.Value {
	span_start870 := int64(p.spanStart())
	var _t1603 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1603 = 12
	} else {
		var _t1604 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1604 = 11
		} else {
			var _t1605 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1605 = 12
			} else {
				var _t1606 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1607 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1607 = 1
					} else {
						var _t1608 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1608 = 0
						} else {
							_t1608 = -1
						}
						_t1607 = _t1608
					}
					_t1606 = _t1607
				} else {
					var _t1609 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1609 = 7
					} else {
						var _t1610 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1610 = 8
						} else {
							var _t1611 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1611 = 2
							} else {
								var _t1612 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1612 = 3
								} else {
									var _t1613 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1613 = 9
									} else {
										var _t1614 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1614 = 4
										} else {
											var _t1615 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1615 = 5
											} else {
												var _t1616 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1616 = 6
												} else {
													var _t1617 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1617 = 10
													} else {
														_t1617 = -1
													}
													_t1616 = _t1617
												}
												_t1615 = _t1616
											}
											_t1614 = _t1615
										}
										_t1613 = _t1614
									}
									_t1612 = _t1613
								}
								_t1611 = _t1612
							}
							_t1610 = _t1611
						}
						_t1609 = _t1610
					}
					_t1606 = _t1609
				}
				_t1605 = _t1606
			}
			_t1604 = _t1605
		}
		_t1603 = _t1604
	}
	prediction857 := _t1603
	var _t1618 *pb.Value
	if prediction857 == 12 {
		_t1619 := p.parse_boolean_value()
		boolean_value869 := _t1619
		_t1620 := &pb.Value{}
		_t1620.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value869}
		_t1618 = _t1620
	} else {
		var _t1621 *pb.Value
		if prediction857 == 11 {
			p.consumeLiteral("missing")
			_t1622 := &pb.MissingValue{}
			_t1623 := &pb.Value{}
			_t1623.Value = &pb.Value_MissingValue{MissingValue: _t1622}
			_t1621 = _t1623
		} else {
			var _t1624 *pb.Value
			if prediction857 == 10 {
				formatted_decimal868 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1625 := &pb.Value{}
				_t1625.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal868}
				_t1624 = _t1625
			} else {
				var _t1626 *pb.Value
				if prediction857 == 9 {
					formatted_int128867 := p.consumeTerminal("INT128").Value.int128
					_t1627 := &pb.Value{}
					_t1627.Value = &pb.Value_Int128Value{Int128Value: formatted_int128867}
					_t1626 = _t1627
				} else {
					var _t1628 *pb.Value
					if prediction857 == 8 {
						formatted_uint128866 := p.consumeTerminal("UINT128").Value.uint128
						_t1629 := &pb.Value{}
						_t1629.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128866}
						_t1628 = _t1629
					} else {
						var _t1630 *pb.Value
						if prediction857 == 7 {
							formatted_uint32865 := p.consumeTerminal("UINT32").Value.u32
							_t1631 := &pb.Value{}
							_t1631.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32865}
							_t1630 = _t1631
						} else {
							var _t1632 *pb.Value
							if prediction857 == 6 {
								formatted_float864 := p.consumeTerminal("FLOAT").Value.f64
								_t1633 := &pb.Value{}
								_t1633.Value = &pb.Value_FloatValue{FloatValue: formatted_float864}
								_t1632 = _t1633
							} else {
								var _t1634 *pb.Value
								if prediction857 == 5 {
									formatted_float32863 := p.consumeTerminal("FLOAT32").Value.f32
									_t1635 := &pb.Value{}
									_t1635.Value = &pb.Value_Float32Value{Float32Value: formatted_float32863}
									_t1634 = _t1635
								} else {
									var _t1636 *pb.Value
									if prediction857 == 4 {
										formatted_int862 := p.consumeTerminal("INT").Value.i64
										_t1637 := &pb.Value{}
										_t1637.Value = &pb.Value_IntValue{IntValue: formatted_int862}
										_t1636 = _t1637
									} else {
										var _t1638 *pb.Value
										if prediction857 == 3 {
											formatted_int32861 := p.consumeTerminal("INT32").Value.i32
											_t1639 := &pb.Value{}
											_t1639.Value = &pb.Value_Int32Value{Int32Value: formatted_int32861}
											_t1638 = _t1639
										} else {
											var _t1640 *pb.Value
											if prediction857 == 2 {
												formatted_string860 := p.consumeTerminal("STRING").Value.str
												_t1641 := &pb.Value{}
												_t1641.Value = &pb.Value_StringValue{StringValue: formatted_string860}
												_t1640 = _t1641
											} else {
												var _t1642 *pb.Value
												if prediction857 == 1 {
													_t1643 := p.parse_datetime()
													datetime859 := _t1643
													_t1644 := &pb.Value{}
													_t1644.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime859}
													_t1642 = _t1644
												} else {
													var _t1645 *pb.Value
													if prediction857 == 0 {
														_t1646 := p.parse_date()
														date858 := _t1646
														_t1647 := &pb.Value{}
														_t1647.Value = &pb.Value_DateValue{DateValue: date858}
														_t1645 = _t1647
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1642 = _t1645
												}
												_t1640 = _t1642
											}
											_t1638 = _t1640
										}
										_t1636 = _t1638
									}
									_t1634 = _t1636
								}
								_t1632 = _t1634
							}
							_t1630 = _t1632
						}
						_t1628 = _t1630
					}
					_t1626 = _t1628
				}
				_t1624 = _t1626
			}
			_t1621 = _t1624
		}
		_t1618 = _t1621
	}
	result871 := _t1618
	p.recordSpan(int(span_start870), "Value")
	return result871
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start875 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int872 := p.consumeTerminal("INT").Value.i64
	formatted_int_3873 := p.consumeTerminal("INT").Value.i64
	formatted_int_4874 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1648 := &pb.DateValue{Year: int32(formatted_int872), Month: int32(formatted_int_3873), Day: int32(formatted_int_4874)}
	result876 := _t1648
	p.recordSpan(int(span_start875), "DateValue")
	return result876
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start884 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int877 := p.consumeTerminal("INT").Value.i64
	formatted_int_3878 := p.consumeTerminal("INT").Value.i64
	formatted_int_4879 := p.consumeTerminal("INT").Value.i64
	formatted_int_5880 := p.consumeTerminal("INT").Value.i64
	formatted_int_6881 := p.consumeTerminal("INT").Value.i64
	formatted_int_7882 := p.consumeTerminal("INT").Value.i64
	var _t1649 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1649 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8883 := _t1649
	p.consumeLiteral(")")
	_t1650 := &pb.DateTimeValue{Year: int32(formatted_int877), Month: int32(formatted_int_3878), Day: int32(formatted_int_4879), Hour: int32(formatted_int_5880), Minute: int32(formatted_int_6881), Second: int32(formatted_int_7882), Microsecond: int32(deref(formatted_int_8883, 0))}
	result885 := _t1650
	p.recordSpan(int(span_start884), "DateTimeValue")
	return result885
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start890 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs886 := []*pb.Formula{}
	cond887 := p.matchLookaheadLiteral("(", 0)
	for cond887 {
		_t1651 := p.parse_formula()
		item888 := _t1651
		xs886 = append(xs886, item888)
		cond887 = p.matchLookaheadLiteral("(", 0)
	}
	formulas889 := xs886
	p.consumeLiteral(")")
	_t1652 := &pb.Conjunction{Args: formulas889}
	result891 := _t1652
	p.recordSpan(int(span_start890), "Conjunction")
	return result891
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs892 := []*pb.Formula{}
	cond893 := p.matchLookaheadLiteral("(", 0)
	for cond893 {
		_t1653 := p.parse_formula()
		item894 := _t1653
		xs892 = append(xs892, item894)
		cond893 = p.matchLookaheadLiteral("(", 0)
	}
	formulas895 := xs892
	p.consumeLiteral(")")
	_t1654 := &pb.Disjunction{Args: formulas895}
	result897 := _t1654
	p.recordSpan(int(span_start896), "Disjunction")
	return result897
}

func (p *Parser) parse_not() *pb.Not {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1655 := p.parse_formula()
	formula898 := _t1655
	p.consumeLiteral(")")
	_t1656 := &pb.Not{Arg: formula898}
	result900 := _t1656
	p.recordSpan(int(span_start899), "Not")
	return result900
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1657 := p.parse_name()
	name901 := _t1657
	_t1658 := p.parse_ffi_args()
	ffi_args902 := _t1658
	_t1659 := p.parse_terms()
	terms903 := _t1659
	p.consumeLiteral(")")
	_t1660 := &pb.FFI{Name: name901, Args: ffi_args902, Terms: terms903}
	result905 := _t1660
	p.recordSpan(int(span_start904), "FFI")
	return result905
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol906 := p.consumeTerminal("SYMBOL").Value.str
	return symbol906
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs907 := []*pb.Abstraction{}
	cond908 := p.matchLookaheadLiteral("(", 0)
	for cond908 {
		_t1661 := p.parse_abstraction()
		item909 := _t1661
		xs907 = append(xs907, item909)
		cond908 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions910 := xs907
	p.consumeLiteral(")")
	return abstractions910
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start916 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1662 := p.parse_relation_id()
	relation_id911 := _t1662
	xs912 := []*pb.Term{}
	cond913 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond913 {
		_t1663 := p.parse_term()
		item914 := _t1663
		xs912 = append(xs912, item914)
		cond913 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms915 := xs912
	p.consumeLiteral(")")
	_t1664 := &pb.Atom{Name: relation_id911, Terms: terms915}
	result917 := _t1664
	p.recordSpan(int(span_start916), "Atom")
	return result917
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1665 := p.parse_name()
	name918 := _t1665
	xs919 := []*pb.Term{}
	cond920 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond920 {
		_t1666 := p.parse_term()
		item921 := _t1666
		xs919 = append(xs919, item921)
		cond920 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms922 := xs919
	p.consumeLiteral(")")
	_t1667 := &pb.Pragma{Name: name918, Terms: terms922}
	result924 := _t1667
	p.recordSpan(int(span_start923), "Pragma")
	return result924
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start940 := int64(p.spanStart())
	var _t1668 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1669 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1669 = 9
		} else {
			var _t1670 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1670 = 4
			} else {
				var _t1671 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1671 = 3
				} else {
					var _t1672 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1672 = 0
					} else {
						var _t1673 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1673 = 2
						} else {
							var _t1674 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1674 = 1
							} else {
								var _t1675 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1675 = 8
								} else {
									var _t1676 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1676 = 6
									} else {
										var _t1677 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1677 = 5
										} else {
											var _t1678 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1678 = 7
											} else {
												_t1678 = -1
											}
											_t1677 = _t1678
										}
										_t1676 = _t1677
									}
									_t1675 = _t1676
								}
								_t1674 = _t1675
							}
							_t1673 = _t1674
						}
						_t1672 = _t1673
					}
					_t1671 = _t1672
				}
				_t1670 = _t1671
			}
			_t1669 = _t1670
		}
		_t1668 = _t1669
	} else {
		_t1668 = -1
	}
	prediction925 := _t1668
	var _t1679 *pb.Primitive
	if prediction925 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1680 := p.parse_name()
		name935 := _t1680
		xs936 := []*pb.RelTerm{}
		cond937 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond937 {
			_t1681 := p.parse_rel_term()
			item938 := _t1681
			xs936 = append(xs936, item938)
			cond937 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms939 := xs936
		p.consumeLiteral(")")
		_t1682 := &pb.Primitive{Name: name935, Terms: rel_terms939}
		_t1679 = _t1682
	} else {
		var _t1683 *pb.Primitive
		if prediction925 == 8 {
			_t1684 := p.parse_divide()
			divide934 := _t1684
			_t1683 = divide934
		} else {
			var _t1685 *pb.Primitive
			if prediction925 == 7 {
				_t1686 := p.parse_multiply()
				multiply933 := _t1686
				_t1685 = multiply933
			} else {
				var _t1687 *pb.Primitive
				if prediction925 == 6 {
					_t1688 := p.parse_minus()
					minus932 := _t1688
					_t1687 = minus932
				} else {
					var _t1689 *pb.Primitive
					if prediction925 == 5 {
						_t1690 := p.parse_add()
						add931 := _t1690
						_t1689 = add931
					} else {
						var _t1691 *pb.Primitive
						if prediction925 == 4 {
							_t1692 := p.parse_gt_eq()
							gt_eq930 := _t1692
							_t1691 = gt_eq930
						} else {
							var _t1693 *pb.Primitive
							if prediction925 == 3 {
								_t1694 := p.parse_gt()
								gt929 := _t1694
								_t1693 = gt929
							} else {
								var _t1695 *pb.Primitive
								if prediction925 == 2 {
									_t1696 := p.parse_lt_eq()
									lt_eq928 := _t1696
									_t1695 = lt_eq928
								} else {
									var _t1697 *pb.Primitive
									if prediction925 == 1 {
										_t1698 := p.parse_lt()
										lt927 := _t1698
										_t1697 = lt927
									} else {
										var _t1699 *pb.Primitive
										if prediction925 == 0 {
											_t1700 := p.parse_eq()
											eq926 := _t1700
											_t1699 = eq926
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1697 = _t1699
									}
									_t1695 = _t1697
								}
								_t1693 = _t1695
							}
							_t1691 = _t1693
						}
						_t1689 = _t1691
					}
					_t1687 = _t1689
				}
				_t1685 = _t1687
			}
			_t1683 = _t1685
		}
		_t1679 = _t1683
	}
	result941 := _t1679
	p.recordSpan(int(span_start940), "Primitive")
	return result941
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start944 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1701 := p.parse_term()
	term942 := _t1701
	_t1702 := p.parse_term()
	term_3943 := _t1702
	p.consumeLiteral(")")
	_t1703 := &pb.RelTerm{}
	_t1703.RelTermType = &pb.RelTerm_Term{Term: term942}
	_t1704 := &pb.RelTerm{}
	_t1704.RelTermType = &pb.RelTerm_Term{Term: term_3943}
	_t1705 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1703, _t1704}}
	result945 := _t1705
	p.recordSpan(int(span_start944), "Primitive")
	return result945
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1706 := p.parse_term()
	term946 := _t1706
	_t1707 := p.parse_term()
	term_3947 := _t1707
	p.consumeLiteral(")")
	_t1708 := &pb.RelTerm{}
	_t1708.RelTermType = &pb.RelTerm_Term{Term: term946}
	_t1709 := &pb.RelTerm{}
	_t1709.RelTermType = &pb.RelTerm_Term{Term: term_3947}
	_t1710 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1708, _t1709}}
	result949 := _t1710
	p.recordSpan(int(span_start948), "Primitive")
	return result949
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1711 := p.parse_term()
	term950 := _t1711
	_t1712 := p.parse_term()
	term_3951 := _t1712
	p.consumeLiteral(")")
	_t1713 := &pb.RelTerm{}
	_t1713.RelTermType = &pb.RelTerm_Term{Term: term950}
	_t1714 := &pb.RelTerm{}
	_t1714.RelTermType = &pb.RelTerm_Term{Term: term_3951}
	_t1715 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1713, _t1714}}
	result953 := _t1715
	p.recordSpan(int(span_start952), "Primitive")
	return result953
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start956 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1716 := p.parse_term()
	term954 := _t1716
	_t1717 := p.parse_term()
	term_3955 := _t1717
	p.consumeLiteral(")")
	_t1718 := &pb.RelTerm{}
	_t1718.RelTermType = &pb.RelTerm_Term{Term: term954}
	_t1719 := &pb.RelTerm{}
	_t1719.RelTermType = &pb.RelTerm_Term{Term: term_3955}
	_t1720 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1718, _t1719}}
	result957 := _t1720
	p.recordSpan(int(span_start956), "Primitive")
	return result957
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1721 := p.parse_term()
	term958 := _t1721
	_t1722 := p.parse_term()
	term_3959 := _t1722
	p.consumeLiteral(")")
	_t1723 := &pb.RelTerm{}
	_t1723.RelTermType = &pb.RelTerm_Term{Term: term958}
	_t1724 := &pb.RelTerm{}
	_t1724.RelTermType = &pb.RelTerm_Term{Term: term_3959}
	_t1725 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1723, _t1724}}
	result961 := _t1725
	p.recordSpan(int(span_start960), "Primitive")
	return result961
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1726 := p.parse_term()
	term962 := _t1726
	_t1727 := p.parse_term()
	term_3963 := _t1727
	_t1728 := p.parse_term()
	term_4964 := _t1728
	p.consumeLiteral(")")
	_t1729 := &pb.RelTerm{}
	_t1729.RelTermType = &pb.RelTerm_Term{Term: term962}
	_t1730 := &pb.RelTerm{}
	_t1730.RelTermType = &pb.RelTerm_Term{Term: term_3963}
	_t1731 := &pb.RelTerm{}
	_t1731.RelTermType = &pb.RelTerm_Term{Term: term_4964}
	_t1732 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1729, _t1730, _t1731}}
	result966 := _t1732
	p.recordSpan(int(span_start965), "Primitive")
	return result966
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1733 := p.parse_term()
	term967 := _t1733
	_t1734 := p.parse_term()
	term_3968 := _t1734
	_t1735 := p.parse_term()
	term_4969 := _t1735
	p.consumeLiteral(")")
	_t1736 := &pb.RelTerm{}
	_t1736.RelTermType = &pb.RelTerm_Term{Term: term967}
	_t1737 := &pb.RelTerm{}
	_t1737.RelTermType = &pb.RelTerm_Term{Term: term_3968}
	_t1738 := &pb.RelTerm{}
	_t1738.RelTermType = &pb.RelTerm_Term{Term: term_4969}
	_t1739 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1736, _t1737, _t1738}}
	result971 := _t1739
	p.recordSpan(int(span_start970), "Primitive")
	return result971
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1740 := p.parse_term()
	term972 := _t1740
	_t1741 := p.parse_term()
	term_3973 := _t1741
	_t1742 := p.parse_term()
	term_4974 := _t1742
	p.consumeLiteral(")")
	_t1743 := &pb.RelTerm{}
	_t1743.RelTermType = &pb.RelTerm_Term{Term: term972}
	_t1744 := &pb.RelTerm{}
	_t1744.RelTermType = &pb.RelTerm_Term{Term: term_3973}
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term_4974}
	_t1746 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1743, _t1744, _t1745}}
	result976 := _t1746
	p.recordSpan(int(span_start975), "Primitive")
	return result976
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1747 := p.parse_term()
	term977 := _t1747
	_t1748 := p.parse_term()
	term_3978 := _t1748
	_t1749 := p.parse_term()
	term_4979 := _t1749
	p.consumeLiteral(")")
	_t1750 := &pb.RelTerm{}
	_t1750.RelTermType = &pb.RelTerm_Term{Term: term977}
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term_3978}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_4979}
	_t1753 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1750, _t1751, _t1752}}
	result981 := _t1753
	p.recordSpan(int(span_start980), "Primitive")
	return result981
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start985 := int64(p.spanStart())
	var _t1754 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1754 = 1
	} else {
		var _t1755 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1755 = 1
		} else {
			var _t1756 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1756 = 1
			} else {
				var _t1757 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1757 = 1
				} else {
					var _t1758 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1758 = 0
					} else {
						var _t1759 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1759 = 1
						} else {
							var _t1760 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1760 = 1
							} else {
								var _t1761 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1761 = 1
								} else {
									var _t1762 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1762 = 1
									} else {
										var _t1763 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1763 = 1
										} else {
											var _t1764 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1764 = 1
											} else {
												var _t1765 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1765 = 1
												} else {
													var _t1766 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1766 = 1
													} else {
														var _t1767 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1767 = 1
														} else {
															var _t1768 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1768 = 1
															} else {
																_t1768 = -1
															}
															_t1767 = _t1768
														}
														_t1766 = _t1767
													}
													_t1765 = _t1766
												}
												_t1764 = _t1765
											}
											_t1763 = _t1764
										}
										_t1762 = _t1763
									}
									_t1761 = _t1762
								}
								_t1760 = _t1761
							}
							_t1759 = _t1760
						}
						_t1758 = _t1759
					}
					_t1757 = _t1758
				}
				_t1756 = _t1757
			}
			_t1755 = _t1756
		}
		_t1754 = _t1755
	}
	prediction982 := _t1754
	var _t1769 *pb.RelTerm
	if prediction982 == 1 {
		_t1770 := p.parse_term()
		term984 := _t1770
		_t1771 := &pb.RelTerm{}
		_t1771.RelTermType = &pb.RelTerm_Term{Term: term984}
		_t1769 = _t1771
	} else {
		var _t1772 *pb.RelTerm
		if prediction982 == 0 {
			_t1773 := p.parse_specialized_value()
			specialized_value983 := _t1773
			_t1774 := &pb.RelTerm{}
			_t1774.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value983}
			_t1772 = _t1774
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1769 = _t1772
	}
	result986 := _t1769
	p.recordSpan(int(span_start985), "RelTerm")
	return result986
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start988 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1775 := p.parse_raw_value()
	raw_value987 := _t1775
	result989 := raw_value987
	p.recordSpan(int(span_start988), "Value")
	return result989
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start995 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1776 := p.parse_name()
	name990 := _t1776
	xs991 := []*pb.RelTerm{}
	cond992 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond992 {
		_t1777 := p.parse_rel_term()
		item993 := _t1777
		xs991 = append(xs991, item993)
		cond992 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms994 := xs991
	p.consumeLiteral(")")
	_t1778 := &pb.RelAtom{Name: name990, Terms: rel_terms994}
	result996 := _t1778
	p.recordSpan(int(span_start995), "RelAtom")
	return result996
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start999 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1779 := p.parse_term()
	term997 := _t1779
	_t1780 := p.parse_term()
	term_3998 := _t1780
	p.consumeLiteral(")")
	_t1781 := &pb.Cast{Input: term997, Result: term_3998}
	result1000 := _t1781
	p.recordSpan(int(span_start999), "Cast")
	return result1000
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1001 := []*pb.Attribute{}
	cond1002 := p.matchLookaheadLiteral("(", 0)
	for cond1002 {
		_t1782 := p.parse_attribute()
		item1003 := _t1782
		xs1001 = append(xs1001, item1003)
		cond1002 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1004 := xs1001
	p.consumeLiteral(")")
	return attributes1004
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1010 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1783 := p.parse_name()
	name1005 := _t1783
	xs1006 := []*pb.Value{}
	cond1007 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1007 {
		_t1784 := p.parse_raw_value()
		item1008 := _t1784
		xs1006 = append(xs1006, item1008)
		cond1007 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1009 := xs1006
	p.consumeLiteral(")")
	_t1785 := &pb.Attribute{Name: name1005, Args: raw_values1009}
	result1011 := _t1785
	p.recordSpan(int(span_start1010), "Attribute")
	return result1011
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1012 := []*pb.RelationId{}
	cond1013 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1013 {
		_t1786 := p.parse_relation_id()
		item1014 := _t1786
		xs1012 = append(xs1012, item1014)
		cond1013 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1015 := xs1012
	_t1787 := p.parse_script()
	script1016 := _t1787
	p.consumeLiteral(")")
	_t1788 := &pb.Algorithm{Global: relation_ids1015, Body: script1016}
	result1018 := _t1788
	p.recordSpan(int(span_start1017), "Algorithm")
	return result1018
}

func (p *Parser) parse_script() *pb.Script {
	span_start1023 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1019 := []*pb.Construct{}
	cond1020 := p.matchLookaheadLiteral("(", 0)
	for cond1020 {
		_t1789 := p.parse_construct()
		item1021 := _t1789
		xs1019 = append(xs1019, item1021)
		cond1020 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1022 := xs1019
	p.consumeLiteral(")")
	_t1790 := &pb.Script{Constructs: constructs1022}
	result1024 := _t1790
	p.recordSpan(int(span_start1023), "Script")
	return result1024
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1028 := int64(p.spanStart())
	var _t1791 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1792 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1792 = 1
		} else {
			var _t1793 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1793 = 1
			} else {
				var _t1794 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1794 = 1
				} else {
					var _t1795 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1795 = 0
					} else {
						var _t1796 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1796 = 1
						} else {
							var _t1797 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1797 = 1
							} else {
								_t1797 = -1
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
	} else {
		_t1791 = -1
	}
	prediction1025 := _t1791
	var _t1798 *pb.Construct
	if prediction1025 == 1 {
		_t1799 := p.parse_instruction()
		instruction1027 := _t1799
		_t1800 := &pb.Construct{}
		_t1800.ConstructType = &pb.Construct_Instruction{Instruction: instruction1027}
		_t1798 = _t1800
	} else {
		var _t1801 *pb.Construct
		if prediction1025 == 0 {
			_t1802 := p.parse_loop()
			loop1026 := _t1802
			_t1803 := &pb.Construct{}
			_t1803.ConstructType = &pb.Construct_Loop{Loop: loop1026}
			_t1801 = _t1803
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1798 = _t1801
	}
	result1029 := _t1798
	p.recordSpan(int(span_start1028), "Construct")
	return result1029
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1804 := p.parse_init()
	init1030 := _t1804
	_t1805 := p.parse_script()
	script1031 := _t1805
	p.consumeLiteral(")")
	_t1806 := &pb.Loop{Init: init1030, Body: script1031}
	result1033 := _t1806
	p.recordSpan(int(span_start1032), "Loop")
	return result1033
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1034 := []*pb.Instruction{}
	cond1035 := p.matchLookaheadLiteral("(", 0)
	for cond1035 {
		_t1807 := p.parse_instruction()
		item1036 := _t1807
		xs1034 = append(xs1034, item1036)
		cond1035 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1037 := xs1034
	p.consumeLiteral(")")
	return instructions1037
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1044 := int64(p.spanStart())
	var _t1808 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1809 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1809 = 1
		} else {
			var _t1810 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1810 = 4
			} else {
				var _t1811 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1811 = 3
				} else {
					var _t1812 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1812 = 2
					} else {
						var _t1813 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1813 = 0
						} else {
							_t1813 = -1
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
	} else {
		_t1808 = -1
	}
	prediction1038 := _t1808
	var _t1814 *pb.Instruction
	if prediction1038 == 4 {
		_t1815 := p.parse_monus_def()
		monus_def1043 := _t1815
		_t1816 := &pb.Instruction{}
		_t1816.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1043}
		_t1814 = _t1816
	} else {
		var _t1817 *pb.Instruction
		if prediction1038 == 3 {
			_t1818 := p.parse_monoid_def()
			monoid_def1042 := _t1818
			_t1819 := &pb.Instruction{}
			_t1819.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1042}
			_t1817 = _t1819
		} else {
			var _t1820 *pb.Instruction
			if prediction1038 == 2 {
				_t1821 := p.parse_break()
				break1041 := _t1821
				_t1822 := &pb.Instruction{}
				_t1822.InstrType = &pb.Instruction_Break{Break: break1041}
				_t1820 = _t1822
			} else {
				var _t1823 *pb.Instruction
				if prediction1038 == 1 {
					_t1824 := p.parse_upsert()
					upsert1040 := _t1824
					_t1825 := &pb.Instruction{}
					_t1825.InstrType = &pb.Instruction_Upsert{Upsert: upsert1040}
					_t1823 = _t1825
				} else {
					var _t1826 *pb.Instruction
					if prediction1038 == 0 {
						_t1827 := p.parse_assign()
						assign1039 := _t1827
						_t1828 := &pb.Instruction{}
						_t1828.InstrType = &pb.Instruction_Assign{Assign: assign1039}
						_t1826 = _t1828
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1823 = _t1826
				}
				_t1820 = _t1823
			}
			_t1817 = _t1820
		}
		_t1814 = _t1817
	}
	result1045 := _t1814
	p.recordSpan(int(span_start1044), "Instruction")
	return result1045
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1049 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1829 := p.parse_relation_id()
	relation_id1046 := _t1829
	_t1830 := p.parse_abstraction()
	abstraction1047 := _t1830
	var _t1831 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1832 := p.parse_attrs()
		_t1831 = _t1832
	}
	attrs1048 := _t1831
	p.consumeLiteral(")")
	_t1833 := attrs1048
	if attrs1048 == nil {
		_t1833 = []*pb.Attribute{}
	}
	_t1834 := &pb.Assign{Name: relation_id1046, Body: abstraction1047, Attrs: _t1833}
	result1050 := _t1834
	p.recordSpan(int(span_start1049), "Assign")
	return result1050
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1054 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1835 := p.parse_relation_id()
	relation_id1051 := _t1835
	_t1836 := p.parse_abstraction_with_arity()
	abstraction_with_arity1052 := _t1836
	var _t1837 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1838 := p.parse_attrs()
		_t1837 = _t1838
	}
	attrs1053 := _t1837
	p.consumeLiteral(")")
	_t1839 := attrs1053
	if attrs1053 == nil {
		_t1839 = []*pb.Attribute{}
	}
	_t1840 := &pb.Upsert{Name: relation_id1051, Body: abstraction_with_arity1052[0].(*pb.Abstraction), Attrs: _t1839, ValueArity: abstraction_with_arity1052[1].(int64)}
	result1055 := _t1840
	p.recordSpan(int(span_start1054), "Upsert")
	return result1055
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1841 := p.parse_bindings()
	bindings1056 := _t1841
	_t1842 := p.parse_formula()
	formula1057 := _t1842
	p.consumeLiteral(")")
	_t1843 := &pb.Abstraction{Vars: listConcat(bindings1056[0].([]*pb.Binding), bindings1056[1].([]*pb.Binding)), Value: formula1057}
	return []interface{}{_t1843, int64(len(bindings1056[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1061 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1844 := p.parse_relation_id()
	relation_id1058 := _t1844
	_t1845 := p.parse_abstraction()
	abstraction1059 := _t1845
	var _t1846 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1847 := p.parse_attrs()
		_t1846 = _t1847
	}
	attrs1060 := _t1846
	p.consumeLiteral(")")
	_t1848 := attrs1060
	if attrs1060 == nil {
		_t1848 = []*pb.Attribute{}
	}
	_t1849 := &pb.Break{Name: relation_id1058, Body: abstraction1059, Attrs: _t1848}
	result1062 := _t1849
	p.recordSpan(int(span_start1061), "Break")
	return result1062
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1067 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1850 := p.parse_monoid()
	monoid1063 := _t1850
	_t1851 := p.parse_relation_id()
	relation_id1064 := _t1851
	_t1852 := p.parse_abstraction_with_arity()
	abstraction_with_arity1065 := _t1852
	var _t1853 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1854 := p.parse_attrs()
		_t1853 = _t1854
	}
	attrs1066 := _t1853
	p.consumeLiteral(")")
	_t1855 := attrs1066
	if attrs1066 == nil {
		_t1855 = []*pb.Attribute{}
	}
	_t1856 := &pb.MonoidDef{Monoid: monoid1063, Name: relation_id1064, Body: abstraction_with_arity1065[0].(*pb.Abstraction), Attrs: _t1855, ValueArity: abstraction_with_arity1065[1].(int64)}
	result1068 := _t1856
	p.recordSpan(int(span_start1067), "MonoidDef")
	return result1068
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1074 := int64(p.spanStart())
	var _t1857 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1858 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1858 = 3
		} else {
			var _t1859 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1859 = 0
			} else {
				var _t1860 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1860 = 1
				} else {
					var _t1861 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1861 = 2
					} else {
						_t1861 = -1
					}
					_t1860 = _t1861
				}
				_t1859 = _t1860
			}
			_t1858 = _t1859
		}
		_t1857 = _t1858
	} else {
		_t1857 = -1
	}
	prediction1069 := _t1857
	var _t1862 *pb.Monoid
	if prediction1069 == 3 {
		_t1863 := p.parse_sum_monoid()
		sum_monoid1073 := _t1863
		_t1864 := &pb.Monoid{}
		_t1864.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1073}
		_t1862 = _t1864
	} else {
		var _t1865 *pb.Monoid
		if prediction1069 == 2 {
			_t1866 := p.parse_max_monoid()
			max_monoid1072 := _t1866
			_t1867 := &pb.Monoid{}
			_t1867.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1072}
			_t1865 = _t1867
		} else {
			var _t1868 *pb.Monoid
			if prediction1069 == 1 {
				_t1869 := p.parse_min_monoid()
				min_monoid1071 := _t1869
				_t1870 := &pb.Monoid{}
				_t1870.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1071}
				_t1868 = _t1870
			} else {
				var _t1871 *pb.Monoid
				if prediction1069 == 0 {
					_t1872 := p.parse_or_monoid()
					or_monoid1070 := _t1872
					_t1873 := &pb.Monoid{}
					_t1873.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1070}
					_t1871 = _t1873
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1868 = _t1871
			}
			_t1865 = _t1868
		}
		_t1862 = _t1865
	}
	result1075 := _t1862
	p.recordSpan(int(span_start1074), "Monoid")
	return result1075
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1076 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1874 := &pb.OrMonoid{}
	result1077 := _t1874
	p.recordSpan(int(span_start1076), "OrMonoid")
	return result1077
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1079 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1875 := p.parse_type()
	type1078 := _t1875
	p.consumeLiteral(")")
	_t1876 := &pb.MinMonoid{Type: type1078}
	result1080 := _t1876
	p.recordSpan(int(span_start1079), "MinMonoid")
	return result1080
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1877 := p.parse_type()
	type1081 := _t1877
	p.consumeLiteral(")")
	_t1878 := &pb.MaxMonoid{Type: type1081}
	result1083 := _t1878
	p.recordSpan(int(span_start1082), "MaxMonoid")
	return result1083
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1085 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1879 := p.parse_type()
	type1084 := _t1879
	p.consumeLiteral(")")
	_t1880 := &pb.SumMonoid{Type: type1084}
	result1086 := _t1880
	p.recordSpan(int(span_start1085), "SumMonoid")
	return result1086
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1091 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1881 := p.parse_monoid()
	monoid1087 := _t1881
	_t1882 := p.parse_relation_id()
	relation_id1088 := _t1882
	_t1883 := p.parse_abstraction_with_arity()
	abstraction_with_arity1089 := _t1883
	var _t1884 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1885 := p.parse_attrs()
		_t1884 = _t1885
	}
	attrs1090 := _t1884
	p.consumeLiteral(")")
	_t1886 := attrs1090
	if attrs1090 == nil {
		_t1886 = []*pb.Attribute{}
	}
	_t1887 := &pb.MonusDef{Monoid: monoid1087, Name: relation_id1088, Body: abstraction_with_arity1089[0].(*pb.Abstraction), Attrs: _t1886, ValueArity: abstraction_with_arity1089[1].(int64)}
	result1092 := _t1887
	p.recordSpan(int(span_start1091), "MonusDef")
	return result1092
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1888 := p.parse_relation_id()
	relation_id1093 := _t1888
	_t1889 := p.parse_abstraction()
	abstraction1094 := _t1889
	_t1890 := p.parse_functional_dependency_keys()
	functional_dependency_keys1095 := _t1890
	_t1891 := p.parse_functional_dependency_values()
	functional_dependency_values1096 := _t1891
	p.consumeLiteral(")")
	_t1892 := &pb.FunctionalDependency{Guard: abstraction1094, Keys: functional_dependency_keys1095, Values: functional_dependency_values1096}
	_t1893 := &pb.Constraint{Name: relation_id1093}
	_t1893.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1892}
	result1098 := _t1893
	p.recordSpan(int(span_start1097), "Constraint")
	return result1098
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1099 := []*pb.Var{}
	cond1100 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1100 {
		_t1894 := p.parse_var()
		item1101 := _t1894
		xs1099 = append(xs1099, item1101)
		cond1100 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1102 := xs1099
	p.consumeLiteral(")")
	return vars1102
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1103 := []*pb.Var{}
	cond1104 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1104 {
		_t1895 := p.parse_var()
		item1105 := _t1895
		xs1103 = append(xs1103, item1105)
		cond1104 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1106 := xs1103
	p.consumeLiteral(")")
	return vars1106
}

func (p *Parser) parse_data() *pb.Data {
	span_start1112 := int64(p.spanStart())
	var _t1896 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1897 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1897 = 3
		} else {
			var _t1898 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1898 = 0
			} else {
				var _t1899 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1899 = 2
				} else {
					var _t1900 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1900 = 1
					} else {
						_t1900 = -1
					}
					_t1899 = _t1900
				}
				_t1898 = _t1899
			}
			_t1897 = _t1898
		}
		_t1896 = _t1897
	} else {
		_t1896 = -1
	}
	prediction1107 := _t1896
	var _t1901 *pb.Data
	if prediction1107 == 3 {
		_t1902 := p.parse_iceberg_data()
		iceberg_data1111 := _t1902
		_t1903 := &pb.Data{}
		_t1903.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1111}
		_t1901 = _t1903
	} else {
		var _t1904 *pb.Data
		if prediction1107 == 2 {
			_t1905 := p.parse_csv_data()
			csv_data1110 := _t1905
			_t1906 := &pb.Data{}
			_t1906.DataType = &pb.Data_CsvData{CsvData: csv_data1110}
			_t1904 = _t1906
		} else {
			var _t1907 *pb.Data
			if prediction1107 == 1 {
				_t1908 := p.parse_betree_relation()
				betree_relation1109 := _t1908
				_t1909 := &pb.Data{}
				_t1909.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1109}
				_t1907 = _t1909
			} else {
				var _t1910 *pb.Data
				if prediction1107 == 0 {
					_t1911 := p.parse_edb()
					edb1108 := _t1911
					_t1912 := &pb.Data{}
					_t1912.DataType = &pb.Data_Edb{Edb: edb1108}
					_t1910 = _t1912
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1907 = _t1910
			}
			_t1904 = _t1907
		}
		_t1901 = _t1904
	}
	result1113 := _t1901
	p.recordSpan(int(span_start1112), "Data")
	return result1113
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1913 := p.parse_relation_id()
	relation_id1114 := _t1913
	_t1914 := p.parse_edb_path()
	edb_path1115 := _t1914
	_t1915 := p.parse_edb_types()
	edb_types1116 := _t1915
	p.consumeLiteral(")")
	_t1916 := &pb.EDB{TargetId: relation_id1114, Path: edb_path1115, Types: edb_types1116}
	result1118 := _t1916
	p.recordSpan(int(span_start1117), "EDB")
	return result1118
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1119 := []string{}
	cond1120 := p.matchLookaheadTerminal("STRING", 0)
	for cond1120 {
		item1121 := p.consumeTerminal("STRING").Value.str
		xs1119 = append(xs1119, item1121)
		cond1120 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1122 := xs1119
	p.consumeLiteral("]")
	return strings1122
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1123 := []*pb.Type{}
	cond1124 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1124 {
		_t1917 := p.parse_type()
		item1125 := _t1917
		xs1123 = append(xs1123, item1125)
		cond1124 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1126 := xs1123
	p.consumeLiteral("]")
	return types1126
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1129 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1918 := p.parse_relation_id()
	relation_id1127 := _t1918
	_t1919 := p.parse_betree_info()
	betree_info1128 := _t1919
	p.consumeLiteral(")")
	_t1920 := &pb.BeTreeRelation{Name: relation_id1127, RelationInfo: betree_info1128}
	result1130 := _t1920
	p.recordSpan(int(span_start1129), "BeTreeRelation")
	return result1130
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1921 := p.parse_betree_info_key_types()
	betree_info_key_types1131 := _t1921
	_t1922 := p.parse_betree_info_value_types()
	betree_info_value_types1132 := _t1922
	_t1923 := p.parse_config_dict()
	config_dict1133 := _t1923
	p.consumeLiteral(")")
	_t1924 := p.construct_betree_info(betree_info_key_types1131, betree_info_value_types1132, config_dict1133)
	result1135 := _t1924
	p.recordSpan(int(span_start1134), "BeTreeInfo")
	return result1135
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1136 := []*pb.Type{}
	cond1137 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1137 {
		_t1925 := p.parse_type()
		item1138 := _t1925
		xs1136 = append(xs1136, item1138)
		cond1137 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1139 := xs1136
	p.consumeLiteral(")")
	return types1139
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1140 := []*pb.Type{}
	cond1141 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1141 {
		_t1926 := p.parse_type()
		item1142 := _t1926
		xs1140 = append(xs1140, item1142)
		cond1141 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1143 := xs1140
	p.consumeLiteral(")")
	return types1143
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1148 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1927 := p.parse_csvlocator()
	csvlocator1144 := _t1927
	_t1928 := p.parse_csv_config()
	csv_config1145 := _t1928
	_t1929 := p.parse_gnf_columns()
	gnf_columns1146 := _t1929
	_t1930 := p.parse_csv_asof()
	csv_asof1147 := _t1930
	p.consumeLiteral(")")
	_t1931 := &pb.CSVData{Locator: csvlocator1144, Config: csv_config1145, Columns: gnf_columns1146, Asof: csv_asof1147}
	result1149 := _t1931
	p.recordSpan(int(span_start1148), "CSVData")
	return result1149
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1152 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1932 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1933 := p.parse_csv_locator_paths()
		_t1932 = _t1933
	}
	csv_locator_paths1150 := _t1932
	var _t1934 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1935 := p.parse_csv_locator_inline_data()
		_t1934 = ptr(_t1935)
	}
	csv_locator_inline_data1151 := _t1934
	p.consumeLiteral(")")
	_t1936 := csv_locator_paths1150
	if csv_locator_paths1150 == nil {
		_t1936 = []string{}
	}
	_t1937 := &pb.CSVLocator{Paths: _t1936, InlineData: []byte(deref(csv_locator_inline_data1151, ""))}
	result1153 := _t1937
	p.recordSpan(int(span_start1152), "CSVLocator")
	return result1153
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1154 := []string{}
	cond1155 := p.matchLookaheadTerminal("STRING", 0)
	for cond1155 {
		item1156 := p.consumeTerminal("STRING").Value.str
		xs1154 = append(xs1154, item1156)
		cond1155 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1157 := xs1154
	p.consumeLiteral(")")
	return strings1157
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1158 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1158
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1160 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1938 := p.parse_config_dict()
	config_dict1159 := _t1938
	p.consumeLiteral(")")
	_t1939 := p.construct_csv_config(config_dict1159)
	result1161 := _t1939
	p.recordSpan(int(span_start1160), "CSVConfig")
	return result1161
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1162 := []*pb.GNFColumn{}
	cond1163 := p.matchLookaheadLiteral("(", 0)
	for cond1163 {
		_t1940 := p.parse_gnf_column()
		item1164 := _t1940
		xs1162 = append(xs1162, item1164)
		cond1163 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1165 := xs1162
	p.consumeLiteral(")")
	return gnf_columns1165
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1172 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1941 := p.parse_gnf_column_path()
	gnf_column_path1166 := _t1941
	var _t1942 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1943 := p.parse_relation_id()
		_t1942 = _t1943
	}
	relation_id1167 := _t1942
	p.consumeLiteral("[")
	xs1168 := []*pb.Type{}
	cond1169 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1169 {
		_t1944 := p.parse_type()
		item1170 := _t1944
		xs1168 = append(xs1168, item1170)
		cond1169 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1171 := xs1168
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1945 := &pb.GNFColumn{ColumnPath: gnf_column_path1166, TargetId: relation_id1167, Types: types1171}
	result1173 := _t1945
	p.recordSpan(int(span_start1172), "GNFColumn")
	return result1173
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1946 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1946 = 1
	} else {
		var _t1947 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1947 = 0
		} else {
			_t1947 = -1
		}
		_t1946 = _t1947
	}
	prediction1174 := _t1946
	var _t1948 []string
	if prediction1174 == 1 {
		p.consumeLiteral("[")
		xs1176 := []string{}
		cond1177 := p.matchLookaheadTerminal("STRING", 0)
		for cond1177 {
			item1178 := p.consumeTerminal("STRING").Value.str
			xs1176 = append(xs1176, item1178)
			cond1177 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1179 := xs1176
		p.consumeLiteral("]")
		_t1948 = strings1179
	} else {
		var _t1949 []string
		if prediction1174 == 0 {
			string1175 := p.consumeTerminal("STRING").Value.str
			_ = string1175
			_t1949 = []string{string1175}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1948 = _t1949
	}
	return _t1948
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1180 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1180
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1185 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1950 := p.parse_iceberg_locator()
	iceberg_locator1181 := _t1950
	_t1951 := p.parse_iceberg_config()
	iceberg_config1182 := _t1951
	_t1952 := p.parse_gnf_columns()
	gnf_columns1183 := _t1952
	var _t1953 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1954 := p.parse_iceberg_to_snapshot()
		_t1953 = ptr(_t1954)
	}
	iceberg_to_snapshot1184 := _t1953
	p.consumeLiteral(")")
	_t1955 := &pb.IcebergData{Locator: iceberg_locator1181, Config: iceberg_config1182, Columns: gnf_columns1183, ToSnapshot: ptr(deref(iceberg_to_snapshot1184, ""))}
	result1186 := _t1955
	p.recordSpan(int(span_start1185), "IcebergData")
	return result1186
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1193 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1187 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1188 := []string{}
	cond1189 := p.matchLookaheadTerminal("STRING", 0)
	for cond1189 {
		item1190 := p.consumeTerminal("STRING").Value.str
		xs1188 = append(xs1188, item1190)
		cond1189 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1191 := xs1188
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121192 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1956 := &pb.IcebergLocator{TableName: string1187, Namespace: strings1191, Warehouse: string_121192}
	result1194 := _t1956
	p.recordSpan(int(span_start1193), "IcebergLocator")
	return result1194
}

func (p *Parser) parse_iceberg_config() *pb.IcebergConfig {
	span_start1205 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1195 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1957 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1958 := p.parse_iceberg_config_scope()
		_t1957 = ptr(_t1958)
	}
	iceberg_config_scope1196 := _t1957
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1197 := [][]interface{}{}
	cond1198 := p.matchLookaheadLiteral("(", 0)
	for cond1198 {
		_t1959 := p.parse_iceberg_property_entry()
		item1199 := _t1959
		xs1197 = append(xs1197, item1199)
		cond1198 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1200 := xs1197
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1201 := [][]interface{}{}
	cond1202 := p.matchLookaheadLiteral("(", 0)
	for cond1202 {
		_t1960 := p.parse_iceberg_property_entry()
		item1203 := _t1960
		xs1201 = append(xs1201, item1203)
		cond1202 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys_131204 := xs1201
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1961 := p.construct_iceberg_config(string1195, iceberg_config_scope1196, iceberg_property_entrys1200, iceberg_property_entrys_131204)
	result1206 := _t1961
	p.recordSpan(int(span_start1205), "IcebergConfig")
	return result1206
}

func (p *Parser) parse_iceberg_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1207 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1207
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1208 := p.consumeTerminal("STRING").Value.str
	string_31209 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1208, string_31209}
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1210 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1210
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1962 := p.parse_fragment_id()
	fragment_id1211 := _t1962
	p.consumeLiteral(")")
	_t1963 := &pb.Undefine{FragmentId: fragment_id1211}
	result1213 := _t1963
	p.recordSpan(int(span_start1212), "Undefine")
	return result1213
}

func (p *Parser) parse_context() *pb.Context {
	span_start1218 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1214 := []*pb.RelationId{}
	cond1215 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1215 {
		_t1964 := p.parse_relation_id()
		item1216 := _t1964
		xs1214 = append(xs1214, item1216)
		cond1215 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1217 := xs1214
	p.consumeLiteral(")")
	_t1965 := &pb.Context{Relations: relation_ids1217}
	result1219 := _t1965
	p.recordSpan(int(span_start1218), "Context")
	return result1219
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1224 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1220 := []*pb.SnapshotMapping{}
	cond1221 := p.matchLookaheadLiteral("[", 0)
	for cond1221 {
		_t1966 := p.parse_snapshot_mapping()
		item1222 := _t1966
		xs1220 = append(xs1220, item1222)
		cond1221 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1223 := xs1220
	p.consumeLiteral(")")
	_t1967 := &pb.Snapshot{Mappings: snapshot_mappings1223}
	result1225 := _t1967
	p.recordSpan(int(span_start1224), "Snapshot")
	return result1225
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1228 := int64(p.spanStart())
	_t1968 := p.parse_edb_path()
	edb_path1226 := _t1968
	_t1969 := p.parse_relation_id()
	relation_id1227 := _t1969
	_t1970 := &pb.SnapshotMapping{DestinationPath: edb_path1226, SourceRelation: relation_id1227}
	result1229 := _t1970
	p.recordSpan(int(span_start1228), "SnapshotMapping")
	return result1229
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1230 := []*pb.Read{}
	cond1231 := p.matchLookaheadLiteral("(", 0)
	for cond1231 {
		_t1971 := p.parse_read()
		item1232 := _t1971
		xs1230 = append(xs1230, item1232)
		cond1231 = p.matchLookaheadLiteral("(", 0)
	}
	reads1233 := xs1230
	p.consumeLiteral(")")
	return reads1233
}

func (p *Parser) parse_read() *pb.Read {
	span_start1240 := int64(p.spanStart())
	var _t1972 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1973 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1973 = 2
		} else {
			var _t1974 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1974 = 1
			} else {
				var _t1975 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1975 = 4
				} else {
					var _t1976 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1976 = 4
					} else {
						var _t1977 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1977 = 0
						} else {
							var _t1978 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1978 = 3
							} else {
								_t1978 = -1
							}
							_t1977 = _t1978
						}
						_t1976 = _t1977
					}
					_t1975 = _t1976
				}
				_t1974 = _t1975
			}
			_t1973 = _t1974
		}
		_t1972 = _t1973
	} else {
		_t1972 = -1
	}
	prediction1234 := _t1972
	var _t1979 *pb.Read
	if prediction1234 == 4 {
		_t1980 := p.parse_export()
		export1239 := _t1980
		_t1981 := &pb.Read{}
		_t1981.ReadType = &pb.Read_Export{Export: export1239}
		_t1979 = _t1981
	} else {
		var _t1982 *pb.Read
		if prediction1234 == 3 {
			_t1983 := p.parse_abort()
			abort1238 := _t1983
			_t1984 := &pb.Read{}
			_t1984.ReadType = &pb.Read_Abort{Abort: abort1238}
			_t1982 = _t1984
		} else {
			var _t1985 *pb.Read
			if prediction1234 == 2 {
				_t1986 := p.parse_what_if()
				what_if1237 := _t1986
				_t1987 := &pb.Read{}
				_t1987.ReadType = &pb.Read_WhatIf{WhatIf: what_if1237}
				_t1985 = _t1987
			} else {
				var _t1988 *pb.Read
				if prediction1234 == 1 {
					_t1989 := p.parse_output()
					output1236 := _t1989
					_t1990 := &pb.Read{}
					_t1990.ReadType = &pb.Read_Output{Output: output1236}
					_t1988 = _t1990
				} else {
					var _t1991 *pb.Read
					if prediction1234 == 0 {
						_t1992 := p.parse_demand()
						demand1235 := _t1992
						_t1993 := &pb.Read{}
						_t1993.ReadType = &pb.Read_Demand{Demand: demand1235}
						_t1991 = _t1993
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1988 = _t1991
				}
				_t1985 = _t1988
			}
			_t1982 = _t1985
		}
		_t1979 = _t1982
	}
	result1241 := _t1979
	p.recordSpan(int(span_start1240), "Read")
	return result1241
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1243 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1994 := p.parse_relation_id()
	relation_id1242 := _t1994
	p.consumeLiteral(")")
	_t1995 := &pb.Demand{RelationId: relation_id1242}
	result1244 := _t1995
	p.recordSpan(int(span_start1243), "Demand")
	return result1244
}

func (p *Parser) parse_output() *pb.Output {
	span_start1247 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1996 := p.parse_name()
	name1245 := _t1996
	_t1997 := p.parse_relation_id()
	relation_id1246 := _t1997
	p.consumeLiteral(")")
	_t1998 := &pb.Output{Name: name1245, RelationId: relation_id1246}
	result1248 := _t1998
	p.recordSpan(int(span_start1247), "Output")
	return result1248
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1251 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1999 := p.parse_name()
	name1249 := _t1999
	_t2000 := p.parse_epoch()
	epoch1250 := _t2000
	p.consumeLiteral(")")
	_t2001 := &pb.WhatIf{Branch: name1249, Epoch: epoch1250}
	result1252 := _t2001
	p.recordSpan(int(span_start1251), "WhatIf")
	return result1252
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2002 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2003 := p.parse_name()
		_t2002 = ptr(_t2003)
	}
	name1253 := _t2002
	_t2004 := p.parse_relation_id()
	relation_id1254 := _t2004
	p.consumeLiteral(")")
	_t2005 := &pb.Abort{Name: deref(name1253, "abort"), RelationId: relation_id1254}
	result1256 := _t2005
	p.recordSpan(int(span_start1255), "Abort")
	return result1256
}

func (p *Parser) parse_export() *pb.Export {
	span_start1260 := int64(p.spanStart())
	var _t2006 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2007 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2007 = 1
		} else {
			var _t2008 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2008 = 0
			} else {
				_t2008 = -1
			}
			_t2007 = _t2008
		}
		_t2006 = _t2007
	} else {
		_t2006 = -1
	}
	prediction1257 := _t2006
	var _t2009 *pb.Export
	if prediction1257 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2010 := p.parse_export_iceberg_config()
		export_iceberg_config1259 := _t2010
		p.consumeLiteral(")")
		_t2011 := &pb.Export{}
		_t2011.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1259}
		_t2009 = _t2011
	} else {
		var _t2012 *pb.Export
		if prediction1257 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2013 := p.parse_export_csv_config()
			export_csv_config1258 := _t2013
			p.consumeLiteral(")")
			_t2014 := &pb.Export{}
			_t2014.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1258}
			_t2012 = _t2014
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2009 = _t2012
	}
	result1261 := _t2009
	p.recordSpan(int(span_start1260), "Export")
	return result1261
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1269 := int64(p.spanStart())
	var _t2015 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2016 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2016 = 0
		} else {
			var _t2017 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2017 = 1
			} else {
				_t2017 = -1
			}
			_t2016 = _t2017
		}
		_t2015 = _t2016
	} else {
		_t2015 = -1
	}
	prediction1262 := _t2015
	var _t2018 *pb.ExportCSVConfig
	if prediction1262 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2019 := p.parse_export_csv_path()
		export_csv_path1266 := _t2019
		_t2020 := p.parse_export_csv_columns_list()
		export_csv_columns_list1267 := _t2020
		_t2021 := p.parse_config_dict()
		config_dict1268 := _t2021
		p.consumeLiteral(")")
		_t2022 := p.construct_export_csv_config(export_csv_path1266, export_csv_columns_list1267, config_dict1268)
		_t2018 = _t2022
	} else {
		var _t2023 *pb.ExportCSVConfig
		if prediction1262 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2024 := p.parse_export_csv_path()
			export_csv_path1263 := _t2024
			_t2025 := p.parse_export_csv_source()
			export_csv_source1264 := _t2025
			_t2026 := p.parse_csv_config()
			csv_config1265 := _t2026
			p.consumeLiteral(")")
			_t2027 := p.construct_export_csv_config_with_source(export_csv_path1263, export_csv_source1264, csv_config1265)
			_t2023 = _t2027
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2018 = _t2023
	}
	result1270 := _t2018
	p.recordSpan(int(span_start1269), "ExportCSVConfig")
	return result1270
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1271 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1271
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1278 := int64(p.spanStart())
	var _t2028 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2029 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2029 = 1
		} else {
			var _t2030 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2030 = 0
			} else {
				_t2030 = -1
			}
			_t2029 = _t2030
		}
		_t2028 = _t2029
	} else {
		_t2028 = -1
	}
	prediction1272 := _t2028
	var _t2031 *pb.ExportCSVSource
	if prediction1272 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2032 := p.parse_relation_id()
		relation_id1277 := _t2032
		p.consumeLiteral(")")
		_t2033 := &pb.ExportCSVSource{}
		_t2033.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1277}
		_t2031 = _t2033
	} else {
		var _t2034 *pb.ExportCSVSource
		if prediction1272 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1273 := []*pb.ExportCSVColumn{}
			cond1274 := p.matchLookaheadLiteral("(", 0)
			for cond1274 {
				_t2035 := p.parse_export_csv_column()
				item1275 := _t2035
				xs1273 = append(xs1273, item1275)
				cond1274 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1276 := xs1273
			p.consumeLiteral(")")
			_t2036 := &pb.ExportCSVColumns{Columns: export_csv_columns1276}
			_t2037 := &pb.ExportCSVSource{}
			_t2037.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2036}
			_t2034 = _t2037
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2031 = _t2034
	}
	result1279 := _t2031
	p.recordSpan(int(span_start1278), "ExportCSVSource")
	return result1279
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1282 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1280 := p.consumeTerminal("STRING").Value.str
	_t2038 := p.parse_relation_id()
	relation_id1281 := _t2038
	p.consumeLiteral(")")
	_t2039 := &pb.ExportCSVColumn{ColumnName: string1280, ColumnData: relation_id1281}
	result1283 := _t2039
	p.recordSpan(int(span_start1282), "ExportCSVColumn")
	return result1283
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1284 := []*pb.ExportCSVColumn{}
	cond1285 := p.matchLookaheadLiteral("(", 0)
	for cond1285 {
		_t2040 := p.parse_export_csv_column()
		item1286 := _t2040
		xs1284 = append(xs1284, item1286)
		cond1285 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1287 := xs1284
	p.consumeLiteral(")")
	return export_csv_columns1287
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1295 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2041 := p.parse_iceberg_locator()
	iceberg_locator1288 := _t2041
	_t2042 := p.parse_iceberg_config()
	iceberg_config1289 := _t2042
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1290 := []*pb.IcebergExportColumn{}
	cond1291 := p.matchLookaheadLiteral("(", 0)
	for cond1291 {
		_t2043 := p.parse_iceberg_export_column()
		item1292 := _t2043
		xs1290 = append(xs1290, item1292)
		cond1291 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_export_columns1293 := xs1290
	p.consumeLiteral(")")
	var _t2044 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2045 := p.parse_config_dict()
		_t2044 = _t2045
	}
	config_dict1294 := _t2044
	p.consumeLiteral(")")
	_t2046 := p.construct_export_iceberg_config_full(iceberg_locator1288, iceberg_config1289, iceberg_export_columns1293, config_dict1294)
	result1296 := _t2046
	p.recordSpan(int(span_start1295), "ExportIcebergConfig")
	return result1296
}

func (p *Parser) parse_iceberg_export_column() *pb.IcebergExportColumn {
	span_start1300 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_column")
	string1297 := p.consumeTerminal("STRING").Value.str
	_t2047 := p.parse_type()
	type1298 := _t2047
	_t2048 := p.parse_boolean_value()
	boolean_value1299 := _t2048
	p.consumeLiteral(")")
	_t2049 := &pb.IcebergExportColumn{Name: string1297, Type: type1298, Nullable: boolean_value1299}
	result1301 := _t2049
	p.recordSpan(int(span_start1300), "IcebergExportColumn")
	return result1301
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
