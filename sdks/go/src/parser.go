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
	var _t2068 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2068
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2069 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2069
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2070 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2070
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2071 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2071
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2072 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2072
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2073 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2073
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2074 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2074
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2075 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2075
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2076 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2076
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2077 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2077
	_t2078 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2078
	_t2079 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2079
	_t2080 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2080
	_t2081 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2081
	_t2082 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2082
	_t2083 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2083
	_t2084 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2084
	_t2085 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2085
	_t2086 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2086
	_t2087 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2087
	_t2088 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2088
	_t2089 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2089
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2090 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2090
	_t2091 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2091
	_t2092 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2092
	_t2093 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2093
	_t2094 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2094
	_t2095 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2095
	_t2096 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2096
	_t2097 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2097
	_t2098 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2098
	_t2099 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2099.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2099.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2099
	_t2100 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2100
}

func (p *Parser) default_configure() *pb.Configure {
	_t2101 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2101
	_t2102 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2102
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
	_t2103 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2103
	_t2104 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2104
	_t2105 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2105
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2106 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2106
	_t2107 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2107
	_t2108 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2108
	_t2109 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2109
	_t2110 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2110
	_t2111 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2111
	_t2112 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2112
	_t2113 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2113
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2114 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2114
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2115 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2115
}

func (p *Parser) construct_iceberg_locator(table_name string, namespace []string, warehouse string, from_snapshot_opt *string, to_snapshot_opt *string) *pb.IcebergLocator {
	_t2116 := &pb.IcebergLocator{TableName: table_name, Namespace: namespace, Warehouse: warehouse, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, ""))}
	return _t2116
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportGNFColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2117 := config_dict
	if config_dict == nil {
		_t2117 = [][]interface{}{}
	}
	cfg := dictFromList(_t2117)
	_t2118 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2118
	_t2119 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2119
	_t2120 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2120
	table_props := stringMapFromPairs(table_property_pairs)
	_t2121 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2121
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start664 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1316 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1317 := p.parse_configure()
		_t1316 = _t1317
	}
	configure658 := _t1316
	var _t1318 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1319 := p.parse_sync()
		_t1318 = _t1319
	}
	sync659 := _t1318
	xs660 := []*pb.Epoch{}
	cond661 := p.matchLookaheadLiteral("(", 0)
	for cond661 {
		_t1320 := p.parse_epoch()
		item662 := _t1320
		xs660 = append(xs660, item662)
		cond661 = p.matchLookaheadLiteral("(", 0)
	}
	epochs663 := xs660
	p.consumeLiteral(")")
	_t1321 := p.default_configure()
	_t1322 := configure658
	if configure658 == nil {
		_t1322 = _t1321
	}
	_t1323 := &pb.Transaction{Epochs: epochs663, Configure: _t1322, Sync: sync659}
	result665 := _t1323
	p.recordSpan(int(span_start664), "Transaction")
	return result665
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start667 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1324 := p.parse_config_dict()
	config_dict666 := _t1324
	p.consumeLiteral(")")
	_t1325 := p.construct_configure(config_dict666)
	result668 := _t1325
	p.recordSpan(int(span_start667), "Configure")
	return result668
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs669 := [][]interface{}{}
	cond670 := p.matchLookaheadLiteral(":", 0)
	for cond670 {
		_t1326 := p.parse_config_key_value()
		item671 := _t1326
		xs669 = append(xs669, item671)
		cond670 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values672 := xs669
	p.consumeLiteral("}")
	return config_key_values672
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol673 := p.consumeTerminal("SYMBOL").Value.str
	_t1327 := p.parse_raw_value()
	raw_value674 := _t1327
	return []interface{}{symbol673, raw_value674}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start688 := int64(p.spanStart())
	var _t1328 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1328 = 12
	} else {
		var _t1329 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1329 = 11
		} else {
			var _t1330 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1330 = 12
			} else {
				var _t1331 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1332 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1332 = 1
					} else {
						var _t1333 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1333 = 0
						} else {
							_t1333 = -1
						}
						_t1332 = _t1333
					}
					_t1331 = _t1332
				} else {
					var _t1334 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1334 = 7
					} else {
						var _t1335 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1335 = 8
						} else {
							var _t1336 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1336 = 2
							} else {
								var _t1337 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1337 = 3
								} else {
									var _t1338 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1338 = 9
									} else {
										var _t1339 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1339 = 4
										} else {
											var _t1340 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1340 = 5
											} else {
												var _t1341 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1341 = 6
												} else {
													var _t1342 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1342 = 10
													} else {
														_t1342 = -1
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
							_t1335 = _t1336
						}
						_t1334 = _t1335
					}
					_t1331 = _t1334
				}
				_t1330 = _t1331
			}
			_t1329 = _t1330
		}
		_t1328 = _t1329
	}
	prediction675 := _t1328
	var _t1343 *pb.Value
	if prediction675 == 12 {
		_t1344 := p.parse_boolean_value()
		boolean_value687 := _t1344
		_t1345 := &pb.Value{}
		_t1345.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value687}
		_t1343 = _t1345
	} else {
		var _t1346 *pb.Value
		if prediction675 == 11 {
			p.consumeLiteral("missing")
			_t1347 := &pb.MissingValue{}
			_t1348 := &pb.Value{}
			_t1348.Value = &pb.Value_MissingValue{MissingValue: _t1347}
			_t1346 = _t1348
		} else {
			var _t1349 *pb.Value
			if prediction675 == 10 {
				decimal686 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1350 := &pb.Value{}
				_t1350.Value = &pb.Value_DecimalValue{DecimalValue: decimal686}
				_t1349 = _t1350
			} else {
				var _t1351 *pb.Value
				if prediction675 == 9 {
					int128685 := p.consumeTerminal("INT128").Value.int128
					_t1352 := &pb.Value{}
					_t1352.Value = &pb.Value_Int128Value{Int128Value: int128685}
					_t1351 = _t1352
				} else {
					var _t1353 *pb.Value
					if prediction675 == 8 {
						uint128684 := p.consumeTerminal("UINT128").Value.uint128
						_t1354 := &pb.Value{}
						_t1354.Value = &pb.Value_Uint128Value{Uint128Value: uint128684}
						_t1353 = _t1354
					} else {
						var _t1355 *pb.Value
						if prediction675 == 7 {
							uint32683 := p.consumeTerminal("UINT32").Value.u32
							_t1356 := &pb.Value{}
							_t1356.Value = &pb.Value_Uint32Value{Uint32Value: uint32683}
							_t1355 = _t1356
						} else {
							var _t1357 *pb.Value
							if prediction675 == 6 {
								float682 := p.consumeTerminal("FLOAT").Value.f64
								_t1358 := &pb.Value{}
								_t1358.Value = &pb.Value_FloatValue{FloatValue: float682}
								_t1357 = _t1358
							} else {
								var _t1359 *pb.Value
								if prediction675 == 5 {
									float32681 := p.consumeTerminal("FLOAT32").Value.f32
									_t1360 := &pb.Value{}
									_t1360.Value = &pb.Value_Float32Value{Float32Value: float32681}
									_t1359 = _t1360
								} else {
									var _t1361 *pb.Value
									if prediction675 == 4 {
										int680 := p.consumeTerminal("INT").Value.i64
										_t1362 := &pb.Value{}
										_t1362.Value = &pb.Value_IntValue{IntValue: int680}
										_t1361 = _t1362
									} else {
										var _t1363 *pb.Value
										if prediction675 == 3 {
											int32679 := p.consumeTerminal("INT32").Value.i32
											_t1364 := &pb.Value{}
											_t1364.Value = &pb.Value_Int32Value{Int32Value: int32679}
											_t1363 = _t1364
										} else {
											var _t1365 *pb.Value
											if prediction675 == 2 {
												string678 := p.consumeTerminal("STRING").Value.str
												_t1366 := &pb.Value{}
												_t1366.Value = &pb.Value_StringValue{StringValue: string678}
												_t1365 = _t1366
											} else {
												var _t1367 *pb.Value
												if prediction675 == 1 {
													_t1368 := p.parse_raw_datetime()
													raw_datetime677 := _t1368
													_t1369 := &pb.Value{}
													_t1369.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime677}
													_t1367 = _t1369
												} else {
													var _t1370 *pb.Value
													if prediction675 == 0 {
														_t1371 := p.parse_raw_date()
														raw_date676 := _t1371
														_t1372 := &pb.Value{}
														_t1372.Value = &pb.Value_DateValue{DateValue: raw_date676}
														_t1370 = _t1372
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1367 = _t1370
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
				_t1349 = _t1351
			}
			_t1346 = _t1349
		}
		_t1343 = _t1346
	}
	result689 := _t1343
	p.recordSpan(int(span_start688), "Value")
	return result689
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start693 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int690 := p.consumeTerminal("INT").Value.i64
	int_3691 := p.consumeTerminal("INT").Value.i64
	int_4692 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1373 := &pb.DateValue{Year: int32(int690), Month: int32(int_3691), Day: int32(int_4692)}
	result694 := _t1373
	p.recordSpan(int(span_start693), "DateValue")
	return result694
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start702 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int695 := p.consumeTerminal("INT").Value.i64
	int_3696 := p.consumeTerminal("INT").Value.i64
	int_4697 := p.consumeTerminal("INT").Value.i64
	int_5698 := p.consumeTerminal("INT").Value.i64
	int_6699 := p.consumeTerminal("INT").Value.i64
	int_7700 := p.consumeTerminal("INT").Value.i64
	var _t1374 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1374 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8701 := _t1374
	p.consumeLiteral(")")
	_t1375 := &pb.DateTimeValue{Year: int32(int695), Month: int32(int_3696), Day: int32(int_4697), Hour: int32(int_5698), Minute: int32(int_6699), Second: int32(int_7700), Microsecond: int32(deref(int_8701, 0))}
	result703 := _t1375
	p.recordSpan(int(span_start702), "DateTimeValue")
	return result703
}

func (p *Parser) parse_boolean_value() bool {
	var _t1376 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1376 = 0
	} else {
		var _t1377 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1377 = 1
		} else {
			_t1377 = -1
		}
		_t1376 = _t1377
	}
	prediction704 := _t1376
	var _t1378 bool
	if prediction704 == 1 {
		p.consumeLiteral("false")
		_t1378 = false
	} else {
		var _t1379 bool
		if prediction704 == 0 {
			p.consumeLiteral("true")
			_t1379 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1378 = _t1379
	}
	return _t1378
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs705 := []*pb.FragmentId{}
	cond706 := p.matchLookaheadLiteral(":", 0)
	for cond706 {
		_t1380 := p.parse_fragment_id()
		item707 := _t1380
		xs705 = append(xs705, item707)
		cond706 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids708 := xs705
	p.consumeLiteral(")")
	_t1381 := &pb.Sync{Fragments: fragment_ids708}
	result710 := _t1381
	p.recordSpan(int(span_start709), "Sync")
	return result710
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start712 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol711 := p.consumeTerminal("SYMBOL").Value.str
	result713 := &pb.FragmentId{Id: []byte(symbol711)}
	p.recordSpan(int(span_start712), "FragmentId")
	return result713
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start716 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1382 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1383 := p.parse_epoch_writes()
		_t1382 = _t1383
	}
	epoch_writes714 := _t1382
	var _t1384 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1385 := p.parse_epoch_reads()
		_t1384 = _t1385
	}
	epoch_reads715 := _t1384
	p.consumeLiteral(")")
	_t1386 := epoch_writes714
	if epoch_writes714 == nil {
		_t1386 = []*pb.Write{}
	}
	_t1387 := epoch_reads715
	if epoch_reads715 == nil {
		_t1387 = []*pb.Read{}
	}
	_t1388 := &pb.Epoch{Writes: _t1386, Reads: _t1387}
	result717 := _t1388
	p.recordSpan(int(span_start716), "Epoch")
	return result717
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs718 := []*pb.Write{}
	cond719 := p.matchLookaheadLiteral("(", 0)
	for cond719 {
		_t1389 := p.parse_write()
		item720 := _t1389
		xs718 = append(xs718, item720)
		cond719 = p.matchLookaheadLiteral("(", 0)
	}
	writes721 := xs718
	p.consumeLiteral(")")
	return writes721
}

func (p *Parser) parse_write() *pb.Write {
	span_start727 := int64(p.spanStart())
	var _t1390 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1391 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1391 = 1
		} else {
			var _t1392 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1392 = 3
			} else {
				var _t1393 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1393 = 0
				} else {
					var _t1394 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1394 = 2
					} else {
						_t1394 = -1
					}
					_t1393 = _t1394
				}
				_t1392 = _t1393
			}
			_t1391 = _t1392
		}
		_t1390 = _t1391
	} else {
		_t1390 = -1
	}
	prediction722 := _t1390
	var _t1395 *pb.Write
	if prediction722 == 3 {
		_t1396 := p.parse_snapshot()
		snapshot726 := _t1396
		_t1397 := &pb.Write{}
		_t1397.WriteType = &pb.Write_Snapshot{Snapshot: snapshot726}
		_t1395 = _t1397
	} else {
		var _t1398 *pb.Write
		if prediction722 == 2 {
			_t1399 := p.parse_context()
			context725 := _t1399
			_t1400 := &pb.Write{}
			_t1400.WriteType = &pb.Write_Context{Context: context725}
			_t1398 = _t1400
		} else {
			var _t1401 *pb.Write
			if prediction722 == 1 {
				_t1402 := p.parse_undefine()
				undefine724 := _t1402
				_t1403 := &pb.Write{}
				_t1403.WriteType = &pb.Write_Undefine{Undefine: undefine724}
				_t1401 = _t1403
			} else {
				var _t1404 *pb.Write
				if prediction722 == 0 {
					_t1405 := p.parse_define()
					define723 := _t1405
					_t1406 := &pb.Write{}
					_t1406.WriteType = &pb.Write_Define{Define: define723}
					_t1404 = _t1406
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1401 = _t1404
			}
			_t1398 = _t1401
		}
		_t1395 = _t1398
	}
	result728 := _t1395
	p.recordSpan(int(span_start727), "Write")
	return result728
}

func (p *Parser) parse_define() *pb.Define {
	span_start730 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1407 := p.parse_fragment()
	fragment729 := _t1407
	p.consumeLiteral(")")
	_t1408 := &pb.Define{Fragment: fragment729}
	result731 := _t1408
	p.recordSpan(int(span_start730), "Define")
	return result731
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1409 := p.parse_new_fragment_id()
	new_fragment_id732 := _t1409
	xs733 := []*pb.Declaration{}
	cond734 := p.matchLookaheadLiteral("(", 0)
	for cond734 {
		_t1410 := p.parse_declaration()
		item735 := _t1410
		xs733 = append(xs733, item735)
		cond734 = p.matchLookaheadLiteral("(", 0)
	}
	declarations736 := xs733
	p.consumeLiteral(")")
	result738 := p.constructFragment(new_fragment_id732, declarations736)
	p.recordSpan(int(span_start737), "Fragment")
	return result738
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start740 := int64(p.spanStart())
	_t1411 := p.parse_fragment_id()
	fragment_id739 := _t1411
	p.startFragment(fragment_id739)
	result741 := fragment_id739
	p.recordSpan(int(span_start740), "FragmentId")
	return result741
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start747 := int64(p.spanStart())
	var _t1412 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1413 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1413 = 3
		} else {
			var _t1414 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1414 = 2
			} else {
				var _t1415 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1415 = 3
				} else {
					var _t1416 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1416 = 0
					} else {
						var _t1417 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1417 = 3
						} else {
							var _t1418 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1418 = 3
							} else {
								var _t1419 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1419 = 1
								} else {
									_t1419 = -1
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
			}
			_t1413 = _t1414
		}
		_t1412 = _t1413
	} else {
		_t1412 = -1
	}
	prediction742 := _t1412
	var _t1420 *pb.Declaration
	if prediction742 == 3 {
		_t1421 := p.parse_data()
		data746 := _t1421
		_t1422 := &pb.Declaration{}
		_t1422.DeclarationType = &pb.Declaration_Data{Data: data746}
		_t1420 = _t1422
	} else {
		var _t1423 *pb.Declaration
		if prediction742 == 2 {
			_t1424 := p.parse_constraint()
			constraint745 := _t1424
			_t1425 := &pb.Declaration{}
			_t1425.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint745}
			_t1423 = _t1425
		} else {
			var _t1426 *pb.Declaration
			if prediction742 == 1 {
				_t1427 := p.parse_algorithm()
				algorithm744 := _t1427
				_t1428 := &pb.Declaration{}
				_t1428.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm744}
				_t1426 = _t1428
			} else {
				var _t1429 *pb.Declaration
				if prediction742 == 0 {
					_t1430 := p.parse_def()
					def743 := _t1430
					_t1431 := &pb.Declaration{}
					_t1431.DeclarationType = &pb.Declaration_Def{Def: def743}
					_t1429 = _t1431
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1426 = _t1429
			}
			_t1423 = _t1426
		}
		_t1420 = _t1423
	}
	result748 := _t1420
	p.recordSpan(int(span_start747), "Declaration")
	return result748
}

func (p *Parser) parse_def() *pb.Def {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1432 := p.parse_relation_id()
	relation_id749 := _t1432
	_t1433 := p.parse_abstraction()
	abstraction750 := _t1433
	var _t1434 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1435 := p.parse_attrs()
		_t1434 = _t1435
	}
	attrs751 := _t1434
	p.consumeLiteral(")")
	_t1436 := attrs751
	if attrs751 == nil {
		_t1436 = []*pb.Attribute{}
	}
	_t1437 := &pb.Def{Name: relation_id749, Body: abstraction750, Attrs: _t1436}
	result753 := _t1437
	p.recordSpan(int(span_start752), "Def")
	return result753
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start757 := int64(p.spanStart())
	var _t1438 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1438 = 0
	} else {
		var _t1439 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1439 = 1
		} else {
			_t1439 = -1
		}
		_t1438 = _t1439
	}
	prediction754 := _t1438
	var _t1440 *pb.RelationId
	if prediction754 == 1 {
		uint128756 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128756
		_t1440 = &pb.RelationId{IdLow: uint128756.Low, IdHigh: uint128756.High}
	} else {
		var _t1441 *pb.RelationId
		if prediction754 == 0 {
			p.consumeLiteral(":")
			symbol755 := p.consumeTerminal("SYMBOL").Value.str
			_t1441 = p.relationIdFromString(symbol755)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1440 = _t1441
	}
	result758 := _t1440
	p.recordSpan(int(span_start757), "RelationId")
	return result758
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1442 := p.parse_bindings()
	bindings759 := _t1442
	_t1443 := p.parse_formula()
	formula760 := _t1443
	p.consumeLiteral(")")
	_t1444 := &pb.Abstraction{Vars: listConcat(bindings759[0].([]*pb.Binding), bindings759[1].([]*pb.Binding)), Value: formula760}
	result762 := _t1444
	p.recordSpan(int(span_start761), "Abstraction")
	return result762
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs763 := []*pb.Binding{}
	cond764 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond764 {
		_t1445 := p.parse_binding()
		item765 := _t1445
		xs763 = append(xs763, item765)
		cond764 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings766 := xs763
	var _t1446 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1447 := p.parse_value_bindings()
		_t1446 = _t1447
	}
	value_bindings767 := _t1446
	p.consumeLiteral("]")
	_t1448 := value_bindings767
	if value_bindings767 == nil {
		_t1448 = []*pb.Binding{}
	}
	return []interface{}{bindings766, _t1448}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start770 := int64(p.spanStart())
	symbol768 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1449 := p.parse_type()
	type769 := _t1449
	_t1450 := &pb.Var{Name: symbol768}
	_t1451 := &pb.Binding{Var: _t1450, Type: type769}
	result771 := _t1451
	p.recordSpan(int(span_start770), "Binding")
	return result771
}

func (p *Parser) parse_type() *pb.Type {
	span_start787 := int64(p.spanStart())
	var _t1452 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1452 = 0
	} else {
		var _t1453 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1453 = 13
		} else {
			var _t1454 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1454 = 4
			} else {
				var _t1455 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1455 = 1
				} else {
					var _t1456 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1456 = 8
					} else {
						var _t1457 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1457 = 11
						} else {
							var _t1458 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1458 = 5
							} else {
								var _t1459 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1459 = 2
								} else {
									var _t1460 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1460 = 12
									} else {
										var _t1461 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1461 = 3
										} else {
											var _t1462 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1462 = 7
											} else {
												var _t1463 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1463 = 6
												} else {
													var _t1464 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1464 = 10
													} else {
														var _t1465 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1465 = 9
														} else {
															_t1465 = -1
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
			_t1453 = _t1454
		}
		_t1452 = _t1453
	}
	prediction772 := _t1452
	var _t1466 *pb.Type
	if prediction772 == 13 {
		_t1467 := p.parse_uint32_type()
		uint32_type786 := _t1467
		_t1468 := &pb.Type{}
		_t1468.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type786}
		_t1466 = _t1468
	} else {
		var _t1469 *pb.Type
		if prediction772 == 12 {
			_t1470 := p.parse_float32_type()
			float32_type785 := _t1470
			_t1471 := &pb.Type{}
			_t1471.Type = &pb.Type_Float32Type{Float32Type: float32_type785}
			_t1469 = _t1471
		} else {
			var _t1472 *pb.Type
			if prediction772 == 11 {
				_t1473 := p.parse_int32_type()
				int32_type784 := _t1473
				_t1474 := &pb.Type{}
				_t1474.Type = &pb.Type_Int32Type{Int32Type: int32_type784}
				_t1472 = _t1474
			} else {
				var _t1475 *pb.Type
				if prediction772 == 10 {
					_t1476 := p.parse_boolean_type()
					boolean_type783 := _t1476
					_t1477 := &pb.Type{}
					_t1477.Type = &pb.Type_BooleanType{BooleanType: boolean_type783}
					_t1475 = _t1477
				} else {
					var _t1478 *pb.Type
					if prediction772 == 9 {
						_t1479 := p.parse_decimal_type()
						decimal_type782 := _t1479
						_t1480 := &pb.Type{}
						_t1480.Type = &pb.Type_DecimalType{DecimalType: decimal_type782}
						_t1478 = _t1480
					} else {
						var _t1481 *pb.Type
						if prediction772 == 8 {
							_t1482 := p.parse_missing_type()
							missing_type781 := _t1482
							_t1483 := &pb.Type{}
							_t1483.Type = &pb.Type_MissingType{MissingType: missing_type781}
							_t1481 = _t1483
						} else {
							var _t1484 *pb.Type
							if prediction772 == 7 {
								_t1485 := p.parse_datetime_type()
								datetime_type780 := _t1485
								_t1486 := &pb.Type{}
								_t1486.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type780}
								_t1484 = _t1486
							} else {
								var _t1487 *pb.Type
								if prediction772 == 6 {
									_t1488 := p.parse_date_type()
									date_type779 := _t1488
									_t1489 := &pb.Type{}
									_t1489.Type = &pb.Type_DateType{DateType: date_type779}
									_t1487 = _t1489
								} else {
									var _t1490 *pb.Type
									if prediction772 == 5 {
										_t1491 := p.parse_int128_type()
										int128_type778 := _t1491
										_t1492 := &pb.Type{}
										_t1492.Type = &pb.Type_Int128Type{Int128Type: int128_type778}
										_t1490 = _t1492
									} else {
										var _t1493 *pb.Type
										if prediction772 == 4 {
											_t1494 := p.parse_uint128_type()
											uint128_type777 := _t1494
											_t1495 := &pb.Type{}
											_t1495.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type777}
											_t1493 = _t1495
										} else {
											var _t1496 *pb.Type
											if prediction772 == 3 {
												_t1497 := p.parse_float_type()
												float_type776 := _t1497
												_t1498 := &pb.Type{}
												_t1498.Type = &pb.Type_FloatType{FloatType: float_type776}
												_t1496 = _t1498
											} else {
												var _t1499 *pb.Type
												if prediction772 == 2 {
													_t1500 := p.parse_int_type()
													int_type775 := _t1500
													_t1501 := &pb.Type{}
													_t1501.Type = &pb.Type_IntType{IntType: int_type775}
													_t1499 = _t1501
												} else {
													var _t1502 *pb.Type
													if prediction772 == 1 {
														_t1503 := p.parse_string_type()
														string_type774 := _t1503
														_t1504 := &pb.Type{}
														_t1504.Type = &pb.Type_StringType{StringType: string_type774}
														_t1502 = _t1504
													} else {
														var _t1505 *pb.Type
														if prediction772 == 0 {
															_t1506 := p.parse_unspecified_type()
															unspecified_type773 := _t1506
															_t1507 := &pb.Type{}
															_t1507.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type773}
															_t1505 = _t1507
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
	result788 := _t1466
	p.recordSpan(int(span_start787), "Type")
	return result788
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start789 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1508 := &pb.UnspecifiedType{}
	result790 := _t1508
	p.recordSpan(int(span_start789), "UnspecifiedType")
	return result790
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1509 := &pb.StringType{}
	result792 := _t1509
	p.recordSpan(int(span_start791), "StringType")
	return result792
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start793 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1510 := &pb.IntType{}
	result794 := _t1510
	p.recordSpan(int(span_start793), "IntType")
	return result794
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start795 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1511 := &pb.FloatType{}
	result796 := _t1511
	p.recordSpan(int(span_start795), "FloatType")
	return result796
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1512 := &pb.UInt128Type{}
	result798 := _t1512
	p.recordSpan(int(span_start797), "UInt128Type")
	return result798
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start799 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1513 := &pb.Int128Type{}
	result800 := _t1513
	p.recordSpan(int(span_start799), "Int128Type")
	return result800
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1514 := &pb.DateType{}
	result802 := _t1514
	p.recordSpan(int(span_start801), "DateType")
	return result802
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1515 := &pb.DateTimeType{}
	result804 := _t1515
	p.recordSpan(int(span_start803), "DateTimeType")
	return result804
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1516 := &pb.MissingType{}
	result806 := _t1516
	p.recordSpan(int(span_start805), "MissingType")
	return result806
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int807 := p.consumeTerminal("INT").Value.i64
	int_3808 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1517 := &pb.DecimalType{Precision: int32(int807), Scale: int32(int_3808)}
	result810 := _t1517
	p.recordSpan(int(span_start809), "DecimalType")
	return result810
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1518 := &pb.BooleanType{}
	result812 := _t1518
	p.recordSpan(int(span_start811), "BooleanType")
	return result812
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1519 := &pb.Int32Type{}
	result814 := _t1519
	p.recordSpan(int(span_start813), "Int32Type")
	return result814
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1520 := &pb.Float32Type{}
	result816 := _t1520
	p.recordSpan(int(span_start815), "Float32Type")
	return result816
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1521 := &pb.UInt32Type{}
	result818 := _t1521
	p.recordSpan(int(span_start817), "UInt32Type")
	return result818
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs819 := []*pb.Binding{}
	cond820 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond820 {
		_t1522 := p.parse_binding()
		item821 := _t1522
		xs819 = append(xs819, item821)
		cond820 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings822 := xs819
	return bindings822
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start837 := int64(p.spanStart())
	var _t1523 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1524 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1524 = 0
		} else {
			var _t1525 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1525 = 11
			} else {
				var _t1526 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1526 = 3
				} else {
					var _t1527 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1527 = 10
					} else {
						var _t1528 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1528 = 9
						} else {
							var _t1529 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1529 = 5
							} else {
								var _t1530 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1530 = 6
								} else {
									var _t1531 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1531 = 7
									} else {
										var _t1532 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1532 = 1
										} else {
											var _t1533 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1533 = 2
											} else {
												var _t1534 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1534 = 12
												} else {
													var _t1535 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1535 = 8
													} else {
														var _t1536 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1536 = 4
														} else {
															var _t1537 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1537 = 10
															} else {
																var _t1538 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1538 = 10
																} else {
																	var _t1539 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1539 = 10
																	} else {
																		var _t1540 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1540 = 10
																		} else {
																			var _t1541 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1541 = 10
																			} else {
																				var _t1542 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1542 = 10
																				} else {
																					var _t1543 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1543 = 10
																					} else {
																						var _t1544 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1544 = 10
																						} else {
																							var _t1545 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1545 = 10
																							} else {
																								_t1545 = -1
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
			}
			_t1524 = _t1525
		}
		_t1523 = _t1524
	} else {
		_t1523 = -1
	}
	prediction823 := _t1523
	var _t1546 *pb.Formula
	if prediction823 == 12 {
		_t1547 := p.parse_cast()
		cast836 := _t1547
		_t1548 := &pb.Formula{}
		_t1548.FormulaType = &pb.Formula_Cast{Cast: cast836}
		_t1546 = _t1548
	} else {
		var _t1549 *pb.Formula
		if prediction823 == 11 {
			_t1550 := p.parse_rel_atom()
			rel_atom835 := _t1550
			_t1551 := &pb.Formula{}
			_t1551.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom835}
			_t1549 = _t1551
		} else {
			var _t1552 *pb.Formula
			if prediction823 == 10 {
				_t1553 := p.parse_primitive()
				primitive834 := _t1553
				_t1554 := &pb.Formula{}
				_t1554.FormulaType = &pb.Formula_Primitive{Primitive: primitive834}
				_t1552 = _t1554
			} else {
				var _t1555 *pb.Formula
				if prediction823 == 9 {
					_t1556 := p.parse_pragma()
					pragma833 := _t1556
					_t1557 := &pb.Formula{}
					_t1557.FormulaType = &pb.Formula_Pragma{Pragma: pragma833}
					_t1555 = _t1557
				} else {
					var _t1558 *pb.Formula
					if prediction823 == 8 {
						_t1559 := p.parse_atom()
						atom832 := _t1559
						_t1560 := &pb.Formula{}
						_t1560.FormulaType = &pb.Formula_Atom{Atom: atom832}
						_t1558 = _t1560
					} else {
						var _t1561 *pb.Formula
						if prediction823 == 7 {
							_t1562 := p.parse_ffi()
							ffi831 := _t1562
							_t1563 := &pb.Formula{}
							_t1563.FormulaType = &pb.Formula_Ffi{Ffi: ffi831}
							_t1561 = _t1563
						} else {
							var _t1564 *pb.Formula
							if prediction823 == 6 {
								_t1565 := p.parse_not()
								not830 := _t1565
								_t1566 := &pb.Formula{}
								_t1566.FormulaType = &pb.Formula_Not{Not: not830}
								_t1564 = _t1566
							} else {
								var _t1567 *pb.Formula
								if prediction823 == 5 {
									_t1568 := p.parse_disjunction()
									disjunction829 := _t1568
									_t1569 := &pb.Formula{}
									_t1569.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction829}
									_t1567 = _t1569
								} else {
									var _t1570 *pb.Formula
									if prediction823 == 4 {
										_t1571 := p.parse_conjunction()
										conjunction828 := _t1571
										_t1572 := &pb.Formula{}
										_t1572.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction828}
										_t1570 = _t1572
									} else {
										var _t1573 *pb.Formula
										if prediction823 == 3 {
											_t1574 := p.parse_reduce()
											reduce827 := _t1574
											_t1575 := &pb.Formula{}
											_t1575.FormulaType = &pb.Formula_Reduce{Reduce: reduce827}
											_t1573 = _t1575
										} else {
											var _t1576 *pb.Formula
											if prediction823 == 2 {
												_t1577 := p.parse_exists()
												exists826 := _t1577
												_t1578 := &pb.Formula{}
												_t1578.FormulaType = &pb.Formula_Exists{Exists: exists826}
												_t1576 = _t1578
											} else {
												var _t1579 *pb.Formula
												if prediction823 == 1 {
													_t1580 := p.parse_false()
													false825 := _t1580
													_t1581 := &pb.Formula{}
													_t1581.FormulaType = &pb.Formula_Disjunction{Disjunction: false825}
													_t1579 = _t1581
												} else {
													var _t1582 *pb.Formula
													if prediction823 == 0 {
														_t1583 := p.parse_true()
														true824 := _t1583
														_t1584 := &pb.Formula{}
														_t1584.FormulaType = &pb.Formula_Conjunction{Conjunction: true824}
														_t1582 = _t1584
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
	result838 := _t1546
	p.recordSpan(int(span_start837), "Formula")
	return result838
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1585 := &pb.Conjunction{Args: []*pb.Formula{}}
	result840 := _t1585
	p.recordSpan(int(span_start839), "Conjunction")
	return result840
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1586 := &pb.Disjunction{Args: []*pb.Formula{}}
	result842 := _t1586
	p.recordSpan(int(span_start841), "Disjunction")
	return result842
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1587 := p.parse_bindings()
	bindings843 := _t1587
	_t1588 := p.parse_formula()
	formula844 := _t1588
	p.consumeLiteral(")")
	_t1589 := &pb.Abstraction{Vars: listConcat(bindings843[0].([]*pb.Binding), bindings843[1].([]*pb.Binding)), Value: formula844}
	_t1590 := &pb.Exists{Body: _t1589}
	result846 := _t1590
	p.recordSpan(int(span_start845), "Exists")
	return result846
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start850 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1591 := p.parse_abstraction()
	abstraction847 := _t1591
	_t1592 := p.parse_abstraction()
	abstraction_3848 := _t1592
	_t1593 := p.parse_terms()
	terms849 := _t1593
	p.consumeLiteral(")")
	_t1594 := &pb.Reduce{Op: abstraction847, Body: abstraction_3848, Terms: terms849}
	result851 := _t1594
	p.recordSpan(int(span_start850), "Reduce")
	return result851
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs852 := []*pb.Term{}
	cond853 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond853 {
		_t1595 := p.parse_term()
		item854 := _t1595
		xs852 = append(xs852, item854)
		cond853 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms855 := xs852
	p.consumeLiteral(")")
	return terms855
}

func (p *Parser) parse_term() *pb.Term {
	span_start859 := int64(p.spanStart())
	var _t1596 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1596 = 1
	} else {
		var _t1597 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1597 = 1
		} else {
			var _t1598 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1598 = 1
			} else {
				var _t1599 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1599 = 1
				} else {
					var _t1600 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1600 = 0
					} else {
						var _t1601 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1601 = 1
						} else {
							var _t1602 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1602 = 1
							} else {
								var _t1603 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1603 = 1
								} else {
									var _t1604 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1604 = 1
									} else {
										var _t1605 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1605 = 1
										} else {
											var _t1606 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1606 = 1
											} else {
												var _t1607 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1607 = 1
												} else {
													var _t1608 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1608 = 1
													} else {
														var _t1609 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1609 = 1
														} else {
															_t1609 = -1
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
			_t1597 = _t1598
		}
		_t1596 = _t1597
	}
	prediction856 := _t1596
	var _t1610 *pb.Term
	if prediction856 == 1 {
		_t1611 := p.parse_value()
		value858 := _t1611
		_t1612 := &pb.Term{}
		_t1612.TermType = &pb.Term_Constant{Constant: value858}
		_t1610 = _t1612
	} else {
		var _t1613 *pb.Term
		if prediction856 == 0 {
			_t1614 := p.parse_var()
			var857 := _t1614
			_t1615 := &pb.Term{}
			_t1615.TermType = &pb.Term_Var{Var: var857}
			_t1613 = _t1615
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1610 = _t1613
	}
	result860 := _t1610
	p.recordSpan(int(span_start859), "Term")
	return result860
}

func (p *Parser) parse_var() *pb.Var {
	span_start862 := int64(p.spanStart())
	symbol861 := p.consumeTerminal("SYMBOL").Value.str
	_t1616 := &pb.Var{Name: symbol861}
	result863 := _t1616
	p.recordSpan(int(span_start862), "Var")
	return result863
}

func (p *Parser) parse_value() *pb.Value {
	span_start877 := int64(p.spanStart())
	var _t1617 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1617 = 12
	} else {
		var _t1618 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1618 = 11
		} else {
			var _t1619 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1619 = 12
			} else {
				var _t1620 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1621 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1621 = 1
					} else {
						var _t1622 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1622 = 0
						} else {
							_t1622 = -1
						}
						_t1621 = _t1622
					}
					_t1620 = _t1621
				} else {
					var _t1623 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1623 = 7
					} else {
						var _t1624 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1624 = 8
						} else {
							var _t1625 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1625 = 2
							} else {
								var _t1626 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1626 = 3
								} else {
									var _t1627 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1627 = 9
									} else {
										var _t1628 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1628 = 4
										} else {
											var _t1629 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1629 = 5
											} else {
												var _t1630 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1630 = 6
												} else {
													var _t1631 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1631 = 10
													} else {
														_t1631 = -1
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
					_t1620 = _t1623
				}
				_t1619 = _t1620
			}
			_t1618 = _t1619
		}
		_t1617 = _t1618
	}
	prediction864 := _t1617
	var _t1632 *pb.Value
	if prediction864 == 12 {
		_t1633 := p.parse_boolean_value()
		boolean_value876 := _t1633
		_t1634 := &pb.Value{}
		_t1634.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value876}
		_t1632 = _t1634
	} else {
		var _t1635 *pb.Value
		if prediction864 == 11 {
			p.consumeLiteral("missing")
			_t1636 := &pb.MissingValue{}
			_t1637 := &pb.Value{}
			_t1637.Value = &pb.Value_MissingValue{MissingValue: _t1636}
			_t1635 = _t1637
		} else {
			var _t1638 *pb.Value
			if prediction864 == 10 {
				formatted_decimal875 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1639 := &pb.Value{}
				_t1639.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal875}
				_t1638 = _t1639
			} else {
				var _t1640 *pb.Value
				if prediction864 == 9 {
					formatted_int128874 := p.consumeTerminal("INT128").Value.int128
					_t1641 := &pb.Value{}
					_t1641.Value = &pb.Value_Int128Value{Int128Value: formatted_int128874}
					_t1640 = _t1641
				} else {
					var _t1642 *pb.Value
					if prediction864 == 8 {
						formatted_uint128873 := p.consumeTerminal("UINT128").Value.uint128
						_t1643 := &pb.Value{}
						_t1643.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128873}
						_t1642 = _t1643
					} else {
						var _t1644 *pb.Value
						if prediction864 == 7 {
							formatted_uint32872 := p.consumeTerminal("UINT32").Value.u32
							_t1645 := &pb.Value{}
							_t1645.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32872}
							_t1644 = _t1645
						} else {
							var _t1646 *pb.Value
							if prediction864 == 6 {
								formatted_float871 := p.consumeTerminal("FLOAT").Value.f64
								_t1647 := &pb.Value{}
								_t1647.Value = &pb.Value_FloatValue{FloatValue: formatted_float871}
								_t1646 = _t1647
							} else {
								var _t1648 *pb.Value
								if prediction864 == 5 {
									formatted_float32870 := p.consumeTerminal("FLOAT32").Value.f32
									_t1649 := &pb.Value{}
									_t1649.Value = &pb.Value_Float32Value{Float32Value: formatted_float32870}
									_t1648 = _t1649
								} else {
									var _t1650 *pb.Value
									if prediction864 == 4 {
										formatted_int869 := p.consumeTerminal("INT").Value.i64
										_t1651 := &pb.Value{}
										_t1651.Value = &pb.Value_IntValue{IntValue: formatted_int869}
										_t1650 = _t1651
									} else {
										var _t1652 *pb.Value
										if prediction864 == 3 {
											formatted_int32868 := p.consumeTerminal("INT32").Value.i32
											_t1653 := &pb.Value{}
											_t1653.Value = &pb.Value_Int32Value{Int32Value: formatted_int32868}
											_t1652 = _t1653
										} else {
											var _t1654 *pb.Value
											if prediction864 == 2 {
												formatted_string867 := p.consumeTerminal("STRING").Value.str
												_t1655 := &pb.Value{}
												_t1655.Value = &pb.Value_StringValue{StringValue: formatted_string867}
												_t1654 = _t1655
											} else {
												var _t1656 *pb.Value
												if prediction864 == 1 {
													_t1657 := p.parse_datetime()
													datetime866 := _t1657
													_t1658 := &pb.Value{}
													_t1658.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime866}
													_t1656 = _t1658
												} else {
													var _t1659 *pb.Value
													if prediction864 == 0 {
														_t1660 := p.parse_date()
														date865 := _t1660
														_t1661 := &pb.Value{}
														_t1661.Value = &pb.Value_DateValue{DateValue: date865}
														_t1659 = _t1661
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1656 = _t1659
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
				_t1638 = _t1640
			}
			_t1635 = _t1638
		}
		_t1632 = _t1635
	}
	result878 := _t1632
	p.recordSpan(int(span_start877), "Value")
	return result878
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start882 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int879 := p.consumeTerminal("INT").Value.i64
	formatted_int_3880 := p.consumeTerminal("INT").Value.i64
	formatted_int_4881 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1662 := &pb.DateValue{Year: int32(formatted_int879), Month: int32(formatted_int_3880), Day: int32(formatted_int_4881)}
	result883 := _t1662
	p.recordSpan(int(span_start882), "DateValue")
	return result883
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int884 := p.consumeTerminal("INT").Value.i64
	formatted_int_3885 := p.consumeTerminal("INT").Value.i64
	formatted_int_4886 := p.consumeTerminal("INT").Value.i64
	formatted_int_5887 := p.consumeTerminal("INT").Value.i64
	formatted_int_6888 := p.consumeTerminal("INT").Value.i64
	formatted_int_7889 := p.consumeTerminal("INT").Value.i64
	var _t1663 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1663 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8890 := _t1663
	p.consumeLiteral(")")
	_t1664 := &pb.DateTimeValue{Year: int32(formatted_int884), Month: int32(formatted_int_3885), Day: int32(formatted_int_4886), Hour: int32(formatted_int_5887), Minute: int32(formatted_int_6888), Second: int32(formatted_int_7889), Microsecond: int32(deref(formatted_int_8890, 0))}
	result892 := _t1664
	p.recordSpan(int(span_start891), "DateTimeValue")
	return result892
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start897 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs893 := []*pb.Formula{}
	cond894 := p.matchLookaheadLiteral("(", 0)
	for cond894 {
		_t1665 := p.parse_formula()
		item895 := _t1665
		xs893 = append(xs893, item895)
		cond894 = p.matchLookaheadLiteral("(", 0)
	}
	formulas896 := xs893
	p.consumeLiteral(")")
	_t1666 := &pb.Conjunction{Args: formulas896}
	result898 := _t1666
	p.recordSpan(int(span_start897), "Conjunction")
	return result898
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs899 := []*pb.Formula{}
	cond900 := p.matchLookaheadLiteral("(", 0)
	for cond900 {
		_t1667 := p.parse_formula()
		item901 := _t1667
		xs899 = append(xs899, item901)
		cond900 = p.matchLookaheadLiteral("(", 0)
	}
	formulas902 := xs899
	p.consumeLiteral(")")
	_t1668 := &pb.Disjunction{Args: formulas902}
	result904 := _t1668
	p.recordSpan(int(span_start903), "Disjunction")
	return result904
}

func (p *Parser) parse_not() *pb.Not {
	span_start906 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1669 := p.parse_formula()
	formula905 := _t1669
	p.consumeLiteral(")")
	_t1670 := &pb.Not{Arg: formula905}
	result907 := _t1670
	p.recordSpan(int(span_start906), "Not")
	return result907
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start911 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1671 := p.parse_name()
	name908 := _t1671
	_t1672 := p.parse_ffi_args()
	ffi_args909 := _t1672
	_t1673 := p.parse_terms()
	terms910 := _t1673
	p.consumeLiteral(")")
	_t1674 := &pb.FFI{Name: name908, Args: ffi_args909, Terms: terms910}
	result912 := _t1674
	p.recordSpan(int(span_start911), "FFI")
	return result912
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol913 := p.consumeTerminal("SYMBOL").Value.str
	return symbol913
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs914 := []*pb.Abstraction{}
	cond915 := p.matchLookaheadLiteral("(", 0)
	for cond915 {
		_t1675 := p.parse_abstraction()
		item916 := _t1675
		xs914 = append(xs914, item916)
		cond915 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions917 := xs914
	p.consumeLiteral(")")
	return abstractions917
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1676 := p.parse_relation_id()
	relation_id918 := _t1676
	xs919 := []*pb.Term{}
	cond920 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond920 {
		_t1677 := p.parse_term()
		item921 := _t1677
		xs919 = append(xs919, item921)
		cond920 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms922 := xs919
	p.consumeLiteral(")")
	_t1678 := &pb.Atom{Name: relation_id918, Terms: terms922}
	result924 := _t1678
	p.recordSpan(int(span_start923), "Atom")
	return result924
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start930 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1679 := p.parse_name()
	name925 := _t1679
	xs926 := []*pb.Term{}
	cond927 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond927 {
		_t1680 := p.parse_term()
		item928 := _t1680
		xs926 = append(xs926, item928)
		cond927 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms929 := xs926
	p.consumeLiteral(")")
	_t1681 := &pb.Pragma{Name: name925, Terms: terms929}
	result931 := _t1681
	p.recordSpan(int(span_start930), "Pragma")
	return result931
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start947 := int64(p.spanStart())
	var _t1682 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1683 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1683 = 9
		} else {
			var _t1684 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1684 = 4
			} else {
				var _t1685 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1685 = 3
				} else {
					var _t1686 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1686 = 0
					} else {
						var _t1687 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1687 = 2
						} else {
							var _t1688 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1688 = 1
							} else {
								var _t1689 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1689 = 8
								} else {
									var _t1690 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1690 = 6
									} else {
										var _t1691 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1691 = 5
										} else {
											var _t1692 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1692 = 7
											} else {
												_t1692 = -1
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
			}
			_t1683 = _t1684
		}
		_t1682 = _t1683
	} else {
		_t1682 = -1
	}
	prediction932 := _t1682
	var _t1693 *pb.Primitive
	if prediction932 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1694 := p.parse_name()
		name942 := _t1694
		xs943 := []*pb.RelTerm{}
		cond944 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond944 {
			_t1695 := p.parse_rel_term()
			item945 := _t1695
			xs943 = append(xs943, item945)
			cond944 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms946 := xs943
		p.consumeLiteral(")")
		_t1696 := &pb.Primitive{Name: name942, Terms: rel_terms946}
		_t1693 = _t1696
	} else {
		var _t1697 *pb.Primitive
		if prediction932 == 8 {
			_t1698 := p.parse_divide()
			divide941 := _t1698
			_t1697 = divide941
		} else {
			var _t1699 *pb.Primitive
			if prediction932 == 7 {
				_t1700 := p.parse_multiply()
				multiply940 := _t1700
				_t1699 = multiply940
			} else {
				var _t1701 *pb.Primitive
				if prediction932 == 6 {
					_t1702 := p.parse_minus()
					minus939 := _t1702
					_t1701 = minus939
				} else {
					var _t1703 *pb.Primitive
					if prediction932 == 5 {
						_t1704 := p.parse_add()
						add938 := _t1704
						_t1703 = add938
					} else {
						var _t1705 *pb.Primitive
						if prediction932 == 4 {
							_t1706 := p.parse_gt_eq()
							gt_eq937 := _t1706
							_t1705 = gt_eq937
						} else {
							var _t1707 *pb.Primitive
							if prediction932 == 3 {
								_t1708 := p.parse_gt()
								gt936 := _t1708
								_t1707 = gt936
							} else {
								var _t1709 *pb.Primitive
								if prediction932 == 2 {
									_t1710 := p.parse_lt_eq()
									lt_eq935 := _t1710
									_t1709 = lt_eq935
								} else {
									var _t1711 *pb.Primitive
									if prediction932 == 1 {
										_t1712 := p.parse_lt()
										lt934 := _t1712
										_t1711 = lt934
									} else {
										var _t1713 *pb.Primitive
										if prediction932 == 0 {
											_t1714 := p.parse_eq()
											eq933 := _t1714
											_t1713 = eq933
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1697 = _t1699
		}
		_t1693 = _t1697
	}
	result948 := _t1693
	p.recordSpan(int(span_start947), "Primitive")
	return result948
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start951 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1715 := p.parse_term()
	term949 := _t1715
	_t1716 := p.parse_term()
	term_3950 := _t1716
	p.consumeLiteral(")")
	_t1717 := &pb.RelTerm{}
	_t1717.RelTermType = &pb.RelTerm_Term{Term: term949}
	_t1718 := &pb.RelTerm{}
	_t1718.RelTermType = &pb.RelTerm_Term{Term: term_3950}
	_t1719 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1717, _t1718}}
	result952 := _t1719
	p.recordSpan(int(span_start951), "Primitive")
	return result952
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start955 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1720 := p.parse_term()
	term953 := _t1720
	_t1721 := p.parse_term()
	term_3954 := _t1721
	p.consumeLiteral(")")
	_t1722 := &pb.RelTerm{}
	_t1722.RelTermType = &pb.RelTerm_Term{Term: term953}
	_t1723 := &pb.RelTerm{}
	_t1723.RelTermType = &pb.RelTerm_Term{Term: term_3954}
	_t1724 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1722, _t1723}}
	result956 := _t1724
	p.recordSpan(int(span_start955), "Primitive")
	return result956
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start959 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1725 := p.parse_term()
	term957 := _t1725
	_t1726 := p.parse_term()
	term_3958 := _t1726
	p.consumeLiteral(")")
	_t1727 := &pb.RelTerm{}
	_t1727.RelTermType = &pb.RelTerm_Term{Term: term957}
	_t1728 := &pb.RelTerm{}
	_t1728.RelTermType = &pb.RelTerm_Term{Term: term_3958}
	_t1729 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1727, _t1728}}
	result960 := _t1729
	p.recordSpan(int(span_start959), "Primitive")
	return result960
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start963 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1730 := p.parse_term()
	term961 := _t1730
	_t1731 := p.parse_term()
	term_3962 := _t1731
	p.consumeLiteral(")")
	_t1732 := &pb.RelTerm{}
	_t1732.RelTermType = &pb.RelTerm_Term{Term: term961}
	_t1733 := &pb.RelTerm{}
	_t1733.RelTermType = &pb.RelTerm_Term{Term: term_3962}
	_t1734 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1732, _t1733}}
	result964 := _t1734
	p.recordSpan(int(span_start963), "Primitive")
	return result964
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start967 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1735 := p.parse_term()
	term965 := _t1735
	_t1736 := p.parse_term()
	term_3966 := _t1736
	p.consumeLiteral(")")
	_t1737 := &pb.RelTerm{}
	_t1737.RelTermType = &pb.RelTerm_Term{Term: term965}
	_t1738 := &pb.RelTerm{}
	_t1738.RelTermType = &pb.RelTerm_Term{Term: term_3966}
	_t1739 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1737, _t1738}}
	result968 := _t1739
	p.recordSpan(int(span_start967), "Primitive")
	return result968
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1740 := p.parse_term()
	term969 := _t1740
	_t1741 := p.parse_term()
	term_3970 := _t1741
	_t1742 := p.parse_term()
	term_4971 := _t1742
	p.consumeLiteral(")")
	_t1743 := &pb.RelTerm{}
	_t1743.RelTermType = &pb.RelTerm_Term{Term: term969}
	_t1744 := &pb.RelTerm{}
	_t1744.RelTermType = &pb.RelTerm_Term{Term: term_3970}
	_t1745 := &pb.RelTerm{}
	_t1745.RelTermType = &pb.RelTerm_Term{Term: term_4971}
	_t1746 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1743, _t1744, _t1745}}
	result973 := _t1746
	p.recordSpan(int(span_start972), "Primitive")
	return result973
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start977 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1747 := p.parse_term()
	term974 := _t1747
	_t1748 := p.parse_term()
	term_3975 := _t1748
	_t1749 := p.parse_term()
	term_4976 := _t1749
	p.consumeLiteral(")")
	_t1750 := &pb.RelTerm{}
	_t1750.RelTermType = &pb.RelTerm_Term{Term: term974}
	_t1751 := &pb.RelTerm{}
	_t1751.RelTermType = &pb.RelTerm_Term{Term: term_3975}
	_t1752 := &pb.RelTerm{}
	_t1752.RelTermType = &pb.RelTerm_Term{Term: term_4976}
	_t1753 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1750, _t1751, _t1752}}
	result978 := _t1753
	p.recordSpan(int(span_start977), "Primitive")
	return result978
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start982 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1754 := p.parse_term()
	term979 := _t1754
	_t1755 := p.parse_term()
	term_3980 := _t1755
	_t1756 := p.parse_term()
	term_4981 := _t1756
	p.consumeLiteral(")")
	_t1757 := &pb.RelTerm{}
	_t1757.RelTermType = &pb.RelTerm_Term{Term: term979}
	_t1758 := &pb.RelTerm{}
	_t1758.RelTermType = &pb.RelTerm_Term{Term: term_3980}
	_t1759 := &pb.RelTerm{}
	_t1759.RelTermType = &pb.RelTerm_Term{Term: term_4981}
	_t1760 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1757, _t1758, _t1759}}
	result983 := _t1760
	p.recordSpan(int(span_start982), "Primitive")
	return result983
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start987 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1761 := p.parse_term()
	term984 := _t1761
	_t1762 := p.parse_term()
	term_3985 := _t1762
	_t1763 := p.parse_term()
	term_4986 := _t1763
	p.consumeLiteral(")")
	_t1764 := &pb.RelTerm{}
	_t1764.RelTermType = &pb.RelTerm_Term{Term: term984}
	_t1765 := &pb.RelTerm{}
	_t1765.RelTermType = &pb.RelTerm_Term{Term: term_3985}
	_t1766 := &pb.RelTerm{}
	_t1766.RelTermType = &pb.RelTerm_Term{Term: term_4986}
	_t1767 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1764, _t1765, _t1766}}
	result988 := _t1767
	p.recordSpan(int(span_start987), "Primitive")
	return result988
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start992 := int64(p.spanStart())
	var _t1768 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1768 = 1
	} else {
		var _t1769 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1769 = 1
		} else {
			var _t1770 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1770 = 1
			} else {
				var _t1771 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1771 = 1
				} else {
					var _t1772 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1772 = 0
					} else {
						var _t1773 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1773 = 1
						} else {
							var _t1774 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1774 = 1
							} else {
								var _t1775 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1775 = 1
								} else {
									var _t1776 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1776 = 1
									} else {
										var _t1777 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1777 = 1
										} else {
											var _t1778 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1778 = 1
											} else {
												var _t1779 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1779 = 1
												} else {
													var _t1780 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1780 = 1
													} else {
														var _t1781 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1781 = 1
														} else {
															var _t1782 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1782 = 1
															} else {
																_t1782 = -1
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
			_t1769 = _t1770
		}
		_t1768 = _t1769
	}
	prediction989 := _t1768
	var _t1783 *pb.RelTerm
	if prediction989 == 1 {
		_t1784 := p.parse_term()
		term991 := _t1784
		_t1785 := &pb.RelTerm{}
		_t1785.RelTermType = &pb.RelTerm_Term{Term: term991}
		_t1783 = _t1785
	} else {
		var _t1786 *pb.RelTerm
		if prediction989 == 0 {
			_t1787 := p.parse_specialized_value()
			specialized_value990 := _t1787
			_t1788 := &pb.RelTerm{}
			_t1788.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value990}
			_t1786 = _t1788
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1783 = _t1786
	}
	result993 := _t1783
	p.recordSpan(int(span_start992), "RelTerm")
	return result993
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start995 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1789 := p.parse_raw_value()
	raw_value994 := _t1789
	result996 := raw_value994
	p.recordSpan(int(span_start995), "Value")
	return result996
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1790 := p.parse_name()
	name997 := _t1790
	xs998 := []*pb.RelTerm{}
	cond999 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond999 {
		_t1791 := p.parse_rel_term()
		item1000 := _t1791
		xs998 = append(xs998, item1000)
		cond999 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1001 := xs998
	p.consumeLiteral(")")
	_t1792 := &pb.RelAtom{Name: name997, Terms: rel_terms1001}
	result1003 := _t1792
	p.recordSpan(int(span_start1002), "RelAtom")
	return result1003
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1006 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1793 := p.parse_term()
	term1004 := _t1793
	_t1794 := p.parse_term()
	term_31005 := _t1794
	p.consumeLiteral(")")
	_t1795 := &pb.Cast{Input: term1004, Result: term_31005}
	result1007 := _t1795
	p.recordSpan(int(span_start1006), "Cast")
	return result1007
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1008 := []*pb.Attribute{}
	cond1009 := p.matchLookaheadLiteral("(", 0)
	for cond1009 {
		_t1796 := p.parse_attribute()
		item1010 := _t1796
		xs1008 = append(xs1008, item1010)
		cond1009 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1011 := xs1008
	p.consumeLiteral(")")
	return attributes1011
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1797 := p.parse_name()
	name1012 := _t1797
	xs1013 := []*pb.Value{}
	cond1014 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1014 {
		_t1798 := p.parse_raw_value()
		item1015 := _t1798
		xs1013 = append(xs1013, item1015)
		cond1014 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1016 := xs1013
	p.consumeLiteral(")")
	_t1799 := &pb.Attribute{Name: name1012, Args: raw_values1016}
	result1018 := _t1799
	p.recordSpan(int(span_start1017), "Attribute")
	return result1018
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1019 := []*pb.RelationId{}
	cond1020 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1020 {
		_t1800 := p.parse_relation_id()
		item1021 := _t1800
		xs1019 = append(xs1019, item1021)
		cond1020 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1022 := xs1019
	_t1801 := p.parse_script()
	script1023 := _t1801
	p.consumeLiteral(")")
	_t1802 := &pb.Algorithm{Global: relation_ids1022, Body: script1023}
	result1025 := _t1802
	p.recordSpan(int(span_start1024), "Algorithm")
	return result1025
}

func (p *Parser) parse_script() *pb.Script {
	span_start1030 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1026 := []*pb.Construct{}
	cond1027 := p.matchLookaheadLiteral("(", 0)
	for cond1027 {
		_t1803 := p.parse_construct()
		item1028 := _t1803
		xs1026 = append(xs1026, item1028)
		cond1027 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1029 := xs1026
	p.consumeLiteral(")")
	_t1804 := &pb.Script{Constructs: constructs1029}
	result1031 := _t1804
	p.recordSpan(int(span_start1030), "Script")
	return result1031
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1035 := int64(p.spanStart())
	var _t1805 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1806 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1806 = 1
		} else {
			var _t1807 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1807 = 1
			} else {
				var _t1808 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1808 = 1
				} else {
					var _t1809 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1809 = 0
					} else {
						var _t1810 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1810 = 1
						} else {
							var _t1811 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1811 = 1
							} else {
								_t1811 = -1
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
		_t1805 = _t1806
	} else {
		_t1805 = -1
	}
	prediction1032 := _t1805
	var _t1812 *pb.Construct
	if prediction1032 == 1 {
		_t1813 := p.parse_instruction()
		instruction1034 := _t1813
		_t1814 := &pb.Construct{}
		_t1814.ConstructType = &pb.Construct_Instruction{Instruction: instruction1034}
		_t1812 = _t1814
	} else {
		var _t1815 *pb.Construct
		if prediction1032 == 0 {
			_t1816 := p.parse_loop()
			loop1033 := _t1816
			_t1817 := &pb.Construct{}
			_t1817.ConstructType = &pb.Construct_Loop{Loop: loop1033}
			_t1815 = _t1817
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1812 = _t1815
	}
	result1036 := _t1812
	p.recordSpan(int(span_start1035), "Construct")
	return result1036
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1039 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1818 := p.parse_init()
	init1037 := _t1818
	_t1819 := p.parse_script()
	script1038 := _t1819
	p.consumeLiteral(")")
	_t1820 := &pb.Loop{Init: init1037, Body: script1038}
	result1040 := _t1820
	p.recordSpan(int(span_start1039), "Loop")
	return result1040
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1041 := []*pb.Instruction{}
	cond1042 := p.matchLookaheadLiteral("(", 0)
	for cond1042 {
		_t1821 := p.parse_instruction()
		item1043 := _t1821
		xs1041 = append(xs1041, item1043)
		cond1042 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1044 := xs1041
	p.consumeLiteral(")")
	return instructions1044
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1051 := int64(p.spanStart())
	var _t1822 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1823 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1823 = 1
		} else {
			var _t1824 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1824 = 4
			} else {
				var _t1825 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1825 = 3
				} else {
					var _t1826 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1826 = 2
					} else {
						var _t1827 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1827 = 0
						} else {
							_t1827 = -1
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
	prediction1045 := _t1822
	var _t1828 *pb.Instruction
	if prediction1045 == 4 {
		_t1829 := p.parse_monus_def()
		monus_def1050 := _t1829
		_t1830 := &pb.Instruction{}
		_t1830.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1050}
		_t1828 = _t1830
	} else {
		var _t1831 *pb.Instruction
		if prediction1045 == 3 {
			_t1832 := p.parse_monoid_def()
			monoid_def1049 := _t1832
			_t1833 := &pb.Instruction{}
			_t1833.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1049}
			_t1831 = _t1833
		} else {
			var _t1834 *pb.Instruction
			if prediction1045 == 2 {
				_t1835 := p.parse_break()
				break1048 := _t1835
				_t1836 := &pb.Instruction{}
				_t1836.InstrType = &pb.Instruction_Break{Break: break1048}
				_t1834 = _t1836
			} else {
				var _t1837 *pb.Instruction
				if prediction1045 == 1 {
					_t1838 := p.parse_upsert()
					upsert1047 := _t1838
					_t1839 := &pb.Instruction{}
					_t1839.InstrType = &pb.Instruction_Upsert{Upsert: upsert1047}
					_t1837 = _t1839
				} else {
					var _t1840 *pb.Instruction
					if prediction1045 == 0 {
						_t1841 := p.parse_assign()
						assign1046 := _t1841
						_t1842 := &pb.Instruction{}
						_t1842.InstrType = &pb.Instruction_Assign{Assign: assign1046}
						_t1840 = _t1842
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1837 = _t1840
				}
				_t1834 = _t1837
			}
			_t1831 = _t1834
		}
		_t1828 = _t1831
	}
	result1052 := _t1828
	p.recordSpan(int(span_start1051), "Instruction")
	return result1052
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1056 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1843 := p.parse_relation_id()
	relation_id1053 := _t1843
	_t1844 := p.parse_abstraction()
	abstraction1054 := _t1844
	var _t1845 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1846 := p.parse_attrs()
		_t1845 = _t1846
	}
	attrs1055 := _t1845
	p.consumeLiteral(")")
	_t1847 := attrs1055
	if attrs1055 == nil {
		_t1847 = []*pb.Attribute{}
	}
	_t1848 := &pb.Assign{Name: relation_id1053, Body: abstraction1054, Attrs: _t1847}
	result1057 := _t1848
	p.recordSpan(int(span_start1056), "Assign")
	return result1057
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1061 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1849 := p.parse_relation_id()
	relation_id1058 := _t1849
	_t1850 := p.parse_abstraction_with_arity()
	abstraction_with_arity1059 := _t1850
	var _t1851 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1852 := p.parse_attrs()
		_t1851 = _t1852
	}
	attrs1060 := _t1851
	p.consumeLiteral(")")
	_t1853 := attrs1060
	if attrs1060 == nil {
		_t1853 = []*pb.Attribute{}
	}
	_t1854 := &pb.Upsert{Name: relation_id1058, Body: abstraction_with_arity1059[0].(*pb.Abstraction), Attrs: _t1853, ValueArity: abstraction_with_arity1059[1].(int64)}
	result1062 := _t1854
	p.recordSpan(int(span_start1061), "Upsert")
	return result1062
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1855 := p.parse_bindings()
	bindings1063 := _t1855
	_t1856 := p.parse_formula()
	formula1064 := _t1856
	p.consumeLiteral(")")
	_t1857 := &pb.Abstraction{Vars: listConcat(bindings1063[0].([]*pb.Binding), bindings1063[1].([]*pb.Binding)), Value: formula1064}
	return []interface{}{_t1857, int64(len(bindings1063[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1858 := p.parse_relation_id()
	relation_id1065 := _t1858
	_t1859 := p.parse_abstraction()
	abstraction1066 := _t1859
	var _t1860 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1861 := p.parse_attrs()
		_t1860 = _t1861
	}
	attrs1067 := _t1860
	p.consumeLiteral(")")
	_t1862 := attrs1067
	if attrs1067 == nil {
		_t1862 = []*pb.Attribute{}
	}
	_t1863 := &pb.Break{Name: relation_id1065, Body: abstraction1066, Attrs: _t1862}
	result1069 := _t1863
	p.recordSpan(int(span_start1068), "Break")
	return result1069
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1864 := p.parse_monoid()
	monoid1070 := _t1864
	_t1865 := p.parse_relation_id()
	relation_id1071 := _t1865
	_t1866 := p.parse_abstraction_with_arity()
	abstraction_with_arity1072 := _t1866
	var _t1867 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1868 := p.parse_attrs()
		_t1867 = _t1868
	}
	attrs1073 := _t1867
	p.consumeLiteral(")")
	_t1869 := attrs1073
	if attrs1073 == nil {
		_t1869 = []*pb.Attribute{}
	}
	_t1870 := &pb.MonoidDef{Monoid: monoid1070, Name: relation_id1071, Body: abstraction_with_arity1072[0].(*pb.Abstraction), Attrs: _t1869, ValueArity: abstraction_with_arity1072[1].(int64)}
	result1075 := _t1870
	p.recordSpan(int(span_start1074), "MonoidDef")
	return result1075
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1081 := int64(p.spanStart())
	var _t1871 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1872 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1872 = 3
		} else {
			var _t1873 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1873 = 0
			} else {
				var _t1874 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1874 = 1
				} else {
					var _t1875 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1875 = 2
					} else {
						_t1875 = -1
					}
					_t1874 = _t1875
				}
				_t1873 = _t1874
			}
			_t1872 = _t1873
		}
		_t1871 = _t1872
	} else {
		_t1871 = -1
	}
	prediction1076 := _t1871
	var _t1876 *pb.Monoid
	if prediction1076 == 3 {
		_t1877 := p.parse_sum_monoid()
		sum_monoid1080 := _t1877
		_t1878 := &pb.Monoid{}
		_t1878.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1080}
		_t1876 = _t1878
	} else {
		var _t1879 *pb.Monoid
		if prediction1076 == 2 {
			_t1880 := p.parse_max_monoid()
			max_monoid1079 := _t1880
			_t1881 := &pb.Monoid{}
			_t1881.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1079}
			_t1879 = _t1881
		} else {
			var _t1882 *pb.Monoid
			if prediction1076 == 1 {
				_t1883 := p.parse_min_monoid()
				min_monoid1078 := _t1883
				_t1884 := &pb.Monoid{}
				_t1884.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1078}
				_t1882 = _t1884
			} else {
				var _t1885 *pb.Monoid
				if prediction1076 == 0 {
					_t1886 := p.parse_or_monoid()
					or_monoid1077 := _t1886
					_t1887 := &pb.Monoid{}
					_t1887.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1077}
					_t1885 = _t1887
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1882 = _t1885
			}
			_t1879 = _t1882
		}
		_t1876 = _t1879
	}
	result1082 := _t1876
	p.recordSpan(int(span_start1081), "Monoid")
	return result1082
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1083 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1888 := &pb.OrMonoid{}
	result1084 := _t1888
	p.recordSpan(int(span_start1083), "OrMonoid")
	return result1084
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1889 := p.parse_type()
	type1085 := _t1889
	p.consumeLiteral(")")
	_t1890 := &pb.MinMonoid{Type: type1085}
	result1087 := _t1890
	p.recordSpan(int(span_start1086), "MinMonoid")
	return result1087
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1089 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1891 := p.parse_type()
	type1088 := _t1891
	p.consumeLiteral(")")
	_t1892 := &pb.MaxMonoid{Type: type1088}
	result1090 := _t1892
	p.recordSpan(int(span_start1089), "MaxMonoid")
	return result1090
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1092 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1893 := p.parse_type()
	type1091 := _t1893
	p.consumeLiteral(")")
	_t1894 := &pb.SumMonoid{Type: type1091}
	result1093 := _t1894
	p.recordSpan(int(span_start1092), "SumMonoid")
	return result1093
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1098 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1895 := p.parse_monoid()
	monoid1094 := _t1895
	_t1896 := p.parse_relation_id()
	relation_id1095 := _t1896
	_t1897 := p.parse_abstraction_with_arity()
	abstraction_with_arity1096 := _t1897
	var _t1898 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1899 := p.parse_attrs()
		_t1898 = _t1899
	}
	attrs1097 := _t1898
	p.consumeLiteral(")")
	_t1900 := attrs1097
	if attrs1097 == nil {
		_t1900 = []*pb.Attribute{}
	}
	_t1901 := &pb.MonusDef{Monoid: monoid1094, Name: relation_id1095, Body: abstraction_with_arity1096[0].(*pb.Abstraction), Attrs: _t1900, ValueArity: abstraction_with_arity1096[1].(int64)}
	result1099 := _t1901
	p.recordSpan(int(span_start1098), "MonusDef")
	return result1099
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1902 := p.parse_relation_id()
	relation_id1100 := _t1902
	_t1903 := p.parse_abstraction()
	abstraction1101 := _t1903
	_t1904 := p.parse_functional_dependency_keys()
	functional_dependency_keys1102 := _t1904
	_t1905 := p.parse_functional_dependency_values()
	functional_dependency_values1103 := _t1905
	p.consumeLiteral(")")
	_t1906 := &pb.FunctionalDependency{Guard: abstraction1101, Keys: functional_dependency_keys1102, Values: functional_dependency_values1103}
	_t1907 := &pb.Constraint{Name: relation_id1100}
	_t1907.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1906}
	result1105 := _t1907
	p.recordSpan(int(span_start1104), "Constraint")
	return result1105
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1106 := []*pb.Var{}
	cond1107 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1107 {
		_t1908 := p.parse_var()
		item1108 := _t1908
		xs1106 = append(xs1106, item1108)
		cond1107 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1109 := xs1106
	p.consumeLiteral(")")
	return vars1109
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1110 := []*pb.Var{}
	cond1111 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1111 {
		_t1909 := p.parse_var()
		item1112 := _t1909
		xs1110 = append(xs1110, item1112)
		cond1111 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1113 := xs1110
	p.consumeLiteral(")")
	return vars1113
}

func (p *Parser) parse_data() *pb.Data {
	span_start1119 := int64(p.spanStart())
	var _t1910 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1911 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1911 = 3
		} else {
			var _t1912 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1912 = 0
			} else {
				var _t1913 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1913 = 2
				} else {
					var _t1914 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1914 = 1
					} else {
						_t1914 = -1
					}
					_t1913 = _t1914
				}
				_t1912 = _t1913
			}
			_t1911 = _t1912
		}
		_t1910 = _t1911
	} else {
		_t1910 = -1
	}
	prediction1114 := _t1910
	var _t1915 *pb.Data
	if prediction1114 == 3 {
		_t1916 := p.parse_iceberg_data()
		iceberg_data1118 := _t1916
		_t1917 := &pb.Data{}
		_t1917.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1118}
		_t1915 = _t1917
	} else {
		var _t1918 *pb.Data
		if prediction1114 == 2 {
			_t1919 := p.parse_csv_data()
			csv_data1117 := _t1919
			_t1920 := &pb.Data{}
			_t1920.DataType = &pb.Data_CsvData{CsvData: csv_data1117}
			_t1918 = _t1920
		} else {
			var _t1921 *pb.Data
			if prediction1114 == 1 {
				_t1922 := p.parse_betree_relation()
				betree_relation1116 := _t1922
				_t1923 := &pb.Data{}
				_t1923.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1116}
				_t1921 = _t1923
			} else {
				var _t1924 *pb.Data
				if prediction1114 == 0 {
					_t1925 := p.parse_edb()
					edb1115 := _t1925
					_t1926 := &pb.Data{}
					_t1926.DataType = &pb.Data_Edb{Edb: edb1115}
					_t1924 = _t1926
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1921 = _t1924
			}
			_t1918 = _t1921
		}
		_t1915 = _t1918
	}
	result1120 := _t1915
	p.recordSpan(int(span_start1119), "Data")
	return result1120
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1927 := p.parse_relation_id()
	relation_id1121 := _t1927
	_t1928 := p.parse_edb_path()
	edb_path1122 := _t1928
	_t1929 := p.parse_edb_types()
	edb_types1123 := _t1929
	p.consumeLiteral(")")
	_t1930 := &pb.EDB{TargetId: relation_id1121, Path: edb_path1122, Types: edb_types1123}
	result1125 := _t1930
	p.recordSpan(int(span_start1124), "EDB")
	return result1125
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1126 := []string{}
	cond1127 := p.matchLookaheadTerminal("STRING", 0)
	for cond1127 {
		item1128 := p.consumeTerminal("STRING").Value.str
		xs1126 = append(xs1126, item1128)
		cond1127 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1129 := xs1126
	p.consumeLiteral("]")
	return strings1129
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1130 := []*pb.Type{}
	cond1131 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1131 {
		_t1931 := p.parse_type()
		item1132 := _t1931
		xs1130 = append(xs1130, item1132)
		cond1131 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1133 := xs1130
	p.consumeLiteral("]")
	return types1133
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1136 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1932 := p.parse_relation_id()
	relation_id1134 := _t1932
	_t1933 := p.parse_betree_info()
	betree_info1135 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.BeTreeRelation{Name: relation_id1134, RelationInfo: betree_info1135}
	result1137 := _t1934
	p.recordSpan(int(span_start1136), "BeTreeRelation")
	return result1137
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1141 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1935 := p.parse_betree_info_key_types()
	betree_info_key_types1138 := _t1935
	_t1936 := p.parse_betree_info_value_types()
	betree_info_value_types1139 := _t1936
	_t1937 := p.parse_config_dict()
	config_dict1140 := _t1937
	p.consumeLiteral(")")
	_t1938 := p.construct_betree_info(betree_info_key_types1138, betree_info_value_types1139, config_dict1140)
	result1142 := _t1938
	p.recordSpan(int(span_start1141), "BeTreeInfo")
	return result1142
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1143 := []*pb.Type{}
	cond1144 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1144 {
		_t1939 := p.parse_type()
		item1145 := _t1939
		xs1143 = append(xs1143, item1145)
		cond1144 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1146 := xs1143
	p.consumeLiteral(")")
	return types1146
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1147 := []*pb.Type{}
	cond1148 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1148 {
		_t1940 := p.parse_type()
		item1149 := _t1940
		xs1147 = append(xs1147, item1149)
		cond1148 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1150 := xs1147
	p.consumeLiteral(")")
	return types1150
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1941 := p.parse_csvlocator()
	csvlocator1151 := _t1941
	_t1942 := p.parse_csv_config()
	csv_config1152 := _t1942
	_t1943 := p.parse_gnf_columns()
	gnf_columns1153 := _t1943
	_t1944 := p.parse_csv_asof()
	csv_asof1154 := _t1944
	p.consumeLiteral(")")
	_t1945 := &pb.CSVData{Locator: csvlocator1151, Config: csv_config1152, Columns: gnf_columns1153, Asof: csv_asof1154}
	result1156 := _t1945
	p.recordSpan(int(span_start1155), "CSVData")
	return result1156
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1159 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1946 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1947 := p.parse_csv_locator_paths()
		_t1946 = _t1947
	}
	csv_locator_paths1157 := _t1946
	var _t1948 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1949 := p.parse_csv_locator_inline_data()
		_t1948 = ptr(_t1949)
	}
	csv_locator_inline_data1158 := _t1948
	p.consumeLiteral(")")
	_t1950 := csv_locator_paths1157
	if csv_locator_paths1157 == nil {
		_t1950 = []string{}
	}
	_t1951 := &pb.CSVLocator{Paths: _t1950, InlineData: []byte(deref(csv_locator_inline_data1158, ""))}
	result1160 := _t1951
	p.recordSpan(int(span_start1159), "CSVLocator")
	return result1160
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1161 := []string{}
	cond1162 := p.matchLookaheadTerminal("STRING", 0)
	for cond1162 {
		item1163 := p.consumeTerminal("STRING").Value.str
		xs1161 = append(xs1161, item1163)
		cond1162 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1164 := xs1161
	p.consumeLiteral(")")
	return strings1164
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1165 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1165
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1167 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1952 := p.parse_config_dict()
	config_dict1166 := _t1952
	p.consumeLiteral(")")
	_t1953 := p.construct_csv_config(config_dict1166)
	result1168 := _t1953
	p.recordSpan(int(span_start1167), "CSVConfig")
	return result1168
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1169 := []*pb.GNFColumn{}
	cond1170 := p.matchLookaheadLiteral("(", 0)
	for cond1170 {
		_t1954 := p.parse_gnf_column()
		item1171 := _t1954
		xs1169 = append(xs1169, item1171)
		cond1170 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1172 := xs1169
	p.consumeLiteral(")")
	return gnf_columns1172
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1179 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1955 := p.parse_gnf_column_path()
	gnf_column_path1173 := _t1955
	var _t1956 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1957 := p.parse_relation_id()
		_t1956 = _t1957
	}
	relation_id1174 := _t1956
	p.consumeLiteral("[")
	xs1175 := []*pb.Type{}
	cond1176 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1176 {
		_t1958 := p.parse_type()
		item1177 := _t1958
		xs1175 = append(xs1175, item1177)
		cond1176 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1178 := xs1175
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1959 := &pb.GNFColumn{ColumnPath: gnf_column_path1173, TargetId: relation_id1174, Types: types1178}
	result1180 := _t1959
	p.recordSpan(int(span_start1179), "GNFColumn")
	return result1180
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1960 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1960 = 1
	} else {
		var _t1961 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1961 = 0
		} else {
			_t1961 = -1
		}
		_t1960 = _t1961
	}
	prediction1181 := _t1960
	var _t1962 []string
	if prediction1181 == 1 {
		p.consumeLiteral("[")
		xs1183 := []string{}
		cond1184 := p.matchLookaheadTerminal("STRING", 0)
		for cond1184 {
			item1185 := p.consumeTerminal("STRING").Value.str
			xs1183 = append(xs1183, item1185)
			cond1184 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1186 := xs1183
		p.consumeLiteral("]")
		_t1962 = strings1186
	} else {
		var _t1963 []string
		if prediction1181 == 0 {
			string1182 := p.consumeTerminal("STRING").Value.str
			_ = string1182
			_t1963 = []string{string1182}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1962 = _t1963
	}
	return _t1962
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1187 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1187
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1192 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1964 := p.parse_iceberg_locator()
	iceberg_locator1188 := _t1964
	_t1965 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1189 := _t1965
	_t1966 := p.parse_gnf_columns()
	gnf_columns1190 := _t1966
	_t1967 := p.parse_boolean_value()
	boolean_value1191 := _t1967
	p.consumeLiteral(")")
	_t1968 := &pb.IcebergData{Locator: iceberg_locator1188, Config: iceberg_catalog_config1189, Columns: gnf_columns1190, ReturnsDelta: boolean_value1191}
	result1193 := _t1968
	p.recordSpan(int(span_start1192), "IcebergData")
	return result1193
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1202 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1194 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1195 := []string{}
	cond1196 := p.matchLookaheadTerminal("STRING", 0)
	for cond1196 {
		item1197 := p.consumeTerminal("STRING").Value.str
		xs1195 = append(xs1195, item1197)
		cond1196 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1198 := xs1195
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121199 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1969 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1970 := p.parse_iceberg_from_snapshot()
		_t1969 = ptr(_t1970)
	}
	iceberg_from_snapshot1200 := _t1969
	var _t1971 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1972 := p.parse_iceberg_to_snapshot()
		_t1971 = ptr(_t1972)
	}
	iceberg_to_snapshot1201 := _t1971
	p.consumeLiteral(")")
	_t1973 := p.construct_iceberg_locator(string1194, strings1198, string_121199, iceberg_from_snapshot1200, iceberg_to_snapshot1201)
	result1203 := _t1973
	p.recordSpan(int(span_start1202), "IcebergLocator")
	return result1203
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1204 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1204
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1205 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1205
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1216 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1206 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1974 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1975 := p.parse_iceberg_catalog_config_scope()
		_t1974 = ptr(_t1975)
	}
	iceberg_catalog_config_scope1207 := _t1974
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1208 := [][]interface{}{}
	cond1209 := p.matchLookaheadLiteral("(", 0)
	for cond1209 {
		_t1976 := p.parse_iceberg_property_entry()
		item1210 := _t1976
		xs1208 = append(xs1208, item1210)
		cond1209 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1211 := xs1208
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1212 := [][]interface{}{}
	cond1213 := p.matchLookaheadLiteral("(", 0)
	for cond1213 {
		_t1977 := p.parse_iceberg_property_entry()
		item1214 := _t1977
		xs1212 = append(xs1212, item1214)
		cond1213 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys_131215 := xs1212
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1978 := p.construct_iceberg_catalog_config(string1206, iceberg_catalog_config_scope1207, iceberg_property_entrys1211, iceberg_property_entrys_131215)
	result1217 := _t1978
	p.recordSpan(int(span_start1216), "IcebergCatalogConfig")
	return result1217
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1218 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1218
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1219 := p.consumeTerminal("STRING").Value.str
	string_31220 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1219, string_31220}
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1222 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1979 := p.parse_fragment_id()
	fragment_id1221 := _t1979
	p.consumeLiteral(")")
	_t1980 := &pb.Undefine{FragmentId: fragment_id1221}
	result1223 := _t1980
	p.recordSpan(int(span_start1222), "Undefine")
	return result1223
}

func (p *Parser) parse_context() *pb.Context {
	span_start1228 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1224 := []*pb.RelationId{}
	cond1225 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1225 {
		_t1981 := p.parse_relation_id()
		item1226 := _t1981
		xs1224 = append(xs1224, item1226)
		cond1225 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1227 := xs1224
	p.consumeLiteral(")")
	_t1982 := &pb.Context{Relations: relation_ids1227}
	result1229 := _t1982
	p.recordSpan(int(span_start1228), "Context")
	return result1229
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1234 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1230 := []*pb.SnapshotMapping{}
	cond1231 := p.matchLookaheadLiteral("[", 0)
	for cond1231 {
		_t1983 := p.parse_snapshot_mapping()
		item1232 := _t1983
		xs1230 = append(xs1230, item1232)
		cond1231 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1233 := xs1230
	p.consumeLiteral(")")
	_t1984 := &pb.Snapshot{Mappings: snapshot_mappings1233}
	result1235 := _t1984
	p.recordSpan(int(span_start1234), "Snapshot")
	return result1235
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1238 := int64(p.spanStart())
	_t1985 := p.parse_edb_path()
	edb_path1236 := _t1985
	_t1986 := p.parse_relation_id()
	relation_id1237 := _t1986
	_t1987 := &pb.SnapshotMapping{DestinationPath: edb_path1236, SourceRelation: relation_id1237}
	result1239 := _t1987
	p.recordSpan(int(span_start1238), "SnapshotMapping")
	return result1239
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1240 := []*pb.Read{}
	cond1241 := p.matchLookaheadLiteral("(", 0)
	for cond1241 {
		_t1988 := p.parse_read()
		item1242 := _t1988
		xs1240 = append(xs1240, item1242)
		cond1241 = p.matchLookaheadLiteral("(", 0)
	}
	reads1243 := xs1240
	p.consumeLiteral(")")
	return reads1243
}

func (p *Parser) parse_read() *pb.Read {
	span_start1250 := int64(p.spanStart())
	var _t1989 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1990 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1990 = 2
		} else {
			var _t1991 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1991 = 1
			} else {
				var _t1992 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1992 = 4
				} else {
					var _t1993 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1993 = 4
					} else {
						var _t1994 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1994 = 0
						} else {
							var _t1995 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1995 = 3
							} else {
								_t1995 = -1
							}
							_t1994 = _t1995
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
	} else {
		_t1989 = -1
	}
	prediction1244 := _t1989
	var _t1996 *pb.Read
	if prediction1244 == 4 {
		_t1997 := p.parse_export()
		export1249 := _t1997
		_t1998 := &pb.Read{}
		_t1998.ReadType = &pb.Read_Export{Export: export1249}
		_t1996 = _t1998
	} else {
		var _t1999 *pb.Read
		if prediction1244 == 3 {
			_t2000 := p.parse_abort()
			abort1248 := _t2000
			_t2001 := &pb.Read{}
			_t2001.ReadType = &pb.Read_Abort{Abort: abort1248}
			_t1999 = _t2001
		} else {
			var _t2002 *pb.Read
			if prediction1244 == 2 {
				_t2003 := p.parse_what_if()
				what_if1247 := _t2003
				_t2004 := &pb.Read{}
				_t2004.ReadType = &pb.Read_WhatIf{WhatIf: what_if1247}
				_t2002 = _t2004
			} else {
				var _t2005 *pb.Read
				if prediction1244 == 1 {
					_t2006 := p.parse_output()
					output1246 := _t2006
					_t2007 := &pb.Read{}
					_t2007.ReadType = &pb.Read_Output{Output: output1246}
					_t2005 = _t2007
				} else {
					var _t2008 *pb.Read
					if prediction1244 == 0 {
						_t2009 := p.parse_demand()
						demand1245 := _t2009
						_t2010 := &pb.Read{}
						_t2010.ReadType = &pb.Read_Demand{Demand: demand1245}
						_t2008 = _t2010
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2005 = _t2008
				}
				_t2002 = _t2005
			}
			_t1999 = _t2002
		}
		_t1996 = _t1999
	}
	result1251 := _t1996
	p.recordSpan(int(span_start1250), "Read")
	return result1251
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1253 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2011 := p.parse_relation_id()
	relation_id1252 := _t2011
	p.consumeLiteral(")")
	_t2012 := &pb.Demand{RelationId: relation_id1252}
	result1254 := _t2012
	p.recordSpan(int(span_start1253), "Demand")
	return result1254
}

func (p *Parser) parse_output() *pb.Output {
	span_start1257 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2013 := p.parse_name()
	name1255 := _t2013
	_t2014 := p.parse_relation_id()
	relation_id1256 := _t2014
	p.consumeLiteral(")")
	_t2015 := &pb.Output{Name: name1255, RelationId: relation_id1256}
	result1258 := _t2015
	p.recordSpan(int(span_start1257), "Output")
	return result1258
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1261 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2016 := p.parse_name()
	name1259 := _t2016
	_t2017 := p.parse_epoch()
	epoch1260 := _t2017
	p.consumeLiteral(")")
	_t2018 := &pb.WhatIf{Branch: name1259, Epoch: epoch1260}
	result1262 := _t2018
	p.recordSpan(int(span_start1261), "WhatIf")
	return result1262
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1265 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2019 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2020 := p.parse_name()
		_t2019 = ptr(_t2020)
	}
	name1263 := _t2019
	_t2021 := p.parse_relation_id()
	relation_id1264 := _t2021
	p.consumeLiteral(")")
	_t2022 := &pb.Abort{Name: deref(name1263, "abort"), RelationId: relation_id1264}
	result1266 := _t2022
	p.recordSpan(int(span_start1265), "Abort")
	return result1266
}

func (p *Parser) parse_export() *pb.Export {
	span_start1270 := int64(p.spanStart())
	var _t2023 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2024 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2024 = 1
		} else {
			var _t2025 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2025 = 0
			} else {
				_t2025 = -1
			}
			_t2024 = _t2025
		}
		_t2023 = _t2024
	} else {
		_t2023 = -1
	}
	prediction1267 := _t2023
	var _t2026 *pb.Export
	if prediction1267 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2027 := p.parse_export_iceberg_config()
		export_iceberg_config1269 := _t2027
		p.consumeLiteral(")")
		_t2028 := &pb.Export{}
		_t2028.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1269}
		_t2026 = _t2028
	} else {
		var _t2029 *pb.Export
		if prediction1267 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2030 := p.parse_export_csv_config()
			export_csv_config1268 := _t2030
			p.consumeLiteral(")")
			_t2031 := &pb.Export{}
			_t2031.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1268}
			_t2029 = _t2031
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2026 = _t2029
	}
	result1271 := _t2026
	p.recordSpan(int(span_start1270), "Export")
	return result1271
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1279 := int64(p.spanStart())
	var _t2032 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2033 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2033 = 0
		} else {
			var _t2034 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2034 = 1
			} else {
				_t2034 = -1
			}
			_t2033 = _t2034
		}
		_t2032 = _t2033
	} else {
		_t2032 = -1
	}
	prediction1272 := _t2032
	var _t2035 *pb.ExportCSVConfig
	if prediction1272 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2036 := p.parse_export_csv_path()
		export_csv_path1276 := _t2036
		_t2037 := p.parse_export_csv_columns_list()
		export_csv_columns_list1277 := _t2037
		_t2038 := p.parse_config_dict()
		config_dict1278 := _t2038
		p.consumeLiteral(")")
		_t2039 := p.construct_export_csv_config(export_csv_path1276, export_csv_columns_list1277, config_dict1278)
		_t2035 = _t2039
	} else {
		var _t2040 *pb.ExportCSVConfig
		if prediction1272 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2041 := p.parse_export_csv_path()
			export_csv_path1273 := _t2041
			_t2042 := p.parse_export_csv_source()
			export_csv_source1274 := _t2042
			_t2043 := p.parse_csv_config()
			csv_config1275 := _t2043
			p.consumeLiteral(")")
			_t2044 := p.construct_export_csv_config_with_source(export_csv_path1273, export_csv_source1274, csv_config1275)
			_t2040 = _t2044
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2035 = _t2040
	}
	result1280 := _t2035
	p.recordSpan(int(span_start1279), "ExportCSVConfig")
	return result1280
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1281 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1281
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1288 := int64(p.spanStart())
	var _t2045 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2046 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2046 = 1
		} else {
			var _t2047 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2047 = 0
			} else {
				_t2047 = -1
			}
			_t2046 = _t2047
		}
		_t2045 = _t2046
	} else {
		_t2045 = -1
	}
	prediction1282 := _t2045
	var _t2048 *pb.ExportCSVSource
	if prediction1282 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2049 := p.parse_relation_id()
		relation_id1287 := _t2049
		p.consumeLiteral(")")
		_t2050 := &pb.ExportCSVSource{}
		_t2050.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1287}
		_t2048 = _t2050
	} else {
		var _t2051 *pb.ExportCSVSource
		if prediction1282 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1283 := []*pb.ExportCSVColumn{}
			cond1284 := p.matchLookaheadLiteral("(", 0)
			for cond1284 {
				_t2052 := p.parse_export_csv_column()
				item1285 := _t2052
				xs1283 = append(xs1283, item1285)
				cond1284 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1286 := xs1283
			p.consumeLiteral(")")
			_t2053 := &pb.ExportCSVColumns{Columns: export_csv_columns1286}
			_t2054 := &pb.ExportCSVSource{}
			_t2054.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2053}
			_t2051 = _t2054
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2048 = _t2051
	}
	result1289 := _t2048
	p.recordSpan(int(span_start1288), "ExportCSVSource")
	return result1289
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1292 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1290 := p.consumeTerminal("STRING").Value.str
	_t2055 := p.parse_relation_id()
	relation_id1291 := _t2055
	p.consumeLiteral(")")
	_t2056 := &pb.ExportCSVColumn{ColumnName: string1290, ColumnData: relation_id1291}
	result1293 := _t2056
	p.recordSpan(int(span_start1292), "ExportCSVColumn")
	return result1293
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1294 := []*pb.ExportCSVColumn{}
	cond1295 := p.matchLookaheadLiteral("(", 0)
	for cond1295 {
		_t2057 := p.parse_export_csv_column()
		item1296 := _t2057
		xs1294 = append(xs1294, item1296)
		cond1295 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1297 := xs1294
	p.consumeLiteral(")")
	return export_csv_columns1297
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1310 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2058 := p.parse_iceberg_locator()
	iceberg_locator1298 := _t2058
	_t2059 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1299 := _t2059
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2060 := p.parse_relation_id()
	relation_id1300 := _t2060
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1301 := []*pb.ExportGNFColumn{}
	cond1302 := p.matchLookaheadLiteral("(", 0)
	for cond1302 {
		_t2061 := p.parse_export_gnf_column()
		item1303 := _t2061
		xs1301 = append(xs1301, item1303)
		cond1302 = p.matchLookaheadLiteral("(", 0)
	}
	export_gnf_columns1304 := xs1301
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1305 := [][]interface{}{}
	cond1306 := p.matchLookaheadLiteral("(", 0)
	for cond1306 {
		_t2062 := p.parse_iceberg_property_entry()
		item1307 := _t2062
		xs1305 = append(xs1305, item1307)
		cond1306 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1308 := xs1305
	p.consumeLiteral(")")
	var _t2063 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2064 := p.parse_config_dict()
		_t2063 = _t2064
	}
	config_dict1309 := _t2063
	p.consumeLiteral(")")
	_t2065 := p.construct_export_iceberg_config_full(iceberg_locator1298, iceberg_catalog_config1299, relation_id1300, export_gnf_columns1304, iceberg_property_entrys1308, config_dict1309)
	result1311 := _t2065
	p.recordSpan(int(span_start1310), "ExportIcebergConfig")
	return result1311
}

func (p *Parser) parse_export_gnf_column() *pb.ExportGNFColumn {
	span_start1314 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("gnf_column")
	string1312 := p.consumeTerminal("STRING").Value.str
	_t2066 := p.parse_boolean_value()
	boolean_value1313 := _t2066
	p.consumeLiteral(")")
	_t2067 := &pb.ExportGNFColumn{Name: string1312, Nullable: boolean_value1313}
	result1315 := _t2067
	p.recordSpan(int(span_start1314), "ExportGNFColumn")
	return result1315
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
