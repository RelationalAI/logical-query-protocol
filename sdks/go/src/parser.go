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
	var _t1823 interface{}
	if (value != nil && hasProtoField(value, "int32_value")) {
		return value.GetInt32Value()
	}
	_ = _t1823
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1824 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1824
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1825 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1825
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1826 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1826
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1827 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1827
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1828 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1828
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1829 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1829
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1830 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1830
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1831 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1831
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1832 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1832
	_t1833 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1833
	_t1834 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1834
	_t1835 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1835
	_t1836 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1836
	_t1837 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1837
	_t1838 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1838
	_t1839 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1839
	_t1840 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1840
	_t1841 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1841
	_t1842 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1842
	_t1843 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1843
	_t1844 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1844
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1845 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1845
	_t1846 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1846
	_t1847 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1847
	_t1848 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1848
	_t1849 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1849
	_t1850 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1850
	_t1851 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1851
	_t1852 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1852
	_t1853 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1853
	_t1854 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1854.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1854.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1854
	_t1855 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1855
}

func (p *Parser) default_configure() *pb.Configure {
	_t1856 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1856
	_t1857 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1857
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
	_t1858 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1858
	_t1859 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1859
	_t1860 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1860
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1861 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1861
	_t1862 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1862
	_t1863 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1863
	_t1864 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1864
	_t1865 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1865
	_t1866 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1866
	_t1867 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1867
	_t1868 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1868
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1869 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1869
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start584 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1156 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1157 := p.parse_configure()
		_t1156 = _t1157
	}
	configure578 := _t1156
	var _t1158 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1159 := p.parse_sync()
		_t1158 = _t1159
	}
	sync579 := _t1158
	xs580 := []*pb.Epoch{}
	cond581 := p.matchLookaheadLiteral("(", 0)
	for cond581 {
		_t1160 := p.parse_epoch()
		item582 := _t1160
		xs580 = append(xs580, item582)
		cond581 = p.matchLookaheadLiteral("(", 0)
	}
	epochs583 := xs580
	p.consumeLiteral(")")
	_t1161 := p.default_configure()
	_t1162 := configure578
	if configure578 == nil {
		_t1162 = _t1161
	}
	_t1163 := &pb.Transaction{Epochs: epochs583, Configure: _t1162, Sync: sync579}
	result585 := _t1163
	p.recordSpan(int(span_start584), "Transaction")
	return result585
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start587 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1164 := p.parse_config_dict()
	config_dict586 := _t1164
	p.consumeLiteral(")")
	_t1165 := p.construct_configure(config_dict586)
	result588 := _t1165
	p.recordSpan(int(span_start587), "Configure")
	return result588
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs589 := [][]interface{}{}
	cond590 := p.matchLookaheadLiteral(":", 0)
	for cond590 {
		_t1166 := p.parse_config_key_value()
		item591 := _t1166
		xs589 = append(xs589, item591)
		cond590 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values592 := xs589
	p.consumeLiteral("}")
	return config_key_values592
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol593 := p.consumeTerminal("SYMBOL").Value.str
	_t1167 := p.parse_value()
	value594 := _t1167
	return []interface{}{symbol593, value594}
}

func (p *Parser) parse_value() *pb.Value {
	span_start608 := int64(p.spanStart())
	var _t1168 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1168 = 9
	} else {
		var _t1169 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1169 = 8
		} else {
			var _t1170 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1170 = 9
			} else {
				var _t1171 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1172 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1172 = 1
					} else {
						var _t1173 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1173 = 0
						} else {
							_t1173 = -1
						}
						_t1172 = _t1173
					}
					_t1171 = _t1172
				} else {
					var _t1174 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1174 = 12
					} else {
						var _t1175 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1175 = 5
						} else {
							var _t1176 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1176 = 2
							} else {
								var _t1177 int64
								if p.matchLookaheadTerminal("INT32", 0) {
									_t1177 = 10
								} else {
									var _t1178 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1178 = 6
									} else {
										var _t1179 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1179 = 3
										} else {
											var _t1180 int64
											if p.matchLookaheadTerminal("FLOAT32", 0) {
												_t1180 = 11
											} else {
												var _t1181 int64
												if p.matchLookaheadTerminal("FLOAT", 0) {
													_t1181 = 4
												} else {
													var _t1182 int64
													if p.matchLookaheadTerminal("DECIMAL", 0) {
														_t1182 = 7
													} else {
														_t1182 = -1
													}
													_t1181 = _t1182
												}
												_t1180 = _t1181
											}
											_t1179 = _t1180
										}
										_t1178 = _t1179
									}
									_t1177 = _t1178
								}
								_t1176 = _t1177
							}
							_t1175 = _t1176
						}
						_t1174 = _t1175
					}
					_t1171 = _t1174
				}
				_t1170 = _t1171
			}
			_t1169 = _t1170
		}
		_t1168 = _t1169
	}
	prediction595 := _t1168
	var _t1183 *pb.Value
	if prediction595 == 12 {
		uint32607 := p.consumeTerminal("UINT32").Value.u32
		_t1184 := &pb.Value{}
		_t1184.Value = &pb.Value_Uint32Value{Uint32Value: uint32607}
		_t1183 = _t1184
	} else {
		var _t1185 *pb.Value
		if prediction595 == 11 {
			float32606 := p.consumeTerminal("FLOAT32").Value.f32
			_t1186 := &pb.Value{}
			_t1186.Value = &pb.Value_Float32Value{Float32Value: float32606}
			_t1185 = _t1186
		} else {
			var _t1187 *pb.Value
			if prediction595 == 10 {
				int32605 := p.consumeTerminal("INT32").Value.i32
				_t1188 := &pb.Value{}
				_t1188.Value = &pb.Value_Int32Value{Int32Value: int32605}
				_t1187 = _t1188
			} else {
				var _t1189 *pb.Value
				if prediction595 == 9 {
					_t1190 := p.parse_boolean_value()
					boolean_value604 := _t1190
					_t1191 := &pb.Value{}
					_t1191.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value604}
					_t1189 = _t1191
				} else {
					var _t1192 *pb.Value
					if prediction595 == 8 {
						p.consumeLiteral("missing")
						_t1193 := &pb.MissingValue{}
						_t1194 := &pb.Value{}
						_t1194.Value = &pb.Value_MissingValue{MissingValue: _t1193}
						_t1192 = _t1194
					} else {
						var _t1195 *pb.Value
						if prediction595 == 7 {
							decimal603 := p.consumeTerminal("DECIMAL").Value.decimal
							_t1196 := &pb.Value{}
							_t1196.Value = &pb.Value_DecimalValue{DecimalValue: decimal603}
							_t1195 = _t1196
						} else {
							var _t1197 *pb.Value
							if prediction595 == 6 {
								int128602 := p.consumeTerminal("INT128").Value.int128
								_t1198 := &pb.Value{}
								_t1198.Value = &pb.Value_Int128Value{Int128Value: int128602}
								_t1197 = _t1198
							} else {
								var _t1199 *pb.Value
								if prediction595 == 5 {
									uint128601 := p.consumeTerminal("UINT128").Value.uint128
									_t1200 := &pb.Value{}
									_t1200.Value = &pb.Value_Uint128Value{Uint128Value: uint128601}
									_t1199 = _t1200
								} else {
									var _t1201 *pb.Value
									if prediction595 == 4 {
										float600 := p.consumeTerminal("FLOAT").Value.f64
										_t1202 := &pb.Value{}
										_t1202.Value = &pb.Value_FloatValue{FloatValue: float600}
										_t1201 = _t1202
									} else {
										var _t1203 *pb.Value
										if prediction595 == 3 {
											int599 := p.consumeTerminal("INT").Value.i64
											_t1204 := &pb.Value{}
											_t1204.Value = &pb.Value_IntValue{IntValue: int599}
											_t1203 = _t1204
										} else {
											var _t1205 *pb.Value
											if prediction595 == 2 {
												string598 := p.consumeTerminal("STRING").Value.str
												_t1206 := &pb.Value{}
												_t1206.Value = &pb.Value_StringValue{StringValue: string598}
												_t1205 = _t1206
											} else {
												var _t1207 *pb.Value
												if prediction595 == 1 {
													_t1208 := p.parse_datetime()
													datetime597 := _t1208
													_t1209 := &pb.Value{}
													_t1209.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime597}
													_t1207 = _t1209
												} else {
													var _t1210 *pb.Value
													if prediction595 == 0 {
														_t1211 := p.parse_date()
														date596 := _t1211
														_t1212 := &pb.Value{}
														_t1212.Value = &pb.Value_DateValue{DateValue: date596}
														_t1210 = _t1212
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1207 = _t1210
												}
												_t1205 = _t1207
											}
											_t1203 = _t1205
										}
										_t1201 = _t1203
									}
									_t1199 = _t1201
								}
								_t1197 = _t1199
							}
							_t1195 = _t1197
						}
						_t1192 = _t1195
					}
					_t1189 = _t1192
				}
				_t1187 = _t1189
			}
			_t1185 = _t1187
		}
		_t1183 = _t1185
	}
	result609 := _t1183
	p.recordSpan(int(span_start608), "Value")
	return result609
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start613 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int610 := p.consumeTerminal("INT").Value.i64
	int_3611 := p.consumeTerminal("INT").Value.i64
	int_4612 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1213 := &pb.DateValue{Year: int32(int610), Month: int32(int_3611), Day: int32(int_4612)}
	result614 := _t1213
	p.recordSpan(int(span_start613), "DateValue")
	return result614
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start622 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int615 := p.consumeTerminal("INT").Value.i64
	int_3616 := p.consumeTerminal("INT").Value.i64
	int_4617 := p.consumeTerminal("INT").Value.i64
	int_5618 := p.consumeTerminal("INT").Value.i64
	int_6619 := p.consumeTerminal("INT").Value.i64
	int_7620 := p.consumeTerminal("INT").Value.i64
	var _t1214 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1214 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8621 := _t1214
	p.consumeLiteral(")")
	_t1215 := &pb.DateTimeValue{Year: int32(int615), Month: int32(int_3616), Day: int32(int_4617), Hour: int32(int_5618), Minute: int32(int_6619), Second: int32(int_7620), Microsecond: int32(deref(int_8621, 0))}
	result623 := _t1215
	p.recordSpan(int(span_start622), "DateTimeValue")
	return result623
}

func (p *Parser) parse_boolean_value() bool {
	var _t1216 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1216 = 0
	} else {
		var _t1217 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1217 = 1
		} else {
			_t1217 = -1
		}
		_t1216 = _t1217
	}
	prediction624 := _t1216
	var _t1218 bool
	if prediction624 == 1 {
		p.consumeLiteral("false")
		_t1218 = false
	} else {
		var _t1219 bool
		if prediction624 == 0 {
			p.consumeLiteral("true")
			_t1219 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1218 = _t1219
	}
	return _t1218
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start629 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs625 := []*pb.FragmentId{}
	cond626 := p.matchLookaheadLiteral(":", 0)
	for cond626 {
		_t1220 := p.parse_fragment_id()
		item627 := _t1220
		xs625 = append(xs625, item627)
		cond626 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids628 := xs625
	p.consumeLiteral(")")
	_t1221 := &pb.Sync{Fragments: fragment_ids628}
	result630 := _t1221
	p.recordSpan(int(span_start629), "Sync")
	return result630
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start632 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol631 := p.consumeTerminal("SYMBOL").Value.str
	result633 := &pb.FragmentId{Id: []byte(symbol631)}
	p.recordSpan(int(span_start632), "FragmentId")
	return result633
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start636 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1222 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1223 := p.parse_epoch_writes()
		_t1222 = _t1223
	}
	epoch_writes634 := _t1222
	var _t1224 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1225 := p.parse_epoch_reads()
		_t1224 = _t1225
	}
	epoch_reads635 := _t1224
	p.consumeLiteral(")")
	_t1226 := epoch_writes634
	if epoch_writes634 == nil {
		_t1226 = []*pb.Write{}
	}
	_t1227 := epoch_reads635
	if epoch_reads635 == nil {
		_t1227 = []*pb.Read{}
	}
	_t1228 := &pb.Epoch{Writes: _t1226, Reads: _t1227}
	result637 := _t1228
	p.recordSpan(int(span_start636), "Epoch")
	return result637
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs638 := []*pb.Write{}
	cond639 := p.matchLookaheadLiteral("(", 0)
	for cond639 {
		_t1229 := p.parse_write()
		item640 := _t1229
		xs638 = append(xs638, item640)
		cond639 = p.matchLookaheadLiteral("(", 0)
	}
	writes641 := xs638
	p.consumeLiteral(")")
	return writes641
}

func (p *Parser) parse_write() *pb.Write {
	span_start647 := int64(p.spanStart())
	var _t1230 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1231 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1231 = 1
		} else {
			var _t1232 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1232 = 3
			} else {
				var _t1233 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1233 = 0
				} else {
					var _t1234 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1234 = 2
					} else {
						_t1234 = -1
					}
					_t1233 = _t1234
				}
				_t1232 = _t1233
			}
			_t1231 = _t1232
		}
		_t1230 = _t1231
	} else {
		_t1230 = -1
	}
	prediction642 := _t1230
	var _t1235 *pb.Write
	if prediction642 == 3 {
		_t1236 := p.parse_snapshot()
		snapshot646 := _t1236
		_t1237 := &pb.Write{}
		_t1237.WriteType = &pb.Write_Snapshot{Snapshot: snapshot646}
		_t1235 = _t1237
	} else {
		var _t1238 *pb.Write
		if prediction642 == 2 {
			_t1239 := p.parse_context()
			context645 := _t1239
			_t1240 := &pb.Write{}
			_t1240.WriteType = &pb.Write_Context{Context: context645}
			_t1238 = _t1240
		} else {
			var _t1241 *pb.Write
			if prediction642 == 1 {
				_t1242 := p.parse_undefine()
				undefine644 := _t1242
				_t1243 := &pb.Write{}
				_t1243.WriteType = &pb.Write_Undefine{Undefine: undefine644}
				_t1241 = _t1243
			} else {
				var _t1244 *pb.Write
				if prediction642 == 0 {
					_t1245 := p.parse_define()
					define643 := _t1245
					_t1246 := &pb.Write{}
					_t1246.WriteType = &pb.Write_Define{Define: define643}
					_t1244 = _t1246
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1241 = _t1244
			}
			_t1238 = _t1241
		}
		_t1235 = _t1238
	}
	result648 := _t1235
	p.recordSpan(int(span_start647), "Write")
	return result648
}

func (p *Parser) parse_define() *pb.Define {
	span_start650 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1247 := p.parse_fragment()
	fragment649 := _t1247
	p.consumeLiteral(")")
	_t1248 := &pb.Define{Fragment: fragment649}
	result651 := _t1248
	p.recordSpan(int(span_start650), "Define")
	return result651
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start657 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1249 := p.parse_new_fragment_id()
	new_fragment_id652 := _t1249
	xs653 := []*pb.Declaration{}
	cond654 := p.matchLookaheadLiteral("(", 0)
	for cond654 {
		_t1250 := p.parse_declaration()
		item655 := _t1250
		xs653 = append(xs653, item655)
		cond654 = p.matchLookaheadLiteral("(", 0)
	}
	declarations656 := xs653
	p.consumeLiteral(")")
	result658 := p.constructFragment(new_fragment_id652, declarations656)
	p.recordSpan(int(span_start657), "Fragment")
	return result658
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start660 := int64(p.spanStart())
	_t1251 := p.parse_fragment_id()
	fragment_id659 := _t1251
	p.startFragment(fragment_id659)
	result661 := fragment_id659
	p.recordSpan(int(span_start660), "FragmentId")
	return result661
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start667 := int64(p.spanStart())
	var _t1252 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1253 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1253 = 2
		} else {
			var _t1254 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1254 = 3
			} else {
				var _t1255 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1255 = 0
				} else {
					var _t1256 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1256 = 3
					} else {
						var _t1257 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1257 = 3
						} else {
							var _t1258 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1258 = 1
							} else {
								_t1258 = -1
							}
							_t1257 = _t1258
						}
						_t1256 = _t1257
					}
					_t1255 = _t1256
				}
				_t1254 = _t1255
			}
			_t1253 = _t1254
		}
		_t1252 = _t1253
	} else {
		_t1252 = -1
	}
	prediction662 := _t1252
	var _t1259 *pb.Declaration
	if prediction662 == 3 {
		_t1260 := p.parse_data()
		data666 := _t1260
		_t1261 := &pb.Declaration{}
		_t1261.DeclarationType = &pb.Declaration_Data{Data: data666}
		_t1259 = _t1261
	} else {
		var _t1262 *pb.Declaration
		if prediction662 == 2 {
			_t1263 := p.parse_constraint()
			constraint665 := _t1263
			_t1264 := &pb.Declaration{}
			_t1264.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint665}
			_t1262 = _t1264
		} else {
			var _t1265 *pb.Declaration
			if prediction662 == 1 {
				_t1266 := p.parse_algorithm()
				algorithm664 := _t1266
				_t1267 := &pb.Declaration{}
				_t1267.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm664}
				_t1265 = _t1267
			} else {
				var _t1268 *pb.Declaration
				if prediction662 == 0 {
					_t1269 := p.parse_def()
					def663 := _t1269
					_t1270 := &pb.Declaration{}
					_t1270.DeclarationType = &pb.Declaration_Def{Def: def663}
					_t1268 = _t1270
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1265 = _t1268
			}
			_t1262 = _t1265
		}
		_t1259 = _t1262
	}
	result668 := _t1259
	p.recordSpan(int(span_start667), "Declaration")
	return result668
}

func (p *Parser) parse_def() *pb.Def {
	span_start672 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1271 := p.parse_relation_id()
	relation_id669 := _t1271
	_t1272 := p.parse_abstraction()
	abstraction670 := _t1272
	var _t1273 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1274 := p.parse_attrs()
		_t1273 = _t1274
	}
	attrs671 := _t1273
	p.consumeLiteral(")")
	_t1275 := attrs671
	if attrs671 == nil {
		_t1275 = []*pb.Attribute{}
	}
	_t1276 := &pb.Def{Name: relation_id669, Body: abstraction670, Attrs: _t1275}
	result673 := _t1276
	p.recordSpan(int(span_start672), "Def")
	return result673
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start677 := int64(p.spanStart())
	var _t1277 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1277 = 0
	} else {
		var _t1278 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1278 = 1
		} else {
			_t1278 = -1
		}
		_t1277 = _t1278
	}
	prediction674 := _t1277
	var _t1279 *pb.RelationId
	if prediction674 == 1 {
		uint128676 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128676
		_t1279 = &pb.RelationId{IdLow: uint128676.Low, IdHigh: uint128676.High}
	} else {
		var _t1280 *pb.RelationId
		if prediction674 == 0 {
			p.consumeLiteral(":")
			symbol675 := p.consumeTerminal("SYMBOL").Value.str
			_t1280 = p.relationIdFromString(symbol675)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1279 = _t1280
	}
	result678 := _t1279
	p.recordSpan(int(span_start677), "RelationId")
	return result678
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start681 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1281 := p.parse_bindings()
	bindings679 := _t1281
	_t1282 := p.parse_formula()
	formula680 := _t1282
	p.consumeLiteral(")")
	_t1283 := &pb.Abstraction{Vars: listConcat(bindings679[0].([]*pb.Binding), bindings679[1].([]*pb.Binding)), Value: formula680}
	result682 := _t1283
	p.recordSpan(int(span_start681), "Abstraction")
	return result682
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs683 := []*pb.Binding{}
	cond684 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond684 {
		_t1284 := p.parse_binding()
		item685 := _t1284
		xs683 = append(xs683, item685)
		cond684 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings686 := xs683
	var _t1285 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1286 := p.parse_value_bindings()
		_t1285 = _t1286
	}
	value_bindings687 := _t1285
	p.consumeLiteral("]")
	_t1287 := value_bindings687
	if value_bindings687 == nil {
		_t1287 = []*pb.Binding{}
	}
	return []interface{}{bindings686, _t1287}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start690 := int64(p.spanStart())
	symbol688 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1288 := p.parse_type()
	type689 := _t1288
	_t1289 := &pb.Var{Name: symbol688}
	_t1290 := &pb.Binding{Var: _t1289, Type: type689}
	result691 := _t1290
	p.recordSpan(int(span_start690), "Binding")
	return result691
}

func (p *Parser) parse_type() *pb.Type {
	span_start707 := int64(p.spanStart())
	var _t1291 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1291 = 0
	} else {
		var _t1292 int64
		if p.matchLookaheadLiteral("UINT32", 0) {
			_t1292 = 13
		} else {
			var _t1293 int64
			if p.matchLookaheadLiteral("UINT128", 0) {
				_t1293 = 4
			} else {
				var _t1294 int64
				if p.matchLookaheadLiteral("STRING", 0) {
					_t1294 = 1
				} else {
					var _t1295 int64
					if p.matchLookaheadLiteral("MISSING", 0) {
						_t1295 = 8
					} else {
						var _t1296 int64
						if p.matchLookaheadLiteral("INT32", 0) {
							_t1296 = 11
						} else {
							var _t1297 int64
							if p.matchLookaheadLiteral("INT128", 0) {
								_t1297 = 5
							} else {
								var _t1298 int64
								if p.matchLookaheadLiteral("INT", 0) {
									_t1298 = 2
								} else {
									var _t1299 int64
									if p.matchLookaheadLiteral("FLOAT32", 0) {
										_t1299 = 12
									} else {
										var _t1300 int64
										if p.matchLookaheadLiteral("FLOAT", 0) {
											_t1300 = 3
										} else {
											var _t1301 int64
											if p.matchLookaheadLiteral("DATETIME", 0) {
												_t1301 = 7
											} else {
												var _t1302 int64
												if p.matchLookaheadLiteral("DATE", 0) {
													_t1302 = 6
												} else {
													var _t1303 int64
													if p.matchLookaheadLiteral("BOOLEAN", 0) {
														_t1303 = 10
													} else {
														var _t1304 int64
														if p.matchLookaheadLiteral("(", 0) {
															_t1304 = 9
														} else {
															_t1304 = -1
														}
														_t1303 = _t1304
													}
													_t1302 = _t1303
												}
												_t1301 = _t1302
											}
											_t1300 = _t1301
										}
										_t1299 = _t1300
									}
									_t1298 = _t1299
								}
								_t1297 = _t1298
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
	}
	prediction692 := _t1291
	var _t1305 *pb.Type
	if prediction692 == 13 {
		_t1306 := p.parse_uint32_type()
		uint32_type706 := _t1306
		_t1307 := &pb.Type{}
		_t1307.Type = &pb.Type_Uint32Type{Uint32Type: uint32_type706}
		_t1305 = _t1307
	} else {
		var _t1308 *pb.Type
		if prediction692 == 12 {
			_t1309 := p.parse_float32_type()
			float32_type705 := _t1309
			_t1310 := &pb.Type{}
			_t1310.Type = &pb.Type_Float32Type{Float32Type: float32_type705}
			_t1308 = _t1310
		} else {
			var _t1311 *pb.Type
			if prediction692 == 11 {
				_t1312 := p.parse_int32_type()
				int32_type704 := _t1312
				_t1313 := &pb.Type{}
				_t1313.Type = &pb.Type_Int32Type{Int32Type: int32_type704}
				_t1311 = _t1313
			} else {
				var _t1314 *pb.Type
				if prediction692 == 10 {
					_t1315 := p.parse_boolean_type()
					boolean_type703 := _t1315
					_t1316 := &pb.Type{}
					_t1316.Type = &pb.Type_BooleanType{BooleanType: boolean_type703}
					_t1314 = _t1316
				} else {
					var _t1317 *pb.Type
					if prediction692 == 9 {
						_t1318 := p.parse_decimal_type()
						decimal_type702 := _t1318
						_t1319 := &pb.Type{}
						_t1319.Type = &pb.Type_DecimalType{DecimalType: decimal_type702}
						_t1317 = _t1319
					} else {
						var _t1320 *pb.Type
						if prediction692 == 8 {
							_t1321 := p.parse_missing_type()
							missing_type701 := _t1321
							_t1322 := &pb.Type{}
							_t1322.Type = &pb.Type_MissingType{MissingType: missing_type701}
							_t1320 = _t1322
						} else {
							var _t1323 *pb.Type
							if prediction692 == 7 {
								_t1324 := p.parse_datetime_type()
								datetime_type700 := _t1324
								_t1325 := &pb.Type{}
								_t1325.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type700}
								_t1323 = _t1325
							} else {
								var _t1326 *pb.Type
								if prediction692 == 6 {
									_t1327 := p.parse_date_type()
									date_type699 := _t1327
									_t1328 := &pb.Type{}
									_t1328.Type = &pb.Type_DateType{DateType: date_type699}
									_t1326 = _t1328
								} else {
									var _t1329 *pb.Type
									if prediction692 == 5 {
										_t1330 := p.parse_int128_type()
										int128_type698 := _t1330
										_t1331 := &pb.Type{}
										_t1331.Type = &pb.Type_Int128Type{Int128Type: int128_type698}
										_t1329 = _t1331
									} else {
										var _t1332 *pb.Type
										if prediction692 == 4 {
											_t1333 := p.parse_uint128_type()
											uint128_type697 := _t1333
											_t1334 := &pb.Type{}
											_t1334.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type697}
											_t1332 = _t1334
										} else {
											var _t1335 *pb.Type
											if prediction692 == 3 {
												_t1336 := p.parse_float_type()
												float_type696 := _t1336
												_t1337 := &pb.Type{}
												_t1337.Type = &pb.Type_FloatType{FloatType: float_type696}
												_t1335 = _t1337
											} else {
												var _t1338 *pb.Type
												if prediction692 == 2 {
													_t1339 := p.parse_int_type()
													int_type695 := _t1339
													_t1340 := &pb.Type{}
													_t1340.Type = &pb.Type_IntType{IntType: int_type695}
													_t1338 = _t1340
												} else {
													var _t1341 *pb.Type
													if prediction692 == 1 {
														_t1342 := p.parse_string_type()
														string_type694 := _t1342
														_t1343 := &pb.Type{}
														_t1343.Type = &pb.Type_StringType{StringType: string_type694}
														_t1341 = _t1343
													} else {
														var _t1344 *pb.Type
														if prediction692 == 0 {
															_t1345 := p.parse_unspecified_type()
															unspecified_type693 := _t1345
															_t1346 := &pb.Type{}
															_t1346.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type693}
															_t1344 = _t1346
														} else {
															panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
														}
														_t1341 = _t1344
													}
													_t1338 = _t1341
												}
												_t1335 = _t1338
											}
											_t1332 = _t1335
										}
										_t1329 = _t1332
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
	result708 := _t1305
	p.recordSpan(int(span_start707), "Type")
	return result708
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start709 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1347 := &pb.UnspecifiedType{}
	result710 := _t1347
	p.recordSpan(int(span_start709), "UnspecifiedType")
	return result710
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1348 := &pb.StringType{}
	result712 := _t1348
	p.recordSpan(int(span_start711), "StringType")
	return result712
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1349 := &pb.IntType{}
	result714 := _t1349
	p.recordSpan(int(span_start713), "IntType")
	return result714
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1350 := &pb.FloatType{}
	result716 := _t1350
	p.recordSpan(int(span_start715), "FloatType")
	return result716
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1351 := &pb.UInt128Type{}
	result718 := _t1351
	p.recordSpan(int(span_start717), "UInt128Type")
	return result718
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start719 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1352 := &pb.Int128Type{}
	result720 := _t1352
	p.recordSpan(int(span_start719), "Int128Type")
	return result720
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start721 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1353 := &pb.DateType{}
	result722 := _t1353
	p.recordSpan(int(span_start721), "DateType")
	return result722
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start723 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1354 := &pb.DateTimeType{}
	result724 := _t1354
	p.recordSpan(int(span_start723), "DateTimeType")
	return result724
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start725 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1355 := &pb.MissingType{}
	result726 := _t1355
	p.recordSpan(int(span_start725), "MissingType")
	return result726
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start729 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int727 := p.consumeTerminal("INT").Value.i64
	int_3728 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1356 := &pb.DecimalType{Precision: int32(int727), Scale: int32(int_3728)}
	result730 := _t1356
	p.recordSpan(int(span_start729), "DecimalType")
	return result730
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1357 := &pb.BooleanType{}
	result732 := _t1357
	p.recordSpan(int(span_start731), "BooleanType")
	return result732
}

func (p *Parser) parse_int32_type() *pb.Int32Type {
	span_start733 := int64(p.spanStart())
	p.consumeLiteral("INT32")
	_t1358 := &pb.Int32Type{}
	result734 := _t1358
	p.recordSpan(int(span_start733), "Int32Type")
	return result734
}

func (p *Parser) parse_float32_type() *pb.Float32Type {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("FLOAT32")
	_t1359 := &pb.Float32Type{}
	result736 := _t1359
	p.recordSpan(int(span_start735), "Float32Type")
	return result736
}

func (p *Parser) parse_uint32_type() *pb.UInt32Type {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("UINT32")
	_t1360 := &pb.UInt32Type{}
	result738 := _t1360
	p.recordSpan(int(span_start737), "UInt32Type")
	return result738
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs739 := []*pb.Binding{}
	cond740 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond740 {
		_t1361 := p.parse_binding()
		item741 := _t1361
		xs739 = append(xs739, item741)
		cond740 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings742 := xs739
	return bindings742
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start757 := int64(p.spanStart())
	var _t1362 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1363 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1363 = 0
		} else {
			var _t1364 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1364 = 11
			} else {
				var _t1365 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1365 = 3
				} else {
					var _t1366 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1366 = 10
					} else {
						var _t1367 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1367 = 9
						} else {
							var _t1368 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1368 = 5
							} else {
								var _t1369 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1369 = 6
								} else {
									var _t1370 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1370 = 7
									} else {
										var _t1371 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1371 = 1
										} else {
											var _t1372 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1372 = 2
											} else {
												var _t1373 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1373 = 12
												} else {
													var _t1374 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1374 = 8
													} else {
														var _t1375 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1375 = 4
														} else {
															var _t1376 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1376 = 10
															} else {
																var _t1377 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1377 = 10
																} else {
																	var _t1378 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1378 = 10
																	} else {
																		var _t1379 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1379 = 10
																		} else {
																			var _t1380 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1380 = 10
																			} else {
																				var _t1381 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1381 = 10
																				} else {
																					var _t1382 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1382 = 10
																					} else {
																						var _t1383 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1383 = 10
																						} else {
																							var _t1384 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1384 = 10
																							} else {
																								_t1384 = -1
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
																_t1376 = _t1377
															}
															_t1375 = _t1376
														}
														_t1374 = _t1375
													}
													_t1373 = _t1374
												}
												_t1372 = _t1373
											}
											_t1371 = _t1372
										}
										_t1370 = _t1371
									}
									_t1369 = _t1370
								}
								_t1368 = _t1369
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
	} else {
		_t1362 = -1
	}
	prediction743 := _t1362
	var _t1385 *pb.Formula
	if prediction743 == 12 {
		_t1386 := p.parse_cast()
		cast756 := _t1386
		_t1387 := &pb.Formula{}
		_t1387.FormulaType = &pb.Formula_Cast{Cast: cast756}
		_t1385 = _t1387
	} else {
		var _t1388 *pb.Formula
		if prediction743 == 11 {
			_t1389 := p.parse_rel_atom()
			rel_atom755 := _t1389
			_t1390 := &pb.Formula{}
			_t1390.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom755}
			_t1388 = _t1390
		} else {
			var _t1391 *pb.Formula
			if prediction743 == 10 {
				_t1392 := p.parse_primitive()
				primitive754 := _t1392
				_t1393 := &pb.Formula{}
				_t1393.FormulaType = &pb.Formula_Primitive{Primitive: primitive754}
				_t1391 = _t1393
			} else {
				var _t1394 *pb.Formula
				if prediction743 == 9 {
					_t1395 := p.parse_pragma()
					pragma753 := _t1395
					_t1396 := &pb.Formula{}
					_t1396.FormulaType = &pb.Formula_Pragma{Pragma: pragma753}
					_t1394 = _t1396
				} else {
					var _t1397 *pb.Formula
					if prediction743 == 8 {
						_t1398 := p.parse_atom()
						atom752 := _t1398
						_t1399 := &pb.Formula{}
						_t1399.FormulaType = &pb.Formula_Atom{Atom: atom752}
						_t1397 = _t1399
					} else {
						var _t1400 *pb.Formula
						if prediction743 == 7 {
							_t1401 := p.parse_ffi()
							ffi751 := _t1401
							_t1402 := &pb.Formula{}
							_t1402.FormulaType = &pb.Formula_Ffi{Ffi: ffi751}
							_t1400 = _t1402
						} else {
							var _t1403 *pb.Formula
							if prediction743 == 6 {
								_t1404 := p.parse_not()
								not750 := _t1404
								_t1405 := &pb.Formula{}
								_t1405.FormulaType = &pb.Formula_Not{Not: not750}
								_t1403 = _t1405
							} else {
								var _t1406 *pb.Formula
								if prediction743 == 5 {
									_t1407 := p.parse_disjunction()
									disjunction749 := _t1407
									_t1408 := &pb.Formula{}
									_t1408.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction749}
									_t1406 = _t1408
								} else {
									var _t1409 *pb.Formula
									if prediction743 == 4 {
										_t1410 := p.parse_conjunction()
										conjunction748 := _t1410
										_t1411 := &pb.Formula{}
										_t1411.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction748}
										_t1409 = _t1411
									} else {
										var _t1412 *pb.Formula
										if prediction743 == 3 {
											_t1413 := p.parse_reduce()
											reduce747 := _t1413
											_t1414 := &pb.Formula{}
											_t1414.FormulaType = &pb.Formula_Reduce{Reduce: reduce747}
											_t1412 = _t1414
										} else {
											var _t1415 *pb.Formula
											if prediction743 == 2 {
												_t1416 := p.parse_exists()
												exists746 := _t1416
												_t1417 := &pb.Formula{}
												_t1417.FormulaType = &pb.Formula_Exists{Exists: exists746}
												_t1415 = _t1417
											} else {
												var _t1418 *pb.Formula
												if prediction743 == 1 {
													_t1419 := p.parse_false()
													false745 := _t1419
													_t1420 := &pb.Formula{}
													_t1420.FormulaType = &pb.Formula_Disjunction{Disjunction: false745}
													_t1418 = _t1420
												} else {
													var _t1421 *pb.Formula
													if prediction743 == 0 {
														_t1422 := p.parse_true()
														true744 := _t1422
														_t1423 := &pb.Formula{}
														_t1423.FormulaType = &pb.Formula_Conjunction{Conjunction: true744}
														_t1421 = _t1423
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1388 = _t1391
		}
		_t1385 = _t1388
	}
	result758 := _t1385
	p.recordSpan(int(span_start757), "Formula")
	return result758
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1424 := &pb.Conjunction{Args: []*pb.Formula{}}
	result760 := _t1424
	p.recordSpan(int(span_start759), "Conjunction")
	return result760
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1425 := &pb.Disjunction{Args: []*pb.Formula{}}
	result762 := _t1425
	p.recordSpan(int(span_start761), "Disjunction")
	return result762
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start765 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1426 := p.parse_bindings()
	bindings763 := _t1426
	_t1427 := p.parse_formula()
	formula764 := _t1427
	p.consumeLiteral(")")
	_t1428 := &pb.Abstraction{Vars: listConcat(bindings763[0].([]*pb.Binding), bindings763[1].([]*pb.Binding)), Value: formula764}
	_t1429 := &pb.Exists{Body: _t1428}
	result766 := _t1429
	p.recordSpan(int(span_start765), "Exists")
	return result766
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start770 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1430 := p.parse_abstraction()
	abstraction767 := _t1430
	_t1431 := p.parse_abstraction()
	abstraction_3768 := _t1431
	_t1432 := p.parse_terms()
	terms769 := _t1432
	p.consumeLiteral(")")
	_t1433 := &pb.Reduce{Op: abstraction767, Body: abstraction_3768, Terms: terms769}
	result771 := _t1433
	p.recordSpan(int(span_start770), "Reduce")
	return result771
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs772 := []*pb.Term{}
	cond773 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond773 {
		_t1434 := p.parse_term()
		item774 := _t1434
		xs772 = append(xs772, item774)
		cond773 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms775 := xs772
	p.consumeLiteral(")")
	return terms775
}

func (p *Parser) parse_term() *pb.Term {
	span_start779 := int64(p.spanStart())
	var _t1435 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1435 = 1
	} else {
		var _t1436 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1436 = 1
		} else {
			var _t1437 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1437 = 1
			} else {
				var _t1438 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1438 = 1
				} else {
					var _t1439 int64
					if p.matchLookaheadTerminal("UINT32", 0) {
						_t1439 = 1
					} else {
						var _t1440 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1440 = 1
						} else {
							var _t1441 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1441 = 0
							} else {
								var _t1442 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1442 = 1
								} else {
									var _t1443 int64
									if p.matchLookaheadTerminal("INT32", 0) {
										_t1443 = 1
									} else {
										var _t1444 int64
										if p.matchLookaheadTerminal("INT128", 0) {
											_t1444 = 1
										} else {
											var _t1445 int64
											if p.matchLookaheadTerminal("INT", 0) {
												_t1445 = 1
											} else {
												var _t1446 int64
												if p.matchLookaheadTerminal("FLOAT32", 0) {
													_t1446 = 1
												} else {
													var _t1447 int64
													if p.matchLookaheadTerminal("FLOAT", 0) {
														_t1447 = 1
													} else {
														var _t1448 int64
														if p.matchLookaheadTerminal("DECIMAL", 0) {
															_t1448 = 1
														} else {
															_t1448 = -1
														}
														_t1447 = _t1448
													}
													_t1446 = _t1447
												}
												_t1445 = _t1446
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
				}
				_t1437 = _t1438
			}
			_t1436 = _t1437
		}
		_t1435 = _t1436
	}
	prediction776 := _t1435
	var _t1449 *pb.Term
	if prediction776 == 1 {
		_t1450 := p.parse_constant()
		constant778 := _t1450
		_t1451 := &pb.Term{}
		_t1451.TermType = &pb.Term_Constant{Constant: constant778}
		_t1449 = _t1451
	} else {
		var _t1452 *pb.Term
		if prediction776 == 0 {
			_t1453 := p.parse_var()
			var777 := _t1453
			_t1454 := &pb.Term{}
			_t1454.TermType = &pb.Term_Var{Var: var777}
			_t1452 = _t1454
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1449 = _t1452
	}
	result780 := _t1449
	p.recordSpan(int(span_start779), "Term")
	return result780
}

func (p *Parser) parse_var() *pb.Var {
	span_start782 := int64(p.spanStart())
	symbol781 := p.consumeTerminal("SYMBOL").Value.str
	_t1455 := &pb.Var{Name: symbol781}
	result783 := _t1455
	p.recordSpan(int(span_start782), "Var")
	return result783
}

func (p *Parser) parse_constant() *pb.Value {
	span_start785 := int64(p.spanStart())
	_t1456 := p.parse_value()
	value784 := _t1456
	result786 := value784
	p.recordSpan(int(span_start785), "Value")
	return result786
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start791 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs787 := []*pb.Formula{}
	cond788 := p.matchLookaheadLiteral("(", 0)
	for cond788 {
		_t1457 := p.parse_formula()
		item789 := _t1457
		xs787 = append(xs787, item789)
		cond788 = p.matchLookaheadLiteral("(", 0)
	}
	formulas790 := xs787
	p.consumeLiteral(")")
	_t1458 := &pb.Conjunction{Args: formulas790}
	result792 := _t1458
	p.recordSpan(int(span_start791), "Conjunction")
	return result792
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs793 := []*pb.Formula{}
	cond794 := p.matchLookaheadLiteral("(", 0)
	for cond794 {
		_t1459 := p.parse_formula()
		item795 := _t1459
		xs793 = append(xs793, item795)
		cond794 = p.matchLookaheadLiteral("(", 0)
	}
	formulas796 := xs793
	p.consumeLiteral(")")
	_t1460 := &pb.Disjunction{Args: formulas796}
	result798 := _t1460
	p.recordSpan(int(span_start797), "Disjunction")
	return result798
}

func (p *Parser) parse_not() *pb.Not {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1461 := p.parse_formula()
	formula799 := _t1461
	p.consumeLiteral(")")
	_t1462 := &pb.Not{Arg: formula799}
	result801 := _t1462
	p.recordSpan(int(span_start800), "Not")
	return result801
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1463 := p.parse_name()
	name802 := _t1463
	_t1464 := p.parse_ffi_args()
	ffi_args803 := _t1464
	_t1465 := p.parse_terms()
	terms804 := _t1465
	p.consumeLiteral(")")
	_t1466 := &pb.FFI{Name: name802, Args: ffi_args803, Terms: terms804}
	result806 := _t1466
	p.recordSpan(int(span_start805), "FFI")
	return result806
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol807 := p.consumeTerminal("SYMBOL").Value.str
	return symbol807
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs808 := []*pb.Abstraction{}
	cond809 := p.matchLookaheadLiteral("(", 0)
	for cond809 {
		_t1467 := p.parse_abstraction()
		item810 := _t1467
		xs808 = append(xs808, item810)
		cond809 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions811 := xs808
	p.consumeLiteral(")")
	return abstractions811
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start817 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1468 := p.parse_relation_id()
	relation_id812 := _t1468
	xs813 := []*pb.Term{}
	cond814 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond814 {
		_t1469 := p.parse_term()
		item815 := _t1469
		xs813 = append(xs813, item815)
		cond814 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms816 := xs813
	p.consumeLiteral(")")
	_t1470 := &pb.Atom{Name: relation_id812, Terms: terms816}
	result818 := _t1470
	p.recordSpan(int(span_start817), "Atom")
	return result818
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1471 := p.parse_name()
	name819 := _t1471
	xs820 := []*pb.Term{}
	cond821 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond821 {
		_t1472 := p.parse_term()
		item822 := _t1472
		xs820 = append(xs820, item822)
		cond821 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	terms823 := xs820
	p.consumeLiteral(")")
	_t1473 := &pb.Pragma{Name: name819, Terms: terms823}
	result825 := _t1473
	p.recordSpan(int(span_start824), "Pragma")
	return result825
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start841 := int64(p.spanStart())
	var _t1474 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1475 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1475 = 9
		} else {
			var _t1476 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1476 = 4
			} else {
				var _t1477 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1477 = 3
				} else {
					var _t1478 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1478 = 0
					} else {
						var _t1479 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1479 = 2
						} else {
							var _t1480 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1480 = 1
							} else {
								var _t1481 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1481 = 8
								} else {
									var _t1482 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1482 = 6
									} else {
										var _t1483 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1483 = 5
										} else {
											var _t1484 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1484 = 7
											} else {
												_t1484 = -1
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
					_t1477 = _t1478
				}
				_t1476 = _t1477
			}
			_t1475 = _t1476
		}
		_t1474 = _t1475
	} else {
		_t1474 = -1
	}
	prediction826 := _t1474
	var _t1485 *pb.Primitive
	if prediction826 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1486 := p.parse_name()
		name836 := _t1486
		xs837 := []*pb.RelTerm{}
		cond838 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
		for cond838 {
			_t1487 := p.parse_rel_term()
			item839 := _t1487
			xs837 = append(xs837, item839)
			cond838 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
		}
		rel_terms840 := xs837
		p.consumeLiteral(")")
		_t1488 := &pb.Primitive{Name: name836, Terms: rel_terms840}
		_t1485 = _t1488
	} else {
		var _t1489 *pb.Primitive
		if prediction826 == 8 {
			_t1490 := p.parse_divide()
			divide835 := _t1490
			_t1489 = divide835
		} else {
			var _t1491 *pb.Primitive
			if prediction826 == 7 {
				_t1492 := p.parse_multiply()
				multiply834 := _t1492
				_t1491 = multiply834
			} else {
				var _t1493 *pb.Primitive
				if prediction826 == 6 {
					_t1494 := p.parse_minus()
					minus833 := _t1494
					_t1493 = minus833
				} else {
					var _t1495 *pb.Primitive
					if prediction826 == 5 {
						_t1496 := p.parse_add()
						add832 := _t1496
						_t1495 = add832
					} else {
						var _t1497 *pb.Primitive
						if prediction826 == 4 {
							_t1498 := p.parse_gt_eq()
							gt_eq831 := _t1498
							_t1497 = gt_eq831
						} else {
							var _t1499 *pb.Primitive
							if prediction826 == 3 {
								_t1500 := p.parse_gt()
								gt830 := _t1500
								_t1499 = gt830
							} else {
								var _t1501 *pb.Primitive
								if prediction826 == 2 {
									_t1502 := p.parse_lt_eq()
									lt_eq829 := _t1502
									_t1501 = lt_eq829
								} else {
									var _t1503 *pb.Primitive
									if prediction826 == 1 {
										_t1504 := p.parse_lt()
										lt828 := _t1504
										_t1503 = lt828
									} else {
										var _t1505 *pb.Primitive
										if prediction826 == 0 {
											_t1506 := p.parse_eq()
											eq827 := _t1506
											_t1505 = eq827
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1503 = _t1505
									}
									_t1501 = _t1503
								}
								_t1499 = _t1501
							}
							_t1497 = _t1499
						}
						_t1495 = _t1497
					}
					_t1493 = _t1495
				}
				_t1491 = _t1493
			}
			_t1489 = _t1491
		}
		_t1485 = _t1489
	}
	result842 := _t1485
	p.recordSpan(int(span_start841), "Primitive")
	return result842
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start845 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1507 := p.parse_term()
	term843 := _t1507
	_t1508 := p.parse_term()
	term_3844 := _t1508
	p.consumeLiteral(")")
	_t1509 := &pb.RelTerm{}
	_t1509.RelTermType = &pb.RelTerm_Term{Term: term843}
	_t1510 := &pb.RelTerm{}
	_t1510.RelTermType = &pb.RelTerm_Term{Term: term_3844}
	_t1511 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1509, _t1510}}
	result846 := _t1511
	p.recordSpan(int(span_start845), "Primitive")
	return result846
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start849 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1512 := p.parse_term()
	term847 := _t1512
	_t1513 := p.parse_term()
	term_3848 := _t1513
	p.consumeLiteral(")")
	_t1514 := &pb.RelTerm{}
	_t1514.RelTermType = &pb.RelTerm_Term{Term: term847}
	_t1515 := &pb.RelTerm{}
	_t1515.RelTermType = &pb.RelTerm_Term{Term: term_3848}
	_t1516 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1514, _t1515}}
	result850 := _t1516
	p.recordSpan(int(span_start849), "Primitive")
	return result850
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1517 := p.parse_term()
	term851 := _t1517
	_t1518 := p.parse_term()
	term_3852 := _t1518
	p.consumeLiteral(")")
	_t1519 := &pb.RelTerm{}
	_t1519.RelTermType = &pb.RelTerm_Term{Term: term851}
	_t1520 := &pb.RelTerm{}
	_t1520.RelTermType = &pb.RelTerm_Term{Term: term_3852}
	_t1521 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1519, _t1520}}
	result854 := _t1521
	p.recordSpan(int(span_start853), "Primitive")
	return result854
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1522 := p.parse_term()
	term855 := _t1522
	_t1523 := p.parse_term()
	term_3856 := _t1523
	p.consumeLiteral(")")
	_t1524 := &pb.RelTerm{}
	_t1524.RelTermType = &pb.RelTerm_Term{Term: term855}
	_t1525 := &pb.RelTerm{}
	_t1525.RelTermType = &pb.RelTerm_Term{Term: term_3856}
	_t1526 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1524, _t1525}}
	result858 := _t1526
	p.recordSpan(int(span_start857), "Primitive")
	return result858
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1527 := p.parse_term()
	term859 := _t1527
	_t1528 := p.parse_term()
	term_3860 := _t1528
	p.consumeLiteral(")")
	_t1529 := &pb.RelTerm{}
	_t1529.RelTermType = &pb.RelTerm_Term{Term: term859}
	_t1530 := &pb.RelTerm{}
	_t1530.RelTermType = &pb.RelTerm_Term{Term: term_3860}
	_t1531 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1529, _t1530}}
	result862 := _t1531
	p.recordSpan(int(span_start861), "Primitive")
	return result862
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start866 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1532 := p.parse_term()
	term863 := _t1532
	_t1533 := p.parse_term()
	term_3864 := _t1533
	_t1534 := p.parse_term()
	term_4865 := _t1534
	p.consumeLiteral(")")
	_t1535 := &pb.RelTerm{}
	_t1535.RelTermType = &pb.RelTerm_Term{Term: term863}
	_t1536 := &pb.RelTerm{}
	_t1536.RelTermType = &pb.RelTerm_Term{Term: term_3864}
	_t1537 := &pb.RelTerm{}
	_t1537.RelTermType = &pb.RelTerm_Term{Term: term_4865}
	_t1538 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1535, _t1536, _t1537}}
	result867 := _t1538
	p.recordSpan(int(span_start866), "Primitive")
	return result867
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start871 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1539 := p.parse_term()
	term868 := _t1539
	_t1540 := p.parse_term()
	term_3869 := _t1540
	_t1541 := p.parse_term()
	term_4870 := _t1541
	p.consumeLiteral(")")
	_t1542 := &pb.RelTerm{}
	_t1542.RelTermType = &pb.RelTerm_Term{Term: term868}
	_t1543 := &pb.RelTerm{}
	_t1543.RelTermType = &pb.RelTerm_Term{Term: term_3869}
	_t1544 := &pb.RelTerm{}
	_t1544.RelTermType = &pb.RelTerm_Term{Term: term_4870}
	_t1545 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1542, _t1543, _t1544}}
	result872 := _t1545
	p.recordSpan(int(span_start871), "Primitive")
	return result872
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start876 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1546 := p.parse_term()
	term873 := _t1546
	_t1547 := p.parse_term()
	term_3874 := _t1547
	_t1548 := p.parse_term()
	term_4875 := _t1548
	p.consumeLiteral(")")
	_t1549 := &pb.RelTerm{}
	_t1549.RelTermType = &pb.RelTerm_Term{Term: term873}
	_t1550 := &pb.RelTerm{}
	_t1550.RelTermType = &pb.RelTerm_Term{Term: term_3874}
	_t1551 := &pb.RelTerm{}
	_t1551.RelTermType = &pb.RelTerm_Term{Term: term_4875}
	_t1552 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1549, _t1550, _t1551}}
	result877 := _t1552
	p.recordSpan(int(span_start876), "Primitive")
	return result877
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start881 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1553 := p.parse_term()
	term878 := _t1553
	_t1554 := p.parse_term()
	term_3879 := _t1554
	_t1555 := p.parse_term()
	term_4880 := _t1555
	p.consumeLiteral(")")
	_t1556 := &pb.RelTerm{}
	_t1556.RelTermType = &pb.RelTerm_Term{Term: term878}
	_t1557 := &pb.RelTerm{}
	_t1557.RelTermType = &pb.RelTerm_Term{Term: term_3879}
	_t1558 := &pb.RelTerm{}
	_t1558.RelTermType = &pb.RelTerm_Term{Term: term_4880}
	_t1559 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1556, _t1557, _t1558}}
	result882 := _t1559
	p.recordSpan(int(span_start881), "Primitive")
	return result882
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start886 := int64(p.spanStart())
	var _t1560 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1560 = 1
	} else {
		var _t1561 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1561 = 1
		} else {
			var _t1562 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1562 = 1
			} else {
				var _t1563 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1563 = 1
				} else {
					var _t1564 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1564 = 0
					} else {
						var _t1565 int64
						if p.matchLookaheadTerminal("UINT32", 0) {
							_t1565 = 1
						} else {
							var _t1566 int64
							if p.matchLookaheadTerminal("UINT128", 0) {
								_t1566 = 1
							} else {
								var _t1567 int64
								if p.matchLookaheadTerminal("SYMBOL", 0) {
									_t1567 = 1
								} else {
									var _t1568 int64
									if p.matchLookaheadTerminal("STRING", 0) {
										_t1568 = 1
									} else {
										var _t1569 int64
										if p.matchLookaheadTerminal("INT32", 0) {
											_t1569 = 1
										} else {
											var _t1570 int64
											if p.matchLookaheadTerminal("INT128", 0) {
												_t1570 = 1
											} else {
												var _t1571 int64
												if p.matchLookaheadTerminal("INT", 0) {
													_t1571 = 1
												} else {
													var _t1572 int64
													if p.matchLookaheadTerminal("FLOAT32", 0) {
														_t1572 = 1
													} else {
														var _t1573 int64
														if p.matchLookaheadTerminal("FLOAT", 0) {
															_t1573 = 1
														} else {
															var _t1574 int64
															if p.matchLookaheadTerminal("DECIMAL", 0) {
																_t1574 = 1
															} else {
																_t1574 = -1
															}
															_t1573 = _t1574
														}
														_t1572 = _t1573
													}
													_t1571 = _t1572
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
	prediction883 := _t1560
	var _t1575 *pb.RelTerm
	if prediction883 == 1 {
		_t1576 := p.parse_term()
		term885 := _t1576
		_t1577 := &pb.RelTerm{}
		_t1577.RelTermType = &pb.RelTerm_Term{Term: term885}
		_t1575 = _t1577
	} else {
		var _t1578 *pb.RelTerm
		if prediction883 == 0 {
			_t1579 := p.parse_specialized_value()
			specialized_value884 := _t1579
			_t1580 := &pb.RelTerm{}
			_t1580.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value884}
			_t1578 = _t1580
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1575 = _t1578
	}
	result887 := _t1575
	p.recordSpan(int(span_start886), "RelTerm")
	return result887
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start889 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1581 := p.parse_value()
	value888 := _t1581
	result890 := value888
	p.recordSpan(int(span_start889), "Value")
	return result890
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1582 := p.parse_name()
	name891 := _t1582
	xs892 := []*pb.RelTerm{}
	cond893 := ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond893 {
		_t1583 := p.parse_rel_term()
		item894 := _t1583
		xs892 = append(xs892, item894)
		cond893 = ((((((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	rel_terms895 := xs892
	p.consumeLiteral(")")
	_t1584 := &pb.RelAtom{Name: name891, Terms: rel_terms895}
	result897 := _t1584
	p.recordSpan(int(span_start896), "RelAtom")
	return result897
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1585 := p.parse_term()
	term898 := _t1585
	_t1586 := p.parse_term()
	term_3899 := _t1586
	p.consumeLiteral(")")
	_t1587 := &pb.Cast{Input: term898, Result: term_3899}
	result901 := _t1587
	p.recordSpan(int(span_start900), "Cast")
	return result901
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs902 := []*pb.Attribute{}
	cond903 := p.matchLookaheadLiteral("(", 0)
	for cond903 {
		_t1588 := p.parse_attribute()
		item904 := _t1588
		xs902 = append(xs902, item904)
		cond903 = p.matchLookaheadLiteral("(", 0)
	}
	attributes905 := xs902
	p.consumeLiteral(")")
	return attributes905
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start911 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1589 := p.parse_name()
	name906 := _t1589
	xs907 := []*pb.Value{}
	cond908 := ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	for cond908 {
		_t1590 := p.parse_value()
		item909 := _t1590
		xs907 = append(xs907, item909)
		cond908 = ((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("FLOAT32", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("INT32", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0)) || p.matchLookaheadTerminal("UINT32", 0))
	}
	values910 := xs907
	p.consumeLiteral(")")
	_t1591 := &pb.Attribute{Name: name906, Args: values910}
	result912 := _t1591
	p.recordSpan(int(span_start911), "Attribute")
	return result912
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start918 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs913 := []*pb.RelationId{}
	cond914 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond914 {
		_t1592 := p.parse_relation_id()
		item915 := _t1592
		xs913 = append(xs913, item915)
		cond914 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids916 := xs913
	_t1593 := p.parse_script()
	script917 := _t1593
	p.consumeLiteral(")")
	_t1594 := &pb.Algorithm{Global: relation_ids916, Body: script917}
	result919 := _t1594
	p.recordSpan(int(span_start918), "Algorithm")
	return result919
}

func (p *Parser) parse_script() *pb.Script {
	span_start924 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs920 := []*pb.Construct{}
	cond921 := p.matchLookaheadLiteral("(", 0)
	for cond921 {
		_t1595 := p.parse_construct()
		item922 := _t1595
		xs920 = append(xs920, item922)
		cond921 = p.matchLookaheadLiteral("(", 0)
	}
	constructs923 := xs920
	p.consumeLiteral(")")
	_t1596 := &pb.Script{Constructs: constructs923}
	result925 := _t1596
	p.recordSpan(int(span_start924), "Script")
	return result925
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start929 := int64(p.spanStart())
	var _t1597 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1598 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1598 = 1
		} else {
			var _t1599 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1599 = 1
			} else {
				var _t1600 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1600 = 1
				} else {
					var _t1601 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1601 = 0
					} else {
						var _t1602 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1602 = 1
						} else {
							var _t1603 int64
							if p.matchLookaheadLiteral("assign", 1) {
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
	} else {
		_t1597 = -1
	}
	prediction926 := _t1597
	var _t1604 *pb.Construct
	if prediction926 == 1 {
		_t1605 := p.parse_instruction()
		instruction928 := _t1605
		_t1606 := &pb.Construct{}
		_t1606.ConstructType = &pb.Construct_Instruction{Instruction: instruction928}
		_t1604 = _t1606
	} else {
		var _t1607 *pb.Construct
		if prediction926 == 0 {
			_t1608 := p.parse_loop()
			loop927 := _t1608
			_t1609 := &pb.Construct{}
			_t1609.ConstructType = &pb.Construct_Loop{Loop: loop927}
			_t1607 = _t1609
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1604 = _t1607
	}
	result930 := _t1604
	p.recordSpan(int(span_start929), "Construct")
	return result930
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start933 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1610 := p.parse_init()
	init931 := _t1610
	_t1611 := p.parse_script()
	script932 := _t1611
	p.consumeLiteral(")")
	_t1612 := &pb.Loop{Init: init931, Body: script932}
	result934 := _t1612
	p.recordSpan(int(span_start933), "Loop")
	return result934
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs935 := []*pb.Instruction{}
	cond936 := p.matchLookaheadLiteral("(", 0)
	for cond936 {
		_t1613 := p.parse_instruction()
		item937 := _t1613
		xs935 = append(xs935, item937)
		cond936 = p.matchLookaheadLiteral("(", 0)
	}
	instructions938 := xs935
	p.consumeLiteral(")")
	return instructions938
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start945 := int64(p.spanStart())
	var _t1614 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1615 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1615 = 1
		} else {
			var _t1616 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1616 = 4
			} else {
				var _t1617 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1617 = 3
				} else {
					var _t1618 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1618 = 2
					} else {
						var _t1619 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1619 = 0
						} else {
							_t1619 = -1
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
	} else {
		_t1614 = -1
	}
	prediction939 := _t1614
	var _t1620 *pb.Instruction
	if prediction939 == 4 {
		_t1621 := p.parse_monus_def()
		monus_def944 := _t1621
		_t1622 := &pb.Instruction{}
		_t1622.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def944}
		_t1620 = _t1622
	} else {
		var _t1623 *pb.Instruction
		if prediction939 == 3 {
			_t1624 := p.parse_monoid_def()
			monoid_def943 := _t1624
			_t1625 := &pb.Instruction{}
			_t1625.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def943}
			_t1623 = _t1625
		} else {
			var _t1626 *pb.Instruction
			if prediction939 == 2 {
				_t1627 := p.parse_break()
				break942 := _t1627
				_t1628 := &pb.Instruction{}
				_t1628.InstrType = &pb.Instruction_Break{Break: break942}
				_t1626 = _t1628
			} else {
				var _t1629 *pb.Instruction
				if prediction939 == 1 {
					_t1630 := p.parse_upsert()
					upsert941 := _t1630
					_t1631 := &pb.Instruction{}
					_t1631.InstrType = &pb.Instruction_Upsert{Upsert: upsert941}
					_t1629 = _t1631
				} else {
					var _t1632 *pb.Instruction
					if prediction939 == 0 {
						_t1633 := p.parse_assign()
						assign940 := _t1633
						_t1634 := &pb.Instruction{}
						_t1634.InstrType = &pb.Instruction_Assign{Assign: assign940}
						_t1632 = _t1634
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1629 = _t1632
				}
				_t1626 = _t1629
			}
			_t1623 = _t1626
		}
		_t1620 = _t1623
	}
	result946 := _t1620
	p.recordSpan(int(span_start945), "Instruction")
	return result946
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start950 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1635 := p.parse_relation_id()
	relation_id947 := _t1635
	_t1636 := p.parse_abstraction()
	abstraction948 := _t1636
	var _t1637 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1638 := p.parse_attrs()
		_t1637 = _t1638
	}
	attrs949 := _t1637
	p.consumeLiteral(")")
	_t1639 := attrs949
	if attrs949 == nil {
		_t1639 = []*pb.Attribute{}
	}
	_t1640 := &pb.Assign{Name: relation_id947, Body: abstraction948, Attrs: _t1639}
	result951 := _t1640
	p.recordSpan(int(span_start950), "Assign")
	return result951
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start955 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1641 := p.parse_relation_id()
	relation_id952 := _t1641
	_t1642 := p.parse_abstraction_with_arity()
	abstraction_with_arity953 := _t1642
	var _t1643 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1644 := p.parse_attrs()
		_t1643 = _t1644
	}
	attrs954 := _t1643
	p.consumeLiteral(")")
	_t1645 := attrs954
	if attrs954 == nil {
		_t1645 = []*pb.Attribute{}
	}
	_t1646 := &pb.Upsert{Name: relation_id952, Body: abstraction_with_arity953[0].(*pb.Abstraction), Attrs: _t1645, ValueArity: abstraction_with_arity953[1].(int64)}
	result956 := _t1646
	p.recordSpan(int(span_start955), "Upsert")
	return result956
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1647 := p.parse_bindings()
	bindings957 := _t1647
	_t1648 := p.parse_formula()
	formula958 := _t1648
	p.consumeLiteral(")")
	_t1649 := &pb.Abstraction{Vars: listConcat(bindings957[0].([]*pb.Binding), bindings957[1].([]*pb.Binding)), Value: formula958}
	return []interface{}{_t1649, int64(len(bindings957[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start962 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1650 := p.parse_relation_id()
	relation_id959 := _t1650
	_t1651 := p.parse_abstraction()
	abstraction960 := _t1651
	var _t1652 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1653 := p.parse_attrs()
		_t1652 = _t1653
	}
	attrs961 := _t1652
	p.consumeLiteral(")")
	_t1654 := attrs961
	if attrs961 == nil {
		_t1654 = []*pb.Attribute{}
	}
	_t1655 := &pb.Break{Name: relation_id959, Body: abstraction960, Attrs: _t1654}
	result963 := _t1655
	p.recordSpan(int(span_start962), "Break")
	return result963
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1656 := p.parse_monoid()
	monoid964 := _t1656
	_t1657 := p.parse_relation_id()
	relation_id965 := _t1657
	_t1658 := p.parse_abstraction_with_arity()
	abstraction_with_arity966 := _t1658
	var _t1659 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1660 := p.parse_attrs()
		_t1659 = _t1660
	}
	attrs967 := _t1659
	p.consumeLiteral(")")
	_t1661 := attrs967
	if attrs967 == nil {
		_t1661 = []*pb.Attribute{}
	}
	_t1662 := &pb.MonoidDef{Monoid: monoid964, Name: relation_id965, Body: abstraction_with_arity966[0].(*pb.Abstraction), Attrs: _t1661, ValueArity: abstraction_with_arity966[1].(int64)}
	result969 := _t1662
	p.recordSpan(int(span_start968), "MonoidDef")
	return result969
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start975 := int64(p.spanStart())
	var _t1663 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1664 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1664 = 3
		} else {
			var _t1665 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1665 = 0
			} else {
				var _t1666 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1666 = 1
				} else {
					var _t1667 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1667 = 2
					} else {
						_t1667 = -1
					}
					_t1666 = _t1667
				}
				_t1665 = _t1666
			}
			_t1664 = _t1665
		}
		_t1663 = _t1664
	} else {
		_t1663 = -1
	}
	prediction970 := _t1663
	var _t1668 *pb.Monoid
	if prediction970 == 3 {
		_t1669 := p.parse_sum_monoid()
		sum_monoid974 := _t1669
		_t1670 := &pb.Monoid{}
		_t1670.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid974}
		_t1668 = _t1670
	} else {
		var _t1671 *pb.Monoid
		if prediction970 == 2 {
			_t1672 := p.parse_max_monoid()
			max_monoid973 := _t1672
			_t1673 := &pb.Monoid{}
			_t1673.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid973}
			_t1671 = _t1673
		} else {
			var _t1674 *pb.Monoid
			if prediction970 == 1 {
				_t1675 := p.parse_min_monoid()
				min_monoid972 := _t1675
				_t1676 := &pb.Monoid{}
				_t1676.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid972}
				_t1674 = _t1676
			} else {
				var _t1677 *pb.Monoid
				if prediction970 == 0 {
					_t1678 := p.parse_or_monoid()
					or_monoid971 := _t1678
					_t1679 := &pb.Monoid{}
					_t1679.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid971}
					_t1677 = _t1679
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1674 = _t1677
			}
			_t1671 = _t1674
		}
		_t1668 = _t1671
	}
	result976 := _t1668
	p.recordSpan(int(span_start975), "Monoid")
	return result976
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start977 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1680 := &pb.OrMonoid{}
	result978 := _t1680
	p.recordSpan(int(span_start977), "OrMonoid")
	return result978
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1681 := p.parse_type()
	type979 := _t1681
	p.consumeLiteral(")")
	_t1682 := &pb.MinMonoid{Type: type979}
	result981 := _t1682
	p.recordSpan(int(span_start980), "MinMonoid")
	return result981
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start983 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1683 := p.parse_type()
	type982 := _t1683
	p.consumeLiteral(")")
	_t1684 := &pb.MaxMonoid{Type: type982}
	result984 := _t1684
	p.recordSpan(int(span_start983), "MaxMonoid")
	return result984
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1685 := p.parse_type()
	type985 := _t1685
	p.consumeLiteral(")")
	_t1686 := &pb.SumMonoid{Type: type985}
	result987 := _t1686
	p.recordSpan(int(span_start986), "SumMonoid")
	return result987
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start992 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1687 := p.parse_monoid()
	monoid988 := _t1687
	_t1688 := p.parse_relation_id()
	relation_id989 := _t1688
	_t1689 := p.parse_abstraction_with_arity()
	abstraction_with_arity990 := _t1689
	var _t1690 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1691 := p.parse_attrs()
		_t1690 = _t1691
	}
	attrs991 := _t1690
	p.consumeLiteral(")")
	_t1692 := attrs991
	if attrs991 == nil {
		_t1692 = []*pb.Attribute{}
	}
	_t1693 := &pb.MonusDef{Monoid: monoid988, Name: relation_id989, Body: abstraction_with_arity990[0].(*pb.Abstraction), Attrs: _t1692, ValueArity: abstraction_with_arity990[1].(int64)}
	result993 := _t1693
	p.recordSpan(int(span_start992), "MonusDef")
	return result993
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start998 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1694 := p.parse_relation_id()
	relation_id994 := _t1694
	_t1695 := p.parse_abstraction()
	abstraction995 := _t1695
	_t1696 := p.parse_functional_dependency_keys()
	functional_dependency_keys996 := _t1696
	_t1697 := p.parse_functional_dependency_values()
	functional_dependency_values997 := _t1697
	p.consumeLiteral(")")
	_t1698 := &pb.FunctionalDependency{Guard: abstraction995, Keys: functional_dependency_keys996, Values: functional_dependency_values997}
	_t1699 := &pb.Constraint{Name: relation_id994}
	_t1699.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1698}
	result999 := _t1699
	p.recordSpan(int(span_start998), "Constraint")
	return result999
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1000 := []*pb.Var{}
	cond1001 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1001 {
		_t1700 := p.parse_var()
		item1002 := _t1700
		xs1000 = append(xs1000, item1002)
		cond1001 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1003 := xs1000
	p.consumeLiteral(")")
	return vars1003
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1004 := []*pb.Var{}
	cond1005 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1005 {
		_t1701 := p.parse_var()
		item1006 := _t1701
		xs1004 = append(xs1004, item1006)
		cond1005 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1007 := xs1004
	p.consumeLiteral(")")
	return vars1007
}

func (p *Parser) parse_data() *pb.Data {
	span_start1012 := int64(p.spanStart())
	var _t1702 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1703 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1703 = 0
		} else {
			var _t1704 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1704 = 2
			} else {
				var _t1705 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1705 = 1
				} else {
					_t1705 = -1
				}
				_t1704 = _t1705
			}
			_t1703 = _t1704
		}
		_t1702 = _t1703
	} else {
		_t1702 = -1
	}
	prediction1008 := _t1702
	var _t1706 *pb.Data
	if prediction1008 == 2 {
		_t1707 := p.parse_csv_data()
		csv_data1011 := _t1707
		_t1708 := &pb.Data{}
		_t1708.DataType = &pb.Data_CsvData{CsvData: csv_data1011}
		_t1706 = _t1708
	} else {
		var _t1709 *pb.Data
		if prediction1008 == 1 {
			_t1710 := p.parse_betree_relation()
			betree_relation1010 := _t1710
			_t1711 := &pb.Data{}
			_t1711.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1010}
			_t1709 = _t1711
		} else {
			var _t1712 *pb.Data
			if prediction1008 == 0 {
				_t1713 := p.parse_edb()
				edb1009 := _t1713
				_t1714 := &pb.Data{}
				_t1714.DataType = &pb.Data_Edb{Edb: edb1009}
				_t1712 = _t1714
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1709 = _t1712
		}
		_t1706 = _t1709
	}
	result1013 := _t1706
	p.recordSpan(int(span_start1012), "Data")
	return result1013
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start1017 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1715 := p.parse_relation_id()
	relation_id1014 := _t1715
	_t1716 := p.parse_edb_path()
	edb_path1015 := _t1716
	_t1717 := p.parse_edb_types()
	edb_types1016 := _t1717
	p.consumeLiteral(")")
	_t1718 := &pb.EDB{TargetId: relation_id1014, Path: edb_path1015, Types: edb_types1016}
	result1018 := _t1718
	p.recordSpan(int(span_start1017), "EDB")
	return result1018
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs1019 := []string{}
	cond1020 := p.matchLookaheadTerminal("STRING", 0)
	for cond1020 {
		item1021 := p.consumeTerminal("STRING").Value.str
		xs1019 = append(xs1019, item1021)
		cond1020 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1022 := xs1019
	p.consumeLiteral("]")
	return strings1022
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1023 := []*pb.Type{}
	cond1024 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1024 {
		_t1719 := p.parse_type()
		item1025 := _t1719
		xs1023 = append(xs1023, item1025)
		cond1024 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1026 := xs1023
	p.consumeLiteral("]")
	return types1026
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1029 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1720 := p.parse_relation_id()
	relation_id1027 := _t1720
	_t1721 := p.parse_betree_info()
	betree_info1028 := _t1721
	p.consumeLiteral(")")
	_t1722 := &pb.BeTreeRelation{Name: relation_id1027, RelationInfo: betree_info1028}
	result1030 := _t1722
	p.recordSpan(int(span_start1029), "BeTreeRelation")
	return result1030
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1723 := p.parse_betree_info_key_types()
	betree_info_key_types1031 := _t1723
	_t1724 := p.parse_betree_info_value_types()
	betree_info_value_types1032 := _t1724
	_t1725 := p.parse_config_dict()
	config_dict1033 := _t1725
	p.consumeLiteral(")")
	_t1726 := p.construct_betree_info(betree_info_key_types1031, betree_info_value_types1032, config_dict1033)
	result1035 := _t1726
	p.recordSpan(int(span_start1034), "BeTreeInfo")
	return result1035
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1036 := []*pb.Type{}
	cond1037 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1037 {
		_t1727 := p.parse_type()
		item1038 := _t1727
		xs1036 = append(xs1036, item1038)
		cond1037 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1039 := xs1036
	p.consumeLiteral(")")
	return types1039
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1040 := []*pb.Type{}
	cond1041 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1041 {
		_t1728 := p.parse_type()
		item1042 := _t1728
		xs1040 = append(xs1040, item1042)
		cond1041 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1043 := xs1040
	p.consumeLiteral(")")
	return types1043
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1048 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1729 := p.parse_csvlocator()
	csvlocator1044 := _t1729
	_t1730 := p.parse_csv_config()
	csv_config1045 := _t1730
	_t1731 := p.parse_gnf_columns()
	gnf_columns1046 := _t1731
	_t1732 := p.parse_csv_asof()
	csv_asof1047 := _t1732
	p.consumeLiteral(")")
	_t1733 := &pb.CSVData{Locator: csvlocator1044, Config: csv_config1045, Columns: gnf_columns1046, Asof: csv_asof1047}
	result1049 := _t1733
	p.recordSpan(int(span_start1048), "CSVData")
	return result1049
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1052 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1734 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1735 := p.parse_csv_locator_paths()
		_t1734 = _t1735
	}
	csv_locator_paths1050 := _t1734
	var _t1736 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1737 := p.parse_csv_locator_inline_data()
		_t1736 = ptr(_t1737)
	}
	csv_locator_inline_data1051 := _t1736
	p.consumeLiteral(")")
	_t1738 := csv_locator_paths1050
	if csv_locator_paths1050 == nil {
		_t1738 = []string{}
	}
	_t1739 := &pb.CSVLocator{Paths: _t1738, InlineData: []byte(deref(csv_locator_inline_data1051, ""))}
	result1053 := _t1739
	p.recordSpan(int(span_start1052), "CSVLocator")
	return result1053
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1054 := []string{}
	cond1055 := p.matchLookaheadTerminal("STRING", 0)
	for cond1055 {
		item1056 := p.consumeTerminal("STRING").Value.str
		xs1054 = append(xs1054, item1056)
		cond1055 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1057 := xs1054
	p.consumeLiteral(")")
	return strings1057
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1058 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1058
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1060 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1740 := p.parse_config_dict()
	config_dict1059 := _t1740
	p.consumeLiteral(")")
	_t1741 := p.construct_csv_config(config_dict1059)
	result1061 := _t1741
	p.recordSpan(int(span_start1060), "CSVConfig")
	return result1061
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1062 := []*pb.GNFColumn{}
	cond1063 := p.matchLookaheadLiteral("(", 0)
	for cond1063 {
		_t1742 := p.parse_gnf_column()
		item1064 := _t1742
		xs1062 = append(xs1062, item1064)
		cond1063 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1065 := xs1062
	p.consumeLiteral(")")
	return gnf_columns1065
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1072 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1743 := p.parse_gnf_column_path()
	gnf_column_path1066 := _t1743
	var _t1744 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1745 := p.parse_relation_id()
		_t1744 = _t1745
	}
	relation_id1067 := _t1744
	p.consumeLiteral("[")
	xs1068 := []*pb.Type{}
	cond1069 := (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1069 {
		_t1746 := p.parse_type()
		item1070 := _t1746
		xs1068 = append(xs1068, item1070)
		cond1069 = (((((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("FLOAT32", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("INT32", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UINT32", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1071 := xs1068
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1747 := &pb.GNFColumn{ColumnPath: gnf_column_path1066, TargetId: relation_id1067, Types: types1071}
	result1073 := _t1747
	p.recordSpan(int(span_start1072), "GNFColumn")
	return result1073
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1748 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1748 = 1
	} else {
		var _t1749 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1749 = 0
		} else {
			_t1749 = -1
		}
		_t1748 = _t1749
	}
	prediction1074 := _t1748
	var _t1750 []string
	if prediction1074 == 1 {
		p.consumeLiteral("[")
		xs1076 := []string{}
		cond1077 := p.matchLookaheadTerminal("STRING", 0)
		for cond1077 {
			item1078 := p.consumeTerminal("STRING").Value.str
			xs1076 = append(xs1076, item1078)
			cond1077 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1079 := xs1076
		p.consumeLiteral("]")
		_t1750 = strings1079
	} else {
		var _t1751 []string
		if prediction1074 == 0 {
			string1075 := p.consumeTerminal("STRING").Value.str
			_ = string1075
			_t1751 = []string{string1075}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1750 = _t1751
	}
	return _t1750
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1080 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1080
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1752 := p.parse_fragment_id()
	fragment_id1081 := _t1752
	p.consumeLiteral(")")
	_t1753 := &pb.Undefine{FragmentId: fragment_id1081}
	result1083 := _t1753
	p.recordSpan(int(span_start1082), "Undefine")
	return result1083
}

func (p *Parser) parse_context() *pb.Context {
	span_start1088 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1084 := []*pb.RelationId{}
	cond1085 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1085 {
		_t1754 := p.parse_relation_id()
		item1086 := _t1754
		xs1084 = append(xs1084, item1086)
		cond1085 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1087 := xs1084
	p.consumeLiteral(")")
	_t1755 := &pb.Context{Relations: relation_ids1087}
	result1089 := _t1755
	p.recordSpan(int(span_start1088), "Context")
	return result1089
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1094 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1090 := []*pb.SnapshotMapping{}
	cond1091 := p.matchLookaheadLiteral("[", 0)
	for cond1091 {
		_t1756 := p.parse_snapshot_mapping()
		item1092 := _t1756
		xs1090 = append(xs1090, item1092)
		cond1091 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1093 := xs1090
	p.consumeLiteral(")")
	_t1757 := &pb.Snapshot{Mappings: snapshot_mappings1093}
	result1095 := _t1757
	p.recordSpan(int(span_start1094), "Snapshot")
	return result1095
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1098 := int64(p.spanStart())
	_t1758 := p.parse_edb_path()
	edb_path1096 := _t1758
	_t1759 := p.parse_relation_id()
	relation_id1097 := _t1759
	_t1760 := &pb.SnapshotMapping{DestinationPath: edb_path1096, SourceRelation: relation_id1097}
	result1099 := _t1760
	p.recordSpan(int(span_start1098), "SnapshotMapping")
	return result1099
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1100 := []*pb.Read{}
	cond1101 := p.matchLookaheadLiteral("(", 0)
	for cond1101 {
		_t1761 := p.parse_read()
		item1102 := _t1761
		xs1100 = append(xs1100, item1102)
		cond1101 = p.matchLookaheadLiteral("(", 0)
	}
	reads1103 := xs1100
	p.consumeLiteral(")")
	return reads1103
}

func (p *Parser) parse_read() *pb.Read {
	span_start1110 := int64(p.spanStart())
	var _t1762 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1763 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1763 = 2
		} else {
			var _t1764 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1764 = 1
			} else {
				var _t1765 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1765 = 4
				} else {
					var _t1766 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1766 = 0
					} else {
						var _t1767 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1767 = 3
						} else {
							_t1767 = -1
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
	} else {
		_t1762 = -1
	}
	prediction1104 := _t1762
	var _t1768 *pb.Read
	if prediction1104 == 4 {
		_t1769 := p.parse_export()
		export1109 := _t1769
		_t1770 := &pb.Read{}
		_t1770.ReadType = &pb.Read_Export{Export: export1109}
		_t1768 = _t1770
	} else {
		var _t1771 *pb.Read
		if prediction1104 == 3 {
			_t1772 := p.parse_abort()
			abort1108 := _t1772
			_t1773 := &pb.Read{}
			_t1773.ReadType = &pb.Read_Abort{Abort: abort1108}
			_t1771 = _t1773
		} else {
			var _t1774 *pb.Read
			if prediction1104 == 2 {
				_t1775 := p.parse_what_if()
				what_if1107 := _t1775
				_t1776 := &pb.Read{}
				_t1776.ReadType = &pb.Read_WhatIf{WhatIf: what_if1107}
				_t1774 = _t1776
			} else {
				var _t1777 *pb.Read
				if prediction1104 == 1 {
					_t1778 := p.parse_output()
					output1106 := _t1778
					_t1779 := &pb.Read{}
					_t1779.ReadType = &pb.Read_Output{Output: output1106}
					_t1777 = _t1779
				} else {
					var _t1780 *pb.Read
					if prediction1104 == 0 {
						_t1781 := p.parse_demand()
						demand1105 := _t1781
						_t1782 := &pb.Read{}
						_t1782.ReadType = &pb.Read_Demand{Demand: demand1105}
						_t1780 = _t1782
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1777 = _t1780
				}
				_t1774 = _t1777
			}
			_t1771 = _t1774
		}
		_t1768 = _t1771
	}
	result1111 := _t1768
	p.recordSpan(int(span_start1110), "Read")
	return result1111
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1113 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1783 := p.parse_relation_id()
	relation_id1112 := _t1783
	p.consumeLiteral(")")
	_t1784 := &pb.Demand{RelationId: relation_id1112}
	result1114 := _t1784
	p.recordSpan(int(span_start1113), "Demand")
	return result1114
}

func (p *Parser) parse_output() *pb.Output {
	span_start1117 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1785 := p.parse_name()
	name1115 := _t1785
	_t1786 := p.parse_relation_id()
	relation_id1116 := _t1786
	p.consumeLiteral(")")
	_t1787 := &pb.Output{Name: name1115, RelationId: relation_id1116}
	result1118 := _t1787
	p.recordSpan(int(span_start1117), "Output")
	return result1118
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1121 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1788 := p.parse_name()
	name1119 := _t1788
	_t1789 := p.parse_epoch()
	epoch1120 := _t1789
	p.consumeLiteral(")")
	_t1790 := &pb.WhatIf{Branch: name1119, Epoch: epoch1120}
	result1122 := _t1790
	p.recordSpan(int(span_start1121), "WhatIf")
	return result1122
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1125 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1791 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1792 := p.parse_name()
		_t1791 = ptr(_t1792)
	}
	name1123 := _t1791
	_t1793 := p.parse_relation_id()
	relation_id1124 := _t1793
	p.consumeLiteral(")")
	_t1794 := &pb.Abort{Name: deref(name1123, "abort"), RelationId: relation_id1124}
	result1126 := _t1794
	p.recordSpan(int(span_start1125), "Abort")
	return result1126
}

func (p *Parser) parse_export() *pb.Export {
	span_start1128 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1795 := p.parse_export_csv_config()
	export_csv_config1127 := _t1795
	p.consumeLiteral(")")
	_t1796 := &pb.Export{}
	_t1796.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1127}
	result1129 := _t1796
	p.recordSpan(int(span_start1128), "Export")
	return result1129
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1137 := int64(p.spanStart())
	var _t1797 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1798 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1798 = 0
		} else {
			var _t1799 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1799 = 1
			} else {
				_t1799 = -1
			}
			_t1798 = _t1799
		}
		_t1797 = _t1798
	} else {
		_t1797 = -1
	}
	prediction1130 := _t1797
	var _t1800 *pb.ExportCSVConfig
	if prediction1130 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1801 := p.parse_export_csv_path()
		export_csv_path1134 := _t1801
		_t1802 := p.parse_export_csv_columns_list()
		export_csv_columns_list1135 := _t1802
		_t1803 := p.parse_config_dict()
		config_dict1136 := _t1803
		p.consumeLiteral(")")
		_t1804 := p.construct_export_csv_config(export_csv_path1134, export_csv_columns_list1135, config_dict1136)
		_t1800 = _t1804
	} else {
		var _t1805 *pb.ExportCSVConfig
		if prediction1130 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1806 := p.parse_export_csv_path()
			export_csv_path1131 := _t1806
			_t1807 := p.parse_export_csv_source()
			export_csv_source1132 := _t1807
			_t1808 := p.parse_csv_config()
			csv_config1133 := _t1808
			p.consumeLiteral(")")
			_t1809 := p.construct_export_csv_config_with_source(export_csv_path1131, export_csv_source1132, csv_config1133)
			_t1805 = _t1809
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1800 = _t1805
	}
	result1138 := _t1800
	p.recordSpan(int(span_start1137), "ExportCSVConfig")
	return result1138
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1139 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1139
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1146 := int64(p.spanStart())
	var _t1810 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1811 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1811 = 1
		} else {
			var _t1812 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1812 = 0
			} else {
				_t1812 = -1
			}
			_t1811 = _t1812
		}
		_t1810 = _t1811
	} else {
		_t1810 = -1
	}
	prediction1140 := _t1810
	var _t1813 *pb.ExportCSVSource
	if prediction1140 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1814 := p.parse_relation_id()
		relation_id1145 := _t1814
		p.consumeLiteral(")")
		_t1815 := &pb.ExportCSVSource{}
		_t1815.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1145}
		_t1813 = _t1815
	} else {
		var _t1816 *pb.ExportCSVSource
		if prediction1140 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1141 := []*pb.ExportCSVColumn{}
			cond1142 := p.matchLookaheadLiteral("(", 0)
			for cond1142 {
				_t1817 := p.parse_export_csv_column()
				item1143 := _t1817
				xs1141 = append(xs1141, item1143)
				cond1142 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1144 := xs1141
			p.consumeLiteral(")")
			_t1818 := &pb.ExportCSVColumns{Columns: export_csv_columns1144}
			_t1819 := &pb.ExportCSVSource{}
			_t1819.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1818}
			_t1816 = _t1819
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1813 = _t1816
	}
	result1147 := _t1813
	p.recordSpan(int(span_start1146), "ExportCSVSource")
	return result1147
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1150 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1148 := p.consumeTerminal("STRING").Value.str
	_t1820 := p.parse_relation_id()
	relation_id1149 := _t1820
	p.consumeLiteral(")")
	_t1821 := &pb.ExportCSVColumn{ColumnName: string1148, ColumnData: relation_id1149}
	result1151 := _t1821
	p.recordSpan(int(span_start1150), "ExportCSVColumn")
	return result1151
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1152 := []*pb.ExportCSVColumn{}
	cond1153 := p.matchLookaheadLiteral("(", 0)
	for cond1153 {
		_t1822 := p.parse_export_csv_column()
		item1154 := _t1822
		xs1152 = append(xs1152, item1154)
		cond1153 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1155 := xs1152
	p.consumeLiteral(")")
	return export_csv_columns1155
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
