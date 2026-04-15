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
	var _t2094 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2094
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2095 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2095
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2096 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2096
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2097 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2097
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2098 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2098
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2099 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2099
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2100 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2100
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2101 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2101
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2102 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2102
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2103 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2103
	_t2104 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2104
	_t2105 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2105
	_t2106 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2106
	_t2107 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2107
	_t2108 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2108
	_t2109 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2109
	_t2110 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2110
	_t2111 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2111
	_t2112 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2112
	_t2113 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2113
	_t2114 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2114
	_t2115 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2115
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2116 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2116
	_t2117 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2117
	_t2118 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2118
	_t2119 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2119
	_t2120 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2120
	_t2121 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2121
	_t2122 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2122
	_t2123 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2123
	_t2124 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2124
	_t2125 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2125.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2125.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2125
	_t2126 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2126
}

func (p *Parser) default_configure() *pb.Configure {
	_t2127 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2127
	_t2128 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2128
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
	_t2129 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2129
	_t2130 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2130
	_t2131 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2131
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2132 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2132
	_t2133 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2133
	_t2134 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2134
	_t2135 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2135
	_t2136 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2136
	_t2137 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2137
	_t2138 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2138
	_t2139 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2139
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2140 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2140
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2141 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2141
}

func (p *Parser) construct_iceberg_data(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns []*pb.GNFColumn, from_snapshot_opt *string, to_snapshot_opt *string, returns_delta bool) *pb.IcebergData {
	_t2142 := &pb.IcebergData{Locator: locator, Config: config, Columns: columns, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, "")), ReturnsDelta: returns_delta}
	return _t2142
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2143 := config_dict
	if config_dict == nil {
		_t2143 = [][]interface{}{}
	}
	cfg := dictFromList(_t2143)
	_t2144 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2144
	_t2145 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2145
	_t2146 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2146
	table_props := stringMapFromPairs(table_property_pairs)
	_t2147 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2147
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start671 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1330 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1331 := p.parse_configure()
		_t1330 = _t1331
	}
	configure665 := _t1330
	var _t1332 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1333 := p.parse_sync()
		_t1332 = _t1333
	}
	sync666 := _t1332
	xs667 := []*pb.Epoch{}
	cond668 := p.matchLookaheadLiteral("(", 0)
	for cond668 {
		_t1334 := p.parse_epoch()
		item669 := _t1334
		xs667 = append(xs667, item669)
		cond668 = p.matchLookaheadLiteral("(", 0)
	}
	epochs670 := xs667
	p.consumeLiteral(")")
	_t1335 := p.default_configure()
	_t1336 := configure665
	if configure665 == nil {
		_t1336 = _t1335
	}
	_t1337 := &pb.Transaction{Epochs: epochs670, Configure: _t1336, Sync: sync666}
	result672 := _t1337
	p.recordSpan(int(span_start671), "Transaction")
	return result672
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start674 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1338 := p.parse_config_dict()
	config_dict673 := _t1338
	p.consumeLiteral(")")
	_t1339 := p.construct_configure(config_dict673)
	result675 := _t1339
	p.recordSpan(int(span_start674), "Configure")
	return result675
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs676 := [][]interface{}{}
	cond677 := p.matchLookaheadLiteral(":", 0)
	for cond677 {
		_t1340 := p.parse_config_key_value()
		item678 := _t1340
		xs676 = append(xs676, item678)
		cond677 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values679 := xs676
	p.consumeLiteral("}")
	return config_key_values679
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol680 := p.consumeTerminal("SYMBOL").Value.str
	_t1341 := p.parse_raw_value()
	raw_value681 := _t1341
	return []interface{}{symbol680, raw_value681}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start695 := int64(p.spanStart())
	var _t1342 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1342 = 12
	} else {
		var _t1343 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1343 = 11
		} else {
			var _t1344 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1344 = 12
			} else {
				var _t1345 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1346 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1346 = 1
					} else {
						var _t1347 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1347 = 0
						} else {
							_t1347 = -1
						}
						_t1346 = _t1347
					}
					_t1345 = _t1346
				} else {
					var _t1348 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1348 = 7
					} else {
						var _t1349 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1349 = 8
						} else {
							var _t1350 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1350 = 2
							} else {
								var _t1351 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1351 = 3
								} else {
									var _t1352 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1352 = 9
									} else {
										var _t1353 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1353 = 4
										} else {
											var _t1354 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1354 = 5
											} else {
												var _t1355 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1355 = 6
												} else {
													var _t1356 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1356 = 10
													} else {
														_t1356 = -1
													}
													_t1355 = _t1356
												}
												_t1354 = _t1355
											}
											_t1353 = _t1354
										}
										_t1352 = _t1353
									}
									_t1351 = _t1352
								}
								_t1350 = _t1351
							}
							_t1349 = _t1350
						}
						_t1348 = _t1349
					}
					_t1345 = _t1348
				}
				_t1344 = _t1345
			}
			_t1343 = _t1344
		}
		_t1342 = _t1343
	}
	prediction682 := _t1342
	var _t1357 *pb.Value
	if prediction682 == 12 {
		_t1358 := p.parse_boolean_value()
		boolean_value694 := _t1358
		_t1359 := &pb.Value{}
		_t1359.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value694}
		_t1357 = _t1359
	} else {
		var _t1360 *pb.Value
		if prediction682 == 11 {
			p.consumeLiteral("missing")
			_t1361 := &pb.MissingValue{}
			_t1362 := &pb.Value{}
			_t1362.Value = &pb.Value_MissingValue{MissingValue: _t1361}
			_t1360 = _t1362
		} else {
			var _t1363 *pb.Value
			if prediction682 == 10 {
				decimal693 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1364 := &pb.Value{}
				_t1364.Value = &pb.Value_DecimalValue{DecimalValue: decimal693}
				_t1363 = _t1364
			} else {
				var _t1365 *pb.Value
				if prediction682 == 9 {
					int128692 := p.consumeTerminal("INT128").Value.int128
					_t1366 := &pb.Value{}
					_t1366.Value = &pb.Value_Int128Value{Int128Value: int128692}
					_t1365 = _t1366
				} else {
					var _t1367 *pb.Value
					if prediction682 == 8 {
						uint128691 := p.consumeTerminal("UINT128").Value.uint128
						_t1368 := &pb.Value{}
						_t1368.Value = &pb.Value_Uint128Value{Uint128Value: uint128691}
						_t1367 = _t1368
					} else {
						var _t1369 *pb.Value
						if prediction682 == 7 {
							uint32690 := p.consumeTerminal("UINT32").Value.u32
							_t1370 := &pb.Value{}
							_t1370.Value = &pb.Value_Uint32Value{Uint32Value: uint32690}
							_t1369 = _t1370
						} else {
							var _t1371 *pb.Value
							if prediction682 == 6 {
								float689 := p.consumeTerminal("FLOAT").Value.f64
								_t1372 := &pb.Value{}
								_t1372.Value = &pb.Value_FloatValue{FloatValue: float689}
								_t1371 = _t1372
							} else {
								var _t1373 *pb.Value
								if prediction682 == 5 {
									float32688 := p.consumeTerminal("FLOAT32").Value.f32
									_t1374 := &pb.Value{}
									_t1374.Value = &pb.Value_Float32Value{Float32Value: float32688}
									_t1373 = _t1374
								} else {
									var _t1375 *pb.Value
									if prediction682 == 4 {
										int687 := p.consumeTerminal("INT").Value.i64
										_t1376 := &pb.Value{}
										_t1376.Value = &pb.Value_IntValue{IntValue: int687}
										_t1375 = _t1376
									} else {
										var _t1377 *pb.Value
										if prediction682 == 3 {
											int32686 := p.consumeTerminal("INT32").Value.i32
											_t1378 := &pb.Value{}
											_t1378.Value = &pb.Value_Int32Value{Int32Value: int32686}
											_t1377 = _t1378
										} else {
											var _t1379 *pb.Value
											if prediction682 == 2 {
												string685 := p.consumeTerminal("STRING").Value.str
												_t1380 := &pb.Value{}
												_t1380.Value = &pb.Value_StringValue{StringValue: string685}
												_t1379 = _t1380
											} else {
												var _t1381 *pb.Value
												if prediction682 == 1 {
													_t1382 := p.parse_raw_datetime()
													raw_datetime684 := _t1382
													_t1383 := &pb.Value{}
													_t1383.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime684}
													_t1381 = _t1383
												} else {
													var _t1384 *pb.Value
													if prediction682 == 0 {
														_t1385 := p.parse_raw_date()
														raw_date683 := _t1385
														_t1386 := &pb.Value{}
														_t1386.Value = &pb.Value_DateValue{DateValue: raw_date683}
														_t1384 = _t1386
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1381 = _t1384
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
					_t1365 = _t1367
				}
				_t1363 = _t1365
			}
			_t1360 = _t1363
		}
		_t1357 = _t1360
	}
	result696 := _t1357
	p.recordSpan(int(span_start695), "Value")
	return result696
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start700 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int697 := p.consumeTerminal("INT").Value.i64
	int_3698 := p.consumeTerminal("INT").Value.i64
	int_4699 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1387 := &pb.DateValue{Year: int32(int697), Month: int32(int_3698), Day: int32(int_4699)}
	result701 := _t1387
	p.recordSpan(int(span_start700), "DateValue")
	return result701
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int702 := p.consumeTerminal("INT").Value.i64
	int_3703 := p.consumeTerminal("INT").Value.i64
	int_4704 := p.consumeTerminal("INT").Value.i64
	int_5705 := p.consumeTerminal("INT").Value.i64
	int_6706 := p.consumeTerminal("INT").Value.i64
	int_7707 := p.consumeTerminal("INT").Value.i64
	var _t1388 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1388 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8708 := _t1388
	p.consumeLiteral(")")
	_t1389 := &pb.DateTimeValue{Year: int32(int702), Month: int32(int_3703), Day: int32(int_4704), Hour: int32(int_5705), Minute: int32(int_6706), Second: int32(int_7707), Microsecond: int32(deref(int_8708, 0))}
	result710 := _t1389
	p.recordSpan(int(span_start709), "DateTimeValue")
	return result710
}

func (p *Parser) parse_boolean_value() bool {
	var _t1390 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1390 = 0
	} else {
		var _t1391 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1391 = 1
		} else {
			_t1391 = -1
		}
		_t1390 = _t1391
	}
	prediction711 := _t1390
	var _t1392 bool
	if prediction711 == 1 {
		p.consumeLiteral("false")
		_t1392 = false
	} else {
		var _t1393 bool
		if prediction711 == 0 {
			p.consumeLiteral("true")
			_t1393 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1392 = _t1393
	}
	return _t1392
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start716 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs712 := []*pb.FragmentId{}
	cond713 := p.matchLookaheadLiteral(":", 0)
	for cond713 {
		_t1394 := p.parse_fragment_id()
		item714 := _t1394
		xs712 = append(xs712, item714)
		cond713 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids715 := xs712
	p.consumeLiteral(")")
	_t1395 := &pb.Sync{Fragments: fragment_ids715}
	result717 := _t1395
	p.recordSpan(int(span_start716), "Sync")
	return result717
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start719 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol718 := p.consumeTerminal("SYMBOL").Value.str
	result720 := &pb.FragmentId{Id: []byte(symbol718)}
	p.recordSpan(int(span_start719), "FragmentId")
	return result720
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1396 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1397 := p.parse_epoch_writes()
		_t1396 = _t1397
	}
	epoch_writes721 := _t1396
	var _t1398 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1399 := p.parse_epoch_reads()
		_t1398 = _t1399
	}
	epoch_reads722 := _t1398
	p.consumeLiteral(")")
	_t1400 := epoch_writes721
	if epoch_writes721 == nil {
		_t1400 = []*pb.Write{}
	}
	_t1401 := epoch_reads722
	if epoch_reads722 == nil {
		_t1401 = []*pb.Read{}
	}
	_t1402 := &pb.Epoch{Writes: _t1400, Reads: _t1401}
	result724 := _t1402
	p.recordSpan(int(span_start723), "Epoch")
	return result724
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs725 := []*pb.Write{}
	cond726 := p.matchLookaheadLiteral("(", 0)
	for cond726 {
		_t1403 := p.parse_write()
		item727 := _t1403
		xs725 = append(xs725, item727)
		cond726 = p.matchLookaheadLiteral("(", 0)
	}
	writes728 := xs725
	p.consumeLiteral(")")
	return writes728
}

func (p *Parser) parse_write() *pb.Write {
	span_start734 := int64(p.spanStart())
	var _t1404 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1405 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1405 = 1
		} else {
			var _t1406 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1406 = 3
			} else {
				var _t1407 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1407 = 0
				} else {
					var _t1408 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1408 = 2
					} else {
						_t1408 = -1
					}
					_t1407 = _t1408
				}
				_t1406 = _t1407
			}
			_t1405 = _t1406
		}
		_t1404 = _t1405
	} else {
		_t1404 = -1
	}
	prediction729 := _t1404
	var _t1409 *pb.Write
	if prediction729 == 3 {
		_t1410 := p.parse_snapshot()
		snapshot733 := _t1410
		_t1411 := &pb.Write{}
		_t1411.WriteType = &pb.Write_Snapshot{Snapshot: snapshot733}
		_t1409 = _t1411
	} else {
		var _t1412 *pb.Write
		if prediction729 == 2 {
			_t1413 := p.parse_context()
			context732 := _t1413
			_t1414 := &pb.Write{}
			_t1414.WriteType = &pb.Write_Context{Context: context732}
			_t1412 = _t1414
		} else {
			var _t1415 *pb.Write
			if prediction729 == 1 {
				_t1416 := p.parse_undefine()
				undefine731 := _t1416
				_t1417 := &pb.Write{}
				_t1417.WriteType = &pb.Write_Undefine{Undefine: undefine731}
				_t1415 = _t1417
			} else {
				var _t1418 *pb.Write
				if prediction729 == 0 {
					_t1419 := p.parse_define()
					define730 := _t1419
					_t1420 := &pb.Write{}
					_t1420.WriteType = &pb.Write_Define{Define: define730}
					_t1418 = _t1420
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1415 = _t1418
			}
			_t1412 = _t1415
		}
		_t1409 = _t1412
	}
	result735 := _t1409
	p.recordSpan(int(span_start734), "Write")
	return result735
}

func (p *Parser) parse_define() *pb.Define {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1421 := p.parse_fragment()
	fragment736 := _t1421
	p.consumeLiteral(")")
	_t1422 := &pb.Define{Fragment: fragment736}
	result738 := _t1422
	p.recordSpan(int(span_start737), "Define")
	return result738
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start744 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1423 := p.parse_new_fragment_id()
	new_fragment_id739 := _t1423
	xs740 := []*pb.Declaration{}
	cond741 := p.matchLookaheadLiteral("(", 0)
	for cond741 {
		_t1424 := p.parse_declaration()
		item742 := _t1424
		xs740 = append(xs740, item742)
		cond741 = p.matchLookaheadLiteral("(", 0)
	}
	declarations743 := xs740
	p.consumeLiteral(")")
	result745 := p.constructFragment(new_fragment_id739, declarations743)
	p.recordSpan(int(span_start744), "Fragment")
	return result745
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start747 := int64(p.spanStart())
	_t1425 := p.parse_fragment_id()
	fragment_id746 := _t1425
	p.startFragment(fragment_id746)
	result748 := fragment_id746
	p.recordSpan(int(span_start747), "FragmentId")
	return result748
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start754 := int64(p.spanStart())
	var _t1426 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1427 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1427 = 3
		} else {
			var _t1428 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1428 = 2
			} else {
				var _t1429 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1429 = 3
				} else {
					var _t1430 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1430 = 0
					} else {
						var _t1431 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1431 = 3
						} else {
							var _t1432 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1432 = 3
							} else {
								var _t1433 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1433 = 1
								} else {
									_t1433 = -1
								}
								_t1432 = _t1433
							}
							_t1431 = _t1432
						}
						_t1430 = _t1431
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
	prediction749 := _t1426
	var _t1434 *pb.Declaration
	if prediction749 == 3 {
		_t1435 := p.parse_data()
		data753 := _t1435
		_t1436 := &pb.Declaration{}
		_t1436.DeclarationType = &pb.Declaration_Data{Data: data753}
		_t1434 = _t1436
	} else {
		var _t1437 *pb.Declaration
		if prediction749 == 2 {
			_t1438 := p.parse_constraint()
			constraint752 := _t1438
			_t1439 := &pb.Declaration{}
			_t1439.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint752}
			_t1437 = _t1439
		} else {
			var _t1440 *pb.Declaration
			if prediction749 == 1 {
				_t1441 := p.parse_algorithm()
				algorithm751 := _t1441
				_t1442 := &pb.Declaration{}
				_t1442.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm751}
				_t1440 = _t1442
			} else {
				var _t1443 *pb.Declaration
				if prediction749 == 0 {
					_t1444 := p.parse_def()
					def750 := _t1444
					_t1445 := &pb.Declaration{}
					_t1445.DeclarationType = &pb.Declaration_Def{Def: def750}
					_t1443 = _t1445
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1440 = _t1443
			}
			_t1437 = _t1440
		}
		_t1434 = _t1437
	}
	result755 := _t1434
	p.recordSpan(int(span_start754), "Declaration")
	return result755
}

func (p *Parser) parse_def() *pb.Def {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1446 := p.parse_relation_id()
	relation_id756 := _t1446
	_t1447 := p.parse_abstraction()
	abstraction757 := _t1447
	var _t1448 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1449 := p.parse_attrs()
		_t1448 = _t1449
	}
	attrs758 := _t1448
	p.consumeLiteral(")")
	_t1450 := attrs758
	if attrs758 == nil {
		_t1450 = []*pb.Attribute{}
	}
	_t1451 := &pb.Def{Name: relation_id756, Body: abstraction757, Attrs: _t1450}
	result760 := _t1451
	p.recordSpan(int(span_start759), "Def")
	return result760
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start764 := int64(p.spanStart())
	var _t1452 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1452 = 0
	} else {
		var _t1453 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1453 = 1
		} else {
			_t1453 = -1
		}
		_t1452 = _t1453
	}
	prediction761 := _t1452
	var _t1454 *pb.RelationId
	if prediction761 == 1 {
		uint128763 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128763
		_t1454 = &pb.RelationId{IdLow: uint128763.Low, IdHigh: uint128763.High}
	} else {
		var _t1455 *pb.RelationId
		if prediction761 == 0 {
			p.consumeLiteral(":")
			symbol762 := p.consumeTerminal("SYMBOL").Value.str
			_t1455 = p.relationIdFromString(symbol762)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1454 = _t1455
	}
	result765 := _t1454
	p.recordSpan(int(span_start764), "RelationId")
	return result765
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start768 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1456 := p.parse_bindings()
	bindings766 := _t1456
	_t1457 := p.parse_formula()
	formula767 := _t1457
	p.consumeLiteral(")")
	_t1458 := &pb.Abstraction{Vars: listConcat(bindings766[0].([]*pb.Binding), bindings766[1].([]*pb.Binding)), Value: formula767}
	result769 := _t1458
	p.recordSpan(int(span_start768), "Abstraction")
	return result769
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs770 := []*pb.Binding{}
	cond771 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond771 {
		_t1459 := p.parse_binding()
		item772 := _t1459
		xs770 = append(xs770, item772)
		cond771 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings773 := xs770
	var _t1460 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1461 := p.parse_value_bindings()
		_t1460 = _t1461
	}
	value_bindings774 := _t1460
	p.consumeLiteral("]")
	_t1462 := value_bindings774
	if value_bindings774 == nil {
		_t1462 = []*pb.Binding{}
	}
	return []interface{}{bindings773, _t1462}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start777 := int64(p.spanStart())
	symbol775 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1463 := p.parse_type()
	type776 := _t1463
	_t1464 := &pb.Var{Name: symbol775}
	_t1465 := &pb.Binding{Var: _t1464, Type: type776}
	result778 := _t1465
	p.recordSpan(int(span_start777), "Binding")
	return result778
}

func (p *Parser) parse_type() *pb.Type {
	span_start794 := int64(p.spanStart())
	var _t1466 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1466 = 0
	} else {
		var _t1467 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1467 = 13
		} else {
			var _t1468 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1468 = 4
			} else {
				var _t1469 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1469 = 1
				} else {
					var _t1470 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1470 = 8
					} else {
						var _t1471 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1471 = 11
						} else {
							var _t1472 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1472 = 5
							} else {
								var _t1473 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1473 = 2
								} else {
									var _t1474 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1474 = 12
									} else {
										var _t1475 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1475 = 3
										} else {
											var _t1476 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1476 = 7
											} else {
												var _t1477 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1477 = 6
												} else {
													var _t1478 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1478 = 10
													} else {
														var _t1479 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1479 = 9
														} else {
															_t1479 = -1
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
					_t1469 = _t1470
				}
				_t1468 = _t1469
			}
			_t1467 = _t1468
		}
		_t1466 = _t1467
	}
	prediction779 := _t1466
	var _t1480 *pb.Type
	if prediction779 == 13 {
		_t1481 := p.parse_uint32_type()
		uint32_type793 := _t1481
		_t1482 := &pb.Type{}
		_t1482.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type793}
		_t1480 = _t1482
	} else {
		var _t1483 *pb.Type
		if prediction779 == 12 {
			_t1484 := p.parse_float32_type()
			float32_type792 := _t1484
			_t1485 := &pb.Type{}
			_t1485.Type = &pb.Type_Float32Type{Float32Type: float32_type792}
			_t1483 = _t1485
		} else {
			var _t1486 *pb.Type
			if prediction779 == 11 {
				_t1487 := p.parse_int32_type()
				int32_type791 := _t1487
				_t1488 := &pb.Type{}
				_t1488.Type = &pb.Type_Int32Type{Int32Type: int32_type791}
				_t1486 = _t1488
			} else {
				var _t1489 *pb.Type
				if prediction779 == 10 {
					_t1490 := p.parse_boolean_type()
					boolean_type790 := _t1490
					_t1491 := &pb.Type{}
					_t1491.Type = &pb.Type_BooleanType{BooleanType: boolean_type790}
					_t1489 = _t1491
				} else {
					var _t1492 *pb.Type
					if prediction779 == 9 {
						_t1493 := p.parse_decimal_type()
						decimal_type789 := _t1493
						_t1494 := &pb.Type{}
						_t1494.Type = &pb.Type_DecimalType{DecimalType: decimal_type789}
						_t1492 = _t1494
					} else {
						var _t1495 *pb.Type
						if prediction779 == 8 {
							_t1496 := p.parse_missing_type()
							missing_type788 := _t1496
							_t1497 := &pb.Type{}
							_t1497.Type = &pb.Type_MissingType{MissingType: missing_type788}
							_t1495 = _t1497
						} else {
							var _t1498 *pb.Type
							if prediction779 == 7 {
								_t1499 := p.parse_datetime_type()
								datetime_type787 := _t1499
								_t1500 := &pb.Type{}
								_t1500.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type787}
								_t1498 = _t1500
							} else {
								var _t1501 *pb.Type
								if prediction779 == 6 {
									_t1502 := p.parse_date_type()
									date_type786 := _t1502
									_t1503 := &pb.Type{}
									_t1503.Type = &pb.Type_DateType{DateType: date_type786}
									_t1501 = _t1503
								} else {
									var _t1504 *pb.Type
									if prediction779 == 5 {
										_t1505 := p.parse_int128_type()
										int128_type785 := _t1505
										_t1506 := &pb.Type{}
										_t1506.Type = &pb.Type_Int128Type{Int128Type: int128_type785}
										_t1504 = _t1506
									} else {
										var _t1507 *pb.Type
										if prediction779 == 4 {
											_t1508 := p.parse_uint128_type()
											uint128_type784 := _t1508
											_t1509 := &pb.Type{}
											_t1509.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type784}
											_t1507 = _t1509
										} else {
											var _t1510 *pb.Type
											if prediction779 == 3 {
												_t1511 := p.parse_float_type()
												float_type783 := _t1511
												_t1512 := &pb.Type{}
												_t1512.Type = &pb.Type_FloatType{FloatType: float_type783}
												_t1510 = _t1512
											} else {
												var _t1513 *pb.Type
												if prediction779 == 2 {
													_t1514 := p.parse_int_type()
													int_type782 := _t1514
													_t1515 := &pb.Type{}
													_t1515.Type = &pb.Type_IntType{IntType: int_type782}
													_t1513 = _t1515
												} else {
													var _t1516 *pb.Type
													if prediction779 == 1 {
														_t1517 := p.parse_string_type()
														string_type781 := _t1517
														_t1518 := &pb.Type{}
														_t1518.Type = &pb.Type_StringType{StringType: string_type781}
														_t1516 = _t1518
													} else {
														var _t1519 *pb.Type
														if prediction779 == 0 {
															_t1520 := p.parse_unspecified_type()
															unspecified_type780 := _t1520
															_t1521 := &pb.Type{}
															_t1521.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type780}
															_t1519 = _t1521
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1489 = _t1492
				}
				_t1486 = _t1489
			}
			_t1483 = _t1486
		}
		_t1480 = _t1483
	}
	result795 := _t1480
	p.recordSpan(int(span_start794), "Type")
	return result795
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1522 := &pb.UnspecifiedType{}
	result797 := _t1522
	p.recordSpan(int(span_start796), "UnspecifiedType")
	return result797
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1523 := &pb.StringType{}
	result799 := _t1523
	p.recordSpan(int(span_start798), "StringType")
	return result799
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1524 := &pb.IntType{}
	result801 := _t1524
	p.recordSpan(int(span_start800), "IntType")
	return result801
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1525 := &pb.FloatType{}
	result803 := _t1525
	p.recordSpan(int(span_start802), "FloatType")
	return result803
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1526 := &pb.UInt128Type{}
	result805 := _t1526
	p.recordSpan(int(span_start804), "UInt128Type")
	return result805
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1527 := &pb.Int128Type{}
	result807 := _t1527
	p.recordSpan(int(span_start806), "Int128Type")
	return result807
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1528 := &pb.DateType{}
	result809 := _t1528
	p.recordSpan(int(span_start808), "DateType")
	return result809
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1529 := &pb.DateTimeType{}
	result811 := _t1529
	p.recordSpan(int(span_start810), "DateTimeType")
	return result811
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1530 := &pb.MissingType{}
	result813 := _t1530
	p.recordSpan(int(span_start812), "MissingType")
	return result813
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int814 := p.consumeTerminal("INT").Value.i64
	int_3815 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1531 := &pb.DecimalType{Precision: int32(int814), Scale: int32(int_3815)}
	result817 := _t1531
	p.recordSpan(int(span_start816), "DecimalType")
	return result817
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1532 := &pb.BooleanType{}
	result819 := _t1532
	p.recordSpan(int(span_start818), "BooleanType")
	return result819
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start820 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1533 := &pb.Int32Type{}
	result821 := _t1533
	p.recordSpan(int(span_start820), "Int32Type")
	return result821
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1534 := &pb.Float32Type{}
	result823 := _t1534
	p.recordSpan(int(span_start822), "Float32Type")
	return result823
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1535 := &pb.UInt32Type{}
	result825 := _t1535
	p.recordSpan(int(span_start824), "UInt32Type")
	return result825
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs826 := []*pb.Binding{}
	cond827 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond827 {
		_t1536 := p.parse_binding()
		item828 := _t1536
		xs826 = append(xs826, item828)
		cond827 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings829 := xs826
	return bindings829
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start844 := int64(p.spanStart())
	var _t1537 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1538 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1538 = 0
		} else {
			var _t1539 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1539 = 11
			} else {
				var _t1540 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1540 = 3
				} else {
					var _t1541 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1541 = 10
					} else {
						var _t1542 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1542 = 9
						} else {
							var _t1543 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1543 = 5
							} else {
								var _t1544 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1544 = 6
								} else {
									var _t1545 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1545 = 7
									} else {
										var _t1546 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1546 = 1
										} else {
											var _t1547 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1547 = 2
											} else {
												var _t1548 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1548 = 12
												} else {
													var _t1549 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1549 = 8
													} else {
														var _t1550 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1550 = 4
														} else {
															var _t1551 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1551 = 10
															} else {
																var _t1552 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1552 = 10
																} else {
																	var _t1553 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1553 = 10
																	} else {
																		var _t1554 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1554 = 10
																		} else {
																			var _t1555 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1555 = 10
																			} else {
																				var _t1556 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1556 = 10
																				} else {
																					var _t1557 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1557 = 10
																					} else {
																						var _t1558 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1558 = 10
																						} else {
																							var _t1559 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1559 = 10
																							} else {
																								_t1559 = -1
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
					}
					_t1540 = _t1541
				}
				_t1539 = _t1540
			}
			_t1538 = _t1539
		}
		_t1537 = _t1538
	} else {
		_t1537 = -1
	}
	prediction830 := _t1537
	var _t1560 *pb.Formula
	if prediction830 == 12 {
		_t1561 := p.parse_cast()
		cast843 := _t1561
		_t1562 := &pb.Formula{}
		_t1562.FormulaType = &pb.Formula_Cast{Cast: cast843}
		_t1560 = _t1562
	} else {
		var _t1563 *pb.Formula
		if prediction830 == 11 {
			_t1564 := p.parse_rel_atom()
			rel_atom842 := _t1564
			_t1565 := &pb.Formula{}
			_t1565.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom842}
			_t1563 = _t1565
		} else {
			var _t1566 *pb.Formula
			if prediction830 == 10 {
				_t1567 := p.parse_primitive()
				primitive841 := _t1567
				_t1568 := &pb.Formula{}
				_t1568.FormulaType = &pb.Formula_Primitive{Primitive: primitive841}
				_t1566 = _t1568
			} else {
				var _t1569 *pb.Formula
				if prediction830 == 9 {
					_t1570 := p.parse_pragma()
					pragma840 := _t1570
					_t1571 := &pb.Formula{}
					_t1571.FormulaType = &pb.Formula_Pragma{Pragma: pragma840}
					_t1569 = _t1571
				} else {
					var _t1572 *pb.Formula
					if prediction830 == 8 {
						_t1573 := p.parse_atom()
						atom839 := _t1573
						_t1574 := &pb.Formula{}
						_t1574.FormulaType = &pb.Formula_Atom{Atom: atom839}
						_t1572 = _t1574
					} else {
						var _t1575 *pb.Formula
						if prediction830 == 7 {
							_t1576 := p.parse_ffi()
							ffi838 := _t1576
							_t1577 := &pb.Formula{}
							_t1577.FormulaType = &pb.Formula_Ffi{Ffi: ffi838}
							_t1575 = _t1577
						} else {
							var _t1578 *pb.Formula
							if prediction830 == 6 {
								_t1579 := p.parse_not()
								not837 := _t1579
								_t1580 := &pb.Formula{}
								_t1580.FormulaType = &pb.Formula_Not{Not: not837}
								_t1578 = _t1580
							} else {
								var _t1581 *pb.Formula
								if prediction830 == 5 {
									_t1582 := p.parse_disjunction()
									disjunction836 := _t1582
									_t1583 := &pb.Formula{}
									_t1583.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction836}
									_t1581 = _t1583
								} else {
									var _t1584 *pb.Formula
									if prediction830 == 4 {
										_t1585 := p.parse_conjunction()
										conjunction835 := _t1585
										_t1586 := &pb.Formula{}
										_t1586.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction835}
										_t1584 = _t1586
									} else {
										var _t1587 *pb.Formula
										if prediction830 == 3 {
											_t1588 := p.parse_reduce()
											reduce834 := _t1588
											_t1589 := &pb.Formula{}
											_t1589.FormulaType = &pb.Formula_Reduce{Reduce: reduce834}
											_t1587 = _t1589
										} else {
											var _t1590 *pb.Formula
											if prediction830 == 2 {
												_t1591 := p.parse_exists()
												exists833 := _t1591
												_t1592 := &pb.Formula{}
												_t1592.FormulaType = &pb.Formula_Exists{Exists: exists833}
												_t1590 = _t1592
											} else {
												var _t1593 *pb.Formula
												if prediction830 == 1 {
													_t1594 := p.parse_false()
													false832 := _t1594
													_t1595 := &pb.Formula{}
													_t1595.FormulaType = &pb.Formula_Disjunction{Disjunction: false832}
													_t1593 = _t1595
												} else {
													var _t1596 *pb.Formula
													if prediction830 == 0 {
														_t1597 := p.parse_true()
														true831 := _t1597
														_t1598 := &pb.Formula{}
														_t1598.FormulaType = &pb.Formula_Conjunction{Conjunction: true831}
														_t1596 = _t1598
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1569 = _t1572
				}
				_t1566 = _t1569
			}
			_t1563 = _t1566
		}
		_t1560 = _t1563
	}
	result845 := _t1560
	p.recordSpan(int(span_start844), "Formula")
	return result845
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start846 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1599 := &pb.Conjunction{Args: []*pb.Formula{}}
	result847 := _t1599
	p.recordSpan(int(span_start846), "Conjunction")
	return result847
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1600 := &pb.Disjunction{Args: []*pb.Formula{}}
	result849 := _t1600
	p.recordSpan(int(span_start848), "Disjunction")
	return result849
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1601 := p.parse_bindings()
	bindings850 := _t1601
	_t1602 := p.parse_formula()
	formula851 := _t1602
	p.consumeLiteral(")")
	_t1603 := &pb.Abstraction{Vars: listConcat(bindings850[0].([]*pb.Binding), bindings850[1].([]*pb.Binding)), Value: formula851}
	_t1604 := &pb.Exists{Body: _t1603}
	result853 := _t1604
	p.recordSpan(int(span_start852), "Exists")
	return result853
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1605 := p.parse_abstraction()
	abstraction854 := _t1605
	_t1606 := p.parse_abstraction()
	abstraction_3855 := _t1606
	_t1607 := p.parse_terms()
	terms856 := _t1607
	p.consumeLiteral(")")
	_t1608 := &pb.Reduce{Op: abstraction854, Body: abstraction_3855, Terms: terms856}
	result858 := _t1608
	p.recordSpan(int(span_start857), "Reduce")
	return result858
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs859 := []*pb.Term{}
	cond860 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond860 {
		_t1609 := p.parse_term()
		item861 := _t1609
		xs859 = append(xs859, item861)
		cond860 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms862 := xs859
	p.consumeLiteral(")")
	return terms862
}

func (p *Parser) parse_term() *pb.Term {
	span_start866 := int64(p.spanStart())
	var _t1610 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1610 = 1
	} else {
		var _t1611 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1611 = 1
		} else {
			var _t1612 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1612 = 1
			} else {
				var _t1613 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1613 = 1
				} else {
					var _t1614 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1614 = 0
					} else {
						var _t1615 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1615 = 1
						} else {
							var _t1616 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1616 = 1
							} else {
								var _t1617 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1617 = 1
								} else {
									var _t1618 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1618 = 1
									} else {
										var _t1619 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1619 = 1
										} else {
											var _t1620 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1620 = 1
											} else {
												var _t1621 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1621 = 1
												} else {
													var _t1622 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1622 = 1
													} else {
														var _t1623 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1623 = 1
														} else {
															_t1623 = -1
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
					_t1613 = _t1614
				}
				_t1612 = _t1613
			}
			_t1611 = _t1612
		}
		_t1610 = _t1611
	}
	prediction863 := _t1610
	var _t1624 *pb.Term
	if prediction863 == 1 {
		_t1625 := p.parse_value()
		value865 := _t1625
		_t1626 := &pb.Term{}
		_t1626.TermType = &pb.Term_Constant{Constant: value865}
		_t1624 = _t1626
	} else {
		var _t1627 *pb.Term
		if prediction863 == 0 {
			_t1628 := p.parse_var()
			var864 := _t1628
			_t1629 := &pb.Term{}
			_t1629.TermType = &pb.Term_Var{Var: var864}
			_t1627 = _t1629
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1624 = _t1627
	}
	result867 := _t1624
	p.recordSpan(int(span_start866), "Term")
	return result867
}

func (p *Parser) parse_var() *pb.Var {
	span_start869 := int64(p.spanStart())
	symbol868 := p.consumeTerminal("SYMBOL").Value.str
	_t1630 := &pb.Var{Name: symbol868}
	result870 := _t1630
	p.recordSpan(int(span_start869), "Var")
	return result870
}

func (p *Parser) parse_value() *pb.Value {
	span_start884 := int64(p.spanStart())
	var _t1631 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1631 = 12
	} else {
		var _t1632 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1632 = 11
		} else {
			var _t1633 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1633 = 12
			} else {
				var _t1634 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1635 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1635 = 1
					} else {
						var _t1636 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1636 = 0
						} else {
							_t1636 = -1
						}
						_t1635 = _t1636
					}
					_t1634 = _t1635
				} else {
					var _t1637 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1637 = 7
					} else {
						var _t1638 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1638 = 8
						} else {
							var _t1639 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1639 = 2
							} else {
								var _t1640 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1640 = 3
								} else {
									var _t1641 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1641 = 9
									} else {
										var _t1642 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1642 = 4
										} else {
											var _t1643 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1643 = 5
											} else {
												var _t1644 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1644 = 6
												} else {
													var _t1645 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1645 = 10
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
					_t1634 = _t1637
				}
				_t1633 = _t1634
			}
			_t1632 = _t1633
		}
		_t1631 = _t1632
	}
	prediction871 := _t1631
	var _t1646 *pb.Value
	if prediction871 == 12 {
		_t1647 := p.parse_boolean_value()
		boolean_value883 := _t1647
		_t1648 := &pb.Value{}
		_t1648.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value883}
		_t1646 = _t1648
	} else {
		var _t1649 *pb.Value
		if prediction871 == 11 {
			p.consumeLiteral("missing")
			_t1650 := &pb.MissingValue{}
			_t1651 := &pb.Value{}
			_t1651.Value = &pb.Value_MissingValue{MissingValue: _t1650}
			_t1649 = _t1651
		} else {
			var _t1652 *pb.Value
			if prediction871 == 10 {
				formatted_decimal882 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1653 := &pb.Value{}
				_t1653.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal882}
				_t1652 = _t1653
			} else {
				var _t1654 *pb.Value
				if prediction871 == 9 {
					formatted_int128881 := p.consumeTerminal("INT128").Value.int128
					_t1655 := &pb.Value{}
					_t1655.Value = &pb.Value_Int128Value{Int128Value: formatted_int128881}
					_t1654 = _t1655
				} else {
					var _t1656 *pb.Value
					if prediction871 == 8 {
						formatted_uint128880 := p.consumeTerminal("UINT128").Value.uint128
						_t1657 := &pb.Value{}
						_t1657.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128880}
						_t1656 = _t1657
					} else {
						var _t1658 *pb.Value
						if prediction871 == 7 {
							formatted_uint32879 := p.consumeTerminal("UINT32").Value.u32
							_t1659 := &pb.Value{}
							_t1659.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32879}
							_t1658 = _t1659
						} else {
							var _t1660 *pb.Value
							if prediction871 == 6 {
								formatted_float878 := p.consumeTerminal("FLOAT").Value.f64
								_t1661 := &pb.Value{}
								_t1661.Value = &pb.Value_FloatValue{FloatValue: formatted_float878}
								_t1660 = _t1661
							} else {
								var _t1662 *pb.Value
								if prediction871 == 5 {
									formatted_float32877 := p.consumeTerminal("FLOAT32").Value.f32
									_t1663 := &pb.Value{}
									_t1663.Value = &pb.Value_Float32Value{Float32Value: formatted_float32877}
									_t1662 = _t1663
								} else {
									var _t1664 *pb.Value
									if prediction871 == 4 {
										formatted_int876 := p.consumeTerminal("INT").Value.i64
										_t1665 := &pb.Value{}
										_t1665.Value = &pb.Value_IntValue{IntValue: formatted_int876}
										_t1664 = _t1665
									} else {
										var _t1666 *pb.Value
										if prediction871 == 3 {
											formatted_int32875 := p.consumeTerminal("INT32").Value.i32
											_t1667 := &pb.Value{}
											_t1667.Value = &pb.Value_Int32Value{Int32Value: formatted_int32875}
											_t1666 = _t1667
										} else {
											var _t1668 *pb.Value
											if prediction871 == 2 {
												formatted_string874 := p.consumeTerminal("STRING").Value.str
												_t1669 := &pb.Value{}
												_t1669.Value = &pb.Value_StringValue{StringValue: formatted_string874}
												_t1668 = _t1669
											} else {
												var _t1670 *pb.Value
												if prediction871 == 1 {
													_t1671 := p.parse_datetime()
													datetime873 := _t1671
													_t1672 := &pb.Value{}
													_t1672.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime873}
													_t1670 = _t1672
												} else {
													var _t1673 *pb.Value
													if prediction871 == 0 {
														_t1674 := p.parse_date()
														date872 := _t1674
														_t1675 := &pb.Value{}
														_t1675.Value = &pb.Value_DateValue{DateValue: date872}
														_t1673 = _t1675
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1670 = _t1673
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
					_t1654 = _t1656
				}
				_t1652 = _t1654
			}
			_t1649 = _t1652
		}
		_t1646 = _t1649
	}
	result885 := _t1646
	p.recordSpan(int(span_start884), "Value")
	return result885
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start889 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int886 := p.consumeTerminal("INT").Value.i64
	formatted_int_3887 := p.consumeTerminal("INT").Value.i64
	formatted_int_4888 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1676 := &pb.DateValue{Year: int32(formatted_int886), Month: int32(formatted_int_3887), Day: int32(formatted_int_4888)}
	result890 := _t1676
	p.recordSpan(int(span_start889), "DateValue")
	return result890
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start898 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int891 := p.consumeTerminal("INT").Value.i64
	formatted_int_3892 := p.consumeTerminal("INT").Value.i64
	formatted_int_4893 := p.consumeTerminal("INT").Value.i64
	formatted_int_5894 := p.consumeTerminal("INT").Value.i64
	formatted_int_6895 := p.consumeTerminal("INT").Value.i64
	formatted_int_7896 := p.consumeTerminal("INT").Value.i64
	var _t1677 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1677 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8897 := _t1677
	p.consumeLiteral(")")
	_t1678 := &pb.DateTimeValue{Year: int32(formatted_int891), Month: int32(formatted_int_3892), Day: int32(formatted_int_4893), Hour: int32(formatted_int_5894), Minute: int32(formatted_int_6895), Second: int32(formatted_int_7896), Microsecond: int32(deref(formatted_int_8897, 0))}
	result899 := _t1678
	p.recordSpan(int(span_start898), "DateTimeValue")
	return result899
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs900 := []*pb.Formula{}
	cond901 := p.matchLookaheadLiteral("(", 0)
	for cond901 {
		_t1679 := p.parse_formula()
		item902 := _t1679
		xs900 = append(xs900, item902)
		cond901 = p.matchLookaheadLiteral("(", 0)
	}
	formulas903 := xs900
	p.consumeLiteral(")")
	_t1680 := &pb.Conjunction{Args: formulas903}
	result905 := _t1680
	p.recordSpan(int(span_start904), "Conjunction")
	return result905
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start910 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs906 := []*pb.Formula{}
	cond907 := p.matchLookaheadLiteral("(", 0)
	for cond907 {
		_t1681 := p.parse_formula()
		item908 := _t1681
		xs906 = append(xs906, item908)
		cond907 = p.matchLookaheadLiteral("(", 0)
	}
	formulas909 := xs906
	p.consumeLiteral(")")
	_t1682 := &pb.Disjunction{Args: formulas909}
	result911 := _t1682
	p.recordSpan(int(span_start910), "Disjunction")
	return result911
}

func (p *Parser) parse_not() *pb.Not {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1683 := p.parse_formula()
	formula912 := _t1683
	p.consumeLiteral(")")
	_t1684 := &pb.Not{Arg: formula912}
	result914 := _t1684
	p.recordSpan(int(span_start913), "Not")
	return result914
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1685 := p.parse_name()
	name915 := _t1685
	_t1686 := p.parse_ffi_args()
	ffi_args916 := _t1686
	_t1687 := p.parse_terms()
	terms917 := _t1687
	p.consumeLiteral(")")
	_t1688 := &pb.FFI{Name: name915, Args: ffi_args916, Terms: terms917}
	result919 := _t1688
	p.recordSpan(int(span_start918), "FFI")
	return result919
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol920 := p.consumeTerminal("SYMBOL").Value.str
	return symbol920
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs921 := []*pb.Abstraction{}
	cond922 := p.matchLookaheadLiteral("(", 0)
	for cond922 {
		_t1689 := p.parse_abstraction()
		item923 := _t1689
		xs921 = append(xs921, item923)
		cond922 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions924 := xs921
	p.consumeLiteral(")")
	return abstractions924
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start930 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1690 := p.parse_relation_id()
	relation_id925 := _t1690
	xs926 := []*pb.Term{}
	cond927 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond927 {
		_t1691 := p.parse_term()
		item928 := _t1691
		xs926 = append(xs926, item928)
		cond927 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms929 := xs926
	p.consumeLiteral(")")
	_t1692 := &pb.Atom{Name: relation_id925, Terms: terms929}
	result931 := _t1692
	p.recordSpan(int(span_start930), "Atom")
	return result931
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start937 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1693 := p.parse_name()
	name932 := _t1693
	xs933 := []*pb.Term{}
	cond934 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond934 {
		_t1694 := p.parse_term()
		item935 := _t1694
		xs933 = append(xs933, item935)
		cond934 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms936 := xs933
	p.consumeLiteral(")")
	_t1695 := &pb.Pragma{Name: name932, Terms: terms936}
	result938 := _t1695
	p.recordSpan(int(span_start937), "Pragma")
	return result938
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start954 := int64(p.spanStart())
	var _t1696 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1697 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1697 = 9
		} else {
			var _t1698 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1698 = 4
			} else {
				var _t1699 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1699 = 3
				} else {
					var _t1700 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1700 = 0
					} else {
						var _t1701 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1701 = 2
						} else {
							var _t1702 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1702 = 1
							} else {
								var _t1703 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1703 = 8
								} else {
									var _t1704 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1704 = 6
									} else {
										var _t1705 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1705 = 5
										} else {
											var _t1706 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1706 = 7
											} else {
												_t1706 = -1
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
					}
					_t1699 = _t1700
				}
				_t1698 = _t1699
			}
			_t1697 = _t1698
		}
		_t1696 = _t1697
	} else {
		_t1696 = -1
	}
	prediction939 := _t1696
	var _t1707 *pb.Primitive
	if prediction939 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1708 := p.parse_name()
		name949 := _t1708
		xs950 := []*pb.RelTerm{}
		cond951 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond951 {
			_t1709 := p.parse_rel_term()
			item952 := _t1709
			xs950 = append(xs950, item952)
			cond951 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms953 := xs950
		p.consumeLiteral(")")
		_t1710 := &pb.Primitive{Name: name949, Terms: rel_terms953}
		_t1707 = _t1710
	} else {
		var _t1711 *pb.Primitive
		if prediction939 == 8 {
			_t1712 := p.parse_divide()
			divide948 := _t1712
			_t1711 = divide948
		} else {
			var _t1713 *pb.Primitive
			if prediction939 == 7 {
				_t1714 := p.parse_multiply()
				multiply947 := _t1714
				_t1713 = multiply947
			} else {
				var _t1715 *pb.Primitive
				if prediction939 == 6 {
					_t1716 := p.parse_minus()
					minus946 := _t1716
					_t1715 = minus946
				} else {
					var _t1717 *pb.Primitive
					if prediction939 == 5 {
						_t1718 := p.parse_add()
						add945 := _t1718
						_t1717 = add945
					} else {
						var _t1719 *pb.Primitive
						if prediction939 == 4 {
							_t1720 := p.parse_gt_eq()
							gt_eq944 := _t1720
							_t1719 = gt_eq944
						} else {
							var _t1721 *pb.Primitive
							if prediction939 == 3 {
								_t1722 := p.parse_gt()
								gt943 := _t1722
								_t1721 = gt943
							} else {
								var _t1723 *pb.Primitive
								if prediction939 == 2 {
									_t1724 := p.parse_lt_eq()
									lt_eq942 := _t1724
									_t1723 = lt_eq942
								} else {
									var _t1725 *pb.Primitive
									if prediction939 == 1 {
										_t1726 := p.parse_lt()
										lt941 := _t1726
										_t1725 = lt941
									} else {
										var _t1727 *pb.Primitive
										if prediction939 == 0 {
											_t1728 := p.parse_eq()
											eq940 := _t1728
											_t1727 = eq940
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
				_t1713 = _t1715
			}
			_t1711 = _t1713
		}
		_t1707 = _t1711
	}
	result955 := _t1707
	p.recordSpan(int(span_start954), "Primitive")
	return result955
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start958 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1729 := p.parse_term()
	term956 := _t1729
	_t1730 := p.parse_term()
	term_3957 := _t1730
	p.consumeLiteral(")")
	_t1731 := &pb.RelTerm{}
	_t1731.RelTermType = &pb.RelTerm_Term{Term: term956}
	_t1732 := &pb.RelTerm{}
	_t1732.RelTermType = &pb.RelTerm_Term{Term: term_3957}
	_t1733 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1731, _t1732}}
	result959 := _t1733
	p.recordSpan(int(span_start958), "Primitive")
	return result959
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start962 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1734 := p.parse_term()
	term960 := _t1734
	_t1735 := p.parse_term()
	term_3961 := _t1735
	p.consumeLiteral(")")
	_t1736 := &pb.RelTerm{}
	_t1736.RelTermType = &pb.RelTerm_Term{Term: term960}
	_t1737 := &pb.RelTerm{}
	_t1737.RelTermType = &pb.RelTerm_Term{Term: term_3961}
	_t1738 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1736, _t1737}}
	result963 := _t1738
	p.recordSpan(int(span_start962), "Primitive")
	return result963
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start966 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1739 := p.parse_term()
	term964 := _t1739
	_t1740 := p.parse_term()
	term_3965 := _t1740
	p.consumeLiteral(")")
	_t1741 := &pb.RelTerm{}
	_t1741.RelTermType = &pb.RelTerm_Term{Term: term964}
	_t1742 := &pb.RelTerm{}
	_t1742.RelTermType = &pb.RelTerm_Term{Term: term_3965}
	_t1743 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1741, _t1742}}
	result967 := _t1743
	p.recordSpan(int(span_start966), "Primitive")
	return result967
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start970 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1744 := p.parse_term()
	term968 := _t1744
	_t1745 := p.parse_term()
	term_3969 := _t1745
	p.consumeLiteral(")")
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term968}
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term_3969}
	_t1748 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1746, _t1747}}
	result971 := _t1748
	p.recordSpan(int(span_start970), "Primitive")
	return result971
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1749 := p.parse_term()
	term972 := _t1749
	_t1750 := p.parse_term()
	term_3973 := _t1750
	p.consumeLiteral(")")
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term972}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_3973}
	_t1753 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1751, _t1752}}
	result975 := _t1753
	p.recordSpan(int(span_start974), "Primitive")
	return result975
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1754 := p.parse_term()
	term976 := _t1754
	_t1755 := p.parse_term()
	term_3977 := _t1755
	_t1756 := p.parse_term()
	term_4978 := _t1756
	p.consumeLiteral(")")
	_t1757 := &pb.RelTerm{}
	_t1757.RelTermType = &pb.RelTerm_Term{Term: term976}
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term_3977}
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term_4978}
	_t1760 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1757, _t1758, _t1759}}
	result980 := _t1760
	p.recordSpan(int(span_start979), "Primitive")
	return result980
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1761 := p.parse_term()
	term981 := _t1761
	_t1762 := p.parse_term()
	term_3982 := _t1762
	_t1763 := p.parse_term()
	term_4983 := _t1763
	p.consumeLiteral(")")
	_t1764 := &pb.RelTerm{}
	_t1764.RelTermType = &pb.RelTerm_Term{Term: term981}
	_t1765 := &pb.RelTerm{}
	_t1765.RelTermType = &pb.RelTerm_Term{Term: term_3982}
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term_4983}
	_t1767 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1764, _t1765, _t1766}}
	result985 := _t1767
	p.recordSpan(int(span_start984), "Primitive")
	return result985
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start989 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1768 := p.parse_term()
	term986 := _t1768
	_t1769 := p.parse_term()
	term_3987 := _t1769
	_t1770 := p.parse_term()
	term_4988 := _t1770
	p.consumeLiteral(")")
	_t1771 := &pb.RelTerm{}
	_t1771.RelTermType = &pb.RelTerm_Term{Term: term986}
	_t1772 := &pb.RelTerm{}
	_t1772.RelTermType = &pb.RelTerm_Term{Term: term_3987}
	_t1773 := &pb.RelTerm{}
	_t1773.RelTermType = &pb.RelTerm_Term{Term: term_4988}
	_t1774 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1771, _t1772, _t1773}}
	result990 := _t1774
	p.recordSpan(int(span_start989), "Primitive")
	return result990
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start994 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1775 := p.parse_term()
	term991 := _t1775
	_t1776 := p.parse_term()
	term_3992 := _t1776
	_t1777 := p.parse_term()
	term_4993 := _t1777
	p.consumeLiteral(")")
	_t1778 := &pb.RelTerm{}
	_t1778.RelTermType = &pb.RelTerm_Term{Term: term991}
	_t1779 := &pb.RelTerm{}
	_t1779.RelTermType = &pb.RelTerm_Term{Term: term_3992}
	_t1780 := &pb.RelTerm{}
	_t1780.RelTermType = &pb.RelTerm_Term{Term: term_4993}
	_t1781 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1778, _t1779, _t1780}}
	result995 := _t1781
	p.recordSpan(int(span_start994), "Primitive")
	return result995
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start999 := int64(p.spanStart())
	var _t1782 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1782 = 1
	} else {
		var _t1783 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1783 = 1
		} else {
			var _t1784 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1784 = 1
			} else {
				var _t1785 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1785 = 1
				} else {
					var _t1786 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1786 = 0
					} else {
						var _t1787 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1787 = 1
						} else {
							var _t1788 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1788 = 1
							} else {
								var _t1789 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1789 = 1
								} else {
									var _t1790 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1790 = 1
									} else {
										var _t1791 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1791 = 1
										} else {
											var _t1792 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1792 = 1
											} else {
												var _t1793 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1793 = 1
												} else {
													var _t1794 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1794 = 1
													} else {
														var _t1795 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1795 = 1
														} else {
															var _t1796 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1796 = 1
															} else {
																_t1796 = -1
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
					_t1785 = _t1786
				}
				_t1784 = _t1785
			}
			_t1783 = _t1784
		}
		_t1782 = _t1783
	}
	prediction996 := _t1782
	var _t1797 *pb.RelTerm
	if prediction996 == 1 {
		_t1798 := p.parse_term()
		term998 := _t1798
		_t1799 := &pb.RelTerm{}
		_t1799.RelTermType = &pb.RelTerm_Term{Term: term998}
		_t1797 = _t1799
	} else {
		var _t1800 *pb.RelTerm
		if prediction996 == 0 {
			_t1801 := p.parse_specialized_value()
			specialized_value997 := _t1801
			_t1802 := &pb.RelTerm{}
			_t1802.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value997}
			_t1800 = _t1802
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1797 = _t1800
	}
	result1000 := _t1797
	p.recordSpan(int(span_start999), "RelTerm")
	return result1000
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1803 := p.parse_raw_value()
	raw_value1001 := _t1803
	result1003 := raw_value1001
	p.recordSpan(int(span_start1002), "Value")
	return result1003
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1804 := p.parse_name()
	name1004 := _t1804
	xs1005 := []*pb.RelTerm{}
	cond1006 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1006 {
		_t1805 := p.parse_rel_term()
		item1007 := _t1805
		xs1005 = append(xs1005, item1007)
		cond1006 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1008 := xs1005
	p.consumeLiteral(")")
	_t1806 := &pb.RelAtom{Name: name1004, Terms: rel_terms1008}
	result1010 := _t1806
	p.recordSpan(int(span_start1009), "RelAtom")
	return result1010
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1013 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1807 := p.parse_term()
	term1011 := _t1807
	_t1808 := p.parse_term()
	term_31012 := _t1808
	p.consumeLiteral(")")
	_t1809 := &pb.Cast{Input: term1011, Result: term_31012}
	result1014 := _t1809
	p.recordSpan(int(span_start1013), "Cast")
	return result1014
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1015 := []*pb.Attribute{}
	cond1016 := p.matchLookaheadLiteral("(", 0)
	for cond1016 {
		_t1810 := p.parse_attribute()
		item1017 := _t1810
		xs1015 = append(xs1015, item1017)
		cond1016 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1018 := xs1015
	p.consumeLiteral(")")
	return attributes1018
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1811 := p.parse_name()
	name1019 := _t1811
	xs1020 := []*pb.Value{}
	cond1021 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1021 {
		_t1812 := p.parse_raw_value()
		item1022 := _t1812
		xs1020 = append(xs1020, item1022)
		cond1021 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1023 := xs1020
	p.consumeLiteral(")")
	_t1813 := &pb.Attribute{Name: name1019, Args: raw_values1023}
	result1025 := _t1813
	p.recordSpan(int(span_start1024), "Attribute")
	return result1025
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1026 := []*pb.RelationId{}
	cond1027 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1027 {
		_t1814 := p.parse_relation_id()
		item1028 := _t1814
		xs1026 = append(xs1026, item1028)
		cond1027 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1029 := xs1026
	_t1815 := p.parse_script()
	script1030 := _t1815
	var _t1816 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1817 := p.parse_attrs()
		_t1816 = _t1817
	}
	attrs1031 := _t1816
	p.consumeLiteral(")")
	_t1818 := attrs1031
	if attrs1031 == nil {
		_t1818 = []*pb.Attribute{}
	}
	_t1819 := &pb.Algorithm{Global: relation_ids1029, Body: script1030, Attrs: _t1818}
	result1033 := _t1819
	p.recordSpan(int(span_start1032), "Algorithm")
	return result1033
}

func (p *Parser) parse_script() *pb.Script {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1034 := []*pb.Construct{}
	cond1035 := p.matchLookaheadLiteral("(", 0)
	for cond1035 {
		_t1820 := p.parse_construct()
		item1036 := _t1820
		xs1034 = append(xs1034, item1036)
		cond1035 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1037 := xs1034
	p.consumeLiteral(")")
	_t1821 := &pb.Script{Constructs: constructs1037}
	result1039 := _t1821
	p.recordSpan(int(span_start1038), "Script")
	return result1039
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1043 := int64(p.spanStart())
	var _t1822 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1823 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1823 = 1
		} else {
			var _t1824 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1824 = 1
			} else {
				var _t1825 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1825 = 1
				} else {
					var _t1826 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1826 = 0
					} else {
						var _t1827 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1827 = 1
						} else {
							var _t1828 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1828 = 1
							} else {
								_t1828 = -1
							}
							_t1827 = _t1828
						}
						_t1826 = _t1827
					}
					_t1825 = _t1826
				}
				_t1824 = _t1825
			}
			_t1823 = _t1824
		}
		_t1822 = _t1823
	} else {
		_t1822 = -1
	}
	prediction1040 := _t1822
	var _t1829 *pb.Construct
	if prediction1040 == 1 {
		_t1830 := p.parse_instruction()
		instruction1042 := _t1830
		_t1831 := &pb.Construct{}
		_t1831.ConstructType = &pb.Construct_Instruction{Instruction: instruction1042}
		_t1829 = _t1831
	} else {
		var _t1832 *pb.Construct
		if prediction1040 == 0 {
			_t1833 := p.parse_loop()
			loop1041 := _t1833
			_t1834 := &pb.Construct{}
			_t1834.ConstructType = &pb.Construct_Loop{Loop: loop1041}
			_t1832 = _t1834
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1829 = _t1832
	}
	result1044 := _t1829
	p.recordSpan(int(span_start1043), "Construct")
	return result1044
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1048 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1835 := p.parse_init()
	init1045 := _t1835
	_t1836 := p.parse_script()
	script1046 := _t1836
	var _t1837 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1838 := p.parse_attrs()
		_t1837 = _t1838
	}
	attrs1047 := _t1837
	p.consumeLiteral(")")
	_t1839 := attrs1047
	if attrs1047 == nil {
		_t1839 = []*pb.Attribute{}
	}
	_t1840 := &pb.Loop{Init: init1045, Body: script1046, Attrs: _t1839}
	result1049 := _t1840
	p.recordSpan(int(span_start1048), "Loop")
	return result1049
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1050 := []*pb.Instruction{}
	cond1051 := p.matchLookaheadLiteral("(", 0)
	for cond1051 {
		_t1841 := p.parse_instruction()
		item1052 := _t1841
		xs1050 = append(xs1050, item1052)
		cond1051 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1053 := xs1050
	p.consumeLiteral(")")
	return instructions1053
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1060 := int64(p.spanStart())
	var _t1842 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1843 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1843 = 1
		} else {
			var _t1844 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1844 = 4
			} else {
				var _t1845 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1845 = 3
				} else {
					var _t1846 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1846 = 2
					} else {
						var _t1847 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1847 = 0
						} else {
							_t1847 = -1
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
	prediction1054 := _t1842
	var _t1848 *pb.Instruction
	if prediction1054 == 4 {
		_t1849 := p.parse_monus_def()
		monus_def1059 := _t1849
		_t1850 := &pb.Instruction{}
		_t1850.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1059}
		_t1848 = _t1850
	} else {
		var _t1851 *pb.Instruction
		if prediction1054 == 3 {
			_t1852 := p.parse_monoid_def()
			monoid_def1058 := _t1852
			_t1853 := &pb.Instruction{}
			_t1853.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1058}
			_t1851 = _t1853
		} else {
			var _t1854 *pb.Instruction
			if prediction1054 == 2 {
				_t1855 := p.parse_break()
				break1057 := _t1855
				_t1856 := &pb.Instruction{}
				_t1856.InstrType = &pb.Instruction_Break{Break: break1057}
				_t1854 = _t1856
			} else {
				var _t1857 *pb.Instruction
				if prediction1054 == 1 {
					_t1858 := p.parse_upsert()
					upsert1056 := _t1858
					_t1859 := &pb.Instruction{}
					_t1859.InstrType = &pb.Instruction_Upsert{Upsert: upsert1056}
					_t1857 = _t1859
				} else {
					var _t1860 *pb.Instruction
					if prediction1054 == 0 {
						_t1861 := p.parse_assign()
						assign1055 := _t1861
						_t1862 := &pb.Instruction{}
						_t1862.InstrType = &pb.Instruction_Assign{Assign: assign1055}
						_t1860 = _t1862
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1857 = _t1860
				}
				_t1854 = _t1857
			}
			_t1851 = _t1854
		}
		_t1848 = _t1851
	}
	result1061 := _t1848
	p.recordSpan(int(span_start1060), "Instruction")
	return result1061
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1065 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1863 := p.parse_relation_id()
	relation_id1062 := _t1863
	_t1864 := p.parse_abstraction()
	abstraction1063 := _t1864
	var _t1865 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1866 := p.parse_attrs()
		_t1865 = _t1866
	}
	attrs1064 := _t1865
	p.consumeLiteral(")")
	_t1867 := attrs1064
	if attrs1064 == nil {
		_t1867 = []*pb.Attribute{}
	}
	_t1868 := &pb.Assign{Name: relation_id1062, Body: abstraction1063, Attrs: _t1867}
	result1066 := _t1868
	p.recordSpan(int(span_start1065), "Assign")
	return result1066
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1070 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1869 := p.parse_relation_id()
	relation_id1067 := _t1869
	_t1870 := p.parse_abstraction_with_arity()
	abstraction_with_arity1068 := _t1870
	var _t1871 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1872 := p.parse_attrs()
		_t1871 = _t1872
	}
	attrs1069 := _t1871
	p.consumeLiteral(")")
	_t1873 := attrs1069
	if attrs1069 == nil {
		_t1873 = []*pb.Attribute{}
	}
	_t1874 := &pb.Upsert{Name: relation_id1067, Body: abstraction_with_arity1068[0].(*pb.Abstraction), Attrs: _t1873, ValueArity: abstraction_with_arity1068[1].(int64)}
	result1071 := _t1874
	p.recordSpan(int(span_start1070), "Upsert")
	return result1071
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1875 := p.parse_bindings()
	bindings1072 := _t1875
	_t1876 := p.parse_formula()
	formula1073 := _t1876
	p.consumeLiteral(")")
	_t1877 := &pb.Abstraction{Vars: listConcat(bindings1072[0].([]*pb.Binding), bindings1072[1].([]*pb.Binding)), Value: formula1073}
	return []interface{}{_t1877, int64(len(bindings1072[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1077 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1878 := p.parse_relation_id()
	relation_id1074 := _t1878
	_t1879 := p.parse_abstraction()
	abstraction1075 := _t1879
	var _t1880 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1881 := p.parse_attrs()
		_t1880 = _t1881
	}
	attrs1076 := _t1880
	p.consumeLiteral(")")
	_t1882 := attrs1076
	if attrs1076 == nil {
		_t1882 = []*pb.Attribute{}
	}
	_t1883 := &pb.Break{Name: relation_id1074, Body: abstraction1075, Attrs: _t1882}
	result1078 := _t1883
	p.recordSpan(int(span_start1077), "Break")
	return result1078
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1083 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1884 := p.parse_monoid()
	monoid1079 := _t1884
	_t1885 := p.parse_relation_id()
	relation_id1080 := _t1885
	_t1886 := p.parse_abstraction_with_arity()
	abstraction_with_arity1081 := _t1886
	var _t1887 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1888 := p.parse_attrs()
		_t1887 = _t1888
	}
	attrs1082 := _t1887
	p.consumeLiteral(")")
	_t1889 := attrs1082
	if attrs1082 == nil {
		_t1889 = []*pb.Attribute{}
	}
	_t1890 := &pb.MonoidDef{Monoid: monoid1079, Name: relation_id1080, Body: abstraction_with_arity1081[0].(*pb.Abstraction), Attrs: _t1889, ValueArity: abstraction_with_arity1081[1].(int64)}
	result1084 := _t1890
	p.recordSpan(int(span_start1083), "MonoidDef")
	return result1084
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1090 := int64(p.spanStart())
	var _t1891 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1892 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1892 = 3
		} else {
			var _t1893 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1893 = 0
			} else {
				var _t1894 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1894 = 1
				} else {
					var _t1895 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1895 = 2
					} else {
						_t1895 = -1
					}
					_t1894 = _t1895
				}
				_t1893 = _t1894
			}
			_t1892 = _t1893
		}
		_t1891 = _t1892
	} else {
		_t1891 = -1
	}
	prediction1085 := _t1891
	var _t1896 *pb.Monoid
	if prediction1085 == 3 {
		_t1897 := p.parse_sum_monoid()
		sum_monoid1089 := _t1897
		_t1898 := &pb.Monoid{}
		_t1898.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1089}
		_t1896 = _t1898
	} else {
		var _t1899 *pb.Monoid
		if prediction1085 == 2 {
			_t1900 := p.parse_max_monoid()
			max_monoid1088 := _t1900
			_t1901 := &pb.Monoid{}
			_t1901.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1088}
			_t1899 = _t1901
		} else {
			var _t1902 *pb.Monoid
			if prediction1085 == 1 {
				_t1903 := p.parse_min_monoid()
				min_monoid1087 := _t1903
				_t1904 := &pb.Monoid{}
				_t1904.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1087}
				_t1902 = _t1904
			} else {
				var _t1905 *pb.Monoid
				if prediction1085 == 0 {
					_t1906 := p.parse_or_monoid()
					or_monoid1086 := _t1906
					_t1907 := &pb.Monoid{}
					_t1907.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1086}
					_t1905 = _t1907
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1902 = _t1905
			}
			_t1899 = _t1902
		}
		_t1896 = _t1899
	}
	result1091 := _t1896
	p.recordSpan(int(span_start1090), "Monoid")
	return result1091
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1092 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1908 := &pb.OrMonoid{}
	result1093 := _t1908
	p.recordSpan(int(span_start1092), "OrMonoid")
	return result1093
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1095 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1909 := p.parse_type()
	type1094 := _t1909
	p.consumeLiteral(")")
	_t1910 := &pb.MinMonoid{Type: type1094}
	result1096 := _t1910
	p.recordSpan(int(span_start1095), "MinMonoid")
	return result1096
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1098 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1911 := p.parse_type()
	type1097 := _t1911
	p.consumeLiteral(")")
	_t1912 := &pb.MaxMonoid{Type: type1097}
	result1099 := _t1912
	p.recordSpan(int(span_start1098), "MaxMonoid")
	return result1099
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1101 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1913 := p.parse_type()
	type1100 := _t1913
	p.consumeLiteral(")")
	_t1914 := &pb.SumMonoid{Type: type1100}
	result1102 := _t1914
	p.recordSpan(int(span_start1101), "SumMonoid")
	return result1102
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1915 := p.parse_monoid()
	monoid1103 := _t1915
	_t1916 := p.parse_relation_id()
	relation_id1104 := _t1916
	_t1917 := p.parse_abstraction_with_arity()
	abstraction_with_arity1105 := _t1917
	var _t1918 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1919 := p.parse_attrs()
		_t1918 = _t1919
	}
	attrs1106 := _t1918
	p.consumeLiteral(")")
	_t1920 := attrs1106
	if attrs1106 == nil {
		_t1920 = []*pb.Attribute{}
	}
	_t1921 := &pb.MonusDef{Monoid: monoid1103, Name: relation_id1104, Body: abstraction_with_arity1105[0].(*pb.Abstraction), Attrs: _t1920, ValueArity: abstraction_with_arity1105[1].(int64)}
	result1108 := _t1921
	p.recordSpan(int(span_start1107), "MonusDef")
	return result1108
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1113 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1922 := p.parse_relation_id()
	relation_id1109 := _t1922
	_t1923 := p.parse_abstraction()
	abstraction1110 := _t1923
	_t1924 := p.parse_functional_dependency_keys()
	functional_dependency_keys1111 := _t1924
	_t1925 := p.parse_functional_dependency_values()
	functional_dependency_values1112 := _t1925
	p.consumeLiteral(")")
	_t1926 := &pb.FunctionalDependency{Guard: abstraction1110, Keys: functional_dependency_keys1111, Values: functional_dependency_values1112}
	_t1927 := &pb.Constraint{Name: relation_id1109}
	_t1927.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1926}
	result1114 := _t1927
	p.recordSpan(int(span_start1113), "Constraint")
	return result1114
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1115 := []*pb.Var{}
	cond1116 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1116 {
		_t1928 := p.parse_var()
		item1117 := _t1928
		xs1115 = append(xs1115, item1117)
		cond1116 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1118 := xs1115
	p.consumeLiteral(")")
	return vars1118
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1119 := []*pb.Var{}
	cond1120 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1120 {
		_t1929 := p.parse_var()
		item1121 := _t1929
		xs1119 = append(xs1119, item1121)
		cond1120 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1122 := xs1119
	p.consumeLiteral(")")
	return vars1122
}

func (p *Parser) parse_data() *pb.Data {
	span_start1128 := int64(p.spanStart())
	var _t1930 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1931 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1931 = 3
		} else {
			var _t1932 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1932 = 0
			} else {
				var _t1933 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1933 = 2
				} else {
					var _t1934 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1934 = 1
					} else {
						_t1934 = -1
					}
					_t1933 = _t1934
				}
				_t1932 = _t1933
			}
			_t1931 = _t1932
		}
		_t1930 = _t1931
	} else {
		_t1930 = -1
	}
	prediction1123 := _t1930
	var _t1935 *pb.Data
	if prediction1123 == 3 {
		_t1936 := p.parse_iceberg_data()
		iceberg_data1127 := _t1936
		_t1937 := &pb.Data{}
		_t1937.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1127}
		_t1935 = _t1937
	} else {
		var _t1938 *pb.Data
		if prediction1123 == 2 {
			_t1939 := p.parse_csv_data()
			csv_data1126 := _t1939
			_t1940 := &pb.Data{}
			_t1940.DataType = &pb.Data_CsvData{CsvData: csv_data1126}
			_t1938 = _t1940
		} else {
			var _t1941 *pb.Data
			if prediction1123 == 1 {
				_t1942 := p.parse_betree_relation()
				betree_relation1125 := _t1942
				_t1943 := &pb.Data{}
				_t1943.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1125}
				_t1941 = _t1943
			} else {
				var _t1944 *pb.Data
				if prediction1123 == 0 {
					_t1945 := p.parse_edb()
					edb1124 := _t1945
					_t1946 := &pb.Data{}
					_t1946.DataType = &pb.Data_Edb{Edb: edb1124}
					_t1944 = _t1946
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1941 = _t1944
			}
			_t1938 = _t1941
		}
		_t1935 = _t1938
	}
	result1129 := _t1935
	p.recordSpan(int(span_start1128), "Data")
	return result1129
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1133 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1947 := p.parse_relation_id()
	relation_id1130 := _t1947
	_t1948 := p.parse_edb_path()
	edb_path1131 := _t1948
	_t1949 := p.parse_edb_types()
	edb_types1132 := _t1949
	p.consumeLiteral(")")
	_t1950 := &pb.EDB{TargetId: relation_id1130, Path: edb_path1131, Types: edb_types1132}
	result1134 := _t1950
	p.recordSpan(int(span_start1133), "EDB")
	return result1134
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1135 := []string{}
	cond1136 := p.matchLookaheadTerminal("STRING", 0)
	for cond1136 {
		item1137 := p.consumeTerminal("STRING").Value.str
		xs1135 = append(xs1135, item1137)
		cond1136 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1138 := xs1135
	p.consumeLiteral("]")
	return strings1138
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1139 := []*pb.Type{}
	cond1140 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1140 {
		_t1951 := p.parse_type()
		item1141 := _t1951
		xs1139 = append(xs1139, item1141)
		cond1140 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1142 := xs1139
	p.consumeLiteral("]")
	return types1142
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1145 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1952 := p.parse_relation_id()
	relation_id1143 := _t1952
	_t1953 := p.parse_betree_info()
	betree_info1144 := _t1953
	p.consumeLiteral(")")
	_t1954 := &pb.BeTreeRelation{Name: relation_id1143, RelationInfo: betree_info1144}
	result1146 := _t1954
	p.recordSpan(int(span_start1145), "BeTreeRelation")
	return result1146
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1955 := p.parse_betree_info_key_types()
	betree_info_key_types1147 := _t1955
	_t1956 := p.parse_betree_info_value_types()
	betree_info_value_types1148 := _t1956
	_t1957 := p.parse_config_dict()
	config_dict1149 := _t1957
	p.consumeLiteral(")")
	_t1958 := p.construct_betree_info(betree_info_key_types1147, betree_info_value_types1148, config_dict1149)
	result1151 := _t1958
	p.recordSpan(int(span_start1150), "BeTreeInfo")
	return result1151
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1152 := []*pb.Type{}
	cond1153 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1153 {
		_t1959 := p.parse_type()
		item1154 := _t1959
		xs1152 = append(xs1152, item1154)
		cond1153 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1155 := xs1152
	p.consumeLiteral(")")
	return types1155
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1156 := []*pb.Type{}
	cond1157 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1157 {
		_t1960 := p.parse_type()
		item1158 := _t1960
		xs1156 = append(xs1156, item1158)
		cond1157 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1159 := xs1156
	p.consumeLiteral(")")
	return types1159
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1164 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1961 := p.parse_csvlocator()
	csvlocator1160 := _t1961
	_t1962 := p.parse_csv_config()
	csv_config1161 := _t1962
	_t1963 := p.parse_gnf_columns()
	gnf_columns1162 := _t1963
	_t1964 := p.parse_csv_asof()
	csv_asof1163 := _t1964
	p.consumeLiteral(")")
	_t1965 := &pb.CSVData{Locator: csvlocator1160, Config: csv_config1161, Columns: gnf_columns1162, Asof: csv_asof1163}
	result1165 := _t1965
	p.recordSpan(int(span_start1164), "CSVData")
	return result1165
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1168 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1966 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1967 := p.parse_csv_locator_paths()
		_t1966 = _t1967
	}
	csv_locator_paths1166 := _t1966
	var _t1968 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1969 := p.parse_csv_locator_inline_data()
		_t1968 = ptr(_t1969)
	}
	csv_locator_inline_data1167 := _t1968
	p.consumeLiteral(")")
	_t1970 := csv_locator_paths1166
	if csv_locator_paths1166 == nil {
		_t1970 = []string{}
	}
	_t1971 := &pb.CSVLocator{Paths: _t1970, InlineData: []byte(deref(csv_locator_inline_data1167, ""))}
	result1169 := _t1971
	p.recordSpan(int(span_start1168), "CSVLocator")
	return result1169
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1170 := []string{}
	cond1171 := p.matchLookaheadTerminal("STRING", 0)
	for cond1171 {
		item1172 := p.consumeTerminal("STRING").Value.str
		xs1170 = append(xs1170, item1172)
		cond1171 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1173 := xs1170
	p.consumeLiteral(")")
	return strings1173
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1174 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1174
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1176 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1972 := p.parse_config_dict()
	config_dict1175 := _t1972
	p.consumeLiteral(")")
	_t1973 := p.construct_csv_config(config_dict1175)
	result1177 := _t1973
	p.recordSpan(int(span_start1176), "CSVConfig")
	return result1177
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1178 := []*pb.GNFColumn{}
	cond1179 := p.matchLookaheadLiteral("(", 0)
	for cond1179 {
		_t1974 := p.parse_gnf_column()
		item1180 := _t1974
		xs1178 = append(xs1178, item1180)
		cond1179 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1181 := xs1178
	p.consumeLiteral(")")
	return gnf_columns1181
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1188 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1975 := p.parse_gnf_column_path()
	gnf_column_path1182 := _t1975
	var _t1976 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1977 := p.parse_relation_id()
		_t1976 = _t1977
	}
	relation_id1183 := _t1976
	p.consumeLiteral("[")
	xs1184 := []*pb.Type{}
	cond1185 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1185 {
		_t1978 := p.parse_type()
		item1186 := _t1978
		xs1184 = append(xs1184, item1186)
		cond1185 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1187 := xs1184
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1979 := &pb.GNFColumn{ColumnPath: gnf_column_path1182, TargetId: relation_id1183, Types: types1187}
	result1189 := _t1979
	p.recordSpan(int(span_start1188), "GNFColumn")
	return result1189
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1980 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1980 = 1
	} else {
		var _t1981 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1981 = 0
		} else {
			_t1981 = -1
		}
		_t1980 = _t1981
	}
	prediction1190 := _t1980
	var _t1982 []string
	if prediction1190 == 1 {
		p.consumeLiteral("[")
		xs1192 := []string{}
		cond1193 := p.matchLookaheadTerminal("STRING", 0)
		for cond1193 {
			item1194 := p.consumeTerminal("STRING").Value.str
			xs1192 = append(xs1192, item1194)
			cond1193 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1195 := xs1192
		p.consumeLiteral("]")
		_t1982 = strings1195
	} else {
		var _t1983 []string
		if prediction1190 == 0 {
			string1191 := p.consumeTerminal("STRING").Value.str
			_ = string1191
			_t1983 = []string{string1191}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1982 = _t1983
	}
	return _t1982
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1196 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1196
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1203 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1984 := p.parse_iceberg_locator()
	iceberg_locator1197 := _t1984
	_t1985 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1198 := _t1985
	_t1986 := p.parse_gnf_columns()
	gnf_columns1199 := _t1986
	var _t1987 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1988 := p.parse_iceberg_from_snapshot()
		_t1987 = ptr(_t1988)
	}
	iceberg_from_snapshot1200 := _t1987
	var _t1989 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1990 := p.parse_iceberg_to_snapshot()
		_t1989 = ptr(_t1990)
	}
	iceberg_to_snapshot1201 := _t1989
	_t1991 := p.parse_boolean_value()
	boolean_value1202 := _t1991
	p.consumeLiteral(")")
	_t1992 := p.construct_iceberg_data(iceberg_locator1197, iceberg_catalog_config1198, gnf_columns1199, iceberg_from_snapshot1200, iceberg_to_snapshot1201, boolean_value1202)
	result1204 := _t1992
	p.recordSpan(int(span_start1203), "IcebergData")
	return result1204
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1208 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	_t1993 := p.parse_iceberg_locator_table_name()
	iceberg_locator_table_name1205 := _t1993
	_t1994 := p.parse_iceberg_locator_namespace()
	iceberg_locator_namespace1206 := _t1994
	_t1995 := p.parse_iceberg_locator_warehouse()
	iceberg_locator_warehouse1207 := _t1995
	p.consumeLiteral(")")
	_t1996 := &pb.IcebergLocator{TableName: iceberg_locator_table_name1205, Namespace: iceberg_locator_namespace1206, Warehouse: iceberg_locator_warehouse1207}
	result1209 := _t1996
	p.recordSpan(int(span_start1208), "IcebergLocator")
	return result1209
}

func (p *Parser) parse_iceberg_locator_table_name() string {
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1210 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1210
}

func (p *Parser) parse_iceberg_locator_namespace() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1211 := []string{}
	cond1212 := p.matchLookaheadTerminal("STRING", 0)
	for cond1212 {
		item1213 := p.consumeTerminal("STRING").Value.str
		xs1211 = append(xs1211, item1213)
		cond1212 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1214 := xs1211
	p.consumeLiteral(")")
	return strings1214
}

func (p *Parser) parse_iceberg_locator_warehouse() string {
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1215 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1215
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	_t1997 := p.parse_iceberg_catalog_uri()
	iceberg_catalog_uri1216 := _t1997
	var _t1998 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1999 := p.parse_iceberg_catalog_config_scope()
		_t1998 = ptr(_t1999)
	}
	iceberg_catalog_config_scope1217 := _t1998
	_t2000 := p.parse_iceberg_properties()
	iceberg_properties1218 := _t2000
	_t2001 := p.parse_iceberg_auth_properties()
	iceberg_auth_properties1219 := _t2001
	p.consumeLiteral(")")
	_t2002 := p.construct_iceberg_catalog_config(iceberg_catalog_uri1216, iceberg_catalog_config_scope1217, iceberg_properties1218, iceberg_auth_properties1219)
	result1221 := _t2002
	p.recordSpan(int(span_start1220), "IcebergCatalogConfig")
	return result1221
}

func (p *Parser) parse_iceberg_catalog_uri() string {
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1222 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1222
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1223 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1223
}

func (p *Parser) parse_iceberg_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1224 := [][]interface{}{}
	cond1225 := p.matchLookaheadLiteral("(", 0)
	for cond1225 {
		_t2003 := p.parse_iceberg_property_entry()
		item1226 := _t2003
		xs1224 = append(xs1224, item1226)
		cond1225 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1227 := xs1224
	p.consumeLiteral(")")
	return iceberg_property_entrys1227
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1228 := p.consumeTerminal("STRING").Value.str
	string_31229 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1228, string_31229}
}

func (p *Parser) parse_iceberg_auth_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1230 := [][]interface{}{}
	cond1231 := p.matchLookaheadLiteral("(", 0)
	for cond1231 {
		_t2004 := p.parse_iceberg_masked_property_entry()
		item1232 := _t2004
		xs1230 = append(xs1230, item1232)
		cond1231 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1233 := xs1230
	p.consumeLiteral(")")
	return iceberg_masked_property_entrys1233
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1234 := p.consumeTerminal("STRING").Value.str
	string_31235 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1234, string_31235}
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1236 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1236
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1237 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1237
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1239 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t2005 := p.parse_fragment_id()
	fragment_id1238 := _t2005
	p.consumeLiteral(")")
	_t2006 := &pb.Undefine{FragmentId: fragment_id1238}
	result1240 := _t2006
	p.recordSpan(int(span_start1239), "Undefine")
	return result1240
}

func (p *Parser) parse_context() *pb.Context {
	span_start1245 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1241 := []*pb.RelationId{}
	cond1242 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1242 {
		_t2007 := p.parse_relation_id()
		item1243 := _t2007
		xs1241 = append(xs1241, item1243)
		cond1242 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1244 := xs1241
	p.consumeLiteral(")")
	_t2008 := &pb.Context{Relations: relation_ids1244}
	result1246 := _t2008
	p.recordSpan(int(span_start1245), "Context")
	return result1246
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1252 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t2009 := p.parse_edb_path()
	edb_path1247 := _t2009
	xs1248 := []*pb.SnapshotMapping{}
	cond1249 := p.matchLookaheadLiteral("[", 0)
	for cond1249 {
		_t2010 := p.parse_snapshot_mapping()
		item1250 := _t2010
		xs1248 = append(xs1248, item1250)
		cond1249 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1251 := xs1248
	p.consumeLiteral(")")
	_t2011 := &pb.Snapshot{Prefix: edb_path1247, Mappings: snapshot_mappings1251}
	result1253 := _t2011
	p.recordSpan(int(span_start1252), "Snapshot")
	return result1253
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1256 := int64(p.spanStart())
	_t2012 := p.parse_edb_path()
	edb_path1254 := _t2012
	_t2013 := p.parse_relation_id()
	relation_id1255 := _t2013
	_t2014 := &pb.SnapshotMapping{DestinationPath: edb_path1254, SourceRelation: relation_id1255}
	result1257 := _t2014
	p.recordSpan(int(span_start1256), "SnapshotMapping")
	return result1257
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1258 := []*pb.Read{}
	cond1259 := p.matchLookaheadLiteral("(", 0)
	for cond1259 {
		_t2015 := p.parse_read()
		item1260 := _t2015
		xs1258 = append(xs1258, item1260)
		cond1259 = p.matchLookaheadLiteral("(", 0)
	}
	reads1261 := xs1258
	p.consumeLiteral(")")
	return reads1261
}

func (p *Parser) parse_read() *pb.Read {
	span_start1268 := int64(p.spanStart())
	var _t2016 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2017 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t2017 = 2
		} else {
			var _t2018 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t2018 = 1
			} else {
				var _t2019 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t2019 = 4
				} else {
					var _t2020 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t2020 = 4
					} else {
						var _t2021 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t2021 = 0
						} else {
							var _t2022 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t2022 = 3
							} else {
								_t2022 = -1
							}
							_t2021 = _t2022
						}
						_t2020 = _t2021
					}
					_t2019 = _t2020
				}
				_t2018 = _t2019
			}
			_t2017 = _t2018
		}
		_t2016 = _t2017
	} else {
		_t2016 = -1
	}
	prediction1262 := _t2016
	var _t2023 *pb.Read
	if prediction1262 == 4 {
		_t2024 := p.parse_export()
		export1267 := _t2024
		_t2025 := &pb.Read{}
		_t2025.ReadType = &pb.Read_Export{Export: export1267}
		_t2023 = _t2025
	} else {
		var _t2026 *pb.Read
		if prediction1262 == 3 {
			_t2027 := p.parse_abort()
			abort1266 := _t2027
			_t2028 := &pb.Read{}
			_t2028.ReadType = &pb.Read_Abort{Abort: abort1266}
			_t2026 = _t2028
		} else {
			var _t2029 *pb.Read
			if prediction1262 == 2 {
				_t2030 := p.parse_what_if()
				what_if1265 := _t2030
				_t2031 := &pb.Read{}
				_t2031.ReadType = &pb.Read_WhatIf{WhatIf: what_if1265}
				_t2029 = _t2031
			} else {
				var _t2032 *pb.Read
				if prediction1262 == 1 {
					_t2033 := p.parse_output()
					output1264 := _t2033
					_t2034 := &pb.Read{}
					_t2034.ReadType = &pb.Read_Output{Output: output1264}
					_t2032 = _t2034
				} else {
					var _t2035 *pb.Read
					if prediction1262 == 0 {
						_t2036 := p.parse_demand()
						demand1263 := _t2036
						_t2037 := &pb.Read{}
						_t2037.ReadType = &pb.Read_Demand{Demand: demand1263}
						_t2035 = _t2037
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2032 = _t2035
				}
				_t2029 = _t2032
			}
			_t2026 = _t2029
		}
		_t2023 = _t2026
	}
	result1269 := _t2023
	p.recordSpan(int(span_start1268), "Read")
	return result1269
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1271 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2038 := p.parse_relation_id()
	relation_id1270 := _t2038
	p.consumeLiteral(")")
	_t2039 := &pb.Demand{RelationId: relation_id1270}
	result1272 := _t2039
	p.recordSpan(int(span_start1271), "Demand")
	return result1272
}

func (p *Parser) parse_output() *pb.Output {
	span_start1275 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2040 := p.parse_name()
	name1273 := _t2040
	_t2041 := p.parse_relation_id()
	relation_id1274 := _t2041
	p.consumeLiteral(")")
	_t2042 := &pb.Output{Name: name1273, RelationId: relation_id1274}
	result1276 := _t2042
	p.recordSpan(int(span_start1275), "Output")
	return result1276
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1279 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2043 := p.parse_name()
	name1277 := _t2043
	_t2044 := p.parse_epoch()
	epoch1278 := _t2044
	p.consumeLiteral(")")
	_t2045 := &pb.WhatIf{Branch: name1277, Epoch: epoch1278}
	result1280 := _t2045
	p.recordSpan(int(span_start1279), "WhatIf")
	return result1280
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1283 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2046 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2047 := p.parse_name()
		_t2046 = ptr(_t2047)
	}
	name1281 := _t2046
	_t2048 := p.parse_relation_id()
	relation_id1282 := _t2048
	p.consumeLiteral(")")
	_t2049 := &pb.Abort{Name: deref(name1281, "abort"), RelationId: relation_id1282}
	result1284 := _t2049
	p.recordSpan(int(span_start1283), "Abort")
	return result1284
}

func (p *Parser) parse_export() *pb.Export {
	span_start1288 := int64(p.spanStart())
	var _t2050 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2051 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2051 = 1
		} else {
			var _t2052 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2052 = 0
			} else {
				_t2052 = -1
			}
			_t2051 = _t2052
		}
		_t2050 = _t2051
	} else {
		_t2050 = -1
	}
	prediction1285 := _t2050
	var _t2053 *pb.Export
	if prediction1285 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2054 := p.parse_export_iceberg_config()
		export_iceberg_config1287 := _t2054
		p.consumeLiteral(")")
		_t2055 := &pb.Export{}
		_t2055.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1287}
		_t2053 = _t2055
	} else {
		var _t2056 *pb.Export
		if prediction1285 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2057 := p.parse_export_csv_config()
			export_csv_config1286 := _t2057
			p.consumeLiteral(")")
			_t2058 := &pb.Export{}
			_t2058.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1286}
			_t2056 = _t2058
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2053 = _t2056
	}
	result1289 := _t2053
	p.recordSpan(int(span_start1288), "Export")
	return result1289
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1297 := int64(p.spanStart())
	var _t2059 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2060 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2060 = 0
		} else {
			var _t2061 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2061 = 1
			} else {
				_t2061 = -1
			}
			_t2060 = _t2061
		}
		_t2059 = _t2060
	} else {
		_t2059 = -1
	}
	prediction1290 := _t2059
	var _t2062 *pb.ExportCSVConfig
	if prediction1290 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2063 := p.parse_export_csv_path()
		export_csv_path1294 := _t2063
		_t2064 := p.parse_export_csv_columns_list()
		export_csv_columns_list1295 := _t2064
		_t2065 := p.parse_config_dict()
		config_dict1296 := _t2065
		p.consumeLiteral(")")
		_t2066 := p.construct_export_csv_config(export_csv_path1294, export_csv_columns_list1295, config_dict1296)
		_t2062 = _t2066
	} else {
		var _t2067 *pb.ExportCSVConfig
		if prediction1290 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2068 := p.parse_export_csv_path()
			export_csv_path1291 := _t2068
			_t2069 := p.parse_export_csv_source()
			export_csv_source1292 := _t2069
			_t2070 := p.parse_csv_config()
			csv_config1293 := _t2070
			p.consumeLiteral(")")
			_t2071 := p.construct_export_csv_config_with_source(export_csv_path1291, export_csv_source1292, csv_config1293)
			_t2067 = _t2071
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2062 = _t2067
	}
	result1298 := _t2062
	p.recordSpan(int(span_start1297), "ExportCSVConfig")
	return result1298
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1299 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1299
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1306 := int64(p.spanStart())
	var _t2072 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2073 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2073 = 1
		} else {
			var _t2074 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2074 = 0
			} else {
				_t2074 = -1
			}
			_t2073 = _t2074
		}
		_t2072 = _t2073
	} else {
		_t2072 = -1
	}
	prediction1300 := _t2072
	var _t2075 *pb.ExportCSVSource
	if prediction1300 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2076 := p.parse_relation_id()
		relation_id1305 := _t2076
		p.consumeLiteral(")")
		_t2077 := &pb.ExportCSVSource{}
		_t2077.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1305}
		_t2075 = _t2077
	} else {
		var _t2078 *pb.ExportCSVSource
		if prediction1300 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1301 := []*pb.ExportCSVColumn{}
			cond1302 := p.matchLookaheadLiteral("(", 0)
			for cond1302 {
				_t2079 := p.parse_export_csv_column()
				item1303 := _t2079
				xs1301 = append(xs1301, item1303)
				cond1302 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1304 := xs1301
			p.consumeLiteral(")")
			_t2080 := &pb.ExportCSVColumns{Columns: export_csv_columns1304}
			_t2081 := &pb.ExportCSVSource{}
			_t2081.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2080}
			_t2078 = _t2081
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2075 = _t2078
	}
	result1307 := _t2075
	p.recordSpan(int(span_start1306), "ExportCSVSource")
	return result1307
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1310 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1308 := p.consumeTerminal("STRING").Value.str
	_t2082 := p.parse_relation_id()
	relation_id1309 := _t2082
	p.consumeLiteral(")")
	_t2083 := &pb.ExportCSVColumn{ColumnName: string1308, ColumnData: relation_id1309}
	result1311 := _t2083
	p.recordSpan(int(span_start1310), "ExportCSVColumn")
	return result1311
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1312 := []*pb.ExportCSVColumn{}
	cond1313 := p.matchLookaheadLiteral("(", 0)
	for cond1313 {
		_t2084 := p.parse_export_csv_column()
		item1314 := _t2084
		xs1312 = append(xs1312, item1314)
		cond1313 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1315 := xs1312
	p.consumeLiteral(")")
	return export_csv_columns1315
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1321 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2085 := p.parse_iceberg_locator()
	iceberg_locator1316 := _t2085
	_t2086 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1317 := _t2086
	_t2087 := p.parse_export_iceberg_table_def()
	export_iceberg_table_def1318 := _t2087
	_t2088 := p.parse_iceberg_table_properties()
	iceberg_table_properties1319 := _t2088
	var _t2089 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2090 := p.parse_config_dict()
		_t2089 = _t2090
	}
	config_dict1320 := _t2089
	p.consumeLiteral(")")
	_t2091 := p.construct_export_iceberg_config_full(iceberg_locator1316, iceberg_catalog_config1317, export_iceberg_table_def1318, iceberg_table_properties1319, config_dict1320)
	result1322 := _t2091
	p.recordSpan(int(span_start1321), "ExportIcebergConfig")
	return result1322
}

func (p *Parser) parse_export_iceberg_table_def() *pb.RelationId {
	span_start1324 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2092 := p.parse_relation_id()
	relation_id1323 := _t2092
	p.consumeLiteral(")")
	result1325 := relation_id1323
	p.recordSpan(int(span_start1324), "RelationId")
	return result1325
}

func (p *Parser) parse_iceberg_table_properties() [][]interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1326 := [][]interface{}{}
	cond1327 := p.matchLookaheadLiteral("(", 0)
	for cond1327 {
		_t2093 := p.parse_iceberg_property_entry()
		item1328 := _t2093
		xs1326 = append(xs1326, item1328)
		cond1327 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1329 := xs1326
	p.consumeLiteral(")")
	return iceberg_property_entrys1329
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
