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
	var _t1805 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1805
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1806 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1806
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1807 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1807
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1808 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1808
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1809 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1809
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1810 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1810
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1811 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1811
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1812 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1812
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1813 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1813
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1814 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1814
	_t1815 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1815
	_t1816 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1816
	_t1817 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1817
	_t1818 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1818
	_t1819 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1819
	_t1820 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1820
	_t1821 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1821
	_t1822 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1822
	_t1823 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1823
	_t1824 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1824
	_t1825 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1825
	_t1826 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1826
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1827 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1827
	_t1828 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1828
	_t1829 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1829
	_t1830 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1830
	_t1831 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1831
	_t1832 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1832
	_t1833 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1833
	_t1834 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1834
	_t1835 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1835
	_t1836 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1836.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1836.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1836
	_t1837 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1837
}

func (p *Parser) default_configure() *pb.Configure {
	_t1838 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1838
	_t1839 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1839
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
	_t1840 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1840
	_t1841 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1841
	_t1842 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1842
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1843 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1843
	_t1844 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1844
	_t1845 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1845
	_t1846 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1846
	_t1847 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1847
	_t1848 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1848
	_t1849 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1849
	_t1850 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1850
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1851 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1851
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start580 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1148 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1149 := p.parse_configure()
		_t1148 = _t1149
	}
	configure574 := _t1148
	var _t1150 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1151 := p.parse_sync()
		_t1150 = _t1151
	}
	sync575 := _t1150
	xs576 := []*pb.Epoch{}
	cond577 := p.matchLookaheadLiteral("(", 0)
	for cond577 {
		_t1152 := p.parse_epoch()
		item578 := _t1152
		xs576 = append(xs576, item578)
		cond577 = p.matchLookaheadLiteral("(", 0)
	}
	epochs579 := xs576
	p.consumeLiteral(")")
	_t1153 := p.default_configure()
	_t1154 := configure574
	if configure574 == nil {
		_t1154 = _t1153
	}
	_t1155 := &pb.Transaction{Epochs: epochs579, Configure: _t1154, Sync: sync575}
	result581 := _t1155
	p.recordSpan(int(span_start580), "Transaction")
	return result581
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start583 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1156 := p.parse_config_dict()
	config_dict582 := _t1156
	p.consumeLiteral(")")
	_t1157 := p.construct_configure(config_dict582)
	result584 := _t1157
	p.recordSpan(int(span_start583), "Configure")
	return result584
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs585 := [][]interface{}{}
	cond586 := p.matchLookaheadLiteral(":", 0)
	for cond586 {
		_t1158 := p.parse_config_key_value()
		item587 := _t1158
		xs585 = append(xs585, item587)
		cond586 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values588 := xs585
	p.consumeLiteral("}")
	return config_key_values588
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol589 := p.consumeTerminal("SYMBOL").Value.str
	_t1159 := p.parse_value()
	value590 := _t1159
	return []interface{}{symbol589, value590}
}

func (p *Parser) parse_value() *pb.Value {
	span_start603 := int64(p.spanStart())
	var _t1160 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1160 = 9
	} else {
		var _t1161 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1161 = 8
		} else {
			var _t1162 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1162 = 9
			} else {
				var _t1163 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1164 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1164 = 1
					} else {
						var _t1165 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1165 = 0
						} else {
							_t1165 = -1
						}
						_t1164 = _t1165
					}
					_t1163 = _t1164
				} else {
					var _t1166 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1166 = 5
					} else {
						var _t1167 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1167 = 2
						} else {
							var _t1168 int64
							if p.matchLookaheadTerminal("INT32", 0) {
								_t1168 = 10
							} else {
								var _t1169 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1169 = 6
								} else {
									var _t1170 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1170 = 3
									} else {
										var _t1171 int64
										if p.matchLookaheadTerminal("FLOAT32", 0) {
											_t1171 = 11
										} else {
											var _t1172 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1172 = 4
											} else {
												var _t1173 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1173 = 7
												} else {
													_t1173 = -1
												}
												_t1172 = _t1173
											}
											_t1171 = _t1172
										}
										_t1170 = _t1171
									}
									_t1169 = _t1170
								}
								_t1168 = _t1169
							}
							_t1167 = _t1168
						}
						_t1166 = _t1167
					}
					_t1163 = _t1166
				}
				_t1162 = _t1163
			}
			_t1161 = _t1162
		}
		_t1160 = _t1161
	}
	prediction591 := _t1160
	var _t1174 *pb.Value
	if prediction591 == 11 {
		float32602 := p.consumeTerminal("FLOAT32").Value.f32
		_t1175 := &pb.Value{}
		_t1175.Value = &pb.Value_Float32Value{Float32Value: float32602}
		_t1174 = _t1175
	} else {
		var _t1176 *pb.Value
		if prediction591 == 10 {
			int32601 := p.consumeTerminal("INT32").Value.i32
			_t1177 := &pb.Value{}
			_t1177.Value = &pb.Value_Int32Value{Int32Value: int32601}
			_t1176 = _t1177
		} else {
			var _t1178 *pb.Value
			if prediction591 == 9 {
				_t1179 := p.parse_boolean_value()
				boolean_value600 := _t1179
				_t1180 := &pb.Value{}
				_t1180.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value600}
				_t1178 = _t1180
			} else {
				var _t1181 *pb.Value
				if prediction591 == 8 {
					p.consumeLiteral("missing")
					_t1182 := &pb.MissingValue{}
					_t1183 := &pb.Value{}
					_t1183.Value = &pb.Value_MissingValue{MissingValue: _t1182}
					_t1181 = _t1183
				} else {
					var _t1184 *pb.Value
					if prediction591 == 7 {
						decimal599 := p.consumeTerminal("DECIMAL").Value.decimal
						_t1185 := &pb.Value{}
						_t1185.Value = &pb.Value_DecimalValue{DecimalValue: decimal599}
						_t1184 = _t1185
					} else {
						var _t1186 *pb.Value
						if prediction591 == 6 {
							int128598 := p.consumeTerminal("INT128").Value.int128
							_t1187 := &pb.Value{}
							_t1187.Value = &pb.Value_Int128Value{Int128Value: int128598}
							_t1186 = _t1187
						} else {
							var _t1188 *pb.Value
							if prediction591 == 5 {
								uint128597 := p.consumeTerminal("UINT128").Value.uint128
								_t1189 := &pb.Value{}
								_t1189.Value = &pb.Value_Uint128Value{Uint128Value: uint128597}
								_t1188 = _t1189
							} else {
								var _t1190 *pb.Value
								if prediction591 == 4 {
									float596 := p.consumeTerminal("FLOAT").Value.f64
									_t1191 := &pb.Value{}
									_t1191.Value = &pb.Value_FloatValue{FloatValue: float596}
									_t1190 = _t1191
								} else {
									var _t1192 *pb.Value
									if prediction591 == 3 {
										int595 := p.consumeTerminal("INT").Value.i64
										_t1193 := &pb.Value{}
										_t1193.Value = &pb.Value_IntValue{IntValue: int595}
										_t1192 = _t1193
									} else {
										var _t1194 *pb.Value
										if prediction591 == 2 {
											string594 := p.consumeTerminal("STRING").Value.str
											_t1195 := &pb.Value{}
											_t1195.Value = &pb.Value_StringValue{StringValue: string594}
											_t1194 = _t1195
										} else {
											var _t1196 *pb.Value
											if prediction591 == 1 {
												_t1197 := p.parse_datetime()
												datetime593 := _t1197
												_t1198 := &pb.Value{}
												_t1198.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime593}
												_t1196 = _t1198
											} else {
												var _t1199 *pb.Value
												if prediction591 == 0 {
													_t1200 := p.parse_date()
													date592 := _t1200
													_t1201 := &pb.Value{}
													_t1201.Value = &pb.Value_DateValue{DateValue: date592}
													_t1199 = _t1201
												} else {
													panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
												}
												_t1196 = _t1199
											}
											_t1194 = _t1196
										}
										_t1192 = _t1194
									}
									_t1190 = _t1192
								}
								_t1188 = _t1190
							}
							_t1186 = _t1188
						}
						_t1184 = _t1186
					}
					_t1181 = _t1184
				}
				_t1178 = _t1181
			}
			_t1176 = _t1178
		}
		_t1174 = _t1176
	}
	result604 := _t1174
	p.recordSpan(int(span_start603), "Value")
	return result604
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start608 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int605 := p.consumeTerminal("INT").Value.i64
	int_3606 := p.consumeTerminal("INT").Value.i64
	int_4607 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1202 := &pb.DateValue{Year: int32(int605), Month: int32(int_3606), Day: int32(int_4607)}
	result609 := _t1202
	p.recordSpan(int(span_start608), "DateValue")
	return result609
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start617 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int610 := p.consumeTerminal("INT").Value.i64
	int_3611 := p.consumeTerminal("INT").Value.i64
	int_4612 := p.consumeTerminal("INT").Value.i64
	int_5613 := p.consumeTerminal("INT").Value.i64
	int_6614 := p.consumeTerminal("INT").Value.i64
	int_7615 := p.consumeTerminal("INT").Value.i64
	var _t1203 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1203 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8616 := _t1203
	p.consumeLiteral(")")
	_t1204 := &pb.DateTimeValue{Year: int32(int610), Month: int32(int_3611), Day: int32(int_4612), Hour: int32(int_5613), Minute: int32(int_6614), Second: int32(int_7615), Microsecond: int32(deref(int_8616, 0))}
	result618 := _t1204
	p.recordSpan(int(span_start617), "DateTimeValue")
	return result618
}

func (p *Parser) parse_boolean_value() bool {
	var _t1205 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1205 = 0
	} else {
		var _t1206 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1206 = 1
		} else {
			_t1206 = -1
		}
		_t1205 = _t1206
	}
	prediction619 := _t1205
	var _t1207 bool
	if prediction619 == 1 {
		p.consumeLiteral("false")
		_t1207 = false
	} else {
		var _t1208 bool
		if prediction619 == 0 {
			p.consumeLiteral("true")
			_t1208 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1207 = _t1208
	}
	return _t1207
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start624 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs620 := []*pb.FragmentId{}
	cond621 := p.matchLookaheadLiteral(":", 0)
	for cond621 {
		_t1209 := p.parse_fragment_id()
		item622 := _t1209
		xs620 = append(xs620, item622)
		cond621 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids623 := xs620
	p.consumeLiteral(")")
	_t1210 := &pb.Sync{Fragments: fragment_ids623}
	result625 := _t1210
	p.recordSpan(int(span_start624), "Sync")
	return result625
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start627 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol626 := p.consumeTerminal("SYMBOL").Value.str
	result628 := &pb.FragmentId{Id: []byte(symbol626)}
	p.recordSpan(int(span_start627), "FragmentId")
	return result628
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start631 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1211 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1212 := p.parse_epoch_writes()
		_t1211 = _t1212
	}
	epoch_writes629 := _t1211
	var _t1213 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1214 := p.parse_epoch_reads()
		_t1213 = _t1214
	}
	epoch_reads630 := _t1213
	p.consumeLiteral(")")
	_t1215 := epoch_writes629
	if epoch_writes629 == nil {
		_t1215 = []*pb.Write{}
	}
	_t1216 := epoch_reads630
	if epoch_reads630 == nil {
		_t1216 = []*pb.Read{}
	}
	_t1217 := &pb.Epoch{Writes: _t1215, Reads: _t1216}
	result632 := _t1217
	p.recordSpan(int(span_start631), "Epoch")
	return result632
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs633 := []*pb.Write{}
	cond634 := p.matchLookaheadLiteral("(", 0)
	for cond634 {
		_t1218 := p.parse_write()
		item635 := _t1218
		xs633 = append(xs633, item635)
		cond634 = p.matchLookaheadLiteral("(", 0)
	}
	writes636 := xs633
	p.consumeLiteral(")")
	return writes636
}

func (p *Parser) parse_write() *pb.Write {
	span_start642 := int64(p.spanStart())
	var _t1219 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1220 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1220 = 1
		} else {
			var _t1221 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1221 = 3
			} else {
				var _t1222 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1222 = 0
				} else {
					var _t1223 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1223 = 2
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
	} else {
		_t1219 = -1
	}
	prediction637 := _t1219
	var _t1224 *pb.Write
	if prediction637 == 3 {
		_t1225 := p.parse_snapshot()
		snapshot641 := _t1225
		_t1226 := &pb.Write{}
		_t1226.WriteType = &pb.Write_Snapshot{Snapshot: snapshot641}
		_t1224 = _t1226
	} else {
		var _t1227 *pb.Write
		if prediction637 == 2 {
			_t1228 := p.parse_context()
			context640 := _t1228
			_t1229 := &pb.Write{}
			_t1229.WriteType = &pb.Write_Context{Context: context640}
			_t1227 = _t1229
		} else {
			var _t1230 *pb.Write
			if prediction637 == 1 {
				_t1231 := p.parse_undefine()
				undefine639 := _t1231
				_t1232 := &pb.Write{}
				_t1232.WriteType = &pb.Write_Undefine{Undefine: undefine639}
				_t1230 = _t1232
			} else {
				var _t1233 *pb.Write
				if prediction637 == 0 {
					_t1234 := p.parse_define()
					define638 := _t1234
					_t1235 := &pb.Write{}
					_t1235.WriteType = &pb.Write_Define{Define: define638}
					_t1233 = _t1235
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1230 = _t1233
			}
			_t1227 = _t1230
		}
		_t1224 = _t1227
	}
	result643 := _t1224
	p.recordSpan(int(span_start642), "Write")
	return result643
}

func (p *Parser) parse_define() *pb.Define {
	span_start645 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1236 := p.parse_fragment()
	fragment644 := _t1236
	p.consumeLiteral(")")
	_t1237 := &pb.Define{Fragment: fragment644}
	result646 := _t1237
	p.recordSpan(int(span_start645), "Define")
	return result646
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start652 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1238 := p.parse_new_fragment_id()
	new_fragment_id647 := _t1238
	xs648 := []*pb.Declaration{}
	cond649 := p.matchLookaheadLiteral("(", 0)
	for cond649 {
		_t1239 := p.parse_declaration()
		item650 := _t1239
		xs648 = append(xs648, item650)
		cond649 = p.matchLookaheadLiteral("(", 0)
	}
	declarations651 := xs648
	p.consumeLiteral(")")
	result653 := p.constructFragment(new_fragment_id647, declarations651)
	p.recordSpan(int(span_start652), "Fragment")
	return result653
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start655 := int64(p.spanStart())
	_t1240 := p.parse_fragment_id()
	fragment_id654 := _t1240
	p.startFragment(fragment_id654)
	result656 := fragment_id654
	p.recordSpan(int(span_start655), "FragmentId")
	return result656
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start662 := int64(p.spanStart())
	var _t1241 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1242 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1242 = 2
		} else {
			var _t1243 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1243 = 3
			} else {
				var _t1244 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1244 = 0
				} else {
					var _t1245 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1245 = 3
					} else {
						var _t1246 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1246 = 3
						} else {
							var _t1247 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1247 = 1
							} else {
								_t1247 = -1
							}
							_t1246 = _t1247
						}
						_t1245 = _t1246
					}
					_t1244 = _t1245
				}
				_t1243 = _t1244
			}
			_t1242 = _t1243
		}
		_t1241 = _t1242
	} else {
		_t1241 = -1
	}
	prediction657 := _t1241
	var _t1248 *pb.Declaration
	if prediction657 == 3 {
		_t1249 := p.parse_data()
		data661 := _t1249
		_t1250 := &pb.Declaration{}
		_t1250.DeclarationType = &pb.Declaration_Data{Data: data661}
		_t1248 = _t1250
	} else {
		var _t1251 *pb.Declaration
		if prediction657 == 2 {
			_t1252 := p.parse_constraint()
			constraint660 := _t1252
			_t1253 := &pb.Declaration{}
			_t1253.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint660}
			_t1251 = _t1253
		} else {
			var _t1254 *pb.Declaration
			if prediction657 == 1 {
				_t1255 := p.parse_algorithm()
				algorithm659 := _t1255
				_t1256 := &pb.Declaration{}
				_t1256.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm659}
				_t1254 = _t1256
			} else {
				var _t1257 *pb.Declaration
				if prediction657 == 0 {
					_t1258 := p.parse_def()
					def658 := _t1258
					_t1259 := &pb.Declaration{}
					_t1259.DeclarationType = &pb.Declaration_Def{Def: def658}
					_t1257 = _t1259
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1254 = _t1257
			}
			_t1251 = _t1254
		}
		_t1248 = _t1251
	}
	result663 := _t1248
	p.recordSpan(int(span_start662), "Declaration")
	return result663
}

func (p *Parser) parse_def() *pb.Def {
	span_start667 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1260 := p.parse_relation_id()
	relation_id664 := _t1260
	_t1261 := p.parse_abstraction()
	abstraction665 := _t1261
	var _t1262 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1263 := p.parse_attrs()
		_t1262 = _t1263
	}
	attrs666 := _t1262
	p.consumeLiteral(")")
	_t1264 := attrs666
	if attrs666 == nil {
		_t1264 = []*pb.Attribute{}
	}
	_t1265 := &pb.Def{Name: relation_id664, Body: abstraction665, Attrs: _t1264}
	result668 := _t1265
	p.recordSpan(int(span_start667), "Def")
	return result668
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start672 := int64(p.spanStart())
	var _t1266 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1266 = 0
	} else {
		var _t1267 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1267 = 1
		} else {
			_t1267 = -1
		}
		_t1266 = _t1267
	}
	prediction669 := _t1266
	var _t1268 *pb.RelationId
	if prediction669 == 1 {
		uint128671 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128671
		_t1268 = &pb.RelationId{IdLow: uint128671.Low, IdHigh: uint128671.High}
	} else {
		var _t1269 *pb.RelationId
		if prediction669 == 0 {
			p.consumeLiteral(":")
			symbol670 := p.consumeTerminal("SYMBOL").Value.str
			_t1269 = p.relationIdFromString(symbol670)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1268 = _t1269
	}
	result673 := _t1268
	p.recordSpan(int(span_start672), "RelationId")
	return result673
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start676 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1270 := p.parse_bindings()
	bindings674 := _t1270
	_t1271 := p.parse_formula()
	formula675 := _t1271
	p.consumeLiteral(")")
	_t1272 := &pb.Abstraction{Vars: listConcat(bindings674[0].([]*pb.Binding), bindings674[1].([]*pb.Binding)), Value: formula675}
	result677 := _t1272
	p.recordSpan(int(span_start676), "Abstraction")
	return result677
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs678 := []*pb.Binding{}
	cond679 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond679 {
		_t1273 := p.parse_binding()
		item680 := _t1273
		xs678 = append(xs678, item680)
		cond679 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings681 := xs678
	var _t1274 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1275 := p.parse_value_bindings()
		_t1274 = _t1275
	}
	value_bindings682 := _t1274
	p.consumeLiteral("]")
	_t1276 := value_bindings682
	if value_bindings682 == nil {
		_t1276 = []*pb.Binding{}
	}
	return []interface{}{bindings681, _t1276}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start685 := int64(p.spanStart())
	symbol683 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1277 := p.parse_type()
	type684 := _t1277
	_t1278 := &pb.Var{Name: symbol683}
	_t1279 := &pb.Binding{Var: _t1278, Type: type684}
	result686 := _t1279
	p.recordSpan(int(span_start685), "Binding")
	return result686
}

func (p *Parser) parse_type() *pb.Type {
	span_start701 := int64(p.spanStart())
	var _t1280 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1280 = 0
	} else {
		var _t1281 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1281 = 4
		} else {
			var _t1282 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1282 = 1
			} else {
				var _t1283 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1283 = 8
				} else {
					var _t1284 int64
					if p.matchLookaheadLiteral("INT32", 0) {
						_t1284 = 11
					} else {
						var _t1285 int64
						if p.matchLookaheadLiteral("INT128", 0) {
							_t1285 = 5
						} else {
							var _t1286 int64
							if p.matchLookaheadLiteral("INT", 0) {
								_t1286 = 2
							} else {
								var _t1287 int64
								if p.matchLookaheadLiteral("FLOAT32", 0) {
									_t1287 = 12
								} else {
									var _t1288 int64
									if p.matchLookaheadLiteral("FLOAT", 0) {
										_t1288 = 3
									} else {
										var _t1289 int64
										if p.matchLookaheadLiteral("DATETIME", 0) {
											_t1289 = 7
										} else {
											var _t1290 int64
											if p.matchLookaheadLiteral("DATE", 0) {
												_t1290 = 6
											} else {
												var _t1291 int64
												if p.matchLookaheadLiteral("BOOLEAN", 0) {
													_t1291 = 10
												} else {
													var _t1292 int64
													if p.matchLookaheadLiteral("(", 0) {
														_t1292 = 9
													} else {
														_t1292 = -1
													}
													_t1291 = _t1292
												}
												_t1290 = _t1291
											}
											_t1289 = _t1290
										}
										_t1288 = _t1289
									}
									_t1287 = _t1288
								}
								_t1286 = _t1287
							}
							_t1285 = _t1286
						}
						_t1284 = _t1285
					}
					_t1283 = _t1284
				}
				_t1282 = _t1283
			}
			_t1281 = _t1282
		}
		_t1280 = _t1281
	}
	prediction687 := _t1280
	var _t1293 *pb.Type
	if prediction687 == 12 {
		_t1294 := p.parse_float32_type()
		float32_type700 := _t1294
		_t1295 := &pb.Type{}
		_t1295.Type = &pb.Type_Float32Type{Float32Type: float32_type700}
		_t1293 = _t1295
	} else {
		var _t1296 *pb.Type
		if prediction687 == 11 {
			_t1297 := p.parse_int32_type()
			int32_type699 := _t1297
			_t1298 := &pb.Type{}
			_t1298.Type = &pb.Type_Int32Type{Int32Type: int32_type699}
			_t1296 = _t1298
		} else {
			var _t1299 *pb.Type
			if prediction687 == 10 {
				_t1300 := p.parse_boolean_type()
				boolean_type698 := _t1300
				_t1301 := &pb.Type{}
				_t1301.Type = &pb.Type_BooleanType{BooleanType: boolean_type698}
				_t1299 = _t1301
			} else {
				var _t1302 *pb.Type
				if prediction687 == 9 {
					_t1303 := p.parse_decimal_type()
					decimal_type697 := _t1303
					_t1304 := &pb.Type{}
					_t1304.Type = &pb.Type_DecimalType{DecimalType: decimal_type697}
					_t1302 = _t1304
				} else {
					var _t1305 *pb.Type
					if prediction687 == 8 {
						_t1306 := p.parse_missing_type()
						missing_type696 := _t1306
						_t1307 := &pb.Type{}
						_t1307.Type = &pb.Type_MissingType{MissingType: missing_type696}
						_t1305 = _t1307
					} else {
						var _t1308 *pb.Type
						if prediction687 == 7 {
							_t1309 := p.parse_datetime_type()
							datetime_type695 := _t1309
							_t1310 := &pb.Type{}
							_t1310.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type695}
							_t1308 = _t1310
						} else {
							var _t1311 *pb.Type
							if prediction687 == 6 {
								_t1312 := p.parse_date_type()
								date_type694 := _t1312
								_t1313 := &pb.Type{}
								_t1313.Type = &pb.Type_DateType{DateType: date_type694}
								_t1311 = _t1313
							} else {
								var _t1314 *pb.Type
								if prediction687 == 5 {
									_t1315 := p.parse_int128_type()
									int128_type693 := _t1315
									_t1316 := &pb.Type{}
									_t1316.Type = &pb.Type_Int128Type{Int128Type: int128_type693}
									_t1314 = _t1316
								} else {
									var _t1317 *pb.Type
									if prediction687 == 4 {
										_t1318 := p.parse_uint128_type()
										uint128_type692 := _t1318
										_t1319 := &pb.Type{}
										_t1319.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type692}
										_t1317 = _t1319
									} else {
										var _t1320 *pb.Type
										if prediction687 == 3 {
											_t1321 := p.parse_float_type()
											float_type691 := _t1321
											_t1322 := &pb.Type{}
											_t1322.Type = &pb.Type_FloatType{FloatType: float_type691}
											_t1320 = _t1322
										} else {
											var _t1323 *pb.Type
											if prediction687 == 2 {
												_t1324 := p.parse_int_type()
												int_type690 := _t1324
												_t1325 := &pb.Type{}
												_t1325.Type = &pb.Type_IntType{IntType: int_type690}
												_t1323 = _t1325
											} else {
												var _t1326 *pb.Type
												if prediction687 == 1 {
													_t1327 := p.parse_string_type()
													string_type689 := _t1327
													_t1328 := &pb.Type{}
													_t1328.Type = &pb.Type_StringType{StringType: string_type689}
													_t1326 = _t1328
												} else {
													var _t1329 *pb.Type
													if prediction687 == 0 {
														_t1330 := p.parse_unspecified_type()
														unspecified_type688 := _t1330
														_t1331 := &pb.Type{}
														_t1331.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type688}
														_t1329 = _t1331
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1326 = _t1329
												}
												_t1323 = _t1326
											}
											_t1320 = _t1323
										}
										_t1317 = _t1320
									}
									_t1314 = _t1317
								}
								_t1311 = _t1314
							}
							_t1308 = _t1311
						}
						_t1305 = _t1308
					}
					_t1302 = _t1305
				}
				_t1299 = _t1302
			}
			_t1296 = _t1299
		}
		_t1293 = _t1296
	}
	result702 := _t1293
	p.recordSpan(int(span_start701), "Type")
	return result702
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start703 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1332 := &pb.UnspecifiedType{}
	result704 := _t1332
	p.recordSpan(int(span_start703), "UnspecifiedType")
	return result704
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start705 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1333 := &pb.StringType{}
	result706 := _t1333
	p.recordSpan(int(span_start705), "StringType")
	return result706
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1334 := &pb.IntType{}
	result708 := _t1334
	p.recordSpan(int(span_start707), "IntType")
	return result708
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1335 := &pb.FloatType{}
	result710 := _t1335
	p.recordSpan(int(span_start709), "FloatType")
	return result710
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1336 := &pb.UInt128Type{}
	result712 := _t1336
	p.recordSpan(int(span_start711), "UInt128Type")
	return result712
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1337 := &pb.Int128Type{}
	result714 := _t1337
	p.recordSpan(int(span_start713), "Int128Type")
	return result714
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1338 := &pb.DateType{}
	result716 := _t1338
	p.recordSpan(int(span_start715), "DateType")
	return result716
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1339 := &pb.DateTimeType{}
	result718 := _t1339
	p.recordSpan(int(span_start717), "DateTimeType")
	return result718
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start719 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1340 := &pb.MissingType{}
	result720 := _t1340
	p.recordSpan(int(span_start719), "MissingType")
	return result720
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int721 := p.consumeTerminal("INT").Value.i64
	int_3722 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1341 := &pb.DecimalType{Precision: int32(int721), Scale: int32(int_3722)}
	result724 := _t1341
	p.recordSpan(int(span_start723), "DecimalType")
	return result724
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1342 := &pb.BooleanType{}
	result726 := _t1342
	p.recordSpan(int(span_start725), "BooleanType")
	return result726
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start727 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1343 := &pb.Int32Type{}
	result728 := _t1343
	p.recordSpan(int(span_start727), "Int32Type")
	return result728
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start729 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1344 := &pb.Float32Type{}
	result730 := _t1344
	p.recordSpan(int(span_start729), "Float32Type")
	return result730
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs731 := []*pb.Binding{}
	cond732 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond732 {
		_t1345 := p.parse_binding()
		item733 := _t1345
		xs731 = append(xs731, item733)
		cond732 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings734 := xs731
	return bindings734
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start749 := int64(p.spanStart())
	var _t1346 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1347 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1347 = 0
		} else {
			var _t1348 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1348 = 11
			} else {
				var _t1349 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1349 = 3
				} else {
					var _t1350 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1350 = 10
					} else {
						var _t1351 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1351 = 9
						} else {
							var _t1352 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1352 = 5
							} else {
								var _t1353 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1353 = 6
								} else {
									var _t1354 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1354 = 7
									} else {
										var _t1355 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1355 = 1
										} else {
											var _t1356 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1356 = 2
											} else {
												var _t1357 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1357 = 12
												} else {
													var _t1358 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1358 = 8
													} else {
														var _t1359 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1359 = 4
														} else {
															var _t1360 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1360 = 10
															} else {
																var _t1361 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1361 = 10
																} else {
																	var _t1362 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1362 = 10
																	} else {
																		var _t1363 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1363 = 10
																		} else {
																			var _t1364 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1364 = 10
																			} else {
																				var _t1365 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1365 = 10
																				} else {
																					var _t1366 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1366 = 10
																					} else {
																						var _t1367 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1367 = 10
																						} else {
																							var _t1368 int64
																							if p.matchLookaheadLiteral("*", 1) {
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
															_t1359 = _t1360
														}
														_t1358 = _t1359
													}
													_t1357 = _t1358
												}
												_t1356 = _t1357
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
			_t1347 = _t1348
		}
		_t1346 = _t1347
	} else {
		_t1346 = -1
	}
	prediction735 := _t1346
	var _t1369 *pb.Formula
	if prediction735 == 12 {
		_t1370 := p.parse_cast()
		cast748 := _t1370
		_t1371 := &pb.Formula{}
		_t1371.FormulaType = &pb.Formula_Cast{Cast: cast748}
		_t1369 = _t1371
	} else {
		var _t1372 *pb.Formula
		if prediction735 == 11 {
			_t1373 := p.parse_rel_atom()
			rel_atom747 := _t1373
			_t1374 := &pb.Formula{}
			_t1374.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom747}
			_t1372 = _t1374
		} else {
			var _t1375 *pb.Formula
			if prediction735 == 10 {
				_t1376 := p.parse_primitive()
				primitive746 := _t1376
				_t1377 := &pb.Formula{}
				_t1377.FormulaType = &pb.Formula_Primitive{Primitive: primitive746}
				_t1375 = _t1377
			} else {
				var _t1378 *pb.Formula
				if prediction735 == 9 {
					_t1379 := p.parse_pragma()
					pragma745 := _t1379
					_t1380 := &pb.Formula{}
					_t1380.FormulaType = &pb.Formula_Pragma{Pragma: pragma745}
					_t1378 = _t1380
				} else {
					var _t1381 *pb.Formula
					if prediction735 == 8 {
						_t1382 := p.parse_atom()
						atom744 := _t1382
						_t1383 := &pb.Formula{}
						_t1383.FormulaType = &pb.Formula_Atom{Atom: atom744}
						_t1381 = _t1383
					} else {
						var _t1384 *pb.Formula
						if prediction735 == 7 {
							_t1385 := p.parse_ffi()
							ffi743 := _t1385
							_t1386 := &pb.Formula{}
							_t1386.FormulaType = &pb.Formula_Ffi{Ffi: ffi743}
							_t1384 = _t1386
						} else {
							var _t1387 *pb.Formula
							if prediction735 == 6 {
								_t1388 := p.parse_not()
								not742 := _t1388
								_t1389 := &pb.Formula{}
								_t1389.FormulaType = &pb.Formula_Not{Not: not742}
								_t1387 = _t1389
							} else {
								var _t1390 *pb.Formula
								if prediction735 == 5 {
									_t1391 := p.parse_disjunction()
									disjunction741 := _t1391
									_t1392 := &pb.Formula{}
									_t1392.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction741}
									_t1390 = _t1392
								} else {
									var _t1393 *pb.Formula
									if prediction735 == 4 {
										_t1394 := p.parse_conjunction()
										conjunction740 := _t1394
										_t1395 := &pb.Formula{}
										_t1395.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction740}
										_t1393 = _t1395
									} else {
										var _t1396 *pb.Formula
										if prediction735 == 3 {
											_t1397 := p.parse_reduce()
											reduce739 := _t1397
											_t1398 := &pb.Formula{}
											_t1398.FormulaType = &pb.Formula_Reduce{Reduce: reduce739}
											_t1396 = _t1398
										} else {
											var _t1399 *pb.Formula
											if prediction735 == 2 {
												_t1400 := p.parse_exists()
												exists738 := _t1400
												_t1401 := &pb.Formula{}
												_t1401.FormulaType = &pb.Formula_Exists{Exists: exists738}
												_t1399 = _t1401
											} else {
												var _t1402 *pb.Formula
												if prediction735 == 1 {
													_t1403 := p.parse_false()
													false737 := _t1403
													_t1404 := &pb.Formula{}
													_t1404.FormulaType = &pb.Formula_Disjunction{Disjunction: false737}
													_t1402 = _t1404
												} else {
													var _t1405 *pb.Formula
													if prediction735 == 0 {
														_t1406 := p.parse_true()
														true736 := _t1406
														_t1407 := &pb.Formula{}
														_t1407.FormulaType = &pb.Formula_Conjunction{Conjunction: true736}
														_t1405 = _t1407
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1402 = _t1405
												}
												_t1399 = _t1402
											}
											_t1396 = _t1399
										}
										_t1393 = _t1396
									}
									_t1390 = _t1393
								}
								_t1387 = _t1390
							}
							_t1384 = _t1387
						}
						_t1381 = _t1384
					}
					_t1378 = _t1381
				}
				_t1375 = _t1378
			}
			_t1372 = _t1375
		}
		_t1369 = _t1372
	}
	result750 := _t1369
	p.recordSpan(int(span_start749), "Formula")
	return result750
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1408 := &pb.Conjunction{Args: []*pb.Formula{}}
	result752 := _t1408
	p.recordSpan(int(span_start751), "Conjunction")
	return result752
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1409 := &pb.Disjunction{Args: []*pb.Formula{}}
	result754 := _t1409
	p.recordSpan(int(span_start753), "Disjunction")
	return result754
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1410 := p.parse_bindings()
	bindings755 := _t1410
	_t1411 := p.parse_formula()
	formula756 := _t1411
	p.consumeLiteral(")")
	_t1412 := &pb.Abstraction{Vars: listConcat(bindings755[0].([]*pb.Binding), bindings755[1].([]*pb.Binding)), Value: formula756}
	_t1413 := &pb.Exists{Body: _t1412}
	result758 := _t1413
	p.recordSpan(int(span_start757), "Exists")
	return result758
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start762 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1414 := p.parse_abstraction()
	abstraction759 := _t1414
	_t1415 := p.parse_abstraction()
	abstraction_3760 := _t1415
	_t1416 := p.parse_terms()
	terms761 := _t1416
	p.consumeLiteral(")")
	_t1417 := &pb.Reduce{Op: abstraction759, Body: abstraction_3760, Terms: terms761}
	result763 := _t1417
	p.recordSpan(int(span_start762), "Reduce")
	return result763
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs764 := []*pb.Term{}
	cond765 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond765 {
		_t1418 := p.parse_term()
		item766 := _t1418
		xs764 = append(xs764, item766)
		cond765 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms767 := xs764
	p.consumeLiteral(")")
	return terms767
}

func (p *Parser) parse_term() *pb.Term {
	span_start771 := int64(p.spanStart())
	var _t1419 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1419 = 1
	} else {
		var _t1420 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1420 = 1
		} else {
			var _t1421 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1421 = 1
			} else {
				var _t1422 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1422 = 1
				} else {
					var _t1423 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1423 = 1
					} else {
						var _t1424 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1424 = 0
						} else {
							var _t1425 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1425 = 1
							} else {
								var _t1426 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1426 = 1
								} else {
									var _t1427 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1427 = 1
									} else {
										var _t1428 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1428 = 1
										} else {
											var _t1429 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1429 = 1
											} else {
												var _t1430 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1430 = 1
												} else {
													var _t1431 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1431 = 1
													} else {
														_t1431 = -1
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
								}
								_t1425 = _t1426
							}
							_t1424 = _t1425
						}
						_t1423 = _t1424
					}
					_t1422 = _t1423
				}
				_t1421 = _t1422
			}
			_t1420 = _t1421
		}
		_t1419 = _t1420
	}
	prediction768 := _t1419
	var _t1432 *pb.Term
	if prediction768 == 1 {
		_t1433 := p.parse_constant()
		constant770 := _t1433
		_t1434 := &pb.Term{}
		_t1434.TermType = &pb.Term_Constant{Constant: constant770}
		_t1432 = _t1434
	} else {
		var _t1435 *pb.Term
		if prediction768 == 0 {
			_t1436 := p.parse_var()
			var769 := _t1436
			_t1437 := &pb.Term{}
			_t1437.TermType = &pb.Term_Var{Var: var769}
			_t1435 = _t1437
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1432 = _t1435
	}
	result772 := _t1432
	p.recordSpan(int(span_start771), "Term")
	return result772
}

func (p *Parser) parse_var() *pb.Var {
	span_start774 := int64(p.spanStart())
	symbol773 := p.consumeTerminal("SYMBOL").Value.str
	_t1438 := &pb.Var{Name: symbol773}
	result775 := _t1438
	p.recordSpan(int(span_start774), "Var")
	return result775
}

func (p *Parser) parse_constant() *pb.Value {
	span_start777 := int64(p.spanStart())
	_t1439 := p.parse_value()
	value776 := _t1439
	result778 := value776
	p.recordSpan(int(span_start777), "Value")
	return result778
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start783 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs779 := []*pb.Formula{}
	cond780 := p.matchLookaheadLiteral("(", 0)
	for cond780 {
		_t1440 := p.parse_formula()
		item781 := _t1440
		xs779 = append(xs779, item781)
		cond780 = p.matchLookaheadLiteral("(", 0)
	}
	formulas782 := xs779
	p.consumeLiteral(")")
	_t1441 := &pb.Conjunction{Args: formulas782}
	result784 := _t1441
	p.recordSpan(int(span_start783), "Conjunction")
	return result784
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start789 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs785 := []*pb.Formula{}
	cond786 := p.matchLookaheadLiteral("(", 0)
	for cond786 {
		_t1442 := p.parse_formula()
		item787 := _t1442
		xs785 = append(xs785, item787)
		cond786 = p.matchLookaheadLiteral("(", 0)
	}
	formulas788 := xs785
	p.consumeLiteral(")")
	_t1443 := &pb.Disjunction{Args: formulas788}
	result790 := _t1443
	p.recordSpan(int(span_start789), "Disjunction")
	return result790
}

func (p *Parser) parse_not() *pb.Not {
	span_start792 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1444 := p.parse_formula()
	formula791 := _t1444
	p.consumeLiteral(")")
	_t1445 := &pb.Not{Arg: formula791}
	result793 := _t1445
	p.recordSpan(int(span_start792), "Not")
	return result793
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1446 := p.parse_name()
	name794 := _t1446
	_t1447 := p.parse_ffi_args()
	ffi_args795 := _t1447
	_t1448 := p.parse_terms()
	terms796 := _t1448
	p.consumeLiteral(")")
	_t1449 := &pb.FFI{Name: name794, Args: ffi_args795, Terms: terms796}
	result798 := _t1449
	p.recordSpan(int(span_start797), "FFI")
	return result798
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol799 := p.consumeTerminal("SYMBOL").Value.str
	return symbol799
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs800 := []*pb.Abstraction{}
	cond801 := p.matchLookaheadLiteral("(", 0)
	for cond801 {
		_t1450 := p.parse_abstraction()
		item802 := _t1450
		xs800 = append(xs800, item802)
		cond801 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions803 := xs800
	p.consumeLiteral(")")
	return abstractions803
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1451 := p.parse_relation_id()
	relation_id804 := _t1451
	xs805 := []*pb.Term{}
	cond806 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond806 {
		_t1452 := p.parse_term()
		item807 := _t1452
		xs805 = append(xs805, item807)
		cond806 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms808 := xs805
	p.consumeLiteral(")")
	_t1453 := &pb.Atom{Name: relation_id804, Terms: terms808}
	result810 := _t1453
	p.recordSpan(int(span_start809), "Atom")
	return result810
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1454 := p.parse_name()
	name811 := _t1454
	xs812 := []*pb.Term{}
	cond813 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond813 {
		_t1455 := p.parse_term()
		item814 := _t1455
		xs812 = append(xs812, item814)
		cond813 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms815 := xs812
	p.consumeLiteral(")")
	_t1456 := &pb.Pragma{Name: name811, Terms: terms815}
	result817 := _t1456
	p.recordSpan(int(span_start816), "Pragma")
	return result817
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start833 := int64(p.spanStart())
	var _t1457 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1458 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1458 = 9
		} else {
			var _t1459 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1459 = 4
			} else {
				var _t1460 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1460 = 3
				} else {
					var _t1461 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1461 = 0
					} else {
						var _t1462 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1462 = 2
						} else {
							var _t1463 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1463 = 1
							} else {
								var _t1464 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1464 = 8
								} else {
									var _t1465 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1465 = 6
									} else {
										var _t1466 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1466 = 5
										} else {
											var _t1467 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1467 = 7
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
	} else {
		_t1457 = -1
	}
	prediction818 := _t1457
	var _t1468 *pb.Primitive
	if prediction818 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1469 := p.parse_name()
		name828 := _t1469
		xs829 := []*pb.RelTerm{}
		cond830 := (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond830 {
			_t1470 := p.parse_rel_term()
			item831 := _t1470
			xs829 = append(xs829, item831)
			cond830 = (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms832 := xs829
		p.consumeLiteral(")")
		_t1471 := &pb.Primitive{Name: name828, Terms: rel_terms832}
		_t1468 = _t1471
	} else {
		var _t1472 *pb.Primitive
		if prediction818 == 8 {
			_t1473 := p.parse_divide()
			divide827 := _t1473
			_t1472 = divide827
		} else {
			var _t1474 *pb.Primitive
			if prediction818 == 7 {
				_t1475 := p.parse_multiply()
				multiply826 := _t1475
				_t1474 = multiply826
			} else {
				var _t1476 *pb.Primitive
				if prediction818 == 6 {
					_t1477 := p.parse_minus()
					minus825 := _t1477
					_t1476 = minus825
				} else {
					var _t1478 *pb.Primitive
					if prediction818 == 5 {
						_t1479 := p.parse_add()
						add824 := _t1479
						_t1478 = add824
					} else {
						var _t1480 *pb.Primitive
						if prediction818 == 4 {
							_t1481 := p.parse_gt_eq()
							gt_eq823 := _t1481
							_t1480 = gt_eq823
						} else {
							var _t1482 *pb.Primitive
							if prediction818 == 3 {
								_t1483 := p.parse_gt()
								gt822 := _t1483
								_t1482 = gt822
							} else {
								var _t1484 *pb.Primitive
								if prediction818 == 2 {
									_t1485 := p.parse_lt_eq()
									lt_eq821 := _t1485
									_t1484 = lt_eq821
								} else {
									var _t1486 *pb.Primitive
									if prediction818 == 1 {
										_t1487 := p.parse_lt()
										lt820 := _t1487
										_t1486 = lt820
									} else {
										var _t1488 *pb.Primitive
										if prediction818 == 0 {
											_t1489 := p.parse_eq()
											eq819 := _t1489
											_t1488 = eq819
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1486 = _t1488
									}
									_t1484 = _t1486
								}
								_t1482 = _t1484
							}
							_t1480 = _t1482
						}
						_t1478 = _t1480
					}
					_t1476 = _t1478
				}
				_t1474 = _t1476
			}
			_t1472 = _t1474
		}
		_t1468 = _t1472
	}
	result834 := _t1468
	p.recordSpan(int(span_start833), "Primitive")
	return result834
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1490 := p.parse_term()
	term835 := _t1490
	_t1491 := p.parse_term()
	term_3836 := _t1491
	p.consumeLiteral(")")
	_t1492 := &pb.RelTerm{}
	_t1492.RelTermType = &pb.RelTerm_Term{Term: term835}
	_t1493 := &pb.RelTerm{}
	_t1493.RelTermType = &pb.RelTerm_Term{Term: term_3836}
	_t1494 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1492, _t1493}}
	result838 := _t1494
	p.recordSpan(int(span_start837), "Primitive")
	return result838
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1495 := p.parse_term()
	term839 := _t1495
	_t1496 := p.parse_term()
	term_3840 := _t1496
	p.consumeLiteral(")")
	_t1497 := &pb.RelTerm{}
	_t1497.RelTermType = &pb.RelTerm_Term{Term: term839}
	_t1498 := &pb.RelTerm{}
	_t1498.RelTermType = &pb.RelTerm_Term{Term: term_3840}
	_t1499 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1497, _t1498}}
	result842 := _t1499
	p.recordSpan(int(span_start841), "Primitive")
	return result842
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1500 := p.parse_term()
	term843 := _t1500
	_t1501 := p.parse_term()
	term_3844 := _t1501
	p.consumeLiteral(")")
	_t1502 := &pb.RelTerm{}
	_t1502.RelTermType = &pb.RelTerm_Term{Term: term843}
	_t1503 := &pb.RelTerm{}
	_t1503.RelTermType = &pb.RelTerm_Term{Term: term_3844}
	_t1504 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1502, _t1503}}
	result846 := _t1504
	p.recordSpan(int(span_start845), "Primitive")
	return result846
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1505 := p.parse_term()
	term847 := _t1505
	_t1506 := p.parse_term()
	term_3848 := _t1506
	p.consumeLiteral(")")
	_t1507 := &pb.RelTerm{}
	_t1507.RelTermType = &pb.RelTerm_Term{Term: term847}
	_t1508 := &pb.RelTerm{}
	_t1508.RelTermType = &pb.RelTerm_Term{Term: term_3848}
	_t1509 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1507, _t1508}}
	result850 := _t1509
	p.recordSpan(int(span_start849), "Primitive")
	return result850
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1510 := p.parse_term()
	term851 := _t1510
	_t1511 := p.parse_term()
	term_3852 := _t1511
	p.consumeLiteral(")")
	_t1512 := &pb.RelTerm{}
	_t1512.RelTermType = &pb.RelTerm_Term{Term: term851}
	_t1513 := &pb.RelTerm{}
	_t1513.RelTermType = &pb.RelTerm_Term{Term: term_3852}
	_t1514 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1512, _t1513}}
	result854 := _t1514
	p.recordSpan(int(span_start853), "Primitive")
	return result854
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start858 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1515 := p.parse_term()
	term855 := _t1515
	_t1516 := p.parse_term()
	term_3856 := _t1516
	_t1517 := p.parse_term()
	term_4857 := _t1517
	p.consumeLiteral(")")
	_t1518 := &pb.RelTerm{}
	_t1518.RelTermType = &pb.RelTerm_Term{Term: term855}
	_t1519 := &pb.RelTerm{}
	_t1519.RelTermType = &pb.RelTerm_Term{Term: term_3856}
	_t1520 := &pb.RelTerm{}
	_t1520.RelTermType = &pb.RelTerm_Term{Term: term_4857}
	_t1521 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1518, _t1519, _t1520}}
	result859 := _t1521
	p.recordSpan(int(span_start858), "Primitive")
	return result859
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1522 := p.parse_term()
	term860 := _t1522
	_t1523 := p.parse_term()
	term_3861 := _t1523
	_t1524 := p.parse_term()
	term_4862 := _t1524
	p.consumeLiteral(")")
	_t1525 := &pb.RelTerm{}
	_t1525.RelTermType = &pb.RelTerm_Term{Term: term860}
	_t1526 := &pb.RelTerm{}
	_t1526.RelTermType = &pb.RelTerm_Term{Term: term_3861}
	_t1527 := &pb.RelTerm{}
	_t1527.RelTermType = &pb.RelTerm_Term{Term: term_4862}
	_t1528 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1525, _t1526, _t1527}}
	result864 := _t1528
	p.recordSpan(int(span_start863), "Primitive")
	return result864
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start868 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1529 := p.parse_term()
	term865 := _t1529
	_t1530 := p.parse_term()
	term_3866 := _t1530
	_t1531 := p.parse_term()
	term_4867 := _t1531
	p.consumeLiteral(")")
	_t1532 := &pb.RelTerm{}
	_t1532.RelTermType = &pb.RelTerm_Term{Term: term865}
	_t1533 := &pb.RelTerm{}
	_t1533.RelTermType = &pb.RelTerm_Term{Term: term_3866}
	_t1534 := &pb.RelTerm{}
	_t1534.RelTermType = &pb.RelTerm_Term{Term: term_4867}
	_t1535 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1532, _t1533, _t1534}}
	result869 := _t1535
	p.recordSpan(int(span_start868), "Primitive")
	return result869
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start873 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1536 := p.parse_term()
	term870 := _t1536
	_t1537 := p.parse_term()
	term_3871 := _t1537
	_t1538 := p.parse_term()
	term_4872 := _t1538
	p.consumeLiteral(")")
	_t1539 := &pb.RelTerm{}
	_t1539.RelTermType = &pb.RelTerm_Term{Term: term870}
	_t1540 := &pb.RelTerm{}
	_t1540.RelTermType = &pb.RelTerm_Term{Term: term_3871}
	_t1541 := &pb.RelTerm{}
	_t1541.RelTermType = &pb.RelTerm_Term{Term: term_4872}
	_t1542 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1539, _t1540, _t1541}}
	result874 := _t1542
	p.recordSpan(int(span_start873), "Primitive")
	return result874
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start878 := int64(p.spanStart())
	var _t1543 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1543 = 1
	} else {
		var _t1544 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1544 = 1
		} else {
			var _t1545 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1545 = 1
			} else {
				var _t1546 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1546 = 1
				} else {
					var _t1547 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1547 = 0
					} else {
						var _t1548 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1548 = 1
						} else {
							var _t1549 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1549 = 1
							} else {
								var _t1550 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1550 = 1
								} else {
									var _t1551 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1551 = 1
									} else {
										var _t1552 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1552 = 1
										} else {
											var _t1553 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1553 = 1
											} else {
												var _t1554 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1554 = 1
												} else {
													var _t1555 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1555 = 1
													} else {
														var _t1556 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1556 = 1
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
	prediction875 := _t1543
	var _t1557 *pb.RelTerm
	if prediction875 == 1 {
		_t1558 := p.parse_term()
		term877 := _t1558
		_t1559 := &pb.RelTerm{}
		_t1559.RelTermType = &pb.RelTerm_Term{Term: term877}
		_t1557 = _t1559
	} else {
		var _t1560 *pb.RelTerm
		if prediction875 == 0 {
			_t1561 := p.parse_specialized_value()
			specialized_value876 := _t1561
			_t1562 := &pb.RelTerm{}
			_t1562.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value876}
			_t1560 = _t1562
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1557 = _t1560
	}
	result879 := _t1557
	p.recordSpan(int(span_start878), "RelTerm")
	return result879
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start881 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1563 := p.parse_value()
	value880 := _t1563
	result882 := value880
	p.recordSpan(int(span_start881), "Value")
	return result882
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start888 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1564 := p.parse_name()
	name883 := _t1564
	xs884 := []*pb.RelTerm{}
	cond885 := (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond885 {
		_t1565 := p.parse_rel_term()
		item886 := _t1565
		xs884 = append(xs884, item886)
		cond885 = (((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms887 := xs884
	p.consumeLiteral(")")
	_t1566 := &pb.RelAtom{Name: name883, Terms: rel_terms887}
	result889 := _t1566
	p.recordSpan(int(span_start888), "RelAtom")
	return result889
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start892 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1567 := p.parse_term()
	term890 := _t1567
	_t1568 := p.parse_term()
	term_3891 := _t1568
	p.consumeLiteral(")")
	_t1569 := &pb.Cast{Input: term890, Result: term_3891}
	result893 := _t1569
	p.recordSpan(int(span_start892), "Cast")
	return result893
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs894 := []*pb.Attribute{}
	cond895 := p.matchLookaheadLiteral("(", 0)
	for cond895 {
		_t1570 := p.parse_attribute()
		item896 := _t1570
		xs894 = append(xs894, item896)
		cond895 = p.matchLookaheadLiteral("(", 0)
	}
	attributes897 := xs894
	p.consumeLiteral(")")
	return attributes897
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start903 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1571 := p.parse_name()
	name898 := _t1571
	xs899 := []*pb.Value{}
	cond900 := (((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond900 {
		_t1572 := p.parse_value()
		item901 := _t1572
		xs899 = append(xs899, item901)
		cond900 = (((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values902 := xs899
	p.consumeLiteral(")")
	_t1573 := &pb.Attribute{Name: name898, Args: values902}
	result904 := _t1573
	p.recordSpan(int(span_start903), "Attribute")
	return result904
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start910 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs905 := []*pb.RelationId{}
	cond906 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond906 {
		_t1574 := p.parse_relation_id()
		item907 := _t1574
		xs905 = append(xs905, item907)
		cond906 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids908 := xs905
	_t1575 := p.parse_script()
	script909 := _t1575
	p.consumeLiteral(")")
	_t1576 := &pb.Algorithm{Global: relation_ids908, Body: script909}
	result911 := _t1576
	p.recordSpan(int(span_start910), "Algorithm")
	return result911
}

func (p *Parser) parse_script() *pb.Script {
	span_start916 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs912 := []*pb.Construct{}
	cond913 := p.matchLookaheadLiteral("(", 0)
	for cond913 {
		_t1577 := p.parse_construct()
		item914 := _t1577
		xs912 = append(xs912, item914)
		cond913 = p.matchLookaheadLiteral("(", 0)
	}
	constructs915 := xs912
	p.consumeLiteral(")")
	_t1578 := &pb.Script{Constructs: constructs915}
	result917 := _t1578
	p.recordSpan(int(span_start916), "Script")
	return result917
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start921 := int64(p.spanStart())
	var _t1579 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1580 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1580 = 1
		} else {
			var _t1581 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1581 = 1
			} else {
				var _t1582 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1582 = 1
				} else {
					var _t1583 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1583 = 0
					} else {
						var _t1584 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1584 = 1
						} else {
							var _t1585 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1585 = 1
							} else {
								_t1585 = -1
							}
							_t1584 = _t1585
						}
						_t1583 = _t1584
					}
					_t1582 = _t1583
				}
				_t1581 = _t1582
			}
			_t1580 = _t1581
		}
		_t1579 = _t1580
	} else {
		_t1579 = -1
	}
	prediction918 := _t1579
	var _t1586 *pb.Construct
	if prediction918 == 1 {
		_t1587 := p.parse_instruction()
		instruction920 := _t1587
		_t1588 := &pb.Construct{}
		_t1588.ConstructType = &pb.Construct_Instruction{Instruction: instruction920}
		_t1586 = _t1588
	} else {
		var _t1589 *pb.Construct
		if prediction918 == 0 {
			_t1590 := p.parse_loop()
			loop919 := _t1590
			_t1591 := &pb.Construct{}
			_t1591.ConstructType = &pb.Construct_Loop{Loop: loop919}
			_t1589 = _t1591
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1586 = _t1589
	}
	result922 := _t1586
	p.recordSpan(int(span_start921), "Construct")
	return result922
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start925 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1592 := p.parse_init()
	init923 := _t1592
	_t1593 := p.parse_script()
	script924 := _t1593
	p.consumeLiteral(")")
	_t1594 := &pb.Loop{Init: init923, Body: script924}
	result926 := _t1594
	p.recordSpan(int(span_start925), "Loop")
	return result926
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs927 := []*pb.Instruction{}
	cond928 := p.matchLookaheadLiteral("(", 0)
	for cond928 {
		_t1595 := p.parse_instruction()
		item929 := _t1595
		xs927 = append(xs927, item929)
		cond928 = p.matchLookaheadLiteral("(", 0)
	}
	instructions930 := xs927
	p.consumeLiteral(")")
	return instructions930
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start937 := int64(p.spanStart())
	var _t1596 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1597 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1597 = 1
		} else {
			var _t1598 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1598 = 4
			} else {
				var _t1599 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1599 = 3
				} else {
					var _t1600 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1600 = 2
					} else {
						var _t1601 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1601 = 0
						} else {
							_t1601 = -1
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
	} else {
		_t1596 = -1
	}
	prediction931 := _t1596
	var _t1602 *pb.Instruction
	if prediction931 == 4 {
		_t1603 := p.parse_monus_def()
		monus_def936 := _t1603
		_t1604 := &pb.Instruction{}
		_t1604.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def936}
		_t1602 = _t1604
	} else {
		var _t1605 *pb.Instruction
		if prediction931 == 3 {
			_t1606 := p.parse_monoid_def()
			monoid_def935 := _t1606
			_t1607 := &pb.Instruction{}
			_t1607.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def935}
			_t1605 = _t1607
		} else {
			var _t1608 *pb.Instruction
			if prediction931 == 2 {
				_t1609 := p.parse_break()
				break934 := _t1609
				_t1610 := &pb.Instruction{}
				_t1610.InstrType = &pb.Instruction_Break{Break: break934}
				_t1608 = _t1610
			} else {
				var _t1611 *pb.Instruction
				if prediction931 == 1 {
					_t1612 := p.parse_upsert()
					upsert933 := _t1612
					_t1613 := &pb.Instruction{}
					_t1613.InstrType = &pb.Instruction_Upsert{Upsert: upsert933}
					_t1611 = _t1613
				} else {
					var _t1614 *pb.Instruction
					if prediction931 == 0 {
						_t1615 := p.parse_assign()
						assign932 := _t1615
						_t1616 := &pb.Instruction{}
						_t1616.InstrType = &pb.Instruction_Assign{Assign: assign932}
						_t1614 = _t1616
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1611 = _t1614
				}
				_t1608 = _t1611
			}
			_t1605 = _t1608
		}
		_t1602 = _t1605
	}
	result938 := _t1602
	p.recordSpan(int(span_start937), "Instruction")
	return result938
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1617 := p.parse_relation_id()
	relation_id939 := _t1617
	_t1618 := p.parse_abstraction()
	abstraction940 := _t1618
	var _t1619 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1620 := p.parse_attrs()
		_t1619 = _t1620
	}
	attrs941 := _t1619
	p.consumeLiteral(")")
	_t1621 := attrs941
	if attrs941 == nil {
		_t1621 = []*pb.Attribute{}
	}
	_t1622 := &pb.Assign{Name: relation_id939, Body: abstraction940, Attrs: _t1621}
	result943 := _t1622
	p.recordSpan(int(span_start942), "Assign")
	return result943
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start947 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1623 := p.parse_relation_id()
	relation_id944 := _t1623
	_t1624 := p.parse_abstraction_with_arity()
	abstraction_with_arity945 := _t1624
	var _t1625 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1626 := p.parse_attrs()
		_t1625 = _t1626
	}
	attrs946 := _t1625
	p.consumeLiteral(")")
	_t1627 := attrs946
	if attrs946 == nil {
		_t1627 = []*pb.Attribute{}
	}
	_t1628 := &pb.Upsert{Name: relation_id944, Body: abstraction_with_arity945[0].(*pb.Abstraction), Attrs: _t1627, ValueArity: abstraction_with_arity945[1].(int64)}
	result948 := _t1628
	p.recordSpan(int(span_start947), "Upsert")
	return result948
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1629 := p.parse_bindings()
	bindings949 := _t1629
	_t1630 := p.parse_formula()
	formula950 := _t1630
	p.consumeLiteral(")")
	_t1631 := &pb.Abstraction{Vars: listConcat(bindings949[0].([]*pb.Binding), bindings949[1].([]*pb.Binding)), Value: formula950}
	return []interface{}{_t1631, int64(len(bindings949[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start954 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1632 := p.parse_relation_id()
	relation_id951 := _t1632
	_t1633 := p.parse_abstraction()
	abstraction952 := _t1633
	var _t1634 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1635 := p.parse_attrs()
		_t1634 = _t1635
	}
	attrs953 := _t1634
	p.consumeLiteral(")")
	_t1636 := attrs953
	if attrs953 == nil {
		_t1636 = []*pb.Attribute{}
	}
	_t1637 := &pb.Break{Name: relation_id951, Body: abstraction952, Attrs: _t1636}
	result955 := _t1637
	p.recordSpan(int(span_start954), "Break")
	return result955
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start960 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1638 := p.parse_monoid()
	monoid956 := _t1638
	_t1639 := p.parse_relation_id()
	relation_id957 := _t1639
	_t1640 := p.parse_abstraction_with_arity()
	abstraction_with_arity958 := _t1640
	var _t1641 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1642 := p.parse_attrs()
		_t1641 = _t1642
	}
	attrs959 := _t1641
	p.consumeLiteral(")")
	_t1643 := attrs959
	if attrs959 == nil {
		_t1643 = []*pb.Attribute{}
	}
	_t1644 := &pb.MonoidDef{Monoid: monoid956, Name: relation_id957, Body: abstraction_with_arity958[0].(*pb.Abstraction), Attrs: _t1643, ValueArity: abstraction_with_arity958[1].(int64)}
	result961 := _t1644
	p.recordSpan(int(span_start960), "MonoidDef")
	return result961
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start967 := int64(p.spanStart())
	var _t1645 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1646 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1646 = 3
		} else {
			var _t1647 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1647 = 0
			} else {
				var _t1648 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1648 = 1
				} else {
					var _t1649 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1649 = 2
					} else {
						_t1649 = -1
					}
					_t1648 = _t1649
				}
				_t1647 = _t1648
			}
			_t1646 = _t1647
		}
		_t1645 = _t1646
	} else {
		_t1645 = -1
	}
	prediction962 := _t1645
	var _t1650 *pb.Monoid
	if prediction962 == 3 {
		_t1651 := p.parse_sum_monoid()
		sum_monoid966 := _t1651
		_t1652 := &pb.Monoid{}
		_t1652.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid966}
		_t1650 = _t1652
	} else {
		var _t1653 *pb.Monoid
		if prediction962 == 2 {
			_t1654 := p.parse_max_monoid()
			max_monoid965 := _t1654
			_t1655 := &pb.Monoid{}
			_t1655.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid965}
			_t1653 = _t1655
		} else {
			var _t1656 *pb.Monoid
			if prediction962 == 1 {
				_t1657 := p.parse_min_monoid()
				min_monoid964 := _t1657
				_t1658 := &pb.Monoid{}
				_t1658.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid964}
				_t1656 = _t1658
			} else {
				var _t1659 *pb.Monoid
				if prediction962 == 0 {
					_t1660 := p.parse_or_monoid()
					or_monoid963 := _t1660
					_t1661 := &pb.Monoid{}
					_t1661.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid963}
					_t1659 = _t1661
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1656 = _t1659
			}
			_t1653 = _t1656
		}
		_t1650 = _t1653
	}
	result968 := _t1650
	p.recordSpan(int(span_start967), "Monoid")
	return result968
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1662 := &pb.OrMonoid{}
	result970 := _t1662
	p.recordSpan(int(span_start969), "OrMonoid")
	return result970
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start972 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1663 := p.parse_type()
	type971 := _t1663
	p.consumeLiteral(")")
	_t1664 := &pb.MinMonoid{Type: type971}
	result973 := _t1664
	p.recordSpan(int(span_start972), "MinMonoid")
	return result973
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start975 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1665 := p.parse_type()
	type974 := _t1665
	p.consumeLiteral(")")
	_t1666 := &pb.MaxMonoid{Type: type974}
	result976 := _t1666
	p.recordSpan(int(span_start975), "MaxMonoid")
	return result976
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start978 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1667 := p.parse_type()
	type977 := _t1667
	p.consumeLiteral(")")
	_t1668 := &pb.SumMonoid{Type: type977}
	result979 := _t1668
	p.recordSpan(int(span_start978), "SumMonoid")
	return result979
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start984 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1669 := p.parse_monoid()
	monoid980 := _t1669
	_t1670 := p.parse_relation_id()
	relation_id981 := _t1670
	_t1671 := p.parse_abstraction_with_arity()
	abstraction_with_arity982 := _t1671
	var _t1672 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1673 := p.parse_attrs()
		_t1672 = _t1673
	}
	attrs983 := _t1672
	p.consumeLiteral(")")
	_t1674 := attrs983
	if attrs983 == nil {
		_t1674 = []*pb.Attribute{}
	}
	_t1675 := &pb.MonusDef{Monoid: monoid980, Name: relation_id981, Body: abstraction_with_arity982[0].(*pb.Abstraction), Attrs: _t1674, ValueArity: abstraction_with_arity982[1].(int64)}
	result985 := _t1675
	p.recordSpan(int(span_start984), "MonusDef")
	return result985
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start990 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1676 := p.parse_relation_id()
	relation_id986 := _t1676
	_t1677 := p.parse_abstraction()
	abstraction987 := _t1677
	_t1678 := p.parse_functional_dependency_keys()
	functional_dependency_keys988 := _t1678
	_t1679 := p.parse_functional_dependency_values()
	functional_dependency_values989 := _t1679
	p.consumeLiteral(")")
	_t1680 := &pb.FunctionalDependency{Guard: abstraction987, Keys: functional_dependency_keys988, Values: functional_dependency_values989}
	_t1681 := &pb.Constraint{Name: relation_id986}
	_t1681.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1680}
	result991 := _t1681
	p.recordSpan(int(span_start990), "Constraint")
	return result991
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs992 := []*pb.Var{}
	cond993 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond993 {
		_t1682 := p.parse_var()
		item994 := _t1682
		xs992 = append(xs992, item994)
		cond993 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars995 := xs992
	p.consumeLiteral(")")
	return vars995
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs996 := []*pb.Var{}
	cond997 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond997 {
		_t1683 := p.parse_var()
		item998 := _t1683
		xs996 = append(xs996, item998)
		cond997 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars999 := xs996
	p.consumeLiteral(")")
	return vars999
}

func (p *Parser) parse_data() *pb.Data {
	span_start1004 := int64(p.spanStart())
	var _t1684 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1685 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1685 = 0
		} else {
			var _t1686 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1686 = 2
			} else {
				var _t1687 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1687 = 1
				} else {
					_t1687 = -1
				}
				_t1686 = _t1687
			}
			_t1685 = _t1686
		}
		_t1684 = _t1685
	} else {
		_t1684 = -1
	}
	prediction1000 := _t1684
	var _t1688 *pb.Data
	if prediction1000 == 2 {
		_t1689 := p.parse_csv_data()
		csv_data1003 := _t1689
		_t1690 := &pb.Data{}
		_t1690.DataType = &pb.Data_CsvData{CsvData: csv_data1003}
		_t1688 = _t1690
	} else {
		var _t1691 *pb.Data
		if prediction1000 == 1 {
			_t1692 := p.parse_betree_relation()
			betree_relation1002 := _t1692
			_t1693 := &pb.Data{}
			_t1693.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1002}
			_t1691 = _t1693
		} else {
			var _t1694 *pb.Data
			if prediction1000 == 0 {
				_t1695 := p.parse_edb()
				edb1001 := _t1695
				_t1696 := &pb.Data{}
				_t1696.DataType = &pb.Data_Edb{Edb: edb1001}
				_t1694 = _t1696
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1691 = _t1694
		}
		_t1688 = _t1691
	}
	result1005 := _t1688
	p.recordSpan(int(span_start1004), "Data")
	return result1005
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1697 := p.parse_relation_id()
	relation_id1006 := _t1697
	_t1698 := p.parse_edb_path()
	edb_path1007 := _t1698
	_t1699 := p.parse_edb_types()
	edb_types1008 := _t1699
	p.consumeLiteral(")")
	_t1700 := &pb.EDB{TargetId: relation_id1006, Path: edb_path1007, Types: edb_types1008}
	result1010 := _t1700
	p.recordSpan(int(span_start1009), "EDB")
	return result1010
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1011 := []string{}
	cond1012 := p.matchLookaheadTerminal("STRING", 0)
	for cond1012 {
		item1013 := p.consumeTerminal("STRING").Value.str
		xs1011 = append(xs1011, item1013)
		cond1012 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1014 := xs1011
	p.consumeLiteral("]")
	return strings1014
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1015 := []*pb.Type{}
	cond1016 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1016 {
		_t1701 := p.parse_type()
		item1017 := _t1701
		xs1015 = append(xs1015, item1017)
		cond1016 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1018 := xs1015
	p.consumeLiteral("]")
	return types1018
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1021 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1702 := p.parse_relation_id()
	relation_id1019 := _t1702
	_t1703 := p.parse_betree_info()
	betree_info1020 := _t1703
	p.consumeLiteral(")")
	_t1704 := &pb.BeTreeRelation{Name: relation_id1019, RelationInfo: betree_info1020}
	result1022 := _t1704
	p.recordSpan(int(span_start1021), "BeTreeRelation")
	return result1022
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1026 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1705 := p.parse_betree_info_key_types()
	betree_info_key_types1023 := _t1705
	_t1706 := p.parse_betree_info_value_types()
	betree_info_value_types1024 := _t1706
	_t1707 := p.parse_config_dict()
	config_dict1025 := _t1707
	p.consumeLiteral(")")
	_t1708 := p.construct_betree_info(betree_info_key_types1023, betree_info_value_types1024, config_dict1025)
	result1027 := _t1708
	p.recordSpan(int(span_start1026), "BeTreeInfo")
	return result1027
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1028 := []*pb.Type{}
	cond1029 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1029 {
		_t1709 := p.parse_type()
		item1030 := _t1709
		xs1028 = append(xs1028, item1030)
		cond1029 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1031 := xs1028
	p.consumeLiteral(")")
	return types1031
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1032 := []*pb.Type{}
	cond1033 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1033 {
		_t1710 := p.parse_type()
		item1034 := _t1710
		xs1032 = append(xs1032, item1034)
		cond1033 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1035 := xs1032
	p.consumeLiteral(")")
	return types1035
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1040 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1711 := p.parse_csvlocator()
	csvlocator1036 := _t1711
	_t1712 := p.parse_csv_config()
	csv_config1037 := _t1712
	_t1713 := p.parse_gnf_columns()
	gnf_columns1038 := _t1713
	_t1714 := p.parse_csv_asof()
	csv_asof1039 := _t1714
	p.consumeLiteral(")")
	_t1715 := &pb.CSVData{Locator: csvlocator1036, Config: csv_config1037, Columns: gnf_columns1038, Asof: csv_asof1039}
	result1041 := _t1715
	p.recordSpan(int(span_start1040), "CSVData")
	return result1041
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1044 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1716 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1717 := p.parse_csv_locator_paths()
		_t1716 = _t1717
	}
	csv_locator_paths1042 := _t1716
	var _t1718 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1719 := p.parse_csv_locator_inline_data()
		_t1718 = ptr(_t1719)
	}
	csv_locator_inline_data1043 := _t1718
	p.consumeLiteral(")")
	_t1720 := csv_locator_paths1042
	if csv_locator_paths1042 == nil {
		_t1720 = []string{}
	}
	_t1721 := &pb.CSVLocator{Paths: _t1720, InlineData: []byte(deref(csv_locator_inline_data1043, ""))}
	result1045 := _t1721
	p.recordSpan(int(span_start1044), "CSVLocator")
	return result1045
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1046 := []string{}
	cond1047 := p.matchLookaheadTerminal("STRING", 0)
	for cond1047 {
		item1048 := p.consumeTerminal("STRING").Value.str
		xs1046 = append(xs1046, item1048)
		cond1047 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1049 := xs1046
	p.consumeLiteral(")")
	return strings1049
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1050 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1050
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1722 := p.parse_config_dict()
	config_dict1051 := _t1722
	p.consumeLiteral(")")
	_t1723 := p.construct_csv_config(config_dict1051)
	result1053 := _t1723
	p.recordSpan(int(span_start1052), "CSVConfig")
	return result1053
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1054 := []*pb.GNFColumn{}
	cond1055 := p.matchLookaheadLiteral("(", 0)
	for cond1055 {
		_t1724 := p.parse_gnf_column()
		item1056 := _t1724
		xs1054 = append(xs1054, item1056)
		cond1055 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1057 := xs1054
	p.consumeLiteral(")")
	return gnf_columns1057
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1064 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1725 := p.parse_gnf_column_path()
	gnf_column_path1058 := _t1725
	var _t1726 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1727 := p.parse_relation_id()
		_t1726 = _t1727
	}
	relation_id1059 := _t1726
	p.consumeLiteral("[")
	xs1060 := []*pb.Type{}
	cond1061 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1061 {
		_t1728 := p.parse_type()
		item1062 := _t1728
		xs1060 = append(xs1060, item1062)
		cond1061 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1063 := xs1060
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1729 := &pb.GNFColumn{ColumnPath: gnf_column_path1058, TargetId: relation_id1059, Types: types1063}
	result1065 := _t1729
	p.recordSpan(int(span_start1064), "GNFColumn")
	return result1065
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1730 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1730 = 1
	} else {
		var _t1731 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1731 = 0
		} else {
			_t1731 = -1
		}
		_t1730 = _t1731
	}
	prediction1066 := _t1730
	var _t1732 []string
	if prediction1066 == 1 {
		p.consumeLiteral("[")
		xs1068 := []string{}
		cond1069 := p.matchLookaheadTerminal("STRING", 0)
		for cond1069 {
			item1070 := p.consumeTerminal("STRING").Value.str
			xs1068 = append(xs1068, item1070)
			cond1069 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1071 := xs1068
		p.consumeLiteral("]")
		_t1732 = strings1071
	} else {
		var _t1733 []string
		if prediction1066 == 0 {
			string1067 := p.consumeTerminal("STRING").Value.str
			_ = string1067
			_t1733 = []string{string1067}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1732 = _t1733
	}
	return _t1732
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1072 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1072
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1734 := p.parse_fragment_id()
	fragment_id1073 := _t1734
	p.consumeLiteral(")")
	_t1735 := &pb.Undefine{FragmentId: fragment_id1073}
	result1075 := _t1735
	p.recordSpan(int(span_start1074), "Undefine")
	return result1075
}

func (p *Parser) parse_context() *pb.Context {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1076 := []*pb.RelationId{}
	cond1077 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1077 {
		_t1736 := p.parse_relation_id()
		item1078 := _t1736
		xs1076 = append(xs1076, item1078)
		cond1077 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1079 := xs1076
	p.consumeLiteral(")")
	_t1737 := &pb.Context{Relations: relation_ids1079}
	result1081 := _t1737
	p.recordSpan(int(span_start1080), "Context")
	return result1081
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1082 := []*pb.SnapshotMapping{}
	cond1083 := p.matchLookaheadLiteral("[", 0)
	for cond1083 {
		_t1738 := p.parse_snapshot_mapping()
		item1084 := _t1738
		xs1082 = append(xs1082, item1084)
		cond1083 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1085 := xs1082
	p.consumeLiteral(")")
	_t1739 := &pb.Snapshot{Mappings: snapshot_mappings1085}
	result1087 := _t1739
	p.recordSpan(int(span_start1086), "Snapshot")
	return result1087
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1090 := int64(p.spanStart())
	_t1740 := p.parse_edb_path()
	edb_path1088 := _t1740
	_t1741 := p.parse_relation_id()
	relation_id1089 := _t1741
	_t1742 := &pb.SnapshotMapping{DestinationPath: edb_path1088, SourceRelation: relation_id1089}
	result1091 := _t1742
	p.recordSpan(int(span_start1090), "SnapshotMapping")
	return result1091
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1092 := []*pb.Read{}
	cond1093 := p.matchLookaheadLiteral("(", 0)
	for cond1093 {
		_t1743 := p.parse_read()
		item1094 := _t1743
		xs1092 = append(xs1092, item1094)
		cond1093 = p.matchLookaheadLiteral("(", 0)
	}
	reads1095 := xs1092
	p.consumeLiteral(")")
	return reads1095
}

func (p *Parser) parse_read() *pb.Read {
	span_start1102 := int64(p.spanStart())
	var _t1744 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1745 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1745 = 2
		} else {
			var _t1746 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1746 = 1
			} else {
				var _t1747 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1747 = 4
				} else {
					var _t1748 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1748 = 0
					} else {
						var _t1749 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1749 = 3
						} else {
							_t1749 = -1
						}
						_t1748 = _t1749
					}
					_t1747 = _t1748
				}
				_t1746 = _t1747
			}
			_t1745 = _t1746
		}
		_t1744 = _t1745
	} else {
		_t1744 = -1
	}
	prediction1096 := _t1744
	var _t1750 *pb.Read
	if prediction1096 == 4 {
		_t1751 := p.parse_export()
		export1101 := _t1751
		_t1752 := &pb.Read{}
		_t1752.ReadType = &pb.Read_Export{Export: export1101}
		_t1750 = _t1752
	} else {
		var _t1753 *pb.Read
		if prediction1096 == 3 {
			_t1754 := p.parse_abort()
			abort1100 := _t1754
			_t1755 := &pb.Read{}
			_t1755.ReadType = &pb.Read_Abort{Abort: abort1100}
			_t1753 = _t1755
		} else {
			var _t1756 *pb.Read
			if prediction1096 == 2 {
				_t1757 := p.parse_what_if()
				what_if1099 := _t1757
				_t1758 := &pb.Read{}
				_t1758.ReadType = &pb.Read_WhatIf{WhatIf: what_if1099}
				_t1756 = _t1758
			} else {
				var _t1759 *pb.Read
				if prediction1096 == 1 {
					_t1760 := p.parse_output()
					output1098 := _t1760
					_t1761 := &pb.Read{}
					_t1761.ReadType = &pb.Read_Output{Output: output1098}
					_t1759 = _t1761
				} else {
					var _t1762 *pb.Read
					if prediction1096 == 0 {
						_t1763 := p.parse_demand()
						demand1097 := _t1763
						_t1764 := &pb.Read{}
						_t1764.ReadType = &pb.Read_Demand{Demand: demand1097}
						_t1762 = _t1764
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1759 = _t1762
				}
				_t1756 = _t1759
			}
			_t1753 = _t1756
		}
		_t1750 = _t1753
	}
	result1103 := _t1750
	p.recordSpan(int(span_start1102), "Read")
	return result1103
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1105 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1765 := p.parse_relation_id()
	relation_id1104 := _t1765
	p.consumeLiteral(")")
	_t1766 := &pb.Demand{RelationId: relation_id1104}
	result1106 := _t1766
	p.recordSpan(int(span_start1105), "Demand")
	return result1106
}

func (p *Parser) parse_output() *pb.Output {
	span_start1109 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1767 := p.parse_name()
	name1107 := _t1767
	_t1768 := p.parse_relation_id()
	relation_id1108 := _t1768
	p.consumeLiteral(")")
	_t1769 := &pb.Output{Name: name1107, RelationId: relation_id1108}
	result1110 := _t1769
	p.recordSpan(int(span_start1109), "Output")
	return result1110
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1113 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1770 := p.parse_name()
	name1111 := _t1770
	_t1771 := p.parse_epoch()
	epoch1112 := _t1771
	p.consumeLiteral(")")
	_t1772 := &pb.WhatIf{Branch: name1111, Epoch: epoch1112}
	result1114 := _t1772
	p.recordSpan(int(span_start1113), "WhatIf")
	return result1114
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1773 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1774 := p.parse_name()
		_t1773 = ptr(_t1774)
	}
	name1115 := _t1773
	_t1775 := p.parse_relation_id()
	relation_id1116 := _t1775
	p.consumeLiteral(")")
	_t1776 := &pb.Abort{Name: deref(name1115, "abort"), RelationId: relation_id1116}
	result1118 := _t1776
	p.recordSpan(int(span_start1117), "Abort")
	return result1118
}

func (p *Parser) parse_export() *pb.Export {
	span_start1120 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1777 := p.parse_export_csv_config()
	export_csv_config1119 := _t1777
	p.consumeLiteral(")")
	_t1778 := &pb.Export{}
	_t1778.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1119}
	result1121 := _t1778
	p.recordSpan(int(span_start1120), "Export")
	return result1121
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1129 := int64(p.spanStart())
	var _t1779 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1780 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1780 = 0
		} else {
			var _t1781 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1781 = 1
			} else {
				_t1781 = -1
			}
			_t1780 = _t1781
		}
		_t1779 = _t1780
	} else {
		_t1779 = -1
	}
	prediction1122 := _t1779
	var _t1782 *pb.ExportCSVConfig
	if prediction1122 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1783 := p.parse_export_csv_path()
		export_csv_path1126 := _t1783
		_t1784 := p.parse_export_csv_columns_list()
		export_csv_columns_list1127 := _t1784
		_t1785 := p.parse_config_dict()
		config_dict1128 := _t1785
		p.consumeLiteral(")")
		_t1786 := p.construct_export_csv_config(export_csv_path1126, export_csv_columns_list1127, config_dict1128)
		_t1782 = _t1786
	} else {
		var _t1787 *pb.ExportCSVConfig
		if prediction1122 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1788 := p.parse_export_csv_path()
			export_csv_path1123 := _t1788
			_t1789 := p.parse_export_csv_source()
			export_csv_source1124 := _t1789
			_t1790 := p.parse_csv_config()
			csv_config1125 := _t1790
			p.consumeLiteral(")")
			_t1791 := p.construct_export_csv_config_with_source(export_csv_path1123, export_csv_source1124, csv_config1125)
			_t1787 = _t1791
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1782 = _t1787
	}
	result1130 := _t1782
	p.recordSpan(int(span_start1129), "ExportCSVConfig")
	return result1130
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1131 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1131
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1138 := int64(p.spanStart())
	var _t1792 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1793 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1793 = 1
		} else {
			var _t1794 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1794 = 0
			} else {
				_t1794 = -1
			}
			_t1793 = _t1794
		}
		_t1792 = _t1793
	} else {
		_t1792 = -1
	}
	prediction1132 := _t1792
	var _t1795 *pb.ExportCSVSource
	if prediction1132 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1796 := p.parse_relation_id()
		relation_id1137 := _t1796
		p.consumeLiteral(")")
		_t1797 := &pb.ExportCSVSource{}
		_t1797.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1137}
		_t1795 = _t1797
	} else {
		var _t1798 *pb.ExportCSVSource
		if prediction1132 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1133 := []*pb.ExportCSVColumn{}
			cond1134 := p.matchLookaheadLiteral("(", 0)
			for cond1134 {
				_t1799 := p.parse_export_csv_column()
				item1135 := _t1799
				xs1133 = append(xs1133, item1135)
				cond1134 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1136 := xs1133
			p.consumeLiteral(")")
			_t1800 := &pb.ExportCSVColumns{Columns: export_csv_columns1136}
			_t1801 := &pb.ExportCSVSource{}
			_t1801.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1800}
			_t1798 = _t1801
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1795 = _t1798
	}
	result1139 := _t1795
	p.recordSpan(int(span_start1138), "ExportCSVSource")
	return result1139
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1142 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1140 := p.consumeTerminal("STRING").Value.str
	_t1802 := p.parse_relation_id()
	relation_id1141 := _t1802
	p.consumeLiteral(")")
	_t1803 := &pb.ExportCSVColumn{ColumnName: string1140, ColumnData: relation_id1141}
	result1143 := _t1803
	p.recordSpan(int(span_start1142), "ExportCSVColumn")
	return result1143
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1144 := []*pb.ExportCSVColumn{}
	cond1145 := p.matchLookaheadLiteral("(", 0)
	for cond1145 {
		_t1804 := p.parse_export_csv_column()
		item1146 := _t1804
		xs1144 = append(xs1144, item1146)
		cond1145 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1147 := xs1144
	p.consumeLiteral(")")
	return export_csv_columns1147
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
