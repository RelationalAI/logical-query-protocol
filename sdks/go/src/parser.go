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
	Start Location
	Stop  Location
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
	kindFloat64
	kindUint128
	kindInt128
	kindDecimal
)

// TokenValue holds a typed token value.
type TokenValue struct {
	kind    tokenKind
	str     string
	i64     int64
	f64     float64
	uint128 *pb.UInt128Value
	int128  *pb.Int128Value
	decimal *pb.DecimalValue
}

func (tv TokenValue) String() string {
	switch tv.kind {
	case kindInt64:
		return strconv.FormatInt(tv.i64, 10)
	case kindFloat64:
		return strconv.FormatFloat(tv.f64, 'g', -1, 64)
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
		{"INT", regexp.MustCompile(`^[-]?\d+`), func(s string) TokenValue { return TokenValue{kind: kindInt64, i64: scanInt(s)} }},
		{"INT128", regexp.MustCompile(`^[-]?\d+i128`), func(s string) TokenValue { return TokenValue{kind: kindInt128, int128: scanInt128(s)} }},
		{"STRING", regexp.MustCompile(`^"(?:[^"\\]|\\.)*"`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanString(s)} }},
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_.-]*`), func(s string) TokenValue { return TokenValue{kind: kindString, str: scanSymbol(s)} }},
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
	Provenance        map[string]Span
	lineStarts        []int
}

// NewParser creates a new parser
func NewParser(tokens []Token, input string) *Parser {
	return &Parser{
		tokens:            tokens,
		pos:               0,
		idToDebugInfo:     make(map[string]map[relationIdKey]string),
		currentFragmentID: nil,
		Provenance:        make(map[string]Span),
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

func (p *Parser) recordSpan(startOffset int) {
	endOffset := startOffset
	if p.pos > 0 {
		endOffset = p.tokens[p.pos-1].EndPos
	}
	s := Span{
		Start: p.makeLocation(startOffset),
		Stop:  p.makeLocation(endOffset),
	}
	p.Provenance[""] = s
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
	// Create RelationId from string hash (matching Python implementation)
	// Python uses: int(hashlib.sha256(name.encode()).hexdigest()[:16], 16)
	// This takes only first 8 bytes (16 hex chars) as id_low, id_high is always 0
	// Python interprets the hex as big-endian, so we read bytes in big-endian order
	hash := sha256.Sum256([]byte(name))
	var low uint64
	for i := 0; i < 8; i++ {
		low = (low << 8) | uint64(hash[i])
	}
	high := uint64(0)
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
	var _t1794 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1794
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1795 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1795
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1796 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1796
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1797 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1797
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1798 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1798
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1799 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1799
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1800 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1800
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1801 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1801
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1802 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1802
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1803 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1803
	_t1804 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1804
	_t1805 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1805
	_t1806 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1806
	_t1807 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1807
	_t1808 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1808
	_t1809 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1809
	_t1810 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1810
	_t1811 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1811
	_t1812 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1812
	_t1813 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1813
	_t1814 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1814
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1815 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1815
	_t1816 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1816
	_t1817 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1817
	_t1818 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1818
	_t1819 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1819
	_t1820 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1820
	_t1821 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1821
	_t1822 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1822
	_t1823 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1823
	_t1824 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1824.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1824.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1824
	_t1825 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1825
}

func (p *Parser) default_configure() *pb.Configure {
	_t1826 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1826
	_t1827 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1827
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
	_t1828 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1828
	_t1829 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1829
	_t1830 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1830
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1831 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1831
	_t1832 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1832
	_t1833 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1833
	_t1834 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1834
	_t1835 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1835
	_t1836 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1836
	_t1837 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1837
	_t1838 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1838
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start598 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1184 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1185 := p.parse_configure()
		_t1184 = _t1185
	}
	configure592 := _t1184
	var _t1186 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1187 := p.parse_sync()
		_t1186 = _t1187
	}
	sync593 := _t1186
	xs594 := []*pb.Epoch{}
	cond595 := p.matchLookaheadLiteral("(", 0)
	for cond595 {
		_t1188 := p.parse_epoch()
		item596 := _t1188
		xs594 = append(xs594, item596)
		cond595 = p.matchLookaheadLiteral("(", 0)
	}
	epochs597 := xs594
	p.consumeLiteral(")")
	_t1189 := p.default_configure()
	_t1190 := configure592
	if configure592 == nil {
		_t1190 = _t1189
	}
	_t1191 := &pb.Transaction{Epochs: epochs597, Configure: _t1190, Sync: sync593}
	result599 := _t1191
	p.recordSpan(int(span_start598))
	return result599
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start601 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1192 := p.parse_config_dict()
	config_dict600 := _t1192
	p.consumeLiteral(")")
	_t1193 := p.construct_configure(config_dict600)
	result602 := _t1193
	p.recordSpan(int(span_start601))
	return result602
}

func (p *Parser) parse_config_dict() [][]interface{} {
	span_start607 := int64(p.spanStart())
	p.consumeLiteral("{")
	xs603 := [][]interface{}{}
	cond604 := p.matchLookaheadLiteral(":", 0)
	for cond604 {
		_t1194 := p.parse_config_key_value()
		item605 := _t1194
		xs603 = append(xs603, item605)
		cond604 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values606 := xs603
	p.consumeLiteral("}")
	result608 := config_key_values606
	p.recordSpan(int(span_start607))
	return result608
}

func (p *Parser) parse_config_key_value() []interface{} {
	span_start611 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol609 := p.consumeTerminal("SYMBOL").Value.str
	_t1195 := p.parse_value()
	value610 := _t1195
	result612 := []interface{}{symbol609, value610}
	p.recordSpan(int(span_start611))
	return result612
}

func (p *Parser) parse_value() *pb.Value {
	span_start623 := int64(p.spanStart())
	var _t1196 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1196 = 9
	} else {
		var _t1197 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1197 = 8
		} else {
			var _t1198 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1198 = 9
			} else {
				var _t1199 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1200 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1200 = 1
					} else {
						var _t1201 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1201 = 0
						} else {
							_t1201 = -1
						}
						_t1200 = _t1201
					}
					_t1199 = _t1200
				} else {
					var _t1202 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1202 = 5
					} else {
						var _t1203 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1203 = 2
						} else {
							var _t1204 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1204 = 6
							} else {
								var _t1205 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1205 = 3
								} else {
									var _t1206 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1206 = 4
									} else {
										var _t1207 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1207 = 7
										} else {
											_t1207 = -1
										}
										_t1206 = _t1207
									}
									_t1205 = _t1206
								}
								_t1204 = _t1205
							}
							_t1203 = _t1204
						}
						_t1202 = _t1203
					}
					_t1199 = _t1202
				}
				_t1198 = _t1199
			}
			_t1197 = _t1198
		}
		_t1196 = _t1197
	}
	prediction613 := _t1196
	var _t1208 *pb.Value
	if prediction613 == 9 {
		_t1209 := p.parse_boolean_value()
		boolean_value622 := _t1209
		_t1210 := &pb.Value{}
		_t1210.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value622}
		_t1208 = _t1210
	} else {
		var _t1211 *pb.Value
		if prediction613 == 8 {
			p.consumeLiteral("missing")
			_t1212 := &pb.MissingValue{}
			_t1213 := &pb.Value{}
			_t1213.Value = &pb.Value_MissingValue{MissingValue: _t1212}
			_t1211 = _t1213
		} else {
			var _t1214 *pb.Value
			if prediction613 == 7 {
				decimal621 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1215 := &pb.Value{}
				_t1215.Value = &pb.Value_DecimalValue{DecimalValue: decimal621}
				_t1214 = _t1215
			} else {
				var _t1216 *pb.Value
				if prediction613 == 6 {
					int128620 := p.consumeTerminal("INT128").Value.int128
					_t1217 := &pb.Value{}
					_t1217.Value = &pb.Value_Int128Value{Int128Value: int128620}
					_t1216 = _t1217
				} else {
					var _t1218 *pb.Value
					if prediction613 == 5 {
						uint128619 := p.consumeTerminal("UINT128").Value.uint128
						_t1219 := &pb.Value{}
						_t1219.Value = &pb.Value_Uint128Value{Uint128Value: uint128619}
						_t1218 = _t1219
					} else {
						var _t1220 *pb.Value
						if prediction613 == 4 {
							float618 := p.consumeTerminal("FLOAT").Value.f64
							_t1221 := &pb.Value{}
							_t1221.Value = &pb.Value_FloatValue{FloatValue: float618}
							_t1220 = _t1221
						} else {
							var _t1222 *pb.Value
							if prediction613 == 3 {
								int617 := p.consumeTerminal("INT").Value.i64
								_t1223 := &pb.Value{}
								_t1223.Value = &pb.Value_IntValue{IntValue: int617}
								_t1222 = _t1223
							} else {
								var _t1224 *pb.Value
								if prediction613 == 2 {
									string616 := p.consumeTerminal("STRING").Value.str
									_t1225 := &pb.Value{}
									_t1225.Value = &pb.Value_StringValue{StringValue: string616}
									_t1224 = _t1225
								} else {
									var _t1226 *pb.Value
									if prediction613 == 1 {
										_t1227 := p.parse_datetime()
										datetime615 := _t1227
										_t1228 := &pb.Value{}
										_t1228.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime615}
										_t1226 = _t1228
									} else {
										var _t1229 *pb.Value
										if prediction613 == 0 {
											_t1230 := p.parse_date()
											date614 := _t1230
											_t1231 := &pb.Value{}
											_t1231.Value = &pb.Value_DateValue{DateValue: date614}
											_t1229 = _t1231
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1226 = _t1229
									}
									_t1224 = _t1226
								}
								_t1222 = _t1224
							}
							_t1220 = _t1222
						}
						_t1218 = _t1220
					}
					_t1216 = _t1218
				}
				_t1214 = _t1216
			}
			_t1211 = _t1214
		}
		_t1208 = _t1211
	}
	result624 := _t1208
	p.recordSpan(int(span_start623))
	return result624
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start628 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int625 := p.consumeTerminal("INT").Value.i64
	int_3626 := p.consumeTerminal("INT").Value.i64
	int_4627 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1232 := &pb.DateValue{Year: int32(int625), Month: int32(int_3626), Day: int32(int_4627)}
	result629 := _t1232
	p.recordSpan(int(span_start628))
	return result629
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start637 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int630 := p.consumeTerminal("INT").Value.i64
	int_3631 := p.consumeTerminal("INT").Value.i64
	int_4632 := p.consumeTerminal("INT").Value.i64
	int_5633 := p.consumeTerminal("INT").Value.i64
	int_6634 := p.consumeTerminal("INT").Value.i64
	int_7635 := p.consumeTerminal("INT").Value.i64
	var _t1233 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1233 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8636 := _t1233
	p.consumeLiteral(")")
	_t1234 := &pb.DateTimeValue{Year: int32(int630), Month: int32(int_3631), Day: int32(int_4632), Hour: int32(int_5633), Minute: int32(int_6634), Second: int32(int_7635), Microsecond: int32(deref(int_8636, 0))}
	result638 := _t1234
	p.recordSpan(int(span_start637))
	return result638
}

func (p *Parser) parse_boolean_value() bool {
	span_start640 := int64(p.spanStart())
	var _t1235 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1235 = 0
	} else {
		var _t1236 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1236 = 1
		} else {
			_t1236 = -1
		}
		_t1235 = _t1236
	}
	prediction639 := _t1235
	var _t1237 bool
	if prediction639 == 1 {
		p.consumeLiteral("false")
		_t1237 = false
	} else {
		var _t1238 bool
		if prediction639 == 0 {
			p.consumeLiteral("true")
			_t1238 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1237 = _t1238
	}
	result641 := _t1237
	p.recordSpan(int(span_start640))
	return result641
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start646 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs642 := []*pb.FragmentId{}
	cond643 := p.matchLookaheadLiteral(":", 0)
	for cond643 {
		_t1239 := p.parse_fragment_id()
		item644 := _t1239
		xs642 = append(xs642, item644)
		cond643 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids645 := xs642
	p.consumeLiteral(")")
	_t1240 := &pb.Sync{Fragments: fragment_ids645}
	result647 := _t1240
	p.recordSpan(int(span_start646))
	return result647
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start649 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol648 := p.consumeTerminal("SYMBOL").Value.str
	result650 := &pb.FragmentId{Id: []byte(symbol648)}
	p.recordSpan(int(span_start649))
	return result650
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start653 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1241 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1242 := p.parse_epoch_writes()
		_t1241 = _t1242
	}
	epoch_writes651 := _t1241
	var _t1243 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1244 := p.parse_epoch_reads()
		_t1243 = _t1244
	}
	epoch_reads652 := _t1243
	p.consumeLiteral(")")
	_t1245 := epoch_writes651
	if epoch_writes651 == nil {
		_t1245 = []*pb.Write{}
	}
	_t1246 := epoch_reads652
	if epoch_reads652 == nil {
		_t1246 = []*pb.Read{}
	}
	_t1247 := &pb.Epoch{Writes: _t1245, Reads: _t1246}
	result654 := _t1247
	p.recordSpan(int(span_start653))
	return result654
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	span_start659 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs655 := []*pb.Write{}
	cond656 := p.matchLookaheadLiteral("(", 0)
	for cond656 {
		_t1248 := p.parse_write()
		item657 := _t1248
		xs655 = append(xs655, item657)
		cond656 = p.matchLookaheadLiteral("(", 0)
	}
	writes658 := xs655
	p.consumeLiteral(")")
	result660 := writes658
	p.recordSpan(int(span_start659))
	return result660
}

func (p *Parser) parse_write() *pb.Write {
	span_start666 := int64(p.spanStart())
	var _t1249 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1250 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1250 = 1
		} else {
			var _t1251 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1251 = 3
			} else {
				var _t1252 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1252 = 0
				} else {
					var _t1253 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1253 = 2
					} else {
						_t1253 = -1
					}
					_t1252 = _t1253
				}
				_t1251 = _t1252
			}
			_t1250 = _t1251
		}
		_t1249 = _t1250
	} else {
		_t1249 = -1
	}
	prediction661 := _t1249
	var _t1254 *pb.Write
	if prediction661 == 3 {
		_t1255 := p.parse_snapshot()
		snapshot665 := _t1255
		_t1256 := &pb.Write{}
		_t1256.WriteType = &pb.Write_Snapshot{Snapshot: snapshot665}
		_t1254 = _t1256
	} else {
		var _t1257 *pb.Write
		if prediction661 == 2 {
			_t1258 := p.parse_context()
			context664 := _t1258
			_t1259 := &pb.Write{}
			_t1259.WriteType = &pb.Write_Context{Context: context664}
			_t1257 = _t1259
		} else {
			var _t1260 *pb.Write
			if prediction661 == 1 {
				_t1261 := p.parse_undefine()
				undefine663 := _t1261
				_t1262 := &pb.Write{}
				_t1262.WriteType = &pb.Write_Undefine{Undefine: undefine663}
				_t1260 = _t1262
			} else {
				var _t1263 *pb.Write
				if prediction661 == 0 {
					_t1264 := p.parse_define()
					define662 := _t1264
					_t1265 := &pb.Write{}
					_t1265.WriteType = &pb.Write_Define{Define: define662}
					_t1263 = _t1265
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1260 = _t1263
			}
			_t1257 = _t1260
		}
		_t1254 = _t1257
	}
	result667 := _t1254
	p.recordSpan(int(span_start666))
	return result667
}

func (p *Parser) parse_define() *pb.Define {
	span_start669 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1266 := p.parse_fragment()
	fragment668 := _t1266
	p.consumeLiteral(")")
	_t1267 := &pb.Define{Fragment: fragment668}
	result670 := _t1267
	p.recordSpan(int(span_start669))
	return result670
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start676 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1268 := p.parse_new_fragment_id()
	new_fragment_id671 := _t1268
	xs672 := []*pb.Declaration{}
	cond673 := p.matchLookaheadLiteral("(", 0)
	for cond673 {
		_t1269 := p.parse_declaration()
		item674 := _t1269
		xs672 = append(xs672, item674)
		cond673 = p.matchLookaheadLiteral("(", 0)
	}
	declarations675 := xs672
	p.consumeLiteral(")")
	result677 := p.constructFragment(new_fragment_id671, declarations675)
	p.recordSpan(int(span_start676))
	return result677
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start679 := int64(p.spanStart())
	_t1270 := p.parse_fragment_id()
	fragment_id678 := _t1270
	p.startFragment(fragment_id678)
	result680 := fragment_id678
	p.recordSpan(int(span_start679))
	return result680
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start686 := int64(p.spanStart())
	var _t1271 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1272 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1272 = 3
		} else {
			var _t1273 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1273 = 2
			} else {
				var _t1274 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1274 = 0
				} else {
					var _t1275 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1275 = 3
					} else {
						var _t1276 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1276 = 3
						} else {
							var _t1277 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1277 = 1
							} else {
								_t1277 = -1
							}
							_t1276 = _t1277
						}
						_t1275 = _t1276
					}
					_t1274 = _t1275
				}
				_t1273 = _t1274
			}
			_t1272 = _t1273
		}
		_t1271 = _t1272
	} else {
		_t1271 = -1
	}
	prediction681 := _t1271
	var _t1278 *pb.Declaration
	if prediction681 == 3 {
		_t1279 := p.parse_data()
		data685 := _t1279
		_t1280 := &pb.Declaration{}
		_t1280.DeclarationType = &pb.Declaration_Data{Data: data685}
		_t1278 = _t1280
	} else {
		var _t1281 *pb.Declaration
		if prediction681 == 2 {
			_t1282 := p.parse_constraint()
			constraint684 := _t1282
			_t1283 := &pb.Declaration{}
			_t1283.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint684}
			_t1281 = _t1283
		} else {
			var _t1284 *pb.Declaration
			if prediction681 == 1 {
				_t1285 := p.parse_algorithm()
				algorithm683 := _t1285
				_t1286 := &pb.Declaration{}
				_t1286.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm683}
				_t1284 = _t1286
			} else {
				var _t1287 *pb.Declaration
				if prediction681 == 0 {
					_t1288 := p.parse_def()
					def682 := _t1288
					_t1289 := &pb.Declaration{}
					_t1289.DeclarationType = &pb.Declaration_Def{Def: def682}
					_t1287 = _t1289
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1284 = _t1287
			}
			_t1281 = _t1284
		}
		_t1278 = _t1281
	}
	result687 := _t1278
	p.recordSpan(int(span_start686))
	return result687
}

func (p *Parser) parse_def() *pb.Def {
	span_start691 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1290 := p.parse_relation_id()
	relation_id688 := _t1290
	_t1291 := p.parse_abstraction()
	abstraction689 := _t1291
	var _t1292 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1293 := p.parse_attrs()
		_t1292 = _t1293
	}
	attrs690 := _t1292
	p.consumeLiteral(")")
	_t1294 := attrs690
	if attrs690 == nil {
		_t1294 = []*pb.Attribute{}
	}
	_t1295 := &pb.Def{Name: relation_id688, Body: abstraction689, Attrs: _t1294}
	result692 := _t1295
	p.recordSpan(int(span_start691))
	return result692
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start696 := int64(p.spanStart())
	var _t1296 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1296 = 0
	} else {
		var _t1297 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1297 = 1
		} else {
			_t1297 = -1
		}
		_t1296 = _t1297
	}
	prediction693 := _t1296
	var _t1298 *pb.RelationId
	if prediction693 == 1 {
		uint128695 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128695
		_t1298 = &pb.RelationId{IdLow: uint128695.Low, IdHigh: uint128695.High}
	} else {
		var _t1299 *pb.RelationId
		if prediction693 == 0 {
			p.consumeLiteral(":")
			symbol694 := p.consumeTerminal("SYMBOL").Value.str
			_t1299 = p.relationIdFromString(symbol694)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1298 = _t1299
	}
	result697 := _t1298
	p.recordSpan(int(span_start696))
	return result697
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start700 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1300 := p.parse_bindings()
	bindings698 := _t1300
	_t1301 := p.parse_formula()
	formula699 := _t1301
	p.consumeLiteral(")")
	_t1302 := &pb.Abstraction{Vars: listConcat(bindings698[0].([]*pb.Binding), bindings698[1].([]*pb.Binding)), Value: formula699}
	result701 := _t1302
	p.recordSpan(int(span_start700))
	return result701
}

func (p *Parser) parse_bindings() []interface{} {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs702 := []*pb.Binding{}
	cond703 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond703 {
		_t1303 := p.parse_binding()
		item704 := _t1303
		xs702 = append(xs702, item704)
		cond703 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings705 := xs702
	var _t1304 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1305 := p.parse_value_bindings()
		_t1304 = _t1305
	}
	value_bindings706 := _t1304
	p.consumeLiteral("]")
	_t1306 := value_bindings706
	if value_bindings706 == nil {
		_t1306 = []*pb.Binding{}
	}
	result708 := []interface{}{bindings705, _t1306}
	p.recordSpan(int(span_start707))
	return result708
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start711 := int64(p.spanStart())
	symbol709 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1307 := p.parse_type()
	type710 := _t1307
	_t1308 := &pb.Var{Name: symbol709}
	_t1309 := &pb.Binding{Var: _t1308, Type: type710}
	result712 := _t1309
	p.recordSpan(int(span_start711))
	return result712
}

func (p *Parser) parse_type() *pb.Type {
	span_start725 := int64(p.spanStart())
	var _t1310 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1310 = 0
	} else {
		var _t1311 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1311 = 4
		} else {
			var _t1312 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1312 = 1
			} else {
				var _t1313 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1313 = 8
				} else {
					var _t1314 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1314 = 5
					} else {
						var _t1315 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1315 = 2
						} else {
							var _t1316 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1316 = 3
							} else {
								var _t1317 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1317 = 7
								} else {
									var _t1318 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1318 = 6
									} else {
										var _t1319 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1319 = 10
										} else {
											var _t1320 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1320 = 9
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
							}
							_t1315 = _t1316
						}
						_t1314 = _t1315
					}
					_t1313 = _t1314
				}
				_t1312 = _t1313
			}
			_t1311 = _t1312
		}
		_t1310 = _t1311
	}
	prediction713 := _t1310
	var _t1321 *pb.Type
	if prediction713 == 10 {
		_t1322 := p.parse_boolean_type()
		boolean_type724 := _t1322
		_t1323 := &pb.Type{}
		_t1323.Type = &pb.Type_BooleanType{BooleanType: boolean_type724}
		_t1321 = _t1323
	} else {
		var _t1324 *pb.Type
		if prediction713 == 9 {
			_t1325 := p.parse_decimal_type()
			decimal_type723 := _t1325
			_t1326 := &pb.Type{}
			_t1326.Type = &pb.Type_DecimalType{DecimalType: decimal_type723}
			_t1324 = _t1326
		} else {
			var _t1327 *pb.Type
			if prediction713 == 8 {
				_t1328 := p.parse_missing_type()
				missing_type722 := _t1328
				_t1329 := &pb.Type{}
				_t1329.Type = &pb.Type_MissingType{MissingType: missing_type722}
				_t1327 = _t1329
			} else {
				var _t1330 *pb.Type
				if prediction713 == 7 {
					_t1331 := p.parse_datetime_type()
					datetime_type721 := _t1331
					_t1332 := &pb.Type{}
					_t1332.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type721}
					_t1330 = _t1332
				} else {
					var _t1333 *pb.Type
					if prediction713 == 6 {
						_t1334 := p.parse_date_type()
						date_type720 := _t1334
						_t1335 := &pb.Type{}
						_t1335.Type = &pb.Type_DateType{DateType: date_type720}
						_t1333 = _t1335
					} else {
						var _t1336 *pb.Type
						if prediction713 == 5 {
							_t1337 := p.parse_int128_type()
							int128_type719 := _t1337
							_t1338 := &pb.Type{}
							_t1338.Type = &pb.Type_Int128Type{Int128Type: int128_type719}
							_t1336 = _t1338
						} else {
							var _t1339 *pb.Type
							if prediction713 == 4 {
								_t1340 := p.parse_uint128_type()
								uint128_type718 := _t1340
								_t1341 := &pb.Type{}
								_t1341.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type718}
								_t1339 = _t1341
							} else {
								var _t1342 *pb.Type
								if prediction713 == 3 {
									_t1343 := p.parse_float_type()
									float_type717 := _t1343
									_t1344 := &pb.Type{}
									_t1344.Type = &pb.Type_FloatType{FloatType: float_type717}
									_t1342 = _t1344
								} else {
									var _t1345 *pb.Type
									if prediction713 == 2 {
										_t1346 := p.parse_int_type()
										int_type716 := _t1346
										_t1347 := &pb.Type{}
										_t1347.Type = &pb.Type_IntType{IntType: int_type716}
										_t1345 = _t1347
									} else {
										var _t1348 *pb.Type
										if prediction713 == 1 {
											_t1349 := p.parse_string_type()
											string_type715 := _t1349
											_t1350 := &pb.Type{}
											_t1350.Type = &pb.Type_StringType{StringType: string_type715}
											_t1348 = _t1350
										} else {
											var _t1351 *pb.Type
											if prediction713 == 0 {
												_t1352 := p.parse_unspecified_type()
												unspecified_type714 := _t1352
												_t1353 := &pb.Type{}
												_t1353.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type714}
												_t1351 = _t1353
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t1348 = _t1351
										}
										_t1345 = _t1348
									}
									_t1342 = _t1345
								}
								_t1339 = _t1342
							}
							_t1336 = _t1339
						}
						_t1333 = _t1336
					}
					_t1330 = _t1333
				}
				_t1327 = _t1330
			}
			_t1324 = _t1327
		}
		_t1321 = _t1324
	}
	result726 := _t1321
	p.recordSpan(int(span_start725))
	return result726
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start727 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1354 := &pb.UnspecifiedType{}
	result728 := _t1354
	p.recordSpan(int(span_start727))
	return result728
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start729 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1355 := &pb.StringType{}
	result730 := _t1355
	p.recordSpan(int(span_start729))
	return result730
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1356 := &pb.IntType{}
	result732 := _t1356
	p.recordSpan(int(span_start731))
	return result732
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start733 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1357 := &pb.FloatType{}
	result734 := _t1357
	p.recordSpan(int(span_start733))
	return result734
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1358 := &pb.UInt128Type{}
	result736 := _t1358
	p.recordSpan(int(span_start735))
	return result736
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1359 := &pb.Int128Type{}
	result738 := _t1359
	p.recordSpan(int(span_start737))
	return result738
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1360 := &pb.DateType{}
	result740 := _t1360
	p.recordSpan(int(span_start739))
	return result740
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start741 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1361 := &pb.DateTimeType{}
	result742 := _t1361
	p.recordSpan(int(span_start741))
	return result742
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1362 := &pb.MissingType{}
	result744 := _t1362
	p.recordSpan(int(span_start743))
	return result744
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int745 := p.consumeTerminal("INT").Value.i64
	int_3746 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1363 := &pb.DecimalType{Precision: int32(int745), Scale: int32(int_3746)}
	result748 := _t1363
	p.recordSpan(int(span_start747))
	return result748
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1364 := &pb.BooleanType{}
	result750 := _t1364
	p.recordSpan(int(span_start749))
	return result750
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("|")
	xs751 := []*pb.Binding{}
	cond752 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond752 {
		_t1365 := p.parse_binding()
		item753 := _t1365
		xs751 = append(xs751, item753)
		cond752 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings754 := xs751
	result756 := bindings754
	p.recordSpan(int(span_start755))
	return result756
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start771 := int64(p.spanStart())
	var _t1366 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1367 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1367 = 0
		} else {
			var _t1368 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1368 = 11
			} else {
				var _t1369 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1369 = 3
				} else {
					var _t1370 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1370 = 10
					} else {
						var _t1371 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1371 = 9
						} else {
							var _t1372 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1372 = 5
							} else {
								var _t1373 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1373 = 6
								} else {
									var _t1374 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1374 = 7
									} else {
										var _t1375 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1375 = 1
										} else {
											var _t1376 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1376 = 2
											} else {
												var _t1377 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1377 = 12
												} else {
													var _t1378 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1378 = 8
													} else {
														var _t1379 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1379 = 4
														} else {
															var _t1380 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1380 = 10
															} else {
																var _t1381 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1381 = 10
																} else {
																	var _t1382 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1382 = 10
																	} else {
																		var _t1383 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1383 = 10
																		} else {
																			var _t1384 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1384 = 10
																			} else {
																				var _t1385 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1385 = 10
																				} else {
																					var _t1386 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1386 = 10
																					} else {
																						var _t1387 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1387 = 10
																						} else {
																							var _t1388 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1388 = 10
																							} else {
																								_t1388 = -1
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
	} else {
		_t1366 = -1
	}
	prediction757 := _t1366
	var _t1389 *pb.Formula
	if prediction757 == 12 {
		_t1390 := p.parse_cast()
		cast770 := _t1390
		_t1391 := &pb.Formula{}
		_t1391.FormulaType = &pb.Formula_Cast{Cast: cast770}
		_t1389 = _t1391
	} else {
		var _t1392 *pb.Formula
		if prediction757 == 11 {
			_t1393 := p.parse_rel_atom()
			rel_atom769 := _t1393
			_t1394 := &pb.Formula{}
			_t1394.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom769}
			_t1392 = _t1394
		} else {
			var _t1395 *pb.Formula
			if prediction757 == 10 {
				_t1396 := p.parse_primitive()
				primitive768 := _t1396
				_t1397 := &pb.Formula{}
				_t1397.FormulaType = &pb.Formula_Primitive{Primitive: primitive768}
				_t1395 = _t1397
			} else {
				var _t1398 *pb.Formula
				if prediction757 == 9 {
					_t1399 := p.parse_pragma()
					pragma767 := _t1399
					_t1400 := &pb.Formula{}
					_t1400.FormulaType = &pb.Formula_Pragma{Pragma: pragma767}
					_t1398 = _t1400
				} else {
					var _t1401 *pb.Formula
					if prediction757 == 8 {
						_t1402 := p.parse_atom()
						atom766 := _t1402
						_t1403 := &pb.Formula{}
						_t1403.FormulaType = &pb.Formula_Atom{Atom: atom766}
						_t1401 = _t1403
					} else {
						var _t1404 *pb.Formula
						if prediction757 == 7 {
							_t1405 := p.parse_ffi()
							ffi765 := _t1405
							_t1406 := &pb.Formula{}
							_t1406.FormulaType = &pb.Formula_Ffi{Ffi: ffi765}
							_t1404 = _t1406
						} else {
							var _t1407 *pb.Formula
							if prediction757 == 6 {
								_t1408 := p.parse_not()
								not764 := _t1408
								_t1409 := &pb.Formula{}
								_t1409.FormulaType = &pb.Formula_Not{Not: not764}
								_t1407 = _t1409
							} else {
								var _t1410 *pb.Formula
								if prediction757 == 5 {
									_t1411 := p.parse_disjunction()
									disjunction763 := _t1411
									_t1412 := &pb.Formula{}
									_t1412.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction763}
									_t1410 = _t1412
								} else {
									var _t1413 *pb.Formula
									if prediction757 == 4 {
										_t1414 := p.parse_conjunction()
										conjunction762 := _t1414
										_t1415 := &pb.Formula{}
										_t1415.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction762}
										_t1413 = _t1415
									} else {
										var _t1416 *pb.Formula
										if prediction757 == 3 {
											_t1417 := p.parse_reduce()
											reduce761 := _t1417
											_t1418 := &pb.Formula{}
											_t1418.FormulaType = &pb.Formula_Reduce{Reduce: reduce761}
											_t1416 = _t1418
										} else {
											var _t1419 *pb.Formula
											if prediction757 == 2 {
												_t1420 := p.parse_exists()
												exists760 := _t1420
												_t1421 := &pb.Formula{}
												_t1421.FormulaType = &pb.Formula_Exists{Exists: exists760}
												_t1419 = _t1421
											} else {
												var _t1422 *pb.Formula
												if prediction757 == 1 {
													_t1423 := p.parse_false()
													false759 := _t1423
													_t1424 := &pb.Formula{}
													_t1424.FormulaType = &pb.Formula_Disjunction{Disjunction: false759}
													_t1422 = _t1424
												} else {
													var _t1425 *pb.Formula
													if prediction757 == 0 {
														_t1426 := p.parse_true()
														true758 := _t1426
														_t1427 := &pb.Formula{}
														_t1427.FormulaType = &pb.Formula_Conjunction{Conjunction: true758}
														_t1425 = _t1427
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1422 = _t1425
												}
												_t1419 = _t1422
											}
											_t1416 = _t1419
										}
										_t1413 = _t1416
									}
									_t1410 = _t1413
								}
								_t1407 = _t1410
							}
							_t1404 = _t1407
						}
						_t1401 = _t1404
					}
					_t1398 = _t1401
				}
				_t1395 = _t1398
			}
			_t1392 = _t1395
		}
		_t1389 = _t1392
	}
	result772 := _t1389
	p.recordSpan(int(span_start771))
	return result772
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start773 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1428 := &pb.Conjunction{Args: []*pb.Formula{}}
	result774 := _t1428
	p.recordSpan(int(span_start773))
	return result774
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start775 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1429 := &pb.Disjunction{Args: []*pb.Formula{}}
	result776 := _t1429
	p.recordSpan(int(span_start775))
	return result776
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start779 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1430 := p.parse_bindings()
	bindings777 := _t1430
	_t1431 := p.parse_formula()
	formula778 := _t1431
	p.consumeLiteral(")")
	_t1432 := &pb.Abstraction{Vars: listConcat(bindings777[0].([]*pb.Binding), bindings777[1].([]*pb.Binding)), Value: formula778}
	_t1433 := &pb.Exists{Body: _t1432}
	result780 := _t1433
	p.recordSpan(int(span_start779))
	return result780
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start784 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1434 := p.parse_abstraction()
	abstraction781 := _t1434
	_t1435 := p.parse_abstraction()
	abstraction_3782 := _t1435
	_t1436 := p.parse_terms()
	terms783 := _t1436
	p.consumeLiteral(")")
	_t1437 := &pb.Reduce{Op: abstraction781, Body: abstraction_3782, Terms: terms783}
	result785 := _t1437
	p.recordSpan(int(span_start784))
	return result785
}

func (p *Parser) parse_terms() []*pb.Term {
	span_start790 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs786 := []*pb.Term{}
	cond787 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond787 {
		_t1438 := p.parse_term()
		item788 := _t1438
		xs786 = append(xs786, item788)
		cond787 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms789 := xs786
	p.consumeLiteral(")")
	result791 := terms789
	p.recordSpan(int(span_start790))
	return result791
}

func (p *Parser) parse_term() *pb.Term {
	span_start795 := int64(p.spanStart())
	var _t1439 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1439 = 1
	} else {
		var _t1440 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1440 = 1
		} else {
			var _t1441 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1441 = 1
			} else {
				var _t1442 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1442 = 1
				} else {
					var _t1443 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1443 = 1
					} else {
						var _t1444 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1444 = 0
						} else {
							var _t1445 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1445 = 1
							} else {
								var _t1446 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1446 = 1
								} else {
									var _t1447 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1447 = 1
									} else {
										var _t1448 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1448 = 1
										} else {
											var _t1449 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1449 = 1
											} else {
												_t1449 = -1
											}
											_t1448 = _t1449
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
	prediction792 := _t1439
	var _t1450 *pb.Term
	if prediction792 == 1 {
		_t1451 := p.parse_constant()
		constant794 := _t1451
		_t1452 := &pb.Term{}
		_t1452.TermType = &pb.Term_Constant{Constant: constant794}
		_t1450 = _t1452
	} else {
		var _t1453 *pb.Term
		if prediction792 == 0 {
			_t1454 := p.parse_var()
			var793 := _t1454
			_t1455 := &pb.Term{}
			_t1455.TermType = &pb.Term_Var{Var: var793}
			_t1453 = _t1455
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1450 = _t1453
	}
	result796 := _t1450
	p.recordSpan(int(span_start795))
	return result796
}

func (p *Parser) parse_var() *pb.Var {
	span_start798 := int64(p.spanStart())
	symbol797 := p.consumeTerminal("SYMBOL").Value.str
	_t1456 := &pb.Var{Name: symbol797}
	result799 := _t1456
	p.recordSpan(int(span_start798))
	return result799
}

func (p *Parser) parse_constant() *pb.Value {
	span_start801 := int64(p.spanStart())
	_t1457 := p.parse_value()
	value800 := _t1457
	result802 := value800
	p.recordSpan(int(span_start801))
	return result802
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs803 := []*pb.Formula{}
	cond804 := p.matchLookaheadLiteral("(", 0)
	for cond804 {
		_t1458 := p.parse_formula()
		item805 := _t1458
		xs803 = append(xs803, item805)
		cond804 = p.matchLookaheadLiteral("(", 0)
	}
	formulas806 := xs803
	p.consumeLiteral(")")
	_t1459 := &pb.Conjunction{Args: formulas806}
	result808 := _t1459
	p.recordSpan(int(span_start807))
	return result808
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs809 := []*pb.Formula{}
	cond810 := p.matchLookaheadLiteral("(", 0)
	for cond810 {
		_t1460 := p.parse_formula()
		item811 := _t1460
		xs809 = append(xs809, item811)
		cond810 = p.matchLookaheadLiteral("(", 0)
	}
	formulas812 := xs809
	p.consumeLiteral(")")
	_t1461 := &pb.Disjunction{Args: formulas812}
	result814 := _t1461
	p.recordSpan(int(span_start813))
	return result814
}

func (p *Parser) parse_not() *pb.Not {
	span_start816 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1462 := p.parse_formula()
	formula815 := _t1462
	p.consumeLiteral(")")
	_t1463 := &pb.Not{Arg: formula815}
	result817 := _t1463
	p.recordSpan(int(span_start816))
	return result817
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start821 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1464 := p.parse_name()
	name818 := _t1464
	_t1465 := p.parse_ffi_args()
	ffi_args819 := _t1465
	_t1466 := p.parse_terms()
	terms820 := _t1466
	p.consumeLiteral(")")
	_t1467 := &pb.FFI{Name: name818, Args: ffi_args819, Terms: terms820}
	result822 := _t1467
	p.recordSpan(int(span_start821))
	return result822
}

func (p *Parser) parse_name() string {
	span_start824 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol823 := p.consumeTerminal("SYMBOL").Value.str
	result825 := symbol823
	p.recordSpan(int(span_start824))
	return result825
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	span_start830 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs826 := []*pb.Abstraction{}
	cond827 := p.matchLookaheadLiteral("(", 0)
	for cond827 {
		_t1468 := p.parse_abstraction()
		item828 := _t1468
		xs826 = append(xs826, item828)
		cond827 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions829 := xs826
	p.consumeLiteral(")")
	result831 := abstractions829
	p.recordSpan(int(span_start830))
	return result831
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1469 := p.parse_relation_id()
	relation_id832 := _t1469
	xs833 := []*pb.Term{}
	cond834 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond834 {
		_t1470 := p.parse_term()
		item835 := _t1470
		xs833 = append(xs833, item835)
		cond834 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms836 := xs833
	p.consumeLiteral(")")
	_t1471 := &pb.Atom{Name: relation_id832, Terms: terms836}
	result838 := _t1471
	p.recordSpan(int(span_start837))
	return result838
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start844 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1472 := p.parse_name()
	name839 := _t1472
	xs840 := []*pb.Term{}
	cond841 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond841 {
		_t1473 := p.parse_term()
		item842 := _t1473
		xs840 = append(xs840, item842)
		cond841 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms843 := xs840
	p.consumeLiteral(")")
	_t1474 := &pb.Pragma{Name: name839, Terms: terms843}
	result845 := _t1474
	p.recordSpan(int(span_start844))
	return result845
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start861 := int64(p.spanStart())
	var _t1475 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1476 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1476 = 9
		} else {
			var _t1477 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1477 = 4
			} else {
				var _t1478 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1478 = 3
				} else {
					var _t1479 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1479 = 0
					} else {
						var _t1480 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1480 = 2
						} else {
							var _t1481 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1481 = 1
							} else {
								var _t1482 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1482 = 8
								} else {
									var _t1483 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1483 = 6
									} else {
										var _t1484 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1484 = 5
										} else {
											var _t1485 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1485 = 7
											} else {
												_t1485 = -1
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
				_t1477 = _t1478
			}
			_t1476 = _t1477
		}
		_t1475 = _t1476
	} else {
		_t1475 = -1
	}
	prediction846 := _t1475
	var _t1486 *pb.Primitive
	if prediction846 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1487 := p.parse_name()
		name856 := _t1487
		xs857 := []*pb.RelTerm{}
		cond858 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond858 {
			_t1488 := p.parse_rel_term()
			item859 := _t1488
			xs857 = append(xs857, item859)
			cond858 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms860 := xs857
		p.consumeLiteral(")")
		_t1489 := &pb.Primitive{Name: name856, Terms: rel_terms860}
		_t1486 = _t1489
	} else {
		var _t1490 *pb.Primitive
		if prediction846 == 8 {
			_t1491 := p.parse_divide()
			divide855 := _t1491
			_t1490 = divide855
		} else {
			var _t1492 *pb.Primitive
			if prediction846 == 7 {
				_t1493 := p.parse_multiply()
				multiply854 := _t1493
				_t1492 = multiply854
			} else {
				var _t1494 *pb.Primitive
				if prediction846 == 6 {
					_t1495 := p.parse_minus()
					minus853 := _t1495
					_t1494 = minus853
				} else {
					var _t1496 *pb.Primitive
					if prediction846 == 5 {
						_t1497 := p.parse_add()
						add852 := _t1497
						_t1496 = add852
					} else {
						var _t1498 *pb.Primitive
						if prediction846 == 4 {
							_t1499 := p.parse_gt_eq()
							gt_eq851 := _t1499
							_t1498 = gt_eq851
						} else {
							var _t1500 *pb.Primitive
							if prediction846 == 3 {
								_t1501 := p.parse_gt()
								gt850 := _t1501
								_t1500 = gt850
							} else {
								var _t1502 *pb.Primitive
								if prediction846 == 2 {
									_t1503 := p.parse_lt_eq()
									lt_eq849 := _t1503
									_t1502 = lt_eq849
								} else {
									var _t1504 *pb.Primitive
									if prediction846 == 1 {
										_t1505 := p.parse_lt()
										lt848 := _t1505
										_t1504 = lt848
									} else {
										var _t1506 *pb.Primitive
										if prediction846 == 0 {
											_t1507 := p.parse_eq()
											eq847 := _t1507
											_t1506 = eq847
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1504 = _t1506
									}
									_t1502 = _t1504
								}
								_t1500 = _t1502
							}
							_t1498 = _t1500
						}
						_t1496 = _t1498
					}
					_t1494 = _t1496
				}
				_t1492 = _t1494
			}
			_t1490 = _t1492
		}
		_t1486 = _t1490
	}
	result862 := _t1486
	p.recordSpan(int(span_start861))
	return result862
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1508 := p.parse_term()
	term863 := _t1508
	_t1509 := p.parse_term()
	term_3864 := _t1509
	p.consumeLiteral(")")
	_t1510 := &pb.RelTerm{}
	_t1510.RelTermType = &pb.RelTerm_Term{Term: term863}
	_t1511 := &pb.RelTerm{}
	_t1511.RelTermType = &pb.RelTerm_Term{Term: term_3864}
	_t1512 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1510, _t1511}}
	result866 := _t1512
	p.recordSpan(int(span_start865))
	return result866
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start869 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1513 := p.parse_term()
	term867 := _t1513
	_t1514 := p.parse_term()
	term_3868 := _t1514
	p.consumeLiteral(")")
	_t1515 := &pb.RelTerm{}
	_t1515.RelTermType = &pb.RelTerm_Term{Term: term867}
	_t1516 := &pb.RelTerm{}
	_t1516.RelTermType = &pb.RelTerm_Term{Term: term_3868}
	_t1517 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1515, _t1516}}
	result870 := _t1517
	p.recordSpan(int(span_start869))
	return result870
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start873 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1518 := p.parse_term()
	term871 := _t1518
	_t1519 := p.parse_term()
	term_3872 := _t1519
	p.consumeLiteral(")")
	_t1520 := &pb.RelTerm{}
	_t1520.RelTermType = &pb.RelTerm_Term{Term: term871}
	_t1521 := &pb.RelTerm{}
	_t1521.RelTermType = &pb.RelTerm_Term{Term: term_3872}
	_t1522 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1520, _t1521}}
	result874 := _t1522
	p.recordSpan(int(span_start873))
	return result874
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start877 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1523 := p.parse_term()
	term875 := _t1523
	_t1524 := p.parse_term()
	term_3876 := _t1524
	p.consumeLiteral(")")
	_t1525 := &pb.RelTerm{}
	_t1525.RelTermType = &pb.RelTerm_Term{Term: term875}
	_t1526 := &pb.RelTerm{}
	_t1526.RelTermType = &pb.RelTerm_Term{Term: term_3876}
	_t1527 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1525, _t1526}}
	result878 := _t1527
	p.recordSpan(int(span_start877))
	return result878
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start881 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1528 := p.parse_term()
	term879 := _t1528
	_t1529 := p.parse_term()
	term_3880 := _t1529
	p.consumeLiteral(")")
	_t1530 := &pb.RelTerm{}
	_t1530.RelTermType = &pb.RelTerm_Term{Term: term879}
	_t1531 := &pb.RelTerm{}
	_t1531.RelTermType = &pb.RelTerm_Term{Term: term_3880}
	_t1532 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1530, _t1531}}
	result882 := _t1532
	p.recordSpan(int(span_start881))
	return result882
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start886 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1533 := p.parse_term()
	term883 := _t1533
	_t1534 := p.parse_term()
	term_3884 := _t1534
	_t1535 := p.parse_term()
	term_4885 := _t1535
	p.consumeLiteral(")")
	_t1536 := &pb.RelTerm{}
	_t1536.RelTermType = &pb.RelTerm_Term{Term: term883}
	_t1537 := &pb.RelTerm{}
	_t1537.RelTermType = &pb.RelTerm_Term{Term: term_3884}
	_t1538 := &pb.RelTerm{}
	_t1538.RelTermType = &pb.RelTerm_Term{Term: term_4885}
	_t1539 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1536, _t1537, _t1538}}
	result887 := _t1539
	p.recordSpan(int(span_start886))
	return result887
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start891 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1540 := p.parse_term()
	term888 := _t1540
	_t1541 := p.parse_term()
	term_3889 := _t1541
	_t1542 := p.parse_term()
	term_4890 := _t1542
	p.consumeLiteral(")")
	_t1543 := &pb.RelTerm{}
	_t1543.RelTermType = &pb.RelTerm_Term{Term: term888}
	_t1544 := &pb.RelTerm{}
	_t1544.RelTermType = &pb.RelTerm_Term{Term: term_3889}
	_t1545 := &pb.RelTerm{}
	_t1545.RelTermType = &pb.RelTerm_Term{Term: term_4890}
	_t1546 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1543, _t1544, _t1545}}
	result892 := _t1546
	p.recordSpan(int(span_start891))
	return result892
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1547 := p.parse_term()
	term893 := _t1547
	_t1548 := p.parse_term()
	term_3894 := _t1548
	_t1549 := p.parse_term()
	term_4895 := _t1549
	p.consumeLiteral(")")
	_t1550 := &pb.RelTerm{}
	_t1550.RelTermType = &pb.RelTerm_Term{Term: term893}
	_t1551 := &pb.RelTerm{}
	_t1551.RelTermType = &pb.RelTerm_Term{Term: term_3894}
	_t1552 := &pb.RelTerm{}
	_t1552.RelTermType = &pb.RelTerm_Term{Term: term_4895}
	_t1553 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1550, _t1551, _t1552}}
	result897 := _t1553
	p.recordSpan(int(span_start896))
	return result897
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1554 := p.parse_term()
	term898 := _t1554
	_t1555 := p.parse_term()
	term_3899 := _t1555
	_t1556 := p.parse_term()
	term_4900 := _t1556
	p.consumeLiteral(")")
	_t1557 := &pb.RelTerm{}
	_t1557.RelTermType = &pb.RelTerm_Term{Term: term898}
	_t1558 := &pb.RelTerm{}
	_t1558.RelTermType = &pb.RelTerm_Term{Term: term_3899}
	_t1559 := &pb.RelTerm{}
	_t1559.RelTermType = &pb.RelTerm_Term{Term: term_4900}
	_t1560 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1557, _t1558, _t1559}}
	result902 := _t1560
	p.recordSpan(int(span_start901))
	return result902
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start906 := int64(p.spanStart())
	var _t1561 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1561 = 1
	} else {
		var _t1562 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1562 = 1
		} else {
			var _t1563 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1563 = 1
			} else {
				var _t1564 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1564 = 1
				} else {
					var _t1565 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1565 = 0
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
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1569 = 1
									} else {
										var _t1570 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1570 = 1
										} else {
											var _t1571 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1571 = 1
											} else {
												var _t1572 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1572 = 1
												} else {
													_t1572 = -1
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
	prediction903 := _t1561
	var _t1573 *pb.RelTerm
	if prediction903 == 1 {
		_t1574 := p.parse_term()
		term905 := _t1574
		_t1575 := &pb.RelTerm{}
		_t1575.RelTermType = &pb.RelTerm_Term{Term: term905}
		_t1573 = _t1575
	} else {
		var _t1576 *pb.RelTerm
		if prediction903 == 0 {
			_t1577 := p.parse_specialized_value()
			specialized_value904 := _t1577
			_t1578 := &pb.RelTerm{}
			_t1578.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value904}
			_t1576 = _t1578
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1573 = _t1576
	}
	result907 := _t1573
	p.recordSpan(int(span_start906))
	return result907
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1579 := p.parse_value()
	value908 := _t1579
	result910 := value908
	p.recordSpan(int(span_start909))
	return result910
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start916 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1580 := p.parse_name()
	name911 := _t1580
	xs912 := []*pb.RelTerm{}
	cond913 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond913 {
		_t1581 := p.parse_rel_term()
		item914 := _t1581
		xs912 = append(xs912, item914)
		cond913 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms915 := xs912
	p.consumeLiteral(")")
	_t1582 := &pb.RelAtom{Name: name911, Terms: rel_terms915}
	result917 := _t1582
	p.recordSpan(int(span_start916))
	return result917
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1583 := p.parse_term()
	term918 := _t1583
	_t1584 := p.parse_term()
	term_3919 := _t1584
	p.consumeLiteral(")")
	_t1585 := &pb.Cast{Input: term918, Result: term_3919}
	result921 := _t1585
	p.recordSpan(int(span_start920))
	return result921
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	span_start926 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs922 := []*pb.Attribute{}
	cond923 := p.matchLookaheadLiteral("(", 0)
	for cond923 {
		_t1586 := p.parse_attribute()
		item924 := _t1586
		xs922 = append(xs922, item924)
		cond923 = p.matchLookaheadLiteral("(", 0)
	}
	attributes925 := xs922
	p.consumeLiteral(")")
	result927 := attributes925
	p.recordSpan(int(span_start926))
	return result927
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start933 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1587 := p.parse_name()
	name928 := _t1587
	xs929 := []*pb.Value{}
	cond930 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond930 {
		_t1588 := p.parse_value()
		item931 := _t1588
		xs929 = append(xs929, item931)
		cond930 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values932 := xs929
	p.consumeLiteral(")")
	_t1589 := &pb.Attribute{Name: name928, Args: values932}
	result934 := _t1589
	p.recordSpan(int(span_start933))
	return result934
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start940 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs935 := []*pb.RelationId{}
	cond936 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond936 {
		_t1590 := p.parse_relation_id()
		item937 := _t1590
		xs935 = append(xs935, item937)
		cond936 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids938 := xs935
	_t1591 := p.parse_script()
	script939 := _t1591
	p.consumeLiteral(")")
	_t1592 := &pb.Algorithm{Global: relation_ids938, Body: script939}
	result941 := _t1592
	p.recordSpan(int(span_start940))
	return result941
}

func (p *Parser) parse_script() *pb.Script {
	span_start946 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs942 := []*pb.Construct{}
	cond943 := p.matchLookaheadLiteral("(", 0)
	for cond943 {
		_t1593 := p.parse_construct()
		item944 := _t1593
		xs942 = append(xs942, item944)
		cond943 = p.matchLookaheadLiteral("(", 0)
	}
	constructs945 := xs942
	p.consumeLiteral(")")
	_t1594 := &pb.Script{Constructs: constructs945}
	result947 := _t1594
	p.recordSpan(int(span_start946))
	return result947
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start951 := int64(p.spanStart())
	var _t1595 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1596 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1596 = 1
		} else {
			var _t1597 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1597 = 1
			} else {
				var _t1598 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1598 = 1
				} else {
					var _t1599 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1599 = 0
					} else {
						var _t1600 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1600 = 1
						} else {
							var _t1601 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1601 = 1
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
		}
		_t1595 = _t1596
	} else {
		_t1595 = -1
	}
	prediction948 := _t1595
	var _t1602 *pb.Construct
	if prediction948 == 1 {
		_t1603 := p.parse_instruction()
		instruction950 := _t1603
		_t1604 := &pb.Construct{}
		_t1604.ConstructType = &pb.Construct_Instruction{Instruction: instruction950}
		_t1602 = _t1604
	} else {
		var _t1605 *pb.Construct
		if prediction948 == 0 {
			_t1606 := p.parse_loop()
			loop949 := _t1606
			_t1607 := &pb.Construct{}
			_t1607.ConstructType = &pb.Construct_Loop{Loop: loop949}
			_t1605 = _t1607
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1602 = _t1605
	}
	result952 := _t1602
	p.recordSpan(int(span_start951))
	return result952
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start955 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1608 := p.parse_init()
	init953 := _t1608
	_t1609 := p.parse_script()
	script954 := _t1609
	p.consumeLiteral(")")
	_t1610 := &pb.Loop{Init: init953, Body: script954}
	result956 := _t1610
	p.recordSpan(int(span_start955))
	return result956
}

func (p *Parser) parse_init() []*pb.Instruction {
	span_start961 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs957 := []*pb.Instruction{}
	cond958 := p.matchLookaheadLiteral("(", 0)
	for cond958 {
		_t1611 := p.parse_instruction()
		item959 := _t1611
		xs957 = append(xs957, item959)
		cond958 = p.matchLookaheadLiteral("(", 0)
	}
	instructions960 := xs957
	p.consumeLiteral(")")
	result962 := instructions960
	p.recordSpan(int(span_start961))
	return result962
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start969 := int64(p.spanStart())
	var _t1612 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1613 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1613 = 1
		} else {
			var _t1614 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1614 = 4
			} else {
				var _t1615 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1615 = 3
				} else {
					var _t1616 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1616 = 2
					} else {
						var _t1617 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1617 = 0
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
	} else {
		_t1612 = -1
	}
	prediction963 := _t1612
	var _t1618 *pb.Instruction
	if prediction963 == 4 {
		_t1619 := p.parse_monus_def()
		monus_def968 := _t1619
		_t1620 := &pb.Instruction{}
		_t1620.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def968}
		_t1618 = _t1620
	} else {
		var _t1621 *pb.Instruction
		if prediction963 == 3 {
			_t1622 := p.parse_monoid_def()
			monoid_def967 := _t1622
			_t1623 := &pb.Instruction{}
			_t1623.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def967}
			_t1621 = _t1623
		} else {
			var _t1624 *pb.Instruction
			if prediction963 == 2 {
				_t1625 := p.parse_break()
				break966 := _t1625
				_t1626 := &pb.Instruction{}
				_t1626.InstrType = &pb.Instruction_Break{Break: break966}
				_t1624 = _t1626
			} else {
				var _t1627 *pb.Instruction
				if prediction963 == 1 {
					_t1628 := p.parse_upsert()
					upsert965 := _t1628
					_t1629 := &pb.Instruction{}
					_t1629.InstrType = &pb.Instruction_Upsert{Upsert: upsert965}
					_t1627 = _t1629
				} else {
					var _t1630 *pb.Instruction
					if prediction963 == 0 {
						_t1631 := p.parse_assign()
						assign964 := _t1631
						_t1632 := &pb.Instruction{}
						_t1632.InstrType = &pb.Instruction_Assign{Assign: assign964}
						_t1630 = _t1632
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1627 = _t1630
				}
				_t1624 = _t1627
			}
			_t1621 = _t1624
		}
		_t1618 = _t1621
	}
	result970 := _t1618
	p.recordSpan(int(span_start969))
	return result970
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1633 := p.parse_relation_id()
	relation_id971 := _t1633
	_t1634 := p.parse_abstraction()
	abstraction972 := _t1634
	var _t1635 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1636 := p.parse_attrs()
		_t1635 = _t1636
	}
	attrs973 := _t1635
	p.consumeLiteral(")")
	_t1637 := attrs973
	if attrs973 == nil {
		_t1637 = []*pb.Attribute{}
	}
	_t1638 := &pb.Assign{Name: relation_id971, Body: abstraction972, Attrs: _t1637}
	result975 := _t1638
	p.recordSpan(int(span_start974))
	return result975
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start979 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1639 := p.parse_relation_id()
	relation_id976 := _t1639
	_t1640 := p.parse_abstraction_with_arity()
	abstraction_with_arity977 := _t1640
	var _t1641 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1642 := p.parse_attrs()
		_t1641 = _t1642
	}
	attrs978 := _t1641
	p.consumeLiteral(")")
	_t1643 := attrs978
	if attrs978 == nil {
		_t1643 = []*pb.Attribute{}
	}
	_t1644 := &pb.Upsert{Name: relation_id976, Body: abstraction_with_arity977[0].(*pb.Abstraction), Attrs: _t1643, ValueArity: abstraction_with_arity977[1].(int64)}
	result980 := _t1644
	p.recordSpan(int(span_start979))
	return result980
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	span_start983 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1645 := p.parse_bindings()
	bindings981 := _t1645
	_t1646 := p.parse_formula()
	formula982 := _t1646
	p.consumeLiteral(")")
	_t1647 := &pb.Abstraction{Vars: listConcat(bindings981[0].([]*pb.Binding), bindings981[1].([]*pb.Binding)), Value: formula982}
	result984 := []interface{}{_t1647, int64(len(bindings981[1].([]*pb.Binding)))}
	p.recordSpan(int(span_start983))
	return result984
}

func (p *Parser) parse_break() *pb.Break {
	span_start988 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1648 := p.parse_relation_id()
	relation_id985 := _t1648
	_t1649 := p.parse_abstraction()
	abstraction986 := _t1649
	var _t1650 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1651 := p.parse_attrs()
		_t1650 = _t1651
	}
	attrs987 := _t1650
	p.consumeLiteral(")")
	_t1652 := attrs987
	if attrs987 == nil {
		_t1652 = []*pb.Attribute{}
	}
	_t1653 := &pb.Break{Name: relation_id985, Body: abstraction986, Attrs: _t1652}
	result989 := _t1653
	p.recordSpan(int(span_start988))
	return result989
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start994 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1654 := p.parse_monoid()
	monoid990 := _t1654
	_t1655 := p.parse_relation_id()
	relation_id991 := _t1655
	_t1656 := p.parse_abstraction_with_arity()
	abstraction_with_arity992 := _t1656
	var _t1657 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1658 := p.parse_attrs()
		_t1657 = _t1658
	}
	attrs993 := _t1657
	p.consumeLiteral(")")
	_t1659 := attrs993
	if attrs993 == nil {
		_t1659 = []*pb.Attribute{}
	}
	_t1660 := &pb.MonoidDef{Monoid: monoid990, Name: relation_id991, Body: abstraction_with_arity992[0].(*pb.Abstraction), Attrs: _t1659, ValueArity: abstraction_with_arity992[1].(int64)}
	result995 := _t1660
	p.recordSpan(int(span_start994))
	return result995
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1001 := int64(p.spanStart())
	var _t1661 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1662 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1662 = 3
		} else {
			var _t1663 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1663 = 0
			} else {
				var _t1664 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1664 = 1
				} else {
					var _t1665 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1665 = 2
					} else {
						_t1665 = -1
					}
					_t1664 = _t1665
				}
				_t1663 = _t1664
			}
			_t1662 = _t1663
		}
		_t1661 = _t1662
	} else {
		_t1661 = -1
	}
	prediction996 := _t1661
	var _t1666 *pb.Monoid
	if prediction996 == 3 {
		_t1667 := p.parse_sum_monoid()
		sum_monoid1000 := _t1667
		_t1668 := &pb.Monoid{}
		_t1668.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1000}
		_t1666 = _t1668
	} else {
		var _t1669 *pb.Monoid
		if prediction996 == 2 {
			_t1670 := p.parse_max_monoid()
			max_monoid999 := _t1670
			_t1671 := &pb.Monoid{}
			_t1671.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid999}
			_t1669 = _t1671
		} else {
			var _t1672 *pb.Monoid
			if prediction996 == 1 {
				_t1673 := p.parse_min_monoid()
				min_monoid998 := _t1673
				_t1674 := &pb.Monoid{}
				_t1674.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid998}
				_t1672 = _t1674
			} else {
				var _t1675 *pb.Monoid
				if prediction996 == 0 {
					_t1676 := p.parse_or_monoid()
					or_monoid997 := _t1676
					_t1677 := &pb.Monoid{}
					_t1677.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid997}
					_t1675 = _t1677
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1672 = _t1675
			}
			_t1669 = _t1672
		}
		_t1666 = _t1669
	}
	result1002 := _t1666
	p.recordSpan(int(span_start1001))
	return result1002
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1003 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1678 := &pb.OrMonoid{}
	result1004 := _t1678
	p.recordSpan(int(span_start1003))
	return result1004
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1006 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1679 := p.parse_type()
	type1005 := _t1679
	p.consumeLiteral(")")
	_t1680 := &pb.MinMonoid{Type: type1005}
	result1007 := _t1680
	p.recordSpan(int(span_start1006))
	return result1007
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1009 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1681 := p.parse_type()
	type1008 := _t1681
	p.consumeLiteral(")")
	_t1682 := &pb.MaxMonoid{Type: type1008}
	result1010 := _t1682
	p.recordSpan(int(span_start1009))
	return result1010
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1012 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1683 := p.parse_type()
	type1011 := _t1683
	p.consumeLiteral(")")
	_t1684 := &pb.SumMonoid{Type: type1011}
	result1013 := _t1684
	p.recordSpan(int(span_start1012))
	return result1013
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1685 := p.parse_monoid()
	monoid1014 := _t1685
	_t1686 := p.parse_relation_id()
	relation_id1015 := _t1686
	_t1687 := p.parse_abstraction_with_arity()
	abstraction_with_arity1016 := _t1687
	var _t1688 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1689 := p.parse_attrs()
		_t1688 = _t1689
	}
	attrs1017 := _t1688
	p.consumeLiteral(")")
	_t1690 := attrs1017
	if attrs1017 == nil {
		_t1690 = []*pb.Attribute{}
	}
	_t1691 := &pb.MonusDef{Monoid: monoid1014, Name: relation_id1015, Body: abstraction_with_arity1016[0].(*pb.Abstraction), Attrs: _t1690, ValueArity: abstraction_with_arity1016[1].(int64)}
	result1019 := _t1691
	p.recordSpan(int(span_start1018))
	return result1019
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1692 := p.parse_relation_id()
	relation_id1020 := _t1692
	_t1693 := p.parse_abstraction()
	abstraction1021 := _t1693
	_t1694 := p.parse_functional_dependency_keys()
	functional_dependency_keys1022 := _t1694
	_t1695 := p.parse_functional_dependency_values()
	functional_dependency_values1023 := _t1695
	p.consumeLiteral(")")
	_t1696 := &pb.FunctionalDependency{Guard: abstraction1021, Keys: functional_dependency_keys1022, Values: functional_dependency_values1023}
	_t1697 := &pb.Constraint{Name: relation_id1020}
	_t1697.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1696}
	result1025 := _t1697
	p.recordSpan(int(span_start1024))
	return result1025
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	span_start1030 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1026 := []*pb.Var{}
	cond1027 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1027 {
		_t1698 := p.parse_var()
		item1028 := _t1698
		xs1026 = append(xs1026, item1028)
		cond1027 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1029 := xs1026
	p.consumeLiteral(")")
	result1031 := vars1029
	p.recordSpan(int(span_start1030))
	return result1031
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1032 := []*pb.Var{}
	cond1033 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1033 {
		_t1699 := p.parse_var()
		item1034 := _t1699
		xs1032 = append(xs1032, item1034)
		cond1033 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1035 := xs1032
	p.consumeLiteral(")")
	result1037 := vars1035
	p.recordSpan(int(span_start1036))
	return result1037
}

func (p *Parser) parse_data() *pb.Data {
	span_start1042 := int64(p.spanStart())
	var _t1700 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1701 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1701 = 0
		} else {
			var _t1702 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1702 = 2
			} else {
				var _t1703 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1703 = 1
				} else {
					_t1703 = -1
				}
				_t1702 = _t1703
			}
			_t1701 = _t1702
		}
		_t1700 = _t1701
	} else {
		_t1700 = -1
	}
	prediction1038 := _t1700
	var _t1704 *pb.Data
	if prediction1038 == 2 {
		_t1705 := p.parse_csv_data()
		csv_data1041 := _t1705
		_t1706 := &pb.Data{}
		_t1706.DataType = &pb.Data_CsvData{CsvData: csv_data1041}
		_t1704 = _t1706
	} else {
		var _t1707 *pb.Data
		if prediction1038 == 1 {
			_t1708 := p.parse_betree_relation()
			betree_relation1040 := _t1708
			_t1709 := &pb.Data{}
			_t1709.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1040}
			_t1707 = _t1709
		} else {
			var _t1710 *pb.Data
			if prediction1038 == 0 {
				_t1711 := p.parse_rel_edb()
				rel_edb1039 := _t1711
				_t1712 := &pb.Data{}
				_t1712.DataType = &pb.Data_RelEdb{RelEdb: rel_edb1039}
				_t1710 = _t1712
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1707 = _t1710
		}
		_t1704 = _t1707
	}
	result1043 := _t1704
	p.recordSpan(int(span_start1042))
	return result1043
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	span_start1047 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1713 := p.parse_relation_id()
	relation_id1044 := _t1713
	_t1714 := p.parse_rel_edb_path()
	rel_edb_path1045 := _t1714
	_t1715 := p.parse_rel_edb_types()
	rel_edb_types1046 := _t1715
	p.consumeLiteral(")")
	_t1716 := &pb.RelEDB{TargetId: relation_id1044, Path: rel_edb_path1045, Types: rel_edb_types1046}
	result1048 := _t1716
	p.recordSpan(int(span_start1047))
	return result1048
}

func (p *Parser) parse_rel_edb_path() []string {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1049 := []string{}
	cond1050 := p.matchLookaheadTerminal("STRING", 0)
	for cond1050 {
		item1051 := p.consumeTerminal("STRING").Value.str
		xs1049 = append(xs1049, item1051)
		cond1050 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1052 := xs1049
	p.consumeLiteral("]")
	result1054 := strings1052
	p.recordSpan(int(span_start1053))
	return result1054
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	span_start1059 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1055 := []*pb.Type{}
	cond1056 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1056 {
		_t1717 := p.parse_type()
		item1057 := _t1717
		xs1055 = append(xs1055, item1057)
		cond1056 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1058 := xs1055
	p.consumeLiteral("]")
	result1060 := types1058
	p.recordSpan(int(span_start1059))
	return result1060
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1063 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1718 := p.parse_relation_id()
	relation_id1061 := _t1718
	_t1719 := p.parse_betree_info()
	betree_info1062 := _t1719
	p.consumeLiteral(")")
	_t1720 := &pb.BeTreeRelation{Name: relation_id1061, RelationInfo: betree_info1062}
	result1064 := _t1720
	p.recordSpan(int(span_start1063))
	return result1064
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1721 := p.parse_betree_info_key_types()
	betree_info_key_types1065 := _t1721
	_t1722 := p.parse_betree_info_value_types()
	betree_info_value_types1066 := _t1722
	_t1723 := p.parse_config_dict()
	config_dict1067 := _t1723
	p.consumeLiteral(")")
	_t1724 := p.construct_betree_info(betree_info_key_types1065, betree_info_value_types1066, config_dict1067)
	result1069 := _t1724
	p.recordSpan(int(span_start1068))
	return result1069
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1070 := []*pb.Type{}
	cond1071 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1071 {
		_t1725 := p.parse_type()
		item1072 := _t1725
		xs1070 = append(xs1070, item1072)
		cond1071 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1073 := xs1070
	p.consumeLiteral(")")
	result1075 := types1073
	p.recordSpan(int(span_start1074))
	return result1075
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1076 := []*pb.Type{}
	cond1077 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1077 {
		_t1726 := p.parse_type()
		item1078 := _t1726
		xs1076 = append(xs1076, item1078)
		cond1077 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1079 := xs1076
	p.consumeLiteral(")")
	result1081 := types1079
	p.recordSpan(int(span_start1080))
	return result1081
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1727 := p.parse_csvlocator()
	csvlocator1082 := _t1727
	_t1728 := p.parse_csv_config()
	csv_config1083 := _t1728
	_t1729 := p.parse_csv_columns()
	csv_columns1084 := _t1729
	_t1730 := p.parse_csv_asof()
	csv_asof1085 := _t1730
	p.consumeLiteral(")")
	_t1731 := &pb.CSVData{Locator: csvlocator1082, Config: csv_config1083, Columns: csv_columns1084, Asof: csv_asof1085}
	result1087 := _t1731
	p.recordSpan(int(span_start1086))
	return result1087
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1090 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1732 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1733 := p.parse_csv_locator_paths()
		_t1732 = _t1733
	}
	csv_locator_paths1088 := _t1732
	var _t1734 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1735 := p.parse_csv_locator_inline_data()
		_t1734 = ptr(_t1735)
	}
	csv_locator_inline_data1089 := _t1734
	p.consumeLiteral(")")
	_t1736 := csv_locator_paths1088
	if csv_locator_paths1088 == nil {
		_t1736 = []string{}
	}
	_t1737 := &pb.CSVLocator{Paths: _t1736, InlineData: []byte(deref(csv_locator_inline_data1089, ""))}
	result1091 := _t1737
	p.recordSpan(int(span_start1090))
	return result1091
}

func (p *Parser) parse_csv_locator_paths() []string {
	span_start1096 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1092 := []string{}
	cond1093 := p.matchLookaheadTerminal("STRING", 0)
	for cond1093 {
		item1094 := p.consumeTerminal("STRING").Value.str
		xs1092 = append(xs1092, item1094)
		cond1093 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1095 := xs1092
	p.consumeLiteral(")")
	result1097 := strings1095
	p.recordSpan(int(span_start1096))
	return result1097
}

func (p *Parser) parse_csv_locator_inline_data() string {
	span_start1099 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1098 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1100 := string1098
	p.recordSpan(int(span_start1099))
	return result1100
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1102 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1738 := p.parse_config_dict()
	config_dict1101 := _t1738
	p.consumeLiteral(")")
	_t1739 := p.construct_csv_config(config_dict1101)
	result1103 := _t1739
	p.recordSpan(int(span_start1102))
	return result1103
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	span_start1108 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1104 := []*pb.CSVColumn{}
	cond1105 := p.matchLookaheadLiteral("(", 0)
	for cond1105 {
		_t1740 := p.parse_csv_column()
		item1106 := _t1740
		xs1104 = append(xs1104, item1106)
		cond1105 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns1107 := xs1104
	p.consumeLiteral(")")
	result1109 := csv_columns1107
	p.recordSpan(int(span_start1108))
	return result1109
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	span_start1116 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1110 := p.consumeTerminal("STRING").Value.str
	_t1741 := p.parse_relation_id()
	relation_id1111 := _t1741
	p.consumeLiteral("[")
	xs1112 := []*pb.Type{}
	cond1113 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1113 {
		_t1742 := p.parse_type()
		item1114 := _t1742
		xs1112 = append(xs1112, item1114)
		cond1113 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1115 := xs1112
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1743 := &pb.CSVColumn{ColumnName: string1110, TargetId: relation_id1111, Types: types1115}
	result1117 := _t1743
	p.recordSpan(int(span_start1116))
	return result1117
}

func (p *Parser) parse_csv_asof() string {
	span_start1119 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1118 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1120 := string1118
	p.recordSpan(int(span_start1119))
	return result1120
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1122 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1744 := p.parse_fragment_id()
	fragment_id1121 := _t1744
	p.consumeLiteral(")")
	_t1745 := &pb.Undefine{FragmentId: fragment_id1121}
	result1123 := _t1745
	p.recordSpan(int(span_start1122))
	return result1123
}

func (p *Parser) parse_context() *pb.Context {
	span_start1128 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1124 := []*pb.RelationId{}
	cond1125 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1125 {
		_t1746 := p.parse_relation_id()
		item1126 := _t1746
		xs1124 = append(xs1124, item1126)
		cond1125 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1127 := xs1124
	p.consumeLiteral(")")
	_t1747 := &pb.Context{Relations: relation_ids1127}
	result1129 := _t1747
	p.recordSpan(int(span_start1128))
	return result1129
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1132 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1748 := p.parse_rel_edb_path()
	rel_edb_path1130 := _t1748
	_t1749 := p.parse_relation_id()
	relation_id1131 := _t1749
	p.consumeLiteral(")")
	_t1750 := &pb.Snapshot{DestinationPath: rel_edb_path1130, SourceRelation: relation_id1131}
	result1133 := _t1750
	p.recordSpan(int(span_start1132))
	return result1133
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	span_start1138 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1134 := []*pb.Read{}
	cond1135 := p.matchLookaheadLiteral("(", 0)
	for cond1135 {
		_t1751 := p.parse_read()
		item1136 := _t1751
		xs1134 = append(xs1134, item1136)
		cond1135 = p.matchLookaheadLiteral("(", 0)
	}
	reads1137 := xs1134
	p.consumeLiteral(")")
	result1139 := reads1137
	p.recordSpan(int(span_start1138))
	return result1139
}

func (p *Parser) parse_read() *pb.Read {
	span_start1146 := int64(p.spanStart())
	var _t1752 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1753 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1753 = 2
		} else {
			var _t1754 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1754 = 1
			} else {
				var _t1755 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1755 = 4
				} else {
					var _t1756 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1756 = 0
					} else {
						var _t1757 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1757 = 3
						} else {
							_t1757 = -1
						}
						_t1756 = _t1757
					}
					_t1755 = _t1756
				}
				_t1754 = _t1755
			}
			_t1753 = _t1754
		}
		_t1752 = _t1753
	} else {
		_t1752 = -1
	}
	prediction1140 := _t1752
	var _t1758 *pb.Read
	if prediction1140 == 4 {
		_t1759 := p.parse_export()
		export1145 := _t1759
		_t1760 := &pb.Read{}
		_t1760.ReadType = &pb.Read_Export{Export: export1145}
		_t1758 = _t1760
	} else {
		var _t1761 *pb.Read
		if prediction1140 == 3 {
			_t1762 := p.parse_abort()
			abort1144 := _t1762
			_t1763 := &pb.Read{}
			_t1763.ReadType = &pb.Read_Abort{Abort: abort1144}
			_t1761 = _t1763
		} else {
			var _t1764 *pb.Read
			if prediction1140 == 2 {
				_t1765 := p.parse_what_if()
				what_if1143 := _t1765
				_t1766 := &pb.Read{}
				_t1766.ReadType = &pb.Read_WhatIf{WhatIf: what_if1143}
				_t1764 = _t1766
			} else {
				var _t1767 *pb.Read
				if prediction1140 == 1 {
					_t1768 := p.parse_output()
					output1142 := _t1768
					_t1769 := &pb.Read{}
					_t1769.ReadType = &pb.Read_Output{Output: output1142}
					_t1767 = _t1769
				} else {
					var _t1770 *pb.Read
					if prediction1140 == 0 {
						_t1771 := p.parse_demand()
						demand1141 := _t1771
						_t1772 := &pb.Read{}
						_t1772.ReadType = &pb.Read_Demand{Demand: demand1141}
						_t1770 = _t1772
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1767 = _t1770
				}
				_t1764 = _t1767
			}
			_t1761 = _t1764
		}
		_t1758 = _t1761
	}
	result1147 := _t1758
	p.recordSpan(int(span_start1146))
	return result1147
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1149 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1773 := p.parse_relation_id()
	relation_id1148 := _t1773
	p.consumeLiteral(")")
	_t1774 := &pb.Demand{RelationId: relation_id1148}
	result1150 := _t1774
	p.recordSpan(int(span_start1149))
	return result1150
}

func (p *Parser) parse_output() *pb.Output {
	span_start1153 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1775 := p.parse_name()
	name1151 := _t1775
	_t1776 := p.parse_relation_id()
	relation_id1152 := _t1776
	p.consumeLiteral(")")
	_t1777 := &pb.Output{Name: name1151, RelationId: relation_id1152}
	result1154 := _t1777
	p.recordSpan(int(span_start1153))
	return result1154
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1157 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1778 := p.parse_name()
	name1155 := _t1778
	_t1779 := p.parse_epoch()
	epoch1156 := _t1779
	p.consumeLiteral(")")
	_t1780 := &pb.WhatIf{Branch: name1155, Epoch: epoch1156}
	result1158 := _t1780
	p.recordSpan(int(span_start1157))
	return result1158
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1161 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1781 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1782 := p.parse_name()
		_t1781 = ptr(_t1782)
	}
	name1159 := _t1781
	_t1783 := p.parse_relation_id()
	relation_id1160 := _t1783
	p.consumeLiteral(")")
	_t1784 := &pb.Abort{Name: deref(name1159, "abort"), RelationId: relation_id1160}
	result1162 := _t1784
	p.recordSpan(int(span_start1161))
	return result1162
}

func (p *Parser) parse_export() *pb.Export {
	span_start1164 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1785 := p.parse_export_csv_config()
	export_csv_config1163 := _t1785
	p.consumeLiteral(")")
	_t1786 := &pb.Export{}
	_t1786.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1163}
	result1165 := _t1786
	p.recordSpan(int(span_start1164))
	return result1165
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1169 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1787 := p.parse_export_csv_path()
	export_csv_path1166 := _t1787
	_t1788 := p.parse_export_csv_columns()
	export_csv_columns1167 := _t1788
	_t1789 := p.parse_config_dict()
	config_dict1168 := _t1789
	p.consumeLiteral(")")
	_t1790 := p.export_csv_config(export_csv_path1166, export_csv_columns1167, config_dict1168)
	result1170 := _t1790
	p.recordSpan(int(span_start1169))
	return result1170
}

func (p *Parser) parse_export_csv_path() string {
	span_start1172 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1171 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1173 := string1171
	p.recordSpan(int(span_start1172))
	return result1173
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	span_start1178 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1174 := []*pb.ExportCSVColumn{}
	cond1175 := p.matchLookaheadLiteral("(", 0)
	for cond1175 {
		_t1791 := p.parse_export_csv_column()
		item1176 := _t1791
		xs1174 = append(xs1174, item1176)
		cond1175 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1177 := xs1174
	p.consumeLiteral(")")
	result1179 := export_csv_columns1177
	p.recordSpan(int(span_start1178))
	return result1179
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1182 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1180 := p.consumeTerminal("STRING").Value.str
	_t1792 := p.parse_relation_id()
	relation_id1181 := _t1792
	p.consumeLiteral(")")
	_t1793 := &pb.ExportCSVColumn{ColumnName: string1180, ColumnData: relation_id1181}
	result1183 := _t1793
	p.recordSpan(int(span_start1182))
	return result1183
}


// Parse parses the input string and returns (result, provenance, error).
func Parse(input string) (result *pb.Transaction, provenance map[string]Span, err error) {
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
