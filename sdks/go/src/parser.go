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
	var _t1846 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1846
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1847 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1847
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1848 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1848
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1849 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1849
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1850 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1850
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1851 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1851
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1852 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1852
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1853 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1853
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1854 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1854
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1855 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1855
	_t1856 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1856
	_t1857 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1857
	_t1858 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1858
	_t1859 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1859
	_t1860 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1860
	_t1861 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1861
	_t1862 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1862
	_t1863 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1863
	_t1864 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1864
	_t1865 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1865
	_t1866 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1866
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1867 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1867
	_t1868 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1868
	_t1869 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1869
	_t1870 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1870
	_t1871 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1871
	_t1872 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1872
	_t1873 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1873
	_t1874 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1874
	_t1875 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1875
	_t1876 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1876.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1876.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1876
	_t1877 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1877
}

func (p *Parser) default_configure() *pb.Configure {
	_t1878 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1878
	_t1879 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1879
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
	_t1880 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1880
	_t1881 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1881
	_t1882 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1882
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1883 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1883
	_t1884 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1884
	_t1885 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1885
	_t1886 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1886
	_t1887 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1887
	_t1888 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1888
	_t1889 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1889
	_t1890 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1890
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start602 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	p.pushPath(int(2))
	var _t1236 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1237 := p.parse_configure()
		_t1236 = _t1237
	}
	configure592 := _t1236
	p.popPath()
	p.pushPath(int(3))
	var _t1238 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1239 := p.parse_sync()
		_t1238 = _t1239
	}
	sync593 := _t1238
	p.popPath()
	p.pushPath(int(1))
	xs598 := []*pb.Epoch{}
	cond599 := p.matchLookaheadLiteral("(", 0)
	idx600 := 0
	for cond599 {
		p.pushPath(int(idx600))
		_t1240 := p.parse_epoch()
		item601 := _t1240
		p.popPath()
		xs598 = append(xs598, item601)
		idx600 = (idx600 + 1)
		cond599 = p.matchLookaheadLiteral("(", 0)
	}
	epochs597 := xs598
	p.popPath()
	p.consumeLiteral(")")
	_t1241 := p.default_configure()
	_t1242 := configure592
	if configure592 == nil {
		_t1242 = _t1241
	}
	_t1243 := &pb.Transaction{Epochs: epochs597, Configure: _t1242, Sync: sync593}
	result603 := _t1243
	p.recordSpan(int(span_start602))
	return result603
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start605 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1244 := p.parse_config_dict()
	config_dict604 := _t1244
	p.consumeLiteral(")")
	_t1245 := p.construct_configure(config_dict604)
	result606 := _t1245
	p.recordSpan(int(span_start605))
	return result606
}

func (p *Parser) parse_config_dict() [][]interface{} {
	span_start611 := int64(p.spanStart())
	p.consumeLiteral("{")
	xs607 := [][]interface{}{}
	cond608 := p.matchLookaheadLiteral(":", 0)
	for cond608 {
		_t1246 := p.parse_config_key_value()
		item609 := _t1246
		xs607 = append(xs607, item609)
		cond608 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values610 := xs607
	p.consumeLiteral("}")
	result612 := config_key_values610
	p.recordSpan(int(span_start611))
	return result612
}

func (p *Parser) parse_config_key_value() []interface{} {
	span_start615 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol613 := p.consumeTerminal("SYMBOL").Value.str
	_t1247 := p.parse_value()
	value614 := _t1247
	result616 := []interface{}{symbol613, value614}
	p.recordSpan(int(span_start615))
	return result616
}

func (p *Parser) parse_value() *pb.Value {
	span_start627 := int64(p.spanStart())
	var _t1248 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1248 = 9
	} else {
		var _t1249 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1249 = 8
		} else {
			var _t1250 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1250 = 9
			} else {
				var _t1251 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1252 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1252 = 1
					} else {
						var _t1253 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1253 = 0
						} else {
							_t1253 = -1
						}
						_t1252 = _t1253
					}
					_t1251 = _t1252
				} else {
					var _t1254 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1254 = 5
					} else {
						var _t1255 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1255 = 2
						} else {
							var _t1256 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1256 = 6
							} else {
								var _t1257 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1257 = 3
								} else {
									var _t1258 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1258 = 4
									} else {
										var _t1259 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1259 = 7
										} else {
											_t1259 = -1
										}
										_t1258 = _t1259
									}
									_t1257 = _t1258
								}
								_t1256 = _t1257
							}
							_t1255 = _t1256
						}
						_t1254 = _t1255
					}
					_t1251 = _t1254
				}
				_t1250 = _t1251
			}
			_t1249 = _t1250
		}
		_t1248 = _t1249
	}
	prediction617 := _t1248
	var _t1260 *pb.Value
	if prediction617 == 9 {
		_t1261 := p.parse_boolean_value()
		boolean_value626 := _t1261
		_t1262 := &pb.Value{}
		_t1262.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value626}
		_t1260 = _t1262
	} else {
		var _t1263 *pb.Value
		if prediction617 == 8 {
			p.consumeLiteral("missing")
			_t1264 := &pb.MissingValue{}
			_t1265 := &pb.Value{}
			_t1265.Value = &pb.Value_MissingValue{MissingValue: _t1264}
			_t1263 = _t1265
		} else {
			var _t1266 *pb.Value
			if prediction617 == 7 {
				decimal625 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1267 := &pb.Value{}
				_t1267.Value = &pb.Value_DecimalValue{DecimalValue: decimal625}
				_t1266 = _t1267
			} else {
				var _t1268 *pb.Value
				if prediction617 == 6 {
					int128624 := p.consumeTerminal("INT128").Value.int128
					_t1269 := &pb.Value{}
					_t1269.Value = &pb.Value_Int128Value{Int128Value: int128624}
					_t1268 = _t1269
				} else {
					var _t1270 *pb.Value
					if prediction617 == 5 {
						uint128623 := p.consumeTerminal("UINT128").Value.uint128
						_t1271 := &pb.Value{}
						_t1271.Value = &pb.Value_Uint128Value{Uint128Value: uint128623}
						_t1270 = _t1271
					} else {
						var _t1272 *pb.Value
						if prediction617 == 4 {
							float622 := p.consumeTerminal("FLOAT").Value.f64
							_t1273 := &pb.Value{}
							_t1273.Value = &pb.Value_FloatValue{FloatValue: float622}
							_t1272 = _t1273
						} else {
							var _t1274 *pb.Value
							if prediction617 == 3 {
								int621 := p.consumeTerminal("INT").Value.i64
								_t1275 := &pb.Value{}
								_t1275.Value = &pb.Value_IntValue{IntValue: int621}
								_t1274 = _t1275
							} else {
								var _t1276 *pb.Value
								if prediction617 == 2 {
									string620 := p.consumeTerminal("STRING").Value.str
									_t1277 := &pb.Value{}
									_t1277.Value = &pb.Value_StringValue{StringValue: string620}
									_t1276 = _t1277
								} else {
									var _t1278 *pb.Value
									if prediction617 == 1 {
										_t1279 := p.parse_datetime()
										datetime619 := _t1279
										_t1280 := &pb.Value{}
										_t1280.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime619}
										_t1278 = _t1280
									} else {
										var _t1281 *pb.Value
										if prediction617 == 0 {
											_t1282 := p.parse_date()
											date618 := _t1282
											_t1283 := &pb.Value{}
											_t1283.Value = &pb.Value_DateValue{DateValue: date618}
											_t1281 = _t1283
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1278 = _t1281
									}
									_t1276 = _t1278
								}
								_t1274 = _t1276
							}
							_t1272 = _t1274
						}
						_t1270 = _t1272
					}
					_t1268 = _t1270
				}
				_t1266 = _t1268
			}
			_t1263 = _t1266
		}
		_t1260 = _t1263
	}
	result628 := _t1260
	p.recordSpan(int(span_start627))
	return result628
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start632 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	p.pushPath(int(1))
	int629 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3630 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(3))
	int_4631 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.consumeLiteral(")")
	_t1284 := &pb.DateValue{Year: int32(int629), Month: int32(int_3630), Day: int32(int_4631)}
	result633 := _t1284
	p.recordSpan(int(span_start632))
	return result633
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start641 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	p.pushPath(int(1))
	int634 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3635 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(3))
	int_4636 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(4))
	int_5637 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(5))
	int_6638 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(6))
	int_7639 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(7))
	var _t1285 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1285 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8640 := _t1285
	p.popPath()
	p.consumeLiteral(")")
	_t1286 := &pb.DateTimeValue{Year: int32(int634), Month: int32(int_3635), Day: int32(int_4636), Hour: int32(int_5637), Minute: int32(int_6638), Second: int32(int_7639), Microsecond: int32(deref(int_8640, 0))}
	result642 := _t1286
	p.recordSpan(int(span_start641))
	return result642
}

func (p *Parser) parse_boolean_value() bool {
	span_start644 := int64(p.spanStart())
	var _t1287 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1287 = 0
	} else {
		var _t1288 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1288 = 1
		} else {
			_t1288 = -1
		}
		_t1287 = _t1288
	}
	prediction643 := _t1287
	var _t1289 bool
	if prediction643 == 1 {
		p.consumeLiteral("false")
		_t1289 = false
	} else {
		var _t1290 bool
		if prediction643 == 0 {
			p.consumeLiteral("true")
			_t1290 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1289 = _t1290
	}
	result645 := _t1289
	p.recordSpan(int(span_start644))
	return result645
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start654 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	p.pushPath(int(1))
	xs650 := []*pb.FragmentId{}
	cond651 := p.matchLookaheadLiteral(":", 0)
	idx652 := 0
	for cond651 {
		p.pushPath(int(idx652))
		_t1291 := p.parse_fragment_id()
		item653 := _t1291
		p.popPath()
		xs650 = append(xs650, item653)
		idx652 = (idx652 + 1)
		cond651 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids649 := xs650
	p.popPath()
	p.consumeLiteral(")")
	_t1292 := &pb.Sync{Fragments: fragment_ids649}
	result655 := _t1292
	p.recordSpan(int(span_start654))
	return result655
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start657 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol656 := p.consumeTerminal("SYMBOL").Value.str
	result658 := &pb.FragmentId{Id: []byte(symbol656)}
	p.recordSpan(int(span_start657))
	return result658
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start661 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	p.pushPath(int(1))
	var _t1293 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1294 := p.parse_epoch_writes()
		_t1293 = _t1294
	}
	epoch_writes659 := _t1293
	p.popPath()
	p.pushPath(int(2))
	var _t1295 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1296 := p.parse_epoch_reads()
		_t1295 = _t1296
	}
	epoch_reads660 := _t1295
	p.popPath()
	p.consumeLiteral(")")
	_t1297 := epoch_writes659
	if epoch_writes659 == nil {
		_t1297 = []*pb.Write{}
	}
	_t1298 := epoch_reads660
	if epoch_reads660 == nil {
		_t1298 = []*pb.Read{}
	}
	_t1299 := &pb.Epoch{Writes: _t1297, Reads: _t1298}
	result662 := _t1299
	p.recordSpan(int(span_start661))
	return result662
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	span_start667 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs663 := []*pb.Write{}
	cond664 := p.matchLookaheadLiteral("(", 0)
	for cond664 {
		_t1300 := p.parse_write()
		item665 := _t1300
		xs663 = append(xs663, item665)
		cond664 = p.matchLookaheadLiteral("(", 0)
	}
	writes666 := xs663
	p.consumeLiteral(")")
	result668 := writes666
	p.recordSpan(int(span_start667))
	return result668
}

func (p *Parser) parse_write() *pb.Write {
	span_start674 := int64(p.spanStart())
	var _t1301 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1302 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1302 = 1
		} else {
			var _t1303 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1303 = 3
			} else {
				var _t1304 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1304 = 0
				} else {
					var _t1305 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1305 = 2
					} else {
						_t1305 = -1
					}
					_t1304 = _t1305
				}
				_t1303 = _t1304
			}
			_t1302 = _t1303
		}
		_t1301 = _t1302
	} else {
		_t1301 = -1
	}
	prediction669 := _t1301
	var _t1306 *pb.Write
	if prediction669 == 3 {
		_t1307 := p.parse_snapshot()
		snapshot673 := _t1307
		_t1308 := &pb.Write{}
		_t1308.WriteType = &pb.Write_Snapshot{Snapshot: snapshot673}
		_t1306 = _t1308
	} else {
		var _t1309 *pb.Write
		if prediction669 == 2 {
			_t1310 := p.parse_context()
			context672 := _t1310
			_t1311 := &pb.Write{}
			_t1311.WriteType = &pb.Write_Context{Context: context672}
			_t1309 = _t1311
		} else {
			var _t1312 *pb.Write
			if prediction669 == 1 {
				_t1313 := p.parse_undefine()
				undefine671 := _t1313
				_t1314 := &pb.Write{}
				_t1314.WriteType = &pb.Write_Undefine{Undefine: undefine671}
				_t1312 = _t1314
			} else {
				var _t1315 *pb.Write
				if prediction669 == 0 {
					_t1316 := p.parse_define()
					define670 := _t1316
					_t1317 := &pb.Write{}
					_t1317.WriteType = &pb.Write_Define{Define: define670}
					_t1315 = _t1317
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1312 = _t1315
			}
			_t1309 = _t1312
		}
		_t1306 = _t1309
	}
	result675 := _t1306
	p.recordSpan(int(span_start674))
	return result675
}

func (p *Parser) parse_define() *pb.Define {
	span_start677 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	p.pushPath(int(1))
	_t1318 := p.parse_fragment()
	fragment676 := _t1318
	p.popPath()
	p.consumeLiteral(")")
	_t1319 := &pb.Define{Fragment: fragment676}
	result678 := _t1319
	p.recordSpan(int(span_start677))
	return result678
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start684 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1320 := p.parse_new_fragment_id()
	new_fragment_id679 := _t1320
	xs680 := []*pb.Declaration{}
	cond681 := p.matchLookaheadLiteral("(", 0)
	for cond681 {
		_t1321 := p.parse_declaration()
		item682 := _t1321
		xs680 = append(xs680, item682)
		cond681 = p.matchLookaheadLiteral("(", 0)
	}
	declarations683 := xs680
	p.consumeLiteral(")")
	result685 := p.constructFragment(new_fragment_id679, declarations683)
	p.recordSpan(int(span_start684))
	return result685
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start687 := int64(p.spanStart())
	_t1322 := p.parse_fragment_id()
	fragment_id686 := _t1322
	p.startFragment(fragment_id686)
	result688 := fragment_id686
	p.recordSpan(int(span_start687))
	return result688
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start694 := int64(p.spanStart())
	var _t1323 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1324 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1324 = 3
		} else {
			var _t1325 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1325 = 2
			} else {
				var _t1326 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1326 = 0
				} else {
					var _t1327 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1327 = 3
					} else {
						var _t1328 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1328 = 3
						} else {
							var _t1329 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1329 = 1
							} else {
								_t1329 = -1
							}
							_t1328 = _t1329
						}
						_t1327 = _t1328
					}
					_t1326 = _t1327
				}
				_t1325 = _t1326
			}
			_t1324 = _t1325
		}
		_t1323 = _t1324
	} else {
		_t1323 = -1
	}
	prediction689 := _t1323
	var _t1330 *pb.Declaration
	if prediction689 == 3 {
		_t1331 := p.parse_data()
		data693 := _t1331
		_t1332 := &pb.Declaration{}
		_t1332.DeclarationType = &pb.Declaration_Data{Data: data693}
		_t1330 = _t1332
	} else {
		var _t1333 *pb.Declaration
		if prediction689 == 2 {
			_t1334 := p.parse_constraint()
			constraint692 := _t1334
			_t1335 := &pb.Declaration{}
			_t1335.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint692}
			_t1333 = _t1335
		} else {
			var _t1336 *pb.Declaration
			if prediction689 == 1 {
				_t1337 := p.parse_algorithm()
				algorithm691 := _t1337
				_t1338 := &pb.Declaration{}
				_t1338.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm691}
				_t1336 = _t1338
			} else {
				var _t1339 *pb.Declaration
				if prediction689 == 0 {
					_t1340 := p.parse_def()
					def690 := _t1340
					_t1341 := &pb.Declaration{}
					_t1341.DeclarationType = &pb.Declaration_Def{Def: def690}
					_t1339 = _t1341
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1336 = _t1339
			}
			_t1333 = _t1336
		}
		_t1330 = _t1333
	}
	result695 := _t1330
	p.recordSpan(int(span_start694))
	return result695
}

func (p *Parser) parse_def() *pb.Def {
	span_start699 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	p.pushPath(int(1))
	_t1342 := p.parse_relation_id()
	relation_id696 := _t1342
	p.popPath()
	p.pushPath(int(2))
	_t1343 := p.parse_abstraction()
	abstraction697 := _t1343
	p.popPath()
	p.pushPath(int(3))
	var _t1344 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1345 := p.parse_attrs()
		_t1344 = _t1345
	}
	attrs698 := _t1344
	p.popPath()
	p.consumeLiteral(")")
	_t1346 := attrs698
	if attrs698 == nil {
		_t1346 = []*pb.Attribute{}
	}
	_t1347 := &pb.Def{Name: relation_id696, Body: abstraction697, Attrs: _t1346}
	result700 := _t1347
	p.recordSpan(int(span_start699))
	return result700
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start704 := int64(p.spanStart())
	var _t1348 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1348 = 0
	} else {
		var _t1349 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1349 = 1
		} else {
			_t1349 = -1
		}
		_t1348 = _t1349
	}
	prediction701 := _t1348
	var _t1350 *pb.RelationId
	if prediction701 == 1 {
		uint128703 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128703
		_t1350 = &pb.RelationId{IdLow: uint128703.Low, IdHigh: uint128703.High}
	} else {
		var _t1351 *pb.RelationId
		if prediction701 == 0 {
			p.consumeLiteral(":")
			symbol702 := p.consumeTerminal("SYMBOL").Value.str
			_t1351 = p.relationIdFromString(symbol702)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1350 = _t1351
	}
	result705 := _t1350
	p.recordSpan(int(span_start704))
	return result705
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start708 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1352 := p.parse_bindings()
	bindings706 := _t1352
	p.pushPath(int(2))
	_t1353 := p.parse_formula()
	formula707 := _t1353
	p.popPath()
	p.consumeLiteral(")")
	_t1354 := &pb.Abstraction{Vars: listConcat(bindings706[0].([]*pb.Binding), bindings706[1].([]*pb.Binding)), Value: formula707}
	result709 := _t1354
	p.recordSpan(int(span_start708))
	return result709
}

func (p *Parser) parse_bindings() []interface{} {
	span_start715 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs710 := []*pb.Binding{}
	cond711 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond711 {
		_t1355 := p.parse_binding()
		item712 := _t1355
		xs710 = append(xs710, item712)
		cond711 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings713 := xs710
	var _t1356 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1357 := p.parse_value_bindings()
		_t1356 = _t1357
	}
	value_bindings714 := _t1356
	p.consumeLiteral("]")
	_t1358 := value_bindings714
	if value_bindings714 == nil {
		_t1358 = []*pb.Binding{}
	}
	result716 := []interface{}{bindings713, _t1358}
	p.recordSpan(int(span_start715))
	return result716
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start719 := int64(p.spanStart())
	symbol717 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	p.pushPath(int(2))
	_t1359 := p.parse_type()
	type718 := _t1359
	p.popPath()
	_t1360 := &pb.Var{Name: symbol717}
	_t1361 := &pb.Binding{Var: _t1360, Type: type718}
	result720 := _t1361
	p.recordSpan(int(span_start719))
	return result720
}

func (p *Parser) parse_type() *pb.Type {
	span_start733 := int64(p.spanStart())
	var _t1362 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1362 = 0
	} else {
		var _t1363 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1363 = 4
		} else {
			var _t1364 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1364 = 1
			} else {
				var _t1365 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1365 = 8
				} else {
					var _t1366 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1366 = 5
					} else {
						var _t1367 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1367 = 2
						} else {
							var _t1368 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1368 = 3
							} else {
								var _t1369 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1369 = 7
								} else {
									var _t1370 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1370 = 6
									} else {
										var _t1371 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1371 = 10
										} else {
											var _t1372 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1372 = 9
											} else {
												_t1372 = -1
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
	}
	prediction721 := _t1362
	var _t1373 *pb.Type
	if prediction721 == 10 {
		_t1374 := p.parse_boolean_type()
		boolean_type732 := _t1374
		_t1375 := &pb.Type{}
		_t1375.Type = &pb.Type_BooleanType{BooleanType: boolean_type732}
		_t1373 = _t1375
	} else {
		var _t1376 *pb.Type
		if prediction721 == 9 {
			_t1377 := p.parse_decimal_type()
			decimal_type731 := _t1377
			_t1378 := &pb.Type{}
			_t1378.Type = &pb.Type_DecimalType{DecimalType: decimal_type731}
			_t1376 = _t1378
		} else {
			var _t1379 *pb.Type
			if prediction721 == 8 {
				_t1380 := p.parse_missing_type()
				missing_type730 := _t1380
				_t1381 := &pb.Type{}
				_t1381.Type = &pb.Type_MissingType{MissingType: missing_type730}
				_t1379 = _t1381
			} else {
				var _t1382 *pb.Type
				if prediction721 == 7 {
					_t1383 := p.parse_datetime_type()
					datetime_type729 := _t1383
					_t1384 := &pb.Type{}
					_t1384.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type729}
					_t1382 = _t1384
				} else {
					var _t1385 *pb.Type
					if prediction721 == 6 {
						_t1386 := p.parse_date_type()
						date_type728 := _t1386
						_t1387 := &pb.Type{}
						_t1387.Type = &pb.Type_DateType{DateType: date_type728}
						_t1385 = _t1387
					} else {
						var _t1388 *pb.Type
						if prediction721 == 5 {
							_t1389 := p.parse_int128_type()
							int128_type727 := _t1389
							_t1390 := &pb.Type{}
							_t1390.Type = &pb.Type_Int128Type{Int128Type: int128_type727}
							_t1388 = _t1390
						} else {
							var _t1391 *pb.Type
							if prediction721 == 4 {
								_t1392 := p.parse_uint128_type()
								uint128_type726 := _t1392
								_t1393 := &pb.Type{}
								_t1393.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type726}
								_t1391 = _t1393
							} else {
								var _t1394 *pb.Type
								if prediction721 == 3 {
									_t1395 := p.parse_float_type()
									float_type725 := _t1395
									_t1396 := &pb.Type{}
									_t1396.Type = &pb.Type_FloatType{FloatType: float_type725}
									_t1394 = _t1396
								} else {
									var _t1397 *pb.Type
									if prediction721 == 2 {
										_t1398 := p.parse_int_type()
										int_type724 := _t1398
										_t1399 := &pb.Type{}
										_t1399.Type = &pb.Type_IntType{IntType: int_type724}
										_t1397 = _t1399
									} else {
										var _t1400 *pb.Type
										if prediction721 == 1 {
											_t1401 := p.parse_string_type()
											string_type723 := _t1401
											_t1402 := &pb.Type{}
											_t1402.Type = &pb.Type_StringType{StringType: string_type723}
											_t1400 = _t1402
										} else {
											var _t1403 *pb.Type
											if prediction721 == 0 {
												_t1404 := p.parse_unspecified_type()
												unspecified_type722 := _t1404
												_t1405 := &pb.Type{}
												_t1405.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type722}
												_t1403 = _t1405
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t1382 = _t1385
				}
				_t1379 = _t1382
			}
			_t1376 = _t1379
		}
		_t1373 = _t1376
	}
	result734 := _t1373
	p.recordSpan(int(span_start733))
	return result734
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1406 := &pb.UnspecifiedType{}
	result736 := _t1406
	p.recordSpan(int(span_start735))
	return result736
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1407 := &pb.StringType{}
	result738 := _t1407
	p.recordSpan(int(span_start737))
	return result738
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start739 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1408 := &pb.IntType{}
	result740 := _t1408
	p.recordSpan(int(span_start739))
	return result740
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start741 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1409 := &pb.FloatType{}
	result742 := _t1409
	p.recordSpan(int(span_start741))
	return result742
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1410 := &pb.UInt128Type{}
	result744 := _t1410
	p.recordSpan(int(span_start743))
	return result744
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start745 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1411 := &pb.Int128Type{}
	result746 := _t1411
	p.recordSpan(int(span_start745))
	return result746
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start747 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1412 := &pb.DateType{}
	result748 := _t1412
	p.recordSpan(int(span_start747))
	return result748
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1413 := &pb.DateTimeType{}
	result750 := _t1413
	p.recordSpan(int(span_start749))
	return result750
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start751 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1414 := &pb.MissingType{}
	result752 := _t1414
	p.recordSpan(int(span_start751))
	return result752
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start755 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	p.pushPath(int(1))
	int753 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.pushPath(int(2))
	int_3754 := p.consumeTerminal("INT").Value.i64
	p.popPath()
	p.consumeLiteral(")")
	_t1415 := &pb.DecimalType{Precision: int32(int753), Scale: int32(int_3754)}
	result756 := _t1415
	p.recordSpan(int(span_start755))
	return result756
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1416 := &pb.BooleanType{}
	result758 := _t1416
	p.recordSpan(int(span_start757))
	return result758
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	span_start763 := int64(p.spanStart())
	p.consumeLiteral("|")
	xs759 := []*pb.Binding{}
	cond760 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond760 {
		_t1417 := p.parse_binding()
		item761 := _t1417
		xs759 = append(xs759, item761)
		cond760 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings762 := xs759
	result764 := bindings762
	p.recordSpan(int(span_start763))
	return result764
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start779 := int64(p.spanStart())
	var _t1418 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1419 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1419 = 0
		} else {
			var _t1420 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1420 = 11
			} else {
				var _t1421 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1421 = 3
				} else {
					var _t1422 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1422 = 10
					} else {
						var _t1423 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1423 = 9
						} else {
							var _t1424 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1424 = 5
							} else {
								var _t1425 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1425 = 6
								} else {
									var _t1426 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1426 = 7
									} else {
										var _t1427 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1427 = 1
										} else {
											var _t1428 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1428 = 2
											} else {
												var _t1429 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1429 = 12
												} else {
													var _t1430 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1430 = 8
													} else {
														var _t1431 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1431 = 4
														} else {
															var _t1432 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1432 = 10
															} else {
																var _t1433 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1433 = 10
																} else {
																	var _t1434 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1434 = 10
																	} else {
																		var _t1435 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1435 = 10
																		} else {
																			var _t1436 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1436 = 10
																			} else {
																				var _t1437 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1437 = 10
																				} else {
																					var _t1438 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1438 = 10
																					} else {
																						var _t1439 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1439 = 10
																						} else {
																							var _t1440 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1440 = 10
																							} else {
																								_t1440 = -1
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
																		_t1434 = _t1435
																	}
																	_t1433 = _t1434
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
		_t1418 = _t1419
	} else {
		_t1418 = -1
	}
	prediction765 := _t1418
	var _t1441 *pb.Formula
	if prediction765 == 12 {
		_t1442 := p.parse_cast()
		cast778 := _t1442
		_t1443 := &pb.Formula{}
		_t1443.FormulaType = &pb.Formula_Cast{Cast: cast778}
		_t1441 = _t1443
	} else {
		var _t1444 *pb.Formula
		if prediction765 == 11 {
			_t1445 := p.parse_rel_atom()
			rel_atom777 := _t1445
			_t1446 := &pb.Formula{}
			_t1446.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom777}
			_t1444 = _t1446
		} else {
			var _t1447 *pb.Formula
			if prediction765 == 10 {
				_t1448 := p.parse_primitive()
				primitive776 := _t1448
				_t1449 := &pb.Formula{}
				_t1449.FormulaType = &pb.Formula_Primitive{Primitive: primitive776}
				_t1447 = _t1449
			} else {
				var _t1450 *pb.Formula
				if prediction765 == 9 {
					_t1451 := p.parse_pragma()
					pragma775 := _t1451
					_t1452 := &pb.Formula{}
					_t1452.FormulaType = &pb.Formula_Pragma{Pragma: pragma775}
					_t1450 = _t1452
				} else {
					var _t1453 *pb.Formula
					if prediction765 == 8 {
						_t1454 := p.parse_atom()
						atom774 := _t1454
						_t1455 := &pb.Formula{}
						_t1455.FormulaType = &pb.Formula_Atom{Atom: atom774}
						_t1453 = _t1455
					} else {
						var _t1456 *pb.Formula
						if prediction765 == 7 {
							_t1457 := p.parse_ffi()
							ffi773 := _t1457
							_t1458 := &pb.Formula{}
							_t1458.FormulaType = &pb.Formula_Ffi{Ffi: ffi773}
							_t1456 = _t1458
						} else {
							var _t1459 *pb.Formula
							if prediction765 == 6 {
								_t1460 := p.parse_not()
								not772 := _t1460
								_t1461 := &pb.Formula{}
								_t1461.FormulaType = &pb.Formula_Not{Not: not772}
								_t1459 = _t1461
							} else {
								var _t1462 *pb.Formula
								if prediction765 == 5 {
									_t1463 := p.parse_disjunction()
									disjunction771 := _t1463
									_t1464 := &pb.Formula{}
									_t1464.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction771}
									_t1462 = _t1464
								} else {
									var _t1465 *pb.Formula
									if prediction765 == 4 {
										_t1466 := p.parse_conjunction()
										conjunction770 := _t1466
										_t1467 := &pb.Formula{}
										_t1467.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction770}
										_t1465 = _t1467
									} else {
										var _t1468 *pb.Formula
										if prediction765 == 3 {
											_t1469 := p.parse_reduce()
											reduce769 := _t1469
											_t1470 := &pb.Formula{}
											_t1470.FormulaType = &pb.Formula_Reduce{Reduce: reduce769}
											_t1468 = _t1470
										} else {
											var _t1471 *pb.Formula
											if prediction765 == 2 {
												_t1472 := p.parse_exists()
												exists768 := _t1472
												_t1473 := &pb.Formula{}
												_t1473.FormulaType = &pb.Formula_Exists{Exists: exists768}
												_t1471 = _t1473
											} else {
												var _t1474 *pb.Formula
												if prediction765 == 1 {
													_t1475 := p.parse_false()
													false767 := _t1475
													_t1476 := &pb.Formula{}
													_t1476.FormulaType = &pb.Formula_Disjunction{Disjunction: false767}
													_t1474 = _t1476
												} else {
													var _t1477 *pb.Formula
													if prediction765 == 0 {
														_t1478 := p.parse_true()
														true766 := _t1478
														_t1479 := &pb.Formula{}
														_t1479.FormulaType = &pb.Formula_Conjunction{Conjunction: true766}
														_t1477 = _t1479
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1474 = _t1477
												}
												_t1471 = _t1474
											}
											_t1468 = _t1471
										}
										_t1465 = _t1468
									}
									_t1462 = _t1465
								}
								_t1459 = _t1462
							}
							_t1456 = _t1459
						}
						_t1453 = _t1456
					}
					_t1450 = _t1453
				}
				_t1447 = _t1450
			}
			_t1444 = _t1447
		}
		_t1441 = _t1444
	}
	result780 := _t1441
	p.recordSpan(int(span_start779))
	return result780
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start781 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1480 := &pb.Conjunction{Args: []*pb.Formula{}}
	result782 := _t1480
	p.recordSpan(int(span_start781))
	return result782
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start783 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1481 := &pb.Disjunction{Args: []*pb.Formula{}}
	result784 := _t1481
	p.recordSpan(int(span_start783))
	return result784
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start787 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1482 := p.parse_bindings()
	bindings785 := _t1482
	_t1483 := p.parse_formula()
	formula786 := _t1483
	p.consumeLiteral(")")
	_t1484 := &pb.Abstraction{Vars: listConcat(bindings785[0].([]*pb.Binding), bindings785[1].([]*pb.Binding)), Value: formula786}
	_t1485 := &pb.Exists{Body: _t1484}
	result788 := _t1485
	p.recordSpan(int(span_start787))
	return result788
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start792 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	p.pushPath(int(1))
	_t1486 := p.parse_abstraction()
	abstraction789 := _t1486
	p.popPath()
	p.pushPath(int(2))
	_t1487 := p.parse_abstraction()
	abstraction_3790 := _t1487
	p.popPath()
	p.pushPath(int(3))
	_t1488 := p.parse_terms()
	terms791 := _t1488
	p.popPath()
	p.consumeLiteral(")")
	_t1489 := &pb.Reduce{Op: abstraction789, Body: abstraction_3790, Terms: terms791}
	result793 := _t1489
	p.recordSpan(int(span_start792))
	return result793
}

func (p *Parser) parse_terms() []*pb.Term {
	span_start798 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs794 := []*pb.Term{}
	cond795 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond795 {
		_t1490 := p.parse_term()
		item796 := _t1490
		xs794 = append(xs794, item796)
		cond795 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms797 := xs794
	p.consumeLiteral(")")
	result799 := terms797
	p.recordSpan(int(span_start798))
	return result799
}

func (p *Parser) parse_term() *pb.Term {
	span_start803 := int64(p.spanStart())
	var _t1491 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1491 = 1
	} else {
		var _t1492 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1492 = 1
		} else {
			var _t1493 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1493 = 1
			} else {
				var _t1494 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1494 = 1
				} else {
					var _t1495 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1495 = 1
					} else {
						var _t1496 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1496 = 0
						} else {
							var _t1497 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1497 = 1
							} else {
								var _t1498 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1498 = 1
								} else {
									var _t1499 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1499 = 1
									} else {
										var _t1500 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1500 = 1
										} else {
											var _t1501 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1501 = 1
											} else {
												_t1501 = -1
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
				}
				_t1493 = _t1494
			}
			_t1492 = _t1493
		}
		_t1491 = _t1492
	}
	prediction800 := _t1491
	var _t1502 *pb.Term
	if prediction800 == 1 {
		_t1503 := p.parse_constant()
		constant802 := _t1503
		_t1504 := &pb.Term{}
		_t1504.TermType = &pb.Term_Constant{Constant: constant802}
		_t1502 = _t1504
	} else {
		var _t1505 *pb.Term
		if prediction800 == 0 {
			_t1506 := p.parse_var()
			var801 := _t1506
			_t1507 := &pb.Term{}
			_t1507.TermType = &pb.Term_Var{Var: var801}
			_t1505 = _t1507
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1502 = _t1505
	}
	result804 := _t1502
	p.recordSpan(int(span_start803))
	return result804
}

func (p *Parser) parse_var() *pb.Var {
	span_start806 := int64(p.spanStart())
	symbol805 := p.consumeTerminal("SYMBOL").Value.str
	_t1508 := &pb.Var{Name: symbol805}
	result807 := _t1508
	p.recordSpan(int(span_start806))
	return result807
}

func (p *Parser) parse_constant() *pb.Value {
	span_start809 := int64(p.spanStart())
	_t1509 := p.parse_value()
	value808 := _t1509
	result810 := value808
	p.recordSpan(int(span_start809))
	return result810
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start819 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	p.pushPath(int(1))
	xs815 := []*pb.Formula{}
	cond816 := p.matchLookaheadLiteral("(", 0)
	idx817 := 0
	for cond816 {
		p.pushPath(int(idx817))
		_t1510 := p.parse_formula()
		item818 := _t1510
		p.popPath()
		xs815 = append(xs815, item818)
		idx817 = (idx817 + 1)
		cond816 = p.matchLookaheadLiteral("(", 0)
	}
	formulas814 := xs815
	p.popPath()
	p.consumeLiteral(")")
	_t1511 := &pb.Conjunction{Args: formulas814}
	result820 := _t1511
	p.recordSpan(int(span_start819))
	return result820
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.pushPath(int(1))
	xs825 := []*pb.Formula{}
	cond826 := p.matchLookaheadLiteral("(", 0)
	idx827 := 0
	for cond826 {
		p.pushPath(int(idx827))
		_t1512 := p.parse_formula()
		item828 := _t1512
		p.popPath()
		xs825 = append(xs825, item828)
		idx827 = (idx827 + 1)
		cond826 = p.matchLookaheadLiteral("(", 0)
	}
	formulas824 := xs825
	p.popPath()
	p.consumeLiteral(")")
	_t1513 := &pb.Disjunction{Args: formulas824}
	result830 := _t1513
	p.recordSpan(int(span_start829))
	return result830
}

func (p *Parser) parse_not() *pb.Not {
	span_start832 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	p.pushPath(int(1))
	_t1514 := p.parse_formula()
	formula831 := _t1514
	p.popPath()
	p.consumeLiteral(")")
	_t1515 := &pb.Not{Arg: formula831}
	result833 := _t1515
	p.recordSpan(int(span_start832))
	return result833
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	p.pushPath(int(1))
	_t1516 := p.parse_name()
	name834 := _t1516
	p.popPath()
	p.pushPath(int(2))
	_t1517 := p.parse_ffi_args()
	ffi_args835 := _t1517
	p.popPath()
	p.pushPath(int(3))
	_t1518 := p.parse_terms()
	terms836 := _t1518
	p.popPath()
	p.consumeLiteral(")")
	_t1519 := &pb.FFI{Name: name834, Args: ffi_args835, Terms: terms836}
	result838 := _t1519
	p.recordSpan(int(span_start837))
	return result838
}

func (p *Parser) parse_name() string {
	span_start840 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol839 := p.consumeTerminal("SYMBOL").Value.str
	result841 := symbol839
	p.recordSpan(int(span_start840))
	return result841
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	span_start846 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs842 := []*pb.Abstraction{}
	cond843 := p.matchLookaheadLiteral("(", 0)
	for cond843 {
		_t1520 := p.parse_abstraction()
		item844 := _t1520
		xs842 = append(xs842, item844)
		cond843 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions845 := xs842
	p.consumeLiteral(")")
	result847 := abstractions845
	p.recordSpan(int(span_start846))
	return result847
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	p.pushPath(int(1))
	_t1521 := p.parse_relation_id()
	relation_id848 := _t1521
	p.popPath()
	p.pushPath(int(2))
	xs853 := []*pb.Term{}
	cond854 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx855 := 0
	for cond854 {
		p.pushPath(int(idx855))
		_t1522 := p.parse_term()
		item856 := _t1522
		p.popPath()
		xs853 = append(xs853, item856)
		idx855 = (idx855 + 1)
		cond854 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms852 := xs853
	p.popPath()
	p.consumeLiteral(")")
	_t1523 := &pb.Atom{Name: relation_id848, Terms: terms852}
	result858 := _t1523
	p.recordSpan(int(span_start857))
	return result858
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start868 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	p.pushPath(int(1))
	_t1524 := p.parse_name()
	name859 := _t1524
	p.popPath()
	p.pushPath(int(2))
	xs864 := []*pb.Term{}
	cond865 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx866 := 0
	for cond865 {
		p.pushPath(int(idx866))
		_t1525 := p.parse_term()
		item867 := _t1525
		p.popPath()
		xs864 = append(xs864, item867)
		idx866 = (idx866 + 1)
		cond865 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms863 := xs864
	p.popPath()
	p.consumeLiteral(")")
	_t1526 := &pb.Pragma{Name: name859, Terms: terms863}
	result869 := _t1526
	p.recordSpan(int(span_start868))
	return result869
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start889 := int64(p.spanStart())
	var _t1527 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1528 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1528 = 9
		} else {
			var _t1529 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1529 = 4
			} else {
				var _t1530 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1530 = 3
				} else {
					var _t1531 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1531 = 0
					} else {
						var _t1532 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1532 = 2
						} else {
							var _t1533 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1533 = 1
							} else {
								var _t1534 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1534 = 8
								} else {
									var _t1535 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1535 = 6
									} else {
										var _t1536 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1536 = 5
										} else {
											var _t1537 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1537 = 7
											} else {
												_t1537 = -1
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
	prediction870 := _t1527
	var _t1538 *pb.Primitive
	if prediction870 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		p.pushPath(int(1))
		_t1539 := p.parse_name()
		name880 := _t1539
		p.popPath()
		p.pushPath(int(2))
		xs885 := []*pb.RelTerm{}
		cond886 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		idx887 := 0
		for cond886 {
			p.pushPath(int(idx887))
			_t1540 := p.parse_rel_term()
			item888 := _t1540
			p.popPath()
			xs885 = append(xs885, item888)
			idx887 = (idx887 + 1)
			cond886 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms884 := xs885
		p.popPath()
		p.consumeLiteral(")")
		_t1541 := &pb.Primitive{Name: name880, Terms: rel_terms884}
		_t1538 = _t1541
	} else {
		var _t1542 *pb.Primitive
		if prediction870 == 8 {
			_t1543 := p.parse_divide()
			divide879 := _t1543
			_t1542 = divide879
		} else {
			var _t1544 *pb.Primitive
			if prediction870 == 7 {
				_t1545 := p.parse_multiply()
				multiply878 := _t1545
				_t1544 = multiply878
			} else {
				var _t1546 *pb.Primitive
				if prediction870 == 6 {
					_t1547 := p.parse_minus()
					minus877 := _t1547
					_t1546 = minus877
				} else {
					var _t1548 *pb.Primitive
					if prediction870 == 5 {
						_t1549 := p.parse_add()
						add876 := _t1549
						_t1548 = add876
					} else {
						var _t1550 *pb.Primitive
						if prediction870 == 4 {
							_t1551 := p.parse_gt_eq()
							gt_eq875 := _t1551
							_t1550 = gt_eq875
						} else {
							var _t1552 *pb.Primitive
							if prediction870 == 3 {
								_t1553 := p.parse_gt()
								gt874 := _t1553
								_t1552 = gt874
							} else {
								var _t1554 *pb.Primitive
								if prediction870 == 2 {
									_t1555 := p.parse_lt_eq()
									lt_eq873 := _t1555
									_t1554 = lt_eq873
								} else {
									var _t1556 *pb.Primitive
									if prediction870 == 1 {
										_t1557 := p.parse_lt()
										lt872 := _t1557
										_t1556 = lt872
									} else {
										var _t1558 *pb.Primitive
										if prediction870 == 0 {
											_t1559 := p.parse_eq()
											eq871 := _t1559
											_t1558 = eq871
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1556 = _t1558
									}
									_t1554 = _t1556
								}
								_t1552 = _t1554
							}
							_t1550 = _t1552
						}
						_t1548 = _t1550
					}
					_t1546 = _t1548
				}
				_t1544 = _t1546
			}
			_t1542 = _t1544
		}
		_t1538 = _t1542
	}
	result890 := _t1538
	p.recordSpan(int(span_start889))
	return result890
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start893 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1560 := p.parse_term()
	term891 := _t1560
	_t1561 := p.parse_term()
	term_3892 := _t1561
	p.consumeLiteral(")")
	_t1562 := &pb.RelTerm{}
	_t1562.RelTermType = &pb.RelTerm_Term{Term: term891}
	_t1563 := &pb.RelTerm{}
	_t1563.RelTermType = &pb.RelTerm_Term{Term: term_3892}
	_t1564 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1562, _t1563}}
	result894 := _t1564
	p.recordSpan(int(span_start893))
	return result894
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start897 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1565 := p.parse_term()
	term895 := _t1565
	_t1566 := p.parse_term()
	term_3896 := _t1566
	p.consumeLiteral(")")
	_t1567 := &pb.RelTerm{}
	_t1567.RelTermType = &pb.RelTerm_Term{Term: term895}
	_t1568 := &pb.RelTerm{}
	_t1568.RelTermType = &pb.RelTerm_Term{Term: term_3896}
	_t1569 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1567, _t1568}}
	result898 := _t1569
	p.recordSpan(int(span_start897))
	return result898
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start901 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1570 := p.parse_term()
	term899 := _t1570
	_t1571 := p.parse_term()
	term_3900 := _t1571
	p.consumeLiteral(")")
	_t1572 := &pb.RelTerm{}
	_t1572.RelTermType = &pb.RelTerm_Term{Term: term899}
	_t1573 := &pb.RelTerm{}
	_t1573.RelTermType = &pb.RelTerm_Term{Term: term_3900}
	_t1574 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1572, _t1573}}
	result902 := _t1574
	p.recordSpan(int(span_start901))
	return result902
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start905 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1575 := p.parse_term()
	term903 := _t1575
	_t1576 := p.parse_term()
	term_3904 := _t1576
	p.consumeLiteral(")")
	_t1577 := &pb.RelTerm{}
	_t1577.RelTermType = &pb.RelTerm_Term{Term: term903}
	_t1578 := &pb.RelTerm{}
	_t1578.RelTermType = &pb.RelTerm_Term{Term: term_3904}
	_t1579 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1577, _t1578}}
	result906 := _t1579
	p.recordSpan(int(span_start905))
	return result906
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1580 := p.parse_term()
	term907 := _t1580
	_t1581 := p.parse_term()
	term_3908 := _t1581
	p.consumeLiteral(")")
	_t1582 := &pb.RelTerm{}
	_t1582.RelTermType = &pb.RelTerm_Term{Term: term907}
	_t1583 := &pb.RelTerm{}
	_t1583.RelTermType = &pb.RelTerm_Term{Term: term_3908}
	_t1584 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1582, _t1583}}
	result910 := _t1584
	p.recordSpan(int(span_start909))
	return result910
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start914 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1585 := p.parse_term()
	term911 := _t1585
	_t1586 := p.parse_term()
	term_3912 := _t1586
	_t1587 := p.parse_term()
	term_4913 := _t1587
	p.consumeLiteral(")")
	_t1588 := &pb.RelTerm{}
	_t1588.RelTermType = &pb.RelTerm_Term{Term: term911}
	_t1589 := &pb.RelTerm{}
	_t1589.RelTermType = &pb.RelTerm_Term{Term: term_3912}
	_t1590 := &pb.RelTerm{}
	_t1590.RelTermType = &pb.RelTerm_Term{Term: term_4913}
	_t1591 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1588, _t1589, _t1590}}
	result915 := _t1591
	p.recordSpan(int(span_start914))
	return result915
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start919 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1592 := p.parse_term()
	term916 := _t1592
	_t1593 := p.parse_term()
	term_3917 := _t1593
	_t1594 := p.parse_term()
	term_4918 := _t1594
	p.consumeLiteral(")")
	_t1595 := &pb.RelTerm{}
	_t1595.RelTermType = &pb.RelTerm_Term{Term: term916}
	_t1596 := &pb.RelTerm{}
	_t1596.RelTermType = &pb.RelTerm_Term{Term: term_3917}
	_t1597 := &pb.RelTerm{}
	_t1597.RelTermType = &pb.RelTerm_Term{Term: term_4918}
	_t1598 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1595, _t1596, _t1597}}
	result920 := _t1598
	p.recordSpan(int(span_start919))
	return result920
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start924 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1599 := p.parse_term()
	term921 := _t1599
	_t1600 := p.parse_term()
	term_3922 := _t1600
	_t1601 := p.parse_term()
	term_4923 := _t1601
	p.consumeLiteral(")")
	_t1602 := &pb.RelTerm{}
	_t1602.RelTermType = &pb.RelTerm_Term{Term: term921}
	_t1603 := &pb.RelTerm{}
	_t1603.RelTermType = &pb.RelTerm_Term{Term: term_3922}
	_t1604 := &pb.RelTerm{}
	_t1604.RelTermType = &pb.RelTerm_Term{Term: term_4923}
	_t1605 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1602, _t1603, _t1604}}
	result925 := _t1605
	p.recordSpan(int(span_start924))
	return result925
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start929 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1606 := p.parse_term()
	term926 := _t1606
	_t1607 := p.parse_term()
	term_3927 := _t1607
	_t1608 := p.parse_term()
	term_4928 := _t1608
	p.consumeLiteral(")")
	_t1609 := &pb.RelTerm{}
	_t1609.RelTermType = &pb.RelTerm_Term{Term: term926}
	_t1610 := &pb.RelTerm{}
	_t1610.RelTermType = &pb.RelTerm_Term{Term: term_3927}
	_t1611 := &pb.RelTerm{}
	_t1611.RelTermType = &pb.RelTerm_Term{Term: term_4928}
	_t1612 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1609, _t1610, _t1611}}
	result930 := _t1612
	p.recordSpan(int(span_start929))
	return result930
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start934 := int64(p.spanStart())
	var _t1613 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1613 = 1
	} else {
		var _t1614 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1614 = 1
		} else {
			var _t1615 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1615 = 1
			} else {
				var _t1616 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1616 = 1
				} else {
					var _t1617 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1617 = 0
					} else {
						var _t1618 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1618 = 1
						} else {
							var _t1619 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1619 = 1
							} else {
								var _t1620 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1620 = 1
								} else {
									var _t1621 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1621 = 1
									} else {
										var _t1622 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1622 = 1
										} else {
											var _t1623 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1623 = 1
											} else {
												var _t1624 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1624 = 1
												} else {
													_t1624 = -1
												}
												_t1623 = _t1624
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
	prediction931 := _t1613
	var _t1625 *pb.RelTerm
	if prediction931 == 1 {
		_t1626 := p.parse_term()
		term933 := _t1626
		_t1627 := &pb.RelTerm{}
		_t1627.RelTermType = &pb.RelTerm_Term{Term: term933}
		_t1625 = _t1627
	} else {
		var _t1628 *pb.RelTerm
		if prediction931 == 0 {
			_t1629 := p.parse_specialized_value()
			specialized_value932 := _t1629
			_t1630 := &pb.RelTerm{}
			_t1630.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value932}
			_t1628 = _t1630
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1625 = _t1628
	}
	result935 := _t1625
	p.recordSpan(int(span_start934))
	return result935
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start937 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1631 := p.parse_value()
	value936 := _t1631
	result938 := value936
	p.recordSpan(int(span_start937))
	return result938
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start948 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	p.pushPath(int(3))
	_t1632 := p.parse_name()
	name939 := _t1632
	p.popPath()
	p.pushPath(int(2))
	xs944 := []*pb.RelTerm{}
	cond945 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx946 := 0
	for cond945 {
		p.pushPath(int(idx946))
		_t1633 := p.parse_rel_term()
		item947 := _t1633
		p.popPath()
		xs944 = append(xs944, item947)
		idx946 = (idx946 + 1)
		cond945 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms943 := xs944
	p.popPath()
	p.consumeLiteral(")")
	_t1634 := &pb.RelAtom{Name: name939, Terms: rel_terms943}
	result949 := _t1634
	p.recordSpan(int(span_start948))
	return result949
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start952 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	p.pushPath(int(2))
	_t1635 := p.parse_term()
	term950 := _t1635
	p.popPath()
	p.pushPath(int(3))
	_t1636 := p.parse_term()
	term_3951 := _t1636
	p.popPath()
	p.consumeLiteral(")")
	_t1637 := &pb.Cast{Input: term950, Result: term_3951}
	result953 := _t1637
	p.recordSpan(int(span_start952))
	return result953
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	span_start958 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs954 := []*pb.Attribute{}
	cond955 := p.matchLookaheadLiteral("(", 0)
	for cond955 {
		_t1638 := p.parse_attribute()
		item956 := _t1638
		xs954 = append(xs954, item956)
		cond955 = p.matchLookaheadLiteral("(", 0)
	}
	attributes957 := xs954
	p.consumeLiteral(")")
	result959 := attributes957
	p.recordSpan(int(span_start958))
	return result959
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	p.pushPath(int(1))
	_t1639 := p.parse_name()
	name960 := _t1639
	p.popPath()
	p.pushPath(int(2))
	xs965 := []*pb.Value{}
	cond966 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx967 := 0
	for cond966 {
		p.pushPath(int(idx967))
		_t1640 := p.parse_value()
		item968 := _t1640
		p.popPath()
		xs965 = append(xs965, item968)
		idx967 = (idx967 + 1)
		cond966 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values964 := xs965
	p.popPath()
	p.consumeLiteral(")")
	_t1641 := &pb.Attribute{Name: name960, Args: values964}
	result970 := _t1641
	p.recordSpan(int(span_start969))
	return result970
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start980 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	p.pushPath(int(1))
	xs975 := []*pb.RelationId{}
	cond976 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx977 := 0
	for cond976 {
		p.pushPath(int(idx977))
		_t1642 := p.parse_relation_id()
		item978 := _t1642
		p.popPath()
		xs975 = append(xs975, item978)
		idx977 = (idx977 + 1)
		cond976 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids974 := xs975
	p.popPath()
	p.pushPath(int(2))
	_t1643 := p.parse_script()
	script979 := _t1643
	p.popPath()
	p.consumeLiteral(")")
	_t1644 := &pb.Algorithm{Global: relation_ids974, Body: script979}
	result981 := _t1644
	p.recordSpan(int(span_start980))
	return result981
}

func (p *Parser) parse_script() *pb.Script {
	span_start990 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	p.pushPath(int(1))
	xs986 := []*pb.Construct{}
	cond987 := p.matchLookaheadLiteral("(", 0)
	idx988 := 0
	for cond987 {
		p.pushPath(int(idx988))
		_t1645 := p.parse_construct()
		item989 := _t1645
		p.popPath()
		xs986 = append(xs986, item989)
		idx988 = (idx988 + 1)
		cond987 = p.matchLookaheadLiteral("(", 0)
	}
	constructs985 := xs986
	p.popPath()
	p.consumeLiteral(")")
	_t1646 := &pb.Script{Constructs: constructs985}
	result991 := _t1646
	p.recordSpan(int(span_start990))
	return result991
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start995 := int64(p.spanStart())
	var _t1647 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1648 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1648 = 1
		} else {
			var _t1649 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1649 = 1
			} else {
				var _t1650 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1650 = 1
				} else {
					var _t1651 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1651 = 0
					} else {
						var _t1652 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1652 = 1
						} else {
							var _t1653 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1653 = 1
							} else {
								_t1653 = -1
							}
							_t1652 = _t1653
						}
						_t1651 = _t1652
					}
					_t1650 = _t1651
				}
				_t1649 = _t1650
			}
			_t1648 = _t1649
		}
		_t1647 = _t1648
	} else {
		_t1647 = -1
	}
	prediction992 := _t1647
	var _t1654 *pb.Construct
	if prediction992 == 1 {
		_t1655 := p.parse_instruction()
		instruction994 := _t1655
		_t1656 := &pb.Construct{}
		_t1656.ConstructType = &pb.Construct_Instruction{Instruction: instruction994}
		_t1654 = _t1656
	} else {
		var _t1657 *pb.Construct
		if prediction992 == 0 {
			_t1658 := p.parse_loop()
			loop993 := _t1658
			_t1659 := &pb.Construct{}
			_t1659.ConstructType = &pb.Construct_Loop{Loop: loop993}
			_t1657 = _t1659
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1654 = _t1657
	}
	result996 := _t1654
	p.recordSpan(int(span_start995))
	return result996
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start999 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	p.pushPath(int(1))
	_t1660 := p.parse_init()
	init997 := _t1660
	p.popPath()
	p.pushPath(int(2))
	_t1661 := p.parse_script()
	script998 := _t1661
	p.popPath()
	p.consumeLiteral(")")
	_t1662 := &pb.Loop{Init: init997, Body: script998}
	result1000 := _t1662
	p.recordSpan(int(span_start999))
	return result1000
}

func (p *Parser) parse_init() []*pb.Instruction {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1001 := []*pb.Instruction{}
	cond1002 := p.matchLookaheadLiteral("(", 0)
	for cond1002 {
		_t1663 := p.parse_instruction()
		item1003 := _t1663
		xs1001 = append(xs1001, item1003)
		cond1002 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1004 := xs1001
	p.consumeLiteral(")")
	result1006 := instructions1004
	p.recordSpan(int(span_start1005))
	return result1006
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start1013 := int64(p.spanStart())
	var _t1664 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1665 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1665 = 1
		} else {
			var _t1666 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1666 = 4
			} else {
				var _t1667 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1667 = 3
				} else {
					var _t1668 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1668 = 2
					} else {
						var _t1669 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1669 = 0
						} else {
							_t1669 = -1
						}
						_t1668 = _t1669
					}
					_t1667 = _t1668
				}
				_t1666 = _t1667
			}
			_t1665 = _t1666
		}
		_t1664 = _t1665
	} else {
		_t1664 = -1
	}
	prediction1007 := _t1664
	var _t1670 *pb.Instruction
	if prediction1007 == 4 {
		_t1671 := p.parse_monus_def()
		monus_def1012 := _t1671
		_t1672 := &pb.Instruction{}
		_t1672.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1012}
		_t1670 = _t1672
	} else {
		var _t1673 *pb.Instruction
		if prediction1007 == 3 {
			_t1674 := p.parse_monoid_def()
			monoid_def1011 := _t1674
			_t1675 := &pb.Instruction{}
			_t1675.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1011}
			_t1673 = _t1675
		} else {
			var _t1676 *pb.Instruction
			if prediction1007 == 2 {
				_t1677 := p.parse_break()
				break1010 := _t1677
				_t1678 := &pb.Instruction{}
				_t1678.InstrType = &pb.Instruction_Break{Break: break1010}
				_t1676 = _t1678
			} else {
				var _t1679 *pb.Instruction
				if prediction1007 == 1 {
					_t1680 := p.parse_upsert()
					upsert1009 := _t1680
					_t1681 := &pb.Instruction{}
					_t1681.InstrType = &pb.Instruction_Upsert{Upsert: upsert1009}
					_t1679 = _t1681
				} else {
					var _t1682 *pb.Instruction
					if prediction1007 == 0 {
						_t1683 := p.parse_assign()
						assign1008 := _t1683
						_t1684 := &pb.Instruction{}
						_t1684.InstrType = &pb.Instruction_Assign{Assign: assign1008}
						_t1682 = _t1684
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1679 = _t1682
				}
				_t1676 = _t1679
			}
			_t1673 = _t1676
		}
		_t1670 = _t1673
	}
	result1014 := _t1670
	p.recordSpan(int(span_start1013))
	return result1014
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start1018 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	p.pushPath(int(1))
	_t1685 := p.parse_relation_id()
	relation_id1015 := _t1685
	p.popPath()
	p.pushPath(int(2))
	_t1686 := p.parse_abstraction()
	abstraction1016 := _t1686
	p.popPath()
	p.pushPath(int(3))
	var _t1687 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1688 := p.parse_attrs()
		_t1687 = _t1688
	}
	attrs1017 := _t1687
	p.popPath()
	p.consumeLiteral(")")
	_t1689 := attrs1017
	if attrs1017 == nil {
		_t1689 = []*pb.Attribute{}
	}
	_t1690 := &pb.Assign{Name: relation_id1015, Body: abstraction1016, Attrs: _t1689}
	result1019 := _t1690
	p.recordSpan(int(span_start1018))
	return result1019
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start1023 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	p.pushPath(int(1))
	_t1691 := p.parse_relation_id()
	relation_id1020 := _t1691
	p.popPath()
	_t1692 := p.parse_abstraction_with_arity()
	abstraction_with_arity1021 := _t1692
	p.pushPath(int(3))
	var _t1693 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1694 := p.parse_attrs()
		_t1693 = _t1694
	}
	attrs1022 := _t1693
	p.popPath()
	p.consumeLiteral(")")
	_t1695 := attrs1022
	if attrs1022 == nil {
		_t1695 = []*pb.Attribute{}
	}
	_t1696 := &pb.Upsert{Name: relation_id1020, Body: abstraction_with_arity1021[0].(*pb.Abstraction), Attrs: _t1695, ValueArity: abstraction_with_arity1021[1].(int64)}
	result1024 := _t1696
	p.recordSpan(int(span_start1023))
	return result1024
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	span_start1027 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1697 := p.parse_bindings()
	bindings1025 := _t1697
	_t1698 := p.parse_formula()
	formula1026 := _t1698
	p.consumeLiteral(")")
	_t1699 := &pb.Abstraction{Vars: listConcat(bindings1025[0].([]*pb.Binding), bindings1025[1].([]*pb.Binding)), Value: formula1026}
	result1028 := []interface{}{_t1699, int64(len(bindings1025[1].([]*pb.Binding)))}
	p.recordSpan(int(span_start1027))
	return result1028
}

func (p *Parser) parse_break() *pb.Break {
	span_start1032 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	p.pushPath(int(1))
	_t1700 := p.parse_relation_id()
	relation_id1029 := _t1700
	p.popPath()
	p.pushPath(int(2))
	_t1701 := p.parse_abstraction()
	abstraction1030 := _t1701
	p.popPath()
	p.pushPath(int(3))
	var _t1702 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1703 := p.parse_attrs()
		_t1702 = _t1703
	}
	attrs1031 := _t1702
	p.popPath()
	p.consumeLiteral(")")
	_t1704 := attrs1031
	if attrs1031 == nil {
		_t1704 = []*pb.Attribute{}
	}
	_t1705 := &pb.Break{Name: relation_id1029, Body: abstraction1030, Attrs: _t1704}
	result1033 := _t1705
	p.recordSpan(int(span_start1032))
	return result1033
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	p.pushPath(int(1))
	_t1706 := p.parse_monoid()
	monoid1034 := _t1706
	p.popPath()
	p.pushPath(int(2))
	_t1707 := p.parse_relation_id()
	relation_id1035 := _t1707
	p.popPath()
	_t1708 := p.parse_abstraction_with_arity()
	abstraction_with_arity1036 := _t1708
	p.pushPath(int(4))
	var _t1709 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1710 := p.parse_attrs()
		_t1709 = _t1710
	}
	attrs1037 := _t1709
	p.popPath()
	p.consumeLiteral(")")
	_t1711 := attrs1037
	if attrs1037 == nil {
		_t1711 = []*pb.Attribute{}
	}
	_t1712 := &pb.MonoidDef{Monoid: monoid1034, Name: relation_id1035, Body: abstraction_with_arity1036[0].(*pb.Abstraction), Attrs: _t1711, ValueArity: abstraction_with_arity1036[1].(int64)}
	result1039 := _t1712
	p.recordSpan(int(span_start1038))
	return result1039
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start1045 := int64(p.spanStart())
	var _t1713 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1714 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1714 = 3
		} else {
			var _t1715 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1715 = 0
			} else {
				var _t1716 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1716 = 1
				} else {
					var _t1717 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1717 = 2
					} else {
						_t1717 = -1
					}
					_t1716 = _t1717
				}
				_t1715 = _t1716
			}
			_t1714 = _t1715
		}
		_t1713 = _t1714
	} else {
		_t1713 = -1
	}
	prediction1040 := _t1713
	var _t1718 *pb.Monoid
	if prediction1040 == 3 {
		_t1719 := p.parse_sum_monoid()
		sum_monoid1044 := _t1719
		_t1720 := &pb.Monoid{}
		_t1720.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1044}
		_t1718 = _t1720
	} else {
		var _t1721 *pb.Monoid
		if prediction1040 == 2 {
			_t1722 := p.parse_max_monoid()
			max_monoid1043 := _t1722
			_t1723 := &pb.Monoid{}
			_t1723.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1043}
			_t1721 = _t1723
		} else {
			var _t1724 *pb.Monoid
			if prediction1040 == 1 {
				_t1725 := p.parse_min_monoid()
				min_monoid1042 := _t1725
				_t1726 := &pb.Monoid{}
				_t1726.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1042}
				_t1724 = _t1726
			} else {
				var _t1727 *pb.Monoid
				if prediction1040 == 0 {
					_t1728 := p.parse_or_monoid()
					or_monoid1041 := _t1728
					_t1729 := &pb.Monoid{}
					_t1729.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1041}
					_t1727 = _t1729
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1724 = _t1727
			}
			_t1721 = _t1724
		}
		_t1718 = _t1721
	}
	result1046 := _t1718
	p.recordSpan(int(span_start1045))
	return result1046
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start1047 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1730 := &pb.OrMonoid{}
	result1048 := _t1730
	p.recordSpan(int(span_start1047))
	return result1048
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start1050 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	p.pushPath(int(1))
	_t1731 := p.parse_type()
	type1049 := _t1731
	p.popPath()
	p.consumeLiteral(")")
	_t1732 := &pb.MinMonoid{Type: type1049}
	result1051 := _t1732
	p.recordSpan(int(span_start1050))
	return result1051
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	p.pushPath(int(1))
	_t1733 := p.parse_type()
	type1052 := _t1733
	p.popPath()
	p.consumeLiteral(")")
	_t1734 := &pb.MaxMonoid{Type: type1052}
	result1054 := _t1734
	p.recordSpan(int(span_start1053))
	return result1054
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start1056 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	p.pushPath(int(1))
	_t1735 := p.parse_type()
	type1055 := _t1735
	p.popPath()
	p.consumeLiteral(")")
	_t1736 := &pb.SumMonoid{Type: type1055}
	result1057 := _t1736
	p.recordSpan(int(span_start1056))
	return result1057
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start1062 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	p.pushPath(int(1))
	_t1737 := p.parse_monoid()
	monoid1058 := _t1737
	p.popPath()
	p.pushPath(int(2))
	_t1738 := p.parse_relation_id()
	relation_id1059 := _t1738
	p.popPath()
	_t1739 := p.parse_abstraction_with_arity()
	abstraction_with_arity1060 := _t1739
	p.pushPath(int(4))
	var _t1740 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1741 := p.parse_attrs()
		_t1740 = _t1741
	}
	attrs1061 := _t1740
	p.popPath()
	p.consumeLiteral(")")
	_t1742 := attrs1061
	if attrs1061 == nil {
		_t1742 = []*pb.Attribute{}
	}
	_t1743 := &pb.MonusDef{Monoid: monoid1058, Name: relation_id1059, Body: abstraction_with_arity1060[0].(*pb.Abstraction), Attrs: _t1742, ValueArity: abstraction_with_arity1060[1].(int64)}
	result1063 := _t1743
	p.recordSpan(int(span_start1062))
	return result1063
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	p.pushPath(int(2))
	_t1744 := p.parse_relation_id()
	relation_id1064 := _t1744
	p.popPath()
	_t1745 := p.parse_abstraction()
	abstraction1065 := _t1745
	_t1746 := p.parse_functional_dependency_keys()
	functional_dependency_keys1066 := _t1746
	_t1747 := p.parse_functional_dependency_values()
	functional_dependency_values1067 := _t1747
	p.consumeLiteral(")")
	_t1748 := &pb.FunctionalDependency{Guard: abstraction1065, Keys: functional_dependency_keys1066, Values: functional_dependency_values1067}
	_t1749 := &pb.Constraint{Name: relation_id1064}
	_t1749.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1748}
	result1069 := _t1749
	p.recordSpan(int(span_start1068))
	return result1069
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	span_start1074 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1070 := []*pb.Var{}
	cond1071 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1071 {
		_t1750 := p.parse_var()
		item1072 := _t1750
		xs1070 = append(xs1070, item1072)
		cond1071 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1073 := xs1070
	p.consumeLiteral(")")
	result1075 := vars1073
	p.recordSpan(int(span_start1074))
	return result1075
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	span_start1080 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1076 := []*pb.Var{}
	cond1077 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1077 {
		_t1751 := p.parse_var()
		item1078 := _t1751
		xs1076 = append(xs1076, item1078)
		cond1077 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1079 := xs1076
	p.consumeLiteral(")")
	result1081 := vars1079
	p.recordSpan(int(span_start1080))
	return result1081
}

func (p *Parser) parse_data() *pb.Data {
	span_start1086 := int64(p.spanStart())
	var _t1752 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1753 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1753 = 0
		} else {
			var _t1754 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1754 = 2
			} else {
				var _t1755 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1755 = 1
				} else {
					_t1755 = -1
				}
				_t1754 = _t1755
			}
			_t1753 = _t1754
		}
		_t1752 = _t1753
	} else {
		_t1752 = -1
	}
	prediction1082 := _t1752
	var _t1756 *pb.Data
	if prediction1082 == 2 {
		_t1757 := p.parse_csv_data()
		csv_data1085 := _t1757
		_t1758 := &pb.Data{}
		_t1758.DataType = &pb.Data_CsvData{CsvData: csv_data1085}
		_t1756 = _t1758
	} else {
		var _t1759 *pb.Data
		if prediction1082 == 1 {
			_t1760 := p.parse_betree_relation()
			betree_relation1084 := _t1760
			_t1761 := &pb.Data{}
			_t1761.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1084}
			_t1759 = _t1761
		} else {
			var _t1762 *pb.Data
			if prediction1082 == 0 {
				_t1763 := p.parse_rel_edb()
				rel_edb1083 := _t1763
				_t1764 := &pb.Data{}
				_t1764.DataType = &pb.Data_RelEdb{RelEdb: rel_edb1083}
				_t1762 = _t1764
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1759 = _t1762
		}
		_t1756 = _t1759
	}
	result1087 := _t1756
	p.recordSpan(int(span_start1086))
	return result1087
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	span_start1091 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	p.pushPath(int(1))
	_t1765 := p.parse_relation_id()
	relation_id1088 := _t1765
	p.popPath()
	p.pushPath(int(2))
	_t1766 := p.parse_rel_edb_path()
	rel_edb_path1089 := _t1766
	p.popPath()
	p.pushPath(int(3))
	_t1767 := p.parse_rel_edb_types()
	rel_edb_types1090 := _t1767
	p.popPath()
	p.consumeLiteral(")")
	_t1768 := &pb.RelEDB{TargetId: relation_id1088, Path: rel_edb_path1089, Types: rel_edb_types1090}
	result1092 := _t1768
	p.recordSpan(int(span_start1091))
	return result1092
}

func (p *Parser) parse_rel_edb_path() []string {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1093 := []string{}
	cond1094 := p.matchLookaheadTerminal("STRING", 0)
	for cond1094 {
		item1095 := p.consumeTerminal("STRING").Value.str
		xs1093 = append(xs1093, item1095)
		cond1094 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1096 := xs1093
	p.consumeLiteral("]")
	result1098 := strings1096
	p.recordSpan(int(span_start1097))
	return result1098
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	span_start1103 := int64(p.spanStart())
	p.consumeLiteral("[")
	xs1099 := []*pb.Type{}
	cond1100 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1100 {
		_t1769 := p.parse_type()
		item1101 := _t1769
		xs1099 = append(xs1099, item1101)
		cond1100 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1102 := xs1099
	p.consumeLiteral("]")
	result1104 := types1102
	p.recordSpan(int(span_start1103))
	return result1104
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1107 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	p.pushPath(int(1))
	_t1770 := p.parse_relation_id()
	relation_id1105 := _t1770
	p.popPath()
	p.pushPath(int(2))
	_t1771 := p.parse_betree_info()
	betree_info1106 := _t1771
	p.popPath()
	p.consumeLiteral(")")
	_t1772 := &pb.BeTreeRelation{Name: relation_id1105, RelationInfo: betree_info1106}
	result1108 := _t1772
	p.recordSpan(int(span_start1107))
	return result1108
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1112 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1773 := p.parse_betree_info_key_types()
	betree_info_key_types1109 := _t1773
	_t1774 := p.parse_betree_info_value_types()
	betree_info_value_types1110 := _t1774
	_t1775 := p.parse_config_dict()
	config_dict1111 := _t1775
	p.consumeLiteral(")")
	_t1776 := p.construct_betree_info(betree_info_key_types1109, betree_info_value_types1110, config_dict1111)
	result1113 := _t1776
	p.recordSpan(int(span_start1112))
	return result1113
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	span_start1118 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1114 := []*pb.Type{}
	cond1115 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1115 {
		_t1777 := p.parse_type()
		item1116 := _t1777
		xs1114 = append(xs1114, item1116)
		cond1115 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1117 := xs1114
	p.consumeLiteral(")")
	result1119 := types1117
	p.recordSpan(int(span_start1118))
	return result1119
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	span_start1124 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1120 := []*pb.Type{}
	cond1121 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1121 {
		_t1778 := p.parse_type()
		item1122 := _t1778
		xs1120 = append(xs1120, item1122)
		cond1121 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1123 := xs1120
	p.consumeLiteral(")")
	result1125 := types1123
	p.recordSpan(int(span_start1124))
	return result1125
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1130 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	p.pushPath(int(1))
	_t1779 := p.parse_csvlocator()
	csvlocator1126 := _t1779
	p.popPath()
	p.pushPath(int(2))
	_t1780 := p.parse_csv_config()
	csv_config1127 := _t1780
	p.popPath()
	p.pushPath(int(3))
	_t1781 := p.parse_csv_columns()
	csv_columns1128 := _t1781
	p.popPath()
	p.pushPath(int(4))
	_t1782 := p.parse_csv_asof()
	csv_asof1129 := _t1782
	p.popPath()
	p.consumeLiteral(")")
	_t1783 := &pb.CSVData{Locator: csvlocator1126, Config: csv_config1127, Columns: csv_columns1128, Asof: csv_asof1129}
	result1131 := _t1783
	p.recordSpan(int(span_start1130))
	return result1131
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1134 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	p.pushPath(int(1))
	var _t1784 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1785 := p.parse_csv_locator_paths()
		_t1784 = _t1785
	}
	csv_locator_paths1132 := _t1784
	p.popPath()
	p.pushPath(int(2))
	var _t1786 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1787 := p.parse_csv_locator_inline_data()
		_t1786 = ptr(_t1787)
	}
	csv_locator_inline_data1133 := _t1786
	p.popPath()
	p.consumeLiteral(")")
	_t1788 := csv_locator_paths1132
	if csv_locator_paths1132 == nil {
		_t1788 = []string{}
	}
	_t1789 := &pb.CSVLocator{Paths: _t1788, InlineData: []byte(deref(csv_locator_inline_data1133, ""))}
	result1135 := _t1789
	p.recordSpan(int(span_start1134))
	return result1135
}

func (p *Parser) parse_csv_locator_paths() []string {
	span_start1140 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1136 := []string{}
	cond1137 := p.matchLookaheadTerminal("STRING", 0)
	for cond1137 {
		item1138 := p.consumeTerminal("STRING").Value.str
		xs1136 = append(xs1136, item1138)
		cond1137 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1139 := xs1136
	p.consumeLiteral(")")
	result1141 := strings1139
	p.recordSpan(int(span_start1140))
	return result1141
}

func (p *Parser) parse_csv_locator_inline_data() string {
	span_start1143 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1142 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1144 := string1142
	p.recordSpan(int(span_start1143))
	return result1144
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1146 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1790 := p.parse_config_dict()
	config_dict1145 := _t1790
	p.consumeLiteral(")")
	_t1791 := p.construct_csv_config(config_dict1145)
	result1147 := _t1791
	p.recordSpan(int(span_start1146))
	return result1147
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	span_start1152 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1148 := []*pb.CSVColumn{}
	cond1149 := p.matchLookaheadLiteral("(", 0)
	for cond1149 {
		_t1792 := p.parse_csv_column()
		item1150 := _t1792
		xs1148 = append(xs1148, item1150)
		cond1149 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns1151 := xs1148
	p.consumeLiteral(")")
	result1153 := csv_columns1151
	p.recordSpan(int(span_start1152))
	return result1153
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	span_start1164 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(int(1))
	string1154 := p.consumeTerminal("STRING").Value.str
	p.popPath()
	p.pushPath(int(2))
	_t1793 := p.parse_relation_id()
	relation_id1155 := _t1793
	p.popPath()
	p.consumeLiteral("[")
	p.pushPath(int(3))
	xs1160 := []*pb.Type{}
	cond1161 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx1162 := 0
	for cond1161 {
		p.pushPath(int(idx1162))
		_t1794 := p.parse_type()
		item1163 := _t1794
		p.popPath()
		xs1160 = append(xs1160, item1163)
		idx1162 = (idx1162 + 1)
		cond1161 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1159 := xs1160
	p.popPath()
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1795 := &pb.CSVColumn{ColumnName: string1154, TargetId: relation_id1155, Types: types1159}
	result1165 := _t1795
	p.recordSpan(int(span_start1164))
	return result1165
}

func (p *Parser) parse_csv_asof() string {
	span_start1167 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1166 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1168 := string1166
	p.recordSpan(int(span_start1167))
	return result1168
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1170 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	p.pushPath(int(1))
	_t1796 := p.parse_fragment_id()
	fragment_id1169 := _t1796
	p.popPath()
	p.consumeLiteral(")")
	_t1797 := &pb.Undefine{FragmentId: fragment_id1169}
	result1171 := _t1797
	p.recordSpan(int(span_start1170))
	return result1171
}

func (p *Parser) parse_context() *pb.Context {
	span_start1180 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	p.pushPath(int(1))
	xs1176 := []*pb.RelationId{}
	cond1177 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx1178 := 0
	for cond1177 {
		p.pushPath(int(idx1178))
		_t1798 := p.parse_relation_id()
		item1179 := _t1798
		p.popPath()
		xs1176 = append(xs1176, item1179)
		idx1178 = (idx1178 + 1)
		cond1177 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1175 := xs1176
	p.popPath()
	p.consumeLiteral(")")
	_t1799 := &pb.Context{Relations: relation_ids1175}
	result1181 := _t1799
	p.recordSpan(int(span_start1180))
	return result1181
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1184 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	p.pushPath(int(1))
	_t1800 := p.parse_rel_edb_path()
	rel_edb_path1182 := _t1800
	p.popPath()
	p.pushPath(int(2))
	_t1801 := p.parse_relation_id()
	relation_id1183 := _t1801
	p.popPath()
	p.consumeLiteral(")")
	_t1802 := &pb.Snapshot{DestinationPath: rel_edb_path1182, SourceRelation: relation_id1183}
	result1185 := _t1802
	p.recordSpan(int(span_start1184))
	return result1185
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	span_start1190 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1186 := []*pb.Read{}
	cond1187 := p.matchLookaheadLiteral("(", 0)
	for cond1187 {
		_t1803 := p.parse_read()
		item1188 := _t1803
		xs1186 = append(xs1186, item1188)
		cond1187 = p.matchLookaheadLiteral("(", 0)
	}
	reads1189 := xs1186
	p.consumeLiteral(")")
	result1191 := reads1189
	p.recordSpan(int(span_start1190))
	return result1191
}

func (p *Parser) parse_read() *pb.Read {
	span_start1198 := int64(p.spanStart())
	var _t1804 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1805 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1805 = 2
		} else {
			var _t1806 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1806 = 1
			} else {
				var _t1807 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1807 = 4
				} else {
					var _t1808 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1808 = 0
					} else {
						var _t1809 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1809 = 3
						} else {
							_t1809 = -1
						}
						_t1808 = _t1809
					}
					_t1807 = _t1808
				}
				_t1806 = _t1807
			}
			_t1805 = _t1806
		}
		_t1804 = _t1805
	} else {
		_t1804 = -1
	}
	prediction1192 := _t1804
	var _t1810 *pb.Read
	if prediction1192 == 4 {
		_t1811 := p.parse_export()
		export1197 := _t1811
		_t1812 := &pb.Read{}
		_t1812.ReadType = &pb.Read_Export{Export: export1197}
		_t1810 = _t1812
	} else {
		var _t1813 *pb.Read
		if prediction1192 == 3 {
			_t1814 := p.parse_abort()
			abort1196 := _t1814
			_t1815 := &pb.Read{}
			_t1815.ReadType = &pb.Read_Abort{Abort: abort1196}
			_t1813 = _t1815
		} else {
			var _t1816 *pb.Read
			if prediction1192 == 2 {
				_t1817 := p.parse_what_if()
				what_if1195 := _t1817
				_t1818 := &pb.Read{}
				_t1818.ReadType = &pb.Read_WhatIf{WhatIf: what_if1195}
				_t1816 = _t1818
			} else {
				var _t1819 *pb.Read
				if prediction1192 == 1 {
					_t1820 := p.parse_output()
					output1194 := _t1820
					_t1821 := &pb.Read{}
					_t1821.ReadType = &pb.Read_Output{Output: output1194}
					_t1819 = _t1821
				} else {
					var _t1822 *pb.Read
					if prediction1192 == 0 {
						_t1823 := p.parse_demand()
						demand1193 := _t1823
						_t1824 := &pb.Read{}
						_t1824.ReadType = &pb.Read_Demand{Demand: demand1193}
						_t1822 = _t1824
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1819 = _t1822
				}
				_t1816 = _t1819
			}
			_t1813 = _t1816
		}
		_t1810 = _t1813
	}
	result1199 := _t1810
	p.recordSpan(int(span_start1198))
	return result1199
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1201 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	p.pushPath(int(1))
	_t1825 := p.parse_relation_id()
	relation_id1200 := _t1825
	p.popPath()
	p.consumeLiteral(")")
	_t1826 := &pb.Demand{RelationId: relation_id1200}
	result1202 := _t1826
	p.recordSpan(int(span_start1201))
	return result1202
}

func (p *Parser) parse_output() *pb.Output {
	span_start1205 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	p.pushPath(int(1))
	_t1827 := p.parse_name()
	name1203 := _t1827
	p.popPath()
	p.pushPath(int(2))
	_t1828 := p.parse_relation_id()
	relation_id1204 := _t1828
	p.popPath()
	p.consumeLiteral(")")
	_t1829 := &pb.Output{Name: name1203, RelationId: relation_id1204}
	result1206 := _t1829
	p.recordSpan(int(span_start1205))
	return result1206
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1209 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	p.pushPath(int(1))
	_t1830 := p.parse_name()
	name1207 := _t1830
	p.popPath()
	p.pushPath(int(2))
	_t1831 := p.parse_epoch()
	epoch1208 := _t1831
	p.popPath()
	p.consumeLiteral(")")
	_t1832 := &pb.WhatIf{Branch: name1207, Epoch: epoch1208}
	result1210 := _t1832
	p.recordSpan(int(span_start1209))
	return result1210
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1213 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	p.pushPath(int(1))
	var _t1833 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1834 := p.parse_name()
		_t1833 = ptr(_t1834)
	}
	name1211 := _t1833
	p.popPath()
	p.pushPath(int(2))
	_t1835 := p.parse_relation_id()
	relation_id1212 := _t1835
	p.popPath()
	p.consumeLiteral(")")
	_t1836 := &pb.Abort{Name: deref(name1211, "abort"), RelationId: relation_id1212}
	result1214 := _t1836
	p.recordSpan(int(span_start1213))
	return result1214
}

func (p *Parser) parse_export() *pb.Export {
	span_start1216 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	p.pushPath(int(1))
	_t1837 := p.parse_export_csv_config()
	export_csv_config1215 := _t1837
	p.popPath()
	p.consumeLiteral(")")
	_t1838 := &pb.Export{}
	_t1838.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1215}
	result1217 := _t1838
	p.recordSpan(int(span_start1216))
	return result1217
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1221 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1839 := p.parse_export_csv_path()
	export_csv_path1218 := _t1839
	_t1840 := p.parse_export_csv_columns()
	export_csv_columns1219 := _t1840
	_t1841 := p.parse_config_dict()
	config_dict1220 := _t1841
	p.consumeLiteral(")")
	_t1842 := p.export_csv_config(export_csv_path1218, export_csv_columns1219, config_dict1220)
	result1222 := _t1842
	p.recordSpan(int(span_start1221))
	return result1222
}

func (p *Parser) parse_export_csv_path() string {
	span_start1224 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1223 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	result1225 := string1223
	p.recordSpan(int(span_start1224))
	return result1225
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	span_start1230 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1226 := []*pb.ExportCSVColumn{}
	cond1227 := p.matchLookaheadLiteral("(", 0)
	for cond1227 {
		_t1843 := p.parse_export_csv_column()
		item1228 := _t1843
		xs1226 = append(xs1226, item1228)
		cond1227 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1229 := xs1226
	p.consumeLiteral(")")
	result1231 := export_csv_columns1229
	p.recordSpan(int(span_start1230))
	return result1231
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1234 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(int(1))
	string1232 := p.consumeTerminal("STRING").Value.str
	p.popPath()
	p.pushPath(int(2))
	_t1844 := p.parse_relation_id()
	relation_id1233 := _t1844
	p.popPath()
	p.consumeLiteral(")")
	_t1845 := &pb.ExportCSVColumn{ColumnName: string1232, ColumnData: relation_id1233}
	result1235 := _t1845
	p.recordSpan(int(span_start1234))
	return result1235
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
