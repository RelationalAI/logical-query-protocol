// Auto-generated LL(k) recursive-descent parser.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the parser, edit the generator code
// in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
//
// Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --parser go

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

	pb "logical-query-protocol/src/lqp/v1"
)

// ParseError represents a parse error
type ParseError struct {
	msg string
}

func (e ParseError) Error() string {
	return e.msg
}

// Option represents an optional value (Some or None)
type Option[T any] struct {
	Value T
	Valid bool
}

// Some creates an Option containing a value
func Some[T any](v T) Option[T] {
	return Option[T]{Value: v, Valid: true}
}

// None creates an empty Option
func None[T any]() Option[T] {
	return Option[T]{}
}

// UnwrapOr returns the value if present, otherwise returns the default
func (o Option[T]) UnwrapOr(defaultVal T) T {
	if o.Valid {
		return o.Value
	}
	return defaultVal
}

// Token represents a lexer token
type Token struct {
	Type  string
	Value interface{}
	Pos   int
}

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, %v, %d)", t.Type, t.Value, t.Pos)
}

// TokenSpec represents a token specification for the lexer
type tokenSpec struct {
	name   string
	regex  *regexp.Regexp
	action func(string) interface{}
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
		{"LITERAL", regexp.MustCompile(`^::`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^<=`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^>=`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\#`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\(`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\)`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\*`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\+`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\-`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^/`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^:`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^<`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^=`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^>`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\[`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\]`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\{`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\|`), func(s string) interface{} { return s }},
		{"LITERAL", regexp.MustCompile(`^\}`), func(s string) interface{} { return s }},
		{"DECIMAL", regexp.MustCompile(`^[-]?\d+\.\d+d\d+`), scanDecimal},
		{"FLOAT", regexp.MustCompile(`^[-]?\d+\.\d+|inf|nan`), scanFloat},
		{"INT", regexp.MustCompile(`^[-]?\d+`), scanInt},
		{"INT128", regexp.MustCompile(`^[-]?\d+i128`), scanInt128},
		{"STRING", regexp.MustCompile(`^"(?:[^"\\]|\\.)*"`), scanString},
		{"SYMBOL", regexp.MustCompile(`^[a-zA-Z_][a-zA-Z0-9_.-]*`), scanSymbol},
		{"UINT128", regexp.MustCompile(`^0x[0-9a-fA-F]+`), scanUint128},
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
			action    func(string) interface{}
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

	l.tokens = append(l.tokens, Token{Type: "$", Value: "", Pos: l.pos})
}

// Scanner functions for each token type
func scanSymbol(s string) interface{} {
	return s
}

func scanColonSymbol(s string) interface{} {
	return s[1:]
}

func scanString(s string) interface{} {
	// Strip quotes and process escaping
	content := s[1 : len(s)-1]
	// Simple escape processing
	content = strings.ReplaceAll(content, "\\n", "\n")
	content = strings.ReplaceAll(content, "\\t", "\t")
	content = strings.ReplaceAll(content, "\\r", "\r")
	content = strings.ReplaceAll(content, "\\\\", "\\")
	content = strings.ReplaceAll(content, "\\\"", "\"")
	return content
}

func scanInt(s string) interface{} {
	n, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid integer: %s", s)})
	}
	return n
}

func scanFloat(s string) interface{} {
	if s == "inf" {
		return math.Inf(1) // +Inf
	} else if s == "nan" {
		return math.NaN() // NaN
	}
	f, err := strconv.ParseFloat(s, 64)
	if err != nil {
		panic(ParseError{msg: fmt.Sprintf("Invalid float: %s", s)})
	}
	return f
}

func scanUint128(s string) interface{} {
	// Remove the '0x' prefix
	hexStr := s[2:]
	// Parse as uint64 for now (simplified)
	// For full uint128 support, would need big.Int
	var low, high uint64
	if len(hexStr) > 16 {
		highPart := hexStr[:len(hexStr)-16]
		lowPart := hexStr[len(hexStr)-16:]
		high, _ = strconv.ParseUint(highPart, 16, 64)
		low, _ = strconv.ParseUint(lowPart, 16, 64)
	} else {
		low, _ = strconv.ParseUint(hexStr, 16, 64)
		high = 0
	}
	return &pb.UInt128Value{Low: low, High: high}
}

func scanInt128(s string) interface{} {
	// Remove the 'i128' suffix
	numStr := s[:len(s)-4]
	// Use big.Int for full 128-bit precision
	n := new(big.Int)
	n.SetString(numStr, 10)

	var low, high uint64
	if n.Sign() >= 0 {
		// Positive number: extract low and high 64 bits
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(n, mask).Uint64()
		high = new(big.Int).Rsh(n, 64).Uint64()
	} else {
		// Negative number: two's complement representation
		// Add 2^128 to get the unsigned representation
		twoTo128 := new(big.Int).Lsh(big.NewInt(1), 128)
		unsigned := new(big.Int).Add(n, twoTo128)
		mask := new(big.Int).SetUint64(0xFFFFFFFFFFFFFFFF)
		low = new(big.Int).And(unsigned, mask).Uint64()
		high = new(big.Int).Rsh(unsigned, 64).Uint64()
	}
	return &pb.Int128Value{Low: low, High: high}
}

func scanDecimal(s string) interface{} {
	// Decimal is a string like '123.456d12' where the last part after `d` is the
	// precision, and the scale is the number of digits between the decimal point and `d`
	parts := strings.Split(s, "d")
	if len(parts) != 2 {
		panic(ParseError{msg: fmt.Sprintf("Invalid decimal format: %s", s)})
	}
	decParts := strings.Split(parts[0], ".")
	scale := int32(0)
	if len(decParts) == 2 {
		scale = int32(len(decParts[1]))
	}
	precision, _ := strconv.ParseInt(parts[1], 10, 32)

	// Parse the integer value
	intStr := strings.ReplaceAll(parts[0], ".", "")
	n, _ := strconv.ParseInt(intStr, 10, 64)
	var low, high uint64
	if n >= 0 {
		low = uint64(n)
		high = 0
	} else {
		low = uint64(n)
		high = 0xFFFFFFFFFFFFFFFF
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
	return Token{Type: "$", Value: "", Pos: -1}
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
	if token.Type == "LITERAL" && token.Value == literal {
		return true
	}
	if token.Type == "SYMBOL" && token.Value == literal {
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
	// Get the debug info for this fragment
	fragKey := string(fragmentID.Id)
	debugInfoMap := p.idToDebugInfo[fragKey]

	// Convert to DebugInfo protobuf
	var ids []*pb.RelationId
	var origNames []string
	for idKey, name := range debugInfoMap {
		ids = append(ids, &pb.RelationId{IdLow: idKey.Low, IdHigh: idKey.High})
		origNames = append(origNames, name)
	}

	// Create DebugInfo
	debugInfo := &pb.DebugInfo{Ids: ids, OrigNames: origNames}

	// Clear currentFragmentID before the return
	p.currentFragmentID = nil

	// Create and return Fragment
	return &pb.Fragment{Id: fragmentID, Declarations: declarations, DebugInfo: debugInfo}
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
func dictGetValue(m map[string]interface{}, key string) Option[*pb.Value] {
	if v, ok := m[key]; ok {
		if val, ok := v.(*pb.Value); ok {
			return Some(val)
		}
	}
	return Option[*pb.Value]{}
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

	// Handle Option types by extracting .Value field via reflection
	val := reflect.ValueOf(msg)
	if val.Kind() == reflect.Struct {
		// Check if this looks like an Option[T] (has Valid and Value fields)
		validField := val.FieldByName("Valid")
		valueField := val.FieldByName("Value")
		if validField.IsValid() && valueField.IsValid() && validField.Kind() == reflect.Bool {
			// This is an Option type - if Valid is true, use Value
			if validField.Bool() {
				msg = valueField.Interface()
			} else {
				return false
			}
		}
	}

	// For oneOf fields in Go protobuf, the getter returns nil if not set
	// We use reflection to call the getter method
	val = reflect.ValueOf(msg)
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

func (p *Parser) _extract_value_int64(value Option[*pb.Value], default_ int64) int64 {
	if (value.Valid && hasProtoField(value.Value, "int_value")) {
		return value.Value.GetIntValue()
	}
	return default_
}

func (p *Parser) _extract_value_float64(value Option[*pb.Value], default_ float64) float64 {
	if (value.Valid && hasProtoField(value.Value, "float_value")) {
		return value.Value.GetFloatValue()
	}
	return default_
}

func (p *Parser) _extract_value_string(value Option[*pb.Value], default_ string) string {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return value.Value.GetStringValue()
	}
	return default_
}

func (p *Parser) _extract_value_boolean(value Option[*pb.Value], default_ bool) bool {
	if (value.Valid && hasProtoField(value.Value, "boolean_value")) {
		return value.Value.GetBooleanValue()
	}
	return default_
}

func (p *Parser) _extract_value_bytes(value Option[*pb.Value], default_ []byte) []byte {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return []byte(value.Value.GetStringValue())
	}
	return default_
}

func (p *Parser) _extract_value_uint128(value Option[*pb.Value], default_ *pb.UInt128Value) *pb.UInt128Value {
	if (value.Valid && hasProtoField(value.Value, "uint128_value")) {
		return value.Value.GetUint128Value()
	}
	return default_
}

func (p *Parser) _extract_value_string_list(value Option[*pb.Value], default_ []string) []string {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return []string{value.Value.GetStringValue()}
	}
	return default_
}

func (p *Parser) _try_extract_value_int64(value Option[*pb.Value]) Option[int64] {
	if (value.Valid && hasProtoField(value.Value, "int_value")) {
		return Some(value.Value.GetIntValue())
	}
	return Option[int64]{}
}

func (p *Parser) _try_extract_value_float64(value Option[*pb.Value]) Option[float64] {
	if (value.Valid && hasProtoField(value.Value, "float_value")) {
		return Some(value.Value.GetFloatValue())
	}
	return Option[float64]{}
}

func (p *Parser) _try_extract_value_string(value Option[*pb.Value]) Option[string] {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return Some(value.Value.GetStringValue())
	}
	return Option[string]{}
}

func (p *Parser) _try_extract_value_bytes(value Option[*pb.Value]) Option[[]byte] {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return Some([]byte(value.Value.GetStringValue()))
	}
	return Option[[]byte]{}
}

func (p *Parser) _try_extract_value_uint128(value Option[*pb.Value]) Option[*pb.UInt128Value] {
	if (value.Valid && hasProtoField(value.Value, "uint128_value")) {
		return Some(value.Value.GetUint128Value())
	}
	return Option[*pb.UInt128Value]{}
}

func (p *Parser) _try_extract_value_string_list(value Option[*pb.Value]) Option[[]string] {
	if (value.Valid && hasProtoField(value.Value, "string_value")) {
		return Some([]string{value.Value.GetStringValue()})
	}
	return Option[[]string]{}
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1173 := p._extract_value_int64(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1173
	_t1174 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1174
	_t1175 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1175
	_t1176 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1176
	_t1177 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1177
	_t1178 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1178
	_t1179 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1179
	_t1180 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1180
	_t1181 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1181
	_t1182 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1182
	_t1183 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1183
	_t1184 := &pb.CSVConfig{HeaderRow: int32(header_row), Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1184
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1185 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1185
	_t1186 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1186
	_t1187 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1187
	_t1188 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1188
	_t1189 := &pb.BeTreeConfig{Epsilon: epsilon.UnwrapOr(0.0), MaxPivots: max_pivots.UnwrapOr(0), MaxDeltas: max_deltas.UnwrapOr(0), MaxLeaf: max_leaf.UnwrapOr(0)}
	storage_config := _t1189
	_t1190 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1190
	_t1191 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1191
	_t1192 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1192
	_t1193 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1193
	_t1194 := &pb.BeTreeLocator{ElementCount: element_count.UnwrapOr(0), TreeHeight: tree_height.UnwrapOr(0)}
	if root_pageid.Valid {
		_t1194.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid.UnwrapOr(nil)}
	} else {
		_t1194.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data.UnwrapOr(nil)}
	}
	relation_locator := _t1194
	_t1195 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1195
}

func (p *Parser) construct_configure(config_dict [][]interface{}) *pb.Configure {
	config := dictFromList(config_dict)
	maintenance_level_val := dictGetValue(config, "ivm.maintenance_level")
	maintenance_level := pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
	if (maintenance_level_val.Valid && hasProtoField(maintenance_level_val, "string_value")) {
		if maintenance_level_val.Value.GetStringValue() == "off" {
			maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
		} else {
			if maintenance_level_val.Value.GetStringValue() == "auto" {
				maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO
			} else {
				if maintenance_level_val.Value.GetStringValue() == "all" {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL
				} else {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
				}
			}
		}
	} else {
	}
	_t1196 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1196
	_t1197 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1197
	_t1198 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1198
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1199 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1199
	_t1200 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1200
	_t1201 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1201
	_t1202 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1202
	_t1203 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1203
	_t1204 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1204
	_t1205 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1205
	_t1206 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptrInt64(partition_size), Compression: ptrString(compression), SyntaxHeaderRow: ptrBool(syntax_header_row), SyntaxMissingString: ptrString(syntax_missing_string), SyntaxDelim: ptrString(syntax_delim), SyntaxQuotechar: ptrString(syntax_quotechar), SyntaxEscapechar: ptrString(syntax_escapechar)}
	return _t1206
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t353 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t353 = p.matchLookaheadLiteral("configure", 1)
	} else {
		_t353 = false
	}
	var _t355 Option[*pb.Configure]
	if _t353 {
		_t356 := p.parse_configure()
		_t355 = Some(_t356)
	} else {
		_t355 = Option[*pb.Configure]{}
	}
	configure0 := _t355
	var _t357 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t357 = p.matchLookaheadLiteral("sync", 1)
	} else {
		_t357 = false
	}
	var _t359 Option[*pb.Sync]
	if _t357 {
		_t360 := p.parse_sync()
		_t359 = Some(_t360)
	} else {
		_t359 = Option[*pb.Sync]{}
	}
	sync1 := _t359
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	for cond3 {
		_t361 := p.parse_epoch()
		item4 := _t361
		xs2 = listConcat(xs2, []*pb.Epoch{item4})
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	epochs5 := xs2
	p.consumeLiteral(")")
	_t362 := p.construct_configure([][]interface{}{})
	_t363 := &pb.Transaction{Epochs: epochs5, Configure: configure0.UnwrapOr(_t362), Sync: sync1.UnwrapOr(nil)}
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
		xs7 = listConcat(xs7, [][]interface{}{item9})
		cond8 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values10 := xs7
	p.consumeLiteral("}")
	return config_key_values10
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol11 := p.consumeTerminal("SYMBOL").Value.(string)
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
				decimal21 := p.consumeTerminal("DECIMAL").Value.(*pb.DecimalValue)
				_t387 := &pb.Value{}
				_t387.Value = &pb.Value_DecimalValue{DecimalValue: decimal21}
				_t386 = _t387
			} else {
				var _t388 *pb.Value
				if prediction13 == 6 {
					int12820 := p.consumeTerminal("INT128").Value.(*pb.Int128Value)
					_t389 := &pb.Value{}
					_t389.Value = &pb.Value_Int128Value{Int128Value: int12820}
					_t388 = _t389
				} else {
					var _t390 *pb.Value
					if prediction13 == 5 {
						uint12819 := p.consumeTerminal("UINT128").Value.(*pb.UInt128Value)
						_t391 := &pb.Value{}
						_t391.Value = &pb.Value_Uint128Value{Uint128Value: uint12819}
						_t390 = _t391
					} else {
						var _t392 *pb.Value
						if prediction13 == 4 {
							float18 := p.consumeTerminal("FLOAT").Value.(float64)
							_t393 := &pb.Value{}
							_t393.Value = &pb.Value_FloatValue{FloatValue: float18}
							_t392 = _t393
						} else {
							var _t394 *pb.Value
							if prediction13 == 3 {
								int17 := p.consumeTerminal("INT").Value.(int64)
								_t395 := &pb.Value{}
								_t395.Value = &pb.Value_IntValue{IntValue: int17}
								_t394 = _t395
							} else {
								var _t396 *pb.Value
								if prediction13 == 2 {
									string16 := p.consumeTerminal("STRING").Value.(string)
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
	int23 := p.consumeTerminal("INT").Value.(int64)
	int_324 := p.consumeTerminal("INT").Value.(int64)
	int_425 := p.consumeTerminal("INT").Value.(int64)
	p.consumeLiteral(")")
	_t404 := &pb.DateValue{Year: int32(int23), Month: int32(int_324), Day: int32(int_425)}
	return _t404
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int26 := p.consumeTerminal("INT").Value.(int64)
	int_327 := p.consumeTerminal("INT").Value.(int64)
	int_428 := p.consumeTerminal("INT").Value.(int64)
	int_529 := p.consumeTerminal("INT").Value.(int64)
	int_630 := p.consumeTerminal("INT").Value.(int64)
	int_731 := p.consumeTerminal("INT").Value.(int64)
	var _t405 Option[int64]
	if p.matchLookaheadTerminal("INT", 0) {
		_t405 = Some(p.consumeTerminal("INT").Value.(int64))
	} else {
		_t405 = Option[int64]{}
	}
	int_832 := _t405
	p.consumeLiteral(")")
	_t406 := &pb.DateTimeValue{Year: int32(int26), Month: int32(int_327), Day: int32(int_428), Hour: int32(int_529), Minute: int32(int_630), Second: int32(int_731), Microsecond: int32(int_832.UnwrapOr(0))}
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
		xs34 = listConcat(xs34, []*pb.FragmentId{item36})
		cond35 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids37 := xs34
	p.consumeLiteral(")")
	_t412 := &pb.Sync{Fragments: fragment_ids37}
	return _t412
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol38 := p.consumeTerminal("SYMBOL").Value.(string)
	return &pb.FragmentId{Id: []byte(symbol38)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t413 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t413 = p.matchLookaheadLiteral("writes", 1)
	} else {
		_t413 = false
	}
	var _t415 Option[[]*pb.Write]
	if _t413 {
		_t416 := p.parse_epoch_writes()
		_t415 = Some(_t416)
	} else {
		_t415 = Option[[]*pb.Write]{}
	}
	epoch_writes39 := _t415
	var _t418 Option[[]*pb.Read]
	if p.matchLookaheadLiteral("(", 0) {
		_t419 := p.parse_epoch_reads()
		_t418 = Some(_t419)
	} else {
		_t418 = Option[[]*pb.Read]{}
	}
	epoch_reads40 := _t418
	p.consumeLiteral(")")
	_t420 := &pb.Epoch{Writes: epoch_writes39.UnwrapOr(nil), Reads: epoch_reads40.UnwrapOr(nil)}
	return _t420
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs41 := []*pb.Write{}
	cond42 := p.matchLookaheadLiteral("(", 0)
	for cond42 {
		_t421 := p.parse_write()
		item43 := _t421
		xs41 = listConcat(xs41, []*pb.Write{item43})
		cond42 = p.matchLookaheadLiteral("(", 0)
	}
	writes44 := xs41
	p.consumeLiteral(")")
	return writes44
}

func (p *Parser) parse_write() *pb.Write {
	var _t422 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t423 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t423 = 1
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
	} else {
		_t422 = -1
	}
	prediction45 := _t422
	var _t426 *pb.Write
	if prediction45 == 2 {
		_t427 := p.parse_context()
		context48 := _t427
		_t428 := &pb.Write{}
		_t428.WriteType = &pb.Write_Context{Context: context48}
		_t426 = _t428
	} else {
		var _t429 *pb.Write
		if prediction45 == 1 {
			_t430 := p.parse_undefine()
			undefine47 := _t430
			_t431 := &pb.Write{}
			_t431.WriteType = &pb.Write_Undefine{Undefine: undefine47}
			_t429 = _t431
		} else {
			var _t432 *pb.Write
			if prediction45 == 0 {
				_t433 := p.parse_define()
				define46 := _t433
				_t434 := &pb.Write{}
				_t434.WriteType = &pb.Write_Define{Define: define46}
				_t432 = _t434
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
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
	_t435 := p.parse_fragment()
	fragment49 := _t435
	p.consumeLiteral(")")
	_t436 := &pb.Define{Fragment: fragment49}
	return _t436
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t437 := p.parse_new_fragment_id()
	new_fragment_id50 := _t437
	xs51 := []*pb.Declaration{}
	cond52 := p.matchLookaheadLiteral("(", 0)
	for cond52 {
		_t438 := p.parse_declaration()
		item53 := _t438
		xs51 = listConcat(xs51, []*pb.Declaration{item53})
		cond52 = p.matchLookaheadLiteral("(", 0)
	}
	declarations54 := xs51
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id50, declarations54)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t439 := p.parse_fragment_id()
	fragment_id55 := _t439
	p.startFragment(fragment_id55)
	return fragment_id55
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t440 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t441 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t441 = 3
		} else {
			var _t442 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t442 = 2
			} else {
				var _t443 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t443 = 0
				} else {
					var _t444 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t444 = 3
					} else {
						var _t445 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t445 = 3
						} else {
							var _t446 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t446 = 1
							} else {
								_t446 = -1
							}
							_t445 = _t446
						}
						_t444 = _t445
					}
					_t443 = _t444
				}
				_t442 = _t443
			}
			_t441 = _t442
		}
		_t440 = _t441
	} else {
		_t440 = -1
	}
	prediction56 := _t440
	var _t447 *pb.Declaration
	if prediction56 == 3 {
		_t448 := p.parse_data()
		data60 := _t448
		_t449 := &pb.Declaration{}
		_t449.DeclarationType = &pb.Declaration_Data{Data: data60}
		_t447 = _t449
	} else {
		var _t450 *pb.Declaration
		if prediction56 == 2 {
			_t451 := p.parse_constraint()
			constraint59 := _t451
			_t452 := &pb.Declaration{}
			_t452.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint59}
			_t450 = _t452
		} else {
			var _t453 *pb.Declaration
			if prediction56 == 1 {
				_t454 := p.parse_algorithm()
				algorithm58 := _t454
				_t455 := &pb.Declaration{}
				_t455.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm58}
				_t453 = _t455
			} else {
				var _t456 *pb.Declaration
				if prediction56 == 0 {
					_t457 := p.parse_def()
					def57 := _t457
					_t458 := &pb.Declaration{}
					_t458.DeclarationType = &pb.Declaration_Def{Def: def57}
					_t456 = _t458
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t453 = _t456
			}
			_t450 = _t453
		}
		_t447 = _t450
	}
	return _t447
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t459 := p.parse_relation_id()
	relation_id61 := _t459
	_t460 := p.parse_abstraction()
	abstraction62 := _t460
	var _t462 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t463 := p.parse_attrs()
		_t462 = Some(_t463)
	} else {
		_t462 = Option[[]*pb.Attribute]{}
	}
	attrs63 := _t462
	p.consumeLiteral(")")
	_t464 := &pb.Def{Name: relation_id61, Body: abstraction62, Attrs: attrs63.UnwrapOr(nil)}
	return _t464
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t465 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t465 = 0
	} else {
		var _t466 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t466 = 1
		} else {
			_t466 = -1
		}
		_t465 = _t466
	}
	prediction64 := _t465
	var _t467 *pb.RelationId
	if prediction64 == 1 {
		uint12866 := p.consumeTerminal("UINT128").Value.(*pb.UInt128Value)
		_t467 = &pb.RelationId{IdLow: uint12866.Low, IdHigh: uint12866.High}
	} else {
		var _t468 *pb.RelationId
		if prediction64 == 0 {
			p.consumeLiteral(":")
			symbol65 := p.consumeTerminal("SYMBOL").Value.(string)
			_t468 = p.relationIdFromString(symbol65)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t467 = _t468
	}
	return _t467
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t469 := p.parse_bindings()
	bindings67 := _t469
	_t470 := p.parse_formula()
	formula68 := _t470
	p.consumeLiteral(")")
	_t471 := &pb.Abstraction{Vars: listConcat(bindings67[0].([]*pb.Binding), bindings67[1].([]*pb.Binding)), Value: formula68}
	return _t471
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs69 := []*pb.Binding{}
	cond70 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond70 {
		_t472 := p.parse_binding()
		item71 := _t472
		xs69 = listConcat(xs69, []*pb.Binding{item71})
		cond70 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings72 := xs69
	var _t474 Option[[]*pb.Binding]
	if p.matchLookaheadLiteral("|", 0) {
		_t475 := p.parse_value_bindings()
		_t474 = Some(_t475)
	} else {
		_t474 = Option[[]*pb.Binding]{}
	}
	value_bindings73 := _t474
	p.consumeLiteral("]")
	return []interface{}{bindings72, value_bindings73.UnwrapOr(nil)}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol74 := p.consumeTerminal("SYMBOL").Value.(string)
	p.consumeLiteral("::")
	_t476 := p.parse_type()
	type75 := _t476
	_t477 := &pb.Var{Name: symbol74}
	_t478 := &pb.Binding{Var: _t477, Type: type75}
	return _t478
}

func (p *Parser) parse_type() *pb.Type {
	var _t479 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t479 = 0
	} else {
		var _t480 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t480 = 4
		} else {
			var _t481 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t481 = 1
			} else {
				var _t482 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t482 = 8
				} else {
					var _t483 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t483 = 5
					} else {
						var _t484 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t484 = 2
						} else {
							var _t485 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t485 = 3
							} else {
								var _t486 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t486 = 7
								} else {
									var _t487 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t487 = 6
									} else {
										var _t488 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t488 = 10
										} else {
											var _t489 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t489 = 9
											} else {
												_t489 = -1
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
				_t481 = _t482
			}
			_t480 = _t481
		}
		_t479 = _t480
	}
	prediction76 := _t479
	var _t490 *pb.Type
	if prediction76 == 10 {
		_t491 := p.parse_boolean_type()
		boolean_type87 := _t491
		_t492 := &pb.Type{}
		_t492.Type = &pb.Type_BooleanType{BooleanType: boolean_type87}
		_t490 = _t492
	} else {
		var _t493 *pb.Type
		if prediction76 == 9 {
			_t494 := p.parse_decimal_type()
			decimal_type86 := _t494
			_t495 := &pb.Type{}
			_t495.Type = &pb.Type_DecimalType{DecimalType: decimal_type86}
			_t493 = _t495
		} else {
			var _t496 *pb.Type
			if prediction76 == 8 {
				_t497 := p.parse_missing_type()
				missing_type85 := _t497
				_t498 := &pb.Type{}
				_t498.Type = &pb.Type_MissingType{MissingType: missing_type85}
				_t496 = _t498
			} else {
				var _t499 *pb.Type
				if prediction76 == 7 {
					_t500 := p.parse_datetime_type()
					datetime_type84 := _t500
					_t501 := &pb.Type{}
					_t501.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type84}
					_t499 = _t501
				} else {
					var _t502 *pb.Type
					if prediction76 == 6 {
						_t503 := p.parse_date_type()
						date_type83 := _t503
						_t504 := &pb.Type{}
						_t504.Type = &pb.Type_DateType{DateType: date_type83}
						_t502 = _t504
					} else {
						var _t505 *pb.Type
						if prediction76 == 5 {
							_t506 := p.parse_int128_type()
							int128_type82 := _t506
							_t507 := &pb.Type{}
							_t507.Type = &pb.Type_Int128Type{Int128Type: int128_type82}
							_t505 = _t507
						} else {
							var _t508 *pb.Type
							if prediction76 == 4 {
								_t509 := p.parse_uint128_type()
								uint128_type81 := _t509
								_t510 := &pb.Type{}
								_t510.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type81}
								_t508 = _t510
							} else {
								var _t511 *pb.Type
								if prediction76 == 3 {
									_t512 := p.parse_float_type()
									float_type80 := _t512
									_t513 := &pb.Type{}
									_t513.Type = &pb.Type_FloatType{FloatType: float_type80}
									_t511 = _t513
								} else {
									var _t514 *pb.Type
									if prediction76 == 2 {
										_t515 := p.parse_int_type()
										int_type79 := _t515
										_t516 := &pb.Type{}
										_t516.Type = &pb.Type_IntType{IntType: int_type79}
										_t514 = _t516
									} else {
										var _t517 *pb.Type
										if prediction76 == 1 {
											_t518 := p.parse_string_type()
											string_type78 := _t518
											_t519 := &pb.Type{}
											_t519.Type = &pb.Type_StringType{StringType: string_type78}
											_t517 = _t519
										} else {
											var _t520 *pb.Type
											if prediction76 == 0 {
												_t521 := p.parse_unspecified_type()
												unspecified_type77 := _t521
												_t522 := &pb.Type{}
												_t522.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type77}
												_t520 = _t522
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
		_t490 = _t493
	}
	return _t490
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t523 := &pb.UnspecifiedType{}
	return _t523
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t524 := &pb.StringType{}
	return _t524
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t525 := &pb.IntType{}
	return _t525
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t526 := &pb.FloatType{}
	return _t526
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t527 := &pb.UInt128Type{}
	return _t527
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t528 := &pb.Int128Type{}
	return _t528
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t529 := &pb.DateType{}
	return _t529
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t530 := &pb.DateTimeType{}
	return _t530
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t531 := &pb.MissingType{}
	return _t531
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int88 := p.consumeTerminal("INT").Value.(int64)
	int_389 := p.consumeTerminal("INT").Value.(int64)
	p.consumeLiteral(")")
	_t532 := &pb.DecimalType{Precision: int32(int88), Scale: int32(int_389)}
	return _t532
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t533 := &pb.BooleanType{}
	return _t533
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs90 := []*pb.Binding{}
	cond91 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond91 {
		_t534 := p.parse_binding()
		item92 := _t534
		xs90 = listConcat(xs90, []*pb.Binding{item92})
		cond91 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings93 := xs90
	return bindings93
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t535 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t536 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t536 = 0
		} else {
			var _t537 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t537 = 11
			} else {
				var _t538 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t538 = 3
				} else {
					var _t539 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t539 = 10
					} else {
						var _t540 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t540 = 9
						} else {
							var _t541 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t541 = 5
							} else {
								var _t542 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t542 = 6
								} else {
									var _t543 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t543 = 7
									} else {
										var _t544 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t544 = 1
										} else {
											var _t545 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t545 = 2
											} else {
												var _t546 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t546 = 12
												} else {
													var _t547 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t547 = 8
													} else {
														var _t548 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t548 = 4
														} else {
															var _t549 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t549 = 10
															} else {
																var _t550 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t550 = 10
																} else {
																	var _t551 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t551 = 10
																	} else {
																		var _t552 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t552 = 10
																		} else {
																			var _t553 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t553 = 10
																			} else {
																				var _t554 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t554 = 10
																				} else {
																					var _t555 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t555 = 10
																					} else {
																						var _t556 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t556 = 10
																						} else {
																							var _t557 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t557 = 10
																							} else {
																								_t557 = -1
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
				}
				_t537 = _t538
			}
			_t536 = _t537
		}
		_t535 = _t536
	} else {
		_t535 = -1
	}
	prediction94 := _t535
	var _t558 *pb.Formula
	if prediction94 == 12 {
		_t559 := p.parse_cast()
		cast107 := _t559
		_t560 := &pb.Formula{}
		_t560.FormulaType = &pb.Formula_Cast{Cast: cast107}
		_t558 = _t560
	} else {
		var _t561 *pb.Formula
		if prediction94 == 11 {
			_t562 := p.parse_rel_atom()
			rel_atom106 := _t562
			_t563 := &pb.Formula{}
			_t563.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom106}
			_t561 = _t563
		} else {
			var _t564 *pb.Formula
			if prediction94 == 10 {
				_t565 := p.parse_primitive()
				primitive105 := _t565
				_t566 := &pb.Formula{}
				_t566.FormulaType = &pb.Formula_Primitive{Primitive: primitive105}
				_t564 = _t566
			} else {
				var _t567 *pb.Formula
				if prediction94 == 9 {
					_t568 := p.parse_pragma()
					pragma104 := _t568
					_t569 := &pb.Formula{}
					_t569.FormulaType = &pb.Formula_Pragma{Pragma: pragma104}
					_t567 = _t569
				} else {
					var _t570 *pb.Formula
					if prediction94 == 8 {
						_t571 := p.parse_atom()
						atom103 := _t571
						_t572 := &pb.Formula{}
						_t572.FormulaType = &pb.Formula_Atom{Atom: atom103}
						_t570 = _t572
					} else {
						var _t573 *pb.Formula
						if prediction94 == 7 {
							_t574 := p.parse_ffi()
							ffi102 := _t574
							_t575 := &pb.Formula{}
							_t575.FormulaType = &pb.Formula_Ffi{Ffi: ffi102}
							_t573 = _t575
						} else {
							var _t576 *pb.Formula
							if prediction94 == 6 {
								_t577 := p.parse_not()
								not101 := _t577
								_t578 := &pb.Formula{}
								_t578.FormulaType = &pb.Formula_Not{Not: not101}
								_t576 = _t578
							} else {
								var _t579 *pb.Formula
								if prediction94 == 5 {
									_t580 := p.parse_disjunction()
									disjunction100 := _t580
									_t581 := &pb.Formula{}
									_t581.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction100}
									_t579 = _t581
								} else {
									var _t582 *pb.Formula
									if prediction94 == 4 {
										_t583 := p.parse_conjunction()
										conjunction99 := _t583
										_t584 := &pb.Formula{}
										_t584.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction99}
										_t582 = _t584
									} else {
										var _t585 *pb.Formula
										if prediction94 == 3 {
											_t586 := p.parse_reduce()
											reduce98 := _t586
											_t587 := &pb.Formula{}
											_t587.FormulaType = &pb.Formula_Reduce{Reduce: reduce98}
											_t585 = _t587
										} else {
											var _t588 *pb.Formula
											if prediction94 == 2 {
												_t589 := p.parse_exists()
												exists97 := _t589
												_t590 := &pb.Formula{}
												_t590.FormulaType = &pb.Formula_Exists{Exists: exists97}
												_t588 = _t590
											} else {
												var _t591 *pb.Formula
												if prediction94 == 1 {
													_t592 := p.parse_false()
													false96 := _t592
													_t593 := &pb.Formula{}
													_t593.FormulaType = &pb.Formula_Disjunction{Disjunction: false96}
													_t591 = _t593
												} else {
													var _t594 *pb.Formula
													if prediction94 == 0 {
														_t595 := p.parse_true()
														true95 := _t595
														_t596 := &pb.Formula{}
														_t596.FormulaType = &pb.Formula_Conjunction{Conjunction: true95}
														_t594 = _t596
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
		_t558 = _t561
	}
	return _t558
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t597 := &pb.Conjunction{Args: nil}
	return _t597
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t598 := &pb.Disjunction{Args: nil}
	return _t598
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t599 := p.parse_bindings()
	bindings108 := _t599
	_t600 := p.parse_formula()
	formula109 := _t600
	p.consumeLiteral(")")
	_t601 := &pb.Abstraction{Vars: listConcat(bindings108[0].([]*pb.Binding), bindings108[1].([]*pb.Binding)), Value: formula109}
	_t602 := &pb.Exists{Body: _t601}
	return _t602
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t603 := p.parse_abstraction()
	abstraction110 := _t603
	_t604 := p.parse_abstraction()
	abstraction_3111 := _t604
	_t605 := p.parse_terms()
	terms112 := _t605
	p.consumeLiteral(")")
	_t606 := &pb.Reduce{Op: abstraction110, Body: abstraction_3111, Terms: terms112}
	return _t606
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs113 := []*pb.Term{}
	var _t607 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t607 = true
	} else {
		_t607 = p.matchLookaheadLiteral("false", 0)
	}
	var _t608 bool
	if _t607 {
		_t608 = true
	} else {
		_t608 = p.matchLookaheadLiteral("missing", 0)
	}
	var _t609 bool
	if _t608 {
		_t609 = true
	} else {
		_t609 = p.matchLookaheadLiteral("true", 0)
	}
	var _t610 bool
	if _t609 {
		_t610 = true
	} else {
		_t610 = p.matchLookaheadTerminal("DECIMAL", 0)
	}
	var _t611 bool
	if _t610 {
		_t611 = true
	} else {
		_t611 = p.matchLookaheadTerminal("FLOAT", 0)
	}
	var _t612 bool
	if _t611 {
		_t612 = true
	} else {
		_t612 = p.matchLookaheadTerminal("INT", 0)
	}
	var _t613 bool
	if _t612 {
		_t613 = true
	} else {
		_t613 = p.matchLookaheadTerminal("INT128", 0)
	}
	var _t614 bool
	if _t613 {
		_t614 = true
	} else {
		_t614 = p.matchLookaheadTerminal("STRING", 0)
	}
	var _t615 bool
	if _t614 {
		_t615 = true
	} else {
		_t615 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	var _t616 bool
	if _t615 {
		_t616 = true
	} else {
		_t616 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond114 := _t616
	for cond114 {
		_t617 := p.parse_term()
		item115 := _t617
		xs113 = listConcat(xs113, []*pb.Term{item115})
		var _t618 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t618 = true
		} else {
			_t618 = p.matchLookaheadLiteral("false", 0)
		}
		var _t619 bool
		if _t618 {
			_t619 = true
		} else {
			_t619 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t620 bool
		if _t619 {
			_t620 = true
		} else {
			_t620 = p.matchLookaheadLiteral("true", 0)
		}
		var _t621 bool
		if _t620 {
			_t621 = true
		} else {
			_t621 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t622 bool
		if _t621 {
			_t622 = true
		} else {
			_t622 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t623 bool
		if _t622 {
			_t623 = true
		} else {
			_t623 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t624 bool
		if _t623 {
			_t624 = true
		} else {
			_t624 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t625 bool
		if _t624 {
			_t625 = true
		} else {
			_t625 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t626 bool
		if _t625 {
			_t626 = true
		} else {
			_t626 = p.matchLookaheadTerminal("SYMBOL", 0)
		}
		var _t627 bool
		if _t626 {
			_t627 = true
		} else {
			_t627 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond114 = _t627
	}
	terms116 := xs113
	p.consumeLiteral(")")
	return terms116
}

func (p *Parser) parse_term() *pb.Term {
	var _t628 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t628 = 1
	} else {
		var _t629 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t629 = 1
		} else {
			var _t630 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t630 = 1
			} else {
				var _t631 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t631 = 1
				} else {
					var _t632 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t632 = 1
					} else {
						var _t633 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t633 = 0
						} else {
							var _t634 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t634 = 1
							} else {
								var _t635 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t635 = 1
								} else {
									var _t636 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t636 = 1
									} else {
										var _t637 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t637 = 1
										} else {
											var _t638 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t638 = 1
											} else {
												_t638 = -1
											}
											_t637 = _t638
										}
										_t636 = _t637
									}
									_t635 = _t636
								}
								_t634 = _t635
							}
							_t633 = _t634
						}
						_t632 = _t633
					}
					_t631 = _t632
				}
				_t630 = _t631
			}
			_t629 = _t630
		}
		_t628 = _t629
	}
	prediction117 := _t628
	var _t639 *pb.Term
	if prediction117 == 1 {
		_t640 := p.parse_constant()
		constant119 := _t640
		_t641 := &pb.Term{}
		_t641.TermType = &pb.Term_Constant{Constant: constant119}
		_t639 = _t641
	} else {
		var _t642 *pb.Term
		if prediction117 == 0 {
			_t643 := p.parse_var()
			var118 := _t643
			_t644 := &pb.Term{}
			_t644.TermType = &pb.Term_Var{Var: var118}
			_t642 = _t644
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t639 = _t642
	}
	return _t639
}

func (p *Parser) parse_var() *pb.Var {
	symbol120 := p.consumeTerminal("SYMBOL").Value.(string)
	_t645 := &pb.Var{Name: symbol120}
	return _t645
}

func (p *Parser) parse_constant() *pb.Value {
	_t646 := p.parse_value()
	value121 := _t646
	return value121
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs122 := []*pb.Formula{}
	cond123 := p.matchLookaheadLiteral("(", 0)
	for cond123 {
		_t647 := p.parse_formula()
		item124 := _t647
		xs122 = listConcat(xs122, []*pb.Formula{item124})
		cond123 = p.matchLookaheadLiteral("(", 0)
	}
	formulas125 := xs122
	p.consumeLiteral(")")
	_t648 := &pb.Conjunction{Args: formulas125}
	return _t648
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs126 := []*pb.Formula{}
	cond127 := p.matchLookaheadLiteral("(", 0)
	for cond127 {
		_t649 := p.parse_formula()
		item128 := _t649
		xs126 = listConcat(xs126, []*pb.Formula{item128})
		cond127 = p.matchLookaheadLiteral("(", 0)
	}
	formulas129 := xs126
	p.consumeLiteral(")")
	_t650 := &pb.Disjunction{Args: formulas129}
	return _t650
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t651 := p.parse_formula()
	formula130 := _t651
	p.consumeLiteral(")")
	_t652 := &pb.Not{Arg: formula130}
	return _t652
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t653 := p.parse_name()
	name131 := _t653
	_t654 := p.parse_ffi_args()
	ffi_args132 := _t654
	_t655 := p.parse_terms()
	terms133 := _t655
	p.consumeLiteral(")")
	_t656 := &pb.FFI{Name: name131, Args: ffi_args132, Terms: terms133}
	return _t656
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol134 := p.consumeTerminal("SYMBOL").Value.(string)
	return symbol134
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs135 := []*pb.Abstraction{}
	cond136 := p.matchLookaheadLiteral("(", 0)
	for cond136 {
		_t657 := p.parse_abstraction()
		item137 := _t657
		xs135 = listConcat(xs135, []*pb.Abstraction{item137})
		cond136 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions138 := xs135
	p.consumeLiteral(")")
	return abstractions138
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t658 := p.parse_relation_id()
	relation_id139 := _t658
	xs140 := []*pb.Term{}
	var _t659 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t659 = true
	} else {
		_t659 = p.matchLookaheadLiteral("false", 0)
	}
	var _t660 bool
	if _t659 {
		_t660 = true
	} else {
		_t660 = p.matchLookaheadLiteral("missing", 0)
	}
	var _t661 bool
	if _t660 {
		_t661 = true
	} else {
		_t661 = p.matchLookaheadLiteral("true", 0)
	}
	var _t662 bool
	if _t661 {
		_t662 = true
	} else {
		_t662 = p.matchLookaheadTerminal("DECIMAL", 0)
	}
	var _t663 bool
	if _t662 {
		_t663 = true
	} else {
		_t663 = p.matchLookaheadTerminal("FLOAT", 0)
	}
	var _t664 bool
	if _t663 {
		_t664 = true
	} else {
		_t664 = p.matchLookaheadTerminal("INT", 0)
	}
	var _t665 bool
	if _t664 {
		_t665 = true
	} else {
		_t665 = p.matchLookaheadTerminal("INT128", 0)
	}
	var _t666 bool
	if _t665 {
		_t666 = true
	} else {
		_t666 = p.matchLookaheadTerminal("STRING", 0)
	}
	var _t667 bool
	if _t666 {
		_t667 = true
	} else {
		_t667 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	var _t668 bool
	if _t667 {
		_t668 = true
	} else {
		_t668 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond141 := _t668
	for cond141 {
		_t669 := p.parse_term()
		item142 := _t669
		xs140 = listConcat(xs140, []*pb.Term{item142})
		var _t670 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t670 = true
		} else {
			_t670 = p.matchLookaheadLiteral("false", 0)
		}
		var _t671 bool
		if _t670 {
			_t671 = true
		} else {
			_t671 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t672 bool
		if _t671 {
			_t672 = true
		} else {
			_t672 = p.matchLookaheadLiteral("true", 0)
		}
		var _t673 bool
		if _t672 {
			_t673 = true
		} else {
			_t673 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t674 bool
		if _t673 {
			_t674 = true
		} else {
			_t674 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t675 bool
		if _t674 {
			_t675 = true
		} else {
			_t675 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t676 bool
		if _t675 {
			_t676 = true
		} else {
			_t676 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t677 bool
		if _t676 {
			_t677 = true
		} else {
			_t677 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t678 bool
		if _t677 {
			_t678 = true
		} else {
			_t678 = p.matchLookaheadTerminal("SYMBOL", 0)
		}
		var _t679 bool
		if _t678 {
			_t679 = true
		} else {
			_t679 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond141 = _t679
	}
	terms143 := xs140
	p.consumeLiteral(")")
	_t680 := &pb.Atom{Name: relation_id139, Terms: terms143}
	return _t680
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t681 := p.parse_name()
	name144 := _t681
	xs145 := []*pb.Term{}
	var _t682 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t682 = true
	} else {
		_t682 = p.matchLookaheadLiteral("false", 0)
	}
	var _t683 bool
	if _t682 {
		_t683 = true
	} else {
		_t683 = p.matchLookaheadLiteral("missing", 0)
	}
	var _t684 bool
	if _t683 {
		_t684 = true
	} else {
		_t684 = p.matchLookaheadLiteral("true", 0)
	}
	var _t685 bool
	if _t684 {
		_t685 = true
	} else {
		_t685 = p.matchLookaheadTerminal("DECIMAL", 0)
	}
	var _t686 bool
	if _t685 {
		_t686 = true
	} else {
		_t686 = p.matchLookaheadTerminal("FLOAT", 0)
	}
	var _t687 bool
	if _t686 {
		_t687 = true
	} else {
		_t687 = p.matchLookaheadTerminal("INT", 0)
	}
	var _t688 bool
	if _t687 {
		_t688 = true
	} else {
		_t688 = p.matchLookaheadTerminal("INT128", 0)
	}
	var _t689 bool
	if _t688 {
		_t689 = true
	} else {
		_t689 = p.matchLookaheadTerminal("STRING", 0)
	}
	var _t690 bool
	if _t689 {
		_t690 = true
	} else {
		_t690 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	var _t691 bool
	if _t690 {
		_t691 = true
	} else {
		_t691 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond146 := _t691
	for cond146 {
		_t692 := p.parse_term()
		item147 := _t692
		xs145 = listConcat(xs145, []*pb.Term{item147})
		var _t693 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t693 = true
		} else {
			_t693 = p.matchLookaheadLiteral("false", 0)
		}
		var _t694 bool
		if _t693 {
			_t694 = true
		} else {
			_t694 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t695 bool
		if _t694 {
			_t695 = true
		} else {
			_t695 = p.matchLookaheadLiteral("true", 0)
		}
		var _t696 bool
		if _t695 {
			_t696 = true
		} else {
			_t696 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t697 bool
		if _t696 {
			_t697 = true
		} else {
			_t697 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t698 bool
		if _t697 {
			_t698 = true
		} else {
			_t698 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t699 bool
		if _t698 {
			_t699 = true
		} else {
			_t699 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t700 bool
		if _t699 {
			_t700 = true
		} else {
			_t700 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t701 bool
		if _t700 {
			_t701 = true
		} else {
			_t701 = p.matchLookaheadTerminal("SYMBOL", 0)
		}
		var _t702 bool
		if _t701 {
			_t702 = true
		} else {
			_t702 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond146 = _t702
	}
	terms148 := xs145
	p.consumeLiteral(")")
	_t703 := &pb.Pragma{Name: name144, Terms: terms148}
	return _t703
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t704 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t705 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t705 = 9
		} else {
			var _t706 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t706 = 4
			} else {
				var _t707 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t707 = 3
				} else {
					var _t708 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t708 = 0
					} else {
						var _t709 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t709 = 2
						} else {
							var _t710 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t710 = 1
							} else {
								var _t711 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t711 = 8
								} else {
									var _t712 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t712 = 6
									} else {
										var _t713 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t713 = 5
										} else {
											var _t714 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t714 = 7
											} else {
												_t714 = -1
											}
											_t713 = _t714
										}
										_t712 = _t713
									}
									_t711 = _t712
								}
								_t710 = _t711
							}
							_t709 = _t710
						}
						_t708 = _t709
					}
					_t707 = _t708
				}
				_t706 = _t707
			}
			_t705 = _t706
		}
		_t704 = _t705
	} else {
		_t704 = -1
	}
	prediction149 := _t704
	var _t715 *pb.Primitive
	if prediction149 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t716 := p.parse_name()
		name159 := _t716
		xs160 := []*pb.RelTerm{}
		var _t717 bool
		if p.matchLookaheadLiteral("#", 0) {
			_t717 = true
		} else {
			_t717 = p.matchLookaheadLiteral("(", 0)
		}
		var _t718 bool
		if _t717 {
			_t718 = true
		} else {
			_t718 = p.matchLookaheadLiteral("false", 0)
		}
		var _t719 bool
		if _t718 {
			_t719 = true
		} else {
			_t719 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t720 bool
		if _t719 {
			_t720 = true
		} else {
			_t720 = p.matchLookaheadLiteral("true", 0)
		}
		var _t721 bool
		if _t720 {
			_t721 = true
		} else {
			_t721 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t722 bool
		if _t721 {
			_t722 = true
		} else {
			_t722 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t723 bool
		if _t722 {
			_t723 = true
		} else {
			_t723 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t724 bool
		if _t723 {
			_t724 = true
		} else {
			_t724 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t725 bool
		if _t724 {
			_t725 = true
		} else {
			_t725 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t726 bool
		if _t725 {
			_t726 = true
		} else {
			_t726 = p.matchLookaheadTerminal("SYMBOL", 0)
		}
		var _t727 bool
		if _t726 {
			_t727 = true
		} else {
			_t727 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond161 := _t727
		for cond161 {
			_t728 := p.parse_rel_term()
			item162 := _t728
			xs160 = listConcat(xs160, []*pb.RelTerm{item162})
			var _t729 bool
			if p.matchLookaheadLiteral("#", 0) {
				_t729 = true
			} else {
				_t729 = p.matchLookaheadLiteral("(", 0)
			}
			var _t730 bool
			if _t729 {
				_t730 = true
			} else {
				_t730 = p.matchLookaheadLiteral("false", 0)
			}
			var _t731 bool
			if _t730 {
				_t731 = true
			} else {
				_t731 = p.matchLookaheadLiteral("missing", 0)
			}
			var _t732 bool
			if _t731 {
				_t732 = true
			} else {
				_t732 = p.matchLookaheadLiteral("true", 0)
			}
			var _t733 bool
			if _t732 {
				_t733 = true
			} else {
				_t733 = p.matchLookaheadTerminal("DECIMAL", 0)
			}
			var _t734 bool
			if _t733 {
				_t734 = true
			} else {
				_t734 = p.matchLookaheadTerminal("FLOAT", 0)
			}
			var _t735 bool
			if _t734 {
				_t735 = true
			} else {
				_t735 = p.matchLookaheadTerminal("INT", 0)
			}
			var _t736 bool
			if _t735 {
				_t736 = true
			} else {
				_t736 = p.matchLookaheadTerminal("INT128", 0)
			}
			var _t737 bool
			if _t736 {
				_t737 = true
			} else {
				_t737 = p.matchLookaheadTerminal("STRING", 0)
			}
			var _t738 bool
			if _t737 {
				_t738 = true
			} else {
				_t738 = p.matchLookaheadTerminal("SYMBOL", 0)
			}
			var _t739 bool
			if _t738 {
				_t739 = true
			} else {
				_t739 = p.matchLookaheadTerminal("UINT128", 0)
			}
			cond161 = _t739
		}
		rel_terms163 := xs160
		p.consumeLiteral(")")
		_t740 := &pb.Primitive{Name: name159, Terms: rel_terms163}
		_t715 = _t740
	} else {
		var _t741 *pb.Primitive
		if prediction149 == 8 {
			_t742 := p.parse_divide()
			divide158 := _t742
			_t741 = divide158
		} else {
			var _t743 *pb.Primitive
			if prediction149 == 7 {
				_t744 := p.parse_multiply()
				multiply157 := _t744
				_t743 = multiply157
			} else {
				var _t745 *pb.Primitive
				if prediction149 == 6 {
					_t746 := p.parse_minus()
					minus156 := _t746
					_t745 = minus156
				} else {
					var _t747 *pb.Primitive
					if prediction149 == 5 {
						_t748 := p.parse_add()
						add155 := _t748
						_t747 = add155
					} else {
						var _t749 *pb.Primitive
						if prediction149 == 4 {
							_t750 := p.parse_gt_eq()
							gt_eq154 := _t750
							_t749 = gt_eq154
						} else {
							var _t751 *pb.Primitive
							if prediction149 == 3 {
								_t752 := p.parse_gt()
								gt153 := _t752
								_t751 = gt153
							} else {
								var _t753 *pb.Primitive
								if prediction149 == 2 {
									_t754 := p.parse_lt_eq()
									lt_eq152 := _t754
									_t753 = lt_eq152
								} else {
									var _t755 *pb.Primitive
									if prediction149 == 1 {
										_t756 := p.parse_lt()
										lt151 := _t756
										_t755 = lt151
									} else {
										var _t757 *pb.Primitive
										if prediction149 == 0 {
											_t758 := p.parse_eq()
											eq150 := _t758
											_t757 = eq150
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t755 = _t757
									}
									_t753 = _t755
								}
								_t751 = _t753
							}
							_t749 = _t751
						}
						_t747 = _t749
					}
					_t745 = _t747
				}
				_t743 = _t745
			}
			_t741 = _t743
		}
		_t715 = _t741
	}
	return _t715
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t759 := p.parse_term()
	term164 := _t759
	_t760 := p.parse_term()
	term_3165 := _t760
	p.consumeLiteral(")")
	_t761 := &pb.RelTerm{}
	_t761.RelTermType = &pb.RelTerm_Term{Term: term164}
	_t762 := &pb.RelTerm{}
	_t762.RelTermType = &pb.RelTerm_Term{Term: term_3165}
	_t763 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t761, _t762}}
	return _t763
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t764 := p.parse_term()
	term166 := _t764
	_t765 := p.parse_term()
	term_3167 := _t765
	p.consumeLiteral(")")
	_t766 := &pb.RelTerm{}
	_t766.RelTermType = &pb.RelTerm_Term{Term: term166}
	_t767 := &pb.RelTerm{}
	_t767.RelTermType = &pb.RelTerm_Term{Term: term_3167}
	_t768 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t766, _t767}}
	return _t768
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t769 := p.parse_term()
	term168 := _t769
	_t770 := p.parse_term()
	term_3169 := _t770
	p.consumeLiteral(")")
	_t771 := &pb.RelTerm{}
	_t771.RelTermType = &pb.RelTerm_Term{Term: term168}
	_t772 := &pb.RelTerm{}
	_t772.RelTermType = &pb.RelTerm_Term{Term: term_3169}
	_t773 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t771, _t772}}
	return _t773
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t774 := p.parse_term()
	term170 := _t774
	_t775 := p.parse_term()
	term_3171 := _t775
	p.consumeLiteral(")")
	_t776 := &pb.RelTerm{}
	_t776.RelTermType = &pb.RelTerm_Term{Term: term170}
	_t777 := &pb.RelTerm{}
	_t777.RelTermType = &pb.RelTerm_Term{Term: term_3171}
	_t778 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t776, _t777}}
	return _t778
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t779 := p.parse_term()
	term172 := _t779
	_t780 := p.parse_term()
	term_3173 := _t780
	p.consumeLiteral(")")
	_t781 := &pb.RelTerm{}
	_t781.RelTermType = &pb.RelTerm_Term{Term: term172}
	_t782 := &pb.RelTerm{}
	_t782.RelTermType = &pb.RelTerm_Term{Term: term_3173}
	_t783 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t781, _t782}}
	return _t783
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t784 := p.parse_term()
	term174 := _t784
	_t785 := p.parse_term()
	term_3175 := _t785
	_t786 := p.parse_term()
	term_4176 := _t786
	p.consumeLiteral(")")
	_t787 := &pb.RelTerm{}
	_t787.RelTermType = &pb.RelTerm_Term{Term: term174}
	_t788 := &pb.RelTerm{}
	_t788.RelTermType = &pb.RelTerm_Term{Term: term_3175}
	_t789 := &pb.RelTerm{}
	_t789.RelTermType = &pb.RelTerm_Term{Term: term_4176}
	_t790 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t787, _t788, _t789}}
	return _t790
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t791 := p.parse_term()
	term177 := _t791
	_t792 := p.parse_term()
	term_3178 := _t792
	_t793 := p.parse_term()
	term_4179 := _t793
	p.consumeLiteral(")")
	_t794 := &pb.RelTerm{}
	_t794.RelTermType = &pb.RelTerm_Term{Term: term177}
	_t795 := &pb.RelTerm{}
	_t795.RelTermType = &pb.RelTerm_Term{Term: term_3178}
	_t796 := &pb.RelTerm{}
	_t796.RelTermType = &pb.RelTerm_Term{Term: term_4179}
	_t797 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t794, _t795, _t796}}
	return _t797
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t798 := p.parse_term()
	term180 := _t798
	_t799 := p.parse_term()
	term_3181 := _t799
	_t800 := p.parse_term()
	term_4182 := _t800
	p.consumeLiteral(")")
	_t801 := &pb.RelTerm{}
	_t801.RelTermType = &pb.RelTerm_Term{Term: term180}
	_t802 := &pb.RelTerm{}
	_t802.RelTermType = &pb.RelTerm_Term{Term: term_3181}
	_t803 := &pb.RelTerm{}
	_t803.RelTermType = &pb.RelTerm_Term{Term: term_4182}
	_t804 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t801, _t802, _t803}}
	return _t804
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t805 := p.parse_term()
	term183 := _t805
	_t806 := p.parse_term()
	term_3184 := _t806
	_t807 := p.parse_term()
	term_4185 := _t807
	p.consumeLiteral(")")
	_t808 := &pb.RelTerm{}
	_t808.RelTermType = &pb.RelTerm_Term{Term: term183}
	_t809 := &pb.RelTerm{}
	_t809.RelTermType = &pb.RelTerm_Term{Term: term_3184}
	_t810 := &pb.RelTerm{}
	_t810.RelTermType = &pb.RelTerm_Term{Term: term_4185}
	_t811 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t808, _t809, _t810}}
	return _t811
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t812 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t812 = 1
	} else {
		var _t813 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t813 = 1
		} else {
			var _t814 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t814 = 1
			} else {
				var _t815 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t815 = 1
				} else {
					var _t816 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t816 = 0
					} else {
						var _t817 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t817 = 1
						} else {
							var _t818 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t818 = 1
							} else {
								var _t819 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t819 = 1
								} else {
									var _t820 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t820 = 1
									} else {
										var _t821 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t821 = 1
										} else {
											var _t822 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t822 = 1
											} else {
												var _t823 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t823 = 1
												} else {
													_t823 = -1
												}
												_t822 = _t823
											}
											_t821 = _t822
										}
										_t820 = _t821
									}
									_t819 = _t820
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
	prediction186 := _t812
	var _t824 *pb.RelTerm
	if prediction186 == 1 {
		_t825 := p.parse_term()
		term188 := _t825
		_t826 := &pb.RelTerm{}
		_t826.RelTermType = &pb.RelTerm_Term{Term: term188}
		_t824 = _t826
	} else {
		var _t827 *pb.RelTerm
		if prediction186 == 0 {
			_t828 := p.parse_specialized_value()
			specialized_value187 := _t828
			_t829 := &pb.RelTerm{}
			_t829.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value187}
			_t827 = _t829
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t824 = _t827
	}
	return _t824
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t830 := p.parse_value()
	value189 := _t830
	return value189
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t831 := p.parse_name()
	name190 := _t831
	xs191 := []*pb.RelTerm{}
	var _t832 bool
	if p.matchLookaheadLiteral("#", 0) {
		_t832 = true
	} else {
		_t832 = p.matchLookaheadLiteral("(", 0)
	}
	var _t833 bool
	if _t832 {
		_t833 = true
	} else {
		_t833 = p.matchLookaheadLiteral("false", 0)
	}
	var _t834 bool
	if _t833 {
		_t834 = true
	} else {
		_t834 = p.matchLookaheadLiteral("missing", 0)
	}
	var _t835 bool
	if _t834 {
		_t835 = true
	} else {
		_t835 = p.matchLookaheadLiteral("true", 0)
	}
	var _t836 bool
	if _t835 {
		_t836 = true
	} else {
		_t836 = p.matchLookaheadTerminal("DECIMAL", 0)
	}
	var _t837 bool
	if _t836 {
		_t837 = true
	} else {
		_t837 = p.matchLookaheadTerminal("FLOAT", 0)
	}
	var _t838 bool
	if _t837 {
		_t838 = true
	} else {
		_t838 = p.matchLookaheadTerminal("INT", 0)
	}
	var _t839 bool
	if _t838 {
		_t839 = true
	} else {
		_t839 = p.matchLookaheadTerminal("INT128", 0)
	}
	var _t840 bool
	if _t839 {
		_t840 = true
	} else {
		_t840 = p.matchLookaheadTerminal("STRING", 0)
	}
	var _t841 bool
	if _t840 {
		_t841 = true
	} else {
		_t841 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	var _t842 bool
	if _t841 {
		_t842 = true
	} else {
		_t842 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond192 := _t842
	for cond192 {
		_t843 := p.parse_rel_term()
		item193 := _t843
		xs191 = listConcat(xs191, []*pb.RelTerm{item193})
		var _t844 bool
		if p.matchLookaheadLiteral("#", 0) {
			_t844 = true
		} else {
			_t844 = p.matchLookaheadLiteral("(", 0)
		}
		var _t845 bool
		if _t844 {
			_t845 = true
		} else {
			_t845 = p.matchLookaheadLiteral("false", 0)
		}
		var _t846 bool
		if _t845 {
			_t846 = true
		} else {
			_t846 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t847 bool
		if _t846 {
			_t847 = true
		} else {
			_t847 = p.matchLookaheadLiteral("true", 0)
		}
		var _t848 bool
		if _t847 {
			_t848 = true
		} else {
			_t848 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t849 bool
		if _t848 {
			_t849 = true
		} else {
			_t849 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t850 bool
		if _t849 {
			_t850 = true
		} else {
			_t850 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t851 bool
		if _t850 {
			_t851 = true
		} else {
			_t851 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t852 bool
		if _t851 {
			_t852 = true
		} else {
			_t852 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t853 bool
		if _t852 {
			_t853 = true
		} else {
			_t853 = p.matchLookaheadTerminal("SYMBOL", 0)
		}
		var _t854 bool
		if _t853 {
			_t854 = true
		} else {
			_t854 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond192 = _t854
	}
	rel_terms194 := xs191
	p.consumeLiteral(")")
	_t855 := &pb.RelAtom{Name: name190, Terms: rel_terms194}
	return _t855
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t856 := p.parse_term()
	term195 := _t856
	_t857 := p.parse_term()
	term_3196 := _t857
	p.consumeLiteral(")")
	_t858 := &pb.Cast{Input: term195, Result: term_3196}
	return _t858
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs197 := []*pb.Attribute{}
	cond198 := p.matchLookaheadLiteral("(", 0)
	for cond198 {
		_t859 := p.parse_attribute()
		item199 := _t859
		xs197 = listConcat(xs197, []*pb.Attribute{item199})
		cond198 = p.matchLookaheadLiteral("(", 0)
	}
	attributes200 := xs197
	p.consumeLiteral(")")
	return attributes200
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t860 := p.parse_name()
	name201 := _t860
	xs202 := []*pb.Value{}
	var _t861 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t861 = true
	} else {
		_t861 = p.matchLookaheadLiteral("false", 0)
	}
	var _t862 bool
	if _t861 {
		_t862 = true
	} else {
		_t862 = p.matchLookaheadLiteral("missing", 0)
	}
	var _t863 bool
	if _t862 {
		_t863 = true
	} else {
		_t863 = p.matchLookaheadLiteral("true", 0)
	}
	var _t864 bool
	if _t863 {
		_t864 = true
	} else {
		_t864 = p.matchLookaheadTerminal("DECIMAL", 0)
	}
	var _t865 bool
	if _t864 {
		_t865 = true
	} else {
		_t865 = p.matchLookaheadTerminal("FLOAT", 0)
	}
	var _t866 bool
	if _t865 {
		_t866 = true
	} else {
		_t866 = p.matchLookaheadTerminal("INT", 0)
	}
	var _t867 bool
	if _t866 {
		_t867 = true
	} else {
		_t867 = p.matchLookaheadTerminal("INT128", 0)
	}
	var _t868 bool
	if _t867 {
		_t868 = true
	} else {
		_t868 = p.matchLookaheadTerminal("STRING", 0)
	}
	var _t869 bool
	if _t868 {
		_t869 = true
	} else {
		_t869 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond203 := _t869
	for cond203 {
		_t870 := p.parse_value()
		item204 := _t870
		xs202 = listConcat(xs202, []*pb.Value{item204})
		var _t871 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t871 = true
		} else {
			_t871 = p.matchLookaheadLiteral("false", 0)
		}
		var _t872 bool
		if _t871 {
			_t872 = true
		} else {
			_t872 = p.matchLookaheadLiteral("missing", 0)
		}
		var _t873 bool
		if _t872 {
			_t873 = true
		} else {
			_t873 = p.matchLookaheadLiteral("true", 0)
		}
		var _t874 bool
		if _t873 {
			_t874 = true
		} else {
			_t874 = p.matchLookaheadTerminal("DECIMAL", 0)
		}
		var _t875 bool
		if _t874 {
			_t875 = true
		} else {
			_t875 = p.matchLookaheadTerminal("FLOAT", 0)
		}
		var _t876 bool
		if _t875 {
			_t876 = true
		} else {
			_t876 = p.matchLookaheadTerminal("INT", 0)
		}
		var _t877 bool
		if _t876 {
			_t877 = true
		} else {
			_t877 = p.matchLookaheadTerminal("INT128", 0)
		}
		var _t878 bool
		if _t877 {
			_t878 = true
		} else {
			_t878 = p.matchLookaheadTerminal("STRING", 0)
		}
		var _t879 bool
		if _t878 {
			_t879 = true
		} else {
			_t879 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond203 = _t879
	}
	values205 := xs202
	p.consumeLiteral(")")
	_t880 := &pb.Attribute{Name: name201, Args: values205}
	return _t880
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs206 := []*pb.RelationId{}
	var _t881 bool
	if p.matchLookaheadLiteral(":", 0) {
		_t881 = true
	} else {
		_t881 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond207 := _t881
	for cond207 {
		_t882 := p.parse_relation_id()
		item208 := _t882
		xs206 = listConcat(xs206, []*pb.RelationId{item208})
		var _t883 bool
		if p.matchLookaheadLiteral(":", 0) {
			_t883 = true
		} else {
			_t883 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond207 = _t883
	}
	relation_ids209 := xs206
	_t884 := p.parse_script()
	script210 := _t884
	p.consumeLiteral(")")
	_t885 := &pb.Algorithm{Global: relation_ids209, Body: script210}
	return _t885
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs211 := []*pb.Construct{}
	cond212 := p.matchLookaheadLiteral("(", 0)
	for cond212 {
		_t886 := p.parse_construct()
		item213 := _t886
		xs211 = listConcat(xs211, []*pb.Construct{item213})
		cond212 = p.matchLookaheadLiteral("(", 0)
	}
	constructs214 := xs211
	p.consumeLiteral(")")
	_t887 := &pb.Script{Constructs: constructs214}
	return _t887
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t888 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t889 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t889 = 1
		} else {
			var _t890 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t890 = 1
			} else {
				var _t891 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t891 = 1
				} else {
					var _t892 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t892 = 0
					} else {
						var _t893 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t893 = 1
						} else {
							var _t894 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t894 = 1
							} else {
								_t894 = -1
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
	} else {
		_t888 = -1
	}
	prediction215 := _t888
	var _t895 *pb.Construct
	if prediction215 == 1 {
		_t896 := p.parse_instruction()
		instruction217 := _t896
		_t897 := &pb.Construct{}
		_t897.ConstructType = &pb.Construct_Instruction{Instruction: instruction217}
		_t895 = _t897
	} else {
		var _t898 *pb.Construct
		if prediction215 == 0 {
			_t899 := p.parse_loop()
			loop216 := _t899
			_t900 := &pb.Construct{}
			_t900.ConstructType = &pb.Construct_Loop{Loop: loop216}
			_t898 = _t900
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t895 = _t898
	}
	return _t895
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t901 := p.parse_init()
	init218 := _t901
	_t902 := p.parse_script()
	script219 := _t902
	p.consumeLiteral(")")
	_t903 := &pb.Loop{Init: init218, Body: script219}
	return _t903
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs220 := []*pb.Instruction{}
	cond221 := p.matchLookaheadLiteral("(", 0)
	for cond221 {
		_t904 := p.parse_instruction()
		item222 := _t904
		xs220 = listConcat(xs220, []*pb.Instruction{item222})
		cond221 = p.matchLookaheadLiteral("(", 0)
	}
	instructions223 := xs220
	p.consumeLiteral(")")
	return instructions223
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t905 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t906 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t906 = 1
		} else {
			var _t907 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t907 = 4
			} else {
				var _t908 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t908 = 3
				} else {
					var _t909 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t909 = 2
					} else {
						var _t910 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t910 = 0
						} else {
							_t910 = -1
						}
						_t909 = _t910
					}
					_t908 = _t909
				}
				_t907 = _t908
			}
			_t906 = _t907
		}
		_t905 = _t906
	} else {
		_t905 = -1
	}
	prediction224 := _t905
	var _t911 *pb.Instruction
	if prediction224 == 4 {
		_t912 := p.parse_monus_def()
		monus_def229 := _t912
		_t913 := &pb.Instruction{}
		_t913.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def229}
		_t911 = _t913
	} else {
		var _t914 *pb.Instruction
		if prediction224 == 3 {
			_t915 := p.parse_monoid_def()
			monoid_def228 := _t915
			_t916 := &pb.Instruction{}
			_t916.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def228}
			_t914 = _t916
		} else {
			var _t917 *pb.Instruction
			if prediction224 == 2 {
				_t918 := p.parse_break()
				break227 := _t918
				_t919 := &pb.Instruction{}
				_t919.InstrType = &pb.Instruction_Break{Break: break227}
				_t917 = _t919
			} else {
				var _t920 *pb.Instruction
				if prediction224 == 1 {
					_t921 := p.parse_upsert()
					upsert226 := _t921
					_t922 := &pb.Instruction{}
					_t922.InstrType = &pb.Instruction_Upsert{Upsert: upsert226}
					_t920 = _t922
				} else {
					var _t923 *pb.Instruction
					if prediction224 == 0 {
						_t924 := p.parse_assign()
						assign225 := _t924
						_t925 := &pb.Instruction{}
						_t925.InstrType = &pb.Instruction_Assign{Assign: assign225}
						_t923 = _t925
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t920 = _t923
				}
				_t917 = _t920
			}
			_t914 = _t917
		}
		_t911 = _t914
	}
	return _t911
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t926 := p.parse_relation_id()
	relation_id230 := _t926
	_t927 := p.parse_abstraction()
	abstraction231 := _t927
	var _t929 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t930 := p.parse_attrs()
		_t929 = Some(_t930)
	} else {
		_t929 = Option[[]*pb.Attribute]{}
	}
	attrs232 := _t929
	p.consumeLiteral(")")
	_t931 := &pb.Assign{Name: relation_id230, Body: abstraction231, Attrs: attrs232.UnwrapOr(nil)}
	return _t931
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t932 := p.parse_relation_id()
	relation_id233 := _t932
	_t933 := p.parse_abstraction_with_arity()
	abstraction_with_arity234 := _t933
	var _t935 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t936 := p.parse_attrs()
		_t935 = Some(_t936)
	} else {
		_t935 = Option[[]*pb.Attribute]{}
	}
	attrs235 := _t935
	p.consumeLiteral(")")
	_t937 := &pb.Upsert{Name: relation_id233, Body: abstraction_with_arity234[0].(*pb.Abstraction), Attrs: attrs235.UnwrapOr(nil), ValueArity: abstraction_with_arity234[1].(int64)}
	return _t937
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t938 := p.parse_bindings()
	bindings236 := _t938
	_t939 := p.parse_formula()
	formula237 := _t939
	p.consumeLiteral(")")
	_t940 := &pb.Abstraction{Vars: listConcat(bindings236[0].([]*pb.Binding), bindings236[1].([]*pb.Binding)), Value: formula237}
	return []interface{}{_t940, int64(len(bindings236[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t941 := p.parse_relation_id()
	relation_id238 := _t941
	_t942 := p.parse_abstraction()
	abstraction239 := _t942
	var _t944 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t945 := p.parse_attrs()
		_t944 = Some(_t945)
	} else {
		_t944 = Option[[]*pb.Attribute]{}
	}
	attrs240 := _t944
	p.consumeLiteral(")")
	_t946 := &pb.Break{Name: relation_id238, Body: abstraction239, Attrs: attrs240.UnwrapOr(nil)}
	return _t946
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t947 := p.parse_monoid()
	monoid241 := _t947
	_t948 := p.parse_relation_id()
	relation_id242 := _t948
	_t949 := p.parse_abstraction_with_arity()
	abstraction_with_arity243 := _t949
	var _t951 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t952 := p.parse_attrs()
		_t951 = Some(_t952)
	} else {
		_t951 = Option[[]*pb.Attribute]{}
	}
	attrs244 := _t951
	p.consumeLiteral(")")
	_t953 := &pb.MonoidDef{Monoid: monoid241, Name: relation_id242, Body: abstraction_with_arity243[0].(*pb.Abstraction), Attrs: attrs244.UnwrapOr(nil), ValueArity: abstraction_with_arity243[1].(int64)}
	return _t953
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t954 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t955 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t955 = 3
		} else {
			var _t956 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t956 = 0
			} else {
				var _t957 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t957 = 1
				} else {
					var _t958 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t958 = 2
					} else {
						_t958 = -1
					}
					_t957 = _t958
				}
				_t956 = _t957
			}
			_t955 = _t956
		}
		_t954 = _t955
	} else {
		_t954 = -1
	}
	prediction245 := _t954
	var _t959 *pb.Monoid
	if prediction245 == 3 {
		_t960 := p.parse_sum_monoid()
		sum_monoid249 := _t960
		_t961 := &pb.Monoid{}
		_t961.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid249}
		_t959 = _t961
	} else {
		var _t962 *pb.Monoid
		if prediction245 == 2 {
			_t963 := p.parse_max_monoid()
			max_monoid248 := _t963
			_t964 := &pb.Monoid{}
			_t964.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid248}
			_t962 = _t964
		} else {
			var _t965 *pb.Monoid
			if prediction245 == 1 {
				_t966 := p.parse_min_monoid()
				min_monoid247 := _t966
				_t967 := &pb.Monoid{}
				_t967.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid247}
				_t965 = _t967
			} else {
				var _t968 *pb.Monoid
				if prediction245 == 0 {
					_t969 := p.parse_or_monoid()
					or_monoid246 := _t969
					_t970 := &pb.Monoid{}
					_t970.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid246}
					_t968 = _t970
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t965 = _t968
			}
			_t962 = _t965
		}
		_t959 = _t962
	}
	return _t959
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t971 := &pb.OrMonoid{}
	return _t971
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t972 := p.parse_type()
	type250 := _t972
	p.consumeLiteral(")")
	_t973 := &pb.MinMonoid{Type: type250}
	return _t973
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t974 := p.parse_type()
	type251 := _t974
	p.consumeLiteral(")")
	_t975 := &pb.MaxMonoid{Type: type251}
	return _t975
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t976 := p.parse_type()
	type252 := _t976
	p.consumeLiteral(")")
	_t977 := &pb.SumMonoid{Type: type252}
	return _t977
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t978 := p.parse_monoid()
	monoid253 := _t978
	_t979 := p.parse_relation_id()
	relation_id254 := _t979
	_t980 := p.parse_abstraction_with_arity()
	abstraction_with_arity255 := _t980
	var _t982 Option[[]*pb.Attribute]
	if p.matchLookaheadLiteral("(", 0) {
		_t983 := p.parse_attrs()
		_t982 = Some(_t983)
	} else {
		_t982 = Option[[]*pb.Attribute]{}
	}
	attrs256 := _t982
	p.consumeLiteral(")")
	_t984 := &pb.MonusDef{Monoid: monoid253, Name: relation_id254, Body: abstraction_with_arity255[0].(*pb.Abstraction), Attrs: attrs256.UnwrapOr(nil), ValueArity: abstraction_with_arity255[1].(int64)}
	return _t984
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t985 := p.parse_relation_id()
	relation_id257 := _t985
	_t986 := p.parse_abstraction()
	abstraction258 := _t986
	_t987 := p.parse_functional_dependency_keys()
	functional_dependency_keys259 := _t987
	_t988 := p.parse_functional_dependency_values()
	functional_dependency_values260 := _t988
	p.consumeLiteral(")")
	_t989 := &pb.FunctionalDependency{Guard: abstraction258, Keys: functional_dependency_keys259, Values: functional_dependency_values260}
	_t990 := &pb.Constraint{Name: relation_id257}
	_t990.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t989}
	return _t990
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs261 := []*pb.Var{}
	cond262 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond262 {
		_t991 := p.parse_var()
		item263 := _t991
		xs261 = listConcat(xs261, []*pb.Var{item263})
		cond262 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars264 := xs261
	p.consumeLiteral(")")
	return vars264
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs265 := []*pb.Var{}
	cond266 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond266 {
		_t992 := p.parse_var()
		item267 := _t992
		xs265 = listConcat(xs265, []*pb.Var{item267})
		cond266 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars268 := xs265
	p.consumeLiteral(")")
	return vars268
}

func (p *Parser) parse_data() *pb.Data {
	var _t993 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t994 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t994 = 0
		} else {
			var _t995 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t995 = 2
			} else {
				var _t996 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t996 = 1
				} else {
					_t996 = -1
				}
				_t995 = _t996
			}
			_t994 = _t995
		}
		_t993 = _t994
	} else {
		_t993 = -1
	}
	prediction269 := _t993
	var _t997 *pb.Data
	if prediction269 == 2 {
		_t998 := p.parse_csv_data()
		csv_data272 := _t998
		_t999 := &pb.Data{}
		_t999.DataType = &pb.Data_CsvData{CsvData: csv_data272}
		_t997 = _t999
	} else {
		var _t1000 *pb.Data
		if prediction269 == 1 {
			_t1001 := p.parse_betree_relation()
			betree_relation271 := _t1001
			_t1002 := &pb.Data{}
			_t1002.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation271}
			_t1000 = _t1002
		} else {
			var _t1003 *pb.Data
			if prediction269 == 0 {
				_t1004 := p.parse_rel_edb()
				rel_edb270 := _t1004
				_t1005 := &pb.Data{}
				_t1005.DataType = &pb.Data_RelEdb{RelEdb: rel_edb270}
				_t1003 = _t1005
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1000 = _t1003
		}
		_t997 = _t1000
	}
	return _t997
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1006 := p.parse_relation_id()
	relation_id273 := _t1006
	_t1007 := p.parse_rel_edb_path()
	rel_edb_path274 := _t1007
	_t1008 := p.parse_rel_edb_types()
	rel_edb_types275 := _t1008
	p.consumeLiteral(")")
	_t1009 := &pb.RelEDB{TargetId: relation_id273, Path: rel_edb_path274, Types: rel_edb_types275}
	return _t1009
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs276 := []string{}
	cond277 := p.matchLookaheadTerminal("STRING", 0)
	for cond277 {
		item278 := p.consumeTerminal("STRING").Value.(string)
		xs276 = listConcat(xs276, []string{item278})
		cond277 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings279 := xs276
	p.consumeLiteral("]")
	return strings279
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs280 := []*pb.Type{}
	var _t1010 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t1010 = true
	} else {
		_t1010 = p.matchLookaheadLiteral("BOOLEAN", 0)
	}
	var _t1011 bool
	if _t1010 {
		_t1011 = true
	} else {
		_t1011 = p.matchLookaheadLiteral("DATE", 0)
	}
	var _t1012 bool
	if _t1011 {
		_t1012 = true
	} else {
		_t1012 = p.matchLookaheadLiteral("DATETIME", 0)
	}
	var _t1013 bool
	if _t1012 {
		_t1013 = true
	} else {
		_t1013 = p.matchLookaheadLiteral("FLOAT", 0)
	}
	var _t1014 bool
	if _t1013 {
		_t1014 = true
	} else {
		_t1014 = p.matchLookaheadLiteral("INT", 0)
	}
	var _t1015 bool
	if _t1014 {
		_t1015 = true
	} else {
		_t1015 = p.matchLookaheadLiteral("INT128", 0)
	}
	var _t1016 bool
	if _t1015 {
		_t1016 = true
	} else {
		_t1016 = p.matchLookaheadLiteral("MISSING", 0)
	}
	var _t1017 bool
	if _t1016 {
		_t1017 = true
	} else {
		_t1017 = p.matchLookaheadLiteral("STRING", 0)
	}
	var _t1018 bool
	if _t1017 {
		_t1018 = true
	} else {
		_t1018 = p.matchLookaheadLiteral("UINT128", 0)
	}
	var _t1019 bool
	if _t1018 {
		_t1019 = true
	} else {
		_t1019 = p.matchLookaheadLiteral("UNKNOWN", 0)
	}
	cond281 := _t1019
	for cond281 {
		_t1020 := p.parse_type()
		item282 := _t1020
		xs280 = listConcat(xs280, []*pb.Type{item282})
		var _t1021 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t1021 = true
		} else {
			_t1021 = p.matchLookaheadLiteral("BOOLEAN", 0)
		}
		var _t1022 bool
		if _t1021 {
			_t1022 = true
		} else {
			_t1022 = p.matchLookaheadLiteral("DATE", 0)
		}
		var _t1023 bool
		if _t1022 {
			_t1023 = true
		} else {
			_t1023 = p.matchLookaheadLiteral("DATETIME", 0)
		}
		var _t1024 bool
		if _t1023 {
			_t1024 = true
		} else {
			_t1024 = p.matchLookaheadLiteral("FLOAT", 0)
		}
		var _t1025 bool
		if _t1024 {
			_t1025 = true
		} else {
			_t1025 = p.matchLookaheadLiteral("INT", 0)
		}
		var _t1026 bool
		if _t1025 {
			_t1026 = true
		} else {
			_t1026 = p.matchLookaheadLiteral("INT128", 0)
		}
		var _t1027 bool
		if _t1026 {
			_t1027 = true
		} else {
			_t1027 = p.matchLookaheadLiteral("MISSING", 0)
		}
		var _t1028 bool
		if _t1027 {
			_t1028 = true
		} else {
			_t1028 = p.matchLookaheadLiteral("STRING", 0)
		}
		var _t1029 bool
		if _t1028 {
			_t1029 = true
		} else {
			_t1029 = p.matchLookaheadLiteral("UINT128", 0)
		}
		var _t1030 bool
		if _t1029 {
			_t1030 = true
		} else {
			_t1030 = p.matchLookaheadLiteral("UNKNOWN", 0)
		}
		cond281 = _t1030
	}
	types283 := xs280
	p.consumeLiteral("]")
	return types283
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1031 := p.parse_relation_id()
	relation_id284 := _t1031
	_t1032 := p.parse_betree_info()
	betree_info285 := _t1032
	p.consumeLiteral(")")
	_t1033 := &pb.BeTreeRelation{Name: relation_id284, RelationInfo: betree_info285}
	return _t1033
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1034 := p.parse_betree_info_key_types()
	betree_info_key_types286 := _t1034
	_t1035 := p.parse_betree_info_value_types()
	betree_info_value_types287 := _t1035
	_t1036 := p.parse_config_dict()
	config_dict288 := _t1036
	p.consumeLiteral(")")
	_t1037 := p.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
	return _t1037
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs289 := []*pb.Type{}
	var _t1038 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t1038 = true
	} else {
		_t1038 = p.matchLookaheadLiteral("BOOLEAN", 0)
	}
	var _t1039 bool
	if _t1038 {
		_t1039 = true
	} else {
		_t1039 = p.matchLookaheadLiteral("DATE", 0)
	}
	var _t1040 bool
	if _t1039 {
		_t1040 = true
	} else {
		_t1040 = p.matchLookaheadLiteral("DATETIME", 0)
	}
	var _t1041 bool
	if _t1040 {
		_t1041 = true
	} else {
		_t1041 = p.matchLookaheadLiteral("FLOAT", 0)
	}
	var _t1042 bool
	if _t1041 {
		_t1042 = true
	} else {
		_t1042 = p.matchLookaheadLiteral("INT", 0)
	}
	var _t1043 bool
	if _t1042 {
		_t1043 = true
	} else {
		_t1043 = p.matchLookaheadLiteral("INT128", 0)
	}
	var _t1044 bool
	if _t1043 {
		_t1044 = true
	} else {
		_t1044 = p.matchLookaheadLiteral("MISSING", 0)
	}
	var _t1045 bool
	if _t1044 {
		_t1045 = true
	} else {
		_t1045 = p.matchLookaheadLiteral("STRING", 0)
	}
	var _t1046 bool
	if _t1045 {
		_t1046 = true
	} else {
		_t1046 = p.matchLookaheadLiteral("UINT128", 0)
	}
	var _t1047 bool
	if _t1046 {
		_t1047 = true
	} else {
		_t1047 = p.matchLookaheadLiteral("UNKNOWN", 0)
	}
	cond290 := _t1047
	for cond290 {
		_t1048 := p.parse_type()
		item291 := _t1048
		xs289 = listConcat(xs289, []*pb.Type{item291})
		var _t1049 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t1049 = true
		} else {
			_t1049 = p.matchLookaheadLiteral("BOOLEAN", 0)
		}
		var _t1050 bool
		if _t1049 {
			_t1050 = true
		} else {
			_t1050 = p.matchLookaheadLiteral("DATE", 0)
		}
		var _t1051 bool
		if _t1050 {
			_t1051 = true
		} else {
			_t1051 = p.matchLookaheadLiteral("DATETIME", 0)
		}
		var _t1052 bool
		if _t1051 {
			_t1052 = true
		} else {
			_t1052 = p.matchLookaheadLiteral("FLOAT", 0)
		}
		var _t1053 bool
		if _t1052 {
			_t1053 = true
		} else {
			_t1053 = p.matchLookaheadLiteral("INT", 0)
		}
		var _t1054 bool
		if _t1053 {
			_t1054 = true
		} else {
			_t1054 = p.matchLookaheadLiteral("INT128", 0)
		}
		var _t1055 bool
		if _t1054 {
			_t1055 = true
		} else {
			_t1055 = p.matchLookaheadLiteral("MISSING", 0)
		}
		var _t1056 bool
		if _t1055 {
			_t1056 = true
		} else {
			_t1056 = p.matchLookaheadLiteral("STRING", 0)
		}
		var _t1057 bool
		if _t1056 {
			_t1057 = true
		} else {
			_t1057 = p.matchLookaheadLiteral("UINT128", 0)
		}
		var _t1058 bool
		if _t1057 {
			_t1058 = true
		} else {
			_t1058 = p.matchLookaheadLiteral("UNKNOWN", 0)
		}
		cond290 = _t1058
	}
	types292 := xs289
	p.consumeLiteral(")")
	return types292
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs293 := []*pb.Type{}
	var _t1059 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t1059 = true
	} else {
		_t1059 = p.matchLookaheadLiteral("BOOLEAN", 0)
	}
	var _t1060 bool
	if _t1059 {
		_t1060 = true
	} else {
		_t1060 = p.matchLookaheadLiteral("DATE", 0)
	}
	var _t1061 bool
	if _t1060 {
		_t1061 = true
	} else {
		_t1061 = p.matchLookaheadLiteral("DATETIME", 0)
	}
	var _t1062 bool
	if _t1061 {
		_t1062 = true
	} else {
		_t1062 = p.matchLookaheadLiteral("FLOAT", 0)
	}
	var _t1063 bool
	if _t1062 {
		_t1063 = true
	} else {
		_t1063 = p.matchLookaheadLiteral("INT", 0)
	}
	var _t1064 bool
	if _t1063 {
		_t1064 = true
	} else {
		_t1064 = p.matchLookaheadLiteral("INT128", 0)
	}
	var _t1065 bool
	if _t1064 {
		_t1065 = true
	} else {
		_t1065 = p.matchLookaheadLiteral("MISSING", 0)
	}
	var _t1066 bool
	if _t1065 {
		_t1066 = true
	} else {
		_t1066 = p.matchLookaheadLiteral("STRING", 0)
	}
	var _t1067 bool
	if _t1066 {
		_t1067 = true
	} else {
		_t1067 = p.matchLookaheadLiteral("UINT128", 0)
	}
	var _t1068 bool
	if _t1067 {
		_t1068 = true
	} else {
		_t1068 = p.matchLookaheadLiteral("UNKNOWN", 0)
	}
	cond294 := _t1068
	for cond294 {
		_t1069 := p.parse_type()
		item295 := _t1069
		xs293 = listConcat(xs293, []*pb.Type{item295})
		var _t1070 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t1070 = true
		} else {
			_t1070 = p.matchLookaheadLiteral("BOOLEAN", 0)
		}
		var _t1071 bool
		if _t1070 {
			_t1071 = true
		} else {
			_t1071 = p.matchLookaheadLiteral("DATE", 0)
		}
		var _t1072 bool
		if _t1071 {
			_t1072 = true
		} else {
			_t1072 = p.matchLookaheadLiteral("DATETIME", 0)
		}
		var _t1073 bool
		if _t1072 {
			_t1073 = true
		} else {
			_t1073 = p.matchLookaheadLiteral("FLOAT", 0)
		}
		var _t1074 bool
		if _t1073 {
			_t1074 = true
		} else {
			_t1074 = p.matchLookaheadLiteral("INT", 0)
		}
		var _t1075 bool
		if _t1074 {
			_t1075 = true
		} else {
			_t1075 = p.matchLookaheadLiteral("INT128", 0)
		}
		var _t1076 bool
		if _t1075 {
			_t1076 = true
		} else {
			_t1076 = p.matchLookaheadLiteral("MISSING", 0)
		}
		var _t1077 bool
		if _t1076 {
			_t1077 = true
		} else {
			_t1077 = p.matchLookaheadLiteral("STRING", 0)
		}
		var _t1078 bool
		if _t1077 {
			_t1078 = true
		} else {
			_t1078 = p.matchLookaheadLiteral("UINT128", 0)
		}
		var _t1079 bool
		if _t1078 {
			_t1079 = true
		} else {
			_t1079 = p.matchLookaheadLiteral("UNKNOWN", 0)
		}
		cond294 = _t1079
	}
	types296 := xs293
	p.consumeLiteral(")")
	return types296
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1080 := p.parse_csvlocator()
	csvlocator297 := _t1080
	_t1081 := p.parse_csv_config()
	csv_config298 := _t1081
	_t1082 := p.parse_csv_columns()
	csv_columns299 := _t1082
	_t1083 := p.parse_csv_asof()
	csv_asof300 := _t1083
	p.consumeLiteral(")")
	_t1084 := &pb.CSVData{Locator: csvlocator297, Config: csv_config298, Columns: csv_columns299, Asof: csv_asof300}
	return _t1084
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1085 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t1085 = p.matchLookaheadLiteral("paths", 1)
	} else {
		_t1085 = false
	}
	var _t1087 Option[[]string]
	if _t1085 {
		_t1088 := p.parse_csv_locator_paths()
		_t1087 = Some(_t1088)
	} else {
		_t1087 = Option[[]string]{}
	}
	csv_locator_paths301 := _t1087
	var _t1090 Option[string]
	if p.matchLookaheadLiteral("(", 0) {
		_t1091 := p.parse_csv_locator_inline_data()
		_t1090 = Some(_t1091)
	} else {
		_t1090 = Option[string]{}
	}
	csv_locator_inline_data302 := _t1090
	p.consumeLiteral(")")
	_t1092 := &pb.CSVLocator{Paths: csv_locator_paths301.UnwrapOr(nil), InlineData: []byte(csv_locator_inline_data302.UnwrapOr(""))}
	return _t1092
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs303 := []string{}
	cond304 := p.matchLookaheadTerminal("STRING", 0)
	for cond304 {
		item305 := p.consumeTerminal("STRING").Value.(string)
		xs303 = listConcat(xs303, []string{item305})
		cond304 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings306 := xs303
	p.consumeLiteral(")")
	return strings306
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string307 := p.consumeTerminal("STRING").Value.(string)
	p.consumeLiteral(")")
	return string307
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1093 := p.parse_config_dict()
	config_dict308 := _t1093
	p.consumeLiteral(")")
	_t1094 := p.construct_csv_config(config_dict308)
	return _t1094
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs309 := []*pb.CSVColumn{}
	cond310 := p.matchLookaheadLiteral("(", 0)
	for cond310 {
		_t1095 := p.parse_csv_column()
		item311 := _t1095
		xs309 = listConcat(xs309, []*pb.CSVColumn{item311})
		cond310 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns312 := xs309
	p.consumeLiteral(")")
	return csv_columns312
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string313 := p.consumeTerminal("STRING").Value.(string)
	_t1096 := p.parse_relation_id()
	relation_id314 := _t1096
	p.consumeLiteral("[")
	xs315 := []*pb.Type{}
	var _t1097 bool
	if p.matchLookaheadLiteral("(", 0) {
		_t1097 = true
	} else {
		_t1097 = p.matchLookaheadLiteral("BOOLEAN", 0)
	}
	var _t1098 bool
	if _t1097 {
		_t1098 = true
	} else {
		_t1098 = p.matchLookaheadLiteral("DATE", 0)
	}
	var _t1099 bool
	if _t1098 {
		_t1099 = true
	} else {
		_t1099 = p.matchLookaheadLiteral("DATETIME", 0)
	}
	var _t1100 bool
	if _t1099 {
		_t1100 = true
	} else {
		_t1100 = p.matchLookaheadLiteral("FLOAT", 0)
	}
	var _t1101 bool
	if _t1100 {
		_t1101 = true
	} else {
		_t1101 = p.matchLookaheadLiteral("INT", 0)
	}
	var _t1102 bool
	if _t1101 {
		_t1102 = true
	} else {
		_t1102 = p.matchLookaheadLiteral("INT128", 0)
	}
	var _t1103 bool
	if _t1102 {
		_t1103 = true
	} else {
		_t1103 = p.matchLookaheadLiteral("MISSING", 0)
	}
	var _t1104 bool
	if _t1103 {
		_t1104 = true
	} else {
		_t1104 = p.matchLookaheadLiteral("STRING", 0)
	}
	var _t1105 bool
	if _t1104 {
		_t1105 = true
	} else {
		_t1105 = p.matchLookaheadLiteral("UINT128", 0)
	}
	var _t1106 bool
	if _t1105 {
		_t1106 = true
	} else {
		_t1106 = p.matchLookaheadLiteral("UNKNOWN", 0)
	}
	cond316 := _t1106
	for cond316 {
		_t1107 := p.parse_type()
		item317 := _t1107
		xs315 = listConcat(xs315, []*pb.Type{item317})
		var _t1108 bool
		if p.matchLookaheadLiteral("(", 0) {
			_t1108 = true
		} else {
			_t1108 = p.matchLookaheadLiteral("BOOLEAN", 0)
		}
		var _t1109 bool
		if _t1108 {
			_t1109 = true
		} else {
			_t1109 = p.matchLookaheadLiteral("DATE", 0)
		}
		var _t1110 bool
		if _t1109 {
			_t1110 = true
		} else {
			_t1110 = p.matchLookaheadLiteral("DATETIME", 0)
		}
		var _t1111 bool
		if _t1110 {
			_t1111 = true
		} else {
			_t1111 = p.matchLookaheadLiteral("FLOAT", 0)
		}
		var _t1112 bool
		if _t1111 {
			_t1112 = true
		} else {
			_t1112 = p.matchLookaheadLiteral("INT", 0)
		}
		var _t1113 bool
		if _t1112 {
			_t1113 = true
		} else {
			_t1113 = p.matchLookaheadLiteral("INT128", 0)
		}
		var _t1114 bool
		if _t1113 {
			_t1114 = true
		} else {
			_t1114 = p.matchLookaheadLiteral("MISSING", 0)
		}
		var _t1115 bool
		if _t1114 {
			_t1115 = true
		} else {
			_t1115 = p.matchLookaheadLiteral("STRING", 0)
		}
		var _t1116 bool
		if _t1115 {
			_t1116 = true
		} else {
			_t1116 = p.matchLookaheadLiteral("UINT128", 0)
		}
		var _t1117 bool
		if _t1116 {
			_t1117 = true
		} else {
			_t1117 = p.matchLookaheadLiteral("UNKNOWN", 0)
		}
		cond316 = _t1117
	}
	types318 := xs315
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1118 := &pb.CSVColumn{ColumnName: string313, TargetId: relation_id314, Types: types318}
	return _t1118
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string319 := p.consumeTerminal("STRING").Value.(string)
	p.consumeLiteral(")")
	return string319
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1119 := p.parse_fragment_id()
	fragment_id320 := _t1119
	p.consumeLiteral(")")
	_t1120 := &pb.Undefine{FragmentId: fragment_id320}
	return _t1120
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs321 := []*pb.RelationId{}
	var _t1121 bool
	if p.matchLookaheadLiteral(":", 0) {
		_t1121 = true
	} else {
		_t1121 = p.matchLookaheadTerminal("UINT128", 0)
	}
	cond322 := _t1121
	for cond322 {
		_t1122 := p.parse_relation_id()
		item323 := _t1122
		xs321 = listConcat(xs321, []*pb.RelationId{item323})
		var _t1123 bool
		if p.matchLookaheadLiteral(":", 0) {
			_t1123 = true
		} else {
			_t1123 = p.matchLookaheadTerminal("UINT128", 0)
		}
		cond322 = _t1123
	}
	relation_ids324 := xs321
	p.consumeLiteral(")")
	_t1124 := &pb.Context{Relations: relation_ids324}
	return _t1124
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs325 := []*pb.Read{}
	cond326 := p.matchLookaheadLiteral("(", 0)
	for cond326 {
		_t1125 := p.parse_read()
		item327 := _t1125
		xs325 = listConcat(xs325, []*pb.Read{item327})
		cond326 = p.matchLookaheadLiteral("(", 0)
	}
	reads328 := xs325
	p.consumeLiteral(")")
	return reads328
}

func (p *Parser) parse_read() *pb.Read {
	var _t1126 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1127 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1127 = 2
		} else {
			var _t1128 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1128 = 1
			} else {
				var _t1129 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1129 = 4
				} else {
					var _t1130 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1130 = 0
					} else {
						var _t1131 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1131 = 3
						} else {
							_t1131 = -1
						}
						_t1130 = _t1131
					}
					_t1129 = _t1130
				}
				_t1128 = _t1129
			}
			_t1127 = _t1128
		}
		_t1126 = _t1127
	} else {
		_t1126 = -1
	}
	prediction329 := _t1126
	var _t1132 *pb.Read
	if prediction329 == 4 {
		_t1133 := p.parse_export()
		export334 := _t1133
		_t1134 := &pb.Read{}
		_t1134.ReadType = &pb.Read_Export{Export: export334}
		_t1132 = _t1134
	} else {
		var _t1135 *pb.Read
		if prediction329 == 3 {
			_t1136 := p.parse_abort()
			abort333 := _t1136
			_t1137 := &pb.Read{}
			_t1137.ReadType = &pb.Read_Abort{Abort: abort333}
			_t1135 = _t1137
		} else {
			var _t1138 *pb.Read
			if prediction329 == 2 {
				_t1139 := p.parse_what_if()
				what_if332 := _t1139
				_t1140 := &pb.Read{}
				_t1140.ReadType = &pb.Read_WhatIf{WhatIf: what_if332}
				_t1138 = _t1140
			} else {
				var _t1141 *pb.Read
				if prediction329 == 1 {
					_t1142 := p.parse_output()
					output331 := _t1142
					_t1143 := &pb.Read{}
					_t1143.ReadType = &pb.Read_Output{Output: output331}
					_t1141 = _t1143
				} else {
					var _t1144 *pb.Read
					if prediction329 == 0 {
						_t1145 := p.parse_demand()
						demand330 := _t1145
						_t1146 := &pb.Read{}
						_t1146.ReadType = &pb.Read_Demand{Demand: demand330}
						_t1144 = _t1146
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1141 = _t1144
				}
				_t1138 = _t1141
			}
			_t1135 = _t1138
		}
		_t1132 = _t1135
	}
	return _t1132
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1147 := p.parse_relation_id()
	relation_id335 := _t1147
	p.consumeLiteral(")")
	_t1148 := &pb.Demand{RelationId: relation_id335}
	return _t1148
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	var _t1149 bool
	if p.matchLookaheadLiteral(":", 0) {
		_t1149 = p.matchLookaheadTerminal("SYMBOL", 1)
	} else {
		_t1149 = false
	}
	var _t1151 Option[string]
	if _t1149 {
		_t1152 := p.parse_name()
		_t1151 = Some(_t1152)
	} else {
		_t1151 = Option[string]{}
	}
	name336 := _t1151
	_t1153 := p.parse_relation_id()
	relation_id337 := _t1153
	p.consumeLiteral(")")
	_t1154 := &pb.Output{Name: name336.UnwrapOr("output"), RelationId: relation_id337}
	return _t1154
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1155 := p.parse_name()
	name338 := _t1155
	_t1156 := p.parse_epoch()
	epoch339 := _t1156
	p.consumeLiteral(")")
	_t1157 := &pb.WhatIf{Branch: name338, Epoch: epoch339}
	return _t1157
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1158 bool
	if p.matchLookaheadLiteral(":", 0) {
		_t1158 = p.matchLookaheadTerminal("SYMBOL", 1)
	} else {
		_t1158 = false
	}
	var _t1160 Option[string]
	if _t1158 {
		_t1161 := p.parse_name()
		_t1160 = Some(_t1161)
	} else {
		_t1160 = Option[string]{}
	}
	name340 := _t1160
	_t1162 := p.parse_relation_id()
	relation_id341 := _t1162
	p.consumeLiteral(")")
	_t1163 := &pb.Abort{Name: name340.UnwrapOr("abort"), RelationId: relation_id341}
	return _t1163
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1164 := p.parse_export_csv_config()
	export_csv_config342 := _t1164
	p.consumeLiteral(")")
	_t1165 := &pb.Export{}
	_t1165.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config342}
	return _t1165
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1166 := p.parse_export_csv_path()
	export_csv_path343 := _t1166
	_t1167 := p.parse_export_csv_columns()
	export_csv_columns344 := _t1167
	_t1168 := p.parse_config_dict()
	config_dict345 := _t1168
	p.consumeLiteral(")")
	_t1169 := p.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)
	return _t1169
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string346 := p.consumeTerminal("STRING").Value.(string)
	p.consumeLiteral(")")
	return string346
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs347 := []*pb.ExportCSVColumn{}
	cond348 := p.matchLookaheadLiteral("(", 0)
	for cond348 {
		_t1170 := p.parse_export_csv_column()
		item349 := _t1170
		xs347 = listConcat(xs347, []*pb.ExportCSVColumn{item349})
		cond348 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns350 := xs347
	p.consumeLiteral(")")
	return export_csv_columns350
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string351 := p.consumeTerminal("STRING").Value.(string)
	_t1171 := p.parse_relation_id()
	relation_id352 := _t1171
	p.consumeLiteral(")")
	_t1172 := &pb.ExportCSVColumn{ColumnName: string351, ColumnData: relation_id352}
	return _t1172
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
