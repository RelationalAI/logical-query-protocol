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
	var _t2072 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t2072
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t2073 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t2073
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t2074 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t2074
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t2075 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t2075
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t2076 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t2076
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t2077 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t2077
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t2078 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t2078
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t2079 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t2079
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t2080 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t2080
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t2081 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t2081
	_t2082 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t2082
	_t2083 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t2083
	_t2084 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t2084
	_t2085 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t2085
	_t2086 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t2086
	_t2087 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t2087
	_t2088 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t2088
	_t2089 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t2089
	_t2090 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t2090
	_t2091 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t2091
	_t2092 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t2092
	_t2093 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t2093
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t2094 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t2094
	_t2095 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t2095
	_t2096 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t2096
	_t2097 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t2097
	_t2098 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t2098
	_t2099 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t2099
	_t2100 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t2100
	_t2101 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2101
	_t2102 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2102
	_t2103 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2103.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2103.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2103
	_t2104 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2104
}

func (p *Parser) default_configure() *pb.Configure {
	_t2105 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2105
	_t2106 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2106
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
	_t2107 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2107
	_t2108 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2108
	_t2109 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2109
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2110 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2110
	_t2111 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2111
	_t2112 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2112
	_t2113 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2113
	_t2114 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2114
	_t2115 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2115
	_t2116 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2116
	_t2117 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2117
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2118 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2118
}

func (p *Parser) construct_iceberg_catalog_config(catalog_uri string, scope_opt *string, property_pairs [][]interface{}, auth_property_pairs [][]interface{}) *pb.IcebergCatalogConfig {
	props := stringMapFromPairs(property_pairs)
	auth_props := stringMapFromPairs(auth_property_pairs)
	_t2119 := &pb.IcebergCatalogConfig{CatalogUri: catalog_uri, Scope: ptr(deref(scope_opt, "")), Properties: props, AuthProperties: auth_props}
	return _t2119
}

func (p *Parser) construct_iceberg_locator(table_name string, namespace []string, warehouse string, from_snapshot_opt *string, to_snapshot_opt *string) *pb.IcebergLocator {
	_t2120 := &pb.IcebergLocator{TableName: table_name, Namespace: namespace, Warehouse: warehouse, FromSnapshot: ptr(deref(from_snapshot_opt, "")), ToSnapshot: ptr(deref(to_snapshot_opt, ""))}
	return _t2120
}

func (p *Parser) construct_export_iceberg_config_full(locator *pb.IcebergLocator, config *pb.IcebergCatalogConfig, table_def *pb.RelationId, columns []*pb.ExportGNFColumn, table_property_pairs [][]interface{}, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	_t2121 := config_dict
	if config_dict == nil {
		_t2121 = [][]interface{}{}
	}
	cfg := dictFromList(_t2121)
	_t2122 := p._extract_value_string(dictGetValue(cfg, "prefix"), "")
	prefix := _t2122
	_t2123 := p._extract_value_int64(dictGetValue(cfg, "target_file_size_bytes"), 0)
	target_file_size_bytes := _t2123
	_t2124 := p._extract_value_string(dictGetValue(cfg, "compression"), "")
	compression := _t2124
	table_props := stringMapFromPairs(table_property_pairs)
	_t2125 := &pb.ExportIcebergConfig{Locator: locator, Config: config, TableDef: table_def, Columns: columns, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression, TableProperties: table_props}
	return _t2125
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start666 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1320 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1321 := p.parse_configure()
		_t1320 = _t1321
	}
	configure660 := _t1320
	var _t1322 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1323 := p.parse_sync()
		_t1322 = _t1323
	}
	sync661 := _t1322
	xs662 := []*pb.Epoch{}
	cond663 := p.matchLookaheadLiteral("(", 0)
	for cond663 {
		_t1324 := p.parse_epoch()
		item664 := _t1324
		xs662 = append(xs662, item664)
		cond663 = p.matchLookaheadLiteral("(", 0)
	}
	epochs665 := xs662
	p.consumeLiteral(")")
	_t1325 := p.default_configure()
	_t1326 := configure660
	if configure660 == nil {
		_t1326 = _t1325
	}
	_t1327 := &pb.Transaction{Epochs: epochs665, Configure: _t1326, Sync: sync661}
	result667 := _t1327
	p.recordSpan(int(span_start666), "Transaction")
	return result667
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start669 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1328 := p.parse_config_dict()
	config_dict668 := _t1328
	p.consumeLiteral(")")
	_t1329 := p.construct_configure(config_dict668)
	result670 := _t1329
	p.recordSpan(int(span_start669), "Configure")
	return result670
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs671 := [][]interface{}{}
	cond672 := p.matchLookaheadLiteral(":", 0)
	for cond672 {
		_t1330 := p.parse_config_key_value()
		item673 := _t1330
		xs671 = append(xs671, item673)
		cond672 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values674 := xs671
	p.consumeLiteral("}")
	return config_key_values674
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol675 := p.consumeTerminal("SYMBOL").Value.str
	_t1331 := p.parse_raw_value()
	raw_value676 := _t1331
	return []interface{}{symbol675, raw_value676}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start690 := int64(p.spanStart())
	var _t1332 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1332 = 12
	} else {
		var _t1333 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1333 = 11
		} else {
			var _t1334 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1334 = 12
			} else {
				var _t1335 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1336 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1336 = 1
					} else {
						var _t1337 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1337 = 0
						} else {
							_t1337 = -1
						}
						_t1336 = _t1337
					}
					_t1335 = _t1336
				} else {
					var _t1338 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1338 = 7
					} else {
						var _t1339 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1339 = 8
						} else {
							var _t1340 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1340 = 2
							} else {
								var _t1341 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1341 = 3
								} else {
									var _t1342 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1342 = 9
									} else {
										var _t1343 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1343 = 4
										} else {
											var _t1344 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1344 = 5
											} else {
												var _t1345 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1345 = 6
												} else {
													var _t1346 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1346 = 10
													} else {
														_t1346 = -1
													}
													_t1345 = _t1346
												}
												_t1344 = _t1345
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
					_t1335 = _t1338
				}
				_t1334 = _t1335
			}
			_t1333 = _t1334
		}
		_t1332 = _t1333
	}
	prediction677 := _t1332
	var _t1347 *pb.Value
	if prediction677 == 12 {
		_t1348 := p.parse_boolean_value()
		boolean_value689 := _t1348
		_t1349 := &pb.Value{}
		_t1349.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value689}
		_t1347 = _t1349
	} else {
		var _t1350 *pb.Value
		if prediction677 == 11 {
			p.consumeLiteral("missing")
			_t1351 := &pb.MissingValue{}
			_t1352 := &pb.Value{}
			_t1352.Value = &pb.Value_MissingValue{MissingValue: _t1351}
			_t1350 = _t1352
		} else {
			var _t1353 *pb.Value
			if prediction677 == 10 {
				decimal688 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1354 := &pb.Value{}
				_t1354.Value = &pb.Value_DecimalValue{DecimalValue: decimal688}
				_t1353 = _t1354
			} else {
				var _t1355 *pb.Value
				if prediction677 == 9 {
					int128687 := p.consumeTerminal("INT128").Value.int128
					_t1356 := &pb.Value{}
					_t1356.Value = &pb.Value_Int128Value{Int128Value: int128687}
					_t1355 = _t1356
				} else {
					var _t1357 *pb.Value
					if prediction677 == 8 {
						uint128686 := p.consumeTerminal("UINT128").Value.uint128
						_t1358 := &pb.Value{}
						_t1358.Value = &pb.Value_Uint128Value{Uint128Value: uint128686}
						_t1357 = _t1358
					} else {
						var _t1359 *pb.Value
						if prediction677 == 7 {
							uint32685 := p.consumeTerminal("UINT32").Value.u32
							_t1360 := &pb.Value{}
							_t1360.Value = &pb.Value_Uint32Value{Uint32Value: uint32685}
							_t1359 = _t1360
						} else {
							var _t1361 *pb.Value
							if prediction677 == 6 {
								float684 := p.consumeTerminal("FLOAT").Value.f64
								_t1362 := &pb.Value{}
								_t1362.Value = &pb.Value_FloatValue{FloatValue: float684}
								_t1361 = _t1362
							} else {
								var _t1363 *pb.Value
								if prediction677 == 5 {
									float32683 := p.consumeTerminal("FLOAT32").Value.f32
									_t1364 := &pb.Value{}
									_t1364.Value = &pb.Value_Float32Value{Float32Value: float32683}
									_t1363 = _t1364
								} else {
									var _t1365 *pb.Value
									if prediction677 == 4 {
										int682 := p.consumeTerminal("INT").Value.i64
										_t1366 := &pb.Value{}
										_t1366.Value = &pb.Value_IntValue{IntValue: int682}
										_t1365 = _t1366
									} else {
										var _t1367 *pb.Value
										if prediction677 == 3 {
											int32681 := p.consumeTerminal("INT32").Value.i32
											_t1368 := &pb.Value{}
											_t1368.Value = &pb.Value_Int32Value{Int32Value: int32681}
											_t1367 = _t1368
										} else {
											var _t1369 *pb.Value
											if prediction677 == 2 {
												string680 := p.consumeTerminal("STRING").Value.str
												_t1370 := &pb.Value{}
												_t1370.Value = &pb.Value_StringValue{StringValue: string680}
												_t1369 = _t1370
											} else {
												var _t1371 *pb.Value
												if prediction677 == 1 {
													_t1372 := p.parse_raw_datetime()
													raw_datetime679 := _t1372
													_t1373 := &pb.Value{}
													_t1373.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime679}
													_t1371 = _t1373
												} else {
													var _t1374 *pb.Value
													if prediction677 == 0 {
														_t1375 := p.parse_raw_date()
														raw_date678 := _t1375
														_t1376 := &pb.Value{}
														_t1376.Value = &pb.Value_DateValue{DateValue: raw_date678}
														_t1374 = _t1376
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1371 = _t1374
												}
												_t1369 = _t1371
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
			_t1350 = _t1353
		}
		_t1347 = _t1350
	}
	result691 := _t1347
	p.recordSpan(int(span_start690), "Value")
	return result691
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start695 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int692 := p.consumeTerminal("INT").Value.i64
	int_3693 := p.consumeTerminal("INT").Value.i64
	int_4694 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1377 := &pb.DateValue{Year: int32(int692), Month: int32(int_3693), Day: int32(int_4694)}
	result696 := _t1377
	p.recordSpan(int(span_start695), "DateValue")
	return result696
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start704 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int697 := p.consumeTerminal("INT").Value.i64
	int_3698 := p.consumeTerminal("INT").Value.i64
	int_4699 := p.consumeTerminal("INT").Value.i64
	int_5700 := p.consumeTerminal("INT").Value.i64
	int_6701 := p.consumeTerminal("INT").Value.i64
	int_7702 := p.consumeTerminal("INT").Value.i64
	var _t1378 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1378 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8703 := _t1378
	p.consumeLiteral(")")
	_t1379 := &pb.DateTimeValue{Year: int32(int697), Month: int32(int_3698), Day: int32(int_4699), Hour: int32(int_5700), Minute: int32(int_6701), Second: int32(int_7702), Microsecond: int32(deref(int_8703, 0))}
	result705 := _t1379
	p.recordSpan(int(span_start704), "DateTimeValue")
	return result705
}

func (p *Parser) parse_boolean_value() bool {
	var _t1380 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1380 = 0
	} else {
		var _t1381 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1381 = 1
		} else {
			_t1381 = -1
		}
		_t1380 = _t1381
	}
	prediction706 := _t1380
	var _t1382 bool
	if prediction706 == 1 {
		p.consumeLiteral("false")
		_t1382 = false
	} else {
		var _t1383 bool
		if prediction706 == 0 {
			p.consumeLiteral("true")
			_t1383 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1382 = _t1383
	}
	return _t1382
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs707 := []*pb.FragmentId{}
	cond708 := p.matchLookaheadLiteral(":", 0)
	for cond708 {
		_t1384 := p.parse_fragment_id()
		item709 := _t1384
		xs707 = append(xs707, item709)
		cond708 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids710 := xs707
	p.consumeLiteral(")")
	_t1385 := &pb.Sync{Fragments: fragment_ids710}
	result712 := _t1385
	p.recordSpan(int(span_start711), "Sync")
	return result712
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start714 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol713 := p.consumeTerminal("SYMBOL").Value.str
	result715 := &pb.FragmentId{Id: []byte(symbol713)}
	p.recordSpan(int(span_start714), "FragmentId")
	return result715
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start718 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1386 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1387 := p.parse_epoch_writes()
		_t1386 = _t1387
	}
	epoch_writes716 := _t1386
	var _t1388 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1389 := p.parse_epoch_reads()
		_t1388 = _t1389
	}
	epoch_reads717 := _t1388
	p.consumeLiteral(")")
	_t1390 := epoch_writes716
	if epoch_writes716 == nil {
		_t1390 = []*pb.Write{}
	}
	_t1391 := epoch_reads717
	if epoch_reads717 == nil {
		_t1391 = []*pb.Read{}
	}
	_t1392 := &pb.Epoch{Writes: _t1390, Reads: _t1391}
	result719 := _t1392
	p.recordSpan(int(span_start718), "Epoch")
	return result719
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs720 := []*pb.Write{}
	cond721 := p.matchLookaheadLiteral("(", 0)
	for cond721 {
		_t1393 := p.parse_write()
		item722 := _t1393
		xs720 = append(xs720, item722)
		cond721 = p.matchLookaheadLiteral("(", 0)
	}
	writes723 := xs720
	p.consumeLiteral(")")
	return writes723
}

func (p *Parser) parse_write() *pb.Write {
	span_start729 := int64(p.spanStart())
	var _t1394 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1395 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1395 = 1
		} else {
			var _t1396 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1396 = 3
			} else {
				var _t1397 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1397 = 0
				} else {
					var _t1398 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1398 = 2
					} else {
						_t1398 = -1
					}
					_t1397 = _t1398
				}
				_t1396 = _t1397
			}
			_t1395 = _t1396
		}
		_t1394 = _t1395
	} else {
		_t1394 = -1
	}
	prediction724 := _t1394
	var _t1399 *pb.Write
	if prediction724 == 3 {
		_t1400 := p.parse_snapshot()
		snapshot728 := _t1400
		_t1401 := &pb.Write{}
		_t1401.WriteType = &pb.Write_Snapshot{Snapshot: snapshot728}
		_t1399 = _t1401
	} else {
		var _t1402 *pb.Write
		if prediction724 == 2 {
			_t1403 := p.parse_context()
			context727 := _t1403
			_t1404 := &pb.Write{}
			_t1404.WriteType = &pb.Write_Context{Context: context727}
			_t1402 = _t1404
		} else {
			var _t1405 *pb.Write
			if prediction724 == 1 {
				_t1406 := p.parse_undefine()
				undefine726 := _t1406
				_t1407 := &pb.Write{}
				_t1407.WriteType = &pb.Write_Undefine{Undefine: undefine726}
				_t1405 = _t1407
			} else {
				var _t1408 *pb.Write
				if prediction724 == 0 {
					_t1409 := p.parse_define()
					define725 := _t1409
					_t1410 := &pb.Write{}
					_t1410.WriteType = &pb.Write_Define{Define: define725}
					_t1408 = _t1410
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1405 = _t1408
			}
			_t1402 = _t1405
		}
		_t1399 = _t1402
	}
	result730 := _t1399
	p.recordSpan(int(span_start729), "Write")
	return result730
}

func (p *Parser) parse_define() *pb.Define {
	span_start732 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1411 := p.parse_fragment()
	fragment731 := _t1411
	p.consumeLiteral(")")
	_t1412 := &pb.Define{Fragment: fragment731}
	result733 := _t1412
	p.recordSpan(int(span_start732), "Define")
	return result733
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1413 := p.parse_new_fragment_id()
	new_fragment_id734 := _t1413
	xs735 := []*pb.Declaration{}
	cond736 := p.matchLookaheadLiteral("(", 0)
	for cond736 {
		_t1414 := p.parse_declaration()
		item737 := _t1414
		xs735 = append(xs735, item737)
		cond736 = p.matchLookaheadLiteral("(", 0)
	}
	declarations738 := xs735
	p.consumeLiteral(")")
	result740 := p.constructFragment(new_fragment_id734, declarations738)
	p.recordSpan(int(span_start739), "Fragment")
	return result740
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start742 := int64(p.spanStart())
	_t1415 := p.parse_fragment_id()
	fragment_id741 := _t1415
	p.startFragment(fragment_id741)
	result743 := fragment_id741
	p.recordSpan(int(span_start742), "FragmentId")
	return result743
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start749 := int64(p.spanStart())
	var _t1416 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1417 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1417 = 3
		} else {
			var _t1418 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1418 = 2
			} else {
				var _t1419 int64
				if p.matchLookaheadLiteral("edb", 1) {
					_t1419 = 3
				} else {
					var _t1420 int64
					if p.matchLookaheadLiteral("def", 1) {
						_t1420 = 0
					} else {
						var _t1421 int64
						if p.matchLookaheadLiteral("csv_data", 1) {
							_t1421 = 3
						} else {
							var _t1422 int64
							if p.matchLookaheadLiteral("betree_relation", 1) {
								_t1422 = 3
							} else {
								var _t1423 int64
								if p.matchLookaheadLiteral("algorithm", 1) {
									_t1423 = 1
								} else {
									_t1423 = -1
								}
								_t1422 = _t1423
							}
							_t1421 = _t1422
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
	} else {
		_t1416 = -1
	}
	prediction744 := _t1416
	var _t1424 *pb.Declaration
	if prediction744 == 3 {
		_t1425 := p.parse_data()
		data748 := _t1425
		_t1426 := &pb.Declaration{}
		_t1426.DeclarationType = &pb.Declaration_Data{Data: data748}
		_t1424 = _t1426
	} else {
		var _t1427 *pb.Declaration
		if prediction744 == 2 {
			_t1428 := p.parse_constraint()
			constraint747 := _t1428
			_t1429 := &pb.Declaration{}
			_t1429.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint747}
			_t1427 = _t1429
		} else {
			var _t1430 *pb.Declaration
			if prediction744 == 1 {
				_t1431 := p.parse_algorithm()
				algorithm746 := _t1431
				_t1432 := &pb.Declaration{}
				_t1432.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm746}
				_t1430 = _t1432
			} else {
				var _t1433 *pb.Declaration
				if prediction744 == 0 {
					_t1434 := p.parse_def()
					def745 := _t1434
					_t1435 := &pb.Declaration{}
					_t1435.DeclarationType = &pb.Declaration_Def{Def: def745}
					_t1433 = _t1435
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1430 = _t1433
			}
			_t1427 = _t1430
		}
		_t1424 = _t1427
	}
	result750 := _t1424
	p.recordSpan(int(span_start749), "Declaration")
	return result750
}

func (p *Parser) parse_def() *pb.Def {
	span_start754 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1436 := p.parse_relation_id()
	relation_id751 := _t1436
	_t1437 := p.parse_abstraction()
	abstraction752 := _t1437
	var _t1438 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1439 := p.parse_attrs()
		_t1438 = _t1439
	}
	attrs753 := _t1438
	p.consumeLiteral(")")
	_t1440 := attrs753
	if attrs753 == nil {
		_t1440 = []*pb.Attribute{}
	}
	_t1441 := &pb.Def{Name: relation_id751, Body: abstraction752, Attrs: _t1440}
	result755 := _t1441
	p.recordSpan(int(span_start754), "Def")
	return result755
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start759 := int64(p.spanStart())
	var _t1442 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1442 = 0
	} else {
		var _t1443 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1443 = 1
		} else {
			_t1443 = -1
		}
		_t1442 = _t1443
	}
	prediction756 := _t1442
	var _t1444 *pb.RelationId
	if prediction756 == 1 {
		uint128758 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128758
		_t1444 = &pb.RelationId{IdLow: uint128758.Low, IdHigh: uint128758.High}
	} else {
		var _t1445 *pb.RelationId
		if prediction756 == 0 {
			p.consumeLiteral(":")
			symbol757 := p.consumeTerminal("SYMBOL").Value.str
			_t1445 = p.relationIdFromString(symbol757)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1444 = _t1445
	}
	result760 := _t1444
	p.recordSpan(int(span_start759), "RelationId")
	return result760
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1446 := p.parse_bindings()
	bindings761 := _t1446
	_t1447 := p.parse_formula()
	formula762 := _t1447
	p.consumeLiteral(")")
	_t1448 := &pb.Abstraction{Vars: listConcat(bindings761[0].([]*pb.Binding), bindings761[1].([]*pb.Binding)), Value: formula762}
	result764 := _t1448
	p.recordSpan(int(span_start763), "Abstraction")
	return result764
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs765 := []*pb.Binding{}
	cond766 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond766 {
		_t1449 := p.parse_binding()
		item767 := _t1449
		xs765 = append(xs765, item767)
		cond766 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings768 := xs765
	var _t1450 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1451 := p.parse_value_bindings()
		_t1450 = _t1451
	}
	value_bindings769 := _t1450
	p.consumeLiteral("]")
	_t1452 := value_bindings769
	if value_bindings769 == nil {
		_t1452 = []*pb.Binding{}
	}
	return []interface{}{bindings768, _t1452}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start772 := int64(p.spanStart())
	symbol770 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1453 := p.parse_type()
	type771 := _t1453
	_t1454 := &pb.Var{Name: symbol770}
	_t1455 := &pb.Binding{Var: _t1454, Type: type771}
	result773 := _t1455
	p.recordSpan(int(span_start772), "Binding")
	return result773
}

func (p *Parser) parse_type() *pb.Type {
	span_start789 := int64(p.spanStart())
	var _t1456 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1456 = 0
	} else {
		var _t1457 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1457 = 13
		} else {
			var _t1458 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1458 = 4
			} else {
				var _t1459 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1459 = 1
				} else {
					var _t1460 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1460 = 8
					} else {
						var _t1461 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1461 = 11
						} else {
							var _t1462 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1462 = 5
							} else {
								var _t1463 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1463 = 2
								} else {
									var _t1464 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1464 = 12
									} else {
										var _t1465 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1465 = 3
										} else {
											var _t1466 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1466 = 7
											} else {
												var _t1467 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1467 = 6
												} else {
													var _t1468 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1468 = 10
													} else {
														var _t1469 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1469 = 9
														} else {
															_t1469 = -1
														}
														_t1468 = _t1469
													}
													_t1467 = _t1468
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
	prediction774 := _t1456
	var _t1470 *pb.Type
	if prediction774 == 13 {
		_t1471 := p.parse_uint32_type()
		uint32_type788 := _t1471
		_t1472 := &pb.Type{}
		_t1472.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type788}
		_t1470 = _t1472
	} else {
		var _t1473 *pb.Type
		if prediction774 == 12 {
			_t1474 := p.parse_float32_type()
			float32_type787 := _t1474
			_t1475 := &pb.Type{}
			_t1475.Type = &pb.Type_Float32Type{Float32Type: float32_type787}
			_t1473 = _t1475
		} else {
			var _t1476 *pb.Type
			if prediction774 == 11 {
				_t1477 := p.parse_int32_type()
				int32_type786 := _t1477
				_t1478 := &pb.Type{}
				_t1478.Type = &pb.Type_Int32Type{Int32Type: int32_type786}
				_t1476 = _t1478
			} else {
				var _t1479 *pb.Type
				if prediction774 == 10 {
					_t1480 := p.parse_boolean_type()
					boolean_type785 := _t1480
					_t1481 := &pb.Type{}
					_t1481.Type = &pb.Type_BooleanType{BooleanType: boolean_type785}
					_t1479 = _t1481
				} else {
					var _t1482 *pb.Type
					if prediction774 == 9 {
						_t1483 := p.parse_decimal_type()
						decimal_type784 := _t1483
						_t1484 := &pb.Type{}
						_t1484.Type = &pb.Type_DecimalType{DecimalType: decimal_type784}
						_t1482 = _t1484
					} else {
						var _t1485 *pb.Type
						if prediction774 == 8 {
							_t1486 := p.parse_missing_type()
							missing_type783 := _t1486
							_t1487 := &pb.Type{}
							_t1487.Type = &pb.Type_MissingType{MissingType: missing_type783}
							_t1485 = _t1487
						} else {
							var _t1488 *pb.Type
							if prediction774 == 7 {
								_t1489 := p.parse_datetime_type()
								datetime_type782 := _t1489
								_t1490 := &pb.Type{}
								_t1490.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type782}
								_t1488 = _t1490
							} else {
								var _t1491 *pb.Type
								if prediction774 == 6 {
									_t1492 := p.parse_date_type()
									date_type781 := _t1492
									_t1493 := &pb.Type{}
									_t1493.Type = &pb.Type_DateType{DateType: date_type781}
									_t1491 = _t1493
								} else {
									var _t1494 *pb.Type
									if prediction774 == 5 {
										_t1495 := p.parse_int128_type()
										int128_type780 := _t1495
										_t1496 := &pb.Type{}
										_t1496.Type = &pb.Type_Int128Type{Int128Type: int128_type780}
										_t1494 = _t1496
									} else {
										var _t1497 *pb.Type
										if prediction774 == 4 {
											_t1498 := p.parse_uint128_type()
											uint128_type779 := _t1498
											_t1499 := &pb.Type{}
											_t1499.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type779}
											_t1497 = _t1499
										} else {
											var _t1500 *pb.Type
											if prediction774 == 3 {
												_t1501 := p.parse_float_type()
												float_type778 := _t1501
												_t1502 := &pb.Type{}
												_t1502.Type = &pb.Type_FloatType{FloatType: float_type778}
												_t1500 = _t1502
											} else {
												var _t1503 *pb.Type
												if prediction774 == 2 {
													_t1504 := p.parse_int_type()
													int_type777 := _t1504
													_t1505 := &pb.Type{}
													_t1505.Type = &pb.Type_IntType{IntType: int_type777}
													_t1503 = _t1505
												} else {
													var _t1506 *pb.Type
													if prediction774 == 1 {
														_t1507 := p.parse_string_type()
														string_type776 := _t1507
														_t1508 := &pb.Type{}
														_t1508.Type = &pb.Type_StringType{StringType: string_type776}
														_t1506 = _t1508
													} else {
														var _t1509 *pb.Type
														if prediction774 == 0 {
															_t1510 := p.parse_unspecified_type()
															unspecified_type775 := _t1510
															_t1511 := &pb.Type{}
															_t1511.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type775}
															_t1509 = _t1511
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
									_t1491 = _t1494
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
	result790 := _t1470
	p.recordSpan(int(span_start789), "Type")
	return result790
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1512 := &pb.UnspecifiedType{}
	result792 := _t1512
	p.recordSpan(int(span_start791), "UnspecifiedType")
	return result792
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start793 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1513 := &pb.StringType{}
	result794 := _t1513
	p.recordSpan(int(span_start793), "StringType")
	return result794
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start795 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1514 := &pb.IntType{}
	result796 := _t1514
	p.recordSpan(int(span_start795), "IntType")
	return result796
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1515 := &pb.FloatType{}
	result798 := _t1515
	p.recordSpan(int(span_start797), "FloatType")
	return result798
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start799 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1516 := &pb.UInt128Type{}
	result800 := _t1516
	p.recordSpan(int(span_start799), "UInt128Type")
	return result800
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1517 := &pb.Int128Type{}
	result802 := _t1517
	p.recordSpan(int(span_start801), "Int128Type")
	return result802
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1518 := &pb.DateType{}
	result804 := _t1518
	p.recordSpan(int(span_start803), "DateType")
	return result804
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1519 := &pb.DateTimeType{}
	result806 := _t1519
	p.recordSpan(int(span_start805), "DateTimeType")
	return result806
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1520 := &pb.MissingType{}
	result808 := _t1520
	p.recordSpan(int(span_start807), "MissingType")
	return result808
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start811 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int809 := p.consumeTerminal("INT").Value.i64
	int_3810 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1521 := &pb.DecimalType{Precision: int32(int809), Scale: int32(int_3810)}
	result812 := _t1521
	p.recordSpan(int(span_start811), "DecimalType")
	return result812
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1522 := &pb.BooleanType{}
	result814 := _t1522
	p.recordSpan(int(span_start813), "BooleanType")
	return result814
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start815 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1523 := &pb.Int32Type{}
	result816 := _t1523
	p.recordSpan(int(span_start815), "Int32Type")
	return result816
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1524 := &pb.Float32Type{}
	result818 := _t1524
	p.recordSpan(int(span_start817), "Float32Type")
	return result818
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1525 := &pb.UInt32Type{}
	result820 := _t1525
	p.recordSpan(int(span_start819), "UInt32Type")
	return result820
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs821 := []*pb.Binding{}
	cond822 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond822 {
		_t1526 := p.parse_binding()
		item823 := _t1526
		xs821 = append(xs821, item823)
		cond822 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings824 := xs821
	return bindings824
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start839 := int64(p.spanStart())
	var _t1527 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1528 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1528 = 0
		} else {
			var _t1529 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1529 = 11
			} else {
				var _t1530 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1530 = 3
				} else {
					var _t1531 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1531 = 10
					} else {
						var _t1532 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1532 = 9
						} else {
							var _t1533 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1533 = 5
							} else {
								var _t1534 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1534 = 6
								} else {
									var _t1535 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1535 = 7
									} else {
										var _t1536 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1536 = 1
										} else {
											var _t1537 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1537 = 2
											} else {
												var _t1538 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1538 = 12
												} else {
													var _t1539 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1539 = 8
													} else {
														var _t1540 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1540 = 4
														} else {
															var _t1541 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1541 = 10
															} else {
																var _t1542 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1542 = 10
																} else {
																	var _t1543 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1543 = 10
																	} else {
																		var _t1544 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1544 = 10
																		} else {
																			var _t1545 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1545 = 10
																			} else {
																				var _t1546 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1546 = 10
																				} else {
																					var _t1547 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1547 = 10
																					} else {
																						var _t1548 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1548 = 10
																						} else {
																							var _t1549 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1549 = 10
																							} else {
																								_t1549 = -1
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
	} else {
		_t1527 = -1
	}
	prediction825 := _t1527
	var _t1550 *pb.Formula
	if prediction825 == 12 {
		_t1551 := p.parse_cast()
		cast838 := _t1551
		_t1552 := &pb.Formula{}
		_t1552.FormulaType = &pb.Formula_Cast{Cast: cast838}
		_t1550 = _t1552
	} else {
		var _t1553 *pb.Formula
		if prediction825 == 11 {
			_t1554 := p.parse_rel_atom()
			rel_atom837 := _t1554
			_t1555 := &pb.Formula{}
			_t1555.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom837}
			_t1553 = _t1555
		} else {
			var _t1556 *pb.Formula
			if prediction825 == 10 {
				_t1557 := p.parse_primitive()
				primitive836 := _t1557
				_t1558 := &pb.Formula{}
				_t1558.FormulaType = &pb.Formula_Primitive{Primitive: primitive836}
				_t1556 = _t1558
			} else {
				var _t1559 *pb.Formula
				if prediction825 == 9 {
					_t1560 := p.parse_pragma()
					pragma835 := _t1560
					_t1561 := &pb.Formula{}
					_t1561.FormulaType = &pb.Formula_Pragma{Pragma: pragma835}
					_t1559 = _t1561
				} else {
					var _t1562 *pb.Formula
					if prediction825 == 8 {
						_t1563 := p.parse_atom()
						atom834 := _t1563
						_t1564 := &pb.Formula{}
						_t1564.FormulaType = &pb.Formula_Atom{Atom: atom834}
						_t1562 = _t1564
					} else {
						var _t1565 *pb.Formula
						if prediction825 == 7 {
							_t1566 := p.parse_ffi()
							ffi833 := _t1566
							_t1567 := &pb.Formula{}
							_t1567.FormulaType = &pb.Formula_Ffi{Ffi: ffi833}
							_t1565 = _t1567
						} else {
							var _t1568 *pb.Formula
							if prediction825 == 6 {
								_t1569 := p.parse_not()
								not832 := _t1569
								_t1570 := &pb.Formula{}
								_t1570.FormulaType = &pb.Formula_Not{Not: not832}
								_t1568 = _t1570
							} else {
								var _t1571 *pb.Formula
								if prediction825 == 5 {
									_t1572 := p.parse_disjunction()
									disjunction831 := _t1572
									_t1573 := &pb.Formula{}
									_t1573.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction831}
									_t1571 = _t1573
								} else {
									var _t1574 *pb.Formula
									if prediction825 == 4 {
										_t1575 := p.parse_conjunction()
										conjunction830 := _t1575
										_t1576 := &pb.Formula{}
										_t1576.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction830}
										_t1574 = _t1576
									} else {
										var _t1577 *pb.Formula
										if prediction825 == 3 {
											_t1578 := p.parse_reduce()
											reduce829 := _t1578
											_t1579 := &pb.Formula{}
											_t1579.FormulaType = &pb.Formula_Reduce{Reduce: reduce829}
											_t1577 = _t1579
										} else {
											var _t1580 *pb.Formula
											if prediction825 == 2 {
												_t1581 := p.parse_exists()
												exists828 := _t1581
												_t1582 := &pb.Formula{}
												_t1582.FormulaType = &pb.Formula_Exists{Exists: exists828}
												_t1580 = _t1582
											} else {
												var _t1583 *pb.Formula
												if prediction825 == 1 {
													_t1584 := p.parse_false()
													false827 := _t1584
													_t1585 := &pb.Formula{}
													_t1585.FormulaType = &pb.Formula_Disjunction{Disjunction: false827}
													_t1583 = _t1585
												} else {
													var _t1586 *pb.Formula
													if prediction825 == 0 {
														_t1587 := p.parse_true()
														true826 := _t1587
														_t1588 := &pb.Formula{}
														_t1588.FormulaType = &pb.Formula_Conjunction{Conjunction: true826}
														_t1586 = _t1588
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1583 = _t1586
												}
												_t1580 = _t1583
											}
											_t1577 = _t1580
										}
										_t1574 = _t1577
									}
									_t1571 = _t1574
								}
								_t1568 = _t1571
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
	result840 := _t1550
	p.recordSpan(int(span_start839), "Formula")
	return result840
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1589 := &pb.Conjunction{Args: []*pb.Formula{}}
	result842 := _t1589
	p.recordSpan(int(span_start841), "Conjunction")
	return result842
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1590 := &pb.Disjunction{Args: []*pb.Formula{}}
	result844 := _t1590
	p.recordSpan(int(span_start843), "Disjunction")
	return result844
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1591 := p.parse_bindings()
	bindings845 := _t1591
	_t1592 := p.parse_formula()
	formula846 := _t1592
	p.consumeLiteral(")")
	_t1593 := &pb.Abstraction{Vars: listConcat(bindings845[0].([]*pb.Binding), bindings845[1].([]*pb.Binding)), Value: formula846}
	_t1594 := &pb.Exists{Body: _t1593}
	result848 := _t1594
	p.recordSpan(int(span_start847), "Exists")
	return result848
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1595 := p.parse_abstraction()
	abstraction849 := _t1595
	_t1596 := p.parse_abstraction()
	abstraction_3850 := _t1596
	_t1597 := p.parse_terms()
	terms851 := _t1597
	p.consumeLiteral(")")
	_t1598 := &pb.Reduce{Op: abstraction849, Body: abstraction_3850, Terms: terms851}
	result853 := _t1598
	p.recordSpan(int(span_start852), "Reduce")
	return result853
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs854 := []*pb.Term{}
	cond855 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond855 {
		_t1599 := p.parse_term()
		item856 := _t1599
		xs854 = append(xs854, item856)
		cond855 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms857 := xs854
	p.consumeLiteral(")")
	return terms857
}

func (p *Parser) parse_term() *pb.Term {
	span_start861 := int64(p.spanStart())
	var _t1600 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1600 = 1
	} else {
		var _t1601 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1601 = 1
		} else {
			var _t1602 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1602 = 1
			} else {
				var _t1603 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1603 = 1
				} else {
					var _t1604 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1604 = 0
					} else {
						var _t1605 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1605 = 1
						} else {
							var _t1606 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1606 = 1
							} else {
								var _t1607 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1607 = 1
								} else {
									var _t1608 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1608 = 1
									} else {
										var _t1609 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1609 = 1
										} else {
											var _t1610 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1610 = 1
											} else {
												var _t1611 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1611 = 1
												} else {
													var _t1612 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1612 = 1
													} else {
														var _t1613 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1613 = 1
														} else {
															_t1613 = -1
														}
														_t1612 = _t1613
													}
													_t1611 = _t1612
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
	prediction858 := _t1600
	var _t1614 *pb.Term
	if prediction858 == 1 {
		_t1615 := p.parse_value()
		value860 := _t1615
		_t1616 := &pb.Term{}
		_t1616.TermType = &pb.Term_Constant{Constant: value860}
		_t1614 = _t1616
	} else {
		var _t1617 *pb.Term
		if prediction858 == 0 {
			_t1618 := p.parse_var()
			var859 := _t1618
			_t1619 := &pb.Term{}
			_t1619.TermType = &pb.Term_Var{Var: var859}
			_t1617 = _t1619
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1614 = _t1617
	}
	result862 := _t1614
	p.recordSpan(int(span_start861), "Term")
	return result862
}

func (p *Parser) parse_var() *pb.Var {
	span_start864 := int64(p.spanStart())
	symbol863 := p.consumeTerminal("SYMBOL").Value.str
	_t1620 := &pb.Var{Name: symbol863}
	result865 := _t1620
	p.recordSpan(int(span_start864), "Var")
	return result865
}

func (p *Parser) parse_value() *pb.Value {
	span_start879 := int64(p.spanStart())
	var _t1621 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1621 = 12
	} else {
		var _t1622 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1622 = 11
		} else {
			var _t1623 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1623 = 12
			} else {
				var _t1624 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1625 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1625 = 1
					} else {
						var _t1626 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1626 = 0
						} else {
							_t1626 = -1
						}
						_t1625 = _t1626
					}
					_t1624 = _t1625
				} else {
					var _t1627 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1627 = 7
					} else {
						var _t1628 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1628 = 8
						} else {
							var _t1629 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1629 = 2
							} else {
								var _t1630 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1630 = 3
								} else {
									var _t1631 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1631 = 9
									} else {
										var _t1632 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1632 = 4
										} else {
											var _t1633 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1633 = 5
											} else {
												var _t1634 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1634 = 6
												} else {
													var _t1635 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1635 = 10
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
					_t1624 = _t1627
				}
				_t1623 = _t1624
			}
			_t1622 = _t1623
		}
		_t1621 = _t1622
	}
	prediction866 := _t1621
	var _t1636 *pb.Value
	if prediction866 == 12 {
		_t1637 := p.parse_boolean_value()
		boolean_value878 := _t1637
		_t1638 := &pb.Value{}
		_t1638.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value878}
		_t1636 = _t1638
	} else {
		var _t1639 *pb.Value
		if prediction866 == 11 {
			p.consumeLiteral("missing")
			_t1640 := &pb.MissingValue{}
			_t1641 := &pb.Value{}
			_t1641.Value = &pb.Value_MissingValue{MissingValue: _t1640}
			_t1639 = _t1641
		} else {
			var _t1642 *pb.Value
			if prediction866 == 10 {
				formatted_decimal877 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1643 := &pb.Value{}
				_t1643.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal877}
				_t1642 = _t1643
			} else {
				var _t1644 *pb.Value
				if prediction866 == 9 {
					formatted_int128876 := p.consumeTerminal("INT128").Value.int128
					_t1645 := &pb.Value{}
					_t1645.Value = &pb.Value_Int128Value{Int128Value: formatted_int128876}
					_t1644 = _t1645
				} else {
					var _t1646 *pb.Value
					if prediction866 == 8 {
						formatted_uint128875 := p.consumeTerminal("UINT128").Value.uint128
						_t1647 := &pb.Value{}
						_t1647.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128875}
						_t1646 = _t1647
					} else {
						var _t1648 *pb.Value
						if prediction866 == 7 {
							formatted_uint32874 := p.consumeTerminal("UINT32").Value.u32
							_t1649 := &pb.Value{}
							_t1649.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32874}
							_t1648 = _t1649
						} else {
							var _t1650 *pb.Value
							if prediction866 == 6 {
								formatted_float873 := p.consumeTerminal("FLOAT").Value.f64
								_t1651 := &pb.Value{}
								_t1651.Value = &pb.Value_FloatValue{FloatValue: formatted_float873}
								_t1650 = _t1651
							} else {
								var _t1652 *pb.Value
								if prediction866 == 5 {
									formatted_float32872 := p.consumeTerminal("FLOAT32").Value.f32
									_t1653 := &pb.Value{}
									_t1653.Value = &pb.Value_Float32Value{Float32Value: formatted_float32872}
									_t1652 = _t1653
								} else {
									var _t1654 *pb.Value
									if prediction866 == 4 {
										formatted_int871 := p.consumeTerminal("INT").Value.i64
										_t1655 := &pb.Value{}
										_t1655.Value = &pb.Value_IntValue{IntValue: formatted_int871}
										_t1654 = _t1655
									} else {
										var _t1656 *pb.Value
										if prediction866 == 3 {
											formatted_int32870 := p.consumeTerminal("INT32").Value.i32
											_t1657 := &pb.Value{}
											_t1657.Value = &pb.Value_Int32Value{Int32Value: formatted_int32870}
											_t1656 = _t1657
										} else {
											var _t1658 *pb.Value
											if prediction866 == 2 {
												formatted_string869 := p.consumeTerminal("STRING").Value.str
												_t1659 := &pb.Value{}
												_t1659.Value = &pb.Value_StringValue{StringValue: formatted_string869}
												_t1658 = _t1659
											} else {
												var _t1660 *pb.Value
												if prediction866 == 1 {
													_t1661 := p.parse_datetime()
													datetime868 := _t1661
													_t1662 := &pb.Value{}
													_t1662.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime868}
													_t1660 = _t1662
												} else {
													var _t1663 *pb.Value
													if prediction866 == 0 {
														_t1664 := p.parse_date()
														date867 := _t1664
														_t1665 := &pb.Value{}
														_t1665.Value = &pb.Value_DateValue{DateValue: date867}
														_t1663 = _t1665
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1660 = _t1663
												}
												_t1658 = _t1660
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
			_t1639 = _t1642
		}
		_t1636 = _t1639
	}
	result880 := _t1636
	p.recordSpan(int(span_start879), "Value")
	return result880
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start884 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int881 := p.consumeTerminal("INT").Value.i64
	formatted_int_3882 := p.consumeTerminal("INT").Value.i64
	formatted_int_4883 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1666 := &pb.DateValue{Year: int32(formatted_int881), Month: int32(formatted_int_3882), Day: int32(formatted_int_4883)}
	result885 := _t1666
	p.recordSpan(int(span_start884), "DateValue")
	return result885
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start893 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int886 := p.consumeTerminal("INT").Value.i64
	formatted_int_3887 := p.consumeTerminal("INT").Value.i64
	formatted_int_4888 := p.consumeTerminal("INT").Value.i64
	formatted_int_5889 := p.consumeTerminal("INT").Value.i64
	formatted_int_6890 := p.consumeTerminal("INT").Value.i64
	formatted_int_7891 := p.consumeTerminal("INT").Value.i64
	var _t1667 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1667 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8892 := _t1667
	p.consumeLiteral(")")
	_t1668 := &pb.DateTimeValue{Year: int32(formatted_int886), Month: int32(formatted_int_3887), Day: int32(formatted_int_4888), Hour: int32(formatted_int_5889), Minute: int32(formatted_int_6890), Second: int32(formatted_int_7891), Microsecond: int32(deref(formatted_int_8892, 0))}
	result894 := _t1668
	p.recordSpan(int(span_start893), "DateTimeValue")
	return result894
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs895 := []*pb.Formula{}
	cond896 := p.matchLookaheadLiteral("(", 0)
	for cond896 {
		_t1669 := p.parse_formula()
		item897 := _t1669
		xs895 = append(xs895, item897)
		cond896 = p.matchLookaheadLiteral("(", 0)
	}
	formulas898 := xs895
	p.consumeLiteral(")")
	_t1670 := &pb.Conjunction{Args: formulas898}
	result900 := _t1670
	p.recordSpan(int(span_start899), "Conjunction")
	return result900
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start905 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs901 := []*pb.Formula{}
	cond902 := p.matchLookaheadLiteral("(", 0)
	for cond902 {
		_t1671 := p.parse_formula()
		item903 := _t1671
		xs901 = append(xs901, item903)
		cond902 = p.matchLookaheadLiteral("(", 0)
	}
	formulas904 := xs901
	p.consumeLiteral(")")
	_t1672 := &pb.Disjunction{Args: formulas904}
	result906 := _t1672
	p.recordSpan(int(span_start905), "Disjunction")
	return result906
}

func (p *Parser) parse_not() *pb.Not {
	span_start908 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1673 := p.parse_formula()
	formula907 := _t1673
	p.consumeLiteral(")")
	_t1674 := &pb.Not{Arg: formula907}
	result909 := _t1674
	p.recordSpan(int(span_start908), "Not")
	return result909
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1675 := p.parse_name()
	name910 := _t1675
	_t1676 := p.parse_ffi_args()
	ffi_args911 := _t1676
	_t1677 := p.parse_terms()
	terms912 := _t1677
	p.consumeLiteral(")")
	_t1678 := &pb.FFI{Name: name910, Args: ffi_args911, Terms: terms912}
	result914 := _t1678
	p.recordSpan(int(span_start913), "FFI")
	return result914
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol915 := p.consumeTerminal("SYMBOL").Value.str
	return symbol915
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs916 := []*pb.Abstraction{}
	cond917 := p.matchLookaheadLiteral("(", 0)
	for cond917 {
		_t1679 := p.parse_abstraction()
		item918 := _t1679
		xs916 = append(xs916, item918)
		cond917 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions919 := xs916
	p.consumeLiteral(")")
	return abstractions919
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start925 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1680 := p.parse_relation_id()
	relation_id920 := _t1680
	xs921 := []*pb.Term{}
	cond922 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond922 {
		_t1681 := p.parse_term()
		item923 := _t1681
		xs921 = append(xs921, item923)
		cond922 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms924 := xs921
	p.consumeLiteral(")")
	_t1682 := &pb.Atom{Name: relation_id920, Terms: terms924}
	result926 := _t1682
	p.recordSpan(int(span_start925), "Atom")
	return result926
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start932 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1683 := p.parse_name()
	name927 := _t1683
	xs928 := []*pb.Term{}
	cond929 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond929 {
		_t1684 := p.parse_term()
		item930 := _t1684
		xs928 = append(xs928, item930)
		cond929 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms931 := xs928
	p.consumeLiteral(")")
	_t1685 := &pb.Pragma{Name: name927, Terms: terms931}
	result933 := _t1685
	p.recordSpan(int(span_start932), "Pragma")
	return result933
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start949 := int64(p.spanStart())
	var _t1686 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1687 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1687 = 9
		} else {
			var _t1688 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1688 = 4
			} else {
				var _t1689 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1689 = 3
				} else {
					var _t1690 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1690 = 0
					} else {
						var _t1691 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1691 = 2
						} else {
							var _t1692 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1692 = 1
							} else {
								var _t1693 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1693 = 8
								} else {
									var _t1694 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1694 = 6
									} else {
										var _t1695 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1695 = 5
										} else {
											var _t1696 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1696 = 7
											} else {
												_t1696 = -1
											}
											_t1695 = _t1696
										}
										_t1694 = _t1695
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
	} else {
		_t1686 = -1
	}
	prediction934 := _t1686
	var _t1697 *pb.Primitive
	if prediction934 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1698 := p.parse_name()
		name944 := _t1698
		xs945 := []*pb.RelTerm{}
		cond946 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond946 {
			_t1699 := p.parse_rel_term()
			item947 := _t1699
			xs945 = append(xs945, item947)
			cond946 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms948 := xs945
		p.consumeLiteral(")")
		_t1700 := &pb.Primitive{Name: name944, Terms: rel_terms948}
		_t1697 = _t1700
	} else {
		var _t1701 *pb.Primitive
		if prediction934 == 8 {
			_t1702 := p.parse_divide()
			divide943 := _t1702
			_t1701 = divide943
		} else {
			var _t1703 *pb.Primitive
			if prediction934 == 7 {
				_t1704 := p.parse_multiply()
				multiply942 := _t1704
				_t1703 = multiply942
			} else {
				var _t1705 *pb.Primitive
				if prediction934 == 6 {
					_t1706 := p.parse_minus()
					minus941 := _t1706
					_t1705 = minus941
				} else {
					var _t1707 *pb.Primitive
					if prediction934 == 5 {
						_t1708 := p.parse_add()
						add940 := _t1708
						_t1707 = add940
					} else {
						var _t1709 *pb.Primitive
						if prediction934 == 4 {
							_t1710 := p.parse_gt_eq()
							gt_eq939 := _t1710
							_t1709 = gt_eq939
						} else {
							var _t1711 *pb.Primitive
							if prediction934 == 3 {
								_t1712 := p.parse_gt()
								gt938 := _t1712
								_t1711 = gt938
							} else {
								var _t1713 *pb.Primitive
								if prediction934 == 2 {
									_t1714 := p.parse_lt_eq()
									lt_eq937 := _t1714
									_t1713 = lt_eq937
								} else {
									var _t1715 *pb.Primitive
									if prediction934 == 1 {
										_t1716 := p.parse_lt()
										lt936 := _t1716
										_t1715 = lt936
									} else {
										var _t1717 *pb.Primitive
										if prediction934 == 0 {
											_t1718 := p.parse_eq()
											eq935 := _t1718
											_t1717 = eq935
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1715 = _t1717
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
		_t1697 = _t1701
	}
	result950 := _t1697
	p.recordSpan(int(span_start949), "Primitive")
	return result950
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1719 := p.parse_term()
	term951 := _t1719
	_t1720 := p.parse_term()
	term_3952 := _t1720
	p.consumeLiteral(")")
	_t1721 := &pb.RelTerm{}
	_t1721.RelTermType = &pb.RelTerm_Term{Term: term951}
	_t1722 := &pb.RelTerm{}
	_t1722.RelTermType = &pb.RelTerm_Term{Term: term_3952}
	_t1723 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1721, _t1722}}
	result954 := _t1723
	p.recordSpan(int(span_start953), "Primitive")
	return result954
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1724 := p.parse_term()
	term955 := _t1724
	_t1725 := p.parse_term()
	term_3956 := _t1725
	p.consumeLiteral(")")
	_t1726 := &pb.RelTerm{}
	_t1726.RelTermType = &pb.RelTerm_Term{Term: term955}
	_t1727 := &pb.RelTerm{}
	_t1727.RelTermType = &pb.RelTerm_Term{Term: term_3956}
	_t1728 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1726, _t1727}}
	result958 := _t1728
	p.recordSpan(int(span_start957), "Primitive")
	return result958
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start961 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1729 := p.parse_term()
	term959 := _t1729
	_t1730 := p.parse_term()
	term_3960 := _t1730
	p.consumeLiteral(")")
	_t1731 := &pb.RelTerm{}
	_t1731.RelTermType = &pb.RelTerm_Term{Term: term959}
	_t1732 := &pb.RelTerm{}
	_t1732.RelTermType = &pb.RelTerm_Term{Term: term_3960}
	_t1733 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1731, _t1732}}
	result962 := _t1733
	p.recordSpan(int(span_start961), "Primitive")
	return result962
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1734 := p.parse_term()
	term963 := _t1734
	_t1735 := p.parse_term()
	term_3964 := _t1735
	p.consumeLiteral(")")
	_t1736 := &pb.RelTerm{}
	_t1736.RelTermType = &pb.RelTerm_Term{Term: term963}
	_t1737 := &pb.RelTerm{}
	_t1737.RelTermType = &pb.RelTerm_Term{Term: term_3964}
	_t1738 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1736, _t1737}}
	result966 := _t1738
	p.recordSpan(int(span_start965), "Primitive")
	return result966
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1739 := p.parse_term()
	term967 := _t1739
	_t1740 := p.parse_term()
	term_3968 := _t1740
	p.consumeLiteral(")")
	_t1741 := &pb.RelTerm{}
	_t1741.RelTermType = &pb.RelTerm_Term{Term: term967}
	_t1742 := &pb.RelTerm{}
	_t1742.RelTermType = &pb.RelTerm_Term{Term: term_3968}
	_t1743 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1741, _t1742}}
	result970 := _t1743
	p.recordSpan(int(span_start969), "Primitive")
	return result970
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1744 := p.parse_term()
	term971 := _t1744
	_t1745 := p.parse_term()
	term_3972 := _t1745
	_t1746 := p.parse_term()
	term_4973 := _t1746
	p.consumeLiteral(")")
	_t1747 := &pb.RelTerm{}
	_t1747.RelTermType = &pb.RelTerm_Term{Term: term971}
	_t1748 := &pb.RelTerm{}
	_t1748.RelTermType = &pb.RelTerm_Term{Term: term_3972}
	_t1749 := &pb.RelTerm{}
	_t1749.RelTermType = &pb.RelTerm_Term{Term: term_4973}
	_t1750 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1747, _t1748, _t1749}}
	result975 := _t1750
	p.recordSpan(int(span_start974), "Primitive")
	return result975
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1751 := p.parse_term()
	term976 := _t1751
	_t1752 := p.parse_term()
	term_3977 := _t1752
	_t1753 := p.parse_term()
	term_4978 := _t1753
	p.consumeLiteral(")")
	_t1754 := &pb.RelTerm{}
	_t1754.RelTermType = &pb.RelTerm_Term{Term: term976}
	_t1755 := &pb.RelTerm{}
	_t1755.RelTermType = &pb.RelTerm_Term{Term: term_3977}
	_t1756 := &pb.RelTerm{}
	_t1756.RelTermType = &pb.RelTerm_Term{Term: term_4978}
	_t1757 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1754, _t1755, _t1756}}
	result980 := _t1757
	p.recordSpan(int(span_start979), "Primitive")
	return result980
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1758 := p.parse_term()
	term981 := _t1758
	_t1759 := p.parse_term()
	term_3982 := _t1759
	_t1760 := p.parse_term()
	term_4983 := _t1760
	p.consumeLiteral(")")
	_t1761 := &pb.RelTerm{}
	_t1761.RelTermType = &pb.RelTerm_Term{Term: term981}
	_t1762 := &pb.RelTerm{}
	_t1762.RelTermType = &pb.RelTerm_Term{Term: term_3982}
	_t1763 := &pb.RelTerm{}
	_t1763.RelTermType = &pb.RelTerm_Term{Term: term_4983}
	_t1764 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1761, _t1762, _t1763}}
	result985 := _t1764
	p.recordSpan(int(span_start984), "Primitive")
	return result985
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start989 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1765 := p.parse_term()
	term986 := _t1765
	_t1766 := p.parse_term()
	term_3987 := _t1766
	_t1767 := p.parse_term()
	term_4988 := _t1767
	p.consumeLiteral(")")
	_t1768 := &pb.RelTerm{}
	_t1768.RelTermType = &pb.RelTerm_Term{Term: term986}
	_t1769 := &pb.RelTerm{}
	_t1769.RelTermType = &pb.RelTerm_Term{Term: term_3987}
	_t1770 := &pb.RelTerm{}
	_t1770.RelTermType = &pb.RelTerm_Term{Term: term_4988}
	_t1771 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1768, _t1769, _t1770}}
	result990 := _t1771
	p.recordSpan(int(span_start989), "Primitive")
	return result990
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start994 := int64(p.spanStart())
	var _t1772 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1772 = 1
	} else {
		var _t1773 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1773 = 1
		} else {
			var _t1774 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1774 = 1
			} else {
				var _t1775 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1775 = 1
				} else {
					var _t1776 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1776 = 0
					} else {
						var _t1777 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1777 = 1
						} else {
							var _t1778 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1778 = 1
							} else {
								var _t1779 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1779 = 1
								} else {
									var _t1780 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1780 = 1
									} else {
										var _t1781 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1781 = 1
										} else {
											var _t1782 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1782 = 1
											} else {
												var _t1783 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1783 = 1
												} else {
													var _t1784 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1784 = 1
													} else {
														var _t1785 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1785 = 1
														} else {
															var _t1786 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1786 = 1
															} else {
																_t1786 = -1
															}
															_t1785 = _t1786
														}
														_t1784 = _t1785
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
	prediction991 := _t1772
	var _t1787 *pb.RelTerm
	if prediction991 == 1 {
		_t1788 := p.parse_term()
		term993 := _t1788
		_t1789 := &pb.RelTerm{}
		_t1789.RelTermType = &pb.RelTerm_Term{Term: term993}
		_t1787 = _t1789
	} else {
		var _t1790 *pb.RelTerm
		if prediction991 == 0 {
			_t1791 := p.parse_specialized_value()
			specialized_value992 := _t1791
			_t1792 := &pb.RelTerm{}
			_t1792.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value992}
			_t1790 = _t1792
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1787 = _t1790
	}
	result995 := _t1787
	p.recordSpan(int(span_start994), "RelTerm")
	return result995
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start997 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1793 := p.parse_raw_value()
	raw_value996 := _t1793
	result998 := raw_value996
	p.recordSpan(int(span_start997), "Value")
	return result998
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1794 := p.parse_name()
	name999 := _t1794
	xs1000 := []*pb.RelTerm{}
	cond1001 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond1001 {
		_t1795 := p.parse_rel_term()
		item1002 := _t1795
		xs1000 = append(xs1000, item1002)
		cond1001 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms1003 := xs1000
	p.consumeLiteral(")")
	_t1796 := &pb.RelAtom{Name: name999, Terms: rel_terms1003}
	result1005 := _t1796
	p.recordSpan(int(span_start1004), "RelAtom")
	return result1005
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start1008 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1797 := p.parse_term()
	term1006 := _t1797
	_t1798 := p.parse_term()
	term_31007 := _t1798
	p.consumeLiteral(")")
	_t1799 := &pb.Cast{Input: term1006, Result: term_31007}
	result1009 := _t1799
	p.recordSpan(int(span_start1008), "Cast")
	return result1009
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1010 := []*pb.Attribute{}
	cond1011 := p.matchLookaheadLiteral("(", 0)
	for cond1011 {
		_t1800 := p.parse_attribute()
		item1012 := _t1800
		xs1010 = append(xs1010, item1012)
		cond1011 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1013 := xs1010
	p.consumeLiteral(")")
	return attributes1013
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1019 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1801 := p.parse_name()
	name1014 := _t1801
	xs1015 := []*pb.Value{}
	cond1016 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond1016 {
		_t1802 := p.parse_raw_value()
		item1017 := _t1802
		xs1015 = append(xs1015, item1017)
		cond1016 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values1018 := xs1015
	p.consumeLiteral(")")
	_t1803 := &pb.Attribute{Name: name1014, Args: raw_values1018}
	result1020 := _t1803
	p.recordSpan(int(span_start1019), "Attribute")
	return result1020
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1021 := []*pb.RelationId{}
	cond1022 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1022 {
		_t1804 := p.parse_relation_id()
		item1023 := _t1804
		xs1021 = append(xs1021, item1023)
		cond1022 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1024 := xs1021
	_t1805 := p.parse_script()
	script1025 := _t1805
	p.consumeLiteral(")")
	_t1806 := &pb.Algorithm{Global: relation_ids1024, Body: script1025}
	result1027 := _t1806
	p.recordSpan(int(span_start1026), "Algorithm")
	return result1027
}

func (p *Parser) parse_script() *pb.Script {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1028 := []*pb.Construct{}
	cond1029 := p.matchLookaheadLiteral("(", 0)
	for cond1029 {
		_t1807 := p.parse_construct()
		item1030 := _t1807
		xs1028 = append(xs1028, item1030)
		cond1029 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1031 := xs1028
	p.consumeLiteral(")")
	_t1808 := &pb.Script{Constructs: constructs1031}
	result1033 := _t1808
	p.recordSpan(int(span_start1032), "Script")
	return result1033
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1037 := int64(p.spanStart())
	var _t1809 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1810 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1810 = 1
		} else {
			var _t1811 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1811 = 1
			} else {
				var _t1812 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1812 = 1
				} else {
					var _t1813 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1813 = 0
					} else {
						var _t1814 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1814 = 1
						} else {
							var _t1815 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1815 = 1
							} else {
								_t1815 = -1
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
	} else {
		_t1809 = -1
	}
	prediction1034 := _t1809
	var _t1816 *pb.Construct
	if prediction1034 == 1 {
		_t1817 := p.parse_instruction()
		instruction1036 := _t1817
		_t1818 := &pb.Construct{}
		_t1818.ConstructType = &pb.Construct_Instruction{Instruction: instruction1036}
		_t1816 = _t1818
	} else {
		var _t1819 *pb.Construct
		if prediction1034 == 0 {
			_t1820 := p.parse_loop()
			loop1035 := _t1820
			_t1821 := &pb.Construct{}
			_t1821.ConstructType = &pb.Construct_Loop{Loop: loop1035}
			_t1819 = _t1821
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1816 = _t1819
	}
	result1038 := _t1816
	p.recordSpan(int(span_start1037), "Construct")
	return result1038
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1041 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1822 := p.parse_init()
	init1039 := _t1822
	_t1823 := p.parse_script()
	script1040 := _t1823
	p.consumeLiteral(")")
	_t1824 := &pb.Loop{Init: init1039, Body: script1040}
	result1042 := _t1824
	p.recordSpan(int(span_start1041), "Loop")
	return result1042
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1043 := []*pb.Instruction{}
	cond1044 := p.matchLookaheadLiteral("(", 0)
	for cond1044 {
		_t1825 := p.parse_instruction()
		item1045 := _t1825
		xs1043 = append(xs1043, item1045)
		cond1044 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1046 := xs1043
	p.consumeLiteral(")")
	return instructions1046
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1053 := int64(p.spanStart())
	var _t1826 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1827 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1827 = 1
		} else {
			var _t1828 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1828 = 4
			} else {
				var _t1829 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1829 = 3
				} else {
					var _t1830 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1830 = 2
					} else {
						var _t1831 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1831 = 0
						} else {
							_t1831 = -1
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
	prediction1047 := _t1826
	var _t1832 *pb.Instruction
	if prediction1047 == 4 {
		_t1833 := p.parse_monus_def()
		monus_def1052 := _t1833
		_t1834 := &pb.Instruction{}
		_t1834.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1052}
		_t1832 = _t1834
	} else {
		var _t1835 *pb.Instruction
		if prediction1047 == 3 {
			_t1836 := p.parse_monoid_def()
			monoid_def1051 := _t1836
			_t1837 := &pb.Instruction{}
			_t1837.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1051}
			_t1835 = _t1837
		} else {
			var _t1838 *pb.Instruction
			if prediction1047 == 2 {
				_t1839 := p.parse_break()
				break1050 := _t1839
				_t1840 := &pb.Instruction{}
				_t1840.InstrType = &pb.Instruction_Break{Break: break1050}
				_t1838 = _t1840
			} else {
				var _t1841 *pb.Instruction
				if prediction1047 == 1 {
					_t1842 := p.parse_upsert()
					upsert1049 := _t1842
					_t1843 := &pb.Instruction{}
					_t1843.InstrType = &pb.Instruction_Upsert{Upsert: upsert1049}
					_t1841 = _t1843
				} else {
					var _t1844 *pb.Instruction
					if prediction1047 == 0 {
						_t1845 := p.parse_assign()
						assign1048 := _t1845
						_t1846 := &pb.Instruction{}
						_t1846.InstrType = &pb.Instruction_Assign{Assign: assign1048}
						_t1844 = _t1846
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1841 = _t1844
				}
				_t1838 = _t1841
			}
			_t1835 = _t1838
		}
		_t1832 = _t1835
	}
	result1054 := _t1832
	p.recordSpan(int(span_start1053), "Instruction")
	return result1054
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1058 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1847 := p.parse_relation_id()
	relation_id1055 := _t1847
	_t1848 := p.parse_abstraction()
	abstraction1056 := _t1848
	var _t1849 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1850 := p.parse_attrs()
		_t1849 = _t1850
	}
	attrs1057 := _t1849
	p.consumeLiteral(")")
	_t1851 := attrs1057
	if attrs1057 == nil {
		_t1851 = []*pb.Attribute{}
	}
	_t1852 := &pb.Assign{Name: relation_id1055, Body: abstraction1056, Attrs: _t1851}
	result1059 := _t1852
	p.recordSpan(int(span_start1058), "Assign")
	return result1059
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1063 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1853 := p.parse_relation_id()
	relation_id1060 := _t1853
	_t1854 := p.parse_abstraction_with_arity()
	abstraction_with_arity1061 := _t1854
	var _t1855 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1856 := p.parse_attrs()
		_t1855 = _t1856
	}
	attrs1062 := _t1855
	p.consumeLiteral(")")
	_t1857 := attrs1062
	if attrs1062 == nil {
		_t1857 = []*pb.Attribute{}
	}
	_t1858 := &pb.Upsert{Name: relation_id1060, Body: abstraction_with_arity1061[0].(*pb.Abstraction), Attrs: _t1857, ValueArity: abstraction_with_arity1061[1].(int64)}
	result1064 := _t1858
	p.recordSpan(int(span_start1063), "Upsert")
	return result1064
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1859 := p.parse_bindings()
	bindings1065 := _t1859
	_t1860 := p.parse_formula()
	formula1066 := _t1860
	p.consumeLiteral(")")
	_t1861 := &pb.Abstraction{Vars: listConcat(bindings1065[0].([]*pb.Binding), bindings1065[1].([]*pb.Binding)), Value: formula1066}
	return []interface{}{_t1861, int64(len(bindings1065[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1070 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1862 := p.parse_relation_id()
	relation_id1067 := _t1862
	_t1863 := p.parse_abstraction()
	abstraction1068 := _t1863
	var _t1864 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1865 := p.parse_attrs()
		_t1864 = _t1865
	}
	attrs1069 := _t1864
	p.consumeLiteral(")")
	_t1866 := attrs1069
	if attrs1069 == nil {
		_t1866 = []*pb.Attribute{}
	}
	_t1867 := &pb.Break{Name: relation_id1067, Body: abstraction1068, Attrs: _t1866}
	result1071 := _t1867
	p.recordSpan(int(span_start1070), "Break")
	return result1071
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1076 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1868 := p.parse_monoid()
	monoid1072 := _t1868
	_t1869 := p.parse_relation_id()
	relation_id1073 := _t1869
	_t1870 := p.parse_abstraction_with_arity()
	abstraction_with_arity1074 := _t1870
	var _t1871 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1872 := p.parse_attrs()
		_t1871 = _t1872
	}
	attrs1075 := _t1871
	p.consumeLiteral(")")
	_t1873 := attrs1075
	if attrs1075 == nil {
		_t1873 = []*pb.Attribute{}
	}
	_t1874 := &pb.MonoidDef{Monoid: monoid1072, Name: relation_id1073, Body: abstraction_with_arity1074[0].(*pb.Abstraction), Attrs: _t1873, ValueArity: abstraction_with_arity1074[1].(int64)}
	result1077 := _t1874
	p.recordSpan(int(span_start1076), "MonoidDef")
	return result1077
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1083 := int64(p.spanStart())
	var _t1875 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1876 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1876 = 3
		} else {
			var _t1877 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1877 = 0
			} else {
				var _t1878 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1878 = 1
				} else {
					var _t1879 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1879 = 2
					} else {
						_t1879 = -1
					}
					_t1878 = _t1879
				}
				_t1877 = _t1878
			}
			_t1876 = _t1877
		}
		_t1875 = _t1876
	} else {
		_t1875 = -1
	}
	prediction1078 := _t1875
	var _t1880 *pb.Monoid
	if prediction1078 == 3 {
		_t1881 := p.parse_sum_monoid()
		sum_monoid1082 := _t1881
		_t1882 := &pb.Monoid{}
		_t1882.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1082}
		_t1880 = _t1882
	} else {
		var _t1883 *pb.Monoid
		if prediction1078 == 2 {
			_t1884 := p.parse_max_monoid()
			max_monoid1081 := _t1884
			_t1885 := &pb.Monoid{}
			_t1885.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1081}
			_t1883 = _t1885
		} else {
			var _t1886 *pb.Monoid
			if prediction1078 == 1 {
				_t1887 := p.parse_min_monoid()
				min_monoid1080 := _t1887
				_t1888 := &pb.Monoid{}
				_t1888.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1080}
				_t1886 = _t1888
			} else {
				var _t1889 *pb.Monoid
				if prediction1078 == 0 {
					_t1890 := p.parse_or_monoid()
					or_monoid1079 := _t1890
					_t1891 := &pb.Monoid{}
					_t1891.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1079}
					_t1889 = _t1891
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1886 = _t1889
			}
			_t1883 = _t1886
		}
		_t1880 = _t1883
	}
	result1084 := _t1880
	p.recordSpan(int(span_start1083), "Monoid")
	return result1084
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1085 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1892 := &pb.OrMonoid{}
	result1086 := _t1892
	p.recordSpan(int(span_start1085), "OrMonoid")
	return result1086
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1893 := p.parse_type()
	type1087 := _t1893
	p.consumeLiteral(")")
	_t1894 := &pb.MinMonoid{Type: type1087}
	result1089 := _t1894
	p.recordSpan(int(span_start1088), "MinMonoid")
	return result1089
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1091 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1895 := p.parse_type()
	type1090 := _t1895
	p.consumeLiteral(")")
	_t1896 := &pb.MaxMonoid{Type: type1090}
	result1092 := _t1896
	p.recordSpan(int(span_start1091), "MaxMonoid")
	return result1092
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1897 := p.parse_type()
	type1093 := _t1897
	p.consumeLiteral(")")
	_t1898 := &pb.SumMonoid{Type: type1093}
	result1095 := _t1898
	p.recordSpan(int(span_start1094), "SumMonoid")
	return result1095
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1100 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1899 := p.parse_monoid()
	monoid1096 := _t1899
	_t1900 := p.parse_relation_id()
	relation_id1097 := _t1900
	_t1901 := p.parse_abstraction_with_arity()
	abstraction_with_arity1098 := _t1901
	var _t1902 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1903 := p.parse_attrs()
		_t1902 = _t1903
	}
	attrs1099 := _t1902
	p.consumeLiteral(")")
	_t1904 := attrs1099
	if attrs1099 == nil {
		_t1904 = []*pb.Attribute{}
	}
	_t1905 := &pb.MonusDef{Monoid: monoid1096, Name: relation_id1097, Body: abstraction_with_arity1098[0].(*pb.Abstraction), Attrs: _t1904, ValueArity: abstraction_with_arity1098[1].(int64)}
	result1101 := _t1905
	p.recordSpan(int(span_start1100), "MonusDef")
	return result1101
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1106 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1906 := p.parse_relation_id()
	relation_id1102 := _t1906
	_t1907 := p.parse_abstraction()
	abstraction1103 := _t1907
	_t1908 := p.parse_functional_dependency_keys()
	functional_dependency_keys1104 := _t1908
	_t1909 := p.parse_functional_dependency_values()
	functional_dependency_values1105 := _t1909
	p.consumeLiteral(")")
	_t1910 := &pb.FunctionalDependency{Guard: abstraction1103, Keys: functional_dependency_keys1104, Values: functional_dependency_values1105}
	_t1911 := &pb.Constraint{Name: relation_id1102}
	_t1911.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1910}
	result1107 := _t1911
	p.recordSpan(int(span_start1106), "Constraint")
	return result1107
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1108 := []*pb.Var{}
	cond1109 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1109 {
		_t1912 := p.parse_var()
		item1110 := _t1912
		xs1108 = append(xs1108, item1110)
		cond1109 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1111 := xs1108
	p.consumeLiteral(")")
	return vars1111
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1112 := []*pb.Var{}
	cond1113 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1113 {
		_t1913 := p.parse_var()
		item1114 := _t1913
		xs1112 = append(xs1112, item1114)
		cond1113 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1115 := xs1112
	p.consumeLiteral(")")
	return vars1115
}

func (p *Parser) parse_data() *pb.Data {
	span_start1121 := int64(p.spanStart())
	var _t1914 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1915 int64
		if p.matchLookaheadLiteral("iceberg_data", 1) {
			_t1915 = 3
		} else {
			var _t1916 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1916 = 0
			} else {
				var _t1917 int64
				if p.matchLookaheadLiteral("csv_data", 1) {
					_t1917 = 2
				} else {
					var _t1918 int64
					if p.matchLookaheadLiteral("betree_relation", 1) {
						_t1918 = 1
					} else {
						_t1918 = -1
					}
					_t1917 = _t1918
				}
				_t1916 = _t1917
			}
			_t1915 = _t1916
		}
		_t1914 = _t1915
	} else {
		_t1914 = -1
	}
	prediction1116 := _t1914
	var _t1919 *pb.Data
	if prediction1116 == 3 {
		_t1920 := p.parse_iceberg_data()
		iceberg_data1120 := _t1920
		_t1921 := &pb.Data{}
		_t1921.DataType = &pb.Data_IcebergData{IcebergData: iceberg_data1120}
		_t1919 = _t1921
	} else {
		var _t1922 *pb.Data
		if prediction1116 == 2 {
			_t1923 := p.parse_csv_data()
			csv_data1119 := _t1923
			_t1924 := &pb.Data{}
			_t1924.DataType = &pb.Data_CsvData{CsvData: csv_data1119}
			_t1922 = _t1924
		} else {
			var _t1925 *pb.Data
			if prediction1116 == 1 {
				_t1926 := p.parse_betree_relation()
				betree_relation1118 := _t1926
				_t1927 := &pb.Data{}
				_t1927.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1118}
				_t1925 = _t1927
			} else {
				var _t1928 *pb.Data
				if prediction1116 == 0 {
					_t1929 := p.parse_edb()
					edb1117 := _t1929
					_t1930 := &pb.Data{}
					_t1930.DataType = &pb.Data_Edb{Edb: edb1117}
					_t1928 = _t1930
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1925 = _t1928
			}
			_t1922 = _t1925
		}
		_t1919 = _t1922
	}
	result1122 := _t1919
	p.recordSpan(int(span_start1121), "Data")
	return result1122
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1126 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1931 := p.parse_relation_id()
	relation_id1123 := _t1931
	_t1932 := p.parse_edb_path()
	edb_path1124 := _t1932
	_t1933 := p.parse_edb_types()
	edb_types1125 := _t1933
	p.consumeLiteral(")")
	_t1934 := &pb.EDB{TargetId: relation_id1123, Path: edb_path1124, Types: edb_types1125}
	result1127 := _t1934
	p.recordSpan(int(span_start1126), "EDB")
	return result1127
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1128 := []string{}
	cond1129 := p.matchLookaheadTerminal("STRING", 0)
	for cond1129 {
		item1130 := p.consumeTerminal("STRING").Value.str
		xs1128 = append(xs1128, item1130)
		cond1129 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1131 := xs1128
	p.consumeLiteral("]")
	return strings1131
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1132 := []*pb.Type{}
	cond1133 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1133 {
		_t1935 := p.parse_type()
		item1134 := _t1935
		xs1132 = append(xs1132, item1134)
		cond1133 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1135 := xs1132
	p.consumeLiteral("]")
	return types1135
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1936 := p.parse_relation_id()
	relation_id1136 := _t1936
	_t1937 := p.parse_betree_info()
	betree_info1137 := _t1937
	p.consumeLiteral(")")
	_t1938 := &pb.BeTreeRelation{Name: relation_id1136, RelationInfo: betree_info1137}
	result1139 := _t1938
	p.recordSpan(int(span_start1138), "BeTreeRelation")
	return result1139
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1143 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1939 := p.parse_betree_info_key_types()
	betree_info_key_types1140 := _t1939
	_t1940 := p.parse_betree_info_value_types()
	betree_info_value_types1141 := _t1940
	_t1941 := p.parse_config_dict()
	config_dict1142 := _t1941
	p.consumeLiteral(")")
	_t1942 := p.construct_betree_info(betree_info_key_types1140, betree_info_value_types1141, config_dict1142)
	result1144 := _t1942
	p.recordSpan(int(span_start1143), "BeTreeInfo")
	return result1144
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1145 := []*pb.Type{}
	cond1146 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1146 {
		_t1943 := p.parse_type()
		item1147 := _t1943
		xs1145 = append(xs1145, item1147)
		cond1146 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1148 := xs1145
	p.consumeLiteral(")")
	return types1148
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1149 := []*pb.Type{}
	cond1150 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1150 {
		_t1944 := p.parse_type()
		item1151 := _t1944
		xs1149 = append(xs1149, item1151)
		cond1150 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1152 := xs1149
	p.consumeLiteral(")")
	return types1152
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1945 := p.parse_csvlocator()
	csvlocator1153 := _t1945
	_t1946 := p.parse_csv_config()
	csv_config1154 := _t1946
	_t1947 := p.parse_gnf_columns()
	gnf_columns1155 := _t1947
	_t1948 := p.parse_csv_asof()
	csv_asof1156 := _t1948
	p.consumeLiteral(")")
	_t1949 := &pb.CSVData{Locator: csvlocator1153, Config: csv_config1154, Columns: gnf_columns1155, Asof: csv_asof1156}
	result1158 := _t1949
	p.recordSpan(int(span_start1157), "CSVData")
	return result1158
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1161 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1950 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1951 := p.parse_csv_locator_paths()
		_t1950 = _t1951
	}
	csv_locator_paths1159 := _t1950
	var _t1952 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1953 := p.parse_csv_locator_inline_data()
		_t1952 = ptr(_t1953)
	}
	csv_locator_inline_data1160 := _t1952
	p.consumeLiteral(")")
	_t1954 := csv_locator_paths1159
	if csv_locator_paths1159 == nil {
		_t1954 = []string{}
	}
	_t1955 := &pb.CSVLocator{Paths: _t1954, InlineData: []byte(deref(csv_locator_inline_data1160, ""))}
	result1162 := _t1955
	p.recordSpan(int(span_start1161), "CSVLocator")
	return result1162
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1163 := []string{}
	cond1164 := p.matchLookaheadTerminal("STRING", 0)
	for cond1164 {
		item1165 := p.consumeTerminal("STRING").Value.str
		xs1163 = append(xs1163, item1165)
		cond1164 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1166 := xs1163
	p.consumeLiteral(")")
	return strings1166
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1167 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1167
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1169 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1956 := p.parse_config_dict()
	config_dict1168 := _t1956
	p.consumeLiteral(")")
	_t1957 := p.construct_csv_config(config_dict1168)
	result1170 := _t1957
	p.recordSpan(int(span_start1169), "CSVConfig")
	return result1170
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1171 := []*pb.GNFColumn{}
	cond1172 := p.matchLookaheadLiteral("(", 0)
	for cond1172 {
		_t1958 := p.parse_gnf_column()
		item1173 := _t1958
		xs1171 = append(xs1171, item1173)
		cond1172 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1174 := xs1171
	p.consumeLiteral(")")
	return gnf_columns1174
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1181 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1959 := p.parse_gnf_column_path()
	gnf_column_path1175 := _t1959
	var _t1960 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1961 := p.parse_relation_id()
		_t1960 = _t1961
	}
	relation_id1176 := _t1960
	p.consumeLiteral("[")
	xs1177 := []*pb.Type{}
	cond1178 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1178 {
		_t1962 := p.parse_type()
		item1179 := _t1962
		xs1177 = append(xs1177, item1179)
		cond1178 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1180 := xs1177
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1963 := &pb.GNFColumn{ColumnPath: gnf_column_path1175, TargetId: relation_id1176, Types: types1180}
	result1182 := _t1963
	p.recordSpan(int(span_start1181), "GNFColumn")
	return result1182
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1964 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1964 = 1
	} else {
		var _t1965 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1965 = 0
		} else {
			_t1965 = -1
		}
		_t1964 = _t1965
	}
	prediction1183 := _t1964
	var _t1966 []string
	if prediction1183 == 1 {
		p.consumeLiteral("[")
		xs1185 := []string{}
		cond1186 := p.matchLookaheadTerminal("STRING", 0)
		for cond1186 {
			item1187 := p.consumeTerminal("STRING").Value.str
			xs1185 = append(xs1185, item1187)
			cond1186 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1188 := xs1185
		p.consumeLiteral("]")
		_t1966 = strings1188
	} else {
		var _t1967 []string
		if prediction1183 == 0 {
			string1184 := p.consumeTerminal("STRING").Value.str
			_ = string1184
			_t1967 = []string{string1184}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1966 = _t1967
	}
	return _t1966
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1189 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1189
}

func (p *Parser) parse_iceberg_data() *pb.IcebergData {
	span_start1194 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_data")
	_t1968 := p.parse_iceberg_locator()
	iceberg_locator1190 := _t1968
	_t1969 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1191 := _t1969
	_t1970 := p.parse_gnf_columns()
	gnf_columns1192 := _t1970
	_t1971 := p.parse_boolean_value()
	boolean_value1193 := _t1971
	p.consumeLiteral(")")
	_t1972 := &pb.IcebergData{Locator: iceberg_locator1190, Config: iceberg_catalog_config1191, Columns: gnf_columns1192, ReturnsDelta: boolean_value1193}
	result1195 := _t1972
	p.recordSpan(int(span_start1194), "IcebergData")
	return result1195
}

func (p *Parser) parse_iceberg_locator() *pb.IcebergLocator {
	span_start1204 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_locator")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string1196 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1197 := []string{}
	cond1198 := p.matchLookaheadTerminal("STRING", 0)
	for cond1198 {
		item1199 := p.consumeTerminal("STRING").Value.str
		xs1197 = append(xs1197, item1199)
		cond1198 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1200 := xs1197
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string_121201 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1973 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("from_snapshot", 1)) {
		_t1974 := p.parse_iceberg_from_snapshot()
		_t1973 = ptr(_t1974)
	}
	iceberg_from_snapshot1202 := _t1973
	var _t1975 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1976 := p.parse_iceberg_to_snapshot()
		_t1975 = ptr(_t1976)
	}
	iceberg_to_snapshot1203 := _t1975
	p.consumeLiteral(")")
	_t1977 := p.construct_iceberg_locator(string1196, strings1200, string_121201, iceberg_from_snapshot1202, iceberg_to_snapshot1203)
	result1205 := _t1977
	p.recordSpan(int(span_start1204), "IcebergLocator")
	return result1205
}

func (p *Parser) parse_iceberg_from_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("from_snapshot")
	string1206 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1206
}

func (p *Parser) parse_iceberg_to_snapshot() string {
	p.consumeLiteral("(")
	p.consumeLiteral("to_snapshot")
	string1207 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1207
}

func (p *Parser) parse_iceberg_catalog_config() *pb.IcebergCatalogConfig {
	span_start1218 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("iceberg_catalog_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1208 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1978 *string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("scope", 1)) {
		_t1979 := p.parse_iceberg_catalog_config_scope()
		_t1978 = ptr(_t1979)
	}
	iceberg_catalog_config_scope1209 := _t1978
	p.consumeLiteral("(")
	p.consumeLiteral("properties")
	xs1210 := [][]interface{}{}
	cond1211 := p.matchLookaheadLiteral("(", 0)
	for cond1211 {
		_t1980 := p.parse_iceberg_property_entry()
		item1212 := _t1980
		xs1210 = append(xs1210, item1212)
		cond1211 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1213 := xs1210
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("auth_properties")
	xs1214 := [][]interface{}{}
	cond1215 := p.matchLookaheadLiteral("(", 0)
	for cond1215 {
		_t1981 := p.parse_iceberg_masked_property_entry()
		item1216 := _t1981
		xs1214 = append(xs1214, item1216)
		cond1215 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_masked_property_entrys1217 := xs1214
	p.consumeLiteral(")")
	p.consumeLiteral(")")
	_t1982 := p.construct_iceberg_catalog_config(string1208, iceberg_catalog_config_scope1209, iceberg_property_entrys1213, iceberg_masked_property_entrys1217)
	result1219 := _t1982
	p.recordSpan(int(span_start1218), "IcebergCatalogConfig")
	return result1219
}

func (p *Parser) parse_iceberg_catalog_config_scope() string {
	p.consumeLiteral("(")
	p.consumeLiteral("scope")
	string1220 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1220
}

func (p *Parser) parse_iceberg_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1221 := p.consumeTerminal("STRING").Value.str
	string_31222 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1221, string_31222}
}

func (p *Parser) parse_iceberg_masked_property_entry() []interface{} {
	p.consumeLiteral("(")
	p.consumeLiteral("prop")
	string1223 := p.consumeTerminal("STRING").Value.str
	string_31224 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return []interface{}{string1223, string_31224}
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1226 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1983 := p.parse_fragment_id()
	fragment_id1225 := _t1983
	p.consumeLiteral(")")
	_t1984 := &pb.Undefine{FragmentId: fragment_id1225}
	result1227 := _t1984
	p.recordSpan(int(span_start1226), "Undefine")
	return result1227
}

func (p *Parser) parse_context() *pb.Context {
	span_start1232 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1228 := []*pb.RelationId{}
	cond1229 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1229 {
		_t1985 := p.parse_relation_id()
		item1230 := _t1985
		xs1228 = append(xs1228, item1230)
		cond1229 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1231 := xs1228
	p.consumeLiteral(")")
	_t1986 := &pb.Context{Relations: relation_ids1231}
	result1233 := _t1986
	p.recordSpan(int(span_start1232), "Context")
	return result1233
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1238 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1234 := []*pb.SnapshotMapping{}
	cond1235 := p.matchLookaheadLiteral("[", 0)
	for cond1235 {
		_t1987 := p.parse_snapshot_mapping()
		item1236 := _t1987
		xs1234 = append(xs1234, item1236)
		cond1235 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1237 := xs1234
	p.consumeLiteral(")")
	_t1988 := &pb.Snapshot{Mappings: snapshot_mappings1237}
	result1239 := _t1988
	p.recordSpan(int(span_start1238), "Snapshot")
	return result1239
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1242 := int64(p.spanStart())
	_t1989 := p.parse_edb_path()
	edb_path1240 := _t1989
	_t1990 := p.parse_relation_id()
	relation_id1241 := _t1990
	_t1991 := &pb.SnapshotMapping{DestinationPath: edb_path1240, SourceRelation: relation_id1241}
	result1243 := _t1991
	p.recordSpan(int(span_start1242), "SnapshotMapping")
	return result1243
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1244 := []*pb.Read{}
	cond1245 := p.matchLookaheadLiteral("(", 0)
	for cond1245 {
		_t1992 := p.parse_read()
		item1246 := _t1992
		xs1244 = append(xs1244, item1246)
		cond1245 = p.matchLookaheadLiteral("(", 0)
	}
	reads1247 := xs1244
	p.consumeLiteral(")")
	return reads1247
}

func (p *Parser) parse_read() *pb.Read {
	span_start1254 := int64(p.spanStart())
	var _t1993 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1994 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1994 = 2
		} else {
			var _t1995 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1995 = 1
			} else {
				var _t1996 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1996 = 4
				} else {
					var _t1997 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1997 = 4
					} else {
						var _t1998 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1998 = 0
						} else {
							var _t1999 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1999 = 3
							} else {
								_t1999 = -1
							}
							_t1998 = _t1999
						}
						_t1997 = _t1998
					}
					_t1996 = _t1997
				}
				_t1995 = _t1996
			}
			_t1994 = _t1995
		}
		_t1993 = _t1994
	} else {
		_t1993 = -1
	}
	prediction1248 := _t1993
	var _t2000 *pb.Read
	if prediction1248 == 4 {
		_t2001 := p.parse_export()
		export1253 := _t2001
		_t2002 := &pb.Read{}
		_t2002.ReadType = &pb.Read_Export{Export: export1253}
		_t2000 = _t2002
	} else {
		var _t2003 *pb.Read
		if prediction1248 == 3 {
			_t2004 := p.parse_abort()
			abort1252 := _t2004
			_t2005 := &pb.Read{}
			_t2005.ReadType = &pb.Read_Abort{Abort: abort1252}
			_t2003 = _t2005
		} else {
			var _t2006 *pb.Read
			if prediction1248 == 2 {
				_t2007 := p.parse_what_if()
				what_if1251 := _t2007
				_t2008 := &pb.Read{}
				_t2008.ReadType = &pb.Read_WhatIf{WhatIf: what_if1251}
				_t2006 = _t2008
			} else {
				var _t2009 *pb.Read
				if prediction1248 == 1 {
					_t2010 := p.parse_output()
					output1250 := _t2010
					_t2011 := &pb.Read{}
					_t2011.ReadType = &pb.Read_Output{Output: output1250}
					_t2009 = _t2011
				} else {
					var _t2012 *pb.Read
					if prediction1248 == 0 {
						_t2013 := p.parse_demand()
						demand1249 := _t2013
						_t2014 := &pb.Read{}
						_t2014.ReadType = &pb.Read_Demand{Demand: demand1249}
						_t2012 = _t2014
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t2009 = _t2012
				}
				_t2006 = _t2009
			}
			_t2003 = _t2006
		}
		_t2000 = _t2003
	}
	result1255 := _t2000
	p.recordSpan(int(span_start1254), "Read")
	return result1255
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1257 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t2015 := p.parse_relation_id()
	relation_id1256 := _t2015
	p.consumeLiteral(")")
	_t2016 := &pb.Demand{RelationId: relation_id1256}
	result1258 := _t2016
	p.recordSpan(int(span_start1257), "Demand")
	return result1258
}

func (p *Parser) parse_output() *pb.Output {
	span_start1261 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t2017 := p.parse_name()
	name1259 := _t2017
	_t2018 := p.parse_relation_id()
	relation_id1260 := _t2018
	p.consumeLiteral(")")
	_t2019 := &pb.Output{Name: name1259, RelationId: relation_id1260}
	result1262 := _t2019
	p.recordSpan(int(span_start1261), "Output")
	return result1262
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1265 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t2020 := p.parse_name()
	name1263 := _t2020
	_t2021 := p.parse_epoch()
	epoch1264 := _t2021
	p.consumeLiteral(")")
	_t2022 := &pb.WhatIf{Branch: name1263, Epoch: epoch1264}
	result1266 := _t2022
	p.recordSpan(int(span_start1265), "WhatIf")
	return result1266
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1269 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t2023 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t2024 := p.parse_name()
		_t2023 = ptr(_t2024)
	}
	name1267 := _t2023
	_t2025 := p.parse_relation_id()
	relation_id1268 := _t2025
	p.consumeLiteral(")")
	_t2026 := &pb.Abort{Name: deref(name1267, "abort"), RelationId: relation_id1268}
	result1270 := _t2026
	p.recordSpan(int(span_start1269), "Abort")
	return result1270
}

func (p *Parser) parse_export() *pb.Export {
	span_start1274 := int64(p.spanStart())
	var _t2027 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2028 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t2028 = 1
		} else {
			var _t2029 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t2029 = 0
			} else {
				_t2029 = -1
			}
			_t2028 = _t2029
		}
		_t2027 = _t2028
	} else {
		_t2027 = -1
	}
	prediction1271 := _t2027
	var _t2030 *pb.Export
	if prediction1271 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t2031 := p.parse_export_iceberg_config()
		export_iceberg_config1273 := _t2031
		p.consumeLiteral(")")
		_t2032 := &pb.Export{}
		_t2032.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1273}
		_t2030 = _t2032
	} else {
		var _t2033 *pb.Export
		if prediction1271 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t2034 := p.parse_export_csv_config()
			export_csv_config1272 := _t2034
			p.consumeLiteral(")")
			_t2035 := &pb.Export{}
			_t2035.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1272}
			_t2033 = _t2035
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2030 = _t2033
	}
	result1275 := _t2030
	p.recordSpan(int(span_start1274), "Export")
	return result1275
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1283 := int64(p.spanStart())
	var _t2036 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2037 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t2037 = 0
		} else {
			var _t2038 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t2038 = 1
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
	var _t2039 *pb.ExportCSVConfig
	if prediction1276 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t2040 := p.parse_export_csv_path()
		export_csv_path1280 := _t2040
		_t2041 := p.parse_export_csv_columns_list()
		export_csv_columns_list1281 := _t2041
		_t2042 := p.parse_config_dict()
		config_dict1282 := _t2042
		p.consumeLiteral(")")
		_t2043 := p.construct_export_csv_config(export_csv_path1280, export_csv_columns_list1281, config_dict1282)
		_t2039 = _t2043
	} else {
		var _t2044 *pb.ExportCSVConfig
		if prediction1276 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t2045 := p.parse_export_csv_path()
			export_csv_path1277 := _t2045
			_t2046 := p.parse_export_csv_source()
			export_csv_source1278 := _t2046
			_t2047 := p.parse_csv_config()
			csv_config1279 := _t2047
			p.consumeLiteral(")")
			_t2048 := p.construct_export_csv_config_with_source(export_csv_path1277, export_csv_source1278, csv_config1279)
			_t2044 = _t2048
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2039 = _t2044
	}
	result1284 := _t2039
	p.recordSpan(int(span_start1283), "ExportCSVConfig")
	return result1284
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1285 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1285
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1292 := int64(p.spanStart())
	var _t2049 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t2050 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t2050 = 1
		} else {
			var _t2051 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t2051 = 0
			} else {
				_t2051 = -1
			}
			_t2050 = _t2051
		}
		_t2049 = _t2050
	} else {
		_t2049 = -1
	}
	prediction1286 := _t2049
	var _t2052 *pb.ExportCSVSource
	if prediction1286 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t2053 := p.parse_relation_id()
		relation_id1291 := _t2053
		p.consumeLiteral(")")
		_t2054 := &pb.ExportCSVSource{}
		_t2054.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1291}
		_t2052 = _t2054
	} else {
		var _t2055 *pb.ExportCSVSource
		if prediction1286 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1287 := []*pb.ExportCSVColumn{}
			cond1288 := p.matchLookaheadLiteral("(", 0)
			for cond1288 {
				_t2056 := p.parse_export_csv_column()
				item1289 := _t2056
				xs1287 = append(xs1287, item1289)
				cond1288 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1290 := xs1287
			p.consumeLiteral(")")
			_t2057 := &pb.ExportCSVColumns{Columns: export_csv_columns1290}
			_t2058 := &pb.ExportCSVSource{}
			_t2058.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t2057}
			_t2055 = _t2058
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t2052 = _t2055
	}
	result1293 := _t2052
	p.recordSpan(int(span_start1292), "ExportCSVSource")
	return result1293
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1296 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1294 := p.consumeTerminal("STRING").Value.str
	_t2059 := p.parse_relation_id()
	relation_id1295 := _t2059
	p.consumeLiteral(")")
	_t2060 := &pb.ExportCSVColumn{ColumnName: string1294, ColumnData: relation_id1295}
	result1297 := _t2060
	p.recordSpan(int(span_start1296), "ExportCSVColumn")
	return result1297
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1298 := []*pb.ExportCSVColumn{}
	cond1299 := p.matchLookaheadLiteral("(", 0)
	for cond1299 {
		_t2061 := p.parse_export_csv_column()
		item1300 := _t2061
		xs1298 = append(xs1298, item1300)
		cond1299 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1301 := xs1298
	p.consumeLiteral(")")
	return export_csv_columns1301
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1314 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	_t2062 := p.parse_iceberg_locator()
	iceberg_locator1302 := _t2062
	_t2063 := p.parse_iceberg_catalog_config()
	iceberg_catalog_config1303 := _t2063
	p.consumeLiteral("(")
	p.consumeLiteral("table_def")
	_t2064 := p.parse_relation_id()
	relation_id1304 := _t2064
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1305 := []*pb.ExportGNFColumn{}
	cond1306 := p.matchLookaheadLiteral("(", 0)
	for cond1306 {
		_t2065 := p.parse_export_gnf_column()
		item1307 := _t2065
		xs1305 = append(xs1305, item1307)
		cond1306 = p.matchLookaheadLiteral("(", 0)
	}
	export_gnf_columns1308 := xs1305
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("table_properties")
	xs1309 := [][]interface{}{}
	cond1310 := p.matchLookaheadLiteral("(", 0)
	for cond1310 {
		_t2066 := p.parse_iceberg_property_entry()
		item1311 := _t2066
		xs1309 = append(xs1309, item1311)
		cond1310 = p.matchLookaheadLiteral("(", 0)
	}
	iceberg_property_entrys1312 := xs1309
	p.consumeLiteral(")")
	var _t2067 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t2068 := p.parse_config_dict()
		_t2067 = _t2068
	}
	config_dict1313 := _t2067
	p.consumeLiteral(")")
	_t2069 := p.construct_export_iceberg_config_full(iceberg_locator1302, iceberg_catalog_config1303, relation_id1304, export_gnf_columns1308, iceberg_property_entrys1312, config_dict1313)
	result1315 := _t2069
	p.recordSpan(int(span_start1314), "ExportIcebergConfig")
	return result1315
}

func (p *Parser) parse_export_gnf_column() *pb.ExportGNFColumn {
	span_start1318 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("gnf_column")
	string1316 := p.consumeTerminal("STRING").Value.str
	_t2070 := p.parse_boolean_value()
	boolean_value1317 := _t2070
	p.consumeLiteral(")")
	_t2071 := &pb.ExportGNFColumn{Name: string1316, Nullable: boolean_value1317}
	result1319 := _t2071
	p.recordSpan(int(span_start1318), "ExportGNFColumn")
	return result1319
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
