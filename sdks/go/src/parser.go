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
	var _t2059 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2059
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2060 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2060
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2061 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2061
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2062 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2062
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2063 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2063
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2064 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2064
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2065 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2065
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2066 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2066
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2067 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2067
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2068 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2068
	_t2069 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2069
	_t2070 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2070
	_t2071 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2071
	_t2072 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2072
	_t2073 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2073
	_t2074 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2074
	_t2075 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2075
	_t2076 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2076
	_t2077 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2077
	_t2078 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2078
	_t2079 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2079
	_t2080 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2080
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2081 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2081
	_t2082 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2082
	_t2083 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2083
	_t2084 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2084
	_t2085 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2085
	_t2086 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2086
	_t2087 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2087
	_t2088 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2088
	_t2089 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2089
	_t2090 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2090.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2090.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2090
	_t2091 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2091
}

func (p *Parser) default_configure() *pb.Configure {
	_t2092 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2092
	_t2093 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2093
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
	_t2094 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2094
	_t2095 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2095
	_t2096 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2096
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2097 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2097
	_t2098 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2098
	_t2099 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2099
	_t2100 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2100
	_t2101 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2101
	_t2102 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2102
	_t2103 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2103
	_t2104 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2104
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2105 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2105
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2106 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2106
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportIcebergColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2107 := config_dict
	if config_dict == nil {
		_t2107 = [][]interface{}{}
	}
	cfg := dictFromList(_t2107)
	_t2108 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2108
	_t2109 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2109
	_t2110 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2110
	table_props := stringMapFromPairs(table_property_pairs)
	_t2111 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2111
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start661 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1310 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1311 := p.parse_configure()
		_t1310 = _t1311
	}
	configure655 := _t1310
	var _t1312 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1313 := p.parse_sync()
		_t1312 = _t1313
	}
	sync656 := _t1312
	xs657 := []*pb.Epoch{}
	cond658 := p.matchLookaheadLiteral("(", 0)
	for cond658 {
		_t1314 := p.parse_epoch()
		item659 := _t1314
		xs657 = append(xs657, item659)
		cond658 = p.matchLookaheadLiteral("(", 0)
	}
	epochs660 := xs657
	p.consumeLiteral(")")
	_t1315 := p.default_configure()
	_t1316 := configure655
	if configure655 == nil {
		_t1316 = _t1315
	}
	_t1317 := &pb.Transaction{Epochs: epochs660, Configure: _t1316, Sync: sync656}
	result662 := _t1317
	p.recordSpan(int(span_start661), "Transaction")
	return result662
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start664 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1318 := p.parse_config_dict()
	config_dict663 := _t1318
	p.consumeLiteral(")")
	_t1319 := p.construct_configure(config_dict663)
	result665 := _t1319
	p.recordSpan(int(span_start664), "Configure")
	return result665
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs666 := [][]interface{}{}
	cond667 := p.matchLookaheadLiteral(":", 0)
	for cond667 {
		_t1320 := p.parse_config_key_value()
		item668 := _t1320
		xs666 = append(xs666, item668)
		cond667 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values669 := xs666
	p.consumeLiteral("}")
	return config_key_values669
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol670 := p.consumeTerminal("SYMBOL").Value.str
	_t1321 := p.parse_raw_value()
	raw_value671 := _t1321
	return []interface{}{symbol670, raw_value671}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start685 := int64(p.spanStart())
	var _t1322 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1322 = 12
	} else {
		var _t1323 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1323 = 11
		} else {
			var _t1324 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1324 = 12
			} else {
				var _t1325 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1326 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1326 = 1
					} else {
						var _t1327 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1327 = 0
						} else {
							_t1327 = -1
						}
						_t1326 = _t1327
					}
					_t1325 = _t1326
				} else {
					var _t1328 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1328 = 7
					} else {
						var _t1329 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1329 = 8
						} else {
							var _t1330 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1330 = 2
							} else {
								var _t1331 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1331 = 3
								} else {
									var _t1332 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1332 = 9
									} else {
										var _t1333 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1333 = 4
										} else {
											var _t1334 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1334 = 5
											} else {
												var _t1335 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1335 = 6
												} else {
													var _t1336 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1336 = 10
													} else {
														_t1336 = -1
													}
													_t1335 = _t1336
												}
												_t1334 = _t1335
											}
											_t1333 = _t1334
										}
										_t1332 = _t1333
									}
									_t1331 = _t1332
								}
								_t1330 = _t1331
							}
							_t1329 = _t1330
						}
						_t1328 = _t1329
					}
					_t1325 = _t1328
				}
				_t1324 = _t1325
			}
			_t1323 = _t1324
		}
		_t1322 = _t1323
	}
	prediction672 := _t1322
	var _t1337 *pb.Value
	if prediction672 == 12 {
		_t1338 := p.parse_boolean_value()
		boolean_value684 := _t1338
		_t1339 := &pb.Value{}
		_t1339.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value684}
		_t1337 = _t1339
	} else {
		var _t1340 *pb.Value
		if prediction672 == 11 {
			p.consumeLiteral("missing")
			_t1341 := &pb.MissingValue{}
			_t1342 := &pb.Value{}
			_t1342.Value = &pb.Value_MissingValue{MissingValue: _t1341}
			_t1340 = _t1342
		} else {
			var _t1343 *pb.Value
			if prediction672 == 10 {
				decimal683 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1344 := &pb.Value{}
				_t1344.Value = &pb.Value_DecimalValue{DecimalValue: decimal683}
				_t1343 = _t1344
			} else {
				var _t1345 *pb.Value
				if prediction672 == 9 {
					int128682 := p.consumeTerminal("INT128").Value.int128
					_t1346 := &pb.Value{}
					_t1346.Value = &pb.Value_Int128Value{Int128Value: int128682}
					_t1345 = _t1346
				} else {
					var _t1347 *pb.Value
					if prediction672 == 8 {
						uint128681 := p.consumeTerminal("UINT128").Value.uint128
						_t1348 := &pb.Value{}
						_t1348.Value = &pb.Value_Uint128Value{Uint128Value: uint128681}
						_t1347 = _t1348
					} else {
						var _t1349 *pb.Value
						if prediction672 == 7 {
							uint32680 := p.consumeTerminal("UINT32").Value.u32
							_t1350 := &pb.Value{}
							_t1350.Value = &pb.Value_Uint32Value{Uint32Value: uint32680}
							_t1349 = _t1350
						} else {
							var _t1351 *pb.Value
							if prediction672 == 6 {
								float679 := p.consumeTerminal("FLOAT").Value.f64
								_t1352 := &pb.Value{}
								_t1352.Value = &pb.Value_FloatValue{FloatValue: float679}
								_t1351 = _t1352
							} else {
								var _t1353 *pb.Value
								if prediction672 == 5 {
									float32678 := p.consumeTerminal("FLOAT32").Value.f32
									_t1354 := &pb.Value{}
									_t1354.Value = &pb.Value_Float32Value{Float32Value: float32678}
									_t1353 = _t1354
								} else {
									var _t1355 *pb.Value
									if prediction672 == 4 {
										int677 := p.consumeTerminal("INT").Value.i64
										_t1356 := &pb.Value{}
										_t1356.Value = &pb.Value_IntValue{IntValue: int677}
										_t1355 = _t1356
									} else {
										var _t1357 *pb.Value
										if prediction672 == 3 {
											int32676 := p.consumeTerminal("INT32").Value.i32
											_t1358 := &pb.Value{}
											_t1358.Value = &pb.Value_Int32Value{Int32Value: int32676}
											_t1357 = _t1358
										} else {
											var _t1359 *pb.Value
											if prediction672 == 2 {
												string675 := p.consumeTerminal("STRING").Value.str
												_t1360 := &pb.Value{}
												_t1360.Value = &pb.Value_StringValue{StringValue: string675}
												_t1359 = _t1360
											} else {
												var _t1361 *pb.Value
												if prediction672 == 1 {
													_t1362 := p.parse_raw_datetime()
													raw_datetime674 := _t1362
													_t1363 := &pb.Value{}
													_t1363.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime674}
													_t1361 = _t1363
												} else {
													var _t1364 *pb.Value
													if prediction672 == 0 {
														_t1365 := p.parse_raw_date()
														raw_date673 := _t1365
														_t1366 := &pb.Value{}
														_t1366.Value = &pb.Value_DateValue{DateValue: raw_date673}
														_t1364 = _t1366
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1361 = _t1364
												}
												_t1359 = _t1361
											}
											_t1357 = _t1359
										}
										_t1355 = _t1357
									}
									_t1353 = _t1355
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
			_t1340 = _t1343
		}
		_t1337 = _t1340
	}
	result686 := _t1337
	p.recordSpan(int(span_start685), "Value")
	return result686
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start690 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int687 := p.consumeTerminal("INT").Value.i64
	int_3688 := p.consumeTerminal("INT").Value.i64
	int_4689 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1367 := &pb.DateValue{Year: int32(int687), Month: int32(int_3688), Day: int32(int_4689)}
	result691 := _t1367
	p.recordSpan(int(span_start690), "DateValue")
	return result691
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start699 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int692 := p.consumeTerminal("INT").Value.i64
	int_3693 := p.consumeTerminal("INT").Value.i64
	int_4694 := p.consumeTerminal("INT").Value.i64
	int_5695 := p.consumeTerminal("INT").Value.i64
	int_6696 := p.consumeTerminal("INT").Value.i64
	int_7697 := p.consumeTerminal("INT").Value.i64
	var _t1368 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1368 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8698 := _t1368
	p.consumeLiteral(")")
	_t1369 := &pb.DateTimeValue{Year: int32(int692), Month: int32(int_3693), Day: int32(int_4694), Hour: int32(int_5695), Minute: int32(int_6696), Second: int32(int_7697), Microsecond: int32(deref(int_8698, 0))}
	result700 := _t1369
	p.recordSpan(int(span_start699), "DateTimeValue")
	return result700
}

func (p *Parser) parse_boolean_value() bool {
	var _t1370 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1370 = 0
	} else {
		var _t1371 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1371 = 1
		} else {
			_t1371 = -1
		}
		_t1370 = _t1371
	}
	prediction701 := _t1370
	var _t1372 bool
	if prediction701 == 1 {
		p.consumeLiteral("false")
		_t1372 = false
	} else {
		var _t1373 bool
		if prediction701 == 0 {
			p.consumeLiteral("true")
			_t1373 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1372 = _t1373
	}
	return _t1372
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start706 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs702 := []*pb.FragmentId{}
	cond703 := p.matchLookaheadLiteral(":", 0)
	for cond703 {
		_t1374 := p.parse_fragment_id()
		item704 := _t1374
		xs702 = append(xs702, item704)
		cond703 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids705 := xs702
	p.consumeLiteral(")")
	_t1375 := &pb.Sync{Fragments: fragment_ids705}
	result707 := _t1375
	p.recordSpan(int(span_start706), "Sync")
	return result707
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol708 := p.consumeTerminal("SYMBOL").Value.str
	result710 := &pb.FragmentId{Id: []byte(symbol708)}
	p.recordSpan(int(span_start709), "FragmentId")
	return result710
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1376 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1377 := p.parse_epoch_writes()
		_t1376 = _t1377
	}
	epoch_writes711 := _t1376
	var _t1378 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1379 := p.parse_epoch_reads()
		_t1378 = _t1379
	}
	epoch_reads712 := _t1378
	p.consumeLiteral(")")
	_t1380 := epoch_writes711
	if epoch_writes711 == nil {
		_t1380 = []*pb.Write{}
	}
	_t1381 := epoch_reads712
	if epoch_reads712 == nil {
		_t1381 = []*pb.Read{}
	}
	_t1382 := &pb.Epoch{Writes: _t1380, Reads: _t1381}
	result714 := _t1382
	p.recordSpan(int(span_start713), "Epoch")
	return result714
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs715 := []*pb.Write{}
	cond716 := p.matchLookaheadLiteral("(", 0)
	for cond716 {
		_t1383 := p.parse_write()
		item717 := _t1383
		xs715 = append(xs715, item717)
		cond716 = p.matchLookaheadLiteral("(", 0)
	}
	writes718 := xs715
	p.consumeLiteral(")")
	return writes718
}

func (p *Parser) parse_write() *pb.Write {
	span_start724 := int64(p.spanStart())
	var _t1384 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1385 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1385 = 1
		} else {
			var _t1386 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1386 = 3
			} else {
				var _t1387 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1387 = 0
				} else {
					var _t1388 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1388 = 2
					} else {
						_t1388 = -1
					}
					_t1387 = _t1388
				}
				_t1386 = _t1387
			}
			_t1385 = _t1386
		}
		_t1384 = _t1385
	} else {
		_t1384 = -1
	}
	prediction719 := _t1384
	var _t1389 *pb.Write
	if prediction719 == 3 {
		_t1390 := p.parse_snapshot()
		snapshot723 := _t1390
		_t1391 := &pb.Write{}
		_t1391.WriteType = &pb.Write_Snapshot{Snapshot: snapshot723}
		_t1389 = _t1391
	} else {
		var _t1392 *pb.Write
		if prediction719 == 2 {
			_t1393 := p.parse_context()
			context722 := _t1393
			_t1394 := &pb.Write{}
			_t1394.WriteType = &pb.Write_Context{Context: context722}
			_t1392 = _t1394
		} else {
			var _t1395 *pb.Write
			if prediction719 == 1 {
				_t1396 := p.parse_undefine()
				undefine721 := _t1396
				_t1397 := &pb.Write{}
				_t1397.WriteType = &pb.Write_Undefine{Undefine: undefine721}
				_t1395 = _t1397
			} else {
				var _t1398 *pb.Write
				if prediction719 == 0 {
					_t1399 := p.parse_define()
					define720 := _t1399
					_t1400 := &pb.Write{}
					_t1400.WriteType = &pb.Write_Define{Define: define720}
					_t1398 = _t1400
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1395 = _t1398
			}
			_t1392 = _t1395
		}
		_t1389 = _t1392
	}
	result725 := _t1389
	p.recordSpan(int(span_start724), "Write")
	return result725
}

func (p *Parser) parse_define() *pb.Define {
	span_start727 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1401 := p.parse_fragment()
	fragment726 := _t1401
	p.consumeLiteral(")")
	_t1402 := &pb.Define{Fragment: fragment726}
	result728 := _t1402
	p.recordSpan(int(span_start727), "Define")
	return result728
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start734 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1403 := p.parse_new_fragment_id()
	new_fragment_id729 := _t1403
	xs730 := []*pb.Declaration{}
	cond731 := p.matchLookaheadLiteral("(", 0)
	for cond731 {
		_t1404 := p.parse_declaration()
		item732 := _t1404
		xs730 = append(xs730, item732)
		cond731 = p.matchLookaheadLiteral("(", 0)
	}
	declarations733 := xs730
	p.consumeLiteral(")")
	result735 := p.constructFragment(new_fragment_id729, declarations733)
	p.recordSpan(int(span_start734), "Fragment")
	return result735
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start737 := int64(p.spanStart())
	_t1405 := p.parse_fragment_id()
	fragment_id736 := _t1405
	p.startFragment(fragment_id736)
	result738 := fragment_id736
	p.recordSpan(int(span_start737), "FragmentId")
	return result738
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start744 := int64(p.spanStart())
	var _t1406 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1407 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1407 = 3
		} else {
			var _t1408 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1408 = 2
			} else {
				var _t1409 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1409 = 3
				} else {
					var _t1410 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1410 = 0
					} else {
						var _t1411 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1411 = 3
						} else {
							var _t1412 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1412 = 3
							} else {
								var _t1413 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1413 = 1
								} else {
									_t1413 = -1
								}
								_t1412 = _t1413
							}
							_t1411 = _t1412
						}
						_t1410 = _t1411
					}
					_t1409 = _t1410
				}
				_t1408 = _t1409
			}
			_t1407 = _t1408
		}
		_t1406 = _t1407
	} else {
		_t1406 = -1
	}
	prediction739 := _t1406
	var _t1414 *pb.Declaration
	if prediction739 == 3 {
		_t1415 := p.parse_data()
		data743 := _t1415
		_t1416 := &pb.Declaration{}
		_t1416.DeclarationType = &pb.Declaration_Data{Data: data743}
		_t1414 = _t1416
	} else {
		var _t1417 *pb.Declaration
		if prediction739 == 2 {
			_t1418 := p.parse_constraint()
			constraint742 := _t1418
			_t1419 := &pb.Declaration{}
			_t1419.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint742}
			_t1417 = _t1419
		} else {
			var _t1420 *pb.Declaration
			if prediction739 == 1 {
				_t1421 := p.parse_algorithm()
				algorithm741 := _t1421
				_t1422 := &pb.Declaration{}
				_t1422.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm741}
				_t1420 = _t1422
			} else {
				var _t1423 *pb.Declaration
				if prediction739 == 0 {
					_t1424 := p.parse_def()
					def740 := _t1424
					_t1425 := &pb.Declaration{}
					_t1425.DeclarationType = &pb.Declaration_Def{Def: def740}
					_t1423 = _t1425
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1420 = _t1423
			}
			_t1417 = _t1420
		}
		_t1414 = _t1417
	}
	result745 := _t1414
	p.recordSpan(int(span_start744), "Declaration")
	return result745
}

func (p *Parser) parse_def() *pb.Def {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1426 := p.parse_relation_id()
	relation_id746 := _t1426
	_t1427 := p.parse_abstraction()
	abstraction747 := _t1427
	var _t1428 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1429 := p.parse_attrs()
		_t1428 = _t1429
	}
	attrs748 := _t1428
	p.consumeLiteral(")")
	_t1430 := attrs748
	if attrs748 == nil {
		_t1430 = []*pb.Attribute{}
	}
	_t1431 := &pb.Def{Name: relation_id746, Body: abstraction747, Attrs: _t1430}
	result750 := _t1431
	p.recordSpan(int(span_start749), "Def")
	return result750
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start754 := int64(p.spanStart())
	var _t1432 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1432 = 0
	} else {
		var _t1433 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1433 = 1
		} else {
			_t1433 = -1
		}
		_t1432 = _t1433
	}
	prediction751 := _t1432
	var _t1434 *pb.RelationId
	if prediction751 == 1 {
		uint128753 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128753
		_t1434 = &pb.RelationId{IdLow: uint128753.Low, IdHigh: uint128753.High}
	} else {
		var _t1435 *pb.RelationId
		if prediction751 == 0 {
			p.consumeLiteral(":")
			symbol752 := p.consumeTerminal("SYMBOL").Value.str
			_t1435 = p.relationIdFromString(symbol752)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1434 = _t1435
	}
	result755 := _t1434
	p.recordSpan(int(span_start754), "RelationId")
	return result755
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start758 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1436 := p.parse_bindings()
	bindings756 := _t1436
	_t1437 := p.parse_formula()
	formula757 := _t1437
	p.consumeLiteral(")")
	_t1438 := &pb.Abstraction{Vars: listConcat(bindings756[0].([]*pb.Binding), bindings756[1].([]*pb.Binding)), Value: formula757}
	result759 := _t1438
	p.recordSpan(int(span_start758), "Abstraction")
	return result759
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs760 := []*pb.Binding{}
	cond761 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond761 {
		_t1439 := p.parse_binding()
		item762 := _t1439
		xs760 = append(xs760, item762)
		cond761 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings763 := xs760
	var _t1440 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1441 := p.parse_value_bindings()
		_t1440 = _t1441
	}
	value_bindings764 := _t1440
	p.consumeLiteral("]")
	_t1442 := value_bindings764
	if value_bindings764 == nil {
		_t1442 = []*pb.Binding{}
	}
	return []interface{}{bindings763, _t1442}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start767 := int64(p.spanStart())
	symbol765 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1443 := p.parse_type()
	type766 := _t1443
	_t1444 := &pb.Var{Name: symbol765}
	_t1445 := &pb.Binding{Var: _t1444, Type: type766}
	result768 := _t1445
	p.recordSpan(int(span_start767), "Binding")
	return result768
}

func (p *Parser) parse_type() *pb.Type {
	span_start784 := int64(p.spanStart())
	var _t1446 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1446 = 0
	} else {
		var _t1447 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1447 = 13
		} else {
			var _t1448 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1448 = 4
			} else {
				var _t1449 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1449 = 1
				} else {
					var _t1450 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1450 = 8
					} else {
						var _t1451 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1451 = 11
						} else {
							var _t1452 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1452 = 5
							} else {
								var _t1453 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1453 = 2
								} else {
									var _t1454 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1454 = 12
									} else {
										var _t1455 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1455 = 3
										} else {
											var _t1456 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1456 = 7
											} else {
												var _t1457 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1457 = 6
												} else {
													var _t1458 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1458 = 10
													} else {
														var _t1459 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1459 = 9
														} else {
															_t1459 = -1
														}
														_t1458 = _t1459
													}
													_t1457 = _t1458
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
					}
					_t1449 = _t1450
				}
				_t1448 = _t1449
			}
			_t1447 = _t1448
		}
		_t1446 = _t1447
	}
	prediction769 := _t1446
	var _t1460 *pb.Type
	if prediction769 == 13 {
		_t1461 := p.parse_uint32_type()
		uint32_type783 := _t1461
		_t1462 := &pb.Type{}
		_t1462.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type783}
		_t1460 = _t1462
	} else {
		var _t1463 *pb.Type
		if prediction769 == 12 {
			_t1464 := p.parse_float32_type()
			float32_type782 := _t1464
			_t1465 := &pb.Type{}
			_t1465.Type = &pb.Type_Float32Type{Float32Type: float32_type782}
			_t1463 = _t1465
		} else {
			var _t1466 *pb.Type
			if prediction769 == 11 {
				_t1467 := p.parse_int32_type()
				int32_type781 := _t1467
				_t1468 := &pb.Type{}
				_t1468.Type = &pb.Type_Int32Type{Int32Type: int32_type781}
				_t1466 = _t1468
			} else {
				var _t1469 *pb.Type
				if prediction769 == 10 {
					_t1470 := p.parse_boolean_type()
					boolean_type780 := _t1470
					_t1471 := &pb.Type{}
					_t1471.Type = &pb.Type_BooleanType{BooleanType: boolean_type780}
					_t1469 = _t1471
				} else {
					var _t1472 *pb.Type
					if prediction769 == 9 {
						_t1473 := p.parse_decimal_type()
						decimal_type779 := _t1473
						_t1474 := &pb.Type{}
						_t1474.Type = &pb.Type_DecimalType{DecimalType: decimal_type779}
						_t1472 = _t1474
					} else {
						var _t1475 *pb.Type
						if prediction769 == 8 {
							_t1476 := p.parse_missing_type()
							missing_type778 := _t1476
							_t1477 := &pb.Type{}
							_t1477.Type = &pb.Type_MissingType{MissingType: missing_type778}
							_t1475 = _t1477
						} else {
							var _t1478 *pb.Type
							if prediction769 == 7 {
								_t1479 := p.parse_datetime_type()
								datetime_type777 := _t1479
								_t1480 := &pb.Type{}
								_t1480.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type777}
								_t1478 = _t1480
							} else {
								var _t1481 *pb.Type
								if prediction769 == 6 {
									_t1482 := p.parse_date_type()
									date_type776 := _t1482
									_t1483 := &pb.Type{}
									_t1483.Type = &pb.Type_DateType{DateType: date_type776}
									_t1481 = _t1483
								} else {
									var _t1484 *pb.Type
									if prediction769 == 5 {
										_t1485 := p.parse_int128_type()
										int128_type775 := _t1485
										_t1486 := &pb.Type{}
										_t1486.Type = &pb.Type_Int128Type{Int128Type: int128_type775}
										_t1484 = _t1486
									} else {
										var _t1487 *pb.Type
										if prediction769 == 4 {
											_t1488 := p.parse_uint128_type()
											uint128_type774 := _t1488
											_t1489 := &pb.Type{}
											_t1489.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type774}
											_t1487 = _t1489
										} else {
											var _t1490 *pb.Type
											if prediction769 == 3 {
												_t1491 := p.parse_float_type()
												float_type773 := _t1491
												_t1492 := &pb.Type{}
												_t1492.Type = &pb.Type_FloatType{FloatType: float_type773}
												_t1490 = _t1492
											} else {
												var _t1493 *pb.Type
												if prediction769 == 2 {
													_t1494 := p.parse_int_type()
													int_type772 := _t1494
													_t1495 := &pb.Type{}
													_t1495.Type = &pb.Type_IntType{IntType: int_type772}
													_t1493 = _t1495
												} else {
													var _t1496 *pb.Type
													if prediction769 == 1 {
														_t1497 := p.parse_string_type()
														string_type771 := _t1497
														_t1498 := &pb.Type{}
														_t1498.Type = &pb.Type_StringType{StringType: string_type771}
														_t1496 = _t1498
													} else {
														var _t1499 *pb.Type
														if prediction769 == 0 {
															_t1500 := p.parse_unspecified_type()
															unspecified_type770 := _t1500
															_t1501 := &pb.Type{}
															_t1501.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type770}
															_t1499 = _t1501
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
									_t1481 = _t1484
								}
								_t1478 = _t1481
							}
							_t1475 = _t1478
						}
						_t1472 = _t1475
					}
					_t1469 = _t1472
				}
				_t1466 = _t1469
			}
			_t1463 = _t1466
		}
		_t1460 = _t1463
	}
	result785 := _t1460
	p.recordSpan(int(span_start784), "Type")
	return result785
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start786 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1502 := &pb.UnspecifiedType{}
	result787 := _t1502
	p.recordSpan(int(span_start786), "UnspecifiedType")
	return result787
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start788 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1503 := &pb.StringType{}
	result789 := _t1503
	p.recordSpan(int(span_start788), "StringType")
	return result789
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start790 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1504 := &pb.IntType{}
	result791 := _t1504
	p.recordSpan(int(span_start790), "IntType")
	return result791
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start792 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1505 := &pb.FloatType{}
	result793 := _t1505
	p.recordSpan(int(span_start792), "FloatType")
	return result793
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start794 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1506 := &pb.UInt128Type{}
	result795 := _t1506
	p.recordSpan(int(span_start794), "UInt128Type")
	return result795
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1507 := &pb.Int128Type{}
	result797 := _t1507
	p.recordSpan(int(span_start796), "Int128Type")
	return result797
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1508 := &pb.DateType{}
	result799 := _t1508
	p.recordSpan(int(span_start798), "DateType")
	return result799
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1509 := &pb.DateTimeType{}
	result801 := _t1509
	p.recordSpan(int(span_start800), "DateTimeType")
	return result801
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1510 := &pb.MissingType{}
	result803 := _t1510
	p.recordSpan(int(span_start802), "MissingType")
	return result803
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int804 := p.consumeTerminal("INT").Value.i64
	int_3805 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1511 := &pb.DecimalType{Precision: int32(int804), Scale: int32(int_3805)}
	result807 := _t1511
	p.recordSpan(int(span_start806), "DecimalType")
	return result807
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1512 := &pb.BooleanType{}
	result809 := _t1512
	p.recordSpan(int(span_start808), "BooleanType")
	return result809
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1513 := &pb.Int32Type{}
	result811 := _t1513
	p.recordSpan(int(span_start810), "Int32Type")
	return result811
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1514 := &pb.Float32Type{}
	result813 := _t1514
	p.recordSpan(int(span_start812), "Float32Type")
	return result813
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1515 := &pb.UInt32Type{}
	result815 := _t1515
	p.recordSpan(int(span_start814), "UInt32Type")
	return result815
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs816 := []*pb.Binding{}
	cond817 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond817 {
		_t1516 := p.parse_binding()
		item818 := _t1516
		xs816 = append(xs816, item818)
		cond817 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings819 := xs816
	return bindings819
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start834 := int64(p.spanStart())
	var _t1517 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1518 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1518 = 0
		} else {
			var _t1519 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1519 = 11
			} else {
				var _t1520 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1520 = 3
				} else {
					var _t1521 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1521 = 10
					} else {
						var _t1522 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1522 = 9
						} else {
							var _t1523 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1523 = 5
							} else {
								var _t1524 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1524 = 6
								} else {
									var _t1525 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1525 = 7
									} else {
										var _t1526 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1526 = 1
										} else {
											var _t1527 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1527 = 2
											} else {
												var _t1528 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1528 = 12
												} else {
													var _t1529 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1529 = 8
													} else {
														var _t1530 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1530 = 4
														} else {
															var _t1531 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1531 = 10
															} else {
																var _t1532 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1532 = 10
																} else {
																	var _t1533 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1533 = 10
																	} else {
																		var _t1534 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1534 = 10
																		} else {
																			var _t1535 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1535 = 10
																			} else {
																				var _t1536 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1536 = 10
																				} else {
																					var _t1537 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1537 = 10
																					} else {
																						var _t1538 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1538 = 10
																						} else {
																							var _t1539 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1539 = 10
																							} else {
																								_t1539 = -1
																							}
																							_t1538 = _t1539
																						}
																						_t1537 = _t1538
																					}
																					_t1536 = _t1537
																				}
																				_t1535 = _t1536
																			}
																			_t1534 = _t1535
																		}
																		_t1533 = _t1534
																	}
																	_t1532 = _t1533
																}
																_t1531 = _t1532
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
	} else {
		_t1517 = -1
	}
	prediction820 := _t1517
	var _t1540 *pb.Formula
	if prediction820 == 12 {
		_t1541 := p.parse_cast()
		cast833 := _t1541
		_t1542 := &pb.Formula{}
		_t1542.FormulaType = &pb.Formula_Cast{Cast: cast833}
		_t1540 = _t1542
	} else {
		var _t1543 *pb.Formula
		if prediction820 == 11 {
			_t1544 := p.parse_rel_atom()
			rel_atom832 := _t1544
			_t1545 := &pb.Formula{}
			_t1545.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom832}
			_t1543 = _t1545
		} else {
			var _t1546 *pb.Formula
			if prediction820 == 10 {
				_t1547 := p.parse_primitive()
				primitive831 := _t1547
				_t1548 := &pb.Formula{}
				_t1548.FormulaType = &pb.Formula_Primitive{Primitive: primitive831}
				_t1546 = _t1548
			} else {
				var _t1549 *pb.Formula
				if prediction820 == 9 {
					_t1550 := p.parse_pragma()
					pragma830 := _t1550
					_t1551 := &pb.Formula{}
					_t1551.FormulaType = &pb.Formula_Pragma{Pragma: pragma830}
					_t1549 = _t1551
				} else {
					var _t1552 *pb.Formula
					if prediction820 == 8 {
						_t1553 := p.parse_atom()
						atom829 := _t1553
						_t1554 := &pb.Formula{}
						_t1554.FormulaType = &pb.Formula_Atom{Atom: atom829}
						_t1552 = _t1554
					} else {
						var _t1555 *pb.Formula
						if prediction820 == 7 {
							_t1556 := p.parse_ffi()
							ffi828 := _t1556
							_t1557 := &pb.Formula{}
							_t1557.FormulaType = &pb.Formula_Ffi{Ffi: ffi828}
							_t1555 = _t1557
						} else {
							var _t1558 *pb.Formula
							if prediction820 == 6 {
								_t1559 := p.parse_not()
								not827 := _t1559
								_t1560 := &pb.Formula{}
								_t1560.FormulaType = &pb.Formula_Not{Not: not827}
								_t1558 = _t1560
							} else {
								var _t1561 *pb.Formula
								if prediction820 == 5 {
									_t1562 := p.parse_disjunction()
									disjunction826 := _t1562
									_t1563 := &pb.Formula{}
									_t1563.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction826}
									_t1561 = _t1563
								} else {
									var _t1564 *pb.Formula
									if prediction820 == 4 {
										_t1565 := p.parse_conjunction()
										conjunction825 := _t1565
										_t1566 := &pb.Formula{}
										_t1566.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction825}
										_t1564 = _t1566
									} else {
										var _t1567 *pb.Formula
										if prediction820 == 3 {
											_t1568 := p.parse_reduce()
											reduce824 := _t1568
											_t1569 := &pb.Formula{}
											_t1569.FormulaType = &pb.Formula_Reduce{Reduce: reduce824}
											_t1567 = _t1569
										} else {
											var _t1570 *pb.Formula
											if prediction820 == 2 {
												_t1571 := p.parse_exists()
												exists823 := _t1571
												_t1572 := &pb.Formula{}
												_t1572.FormulaType = &pb.Formula_Exists{Exists: exists823}
												_t1570 = _t1572
											} else {
												var _t1573 *pb.Formula
												if prediction820 == 1 {
													_t1574 := p.parse_false()
													false822 := _t1574
													_t1575 := &pb.Formula{}
													_t1575.FormulaType = &pb.Formula_Disjunction{Disjunction: false822}
													_t1573 = _t1575
												} else {
													var _t1576 *pb.Formula
													if prediction820 == 0 {
														_t1577 := p.parse_true()
														true821 := _t1577
														_t1578 := &pb.Formula{}
														_t1578.FormulaType = &pb.Formula_Conjunction{Conjunction: true821}
														_t1576 = _t1578
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
							_t1555 = _t1558
						}
						_t1552 = _t1555
					}
					_t1549 = _t1552
				}
				_t1546 = _t1549
			}
			_t1543 = _t1546
		}
		_t1540 = _t1543
	}
	result835 := _t1540
	p.recordSpan(int(span_start834), "Formula")
	return result835
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start836 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1579 := &pb.Conjunction{Args: []*pb.Formula{}}
	result837 := _t1579
	p.recordSpan(int(span_start836), "Conjunction")
	return result837
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start838 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1580 := &pb.Disjunction{Args: []*pb.Formula{}}
	result839 := _t1580
	p.recordSpan(int(span_start838), "Disjunction")
	return result839
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1581 := p.parse_bindings()
	bindings840 := _t1581
	_t1582 := p.parse_formula()
	formula841 := _t1582
	p.consumeLiteral(")")
	_t1583 := &pb.Abstraction{Vars: listConcat(bindings840[0].([]*pb.Binding), bindings840[1].([]*pb.Binding)), Value: formula841}
	_t1584 := &pb.Exists{Body: _t1583}
	result843 := _t1584
	p.recordSpan(int(span_start842), "Exists")
	return result843
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1585 := p.parse_abstraction()
	abstraction844 := _t1585
	_t1586 := p.parse_abstraction()
	abstraction_3845 := _t1586
	_t1587 := p.parse_terms()
	terms846 := _t1587
	p.consumeLiteral(")")
	_t1588 := &pb.Reduce{Op: abstraction844, Body: abstraction_3845, Terms: terms846}
	result848 := _t1588
	p.recordSpan(int(span_start847), "Reduce")
	return result848
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs849 := []*pb.Term{}
	cond850 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond850 {
		_t1589 := p.parse_term()
		item851 := _t1589
		xs849 = append(xs849, item851)
		cond850 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms852 := xs849
	p.consumeLiteral(")")
	return terms852
}

func (p *Parser) parse_term() *pb.Term {
	span_start856 := int64(p.spanStart())
	var _t1590 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1590 = 1
	} else {
		var _t1591 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1591 = 1
		} else {
			var _t1592 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1592 = 1
			} else {
				var _t1593 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1593 = 1
				} else {
					var _t1594 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1594 = 0
					} else {
						var _t1595 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1595 = 1
						} else {
							var _t1596 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1596 = 1
							} else {
								var _t1597 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1597 = 1
								} else {
									var _t1598 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1598 = 1
									} else {
										var _t1599 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1599 = 1
										} else {
											var _t1600 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1600 = 1
											} else {
												var _t1601 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1601 = 1
												} else {
													var _t1602 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1602 = 1
													} else {
														var _t1603 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1603 = 1
														} else {
															_t1603 = -1
														}
														_t1602 = _t1603
													}
													_t1601 = _t1602
												}
												_t1600 = _t1601
											}
											_t1599 = _t1600
										}
										_t1598 = _t1599
									}
									_t1597 = _t1598
								}
								_t1596 = _t1597
							}
							_t1595 = _t1596
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
	prediction853 := _t1590
	var _t1604 *pb.Term
	if prediction853 == 1 {
		_t1605 := p.parse_value()
		value855 := _t1605
		_t1606 := &pb.Term{}
		_t1606.TermType = &pb.Term_Constant{Constant: value855}
		_t1604 = _t1606
	} else {
		var _t1607 *pb.Term
		if prediction853 == 0 {
			_t1608 := p.parse_var()
			var854 := _t1608
			_t1609 := &pb.Term{}
			_t1609.TermType = &pb.Term_Var{Var: var854}
			_t1607 = _t1609
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1604 = _t1607
	}
	result857 := _t1604
	p.recordSpan(int(span_start856), "Term")
	return result857
}

func (p *Parser) parse_var() *pb.Var {
	span_start859 := int64(p.spanStart())
	symbol858 := p.consumeTerminal("SYMBOL").Value.str
	_t1610 := &pb.Var{Name: symbol858}
	result860 := _t1610
	p.recordSpan(int(span_start859), "Var")
	return result860
}

func (p *Parser) parse_value() *pb.Value {
	span_start874 := int64(p.spanStart())
	var _t1611 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1611 = 12
	} else {
		var _t1612 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1612 = 11
		} else {
			var _t1613 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1613 = 12
			} else {
				var _t1614 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1615 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1615 = 1
					} else {
						var _t1616 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1616 = 0
						} else {
							_t1616 = -1
						}
						_t1615 = _t1616
					}
					_t1614 = _t1615
				} else {
					var _t1617 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1617 = 7
					} else {
						var _t1618 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1618 = 8
						} else {
							var _t1619 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1619 = 2
							} else {
								var _t1620 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1620 = 3
								} else {
									var _t1621 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1621 = 9
									} else {
										var _t1622 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1622 = 4
										} else {
											var _t1623 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1623 = 5
											} else {
												var _t1624 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1624 = 6
												} else {
													var _t1625 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1625 = 10
													} else {
														_t1625 = -1
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
					_t1614 = _t1617
				}
				_t1613 = _t1614
			}
			_t1612 = _t1613
		}
		_t1611 = _t1612
	}
	prediction861 := _t1611
	var _t1626 *pb.Value
	if prediction861 == 12 {
		_t1627 := p.parse_boolean_value()
		boolean_value873 := _t1627
		_t1628 := &pb.Value{}
		_t1628.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value873}
		_t1626 = _t1628
	} else {
		var _t1629 *pb.Value
		if prediction861 == 11 {
			p.consumeLiteral("missing")
			_t1630 := &pb.MissingValue{}
			_t1631 := &pb.Value{}
			_t1631.Value = &pb.Value_MissingValue{MissingValue: _t1630}
			_t1629 = _t1631
		} else {
			var _t1632 *pb.Value
			if prediction861 == 10 {
				formatted_decimal872 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1633 := &pb.Value{}
				_t1633.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal872}
				_t1632 = _t1633
			} else {
				var _t1634 *pb.Value
				if prediction861 == 9 {
					formatted_int128871 := p.consumeTerminal("INT128").Value.int128
					_t1635 := &pb.Value{}
					_t1635.Value = &pb.Value_Int128Value{Int128Value: formatted_int128871}
					_t1634 = _t1635
				} else {
					var _t1636 *pb.Value
					if prediction861 == 8 {
						formatted_uint128870 := p.consumeTerminal("UINT128").Value.uint128
						_t1637 := &pb.Value{}
						_t1637.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128870}
						_t1636 = _t1637
					} else {
						var _t1638 *pb.Value
						if prediction861 == 7 {
							formatted_uint32869 := p.consumeTerminal("UINT32").Value.u32
							_t1639 := &pb.Value{}
							_t1639.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32869}
							_t1638 = _t1639
						} else {
							var _t1640 *pb.Value
							if prediction861 == 6 {
								formatted_float868 := p.consumeTerminal("FLOAT").Value.f64
								_t1641 := &pb.Value{}
								_t1641.Value = &pb.Value_FloatValue{FloatValue: formatted_float868}
								_t1640 = _t1641
							} else {
								var _t1642 *pb.Value
								if prediction861 == 5 {
									formatted_float32867 := p.consumeTerminal("FLOAT32").Value.f32
									_t1643 := &pb.Value{}
									_t1643.Value = &pb.Value_Float32Value{Float32Value: formatted_float32867}
									_t1642 = _t1643
								} else {
									var _t1644 *pb.Value
									if prediction861 == 4 {
										formatted_int866 := p.consumeTerminal("INT").Value.i64
										_t1645 := &pb.Value{}
										_t1645.Value = &pb.Value_IntValue{IntValue: formatted_int866}
										_t1644 = _t1645
									} else {
										var _t1646 *pb.Value
										if prediction861 == 3 {
											formatted_int32865 := p.consumeTerminal("INT32").Value.i32
											_t1647 := &pb.Value{}
											_t1647.Value = &pb.Value_Int32Value{Int32Value: formatted_int32865}
											_t1646 = _t1647
										} else {
											var _t1648 *pb.Value
											if prediction861 == 2 {
												formatted_string864 := p.consumeTerminal("STRING").Value.str
												_t1649 := &pb.Value{}
												_t1649.Value = &pb.Value_StringValue{StringValue: formatted_string864}
												_t1648 = _t1649
											} else {
												var _t1650 *pb.Value
												if prediction861 == 1 {
													_t1651 := p.parse_datetime()
													datetime863 := _t1651
													_t1652 := &pb.Value{}
													_t1652.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime863}
													_t1650 = _t1652
												} else {
													var _t1653 *pb.Value
													if prediction861 == 0 {
														_t1654 := p.parse_date()
														date862 := _t1654
														_t1655 := &pb.Value{}
														_t1655.Value = &pb.Value_DateValue{DateValue: date862}
														_t1653 = _t1655
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1650 = _t1653
												}
												_t1648 = _t1650
											}
											_t1646 = _t1648
										}
										_t1644 = _t1646
									}
									_t1642 = _t1644
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
			_t1629 = _t1632
		}
		_t1626 = _t1629
	}
	result875 := _t1626
	p.recordSpan(int(span_start874), "Value")
	return result875
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start879 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int876 := p.consumeTerminal("INT").Value.i64
	formatted_int_3877 := p.consumeTerminal("INT").Value.i64
	formatted_int_4878 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1656 := &pb.DateValue{Year: int32(formatted_int876), Month: int32(formatted_int_3877), Day: int32(formatted_int_4878)}
	result880 := _t1656
	p.recordSpan(int(span_start879), "DateValue")
	return result880
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start888 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int881 := p.consumeTerminal("INT").Value.i64
	formatted_int_3882 := p.consumeTerminal("INT").Value.i64
	formatted_int_4883 := p.consumeTerminal("INT").Value.i64
	formatted_int_5884 := p.consumeTerminal("INT").Value.i64
	formatted_int_6885 := p.consumeTerminal("INT").Value.i64
	formatted_int_7886 := p.consumeTerminal("INT").Value.i64
	var _t1657 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1657 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8887 := _t1657
	p.consumeLiteral(")")
	_t1658 := &pb.DateTimeValue{Year: int32(formatted_int881), Month: int32(formatted_int_3882), Day: int32(formatted_int_4883), Hour: int32(formatted_int_5884), Minute: int32(formatted_int_6885), Second: int32(formatted_int_7886), Microsecond: int32(deref(formatted_int_8887, 0))}
	result889 := _t1658
	p.recordSpan(int(span_start888), "DateTimeValue")
	return result889
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start894 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs890 := []*pb.Formula{}
	cond891 := p.matchLookaheadLiteral("(", 0)
	for cond891 {
		_t1659 := p.parse_formula()
		item892 := _t1659
		xs890 = append(xs890, item892)
		cond891 = p.matchLookaheadLiteral("(", 0)
	}
	formulas893 := xs890
	p.consumeLiteral(")")
	_t1660 := &pb.Conjunction{Args: formulas893}
	result895 := _t1660
	p.recordSpan(int(span_start894), "Conjunction")
	return result895
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs896 := []*pb.Formula{}
	cond897 := p.matchLookaheadLiteral("(", 0)
	for cond897 {
		_t1661 := p.parse_formula()
		item898 := _t1661
		xs896 = append(xs896, item898)
		cond897 = p.matchLookaheadLiteral("(", 0)
	}
	formulas899 := xs896
	p.consumeLiteral(")")
	_t1662 := &pb.Disjunction{Args: formulas899}
	result901 := _t1662
	p.recordSpan(int(span_start900), "Disjunction")
	return result901
}

func (p *Parser) parse_not() *pb.Not {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1663 := p.parse_formula()
	formula902 := _t1663
	p.consumeLiteral(")")
	_t1664 := &pb.Not{Arg: formula902}
	result904 := _t1664
	p.recordSpan(int(span_start903), "Not")
	return result904
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start908 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1665 := p.parse_name()
	name905 := _t1665
	_t1666 := p.parse_ffi_args()
	ffi_args906 := _t1666
	_t1667 := p.parse_terms()
	terms907 := _t1667
	p.consumeLiteral(")")
	_t1668 := &pb.FFI{Name: name905, Args: ffi_args906, Terms: terms907}
	result909 := _t1668
	p.recordSpan(int(span_start908), "FFI")
	return result909
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol910 := p.consumeTerminal("SYMBOL").Value.str
	return symbol910
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs911 := []*pb.Abstraction{}
	cond912 := p.matchLookaheadLiteral("(", 0)
	for cond912 {
		_t1669 := p.parse_abstraction()
		item913 := _t1669
		xs911 = append(xs911, item913)
		cond912 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions914 := xs911
	p.consumeLiteral(")")
	return abstractions914
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1670 := p.parse_relation_id()
	relation_id915 := _t1670
	xs916 := []*pb.Term{}
	cond917 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond917 {
		_t1671 := p.parse_term()
		item918 := _t1671
		xs916 = append(xs916, item918)
		cond917 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms919 := xs916
	p.consumeLiteral(")")
	_t1672 := &pb.Atom{Name: relation_id915, Terms: terms919}
	result921 := _t1672
	p.recordSpan(int(span_start920), "Atom")
	return result921
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start927 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1673 := p.parse_name()
	name922 := _t1673
	xs923 := []*pb.Term{}
	cond924 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond924 {
		_t1674 := p.parse_term()
		item925 := _t1674
		xs923 = append(xs923, item925)
		cond924 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms926 := xs923
	p.consumeLiteral(")")
	_t1675 := &pb.Pragma{Name: name922, Terms: terms926}
	result928 := _t1675
	p.recordSpan(int(span_start927), "Pragma")
	return result928
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start944 := int64(p.spanStart())
	var _t1676 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1677 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1677 = 9
		} else {
			var _t1678 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1678 = 4
			} else {
				var _t1679 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1679 = 3
				} else {
					var _t1680 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1680 = 0
					} else {
						var _t1681 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1681 = 2
						} else {
							var _t1682 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1682 = 1
							} else {
								var _t1683 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1683 = 8
								} else {
									var _t1684 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1684 = 6
									} else {
										var _t1685 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1685 = 5
										} else {
											var _t1686 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1686 = 7
											} else {
												_t1686 = -1
											}
											_t1685 = _t1686
										}
										_t1684 = _t1685
									}
									_t1683 = _t1684
								}
								_t1682 = _t1683
							}
							_t1681 = _t1682
						}
						_t1680 = _t1681
					}
					_t1679 = _t1680
				}
				_t1678 = _t1679
			}
			_t1677 = _t1678
		}
		_t1676 = _t1677
	} else {
		_t1676 = -1
	}
	prediction929 := _t1676
	var _t1687 *pb.Primitive
	if prediction929 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1688 := p.parse_name()
		name939 := _t1688
		xs940 := []*pb.RelTerm{}
		cond941 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond941 {
			_t1689 := p.parse_rel_term()
			item942 := _t1689
			xs940 = append(xs940, item942)
			cond941 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms943 := xs940
		p.consumeLiteral(")")
		_t1690 := &pb.Primitive{Name: name939, Terms: rel_terms943}
		_t1687 = _t1690
	} else {
		var _t1691 *pb.Primitive
		if prediction929 == 8 {
			_t1692 := p.parse_divide()
			divide938 := _t1692
			_t1691 = divide938
		} else {
			var _t1693 *pb.Primitive
			if prediction929 == 7 {
				_t1694 := p.parse_multiply()
				multiply937 := _t1694
				_t1693 = multiply937
			} else {
				var _t1695 *pb.Primitive
				if prediction929 == 6 {
					_t1696 := p.parse_minus()
					minus936 := _t1696
					_t1695 = minus936
				} else {
					var _t1697 *pb.Primitive
					if prediction929 == 5 {
						_t1698 := p.parse_add()
						add935 := _t1698
						_t1697 = add935
					} else {
						var _t1699 *pb.Primitive
						if prediction929 == 4 {
							_t1700 := p.parse_gt_eq()
							gt_eq934 := _t1700
							_t1699 = gt_eq934
						} else {
							var _t1701 *pb.Primitive
							if prediction929 == 3 {
								_t1702 := p.parse_gt()
								gt933 := _t1702
								_t1701 = gt933
							} else {
								var _t1703 *pb.Primitive
								if prediction929 == 2 {
									_t1704 := p.parse_lt_eq()
									lt_eq932 := _t1704
									_t1703 = lt_eq932
								} else {
									var _t1705 *pb.Primitive
									if prediction929 == 1 {
										_t1706 := p.parse_lt()
										lt931 := _t1706
										_t1705 = lt931
									} else {
										var _t1707 *pb.Primitive
										if prediction929 == 0 {
											_t1708 := p.parse_eq()
											eq930 := _t1708
											_t1707 = eq930
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1705 = _t1707
									}
									_t1703 = _t1705
								}
								_t1701 = _t1703
							}
							_t1699 = _t1701
						}
						_t1697 = _t1699
					}
					_t1695 = _t1697
				}
				_t1693 = _t1695
			}
			_t1691 = _t1693
		}
		_t1687 = _t1691
	}
	result945 := _t1687
	p.recordSpan(int(span_start944), "Primitive")
	return result945
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1709 := p.parse_term()
	term946 := _t1709
	_t1710 := p.parse_term()
	term_3947 := _t1710
	p.consumeLiteral(")")
	_t1711 := &pb.RelTerm{}
	_t1711.RelTermType = &pb.RelTerm_Term{Term: term946}
	_t1712 := &pb.RelTerm{}
	_t1712.RelTermType = &pb.RelTerm_Term{Term: term_3947}
	_t1713 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1711, _t1712}}
	result949 := _t1713
	p.recordSpan(int(span_start948), "Primitive")
	return result949
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1714 := p.parse_term()
	term950 := _t1714
	_t1715 := p.parse_term()
	term_3951 := _t1715
	p.consumeLiteral(")")
	_t1716 := &pb.RelTerm{}
	_t1716.RelTermType = &pb.RelTerm_Term{Term: term950}
	_t1717 := &pb.RelTerm{}
	_t1717.RelTermType = &pb.RelTerm_Term{Term: term_3951}
	_t1718 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1716, _t1717}}
	result953 := _t1718
	p.recordSpan(int(span_start952), "Primitive")
	return result953
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start956 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1719 := p.parse_term()
	term954 := _t1719
	_t1720 := p.parse_term()
	term_3955 := _t1720
	p.consumeLiteral(")")
	_t1721 := &pb.RelTerm{}
	_t1721.RelTermType = &pb.RelTerm_Term{Term: term954}
	_t1722 := &pb.RelTerm{}
	_t1722.RelTermType = &pb.RelTerm_Term{Term: term_3955}
	_t1723 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1721, _t1722}}
	result957 := _t1723
	p.recordSpan(int(span_start956), "Primitive")
	return result957
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1724 := p.parse_term()
	term958 := _t1724
	_t1725 := p.parse_term()
	term_3959 := _t1725
	p.consumeLiteral(")")
	_t1726 := &pb.RelTerm{}
	_t1726.RelTermType = &pb.RelTerm_Term{Term: term958}
	_t1727 := &pb.RelTerm{}
	_t1727.RelTermType = &pb.RelTerm_Term{Term: term_3959}
	_t1728 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1726, _t1727}}
	result961 := _t1728
	p.recordSpan(int(span_start960), "Primitive")
	return result961
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start964 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1729 := p.parse_term()
	term962 := _t1729
	_t1730 := p.parse_term()
	term_3963 := _t1730
	p.consumeLiteral(")")
	_t1731 := &pb.RelTerm{}
	_t1731.RelTermType = &pb.RelTerm_Term{Term: term962}
	_t1732 := &pb.RelTerm{}
	_t1732.RelTermType = &pb.RelTerm_Term{Term: term_3963}
	_t1733 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1731, _t1732}}
	result965 := _t1733
	p.recordSpan(int(span_start964), "Primitive")
	return result965
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1734 := p.parse_term()
	term966 := _t1734
	_t1735 := p.parse_term()
	term_3967 := _t1735
	_t1736 := p.parse_term()
	term_4968 := _t1736
	p.consumeLiteral(")")
	_t1737 := &pb.RelTerm{}
	_t1737.RelTermType = &pb.RelTerm_Term{Term: term966}
	_t1738 := &pb.RelTerm{}
	_t1738.RelTermType = &pb.RelTerm_Term{Term: term_3967}
	_t1739 := &pb.RelTerm{}
	_t1739.RelTermType = &pb.RelTerm_Term{Term: term_4968}
	_t1740 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1737, _t1738, _t1739}}
	result970 := _t1740
	p.recordSpan(int(span_start969), "Primitive")
	return result970
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1741 := p.parse_term()
	term971 := _t1741
	_t1742 := p.parse_term()
	term_3972 := _t1742
	_t1743 := p.parse_term()
	term_4973 := _t1743
	p.consumeLiteral(")")
	_t1744 := &pb.RelTerm{}
	_t1744.RelTermType = &pb.RelTerm_Term{Term: term971}
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term_3972}
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term_4973}
	_t1747 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1744, _t1745, _t1746}}
	result975 := _t1747
	p.recordSpan(int(span_start974), "Primitive")
	return result975
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1748 := p.parse_term()
	term976 := _t1748
	_t1749 := p.parse_term()
	term_3977 := _t1749
	_t1750 := p.parse_term()
	term_4978 := _t1750
	p.consumeLiteral(")")
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term976}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_3977}
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term_4978}
	_t1754 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1751, _t1752, _t1753}}
	result980 := _t1754
	p.recordSpan(int(span_start979), "Primitive")
	return result980
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1755 := p.parse_term()
	term981 := _t1755
	_t1756 := p.parse_term()
	term_3982 := _t1756
	_t1757 := p.parse_term()
	term_4983 := _t1757
	p.consumeLiteral(")")
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term981}
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term_3982}
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term_4983}
	_t1761 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1758, _t1759, _t1760}}
	result985 := _t1761
	p.recordSpan(int(span_start984), "Primitive")
	return result985
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start989 := int64(p.spanStart())
	var _t1762 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1762 = 1
	} else {
		var _t1763 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1763 = 1
		} else {
			var _t1764 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1764 = 1
			} else {
				var _t1765 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1765 = 1
				} else {
					var _t1766 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1766 = 0
					} else {
						var _t1767 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1767 = 1
						} else {
							var _t1768 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1768 = 1
							} else {
								var _t1769 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1769 = 1
								} else {
									var _t1770 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1770 = 1
									} else {
										var _t1771 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1771 = 1
										} else {
											var _t1772 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1772 = 1
											} else {
												var _t1773 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1773 = 1
												} else {
													var _t1774 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1774 = 1
													} else {
														var _t1775 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1775 = 1
														} else {
															var _t1776 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1776 = 1
															} else {
																_t1776 = -1
															}
															_t1775 = _t1776
														}
														_t1774 = _t1775
													}
													_t1773 = _t1774
												}
												_t1772 = _t1773
											}
											_t1771 = _t1772
										}
										_t1770 = _t1771
									}
									_t1769 = _t1770
								}
								_t1768 = _t1769
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
	prediction986 := _t1762
	var _t1777 *pb.RelTerm
	if prediction986 == 1 {
		_t1778 := p.parse_term()
		term988 := _t1778
		_t1779 := &pb.RelTerm{}
		_t1779.RelTermType = &pb.RelTerm_Term{Term: term988}
		_t1777 = _t1779
	} else {
		var _t1780 *pb.RelTerm
		if prediction986 == 0 {
			_t1781 := p.parse_specialized_value()
			specialized_value987 := _t1781
			_t1782 := &pb.RelTerm{}
			_t1782.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value987}
			_t1780 = _t1782
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1777 = _t1780
	}
	result990 := _t1777
	p.recordSpan(int(span_start989), "RelTerm")
	return result990
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start992 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1783 := p.parse_raw_value()
	raw_value991 := _t1783
	result993 := raw_value991
	p.recordSpan(int(span_start992), "Value")
	return result993
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start999 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1784 := p.parse_name()
	name994 := _t1784
	xs995 := []*pb.RelTerm{}
	cond996 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond996 {
		_t1785 := p.parse_rel_term()
		item997 := _t1785
		xs995 = append(xs995, item997)
		cond996 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms998 := xs995
	p.consumeLiteral(")")
	_t1786 := &pb.RelAtom{Name: name994, Terms: rel_terms998}
	result1000 := _t1786
	p.recordSpan(int(span_start999), "RelAtom")
	return result1000
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1003 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1787 := p.parse_term()
	term1001 := _t1787
	_t1788 := p.parse_term()
	term_31002 := _t1788
	p.consumeLiteral(")")
	_t1789 := &pb.Cast{Input: term1001, Result: term_31002}
	result1004 := _t1789
	p.recordSpan(int(span_start1003), "Cast")
	return result1004
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1005 := []*pb.Attribute{}
	cond1006 := p.matchLookaheadLiteral("(", 0)
	for cond1006 {
		_t1790 := p.parse_attribute()
		item1007 := _t1790
		xs1005 = append(xs1005, item1007)
		cond1006 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1008 := xs1005
	p.consumeLiteral(")")
	return attributes1008
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1014 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1791 := p.parse_name()
	name1009 := _t1791
	xs1010 := []*pb.Value{}
	cond1011 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1011 {
		_t1792 := p.parse_raw_value()
		item1012 := _t1792
		xs1010 = append(xs1010, item1012)
		cond1011 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1013 := xs1010
	p.consumeLiteral(")")
	_t1793 := &pb.Attribute{Name: name1009, Args: raw_values1013}
	result1015 := _t1793
	p.recordSpan(int(span_start1014), "Attribute")
	return result1015
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1016 := []*pb.RelationId{}
	cond1017 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1017 {
		_t1794 := p.parse_relation_id()
		item1018 := _t1794
		xs1016 = append(xs1016, item1018)
		cond1017 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1019 := xs1016
	_t1795 := p.parse_script()
	script1020 := _t1795
	p.consumeLiteral(")")
	_t1796 := &pb.Algorithm{Global: relation_ids1019, Body: script1020}
	result1022 := _t1796
	p.recordSpan(int(span_start1021), "Algorithm")
	return result1022
}

func (p *Parser) parse_script() *pb.Script {
	span_start1027 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1023 := []*pb.Construct{}
	cond1024 := p.matchLookaheadLiteral("(", 0)
	for cond1024 {
		_t1797 := p.parse_construct()
		item1025 := _t1797
		xs1023 = append(xs1023, item1025)
		cond1024 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1026 := xs1023
	p.consumeLiteral(")")
	_t1798 := &pb.Script{Constructs: constructs1026}
	result1028 := _t1798
	p.recordSpan(int(span_start1027), "Script")
	return result1028
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1032 := int64(p.spanStart())
	var _t1799 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1800 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1800 = 1
		} else {
			var _t1801 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1801 = 1
			} else {
				var _t1802 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1802 = 1
				} else {
					var _t1803 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1803 = 0
					} else {
						var _t1804 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1804 = 1
						} else {
							var _t1805 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1805 = 1
							} else {
								_t1805 = -1
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
	} else {
		_t1799 = -1
	}
	prediction1029 := _t1799
	var _t1806 *pb.Construct
	if prediction1029 == 1 {
		_t1807 := p.parse_instruction()
		instruction1031 := _t1807
		_t1808 := &pb.Construct{}
		_t1808.ConstructType = &pb.Construct_Instruction{Instruction: instruction1031}
		_t1806 = _t1808
	} else {
		var _t1809 *pb.Construct
		if prediction1029 == 0 {
			_t1810 := p.parse_loop()
			loop1030 := _t1810
			_t1811 := &pb.Construct{}
			_t1811.ConstructType = &pb.Construct_Loop{Loop: loop1030}
			_t1809 = _t1811
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1806 = _t1809
	}
	result1033 := _t1806
	p.recordSpan(int(span_start1032), "Construct")
	return result1033
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1812 := p.parse_init()
	init1034 := _t1812
	_t1813 := p.parse_script()
	script1035 := _t1813
	p.consumeLiteral(")")
	_t1814 := &pb.Loop{Init: init1034, Body: script1035}
	result1037 := _t1814
	p.recordSpan(int(span_start1036), "Loop")
	return result1037
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1038 := []*pb.Instruction{}
	cond1039 := p.matchLookaheadLiteral("(", 0)
	for cond1039 {
		_t1815 := p.parse_instruction()
		item1040 := _t1815
		xs1038 = append(xs1038, item1040)
		cond1039 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1041 := xs1038
	p.consumeLiteral(")")
	return instructions1041
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1048 := int64(p.spanStart())
	var _t1816 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1817 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1817 = 1
		} else {
			var _t1818 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1818 = 4
			} else {
				var _t1819 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1819 = 3
				} else {
					var _t1820 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1820 = 2
					} else {
						var _t1821 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1821 = 0
						} else {
							_t1821 = -1
						}
						_t1820 = _t1821
					}
					_t1819 = _t1820
				}
				_t1818 = _t1819
			}
			_t1817 = _t1818
		}
		_t1816 = _t1817
	} else {
		_t1816 = -1
	}
	prediction1042 := _t1816
	var _t1822 *pb.Instruction
	if prediction1042 == 4 {
		_t1823 := p.parse_monus_def()
		monus_def1047 := _t1823
		_t1824 := &pb.Instruction{}
		_t1824.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1047}
		_t1822 = _t1824
	} else {
		var _t1825 *pb.Instruction
		if prediction1042 == 3 {
			_t1826 := p.parse_monoid_def()
			monoid_def1046 := _t1826
			_t1827 := &pb.Instruction{}
			_t1827.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1046}
			_t1825 = _t1827
		} else {
			var _t1828 *pb.Instruction
			if prediction1042 == 2 {
				_t1829 := p.parse_break()
				break1045 := _t1829
				_t1830 := &pb.Instruction{}
				_t1830.InstrType = &pb.Instruction_Break{Break: break1045}
				_t1828 = _t1830
			} else {
				var _t1831 *pb.Instruction
				if prediction1042 == 1 {
					_t1832 := p.parse_upsert()
					upsert1044 := _t1832
					_t1833 := &pb.Instruction{}
					_t1833.InstrType = &pb.Instruction_Upsert{Upsert: upsert1044}
					_t1831 = _t1833
				} else {
					var _t1834 *pb.Instruction
					if prediction1042 == 0 {
						_t1835 := p.parse_assign()
						assign1043 := _t1835
						_t1836 := &pb.Instruction{}
						_t1836.InstrType = &pb.Instruction_Assign{Assign: assign1043}
						_t1834 = _t1836
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1831 = _t1834
				}
				_t1828 = _t1831
			}
			_t1825 = _t1828
		}
		_t1822 = _t1825
	}
	result1049 := _t1822
	p.recordSpan(int(span_start1048), "Instruction")
	return result1049
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1837 := p.parse_relation_id()
	relation_id1050 := _t1837
	_t1838 := p.parse_abstraction()
	abstraction1051 := _t1838
	var _t1839 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1840 := p.parse_attrs()
		_t1839 = _t1840
	}
	attrs1052 := _t1839
	p.consumeLiteral(")")
	_t1841 := attrs1052
	if attrs1052 == nil {
		_t1841 = []*pb.Attribute{}
	}
	_t1842 := &pb.Assign{Name: relation_id1050, Body: abstraction1051, Attrs: _t1841}
	result1054 := _t1842
	p.recordSpan(int(span_start1053), "Assign")
	return result1054
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1058 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1843 := p.parse_relation_id()
	relation_id1055 := _t1843
	_t1844 := p.parse_abstraction_with_arity()
	abstraction_with_arity1056 := _t1844
	var _t1845 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1846 := p.parse_attrs()
		_t1845 = _t1846
	}
	attrs1057 := _t1845
	p.consumeLiteral(")")
	_t1847 := attrs1057
	if attrs1057 == nil {
		_t1847 = []*pb.Attribute{}
	}
	_t1848 := &pb.Upsert{Name: relation_id1055, Body: abstraction_with_arity1056[0].(*pb.Abstraction), Attrs: _t1847, ValueArity: abstraction_with_arity1056[1].(int64)}
	result1059 := _t1848
	p.recordSpan(int(span_start1058), "Upsert")
	return result1059
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1849 := p.parse_bindings()
	bindings1060 := _t1849
	_t1850 := p.parse_formula()
	formula1061 := _t1850
	p.consumeLiteral(")")
	_t1851 := &pb.Abstraction{Vars: listConcat(bindings1060[0].([]*pb.Binding), bindings1060[1].([]*pb.Binding)), Value: formula1061}
	return []interface{}{_t1851, int64(len(bindings1060[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1065 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1852 := p.parse_relation_id()
	relation_id1062 := _t1852
	_t1853 := p.parse_abstraction()
	abstraction1063 := _t1853
	var _t1854 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1855 := p.parse_attrs()
		_t1854 = _t1855
	}
	attrs1064 := _t1854
	p.consumeLiteral(")")
	_t1856 := attrs1064
	if attrs1064 == nil {
		_t1856 = []*pb.Attribute{}
	}
	_t1857 := &pb.Break{Name: relation_id1062, Body: abstraction1063, Attrs: _t1856}
	result1066 := _t1857
	p.recordSpan(int(span_start1065), "Break")
	return result1066
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1071 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1858 := p.parse_monoid()
	monoid1067 := _t1858
	_t1859 := p.parse_relation_id()
	relation_id1068 := _t1859
	_t1860 := p.parse_abstraction_with_arity()
	abstraction_with_arity1069 := _t1860
	var _t1861 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1862 := p.parse_attrs()
		_t1861 = _t1862
	}
	attrs1070 := _t1861
	p.consumeLiteral(")")
	_t1863 := attrs1070
	if attrs1070 == nil {
		_t1863 = []*pb.Attribute{}
	}
	_t1864 := &pb.MonoidDef{Monoid: monoid1067, Name: relation_id1068, Body: abstraction_with_arity1069[0].(*pb.Abstraction), Attrs: _t1863, ValueArity: abstraction_with_arity1069[1].(int64)}
	result1072 := _t1864
	p.recordSpan(int(span_start1071), "MonoidDef")
	return result1072
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1078 := int64(p.spanStart())
	var _t1865 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1866 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1866 = 3
		} else {
			var _t1867 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1867 = 0
			} else {
				var _t1868 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1868 = 1
				} else {
					var _t1869 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1869 = 2
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
	} else {
		_t1865 = -1
	}
	prediction1073 := _t1865
	var _t1870 *pb.Monoid
	if prediction1073 == 3 {
		_t1871 := p.parse_sum_monoid()
		sum_monoid1077 := _t1871
		_t1872 := &pb.Monoid{}
		_t1872.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1077}
		_t1870 = _t1872
	} else {
		var _t1873 *pb.Monoid
		if prediction1073 == 2 {
			_t1874 := p.parse_max_monoid()
			max_monoid1076 := _t1874
			_t1875 := &pb.Monoid{}
			_t1875.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1076}
			_t1873 = _t1875
		} else {
			var _t1876 *pb.Monoid
			if prediction1073 == 1 {
				_t1877 := p.parse_min_monoid()
				min_monoid1075 := _t1877
				_t1878 := &pb.Monoid{}
				_t1878.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1075}
				_t1876 = _t1878
			} else {
				var _t1879 *pb.Monoid
				if prediction1073 == 0 {
					_t1880 := p.parse_or_monoid()
					or_monoid1074 := _t1880
					_t1881 := &pb.Monoid{}
					_t1881.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1074}
					_t1879 = _t1881
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1876 = _t1879
			}
			_t1873 = _t1876
		}
		_t1870 = _t1873
	}
	result1079 := _t1870
	p.recordSpan(int(span_start1078), "Monoid")
	return result1079
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1882 := &pb.OrMonoid{}
	result1081 := _t1882
	p.recordSpan(int(span_start1080), "OrMonoid")
	return result1081
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1083 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1883 := p.parse_type()
	type1082 := _t1883
	p.consumeLiteral(")")
	_t1884 := &pb.MinMonoid{Type: type1082}
	result1084 := _t1884
	p.recordSpan(int(span_start1083), "MinMonoid")
	return result1084
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1885 := p.parse_type()
	type1085 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.MaxMonoid{Type: type1085}
	result1087 := _t1886
	p.recordSpan(int(span_start1086), "MaxMonoid")
	return result1087
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1089 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1887 := p.parse_type()
	type1088 := _t1887
	p.consumeLiteral(")")
	_t1888 := &pb.SumMonoid{Type: type1088}
	result1090 := _t1888
	p.recordSpan(int(span_start1089), "SumMonoid")
	return result1090
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1095 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1889 := p.parse_monoid()
	monoid1091 := _t1889
	_t1890 := p.parse_relation_id()
	relation_id1092 := _t1890
	_t1891 := p.parse_abstraction_with_arity()
	abstraction_with_arity1093 := _t1891
	var _t1892 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1893 := p.parse_attrs()
		_t1892 = _t1893
	}
	attrs1094 := _t1892
	p.consumeLiteral(")")
	_t1894 := attrs1094
	if attrs1094 == nil {
		_t1894 = []*pb.Attribute{}
	}
	_t1895 := &pb.MonusDef{Monoid: monoid1091, Name: relation_id1092, Body: abstraction_with_arity1093[0].(*pb.Abstraction), Attrs: _t1894, ValueArity: abstraction_with_arity1093[1].(int64)}
	result1096 := _t1895
	p.recordSpan(int(span_start1095), "MonusDef")
	return result1096
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1101 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1896 := p.parse_relation_id()
	relation_id1097 := _t1896
	_t1897 := p.parse_abstraction()
	abstraction1098 := _t1897
	_t1898 := p.parse_functional_dependency_keys()
	functional_dependency_keys1099 := _t1898
	_t1899 := p.parse_functional_dependency_values()
	functional_dependency_values1100 := _t1899
	p.consumeLiteral(")")
	_t1900 := &pb.FunctionalDependency{Guard: abstraction1098, Keys: functional_dependency_keys1099, Values: functional_dependency_values1100}
	_t1901 := &pb.Constraint{Name: relation_id1097}
	_t1901.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1900}
	result1102 := _t1901
	p.recordSpan(int(span_start1101), "Constraint")
	return result1102
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1103 := []*pb.Var{}
	cond1104 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1104 {
		_t1902 := p.parse_var()
		item1105 := _t1902
		xs1103 = append(xs1103, item1105)
		cond1104 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1106 := xs1103
	p.consumeLiteral(")")
	return vars1106
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1107 := []*pb.Var{}
	cond1108 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1108 {
		_t1903 := p.parse_var()
		item1109 := _t1903
		xs1107 = append(xs1107, item1109)
		cond1108 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1110 := xs1107
	p.consumeLiteral(")")
	return vars1110
}

func (p *Parser) parse_data() *pb.Data {
	span_start1116 := int64(p.spanStart())
	var _t1904 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1905 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1905 = 3
		} else {
			var _t1906 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1906 = 0
			} else {
				var _t1907 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1907 = 2
				} else {
					var _t1908 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1908 = 1
					} else {
						_t1908 = -1
					}
					_t1907 = _t1908
				}
				_t1906 = _t1907
			}
			_t1905 = _t1906
		}
		_t1904 = _t1905
	} else {
		_t1904 = -1
	}
	prediction1111 := _t1904
	var _t1909 *pb.Data
	if prediction1111 == 3 {
		_t1910 := p.parse_iceberg_data()
		iceberg_data1115 := _t1910
		_t1911 := &pb.Data{}
		_t1911.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1115}
		_t1909 = _t1911
	} else {
		var _t1912 *pb.Data
		if prediction1111 == 2 {
			_t1913 := p.parse_csv_data()
			csv_data1114 := _t1913
			_t1914 := &pb.Data{}
			_t1914.DataType = &pb.Data_CsvData{CsvData: csv_data1114}
			_t1912 = _t1914
		} else {
			var _t1915 *pb.Data
			if prediction1111 == 1 {
				_t1916 := p.parse_betree_relation()
				betree_relation1113 := _t1916
				_t1917 := &pb.Data{}
				_t1917.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1113}
				_t1915 = _t1917
			} else {
				var _t1918 *pb.Data
				if prediction1111 == 0 {
					_t1919 := p.parse_edb()
					edb1112 := _t1919
					_t1920 := &pb.Data{}
					_t1920.DataType = &pb.Data_Edb{Edb: edb1112}
					_t1918 = _t1920
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1915 = _t1918
			}
			_t1912 = _t1915
		}
		_t1909 = _t1912
	}
	result1117 := _t1909
	p.recordSpan(int(span_start1116), "Data")
	return result1117
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1921 := p.parse_relation_id()
	relation_id1118 := _t1921
	_t1922 := p.parse_edb_path()
	edb_path1119 := _t1922
	_t1923 := p.parse_edb_types()
	edb_types1120 := _t1923
	p.consumeLiteral(")")
	_t1924 := &pb.EDB{TargetId: relation_id1118, Path: edb_path1119, Types: edb_types1120}
	result1122 := _t1924
	p.recordSpan(int(span_start1121), "EDB")
	return result1122
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1123 := []string{}
	cond1124 := p.matchLookaheadTerminal("STRING", 0)
	for cond1124 {
		item1125 := p.consumeTerminal("STRING").Value.str
		xs1123 = append(xs1123, item1125)
		cond1124 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1126 := xs1123
	p.consumeLiteral("]")
	return strings1126
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1127 := []*pb.Type{}
	cond1128 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1128 {
		_t1925 := p.parse_type()
		item1129 := _t1925
		xs1127 = append(xs1127, item1129)
		cond1128 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1130 := xs1127
	p.consumeLiteral("]")
	return types1130
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1133 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1926 := p.parse_relation_id()
	relation_id1131 := _t1926
	_t1927 := p.parse_betree_info()
	betree_info1132 := _t1927
	p.consumeLiteral(")")
	_t1928 := &pb.BeTreeRelation{Name: relation_id1131, RelationInfo: betree_info1132}
	result1134 := _t1928
	p.recordSpan(int(span_start1133), "BeTreeRelation")
	return result1134
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1929 := p.parse_betree_info_key_types()
	betree_info_key_types1135 := _t1929
	_t1930 := p.parse_betree_info_value_types()
	betree_info_value_types1136 := _t1930
	_t1931 := p.parse_config_dict()
	config_dict1137 := _t1931
	p.consumeLiteral(")")
	_t1932 := p.construct_betree_info(betree_info_key_types1135, betree_info_value_types1136, config_dict1137)
	result1139 := _t1932
	p.recordSpan(int(span_start1138), "BeTreeInfo")
	return result1139
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1140 := []*pb.Type{}
	cond1141 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1141 {
		_t1933 := p.parse_type()
		item1142 := _t1933
		xs1140 = append(xs1140, item1142)
		cond1141 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1143 := xs1140
	p.consumeLiteral(")")
	return types1143
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1144 := []*pb.Type{}
	cond1145 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1145 {
		_t1934 := p.parse_type()
		item1146 := _t1934
		xs1144 = append(xs1144, item1146)
		cond1145 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1147 := xs1144
	p.consumeLiteral(")")
	return types1147
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1152 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1935 := p.parse_csvlocator()
	csvlocator1148 := _t1935
	_t1936 := p.parse_csv_config()
	csv_config1149 := _t1936
	_t1937 := p.parse_gnf_columns()
	gnf_columns1150 := _t1937
	_t1938 := p.parse_csv_asof()
	csv_asof1151 := _t1938
	p.consumeLiteral(")")
	_t1939 := &pb.CSVData{Locator: csvlocator1148, Config: csv_config1149, Columns: gnf_columns1150, Asof: csv_asof1151}
	result1153 := _t1939
	p.recordSpan(int(span_start1152), "CSVData")
	return result1153
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1940 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1941 := p.parse_csv_locator_paths()
		_t1940 = _t1941
	}
	csv_locator_paths1154 := _t1940
	var _t1942 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1943 := p.parse_csv_locator_inline_data()
		_t1942 = ptr(_t1943)
	}
	csv_locator_inline_data1155 := _t1942
	p.consumeLiteral(")")
	_t1944 := csv_locator_paths1154
	if csv_locator_paths1154 == nil {
		_t1944 = []string{}
	}
	_t1945 := &pb.CSVLocator{Paths: _t1944, InlineData: []byte(deref(csv_locator_inline_data1155, ""))}
	result1157 := _t1945
	p.recordSpan(int(span_start1156), "CSVLocator")
	return result1157
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1158 := []string{}
	cond1159 := p.matchLookaheadTerminal("STRING", 0)
	for cond1159 {
		item1160 := p.consumeTerminal("STRING").Value.str
		xs1158 = append(xs1158, item1160)
		cond1159 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1161 := xs1158
	p.consumeLiteral(")")
	return strings1161
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1162 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1162
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1164 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1946 := p.parse_config_dict()
	config_dict1163 := _t1946
	p.consumeLiteral(")")
	_t1947 := p.construct_csv_config(config_dict1163)
	result1165 := _t1947
	p.recordSpan(int(span_start1164), "CSVConfig")
	return result1165
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1166 := []*pb.GNFColumn{}
	cond1167 := p.matchLookaheadLiteral("(", 0)
	for cond1167 {
		_t1948 := p.parse_gnf_column()
		item1168 := _t1948
		xs1166 = append(xs1166, item1168)
		cond1167 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1169 := xs1166
	p.consumeLiteral(")")
	return gnf_columns1169
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1176 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1949 := p.parse_gnf_column_path()
	gnf_column_path1170 := _t1949
	var _t1950 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1951 := p.parse_relation_id()
		_t1950 = _t1951
	}
	relation_id1171 := _t1950
	p.consumeLiteral("[")
	xs1172 := []*pb.Type{}
	cond1173 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1173 {
		_t1952 := p.parse_type()
		item1174 := _t1952
		xs1172 = append(xs1172, item1174)
		cond1173 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1175 := xs1172
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1953 := &pb.GNFColumn{ColumnPath: gnf_column_path1170, TargetId: relation_id1171, Types: types1175}
	result1177 := _t1953
	p.recordSpan(int(span_start1176), "GNFColumn")
	return result1177
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1954 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1954 = 1
	} else {
		var _t1955 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1955 = 0
		} else {
			_t1955 = -1
		}
		_t1954 = _t1955
	}
	prediction1178 := _t1954
	var _t1956 []string
	if prediction1178 == 1 {
		p.consumeLiteral("[")
		xs1180 := []string{}
		cond1181 := p.matchLookaheadTerminal("STRING", 0)
		for cond1181 {
			item1182 := p.consumeTerminal("STRING").Value.str
			xs1180 = append(xs1180, item1182)
			cond1181 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1183 := xs1180
		p.consumeLiteral("]")
		_t1956 = strings1183
	} else {
		var _t1957 []string
		if prediction1178 == 0 {
			string1179 := p.consumeTerminal("STRING").Value.str
			_ = string1179
			_t1957 = []string{string1179}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1956 = _t1957
	}
	return _t1956
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1184 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1184
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1189 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1958 := p.parse_iceberg_locator()
	iceberg_locator1185 := _t1958
	_t1959 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1186 := _t1959
	_t1960 := p.parse_gnf_columns()
	gnf_columns1187 := _t1960
	var _t1961 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1962 := p.parse_iceberg_to_snapshot()
		_t1961 = ptr(_t1962)
	}
	iceberg_to_snapshot1188 := _t1961
	p.consumeLiteral(")")
	_t1963 := &pb.IcebergData{Locator: iceberg_locator1185, Config: iceberg_catalog_config1186, Columns: gnf_columns1187, ToSnapshot: ptr(deref(iceberg_to_snapshot1188, ""))}
	result1190 := _t1963
	p.recordSpan(int(span_start1189), "IcebergData")
	return result1190
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1197 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1191 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1192 := []string{}
	cond1193 := p.matchLookaheadTerminal("STRING", 0)
	for cond1193 {
		item1194 := p.consumeTerminal("STRING").Value.str
		xs1192 = append(xs1192, item1194)
		cond1193 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1195 := xs1192
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121196 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1964 := &pb.IcebergLocator{TableName: string1191, Namespace: strings1195, Warehouse: string_121196}
	result1198 := _t1964
	p.recordSpan(int(span_start1197), "IcebergLocator")
	return result1198
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1209 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1199 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1965 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1966 := p.parse_iceberg_catalog_config_scope()
		_t1965 = ptr(_t1966)
	}
	iceberg_catalog_config_scope1200 := _t1965
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1201 := [][]interface{}{}
	cond1202 := p.matchLookaheadLiteral("(", 0)
	for cond1202 {
		_t1967 := p.parse_iceberg_property_entry()
		item1203 := _t1967
		xs1201 = append(xs1201, item1203)
		cond1202 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1204 := xs1201
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1205 := [][]interface{}{}
	cond1206 := p.matchLookaheadLiteral("(", 0)
	for cond1206 {
		_t1968 := p.parse_iceberg_property_entry()
		item1207 := _t1968
		xs1205 = append(xs1205, item1207)
		cond1206 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys_131208 := xs1205
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1969 := p.construct_iceberg_catalog_config(string1199, iceberg_catalog_config_scope1200, iceberg_property_entrys1204, iceberg_property_entrys_131208)
	result1210 := _t1969
	p.recordSpan(int(span_start1209), "IcebergCatalogConfig")
	return result1210
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1211 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1211
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1212 := p.consumeTerminal("STRING").Value.str
	string_31213 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1212, string_31213}
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1214 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1214
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1216 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1970 := p.parse_fragment_id()
	fragment_id1215 := _t1970
	p.consumeLiteral(")")
	_t1971 := &pb.Undefine{FragmentId: fragment_id1215}
	result1217 := _t1971
	p.recordSpan(int(span_start1216), "Undefine")
	return result1217
}

func (p *Parser) parse_context() *pb.Context {
	span_start1222 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1218 := []*pb.RelationId{}
	cond1219 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1219 {
		_t1972 := p.parse_relation_id()
		item1220 := _t1972
		xs1218 = append(xs1218, item1220)
		cond1219 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1221 := xs1218
	p.consumeLiteral(")")
	_t1973 := &pb.Context{Relations: relation_ids1221}
	result1223 := _t1973
	p.recordSpan(int(span_start1222), "Context")
	return result1223
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1228 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1224 := []*pb.SnapshotMapping{}
	cond1225 := p.matchLookaheadLiteral("[", 0)
	for cond1225 {
		_t1974 := p.parse_snapshot_mapping()
		item1226 := _t1974
		xs1224 = append(xs1224, item1226)
		cond1225 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1227 := xs1224
	p.consumeLiteral(")")
	_t1975 := &pb.Snapshot{Mappings: snapshot_mappings1227}
	result1229 := _t1975
	p.recordSpan(int(span_start1228), "Snapshot")
	return result1229
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1232 := int64(p.spanStart())
	_t1976 := p.parse_edb_path()
	edb_path1230 := _t1976
	_t1977 := p.parse_relation_id()
	relation_id1231 := _t1977
	_t1978 := &pb.SnapshotMapping{DestinationPath: edb_path1230, SourceRelation: relation_id1231}
	result1233 := _t1978
	p.recordSpan(int(span_start1232), "SnapshotMapping")
	return result1233
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1234 := []*pb.Read{}
	cond1235 := p.matchLookaheadLiteral("(", 0)
	for cond1235 {
		_t1979 := p.parse_read()
		item1236 := _t1979
		xs1234 = append(xs1234, item1236)
		cond1235 = p.matchLookaheadLiteral("(", 0)
	}
	reads1237 := xs1234
	p.consumeLiteral(")")
	return reads1237
}

func (p *Parser) parse_read() *pb.Read {
	span_start1244 := int64(p.spanStart())
	var _t1980 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1981 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1981 = 2
		} else {
			var _t1982 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1982 = 1
			} else {
				var _t1983 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1983 = 4
				} else {
					var _t1984 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1984 = 4
					} else {
						var _t1985 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1985 = 0
						} else {
							var _t1986 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1986 = 3
							} else {
								_t1986 = -1
							}
							_t1985 = _t1986
						}
						_t1984 = _t1985
					}
					_t1983 = _t1984
				}
				_t1982 = _t1983
			}
			_t1981 = _t1982
		}
		_t1980 = _t1981
	} else {
		_t1980 = -1
	}
	prediction1238 := _t1980
	var _t1987 *pb.Read
	if prediction1238 == 4 {
		_t1988 := p.parse_export()
		export1243 := _t1988
		_t1989 := &pb.Read{}
		_t1989.ReadType = &pb.Read_Export{Export: export1243}
		_t1987 = _t1989
	} else {
		var _t1990 *pb.Read
		if prediction1238 == 3 {
			_t1991 := p.parse_abort()
			abort1242 := _t1991
			_t1992 := &pb.Read{}
			_t1992.ReadType = &pb.Read_Abort{Abort: abort1242}
			_t1990 = _t1992
		} else {
			var _t1993 *pb.Read
			if prediction1238 == 2 {
				_t1994 := p.parse_what_if()
				what_if1241 := _t1994
				_t1995 := &pb.Read{}
				_t1995.ReadType = &pb.Read_WhatIf{WhatIf: what_if1241}
				_t1993 = _t1995
			} else {
				var _t1996 *pb.Read
				if prediction1238 == 1 {
					_t1997 := p.parse_output()
					output1240 := _t1997
					_t1998 := &pb.Read{}
					_t1998.ReadType = &pb.Read_Output{Output: output1240}
					_t1996 = _t1998
				} else {
					var _t1999 *pb.Read
					if prediction1238 == 0 {
						_t2000 := p.parse_demand()
						demand1239 := _t2000
						_t2001 := &pb.Read{}
						_t2001.ReadType = &pb.Read_Demand{Demand: demand1239}
						_t1999 = _t2001
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1996 = _t1999
				}
				_t1993 = _t1996
			}
			_t1990 = _t1993
		}
		_t1987 = _t1990
	}
	result1245 := _t1987
	p.recordSpan(int(span_start1244), "Read")
	return result1245
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1247 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2002 := p.parse_relation_id()
	relation_id1246 := _t2002
	p.consumeLiteral(")")
	_t2003 := &pb.Demand{RelationId: relation_id1246}
	result1248 := _t2003
	p.recordSpan(int(span_start1247), "Demand")
	return result1248
}

func (p *Parser) parse_output() *pb.Output {
	span_start1251 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2004 := p.parse_name()
	name1249 := _t2004
	_t2005 := p.parse_relation_id()
	relation_id1250 := _t2005
	p.consumeLiteral(")")
	_t2006 := &pb.Output{Name: name1249, RelationId: relation_id1250}
	result1252 := _t2006
	p.recordSpan(int(span_start1251), "Output")
	return result1252
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2007 := p.parse_name()
	name1253 := _t2007
	_t2008 := p.parse_epoch()
	epoch1254 := _t2008
	p.consumeLiteral(")")
	_t2009 := &pb.WhatIf{Branch: name1253, Epoch: epoch1254}
	result1256 := _t2009
	p.recordSpan(int(span_start1255), "WhatIf")
	return result1256
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1259 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2010 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2011 := p.parse_name()
		_t2010 = ptr(_t2011)
	}
	name1257 := _t2010
	_t2012 := p.parse_relation_id()
	relation_id1258 := _t2012
	p.consumeLiteral(")")
	_t2013 := &pb.Abort{Name: deref(name1257, "abort"), RelationId: relation_id1258}
	result1260 := _t2013
	p.recordSpan(int(span_start1259), "Abort")
	return result1260
}

func (p *Parser) parse_export() *pb.Export {
	span_start1264 := int64(p.spanStart())
	var _t2014 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2015 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2015 = 1
		} else {
			var _t2016 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2016 = 0
			} else {
				_t2016 = -1
			}
			_t2015 = _t2016
		}
		_t2014 = _t2015
	} else {
		_t2014 = -1
	}
	prediction1261 := _t2014
	var _t2017 *pb.Export
	if prediction1261 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2018 := p.parse_export_iceberg_config()
		export_iceberg_config1263 := _t2018
		p.consumeLiteral(")")
		_t2019 := &pb.Export{}
		_t2019.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1263}
		_t2017 = _t2019
	} else {
		var _t2020 *pb.Export
		if prediction1261 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2021 := p.parse_export_csv_config()
			export_csv_config1262 := _t2021
			p.consumeLiteral(")")
			_t2022 := &pb.Export{}
			_t2022.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1262}
			_t2020 = _t2022
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2017 = _t2020
	}
	result1265 := _t2017
	p.recordSpan(int(span_start1264), "Export")
	return result1265
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1273 := int64(p.spanStart())
	var _t2023 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2024 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2024 = 0
		} else {
			var _t2025 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2025 = 1
			} else {
				_t2025 = -1
			}
			_t2024 = _t2025
		}
		_t2023 = _t2024
	} else {
		_t2023 = -1
	}
	prediction1266 := _t2023
	var _t2026 *pb.ExportCSVConfig
	if prediction1266 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2027 := p.parse_export_csv_path()
		export_csv_path1270 := _t2027
		_t2028 := p.parse_export_csv_columns_list()
		export_csv_columns_list1271 := _t2028
		_t2029 := p.parse_config_dict()
		config_dict1272 := _t2029
		p.consumeLiteral(")")
		_t2030 := p.construct_export_csv_config(export_csv_path1270, export_csv_columns_list1271, config_dict1272)
		_t2026 = _t2030
	} else {
		var _t2031 *pb.ExportCSVConfig
		if prediction1266 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2032 := p.parse_export_csv_path()
			export_csv_path1267 := _t2032
			_t2033 := p.parse_export_csv_source()
			export_csv_source1268 := _t2033
			_t2034 := p.parse_csv_config()
			csv_config1269 := _t2034
			p.consumeLiteral(")")
			_t2035 := p.construct_export_csv_config_with_source(export_csv_path1267, export_csv_source1268, csv_config1269)
			_t2031 = _t2035
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2026 = _t2031
	}
	result1274 := _t2026
	p.recordSpan(int(span_start1273), "ExportCSVConfig")
	return result1274
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1275 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1275
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1282 := int64(p.spanStart())
	var _t2036 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2037 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2037 = 1
		} else {
			var _t2038 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2038 = 0
			} else {
				_t2038 = -1
			}
			_t2037 = _t2038
		}
		_t2036 = _t2037
	} else {
		_t2036 = -1
	}
	prediction1276 := _t2036
	var _t2039 *pb.ExportCSVSource
	if prediction1276 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2040 := p.parse_relation_id()
		relation_id1281 := _t2040
		p.consumeLiteral(")")
		_t2041 := &pb.ExportCSVSource{}
		_t2041.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1281}
		_t2039 = _t2041
	} else {
		var _t2042 *pb.ExportCSVSource
		if prediction1276 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1277 := []*pb.ExportCSVColumn{}
			cond1278 := p.matchLookaheadLiteral("(", 0)
			for cond1278 {
				_t2043 := p.parse_export_csv_column()
				item1279 := _t2043
				xs1277 = append(xs1277, item1279)
				cond1278 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1280 := xs1277
			p.consumeLiteral(")")
			_t2044 := &pb.ExportCSVColumns{Columns: export_csv_columns1280}
			_t2045 := &pb.ExportCSVSource{}
			_t2045.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2044}
			_t2042 = _t2045
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2039 = _t2042
	}
	result1283 := _t2039
	p.recordSpan(int(span_start1282), "ExportCSVSource")
	return result1283
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1286 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1284 := p.consumeTerminal("STRING").Value.str
	_t2046 := p.parse_relation_id()
	relation_id1285 := _t2046
	p.consumeLiteral(")")
	_t2047 := &pb.ExportCSVColumn{ColumnName: string1284, ColumnData: relation_id1285}
	result1287 := _t2047
	p.recordSpan(int(span_start1286), "ExportCSVColumn")
	return result1287
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1288 := []*pb.ExportCSVColumn{}
	cond1289 := p.matchLookaheadLiteral("(", 0)
	for cond1289 {
		_t2048 := p.parse_export_csv_column()
		item1290 := _t2048
		xs1288 = append(xs1288, item1290)
		cond1289 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1291 := xs1288
	p.consumeLiteral(")")
	return export_csv_columns1291
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1304 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2049 := p.parse_iceberg_locator()
	iceberg_locator1292 := _t2049
	_t2050 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1293 := _t2050
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2051 := p.parse_relation_id()
	relation_id1294 := _t2051
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1295 := []*pb.ExportIcebergColumn{}
	cond1296 := p.matchLookaheadLiteral("(", 0)
	for cond1296 {
		_t2052 := p.parse_export_iceberg_column()
		item1297 := _t2052
		xs1295 = append(xs1295, item1297)
		cond1296 = p.matchLookaheadLiteral("(", 0)
	}
	export_iceberg_columns1298 := xs1295
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1299 := [][]interface{}{}
	cond1300 := p.matchLookaheadLiteral("(", 0)
	for cond1300 {
		_t2053 := p.parse_iceberg_property_entry()
		item1301 := _t2053
		xs1299 = append(xs1299, item1301)
		cond1300 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1302 := xs1299
	p.consumeLiteral(")")
	var _t2054 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2055 := p.parse_config_dict()
		_t2054 = _t2055
	}
	config_dict1303 := _t2054
	p.consumeLiteral(")")
	_t2056 := p.construct_export_iceberg_config_full(iceberg_locator1292, iceberg_catalog_config1293, relation_id1294, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
	result1305 := _t2056
	p.recordSpan(int(span_start1304), "ExportIcebergConfig")
	return result1305
}

func (p *Parser) parse_export_iceberg_column() *pb.ExportIcebergColumn {
	span_start1308 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_column")
	string1306 := p.consumeTerminal("STRING").Value.str
	_t2057 := p.parse_boolean_value()
	boolean_value1307 := _t2057
	p.consumeLiteral(")")
	_t2058 := &pb.ExportIcebergColumn{Name: string1306, Nullable: boolean_value1307}
	result1309 := _t2058
	p.recordSpan(int(span_start1308), "ExportIcebergColumn")
	return result1309
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
