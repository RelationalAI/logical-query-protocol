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
	var _t1971 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1971
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1972 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1972
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1973 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1973
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1974 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1974
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1975 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1975
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1976 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1976
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1977 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1977
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1978 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1978
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1979 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1979
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1980 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1980
	_t1981 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1981
	_t1982 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1982
	_t1983 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1983
	_t1984 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1984
	_t1985 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1985
	_t1986 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1986
	_t1987 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1987
	_t1988 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1988
	_t1989 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1989
	_t1990 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1990
	_t1991 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1991
	_t1992 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1992
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1993 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1993
	_t1994 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1994
	_t1995 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1995
	_t1996 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1996
	_t1997 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1997
	_t1998 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1998
	_t1999 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1999
	_t2000 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t2000
	_t2001 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t2001
	_t2002 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t2002.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t2002.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t2002
	_t2003 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t2003
}

func (p *Parser) default_configure() *pb.Configure {
	_t2004 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t2004
	_t2005 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t2005
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
	_t2006 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t2006
	_t2007 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t2007
	_t2008 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t2008
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t2009 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t2009
	_t2010 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t2010
	_t2011 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t2011
	_t2012 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t2012
	_t2013 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t2013
	_t2014 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t2014
	_t2015 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t2015
	_t2016 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t2016
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t2017 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t2017
}

func (p *Parser) construct_export_iceberg_config_from_optional(catalog_uri string, namespace []string, table_name string, catalog_properties *pb.IcebergCatalogProperties, schema string, config_dict [][]interface{}) *pb.ExportIcebergConfig {
	prefix := ""
	_t2018 := p._extract_value_int64(nil, 0)
	target_file_size_bytes := _t2018
	compression := ""
	if config_dict != nil {
		config := dictFromList(config_dict)
		_t2019 := p._extract_value_string(dictGetValue(config, "prefix"), "")
		prefix = _t2019
		_t2020 := p._extract_value_int64(dictGetValue(config, "target_file_size_bytes"), 0)
		target_file_size_bytes = _t2020
		_t2021 := p._extract_value_string(dictGetValue(config, "compression"), "")
		compression = _t2021
	}
	_t2022 := &pb.ExportIcebergConfig{CatalogUri: catalog_uri, Namespace: namespace, TableName: table_name, CatalogProperties: catalog_properties, Schema: schema, Prefix: ptr(prefix), TargetFileSizeBytes: ptr(target_file_size_bytes), Compression: compression}
	return _t2022
}

func (p *Parser) construct_iceberg_catalog_properties_from_optional(warehouse string, config_dict [][]interface{}) *pb.IcebergCatalogProperties {
	token := ""
	credential := ""
	if config_dict != nil {
		config := dictFromList(config_dict)
		_t2023 := p._extract_value_string(dictGetValue(config, "token"), "")
		token = _t2023
		_t2024 := p._extract_value_string(dictGetValue(config, "credential"), "")
		credential = _t2024
	}
	_t2025 := &pb.IcebergCatalogProperties{Warehouse: warehouse, Token: ptr(token), Credential: ptr(credential)}
	return _t2025
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start627 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1242 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1243 := p.parse_configure()
		_t1242 = _t1243
	}
	configure621 := _t1242
	var _t1244 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1245 := p.parse_sync()
		_t1244 = _t1245
	}
	sync622 := _t1244
	xs623 := []*pb.Epoch{}
	cond624 := p.matchLookaheadLiteral("(", 0)
	for cond624 {
		_t1246 := p.parse_epoch()
		item625 := _t1246
		xs623 = append(xs623, item625)
		cond624 = p.matchLookaheadLiteral("(", 0)
	}
	epochs626 := xs623
	p.consumeLiteral(")")
	_t1247 := p.default_configure()
	_t1248 := configure621
	if configure621 == nil {
		_t1248 = _t1247
	}
	_t1249 := &pb.Transaction{Epochs: epochs626, Configure: _t1248, Sync: sync622}
	result628 := _t1249
	p.recordSpan(int(span_start627), "Transaction")
	return result628
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start630 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1250 := p.parse_config_dict()
	config_dict629 := _t1250
	p.consumeLiteral(")")
	_t1251 := p.construct_configure(config_dict629)
	result631 := _t1251
	p.recordSpan(int(span_start630), "Configure")
	return result631
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs632 := [][]interface{}{}
	cond633 := p.matchLookaheadLiteral(":", 0)
	for cond633 {
		_t1252 := p.parse_config_key_value()
		item634 := _t1252
		xs632 = append(xs632, item634)
		cond633 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values635 := xs632
	p.consumeLiteral("}")
	return config_key_values635
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol636 := p.consumeTerminal("SYMBOL").Value.str
	_t1253 := p.parse_raw_value()
	raw_value637 := _t1253
	return []interface{}{symbol636, raw_value637}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start651 := int64(p.spanStart())
	var _t1254 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1254 = 12
	} else {
		var _t1255 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1255 = 11
		} else {
			var _t1256 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1256 = 12
			} else {
				var _t1257 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1258 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1258 = 1
					} else {
						var _t1259 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1259 = 0
						} else {
							_t1259 = -1
						}
						_t1258 = _t1259
					}
					_t1257 = _t1258
				} else {
					var _t1260 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1260 = 7
					} else {
						var _t1261 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1261 = 8
						} else {
							var _t1262 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1262 = 2
							} else {
								var _t1263 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1263 = 3
								} else {
									var _t1264 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1264 = 9
									} else {
										var _t1265 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1265 = 4
										} else {
											var _t1266 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1266 = 5
											} else {
												var _t1267 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1267 = 6
												} else {
													var _t1268 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1268 = 10
													} else {
														_t1268 = -1
													}
													_t1267 = _t1268
												}
												_t1266 = _t1267
											}
											_t1265 = _t1266
										}
										_t1264 = _t1265
									}
									_t1263 = _t1264
								}
								_t1262 = _t1263
							}
							_t1261 = _t1262
						}
						_t1260 = _t1261
					}
					_t1257 = _t1260
				}
				_t1256 = _t1257
			}
			_t1255 = _t1256
		}
		_t1254 = _t1255
	}
	prediction638 := _t1254
	var _t1269 *pb.Value
	if prediction638 == 12 {
		_t1270 := p.parse_boolean_value()
		boolean_value650 := _t1270
		_t1271 := &pb.Value{}
		_t1271.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value650}
		_t1269 = _t1271
	} else {
		var _t1272 *pb.Value
		if prediction638 == 11 {
			p.consumeLiteral("missing")
			_t1273 := &pb.MissingValue{}
			_t1274 := &pb.Value{}
			_t1274.Value = &pb.Value_MissingValue{MissingValue: _t1273}
			_t1272 = _t1274
		} else {
			var _t1275 *pb.Value
			if prediction638 == 10 {
				decimal649 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1276 := &pb.Value{}
				_t1276.Value = &pb.Value_DecimalValue{DecimalValue: decimal649}
				_t1275 = _t1276
			} else {
				var _t1277 *pb.Value
				if prediction638 == 9 {
					int128648 := p.consumeTerminal("INT128").Value.int128
					_t1278 := &pb.Value{}
					_t1278.Value = &pb.Value_Int128Value{Int128Value: int128648}
					_t1277 = _t1278
				} else {
					var _t1279 *pb.Value
					if prediction638 == 8 {
						uint128647 := p.consumeTerminal("UINT128").Value.uint128
						_t1280 := &pb.Value{}
						_t1280.Value = &pb.Value_Uint128Value{Uint128Value: uint128647}
						_t1279 = _t1280
					} else {
						var _t1281 *pb.Value
						if prediction638 == 7 {
							uint32646 := p.consumeTerminal("UINT32").Value.u32
							_t1282 := &pb.Value{}
							_t1282.Value = &pb.Value_Uint32Value{Uint32Value: uint32646}
							_t1281 = _t1282
						} else {
							var _t1283 *pb.Value
							if prediction638 == 6 {
								float645 := p.consumeTerminal("FLOAT").Value.f64
								_t1284 := &pb.Value{}
								_t1284.Value = &pb.Value_FloatValue{FloatValue: float645}
								_t1283 = _t1284
							} else {
								var _t1285 *pb.Value
								if prediction638 == 5 {
									float32644 := p.consumeTerminal("FLOAT32").Value.f32
									_t1286 := &pb.Value{}
									_t1286.Value = &pb.Value_Float32Value{Float32Value: float32644}
									_t1285 = _t1286
								} else {
									var _t1287 *pb.Value
									if prediction638 == 4 {
										int643 := p.consumeTerminal("INT").Value.i64
										_t1288 := &pb.Value{}
										_t1288.Value = &pb.Value_IntValue{IntValue: int643}
										_t1287 = _t1288
									} else {
										var _t1289 *pb.Value
										if prediction638 == 3 {
											int32642 := p.consumeTerminal("INT32").Value.i32
											_t1290 := &pb.Value{}
											_t1290.Value = &pb.Value_Int32Value{Int32Value: int32642}
											_t1289 = _t1290
										} else {
											var _t1291 *pb.Value
											if prediction638 == 2 {
												string641 := p.consumeTerminal("STRING").Value.str
												_t1292 := &pb.Value{}
												_t1292.Value = &pb.Value_StringValue{StringValue: string641}
												_t1291 = _t1292
											} else {
												var _t1293 *pb.Value
												if prediction638 == 1 {
													_t1294 := p.parse_raw_datetime()
													raw_datetime640 := _t1294
													_t1295 := &pb.Value{}
													_t1295.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime640}
													_t1293 = _t1295
												} else {
													var _t1296 *pb.Value
													if prediction638 == 0 {
														_t1297 := p.parse_raw_date()
														raw_date639 := _t1297
														_t1298 := &pb.Value{}
														_t1298.Value = &pb.Value_DateValue{DateValue: raw_date639}
														_t1296 = _t1298
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1293 = _t1296
												}
												_t1291 = _t1293
											}
											_t1289 = _t1291
										}
										_t1287 = _t1289
									}
									_t1285 = _t1287
								}
								_t1283 = _t1285
							}
							_t1281 = _t1283
						}
						_t1279 = _t1281
					}
					_t1277 = _t1279
				}
				_t1275 = _t1277
			}
			_t1272 = _t1275
		}
		_t1269 = _t1272
	}
	result652 := _t1269
	p.recordSpan(int(span_start651), "Value")
	return result652
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start656 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int653 := p.consumeTerminal("INT").Value.i64
	int_3654 := p.consumeTerminal("INT").Value.i64
	int_4655 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1299 := &pb.DateValue{Year: int32(int653), Month: int32(int_3654), Day: int32(int_4655)}
	result657 := _t1299
	p.recordSpan(int(span_start656), "DateValue")
	return result657
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start665 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int658 := p.consumeTerminal("INT").Value.i64
	int_3659 := p.consumeTerminal("INT").Value.i64
	int_4660 := p.consumeTerminal("INT").Value.i64
	int_5661 := p.consumeTerminal("INT").Value.i64
	int_6662 := p.consumeTerminal("INT").Value.i64
	int_7663 := p.consumeTerminal("INT").Value.i64
	var _t1300 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1300 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8664 := _t1300
	p.consumeLiteral(")")
	_t1301 := &pb.DateTimeValue{Year: int32(int658), Month: int32(int_3659), Day: int32(int_4660), Hour: int32(int_5661), Minute: int32(int_6662), Second: int32(int_7663), Microsecond: int32(deref(int_8664, 0))}
	result666 := _t1301
	p.recordSpan(int(span_start665), "DateTimeValue")
	return result666
}

func (p *Parser) parse_boolean_value() bool {
	var _t1302 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1302 = 0
	} else {
		var _t1303 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1303 = 1
		} else {
			_t1303 = -1
		}
		_t1302 = _t1303
	}
	prediction667 := _t1302
	var _t1304 bool
	if prediction667 == 1 {
		p.consumeLiteral("false")
		_t1304 = false
	} else {
		var _t1305 bool
		if prediction667 == 0 {
			p.consumeLiteral("true")
			_t1305 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1304 = _t1305
	}
	return _t1304
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start672 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs668 := []*pb.FragmentId{}
	cond669 := p.matchLookaheadLiteral(":", 0)
	for cond669 {
		_t1306 := p.parse_fragment_id()
		item670 := _t1306
		xs668 = append(xs668, item670)
		cond669 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids671 := xs668
	p.consumeLiteral(")")
	_t1307 := &pb.Sync{Fragments: fragment_ids671}
	result673 := _t1307
	p.recordSpan(int(span_start672), "Sync")
	return result673
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start675 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol674 := p.consumeTerminal("SYMBOL").Value.str
	result676 := &pb.FragmentId{Id: []byte(symbol674)}
	p.recordSpan(int(span_start675), "FragmentId")
	return result676
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start679 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1308 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1309 := p.parse_epoch_writes()
		_t1308 = _t1309
	}
	epoch_writes677 := _t1308
	var _t1310 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1311 := p.parse_epoch_reads()
		_t1310 = _t1311
	}
	epoch_reads678 := _t1310
	p.consumeLiteral(")")
	_t1312 := epoch_writes677
	if epoch_writes677 == nil {
		_t1312 = []*pb.Write{}
	}
	_t1313 := epoch_reads678
	if epoch_reads678 == nil {
		_t1313 = []*pb.Read{}
	}
	_t1314 := &pb.Epoch{Writes: _t1312, Reads: _t1313}
	result680 := _t1314
	p.recordSpan(int(span_start679), "Epoch")
	return result680
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs681 := []*pb.Write{}
	cond682 := p.matchLookaheadLiteral("(", 0)
	for cond682 {
		_t1315 := p.parse_write()
		item683 := _t1315
		xs681 = append(xs681, item683)
		cond682 = p.matchLookaheadLiteral("(", 0)
	}
	writes684 := xs681
	p.consumeLiteral(")")
	return writes684
}

func (p *Parser) parse_write() *pb.Write {
	span_start690 := int64(p.spanStart())
	var _t1316 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1317 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1317 = 1
		} else {
			var _t1318 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1318 = 3
			} else {
				var _t1319 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1319 = 0
				} else {
					var _t1320 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1320 = 2
					} else {
						_t1320 = -1
					}
					_t1319 = _t1320
				}
				_t1318 = _t1319
			}
			_t1317 = _t1318
		}
		_t1316 = _t1317
	} else {
		_t1316 = -1
	}
	prediction685 := _t1316
	var _t1321 *pb.Write
	if prediction685 == 3 {
		_t1322 := p.parse_snapshot()
		snapshot689 := _t1322
		_t1323 := &pb.Write{}
		_t1323.WriteType = &pb.Write_Snapshot{Snapshot: snapshot689}
		_t1321 = _t1323
	} else {
		var _t1324 *pb.Write
		if prediction685 == 2 {
			_t1325 := p.parse_context()
			context688 := _t1325
			_t1326 := &pb.Write{}
			_t1326.WriteType = &pb.Write_Context{Context: context688}
			_t1324 = _t1326
		} else {
			var _t1327 *pb.Write
			if prediction685 == 1 {
				_t1328 := p.parse_undefine()
				undefine687 := _t1328
				_t1329 := &pb.Write{}
				_t1329.WriteType = &pb.Write_Undefine{Undefine: undefine687}
				_t1327 = _t1329
			} else {
				var _t1330 *pb.Write
				if prediction685 == 0 {
					_t1331 := p.parse_define()
					define686 := _t1331
					_t1332 := &pb.Write{}
					_t1332.WriteType = &pb.Write_Define{Define: define686}
					_t1330 = _t1332
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1327 = _t1330
			}
			_t1324 = _t1327
		}
		_t1321 = _t1324
	}
	result691 := _t1321
	p.recordSpan(int(span_start690), "Write")
	return result691
}

func (p *Parser) parse_define() *pb.Define {
	span_start693 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1333 := p.parse_fragment()
	fragment692 := _t1333
	p.consumeLiteral(")")
	_t1334 := &pb.Define{Fragment: fragment692}
	result694 := _t1334
	p.recordSpan(int(span_start693), "Define")
	return result694
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start700 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1335 := p.parse_new_fragment_id()
	new_fragment_id695 := _t1335
	xs696 := []*pb.Declaration{}
	cond697 := p.matchLookaheadLiteral("(", 0)
	for cond697 {
		_t1336 := p.parse_declaration()
		item698 := _t1336
		xs696 = append(xs696, item698)
		cond697 = p.matchLookaheadLiteral("(", 0)
	}
	declarations699 := xs696
	p.consumeLiteral(")")
	result701 := p.constructFragment(new_fragment_id695, declarations699)
	p.recordSpan(int(span_start700), "Fragment")
	return result701
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start703 := int64(p.spanStart())
	_t1337 := p.parse_fragment_id()
	fragment_id702 := _t1337
	p.startFragment(fragment_id702)
	result704 := fragment_id702
	p.recordSpan(int(span_start703), "FragmentId")
	return result704
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start710 := int64(p.spanStart())
	var _t1338 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1339 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1339 = 2
		} else {
			var _t1340 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1340 = 3
			} else {
				var _t1341 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1341 = 0
				} else {
					var _t1342 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1342 = 3
					} else {
						var _t1343 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1343 = 3
						} else {
							var _t1344 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1344 = 1
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
	} else {
		_t1338 = -1
	}
	prediction705 := _t1338
	var _t1345 *pb.Declaration
	if prediction705 == 3 {
		_t1346 := p.parse_data()
		data709 := _t1346
		_t1347 := &pb.Declaration{}
		_t1347.DeclarationType = &pb.Declaration_Data{Data: data709}
		_t1345 = _t1347
	} else {
		var _t1348 *pb.Declaration
		if prediction705 == 2 {
			_t1349 := p.parse_constraint()
			constraint708 := _t1349
			_t1350 := &pb.Declaration{}
			_t1350.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint708}
			_t1348 = _t1350
		} else {
			var _t1351 *pb.Declaration
			if prediction705 == 1 {
				_t1352 := p.parse_algorithm()
				algorithm707 := _t1352
				_t1353 := &pb.Declaration{}
				_t1353.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm707}
				_t1351 = _t1353
			} else {
				var _t1354 *pb.Declaration
				if prediction705 == 0 {
					_t1355 := p.parse_def()
					def706 := _t1355
					_t1356 := &pb.Declaration{}
					_t1356.DeclarationType = &pb.Declaration_Def{Def: def706}
					_t1354 = _t1356
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1351 = _t1354
			}
			_t1348 = _t1351
		}
		_t1345 = _t1348
	}
	result711 := _t1345
	p.recordSpan(int(span_start710), "Declaration")
	return result711
}

func (p *Parser) parse_def() *pb.Def {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1357 := p.parse_relation_id()
	relation_id712 := _t1357
	_t1358 := p.parse_abstraction()
	abstraction713 := _t1358
	var _t1359 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1360 := p.parse_attrs()
		_t1359 = _t1360
	}
	attrs714 := _t1359
	p.consumeLiteral(")")
	_t1361 := attrs714
	if attrs714 == nil {
		_t1361 = []*pb.Attribute{}
	}
	_t1362 := &pb.Def{Name: relation_id712, Body: abstraction713, Attrs: _t1361}
	result716 := _t1362
	p.recordSpan(int(span_start715), "Def")
	return result716
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start720 := int64(p.spanStart())
	var _t1363 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1363 = 0
	} else {
		var _t1364 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1364 = 1
		} else {
			_t1364 = -1
		}
		_t1363 = _t1364
	}
	prediction717 := _t1363
	var _t1365 *pb.RelationId
	if prediction717 == 1 {
		uint128719 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128719
		_t1365 = &pb.RelationId{IdLow: uint128719.Low, IdHigh: uint128719.High}
	} else {
		var _t1366 *pb.RelationId
		if prediction717 == 0 {
			p.consumeLiteral(":")
			symbol718 := p.consumeTerminal("SYMBOL").Value.str
			_t1366 = p.relationIdFromString(symbol718)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1365 = _t1366
	}
	result721 := _t1365
	p.recordSpan(int(span_start720), "RelationId")
	return result721
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start724 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1367 := p.parse_bindings()
	bindings722 := _t1367
	_t1368 := p.parse_formula()
	formula723 := _t1368
	p.consumeLiteral(")")
	_t1369 := &pb.Abstraction{Vars: listConcat(bindings722[0].([]*pb.Binding), bindings722[1].([]*pb.Binding)), Value: formula723}
	result725 := _t1369
	p.recordSpan(int(span_start724), "Abstraction")
	return result725
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs726 := []*pb.Binding{}
	cond727 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond727 {
		_t1370 := p.parse_binding()
		item728 := _t1370
		xs726 = append(xs726, item728)
		cond727 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings729 := xs726
	var _t1371 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1372 := p.parse_value_bindings()
		_t1371 = _t1372
	}
	value_bindings730 := _t1371
	p.consumeLiteral("]")
	_t1373 := value_bindings730
	if value_bindings730 == nil {
		_t1373 = []*pb.Binding{}
	}
	return []interface{}{bindings729, _t1373}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start733 := int64(p.spanStart())
	symbol731 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1374 := p.parse_type()
	type732 := _t1374
	_t1375 := &pb.Var{Name: symbol731}
	_t1376 := &pb.Binding{Var: _t1375, Type: type732}
	result734 := _t1376
	p.recordSpan(int(span_start733), "Binding")
	return result734
}

func (p *Parser) parse_type() *pb.Type {
	span_start750 := int64(p.spanStart())
	var _t1377 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1377 = 0
	} else {
		var _t1378 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1378 = 13
		} else {
			var _t1379 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1379 = 4
			} else {
				var _t1380 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1380 = 1
				} else {
					var _t1381 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1381 = 8
					} else {
						var _t1382 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1382 = 11
						} else {
							var _t1383 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1383 = 5
							} else {
								var _t1384 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1384 = 2
								} else {
									var _t1385 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1385 = 12
									} else {
										var _t1386 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1386 = 3
										} else {
											var _t1387 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1387 = 7
											} else {
												var _t1388 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1388 = 6
												} else {
													var _t1389 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1389 = 10
													} else {
														var _t1390 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1390 = 9
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
										}
										_t1385 = _t1386
									}
									_t1384 = _t1385
								}
								_t1383 = _t1384
							}
							_t1382 = _t1383
						}
						_t1381 = _t1382
					}
					_t1380 = _t1381
				}
				_t1379 = _t1380
			}
			_t1378 = _t1379
		}
		_t1377 = _t1378
	}
	prediction735 := _t1377
	var _t1391 *pb.Type
	if prediction735 == 13 {
		_t1392 := p.parse_uint32_type()
		uint32_type749 := _t1392
		_t1393 := &pb.Type{}
		_t1393.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type749}
		_t1391 = _t1393
	} else {
		var _t1394 *pb.Type
		if prediction735 == 12 {
			_t1395 := p.parse_float32_type()
			float32_type748 := _t1395
			_t1396 := &pb.Type{}
			_t1396.Type = &pb.Type_Float32Type{Float32Type: float32_type748}
			_t1394 = _t1396
		} else {
			var _t1397 *pb.Type
			if prediction735 == 11 {
				_t1398 := p.parse_int32_type()
				int32_type747 := _t1398
				_t1399 := &pb.Type{}
				_t1399.Type = &pb.Type_Int32Type{Int32Type: int32_type747}
				_t1397 = _t1399
			} else {
				var _t1400 *pb.Type
				if prediction735 == 10 {
					_t1401 := p.parse_boolean_type()
					boolean_type746 := _t1401
					_t1402 := &pb.Type{}
					_t1402.Type = &pb.Type_BooleanType{BooleanType: boolean_type746}
					_t1400 = _t1402
				} else {
					var _t1403 *pb.Type
					if prediction735 == 9 {
						_t1404 := p.parse_decimal_type()
						decimal_type745 := _t1404
						_t1405 := &pb.Type{}
						_t1405.Type = &pb.Type_DecimalType{DecimalType: decimal_type745}
						_t1403 = _t1405
					} else {
						var _t1406 *pb.Type
						if prediction735 == 8 {
							_t1407 := p.parse_missing_type()
							missing_type744 := _t1407
							_t1408 := &pb.Type{}
							_t1408.Type = &pb.Type_MissingType{MissingType: missing_type744}
							_t1406 = _t1408
						} else {
							var _t1409 *pb.Type
							if prediction735 == 7 {
								_t1410 := p.parse_datetime_type()
								datetime_type743 := _t1410
								_t1411 := &pb.Type{}
								_t1411.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type743}
								_t1409 = _t1411
							} else {
								var _t1412 *pb.Type
								if prediction735 == 6 {
									_t1413 := p.parse_date_type()
									date_type742 := _t1413
									_t1414 := &pb.Type{}
									_t1414.Type = &pb.Type_DateType{DateType: date_type742}
									_t1412 = _t1414
								} else {
									var _t1415 *pb.Type
									if prediction735 == 5 {
										_t1416 := p.parse_int128_type()
										int128_type741 := _t1416
										_t1417 := &pb.Type{}
										_t1417.Type = &pb.Type_Int128Type{Int128Type: int128_type741}
										_t1415 = _t1417
									} else {
										var _t1418 *pb.Type
										if prediction735 == 4 {
											_t1419 := p.parse_uint128_type()
											uint128_type740 := _t1419
											_t1420 := &pb.Type{}
											_t1420.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type740}
											_t1418 = _t1420
										} else {
											var _t1421 *pb.Type
											if prediction735 == 3 {
												_t1422 := p.parse_float_type()
												float_type739 := _t1422
												_t1423 := &pb.Type{}
												_t1423.Type = &pb.Type_FloatType{FloatType: float_type739}
												_t1421 = _t1423
											} else {
												var _t1424 *pb.Type
												if prediction735 == 2 {
													_t1425 := p.parse_int_type()
													int_type738 := _t1425
													_t1426 := &pb.Type{}
													_t1426.Type = &pb.Type_IntType{IntType: int_type738}
													_t1424 = _t1426
												} else {
													var _t1427 *pb.Type
													if prediction735 == 1 {
														_t1428 := p.parse_string_type()
														string_type737 := _t1428
														_t1429 := &pb.Type{}
														_t1429.Type = &pb.Type_StringType{StringType: string_type737}
														_t1427 = _t1429
													} else {
														var _t1430 *pb.Type
														if prediction735 == 0 {
															_t1431 := p.parse_unspecified_type()
															unspecified_type736 := _t1431
															_t1432 := &pb.Type{}
															_t1432.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type736}
															_t1430 = _t1432
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1427 = _t1430
													}
													_t1424 = _t1427
												}
												_t1421 = _t1424
											}
											_t1418 = _t1421
										}
										_t1415 = _t1418
									}
									_t1412 = _t1415
								}
								_t1409 = _t1412
							}
							_t1406 = _t1409
						}
						_t1403 = _t1406
					}
					_t1400 = _t1403
				}
				_t1397 = _t1400
			}
			_t1394 = _t1397
		}
		_t1391 = _t1394
	}
	result751 := _t1391
	p.recordSpan(int(span_start750), "Type")
	return result751
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1433 := &pb.UnspecifiedType{}
	result753 := _t1433
	p.recordSpan(int(span_start752), "UnspecifiedType")
	return result753
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start754 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1434 := &pb.StringType{}
	result755 := _t1434
	p.recordSpan(int(span_start754), "StringType")
	return result755
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start756 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1435 := &pb.IntType{}
	result757 := _t1435
	p.recordSpan(int(span_start756), "IntType")
	return result757
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start758 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1436 := &pb.FloatType{}
	result759 := _t1436
	p.recordSpan(int(span_start758), "FloatType")
	return result759
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start760 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1437 := &pb.UInt128Type{}
	result761 := _t1437
	p.recordSpan(int(span_start760), "UInt128Type")
	return result761
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start762 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1438 := &pb.Int128Type{}
	result763 := _t1438
	p.recordSpan(int(span_start762), "Int128Type")
	return result763
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start764 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1439 := &pb.DateType{}
	result765 := _t1439
	p.recordSpan(int(span_start764), "DateType")
	return result765
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start766 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1440 := &pb.DateTimeType{}
	result767 := _t1440
	p.recordSpan(int(span_start766), "DateTimeType")
	return result767
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start768 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1441 := &pb.MissingType{}
	result769 := _t1441
	p.recordSpan(int(span_start768), "MissingType")
	return result769
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start772 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int770 := p.consumeTerminal("INT").Value.i64
	int_3771 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1442 := &pb.DecimalType{Precision: int32(int770), Scale: int32(int_3771)}
	result773 := _t1442
	p.recordSpan(int(span_start772), "DecimalType")
	return result773
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start774 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1443 := &pb.BooleanType{}
	result775 := _t1443
	p.recordSpan(int(span_start774), "BooleanType")
	return result775
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1444 := &pb.Int32Type{}
	result777 := _t1444
	p.recordSpan(int(span_start776), "Int32Type")
	return result777
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start778 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1445 := &pb.Float32Type{}
	result779 := _t1445
	p.recordSpan(int(span_start778), "Float32Type")
	return result779
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start780 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1446 := &pb.UInt32Type{}
	result781 := _t1446
	p.recordSpan(int(span_start780), "UInt32Type")
	return result781
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs782 := []*pb.Binding{}
	cond783 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond783 {
		_t1447 := p.parse_binding()
		item784 := _t1447
		xs782 = append(xs782, item784)
		cond783 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings785 := xs782
	return bindings785
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start800 := int64(p.spanStart())
	var _t1448 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1449 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1449 = 0
		} else {
			var _t1450 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1450 = 11
			} else {
				var _t1451 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1451 = 3
				} else {
					var _t1452 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1452 = 10
					} else {
						var _t1453 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1453 = 9
						} else {
							var _t1454 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1454 = 5
							} else {
								var _t1455 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1455 = 6
								} else {
									var _t1456 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1456 = 7
									} else {
										var _t1457 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1457 = 1
										} else {
											var _t1458 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1458 = 2
											} else {
												var _t1459 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1459 = 12
												} else {
													var _t1460 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1460 = 8
													} else {
														var _t1461 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1461 = 4
														} else {
															var _t1462 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1462 = 10
															} else {
																var _t1463 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1463 = 10
																} else {
																	var _t1464 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1464 = 10
																	} else {
																		var _t1465 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1465 = 10
																		} else {
																			var _t1466 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1466 = 10
																			} else {
																				var _t1467 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1467 = 10
																				} else {
																					var _t1468 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1468 = 10
																					} else {
																						var _t1469 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1469 = 10
																						} else {
																							var _t1470 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1470 = 10
																							} else {
																								_t1470 = -1
																							}
																							_t1469 = _t1470
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
	} else {
		_t1448 = -1
	}
	prediction786 := _t1448
	var _t1471 *pb.Formula
	if prediction786 == 12 {
		_t1472 := p.parse_cast()
		cast799 := _t1472
		_t1473 := &pb.Formula{}
		_t1473.FormulaType = &pb.Formula_Cast{Cast: cast799}
		_t1471 = _t1473
	} else {
		var _t1474 *pb.Formula
		if prediction786 == 11 {
			_t1475 := p.parse_rel_atom()
			rel_atom798 := _t1475
			_t1476 := &pb.Formula{}
			_t1476.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom798}
			_t1474 = _t1476
		} else {
			var _t1477 *pb.Formula
			if prediction786 == 10 {
				_t1478 := p.parse_primitive()
				primitive797 := _t1478
				_t1479 := &pb.Formula{}
				_t1479.FormulaType = &pb.Formula_Primitive{Primitive: primitive797}
				_t1477 = _t1479
			} else {
				var _t1480 *pb.Formula
				if prediction786 == 9 {
					_t1481 := p.parse_pragma()
					pragma796 := _t1481
					_t1482 := &pb.Formula{}
					_t1482.FormulaType = &pb.Formula_Pragma{Pragma: pragma796}
					_t1480 = _t1482
				} else {
					var _t1483 *pb.Formula
					if prediction786 == 8 {
						_t1484 := p.parse_atom()
						atom795 := _t1484
						_t1485 := &pb.Formula{}
						_t1485.FormulaType = &pb.Formula_Atom{Atom: atom795}
						_t1483 = _t1485
					} else {
						var _t1486 *pb.Formula
						if prediction786 == 7 {
							_t1487 := p.parse_ffi()
							ffi794 := _t1487
							_t1488 := &pb.Formula{}
							_t1488.FormulaType = &pb.Formula_Ffi{Ffi: ffi794}
							_t1486 = _t1488
						} else {
							var _t1489 *pb.Formula
							if prediction786 == 6 {
								_t1490 := p.parse_not()
								not793 := _t1490
								_t1491 := &pb.Formula{}
								_t1491.FormulaType = &pb.Formula_Not{Not: not793}
								_t1489 = _t1491
							} else {
								var _t1492 *pb.Formula
								if prediction786 == 5 {
									_t1493 := p.parse_disjunction()
									disjunction792 := _t1493
									_t1494 := &pb.Formula{}
									_t1494.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction792}
									_t1492 = _t1494
								} else {
									var _t1495 *pb.Formula
									if prediction786 == 4 {
										_t1496 := p.parse_conjunction()
										conjunction791 := _t1496
										_t1497 := &pb.Formula{}
										_t1497.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction791}
										_t1495 = _t1497
									} else {
										var _t1498 *pb.Formula
										if prediction786 == 3 {
											_t1499 := p.parse_reduce()
											reduce790 := _t1499
											_t1500 := &pb.Formula{}
											_t1500.FormulaType = &pb.Formula_Reduce{Reduce: reduce790}
											_t1498 = _t1500
										} else {
											var _t1501 *pb.Formula
											if prediction786 == 2 {
												_t1502 := p.parse_exists()
												exists789 := _t1502
												_t1503 := &pb.Formula{}
												_t1503.FormulaType = &pb.Formula_Exists{Exists: exists789}
												_t1501 = _t1503
											} else {
												var _t1504 *pb.Formula
												if prediction786 == 1 {
													_t1505 := p.parse_false()
													false788 := _t1505
													_t1506 := &pb.Formula{}
													_t1506.FormulaType = &pb.Formula_Disjunction{Disjunction: false788}
													_t1504 = _t1506
												} else {
													var _t1507 *pb.Formula
													if prediction786 == 0 {
														_t1508 := p.parse_true()
														true787 := _t1508
														_t1509 := &pb.Formula{}
														_t1509.FormulaType = &pb.Formula_Conjunction{Conjunction: true787}
														_t1507 = _t1509
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
	result801 := _t1471
	p.recordSpan(int(span_start800), "Formula")
	return result801
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start802 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1510 := &pb.Conjunction{Args: []*pb.Formula{}}
	result803 := _t1510
	p.recordSpan(int(span_start802), "Conjunction")
	return result803
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start804 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1511 := &pb.Disjunction{Args: []*pb.Formula{}}
	result805 := _t1511
	p.recordSpan(int(span_start804), "Disjunction")
	return result805
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start808 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1512 := p.parse_bindings()
	bindings806 := _t1512
	_t1513 := p.parse_formula()
	formula807 := _t1513
	p.consumeLiteral(")")
	_t1514 := &pb.Abstraction{Vars: listConcat(bindings806[0].([]*pb.Binding), bindings806[1].([]*pb.Binding)), Value: formula807}
	_t1515 := &pb.Exists{Body: _t1514}
	result809 := _t1515
	p.recordSpan(int(span_start808), "Exists")
	return result809
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1516 := p.parse_abstraction()
	abstraction810 := _t1516
	_t1517 := p.parse_abstraction()
	abstraction_3811 := _t1517
	_t1518 := p.parse_terms()
	terms812 := _t1518
	p.consumeLiteral(")")
	_t1519 := &pb.Reduce{Op: abstraction810, Body: abstraction_3811, Terms: terms812}
	result814 := _t1519
	p.recordSpan(int(span_start813), "Reduce")
	return result814
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs815 := []*pb.Term{}
	cond816 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond816 {
		_t1520 := p.parse_term()
		item817 := _t1520
		xs815 = append(xs815, item817)
		cond816 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms818 := xs815
	p.consumeLiteral(")")
	return terms818
}

func (p *Parser) parse_term() *pb.Term {
	span_start822 := int64(p.spanStart())
	var _t1521 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1521 = 1
	} else {
		var _t1522 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1522 = 1
		} else {
			var _t1523 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1523 = 1
			} else {
				var _t1524 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1524 = 1
				} else {
					var _t1525 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1525 = 0
					} else {
						var _t1526 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1526 = 1
						} else {
							var _t1527 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1527 = 1
							} else {
								var _t1528 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1528 = 1
								} else {
									var _t1529 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1529 = 1
									} else {
										var _t1530 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1530 = 1
										} else {
											var _t1531 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1531 = 1
											} else {
												var _t1532 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1532 = 1
												} else {
													var _t1533 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1533 = 1
													} else {
														var _t1534 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1534 = 1
														} else {
															_t1534 = -1
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
	prediction819 := _t1521
	var _t1535 *pb.Term
	if prediction819 == 1 {
		_t1536 := p.parse_value()
		value821 := _t1536
		_t1537 := &pb.Term{}
		_t1537.TermType = &pb.Term_Constant{Constant: value821}
		_t1535 = _t1537
	} else {
		var _t1538 *pb.Term
		if prediction819 == 0 {
			_t1539 := p.parse_var()
			var820 := _t1539
			_t1540 := &pb.Term{}
			_t1540.TermType = &pb.Term_Var{Var: var820}
			_t1538 = _t1540
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1535 = _t1538
	}
	result823 := _t1535
	p.recordSpan(int(span_start822), "Term")
	return result823
}

func (p *Parser) parse_var() *pb.Var {
	span_start825 := int64(p.spanStart())
	symbol824 := p.consumeTerminal("SYMBOL").Value.str
	_t1541 := &pb.Var{Name: symbol824}
	result826 := _t1541
	p.recordSpan(int(span_start825), "Var")
	return result826
}

func (p *Parser) parse_value() *pb.Value {
	span_start840 := int64(p.spanStart())
	var _t1542 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1542 = 12
	} else {
		var _t1543 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1543 = 11
		} else {
			var _t1544 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1544 = 12
			} else {
				var _t1545 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1546 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1546 = 1
					} else {
						var _t1547 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1547 = 0
						} else {
							_t1547 = -1
						}
						_t1546 = _t1547
					}
					_t1545 = _t1546
				} else {
					var _t1548 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1548 = 7
					} else {
						var _t1549 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1549 = 8
						} else {
							var _t1550 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1550 = 2
							} else {
								var _t1551 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1551 = 3
								} else {
									var _t1552 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1552 = 9
									} else {
										var _t1553 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1553 = 4
										} else {
											var _t1554 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1554 = 5
											} else {
												var _t1555 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1555 = 6
												} else {
													var _t1556 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1556 = 10
													} else {
														_t1556 = -1
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
					_t1545 = _t1548
				}
				_t1544 = _t1545
			}
			_t1543 = _t1544
		}
		_t1542 = _t1543
	}
	prediction827 := _t1542
	var _t1557 *pb.Value
	if prediction827 == 12 {
		_t1558 := p.parse_boolean_value()
		boolean_value839 := _t1558
		_t1559 := &pb.Value{}
		_t1559.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value839}
		_t1557 = _t1559
	} else {
		var _t1560 *pb.Value
		if prediction827 == 11 {
			p.consumeLiteral("missing")
			_t1561 := &pb.MissingValue{}
			_t1562 := &pb.Value{}
			_t1562.Value = &pb.Value_MissingValue{MissingValue: _t1561}
			_t1560 = _t1562
		} else {
			var _t1563 *pb.Value
			if prediction827 == 10 {
				formatted_decimal838 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1564 := &pb.Value{}
				_t1564.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal838}
				_t1563 = _t1564
			} else {
				var _t1565 *pb.Value
				if prediction827 == 9 {
					formatted_int128837 := p.consumeTerminal("INT128").Value.int128
					_t1566 := &pb.Value{}
					_t1566.Value = &pb.Value_Int128Value{Int128Value: formatted_int128837}
					_t1565 = _t1566
				} else {
					var _t1567 *pb.Value
					if prediction827 == 8 {
						formatted_uint128836 := p.consumeTerminal("UINT128").Value.uint128
						_t1568 := &pb.Value{}
						_t1568.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128836}
						_t1567 = _t1568
					} else {
						var _t1569 *pb.Value
						if prediction827 == 7 {
							formatted_uint32835 := p.consumeTerminal("UINT32").Value.u32
							_t1570 := &pb.Value{}
							_t1570.Value = &pb.Value_Uint32Value{Uint32Value: formatted_uint32835}
							_t1569 = _t1570
						} else {
							var _t1571 *pb.Value
							if prediction827 == 6 {
								formatted_float834 := p.consumeTerminal("FLOAT").Value.f64
								_t1572 := &pb.Value{}
								_t1572.Value = &pb.Value_FloatValue{FloatValue: formatted_float834}
								_t1571 = _t1572
							} else {
								var _t1573 *pb.Value
								if prediction827 == 5 {
									formatted_float32833 := p.consumeTerminal("FLOAT32").Value.f32
									_t1574 := &pb.Value{}
									_t1574.Value = &pb.Value_Float32Value{Float32Value: formatted_float32833}
									_t1573 = _t1574
								} else {
									var _t1575 *pb.Value
									if prediction827 == 4 {
										formatted_int832 := p.consumeTerminal("INT").Value.i64
										_t1576 := &pb.Value{}
										_t1576.Value = &pb.Value_IntValue{IntValue: formatted_int832}
										_t1575 = _t1576
									} else {
										var _t1577 *pb.Value
										if prediction827 == 3 {
											formatted_int32831 := p.consumeTerminal("INT32").Value.i32
											_t1578 := &pb.Value{}
											_t1578.Value = &pb.Value_Int32Value{Int32Value: formatted_int32831}
											_t1577 = _t1578
										} else {
											var _t1579 *pb.Value
											if prediction827 == 2 {
												formatted_string830 := p.consumeTerminal("STRING").Value.str
												_t1580 := &pb.Value{}
												_t1580.Value = &pb.Value_StringValue{StringValue: formatted_string830}
												_t1579 = _t1580
											} else {
												var _t1581 *pb.Value
												if prediction827 == 1 {
													_t1582 := p.parse_datetime()
													datetime829 := _t1582
													_t1583 := &pb.Value{}
													_t1583.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime829}
													_t1581 = _t1583
												} else {
													var _t1584 *pb.Value
													if prediction827 == 0 {
														_t1585 := p.parse_date()
														date828 := _t1585
														_t1586 := &pb.Value{}
														_t1586.Value = &pb.Value_DateValue{DateValue: date828}
														_t1584 = _t1586
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1581 = _t1584
												}
												_t1579 = _t1581
											}
											_t1577 = _t1579
										}
										_t1575 = _t1577
									}
									_t1573 = _t1575
								}
								_t1571 = _t1573
							}
							_t1569 = _t1571
						}
						_t1567 = _t1569
					}
					_t1565 = _t1567
				}
				_t1563 = _t1565
			}
			_t1560 = _t1563
		}
		_t1557 = _t1560
	}
	result841 := _t1557
	p.recordSpan(int(span_start840), "Value")
	return result841
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int842 := p.consumeTerminal("INT").Value.i64
	formatted_int_3843 := p.consumeTerminal("INT").Value.i64
	formatted_int_4844 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1587 := &pb.DateValue{Year: int32(formatted_int842), Month: int32(formatted_int_3843), Day: int32(formatted_int_4844)}
	result846 := _t1587
	p.recordSpan(int(span_start845), "DateValue")
	return result846
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start854 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int847 := p.consumeTerminal("INT").Value.i64
	formatted_int_3848 := p.consumeTerminal("INT").Value.i64
	formatted_int_4849 := p.consumeTerminal("INT").Value.i64
	formatted_int_5850 := p.consumeTerminal("INT").Value.i64
	formatted_int_6851 := p.consumeTerminal("INT").Value.i64
	formatted_int_7852 := p.consumeTerminal("INT").Value.i64
	var _t1588 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1588 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8853 := _t1588
	p.consumeLiteral(")")
	_t1589 := &pb.DateTimeValue{Year: int32(formatted_int847), Month: int32(formatted_int_3848), Day: int32(formatted_int_4849), Hour: int32(formatted_int_5850), Minute: int32(formatted_int_6851), Second: int32(formatted_int_7852), Microsecond: int32(deref(formatted_int_8853, 0))}
	result855 := _t1589
	p.recordSpan(int(span_start854), "DateTimeValue")
	return result855
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start860 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs856 := []*pb.Formula{}
	cond857 := p.matchLookaheadLiteral("(", 0)
	for cond857 {
		_t1590 := p.parse_formula()
		item858 := _t1590
		xs856 = append(xs856, item858)
		cond857 = p.matchLookaheadLiteral("(", 0)
	}
	formulas859 := xs856
	p.consumeLiteral(")")
	_t1591 := &pb.Conjunction{Args: formulas859}
	result861 := _t1591
	p.recordSpan(int(span_start860), "Conjunction")
	return result861
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs862 := []*pb.Formula{}
	cond863 := p.matchLookaheadLiteral("(", 0)
	for cond863 {
		_t1592 := p.parse_formula()
		item864 := _t1592
		xs862 = append(xs862, item864)
		cond863 = p.matchLookaheadLiteral("(", 0)
	}
	formulas865 := xs862
	p.consumeLiteral(")")
	_t1593 := &pb.Disjunction{Args: formulas865}
	result867 := _t1593
	p.recordSpan(int(span_start866), "Disjunction")
	return result867
}

func (p *Parser) parse_not() *pb.Not {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1594 := p.parse_formula()
	formula868 := _t1594
	p.consumeLiteral(")")
	_t1595 := &pb.Not{Arg: formula868}
	result870 := _t1595
	p.recordSpan(int(span_start869), "Not")
	return result870
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start874 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1596 := p.parse_name()
	name871 := _t1596
	_t1597 := p.parse_ffi_args()
	ffi_args872 := _t1597
	_t1598 := p.parse_terms()
	terms873 := _t1598
	p.consumeLiteral(")")
	_t1599 := &pb.FFI{Name: name871, Args: ffi_args872, Terms: terms873}
	result875 := _t1599
	p.recordSpan(int(span_start874), "FFI")
	return result875
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol876 := p.consumeTerminal("SYMBOL").Value.str
	return symbol876
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs877 := []*pb.Abstraction{}
	cond878 := p.matchLookaheadLiteral("(", 0)
	for cond878 {
		_t1600 := p.parse_abstraction()
		item879 := _t1600
		xs877 = append(xs877, item879)
		cond878 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions880 := xs877
	p.consumeLiteral(")")
	return abstractions880
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start886 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1601 := p.parse_relation_id()
	relation_id881 := _t1601
	xs882 := []*pb.Term{}
	cond883 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond883 {
		_t1602 := p.parse_term()
		item884 := _t1602
		xs882 = append(xs882, item884)
		cond883 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms885 := xs882
	p.consumeLiteral(")")
	_t1603 := &pb.Atom{Name: relation_id881, Terms: terms885}
	result887 := _t1603
	p.recordSpan(int(span_start886), "Atom")
	return result887
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start893 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1604 := p.parse_name()
	name888 := _t1604
	xs889 := []*pb.Term{}
	cond890 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond890 {
		_t1605 := p.parse_term()
		item891 := _t1605
		xs889 = append(xs889, item891)
		cond890 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms892 := xs889
	p.consumeLiteral(")")
	_t1606 := &pb.Pragma{Name: name888, Terms: terms892}
	result894 := _t1606
	p.recordSpan(int(span_start893), "Pragma")
	return result894
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start910 := int64(p.spanStart())
	var _t1607 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1608 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1608 = 9
		} else {
			var _t1609 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1609 = 4
			} else {
				var _t1610 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1610 = 3
				} else {
					var _t1611 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1611 = 0
					} else {
						var _t1612 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1612 = 2
						} else {
							var _t1613 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1613 = 1
							} else {
								var _t1614 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1614 = 8
								} else {
									var _t1615 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1615 = 6
									} else {
										var _t1616 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1616 = 5
										} else {
											var _t1617 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1617 = 7
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
			_t1608 = _t1609
		}
		_t1607 = _t1608
	} else {
		_t1607 = -1
	}
	prediction895 := _t1607
	var _t1618 *pb.Primitive
	if prediction895 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1619 := p.parse_name()
		name905 := _t1619
		xs906 := []*pb.RelTerm{}
		cond907 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond907 {
			_t1620 := p.parse_rel_term()
			item908 := _t1620
			xs906 = append(xs906, item908)
			cond907 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms909 := xs906
		p.consumeLiteral(")")
		_t1621 := &pb.Primitive{Name: name905, Terms: rel_terms909}
		_t1618 = _t1621
	} else {
		var _t1622 *pb.Primitive
		if prediction895 == 8 {
			_t1623 := p.parse_divide()
			divide904 := _t1623
			_t1622 = divide904
		} else {
			var _t1624 *pb.Primitive
			if prediction895 == 7 {
				_t1625 := p.parse_multiply()
				multiply903 := _t1625
				_t1624 = multiply903
			} else {
				var _t1626 *pb.Primitive
				if prediction895 == 6 {
					_t1627 := p.parse_minus()
					minus902 := _t1627
					_t1626 = minus902
				} else {
					var _t1628 *pb.Primitive
					if prediction895 == 5 {
						_t1629 := p.parse_add()
						add901 := _t1629
						_t1628 = add901
					} else {
						var _t1630 *pb.Primitive
						if prediction895 == 4 {
							_t1631 := p.parse_gt_eq()
							gt_eq900 := _t1631
							_t1630 = gt_eq900
						} else {
							var _t1632 *pb.Primitive
							if prediction895 == 3 {
								_t1633 := p.parse_gt()
								gt899 := _t1633
								_t1632 = gt899
							} else {
								var _t1634 *pb.Primitive
								if prediction895 == 2 {
									_t1635 := p.parse_lt_eq()
									lt_eq898 := _t1635
									_t1634 = lt_eq898
								} else {
									var _t1636 *pb.Primitive
									if prediction895 == 1 {
										_t1637 := p.parse_lt()
										lt897 := _t1637
										_t1636 = lt897
									} else {
										var _t1638 *pb.Primitive
										if prediction895 == 0 {
											_t1639 := p.parse_eq()
											eq896 := _t1639
											_t1638 = eq896
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1622 = _t1624
		}
		_t1618 = _t1622
	}
	result911 := _t1618
	p.recordSpan(int(span_start910), "Primitive")
	return result911
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start914 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1640 := p.parse_term()
	term912 := _t1640
	_t1641 := p.parse_term()
	term_3913 := _t1641
	p.consumeLiteral(")")
	_t1642 := &pb.RelTerm{}
	_t1642.RelTermType = &pb.RelTerm_Term{Term: term912}
	_t1643 := &pb.RelTerm{}
	_t1643.RelTermType = &pb.RelTerm_Term{Term: term_3913}
	_t1644 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1642, _t1643}}
	result915 := _t1644
	p.recordSpan(int(span_start914), "Primitive")
	return result915
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1645 := p.parse_term()
	term916 := _t1645
	_t1646 := p.parse_term()
	term_3917 := _t1646
	p.consumeLiteral(")")
	_t1647 := &pb.RelTerm{}
	_t1647.RelTermType = &pb.RelTerm_Term{Term: term916}
	_t1648 := &pb.RelTerm{}
	_t1648.RelTermType = &pb.RelTerm_Term{Term: term_3917}
	_t1649 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1647, _t1648}}
	result919 := _t1649
	p.recordSpan(int(span_start918), "Primitive")
	return result919
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start922 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1650 := p.parse_term()
	term920 := _t1650
	_t1651 := p.parse_term()
	term_3921 := _t1651
	p.consumeLiteral(")")
	_t1652 := &pb.RelTerm{}
	_t1652.RelTermType = &pb.RelTerm_Term{Term: term920}
	_t1653 := &pb.RelTerm{}
	_t1653.RelTermType = &pb.RelTerm_Term{Term: term_3921}
	_t1654 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1652, _t1653}}
	result923 := _t1654
	p.recordSpan(int(span_start922), "Primitive")
	return result923
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start926 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1655 := p.parse_term()
	term924 := _t1655
	_t1656 := p.parse_term()
	term_3925 := _t1656
	p.consumeLiteral(")")
	_t1657 := &pb.RelTerm{}
	_t1657.RelTermType = &pb.RelTerm_Term{Term: term924}
	_t1658 := &pb.RelTerm{}
	_t1658.RelTermType = &pb.RelTerm_Term{Term: term_3925}
	_t1659 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1657, _t1658}}
	result927 := _t1659
	p.recordSpan(int(span_start926), "Primitive")
	return result927
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start930 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1660 := p.parse_term()
	term928 := _t1660
	_t1661 := p.parse_term()
	term_3929 := _t1661
	p.consumeLiteral(")")
	_t1662 := &pb.RelTerm{}
	_t1662.RelTermType = &pb.RelTerm_Term{Term: term928}
	_t1663 := &pb.RelTerm{}
	_t1663.RelTermType = &pb.RelTerm_Term{Term: term_3929}
	_t1664 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1662, _t1663}}
	result931 := _t1664
	p.recordSpan(int(span_start930), "Primitive")
	return result931
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start935 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1665 := p.parse_term()
	term932 := _t1665
	_t1666 := p.parse_term()
	term_3933 := _t1666
	_t1667 := p.parse_term()
	term_4934 := _t1667
	p.consumeLiteral(")")
	_t1668 := &pb.RelTerm{}
	_t1668.RelTermType = &pb.RelTerm_Term{Term: term932}
	_t1669 := &pb.RelTerm{}
	_t1669.RelTermType = &pb.RelTerm_Term{Term: term_3933}
	_t1670 := &pb.RelTerm{}
	_t1670.RelTermType = &pb.RelTerm_Term{Term: term_4934}
	_t1671 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1668, _t1669, _t1670}}
	result936 := _t1671
	p.recordSpan(int(span_start935), "Primitive")
	return result936
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start940 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1672 := p.parse_term()
	term937 := _t1672
	_t1673 := p.parse_term()
	term_3938 := _t1673
	_t1674 := p.parse_term()
	term_4939 := _t1674
	p.consumeLiteral(")")
	_t1675 := &pb.RelTerm{}
	_t1675.RelTermType = &pb.RelTerm_Term{Term: term937}
	_t1676 := &pb.RelTerm{}
	_t1676.RelTermType = &pb.RelTerm_Term{Term: term_3938}
	_t1677 := &pb.RelTerm{}
	_t1677.RelTermType = &pb.RelTerm_Term{Term: term_4939}
	_t1678 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1675, _t1676, _t1677}}
	result941 := _t1678
	p.recordSpan(int(span_start940), "Primitive")
	return result941
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start945 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1679 := p.parse_term()
	term942 := _t1679
	_t1680 := p.parse_term()
	term_3943 := _t1680
	_t1681 := p.parse_term()
	term_4944 := _t1681
	p.consumeLiteral(")")
	_t1682 := &pb.RelTerm{}
	_t1682.RelTermType = &pb.RelTerm_Term{Term: term942}
	_t1683 := &pb.RelTerm{}
	_t1683.RelTermType = &pb.RelTerm_Term{Term: term_3943}
	_t1684 := &pb.RelTerm{}
	_t1684.RelTermType = &pb.RelTerm_Term{Term: term_4944}
	_t1685 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1682, _t1683, _t1684}}
	result946 := _t1685
	p.recordSpan(int(span_start945), "Primitive")
	return result946
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start950 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1686 := p.parse_term()
	term947 := _t1686
	_t1687 := p.parse_term()
	term_3948 := _t1687
	_t1688 := p.parse_term()
	term_4949 := _t1688
	p.consumeLiteral(")")
	_t1689 := &pb.RelTerm{}
	_t1689.RelTermType = &pb.RelTerm_Term{Term: term947}
	_t1690 := &pb.RelTerm{}
	_t1690.RelTermType = &pb.RelTerm_Term{Term: term_3948}
	_t1691 := &pb.RelTerm{}
	_t1691.RelTermType = &pb.RelTerm_Term{Term: term_4949}
	_t1692 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1689, _t1690, _t1691}}
	result951 := _t1692
	p.recordSpan(int(span_start950), "Primitive")
	return result951
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start955 := int64(p.spanStart())
	var _t1693 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1693 = 1
	} else {
		var _t1694 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1694 = 1
		} else {
			var _t1695 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1695 = 1
			} else {
				var _t1696 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1696 = 1
				} else {
					var _t1697 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1697 = 0
					} else {
						var _t1698 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1698 = 1
						} else {
							var _t1699 int64
							if p.matchLookaheadTerminal("UINT32", 0) {
								_t1699 = 1
							} else {
								var _t1700 int64
								if p.matchLookaheadTerminal("UINT128", 0) {
									_t1700 = 1
								} else {
									var _t1701 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1701 = 1
									} else {
										var _t1702 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1702 = 1
										} else {
											var _t1703 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1703 = 1
											} else {
												var _t1704 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1704 = 1
												} else {
													var _t1705 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1705 = 1
													} else {
														var _t1706 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1706 = 1
														} else {
															var _t1707 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1707 = 1
															} else {
																_t1707 = -1
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
								}
								_t1699 = _t1700
							}
							_t1698 = _t1699
						}
						_t1697 = _t1698
					}
					_t1696 = _t1697
				}
				_t1695 = _t1696
			}
			_t1694 = _t1695
		}
		_t1693 = _t1694
	}
	prediction952 := _t1693
	var _t1708 *pb.RelTerm
	if prediction952 == 1 {
		_t1709 := p.parse_term()
		term954 := _t1709
		_t1710 := &pb.RelTerm{}
		_t1710.RelTermType = &pb.RelTerm_Term{Term: term954}
		_t1708 = _t1710
	} else {
		var _t1711 *pb.RelTerm
		if prediction952 == 0 {
			_t1712 := p.parse_specialized_value()
			specialized_value953 := _t1712
			_t1713 := &pb.RelTerm{}
			_t1713.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value953}
			_t1711 = _t1713
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1708 = _t1711
	}
	result956 := _t1708
	p.recordSpan(int(span_start955), "RelTerm")
	return result956
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start958 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1714 := p.parse_raw_value()
	raw_value957 := _t1714
	result959 := raw_value957
	p.recordSpan(int(span_start958), "Value")
	return result959
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1715 := p.parse_name()
	name960 := _t1715
	xs961 := []*pb.RelTerm{}
	cond962 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond962 {
		_t1716 := p.parse_rel_term()
		item963 := _t1716
		xs961 = append(xs961, item963)
		cond962 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms964 := xs961
	p.consumeLiteral(")")
	_t1717 := &pb.RelAtom{Name: name960, Terms: rel_terms964}
	result966 := _t1717
	p.recordSpan(int(span_start965), "RelAtom")
	return result966
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1718 := p.parse_term()
	term967 := _t1718
	_t1719 := p.parse_term()
	term_3968 := _t1719
	p.consumeLiteral(")")
	_t1720 := &pb.Cast{Input: term967, Result: term_3968}
	result970 := _t1720
	p.recordSpan(int(span_start969), "Cast")
	return result970
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs971 := []*pb.Attribute{}
	cond972 := p.matchLookaheadLiteral("(", 0)
	for cond972 {
		_t1721 := p.parse_attribute()
		item973 := _t1721
		xs971 = append(xs971, item973)
		cond972 = p.matchLookaheadLiteral("(", 0)
	}
	attributes974 := xs971
	p.consumeLiteral(")")
	return attributes974
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1722 := p.parse_name()
	name975 := _t1722
	xs976 := []*pb.Value{}
	cond977 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond977 {
		_t1723 := p.parse_raw_value()
		item978 := _t1723
		xs976 = append(xs976, item978)
		cond977 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	raw_values979 := xs976
	p.consumeLiteral(")")
	_t1724 := &pb.Attribute{Name: name975, Args: raw_values979}
	result981 := _t1724
	p.recordSpan(int(span_start980), "Attribute")
	return result981
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start987 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs982 := []*pb.RelationId{}
	cond983 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond983 {
		_t1725 := p.parse_relation_id()
		item984 := _t1725
		xs982 = append(xs982, item984)
		cond983 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids985 := xs982
	_t1726 := p.parse_script()
	script986 := _t1726
	p.consumeLiteral(")")
	_t1727 := &pb.Algorithm{Global: relation_ids985, Body: script986}
	result988 := _t1727
	p.recordSpan(int(span_start987), "Algorithm")
	return result988
}

func (p *Parser) parse_script() *pb.Script {
	span_start993 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs989 := []*pb.Construct{}
	cond990 := p.matchLookaheadLiteral("(", 0)
	for cond990 {
		_t1728 := p.parse_construct()
		item991 := _t1728
		xs989 = append(xs989, item991)
		cond990 = p.matchLookaheadLiteral("(", 0)
	}
	constructs992 := xs989
	p.consumeLiteral(")")
	_t1729 := &pb.Script{Constructs: constructs992}
	result994 := _t1729
	p.recordSpan(int(span_start993), "Script")
	return result994
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start998 := int64(p.spanStart())
	var _t1730 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1731 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1731 = 1
		} else {
			var _t1732 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1732 = 1
			} else {
				var _t1733 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1733 = 1
				} else {
					var _t1734 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1734 = 0
					} else {
						var _t1735 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1735 = 1
						} else {
							var _t1736 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1736 = 1
							} else {
								_t1736 = -1
							}
							_t1735 = _t1736
						}
						_t1734 = _t1735
					}
					_t1733 = _t1734
				}
				_t1732 = _t1733
			}
			_t1731 = _t1732
		}
		_t1730 = _t1731
	} else {
		_t1730 = -1
	}
	prediction995 := _t1730
	var _t1737 *pb.Construct
	if prediction995 == 1 {
		_t1738 := p.parse_instruction()
		instruction997 := _t1738
		_t1739 := &pb.Construct{}
		_t1739.ConstructType = &pb.Construct_Instruction{Instruction: instruction997}
		_t1737 = _t1739
	} else {
		var _t1740 *pb.Construct
		if prediction995 == 0 {
			_t1741 := p.parse_loop()
			loop996 := _t1741
			_t1742 := &pb.Construct{}
			_t1742.ConstructType = &pb.Construct_Loop{Loop: loop996}
			_t1740 = _t1742
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1737 = _t1740
	}
	result999 := _t1737
	p.recordSpan(int(span_start998), "Construct")
	return result999
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1002 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1743 := p.parse_init()
	init1000 := _t1743
	_t1744 := p.parse_script()
	script1001 := _t1744
	p.consumeLiteral(")")
	_t1745 := &pb.Loop{Init: init1000, Body: script1001}
	result1003 := _t1745
	p.recordSpan(int(span_start1002), "Loop")
	return result1003
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1004 := []*pb.Instruction{}
	cond1005 := p.matchLookaheadLiteral("(", 0)
	for cond1005 {
		_t1746 := p.parse_instruction()
		item1006 := _t1746
		xs1004 = append(xs1004, item1006)
		cond1005 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1007 := xs1004
	p.consumeLiteral(")")
	return instructions1007
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1014 := int64(p.spanStart())
	var _t1747 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1748 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1748 = 1
		} else {
			var _t1749 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1749 = 4
			} else {
				var _t1750 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1750 = 3
				} else {
					var _t1751 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1751 = 2
					} else {
						var _t1752 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1752 = 0
						} else {
							_t1752 = -1
						}
						_t1751 = _t1752
					}
					_t1750 = _t1751
				}
				_t1749 = _t1750
			}
			_t1748 = _t1749
		}
		_t1747 = _t1748
	} else {
		_t1747 = -1
	}
	prediction1008 := _t1747
	var _t1753 *pb.Instruction
	if prediction1008 == 4 {
		_t1754 := p.parse_monus_def()
		monus_def1013 := _t1754
		_t1755 := &pb.Instruction{}
		_t1755.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1013}
		_t1753 = _t1755
	} else {
		var _t1756 *pb.Instruction
		if prediction1008 == 3 {
			_t1757 := p.parse_monoid_def()
			monoid_def1012 := _t1757
			_t1758 := &pb.Instruction{}
			_t1758.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1012}
			_t1756 = _t1758
		} else {
			var _t1759 *pb.Instruction
			if prediction1008 == 2 {
				_t1760 := p.parse_break()
				break1011 := _t1760
				_t1761 := &pb.Instruction{}
				_t1761.InstrType = &pb.Instruction_Break{Break: break1011}
				_t1759 = _t1761
			} else {
				var _t1762 *pb.Instruction
				if prediction1008 == 1 {
					_t1763 := p.parse_upsert()
					upsert1010 := _t1763
					_t1764 := &pb.Instruction{}
					_t1764.InstrType = &pb.Instruction_Upsert{Upsert: upsert1010}
					_t1762 = _t1764
				} else {
					var _t1765 *pb.Instruction
					if prediction1008 == 0 {
						_t1766 := p.parse_assign()
						assign1009 := _t1766
						_t1767 := &pb.Instruction{}
						_t1767.InstrType = &pb.Instruction_Assign{Assign: assign1009}
						_t1765 = _t1767
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1762 = _t1765
				}
				_t1759 = _t1762
			}
			_t1756 = _t1759
		}
		_t1753 = _t1756
	}
	result1015 := _t1753
	p.recordSpan(int(span_start1014), "Instruction")
	return result1015
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1019 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1768 := p.parse_relation_id()
	relation_id1016 := _t1768
	_t1769 := p.parse_abstraction()
	abstraction1017 := _t1769
	var _t1770 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1771 := p.parse_attrs()
		_t1770 = _t1771
	}
	attrs1018 := _t1770
	p.consumeLiteral(")")
	_t1772 := attrs1018
	if attrs1018 == nil {
		_t1772 = []*pb.Attribute{}
	}
	_t1773 := &pb.Assign{Name: relation_id1016, Body: abstraction1017, Attrs: _t1772}
	result1020 := _t1773
	p.recordSpan(int(span_start1019), "Assign")
	return result1020
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1774 := p.parse_relation_id()
	relation_id1021 := _t1774
	_t1775 := p.parse_abstraction_with_arity()
	abstraction_with_arity1022 := _t1775
	var _t1776 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1777 := p.parse_attrs()
		_t1776 = _t1777
	}
	attrs1023 := _t1776
	p.consumeLiteral(")")
	_t1778 := attrs1023
	if attrs1023 == nil {
		_t1778 = []*pb.Attribute{}
	}
	_t1779 := &pb.Upsert{Name: relation_id1021, Body: abstraction_with_arity1022[0].(*pb.Abstraction), Attrs: _t1778, ValueArity: abstraction_with_arity1022[1].(int64)}
	result1025 := _t1779
	p.recordSpan(int(span_start1024), "Upsert")
	return result1025
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1780 := p.parse_bindings()
	bindings1026 := _t1780
	_t1781 := p.parse_formula()
	formula1027 := _t1781
	p.consumeLiteral(")")
	_t1782 := &pb.Abstraction{Vars: listConcat(bindings1026[0].([]*pb.Binding), bindings1026[1].([]*pb.Binding)), Value: formula1027}
	return []interface{}{_t1782, int64(len(bindings1026[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1783 := p.parse_relation_id()
	relation_id1028 := _t1783
	_t1784 := p.parse_abstraction()
	abstraction1029 := _t1784
	var _t1785 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1786 := p.parse_attrs()
		_t1785 = _t1786
	}
	attrs1030 := _t1785
	p.consumeLiteral(")")
	_t1787 := attrs1030
	if attrs1030 == nil {
		_t1787 = []*pb.Attribute{}
	}
	_t1788 := &pb.Break{Name: relation_id1028, Body: abstraction1029, Attrs: _t1787}
	result1032 := _t1788
	p.recordSpan(int(span_start1031), "Break")
	return result1032
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1037 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1789 := p.parse_monoid()
	monoid1033 := _t1789
	_t1790 := p.parse_relation_id()
	relation_id1034 := _t1790
	_t1791 := p.parse_abstraction_with_arity()
	abstraction_with_arity1035 := _t1791
	var _t1792 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1793 := p.parse_attrs()
		_t1792 = _t1793
	}
	attrs1036 := _t1792
	p.consumeLiteral(")")
	_t1794 := attrs1036
	if attrs1036 == nil {
		_t1794 = []*pb.Attribute{}
	}
	_t1795 := &pb.MonoidDef{Monoid: monoid1033, Name: relation_id1034, Body: abstraction_with_arity1035[0].(*pb.Abstraction), Attrs: _t1794, ValueArity: abstraction_with_arity1035[1].(int64)}
	result1038 := _t1795
	p.recordSpan(int(span_start1037), "MonoidDef")
	return result1038
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1044 := int64(p.spanStart())
	var _t1796 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1797 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1797 = 3
		} else {
			var _t1798 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1798 = 0
			} else {
				var _t1799 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1799 = 1
				} else {
					var _t1800 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1800 = 2
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
	} else {
		_t1796 = -1
	}
	prediction1039 := _t1796
	var _t1801 *pb.Monoid
	if prediction1039 == 3 {
		_t1802 := p.parse_sum_monoid()
		sum_monoid1043 := _t1802
		_t1803 := &pb.Monoid{}
		_t1803.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1043}
		_t1801 = _t1803
	} else {
		var _t1804 *pb.Monoid
		if prediction1039 == 2 {
			_t1805 := p.parse_max_monoid()
			max_monoid1042 := _t1805
			_t1806 := &pb.Monoid{}
			_t1806.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1042}
			_t1804 = _t1806
		} else {
			var _t1807 *pb.Monoid
			if prediction1039 == 1 {
				_t1808 := p.parse_min_monoid()
				min_monoid1041 := _t1808
				_t1809 := &pb.Monoid{}
				_t1809.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1041}
				_t1807 = _t1809
			} else {
				var _t1810 *pb.Monoid
				if prediction1039 == 0 {
					_t1811 := p.parse_or_monoid()
					or_monoid1040 := _t1811
					_t1812 := &pb.Monoid{}
					_t1812.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1040}
					_t1810 = _t1812
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1807 = _t1810
			}
			_t1804 = _t1807
		}
		_t1801 = _t1804
	}
	result1045 := _t1801
	p.recordSpan(int(span_start1044), "Monoid")
	return result1045
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1046 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1813 := &pb.OrMonoid{}
	result1047 := _t1813
	p.recordSpan(int(span_start1046), "OrMonoid")
	return result1047
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1049 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1814 := p.parse_type()
	type1048 := _t1814
	p.consumeLiteral(")")
	_t1815 := &pb.MinMonoid{Type: type1048}
	result1050 := _t1815
	p.recordSpan(int(span_start1049), "MinMonoid")
	return result1050
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1816 := p.parse_type()
	type1051 := _t1816
	p.consumeLiteral(")")
	_t1817 := &pb.MaxMonoid{Type: type1051}
	result1053 := _t1817
	p.recordSpan(int(span_start1052), "MaxMonoid")
	return result1053
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1055 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1818 := p.parse_type()
	type1054 := _t1818
	p.consumeLiteral(")")
	_t1819 := &pb.SumMonoid{Type: type1054}
	result1056 := _t1819
	p.recordSpan(int(span_start1055), "SumMonoid")
	return result1056
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1061 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1820 := p.parse_monoid()
	monoid1057 := _t1820
	_t1821 := p.parse_relation_id()
	relation_id1058 := _t1821
	_t1822 := p.parse_abstraction_with_arity()
	abstraction_with_arity1059 := _t1822
	var _t1823 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1824 := p.parse_attrs()
		_t1823 = _t1824
	}
	attrs1060 := _t1823
	p.consumeLiteral(")")
	_t1825 := attrs1060
	if attrs1060 == nil {
		_t1825 = []*pb.Attribute{}
	}
	_t1826 := &pb.MonusDef{Monoid: monoid1057, Name: relation_id1058, Body: abstraction_with_arity1059[0].(*pb.Abstraction), Attrs: _t1825, ValueArity: abstraction_with_arity1059[1].(int64)}
	result1062 := _t1826
	p.recordSpan(int(span_start1061), "MonusDef")
	return result1062
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1067 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1827 := p.parse_relation_id()
	relation_id1063 := _t1827
	_t1828 := p.parse_abstraction()
	abstraction1064 := _t1828
	_t1829 := p.parse_functional_dependency_keys()
	functional_dependency_keys1065 := _t1829
	_t1830 := p.parse_functional_dependency_values()
	functional_dependency_values1066 := _t1830
	p.consumeLiteral(")")
	_t1831 := &pb.FunctionalDependency{Guard: abstraction1064, Keys: functional_dependency_keys1065, Values: functional_dependency_values1066}
	_t1832 := &pb.Constraint{Name: relation_id1063}
	_t1832.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1831}
	result1068 := _t1832
	p.recordSpan(int(span_start1067), "Constraint")
	return result1068
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1069 := []*pb.Var{}
	cond1070 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1070 {
		_t1833 := p.parse_var()
		item1071 := _t1833
		xs1069 = append(xs1069, item1071)
		cond1070 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1072 := xs1069
	p.consumeLiteral(")")
	return vars1072
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1073 := []*pb.Var{}
	cond1074 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1074 {
		_t1834 := p.parse_var()
		item1075 := _t1834
		xs1073 = append(xs1073, item1075)
		cond1074 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1076 := xs1073
	p.consumeLiteral(")")
	return vars1076
}

func (p *Parser) parse_data() *pb.Data {
	span_start1081 := int64(p.spanStart())
	var _t1835 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1836 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1836 = 0
		} else {
			var _t1837 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1837 = 2
			} else {
				var _t1838 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1838 = 1
				} else {
					_t1838 = -1
				}
				_t1837 = _t1838
			}
			_t1836 = _t1837
		}
		_t1835 = _t1836
	} else {
		_t1835 = -1
	}
	prediction1077 := _t1835
	var _t1839 *pb.Data
	if prediction1077 == 2 {
		_t1840 := p.parse_csv_data()
		csv_data1080 := _t1840
		_t1841 := &pb.Data{}
		_t1841.DataType = &pb.Data_CsvData{CsvData: csv_data1080}
		_t1839 = _t1841
	} else {
		var _t1842 *pb.Data
		if prediction1077 == 1 {
			_t1843 := p.parse_betree_relation()
			betree_relation1079 := _t1843
			_t1844 := &pb.Data{}
			_t1844.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1079}
			_t1842 = _t1844
		} else {
			var _t1845 *pb.Data
			if prediction1077 == 0 {
				_t1846 := p.parse_edb()
				edb1078 := _t1846
				_t1847 := &pb.Data{}
				_t1847.DataType = &pb.Data_Edb{Edb: edb1078}
				_t1845 = _t1847
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1842 = _t1845
		}
		_t1839 = _t1842
	}
	result1082 := _t1839
	p.recordSpan(int(span_start1081), "Data")
	return result1082
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1848 := p.parse_relation_id()
	relation_id1083 := _t1848
	_t1849 := p.parse_edb_path()
	edb_path1084 := _t1849
	_t1850 := p.parse_edb_types()
	edb_types1085 := _t1850
	p.consumeLiteral(")")
	_t1851 := &pb.EDB{TargetId: relation_id1083, Path: edb_path1084, Types: edb_types1085}
	result1087 := _t1851
	p.recordSpan(int(span_start1086), "EDB")
	return result1087
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1088 := []string{}
	cond1089 := p.matchLookaheadTerminal("STRING", 0)
	for cond1089 {
		item1090 := p.consumeTerminal("STRING").Value.str
		xs1088 = append(xs1088, item1090)
		cond1089 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1091 := xs1088
	p.consumeLiteral("]")
	return strings1091
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1092 := []*pb.Type{}
	cond1093 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1093 {
		_t1852 := p.parse_type()
		item1094 := _t1852
		xs1092 = append(xs1092, item1094)
		cond1093 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1095 := xs1092
	p.consumeLiteral("]")
	return types1095
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1098 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1853 := p.parse_relation_id()
	relation_id1096 := _t1853
	_t1854 := p.parse_betree_info()
	betree_info1097 := _t1854
	p.consumeLiteral(")")
	_t1855 := &pb.BeTreeRelation{Name: relation_id1096, RelationInfo: betree_info1097}
	result1099 := _t1855
	p.recordSpan(int(span_start1098), "BeTreeRelation")
	return result1099
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1856 := p.parse_betree_info_key_types()
	betree_info_key_types1100 := _t1856
	_t1857 := p.parse_betree_info_value_types()
	betree_info_value_types1101 := _t1857
	_t1858 := p.parse_config_dict()
	config_dict1102 := _t1858
	p.consumeLiteral(")")
	_t1859 := p.construct_betree_info(betree_info_key_types1100, betree_info_value_types1101, config_dict1102)
	result1104 := _t1859
	p.recordSpan(int(span_start1103), "BeTreeInfo")
	return result1104
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1105 := []*pb.Type{}
	cond1106 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1106 {
		_t1860 := p.parse_type()
		item1107 := _t1860
		xs1105 = append(xs1105, item1107)
		cond1106 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1108 := xs1105
	p.consumeLiteral(")")
	return types1108
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1109 := []*pb.Type{}
	cond1110 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1110 {
		_t1861 := p.parse_type()
		item1111 := _t1861
		xs1109 = append(xs1109, item1111)
		cond1110 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1112 := xs1109
	p.consumeLiteral(")")
	return types1112
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1862 := p.parse_csvlocator()
	csvlocator1113 := _t1862
	_t1863 := p.parse_csv_config()
	csv_config1114 := _t1863
	_t1864 := p.parse_gnf_columns()
	gnf_columns1115 := _t1864
	_t1865 := p.parse_csv_asof()
	csv_asof1116 := _t1865
	p.consumeLiteral(")")
	_t1866 := &pb.CSVData{Locator: csvlocator1113, Config: csv_config1114, Columns: gnf_columns1115, Asof: csv_asof1116}
	result1118 := _t1866
	p.recordSpan(int(span_start1117), "CSVData")
	return result1118
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1867 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1868 := p.parse_csv_locator_paths()
		_t1867 = _t1868
	}
	csv_locator_paths1119 := _t1867
	var _t1869 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1870 := p.parse_csv_locator_inline_data()
		_t1869 = ptr(_t1870)
	}
	csv_locator_inline_data1120 := _t1869
	p.consumeLiteral(")")
	_t1871 := csv_locator_paths1119
	if csv_locator_paths1119 == nil {
		_t1871 = []string{}
	}
	_t1872 := &pb.CSVLocator{Paths: _t1871, InlineData: []byte(deref(csv_locator_inline_data1120, ""))}
	result1122 := _t1872
	p.recordSpan(int(span_start1121), "CSVLocator")
	return result1122
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1123 := []string{}
	cond1124 := p.matchLookaheadTerminal("STRING", 0)
	for cond1124 {
		item1125 := p.consumeTerminal("STRING").Value.str
		xs1123 = append(xs1123, item1125)
		cond1124 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1126 := xs1123
	p.consumeLiteral(")")
	return strings1126
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1127 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1127
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1129 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1873 := p.parse_config_dict()
	config_dict1128 := _t1873
	p.consumeLiteral(")")
	_t1874 := p.construct_csv_config(config_dict1128)
	result1130 := _t1874
	p.recordSpan(int(span_start1129), "CSVConfig")
	return result1130
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1131 := []*pb.GNFColumn{}
	cond1132 := p.matchLookaheadLiteral("(", 0)
	for cond1132 {
		_t1875 := p.parse_gnf_column()
		item1133 := _t1875
		xs1131 = append(xs1131, item1133)
		cond1132 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1134 := xs1131
	p.consumeLiteral(")")
	return gnf_columns1134
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1141 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1876 := p.parse_gnf_column_path()
	gnf_column_path1135 := _t1876
	var _t1877 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1878 := p.parse_relation_id()
		_t1877 = _t1878
	}
	relation_id1136 := _t1877
	p.consumeLiteral("[")
	xs1137 := []*pb.Type{}
	cond1138 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1138 {
		_t1879 := p.parse_type()
		item1139 := _t1879
		xs1137 = append(xs1137, item1139)
		cond1138 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1140 := xs1137
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1880 := &pb.GNFColumn{ColumnPath: gnf_column_path1135, TargetId: relation_id1136, Types: types1140}
	result1142 := _t1880
	p.recordSpan(int(span_start1141), "GNFColumn")
	return result1142
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1881 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1881 = 1
	} else {
		var _t1882 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1882 = 0
		} else {
			_t1882 = -1
		}
		_t1881 = _t1882
	}
	prediction1143 := _t1881
	var _t1883 []string
	if prediction1143 == 1 {
		p.consumeLiteral("[")
		xs1145 := []string{}
		cond1146 := p.matchLookaheadTerminal("STRING", 0)
		for cond1146 {
			item1147 := p.consumeTerminal("STRING").Value.str
			xs1145 = append(xs1145, item1147)
			cond1146 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1148 := xs1145
		p.consumeLiteral("]")
		_t1883 = strings1148
	} else {
		var _t1884 []string
		if prediction1143 == 0 {
			string1144 := p.consumeTerminal("STRING").Value.str
			_ = string1144
			_t1884 = []string{string1144}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1883 = _t1884
	}
	return _t1883
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1149 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1149
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1151 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1885 := p.parse_fragment_id()
	fragment_id1150 := _t1885
	p.consumeLiteral(")")
	_t1886 := &pb.Undefine{FragmentId: fragment_id1150}
	result1152 := _t1886
	p.recordSpan(int(span_start1151), "Undefine")
	return result1152
}

func (p *Parser) parse_context() *pb.Context {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1153 := []*pb.RelationId{}
	cond1154 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1154 {
		_t1887 := p.parse_relation_id()
		item1155 := _t1887
		xs1153 = append(xs1153, item1155)
		cond1154 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1156 := xs1153
	p.consumeLiteral(")")
	_t1888 := &pb.Context{Relations: relation_ids1156}
	result1158 := _t1888
	p.recordSpan(int(span_start1157), "Context")
	return result1158
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1163 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1159 := []*pb.SnapshotMapping{}
	cond1160 := p.matchLookaheadLiteral("[", 0)
	for cond1160 {
		_t1889 := p.parse_snapshot_mapping()
		item1161 := _t1889
		xs1159 = append(xs1159, item1161)
		cond1160 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1162 := xs1159
	p.consumeLiteral(")")
	_t1890 := &pb.Snapshot{Mappings: snapshot_mappings1162}
	result1164 := _t1890
	p.recordSpan(int(span_start1163), "Snapshot")
	return result1164
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1167 := int64(p.spanStart())
	_t1891 := p.parse_edb_path()
	edb_path1165 := _t1891
	_t1892 := p.parse_relation_id()
	relation_id1166 := _t1892
	_t1893 := &pb.SnapshotMapping{DestinationPath: edb_path1165, SourceRelation: relation_id1166}
	result1168 := _t1893
	p.recordSpan(int(span_start1167), "SnapshotMapping")
	return result1168
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1169 := []*pb.Read{}
	cond1170 := p.matchLookaheadLiteral("(", 0)
	for cond1170 {
		_t1894 := p.parse_read()
		item1171 := _t1894
		xs1169 = append(xs1169, item1171)
		cond1170 = p.matchLookaheadLiteral("(", 0)
	}
	reads1172 := xs1169
	p.consumeLiteral(")")
	return reads1172
}

func (p *Parser) parse_read() *pb.Read {
	span_start1179 := int64(p.spanStart())
	var _t1895 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1896 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1896 = 2
		} else {
			var _t1897 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1897 = 1
			} else {
				var _t1898 int64
				if p.matchLookaheadLiteral("export_iceberg", 1) {
					_t1898 = 4
				} else {
					var _t1899 int64
					if p.matchLookaheadLiteral("export", 1) {
						_t1899 = 4
					} else {
						var _t1900 int64
						if p.matchLookaheadLiteral("demand", 1) {
							_t1900 = 0
						} else {
							var _t1901 int64
							if p.matchLookaheadLiteral("abort", 1) {
								_t1901 = 3
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
			}
			_t1896 = _t1897
		}
		_t1895 = _t1896
	} else {
		_t1895 = -1
	}
	prediction1173 := _t1895
	var _t1902 *pb.Read
	if prediction1173 == 4 {
		_t1903 := p.parse_export()
		export1178 := _t1903
		_t1904 := &pb.Read{}
		_t1904.ReadType = &pb.Read_Export{Export: export1178}
		_t1902 = _t1904
	} else {
		var _t1905 *pb.Read
		if prediction1173 == 3 {
			_t1906 := p.parse_abort()
			abort1177 := _t1906
			_t1907 := &pb.Read{}
			_t1907.ReadType = &pb.Read_Abort{Abort: abort1177}
			_t1905 = _t1907
		} else {
			var _t1908 *pb.Read
			if prediction1173 == 2 {
				_t1909 := p.parse_what_if()
				what_if1176 := _t1909
				_t1910 := &pb.Read{}
				_t1910.ReadType = &pb.Read_WhatIf{WhatIf: what_if1176}
				_t1908 = _t1910
			} else {
				var _t1911 *pb.Read
				if prediction1173 == 1 {
					_t1912 := p.parse_output()
					output1175 := _t1912
					_t1913 := &pb.Read{}
					_t1913.ReadType = &pb.Read_Output{Output: output1175}
					_t1911 = _t1913
				} else {
					var _t1914 *pb.Read
					if prediction1173 == 0 {
						_t1915 := p.parse_demand()
						demand1174 := _t1915
						_t1916 := &pb.Read{}
						_t1916.ReadType = &pb.Read_Demand{Demand: demand1174}
						_t1914 = _t1916
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1911 = _t1914
				}
				_t1908 = _t1911
			}
			_t1905 = _t1908
		}
		_t1902 = _t1905
	}
	result1180 := _t1902
	p.recordSpan(int(span_start1179), "Read")
	return result1180
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1182 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1917 := p.parse_relation_id()
	relation_id1181 := _t1917
	p.consumeLiteral(")")
	_t1918 := &pb.Demand{RelationId: relation_id1181}
	result1183 := _t1918
	p.recordSpan(int(span_start1182), "Demand")
	return result1183
}

func (p *Parser) parse_output() *pb.Output {
	span_start1186 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1919 := p.parse_name()
	name1184 := _t1919
	_t1920 := p.parse_relation_id()
	relation_id1185 := _t1920
	p.consumeLiteral(")")
	_t1921 := &pb.Output{Name: name1184, RelationId: relation_id1185}
	result1187 := _t1921
	p.recordSpan(int(span_start1186), "Output")
	return result1187
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1190 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1922 := p.parse_name()
	name1188 := _t1922
	_t1923 := p.parse_epoch()
	epoch1189 := _t1923
	p.consumeLiteral(")")
	_t1924 := &pb.WhatIf{Branch: name1188, Epoch: epoch1189}
	result1191 := _t1924
	p.recordSpan(int(span_start1190), "WhatIf")
	return result1191
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1194 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1925 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1926 := p.parse_name()
		_t1925 = ptr(_t1926)
	}
	name1192 := _t1925
	_t1927 := p.parse_relation_id()
	relation_id1193 := _t1927
	p.consumeLiteral(")")
	_t1928 := &pb.Abort{Name: deref(name1192, "abort"), RelationId: relation_id1193}
	result1195 := _t1928
	p.recordSpan(int(span_start1194), "Abort")
	return result1195
}

func (p *Parser) parse_export() *pb.Export {
	span_start1199 := int64(p.spanStart())
	var _t1929 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1930 int64
		if p.matchLookaheadLiteral("export_iceberg", 1) {
			_t1930 = 1
		} else {
			var _t1931 int64
			if p.matchLookaheadLiteral("export", 1) {
				_t1931 = 0
			} else {
				_t1931 = -1
			}
			_t1930 = _t1931
		}
		_t1929 = _t1930
	} else {
		_t1929 = -1
	}
	prediction1196 := _t1929
	var _t1932 *pb.Export
	if prediction1196 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_iceberg")
		_t1933 := p.parse_export_iceberg_config()
		export_iceberg_config1198 := _t1933
		p.consumeLiteral(")")
		_t1934 := &pb.Export{}
		_t1934.ExportConfig = &pb.Export_IcebergConfig{IcebergConfig: export_iceberg_config1198}
		_t1932 = _t1934
	} else {
		var _t1935 *pb.Export
		if prediction1196 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export")
			_t1936 := p.parse_export_csv_config()
			export_csv_config1197 := _t1936
			p.consumeLiteral(")")
			_t1937 := &pb.Export{}
			_t1937.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1197}
			_t1935 = _t1937
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1932 = _t1935
	}
	result1200 := _t1932
	p.recordSpan(int(span_start1199), "Export")
	return result1200
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1208 := int64(p.spanStart())
	var _t1938 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1939 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1939 = 0
		} else {
			var _t1940 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1940 = 1
			} else {
				_t1940 = -1
			}
			_t1939 = _t1940
		}
		_t1938 = _t1939
	} else {
		_t1938 = -1
	}
	prediction1201 := _t1938
	var _t1941 *pb.ExportCSVConfig
	if prediction1201 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1942 := p.parse_export_csv_path()
		export_csv_path1205 := _t1942
		_t1943 := p.parse_export_csv_columns_list()
		export_csv_columns_list1206 := _t1943
		_t1944 := p.parse_config_dict()
		config_dict1207 := _t1944
		p.consumeLiteral(")")
		_t1945 := p.construct_export_csv_config(export_csv_path1205, export_csv_columns_list1206, config_dict1207)
		_t1941 = _t1945
	} else {
		var _t1946 *pb.ExportCSVConfig
		if prediction1201 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1947 := p.parse_export_csv_path()
			export_csv_path1202 := _t1947
			_t1948 := p.parse_export_csv_source()
			export_csv_source1203 := _t1948
			_t1949 := p.parse_csv_config()
			csv_config1204 := _t1949
			p.consumeLiteral(")")
			_t1950 := p.construct_export_csv_config_with_source(export_csv_path1202, export_csv_source1203, csv_config1204)
			_t1946 = _t1950
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1941 = _t1946
	}
	result1209 := _t1941
	p.recordSpan(int(span_start1208), "ExportCSVConfig")
	return result1209
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1210 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1210
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1217 := int64(p.spanStart())
	var _t1951 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1952 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1952 = 1
		} else {
			var _t1953 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1953 = 0
			} else {
				_t1953 = -1
			}
			_t1952 = _t1953
		}
		_t1951 = _t1952
	} else {
		_t1951 = -1
	}
	prediction1211 := _t1951
	var _t1954 *pb.ExportCSVSource
	if prediction1211 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1955 := p.parse_relation_id()
		relation_id1216 := _t1955
		p.consumeLiteral(")")
		_t1956 := &pb.ExportCSVSource{}
		_t1956.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1216}
		_t1954 = _t1956
	} else {
		var _t1957 *pb.ExportCSVSource
		if prediction1211 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1212 := []*pb.ExportCSVColumn{}
			cond1213 := p.matchLookaheadLiteral("(", 0)
			for cond1213 {
				_t1958 := p.parse_export_csv_column()
				item1214 := _t1958
				xs1212 = append(xs1212, item1214)
				cond1213 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1215 := xs1212
			p.consumeLiteral(")")
			_t1959 := &pb.ExportCSVColumns{Columns: export_csv_columns1215}
			_t1960 := &pb.ExportCSVSource{}
			_t1960.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1959}
			_t1957 = _t1960
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1954 = _t1957
	}
	result1218 := _t1954
	p.recordSpan(int(span_start1217), "ExportCSVSource")
	return result1218
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1221 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1219 := p.consumeTerminal("STRING").Value.str
	_t1961 := p.parse_relation_id()
	relation_id1220 := _t1961
	p.consumeLiteral(")")
	_t1962 := &pb.ExportCSVColumn{ColumnName: string1219, ColumnData: relation_id1220}
	result1222 := _t1962
	p.recordSpan(int(span_start1221), "ExportCSVColumn")
	return result1222
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1223 := []*pb.ExportCSVColumn{}
	cond1224 := p.matchLookaheadLiteral("(", 0)
	for cond1224 {
		_t1963 := p.parse_export_csv_column()
		item1225 := _t1963
		xs1223 = append(xs1223, item1225)
		cond1224 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1226 := xs1223
	p.consumeLiteral(")")
	return export_csv_columns1226
}

func (p *Parser) parse_export_iceberg_config() *pb.ExportIcebergConfig {
	span_start1236 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_iceberg_config")
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_uri")
	string1227 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("namespace")
	xs1228 := []string{}
	cond1229 := p.matchLookaheadTerminal("STRING", 0)
	for cond1229 {
		item1230 := p.consumeTerminal("STRING").Value.str
		xs1228 = append(xs1228, item1230)
		cond1229 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1231 := xs1228
	p.consumeLiteral(")")
	p.consumeLiteral("(")
	p.consumeLiteral("table_name")
	string_121232 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	_t1964 := p.parse_export_iceberg_catalog_properties()
	export_iceberg_catalog_properties1233 := _t1964
	p.consumeLiteral("(")
	p.consumeLiteral("schema")
	string_171234 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1965 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t1966 := p.parse_config_dict()
		_t1965 = _t1966
	}
	config_dict1235 := _t1965
	p.consumeLiteral(")")
	_t1967 := p.construct_export_iceberg_config_from_optional(string1227, strings1231, string_121232, export_iceberg_catalog_properties1233, string_171234, config_dict1235)
	result1237 := _t1967
	p.recordSpan(int(span_start1236), "ExportIcebergConfig")
	return result1237
}

func (p *Parser) parse_export_iceberg_catalog_properties() *pb.IcebergCatalogProperties {
	span_start1240 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("catalog_properties")
	p.consumeLiteral("(")
	p.consumeLiteral("warehouse")
	string1238 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	var _t1968 [][]interface{}
	if p.matchLookaheadLiteral("{", 0) {
		_t1969 := p.parse_config_dict()
		_t1968 = _t1969
	}
	config_dict1239 := _t1968
	p.consumeLiteral(")")
	_t1970 := p.construct_iceberg_catalog_properties_from_optional(string1238, config_dict1239)
	result1241 := _t1970
	p.recordSpan(int(span_start1240), "IcebergCatalogProperties")
	return result1241
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
