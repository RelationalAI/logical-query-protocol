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
	var _t1309 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1309
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1310 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1310
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1311 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1311
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1312 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1312
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1313 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1313
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1314 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1314
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1315 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1315
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1316 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1316
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1317 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1317
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1318 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1318
	_t1319 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1319
	_t1320 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1320
	_t1321 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1321
	_t1322 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1322
	_t1323 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1323
	_t1324 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1324
	_t1325 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1325
	_t1326 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1326
	_t1327 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1327
	_t1328 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1328
	_t1329 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1329
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1330 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1330
	_t1331 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1331
	_t1332 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1332
	_t1333 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1333
	_t1334 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1334
	_t1335 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1335
	_t1336 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1336
	_t1337 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1337
	_t1338 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1338
	_t1339 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1339.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1339.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1339
	_t1340 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1340
}

func (p *Parser) default_configure() *pb.Configure {
	_t1341 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1341
	_t1342 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1342
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
	_t1343 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1343
	_t1344 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1344
	_t1345 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1345
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1346 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1346
	_t1347 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1347
	_t1348 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1348
	_t1349 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1349
	_t1350 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1350
	_t1351 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1351
	_t1352 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1352
	_t1353 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1353
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t706 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t707 := p.parse_configure()
		_t706 = _t707
	}
	configure353 := _t706
	var _t708 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t709 := p.parse_sync()
		_t708 = _t709
	}
	sync354 := _t708
	xs355 := []*pb.Epoch{}
	cond356 := p.matchLookaheadLiteral("(", 0)
	for cond356 {
		_t710 := p.parse_epoch()
		item357 := _t710
		xs355 = append(xs355, item357)
		cond356 = p.matchLookaheadLiteral("(", 0)
	}
	epochs358 := xs355
	p.consumeLiteral(")")
	_t711 := p.default_configure()
	_t712 := configure353
	if configure353 == nil {
		_t712 = _t711
	}
	_t713 := &pb.Transaction{Epochs: epochs358, Configure: _t712, Sync: sync354}
	return _t713
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t714 := p.parse_config_dict()
	config_dict359 := _t714
	p.consumeLiteral(")")
	_t715 := p.construct_configure(config_dict359)
	return _t715
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs360 := [][]interface{}{}
	cond361 := p.matchLookaheadLiteral(":", 0)
	for cond361 {
		_t716 := p.parse_config_key_value()
		item362 := _t716
		xs360 = append(xs360, item362)
		cond361 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values363 := xs360
	p.consumeLiteral("}")
	return config_key_values363
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol364 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t717 := p.parse_value()
	value365 := _t717
	return []interface{}{symbol364, value365}
}

func (p *Parser) parse_value() *pb.Value {
	var _t718 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t718 = 9
	} else {
		var _t719 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t719 = 8
		} else {
			var _t720 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t720 = 9
			} else {
				var _t721 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t722 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t722 = 1
					} else {
						var _t723 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t723 = 0
						} else {
							_t723 = -1
						}
						_t722 = _t723
					}
					_t721 = _t722
				} else {
					var _t724 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t724 = 5
					} else {
						var _t725 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t725 = 2
						} else {
							var _t726 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t726 = 6
							} else {
								var _t727 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t727 = 3
								} else {
									var _t728 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t728 = 4
									} else {
										var _t729 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t729 = 7
										} else {
											_t729 = -1
										}
										_t728 = _t729
									}
									_t727 = _t728
								}
								_t726 = _t727
							}
							_t725 = _t726
						}
						_t724 = _t725
					}
					_t721 = _t724
				}
				_t720 = _t721
			}
			_t719 = _t720
		}
		_t718 = _t719
	}
	prediction366 := _t718
	var _t730 *pb.Value
	if prediction366 == 9 {
		_t731 := p.parse_boolean_value()
		boolean_value375 := _t731
		_t732 := &pb.Value{}
		_t732.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value375}
		_t730 = _t732
	} else {
		var _t733 *pb.Value
		if prediction366 == 8 {
			p.consumeLiteral("missing")
			_t734 := &pb.MissingValue{}
			_t735 := &pb.Value{}
			_t735.Value = &pb.Value_MissingValue{MissingValue: _t734}
			_t733 = _t735
		} else {
			var _t736 *pb.Value
			if prediction366 == 7 {
				decimal374 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t737 := &pb.Value{}
				_t737.Value = &pb.Value_DecimalValue{DecimalValue: decimal374}
				_t736 = _t737
			} else {
				var _t738 *pb.Value
				if prediction366 == 6 {
					int128373 := p.consumeTerminal("INT128").Value.AsInt128()
					_t739 := &pb.Value{}
					_t739.Value = &pb.Value_Int128Value{Int128Value: int128373}
					_t738 = _t739
				} else {
					var _t740 *pb.Value
					if prediction366 == 5 {
						uint128372 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t741 := &pb.Value{}
						_t741.Value = &pb.Value_Uint128Value{Uint128Value: uint128372}
						_t740 = _t741
					} else {
						var _t742 *pb.Value
						if prediction366 == 4 {
							float371 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t743 := &pb.Value{}
							_t743.Value = &pb.Value_FloatValue{FloatValue: float371}
							_t742 = _t743
						} else {
							var _t744 *pb.Value
							if prediction366 == 3 {
								int370 := p.consumeTerminal("INT").Value.AsInt64()
								_t745 := &pb.Value{}
								_t745.Value = &pb.Value_IntValue{IntValue: int370}
								_t744 = _t745
							} else {
								var _t746 *pb.Value
								if prediction366 == 2 {
									string369 := p.consumeTerminal("STRING").Value.AsString()
									_t747 := &pb.Value{}
									_t747.Value = &pb.Value_StringValue{StringValue: string369}
									_t746 = _t747
								} else {
									var _t748 *pb.Value
									if prediction366 == 1 {
										_t749 := p.parse_datetime()
										datetime368 := _t749
										_t750 := &pb.Value{}
										_t750.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime368}
										_t748 = _t750
									} else {
										var _t751 *pb.Value
										if prediction366 == 0 {
											_t752 := p.parse_date()
											date367 := _t752
											_t753 := &pb.Value{}
											_t753.Value = &pb.Value_DateValue{DateValue: date367}
											_t751 = _t753
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t748 = _t751
									}
									_t746 = _t748
								}
								_t744 = _t746
							}
							_t742 = _t744
						}
						_t740 = _t742
					}
					_t738 = _t740
				}
				_t736 = _t738
			}
			_t733 = _t736
		}
		_t730 = _t733
	}
	return _t730
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int376 := p.consumeTerminal("INT").Value.AsInt64()
	int_3377 := p.consumeTerminal("INT").Value.AsInt64()
	int_4378 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t754 := &pb.DateValue{Year: int32(int376), Month: int32(int_3377), Day: int32(int_4378)}
	return _t754
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int379 := p.consumeTerminal("INT").Value.AsInt64()
	int_3380 := p.consumeTerminal("INT").Value.AsInt64()
	int_4381 := p.consumeTerminal("INT").Value.AsInt64()
	int_5382 := p.consumeTerminal("INT").Value.AsInt64()
	int_6383 := p.consumeTerminal("INT").Value.AsInt64()
	int_7384 := p.consumeTerminal("INT").Value.AsInt64()
	var _t755 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t755 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_8385 := _t755
	p.consumeLiteral(")")
	_t756 := &pb.DateTimeValue{Year: int32(int379), Month: int32(int_3380), Day: int32(int_4381), Hour: int32(int_5382), Minute: int32(int_6383), Second: int32(int_7384), Microsecond: int32(deref(int_8385, 0))}
	return _t756
}

func (p *Parser) parse_boolean_value() bool {
	var _t757 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t757 = 0
	} else {
		var _t758 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t758 = 1
		} else {
			_t758 = -1
		}
		_t757 = _t758
	}
	prediction386 := _t757
	var _t759 bool
	if prediction386 == 1 {
		p.consumeLiteral("false")
		_t759 = false
	} else {
		var _t760 bool
		if prediction386 == 0 {
			p.consumeLiteral("true")
			_t760 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t759 = _t760
	}
	return _t759
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs387 := []*pb.FragmentId{}
	cond388 := p.matchLookaheadLiteral(":", 0)
	for cond388 {
		_t761 := p.parse_fragment_id()
		item389 := _t761
		xs387 = append(xs387, item389)
		cond388 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids390 := xs387
	p.consumeLiteral(")")
	_t762 := &pb.Sync{Fragments: fragment_ids390}
	return _t762
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol391 := p.consumeTerminal("SYMBOL").Value.AsString()
	return &pb.FragmentId{Id: []byte(symbol391)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t763 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t764 := p.parse_epoch_writes()
		_t763 = _t764
	}
	epoch_writes392 := _t763
	var _t765 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t766 := p.parse_epoch_reads()
		_t765 = _t766
	}
	epoch_reads393 := _t765
	p.consumeLiteral(")")
	_t767 := epoch_writes392
	if epoch_writes392 == nil {
		_t767 = []*pb.Write{}
	}
	_t768 := epoch_reads393
	if epoch_reads393 == nil {
		_t768 = []*pb.Read{}
	}
	_t769 := &pb.Epoch{Writes: _t767, Reads: _t768}
	return _t769
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs394 := []*pb.Write{}
	cond395 := p.matchLookaheadLiteral("(", 0)
	for cond395 {
		_t770 := p.parse_write()
		item396 := _t770
		xs394 = append(xs394, item396)
		cond395 = p.matchLookaheadLiteral("(", 0)
	}
	writes397 := xs394
	p.consumeLiteral(")")
	return writes397
}

func (p *Parser) parse_write() *pb.Write {
	var _t771 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t772 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t772 = 1
		} else {
			var _t773 int64
			if p.matchLookaheadLiteral("define", 1) {
				_t773 = 0
			} else {
				var _t774 int64
				if p.matchLookaheadLiteral("context", 1) {
					_t774 = 2
				} else {
					_t774 = -1
				}
				_t773 = _t774
			}
			_t772 = _t773
		}
		_t771 = _t772
	} else {
		_t771 = -1
	}
	prediction398 := _t771
	var _t775 *pb.Write
	if prediction398 == 2 {
		_t776 := p.parse_context()
		context401 := _t776
		_t777 := &pb.Write{}
		_t777.WriteType = &pb.Write_Context{Context: context401}
		_t775 = _t777
	} else {
		var _t778 *pb.Write
		if prediction398 == 1 {
			_t779 := p.parse_undefine()
			undefine400 := _t779
			_t780 := &pb.Write{}
			_t780.WriteType = &pb.Write_Undefine{Undefine: undefine400}
			_t778 = _t780
		} else {
			var _t781 *pb.Write
			if prediction398 == 0 {
				_t782 := p.parse_define()
				define399 := _t782
				_t783 := &pb.Write{}
				_t783.WriteType = &pb.Write_Define{Define: define399}
				_t781 = _t783
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t778 = _t781
		}
		_t775 = _t778
	}
	return _t775
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t784 := p.parse_fragment()
	fragment402 := _t784
	p.consumeLiteral(")")
	_t785 := &pb.Define{Fragment: fragment402}
	return _t785
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t786 := p.parse_new_fragment_id()
	new_fragment_id403 := _t786
	xs404 := []*pb.Declaration{}
	cond405 := p.matchLookaheadLiteral("(", 0)
	for cond405 {
		_t787 := p.parse_declaration()
		item406 := _t787
		xs404 = append(xs404, item406)
		cond405 = p.matchLookaheadLiteral("(", 0)
	}
	declarations407 := xs404
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id403, declarations407)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t788 := p.parse_fragment_id()
	fragment_id408 := _t788
	p.startFragment(fragment_id408)
	return fragment_id408
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t789 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t790 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t790 = 3
		} else {
			var _t791 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t791 = 2
			} else {
				var _t792 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t792 = 0
				} else {
					var _t793 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t793 = 3
					} else {
						var _t794 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t794 = 3
						} else {
							var _t795 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t795 = 1
							} else {
								_t795 = -1
							}
							_t794 = _t795
						}
						_t793 = _t794
					}
					_t792 = _t793
				}
				_t791 = _t792
			}
			_t790 = _t791
		}
		_t789 = _t790
	} else {
		_t789 = -1
	}
	prediction409 := _t789
	var _t796 *pb.Declaration
	if prediction409 == 3 {
		_t797 := p.parse_data()
		data413 := _t797
		_t798 := &pb.Declaration{}
		_t798.DeclarationType = &pb.Declaration_Data{Data: data413}
		_t796 = _t798
	} else {
		var _t799 *pb.Declaration
		if prediction409 == 2 {
			_t800 := p.parse_constraint()
			constraint412 := _t800
			_t801 := &pb.Declaration{}
			_t801.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint412}
			_t799 = _t801
		} else {
			var _t802 *pb.Declaration
			if prediction409 == 1 {
				_t803 := p.parse_algorithm()
				algorithm411 := _t803
				_t804 := &pb.Declaration{}
				_t804.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm411}
				_t802 = _t804
			} else {
				var _t805 *pb.Declaration
				if prediction409 == 0 {
					_t806 := p.parse_def()
					def410 := _t806
					_t807 := &pb.Declaration{}
					_t807.DeclarationType = &pb.Declaration_Def{Def: def410}
					_t805 = _t807
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t802 = _t805
			}
			_t799 = _t802
		}
		_t796 = _t799
	}
	return _t796
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t808 := p.parse_relation_id()
	relation_id414 := _t808
	_t809 := p.parse_abstraction()
	abstraction415 := _t809
	var _t810 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t811 := p.parse_attrs()
		_t810 = _t811
	}
	attrs416 := _t810
	p.consumeLiteral(")")
	_t812 := attrs416
	if attrs416 == nil {
		_t812 = []*pb.Attribute{}
	}
	_t813 := &pb.Def{Name: relation_id414, Body: abstraction415, Attrs: _t812}
	return _t813
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t814 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t814 = 0
	} else {
		var _t815 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t815 = 1
		} else {
			_t815 = -1
		}
		_t814 = _t815
	}
	prediction417 := _t814
	var _t816 *pb.RelationId
	if prediction417 == 1 {
		uint128419 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t816 = &pb.RelationId{IdLow: uint128419.Low, IdHigh: uint128419.High}
	} else {
		var _t817 *pb.RelationId
		if prediction417 == 0 {
			p.consumeLiteral(":")
			symbol418 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t817 = p.relationIdFromString(symbol418)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t816 = _t817
	}
	return _t816
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t818 := p.parse_bindings()
	bindings420 := _t818
	_t819 := p.parse_formula()
	formula421 := _t819
	p.consumeLiteral(")")
	_t820 := &pb.Abstraction{Vars: listConcat(bindings420[0].([]*pb.Binding), bindings420[1].([]*pb.Binding)), Value: formula421}
	return _t820
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs422 := []*pb.Binding{}
	cond423 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond423 {
		_t821 := p.parse_binding()
		item424 := _t821
		xs422 = append(xs422, item424)
		cond423 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings425 := xs422
	var _t822 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t823 := p.parse_value_bindings()
		_t822 = _t823
	}
	value_bindings426 := _t822
	p.consumeLiteral("]")
	_t824 := value_bindings426
	if value_bindings426 == nil {
		_t824 = []*pb.Binding{}
	}
	return []interface{}{bindings425, _t824}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol427 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	_t825 := p.parse_type()
	type428 := _t825
	_t826 := &pb.Var{Name: symbol427}
	_t827 := &pb.Binding{Var: _t826, Type: type428}
	return _t827
}

func (p *Parser) parse_type() *pb.Type {
	var _t828 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t828 = 0
	} else {
		var _t829 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t829 = 4
		} else {
			var _t830 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t830 = 1
			} else {
				var _t831 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t831 = 8
				} else {
					var _t832 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t832 = 5
					} else {
						var _t833 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t833 = 2
						} else {
							var _t834 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t834 = 3
							} else {
								var _t835 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t835 = 7
								} else {
									var _t836 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t836 = 6
									} else {
										var _t837 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t837 = 10
										} else {
											var _t838 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t838 = 9
											} else {
												_t838 = -1
											}
											_t837 = _t838
										}
										_t836 = _t837
									}
									_t835 = _t836
								}
								_t834 = _t835
							}
							_t833 = _t834
						}
						_t832 = _t833
					}
					_t831 = _t832
				}
				_t830 = _t831
			}
			_t829 = _t830
		}
		_t828 = _t829
	}
	prediction429 := _t828
	var _t839 *pb.Type
	if prediction429 == 10 {
		_t840 := p.parse_boolean_type()
		boolean_type440 := _t840
		_t841 := &pb.Type{}
		_t841.Type = &pb.Type_BooleanType{BooleanType: boolean_type440}
		_t839 = _t841
	} else {
		var _t842 *pb.Type
		if prediction429 == 9 {
			_t843 := p.parse_decimal_type()
			decimal_type439 := _t843
			_t844 := &pb.Type{}
			_t844.Type = &pb.Type_DecimalType{DecimalType: decimal_type439}
			_t842 = _t844
		} else {
			var _t845 *pb.Type
			if prediction429 == 8 {
				_t846 := p.parse_missing_type()
				missing_type438 := _t846
				_t847 := &pb.Type{}
				_t847.Type = &pb.Type_MissingType{MissingType: missing_type438}
				_t845 = _t847
			} else {
				var _t848 *pb.Type
				if prediction429 == 7 {
					_t849 := p.parse_datetime_type()
					datetime_type437 := _t849
					_t850 := &pb.Type{}
					_t850.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type437}
					_t848 = _t850
				} else {
					var _t851 *pb.Type
					if prediction429 == 6 {
						_t852 := p.parse_date_type()
						date_type436 := _t852
						_t853 := &pb.Type{}
						_t853.Type = &pb.Type_DateType{DateType: date_type436}
						_t851 = _t853
					} else {
						var _t854 *pb.Type
						if prediction429 == 5 {
							_t855 := p.parse_int128_type()
							int128_type435 := _t855
							_t856 := &pb.Type{}
							_t856.Type = &pb.Type_Int128Type{Int128Type: int128_type435}
							_t854 = _t856
						} else {
							var _t857 *pb.Type
							if prediction429 == 4 {
								_t858 := p.parse_uint128_type()
								uint128_type434 := _t858
								_t859 := &pb.Type{}
								_t859.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type434}
								_t857 = _t859
							} else {
								var _t860 *pb.Type
								if prediction429 == 3 {
									_t861 := p.parse_float_type()
									float_type433 := _t861
									_t862 := &pb.Type{}
									_t862.Type = &pb.Type_FloatType{FloatType: float_type433}
									_t860 = _t862
								} else {
									var _t863 *pb.Type
									if prediction429 == 2 {
										_t864 := p.parse_int_type()
										int_type432 := _t864
										_t865 := &pb.Type{}
										_t865.Type = &pb.Type_IntType{IntType: int_type432}
										_t863 = _t865
									} else {
										var _t866 *pb.Type
										if prediction429 == 1 {
											_t867 := p.parse_string_type()
											string_type431 := _t867
											_t868 := &pb.Type{}
											_t868.Type = &pb.Type_StringType{StringType: string_type431}
											_t866 = _t868
										} else {
											var _t869 *pb.Type
											if prediction429 == 0 {
												_t870 := p.parse_unspecified_type()
												unspecified_type430 := _t870
												_t871 := &pb.Type{}
												_t871.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type430}
												_t869 = _t871
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t866 = _t869
										}
										_t863 = _t866
									}
									_t860 = _t863
								}
								_t857 = _t860
							}
							_t854 = _t857
						}
						_t851 = _t854
					}
					_t848 = _t851
				}
				_t845 = _t848
			}
			_t842 = _t845
		}
		_t839 = _t842
	}
	return _t839
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t872 := &pb.UnspecifiedType{}
	return _t872
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t873 := &pb.StringType{}
	return _t873
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t874 := &pb.IntType{}
	return _t874
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t875 := &pb.FloatType{}
	return _t875
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t876 := &pb.UInt128Type{}
	return _t876
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t877 := &pb.Int128Type{}
	return _t877
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t878 := &pb.DateType{}
	return _t878
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t879 := &pb.DateTimeType{}
	return _t879
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t880 := &pb.MissingType{}
	return _t880
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int441 := p.consumeTerminal("INT").Value.AsInt64()
	int_3442 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t881 := &pb.DecimalType{Precision: int32(int441), Scale: int32(int_3442)}
	return _t881
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t882 := &pb.BooleanType{}
	return _t882
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs443 := []*pb.Binding{}
	cond444 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond444 {
		_t883 := p.parse_binding()
		item445 := _t883
		xs443 = append(xs443, item445)
		cond444 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings446 := xs443
	return bindings446
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t884 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t885 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t885 = 0
		} else {
			var _t886 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t886 = 11
			} else {
				var _t887 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t887 = 3
				} else {
					var _t888 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t888 = 10
					} else {
						var _t889 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t889 = 9
						} else {
							var _t890 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t890 = 5
							} else {
								var _t891 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t891 = 6
								} else {
									var _t892 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t892 = 7
									} else {
										var _t893 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t893 = 1
										} else {
											var _t894 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t894 = 2
											} else {
												var _t895 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t895 = 12
												} else {
													var _t896 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t896 = 8
													} else {
														var _t897 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t897 = 4
														} else {
															var _t898 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t898 = 10
															} else {
																var _t899 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t899 = 10
																} else {
																	var _t900 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t900 = 10
																	} else {
																		var _t901 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t901 = 10
																		} else {
																			var _t902 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t902 = 10
																			} else {
																				var _t903 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t903 = 10
																				} else {
																					var _t904 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t904 = 10
																					} else {
																						var _t905 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t905 = 10
																						} else {
																							var _t906 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t906 = 10
																							} else {
																								_t906 = -1
																							}
																							_t905 = _t906
																						}
																						_t904 = _t905
																					}
																					_t903 = _t904
																				}
																				_t902 = _t903
																			}
																			_t901 = _t902
																		}
																		_t900 = _t901
																	}
																	_t899 = _t900
																}
																_t898 = _t899
															}
															_t897 = _t898
														}
														_t896 = _t897
													}
													_t895 = _t896
												}
												_t894 = _t895
											}
											_t893 = _t894
										}
										_t892 = _t893
									}
									_t891 = _t892
								}
								_t890 = _t891
							}
							_t889 = _t890
						}
						_t888 = _t889
					}
					_t887 = _t888
				}
				_t886 = _t887
			}
			_t885 = _t886
		}
		_t884 = _t885
	} else {
		_t884 = -1
	}
	prediction447 := _t884
	var _t907 *pb.Formula
	if prediction447 == 12 {
		_t908 := p.parse_cast()
		cast460 := _t908
		_t909 := &pb.Formula{}
		_t909.FormulaType = &pb.Formula_Cast{Cast: cast460}
		_t907 = _t909
	} else {
		var _t910 *pb.Formula
		if prediction447 == 11 {
			_t911 := p.parse_rel_atom()
			rel_atom459 := _t911
			_t912 := &pb.Formula{}
			_t912.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom459}
			_t910 = _t912
		} else {
			var _t913 *pb.Formula
			if prediction447 == 10 {
				_t914 := p.parse_primitive()
				primitive458 := _t914
				_t915 := &pb.Formula{}
				_t915.FormulaType = &pb.Formula_Primitive{Primitive: primitive458}
				_t913 = _t915
			} else {
				var _t916 *pb.Formula
				if prediction447 == 9 {
					_t917 := p.parse_pragma()
					pragma457 := _t917
					_t918 := &pb.Formula{}
					_t918.FormulaType = &pb.Formula_Pragma{Pragma: pragma457}
					_t916 = _t918
				} else {
					var _t919 *pb.Formula
					if prediction447 == 8 {
						_t920 := p.parse_atom()
						atom456 := _t920
						_t921 := &pb.Formula{}
						_t921.FormulaType = &pb.Formula_Atom{Atom: atom456}
						_t919 = _t921
					} else {
						var _t922 *pb.Formula
						if prediction447 == 7 {
							_t923 := p.parse_ffi()
							ffi455 := _t923
							_t924 := &pb.Formula{}
							_t924.FormulaType = &pb.Formula_Ffi{Ffi: ffi455}
							_t922 = _t924
						} else {
							var _t925 *pb.Formula
							if prediction447 == 6 {
								_t926 := p.parse_not()
								not454 := _t926
								_t927 := &pb.Formula{}
								_t927.FormulaType = &pb.Formula_Not{Not: not454}
								_t925 = _t927
							} else {
								var _t928 *pb.Formula
								if prediction447 == 5 {
									_t929 := p.parse_disjunction()
									disjunction453 := _t929
									_t930 := &pb.Formula{}
									_t930.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction453}
									_t928 = _t930
								} else {
									var _t931 *pb.Formula
									if prediction447 == 4 {
										_t932 := p.parse_conjunction()
										conjunction452 := _t932
										_t933 := &pb.Formula{}
										_t933.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction452}
										_t931 = _t933
									} else {
										var _t934 *pb.Formula
										if prediction447 == 3 {
											_t935 := p.parse_reduce()
											reduce451 := _t935
											_t936 := &pb.Formula{}
											_t936.FormulaType = &pb.Formula_Reduce{Reduce: reduce451}
											_t934 = _t936
										} else {
											var _t937 *pb.Formula
											if prediction447 == 2 {
												_t938 := p.parse_exists()
												exists450 := _t938
												_t939 := &pb.Formula{}
												_t939.FormulaType = &pb.Formula_Exists{Exists: exists450}
												_t937 = _t939
											} else {
												var _t940 *pb.Formula
												if prediction447 == 1 {
													_t941 := p.parse_false()
													false449 := _t941
													_t942 := &pb.Formula{}
													_t942.FormulaType = &pb.Formula_Disjunction{Disjunction: false449}
													_t940 = _t942
												} else {
													var _t943 *pb.Formula
													if prediction447 == 0 {
														_t944 := p.parse_true()
														true448 := _t944
														_t945 := &pb.Formula{}
														_t945.FormulaType = &pb.Formula_Conjunction{Conjunction: true448}
														_t943 = _t945
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t940 = _t943
												}
												_t937 = _t940
											}
											_t934 = _t937
										}
										_t931 = _t934
									}
									_t928 = _t931
								}
								_t925 = _t928
							}
							_t922 = _t925
						}
						_t919 = _t922
					}
					_t916 = _t919
				}
				_t913 = _t916
			}
			_t910 = _t913
		}
		_t907 = _t910
	}
	return _t907
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t946 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t946
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t947 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t947
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t948 := p.parse_bindings()
	bindings461 := _t948
	_t949 := p.parse_formula()
	formula462 := _t949
	p.consumeLiteral(")")
	_t950 := &pb.Abstraction{Vars: listConcat(bindings461[0].([]*pb.Binding), bindings461[1].([]*pb.Binding)), Value: formula462}
	_t951 := &pb.Exists{Body: _t950}
	return _t951
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t952 := p.parse_abstraction()
	abstraction463 := _t952
	_t953 := p.parse_abstraction()
	abstraction_3464 := _t953
	_t954 := p.parse_terms()
	terms465 := _t954
	p.consumeLiteral(")")
	_t955 := &pb.Reduce{Op: abstraction463, Body: abstraction_3464, Terms: terms465}
	return _t955
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs466 := []*pb.Term{}
	cond467 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond467 {
		_t956 := p.parse_term()
		item468 := _t956
		xs466 = append(xs466, item468)
		cond467 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms469 := xs466
	p.consumeLiteral(")")
	return terms469
}

func (p *Parser) parse_term() *pb.Term {
	var _t957 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t957 = 1
	} else {
		var _t958 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t958 = 1
		} else {
			var _t959 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t959 = 1
			} else {
				var _t960 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t960 = 1
				} else {
					var _t961 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t961 = 1
					} else {
						var _t962 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t962 = 0
						} else {
							var _t963 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t963 = 1
							} else {
								var _t964 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t964 = 1
								} else {
									var _t965 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t965 = 1
									} else {
										var _t966 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t966 = 1
										} else {
											var _t967 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t967 = 1
											} else {
												_t967 = -1
											}
											_t966 = _t967
										}
										_t965 = _t966
									}
									_t964 = _t965
								}
								_t963 = _t964
							}
							_t962 = _t963
						}
						_t961 = _t962
					}
					_t960 = _t961
				}
				_t959 = _t960
			}
			_t958 = _t959
		}
		_t957 = _t958
	}
	prediction470 := _t957
	var _t968 *pb.Term
	if prediction470 == 1 {
		_t969 := p.parse_constant()
		constant472 := _t969
		_t970 := &pb.Term{}
		_t970.TermType = &pb.Term_Constant{Constant: constant472}
		_t968 = _t970
	} else {
		var _t971 *pb.Term
		if prediction470 == 0 {
			_t972 := p.parse_var()
			var471 := _t972
			_t973 := &pb.Term{}
			_t973.TermType = &pb.Term_Var{Var: var471}
			_t971 = _t973
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t968 = _t971
	}
	return _t968
}

func (p *Parser) parse_var() *pb.Var {
	symbol473 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t974 := &pb.Var{Name: symbol473}
	return _t974
}

func (p *Parser) parse_constant() *pb.Value {
	_t975 := p.parse_value()
	value474 := _t975
	return value474
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs475 := []*pb.Formula{}
	cond476 := p.matchLookaheadLiteral("(", 0)
	for cond476 {
		_t976 := p.parse_formula()
		item477 := _t976
		xs475 = append(xs475, item477)
		cond476 = p.matchLookaheadLiteral("(", 0)
	}
	formulas478 := xs475
	p.consumeLiteral(")")
	_t977 := &pb.Conjunction{Args: formulas478}
	return _t977
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs479 := []*pb.Formula{}
	cond480 := p.matchLookaheadLiteral("(", 0)
	for cond480 {
		_t978 := p.parse_formula()
		item481 := _t978
		xs479 = append(xs479, item481)
		cond480 = p.matchLookaheadLiteral("(", 0)
	}
	formulas482 := xs479
	p.consumeLiteral(")")
	_t979 := &pb.Disjunction{Args: formulas482}
	return _t979
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t980 := p.parse_formula()
	formula483 := _t980
	p.consumeLiteral(")")
	_t981 := &pb.Not{Arg: formula483}
	return _t981
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t982 := p.parse_name()
	name484 := _t982
	_t983 := p.parse_ffi_args()
	ffi_args485 := _t983
	_t984 := p.parse_terms()
	terms486 := _t984
	p.consumeLiteral(")")
	_t985 := &pb.FFI{Name: name484, Args: ffi_args485, Terms: terms486}
	return _t985
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol487 := p.consumeTerminal("SYMBOL").Value.AsString()
	return symbol487
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs488 := []*pb.Abstraction{}
	cond489 := p.matchLookaheadLiteral("(", 0)
	for cond489 {
		_t986 := p.parse_abstraction()
		item490 := _t986
		xs488 = append(xs488, item490)
		cond489 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions491 := xs488
	p.consumeLiteral(")")
	return abstractions491
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t987 := p.parse_relation_id()
	relation_id492 := _t987
	xs493 := []*pb.Term{}
	cond494 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond494 {
		_t988 := p.parse_term()
		item495 := _t988
		xs493 = append(xs493, item495)
		cond494 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms496 := xs493
	p.consumeLiteral(")")
	_t989 := &pb.Atom{Name: relation_id492, Terms: terms496}
	return _t989
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t990 := p.parse_name()
	name497 := _t990
	xs498 := []*pb.Term{}
	cond499 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond499 {
		_t991 := p.parse_term()
		item500 := _t991
		xs498 = append(xs498, item500)
		cond499 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms501 := xs498
	p.consumeLiteral(")")
	_t992 := &pb.Pragma{Name: name497, Terms: terms501}
	return _t992
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t993 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t994 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t994 = 9
		} else {
			var _t995 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t995 = 4
			} else {
				var _t996 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t996 = 3
				} else {
					var _t997 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t997 = 0
					} else {
						var _t998 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t998 = 2
						} else {
							var _t999 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t999 = 1
							} else {
								var _t1000 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1000 = 8
								} else {
									var _t1001 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1001 = 6
									} else {
										var _t1002 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1002 = 5
										} else {
											var _t1003 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1003 = 7
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
	} else {
		_t993 = -1
	}
	prediction502 := _t993
	var _t1004 *pb.Primitive
	if prediction502 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1005 := p.parse_name()
		name512 := _t1005
		xs513 := []*pb.RelTerm{}
		cond514 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond514 {
			_t1006 := p.parse_rel_term()
			item515 := _t1006
			xs513 = append(xs513, item515)
			cond514 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms516 := xs513
		p.consumeLiteral(")")
		_t1007 := &pb.Primitive{Name: name512, Terms: rel_terms516}
		_t1004 = _t1007
	} else {
		var _t1008 *pb.Primitive
		if prediction502 == 8 {
			_t1009 := p.parse_divide()
			divide511 := _t1009
			_t1008 = divide511
		} else {
			var _t1010 *pb.Primitive
			if prediction502 == 7 {
				_t1011 := p.parse_multiply()
				multiply510 := _t1011
				_t1010 = multiply510
			} else {
				var _t1012 *pb.Primitive
				if prediction502 == 6 {
					_t1013 := p.parse_minus()
					minus509 := _t1013
					_t1012 = minus509
				} else {
					var _t1014 *pb.Primitive
					if prediction502 == 5 {
						_t1015 := p.parse_add()
						add508 := _t1015
						_t1014 = add508
					} else {
						var _t1016 *pb.Primitive
						if prediction502 == 4 {
							_t1017 := p.parse_gt_eq()
							gt_eq507 := _t1017
							_t1016 = gt_eq507
						} else {
							var _t1018 *pb.Primitive
							if prediction502 == 3 {
								_t1019 := p.parse_gt()
								gt506 := _t1019
								_t1018 = gt506
							} else {
								var _t1020 *pb.Primitive
								if prediction502 == 2 {
									_t1021 := p.parse_lt_eq()
									lt_eq505 := _t1021
									_t1020 = lt_eq505
								} else {
									var _t1022 *pb.Primitive
									if prediction502 == 1 {
										_t1023 := p.parse_lt()
										lt504 := _t1023
										_t1022 = lt504
									} else {
										var _t1024 *pb.Primitive
										if prediction502 == 0 {
											_t1025 := p.parse_eq()
											eq503 := _t1025
											_t1024 = eq503
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1022 = _t1024
									}
									_t1020 = _t1022
								}
								_t1018 = _t1020
							}
							_t1016 = _t1018
						}
						_t1014 = _t1016
					}
					_t1012 = _t1014
				}
				_t1010 = _t1012
			}
			_t1008 = _t1010
		}
		_t1004 = _t1008
	}
	return _t1004
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1026 := p.parse_term()
	term517 := _t1026
	_t1027 := p.parse_term()
	term_3518 := _t1027
	p.consumeLiteral(")")
	_t1028 := &pb.RelTerm{}
	_t1028.RelTermType = &pb.RelTerm_Term{Term: term517}
	_t1029 := &pb.RelTerm{}
	_t1029.RelTermType = &pb.RelTerm_Term{Term: term_3518}
	_t1030 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1028, _t1029}}
	return _t1030
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1031 := p.parse_term()
	term519 := _t1031
	_t1032 := p.parse_term()
	term_3520 := _t1032
	p.consumeLiteral(")")
	_t1033 := &pb.RelTerm{}
	_t1033.RelTermType = &pb.RelTerm_Term{Term: term519}
	_t1034 := &pb.RelTerm{}
	_t1034.RelTermType = &pb.RelTerm_Term{Term: term_3520}
	_t1035 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1033, _t1034}}
	return _t1035
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1036 := p.parse_term()
	term521 := _t1036
	_t1037 := p.parse_term()
	term_3522 := _t1037
	p.consumeLiteral(")")
	_t1038 := &pb.RelTerm{}
	_t1038.RelTermType = &pb.RelTerm_Term{Term: term521}
	_t1039 := &pb.RelTerm{}
	_t1039.RelTermType = &pb.RelTerm_Term{Term: term_3522}
	_t1040 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1038, _t1039}}
	return _t1040
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1041 := p.parse_term()
	term523 := _t1041
	_t1042 := p.parse_term()
	term_3524 := _t1042
	p.consumeLiteral(")")
	_t1043 := &pb.RelTerm{}
	_t1043.RelTermType = &pb.RelTerm_Term{Term: term523}
	_t1044 := &pb.RelTerm{}
	_t1044.RelTermType = &pb.RelTerm_Term{Term: term_3524}
	_t1045 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1043, _t1044}}
	return _t1045
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1046 := p.parse_term()
	term525 := _t1046
	_t1047 := p.parse_term()
	term_3526 := _t1047
	p.consumeLiteral(")")
	_t1048 := &pb.RelTerm{}
	_t1048.RelTermType = &pb.RelTerm_Term{Term: term525}
	_t1049 := &pb.RelTerm{}
	_t1049.RelTermType = &pb.RelTerm_Term{Term: term_3526}
	_t1050 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1048, _t1049}}
	return _t1050
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1051 := p.parse_term()
	term527 := _t1051
	_t1052 := p.parse_term()
	term_3528 := _t1052
	_t1053 := p.parse_term()
	term_4529 := _t1053
	p.consumeLiteral(")")
	_t1054 := &pb.RelTerm{}
	_t1054.RelTermType = &pb.RelTerm_Term{Term: term527}
	_t1055 := &pb.RelTerm{}
	_t1055.RelTermType = &pb.RelTerm_Term{Term: term_3528}
	_t1056 := &pb.RelTerm{}
	_t1056.RelTermType = &pb.RelTerm_Term{Term: term_4529}
	_t1057 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1054, _t1055, _t1056}}
	return _t1057
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1058 := p.parse_term()
	term530 := _t1058
	_t1059 := p.parse_term()
	term_3531 := _t1059
	_t1060 := p.parse_term()
	term_4532 := _t1060
	p.consumeLiteral(")")
	_t1061 := &pb.RelTerm{}
	_t1061.RelTermType = &pb.RelTerm_Term{Term: term530}
	_t1062 := &pb.RelTerm{}
	_t1062.RelTermType = &pb.RelTerm_Term{Term: term_3531}
	_t1063 := &pb.RelTerm{}
	_t1063.RelTermType = &pb.RelTerm_Term{Term: term_4532}
	_t1064 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1061, _t1062, _t1063}}
	return _t1064
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1065 := p.parse_term()
	term533 := _t1065
	_t1066 := p.parse_term()
	term_3534 := _t1066
	_t1067 := p.parse_term()
	term_4535 := _t1067
	p.consumeLiteral(")")
	_t1068 := &pb.RelTerm{}
	_t1068.RelTermType = &pb.RelTerm_Term{Term: term533}
	_t1069 := &pb.RelTerm{}
	_t1069.RelTermType = &pb.RelTerm_Term{Term: term_3534}
	_t1070 := &pb.RelTerm{}
	_t1070.RelTermType = &pb.RelTerm_Term{Term: term_4535}
	_t1071 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1068, _t1069, _t1070}}
	return _t1071
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1072 := p.parse_term()
	term536 := _t1072
	_t1073 := p.parse_term()
	term_3537 := _t1073
	_t1074 := p.parse_term()
	term_4538 := _t1074
	p.consumeLiteral(")")
	_t1075 := &pb.RelTerm{}
	_t1075.RelTermType = &pb.RelTerm_Term{Term: term536}
	_t1076 := &pb.RelTerm{}
	_t1076.RelTermType = &pb.RelTerm_Term{Term: term_3537}
	_t1077 := &pb.RelTerm{}
	_t1077.RelTermType = &pb.RelTerm_Term{Term: term_4538}
	_t1078 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1075, _t1076, _t1077}}
	return _t1078
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1079 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1079 = 1
	} else {
		var _t1080 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1080 = 1
		} else {
			var _t1081 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1081 = 1
			} else {
				var _t1082 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1082 = 1
				} else {
					var _t1083 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1083 = 0
					} else {
						var _t1084 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1084 = 1
						} else {
							var _t1085 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1085 = 1
							} else {
								var _t1086 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1086 = 1
								} else {
									var _t1087 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1087 = 1
									} else {
										var _t1088 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1088 = 1
										} else {
											var _t1089 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1089 = 1
											} else {
												var _t1090 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1090 = 1
												} else {
													_t1090 = -1
												}
												_t1089 = _t1090
											}
											_t1088 = _t1089
										}
										_t1087 = _t1088
									}
									_t1086 = _t1087
								}
								_t1085 = _t1086
							}
							_t1084 = _t1085
						}
						_t1083 = _t1084
					}
					_t1082 = _t1083
				}
				_t1081 = _t1082
			}
			_t1080 = _t1081
		}
		_t1079 = _t1080
	}
	prediction539 := _t1079
	var _t1091 *pb.RelTerm
	if prediction539 == 1 {
		_t1092 := p.parse_term()
		term541 := _t1092
		_t1093 := &pb.RelTerm{}
		_t1093.RelTermType = &pb.RelTerm_Term{Term: term541}
		_t1091 = _t1093
	} else {
		var _t1094 *pb.RelTerm
		if prediction539 == 0 {
			_t1095 := p.parse_specialized_value()
			specialized_value540 := _t1095
			_t1096 := &pb.RelTerm{}
			_t1096.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value540}
			_t1094 = _t1096
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1091 = _t1094
	}
	return _t1091
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1097 := p.parse_value()
	value542 := _t1097
	return value542
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1098 := p.parse_name()
	name543 := _t1098
	xs544 := []*pb.RelTerm{}
	cond545 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond545 {
		_t1099 := p.parse_rel_term()
		item546 := _t1099
		xs544 = append(xs544, item546)
		cond545 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms547 := xs544
	p.consumeLiteral(")")
	_t1100 := &pb.RelAtom{Name: name543, Terms: rel_terms547}
	return _t1100
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1101 := p.parse_term()
	term548 := _t1101
	_t1102 := p.parse_term()
	term_3549 := _t1102
	p.consumeLiteral(")")
	_t1103 := &pb.Cast{Input: term548, Result: term_3549}
	return _t1103
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs550 := []*pb.Attribute{}
	cond551 := p.matchLookaheadLiteral("(", 0)
	for cond551 {
		_t1104 := p.parse_attribute()
		item552 := _t1104
		xs550 = append(xs550, item552)
		cond551 = p.matchLookaheadLiteral("(", 0)
	}
	attributes553 := xs550
	p.consumeLiteral(")")
	return attributes553
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1105 := p.parse_name()
	name554 := _t1105
	xs555 := []*pb.Value{}
	cond556 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond556 {
		_t1106 := p.parse_value()
		item557 := _t1106
		xs555 = append(xs555, item557)
		cond556 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values558 := xs555
	p.consumeLiteral(")")
	_t1107 := &pb.Attribute{Name: name554, Args: values558}
	return _t1107
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs559 := []*pb.RelationId{}
	cond560 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond560 {
		_t1108 := p.parse_relation_id()
		item561 := _t1108
		xs559 = append(xs559, item561)
		cond560 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids562 := xs559
	_t1109 := p.parse_script()
	script563 := _t1109
	p.consumeLiteral(")")
	_t1110 := &pb.Algorithm{Global: relation_ids562, Body: script563}
	return _t1110
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs564 := []*pb.Construct{}
	cond565 := p.matchLookaheadLiteral("(", 0)
	for cond565 {
		_t1111 := p.parse_construct()
		item566 := _t1111
		xs564 = append(xs564, item566)
		cond565 = p.matchLookaheadLiteral("(", 0)
	}
	constructs567 := xs564
	p.consumeLiteral(")")
	_t1112 := &pb.Script{Constructs: constructs567}
	return _t1112
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1113 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1114 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1114 = 1
		} else {
			var _t1115 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1115 = 1
			} else {
				var _t1116 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1116 = 1
				} else {
					var _t1117 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1117 = 0
					} else {
						var _t1118 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1118 = 1
						} else {
							var _t1119 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1119 = 1
							} else {
								_t1119 = -1
							}
							_t1118 = _t1119
						}
						_t1117 = _t1118
					}
					_t1116 = _t1117
				}
				_t1115 = _t1116
			}
			_t1114 = _t1115
		}
		_t1113 = _t1114
	} else {
		_t1113 = -1
	}
	prediction568 := _t1113
	var _t1120 *pb.Construct
	if prediction568 == 1 {
		_t1121 := p.parse_instruction()
		instruction570 := _t1121
		_t1122 := &pb.Construct{}
		_t1122.ConstructType = &pb.Construct_Instruction{Instruction: instruction570}
		_t1120 = _t1122
	} else {
		var _t1123 *pb.Construct
		if prediction568 == 0 {
			_t1124 := p.parse_loop()
			loop569 := _t1124
			_t1125 := &pb.Construct{}
			_t1125.ConstructType = &pb.Construct_Loop{Loop: loop569}
			_t1123 = _t1125
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1120 = _t1123
	}
	return _t1120
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1126 := p.parse_init()
	init571 := _t1126
	_t1127 := p.parse_script()
	script572 := _t1127
	p.consumeLiteral(")")
	_t1128 := &pb.Loop{Init: init571, Body: script572}
	return _t1128
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs573 := []*pb.Instruction{}
	cond574 := p.matchLookaheadLiteral("(", 0)
	for cond574 {
		_t1129 := p.parse_instruction()
		item575 := _t1129
		xs573 = append(xs573, item575)
		cond574 = p.matchLookaheadLiteral("(", 0)
	}
	instructions576 := xs573
	p.consumeLiteral(")")
	return instructions576
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1130 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1131 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1131 = 1
		} else {
			var _t1132 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1132 = 4
			} else {
				var _t1133 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1133 = 3
				} else {
					var _t1134 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1134 = 2
					} else {
						var _t1135 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1135 = 0
						} else {
							_t1135 = -1
						}
						_t1134 = _t1135
					}
					_t1133 = _t1134
				}
				_t1132 = _t1133
			}
			_t1131 = _t1132
		}
		_t1130 = _t1131
	} else {
		_t1130 = -1
	}
	prediction577 := _t1130
	var _t1136 *pb.Instruction
	if prediction577 == 4 {
		_t1137 := p.parse_monus_def()
		monus_def582 := _t1137
		_t1138 := &pb.Instruction{}
		_t1138.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def582}
		_t1136 = _t1138
	} else {
		var _t1139 *pb.Instruction
		if prediction577 == 3 {
			_t1140 := p.parse_monoid_def()
			monoid_def581 := _t1140
			_t1141 := &pb.Instruction{}
			_t1141.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def581}
			_t1139 = _t1141
		} else {
			var _t1142 *pb.Instruction
			if prediction577 == 2 {
				_t1143 := p.parse_break()
				break580 := _t1143
				_t1144 := &pb.Instruction{}
				_t1144.InstrType = &pb.Instruction_Break{Break: break580}
				_t1142 = _t1144
			} else {
				var _t1145 *pb.Instruction
				if prediction577 == 1 {
					_t1146 := p.parse_upsert()
					upsert579 := _t1146
					_t1147 := &pb.Instruction{}
					_t1147.InstrType = &pb.Instruction_Upsert{Upsert: upsert579}
					_t1145 = _t1147
				} else {
					var _t1148 *pb.Instruction
					if prediction577 == 0 {
						_t1149 := p.parse_assign()
						assign578 := _t1149
						_t1150 := &pb.Instruction{}
						_t1150.InstrType = &pb.Instruction_Assign{Assign: assign578}
						_t1148 = _t1150
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1145 = _t1148
				}
				_t1142 = _t1145
			}
			_t1139 = _t1142
		}
		_t1136 = _t1139
	}
	return _t1136
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1151 := p.parse_relation_id()
	relation_id583 := _t1151
	_t1152 := p.parse_abstraction()
	abstraction584 := _t1152
	var _t1153 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1154 := p.parse_attrs()
		_t1153 = _t1154
	}
	attrs585 := _t1153
	p.consumeLiteral(")")
	_t1155 := attrs585
	if attrs585 == nil {
		_t1155 = []*pb.Attribute{}
	}
	_t1156 := &pb.Assign{Name: relation_id583, Body: abstraction584, Attrs: _t1155}
	return _t1156
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1157 := p.parse_relation_id()
	relation_id586 := _t1157
	_t1158 := p.parse_abstraction_with_arity()
	abstraction_with_arity587 := _t1158
	var _t1159 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1160 := p.parse_attrs()
		_t1159 = _t1160
	}
	attrs588 := _t1159
	p.consumeLiteral(")")
	_t1161 := attrs588
	if attrs588 == nil {
		_t1161 = []*pb.Attribute{}
	}
	_t1162 := &pb.Upsert{Name: relation_id586, Body: abstraction_with_arity587[0].(*pb.Abstraction), Attrs: _t1161, ValueArity: abstraction_with_arity587[1].(int64)}
	return _t1162
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1163 := p.parse_bindings()
	bindings589 := _t1163
	_t1164 := p.parse_formula()
	formula590 := _t1164
	p.consumeLiteral(")")
	_t1165 := &pb.Abstraction{Vars: listConcat(bindings589[0].([]*pb.Binding), bindings589[1].([]*pb.Binding)), Value: formula590}
	return []interface{}{_t1165, int64(len(bindings589[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1166 := p.parse_relation_id()
	relation_id591 := _t1166
	_t1167 := p.parse_abstraction()
	abstraction592 := _t1167
	var _t1168 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1169 := p.parse_attrs()
		_t1168 = _t1169
	}
	attrs593 := _t1168
	p.consumeLiteral(")")
	_t1170 := attrs593
	if attrs593 == nil {
		_t1170 = []*pb.Attribute{}
	}
	_t1171 := &pb.Break{Name: relation_id591, Body: abstraction592, Attrs: _t1170}
	return _t1171
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1172 := p.parse_monoid()
	monoid594 := _t1172
	_t1173 := p.parse_relation_id()
	relation_id595 := _t1173
	_t1174 := p.parse_abstraction_with_arity()
	abstraction_with_arity596 := _t1174
	var _t1175 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1176 := p.parse_attrs()
		_t1175 = _t1176
	}
	attrs597 := _t1175
	p.consumeLiteral(")")
	_t1177 := attrs597
	if attrs597 == nil {
		_t1177 = []*pb.Attribute{}
	}
	_t1178 := &pb.MonoidDef{Monoid: monoid594, Name: relation_id595, Body: abstraction_with_arity596[0].(*pb.Abstraction), Attrs: _t1177, ValueArity: abstraction_with_arity596[1].(int64)}
	return _t1178
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1179 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1180 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1180 = 3
		} else {
			var _t1181 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1181 = 0
			} else {
				var _t1182 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1182 = 1
				} else {
					var _t1183 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1183 = 2
					} else {
						_t1183 = -1
					}
					_t1182 = _t1183
				}
				_t1181 = _t1182
			}
			_t1180 = _t1181
		}
		_t1179 = _t1180
	} else {
		_t1179 = -1
	}
	prediction598 := _t1179
	var _t1184 *pb.Monoid
	if prediction598 == 3 {
		_t1185 := p.parse_sum_monoid()
		sum_monoid602 := _t1185
		_t1186 := &pb.Monoid{}
		_t1186.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid602}
		_t1184 = _t1186
	} else {
		var _t1187 *pb.Monoid
		if prediction598 == 2 {
			_t1188 := p.parse_max_monoid()
			max_monoid601 := _t1188
			_t1189 := &pb.Monoid{}
			_t1189.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid601}
			_t1187 = _t1189
		} else {
			var _t1190 *pb.Monoid
			if prediction598 == 1 {
				_t1191 := p.parse_min_monoid()
				min_monoid600 := _t1191
				_t1192 := &pb.Monoid{}
				_t1192.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid600}
				_t1190 = _t1192
			} else {
				var _t1193 *pb.Monoid
				if prediction598 == 0 {
					_t1194 := p.parse_or_monoid()
					or_monoid599 := _t1194
					_t1195 := &pb.Monoid{}
					_t1195.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid599}
					_t1193 = _t1195
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1190 = _t1193
			}
			_t1187 = _t1190
		}
		_t1184 = _t1187
	}
	return _t1184
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1196 := &pb.OrMonoid{}
	return _t1196
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1197 := p.parse_type()
	type603 := _t1197
	p.consumeLiteral(")")
	_t1198 := &pb.MinMonoid{Type: type603}
	return _t1198
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1199 := p.parse_type()
	type604 := _t1199
	p.consumeLiteral(")")
	_t1200 := &pb.MaxMonoid{Type: type604}
	return _t1200
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1201 := p.parse_type()
	type605 := _t1201
	p.consumeLiteral(")")
	_t1202 := &pb.SumMonoid{Type: type605}
	return _t1202
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1203 := p.parse_monoid()
	monoid606 := _t1203
	_t1204 := p.parse_relation_id()
	relation_id607 := _t1204
	_t1205 := p.parse_abstraction_with_arity()
	abstraction_with_arity608 := _t1205
	var _t1206 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1207 := p.parse_attrs()
		_t1206 = _t1207
	}
	attrs609 := _t1206
	p.consumeLiteral(")")
	_t1208 := attrs609
	if attrs609 == nil {
		_t1208 = []*pb.Attribute{}
	}
	_t1209 := &pb.MonusDef{Monoid: monoid606, Name: relation_id607, Body: abstraction_with_arity608[0].(*pb.Abstraction), Attrs: _t1208, ValueArity: abstraction_with_arity608[1].(int64)}
	return _t1209
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1210 := p.parse_relation_id()
	relation_id610 := _t1210
	_t1211 := p.parse_abstraction()
	abstraction611 := _t1211
	_t1212 := p.parse_functional_dependency_keys()
	functional_dependency_keys612 := _t1212
	_t1213 := p.parse_functional_dependency_values()
	functional_dependency_values613 := _t1213
	p.consumeLiteral(")")
	_t1214 := &pb.FunctionalDependency{Guard: abstraction611, Keys: functional_dependency_keys612, Values: functional_dependency_values613}
	_t1215 := &pb.Constraint{Name: relation_id610}
	_t1215.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1214}
	return _t1215
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs614 := []*pb.Var{}
	cond615 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond615 {
		_t1216 := p.parse_var()
		item616 := _t1216
		xs614 = append(xs614, item616)
		cond615 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars617 := xs614
	p.consumeLiteral(")")
	return vars617
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs618 := []*pb.Var{}
	cond619 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond619 {
		_t1217 := p.parse_var()
		item620 := _t1217
		xs618 = append(xs618, item620)
		cond619 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars621 := xs618
	p.consumeLiteral(")")
	return vars621
}

func (p *Parser) parse_data() *pb.Data {
	var _t1218 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1219 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1219 = 0
		} else {
			var _t1220 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1220 = 2
			} else {
				var _t1221 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1221 = 1
				} else {
					_t1221 = -1
				}
				_t1220 = _t1221
			}
			_t1219 = _t1220
		}
		_t1218 = _t1219
	} else {
		_t1218 = -1
	}
	prediction622 := _t1218
	var _t1222 *pb.Data
	if prediction622 == 2 {
		_t1223 := p.parse_csv_data()
		csv_data625 := _t1223
		_t1224 := &pb.Data{}
		_t1224.DataType = &pb.Data_CsvData{CsvData: csv_data625}
		_t1222 = _t1224
	} else {
		var _t1225 *pb.Data
		if prediction622 == 1 {
			_t1226 := p.parse_betree_relation()
			betree_relation624 := _t1226
			_t1227 := &pb.Data{}
			_t1227.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation624}
			_t1225 = _t1227
		} else {
			var _t1228 *pb.Data
			if prediction622 == 0 {
				_t1229 := p.parse_rel_edb()
				rel_edb623 := _t1229
				_t1230 := &pb.Data{}
				_t1230.DataType = &pb.Data_RelEdb{RelEdb: rel_edb623}
				_t1228 = _t1230
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1225 = _t1228
		}
		_t1222 = _t1225
	}
	return _t1222
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1231 := p.parse_relation_id()
	relation_id626 := _t1231
	_t1232 := p.parse_rel_edb_path()
	rel_edb_path627 := _t1232
	_t1233 := p.parse_rel_edb_types()
	rel_edb_types628 := _t1233
	p.consumeLiteral(")")
	_t1234 := &pb.RelEDB{TargetId: relation_id626, Path: rel_edb_path627, Types: rel_edb_types628}
	return _t1234
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs629 := []string{}
	cond630 := p.matchLookaheadTerminal("STRING", 0)
	for cond630 {
		item631 := p.consumeTerminal("STRING").Value.AsString()
		xs629 = append(xs629, item631)
		cond630 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings632 := xs629
	p.consumeLiteral("]")
	return strings632
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs633 := []*pb.Type{}
	cond634 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond634 {
		_t1235 := p.parse_type()
		item635 := _t1235
		xs633 = append(xs633, item635)
		cond634 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types636 := xs633
	p.consumeLiteral("]")
	return types636
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1236 := p.parse_relation_id()
	relation_id637 := _t1236
	_t1237 := p.parse_betree_info()
	betree_info638 := _t1237
	p.consumeLiteral(")")
	_t1238 := &pb.BeTreeRelation{Name: relation_id637, RelationInfo: betree_info638}
	return _t1238
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1239 := p.parse_betree_info_key_types()
	betree_info_key_types639 := _t1239
	_t1240 := p.parse_betree_info_value_types()
	betree_info_value_types640 := _t1240
	_t1241 := p.parse_config_dict()
	config_dict641 := _t1241
	p.consumeLiteral(")")
	_t1242 := p.construct_betree_info(betree_info_key_types639, betree_info_value_types640, config_dict641)
	return _t1242
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs642 := []*pb.Type{}
	cond643 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond643 {
		_t1243 := p.parse_type()
		item644 := _t1243
		xs642 = append(xs642, item644)
		cond643 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types645 := xs642
	p.consumeLiteral(")")
	return types645
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs646 := []*pb.Type{}
	cond647 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond647 {
		_t1244 := p.parse_type()
		item648 := _t1244
		xs646 = append(xs646, item648)
		cond647 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types649 := xs646
	p.consumeLiteral(")")
	return types649
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1245 := p.parse_csvlocator()
	csvlocator650 := _t1245
	_t1246 := p.parse_csv_config()
	csv_config651 := _t1246
	_t1247 := p.parse_csv_columns()
	csv_columns652 := _t1247
	_t1248 := p.parse_csv_asof()
	csv_asof653 := _t1248
	p.consumeLiteral(")")
	_t1249 := &pb.CSVData{Locator: csvlocator650, Config: csv_config651, Columns: csv_columns652, Asof: csv_asof653}
	return _t1249
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1250 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1251 := p.parse_csv_locator_paths()
		_t1250 = _t1251
	}
	csv_locator_paths654 := _t1250
	var _t1252 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1253 := p.parse_csv_locator_inline_data()
		_t1252 = ptr(_t1253)
	}
	csv_locator_inline_data655 := _t1252
	p.consumeLiteral(")")
	_t1254 := csv_locator_paths654
	if csv_locator_paths654 == nil {
		_t1254 = []string{}
	}
	_t1255 := &pb.CSVLocator{Paths: _t1254, InlineData: []byte(deref(csv_locator_inline_data655, ""))}
	return _t1255
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs656 := []string{}
	cond657 := p.matchLookaheadTerminal("STRING", 0)
	for cond657 {
		item658 := p.consumeTerminal("STRING").Value.AsString()
		xs656 = append(xs656, item658)
		cond657 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings659 := xs656
	p.consumeLiteral(")")
	return strings659
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string660 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string660
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1256 := p.parse_config_dict()
	config_dict661 := _t1256
	p.consumeLiteral(")")
	_t1257 := p.construct_csv_config(config_dict661)
	return _t1257
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs662 := []*pb.CSVColumn{}
	cond663 := p.matchLookaheadLiteral("(", 0)
	for cond663 {
		_t1258 := p.parse_csv_column()
		item664 := _t1258
		xs662 = append(xs662, item664)
		cond663 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns665 := xs662
	p.consumeLiteral(")")
	return csv_columns665
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string666 := p.consumeTerminal("STRING").Value.AsString()
	_t1259 := p.parse_relation_id()
	relation_id667 := _t1259
	p.consumeLiteral("[")
	xs668 := []*pb.Type{}
	cond669 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond669 {
		_t1260 := p.parse_type()
		item670 := _t1260
		xs668 = append(xs668, item670)
		cond669 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types671 := xs668
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1261 := &pb.CSVColumn{ColumnName: string666, TargetId: relation_id667, Types: types671}
	return _t1261
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string672 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string672
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1262 := p.parse_fragment_id()
	fragment_id673 := _t1262
	p.consumeLiteral(")")
	_t1263 := &pb.Undefine{FragmentId: fragment_id673}
	return _t1263
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs674 := []*pb.RelationId{}
	cond675 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond675 {
		_t1264 := p.parse_relation_id()
		item676 := _t1264
		xs674 = append(xs674, item676)
		cond675 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids677 := xs674
	p.consumeLiteral(")")
	_t1265 := &pb.Context{Relations: relation_ids677}
	return _t1265
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs678 := []*pb.Read{}
	cond679 := p.matchLookaheadLiteral("(", 0)
	for cond679 {
		_t1266 := p.parse_read()
		item680 := _t1266
		xs678 = append(xs678, item680)
		cond679 = p.matchLookaheadLiteral("(", 0)
	}
	reads681 := xs678
	p.consumeLiteral(")")
	return reads681
}

func (p *Parser) parse_read() *pb.Read {
	var _t1267 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1268 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1268 = 2
		} else {
			var _t1269 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1269 = 1
			} else {
				var _t1270 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1270 = 4
				} else {
					var _t1271 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1271 = 0
					} else {
						var _t1272 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1272 = 3
						} else {
							_t1272 = -1
						}
						_t1271 = _t1272
					}
					_t1270 = _t1271
				}
				_t1269 = _t1270
			}
			_t1268 = _t1269
		}
		_t1267 = _t1268
	} else {
		_t1267 = -1
	}
	prediction682 := _t1267
	var _t1273 *pb.Read
	if prediction682 == 4 {
		_t1274 := p.parse_export()
		export687 := _t1274
		_t1275 := &pb.Read{}
		_t1275.ReadType = &pb.Read_Export{Export: export687}
		_t1273 = _t1275
	} else {
		var _t1276 *pb.Read
		if prediction682 == 3 {
			_t1277 := p.parse_abort()
			abort686 := _t1277
			_t1278 := &pb.Read{}
			_t1278.ReadType = &pb.Read_Abort{Abort: abort686}
			_t1276 = _t1278
		} else {
			var _t1279 *pb.Read
			if prediction682 == 2 {
				_t1280 := p.parse_what_if()
				what_if685 := _t1280
				_t1281 := &pb.Read{}
				_t1281.ReadType = &pb.Read_WhatIf{WhatIf: what_if685}
				_t1279 = _t1281
			} else {
				var _t1282 *pb.Read
				if prediction682 == 1 {
					_t1283 := p.parse_output()
					output684 := _t1283
					_t1284 := &pb.Read{}
					_t1284.ReadType = &pb.Read_Output{Output: output684}
					_t1282 = _t1284
				} else {
					var _t1285 *pb.Read
					if prediction682 == 0 {
						_t1286 := p.parse_demand()
						demand683 := _t1286
						_t1287 := &pb.Read{}
						_t1287.ReadType = &pb.Read_Demand{Demand: demand683}
						_t1285 = _t1287
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1282 = _t1285
				}
				_t1279 = _t1282
			}
			_t1276 = _t1279
		}
		_t1273 = _t1276
	}
	return _t1273
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1288 := p.parse_relation_id()
	relation_id688 := _t1288
	p.consumeLiteral(")")
	_t1289 := &pb.Demand{RelationId: relation_id688}
	return _t1289
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1290 := p.parse_name()
	name689 := _t1290
	_t1291 := p.parse_relation_id()
	relation_id690 := _t1291
	p.consumeLiteral(")")
	_t1292 := &pb.Output{Name: name689, RelationId: relation_id690}
	return _t1292
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1293 := p.parse_name()
	name691 := _t1293
	_t1294 := p.parse_epoch()
	epoch692 := _t1294
	p.consumeLiteral(")")
	_t1295 := &pb.WhatIf{Branch: name691, Epoch: epoch692}
	return _t1295
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1296 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1297 := p.parse_name()
		_t1296 = ptr(_t1297)
	}
	name693 := _t1296
	_t1298 := p.parse_relation_id()
	relation_id694 := _t1298
	p.consumeLiteral(")")
	_t1299 := &pb.Abort{Name: deref(name693, "abort"), RelationId: relation_id694}
	return _t1299
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1300 := p.parse_export_csv_config()
	export_csv_config695 := _t1300
	p.consumeLiteral(")")
	_t1301 := &pb.Export{}
	_t1301.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config695}
	return _t1301
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1302 := p.parse_export_csv_path()
	export_csv_path696 := _t1302
	_t1303 := p.parse_export_csv_columns()
	export_csv_columns697 := _t1303
	_t1304 := p.parse_config_dict()
	config_dict698 := _t1304
	p.consumeLiteral(")")
	_t1305 := p.export_csv_config(export_csv_path696, export_csv_columns697, config_dict698)
	return _t1305
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string699 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string699
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs700 := []*pb.ExportCSVColumn{}
	cond701 := p.matchLookaheadLiteral("(", 0)
	for cond701 {
		_t1306 := p.parse_export_csv_column()
		item702 := _t1306
		xs700 = append(xs700, item702)
		cond701 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns703 := xs700
	p.consumeLiteral(")")
	return export_csv_columns703
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string704 := p.consumeTerminal("STRING").Value.AsString()
	_t1307 := p.parse_relation_id()
	relation_id705 := _t1307
	p.consumeLiteral(")")
	_t1308 := &pb.ExportCSVColumn{ColumnName: string704, ColumnData: relation_id705}
	return _t1308
}


// Parse parses the input string and returns the result
func Parse(input string) (result *pb.Transaction, err error) {
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
	parser := NewParser(lexer.tokens)
	result = parser.parse_transaction()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, nil
}
