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
	case kindFloat64:
		return strconv.FormatFloat(tv.f64, 'g', -1, 64)
	case kindFloat32:
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
		{"FLOAT", regexp.MustCompile(`^([-]?\d+\.\d+|inf|nan)`), func(s string) TokenValue { return TokenValue{kind: kindFloat64, f64: scanFloat(s)} }},
		{"FLOAT32", regexp.MustCompile(`^[-]?\d+\.\d+f32`), func(s string) TokenValue { return TokenValue{kind: kindFloat32, f32: scanFloat32(s)} }},
		{"INT", regexp.MustCompile(`^[-]?\d+`), func(s string) TokenValue { return TokenValue{kind: kindInt64, i64: scanInt(s)} }},
		{"INT32", regexp.MustCompile(`^[-]?\d+i32`), func(s string) TokenValue { return TokenValue{kind: kindInt32, i32: scanInt32(s)} }},
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

func scanFloat32(s string) float32 {
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
	var _t1899 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1899
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1900 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1900
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1901 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1901
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1902 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1902
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1903 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1903
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1904 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1904
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1905 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1905
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1906 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1906
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1907 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1907
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1908 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1908
	_t1909 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1909
	_t1910 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1910
	_t1911 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1911
	_t1912 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1912
	_t1913 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1913
	_t1914 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1914
	_t1915 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1915
	_t1916 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1916
	_t1917 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1917
	_t1918 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1918
	_t1919 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1919
	_t1920 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1920
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1921 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1921
	_t1922 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1922
	_t1923 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1923
	_t1924 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1924
	_t1925 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1925
	_t1926 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1926
	_t1927 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1927
	_t1928 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1928
	_t1929 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1929
	_t1930 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1930.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1930.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1930
	_t1931 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1931
}

func (p *Parser) default_configure() *pb.Configure {
	_t1932 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1932
	_t1933 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1933
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
	_t1934 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1934
	_t1935 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1935
	_t1936 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1936
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1937 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1937
	_t1938 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1938
	_t1939 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1939
	_t1940 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1940
	_t1941 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1941
	_t1942 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1942
	_t1943 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1943
	_t1944 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1944
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1945 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1945
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start605 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1198 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1199 := p.parse_configure()
		_t1198 = _t1199
	}
	configure599 := _t1198
	var _t1200 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1201 := p.parse_sync()
		_t1200 = _t1201
	}
	sync600 := _t1200
	xs601 := []*pb.Epoch{}
	cond602 := p.matchLookaheadLiteral("(", 0)
	for cond602 {
		_t1202 := p.parse_epoch()
		item603 := _t1202
		xs601 = append(xs601, item603)
		cond602 = p.matchLookaheadLiteral("(", 0)
	}
	epochs604 := xs601
	p.consumeLiteral(")")
	_t1203 := p.default_configure()
	_t1204 := configure599
	if configure599 == nil {
		_t1204 = _t1203
	}
	_t1205 := &pb.Transaction{Epochs: epochs604, Configure: _t1204, Sync: sync600}
	result606 := _t1205
	p.recordSpan(int(span_start605), "Transaction")
	return result606
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start608 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1206 := p.parse_config_dict()
	config_dict607 := _t1206
	p.consumeLiteral(")")
	_t1207 := p.construct_configure(config_dict607)
	result609 := _t1207
	p.recordSpan(int(span_start608), "Configure")
	return result609
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs610 := [][]interface{}{}
	cond611 := p.matchLookaheadLiteral(":", 0)
	for cond611 {
		_t1208 := p.parse_config_key_value()
		item612 := _t1208
		xs610 = append(xs610, item612)
		cond611 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values613 := xs610
	p.consumeLiteral("}")
	return config_key_values613
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol614 := p.consumeTerminal("SYMBOL").Value.str
	_t1209 := p.parse_raw_value()
	raw_value615 := _t1209
	return []interface{}{symbol614, raw_value615}
}

func (p *Parser) parse_raw_value() *pb.Value {
	span_start628 := int64(p.spanStart())
	var _t1210 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1210 = 11
	} else {
		var _t1211 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1211 = 10
		} else {
			var _t1212 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1212 = 11
			} else {
				var _t1213 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1214 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1214 = 1
					} else {
						var _t1215 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1215 = 0
						} else {
							_t1215 = -1
						}
						_t1214 = _t1215
					}
					_t1213 = _t1214
				} else {
					var _t1216 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1216 = 7
					} else {
						var _t1217 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1217 = 2
						} else {
							var _t1218 int64
							if p.matchLookaheadTerminal("INT32", 0) {
								_t1218 = 3
							} else {
								var _t1219 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1219 = 8
								} else {
									var _t1220 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1220 = 4
									} else {
										var _t1221 int64
										if p.matchLookaheadTerminal("FLOAT32", 0) {
											_t1221 = 5
										} else {
											var _t1222 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1222 = 6
											} else {
												var _t1223 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1223 = 9
												} else {
													_t1223 = -1
												}
												_t1222 = _t1223
											}
											_t1221 = _t1222
										}
										_t1220 = _t1221
									}
									_t1219 = _t1220
								}
								_t1218 = _t1219
							}
							_t1217 = _t1218
						}
						_t1216 = _t1217
					}
					_t1213 = _t1216
				}
				_t1212 = _t1213
			}
			_t1211 = _t1212
		}
		_t1210 = _t1211
	}
	prediction616 := _t1210
	var _t1224 *pb.Value
	if prediction616 == 11 {
		_t1225 := p.parse_boolean_value()
		boolean_value627 := _t1225
		_t1226 := &pb.Value{}
		_t1226.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value627}
		_t1224 = _t1226
	} else {
		var _t1227 *pb.Value
		if prediction616 == 10 {
			p.consumeLiteral("missing")
			_t1228 := &pb.MissingValue{}
			_t1229 := &pb.Value{}
			_t1229.Value = &pb.Value_MissingValue{MissingValue: _t1228}
			_t1227 = _t1229
		} else {
			var _t1230 *pb.Value
			if prediction616 == 9 {
				decimal626 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1231 := &pb.Value{}
				_t1231.Value = &pb.Value_DecimalValue{DecimalValue: decimal626}
				_t1230 = _t1231
			} else {
				var _t1232 *pb.Value
				if prediction616 == 8 {
					int128625 := p.consumeTerminal("INT128").Value.int128
					_t1233 := &pb.Value{}
					_t1233.Value = &pb.Value_Int128Value{Int128Value: int128625}
					_t1232 = _t1233
				} else {
					var _t1234 *pb.Value
					if prediction616 == 7 {
						uint128624 := p.consumeTerminal("UINT128").Value.uint128
						_t1235 := &pb.Value{}
						_t1235.Value = &pb.Value_Uint128Value{Uint128Value: uint128624}
						_t1234 = _t1235
					} else {
						var _t1236 *pb.Value
						if prediction616 == 6 {
							float623 := p.consumeTerminal("FLOAT").Value.f64
							_t1237 := &pb.Value{}
							_t1237.Value = &pb.Value_FloatValue{FloatValue: float623}
							_t1236 = _t1237
						} else {
							var _t1238 *pb.Value
							if prediction616 == 5 {
								float32622 := p.consumeTerminal("FLOAT32").Value.f32
								_t1239 := &pb.Value{}
								_t1239.Value = &pb.Value_Float32Value{Float32Value: float32622}
								_t1238 = _t1239
							} else {
								var _t1240 *pb.Value
								if prediction616 == 4 {
									int621 := p.consumeTerminal("INT").Value.i64
									_t1241 := &pb.Value{}
									_t1241.Value = &pb.Value_IntValue{IntValue: int621}
									_t1240 = _t1241
								} else {
									var _t1242 *pb.Value
									if prediction616 == 3 {
										int32620 := p.consumeTerminal("INT32").Value.i32
										_t1243 := &pb.Value{}
										_t1243.Value = &pb.Value_Int32Value{Int32Value: int32620}
										_t1242 = _t1243
									} else {
										var _t1244 *pb.Value
										if prediction616 == 2 {
											string619 := p.consumeTerminal("STRING").Value.str
											_t1245 := &pb.Value{}
											_t1245.Value = &pb.Value_StringValue{StringValue: string619}
											_t1244 = _t1245
										} else {
											var _t1246 *pb.Value
											if prediction616 == 1 {
												_t1247 := p.parse_raw_datetime()
												raw_datetime618 := _t1247
												_t1248 := &pb.Value{}
												_t1248.Value = &pb.Value_DatetimeValue{DatetimeValue: raw_datetime618}
												_t1246 = _t1248
											} else {
												var _t1249 *pb.Value
												if prediction616 == 0 {
													_t1250 := p.parse_raw_date()
													raw_date617 := _t1250
													_t1251 := &pb.Value{}
													_t1251.Value = &pb.Value_DateValue{DateValue: raw_date617}
													_t1249 = _t1251
												} else {
													panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in raw_value", p.lookahead(0).Type, p.lookahead(0).Value)})
												}
												_t1246 = _t1249
											}
											_t1244 = _t1246
										}
										_t1242 = _t1244
									}
									_t1240 = _t1242
								}
								_t1238 = _t1240
							}
							_t1236 = _t1238
						}
						_t1234 = _t1236
					}
					_t1232 = _t1234
				}
				_t1230 = _t1232
			}
			_t1227 = _t1230
		}
		_t1224 = _t1227
	}
	result629 := _t1224
	p.recordSpan(int(span_start628), "Value")
	return result629
}

func (p *Parser) parse_raw_date() *pb.DateValue {
	span_start633 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int630 := p.consumeTerminal("INT").Value.i64
	int_3631 := p.consumeTerminal("INT").Value.i64
	int_4632 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1252 := &pb.DateValue{Year: int32(int630), Month: int32(int_3631), Day: int32(int_4632)}
	result634 := _t1252
	p.recordSpan(int(span_start633), "DateValue")
	return result634
}

func (p *Parser) parse_raw_datetime() *pb.DateTimeValue {
	span_start642 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int635 := p.consumeTerminal("INT").Value.i64
	int_3636 := p.consumeTerminal("INT").Value.i64
	int_4637 := p.consumeTerminal("INT").Value.i64
	int_5638 := p.consumeTerminal("INT").Value.i64
	int_6639 := p.consumeTerminal("INT").Value.i64
	int_7640 := p.consumeTerminal("INT").Value.i64
	var _t1253 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1253 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8641 := _t1253
	p.consumeLiteral(")")
	_t1254 := &pb.DateTimeValue{Year: int32(int635), Month: int32(int_3636), Day: int32(int_4637), Hour: int32(int_5638), Minute: int32(int_6639), Second: int32(int_7640), Microsecond: int32(deref(int_8641, 0))}
	result643 := _t1254
	p.recordSpan(int(span_start642), "DateTimeValue")
	return result643
}

func (p *Parser) parse_boolean_value() bool {
	var _t1255 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1255 = 0
	} else {
		var _t1256 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1256 = 1
		} else {
			_t1256 = -1
		}
		_t1255 = _t1256
	}
	prediction644 := _t1255
	var _t1257 bool
	if prediction644 == 1 {
		p.consumeLiteral("false")
		_t1257 = false
	} else {
		var _t1258 bool
		if prediction644 == 0 {
			p.consumeLiteral("true")
			_t1258 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1257 = _t1258
	}
	return _t1257
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start649 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs645 := []*pb.FragmentId{}
	cond646 := p.matchLookaheadLiteral(":", 0)
	for cond646 {
		_t1259 := p.parse_fragment_id()
		item647 := _t1259
		xs645 = append(xs645, item647)
		cond646 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids648 := xs645
	p.consumeLiteral(")")
	_t1260 := &pb.Sync{Fragments: fragment_ids648}
	result650 := _t1260
	p.recordSpan(int(span_start649), "Sync")
	return result650
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start652 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol651 := p.consumeTerminal("SYMBOL").Value.str
	result653 := &pb.FragmentId{Id: []byte(symbol651)}
	p.recordSpan(int(span_start652), "FragmentId")
	return result653
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start656 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1261 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1262 := p.parse_epoch_writes()
		_t1261 = _t1262
	}
	epoch_writes654 := _t1261
	var _t1263 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1264 := p.parse_epoch_reads()
		_t1263 = _t1264
	}
	epoch_reads655 := _t1263
	p.consumeLiteral(")")
	_t1265 := epoch_writes654
	if epoch_writes654 == nil {
		_t1265 = []*pb.Write{}
	}
	_t1266 := epoch_reads655
	if epoch_reads655 == nil {
		_t1266 = []*pb.Read{}
	}
	_t1267 := &pb.Epoch{Writes: _t1265, Reads: _t1266}
	result657 := _t1267
	p.recordSpan(int(span_start656), "Epoch")
	return result657
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs658 := []*pb.Write{}
	cond659 := p.matchLookaheadLiteral("(", 0)
	for cond659 {
		_t1268 := p.parse_write()
		item660 := _t1268
		xs658 = append(xs658, item660)
		cond659 = p.matchLookaheadLiteral("(", 0)
	}
	writes661 := xs658
	p.consumeLiteral(")")
	return writes661
}

func (p *Parser) parse_write() *pb.Write {
	span_start667 := int64(p.spanStart())
	var _t1269 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1270 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1270 = 1
		} else {
			var _t1271 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1271 = 3
			} else {
				var _t1272 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1272 = 0
				} else {
					var _t1273 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1273 = 2
					} else {
						_t1273 = -1
					}
					_t1272 = _t1273
				}
				_t1271 = _t1272
			}
			_t1270 = _t1271
		}
		_t1269 = _t1270
	} else {
		_t1269 = -1
	}
	prediction662 := _t1269
	var _t1274 *pb.Write
	if prediction662 == 3 {
		_t1275 := p.parse_snapshot()
		snapshot666 := _t1275
		_t1276 := &pb.Write{}
		_t1276.WriteType = &pb.Write_Snapshot{Snapshot: snapshot666}
		_t1274 = _t1276
	} else {
		var _t1277 *pb.Write
		if prediction662 == 2 {
			_t1278 := p.parse_context()
			context665 := _t1278
			_t1279 := &pb.Write{}
			_t1279.WriteType = &pb.Write_Context{Context: context665}
			_t1277 = _t1279
		} else {
			var _t1280 *pb.Write
			if prediction662 == 1 {
				_t1281 := p.parse_undefine()
				undefine664 := _t1281
				_t1282 := &pb.Write{}
				_t1282.WriteType = &pb.Write_Undefine{Undefine: undefine664}
				_t1280 = _t1282
			} else {
				var _t1283 *pb.Write
				if prediction662 == 0 {
					_t1284 := p.parse_define()
					define663 := _t1284
					_t1285 := &pb.Write{}
					_t1285.WriteType = &pb.Write_Define{Define: define663}
					_t1283 = _t1285
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1280 = _t1283
			}
			_t1277 = _t1280
		}
		_t1274 = _t1277
	}
	result668 := _t1274
	p.recordSpan(int(span_start667), "Write")
	return result668
}

func (p *Parser) parse_define() *pb.Define {
	span_start670 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1286 := p.parse_fragment()
	fragment669 := _t1286
	p.consumeLiteral(")")
	_t1287 := &pb.Define{Fragment: fragment669}
	result671 := _t1287
	p.recordSpan(int(span_start670), "Define")
	return result671
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start677 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1288 := p.parse_new_fragment_id()
	new_fragment_id672 := _t1288
	xs673 := []*pb.Declaration{}
	cond674 := p.matchLookaheadLiteral("(", 0)
	for cond674 {
		_t1289 := p.parse_declaration()
		item675 := _t1289
		xs673 = append(xs673, item675)
		cond674 = p.matchLookaheadLiteral("(", 0)
	}
	declarations676 := xs673
	p.consumeLiteral(")")
	result678 := p.constructFragment(new_fragment_id672, declarations676)
	p.recordSpan(int(span_start677), "Fragment")
	return result678
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start680 := int64(p.spanStart())
	_t1290 := p.parse_fragment_id()
	fragment_id679 := _t1290
	p.startFragment(fragment_id679)
	result681 := fragment_id679
	p.recordSpan(int(span_start680), "FragmentId")
	return result681
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start687 := int64(p.spanStart())
	var _t1291 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1292 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1292 = 2
		} else {
			var _t1293 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1293 = 3
			} else {
				var _t1294 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1294 = 0
				} else {
					var _t1295 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1295 = 3
					} else {
						var _t1296 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1296 = 3
						} else {
							var _t1297 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1297 = 1
							} else {
								_t1297 = -1
							}
							_t1296 = _t1297
						}
						_t1295 = _t1296
					}
					_t1294 = _t1295
				}
				_t1293 = _t1294
			}
			_t1292 = _t1293
		}
		_t1291 = _t1292
	} else {
		_t1291 = -1
	}
	prediction682 := _t1291
	var _t1298 *pb.Declaration
	if prediction682 == 3 {
		_t1299 := p.parse_data()
		data686 := _t1299
		_t1300 := &pb.Declaration{}
		_t1300.DeclarationType = &pb.Declaration_Data{Data: data686}
		_t1298 = _t1300
	} else {
		var _t1301 *pb.Declaration
		if prediction682 == 2 {
			_t1302 := p.parse_constraint()
			constraint685 := _t1302
			_t1303 := &pb.Declaration{}
			_t1303.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint685}
			_t1301 = _t1303
		} else {
			var _t1304 *pb.Declaration
			if prediction682 == 1 {
				_t1305 := p.parse_algorithm()
				algorithm684 := _t1305
				_t1306 := &pb.Declaration{}
				_t1306.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm684}
				_t1304 = _t1306
			} else {
				var _t1307 *pb.Declaration
				if prediction682 == 0 {
					_t1308 := p.parse_def()
					def683 := _t1308
					_t1309 := &pb.Declaration{}
					_t1309.DeclarationType = &pb.Declaration_Def{Def: def683}
					_t1307 = _t1309
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1304 = _t1307
			}
			_t1301 = _t1304
		}
		_t1298 = _t1301
	}
	result688 := _t1298
	p.recordSpan(int(span_start687), "Declaration")
	return result688
}

func (p *Parser) parse_def() *pb.Def {
	span_start692 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1310 := p.parse_relation_id()
	relation_id689 := _t1310
	_t1311 := p.parse_abstraction()
	abstraction690 := _t1311
	var _t1312 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1313 := p.parse_attrs()
		_t1312 = _t1313
	}
	attrs691 := _t1312
	p.consumeLiteral(")")
	_t1314 := attrs691
	if attrs691 == nil {
		_t1314 = []*pb.Attribute{}
	}
	_t1315 := &pb.Def{Name: relation_id689, Body: abstraction690, Attrs: _t1314}
	result693 := _t1315
	p.recordSpan(int(span_start692), "Def")
	return result693
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start697 := int64(p.spanStart())
	var _t1316 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1316 = 0
	} else {
		var _t1317 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1317 = 1
		} else {
			_t1317 = -1
		}
		_t1316 = _t1317
	}
	prediction694 := _t1316
	var _t1318 *pb.RelationId
	if prediction694 == 1 {
		uint128696 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128696
		_t1318 = &pb.RelationId{IdLow: uint128696.Low, IdHigh: uint128696.High}
	} else {
		var _t1319 *pb.RelationId
		if prediction694 == 0 {
			p.consumeLiteral(":")
			symbol695 := p.consumeTerminal("SYMBOL").Value.str
			_t1319 = p.relationIdFromString(symbol695)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1318 = _t1319
	}
	result698 := _t1318
	p.recordSpan(int(span_start697), "RelationId")
	return result698
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start701 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1320 := p.parse_bindings()
	bindings699 := _t1320
	_t1321 := p.parse_formula()
	formula700 := _t1321
	p.consumeLiteral(")")
	_t1322 := &pb.Abstraction{Vars: listConcat(bindings699[0].([]*pb.Binding), bindings699[1].([]*pb.Binding)), Value: formula700}
	result702 := _t1322
	p.recordSpan(int(span_start701), "Abstraction")
	return result702
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs703 := []*pb.Binding{}
	cond704 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond704 {
		_t1323 := p.parse_binding()
		item705 := _t1323
		xs703 = append(xs703, item705)
		cond704 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings706 := xs703
	var _t1324 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1325 := p.parse_value_bindings()
		_t1324 = _t1325
	}
	value_bindings707 := _t1324
	p.consumeLiteral("]")
	_t1326 := value_bindings707
	if value_bindings707 == nil {
		_t1326 = []*pb.Binding{}
	}
	return []interface{}{bindings706, _t1326}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start710 := int64(p.spanStart())
	symbol708 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1327 := p.parse_type()
	type709 := _t1327
	_t1328 := &pb.Var{Name: symbol708}
	_t1329 := &pb.Binding{Var: _t1328, Type: type709}
	result711 := _t1329
	p.recordSpan(int(span_start710), "Binding")
	return result711
}

func (p *Parser) parse_type() *pb.Type {
	span_start726 := int64(p.spanStart())
	var _t1330 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1330 = 0
	} else {
		var _t1331 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1331 = 4
		} else {
			var _t1332 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1332 = 1
			} else {
				var _t1333 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1333 = 8
				} else {
					var _t1334 int64
					if p.matchLookaheadLiteral("INT32", 0) {
						_t1334 = 11
					} else {
						var _t1335 int64
						if p.matchLookaheadLiteral("INT128", 0) {
							_t1335 = 5
						} else {
							var _t1336 int64
							if p.matchLookaheadLiteral("INT", 0) {
								_t1336 = 2
							} else {
								var _t1337 int64
								if p.matchLookaheadLiteral("FLOAT32", 0) {
									_t1337 = 12
								} else {
									var _t1338 int64
									if p.matchLookaheadLiteral("FLOAT", 0) {
										_t1338 = 3
									} else {
										var _t1339 int64
										if p.matchLookaheadLiteral("DATETIME", 0) {
											_t1339 = 7
										} else {
											var _t1340 int64
											if p.matchLookaheadLiteral("DATE", 0) {
												_t1340 = 6
											} else {
												var _t1341 int64
												if p.matchLookaheadLiteral("BOOLEAN", 0) {
													_t1341 = 10
												} else {
													var _t1342 int64
													if p.matchLookaheadLiteral("(", 0) {
														_t1342 = 9
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
					_t1333 = _t1334
				}
				_t1332 = _t1333
			}
			_t1331 = _t1332
		}
		_t1330 = _t1331
	}
	prediction712 := _t1330
	var _t1343 *pb.Type
	if prediction712 == 12 {
		_t1344 := p.parse_float32_type()
		float32_type725 := _t1344
		_t1345 := &pb.Type{}
		_t1345.Type = &pb.Type_Float32Type{Float32Type: float32_type725}
		_t1343 = _t1345
	} else {
		var _t1346 *pb.Type
		if prediction712 == 11 {
			_t1347 := p.parse_int32_type()
			int32_type724 := _t1347
			_t1348 := &pb.Type{}
			_t1348.Type = &pb.Type_Int32Type{Int32Type: int32_type724}
			_t1346 = _t1348
		} else {
			var _t1349 *pb.Type
			if prediction712 == 10 {
				_t1350 := p.parse_boolean_type()
				boolean_type723 := _t1350
				_t1351 := &pb.Type{}
				_t1351.Type = &pb.Type_BooleanType{BooleanType: boolean_type723}
				_t1349 = _t1351
			} else {
				var _t1352 *pb.Type
				if prediction712 == 9 {
					_t1353 := p.parse_decimal_type()
					decimal_type722 := _t1353
					_t1354 := &pb.Type{}
					_t1354.Type = &pb.Type_DecimalType{DecimalType: decimal_type722}
					_t1352 = _t1354
				} else {
					var _t1355 *pb.Type
					if prediction712 == 8 {
						_t1356 := p.parse_missing_type()
						missing_type721 := _t1356
						_t1357 := &pb.Type{}
						_t1357.Type = &pb.Type_MissingType{MissingType: missing_type721}
						_t1355 = _t1357
					} else {
						var _t1358 *pb.Type
						if prediction712 == 7 {
							_t1359 := p.parse_datetime_type()
							datetime_type720 := _t1359
							_t1360 := &pb.Type{}
							_t1360.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type720}
							_t1358 = _t1360
						} else {
							var _t1361 *pb.Type
							if prediction712 == 6 {
								_t1362 := p.parse_date_type()
								date_type719 := _t1362
								_t1363 := &pb.Type{}
								_t1363.Type = &pb.Type_DateType{DateType: date_type719}
								_t1361 = _t1363
							} else {
								var _t1364 *pb.Type
								if prediction712 == 5 {
									_t1365 := p.parse_int128_type()
									int128_type718 := _t1365
									_t1366 := &pb.Type{}
									_t1366.Type = &pb.Type_Int128Type{Int128Type: int128_type718}
									_t1364 = _t1366
								} else {
									var _t1367 *pb.Type
									if prediction712 == 4 {
										_t1368 := p.parse_uint128_type()
										uint128_type717 := _t1368
										_t1369 := &pb.Type{}
										_t1369.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type717}
										_t1367 = _t1369
									} else {
										var _t1370 *pb.Type
										if prediction712 == 3 {
											_t1371 := p.parse_float_type()
											float_type716 := _t1371
											_t1372 := &pb.Type{}
											_t1372.Type = &pb.Type_FloatType{FloatType: float_type716}
											_t1370 = _t1372
										} else {
											var _t1373 *pb.Type
											if prediction712 == 2 {
												_t1374 := p.parse_int_type()
												int_type715 := _t1374
												_t1375 := &pb.Type{}
												_t1375.Type = &pb.Type_IntType{IntType: int_type715}
												_t1373 = _t1375
											} else {
												var _t1376 *pb.Type
												if prediction712 == 1 {
													_t1377 := p.parse_string_type()
													string_type714 := _t1377
													_t1378 := &pb.Type{}
													_t1378.Type = &pb.Type_StringType{StringType: string_type714}
													_t1376 = _t1378
												} else {
													var _t1379 *pb.Type
													if prediction712 == 0 {
														_t1380 := p.parse_unspecified_type()
														unspecified_type713 := _t1380
														_t1381 := &pb.Type{}
														_t1381.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type713}
														_t1379 = _t1381
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1376 = _t1379
												}
												_t1373 = _t1376
											}
											_t1370 = _t1373
										}
										_t1367 = _t1370
									}
									_t1364 = _t1367
								}
								_t1361 = _t1364
							}
							_t1358 = _t1361
						}
						_t1355 = _t1358
					}
					_t1352 = _t1355
				}
				_t1349 = _t1352
			}
			_t1346 = _t1349
		}
		_t1343 = _t1346
	}
	result727 := _t1343
	p.recordSpan(int(span_start726), "Type")
	return result727
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start728 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1382 := &pb.UnspecifiedType{}
	result729 := _t1382
	p.recordSpan(int(span_start728), "UnspecifiedType")
	return result729
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start730 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1383 := &pb.StringType{}
	result731 := _t1383
	p.recordSpan(int(span_start730), "StringType")
	return result731
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start732 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1384 := &pb.IntType{}
	result733 := _t1384
	p.recordSpan(int(span_start732), "IntType")
	return result733
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start734 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1385 := &pb.FloatType{}
	result735 := _t1385
	p.recordSpan(int(span_start734), "FloatType")
	return result735
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start736 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1386 := &pb.UInt128Type{}
	result737 := _t1386
	p.recordSpan(int(span_start736), "UInt128Type")
	return result737
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start738 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1387 := &pb.Int128Type{}
	result739 := _t1387
	p.recordSpan(int(span_start738), "Int128Type")
	return result739
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start740 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1388 := &pb.DateType{}
	result741 := _t1388
	p.recordSpan(int(span_start740), "DateType")
	return result741
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start742 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1389 := &pb.DateTimeType{}
	result743 := _t1389
	p.recordSpan(int(span_start742), "DateTimeType")
	return result743
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start744 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1390 := &pb.MissingType{}
	result745 := _t1390
	p.recordSpan(int(span_start744), "MissingType")
	return result745
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start748 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int746 := p.consumeTerminal("INT").Value.i64
	int_3747 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1391 := &pb.DecimalType{Precision: int32(int746), Scale: int32(int_3747)}
	result749 := _t1391
	p.recordSpan(int(span_start748), "DecimalType")
	return result749
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start750 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1392 := &pb.BooleanType{}
	result751 := _t1392
	p.recordSpan(int(span_start750), "BooleanType")
	return result751
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1393 := &pb.Int32Type{}
	result753 := _t1393
	p.recordSpan(int(span_start752), "Int32Type")
	return result753
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start754 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1394 := &pb.Float32Type{}
	result755 := _t1394
	p.recordSpan(int(span_start754), "Float32Type")
	return result755
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs756 := []*pb.Binding{}
	cond757 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond757 {
		_t1395 := p.parse_binding()
		item758 := _t1395
		xs756 = append(xs756, item758)
		cond757 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings759 := xs756
	return bindings759
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start774 := int64(p.spanStart())
	var _t1396 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1397 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1397 = 0
		} else {
			var _t1398 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1398 = 11
			} else {
				var _t1399 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1399 = 3
				} else {
					var _t1400 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1400 = 10
					} else {
						var _t1401 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1401 = 9
						} else {
							var _t1402 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1402 = 5
							} else {
								var _t1403 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1403 = 6
								} else {
									var _t1404 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1404 = 7
									} else {
										var _t1405 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1405 = 1
										} else {
											var _t1406 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1406 = 2
											} else {
												var _t1407 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1407 = 12
												} else {
													var _t1408 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1408 = 8
													} else {
														var _t1409 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1409 = 4
														} else {
															var _t1410 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1410 = 10
															} else {
																var _t1411 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1411 = 10
																} else {
																	var _t1412 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1412 = 10
																	} else {
																		var _t1413 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1413 = 10
																		} else {
																			var _t1414 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1414 = 10
																			} else {
																				var _t1415 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1415 = 10
																				} else {
																					var _t1416 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1416 = 10
																					} else {
																						var _t1417 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1417 = 10
																						} else {
																							var _t1418 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1418 = 10
																							} else {
																								_t1418 = -1
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
											}
											_t1405 = _t1406
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
			}
			_t1397 = _t1398
		}
		_t1396 = _t1397
	} else {
		_t1396 = -1
	}
	prediction760 := _t1396
	var _t1419 *pb.Formula
	if prediction760 == 12 {
		_t1420 := p.parse_cast()
		cast773 := _t1420
		_t1421 := &pb.Formula{}
		_t1421.FormulaType = &pb.Formula_Cast{Cast: cast773}
		_t1419 = _t1421
	} else {
		var _t1422 *pb.Formula
		if prediction760 == 11 {
			_t1423 := p.parse_rel_atom()
			rel_atom772 := _t1423
			_t1424 := &pb.Formula{}
			_t1424.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom772}
			_t1422 = _t1424
		} else {
			var _t1425 *pb.Formula
			if prediction760 == 10 {
				_t1426 := p.parse_primitive()
				primitive771 := _t1426
				_t1427 := &pb.Formula{}
				_t1427.FormulaType = &pb.Formula_Primitive{Primitive: primitive771}
				_t1425 = _t1427
			} else {
				var _t1428 *pb.Formula
				if prediction760 == 9 {
					_t1429 := p.parse_pragma()
					pragma770 := _t1429
					_t1430 := &pb.Formula{}
					_t1430.FormulaType = &pb.Formula_Pragma{Pragma: pragma770}
					_t1428 = _t1430
				} else {
					var _t1431 *pb.Formula
					if prediction760 == 8 {
						_t1432 := p.parse_atom()
						atom769 := _t1432
						_t1433 := &pb.Formula{}
						_t1433.FormulaType = &pb.Formula_Atom{Atom: atom769}
						_t1431 = _t1433
					} else {
						var _t1434 *pb.Formula
						if prediction760 == 7 {
							_t1435 := p.parse_ffi()
							ffi768 := _t1435
							_t1436 := &pb.Formula{}
							_t1436.FormulaType = &pb.Formula_Ffi{Ffi: ffi768}
							_t1434 = _t1436
						} else {
							var _t1437 *pb.Formula
							if prediction760 == 6 {
								_t1438 := p.parse_not()
								not767 := _t1438
								_t1439 := &pb.Formula{}
								_t1439.FormulaType = &pb.Formula_Not{Not: not767}
								_t1437 = _t1439
							} else {
								var _t1440 *pb.Formula
								if prediction760 == 5 {
									_t1441 := p.parse_disjunction()
									disjunction766 := _t1441
									_t1442 := &pb.Formula{}
									_t1442.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction766}
									_t1440 = _t1442
								} else {
									var _t1443 *pb.Formula
									if prediction760 == 4 {
										_t1444 := p.parse_conjunction()
										conjunction765 := _t1444
										_t1445 := &pb.Formula{}
										_t1445.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction765}
										_t1443 = _t1445
									} else {
										var _t1446 *pb.Formula
										if prediction760 == 3 {
											_t1447 := p.parse_reduce()
											reduce764 := _t1447
											_t1448 := &pb.Formula{}
											_t1448.FormulaType = &pb.Formula_Reduce{Reduce: reduce764}
											_t1446 = _t1448
										} else {
											var _t1449 *pb.Formula
											if prediction760 == 2 {
												_t1450 := p.parse_exists()
												exists763 := _t1450
												_t1451 := &pb.Formula{}
												_t1451.FormulaType = &pb.Formula_Exists{Exists: exists763}
												_t1449 = _t1451
											} else {
												var _t1452 *pb.Formula
												if prediction760 == 1 {
													_t1453 := p.parse_false()
													false762 := _t1453
													_t1454 := &pb.Formula{}
													_t1454.FormulaType = &pb.Formula_Disjunction{Disjunction: false762}
													_t1452 = _t1454
												} else {
													var _t1455 *pb.Formula
													if prediction760 == 0 {
														_t1456 := p.parse_true()
														true761 := _t1456
														_t1457 := &pb.Formula{}
														_t1457.FormulaType = &pb.Formula_Conjunction{Conjunction: true761}
														_t1455 = _t1457
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1452 = _t1455
												}
												_t1449 = _t1452
											}
											_t1446 = _t1449
										}
										_t1443 = _t1446
									}
									_t1440 = _t1443
								}
								_t1437 = _t1440
							}
							_t1434 = _t1437
						}
						_t1431 = _t1434
					}
					_t1428 = _t1431
				}
				_t1425 = _t1428
			}
			_t1422 = _t1425
		}
		_t1419 = _t1422
	}
	result775 := _t1419
	p.recordSpan(int(span_start774), "Formula")
	return result775
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1458 := &pb.Conjunction{Args: []*pb.Formula{}}
	result777 := _t1458
	p.recordSpan(int(span_start776), "Conjunction")
	return result777
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start778 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1459 := &pb.Disjunction{Args: []*pb.Formula{}}
	result779 := _t1459
	p.recordSpan(int(span_start778), "Disjunction")
	return result779
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start782 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1460 := p.parse_bindings()
	bindings780 := _t1460
	_t1461 := p.parse_formula()
	formula781 := _t1461
	p.consumeLiteral(")")
	_t1462 := &pb.Abstraction{Vars: listConcat(bindings780[0].([]*pb.Binding), bindings780[1].([]*pb.Binding)), Value: formula781}
	_t1463 := &pb.Exists{Body: _t1462}
	result783 := _t1463
	p.recordSpan(int(span_start782), "Exists")
	return result783
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start787 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1464 := p.parse_abstraction()
	abstraction784 := _t1464
	_t1465 := p.parse_abstraction()
	abstraction_3785 := _t1465
	_t1466 := p.parse_terms()
	terms786 := _t1466
	p.consumeLiteral(")")
	_t1467 := &pb.Reduce{Op: abstraction784, Body: abstraction_3785, Terms: terms786}
	result788 := _t1467
	p.recordSpan(int(span_start787), "Reduce")
	return result788
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs789 := []*pb.Term{}
	cond790 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond790 {
		_t1468 := p.parse_term()
		item791 := _t1468
		xs789 = append(xs789, item791)
		cond790 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms792 := xs789
	p.consumeLiteral(")")
	return terms792
}

func (p *Parser) parse_term() *pb.Term {
	span_start796 := int64(p.spanStart())
	var _t1469 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1469 = 1
	} else {
		var _t1470 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1470 = 1
		} else {
			var _t1471 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1471 = 1
			} else {
				var _t1472 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1472 = 1
				} else {
					var _t1473 int64
					if p.matchLookaheadTerminal("SYMBOL", 0) {
						_t1473 = 0
					} else {
						var _t1474 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1474 = 1
						} else {
							var _t1475 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1475 = 1
							} else {
								var _t1476 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1476 = 1
								} else {
									var _t1477 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1477 = 1
									} else {
										var _t1478 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1478 = 1
										} else {
											var _t1479 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1479 = 1
											} else {
												var _t1480 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1480 = 1
												} else {
													var _t1481 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1481 = 1
													} else {
														_t1481 = -1
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
		_t1469 = _t1470
	}
	prediction793 := _t1469
	var _t1482 *pb.Term
	if prediction793 == 1 {
		_t1483 := p.parse_value()
		value795 := _t1483
		_t1484 := &pb.Term{}
		_t1484.TermType = &pb.Term_Constant{Constant: value795}
		_t1482 = _t1484
	} else {
		var _t1485 *pb.Term
		if prediction793 == 0 {
			_t1486 := p.parse_var()
			var794 := _t1486
			_t1487 := &pb.Term{}
			_t1487.TermType = &pb.Term_Var{Var: var794}
			_t1485 = _t1487
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1482 = _t1485
	}
	result797 := _t1482
	p.recordSpan(int(span_start796), "Term")
	return result797
}

func (p *Parser) parse_var() *pb.Var {
	span_start799 := int64(p.spanStart())
	symbol798 := p.consumeTerminal("SYMBOL").Value.str
	_t1488 := &pb.Var{Name: symbol798}
	result800 := _t1488
	p.recordSpan(int(span_start799), "Var")
	return result800
}

func (p *Parser) parse_value() *pb.Value {
	span_start813 := int64(p.spanStart())
	var _t1489 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1489 = 11
	} else {
		var _t1490 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1490 = 10
		} else {
			var _t1491 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1491 = 11
			} else {
				var _t1492 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1493 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1493 = 1
					} else {
						var _t1494 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1494 = 0
						} else {
							_t1494 = -1
						}
						_t1493 = _t1494
					}
					_t1492 = _t1493
				} else {
					var _t1495 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1495 = 7
					} else {
						var _t1496 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1496 = 2
						} else {
							var _t1497 int64
							if p.matchLookaheadTerminal("INT32", 0) {
								_t1497 = 3
							} else {
								var _t1498 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1498 = 8
								} else {
									var _t1499 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1499 = 4
									} else {
										var _t1500 int64
										if p.matchLookaheadTerminal("FLOAT32", 0) {
											_t1500 = 5
										} else {
											var _t1501 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1501 = 6
											} else {
												var _t1502 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1502 = 9
												} else {
													_t1502 = -1
												}
												_t1501 = _t1502
											}
											_t1500 = _t1501
										}
										_t1499 = _t1500
									}
									_t1498 = _t1499
								}
								_t1497 = _t1498
							}
							_t1496 = _t1497
						}
						_t1495 = _t1496
					}
					_t1492 = _t1495
				}
				_t1491 = _t1492
			}
			_t1490 = _t1491
		}
		_t1489 = _t1490
	}
	prediction801 := _t1489
	var _t1503 *pb.Value
	if prediction801 == 11 {
		_t1504 := p.parse_boolean_value()
		boolean_value812 := _t1504
		_t1505 := &pb.Value{}
		_t1505.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value812}
		_t1503 = _t1505
	} else {
		var _t1506 *pb.Value
		if prediction801 == 10 {
			p.consumeLiteral("missing")
			_t1507 := &pb.MissingValue{}
			_t1508 := &pb.Value{}
			_t1508.Value = &pb.Value_MissingValue{MissingValue: _t1507}
			_t1506 = _t1508
		} else {
			var _t1509 *pb.Value
			if prediction801 == 9 {
				formatted_decimal811 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1510 := &pb.Value{}
				_t1510.Value = &pb.Value_DecimalValue{DecimalValue: formatted_decimal811}
				_t1509 = _t1510
			} else {
				var _t1511 *pb.Value
				if prediction801 == 8 {
					formatted_int128810 := p.consumeTerminal("INT128").Value.int128
					_t1512 := &pb.Value{}
					_t1512.Value = &pb.Value_Int128Value{Int128Value: formatted_int128810}
					_t1511 = _t1512
				} else {
					var _t1513 *pb.Value
					if prediction801 == 7 {
						formatted_uint128809 := p.consumeTerminal("UINT128").Value.uint128
						_t1514 := &pb.Value{}
						_t1514.Value = &pb.Value_Uint128Value{Uint128Value: formatted_uint128809}
						_t1513 = _t1514
					} else {
						var _t1515 *pb.Value
						if prediction801 == 6 {
							formatted_float808 := p.consumeTerminal("FLOAT").Value.f64
							_t1516 := &pb.Value{}
							_t1516.Value = &pb.Value_FloatValue{FloatValue: formatted_float808}
							_t1515 = _t1516
						} else {
							var _t1517 *pb.Value
							if prediction801 == 5 {
								formatted_float32807 := p.consumeTerminal("FLOAT32").Value.f32
								_t1518 := &pb.Value{}
								_t1518.Value = &pb.Value_Float32Value{Float32Value: formatted_float32807}
								_t1517 = _t1518
							} else {
								var _t1519 *pb.Value
								if prediction801 == 4 {
									formatted_int806 := p.consumeTerminal("INT").Value.i64
									_t1520 := &pb.Value{}
									_t1520.Value = &pb.Value_IntValue{IntValue: formatted_int806}
									_t1519 = _t1520
								} else {
									var _t1521 *pb.Value
									if prediction801 == 3 {
										formatted_int32805 := p.consumeTerminal("INT32").Value.i32
										_t1522 := &pb.Value{}
										_t1522.Value = &pb.Value_Int32Value{Int32Value: formatted_int32805}
										_t1521 = _t1522
									} else {
										var _t1523 *pb.Value
										if prediction801 == 2 {
											formatted_string804 := p.consumeTerminal("STRING").Value.str
											_t1524 := &pb.Value{}
											_t1524.Value = &pb.Value_StringValue{StringValue: formatted_string804}
											_t1523 = _t1524
										} else {
											var _t1525 *pb.Value
											if prediction801 == 1 {
												_t1526 := p.parse_datetime()
												datetime803 := _t1526
												_t1527 := &pb.Value{}
												_t1527.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime803}
												_t1525 = _t1527
											} else {
												var _t1528 *pb.Value
												if prediction801 == 0 {
													_t1529 := p.parse_date()
													date802 := _t1529
													_t1530 := &pb.Value{}
													_t1530.Value = &pb.Value_DateValue{DateValue: date802}
													_t1528 = _t1530
												} else {
													panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
												}
												_t1525 = _t1528
											}
											_t1523 = _t1525
										}
										_t1521 = _t1523
									}
									_t1519 = _t1521
								}
								_t1517 = _t1519
							}
							_t1515 = _t1517
						}
						_t1513 = _t1515
					}
					_t1511 = _t1513
				}
				_t1509 = _t1511
			}
			_t1506 = _t1509
		}
		_t1503 = _t1506
	}
	result814 := _t1503
	p.recordSpan(int(span_start813), "Value")
	return result814
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	formatted_int815 := p.consumeTerminal("INT").Value.i64
	formatted_int_3816 := p.consumeTerminal("INT").Value.i64
	formatted_int_4817 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1531 := &pb.DateValue{Year: int32(formatted_int815), Month: int32(formatted_int_3816), Day: int32(formatted_int_4817)}
	result819 := _t1531
	p.recordSpan(int(span_start818), "DateValue")
	return result819
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start827 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	formatted_int820 := p.consumeTerminal("INT").Value.i64
	formatted_int_3821 := p.consumeTerminal("INT").Value.i64
	formatted_int_4822 := p.consumeTerminal("INT").Value.i64
	formatted_int_5823 := p.consumeTerminal("INT").Value.i64
	formatted_int_6824 := p.consumeTerminal("INT").Value.i64
	formatted_int_7825 := p.consumeTerminal("INT").Value.i64
	var _t1532 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1532 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	formatted_int_8826 := _t1532
	p.consumeLiteral(")")
	_t1533 := &pb.DateTimeValue{Year: int32(formatted_int820), Month: int32(formatted_int_3821), Day: int32(formatted_int_4822), Hour: int32(formatted_int_5823), Minute: int32(formatted_int_6824), Second: int32(formatted_int_7825), Microsecond: int32(deref(formatted_int_8826, 0))}
	result828 := _t1533
	p.recordSpan(int(span_start827), "DateTimeValue")
	return result828
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start833 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs829 := []*pb.Formula{}
	cond830 := p.matchLookaheadLiteral("(", 0)
	for cond830 {
		_t1534 := p.parse_formula()
		item831 := _t1534
		xs829 = append(xs829, item831)
		cond830 = p.matchLookaheadLiteral("(", 0)
	}
	formulas832 := xs829
	p.consumeLiteral(")")
	_t1535 := &pb.Conjunction{Args: formulas832}
	result834 := _t1535
	p.recordSpan(int(span_start833), "Conjunction")
	return result834
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start839 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs835 := []*pb.Formula{}
	cond836 := p.matchLookaheadLiteral("(", 0)
	for cond836 {
		_t1536 := p.parse_formula()
		item837 := _t1536
		xs835 = append(xs835, item837)
		cond836 = p.matchLookaheadLiteral("(", 0)
	}
	formulas838 := xs835
	p.consumeLiteral(")")
	_t1537 := &pb.Disjunction{Args: formulas838}
	result840 := _t1537
	p.recordSpan(int(span_start839), "Disjunction")
	return result840
}

func (p *Parser) parse_not() *pb.Not {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1538 := p.parse_formula()
	formula841 := _t1538
	p.consumeLiteral(")")
	_t1539 := &pb.Not{Arg: formula841}
	result843 := _t1539
	p.recordSpan(int(span_start842), "Not")
	return result843
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1540 := p.parse_name()
	name844 := _t1540
	_t1541 := p.parse_ffi_args()
	ffi_args845 := _t1541
	_t1542 := p.parse_terms()
	terms846 := _t1542
	p.consumeLiteral(")")
	_t1543 := &pb.FFI{Name: name844, Args: ffi_args845, Terms: terms846}
	result848 := _t1543
	p.recordSpan(int(span_start847), "FFI")
	return result848
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol849 := p.consumeTerminal("SYMBOL").Value.str
	return symbol849
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs850 := []*pb.Abstraction{}
	cond851 := p.matchLookaheadLiteral("(", 0)
	for cond851 {
		_t1544 := p.parse_abstraction()
		item852 := _t1544
		xs850 = append(xs850, item852)
		cond851 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions853 := xs850
	p.consumeLiteral(")")
	return abstractions853
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start859 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1545 := p.parse_relation_id()
	relation_id854 := _t1545
	xs855 := []*pb.Term{}
	cond856 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond856 {
		_t1546 := p.parse_term()
		item857 := _t1546
		xs855 = append(xs855, item857)
		cond856 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms858 := xs855
	p.consumeLiteral(")")
	_t1547 := &pb.Atom{Name: relation_id854, Terms: terms858}
	result860 := _t1547
	p.recordSpan(int(span_start859), "Atom")
	return result860
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1548 := p.parse_name()
	name861 := _t1548
	xs862 := []*pb.Term{}
	cond863 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond863 {
		_t1549 := p.parse_term()
		item864 := _t1549
		xs862 = append(xs862, item864)
		cond863 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	terms865 := xs862
	p.consumeLiteral(")")
	_t1550 := &pb.Pragma{Name: name861, Terms: terms865}
	result867 := _t1550
	p.recordSpan(int(span_start866), "Pragma")
	return result867
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start883 := int64(p.spanStart())
	var _t1551 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1552 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1552 = 9
		} else {
			var _t1553 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1553 = 4
			} else {
				var _t1554 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1554 = 3
				} else {
					var _t1555 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1555 = 0
					} else {
						var _t1556 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1556 = 2
						} else {
							var _t1557 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1557 = 1
							} else {
								var _t1558 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1558 = 8
								} else {
									var _t1559 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1559 = 6
									} else {
										var _t1560 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1560 = 5
										} else {
											var _t1561 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1561 = 7
											} else {
												_t1561 = -1
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
	} else {
		_t1551 = -1
	}
	prediction868 := _t1551
	var _t1562 *pb.Primitive
	if prediction868 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1563 := p.parse_name()
		name878 := _t1563
		xs879 := []*pb.RelTerm{}
		cond880 := (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		for cond880 {
			_t1564 := p.parse_rel_term()
			item881 := _t1564
			xs879 = append(xs879, item881)
			cond880 = (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
		}
		rel_terms882 := xs879
		p.consumeLiteral(")")
		_t1565 := &pb.Primitive{Name: name878, Terms: rel_terms882}
		_t1562 = _t1565
	} else {
		var _t1566 *pb.Primitive
		if prediction868 == 8 {
			_t1567 := p.parse_divide()
			divide877 := _t1567
			_t1566 = divide877
		} else {
			var _t1568 *pb.Primitive
			if prediction868 == 7 {
				_t1569 := p.parse_multiply()
				multiply876 := _t1569
				_t1568 = multiply876
			} else {
				var _t1570 *pb.Primitive
				if prediction868 == 6 {
					_t1571 := p.parse_minus()
					minus875 := _t1571
					_t1570 = minus875
				} else {
					var _t1572 *pb.Primitive
					if prediction868 == 5 {
						_t1573 := p.parse_add()
						add874 := _t1573
						_t1572 = add874
					} else {
						var _t1574 *pb.Primitive
						if prediction868 == 4 {
							_t1575 := p.parse_gt_eq()
							gt_eq873 := _t1575
							_t1574 = gt_eq873
						} else {
							var _t1576 *pb.Primitive
							if prediction868 == 3 {
								_t1577 := p.parse_gt()
								gt872 := _t1577
								_t1576 = gt872
							} else {
								var _t1578 *pb.Primitive
								if prediction868 == 2 {
									_t1579 := p.parse_lt_eq()
									lt_eq871 := _t1579
									_t1578 = lt_eq871
								} else {
									var _t1580 *pb.Primitive
									if prediction868 == 1 {
										_t1581 := p.parse_lt()
										lt870 := _t1581
										_t1580 = lt870
									} else {
										var _t1582 *pb.Primitive
										if prediction868 == 0 {
											_t1583 := p.parse_eq()
											eq869 := _t1583
											_t1582 = eq869
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1580 = _t1582
									}
									_t1578 = _t1580
								}
								_t1576 = _t1578
							}
							_t1574 = _t1576
						}
						_t1572 = _t1574
					}
					_t1570 = _t1572
				}
				_t1568 = _t1570
			}
			_t1566 = _t1568
		}
		_t1562 = _t1566
	}
	result884 := _t1562
	p.recordSpan(int(span_start883), "Primitive")
	return result884
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start887 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1584 := p.parse_term()
	term885 := _t1584
	_t1585 := p.parse_term()
	term_3886 := _t1585
	p.consumeLiteral(")")
	_t1586 := &pb.RelTerm{}
	_t1586.RelTermType = &pb.RelTerm_Term{Term: term885}
	_t1587 := &pb.RelTerm{}
	_t1587.RelTermType = &pb.RelTerm_Term{Term: term_3886}
	_t1588 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1586, _t1587}}
	result888 := _t1588
	p.recordSpan(int(span_start887), "Primitive")
	return result888
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1589 := p.parse_term()
	term889 := _t1589
	_t1590 := p.parse_term()
	term_3890 := _t1590
	p.consumeLiteral(")")
	_t1591 := &pb.RelTerm{}
	_t1591.RelTermType = &pb.RelTerm_Term{Term: term889}
	_t1592 := &pb.RelTerm{}
	_t1592.RelTermType = &pb.RelTerm_Term{Term: term_3890}
	_t1593 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1591, _t1592}}
	result892 := _t1593
	p.recordSpan(int(span_start891), "Primitive")
	return result892
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start895 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1594 := p.parse_term()
	term893 := _t1594
	_t1595 := p.parse_term()
	term_3894 := _t1595
	p.consumeLiteral(")")
	_t1596 := &pb.RelTerm{}
	_t1596.RelTermType = &pb.RelTerm_Term{Term: term893}
	_t1597 := &pb.RelTerm{}
	_t1597.RelTermType = &pb.RelTerm_Term{Term: term_3894}
	_t1598 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1596, _t1597}}
	result896 := _t1598
	p.recordSpan(int(span_start895), "Primitive")
	return result896
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start899 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1599 := p.parse_term()
	term897 := _t1599
	_t1600 := p.parse_term()
	term_3898 := _t1600
	p.consumeLiteral(")")
	_t1601 := &pb.RelTerm{}
	_t1601.RelTermType = &pb.RelTerm_Term{Term: term897}
	_t1602 := &pb.RelTerm{}
	_t1602.RelTermType = &pb.RelTerm_Term{Term: term_3898}
	_t1603 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1601, _t1602}}
	result900 := _t1603
	p.recordSpan(int(span_start899), "Primitive")
	return result900
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1604 := p.parse_term()
	term901 := _t1604
	_t1605 := p.parse_term()
	term_3902 := _t1605
	p.consumeLiteral(")")
	_t1606 := &pb.RelTerm{}
	_t1606.RelTermType = &pb.RelTerm_Term{Term: term901}
	_t1607 := &pb.RelTerm{}
	_t1607.RelTermType = &pb.RelTerm_Term{Term: term_3902}
	_t1608 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1606, _t1607}}
	result904 := _t1608
	p.recordSpan(int(span_start903), "Primitive")
	return result904
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start908 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1609 := p.parse_term()
	term905 := _t1609
	_t1610 := p.parse_term()
	term_3906 := _t1610
	_t1611 := p.parse_term()
	term_4907 := _t1611
	p.consumeLiteral(")")
	_t1612 := &pb.RelTerm{}
	_t1612.RelTermType = &pb.RelTerm_Term{Term: term905}
	_t1613 := &pb.RelTerm{}
	_t1613.RelTermType = &pb.RelTerm_Term{Term: term_3906}
	_t1614 := &pb.RelTerm{}
	_t1614.RelTermType = &pb.RelTerm_Term{Term: term_4907}
	_t1615 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1612, _t1613, _t1614}}
	result909 := _t1615
	p.recordSpan(int(span_start908), "Primitive")
	return result909
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start913 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1616 := p.parse_term()
	term910 := _t1616
	_t1617 := p.parse_term()
	term_3911 := _t1617
	_t1618 := p.parse_term()
	term_4912 := _t1618
	p.consumeLiteral(")")
	_t1619 := &pb.RelTerm{}
	_t1619.RelTermType = &pb.RelTerm_Term{Term: term910}
	_t1620 := &pb.RelTerm{}
	_t1620.RelTermType = &pb.RelTerm_Term{Term: term_3911}
	_t1621 := &pb.RelTerm{}
	_t1621.RelTermType = &pb.RelTerm_Term{Term: term_4912}
	_t1622 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1619, _t1620, _t1621}}
	result914 := _t1622
	p.recordSpan(int(span_start913), "Primitive")
	return result914
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1623 := p.parse_term()
	term915 := _t1623
	_t1624 := p.parse_term()
	term_3916 := _t1624
	_t1625 := p.parse_term()
	term_4917 := _t1625
	p.consumeLiteral(")")
	_t1626 := &pb.RelTerm{}
	_t1626.RelTermType = &pb.RelTerm_Term{Term: term915}
	_t1627 := &pb.RelTerm{}
	_t1627.RelTermType = &pb.RelTerm_Term{Term: term_3916}
	_t1628 := &pb.RelTerm{}
	_t1628.RelTermType = &pb.RelTerm_Term{Term: term_4917}
	_t1629 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1626, _t1627, _t1628}}
	result919 := _t1629
	p.recordSpan(int(span_start918), "Primitive")
	return result919
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start923 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1630 := p.parse_term()
	term920 := _t1630
	_t1631 := p.parse_term()
	term_3921 := _t1631
	_t1632 := p.parse_term()
	term_4922 := _t1632
	p.consumeLiteral(")")
	_t1633 := &pb.RelTerm{}
	_t1633.RelTermType = &pb.RelTerm_Term{Term: term920}
	_t1634 := &pb.RelTerm{}
	_t1634.RelTermType = &pb.RelTerm_Term{Term: term_3921}
	_t1635 := &pb.RelTerm{}
	_t1635.RelTermType = &pb.RelTerm_Term{Term: term_4922}
	_t1636 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1633, _t1634, _t1635}}
	result924 := _t1636
	p.recordSpan(int(span_start923), "Primitive")
	return result924
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start928 := int64(p.spanStart())
	var _t1637 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1637 = 1
	} else {
		var _t1638 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1638 = 1
		} else {
			var _t1639 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1639 = 1
			} else {
				var _t1640 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1640 = 1
				} else {
					var _t1641 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1641 = 0
					} else {
						var _t1642 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1642 = 1
						} else {
							var _t1643 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1643 = 1
							} else {
								var _t1644 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1644 = 1
								} else {
									var _t1645 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1645 = 1
									} else {
										var _t1646 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1646 = 1
										} else {
											var _t1647 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1647 = 1
											} else {
												var _t1648 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1648 = 1
												} else {
													var _t1649 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1649 = 1
													} else {
														var _t1650 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1650 = 1
														} else {
															_t1650 = -1
														}
														_t1649 = _t1650
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
					_t1640 = _t1641
				}
				_t1639 = _t1640
			}
			_t1638 = _t1639
		}
		_t1637 = _t1638
	}
	prediction925 := _t1637
	var _t1651 *pb.RelTerm
	if prediction925 == 1 {
		_t1652 := p.parse_term()
		term927 := _t1652
		_t1653 := &pb.RelTerm{}
		_t1653.RelTermType = &pb.RelTerm_Term{Term: term927}
		_t1651 = _t1653
	} else {
		var _t1654 *pb.RelTerm
		if prediction925 == 0 {
			_t1655 := p.parse_specialized_value()
			specialized_value926 := _t1655
			_t1656 := &pb.RelTerm{}
			_t1656.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value926}
			_t1654 = _t1656
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1651 = _t1654
	}
	result929 := _t1651
	p.recordSpan(int(span_start928), "RelTerm")
	return result929
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start931 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1657 := p.parse_raw_value()
	raw_value930 := _t1657
	result932 := raw_value930
	p.recordSpan(int(span_start931), "Value")
	return result932
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start938 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1658 := p.parse_name()
	name933 := _t1658
	xs934 := []*pb.RelTerm{}
	cond935 := (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	for cond935 {
		_t1659 := p.parse_rel_term()
		item936 := _t1659
		xs934 = append(xs934, item936)
		cond935 = (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("SYMBOL", 0))
	}
	rel_terms937 := xs934
	p.consumeLiteral(")")
	_t1660 := &pb.RelAtom{Name: name933, Terms: rel_terms937}
	result939 := _t1660
	p.recordSpan(int(span_start938), "RelAtom")
	return result939
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1661 := p.parse_term()
	term940 := _t1661
	_t1662 := p.parse_term()
	term_3941 := _t1662
	p.consumeLiteral(")")
	_t1663 := &pb.Cast{Input: term940, Result: term_3941}
	result943 := _t1663
	p.recordSpan(int(span_start942), "Cast")
	return result943
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs944 := []*pb.Attribute{}
	cond945 := p.matchLookaheadLiteral("(", 0)
	for cond945 {
		_t1664 := p.parse_attribute()
		item946 := _t1664
		xs944 = append(xs944, item946)
		cond945 = p.matchLookaheadLiteral("(", 0)
	}
	attributes947 := xs944
	p.consumeLiteral(")")
	return attributes947
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1665 := p.parse_name()
	name948 := _t1665
	xs949 := []*pb.Value{}
	cond950 := (((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond950 {
		_t1666 := p.parse_raw_value()
		item951 := _t1666
		xs949 = append(xs949, item951)
		cond950 = (((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	raw_values952 := xs949
	p.consumeLiteral(")")
	_t1667 := &pb.Attribute{Name: name948, Args: raw_values952}
	result954 := _t1667
	p.recordSpan(int(span_start953), "Attribute")
	return result954
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs955 := []*pb.RelationId{}
	cond956 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond956 {
		_t1668 := p.parse_relation_id()
		item957 := _t1668
		xs955 = append(xs955, item957)
		cond956 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids958 := xs955
	_t1669 := p.parse_script()
	script959 := _t1669
	p.consumeLiteral(")")
	_t1670 := &pb.Algorithm{Global: relation_ids958, Body: script959}
	result961 := _t1670
	p.recordSpan(int(span_start960), "Algorithm")
	return result961
}

func (p *Parser) parse_script() *pb.Script {
	span_start966 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs962 := []*pb.Construct{}
	cond963 := p.matchLookaheadLiteral("(", 0)
	for cond963 {
		_t1671 := p.parse_construct()
		item964 := _t1671
		xs962 = append(xs962, item964)
		cond963 = p.matchLookaheadLiteral("(", 0)
	}
	constructs965 := xs962
	p.consumeLiteral(")")
	_t1672 := &pb.Script{Constructs: constructs965}
	result967 := _t1672
	p.recordSpan(int(span_start966), "Script")
	return result967
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start971 := int64(p.spanStart())
	var _t1673 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1674 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1674 = 1
		} else {
			var _t1675 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1675 = 1
			} else {
				var _t1676 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1676 = 1
				} else {
					var _t1677 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1677 = 0
					} else {
						var _t1678 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1678 = 1
						} else {
							var _t1679 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1679 = 1
							} else {
								_t1679 = -1
							}
							_t1678 = _t1679
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
	} else {
		_t1673 = -1
	}
	prediction968 := _t1673
	var _t1680 *pb.Construct
	if prediction968 == 1 {
		_t1681 := p.parse_instruction()
		instruction970 := _t1681
		_t1682 := &pb.Construct{}
		_t1682.ConstructType = &pb.Construct_Instruction{Instruction: instruction970}
		_t1680 = _t1682
	} else {
		var _t1683 *pb.Construct
		if prediction968 == 0 {
			_t1684 := p.parse_loop()
			loop969 := _t1684
			_t1685 := &pb.Construct{}
			_t1685.ConstructType = &pb.Construct_Loop{Loop: loop969}
			_t1683 = _t1685
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1680 = _t1683
	}
	result972 := _t1680
	p.recordSpan(int(span_start971), "Construct")
	return result972
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1686 := p.parse_init()
	init973 := _t1686
	_t1687 := p.parse_script()
	script974 := _t1687
	p.consumeLiteral(")")
	_t1688 := &pb.Loop{Init: init973, Body: script974}
	result976 := _t1688
	p.recordSpan(int(span_start975), "Loop")
	return result976
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs977 := []*pb.Instruction{}
	cond978 := p.matchLookaheadLiteral("(", 0)
	for cond978 {
		_t1689 := p.parse_instruction()
		item979 := _t1689
		xs977 = append(xs977, item979)
		cond978 = p.matchLookaheadLiteral("(", 0)
	}
	instructions980 := xs977
	p.consumeLiteral(")")
	return instructions980
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start987 := int64(p.spanStart())
	var _t1690 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1691 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1691 = 1
		} else {
			var _t1692 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1692 = 4
			} else {
				var _t1693 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1693 = 3
				} else {
					var _t1694 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1694 = 2
					} else {
						var _t1695 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1695 = 0
						} else {
							_t1695 = -1
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
	} else {
		_t1690 = -1
	}
	prediction981 := _t1690
	var _t1696 *pb.Instruction
	if prediction981 == 4 {
		_t1697 := p.parse_monus_def()
		monus_def986 := _t1697
		_t1698 := &pb.Instruction{}
		_t1698.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def986}
		_t1696 = _t1698
	} else {
		var _t1699 *pb.Instruction
		if prediction981 == 3 {
			_t1700 := p.parse_monoid_def()
			monoid_def985 := _t1700
			_t1701 := &pb.Instruction{}
			_t1701.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def985}
			_t1699 = _t1701
		} else {
			var _t1702 *pb.Instruction
			if prediction981 == 2 {
				_t1703 := p.parse_break()
				break984 := _t1703
				_t1704 := &pb.Instruction{}
				_t1704.InstrType = &pb.Instruction_Break{Break: break984}
				_t1702 = _t1704
			} else {
				var _t1705 *pb.Instruction
				if prediction981 == 1 {
					_t1706 := p.parse_upsert()
					upsert983 := _t1706
					_t1707 := &pb.Instruction{}
					_t1707.InstrType = &pb.Instruction_Upsert{Upsert: upsert983}
					_t1705 = _t1707
				} else {
					var _t1708 *pb.Instruction
					if prediction981 == 0 {
						_t1709 := p.parse_assign()
						assign982 := _t1709
						_t1710 := &pb.Instruction{}
						_t1710.InstrType = &pb.Instruction_Assign{Assign: assign982}
						_t1708 = _t1710
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1705 = _t1708
				}
				_t1702 = _t1705
			}
			_t1699 = _t1702
		}
		_t1696 = _t1699
	}
	result988 := _t1696
	p.recordSpan(int(span_start987), "Instruction")
	return result988
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start992 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1711 := p.parse_relation_id()
	relation_id989 := _t1711
	_t1712 := p.parse_abstraction()
	abstraction990 := _t1712
	var _t1713 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1714 := p.parse_attrs()
		_t1713 = _t1714
	}
	attrs991 := _t1713
	p.consumeLiteral(")")
	_t1715 := attrs991
	if attrs991 == nil {
		_t1715 = []*pb.Attribute{}
	}
	_t1716 := &pb.Assign{Name: relation_id989, Body: abstraction990, Attrs: _t1715}
	result993 := _t1716
	p.recordSpan(int(span_start992), "Assign")
	return result993
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start997 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1717 := p.parse_relation_id()
	relation_id994 := _t1717
	_t1718 := p.parse_abstraction_with_arity()
	abstraction_with_arity995 := _t1718
	var _t1719 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1720 := p.parse_attrs()
		_t1719 = _t1720
	}
	attrs996 := _t1719
	p.consumeLiteral(")")
	_t1721 := attrs996
	if attrs996 == nil {
		_t1721 = []*pb.Attribute{}
	}
	_t1722 := &pb.Upsert{Name: relation_id994, Body: abstraction_with_arity995[0].(*pb.Abstraction), Attrs: _t1721, ValueArity: abstraction_with_arity995[1].(int64)}
	result998 := _t1722
	p.recordSpan(int(span_start997), "Upsert")
	return result998
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1723 := p.parse_bindings()
	bindings999 := _t1723
	_t1724 := p.parse_formula()
	formula1000 := _t1724
	p.consumeLiteral(")")
	_t1725 := &pb.Abstraction{Vars: listConcat(bindings999[0].([]*pb.Binding), bindings999[1].([]*pb.Binding)), Value: formula1000}
	return []interface{}{_t1725, int64(len(bindings999[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1726 := p.parse_relation_id()
	relation_id1001 := _t1726
	_t1727 := p.parse_abstraction()
	abstraction1002 := _t1727
	var _t1728 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1729 := p.parse_attrs()
		_t1728 = _t1729
	}
	attrs1003 := _t1728
	p.consumeLiteral(")")
	_t1730 := attrs1003
	if attrs1003 == nil {
		_t1730 = []*pb.Attribute{}
	}
	_t1731 := &pb.Break{Name: relation_id1001, Body: abstraction1002, Attrs: _t1730}
	result1005 := _t1731
	p.recordSpan(int(span_start1004), "Break")
	return result1005
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1010 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1732 := p.parse_monoid()
	monoid1006 := _t1732
	_t1733 := p.parse_relation_id()
	relation_id1007 := _t1733
	_t1734 := p.parse_abstraction_with_arity()
	abstraction_with_arity1008 := _t1734
	var _t1735 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1736 := p.parse_attrs()
		_t1735 = _t1736
	}
	attrs1009 := _t1735
	p.consumeLiteral(")")
	_t1737 := attrs1009
	if attrs1009 == nil {
		_t1737 = []*pb.Attribute{}
	}
	_t1738 := &pb.MonoidDef{Monoid: monoid1006, Name: relation_id1007, Body: abstraction_with_arity1008[0].(*pb.Abstraction), Attrs: _t1737, ValueArity: abstraction_with_arity1008[1].(int64)}
	result1011 := _t1738
	p.recordSpan(int(span_start1010), "MonoidDef")
	return result1011
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1017 := int64(p.spanStart())
	var _t1739 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1740 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1740 = 3
		} else {
			var _t1741 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1741 = 0
			} else {
				var _t1742 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1742 = 1
				} else {
					var _t1743 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1743 = 2
					} else {
						_t1743 = -1
					}
					_t1742 = _t1743
				}
				_t1741 = _t1742
			}
			_t1740 = _t1741
		}
		_t1739 = _t1740
	} else {
		_t1739 = -1
	}
	prediction1012 := _t1739
	var _t1744 *pb.Monoid
	if prediction1012 == 3 {
		_t1745 := p.parse_sum_monoid()
		sum_monoid1016 := _t1745
		_t1746 := &pb.Monoid{}
		_t1746.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1016}
		_t1744 = _t1746
	} else {
		var _t1747 *pb.Monoid
		if prediction1012 == 2 {
			_t1748 := p.parse_max_monoid()
			max_monoid1015 := _t1748
			_t1749 := &pb.Monoid{}
			_t1749.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1015}
			_t1747 = _t1749
		} else {
			var _t1750 *pb.Monoid
			if prediction1012 == 1 {
				_t1751 := p.parse_min_monoid()
				min_monoid1014 := _t1751
				_t1752 := &pb.Monoid{}
				_t1752.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1014}
				_t1750 = _t1752
			} else {
				var _t1753 *pb.Monoid
				if prediction1012 == 0 {
					_t1754 := p.parse_or_monoid()
					or_monoid1013 := _t1754
					_t1755 := &pb.Monoid{}
					_t1755.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1013}
					_t1753 = _t1755
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1750 = _t1753
			}
			_t1747 = _t1750
		}
		_t1744 = _t1747
	}
	result1018 := _t1744
	p.recordSpan(int(span_start1017), "Monoid")
	return result1018
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1019 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1756 := &pb.OrMonoid{}
	result1020 := _t1756
	p.recordSpan(int(span_start1019), "OrMonoid")
	return result1020
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1757 := p.parse_type()
	type1021 := _t1757
	p.consumeLiteral(")")
	_t1758 := &pb.MinMonoid{Type: type1021}
	result1023 := _t1758
	p.recordSpan(int(span_start1022), "MinMonoid")
	return result1023
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1025 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1759 := p.parse_type()
	type1024 := _t1759
	p.consumeLiteral(")")
	_t1760 := &pb.MaxMonoid{Type: type1024}
	result1026 := _t1760
	p.recordSpan(int(span_start1025), "MaxMonoid")
	return result1026
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1761 := p.parse_type()
	type1027 := _t1761
	p.consumeLiteral(")")
	_t1762 := &pb.SumMonoid{Type: type1027}
	result1029 := _t1762
	p.recordSpan(int(span_start1028), "SumMonoid")
	return result1029
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1763 := p.parse_monoid()
	monoid1030 := _t1763
	_t1764 := p.parse_relation_id()
	relation_id1031 := _t1764
	_t1765 := p.parse_abstraction_with_arity()
	abstraction_with_arity1032 := _t1765
	var _t1766 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1767 := p.parse_attrs()
		_t1766 = _t1767
	}
	attrs1033 := _t1766
	p.consumeLiteral(")")
	_t1768 := attrs1033
	if attrs1033 == nil {
		_t1768 = []*pb.Attribute{}
	}
	_t1769 := &pb.MonusDef{Monoid: monoid1030, Name: relation_id1031, Body: abstraction_with_arity1032[0].(*pb.Abstraction), Attrs: _t1768, ValueArity: abstraction_with_arity1032[1].(int64)}
	result1035 := _t1769
	p.recordSpan(int(span_start1034), "MonusDef")
	return result1035
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1770 := p.parse_relation_id()
	relation_id1036 := _t1770
	_t1771 := p.parse_abstraction()
	abstraction1037 := _t1771
	_t1772 := p.parse_functional_dependency_keys()
	functional_dependency_keys1038 := _t1772
	_t1773 := p.parse_functional_dependency_values()
	functional_dependency_values1039 := _t1773
	p.consumeLiteral(")")
	_t1774 := &pb.FunctionalDependency{Guard: abstraction1037, Keys: functional_dependency_keys1038, Values: functional_dependency_values1039}
	_t1775 := &pb.Constraint{Name: relation_id1036}
	_t1775.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1774}
	result1041 := _t1775
	p.recordSpan(int(span_start1040), "Constraint")
	return result1041
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1042 := []*pb.Var{}
	cond1043 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1043 {
		_t1776 := p.parse_var()
		item1044 := _t1776
		xs1042 = append(xs1042, item1044)
		cond1043 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1045 := xs1042
	p.consumeLiteral(")")
	return vars1045
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1046 := []*pb.Var{}
	cond1047 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1047 {
		_t1777 := p.parse_var()
		item1048 := _t1777
		xs1046 = append(xs1046, item1048)
		cond1047 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1049 := xs1046
	p.consumeLiteral(")")
	return vars1049
}

func (p *Parser) parse_data() *pb.Data {
	span_start1054 := int64(p.spanStart())
	var _t1778 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1779 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1779 = 0
		} else {
			var _t1780 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1780 = 2
			} else {
				var _t1781 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1781 = 1
				} else {
					_t1781 = -1
				}
				_t1780 = _t1781
			}
			_t1779 = _t1780
		}
		_t1778 = _t1779
	} else {
		_t1778 = -1
	}
	prediction1050 := _t1778
	var _t1782 *pb.Data
	if prediction1050 == 2 {
		_t1783 := p.parse_csv_data()
		csv_data1053 := _t1783
		_t1784 := &pb.Data{}
		_t1784.DataType = &pb.Data_CsvData{CsvData: csv_data1053}
		_t1782 = _t1784
	} else {
		var _t1785 *pb.Data
		if prediction1050 == 1 {
			_t1786 := p.parse_betree_relation()
			betree_relation1052 := _t1786
			_t1787 := &pb.Data{}
			_t1787.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1052}
			_t1785 = _t1787
		} else {
			var _t1788 *pb.Data
			if prediction1050 == 0 {
				_t1789 := p.parse_edb()
				edb1051 := _t1789
				_t1790 := &pb.Data{}
				_t1790.DataType = &pb.Data_Edb{Edb: edb1051}
				_t1788 = _t1790
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1785 = _t1788
		}
		_t1782 = _t1785
	}
	result1055 := _t1782
	p.recordSpan(int(span_start1054), "Data")
	return result1055
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1059 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1791 := p.parse_relation_id()
	relation_id1056 := _t1791
	_t1792 := p.parse_edb_path()
	edb_path1057 := _t1792
	_t1793 := p.parse_edb_types()
	edb_types1058 := _t1793
	p.consumeLiteral(")")
	_t1794 := &pb.EDB{TargetId: relation_id1056, Path: edb_path1057, Types: edb_types1058}
	result1060 := _t1794
	p.recordSpan(int(span_start1059), "EDB")
	return result1060
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1061 := []string{}
	cond1062 := p.matchLookaheadTerminal("STRING", 0)
	for cond1062 {
		item1063 := p.consumeTerminal("STRING").Value.str
		xs1061 = append(xs1061, item1063)
		cond1062 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1064 := xs1061
	p.consumeLiteral("]")
	return strings1064
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1065 := []*pb.Type{}
	cond1066 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1066 {
		_t1795 := p.parse_type()
		item1067 := _t1795
		xs1065 = append(xs1065, item1067)
		cond1066 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1068 := xs1065
	p.consumeLiteral("]")
	return types1068
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1071 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1796 := p.parse_relation_id()
	relation_id1069 := _t1796
	_t1797 := p.parse_betree_info()
	betree_info1070 := _t1797
	p.consumeLiteral(")")
	_t1798 := &pb.BeTreeRelation{Name: relation_id1069, RelationInfo: betree_info1070}
	result1072 := _t1798
	p.recordSpan(int(span_start1071), "BeTreeRelation")
	return result1072
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1076 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1799 := p.parse_betree_info_key_types()
	betree_info_key_types1073 := _t1799
	_t1800 := p.parse_betree_info_value_types()
	betree_info_value_types1074 := _t1800
	_t1801 := p.parse_config_dict()
	config_dict1075 := _t1801
	p.consumeLiteral(")")
	_t1802 := p.construct_betree_info(betree_info_key_types1073, betree_info_value_types1074, config_dict1075)
	result1077 := _t1802
	p.recordSpan(int(span_start1076), "BeTreeInfo")
	return result1077
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1078 := []*pb.Type{}
	cond1079 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1079 {
		_t1803 := p.parse_type()
		item1080 := _t1803
		xs1078 = append(xs1078, item1080)
		cond1079 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1081 := xs1078
	p.consumeLiteral(")")
	return types1081
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1082 := []*pb.Type{}
	cond1083 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1083 {
		_t1804 := p.parse_type()
		item1084 := _t1804
		xs1082 = append(xs1082, item1084)
		cond1083 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1085 := xs1082
	p.consumeLiteral(")")
	return types1085
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1090 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1805 := p.parse_csvlocator()
	csvlocator1086 := _t1805
	_t1806 := p.parse_csv_config()
	csv_config1087 := _t1806
	_t1807 := p.parse_gnf_columns()
	gnf_columns1088 := _t1807
	_t1808 := p.parse_csv_asof()
	csv_asof1089 := _t1808
	p.consumeLiteral(")")
	_t1809 := &pb.CSVData{Locator: csvlocator1086, Config: csv_config1087, Columns: gnf_columns1088, Asof: csv_asof1089}
	result1091 := _t1809
	p.recordSpan(int(span_start1090), "CSVData")
	return result1091
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1810 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1811 := p.parse_csv_locator_paths()
		_t1810 = _t1811
	}
	csv_locator_paths1092 := _t1810
	var _t1812 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1813 := p.parse_csv_locator_inline_data()
		_t1812 = ptr(_t1813)
	}
	csv_locator_inline_data1093 := _t1812
	p.consumeLiteral(")")
	_t1814 := csv_locator_paths1092
	if csv_locator_paths1092 == nil {
		_t1814 = []string{}
	}
	_t1815 := &pb.CSVLocator{Paths: _t1814, InlineData: []byte(deref(csv_locator_inline_data1093, ""))}
	result1095 := _t1815
	p.recordSpan(int(span_start1094), "CSVLocator")
	return result1095
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1096 := []string{}
	cond1097 := p.matchLookaheadTerminal("STRING", 0)
	for cond1097 {
		item1098 := p.consumeTerminal("STRING").Value.str
		xs1096 = append(xs1096, item1098)
		cond1097 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1099 := xs1096
	p.consumeLiteral(")")
	return strings1099
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1100 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1100
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1102 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1816 := p.parse_config_dict()
	config_dict1101 := _t1816
	p.consumeLiteral(")")
	_t1817 := p.construct_csv_config(config_dict1101)
	result1103 := _t1817
	p.recordSpan(int(span_start1102), "CSVConfig")
	return result1103
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1104 := []*pb.GNFColumn{}
	cond1105 := p.matchLookaheadLiteral("(", 0)
	for cond1105 {
		_t1818 := p.parse_gnf_column()
		item1106 := _t1818
		xs1104 = append(xs1104, item1106)
		cond1105 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1107 := xs1104
	p.consumeLiteral(")")
	return gnf_columns1107
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1114 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1819 := p.parse_gnf_column_path()
	gnf_column_path1108 := _t1819
	var _t1820 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1821 := p.parse_relation_id()
		_t1820 = _t1821
	}
	relation_id1109 := _t1820
	p.consumeLiteral("[")
	xs1110 := []*pb.Type{}
	cond1111 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1111 {
		_t1822 := p.parse_type()
		item1112 := _t1822
		xs1110 = append(xs1110, item1112)
		cond1111 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1113 := xs1110
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1823 := &pb.GNFColumn{ColumnPath: gnf_column_path1108, TargetId: relation_id1109, Types: types1113}
	result1115 := _t1823
	p.recordSpan(int(span_start1114), "GNFColumn")
	return result1115
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1824 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1824 = 1
	} else {
		var _t1825 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1825 = 0
		} else {
			_t1825 = -1
		}
		_t1824 = _t1825
	}
	prediction1116 := _t1824
	var _t1826 []string
	if prediction1116 == 1 {
		p.consumeLiteral("[")
		xs1118 := []string{}
		cond1119 := p.matchLookaheadTerminal("STRING", 0)
		for cond1119 {
			item1120 := p.consumeTerminal("STRING").Value.str
			xs1118 = append(xs1118, item1120)
			cond1119 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1121 := xs1118
		p.consumeLiteral("]")
		_t1826 = strings1121
	} else {
		var _t1827 []string
		if prediction1116 == 0 {
			string1117 := p.consumeTerminal("STRING").Value.str
			_ = string1117
			_t1827 = []string{string1117}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1826 = _t1827
	}
	return _t1826
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1122 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1122
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1828 := p.parse_fragment_id()
	fragment_id1123 := _t1828
	p.consumeLiteral(")")
	_t1829 := &pb.Undefine{FragmentId: fragment_id1123}
	result1125 := _t1829
	p.recordSpan(int(span_start1124), "Undefine")
	return result1125
}

func (p *Parser) parse_context() *pb.Context {
	span_start1130 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1126 := []*pb.RelationId{}
	cond1127 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1127 {
		_t1830 := p.parse_relation_id()
		item1128 := _t1830
		xs1126 = append(xs1126, item1128)
		cond1127 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1129 := xs1126
	p.consumeLiteral(")")
	_t1831 := &pb.Context{Relations: relation_ids1129}
	result1131 := _t1831
	p.recordSpan(int(span_start1130), "Context")
	return result1131
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1136 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1132 := []*pb.SnapshotMapping{}
	cond1133 := p.matchLookaheadLiteral("[", 0)
	for cond1133 {
		_t1832 := p.parse_snapshot_mapping()
		item1134 := _t1832
		xs1132 = append(xs1132, item1134)
		cond1133 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1135 := xs1132
	p.consumeLiteral(")")
	_t1833 := &pb.Snapshot{Mappings: snapshot_mappings1135}
	result1137 := _t1833
	p.recordSpan(int(span_start1136), "Snapshot")
	return result1137
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1140 := int64(p.spanStart())
	_t1834 := p.parse_edb_path()
	edb_path1138 := _t1834
	_t1835 := p.parse_relation_id()
	relation_id1139 := _t1835
	_t1836 := &pb.SnapshotMapping{DestinationPath: edb_path1138, SourceRelation: relation_id1139}
	result1141 := _t1836
	p.recordSpan(int(span_start1140), "SnapshotMapping")
	return result1141
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1142 := []*pb.Read{}
	cond1143 := p.matchLookaheadLiteral("(", 0)
	for cond1143 {
		_t1837 := p.parse_read()
		item1144 := _t1837
		xs1142 = append(xs1142, item1144)
		cond1143 = p.matchLookaheadLiteral("(", 0)
	}
	reads1145 := xs1142
	p.consumeLiteral(")")
	return reads1145
}

func (p *Parser) parse_read() *pb.Read {
	span_start1152 := int64(p.spanStart())
	var _t1838 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1839 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1839 = 2
		} else {
			var _t1840 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1840 = 1
			} else {
				var _t1841 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1841 = 4
				} else {
					var _t1842 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1842 = 0
					} else {
						var _t1843 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1843 = 3
						} else {
							_t1843 = -1
						}
						_t1842 = _t1843
					}
					_t1841 = _t1842
				}
				_t1840 = _t1841
			}
			_t1839 = _t1840
		}
		_t1838 = _t1839
	} else {
		_t1838 = -1
	}
	prediction1146 := _t1838
	var _t1844 *pb.Read
	if prediction1146 == 4 {
		_t1845 := p.parse_export()
		export1151 := _t1845
		_t1846 := &pb.Read{}
		_t1846.ReadType = &pb.Read_Export{Export: export1151}
		_t1844 = _t1846
	} else {
		var _t1847 *pb.Read
		if prediction1146 == 3 {
			_t1848 := p.parse_abort()
			abort1150 := _t1848
			_t1849 := &pb.Read{}
			_t1849.ReadType = &pb.Read_Abort{Abort: abort1150}
			_t1847 = _t1849
		} else {
			var _t1850 *pb.Read
			if prediction1146 == 2 {
				_t1851 := p.parse_what_if()
				what_if1149 := _t1851
				_t1852 := &pb.Read{}
				_t1852.ReadType = &pb.Read_WhatIf{WhatIf: what_if1149}
				_t1850 = _t1852
			} else {
				var _t1853 *pb.Read
				if prediction1146 == 1 {
					_t1854 := p.parse_output()
					output1148 := _t1854
					_t1855 := &pb.Read{}
					_t1855.ReadType = &pb.Read_Output{Output: output1148}
					_t1853 = _t1855
				} else {
					var _t1856 *pb.Read
					if prediction1146 == 0 {
						_t1857 := p.parse_demand()
						demand1147 := _t1857
						_t1858 := &pb.Read{}
						_t1858.ReadType = &pb.Read_Demand{Demand: demand1147}
						_t1856 = _t1858
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1853 = _t1856
				}
				_t1850 = _t1853
			}
			_t1847 = _t1850
		}
		_t1844 = _t1847
	}
	result1153 := _t1844
	p.recordSpan(int(span_start1152), "Read")
	return result1153
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1859 := p.parse_relation_id()
	relation_id1154 := _t1859
	p.consumeLiteral(")")
	_t1860 := &pb.Demand{RelationId: relation_id1154}
	result1156 := _t1860
	p.recordSpan(int(span_start1155), "Demand")
	return result1156
}

func (p *Parser) parse_output() *pb.Output {
	span_start1159 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1861 := p.parse_name()
	name1157 := _t1861
	_t1862 := p.parse_relation_id()
	relation_id1158 := _t1862
	p.consumeLiteral(")")
	_t1863 := &pb.Output{Name: name1157, RelationId: relation_id1158}
	result1160 := _t1863
	p.recordSpan(int(span_start1159), "Output")
	return result1160
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1163 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1864 := p.parse_name()
	name1161 := _t1864
	_t1865 := p.parse_epoch()
	epoch1162 := _t1865
	p.consumeLiteral(")")
	_t1866 := &pb.WhatIf{Branch: name1161, Epoch: epoch1162}
	result1164 := _t1866
	p.recordSpan(int(span_start1163), "WhatIf")
	return result1164
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1167 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1867 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1868 := p.parse_name()
		_t1867 = ptr(_t1868)
	}
	name1165 := _t1867
	_t1869 := p.parse_relation_id()
	relation_id1166 := _t1869
	p.consumeLiteral(")")
	_t1870 := &pb.Abort{Name: deref(name1165, "abort"), RelationId: relation_id1166}
	result1168 := _t1870
	p.recordSpan(int(span_start1167), "Abort")
	return result1168
}

func (p *Parser) parse_export() *pb.Export {
	span_start1170 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1871 := p.parse_export_csv_config()
	export_csv_config1169 := _t1871
	p.consumeLiteral(")")
	_t1872 := &pb.Export{}
	_t1872.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1169}
	result1171 := _t1872
	p.recordSpan(int(span_start1170), "Export")
	return result1171
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1179 := int64(p.spanStart())
	var _t1873 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1874 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1874 = 0
		} else {
			var _t1875 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1875 = 1
			} else {
				_t1875 = -1
			}
			_t1874 = _t1875
		}
		_t1873 = _t1874
	} else {
		_t1873 = -1
	}
	prediction1172 := _t1873
	var _t1876 *pb.ExportCSVConfig
	if prediction1172 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1877 := p.parse_export_csv_path()
		export_csv_path1176 := _t1877
		_t1878 := p.parse_export_csv_columns_list()
		export_csv_columns_list1177 := _t1878
		_t1879 := p.parse_config_dict()
		config_dict1178 := _t1879
		p.consumeLiteral(")")
		_t1880 := p.construct_export_csv_config(export_csv_path1176, export_csv_columns_list1177, config_dict1178)
		_t1876 = _t1880
	} else {
		var _t1881 *pb.ExportCSVConfig
		if prediction1172 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1882 := p.parse_export_csv_path()
			export_csv_path1173 := _t1882
			_t1883 := p.parse_export_csv_source()
			export_csv_source1174 := _t1883
			_t1884 := p.parse_csv_config()
			csv_config1175 := _t1884
			p.consumeLiteral(")")
			_t1885 := p.construct_export_csv_config_with_source(export_csv_path1173, export_csv_source1174, csv_config1175)
			_t1881 = _t1885
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1876 = _t1881
	}
	result1180 := _t1876
	p.recordSpan(int(span_start1179), "ExportCSVConfig")
	return result1180
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1181 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1181
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1188 := int64(p.spanStart())
	var _t1886 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1887 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1887 = 1
		} else {
			var _t1888 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1888 = 0
			} else {
				_t1888 = -1
			}
			_t1887 = _t1888
		}
		_t1886 = _t1887
	} else {
		_t1886 = -1
	}
	prediction1182 := _t1886
	var _t1889 *pb.ExportCSVSource
	if prediction1182 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1890 := p.parse_relation_id()
		relation_id1187 := _t1890
		p.consumeLiteral(")")
		_t1891 := &pb.ExportCSVSource{}
		_t1891.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1187}
		_t1889 = _t1891
	} else {
		var _t1892 *pb.ExportCSVSource
		if prediction1182 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1183 := []*pb.ExportCSVColumn{}
			cond1184 := p.matchLookaheadLiteral("(", 0)
			for cond1184 {
				_t1893 := p.parse_export_csv_column()
				item1185 := _t1893
				xs1183 = append(xs1183, item1185)
				cond1184 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1186 := xs1183
			p.consumeLiteral(")")
			_t1894 := &pb.ExportCSVColumns{Columns: export_csv_columns1186}
			_t1895 := &pb.ExportCSVSource{}
			_t1895.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1894}
			_t1892 = _t1895
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1889 = _t1892
	}
	result1189 := _t1889
	p.recordSpan(int(span_start1188), "ExportCSVSource")
	return result1189
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1192 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1190 := p.consumeTerminal("STRING").Value.str
	_t1896 := p.parse_relation_id()
	relation_id1191 := _t1896
	p.consumeLiteral(")")
	_t1897 := &pb.ExportCSVColumn{ColumnName: string1190, ColumnData: relation_id1191}
	result1193 := _t1897
	p.recordSpan(int(span_start1192), "ExportCSVColumn")
	return result1193
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1194 := []*pb.ExportCSVColumn{}
	cond1195 := p.matchLookaheadLiteral("(", 0)
	for cond1195 {
		_t1898 := p.parse_export_csv_column()
		item1196 := _t1898
		xs1194 = append(xs1194, item1196)
		cond1195 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1197 := xs1194
	p.consumeLiteral(")")
	return export_csv_columns1197
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
