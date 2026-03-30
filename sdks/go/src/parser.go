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
	var _t2103 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2103
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2104 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2104
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2105 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2105
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2106 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2106
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2107 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2107
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2108 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2108
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2109 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2109
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2110 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2110
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2111 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2111
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2112 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2112
	_t2113 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2113
	_t2114 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2114
	_t2115 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2115
	_t2116 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2116
	_t2117 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2117
	_t2118 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2118
	_t2119 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2119
	_t2120 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2120
	_t2121 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2121
	_t2122 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2122
	_t2123 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2123
	_t2124 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2124
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2125 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2125
	_t2126 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2126
	_t2127 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2127
	_t2128 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2128
	_t2129 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2129
	_t2130 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2130
	_t2131 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2131
	_t2132 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2132
	_t2133 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2133
	_t2134 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2134.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2134.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2134
	_t2135 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2135
}

func (p *Parser) default_configure() *pb.Configure {
	_t2136 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2136
	_t2137 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2137
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
	_t2138 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2138
	_t2139 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2139
	_t2140 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2140
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2141 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2141
	_t2142 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2142
	_t2143 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2143
	_t2144 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2144
	_t2145 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2145
	_t2146 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2146
	_t2147 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2147
	_t2148 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2148
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2149 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2149
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2150 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2150
}

func (p *Parser) construct_iceberg_locator(table_name string, namespace []string, warehouse string, from_snapshot_opt *string, to_snapshot_opt *string) *pb.IcebergLocator {
	_t2151 := &pb.IcebergLocator{TableName: table_name, Namespace: namespace, Warehouse: warehouse, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, ""))}
	return _t2151
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportGNFColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2152 := config_dict
	if config_dict == nil {
		_t2152 = [][]interface{}{}
	}
	cfg := dictFromList(_t2152)
	_t2153 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2153
	_t2154 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2154
	_t2155 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2155
	table_props := stringMapFromPairs(table_property_pairs)
	_t2156 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2156
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start677 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1342 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1343 := p.parse_configure()
		_t1342 = _t1343
	}
	configure671 := _t1342
	var _t1344 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1345 := p.parse_sync()
		_t1344 = _t1345
	}
	sync672 := _t1344
	xs673 := []*pb.Epoch{}
	cond674 := p.matchLookaheadLiteral("(", 0)
	for cond674 {
		_t1346 := p.parse_epoch()
		item675 := _t1346
		xs673 = append(xs673, item675)
		cond674 = p.matchLookaheadLiteral("(", 0)
	}
	epochs676 := xs673
	p.consumeLiteral(")")
	_t1347 := p.default_configure()
	_t1348 := configure671
	if configure671 == nil {
		_t1348 = _t1347
	}
	_t1349 := &pb.Transaction{Epochs: epochs676, Configure: _t1348, Sync: sync672}
	result678 := _t1349
	p.recordSpan(int(span_start677), "Transaction")
	return result678
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start680 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1350 := p.parse_config_dict()
	config_dict679 := _t1350
	p.consumeLiteral(")")
	_t1351 := p.construct_configure(config_dict679)
	result681 := _t1351
	p.recordSpan(int(span_start680), "Configure")
	return result681
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs682 := [][]interface{}{}
	cond683 := p.matchLookaheadLiteral(":", 0)
	for cond683 {
		_t1352 := p.parse_config_key_value()
		item684 := _t1352
		xs682 = append(xs682, item684)
		cond683 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values685 := xs682
	p.consumeLiteral("}")
	return config_key_values685
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol686 := p.consumeTerminal("SYMBOL").Value.str
	_t1353 := p.parse_raw_value()
	raw_value687 := _t1353
	return []interface{}{symbol686, raw_value687}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start701 := int64(p.spanStart())
	var _t1354 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1354 = 12
	} else {
		var _t1355 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1355 = 11
		} else {
			var _t1356 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1356 = 12
			} else {
				var _t1357 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1358 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1358 = 1
					} else {
						var _t1359 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1359 = 0
						} else {
							_t1359 = -1
						}
						_t1358 = _t1359
					}
					_t1357 = _t1358
				} else {
					var _t1360 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1360 = 7
					} else {
						var _t1361 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1361 = 8
						} else {
							var _t1362 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1362 = 2
							} else {
								var _t1363 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1363 = 3
								} else {
									var _t1364 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1364 = 9
									} else {
										var _t1365 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1365 = 4
										} else {
											var _t1366 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1366 = 5
											} else {
												var _t1367 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1367 = 6
												} else {
													var _t1368 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1368 = 10
													} else {
														_t1368 = -1
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
							_t1361 = _t1362
						}
						_t1360 = _t1361
					}
					_t1357 = _t1360
				}
				_t1356 = _t1357
			}
			_t1355 = _t1356
		}
		_t1354 = _t1355
	}
	prediction688 := _t1354
	var _t1369 *pb.Value
	if prediction688 == 12 {
		_t1370 := p.parse_boolean_value()
		boolean_value700 := _t1370
		_t1371 := &pb.Value{}
		_t1371.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value700}
		_t1369 = _t1371
	} else {
		var _t1372 *pb.Value
		if prediction688 == 11 {
			p.consumeLiteral("missing")
			_t1373 := &pb.MissingValue{}
			_t1374 := &pb.Value{}
			_t1374.Value = &pb.Value_MissingValue{MissingValue: _t1373}
			_t1372 = _t1374
		} else {
			var _t1375 *pb.Value
			if prediction688 == 10 {
				decimal699 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1376 := &pb.Value{}
				_t1376.Value = &pb.Value_DecimalValue{DecimalValue: decimal699}
				_t1375 = _t1376
			} else {
				var _t1377 *pb.Value
				if prediction688 == 9 {
					int128698 := p.consumeTerminal("INT128").Value.int128
					_t1378 := &pb.Value{}
					_t1378.Value = &pb.Value_Int128Value{Int128Value: int128698}
					_t1377 = _t1378
				} else {
					var _t1379 *pb.Value
					if prediction688 == 8 {
						uint128697 := p.consumeTerminal("UINT128").Value.uint128
						_t1380 := &pb.Value{}
						_t1380.Value = &pb.Value_Uint128Value{Uint128Value: uint128697}
						_t1379 = _t1380
					} else {
						var _t1381 *pb.Value
						if prediction688 == 7 {
							uint32696 := p.consumeTerminal("UINT32").Value.u32
							_t1382 := &pb.Value{}
							_t1382.Value = &pb.Value_Uint32Value{Uint32Value: uint32696}
							_t1381 = _t1382
						} else {
							var _t1383 *pb.Value
							if prediction688 == 6 {
								float695 := p.consumeTerminal("FLOAT").Value.f64
								_t1384 := &pb.Value{}
								_t1384.Value = &pb.Value_FloatValue{FloatValue: float695}
								_t1383 = _t1384
							} else {
								var _t1385 *pb.Value
								if prediction688 == 5 {
									float32694 := p.consumeTerminal("FLOAT32").Value.f32
									_t1386 := &pb.Value{}
									_t1386.Value = &pb.Value_Float32Value{Float32Value: float32694}
									_t1385 = _t1386
								} else {
									var _t1387 *pb.Value
									if prediction688 == 4 {
										int693 := p.consumeTerminal("INT").Value.i64
										_t1388 := &pb.Value{}
										_t1388.Value = &pb.Value_IntValue{IntValue: int693}
										_t1387 = _t1388
									} else {
										var _t1389 *pb.Value
										if prediction688 == 3 {
											int32692 := p.consumeTerminal("INT32").Value.i32
											_t1390 := &pb.Value{}
											_t1390.Value = &pb.Value_Int32Value{Int32Value: int32692}
											_t1389 = _t1390
										} else {
											var _t1391 *pb.Value
											if prediction688 == 2 {
												string691 := p.consumeTerminal("STRING").Value.str
												_t1392 := &pb.Value{}
												_t1392.Value = &pb.Value_StringValue{StringValue: string691}
												_t1391 = _t1392
											} else {
												var _t1393 *pb.Value
												if prediction688 == 1 {
													_t1394 := p.parse_raw_datetime()
													raw_datetime690 := _t1394
													_t1395 := &pb.Value{}
													_t1395.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime690}
													_t1393 = _t1395
												} else {
													var _t1396 *pb.Value
													if prediction688 == 0 {
														_t1397 := p.parse_raw_date()
														raw_date689 := _t1397
														_t1398 := &pb.Value{}
														_t1398.Value = &pb.Value_DateValue{DateValue: raw_date689}
														_t1396 = _t1398
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1393 = _t1396
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
				_t1375 = _t1377
			}
			_t1372 = _t1375
		}
		_t1369 = _t1372
	}
	result702 := _t1369
	p.recordSpan(int(span_start701), "Value")
	return result702
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start706 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int703 := p.consumeTerminal("INT").Value.i64
	int_3704 := p.consumeTerminal("INT").Value.i64
	int_4705 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1399 := &pb.DateValue{Year: int32(int703), Month: int32(int_3704), Day: int32(int_4705)}
	result707 := _t1399
	p.recordSpan(int(span_start706), "DateValue")
	return result707
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int708 := p.consumeTerminal("INT").Value.i64
	int_3709 := p.consumeTerminal("INT").Value.i64
	int_4710 := p.consumeTerminal("INT").Value.i64
	int_5711 := p.consumeTerminal("INT").Value.i64
	int_6712 := p.consumeTerminal("INT").Value.i64
	int_7713 := p.consumeTerminal("INT").Value.i64
	var _t1400 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1400 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8714 := _t1400
	p.consumeLiteral(")")
	_t1401 := &pb.DateTimeValue{Year: int32(int708), Month: int32(int_3709), Day: int32(int_4710), Hour: int32(int_5711), Minute: int32(int_6712), Second: int32(int_7713), Microsecond: int32(deref(int_8714, 0))}
	result716 := _t1401
	p.recordSpan(int(span_start715), "DateTimeValue")
	return result716
}

func (p *Parser) parse_boolean_value() bool {
	var _t1402 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1402 = 0
	} else {
		var _t1403 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1403 = 1
		} else {
			_t1403 = -1
		}
		_t1402 = _t1403
	}
	prediction717 := _t1402
	var _t1404 bool
	if prediction717 == 1 {
		p.consumeLiteral("false")
		_t1404 = false
	} else {
		var _t1405 bool
		if prediction717 == 0 {
			p.consumeLiteral("true")
			_t1405 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1404 = _t1405
	}
	return _t1404
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start722 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs718 := []*pb.FragmentId{}
	cond719 := p.matchLookaheadLiteral(":", 0)
	for cond719 {
		_t1406 := p.parse_fragment_id()
		item720 := _t1406
		xs718 = append(xs718, item720)
		cond719 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids721 := xs718
	p.consumeLiteral(")")
	_t1407 := &pb.Sync{Fragments: fragment_ids721}
	result723 := _t1407
	p.recordSpan(int(span_start722), "Sync")
	return result723
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol724 := p.consumeTerminal("SYMBOL").Value.str
	result726 := &pb.FragmentId{Id: []byte(symbol724)}
	p.recordSpan(int(span_start725), "FragmentId")
	return result726
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start729 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1408 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1409 := p.parse_epoch_writes()
		_t1408 = _t1409
	}
	epoch_writes727 := _t1408
	var _t1410 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1411 := p.parse_epoch_reads()
		_t1410 = _t1411
	}
	epoch_reads728 := _t1410
	p.consumeLiteral(")")
	_t1412 := epoch_writes727
	if epoch_writes727 == nil {
		_t1412 = []*pb.Write{}
	}
	_t1413 := epoch_reads728
	if epoch_reads728 == nil {
		_t1413 = []*pb.Read{}
	}
	_t1414 := &pb.Epoch{Writes: _t1412, Reads: _t1413}
	result730 := _t1414
	p.recordSpan(int(span_start729), "Epoch")
	return result730
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs731 := []*pb.Write{}
	cond732 := p.matchLookaheadLiteral("(", 0)
	for cond732 {
		_t1415 := p.parse_write()
		item733 := _t1415
		xs731 = append(xs731, item733)
		cond732 = p.matchLookaheadLiteral("(", 0)
	}
	writes734 := xs731
	p.consumeLiteral(")")
	return writes734
}

func (p *Parser) parse_write() *pb.Write {
	span_start740 := int64(p.spanStart())
	var _t1416 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1417 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1417 = 1
		} else {
			var _t1418 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1418 = 3
			} else {
				var _t1419 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1419 = 0
				} else {
					var _t1420 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1420 = 2
					} else {
						_t1420 = -1
					}
					_t1419 = _t1420
				}
				_t1418 = _t1419
			}
			_t1417 = _t1418
		}
		_t1416 = _t1417
	} else {
		_t1416 = -1
	}
	prediction735 := _t1416
	var _t1421 *pb.Write
	if prediction735 == 3 {
		_t1422 := p.parse_snapshot()
		snapshot739 := _t1422
		_t1423 := &pb.Write{}
		_t1423.WriteType = &pb.Write_Snapshot{Snapshot: snapshot739}
		_t1421 = _t1423
	} else {
		var _t1424 *pb.Write
		if prediction735 == 2 {
			_t1425 := p.parse_context()
			context738 := _t1425
			_t1426 := &pb.Write{}
			_t1426.WriteType = &pb.Write_Context{Context: context738}
			_t1424 = _t1426
		} else {
			var _t1427 *pb.Write
			if prediction735 == 1 {
				_t1428 := p.parse_undefine()
				undefine737 := _t1428
				_t1429 := &pb.Write{}
				_t1429.WriteType = &pb.Write_Undefine{Undefine: undefine737}
				_t1427 = _t1429
			} else {
				var _t1430 *pb.Write
				if prediction735 == 0 {
					_t1431 := p.parse_define()
					define736 := _t1431
					_t1432 := &pb.Write{}
					_t1432.WriteType = &pb.Write_Define{Define: define736}
					_t1430 = _t1432
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1427 = _t1430
			}
			_t1424 = _t1427
		}
		_t1421 = _t1424
	}
	result741 := _t1421
	p.recordSpan(int(span_start740), "Write")
	return result741
}

func (p *Parser) parse_define() *pb.Define {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1433 := p.parse_fragment()
	fragment742 := _t1433
	p.consumeLiteral(")")
	_t1434 := &pb.Define{Fragment: fragment742}
	result744 := _t1434
	p.recordSpan(int(span_start743), "Define")
	return result744
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start750 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1435 := p.parse_new_fragment_id()
	new_fragment_id745 := _t1435
	xs746 := []*pb.Declaration{}
	cond747 := p.matchLookaheadLiteral("(", 0)
	for cond747 {
		_t1436 := p.parse_declaration()
		item748 := _t1436
		xs746 = append(xs746, item748)
		cond747 = p.matchLookaheadLiteral("(", 0)
	}
	declarations749 := xs746
	p.consumeLiteral(")")
	result751 := p.constructFragment(new_fragment_id745, declarations749)
	p.recordSpan(int(span_start750), "Fragment")
	return result751
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start753 := int64(p.spanStart())
	_t1437 := p.parse_fragment_id()
	fragment_id752 := _t1437
	p.startFragment(fragment_id752)
	result754 := fragment_id752
	p.recordSpan(int(span_start753), "FragmentId")
	return result754
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start760 := int64(p.spanStart())
	var _t1438 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1439 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1439 = 3
		} else {
			var _t1440 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1440 = 2
			} else {
				var _t1441 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1441 = 3
				} else {
					var _t1442 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1442 = 0
					} else {
						var _t1443 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1443 = 3
						} else {
							var _t1444 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1444 = 3
							} else {
								var _t1445 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1445 = 1
								} else {
									_t1445 = -1
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
	} else {
		_t1438 = -1
	}
	prediction755 := _t1438
	var _t1446 *pb.Declaration
	if prediction755 == 3 {
		_t1447 := p.parse_data()
		data759 := _t1447
		_t1448 := &pb.Declaration{}
		_t1448.DeclarationType = &pb.Declaration_Data{Data: data759}
		_t1446 = _t1448
	} else {
		var _t1449 *pb.Declaration
		if prediction755 == 2 {
			_t1450 := p.parse_constraint()
			constraint758 := _t1450
			_t1451 := &pb.Declaration{}
			_t1451.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint758}
			_t1449 = _t1451
		} else {
			var _t1452 *pb.Declaration
			if prediction755 == 1 {
				_t1453 := p.parse_algorithm()
				algorithm757 := _t1453
				_t1454 := &pb.Declaration{}
				_t1454.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm757}
				_t1452 = _t1454
			} else {
				var _t1455 *pb.Declaration
				if prediction755 == 0 {
					_t1456 := p.parse_def()
					def756 := _t1456
					_t1457 := &pb.Declaration{}
					_t1457.DeclarationType = &pb.Declaration_Def{Def: def756}
					_t1455 = _t1457
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1452 = _t1455
			}
			_t1449 = _t1452
		}
		_t1446 = _t1449
	}
	result761 := _t1446
	p.recordSpan(int(span_start760), "Declaration")
	return result761
}

func (p *Parser) parse_def() *pb.Def {
	span_start765 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1458 := p.parse_relation_id()
	relation_id762 := _t1458
	_t1459 := p.parse_abstraction()
	abstraction763 := _t1459
	var _t1460 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1461 := p.parse_attrs()
		_t1460 = _t1461
	}
	attrs764 := _t1460
	p.consumeLiteral(")")
	_t1462 := attrs764
	if attrs764 == nil {
		_t1462 = []*pb.Attribute{}
	}
	_t1463 := &pb.Def{Name: relation_id762, Body: abstraction763, Attrs: _t1462}
	result766 := _t1463
	p.recordSpan(int(span_start765), "Def")
	return result766
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start770 := int64(p.spanStart())
	var _t1464 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1464 = 0
	} else {
		var _t1465 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1465 = 1
		} else {
			_t1465 = -1
		}
		_t1464 = _t1465
	}
	prediction767 := _t1464
	var _t1466 *pb.RelationId
	if prediction767 == 1 {
		uint128769 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128769
		_t1466 = &pb.RelationId{IdLow: uint128769.Low, IdHigh: uint128769.High}
	} else {
		var _t1467 *pb.RelationId
		if prediction767 == 0 {
			p.consumeLiteral(":")
			symbol768 := p.consumeTerminal("SYMBOL").Value.str
			_t1467 = p.relationIdFromString(symbol768)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1466 = _t1467
	}
	result771 := _t1466
	p.recordSpan(int(span_start770), "RelationId")
	return result771
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start774 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1468 := p.parse_bindings()
	bindings772 := _t1468
	_t1469 := p.parse_formula()
	formula773 := _t1469
	p.consumeLiteral(")")
	_t1470 := &pb.Abstraction{Vars: listConcat(bindings772[0].([]*pb.Binding), bindings772[1].([]*pb.Binding)), Value: formula773}
	result775 := _t1470
	p.recordSpan(int(span_start774), "Abstraction")
	return result775
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs776 := []*pb.Binding{}
	cond777 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond777 {
		_t1471 := p.parse_binding()
		item778 := _t1471
		xs776 = append(xs776, item778)
		cond777 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings779 := xs776
	var _t1472 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1473 := p.parse_value_bindings()
		_t1472 = _t1473
	}
	value_bindings780 := _t1472
	p.consumeLiteral("]")
	_t1474 := value_bindings780
	if value_bindings780 == nil {
		_t1474 = []*pb.Binding{}
	}
	return []interface{}{bindings779, _t1474}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start783 := int64(p.spanStart())
	symbol781 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1475 := p.parse_type()
	type782 := _t1475
	_t1476 := &pb.Var{Name: symbol781}
	_t1477 := &pb.Binding{Var: _t1476, Type: type782}
	result784 := _t1477
	p.recordSpan(int(span_start783), "Binding")
	return result784
}

func (p *Parser) parse_type() *pb.Type {
	span_start800 := int64(p.spanStart())
	var _t1478 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1478 = 0
	} else {
		var _t1479 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1479 = 13
		} else {
			var _t1480 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1480 = 4
			} else {
				var _t1481 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1481 = 1
				} else {
					var _t1482 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1482 = 8
					} else {
						var _t1483 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1483 = 11
						} else {
							var _t1484 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1484 = 5
							} else {
								var _t1485 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1485 = 2
								} else {
									var _t1486 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1486 = 12
									} else {
										var _t1487 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1487 = 3
										} else {
											var _t1488 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1488 = 7
											} else {
												var _t1489 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1489 = 6
												} else {
													var _t1490 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1490 = 10
													} else {
														var _t1491 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1491 = 9
														} else {
															_t1491 = -1
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
			_t1479 = _t1480
		}
		_t1478 = _t1479
	}
	prediction785 := _t1478
	var _t1492 *pb.Type
	if prediction785 == 13 {
		_t1493 := p.parse_uint32_type()
		uint32_type799 := _t1493
		_t1494 := &pb.Type{}
		_t1494.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type799}
		_t1492 = _t1494
	} else {
		var _t1495 *pb.Type
		if prediction785 == 12 {
			_t1496 := p.parse_float32_type()
			float32_type798 := _t1496
			_t1497 := &pb.Type{}
			_t1497.Type = &pb.Type_Float32Type{Float32Type: float32_type798}
			_t1495 = _t1497
		} else {
			var _t1498 *pb.Type
			if prediction785 == 11 {
				_t1499 := p.parse_int32_type()
				int32_type797 := _t1499
				_t1500 := &pb.Type{}
				_t1500.Type = &pb.Type_Int32Type{Int32Type: int32_type797}
				_t1498 = _t1500
			} else {
				var _t1501 *pb.Type
				if prediction785 == 10 {
					_t1502 := p.parse_boolean_type()
					boolean_type796 := _t1502
					_t1503 := &pb.Type{}
					_t1503.Type = &pb.Type_BooleanType{BooleanType: boolean_type796}
					_t1501 = _t1503
				} else {
					var _t1504 *pb.Type
					if prediction785 == 9 {
						_t1505 := p.parse_decimal_type()
						decimal_type795 := _t1505
						_t1506 := &pb.Type{}
						_t1506.Type = &pb.Type_DecimalType{DecimalType: decimal_type795}
						_t1504 = _t1506
					} else {
						var _t1507 *pb.Type
						if prediction785 == 8 {
							_t1508 := p.parse_missing_type()
							missing_type794 := _t1508
							_t1509 := &pb.Type{}
							_t1509.Type = &pb.Type_MissingType{MissingType: missing_type794}
							_t1507 = _t1509
						} else {
							var _t1510 *pb.Type
							if prediction785 == 7 {
								_t1511 := p.parse_datetime_type()
								datetime_type793 := _t1511
								_t1512 := &pb.Type{}
								_t1512.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type793}
								_t1510 = _t1512
							} else {
								var _t1513 *pb.Type
								if prediction785 == 6 {
									_t1514 := p.parse_date_type()
									date_type792 := _t1514
									_t1515 := &pb.Type{}
									_t1515.Type = &pb.Type_DateType{DateType: date_type792}
									_t1513 = _t1515
								} else {
									var _t1516 *pb.Type
									if prediction785 == 5 {
										_t1517 := p.parse_int128_type()
										int128_type791 := _t1517
										_t1518 := &pb.Type{}
										_t1518.Type = &pb.Type_Int128Type{Int128Type: int128_type791}
										_t1516 = _t1518
									} else {
										var _t1519 *pb.Type
										if prediction785 == 4 {
											_t1520 := p.parse_uint128_type()
											uint128_type790 := _t1520
											_t1521 := &pb.Type{}
											_t1521.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type790}
											_t1519 = _t1521
										} else {
											var _t1522 *pb.Type
											if prediction785 == 3 {
												_t1523 := p.parse_float_type()
												float_type789 := _t1523
												_t1524 := &pb.Type{}
												_t1524.Type = &pb.Type_FloatType{FloatType: float_type789}
												_t1522 = _t1524
											} else {
												var _t1525 *pb.Type
												if prediction785 == 2 {
													_t1526 := p.parse_int_type()
													int_type788 := _t1526
													_t1527 := &pb.Type{}
													_t1527.Type = &pb.Type_IntType{IntType: int_type788}
													_t1525 = _t1527
												} else {
													var _t1528 *pb.Type
													if prediction785 == 1 {
														_t1529 := p.parse_string_type()
														string_type787 := _t1529
														_t1530 := &pb.Type{}
														_t1530.Type = &pb.Type_StringType{StringType: string_type787}
														_t1528 = _t1530
													} else {
														var _t1531 *pb.Type
														if prediction785 == 0 {
															_t1532 := p.parse_unspecified_type()
															unspecified_type786 := _t1532
															_t1533 := &pb.Type{}
															_t1533.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type786}
															_t1531 = _t1533
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1501 = _t1504
				}
				_t1498 = _t1501
			}
			_t1495 = _t1498
		}
		_t1492 = _t1495
	}
	result801 := _t1492
	p.recordSpan(int(span_start800), "Type")
	return result801
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1534 := &pb.UnspecifiedType{}
	result803 := _t1534
	p.recordSpan(int(span_start802), "UnspecifiedType")
	return result803
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1535 := &pb.StringType{}
	result805 := _t1535
	p.recordSpan(int(span_start804), "StringType")
	return result805
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1536 := &pb.IntType{}
	result807 := _t1536
	p.recordSpan(int(span_start806), "IntType")
	return result807
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1537 := &pb.FloatType{}
	result809 := _t1537
	p.recordSpan(int(span_start808), "FloatType")
	return result809
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1538 := &pb.UInt128Type{}
	result811 := _t1538
	p.recordSpan(int(span_start810), "UInt128Type")
	return result811
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1539 := &pb.Int128Type{}
	result813 := _t1539
	p.recordSpan(int(span_start812), "Int128Type")
	return result813
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1540 := &pb.DateType{}
	result815 := _t1540
	p.recordSpan(int(span_start814), "DateType")
	return result815
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1541 := &pb.DateTimeType{}
	result817 := _t1541
	p.recordSpan(int(span_start816), "DateTimeType")
	return result817
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1542 := &pb.MissingType{}
	result819 := _t1542
	p.recordSpan(int(span_start818), "MissingType")
	return result819
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int820 := p.consumeTerminal("INT").Value.i64
	int_3821 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1543 := &pb.DecimalType{Precision: int32(int820), Scale: int32(int_3821)}
	result823 := _t1543
	p.recordSpan(int(span_start822), "DecimalType")
	return result823
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1544 := &pb.BooleanType{}
	result825 := _t1544
	p.recordSpan(int(span_start824), "BooleanType")
	return result825
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start826 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1545 := &pb.Int32Type{}
	result827 := _t1545
	p.recordSpan(int(span_start826), "Int32Type")
	return result827
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1546 := &pb.Float32Type{}
	result829 := _t1546
	p.recordSpan(int(span_start828), "Float32Type")
	return result829
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start830 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1547 := &pb.UInt32Type{}
	result831 := _t1547
	p.recordSpan(int(span_start830), "UInt32Type")
	return result831
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs832 := []*pb.Binding{}
	cond833 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond833 {
		_t1548 := p.parse_binding()
		item834 := _t1548
		xs832 = append(xs832, item834)
		cond833 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings835 := xs832
	return bindings835
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start850 := int64(p.spanStart())
	var _t1549 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1550 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1550 = 0
		} else {
			var _t1551 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1551 = 11
			} else {
				var _t1552 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1552 = 3
				} else {
					var _t1553 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1553 = 10
					} else {
						var _t1554 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1554 = 9
						} else {
							var _t1555 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1555 = 5
							} else {
								var _t1556 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1556 = 6
								} else {
									var _t1557 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1557 = 7
									} else {
										var _t1558 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1558 = 1
										} else {
											var _t1559 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1559 = 2
											} else {
												var _t1560 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1560 = 12
												} else {
													var _t1561 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1561 = 8
													} else {
														var _t1562 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1562 = 4
														} else {
															var _t1563 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1563 = 10
															} else {
																var _t1564 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1564 = 10
																} else {
																	var _t1565 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1565 = 10
																	} else {
																		var _t1566 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1566 = 10
																		} else {
																			var _t1567 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1567 = 10
																			} else {
																				var _t1568 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1568 = 10
																				} else {
																					var _t1569 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1569 = 10
																					} else {
																						var _t1570 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1570 = 10
																						} else {
																							var _t1571 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1571 = 10
																							} else {
																								_t1571 = -1
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
			}
			_t1550 = _t1551
		}
		_t1549 = _t1550
	} else {
		_t1549 = -1
	}
	prediction836 := _t1549
	var _t1572 *pb.Formula
	if prediction836 == 12 {
		_t1573 := p.parse_cast()
		cast849 := _t1573
		_t1574 := &pb.Formula{}
		_t1574.FormulaType = &pb.Formula_Cast{Cast: cast849}
		_t1572 = _t1574
	} else {
		var _t1575 *pb.Formula
		if prediction836 == 11 {
			_t1576 := p.parse_rel_atom()
			rel_atom848 := _t1576
			_t1577 := &pb.Formula{}
			_t1577.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom848}
			_t1575 = _t1577
		} else {
			var _t1578 *pb.Formula
			if prediction836 == 10 {
				_t1579 := p.parse_primitive()
				primitive847 := _t1579
				_t1580 := &pb.Formula{}
				_t1580.FormulaType = &pb.Formula_Primitive{Primitive: primitive847}
				_t1578 = _t1580
			} else {
				var _t1581 *pb.Formula
				if prediction836 == 9 {
					_t1582 := p.parse_pragma()
					pragma846 := _t1582
					_t1583 := &pb.Formula{}
					_t1583.FormulaType = &pb.Formula_Pragma{Pragma: pragma846}
					_t1581 = _t1583
				} else {
					var _t1584 *pb.Formula
					if prediction836 == 8 {
						_t1585 := p.parse_atom()
						atom845 := _t1585
						_t1586 := &pb.Formula{}
						_t1586.FormulaType = &pb.Formula_Atom{Atom: atom845}
						_t1584 = _t1586
					} else {
						var _t1587 *pb.Formula
						if prediction836 == 7 {
							_t1588 := p.parse_ffi()
							ffi844 := _t1588
							_t1589 := &pb.Formula{}
							_t1589.FormulaType = &pb.Formula_Ffi{Ffi: ffi844}
							_t1587 = _t1589
						} else {
							var _t1590 *pb.Formula
							if prediction836 == 6 {
								_t1591 := p.parse_not()
								not843 := _t1591
								_t1592 := &pb.Formula{}
								_t1592.FormulaType = &pb.Formula_Not{Not: not843}
								_t1590 = _t1592
							} else {
								var _t1593 *pb.Formula
								if prediction836 == 5 {
									_t1594 := p.parse_disjunction()
									disjunction842 := _t1594
									_t1595 := &pb.Formula{}
									_t1595.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction842}
									_t1593 = _t1595
								} else {
									var _t1596 *pb.Formula
									if prediction836 == 4 {
										_t1597 := p.parse_conjunction()
										conjunction841 := _t1597
										_t1598 := &pb.Formula{}
										_t1598.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction841}
										_t1596 = _t1598
									} else {
										var _t1599 *pb.Formula
										if prediction836 == 3 {
											_t1600 := p.parse_reduce()
											reduce840 := _t1600
											_t1601 := &pb.Formula{}
											_t1601.FormulaType = &pb.Formula_Reduce{Reduce: reduce840}
											_t1599 = _t1601
										} else {
											var _t1602 *pb.Formula
											if prediction836 == 2 {
												_t1603 := p.parse_exists()
												exists839 := _t1603
												_t1604 := &pb.Formula{}
												_t1604.FormulaType = &pb.Formula_Exists{Exists: exists839}
												_t1602 = _t1604
											} else {
												var _t1605 *pb.Formula
												if prediction836 == 1 {
													_t1606 := p.parse_false()
													false838 := _t1606
													_t1607 := &pb.Formula{}
													_t1607.FormulaType = &pb.Formula_Disjunction{Disjunction: false838}
													_t1605 = _t1607
												} else {
													var _t1608 *pb.Formula
													if prediction836 == 0 {
														_t1609 := p.parse_true()
														true837 := _t1609
														_t1610 := &pb.Formula{}
														_t1610.FormulaType = &pb.Formula_Conjunction{Conjunction: true837}
														_t1608 = _t1610
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1581 = _t1584
				}
				_t1578 = _t1581
			}
			_t1575 = _t1578
		}
		_t1572 = _t1575
	}
	result851 := _t1572
	p.recordSpan(int(span_start850), "Formula")
	return result851
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1611 := &pb.Conjunction{Args: []*pb.Formula{}}
	result853 := _t1611
	p.recordSpan(int(span_start852), "Conjunction")
	return result853
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1612 := &pb.Disjunction{Args: []*pb.Formula{}}
	result855 := _t1612
	p.recordSpan(int(span_start854), "Disjunction")
	return result855
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1613 := p.parse_bindings()
	bindings856 := _t1613
	_t1614 := p.parse_formula()
	formula857 := _t1614
	p.consumeLiteral(")")
	_t1615 := &pb.Abstraction{Vars: listConcat(bindings856[0].([]*pb.Binding), bindings856[1].([]*pb.Binding)), Value: formula857}
	_t1616 := &pb.Exists{Body: _t1615}
	result859 := _t1616
	p.recordSpan(int(span_start858), "Exists")
	return result859
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1617 := p.parse_abstraction()
	abstraction860 := _t1617
	_t1618 := p.parse_abstraction()
	abstraction_3861 := _t1618
	_t1619 := p.parse_terms()
	terms862 := _t1619
	p.consumeLiteral(")")
	_t1620 := &pb.Reduce{Op: abstraction860, Body: abstraction_3861, Terms: terms862}
	result864 := _t1620
	p.recordSpan(int(span_start863), "Reduce")
	return result864
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs865 := []*pb.Term{}
	cond866 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond866 {
		_t1621 := p.parse_term()
		item867 := _t1621
		xs865 = append(xs865, item867)
		cond866 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms868 := xs865
	p.consumeLiteral(")")
	return terms868
}

func (p *Parser) parse_term() *pb.Term {
	span_start872 := int64(p.spanStart())
	var _t1622 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1622 = 1
	} else {
		var _t1623 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1623 = 1
		} else {
			var _t1624 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1624 = 1
			} else {
				var _t1625 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1625 = 1
				} else {
					var _t1626 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1626 = 0
					} else {
						var _t1627 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1627 = 1
						} else {
							var _t1628 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1628 = 1
							} else {
								var _t1629 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1629 = 1
								} else {
									var _t1630 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1630 = 1
									} else {
										var _t1631 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1631 = 1
										} else {
											var _t1632 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1632 = 1
											} else {
												var _t1633 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1633 = 1
												} else {
													var _t1634 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1634 = 1
													} else {
														var _t1635 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1635 = 1
														} else {
															_t1635 = -1
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
			_t1623 = _t1624
		}
		_t1622 = _t1623
	}
	prediction869 := _t1622
	var _t1636 *pb.Term
	if prediction869 == 1 {
		_t1637 := p.parse_value()
		value871 := _t1637
		_t1638 := &pb.Term{}
		_t1638.TermType = &pb.Term_Constant{Constant: value871}
		_t1636 = _t1638
	} else {
		var _t1639 *pb.Term
		if prediction869 == 0 {
			_t1640 := p.parse_var()
			var870 := _t1640
			_t1641 := &pb.Term{}
			_t1641.TermType = &pb.Term_Var{Var: var870}
			_t1639 = _t1641
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1636 = _t1639
	}
	result873 := _t1636
	p.recordSpan(int(span_start872), "Term")
	return result873
}

func (p *Parser) parse_var() *pb.Var {
	span_start875 := int64(p.spanStart())
	symbol874 := p.consumeTerminal("SYMBOL").Value.str
	_t1642 := &pb.Var{Name: symbol874}
	result876 := _t1642
	p.recordSpan(int(span_start875), "Var")
	return result876
}

func (p *Parser) parse_value() *pb.Value {
	span_start890 := int64(p.spanStart())
	var _t1643 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1643 = 12
	} else {
		var _t1644 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1644 = 11
		} else {
			var _t1645 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1645 = 12
			} else {
				var _t1646 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1647 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1647 = 1
					} else {
						var _t1648 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1648 = 0
						} else {
							_t1648 = -1
						}
						_t1647 = _t1648
					}
					_t1646 = _t1647
				} else {
					var _t1649 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1649 = 7
					} else {
						var _t1650 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1650 = 8
						} else {
							var _t1651 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1651 = 2
							} else {
								var _t1652 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1652 = 3
								} else {
									var _t1653 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1653 = 9
									} else {
										var _t1654 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1654 = 4
										} else {
											var _t1655 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1655 = 5
											} else {
												var _t1656 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1656 = 6
												} else {
													var _t1657 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1657 = 10
													} else {
														_t1657 = -1
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
							_t1650 = _t1651
						}
						_t1649 = _t1650
					}
					_t1646 = _t1649
				}
				_t1645 = _t1646
			}
			_t1644 = _t1645
		}
		_t1643 = _t1644
	}
	prediction877 := _t1643
	var _t1658 *pb.Value
	if prediction877 == 12 {
		_t1659 := p.parse_boolean_value()
		boolean_value889 := _t1659
		_t1660 := &pb.Value{}
		_t1660.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value889}
		_t1658 = _t1660
	} else {
		var _t1661 *pb.Value
		if prediction877 == 11 {
			p.consumeLiteral("missing")
			_t1662 := &pb.MissingValue{}
			_t1663 := &pb.Value{}
			_t1663.Value = &pb.Value_MissingValue{MissingValue: _t1662}
			_t1661 = _t1663
		} else {
			var _t1664 *pb.Value
			if prediction877 == 10 {
				formatted_decimal888 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1665 := &pb.Value{}
				_t1665.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal888}
				_t1664 = _t1665
			} else {
				var _t1666 *pb.Value
				if prediction877 == 9 {
					formatted_int128887 := p.consumeTerminal("INT128").Value.int128
					_t1667 := &pb.Value{}
					_t1667.Value = &pb.Value_Int128Value{Int128Value: formatted_int128887}
					_t1666 = _t1667
				} else {
					var _t1668 *pb.Value
					if prediction877 == 8 {
						formatted_uint128886 := p.consumeTerminal("UINT128").Value.uint128
						_t1669 := &pb.Value{}
						_t1669.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128886}
						_t1668 = _t1669
					} else {
						var _t1670 *pb.Value
						if prediction877 == 7 {
							formatted_uint32885 := p.consumeTerminal("UINT32").Value.u32
							_t1671 := &pb.Value{}
							_t1671.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32885}
							_t1670 = _t1671
						} else {
							var _t1672 *pb.Value
							if prediction877 == 6 {
								formatted_float884 := p.consumeTerminal("FLOAT").Value.f64
								_t1673 := &pb.Value{}
								_t1673.Value = &pb.Value_FloatValue{FloatValue: formatted_float884}
								_t1672 = _t1673
							} else {
								var _t1674 *pb.Value
								if prediction877 == 5 {
									formatted_float32883 := p.consumeTerminal("FLOAT32").Value.f32
									_t1675 := &pb.Value{}
									_t1675.Value = &pb.Value_Float32Value{Float32Value: formatted_float32883}
									_t1674 = _t1675
								} else {
									var _t1676 *pb.Value
									if prediction877 == 4 {
										formatted_int882 := p.consumeTerminal("INT").Value.i64
										_t1677 := &pb.Value{}
										_t1677.Value = &pb.Value_IntValue{IntValue: formatted_int882}
										_t1676 = _t1677
									} else {
										var _t1678 *pb.Value
										if prediction877 == 3 {
											formatted_int32881 := p.consumeTerminal("INT32").Value.i32
											_t1679 := &pb.Value{}
											_t1679.Value = &pb.Value_Int32Value{Int32Value: formatted_int32881}
											_t1678 = _t1679
										} else {
											var _t1680 *pb.Value
											if prediction877 == 2 {
												formatted_string880 := p.consumeTerminal("STRING").Value.str
												_t1681 := &pb.Value{}
												_t1681.Value = &pb.Value_StringValue{StringValue: formatted_string880}
												_t1680 = _t1681
											} else {
												var _t1682 *pb.Value
												if prediction877 == 1 {
													_t1683 := p.parse_datetime()
													datetime879 := _t1683
													_t1684 := &pb.Value{}
													_t1684.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime879}
													_t1682 = _t1684
												} else {
													var _t1685 *pb.Value
													if prediction877 == 0 {
														_t1686 := p.parse_date()
														date878 := _t1686
														_t1687 := &pb.Value{}
														_t1687.Value = &pb.Value_DateValue{DateValue: date878}
														_t1685 = _t1687
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1682 = _t1685
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
				_t1664 = _t1666
			}
			_t1661 = _t1664
		}
		_t1658 = _t1661
	}
	result891 := _t1658
	p.recordSpan(int(span_start890), "Value")
	return result891
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int892 := p.consumeTerminal("INT").Value.i64
	formatted_int_3893 := p.consumeTerminal("INT").Value.i64
	formatted_int_4894 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1688 := &pb.DateValue{Year: int32(formatted_int892), Month: int32(formatted_int_3893), Day: int32(formatted_int_4894)}
	result896 := _t1688
	p.recordSpan(int(span_start895), "DateValue")
	return result896
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int897 := p.consumeTerminal("INT").Value.i64
	formatted_int_3898 := p.consumeTerminal("INT").Value.i64
	formatted_int_4899 := p.consumeTerminal("INT").Value.i64
	formatted_int_5900 := p.consumeTerminal("INT").Value.i64
	formatted_int_6901 := p.consumeTerminal("INT").Value.i64
	formatted_int_7902 := p.consumeTerminal("INT").Value.i64
	var _t1689 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1689 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8903 := _t1689
	p.consumeLiteral(")")
	_t1690 := &pb.DateTimeValue{Year: int32(formatted_int897), Month: int32(formatted_int_3898), Day: int32(formatted_int_4899), Hour: int32(formatted_int_5900), Minute: int32(formatted_int_6901), Second: int32(formatted_int_7902), Microsecond: int32(deref(formatted_int_8903, 0))}
	result905 := _t1690
	p.recordSpan(int(span_start904), "DateTimeValue")
	return result905
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start910 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs906 := []*pb.Formula{}
	cond907 := p.matchLookaheadLiteral("(", 0)
	for cond907 {
		_t1691 := p.parse_formula()
		item908 := _t1691
		xs906 = append(xs906, item908)
		cond907 = p.matchLookaheadLiteral("(", 0)
	}
	formulas909 := xs906
	p.consumeLiteral(")")
	_t1692 := &pb.Conjunction{Args: formulas909}
	result911 := _t1692
	p.recordSpan(int(span_start910), "Conjunction")
	return result911
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start916 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs912 := []*pb.Formula{}
	cond913 := p.matchLookaheadLiteral("(", 0)
	for cond913 {
		_t1693 := p.parse_formula()
		item914 := _t1693
		xs912 = append(xs912, item914)
		cond913 = p.matchLookaheadLiteral("(", 0)
	}
	formulas915 := xs912
	p.consumeLiteral(")")
	_t1694 := &pb.Disjunction{Args: formulas915}
	result917 := _t1694
	p.recordSpan(int(span_start916), "Disjunction")
	return result917
}

func (p *Parser) parse_not() *pb.Not {
	span_start919 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1695 := p.parse_formula()
	formula918 := _t1695
	p.consumeLiteral(")")
	_t1696 := &pb.Not{Arg: formula918}
	result920 := _t1696
	p.recordSpan(int(span_start919), "Not")
	return result920
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start924 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1697 := p.parse_name()
	name921 := _t1697
	_t1698 := p.parse_ffi_args()
	ffi_args922 := _t1698
	_t1699 := p.parse_terms()
	terms923 := _t1699
	p.consumeLiteral(")")
	_t1700 := &pb.FFI{Name: name921, Args: ffi_args922, Terms: terms923}
	result925 := _t1700
	p.recordSpan(int(span_start924), "FFI")
	return result925
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol926 := p.consumeTerminal("SYMBOL").Value.str
	return symbol926
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs927 := []*pb.Abstraction{}
	cond928 := p.matchLookaheadLiteral("(", 0)
	for cond928 {
		_t1701 := p.parse_abstraction()
		item929 := _t1701
		xs927 = append(xs927, item929)
		cond928 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions930 := xs927
	p.consumeLiteral(")")
	return abstractions930
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start936 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1702 := p.parse_relation_id()
	relation_id931 := _t1702
	xs932 := []*pb.Term{}
	cond933 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond933 {
		_t1703 := p.parse_term()
		item934 := _t1703
		xs932 = append(xs932, item934)
		cond933 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms935 := xs932
	p.consumeLiteral(")")
	_t1704 := &pb.Atom{Name: relation_id931, Terms: terms935}
	result937 := _t1704
	p.recordSpan(int(span_start936), "Atom")
	return result937
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start943 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1705 := p.parse_name()
	name938 := _t1705
	xs939 := []*pb.Term{}
	cond940 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond940 {
		_t1706 := p.parse_term()
		item941 := _t1706
		xs939 = append(xs939, item941)
		cond940 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms942 := xs939
	p.consumeLiteral(")")
	_t1707 := &pb.Pragma{Name: name938, Terms: terms942}
	result944 := _t1707
	p.recordSpan(int(span_start943), "Pragma")
	return result944
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start960 := int64(p.spanStart())
	var _t1708 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1709 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1709 = 9
		} else {
			var _t1710 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1710 = 4
			} else {
				var _t1711 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1711 = 3
				} else {
					var _t1712 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1712 = 0
					} else {
						var _t1713 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1713 = 2
						} else {
							var _t1714 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1714 = 1
							} else {
								var _t1715 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1715 = 8
								} else {
									var _t1716 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1716 = 6
									} else {
										var _t1717 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1717 = 5
										} else {
											var _t1718 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1718 = 7
											} else {
												_t1718 = -1
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
			}
			_t1709 = _t1710
		}
		_t1708 = _t1709
	} else {
		_t1708 = -1
	}
	prediction945 := _t1708
	var _t1719 *pb.Primitive
	if prediction945 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1720 := p.parse_name()
		name955 := _t1720
		xs956 := []*pb.RelTerm{}
		cond957 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond957 {
			_t1721 := p.parse_rel_term()
			item958 := _t1721
			xs956 = append(xs956, item958)
			cond957 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms959 := xs956
		p.consumeLiteral(")")
		_t1722 := &pb.Primitive{Name: name955, Terms: rel_terms959}
		_t1719 = _t1722
	} else {
		var _t1723 *pb.Primitive
		if prediction945 == 8 {
			_t1724 := p.parse_divide()
			divide954 := _t1724
			_t1723 = divide954
		} else {
			var _t1725 *pb.Primitive
			if prediction945 == 7 {
				_t1726 := p.parse_multiply()
				multiply953 := _t1726
				_t1725 = multiply953
			} else {
				var _t1727 *pb.Primitive
				if prediction945 == 6 {
					_t1728 := p.parse_minus()
					minus952 := _t1728
					_t1727 = minus952
				} else {
					var _t1729 *pb.Primitive
					if prediction945 == 5 {
						_t1730 := p.parse_add()
						add951 := _t1730
						_t1729 = add951
					} else {
						var _t1731 *pb.Primitive
						if prediction945 == 4 {
							_t1732 := p.parse_gt_eq()
							gt_eq950 := _t1732
							_t1731 = gt_eq950
						} else {
							var _t1733 *pb.Primitive
							if prediction945 == 3 {
								_t1734 := p.parse_gt()
								gt949 := _t1734
								_t1733 = gt949
							} else {
								var _t1735 *pb.Primitive
								if prediction945 == 2 {
									_t1736 := p.parse_lt_eq()
									lt_eq948 := _t1736
									_t1735 = lt_eq948
								} else {
									var _t1737 *pb.Primitive
									if prediction945 == 1 {
										_t1738 := p.parse_lt()
										lt947 := _t1738
										_t1737 = lt947
									} else {
										var _t1739 *pb.Primitive
										if prediction945 == 0 {
											_t1740 := p.parse_eq()
											eq946 := _t1740
											_t1739 = eq946
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1723 = _t1725
		}
		_t1719 = _t1723
	}
	result961 := _t1719
	p.recordSpan(int(span_start960), "Primitive")
	return result961
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start964 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1741 := p.parse_term()
	term962 := _t1741
	_t1742 := p.parse_term()
	term_3963 := _t1742
	p.consumeLiteral(")")
	_t1743 := &pb.RelTerm{}
	_t1743.RelTermType = &pb.RelTerm_Term{Term: term962}
	_t1744 := &pb.RelTerm{}
	_t1744.RelTermType = &pb.RelTerm_Term{Term: term_3963}
	_t1745 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1743, _t1744}}
	result965 := _t1745
	p.recordSpan(int(span_start964), "Primitive")
	return result965
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1746 := p.parse_term()
	term966 := _t1746
	_t1747 := p.parse_term()
	term_3967 := _t1747
	p.consumeLiteral(")")
	_t1748 := &pb.RelTerm{}
	_t1748.RelTermType = &pb.RelTerm_Term{Term: term966}
	_t1749 := &pb.RelTerm{}
	_t1749.RelTermType = &pb.RelTerm_Term{Term: term_3967}
	_t1750 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1748, _t1749}}
	result969 := _t1750
	p.recordSpan(int(span_start968), "Primitive")
	return result969
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1751 := p.parse_term()
	term970 := _t1751
	_t1752 := p.parse_term()
	term_3971 := _t1752
	p.consumeLiteral(")")
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term970}
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term_3971}
	_t1755 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1753, _t1754}}
	result973 := _t1755
	p.recordSpan(int(span_start972), "Primitive")
	return result973
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1756 := p.parse_term()
	term974 := _t1756
	_t1757 := p.parse_term()
	term_3975 := _t1757
	p.consumeLiteral(")")
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term974}
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term_3975}
	_t1760 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1758, _t1759}}
	result977 := _t1760
	p.recordSpan(int(span_start976), "Primitive")
	return result977
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1761 := p.parse_term()
	term978 := _t1761
	_t1762 := p.parse_term()
	term_3979 := _t1762
	p.consumeLiteral(")")
	_t1763 := &pb.RelTerm{}
	_t1763.RelTermType = &pb.RelTerm_Term{Term: term978}
	_t1764 := &pb.RelTerm{}
	_t1764.RelTermType = &pb.RelTerm_Term{Term: term_3979}
	_t1765 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1763, _t1764}}
	result981 := _t1765
	p.recordSpan(int(span_start980), "Primitive")
	return result981
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start985 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1766 := p.parse_term()
	term982 := _t1766
	_t1767 := p.parse_term()
	term_3983 := _t1767
	_t1768 := p.parse_term()
	term_4984 := _t1768
	p.consumeLiteral(")")
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term982}
	_t1770 := &pb.RelTerm{}
	_t1770.RelTermType = &pb.RelTerm_Term{Term: term_3983}
	_t1771 := &pb.RelTerm{}
	_t1771.RelTermType = &pb.RelTerm_Term{Term: term_4984}
	_t1772 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1769, _t1770, _t1771}}
	result986 := _t1772
	p.recordSpan(int(span_start985), "Primitive")
	return result986
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start990 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1773 := p.parse_term()
	term987 := _t1773
	_t1774 := p.parse_term()
	term_3988 := _t1774
	_t1775 := p.parse_term()
	term_4989 := _t1775
	p.consumeLiteral(")")
	_t1776 := &pb.RelTerm{}
	_t1776.RelTermType = &pb.RelTerm_Term{Term: term987}
	_t1777 := &pb.RelTerm{}
	_t1777.RelTermType = &pb.RelTerm_Term{Term: term_3988}
	_t1778 := &pb.RelTerm{}
	_t1778.RelTermType = &pb.RelTerm_Term{Term: term_4989}
	_t1779 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1776, _t1777, _t1778}}
	result991 := _t1779
	p.recordSpan(int(span_start990), "Primitive")
	return result991
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start995 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1780 := p.parse_term()
	term992 := _t1780
	_t1781 := p.parse_term()
	term_3993 := _t1781
	_t1782 := p.parse_term()
	term_4994 := _t1782
	p.consumeLiteral(")")
	_t1783 := &pb.RelTerm{}
	_t1783.RelTermType = &pb.RelTerm_Term{Term: term992}
	_t1784 := &pb.RelTerm{}
	_t1784.RelTermType = &pb.RelTerm_Term{Term: term_3993}
	_t1785 := &pb.RelTerm{}
	_t1785.RelTermType = &pb.RelTerm_Term{Term: term_4994}
	_t1786 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1783, _t1784, _t1785}}
	result996 := _t1786
	p.recordSpan(int(span_start995), "Primitive")
	return result996
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start1000 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1787 := p.parse_term()
	term997 := _t1787
	_t1788 := p.parse_term()
	term_3998 := _t1788
	_t1789 := p.parse_term()
	term_4999 := _t1789
	p.consumeLiteral(")")
	_t1790 := &pb.RelTerm{}
	_t1790.RelTermType = &pb.RelTerm_Term{Term: term997}
	_t1791 := &pb.RelTerm{}
	_t1791.RelTermType = &pb.RelTerm_Term{Term: term_3998}
	_t1792 := &pb.RelTerm{}
	_t1792.RelTermType = &pb.RelTerm_Term{Term: term_4999}
	_t1793 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1790, _t1791, _t1792}}
	result1001 := _t1793
	p.recordSpan(int(span_start1000), "Primitive")
	return result1001
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start1005 := int64(p.spanStart())
	var _t1794 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1794 = 1
	} else {
		var _t1795 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1795 = 1
		} else {
			var _t1796 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1796 = 1
			} else {
				var _t1797 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1797 = 1
				} else {
					var _t1798 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1798 = 0
					} else {
						var _t1799 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1799 = 1
						} else {
							var _t1800 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1800 = 1
							} else {
								var _t1801 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1801 = 1
								} else {
									var _t1802 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1802 = 1
									} else {
										var _t1803 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1803 = 1
										} else {
											var _t1804 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1804 = 1
											} else {
												var _t1805 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1805 = 1
												} else {
													var _t1806 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1806 = 1
													} else {
														var _t1807 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1807 = 1
														} else {
															var _t1808 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1808 = 1
															} else {
																_t1808 = -1
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
			_t1795 = _t1796
		}
		_t1794 = _t1795
	}
	prediction1002 := _t1794
	var _t1809 *pb.RelTerm
	if prediction1002 == 1 {
		_t1810 := p.parse_term()
		term1004 := _t1810
		_t1811 := &pb.RelTerm{}
		_t1811.RelTermType = &pb.RelTerm_Term{Term: term1004}
		_t1809 = _t1811
	} else {
		var _t1812 *pb.RelTerm
		if prediction1002 == 0 {
			_t1813 := p.parse_specialized_value()
			specialized_value1003 := _t1813
			_t1814 := &pb.RelTerm{}
			_t1814.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1003}
			_t1812 = _t1814
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1809 = _t1812
	}
	result1006 := _t1809
	p.recordSpan(int(span_start1005), "RelTerm")
	return result1006
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1008 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1815 := p.parse_raw_value()
	raw_value1007 := _t1815
	result1009 := raw_value1007
	p.recordSpan(int(span_start1008), "Value")
	return result1009
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1015 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1816 := p.parse_name()
	name1010 := _t1816
	xs1011 := []*pb.RelTerm{}
	cond1012 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1012 {
		_t1817 := p.parse_rel_term()
		item1013 := _t1817
		xs1011 = append(xs1011, item1013)
		cond1012 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1014 := xs1011
	p.consumeLiteral(")")
	_t1818 := &pb.RelAtom{Name: name1010, Terms: rel_terms1014}
	result1016 := _t1818
	p.recordSpan(int(span_start1015), "RelAtom")
	return result1016
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1019 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1819 := p.parse_term()
	term1017 := _t1819
	_t1820 := p.parse_term()
	term_31018 := _t1820
	p.consumeLiteral(")")
	_t1821 := &pb.Cast{Input: term1017, Result: term_31018}
	result1020 := _t1821
	p.recordSpan(int(span_start1019), "Cast")
	return result1020
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1021 := []*pb.Attribute{}
	cond1022 := p.matchLookaheadLiteral("(", 0)
	for cond1022 {
		_t1822 := p.parse_attribute()
		item1023 := _t1822
		xs1021 = append(xs1021, item1023)
		cond1022 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1024 := xs1021
	p.consumeLiteral(")")
	return attributes1024
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1030 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1823 := p.parse_name()
	name1025 := _t1823
	xs1026 := []*pb.Value{}
	cond1027 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1027 {
		_t1824 := p.parse_raw_value()
		item1028 := _t1824
		xs1026 = append(xs1026, item1028)
		cond1027 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1029 := xs1026
	p.consumeLiteral(")")
	_t1825 := &pb.Attribute{Name: name1025, Args: raw_values1029}
	result1031 := _t1825
	p.recordSpan(int(span_start1030), "Attribute")
	return result1031
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1037 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1032 := []*pb.RelationId{}
	cond1033 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1033 {
		_t1826 := p.parse_relation_id()
		item1034 := _t1826
		xs1032 = append(xs1032, item1034)
		cond1033 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1035 := xs1032
	_t1827 := p.parse_script()
	script1036 := _t1827
	p.consumeLiteral(")")
	_t1828 := &pb.Algorithm{Global: relation_ids1035, Body: script1036}
	result1038 := _t1828
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
		_t1829 := p.parse_construct()
		item1041 := _t1829
		xs1039 = append(xs1039, item1041)
		cond1040 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1042 := xs1039
	p.consumeLiteral(")")
	_t1830 := &pb.Script{Constructs: constructs1042}
	result1044 := _t1830
	p.recordSpan(int(span_start1043), "Script")
	return result1044
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1048 := int64(p.spanStart())
	var _t1831 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1832 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1832 = 1
		} else {
			var _t1833 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1833 = 1
			} else {
				var _t1834 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1834 = 1
				} else {
					var _t1835 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1835 = 0
					} else {
						var _t1836 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1836 = 1
						} else {
							var _t1837 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1837 = 1
							} else {
								_t1837 = -1
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
		}
		_t1831 = _t1832
	} else {
		_t1831 = -1
	}
	prediction1045 := _t1831
	var _t1838 *pb.Construct
	if prediction1045 == 1 {
		_t1839 := p.parse_instruction()
		instruction1047 := _t1839
		_t1840 := &pb.Construct{}
		_t1840.ConstructType = &pb.Construct_Instruction{Instruction: instruction1047}
		_t1838 = _t1840
	} else {
		var _t1841 *pb.Construct
		if prediction1045 == 0 {
			_t1842 := p.parse_loop()
			loop1046 := _t1842
			_t1843 := &pb.Construct{}
			_t1843.ConstructType = &pb.Construct_Loop{Loop: loop1046}
			_t1841 = _t1843
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1838 = _t1841
	}
	result1049 := _t1838
	p.recordSpan(int(span_start1048), "Construct")
	return result1049
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1844 := p.parse_init()
	init1050 := _t1844
	_t1845 := p.parse_script()
	script1051 := _t1845
	p.consumeLiteral(")")
	_t1846 := &pb.Loop{Init: init1050, Body: script1051}
	result1053 := _t1846
	p.recordSpan(int(span_start1052), "Loop")
	return result1053
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1054 := []*pb.Instruction{}
	cond1055 := p.matchLookaheadLiteral("(", 0)
	for cond1055 {
		_t1847 := p.parse_instruction()
		item1056 := _t1847
		xs1054 = append(xs1054, item1056)
		cond1055 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1057 := xs1054
	p.consumeLiteral(")")
	return instructions1057
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1064 := int64(p.spanStart())
	var _t1848 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1849 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1849 = 1
		} else {
			var _t1850 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1850 = 4
			} else {
				var _t1851 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1851 = 3
				} else {
					var _t1852 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1852 = 2
					} else {
						var _t1853 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1853 = 0
						} else {
							_t1853 = -1
						}
						_t1852 = _t1853
					}
					_t1851 = _t1852
				}
				_t1850 = _t1851
			}
			_t1849 = _t1850
		}
		_t1848 = _t1849
	} else {
		_t1848 = -1
	}
	prediction1058 := _t1848
	var _t1854 *pb.Instruction
	if prediction1058 == 4 {
		_t1855 := p.parse_monus_def()
		monus_def1063 := _t1855
		_t1856 := &pb.Instruction{}
		_t1856.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1063}
		_t1854 = _t1856
	} else {
		var _t1857 *pb.Instruction
		if prediction1058 == 3 {
			_t1858 := p.parse_monoid_def()
			monoid_def1062 := _t1858
			_t1859 := &pb.Instruction{}
			_t1859.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1062}
			_t1857 = _t1859
		} else {
			var _t1860 *pb.Instruction
			if prediction1058 == 2 {
				_t1861 := p.parse_break()
				break1061 := _t1861
				_t1862 := &pb.Instruction{}
				_t1862.InstrType = &pb.Instruction_Break{Break: break1061}
				_t1860 = _t1862
			} else {
				var _t1863 *pb.Instruction
				if prediction1058 == 1 {
					_t1864 := p.parse_upsert()
					upsert1060 := _t1864
					_t1865 := &pb.Instruction{}
					_t1865.InstrType = &pb.Instruction_Upsert{Upsert: upsert1060}
					_t1863 = _t1865
				} else {
					var _t1866 *pb.Instruction
					if prediction1058 == 0 {
						_t1867 := p.parse_assign()
						assign1059 := _t1867
						_t1868 := &pb.Instruction{}
						_t1868.InstrType = &pb.Instruction_Assign{Assign: assign1059}
						_t1866 = _t1868
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1863 = _t1866
				}
				_t1860 = _t1863
			}
			_t1857 = _t1860
		}
		_t1854 = _t1857
	}
	result1065 := _t1854
	p.recordSpan(int(span_start1064), "Instruction")
	return result1065
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1069 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1869 := p.parse_relation_id()
	relation_id1066 := _t1869
	_t1870 := p.parse_abstraction()
	abstraction1067 := _t1870
	var _t1871 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1872 := p.parse_attrs()
		_t1871 = _t1872
	}
	attrs1068 := _t1871
	p.consumeLiteral(")")
	_t1873 := attrs1068
	if attrs1068 == nil {
		_t1873 = []*pb.Attribute{}
	}
	_t1874 := &pb.Assign{Name: relation_id1066, Body: abstraction1067, Attrs: _t1873}
	result1070 := _t1874
	p.recordSpan(int(span_start1069), "Assign")
	return result1070
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1875 := p.parse_relation_id()
	relation_id1071 := _t1875
	_t1876 := p.parse_abstraction_with_arity()
	abstraction_with_arity1072 := _t1876
	var _t1877 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1878 := p.parse_attrs()
		_t1877 = _t1878
	}
	attrs1073 := _t1877
	p.consumeLiteral(")")
	_t1879 := attrs1073
	if attrs1073 == nil {
		_t1879 = []*pb.Attribute{}
	}
	_t1880 := &pb.Upsert{Name: relation_id1071, Body: abstraction_with_arity1072[0].(*pb.Abstraction), Attrs: _t1879, ValueArity: abstraction_with_arity1072[1].(int64)}
	result1075 := _t1880
	p.recordSpan(int(span_start1074), "Upsert")
	return result1075
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1881 := p.parse_bindings()
	bindings1076 := _t1881
	_t1882 := p.parse_formula()
	formula1077 := _t1882
	p.consumeLiteral(")")
	_t1883 := &pb.Abstraction{Vars: listConcat(bindings1076[0].([]*pb.Binding), bindings1076[1].([]*pb.Binding)), Value: formula1077}
	return []interface{}{_t1883, int64(len(bindings1076[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1081 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1884 := p.parse_relation_id()
	relation_id1078 := _t1884
	_t1885 := p.parse_abstraction()
	abstraction1079 := _t1885
	var _t1886 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1887 := p.parse_attrs()
		_t1886 = _t1887
	}
	attrs1080 := _t1886
	p.consumeLiteral(")")
	_t1888 := attrs1080
	if attrs1080 == nil {
		_t1888 = []*pb.Attribute{}
	}
	_t1889 := &pb.Break{Name: relation_id1078, Body: abstraction1079, Attrs: _t1888}
	result1082 := _t1889
	p.recordSpan(int(span_start1081), "Break")
	return result1082
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1890 := p.parse_monoid()
	monoid1083 := _t1890
	_t1891 := p.parse_relation_id()
	relation_id1084 := _t1891
	_t1892 := p.parse_abstraction_with_arity()
	abstraction_with_arity1085 := _t1892
	var _t1893 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1894 := p.parse_attrs()
		_t1893 = _t1894
	}
	attrs1086 := _t1893
	p.consumeLiteral(")")
	_t1895 := attrs1086
	if attrs1086 == nil {
		_t1895 = []*pb.Attribute{}
	}
	_t1896 := &pb.MonoidDef{Monoid: monoid1083, Name: relation_id1084, Body: abstraction_with_arity1085[0].(*pb.Abstraction), Attrs: _t1895, ValueArity: abstraction_with_arity1085[1].(int64)}
	result1088 := _t1896
	p.recordSpan(int(span_start1087), "MonoidDef")
	return result1088
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1094 := int64(p.spanStart())
	var _t1897 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1898 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1898 = 3
		} else {
			var _t1899 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1899 = 0
			} else {
				var _t1900 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1900 = 1
				} else {
					var _t1901 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1901 = 2
					} else {
						_t1901 = -1
					}
					_t1900 = _t1901
				}
				_t1899 = _t1900
			}
			_t1898 = _t1899
		}
		_t1897 = _t1898
	} else {
		_t1897 = -1
	}
	prediction1089 := _t1897
	var _t1902 *pb.Monoid
	if prediction1089 == 3 {
		_t1903 := p.parse_sum_monoid()
		sum_monoid1093 := _t1903
		_t1904 := &pb.Monoid{}
		_t1904.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1093}
		_t1902 = _t1904
	} else {
		var _t1905 *pb.Monoid
		if prediction1089 == 2 {
			_t1906 := p.parse_max_monoid()
			max_monoid1092 := _t1906
			_t1907 := &pb.Monoid{}
			_t1907.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1092}
			_t1905 = _t1907
		} else {
			var _t1908 *pb.Monoid
			if prediction1089 == 1 {
				_t1909 := p.parse_min_monoid()
				min_monoid1091 := _t1909
				_t1910 := &pb.Monoid{}
				_t1910.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1091}
				_t1908 = _t1910
			} else {
				var _t1911 *pb.Monoid
				if prediction1089 == 0 {
					_t1912 := p.parse_or_monoid()
					or_monoid1090 := _t1912
					_t1913 := &pb.Monoid{}
					_t1913.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1090}
					_t1911 = _t1913
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1908 = _t1911
			}
			_t1905 = _t1908
		}
		_t1902 = _t1905
	}
	result1095 := _t1902
	p.recordSpan(int(span_start1094), "Monoid")
	return result1095
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1096 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1914 := &pb.OrMonoid{}
	result1097 := _t1914
	p.recordSpan(int(span_start1096), "OrMonoid")
	return result1097
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1099 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1915 := p.parse_type()
	type1098 := _t1915
	p.consumeLiteral(")")
	_t1916 := &pb.MinMonoid{Type: type1098}
	result1100 := _t1916
	p.recordSpan(int(span_start1099), "MinMonoid")
	return result1100
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1102 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1917 := p.parse_type()
	type1101 := _t1917
	p.consumeLiteral(")")
	_t1918 := &pb.MaxMonoid{Type: type1101}
	result1103 := _t1918
	p.recordSpan(int(span_start1102), "MaxMonoid")
	return result1103
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1105 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1919 := p.parse_type()
	type1104 := _t1919
	p.consumeLiteral(")")
	_t1920 := &pb.SumMonoid{Type: type1104}
	result1106 := _t1920
	p.recordSpan(int(span_start1105), "SumMonoid")
	return result1106
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1111 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1921 := p.parse_monoid()
	monoid1107 := _t1921
	_t1922 := p.parse_relation_id()
	relation_id1108 := _t1922
	_t1923 := p.parse_abstraction_with_arity()
	abstraction_with_arity1109 := _t1923
	var _t1924 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1925 := p.parse_attrs()
		_t1924 = _t1925
	}
	attrs1110 := _t1924
	p.consumeLiteral(")")
	_t1926 := attrs1110
	if attrs1110 == nil {
		_t1926 = []*pb.Attribute{}
	}
	_t1927 := &pb.MonusDef{Monoid: monoid1107, Name: relation_id1108, Body: abstraction_with_arity1109[0].(*pb.Abstraction), Attrs: _t1926, ValueArity: abstraction_with_arity1109[1].(int64)}
	result1112 := _t1927
	p.recordSpan(int(span_start1111), "MonusDef")
	return result1112
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1928 := p.parse_relation_id()
	relation_id1113 := _t1928
	_t1929 := p.parse_abstraction()
	abstraction1114 := _t1929
	_t1930 := p.parse_functional_dependency_keys()
	functional_dependency_keys1115 := _t1930
	_t1931 := p.parse_functional_dependency_values()
	functional_dependency_values1116 := _t1931
	p.consumeLiteral(")")
	_t1932 := &pb.FunctionalDependency{Guard: abstraction1114, Keys: functional_dependency_keys1115, Values: functional_dependency_values1116}
	_t1933 := &pb.Constraint{Name: relation_id1113}
	_t1933.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1932}
	result1118 := _t1933
	p.recordSpan(int(span_start1117), "Constraint")
	return result1118
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1119 := []*pb.Var{}
	cond1120 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1120 {
		_t1934 := p.parse_var()
		item1121 := _t1934
		xs1119 = append(xs1119, item1121)
		cond1120 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1122 := xs1119
	p.consumeLiteral(")")
	return vars1122
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1123 := []*pb.Var{}
	cond1124 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1124 {
		_t1935 := p.parse_var()
		item1125 := _t1935
		xs1123 = append(xs1123, item1125)
		cond1124 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1126 := xs1123
	p.consumeLiteral(")")
	return vars1126
}

func (p *Parser) parse_data() *pb.Data {
	span_start1132 := int64(p.spanStart())
	var _t1936 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1937 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1937 = 3
		} else {
			var _t1938 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1938 = 0
			} else {
				var _t1939 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1939 = 2
				} else {
					var _t1940 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1940 = 1
					} else {
						_t1940 = -1
					}
					_t1939 = _t1940
				}
				_t1938 = _t1939
			}
			_t1937 = _t1938
		}
		_t1936 = _t1937
	} else {
		_t1936 = -1
	}
	prediction1127 := _t1936
	var _t1941 *pb.Data
	if prediction1127 == 3 {
		_t1942 := p.parse_iceberg_data()
		iceberg_data1131 := _t1942
		_t1943 := &pb.Data{}
		_t1943.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1131}
		_t1941 = _t1943
	} else {
		var _t1944 *pb.Data
		if prediction1127 == 2 {
			_t1945 := p.parse_csv_data()
			csv_data1130 := _t1945
			_t1946 := &pb.Data{}
			_t1946.DataType = &pb.Data_CsvData{CsvData: csv_data1130}
			_t1944 = _t1946
		} else {
			var _t1947 *pb.Data
			if prediction1127 == 1 {
				_t1948 := p.parse_betree_relation()
				betree_relation1129 := _t1948
				_t1949 := &pb.Data{}
				_t1949.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1129}
				_t1947 = _t1949
			} else {
				var _t1950 *pb.Data
				if prediction1127 == 0 {
					_t1951 := p.parse_edb()
					edb1128 := _t1951
					_t1952 := &pb.Data{}
					_t1952.DataType = &pb.Data_Edb{Edb: edb1128}
					_t1950 = _t1952
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1947 = _t1950
			}
			_t1944 = _t1947
		}
		_t1941 = _t1944
	}
	result1133 := _t1941
	p.recordSpan(int(span_start1132), "Data")
	return result1133
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1137 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1953 := p.parse_relation_id()
	relation_id1134 := _t1953
	_t1954 := p.parse_edb_path()
	edb_path1135 := _t1954
	_t1955 := p.parse_edb_types()
	edb_types1136 := _t1955
	p.consumeLiteral(")")
	_t1956 := &pb.EDB{TargetId: relation_id1134, Path: edb_path1135, Types: edb_types1136}
	result1138 := _t1956
	p.recordSpan(int(span_start1137), "EDB")
	return result1138
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1139 := []string{}
	cond1140 := p.matchLookaheadTerminal("STRING", 0)
	for cond1140 {
		item1141 := p.consumeTerminal("STRING").Value.str
		xs1139 = append(xs1139, item1141)
		cond1140 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1142 := xs1139
	p.consumeLiteral("]")
	return strings1142
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1143 := []*pb.Type{}
	cond1144 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1144 {
		_t1957 := p.parse_type()
		item1145 := _t1957
		xs1143 = append(xs1143, item1145)
		cond1144 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1146 := xs1143
	p.consumeLiteral("]")
	return types1146
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1149 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1958 := p.parse_relation_id()
	relation_id1147 := _t1958
	_t1959 := p.parse_betree_info()
	betree_info1148 := _t1959
	p.consumeLiteral(")")
	_t1960 := &pb.BeTreeRelation{Name: relation_id1147, RelationInfo: betree_info1148}
	result1150 := _t1960
	p.recordSpan(int(span_start1149), "BeTreeRelation")
	return result1150
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1154 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1961 := p.parse_betree_info_key_types()
	betree_info_key_types1151 := _t1961
	_t1962 := p.parse_betree_info_value_types()
	betree_info_value_types1152 := _t1962
	_t1963 := p.parse_config_dict()
	config_dict1153 := _t1963
	p.consumeLiteral(")")
	_t1964 := p.construct_betree_info(betree_info_key_types1151, betree_info_value_types1152, config_dict1153)
	result1155 := _t1964
	p.recordSpan(int(span_start1154), "BeTreeInfo")
	return result1155
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1156 := []*pb.Type{}
	cond1157 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1157 {
		_t1965 := p.parse_type()
		item1158 := _t1965
		xs1156 = append(xs1156, item1158)
		cond1157 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1159 := xs1156
	p.consumeLiteral(")")
	return types1159
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1160 := []*pb.Type{}
	cond1161 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1161 {
		_t1966 := p.parse_type()
		item1162 := _t1966
		xs1160 = append(xs1160, item1162)
		cond1161 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1163 := xs1160
	p.consumeLiteral(")")
	return types1163
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1168 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1967 := p.parse_csvlocator()
	csvlocator1164 := _t1967
	_t1968 := p.parse_csv_config()
	csv_config1165 := _t1968
	_t1969 := p.parse_gnf_columns()
	gnf_columns1166 := _t1969
	_t1970 := p.parse_csv_asof()
	csv_asof1167 := _t1970
	p.consumeLiteral(")")
	_t1971 := &pb.CSVData{Locator: csvlocator1164, Config: csv_config1165, Columns: gnf_columns1166, Asof: csv_asof1167}
	result1169 := _t1971
	p.recordSpan(int(span_start1168), "CSVData")
	return result1169
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1172 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1972 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1973 := p.parse_csv_locator_paths()
		_t1972 = _t1973
	}
	csv_locator_paths1170 := _t1972
	var _t1974 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1975 := p.parse_csv_locator_inline_data()
		_t1974 = ptr(_t1975)
	}
	csv_locator_inline_data1171 := _t1974
	p.consumeLiteral(")")
	_t1976 := csv_locator_paths1170
	if csv_locator_paths1170 == nil {
		_t1976 = []string{}
	}
	_t1977 := &pb.CSVLocator{Paths: _t1976, InlineData: []byte(deref(csv_locator_inline_data1171, ""))}
	result1173 := _t1977
	p.recordSpan(int(span_start1172), "CSVLocator")
	return result1173
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1174 := []string{}
	cond1175 := p.matchLookaheadTerminal("STRING", 0)
	for cond1175 {
		item1176 := p.consumeTerminal("STRING").Value.str
		xs1174 = append(xs1174, item1176)
		cond1175 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1177 := xs1174
	p.consumeLiteral(")")
	return strings1177
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1178 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1178
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1180 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1978 := p.parse_config_dict()
	config_dict1179 := _t1978
	p.consumeLiteral(")")
	_t1979 := p.construct_csv_config(config_dict1179)
	result1181 := _t1979
	p.recordSpan(int(span_start1180), "CSVConfig")
	return result1181
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1182 := []*pb.GNFColumn{}
	cond1183 := p.matchLookaheadLiteral("(", 0)
	for cond1183 {
		_t1980 := p.parse_gnf_column()
		item1184 := _t1980
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
	_t1981 := p.parse_gnf_column_path()
	gnf_column_path1186 := _t1981
	var _t1982 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1983 := p.parse_relation_id()
		_t1982 = _t1983
	}
	relation_id1187 := _t1982
	p.consumeLiteral("[")
	xs1188 := []*pb.Type{}
	cond1189 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1189 {
		_t1984 := p.parse_type()
		item1190 := _t1984
		xs1188 = append(xs1188, item1190)
		cond1189 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1191 := xs1188
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1985 := &pb.GNFColumn{ColumnPath: gnf_column_path1186, TargetId: relation_id1187, Types: types1191}
	result1193 := _t1985
	p.recordSpan(int(span_start1192), "GNFColumn")
	return result1193
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1986 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1986 = 1
	} else {
		var _t1987 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1987 = 0
		} else {
			_t1987 = -1
		}
		_t1986 = _t1987
	}
	prediction1194 := _t1986
	var _t1988 []string
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
		_t1988 = strings1199
	} else {
		var _t1989 []string
		if prediction1194 == 0 {
			string1195 := p.consumeTerminal("STRING").Value.str
			_ = string1195
			_t1989 = []string{string1195}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1988 = _t1989
	}
	return _t1988
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1200 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1200
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1205 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1990 := p.parse_iceberg_locator()
	iceberg_locator1201 := _t1990
	_t1991 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1202 := _t1991
	_t1992 := p.parse_gnf_columns()
	gnf_columns1203 := _t1992
	_t1993 := p.parse_boolean_value()
	boolean_value1204 := _t1993
	p.consumeLiteral(")")
	_t1994 := &pb.IcebergData{Locator: iceberg_locator1201, Config: iceberg_catalog_config1202, Columns: gnf_columns1203, ReturnsDelta: boolean_value1204}
	result1206 := _t1994
	p.recordSpan(int(span_start1205), "IcebergData")
	return result1206
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1212 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t1995 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1207 := _t1995
	_t1996 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1208 := _t1996
	_t1997 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1209 := _t1997
	var _t1998 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1999 := p.parse_iceberg_from_snapshot()
		_t1998 = ptr(_t1999)
	}
	iceberg_from_snapshot1210 := _t1998
	var _t2000 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t2001 := p.parse_iceberg_to_snapshot()
		_t2000 = ptr(_t2001)
	}
	iceberg_to_snapshot1211 := _t2000
	p.consumeLiteral(")")
	_t2002 := p.construct_iceberg_locator(iceberg_locator_table_name1207, iceberg_locator_namespace1208, iceberg_locator_warehouse1209, iceberg_from_snapshot1210, iceberg_to_snapshot1211)
	result1213 := _t2002
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

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1220 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1220
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1221 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1221
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1226 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t2003 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1222 := _t2003
	var _t2004 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t2005 := p.parse_iceberg_catalog_config_scope()
		_t2004 = ptr(_t2005)
	}
	iceberg_catalog_config_scope1223 := _t2004
	_t2006 := p.parse_iceberg_properties()
	iceberg_properties1224 := _t2006
	_t2007 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1225 := _t2007
	p.consumeLiteral(")")
	_t2008 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1222, iceberg_catalog_config_scope1223, iceberg_properties1224, iceberg_auth_properties1225)
	result1227 := _t2008
	p.recordSpan(int(span_start1226), "IcebergCatalogConfig")
	return result1227
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1228 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1228
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1229 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1229
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1230 := [][]interface{}{}
	cond1231 := p.matchLookaheadLiteral("(", 0)
	for cond1231 {
		_t2009 := p.parse_iceberg_property_entry()
		item1232 := _t2009
		xs1230 = append(xs1230, item1232)
		cond1231 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1233 := xs1230
	p.consumeLiteral(")")
	return iceberg_property_entrys1233
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1234 := p.consumeTerminal("STRING").Value.str
	string_31235 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1234, string_31235}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1236 := [][]interface{}{}
	cond1237 := p.matchLookaheadLiteral("(", 0)
	for cond1237 {
		_t2010 := p.parse_iceberg_masked_property_entry()
		item1238 := _t2010
		xs1236 = append(xs1236, item1238)
		cond1237 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1239 := xs1236
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1239
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1240 := p.consumeTerminal("STRING").Value.str
	string_31241 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1240, string_31241}
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1243 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2011 := p.parse_fragment_id()
	fragment_id1242 := _t2011
	p.consumeLiteral(")")
	_t2012 := &pb.Undefine{FragmentId: fragment_id1242}
	result1244 := _t2012
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
		_t2013 := p.parse_relation_id()
		item1247 := _t2013
		xs1245 = append(xs1245, item1247)
		cond1246 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1248 := xs1245
	p.consumeLiteral(")")
	_t2014 := &pb.Context{Relations: relation_ids1248}
	result1250 := _t2014
	p.recordSpan(int(span_start1249), "Context")
	return result1250
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1251 := []*pb.SnapshotMapping{}
	cond1252 := p.matchLookaheadLiteral("[", 0)
	for cond1252 {
		_t2015 := p.parse_snapshot_mapping()
		item1253 := _t2015
		xs1251 = append(xs1251, item1253)
		cond1252 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1254 := xs1251
	p.consumeLiteral(")")
	_t2016 := &pb.Snapshot{Mappings: snapshot_mappings1254}
	result1256 := _t2016
	p.recordSpan(int(span_start1255), "Snapshot")
	return result1256
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1259 := int64(p.spanStart())
	_t2017 := p.parse_edb_path()
	edb_path1257 := _t2017
	_t2018 := p.parse_relation_id()
	relation_id1258 := _t2018
	_t2019 := &pb.SnapshotMapping{DestinationPath: edb_path1257, SourceRelation: relation_id1258}
	result1260 := _t2019
	p.recordSpan(int(span_start1259), "SnapshotMapping")
	return result1260
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1261 := []*pb.Read{}
	cond1262 := p.matchLookaheadLiteral("(", 0)
	for cond1262 {
		_t2020 := p.parse_read()
		item1263 := _t2020
		xs1261 = append(xs1261, item1263)
		cond1262 = p.matchLookaheadLiteral("(", 0)
	}
	reads1264 := xs1261
	p.consumeLiteral(")")
	return reads1264
}

func (p *Parser) parse_read() *pb.Read {
	span_start1271 := int64(p.spanStart())
	var _t2021 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2022 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2022 = 2
		} else {
			var _t2023 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2023 = 1
			} else {
				var _t2024 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2024 = 4
				} else {
					var _t2025 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2025 = 4
					} else {
						var _t2026 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2026 = 0
						} else {
							var _t2027 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2027 = 3
							} else {
								_t2027 = -1
							}
							_t2026 = _t2027
						}
						_t2025 = _t2026
					}
					_t2024 = _t2025
				}
				_t2023 = _t2024
			}
			_t2022 = _t2023
		}
		_t2021 = _t2022
	} else {
		_t2021 = -1
	}
	prediction1265 := _t2021
	var _t2028 *pb.Read
	if prediction1265 == 4 {
		_t2029 := p.parse_export()
		export1270 := _t2029
		_t2030 := &pb.Read{}
		_t2030.ReadType = &pb.Read_Export{Export: export1270}
		_t2028 = _t2030
	} else {
		var _t2031 *pb.Read
		if prediction1265 == 3 {
			_t2032 := p.parse_abort()
			abort1269 := _t2032
			_t2033 := &pb.Read{}
			_t2033.ReadType = &pb.Read_Abort{Abort: abort1269}
			_t2031 = _t2033
		} else {
			var _t2034 *pb.Read
			if prediction1265 == 2 {
				_t2035 := p.parse_what_if()
				what_if1268 := _t2035
				_t2036 := &pb.Read{}
				_t2036.ReadType = &pb.Read_WhatIf{WhatIf: what_if1268}
				_t2034 = _t2036
			} else {
				var _t2037 *pb.Read
				if prediction1265 == 1 {
					_t2038 := p.parse_output()
					output1267 := _t2038
					_t2039 := &pb.Read{}
					_t2039.ReadType = &pb.Read_Output{Output: output1267}
					_t2037 = _t2039
				} else {
					var _t2040 *pb.Read
					if prediction1265 == 0 {
						_t2041 := p.parse_demand()
						demand1266 := _t2041
						_t2042 := &pb.Read{}
						_t2042.ReadType = &pb.Read_Demand{Demand: demand1266}
						_t2040 = _t2042
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2037 = _t2040
				}
				_t2034 = _t2037
			}
			_t2031 = _t2034
		}
		_t2028 = _t2031
	}
	result1272 := _t2028
	p.recordSpan(int(span_start1271), "Read")
	return result1272
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1274 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2043 := p.parse_relation_id()
	relation_id1273 := _t2043
	p.consumeLiteral(")")
	_t2044 := &pb.Demand{RelationId: relation_id1273}
	result1275 := _t2044
	p.recordSpan(int(span_start1274), "Demand")
	return result1275
}

func (p *Parser) parse_output() *pb.Output {
	span_start1278 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2045 := p.parse_name()
	name1276 := _t2045
	_t2046 := p.parse_relation_id()
	relation_id1277 := _t2046
	p.consumeLiteral(")")
	_t2047 := &pb.Output{Name: name1276, RelationId: relation_id1277}
	result1279 := _t2047
	p.recordSpan(int(span_start1278), "Output")
	return result1279
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1282 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2048 := p.parse_name()
	name1280 := _t2048
	_t2049 := p.parse_epoch()
	epoch1281 := _t2049
	p.consumeLiteral(")")
	_t2050 := &pb.WhatIf{Branch: name1280, Epoch: epoch1281}
	result1283 := _t2050
	p.recordSpan(int(span_start1282), "WhatIf")
	return result1283
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1286 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2051 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2052 := p.parse_name()
		_t2051 = ptr(_t2052)
	}
	name1284 := _t2051
	_t2053 := p.parse_relation_id()
	relation_id1285 := _t2053
	p.consumeLiteral(")")
	_t2054 := &pb.Abort{Name: deref(name1284, "abort"), RelationId: relation_id1285}
	result1287 := _t2054
	p.recordSpan(int(span_start1286), "Abort")
	return result1287
}

func (p *Parser) parse_export() *pb.Export {
	span_start1291 := int64(p.spanStart())
	var _t2055 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2056 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2056 = 1
		} else {
			var _t2057 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2057 = 0
			} else {
				_t2057 = -1
			}
			_t2056 = _t2057
		}
		_t2055 = _t2056
	} else {
		_t2055 = -1
	}
	prediction1288 := _t2055
	var _t2058 *pb.Export
	if prediction1288 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2059 := p.parse_export_iceberg_config()
		export_iceberg_config1290 := _t2059
		p.consumeLiteral(")")
		_t2060 := &pb.Export{}
		_t2060.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1290}
		_t2058 = _t2060
	} else {
		var _t2061 *pb.Export
		if prediction1288 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2062 := p.parse_export_csv_config()
			export_csv_config1289 := _t2062
			p.consumeLiteral(")")
			_t2063 := &pb.Export{}
			_t2063.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1289}
			_t2061 = _t2063
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2058 = _t2061
	}
	result1292 := _t2058
	p.recordSpan(int(span_start1291), "Export")
	return result1292
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1300 := int64(p.spanStart())
	var _t2064 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2065 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2065 = 0
		} else {
			var _t2066 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2066 = 1
			} else {
				_t2066 = -1
			}
			_t2065 = _t2066
		}
		_t2064 = _t2065
	} else {
		_t2064 = -1
	}
	prediction1293 := _t2064
	var _t2067 *pb.ExportCSVConfig
	if prediction1293 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2068 := p.parse_export_csv_path()
		export_csv_path1297 := _t2068
		_t2069 := p.parse_export_csv_columns_list()
		export_csv_columns_list1298 := _t2069
		_t2070 := p.parse_config_dict()
		config_dict1299 := _t2070
		p.consumeLiteral(")")
		_t2071 := p.construct_export_csv_config(export_csv_path1297, export_csv_columns_list1298, config_dict1299)
		_t2067 = _t2071
	} else {
		var _t2072 *pb.ExportCSVConfig
		if prediction1293 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2073 := p.parse_export_csv_path()
			export_csv_path1294 := _t2073
			_t2074 := p.parse_export_csv_source()
			export_csv_source1295 := _t2074
			_t2075 := p.parse_csv_config()
			csv_config1296 := _t2075
			p.consumeLiteral(")")
			_t2076 := p.construct_export_csv_config_with_source(export_csv_path1294, export_csv_source1295, csv_config1296)
			_t2072 = _t2076
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2067 = _t2072
	}
	result1301 := _t2067
	p.recordSpan(int(span_start1300), "ExportCSVConfig")
	return result1301
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1302 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1302
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1309 := int64(p.spanStart())
	var _t2077 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2078 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2078 = 1
		} else {
			var _t2079 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
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
	prediction1303 := _t2077
	var _t2080 *pb.ExportCSVSource
	if prediction1303 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2081 := p.parse_relation_id()
		relation_id1308 := _t2081
		p.consumeLiteral(")")
		_t2082 := &pb.ExportCSVSource{}
		_t2082.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1308}
		_t2080 = _t2082
	} else {
		var _t2083 *pb.ExportCSVSource
		if prediction1303 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1304 := []*pb.ExportCSVColumn{}
			cond1305 := p.matchLookaheadLiteral("(", 0)
			for cond1305 {
				_t2084 := p.parse_export_csv_column()
				item1306 := _t2084
				xs1304 = append(xs1304, item1306)
				cond1305 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1307 := xs1304
			p.consumeLiteral(")")
			_t2085 := &pb.ExportCSVColumns{Columns: export_csv_columns1307}
			_t2086 := &pb.ExportCSVSource{}
			_t2086.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2085}
			_t2083 = _t2086
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2080 = _t2083
	}
	result1310 := _t2080
	p.recordSpan(int(span_start1309), "ExportCSVSource")
	return result1310
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1313 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1311 := p.consumeTerminal("STRING").Value.str
	_t2087 := p.parse_relation_id()
	relation_id1312 := _t2087
	p.consumeLiteral(")")
	_t2088 := &pb.ExportCSVColumn{ColumnName: string1311, ColumnData: relation_id1312}
	result1314 := _t2088
	p.recordSpan(int(span_start1313), "ExportCSVColumn")
	return result1314
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1315 := []*pb.ExportCSVColumn{}
	cond1316 := p.matchLookaheadLiteral("(", 0)
	for cond1316 {
		_t2089 := p.parse_export_csv_column()
		item1317 := _t2089
		xs1315 = append(xs1315, item1317)
		cond1316 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1318 := xs1315
	p.consumeLiteral(")")
	return export_csv_columns1318
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1325 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2090 := p.parse_iceberg_locator()
	iceberg_locator1319 := _t2090
	_t2091 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1320 := _t2091
	_t2092 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1321 := _t2092
	_t2093 := p.parse_export_iceberg_columns()
	export_iceberg_columns1322 := _t2093
	_t2094 := p.parse_iceberg_table_properties()
	iceberg_table_properties1323 := _t2094
	var _t2095 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2096 := p.parse_config_dict()
		_t2095 = _t2096
	}
	config_dict1324 := _t2095
	p.consumeLiteral(")")
	_t2097 := p.construct_export_iceberg_config_full(iceberg_locator1319, iceberg_catalog_config1320, export_iceberg_table_def1321, export_iceberg_columns1322, iceberg_table_properties1323, config_dict1324)
	result1326 := _t2097
	p.recordSpan(int(span_start1325), "ExportIcebergConfig")
	return result1326
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1328 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2098 := p.parse_relation_id()
	relation_id1327 := _t2098
	p.consumeLiteral(")")
	result1329 := relation_id1327
	p.recordSpan(int(span_start1328), "RelationId")
	return result1329
}

func (p *Parser) parse_export_iceberg_columns() []*pb.ExportGNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1330 := []*pb.ExportGNFColumn{}
	cond1331 := p.matchLookaheadLiteral("(", 0)
	for cond1331 {
		_t2099 := p.parse_export_gnf_column()
		item1332 := _t2099
		xs1330 = append(xs1330, item1332)
		cond1331 = p.matchLookaheadLiteral("(", 0)
	}
	export_gnf_columns1333 := xs1330
	p.consumeLiteral(")")
	return export_gnf_columns1333
}

func (p *Parser) parse_export_gnf_column() *pb.ExportGNFColumn {
	span_start1336 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("gnf_column")
	string1334 := p.consumeTerminal("STRING").Value.str
	_t2100 := p.parse_boolean_value()
	boolean_value1335 := _t2100
	p.consumeLiteral(")")
	_t2101 := &pb.ExportGNFColumn{Name: string1334, Nullable: boolean_value1335}
	result1337 := _t2101
	p.recordSpan(int(span_start1336), "ExportGNFColumn")
	return result1337
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1338 := [][]interface{}{}
	cond1339 := p.matchLookaheadLiteral("(", 0)
	for cond1339 {
		_t2102 := p.parse_iceberg_property_entry()
		item1340 := _t2102
		xs1338 = append(xs1338, item1340)
		cond1339 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1341 := xs1338
	p.consumeLiteral(")")
	return iceberg_property_entrys1341
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
