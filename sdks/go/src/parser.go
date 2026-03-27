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
	var _t2062 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2062
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2063 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2063
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2064 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2064
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2065 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2065
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2066 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2066
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2067 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2067
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2068 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2068
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2069 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2069
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2070 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2070
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2071 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2071
	_t2072 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2072
	_t2073 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2073
	_t2074 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2074
	_t2075 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2075
	_t2076 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2076
	_t2077 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2077
	_t2078 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2078
	_t2079 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2079
	_t2080 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2080
	_t2081 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2081
	_t2082 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2082
	_t2083 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2083
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2084 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2084
	_t2085 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2085
	_t2086 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2086
	_t2087 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2087
	_t2088 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2088
	_t2089 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2089
	_t2090 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2090
	_t2091 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2091
	_t2092 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2092
	_t2093 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2093.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2093.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2093
	_t2094 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2094
}

func (p *Parser) default_configure() *pb.Configure {
	_t2095 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2095
	_t2096 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2096
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
	_t2097 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2097
	_t2098 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2098
	_t2099 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2099
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2100 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2100
	_t2101 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2101
	_t2102 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2102
	_t2103 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2103
	_t2104 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2104
	_t2105 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2105
	_t2106 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2106
	_t2107 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2107
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2108 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2108
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2109 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2109
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.ExportIcebergColumn, create_table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2110 := config_dict
	if config_dict == nil {
		_t2110 = [][]interface{}{}
	}
	cfg := dictFromList(_t2110)
	_t2111 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2111
	_t2112 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2112
	_t2113 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2113
	create_table_props := stringMapFromPairs(create_table_property_pairs)
	_t2114 := &pb.ExportIcebergConfig{Locator: locator, Config: config, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, CreateTableProperties: create_table_props}
	return _t2114
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start662 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1312 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1313 := p.parse_configure()
		_t1312 = _t1313
	}
	configure656 := _t1312
	var _t1314 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1315 := p.parse_sync()
		_t1314 = _t1315
	}
	sync657 := _t1314
	xs658 := []*pb.Epoch{}
	cond659 := p.matchLookaheadLiteral("(", 0)
	for cond659 {
		_t1316 := p.parse_epoch()
		item660 := _t1316
		xs658 = append(xs658, item660)
		cond659 = p.matchLookaheadLiteral("(", 0)
	}
	epochs661 := xs658
	p.consumeLiteral(")")
	_t1317 := p.default_configure()
	_t1318 := configure656
	if configure656 == nil {
		_t1318 = _t1317
	}
	_t1319 := &pb.Transaction{Epochs: epochs661, Configure: _t1318, Sync: sync657}
	result663 := _t1319
	p.recordSpan(int(span_start662), "Transaction")
	return result663
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start665 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1320 := p.parse_config_dict()
	config_dict664 := _t1320
	p.consumeLiteral(")")
	_t1321 := p.construct_configure(config_dict664)
	result666 := _t1321
	p.recordSpan(int(span_start665), "Configure")
	return result666
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs667 := [][]interface{}{}
	cond668 := p.matchLookaheadLiteral(":", 0)
	for cond668 {
		_t1322 := p.parse_config_key_value()
		item669 := _t1322
		xs667 = append(xs667, item669)
		cond668 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values670 := xs667
	p.consumeLiteral("}")
	return config_key_values670
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol671 := p.consumeTerminal("SYMBOL").Value.str
	_t1323 := p.parse_raw_value()
	raw_value672 := _t1323
	return []interface{}{symbol671, raw_value672}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start686 := int64(p.spanStart())
	var _t1324 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1324 = 12
	} else {
		var _t1325 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1325 = 11
		} else {
			var _t1326 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1326 = 12
			} else {
				var _t1327 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1328 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1328 = 1
					} else {
						var _t1329 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1329 = 0
						} else {
							_t1329 = -1
						}
						_t1328 = _t1329
					}
					_t1327 = _t1328
				} else {
					var _t1330 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1330 = 7
					} else {
						var _t1331 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1331 = 8
						} else {
							var _t1332 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1332 = 2
							} else {
								var _t1333 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1333 = 3
								} else {
									var _t1334 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1334 = 9
									} else {
										var _t1335 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1335 = 4
										} else {
											var _t1336 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1336 = 5
											} else {
												var _t1337 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1337 = 6
												} else {
													var _t1338 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1338 = 10
													} else {
														_t1338 = -1
													}
													_t1337 = _t1338
												}
												_t1336 = _t1337
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
					_t1327 = _t1330
				}
				_t1326 = _t1327
			}
			_t1325 = _t1326
		}
		_t1324 = _t1325
	}
	prediction673 := _t1324
	var _t1339 *pb.Value
	if prediction673 == 12 {
		_t1340 := p.parse_boolean_value()
		boolean_value685 := _t1340
		_t1341 := &pb.Value{}
		_t1341.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value685}
		_t1339 = _t1341
	} else {
		var _t1342 *pb.Value
		if prediction673 == 11 {
			p.consumeLiteral("missing")
			_t1343 := &pb.MissingValue{}
			_t1344 := &pb.Value{}
			_t1344.Value = &pb.Value_MissingValue{MissingValue: _t1343}
			_t1342 = _t1344
		} else {
			var _t1345 *pb.Value
			if prediction673 == 10 {
				decimal684 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1346 := &pb.Value{}
				_t1346.Value = &pb.Value_DecimalValue{DecimalValue: decimal684}
				_t1345 = _t1346
			} else {
				var _t1347 *pb.Value
				if prediction673 == 9 {
					int128683 := p.consumeTerminal("INT128").Value.int128
					_t1348 := &pb.Value{}
					_t1348.Value = &pb.Value_Int128Value{Int128Value: int128683}
					_t1347 = _t1348
				} else {
					var _t1349 *pb.Value
					if prediction673 == 8 {
						uint128682 := p.consumeTerminal("UINT128").Value.uint128
						_t1350 := &pb.Value{}
						_t1350.Value = &pb.Value_Uint128Value{Uint128Value: uint128682}
						_t1349 = _t1350
					} else {
						var _t1351 *pb.Value
						if prediction673 == 7 {
							uint32681 := p.consumeTerminal("UINT32").Value.u32
							_t1352 := &pb.Value{}
							_t1352.Value = &pb.Value_Uint32Value{Uint32Value: uint32681}
							_t1351 = _t1352
						} else {
							var _t1353 *pb.Value
							if prediction673 == 6 {
								float680 := p.consumeTerminal("FLOAT").Value.f64
								_t1354 := &pb.Value{}
								_t1354.Value = &pb.Value_FloatValue{FloatValue: float680}
								_t1353 = _t1354
							} else {
								var _t1355 *pb.Value
								if prediction673 == 5 {
									float32679 := p.consumeTerminal("FLOAT32").Value.f32
									_t1356 := &pb.Value{}
									_t1356.Value = &pb.Value_Float32Value{Float32Value: float32679}
									_t1355 = _t1356
								} else {
									var _t1357 *pb.Value
									if prediction673 == 4 {
										int678 := p.consumeTerminal("INT").Value.i64
										_t1358 := &pb.Value{}
										_t1358.Value = &pb.Value_IntValue{IntValue: int678}
										_t1357 = _t1358
									} else {
										var _t1359 *pb.Value
										if prediction673 == 3 {
											int32677 := p.consumeTerminal("INT32").Value.i32
											_t1360 := &pb.Value{}
											_t1360.Value = &pb.Value_Int32Value{Int32Value: int32677}
											_t1359 = _t1360
										} else {
											var _t1361 *pb.Value
											if prediction673 == 2 {
												string676 := p.consumeTerminal("STRING").Value.str
												_t1362 := &pb.Value{}
												_t1362.Value = &pb.Value_StringValue{StringValue: string676}
												_t1361 = _t1362
											} else {
												var _t1363 *pb.Value
												if prediction673 == 1 {
													_t1364 := p.parse_raw_datetime()
													raw_datetime675 := _t1364
													_t1365 := &pb.Value{}
													_t1365.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime675}
													_t1363 = _t1365
												} else {
													var _t1366 *pb.Value
													if prediction673 == 0 {
														_t1367 := p.parse_raw_date()
														raw_date674 := _t1367
														_t1368 := &pb.Value{}
														_t1368.Value = &pb.Value_DateValue{DateValue: raw_date674}
														_t1366 = _t1368
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1363 = _t1366
												}
												_t1361 = _t1363
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
			_t1342 = _t1345
		}
		_t1339 = _t1342
	}
	result687 := _t1339
	p.recordSpan(int(span_start686), "Value")
	return result687
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start691 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int688 := p.consumeTerminal("INT").Value.i64
	int_3689 := p.consumeTerminal("INT").Value.i64
	int_4690 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1369 := &pb.DateValue{Year: int32(int688), Month: int32(int_3689), Day: int32(int_4690)}
	result692 := _t1369
	p.recordSpan(int(span_start691), "DateValue")
	return result692
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start700 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int693 := p.consumeTerminal("INT").Value.i64
	int_3694 := p.consumeTerminal("INT").Value.i64
	int_4695 := p.consumeTerminal("INT").Value.i64
	int_5696 := p.consumeTerminal("INT").Value.i64
	int_6697 := p.consumeTerminal("INT").Value.i64
	int_7698 := p.consumeTerminal("INT").Value.i64
	var _t1370 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1370 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8699 := _t1370
	p.consumeLiteral(")")
	_t1371 := &pb.DateTimeValue{Year: int32(int693), Month: int32(int_3694), Day: int32(int_4695), Hour: int32(int_5696), Minute: int32(int_6697), Second: int32(int_7698), Microsecond: int32(deref(int_8699, 0))}
	result701 := _t1371
	p.recordSpan(int(span_start700), "DateTimeValue")
	return result701
}

func (p *Parser) parse_boolean_value() bool {
	var _t1372 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1372 = 0
	} else {
		var _t1373 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1373 = 1
		} else {
			_t1373 = -1
		}
		_t1372 = _t1373
	}
	prediction702 := _t1372
	var _t1374 bool
	if prediction702 == 1 {
		p.consumeLiteral("false")
		_t1374 = false
	} else {
		var _t1375 bool
		if prediction702 == 0 {
			p.consumeLiteral("true")
			_t1375 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1374 = _t1375
	}
	return _t1374
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs703 := []*pb.FragmentId{}
	cond704 := p.matchLookaheadLiteral(":", 0)
	for cond704 {
		_t1376 := p.parse_fragment_id()
		item705 := _t1376
		xs703 = append(xs703, item705)
		cond704 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids706 := xs703
	p.consumeLiteral(")")
	_t1377 := &pb.Sync{Fragments: fragment_ids706}
	result708 := _t1377
	p.recordSpan(int(span_start707), "Sync")
	return result708
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start710 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol709 := p.consumeTerminal("SYMBOL").Value.str
	result711 := &pb.FragmentId{Id: []byte(symbol709)}
	p.recordSpan(int(span_start710), "FragmentId")
	return result711
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start714 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1378 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1379 := p.parse_epoch_writes()
		_t1378 = _t1379
	}
	epoch_writes712 := _t1378
	var _t1380 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1381 := p.parse_epoch_reads()
		_t1380 = _t1381
	}
	epoch_reads713 := _t1380
	p.consumeLiteral(")")
	_t1382 := epoch_writes712
	if epoch_writes712 == nil {
		_t1382 = []*pb.Write{}
	}
	_t1383 := epoch_reads713
	if epoch_reads713 == nil {
		_t1383 = []*pb.Read{}
	}
	_t1384 := &pb.Epoch{Writes: _t1382, Reads: _t1383}
	result715 := _t1384
	p.recordSpan(int(span_start714), "Epoch")
	return result715
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs716 := []*pb.Write{}
	cond717 := p.matchLookaheadLiteral("(", 0)
	for cond717 {
		_t1385 := p.parse_write()
		item718 := _t1385
		xs716 = append(xs716, item718)
		cond717 = p.matchLookaheadLiteral("(", 0)
	}
	writes719 := xs716
	p.consumeLiteral(")")
	return writes719
}

func (p *Parser) parse_write() *pb.Write {
	span_start725 := int64(p.spanStart())
	var _t1386 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1387 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1387 = 1
		} else {
			var _t1388 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1388 = 3
			} else {
				var _t1389 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1389 = 0
				} else {
					var _t1390 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1390 = 2
					} else {
						_t1390 = -1
					}
					_t1389 = _t1390
				}
				_t1388 = _t1389
			}
			_t1387 = _t1388
		}
		_t1386 = _t1387
	} else {
		_t1386 = -1
	}
	prediction720 := _t1386
	var _t1391 *pb.Write
	if prediction720 == 3 {
		_t1392 := p.parse_snapshot()
		snapshot724 := _t1392
		_t1393 := &pb.Write{}
		_t1393.WriteType = &pb.Write_Snapshot{Snapshot: snapshot724}
		_t1391 = _t1393
	} else {
		var _t1394 *pb.Write
		if prediction720 == 2 {
			_t1395 := p.parse_context()
			context723 := _t1395
			_t1396 := &pb.Write{}
			_t1396.WriteType = &pb.Write_Context{Context: context723}
			_t1394 = _t1396
		} else {
			var _t1397 *pb.Write
			if prediction720 == 1 {
				_t1398 := p.parse_undefine()
				undefine722 := _t1398
				_t1399 := &pb.Write{}
				_t1399.WriteType = &pb.Write_Undefine{Undefine: undefine722}
				_t1397 = _t1399
			} else {
				var _t1400 *pb.Write
				if prediction720 == 0 {
					_t1401 := p.parse_define()
					define721 := _t1401
					_t1402 := &pb.Write{}
					_t1402.WriteType = &pb.Write_Define{Define: define721}
					_t1400 = _t1402
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1397 = _t1400
			}
			_t1394 = _t1397
		}
		_t1391 = _t1394
	}
	result726 := _t1391
	p.recordSpan(int(span_start725), "Write")
	return result726
}

func (p *Parser) parse_define() *pb.Define {
	span_start728 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1403 := p.parse_fragment()
	fragment727 := _t1403
	p.consumeLiteral(")")
	_t1404 := &pb.Define{Fragment: fragment727}
	result729 := _t1404
	p.recordSpan(int(span_start728), "Define")
	return result729
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1405 := p.parse_new_fragment_id()
	new_fragment_id730 := _t1405
	xs731 := []*pb.Declaration{}
	cond732 := p.matchLookaheadLiteral("(", 0)
	for cond732 {
		_t1406 := p.parse_declaration()
		item733 := _t1406
		xs731 = append(xs731, item733)
		cond732 = p.matchLookaheadLiteral("(", 0)
	}
	declarations734 := xs731
	p.consumeLiteral(")")
	result736 := p.constructFragment(new_fragment_id730, declarations734)
	p.recordSpan(int(span_start735), "Fragment")
	return result736
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start738 := int64(p.spanStart())
	_t1407 := p.parse_fragment_id()
	fragment_id737 := _t1407
	p.startFragment(fragment_id737)
	result739 := fragment_id737
	p.recordSpan(int(span_start738), "FragmentId")
	return result739
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start745 := int64(p.spanStart())
	var _t1408 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1409 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1409 = 3
		} else {
			var _t1410 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1410 = 2
			} else {
				var _t1411 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1411 = 3
				} else {
					var _t1412 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1412 = 0
					} else {
						var _t1413 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1413 = 3
						} else {
							var _t1414 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1414 = 3
							} else {
								var _t1415 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1415 = 1
								} else {
									_t1415 = -1
								}
								_t1414 = _t1415
							}
							_t1413 = _t1414
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
	} else {
		_t1408 = -1
	}
	prediction740 := _t1408
	var _t1416 *pb.Declaration
	if prediction740 == 3 {
		_t1417 := p.parse_data()
		data744 := _t1417
		_t1418 := &pb.Declaration{}
		_t1418.DeclarationType = &pb.Declaration_Data{Data: data744}
		_t1416 = _t1418
	} else {
		var _t1419 *pb.Declaration
		if prediction740 == 2 {
			_t1420 := p.parse_constraint()
			constraint743 := _t1420
			_t1421 := &pb.Declaration{}
			_t1421.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint743}
			_t1419 = _t1421
		} else {
			var _t1422 *pb.Declaration
			if prediction740 == 1 {
				_t1423 := p.parse_algorithm()
				algorithm742 := _t1423
				_t1424 := &pb.Declaration{}
				_t1424.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm742}
				_t1422 = _t1424
			} else {
				var _t1425 *pb.Declaration
				if prediction740 == 0 {
					_t1426 := p.parse_def()
					def741 := _t1426
					_t1427 := &pb.Declaration{}
					_t1427.DeclarationType = &pb.Declaration_Def{Def: def741}
					_t1425 = _t1427
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1422 = _t1425
			}
			_t1419 = _t1422
		}
		_t1416 = _t1419
	}
	result746 := _t1416
	p.recordSpan(int(span_start745), "Declaration")
	return result746
}

func (p *Parser) parse_def() *pb.Def {
	span_start750 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1428 := p.parse_relation_id()
	relation_id747 := _t1428
	_t1429 := p.parse_abstraction()
	abstraction748 := _t1429
	var _t1430 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1431 := p.parse_attrs()
		_t1430 = _t1431
	}
	attrs749 := _t1430
	p.consumeLiteral(")")
	_t1432 := attrs749
	if attrs749 == nil {
		_t1432 = []*pb.Attribute{}
	}
	_t1433 := &pb.Def{Name: relation_id747, Body: abstraction748, Attrs: _t1432}
	result751 := _t1433
	p.recordSpan(int(span_start750), "Def")
	return result751
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start755 := int64(p.spanStart())
	var _t1434 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1434 = 0
	} else {
		var _t1435 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1435 = 1
		} else {
			_t1435 = -1
		}
		_t1434 = _t1435
	}
	prediction752 := _t1434
	var _t1436 *pb.RelationId
	if prediction752 == 1 {
		uint128754 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128754
		_t1436 = &pb.RelationId{IdLow: uint128754.Low, IdHigh: uint128754.High}
	} else {
		var _t1437 *pb.RelationId
		if prediction752 == 0 {
			p.consumeLiteral(":")
			symbol753 := p.consumeTerminal("SYMBOL").Value.str
			_t1437 = p.relationIdFromString(symbol753)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1436 = _t1437
	}
	result756 := _t1436
	p.recordSpan(int(span_start755), "RelationId")
	return result756
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1438 := p.parse_bindings()
	bindings757 := _t1438
	_t1439 := p.parse_formula()
	formula758 := _t1439
	p.consumeLiteral(")")
	_t1440 := &pb.Abstraction{Vars: listConcat(bindings757[0].([]*pb.Binding), bindings757[1].([]*pb.Binding)), Value: formula758}
	result760 := _t1440
	p.recordSpan(int(span_start759), "Abstraction")
	return result760
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs761 := []*pb.Binding{}
	cond762 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond762 {
		_t1441 := p.parse_binding()
		item763 := _t1441
		xs761 = append(xs761, item763)
		cond762 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings764 := xs761
	var _t1442 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1443 := p.parse_value_bindings()
		_t1442 = _t1443
	}
	value_bindings765 := _t1442
	p.consumeLiteral("]")
	_t1444 := value_bindings765
	if value_bindings765 == nil {
		_t1444 = []*pb.Binding{}
	}
	return []interface{}{bindings764, _t1444}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start768 := int64(p.spanStart())
	symbol766 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1445 := p.parse_type()
	type767 := _t1445
	_t1446 := &pb.Var{Name: symbol766}
	_t1447 := &pb.Binding{Var: _t1446, Type: type767}
	result769 := _t1447
	p.recordSpan(int(span_start768), "Binding")
	return result769
}

func (p *Parser) parse_type() *pb.Type {
	span_start785 := int64(p.spanStart())
	var _t1448 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1448 = 0
	} else {
		var _t1449 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1449 = 13
		} else {
			var _t1450 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1450 = 4
			} else {
				var _t1451 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1451 = 1
				} else {
					var _t1452 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1452 = 8
					} else {
						var _t1453 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1453 = 11
						} else {
							var _t1454 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1454 = 5
							} else {
								var _t1455 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1455 = 2
								} else {
									var _t1456 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1456 = 12
									} else {
										var _t1457 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1457 = 3
										} else {
											var _t1458 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1458 = 7
											} else {
												var _t1459 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1459 = 6
												} else {
													var _t1460 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1460 = 10
													} else {
														var _t1461 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1461 = 9
														} else {
															_t1461 = -1
														}
														_t1460 = _t1461
													}
													_t1459 = _t1460
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
	prediction770 := _t1448
	var _t1462 *pb.Type
	if prediction770 == 13 {
		_t1463 := p.parse_uint32_type()
		uint32_type784 := _t1463
		_t1464 := &pb.Type{}
		_t1464.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type784}
		_t1462 = _t1464
	} else {
		var _t1465 *pb.Type
		if prediction770 == 12 {
			_t1466 := p.parse_float32_type()
			float32_type783 := _t1466
			_t1467 := &pb.Type{}
			_t1467.Type = &pb.Type_Float32Type{Float32Type: float32_type783}
			_t1465 = _t1467
		} else {
			var _t1468 *pb.Type
			if prediction770 == 11 {
				_t1469 := p.parse_int32_type()
				int32_type782 := _t1469
				_t1470 := &pb.Type{}
				_t1470.Type = &pb.Type_Int32Type{Int32Type: int32_type782}
				_t1468 = _t1470
			} else {
				var _t1471 *pb.Type
				if prediction770 == 10 {
					_t1472 := p.parse_boolean_type()
					boolean_type781 := _t1472
					_t1473 := &pb.Type{}
					_t1473.Type = &pb.Type_BooleanType{BooleanType: boolean_type781}
					_t1471 = _t1473
				} else {
					var _t1474 *pb.Type
					if prediction770 == 9 {
						_t1475 := p.parse_decimal_type()
						decimal_type780 := _t1475
						_t1476 := &pb.Type{}
						_t1476.Type = &pb.Type_DecimalType{DecimalType: decimal_type780}
						_t1474 = _t1476
					} else {
						var _t1477 *pb.Type
						if prediction770 == 8 {
							_t1478 := p.parse_missing_type()
							missing_type779 := _t1478
							_t1479 := &pb.Type{}
							_t1479.Type = &pb.Type_MissingType{MissingType: missing_type779}
							_t1477 = _t1479
						} else {
							var _t1480 *pb.Type
							if prediction770 == 7 {
								_t1481 := p.parse_datetime_type()
								datetime_type778 := _t1481
								_t1482 := &pb.Type{}
								_t1482.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type778}
								_t1480 = _t1482
							} else {
								var _t1483 *pb.Type
								if prediction770 == 6 {
									_t1484 := p.parse_date_type()
									date_type777 := _t1484
									_t1485 := &pb.Type{}
									_t1485.Type = &pb.Type_DateType{DateType: date_type777}
									_t1483 = _t1485
								} else {
									var _t1486 *pb.Type
									if prediction770 == 5 {
										_t1487 := p.parse_int128_type()
										int128_type776 := _t1487
										_t1488 := &pb.Type{}
										_t1488.Type = &pb.Type_Int128Type{Int128Type: int128_type776}
										_t1486 = _t1488
									} else {
										var _t1489 *pb.Type
										if prediction770 == 4 {
											_t1490 := p.parse_uint128_type()
											uint128_type775 := _t1490
											_t1491 := &pb.Type{}
											_t1491.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type775}
											_t1489 = _t1491
										} else {
											var _t1492 *pb.Type
											if prediction770 == 3 {
												_t1493 := p.parse_float_type()
												float_type774 := _t1493
												_t1494 := &pb.Type{}
												_t1494.Type = &pb.Type_FloatType{FloatType: float_type774}
												_t1492 = _t1494
											} else {
												var _t1495 *pb.Type
												if prediction770 == 2 {
													_t1496 := p.parse_int_type()
													int_type773 := _t1496
													_t1497 := &pb.Type{}
													_t1497.Type = &pb.Type_IntType{IntType: int_type773}
													_t1495 = _t1497
												} else {
													var _t1498 *pb.Type
													if prediction770 == 1 {
														_t1499 := p.parse_string_type()
														string_type772 := _t1499
														_t1500 := &pb.Type{}
														_t1500.Type = &pb.Type_StringType{StringType: string_type772}
														_t1498 = _t1500
													} else {
														var _t1501 *pb.Type
														if prediction770 == 0 {
															_t1502 := p.parse_unspecified_type()
															unspecified_type771 := _t1502
															_t1503 := &pb.Type{}
															_t1503.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type771}
															_t1501 = _t1503
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1498 = _t1501
													}
													_t1495 = _t1498
												}
												_t1492 = _t1495
											}
											_t1489 = _t1492
										}
										_t1486 = _t1489
									}
									_t1483 = _t1486
								}
								_t1480 = _t1483
							}
							_t1477 = _t1480
						}
						_t1474 = _t1477
					}
					_t1471 = _t1474
				}
				_t1468 = _t1471
			}
			_t1465 = _t1468
		}
		_t1462 = _t1465
	}
	result786 := _t1462
	p.recordSpan(int(span_start785), "Type")
	return result786
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start787 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1504 := &pb.UnspecifiedType{}
	result788 := _t1504
	p.recordSpan(int(span_start787), "UnspecifiedType")
	return result788
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start789 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1505 := &pb.StringType{}
	result790 := _t1505
	p.recordSpan(int(span_start789), "StringType")
	return result790
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1506 := &pb.IntType{}
	result792 := _t1506
	p.recordSpan(int(span_start791), "IntType")
	return result792
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start793 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1507 := &pb.FloatType{}
	result794 := _t1507
	p.recordSpan(int(span_start793), "FloatType")
	return result794
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start795 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1508 := &pb.UInt128Type{}
	result796 := _t1508
	p.recordSpan(int(span_start795), "UInt128Type")
	return result796
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1509 := &pb.Int128Type{}
	result798 := _t1509
	p.recordSpan(int(span_start797), "Int128Type")
	return result798
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start799 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1510 := &pb.DateType{}
	result800 := _t1510
	p.recordSpan(int(span_start799), "DateType")
	return result800
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1511 := &pb.DateTimeType{}
	result802 := _t1511
	p.recordSpan(int(span_start801), "DateTimeType")
	return result802
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1512 := &pb.MissingType{}
	result804 := _t1512
	p.recordSpan(int(span_start803), "MissingType")
	return result804
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int805 := p.consumeTerminal("INT").Value.i64
	int_3806 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1513 := &pb.DecimalType{Precision: int32(int805), Scale: int32(int_3806)}
	result808 := _t1513
	p.recordSpan(int(span_start807), "DecimalType")
	return result808
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1514 := &pb.BooleanType{}
	result810 := _t1514
	p.recordSpan(int(span_start809), "BooleanType")
	return result810
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1515 := &pb.Int32Type{}
	result812 := _t1515
	p.recordSpan(int(span_start811), "Int32Type")
	return result812
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1516 := &pb.Float32Type{}
	result814 := _t1516
	p.recordSpan(int(span_start813), "Float32Type")
	return result814
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1517 := &pb.UInt32Type{}
	result816 := _t1517
	p.recordSpan(int(span_start815), "UInt32Type")
	return result816
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs817 := []*pb.Binding{}
	cond818 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond818 {
		_t1518 := p.parse_binding()
		item819 := _t1518
		xs817 = append(xs817, item819)
		cond818 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings820 := xs817
	return bindings820
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start835 := int64(p.spanStart())
	var _t1519 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1520 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1520 = 0
		} else {
			var _t1521 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1521 = 11
			} else {
				var _t1522 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1522 = 3
				} else {
					var _t1523 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1523 = 10
					} else {
						var _t1524 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1524 = 9
						} else {
							var _t1525 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1525 = 5
							} else {
								var _t1526 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1526 = 6
								} else {
									var _t1527 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1527 = 7
									} else {
										var _t1528 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1528 = 1
										} else {
											var _t1529 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1529 = 2
											} else {
												var _t1530 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1530 = 12
												} else {
													var _t1531 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1531 = 8
													} else {
														var _t1532 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1532 = 4
														} else {
															var _t1533 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1533 = 10
															} else {
																var _t1534 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1534 = 10
																} else {
																	var _t1535 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1535 = 10
																	} else {
																		var _t1536 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1536 = 10
																		} else {
																			var _t1537 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1537 = 10
																			} else {
																				var _t1538 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1538 = 10
																				} else {
																					var _t1539 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1539 = 10
																					} else {
																						var _t1540 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1540 = 10
																						} else {
																							var _t1541 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1541 = 10
																							} else {
																								_t1541 = -1
																							}
																							_t1540 = _t1541
																						}
																						_t1539 = _t1540
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
	} else {
		_t1519 = -1
	}
	prediction821 := _t1519
	var _t1542 *pb.Formula
	if prediction821 == 12 {
		_t1543 := p.parse_cast()
		cast834 := _t1543
		_t1544 := &pb.Formula{}
		_t1544.FormulaType = &pb.Formula_Cast{Cast: cast834}
		_t1542 = _t1544
	} else {
		var _t1545 *pb.Formula
		if prediction821 == 11 {
			_t1546 := p.parse_rel_atom()
			rel_atom833 := _t1546
			_t1547 := &pb.Formula{}
			_t1547.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom833}
			_t1545 = _t1547
		} else {
			var _t1548 *pb.Formula
			if prediction821 == 10 {
				_t1549 := p.parse_primitive()
				primitive832 := _t1549
				_t1550 := &pb.Formula{}
				_t1550.FormulaType = &pb.Formula_Primitive{Primitive: primitive832}
				_t1548 = _t1550
			} else {
				var _t1551 *pb.Formula
				if prediction821 == 9 {
					_t1552 := p.parse_pragma()
					pragma831 := _t1552
					_t1553 := &pb.Formula{}
					_t1553.FormulaType = &pb.Formula_Pragma{Pragma: pragma831}
					_t1551 = _t1553
				} else {
					var _t1554 *pb.Formula
					if prediction821 == 8 {
						_t1555 := p.parse_atom()
						atom830 := _t1555
						_t1556 := &pb.Formula{}
						_t1556.FormulaType = &pb.Formula_Atom{Atom: atom830}
						_t1554 = _t1556
					} else {
						var _t1557 *pb.Formula
						if prediction821 == 7 {
							_t1558 := p.parse_ffi()
							ffi829 := _t1558
							_t1559 := &pb.Formula{}
							_t1559.FormulaType = &pb.Formula_Ffi{Ffi: ffi829}
							_t1557 = _t1559
						} else {
							var _t1560 *pb.Formula
							if prediction821 == 6 {
								_t1561 := p.parse_not()
								not828 := _t1561
								_t1562 := &pb.Formula{}
								_t1562.FormulaType = &pb.Formula_Not{Not: not828}
								_t1560 = _t1562
							} else {
								var _t1563 *pb.Formula
								if prediction821 == 5 {
									_t1564 := p.parse_disjunction()
									disjunction827 := _t1564
									_t1565 := &pb.Formula{}
									_t1565.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction827}
									_t1563 = _t1565
								} else {
									var _t1566 *pb.Formula
									if prediction821 == 4 {
										_t1567 := p.parse_conjunction()
										conjunction826 := _t1567
										_t1568 := &pb.Formula{}
										_t1568.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction826}
										_t1566 = _t1568
									} else {
										var _t1569 *pb.Formula
										if prediction821 == 3 {
											_t1570 := p.parse_reduce()
											reduce825 := _t1570
											_t1571 := &pb.Formula{}
											_t1571.FormulaType = &pb.Formula_Reduce{Reduce: reduce825}
											_t1569 = _t1571
										} else {
											var _t1572 *pb.Formula
											if prediction821 == 2 {
												_t1573 := p.parse_exists()
												exists824 := _t1573
												_t1574 := &pb.Formula{}
												_t1574.FormulaType = &pb.Formula_Exists{Exists: exists824}
												_t1572 = _t1574
											} else {
												var _t1575 *pb.Formula
												if prediction821 == 1 {
													_t1576 := p.parse_false()
													false823 := _t1576
													_t1577 := &pb.Formula{}
													_t1577.FormulaType = &pb.Formula_Disjunction{Disjunction: false823}
													_t1575 = _t1577
												} else {
													var _t1578 *pb.Formula
													if prediction821 == 0 {
														_t1579 := p.parse_true()
														true822 := _t1579
														_t1580 := &pb.Formula{}
														_t1580.FormulaType = &pb.Formula_Conjunction{Conjunction: true822}
														_t1578 = _t1580
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1575 = _t1578
												}
												_t1572 = _t1575
											}
											_t1569 = _t1572
										}
										_t1566 = _t1569
									}
									_t1563 = _t1566
								}
								_t1560 = _t1563
							}
							_t1557 = _t1560
						}
						_t1554 = _t1557
					}
					_t1551 = _t1554
				}
				_t1548 = _t1551
			}
			_t1545 = _t1548
		}
		_t1542 = _t1545
	}
	result836 := _t1542
	p.recordSpan(int(span_start835), "Formula")
	return result836
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1581 := &pb.Conjunction{Args: []*pb.Formula{}}
	result838 := _t1581
	p.recordSpan(int(span_start837), "Conjunction")
	return result838
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1582 := &pb.Disjunction{Args: []*pb.Formula{}}
	result840 := _t1582
	p.recordSpan(int(span_start839), "Disjunction")
	return result840
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1583 := p.parse_bindings()
	bindings841 := _t1583
	_t1584 := p.parse_formula()
	formula842 := _t1584
	p.consumeLiteral(")")
	_t1585 := &pb.Abstraction{Vars: listConcat(bindings841[0].([]*pb.Binding), bindings841[1].([]*pb.Binding)), Value: formula842}
	_t1586 := &pb.Exists{Body: _t1585}
	result844 := _t1586
	p.recordSpan(int(span_start843), "Exists")
	return result844
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1587 := p.parse_abstraction()
	abstraction845 := _t1587
	_t1588 := p.parse_abstraction()
	abstraction_3846 := _t1588
	_t1589 := p.parse_terms()
	terms847 := _t1589
	p.consumeLiteral(")")
	_t1590 := &pb.Reduce{Op: abstraction845, Body: abstraction_3846, Terms: terms847}
	result849 := _t1590
	p.recordSpan(int(span_start848), "Reduce")
	return result849
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs850 := []*pb.Term{}
	cond851 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond851 {
		_t1591 := p.parse_term()
		item852 := _t1591
		xs850 = append(xs850, item852)
		cond851 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms853 := xs850
	p.consumeLiteral(")")
	return terms853
}

func (p *Parser) parse_term() *pb.Term {
	span_start857 := int64(p.spanStart())
	var _t1592 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1592 = 1
	} else {
		var _t1593 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1593 = 1
		} else {
			var _t1594 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1594 = 1
			} else {
				var _t1595 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1595 = 1
				} else {
					var _t1596 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1596 = 0
					} else {
						var _t1597 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1597 = 1
						} else {
							var _t1598 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1598 = 1
							} else {
								var _t1599 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1599 = 1
								} else {
									var _t1600 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1600 = 1
									} else {
										var _t1601 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1601 = 1
										} else {
											var _t1602 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1602 = 1
											} else {
												var _t1603 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1603 = 1
												} else {
													var _t1604 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1604 = 1
													} else {
														var _t1605 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1605 = 1
														} else {
															_t1605 = -1
														}
														_t1604 = _t1605
													}
													_t1603 = _t1604
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
	prediction854 := _t1592
	var _t1606 *pb.Term
	if prediction854 == 1 {
		_t1607 := p.parse_value()
		value856 := _t1607
		_t1608 := &pb.Term{}
		_t1608.TermType = &pb.Term_Constant{Constant: value856}
		_t1606 = _t1608
	} else {
		var _t1609 *pb.Term
		if prediction854 == 0 {
			_t1610 := p.parse_var()
			var855 := _t1610
			_t1611 := &pb.Term{}
			_t1611.TermType = &pb.Term_Var{Var: var855}
			_t1609 = _t1611
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1606 = _t1609
	}
	result858 := _t1606
	p.recordSpan(int(span_start857), "Term")
	return result858
}

func (p *Parser) parse_var() *pb.Var {
	span_start860 := int64(p.spanStart())
	symbol859 := p.consumeTerminal("SYMBOL").Value.str
	_t1612 := &pb.Var{Name: symbol859}
	result861 := _t1612
	p.recordSpan(int(span_start860), "Var")
	return result861
}

func (p *Parser) parse_value() *pb.Value {
	span_start875 := int64(p.spanStart())
	var _t1613 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1613 = 12
	} else {
		var _t1614 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1614 = 11
		} else {
			var _t1615 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1615 = 12
			} else {
				var _t1616 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1617 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1617 = 1
					} else {
						var _t1618 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1618 = 0
						} else {
							_t1618 = -1
						}
						_t1617 = _t1618
					}
					_t1616 = _t1617
				} else {
					var _t1619 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1619 = 7
					} else {
						var _t1620 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1620 = 8
						} else {
							var _t1621 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1621 = 2
							} else {
								var _t1622 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1622 = 3
								} else {
									var _t1623 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1623 = 9
									} else {
										var _t1624 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1624 = 4
										} else {
											var _t1625 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1625 = 5
											} else {
												var _t1626 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1626 = 6
												} else {
													var _t1627 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1627 = 10
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
					_t1616 = _t1619
				}
				_t1615 = _t1616
			}
			_t1614 = _t1615
		}
		_t1613 = _t1614
	}
	prediction862 := _t1613
	var _t1628 *pb.Value
	if prediction862 == 12 {
		_t1629 := p.parse_boolean_value()
		boolean_value874 := _t1629
		_t1630 := &pb.Value{}
		_t1630.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value874}
		_t1628 = _t1630
	} else {
		var _t1631 *pb.Value
		if prediction862 == 11 {
			p.consumeLiteral("missing")
			_t1632 := &pb.MissingValue{}
			_t1633 := &pb.Value{}
			_t1633.Value = &pb.Value_MissingValue{MissingValue: _t1632}
			_t1631 = _t1633
		} else {
			var _t1634 *pb.Value
			if prediction862 == 10 {
				formatted_decimal873 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1635 := &pb.Value{}
				_t1635.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal873}
				_t1634 = _t1635
			} else {
				var _t1636 *pb.Value
				if prediction862 == 9 {
					formatted_int128872 := p.consumeTerminal("INT128").Value.int128
					_t1637 := &pb.Value{}
					_t1637.Value = &pb.Value_Int128Value{Int128Value: formatted_int128872}
					_t1636 = _t1637
				} else {
					var _t1638 *pb.Value
					if prediction862 == 8 {
						formatted_uint128871 := p.consumeTerminal("UINT128").Value.uint128
						_t1639 := &pb.Value{}
						_t1639.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128871}
						_t1638 = _t1639
					} else {
						var _t1640 *pb.Value
						if prediction862 == 7 {
							formatted_uint32870 := p.consumeTerminal("UINT32").Value.u32
							_t1641 := &pb.Value{}
							_t1641.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32870}
							_t1640 = _t1641
						} else {
							var _t1642 *pb.Value
							if prediction862 == 6 {
								formatted_float869 := p.consumeTerminal("FLOAT").Value.f64
								_t1643 := &pb.Value{}
								_t1643.Value = &pb.Value_FloatValue{FloatValue: formatted_float869}
								_t1642 = _t1643
							} else {
								var _t1644 *pb.Value
								if prediction862 == 5 {
									formatted_float32868 := p.consumeTerminal("FLOAT32").Value.f32
									_t1645 := &pb.Value{}
									_t1645.Value = &pb.Value_Float32Value{Float32Value: formatted_float32868}
									_t1644 = _t1645
								} else {
									var _t1646 *pb.Value
									if prediction862 == 4 {
										formatted_int867 := p.consumeTerminal("INT").Value.i64
										_t1647 := &pb.Value{}
										_t1647.Value = &pb.Value_IntValue{IntValue: formatted_int867}
										_t1646 = _t1647
									} else {
										var _t1648 *pb.Value
										if prediction862 == 3 {
											formatted_int32866 := p.consumeTerminal("INT32").Value.i32
											_t1649 := &pb.Value{}
											_t1649.Value = &pb.Value_Int32Value{Int32Value: formatted_int32866}
											_t1648 = _t1649
										} else {
											var _t1650 *pb.Value
											if prediction862 == 2 {
												formatted_string865 := p.consumeTerminal("STRING").Value.str
												_t1651 := &pb.Value{}
												_t1651.Value = &pb.Value_StringValue{StringValue: formatted_string865}
												_t1650 = _t1651
											} else {
												var _t1652 *pb.Value
												if prediction862 == 1 {
													_t1653 := p.parse_datetime()
													datetime864 := _t1653
													_t1654 := &pb.Value{}
													_t1654.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime864}
													_t1652 = _t1654
												} else {
													var _t1655 *pb.Value
													if prediction862 == 0 {
														_t1656 := p.parse_date()
														date863 := _t1656
														_t1657 := &pb.Value{}
														_t1657.Value = &pb.Value_DateValue{DateValue: date863}
														_t1655 = _t1657
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1652 = _t1655
												}
												_t1650 = _t1652
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
			_t1631 = _t1634
		}
		_t1628 = _t1631
	}
	result876 := _t1628
	p.recordSpan(int(span_start875), "Value")
	return result876
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start880 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int877 := p.consumeTerminal("INT").Value.i64
	formatted_int_3878 := p.consumeTerminal("INT").Value.i64
	formatted_int_4879 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1658 := &pb.DateValue{Year: int32(formatted_int877), Month: int32(formatted_int_3878), Day: int32(formatted_int_4879)}
	result881 := _t1658
	p.recordSpan(int(span_start880), "DateValue")
	return result881
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start889 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int882 := p.consumeTerminal("INT").Value.i64
	formatted_int_3883 := p.consumeTerminal("INT").Value.i64
	formatted_int_4884 := p.consumeTerminal("INT").Value.i64
	formatted_int_5885 := p.consumeTerminal("INT").Value.i64
	formatted_int_6886 := p.consumeTerminal("INT").Value.i64
	formatted_int_7887 := p.consumeTerminal("INT").Value.i64
	var _t1659 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1659 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8888 := _t1659
	p.consumeLiteral(")")
	_t1660 := &pb.DateTimeValue{Year: int32(formatted_int882), Month: int32(formatted_int_3883), Day: int32(formatted_int_4884), Hour: int32(formatted_int_5885), Minute: int32(formatted_int_6886), Second: int32(formatted_int_7887), Microsecond: int32(deref(formatted_int_8888, 0))}
	result890 := _t1660
	p.recordSpan(int(span_start889), "DateTimeValue")
	return result890
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs891 := []*pb.Formula{}
	cond892 := p.matchLookaheadLiteral("(", 0)
	for cond892 {
		_t1661 := p.parse_formula()
		item893 := _t1661
		xs891 = append(xs891, item893)
		cond892 = p.matchLookaheadLiteral("(", 0)
	}
	formulas894 := xs891
	p.consumeLiteral(")")
	_t1662 := &pb.Conjunction{Args: formulas894}
	result896 := _t1662
	p.recordSpan(int(span_start895), "Conjunction")
	return result896
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs897 := []*pb.Formula{}
	cond898 := p.matchLookaheadLiteral("(", 0)
	for cond898 {
		_t1663 := p.parse_formula()
		item899 := _t1663
		xs897 = append(xs897, item899)
		cond898 = p.matchLookaheadLiteral("(", 0)
	}
	formulas900 := xs897
	p.consumeLiteral(")")
	_t1664 := &pb.Disjunction{Args: formulas900}
	result902 := _t1664
	p.recordSpan(int(span_start901), "Disjunction")
	return result902
}

func (p *Parser) parse_not() *pb.Not {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1665 := p.parse_formula()
	formula903 := _t1665
	p.consumeLiteral(")")
	_t1666 := &pb.Not{Arg: formula903}
	result905 := _t1666
	p.recordSpan(int(span_start904), "Not")
	return result905
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1667 := p.parse_name()
	name906 := _t1667
	_t1668 := p.parse_ffi_args()
	ffi_args907 := _t1668
	_t1669 := p.parse_terms()
	terms908 := _t1669
	p.consumeLiteral(")")
	_t1670 := &pb.FFI{Name: name906, Args: ffi_args907, Terms: terms908}
	result910 := _t1670
	p.recordSpan(int(span_start909), "FFI")
	return result910
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol911 := p.consumeTerminal("SYMBOL").Value.str
	return symbol911
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs912 := []*pb.Abstraction{}
	cond913 := p.matchLookaheadLiteral("(", 0)
	for cond913 {
		_t1671 := p.parse_abstraction()
		item914 := _t1671
		xs912 = append(xs912, item914)
		cond913 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions915 := xs912
	p.consumeLiteral(")")
	return abstractions915
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start921 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1672 := p.parse_relation_id()
	relation_id916 := _t1672
	xs917 := []*pb.Term{}
	cond918 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond918 {
		_t1673 := p.parse_term()
		item919 := _t1673
		xs917 = append(xs917, item919)
		cond918 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms920 := xs917
	p.consumeLiteral(")")
	_t1674 := &pb.Atom{Name: relation_id916, Terms: terms920}
	result922 := _t1674
	p.recordSpan(int(span_start921), "Atom")
	return result922
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start928 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1675 := p.parse_name()
	name923 := _t1675
	xs924 := []*pb.Term{}
	cond925 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond925 {
		_t1676 := p.parse_term()
		item926 := _t1676
		xs924 = append(xs924, item926)
		cond925 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms927 := xs924
	p.consumeLiteral(")")
	_t1677 := &pb.Pragma{Name: name923, Terms: terms927}
	result929 := _t1677
	p.recordSpan(int(span_start928), "Pragma")
	return result929
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start945 := int64(p.spanStart())
	var _t1678 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1679 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1679 = 9
		} else {
			var _t1680 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1680 = 4
			} else {
				var _t1681 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1681 = 3
				} else {
					var _t1682 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1682 = 0
					} else {
						var _t1683 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1683 = 2
						} else {
							var _t1684 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1684 = 1
							} else {
								var _t1685 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1685 = 8
								} else {
									var _t1686 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1686 = 6
									} else {
										var _t1687 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1687 = 5
										} else {
											var _t1688 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1688 = 7
											} else {
												_t1688 = -1
											}
											_t1687 = _t1688
										}
										_t1686 = _t1687
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
	} else {
		_t1678 = -1
	}
	prediction930 := _t1678
	var _t1689 *pb.Primitive
	if prediction930 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1690 := p.parse_name()
		name940 := _t1690
		xs941 := []*pb.RelTerm{}
		cond942 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond942 {
			_t1691 := p.parse_rel_term()
			item943 := _t1691
			xs941 = append(xs941, item943)
			cond942 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms944 := xs941
		p.consumeLiteral(")")
		_t1692 := &pb.Primitive{Name: name940, Terms: rel_terms944}
		_t1689 = _t1692
	} else {
		var _t1693 *pb.Primitive
		if prediction930 == 8 {
			_t1694 := p.parse_divide()
			divide939 := _t1694
			_t1693 = divide939
		} else {
			var _t1695 *pb.Primitive
			if prediction930 == 7 {
				_t1696 := p.parse_multiply()
				multiply938 := _t1696
				_t1695 = multiply938
			} else {
				var _t1697 *pb.Primitive
				if prediction930 == 6 {
					_t1698 := p.parse_minus()
					minus937 := _t1698
					_t1697 = minus937
				} else {
					var _t1699 *pb.Primitive
					if prediction930 == 5 {
						_t1700 := p.parse_add()
						add936 := _t1700
						_t1699 = add936
					} else {
						var _t1701 *pb.Primitive
						if prediction930 == 4 {
							_t1702 := p.parse_gt_eq()
							gt_eq935 := _t1702
							_t1701 = gt_eq935
						} else {
							var _t1703 *pb.Primitive
							if prediction930 == 3 {
								_t1704 := p.parse_gt()
								gt934 := _t1704
								_t1703 = gt934
							} else {
								var _t1705 *pb.Primitive
								if prediction930 == 2 {
									_t1706 := p.parse_lt_eq()
									lt_eq933 := _t1706
									_t1705 = lt_eq933
								} else {
									var _t1707 *pb.Primitive
									if prediction930 == 1 {
										_t1708 := p.parse_lt()
										lt932 := _t1708
										_t1707 = lt932
									} else {
										var _t1709 *pb.Primitive
										if prediction930 == 0 {
											_t1710 := p.parse_eq()
											eq931 := _t1710
											_t1709 = eq931
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1707 = _t1709
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
		_t1689 = _t1693
	}
	result946 := _t1689
	p.recordSpan(int(span_start945), "Primitive")
	return result946
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start949 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1711 := p.parse_term()
	term947 := _t1711
	_t1712 := p.parse_term()
	term_3948 := _t1712
	p.consumeLiteral(")")
	_t1713 := &pb.RelTerm{}
	_t1713.RelTermType = &pb.RelTerm_Term{Term: term947}
	_t1714 := &pb.RelTerm{}
	_t1714.RelTermType = &pb.RelTerm_Term{Term: term_3948}
	_t1715 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1713, _t1714}}
	result950 := _t1715
	p.recordSpan(int(span_start949), "Primitive")
	return result950
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1716 := p.parse_term()
	term951 := _t1716
	_t1717 := p.parse_term()
	term_3952 := _t1717
	p.consumeLiteral(")")
	_t1718 := &pb.RelTerm{}
	_t1718.RelTermType = &pb.RelTerm_Term{Term: term951}
	_t1719 := &pb.RelTerm{}
	_t1719.RelTermType = &pb.RelTerm_Term{Term: term_3952}
	_t1720 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1718, _t1719}}
	result954 := _t1720
	p.recordSpan(int(span_start953), "Primitive")
	return result954
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1721 := p.parse_term()
	term955 := _t1721
	_t1722 := p.parse_term()
	term_3956 := _t1722
	p.consumeLiteral(")")
	_t1723 := &pb.RelTerm{}
	_t1723.RelTermType = &pb.RelTerm_Term{Term: term955}
	_t1724 := &pb.RelTerm{}
	_t1724.RelTermType = &pb.RelTerm_Term{Term: term_3956}
	_t1725 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1723, _t1724}}
	result958 := _t1725
	p.recordSpan(int(span_start957), "Primitive")
	return result958
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start961 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1726 := p.parse_term()
	term959 := _t1726
	_t1727 := p.parse_term()
	term_3960 := _t1727
	p.consumeLiteral(")")
	_t1728 := &pb.RelTerm{}
	_t1728.RelTermType = &pb.RelTerm_Term{Term: term959}
	_t1729 := &pb.RelTerm{}
	_t1729.RelTermType = &pb.RelTerm_Term{Term: term_3960}
	_t1730 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1728, _t1729}}
	result962 := _t1730
	p.recordSpan(int(span_start961), "Primitive")
	return result962
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1731 := p.parse_term()
	term963 := _t1731
	_t1732 := p.parse_term()
	term_3964 := _t1732
	p.consumeLiteral(")")
	_t1733 := &pb.RelTerm{}
	_t1733.RelTermType = &pb.RelTerm_Term{Term: term963}
	_t1734 := &pb.RelTerm{}
	_t1734.RelTermType = &pb.RelTerm_Term{Term: term_3964}
	_t1735 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1733, _t1734}}
	result966 := _t1735
	p.recordSpan(int(span_start965), "Primitive")
	return result966
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1736 := p.parse_term()
	term967 := _t1736
	_t1737 := p.parse_term()
	term_3968 := _t1737
	_t1738 := p.parse_term()
	term_4969 := _t1738
	p.consumeLiteral(")")
	_t1739 := &pb.RelTerm{}
	_t1739.RelTermType = &pb.RelTerm_Term{Term: term967}
	_t1740 := &pb.RelTerm{}
	_t1740.RelTermType = &pb.RelTerm_Term{Term: term_3968}
	_t1741 := &pb.RelTerm{}
	_t1741.RelTermType = &pb.RelTerm_Term{Term: term_4969}
	_t1742 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1739, _t1740, _t1741}}
	result971 := _t1742
	p.recordSpan(int(span_start970), "Primitive")
	return result971
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1743 := p.parse_term()
	term972 := _t1743
	_t1744 := p.parse_term()
	term_3973 := _t1744
	_t1745 := p.parse_term()
	term_4974 := _t1745
	p.consumeLiteral(")")
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term972}
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term_3973}
	_t1748 := &pb.RelTerm{}
	_t1748.RelTermType = &pb.RelTerm_Term{Term: term_4974}
	_t1749 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1746, _t1747, _t1748}}
	result976 := _t1749
	p.recordSpan(int(span_start975), "Primitive")
	return result976
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1750 := p.parse_term()
	term977 := _t1750
	_t1751 := p.parse_term()
	term_3978 := _t1751
	_t1752 := p.parse_term()
	term_4979 := _t1752
	p.consumeLiteral(")")
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term977}
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term_3978}
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term_4979}
	_t1756 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1753, _t1754, _t1755}}
	result981 := _t1756
	p.recordSpan(int(span_start980), "Primitive")
	return result981
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start985 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1757 := p.parse_term()
	term982 := _t1757
	_t1758 := p.parse_term()
	term_3983 := _t1758
	_t1759 := p.parse_term()
	term_4984 := _t1759
	p.consumeLiteral(")")
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term982}
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term_3983}
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term_4984}
	_t1763 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1760, _t1761, _t1762}}
	result986 := _t1763
	p.recordSpan(int(span_start985), "Primitive")
	return result986
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start990 := int64(p.spanStart())
	var _t1764 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1764 = 1
	} else {
		var _t1765 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1765 = 1
		} else {
			var _t1766 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1766 = 1
			} else {
				var _t1767 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1767 = 1
				} else {
					var _t1768 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1768 = 0
					} else {
						var _t1769 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1769 = 1
						} else {
							var _t1770 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1770 = 1
							} else {
								var _t1771 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1771 = 1
								} else {
									var _t1772 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1772 = 1
									} else {
										var _t1773 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1773 = 1
										} else {
											var _t1774 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1774 = 1
											} else {
												var _t1775 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1775 = 1
												} else {
													var _t1776 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1776 = 1
													} else {
														var _t1777 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1777 = 1
														} else {
															var _t1778 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1778 = 1
															} else {
																_t1778 = -1
															}
															_t1777 = _t1778
														}
														_t1776 = _t1777
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
	prediction987 := _t1764
	var _t1779 *pb.RelTerm
	if prediction987 == 1 {
		_t1780 := p.parse_term()
		term989 := _t1780
		_t1781 := &pb.RelTerm{}
		_t1781.RelTermType = &pb.RelTerm_Term{Term: term989}
		_t1779 = _t1781
	} else {
		var _t1782 *pb.RelTerm
		if prediction987 == 0 {
			_t1783 := p.parse_specialized_value()
			specialized_value988 := _t1783
			_t1784 := &pb.RelTerm{}
			_t1784.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value988}
			_t1782 = _t1784
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1779 = _t1782
	}
	result991 := _t1779
	p.recordSpan(int(span_start990), "RelTerm")
	return result991
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start993 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1785 := p.parse_raw_value()
	raw_value992 := _t1785
	result994 := raw_value992
	p.recordSpan(int(span_start993), "Value")
	return result994
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1000 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1786 := p.parse_name()
	name995 := _t1786
	xs996 := []*pb.RelTerm{}
	cond997 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond997 {
		_t1787 := p.parse_rel_term()
		item998 := _t1787
		xs996 = append(xs996, item998)
		cond997 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms999 := xs996
	p.consumeLiteral(")")
	_t1788 := &pb.RelAtom{Name: name995, Terms: rel_terms999}
	result1001 := _t1788
	p.recordSpan(int(span_start1000), "RelAtom")
	return result1001
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1789 := p.parse_term()
	term1002 := _t1789
	_t1790 := p.parse_term()
	term_31003 := _t1790
	p.consumeLiteral(")")
	_t1791 := &pb.Cast{Input: term1002, Result: term_31003}
	result1005 := _t1791
	p.recordSpan(int(span_start1004), "Cast")
	return result1005
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1006 := []*pb.Attribute{}
	cond1007 := p.matchLookaheadLiteral("(", 0)
	for cond1007 {
		_t1792 := p.parse_attribute()
		item1008 := _t1792
		xs1006 = append(xs1006, item1008)
		cond1007 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1009 := xs1006
	p.consumeLiteral(")")
	return attributes1009
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1015 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1793 := p.parse_name()
	name1010 := _t1793
	xs1011 := []*pb.Value{}
	cond1012 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1012 {
		_t1794 := p.parse_raw_value()
		item1013 := _t1794
		xs1011 = append(xs1011, item1013)
		cond1012 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1014 := xs1011
	p.consumeLiteral(")")
	_t1795 := &pb.Attribute{Name: name1010, Args: raw_values1014}
	result1016 := _t1795
	p.recordSpan(int(span_start1015), "Attribute")
	return result1016
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1017 := []*pb.RelationId{}
	cond1018 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1018 {
		_t1796 := p.parse_relation_id()
		item1019 := _t1796
		xs1017 = append(xs1017, item1019)
		cond1018 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1020 := xs1017
	_t1797 := p.parse_script()
	script1021 := _t1797
	p.consumeLiteral(")")
	_t1798 := &pb.Algorithm{Global: relation_ids1020, Body: script1021}
	result1023 := _t1798
	p.recordSpan(int(span_start1022), "Algorithm")
	return result1023
}

func (p *Parser) parse_script() *pb.Script {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1024 := []*pb.Construct{}
	cond1025 := p.matchLookaheadLiteral("(", 0)
	for cond1025 {
		_t1799 := p.parse_construct()
		item1026 := _t1799
		xs1024 = append(xs1024, item1026)
		cond1025 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1027 := xs1024
	p.consumeLiteral(")")
	_t1800 := &pb.Script{Constructs: constructs1027}
	result1029 := _t1800
	p.recordSpan(int(span_start1028), "Script")
	return result1029
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1033 := int64(p.spanStart())
	var _t1801 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1802 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1802 = 1
		} else {
			var _t1803 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1803 = 1
			} else {
				var _t1804 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1804 = 1
				} else {
					var _t1805 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1805 = 0
					} else {
						var _t1806 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1806 = 1
						} else {
							var _t1807 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1807 = 1
							} else {
								_t1807 = -1
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
	} else {
		_t1801 = -1
	}
	prediction1030 := _t1801
	var _t1808 *pb.Construct
	if prediction1030 == 1 {
		_t1809 := p.parse_instruction()
		instruction1032 := _t1809
		_t1810 := &pb.Construct{}
		_t1810.ConstructType = &pb.Construct_Instruction{Instruction: instruction1032}
		_t1808 = _t1810
	} else {
		var _t1811 *pb.Construct
		if prediction1030 == 0 {
			_t1812 := p.parse_loop()
			loop1031 := _t1812
			_t1813 := &pb.Construct{}
			_t1813.ConstructType = &pb.Construct_Loop{Loop: loop1031}
			_t1811 = _t1813
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1808 = _t1811
	}
	result1034 := _t1808
	p.recordSpan(int(span_start1033), "Construct")
	return result1034
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1037 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1814 := p.parse_init()
	init1035 := _t1814
	_t1815 := p.parse_script()
	script1036 := _t1815
	p.consumeLiteral(")")
	_t1816 := &pb.Loop{Init: init1035, Body: script1036}
	result1038 := _t1816
	p.recordSpan(int(span_start1037), "Loop")
	return result1038
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1039 := []*pb.Instruction{}
	cond1040 := p.matchLookaheadLiteral("(", 0)
	for cond1040 {
		_t1817 := p.parse_instruction()
		item1041 := _t1817
		xs1039 = append(xs1039, item1041)
		cond1040 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1042 := xs1039
	p.consumeLiteral(")")
	return instructions1042
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1049 := int64(p.spanStart())
	var _t1818 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1819 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1819 = 1
		} else {
			var _t1820 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1820 = 4
			} else {
				var _t1821 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1821 = 3
				} else {
					var _t1822 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1822 = 2
					} else {
						var _t1823 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1823 = 0
						} else {
							_t1823 = -1
						}
						_t1822 = _t1823
					}
					_t1821 = _t1822
				}
				_t1820 = _t1821
			}
			_t1819 = _t1820
		}
		_t1818 = _t1819
	} else {
		_t1818 = -1
	}
	prediction1043 := _t1818
	var _t1824 *pb.Instruction
	if prediction1043 == 4 {
		_t1825 := p.parse_monus_def()
		monus_def1048 := _t1825
		_t1826 := &pb.Instruction{}
		_t1826.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1048}
		_t1824 = _t1826
	} else {
		var _t1827 *pb.Instruction
		if prediction1043 == 3 {
			_t1828 := p.parse_monoid_def()
			monoid_def1047 := _t1828
			_t1829 := &pb.Instruction{}
			_t1829.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1047}
			_t1827 = _t1829
		} else {
			var _t1830 *pb.Instruction
			if prediction1043 == 2 {
				_t1831 := p.parse_break()
				break1046 := _t1831
				_t1832 := &pb.Instruction{}
				_t1832.InstrType = &pb.Instruction_Break{Break: break1046}
				_t1830 = _t1832
			} else {
				var _t1833 *pb.Instruction
				if prediction1043 == 1 {
					_t1834 := p.parse_upsert()
					upsert1045 := _t1834
					_t1835 := &pb.Instruction{}
					_t1835.InstrType = &pb.Instruction_Upsert{Upsert: upsert1045}
					_t1833 = _t1835
				} else {
					var _t1836 *pb.Instruction
					if prediction1043 == 0 {
						_t1837 := p.parse_assign()
						assign1044 := _t1837
						_t1838 := &pb.Instruction{}
						_t1838.InstrType = &pb.Instruction_Assign{Assign: assign1044}
						_t1836 = _t1838
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1833 = _t1836
				}
				_t1830 = _t1833
			}
			_t1827 = _t1830
		}
		_t1824 = _t1827
	}
	result1050 := _t1824
	p.recordSpan(int(span_start1049), "Instruction")
	return result1050
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1054 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1839 := p.parse_relation_id()
	relation_id1051 := _t1839
	_t1840 := p.parse_abstraction()
	abstraction1052 := _t1840
	var _t1841 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1842 := p.parse_attrs()
		_t1841 = _t1842
	}
	attrs1053 := _t1841
	p.consumeLiteral(")")
	_t1843 := attrs1053
	if attrs1053 == nil {
		_t1843 = []*pb.Attribute{}
	}
	_t1844 := &pb.Assign{Name: relation_id1051, Body: abstraction1052, Attrs: _t1843}
	result1055 := _t1844
	p.recordSpan(int(span_start1054), "Assign")
	return result1055
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1059 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1845 := p.parse_relation_id()
	relation_id1056 := _t1845
	_t1846 := p.parse_abstraction_with_arity()
	abstraction_with_arity1057 := _t1846
	var _t1847 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1848 := p.parse_attrs()
		_t1847 = _t1848
	}
	attrs1058 := _t1847
	p.consumeLiteral(")")
	_t1849 := attrs1058
	if attrs1058 == nil {
		_t1849 = []*pb.Attribute{}
	}
	_t1850 := &pb.Upsert{Name: relation_id1056, Body: abstraction_with_arity1057[0].(*pb.Abstraction), Attrs: _t1849, ValueArity: abstraction_with_arity1057[1].(int64)}
	result1060 := _t1850
	p.recordSpan(int(span_start1059), "Upsert")
	return result1060
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1851 := p.parse_bindings()
	bindings1061 := _t1851
	_t1852 := p.parse_formula()
	formula1062 := _t1852
	p.consumeLiteral(")")
	_t1853 := &pb.Abstraction{Vars: listConcat(bindings1061[0].([]*pb.Binding), bindings1061[1].([]*pb.Binding)), Value: formula1062}
	return []interface{}{_t1853, int64(len(bindings1061[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1066 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1854 := p.parse_relation_id()
	relation_id1063 := _t1854
	_t1855 := p.parse_abstraction()
	abstraction1064 := _t1855
	var _t1856 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1857 := p.parse_attrs()
		_t1856 = _t1857
	}
	attrs1065 := _t1856
	p.consumeLiteral(")")
	_t1858 := attrs1065
	if attrs1065 == nil {
		_t1858 = []*pb.Attribute{}
	}
	_t1859 := &pb.Break{Name: relation_id1063, Body: abstraction1064, Attrs: _t1858}
	result1067 := _t1859
	p.recordSpan(int(span_start1066), "Break")
	return result1067
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1072 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1860 := p.parse_monoid()
	monoid1068 := _t1860
	_t1861 := p.parse_relation_id()
	relation_id1069 := _t1861
	_t1862 := p.parse_abstraction_with_arity()
	abstraction_with_arity1070 := _t1862
	var _t1863 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1864 := p.parse_attrs()
		_t1863 = _t1864
	}
	attrs1071 := _t1863
	p.consumeLiteral(")")
	_t1865 := attrs1071
	if attrs1071 == nil {
		_t1865 = []*pb.Attribute{}
	}
	_t1866 := &pb.MonoidDef{Monoid: monoid1068, Name: relation_id1069, Body: abstraction_with_arity1070[0].(*pb.Abstraction), Attrs: _t1865, ValueArity: abstraction_with_arity1070[1].(int64)}
	result1073 := _t1866
	p.recordSpan(int(span_start1072), "MonoidDef")
	return result1073
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1079 := int64(p.spanStart())
	var _t1867 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1868 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1868 = 3
		} else {
			var _t1869 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1869 = 0
			} else {
				var _t1870 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1870 = 1
				} else {
					var _t1871 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1871 = 2
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
	} else {
		_t1867 = -1
	}
	prediction1074 := _t1867
	var _t1872 *pb.Monoid
	if prediction1074 == 3 {
		_t1873 := p.parse_sum_monoid()
		sum_monoid1078 := _t1873
		_t1874 := &pb.Monoid{}
		_t1874.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1078}
		_t1872 = _t1874
	} else {
		var _t1875 *pb.Monoid
		if prediction1074 == 2 {
			_t1876 := p.parse_max_monoid()
			max_monoid1077 := _t1876
			_t1877 := &pb.Monoid{}
			_t1877.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1077}
			_t1875 = _t1877
		} else {
			var _t1878 *pb.Monoid
			if prediction1074 == 1 {
				_t1879 := p.parse_min_monoid()
				min_monoid1076 := _t1879
				_t1880 := &pb.Monoid{}
				_t1880.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1076}
				_t1878 = _t1880
			} else {
				var _t1881 *pb.Monoid
				if prediction1074 == 0 {
					_t1882 := p.parse_or_monoid()
					or_monoid1075 := _t1882
					_t1883 := &pb.Monoid{}
					_t1883.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1075}
					_t1881 = _t1883
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1878 = _t1881
			}
			_t1875 = _t1878
		}
		_t1872 = _t1875
	}
	result1080 := _t1872
	p.recordSpan(int(span_start1079), "Monoid")
	return result1080
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1081 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1884 := &pb.OrMonoid{}
	result1082 := _t1884
	p.recordSpan(int(span_start1081), "OrMonoid")
	return result1082
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1084 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1885 := p.parse_type()
	type1083 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.MinMonoid{Type: type1083}
	result1085 := _t1886
	p.recordSpan(int(span_start1084), "MinMonoid")
	return result1085
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1887 := p.parse_type()
	type1086 := _t1887
	p.consumeLiteral(")")
	_t1888 := &pb.MaxMonoid{Type: type1086}
	result1088 := _t1888
	p.recordSpan(int(span_start1087), "MaxMonoid")
	return result1088
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1090 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1889 := p.parse_type()
	type1089 := _t1889
	p.consumeLiteral(")")
	_t1890 := &pb.SumMonoid{Type: type1089}
	result1091 := _t1890
	p.recordSpan(int(span_start1090), "SumMonoid")
	return result1091
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1096 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1891 := p.parse_monoid()
	monoid1092 := _t1891
	_t1892 := p.parse_relation_id()
	relation_id1093 := _t1892
	_t1893 := p.parse_abstraction_with_arity()
	abstraction_with_arity1094 := _t1893
	var _t1894 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1895 := p.parse_attrs()
		_t1894 = _t1895
	}
	attrs1095 := _t1894
	p.consumeLiteral(")")
	_t1896 := attrs1095
	if attrs1095 == nil {
		_t1896 = []*pb.Attribute{}
	}
	_t1897 := &pb.MonusDef{Monoid: monoid1092, Name: relation_id1093, Body: abstraction_with_arity1094[0].(*pb.Abstraction), Attrs: _t1896, ValueArity: abstraction_with_arity1094[1].(int64)}
	result1097 := _t1897
	p.recordSpan(int(span_start1096), "MonusDef")
	return result1097
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1102 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1898 := p.parse_relation_id()
	relation_id1098 := _t1898
	_t1899 := p.parse_abstraction()
	abstraction1099 := _t1899
	_t1900 := p.parse_functional_dependency_keys()
	functional_dependency_keys1100 := _t1900
	_t1901 := p.parse_functional_dependency_values()
	functional_dependency_values1101 := _t1901
	p.consumeLiteral(")")
	_t1902 := &pb.FunctionalDependency{Guard: abstraction1099, Keys: functional_dependency_keys1100, Values: functional_dependency_values1101}
	_t1903 := &pb.Constraint{Name: relation_id1098}
	_t1903.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1902}
	result1103 := _t1903
	p.recordSpan(int(span_start1102), "Constraint")
	return result1103
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1104 := []*pb.Var{}
	cond1105 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1105 {
		_t1904 := p.parse_var()
		item1106 := _t1904
		xs1104 = append(xs1104, item1106)
		cond1105 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1107 := xs1104
	p.consumeLiteral(")")
	return vars1107
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1108 := []*pb.Var{}
	cond1109 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1109 {
		_t1905 := p.parse_var()
		item1110 := _t1905
		xs1108 = append(xs1108, item1110)
		cond1109 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1111 := xs1108
	p.consumeLiteral(")")
	return vars1111
}

func (p *Parser) parse_data() *pb.Data {
	span_start1117 := int64(p.spanStart())
	var _t1906 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1907 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1907 = 3
		} else {
			var _t1908 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1908 = 0
			} else {
				var _t1909 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1909 = 2
				} else {
					var _t1910 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1910 = 1
					} else {
						_t1910 = -1
					}
					_t1909 = _t1910
				}
				_t1908 = _t1909
			}
			_t1907 = _t1908
		}
		_t1906 = _t1907
	} else {
		_t1906 = -1
	}
	prediction1112 := _t1906
	var _t1911 *pb.Data
	if prediction1112 == 3 {
		_t1912 := p.parse_iceberg_data()
		iceberg_data1116 := _t1912
		_t1913 := &pb.Data{}
		_t1913.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1116}
		_t1911 = _t1913
	} else {
		var _t1914 *pb.Data
		if prediction1112 == 2 {
			_t1915 := p.parse_csv_data()
			csv_data1115 := _t1915
			_t1916 := &pb.Data{}
			_t1916.DataType = &pb.Data_CsvData{CsvData: csv_data1115}
			_t1914 = _t1916
		} else {
			var _t1917 *pb.Data
			if prediction1112 == 1 {
				_t1918 := p.parse_betree_relation()
				betree_relation1114 := _t1918
				_t1919 := &pb.Data{}
				_t1919.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1114}
				_t1917 = _t1919
			} else {
				var _t1920 *pb.Data
				if prediction1112 == 0 {
					_t1921 := p.parse_edb()
					edb1113 := _t1921
					_t1922 := &pb.Data{}
					_t1922.DataType = &pb.Data_Edb{Edb: edb1113}
					_t1920 = _t1922
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1917 = _t1920
			}
			_t1914 = _t1917
		}
		_t1911 = _t1914
	}
	result1118 := _t1911
	p.recordSpan(int(span_start1117), "Data")
	return result1118
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1122 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1923 := p.parse_relation_id()
	relation_id1119 := _t1923
	_t1924 := p.parse_edb_path()
	edb_path1120 := _t1924
	_t1925 := p.parse_edb_types()
	edb_types1121 := _t1925
	p.consumeLiteral(")")
	_t1926 := &pb.EDB{TargetId: relation_id1119, Path: edb_path1120, Types: edb_types1121}
	result1123 := _t1926
	p.recordSpan(int(span_start1122), "EDB")
	return result1123
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1124 := []string{}
	cond1125 := p.matchLookaheadTerminal("STRING", 0)
	for cond1125 {
		item1126 := p.consumeTerminal("STRING").Value.str
		xs1124 = append(xs1124, item1126)
		cond1125 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1127 := xs1124
	p.consumeLiteral("]")
	return strings1127
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1128 := []*pb.Type{}
	cond1129 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1129 {
		_t1927 := p.parse_type()
		item1130 := _t1927
		xs1128 = append(xs1128, item1130)
		cond1129 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1131 := xs1128
	p.consumeLiteral("]")
	return types1131
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1928 := p.parse_relation_id()
	relation_id1132 := _t1928
	_t1929 := p.parse_betree_info()
	betree_info1133 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.BeTreeRelation{Name: relation_id1132, RelationInfo: betree_info1133}
	result1135 := _t1930
	p.recordSpan(int(span_start1134), "BeTreeRelation")
	return result1135
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1139 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1931 := p.parse_betree_info_key_types()
	betree_info_key_types1136 := _t1931
	_t1932 := p.parse_betree_info_value_types()
	betree_info_value_types1137 := _t1932
	_t1933 := p.parse_config_dict()
	config_dict1138 := _t1933
	p.consumeLiteral(")")
	_t1934 := p.construct_betree_info(betree_info_key_types1136, betree_info_value_types1137, config_dict1138)
	result1140 := _t1934
	p.recordSpan(int(span_start1139), "BeTreeInfo")
	return result1140
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1141 := []*pb.Type{}
	cond1142 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1142 {
		_t1935 := p.parse_type()
		item1143 := _t1935
		xs1141 = append(xs1141, item1143)
		cond1142 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1144 := xs1141
	p.consumeLiteral(")")
	return types1144
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1145 := []*pb.Type{}
	cond1146 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1146 {
		_t1936 := p.parse_type()
		item1147 := _t1936
		xs1145 = append(xs1145, item1147)
		cond1146 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1148 := xs1145
	p.consumeLiteral(")")
	return types1148
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1153 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1937 := p.parse_csvlocator()
	csvlocator1149 := _t1937
	_t1938 := p.parse_csv_config()
	csv_config1150 := _t1938
	_t1939 := p.parse_gnf_columns()
	gnf_columns1151 := _t1939
	_t1940 := p.parse_csv_asof()
	csv_asof1152 := _t1940
	p.consumeLiteral(")")
	_t1941 := &pb.CSVData{Locator: csvlocator1149, Config: csv_config1150, Columns: gnf_columns1151, Asof: csv_asof1152}
	result1154 := _t1941
	p.recordSpan(int(span_start1153), "CSVData")
	return result1154
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1942 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1943 := p.parse_csv_locator_paths()
		_t1942 = _t1943
	}
	csv_locator_paths1155 := _t1942
	var _t1944 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1945 := p.parse_csv_locator_inline_data()
		_t1944 = ptr(_t1945)
	}
	csv_locator_inline_data1156 := _t1944
	p.consumeLiteral(")")
	_t1946 := csv_locator_paths1155
	if csv_locator_paths1155 == nil {
		_t1946 = []string{}
	}
	_t1947 := &pb.CSVLocator{Paths: _t1946, InlineData: []byte(deref(csv_locator_inline_data1156, ""))}
	result1158 := _t1947
	p.recordSpan(int(span_start1157), "CSVLocator")
	return result1158
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1159 := []string{}
	cond1160 := p.matchLookaheadTerminal("STRING", 0)
	for cond1160 {
		item1161 := p.consumeTerminal("STRING").Value.str
		xs1159 = append(xs1159, item1161)
		cond1160 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1162 := xs1159
	p.consumeLiteral(")")
	return strings1162
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1163 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1163
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1165 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1948 := p.parse_config_dict()
	config_dict1164 := _t1948
	p.consumeLiteral(")")
	_t1949 := p.construct_csv_config(config_dict1164)
	result1166 := _t1949
	p.recordSpan(int(span_start1165), "CSVConfig")
	return result1166
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1167 := []*pb.GNFColumn{}
	cond1168 := p.matchLookaheadLiteral("(", 0)
	for cond1168 {
		_t1950 := p.parse_gnf_column()
		item1169 := _t1950
		xs1167 = append(xs1167, item1169)
		cond1168 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1170 := xs1167
	p.consumeLiteral(")")
	return gnf_columns1170
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1177 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1951 := p.parse_gnf_column_path()
	gnf_column_path1171 := _t1951
	var _t1952 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1953 := p.parse_relation_id()
		_t1952 = _t1953
	}
	relation_id1172 := _t1952
	p.consumeLiteral("[")
	xs1173 := []*pb.Type{}
	cond1174 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1174 {
		_t1954 := p.parse_type()
		item1175 := _t1954
		xs1173 = append(xs1173, item1175)
		cond1174 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1176 := xs1173
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1955 := &pb.GNFColumn{ColumnPath: gnf_column_path1171, TargetId: relation_id1172, Types: types1176}
	result1178 := _t1955
	p.recordSpan(int(span_start1177), "GNFColumn")
	return result1178
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1956 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1956 = 1
	} else {
		var _t1957 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1957 = 0
		} else {
			_t1957 = -1
		}
		_t1956 = _t1957
	}
	prediction1179 := _t1956
	var _t1958 []string
	if prediction1179 == 1 {
		p.consumeLiteral("[")
		xs1181 := []string{}
		cond1182 := p.matchLookaheadTerminal("STRING", 0)
		for cond1182 {
			item1183 := p.consumeTerminal("STRING").Value.str
			xs1181 = append(xs1181, item1183)
			cond1182 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1184 := xs1181
		p.consumeLiteral("]")
		_t1958 = strings1184
	} else {
		var _t1959 []string
		if prediction1179 == 0 {
			string1180 := p.consumeTerminal("STRING").Value.str
			_ = string1180
			_t1959 = []string{string1180}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1958 = _t1959
	}
	return _t1958
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1185 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1185
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1190 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1960 := p.parse_iceberg_locator()
	iceberg_locator1186 := _t1960
	_t1961 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1187 := _t1961
	_t1962 := p.parse_gnf_columns()
	gnf_columns1188 := _t1962
	var _t1963 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1964 := p.parse_iceberg_to_snapshot()
		_t1963 = ptr(_t1964)
	}
	iceberg_to_snapshot1189 := _t1963
	p.consumeLiteral(")")
	_t1965 := &pb.IcebergData{Locator: iceberg_locator1186, Config: iceberg_catalog_config1187, Columns: gnf_columns1188, ToSnapshot: ptr(deref(iceberg_to_snapshot1189, ""))}
	result1191 := _t1965
	p.recordSpan(int(span_start1190), "IcebergData")
	return result1191
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1198 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1192 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1193 := []string{}
	cond1194 := p.matchLookaheadTerminal("STRING", 0)
	for cond1194 {
		item1195 := p.consumeTerminal("STRING").Value.str
		xs1193 = append(xs1193, item1195)
		cond1194 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1196 := xs1193
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121197 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1966 := &pb.IcebergLocator{TableName: string1192, Namespace: strings1196, Warehouse: string_121197}
	result1199 := _t1966
	p.recordSpan(int(span_start1198), "IcebergLocator")
	return result1199
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1210 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1200 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1967 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1968 := p.parse_iceberg_catalog_config_scope()
		_t1967 = ptr(_t1968)
	}
	iceberg_catalog_config_scope1201 := _t1967
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1202 := [][]interface{}{}
	cond1203 := p.matchLookaheadLiteral("(", 0)
	for cond1203 {
		_t1969 := p.parse_iceberg_property_entry()
		item1204 := _t1969
		xs1202 = append(xs1202, item1204)
		cond1203 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1205 := xs1202
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1206 := [][]interface{}{}
	cond1207 := p.matchLookaheadLiteral("(", 0)
	for cond1207 {
		_t1970 := p.parse_iceberg_property_entry()
		item1208 := _t1970
		xs1206 = append(xs1206, item1208)
		cond1207 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys_131209 := xs1206
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1971 := p.construct_iceberg_catalog_config(string1200, iceberg_catalog_config_scope1201, iceberg_property_entrys1205, iceberg_property_entrys_131209)
	result1211 := _t1971
	p.recordSpan(int(span_start1210), "IcebergCatalogConfig")
	return result1211
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1212 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1212
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1213 := p.consumeTerminal("STRING").Value.str
	string_31214 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1213, string_31214}
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1215 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1215
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1217 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1972 := p.parse_fragment_id()
	fragment_id1216 := _t1972
	p.consumeLiteral(")")
	_t1973 := &pb.Undefine{FragmentId: fragment_id1216}
	result1218 := _t1973
	p.recordSpan(int(span_start1217), "Undefine")
	return result1218
}

func (p *Parser) parse_context() *pb.Context {
	span_start1223 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1219 := []*pb.RelationId{}
	cond1220 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1220 {
		_t1974 := p.parse_relation_id()
		item1221 := _t1974
		xs1219 = append(xs1219, item1221)
		cond1220 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1222 := xs1219
	p.consumeLiteral(")")
	_t1975 := &pb.Context{Relations: relation_ids1222}
	result1224 := _t1975
	p.recordSpan(int(span_start1223), "Context")
	return result1224
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1229 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1225 := []*pb.SnapshotMapping{}
	cond1226 := p.matchLookaheadLiteral("[", 0)
	for cond1226 {
		_t1976 := p.parse_snapshot_mapping()
		item1227 := _t1976
		xs1225 = append(xs1225, item1227)
		cond1226 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1228 := xs1225
	p.consumeLiteral(")")
	_t1977 := &pb.Snapshot{Mappings: snapshot_mappings1228}
	result1230 := _t1977
	p.recordSpan(int(span_start1229), "Snapshot")
	return result1230
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1233 := int64(p.spanStart())
	_t1978 := p.parse_edb_path()
	edb_path1231 := _t1978
	_t1979 := p.parse_relation_id()
	relation_id1232 := _t1979
	_t1980 := &pb.SnapshotMapping{DestinationPath: edb_path1231, SourceRelation: relation_id1232}
	result1234 := _t1980
	p.recordSpan(int(span_start1233), "SnapshotMapping")
	return result1234
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1235 := []*pb.Read{}
	cond1236 := p.matchLookaheadLiteral("(", 0)
	for cond1236 {
		_t1981 := p.parse_read()
		item1237 := _t1981
		xs1235 = append(xs1235, item1237)
		cond1236 = p.matchLookaheadLiteral("(", 0)
	}
	reads1238 := xs1235
	p.consumeLiteral(")")
	return reads1238
}

func (p *Parser) parse_read() *pb.Read {
	span_start1245 := int64(p.spanStart())
	var _t1982 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1983 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1983 = 2
		} else {
			var _t1984 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1984 = 1
			} else {
				var _t1985 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1985 = 4
				} else {
					var _t1986 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1986 = 4
					} else {
						var _t1987 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1987 = 0
						} else {
							var _t1988 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1988 = 3
							} else {
								_t1988 = -1
							}
							_t1987 = _t1988
						}
						_t1986 = _t1987
					}
					_t1985 = _t1986
				}
				_t1984 = _t1985
			}
			_t1983 = _t1984
		}
		_t1982 = _t1983
	} else {
		_t1982 = -1
	}
	prediction1239 := _t1982
	var _t1989 *pb.Read
	if prediction1239 == 4 {
		_t1990 := p.parse_export()
		export1244 := _t1990
		_t1991 := &pb.Read{}
		_t1991.ReadType = &pb.Read_Export{Export: export1244}
		_t1989 = _t1991
	} else {
		var _t1992 *pb.Read
		if prediction1239 == 3 {
			_t1993 := p.parse_abort()
			abort1243 := _t1993
			_t1994 := &pb.Read{}
			_t1994.ReadType = &pb.Read_Abort{Abort: abort1243}
			_t1992 = _t1994
		} else {
			var _t1995 *pb.Read
			if prediction1239 == 2 {
				_t1996 := p.parse_what_if()
				what_if1242 := _t1996
				_t1997 := &pb.Read{}
				_t1997.ReadType = &pb.Read_WhatIf{WhatIf: what_if1242}
				_t1995 = _t1997
			} else {
				var _t1998 *pb.Read
				if prediction1239 == 1 {
					_t1999 := p.parse_output()
					output1241 := _t1999
					_t2000 := &pb.Read{}
					_t2000.ReadType = &pb.Read_Output{Output: output1241}
					_t1998 = _t2000
				} else {
					var _t2001 *pb.Read
					if prediction1239 == 0 {
						_t2002 := p.parse_demand()
						demand1240 := _t2002
						_t2003 := &pb.Read{}
						_t2003.ReadType = &pb.Read_Demand{Demand: demand1240}
						_t2001 = _t2003
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1998 = _t2001
				}
				_t1995 = _t1998
			}
			_t1992 = _t1995
		}
		_t1989 = _t1992
	}
	result1246 := _t1989
	p.recordSpan(int(span_start1245), "Read")
	return result1246
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1248 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2004 := p.parse_relation_id()
	relation_id1247 := _t2004
	p.consumeLiteral(")")
	_t2005 := &pb.Demand{RelationId: relation_id1247}
	result1249 := _t2005
	p.recordSpan(int(span_start1248), "Demand")
	return result1249
}

func (p *Parser) parse_output() *pb.Output {
	span_start1252 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2006 := p.parse_name()
	name1250 := _t2006
	_t2007 := p.parse_relation_id()
	relation_id1251 := _t2007
	p.consumeLiteral(")")
	_t2008 := &pb.Output{Name: name1250, RelationId: relation_id1251}
	result1253 := _t2008
	p.recordSpan(int(span_start1252), "Output")
	return result1253
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1256 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2009 := p.parse_name()
	name1254 := _t2009
	_t2010 := p.parse_epoch()
	epoch1255 := _t2010
	p.consumeLiteral(")")
	_t2011 := &pb.WhatIf{Branch: name1254, Epoch: epoch1255}
	result1257 := _t2011
	p.recordSpan(int(span_start1256), "WhatIf")
	return result1257
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1260 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2012 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2013 := p.parse_name()
		_t2012 = ptr(_t2013)
	}
	name1258 := _t2012
	_t2014 := p.parse_relation_id()
	relation_id1259 := _t2014
	p.consumeLiteral(")")
	_t2015 := &pb.Abort{Name: deref(name1258, "abort"), RelationId: relation_id1259}
	result1261 := _t2015
	p.recordSpan(int(span_start1260), "Abort")
	return result1261
}

func (p *Parser) parse_export() *pb.Export {
	span_start1265 := int64(p.spanStart())
	var _t2016 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2017 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2017 = 1
		} else {
			var _t2018 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2018 = 0
			} else {
				_t2018 = -1
			}
			_t2017 = _t2018
		}
		_t2016 = _t2017
	} else {
		_t2016 = -1
	}
	prediction1262 := _t2016
	var _t2019 *pb.Export
	if prediction1262 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2020 := p.parse_export_iceberg_config()
		export_iceberg_config1264 := _t2020
		p.consumeLiteral(")")
		_t2021 := &pb.Export{}
		_t2021.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1264}
		_t2019 = _t2021
	} else {
		var _t2022 *pb.Export
		if prediction1262 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2023 := p.parse_export_csv_config()
			export_csv_config1263 := _t2023
			p.consumeLiteral(")")
			_t2024 := &pb.Export{}
			_t2024.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1263}
			_t2022 = _t2024
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2019 = _t2022
	}
	result1266 := _t2019
	p.recordSpan(int(span_start1265), "Export")
	return result1266
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1274 := int64(p.spanStart())
	var _t2025 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2026 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2026 = 0
		} else {
			var _t2027 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2027 = 1
			} else {
				_t2027 = -1
			}
			_t2026 = _t2027
		}
		_t2025 = _t2026
	} else {
		_t2025 = -1
	}
	prediction1267 := _t2025
	var _t2028 *pb.ExportCSVConfig
	if prediction1267 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2029 := p.parse_export_csv_path()
		export_csv_path1271 := _t2029
		_t2030 := p.parse_export_csv_columns_list()
		export_csv_columns_list1272 := _t2030
		_t2031 := p.parse_config_dict()
		config_dict1273 := _t2031
		p.consumeLiteral(")")
		_t2032 := p.construct_export_csv_config(export_csv_path1271, export_csv_columns_list1272, config_dict1273)
		_t2028 = _t2032
	} else {
		var _t2033 *pb.ExportCSVConfig
		if prediction1267 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2034 := p.parse_export_csv_path()
			export_csv_path1268 := _t2034
			_t2035 := p.parse_export_csv_source()
			export_csv_source1269 := _t2035
			_t2036 := p.parse_csv_config()
			csv_config1270 := _t2036
			p.consumeLiteral(")")
			_t2037 := p.construct_export_csv_config_with_source(export_csv_path1268, export_csv_source1269, csv_config1270)
			_t2033 = _t2037
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2028 = _t2033
	}
	result1275 := _t2028
	p.recordSpan(int(span_start1274), "ExportCSVConfig")
	return result1275
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1276 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1276
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1283 := int64(p.spanStart())
	var _t2038 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2039 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2039 = 1
		} else {
			var _t2040 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2040 = 0
			} else {
				_t2040 = -1
			}
			_t2039 = _t2040
		}
		_t2038 = _t2039
	} else {
		_t2038 = -1
	}
	prediction1277 := _t2038
	var _t2041 *pb.ExportCSVSource
	if prediction1277 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2042 := p.parse_relation_id()
		relation_id1282 := _t2042
		p.consumeLiteral(")")
		_t2043 := &pb.ExportCSVSource{}
		_t2043.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1282}
		_t2041 = _t2043
	} else {
		var _t2044 *pb.ExportCSVSource
		if prediction1277 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1278 := []*pb.ExportCSVColumn{}
			cond1279 := p.matchLookaheadLiteral("(", 0)
			for cond1279 {
				_t2045 := p.parse_export_csv_column()
				item1280 := _t2045
				xs1278 = append(xs1278, item1280)
				cond1279 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1281 := xs1278
			p.consumeLiteral(")")
			_t2046 := &pb.ExportCSVColumns{Columns: export_csv_columns1281}
			_t2047 := &pb.ExportCSVSource{}
			_t2047.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2046}
			_t2044 = _t2047
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2041 = _t2044
	}
	result1284 := _t2041
	p.recordSpan(int(span_start1283), "ExportCSVSource")
	return result1284
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1287 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1285 := p.consumeTerminal("STRING").Value.str
	_t2048 := p.parse_relation_id()
	relation_id1286 := _t2048
	p.consumeLiteral(")")
	_t2049 := &pb.ExportCSVColumn{ColumnName: string1285, ColumnData: relation_id1286}
	result1288 := _t2049
	p.recordSpan(int(span_start1287), "ExportCSVColumn")
	return result1288
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1289 := []*pb.ExportCSVColumn{}
	cond1290 := p.matchLookaheadLiteral("(", 0)
	for cond1290 {
		_t2050 := p.parse_export_csv_column()
		item1291 := _t2050
		xs1289 = append(xs1289, item1291)
		cond1290 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1292 := xs1289
	p.consumeLiteral(")")
	return export_csv_columns1292
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1304 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2051 := p.parse_iceberg_locator()
	iceberg_locator1293 := _t2051
	_t2052 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1294 := _t2052
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1295 := []*pb.ExportIcebergColumn{}
	cond1296 := p.matchLookaheadLiteral("(", 0)
	for cond1296 {
		_t2053 := p.parse_iceberg_export_column()
		item1297 := _t2053
		xs1295 = append(xs1295, item1297)
		cond1296 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_export_columns1298 := xs1295
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("create_table_properties")
	xs1299 := [][]interface{}{}
	cond1300 := p.matchLookaheadLiteral("(", 0)
	for cond1300 {
		_t2054 := p.parse_iceberg_property_entry()
		item1301 := _t2054
		xs1299 = append(xs1299, item1301)
		cond1300 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1302 := xs1299
	p.consumeLiteral(")")
	var _t2055 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2056 := p.parse_config_dict()
		_t2055 = _t2056
	}
	config_dict1303 := _t2055
	p.consumeLiteral(")")
	_t2057 := p.construct_export_iceberg_config_full(iceberg_locator1293, iceberg_catalog_config1294, iceberg_export_columns1298, iceberg_property_entrys1302, config_dict1303)
	result1305 := _t2057
	p.recordSpan(int(span_start1304), "ExportIcebergConfig")
	return result1305
}

func (p *Parser) parse_iceberg_export_column() *pb.ExportIcebergColumn {
	span_start1310 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_column")
	string1306 := p.consumeTerminal("STRING").Value.str
	_t2058 := p.parse_relation_id()
	relation_id1307 := _t2058
	_t2059 := p.parse_type()
	type1308 := _t2059
	_t2060 := p.parse_boolean_value()
	boolean_value1309 := _t2060
	p.consumeLiteral(")")
	_t2061 := &pb.ExportIcebergColumn{Name: string1306, ColumnData: relation_id1307, Type: type1308, Nullable: boolean_value1309}
	result1311 := _t2061
	p.recordSpan(int(span_start1310), "ExportIcebergColumn")
	return result1311
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
