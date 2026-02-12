// Auto-generated LL(k) recursive-descent parser.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the parser, edit the generator code
// in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
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
	"sort"
	"strconv"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

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

func stringTokenValue(s string) TokenValue              { return TokenValue{kind: kindString, str: s} }
func intTokenValue(n int64) TokenValue                  { return TokenValue{kind: kindInt64, i64: n} }
func floatTokenValue(f float64) TokenValue              { return TokenValue{kind: kindFloat64, f64: f} }
func uint128TokenValue(v *pb.UInt128Value) TokenValue   { return TokenValue{kind: kindUint128, uint128: v} }
func int128TokenValue(v *pb.Int128Value) TokenValue     { return TokenValue{kind: kindInt128, int128: v} }
func decimalTokenValue(v *pb.DecimalValue) TokenValue   { return TokenValue{kind: kindDecimal, decimal: v} }

func (tv TokenValue) AsString() string              { return tv.str }
func (tv TokenValue) AsInt64() int64                { return tv.i64 }
func (tv TokenValue) AsFloat64() float64            { return tv.f64 }
func (tv TokenValue) AsUint128() *pb.UInt128Value   { return tv.uint128 }
func (tv TokenValue) AsInt128() *pb.Int128Value     { return tv.int128 }
func (tv TokenValue) AsDecimal() *pb.DecimalValue   { return tv.decimal }

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

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, %v, %d)", t.Type, t.Value, t.StartPos)
}

// Location represents a source position with 1-based line and column.
type Location struct {
	Line   int
	Column int
	Offset int
}

// Span represents a source range.
type Span struct {
	Start Location
	End   Location
}

// tokenSpec represents a token specification for the lexer
type tokenSpec struct {
	name   string
	regex  *regexp.Regexp
	action func(string) TokenValue
}

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
	tokenSpecs := []tokenSpec{
		{"LITERAL", regexp.MustCompile(`^::`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^<=`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^>=`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\#`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\(`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\)`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\*`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\+`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\-`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^/`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^:`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^<`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^=`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^>`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\[`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\]`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\{`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\|`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"LITERAL", regexp.MustCompile(`^\}`), func(s string) TokenValue { return stringTokenValue(s) }},
		{"DECIMAL", regexp.MustCompile(`^[-]?\d+\.\d+d\d+`), func(s string) TokenValue { return decimalTokenValue(scanDecimal(s)) }},
		{"FLOAT", regexp.MustCompile(`^[-]?\d+\.\d+|inf|nan`), func(s string) TokenValue { return floatTokenValue(scanFloat(s)) }},
		{"INT", regexp.MustCompile(`^[-]?\d+`), func(s string) TokenValue { return intTokenValue(scanInt(s)) }},
		{"INT128", regexp.MustCompile(`^[-]?\d+i128`), func(s string) TokenValue { return int128TokenValue(scanInt128(s)) }},
		{"STRING", regexp.MustCompile(`^"(?:[^"\\]|\\.)*"`), func(s string) TokenValue { return stringTokenValue(scanString(s)) }},
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_.-]*`), func(s string) TokenValue { return stringTokenValue(scanSymbol(s)) }},
		{"UINT128", regexp.MustCompile(`^0x[0-9a-fA-F]+`), func(s string) TokenValue { return uint128TokenValue(scanUint128(s)) }},
	}

	whitespaceRe := regexp.MustCompile(`^\s+`)
	commentRe := regexp.MustCompile(`^;;.*`)

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

	l.tokens = append(l.tokens, Token{Type: "$", Value: stringTokenValue(""), StartPos: l.pos, EndPos: l.pos})
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
		path:              make([]int, 0),
		lineStarts:        computeLineStarts(input),
	}
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

func pathKey(path []int) string {
	if len(path) == 0 {
		return ""
	}
	parts := make([]string, len(path))
	for i, v := range path {
		parts[i] = strconv.Itoa(v)
	}
	return strings.Join(parts, ",")
}

func (p *Parser) lookahead(k int) Token {
	idx := p.pos + k
	if idx < len(p.tokens) {
		return p.tokens[idx]
	}
	return Token{Type: "$", Value: stringTokenValue(""), StartPos: -1, EndPos: -1}
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
	if token.Type == "LITERAL" && token.Value.AsString() == literal {
		return true
	}
	if token.Type == "SYMBOL" && token.Value.AsString() == literal {
		return true
	}
	return false
}

func (p *Parser) matchLookaheadTerminal(terminal string, k int) bool {
	token := p.lookahead(k)
	return token.Type == terminal
}

func (p *Parser) pushPath(n int) {
	p.path = append(p.path, n)
}

func (p *Parser) popPath() {
	p.path = p.path[:len(p.path)-1]
}

func (p *Parser) spanStart() int {
	return p.tokens[p.pos].StartPos
}

func (p *Parser) recordSpan(startOffset int) {
	endOffset := p.tokens[p.pos-1].EndPos
	key := pathKey(p.path)
	p.Provenance[key] = Span{
		Start: p.makeLocation(startOffset),
		End:   p.makeLocation(endOffset),
	}
}

func (p *Parser) makeLocation(offset int) Location {
	// Binary search for the line containing offset
	lo, hi := 0, len(p.lineStarts)-1
	for lo < hi {
		mid := (lo + hi + 1) / 2
		if p.lineStarts[mid] <= offset {
			lo = mid
		} else {
			hi = mid - 1
		}
	}
	line := lo + 1
	column := offset - p.lineStarts[lo] + 1
	return Location{Line: line, Column: column, Offset: offset}
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

func (p *Parser) relationIdToInt(msg *pb.RelationId) *int64 {
	value := int64(msg.GetIdHigh()<<64 | msg.GetIdLow())
	if value >= 0 {
		return &value
	}
	return nil
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

func dictGet(m map[string]interface{}, key string) interface{} {
	if v, ok := m[key]; ok {
		return v
	}
	return nil
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

func stringInList(s string, list []string) bool {
	for _, item := range list {
		if item == s {
			return true
		}
	}
	return false
}


// Type conversion helpers for interface{} to concrete types
func toInt32(v interface{}) int32 {
	if v == nil { return 0 }
	switch x := v.(type) {
	case int32: return x
	case int64: return int32(x)
	case int: return int32(x)
	default: return 0
	}
}

func toInt64(v interface{}) int64 {
	if v == nil { return 0 }
	switch x := v.(type) {
	case int64: return x
	case int32: return int64(x)
	case int: return int64(x)
	default: return 0
	}
}

func toFloat64(v interface{}) float64 {
	if v == nil { return 0.0 }
	if f, ok := v.(float64); ok { return f }
	return 0.0
}

func toString(v interface{}) string {
	if v == nil { return "" }
	if s, ok := v.(string); ok { return s }
	return ""
}

func toBool(v interface{}) bool {
	if v == nil { return false }
	if b, ok := v.(bool); ok { return b }
	return false
}

// Pointer conversion helpers for optional proto3 fields
func ptrInt32(v int32) *int32 { return &v }
func ptrInt64(v int64) *int64 { return &v }
func ptrFloat64(v float64) *float64 { return &v }
func ptrString(v string) *string { return &v }
func ptrBool(v bool) *bool { return &v }
func ptrBytes(v []byte) *[]byte { return &v }

func mapSlice[T any, U any](slice []T, f func(T) U) []U {
	result := make([]U, len(slice))
	for i, v := range slice {
		result[i] = f(v)
	}
	return result
}

func listSort(s [][]interface{}) [][]interface{} {
	sort.Slice(s, func(i, j int) bool {
		ki, _ := s[i][0].(string)
		kj, _ := s[j][0].(string)
		return ki < kj
	})
	return s
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

// listConcatAny concatenates two slices passed as interface{}.
// Used when type information is lost through tuple indexing.
func listConcatAny(a interface{}, b interface{}) interface{} {
	if a == nil {
		return b
	}
	if b == nil {
		return a
	}
	aVal := reflect.ValueOf(a)
	bVal := reflect.ValueOf(b)
	result := reflect.MakeSlice(aVal.Type(), aVal.Len()+bVal.Len(), aVal.Len()+bVal.Len())
	reflect.Copy(result, aVal)
	reflect.Copy(result.Slice(aVal.Len(), result.Len()), bVal)
	return result.Interface()
}

// hasProtoField checks if a proto message has a non-nil field by name
// This uses reflection to check for oneOf fields
func hasProtoField(msg interface{}, fieldName string) bool {
	if msg == nil {
		return false
	}

	val := reflect.ValueOf(msg)
	if val.Kind() == reflect.Ptr {
		val = val.Elem()
	}
	if val.Kind() != reflect.Struct {
		return false
	}

	// Try to find a getter method: Get + PascalCase(fieldName)
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
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	return default_
}

func (p *Parser) _extract_value_float64(value *pb.Value, default_ float64) float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return value.GetFloatValue()
	}
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	return default_
}

func (p *Parser) _extract_value_bytes(value *pb.Value, default_ []byte) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return default_
}

func (p *Parser) _extract_value_uint128(value *pb.Value, default_ *pb.UInt128Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_string(value *pb.Value) *string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return ptr(value.GetStringValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return nil
}

func (p *Parser) _try_extract_value_string_list(value *pb.Value) []string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1222 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1222
	_t1223 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1223
	_t1224 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1224
	_t1225 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1225
	_t1226 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1226
	_t1227 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1227
	_t1228 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1228
	_t1229 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1229
	_t1230 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1230
	_t1231 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1231
	_t1232 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1232
	_t1233 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1233
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1234 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1234
	_t1235 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1235
	_t1236 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1236
	_t1237 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1237
	_t1238 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1238
	_t1239 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1239
	_t1240 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1240
	_t1241 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1241
	_t1242 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1242
	_t1243 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1243.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1243.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1243
	_t1244 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1244
}

func (p *Parser) default_configure() *pb.Configure {
	_t1245 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1245
	_t1246 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1246
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
	_t1247 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1247
	_t1248 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1248
	_t1249 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1249
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1250 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1250
	_t1251 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1251
	_t1252 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1252
	_t1253 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1253
	_t1254 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1254
	_t1255 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1255
	_t1256 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1256
	_t1257 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1257
}

func (p *Parser) _make_value_int32(v int32) *pb.Value {
	_t1258 := &pb.Value{}
	_t1258.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1258
}

func (p *Parser) _make_value_int64(v int64) *pb.Value {
	_t1259 := &pb.Value{}
	_t1259.Value = &pb.Value_IntValue{IntValue: v}
	return _t1259
}

func (p *Parser) _make_value_float64(v float64) *pb.Value {
	_t1260 := &pb.Value{}
	_t1260.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1260
}

func (p *Parser) _make_value_string(v string) *pb.Value {
	_t1261 := &pb.Value{}
	_t1261.Value = &pb.Value_StringValue{StringValue: v}
	return _t1261
}

func (p *Parser) _make_value_boolean(v bool) *pb.Value {
	_t1262 := &pb.Value{}
	_t1262.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1262
}

func (p *Parser) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1263 := &pb.Value{}
	_t1263.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1263
}

func (p *Parser) is_default_configure(cfg *pb.Configure) bool {
	if cfg.GetSemanticsVersion() != 0 {
		return false
	}
	if cfg.GetIvmConfig().GetLevel() != pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
		return false
	}
	return true
}

func (p *Parser) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	var _t1264 interface{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1265 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1265})
		_t1264 = nil
	} else {
		var _t1266 interface{}
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1267 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1267})
			_t1266 = nil
		} else {
			var _t1268 interface{}
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1269 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1269})
				_t1268 = nil
			}
			_t1266 = _t1268
		}
		_t1264 = _t1266
	}
	_ = _t1264
	_t1270 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1270})
	return listSort(result)
}

func (p *Parser) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1271 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1271})
	_t1272 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1272})
	var _t1273 interface{}
	if msg.GetNewLine() != "" {
		_t1274 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1274})
		_t1273 = nil
	}
	_ = _t1273
	_t1275 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1275})
	_t1276 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1276})
	_t1277 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1277})
	var _t1278 interface{}
	if msg.GetComment() != "" {
		_t1279 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1279})
		_t1278 = nil
	}
	_ = _t1278
	for _, missing_string := range msg.GetMissingStrings() {
		_t1280 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1280})
	}
	_t1281 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1281})
	_t1282 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1282})
	_t1283 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1283})
	return listSort(result)
}

func (p *Parser) _maybe_push_float64(result [][]interface{}, key string, val *float64) interface{} {
	var _t1284 interface{}
	if val != nil {
		_t1285 := p._make_value_float64(*val)
		result = append(result, []interface{}{key, _t1285})
		_t1284 = nil
	}
	_ = _t1284
	return nil
}

func (p *Parser) _maybe_push_int64(result [][]interface{}, key string, val *int64) interface{} {
	var _t1286 interface{}
	if val != nil {
		_t1287 := p._make_value_int64(*val)
		result = append(result, []interface{}{key, _t1287})
		_t1286 = nil
	}
	_ = _t1286
	return nil
}

func (p *Parser) _maybe_push_uint128(result [][]interface{}, key string, val *pb.UInt128Value) interface{} {
	var _t1288 interface{}
	if val != nil {
		_t1289 := p._make_value_uint128(val)
		result = append(result, []interface{}{key, _t1289})
		_t1288 = nil
	}
	_ = _t1288
	return nil
}

func (p *Parser) _maybe_push_bytes_as_string(result [][]interface{}, key string, val []byte) interface{} {
	var _t1290 interface{}
	if val != nil {
		_t1291 := p._make_value_string(string(val))
		result = append(result, []interface{}{key, _t1291})
		_t1290 = nil
	}
	_ = _t1290
	return nil
}

func (p *Parser) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1292 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1292})
	_t1293 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1293})
	_t1294 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1294})
	_t1295 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1295})
	var _t1296 interface{}
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		_t1297 := p._maybe_push_uint128(result, "betree_locator_root_pageid", msg.GetRelationLocator().GetRootPageid())
		_t1296 = _t1297
	}
	_ = _t1296
	var _t1298 interface{}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		_t1299 := p._maybe_push_bytes_as_string(result, "betree_locator_inline_data", msg.GetRelationLocator().GetInlineData())
		_t1298 = _t1299
	}
	_ = _t1298
	_t1300 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1300})
	_t1301 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1301})
	return listSort(result)
}

func (p *Parser) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	var _t1302 interface{}
	if msg.PartitionSize != nil {
		_t1303 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1303})
		_t1302 = nil
	}
	_ = _t1302
	var _t1304 interface{}
	if msg.Compression != nil {
		_t1305 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1305})
		_t1304 = nil
	}
	_ = _t1304
	var _t1306 interface{}
	if msg.SyntaxHeaderRow != nil {
		_t1307 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1307})
		_t1306 = nil
	}
	_ = _t1306
	var _t1308 interface{}
	if msg.SyntaxMissingString != nil {
		_t1309 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1309})
		_t1308 = nil
	}
	_ = _t1308
	var _t1310 interface{}
	if msg.SyntaxDelim != nil {
		_t1311 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1311})
		_t1310 = nil
	}
	_ = _t1310
	var _t1312 interface{}
	if msg.SyntaxQuotechar != nil {
		_t1313 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1313})
		_t1312 = nil
	}
	_ = _t1312
	var _t1314 interface{}
	if msg.SyntaxEscapechar != nil {
		_t1315 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1315})
		_t1314 = nil
	}
	_ = _t1314
	return listSort(result)
}

func (p *Parser) deconstruct_relation_id_string(msg *pb.RelationId) *string {
	name := p.relationIdToString(msg)
	if name != "" {
		return ptr(name)
	}
	return nil
}

func (p *Parser) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	if name == "" {
		return p.relationIdToUint128(msg)
	}
	return nil
}

func (p *Parser) deconstruct_bindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *Parser) deconstruct_bindings_with_arity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start7 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	p.pushPath(2)
	var _t619 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t620 := p.parse_configure()
		_t619 = _t620
	}
	configure0 := _t619
	p.popPath()
	p.pushPath(3)
	var _t621 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t622 := p.parse_sync()
		_t621 = _t622
	}
	sync1 := _t621
	p.popPath()
	p.pushPath(1)
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	idx5 := 0
	for cond3 {
		p.pushPath(idx5)
		_t623 := p.parse_epoch()
		item4 := _t623
		p.popPath()
		xs2 = append(xs2, item4)
		idx5 = (idx5 + 1)
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	p.popPath()
	epochs6 := xs2
	p.consumeLiteral(")")
	_t624 := p.default_configure()
	_t625 := configure0
	if configure0 == nil {
		_t625 = _t624
	}
	_t626 := &pb.Transaction{Epochs: epochs6, Configure: _t625, Sync: sync1}
	result8 := _t626
	p.recordSpan(span_start7)
	return result8
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start10 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t627 := p.parse_config_dict()
	config_dict9 := _t627
	p.consumeLiteral(")")
	_t628 := p.construct_configure(config_dict9)
	result11 := _t628
	p.recordSpan(span_start10)
	return result11
}

func (p *Parser) parse_config_dict() [][]interface{} {
	span_start17 := p.spanStart()
	p.consumeLiteral("{")
	xs12 := [][]interface{}{}
	cond13 := p.matchLookaheadLiteral(":", 0)
	idx15 := 0
	for cond13 {
		p.pushPath(idx15)
		_t629 := p.parse_config_key_value()
		item14 := _t629
		p.popPath()
		xs12 = append(xs12, item14)
		idx15 = (idx15 + 1)
		cond13 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values16 := xs12
	p.consumeLiteral("}")
	result18 := config_key_values16
	p.recordSpan(span_start17)
	return result18
}

func (p *Parser) parse_config_key_value() []interface{} {
	span_start21 := p.spanStart()
	p.consumeLiteral(":")
	symbol19 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t630 := p.parse_value()
	value20 := _t630
	result22 := []interface{}{symbol19, value20}
	p.recordSpan(span_start21)
	return result22
}

func (p *Parser) parse_value() *pb.Value {
	span_start33 := p.spanStart()
	var _t631 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t631 = 9
	} else {
		var _t632 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t632 = 8
		} else {
			var _t633 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t633 = 9
			} else {
				var _t634 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t635 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t635 = 1
					} else {
						var _t636 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t636 = 0
						} else {
							_t636 = -1
						}
						_t635 = _t636
					}
					_t634 = _t635
				} else {
					var _t637 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t637 = 5
					} else {
						var _t638 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t638 = 2
						} else {
							var _t639 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t639 = 6
							} else {
								var _t640 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t640 = 3
								} else {
									var _t641 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t641 = 4
									} else {
										var _t642 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t642 = 7
										} else {
											_t642 = -1
										}
										_t641 = _t642
									}
									_t640 = _t641
								}
								_t639 = _t640
							}
							_t638 = _t639
						}
						_t637 = _t638
					}
					_t634 = _t637
				}
				_t633 = _t634
			}
			_t632 = _t633
		}
		_t631 = _t632
	}
	prediction23 := _t631
	var _t643 *pb.Value
	if prediction23 == 9 {
		_t644 := p.parse_boolean_value()
		boolean_value32 := _t644
		_t645 := &pb.Value{}
		_t645.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value32}
		_t643 = _t645
	} else {
		var _t646 *pb.Value
		if prediction23 == 8 {
			p.consumeLiteral("missing")
			_t647 := &pb.MissingValue{}
			_t648 := &pb.Value{}
			_t648.Value = &pb.Value_MissingValue{MissingValue: _t647}
			_t646 = _t648
		} else {
			var _t649 *pb.Value
			if prediction23 == 7 {
				decimal31 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t650 := &pb.Value{}
				_t650.Value = &pb.Value_DecimalValue{DecimalValue: decimal31}
				_t649 = _t650
			} else {
				var _t651 *pb.Value
				if prediction23 == 6 {
					int12830 := p.consumeTerminal("INT128").Value.AsInt128()
					_t652 := &pb.Value{}
					_t652.Value = &pb.Value_Int128Value{Int128Value: int12830}
					_t651 = _t652
				} else {
					var _t653 *pb.Value
					if prediction23 == 5 {
						uint12829 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t654 := &pb.Value{}
						_t654.Value = &pb.Value_Uint128Value{Uint128Value: uint12829}
						_t653 = _t654
					} else {
						var _t655 *pb.Value
						if prediction23 == 4 {
							float28 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t656 := &pb.Value{}
							_t656.Value = &pb.Value_FloatValue{FloatValue: float28}
							_t655 = _t656
						} else {
							var _t657 *pb.Value
							if prediction23 == 3 {
								int27 := p.consumeTerminal("INT").Value.AsInt64()
								_t658 := &pb.Value{}
								_t658.Value = &pb.Value_IntValue{IntValue: int27}
								_t657 = _t658
							} else {
								var _t659 *pb.Value
								if prediction23 == 2 {
									string26 := p.consumeTerminal("STRING").Value.AsString()
									_t660 := &pb.Value{}
									_t660.Value = &pb.Value_StringValue{StringValue: string26}
									_t659 = _t660
								} else {
									var _t661 *pb.Value
									if prediction23 == 1 {
										_t662 := p.parse_datetime()
										datetime25 := _t662
										_t663 := &pb.Value{}
										_t663.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime25}
										_t661 = _t663
									} else {
										var _t664 *pb.Value
										if prediction23 == 0 {
											_t665 := p.parse_date()
											date24 := _t665
											_t666 := &pb.Value{}
											_t666.Value = &pb.Value_DateValue{DateValue: date24}
											_t664 = _t666
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t661 = _t664
									}
									_t659 = _t661
								}
								_t657 = _t659
							}
							_t655 = _t657
						}
						_t653 = _t655
					}
					_t651 = _t653
				}
				_t649 = _t651
			}
			_t646 = _t649
		}
		_t643 = _t646
	}
	result34 := _t643
	p.recordSpan(span_start33)
	return result34
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start38 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	p.pushPath(1)
	int35 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(2)
	int_336 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(3)
	int_437 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.consumeLiteral(")")
	_t667 := &pb.DateValue{Year: int32(int35), Month: int32(int_336), Day: int32(int_437)}
	result39 := _t667
	p.recordSpan(span_start38)
	return result39
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start47 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	p.pushPath(1)
	int40 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(2)
	int_341 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(3)
	int_442 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(4)
	int_543 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(5)
	int_644 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(6)
	int_745 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	var _t668 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t668 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_846 := _t668
	p.consumeLiteral(")")
	_t669 := &pb.DateTimeValue{Year: int32(int40), Month: int32(int_341), Day: int32(int_442), Hour: int32(int_543), Minute: int32(int_644), Second: int32(int_745), Microsecond: int32(deref(int_846, 0))}
	result48 := _t669
	p.recordSpan(span_start47)
	return result48
}

func (p *Parser) parse_boolean_value() bool {
	span_start50 := p.spanStart()
	var _t670 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t670 = 0
	} else {
		var _t671 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t671 = 1
		} else {
			_t671 = -1
		}
		_t670 = _t671
	}
	prediction49 := _t670
	var _t672 bool
	if prediction49 == 1 {
		p.consumeLiteral("false")
		_t672 = false
	} else {
		var _t673 bool
		if prediction49 == 0 {
			p.consumeLiteral("true")
			_t673 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t672 = _t673
	}
	result51 := _t672
	p.recordSpan(span_start50)
	return result51
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start57 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	p.pushPath(1)
	xs52 := []*pb.FragmentId{}
	cond53 := p.matchLookaheadLiteral(":", 0)
	idx55 := 0
	for cond53 {
		p.pushPath(idx55)
		_t674 := p.parse_fragment_id()
		item54 := _t674
		p.popPath()
		xs52 = append(xs52, item54)
		idx55 = (idx55 + 1)
		cond53 = p.matchLookaheadLiteral(":", 0)
	}
	p.popPath()
	fragment_ids56 := xs52
	p.consumeLiteral(")")
	_t675 := &pb.Sync{Fragments: fragment_ids56}
	result58 := _t675
	p.recordSpan(span_start57)
	return result58
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start60 := p.spanStart()
	p.consumeLiteral(":")
	symbol59 := p.consumeTerminal("SYMBOL").Value.AsString()
	result61 := &pb.FragmentId{Id: []byte(symbol59)}
	p.recordSpan(span_start60)
	return result61
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start64 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	p.pushPath(1)
	var _t676 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t677 := p.parse_epoch_writes()
		_t676 = _t677
	}
	epoch_writes62 := _t676
	p.popPath()
	p.pushPath(2)
	var _t678 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t679 := p.parse_epoch_reads()
		_t678 = _t679
	}
	epoch_reads63 := _t678
	p.popPath()
	p.consumeLiteral(")")
	_t680 := epoch_writes62
	if epoch_writes62 == nil {
		_t680 = []*pb.Write{}
	}
	_t681 := epoch_reads63
	if epoch_reads63 == nil {
		_t681 = []*pb.Read{}
	}
	_t682 := &pb.Epoch{Writes: _t680, Reads: _t681}
	result65 := _t682
	p.recordSpan(span_start64)
	return result65
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	span_start71 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs66 := []*pb.Write{}
	cond67 := p.matchLookaheadLiteral("(", 0)
	idx69 := 0
	for cond67 {
		p.pushPath(idx69)
		_t683 := p.parse_write()
		item68 := _t683
		p.popPath()
		xs66 = append(xs66, item68)
		idx69 = (idx69 + 1)
		cond67 = p.matchLookaheadLiteral("(", 0)
	}
	writes70 := xs66
	p.consumeLiteral(")")
	result72 := writes70
	p.recordSpan(span_start71)
	return result72
}

func (p *Parser) parse_write() *pb.Write {
	span_start77 := p.spanStart()
	var _t684 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t685 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t685 = 1
		} else {
			var _t686 int64
			if p.matchLookaheadLiteral("define", 1) {
				_t686 = 0
			} else {
				var _t687 int64
				if p.matchLookaheadLiteral("context", 1) {
					_t687 = 2
				} else {
					_t687 = -1
				}
				_t686 = _t687
			}
			_t685 = _t686
		}
		_t684 = _t685
	} else {
		_t684 = -1
	}
	prediction73 := _t684
	var _t688 *pb.Write
	if prediction73 == 2 {
		_t689 := p.parse_context()
		context76 := _t689
		_t690 := &pb.Write{}
		_t690.WriteType = &pb.Write_Context{Context: context76}
		_t688 = _t690
	} else {
		var _t691 *pb.Write
		if prediction73 == 1 {
			_t692 := p.parse_undefine()
			undefine75 := _t692
			_t693 := &pb.Write{}
			_t693.WriteType = &pb.Write_Undefine{Undefine: undefine75}
			_t691 = _t693
		} else {
			var _t694 *pb.Write
			if prediction73 == 0 {
				_t695 := p.parse_define()
				define74 := _t695
				_t696 := &pb.Write{}
				_t696.WriteType = &pb.Write_Define{Define: define74}
				_t694 = _t696
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t691 = _t694
		}
		_t688 = _t691
	}
	result78 := _t688
	p.recordSpan(span_start77)
	return result78
}

func (p *Parser) parse_define() *pb.Define {
	span_start80 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	p.pushPath(1)
	_t697 := p.parse_fragment()
	fragment79 := _t697
	p.popPath()
	p.consumeLiteral(")")
	_t698 := &pb.Define{Fragment: fragment79}
	result81 := _t698
	p.recordSpan(span_start80)
	return result81
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start88 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t699 := p.parse_new_fragment_id()
	new_fragment_id82 := _t699
	xs83 := []*pb.Declaration{}
	cond84 := p.matchLookaheadLiteral("(", 0)
	idx86 := 0
	for cond84 {
		p.pushPath(idx86)
		_t700 := p.parse_declaration()
		item85 := _t700
		p.popPath()
		xs83 = append(xs83, item85)
		idx86 = (idx86 + 1)
		cond84 = p.matchLookaheadLiteral("(", 0)
	}
	declarations87 := xs83
	p.consumeLiteral(")")
	result89 := p.constructFragment(new_fragment_id82, declarations87)
	p.recordSpan(span_start88)
	return result89
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start91 := p.spanStart()
	_t701 := p.parse_fragment_id()
	fragment_id90 := _t701
	p.startFragment(fragment_id90)
	result92 := fragment_id90
	p.recordSpan(span_start91)
	return result92
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start98 := p.spanStart()
	var _t702 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t703 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t703 = 3
		} else {
			var _t704 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t704 = 2
			} else {
				var _t705 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t705 = 0
				} else {
					var _t706 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t706 = 3
					} else {
						var _t707 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t707 = 3
						} else {
							var _t708 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t708 = 1
							} else {
								_t708 = -1
							}
							_t707 = _t708
						}
						_t706 = _t707
					}
					_t705 = _t706
				}
				_t704 = _t705
			}
			_t703 = _t704
		}
		_t702 = _t703
	} else {
		_t702 = -1
	}
	prediction93 := _t702
	var _t709 *pb.Declaration
	if prediction93 == 3 {
		_t710 := p.parse_data()
		data97 := _t710
		_t711 := &pb.Declaration{}
		_t711.DeclarationType = &pb.Declaration_Data{Data: data97}
		_t709 = _t711
	} else {
		var _t712 *pb.Declaration
		if prediction93 == 2 {
			_t713 := p.parse_constraint()
			constraint96 := _t713
			_t714 := &pb.Declaration{}
			_t714.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint96}
			_t712 = _t714
		} else {
			var _t715 *pb.Declaration
			if prediction93 == 1 {
				_t716 := p.parse_algorithm()
				algorithm95 := _t716
				_t717 := &pb.Declaration{}
				_t717.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm95}
				_t715 = _t717
			} else {
				var _t718 *pb.Declaration
				if prediction93 == 0 {
					_t719 := p.parse_def()
					def94 := _t719
					_t720 := &pb.Declaration{}
					_t720.DeclarationType = &pb.Declaration_Def{Def: def94}
					_t718 = _t720
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t715 = _t718
			}
			_t712 = _t715
		}
		_t709 = _t712
	}
	result99 := _t709
	p.recordSpan(span_start98)
	return result99
}

func (p *Parser) parse_def() *pb.Def {
	span_start103 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	p.pushPath(1)
	_t721 := p.parse_relation_id()
	relation_id100 := _t721
	p.popPath()
	p.pushPath(2)
	_t722 := p.parse_abstraction()
	abstraction101 := _t722
	p.popPath()
	p.pushPath(3)
	var _t723 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t724 := p.parse_attrs()
		_t723 = _t724
	}
	attrs102 := _t723
	p.popPath()
	p.consumeLiteral(")")
	_t725 := attrs102
	if attrs102 == nil {
		_t725 = []*pb.Attribute{}
	}
	_t726 := &pb.Def{Name: relation_id100, Body: abstraction101, Attrs: _t725}
	result104 := _t726
	p.recordSpan(span_start103)
	return result104
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start108 := p.spanStart()
	var _t727 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t727 = 0
	} else {
		var _t728 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t728 = 1
		} else {
			_t728 = -1
		}
		_t727 = _t728
	}
	prediction105 := _t727
	var _t729 *pb.RelationId
	if prediction105 == 1 {
		uint128107 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t729 = &pb.RelationId{IdLow: uint128107.Low, IdHigh: uint128107.High}
	} else {
		var _t730 *pb.RelationId
		if prediction105 == 0 {
			p.consumeLiteral(":")
			symbol106 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t730 = p.relationIdFromString(symbol106)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t729 = _t730
	}
	result109 := _t729
	p.recordSpan(span_start108)
	return result109
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start112 := p.spanStart()
	p.consumeLiteral("(")
	_t731 := p.parse_bindings()
	bindings110 := _t731
	p.pushPath(2)
	_t732 := p.parse_formula()
	formula111 := _t732
	p.popPath()
	p.consumeLiteral(")")
	_t733 := &pb.Abstraction{Vars: listConcat(bindings110[0].([]*pb.Binding), bindings110[1].([]*pb.Binding)), Value: formula111}
	result113 := _t733
	p.recordSpan(span_start112)
	return result113
}

func (p *Parser) parse_bindings() []interface{} {
	span_start120 := p.spanStart()
	p.consumeLiteral("[")
	xs114 := []*pb.Binding{}
	cond115 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx117 := 0
	for cond115 {
		p.pushPath(idx117)
		_t734 := p.parse_binding()
		item116 := _t734
		p.popPath()
		xs114 = append(xs114, item116)
		idx117 = (idx117 + 1)
		cond115 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings118 := xs114
	var _t735 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t736 := p.parse_value_bindings()
		_t735 = _t736
	}
	value_bindings119 := _t735
	p.consumeLiteral("]")
	_t737 := value_bindings119
	if value_bindings119 == nil {
		_t737 = []*pb.Binding{}
	}
	result121 := []interface{}{bindings118, _t737}
	p.recordSpan(span_start120)
	return result121
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start124 := p.spanStart()
	symbol122 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	p.pushPath(2)
	_t738 := p.parse_type()
	type123 := _t738
	p.popPath()
	_t739 := &pb.Var{Name: symbol122}
	_t740 := &pb.Binding{Var: _t739, Type: type123}
	result125 := _t740
	p.recordSpan(span_start124)
	return result125
}

func (p *Parser) parse_type() *pb.Type {
	span_start138 := p.spanStart()
	var _t741 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t741 = 0
	} else {
		var _t742 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t742 = 4
		} else {
			var _t743 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t743 = 1
			} else {
				var _t744 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t744 = 8
				} else {
					var _t745 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t745 = 5
					} else {
						var _t746 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t746 = 2
						} else {
							var _t747 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t747 = 3
							} else {
								var _t748 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t748 = 7
								} else {
									var _t749 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t749 = 6
									} else {
										var _t750 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t750 = 10
										} else {
											var _t751 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t751 = 9
											} else {
												_t751 = -1
											}
											_t750 = _t751
										}
										_t749 = _t750
									}
									_t748 = _t749
								}
								_t747 = _t748
							}
							_t746 = _t747
						}
						_t745 = _t746
					}
					_t744 = _t745
				}
				_t743 = _t744
			}
			_t742 = _t743
		}
		_t741 = _t742
	}
	prediction126 := _t741
	var _t752 *pb.Type
	if prediction126 == 10 {
		_t753 := p.parse_boolean_type()
		boolean_type137 := _t753
		_t754 := &pb.Type{}
		_t754.Type = &pb.Type_BooleanType{BooleanType: boolean_type137}
		_t752 = _t754
	} else {
		var _t755 *pb.Type
		if prediction126 == 9 {
			_t756 := p.parse_decimal_type()
			decimal_type136 := _t756
			_t757 := &pb.Type{}
			_t757.Type = &pb.Type_DecimalType{DecimalType: decimal_type136}
			_t755 = _t757
		} else {
			var _t758 *pb.Type
			if prediction126 == 8 {
				_t759 := p.parse_missing_type()
				missing_type135 := _t759
				_t760 := &pb.Type{}
				_t760.Type = &pb.Type_MissingType{MissingType: missing_type135}
				_t758 = _t760
			} else {
				var _t761 *pb.Type
				if prediction126 == 7 {
					_t762 := p.parse_datetime_type()
					datetime_type134 := _t762
					_t763 := &pb.Type{}
					_t763.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type134}
					_t761 = _t763
				} else {
					var _t764 *pb.Type
					if prediction126 == 6 {
						_t765 := p.parse_date_type()
						date_type133 := _t765
						_t766 := &pb.Type{}
						_t766.Type = &pb.Type_DateType{DateType: date_type133}
						_t764 = _t766
					} else {
						var _t767 *pb.Type
						if prediction126 == 5 {
							_t768 := p.parse_int128_type()
							int128_type132 := _t768
							_t769 := &pb.Type{}
							_t769.Type = &pb.Type_Int128Type{Int128Type: int128_type132}
							_t767 = _t769
						} else {
							var _t770 *pb.Type
							if prediction126 == 4 {
								_t771 := p.parse_uint128_type()
								uint128_type131 := _t771
								_t772 := &pb.Type{}
								_t772.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type131}
								_t770 = _t772
							} else {
								var _t773 *pb.Type
								if prediction126 == 3 {
									_t774 := p.parse_float_type()
									float_type130 := _t774
									_t775 := &pb.Type{}
									_t775.Type = &pb.Type_FloatType{FloatType: float_type130}
									_t773 = _t775
								} else {
									var _t776 *pb.Type
									if prediction126 == 2 {
										_t777 := p.parse_int_type()
										int_type129 := _t777
										_t778 := &pb.Type{}
										_t778.Type = &pb.Type_IntType{IntType: int_type129}
										_t776 = _t778
									} else {
										var _t779 *pb.Type
										if prediction126 == 1 {
											_t780 := p.parse_string_type()
											string_type128 := _t780
											_t781 := &pb.Type{}
											_t781.Type = &pb.Type_StringType{StringType: string_type128}
											_t779 = _t781
										} else {
											var _t782 *pb.Type
											if prediction126 == 0 {
												_t783 := p.parse_unspecified_type()
												unspecified_type127 := _t783
												_t784 := &pb.Type{}
												_t784.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type127}
												_t782 = _t784
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t779 = _t782
										}
										_t776 = _t779
									}
									_t773 = _t776
								}
								_t770 = _t773
							}
							_t767 = _t770
						}
						_t764 = _t767
					}
					_t761 = _t764
				}
				_t758 = _t761
			}
			_t755 = _t758
		}
		_t752 = _t755
	}
	result139 := _t752
	p.recordSpan(span_start138)
	return result139
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start140 := p.spanStart()
	p.consumeLiteral("UNKNOWN")
	_t785 := &pb.UnspecifiedType{}
	result141 := _t785
	p.recordSpan(span_start140)
	return result141
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start142 := p.spanStart()
	p.consumeLiteral("STRING")
	_t786 := &pb.StringType{}
	result143 := _t786
	p.recordSpan(span_start142)
	return result143
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start144 := p.spanStart()
	p.consumeLiteral("INT")
	_t787 := &pb.IntType{}
	result145 := _t787
	p.recordSpan(span_start144)
	return result145
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start146 := p.spanStart()
	p.consumeLiteral("FLOAT")
	_t788 := &pb.FloatType{}
	result147 := _t788
	p.recordSpan(span_start146)
	return result147
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start148 := p.spanStart()
	p.consumeLiteral("UINT128")
	_t789 := &pb.UInt128Type{}
	result149 := _t789
	p.recordSpan(span_start148)
	return result149
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start150 := p.spanStart()
	p.consumeLiteral("INT128")
	_t790 := &pb.Int128Type{}
	result151 := _t790
	p.recordSpan(span_start150)
	return result151
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start152 := p.spanStart()
	p.consumeLiteral("DATE")
	_t791 := &pb.DateType{}
	result153 := _t791
	p.recordSpan(span_start152)
	return result153
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start154 := p.spanStart()
	p.consumeLiteral("DATETIME")
	_t792 := &pb.DateTimeType{}
	result155 := _t792
	p.recordSpan(span_start154)
	return result155
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start156 := p.spanStart()
	p.consumeLiteral("MISSING")
	_t793 := &pb.MissingType{}
	result157 := _t793
	p.recordSpan(span_start156)
	return result157
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start160 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	p.pushPath(1)
	int158 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.pushPath(2)
	int_3159 := p.consumeTerminal("INT").Value.AsInt64()
	p.popPath()
	p.consumeLiteral(")")
	_t794 := &pb.DecimalType{Precision: int32(int158), Scale: int32(int_3159)}
	result161 := _t794
	p.recordSpan(span_start160)
	return result161
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start162 := p.spanStart()
	p.consumeLiteral("BOOLEAN")
	_t795 := &pb.BooleanType{}
	result163 := _t795
	p.recordSpan(span_start162)
	return result163
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	span_start169 := p.spanStart()
	p.consumeLiteral("|")
	xs164 := []*pb.Binding{}
	cond165 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx167 := 0
	for cond165 {
		p.pushPath(idx167)
		_t796 := p.parse_binding()
		item166 := _t796
		p.popPath()
		xs164 = append(xs164, item166)
		idx167 = (idx167 + 1)
		cond165 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings168 := xs164
	result170 := bindings168
	p.recordSpan(span_start169)
	return result170
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start185 := p.spanStart()
	var _t797 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t798 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t798 = 0
		} else {
			var _t799 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t799 = 11
			} else {
				var _t800 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t800 = 3
				} else {
					var _t801 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t801 = 10
					} else {
						var _t802 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t802 = 9
						} else {
							var _t803 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t803 = 5
							} else {
								var _t804 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t804 = 6
								} else {
									var _t805 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t805 = 7
									} else {
										var _t806 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t806 = 1
										} else {
											var _t807 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t807 = 2
											} else {
												var _t808 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t808 = 12
												} else {
													var _t809 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t809 = 8
													} else {
														var _t810 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t810 = 4
														} else {
															var _t811 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t811 = 10
															} else {
																var _t812 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t812 = 10
																} else {
																	var _t813 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t813 = 10
																	} else {
																		var _t814 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t814 = 10
																		} else {
																			var _t815 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t815 = 10
																			} else {
																				var _t816 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t816 = 10
																				} else {
																					var _t817 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t817 = 10
																					} else {
																						var _t818 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t818 = 10
																						} else {
																							var _t819 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t819 = 10
																							} else {
																								_t819 = -1
																							}
																							_t818 = _t819
																						}
																						_t817 = _t818
																					}
																					_t816 = _t817
																				}
																				_t815 = _t816
																			}
																			_t814 = _t815
																		}
																		_t813 = _t814
																	}
																	_t812 = _t813
																}
																_t811 = _t812
															}
															_t810 = _t811
														}
														_t809 = _t810
													}
													_t808 = _t809
												}
												_t807 = _t808
											}
											_t806 = _t807
										}
										_t805 = _t806
									}
									_t804 = _t805
								}
								_t803 = _t804
							}
							_t802 = _t803
						}
						_t801 = _t802
					}
					_t800 = _t801
				}
				_t799 = _t800
			}
			_t798 = _t799
		}
		_t797 = _t798
	} else {
		_t797 = -1
	}
	prediction171 := _t797
	var _t820 *pb.Formula
	if prediction171 == 12 {
		_t821 := p.parse_cast()
		cast184 := _t821
		_t822 := &pb.Formula{}
		_t822.FormulaType = &pb.Formula_Cast{Cast: cast184}
		_t820 = _t822
	} else {
		var _t823 *pb.Formula
		if prediction171 == 11 {
			_t824 := p.parse_rel_atom()
			rel_atom183 := _t824
			_t825 := &pb.Formula{}
			_t825.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom183}
			_t823 = _t825
		} else {
			var _t826 *pb.Formula
			if prediction171 == 10 {
				_t827 := p.parse_primitive()
				primitive182 := _t827
				_t828 := &pb.Formula{}
				_t828.FormulaType = &pb.Formula_Primitive{Primitive: primitive182}
				_t826 = _t828
			} else {
				var _t829 *pb.Formula
				if prediction171 == 9 {
					_t830 := p.parse_pragma()
					pragma181 := _t830
					_t831 := &pb.Formula{}
					_t831.FormulaType = &pb.Formula_Pragma{Pragma: pragma181}
					_t829 = _t831
				} else {
					var _t832 *pb.Formula
					if prediction171 == 8 {
						_t833 := p.parse_atom()
						atom180 := _t833
						_t834 := &pb.Formula{}
						_t834.FormulaType = &pb.Formula_Atom{Atom: atom180}
						_t832 = _t834
					} else {
						var _t835 *pb.Formula
						if prediction171 == 7 {
							_t836 := p.parse_ffi()
							ffi179 := _t836
							_t837 := &pb.Formula{}
							_t837.FormulaType = &pb.Formula_Ffi{Ffi: ffi179}
							_t835 = _t837
						} else {
							var _t838 *pb.Formula
							if prediction171 == 6 {
								_t839 := p.parse_not()
								not178 := _t839
								_t840 := &pb.Formula{}
								_t840.FormulaType = &pb.Formula_Not{Not: not178}
								_t838 = _t840
							} else {
								var _t841 *pb.Formula
								if prediction171 == 5 {
									_t842 := p.parse_disjunction()
									disjunction177 := _t842
									_t843 := &pb.Formula{}
									_t843.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction177}
									_t841 = _t843
								} else {
									var _t844 *pb.Formula
									if prediction171 == 4 {
										_t845 := p.parse_conjunction()
										conjunction176 := _t845
										_t846 := &pb.Formula{}
										_t846.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction176}
										_t844 = _t846
									} else {
										var _t847 *pb.Formula
										if prediction171 == 3 {
											_t848 := p.parse_reduce()
											reduce175 := _t848
											_t849 := &pb.Formula{}
											_t849.FormulaType = &pb.Formula_Reduce{Reduce: reduce175}
											_t847 = _t849
										} else {
											var _t850 *pb.Formula
											if prediction171 == 2 {
												_t851 := p.parse_exists()
												exists174 := _t851
												_t852 := &pb.Formula{}
												_t852.FormulaType = &pb.Formula_Exists{Exists: exists174}
												_t850 = _t852
											} else {
												var _t853 *pb.Formula
												if prediction171 == 1 {
													_t854 := p.parse_false()
													false173 := _t854
													_t855 := &pb.Formula{}
													_t855.FormulaType = &pb.Formula_Disjunction{Disjunction: false173}
													_t853 = _t855
												} else {
													var _t856 *pb.Formula
													if prediction171 == 0 {
														_t857 := p.parse_true()
														true172 := _t857
														_t858 := &pb.Formula{}
														_t858.FormulaType = &pb.Formula_Conjunction{Conjunction: true172}
														_t856 = _t858
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t853 = _t856
												}
												_t850 = _t853
											}
											_t847 = _t850
										}
										_t844 = _t847
									}
									_t841 = _t844
								}
								_t838 = _t841
							}
							_t835 = _t838
						}
						_t832 = _t835
					}
					_t829 = _t832
				}
				_t826 = _t829
			}
			_t823 = _t826
		}
		_t820 = _t823
	}
	result186 := _t820
	p.recordSpan(span_start185)
	return result186
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start187 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t859 := &pb.Conjunction{Args: []*pb.Formula{}}
	result188 := _t859
	p.recordSpan(span_start187)
	return result188
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start189 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t860 := &pb.Disjunction{Args: []*pb.Formula{}}
	result190 := _t860
	p.recordSpan(span_start189)
	return result190
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start193 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t861 := p.parse_bindings()
	bindings191 := _t861
	_t862 := p.parse_formula()
	formula192 := _t862
	p.consumeLiteral(")")
	_t863 := &pb.Abstraction{Vars: listConcat(bindings191[0].([]*pb.Binding), bindings191[1].([]*pb.Binding)), Value: formula192}
	_t864 := &pb.Exists{Body: _t863}
	result194 := _t864
	p.recordSpan(span_start193)
	return result194
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start198 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	p.pushPath(1)
	_t865 := p.parse_abstraction()
	abstraction195 := _t865
	p.popPath()
	p.pushPath(2)
	_t866 := p.parse_abstraction()
	abstraction_3196 := _t866
	p.popPath()
	p.pushPath(3)
	_t867 := p.parse_terms()
	terms197 := _t867
	p.popPath()
	p.consumeLiteral(")")
	_t868 := &pb.Reduce{Op: abstraction195, Body: abstraction_3196, Terms: terms197}
	result199 := _t868
	p.recordSpan(span_start198)
	return result199
}

func (p *Parser) parse_terms() []*pb.Term {
	span_start205 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs200 := []*pb.Term{}
	cond201 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx203 := 0
	for cond201 {
		p.pushPath(idx203)
		_t869 := p.parse_term()
		item202 := _t869
		p.popPath()
		xs200 = append(xs200, item202)
		idx203 = (idx203 + 1)
		cond201 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms204 := xs200
	p.consumeLiteral(")")
	result206 := terms204
	p.recordSpan(span_start205)
	return result206
}

func (p *Parser) parse_term() *pb.Term {
	span_start210 := p.spanStart()
	var _t870 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t870 = 1
	} else {
		var _t871 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t871 = 1
		} else {
			var _t872 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t872 = 1
			} else {
				var _t873 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t873 = 1
				} else {
					var _t874 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t874 = 1
					} else {
						var _t875 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t875 = 0
						} else {
							var _t876 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t876 = 1
							} else {
								var _t877 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t877 = 1
								} else {
									var _t878 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t878 = 1
									} else {
										var _t879 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t879 = 1
										} else {
											var _t880 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t880 = 1
											} else {
												_t880 = -1
											}
											_t879 = _t880
										}
										_t878 = _t879
									}
									_t877 = _t878
								}
								_t876 = _t877
							}
							_t875 = _t876
						}
						_t874 = _t875
					}
					_t873 = _t874
				}
				_t872 = _t873
			}
			_t871 = _t872
		}
		_t870 = _t871
	}
	prediction207 := _t870
	var _t881 *pb.Term
	if prediction207 == 1 {
		_t882 := p.parse_constant()
		constant209 := _t882
		_t883 := &pb.Term{}
		_t883.TermType = &pb.Term_Constant{Constant: constant209}
		_t881 = _t883
	} else {
		var _t884 *pb.Term
		if prediction207 == 0 {
			_t885 := p.parse_var()
			var208 := _t885
			_t886 := &pb.Term{}
			_t886.TermType = &pb.Term_Var{Var: var208}
			_t884 = _t886
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t881 = _t884
	}
	result211 := _t881
	p.recordSpan(span_start210)
	return result211
}

func (p *Parser) parse_var() *pb.Var {
	span_start213 := p.spanStart()
	symbol212 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t887 := &pb.Var{Name: symbol212}
	result214 := _t887
	p.recordSpan(span_start213)
	return result214
}

func (p *Parser) parse_constant() *pb.Value {
	span_start216 := p.spanStart()
	_t888 := p.parse_value()
	value215 := _t888
	result217 := value215
	p.recordSpan(span_start216)
	return result217
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start223 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	p.pushPath(1)
	xs218 := []*pb.Formula{}
	cond219 := p.matchLookaheadLiteral("(", 0)
	idx221 := 0
	for cond219 {
		p.pushPath(idx221)
		_t889 := p.parse_formula()
		item220 := _t889
		p.popPath()
		xs218 = append(xs218, item220)
		idx221 = (idx221 + 1)
		cond219 = p.matchLookaheadLiteral("(", 0)
	}
	p.popPath()
	formulas222 := xs218
	p.consumeLiteral(")")
	_t890 := &pb.Conjunction{Args: formulas222}
	result224 := _t890
	p.recordSpan(span_start223)
	return result224
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start230 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.pushPath(1)
	xs225 := []*pb.Formula{}
	cond226 := p.matchLookaheadLiteral("(", 0)
	idx228 := 0
	for cond226 {
		p.pushPath(idx228)
		_t891 := p.parse_formula()
		item227 := _t891
		p.popPath()
		xs225 = append(xs225, item227)
		idx228 = (idx228 + 1)
		cond226 = p.matchLookaheadLiteral("(", 0)
	}
	p.popPath()
	formulas229 := xs225
	p.consumeLiteral(")")
	_t892 := &pb.Disjunction{Args: formulas229}
	result231 := _t892
	p.recordSpan(span_start230)
	return result231
}

func (p *Parser) parse_not() *pb.Not {
	span_start233 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	p.pushPath(1)
	_t893 := p.parse_formula()
	formula232 := _t893
	p.popPath()
	p.consumeLiteral(")")
	_t894 := &pb.Not{Arg: formula232}
	result234 := _t894
	p.recordSpan(span_start233)
	return result234
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start238 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	p.pushPath(1)
	_t895 := p.parse_name()
	name235 := _t895
	p.popPath()
	p.pushPath(2)
	_t896 := p.parse_ffi_args()
	ffi_args236 := _t896
	p.popPath()
	p.pushPath(3)
	_t897 := p.parse_terms()
	terms237 := _t897
	p.popPath()
	p.consumeLiteral(")")
	_t898 := &pb.FFI{Name: name235, Args: ffi_args236, Terms: terms237}
	result239 := _t898
	p.recordSpan(span_start238)
	return result239
}

func (p *Parser) parse_name() string {
	span_start241 := p.spanStart()
	p.consumeLiteral(":")
	symbol240 := p.consumeTerminal("SYMBOL").Value.AsString()
	result242 := symbol240
	p.recordSpan(span_start241)
	return result242
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	span_start248 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs243 := []*pb.Abstraction{}
	cond244 := p.matchLookaheadLiteral("(", 0)
	idx246 := 0
	for cond244 {
		p.pushPath(idx246)
		_t899 := p.parse_abstraction()
		item245 := _t899
		p.popPath()
		xs243 = append(xs243, item245)
		idx246 = (idx246 + 1)
		cond244 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions247 := xs243
	p.consumeLiteral(")")
	result249 := abstractions247
	p.recordSpan(span_start248)
	return result249
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start256 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	p.pushPath(1)
	_t900 := p.parse_relation_id()
	relation_id250 := _t900
	p.popPath()
	p.pushPath(2)
	xs251 := []*pb.Term{}
	cond252 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx254 := 0
	for cond252 {
		p.pushPath(idx254)
		_t901 := p.parse_term()
		item253 := _t901
		p.popPath()
		xs251 = append(xs251, item253)
		idx254 = (idx254 + 1)
		cond252 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	terms255 := xs251
	p.consumeLiteral(")")
	_t902 := &pb.Atom{Name: relation_id250, Terms: terms255}
	result257 := _t902
	p.recordSpan(span_start256)
	return result257
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start264 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	p.pushPath(1)
	_t903 := p.parse_name()
	name258 := _t903
	p.popPath()
	p.pushPath(2)
	xs259 := []*pb.Term{}
	cond260 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx262 := 0
	for cond260 {
		p.pushPath(idx262)
		_t904 := p.parse_term()
		item261 := _t904
		p.popPath()
		xs259 = append(xs259, item261)
		idx262 = (idx262 + 1)
		cond260 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	terms263 := xs259
	p.consumeLiteral(")")
	_t905 := &pb.Pragma{Name: name258, Terms: terms263}
	result265 := _t905
	p.recordSpan(span_start264)
	return result265
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start282 := p.spanStart()
	var _t906 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t907 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t907 = 9
		} else {
			var _t908 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t908 = 4
			} else {
				var _t909 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t909 = 3
				} else {
					var _t910 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t910 = 0
					} else {
						var _t911 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t911 = 2
						} else {
							var _t912 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t912 = 1
							} else {
								var _t913 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t913 = 8
								} else {
									var _t914 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t914 = 6
									} else {
										var _t915 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t915 = 5
										} else {
											var _t916 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t916 = 7
											} else {
												_t916 = -1
											}
											_t915 = _t916
										}
										_t914 = _t915
									}
									_t913 = _t914
								}
								_t912 = _t913
							}
							_t911 = _t912
						}
						_t910 = _t911
					}
					_t909 = _t910
				}
				_t908 = _t909
			}
			_t907 = _t908
		}
		_t906 = _t907
	} else {
		_t906 = -1
	}
	prediction266 := _t906
	var _t917 *pb.Primitive
	if prediction266 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		p.pushPath(1)
		_t918 := p.parse_name()
		name276 := _t918
		p.popPath()
		p.pushPath(2)
		xs277 := []*pb.RelTerm{}
		cond278 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		idx280 := 0
		for cond278 {
			p.pushPath(idx280)
			_t919 := p.parse_rel_term()
			item279 := _t919
			p.popPath()
			xs277 = append(xs277, item279)
			idx280 = (idx280 + 1)
			cond278 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		p.popPath()
		rel_terms281 := xs277
		p.consumeLiteral(")")
		_t920 := &pb.Primitive{Name: name276, Terms: rel_terms281}
		_t917 = _t920
	} else {
		var _t921 *pb.Primitive
		if prediction266 == 8 {
			_t922 := p.parse_divide()
			divide275 := _t922
			_t921 = divide275
		} else {
			var _t923 *pb.Primitive
			if prediction266 == 7 {
				_t924 := p.parse_multiply()
				multiply274 := _t924
				_t923 = multiply274
			} else {
				var _t925 *pb.Primitive
				if prediction266 == 6 {
					_t926 := p.parse_minus()
					minus273 := _t926
					_t925 = minus273
				} else {
					var _t927 *pb.Primitive
					if prediction266 == 5 {
						_t928 := p.parse_add()
						add272 := _t928
						_t927 = add272
					} else {
						var _t929 *pb.Primitive
						if prediction266 == 4 {
							_t930 := p.parse_gt_eq()
							gt_eq271 := _t930
							_t929 = gt_eq271
						} else {
							var _t931 *pb.Primitive
							if prediction266 == 3 {
								_t932 := p.parse_gt()
								gt270 := _t932
								_t931 = gt270
							} else {
								var _t933 *pb.Primitive
								if prediction266 == 2 {
									_t934 := p.parse_lt_eq()
									lt_eq269 := _t934
									_t933 = lt_eq269
								} else {
									var _t935 *pb.Primitive
									if prediction266 == 1 {
										_t936 := p.parse_lt()
										lt268 := _t936
										_t935 = lt268
									} else {
										var _t937 *pb.Primitive
										if prediction266 == 0 {
											_t938 := p.parse_eq()
											eq267 := _t938
											_t937 = eq267
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t935 = _t937
									}
									_t933 = _t935
								}
								_t931 = _t933
							}
							_t929 = _t931
						}
						_t927 = _t929
					}
					_t925 = _t927
				}
				_t923 = _t925
			}
			_t921 = _t923
		}
		_t917 = _t921
	}
	result283 := _t917
	p.recordSpan(span_start282)
	return result283
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start286 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t939 := p.parse_term()
	term284 := _t939
	_t940 := p.parse_term()
	term_3285 := _t940
	p.consumeLiteral(")")
	_t941 := &pb.RelTerm{}
	_t941.RelTermType = &pb.RelTerm_Term{Term: term284}
	_t942 := &pb.RelTerm{}
	_t942.RelTermType = &pb.RelTerm_Term{Term: term_3285}
	_t943 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t941, _t942}}
	result287 := _t943
	p.recordSpan(span_start286)
	return result287
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start290 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t944 := p.parse_term()
	term288 := _t944
	_t945 := p.parse_term()
	term_3289 := _t945
	p.consumeLiteral(")")
	_t946 := &pb.RelTerm{}
	_t946.RelTermType = &pb.RelTerm_Term{Term: term288}
	_t947 := &pb.RelTerm{}
	_t947.RelTermType = &pb.RelTerm_Term{Term: term_3289}
	_t948 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t946, _t947}}
	result291 := _t948
	p.recordSpan(span_start290)
	return result291
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start294 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t949 := p.parse_term()
	term292 := _t949
	_t950 := p.parse_term()
	term_3293 := _t950
	p.consumeLiteral(")")
	_t951 := &pb.RelTerm{}
	_t951.RelTermType = &pb.RelTerm_Term{Term: term292}
	_t952 := &pb.RelTerm{}
	_t952.RelTermType = &pb.RelTerm_Term{Term: term_3293}
	_t953 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t951, _t952}}
	result295 := _t953
	p.recordSpan(span_start294)
	return result295
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start298 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t954 := p.parse_term()
	term296 := _t954
	_t955 := p.parse_term()
	term_3297 := _t955
	p.consumeLiteral(")")
	_t956 := &pb.RelTerm{}
	_t956.RelTermType = &pb.RelTerm_Term{Term: term296}
	_t957 := &pb.RelTerm{}
	_t957.RelTermType = &pb.RelTerm_Term{Term: term_3297}
	_t958 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t956, _t957}}
	result299 := _t958
	p.recordSpan(span_start298)
	return result299
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start302 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t959 := p.parse_term()
	term300 := _t959
	_t960 := p.parse_term()
	term_3301 := _t960
	p.consumeLiteral(")")
	_t961 := &pb.RelTerm{}
	_t961.RelTermType = &pb.RelTerm_Term{Term: term300}
	_t962 := &pb.RelTerm{}
	_t962.RelTermType = &pb.RelTerm_Term{Term: term_3301}
	_t963 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t961, _t962}}
	result303 := _t963
	p.recordSpan(span_start302)
	return result303
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start307 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t964 := p.parse_term()
	term304 := _t964
	_t965 := p.parse_term()
	term_3305 := _t965
	_t966 := p.parse_term()
	term_4306 := _t966
	p.consumeLiteral(")")
	_t967 := &pb.RelTerm{}
	_t967.RelTermType = &pb.RelTerm_Term{Term: term304}
	_t968 := &pb.RelTerm{}
	_t968.RelTermType = &pb.RelTerm_Term{Term: term_3305}
	_t969 := &pb.RelTerm{}
	_t969.RelTermType = &pb.RelTerm_Term{Term: term_4306}
	_t970 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t967, _t968, _t969}}
	result308 := _t970
	p.recordSpan(span_start307)
	return result308
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start312 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t971 := p.parse_term()
	term309 := _t971
	_t972 := p.parse_term()
	term_3310 := _t972
	_t973 := p.parse_term()
	term_4311 := _t973
	p.consumeLiteral(")")
	_t974 := &pb.RelTerm{}
	_t974.RelTermType = &pb.RelTerm_Term{Term: term309}
	_t975 := &pb.RelTerm{}
	_t975.RelTermType = &pb.RelTerm_Term{Term: term_3310}
	_t976 := &pb.RelTerm{}
	_t976.RelTermType = &pb.RelTerm_Term{Term: term_4311}
	_t977 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t974, _t975, _t976}}
	result313 := _t977
	p.recordSpan(span_start312)
	return result313
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start317 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t978 := p.parse_term()
	term314 := _t978
	_t979 := p.parse_term()
	term_3315 := _t979
	_t980 := p.parse_term()
	term_4316 := _t980
	p.consumeLiteral(")")
	_t981 := &pb.RelTerm{}
	_t981.RelTermType = &pb.RelTerm_Term{Term: term314}
	_t982 := &pb.RelTerm{}
	_t982.RelTermType = &pb.RelTerm_Term{Term: term_3315}
	_t983 := &pb.RelTerm{}
	_t983.RelTermType = &pb.RelTerm_Term{Term: term_4316}
	_t984 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t981, _t982, _t983}}
	result318 := _t984
	p.recordSpan(span_start317)
	return result318
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start322 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t985 := p.parse_term()
	term319 := _t985
	_t986 := p.parse_term()
	term_3320 := _t986
	_t987 := p.parse_term()
	term_4321 := _t987
	p.consumeLiteral(")")
	_t988 := &pb.RelTerm{}
	_t988.RelTermType = &pb.RelTerm_Term{Term: term319}
	_t989 := &pb.RelTerm{}
	_t989.RelTermType = &pb.RelTerm_Term{Term: term_3320}
	_t990 := &pb.RelTerm{}
	_t990.RelTermType = &pb.RelTerm_Term{Term: term_4321}
	_t991 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t988, _t989, _t990}}
	result323 := _t991
	p.recordSpan(span_start322)
	return result323
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start327 := p.spanStart()
	var _t992 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t992 = 1
	} else {
		var _t993 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t993 = 1
		} else {
			var _t994 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t994 = 1
			} else {
				var _t995 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t995 = 1
				} else {
					var _t996 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t996 = 0
					} else {
						var _t997 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t997 = 1
						} else {
							var _t998 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t998 = 1
							} else {
								var _t999 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t999 = 1
								} else {
									var _t1000 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1000 = 1
									} else {
										var _t1001 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1001 = 1
										} else {
											var _t1002 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1002 = 1
											} else {
												var _t1003 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1003 = 1
												} else {
													_t1003 = -1
												}
												_t1002 = _t1003
											}
											_t1001 = _t1002
										}
										_t1000 = _t1001
									}
									_t999 = _t1000
								}
								_t998 = _t999
							}
							_t997 = _t998
						}
						_t996 = _t997
					}
					_t995 = _t996
				}
				_t994 = _t995
			}
			_t993 = _t994
		}
		_t992 = _t993
	}
	prediction324 := _t992
	var _t1004 *pb.RelTerm
	if prediction324 == 1 {
		_t1005 := p.parse_term()
		term326 := _t1005
		_t1006 := &pb.RelTerm{}
		_t1006.RelTermType = &pb.RelTerm_Term{Term: term326}
		_t1004 = _t1006
	} else {
		var _t1007 *pb.RelTerm
		if prediction324 == 0 {
			_t1008 := p.parse_specialized_value()
			specialized_value325 := _t1008
			_t1009 := &pb.RelTerm{}
			_t1009.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value325}
			_t1007 = _t1009
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1004 = _t1007
	}
	result328 := _t1004
	p.recordSpan(span_start327)
	return result328
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start330 := p.spanStart()
	p.consumeLiteral("#")
	_t1010 := p.parse_value()
	value329 := _t1010
	result331 := value329
	p.recordSpan(span_start330)
	return result331
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start338 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	p.pushPath(3)
	_t1011 := p.parse_name()
	name332 := _t1011
	p.popPath()
	p.pushPath(2)
	xs333 := []*pb.RelTerm{}
	cond334 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx336 := 0
	for cond334 {
		p.pushPath(idx336)
		_t1012 := p.parse_rel_term()
		item335 := _t1012
		p.popPath()
		xs333 = append(xs333, item335)
		idx336 = (idx336 + 1)
		cond334 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	rel_terms337 := xs333
	p.consumeLiteral(")")
	_t1013 := &pb.RelAtom{Name: name332, Terms: rel_terms337}
	result339 := _t1013
	p.recordSpan(span_start338)
	return result339
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start342 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	p.pushPath(2)
	_t1014 := p.parse_term()
	term340 := _t1014
	p.popPath()
	p.pushPath(3)
	_t1015 := p.parse_term()
	term_3341 := _t1015
	p.popPath()
	p.consumeLiteral(")")
	_t1016 := &pb.Cast{Input: term340, Result: term_3341}
	result343 := _t1016
	p.recordSpan(span_start342)
	return result343
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	span_start349 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs344 := []*pb.Attribute{}
	cond345 := p.matchLookaheadLiteral("(", 0)
	idx347 := 0
	for cond345 {
		p.pushPath(idx347)
		_t1017 := p.parse_attribute()
		item346 := _t1017
		p.popPath()
		xs344 = append(xs344, item346)
		idx347 = (idx347 + 1)
		cond345 = p.matchLookaheadLiteral("(", 0)
	}
	attributes348 := xs344
	p.consumeLiteral(")")
	result350 := attributes348
	p.recordSpan(span_start349)
	return result350
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start357 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	p.pushPath(1)
	_t1018 := p.parse_name()
	name351 := _t1018
	p.popPath()
	p.pushPath(2)
	xs352 := []*pb.Value{}
	cond353 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	idx355 := 0
	for cond353 {
		p.pushPath(idx355)
		_t1019 := p.parse_value()
		item354 := _t1019
		p.popPath()
		xs352 = append(xs352, item354)
		idx355 = (idx355 + 1)
		cond353 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	values356 := xs352
	p.consumeLiteral(")")
	_t1020 := &pb.Attribute{Name: name351, Args: values356}
	result358 := _t1020
	p.recordSpan(span_start357)
	return result358
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start365 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	p.pushPath(1)
	xs359 := []*pb.RelationId{}
	cond360 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx362 := 0
	for cond360 {
		p.pushPath(idx362)
		_t1021 := p.parse_relation_id()
		item361 := _t1021
		p.popPath()
		xs359 = append(xs359, item361)
		idx362 = (idx362 + 1)
		cond360 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	relation_ids363 := xs359
	p.pushPath(2)
	_t1022 := p.parse_script()
	script364 := _t1022
	p.popPath()
	p.consumeLiteral(")")
	_t1023 := &pb.Algorithm{Global: relation_ids363, Body: script364}
	result366 := _t1023
	p.recordSpan(span_start365)
	return result366
}

func (p *Parser) parse_script() *pb.Script {
	span_start372 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	p.pushPath(1)
	xs367 := []*pb.Construct{}
	cond368 := p.matchLookaheadLiteral("(", 0)
	idx370 := 0
	for cond368 {
		p.pushPath(idx370)
		_t1024 := p.parse_construct()
		item369 := _t1024
		p.popPath()
		xs367 = append(xs367, item369)
		idx370 = (idx370 + 1)
		cond368 = p.matchLookaheadLiteral("(", 0)
	}
	p.popPath()
	constructs371 := xs367
	p.consumeLiteral(")")
	_t1025 := &pb.Script{Constructs: constructs371}
	result373 := _t1025
	p.recordSpan(span_start372)
	return result373
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start377 := p.spanStart()
	var _t1026 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1027 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1027 = 1
		} else {
			var _t1028 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1028 = 1
			} else {
				var _t1029 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1029 = 1
				} else {
					var _t1030 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1030 = 0
					} else {
						var _t1031 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1031 = 1
						} else {
							var _t1032 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1032 = 1
							} else {
								_t1032 = -1
							}
							_t1031 = _t1032
						}
						_t1030 = _t1031
					}
					_t1029 = _t1030
				}
				_t1028 = _t1029
			}
			_t1027 = _t1028
		}
		_t1026 = _t1027
	} else {
		_t1026 = -1
	}
	prediction374 := _t1026
	var _t1033 *pb.Construct
	if prediction374 == 1 {
		_t1034 := p.parse_instruction()
		instruction376 := _t1034
		_t1035 := &pb.Construct{}
		_t1035.ConstructType = &pb.Construct_Instruction{Instruction: instruction376}
		_t1033 = _t1035
	} else {
		var _t1036 *pb.Construct
		if prediction374 == 0 {
			_t1037 := p.parse_loop()
			loop375 := _t1037
			_t1038 := &pb.Construct{}
			_t1038.ConstructType = &pb.Construct_Loop{Loop: loop375}
			_t1036 = _t1038
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1033 = _t1036
	}
	result378 := _t1033
	p.recordSpan(span_start377)
	return result378
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start381 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	p.pushPath(1)
	_t1039 := p.parse_init()
	init379 := _t1039
	p.popPath()
	p.pushPath(2)
	_t1040 := p.parse_script()
	script380 := _t1040
	p.popPath()
	p.consumeLiteral(")")
	_t1041 := &pb.Loop{Init: init379, Body: script380}
	result382 := _t1041
	p.recordSpan(span_start381)
	return result382
}

func (p *Parser) parse_init() []*pb.Instruction {
	span_start388 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs383 := []*pb.Instruction{}
	cond384 := p.matchLookaheadLiteral("(", 0)
	idx386 := 0
	for cond384 {
		p.pushPath(idx386)
		_t1042 := p.parse_instruction()
		item385 := _t1042
		p.popPath()
		xs383 = append(xs383, item385)
		idx386 = (idx386 + 1)
		cond384 = p.matchLookaheadLiteral("(", 0)
	}
	instructions387 := xs383
	p.consumeLiteral(")")
	result389 := instructions387
	p.recordSpan(span_start388)
	return result389
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start396 := p.spanStart()
	var _t1043 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1044 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1044 = 1
		} else {
			var _t1045 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1045 = 4
			} else {
				var _t1046 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1046 = 3
				} else {
					var _t1047 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1047 = 2
					} else {
						var _t1048 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1048 = 0
						} else {
							_t1048 = -1
						}
						_t1047 = _t1048
					}
					_t1046 = _t1047
				}
				_t1045 = _t1046
			}
			_t1044 = _t1045
		}
		_t1043 = _t1044
	} else {
		_t1043 = -1
	}
	prediction390 := _t1043
	var _t1049 *pb.Instruction
	if prediction390 == 4 {
		_t1050 := p.parse_monus_def()
		monus_def395 := _t1050
		_t1051 := &pb.Instruction{}
		_t1051.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def395}
		_t1049 = _t1051
	} else {
		var _t1052 *pb.Instruction
		if prediction390 == 3 {
			_t1053 := p.parse_monoid_def()
			monoid_def394 := _t1053
			_t1054 := &pb.Instruction{}
			_t1054.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def394}
			_t1052 = _t1054
		} else {
			var _t1055 *pb.Instruction
			if prediction390 == 2 {
				_t1056 := p.parse_break()
				break393 := _t1056
				_t1057 := &pb.Instruction{}
				_t1057.InstrType = &pb.Instruction_Break{Break: break393}
				_t1055 = _t1057
			} else {
				var _t1058 *pb.Instruction
				if prediction390 == 1 {
					_t1059 := p.parse_upsert()
					upsert392 := _t1059
					_t1060 := &pb.Instruction{}
					_t1060.InstrType = &pb.Instruction_Upsert{Upsert: upsert392}
					_t1058 = _t1060
				} else {
					var _t1061 *pb.Instruction
					if prediction390 == 0 {
						_t1062 := p.parse_assign()
						assign391 := _t1062
						_t1063 := &pb.Instruction{}
						_t1063.InstrType = &pb.Instruction_Assign{Assign: assign391}
						_t1061 = _t1063
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1058 = _t1061
				}
				_t1055 = _t1058
			}
			_t1052 = _t1055
		}
		_t1049 = _t1052
	}
	result397 := _t1049
	p.recordSpan(span_start396)
	return result397
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start401 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	p.pushPath(1)
	_t1064 := p.parse_relation_id()
	relation_id398 := _t1064
	p.popPath()
	p.pushPath(2)
	_t1065 := p.parse_abstraction()
	abstraction399 := _t1065
	p.popPath()
	p.pushPath(3)
	var _t1066 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1067 := p.parse_attrs()
		_t1066 = _t1067
	}
	attrs400 := _t1066
	p.popPath()
	p.consumeLiteral(")")
	_t1068 := attrs400
	if attrs400 == nil {
		_t1068 = []*pb.Attribute{}
	}
	_t1069 := &pb.Assign{Name: relation_id398, Body: abstraction399, Attrs: _t1068}
	result402 := _t1069
	p.recordSpan(span_start401)
	return result402
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start406 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	p.pushPath(1)
	_t1070 := p.parse_relation_id()
	relation_id403 := _t1070
	p.popPath()
	_t1071 := p.parse_abstraction_with_arity()
	abstraction_with_arity404 := _t1071
	p.pushPath(3)
	var _t1072 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1073 := p.parse_attrs()
		_t1072 = _t1073
	}
	attrs405 := _t1072
	p.popPath()
	p.consumeLiteral(")")
	_t1074 := attrs405
	if attrs405 == nil {
		_t1074 = []*pb.Attribute{}
	}
	_t1075 := &pb.Upsert{Name: relation_id403, Body: abstraction_with_arity404[0].(*pb.Abstraction), Attrs: _t1074, ValueArity: abstraction_with_arity404[1].(int64)}
	result407 := _t1075
	p.recordSpan(span_start406)
	return result407
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	span_start410 := p.spanStart()
	p.consumeLiteral("(")
	_t1076 := p.parse_bindings()
	bindings408 := _t1076
	_t1077 := p.parse_formula()
	formula409 := _t1077
	p.consumeLiteral(")")
	_t1078 := &pb.Abstraction{Vars: listConcat(bindings408[0].([]*pb.Binding), bindings408[1].([]*pb.Binding)), Value: formula409}
	result411 := []interface{}{_t1078, int64(len(bindings408[1].([]*pb.Binding)))}
	p.recordSpan(span_start410)
	return result411
}

func (p *Parser) parse_break() *pb.Break {
	span_start415 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	p.pushPath(1)
	_t1079 := p.parse_relation_id()
	relation_id412 := _t1079
	p.popPath()
	p.pushPath(2)
	_t1080 := p.parse_abstraction()
	abstraction413 := _t1080
	p.popPath()
	p.pushPath(3)
	var _t1081 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1082 := p.parse_attrs()
		_t1081 = _t1082
	}
	attrs414 := _t1081
	p.popPath()
	p.consumeLiteral(")")
	_t1083 := attrs414
	if attrs414 == nil {
		_t1083 = []*pb.Attribute{}
	}
	_t1084 := &pb.Break{Name: relation_id412, Body: abstraction413, Attrs: _t1083}
	result416 := _t1084
	p.recordSpan(span_start415)
	return result416
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start421 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	p.pushPath(1)
	_t1085 := p.parse_monoid()
	monoid417 := _t1085
	p.popPath()
	p.pushPath(2)
	_t1086 := p.parse_relation_id()
	relation_id418 := _t1086
	p.popPath()
	_t1087 := p.parse_abstraction_with_arity()
	abstraction_with_arity419 := _t1087
	p.pushPath(4)
	var _t1088 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1089 := p.parse_attrs()
		_t1088 = _t1089
	}
	attrs420 := _t1088
	p.popPath()
	p.consumeLiteral(")")
	_t1090 := attrs420
	if attrs420 == nil {
		_t1090 = []*pb.Attribute{}
	}
	_t1091 := &pb.MonoidDef{Monoid: monoid417, Name: relation_id418, Body: abstraction_with_arity419[0].(*pb.Abstraction), Attrs: _t1090, ValueArity: abstraction_with_arity419[1].(int64)}
	result422 := _t1091
	p.recordSpan(span_start421)
	return result422
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start428 := p.spanStart()
	var _t1092 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1093 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1093 = 3
		} else {
			var _t1094 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1094 = 0
			} else {
				var _t1095 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1095 = 1
				} else {
					var _t1096 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1096 = 2
					} else {
						_t1096 = -1
					}
					_t1095 = _t1096
				}
				_t1094 = _t1095
			}
			_t1093 = _t1094
		}
		_t1092 = _t1093
	} else {
		_t1092 = -1
	}
	prediction423 := _t1092
	var _t1097 *pb.Monoid
	if prediction423 == 3 {
		_t1098 := p.parse_sum_monoid()
		sum_monoid427 := _t1098
		_t1099 := &pb.Monoid{}
		_t1099.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid427}
		_t1097 = _t1099
	} else {
		var _t1100 *pb.Monoid
		if prediction423 == 2 {
			_t1101 := p.parse_max_monoid()
			max_monoid426 := _t1101
			_t1102 := &pb.Monoid{}
			_t1102.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid426}
			_t1100 = _t1102
		} else {
			var _t1103 *pb.Monoid
			if prediction423 == 1 {
				_t1104 := p.parse_min_monoid()
				min_monoid425 := _t1104
				_t1105 := &pb.Monoid{}
				_t1105.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid425}
				_t1103 = _t1105
			} else {
				var _t1106 *pb.Monoid
				if prediction423 == 0 {
					_t1107 := p.parse_or_monoid()
					or_monoid424 := _t1107
					_t1108 := &pb.Monoid{}
					_t1108.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid424}
					_t1106 = _t1108
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1103 = _t1106
			}
			_t1100 = _t1103
		}
		_t1097 = _t1100
	}
	result429 := _t1097
	p.recordSpan(span_start428)
	return result429
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start430 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1109 := &pb.OrMonoid{}
	result431 := _t1109
	p.recordSpan(span_start430)
	return result431
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start433 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	p.pushPath(1)
	_t1110 := p.parse_type()
	type432 := _t1110
	p.popPath()
	p.consumeLiteral(")")
	_t1111 := &pb.MinMonoid{Type: type432}
	result434 := _t1111
	p.recordSpan(span_start433)
	return result434
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start436 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	p.pushPath(1)
	_t1112 := p.parse_type()
	type435 := _t1112
	p.popPath()
	p.consumeLiteral(")")
	_t1113 := &pb.MaxMonoid{Type: type435}
	result437 := _t1113
	p.recordSpan(span_start436)
	return result437
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start439 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	p.pushPath(1)
	_t1114 := p.parse_type()
	type438 := _t1114
	p.popPath()
	p.consumeLiteral(")")
	_t1115 := &pb.SumMonoid{Type: type438}
	result440 := _t1115
	p.recordSpan(span_start439)
	return result440
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start445 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	p.pushPath(1)
	_t1116 := p.parse_monoid()
	monoid441 := _t1116
	p.popPath()
	p.pushPath(2)
	_t1117 := p.parse_relation_id()
	relation_id442 := _t1117
	p.popPath()
	_t1118 := p.parse_abstraction_with_arity()
	abstraction_with_arity443 := _t1118
	p.pushPath(4)
	var _t1119 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1120 := p.parse_attrs()
		_t1119 = _t1120
	}
	attrs444 := _t1119
	p.popPath()
	p.consumeLiteral(")")
	_t1121 := attrs444
	if attrs444 == nil {
		_t1121 = []*pb.Attribute{}
	}
	_t1122 := &pb.MonusDef{Monoid: monoid441, Name: relation_id442, Body: abstraction_with_arity443[0].(*pb.Abstraction), Attrs: _t1121, ValueArity: abstraction_with_arity443[1].(int64)}
	result446 := _t1122
	p.recordSpan(span_start445)
	return result446
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start451 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	p.pushPath(2)
	_t1123 := p.parse_relation_id()
	relation_id447 := _t1123
	p.popPath()
	_t1124 := p.parse_abstraction()
	abstraction448 := _t1124
	_t1125 := p.parse_functional_dependency_keys()
	functional_dependency_keys449 := _t1125
	_t1126 := p.parse_functional_dependency_values()
	functional_dependency_values450 := _t1126
	p.consumeLiteral(")")
	_t1127 := &pb.FunctionalDependency{Guard: abstraction448, Keys: functional_dependency_keys449, Values: functional_dependency_values450}
	_t1128 := &pb.Constraint{Name: relation_id447}
	_t1128.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1127}
	result452 := _t1128
	p.recordSpan(span_start451)
	return result452
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	span_start458 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs453 := []*pb.Var{}
	cond454 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx456 := 0
	for cond454 {
		p.pushPath(idx456)
		_t1129 := p.parse_var()
		item455 := _t1129
		p.popPath()
		xs453 = append(xs453, item455)
		idx456 = (idx456 + 1)
		cond454 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars457 := xs453
	p.consumeLiteral(")")
	result459 := vars457
	p.recordSpan(span_start458)
	return result459
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	span_start465 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs460 := []*pb.Var{}
	cond461 := p.matchLookaheadTerminal("SYMBOL", 0)
	idx463 := 0
	for cond461 {
		p.pushPath(idx463)
		_t1130 := p.parse_var()
		item462 := _t1130
		p.popPath()
		xs460 = append(xs460, item462)
		idx463 = (idx463 + 1)
		cond461 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars464 := xs460
	p.consumeLiteral(")")
	result466 := vars464
	p.recordSpan(span_start465)
	return result466
}

func (p *Parser) parse_data() *pb.Data {
	span_start471 := p.spanStart()
	var _t1131 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1132 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1132 = 0
		} else {
			var _t1133 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1133 = 2
			} else {
				var _t1134 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1134 = 1
				} else {
					_t1134 = -1
				}
				_t1133 = _t1134
			}
			_t1132 = _t1133
		}
		_t1131 = _t1132
	} else {
		_t1131 = -1
	}
	prediction467 := _t1131
	var _t1135 *pb.Data
	if prediction467 == 2 {
		_t1136 := p.parse_csv_data()
		csv_data470 := _t1136
		_t1137 := &pb.Data{}
		_t1137.DataType = &pb.Data_CsvData{CsvData: csv_data470}
		_t1135 = _t1137
	} else {
		var _t1138 *pb.Data
		if prediction467 == 1 {
			_t1139 := p.parse_betree_relation()
			betree_relation469 := _t1139
			_t1140 := &pb.Data{}
			_t1140.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation469}
			_t1138 = _t1140
		} else {
			var _t1141 *pb.Data
			if prediction467 == 0 {
				_t1142 := p.parse_rel_edb()
				rel_edb468 := _t1142
				_t1143 := &pb.Data{}
				_t1143.DataType = &pb.Data_RelEdb{RelEdb: rel_edb468}
				_t1141 = _t1143
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1138 = _t1141
		}
		_t1135 = _t1138
	}
	result472 := _t1135
	p.recordSpan(span_start471)
	return result472
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	span_start476 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	p.pushPath(1)
	_t1144 := p.parse_relation_id()
	relation_id473 := _t1144
	p.popPath()
	p.pushPath(2)
	_t1145 := p.parse_rel_edb_path()
	rel_edb_path474 := _t1145
	p.popPath()
	p.pushPath(3)
	_t1146 := p.parse_rel_edb_types()
	rel_edb_types475 := _t1146
	p.popPath()
	p.consumeLiteral(")")
	_t1147 := &pb.RelEDB{TargetId: relation_id473, Path: rel_edb_path474, Types: rel_edb_types475}
	result477 := _t1147
	p.recordSpan(span_start476)
	return result477
}

func (p *Parser) parse_rel_edb_path() []string {
	span_start483 := p.spanStart()
	p.consumeLiteral("[")
	xs478 := []string{}
	cond479 := p.matchLookaheadTerminal("STRING", 0)
	idx481 := 0
	for cond479 {
		p.pushPath(idx481)
		item480 := p.consumeTerminal("STRING").Value.AsString()
		p.popPath()
		xs478 = append(xs478, item480)
		idx481 = (idx481 + 1)
		cond479 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings482 := xs478
	p.consumeLiteral("]")
	result484 := strings482
	p.recordSpan(span_start483)
	return result484
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	span_start490 := p.spanStart()
	p.consumeLiteral("[")
	xs485 := []*pb.Type{}
	cond486 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx488 := 0
	for cond486 {
		p.pushPath(idx488)
		_t1148 := p.parse_type()
		item487 := _t1148
		p.popPath()
		xs485 = append(xs485, item487)
		idx488 = (idx488 + 1)
		cond486 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types489 := xs485
	p.consumeLiteral("]")
	result491 := types489
	p.recordSpan(span_start490)
	return result491
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start494 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	p.pushPath(1)
	_t1149 := p.parse_relation_id()
	relation_id492 := _t1149
	p.popPath()
	p.pushPath(2)
	_t1150 := p.parse_betree_info()
	betree_info493 := _t1150
	p.popPath()
	p.consumeLiteral(")")
	_t1151 := &pb.BeTreeRelation{Name: relation_id492, RelationInfo: betree_info493}
	result495 := _t1151
	p.recordSpan(span_start494)
	return result495
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start499 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1152 := p.parse_betree_info_key_types()
	betree_info_key_types496 := _t1152
	_t1153 := p.parse_betree_info_value_types()
	betree_info_value_types497 := _t1153
	_t1154 := p.parse_config_dict()
	config_dict498 := _t1154
	p.consumeLiteral(")")
	_t1155 := p.construct_betree_info(betree_info_key_types496, betree_info_value_types497, config_dict498)
	result500 := _t1155
	p.recordSpan(span_start499)
	return result500
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	span_start506 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs501 := []*pb.Type{}
	cond502 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx504 := 0
	for cond502 {
		p.pushPath(idx504)
		_t1156 := p.parse_type()
		item503 := _t1156
		p.popPath()
		xs501 = append(xs501, item503)
		idx504 = (idx504 + 1)
		cond502 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types505 := xs501
	p.consumeLiteral(")")
	result507 := types505
	p.recordSpan(span_start506)
	return result507
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	span_start513 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs508 := []*pb.Type{}
	cond509 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx511 := 0
	for cond509 {
		p.pushPath(idx511)
		_t1157 := p.parse_type()
		item510 := _t1157
		p.popPath()
		xs508 = append(xs508, item510)
		idx511 = (idx511 + 1)
		cond509 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types512 := xs508
	p.consumeLiteral(")")
	result514 := types512
	p.recordSpan(span_start513)
	return result514
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start519 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	p.pushPath(1)
	_t1158 := p.parse_csvlocator()
	csvlocator515 := _t1158
	p.popPath()
	p.pushPath(2)
	_t1159 := p.parse_csv_config()
	csv_config516 := _t1159
	p.popPath()
	p.pushPath(3)
	_t1160 := p.parse_csv_columns()
	csv_columns517 := _t1160
	p.popPath()
	p.pushPath(4)
	_t1161 := p.parse_csv_asof()
	csv_asof518 := _t1161
	p.popPath()
	p.consumeLiteral(")")
	_t1162 := &pb.CSVData{Locator: csvlocator515, Config: csv_config516, Columns: csv_columns517, Asof: csv_asof518}
	result520 := _t1162
	p.recordSpan(span_start519)
	return result520
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start523 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	p.pushPath(1)
	var _t1163 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1164 := p.parse_csv_locator_paths()
		_t1163 = _t1164
	}
	csv_locator_paths521 := _t1163
	p.popPath()
	var _t1165 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1166 := p.parse_csv_locator_inline_data()
		_t1165 = ptr(_t1166)
	}
	csv_locator_inline_data522 := _t1165
	p.consumeLiteral(")")
	_t1167 := csv_locator_paths521
	if csv_locator_paths521 == nil {
		_t1167 = []string{}
	}
	_t1168 := &pb.CSVLocator{Paths: _t1167, InlineData: []byte(deref(csv_locator_inline_data522, ""))}
	result524 := _t1168
	p.recordSpan(span_start523)
	return result524
}

func (p *Parser) parse_csv_locator_paths() []string {
	span_start530 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs525 := []string{}
	cond526 := p.matchLookaheadTerminal("STRING", 0)
	idx528 := 0
	for cond526 {
		p.pushPath(idx528)
		item527 := p.consumeTerminal("STRING").Value.AsString()
		p.popPath()
		xs525 = append(xs525, item527)
		idx528 = (idx528 + 1)
		cond526 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings529 := xs525
	p.consumeLiteral(")")
	result531 := strings529
	p.recordSpan(span_start530)
	return result531
}

func (p *Parser) parse_csv_locator_inline_data() string {
	span_start533 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string532 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	result534 := string532
	p.recordSpan(span_start533)
	return result534
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start536 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1169 := p.parse_config_dict()
	config_dict535 := _t1169
	p.consumeLiteral(")")
	_t1170 := p.construct_csv_config(config_dict535)
	result537 := _t1170
	p.recordSpan(span_start536)
	return result537
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	span_start543 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs538 := []*pb.CSVColumn{}
	cond539 := p.matchLookaheadLiteral("(", 0)
	idx541 := 0
	for cond539 {
		p.pushPath(idx541)
		_t1171 := p.parse_csv_column()
		item540 := _t1171
		p.popPath()
		xs538 = append(xs538, item540)
		idx541 = (idx541 + 1)
		cond539 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns542 := xs538
	p.consumeLiteral(")")
	result544 := csv_columns542
	p.recordSpan(span_start543)
	return result544
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	span_start552 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(1)
	string545 := p.consumeTerminal("STRING").Value.AsString()
	p.popPath()
	p.pushPath(2)
	_t1172 := p.parse_relation_id()
	relation_id546 := _t1172
	p.popPath()
	p.consumeLiteral("[")
	p.pushPath(3)
	xs547 := []*pb.Type{}
	cond548 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	idx550 := 0
	for cond548 {
		p.pushPath(idx550)
		_t1173 := p.parse_type()
		item549 := _t1173
		p.popPath()
		xs547 = append(xs547, item549)
		idx550 = (idx550 + 1)
		cond548 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	p.popPath()
	types551 := xs547
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1174 := &pb.CSVColumn{ColumnName: string545, TargetId: relation_id546, Types: types551}
	result553 := _t1174
	p.recordSpan(span_start552)
	return result553
}

func (p *Parser) parse_csv_asof() string {
	span_start555 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string554 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	result556 := string554
	p.recordSpan(span_start555)
	return result556
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start558 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	p.pushPath(1)
	_t1175 := p.parse_fragment_id()
	fragment_id557 := _t1175
	p.popPath()
	p.consumeLiteral(")")
	_t1176 := &pb.Undefine{FragmentId: fragment_id557}
	result559 := _t1176
	p.recordSpan(span_start558)
	return result559
}

func (p *Parser) parse_context() *pb.Context {
	span_start565 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	p.pushPath(1)
	xs560 := []*pb.RelationId{}
	cond561 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	idx563 := 0
	for cond561 {
		p.pushPath(idx563)
		_t1177 := p.parse_relation_id()
		item562 := _t1177
		p.popPath()
		xs560 = append(xs560, item562)
		idx563 = (idx563 + 1)
		cond561 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	p.popPath()
	relation_ids564 := xs560
	p.consumeLiteral(")")
	_t1178 := &pb.Context{Relations: relation_ids564}
	result566 := _t1178
	p.recordSpan(span_start565)
	return result566
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	span_start572 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs567 := []*pb.Read{}
	cond568 := p.matchLookaheadLiteral("(", 0)
	idx570 := 0
	for cond568 {
		p.pushPath(idx570)
		_t1179 := p.parse_read()
		item569 := _t1179
		p.popPath()
		xs567 = append(xs567, item569)
		idx570 = (idx570 + 1)
		cond568 = p.matchLookaheadLiteral("(", 0)
	}
	reads571 := xs567
	p.consumeLiteral(")")
	result573 := reads571
	p.recordSpan(span_start572)
	return result573
}

func (p *Parser) parse_read() *pb.Read {
	span_start580 := p.spanStart()
	var _t1180 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1181 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1181 = 2
		} else {
			var _t1182 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1182 = 1
			} else {
				var _t1183 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1183 = 4
				} else {
					var _t1184 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1184 = 0
					} else {
						var _t1185 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1185 = 3
						} else {
							_t1185 = -1
						}
						_t1184 = _t1185
					}
					_t1183 = _t1184
				}
				_t1182 = _t1183
			}
			_t1181 = _t1182
		}
		_t1180 = _t1181
	} else {
		_t1180 = -1
	}
	prediction574 := _t1180
	var _t1186 *pb.Read
	if prediction574 == 4 {
		_t1187 := p.parse_export()
		export579 := _t1187
		_t1188 := &pb.Read{}
		_t1188.ReadType = &pb.Read_Export{Export: export579}
		_t1186 = _t1188
	} else {
		var _t1189 *pb.Read
		if prediction574 == 3 {
			_t1190 := p.parse_abort()
			abort578 := _t1190
			_t1191 := &pb.Read{}
			_t1191.ReadType = &pb.Read_Abort{Abort: abort578}
			_t1189 = _t1191
		} else {
			var _t1192 *pb.Read
			if prediction574 == 2 {
				_t1193 := p.parse_what_if()
				what_if577 := _t1193
				_t1194 := &pb.Read{}
				_t1194.ReadType = &pb.Read_WhatIf{WhatIf: what_if577}
				_t1192 = _t1194
			} else {
				var _t1195 *pb.Read
				if prediction574 == 1 {
					_t1196 := p.parse_output()
					output576 := _t1196
					_t1197 := &pb.Read{}
					_t1197.ReadType = &pb.Read_Output{Output: output576}
					_t1195 = _t1197
				} else {
					var _t1198 *pb.Read
					if prediction574 == 0 {
						_t1199 := p.parse_demand()
						demand575 := _t1199
						_t1200 := &pb.Read{}
						_t1200.ReadType = &pb.Read_Demand{Demand: demand575}
						_t1198 = _t1200
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1195 = _t1198
				}
				_t1192 = _t1195
			}
			_t1189 = _t1192
		}
		_t1186 = _t1189
	}
	result581 := _t1186
	p.recordSpan(span_start580)
	return result581
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start583 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	p.pushPath(1)
	_t1201 := p.parse_relation_id()
	relation_id582 := _t1201
	p.popPath()
	p.consumeLiteral(")")
	_t1202 := &pb.Demand{RelationId: relation_id582}
	result584 := _t1202
	p.recordSpan(span_start583)
	return result584
}

func (p *Parser) parse_output() *pb.Output {
	span_start587 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	p.pushPath(1)
	_t1203 := p.parse_name()
	name585 := _t1203
	p.popPath()
	p.pushPath(2)
	_t1204 := p.parse_relation_id()
	relation_id586 := _t1204
	p.popPath()
	p.consumeLiteral(")")
	_t1205 := &pb.Output{Name: name585, RelationId: relation_id586}
	result588 := _t1205
	p.recordSpan(span_start587)
	return result588
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start591 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	p.pushPath(1)
	_t1206 := p.parse_name()
	name589 := _t1206
	p.popPath()
	p.pushPath(2)
	_t1207 := p.parse_epoch()
	epoch590 := _t1207
	p.popPath()
	p.consumeLiteral(")")
	_t1208 := &pb.WhatIf{Branch: name589, Epoch: epoch590}
	result592 := _t1208
	p.recordSpan(span_start591)
	return result592
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start595 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	p.pushPath(1)
	var _t1209 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1210 := p.parse_name()
		_t1209 = ptr(_t1210)
	}
	name593 := _t1209
	p.popPath()
	p.pushPath(2)
	_t1211 := p.parse_relation_id()
	relation_id594 := _t1211
	p.popPath()
	p.consumeLiteral(")")
	_t1212 := &pb.Abort{Name: deref(name593, "abort"), RelationId: relation_id594}
	result596 := _t1212
	p.recordSpan(span_start595)
	return result596
}

func (p *Parser) parse_export() *pb.Export {
	span_start598 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	p.pushPath(1)
	_t1213 := p.parse_export_csv_config()
	export_csv_config597 := _t1213
	p.popPath()
	p.consumeLiteral(")")
	_t1214 := &pb.Export{}
	_t1214.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config597}
	result599 := _t1214
	p.recordSpan(span_start598)
	return result599
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start603 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1215 := p.parse_export_csv_path()
	export_csv_path600 := _t1215
	_t1216 := p.parse_export_csv_columns()
	export_csv_columns601 := _t1216
	_t1217 := p.parse_config_dict()
	config_dict602 := _t1217
	p.consumeLiteral(")")
	_t1218 := p.export_csv_config(export_csv_path600, export_csv_columns601, config_dict602)
	result604 := _t1218
	p.recordSpan(span_start603)
	return result604
}

func (p *Parser) parse_export_csv_path() string {
	span_start606 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string605 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	result607 := string605
	p.recordSpan(span_start606)
	return result607
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	span_start613 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs608 := []*pb.ExportCSVColumn{}
	cond609 := p.matchLookaheadLiteral("(", 0)
	idx611 := 0
	for cond609 {
		p.pushPath(idx611)
		_t1219 := p.parse_export_csv_column()
		item610 := _t1219
		p.popPath()
		xs608 = append(xs608, item610)
		idx611 = (idx611 + 1)
		cond609 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns612 := xs608
	p.consumeLiteral(")")
	result614 := export_csv_columns612
	p.recordSpan(span_start613)
	return result614
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start617 := p.spanStart()
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	p.pushPath(1)
	string615 := p.consumeTerminal("STRING").Value.AsString()
	p.popPath()
	p.pushPath(2)
	_t1220 := p.parse_relation_id()
	relation_id616 := _t1220
	p.popPath()
	p.consumeLiteral(")")
	_t1221 := &pb.ExportCSVColumn{ColumnName: string615, ColumnData: relation_id616}
	result618 := _t1221
	p.recordSpan(span_start617)
	return result618
}


// Parse parses the input string and returns the result and provenance map
func Parse(input string) (*pb.Transaction, map[string]Span, error) {
	defer func() {
		if r := recover(); r != nil {
			if pe, ok := r.(ParseError); ok {
				panic(pe)
			}
			panic(r)
		}
	}()

	lexer := NewLexer(input)
	parser := NewParser(lexer.tokens, input)
	result := parser.parse_transaction()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, parser.Provenance, nil
}
