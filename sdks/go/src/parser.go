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
	_t966 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t966
	_t967 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t967
	_t968 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t968
	_t969 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t969
	_t970 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t970
	_t971 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t971
	_t972 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t972
	_t973 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t973
	_t974 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t974
	_t975 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t975
	_t976 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t976
	_t977 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t977
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t978 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t978
	_t979 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t979
	_t980 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t980
	_t981 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t981
	_t982 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t982
	_t983 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t983
	_t984 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t984
	_t985 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t985
	_t986 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t986
	_t987 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t987.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t987.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t987
	_t988 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t988
}

func (p *Parser) default_configure() *pb.Configure {
	_t989 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t989
	_t990 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t990
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
	_t991 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t991
	_t992 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t992
	_t993 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t993
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t994 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t994
	_t995 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t995
	_t996 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t996
	_t997 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t997
	_t998 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t998
	_t999 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t999
	_t1000 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1000
	_t1001 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1001
}

func (p *Parser) _make_value_int32(v int32) *pb.Value {
	_t1002 := &pb.Value{}
	_t1002.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1002
}

func (p *Parser) _make_value_int64(v int64) *pb.Value {
	_t1003 := &pb.Value{}
	_t1003.Value = &pb.Value_IntValue{IntValue: v}
	return _t1003
}

func (p *Parser) _make_value_float64(v float64) *pb.Value {
	_t1004 := &pb.Value{}
	_t1004.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1004
}

func (p *Parser) _make_value_string(v string) *pb.Value {
	_t1005 := &pb.Value{}
	_t1005.Value = &pb.Value_StringValue{StringValue: v}
	return _t1005
}

func (p *Parser) _make_value_boolean(v bool) *pb.Value {
	_t1006 := &pb.Value{}
	_t1006.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1006
}

func (p *Parser) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1007 := &pb.Value{}
	_t1007.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1007
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
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1008 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1008})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1009 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1009})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1010 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1010})
			}
		}
	}
	_t1011 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1011})
	return listSort(result)
}

func (p *Parser) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1012 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1012})
	_t1013 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1013})
	if msg.GetNewLine() != "" {
		_t1014 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1014})
	}
	_t1015 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1015})
	_t1016 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1016})
	_t1017 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1017})
	if msg.GetComment() != "" {
		_t1018 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1018})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1019 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1019})
	}
	_t1020 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1020})
	_t1021 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1021})
	_t1022 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1022})
	return listSort(result)
}

func (p *Parser) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1023 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1023})
	_t1024 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1024})
	_t1025 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1025})
	_t1026 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1026})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1027 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1027})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1028 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1028})
		}
	}
	_t1029 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1029})
	_t1030 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1030})
	return listSort(result)
}

func (p *Parser) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1031 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1031})
	}
	if msg.Compression != nil {
		_t1032 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1032})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1033 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1033})
	}
	if msg.SyntaxMissingString != nil {
		_t1034 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1034})
	}
	if msg.SyntaxDelim != nil {
		_t1035 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1035})
	}
	if msg.SyntaxQuotechar != nil {
		_t1036 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1036})
	}
	if msg.SyntaxEscapechar != nil {
		_t1037 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1037})
	}
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
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t356 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t357 := p.parse_configure()
		_t356 = _t357
	}
	configure0 := _t356
	var _t358 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t359 := p.parse_sync()
		_t358 = _t359
	}
	sync1 := _t358
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	for cond3 {
		_t360 := p.parse_epoch()
		item4 := _t360
		xs2 = append(xs2, item4)
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	epochs5 := xs2
	p.consumeLiteral(")")
	_t361 := p.default_configure()
	_t362 := configure0
	if configure0 == nil {
		_t362 = _t361
	}
	_t363 := &pb.Transaction{Epochs: epochs5, Configure: _t362, Sync: sync1}
	return _t363
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t364 := p.parse_config_dict()
	config_dict6 := _t364
	p.consumeLiteral(")")
	_t365 := p.construct_configure(config_dict6)
	return _t365
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs7 := [][]interface{}{}
	cond8 := p.matchLookaheadLiteral(":", 0)
	for cond8 {
		_t366 := p.parse_config_key_value()
		item9 := _t366
		xs7 = append(xs7, item9)
		cond8 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values10 := xs7
	p.consumeLiteral("}")
	return config_key_values10
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol11 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t367 := p.parse_value()
	value12 := _t367
	return []interface{}{symbol11, value12}
}

func (p *Parser) parse_value() *pb.Value {
	var _t368 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t368 = 9
	} else {
		var _t369 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t369 = 8
		} else {
			var _t370 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t370 = 9
			} else {
				var _t371 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t372 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t372 = 1
					} else {
						var _t373 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t373 = 0
						} else {
							_t373 = -1
						}
						_t372 = _t373
					}
					_t371 = _t372
				} else {
					var _t374 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t374 = 5
					} else {
						var _t375 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t375 = 2
						} else {
							var _t376 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t376 = 6
							} else {
								var _t377 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t377 = 3
								} else {
									var _t378 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t378 = 4
									} else {
										var _t379 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t379 = 7
										} else {
											_t379 = -1
										}
										_t378 = _t379
									}
									_t377 = _t378
								}
								_t376 = _t377
							}
							_t375 = _t376
						}
						_t374 = _t375
					}
					_t371 = _t374
				}
				_t370 = _t371
			}
			_t369 = _t370
		}
		_t368 = _t369
	}
	prediction13 := _t368
	var _t380 *pb.Value
	if prediction13 == 9 {
		_t381 := p.parse_boolean_value()
		boolean_value22 := _t381
		_t382 := &pb.Value{}
		_t382.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value22}
		_t380 = _t382
	} else {
		var _t383 *pb.Value
		if prediction13 == 8 {
			p.consumeLiteral("missing")
			_t384 := &pb.MissingValue{}
			_t385 := &pb.Value{}
			_t385.Value = &pb.Value_MissingValue{MissingValue: _t384}
			_t383 = _t385
		} else {
			var _t386 *pb.Value
			if prediction13 == 7 {
				decimal21 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t387 := &pb.Value{}
				_t387.Value = &pb.Value_DecimalValue{DecimalValue: decimal21}
				_t386 = _t387
			} else {
				var _t388 *pb.Value
				if prediction13 == 6 {
					int12820 := p.consumeTerminal("INT128").Value.AsInt128()
					_t389 := &pb.Value{}
					_t389.Value = &pb.Value_Int128Value{Int128Value: int12820}
					_t388 = _t389
				} else {
					var _t390 *pb.Value
					if prediction13 == 5 {
						uint12819 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t391 := &pb.Value{}
						_t391.Value = &pb.Value_Uint128Value{Uint128Value: uint12819}
						_t390 = _t391
					} else {
						var _t392 *pb.Value
						if prediction13 == 4 {
							float18 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t393 := &pb.Value{}
							_t393.Value = &pb.Value_FloatValue{FloatValue: float18}
							_t392 = _t393
						} else {
							var _t394 *pb.Value
							if prediction13 == 3 {
								int17 := p.consumeTerminal("INT").Value.AsInt64()
								_t395 := &pb.Value{}
								_t395.Value = &pb.Value_IntValue{IntValue: int17}
								_t394 = _t395
							} else {
								var _t396 *pb.Value
								if prediction13 == 2 {
									string16 := p.consumeTerminal("STRING").Value.AsString()
									_t397 := &pb.Value{}
									_t397.Value = &pb.Value_StringValue{StringValue: string16}
									_t396 = _t397
								} else {
									var _t398 *pb.Value
									if prediction13 == 1 {
										_t399 := p.parse_datetime()
										datetime15 := _t399
										_t400 := &pb.Value{}
										_t400.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime15}
										_t398 = _t400
									} else {
										var _t401 *pb.Value
										if prediction13 == 0 {
											_t402 := p.parse_date()
											date14 := _t402
											_t403 := &pb.Value{}
											_t403.Value = &pb.Value_DateValue{DateValue: date14}
											_t401 = _t403
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t398 = _t401
									}
									_t396 = _t398
								}
								_t394 = _t396
							}
							_t392 = _t394
						}
						_t390 = _t392
					}
					_t388 = _t390
				}
				_t386 = _t388
			}
			_t383 = _t386
		}
		_t380 = _t383
	}
	return _t380
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int23 := p.consumeTerminal("INT").Value.AsInt64()
	int_324 := p.consumeTerminal("INT").Value.AsInt64()
	int_425 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t404 := &pb.DateValue{Year: int32(int23), Month: int32(int_324), Day: int32(int_425)}
	return _t404
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int26 := p.consumeTerminal("INT").Value.AsInt64()
	int_327 := p.consumeTerminal("INT").Value.AsInt64()
	int_428 := p.consumeTerminal("INT").Value.AsInt64()
	int_529 := p.consumeTerminal("INT").Value.AsInt64()
	int_630 := p.consumeTerminal("INT").Value.AsInt64()
	int_731 := p.consumeTerminal("INT").Value.AsInt64()
	var _t405 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t405 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_832 := _t405
	p.consumeLiteral(")")
	_t406 := &pb.DateTimeValue{Year: int32(int26), Month: int32(int_327), Day: int32(int_428), Hour: int32(int_529), Minute: int32(int_630), Second: int32(int_731), Microsecond: int32(deref(int_832, 0))}
	return _t406
}

func (p *Parser) parse_boolean_value() bool {
	var _t407 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t407 = 0
	} else {
		var _t408 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t408 = 1
		} else {
			_t408 = -1
		}
		_t407 = _t408
	}
	prediction33 := _t407
	var _t409 bool
	if prediction33 == 1 {
		p.consumeLiteral("false")
		_t409 = false
	} else {
		var _t410 bool
		if prediction33 == 0 {
			p.consumeLiteral("true")
			_t410 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t409 = _t410
	}
	return _t409
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs34 := []*pb.FragmentId{}
	cond35 := p.matchLookaheadLiteral(":", 0)
	for cond35 {
		_t411 := p.parse_fragment_id()
		item36 := _t411
		xs34 = append(xs34, item36)
		cond35 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids37 := xs34
	p.consumeLiteral(")")
	_t412 := &pb.Sync{Fragments: fragment_ids37}
	return _t412
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol38 := p.consumeTerminal("SYMBOL").Value.AsString()
	return &pb.FragmentId{Id: []byte(symbol38)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t413 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t414 := p.parse_epoch_writes()
		_t413 = _t414
	}
	epoch_writes39 := _t413
	var _t415 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t416 := p.parse_epoch_reads()
		_t415 = _t416
	}
	epoch_reads40 := _t415
	p.consumeLiteral(")")
	_t417 := epoch_writes39
	if epoch_writes39 == nil {
		_t417 = []*pb.Write{}
	}
	_t418 := epoch_reads40
	if epoch_reads40 == nil {
		_t418 = []*pb.Read{}
	}
	_t419 := &pb.Epoch{Writes: _t417, Reads: _t418}
	return _t419
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs41 := []*pb.Write{}
	cond42 := p.matchLookaheadLiteral("(", 0)
	for cond42 {
		_t420 := p.parse_write()
		item43 := _t420
		xs41 = append(xs41, item43)
		cond42 = p.matchLookaheadLiteral("(", 0)
	}
	writes44 := xs41
	p.consumeLiteral(")")
	return writes44
}

func (p *Parser) parse_write() *pb.Write {
	var _t421 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t422 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t422 = 1
		} else {
			var _t423 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t423 = 3
			} else {
				var _t424 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t424 = 0
				} else {
					var _t425 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t425 = 2
					} else {
						_t425 = -1
					}
					_t424 = _t425
				}
				_t423 = _t424
			}
			_t422 = _t423
		}
		_t421 = _t422
	} else {
		_t421 = -1
	}
	prediction45 := _t421
	var _t426 *pb.Write
	if prediction45 == 3 {
		_t427 := p.parse_snapshot()
		snapshot49 := _t427
		_t428 := &pb.Write{}
		_t428.WriteType = &pb.Write_Snapshot{Snapshot: snapshot49}
		_t426 = _t428
	} else {
		var _t429 *pb.Write
		if prediction45 == 2 {
			_t430 := p.parse_context()
			context48 := _t430
			_t431 := &pb.Write{}
			_t431.WriteType = &pb.Write_Context{Context: context48}
			_t429 = _t431
		} else {
			var _t432 *pb.Write
			if prediction45 == 1 {
				_t433 := p.parse_undefine()
				undefine47 := _t433
				_t434 := &pb.Write{}
				_t434.WriteType = &pb.Write_Undefine{Undefine: undefine47}
				_t432 = _t434
			} else {
				var _t435 *pb.Write
				if prediction45 == 0 {
					_t436 := p.parse_define()
					define46 := _t436
					_t437 := &pb.Write{}
					_t437.WriteType = &pb.Write_Define{Define: define46}
					_t435 = _t437
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t432 = _t435
			}
			_t429 = _t432
		}
		_t426 = _t429
	}
	return _t426
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t438 := p.parse_fragment()
	fragment50 := _t438
	p.consumeLiteral(")")
	_t439 := &pb.Define{Fragment: fragment50}
	return _t439
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t440 := p.parse_new_fragment_id()
	new_fragment_id51 := _t440
	xs52 := []*pb.Declaration{}
	cond53 := p.matchLookaheadLiteral("(", 0)
	for cond53 {
		_t441 := p.parse_declaration()
		item54 := _t441
		xs52 = append(xs52, item54)
		cond53 = p.matchLookaheadLiteral("(", 0)
	}
	declarations55 := xs52
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id51, declarations55)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t442 := p.parse_fragment_id()
	fragment_id56 := _t442
	p.startFragment(fragment_id56)
	return fragment_id56
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t443 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t444 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t444 = 3
		} else {
			var _t445 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t445 = 2
			} else {
				var _t446 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t446 = 0
				} else {
					var _t447 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t447 = 3
					} else {
						var _t448 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t448 = 3
						} else {
							var _t449 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t449 = 1
							} else {
								_t449 = -1
							}
							_t448 = _t449
						}
						_t447 = _t448
					}
					_t446 = _t447
				}
				_t445 = _t446
			}
			_t444 = _t445
		}
		_t443 = _t444
	} else {
		_t443 = -1
	}
	prediction57 := _t443
	var _t450 *pb.Declaration
	if prediction57 == 3 {
		_t451 := p.parse_data()
		data61 := _t451
		_t452 := &pb.Declaration{}
		_t452.DeclarationType = &pb.Declaration_Data{Data: data61}
		_t450 = _t452
	} else {
		var _t453 *pb.Declaration
		if prediction57 == 2 {
			_t454 := p.parse_constraint()
			constraint60 := _t454
			_t455 := &pb.Declaration{}
			_t455.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint60}
			_t453 = _t455
		} else {
			var _t456 *pb.Declaration
			if prediction57 == 1 {
				_t457 := p.parse_algorithm()
				algorithm59 := _t457
				_t458 := &pb.Declaration{}
				_t458.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm59}
				_t456 = _t458
			} else {
				var _t459 *pb.Declaration
				if prediction57 == 0 {
					_t460 := p.parse_def()
					def58 := _t460
					_t461 := &pb.Declaration{}
					_t461.DeclarationType = &pb.Declaration_Def{Def: def58}
					_t459 = _t461
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t456 = _t459
			}
			_t453 = _t456
		}
		_t450 = _t453
	}
	return _t450
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t462 := p.parse_relation_id()
	relation_id62 := _t462
	_t463 := p.parse_abstraction()
	abstraction63 := _t463
	var _t464 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t465 := p.parse_attrs()
		_t464 = _t465
	}
	attrs64 := _t464
	p.consumeLiteral(")")
	_t466 := attrs64
	if attrs64 == nil {
		_t466 = []*pb.Attribute{}
	}
	_t467 := &pb.Def{Name: relation_id62, Body: abstraction63, Attrs: _t466}
	return _t467
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t468 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t468 = 0
	} else {
		var _t469 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t469 = 1
		} else {
			_t469 = -1
		}
		_t468 = _t469
	}
	prediction65 := _t468
	var _t470 *pb.RelationId
	if prediction65 == 1 {
		uint12867 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t470 = &pb.RelationId{IdLow: uint12867.Low, IdHigh: uint12867.High}
	} else {
		var _t471 *pb.RelationId
		if prediction65 == 0 {
			p.consumeLiteral(":")
			symbol66 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t471 = p.relationIdFromString(symbol66)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t470 = _t471
	}
	return _t470
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t472 := p.parse_bindings()
	bindings68 := _t472
	_t473 := p.parse_formula()
	formula69 := _t473
	p.consumeLiteral(")")
	_t474 := &pb.Abstraction{Vars: listConcat(bindings68[0].([]*pb.Binding), bindings68[1].([]*pb.Binding)), Value: formula69}
	return _t474
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs70 := []*pb.Binding{}
	cond71 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond71 {
		_t475 := p.parse_binding()
		item72 := _t475
		xs70 = append(xs70, item72)
		cond71 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings73 := xs70
	var _t476 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t477 := p.parse_value_bindings()
		_t476 = _t477
	}
	value_bindings74 := _t476
	p.consumeLiteral("]")
	_t478 := value_bindings74
	if value_bindings74 == nil {
		_t478 = []*pb.Binding{}
	}
	return []interface{}{bindings73, _t478}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol75 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	_t479 := p.parse_type()
	type76 := _t479
	_t480 := &pb.Var{Name: symbol75}
	_t481 := &pb.Binding{Var: _t480, Type: type76}
	return _t481
}

func (p *Parser) parse_type() *pb.Type {
	var _t482 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t482 = 0
	} else {
		var _t483 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t483 = 4
		} else {
			var _t484 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t484 = 1
			} else {
				var _t485 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t485 = 8
				} else {
					var _t486 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t486 = 5
					} else {
						var _t487 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t487 = 2
						} else {
							var _t488 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t488 = 3
							} else {
								var _t489 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t489 = 7
								} else {
									var _t490 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t490 = 6
									} else {
										var _t491 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t491 = 10
										} else {
											var _t492 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t492 = 9
											} else {
												_t492 = -1
											}
											_t491 = _t492
										}
										_t490 = _t491
									}
									_t489 = _t490
								}
								_t488 = _t489
							}
							_t487 = _t488
						}
						_t486 = _t487
					}
					_t485 = _t486
				}
				_t484 = _t485
			}
			_t483 = _t484
		}
		_t482 = _t483
	}
	prediction77 := _t482
	var _t493 *pb.Type
	if prediction77 == 10 {
		_t494 := p.parse_boolean_type()
		boolean_type88 := _t494
		_t495 := &pb.Type{}
		_t495.Type = &pb.Type_BooleanType{BooleanType: boolean_type88}
		_t493 = _t495
	} else {
		var _t496 *pb.Type
		if prediction77 == 9 {
			_t497 := p.parse_decimal_type()
			decimal_type87 := _t497
			_t498 := &pb.Type{}
			_t498.Type = &pb.Type_DecimalType{DecimalType: decimal_type87}
			_t496 = _t498
		} else {
			var _t499 *pb.Type
			if prediction77 == 8 {
				_t500 := p.parse_missing_type()
				missing_type86 := _t500
				_t501 := &pb.Type{}
				_t501.Type = &pb.Type_MissingType{MissingType: missing_type86}
				_t499 = _t501
			} else {
				var _t502 *pb.Type
				if prediction77 == 7 {
					_t503 := p.parse_datetime_type()
					datetime_type85 := _t503
					_t504 := &pb.Type{}
					_t504.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type85}
					_t502 = _t504
				} else {
					var _t505 *pb.Type
					if prediction77 == 6 {
						_t506 := p.parse_date_type()
						date_type84 := _t506
						_t507 := &pb.Type{}
						_t507.Type = &pb.Type_DateType{DateType: date_type84}
						_t505 = _t507
					} else {
						var _t508 *pb.Type
						if prediction77 == 5 {
							_t509 := p.parse_int128_type()
							int128_type83 := _t509
							_t510 := &pb.Type{}
							_t510.Type = &pb.Type_Int128Type{Int128Type: int128_type83}
							_t508 = _t510
						} else {
							var _t511 *pb.Type
							if prediction77 == 4 {
								_t512 := p.parse_uint128_type()
								uint128_type82 := _t512
								_t513 := &pb.Type{}
								_t513.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type82}
								_t511 = _t513
							} else {
								var _t514 *pb.Type
								if prediction77 == 3 {
									_t515 := p.parse_float_type()
									float_type81 := _t515
									_t516 := &pb.Type{}
									_t516.Type = &pb.Type_FloatType{FloatType: float_type81}
									_t514 = _t516
								} else {
									var _t517 *pb.Type
									if prediction77 == 2 {
										_t518 := p.parse_int_type()
										int_type80 := _t518
										_t519 := &pb.Type{}
										_t519.Type = &pb.Type_IntType{IntType: int_type80}
										_t517 = _t519
									} else {
										var _t520 *pb.Type
										if prediction77 == 1 {
											_t521 := p.parse_string_type()
											string_type79 := _t521
											_t522 := &pb.Type{}
											_t522.Type = &pb.Type_StringType{StringType: string_type79}
											_t520 = _t522
										} else {
											var _t523 *pb.Type
											if prediction77 == 0 {
												_t524 := p.parse_unspecified_type()
												unspecified_type78 := _t524
												_t525 := &pb.Type{}
												_t525.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type78}
												_t523 = _t525
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t520 = _t523
										}
										_t517 = _t520
									}
									_t514 = _t517
								}
								_t511 = _t514
							}
							_t508 = _t511
						}
						_t505 = _t508
					}
					_t502 = _t505
				}
				_t499 = _t502
			}
			_t496 = _t499
		}
		_t493 = _t496
	}
	return _t493
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t526 := &pb.UnspecifiedType{}
	return _t526
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t527 := &pb.StringType{}
	return _t527
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t528 := &pb.IntType{}
	return _t528
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t529 := &pb.FloatType{}
	return _t529
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t530 := &pb.UInt128Type{}
	return _t530
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t531 := &pb.Int128Type{}
	return _t531
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t532 := &pb.DateType{}
	return _t532
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t533 := &pb.DateTimeType{}
	return _t533
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t534 := &pb.MissingType{}
	return _t534
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int89 := p.consumeTerminal("INT").Value.AsInt64()
	int_390 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t535 := &pb.DecimalType{Precision: int32(int89), Scale: int32(int_390)}
	return _t535
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t536 := &pb.BooleanType{}
	return _t536
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs91 := []*pb.Binding{}
	cond92 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond92 {
		_t537 := p.parse_binding()
		item93 := _t537
		xs91 = append(xs91, item93)
		cond92 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings94 := xs91
	return bindings94
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t538 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t539 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t539 = 0
		} else {
			var _t540 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t540 = 11
			} else {
				var _t541 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t541 = 3
				} else {
					var _t542 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t542 = 10
					} else {
						var _t543 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t543 = 9
						} else {
							var _t544 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t544 = 5
							} else {
								var _t545 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t545 = 6
								} else {
									var _t546 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t546 = 7
									} else {
										var _t547 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t547 = 1
										} else {
											var _t548 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t548 = 2
											} else {
												var _t549 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t549 = 12
												} else {
													var _t550 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t550 = 8
													} else {
														var _t551 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t551 = 4
														} else {
															var _t552 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t552 = 10
															} else {
																var _t553 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t553 = 10
																} else {
																	var _t554 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t554 = 10
																	} else {
																		var _t555 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t555 = 10
																		} else {
																			var _t556 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t556 = 10
																			} else {
																				var _t557 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t557 = 10
																				} else {
																					var _t558 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t558 = 10
																					} else {
																						var _t559 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t559 = 10
																						} else {
																							var _t560 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t560 = 10
																							} else {
																								_t560 = -1
																							}
																							_t559 = _t560
																						}
																						_t558 = _t559
																					}
																					_t557 = _t558
																				}
																				_t556 = _t557
																			}
																			_t555 = _t556
																		}
																		_t554 = _t555
																	}
																	_t553 = _t554
																}
																_t552 = _t553
															}
															_t551 = _t552
														}
														_t550 = _t551
													}
													_t549 = _t550
												}
												_t548 = _t549
											}
											_t547 = _t548
										}
										_t546 = _t547
									}
									_t545 = _t546
								}
								_t544 = _t545
							}
							_t543 = _t544
						}
						_t542 = _t543
					}
					_t541 = _t542
				}
				_t540 = _t541
			}
			_t539 = _t540
		}
		_t538 = _t539
	} else {
		_t538 = -1
	}
	prediction95 := _t538
	var _t561 *pb.Formula
	if prediction95 == 12 {
		_t562 := p.parse_cast()
		cast108 := _t562
		_t563 := &pb.Formula{}
		_t563.FormulaType = &pb.Formula_Cast{Cast: cast108}
		_t561 = _t563
	} else {
		var _t564 *pb.Formula
		if prediction95 == 11 {
			_t565 := p.parse_rel_atom()
			rel_atom107 := _t565
			_t566 := &pb.Formula{}
			_t566.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom107}
			_t564 = _t566
		} else {
			var _t567 *pb.Formula
			if prediction95 == 10 {
				_t568 := p.parse_primitive()
				primitive106 := _t568
				_t569 := &pb.Formula{}
				_t569.FormulaType = &pb.Formula_Primitive{Primitive: primitive106}
				_t567 = _t569
			} else {
				var _t570 *pb.Formula
				if prediction95 == 9 {
					_t571 := p.parse_pragma()
					pragma105 := _t571
					_t572 := &pb.Formula{}
					_t572.FormulaType = &pb.Formula_Pragma{Pragma: pragma105}
					_t570 = _t572
				} else {
					var _t573 *pb.Formula
					if prediction95 == 8 {
						_t574 := p.parse_atom()
						atom104 := _t574
						_t575 := &pb.Formula{}
						_t575.FormulaType = &pb.Formula_Atom{Atom: atom104}
						_t573 = _t575
					} else {
						var _t576 *pb.Formula
						if prediction95 == 7 {
							_t577 := p.parse_ffi()
							ffi103 := _t577
							_t578 := &pb.Formula{}
							_t578.FormulaType = &pb.Formula_Ffi{Ffi: ffi103}
							_t576 = _t578
						} else {
							var _t579 *pb.Formula
							if prediction95 == 6 {
								_t580 := p.parse_not()
								not102 := _t580
								_t581 := &pb.Formula{}
								_t581.FormulaType = &pb.Formula_Not{Not: not102}
								_t579 = _t581
							} else {
								var _t582 *pb.Formula
								if prediction95 == 5 {
									_t583 := p.parse_disjunction()
									disjunction101 := _t583
									_t584 := &pb.Formula{}
									_t584.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction101}
									_t582 = _t584
								} else {
									var _t585 *pb.Formula
									if prediction95 == 4 {
										_t586 := p.parse_conjunction()
										conjunction100 := _t586
										_t587 := &pb.Formula{}
										_t587.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction100}
										_t585 = _t587
									} else {
										var _t588 *pb.Formula
										if prediction95 == 3 {
											_t589 := p.parse_reduce()
											reduce99 := _t589
											_t590 := &pb.Formula{}
											_t590.FormulaType = &pb.Formula_Reduce{Reduce: reduce99}
											_t588 = _t590
										} else {
											var _t591 *pb.Formula
											if prediction95 == 2 {
												_t592 := p.parse_exists()
												exists98 := _t592
												_t593 := &pb.Formula{}
												_t593.FormulaType = &pb.Formula_Exists{Exists: exists98}
												_t591 = _t593
											} else {
												var _t594 *pb.Formula
												if prediction95 == 1 {
													_t595 := p.parse_false()
													false97 := _t595
													_t596 := &pb.Formula{}
													_t596.FormulaType = &pb.Formula_Disjunction{Disjunction: false97}
													_t594 = _t596
												} else {
													var _t597 *pb.Formula
													if prediction95 == 0 {
														_t598 := p.parse_true()
														true96 := _t598
														_t599 := &pb.Formula{}
														_t599.FormulaType = &pb.Formula_Conjunction{Conjunction: true96}
														_t597 = _t599
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t594 = _t597
												}
												_t591 = _t594
											}
											_t588 = _t591
										}
										_t585 = _t588
									}
									_t582 = _t585
								}
								_t579 = _t582
							}
							_t576 = _t579
						}
						_t573 = _t576
					}
					_t570 = _t573
				}
				_t567 = _t570
			}
			_t564 = _t567
		}
		_t561 = _t564
	}
	return _t561
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t600 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t600
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t601 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t601
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t602 := p.parse_bindings()
	bindings109 := _t602
	_t603 := p.parse_formula()
	formula110 := _t603
	p.consumeLiteral(")")
	_t604 := &pb.Abstraction{Vars: listConcat(bindings109[0].([]*pb.Binding), bindings109[1].([]*pb.Binding)), Value: formula110}
	_t605 := &pb.Exists{Body: _t604}
	return _t605
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t606 := p.parse_abstraction()
	abstraction111 := _t606
	_t607 := p.parse_abstraction()
	abstraction_3112 := _t607
	_t608 := p.parse_terms()
	terms113 := _t608
	p.consumeLiteral(")")
	_t609 := &pb.Reduce{Op: abstraction111, Body: abstraction_3112, Terms: terms113}
	return _t609
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs114 := []*pb.Term{}
	cond115 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond115 {
		_t610 := p.parse_term()
		item116 := _t610
		xs114 = append(xs114, item116)
		cond115 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms117 := xs114
	p.consumeLiteral(")")
	return terms117
}

func (p *Parser) parse_term() *pb.Term {
	var _t611 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t611 = 1
	} else {
		var _t612 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t612 = 1
		} else {
			var _t613 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t613 = 1
			} else {
				var _t614 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t614 = 1
				} else {
					var _t615 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t615 = 1
					} else {
						var _t616 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t616 = 0
						} else {
							var _t617 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t617 = 1
							} else {
								var _t618 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t618 = 1
								} else {
									var _t619 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t619 = 1
									} else {
										var _t620 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t620 = 1
										} else {
											var _t621 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t621 = 1
											} else {
												_t621 = -1
											}
											_t620 = _t621
										}
										_t619 = _t620
									}
									_t618 = _t619
								}
								_t617 = _t618
							}
							_t616 = _t617
						}
						_t615 = _t616
					}
					_t614 = _t615
				}
				_t613 = _t614
			}
			_t612 = _t613
		}
		_t611 = _t612
	}
	prediction118 := _t611
	var _t622 *pb.Term
	if prediction118 == 1 {
		_t623 := p.parse_constant()
		constant120 := _t623
		_t624 := &pb.Term{}
		_t624.TermType = &pb.Term_Constant{Constant: constant120}
		_t622 = _t624
	} else {
		var _t625 *pb.Term
		if prediction118 == 0 {
			_t626 := p.parse_var()
			var119 := _t626
			_t627 := &pb.Term{}
			_t627.TermType = &pb.Term_Var{Var: var119}
			_t625 = _t627
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t622 = _t625
	}
	return _t622
}

func (p *Parser) parse_var() *pb.Var {
	symbol121 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t628 := &pb.Var{Name: symbol121}
	return _t628
}

func (p *Parser) parse_constant() *pb.Value {
	_t629 := p.parse_value()
	value122 := _t629
	return value122
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs123 := []*pb.Formula{}
	cond124 := p.matchLookaheadLiteral("(", 0)
	for cond124 {
		_t630 := p.parse_formula()
		item125 := _t630
		xs123 = append(xs123, item125)
		cond124 = p.matchLookaheadLiteral("(", 0)
	}
	formulas126 := xs123
	p.consumeLiteral(")")
	_t631 := &pb.Conjunction{Args: formulas126}
	return _t631
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs127 := []*pb.Formula{}
	cond128 := p.matchLookaheadLiteral("(", 0)
	for cond128 {
		_t632 := p.parse_formula()
		item129 := _t632
		xs127 = append(xs127, item129)
		cond128 = p.matchLookaheadLiteral("(", 0)
	}
	formulas130 := xs127
	p.consumeLiteral(")")
	_t633 := &pb.Disjunction{Args: formulas130}
	return _t633
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t634 := p.parse_formula()
	formula131 := _t634
	p.consumeLiteral(")")
	_t635 := &pb.Not{Arg: formula131}
	return _t635
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t636 := p.parse_name()
	name132 := _t636
	_t637 := p.parse_ffi_args()
	ffi_args133 := _t637
	_t638 := p.parse_terms()
	terms134 := _t638
	p.consumeLiteral(")")
	_t639 := &pb.FFI{Name: name132, Args: ffi_args133, Terms: terms134}
	return _t639
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol135 := p.consumeTerminal("SYMBOL").Value.AsString()
	return symbol135
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs136 := []*pb.Abstraction{}
	cond137 := p.matchLookaheadLiteral("(", 0)
	for cond137 {
		_t640 := p.parse_abstraction()
		item138 := _t640
		xs136 = append(xs136, item138)
		cond137 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions139 := xs136
	p.consumeLiteral(")")
	return abstractions139
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t641 := p.parse_relation_id()
	relation_id140 := _t641
	xs141 := []*pb.Term{}
	cond142 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond142 {
		_t642 := p.parse_term()
		item143 := _t642
		xs141 = append(xs141, item143)
		cond142 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms144 := xs141
	p.consumeLiteral(")")
	_t643 := &pb.Atom{Name: relation_id140, Terms: terms144}
	return _t643
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t644 := p.parse_name()
	name145 := _t644
	xs146 := []*pb.Term{}
	cond147 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond147 {
		_t645 := p.parse_term()
		item148 := _t645
		xs146 = append(xs146, item148)
		cond147 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms149 := xs146
	p.consumeLiteral(")")
	_t646 := &pb.Pragma{Name: name145, Terms: terms149}
	return _t646
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t647 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t648 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t648 = 9
		} else {
			var _t649 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t649 = 4
			} else {
				var _t650 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t650 = 3
				} else {
					var _t651 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t651 = 0
					} else {
						var _t652 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t652 = 2
						} else {
							var _t653 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t653 = 1
							} else {
								var _t654 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t654 = 8
								} else {
									var _t655 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t655 = 6
									} else {
										var _t656 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t656 = 5
										} else {
											var _t657 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t657 = 7
											} else {
												_t657 = -1
											}
											_t656 = _t657
										}
										_t655 = _t656
									}
									_t654 = _t655
								}
								_t653 = _t654
							}
							_t652 = _t653
						}
						_t651 = _t652
					}
					_t650 = _t651
				}
				_t649 = _t650
			}
			_t648 = _t649
		}
		_t647 = _t648
	} else {
		_t647 = -1
	}
	prediction150 := _t647
	var _t658 *pb.Primitive
	if prediction150 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t659 := p.parse_name()
		name160 := _t659
		xs161 := []*pb.RelTerm{}
		cond162 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond162 {
			_t660 := p.parse_rel_term()
			item163 := _t660
			xs161 = append(xs161, item163)
			cond162 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms164 := xs161
		p.consumeLiteral(")")
		_t661 := &pb.Primitive{Name: name160, Terms: rel_terms164}
		_t658 = _t661
	} else {
		var _t662 *pb.Primitive
		if prediction150 == 8 {
			_t663 := p.parse_divide()
			divide159 := _t663
			_t662 = divide159
		} else {
			var _t664 *pb.Primitive
			if prediction150 == 7 {
				_t665 := p.parse_multiply()
				multiply158 := _t665
				_t664 = multiply158
			} else {
				var _t666 *pb.Primitive
				if prediction150 == 6 {
					_t667 := p.parse_minus()
					minus157 := _t667
					_t666 = minus157
				} else {
					var _t668 *pb.Primitive
					if prediction150 == 5 {
						_t669 := p.parse_add()
						add156 := _t669
						_t668 = add156
					} else {
						var _t670 *pb.Primitive
						if prediction150 == 4 {
							_t671 := p.parse_gt_eq()
							gt_eq155 := _t671
							_t670 = gt_eq155
						} else {
							var _t672 *pb.Primitive
							if prediction150 == 3 {
								_t673 := p.parse_gt()
								gt154 := _t673
								_t672 = gt154
							} else {
								var _t674 *pb.Primitive
								if prediction150 == 2 {
									_t675 := p.parse_lt_eq()
									lt_eq153 := _t675
									_t674 = lt_eq153
								} else {
									var _t676 *pb.Primitive
									if prediction150 == 1 {
										_t677 := p.parse_lt()
										lt152 := _t677
										_t676 = lt152
									} else {
										var _t678 *pb.Primitive
										if prediction150 == 0 {
											_t679 := p.parse_eq()
											eq151 := _t679
											_t678 = eq151
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t676 = _t678
									}
									_t674 = _t676
								}
								_t672 = _t674
							}
							_t670 = _t672
						}
						_t668 = _t670
					}
					_t666 = _t668
				}
				_t664 = _t666
			}
			_t662 = _t664
		}
		_t658 = _t662
	}
	return _t658
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t680 := p.parse_term()
	term165 := _t680
	_t681 := p.parse_term()
	term_3166 := _t681
	p.consumeLiteral(")")
	_t682 := &pb.RelTerm{}
	_t682.RelTermType = &pb.RelTerm_Term{Term: term165}
	_t683 := &pb.RelTerm{}
	_t683.RelTermType = &pb.RelTerm_Term{Term: term_3166}
	_t684 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t682, _t683}}
	return _t684
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t685 := p.parse_term()
	term167 := _t685
	_t686 := p.parse_term()
	term_3168 := _t686
	p.consumeLiteral(")")
	_t687 := &pb.RelTerm{}
	_t687.RelTermType = &pb.RelTerm_Term{Term: term167}
	_t688 := &pb.RelTerm{}
	_t688.RelTermType = &pb.RelTerm_Term{Term: term_3168}
	_t689 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t687, _t688}}
	return _t689
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t690 := p.parse_term()
	term169 := _t690
	_t691 := p.parse_term()
	term_3170 := _t691
	p.consumeLiteral(")")
	_t692 := &pb.RelTerm{}
	_t692.RelTermType = &pb.RelTerm_Term{Term: term169}
	_t693 := &pb.RelTerm{}
	_t693.RelTermType = &pb.RelTerm_Term{Term: term_3170}
	_t694 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t692, _t693}}
	return _t694
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t695 := p.parse_term()
	term171 := _t695
	_t696 := p.parse_term()
	term_3172 := _t696
	p.consumeLiteral(")")
	_t697 := &pb.RelTerm{}
	_t697.RelTermType = &pb.RelTerm_Term{Term: term171}
	_t698 := &pb.RelTerm{}
	_t698.RelTermType = &pb.RelTerm_Term{Term: term_3172}
	_t699 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t697, _t698}}
	return _t699
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t700 := p.parse_term()
	term173 := _t700
	_t701 := p.parse_term()
	term_3174 := _t701
	p.consumeLiteral(")")
	_t702 := &pb.RelTerm{}
	_t702.RelTermType = &pb.RelTerm_Term{Term: term173}
	_t703 := &pb.RelTerm{}
	_t703.RelTermType = &pb.RelTerm_Term{Term: term_3174}
	_t704 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t702, _t703}}
	return _t704
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t705 := p.parse_term()
	term175 := _t705
	_t706 := p.parse_term()
	term_3176 := _t706
	_t707 := p.parse_term()
	term_4177 := _t707
	p.consumeLiteral(")")
	_t708 := &pb.RelTerm{}
	_t708.RelTermType = &pb.RelTerm_Term{Term: term175}
	_t709 := &pb.RelTerm{}
	_t709.RelTermType = &pb.RelTerm_Term{Term: term_3176}
	_t710 := &pb.RelTerm{}
	_t710.RelTermType = &pb.RelTerm_Term{Term: term_4177}
	_t711 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t708, _t709, _t710}}
	return _t711
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t712 := p.parse_term()
	term178 := _t712
	_t713 := p.parse_term()
	term_3179 := _t713
	_t714 := p.parse_term()
	term_4180 := _t714
	p.consumeLiteral(")")
	_t715 := &pb.RelTerm{}
	_t715.RelTermType = &pb.RelTerm_Term{Term: term178}
	_t716 := &pb.RelTerm{}
	_t716.RelTermType = &pb.RelTerm_Term{Term: term_3179}
	_t717 := &pb.RelTerm{}
	_t717.RelTermType = &pb.RelTerm_Term{Term: term_4180}
	_t718 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t715, _t716, _t717}}
	return _t718
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t719 := p.parse_term()
	term181 := _t719
	_t720 := p.parse_term()
	term_3182 := _t720
	_t721 := p.parse_term()
	term_4183 := _t721
	p.consumeLiteral(")")
	_t722 := &pb.RelTerm{}
	_t722.RelTermType = &pb.RelTerm_Term{Term: term181}
	_t723 := &pb.RelTerm{}
	_t723.RelTermType = &pb.RelTerm_Term{Term: term_3182}
	_t724 := &pb.RelTerm{}
	_t724.RelTermType = &pb.RelTerm_Term{Term: term_4183}
	_t725 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t722, _t723, _t724}}
	return _t725
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t726 := p.parse_term()
	term184 := _t726
	_t727 := p.parse_term()
	term_3185 := _t727
	_t728 := p.parse_term()
	term_4186 := _t728
	p.consumeLiteral(")")
	_t729 := &pb.RelTerm{}
	_t729.RelTermType = &pb.RelTerm_Term{Term: term184}
	_t730 := &pb.RelTerm{}
	_t730.RelTermType = &pb.RelTerm_Term{Term: term_3185}
	_t731 := &pb.RelTerm{}
	_t731.RelTermType = &pb.RelTerm_Term{Term: term_4186}
	_t732 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t729, _t730, _t731}}
	return _t732
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t733 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t733 = 1
	} else {
		var _t734 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t734 = 1
		} else {
			var _t735 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t735 = 1
			} else {
				var _t736 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t736 = 1
				} else {
					var _t737 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t737 = 0
					} else {
						var _t738 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t738 = 1
						} else {
							var _t739 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t739 = 1
							} else {
								var _t740 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t740 = 1
								} else {
									var _t741 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t741 = 1
									} else {
										var _t742 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t742 = 1
										} else {
											var _t743 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t743 = 1
											} else {
												var _t744 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t744 = 1
												} else {
													_t744 = -1
												}
												_t743 = _t744
											}
											_t742 = _t743
										}
										_t741 = _t742
									}
									_t740 = _t741
								}
								_t739 = _t740
							}
							_t738 = _t739
						}
						_t737 = _t738
					}
					_t736 = _t737
				}
				_t735 = _t736
			}
			_t734 = _t735
		}
		_t733 = _t734
	}
	prediction187 := _t733
	var _t745 *pb.RelTerm
	if prediction187 == 1 {
		_t746 := p.parse_term()
		term189 := _t746
		_t747 := &pb.RelTerm{}
		_t747.RelTermType = &pb.RelTerm_Term{Term: term189}
		_t745 = _t747
	} else {
		var _t748 *pb.RelTerm
		if prediction187 == 0 {
			_t749 := p.parse_specialized_value()
			specialized_value188 := _t749
			_t750 := &pb.RelTerm{}
			_t750.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value188}
			_t748 = _t750
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t745 = _t748
	}
	return _t745
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t751 := p.parse_value()
	value190 := _t751
	return value190
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t752 := p.parse_name()
	name191 := _t752
	xs192 := []*pb.RelTerm{}
	cond193 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond193 {
		_t753 := p.parse_rel_term()
		item194 := _t753
		xs192 = append(xs192, item194)
		cond193 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms195 := xs192
	p.consumeLiteral(")")
	_t754 := &pb.RelAtom{Name: name191, Terms: rel_terms195}
	return _t754
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t755 := p.parse_term()
	term196 := _t755
	_t756 := p.parse_term()
	term_3197 := _t756
	p.consumeLiteral(")")
	_t757 := &pb.Cast{Input: term196, Result: term_3197}
	return _t757
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs198 := []*pb.Attribute{}
	cond199 := p.matchLookaheadLiteral("(", 0)
	for cond199 {
		_t758 := p.parse_attribute()
		item200 := _t758
		xs198 = append(xs198, item200)
		cond199 = p.matchLookaheadLiteral("(", 0)
	}
	attributes201 := xs198
	p.consumeLiteral(")")
	return attributes201
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t759 := p.parse_name()
	name202 := _t759
	xs203 := []*pb.Value{}
	cond204 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond204 {
		_t760 := p.parse_value()
		item205 := _t760
		xs203 = append(xs203, item205)
		cond204 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values206 := xs203
	p.consumeLiteral(")")
	_t761 := &pb.Attribute{Name: name202, Args: values206}
	return _t761
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs207 := []*pb.RelationId{}
	cond208 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond208 {
		_t762 := p.parse_relation_id()
		item209 := _t762
		xs207 = append(xs207, item209)
		cond208 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids210 := xs207
	_t763 := p.parse_script()
	script211 := _t763
	p.consumeLiteral(")")
	_t764 := &pb.Algorithm{Global: relation_ids210, Body: script211}
	return _t764
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs212 := []*pb.Construct{}
	cond213 := p.matchLookaheadLiteral("(", 0)
	for cond213 {
		_t765 := p.parse_construct()
		item214 := _t765
		xs212 = append(xs212, item214)
		cond213 = p.matchLookaheadLiteral("(", 0)
	}
	constructs215 := xs212
	p.consumeLiteral(")")
	_t766 := &pb.Script{Constructs: constructs215}
	return _t766
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t767 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t768 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t768 = 1
		} else {
			var _t769 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t769 = 1
			} else {
				var _t770 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t770 = 1
				} else {
					var _t771 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t771 = 0
					} else {
						var _t772 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t772 = 1
						} else {
							var _t773 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t773 = 1
							} else {
								_t773 = -1
							}
							_t772 = _t773
						}
						_t771 = _t772
					}
					_t770 = _t771
				}
				_t769 = _t770
			}
			_t768 = _t769
		}
		_t767 = _t768
	} else {
		_t767 = -1
	}
	prediction216 := _t767
	var _t774 *pb.Construct
	if prediction216 == 1 {
		_t775 := p.parse_instruction()
		instruction218 := _t775
		_t776 := &pb.Construct{}
		_t776.ConstructType = &pb.Construct_Instruction{Instruction: instruction218}
		_t774 = _t776
	} else {
		var _t777 *pb.Construct
		if prediction216 == 0 {
			_t778 := p.parse_loop()
			loop217 := _t778
			_t779 := &pb.Construct{}
			_t779.ConstructType = &pb.Construct_Loop{Loop: loop217}
			_t777 = _t779
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t774 = _t777
	}
	return _t774
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t780 := p.parse_init()
	init219 := _t780
	_t781 := p.parse_script()
	script220 := _t781
	p.consumeLiteral(")")
	_t782 := &pb.Loop{Init: init219, Body: script220}
	return _t782
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs221 := []*pb.Instruction{}
	cond222 := p.matchLookaheadLiteral("(", 0)
	for cond222 {
		_t783 := p.parse_instruction()
		item223 := _t783
		xs221 = append(xs221, item223)
		cond222 = p.matchLookaheadLiteral("(", 0)
	}
	instructions224 := xs221
	p.consumeLiteral(")")
	return instructions224
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t784 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t785 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t785 = 1
		} else {
			var _t786 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t786 = 4
			} else {
				var _t787 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t787 = 3
				} else {
					var _t788 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t788 = 2
					} else {
						var _t789 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t789 = 0
						} else {
							_t789 = -1
						}
						_t788 = _t789
					}
					_t787 = _t788
				}
				_t786 = _t787
			}
			_t785 = _t786
		}
		_t784 = _t785
	} else {
		_t784 = -1
	}
	prediction225 := _t784
	var _t790 *pb.Instruction
	if prediction225 == 4 {
		_t791 := p.parse_monus_def()
		monus_def230 := _t791
		_t792 := &pb.Instruction{}
		_t792.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def230}
		_t790 = _t792
	} else {
		var _t793 *pb.Instruction
		if prediction225 == 3 {
			_t794 := p.parse_monoid_def()
			monoid_def229 := _t794
			_t795 := &pb.Instruction{}
			_t795.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def229}
			_t793 = _t795
		} else {
			var _t796 *pb.Instruction
			if prediction225 == 2 {
				_t797 := p.parse_break()
				break228 := _t797
				_t798 := &pb.Instruction{}
				_t798.InstrType = &pb.Instruction_Break{Break: break228}
				_t796 = _t798
			} else {
				var _t799 *pb.Instruction
				if prediction225 == 1 {
					_t800 := p.parse_upsert()
					upsert227 := _t800
					_t801 := &pb.Instruction{}
					_t801.InstrType = &pb.Instruction_Upsert{Upsert: upsert227}
					_t799 = _t801
				} else {
					var _t802 *pb.Instruction
					if prediction225 == 0 {
						_t803 := p.parse_assign()
						assign226 := _t803
						_t804 := &pb.Instruction{}
						_t804.InstrType = &pb.Instruction_Assign{Assign: assign226}
						_t802 = _t804
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t799 = _t802
				}
				_t796 = _t799
			}
			_t793 = _t796
		}
		_t790 = _t793
	}
	return _t790
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t805 := p.parse_relation_id()
	relation_id231 := _t805
	_t806 := p.parse_abstraction()
	abstraction232 := _t806
	var _t807 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t808 := p.parse_attrs()
		_t807 = _t808
	}
	attrs233 := _t807
	p.consumeLiteral(")")
	_t809 := attrs233
	if attrs233 == nil {
		_t809 = []*pb.Attribute{}
	}
	_t810 := &pb.Assign{Name: relation_id231, Body: abstraction232, Attrs: _t809}
	return _t810
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t811 := p.parse_relation_id()
	relation_id234 := _t811
	_t812 := p.parse_abstraction_with_arity()
	abstraction_with_arity235 := _t812
	var _t813 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t814 := p.parse_attrs()
		_t813 = _t814
	}
	attrs236 := _t813
	p.consumeLiteral(")")
	_t815 := attrs236
	if attrs236 == nil {
		_t815 = []*pb.Attribute{}
	}
	_t816 := &pb.Upsert{Name: relation_id234, Body: abstraction_with_arity235[0].(*pb.Abstraction), Attrs: _t815, ValueArity: abstraction_with_arity235[1].(int64)}
	return _t816
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t817 := p.parse_bindings()
	bindings237 := _t817
	_t818 := p.parse_formula()
	formula238 := _t818
	p.consumeLiteral(")")
	_t819 := &pb.Abstraction{Vars: listConcat(bindings237[0].([]*pb.Binding), bindings237[1].([]*pb.Binding)), Value: formula238}
	return []interface{}{_t819, int64(len(bindings237[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t820 := p.parse_relation_id()
	relation_id239 := _t820
	_t821 := p.parse_abstraction()
	abstraction240 := _t821
	var _t822 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t823 := p.parse_attrs()
		_t822 = _t823
	}
	attrs241 := _t822
	p.consumeLiteral(")")
	_t824 := attrs241
	if attrs241 == nil {
		_t824 = []*pb.Attribute{}
	}
	_t825 := &pb.Break{Name: relation_id239, Body: abstraction240, Attrs: _t824}
	return _t825
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t826 := p.parse_monoid()
	monoid242 := _t826
	_t827 := p.parse_relation_id()
	relation_id243 := _t827
	_t828 := p.parse_abstraction_with_arity()
	abstraction_with_arity244 := _t828
	var _t829 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t830 := p.parse_attrs()
		_t829 = _t830
	}
	attrs245 := _t829
	p.consumeLiteral(")")
	_t831 := attrs245
	if attrs245 == nil {
		_t831 = []*pb.Attribute{}
	}
	_t832 := &pb.MonoidDef{Monoid: monoid242, Name: relation_id243, Body: abstraction_with_arity244[0].(*pb.Abstraction), Attrs: _t831, ValueArity: abstraction_with_arity244[1].(int64)}
	return _t832
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t833 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t834 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t834 = 3
		} else {
			var _t835 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t835 = 0
			} else {
				var _t836 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t836 = 1
				} else {
					var _t837 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t837 = 2
					} else {
						_t837 = -1
					}
					_t836 = _t837
				}
				_t835 = _t836
			}
			_t834 = _t835
		}
		_t833 = _t834
	} else {
		_t833 = -1
	}
	prediction246 := _t833
	var _t838 *pb.Monoid
	if prediction246 == 3 {
		_t839 := p.parse_sum_monoid()
		sum_monoid250 := _t839
		_t840 := &pb.Monoid{}
		_t840.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid250}
		_t838 = _t840
	} else {
		var _t841 *pb.Monoid
		if prediction246 == 2 {
			_t842 := p.parse_max_monoid()
			max_monoid249 := _t842
			_t843 := &pb.Monoid{}
			_t843.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid249}
			_t841 = _t843
		} else {
			var _t844 *pb.Monoid
			if prediction246 == 1 {
				_t845 := p.parse_min_monoid()
				min_monoid248 := _t845
				_t846 := &pb.Monoid{}
				_t846.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid248}
				_t844 = _t846
			} else {
				var _t847 *pb.Monoid
				if prediction246 == 0 {
					_t848 := p.parse_or_monoid()
					or_monoid247 := _t848
					_t849 := &pb.Monoid{}
					_t849.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid247}
					_t847 = _t849
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t844 = _t847
			}
			_t841 = _t844
		}
		_t838 = _t841
	}
	return _t838
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t850 := &pb.OrMonoid{}
	return _t850
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t851 := p.parse_type()
	type251 := _t851
	p.consumeLiteral(")")
	_t852 := &pb.MinMonoid{Type: type251}
	return _t852
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t853 := p.parse_type()
	type252 := _t853
	p.consumeLiteral(")")
	_t854 := &pb.MaxMonoid{Type: type252}
	return _t854
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t855 := p.parse_type()
	type253 := _t855
	p.consumeLiteral(")")
	_t856 := &pb.SumMonoid{Type: type253}
	return _t856
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t857 := p.parse_monoid()
	monoid254 := _t857
	_t858 := p.parse_relation_id()
	relation_id255 := _t858
	_t859 := p.parse_abstraction_with_arity()
	abstraction_with_arity256 := _t859
	var _t860 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t861 := p.parse_attrs()
		_t860 = _t861
	}
	attrs257 := _t860
	p.consumeLiteral(")")
	_t862 := attrs257
	if attrs257 == nil {
		_t862 = []*pb.Attribute{}
	}
	_t863 := &pb.MonusDef{Monoid: monoid254, Name: relation_id255, Body: abstraction_with_arity256[0].(*pb.Abstraction), Attrs: _t862, ValueArity: abstraction_with_arity256[1].(int64)}
	return _t863
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t864 := p.parse_relation_id()
	relation_id258 := _t864
	_t865 := p.parse_abstraction()
	abstraction259 := _t865
	_t866 := p.parse_functional_dependency_keys()
	functional_dependency_keys260 := _t866
	_t867 := p.parse_functional_dependency_values()
	functional_dependency_values261 := _t867
	p.consumeLiteral(")")
	_t868 := &pb.FunctionalDependency{Guard: abstraction259, Keys: functional_dependency_keys260, Values: functional_dependency_values261}
	_t869 := &pb.Constraint{Name: relation_id258}
	_t869.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t868}
	return _t869
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs262 := []*pb.Var{}
	cond263 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond263 {
		_t870 := p.parse_var()
		item264 := _t870
		xs262 = append(xs262, item264)
		cond263 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars265 := xs262
	p.consumeLiteral(")")
	return vars265
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs266 := []*pb.Var{}
	cond267 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond267 {
		_t871 := p.parse_var()
		item268 := _t871
		xs266 = append(xs266, item268)
		cond267 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars269 := xs266
	p.consumeLiteral(")")
	return vars269
}

func (p *Parser) parse_data() *pb.Data {
	var _t872 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t873 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t873 = 0
		} else {
			var _t874 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t874 = 2
			} else {
				var _t875 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t875 = 1
				} else {
					_t875 = -1
				}
				_t874 = _t875
			}
			_t873 = _t874
		}
		_t872 = _t873
	} else {
		_t872 = -1
	}
	prediction270 := _t872
	var _t876 *pb.Data
	if prediction270 == 2 {
		_t877 := p.parse_csv_data()
		csv_data273 := _t877
		_t878 := &pb.Data{}
		_t878.DataType = &pb.Data_CsvData{CsvData: csv_data273}
		_t876 = _t878
	} else {
		var _t879 *pb.Data
		if prediction270 == 1 {
			_t880 := p.parse_betree_relation()
			betree_relation272 := _t880
			_t881 := &pb.Data{}
			_t881.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation272}
			_t879 = _t881
		} else {
			var _t882 *pb.Data
			if prediction270 == 0 {
				_t883 := p.parse_rel_edb()
				rel_edb271 := _t883
				_t884 := &pb.Data{}
				_t884.DataType = &pb.Data_RelEdb{RelEdb: rel_edb271}
				_t882 = _t884
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t879 = _t882
		}
		_t876 = _t879
	}
	return _t876
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t885 := p.parse_relation_id()
	relation_id274 := _t885
	_t886 := p.parse_rel_edb_path()
	rel_edb_path275 := _t886
	_t887 := p.parse_rel_edb_types()
	rel_edb_types276 := _t887
	p.consumeLiteral(")")
	_t888 := &pb.RelEDB{TargetId: relation_id274, Path: rel_edb_path275, Types: rel_edb_types276}
	return _t888
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs277 := []string{}
	cond278 := p.matchLookaheadTerminal("STRING", 0)
	for cond278 {
		item279 := p.consumeTerminal("STRING").Value.AsString()
		xs277 = append(xs277, item279)
		cond278 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings280 := xs277
	p.consumeLiteral("]")
	return strings280
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs281 := []*pb.Type{}
	cond282 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond282 {
		_t889 := p.parse_type()
		item283 := _t889
		xs281 = append(xs281, item283)
		cond282 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types284 := xs281
	p.consumeLiteral("]")
	return types284
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t890 := p.parse_relation_id()
	relation_id285 := _t890
	_t891 := p.parse_betree_info()
	betree_info286 := _t891
	p.consumeLiteral(")")
	_t892 := &pb.BeTreeRelation{Name: relation_id285, RelationInfo: betree_info286}
	return _t892
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t893 := p.parse_betree_info_key_types()
	betree_info_key_types287 := _t893
	_t894 := p.parse_betree_info_value_types()
	betree_info_value_types288 := _t894
	_t895 := p.parse_config_dict()
	config_dict289 := _t895
	p.consumeLiteral(")")
	_t896 := p.construct_betree_info(betree_info_key_types287, betree_info_value_types288, config_dict289)
	return _t896
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs290 := []*pb.Type{}
	cond291 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond291 {
		_t897 := p.parse_type()
		item292 := _t897
		xs290 = append(xs290, item292)
		cond291 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types293 := xs290
	p.consumeLiteral(")")
	return types293
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs294 := []*pb.Type{}
	cond295 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond295 {
		_t898 := p.parse_type()
		item296 := _t898
		xs294 = append(xs294, item296)
		cond295 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types297 := xs294
	p.consumeLiteral(")")
	return types297
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t899 := p.parse_csvlocator()
	csvlocator298 := _t899
	_t900 := p.parse_csv_config()
	csv_config299 := _t900
	_t901 := p.parse_csv_columns()
	csv_columns300 := _t901
	_t902 := p.parse_csv_asof()
	csv_asof301 := _t902
	p.consumeLiteral(")")
	_t903 := &pb.CSVData{Locator: csvlocator298, Config: csv_config299, Columns: csv_columns300, Asof: csv_asof301}
	return _t903
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t904 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t905 := p.parse_csv_locator_paths()
		_t904 = _t905
	}
	csv_locator_paths302 := _t904
	var _t906 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t907 := p.parse_csv_locator_inline_data()
		_t906 = ptr(_t907)
	}
	csv_locator_inline_data303 := _t906
	p.consumeLiteral(")")
	_t908 := csv_locator_paths302
	if csv_locator_paths302 == nil {
		_t908 = []string{}
	}
	_t909 := &pb.CSVLocator{Paths: _t908, InlineData: []byte(deref(csv_locator_inline_data303, ""))}
	return _t909
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs304 := []string{}
	cond305 := p.matchLookaheadTerminal("STRING", 0)
	for cond305 {
		item306 := p.consumeTerminal("STRING").Value.AsString()
		xs304 = append(xs304, item306)
		cond305 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings307 := xs304
	p.consumeLiteral(")")
	return strings307
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string308 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string308
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t910 := p.parse_config_dict()
	config_dict309 := _t910
	p.consumeLiteral(")")
	_t911 := p.construct_csv_config(config_dict309)
	return _t911
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs310 := []*pb.CSVColumn{}
	cond311 := p.matchLookaheadLiteral("(", 0)
	for cond311 {
		_t912 := p.parse_csv_column()
		item312 := _t912
		xs310 = append(xs310, item312)
		cond311 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns313 := xs310
	p.consumeLiteral(")")
	return csv_columns313
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string314 := p.consumeTerminal("STRING").Value.AsString()
	_t913 := p.parse_relation_id()
	relation_id315 := _t913
	p.consumeLiteral("[")
	xs316 := []*pb.Type{}
	cond317 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond317 {
		_t914 := p.parse_type()
		item318 := _t914
		xs316 = append(xs316, item318)
		cond317 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types319 := xs316
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t915 := &pb.CSVColumn{ColumnName: string314, TargetId: relation_id315, Types: types319}
	return _t915
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string320 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string320
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t916 := p.parse_fragment_id()
	fragment_id321 := _t916
	p.consumeLiteral(")")
	_t917 := &pb.Undefine{FragmentId: fragment_id321}
	return _t917
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs322 := []*pb.RelationId{}
	cond323 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond323 {
		_t918 := p.parse_relation_id()
		item324 := _t918
		xs322 = append(xs322, item324)
		cond323 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids325 := xs322
	p.consumeLiteral(")")
	_t919 := &pb.Context{Relations: relation_ids325}
	return _t919
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t920 := p.parse_rel_edb_path()
	rel_edb_path326 := _t920
	_t921 := p.parse_relation_id()
	relation_id327 := _t921
	p.consumeLiteral(")")
	_t922 := &pb.Snapshot{DestinationPath: rel_edb_path326, SourceRelation: relation_id327}
	return _t922
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs328 := []*pb.Read{}
	cond329 := p.matchLookaheadLiteral("(", 0)
	for cond329 {
		_t923 := p.parse_read()
		item330 := _t923
		xs328 = append(xs328, item330)
		cond329 = p.matchLookaheadLiteral("(", 0)
	}
	reads331 := xs328
	p.consumeLiteral(")")
	return reads331
}

func (p *Parser) parse_read() *pb.Read {
	var _t924 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t925 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t925 = 2
		} else {
			var _t926 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t926 = 1
			} else {
				var _t927 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t927 = 4
				} else {
					var _t928 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t928 = 0
					} else {
						var _t929 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t929 = 3
						} else {
							_t929 = -1
						}
						_t928 = _t929
					}
					_t927 = _t928
				}
				_t926 = _t927
			}
			_t925 = _t926
		}
		_t924 = _t925
	} else {
		_t924 = -1
	}
	prediction332 := _t924
	var _t930 *pb.Read
	if prediction332 == 4 {
		_t931 := p.parse_export()
		export337 := _t931
		_t932 := &pb.Read{}
		_t932.ReadType = &pb.Read_Export{Export: export337}
		_t930 = _t932
	} else {
		var _t933 *pb.Read
		if prediction332 == 3 {
			_t934 := p.parse_abort()
			abort336 := _t934
			_t935 := &pb.Read{}
			_t935.ReadType = &pb.Read_Abort{Abort: abort336}
			_t933 = _t935
		} else {
			var _t936 *pb.Read
			if prediction332 == 2 {
				_t937 := p.parse_what_if()
				what_if335 := _t937
				_t938 := &pb.Read{}
				_t938.ReadType = &pb.Read_WhatIf{WhatIf: what_if335}
				_t936 = _t938
			} else {
				var _t939 *pb.Read
				if prediction332 == 1 {
					_t940 := p.parse_output()
					output334 := _t940
					_t941 := &pb.Read{}
					_t941.ReadType = &pb.Read_Output{Output: output334}
					_t939 = _t941
				} else {
					var _t942 *pb.Read
					if prediction332 == 0 {
						_t943 := p.parse_demand()
						demand333 := _t943
						_t944 := &pb.Read{}
						_t944.ReadType = &pb.Read_Demand{Demand: demand333}
						_t942 = _t944
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t939 = _t942
				}
				_t936 = _t939
			}
			_t933 = _t936
		}
		_t930 = _t933
	}
	return _t930
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t945 := p.parse_relation_id()
	relation_id338 := _t945
	p.consumeLiteral(")")
	_t946 := &pb.Demand{RelationId: relation_id338}
	return _t946
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t947 := p.parse_name()
	name339 := _t947
	_t948 := p.parse_relation_id()
	relation_id340 := _t948
	p.consumeLiteral(")")
	_t949 := &pb.Output{Name: name339, RelationId: relation_id340}
	return _t949
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t950 := p.parse_name()
	name341 := _t950
	_t951 := p.parse_epoch()
	epoch342 := _t951
	p.consumeLiteral(")")
	_t952 := &pb.WhatIf{Branch: name341, Epoch: epoch342}
	return _t952
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t953 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t954 := p.parse_name()
		_t953 = ptr(_t954)
	}
	name343 := _t953
	_t955 := p.parse_relation_id()
	relation_id344 := _t955
	p.consumeLiteral(")")
	_t956 := &pb.Abort{Name: deref(name343, "abort"), RelationId: relation_id344}
	return _t956
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t957 := p.parse_export_csv_config()
	export_csv_config345 := _t957
	p.consumeLiteral(")")
	_t958 := &pb.Export{}
	_t958.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config345}
	return _t958
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t959 := p.parse_export_csv_path()
	export_csv_path346 := _t959
	_t960 := p.parse_export_csv_columns()
	export_csv_columns347 := _t960
	_t961 := p.parse_config_dict()
	config_dict348 := _t961
	p.consumeLiteral(")")
	_t962 := p.export_csv_config(export_csv_path346, export_csv_columns347, config_dict348)
	return _t962
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string349 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string349
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs350 := []*pb.ExportCSVColumn{}
	cond351 := p.matchLookaheadLiteral("(", 0)
	for cond351 {
		_t963 := p.parse_export_csv_column()
		item352 := _t963
		xs350 = append(xs350, item352)
		cond351 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns353 := xs350
	p.consumeLiteral(")")
	return export_csv_columns353
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string354 := p.consumeTerminal("STRING").Value.AsString()
	_t964 := p.parse_relation_id()
	relation_id355 := _t964
	p.consumeLiteral(")")
	_t965 := &pb.ExportCSVColumn{ColumnName: string354, ColumnData: relation_id355}
	return _t965
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
