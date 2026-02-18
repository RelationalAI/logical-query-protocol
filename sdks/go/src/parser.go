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

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t985 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t985
	_t986 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t986
	_t987 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t987
	_t988 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t988
	_t989 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t989
	_t990 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t990
	_t991 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t991
	_t992 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t992
	_t993 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t993
	_t994 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t994.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t994.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t994
	_t995 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t995
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
	_t996 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t996
	_t997 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t997
	_t998 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t998
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t999 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t999
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

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return nil
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	return nil
}

func (p *Parser) default_configure() *pb.Configure {
	_t1000 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1000
	_t1001 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1001
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	return default_
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1002 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1002
	_t1003 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1003
	_t1004 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1004
	_t1005 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1005
	_t1006 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1006
	_t1007 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1007
	_t1008 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1008
	_t1009 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1009
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	return default_
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1010 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1010
	_t1011 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1011
	_t1012 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1012
	_t1013 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1013
	_t1014 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1014
	_t1015 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1015
	_t1016 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1016
	_t1017 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1017
	_t1018 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1018
	_t1019 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1019
	_t1020 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1020
	_t1021 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size := _t1021
	_t1022 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size}
	return _t1022
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t363 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t364 := p.parse_configure()
		_t363 = _t364
	}
	configure0 := _t363
	var _t365 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t366 := p.parse_sync()
		_t365 = _t366
	}
	sync1 := _t365
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	for cond3 {
		_t367 := p.parse_epoch()
		item4 := _t367
		xs2 = append(xs2, item4)
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	epochs5 := xs2
	p.consumeLiteral(")")
	_t368 := p.default_configure()
	_t369 := configure0
	if configure0 == nil {
		_t369 = _t368
	}
	_t370 := &pb.Transaction{Epochs: epochs5, Configure: _t369, Sync: sync1}
	return _t370
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t371 := p.parse_config_dict()
	config_dict6 := _t371
	p.consumeLiteral(")")
	_t372 := p.construct_configure(config_dict6)
	return _t372
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs7 := [][]interface{}{}
	cond8 := p.matchLookaheadLiteral(":", 0)
	for cond8 {
		_t373 := p.parse_config_key_value()
		item9 := _t373
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
	_t374 := p.parse_value()
	value12 := _t374
	return []interface{}{symbol11, value12}
}

func (p *Parser) parse_value() *pb.Value {
	var _t375 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t375 = 9
	} else {
		var _t376 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t376 = 8
		} else {
			var _t377 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t377 = 9
			} else {
				var _t378 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t379 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t379 = 1
					} else {
						var _t380 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t380 = 0
						} else {
							_t380 = -1
						}
						_t379 = _t380
					}
					_t378 = _t379
				} else {
					var _t381 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t381 = 5
					} else {
						var _t382 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t382 = 2
						} else {
							var _t383 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t383 = 6
							} else {
								var _t384 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t384 = 3
								} else {
									var _t385 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t385 = 4
									} else {
										var _t386 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t386 = 7
										} else {
											_t386 = -1
										}
										_t385 = _t386
									}
									_t384 = _t385
								}
								_t383 = _t384
							}
							_t382 = _t383
						}
						_t381 = _t382
					}
					_t378 = _t381
				}
				_t377 = _t378
			}
			_t376 = _t377
		}
		_t375 = _t376
	}
	prediction13 := _t375
	var _t387 *pb.Value
	if prediction13 == 9 {
		_t388 := p.parse_boolean_value()
		boolean_value22 := _t388
		_t389 := &pb.Value{}
		_t389.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value22}
		_t387 = _t389
	} else {
		var _t390 *pb.Value
		if prediction13 == 8 {
			p.consumeLiteral("missing")
			_t391 := &pb.MissingValue{}
			_t392 := &pb.Value{}
			_t392.Value = &pb.Value_MissingValue{MissingValue: _t391}
			_t390 = _t392
		} else {
			var _t393 *pb.Value
			if prediction13 == 7 {
				decimal21 := p.consumeTerminal("DECIMAL").Value.AsDecimal()
				_t394 := &pb.Value{}
				_t394.Value = &pb.Value_DecimalValue{DecimalValue: decimal21}
				_t393 = _t394
			} else {
				var _t395 *pb.Value
				if prediction13 == 6 {
					int12820 := p.consumeTerminal("INT128").Value.AsInt128()
					_t396 := &pb.Value{}
					_t396.Value = &pb.Value_Int128Value{Int128Value: int12820}
					_t395 = _t396
				} else {
					var _t397 *pb.Value
					if prediction13 == 5 {
						uint12819 := p.consumeTerminal("UINT128").Value.AsUint128()
						_t398 := &pb.Value{}
						_t398.Value = &pb.Value_Uint128Value{Uint128Value: uint12819}
						_t397 = _t398
					} else {
						var _t399 *pb.Value
						if prediction13 == 4 {
							float18 := p.consumeTerminal("FLOAT").Value.AsFloat64()
							_t400 := &pb.Value{}
							_t400.Value = &pb.Value_FloatValue{FloatValue: float18}
							_t399 = _t400
						} else {
							var _t401 *pb.Value
							if prediction13 == 3 {
								int17 := p.consumeTerminal("INT").Value.AsInt64()
								_t402 := &pb.Value{}
								_t402.Value = &pb.Value_IntValue{IntValue: int17}
								_t401 = _t402
							} else {
								var _t403 *pb.Value
								if prediction13 == 2 {
									string16 := p.consumeTerminal("STRING").Value.AsString()
									_t404 := &pb.Value{}
									_t404.Value = &pb.Value_StringValue{StringValue: string16}
									_t403 = _t404
								} else {
									var _t405 *pb.Value
									if prediction13 == 1 {
										_t406 := p.parse_datetime()
										datetime15 := _t406
										_t407 := &pb.Value{}
										_t407.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime15}
										_t405 = _t407
									} else {
										var _t408 *pb.Value
										if prediction13 == 0 {
											_t409 := p.parse_date()
											date14 := _t409
											_t410 := &pb.Value{}
											_t410.Value = &pb.Value_DateValue{DateValue: date14}
											_t408 = _t410
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t405 = _t408
									}
									_t403 = _t405
								}
								_t401 = _t403
							}
							_t399 = _t401
						}
						_t397 = _t399
					}
					_t395 = _t397
				}
				_t393 = _t395
			}
			_t390 = _t393
		}
		_t387 = _t390
	}
	return _t387
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int23 := p.consumeTerminal("INT").Value.AsInt64()
	int_324 := p.consumeTerminal("INT").Value.AsInt64()
	int_425 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t411 := &pb.DateValue{Year: int32(int23), Month: int32(int_324), Day: int32(int_425)}
	return _t411
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
	var _t412 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t412 = ptr(p.consumeTerminal("INT").Value.AsInt64())
	}
	int_832 := _t412
	p.consumeLiteral(")")
	_t413 := &pb.DateTimeValue{Year: int32(int26), Month: int32(int_327), Day: int32(int_428), Hour: int32(int_529), Minute: int32(int_630), Second: int32(int_731), Microsecond: int32(deref(int_832, 0))}
	return _t413
}

func (p *Parser) parse_boolean_value() bool {
	var _t414 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t414 = 0
	} else {
		var _t415 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t415 = 1
		} else {
			_t415 = -1
		}
		_t414 = _t415
	}
	prediction33 := _t414
	var _t416 bool
	if prediction33 == 1 {
		p.consumeLiteral("false")
		_t416 = false
	} else {
		var _t417 bool
		if prediction33 == 0 {
			p.consumeLiteral("true")
			_t417 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t416 = _t417
	}
	return _t416
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs34 := []*pb.FragmentId{}
	cond35 := p.matchLookaheadLiteral(":", 0)
	for cond35 {
		_t418 := p.parse_fragment_id()
		item36 := _t418
		xs34 = append(xs34, item36)
		cond35 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids37 := xs34
	p.consumeLiteral(")")
	_t419 := &pb.Sync{Fragments: fragment_ids37}
	return _t419
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol38 := p.consumeTerminal("SYMBOL").Value.AsString()
	return &pb.FragmentId{Id: []byte(symbol38)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t420 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t421 := p.parse_epoch_writes()
		_t420 = _t421
	}
	epoch_writes39 := _t420
	var _t422 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t423 := p.parse_epoch_reads()
		_t422 = _t423
	}
	epoch_reads40 := _t422
	p.consumeLiteral(")")
	_t424 := epoch_writes39
	if epoch_writes39 == nil {
		_t424 = []*pb.Write{}
	}
	_t425 := epoch_reads40
	if epoch_reads40 == nil {
		_t425 = []*pb.Read{}
	}
	_t426 := &pb.Epoch{Writes: _t424, Reads: _t425}
	return _t426
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs41 := []*pb.Write{}
	cond42 := p.matchLookaheadLiteral("(", 0)
	for cond42 {
		_t427 := p.parse_write()
		item43 := _t427
		xs41 = append(xs41, item43)
		cond42 = p.matchLookaheadLiteral("(", 0)
	}
	writes44 := xs41
	p.consumeLiteral(")")
	return writes44
}

func (p *Parser) parse_write() *pb.Write {
	var _t428 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t429 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t429 = 1
		} else {
			var _t430 int64
			if p.matchLookaheadLiteral("define", 1) {
				_t430 = 0
			} else {
				var _t431 int64
				if p.matchLookaheadLiteral("context", 1) {
					_t431 = 2
				} else {
					_t431 = -1
				}
				_t430 = _t431
			}
			_t429 = _t430
		}
		_t428 = _t429
	} else {
		_t428 = -1
	}
	prediction45 := _t428
	var _t432 *pb.Write
	if prediction45 == 2 {
		_t433 := p.parse_context()
		context48 := _t433
		_t434 := &pb.Write{}
		_t434.WriteType = &pb.Write_Context{Context: context48}
		_t432 = _t434
	} else {
		var _t435 *pb.Write
		if prediction45 == 1 {
			_t436 := p.parse_undefine()
			undefine47 := _t436
			_t437 := &pb.Write{}
			_t437.WriteType = &pb.Write_Undefine{Undefine: undefine47}
			_t435 = _t437
		} else {
			var _t438 *pb.Write
			if prediction45 == 0 {
				_t439 := p.parse_define()
				define46 := _t439
				_t440 := &pb.Write{}
				_t440.WriteType = &pb.Write_Define{Define: define46}
				_t438 = _t440
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t435 = _t438
		}
		_t432 = _t435
	}
	return _t432
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t441 := p.parse_fragment()
	fragment49 := _t441
	p.consumeLiteral(")")
	_t442 := &pb.Define{Fragment: fragment49}
	return _t442
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t443 := p.parse_new_fragment_id()
	new_fragment_id50 := _t443
	xs51 := []*pb.Declaration{}
	cond52 := p.matchLookaheadLiteral("(", 0)
	for cond52 {
		_t444 := p.parse_declaration()
		item53 := _t444
		xs51 = append(xs51, item53)
		cond52 = p.matchLookaheadLiteral("(", 0)
	}
	declarations54 := xs51
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id50, declarations54)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t445 := p.parse_fragment_id()
	fragment_id55 := _t445
	p.startFragment(fragment_id55)
	return fragment_id55
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t446 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t447 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t447 = 3
		} else {
			var _t448 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t448 = 2
			} else {
				var _t449 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t449 = 0
				} else {
					var _t450 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t450 = 3
					} else {
						var _t451 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t451 = 3
						} else {
							var _t452 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t452 = 1
							} else {
								_t452 = -1
							}
							_t451 = _t452
						}
						_t450 = _t451
					}
					_t449 = _t450
				}
				_t448 = _t449
			}
			_t447 = _t448
		}
		_t446 = _t447
	} else {
		_t446 = -1
	}
	prediction56 := _t446
	var _t453 *pb.Declaration
	if prediction56 == 3 {
		_t454 := p.parse_data()
		data60 := _t454
		_t455 := &pb.Declaration{}
		_t455.DeclarationType = &pb.Declaration_Data{Data: data60}
		_t453 = _t455
	} else {
		var _t456 *pb.Declaration
		if prediction56 == 2 {
			_t457 := p.parse_constraint()
			constraint59 := _t457
			_t458 := &pb.Declaration{}
			_t458.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint59}
			_t456 = _t458
		} else {
			var _t459 *pb.Declaration
			if prediction56 == 1 {
				_t460 := p.parse_algorithm()
				algorithm58 := _t460
				_t461 := &pb.Declaration{}
				_t461.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm58}
				_t459 = _t461
			} else {
				var _t462 *pb.Declaration
				if prediction56 == 0 {
					_t463 := p.parse_def()
					def57 := _t463
					_t464 := &pb.Declaration{}
					_t464.DeclarationType = &pb.Declaration_Def{Def: def57}
					_t462 = _t464
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t459 = _t462
			}
			_t456 = _t459
		}
		_t453 = _t456
	}
	return _t453
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t465 := p.parse_relation_id()
	relation_id61 := _t465
	_t466 := p.parse_abstraction()
	abstraction62 := _t466
	var _t467 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t468 := p.parse_attrs()
		_t467 = _t468
	}
	attrs63 := _t467
	p.consumeLiteral(")")
	_t469 := attrs63
	if attrs63 == nil {
		_t469 = []*pb.Attribute{}
	}
	_t470 := &pb.Def{Name: relation_id61, Body: abstraction62, Attrs: _t469}
	return _t470
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t471 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t471 = 0
	} else {
		var _t472 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t472 = 1
		} else {
			_t472 = -1
		}
		_t471 = _t472
	}
	prediction64 := _t471
	var _t473 *pb.RelationId
	if prediction64 == 1 {
		uint12866 := p.consumeTerminal("UINT128").Value.AsUint128()
		_t473 = &pb.RelationId{IdLow: uint12866.Low, IdHigh: uint12866.High}
	} else {
		var _t474 *pb.RelationId
		if prediction64 == 0 {
			p.consumeLiteral(":")
			symbol65 := p.consumeTerminal("SYMBOL").Value.AsString()
			_t474 = p.relationIdFromString(symbol65)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t473 = _t474
	}
	return _t473
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t475 := p.parse_bindings()
	bindings67 := _t475
	_t476 := p.parse_formula()
	formula68 := _t476
	p.consumeLiteral(")")
	_t477 := &pb.Abstraction{Vars: listConcat(bindings67[0].([]*pb.Binding), bindings67[1].([]*pb.Binding)), Value: formula68}
	return _t477
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs69 := []*pb.Binding{}
	cond70 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond70 {
		_t478 := p.parse_binding()
		item71 := _t478
		xs69 = append(xs69, item71)
		cond70 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings72 := xs69
	var _t479 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t480 := p.parse_value_bindings()
		_t479 = _t480
	}
	value_bindings73 := _t479
	p.consumeLiteral("]")
	_t481 := value_bindings73
	if value_bindings73 == nil {
		_t481 = []*pb.Binding{}
	}
	return []interface{}{bindings72, _t481}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol74 := p.consumeTerminal("SYMBOL").Value.AsString()
	p.consumeLiteral("::")
	_t482 := p.parse_type()
	type75 := _t482
	_t483 := &pb.Var{Name: symbol74}
	_t484 := &pb.Binding{Var: _t483, Type: type75}
	return _t484
}

func (p *Parser) parse_type() *pb.Type {
	var _t485 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t485 = 0
	} else {
		var _t486 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t486 = 4
		} else {
			var _t487 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t487 = 1
			} else {
				var _t488 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t488 = 8
				} else {
					var _t489 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t489 = 5
					} else {
						var _t490 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t490 = 2
						} else {
							var _t491 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t491 = 3
							} else {
								var _t492 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t492 = 7
								} else {
									var _t493 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t493 = 6
									} else {
										var _t494 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t494 = 10
										} else {
											var _t495 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t495 = 9
											} else {
												_t495 = -1
											}
											_t494 = _t495
										}
										_t493 = _t494
									}
									_t492 = _t493
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
	prediction76 := _t485
	var _t496 *pb.Type
	if prediction76 == 10 {
		_t497 := p.parse_boolean_type()
		boolean_type87 := _t497
		_t498 := &pb.Type{}
		_t498.Type = &pb.Type_BooleanType{BooleanType: boolean_type87}
		_t496 = _t498
	} else {
		var _t499 *pb.Type
		if prediction76 == 9 {
			_t500 := p.parse_decimal_type()
			decimal_type86 := _t500
			_t501 := &pb.Type{}
			_t501.Type = &pb.Type_DecimalType{DecimalType: decimal_type86}
			_t499 = _t501
		} else {
			var _t502 *pb.Type
			if prediction76 == 8 {
				_t503 := p.parse_missing_type()
				missing_type85 := _t503
				_t504 := &pb.Type{}
				_t504.Type = &pb.Type_MissingType{MissingType: missing_type85}
				_t502 = _t504
			} else {
				var _t505 *pb.Type
				if prediction76 == 7 {
					_t506 := p.parse_datetime_type()
					datetime_type84 := _t506
					_t507 := &pb.Type{}
					_t507.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type84}
					_t505 = _t507
				} else {
					var _t508 *pb.Type
					if prediction76 == 6 {
						_t509 := p.parse_date_type()
						date_type83 := _t509
						_t510 := &pb.Type{}
						_t510.Type = &pb.Type_DateType{DateType: date_type83}
						_t508 = _t510
					} else {
						var _t511 *pb.Type
						if prediction76 == 5 {
							_t512 := p.parse_int128_type()
							int128_type82 := _t512
							_t513 := &pb.Type{}
							_t513.Type = &pb.Type_Int128Type{Int128Type: int128_type82}
							_t511 = _t513
						} else {
							var _t514 *pb.Type
							if prediction76 == 4 {
								_t515 := p.parse_uint128_type()
								uint128_type81 := _t515
								_t516 := &pb.Type{}
								_t516.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type81}
								_t514 = _t516
							} else {
								var _t517 *pb.Type
								if prediction76 == 3 {
									_t518 := p.parse_float_type()
									float_type80 := _t518
									_t519 := &pb.Type{}
									_t519.Type = &pb.Type_FloatType{FloatType: float_type80}
									_t517 = _t519
								} else {
									var _t520 *pb.Type
									if prediction76 == 2 {
										_t521 := p.parse_int_type()
										int_type79 := _t521
										_t522 := &pb.Type{}
										_t522.Type = &pb.Type_IntType{IntType: int_type79}
										_t520 = _t522
									} else {
										var _t523 *pb.Type
										if prediction76 == 1 {
											_t524 := p.parse_string_type()
											string_type78 := _t524
											_t525 := &pb.Type{}
											_t525.Type = &pb.Type_StringType{StringType: string_type78}
											_t523 = _t525
										} else {
											var _t526 *pb.Type
											if prediction76 == 0 {
												_t527 := p.parse_unspecified_type()
												unspecified_type77 := _t527
												_t528 := &pb.Type{}
												_t528.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type77}
												_t526 = _t528
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t523 = _t526
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
	return _t496
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t529 := &pb.UnspecifiedType{}
	return _t529
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t530 := &pb.StringType{}
	return _t530
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t531 := &pb.IntType{}
	return _t531
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t532 := &pb.FloatType{}
	return _t532
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t533 := &pb.UInt128Type{}
	return _t533
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t534 := &pb.Int128Type{}
	return _t534
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t535 := &pb.DateType{}
	return _t535
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t536 := &pb.DateTimeType{}
	return _t536
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t537 := &pb.MissingType{}
	return _t537
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int88 := p.consumeTerminal("INT").Value.AsInt64()
	int_389 := p.consumeTerminal("INT").Value.AsInt64()
	p.consumeLiteral(")")
	_t538 := &pb.DecimalType{Precision: int32(int88), Scale: int32(int_389)}
	return _t538
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t539 := &pb.BooleanType{}
	return _t539
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs90 := []*pb.Binding{}
	cond91 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond91 {
		_t540 := p.parse_binding()
		item92 := _t540
		xs90 = append(xs90, item92)
		cond91 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings93 := xs90
	return bindings93
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t541 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t542 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t542 = 0
		} else {
			var _t543 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t543 = 11
			} else {
				var _t544 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t544 = 3
				} else {
					var _t545 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t545 = 10
					} else {
						var _t546 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t546 = 9
						} else {
							var _t547 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t547 = 5
							} else {
								var _t548 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t548 = 6
								} else {
									var _t549 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t549 = 7
									} else {
										var _t550 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t550 = 1
										} else {
											var _t551 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t551 = 2
											} else {
												var _t552 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t552 = 12
												} else {
													var _t553 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t553 = 8
													} else {
														var _t554 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t554 = 4
														} else {
															var _t555 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t555 = 10
															} else {
																var _t556 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t556 = 10
																} else {
																	var _t557 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t557 = 10
																	} else {
																		var _t558 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t558 = 10
																		} else {
																			var _t559 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t559 = 10
																			} else {
																				var _t560 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t560 = 10
																				} else {
																					var _t561 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t561 = 10
																					} else {
																						var _t562 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t562 = 10
																						} else {
																							var _t563 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t563 = 10
																							} else {
																								_t563 = -1
																							}
																							_t562 = _t563
																						}
																						_t561 = _t562
																					}
																					_t560 = _t561
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
	} else {
		_t541 = -1
	}
	prediction94 := _t541
	var _t564 *pb.Formula
	if prediction94 == 12 {
		_t565 := p.parse_cast()
		cast107 := _t565
		_t566 := &pb.Formula{}
		_t566.FormulaType = &pb.Formula_Cast{Cast: cast107}
		_t564 = _t566
	} else {
		var _t567 *pb.Formula
		if prediction94 == 11 {
			_t568 := p.parse_rel_atom()
			rel_atom106 := _t568
			_t569 := &pb.Formula{}
			_t569.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom106}
			_t567 = _t569
		} else {
			var _t570 *pb.Formula
			if prediction94 == 10 {
				_t571 := p.parse_primitive()
				primitive105 := _t571
				_t572 := &pb.Formula{}
				_t572.FormulaType = &pb.Formula_Primitive{Primitive: primitive105}
				_t570 = _t572
			} else {
				var _t573 *pb.Formula
				if prediction94 == 9 {
					_t574 := p.parse_pragma()
					pragma104 := _t574
					_t575 := &pb.Formula{}
					_t575.FormulaType = &pb.Formula_Pragma{Pragma: pragma104}
					_t573 = _t575
				} else {
					var _t576 *pb.Formula
					if prediction94 == 8 {
						_t577 := p.parse_atom()
						atom103 := _t577
						_t578 := &pb.Formula{}
						_t578.FormulaType = &pb.Formula_Atom{Atom: atom103}
						_t576 = _t578
					} else {
						var _t579 *pb.Formula
						if prediction94 == 7 {
							_t580 := p.parse_ffi()
							ffi102 := _t580
							_t581 := &pb.Formula{}
							_t581.FormulaType = &pb.Formula_Ffi{Ffi: ffi102}
							_t579 = _t581
						} else {
							var _t582 *pb.Formula
							if prediction94 == 6 {
								_t583 := p.parse_not()
								not101 := _t583
								_t584 := &pb.Formula{}
								_t584.FormulaType = &pb.Formula_Not{Not: not101}
								_t582 = _t584
							} else {
								var _t585 *pb.Formula
								if prediction94 == 5 {
									_t586 := p.parse_disjunction()
									disjunction100 := _t586
									_t587 := &pb.Formula{}
									_t587.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction100}
									_t585 = _t587
								} else {
									var _t588 *pb.Formula
									if prediction94 == 4 {
										_t589 := p.parse_conjunction()
										conjunction99 := _t589
										_t590 := &pb.Formula{}
										_t590.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction99}
										_t588 = _t590
									} else {
										var _t591 *pb.Formula
										if prediction94 == 3 {
											_t592 := p.parse_reduce()
											reduce98 := _t592
											_t593 := &pb.Formula{}
											_t593.FormulaType = &pb.Formula_Reduce{Reduce: reduce98}
											_t591 = _t593
										} else {
											var _t594 *pb.Formula
											if prediction94 == 2 {
												_t595 := p.parse_exists()
												exists97 := _t595
												_t596 := &pb.Formula{}
												_t596.FormulaType = &pb.Formula_Exists{Exists: exists97}
												_t594 = _t596
											} else {
												var _t597 *pb.Formula
												if prediction94 == 1 {
													_t598 := p.parse_false()
													false96 := _t598
													_t599 := &pb.Formula{}
													_t599.FormulaType = &pb.Formula_Disjunction{Disjunction: false96}
													_t597 = _t599
												} else {
													var _t600 *pb.Formula
													if prediction94 == 0 {
														_t601 := p.parse_true()
														true95 := _t601
														_t602 := &pb.Formula{}
														_t602.FormulaType = &pb.Formula_Conjunction{Conjunction: true95}
														_t600 = _t602
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t597 = _t600
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
	return _t564
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t603 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t603
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t604 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t604
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t605 := p.parse_bindings()
	bindings108 := _t605
	_t606 := p.parse_formula()
	formula109 := _t606
	p.consumeLiteral(")")
	_t607 := &pb.Abstraction{Vars: listConcat(bindings108[0].([]*pb.Binding), bindings108[1].([]*pb.Binding)), Value: formula109}
	_t608 := &pb.Exists{Body: _t607}
	return _t608
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t609 := p.parse_abstraction()
	abstraction110 := _t609
	_t610 := p.parse_abstraction()
	abstraction_3111 := _t610
	_t611 := p.parse_terms()
	terms112 := _t611
	p.consumeLiteral(")")
	_t612 := &pb.Reduce{Op: abstraction110, Body: abstraction_3111, Terms: terms112}
	return _t612
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs113 := []*pb.Term{}
	cond114 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond114 {
		_t613 := p.parse_term()
		item115 := _t613
		xs113 = append(xs113, item115)
		cond114 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms116 := xs113
	p.consumeLiteral(")")
	return terms116
}

func (p *Parser) parse_term() *pb.Term {
	var _t614 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t614 = 1
	} else {
		var _t615 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t615 = 1
		} else {
			var _t616 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t616 = 1
			} else {
				var _t617 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t617 = 1
				} else {
					var _t618 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t618 = 1
					} else {
						var _t619 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t619 = 0
						} else {
							var _t620 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t620 = 1
							} else {
								var _t621 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t621 = 1
								} else {
									var _t622 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t622 = 1
									} else {
										var _t623 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t623 = 1
										} else {
											var _t624 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t624 = 1
											} else {
												_t624 = -1
											}
											_t623 = _t624
										}
										_t622 = _t623
									}
									_t621 = _t622
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
	prediction117 := _t614
	var _t625 *pb.Term
	if prediction117 == 1 {
		_t626 := p.parse_constant()
		constant119 := _t626
		_t627 := &pb.Term{}
		_t627.TermType = &pb.Term_Constant{Constant: constant119}
		_t625 = _t627
	} else {
		var _t628 *pb.Term
		if prediction117 == 0 {
			_t629 := p.parse_var()
			var118 := _t629
			_t630 := &pb.Term{}
			_t630.TermType = &pb.Term_Var{Var: var118}
			_t628 = _t630
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t625 = _t628
	}
	return _t625
}

func (p *Parser) parse_var() *pb.Var {
	symbol120 := p.consumeTerminal("SYMBOL").Value.AsString()
	_t631 := &pb.Var{Name: symbol120}
	return _t631
}

func (p *Parser) parse_constant() *pb.Value {
	_t632 := p.parse_value()
	value121 := _t632
	return value121
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs122 := []*pb.Formula{}
	cond123 := p.matchLookaheadLiteral("(", 0)
	for cond123 {
		_t633 := p.parse_formula()
		item124 := _t633
		xs122 = append(xs122, item124)
		cond123 = p.matchLookaheadLiteral("(", 0)
	}
	formulas125 := xs122
	p.consumeLiteral(")")
	_t634 := &pb.Conjunction{Args: formulas125}
	return _t634
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs126 := []*pb.Formula{}
	cond127 := p.matchLookaheadLiteral("(", 0)
	for cond127 {
		_t635 := p.parse_formula()
		item128 := _t635
		xs126 = append(xs126, item128)
		cond127 = p.matchLookaheadLiteral("(", 0)
	}
	formulas129 := xs126
	p.consumeLiteral(")")
	_t636 := &pb.Disjunction{Args: formulas129}
	return _t636
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t637 := p.parse_formula()
	formula130 := _t637
	p.consumeLiteral(")")
	_t638 := &pb.Not{Arg: formula130}
	return _t638
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t639 := p.parse_name()
	name131 := _t639
	_t640 := p.parse_ffi_args()
	ffi_args132 := _t640
	_t641 := p.parse_terms()
	terms133 := _t641
	p.consumeLiteral(")")
	_t642 := &pb.FFI{Name: name131, Args: ffi_args132, Terms: terms133}
	return _t642
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
		_t643 := p.parse_abstraction()
		item137 := _t643
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
	_t644 := p.parse_relation_id()
	relation_id139 := _t644
	xs140 := []*pb.Term{}
	cond141 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond141 {
		_t645 := p.parse_term()
		item142 := _t645
		xs140 = append(xs140, item142)
		cond141 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms143 := xs140
	p.consumeLiteral(")")
	_t646 := &pb.Atom{Name: relation_id139, Terms: terms143}
	return _t646
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t647 := p.parse_name()
	name144 := _t647
	xs145 := []*pb.Term{}
	cond146 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond146 {
		_t648 := p.parse_term()
		item147 := _t648
		xs145 = append(xs145, item147)
		cond146 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms148 := xs145
	p.consumeLiteral(")")
	_t649 := &pb.Pragma{Name: name144, Terms: terms148}
	return _t649
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t650 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t651 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t651 = 9
		} else {
			var _t652 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t652 = 4
			} else {
				var _t653 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t653 = 3
				} else {
					var _t654 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t654 = 0
					} else {
						var _t655 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t655 = 2
						} else {
							var _t656 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t656 = 1
							} else {
								var _t657 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t657 = 8
								} else {
									var _t658 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t658 = 6
									} else {
										var _t659 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t659 = 5
										} else {
											var _t660 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t660 = 7
											} else {
												_t660 = -1
											}
											_t659 = _t660
										}
										_t658 = _t659
									}
									_t657 = _t658
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
	} else {
		_t650 = -1
	}
	prediction149 := _t650
	var _t661 *pb.Primitive
	if prediction149 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t662 := p.parse_name()
		name159 := _t662
		xs160 := []*pb.RelTerm{}
		cond161 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond161 {
			_t663 := p.parse_rel_term()
			item162 := _t663
			xs160 = append(xs160, item162)
			cond161 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms163 := xs160
		p.consumeLiteral(")")
		_t664 := &pb.Primitive{Name: name159, Terms: rel_terms163}
		_t661 = _t664
	} else {
		var _t665 *pb.Primitive
		if prediction149 == 8 {
			_t666 := p.parse_divide()
			divide158 := _t666
			_t665 = divide158
		} else {
			var _t667 *pb.Primitive
			if prediction149 == 7 {
				_t668 := p.parse_multiply()
				multiply157 := _t668
				_t667 = multiply157
			} else {
				var _t669 *pb.Primitive
				if prediction149 == 6 {
					_t670 := p.parse_minus()
					minus156 := _t670
					_t669 = minus156
				} else {
					var _t671 *pb.Primitive
					if prediction149 == 5 {
						_t672 := p.parse_add()
						add155 := _t672
						_t671 = add155
					} else {
						var _t673 *pb.Primitive
						if prediction149 == 4 {
							_t674 := p.parse_gt_eq()
							gt_eq154 := _t674
							_t673 = gt_eq154
						} else {
							var _t675 *pb.Primitive
							if prediction149 == 3 {
								_t676 := p.parse_gt()
								gt153 := _t676
								_t675 = gt153
							} else {
								var _t677 *pb.Primitive
								if prediction149 == 2 {
									_t678 := p.parse_lt_eq()
									lt_eq152 := _t678
									_t677 = lt_eq152
								} else {
									var _t679 *pb.Primitive
									if prediction149 == 1 {
										_t680 := p.parse_lt()
										lt151 := _t680
										_t679 = lt151
									} else {
										var _t681 *pb.Primitive
										if prediction149 == 0 {
											_t682 := p.parse_eq()
											eq150 := _t682
											_t681 = eq150
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t679 = _t681
									}
									_t677 = _t679
								}
								_t675 = _t677
							}
							_t673 = _t675
						}
						_t671 = _t673
					}
					_t669 = _t671
				}
				_t667 = _t669
			}
			_t665 = _t667
		}
		_t661 = _t665
	}
	return _t661
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t683 := p.parse_term()
	term164 := _t683
	_t684 := p.parse_term()
	term_3165 := _t684
	p.consumeLiteral(")")
	_t685 := &pb.RelTerm{}
	_t685.RelTermType = &pb.RelTerm_Term{Term: term164}
	_t686 := &pb.RelTerm{}
	_t686.RelTermType = &pb.RelTerm_Term{Term: term_3165}
	_t687 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t685, _t686}}
	return _t687
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t688 := p.parse_term()
	term166 := _t688
	_t689 := p.parse_term()
	term_3167 := _t689
	p.consumeLiteral(")")
	_t690 := &pb.RelTerm{}
	_t690.RelTermType = &pb.RelTerm_Term{Term: term166}
	_t691 := &pb.RelTerm{}
	_t691.RelTermType = &pb.RelTerm_Term{Term: term_3167}
	_t692 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t690, _t691}}
	return _t692
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t693 := p.parse_term()
	term168 := _t693
	_t694 := p.parse_term()
	term_3169 := _t694
	p.consumeLiteral(")")
	_t695 := &pb.RelTerm{}
	_t695.RelTermType = &pb.RelTerm_Term{Term: term168}
	_t696 := &pb.RelTerm{}
	_t696.RelTermType = &pb.RelTerm_Term{Term: term_3169}
	_t697 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t695, _t696}}
	return _t697
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t698 := p.parse_term()
	term170 := _t698
	_t699 := p.parse_term()
	term_3171 := _t699
	p.consumeLiteral(")")
	_t700 := &pb.RelTerm{}
	_t700.RelTermType = &pb.RelTerm_Term{Term: term170}
	_t701 := &pb.RelTerm{}
	_t701.RelTermType = &pb.RelTerm_Term{Term: term_3171}
	_t702 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t700, _t701}}
	return _t702
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t703 := p.parse_term()
	term172 := _t703
	_t704 := p.parse_term()
	term_3173 := _t704
	p.consumeLiteral(")")
	_t705 := &pb.RelTerm{}
	_t705.RelTermType = &pb.RelTerm_Term{Term: term172}
	_t706 := &pb.RelTerm{}
	_t706.RelTermType = &pb.RelTerm_Term{Term: term_3173}
	_t707 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t705, _t706}}
	return _t707
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t708 := p.parse_term()
	term174 := _t708
	_t709 := p.parse_term()
	term_3175 := _t709
	_t710 := p.parse_term()
	term_4176 := _t710
	p.consumeLiteral(")")
	_t711 := &pb.RelTerm{}
	_t711.RelTermType = &pb.RelTerm_Term{Term: term174}
	_t712 := &pb.RelTerm{}
	_t712.RelTermType = &pb.RelTerm_Term{Term: term_3175}
	_t713 := &pb.RelTerm{}
	_t713.RelTermType = &pb.RelTerm_Term{Term: term_4176}
	_t714 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t711, _t712, _t713}}
	return _t714
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t715 := p.parse_term()
	term177 := _t715
	_t716 := p.parse_term()
	term_3178 := _t716
	_t717 := p.parse_term()
	term_4179 := _t717
	p.consumeLiteral(")")
	_t718 := &pb.RelTerm{}
	_t718.RelTermType = &pb.RelTerm_Term{Term: term177}
	_t719 := &pb.RelTerm{}
	_t719.RelTermType = &pb.RelTerm_Term{Term: term_3178}
	_t720 := &pb.RelTerm{}
	_t720.RelTermType = &pb.RelTerm_Term{Term: term_4179}
	_t721 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t718, _t719, _t720}}
	return _t721
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t722 := p.parse_term()
	term180 := _t722
	_t723 := p.parse_term()
	term_3181 := _t723
	_t724 := p.parse_term()
	term_4182 := _t724
	p.consumeLiteral(")")
	_t725 := &pb.RelTerm{}
	_t725.RelTermType = &pb.RelTerm_Term{Term: term180}
	_t726 := &pb.RelTerm{}
	_t726.RelTermType = &pb.RelTerm_Term{Term: term_3181}
	_t727 := &pb.RelTerm{}
	_t727.RelTermType = &pb.RelTerm_Term{Term: term_4182}
	_t728 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t725, _t726, _t727}}
	return _t728
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t729 := p.parse_term()
	term183 := _t729
	_t730 := p.parse_term()
	term_3184 := _t730
	_t731 := p.parse_term()
	term_4185 := _t731
	p.consumeLiteral(")")
	_t732 := &pb.RelTerm{}
	_t732.RelTermType = &pb.RelTerm_Term{Term: term183}
	_t733 := &pb.RelTerm{}
	_t733.RelTermType = &pb.RelTerm_Term{Term: term_3184}
	_t734 := &pb.RelTerm{}
	_t734.RelTermType = &pb.RelTerm_Term{Term: term_4185}
	_t735 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t732, _t733, _t734}}
	return _t735
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t736 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t736 = 1
	} else {
		var _t737 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t737 = 1
		} else {
			var _t738 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t738 = 1
			} else {
				var _t739 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t739 = 1
				} else {
					var _t740 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t740 = 0
					} else {
						var _t741 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t741 = 1
						} else {
							var _t742 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t742 = 1
							} else {
								var _t743 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t743 = 1
								} else {
									var _t744 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t744 = 1
									} else {
										var _t745 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t745 = 1
										} else {
											var _t746 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t746 = 1
											} else {
												var _t747 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t747 = 1
												} else {
													_t747 = -1
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
	prediction186 := _t736
	var _t748 *pb.RelTerm
	if prediction186 == 1 {
		_t749 := p.parse_term()
		term188 := _t749
		_t750 := &pb.RelTerm{}
		_t750.RelTermType = &pb.RelTerm_Term{Term: term188}
		_t748 = _t750
	} else {
		var _t751 *pb.RelTerm
		if prediction186 == 0 {
			_t752 := p.parse_specialized_value()
			specialized_value187 := _t752
			_t753 := &pb.RelTerm{}
			_t753.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value187}
			_t751 = _t753
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t748 = _t751
	}
	return _t748
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t754 := p.parse_value()
	value189 := _t754
	return value189
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t755 := p.parse_name()
	name190 := _t755
	xs191 := []*pb.RelTerm{}
	cond192 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond192 {
		_t756 := p.parse_rel_term()
		item193 := _t756
		xs191 = append(xs191, item193)
		cond192 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms194 := xs191
	p.consumeLiteral(")")
	_t757 := &pb.RelAtom{Name: name190, Terms: rel_terms194}
	return _t757
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t758 := p.parse_term()
	term195 := _t758
	_t759 := p.parse_term()
	term_3196 := _t759
	p.consumeLiteral(")")
	_t760 := &pb.Cast{Input: term195, Result: term_3196}
	return _t760
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs197 := []*pb.Attribute{}
	cond198 := p.matchLookaheadLiteral("(", 0)
	for cond198 {
		_t761 := p.parse_attribute()
		item199 := _t761
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
	_t762 := p.parse_name()
	name201 := _t762
	xs202 := []*pb.Value{}
	cond203 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond203 {
		_t763 := p.parse_value()
		item204 := _t763
		xs202 = append(xs202, item204)
		cond203 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values205 := xs202
	p.consumeLiteral(")")
	_t764 := &pb.Attribute{Name: name201, Args: values205}
	return _t764
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs206 := []*pb.RelationId{}
	cond207 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond207 {
		_t765 := p.parse_relation_id()
		item208 := _t765
		xs206 = append(xs206, item208)
		cond207 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids209 := xs206
	_t766 := p.parse_script()
	script210 := _t766
	p.consumeLiteral(")")
	_t767 := &pb.Algorithm{Global: relation_ids209, Body: script210}
	return _t767
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs211 := []*pb.Construct{}
	cond212 := p.matchLookaheadLiteral("(", 0)
	for cond212 {
		_t768 := p.parse_construct()
		item213 := _t768
		xs211 = append(xs211, item213)
		cond212 = p.matchLookaheadLiteral("(", 0)
	}
	constructs214 := xs211
	p.consumeLiteral(")")
	_t769 := &pb.Script{Constructs: constructs214}
	return _t769
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t770 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t771 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t771 = 1
		} else {
			var _t772 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t772 = 1
			} else {
				var _t773 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t773 = 1
				} else {
					var _t774 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t774 = 0
					} else {
						var _t775 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t775 = 1
						} else {
							var _t776 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t776 = 1
							} else {
								_t776 = -1
							}
							_t775 = _t776
						}
						_t774 = _t775
					}
					_t773 = _t774
				}
				_t772 = _t773
			}
			_t771 = _t772
		}
		_t770 = _t771
	} else {
		_t770 = -1
	}
	prediction215 := _t770
	var _t777 *pb.Construct
	if prediction215 == 1 {
		_t778 := p.parse_instruction()
		instruction217 := _t778
		_t779 := &pb.Construct{}
		_t779.ConstructType = &pb.Construct_Instruction{Instruction: instruction217}
		_t777 = _t779
	} else {
		var _t780 *pb.Construct
		if prediction215 == 0 {
			_t781 := p.parse_loop()
			loop216 := _t781
			_t782 := &pb.Construct{}
			_t782.ConstructType = &pb.Construct_Loop{Loop: loop216}
			_t780 = _t782
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t777 = _t780
	}
	return _t777
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t783 := p.parse_init()
	init218 := _t783
	_t784 := p.parse_script()
	script219 := _t784
	p.consumeLiteral(")")
	_t785 := &pb.Loop{Init: init218, Body: script219}
	return _t785
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs220 := []*pb.Instruction{}
	cond221 := p.matchLookaheadLiteral("(", 0)
	for cond221 {
		_t786 := p.parse_instruction()
		item222 := _t786
		xs220 = append(xs220, item222)
		cond221 = p.matchLookaheadLiteral("(", 0)
	}
	instructions223 := xs220
	p.consumeLiteral(")")
	return instructions223
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t787 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t788 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t788 = 1
		} else {
			var _t789 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t789 = 4
			} else {
				var _t790 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t790 = 3
				} else {
					var _t791 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t791 = 2
					} else {
						var _t792 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t792 = 0
						} else {
							_t792 = -1
						}
						_t791 = _t792
					}
					_t790 = _t791
				}
				_t789 = _t790
			}
			_t788 = _t789
		}
		_t787 = _t788
	} else {
		_t787 = -1
	}
	prediction224 := _t787
	var _t793 *pb.Instruction
	if prediction224 == 4 {
		_t794 := p.parse_monus_def()
		monus_def229 := _t794
		_t795 := &pb.Instruction{}
		_t795.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def229}
		_t793 = _t795
	} else {
		var _t796 *pb.Instruction
		if prediction224 == 3 {
			_t797 := p.parse_monoid_def()
			monoid_def228 := _t797
			_t798 := &pb.Instruction{}
			_t798.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def228}
			_t796 = _t798
		} else {
			var _t799 *pb.Instruction
			if prediction224 == 2 {
				_t800 := p.parse_break()
				break227 := _t800
				_t801 := &pb.Instruction{}
				_t801.InstrType = &pb.Instruction_Break{Break: break227}
				_t799 = _t801
			} else {
				var _t802 *pb.Instruction
				if prediction224 == 1 {
					_t803 := p.parse_upsert()
					upsert226 := _t803
					_t804 := &pb.Instruction{}
					_t804.InstrType = &pb.Instruction_Upsert{Upsert: upsert226}
					_t802 = _t804
				} else {
					var _t805 *pb.Instruction
					if prediction224 == 0 {
						_t806 := p.parse_assign()
						assign225 := _t806
						_t807 := &pb.Instruction{}
						_t807.InstrType = &pb.Instruction_Assign{Assign: assign225}
						_t805 = _t807
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t802 = _t805
				}
				_t799 = _t802
			}
			_t796 = _t799
		}
		_t793 = _t796
	}
	return _t793
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t808 := p.parse_relation_id()
	relation_id230 := _t808
	_t809 := p.parse_abstraction()
	abstraction231 := _t809
	var _t810 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t811 := p.parse_attrs()
		_t810 = _t811
	}
	attrs232 := _t810
	p.consumeLiteral(")")
	_t812 := attrs232
	if attrs232 == nil {
		_t812 = []*pb.Attribute{}
	}
	_t813 := &pb.Assign{Name: relation_id230, Body: abstraction231, Attrs: _t812}
	return _t813
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t814 := p.parse_relation_id()
	relation_id233 := _t814
	_t815 := p.parse_abstraction_with_arity()
	abstraction_with_arity234 := _t815
	var _t816 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t817 := p.parse_attrs()
		_t816 = _t817
	}
	attrs235 := _t816
	p.consumeLiteral(")")
	_t818 := attrs235
	if attrs235 == nil {
		_t818 = []*pb.Attribute{}
	}
	_t819 := &pb.Upsert{Name: relation_id233, Body: abstraction_with_arity234[0].(*pb.Abstraction), Attrs: _t818, ValueArity: abstraction_with_arity234[1].(int64)}
	return _t819
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t820 := p.parse_bindings()
	bindings236 := _t820
	_t821 := p.parse_formula()
	formula237 := _t821
	p.consumeLiteral(")")
	_t822 := &pb.Abstraction{Vars: listConcat(bindings236[0].([]*pb.Binding), bindings236[1].([]*pb.Binding)), Value: formula237}
	return []interface{}{_t822, int64(len(bindings236[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t823 := p.parse_relation_id()
	relation_id238 := _t823
	_t824 := p.parse_abstraction()
	abstraction239 := _t824
	var _t825 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t826 := p.parse_attrs()
		_t825 = _t826
	}
	attrs240 := _t825
	p.consumeLiteral(")")
	_t827 := attrs240
	if attrs240 == nil {
		_t827 = []*pb.Attribute{}
	}
	_t828 := &pb.Break{Name: relation_id238, Body: abstraction239, Attrs: _t827}
	return _t828
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t829 := p.parse_monoid()
	monoid241 := _t829
	_t830 := p.parse_relation_id()
	relation_id242 := _t830
	_t831 := p.parse_abstraction_with_arity()
	abstraction_with_arity243 := _t831
	var _t832 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t833 := p.parse_attrs()
		_t832 = _t833
	}
	attrs244 := _t832
	p.consumeLiteral(")")
	_t834 := attrs244
	if attrs244 == nil {
		_t834 = []*pb.Attribute{}
	}
	_t835 := &pb.MonoidDef{Monoid: monoid241, Name: relation_id242, Body: abstraction_with_arity243[0].(*pb.Abstraction), Attrs: _t834, ValueArity: abstraction_with_arity243[1].(int64)}
	return _t835
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t836 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t837 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t837 = 3
		} else {
			var _t838 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t838 = 0
			} else {
				var _t839 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t839 = 1
				} else {
					var _t840 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t840 = 2
					} else {
						_t840 = -1
					}
					_t839 = _t840
				}
				_t838 = _t839
			}
			_t837 = _t838
		}
		_t836 = _t837
	} else {
		_t836 = -1
	}
	prediction245 := _t836
	var _t841 *pb.Monoid
	if prediction245 == 3 {
		_t842 := p.parse_sum_monoid()
		sum_monoid249 := _t842
		_t843 := &pb.Monoid{}
		_t843.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid249}
		_t841 = _t843
	} else {
		var _t844 *pb.Monoid
		if prediction245 == 2 {
			_t845 := p.parse_max_monoid()
			max_monoid248 := _t845
			_t846 := &pb.Monoid{}
			_t846.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid248}
			_t844 = _t846
		} else {
			var _t847 *pb.Monoid
			if prediction245 == 1 {
				_t848 := p.parse_min_monoid()
				min_monoid247 := _t848
				_t849 := &pb.Monoid{}
				_t849.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid247}
				_t847 = _t849
			} else {
				var _t850 *pb.Monoid
				if prediction245 == 0 {
					_t851 := p.parse_or_monoid()
					or_monoid246 := _t851
					_t852 := &pb.Monoid{}
					_t852.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid246}
					_t850 = _t852
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t847 = _t850
			}
			_t844 = _t847
		}
		_t841 = _t844
	}
	return _t841
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t853 := &pb.OrMonoid{}
	return _t853
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t854 := p.parse_type()
	type250 := _t854
	p.consumeLiteral(")")
	_t855 := &pb.MinMonoid{Type: type250}
	return _t855
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t856 := p.parse_type()
	type251 := _t856
	p.consumeLiteral(")")
	_t857 := &pb.MaxMonoid{Type: type251}
	return _t857
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t858 := p.parse_type()
	type252 := _t858
	p.consumeLiteral(")")
	_t859 := &pb.SumMonoid{Type: type252}
	return _t859
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t860 := p.parse_monoid()
	monoid253 := _t860
	_t861 := p.parse_relation_id()
	relation_id254 := _t861
	_t862 := p.parse_abstraction_with_arity()
	abstraction_with_arity255 := _t862
	var _t863 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t864 := p.parse_attrs()
		_t863 = _t864
	}
	attrs256 := _t863
	p.consumeLiteral(")")
	_t865 := attrs256
	if attrs256 == nil {
		_t865 = []*pb.Attribute{}
	}
	_t866 := &pb.MonusDef{Monoid: monoid253, Name: relation_id254, Body: abstraction_with_arity255[0].(*pb.Abstraction), Attrs: _t865, ValueArity: abstraction_with_arity255[1].(int64)}
	return _t866
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t867 := p.parse_relation_id()
	relation_id257 := _t867
	_t868 := p.parse_abstraction()
	abstraction258 := _t868
	_t869 := p.parse_functional_dependency_keys()
	functional_dependency_keys259 := _t869
	_t870 := p.parse_functional_dependency_values()
	functional_dependency_values260 := _t870
	p.consumeLiteral(")")
	_t871 := &pb.FunctionalDependency{Guard: abstraction258, Keys: functional_dependency_keys259, Values: functional_dependency_values260}
	_t872 := &pb.Constraint{Name: relation_id257}
	_t872.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t871}
	return _t872
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs261 := []*pb.Var{}
	cond262 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond262 {
		_t873 := p.parse_var()
		item263 := _t873
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
		_t874 := p.parse_var()
		item267 := _t874
		xs265 = append(xs265, item267)
		cond266 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars268 := xs265
	p.consumeLiteral(")")
	return vars268
}

func (p *Parser) parse_data() *pb.Data {
	var _t875 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t876 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t876 = 0
		} else {
			var _t877 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t877 = 2
			} else {
				var _t878 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t878 = 1
				} else {
					_t878 = -1
				}
				_t877 = _t878
			}
			_t876 = _t877
		}
		_t875 = _t876
	} else {
		_t875 = -1
	}
	prediction269 := _t875
	var _t879 *pb.Data
	if prediction269 == 2 {
		_t880 := p.parse_csv_data()
		csv_data272 := _t880
		_t881 := &pb.Data{}
		_t881.DataType = &pb.Data_CsvData{CsvData: csv_data272}
		_t879 = _t881
	} else {
		var _t882 *pb.Data
		if prediction269 == 1 {
			_t883 := p.parse_betree_relation()
			betree_relation271 := _t883
			_t884 := &pb.Data{}
			_t884.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation271}
			_t882 = _t884
		} else {
			var _t885 *pb.Data
			if prediction269 == 0 {
				_t886 := p.parse_rel_edb()
				rel_edb270 := _t886
				_t887 := &pb.Data{}
				_t887.DataType = &pb.Data_RelEdb{RelEdb: rel_edb270}
				_t885 = _t887
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t882 = _t885
		}
		_t879 = _t882
	}
	return _t879
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t888 := p.parse_relation_id()
	relation_id273 := _t888
	_t889 := p.parse_rel_edb_path()
	rel_edb_path274 := _t889
	_t890 := p.parse_rel_edb_types()
	rel_edb_types275 := _t890
	p.consumeLiteral(")")
	_t891 := &pb.RelEDB{TargetId: relation_id273, Path: rel_edb_path274, Types: rel_edb_types275}
	return _t891
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
		_t892 := p.parse_type()
		item282 := _t892
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
	_t893 := p.parse_relation_id()
	relation_id284 := _t893
	_t894 := p.parse_betree_info()
	betree_info285 := _t894
	p.consumeLiteral(")")
	_t895 := &pb.BeTreeRelation{Name: relation_id284, RelationInfo: betree_info285}
	return _t895
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t896 := p.parse_betree_info_key_types()
	betree_info_key_types286 := _t896
	_t897 := p.parse_betree_info_value_types()
	betree_info_value_types287 := _t897
	_t898 := p.parse_config_dict()
	config_dict288 := _t898
	p.consumeLiteral(")")
	_t899 := p.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
	return _t899
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs289 := []*pb.Type{}
	cond290 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond290 {
		_t900 := p.parse_type()
		item291 := _t900
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
		_t901 := p.parse_type()
		item295 := _t901
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
	_t902 := p.parse_csvlocator()
	csvlocator297 := _t902
	_t903 := p.parse_csv_config()
	csv_config298 := _t903
	_t904 := p.parse_csv_columns()
	csv_columns299 := _t904
	_t905 := p.parse_csv_asof()
	csv_asof300 := _t905
	p.consumeLiteral(")")
	_t906 := &pb.CSVData{Locator: csvlocator297, Config: csv_config298, Columns: csv_columns299, Asof: csv_asof300}
	return _t906
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t907 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t908 := p.parse_csv_locator_paths()
		_t907 = _t908
	}
	csv_locator_paths301 := _t907
	var _t909 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t910 := p.parse_csv_locator_inline_data()
		_t909 = ptr(_t910)
	}
	csv_locator_inline_data302 := _t909
	p.consumeLiteral(")")
	_t911 := csv_locator_paths301
	if csv_locator_paths301 == nil {
		_t911 = []string{}
	}
	_t912 := &pb.CSVLocator{Paths: _t911, InlineData: []byte(deref(csv_locator_inline_data302, ""))}
	return _t912
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
	_t913 := p.parse_config_dict()
	config_dict308 := _t913
	p.consumeLiteral(")")
	_t914 := p.construct_csv_config(config_dict308)
	return _t914
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs309 := []*pb.CSVColumn{}
	cond310 := p.matchLookaheadLiteral("(", 0)
	for cond310 {
		_t915 := p.parse_csv_column()
		item311 := _t915
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
	_t916 := p.parse_relation_id()
	relation_id314 := _t916
	p.consumeLiteral("[")
	xs315 := []*pb.Type{}
	cond316 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond316 {
		_t917 := p.parse_type()
		item317 := _t917
		xs315 = append(xs315, item317)
		cond316 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types318 := xs315
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t918 := &pb.CSVColumn{ColumnName: string313, TargetId: relation_id314, Types: types318}
	return _t918
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
	_t919 := p.parse_fragment_id()
	fragment_id320 := _t919
	p.consumeLiteral(")")
	_t920 := &pb.Undefine{FragmentId: fragment_id320}
	return _t920
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs321 := []*pb.RelationId{}
	cond322 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond322 {
		_t921 := p.parse_relation_id()
		item323 := _t921
		xs321 = append(xs321, item323)
		cond322 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids324 := xs321
	p.consumeLiteral(")")
	_t922 := &pb.Context{Relations: relation_ids324}
	return _t922
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs325 := []*pb.Read{}
	cond326 := p.matchLookaheadLiteral("(", 0)
	for cond326 {
		_t923 := p.parse_read()
		item327 := _t923
		xs325 = append(xs325, item327)
		cond326 = p.matchLookaheadLiteral("(", 0)
	}
	reads328 := xs325
	p.consumeLiteral(")")
	return reads328
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
	prediction329 := _t924
	var _t930 *pb.Read
	if prediction329 == 4 {
		_t931 := p.parse_export()
		export334 := _t931
		_t932 := &pb.Read{}
		_t932.ReadType = &pb.Read_Export{Export: export334}
		_t930 = _t932
	} else {
		var _t933 *pb.Read
		if prediction329 == 3 {
			_t934 := p.parse_abort()
			abort333 := _t934
			_t935 := &pb.Read{}
			_t935.ReadType = &pb.Read_Abort{Abort: abort333}
			_t933 = _t935
		} else {
			var _t936 *pb.Read
			if prediction329 == 2 {
				_t937 := p.parse_what_if()
				what_if332 := _t937
				_t938 := &pb.Read{}
				_t938.ReadType = &pb.Read_WhatIf{WhatIf: what_if332}
				_t936 = _t938
			} else {
				var _t939 *pb.Read
				if prediction329 == 1 {
					_t940 := p.parse_output()
					output331 := _t940
					_t941 := &pb.Read{}
					_t941.ReadType = &pb.Read_Output{Output: output331}
					_t939 = _t941
				} else {
					var _t942 *pb.Read
					if prediction329 == 0 {
						_t943 := p.parse_demand()
						demand330 := _t943
						_t944 := &pb.Read{}
						_t944.ReadType = &pb.Read_Demand{Demand: demand330}
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
	relation_id335 := _t945
	p.consumeLiteral(")")
	_t946 := &pb.Demand{RelationId: relation_id335}
	return _t946
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t947 := p.parse_name()
	name336 := _t947
	_t948 := p.parse_relation_id()
	relation_id337 := _t948
	p.consumeLiteral(")")
	_t949 := &pb.Output{Name: name336, RelationId: relation_id337}
	return _t949
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t950 := p.parse_name()
	name338 := _t950
	_t951 := p.parse_epoch()
	epoch339 := _t951
	p.consumeLiteral(")")
	_t952 := &pb.WhatIf{Branch: name338, Epoch: epoch339}
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
	name340 := _t953
	_t955 := p.parse_relation_id()
	relation_id341 := _t955
	p.consumeLiteral(")")
	_t956 := &pb.Abort{Name: deref(name340, "abort"), RelationId: relation_id341}
	return _t956
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t957 := p.parse_export_csv_config()
	export_csv_config342 := _t957
	p.consumeLiteral(")")
	_t958 := &pb.Export{}
	_t958.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config342}
	return _t958
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	var _t959 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t960 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t960 = 0
		} else {
			var _t961 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t961 = 1
			} else {
				_t961 = -1
			}
			_t960 = _t961
		}
		_t959 = _t960
	} else {
		_t959 = -1
	}
	prediction343 := _t959
	var _t962 *pb.ExportCSVConfig
	if prediction343 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t963 := p.parse_export_csv_path()
		export_csv_path347 := _t963
		_t964 := p.parse_export_csv_columns()
		export_csv_columns348 := _t964
		_t965 := p.parse_config_dict()
		config_dict349 := _t965
		p.consumeLiteral(")")
		_t966 := p.construct_export_csv_config(export_csv_path347, export_csv_columns348, config_dict349)
		_t962 = _t966
	} else {
		var _t967 *pb.ExportCSVConfig
		if prediction343 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t968 := p.parse_export_csv_path()
			export_csv_path344 := _t968
			_t969 := p.parse_export_csv_source()
			export_csv_source345 := _t969
			_t970 := p.parse_csv_config()
			csv_config346 := _t970
			p.consumeLiteral(")")
			_t971 := p.construct_export_csv_config_with_source(export_csv_path344, export_csv_source345, csv_config346)
			_t967 = _t971
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t962 = _t967
	}
	return _t962
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string350 := p.consumeTerminal("STRING").Value.AsString()
	p.consumeLiteral(")")
	return string350
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	var _t972 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t973 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t973 = 1
		} else {
			var _t974 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t974 = 0
			} else {
				_t974 = -1
			}
			_t973 = _t974
		}
		_t972 = _t973
	} else {
		_t972 = -1
	}
	prediction351 := _t972
	var _t975 *pb.ExportCSVSource
	if prediction351 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t976 := p.parse_relation_id()
		relation_id356 := _t976
		p.consumeLiteral(")")
		_t977 := &pb.ExportCSVSource{}
		_t977.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id356}
		_t975 = _t977
	} else {
		var _t978 *pb.ExportCSVSource
		if prediction351 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs352 := []*pb.ExportCSVColumn{}
			cond353 := p.matchLookaheadLiteral("(", 0)
			for cond353 {
				_t979 := p.parse_export_csv_column()
				item354 := _t979
				xs352 = append(xs352, item354)
				cond353 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns355 := xs352
			p.consumeLiteral(")")
			_t980 := &pb.ExportCSVColumns{Columns: export_csv_columns355}
			_t981 := &pb.ExportCSVSource{}
			_t981.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t980}
			_t978 = _t981
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t975 = _t978
	}
	return _t975
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string357 := p.consumeTerminal("STRING").Value.AsString()
	_t982 := p.parse_relation_id()
	relation_id358 := _t982
	p.consumeLiteral(")")
	_t983 := &pb.ExportCSVColumn{ColumnName: string357, ColumnData: relation_id358}
	return _t983
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs359 := []*pb.ExportCSVColumn{}
	cond360 := p.matchLookaheadLiteral("(", 0)
	for cond360 {
		_t984 := p.parse_export_csv_column()
		item361 := _t984
		xs359 = append(xs359, item361)
		cond360 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns362 := xs359
	p.consumeLiteral(")")
	return export_csv_columns362
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
