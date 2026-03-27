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
	var _t2070 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2070
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2071 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2071
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2072 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2072
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2073 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2073
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2074 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2074
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2075 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2075
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2076 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2076
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2077 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2077
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2078 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2078
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2079 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2079
	_t2080 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2080
	_t2081 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2081
	_t2082 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2082
	_t2083 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2083
	_t2084 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2084
	_t2085 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2085
	_t2086 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2086
	_t2087 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2087
	_t2088 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2088
	_t2089 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2089
	_t2090 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2090
	_t2091 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2091
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2092 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2092
	_t2093 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2093
	_t2094 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2094
	_t2095 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2095
	_t2096 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2096
	_t2097 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2097
	_t2098 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2098
	_t2099 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2099
	_t2100 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2100
	_t2101 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2101.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2101.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2101
	_t2102 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2102
}

func (p *Parser) default_configure() *pb.Configure {
	_t2103 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2103
	_t2104 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2104
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
	_t2105 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2105
	_t2106 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2106
	_t2107 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2107
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2108 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2108
	_t2109 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2109
	_t2110 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2110
	_t2111 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2111
	_t2112 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2112
	_t2113 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2113
	_t2114 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2114
	_t2115 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2115
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2116 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2116
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2117 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2117
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, columns *pb.ExportIcebergColumns, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2118 := config_dict
	if config_dict == nil {
		_t2118 = [][]interface{}{}
	}
	cfg := dictFromList(_t2118)
	_t2119 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2119
	_t2120 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2120
	_t2121 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2121
	table_props := stringMapFromPairs(table_property_pairs)
	_t2122 := &pb.ExportIcebergConfig{Locator: locator, Config: config, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2122
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start665 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1318 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1319 := p.parse_configure()
		_t1318 = _t1319
	}
	configure659 := _t1318
	var _t1320 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1321 := p.parse_sync()
		_t1320 = _t1321
	}
	sync660 := _t1320
	xs661 := []*pb.Epoch{}
	cond662 := p.matchLookaheadLiteral("(", 0)
	for cond662 {
		_t1322 := p.parse_epoch()
		item663 := _t1322
		xs661 = append(xs661, item663)
		cond662 = p.matchLookaheadLiteral("(", 0)
	}
	epochs664 := xs661
	p.consumeLiteral(")")
	_t1323 := p.default_configure()
	_t1324 := configure659
	if configure659 == nil {
		_t1324 = _t1323
	}
	_t1325 := &pb.Transaction{Epochs: epochs664, Configure: _t1324, Sync: sync660}
	result666 := _t1325
	p.recordSpan(int(span_start665), "Transaction")
	return result666
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start668 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1326 := p.parse_config_dict()
	config_dict667 := _t1326
	p.consumeLiteral(")")
	_t1327 := p.construct_configure(config_dict667)
	result669 := _t1327
	p.recordSpan(int(span_start668), "Configure")
	return result669
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs670 := [][]interface{}{}
	cond671 := p.matchLookaheadLiteral(":", 0)
	for cond671 {
		_t1328 := p.parse_config_key_value()
		item672 := _t1328
		xs670 = append(xs670, item672)
		cond671 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values673 := xs670
	p.consumeLiteral("}")
	return config_key_values673
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol674 := p.consumeTerminal("SYMBOL").Value.str
	_t1329 := p.parse_raw_value()
	raw_value675 := _t1329
	return []interface{}{symbol674, raw_value675}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start689 := int64(p.spanStart())
	var _t1330 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1330 = 12
	} else {
		var _t1331 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1331 = 11
		} else {
			var _t1332 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1332 = 12
			} else {
				var _t1333 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1334 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1334 = 1
					} else {
						var _t1335 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1335 = 0
						} else {
							_t1335 = -1
						}
						_t1334 = _t1335
					}
					_t1333 = _t1334
				} else {
					var _t1336 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1336 = 7
					} else {
						var _t1337 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1337 = 8
						} else {
							var _t1338 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1338 = 2
							} else {
								var _t1339 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1339 = 3
								} else {
									var _t1340 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1340 = 9
									} else {
										var _t1341 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1341 = 4
										} else {
											var _t1342 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1342 = 5
											} else {
												var _t1343 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1343 = 6
												} else {
													var _t1344 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1344 = 10
													} else {
														_t1344 = -1
													}
													_t1343 = _t1344
												}
												_t1342 = _t1343
											}
											_t1341 = _t1342
										}
										_t1340 = _t1341
									}
									_t1339 = _t1340
								}
								_t1338 = _t1339
							}
							_t1337 = _t1338
						}
						_t1336 = _t1337
					}
					_t1333 = _t1336
				}
				_t1332 = _t1333
			}
			_t1331 = _t1332
		}
		_t1330 = _t1331
	}
	prediction676 := _t1330
	var _t1345 *pb.Value
	if prediction676 == 12 {
		_t1346 := p.parse_boolean_value()
		boolean_value688 := _t1346
		_t1347 := &pb.Value{}
		_t1347.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value688}
		_t1345 = _t1347
	} else {
		var _t1348 *pb.Value
		if prediction676 == 11 {
			p.consumeLiteral("missing")
			_t1349 := &pb.MissingValue{}
			_t1350 := &pb.Value{}
			_t1350.Value = &pb.Value_MissingValue{MissingValue: _t1349}
			_t1348 = _t1350
		} else {
			var _t1351 *pb.Value
			if prediction676 == 10 {
				decimal687 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1352 := &pb.Value{}
				_t1352.Value = &pb.Value_DecimalValue{DecimalValue: decimal687}
				_t1351 = _t1352
			} else {
				var _t1353 *pb.Value
				if prediction676 == 9 {
					int128686 := p.consumeTerminal("INT128").Value.int128
					_t1354 := &pb.Value{}
					_t1354.Value = &pb.Value_Int128Value{Int128Value: int128686}
					_t1353 = _t1354
				} else {
					var _t1355 *pb.Value
					if prediction676 == 8 {
						uint128685 := p.consumeTerminal("UINT128").Value.uint128
						_t1356 := &pb.Value{}
						_t1356.Value = &pb.Value_Uint128Value{Uint128Value: uint128685}
						_t1355 = _t1356
					} else {
						var _t1357 *pb.Value
						if prediction676 == 7 {
							uint32684 := p.consumeTerminal("UINT32").Value.u32
							_t1358 := &pb.Value{}
							_t1358.Value = &pb.Value_Uint32Value{Uint32Value: uint32684}
							_t1357 = _t1358
						} else {
							var _t1359 *pb.Value
							if prediction676 == 6 {
								float683 := p.consumeTerminal("FLOAT").Value.f64
								_t1360 := &pb.Value{}
								_t1360.Value = &pb.Value_FloatValue{FloatValue: float683}
								_t1359 = _t1360
							} else {
								var _t1361 *pb.Value
								if prediction676 == 5 {
									float32682 := p.consumeTerminal("FLOAT32").Value.f32
									_t1362 := &pb.Value{}
									_t1362.Value = &pb.Value_Float32Value{Float32Value: float32682}
									_t1361 = _t1362
								} else {
									var _t1363 *pb.Value
									if prediction676 == 4 {
										int681 := p.consumeTerminal("INT").Value.i64
										_t1364 := &pb.Value{}
										_t1364.Value = &pb.Value_IntValue{IntValue: int681}
										_t1363 = _t1364
									} else {
										var _t1365 *pb.Value
										if prediction676 == 3 {
											int32680 := p.consumeTerminal("INT32").Value.i32
											_t1366 := &pb.Value{}
											_t1366.Value = &pb.Value_Int32Value{Int32Value: int32680}
											_t1365 = _t1366
										} else {
											var _t1367 *pb.Value
											if prediction676 == 2 {
												string679 := p.consumeTerminal("STRING").Value.str
												_t1368 := &pb.Value{}
												_t1368.Value = &pb.Value_StringValue{StringValue: string679}
												_t1367 = _t1368
											} else {
												var _t1369 *pb.Value
												if prediction676 == 1 {
													_t1370 := p.parse_raw_datetime()
													raw_datetime678 := _t1370
													_t1371 := &pb.Value{}
													_t1371.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime678}
													_t1369 = _t1371
												} else {
													var _t1372 *pb.Value
													if prediction676 == 0 {
														_t1373 := p.parse_raw_date()
														raw_date677 := _t1373
														_t1374 := &pb.Value{}
														_t1374.Value = &pb.Value_DateValue{DateValue: raw_date677}
														_t1372 = _t1374
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1369 = _t1372
												}
												_t1367 = _t1369
											}
											_t1365 = _t1367
										}
										_t1363 = _t1365
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
			_t1348 = _t1351
		}
		_t1345 = _t1348
	}
	result690 := _t1345
	p.recordSpan(int(span_start689), "Value")
	return result690
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start694 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int691 := p.consumeTerminal("INT").Value.i64
	int_3692 := p.consumeTerminal("INT").Value.i64
	int_4693 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1375 := &pb.DateValue{Year: int32(int691), Month: int32(int_3692), Day: int32(int_4693)}
	result695 := _t1375
	p.recordSpan(int(span_start694), "DateValue")
	return result695
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start703 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int696 := p.consumeTerminal("INT").Value.i64
	int_3697 := p.consumeTerminal("INT").Value.i64
	int_4698 := p.consumeTerminal("INT").Value.i64
	int_5699 := p.consumeTerminal("INT").Value.i64
	int_6700 := p.consumeTerminal("INT").Value.i64
	int_7701 := p.consumeTerminal("INT").Value.i64
	var _t1376 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1376 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8702 := _t1376
	p.consumeLiteral(")")
	_t1377 := &pb.DateTimeValue{Year: int32(int696), Month: int32(int_3697), Day: int32(int_4698), Hour: int32(int_5699), Minute: int32(int_6700), Second: int32(int_7701), Microsecond: int32(deref(int_8702, 0))}
	result704 := _t1377
	p.recordSpan(int(span_start703), "DateTimeValue")
	return result704
}

func (p *Parser) parse_boolean_value() bool {
	var _t1378 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1378 = 0
	} else {
		var _t1379 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1379 = 1
		} else {
			_t1379 = -1
		}
		_t1378 = _t1379
	}
	prediction705 := _t1378
	var _t1380 bool
	if prediction705 == 1 {
		p.consumeLiteral("false")
		_t1380 = false
	} else {
		var _t1381 bool
		if prediction705 == 0 {
			p.consumeLiteral("true")
			_t1381 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1380 = _t1381
	}
	return _t1380
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start710 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs706 := []*pb.FragmentId{}
	cond707 := p.matchLookaheadLiteral(":", 0)
	for cond707 {
		_t1382 := p.parse_fragment_id()
		item708 := _t1382
		xs706 = append(xs706, item708)
		cond707 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids709 := xs706
	p.consumeLiteral(")")
	_t1383 := &pb.Sync{Fragments: fragment_ids709}
	result711 := _t1383
	p.recordSpan(int(span_start710), "Sync")
	return result711
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol712 := p.consumeTerminal("SYMBOL").Value.str
	result714 := &pb.FragmentId{Id: []byte(symbol712)}
	p.recordSpan(int(span_start713), "FragmentId")
	return result714
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1384 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1385 := p.parse_epoch_writes()
		_t1384 = _t1385
	}
	epoch_writes715 := _t1384
	var _t1386 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1387 := p.parse_epoch_reads()
		_t1386 = _t1387
	}
	epoch_reads716 := _t1386
	p.consumeLiteral(")")
	_t1388 := epoch_writes715
	if epoch_writes715 == nil {
		_t1388 = []*pb.Write{}
	}
	_t1389 := epoch_reads716
	if epoch_reads716 == nil {
		_t1389 = []*pb.Read{}
	}
	_t1390 := &pb.Epoch{Writes: _t1388, Reads: _t1389}
	result718 := _t1390
	p.recordSpan(int(span_start717), "Epoch")
	return result718
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs719 := []*pb.Write{}
	cond720 := p.matchLookaheadLiteral("(", 0)
	for cond720 {
		_t1391 := p.parse_write()
		item721 := _t1391
		xs719 = append(xs719, item721)
		cond720 = p.matchLookaheadLiteral("(", 0)
	}
	writes722 := xs719
	p.consumeLiteral(")")
	return writes722
}

func (p *Parser) parse_write() *pb.Write {
	span_start728 := int64(p.spanStart())
	var _t1392 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1393 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1393 = 1
		} else {
			var _t1394 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1394 = 3
			} else {
				var _t1395 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1395 = 0
				} else {
					var _t1396 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1396 = 2
					} else {
						_t1396 = -1
					}
					_t1395 = _t1396
				}
				_t1394 = _t1395
			}
			_t1393 = _t1394
		}
		_t1392 = _t1393
	} else {
		_t1392 = -1
	}
	prediction723 := _t1392
	var _t1397 *pb.Write
	if prediction723 == 3 {
		_t1398 := p.parse_snapshot()
		snapshot727 := _t1398
		_t1399 := &pb.Write{}
		_t1399.WriteType = &pb.Write_Snapshot{Snapshot: snapshot727}
		_t1397 = _t1399
	} else {
		var _t1400 *pb.Write
		if prediction723 == 2 {
			_t1401 := p.parse_context()
			context726 := _t1401
			_t1402 := &pb.Write{}
			_t1402.WriteType = &pb.Write_Context{Context: context726}
			_t1400 = _t1402
		} else {
			var _t1403 *pb.Write
			if prediction723 == 1 {
				_t1404 := p.parse_undefine()
				undefine725 := _t1404
				_t1405 := &pb.Write{}
				_t1405.WriteType = &pb.Write_Undefine{Undefine: undefine725}
				_t1403 = _t1405
			} else {
				var _t1406 *pb.Write
				if prediction723 == 0 {
					_t1407 := p.parse_define()
					define724 := _t1407
					_t1408 := &pb.Write{}
					_t1408.WriteType = &pb.Write_Define{Define: define724}
					_t1406 = _t1408
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1403 = _t1406
			}
			_t1400 = _t1403
		}
		_t1397 = _t1400
	}
	result729 := _t1397
	p.recordSpan(int(span_start728), "Write")
	return result729
}

func (p *Parser) parse_define() *pb.Define {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1409 := p.parse_fragment()
	fragment730 := _t1409
	p.consumeLiteral(")")
	_t1410 := &pb.Define{Fragment: fragment730}
	result732 := _t1410
	p.recordSpan(int(span_start731), "Define")
	return result732
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start738 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1411 := p.parse_new_fragment_id()
	new_fragment_id733 := _t1411
	xs734 := []*pb.Declaration{}
	cond735 := p.matchLookaheadLiteral("(", 0)
	for cond735 {
		_t1412 := p.parse_declaration()
		item736 := _t1412
		xs734 = append(xs734, item736)
		cond735 = p.matchLookaheadLiteral("(", 0)
	}
	declarations737 := xs734
	p.consumeLiteral(")")
	result739 := p.constructFragment(new_fragment_id733, declarations737)
	p.recordSpan(int(span_start738), "Fragment")
	return result739
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start741 := int64(p.spanStart())
	_t1413 := p.parse_fragment_id()
	fragment_id740 := _t1413
	p.startFragment(fragment_id740)
	result742 := fragment_id740
	p.recordSpan(int(span_start741), "FragmentId")
	return result742
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start748 := int64(p.spanStart())
	var _t1414 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1415 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1415 = 3
		} else {
			var _t1416 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1416 = 2
			} else {
				var _t1417 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1417 = 3
				} else {
					var _t1418 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1418 = 0
					} else {
						var _t1419 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1419 = 3
						} else {
							var _t1420 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1420 = 3
							} else {
								var _t1421 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1421 = 1
								} else {
									_t1421 = -1
								}
								_t1420 = _t1421
							}
							_t1419 = _t1420
						}
						_t1418 = _t1419
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
	prediction743 := _t1414
	var _t1422 *pb.Declaration
	if prediction743 == 3 {
		_t1423 := p.parse_data()
		data747 := _t1423
		_t1424 := &pb.Declaration{}
		_t1424.DeclarationType = &pb.Declaration_Data{Data: data747}
		_t1422 = _t1424
	} else {
		var _t1425 *pb.Declaration
		if prediction743 == 2 {
			_t1426 := p.parse_constraint()
			constraint746 := _t1426
			_t1427 := &pb.Declaration{}
			_t1427.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint746}
			_t1425 = _t1427
		} else {
			var _t1428 *pb.Declaration
			if prediction743 == 1 {
				_t1429 := p.parse_algorithm()
				algorithm745 := _t1429
				_t1430 := &pb.Declaration{}
				_t1430.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm745}
				_t1428 = _t1430
			} else {
				var _t1431 *pb.Declaration
				if prediction743 == 0 {
					_t1432 := p.parse_def()
					def744 := _t1432
					_t1433 := &pb.Declaration{}
					_t1433.DeclarationType = &pb.Declaration_Def{Def: def744}
					_t1431 = _t1433
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1428 = _t1431
			}
			_t1425 = _t1428
		}
		_t1422 = _t1425
	}
	result749 := _t1422
	p.recordSpan(int(span_start748), "Declaration")
	return result749
}

func (p *Parser) parse_def() *pb.Def {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1434 := p.parse_relation_id()
	relation_id750 := _t1434
	_t1435 := p.parse_abstraction()
	abstraction751 := _t1435
	var _t1436 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1437 := p.parse_attrs()
		_t1436 = _t1437
	}
	attrs752 := _t1436
	p.consumeLiteral(")")
	_t1438 := attrs752
	if attrs752 == nil {
		_t1438 = []*pb.Attribute{}
	}
	_t1439 := &pb.Def{Name: relation_id750, Body: abstraction751, Attrs: _t1438}
	result754 := _t1439
	p.recordSpan(int(span_start753), "Def")
	return result754
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start758 := int64(p.spanStart())
	var _t1440 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1440 = 0
	} else {
		var _t1441 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1441 = 1
		} else {
			_t1441 = -1
		}
		_t1440 = _t1441
	}
	prediction755 := _t1440
	var _t1442 *pb.RelationId
	if prediction755 == 1 {
		uint128757 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128757
		_t1442 = &pb.RelationId{IdLow: uint128757.Low, IdHigh: uint128757.High}
	} else {
		var _t1443 *pb.RelationId
		if prediction755 == 0 {
			p.consumeLiteral(":")
			symbol756 := p.consumeTerminal("SYMBOL").Value.str
			_t1443 = p.relationIdFromString(symbol756)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1442 = _t1443
	}
	result759 := _t1442
	p.recordSpan(int(span_start758), "RelationId")
	return result759
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start762 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1444 := p.parse_bindings()
	bindings760 := _t1444
	_t1445 := p.parse_formula()
	formula761 := _t1445
	p.consumeLiteral(")")
	_t1446 := &pb.Abstraction{Vars: listConcat(bindings760[0].([]*pb.Binding), bindings760[1].([]*pb.Binding)), Value: formula761}
	result763 := _t1446
	p.recordSpan(int(span_start762), "Abstraction")
	return result763
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs764 := []*pb.Binding{}
	cond765 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond765 {
		_t1447 := p.parse_binding()
		item766 := _t1447
		xs764 = append(xs764, item766)
		cond765 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings767 := xs764
	var _t1448 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1449 := p.parse_value_bindings()
		_t1448 = _t1449
	}
	value_bindings768 := _t1448
	p.consumeLiteral("]")
	_t1450 := value_bindings768
	if value_bindings768 == nil {
		_t1450 = []*pb.Binding{}
	}
	return []interface{}{bindings767, _t1450}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start771 := int64(p.spanStart())
	symbol769 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1451 := p.parse_type()
	type770 := _t1451
	_t1452 := &pb.Var{Name: symbol769}
	_t1453 := &pb.Binding{Var: _t1452, Type: type770}
	result772 := _t1453
	p.recordSpan(int(span_start771), "Binding")
	return result772
}

func (p *Parser) parse_type() *pb.Type {
	span_start788 := int64(p.spanStart())
	var _t1454 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1454 = 0
	} else {
		var _t1455 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1455 = 13
		} else {
			var _t1456 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1456 = 4
			} else {
				var _t1457 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1457 = 1
				} else {
					var _t1458 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1458 = 8
					} else {
						var _t1459 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1459 = 11
						} else {
							var _t1460 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1460 = 5
							} else {
								var _t1461 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1461 = 2
								} else {
									var _t1462 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1462 = 12
									} else {
										var _t1463 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1463 = 3
										} else {
											var _t1464 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1464 = 7
											} else {
												var _t1465 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1465 = 6
												} else {
													var _t1466 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1466 = 10
													} else {
														var _t1467 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1467 = 9
														} else {
															_t1467 = -1
														}
														_t1466 = _t1467
													}
													_t1465 = _t1466
												}
												_t1464 = _t1465
											}
											_t1463 = _t1464
										}
										_t1462 = _t1463
									}
									_t1461 = _t1462
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
	prediction773 := _t1454
	var _t1468 *pb.Type
	if prediction773 == 13 {
		_t1469 := p.parse_uint32_type()
		uint32_type787 := _t1469
		_t1470 := &pb.Type{}
		_t1470.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type787}
		_t1468 = _t1470
	} else {
		var _t1471 *pb.Type
		if prediction773 == 12 {
			_t1472 := p.parse_float32_type()
			float32_type786 := _t1472
			_t1473 := &pb.Type{}
			_t1473.Type = &pb.Type_Float32Type{Float32Type: float32_type786}
			_t1471 = _t1473
		} else {
			var _t1474 *pb.Type
			if prediction773 == 11 {
				_t1475 := p.parse_int32_type()
				int32_type785 := _t1475
				_t1476 := &pb.Type{}
				_t1476.Type = &pb.Type_Int32Type{Int32Type: int32_type785}
				_t1474 = _t1476
			} else {
				var _t1477 *pb.Type
				if prediction773 == 10 {
					_t1478 := p.parse_boolean_type()
					boolean_type784 := _t1478
					_t1479 := &pb.Type{}
					_t1479.Type = &pb.Type_BooleanType{BooleanType: boolean_type784}
					_t1477 = _t1479
				} else {
					var _t1480 *pb.Type
					if prediction773 == 9 {
						_t1481 := p.parse_decimal_type()
						decimal_type783 := _t1481
						_t1482 := &pb.Type{}
						_t1482.Type = &pb.Type_DecimalType{DecimalType: decimal_type783}
						_t1480 = _t1482
					} else {
						var _t1483 *pb.Type
						if prediction773 == 8 {
							_t1484 := p.parse_missing_type()
							missing_type782 := _t1484
							_t1485 := &pb.Type{}
							_t1485.Type = &pb.Type_MissingType{MissingType: missing_type782}
							_t1483 = _t1485
						} else {
							var _t1486 *pb.Type
							if prediction773 == 7 {
								_t1487 := p.parse_datetime_type()
								datetime_type781 := _t1487
								_t1488 := &pb.Type{}
								_t1488.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type781}
								_t1486 = _t1488
							} else {
								var _t1489 *pb.Type
								if prediction773 == 6 {
									_t1490 := p.parse_date_type()
									date_type780 := _t1490
									_t1491 := &pb.Type{}
									_t1491.Type = &pb.Type_DateType{DateType: date_type780}
									_t1489 = _t1491
								} else {
									var _t1492 *pb.Type
									if prediction773 == 5 {
										_t1493 := p.parse_int128_type()
										int128_type779 := _t1493
										_t1494 := &pb.Type{}
										_t1494.Type = &pb.Type_Int128Type{Int128Type: int128_type779}
										_t1492 = _t1494
									} else {
										var _t1495 *pb.Type
										if prediction773 == 4 {
											_t1496 := p.parse_uint128_type()
											uint128_type778 := _t1496
											_t1497 := &pb.Type{}
											_t1497.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type778}
											_t1495 = _t1497
										} else {
											var _t1498 *pb.Type
											if prediction773 == 3 {
												_t1499 := p.parse_float_type()
												float_type777 := _t1499
												_t1500 := &pb.Type{}
												_t1500.Type = &pb.Type_FloatType{FloatType: float_type777}
												_t1498 = _t1500
											} else {
												var _t1501 *pb.Type
												if prediction773 == 2 {
													_t1502 := p.parse_int_type()
													int_type776 := _t1502
													_t1503 := &pb.Type{}
													_t1503.Type = &pb.Type_IntType{IntType: int_type776}
													_t1501 = _t1503
												} else {
													var _t1504 *pb.Type
													if prediction773 == 1 {
														_t1505 := p.parse_string_type()
														string_type775 := _t1505
														_t1506 := &pb.Type{}
														_t1506.Type = &pb.Type_StringType{StringType: string_type775}
														_t1504 = _t1506
													} else {
														var _t1507 *pb.Type
														if prediction773 == 0 {
															_t1508 := p.parse_unspecified_type()
															unspecified_type774 := _t1508
															_t1509 := &pb.Type{}
															_t1509.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type774}
															_t1507 = _t1509
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1477 = _t1480
				}
				_t1474 = _t1477
			}
			_t1471 = _t1474
		}
		_t1468 = _t1471
	}
	result789 := _t1468
	p.recordSpan(int(span_start788), "Type")
	return result789
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start790 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1510 := &pb.UnspecifiedType{}
	result791 := _t1510
	p.recordSpan(int(span_start790), "UnspecifiedType")
	return result791
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start792 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1511 := &pb.StringType{}
	result793 := _t1511
	p.recordSpan(int(span_start792), "StringType")
	return result793
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start794 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1512 := &pb.IntType{}
	result795 := _t1512
	p.recordSpan(int(span_start794), "IntType")
	return result795
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start796 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1513 := &pb.FloatType{}
	result797 := _t1513
	p.recordSpan(int(span_start796), "FloatType")
	return result797
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1514 := &pb.UInt128Type{}
	result799 := _t1514
	p.recordSpan(int(span_start798), "UInt128Type")
	return result799
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1515 := &pb.Int128Type{}
	result801 := _t1515
	p.recordSpan(int(span_start800), "Int128Type")
	return result801
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1516 := &pb.DateType{}
	result803 := _t1516
	p.recordSpan(int(span_start802), "DateType")
	return result803
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1517 := &pb.DateTimeType{}
	result805 := _t1517
	p.recordSpan(int(span_start804), "DateTimeType")
	return result805
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start806 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1518 := &pb.MissingType{}
	result807 := _t1518
	p.recordSpan(int(span_start806), "MissingType")
	return result807
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start810 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int808 := p.consumeTerminal("INT").Value.i64
	int_3809 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1519 := &pb.DecimalType{Precision: int32(int808), Scale: int32(int_3809)}
	result811 := _t1519
	p.recordSpan(int(span_start810), "DecimalType")
	return result811
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1520 := &pb.BooleanType{}
	result813 := _t1520
	p.recordSpan(int(span_start812), "BooleanType")
	return result813
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start814 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1521 := &pb.Int32Type{}
	result815 := _t1521
	p.recordSpan(int(span_start814), "Int32Type")
	return result815
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1522 := &pb.Float32Type{}
	result817 := _t1522
	p.recordSpan(int(span_start816), "Float32Type")
	return result817
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1523 := &pb.UInt32Type{}
	result819 := _t1523
	p.recordSpan(int(span_start818), "UInt32Type")
	return result819
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs820 := []*pb.Binding{}
	cond821 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond821 {
		_t1524 := p.parse_binding()
		item822 := _t1524
		xs820 = append(xs820, item822)
		cond821 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings823 := xs820
	return bindings823
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start838 := int64(p.spanStart())
	var _t1525 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1526 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1526 = 0
		} else {
			var _t1527 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1527 = 11
			} else {
				var _t1528 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1528 = 3
				} else {
					var _t1529 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1529 = 10
					} else {
						var _t1530 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1530 = 9
						} else {
							var _t1531 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1531 = 5
							} else {
								var _t1532 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1532 = 6
								} else {
									var _t1533 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1533 = 7
									} else {
										var _t1534 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1534 = 1
										} else {
											var _t1535 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1535 = 2
											} else {
												var _t1536 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1536 = 12
												} else {
													var _t1537 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1537 = 8
													} else {
														var _t1538 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1538 = 4
														} else {
															var _t1539 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1539 = 10
															} else {
																var _t1540 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1540 = 10
																} else {
																	var _t1541 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1541 = 10
																	} else {
																		var _t1542 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1542 = 10
																		} else {
																			var _t1543 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1543 = 10
																			} else {
																				var _t1544 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1544 = 10
																				} else {
																					var _t1545 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1545 = 10
																					} else {
																						var _t1546 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1546 = 10
																						} else {
																							var _t1547 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1547 = 10
																							} else {
																								_t1547 = -1
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
	} else {
		_t1525 = -1
	}
	prediction824 := _t1525
	var _t1548 *pb.Formula
	if prediction824 == 12 {
		_t1549 := p.parse_cast()
		cast837 := _t1549
		_t1550 := &pb.Formula{}
		_t1550.FormulaType = &pb.Formula_Cast{Cast: cast837}
		_t1548 = _t1550
	} else {
		var _t1551 *pb.Formula
		if prediction824 == 11 {
			_t1552 := p.parse_rel_atom()
			rel_atom836 := _t1552
			_t1553 := &pb.Formula{}
			_t1553.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom836}
			_t1551 = _t1553
		} else {
			var _t1554 *pb.Formula
			if prediction824 == 10 {
				_t1555 := p.parse_primitive()
				primitive835 := _t1555
				_t1556 := &pb.Formula{}
				_t1556.FormulaType = &pb.Formula_Primitive{Primitive: primitive835}
				_t1554 = _t1556
			} else {
				var _t1557 *pb.Formula
				if prediction824 == 9 {
					_t1558 := p.parse_pragma()
					pragma834 := _t1558
					_t1559 := &pb.Formula{}
					_t1559.FormulaType = &pb.Formula_Pragma{Pragma: pragma834}
					_t1557 = _t1559
				} else {
					var _t1560 *pb.Formula
					if prediction824 == 8 {
						_t1561 := p.parse_atom()
						atom833 := _t1561
						_t1562 := &pb.Formula{}
						_t1562.FormulaType = &pb.Formula_Atom{Atom: atom833}
						_t1560 = _t1562
					} else {
						var _t1563 *pb.Formula
						if prediction824 == 7 {
							_t1564 := p.parse_ffi()
							ffi832 := _t1564
							_t1565 := &pb.Formula{}
							_t1565.FormulaType = &pb.Formula_Ffi{Ffi: ffi832}
							_t1563 = _t1565
						} else {
							var _t1566 *pb.Formula
							if prediction824 == 6 {
								_t1567 := p.parse_not()
								not831 := _t1567
								_t1568 := &pb.Formula{}
								_t1568.FormulaType = &pb.Formula_Not{Not: not831}
								_t1566 = _t1568
							} else {
								var _t1569 *pb.Formula
								if prediction824 == 5 {
									_t1570 := p.parse_disjunction()
									disjunction830 := _t1570
									_t1571 := &pb.Formula{}
									_t1571.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction830}
									_t1569 = _t1571
								} else {
									var _t1572 *pb.Formula
									if prediction824 == 4 {
										_t1573 := p.parse_conjunction()
										conjunction829 := _t1573
										_t1574 := &pb.Formula{}
										_t1574.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction829}
										_t1572 = _t1574
									} else {
										var _t1575 *pb.Formula
										if prediction824 == 3 {
											_t1576 := p.parse_reduce()
											reduce828 := _t1576
											_t1577 := &pb.Formula{}
											_t1577.FormulaType = &pb.Formula_Reduce{Reduce: reduce828}
											_t1575 = _t1577
										} else {
											var _t1578 *pb.Formula
											if prediction824 == 2 {
												_t1579 := p.parse_exists()
												exists827 := _t1579
												_t1580 := &pb.Formula{}
												_t1580.FormulaType = &pb.Formula_Exists{Exists: exists827}
												_t1578 = _t1580
											} else {
												var _t1581 *pb.Formula
												if prediction824 == 1 {
													_t1582 := p.parse_false()
													false826 := _t1582
													_t1583 := &pb.Formula{}
													_t1583.FormulaType = &pb.Formula_Disjunction{Disjunction: false826}
													_t1581 = _t1583
												} else {
													var _t1584 *pb.Formula
													if prediction824 == 0 {
														_t1585 := p.parse_true()
														true825 := _t1585
														_t1586 := &pb.Formula{}
														_t1586.FormulaType = &pb.Formula_Conjunction{Conjunction: true825}
														_t1584 = _t1586
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1557 = _t1560
				}
				_t1554 = _t1557
			}
			_t1551 = _t1554
		}
		_t1548 = _t1551
	}
	result839 := _t1548
	p.recordSpan(int(span_start838), "Formula")
	return result839
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start840 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1587 := &pb.Conjunction{Args: []*pb.Formula{}}
	result841 := _t1587
	p.recordSpan(int(span_start840), "Conjunction")
	return result841
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1588 := &pb.Disjunction{Args: []*pb.Formula{}}
	result843 := _t1588
	p.recordSpan(int(span_start842), "Disjunction")
	return result843
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start846 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1589 := p.parse_bindings()
	bindings844 := _t1589
	_t1590 := p.parse_formula()
	formula845 := _t1590
	p.consumeLiteral(")")
	_t1591 := &pb.Abstraction{Vars: listConcat(bindings844[0].([]*pb.Binding), bindings844[1].([]*pb.Binding)), Value: formula845}
	_t1592 := &pb.Exists{Body: _t1591}
	result847 := _t1592
	p.recordSpan(int(span_start846), "Exists")
	return result847
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start851 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1593 := p.parse_abstraction()
	abstraction848 := _t1593
	_t1594 := p.parse_abstraction()
	abstraction_3849 := _t1594
	_t1595 := p.parse_terms()
	terms850 := _t1595
	p.consumeLiteral(")")
	_t1596 := &pb.Reduce{Op: abstraction848, Body: abstraction_3849, Terms: terms850}
	result852 := _t1596
	p.recordSpan(int(span_start851), "Reduce")
	return result852
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs853 := []*pb.Term{}
	cond854 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond854 {
		_t1597 := p.parse_term()
		item855 := _t1597
		xs853 = append(xs853, item855)
		cond854 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms856 := xs853
	p.consumeLiteral(")")
	return terms856
}

func (p *Parser) parse_term() *pb.Term {
	span_start860 := int64(p.spanStart())
	var _t1598 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1598 = 1
	} else {
		var _t1599 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1599 = 1
		} else {
			var _t1600 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1600 = 1
			} else {
				var _t1601 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1601 = 1
				} else {
					var _t1602 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1602 = 0
					} else {
						var _t1603 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1603 = 1
						} else {
							var _t1604 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1604 = 1
							} else {
								var _t1605 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1605 = 1
								} else {
									var _t1606 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1606 = 1
									} else {
										var _t1607 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1607 = 1
										} else {
											var _t1608 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1608 = 1
											} else {
												var _t1609 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1609 = 1
												} else {
													var _t1610 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1610 = 1
													} else {
														var _t1611 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1611 = 1
														} else {
															_t1611 = -1
														}
														_t1610 = _t1611
													}
													_t1609 = _t1610
												}
												_t1608 = _t1609
											}
											_t1607 = _t1608
										}
										_t1606 = _t1607
									}
									_t1605 = _t1606
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
	prediction857 := _t1598
	var _t1612 *pb.Term
	if prediction857 == 1 {
		_t1613 := p.parse_value()
		value859 := _t1613
		_t1614 := &pb.Term{}
		_t1614.TermType = &pb.Term_Constant{Constant: value859}
		_t1612 = _t1614
	} else {
		var _t1615 *pb.Term
		if prediction857 == 0 {
			_t1616 := p.parse_var()
			var858 := _t1616
			_t1617 := &pb.Term{}
			_t1617.TermType = &pb.Term_Var{Var: var858}
			_t1615 = _t1617
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1612 = _t1615
	}
	result861 := _t1612
	p.recordSpan(int(span_start860), "Term")
	return result861
}

func (p *Parser) parse_var() *pb.Var {
	span_start863 := int64(p.spanStart())
	symbol862 := p.consumeTerminal("SYMBOL").Value.str
	_t1618 := &pb.Var{Name: symbol862}
	result864 := _t1618
	p.recordSpan(int(span_start863), "Var")
	return result864
}

func (p *Parser) parse_value() *pb.Value {
	span_start878 := int64(p.spanStart())
	var _t1619 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1619 = 12
	} else {
		var _t1620 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1620 = 11
		} else {
			var _t1621 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1621 = 12
			} else {
				var _t1622 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1623 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1623 = 1
					} else {
						var _t1624 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1624 = 0
						} else {
							_t1624 = -1
						}
						_t1623 = _t1624
					}
					_t1622 = _t1623
				} else {
					var _t1625 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1625 = 7
					} else {
						var _t1626 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1626 = 8
						} else {
							var _t1627 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1627 = 2
							} else {
								var _t1628 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1628 = 3
								} else {
									var _t1629 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1629 = 9
									} else {
										var _t1630 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1630 = 4
										} else {
											var _t1631 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1631 = 5
											} else {
												var _t1632 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1632 = 6
												} else {
													var _t1633 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1633 = 10
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
					_t1622 = _t1625
				}
				_t1621 = _t1622
			}
			_t1620 = _t1621
		}
		_t1619 = _t1620
	}
	prediction865 := _t1619
	var _t1634 *pb.Value
	if prediction865 == 12 {
		_t1635 := p.parse_boolean_value()
		boolean_value877 := _t1635
		_t1636 := &pb.Value{}
		_t1636.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value877}
		_t1634 = _t1636
	} else {
		var _t1637 *pb.Value
		if prediction865 == 11 {
			p.consumeLiteral("missing")
			_t1638 := &pb.MissingValue{}
			_t1639 := &pb.Value{}
			_t1639.Value = &pb.Value_MissingValue{MissingValue: _t1638}
			_t1637 = _t1639
		} else {
			var _t1640 *pb.Value
			if prediction865 == 10 {
				formatted_decimal876 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1641 := &pb.Value{}
				_t1641.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal876}
				_t1640 = _t1641
			} else {
				var _t1642 *pb.Value
				if prediction865 == 9 {
					formatted_int128875 := p.consumeTerminal("INT128").Value.int128
					_t1643 := &pb.Value{}
					_t1643.Value = &pb.Value_Int128Value{Int128Value: formatted_int128875}
					_t1642 = _t1643
				} else {
					var _t1644 *pb.Value
					if prediction865 == 8 {
						formatted_uint128874 := p.consumeTerminal("UINT128").Value.uint128
						_t1645 := &pb.Value{}
						_t1645.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128874}
						_t1644 = _t1645
					} else {
						var _t1646 *pb.Value
						if prediction865 == 7 {
							formatted_uint32873 := p.consumeTerminal("UINT32").Value.u32
							_t1647 := &pb.Value{}
							_t1647.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32873}
							_t1646 = _t1647
						} else {
							var _t1648 *pb.Value
							if prediction865 == 6 {
								formatted_float872 := p.consumeTerminal("FLOAT").Value.f64
								_t1649 := &pb.Value{}
								_t1649.Value = &pb.Value_FloatValue{FloatValue: formatted_float872}
								_t1648 = _t1649
							} else {
								var _t1650 *pb.Value
								if prediction865 == 5 {
									formatted_float32871 := p.consumeTerminal("FLOAT32").Value.f32
									_t1651 := &pb.Value{}
									_t1651.Value = &pb.Value_Float32Value{Float32Value: formatted_float32871}
									_t1650 = _t1651
								} else {
									var _t1652 *pb.Value
									if prediction865 == 4 {
										formatted_int870 := p.consumeTerminal("INT").Value.i64
										_t1653 := &pb.Value{}
										_t1653.Value = &pb.Value_IntValue{IntValue: formatted_int870}
										_t1652 = _t1653
									} else {
										var _t1654 *pb.Value
										if prediction865 == 3 {
											formatted_int32869 := p.consumeTerminal("INT32").Value.i32
											_t1655 := &pb.Value{}
											_t1655.Value = &pb.Value_Int32Value{Int32Value: formatted_int32869}
											_t1654 = _t1655
										} else {
											var _t1656 *pb.Value
											if prediction865 == 2 {
												formatted_string868 := p.consumeTerminal("STRING").Value.str
												_t1657 := &pb.Value{}
												_t1657.Value = &pb.Value_StringValue{StringValue: formatted_string868}
												_t1656 = _t1657
											} else {
												var _t1658 *pb.Value
												if prediction865 == 1 {
													_t1659 := p.parse_datetime()
													datetime867 := _t1659
													_t1660 := &pb.Value{}
													_t1660.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime867}
													_t1658 = _t1660
												} else {
													var _t1661 *pb.Value
													if prediction865 == 0 {
														_t1662 := p.parse_date()
														date866 := _t1662
														_t1663 := &pb.Value{}
														_t1663.Value = &pb.Value_DateValue{DateValue: date866}
														_t1661 = _t1663
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1658 = _t1661
												}
												_t1656 = _t1658
											}
											_t1654 = _t1656
										}
										_t1652 = _t1654
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
			_t1637 = _t1640
		}
		_t1634 = _t1637
	}
	result879 := _t1634
	p.recordSpan(int(span_start878), "Value")
	return result879
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start883 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int880 := p.consumeTerminal("INT").Value.i64
	formatted_int_3881 := p.consumeTerminal("INT").Value.i64
	formatted_int_4882 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1664 := &pb.DateValue{Year: int32(formatted_int880), Month: int32(formatted_int_3881), Day: int32(formatted_int_4882)}
	result884 := _t1664
	p.recordSpan(int(span_start883), "DateValue")
	return result884
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start892 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int885 := p.consumeTerminal("INT").Value.i64
	formatted_int_3886 := p.consumeTerminal("INT").Value.i64
	formatted_int_4887 := p.consumeTerminal("INT").Value.i64
	formatted_int_5888 := p.consumeTerminal("INT").Value.i64
	formatted_int_6889 := p.consumeTerminal("INT").Value.i64
	formatted_int_7890 := p.consumeTerminal("INT").Value.i64
	var _t1665 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1665 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8891 := _t1665
	p.consumeLiteral(")")
	_t1666 := &pb.DateTimeValue{Year: int32(formatted_int885), Month: int32(formatted_int_3886), Day: int32(formatted_int_4887), Hour: int32(formatted_int_5888), Minute: int32(formatted_int_6889), Second: int32(formatted_int_7890), Microsecond: int32(deref(formatted_int_8891, 0))}
	result893 := _t1666
	p.recordSpan(int(span_start892), "DateTimeValue")
	return result893
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start898 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs894 := []*pb.Formula{}
	cond895 := p.matchLookaheadLiteral("(", 0)
	for cond895 {
		_t1667 := p.parse_formula()
		item896 := _t1667
		xs894 = append(xs894, item896)
		cond895 = p.matchLookaheadLiteral("(", 0)
	}
	formulas897 := xs894
	p.consumeLiteral(")")
	_t1668 := &pb.Conjunction{Args: formulas897}
	result899 := _t1668
	p.recordSpan(int(span_start898), "Conjunction")
	return result899
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start904 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs900 := []*pb.Formula{}
	cond901 := p.matchLookaheadLiteral("(", 0)
	for cond901 {
		_t1669 := p.parse_formula()
		item902 := _t1669
		xs900 = append(xs900, item902)
		cond901 = p.matchLookaheadLiteral("(", 0)
	}
	formulas903 := xs900
	p.consumeLiteral(")")
	_t1670 := &pb.Disjunction{Args: formulas903}
	result905 := _t1670
	p.recordSpan(int(span_start904), "Disjunction")
	return result905
}

func (p *Parser) parse_not() *pb.Not {
	span_start907 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1671 := p.parse_formula()
	formula906 := _t1671
	p.consumeLiteral(")")
	_t1672 := &pb.Not{Arg: formula906}
	result908 := _t1672
	p.recordSpan(int(span_start907), "Not")
	return result908
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start912 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1673 := p.parse_name()
	name909 := _t1673
	_t1674 := p.parse_ffi_args()
	ffi_args910 := _t1674
	_t1675 := p.parse_terms()
	terms911 := _t1675
	p.consumeLiteral(")")
	_t1676 := &pb.FFI{Name: name909, Args: ffi_args910, Terms: terms911}
	result913 := _t1676
	p.recordSpan(int(span_start912), "FFI")
	return result913
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol914 := p.consumeTerminal("SYMBOL").Value.str
	return symbol914
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs915 := []*pb.Abstraction{}
	cond916 := p.matchLookaheadLiteral("(", 0)
	for cond916 {
		_t1677 := p.parse_abstraction()
		item917 := _t1677
		xs915 = append(xs915, item917)
		cond916 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions918 := xs915
	p.consumeLiteral(")")
	return abstractions918
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start924 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1678 := p.parse_relation_id()
	relation_id919 := _t1678
	xs920 := []*pb.Term{}
	cond921 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond921 {
		_t1679 := p.parse_term()
		item922 := _t1679
		xs920 = append(xs920, item922)
		cond921 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms923 := xs920
	p.consumeLiteral(")")
	_t1680 := &pb.Atom{Name: relation_id919, Terms: terms923}
	result925 := _t1680
	p.recordSpan(int(span_start924), "Atom")
	return result925
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start931 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1681 := p.parse_name()
	name926 := _t1681
	xs927 := []*pb.Term{}
	cond928 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond928 {
		_t1682 := p.parse_term()
		item929 := _t1682
		xs927 = append(xs927, item929)
		cond928 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms930 := xs927
	p.consumeLiteral(")")
	_t1683 := &pb.Pragma{Name: name926, Terms: terms930}
	result932 := _t1683
	p.recordSpan(int(span_start931), "Pragma")
	return result932
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start948 := int64(p.spanStart())
	var _t1684 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1685 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1685 = 9
		} else {
			var _t1686 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1686 = 4
			} else {
				var _t1687 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1687 = 3
				} else {
					var _t1688 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1688 = 0
					} else {
						var _t1689 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1689 = 2
						} else {
							var _t1690 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1690 = 1
							} else {
								var _t1691 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1691 = 8
								} else {
									var _t1692 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1692 = 6
									} else {
										var _t1693 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1693 = 5
										} else {
											var _t1694 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1694 = 7
											} else {
												_t1694 = -1
											}
											_t1693 = _t1694
										}
										_t1692 = _t1693
									}
									_t1691 = _t1692
								}
								_t1690 = _t1691
							}
							_t1689 = _t1690
						}
						_t1688 = _t1689
					}
					_t1687 = _t1688
				}
				_t1686 = _t1687
			}
			_t1685 = _t1686
		}
		_t1684 = _t1685
	} else {
		_t1684 = -1
	}
	prediction933 := _t1684
	var _t1695 *pb.Primitive
	if prediction933 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1696 := p.parse_name()
		name943 := _t1696
		xs944 := []*pb.RelTerm{}
		cond945 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond945 {
			_t1697 := p.parse_rel_term()
			item946 := _t1697
			xs944 = append(xs944, item946)
			cond945 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms947 := xs944
		p.consumeLiteral(")")
		_t1698 := &pb.Primitive{Name: name943, Terms: rel_terms947}
		_t1695 = _t1698
	} else {
		var _t1699 *pb.Primitive
		if prediction933 == 8 {
			_t1700 := p.parse_divide()
			divide942 := _t1700
			_t1699 = divide942
		} else {
			var _t1701 *pb.Primitive
			if prediction933 == 7 {
				_t1702 := p.parse_multiply()
				multiply941 := _t1702
				_t1701 = multiply941
			} else {
				var _t1703 *pb.Primitive
				if prediction933 == 6 {
					_t1704 := p.parse_minus()
					minus940 := _t1704
					_t1703 = minus940
				} else {
					var _t1705 *pb.Primitive
					if prediction933 == 5 {
						_t1706 := p.parse_add()
						add939 := _t1706
						_t1705 = add939
					} else {
						var _t1707 *pb.Primitive
						if prediction933 == 4 {
							_t1708 := p.parse_gt_eq()
							gt_eq938 := _t1708
							_t1707 = gt_eq938
						} else {
							var _t1709 *pb.Primitive
							if prediction933 == 3 {
								_t1710 := p.parse_gt()
								gt937 := _t1710
								_t1709 = gt937
							} else {
								var _t1711 *pb.Primitive
								if prediction933 == 2 {
									_t1712 := p.parse_lt_eq()
									lt_eq936 := _t1712
									_t1711 = lt_eq936
								} else {
									var _t1713 *pb.Primitive
									if prediction933 == 1 {
										_t1714 := p.parse_lt()
										lt935 := _t1714
										_t1713 = lt935
									} else {
										var _t1715 *pb.Primitive
										if prediction933 == 0 {
											_t1716 := p.parse_eq()
											eq934 := _t1716
											_t1715 = eq934
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1713 = _t1715
									}
									_t1711 = _t1713
								}
								_t1709 = _t1711
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
		_t1695 = _t1699
	}
	result949 := _t1695
	p.recordSpan(int(span_start948), "Primitive")
	return result949
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1717 := p.parse_term()
	term950 := _t1717
	_t1718 := p.parse_term()
	term_3951 := _t1718
	p.consumeLiteral(")")
	_t1719 := &pb.RelTerm{}
	_t1719.RelTermType = &pb.RelTerm_Term{Term: term950}
	_t1720 := &pb.RelTerm{}
	_t1720.RelTermType = &pb.RelTerm_Term{Term: term_3951}
	_t1721 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1719, _t1720}}
	result953 := _t1721
	p.recordSpan(int(span_start952), "Primitive")
	return result953
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start956 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1722 := p.parse_term()
	term954 := _t1722
	_t1723 := p.parse_term()
	term_3955 := _t1723
	p.consumeLiteral(")")
	_t1724 := &pb.RelTerm{}
	_t1724.RelTermType = &pb.RelTerm_Term{Term: term954}
	_t1725 := &pb.RelTerm{}
	_t1725.RelTermType = &pb.RelTerm_Term{Term: term_3955}
	_t1726 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1724, _t1725}}
	result957 := _t1726
	p.recordSpan(int(span_start956), "Primitive")
	return result957
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1727 := p.parse_term()
	term958 := _t1727
	_t1728 := p.parse_term()
	term_3959 := _t1728
	p.consumeLiteral(")")
	_t1729 := &pb.RelTerm{}
	_t1729.RelTermType = &pb.RelTerm_Term{Term: term958}
	_t1730 := &pb.RelTerm{}
	_t1730.RelTermType = &pb.RelTerm_Term{Term: term_3959}
	_t1731 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1729, _t1730}}
	result961 := _t1731
	p.recordSpan(int(span_start960), "Primitive")
	return result961
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start964 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1732 := p.parse_term()
	term962 := _t1732
	_t1733 := p.parse_term()
	term_3963 := _t1733
	p.consumeLiteral(")")
	_t1734 := &pb.RelTerm{}
	_t1734.RelTermType = &pb.RelTerm_Term{Term: term962}
	_t1735 := &pb.RelTerm{}
	_t1735.RelTermType = &pb.RelTerm_Term{Term: term_3963}
	_t1736 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1734, _t1735}}
	result965 := _t1736
	p.recordSpan(int(span_start964), "Primitive")
	return result965
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1737 := p.parse_term()
	term966 := _t1737
	_t1738 := p.parse_term()
	term_3967 := _t1738
	p.consumeLiteral(")")
	_t1739 := &pb.RelTerm{}
	_t1739.RelTermType = &pb.RelTerm_Term{Term: term966}
	_t1740 := &pb.RelTerm{}
	_t1740.RelTermType = &pb.RelTerm_Term{Term: term_3967}
	_t1741 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1739, _t1740}}
	result969 := _t1741
	p.recordSpan(int(span_start968), "Primitive")
	return result969
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start973 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1742 := p.parse_term()
	term970 := _t1742
	_t1743 := p.parse_term()
	term_3971 := _t1743
	_t1744 := p.parse_term()
	term_4972 := _t1744
	p.consumeLiteral(")")
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term970}
	_t1746 := &pb.RelTerm{}
	_t1746.RelTermType = &pb.RelTerm_Term{Term: term_3971}
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term_4972}
	_t1748 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1745, _t1746, _t1747}}
	result974 := _t1748
	p.recordSpan(int(span_start973), "Primitive")
	return result974
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start978 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1749 := p.parse_term()
	term975 := _t1749
	_t1750 := p.parse_term()
	term_3976 := _t1750
	_t1751 := p.parse_term()
	term_4977 := _t1751
	p.consumeLiteral(")")
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term975}
	_t1753 := &pb.RelTerm{}
	_t1753.RelTermType = &pb.RelTerm_Term{Term: term_3976}
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term_4977}
	_t1755 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1752, _t1753, _t1754}}
	result979 := _t1755
	p.recordSpan(int(span_start978), "Primitive")
	return result979
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start983 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1756 := p.parse_term()
	term980 := _t1756
	_t1757 := p.parse_term()
	term_3981 := _t1757
	_t1758 := p.parse_term()
	term_4982 := _t1758
	p.consumeLiteral(")")
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term980}
	_t1760 := &pb.RelTerm{}
	_t1760.RelTermType = &pb.RelTerm_Term{Term: term_3981}
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term_4982}
	_t1762 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1759, _t1760, _t1761}}
	result984 := _t1762
	p.recordSpan(int(span_start983), "Primitive")
	return result984
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start988 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1763 := p.parse_term()
	term985 := _t1763
	_t1764 := p.parse_term()
	term_3986 := _t1764
	_t1765 := p.parse_term()
	term_4987 := _t1765
	p.consumeLiteral(")")
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term985}
	_t1767 := &pb.RelTerm{}
	_t1767.RelTermType = &pb.RelTerm_Term{Term: term_3986}
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term_4987}
	_t1769 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1766, _t1767, _t1768}}
	result989 := _t1769
	p.recordSpan(int(span_start988), "Primitive")
	return result989
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start993 := int64(p.spanStart())
	var _t1770 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1770 = 1
	} else {
		var _t1771 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1771 = 1
		} else {
			var _t1772 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1772 = 1
			} else {
				var _t1773 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1773 = 1
				} else {
					var _t1774 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1774 = 0
					} else {
						var _t1775 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1775 = 1
						} else {
							var _t1776 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1776 = 1
							} else {
								var _t1777 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1777 = 1
								} else {
									var _t1778 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1778 = 1
									} else {
										var _t1779 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1779 = 1
										} else {
											var _t1780 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1780 = 1
											} else {
												var _t1781 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1781 = 1
												} else {
													var _t1782 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1782 = 1
													} else {
														var _t1783 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1783 = 1
														} else {
															var _t1784 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1784 = 1
															} else {
																_t1784 = -1
															}
															_t1783 = _t1784
														}
														_t1782 = _t1783
													}
													_t1781 = _t1782
												}
												_t1780 = _t1781
											}
											_t1779 = _t1780
										}
										_t1778 = _t1779
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
	prediction990 := _t1770
	var _t1785 *pb.RelTerm
	if prediction990 == 1 {
		_t1786 := p.parse_term()
		term992 := _t1786
		_t1787 := &pb.RelTerm{}
		_t1787.RelTermType = &pb.RelTerm_Term{Term: term992}
		_t1785 = _t1787
	} else {
		var _t1788 *pb.RelTerm
		if prediction990 == 0 {
			_t1789 := p.parse_specialized_value()
			specialized_value991 := _t1789
			_t1790 := &pb.RelTerm{}
			_t1790.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value991}
			_t1788 = _t1790
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1785 = _t1788
	}
	result994 := _t1785
	p.recordSpan(int(span_start993), "RelTerm")
	return result994
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start996 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1791 := p.parse_raw_value()
	raw_value995 := _t1791
	result997 := raw_value995
	p.recordSpan(int(span_start996), "Value")
	return result997
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1003 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1792 := p.parse_name()
	name998 := _t1792
	xs999 := []*pb.RelTerm{}
	cond1000 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1000 {
		_t1793 := p.parse_rel_term()
		item1001 := _t1793
		xs999 = append(xs999, item1001)
		cond1000 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1002 := xs999
	p.consumeLiteral(")")
	_t1794 := &pb.RelAtom{Name: name998, Terms: rel_terms1002}
	result1004 := _t1794
	p.recordSpan(int(span_start1003), "RelAtom")
	return result1004
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1007 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1795 := p.parse_term()
	term1005 := _t1795
	_t1796 := p.parse_term()
	term_31006 := _t1796
	p.consumeLiteral(")")
	_t1797 := &pb.Cast{Input: term1005, Result: term_31006}
	result1008 := _t1797
	p.recordSpan(int(span_start1007), "Cast")
	return result1008
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1009 := []*pb.Attribute{}
	cond1010 := p.matchLookaheadLiteral("(", 0)
	for cond1010 {
		_t1798 := p.parse_attribute()
		item1011 := _t1798
		xs1009 = append(xs1009, item1011)
		cond1010 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1012 := xs1009
	p.consumeLiteral(")")
	return attributes1012
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1799 := p.parse_name()
	name1013 := _t1799
	xs1014 := []*pb.Value{}
	cond1015 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1015 {
		_t1800 := p.parse_raw_value()
		item1016 := _t1800
		xs1014 = append(xs1014, item1016)
		cond1015 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1017 := xs1014
	p.consumeLiteral(")")
	_t1801 := &pb.Attribute{Name: name1013, Args: raw_values1017}
	result1019 := _t1801
	p.recordSpan(int(span_start1018), "Attribute")
	return result1019
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1025 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1020 := []*pb.RelationId{}
	cond1021 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1021 {
		_t1802 := p.parse_relation_id()
		item1022 := _t1802
		xs1020 = append(xs1020, item1022)
		cond1021 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1023 := xs1020
	_t1803 := p.parse_script()
	script1024 := _t1803
	p.consumeLiteral(")")
	_t1804 := &pb.Algorithm{Global: relation_ids1023, Body: script1024}
	result1026 := _t1804
	p.recordSpan(int(span_start1025), "Algorithm")
	return result1026
}

func (p *Parser) parse_script() *pb.Script {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1027 := []*pb.Construct{}
	cond1028 := p.matchLookaheadLiteral("(", 0)
	for cond1028 {
		_t1805 := p.parse_construct()
		item1029 := _t1805
		xs1027 = append(xs1027, item1029)
		cond1028 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1030 := xs1027
	p.consumeLiteral(")")
	_t1806 := &pb.Script{Constructs: constructs1030}
	result1032 := _t1806
	p.recordSpan(int(span_start1031), "Script")
	return result1032
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1036 := int64(p.spanStart())
	var _t1807 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1808 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1808 = 1
		} else {
			var _t1809 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1809 = 1
			} else {
				var _t1810 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1810 = 1
				} else {
					var _t1811 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1811 = 0
					} else {
						var _t1812 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1812 = 1
						} else {
							var _t1813 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1813 = 1
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
		}
		_t1807 = _t1808
	} else {
		_t1807 = -1
	}
	prediction1033 := _t1807
	var _t1814 *pb.Construct
	if prediction1033 == 1 {
		_t1815 := p.parse_instruction()
		instruction1035 := _t1815
		_t1816 := &pb.Construct{}
		_t1816.ConstructType = &pb.Construct_Instruction{Instruction: instruction1035}
		_t1814 = _t1816
	} else {
		var _t1817 *pb.Construct
		if prediction1033 == 0 {
			_t1818 := p.parse_loop()
			loop1034 := _t1818
			_t1819 := &pb.Construct{}
			_t1819.ConstructType = &pb.Construct_Loop{Loop: loop1034}
			_t1817 = _t1819
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1814 = _t1817
	}
	result1037 := _t1814
	p.recordSpan(int(span_start1036), "Construct")
	return result1037
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1820 := p.parse_init()
	init1038 := _t1820
	_t1821 := p.parse_script()
	script1039 := _t1821
	p.consumeLiteral(")")
	_t1822 := &pb.Loop{Init: init1038, Body: script1039}
	result1041 := _t1822
	p.recordSpan(int(span_start1040), "Loop")
	return result1041
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1042 := []*pb.Instruction{}
	cond1043 := p.matchLookaheadLiteral("(", 0)
	for cond1043 {
		_t1823 := p.parse_instruction()
		item1044 := _t1823
		xs1042 = append(xs1042, item1044)
		cond1043 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1045 := xs1042
	p.consumeLiteral(")")
	return instructions1045
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1052 := int64(p.spanStart())
	var _t1824 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1825 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1825 = 1
		} else {
			var _t1826 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1826 = 4
			} else {
				var _t1827 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1827 = 3
				} else {
					var _t1828 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1828 = 2
					} else {
						var _t1829 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1829 = 0
						} else {
							_t1829 = -1
						}
						_t1828 = _t1829
					}
					_t1827 = _t1828
				}
				_t1826 = _t1827
			}
			_t1825 = _t1826
		}
		_t1824 = _t1825
	} else {
		_t1824 = -1
	}
	prediction1046 := _t1824
	var _t1830 *pb.Instruction
	if prediction1046 == 4 {
		_t1831 := p.parse_monus_def()
		monus_def1051 := _t1831
		_t1832 := &pb.Instruction{}
		_t1832.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1051}
		_t1830 = _t1832
	} else {
		var _t1833 *pb.Instruction
		if prediction1046 == 3 {
			_t1834 := p.parse_monoid_def()
			monoid_def1050 := _t1834
			_t1835 := &pb.Instruction{}
			_t1835.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1050}
			_t1833 = _t1835
		} else {
			var _t1836 *pb.Instruction
			if prediction1046 == 2 {
				_t1837 := p.parse_break()
				break1049 := _t1837
				_t1838 := &pb.Instruction{}
				_t1838.InstrType = &pb.Instruction_Break{Break: break1049}
				_t1836 = _t1838
			} else {
				var _t1839 *pb.Instruction
				if prediction1046 == 1 {
					_t1840 := p.parse_upsert()
					upsert1048 := _t1840
					_t1841 := &pb.Instruction{}
					_t1841.InstrType = &pb.Instruction_Upsert{Upsert: upsert1048}
					_t1839 = _t1841
				} else {
					var _t1842 *pb.Instruction
					if prediction1046 == 0 {
						_t1843 := p.parse_assign()
						assign1047 := _t1843
						_t1844 := &pb.Instruction{}
						_t1844.InstrType = &pb.Instruction_Assign{Assign: assign1047}
						_t1842 = _t1844
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1839 = _t1842
				}
				_t1836 = _t1839
			}
			_t1833 = _t1836
		}
		_t1830 = _t1833
	}
	result1053 := _t1830
	p.recordSpan(int(span_start1052), "Instruction")
	return result1053
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1057 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1845 := p.parse_relation_id()
	relation_id1054 := _t1845
	_t1846 := p.parse_abstraction()
	abstraction1055 := _t1846
	var _t1847 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1848 := p.parse_attrs()
		_t1847 = _t1848
	}
	attrs1056 := _t1847
	p.consumeLiteral(")")
	_t1849 := attrs1056
	if attrs1056 == nil {
		_t1849 = []*pb.Attribute{}
	}
	_t1850 := &pb.Assign{Name: relation_id1054, Body: abstraction1055, Attrs: _t1849}
	result1058 := _t1850
	p.recordSpan(int(span_start1057), "Assign")
	return result1058
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1062 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1851 := p.parse_relation_id()
	relation_id1059 := _t1851
	_t1852 := p.parse_abstraction_with_arity()
	abstraction_with_arity1060 := _t1852
	var _t1853 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1854 := p.parse_attrs()
		_t1853 = _t1854
	}
	attrs1061 := _t1853
	p.consumeLiteral(")")
	_t1855 := attrs1061
	if attrs1061 == nil {
		_t1855 = []*pb.Attribute{}
	}
	_t1856 := &pb.Upsert{Name: relation_id1059, Body: abstraction_with_arity1060[0].(*pb.Abstraction), Attrs: _t1855, ValueArity: abstraction_with_arity1060[1].(int64)}
	result1063 := _t1856
	p.recordSpan(int(span_start1062), "Upsert")
	return result1063
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1857 := p.parse_bindings()
	bindings1064 := _t1857
	_t1858 := p.parse_formula()
	formula1065 := _t1858
	p.consumeLiteral(")")
	_t1859 := &pb.Abstraction{Vars: listConcat(bindings1064[0].([]*pb.Binding), bindings1064[1].([]*pb.Binding)), Value: formula1065}
	return []interface{}{_t1859, int64(len(bindings1064[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1069 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1860 := p.parse_relation_id()
	relation_id1066 := _t1860
	_t1861 := p.parse_abstraction()
	abstraction1067 := _t1861
	var _t1862 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1863 := p.parse_attrs()
		_t1862 = _t1863
	}
	attrs1068 := _t1862
	p.consumeLiteral(")")
	_t1864 := attrs1068
	if attrs1068 == nil {
		_t1864 = []*pb.Attribute{}
	}
	_t1865 := &pb.Break{Name: relation_id1066, Body: abstraction1067, Attrs: _t1864}
	result1070 := _t1865
	p.recordSpan(int(span_start1069), "Break")
	return result1070
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1075 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1866 := p.parse_monoid()
	monoid1071 := _t1866
	_t1867 := p.parse_relation_id()
	relation_id1072 := _t1867
	_t1868 := p.parse_abstraction_with_arity()
	abstraction_with_arity1073 := _t1868
	var _t1869 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1870 := p.parse_attrs()
		_t1869 = _t1870
	}
	attrs1074 := _t1869
	p.consumeLiteral(")")
	_t1871 := attrs1074
	if attrs1074 == nil {
		_t1871 = []*pb.Attribute{}
	}
	_t1872 := &pb.MonoidDef{Monoid: monoid1071, Name: relation_id1072, Body: abstraction_with_arity1073[0].(*pb.Abstraction), Attrs: _t1871, ValueArity: abstraction_with_arity1073[1].(int64)}
	result1076 := _t1872
	p.recordSpan(int(span_start1075), "MonoidDef")
	return result1076
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1082 := int64(p.spanStart())
	var _t1873 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1874 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1874 = 3
		} else {
			var _t1875 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1875 = 0
			} else {
				var _t1876 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1876 = 1
				} else {
					var _t1877 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1877 = 2
					} else {
						_t1877 = -1
					}
					_t1876 = _t1877
				}
				_t1875 = _t1876
			}
			_t1874 = _t1875
		}
		_t1873 = _t1874
	} else {
		_t1873 = -1
	}
	prediction1077 := _t1873
	var _t1878 *pb.Monoid
	if prediction1077 == 3 {
		_t1879 := p.parse_sum_monoid()
		sum_monoid1081 := _t1879
		_t1880 := &pb.Monoid{}
		_t1880.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1081}
		_t1878 = _t1880
	} else {
		var _t1881 *pb.Monoid
		if prediction1077 == 2 {
			_t1882 := p.parse_max_monoid()
			max_monoid1080 := _t1882
			_t1883 := &pb.Monoid{}
			_t1883.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1080}
			_t1881 = _t1883
		} else {
			var _t1884 *pb.Monoid
			if prediction1077 == 1 {
				_t1885 := p.parse_min_monoid()
				min_monoid1079 := _t1885
				_t1886 := &pb.Monoid{}
				_t1886.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1079}
				_t1884 = _t1886
			} else {
				var _t1887 *pb.Monoid
				if prediction1077 == 0 {
					_t1888 := p.parse_or_monoid()
					or_monoid1078 := _t1888
					_t1889 := &pb.Monoid{}
					_t1889.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1078}
					_t1887 = _t1889
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1884 = _t1887
			}
			_t1881 = _t1884
		}
		_t1878 = _t1881
	}
	result1083 := _t1878
	p.recordSpan(int(span_start1082), "Monoid")
	return result1083
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1084 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1890 := &pb.OrMonoid{}
	result1085 := _t1890
	p.recordSpan(int(span_start1084), "OrMonoid")
	return result1085
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1087 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1891 := p.parse_type()
	type1086 := _t1891
	p.consumeLiteral(")")
	_t1892 := &pb.MinMonoid{Type: type1086}
	result1088 := _t1892
	p.recordSpan(int(span_start1087), "MinMonoid")
	return result1088
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1090 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1893 := p.parse_type()
	type1089 := _t1893
	p.consumeLiteral(")")
	_t1894 := &pb.MaxMonoid{Type: type1089}
	result1091 := _t1894
	p.recordSpan(int(span_start1090), "MaxMonoid")
	return result1091
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1093 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1895 := p.parse_type()
	type1092 := _t1895
	p.consumeLiteral(")")
	_t1896 := &pb.SumMonoid{Type: type1092}
	result1094 := _t1896
	p.recordSpan(int(span_start1093), "SumMonoid")
	return result1094
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1099 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1897 := p.parse_monoid()
	monoid1095 := _t1897
	_t1898 := p.parse_relation_id()
	relation_id1096 := _t1898
	_t1899 := p.parse_abstraction_with_arity()
	abstraction_with_arity1097 := _t1899
	var _t1900 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1901 := p.parse_attrs()
		_t1900 = _t1901
	}
	attrs1098 := _t1900
	p.consumeLiteral(")")
	_t1902 := attrs1098
	if attrs1098 == nil {
		_t1902 = []*pb.Attribute{}
	}
	_t1903 := &pb.MonusDef{Monoid: monoid1095, Name: relation_id1096, Body: abstraction_with_arity1097[0].(*pb.Abstraction), Attrs: _t1902, ValueArity: abstraction_with_arity1097[1].(int64)}
	result1100 := _t1903
	p.recordSpan(int(span_start1099), "MonusDef")
	return result1100
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1105 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1904 := p.parse_relation_id()
	relation_id1101 := _t1904
	_t1905 := p.parse_abstraction()
	abstraction1102 := _t1905
	_t1906 := p.parse_functional_dependency_keys()
	functional_dependency_keys1103 := _t1906
	_t1907 := p.parse_functional_dependency_values()
	functional_dependency_values1104 := _t1907
	p.consumeLiteral(")")
	_t1908 := &pb.FunctionalDependency{Guard: abstraction1102, Keys: functional_dependency_keys1103, Values: functional_dependency_values1104}
	_t1909 := &pb.Constraint{Name: relation_id1101}
	_t1909.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1908}
	result1106 := _t1909
	p.recordSpan(int(span_start1105), "Constraint")
	return result1106
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1107 := []*pb.Var{}
	cond1108 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1108 {
		_t1910 := p.parse_var()
		item1109 := _t1910
		xs1107 = append(xs1107, item1109)
		cond1108 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1110 := xs1107
	p.consumeLiteral(")")
	return vars1110
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1111 := []*pb.Var{}
	cond1112 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1112 {
		_t1911 := p.parse_var()
		item1113 := _t1911
		xs1111 = append(xs1111, item1113)
		cond1112 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1114 := xs1111
	p.consumeLiteral(")")
	return vars1114
}

func (p *Parser) parse_data() *pb.Data {
	span_start1120 := int64(p.spanStart())
	var _t1912 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1913 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1913 = 3
		} else {
			var _t1914 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1914 = 0
			} else {
				var _t1915 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1915 = 2
				} else {
					var _t1916 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1916 = 1
					} else {
						_t1916 = -1
					}
					_t1915 = _t1916
				}
				_t1914 = _t1915
			}
			_t1913 = _t1914
		}
		_t1912 = _t1913
	} else {
		_t1912 = -1
	}
	prediction1115 := _t1912
	var _t1917 *pb.Data
	if prediction1115 == 3 {
		_t1918 := p.parse_iceberg_data()
		iceberg_data1119 := _t1918
		_t1919 := &pb.Data{}
		_t1919.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1119}
		_t1917 = _t1919
	} else {
		var _t1920 *pb.Data
		if prediction1115 == 2 {
			_t1921 := p.parse_csv_data()
			csv_data1118 := _t1921
			_t1922 := &pb.Data{}
			_t1922.DataType = &pb.Data_CsvData{CsvData: csv_data1118}
			_t1920 = _t1922
		} else {
			var _t1923 *pb.Data
			if prediction1115 == 1 {
				_t1924 := p.parse_betree_relation()
				betree_relation1117 := _t1924
				_t1925 := &pb.Data{}
				_t1925.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1117}
				_t1923 = _t1925
			} else {
				var _t1926 *pb.Data
				if prediction1115 == 0 {
					_t1927 := p.parse_edb()
					edb1116 := _t1927
					_t1928 := &pb.Data{}
					_t1928.DataType = &pb.Data_Edb{Edb: edb1116}
					_t1926 = _t1928
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1923 = _t1926
			}
			_t1920 = _t1923
		}
		_t1917 = _t1920
	}
	result1121 := _t1917
	p.recordSpan(int(span_start1120), "Data")
	return result1121
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1929 := p.parse_relation_id()
	relation_id1122 := _t1929
	_t1930 := p.parse_edb_path()
	edb_path1123 := _t1930
	_t1931 := p.parse_edb_types()
	edb_types1124 := _t1931
	p.consumeLiteral(")")
	_t1932 := &pb.EDB{TargetId: relation_id1122, Path: edb_path1123, Types: edb_types1124}
	result1126 := _t1932
	p.recordSpan(int(span_start1125), "EDB")
	return result1126
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1127 := []string{}
	cond1128 := p.matchLookaheadTerminal("STRING", 0)
	for cond1128 {
		item1129 := p.consumeTerminal("STRING").Value.str
		xs1127 = append(xs1127, item1129)
		cond1128 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1130 := xs1127
	p.consumeLiteral("]")
	return strings1130
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1131 := []*pb.Type{}
	cond1132 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1132 {
		_t1933 := p.parse_type()
		item1133 := _t1933
		xs1131 = append(xs1131, item1133)
		cond1132 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1134 := xs1131
	p.consumeLiteral("]")
	return types1134
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1137 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1934 := p.parse_relation_id()
	relation_id1135 := _t1934
	_t1935 := p.parse_betree_info()
	betree_info1136 := _t1935
	p.consumeLiteral(")")
	_t1936 := &pb.BeTreeRelation{Name: relation_id1135, RelationInfo: betree_info1136}
	result1138 := _t1936
	p.recordSpan(int(span_start1137), "BeTreeRelation")
	return result1138
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1142 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1937 := p.parse_betree_info_key_types()
	betree_info_key_types1139 := _t1937
	_t1938 := p.parse_betree_info_value_types()
	betree_info_value_types1140 := _t1938
	_t1939 := p.parse_config_dict()
	config_dict1141 := _t1939
	p.consumeLiteral(")")
	_t1940 := p.construct_betree_info(betree_info_key_types1139, betree_info_value_types1140, config_dict1141)
	result1143 := _t1940
	p.recordSpan(int(span_start1142), "BeTreeInfo")
	return result1143
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1144 := []*pb.Type{}
	cond1145 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1145 {
		_t1941 := p.parse_type()
		item1146 := _t1941
		xs1144 = append(xs1144, item1146)
		cond1145 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1147 := xs1144
	p.consumeLiteral(")")
	return types1147
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1148 := []*pb.Type{}
	cond1149 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1149 {
		_t1942 := p.parse_type()
		item1150 := _t1942
		xs1148 = append(xs1148, item1150)
		cond1149 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1151 := xs1148
	p.consumeLiteral(")")
	return types1151
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1156 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1943 := p.parse_csvlocator()
	csvlocator1152 := _t1943
	_t1944 := p.parse_csv_config()
	csv_config1153 := _t1944
	_t1945 := p.parse_gnf_columns()
	gnf_columns1154 := _t1945
	_t1946 := p.parse_csv_asof()
	csv_asof1155 := _t1946
	p.consumeLiteral(")")
	_t1947 := &pb.CSVData{Locator: csvlocator1152, Config: csv_config1153, Columns: gnf_columns1154, Asof: csv_asof1155}
	result1157 := _t1947
	p.recordSpan(int(span_start1156), "CSVData")
	return result1157
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1160 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1948 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1949 := p.parse_csv_locator_paths()
		_t1948 = _t1949
	}
	csv_locator_paths1158 := _t1948
	var _t1950 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1951 := p.parse_csv_locator_inline_data()
		_t1950 = ptr(_t1951)
	}
	csv_locator_inline_data1159 := _t1950
	p.consumeLiteral(")")
	_t1952 := csv_locator_paths1158
	if csv_locator_paths1158 == nil {
		_t1952 = []string{}
	}
	_t1953 := &pb.CSVLocator{Paths: _t1952, InlineData: []byte(deref(csv_locator_inline_data1159, ""))}
	result1161 := _t1953
	p.recordSpan(int(span_start1160), "CSVLocator")
	return result1161
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1162 := []string{}
	cond1163 := p.matchLookaheadTerminal("STRING", 0)
	for cond1163 {
		item1164 := p.consumeTerminal("STRING").Value.str
		xs1162 = append(xs1162, item1164)
		cond1163 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1165 := xs1162
	p.consumeLiteral(")")
	return strings1165
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1166 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1166
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1168 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1954 := p.parse_config_dict()
	config_dict1167 := _t1954
	p.consumeLiteral(")")
	_t1955 := p.construct_csv_config(config_dict1167)
	result1169 := _t1955
	p.recordSpan(int(span_start1168), "CSVConfig")
	return result1169
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1170 := []*pb.GNFColumn{}
	cond1171 := p.matchLookaheadLiteral("(", 0)
	for cond1171 {
		_t1956 := p.parse_gnf_column()
		item1172 := _t1956
		xs1170 = append(xs1170, item1172)
		cond1171 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1173 := xs1170
	p.consumeLiteral(")")
	return gnf_columns1173
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1180 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1957 := p.parse_gnf_column_path()
	gnf_column_path1174 := _t1957
	var _t1958 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1959 := p.parse_relation_id()
		_t1958 = _t1959
	}
	relation_id1175 := _t1958
	p.consumeLiteral("[")
	xs1176 := []*pb.Type{}
	cond1177 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1177 {
		_t1960 := p.parse_type()
		item1178 := _t1960
		xs1176 = append(xs1176, item1178)
		cond1177 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1179 := xs1176
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1961 := &pb.GNFColumn{ColumnPath: gnf_column_path1174, TargetId: relation_id1175, Types: types1179}
	result1181 := _t1961
	p.recordSpan(int(span_start1180), "GNFColumn")
	return result1181
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1962 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1962 = 1
	} else {
		var _t1963 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1963 = 0
		} else {
			_t1963 = -1
		}
		_t1962 = _t1963
	}
	prediction1182 := _t1962
	var _t1964 []string
	if prediction1182 == 1 {
		p.consumeLiteral("[")
		xs1184 := []string{}
		cond1185 := p.matchLookaheadTerminal("STRING", 0)
		for cond1185 {
			item1186 := p.consumeTerminal("STRING").Value.str
			xs1184 = append(xs1184, item1186)
			cond1185 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1187 := xs1184
		p.consumeLiteral("]")
		_t1964 = strings1187
	} else {
		var _t1965 []string
		if prediction1182 == 0 {
			string1183 := p.consumeTerminal("STRING").Value.str
			_ = string1183
			_t1965 = []string{string1183}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1964 = _t1965
	}
	return _t1964
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1188 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1188
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1193 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1966 := p.parse_iceberg_locator()
	iceberg_locator1189 := _t1966
	_t1967 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1190 := _t1967
	_t1968 := p.parse_gnf_columns()
	gnf_columns1191 := _t1968
	var _t1969 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1970 := p.parse_iceberg_to_snapshot()
		_t1969 = ptr(_t1970)
	}
	iceberg_to_snapshot1192 := _t1969
	p.consumeLiteral(")")
	_t1971 := &pb.IcebergData{Locator: iceberg_locator1189, Config: iceberg_catalog_config1190, Columns: gnf_columns1191, ToSnapshot: ptr(deref(iceberg_to_snapshot1192, ""))}
	result1194 := _t1971
	p.recordSpan(int(span_start1193), "IcebergData")
	return result1194
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1201 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1195 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1196 := []string{}
	cond1197 := p.matchLookaheadTerminal("STRING", 0)
	for cond1197 {
		item1198 := p.consumeTerminal("STRING").Value.str
		xs1196 = append(xs1196, item1198)
		cond1197 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1199 := xs1196
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121200 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1972 := &pb.IcebergLocator{TableName: string1195, Namespace: strings1199, Warehouse: string_121200}
	result1202 := _t1972
	p.recordSpan(int(span_start1201), "IcebergLocator")
	return result1202
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1213 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1203 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1973 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1974 := p.parse_iceberg_catalog_config_scope()
		_t1973 = ptr(_t1974)
	}
	iceberg_catalog_config_scope1204 := _t1973
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1205 := [][]interface{}{}
	cond1206 := p.matchLookaheadLiteral("(", 0)
	for cond1206 {
		_t1975 := p.parse_iceberg_property_entry()
		item1207 := _t1975
		xs1205 = append(xs1205, item1207)
		cond1206 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1208 := xs1205
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1209 := [][]interface{}{}
	cond1210 := p.matchLookaheadLiteral("(", 0)
	for cond1210 {
		_t1976 := p.parse_iceberg_property_entry()
		item1211 := _t1976
		xs1209 = append(xs1209, item1211)
		cond1210 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys_131212 := xs1209
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1977 := p.construct_iceberg_catalog_config(string1203, iceberg_catalog_config_scope1204, iceberg_property_entrys1208, iceberg_property_entrys_131212)
	result1214 := _t1977
	p.recordSpan(int(span_start1213), "IcebergCatalogConfig")
	return result1214
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1215 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1215
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1216 := p.consumeTerminal("STRING").Value.str
	string_31217 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1216, string_31217}
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1218 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1218
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1978 := p.parse_fragment_id()
	fragment_id1219 := _t1978
	p.consumeLiteral(")")
	_t1979 := &pb.Undefine{FragmentId: fragment_id1219}
	result1221 := _t1979
	p.recordSpan(int(span_start1220), "Undefine")
	return result1221
}

func (p *Parser) parse_context() *pb.Context {
	span_start1226 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1222 := []*pb.RelationId{}
	cond1223 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1223 {
		_t1980 := p.parse_relation_id()
		item1224 := _t1980
		xs1222 = append(xs1222, item1224)
		cond1223 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1225 := xs1222
	p.consumeLiteral(")")
	_t1981 := &pb.Context{Relations: relation_ids1225}
	result1227 := _t1981
	p.recordSpan(int(span_start1226), "Context")
	return result1227
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1232 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1228 := []*pb.SnapshotMapping{}
	cond1229 := p.matchLookaheadLiteral("[", 0)
	for cond1229 {
		_t1982 := p.parse_snapshot_mapping()
		item1230 := _t1982
		xs1228 = append(xs1228, item1230)
		cond1229 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1231 := xs1228
	p.consumeLiteral(")")
	_t1983 := &pb.Snapshot{Mappings: snapshot_mappings1231}
	result1233 := _t1983
	p.recordSpan(int(span_start1232), "Snapshot")
	return result1233
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1236 := int64(p.spanStart())
	_t1984 := p.parse_edb_path()
	edb_path1234 := _t1984
	_t1985 := p.parse_relation_id()
	relation_id1235 := _t1985
	_t1986 := &pb.SnapshotMapping{DestinationPath: edb_path1234, SourceRelation: relation_id1235}
	result1237 := _t1986
	p.recordSpan(int(span_start1236), "SnapshotMapping")
	return result1237
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1238 := []*pb.Read{}
	cond1239 := p.matchLookaheadLiteral("(", 0)
	for cond1239 {
		_t1987 := p.parse_read()
		item1240 := _t1987
		xs1238 = append(xs1238, item1240)
		cond1239 = p.matchLookaheadLiteral("(", 0)
	}
	reads1241 := xs1238
	p.consumeLiteral(")")
	return reads1241
}

func (p *Parser) parse_read() *pb.Read {
	span_start1248 := int64(p.spanStart())
	var _t1988 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1989 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1989 = 2
		} else {
			var _t1990 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1990 = 1
			} else {
				var _t1991 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1991 = 4
				} else {
					var _t1992 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1992 = 4
					} else {
						var _t1993 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1993 = 0
						} else {
							var _t1994 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1994 = 3
							} else {
								_t1994 = -1
							}
							_t1993 = _t1994
						}
						_t1992 = _t1993
					}
					_t1991 = _t1992
				}
				_t1990 = _t1991
			}
			_t1989 = _t1990
		}
		_t1988 = _t1989
	} else {
		_t1988 = -1
	}
	prediction1242 := _t1988
	var _t1995 *pb.Read
	if prediction1242 == 4 {
		_t1996 := p.parse_export()
		export1247 := _t1996
		_t1997 := &pb.Read{}
		_t1997.ReadType = &pb.Read_Export{Export: export1247}
		_t1995 = _t1997
	} else {
		var _t1998 *pb.Read
		if prediction1242 == 3 {
			_t1999 := p.parse_abort()
			abort1246 := _t1999
			_t2000 := &pb.Read{}
			_t2000.ReadType = &pb.Read_Abort{Abort: abort1246}
			_t1998 = _t2000
		} else {
			var _t2001 *pb.Read
			if prediction1242 == 2 {
				_t2002 := p.parse_what_if()
				what_if1245 := _t2002
				_t2003 := &pb.Read{}
				_t2003.ReadType = &pb.Read_WhatIf{WhatIf: what_if1245}
				_t2001 = _t2003
			} else {
				var _t2004 *pb.Read
				if prediction1242 == 1 {
					_t2005 := p.parse_output()
					output1244 := _t2005
					_t2006 := &pb.Read{}
					_t2006.ReadType = &pb.Read_Output{Output: output1244}
					_t2004 = _t2006
				} else {
					var _t2007 *pb.Read
					if prediction1242 == 0 {
						_t2008 := p.parse_demand()
						demand1243 := _t2008
						_t2009 := &pb.Read{}
						_t2009.ReadType = &pb.Read_Demand{Demand: demand1243}
						_t2007 = _t2009
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2004 = _t2007
				}
				_t2001 = _t2004
			}
			_t1998 = _t2001
		}
		_t1995 = _t1998
	}
	result1249 := _t1995
	p.recordSpan(int(span_start1248), "Read")
	return result1249
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1251 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2010 := p.parse_relation_id()
	relation_id1250 := _t2010
	p.consumeLiteral(")")
	_t2011 := &pb.Demand{RelationId: relation_id1250}
	result1252 := _t2011
	p.recordSpan(int(span_start1251), "Demand")
	return result1252
}

func (p *Parser) parse_output() *pb.Output {
	span_start1255 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2012 := p.parse_name()
	name1253 := _t2012
	_t2013 := p.parse_relation_id()
	relation_id1254 := _t2013
	p.consumeLiteral(")")
	_t2014 := &pb.Output{Name: name1253, RelationId: relation_id1254}
	result1256 := _t2014
	p.recordSpan(int(span_start1255), "Output")
	return result1256
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1259 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2015 := p.parse_name()
	name1257 := _t2015
	_t2016 := p.parse_epoch()
	epoch1258 := _t2016
	p.consumeLiteral(")")
	_t2017 := &pb.WhatIf{Branch: name1257, Epoch: epoch1258}
	result1260 := _t2017
	p.recordSpan(int(span_start1259), "WhatIf")
	return result1260
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1263 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2018 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2019 := p.parse_name()
		_t2018 = ptr(_t2019)
	}
	name1261 := _t2018
	_t2020 := p.parse_relation_id()
	relation_id1262 := _t2020
	p.consumeLiteral(")")
	_t2021 := &pb.Abort{Name: deref(name1261, "abort"), RelationId: relation_id1262}
	result1264 := _t2021
	p.recordSpan(int(span_start1263), "Abort")
	return result1264
}

func (p *Parser) parse_export() *pb.Export {
	span_start1268 := int64(p.spanStart())
	var _t2022 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2023 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2023 = 1
		} else {
			var _t2024 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2024 = 0
			} else {
				_t2024 = -1
			}
			_t2023 = _t2024
		}
		_t2022 = _t2023
	} else {
		_t2022 = -1
	}
	prediction1265 := _t2022
	var _t2025 *pb.Export
	if prediction1265 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2026 := p.parse_export_iceberg_config()
		export_iceberg_config1267 := _t2026
		p.consumeLiteral(")")
		_t2027 := &pb.Export{}
		_t2027.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1267}
		_t2025 = _t2027
	} else {
		var _t2028 *pb.Export
		if prediction1265 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2029 := p.parse_export_csv_config()
			export_csv_config1266 := _t2029
			p.consumeLiteral(")")
			_t2030 := &pb.Export{}
			_t2030.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1266}
			_t2028 = _t2030
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2025 = _t2028
	}
	result1269 := _t2025
	p.recordSpan(int(span_start1268), "Export")
	return result1269
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1277 := int64(p.spanStart())
	var _t2031 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2032 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2032 = 0
		} else {
			var _t2033 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2033 = 1
			} else {
				_t2033 = -1
			}
			_t2032 = _t2033
		}
		_t2031 = _t2032
	} else {
		_t2031 = -1
	}
	prediction1270 := _t2031
	var _t2034 *pb.ExportCSVConfig
	if prediction1270 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2035 := p.parse_export_csv_path()
		export_csv_path1274 := _t2035
		_t2036 := p.parse_export_csv_columns_list()
		export_csv_columns_list1275 := _t2036
		_t2037 := p.parse_config_dict()
		config_dict1276 := _t2037
		p.consumeLiteral(")")
		_t2038 := p.construct_export_csv_config(export_csv_path1274, export_csv_columns_list1275, config_dict1276)
		_t2034 = _t2038
	} else {
		var _t2039 *pb.ExportCSVConfig
		if prediction1270 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2040 := p.parse_export_csv_path()
			export_csv_path1271 := _t2040
			_t2041 := p.parse_export_csv_source()
			export_csv_source1272 := _t2041
			_t2042 := p.parse_csv_config()
			csv_config1273 := _t2042
			p.consumeLiteral(")")
			_t2043 := p.construct_export_csv_config_with_source(export_csv_path1271, export_csv_source1272, csv_config1273)
			_t2039 = _t2043
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2034 = _t2039
	}
	result1278 := _t2034
	p.recordSpan(int(span_start1277), "ExportCSVConfig")
	return result1278
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1279 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1279
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1286 := int64(p.spanStart())
	var _t2044 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2045 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2045 = 1
		} else {
			var _t2046 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2046 = 0
			} else {
				_t2046 = -1
			}
			_t2045 = _t2046
		}
		_t2044 = _t2045
	} else {
		_t2044 = -1
	}
	prediction1280 := _t2044
	var _t2047 *pb.ExportCSVSource
	if prediction1280 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2048 := p.parse_relation_id()
		relation_id1285 := _t2048
		p.consumeLiteral(")")
		_t2049 := &pb.ExportCSVSource{}
		_t2049.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1285}
		_t2047 = _t2049
	} else {
		var _t2050 *pb.ExportCSVSource
		if prediction1280 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1281 := []*pb.ExportCSVColumn{}
			cond1282 := p.matchLookaheadLiteral("(", 0)
			for cond1282 {
				_t2051 := p.parse_export_csv_column()
				item1283 := _t2051
				xs1281 = append(xs1281, item1283)
				cond1282 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1284 := xs1281
			p.consumeLiteral(")")
			_t2052 := &pb.ExportCSVColumns{Columns: export_csv_columns1284}
			_t2053 := &pb.ExportCSVSource{}
			_t2053.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2052}
			_t2050 = _t2053
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2047 = _t2050
	}
	result1287 := _t2047
	p.recordSpan(int(span_start1286), "ExportCSVSource")
	return result1287
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1290 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1288 := p.consumeTerminal("STRING").Value.str
	_t2054 := p.parse_relation_id()
	relation_id1289 := _t2054
	p.consumeLiteral(")")
	_t2055 := &pb.ExportCSVColumn{ColumnName: string1288, ColumnData: relation_id1289}
	result1291 := _t2055
	p.recordSpan(int(span_start1290), "ExportCSVColumn")
	return result1291
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1292 := []*pb.ExportCSVColumn{}
	cond1293 := p.matchLookaheadLiteral("(", 0)
	for cond1293 {
		_t2056 := p.parse_export_csv_column()
		item1294 := _t2056
		xs1292 = append(xs1292, item1294)
		cond1293 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1295 := xs1292
	p.consumeLiteral(")")
	return export_csv_columns1295
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1304 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2057 := p.parse_iceberg_locator()
	iceberg_locator1296 := _t2057
	_t2058 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1297 := _t2058
	_t2059 := p.parse_export_iceberg_columns()
	export_iceberg_columns1298 := _t2059
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1299 := [][]interface{}{}
	cond1300 := p.matchLookaheadLiteral("(", 0)
	for cond1300 {
		_t2060 := p.parse_iceberg_property_entry()
		item1301 := _t2060
		xs1299 = append(xs1299, item1301)
		cond1300 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1302 := xs1299
	p.consumeLiteral(")")
	var _t2061 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2062 := p.parse_config_dict()
		_t2061 = _t2062
	}
	config_dict1303 := _t2061
	p.consumeLiteral(")")
	_t2063 := p.construct_export_iceberg_config_full(iceberg_locator1296, iceberg_catalog_config1297, export_iceberg_columns1298, iceberg_property_entrys1302, config_dict1303)
	result1305 := _t2063
	p.recordSpan(int(span_start1304), "ExportIcebergConfig")
	return result1305
}

func (p *Parser) parse_export_iceberg_columns() *pb.ExportIcebergColumns {
	span_start1311 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	p.consumeLiteral("(")
	p.consumeLiteral("source_table_def")
	_t2064 := p.parse_relation_id()
	relation_id1306 := _t2064
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("target_columns")
	xs1307 := []*pb.ExportIcebergColumn{}
	cond1308 := p.matchLookaheadLiteral("(", 0)
	for cond1308 {
		_t2065 := p.parse_export_iceberg_column()
		item1309 := _t2065
		xs1307 = append(xs1307, item1309)
		cond1308 = p.matchLookaheadLiteral("(", 0)
	}
	export_iceberg_columns1310 := xs1307
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t2066 := &pb.ExportIcebergColumns{SourceTableDef: relation_id1306, TargetColumns: export_iceberg_columns1310}
	result1312 := _t2066
	p.recordSpan(int(span_start1311), "ExportIcebergColumns")
	return result1312
}

func (p *Parser) parse_export_iceberg_column() *pb.ExportIcebergColumn {
	span_start1316 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_column")
	string1313 := p.consumeTerminal("STRING").Value.str
	_t2067 := p.parse_type()
	type1314 := _t2067
	_t2068 := p.parse_boolean_value()
	boolean_value1315 := _t2068
	p.consumeLiteral(")")
	_t2069 := &pb.ExportIcebergColumn{Name: string1313, Type: type1314, Nullable: boolean_value1315}
	result1317 := _t2069
	p.recordSpan(int(span_start1316), "ExportIcebergColumn")
	return result1317
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
