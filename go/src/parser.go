// Auto-generated LL(k) recursive-descent parser.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the parser, edit the generator code
// in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
//
// Command: python -m meta.cli ../../proto/relationalai/lqp/v1/logic.proto ../../proto/relationalai/lqp/v1/fragments.proto ../../proto/relationalai/lqp/v1/transactions.proto --parser go

package lqp

import (
	"crypto/sha256"
	"fmt"
	"math"
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
	// Parse as int64 for now (simplified)
	n, _ := strconv.ParseInt(numStr, 10, 64)
	var low, high uint64
	if n >= 0 {
		low = uint64(n)
		high = 0
	} else {
		// Two's complement for negative numbers
		low = uint64(n)
		high = 0xFFFFFFFFFFFFFFFF
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

// Parser is an LL(k) recursive-descent parser
type Parser struct {
	tokens            []Token
	pos               int
	idToDebugInfo     map[string]map[uint64]string
	currentFragmentID []byte
}

// NewParser creates a new parser
func NewParser(tokens []Token) *Parser {
	return &Parser{
		tokens:            tokens,
		pos:               0,
		idToDebugInfo:     make(map[string]map[uint64]string),
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

func (p *Parser) consumeTerminal(expected string) interface{} {
	if !p.matchLookaheadTerminal(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected terminal %s but got %s=`%v` at position %d", expected, token.Type, token.Value, token.Pos)})
	}
	token := p.lookahead(0)
	p.pos++
	return token.Value
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
	// Create RelationId from string hash
	hash := sha256.Sum256([]byte(name))
	var low, high uint64
	for i := 0; i < 8; i++ {
		low |= uint64(hash[i]) << (8 * i)
	}
	for i := 0; i < 8; i++ {
		high |= uint64(hash[8+i]) << (8 * i)
	}
	relationId := &pb.RelationId{IdLow: low, IdHigh: high}

	// Store the mapping for the current fragment if we're inside one
	if p.currentFragmentID != nil {
		key := string(p.currentFragmentID)
		if _, ok := p.idToDebugInfo[key]; !ok {
			p.idToDebugInfo[key] = make(map[uint64]string)
		}
		p.idToDebugInfo[key][relationId.IdLow] = name
	}

	return relationId
}

func (p *Parser) constructFragment(fragmentID *pb.FragmentId, declarations []*pb.Declaration) *pb.Fragment {
	// Get the debug info for this fragment
	key := string(fragmentID.Id)
	debugInfoMap := p.idToDebugInfo[key]

	// Convert to DebugInfo protobuf
	var ids []*pb.RelationId
	var origNames []string
	for idLow, name := range debugInfoMap {
		ids = append(ids, &pb.RelationId{IdLow: idLow, IdHigh: 0})
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

func unwrapOr(val interface{}, defaultVal interface{}) interface{} {
	if val != nil {
		return val
	}
	return defaultVal
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
func ptrInt64(v int64) *int64 { return &v }
func ptrString(v string) *string { return &v }
func ptrBool(v bool) *bool { return &v }

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

// hasProtoField checks if a proto message has a non-nil field by name
// This uses reflection to check for oneOf fields
func hasProtoField(msg interface{}, fieldName string) bool {
	if msg == nil {
		return false
	}
	// For oneOf fields in Go protobuf, the getter returns nil if not set
	// We use reflection to call the getter method
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

func (p *Parser) _try_extract_value_int64(value *pb.Value) int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	return 0
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return value.GetFloatValue()
	}
	return 0.0
}

func (p *Parser) _try_extract_value_string(value *pb.Value) string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	return ""
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
	_t1073 := p._extract_value_int64(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1073
	_t1074 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1074
	_t1075 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1075
	_t1076 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1076
	_t1077 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1077
	_t1078 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1078
	_t1079 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1079
	_t1080 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1080
	_t1081 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1081
	_t1082 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1082
	_t1083 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1083
	_t1084 := &pb.CSVConfig{HeaderRow: int32(header_row), Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1084
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1085 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1085
	_t1086 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1086
	_t1087 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1087
	_t1088 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1088
	_t1089 := &pb.BeTreeConfig{Epsilon: epsilon, MaxPivots: max_pivots, MaxDeltas: max_deltas, MaxLeaf: max_leaf}
	storage_config := _t1089
	_t1090 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1090
	_t1091 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1091
	_t1092 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1092
	_t1093 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1093
	_t1094 := &pb.BeTreeLocator{ElementCount: element_count, TreeHeight: tree_height}
	if root_pageid != nil {
		_t1094.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else if inline_data != nil {
		_t1094.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1094
	_t1095 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1095
}

func (p *Parser) construct_configure(config_dict [][]interface{}) *pb.Configure {
	config := dictFromList(config_dict)
	maintenance_level_val := dictGetValue(config, "ivm.maintenance_level")
	var maintenance_level string
	var _t1096 interface{}
	if (maintenance_level_val != nil && hasProtoField(maintenance_level_val, "string_value")) {
		var _t1097 interface{}
		if maintenance_level_val.GetStringValue() == "off" {
			maintenance_level = "MAINTENANCE_LEVEL_OFF"
			_t1097 = nil
		} else {
			var _t1098 interface{}
			if maintenance_level_val.GetStringValue() == "auto" {
				maintenance_level = "MAINTENANCE_LEVEL_AUTO"
				_t1098 = nil
			} else {
				var _t1099 interface{}
				if maintenance_level_val.GetStringValue() == "all" {
					maintenance_level = "MAINTENANCE_LEVEL_ALL"
					_t1099 = nil
				} else {
					maintenance_level = "MAINTENANCE_LEVEL_OFF"
					_t1099 = nil
				}
				_t1098 = _t1099
			}
			_t1097 = _t1098
		}
		_t1096 = _t1097
	} else {
		maintenance_level = "MAINTENANCE_LEVEL_OFF"
		_t1096 = nil
	}
	_t1100 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1100
	_t1101 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1101
	_t1102 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1102
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1103 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1103
	_t1104 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1104
	_t1105 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1105
	_t1106 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1106
	_t1107 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1107
	_t1108 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1108
	_t1109 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1109
	_t1110 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptrInt64(partition_size), Compression: ptrString(compression), SyntaxHeaderRow: ptrBool(syntax_header_row), SyntaxMissingString: ptrString(syntax_missing_string), SyntaxDelim: ptrString(syntax_delim), SyntaxQuotechar: ptrString(syntax_quotechar), SyntaxEscapechar: ptrString(syntax_escapechar)}
	return _t1110
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t354 interface{}
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t355 := p.parse_configure()
		_t354 = _t355
	} else {
		_t354 = nil
	}
	configure0 := _t354
	var _t357 interface{}
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t358 := p.parse_sync()
		_t357 = _t358
	} else {
		_t357 = nil
	}
	sync1 := _t357
	xs2 := []*pb.Epoch{}
	cond3 := p.matchLookaheadLiteral("(", 0)
	for cond3 {
		_t359 := p.parse_epoch()
		item4 := _t359
		xs2 = listConcat(xs2, []*pb.Epoch{item4})
		cond3 = p.matchLookaheadLiteral("(", 0)
	}
	epochs5 := xs2
	p.consumeLiteral(")")
	_t360 := p.construct_configure([][]interface{}{})
	_t361 := &pb.Transaction{Epochs: epochs5, Configure: unwrapOr(configure0, _t360), Sync: sync1}
	return _t361
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t362 := p.parse_config_dict()
	config_dict6 := _t362
	p.consumeLiteral(")")
	_t363 := p.construct_configure(config_dict6)
	return _t363
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs7 := [][]interface{}{}
	cond8 := p.matchLookaheadLiteral(":", 0)
	for cond8 {
		_t364 := p.parse_config_key_value()
		item9 := _t364
		xs7 = listConcat(xs7, [][]interface{}{item9})
		cond8 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values10 := xs7
	p.consumeLiteral("}")
	return config_key_values10
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol11 := p.consumeTerminal("SYMBOL")
	_t365 := p.parse_value()
	value12 := _t365
	return []interface{}{{symbol11, value12}}
}

func (p *Parser) parse_value() *pb.Value {
	var _t366 interface{}
	if p.matchLookaheadLiteral("true", 0) {
		_t366 = 9
	} else {
		var _t367 interface{}
		if p.matchLookaheadLiteral("missing", 0) {
			_t367 = 8
		} else {
			var _t368 interface{}
			if p.matchLookaheadLiteral("false", 0) {
				_t368 = 9
			} else {
				var _t369 interface{}
				if p.matchLookaheadLiteral("(", 0) {
					var _t371 interface{}
					if p.matchLookaheadLiteral("datetime", 1) {
						_t371 = 1
					} else {
						var _t372 interface{}
						if p.matchLookaheadLiteral("date", 1) {
							_t372 = 0
						} else {
							_t372 = -1
						}
						_t371 = _t372
					}
					_t369 = _t371
				} else {
					var _t373 interface{}
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t373 = 5
					} else {
						var _t374 interface{}
						if p.matchLookaheadTerminal("STRING", 0) {
							_t374 = 2
						} else {
							var _t375 interface{}
							if p.matchLookaheadTerminal("INT128", 0) {
								_t375 = 6
							} else {
								var _t376 interface{}
								if p.matchLookaheadTerminal("INT", 0) {
									_t376 = 3
								} else {
									var _t377 interface{}
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t377 = 4
									} else {
										var _t378 interface{}
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t378 = 7
										} else {
											_t378 = -1
										}
										_t377 = _t378
									}
									_t376 = _t377
								}
								_t375 = _t376
							}
							_t374 = _t375
						}
						_t373 = _t374
					}
					_t369 = _t373
				}
				_t368 = _t369
			}
			_t367 = _t368
		}
		_t366 = _t367
	}
	prediction13 := _t366
	var _t379 interface{}
	if prediction13 == 9 {
		_t380 := p.parse_boolean_value()
		boolean_value22 := _t380
		_t381 := &pb.Value{}
		if boolean_value22 != nil {
			_t381.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value22}
		}
		_t379 = _t381
	} else {
		var _t382 interface{}
		if prediction13 == 8 {
			p.consumeLiteral("missing")
			_t383 := &pb.MissingValue{}
			_t384 := &pb.Value{}
			if _t383 != nil {
				_t384.Value = &pb.Value_MissingValue{MissingValue: _t383}
			}
			_t382 = _t384
		} else {
			var _t385 interface{}
			if prediction13 == 7 {
				decimal21 := p.consumeTerminal("DECIMAL")
				_t386 := &pb.Value{}
				if decimal21 != nil {
					_t386.Value = &pb.Value_DecimalValue{DecimalValue: decimal21}
				}
				_t385 = _t386
			} else {
				var _t387 interface{}
				if prediction13 == 6 {
					int12820 := p.consumeTerminal("INT128")
					_t388 := &pb.Value{}
					if int12820 != nil {
						_t388.Value = &pb.Value_Int128Value{Int128Value: int12820}
					}
					_t387 = _t388
				} else {
					var _t389 interface{}
					if prediction13 == 5 {
						uint12819 := p.consumeTerminal("UINT128")
						_t390 := &pb.Value{}
						if uint12819 != nil {
							_t390.Value = &pb.Value_Uint128Value{Uint128Value: uint12819}
						}
						_t389 = _t390
					} else {
						var _t391 interface{}
						if prediction13 == 4 {
							float18 := p.consumeTerminal("FLOAT")
							_t392 := &pb.Value{}
							if float18 != nil {
								_t392.Value = &pb.Value_FloatValue{FloatValue: float18}
							}
							_t391 = _t392
						} else {
							var _t393 interface{}
							if prediction13 == 3 {
								int17 := p.consumeTerminal("INT")
								_t394 := &pb.Value{}
								if int17 != nil {
									_t394.Value = &pb.Value_IntValue{IntValue: int17}
								}
								_t393 = _t394
							} else {
								var _t395 interface{}
								if prediction13 == 2 {
									string16 := p.consumeTerminal("STRING")
									_t396 := &pb.Value{}
									if string16 != nil {
										_t396.Value = &pb.Value_StringValue{StringValue: string16}
									}
									_t395 = _t396
								} else {
									var _t397 interface{}
									if prediction13 == 1 {
										_t398 := p.parse_datetime()
										datetime15 := _t398
										_t399 := &pb.Value{}
										if datetime15 != nil {
											_t399.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime15}
										}
										_t397 = _t399
									} else {
										var _t400 interface{}
										if prediction13 == 0 {
											_t401 := p.parse_date()
											date14 := _t401
											_t402 := &pb.Value{}
											if date14 != nil {
												_t402.Value = &pb.Value_DateValue{DateValue: date14}
											}
											_t400 = _t402
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t397 = _t400
									}
									_t395 = _t397
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
			_t382 = _t385
		}
		_t379 = _t382
	}
	return _t379
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int23 := p.consumeTerminal("INT")
	int_324 := p.consumeTerminal("INT")
	int_425 := p.consumeTerminal("INT")
	p.consumeLiteral(")")
	_t403 := &pb.DateValue{Year: int32(int23), Month: int32(int_324), Day: int32(int_425)}
	return _t403
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int26 := p.consumeTerminal("INT")
	int_327 := p.consumeTerminal("INT")
	int_428 := p.consumeTerminal("INT")
	int_529 := p.consumeTerminal("INT")
	int_630 := p.consumeTerminal("INT")
	int_731 := p.consumeTerminal("INT")
	var _t404 interface{}
	if p.matchLookaheadTerminal("INT", 0) {
		_t404 = p.consumeTerminal("INT")
	} else {
		_t404 = nil
	}
	int_832 := _t404
	p.consumeLiteral(")")
	_t405 := &pb.DateTimeValue{Year: int32(int26), Month: int32(int_327), Day: int32(int_428), Hour: int32(int_529), Minute: int32(int_630), Second: int32(int_731), Microsecond: int32(unwrapOr(int_832, 0))}
	return _t405
}

func (p *Parser) parse_boolean_value() bool {
	var _t406 interface{}
	if p.matchLookaheadLiteral("true", 0) {
		_t406 = 0
	} else {
		_t406 = (p.matchLookaheadLiteral("false", 0) || -1)
	}
	prediction33 := _t406
	var _t407 interface{}
	if prediction33 == 1 {
		p.consumeLiteral("false")
		_t407 = false
	} else {
		var _t408 interface{}
		if prediction33 == 0 {
			p.consumeLiteral("true")
			_t408 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t407 = _t408
	}
	return _t407
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs34 := []*pb.FragmentId{}
	cond35 := p.matchLookaheadLiteral(":", 0)
	for cond35 {
		_t409 := p.parse_fragment_id()
		item36 := _t409
		xs34 = listConcat(xs34, []*pb.FragmentId{item36})
		cond35 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids37 := xs34
	p.consumeLiteral(")")
	_t410 := &pb.Sync{Fragments: fragment_ids37}
	return _t410
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol38 := p.consumeTerminal("SYMBOL")
	return &pb.FragmentId{Id: []byte(symbol38)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t412 interface{}
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t413 := p.parse_epoch_writes()
		_t412 = _t413
	} else {
		_t412 = nil
	}
	epoch_writes39 := _t412
	var _t415 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t416 := p.parse_epoch_reads()
		_t415 = _t416
	} else {
		_t415 = nil
	}
	epoch_reads40 := _t415
	p.consumeLiteral(")")
	_t417 := &pb.Epoch{Writes: unwrapOr(epoch_writes39, []interface{}{}), Reads: unwrapOr(epoch_reads40, []interface{}{})}
	return _t417
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs41 := []*pb.Write{}
	cond42 := p.matchLookaheadLiteral("(", 0)
	for cond42 {
		_t418 := p.parse_write()
		item43 := _t418
		xs41 = listConcat(xs41, []*pb.Write{item43})
		cond42 = p.matchLookaheadLiteral("(", 0)
	}
	writes44 := xs41
	p.consumeLiteral(")")
	return writes44
}

func (p *Parser) parse_write() *pb.Write {
	var _t419 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t422 interface{}
		if p.matchLookaheadLiteral("undefine", 1) {
			_t422 = 1
		} else {
			var _t423 interface{}
			if p.matchLookaheadLiteral("define", 1) {
				_t423 = 0
			} else {
				var _t424 interface{}
				if p.matchLookaheadLiteral("context", 1) {
					_t424 = 2
				} else {
					_t424 = -1
				}
				_t423 = _t424
			}
			_t422 = _t423
		}
		_t419 = _t422
	} else {
		_t419 = -1
	}
	prediction45 := _t419
	var _t425 interface{}
	if prediction45 == 2 {
		_t426 := p.parse_context()
		context48 := _t426
		_t427 := &pb.Write{}
		if context48 != nil {
			_t427.WriteType = &pb.Write_Context{Context: context48}
		}
		_t425 = _t427
	} else {
		var _t428 interface{}
		if prediction45 == 1 {
			_t429 := p.parse_undefine()
			undefine47 := _t429
			_t430 := &pb.Write{}
			if undefine47 != nil {
				_t430.WriteType = &pb.Write_Undefine{Undefine: undefine47}
			}
			_t428 = _t430
		} else {
			var _t431 interface{}
			if prediction45 == 0 {
				_t432 := p.parse_define()
				define46 := _t432
				_t433 := &pb.Write{}
				if define46 != nil {
					_t433.WriteType = &pb.Write_Define{Define: define46}
				}
				_t431 = _t433
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t428 = _t431
		}
		_t425 = _t428
	}
	return _t425
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t434 := p.parse_fragment()
	fragment49 := _t434
	p.consumeLiteral(")")
	_t435 := &pb.Define{Fragment: fragment49}
	return _t435
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t436 := p.parse_new_fragment_id()
	new_fragment_id50 := _t436
	xs51 := []*pb.Declaration{}
	cond52 := p.matchLookaheadLiteral("(", 0)
	for cond52 {
		_t437 := p.parse_declaration()
		item53 := _t437
		xs51 = listConcat(xs51, []*pb.Declaration{item53})
		cond52 = p.matchLookaheadLiteral("(", 0)
	}
	declarations54 := xs51
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id50, declarations54)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t438 := p.parse_fragment_id()
	fragment_id55 := _t438
	p.startFragment(fragment_id55)
	return fragment_id55
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t439 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t440 interface{}
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t440 = 3
		} else {
			var _t441 interface{}
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t441 = 2
			} else {
				var _t442 interface{}
				if p.matchLookaheadLiteral("def", 1) {
					_t442 = 0
				} else {
					var _t443 interface{}
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t443 = 3
					} else {
						var _t444 interface{}
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t444 = 3
						} else {
							_t444 = (p.matchLookaheadLiteral("algorithm", 1) || -1)
						}
						_t443 = _t444
					}
					_t442 = _t443
				}
				_t441 = _t442
			}
			_t440 = _t441
		}
		_t439 = _t440
	} else {
		_t439 = -1
	}
	prediction56 := _t439
	var _t445 interface{}
	if prediction56 == 3 {
		_t446 := p.parse_data()
		data60 := _t446
		_t447 := &pb.Declaration{}
		if data60 != nil {
			_t447.DeclarationType = &pb.Declaration_Data{Data: data60}
		}
		_t445 = _t447
	} else {
		var _t448 interface{}
		if prediction56 == 2 {
			_t449 := p.parse_constraint()
			constraint59 := _t449
			_t450 := &pb.Declaration{}
			if constraint59 != nil {
				_t450.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint59}
			}
			_t448 = _t450
		} else {
			var _t451 interface{}
			if prediction56 == 1 {
				_t452 := p.parse_algorithm()
				algorithm58 := _t452
				_t453 := &pb.Declaration{}
				if algorithm58 != nil {
					_t453.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm58}
				}
				_t451 = _t453
			} else {
				var _t454 interface{}
				if prediction56 == 0 {
					_t455 := p.parse_def()
					def57 := _t455
					_t456 := &pb.Declaration{}
					if def57 != nil {
						_t456.DeclarationType = &pb.Declaration_Def{Def: def57}
					}
					_t454 = _t456
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t451 = _t454
			}
			_t448 = _t451
		}
		_t445 = _t448
	}
	return _t445
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t457 := p.parse_relation_id()
	relation_id61 := _t457
	_t458 := p.parse_abstraction()
	abstraction62 := _t458
	var _t460 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t461 := p.parse_attrs()
		_t460 = _t461
	} else {
		_t460 = nil
	}
	attrs63 := _t460
	p.consumeLiteral(")")
	_t462 := &pb.Def{Name: relation_id61, Body: abstraction62, Attrs: unwrapOr(attrs63, []interface{}{})}
	return _t462
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t463 interface{}
	if p.matchLookaheadLiteral(":", 0) {
		_t463 = 0
	} else {
		_t463 = (p.matchLookaheadTerminal("INT", 0) || -1)
	}
	prediction64 := _t463
	var _t464 interface{}
	if prediction64 == 1 {
		int66 := p.consumeTerminal("INT")
		_t464 = &pb.RelationId{IdLow: uint64(int66 & 0xFFFFFFFFFFFFFFFF), IdHigh: uint64((int66 >> 64) & 0xFFFFFFFFFFFFFFFF)}
	} else {
		var _t465 interface{}
		if prediction64 == 0 {
			p.consumeLiteral(":")
			symbol65 := p.consumeTerminal("SYMBOL")
			_t465 = p.relationIdFromString(symbol65)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t464 = _t465
	}
	return _t464
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t466 := p.parse_bindings()
	bindings67 := _t466
	_t467 := p.parse_formula()
	formula68 := _t467
	p.consumeLiteral(")")
	_t468 := &pb.Abstraction{Vars: listConcat(bindings67[0], bindings67[1]), Value: formula68}
	return _t468
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs69 := []*pb.Binding{}
	cond70 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond70 {
		_t469 := p.parse_binding()
		item71 := _t469
		xs69 = listConcat(xs69, []*pb.Binding{item71})
		cond70 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings72 := xs69
	var _t471 interface{}
	if p.matchLookaheadLiteral("|", 0) {
		_t472 := p.parse_value_bindings()
		_t471 = _t472
	} else {
		_t471 = nil
	}
	value_bindings73 := _t471
	p.consumeLiteral("]")
	return []interface{}{{bindings72, unwrapOr(value_bindings73, []interface{}{})}}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol74 := p.consumeTerminal("SYMBOL")
	p.consumeLiteral("::")
	_t473 := p.parse_type()
	type75 := _t473
	_t474 := &pb.Var{Name: symbol74}
	_t475 := &pb.Binding{Var: _t474, Type: type75}
	return _t475
}

func (p *Parser) parse_type() *pb.Type {
	var _t476 interface{}
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t476 = 0
	} else {
		var _t477 interface{}
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t477 = 4
		} else {
			var _t486 interface{}
			if p.matchLookaheadLiteral("STRING", 0) {
				_t486 = 1
			} else {
				var _t487 interface{}
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t487 = 8
				} else {
					var _t488 interface{}
					if p.matchLookaheadLiteral("INT128", 0) {
						_t488 = 5
					} else {
						var _t489 interface{}
						if p.matchLookaheadLiteral("INT", 0) {
							_t489 = 2
						} else {
							var _t490 interface{}
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t490 = 3
							} else {
								var _t491 interface{}
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t491 = 7
								} else {
									var _t492 interface{}
									if p.matchLookaheadLiteral("DATE", 0) {
										_t492 = 6
									} else {
										var _t493 interface{}
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t493 = 10
										} else {
											var _t494 interface{}
											if p.matchLookaheadLiteral("(", 0) {
												_t494 = 9
											} else {
												_t494 = -1
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
			_t477 = _t486
		}
		_t476 = _t477
	}
	prediction76 := _t476
	var _t495 interface{}
	if prediction76 == 10 {
		_t496 := p.parse_boolean_type()
		boolean_type87 := _t496
		_t497 := &pb.Type{}
		if boolean_type87 != nil {
			_t497.Type = &pb.Type_BooleanType{BooleanType: boolean_type87}
		}
		_t495 = _t497
	} else {
		var _t498 interface{}
		if prediction76 == 9 {
			_t499 := p.parse_decimal_type()
			decimal_type86 := _t499
			_t500 := &pb.Type{}
			if decimal_type86 != nil {
				_t500.Type = &pb.Type_DecimalType{DecimalType: decimal_type86}
			}
			_t498 = _t500
		} else {
			var _t501 interface{}
			if prediction76 == 8 {
				_t502 := p.parse_missing_type()
				missing_type85 := _t502
				_t503 := &pb.Type{}
				if missing_type85 != nil {
					_t503.Type = &pb.Type_MissingType{MissingType: missing_type85}
				}
				_t501 = _t503
			} else {
				var _t504 interface{}
				if prediction76 == 7 {
					_t505 := p.parse_datetime_type()
					datetime_type84 := _t505
					_t506 := &pb.Type{}
					if datetime_type84 != nil {
						_t506.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type84}
					}
					_t504 = _t506
				} else {
					var _t507 interface{}
					if prediction76 == 6 {
						_t508 := p.parse_date_type()
						date_type83 := _t508
						_t509 := &pb.Type{}
						if date_type83 != nil {
							_t509.Type = &pb.Type_DateType{DateType: date_type83}
						}
						_t507 = _t509
					} else {
						var _t510 interface{}
						if prediction76 == 5 {
							_t511 := p.parse_int128_type()
							int128_type82 := _t511
							_t512 := &pb.Type{}
							if int128_type82 != nil {
								_t512.Type = &pb.Type_Int128Type{Int128Type: int128_type82}
							}
							_t510 = _t512
						} else {
							var _t513 interface{}
							if prediction76 == 4 {
								_t514 := p.parse_uint128_type()
								uint128_type81 := _t514
								_t515 := &pb.Type{}
								if uint128_type81 != nil {
									_t515.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type81}
								}
								_t513 = _t515
							} else {
								var _t516 interface{}
								if prediction76 == 3 {
									_t517 := p.parse_float_type()
									float_type80 := _t517
									_t518 := &pb.Type{}
									if float_type80 != nil {
										_t518.Type = &pb.Type_FloatType{FloatType: float_type80}
									}
									_t516 = _t518
								} else {
									var _t519 interface{}
									if prediction76 == 2 {
										_t520 := p.parse_int_type()
										int_type79 := _t520
										_t521 := &pb.Type{}
										if int_type79 != nil {
											_t521.Type = &pb.Type_IntType{IntType: int_type79}
										}
										_t519 = _t521
									} else {
										var _t522 interface{}
										if prediction76 == 1 {
											_t523 := p.parse_string_type()
											string_type78 := _t523
											_t524 := &pb.Type{}
											if string_type78 != nil {
												_t524.Type = &pb.Type_StringType{StringType: string_type78}
											}
											_t522 = _t524
										} else {
											var _t525 interface{}
											if prediction76 == 0 {
												_t526 := p.parse_unspecified_type()
												unspecified_type77 := _t526
												_t527 := &pb.Type{}
												if unspecified_type77 != nil {
													_t527.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type77}
												}
												_t525 = _t527
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t522 = _t525
										}
										_t519 = _t522
									}
									_t516 = _t519
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
	return _t495
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t528 := &pb.UnspecifiedType{}
	return _t528
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t529 := &pb.StringType{}
	return _t529
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t530 := &pb.IntType{}
	return _t530
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t531 := &pb.FloatType{}
	return _t531
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t532 := &pb.UInt128Type{}
	return _t532
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t533 := &pb.Int128Type{}
	return _t533
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t534 := &pb.DateType{}
	return _t534
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t535 := &pb.DateTimeType{}
	return _t535
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t536 := &pb.MissingType{}
	return _t536
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int88 := p.consumeTerminal("INT")
	int_389 := p.consumeTerminal("INT")
	p.consumeLiteral(")")
	_t537 := &pb.DecimalType{Precision: int32(int88), Scale: int32(int_389)}
	return _t537
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t538 := &pb.BooleanType{}
	return _t538
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs90 := []*pb.Binding{}
	cond91 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond91 {
		_t539 := p.parse_binding()
		item92 := _t539
		xs90 = listConcat(xs90, []*pb.Binding{item92})
		cond91 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings93 := xs90
	return bindings93
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t540 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t541 interface{}
		if p.matchLookaheadLiteral("true", 1) {
			_t541 = 0
		} else {
			var _t542 interface{}
			if p.matchLookaheadLiteral("relatom", 1) {
				_t542 = 11
			} else {
				var _t543 interface{}
				if p.matchLookaheadLiteral("reduce", 1) {
					_t543 = 3
				} else {
					var _t544 interface{}
					if p.matchLookaheadLiteral("primitive", 1) {
						_t544 = 10
					} else {
						var _t545 interface{}
						if p.matchLookaheadLiteral("pragma", 1) {
							_t545 = 9
						} else {
							var _t546 interface{}
							if p.matchLookaheadLiteral("or", 1) {
								_t546 = 5
							} else {
								var _t547 interface{}
								if p.matchLookaheadLiteral("not", 1) {
									_t547 = 6
								} else {
									var _t548 interface{}
									if p.matchLookaheadLiteral("ffi", 1) {
										_t548 = 7
									} else {
										var _t562 interface{}
										if p.matchLookaheadLiteral("false", 1) {
											_t562 = 1
										} else {
											var _t563 interface{}
											if p.matchLookaheadLiteral("exists", 1) {
												_t563 = 2
											} else {
												var _t564 interface{}
												if p.matchLookaheadLiteral("cast", 1) {
													_t564 = 12
												} else {
													var _t565 interface{}
													if p.matchLookaheadLiteral("atom", 1) {
														_t565 = 8
													} else {
														var _t566 interface{}
														if p.matchLookaheadLiteral("and", 1) {
															_t566 = 4
														} else {
															var _t567 interface{}
															if p.matchLookaheadLiteral(">=", 1) {
																_t567 = 10
															} else {
																var _t568 interface{}
																if p.matchLookaheadLiteral(">", 1) {
																	_t568 = 10
																} else {
																	var _t569 interface{}
																	if p.matchLookaheadLiteral("=", 1) {
																		_t569 = 10
																	} else {
																		var _t570 interface{}
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t570 = 10
																		} else {
																			var _t571 interface{}
																			if p.matchLookaheadLiteral("<", 1) {
																				_t571 = 10
																			} else {
																				var _t572 interface{}
																				if p.matchLookaheadLiteral("/", 1) {
																					_t572 = 10
																				} else {
																					var _t573 interface{}
																					if p.matchLookaheadLiteral("-", 1) {
																						_t573 = 10
																					} else {
																						var _t574 interface{}
																						if p.matchLookaheadLiteral("+", 1) {
																							_t574 = 10
																						} else {
																							var _t575 interface{}
																							if p.matchLookaheadLiteral("*", 1) {
																								_t575 = 10
																							} else {
																								_t575 = -1
																							}
																							_t574 = _t575
																						}
																						_t573 = _t574
																					}
																					_t572 = _t573
																				}
																				_t571 = _t572
																			}
																			_t570 = _t571
																		}
																		_t569 = _t570
																	}
																	_t568 = _t569
																}
																_t567 = _t568
															}
															_t566 = _t567
														}
														_t565 = _t566
													}
													_t564 = _t565
												}
												_t563 = _t564
											}
											_t562 = _t563
										}
										_t548 = _t562
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
	} else {
		_t540 = -1
	}
	prediction94 := _t540
	var _t576 interface{}
	if prediction94 == 12 {
		_t577 := p.parse_cast()
		cast107 := _t577
		_t578 := &pb.Formula{}
		if cast107 != nil {
			_t578.FormulaType = &pb.Formula_Cast{Cast: cast107}
		}
		_t576 = _t578
	} else {
		var _t579 interface{}
		if prediction94 == 11 {
			_t580 := p.parse_rel_atom()
			rel_atom106 := _t580
			_t581 := &pb.Formula{}
			if rel_atom106 != nil {
				_t581.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom106}
			}
			_t579 = _t581
		} else {
			var _t582 interface{}
			if prediction94 == 10 {
				_t583 := p.parse_primitive()
				primitive105 := _t583
				_t584 := &pb.Formula{}
				if primitive105 != nil {
					_t584.FormulaType = &pb.Formula_Primitive{Primitive: primitive105}
				}
				_t582 = _t584
			} else {
				var _t585 interface{}
				if prediction94 == 9 {
					_t586 := p.parse_pragma()
					pragma104 := _t586
					_t587 := &pb.Formula{}
					if pragma104 != nil {
						_t587.FormulaType = &pb.Formula_Pragma{Pragma: pragma104}
					}
					_t585 = _t587
				} else {
					var _t588 interface{}
					if prediction94 == 8 {
						_t589 := p.parse_atom()
						atom103 := _t589
						_t590 := &pb.Formula{}
						if atom103 != nil {
							_t590.FormulaType = &pb.Formula_Atom{Atom: atom103}
						}
						_t588 = _t590
					} else {
						var _t591 interface{}
						if prediction94 == 7 {
							_t592 := p.parse_ffi()
							ffi102 := _t592
							_t593 := &pb.Formula{}
							if ffi102 != nil {
								_t593.FormulaType = &pb.Formula_Ffi{Ffi: ffi102}
							}
							_t591 = _t593
						} else {
							var _t594 interface{}
							if prediction94 == 6 {
								_t595 := p.parse_not()
								not101 := _t595
								_t596 := &pb.Formula{}
								if not101 != nil {
									_t596.FormulaType = &pb.Formula_Not{Not: not101}
								}
								_t594 = _t596
							} else {
								var _t597 interface{}
								if prediction94 == 5 {
									_t598 := p.parse_disjunction()
									disjunction100 := _t598
									_t599 := &pb.Formula{}
									if disjunction100 != nil {
										_t599.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction100}
									}
									_t597 = _t599
								} else {
									var _t600 interface{}
									if prediction94 == 4 {
										_t601 := p.parse_conjunction()
										conjunction99 := _t601
										_t602 := &pb.Formula{}
										if conjunction99 != nil {
											_t602.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction99}
										}
										_t600 = _t602
									} else {
										var _t603 interface{}
										if prediction94 == 3 {
											_t604 := p.parse_reduce()
											reduce98 := _t604
											_t605 := &pb.Formula{}
											if reduce98 != nil {
												_t605.FormulaType = &pb.Formula_Reduce{Reduce: reduce98}
											}
											_t603 = _t605
										} else {
											var _t606 interface{}
											if prediction94 == 2 {
												_t607 := p.parse_exists()
												exists97 := _t607
												_t608 := &pb.Formula{}
												if exists97 != nil {
													_t608.FormulaType = &pb.Formula_Exists{Exists: exists97}
												}
												_t606 = _t608
											} else {
												var _t609 interface{}
												if prediction94 == 1 {
													_t610 := p.parse_false()
													false96 := _t610
													_t611 := &pb.Formula{}
													if false96 != nil {
														_t611.FormulaType = &pb.Formula_Disjunction{Disjunction: false96}
													}
													_t609 = _t611
												} else {
													var _t612 interface{}
													if prediction94 == 0 {
														_t613 := p.parse_true()
														true95 := _t613
														_t614 := &pb.Formula{}
														if true95 != nil {
															_t614.FormulaType = &pb.Formula_Conjunction{Conjunction: true95}
														}
														_t612 = _t614
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t609 = _t612
												}
												_t606 = _t609
											}
											_t603 = _t606
										}
										_t600 = _t603
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
	return _t576
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t615 := &pb.Conjunction{Args: []interface{}{}}
	return _t615
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t616 := &pb.Disjunction{Args: []interface{}{}}
	return _t616
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t617 := p.parse_bindings()
	bindings108 := _t617
	_t618 := p.parse_formula()
	formula109 := _t618
	p.consumeLiteral(")")
	_t619 := &pb.Abstraction{Vars: listConcat(bindings108[0], bindings108[1]), Value: formula109}
	_t620 := &pb.Exists{Body: _t619}
	return _t620
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t621 := p.parse_abstraction()
	abstraction110 := _t621
	_t622 := p.parse_abstraction()
	abstraction_3111 := _t622
	_t623 := p.parse_terms()
	terms112 := _t623
	p.consumeLiteral(")")
	_t624 := &pb.Reduce{Op: abstraction110, Body: abstraction_3111, Terms: terms112}
	return _t624
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs113 := []*pb.Term{}
	cond114 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond114 {
		_t625 := p.parse_term()
		item115 := _t625
		xs113 = listConcat(xs113, []*pb.Term{item115})
		cond114 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms116 := xs113
	p.consumeLiteral(")")
	return terms116
}

func (p *Parser) parse_term() *pb.Term {
	var _t657 interface{}
	if p.matchLookaheadLiteral("true", 0) {
		_t657 = 1
	} else {
		var _t673 interface{}
		if p.matchLookaheadLiteral("missing", 0) {
			_t673 = 1
		} else {
			var _t681 interface{}
			if p.matchLookaheadLiteral("false", 0) {
				_t681 = 1
			} else {
				var _t685 interface{}
				if p.matchLookaheadLiteral("(", 0) {
					_t685 = 1
				} else {
					var _t687 interface{}
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t687 = 1
					} else {
						var _t688 interface{}
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t688 = 0
						} else {
							_t688 = (p.matchLookaheadTerminal("STRING", 0) || (p.matchLookaheadTerminal("INT128", 0) || (p.matchLookaheadTerminal("INT", 0) || (p.matchLookaheadTerminal("FLOAT", 0) || (p.matchLookaheadTerminal("DECIMAL", 0) || -1)))))
						}
						_t687 = _t688
					}
					_t685 = _t687
				}
				_t681 = _t685
			}
			_t673 = _t681
		}
		_t657 = _t673
	}
	prediction117 := _t657
	var _t689 interface{}
	if prediction117 == 1 {
		_t690 := p.parse_constant()
		constant119 := _t690
		_t691 := &pb.Term{}
		if constant119 != nil {
			_t691.TermType = &pb.Term_Constant{Constant: constant119}
		}
		_t689 = _t691
	} else {
		var _t692 interface{}
		if prediction117 == 0 {
			_t693 := p.parse_var()
			var118 := _t693
			_t694 := &pb.Term{}
			if var118 != nil {
				_t694.TermType = &pb.Term_Var{Var: var118}
			}
			_t692 = _t694
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t689 = _t692
	}
	return _t689
}

func (p *Parser) parse_var() *pb.Var {
	symbol120 := p.consumeTerminal("SYMBOL")
	_t695 := &pb.Var{Name: symbol120}
	return _t695
}

func (p *Parser) parse_constant() *pb.Value {
	_t696 := p.parse_value()
	value121 := _t696
	return value121
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs122 := []*pb.Formula{}
	cond123 := p.matchLookaheadLiteral("(", 0)
	for cond123 {
		_t697 := p.parse_formula()
		item124 := _t697
		xs122 = listConcat(xs122, []*pb.Formula{item124})
		cond123 = p.matchLookaheadLiteral("(", 0)
	}
	formulas125 := xs122
	p.consumeLiteral(")")
	_t698 := &pb.Conjunction{Args: formulas125}
	return _t698
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs126 := []*pb.Formula{}
	cond127 := p.matchLookaheadLiteral("(", 0)
	for cond127 {
		_t699 := p.parse_formula()
		item128 := _t699
		xs126 = listConcat(xs126, []*pb.Formula{item128})
		cond127 = p.matchLookaheadLiteral("(", 0)
	}
	formulas129 := xs126
	p.consumeLiteral(")")
	_t700 := &pb.Disjunction{Args: formulas129}
	return _t700
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t701 := p.parse_formula()
	formula130 := _t701
	p.consumeLiteral(")")
	_t702 := &pb.Not{Arg: formula130}
	return _t702
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t703 := p.parse_name()
	name131 := _t703
	_t704 := p.parse_ffi_args()
	ffi_args132 := _t704
	_t705 := p.parse_terms()
	terms133 := _t705
	p.consumeLiteral(")")
	_t706 := &pb.FFI{Name: name131, Args: ffi_args132, Terms: terms133}
	return _t706
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol134 := p.consumeTerminal("SYMBOL")
	return symbol134
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs135 := []*pb.Abstraction{}
	cond136 := p.matchLookaheadLiteral("(", 0)
	for cond136 {
		_t707 := p.parse_abstraction()
		item137 := _t707
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
	_t708 := p.parse_relation_id()
	relation_id139 := _t708
	xs140 := []*pb.Term{}
	cond141 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond141 {
		_t709 := p.parse_term()
		item142 := _t709
		xs140 = listConcat(xs140, []*pb.Term{item142})
		cond141 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms143 := xs140
	p.consumeLiteral(")")
	_t710 := &pb.Atom{Name: relation_id139, Terms: terms143}
	return _t710
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t711 := p.parse_name()
	name144 := _t711
	xs145 := []*pb.Term{}
	cond146 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond146 {
		_t712 := p.parse_term()
		item147 := _t712
		xs145 = listConcat(xs145, []*pb.Term{item147})
		cond146 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms148 := xs145
	p.consumeLiteral(")")
	_t713 := &pb.Pragma{Name: name144, Terms: terms148}
	return _t713
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t714 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t715 interface{}
		if p.matchLookaheadLiteral("primitive", 1) {
			_t715 = 9
		} else {
			var _t716 interface{}
			if p.matchLookaheadLiteral(">=", 1) {
				_t716 = 4
			} else {
				var _t717 interface{}
				if p.matchLookaheadLiteral(">", 1) {
					_t717 = 3
				} else {
					var _t718 interface{}
					if p.matchLookaheadLiteral("=", 1) {
						_t718 = 0
					} else {
						var _t719 interface{}
						if p.matchLookaheadLiteral("<=", 1) {
							_t719 = 2
						} else {
							var _t724 interface{}
							if p.matchLookaheadLiteral("<", 1) {
								_t724 = 1
							} else {
								var _t725 interface{}
								if p.matchLookaheadLiteral("/", 1) {
									_t725 = 8
								} else {
									var _t726 interface{}
									if p.matchLookaheadLiteral("-", 1) {
										_t726 = 6
									} else {
										var _t727 interface{}
										if p.matchLookaheadLiteral("+", 1) {
											_t727 = 5
										} else {
											var _t728 interface{}
											if p.matchLookaheadLiteral("*", 1) {
												_t728 = 7
											} else {
												_t728 = -1
											}
											_t727 = _t728
										}
										_t726 = _t727
									}
									_t725 = _t726
								}
								_t724 = _t725
							}
							_t719 = _t724
						}
						_t718 = _t719
					}
					_t717 = _t718
				}
				_t716 = _t717
			}
			_t715 = _t716
		}
		_t714 = _t715
	} else {
		_t714 = -1
	}
	prediction149 := _t714
	var _t729 interface{}
	if prediction149 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t730 := p.parse_name()
		name159 := _t730
		xs160 := []*pb.RelTerm{}
		cond161 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond161 {
			_t731 := p.parse_rel_term()
			item162 := _t731
			xs160 = listConcat(xs160, []*pb.RelTerm{item162})
			cond161 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms163 := xs160
		p.consumeLiteral(")")
		_t732 := &pb.Primitive{Name: name159, Terms: rel_terms163}
		_t729 = _t732
	} else {
		var _t733 interface{}
		if prediction149 == 8 {
			_t734 := p.parse_divide()
			divide158 := _t734
			_t733 = divide158
		} else {
			var _t735 interface{}
			if prediction149 == 7 {
				_t736 := p.parse_multiply()
				multiply157 := _t736
				_t735 = multiply157
			} else {
				var _t737 interface{}
				if prediction149 == 6 {
					_t738 := p.parse_minus()
					minus156 := _t738
					_t737 = minus156
				} else {
					var _t739 interface{}
					if prediction149 == 5 {
						_t740 := p.parse_add()
						add155 := _t740
						_t739 = add155
					} else {
						var _t741 interface{}
						if prediction149 == 4 {
							_t742 := p.parse_gt_eq()
							gt_eq154 := _t742
							_t741 = gt_eq154
						} else {
							var _t743 interface{}
							if prediction149 == 3 {
								_t744 := p.parse_gt()
								gt153 := _t744
								_t743 = gt153
							} else {
								var _t745 interface{}
								if prediction149 == 2 {
									_t746 := p.parse_lt_eq()
									lt_eq152 := _t746
									_t745 = lt_eq152
								} else {
									var _t747 interface{}
									if prediction149 == 1 {
										_t748 := p.parse_lt()
										lt151 := _t748
										_t747 = lt151
									} else {
										var _t749 interface{}
										if prediction149 == 0 {
											_t750 := p.parse_eq()
											eq150 := _t750
											_t749 = eq150
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t747 = _t749
									}
									_t745 = _t747
								}
								_t743 = _t745
							}
							_t741 = _t743
						}
						_t739 = _t741
					}
					_t737 = _t739
				}
				_t735 = _t737
			}
			_t733 = _t735
		}
		_t729 = _t733
	}
	return _t729
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t751 := p.parse_term()
	term164 := _t751
	_t752 := p.parse_term()
	term_3165 := _t752
	p.consumeLiteral(")")
	_t753 := &pb.RelTerm{}
	if term164 != nil {
		_t753.RelTermType = &pb.RelTerm_Term{Term: term164}
	}
	_t754 := &pb.RelTerm{}
	if term_3165 != nil {
		_t754.RelTermType = &pb.RelTerm_Term{Term: term_3165}
	}
	_t755 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t753, _t754}}
	return _t755
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t756 := p.parse_term()
	term166 := _t756
	_t757 := p.parse_term()
	term_3167 := _t757
	p.consumeLiteral(")")
	_t758 := &pb.RelTerm{}
	if term166 != nil {
		_t758.RelTermType = &pb.RelTerm_Term{Term: term166}
	}
	_t759 := &pb.RelTerm{}
	if term_3167 != nil {
		_t759.RelTermType = &pb.RelTerm_Term{Term: term_3167}
	}
	_t760 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t758, _t759}}
	return _t760
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t761 := p.parse_term()
	term168 := _t761
	_t762 := p.parse_term()
	term_3169 := _t762
	p.consumeLiteral(")")
	_t763 := &pb.RelTerm{}
	if term168 != nil {
		_t763.RelTermType = &pb.RelTerm_Term{Term: term168}
	}
	_t764 := &pb.RelTerm{}
	if term_3169 != nil {
		_t764.RelTermType = &pb.RelTerm_Term{Term: term_3169}
	}
	_t765 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t763, _t764}}
	return _t765
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t766 := p.parse_term()
	term170 := _t766
	_t767 := p.parse_term()
	term_3171 := _t767
	p.consumeLiteral(")")
	_t768 := &pb.RelTerm{}
	if term170 != nil {
		_t768.RelTermType = &pb.RelTerm_Term{Term: term170}
	}
	_t769 := &pb.RelTerm{}
	if term_3171 != nil {
		_t769.RelTermType = &pb.RelTerm_Term{Term: term_3171}
	}
	_t770 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t768, _t769}}
	return _t770
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t771 := p.parse_term()
	term172 := _t771
	_t772 := p.parse_term()
	term_3173 := _t772
	p.consumeLiteral(")")
	_t773 := &pb.RelTerm{}
	if term172 != nil {
		_t773.RelTermType = &pb.RelTerm_Term{Term: term172}
	}
	_t774 := &pb.RelTerm{}
	if term_3173 != nil {
		_t774.RelTermType = &pb.RelTerm_Term{Term: term_3173}
	}
	_t775 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t773, _t774}}
	return _t775
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t776 := p.parse_term()
	term174 := _t776
	_t777 := p.parse_term()
	term_3175 := _t777
	_t778 := p.parse_term()
	term_4176 := _t778
	p.consumeLiteral(")")
	_t779 := &pb.RelTerm{}
	if term174 != nil {
		_t779.RelTermType = &pb.RelTerm_Term{Term: term174}
	}
	_t780 := &pb.RelTerm{}
	if term_3175 != nil {
		_t780.RelTermType = &pb.RelTerm_Term{Term: term_3175}
	}
	_t781 := &pb.RelTerm{}
	if term_4176 != nil {
		_t781.RelTermType = &pb.RelTerm_Term{Term: term_4176}
	}
	_t782 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t779, _t780, _t781}}
	return _t782
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t783 := p.parse_term()
	term177 := _t783
	_t784 := p.parse_term()
	term_3178 := _t784
	_t785 := p.parse_term()
	term_4179 := _t785
	p.consumeLiteral(")")
	_t786 := &pb.RelTerm{}
	if term177 != nil {
		_t786.RelTermType = &pb.RelTerm_Term{Term: term177}
	}
	_t787 := &pb.RelTerm{}
	if term_3178 != nil {
		_t787.RelTermType = &pb.RelTerm_Term{Term: term_3178}
	}
	_t788 := &pb.RelTerm{}
	if term_4179 != nil {
		_t788.RelTermType = &pb.RelTerm_Term{Term: term_4179}
	}
	_t789 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t786, _t787, _t788}}
	return _t789
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t790 := p.parse_term()
	term180 := _t790
	_t791 := p.parse_term()
	term_3181 := _t791
	_t792 := p.parse_term()
	term_4182 := _t792
	p.consumeLiteral(")")
	_t793 := &pb.RelTerm{}
	if term180 != nil {
		_t793.RelTermType = &pb.RelTerm_Term{Term: term180}
	}
	_t794 := &pb.RelTerm{}
	if term_3181 != nil {
		_t794.RelTermType = &pb.RelTerm_Term{Term: term_3181}
	}
	_t795 := &pb.RelTerm{}
	if term_4182 != nil {
		_t795.RelTermType = &pb.RelTerm_Term{Term: term_4182}
	}
	_t796 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t793, _t794, _t795}}
	return _t796
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t797 := p.parse_term()
	term183 := _t797
	_t798 := p.parse_term()
	term_3184 := _t798
	_t799 := p.parse_term()
	term_4185 := _t799
	p.consumeLiteral(")")
	_t800 := &pb.RelTerm{}
	if term183 != nil {
		_t800.RelTermType = &pb.RelTerm_Term{Term: term183}
	}
	_t801 := &pb.RelTerm{}
	if term_3184 != nil {
		_t801.RelTermType = &pb.RelTerm_Term{Term: term_3184}
	}
	_t802 := &pb.RelTerm{}
	if term_4185 != nil {
		_t802.RelTermType = &pb.RelTerm_Term{Term: term_4185}
	}
	_t803 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t800, _t801, _t802}}
	return _t803
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t819 interface{}
	if p.matchLookaheadLiteral("true", 0) {
		_t819 = 1
	} else {
		var _t827 interface{}
		if p.matchLookaheadLiteral("missing", 0) {
			_t827 = 1
		} else {
			var _t831 interface{}
			if p.matchLookaheadLiteral("false", 0) {
				_t831 = 1
			} else {
				var _t833 interface{}
				if p.matchLookaheadLiteral("(", 0) {
					_t833 = 1
				} else {
					var _t834 interface{}
					if p.matchLookaheadLiteral("#", 0) {
						_t834 = 0
					} else {
						_t834 = (p.matchLookaheadTerminal("UINT128", 0) || (p.matchLookaheadTerminal("SYMBOL", 0) || (p.matchLookaheadTerminal("STRING", 0) || (p.matchLookaheadTerminal("INT128", 0) || (p.matchLookaheadTerminal("INT", 0) || (p.matchLookaheadTerminal("FLOAT", 0) || (p.matchLookaheadTerminal("DECIMAL", 0) || -1)))))))
					}
					_t833 = _t834
				}
				_t831 = _t833
			}
			_t827 = _t831
		}
		_t819 = _t827
	}
	prediction186 := _t819
	var _t835 interface{}
	if prediction186 == 1 {
		_t836 := p.parse_term()
		term188 := _t836
		_t837 := &pb.RelTerm{}
		if term188 != nil {
			_t837.RelTermType = &pb.RelTerm_Term{Term: term188}
		}
		_t835 = _t837
	} else {
		var _t838 interface{}
		if prediction186 == 0 {
			_t839 := p.parse_specialized_value()
			specialized_value187 := _t839
			_t840 := &pb.RelTerm{}
			if specialized_value187 != nil {
				_t840.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value187}
			}
			_t838 = _t840
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t835 = _t838
	}
	return _t835
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t841 := p.parse_value()
	value189 := _t841
	return value189
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t842 := p.parse_name()
	name190 := _t842
	xs191 := []*pb.RelTerm{}
	cond192 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond192 {
		_t843 := p.parse_rel_term()
		item193 := _t843
		xs191 = listConcat(xs191, []*pb.RelTerm{item193})
		cond192 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms194 := xs191
	p.consumeLiteral(")")
	_t844 := &pb.RelAtom{Name: name190, Terms: rel_terms194}
	return _t844
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t845 := p.parse_term()
	term195 := _t845
	_t846 := p.parse_term()
	term_3196 := _t846
	p.consumeLiteral(")")
	_t847 := &pb.Cast{Input: term195, Result: term_3196}
	return _t847
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs197 := []*pb.Attribute{}
	cond198 := p.matchLookaheadLiteral("(", 0)
	for cond198 {
		_t848 := p.parse_attribute()
		item199 := _t848
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
	_t849 := p.parse_name()
	name201 := _t849
	xs202 := []*pb.Value{}
	cond203 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond203 {
		_t850 := p.parse_value()
		item204 := _t850
		xs202 = listConcat(xs202, []*pb.Value{item204})
		cond203 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values205 := xs202
	p.consumeLiteral(")")
	_t851 := &pb.Attribute{Name: name201, Args: values205}
	return _t851
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs206 := []*pb.RelationId{}
	cond207 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("INT", 0))
	for cond207 {
		_t852 := p.parse_relation_id()
		item208 := _t852
		xs206 = listConcat(xs206, []*pb.RelationId{item208})
		cond207 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("INT", 0))
	}
	relation_ids209 := xs206
	_t853 := p.parse_script()
	script210 := _t853
	p.consumeLiteral(")")
	_t854 := &pb.Algorithm{Global: relation_ids209, Body: script210}
	return _t854
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs211 := []*pb.Construct{}
	cond212 := p.matchLookaheadLiteral("(", 0)
	for cond212 {
		_t855 := p.parse_construct()
		item213 := _t855
		xs211 = listConcat(xs211, []*pb.Construct{item213})
		cond212 = p.matchLookaheadLiteral("(", 0)
	}
	constructs214 := xs211
	p.consumeLiteral(")")
	_t856 := &pb.Script{Constructs: constructs214}
	return _t856
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t857 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t865 interface{}
		if p.matchLookaheadLiteral("upsert", 1) {
			_t865 = 1
		} else {
			var _t869 interface{}
			if p.matchLookaheadLiteral("monus", 1) {
				_t869 = 1
			} else {
				var _t871 interface{}
				if p.matchLookaheadLiteral("monoid", 1) {
					_t871 = 1
				} else {
					var _t872 interface{}
					if p.matchLookaheadLiteral("loop", 1) {
						_t872 = 0
					} else {
						_t872 = (p.matchLookaheadLiteral("break", 1) || (p.matchLookaheadLiteral("assign", 1) || -1))
					}
					_t871 = _t872
				}
				_t869 = _t871
			}
			_t865 = _t869
		}
		_t857 = _t865
	} else {
		_t857 = -1
	}
	prediction215 := _t857
	var _t873 interface{}
	if prediction215 == 1 {
		_t874 := p.parse_instruction()
		instruction217 := _t874
		_t875 := &pb.Construct{}
		if instruction217 != nil {
			_t875.ConstructType = &pb.Construct_Instruction{Instruction: instruction217}
		}
		_t873 = _t875
	} else {
		var _t876 interface{}
		if prediction215 == 0 {
			_t877 := p.parse_loop()
			loop216 := _t877
			_t878 := &pb.Construct{}
			if loop216 != nil {
				_t878.ConstructType = &pb.Construct_Loop{Loop: loop216}
			}
			_t876 = _t878
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t873 = _t876
	}
	return _t873
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t879 := p.parse_init()
	init218 := _t879
	_t880 := p.parse_script()
	script219 := _t880
	p.consumeLiteral(")")
	_t881 := &pb.Loop{Init: init218, Body: script219}
	return _t881
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs220 := []*pb.Instruction{}
	cond221 := p.matchLookaheadLiteral("(", 0)
	for cond221 {
		_t882 := p.parse_instruction()
		item222 := _t882
		xs220 = listConcat(xs220, []*pb.Instruction{item222})
		cond221 = p.matchLookaheadLiteral("(", 0)
	}
	instructions223 := xs220
	p.consumeLiteral(")")
	return instructions223
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t883 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t888 interface{}
		if p.matchLookaheadLiteral("upsert", 1) {
			_t888 = 1
		} else {
			var _t889 interface{}
			if p.matchLookaheadLiteral("monus", 1) {
				_t889 = 4
			} else {
				var _t890 interface{}
				if p.matchLookaheadLiteral("monoid", 1) {
					_t890 = 3
				} else {
					var _t891 interface{}
					if p.matchLookaheadLiteral("break", 1) {
						_t891 = 2
					} else {
						var _t892 interface{}
						if p.matchLookaheadLiteral("assign", 1) {
							_t892 = 0
						} else {
							_t892 = -1
						}
						_t891 = _t892
					}
					_t890 = _t891
				}
				_t889 = _t890
			}
			_t888 = _t889
		}
		_t883 = _t888
	} else {
		_t883 = -1
	}
	prediction224 := _t883
	var _t893 interface{}
	if prediction224 == 4 {
		_t894 := p.parse_monus_def()
		monus_def229 := _t894
		_t895 := &pb.Instruction{}
		if monus_def229 != nil {
			_t895.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def229}
		}
		_t893 = _t895
	} else {
		var _t896 interface{}
		if prediction224 == 3 {
			_t897 := p.parse_monoid_def()
			monoid_def228 := _t897
			_t898 := &pb.Instruction{}
			if monoid_def228 != nil {
				_t898.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def228}
			}
			_t896 = _t898
		} else {
			var _t899 interface{}
			if prediction224 == 2 {
				_t900 := p.parse_break()
				break227 := _t900
				_t901 := &pb.Instruction{}
				if break227 != nil {
					_t901.InstrType = &pb.Instruction_Break{Break: break227}
				}
				_t899 = _t901
			} else {
				var _t902 interface{}
				if prediction224 == 1 {
					_t903 := p.parse_upsert()
					upsert226 := _t903
					_t904 := &pb.Instruction{}
					if upsert226 != nil {
						_t904.InstrType = &pb.Instruction_Upsert{Upsert: upsert226}
					}
					_t902 = _t904
				} else {
					var _t905 interface{}
					if prediction224 == 0 {
						_t906 := p.parse_assign()
						assign225 := _t906
						_t907 := &pb.Instruction{}
						if assign225 != nil {
							_t907.InstrType = &pb.Instruction_Assign{Assign: assign225}
						}
						_t905 = _t907
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t902 = _t905
				}
				_t899 = _t902
			}
			_t896 = _t899
		}
		_t893 = _t896
	}
	return _t893
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t908 := p.parse_relation_id()
	relation_id230 := _t908
	_t909 := p.parse_abstraction()
	abstraction231 := _t909
	var _t911 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t912 := p.parse_attrs()
		_t911 = _t912
	} else {
		_t911 = nil
	}
	attrs232 := _t911
	p.consumeLiteral(")")
	_t913 := &pb.Assign{Name: relation_id230, Body: abstraction231, Attrs: unwrapOr(attrs232, []interface{}{})}
	return _t913
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t914 := p.parse_relation_id()
	relation_id233 := _t914
	_t915 := p.parse_abstraction_with_arity()
	abstraction_with_arity234 := _t915
	var _t917 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t918 := p.parse_attrs()
		_t917 = _t918
	} else {
		_t917 = nil
	}
	attrs235 := _t917
	p.consumeLiteral(")")
	_t919 := &pb.Upsert{Name: relation_id233, Body: abstraction_with_arity234[0], Attrs: unwrapOr(attrs235, []interface{}{}), ValueArity: abstraction_with_arity234[1]}
	return _t919
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t920 := p.parse_bindings()
	bindings236 := _t920
	_t921 := p.parse_formula()
	formula237 := _t921
	p.consumeLiteral(")")
	_t922 := &pb.Abstraction{Vars: listConcat(bindings236[0], bindings236[1]), Value: formula237}
	return []interface{}{{_t922, len(bindings236[1])}}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t923 := p.parse_relation_id()
	relation_id238 := _t923
	_t924 := p.parse_abstraction()
	abstraction239 := _t924
	var _t926 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t927 := p.parse_attrs()
		_t926 = _t927
	} else {
		_t926 = nil
	}
	attrs240 := _t926
	p.consumeLiteral(")")
	_t928 := &pb.Break{Name: relation_id238, Body: abstraction239, Attrs: unwrapOr(attrs240, []interface{}{})}
	return _t928
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t929 := p.parse_monoid()
	monoid241 := _t929
	_t930 := p.parse_relation_id()
	relation_id242 := _t930
	_t931 := p.parse_abstraction_with_arity()
	abstraction_with_arity243 := _t931
	var _t933 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t934 := p.parse_attrs()
		_t933 = _t934
	} else {
		_t933 = nil
	}
	attrs244 := _t933
	p.consumeLiteral(")")
	_t935 := &pb.MonoidDef{Monoid: monoid241, Name: relation_id242, Body: abstraction_with_arity243[0], Attrs: unwrapOr(attrs244, []interface{}{}), ValueArity: abstraction_with_arity243[1]}
	return _t935
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t936 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t937 interface{}
		if p.matchLookaheadLiteral("sum", 1) {
			_t937 = 3
		} else {
			var _t938 interface{}
			if p.matchLookaheadLiteral("or", 1) {
				_t938 = 0
			} else {
				var _t940 interface{}
				if p.matchLookaheadLiteral("min", 1) {
					_t940 = 1
				} else {
					var _t941 interface{}
					if p.matchLookaheadLiteral("max", 1) {
						_t941 = 2
					} else {
						_t941 = -1
					}
					_t940 = _t941
				}
				_t938 = _t940
			}
			_t937 = _t938
		}
		_t936 = _t937
	} else {
		_t936 = -1
	}
	prediction245 := _t936
	var _t942 interface{}
	if prediction245 == 3 {
		_t943 := p.parse_sum_monoid()
		sum_monoid249 := _t943
		_t944 := &pb.Monoid{}
		if sum_monoid249 != nil {
			_t944.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid249}
		}
		_t942 = _t944
	} else {
		var _t945 interface{}
		if prediction245 == 2 {
			_t946 := p.parse_max_monoid()
			max_monoid248 := _t946
			_t947 := &pb.Monoid{}
			if max_monoid248 != nil {
				_t947.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid248}
			}
			_t945 = _t947
		} else {
			var _t948 interface{}
			if prediction245 == 1 {
				_t949 := p.parse_min_monoid()
				min_monoid247 := _t949
				_t950 := &pb.Monoid{}
				if min_monoid247 != nil {
					_t950.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid247}
				}
				_t948 = _t950
			} else {
				var _t951 interface{}
				if prediction245 == 0 {
					_t952 := p.parse_or_monoid()
					or_monoid246 := _t952
					_t953 := &pb.Monoid{}
					if or_monoid246 != nil {
						_t953.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid246}
					}
					_t951 = _t953
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t948 = _t951
			}
			_t945 = _t948
		}
		_t942 = _t945
	}
	return _t942
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t954 := &pb.OrMonoid{}
	return _t954
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t955 := p.parse_type()
	type250 := _t955
	p.consumeLiteral(")")
	_t956 := &pb.MinMonoid{Type: type250}
	return _t956
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t957 := p.parse_type()
	type251 := _t957
	p.consumeLiteral(")")
	_t958 := &pb.MaxMonoid{Type: type251}
	return _t958
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t959 := p.parse_type()
	type252 := _t959
	p.consumeLiteral(")")
	_t960 := &pb.SumMonoid{Type: type252}
	return _t960
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t961 := p.parse_monoid()
	monoid253 := _t961
	_t962 := p.parse_relation_id()
	relation_id254 := _t962
	_t963 := p.parse_abstraction_with_arity()
	abstraction_with_arity255 := _t963
	var _t965 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t966 := p.parse_attrs()
		_t965 = _t966
	} else {
		_t965 = nil
	}
	attrs256 := _t965
	p.consumeLiteral(")")
	_t967 := &pb.MonusDef{Monoid: monoid253, Name: relation_id254, Body: abstraction_with_arity255[0], Attrs: unwrapOr(attrs256, []interface{}{}), ValueArity: abstraction_with_arity255[1]}
	return _t967
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t968 := p.parse_relation_id()
	relation_id257 := _t968
	_t969 := p.parse_abstraction()
	abstraction258 := _t969
	_t970 := p.parse_functional_dependency_keys()
	functional_dependency_keys259 := _t970
	_t971 := p.parse_functional_dependency_values()
	functional_dependency_values260 := _t971
	p.consumeLiteral(")")
	_t972 := &pb.FunctionalDependency{Guard: abstraction258, Keys: functional_dependency_keys259, Values: functional_dependency_values260}
	_t973 := &pb.Constraint{Name: relation_id257}
	if _t972 != nil {
		_t973.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t972}
	}
	return _t973
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs261 := []*pb.Var{}
	cond262 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond262 {
		_t974 := p.parse_var()
		item263 := _t974
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
		_t975 := p.parse_var()
		item267 := _t975
		xs265 = listConcat(xs265, []*pb.Var{item267})
		cond266 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars268 := xs265
	p.consumeLiteral(")")
	return vars268
}

func (p *Parser) parse_data() *pb.Data {
	var _t976 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t977 interface{}
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t977 = 0
		} else {
			var _t978 interface{}
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t978 = 2
			} else {
				_t978 = (p.matchLookaheadLiteral("betree_relation", 1) || -1)
			}
			_t977 = _t978
		}
		_t976 = _t977
	} else {
		_t976 = -1
	}
	prediction269 := _t976
	var _t979 interface{}
	if prediction269 == 2 {
		_t980 := p.parse_csv_data()
		csv_data272 := _t980
		_t981 := &pb.Data{}
		if csv_data272 != nil {
			_t981.DataType = &pb.Data_CsvData{CsvData: csv_data272}
		}
		_t979 = _t981
	} else {
		var _t982 interface{}
		if prediction269 == 1 {
			_t983 := p.parse_betree_relation()
			betree_relation271 := _t983
			_t984 := &pb.Data{}
			if betree_relation271 != nil {
				_t984.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation271}
			}
			_t982 = _t984
		} else {
			var _t985 interface{}
			if prediction269 == 0 {
				_t986 := p.parse_rel_edb()
				rel_edb270 := _t986
				_t987 := &pb.Data{}
				if rel_edb270 != nil {
					_t987.DataType = &pb.Data_RelEdb{RelEdb: rel_edb270}
				}
				_t985 = _t987
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t982 = _t985
		}
		_t979 = _t982
	}
	return _t979
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t988 := p.parse_relation_id()
	relation_id273 := _t988
	_t989 := p.parse_rel_edb_path()
	rel_edb_path274 := _t989
	_t990 := p.parse_rel_edb_types()
	rel_edb_types275 := _t990
	p.consumeLiteral(")")
	_t991 := &pb.RelEDB{TargetId: relation_id273, Path: rel_edb_path274, Types: rel_edb_types275}
	return _t991
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs276 := []string{}
	cond277 := p.matchLookaheadTerminal("STRING", 0)
	for cond277 {
		item278 := p.consumeTerminal("STRING")
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
	cond281 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond281 {
		_t992 := p.parse_type()
		item282 := _t992
		xs280 = listConcat(xs280, []*pb.Type{item282})
		cond281 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types283 := xs280
	p.consumeLiteral("]")
	return types283
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t993 := p.parse_relation_id()
	relation_id284 := _t993
	_t994 := p.parse_betree_info()
	betree_info285 := _t994
	p.consumeLiteral(")")
	_t995 := &pb.BeTreeRelation{Name: relation_id284, RelationInfo: betree_info285}
	return _t995
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t996 := p.parse_betree_info_key_types()
	betree_info_key_types286 := _t996
	_t997 := p.parse_betree_info_value_types()
	betree_info_value_types287 := _t997
	_t998 := p.parse_config_dict()
	config_dict288 := _t998
	p.consumeLiteral(")")
	_t999 := p.construct_betree_info(betree_info_key_types286, betree_info_value_types287, config_dict288)
	return _t999
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs289 := []*pb.Type{}
	cond290 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond290 {
		_t1000 := p.parse_type()
		item291 := _t1000
		xs289 = listConcat(xs289, []*pb.Type{item291})
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
		_t1001 := p.parse_type()
		item295 := _t1001
		xs293 = listConcat(xs293, []*pb.Type{item295})
		cond294 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types296 := xs293
	p.consumeLiteral(")")
	return types296
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1002 := p.parse_csvlocator()
	csvlocator297 := _t1002
	_t1003 := p.parse_csv_config()
	csv_config298 := _t1003
	_t1004 := p.parse_csv_columns()
	csv_columns299 := _t1004
	_t1005 := p.parse_csv_asof()
	csv_asof300 := _t1005
	p.consumeLiteral(")")
	_t1006 := &pb.CSVData{Locator: csvlocator297, Config: csv_config298, Columns: csv_columns299, Asof: csv_asof300}
	return _t1006
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1008 interface{}
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1009 := p.parse_csv_locator_paths()
		_t1008 = _t1009
	} else {
		_t1008 = nil
	}
	csv_locator_paths301 := _t1008
	var _t1011 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		_t1012 := p.parse_csv_locator_inline_data()
		_t1011 = _t1012
	} else {
		_t1011 = nil
	}
	csv_locator_inline_data302 := _t1011
	p.consumeLiteral(")")
	_t1013 := &pb.CSVLocator{Paths: unwrapOr(csv_locator_paths301, []interface{}{}), InlineData: []byte(unwrapOr(csv_locator_inline_data302, ""))}
	return _t1013
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs303 := []string{}
	cond304 := p.matchLookaheadTerminal("STRING", 0)
	for cond304 {
		item305 := p.consumeTerminal("STRING")
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
	string307 := p.consumeTerminal("STRING")
	p.consumeLiteral(")")
	return string307
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1014 := p.parse_config_dict()
	config_dict308 := _t1014
	p.consumeLiteral(")")
	_t1015 := p.construct_csv_config(config_dict308)
	return _t1015
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs309 := []*pb.CSVColumn{}
	cond310 := p.matchLookaheadLiteral("(", 0)
	for cond310 {
		_t1016 := p.parse_csv_column()
		item311 := _t1016
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
	string313 := p.consumeTerminal("STRING")
	_t1017 := p.parse_relation_id()
	relation_id314 := _t1017
	p.consumeLiteral("[")
	xs315 := []*pb.Type{}
	cond316 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond316 {
		_t1018 := p.parse_type()
		item317 := _t1018
		xs315 = listConcat(xs315, []*pb.Type{item317})
		cond316 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types318 := xs315
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1019 := &pb.CSVColumn{ColumnName: string313, TargetId: relation_id314, Types: types318}
	return _t1019
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string319 := p.consumeTerminal("STRING")
	p.consumeLiteral(")")
	return string319
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1020 := p.parse_fragment_id()
	fragment_id320 := _t1020
	p.consumeLiteral(")")
	_t1021 := &pb.Undefine{FragmentId: fragment_id320}
	return _t1021
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs321 := []*pb.RelationId{}
	cond322 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("INT", 0))
	for cond322 {
		_t1022 := p.parse_relation_id()
		item323 := _t1022
		xs321 = listConcat(xs321, []*pb.RelationId{item323})
		cond322 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("INT", 0))
	}
	relation_ids324 := xs321
	p.consumeLiteral(")")
	_t1023 := &pb.Context{Relations: relation_ids324}
	return _t1023
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs325 := []*pb.Read{}
	cond326 := p.matchLookaheadLiteral("(", 0)
	for cond326 {
		_t1024 := p.parse_read()
		item327 := _t1024
		xs325 = listConcat(xs325, []*pb.Read{item327})
		cond326 = p.matchLookaheadLiteral("(", 0)
	}
	reads328 := xs325
	p.consumeLiteral(")")
	return reads328
}

func (p *Parser) parse_read() *pb.Read {
	var _t1025 interface{}
	if p.matchLookaheadLiteral("(", 0) {
		var _t1026 interface{}
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1026 = 2
		} else {
			var _t1030 interface{}
			if p.matchLookaheadLiteral("output", 1) {
				_t1030 = 1
			} else {
				var _t1031 interface{}
				if p.matchLookaheadLiteral("export", 1) {
					_t1031 = 4
				} else {
					var _t1032 interface{}
					if p.matchLookaheadLiteral("demand", 1) {
						_t1032 = 0
					} else {
						var _t1033 interface{}
						if p.matchLookaheadLiteral("abort", 1) {
							_t1033 = 3
						} else {
							_t1033 = -1
						}
						_t1032 = _t1033
					}
					_t1031 = _t1032
				}
				_t1030 = _t1031
			}
			_t1026 = _t1030
		}
		_t1025 = _t1026
	} else {
		_t1025 = -1
	}
	prediction329 := _t1025
	var _t1034 interface{}
	if prediction329 == 4 {
		_t1035 := p.parse_export()
		export334 := _t1035
		_t1036 := &pb.Read{}
		if export334 != nil {
			_t1036.ReadType = &pb.Read_Export{Export: export334}
		}
		_t1034 = _t1036
	} else {
		var _t1037 interface{}
		if prediction329 == 3 {
			_t1038 := p.parse_abort()
			abort333 := _t1038
			_t1039 := &pb.Read{}
			if abort333 != nil {
				_t1039.ReadType = &pb.Read_Abort{Abort: abort333}
			}
			_t1037 = _t1039
		} else {
			var _t1040 interface{}
			if prediction329 == 2 {
				_t1041 := p.parse_what_if()
				what_if332 := _t1041
				_t1042 := &pb.Read{}
				if what_if332 != nil {
					_t1042.ReadType = &pb.Read_WhatIf{WhatIf: what_if332}
				}
				_t1040 = _t1042
			} else {
				var _t1043 interface{}
				if prediction329 == 1 {
					_t1044 := p.parse_output()
					output331 := _t1044
					_t1045 := &pb.Read{}
					if output331 != nil {
						_t1045.ReadType = &pb.Read_Output{Output: output331}
					}
					_t1043 = _t1045
				} else {
					var _t1046 interface{}
					if prediction329 == 0 {
						_t1047 := p.parse_demand()
						demand330 := _t1047
						_t1048 := &pb.Read{}
						if demand330 != nil {
							_t1048.ReadType = &pb.Read_Demand{Demand: demand330}
						}
						_t1046 = _t1048
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1043 = _t1046
				}
				_t1040 = _t1043
			}
			_t1037 = _t1040
		}
		_t1034 = _t1037
	}
	return _t1034
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1049 := p.parse_relation_id()
	relation_id335 := _t1049
	p.consumeLiteral(")")
	_t1050 := &pb.Demand{RelationId: relation_id335}
	return _t1050
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	var _t1052 interface{}
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1053 := p.parse_name()
		_t1052 = _t1053
	} else {
		_t1052 = nil
	}
	name336 := _t1052
	_t1054 := p.parse_relation_id()
	relation_id337 := _t1054
	p.consumeLiteral(")")
	_t1055 := &pb.Output{Name: unwrapOr(name336, "output"), RelationId: relation_id337}
	return _t1055
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1056 := p.parse_name()
	name338 := _t1056
	_t1057 := p.parse_epoch()
	epoch339 := _t1057
	p.consumeLiteral(")")
	_t1058 := &pb.WhatIf{Branch: name338, Epoch: epoch339}
	return _t1058
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1060 interface{}
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1061 := p.parse_name()
		_t1060 = _t1061
	} else {
		_t1060 = nil
	}
	name340 := _t1060
	_t1062 := p.parse_relation_id()
	relation_id341 := _t1062
	p.consumeLiteral(")")
	_t1063 := &pb.Abort{Name: unwrapOr(name340, "abort"), RelationId: relation_id341}
	return _t1063
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1064 := p.parse_export_csv_config()
	export_csv_config342 := _t1064
	p.consumeLiteral(")")
	_t1065 := &pb.Export{}
	if export_csv_config342 != nil {
		_t1065.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config342}
	}
	return _t1065
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1066 := p.parse_export_csv_path()
	export_csv_path343 := _t1066
	_t1067 := p.parse_export_csv_columns()
	export_csv_columns344 := _t1067
	_t1068 := p.parse_config_dict()
	config_dict345 := _t1068
	p.consumeLiteral(")")
	_t1069 := p.export_csv_config(export_csv_path343, export_csv_columns344, config_dict345)
	return _t1069
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string346 := p.consumeTerminal("STRING")
	p.consumeLiteral(")")
	return string346
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs347 := []*pb.ExportCSVColumn{}
	cond348 := p.matchLookaheadLiteral("(", 0)
	for cond348 {
		_t1070 := p.parse_export_csv_column()
		item349 := _t1070
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
	string351 := p.consumeTerminal("STRING")
	_t1071 := p.parse_relation_id()
	relation_id352 := _t1071
	p.consumeLiteral(")")
	_t1072 := &pb.ExportCSVColumn{ColumnName: string351, ColumnData: relation_id352}
	return _t1072
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
