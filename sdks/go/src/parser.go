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

func (p *Parser) default_configure() *pb.Configure {
	_t956 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t956
	_t957 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t957
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	return default_
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	return nil
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t958 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t958
	_t959 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t959
	_t960 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t960
	_t961 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t961
	_t962 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t962
	_t963 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t963
	_t964 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t964
	_t965 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t965
	_t966 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t966
	_t967 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t967.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t967.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t967
	_t968 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t968
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t969 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t969
	_t970 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t970
	_t971 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t971
	_t972 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t972
	_t973 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t973
	_t974 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t974
	_t975 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t975
	_t976 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t976
	_t977 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t977
	_t978 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t978
	_t979 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t979
	_t980 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t980
}

func (p *Parser) _extract_value_int32(value *pb.Value, default_ int64) int32 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	return int32(default_)
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	return default_
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	return default_
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return nil
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
	_t981 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t981
	_t982 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t982
	_t983 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t983
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t984 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t984
	_t985 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t985
	_t986 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t986
	_t987 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t987
	_t988 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t988
	_t989 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t989
	_t990 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t990
	_t991 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t991
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t353 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t354 := p.parse_configure()
		_t353 = _t354
	}
	configure0 := _t353
	var _t355 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t356 := p.parse_sync()
		_t355 = _t356
	}
	sync1 := _t355
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	for cond3 {
		_t357 := p.parse_epoch()
		item4 := _t357
		xs2 = append(xs2, item4)
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	epochs5 := xs2
	p.consumeLiteral(")")
	_t358 := p.default_configure()
	_t359 := configure0
	if configure0 == nil {
		_t359 = _t358
	}
	_t360 := &pb.Transaction{Epochs: epochs5, Configure: _t359, Sync: sync1}
	return _t360
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t361 := p.parse_config_dict()
	config_dict6 := _t361
	p.consumeLiteral(")")
	_t362 := p.construct_configure(config_dict6)
	return _t362
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs7 := [][]interface{}{}
	cond8 := p.matchLookaheadLiteral(":", 0)
	for cond8 {
		_t363 := p.parse_config_key_value()
		item9 := _t363
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
	_t364 := p.parse_value()
	value12 := _t364
	return []interface{}{symbol11, value12}
}

func (p *Parser) parse_value() *pb.Value {
	var _t365 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t365 = 9
	} else {
		var _t366 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t366 = 8
		} else {
			var _t367 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t367 = 9
			} else {
				var _t368 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t369 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t369 = 1
					} else {
						var _t370 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t370 = 0
						} else {
							_t370 = -1
						}
						_t369 = _t370
					}
					_t368 = _t369
				} else {
					var _t371 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t371 = 5
					} else {
						var _t372 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t372 = 2
						} else {
							var _t373 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t373 = 6
							} else {
								var _t374 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t374 = 3
								} else {
									var _t375 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t375 = 4
									} else {
										var _t376 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t376 = 7
										} else {
											_t376 = -1
										}
										_t375 = _t376
									}
									_t374 = _t375
								}
								_t373 = _t374
							}
							_t372 = _t373
						}
						_t371 = _t372
					}
					_t368 = _t371
				}
				_t367 = _t368
			}
			_t366 = _t367
		}
		_t365 = _t366
	}
	prediction13 := _t365
	var _t377 *pb.Value
	if prediction13 == 9 {
		_t378 := p.parse_boolean_value()
		boolean_value22 := _t378
		_t379 := &pb.Value{}
		_t379.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value22}
		_t377 = _t379
	} else {
		var _t380 *pb.Value
		if prediction13 == 8 {
			p.consumeLiteral("missing")
			_t381 := &pb.MissingValue{}
			_t382 := &pb.Value{}
			_t382.Value = &pb.Value_MissingValue{MissingValue: _t381}
			_t380 = _t382
		} else {
			var _t383 *pb.Value
			if prediction13 == 7 {
				decimal21 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t384 := &pb.Value{}
				_t384.Value = &pb.Value_DecimalValue{DecimalValue: decimal21}
				_t383 = _t384
			} else {
				var _t385 *pb.Value
				if prediction13 == 6 {
					int12820 := p.consumeTerminal("INT128").Value.AsInt128()
					_t386 := &pb.Value{}
					_t386.Value = &pb.Value_Int128Value{Int128Value: int12820}
					_t385 = _t386
				} else {
					var _t387 *pb.Value
					if prediction13 == 5 {
						uint12819 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t388 := &pb.Value{}
						_t388.Value = &pb.Value_Uint128Value{Uint128Value: uint12819}
						_t387 = _t388
					} else {
						var _t389 *pb.Value
						if prediction13 == 4 {
							float18 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t390 := &pb.Value{}
							_t390.Value = &pb.Value_FloatValue{FloatValue: float18}
							_t389 = _t390
						} else {
							var _t391 *pb.Value
							if prediction13 == 3 {
								int17 := p.consumeTerminal("INT").Value.AsInt64()
								_t392 := &pb.Value{}
								_t392.Value = &pb.Value_IntValue{IntValue: int17}
								_t391 = _t392
							} else {
								var _t393 *pb.Value
								if prediction13 == 2 {
									string16 := p.consumeTerminal("STRING").Value.AsString()
									_t394 := &pb.Value{}
									_t394.Value = &pb.Value_StringValue{StringValue: string16}
									_t393 = _t394
								} else {
									var _t395 *pb.Value
									if prediction13 == 1 {
										_t396 := p.parse_datetime()
										datetime15 := _t396
										_t397 := &pb.Value{}
										_t397.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime15}
										_t395 = _t397
									} else {
										var _t398 *pb.Value
										if prediction13 == 0 {
											_t399 := p.parse_date()
											date14 := _t399
											_t400 := &pb.Value{}
											_t400.Value = &pb.Value_DateValue{DateValue: date14}
											_t398 = _t400
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t395 = _t398
									}
									_t393 = _t395
								}
								_t391 = _t393
							}
							_t389 = _t391
						}
						_t387 = _t389
					}
					_t385 = _t387
				}
				_t383 = _t385
			}
			_t380 = _t383
		}
		_t377 = _t380
	}
	return _t377
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int23 := p.consumeTerminal("INT").Value.AsInt64()
	int_324 := p.consumeTerminal("INT").Value.AsInt64()
	int_425 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t401 := &pb.DateValue{Year: int32(int23), Month: int32(int_324), Day: int32(int_425)}
	return _t401
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
	var _t402 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t402 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_832 := _t402
	p.consumeLiteral(")")
	_t403 := &pb.DateTimeValue{Year: int32(int26), Month: int32(int_327), Day: int32(int_428), Hour: int32(int_529), Minute: int32(int_630), Second: int32(int_731), Microsecond: int32(deref(int_832, 0))}
	return _t403
}

func (p *Parser) parse_boolean_value() bool {
	var _t404 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t404 = 0
	} else {
		var _t405 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t405 = 1
		} else {
			_t405 = -1
		}
		_t404 = _t405
	}
	prediction33 := _t404
	var _t406 bool
	if prediction33 == 1 {
		p.consumeLiteral("false")
		_t406 = false
	} else {
		var _t407 bool
		if prediction33 == 0 {
			p.consumeLiteral("true")
			_t407 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t406 = _t407
	}
	return _t406
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs34 := []*pb.FragmentId{}
	cond35 := p.matchLookaheadLiteral(":", 0)
	for cond35 {
		_t408 := p.parse_fragment_id()
		item36 := _t408
		xs34 = append(xs34, item36)
		cond35 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids37 := xs34
	p.consumeLiteral(")")
	_t409 := &pb.Sync{Fragments: fragment_ids37}
	return _t409
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol38 := p.consumeTerminal("SYMBOL").Value.AsString()
	return &pb.FragmentId{Id: []byte(symbol38)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t410 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t411 := p.parse_epoch_writes()
		_t410 = _t411
	}
	epoch_writes39 := _t410
	var _t412 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t413 := p.parse_epoch_reads()
		_t412 = _t413
	}
	epoch_reads40 := _t412
	p.consumeLiteral(")")
	_t414 := epoch_writes39
	if epoch_writes39 == nil {
		_t414 = []*pb.Write{}
	}
	_t415 := epoch_reads40
	if epoch_reads40 == nil {
		_t415 = []*pb.Read{}
	}
	_t416 := &pb.Epoch{Writes: _t414, Reads: _t415}
	return _t416
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs41 := []*pb.Write{}
	cond42 := p.matchLookaheadLiteral("(", 0)
	for cond42 {
		_t417 := p.parse_write()
		item43 := _t417
		xs41 = append(xs41, item43)
		cond42 = p.matchLookaheadLiteral("(", 0)
	}
	writes44 := xs41
	p.consumeLiteral(")")
	return writes44
}

func (p *Parser) parse_write() *pb.Write {
	var _t418 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t419 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t419 = 1
		} else {
			var _t420 int64
			if p.matchLookaheadLiteral("define", 1) {
				_t420 = 0
			} else {
				var _t421 int64
				if p.matchLookaheadLiteral("context", 1) {
					_t421 = 2
				} else {
					_t421 = -1
				}
				_t420 = _t421
			}
			_t419 = _t420
		}
		_t418 = _t419
	} else {
		_t418 = -1
	}
	prediction45 := _t418
	var _t422 *pb.Write
	if prediction45 == 2 {
		_t423 := p.parse_context()
		context48 := _t423
		_t424 := &pb.Write{}
		_t424.WriteType = &pb.Write_Context{Context: context48}
		_t422 = _t424
	} else {
		var _t425 *pb.Write
		if prediction45 == 1 {
			_t426 := p.parse_undefine()
			undefine47 := _t426
			_t427 := &pb.Write{}
			_t427.WriteType = &pb.Write_Undefine{Undefine: undefine47}
			_t425 = _t427
		} else {
			var _t428 *pb.Write
			if prediction45 == 0 {
				_t429 := p.parse_define()
				define46 := _t429
				_t430 := &pb.Write{}
				_t430.WriteType = &pb.Write_Define{Define: define46}
				_t428 = _t430
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t425 = _t428
		}
		_t422 = _t425
	}
	return _t422
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t431 := p.parse_fragment()
	fragment49 := _t431
	p.consumeLiteral(")")
	_t432 := &pb.Define{Fragment: fragment49}
	return _t432
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t433 := p.parse_new_fragment_id()
	new_fragment_id50 := _t433
	xs51 := []*pb.Declaration{}
	cond52 := p.matchLookaheadLiteral("(", 0)
	for cond52 {
		_t434 := p.parse_declaration()
		item53 := _t434
		xs51 = append(xs51, item53)
		cond52 = p.matchLookaheadLiteral("(", 0)
	}
	declarations54 := xs51
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id50, declarations54)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t435 := p.parse_fragment_id()
	fragment_id55 := _t435
	p.startFragment(fragment_id55)
	return fragment_id55
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t436 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t437 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t437 = 3
		} else {
			var _t438 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t438 = 2
			} else {
				var _t439 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t439 = 0
				} else {
					var _t440 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t440 = 3
					} else {
						var _t441 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t441 = 3
						} else {
							var _t442 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t442 = 1
							} else {
								_t442 = -1
							}
							_t441 = _t442
						}
						_t440 = _t441
					}
					_t439 = _t440
				}
				_t438 = _t439
			}
			_t437 = _t438
		}
		_t436 = _t437
	} else {
		_t436 = -1
	}
	prediction56 := _t436
	var _t443 *pb.Declaration
	if prediction56 == 3 {
		_t444 := p.parse_data()
		data60 := _t444
		_t445 := &pb.Declaration{}
		_t445.DeclarationType = &pb.Declaration_Data{Data: data60}
		_t443 = _t445
	} else {
		var _t446 *pb.Declaration
		if prediction56 == 2 {
			_t447 := p.parse_constraint()
			constraint59 := _t447
			_t448 := &pb.Declaration{}
			_t448.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint59}
			_t446 = _t448
		} else {
			var _t449 *pb.Declaration
			if prediction56 == 1 {
				_t450 := p.parse_algorithm()
				algorithm58 := _t450
				_t451 := &pb.Declaration{}
				_t451.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm58}
				_t449 = _t451
			} else {
				var _t452 *pb.Declaration
				if prediction56 == 0 {
					_t453 := p.parse_def()
					def57 := _t453
					_t454 := &pb.Declaration{}
					_t454.DeclarationType = &pb.Declaration_Def{Def: def57}
					_t452 = _t454
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t449 = _t452
			}
			_t446 = _t449
		}
		_t443 = _t446
	}
	return _t443
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t455 := p.parse_relation_id()
	relation_id61 := _t455
	_t456 := p.parse_abstraction()
	abstraction62 := _t456
	var _t457 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t458 := p.parse_attrs()
		_t457 = _t458
	}
	attrs63 := _t457
	p.consumeLiteral(")")
	_t459 := attrs63
	if attrs63 == nil {
		_t459 = []*pb.Attribute{}
	}
	_t460 := &pb.Def{Name: relation_id61, Body: abstraction62, Attrs: _t459}
	return _t460
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t461 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t461 = 0
	} else {
		var _t462 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t462 = 1
		} else {
			_t462 = -1
		}
		_t461 = _t462
	}
	prediction64 := _t461
	var _t463 *pb.RelationId
	if prediction64 == 1 {
		uint12866 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t463 = &pb.RelationId{IdLow: uint12866.Low, IdHigh: uint12866.High}
	} else {
		var _t464 *pb.RelationId
		if prediction64 == 0 {
			p.consumeLiteral(":")
			symbol65 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t464 = p.relationIdFromString(symbol65)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t463 = _t464
	}
	return _t463
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t465 := p.parse_bindings()
	bindings67 := _t465
	_t466 := p.parse_formula()
	formula68 := _t466
	p.consumeLiteral(")")
	_t467 := &pb.Abstraction{Vars: listConcat(bindings67[0].([]*pb.Binding), bindings67[1].([]*pb.Binding)), Value: formula68}
	return _t467
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs69 := []*pb.Binding{}
	cond70 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond70 {
		_t468 := p.parse_binding()
		item71 := _t468
		xs69 = append(xs69, item71)
		cond70 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings72 := xs69
	var _t469 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t470 := p.parse_value_bindings()
		_t469 = _t470
	}
	value_bindings73 := _t469
	p.consumeLiteral("]")
	_t471 := value_bindings73
	if value_bindings73 == nil {
		_t471 = []*pb.Binding{}
	}
	return []interface{}{bindings72, _t471}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol74 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	_t472 := p.parse_type()
	type75 := _t472
	_t473 := &pb.Var{Name: symbol74}
	_t474 := &pb.Binding{Var: _t473, Type: type75}
	return _t474
}

func (p *Parser) parse_type() *pb.Type {
	var _t475 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t475 = 0
	} else {
		var _t476 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t476 = 4
		} else {
			var _t477 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t477 = 1
			} else {
				var _t478 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t478 = 8
				} else {
					var _t479 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t479 = 5
					} else {
						var _t480 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t480 = 2
						} else {
							var _t481 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t481 = 3
							} else {
								var _t482 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t482 = 7
								} else {
									var _t483 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t483 = 6
									} else {
										var _t484 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t484 = 10
										} else {
											var _t485 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t485 = 9
											} else {
												_t485 = -1
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
					_t478 = _t479
				}
				_t477 = _t478
			}
			_t476 = _t477
		}
		_t475 = _t476
	}
	prediction76 := _t475
	var _t486 *pb.Type
	if prediction76 == 10 {
		_t487 := p.parse_boolean_type()
		boolean_type87 := _t487
		_t488 := &pb.Type{}
		_t488.Type = &pb.Type_BooleanType{BooleanType: boolean_type87}
		_t486 = _t488
	} else {
		var _t489 *pb.Type
		if prediction76 == 9 {
			_t490 := p.parse_decimal_type()
			decimal_type86 := _t490
			_t491 := &pb.Type{}
			_t491.Type = &pb.Type_DecimalType{DecimalType: decimal_type86}
			_t489 = _t491
		} else {
			var _t492 *pb.Type
			if prediction76 == 8 {
				_t493 := p.parse_missing_type()
				missing_type85 := _t493
				_t494 := &pb.Type{}
				_t494.Type = &pb.Type_MissingType{MissingType: missing_type85}
				_t492 = _t494
			} else {
				var _t495 *pb.Type
				if prediction76 == 7 {
					_t496 := p.parse_datetime_type()
					datetime_type84 := _t496
					_t497 := &pb.Type{}
					_t497.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type84}
					_t495 = _t497
				} else {
					var _t498 *pb.Type
					if prediction76 == 6 {
						_t499 := p.parse_date_type()
						date_type83 := _t499
						_t500 := &pb.Type{}
						_t500.Type = &pb.Type_DateType{DateType: date_type83}
						_t498 = _t500
					} else {
						var _t501 *pb.Type
						if prediction76 == 5 {
							_t502 := p.parse_int128_type()
							int128_type82 := _t502
							_t503 := &pb.Type{}
							_t503.Type = &pb.Type_Int128Type{Int128Type: int128_type82}
							_t501 = _t503
						} else {
							var _t504 *pb.Type
							if prediction76 == 4 {
								_t505 := p.parse_uint128_type()
								uint128_type81 := _t505
								_t506 := &pb.Type{}
								_t506.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type81}
								_t504 = _t506
							} else {
								var _t507 *pb.Type
								if prediction76 == 3 {
									_t508 := p.parse_float_type()
									float_type80 := _t508
									_t509 := &pb.Type{}
									_t509.Type = &pb.Type_FloatType{FloatType: float_type80}
									_t507 = _t509
								} else {
									var _t510 *pb.Type
									if prediction76 == 2 {
										_t511 := p.parse_int_type()
										int_type79 := _t511
										_t512 := &pb.Type{}
										_t512.Type = &pb.Type_IntType{IntType: int_type79}
										_t510 = _t512
									} else {
										var _t513 *pb.Type
										if prediction76 == 1 {
											_t514 := p.parse_string_type()
											string_type78 := _t514
											_t515 := &pb.Type{}
											_t515.Type = &pb.Type_StringType{StringType: string_type78}
											_t513 = _t515
										} else {
											var _t516 *pb.Type
											if prediction76 == 0 {
												_t517 := p.parse_unspecified_type()
												unspecified_type77 := _t517
												_t518 := &pb.Type{}
												_t518.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type77}
												_t516 = _t518
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t513 = _t516
										}
										_t510 = _t513
									}
									_t507 = _t510
								}
								_t504 = _t507
							}
							_t501 = _t504
						}
						_t498 = _t501
					}
					_t495 = _t498
				}
				_t492 = _t495
			}
			_t489 = _t492
		}
		_t486 = _t489
	}
	return _t486
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t519 := &pb.UnspecifiedType{}
	return _t519
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t520 := &pb.StringType{}
	return _t520
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t521 := &pb.IntType{}
	return _t521
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t522 := &pb.FloatType{}
	return _t522
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t523 := &pb.UInt128Type{}
	return _t523
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t524 := &pb.Int128Type{}
	return _t524
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t525 := &pb.DateType{}
	return _t525
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t526 := &pb.DateTimeType{}
	return _t526
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t527 := &pb.MissingType{}
	return _t527
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int88 := p.consumeTerminal("INT").Value.AsInt64()
	int_389 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t528 := &pb.DecimalType{Precision: int32(int88), Scale: int32(int_389)}
	return _t528
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t529 := &pb.BooleanType{}
	return _t529
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs90 := []*pb.Binding{}
	cond91 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond91 {
		_t530 := p.parse_binding()
		item92 := _t530
		xs90 = append(xs90, item92)
		cond91 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings93 := xs90
	return bindings93
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t531 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t532 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t532 = 0
		} else {
			var _t533 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t533 = 11
			} else {
				var _t534 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t534 = 3
				} else {
					var _t535 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t535 = 10
					} else {
						var _t536 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t536 = 9
						} else {
							var _t537 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t537 = 5
							} else {
								var _t538 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t538 = 6
								} else {
									var _t539 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t539 = 7
									} else {
										var _t540 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t540 = 1
										} else {
											var _t541 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t541 = 2
											} else {
												var _t542 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t542 = 12
												} else {
													var _t543 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t543 = 8
													} else {
														var _t544 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t544 = 4
														} else {
															var _t545 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t545 = 10
															} else {
																var _t546 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t546 = 10
																} else {
																	var _t547 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t547 = 10
																	} else {
																		var _t548 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t548 = 10
																		} else {
																			var _t549 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t549 = 10
																			} else {
																				var _t550 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t550 = 10
																				} else {
																					var _t551 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t551 = 10
																					} else {
																						var _t552 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t552 = 10
																						} else {
																							var _t553 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t553 = 10
																							} else {
																								_t553 = -1
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
					}
					_t534 = _t535
				}
				_t533 = _t534
			}
			_t532 = _t533
		}
		_t531 = _t532
	} else {
		_t531 = -1
	}
	prediction94 := _t531
	var _t554 *pb.Formula
	if prediction94 == 12 {
		_t555 := p.parse_cast()
		cast107 := _t555
		_t556 := &pb.Formula{}
		_t556.FormulaType = &pb.Formula_Cast{Cast: cast107}
		_t554 = _t556
	} else {
		var _t557 *pb.Formula
		if prediction94 == 11 {
			_t558 := p.parse_rel_atom()
			rel_atom106 := _t558
			_t559 := &pb.Formula{}
			_t559.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom106}
			_t557 = _t559
		} else {
			var _t560 *pb.Formula
			if prediction94 == 10 {
				_t561 := p.parse_primitive()
				primitive105 := _t561
				_t562 := &pb.Formula{}
				_t562.FormulaType = &pb.Formula_Primitive{Primitive: primitive105}
				_t560 = _t562
			} else {
				var _t563 *pb.Formula
				if prediction94 == 9 {
					_t564 := p.parse_pragma()
					pragma104 := _t564
					_t565 := &pb.Formula{}
					_t565.FormulaType = &pb.Formula_Pragma{Pragma: pragma104}
					_t563 = _t565
				} else {
					var _t566 *pb.Formula
					if prediction94 == 8 {
						_t567 := p.parse_atom()
						atom103 := _t567
						_t568 := &pb.Formula{}
						_t568.FormulaType = &pb.Formula_Atom{Atom: atom103}
						_t566 = _t568
					} else {
						var _t569 *pb.Formula
						if prediction94 == 7 {
							_t570 := p.parse_ffi()
							ffi102 := _t570
							_t571 := &pb.Formula{}
							_t571.FormulaType = &pb.Formula_Ffi{Ffi: ffi102}
							_t569 = _t571
						} else {
							var _t572 *pb.Formula
							if prediction94 == 6 {
								_t573 := p.parse_not()
								not101 := _t573
								_t574 := &pb.Formula{}
								_t574.FormulaType = &pb.Formula_Not{Not: not101}
								_t572 = _t574
							} else {
								var _t575 *pb.Formula
								if prediction94 == 5 {
									_t576 := p.parse_disjunction()
									disjunction100 := _t576
									_t577 := &pb.Formula{}
									_t577.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction100}
									_t575 = _t577
								} else {
									var _t578 *pb.Formula
									if prediction94 == 4 {
										_t579 := p.parse_conjunction()
										conjunction99 := _t579
										_t580 := &pb.Formula{}
										_t580.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction99}
										_t578 = _t580
									} else {
										var _t581 *pb.Formula
										if prediction94 == 3 {
											_t582 := p.parse_reduce()
											reduce98 := _t582
											_t583 := &pb.Formula{}
											_t583.FormulaType = &pb.Formula_Reduce{Reduce: reduce98}
											_t581 = _t583
										} else {
											var _t584 *pb.Formula
											if prediction94 == 2 {
												_t585 := p.parse_exists()
												exists97 := _t585
												_t586 := &pb.Formula{}
												_t586.FormulaType = &pb.Formula_Exists{Exists: exists97}
												_t584 = _t586
											} else {
												var _t587 *pb.Formula
												if prediction94 == 1 {
													_t588 := p.parse_false()
													false96 := _t588
													_t589 := &pb.Formula{}
													_t589.FormulaType = &pb.Formula_Disjunction{Disjunction: false96}
													_t587 = _t589
												} else {
													var _t590 *pb.Formula
													if prediction94 == 0 {
														_t591 := p.parse_true()
														true95 := _t591
														_t592 := &pb.Formula{}
														_t592.FormulaType = &pb.Formula_Conjunction{Conjunction: true95}
														_t590 = _t592
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t587 = _t590
												}
												_t584 = _t587
											}
											_t581 = _t584
										}
										_t578 = _t581
									}
									_t575 = _t578
								}
								_t572 = _t575
							}
							_t569 = _t572
						}
						_t566 = _t569
					}
					_t563 = _t566
				}
				_t560 = _t563
			}
			_t557 = _t560
		}
		_t554 = _t557
	}
	return _t554
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t593 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t593
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t594 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t594
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t595 := p.parse_bindings()
	bindings108 := _t595
	_t596 := p.parse_formula()
	formula109 := _t596
	p.consumeLiteral(")")
	_t597 := &pb.Abstraction{Vars: listConcat(bindings108[0].([]*pb.Binding), bindings108[1].([]*pb.Binding)), Value: formula109}
	_t598 := &pb.Exists{Body: _t597}
	return _t598
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t599 := p.parse_abstraction()
	abstraction110 := _t599
	_t600 := p.parse_abstraction()
	abstraction_3111 := _t600
	_t601 := p.parse_terms()
	terms112 := _t601
	p.consumeLiteral(")")
	_t602 := &pb.Reduce{Op: abstraction110, Body: abstraction_3111, Terms: terms112}
	return _t602
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs113 := []*pb.Term{}
	cond114 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond114 {
		_t603 := p.parse_term()
		item115 := _t603
		xs113 = append(xs113, item115)
		cond114 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms116 := xs113
	p.consumeLiteral(")")
	return terms116
}

func (p *Parser) parse_term() *pb.Term {
	var _t604 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t604 = 1
	} else {
		var _t605 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t605 = 1
		} else {
			var _t606 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t606 = 1
			} else {
				var _t607 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t607 = 1
				} else {
					var _t608 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t608 = 1
					} else {
						var _t609 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t609 = 0
						} else {
							var _t610 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t610 = 1
							} else {
								var _t611 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t611 = 1
								} else {
									var _t612 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t612 = 1
									} else {
										var _t613 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t613 = 1
										} else {
											var _t614 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t614 = 1
											} else {
												_t614 = -1
											}
											_t613 = _t614
										}
										_t612 = _t613
									}
									_t611 = _t612
								}
								_t610 = _t611
							}
							_t609 = _t610
						}
						_t608 = _t609
					}
					_t607 = _t608
				}
				_t606 = _t607
			}
			_t605 = _t606
		}
		_t604 = _t605
	}
	prediction117 := _t604
	var _t615 *pb.Term
	if prediction117 == 1 {
		_t616 := p.parse_constant()
		constant119 := _t616
		_t617 := &pb.Term{}
		_t617.TermType = &pb.Term_Constant{Constant: constant119}
		_t615 = _t617
	} else {
		var _t618 *pb.Term
		if prediction117 == 0 {
			_t619 := p.parse_var()
			var118 := _t619
			_t620 := &pb.Term{}
			_t620.TermType = &pb.Term_Var{Var: var118}
			_t618 = _t620
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t615 = _t618
	}
	return _t615
}

func (p *Parser) parse_var() *pb.Var {
	symbol120 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t621 := &pb.Var{Name: symbol120}
	return _t621
}

func (p *Parser) parse_constant() *pb.Value {
	_t622 := p.parse_value()
	value121 := _t622
	return value121
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs122 := []*pb.Formula{}
	cond123 := p.matchLookaheadLiteral("(", 0)
	for cond123 {
		_t623 := p.parse_formula()
		item124 := _t623
		xs122 = append(xs122, item124)
		cond123 = p.matchLookaheadLiteral("(", 0)
	}
	formulas125 := xs122
	p.consumeLiteral(")")
	_t624 := &pb.Conjunction{Args: formulas125}
	return _t624
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs126 := []*pb.Formula{}
	cond127 := p.matchLookaheadLiteral("(", 0)
	for cond127 {
		_t625 := p.parse_formula()
		item128 := _t625
		xs126 = append(xs126, item128)
		cond127 = p.matchLookaheadLiteral("(", 0)
	}
	formulas129 := xs126
	p.consumeLiteral(")")
	_t626 := &pb.Disjunction{Args: formulas129}
	return _t626
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t627 := p.parse_formula()
	formula130 := _t627
	p.consumeLiteral(")")
	_t628 := &pb.Not{Arg: formula130}
	return _t628
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t629 := p.parse_name()
	name131 := _t629
	_t630 := p.parse_ffi_args()
	ffi_args132 := _t630
	_t631 := p.parse_terms()
	terms133 := _t631
	p.consumeLiteral(")")
	_t632 := &pb.FFI{Name: name131, Args: ffi_args132, Terms: terms133}
	return _t632
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol134 := p.consumeTerminal("SYMBOL").Value.AsString()
	return symbol134
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs135 := []*pb.Abstraction{}
	cond136 := p.matchLookaheadLiteral("(", 0)
	for cond136 {
		_t633 := p.parse_abstraction()
		item137 := _t633
		xs135 = append(xs135, item137)
		cond136 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions138 := xs135
	p.consumeLiteral(")")
	return abstractions138
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t634 := p.parse_relation_id()
	relation_id139 := _t634
	xs140 := []*pb.Term{}
	cond141 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond141 {
		_t635 := p.parse_term()
		item142 := _t635
		xs140 = append(xs140, item142)
		cond141 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms143 := xs140
	p.consumeLiteral(")")
	_t636 := &pb.Atom{Name: relation_id139, Terms: terms143}
	return _t636
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t637 := p.parse_name()
	name144 := _t637
	xs145 := []*pb.Term{}
	cond146 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond146 {
		_t638 := p.parse_term()
		item147 := _t638
		xs145 = append(xs145, item147)
		cond146 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms148 := xs145
	p.consumeLiteral(")")
	_t639 := &pb.Pragma{Name: name144, Terms: terms148}
	return _t639
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t640 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t641 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t641 = 9
		} else {
			var _t642 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t642 = 4
			} else {
				var _t643 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t643 = 3
				} else {
					var _t644 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t644 = 0
					} else {
						var _t645 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t645 = 2
						} else {
							var _t646 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t646 = 1
							} else {
								var _t647 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t647 = 8
								} else {
									var _t648 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t648 = 6
									} else {
										var _t649 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t649 = 5
										} else {
											var _t650 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t650 = 7
											} else {
												_t650 = -1
											}
											_t649 = _t650
										}
										_t648 = _t649
									}
									_t647 = _t648
								}
								_t646 = _t647
							}
							_t645 = _t646
						}
						_t644 = _t645
					}
					_t643 = _t644
				}
				_t642 = _t643
			}
			_t641 = _t642
		}
		_t640 = _t641
	} else {
		_t640 = -1
	}
	prediction149 := _t640
	var _t651 *pb.Primitive
	if prediction149 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t652 := p.parse_name()
		name159 := _t652
		xs160 := []*pb.RelTerm{}
		cond161 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond161 {
			_t653 := p.parse_rel_term()
			item162 := _t653
			xs160 = append(xs160, item162)
			cond161 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms163 := xs160
		p.consumeLiteral(")")
		_t654 := &pb.Primitive{Name: name159, Terms: rel_terms163}
		_t651 = _t654
	} else {
		var _t655 *pb.Primitive
		if prediction149 == 8 {
			_t656 := p.parse_divide()
			divide158 := _t656
			_t655 = divide158
		} else {
			var _t657 *pb.Primitive
			if prediction149 == 7 {
				_t658 := p.parse_multiply()
				multiply157 := _t658
				_t657 = multiply157
			} else {
				var _t659 *pb.Primitive
				if prediction149 == 6 {
					_t660 := p.parse_minus()
					minus156 := _t660
					_t659 = minus156
				} else {
					var _t661 *pb.Primitive
					if prediction149 == 5 {
						_t662 := p.parse_add()
						add155 := _t662
						_t661 = add155
					} else {
						var _t663 *pb.Primitive
						if prediction149 == 4 {
							_t664 := p.parse_gt_eq()
							gt_eq154 := _t664
							_t663 = gt_eq154
						} else {
							var _t665 *pb.Primitive
							if prediction149 == 3 {
								_t666 := p.parse_gt()
								gt153 := _t666
								_t665 = gt153
							} else {
								var _t667 *pb.Primitive
								if prediction149 == 2 {
									_t668 := p.parse_lt_eq()
									lt_eq152 := _t668
									_t667 = lt_eq152
								} else {
									var _t669 *pb.Primitive
									if prediction149 == 1 {
										_t670 := p.parse_lt()
										lt151 := _t670
										_t669 = lt151
									} else {
										var _t671 *pb.Primitive
										if prediction149 == 0 {
											_t672 := p.parse_eq()
											eq150 := _t672
											_t671 = eq150
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t669 = _t671
									}
									_t667 = _t669
								}
								_t665 = _t667
							}
							_t663 = _t665
						}
						_t661 = _t663
					}
					_t659 = _t661
				}
				_t657 = _t659
			}
			_t655 = _t657
		}
		_t651 = _t655
	}
	return _t651
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t673 := p.parse_term()
	term164 := _t673
	_t674 := p.parse_term()
	term_3165 := _t674
	p.consumeLiteral(")")
	_t675 := &pb.RelTerm{}
	_t675.RelTermType = &pb.RelTerm_Term{Term: term164}
	_t676 := &pb.RelTerm{}
	_t676.RelTermType = &pb.RelTerm_Term{Term: term_3165}
	_t677 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t675, _t676}}
	return _t677
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t678 := p.parse_term()
	term166 := _t678
	_t679 := p.parse_term()
	term_3167 := _t679
	p.consumeLiteral(")")
	_t680 := &pb.RelTerm{}
	_t680.RelTermType = &pb.RelTerm_Term{Term: term166}
	_t681 := &pb.RelTerm{}
	_t681.RelTermType = &pb.RelTerm_Term{Term: term_3167}
	_t682 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t680, _t681}}
	return _t682
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t683 := p.parse_term()
	term168 := _t683
	_t684 := p.parse_term()
	term_3169 := _t684
	p.consumeLiteral(")")
	_t685 := &pb.RelTerm{}
	_t685.RelTermType = &pb.RelTerm_Term{Term: term168}
	_t686 := &pb.RelTerm{}
	_t686.RelTermType = &pb.RelTerm_Term{Term: term_3169}
	_t687 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t685, _t686}}
	return _t687
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t688 := p.parse_term()
	term170 := _t688
	_t689 := p.parse_term()
	term_3171 := _t689
	p.consumeLiteral(")")
	_t690 := &pb.RelTerm{}
	_t690.RelTermType = &pb.RelTerm_Term{Term: term170}
	_t691 := &pb.RelTerm{}
	_t691.RelTermType = &pb.RelTerm_Term{Term: term_3171}
	_t692 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t690, _t691}}
	return _t692
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t693 := p.parse_term()
	term172 := _t693
	_t694 := p.parse_term()
	term_3173 := _t694
	p.consumeLiteral(")")
	_t695 := &pb.RelTerm{}
	_t695.RelTermType = &pb.RelTerm_Term{Term: term172}
	_t696 := &pb.RelTerm{}
	_t696.RelTermType = &pb.RelTerm_Term{Term: term_3173}
	_t697 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t695, _t696}}
	return _t697
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t698 := p.parse_term()
	term174 := _t698
	_t699 := p.parse_term()
	term_3175 := _t699
	_t700 := p.parse_term()
	term_4176 := _t700
	p.consumeLiteral(")")
	_t701 := &pb.RelTerm{}
	_t701.RelTermType = &pb.RelTerm_Term{Term: term174}
	_t702 := &pb.RelTerm{}
	_t702.RelTermType = &pb.RelTerm_Term{Term: term_3175}
	_t703 := &pb.RelTerm{}
	_t703.RelTermType = &pb.RelTerm_Term{Term: term_4176}
	_t704 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t701, _t702, _t703}}
	return _t704
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t705 := p.parse_term()
	term177 := _t705
	_t706 := p.parse_term()
	term_3178 := _t706
	_t707 := p.parse_term()
	term_4179 := _t707
	p.consumeLiteral(")")
	_t708 := &pb.RelTerm{}
	_t708.RelTermType = &pb.RelTerm_Term{Term: term177}
	_t709 := &pb.RelTerm{}
	_t709.RelTermType = &pb.RelTerm_Term{Term: term_3178}
	_t710 := &pb.RelTerm{}
	_t710.RelTermType = &pb.RelTerm_Term{Term: term_4179}
	_t711 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t708, _t709, _t710}}
	return _t711
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t712 := p.parse_term()
	term180 := _t712
	_t713 := p.parse_term()
	term_3181 := _t713
	_t714 := p.parse_term()
	term_4182 := _t714
	p.consumeLiteral(")")
	_t715 := &pb.RelTerm{}
	_t715.RelTermType = &pb.RelTerm_Term{Term: term180}
	_t716 := &pb.RelTerm{}
	_t716.RelTermType = &pb.RelTerm_Term{Term: term_3181}
	_t717 := &pb.RelTerm{}
	_t717.RelTermType = &pb.RelTerm_Term{Term: term_4182}
	_t718 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t715, _t716, _t717}}
	return _t718
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t719 := p.parse_term()
	term183 := _t719
	_t720 := p.parse_term()
	term_3184 := _t720
	_t721 := p.parse_term()
	term_4185 := _t721
	p.consumeLiteral(")")
	_t722 := &pb.RelTerm{}
	_t722.RelTermType = &pb.RelTerm_Term{Term: term183}
	_t723 := &pb.RelTerm{}
	_t723.RelTermType = &pb.RelTerm_Term{Term: term_3184}
	_t724 := &pb.RelTerm{}
	_t724.RelTermType = &pb.RelTerm_Term{Term: term_4185}
	_t725 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t722, _t723, _t724}}
	return _t725
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t726 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t726 = 1
	} else {
		var _t727 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t727 = 1
		} else {
			var _t728 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t728 = 1
			} else {
				var _t729 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t729 = 1
				} else {
					var _t730 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t730 = 0
					} else {
						var _t731 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t731 = 1
						} else {
							var _t732 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t732 = 1
							} else {
								var _t733 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t733 = 1
								} else {
									var _t734 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t734 = 1
									} else {
										var _t735 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t735 = 1
										} else {
											var _t736 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t736 = 1
											} else {
												var _t737 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t737 = 1
												} else {
													_t737 = -1
												}
												_t736 = _t737
											}
											_t735 = _t736
										}
										_t734 = _t735
									}
									_t733 = _t734
								}
								_t732 = _t733
							}
							_t731 = _t732
						}
						_t730 = _t731
					}
					_t729 = _t730
				}
				_t728 = _t729
			}
			_t727 = _t728
		}
		_t726 = _t727
	}
	prediction186 := _t726
	var _t738 *pb.RelTerm
	if prediction186 == 1 {
		_t739 := p.parse_term()
		term188 := _t739
		_t740 := &pb.RelTerm{}
		_t740.RelTermType = &pb.RelTerm_Term{Term: term188}
		_t738 = _t740
	} else {
		var _t741 *pb.RelTerm
		if prediction186 == 0 {
			_t742 := p.parse_specialized_value()
			specialized_value187 := _t742
			_t743 := &pb.RelTerm{}
			_t743.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value187}
			_t741 = _t743
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t738 = _t741
	}
	return _t738
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t744 := p.parse_value()
	value189 := _t744
	return value189
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t745 := p.parse_name()
	name190 := _t745
	xs191 := []*pb.RelTerm{}
	cond192 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond192 {
		_t746 := p.parse_rel_term()
		item193 := _t746
		xs191 = append(xs191, item193)
		cond192 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms194 := xs191
	p.consumeLiteral(")")
	_t747 := &pb.RelAtom{Name: name190, Terms: rel_terms194}
	return _t747
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t748 := p.parse_term()
	term195 := _t748
	_t749 := p.parse_term()
	term_3196 := _t749
	p.consumeLiteral(")")
	_t750 := &pb.Cast{Input: term195, Result: term_3196}
	return _t750
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs197 := []*pb.Attribute{}
	cond198 := p.matchLookaheadLiteral("(", 0)
	for cond198 {
		_t751 := p.parse_attribute()
		item199 := _t751
		xs197 = append(xs197, item199)
		cond198 = p.matchLookaheadLiteral("(", 0)
	}
	attributes200 := xs197
	p.consumeLiteral(")")
	return attributes200
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t752 := p.parse_name()
	name201 := _t752
	xs202 := []*pb.Value{}
	cond203 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond203 {
		_t753 := p.parse_value()
		item204 := _t753
		xs202 = append(xs202, item204)
		cond203 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values205 := xs202
	p.consumeLiteral(")")
	_t754 := &pb.Attribute{Name: name201, Args: values205}
	return _t754
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs206 := []*pb.RelationId{}
	cond207 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond207 {
		_t755 := p.parse_relation_id()
		item208 := _t755
		xs206 = append(xs206, item208)
		cond207 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids209 := xs206
	_t756 := p.parse_script()
	script210 := _t756
	p.consumeLiteral(")")
	_t757 := &pb.Algorithm{Global: relation_ids209, Body: script210}
	return _t757
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs211 := []*pb.Construct{}
	cond212 := p.matchLookaheadLiteral("(", 0)
	for cond212 {
		_t758 := p.parse_construct()
		item213 := _t758
		xs211 = append(xs211, item213)
		cond212 = p.matchLookaheadLiteral("(", 0)
	}
	constructs214 := xs211
	p.consumeLiteral(")")
	_t759 := &pb.Script{Constructs: constructs214}
	return _t759
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t760 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t761 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t761 = 1
		} else {
			var _t762 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t762 = 1
			} else {
				var _t763 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t763 = 1
				} else {
					var _t764 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t764 = 0
					} else {
						var _t765 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t765 = 1
						} else {
							var _t766 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t766 = 1
							} else {
								_t766 = -1
							}
							_t765 = _t766
						}
						_t764 = _t765
					}
					_t763 = _t764
				}
				_t762 = _t763
			}
			_t761 = _t762
		}
		_t760 = _t761
	} else {
		_t760 = -1
	}
	prediction215 := _t760
	var _t767 *pb.Construct
	if prediction215 == 1 {
		_t768 := p.parse_instruction()
		instruction217 := _t768
		_t769 := &pb.Construct{}
		_t769.ConstructType = &pb.Construct_Instruction{Instruction: instruction217}
		_t767 = _t769
	} else {
		var _t770 *pb.Construct
		if prediction215 == 0 {
			_t771 := p.parse_loop()
			loop216 := _t771
			_t772 := &pb.Construct{}
			_t772.ConstructType = &pb.Construct_Loop{Loop: loop216}
			_t770 = _t772
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t767 = _t770
	}
	return _t767
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t773 := p.parse_init()
	init218 := _t773
	_t774 := p.parse_script()
	script219 := _t774
	p.consumeLiteral(")")
	_t775 := &pb.Loop{Init: init218, Body: script219}
	return _t775
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs220 := []*pb.Instruction{}
	cond221 := p.matchLookaheadLiteral("(", 0)
	for cond221 {
		_t776 := p.parse_instruction()
		item222 := _t776
		xs220 = append(xs220, item222)
		cond221 = p.matchLookaheadLiteral("(", 0)
	}
	instructions223 := xs220
	p.consumeLiteral(")")
	return instructions223
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t777 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t778 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t778 = 1
		} else {
			var _t779 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t779 = 4
			} else {
				var _t780 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t780 = 3
				} else {
					var _t781 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t781 = 2
					} else {
						var _t782 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t782 = 0
						} else {
							_t782 = -1
						}
						_t781 = _t782
					}
					_t780 = _t781
				}
				_t779 = _t780
			}
			_t778 = _t779
		}
		_t777 = _t778
	} else {
		_t777 = -1
	}
	prediction224 := _t777
	var _t783 *pb.Instruction
	if prediction224 == 4 {
		_t784 := p.parse_monus_def()
		monus_def229 := _t784
		_t785 := &pb.Instruction{}
		_t785.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def229}
		_t783 = _t785
	} else {
		var _t786 *pb.Instruction
		if prediction224 == 3 {
			_t787 := p.parse_monoid_def()
			monoid_def228 := _t787
			_t788 := &pb.Instruction{}
			_t788.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def228}
			_t786 = _t788
		} else {
			var _t789 *pb.Instruction
			if prediction224 == 2 {
				_t790 := p.parse_break()
				break227 := _t790
				_t791 := &pb.Instruction{}
				_t791.InstrType = &pb.Instruction_Break{Break: break227}
				_t789 = _t791
			} else {
				var _t792 *pb.Instruction
				if prediction224 == 1 {
					_t793 := p.parse_upsert()
					upsert226 := _t793
					_t794 := &pb.Instruction{}
					_t794.InstrType = &pb.Instruction_Upsert{Upsert: upsert226}
					_t792 = _t794
				} else {
					var _t795 *pb.Instruction
					if prediction224 == 0 {
						_t796 := p.parse_assign()
						assign225 := _t796
						_t797 := &pb.Instruction{}
						_t797.InstrType = &pb.Instruction_Assign{Assign: assign225}
						_t795 = _t797
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t792 = _t795
				}
				_t789 = _t792
			}
			_t786 = _t789
		}
		_t783 = _t786
	}
	return _t783
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t798 := p.parse_relation_id()
	relation_id230 := _t798
	_t799 := p.parse_abstraction()
	abstraction231 := _t799
	var _t800 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t801 := p.parse_attrs()
		_t800 = _t801
	}
	attrs232 := _t800
	p.consumeLiteral(")")
	_t802 := attrs232
	if attrs232 == nil {
		_t802 = []*pb.Attribute{}
	}
	_t803 := &pb.Assign{Name: relation_id230, Body: abstraction231, Attrs: _t802}
	return _t803
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t804 := p.parse_relation_id()
	relation_id233 := _t804
	_t805 := p.parse_abstraction_with_arity()
	abstraction_with_arity234 := _t805
	var _t806 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t807 := p.parse_attrs()
		_t806 = _t807
	}
	attrs235 := _t806
	p.consumeLiteral(")")
	_t808 := attrs235
	if attrs235 == nil {
		_t808 = []*pb.Attribute{}
	}
	_t809 := &pb.Upsert{Name: relation_id233, Body: abstraction_with_arity234[0].(*pb.Abstraction), Attrs: _t808, ValueArity: abstraction_with_arity234[1].(int64)}
	return _t809
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t810 := p.parse_bindings()
	bindings236 := _t810
	_t811 := p.parse_formula()
	formula237 := _t811
	p.consumeLiteral(")")
	_t812 := &pb.Abstraction{Vars: listConcat(bindings236[0].([]*pb.Binding), bindings236[1].([]*pb.Binding)), Value: formula237}
	return []interface{}{_t812, int64(len(bindings236[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t813 := p.parse_relation_id()
	relation_id238 := _t813
	_t814 := p.parse_abstraction()
	abstraction239 := _t814
	var _t815 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t816 := p.parse_attrs()
		_t815 = _t816
	}
	attrs240 := _t815
	p.consumeLiteral(")")
	_t817 := attrs240
	if attrs240 == nil {
		_t817 = []*pb.Attribute{}
	}
	_t818 := &pb.Break{Name: relation_id238, Body: abstraction239, Attrs: _t817}
	return _t818
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t819 := p.parse_monoid()
	monoid241 := _t819
	_t820 := p.parse_relation_id()
	relation_id242 := _t820
	_t821 := p.parse_abstraction_with_arity()
	abstraction_with_arity243 := _t821
	var _t822 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t823 := p.parse_attrs()
		_t822 = _t823
	}
	attrs244 := _t822
	p.consumeLiteral(")")
	_t824 := attrs244
	if attrs244 == nil {
		_t824 = []*pb.Attribute{}
	}
	_t825 := &pb.MonoidDef{Monoid: monoid241, Name: relation_id242, Body: abstraction_with_arity243[0].(*pb.Abstraction), Attrs: _t824, ValueArity: abstraction_with_arity243[1].(int64)}
	return _t825
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t826 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t827 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t827 = 3
		} else {
			var _t828 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t828 = 0
			} else {
				var _t829 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t829 = 1
				} else {
					var _t830 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t830 = 2
					} else {
						_t830 = -1
					}
					_t829 = _t830
				}
				_t828 = _t829
			}
			_t827 = _t828
		}
		_t826 = _t827
	} else {
		_t826 = -1
	}
	prediction245 := _t826
	var _t831 *pb.Monoid
	if prediction245 == 3 {
		_t832 := p.parse_sum_monoid()
		sum_monoid249 := _t832
		_t833 := &pb.Monoid{}
		_t833.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid249}
		_t831 = _t833
	} else {
		var _t834 *pb.Monoid
		if prediction245 == 2 {
			_t835 := p.parse_max_monoid()
			max_monoid248 := _t835
			_t836 := &pb.Monoid{}
			_t836.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid248}
			_t834 = _t836
		} else {
			var _t837 *pb.Monoid
			if prediction245 == 1 {
				_t838 := p.parse_min_monoid()
				min_monoid247 := _t838
				_t839 := &pb.Monoid{}
				_t839.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid247}
				_t837 = _t839
			} else {
				var _t840 *pb.Monoid
				if prediction245 == 0 {
					_t841 := p.parse_or_monoid()
					or_monoid246 := _t841
					_t842 := &pb.Monoid{}
					_t842.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid246}
					_t840 = _t842
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t837 = _t840
			}
			_t834 = _t837
		}
		_t831 = _t834
	}
	return _t831
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t843 := &pb.OrMonoid{}
	return _t843
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t844 := p.parse_type()
	type250 := _t844
	p.consumeLiteral(")")
	_t845 := &pb.MinMonoid{Type: type250}
	return _t845
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t846 := p.parse_type()
	type251 := _t846
	p.consumeLiteral(")")
	_t847 := &pb.MaxMonoid{Type: type251}
	return _t847
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t848 := p.parse_type()
	type252 := _t848
	p.consumeLiteral(")")
	_t849 := &pb.SumMonoid{Type: type252}
	return _t849
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t850 := p.parse_monoid()
	monoid253 := _t850
	_t851 := p.parse_relation_id()
	relation_id254 := _t851
	_t852 := p.parse_abstraction_with_arity()
	abstraction_with_arity255 := _t852
	var _t853 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t854 := p.parse_attrs()
		_t853 = _t854
	}
	attrs256 := _t853
	p.consumeLiteral(")")
	_t855 := attrs256
	if attrs256 == nil {
		_t855 = []*pb.Attribute{}
	}
	_t856 := &pb.MonusDef{Monoid: monoid253, Name: relation_id254, Body: abstraction_with_arity255[0].(*pb.Abstraction), Attrs: _t855, ValueArity: abstraction_with_arity255[1].(int64)}
	return _t856
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t857 := p.parse_relation_id()
	relation_id257 := _t857
	_t858 := p.parse_abstraction()
	abstraction258 := _t858
	_t859 := p.parse_functional_dependency_keys()
	functional_dependency_keys259 := _t859
	_t860 := p.parse_functional_dependency_values()
	functional_dependency_values260 := _t860
	p.consumeLiteral(")")
	_t861 := &pb.FunctionalDependency{Guard: abstraction258, Keys: functional_dependency_keys259, Values: functional_dependency_values260}
	_t862 := &pb.Constraint{Name: relation_id257}
	_t862.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t861}
	return _t862
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs261 := []*pb.Var{}
	cond262 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond262 {
		_t863 := p.parse_var()
		item263 := _t863
		xs261 = append(xs261, item263)
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
		_t864 := p.parse_var()
		item267 := _t864
		xs265 = append(xs265, item267)
		cond266 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars268 := xs265
	p.consumeLiteral(")")
	return vars268
}

func (p *Parser) parse_data() *pb.Data {
	var _t865 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t866 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t866 = 0
		} else {
			var _t867 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t867 = 2
			} else {
				var _t868 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t868 = 1
				} else {
					_t868 = -1
				}
				_t867 = _t868
			}
			_t866 = _t867
		}
		_t865 = _t866
	} else {
		_t865 = -1
	}
	prediction269 := _t865
	var _t869 *pb.Data
	if prediction269 == 2 {
		_t870 := p.parse_csv_data()
		csv_data272 := _t870
		_t871 := &pb.Data{}
		_t871.DataType = &pb.Data_CsvData{CsvData: csv_data272}
		_t869 = _t871
	} else {
		var _t872 *pb.Data
		if prediction269 == 1 {
			_t873 := p.parse_betree_relation()
			betree_relation271 := _t873
			_t874 := &pb.Data{}
			_t874.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation271}
			_t872 = _t874
		} else {
			var _t875 *pb.Data
			if prediction269 == 0 {
				_t876 := p.parse_rel_edb()
				rel_edb270 := _t876
				_t877 := &pb.Data{}
				_t877.DataType = &pb.Data_RelEdb{RelEdb: rel_edb270}
				_t875 = _t877
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t872 = _t875
		}
		_t869 = _t872
	}
	return _t869
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t878 := p.parse_relation_id()
	relation_id273 := _t878
	_t879 := p.parse_rel_edb_path()
	rel_edb_path274 := _t879
	_t880 := p.parse_rel_edb_types()
	rel_edb_types275 := _t880
	p.consumeLiteral(")")
	_t881 := &pb.RelEDB{TargetId: relation_id273, Path: rel_edb_path274, Types: rel_edb_types275}
	return _t881
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs276 := []string{}
	cond277 := p.matchLookaheadTerminal("STRING", 0)
	for cond277 {
		item278 := p.consumeTerminal("STRING").Value.AsString()
		xs276 = append(xs276, item278)
		cond277 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings279 := xs276
	p.consumeLiteral("]")
	return strings279
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs280 := []*pb.Type{}
	cond281 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond281 {
		_t882 := p.parse_type()
		item282 := _t882
		xs280 = append(xs280, item282)
		cond281 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types283 := xs280
	p.consumeLiteral("]")
	return types283
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t883 := p.parse_relation_id()
	relation_id284 := _t883
	_t884 := p.parse_betree_info()
	betree_info285 := _t884
	p.consumeLiteral(")")
	_t885 := &pb.BeTreeRelation{Name: relation_id284, RelationInfo: betree_info285}
	return _t885
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t886 := p.parse_betree_info_key_types()
	betree_info_key_types286 := _t886
	_t887 := p.parse_betree_info_value_types()
	betree_info_value_types287 := _t887
	_t888 := p.parse_config_dict()
	config_dict288 := _t888
	p.consumeLiteral(")")
	_t889 := p.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
	return _t889
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs289 := []*pb.Type{}
	cond290 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond290 {
		_t890 := p.parse_type()
		item291 := _t890
		xs289 = append(xs289, item291)
		cond290 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types292 := xs289
	p.consumeLiteral(")")
	return types292
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs293 := []*pb.Type{}
	cond294 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond294 {
		_t891 := p.parse_type()
		item295 := _t891
		xs293 = append(xs293, item295)
		cond294 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types296 := xs293
	p.consumeLiteral(")")
	return types296
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t892 := p.parse_csvlocator()
	csvlocator297 := _t892
	_t893 := p.parse_csv_config()
	csv_config298 := _t893
	_t894 := p.parse_csv_columns()
	csv_columns299 := _t894
	_t895 := p.parse_csv_asof()
	csv_asof300 := _t895
	p.consumeLiteral(")")
	_t896 := &pb.CSVData{Locator: csvlocator297, Config: csv_config298, Columns: csv_columns299, Asof: csv_asof300}
	return _t896
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t897 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t898 := p.parse_csv_locator_paths()
		_t897 = _t898
	}
	csv_locator_paths301 := _t897
	var _t899 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t900 := p.parse_csv_locator_inline_data()
		_t899 = ptr(_t900)
	}
	csv_locator_inline_data302 := _t899
	p.consumeLiteral(")")
	_t901 := csv_locator_paths301
	if csv_locator_paths301 == nil {
		_t901 = []string{}
	}
	_t902 := &pb.CSVLocator{Paths: _t901, InlineData: []byte(deref(csv_locator_inline_data302, ""))}
	return _t902
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs303 := []string{}
	cond304 := p.matchLookaheadTerminal("STRING", 0)
	for cond304 {
		item305 := p.consumeTerminal("STRING").Value.AsString()
		xs303 = append(xs303, item305)
		cond304 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings306 := xs303
	p.consumeLiteral(")")
	return strings306
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string307 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string307
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t903 := p.parse_config_dict()
	config_dict308 := _t903
	p.consumeLiteral(")")
	_t904 := p.construct_csv_config(config_dict308)
	return _t904
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs309 := []*pb.CSVColumn{}
	cond310 := p.matchLookaheadLiteral("(", 0)
	for cond310 {
		_t905 := p.parse_csv_column()
		item311 := _t905
		xs309 = append(xs309, item311)
		cond310 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns312 := xs309
	p.consumeLiteral(")")
	return csv_columns312
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string313 := p.consumeTerminal("STRING").Value.AsString()
	_t906 := p.parse_relation_id()
	relation_id314 := _t906
	p.consumeLiteral("[")
	xs315 := []*pb.Type{}
	cond316 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond316 {
		_t907 := p.parse_type()
		item317 := _t907
		xs315 = append(xs315, item317)
		cond316 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types318 := xs315
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t908 := &pb.CSVColumn{ColumnName: string313, TargetId: relation_id314, Types: types318}
	return _t908
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string319 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string319
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t909 := p.parse_fragment_id()
	fragment_id320 := _t909
	p.consumeLiteral(")")
	_t910 := &pb.Undefine{FragmentId: fragment_id320}
	return _t910
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs321 := []*pb.RelationId{}
	cond322 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond322 {
		_t911 := p.parse_relation_id()
		item323 := _t911
		xs321 = append(xs321, item323)
		cond322 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids324 := xs321
	p.consumeLiteral(")")
	_t912 := &pb.Context{Relations: relation_ids324}
	return _t912
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs325 := []*pb.Read{}
	cond326 := p.matchLookaheadLiteral("(", 0)
	for cond326 {
		_t913 := p.parse_read()
		item327 := _t913
		xs325 = append(xs325, item327)
		cond326 = p.matchLookaheadLiteral("(", 0)
	}
	reads328 := xs325
	p.consumeLiteral(")")
	return reads328
}

func (p *Parser) parse_read() *pb.Read {
	var _t914 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t915 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t915 = 2
		} else {
			var _t916 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t916 = 1
			} else {
				var _t917 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t917 = 4
				} else {
					var _t918 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t918 = 0
					} else {
						var _t919 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t919 = 3
						} else {
							_t919 = -1
						}
						_t918 = _t919
					}
					_t917 = _t918
				}
				_t916 = _t917
			}
			_t915 = _t916
		}
		_t914 = _t915
	} else {
		_t914 = -1
	}
	prediction329 := _t914
	var _t920 *pb.Read
	if prediction329 == 4 {
		_t921 := p.parse_export()
		export334 := _t921
		_t922 := &pb.Read{}
		_t922.ReadType = &pb.Read_Export{Export: export334}
		_t920 = _t922
	} else {
		var _t923 *pb.Read
		if prediction329 == 3 {
			_t924 := p.parse_abort()
			abort333 := _t924
			_t925 := &pb.Read{}
			_t925.ReadType = &pb.Read_Abort{Abort: abort333}
			_t923 = _t925
		} else {
			var _t926 *pb.Read
			if prediction329 == 2 {
				_t927 := p.parse_what_if()
				what_if332 := _t927
				_t928 := &pb.Read{}
				_t928.ReadType = &pb.Read_WhatIf{WhatIf: what_if332}
				_t926 = _t928
			} else {
				var _t929 *pb.Read
				if prediction329 == 1 {
					_t930 := p.parse_output()
					output331 := _t930
					_t931 := &pb.Read{}
					_t931.ReadType = &pb.Read_Output{Output: output331}
					_t929 = _t931
				} else {
					var _t932 *pb.Read
					if prediction329 == 0 {
						_t933 := p.parse_demand()
						demand330 := _t933
						_t934 := &pb.Read{}
						_t934.ReadType = &pb.Read_Demand{Demand: demand330}
						_t932 = _t934
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t929 = _t932
				}
				_t926 = _t929
			}
			_t923 = _t926
		}
		_t920 = _t923
	}
	return _t920
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t935 := p.parse_relation_id()
	relation_id335 := _t935
	p.consumeLiteral(")")
	_t936 := &pb.Demand{RelationId: relation_id335}
	return _t936
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t937 := p.parse_name()
	name336 := _t937
	_t938 := p.parse_relation_id()
	relation_id337 := _t938
	p.consumeLiteral(")")
	_t939 := &pb.Output{Name: name336, RelationId: relation_id337}
	return _t939
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t940 := p.parse_name()
	name338 := _t940
	_t941 := p.parse_epoch()
	epoch339 := _t941
	p.consumeLiteral(")")
	_t942 := &pb.WhatIf{Branch: name338, Epoch: epoch339}
	return _t942
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t943 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t944 := p.parse_name()
		_t943 = ptr(_t944)
	}
	name340 := _t943
	_t945 := p.parse_relation_id()
	relation_id341 := _t945
	p.consumeLiteral(")")
	_t946 := &pb.Abort{Name: deref(name340, "abort"), RelationId: relation_id341}
	return _t946
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t947 := p.parse_export_csv_config()
	export_csv_config342 := _t947
	p.consumeLiteral(")")
	_t948 := &pb.Export{}
	_t948.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config342}
	return _t948
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t949 := p.parse_export_csv_path()
	export_csv_path343 := _t949
	_t950 := p.parse_export_csv_columns()
	export_csv_columns344 := _t950
	_t951 := p.parse_config_dict()
	config_dict345 := _t951
	p.consumeLiteral(")")
	_t952 := p.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)
	return _t952
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string346 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string346
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs347 := []*pb.ExportCSVColumn{}
	cond348 := p.matchLookaheadLiteral("(", 0)
	for cond348 {
		_t953 := p.parse_export_csv_column()
		item349 := _t953
		xs347 = append(xs347, item349)
		cond348 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns350 := xs347
	p.consumeLiteral(")")
	return export_csv_columns350
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string351 := p.consumeTerminal("STRING").Value.AsString()
	_t954 := p.parse_relation_id()
	relation_id352 := _t954
	p.consumeLiteral(")")
	_t955 := &pb.ExportCSVColumn{ColumnName: string351, ColumnData: relation_id352}
	return _t955
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
