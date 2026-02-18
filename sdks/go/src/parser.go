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
	Type  string
	Value TokenValue
	Pos   int
}

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, %v, %d)", t.Type, t.Value, t.Pos)
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
			Type:  best.tokenType,
			Value: best.action(best.value),
			Pos:   l.pos,
		})
		l.pos = best.endPos
	}

	l.tokens = append(l.tokens, Token{Type: "$", Value: stringTokenValue(""), Pos: l.pos})
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
}

// NewParser creates a new parser
func NewParser(tokens []Token) *Parser {
	return &Parser{
		tokens:            tokens,
		pos:               0,
		idToDebugInfo:     make(map[string]map[relationIdKey]string),
		currentFragmentID: nil,
	}
}

func (p *Parser) lookahead(k int) Token {
	idx := p.pos + k
	if idx < len(p.tokens) {
		return p.tokens[idx]
	}
	return Token{Type: "$", Value: stringTokenValue(""), Pos: -1}
}

func (p *Parser) consumeLiteral(expected string) {
	if !p.matchLookaheadLiteral(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected literal %q but got %s=`%v` at position %d", expected, token.Type, token.Value, token.Pos)})
	}
	p.pos++
}

func (p *Parser) consumeTerminal(expected string) Token {
	if !p.matchLookaheadTerminal(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected terminal %s but got %s=`%v` at position %d", expected, token.Type, token.Value, token.Pos)})
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
	var _t1866 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1866
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1867 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1867
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1868 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1868
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1869 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1869
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1870 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1870
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1871 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1871
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1872 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1872
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1873 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1873
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1874 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1874
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1875 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1875
	_t1876 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1876
	_t1877 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1877
	_t1878 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1878
	_t1879 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1879
	_t1880 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1880
	_t1881 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1881
	_t1882 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1882
	_t1883 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1883
	_t1884 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1884
	_t1885 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1885
	_t1886 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1886
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1887 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1887
	_t1888 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1888
	_t1889 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1889
	_t1890 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1890
	_t1891 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1891
	_t1892 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1892
	_t1893 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1893
	_t1894 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1894
	_t1895 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1895
	_t1896 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1896.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1896.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1896
	_t1897 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1897
}

func (p *Parser) default_configure() *pb.Configure {
	_t1898 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1898
	_t1899 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1899
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
	_t1900 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1900
	_t1901 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1901
	_t1902 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1902
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1903 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1903
	_t1904 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1904
	_t1905 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1905
	_t1906 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1906
	_t1907 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1907
	_t1908 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1908
	_t1909 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1909
	_t1910 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1910
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1263 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1264 := p.parse_configure()
		_t1263 = _t1264
	}
	configure910 := _t1263
	var _t1265 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1266 := p.parse_sync()
		_t1265 = _t1266
	}
	sync911 := _t1265
	xs912 := []*pb.Epoch{}
	cond913 := p.matchLookaheadLiteral("(", 0)
	for cond913 {
		_t1267 := p.parse_epoch()
		item914 := _t1267
		xs912 = append(xs912, item914)
		cond913 = p.matchLookaheadLiteral("(", 0)
	}
	epochs915 := xs912
	p.consumeLiteral(")")
	_t1268 := p.default_configure()
	_t1269 := configure910
	if configure910 == nil {
		_t1269 = _t1268
	}
	_t1270 := &pb.Transaction{Epochs: epochs915, Configure: _t1269, Sync: sync911}
	return _t1270
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1271 := p.parse_config_dict()
	config_dict916 := _t1271
	p.consumeLiteral(")")
	_t1272 := p.construct_configure(config_dict916)
	return _t1272
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs917 := [][]interface{}{}
	cond918 := p.matchLookaheadLiteral(":", 0)
	for cond918 {
		_t1273 := p.parse_config_key_value()
		item919 := _t1273
		xs917 = append(xs917, item919)
		cond918 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values920 := xs917
	p.consumeLiteral("}")
	return config_key_values920
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol921 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t1274 := p.parse_value()
	value922 := _t1274
	return []interface{}{symbol921, value922}
}

func (p *Parser) parse_value() *pb.Value {
	var _t1275 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1275 = 9
	} else {
		var _t1276 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1276 = 8
		} else {
			var _t1277 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1277 = 9
			} else {
				var _t1278 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1279 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1279 = 1
					} else {
						var _t1280 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1280 = 0
						} else {
							_t1280 = -1
						}
						_t1279 = _t1280
					}
					_t1278 = _t1279
				} else {
					var _t1281 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1281 = 5
					} else {
						var _t1282 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1282 = 2
						} else {
							var _t1283 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1283 = 6
							} else {
								var _t1284 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1284 = 3
								} else {
									var _t1285 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1285 = 4
									} else {
										var _t1286 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1286 = 7
										} else {
											_t1286 = -1
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
					_t1278 = _t1281
				}
				_t1277 = _t1278
			}
			_t1276 = _t1277
		}
		_t1275 = _t1276
	}
	prediction923 := _t1275
	var _t1287 *pb.Value
	if prediction923 == 9 {
		_t1288 := p.parse_boolean_value()
		boolean_value932 := _t1288
		_t1289 := &pb.Value{}
		_t1289.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value932}
		_t1287 = _t1289
	} else {
		var _t1290 *pb.Value
		if prediction923 == 8 {
			p.consumeLiteral("missing")
			_t1291 := &pb.MissingValue{}
			_t1292 := &pb.Value{}
			_t1292.Value = &pb.Value_MissingValue{MissingValue: _t1291}
			_t1290 = _t1292
		} else {
			var _t1293 *pb.Value
			if prediction923 == 7 {
				decimal931 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t1294 := &pb.Value{}
				_t1294.Value = &pb.Value_DecimalValue{DecimalValue: decimal931}
				_t1293 = _t1294
			} else {
				var _t1295 *pb.Value
				if prediction923 == 6 {
					int128930 := p.consumeTerminal("INT128").Value.AsInt128()
					_t1296 := &pb.Value{}
					_t1296.Value = &pb.Value_Int128Value{Int128Value: int128930}
					_t1295 = _t1296
				} else {
					var _t1297 *pb.Value
					if prediction923 == 5 {
						uint128929 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t1298 := &pb.Value{}
						_t1298.Value = &pb.Value_Uint128Value{Uint128Value: uint128929}
						_t1297 = _t1298
					} else {
						var _t1299 *pb.Value
						if prediction923 == 4 {
							float928 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t1300 := &pb.Value{}
							_t1300.Value = &pb.Value_FloatValue{FloatValue: float928}
							_t1299 = _t1300
						} else {
							var _t1301 *pb.Value
							if prediction923 == 3 {
								int927 := p.consumeTerminal("INT").Value.AsInt64()
								_t1302 := &pb.Value{}
								_t1302.Value = &pb.Value_IntValue{IntValue: int927}
								_t1301 = _t1302
							} else {
								var _t1303 *pb.Value
								if prediction923 == 2 {
									string926 := p.consumeTerminal("STRING").Value.AsString()
									_t1304 := &pb.Value{}
									_t1304.Value = &pb.Value_StringValue{StringValue: string926}
									_t1303 = _t1304
								} else {
									var _t1305 *pb.Value
									if prediction923 == 1 {
										_t1306 := p.parse_datetime()
										datetime925 := _t1306
										_t1307 := &pb.Value{}
										_t1307.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime925}
										_t1305 = _t1307
									} else {
										var _t1308 *pb.Value
										if prediction923 == 0 {
											_t1309 := p.parse_date()
											date924 := _t1309
											_t1310 := &pb.Value{}
											_t1310.Value = &pb.Value_DateValue{DateValue: date924}
											_t1308 = _t1310
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1305 = _t1308
									}
									_t1303 = _t1305
								}
								_t1301 = _t1303
							}
							_t1299 = _t1301
						}
						_t1297 = _t1299
					}
					_t1295 = _t1297
				}
				_t1293 = _t1295
			}
			_t1290 = _t1293
		}
		_t1287 = _t1290
	}
	return _t1287
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int933 := p.consumeTerminal("INT").Value.AsInt64()
	int_3934 := p.consumeTerminal("INT").Value.AsInt64()
	int_4935 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t1311 := &pb.DateValue{Year: int32(int933), Month: int32(int_3934), Day: int32(int_4935)}
	return _t1311
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int936 := p.consumeTerminal("INT").Value.AsInt64()
	int_3937 := p.consumeTerminal("INT").Value.AsInt64()
	int_4938 := p.consumeTerminal("INT").Value.AsInt64()
	int_5939 := p.consumeTerminal("INT").Value.AsInt64()
	int_6940 := p.consumeTerminal("INT").Value.AsInt64()
	int_7941 := p.consumeTerminal("INT").Value.AsInt64()
	var _t1312 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1312 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_8942 := _t1312
	p.consumeLiteral(")")
	_t1313 := &pb.DateTimeValue{Year: int32(int936), Month: int32(int_3937), Day: int32(int_4938), Hour: int32(int_5939), Minute: int32(int_6940), Second: int32(int_7941), Microsecond: int32(deref(int_8942, 0))}
	return _t1313
}

func (p *Parser) parse_boolean_value() bool {
	var _t1314 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1314 = 0
	} else {
		var _t1315 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1315 = 1
		} else {
			_t1315 = -1
		}
		_t1314 = _t1315
	}
	prediction943 := _t1314
	var _t1316 bool
	if prediction943 == 1 {
		p.consumeLiteral("false")
		_t1316 = false
	} else {
		var _t1317 bool
		if prediction943 == 0 {
			p.consumeLiteral("true")
			_t1317 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1316 = _t1317
	}
	return _t1316
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs944 := []*pb.FragmentId{}
	cond945 := p.matchLookaheadLiteral(":", 0)
	for cond945 {
		_t1318 := p.parse_fragment_id()
		item946 := _t1318
		xs944 = append(xs944, item946)
		cond945 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids947 := xs944
	p.consumeLiteral(")")
	_t1319 := &pb.Sync{Fragments: fragment_ids947}
	return _t1319
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol948 := p.consumeTerminal("SYMBOL").Value.AsString()
	return &pb.FragmentId{Id: []byte(symbol948)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1320 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1321 := p.parse_epoch_writes()
		_t1320 = _t1321
	}
	epoch_writes949 := _t1320
	var _t1322 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1323 := p.parse_epoch_reads()
		_t1322 = _t1323
	}
	epoch_reads950 := _t1322
	p.consumeLiteral(")")
	_t1324 := epoch_writes949
	if epoch_writes949 == nil {
		_t1324 = []*pb.Write{}
	}
	_t1325 := epoch_reads950
	if epoch_reads950 == nil {
		_t1325 = []*pb.Read{}
	}
	_t1326 := &pb.Epoch{Writes: _t1324, Reads: _t1325}
	return _t1326
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs951 := []*pb.Write{}
	cond952 := p.matchLookaheadLiteral("(", 0)
	for cond952 {
		_t1327 := p.parse_write()
		item953 := _t1327
		xs951 = append(xs951, item953)
		cond952 = p.matchLookaheadLiteral("(", 0)
	}
	writes954 := xs951
	p.consumeLiteral(")")
	return writes954
}

func (p *Parser) parse_write() *pb.Write {
	var _t1328 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1329 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1329 = 1
		} else {
			var _t1330 int64
			if p.matchLookaheadLiteral("define", 1) {
				_t1330 = 0
			} else {
				var _t1331 int64
				if p.matchLookaheadLiteral("context", 1) {
					_t1331 = 2
				} else {
					_t1331 = -1
				}
				_t1330 = _t1331
			}
			_t1329 = _t1330
		}
		_t1328 = _t1329
	} else {
		_t1328 = -1
	}
	prediction955 := _t1328
	var _t1332 *pb.Write
	if prediction955 == 2 {
		_t1333 := p.parse_context()
		context958 := _t1333
		_t1334 := &pb.Write{}
		_t1334.WriteType = &pb.Write_Context{Context: context958}
		_t1332 = _t1334
	} else {
		var _t1335 *pb.Write
		if prediction955 == 1 {
			_t1336 := p.parse_undefine()
			undefine957 := _t1336
			_t1337 := &pb.Write{}
			_t1337.WriteType = &pb.Write_Undefine{Undefine: undefine957}
			_t1335 = _t1337
		} else {
			var _t1338 *pb.Write
			if prediction955 == 0 {
				_t1339 := p.parse_define()
				define956 := _t1339
				_t1340 := &pb.Write{}
				_t1340.WriteType = &pb.Write_Define{Define: define956}
				_t1338 = _t1340
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1335 = _t1338
		}
		_t1332 = _t1335
	}
	return _t1332
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1341 := p.parse_fragment()
	fragment959 := _t1341
	p.consumeLiteral(")")
	_t1342 := &pb.Define{Fragment: fragment959}
	return _t1342
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1343 := p.parse_new_fragment_id()
	new_fragment_id960 := _t1343
	xs961 := []*pb.Declaration{}
	cond962 := p.matchLookaheadLiteral("(", 0)
	for cond962 {
		_t1344 := p.parse_declaration()
		item963 := _t1344
		xs961 = append(xs961, item963)
		cond962 = p.matchLookaheadLiteral("(", 0)
	}
	declarations964 := xs961
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id960, declarations964)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t1345 := p.parse_fragment_id()
	fragment_id965 := _t1345
	p.startFragment(fragment_id965)
	return fragment_id965
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t1346 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1347 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1347 = 3
		} else {
			var _t1348 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1348 = 2
			} else {
				var _t1349 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1349 = 0
				} else {
					var _t1350 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1350 = 3
					} else {
						var _t1351 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1351 = 3
						} else {
							var _t1352 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1352 = 1
							} else {
								_t1352 = -1
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
	prediction966 := _t1346
	var _t1353 *pb.Declaration
	if prediction966 == 3 {
		_t1354 := p.parse_data()
		data970 := _t1354
		_t1355 := &pb.Declaration{}
		_t1355.DeclarationType = &pb.Declaration_Data{Data: data970}
		_t1353 = _t1355
	} else {
		var _t1356 *pb.Declaration
		if prediction966 == 2 {
			_t1357 := p.parse_constraint()
			constraint969 := _t1357
			_t1358 := &pb.Declaration{}
			_t1358.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint969}
			_t1356 = _t1358
		} else {
			var _t1359 *pb.Declaration
			if prediction966 == 1 {
				_t1360 := p.parse_algorithm()
				algorithm968 := _t1360
				_t1361 := &pb.Declaration{}
				_t1361.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm968}
				_t1359 = _t1361
			} else {
				var _t1362 *pb.Declaration
				if prediction966 == 0 {
					_t1363 := p.parse_def()
					def967 := _t1363
					_t1364 := &pb.Declaration{}
					_t1364.DeclarationType = &pb.Declaration_Def{Def: def967}
					_t1362 = _t1364
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1359 = _t1362
			}
			_t1356 = _t1359
		}
		_t1353 = _t1356
	}
	return _t1353
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1365 := p.parse_relation_id()
	relation_id971 := _t1365
	_t1366 := p.parse_abstraction()
	abstraction972 := _t1366
	var _t1367 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1368 := p.parse_attrs()
		_t1367 = _t1368
	}
	attrs973 := _t1367
	p.consumeLiteral(")")
	_t1369 := attrs973
	if attrs973 == nil {
		_t1369 = []*pb.Attribute{}
	}
	_t1370 := &pb.Def{Name: relation_id971, Body: abstraction972, Attrs: _t1369}
	return _t1370
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t1371 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1371 = 0
	} else {
		var _t1372 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1372 = 1
		} else {
			_t1372 = -1
		}
		_t1371 = _t1372
	}
	prediction974 := _t1371
	var _t1373 *pb.RelationId
	if prediction974 == 1 {
		uint128976 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t1373 = &pb.RelationId{IdLow: uint128976.Low, IdHigh: uint128976.High}
	} else {
		var _t1374 *pb.RelationId
		if prediction974 == 0 {
			p.consumeLiteral(":")
			symbol975 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t1374 = p.relationIdFromString(symbol975)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1373 = _t1374
	}
	return _t1373
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t1375 := p.parse_bindings()
	bindings977 := _t1375
	_t1376 := p.parse_formula()
	formula978 := _t1376
	p.consumeLiteral(")")
	_t1377 := &pb.Abstraction{Vars: listConcat(bindings977[0].([]*pb.Binding), bindings977[1].([]*pb.Binding)), Value: formula978}
	return _t1377
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs979 := []*pb.Binding{}
	cond980 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond980 {
		_t1378 := p.parse_binding()
		item981 := _t1378
		xs979 = append(xs979, item981)
		cond980 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings982 := xs979
	var _t1379 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1380 := p.parse_value_bindings()
		_t1379 = _t1380
	}
	value_bindings983 := _t1379
	p.consumeLiteral("]")
	_t1381 := value_bindings983
	if value_bindings983 == nil {
		_t1381 = []*pb.Binding{}
	}
	return []interface{}{bindings982, _t1381}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol984 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	_t1382 := p.parse_type()
	type985 := _t1382
	_t1383 := &pb.Var{Name: symbol984}
	_t1384 := &pb.Binding{Var: _t1383, Type: type985}
	return _t1384
}

func (p *Parser) parse_type() *pb.Type {
	var _t1385 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1385 = 0
	} else {
		var _t1386 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1386 = 4
		} else {
			var _t1387 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1387 = 1
			} else {
				var _t1388 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1388 = 8
				} else {
					var _t1389 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1389 = 5
					} else {
						var _t1390 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1390 = 2
						} else {
							var _t1391 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1391 = 3
							} else {
								var _t1392 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1392 = 7
								} else {
									var _t1393 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1393 = 6
									} else {
										var _t1394 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1394 = 10
										} else {
											var _t1395 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1395 = 9
											} else {
												_t1395 = -1
											}
											_t1394 = _t1395
										}
										_t1393 = _t1394
									}
									_t1392 = _t1393
								}
								_t1391 = _t1392
							}
							_t1390 = _t1391
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
	prediction986 := _t1385
	var _t1396 *pb.Type
	if prediction986 == 10 {
		_t1397 := p.parse_boolean_type()
		boolean_type997 := _t1397
		_t1398 := &pb.Type{}
		_t1398.Type = &pb.Type_BooleanType{BooleanType: boolean_type997}
		_t1396 = _t1398
	} else {
		var _t1399 *pb.Type
		if prediction986 == 9 {
			_t1400 := p.parse_decimal_type()
			decimal_type996 := _t1400
			_t1401 := &pb.Type{}
			_t1401.Type = &pb.Type_DecimalType{DecimalType: decimal_type996}
			_t1399 = _t1401
		} else {
			var _t1402 *pb.Type
			if prediction986 == 8 {
				_t1403 := p.parse_missing_type()
				missing_type995 := _t1403
				_t1404 := &pb.Type{}
				_t1404.Type = &pb.Type_MissingType{MissingType: missing_type995}
				_t1402 = _t1404
			} else {
				var _t1405 *pb.Type
				if prediction986 == 7 {
					_t1406 := p.parse_datetime_type()
					datetime_type994 := _t1406
					_t1407 := &pb.Type{}
					_t1407.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type994}
					_t1405 = _t1407
				} else {
					var _t1408 *pb.Type
					if prediction986 == 6 {
						_t1409 := p.parse_date_type()
						date_type993 := _t1409
						_t1410 := &pb.Type{}
						_t1410.Type = &pb.Type_DateType{DateType: date_type993}
						_t1408 = _t1410
					} else {
						var _t1411 *pb.Type
						if prediction986 == 5 {
							_t1412 := p.parse_int128_type()
							int128_type992 := _t1412
							_t1413 := &pb.Type{}
							_t1413.Type = &pb.Type_Int128Type{Int128Type: int128_type992}
							_t1411 = _t1413
						} else {
							var _t1414 *pb.Type
							if prediction986 == 4 {
								_t1415 := p.parse_uint128_type()
								uint128_type991 := _t1415
								_t1416 := &pb.Type{}
								_t1416.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type991}
								_t1414 = _t1416
							} else {
								var _t1417 *pb.Type
								if prediction986 == 3 {
									_t1418 := p.parse_float_type()
									float_type990 := _t1418
									_t1419 := &pb.Type{}
									_t1419.Type = &pb.Type_FloatType{FloatType: float_type990}
									_t1417 = _t1419
								} else {
									var _t1420 *pb.Type
									if prediction986 == 2 {
										_t1421 := p.parse_int_type()
										int_type989 := _t1421
										_t1422 := &pb.Type{}
										_t1422.Type = &pb.Type_IntType{IntType: int_type989}
										_t1420 = _t1422
									} else {
										var _t1423 *pb.Type
										if prediction986 == 1 {
											_t1424 := p.parse_string_type()
											string_type988 := _t1424
											_t1425 := &pb.Type{}
											_t1425.Type = &pb.Type_StringType{StringType: string_type988}
											_t1423 = _t1425
										} else {
											var _t1426 *pb.Type
											if prediction986 == 0 {
												_t1427 := p.parse_unspecified_type()
												unspecified_type987 := _t1427
												_t1428 := &pb.Type{}
												_t1428.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type987}
												_t1426 = _t1428
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t1423 = _t1426
										}
										_t1420 = _t1423
									}
									_t1417 = _t1420
								}
								_t1414 = _t1417
							}
							_t1411 = _t1414
						}
						_t1408 = _t1411
					}
					_t1405 = _t1408
				}
				_t1402 = _t1405
			}
			_t1399 = _t1402
		}
		_t1396 = _t1399
	}
	return _t1396
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t1429 := &pb.UnspecifiedType{}
	return _t1429
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t1430 := &pb.StringType{}
	return _t1430
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t1431 := &pb.IntType{}
	return _t1431
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t1432 := &pb.FloatType{}
	return _t1432
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t1433 := &pb.UInt128Type{}
	return _t1433
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t1434 := &pb.Int128Type{}
	return _t1434
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t1435 := &pb.DateType{}
	return _t1435
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t1436 := &pb.DateTimeType{}
	return _t1436
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t1437 := &pb.MissingType{}
	return _t1437
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int998 := p.consumeTerminal("INT").Value.AsInt64()
	int_3999 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t1438 := &pb.DecimalType{Precision: int32(int998), Scale: int32(int_3999)}
	return _t1438
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t1439 := &pb.BooleanType{}
	return _t1439
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs1000 := []*pb.Binding{}
	cond1001 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1001 {
		_t1440 := p.parse_binding()
		item1002 := _t1440
		xs1000 = append(xs1000, item1002)
		cond1001 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings1003 := xs1000
	return bindings1003
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t1441 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1442 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1442 = 0
		} else {
			var _t1443 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1443 = 11
			} else {
				var _t1444 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1444 = 3
				} else {
					var _t1445 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1445 = 10
					} else {
						var _t1446 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1446 = 9
						} else {
							var _t1447 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1447 = 5
							} else {
								var _t1448 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1448 = 6
								} else {
									var _t1449 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1449 = 7
									} else {
										var _t1450 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1450 = 1
										} else {
											var _t1451 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1451 = 2
											} else {
												var _t1452 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1452 = 12
												} else {
													var _t1453 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1453 = 8
													} else {
														var _t1454 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1454 = 4
														} else {
															var _t1455 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1455 = 10
															} else {
																var _t1456 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1456 = 10
																} else {
																	var _t1457 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1457 = 10
																	} else {
																		var _t1458 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1458 = 10
																		} else {
																			var _t1459 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1459 = 10
																			} else {
																				var _t1460 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1460 = 10
																				} else {
																					var _t1461 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1461 = 10
																					} else {
																						var _t1462 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1462 = 10
																						} else {
																							var _t1463 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1463 = 10
																							} else {
																								_t1463 = -1
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
	} else {
		_t1441 = -1
	}
	prediction1004 := _t1441
	var _t1464 *pb.Formula
	if prediction1004 == 12 {
		_t1465 := p.parse_cast()
		cast1017 := _t1465
		_t1466 := &pb.Formula{}
		_t1466.FormulaType = &pb.Formula_Cast{Cast: cast1017}
		_t1464 = _t1466
	} else {
		var _t1467 *pb.Formula
		if prediction1004 == 11 {
			_t1468 := p.parse_rel_atom()
			rel_atom1016 := _t1468
			_t1469 := &pb.Formula{}
			_t1469.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom1016}
			_t1467 = _t1469
		} else {
			var _t1470 *pb.Formula
			if prediction1004 == 10 {
				_t1471 := p.parse_primitive()
				primitive1015 := _t1471
				_t1472 := &pb.Formula{}
				_t1472.FormulaType = &pb.Formula_Primitive{Primitive: primitive1015}
				_t1470 = _t1472
			} else {
				var _t1473 *pb.Formula
				if prediction1004 == 9 {
					_t1474 := p.parse_pragma()
					pragma1014 := _t1474
					_t1475 := &pb.Formula{}
					_t1475.FormulaType = &pb.Formula_Pragma{Pragma: pragma1014}
					_t1473 = _t1475
				} else {
					var _t1476 *pb.Formula
					if prediction1004 == 8 {
						_t1477 := p.parse_atom()
						atom1013 := _t1477
						_t1478 := &pb.Formula{}
						_t1478.FormulaType = &pb.Formula_Atom{Atom: atom1013}
						_t1476 = _t1478
					} else {
						var _t1479 *pb.Formula
						if prediction1004 == 7 {
							_t1480 := p.parse_ffi()
							ffi1012 := _t1480
							_t1481 := &pb.Formula{}
							_t1481.FormulaType = &pb.Formula_Ffi{Ffi: ffi1012}
							_t1479 = _t1481
						} else {
							var _t1482 *pb.Formula
							if prediction1004 == 6 {
								_t1483 := p.parse_not()
								not1011 := _t1483
								_t1484 := &pb.Formula{}
								_t1484.FormulaType = &pb.Formula_Not{Not: not1011}
								_t1482 = _t1484
							} else {
								var _t1485 *pb.Formula
								if prediction1004 == 5 {
									_t1486 := p.parse_disjunction()
									disjunction1010 := _t1486
									_t1487 := &pb.Formula{}
									_t1487.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction1010}
									_t1485 = _t1487
								} else {
									var _t1488 *pb.Formula
									if prediction1004 == 4 {
										_t1489 := p.parse_conjunction()
										conjunction1009 := _t1489
										_t1490 := &pb.Formula{}
										_t1490.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction1009}
										_t1488 = _t1490
									} else {
										var _t1491 *pb.Formula
										if prediction1004 == 3 {
											_t1492 := p.parse_reduce()
											reduce1008 := _t1492
											_t1493 := &pb.Formula{}
											_t1493.FormulaType = &pb.Formula_Reduce{Reduce: reduce1008}
											_t1491 = _t1493
										} else {
											var _t1494 *pb.Formula
											if prediction1004 == 2 {
												_t1495 := p.parse_exists()
												exists1007 := _t1495
												_t1496 := &pb.Formula{}
												_t1496.FormulaType = &pb.Formula_Exists{Exists: exists1007}
												_t1494 = _t1496
											} else {
												var _t1497 *pb.Formula
												if prediction1004 == 1 {
													_t1498 := p.parse_false()
													false1006 := _t1498
													_t1499 := &pb.Formula{}
													_t1499.FormulaType = &pb.Formula_Disjunction{Disjunction: false1006}
													_t1497 = _t1499
												} else {
													var _t1500 *pb.Formula
													if prediction1004 == 0 {
														_t1501 := p.parse_true()
														true1005 := _t1501
														_t1502 := &pb.Formula{}
														_t1502.FormulaType = &pb.Formula_Conjunction{Conjunction: true1005}
														_t1500 = _t1502
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
			_t1467 = _t1470
		}
		_t1464 = _t1467
	}
	return _t1464
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1503 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t1503
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1504 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t1504
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1505 := p.parse_bindings()
	bindings1018 := _t1505
	_t1506 := p.parse_formula()
	formula1019 := _t1506
	p.consumeLiteral(")")
	_t1507 := &pb.Abstraction{Vars: listConcat(bindings1018[0].([]*pb.Binding), bindings1018[1].([]*pb.Binding)), Value: formula1019}
	_t1508 := &pb.Exists{Body: _t1507}
	return _t1508
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1509 := p.parse_abstraction()
	abstraction1020 := _t1509
	_t1510 := p.parse_abstraction()
	abstraction_31021 := _t1510
	_t1511 := p.parse_terms()
	terms1022 := _t1511
	p.consumeLiteral(")")
	_t1512 := &pb.Reduce{Op: abstraction1020, Body: abstraction_31021, Terms: terms1022}
	return _t1512
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs1023 := []*pb.Term{}
	cond1024 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1024 {
		_t1513 := p.parse_term()
		item1025 := _t1513
		xs1023 = append(xs1023, item1025)
		cond1024 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms1026 := xs1023
	p.consumeLiteral(")")
	return terms1026
}

func (p *Parser) parse_term() *pb.Term {
	var _t1514 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1514 = 1
	} else {
		var _t1515 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1515 = 1
		} else {
			var _t1516 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1516 = 1
			} else {
				var _t1517 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1517 = 1
				} else {
					var _t1518 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1518 = 1
					} else {
						var _t1519 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1519 = 0
						} else {
							var _t1520 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1520 = 1
							} else {
								var _t1521 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1521 = 1
								} else {
									var _t1522 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1522 = 1
									} else {
										var _t1523 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1523 = 1
										} else {
											var _t1524 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1524 = 1
											} else {
												_t1524 = -1
											}
											_t1523 = _t1524
										}
										_t1522 = _t1523
									}
									_t1521 = _t1522
								}
								_t1520 = _t1521
							}
							_t1519 = _t1520
						}
						_t1518 = _t1519
					}
					_t1517 = _t1518
				}
				_t1516 = _t1517
			}
			_t1515 = _t1516
		}
		_t1514 = _t1515
	}
	prediction1027 := _t1514
	var _t1525 *pb.Term
	if prediction1027 == 1 {
		_t1526 := p.parse_constant()
		constant1029 := _t1526
		_t1527 := &pb.Term{}
		_t1527.TermType = &pb.Term_Constant{Constant: constant1029}
		_t1525 = _t1527
	} else {
		var _t1528 *pb.Term
		if prediction1027 == 0 {
			_t1529 := p.parse_var()
			var1028 := _t1529
			_t1530 := &pb.Term{}
			_t1530.TermType = &pb.Term_Var{Var: var1028}
			_t1528 = _t1530
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1525 = _t1528
	}
	return _t1525
}

func (p *Parser) parse_var() *pb.Var {
	symbol1030 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t1531 := &pb.Var{Name: symbol1030}
	return _t1531
}

func (p *Parser) parse_constant() *pb.Value {
	_t1532 := p.parse_value()
	value1031 := _t1532
	return value1031
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs1032 := []*pb.Formula{}
	cond1033 := p.matchLookaheadLiteral("(", 0)
	for cond1033 {
		_t1533 := p.parse_formula()
		item1034 := _t1533
		xs1032 = append(xs1032, item1034)
		cond1033 = p.matchLookaheadLiteral("(", 0)
	}
	formulas1035 := xs1032
	p.consumeLiteral(")")
	_t1534 := &pb.Conjunction{Args: formulas1035}
	return _t1534
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs1036 := []*pb.Formula{}
	cond1037 := p.matchLookaheadLiteral("(", 0)
	for cond1037 {
		_t1535 := p.parse_formula()
		item1038 := _t1535
		xs1036 = append(xs1036, item1038)
		cond1037 = p.matchLookaheadLiteral("(", 0)
	}
	formulas1039 := xs1036
	p.consumeLiteral(")")
	_t1536 := &pb.Disjunction{Args: formulas1039}
	return _t1536
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1537 := p.parse_formula()
	formula1040 := _t1537
	p.consumeLiteral(")")
	_t1538 := &pb.Not{Arg: formula1040}
	return _t1538
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1539 := p.parse_name()
	name1041 := _t1539
	_t1540 := p.parse_ffi_args()
	ffi_args1042 := _t1540
	_t1541 := p.parse_terms()
	terms1043 := _t1541
	p.consumeLiteral(")")
	_t1542 := &pb.FFI{Name: name1041, Args: ffi_args1042, Terms: terms1043}
	return _t1542
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol1044 := p.consumeTerminal("SYMBOL").Value.AsString()
	return symbol1044
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs1045 := []*pb.Abstraction{}
	cond1046 := p.matchLookaheadLiteral("(", 0)
	for cond1046 {
		_t1543 := p.parse_abstraction()
		item1047 := _t1543
		xs1045 = append(xs1045, item1047)
		cond1046 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions1048 := xs1045
	p.consumeLiteral(")")
	return abstractions1048
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1544 := p.parse_relation_id()
	relation_id1049 := _t1544
	xs1050 := []*pb.Term{}
	cond1051 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1051 {
		_t1545 := p.parse_term()
		item1052 := _t1545
		xs1050 = append(xs1050, item1052)
		cond1051 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms1053 := xs1050
	p.consumeLiteral(")")
	_t1546 := &pb.Atom{Name: relation_id1049, Terms: terms1053}
	return _t1546
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1547 := p.parse_name()
	name1054 := _t1547
	xs1055 := []*pb.Term{}
	cond1056 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1056 {
		_t1548 := p.parse_term()
		item1057 := _t1548
		xs1055 = append(xs1055, item1057)
		cond1056 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms1058 := xs1055
	p.consumeLiteral(")")
	_t1549 := &pb.Pragma{Name: name1054, Terms: terms1058}
	return _t1549
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1550 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1551 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1551 = 9
		} else {
			var _t1552 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1552 = 4
			} else {
				var _t1553 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1553 = 3
				} else {
					var _t1554 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1554 = 0
					} else {
						var _t1555 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1555 = 2
						} else {
							var _t1556 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1556 = 1
							} else {
								var _t1557 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1557 = 8
								} else {
									var _t1558 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1558 = 6
									} else {
										var _t1559 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1559 = 5
										} else {
											var _t1560 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1560 = 7
											} else {
												_t1560 = -1
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
		}
		_t1550 = _t1551
	} else {
		_t1550 = -1
	}
	prediction1059 := _t1550
	var _t1561 *pb.Primitive
	if prediction1059 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1562 := p.parse_name()
		name1069 := _t1562
		xs1070 := []*pb.RelTerm{}
		cond1071 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond1071 {
			_t1563 := p.parse_rel_term()
			item1072 := _t1563
			xs1070 = append(xs1070, item1072)
			cond1071 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms1073 := xs1070
		p.consumeLiteral(")")
		_t1564 := &pb.Primitive{Name: name1069, Terms: rel_terms1073}
		_t1561 = _t1564
	} else {
		var _t1565 *pb.Primitive
		if prediction1059 == 8 {
			_t1566 := p.parse_divide()
			divide1068 := _t1566
			_t1565 = divide1068
		} else {
			var _t1567 *pb.Primitive
			if prediction1059 == 7 {
				_t1568 := p.parse_multiply()
				multiply1067 := _t1568
				_t1567 = multiply1067
			} else {
				var _t1569 *pb.Primitive
				if prediction1059 == 6 {
					_t1570 := p.parse_minus()
					minus1066 := _t1570
					_t1569 = minus1066
				} else {
					var _t1571 *pb.Primitive
					if prediction1059 == 5 {
						_t1572 := p.parse_add()
						add1065 := _t1572
						_t1571 = add1065
					} else {
						var _t1573 *pb.Primitive
						if prediction1059 == 4 {
							_t1574 := p.parse_gt_eq()
							gt_eq1064 := _t1574
							_t1573 = gt_eq1064
						} else {
							var _t1575 *pb.Primitive
							if prediction1059 == 3 {
								_t1576 := p.parse_gt()
								gt1063 := _t1576
								_t1575 = gt1063
							} else {
								var _t1577 *pb.Primitive
								if prediction1059 == 2 {
									_t1578 := p.parse_lt_eq()
									lt_eq1062 := _t1578
									_t1577 = lt_eq1062
								} else {
									var _t1579 *pb.Primitive
									if prediction1059 == 1 {
										_t1580 := p.parse_lt()
										lt1061 := _t1580
										_t1579 = lt1061
									} else {
										var _t1581 *pb.Primitive
										if prediction1059 == 0 {
											_t1582 := p.parse_eq()
											eq1060 := _t1582
											_t1581 = eq1060
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
		_t1561 = _t1565
	}
	return _t1561
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1583 := p.parse_term()
	term1074 := _t1583
	_t1584 := p.parse_term()
	term_31075 := _t1584
	p.consumeLiteral(")")
	_t1585 := &pb.RelTerm{}
	_t1585.RelTermType = &pb.RelTerm_Term{Term: term1074}
	_t1586 := &pb.RelTerm{}
	_t1586.RelTermType = &pb.RelTerm_Term{Term: term_31075}
	_t1587 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1585, _t1586}}
	return _t1587
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1588 := p.parse_term()
	term1076 := _t1588
	_t1589 := p.parse_term()
	term_31077 := _t1589
	p.consumeLiteral(")")
	_t1590 := &pb.RelTerm{}
	_t1590.RelTermType = &pb.RelTerm_Term{Term: term1076}
	_t1591 := &pb.RelTerm{}
	_t1591.RelTermType = &pb.RelTerm_Term{Term: term_31077}
	_t1592 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1590, _t1591}}
	return _t1592
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1593 := p.parse_term()
	term1078 := _t1593
	_t1594 := p.parse_term()
	term_31079 := _t1594
	p.consumeLiteral(")")
	_t1595 := &pb.RelTerm{}
	_t1595.RelTermType = &pb.RelTerm_Term{Term: term1078}
	_t1596 := &pb.RelTerm{}
	_t1596.RelTermType = &pb.RelTerm_Term{Term: term_31079}
	_t1597 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1595, _t1596}}
	return _t1597
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1598 := p.parse_term()
	term1080 := _t1598
	_t1599 := p.parse_term()
	term_31081 := _t1599
	p.consumeLiteral(")")
	_t1600 := &pb.RelTerm{}
	_t1600.RelTermType = &pb.RelTerm_Term{Term: term1080}
	_t1601 := &pb.RelTerm{}
	_t1601.RelTermType = &pb.RelTerm_Term{Term: term_31081}
	_t1602 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1600, _t1601}}
	return _t1602
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1603 := p.parse_term()
	term1082 := _t1603
	_t1604 := p.parse_term()
	term_31083 := _t1604
	p.consumeLiteral(")")
	_t1605 := &pb.RelTerm{}
	_t1605.RelTermType = &pb.RelTerm_Term{Term: term1082}
	_t1606 := &pb.RelTerm{}
	_t1606.RelTermType = &pb.RelTerm_Term{Term: term_31083}
	_t1607 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1605, _t1606}}
	return _t1607
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1608 := p.parse_term()
	term1084 := _t1608
	_t1609 := p.parse_term()
	term_31085 := _t1609
	_t1610 := p.parse_term()
	term_41086 := _t1610
	p.consumeLiteral(")")
	_t1611 := &pb.RelTerm{}
	_t1611.RelTermType = &pb.RelTerm_Term{Term: term1084}
	_t1612 := &pb.RelTerm{}
	_t1612.RelTermType = &pb.RelTerm_Term{Term: term_31085}
	_t1613 := &pb.RelTerm{}
	_t1613.RelTermType = &pb.RelTerm_Term{Term: term_41086}
	_t1614 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1611, _t1612, _t1613}}
	return _t1614
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1615 := p.parse_term()
	term1087 := _t1615
	_t1616 := p.parse_term()
	term_31088 := _t1616
	_t1617 := p.parse_term()
	term_41089 := _t1617
	p.consumeLiteral(")")
	_t1618 := &pb.RelTerm{}
	_t1618.RelTermType = &pb.RelTerm_Term{Term: term1087}
	_t1619 := &pb.RelTerm{}
	_t1619.RelTermType = &pb.RelTerm_Term{Term: term_31088}
	_t1620 := &pb.RelTerm{}
	_t1620.RelTermType = &pb.RelTerm_Term{Term: term_41089}
	_t1621 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1618, _t1619, _t1620}}
	return _t1621
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1622 := p.parse_term()
	term1090 := _t1622
	_t1623 := p.parse_term()
	term_31091 := _t1623
	_t1624 := p.parse_term()
	term_41092 := _t1624
	p.consumeLiteral(")")
	_t1625 := &pb.RelTerm{}
	_t1625.RelTermType = &pb.RelTerm_Term{Term: term1090}
	_t1626 := &pb.RelTerm{}
	_t1626.RelTermType = &pb.RelTerm_Term{Term: term_31091}
	_t1627 := &pb.RelTerm{}
	_t1627.RelTermType = &pb.RelTerm_Term{Term: term_41092}
	_t1628 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1625, _t1626, _t1627}}
	return _t1628
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1629 := p.parse_term()
	term1093 := _t1629
	_t1630 := p.parse_term()
	term_31094 := _t1630
	_t1631 := p.parse_term()
	term_41095 := _t1631
	p.consumeLiteral(")")
	_t1632 := &pb.RelTerm{}
	_t1632.RelTermType = &pb.RelTerm_Term{Term: term1093}
	_t1633 := &pb.RelTerm{}
	_t1633.RelTermType = &pb.RelTerm_Term{Term: term_31094}
	_t1634 := &pb.RelTerm{}
	_t1634.RelTermType = &pb.RelTerm_Term{Term: term_41095}
	_t1635 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1632, _t1633, _t1634}}
	return _t1635
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1636 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1636 = 1
	} else {
		var _t1637 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1637 = 1
		} else {
			var _t1638 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1638 = 1
			} else {
				var _t1639 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1639 = 1
				} else {
					var _t1640 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1640 = 0
					} else {
						var _t1641 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1641 = 1
						} else {
							var _t1642 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1642 = 1
							} else {
								var _t1643 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1643 = 1
								} else {
									var _t1644 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1644 = 1
									} else {
										var _t1645 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1645 = 1
										} else {
											var _t1646 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1646 = 1
											} else {
												var _t1647 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1647 = 1
												} else {
													_t1647 = -1
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
		_t1636 = _t1637
	}
	prediction1096 := _t1636
	var _t1648 *pb.RelTerm
	if prediction1096 == 1 {
		_t1649 := p.parse_term()
		term1098 := _t1649
		_t1650 := &pb.RelTerm{}
		_t1650.RelTermType = &pb.RelTerm_Term{Term: term1098}
		_t1648 = _t1650
	} else {
		var _t1651 *pb.RelTerm
		if prediction1096 == 0 {
			_t1652 := p.parse_specialized_value()
			specialized_value1097 := _t1652
			_t1653 := &pb.RelTerm{}
			_t1653.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value1097}
			_t1651 = _t1653
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1648 = _t1651
	}
	return _t1648
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1654 := p.parse_value()
	value1099 := _t1654
	return value1099
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1655 := p.parse_name()
	name1100 := _t1655
	xs1101 := []*pb.RelTerm{}
	cond1102 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1102 {
		_t1656 := p.parse_rel_term()
		item1103 := _t1656
		xs1101 = append(xs1101, item1103)
		cond1102 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms1104 := xs1101
	p.consumeLiteral(")")
	_t1657 := &pb.RelAtom{Name: name1100, Terms: rel_terms1104}
	return _t1657
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1658 := p.parse_term()
	term1105 := _t1658
	_t1659 := p.parse_term()
	term_31106 := _t1659
	p.consumeLiteral(")")
	_t1660 := &pb.Cast{Input: term1105, Result: term_31106}
	return _t1660
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs1107 := []*pb.Attribute{}
	cond1108 := p.matchLookaheadLiteral("(", 0)
	for cond1108 {
		_t1661 := p.parse_attribute()
		item1109 := _t1661
		xs1107 = append(xs1107, item1109)
		cond1108 = p.matchLookaheadLiteral("(", 0)
	}
	attributes1110 := xs1107
	p.consumeLiteral(")")
	return attributes1110
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1662 := p.parse_name()
	name1111 := _t1662
	xs1112 := []*pb.Value{}
	cond1113 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1113 {
		_t1663 := p.parse_value()
		item1114 := _t1663
		xs1112 = append(xs1112, item1114)
		cond1113 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values1115 := xs1112
	p.consumeLiteral(")")
	_t1664 := &pb.Attribute{Name: name1111, Args: values1115}
	return _t1664
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs1116 := []*pb.RelationId{}
	cond1117 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1117 {
		_t1665 := p.parse_relation_id()
		item1118 := _t1665
		xs1116 = append(xs1116, item1118)
		cond1117 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1119 := xs1116
	_t1666 := p.parse_script()
	script1120 := _t1666
	p.consumeLiteral(")")
	_t1667 := &pb.Algorithm{Global: relation_ids1119, Body: script1120}
	return _t1667
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs1121 := []*pb.Construct{}
	cond1122 := p.matchLookaheadLiteral("(", 0)
	for cond1122 {
		_t1668 := p.parse_construct()
		item1123 := _t1668
		xs1121 = append(xs1121, item1123)
		cond1122 = p.matchLookaheadLiteral("(", 0)
	}
	constructs1124 := xs1121
	p.consumeLiteral(")")
	_t1669 := &pb.Script{Constructs: constructs1124}
	return _t1669
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1670 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1671 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1671 = 1
		} else {
			var _t1672 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1672 = 1
			} else {
				var _t1673 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1673 = 1
				} else {
					var _t1674 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1674 = 0
					} else {
						var _t1675 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1675 = 1
						} else {
							var _t1676 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1676 = 1
							} else {
								_t1676 = -1
							}
							_t1675 = _t1676
						}
						_t1674 = _t1675
					}
					_t1673 = _t1674
				}
				_t1672 = _t1673
			}
			_t1671 = _t1672
		}
		_t1670 = _t1671
	} else {
		_t1670 = -1
	}
	prediction1125 := _t1670
	var _t1677 *pb.Construct
	if prediction1125 == 1 {
		_t1678 := p.parse_instruction()
		instruction1127 := _t1678
		_t1679 := &pb.Construct{}
		_t1679.ConstructType = &pb.Construct_Instruction{Instruction: instruction1127}
		_t1677 = _t1679
	} else {
		var _t1680 *pb.Construct
		if prediction1125 == 0 {
			_t1681 := p.parse_loop()
			loop1126 := _t1681
			_t1682 := &pb.Construct{}
			_t1682.ConstructType = &pb.Construct_Loop{Loop: loop1126}
			_t1680 = _t1682
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1677 = _t1680
	}
	return _t1677
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1683 := p.parse_init()
	init1128 := _t1683
	_t1684 := p.parse_script()
	script1129 := _t1684
	p.consumeLiteral(")")
	_t1685 := &pb.Loop{Init: init1128, Body: script1129}
	return _t1685
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs1130 := []*pb.Instruction{}
	cond1131 := p.matchLookaheadLiteral("(", 0)
	for cond1131 {
		_t1686 := p.parse_instruction()
		item1132 := _t1686
		xs1130 = append(xs1130, item1132)
		cond1131 = p.matchLookaheadLiteral("(", 0)
	}
	instructions1133 := xs1130
	p.consumeLiteral(")")
	return instructions1133
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1687 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1688 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1688 = 1
		} else {
			var _t1689 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1689 = 4
			} else {
				var _t1690 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1690 = 3
				} else {
					var _t1691 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1691 = 2
					} else {
						var _t1692 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1692 = 0
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
	} else {
		_t1687 = -1
	}
	prediction1134 := _t1687
	var _t1693 *pb.Instruction
	if prediction1134 == 4 {
		_t1694 := p.parse_monus_def()
		monus_def1139 := _t1694
		_t1695 := &pb.Instruction{}
		_t1695.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def1139}
		_t1693 = _t1695
	} else {
		var _t1696 *pb.Instruction
		if prediction1134 == 3 {
			_t1697 := p.parse_monoid_def()
			monoid_def1138 := _t1697
			_t1698 := &pb.Instruction{}
			_t1698.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def1138}
			_t1696 = _t1698
		} else {
			var _t1699 *pb.Instruction
			if prediction1134 == 2 {
				_t1700 := p.parse_break()
				break1137 := _t1700
				_t1701 := &pb.Instruction{}
				_t1701.InstrType = &pb.Instruction_Break{Break: break1137}
				_t1699 = _t1701
			} else {
				var _t1702 *pb.Instruction
				if prediction1134 == 1 {
					_t1703 := p.parse_upsert()
					upsert1136 := _t1703
					_t1704 := &pb.Instruction{}
					_t1704.InstrType = &pb.Instruction_Upsert{Upsert: upsert1136}
					_t1702 = _t1704
				} else {
					var _t1705 *pb.Instruction
					if prediction1134 == 0 {
						_t1706 := p.parse_assign()
						assign1135 := _t1706
						_t1707 := &pb.Instruction{}
						_t1707.InstrType = &pb.Instruction_Assign{Assign: assign1135}
						_t1705 = _t1707
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1702 = _t1705
				}
				_t1699 = _t1702
			}
			_t1696 = _t1699
		}
		_t1693 = _t1696
	}
	return _t1693
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1708 := p.parse_relation_id()
	relation_id1140 := _t1708
	_t1709 := p.parse_abstraction()
	abstraction1141 := _t1709
	var _t1710 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1711 := p.parse_attrs()
		_t1710 = _t1711
	}
	attrs1142 := _t1710
	p.consumeLiteral(")")
	_t1712 := attrs1142
	if attrs1142 == nil {
		_t1712 = []*pb.Attribute{}
	}
	_t1713 := &pb.Assign{Name: relation_id1140, Body: abstraction1141, Attrs: _t1712}
	return _t1713
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1714 := p.parse_relation_id()
	relation_id1143 := _t1714
	_t1715 := p.parse_abstraction_with_arity()
	abstraction_with_arity1144 := _t1715
	var _t1716 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1717 := p.parse_attrs()
		_t1716 = _t1717
	}
	attrs1145 := _t1716
	p.consumeLiteral(")")
	_t1718 := attrs1145
	if attrs1145 == nil {
		_t1718 = []*pb.Attribute{}
	}
	_t1719 := &pb.Upsert{Name: relation_id1143, Body: abstraction_with_arity1144[0].(*pb.Abstraction), Attrs: _t1718, ValueArity: abstraction_with_arity1144[1].(int64)}
	return _t1719
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1720 := p.parse_bindings()
	bindings1146 := _t1720
	_t1721 := p.parse_formula()
	formula1147 := _t1721
	p.consumeLiteral(")")
	_t1722 := &pb.Abstraction{Vars: listConcat(bindings1146[0].([]*pb.Binding), bindings1146[1].([]*pb.Binding)), Value: formula1147}
	return []interface{}{_t1722, int64(len(bindings1146[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1723 := p.parse_relation_id()
	relation_id1148 := _t1723
	_t1724 := p.parse_abstraction()
	abstraction1149 := _t1724
	var _t1725 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1726 := p.parse_attrs()
		_t1725 = _t1726
	}
	attrs1150 := _t1725
	p.consumeLiteral(")")
	_t1727 := attrs1150
	if attrs1150 == nil {
		_t1727 = []*pb.Attribute{}
	}
	_t1728 := &pb.Break{Name: relation_id1148, Body: abstraction1149, Attrs: _t1727}
	return _t1728
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1729 := p.parse_monoid()
	monoid1151 := _t1729
	_t1730 := p.parse_relation_id()
	relation_id1152 := _t1730
	_t1731 := p.parse_abstraction_with_arity()
	abstraction_with_arity1153 := _t1731
	var _t1732 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1733 := p.parse_attrs()
		_t1732 = _t1733
	}
	attrs1154 := _t1732
	p.consumeLiteral(")")
	_t1734 := attrs1154
	if attrs1154 == nil {
		_t1734 = []*pb.Attribute{}
	}
	_t1735 := &pb.MonoidDef{Monoid: monoid1151, Name: relation_id1152, Body: abstraction_with_arity1153[0].(*pb.Abstraction), Attrs: _t1734, ValueArity: abstraction_with_arity1153[1].(int64)}
	return _t1735
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1736 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1737 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1737 = 3
		} else {
			var _t1738 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1738 = 0
			} else {
				var _t1739 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1739 = 1
				} else {
					var _t1740 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1740 = 2
					} else {
						_t1740 = -1
					}
					_t1739 = _t1740
				}
				_t1738 = _t1739
			}
			_t1737 = _t1738
		}
		_t1736 = _t1737
	} else {
		_t1736 = -1
	}
	prediction1155 := _t1736
	var _t1741 *pb.Monoid
	if prediction1155 == 3 {
		_t1742 := p.parse_sum_monoid()
		sum_monoid1159 := _t1742
		_t1743 := &pb.Monoid{}
		_t1743.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid1159}
		_t1741 = _t1743
	} else {
		var _t1744 *pb.Monoid
		if prediction1155 == 2 {
			_t1745 := p.parse_max_monoid()
			max_monoid1158 := _t1745
			_t1746 := &pb.Monoid{}
			_t1746.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid1158}
			_t1744 = _t1746
		} else {
			var _t1747 *pb.Monoid
			if prediction1155 == 1 {
				_t1748 := p.parse_min_monoid()
				min_monoid1157 := _t1748
				_t1749 := &pb.Monoid{}
				_t1749.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid1157}
				_t1747 = _t1749
			} else {
				var _t1750 *pb.Monoid
				if prediction1155 == 0 {
					_t1751 := p.parse_or_monoid()
					or_monoid1156 := _t1751
					_t1752 := &pb.Monoid{}
					_t1752.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid1156}
					_t1750 = _t1752
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1747 = _t1750
			}
			_t1744 = _t1747
		}
		_t1741 = _t1744
	}
	return _t1741
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1753 := &pb.OrMonoid{}
	return _t1753
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1754 := p.parse_type()
	type1160 := _t1754
	p.consumeLiteral(")")
	_t1755 := &pb.MinMonoid{Type: type1160}
	return _t1755
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1756 := p.parse_type()
	type1161 := _t1756
	p.consumeLiteral(")")
	_t1757 := &pb.MaxMonoid{Type: type1161}
	return _t1757
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1758 := p.parse_type()
	type1162 := _t1758
	p.consumeLiteral(")")
	_t1759 := &pb.SumMonoid{Type: type1162}
	return _t1759
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1760 := p.parse_monoid()
	monoid1163 := _t1760
	_t1761 := p.parse_relation_id()
	relation_id1164 := _t1761
	_t1762 := p.parse_abstraction_with_arity()
	abstraction_with_arity1165 := _t1762
	var _t1763 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1764 := p.parse_attrs()
		_t1763 = _t1764
	}
	attrs1166 := _t1763
	p.consumeLiteral(")")
	_t1765 := attrs1166
	if attrs1166 == nil {
		_t1765 = []*pb.Attribute{}
	}
	_t1766 := &pb.MonusDef{Monoid: monoid1163, Name: relation_id1164, Body: abstraction_with_arity1165[0].(*pb.Abstraction), Attrs: _t1765, ValueArity: abstraction_with_arity1165[1].(int64)}
	return _t1766
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1767 := p.parse_relation_id()
	relation_id1167 := _t1767
	_t1768 := p.parse_abstraction()
	abstraction1168 := _t1768
	_t1769 := p.parse_functional_dependency_keys()
	functional_dependency_keys1169 := _t1769
	_t1770 := p.parse_functional_dependency_values()
	functional_dependency_values1170 := _t1770
	p.consumeLiteral(")")
	_t1771 := &pb.FunctionalDependency{Guard: abstraction1168, Keys: functional_dependency_keys1169, Values: functional_dependency_values1170}
	_t1772 := &pb.Constraint{Name: relation_id1167}
	_t1772.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1771}
	return _t1772
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs1171 := []*pb.Var{}
	cond1172 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1172 {
		_t1773 := p.parse_var()
		item1173 := _t1773
		xs1171 = append(xs1171, item1173)
		cond1172 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1174 := xs1171
	p.consumeLiteral(")")
	return vars1174
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs1175 := []*pb.Var{}
	cond1176 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond1176 {
		_t1774 := p.parse_var()
		item1177 := _t1774
		xs1175 = append(xs1175, item1177)
		cond1176 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars1178 := xs1175
	p.consumeLiteral(")")
	return vars1178
}

func (p *Parser) parse_data() *pb.Data {
	var _t1775 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1776 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1776 = 0
		} else {
			var _t1777 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1777 = 2
			} else {
				var _t1778 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1778 = 1
				} else {
					_t1778 = -1
				}
				_t1777 = _t1778
			}
			_t1776 = _t1777
		}
		_t1775 = _t1776
	} else {
		_t1775 = -1
	}
	prediction1179 := _t1775
	var _t1779 *pb.Data
	if prediction1179 == 2 {
		_t1780 := p.parse_csv_data()
		csv_data1182 := _t1780
		_t1781 := &pb.Data{}
		_t1781.DataType = &pb.Data_CsvData{CsvData: csv_data1182}
		_t1779 = _t1781
	} else {
		var _t1782 *pb.Data
		if prediction1179 == 1 {
			_t1783 := p.parse_betree_relation()
			betree_relation1181 := _t1783
			_t1784 := &pb.Data{}
			_t1784.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation1181}
			_t1782 = _t1784
		} else {
			var _t1785 *pb.Data
			if prediction1179 == 0 {
				_t1786 := p.parse_rel_edb()
				rel_edb1180 := _t1786
				_t1787 := &pb.Data{}
				_t1787.DataType = &pb.Data_RelEdb{RelEdb: rel_edb1180}
				_t1785 = _t1787
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1782 = _t1785
		}
		_t1779 = _t1782
	}
	return _t1779
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1788 := p.parse_relation_id()
	relation_id1183 := _t1788
	_t1789 := p.parse_rel_edb_path()
	rel_edb_path1184 := _t1789
	_t1790 := p.parse_rel_edb_types()
	rel_edb_types1185 := _t1790
	p.consumeLiteral(")")
	_t1791 := &pb.RelEDB{TargetId: relation_id1183, Path: rel_edb_path1184, Types: rel_edb_types1185}
	return _t1791
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs1186 := []string{}
	cond1187 := p.matchLookaheadTerminal("STRING", 0)
	for cond1187 {
		item1188 := p.consumeTerminal("STRING").Value.AsString()
		xs1186 = append(xs1186, item1188)
		cond1187 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1189 := xs1186
	p.consumeLiteral("]")
	return strings1189
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs1190 := []*pb.Type{}
	cond1191 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1191 {
		_t1792 := p.parse_type()
		item1192 := _t1792
		xs1190 = append(xs1190, item1192)
		cond1191 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1193 := xs1190
	p.consumeLiteral("]")
	return types1193
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1793 := p.parse_relation_id()
	relation_id1194 := _t1793
	_t1794 := p.parse_betree_info()
	betree_info1195 := _t1794
	p.consumeLiteral(")")
	_t1795 := &pb.BeTreeRelation{Name: relation_id1194, RelationInfo: betree_info1195}
	return _t1795
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1796 := p.parse_betree_info_key_types()
	betree_info_key_types1196 := _t1796
	_t1797 := p.parse_betree_info_value_types()
	betree_info_value_types1197 := _t1797
	_t1798 := p.parse_config_dict()
	config_dict1198 := _t1798
	p.consumeLiteral(")")
	_t1799 := p.construct_betree_info(betree_info_key_types1196, betree_info_value_types1197, config_dict1198)
	return _t1799
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1199 := []*pb.Type{}
	cond1200 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1200 {
		_t1800 := p.parse_type()
		item1201 := _t1800
		xs1199 = append(xs1199, item1201)
		cond1200 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1202 := xs1199
	p.consumeLiteral(")")
	return types1202
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1203 := []*pb.Type{}
	cond1204 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1204 {
		_t1801 := p.parse_type()
		item1205 := _t1801
		xs1203 = append(xs1203, item1205)
		cond1204 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1206 := xs1203
	p.consumeLiteral(")")
	return types1206
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1802 := p.parse_csvlocator()
	csvlocator1207 := _t1802
	_t1803 := p.parse_csv_config()
	csv_config1208 := _t1803
	_t1804 := p.parse_csv_columns()
	csv_columns1209 := _t1804
	_t1805 := p.parse_csv_asof()
	csv_asof1210 := _t1805
	p.consumeLiteral(")")
	_t1806 := &pb.CSVData{Locator: csvlocator1207, Config: csv_config1208, Columns: csv_columns1209, Asof: csv_asof1210}
	return _t1806
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1807 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1808 := p.parse_csv_locator_paths()
		_t1807 = _t1808
	}
	csv_locator_paths1211 := _t1807
	var _t1809 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1810 := p.parse_csv_locator_inline_data()
		_t1809 = ptr(_t1810)
	}
	csv_locator_inline_data1212 := _t1809
	p.consumeLiteral(")")
	_t1811 := csv_locator_paths1211
	if csv_locator_paths1211 == nil {
		_t1811 = []string{}
	}
	_t1812 := &pb.CSVLocator{Paths: _t1811, InlineData: []byte(deref(csv_locator_inline_data1212, ""))}
	return _t1812
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1213 := []string{}
	cond1214 := p.matchLookaheadTerminal("STRING", 0)
	for cond1214 {
		item1215 := p.consumeTerminal("STRING").Value.AsString()
		xs1213 = append(xs1213, item1215)
		cond1214 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1216 := xs1213
	p.consumeLiteral(")")
	return strings1216
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1217 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string1217
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1813 := p.parse_config_dict()
	config_dict1218 := _t1813
	p.consumeLiteral(")")
	_t1814 := p.construct_csv_config(config_dict1218)
	return _t1814
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1219 := []*pb.CSVColumn{}
	cond1220 := p.matchLookaheadLiteral("(", 0)
	for cond1220 {
		_t1815 := p.parse_csv_column()
		item1221 := _t1815
		xs1219 = append(xs1219, item1221)
		cond1220 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns1222 := xs1219
	p.consumeLiteral(")")
	return csv_columns1222
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1223 := p.consumeTerminal("STRING").Value.AsString()
	_t1816 := p.parse_relation_id()
	relation_id1224 := _t1816
	p.consumeLiteral("[")
	xs1225 := []*pb.Type{}
	cond1226 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1226 {
		_t1817 := p.parse_type()
		item1227 := _t1817
		xs1225 = append(xs1225, item1227)
		cond1226 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1228 := xs1225
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1818 := &pb.CSVColumn{ColumnName: string1223, TargetId: relation_id1224, Types: types1228}
	return _t1818
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1229 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string1229
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1819 := p.parse_fragment_id()
	fragment_id1230 := _t1819
	p.consumeLiteral(")")
	_t1820 := &pb.Undefine{FragmentId: fragment_id1230}
	return _t1820
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1231 := []*pb.RelationId{}
	cond1232 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1232 {
		_t1821 := p.parse_relation_id()
		item1233 := _t1821
		xs1231 = append(xs1231, item1233)
		cond1232 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1234 := xs1231
	p.consumeLiteral(")")
	_t1822 := &pb.Context{Relations: relation_ids1234}
	return _t1822
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1235 := []*pb.Read{}
	cond1236 := p.matchLookaheadLiteral("(", 0)
	for cond1236 {
		_t1823 := p.parse_read()
		item1237 := _t1823
		xs1235 = append(xs1235, item1237)
		cond1236 = p.matchLookaheadLiteral("(", 0)
	}
	reads1238 := xs1235
	p.consumeLiteral(")")
	return reads1238
}

func (p *Parser) parse_read() *pb.Read {
	var _t1824 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1825 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1825 = 2
		} else {
			var _t1826 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1826 = 1
			} else {
				var _t1827 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1827 = 4
				} else {
					var _t1828 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1828 = 0
					} else {
						var _t1829 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1829 = 3
						} else {
							_t1829 = -1
						}
						_t1828 = _t1829
					}
					_t1827 = _t1828
				}
				_t1826 = _t1827
			}
			_t1825 = _t1826
		}
		_t1824 = _t1825
	} else {
		_t1824 = -1
	}
	prediction1239 := _t1824
	var _t1830 *pb.Read
	if prediction1239 == 4 {
		_t1831 := p.parse_export()
		export1244 := _t1831
		_t1832 := &pb.Read{}
		_t1832.ReadType = &pb.Read_Export{Export: export1244}
		_t1830 = _t1832
	} else {
		var _t1833 *pb.Read
		if prediction1239 == 3 {
			_t1834 := p.parse_abort()
			abort1243 := _t1834
			_t1835 := &pb.Read{}
			_t1835.ReadType = &pb.Read_Abort{Abort: abort1243}
			_t1833 = _t1835
		} else {
			var _t1836 *pb.Read
			if prediction1239 == 2 {
				_t1837 := p.parse_what_if()
				what_if1242 := _t1837
				_t1838 := &pb.Read{}
				_t1838.ReadType = &pb.Read_WhatIf{WhatIf: what_if1242}
				_t1836 = _t1838
			} else {
				var _t1839 *pb.Read
				if prediction1239 == 1 {
					_t1840 := p.parse_output()
					output1241 := _t1840
					_t1841 := &pb.Read{}
					_t1841.ReadType = &pb.Read_Output{Output: output1241}
					_t1839 = _t1841
				} else {
					var _t1842 *pb.Read
					if prediction1239 == 0 {
						_t1843 := p.parse_demand()
						demand1240 := _t1843
						_t1844 := &pb.Read{}
						_t1844.ReadType = &pb.Read_Demand{Demand: demand1240}
						_t1842 = _t1844
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1839 = _t1842
				}
				_t1836 = _t1839
			}
			_t1833 = _t1836
		}
		_t1830 = _t1833
	}
	return _t1830
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1845 := p.parse_relation_id()
	relation_id1245 := _t1845
	p.consumeLiteral(")")
	_t1846 := &pb.Demand{RelationId: relation_id1245}
	return _t1846
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1847 := p.parse_name()
	name1246 := _t1847
	_t1848 := p.parse_relation_id()
	relation_id1247 := _t1848
	p.consumeLiteral(")")
	_t1849 := &pb.Output{Name: name1246, RelationId: relation_id1247}
	return _t1849
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1850 := p.parse_name()
	name1248 := _t1850
	_t1851 := p.parse_epoch()
	epoch1249 := _t1851
	p.consumeLiteral(")")
	_t1852 := &pb.WhatIf{Branch: name1248, Epoch: epoch1249}
	return _t1852
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1853 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1854 := p.parse_name()
		_t1853 = ptr(_t1854)
	}
	name1250 := _t1853
	_t1855 := p.parse_relation_id()
	relation_id1251 := _t1855
	p.consumeLiteral(")")
	_t1856 := &pb.Abort{Name: deref(name1250, "abort"), RelationId: relation_id1251}
	return _t1856
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1857 := p.parse_export_csv_config()
	export_csv_config1252 := _t1857
	p.consumeLiteral(")")
	_t1858 := &pb.Export{}
	_t1858.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1252}
	return _t1858
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1859 := p.parse_export_csv_path()
	export_csv_path1253 := _t1859
	_t1860 := p.parse_export_csv_columns()
	export_csv_columns1254 := _t1860
	_t1861 := p.parse_config_dict()
	config_dict1255 := _t1861
	p.consumeLiteral(")")
	_t1862 := p.export_csv_config(export_csv_path1253, export_csv_columns1254, config_dict1255)
	return _t1862
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1256 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string1256
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1257 := []*pb.ExportCSVColumn{}
	cond1258 := p.matchLookaheadLiteral("(", 0)
	for cond1258 {
		_t1863 := p.parse_export_csv_column()
		item1259 := _t1863
		xs1257 = append(xs1257, item1259)
		cond1258 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1260 := xs1257
	p.consumeLiteral(")")
	return export_csv_columns1260
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1261 := p.consumeTerminal("STRING").Value.AsString()
	_t1864 := p.parse_relation_id()
	relation_id1262 := _t1864
	p.consumeLiteral(")")
	_t1865 := &pb.ExportCSVColumn{ColumnName: string1261, ColumnData: relation_id1262}
	return _t1865
}


// Parse parses the input string and returns the result
func Parse(input string) (*pb.Transaction, error) {
	defer func() {
		if r := recover(); r != nil {
			if pe, ok := r.(ParseError); ok {
				panic(pe)
			}
			panic(r)
		}
	}()

	lexer := NewLexer(input)
	parser := NewParser(lexer.tokens)
	result := parser.parse_transaction()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, nil
}
