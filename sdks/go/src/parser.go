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
	path              []int
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
		path:              nil,
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

func (p *Parser) pushPath(n int) {
	p.path = append(p.path, n)
}

func (p *Parser) popPath() {
	p.path = p.path[:len(p.path)-1]
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
	// Build comma-separated path key
	key := ""
	for i, v := range p.path {
		if i > 0 {
			key += ","
		}
		key += fmt.Sprintf("%d", v)
	}
	p.Provenance[key] = s
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
	var _t1922 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1922
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1923 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1923
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1924 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1924
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1925 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1925
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1926 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1926
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1927 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1927
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1928 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1928
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1929 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1929
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1930 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1930
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1931 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1931
	_t1932 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1932
	_t1933 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1933
	_t1934 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1934
	_t1935 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1935
	_t1936 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1936
	_t1937 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1937
	_t1938 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1938
	_t1939 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1939
	_t1940 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1940
	_t1941 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1941
	_t1942 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1942
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1943 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1943
	_t1944 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1944
	_t1945 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1945
	_t1946 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1946
	_t1947 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1947
	_t1948 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1948
	_t1949 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1949
	_t1950 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1950
	_t1951 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1951
	_t1952 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1952.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1952.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1952
	_t1953 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1953
}

func (p *Parser) default_configure() *pb.Configure {
	_t1954 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1954
	_t1955 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1955
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
	_t1956 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1956
	_t1957 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1957
	_t1958 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1958
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1959 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1959
	_t1960 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1960
	_t1961 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1961
	_t1962 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1962
	_t1963 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1963
	_t1964 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1964
	_t1965 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1965
	_t1966 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1966
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start602 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	p.pushPath(int(2))
	var _t1312 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1313 := p.parse_configure()
		_t1312 = _t1313
	}
	configure592 := _t1312
	p.popPath()
	p.pushPath(int(3))
	var _t1314 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1315 := p.parse_sync()
		_t1314 = _t1315
	}
	sync593 := _t1314
	p.popPath()
	p.pushPath(int(1))
	xs598 := []*pb.Epoch{}
	cond599 := p.matchLookaheadLiteral("(", 0)
	idx600 := 0
	for cond599 {
		p.pushPath(int(idx600))
		_t1316 := p.parse_epoch()
		item601 := _t1316
		p.popPath()
		xs598 = append(xs598, item601)
		idx600 = (idx600 + 1)
		cond599 = p.matchLookaheadLiteral("(", 0)
	}
	epochs597 := xs598
	p.popPath()
	p.consumeLiteral(")")
	_t1317 := p.default_configure()
	_t1318 := configure592
	if configure592 == nil {
		_t1318 = _t1317
	}
	_t1319 := &pb.Transaction{Epochs: epochs597, Configure: _t1318, Sync: sync593}
	result603 := _t1319
	p.recordSpan(int(span_start602))
	return result603
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start605 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1320 := p.parse_config_dict()
	config_dict604 := _t1320
	p.consumeLiteral(")")
	_t1321 := p.construct_configure(config_dict604)
	result606 := _t1321
	p.recordSpan(int(span_start605))
	return result606
}

func (p *Parser) parse_config_dict() [][]interface{} {
	span_start615 := int64(p.spanStart())
	p.consumeLiteral("{")
	xs611 := [][]interface{}{}
	cond612 := p.matchLookaheadLiteral(":", 0)
	idx613 := 0
	for cond612 {
		p.pushPath(int(idx613))
		_t1322 := p.parse_config_key_value()
		item614 := _t1322
		p.popPath()
		xs611 = append(xs611, item614)
		idx613 = (idx613 + 1)
		cond612 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values610 := xs611
	p.consumeLiteral("}")
	result616 := config_key_values610
	p.recordSpan(int(span_start615))
	return result616
}

func (p *Parser) parse_config_key_value() []interface{} {
	span_start619 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol617 := p.consumeTerminal("SYMBOL").Value.str
	_t1323 := p.parse_value()
	value618 := _t1323
	result620 := []interface{}{symbol617, value618}
	p.recordSpan(int(span_start619))
	return result620
}

func (p *Parser) parse_value() *pb.Value {
	span_start631 := int64(p.spanStart())
	var _t1324 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1324 = 9
	} else {
		var _t1325 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1325 = 8
		} else {
			var _t1326 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1326 = 9
			} else {
				var _t1327 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1328 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1328 = 1
					} else {
						var _t1329 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1329 = 0
						} else {
							_t1329 = -1
						}
						_t1328 = _t1329
					}
					_t1327 = _t1328
				} else {
					var _t1330 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1330 = 5
					} else {
						var _t1331 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1331 = 2
						} else {
							var _t1332 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1332 = 6
							} else {
								var _t1333 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1333 = 3
								} else {
									var _t1334 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1334 = 4
									} else {
										var _t1335 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1335 = 7
										} else {
											_t1335 = -1
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
					_t1327 = _t1330
				}
				_t1326 = _t1327
			}
			_t1325 = _t1326
		}
		_t1324 = _t1325
	}
	prediction621 := _t1324
	var _t1336 *pb.Value
	if prediction621 == 9 {
		p.pushPath(int(10))
		_t1337 := p.parse_boolean_value()
		boolean_value630 := _t1337
		p.popPath()
		_t1338 := &pb.Value{}
		_t1338.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value630}
		_t1336 = _t1338
	} else {
		var _t1339 *pb.Value
		if prediction621 == 8 {
			p.consumeLiteral("missing")
			_t1340 := &pb.MissingValue{}
			_t1341 := &pb.Value{}
			_t1341.Value = &pb.Value_MissingValue{MissingValue: _t1340}
			_t1339 = _t1341
		} else {
			var _t1342 *pb.Value
			if prediction621 == 7 {
				decimal629 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1343 := &pb.Value{}
				_t1343.Value = &pb.Value_DecimalValue{DecimalValue: decimal629}
				_t1342 = _t1343
			} else {
				var _t1344 *pb.Value
				if prediction621 == 6 {
					int128628 := p.consumeTerminal("INT128").Value.int128
					_t1345 := &pb.Value{}
					_t1345.Value = &pb.Value_Int128Value{Int128Value: int128628}
					_t1344 = _t1345
				} else {
					var _t1346 *pb.Value
					if prediction621 == 5 {
						uint128627 := p.consumeTerminal("UINT128").Value.uint128
						_t1347 := &pb.Value{}
						_t1347.Value = &pb.Value_Uint128Value{Uint128Value: uint128627}
						_t1346 = _t1347
					} else {
						var _t1348 *pb.Value
						if prediction621 == 4 {
							float626 := p.consumeTerminal("FLOAT").Value.f64
							_t1349 := &pb.Value{}
							_t1349.Value = &pb.Value_FloatValue{FloatValue: float626}
							_t1348 = _t1349
						} else {
							var _t1350 *pb.Value
							if prediction621 == 3 {
								int625 := p.consumeTerminal("INT").Value.i64
								_t1351 := &pb.Value{}
								_t1351.Value = &pb.Value_IntValue{IntValue: int625}
								_t1350 = _t1351
							} else {
								var _t1352 *pb.Value
								if prediction621 == 2 {
									string624 := p.consumeTerminal("STRING").Value.str
									_t1353 := &pb.Value{}
									_t1353.Value = &pb.Value_StringValue{StringValue: string624}
									_t1352 = _t1353
								} else {
									var _t1354 *pb.Value
									if prediction621 == 1 {
										p.pushPath(int(8))
										_t1355 := p.parse_datetime()
										datetime623 := _t1355
										p.popPath()
										_t1356 := &pb.Value{}
										_t1356.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime623}
										_t1354 = _t1356
									} else {
										var _t1357 *pb.Value
										if prediction621 == 0 {
											p.pushPath(int(7))
											_t1358 := p.parse_date()
											date622 := _t1358
											p.popPath()
											_t1359 := &pb.Value{}
											_t1359.Value = &pb.Value_DateValue{DateValue: date622}
											_t1357 = _t1359
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1354 = _t1357
									}
									_t1352 = _t1354
								}
								_t1350 = _t1352
							}
							_t1348 = _t1350
						}
						_t1346 = _t1348
					}
					_t1344 = _t1346
				}
				_t1342 = _t1344
			}
			_t1339 = _t1342
		}
		_t1336 = _t1339
	}
	result632 := _t1336
	p.recordSpan(int(span_start631))
	return result632
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start636 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	p.pushPath(int(1))
	int633 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3634 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(3))
	int_4635 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.consumeLiteral(")")
	_t1360 := &pb.DateValue{Year: int32(int633), Month: int32(int_3634), Day: int32(int_4635)}
	result637 := _t1360
	p.recordSpan(int(span_start636))
	return result637
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start645 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	p.pushPath(int(1))
	int638 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3639 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(3))
	int_4640 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(4))
	int_5641 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(5))
	int_6642 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(6))
	int_7643 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(7))
	var _t1361 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1361 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8644 := _t1361
	p.popPath()
	p.consumeLiteral(")")
	_t1362 := &pb.DateTimeValue{Year: int32(int638), Month: int32(int_3639), Day: int32(int_4640), Hour: int32(int_5641), Minute: int32(int_6642), Second: int32(int_7643), Microsecond: int32(deref(int_8644, 0))}
	result646 := _t1362
	p.recordSpan(int(span_start645))
	return result646
}

func (p *Parser) parse_boolean_value() bool {
	span_start648 := int64(p.spanStart())
	var _t1363 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1363 = 0
	} else {
		var _t1364 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1364 = 1
		} else {
			_t1364 = -1
		}
		_t1363 = _t1364
	}
	prediction647 := _t1363
	var _t1365 bool
	if prediction647 == 1 {
		p.consumeLiteral("false")
		_t1365 = false
	} else {
		var _t1366 bool
		if prediction647 == 0 {
			p.consumeLiteral("true")
			_t1366 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1365 = _t1366
	}
	result649 := _t1365
	p.recordSpan(int(span_start648))
	return result649
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start658 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	p.pushPath(int(1))
	xs654 := []*pb.FragmentId{}
	cond655 := p.matchLookaheadLiteral(":", 0)
	idx656 := 0
	for cond655 {
		p.pushPath(int(idx656))
		_t1367 := p.parse_fragment_id()
		item657 := _t1367
		p.popPath()
		xs654 = append(xs654, item657)
		idx656 = (idx656 + 1)
		cond655 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids653 := xs654
	p.popPath()
	p.consumeLiteral(")")
	_t1368 := &pb.Sync{Fragments: fragment_ids653}
	result659 := _t1368
	p.recordSpan(int(span_start658))
	return result659
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start661 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol660 := p.consumeTerminal("SYMBOL").Value.str
	result662 := &pb.FragmentId{Id: []byte(symbol660)}
	p.recordSpan(int(span_start661))
	return result662
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start665 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	p.pushPath(int(1))
	var _t1369 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1370 := p.parse_epoch_writes()
		_t1369 = _t1370
	}
	epoch_writes663 := _t1369
	p.popPath()
	p.pushPath(int(2))
	var _t1371 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1372 := p.parse_epoch_reads()
		_t1371 = _t1372
	}
	epoch_reads664 := _t1371
	p.popPath()
	p.consumeLiteral(")")
	_t1373 := epoch_writes663
	if epoch_writes663 == nil {
		_t1373 = []*pb.Write{}
	}
	_t1374 := epoch_reads664
	if epoch_reads664 == nil {
		_t1374 = []*pb.Read{}
	}
	_t1375 := &pb.Epoch{Writes: _t1373, Reads: _t1374}
	result666 := _t1375
	p.recordSpan(int(span_start665))
	return result666
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	span_start675 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs671 := []*pb.Write{}
	cond672 := p.matchLookaheadLiteral("(", 0)
	idx673 := 0
	for cond672 {
		p.pushPath(int(idx673))
		_t1376 := p.parse_write()
		item674 := _t1376
		p.popPath()
		xs671 = append(xs671, item674)
		idx673 = (idx673 + 1)
		cond672 = p.matchLookaheadLiteral("(", 0)
	}
	writes670 := xs671
	p.consumeLiteral(")")
	result676 := writes670
	p.recordSpan(int(span_start675))
	return result676
}

func (p *Parser) parse_write() *pb.Write {
	span_start682 := int64(p.spanStart())
	var _t1377 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1378 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1378 = 1
		} else {
			var _t1379 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1379 = 3
			} else {
				var _t1380 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1380 = 0
				} else {
					var _t1381 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1381 = 2
					} else {
						_t1381 = -1
					}
					_t1380 = _t1381
				}
				_t1379 = _t1380
			}
			_t1378 = _t1379
		}
		_t1377 = _t1378
	} else {
		_t1377 = -1
	}
	prediction677 := _t1377
	var _t1382 *pb.Write
	if prediction677 == 3 {
		p.pushPath(int(5))
		_t1383 := p.parse_snapshot()
		snapshot681 := _t1383
		p.popPath()
		_t1384 := &pb.Write{}
		_t1384.WriteType = &pb.Write_Snapshot{Snapshot: snapshot681}
		_t1382 = _t1384
	} else {
		var _t1385 *pb.Write
		if prediction677 == 2 {
			p.pushPath(int(3))
			_t1386 := p.parse_context()
			context680 := _t1386
			p.popPath()
			_t1387 := &pb.Write{}
			_t1387.WriteType = &pb.Write_Context{Context: context680}
			_t1385 = _t1387
		} else {
			var _t1388 *pb.Write
			if prediction677 == 1 {
				p.pushPath(int(2))
				_t1389 := p.parse_undefine()
				undefine679 := _t1389
				p.popPath()
				_t1390 := &pb.Write{}
				_t1390.WriteType = &pb.Write_Undefine{Undefine: undefine679}
				_t1388 = _t1390
			} else {
				var _t1391 *pb.Write
				if prediction677 == 0 {
					p.pushPath(int(1))
					_t1392 := p.parse_define()
					define678 := _t1392
					p.popPath()
					_t1393 := &pb.Write{}
					_t1393.WriteType = &pb.Write_Define{Define: define678}
					_t1391 = _t1393
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1388 = _t1391
			}
			_t1385 = _t1388
		}
		_t1382 = _t1385
	}
	result683 := _t1382
	p.recordSpan(int(span_start682))
	return result683
}

func (p *Parser) parse_define() *pb.Define {
	span_start685 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	p.pushPath(int(1))
	_t1394 := p.parse_fragment()
	fragment684 := _t1394
	p.popPath()
	p.consumeLiteral(")")
	_t1395 := &pb.Define{Fragment: fragment684}
	result686 := _t1395
	p.recordSpan(int(span_start685))
	return result686
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start696 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1396 := p.parse_new_fragment_id()
	new_fragment_id687 := _t1396
	p.pushPath(int(2))
	xs692 := []*pb.Declaration{}
	cond693 := p.matchLookaheadLiteral("(", 0)
	idx694 := 0
	for cond693 {
		p.pushPath(int(idx694))
		_t1397 := p.parse_declaration()
		item695 := _t1397
		p.popPath()
		xs692 = append(xs692, item695)
		idx694 = (idx694 + 1)
		cond693 = p.matchLookaheadLiteral("(", 0)
	}
	declarations691 := xs692
	p.popPath()
	p.consumeLiteral(")")
	result697 := p.constructFragment(new_fragment_id687, declarations691)
	p.recordSpan(int(span_start696))
	return result697
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start699 := int64(p.spanStart())
	_t1398 := p.parse_fragment_id()
	fragment_id698 := _t1398
	p.startFragment(fragment_id698)
	result700 := fragment_id698
	p.recordSpan(int(span_start699))
	return result700
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start706 := int64(p.spanStart())
	var _t1399 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1400 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1400 = 3
		} else {
			var _t1401 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1401 = 2
			} else {
				var _t1402 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1402 = 0
				} else {
					var _t1403 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1403 = 3
					} else {
						var _t1404 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1404 = 3
						} else {
							var _t1405 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1405 = 1
							} else {
								_t1405 = -1
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
	} else {
		_t1399 = -1
	}
	prediction701 := _t1399
	var _t1406 *pb.Declaration
	if prediction701 == 3 {
		p.pushPath(int(4))
		_t1407 := p.parse_data()
		data705 := _t1407
		p.popPath()
		_t1408 := &pb.Declaration{}
		_t1408.DeclarationType = &pb.Declaration_Data{Data: data705}
		_t1406 = _t1408
	} else {
		var _t1409 *pb.Declaration
		if prediction701 == 2 {
			p.pushPath(int(3))
			_t1410 := p.parse_constraint()
			constraint704 := _t1410
			p.popPath()
			_t1411 := &pb.Declaration{}
			_t1411.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint704}
			_t1409 = _t1411
		} else {
			var _t1412 *pb.Declaration
			if prediction701 == 1 {
				p.pushPath(int(2))
				_t1413 := p.parse_algorithm()
				algorithm703 := _t1413
				p.popPath()
				_t1414 := &pb.Declaration{}
				_t1414.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm703}
				_t1412 = _t1414
			} else {
				var _t1415 *pb.Declaration
				if prediction701 == 0 {
					p.pushPath(int(1))
					_t1416 := p.parse_def()
					def702 := _t1416
					p.popPath()
					_t1417 := &pb.Declaration{}
					_t1417.DeclarationType = &pb.Declaration_Def{Def: def702}
					_t1415 = _t1417
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1412 = _t1415
			}
			_t1409 = _t1412
		}
		_t1406 = _t1409
	}
	result707 := _t1406
	p.recordSpan(int(span_start706))
	return result707
}

func (p *Parser) parse_def() *pb.Def {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	p.pushPath(int(1))
	_t1418 := p.parse_relation_id()
	relation_id708 := _t1418
	p.popPath()
	p.pushPath(int(2))
	_t1419 := p.parse_abstraction()
	abstraction709 := _t1419
	p.popPath()
	p.pushPath(int(3))
	var _t1420 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1421 := p.parse_attrs()
		_t1420 = _t1421
	}
	attrs710 := _t1420
	p.popPath()
	p.consumeLiteral(")")
	_t1422 := attrs710
	if attrs710 == nil {
		_t1422 = []*pb.Attribute{}
	}
	_t1423 := &pb.Def{Name: relation_id708, Body: abstraction709, Attrs: _t1422}
	result712 := _t1423
	p.recordSpan(int(span_start711))
	return result712
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start716 := int64(p.spanStart())
	var _t1424 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1424 = 0
	} else {
		var _t1425 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1425 = 1
		} else {
			_t1425 = -1
		}
		_t1424 = _t1425
	}
	prediction713 := _t1424
	var _t1426 *pb.RelationId
	if prediction713 == 1 {
		uint128715 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128715
		_t1426 = &pb.RelationId{IdLow: uint128715.Low, IdHigh: uint128715.High}
	} else {
		var _t1427 *pb.RelationId
		if prediction713 == 0 {
			p.consumeLiteral(":")
			symbol714 := p.consumeTerminal("SYMBOL").Value.str
			_t1427 = p.relationIdFromString(symbol714)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1426 = _t1427
	}
	result717 := _t1426
	p.recordSpan(int(span_start716))
	return result717
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start720 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1428 := p.parse_bindings()
	bindings718 := _t1428
	p.pushPath(int(2))
	_t1429 := p.parse_formula()
	formula719 := _t1429
	p.popPath()
	p.consumeLiteral(")")
	_t1430 := &pb.Abstraction{Vars: listConcat(bindings718[0].([]*pb.Binding), bindings718[1].([]*pb.Binding)), Value: formula719}
	result721 := _t1430
	p.recordSpan(int(span_start720))
	return result721
}

func (p *Parser) parse_bindings() []interface{} {
	span_start731 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs726 := []*pb.Binding{}
	cond727 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx728 := 0
	for cond727 {
		p.pushPath(int(idx728))
		_t1431 := p.parse_binding()
		item729 := _t1431
		p.popPath()
		xs726 = append(xs726, item729)
		idx728 = (idx728 + 1)
		cond727 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings725 := xs726
	var _t1432 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1433 := p.parse_value_bindings()
		_t1432 = _t1433
	}
	value_bindings730 := _t1432
	p.consumeLiteral("]")
	_t1434 := value_bindings730
	if value_bindings730 == nil {
		_t1434 = []*pb.Binding{}
	}
	result732 := []interface{}{bindings725, _t1434}
	p.recordSpan(int(span_start731))
	return result732
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start735 := int64(p.spanStart())
	symbol733 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	p.pushPath(int(2))
	_t1435 := p.parse_type()
	type734 := _t1435
	p.popPath()
	_t1436 := &pb.Var{Name: symbol733}
	_t1437 := &pb.Binding{Var: _t1436, Type: type734}
	result736 := _t1437
	p.recordSpan(int(span_start735))
	return result736
}

func (p *Parser) parse_type() *pb.Type {
	span_start749 := int64(p.spanStart())
	var _t1438 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1438 = 0
	} else {
		var _t1439 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1439 = 4
		} else {
			var _t1440 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1440 = 1
			} else {
				var _t1441 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1441 = 8
				} else {
					var _t1442 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1442 = 5
					} else {
						var _t1443 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1443 = 2
						} else {
							var _t1444 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1444 = 3
							} else {
								var _t1445 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1445 = 7
								} else {
									var _t1446 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1446 = 6
									} else {
										var _t1447 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1447 = 10
										} else {
											var _t1448 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1448 = 9
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
	prediction737 := _t1438
	var _t1449 *pb.Type
	if prediction737 == 10 {
		p.pushPath(int(11))
		_t1450 := p.parse_boolean_type()
		boolean_type748 := _t1450
		p.popPath()
		_t1451 := &pb.Type{}
		_t1451.Type = &pb.Type_BooleanType{BooleanType: boolean_type748}
		_t1449 = _t1451
	} else {
		var _t1452 *pb.Type
		if prediction737 == 9 {
			p.pushPath(int(10))
			_t1453 := p.parse_decimal_type()
			decimal_type747 := _t1453
			p.popPath()
			_t1454 := &pb.Type{}
			_t1454.Type = &pb.Type_DecimalType{DecimalType: decimal_type747}
			_t1452 = _t1454
		} else {
			var _t1455 *pb.Type
			if prediction737 == 8 {
				p.pushPath(int(9))
				_t1456 := p.parse_missing_type()
				missing_type746 := _t1456
				p.popPath()
				_t1457 := &pb.Type{}
				_t1457.Type = &pb.Type_MissingType{MissingType: missing_type746}
				_t1455 = _t1457
			} else {
				var _t1458 *pb.Type
				if prediction737 == 7 {
					p.pushPath(int(8))
					_t1459 := p.parse_datetime_type()
					datetime_type745 := _t1459
					p.popPath()
					_t1460 := &pb.Type{}
					_t1460.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type745}
					_t1458 = _t1460
				} else {
					var _t1461 *pb.Type
					if prediction737 == 6 {
						p.pushPath(int(7))
						_t1462 := p.parse_date_type()
						date_type744 := _t1462
						p.popPath()
						_t1463 := &pb.Type{}
						_t1463.Type = &pb.Type_DateType{DateType: date_type744}
						_t1461 = _t1463
					} else {
						var _t1464 *pb.Type
						if prediction737 == 5 {
							p.pushPath(int(6))
							_t1465 := p.parse_int128_type()
							int128_type743 := _t1465
							p.popPath()
							_t1466 := &pb.Type{}
							_t1466.Type = &pb.Type_Int128Type{Int128Type: int128_type743}
							_t1464 = _t1466
						} else {
							var _t1467 *pb.Type
							if prediction737 == 4 {
								p.pushPath(int(5))
								_t1468 := p.parse_uint128_type()
								uint128_type742 := _t1468
								p.popPath()
								_t1469 := &pb.Type{}
								_t1469.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type742}
								_t1467 = _t1469
							} else {
								var _t1470 *pb.Type
								if prediction737 == 3 {
									p.pushPath(int(4))
									_t1471 := p.parse_float_type()
									float_type741 := _t1471
									p.popPath()
									_t1472 := &pb.Type{}
									_t1472.Type = &pb.Type_FloatType{FloatType: float_type741}
									_t1470 = _t1472
								} else {
									var _t1473 *pb.Type
									if prediction737 == 2 {
										p.pushPath(int(3))
										_t1474 := p.parse_int_type()
										int_type740 := _t1474
										p.popPath()
										_t1475 := &pb.Type{}
										_t1475.Type = &pb.Type_IntType{IntType: int_type740}
										_t1473 = _t1475
									} else {
										var _t1476 *pb.Type
										if prediction737 == 1 {
											p.pushPath(int(2))
											_t1477 := p.parse_string_type()
											string_type739 := _t1477
											p.popPath()
											_t1478 := &pb.Type{}
											_t1478.Type = &pb.Type_StringType{StringType: string_type739}
											_t1476 = _t1478
										} else {
											var _t1479 *pb.Type
											if prediction737 == 0 {
												p.pushPath(int(1))
												_t1480 := p.parse_unspecified_type()
												unspecified_type738 := _t1480
												p.popPath()
												_t1481 := &pb.Type{}
												_t1481.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type738}
												_t1479 = _t1481
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t1476 = _t1479
										}
										_t1473 = _t1476
									}
									_t1470 = _t1473
								}
								_t1467 = _t1470
							}
							_t1464 = _t1467
						}
						_t1461 = _t1464
					}
					_t1458 = _t1461
				}
				_t1455 = _t1458
			}
			_t1452 = _t1455
		}
		_t1449 = _t1452
	}
	result750 := _t1449
	p.recordSpan(int(span_start749))
	return result750
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1482 := &pb.UnspecifiedType{}
	result752 := _t1482
	p.recordSpan(int(span_start751))
	return result752
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start753 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1483 := &pb.StringType{}
	result754 := _t1483
	p.recordSpan(int(span_start753))
	return result754
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1484 := &pb.IntType{}
	result756 := _t1484
	p.recordSpan(int(span_start755))
	return result756
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1485 := &pb.FloatType{}
	result758 := _t1485
	p.recordSpan(int(span_start757))
	return result758
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start759 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1486 := &pb.UInt128Type{}
	result760 := _t1486
	p.recordSpan(int(span_start759))
	return result760
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start761 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1487 := &pb.Int128Type{}
	result762 := _t1487
	p.recordSpan(int(span_start761))
	return result762
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1488 := &pb.DateType{}
	result764 := _t1488
	p.recordSpan(int(span_start763))
	return result764
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start765 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1489 := &pb.DateTimeType{}
	result766 := _t1489
	p.recordSpan(int(span_start765))
	return result766
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1490 := &pb.MissingType{}
	result768 := _t1490
	p.recordSpan(int(span_start767))
	return result768
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start771 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	p.pushPath(int(1))
	int769 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3770 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.consumeLiteral(")")
	_t1491 := &pb.DecimalType{Precision: int32(int769), Scale: int32(int_3770)}
	result772 := _t1491
	p.recordSpan(int(span_start771))
	return result772
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start773 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1492 := &pb.BooleanType{}
	result774 := _t1492
	p.recordSpan(int(span_start773))
	return result774
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	span_start783 := int64(p.spanStart())
	p.consumeLiteral("|")
	xs779 := []*pb.Binding{}
	cond780 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx781 := 0
	for cond780 {
		p.pushPath(int(idx781))
		_t1493 := p.parse_binding()
		item782 := _t1493
		p.popPath()
		xs779 = append(xs779, item782)
		idx781 = (idx781 + 1)
		cond780 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings778 := xs779
	result784 := bindings778
	p.recordSpan(int(span_start783))
	return result784
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start799 := int64(p.spanStart())
	var _t1494 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1495 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1495 = 0
		} else {
			var _t1496 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1496 = 11
			} else {
				var _t1497 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1497 = 3
				} else {
					var _t1498 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1498 = 10
					} else {
						var _t1499 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1499 = 9
						} else {
							var _t1500 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1500 = 5
							} else {
								var _t1501 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1501 = 6
								} else {
									var _t1502 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1502 = 7
									} else {
										var _t1503 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1503 = 1
										} else {
											var _t1504 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1504 = 2
											} else {
												var _t1505 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1505 = 12
												} else {
													var _t1506 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1506 = 8
													} else {
														var _t1507 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1507 = 4
														} else {
															var _t1508 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1508 = 10
															} else {
																var _t1509 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1509 = 10
																} else {
																	var _t1510 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1510 = 10
																	} else {
																		var _t1511 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1511 = 10
																		} else {
																			var _t1512 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1512 = 10
																			} else {
																				var _t1513 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1513 = 10
																				} else {
																					var _t1514 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1514 = 10
																					} else {
																						var _t1515 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1515 = 10
																						} else {
																							var _t1516 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1516 = 10
																							} else {
																								_t1516 = -1
																							}
																							_t1515 = _t1516
																						}
																						_t1514 = _t1515
																					}
																					_t1513 = _t1514
																				}
																				_t1512 = _t1513
																			}
																			_t1511 = _t1512
																		}
																		_t1510 = _t1511
																	}
																	_t1509 = _t1510
																}
																_t1508 = _t1509
															}
															_t1507 = _t1508
														}
														_t1506 = _t1507
													}
													_t1505 = _t1506
												}
												_t1504 = _t1505
											}
											_t1503 = _t1504
										}
										_t1502 = _t1503
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
		_t1494 = _t1495
	} else {
		_t1494 = -1
	}
	prediction785 := _t1494
	var _t1517 *pb.Formula
	if prediction785 == 12 {
		p.pushPath(int(11))
		_t1518 := p.parse_cast()
		cast798 := _t1518
		p.popPath()
		_t1519 := &pb.Formula{}
		_t1519.FormulaType = &pb.Formula_Cast{Cast: cast798}
		_t1517 = _t1519
	} else {
		var _t1520 *pb.Formula
		if prediction785 == 11 {
			p.pushPath(int(10))
			_t1521 := p.parse_rel_atom()
			rel_atom797 := _t1521
			p.popPath()
			_t1522 := &pb.Formula{}
			_t1522.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom797}
			_t1520 = _t1522
		} else {
			var _t1523 *pb.Formula
			if prediction785 == 10 {
				p.pushPath(int(9))
				_t1524 := p.parse_primitive()
				primitive796 := _t1524
				p.popPath()
				_t1525 := &pb.Formula{}
				_t1525.FormulaType = &pb.Formula_Primitive{Primitive: primitive796}
				_t1523 = _t1525
			} else {
				var _t1526 *pb.Formula
				if prediction785 == 9 {
					p.pushPath(int(8))
					_t1527 := p.parse_pragma()
					pragma795 := _t1527
					p.popPath()
					_t1528 := &pb.Formula{}
					_t1528.FormulaType = &pb.Formula_Pragma{Pragma: pragma795}
					_t1526 = _t1528
				} else {
					var _t1529 *pb.Formula
					if prediction785 == 8 {
						p.pushPath(int(7))
						_t1530 := p.parse_atom()
						atom794 := _t1530
						p.popPath()
						_t1531 := &pb.Formula{}
						_t1531.FormulaType = &pb.Formula_Atom{Atom: atom794}
						_t1529 = _t1531
					} else {
						var _t1532 *pb.Formula
						if prediction785 == 7 {
							p.pushPath(int(6))
							_t1533 := p.parse_ffi()
							ffi793 := _t1533
							p.popPath()
							_t1534 := &pb.Formula{}
							_t1534.FormulaType = &pb.Formula_Ffi{Ffi: ffi793}
							_t1532 = _t1534
						} else {
							var _t1535 *pb.Formula
							if prediction785 == 6 {
								p.pushPath(int(5))
								_t1536 := p.parse_not()
								not792 := _t1536
								p.popPath()
								_t1537 := &pb.Formula{}
								_t1537.FormulaType = &pb.Formula_Not{Not: not792}
								_t1535 = _t1537
							} else {
								var _t1538 *pb.Formula
								if prediction785 == 5 {
									p.pushPath(int(4))
									_t1539 := p.parse_disjunction()
									disjunction791 := _t1539
									p.popPath()
									_t1540 := &pb.Formula{}
									_t1540.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction791}
									_t1538 = _t1540
								} else {
									var _t1541 *pb.Formula
									if prediction785 == 4 {
										p.pushPath(int(3))
										_t1542 := p.parse_conjunction()
										conjunction790 := _t1542
										p.popPath()
										_t1543 := &pb.Formula{}
										_t1543.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction790}
										_t1541 = _t1543
									} else {
										var _t1544 *pb.Formula
										if prediction785 == 3 {
											p.pushPath(int(2))
											_t1545 := p.parse_reduce()
											reduce789 := _t1545
											p.popPath()
											_t1546 := &pb.Formula{}
											_t1546.FormulaType = &pb.Formula_Reduce{Reduce: reduce789}
											_t1544 = _t1546
										} else {
											var _t1547 *pb.Formula
											if prediction785 == 2 {
												p.pushPath(int(1))
												_t1548 := p.parse_exists()
												exists788 := _t1548
												p.popPath()
												_t1549 := &pb.Formula{}
												_t1549.FormulaType = &pb.Formula_Exists{Exists: exists788}
												_t1547 = _t1549
											} else {
												var _t1550 *pb.Formula
												if prediction785 == 1 {
													p.pushPath(int(4))
													_t1551 := p.parse_false()
													false787 := _t1551
													p.popPath()
													_t1552 := &pb.Formula{}
													_t1552.FormulaType = &pb.Formula_Disjunction{Disjunction: false787}
													_t1550 = _t1552
												} else {
													var _t1553 *pb.Formula
													if prediction785 == 0 {
														p.pushPath(int(3))
														_t1554 := p.parse_true()
														true786 := _t1554
														p.popPath()
														_t1555 := &pb.Formula{}
														_t1555.FormulaType = &pb.Formula_Conjunction{Conjunction: true786}
														_t1553 = _t1555
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1550 = _t1553
												}
												_t1547 = _t1550
											}
											_t1544 = _t1547
										}
										_t1541 = _t1544
									}
									_t1538 = _t1541
								}
								_t1535 = _t1538
							}
							_t1532 = _t1535
						}
						_t1529 = _t1532
					}
					_t1526 = _t1529
				}
				_t1523 = _t1526
			}
			_t1520 = _t1523
		}
		_t1517 = _t1520
	}
	result800 := _t1517
	p.recordSpan(int(span_start799))
	return result800
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1556 := &pb.Conjunction{Args: []*pb.Formula{}}
	result802 := _t1556
	p.recordSpan(int(span_start801))
	return result802
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start803 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1557 := &pb.Disjunction{Args: []*pb.Formula{}}
	result804 := _t1557
	p.recordSpan(int(span_start803))
	return result804
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start807 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1558 := p.parse_bindings()
	bindings805 := _t1558
	_t1559 := p.parse_formula()
	formula806 := _t1559
	p.consumeLiteral(")")
	_t1560 := &pb.Abstraction{Vars: listConcat(bindings805[0].([]*pb.Binding), bindings805[1].([]*pb.Binding)), Value: formula806}
	_t1561 := &pb.Exists{Body: _t1560}
	result808 := _t1561
	p.recordSpan(int(span_start807))
	return result808
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start812 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	p.pushPath(int(1))
	_t1562 := p.parse_abstraction()
	abstraction809 := _t1562
	p.popPath()
	p.pushPath(int(2))
	_t1563 := p.parse_abstraction()
	abstraction_3810 := _t1563
	p.popPath()
	p.pushPath(int(3))
	_t1564 := p.parse_terms()
	terms811 := _t1564
	p.popPath()
	p.consumeLiteral(")")
	_t1565 := &pb.Reduce{Op: abstraction809, Body: abstraction_3810, Terms: terms811}
	result813 := _t1565
	p.recordSpan(int(span_start812))
	return result813
}

func (p *Parser) parse_terms() []*pb.Term {
	span_start822 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs818 := []*pb.Term{}
	cond819 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx820 := 0
	for cond819 {
		p.pushPath(int(idx820))
		_t1566 := p.parse_term()
		item821 := _t1566
		p.popPath()
		xs818 = append(xs818, item821)
		idx820 = (idx820 + 1)
		cond819 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms817 := xs818
	p.consumeLiteral(")")
	result823 := terms817
	p.recordSpan(int(span_start822))
	return result823
}

func (p *Parser) parse_term() *pb.Term {
	span_start827 := int64(p.spanStart())
	var _t1567 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1567 = 1
	} else {
		var _t1568 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1568 = 1
		} else {
			var _t1569 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1569 = 1
			} else {
				var _t1570 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1570 = 1
				} else {
					var _t1571 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1571 = 1
					} else {
						var _t1572 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1572 = 0
						} else {
							var _t1573 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1573 = 1
							} else {
								var _t1574 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1574 = 1
								} else {
									var _t1575 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1575 = 1
									} else {
										var _t1576 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1576 = 1
										} else {
											var _t1577 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1577 = 1
											} else {
												_t1577 = -1
											}
											_t1576 = _t1577
										}
										_t1575 = _t1576
									}
									_t1574 = _t1575
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
	prediction824 := _t1567
	var _t1578 *pb.Term
	if prediction824 == 1 {
		p.pushPath(int(2))
		_t1579 := p.parse_constant()
		constant826 := _t1579
		p.popPath()
		_t1580 := &pb.Term{}
		_t1580.TermType = &pb.Term_Constant{Constant: constant826}
		_t1578 = _t1580
	} else {
		var _t1581 *pb.Term
		if prediction824 == 0 {
			p.pushPath(int(1))
			_t1582 := p.parse_var()
			var825 := _t1582
			p.popPath()
			_t1583 := &pb.Term{}
			_t1583.TermType = &pb.Term_Var{Var: var825}
			_t1581 = _t1583
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1578 = _t1581
	}
	result828 := _t1578
	p.recordSpan(int(span_start827))
	return result828
}

func (p *Parser) parse_var() *pb.Var {
	span_start830 := int64(p.spanStart())
	symbol829 := p.consumeTerminal("SYMBOL").Value.str
	_t1584 := &pb.Var{Name: symbol829}
	result831 := _t1584
	p.recordSpan(int(span_start830))
	return result831
}

func (p *Parser) parse_constant() *pb.Value {
	span_start833 := int64(p.spanStart())
	_t1585 := p.parse_value()
	value832 := _t1585
	result834 := value832
	p.recordSpan(int(span_start833))
	return result834
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start843 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	p.pushPath(int(1))
	xs839 := []*pb.Formula{}
	cond840 := p.matchLookaheadLiteral("(", 0)
	idx841 := 0
	for cond840 {
		p.pushPath(int(idx841))
		_t1586 := p.parse_formula()
		item842 := _t1586
		p.popPath()
		xs839 = append(xs839, item842)
		idx841 = (idx841 + 1)
		cond840 = p.matchLookaheadLiteral("(", 0)
	}
	formulas838 := xs839
	p.popPath()
	p.consumeLiteral(")")
	_t1587 := &pb.Conjunction{Args: formulas838}
	result844 := _t1587
	p.recordSpan(int(span_start843))
	return result844
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start853 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.pushPath(int(1))
	xs849 := []*pb.Formula{}
	cond850 := p.matchLookaheadLiteral("(", 0)
	idx851 := 0
	for cond850 {
		p.pushPath(int(idx851))
		_t1588 := p.parse_formula()
		item852 := _t1588
		p.popPath()
		xs849 = append(xs849, item852)
		idx851 = (idx851 + 1)
		cond850 = p.matchLookaheadLiteral("(", 0)
	}
	formulas848 := xs849
	p.popPath()
	p.consumeLiteral(")")
	_t1589 := &pb.Disjunction{Args: formulas848}
	result854 := _t1589
	p.recordSpan(int(span_start853))
	return result854
}

func (p *Parser) parse_not() *pb.Not {
	span_start856 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	p.pushPath(int(1))
	_t1590 := p.parse_formula()
	formula855 := _t1590
	p.popPath()
	p.consumeLiteral(")")
	_t1591 := &pb.Not{Arg: formula855}
	result857 := _t1591
	p.recordSpan(int(span_start856))
	return result857
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start861 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	p.pushPath(int(1))
	_t1592 := p.parse_name()
	name858 := _t1592
	p.popPath()
	p.pushPath(int(2))
	_t1593 := p.parse_ffi_args()
	ffi_args859 := _t1593
	p.popPath()
	p.pushPath(int(3))
	_t1594 := p.parse_terms()
	terms860 := _t1594
	p.popPath()
	p.consumeLiteral(")")
	_t1595 := &pb.FFI{Name: name858, Args: ffi_args859, Terms: terms860}
	result862 := _t1595
	p.recordSpan(int(span_start861))
	return result862
}

func (p *Parser) parse_name() string {
	span_start864 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol863 := p.consumeTerminal("SYMBOL").Value.str
	result865 := symbol863
	p.recordSpan(int(span_start864))
	return result865
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	span_start874 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs870 := []*pb.Abstraction{}
	cond871 := p.matchLookaheadLiteral("(", 0)
	idx872 := 0
	for cond871 {
		p.pushPath(int(idx872))
		_t1596 := p.parse_abstraction()
		item873 := _t1596
		p.popPath()
		xs870 = append(xs870, item873)
		idx872 = (idx872 + 1)
		cond871 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions869 := xs870
	p.consumeLiteral(")")
	result875 := abstractions869
	p.recordSpan(int(span_start874))
	return result875
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start885 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	p.pushPath(int(1))
	_t1597 := p.parse_relation_id()
	relation_id876 := _t1597
	p.popPath()
	p.pushPath(int(2))
	xs881 := []*pb.Term{}
	cond882 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx883 := 0
	for cond882 {
		p.pushPath(int(idx883))
		_t1598 := p.parse_term()
		item884 := _t1598
		p.popPath()
		xs881 = append(xs881, item884)
		idx883 = (idx883 + 1)
		cond882 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms880 := xs881
	p.popPath()
	p.consumeLiteral(")")
	_t1599 := &pb.Atom{Name: relation_id876, Terms: terms880}
	result886 := _t1599
	p.recordSpan(int(span_start885))
	return result886
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start896 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	p.pushPath(int(1))
	_t1600 := p.parse_name()
	name887 := _t1600
	p.popPath()
	p.pushPath(int(2))
	xs892 := []*pb.Term{}
	cond893 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx894 := 0
	for cond893 {
		p.pushPath(int(idx894))
		_t1601 := p.parse_term()
		item895 := _t1601
		p.popPath()
		xs892 = append(xs892, item895)
		idx894 = (idx894 + 1)
		cond893 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms891 := xs892
	p.popPath()
	p.consumeLiteral(")")
	_t1602 := &pb.Pragma{Name: name887, Terms: terms891}
	result897 := _t1602
	p.recordSpan(int(span_start896))
	return result897
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start917 := int64(p.spanStart())
	var _t1603 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1604 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1604 = 9
		} else {
			var _t1605 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1605 = 4
			} else {
				var _t1606 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1606 = 3
				} else {
					var _t1607 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1607 = 0
					} else {
						var _t1608 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1608 = 2
						} else {
							var _t1609 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1609 = 1
							} else {
								var _t1610 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1610 = 8
								} else {
									var _t1611 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1611 = 6
									} else {
										var _t1612 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1612 = 5
										} else {
											var _t1613 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1613 = 7
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
	} else {
		_t1603 = -1
	}
	prediction898 := _t1603
	var _t1614 *pb.Primitive
	if prediction898 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		p.pushPath(int(1))
		_t1615 := p.parse_name()
		name908 := _t1615
		p.popPath()
		p.pushPath(int(2))
		xs913 := []*pb.RelTerm{}
		cond914 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		idx915 := 0
		for cond914 {
			p.pushPath(int(idx915))
			_t1616 := p.parse_rel_term()
			item916 := _t1616
			p.popPath()
			xs913 = append(xs913, item916)
			idx915 = (idx915 + 1)
			cond914 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms912 := xs913
		p.popPath()
		p.consumeLiteral(")")
		_t1617 := &pb.Primitive{Name: name908, Terms: rel_terms912}
		_t1614 = _t1617
	} else {
		var _t1618 *pb.Primitive
		if prediction898 == 8 {
			_t1619 := p.parse_divide()
			divide907 := _t1619
			_t1618 = divide907
		} else {
			var _t1620 *pb.Primitive
			if prediction898 == 7 {
				_t1621 := p.parse_multiply()
				multiply906 := _t1621
				_t1620 = multiply906
			} else {
				var _t1622 *pb.Primitive
				if prediction898 == 6 {
					_t1623 := p.parse_minus()
					minus905 := _t1623
					_t1622 = minus905
				} else {
					var _t1624 *pb.Primitive
					if prediction898 == 5 {
						_t1625 := p.parse_add()
						add904 := _t1625
						_t1624 = add904
					} else {
						var _t1626 *pb.Primitive
						if prediction898 == 4 {
							_t1627 := p.parse_gt_eq()
							gt_eq903 := _t1627
							_t1626 = gt_eq903
						} else {
							var _t1628 *pb.Primitive
							if prediction898 == 3 {
								_t1629 := p.parse_gt()
								gt902 := _t1629
								_t1628 = gt902
							} else {
								var _t1630 *pb.Primitive
								if prediction898 == 2 {
									_t1631 := p.parse_lt_eq()
									lt_eq901 := _t1631
									_t1630 = lt_eq901
								} else {
									var _t1632 *pb.Primitive
									if prediction898 == 1 {
										_t1633 := p.parse_lt()
										lt900 := _t1633
										_t1632 = lt900
									} else {
										var _t1634 *pb.Primitive
										if prediction898 == 0 {
											_t1635 := p.parse_eq()
											eq899 := _t1635
											_t1634 = eq899
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
				_t1620 = _t1622
			}
			_t1618 = _t1620
		}
		_t1614 = _t1618
	}
	result918 := _t1614
	p.recordSpan(int(span_start917))
	return result918
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start921 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1636 := p.parse_term()
	term919 := _t1636
	_t1637 := p.parse_term()
	term_3920 := _t1637
	p.consumeLiteral(")")
	_t1638 := &pb.RelTerm{}
	_t1638.RelTermType = &pb.RelTerm_Term{Term: term919}
	_t1639 := &pb.RelTerm{}
	_t1639.RelTermType = &pb.RelTerm_Term{Term: term_3920}
	_t1640 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1638, _t1639}}
	result922 := _t1640
	p.recordSpan(int(span_start921))
	return result922
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start925 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1641 := p.parse_term()
	term923 := _t1641
	_t1642 := p.parse_term()
	term_3924 := _t1642
	p.consumeLiteral(")")
	_t1643 := &pb.RelTerm{}
	_t1643.RelTermType = &pb.RelTerm_Term{Term: term923}
	_t1644 := &pb.RelTerm{}
	_t1644.RelTermType = &pb.RelTerm_Term{Term: term_3924}
	_t1645 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1643, _t1644}}
	result926 := _t1645
	p.recordSpan(int(span_start925))
	return result926
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start929 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1646 := p.parse_term()
	term927 := _t1646
	_t1647 := p.parse_term()
	term_3928 := _t1647
	p.consumeLiteral(")")
	_t1648 := &pb.RelTerm{}
	_t1648.RelTermType = &pb.RelTerm_Term{Term: term927}
	_t1649 := &pb.RelTerm{}
	_t1649.RelTermType = &pb.RelTerm_Term{Term: term_3928}
	_t1650 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1648, _t1649}}
	result930 := _t1650
	p.recordSpan(int(span_start929))
	return result930
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start933 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1651 := p.parse_term()
	term931 := _t1651
	_t1652 := p.parse_term()
	term_3932 := _t1652
	p.consumeLiteral(")")
	_t1653 := &pb.RelTerm{}
	_t1653.RelTermType = &pb.RelTerm_Term{Term: term931}
	_t1654 := &pb.RelTerm{}
	_t1654.RelTermType = &pb.RelTerm_Term{Term: term_3932}
	_t1655 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1653, _t1654}}
	result934 := _t1655
	p.recordSpan(int(span_start933))
	return result934
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start937 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1656 := p.parse_term()
	term935 := _t1656
	_t1657 := p.parse_term()
	term_3936 := _t1657
	p.consumeLiteral(")")
	_t1658 := &pb.RelTerm{}
	_t1658.RelTermType = &pb.RelTerm_Term{Term: term935}
	_t1659 := &pb.RelTerm{}
	_t1659.RelTermType = &pb.RelTerm_Term{Term: term_3936}
	_t1660 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1658, _t1659}}
	result938 := _t1660
	p.recordSpan(int(span_start937))
	return result938
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start942 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1661 := p.parse_term()
	term939 := _t1661
	_t1662 := p.parse_term()
	term_3940 := _t1662
	_t1663 := p.parse_term()
	term_4941 := _t1663
	p.consumeLiteral(")")
	_t1664 := &pb.RelTerm{}
	_t1664.RelTermType = &pb.RelTerm_Term{Term: term939}
	_t1665 := &pb.RelTerm{}
	_t1665.RelTermType = &pb.RelTerm_Term{Term: term_3940}
	_t1666 := &pb.RelTerm{}
	_t1666.RelTermType = &pb.RelTerm_Term{Term: term_4941}
	_t1667 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1664, _t1665, _t1666}}
	result943 := _t1667
	p.recordSpan(int(span_start942))
	return result943
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start947 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1668 := p.parse_term()
	term944 := _t1668
	_t1669 := p.parse_term()
	term_3945 := _t1669
	_t1670 := p.parse_term()
	term_4946 := _t1670
	p.consumeLiteral(")")
	_t1671 := &pb.RelTerm{}
	_t1671.RelTermType = &pb.RelTerm_Term{Term: term944}
	_t1672 := &pb.RelTerm{}
	_t1672.RelTermType = &pb.RelTerm_Term{Term: term_3945}
	_t1673 := &pb.RelTerm{}
	_t1673.RelTermType = &pb.RelTerm_Term{Term: term_4946}
	_t1674 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1671, _t1672, _t1673}}
	result948 := _t1674
	p.recordSpan(int(span_start947))
	return result948
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1675 := p.parse_term()
	term949 := _t1675
	_t1676 := p.parse_term()
	term_3950 := _t1676
	_t1677 := p.parse_term()
	term_4951 := _t1677
	p.consumeLiteral(")")
	_t1678 := &pb.RelTerm{}
	_t1678.RelTermType = &pb.RelTerm_Term{Term: term949}
	_t1679 := &pb.RelTerm{}
	_t1679.RelTermType = &pb.RelTerm_Term{Term: term_3950}
	_t1680 := &pb.RelTerm{}
	_t1680.RelTermType = &pb.RelTerm_Term{Term: term_4951}
	_t1681 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1678, _t1679, _t1680}}
	result953 := _t1681
	p.recordSpan(int(span_start952))
	return result953
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start957 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1682 := p.parse_term()
	term954 := _t1682
	_t1683 := p.parse_term()
	term_3955 := _t1683
	_t1684 := p.parse_term()
	term_4956 := _t1684
	p.consumeLiteral(")")
	_t1685 := &pb.RelTerm{}
	_t1685.RelTermType = &pb.RelTerm_Term{Term: term954}
	_t1686 := &pb.RelTerm{}
	_t1686.RelTermType = &pb.RelTerm_Term{Term: term_3955}
	_t1687 := &pb.RelTerm{}
	_t1687.RelTermType = &pb.RelTerm_Term{Term: term_4956}
	_t1688 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1685, _t1686, _t1687}}
	result958 := _t1688
	p.recordSpan(int(span_start957))
	return result958
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start962 := int64(p.spanStart())
	var _t1689 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1689 = 1
	} else {
		var _t1690 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1690 = 1
		} else {
			var _t1691 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1691 = 1
			} else {
				var _t1692 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1692 = 1
				} else {
					var _t1693 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1693 = 0
					} else {
						var _t1694 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1694 = 1
						} else {
							var _t1695 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1695 = 1
							} else {
								var _t1696 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1696 = 1
								} else {
									var _t1697 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1697 = 1
									} else {
										var _t1698 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1698 = 1
										} else {
											var _t1699 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1699 = 1
											} else {
												var _t1700 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1700 = 1
												} else {
													_t1700 = -1
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
					_t1692 = _t1693
				}
				_t1691 = _t1692
			}
			_t1690 = _t1691
		}
		_t1689 = _t1690
	}
	prediction959 := _t1689
	var _t1701 *pb.RelTerm
	if prediction959 == 1 {
		p.pushPath(int(2))
		_t1702 := p.parse_term()
		term961 := _t1702
		p.popPath()
		_t1703 := &pb.RelTerm{}
		_t1703.RelTermType = &pb.RelTerm_Term{Term: term961}
		_t1701 = _t1703
	} else {
		var _t1704 *pb.RelTerm
		if prediction959 == 0 {
			p.pushPath(int(1))
			_t1705 := p.parse_specialized_value()
			specialized_value960 := _t1705
			p.popPath()
			_t1706 := &pb.RelTerm{}
			_t1706.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value960}
			_t1704 = _t1706
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1701 = _t1704
	}
	result963 := _t1701
	p.recordSpan(int(span_start962))
	return result963
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start965 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1707 := p.parse_value()
	value964 := _t1707
	result966 := value964
	p.recordSpan(int(span_start965))
	return result966
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start976 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	p.pushPath(int(3))
	_t1708 := p.parse_name()
	name967 := _t1708
	p.popPath()
	p.pushPath(int(2))
	xs972 := []*pb.RelTerm{}
	cond973 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx974 := 0
	for cond973 {
		p.pushPath(int(idx974))
		_t1709 := p.parse_rel_term()
		item975 := _t1709
		p.popPath()
		xs972 = append(xs972, item975)
		idx974 = (idx974 + 1)
		cond973 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms971 := xs972
	p.popPath()
	p.consumeLiteral(")")
	_t1710 := &pb.RelAtom{Name: name967, Terms: rel_terms971}
	result977 := _t1710
	p.recordSpan(int(span_start976))
	return result977
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	p.pushPath(int(2))
	_t1711 := p.parse_term()
	term978 := _t1711
	p.popPath()
	p.pushPath(int(3))
	_t1712 := p.parse_term()
	term_3979 := _t1712
	p.popPath()
	p.consumeLiteral(")")
	_t1713 := &pb.Cast{Input: term978, Result: term_3979}
	result981 := _t1713
	p.recordSpan(int(span_start980))
	return result981
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	span_start990 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs986 := []*pb.Attribute{}
	cond987 := p.matchLookaheadLiteral("(", 0)
	idx988 := 0
	for cond987 {
		p.pushPath(int(idx988))
		_t1714 := p.parse_attribute()
		item989 := _t1714
		p.popPath()
		xs986 = append(xs986, item989)
		idx988 = (idx988 + 1)
		cond987 = p.matchLookaheadLiteral("(", 0)
	}
	attributes985 := xs986
	p.consumeLiteral(")")
	result991 := attributes985
	p.recordSpan(int(span_start990))
	return result991
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start1001 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	p.pushPath(int(1))
	_t1715 := p.parse_name()
	name992 := _t1715
	p.popPath()
	p.pushPath(int(2))
	xs997 := []*pb.Value{}
	cond998 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx999 := 0
	for cond998 {
		p.pushPath(int(idx999))
		_t1716 := p.parse_value()
		item1000 := _t1716
		p.popPath()
		xs997 = append(xs997, item1000)
		idx999 = (idx999 + 1)
		cond998 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values996 := xs997
	p.popPath()
	p.consumeLiteral(")")
	_t1717 := &pb.Attribute{Name: name992, Args: values996}
	result1002 := _t1717
	p.recordSpan(int(span_start1001))
	return result1002
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start1012 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	p.pushPath(int(1))
	xs1007 := []*pb.RelationId{}
	cond1008 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx1009 := 0
	for cond1008 {
		p.pushPath(int(idx1009))
		_t1718 := p.parse_relation_id()
		item1010 := _t1718
		p.popPath()
		xs1007 = append(xs1007, item1010)
		idx1009 = (idx1009 + 1)
		cond1008 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1006 := xs1007
	p.popPath()
	p.pushPath(int(2))
	_t1719 := p.parse_script()
	script1011 := _t1719
	p.popPath()
	p.consumeLiteral(")")
	_t1720 := &pb.Algorithm{Global: relation_ids1006, Body: script1011}
	result1013 := _t1720
	p.recordSpan(int(span_start1012))
	return result1013
}

func (p *Parser) parse_script() *pb.Script {
	span_start1022 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	p.pushPath(int(1))
	xs1018 := []*pb.Construct{}
	cond1019 := p.matchLookaheadLiteral("(", 0)
	idx1020 := 0
	for cond1019 {
		p.pushPath(int(idx1020))
		_t1721 := p.parse_construct()
		item1021 := _t1721
		p.popPath()
		xs1018 = append(xs1018, item1021)
		idx1020 = (idx1020 + 1)
		cond1019 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1017 := xs1018
	p.popPath()
	p.consumeLiteral(")")
	_t1722 := &pb.Script{Constructs: constructs1017}
	result1023 := _t1722
	p.recordSpan(int(span_start1022))
	return result1023
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start1027 := int64(p.spanStart())
	var _t1723 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1724 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1724 = 1
		} else {
			var _t1725 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1725 = 1
			} else {
				var _t1726 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1726 = 1
				} else {
					var _t1727 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1727 = 0
					} else {
						var _t1728 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1728 = 1
						} else {
							var _t1729 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1729 = 1
							} else {
								_t1729 = -1
							}
							_t1728 = _t1729
						}
						_t1727 = _t1728
					}
					_t1726 = _t1727
				}
				_t1725 = _t1726
			}
			_t1724 = _t1725
		}
		_t1723 = _t1724
	} else {
		_t1723 = -1
	}
	prediction1024 := _t1723
	var _t1730 *pb.Construct
	if prediction1024 == 1 {
		p.pushPath(int(2))
		_t1731 := p.parse_instruction()
		instruction1026 := _t1731
		p.popPath()
		_t1732 := &pb.Construct{}
		_t1732.ConstructType = &pb.Construct_Instruction{Instruction: instruction1026}
		_t1730 = _t1732
	} else {
		var _t1733 *pb.Construct
		if prediction1024 == 0 {
			p.pushPath(int(1))
			_t1734 := p.parse_loop()
			loop1025 := _t1734
			p.popPath()
			_t1735 := &pb.Construct{}
			_t1735.ConstructType = &pb.Construct_Loop{Loop: loop1025}
			_t1733 = _t1735
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1730 = _t1733
	}
	result1028 := _t1730
	p.recordSpan(int(span_start1027))
	return result1028
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start1031 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	p.pushPath(int(1))
	_t1736 := p.parse_init()
	init1029 := _t1736
	p.popPath()
	p.pushPath(int(2))
	_t1737 := p.parse_script()
	script1030 := _t1737
	p.popPath()
	p.consumeLiteral(")")
	_t1738 := &pb.Loop{Init: init1029, Body: script1030}
	result1032 := _t1738
	p.recordSpan(int(span_start1031))
	return result1032
}

func (p *Parser) parse_init() []*pb.Instruction {
	span_start1041 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1037 := []*pb.Instruction{}
	cond1038 := p.matchLookaheadLiteral("(", 0)
	idx1039 := 0
	for cond1038 {
		p.pushPath(int(idx1039))
		_t1739 := p.parse_instruction()
		item1040 := _t1739
		p.popPath()
		xs1037 = append(xs1037, item1040)
		idx1039 = (idx1039 + 1)
		cond1038 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1036 := xs1037
	p.consumeLiteral(")")
	result1042 := instructions1036
	p.recordSpan(int(span_start1041))
	return result1042
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1049 := int64(p.spanStart())
	var _t1740 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1741 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1741 = 1
		} else {
			var _t1742 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1742 = 4
			} else {
				var _t1743 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1743 = 3
				} else {
					var _t1744 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1744 = 2
					} else {
						var _t1745 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1745 = 0
						} else {
							_t1745 = -1
						}
						_t1744 = _t1745
					}
					_t1743 = _t1744
				}
				_t1742 = _t1743
			}
			_t1741 = _t1742
		}
		_t1740 = _t1741
	} else {
		_t1740 = -1
	}
	prediction1043 := _t1740
	var _t1746 *pb.Instruction
	if prediction1043 == 4 {
		p.pushPath(int(6))
		_t1747 := p.parse_monus_def()
		monus_def1048 := _t1747
		p.popPath()
		_t1748 := &pb.Instruction{}
		_t1748.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1048}
		_t1746 = _t1748
	} else {
		var _t1749 *pb.Instruction
		if prediction1043 == 3 {
			p.pushPath(int(5))
			_t1750 := p.parse_monoid_def()
			monoid_def1047 := _t1750
			p.popPath()
			_t1751 := &pb.Instruction{}
			_t1751.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1047}
			_t1749 = _t1751
		} else {
			var _t1752 *pb.Instruction
			if prediction1043 == 2 {
				p.pushPath(int(3))
				_t1753 := p.parse_break()
				break1046 := _t1753
				p.popPath()
				_t1754 := &pb.Instruction{}
				_t1754.InstrType = &pb.Instruction_Break{Break: break1046}
				_t1752 = _t1754
			} else {
				var _t1755 *pb.Instruction
				if prediction1043 == 1 {
					p.pushPath(int(2))
					_t1756 := p.parse_upsert()
					upsert1045 := _t1756
					p.popPath()
					_t1757 := &pb.Instruction{}
					_t1757.InstrType = &pb.Instruction_Upsert{Upsert: upsert1045}
					_t1755 = _t1757
				} else {
					var _t1758 *pb.Instruction
					if prediction1043 == 0 {
						p.pushPath(int(1))
						_t1759 := p.parse_assign()
						assign1044 := _t1759
						p.popPath()
						_t1760 := &pb.Instruction{}
						_t1760.InstrType = &pb.Instruction_Assign{Assign: assign1044}
						_t1758 = _t1760
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1755 = _t1758
				}
				_t1752 = _t1755
			}
			_t1749 = _t1752
		}
		_t1746 = _t1749
	}
	result1050 := _t1746
	p.recordSpan(int(span_start1049))
	return result1050
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1054 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	p.pushPath(int(1))
	_t1761 := p.parse_relation_id()
	relation_id1051 := _t1761
	p.popPath()
	p.pushPath(int(2))
	_t1762 := p.parse_abstraction()
	abstraction1052 := _t1762
	p.popPath()
	p.pushPath(int(3))
	var _t1763 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1764 := p.parse_attrs()
		_t1763 = _t1764
	}
	attrs1053 := _t1763
	p.popPath()
	p.consumeLiteral(")")
	_t1765 := attrs1053
	if attrs1053 == nil {
		_t1765 = []*pb.Attribute{}
	}
	_t1766 := &pb.Assign{Name: relation_id1051, Body: abstraction1052, Attrs: _t1765}
	result1055 := _t1766
	p.recordSpan(int(span_start1054))
	return result1055
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1059 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	p.pushPath(int(1))
	_t1767 := p.parse_relation_id()
	relation_id1056 := _t1767
	p.popPath()
	_t1768 := p.parse_abstraction_with_arity()
	abstraction_with_arity1057 := _t1768
	p.pushPath(int(3))
	var _t1769 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1770 := p.parse_attrs()
		_t1769 = _t1770
	}
	attrs1058 := _t1769
	p.popPath()
	p.consumeLiteral(")")
	_t1771 := attrs1058
	if attrs1058 == nil {
		_t1771 = []*pb.Attribute{}
	}
	_t1772 := &pb.Upsert{Name: relation_id1056, Body: abstraction_with_arity1057[0].(*pb.Abstraction), Attrs: _t1771, ValueArity: abstraction_with_arity1057[1].(int64)}
	result1060 := _t1772
	p.recordSpan(int(span_start1059))
	return result1060
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	span_start1063 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1773 := p.parse_bindings()
	bindings1061 := _t1773
	_t1774 := p.parse_formula()
	formula1062 := _t1774
	p.consumeLiteral(")")
	_t1775 := &pb.Abstraction{Vars: listConcat(bindings1061[0].([]*pb.Binding), bindings1061[1].([]*pb.Binding)), Value: formula1062}
	result1064 := []interface{}{_t1775, int64(len(bindings1061[1].([]*pb.Binding)))}
	p.recordSpan(int(span_start1063))
	return result1064
}

func (p *Parser) parse_break() *pb.Break {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	p.pushPath(int(1))
	_t1776 := p.parse_relation_id()
	relation_id1065 := _t1776
	p.popPath()
	p.pushPath(int(2))
	_t1777 := p.parse_abstraction()
	abstraction1066 := _t1777
	p.popPath()
	p.pushPath(int(3))
	var _t1778 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1779 := p.parse_attrs()
		_t1778 = _t1779
	}
	attrs1067 := _t1778
	p.popPath()
	p.consumeLiteral(")")
	_t1780 := attrs1067
	if attrs1067 == nil {
		_t1780 = []*pb.Attribute{}
	}
	_t1781 := &pb.Break{Name: relation_id1065, Body: abstraction1066, Attrs: _t1780}
	result1069 := _t1781
	p.recordSpan(int(span_start1068))
	return result1069
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	p.pushPath(int(1))
	_t1782 := p.parse_monoid()
	monoid1070 := _t1782
	p.popPath()
	p.pushPath(int(2))
	_t1783 := p.parse_relation_id()
	relation_id1071 := _t1783
	p.popPath()
	_t1784 := p.parse_abstraction_with_arity()
	abstraction_with_arity1072 := _t1784
	p.pushPath(int(4))
	var _t1785 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1786 := p.parse_attrs()
		_t1785 = _t1786
	}
	attrs1073 := _t1785
	p.popPath()
	p.consumeLiteral(")")
	_t1787 := attrs1073
	if attrs1073 == nil {
		_t1787 = []*pb.Attribute{}
	}
	_t1788 := &pb.MonoidDef{Monoid: monoid1070, Name: relation_id1071, Body: abstraction_with_arity1072[0].(*pb.Abstraction), Attrs: _t1787, ValueArity: abstraction_with_arity1072[1].(int64)}
	result1075 := _t1788
	p.recordSpan(int(span_start1074))
	return result1075
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1081 := int64(p.spanStart())
	var _t1789 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1790 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1790 = 3
		} else {
			var _t1791 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1791 = 0
			} else {
				var _t1792 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1792 = 1
				} else {
					var _t1793 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1793 = 2
					} else {
						_t1793 = -1
					}
					_t1792 = _t1793
				}
				_t1791 = _t1792
			}
			_t1790 = _t1791
		}
		_t1789 = _t1790
	} else {
		_t1789 = -1
	}
	prediction1076 := _t1789
	var _t1794 *pb.Monoid
	if prediction1076 == 3 {
		p.pushPath(int(4))
		_t1795 := p.parse_sum_monoid()
		sum_monoid1080 := _t1795
		p.popPath()
		_t1796 := &pb.Monoid{}
		_t1796.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1080}
		_t1794 = _t1796
	} else {
		var _t1797 *pb.Monoid
		if prediction1076 == 2 {
			p.pushPath(int(3))
			_t1798 := p.parse_max_monoid()
			max_monoid1079 := _t1798
			p.popPath()
			_t1799 := &pb.Monoid{}
			_t1799.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1079}
			_t1797 = _t1799
		} else {
			var _t1800 *pb.Monoid
			if prediction1076 == 1 {
				p.pushPath(int(2))
				_t1801 := p.parse_min_monoid()
				min_monoid1078 := _t1801
				p.popPath()
				_t1802 := &pb.Monoid{}
				_t1802.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1078}
				_t1800 = _t1802
			} else {
				var _t1803 *pb.Monoid
				if prediction1076 == 0 {
					p.pushPath(int(1))
					_t1804 := p.parse_or_monoid()
					or_monoid1077 := _t1804
					p.popPath()
					_t1805 := &pb.Monoid{}
					_t1805.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1077}
					_t1803 = _t1805
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1800 = _t1803
			}
			_t1797 = _t1800
		}
		_t1794 = _t1797
	}
	result1082 := _t1794
	p.recordSpan(int(span_start1081))
	return result1082
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1083 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1806 := &pb.OrMonoid{}
	result1084 := _t1806
	p.recordSpan(int(span_start1083))
	return result1084
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1086 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	p.pushPath(int(1))
	_t1807 := p.parse_type()
	type1085 := _t1807
	p.popPath()
	p.consumeLiteral(")")
	_t1808 := &pb.MinMonoid{Type: type1085}
	result1087 := _t1808
	p.recordSpan(int(span_start1086))
	return result1087
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1089 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	p.pushPath(int(1))
	_t1809 := p.parse_type()
	type1088 := _t1809
	p.popPath()
	p.consumeLiteral(")")
	_t1810 := &pb.MaxMonoid{Type: type1088}
	result1090 := _t1810
	p.recordSpan(int(span_start1089))
	return result1090
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1092 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	p.pushPath(int(1))
	_t1811 := p.parse_type()
	type1091 := _t1811
	p.popPath()
	p.consumeLiteral(")")
	_t1812 := &pb.SumMonoid{Type: type1091}
	result1093 := _t1812
	p.recordSpan(int(span_start1092))
	return result1093
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1098 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	p.pushPath(int(1))
	_t1813 := p.parse_monoid()
	monoid1094 := _t1813
	p.popPath()
	p.pushPath(int(2))
	_t1814 := p.parse_relation_id()
	relation_id1095 := _t1814
	p.popPath()
	_t1815 := p.parse_abstraction_with_arity()
	abstraction_with_arity1096 := _t1815
	p.pushPath(int(4))
	var _t1816 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1817 := p.parse_attrs()
		_t1816 = _t1817
	}
	attrs1097 := _t1816
	p.popPath()
	p.consumeLiteral(")")
	_t1818 := attrs1097
	if attrs1097 == nil {
		_t1818 = []*pb.Attribute{}
	}
	_t1819 := &pb.MonusDef{Monoid: monoid1094, Name: relation_id1095, Body: abstraction_with_arity1096[0].(*pb.Abstraction), Attrs: _t1818, ValueArity: abstraction_with_arity1096[1].(int64)}
	result1099 := _t1819
	p.recordSpan(int(span_start1098))
	return result1099
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	p.pushPath(int(2))
	_t1820 := p.parse_relation_id()
	relation_id1100 := _t1820
	p.popPath()
	_t1821 := p.parse_abstraction()
	abstraction1101 := _t1821
	_t1822 := p.parse_functional_dependency_keys()
	functional_dependency_keys1102 := _t1822
	_t1823 := p.parse_functional_dependency_values()
	functional_dependency_values1103 := _t1823
	p.consumeLiteral(")")
	_t1824 := &pb.FunctionalDependency{Guard: abstraction1101, Keys: functional_dependency_keys1102, Values: functional_dependency_values1103}
	_t1825 := &pb.Constraint{Name: relation_id1100}
	_t1825.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1824}
	result1105 := _t1825
	p.recordSpan(int(span_start1104))
	return result1105
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	span_start1114 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1110 := []*pb.Var{}
	cond1111 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx1112 := 0
	for cond1111 {
		p.pushPath(int(idx1112))
		_t1826 := p.parse_var()
		item1113 := _t1826
		p.popPath()
		xs1110 = append(xs1110, item1113)
		idx1112 = (idx1112 + 1)
		cond1111 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1109 := xs1110
	p.consumeLiteral(")")
	result1115 := vars1109
	p.recordSpan(int(span_start1114))
	return result1115
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1120 := []*pb.Var{}
	cond1121 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx1122 := 0
	for cond1121 {
		p.pushPath(int(idx1122))
		_t1827 := p.parse_var()
		item1123 := _t1827
		p.popPath()
		xs1120 = append(xs1120, item1123)
		idx1122 = (idx1122 + 1)
		cond1121 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1119 := xs1120
	p.consumeLiteral(")")
	result1125 := vars1119
	p.recordSpan(int(span_start1124))
	return result1125
}

func (p *Parser) parse_data() *pb.Data {
	span_start1130 := int64(p.spanStart())
	var _t1828 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1829 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1829 = 0
		} else {
			var _t1830 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1830 = 2
			} else {
				var _t1831 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1831 = 1
				} else {
					_t1831 = -1
				}
				_t1830 = _t1831
			}
			_t1829 = _t1830
		}
		_t1828 = _t1829
	} else {
		_t1828 = -1
	}
	prediction1126 := _t1828
	var _t1832 *pb.Data
	if prediction1126 == 2 {
		p.pushPath(int(3))
		_t1833 := p.parse_csv_data()
		csv_data1129 := _t1833
		p.popPath()
		_t1834 := &pb.Data{}
		_t1834.DataType = &pb.Data_CsvData{CsvData: csv_data1129}
		_t1832 = _t1834
	} else {
		var _t1835 *pb.Data
		if prediction1126 == 1 {
			p.pushPath(int(2))
			_t1836 := p.parse_betree_relation()
			betree_relation1128 := _t1836
			p.popPath()
			_t1837 := &pb.Data{}
			_t1837.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1128}
			_t1835 = _t1837
		} else {
			var _t1838 *pb.Data
			if prediction1126 == 0 {
				p.pushPath(int(1))
				_t1839 := p.parse_rel_edb()
				rel_edb1127 := _t1839
				p.popPath()
				_t1840 := &pb.Data{}
				_t1840.DataType = &pb.Data_RelEdb{RelEdb: rel_edb1127}
				_t1838 = _t1840
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1835 = _t1838
		}
		_t1832 = _t1835
	}
	result1131 := _t1832
	p.recordSpan(int(span_start1130))
	return result1131
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	span_start1135 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	p.pushPath(int(1))
	_t1841 := p.parse_relation_id()
	relation_id1132 := _t1841
	p.popPath()
	p.pushPath(int(2))
	_t1842 := p.parse_rel_edb_path()
	rel_edb_path1133 := _t1842
	p.popPath()
	p.pushPath(int(3))
	_t1843 := p.parse_rel_edb_types()
	rel_edb_types1134 := _t1843
	p.popPath()
	p.consumeLiteral(")")
	_t1844 := &pb.RelEDB{TargetId: relation_id1132, Path: rel_edb_path1133, Types: rel_edb_types1134}
	result1136 := _t1844
	p.recordSpan(int(span_start1135))
	return result1136
}

func (p *Parser) parse_rel_edb_path() []string {
	span_start1145 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1141 := []string{}
	cond1142 := p.matchLookaheadTerminal("STRING", 0)
	idx1143 := 0
	for cond1142 {
		p.pushPath(int(idx1143))
		item1144 := p.consumeTerminal("STRING").Value.str
		p.popPath()
		xs1141 = append(xs1141, item1144)
		idx1143 = (idx1143 + 1)
		cond1142 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1140 := xs1141
	p.consumeLiteral("]")
	result1146 := strings1140
	p.recordSpan(int(span_start1145))
	return result1146
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	span_start1155 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1151 := []*pb.Type{}
	cond1152 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx1153 := 0
	for cond1152 {
		p.pushPath(int(idx1153))
		_t1845 := p.parse_type()
		item1154 := _t1845
		p.popPath()
		xs1151 = append(xs1151, item1154)
		idx1153 = (idx1153 + 1)
		cond1152 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1150 := xs1151
	p.consumeLiteral("]")
	result1156 := types1150
	p.recordSpan(int(span_start1155))
	return result1156
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1159 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	p.pushPath(int(1))
	_t1846 := p.parse_relation_id()
	relation_id1157 := _t1846
	p.popPath()
	p.pushPath(int(2))
	_t1847 := p.parse_betree_info()
	betree_info1158 := _t1847
	p.popPath()
	p.consumeLiteral(")")
	_t1848 := &pb.BeTreeRelation{Name: relation_id1157, RelationInfo: betree_info1158}
	result1160 := _t1848
	p.recordSpan(int(span_start1159))
	return result1160
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1164 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1849 := p.parse_betree_info_key_types()
	betree_info_key_types1161 := _t1849
	_t1850 := p.parse_betree_info_value_types()
	betree_info_value_types1162 := _t1850
	_t1851 := p.parse_config_dict()
	config_dict1163 := _t1851
	p.consumeLiteral(")")
	_t1852 := p.construct_betree_info(betree_info_key_types1161, betree_info_value_types1162, config_dict1163)
	result1165 := _t1852
	p.recordSpan(int(span_start1164))
	return result1165
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	span_start1174 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1170 := []*pb.Type{}
	cond1171 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx1172 := 0
	for cond1171 {
		p.pushPath(int(idx1172))
		_t1853 := p.parse_type()
		item1173 := _t1853
		p.popPath()
		xs1170 = append(xs1170, item1173)
		idx1172 = (idx1172 + 1)
		cond1171 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1169 := xs1170
	p.consumeLiteral(")")
	result1175 := types1169
	p.recordSpan(int(span_start1174))
	return result1175
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	span_start1184 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1180 := []*pb.Type{}
	cond1181 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx1182 := 0
	for cond1181 {
		p.pushPath(int(idx1182))
		_t1854 := p.parse_type()
		item1183 := _t1854
		p.popPath()
		xs1180 = append(xs1180, item1183)
		idx1182 = (idx1182 + 1)
		cond1181 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1179 := xs1180
	p.consumeLiteral(")")
	result1185 := types1179
	p.recordSpan(int(span_start1184))
	return result1185
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1190 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	p.pushPath(int(1))
	_t1855 := p.parse_csvlocator()
	csvlocator1186 := _t1855
	p.popPath()
	p.pushPath(int(2))
	_t1856 := p.parse_csv_config()
	csv_config1187 := _t1856
	p.popPath()
	p.pushPath(int(3))
	_t1857 := p.parse_csv_columns()
	csv_columns1188 := _t1857
	p.popPath()
	p.pushPath(int(4))
	_t1858 := p.parse_csv_asof()
	csv_asof1189 := _t1858
	p.popPath()
	p.consumeLiteral(")")
	_t1859 := &pb.CSVData{Locator: csvlocator1186, Config: csv_config1187, Columns: csv_columns1188, Asof: csv_asof1189}
	result1191 := _t1859
	p.recordSpan(int(span_start1190))
	return result1191
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1194 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	p.pushPath(int(1))
	var _t1860 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1861 := p.parse_csv_locator_paths()
		_t1860 = _t1861
	}
	csv_locator_paths1192 := _t1860
	p.popPath()
	p.pushPath(int(2))
	var _t1862 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1863 := p.parse_csv_locator_inline_data()
		_t1862 = ptr(_t1863)
	}
	csv_locator_inline_data1193 := _t1862
	p.popPath()
	p.consumeLiteral(")")
	_t1864 := csv_locator_paths1192
	if csv_locator_paths1192 == nil {
		_t1864 = []string{}
	}
	_t1865 := &pb.CSVLocator{Paths: _t1864, InlineData: []byte(deref(csv_locator_inline_data1193, ""))}
	result1195 := _t1865
	p.recordSpan(int(span_start1194))
	return result1195
}

func (p *Parser) parse_csv_locator_paths() []string {
	span_start1204 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1200 := []string{}
	cond1201 := p.matchLookaheadTerminal("STRING", 0)
	idx1202 := 0
	for cond1201 {
		p.pushPath(int(idx1202))
		item1203 := p.consumeTerminal("STRING").Value.str
		p.popPath()
		xs1200 = append(xs1200, item1203)
		idx1202 = (idx1202 + 1)
		cond1201 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1199 := xs1200
	p.consumeLiteral(")")
	result1205 := strings1199
	p.recordSpan(int(span_start1204))
	return result1205
}

func (p *Parser) parse_csv_locator_inline_data() string {
	span_start1207 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1206 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1208 := string1206
	p.recordSpan(int(span_start1207))
	return result1208
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1210 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1866 := p.parse_config_dict()
	config_dict1209 := _t1866
	p.consumeLiteral(")")
	_t1867 := p.construct_csv_config(config_dict1209)
	result1211 := _t1867
	p.recordSpan(int(span_start1210))
	return result1211
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	span_start1220 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1216 := []*pb.CSVColumn{}
	cond1217 := p.matchLookaheadLiteral("(", 0)
	idx1218 := 0
	for cond1217 {
		p.pushPath(int(idx1218))
		_t1868 := p.parse_csv_column()
		item1219 := _t1868
		p.popPath()
		xs1216 = append(xs1216, item1219)
		idx1218 = (idx1218 + 1)
		cond1217 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns1215 := xs1216
	p.consumeLiteral(")")
	result1221 := csv_columns1215
	p.recordSpan(int(span_start1220))
	return result1221
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	span_start1232 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(int(1))
	string1222 := p.consumeTerminal("STRING").Value.str
	p.popPath()
	p.pushPath(int(2))
	_t1869 := p.parse_relation_id()
	relation_id1223 := _t1869
	p.popPath()
	p.consumeLiteral("[")
	p.pushPath(int(3))
	xs1228 := []*pb.Type{}
	cond1229 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx1230 := 0
	for cond1229 {
		p.pushPath(int(idx1230))
		_t1870 := p.parse_type()
		item1231 := _t1870
		p.popPath()
		xs1228 = append(xs1228, item1231)
		idx1230 = (idx1230 + 1)
		cond1229 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1227 := xs1228
	p.popPath()
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1871 := &pb.CSVColumn{ColumnName: string1222, TargetId: relation_id1223, Types: types1227}
	result1233 := _t1871
	p.recordSpan(int(span_start1232))
	return result1233
}

func (p *Parser) parse_csv_asof() string {
	span_start1235 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1234 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1236 := string1234
	p.recordSpan(int(span_start1235))
	return result1236
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1238 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	p.pushPath(int(1))
	_t1872 := p.parse_fragment_id()
	fragment_id1237 := _t1872
	p.popPath()
	p.consumeLiteral(")")
	_t1873 := &pb.Undefine{FragmentId: fragment_id1237}
	result1239 := _t1873
	p.recordSpan(int(span_start1238))
	return result1239
}

func (p *Parser) parse_context() *pb.Context {
	span_start1248 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	p.pushPath(int(1))
	xs1244 := []*pb.RelationId{}
	cond1245 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx1246 := 0
	for cond1245 {
		p.pushPath(int(idx1246))
		_t1874 := p.parse_relation_id()
		item1247 := _t1874
		p.popPath()
		xs1244 = append(xs1244, item1247)
		idx1246 = (idx1246 + 1)
		cond1245 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1243 := xs1244
	p.popPath()
	p.consumeLiteral(")")
	_t1875 := &pb.Context{Relations: relation_ids1243}
	result1249 := _t1875
	p.recordSpan(int(span_start1248))
	return result1249
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1252 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	p.pushPath(int(1))
	_t1876 := p.parse_rel_edb_path()
	rel_edb_path1250 := _t1876
	p.popPath()
	p.pushPath(int(2))
	_t1877 := p.parse_relation_id()
	relation_id1251 := _t1877
	p.popPath()
	p.consumeLiteral(")")
	_t1878 := &pb.Snapshot{DestinationPath: rel_edb_path1250, SourceRelation: relation_id1251}
	result1253 := _t1878
	p.recordSpan(int(span_start1252))
	return result1253
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	span_start1262 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1258 := []*pb.Read{}
	cond1259 := p.matchLookaheadLiteral("(", 0)
	idx1260 := 0
	for cond1259 {
		p.pushPath(int(idx1260))
		_t1879 := p.parse_read()
		item1261 := _t1879
		p.popPath()
		xs1258 = append(xs1258, item1261)
		idx1260 = (idx1260 + 1)
		cond1259 = p.matchLookaheadLiteral("(", 0)
	}
	reads1257 := xs1258
	p.consumeLiteral(")")
	result1263 := reads1257
	p.recordSpan(int(span_start1262))
	return result1263
}

func (p *Parser) parse_read() *pb.Read {
	span_start1270 := int64(p.spanStart())
	var _t1880 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1881 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1881 = 2
		} else {
			var _t1882 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1882 = 1
			} else {
				var _t1883 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1883 = 4
				} else {
					var _t1884 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1884 = 0
					} else {
						var _t1885 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1885 = 3
						} else {
							_t1885 = -1
						}
						_t1884 = _t1885
					}
					_t1883 = _t1884
				}
				_t1882 = _t1883
			}
			_t1881 = _t1882
		}
		_t1880 = _t1881
	} else {
		_t1880 = -1
	}
	prediction1264 := _t1880
	var _t1886 *pb.Read
	if prediction1264 == 4 {
		p.pushPath(int(5))
		_t1887 := p.parse_export()
		export1269 := _t1887
		p.popPath()
		_t1888 := &pb.Read{}
		_t1888.ReadType = &pb.Read_Export{Export: export1269}
		_t1886 = _t1888
	} else {
		var _t1889 *pb.Read
		if prediction1264 == 3 {
			p.pushPath(int(4))
			_t1890 := p.parse_abort()
			abort1268 := _t1890
			p.popPath()
			_t1891 := &pb.Read{}
			_t1891.ReadType = &pb.Read_Abort{Abort: abort1268}
			_t1889 = _t1891
		} else {
			var _t1892 *pb.Read
			if prediction1264 == 2 {
				p.pushPath(int(3))
				_t1893 := p.parse_what_if()
				what_if1267 := _t1893
				p.popPath()
				_t1894 := &pb.Read{}
				_t1894.ReadType = &pb.Read_WhatIf{WhatIf: what_if1267}
				_t1892 = _t1894
			} else {
				var _t1895 *pb.Read
				if prediction1264 == 1 {
					p.pushPath(int(2))
					_t1896 := p.parse_output()
					output1266 := _t1896
					p.popPath()
					_t1897 := &pb.Read{}
					_t1897.ReadType = &pb.Read_Output{Output: output1266}
					_t1895 = _t1897
				} else {
					var _t1898 *pb.Read
					if prediction1264 == 0 {
						p.pushPath(int(1))
						_t1899 := p.parse_demand()
						demand1265 := _t1899
						p.popPath()
						_t1900 := &pb.Read{}
						_t1900.ReadType = &pb.Read_Demand{Demand: demand1265}
						_t1898 = _t1900
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1895 = _t1898
				}
				_t1892 = _t1895
			}
			_t1889 = _t1892
		}
		_t1886 = _t1889
	}
	result1271 := _t1886
	p.recordSpan(int(span_start1270))
	return result1271
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1273 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	p.pushPath(int(1))
	_t1901 := p.parse_relation_id()
	relation_id1272 := _t1901
	p.popPath()
	p.consumeLiteral(")")
	_t1902 := &pb.Demand{RelationId: relation_id1272}
	result1274 := _t1902
	p.recordSpan(int(span_start1273))
	return result1274
}

func (p *Parser) parse_output() *pb.Output {
	span_start1277 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	p.pushPath(int(1))
	_t1903 := p.parse_name()
	name1275 := _t1903
	p.popPath()
	p.pushPath(int(2))
	_t1904 := p.parse_relation_id()
	relation_id1276 := _t1904
	p.popPath()
	p.consumeLiteral(")")
	_t1905 := &pb.Output{Name: name1275, RelationId: relation_id1276}
	result1278 := _t1905
	p.recordSpan(int(span_start1277))
	return result1278
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1281 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	p.pushPath(int(1))
	_t1906 := p.parse_name()
	name1279 := _t1906
	p.popPath()
	p.pushPath(int(2))
	_t1907 := p.parse_epoch()
	epoch1280 := _t1907
	p.popPath()
	p.consumeLiteral(")")
	_t1908 := &pb.WhatIf{Branch: name1279, Epoch: epoch1280}
	result1282 := _t1908
	p.recordSpan(int(span_start1281))
	return result1282
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1285 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	p.pushPath(int(1))
	var _t1909 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1910 := p.parse_name()
		_t1909 = ptr(_t1910)
	}
	name1283 := _t1909
	p.popPath()
	p.pushPath(int(2))
	_t1911 := p.parse_relation_id()
	relation_id1284 := _t1911
	p.popPath()
	p.consumeLiteral(")")
	_t1912 := &pb.Abort{Name: deref(name1283, "abort"), RelationId: relation_id1284}
	result1286 := _t1912
	p.recordSpan(int(span_start1285))
	return result1286
}

func (p *Parser) parse_export() *pb.Export {
	span_start1288 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	p.pushPath(int(1))
	_t1913 := p.parse_export_csv_config()
	export_csv_config1287 := _t1913
	p.popPath()
	p.consumeLiteral(")")
	_t1914 := &pb.Export{}
	_t1914.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1287}
	result1289 := _t1914
	p.recordSpan(int(span_start1288))
	return result1289
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1293 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1915 := p.parse_export_csv_path()
	export_csv_path1290 := _t1915
	_t1916 := p.parse_export_csv_columns()
	export_csv_columns1291 := _t1916
	_t1917 := p.parse_config_dict()
	config_dict1292 := _t1917
	p.consumeLiteral(")")
	_t1918 := p.export_csv_config(export_csv_path1290, export_csv_columns1291, config_dict1292)
	result1294 := _t1918
	p.recordSpan(int(span_start1293))
	return result1294
}

func (p *Parser) parse_export_csv_path() string {
	span_start1296 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1295 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1297 := string1295
	p.recordSpan(int(span_start1296))
	return result1297
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	span_start1306 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1302 := []*pb.ExportCSVColumn{}
	cond1303 := p.matchLookaheadLiteral("(", 0)
	idx1304 := 0
	for cond1303 {
		p.pushPath(int(idx1304))
		_t1919 := p.parse_export_csv_column()
		item1305 := _t1919
		p.popPath()
		xs1302 = append(xs1302, item1305)
		idx1304 = (idx1304 + 1)
		cond1303 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1301 := xs1302
	p.consumeLiteral(")")
	result1307 := export_csv_columns1301
	p.recordSpan(int(span_start1306))
	return result1307
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1310 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(int(1))
	string1308 := p.consumeTerminal("STRING").Value.str
	p.popPath()
	p.pushPath(int(2))
	_t1920 := p.parse_relation_id()
	relation_id1309 := _t1920
	p.popPath()
	p.consumeLiteral(")")
	_t1921 := &pb.ExportCSVColumn{ColumnName: string1308, ColumnData: relation_id1309}
	result1311 := _t1921
	p.recordSpan(int(span_start1310))
	return result1311
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
