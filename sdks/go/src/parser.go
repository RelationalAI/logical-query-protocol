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
	"encoding/binary"
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
			Type:  best.tokenType,
			Value: best.action(best.value),
			Pos:   l.pos,
		})
		l.pos = best.endPos
	}

	l.tokens = append(l.tokens, Token{Type: "$", Value: TokenValue{}, Pos: l.pos})
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
	return Token{Type: "$", Value: TokenValue{}, Pos: -1}
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
	hash := sha256.Sum256([]byte(name))
	low := binary.LittleEndian.Uint64(hash[:8])
	high := binary.LittleEndian.Uint64(hash[8:16])
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
	var _t1322 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1322
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1323 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1323
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1324 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1324
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1325 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1325
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1326 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1326
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1327 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1327
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1328 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1328
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1329 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1329
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1330 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1330
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1331 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1331
	_t1332 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1332
	_t1333 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1333
	_t1334 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1334
	_t1335 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1335
	_t1336 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1336
	_t1337 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1337
	_t1338 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1338
	_t1339 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1339
	_t1340 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1340
	_t1341 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1341
	_t1342 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1342
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1343 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1343
	_t1344 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1344
	_t1345 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1345
	_t1346 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1346
	_t1347 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1347
	_t1348 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1348
	_t1349 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1349
	_t1350 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1350
	_t1351 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1351
	_t1352 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1352.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1352.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1352
	_t1353 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1353
}

func (p *Parser) default_configure() *pb.Configure {
	_t1354 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1354
	_t1355 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1355
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
	_t1356 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1356
	_t1357 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1357
	_t1358 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1358
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1359 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1359
	_t1360 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1360
	_t1361 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1361
	_t1362 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1362
	_t1363 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1363
	_t1364 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1364
	_t1365 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1365
	_t1366 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1366
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t712 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t713 := p.parse_configure()
		_t712 = _t713
	}
	configure356 := _t712
	var _t714 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t715 := p.parse_sync()
		_t714 = _t715
	}
	sync357 := _t714
	xs358 := []*pb.Epoch{}
	cond359 := p.matchLookaheadLiteral("(", 0)
	for cond359 {
		_t716 := p.parse_epoch()
		item360 := _t716
		xs358 = append(xs358, item360)
		cond359 = p.matchLookaheadLiteral("(", 0)
	}
	epochs361 := xs358
	p.consumeLiteral(")")
	_t717 := p.default_configure()
	_t718 := configure356
	if configure356 == nil {
		_t718 = _t717
	}
	_t719 := &pb.Transaction{Epochs: epochs361, Configure: _t718, Sync: sync357}
	return _t719
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t720 := p.parse_config_dict()
	config_dict362 := _t720
	p.consumeLiteral(")")
	_t721 := p.construct_configure(config_dict362)
	return _t721
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs363 := [][]interface{}{}
	cond364 := p.matchLookaheadLiteral(":", 0)
	for cond364 {
		_t722 := p.parse_config_key_value()
		item365 := _t722
		xs363 = append(xs363, item365)
		cond364 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values366 := xs363
	p.consumeLiteral("}")
	return config_key_values366
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol367 := p.consumeTerminal("SYMBOL").Value.str
	_t723 := p.parse_value()
	value368 := _t723
	return []interface{}{symbol367, value368}
}

func (p *Parser) parse_value() *pb.Value {
	var _t724 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t724 = 9
	} else {
		var _t725 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t725 = 8
		} else {
			var _t726 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t726 = 9
			} else {
				var _t727 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t728 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t728 = 1
					} else {
						var _t729 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t729 = 0
						} else {
							_t729 = -1
						}
						_t728 = _t729
					}
					_t727 = _t728
				} else {
					var _t730 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t730 = 5
					} else {
						var _t731 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t731 = 2
						} else {
							var _t732 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t732 = 6
							} else {
								var _t733 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t733 = 3
								} else {
									var _t734 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t734 = 4
									} else {
										var _t735 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t735 = 7
										} else {
											_t735 = -1
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
					_t727 = _t730
				}
				_t726 = _t727
			}
			_t725 = _t726
		}
		_t724 = _t725
	}
	prediction369 := _t724
	var _t736 *pb.Value
	if prediction369 == 9 {
		_t737 := p.parse_boolean_value()
		boolean_value378 := _t737
		_t738 := &pb.Value{}
		_t738.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value378}
		_t736 = _t738
	} else {
		var _t739 *pb.Value
		if prediction369 == 8 {
			p.consumeLiteral("missing")
			_t740 := &pb.MissingValue{}
			_t741 := &pb.Value{}
			_t741.Value = &pb.Value_MissingValue{MissingValue: _t740}
			_t739 = _t741
		} else {
			var _t742 *pb.Value
			if prediction369 == 7 {
				decimal377 := p.consumeTerminal("DECIMAL").Value.decimal
				_t743 := &pb.Value{}
				_t743.Value = &pb.Value_DecimalValue{DecimalValue: decimal377}
				_t742 = _t743
			} else {
				var _t744 *pb.Value
				if prediction369 == 6 {
					int128376 := p.consumeTerminal("INT128").Value.int128
					_t745 := &pb.Value{}
					_t745.Value = &pb.Value_Int128Value{Int128Value: int128376}
					_t744 = _t745
				} else {
					var _t746 *pb.Value
					if prediction369 == 5 {
						uint128375 := p.consumeTerminal("UINT128").Value.uint128
						_t747 := &pb.Value{}
						_t747.Value = &pb.Value_Uint128Value{Uint128Value: uint128375}
						_t746 = _t747
					} else {
						var _t748 *pb.Value
						if prediction369 == 4 {
							float374 := p.consumeTerminal("FLOAT").Value.f64
							_t749 := &pb.Value{}
							_t749.Value = &pb.Value_FloatValue{FloatValue: float374}
							_t748 = _t749
						} else {
							var _t750 *pb.Value
							if prediction369 == 3 {
								int373 := p.consumeTerminal("INT").Value.i64
								_t751 := &pb.Value{}
								_t751.Value = &pb.Value_IntValue{IntValue: int373}
								_t750 = _t751
							} else {
								var _t752 *pb.Value
								if prediction369 == 2 {
									string372 := p.consumeTerminal("STRING").Value.str
									_t753 := &pb.Value{}
									_t753.Value = &pb.Value_StringValue{StringValue: string372}
									_t752 = _t753
								} else {
									var _t754 *pb.Value
									if prediction369 == 1 {
										_t755 := p.parse_datetime()
										datetime371 := _t755
										_t756 := &pb.Value{}
										_t756.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime371}
										_t754 = _t756
									} else {
										var _t757 *pb.Value
										if prediction369 == 0 {
											_t758 := p.parse_date()
											date370 := _t758
											_t759 := &pb.Value{}
											_t759.Value = &pb.Value_DateValue{DateValue: date370}
											_t757 = _t759
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t754 = _t757
									}
									_t752 = _t754
								}
								_t750 = _t752
							}
							_t748 = _t750
						}
						_t746 = _t748
					}
					_t744 = _t746
				}
				_t742 = _t744
			}
			_t739 = _t742
		}
		_t736 = _t739
	}
	return _t736
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int379 := p.consumeTerminal("INT").Value.i64
	int_3380 := p.consumeTerminal("INT").Value.i64
	int_4381 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t760 := &pb.DateValue{Year: int32(int379), Month: int32(int_3380), Day: int32(int_4381)}
	return _t760
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int382 := p.consumeTerminal("INT").Value.i64
	int_3383 := p.consumeTerminal("INT").Value.i64
	int_4384 := p.consumeTerminal("INT").Value.i64
	int_5385 := p.consumeTerminal("INT").Value.i64
	int_6386 := p.consumeTerminal("INT").Value.i64
	int_7387 := p.consumeTerminal("INT").Value.i64
	var _t761 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t761 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8388 := _t761
	p.consumeLiteral(")")
	_t762 := &pb.DateTimeValue{Year: int32(int382), Month: int32(int_3383), Day: int32(int_4384), Hour: int32(int_5385), Minute: int32(int_6386), Second: int32(int_7387), Microsecond: int32(deref(int_8388, 0))}
	return _t762
}

func (p *Parser) parse_boolean_value() bool {
	var _t763 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t763 = 0
	} else {
		var _t764 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t764 = 1
		} else {
			_t764 = -1
		}
		_t763 = _t764
	}
	prediction389 := _t763
	var _t765 bool
	if prediction389 == 1 {
		p.consumeLiteral("false")
		_t765 = false
	} else {
		var _t766 bool
		if prediction389 == 0 {
			p.consumeLiteral("true")
			_t766 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t765 = _t766
	}
	return _t765
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs390 := []*pb.FragmentId{}
	cond391 := p.matchLookaheadLiteral(":", 0)
	for cond391 {
		_t767 := p.parse_fragment_id()
		item392 := _t767
		xs390 = append(xs390, item392)
		cond391 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids393 := xs390
	p.consumeLiteral(")")
	_t768 := &pb.Sync{Fragments: fragment_ids393}
	return _t768
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol394 := p.consumeTerminal("SYMBOL").Value.str
	return &pb.FragmentId{Id: []byte(symbol394)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t769 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t770 := p.parse_epoch_writes()
		_t769 = _t770
	}
	epoch_writes395 := _t769
	var _t771 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t772 := p.parse_epoch_reads()
		_t771 = _t772
	}
	epoch_reads396 := _t771
	p.consumeLiteral(")")
	_t773 := epoch_writes395
	if epoch_writes395 == nil {
		_t773 = []*pb.Write{}
	}
	_t774 := epoch_reads396
	if epoch_reads396 == nil {
		_t774 = []*pb.Read{}
	}
	_t775 := &pb.Epoch{Writes: _t773, Reads: _t774}
	return _t775
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs397 := []*pb.Write{}
	cond398 := p.matchLookaheadLiteral("(", 0)
	for cond398 {
		_t776 := p.parse_write()
		item399 := _t776
		xs397 = append(xs397, item399)
		cond398 = p.matchLookaheadLiteral("(", 0)
	}
	writes400 := xs397
	p.consumeLiteral(")")
	return writes400
}

func (p *Parser) parse_write() *pb.Write {
	var _t777 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t778 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t778 = 1
		} else {
			var _t779 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t779 = 3
			} else {
				var _t780 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t780 = 0
				} else {
					var _t781 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t781 = 2
					} else {
						_t781 = -1
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
	prediction401 := _t777
	var _t782 *pb.Write
	if prediction401 == 3 {
		_t783 := p.parse_snapshot()
		snapshot405 := _t783
		_t784 := &pb.Write{}
		_t784.WriteType = &pb.Write_Snapshot{Snapshot: snapshot405}
		_t782 = _t784
	} else {
		var _t785 *pb.Write
		if prediction401 == 2 {
			_t786 := p.parse_context()
			context404 := _t786
			_t787 := &pb.Write{}
			_t787.WriteType = &pb.Write_Context{Context: context404}
			_t785 = _t787
		} else {
			var _t788 *pb.Write
			if prediction401 == 1 {
				_t789 := p.parse_undefine()
				undefine403 := _t789
				_t790 := &pb.Write{}
				_t790.WriteType = &pb.Write_Undefine{Undefine: undefine403}
				_t788 = _t790
			} else {
				var _t791 *pb.Write
				if prediction401 == 0 {
					_t792 := p.parse_define()
					define402 := _t792
					_t793 := &pb.Write{}
					_t793.WriteType = &pb.Write_Define{Define: define402}
					_t791 = _t793
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t788 = _t791
			}
			_t785 = _t788
		}
		_t782 = _t785
	}
	return _t782
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t794 := p.parse_fragment()
	fragment406 := _t794
	p.consumeLiteral(")")
	_t795 := &pb.Define{Fragment: fragment406}
	return _t795
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t796 := p.parse_new_fragment_id()
	new_fragment_id407 := _t796
	xs408 := []*pb.Declaration{}
	cond409 := p.matchLookaheadLiteral("(", 0)
	for cond409 {
		_t797 := p.parse_declaration()
		item410 := _t797
		xs408 = append(xs408, item410)
		cond409 = p.matchLookaheadLiteral("(", 0)
	}
	declarations411 := xs408
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id407, declarations411)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t798 := p.parse_fragment_id()
	fragment_id412 := _t798
	p.startFragment(fragment_id412)
	return fragment_id412
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t799 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t800 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t800 = 3
		} else {
			var _t801 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t801 = 2
			} else {
				var _t802 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t802 = 0
				} else {
					var _t803 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t803 = 3
					} else {
						var _t804 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t804 = 3
						} else {
							var _t805 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t805 = 1
							} else {
								_t805 = -1
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
	} else {
		_t799 = -1
	}
	prediction413 := _t799
	var _t806 *pb.Declaration
	if prediction413 == 3 {
		_t807 := p.parse_data()
		data417 := _t807
		_t808 := &pb.Declaration{}
		_t808.DeclarationType = &pb.Declaration_Data{Data: data417}
		_t806 = _t808
	} else {
		var _t809 *pb.Declaration
		if prediction413 == 2 {
			_t810 := p.parse_constraint()
			constraint416 := _t810
			_t811 := &pb.Declaration{}
			_t811.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint416}
			_t809 = _t811
		} else {
			var _t812 *pb.Declaration
			if prediction413 == 1 {
				_t813 := p.parse_algorithm()
				algorithm415 := _t813
				_t814 := &pb.Declaration{}
				_t814.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm415}
				_t812 = _t814
			} else {
				var _t815 *pb.Declaration
				if prediction413 == 0 {
					_t816 := p.parse_def()
					def414 := _t816
					_t817 := &pb.Declaration{}
					_t817.DeclarationType = &pb.Declaration_Def{Def: def414}
					_t815 = _t817
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t812 = _t815
			}
			_t809 = _t812
		}
		_t806 = _t809
	}
	return _t806
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t818 := p.parse_relation_id()
	relation_id418 := _t818
	_t819 := p.parse_abstraction()
	abstraction419 := _t819
	var _t820 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t821 := p.parse_attrs()
		_t820 = _t821
	}
	attrs420 := _t820
	p.consumeLiteral(")")
	_t822 := attrs420
	if attrs420 == nil {
		_t822 = []*pb.Attribute{}
	}
	_t823 := &pb.Def{Name: relation_id418, Body: abstraction419, Attrs: _t822}
	return _t823
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t824 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t824 = 0
	} else {
		var _t825 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t825 = 1
		} else {
			_t825 = -1
		}
		_t824 = _t825
	}
	prediction421 := _t824
	var _t826 *pb.RelationId
	if prediction421 == 1 {
		uint128423 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128423
		_t826 = &pb.RelationId{IdLow: uint128423.Low, IdHigh: uint128423.High}
	} else {
		var _t827 *pb.RelationId
		if prediction421 == 0 {
			p.consumeLiteral(":")
			symbol422 := p.consumeTerminal("SYMBOL").Value.str
			_t827 = p.relationIdFromString(symbol422)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t826 = _t827
	}
	return _t826
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t828 := p.parse_bindings()
	bindings424 := _t828
	_t829 := p.parse_formula()
	formula425 := _t829
	p.consumeLiteral(")")
	_t830 := &pb.Abstraction{Vars: listConcat(bindings424[0].([]*pb.Binding), bindings424[1].([]*pb.Binding)), Value: formula425}
	return _t830
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs426 := []*pb.Binding{}
	cond427 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond427 {
		_t831 := p.parse_binding()
		item428 := _t831
		xs426 = append(xs426, item428)
		cond427 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings429 := xs426
	var _t832 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t833 := p.parse_value_bindings()
		_t832 = _t833
	}
	value_bindings430 := _t832
	p.consumeLiteral("]")
	_t834 := value_bindings430
	if value_bindings430 == nil {
		_t834 = []*pb.Binding{}
	}
	return []interface{}{bindings429, _t834}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol431 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t835 := p.parse_type()
	type432 := _t835
	_t836 := &pb.Var{Name: symbol431}
	_t837 := &pb.Binding{Var: _t836, Type: type432}
	return _t837
}

func (p *Parser) parse_type() *pb.Type {
	var _t838 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t838 = 0
	} else {
		var _t839 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t839 = 4
		} else {
			var _t840 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t840 = 1
			} else {
				var _t841 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t841 = 8
				} else {
					var _t842 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t842 = 5
					} else {
						var _t843 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t843 = 2
						} else {
							var _t844 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t844 = 3
							} else {
								var _t845 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t845 = 7
								} else {
									var _t846 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t846 = 6
									} else {
										var _t847 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t847 = 10
										} else {
											var _t848 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t848 = 9
											} else {
												_t848 = -1
											}
											_t847 = _t848
										}
										_t846 = _t847
									}
									_t845 = _t846
								}
								_t844 = _t845
							}
							_t843 = _t844
						}
						_t842 = _t843
					}
					_t841 = _t842
				}
				_t840 = _t841
			}
			_t839 = _t840
		}
		_t838 = _t839
	}
	prediction433 := _t838
	var _t849 *pb.Type
	if prediction433 == 10 {
		_t850 := p.parse_boolean_type()
		boolean_type444 := _t850
		_t851 := &pb.Type{}
		_t851.Type = &pb.Type_BooleanType{BooleanType: boolean_type444}
		_t849 = _t851
	} else {
		var _t852 *pb.Type
		if prediction433 == 9 {
			_t853 := p.parse_decimal_type()
			decimal_type443 := _t853
			_t854 := &pb.Type{}
			_t854.Type = &pb.Type_DecimalType{DecimalType: decimal_type443}
			_t852 = _t854
		} else {
			var _t855 *pb.Type
			if prediction433 == 8 {
				_t856 := p.parse_missing_type()
				missing_type442 := _t856
				_t857 := &pb.Type{}
				_t857.Type = &pb.Type_MissingType{MissingType: missing_type442}
				_t855 = _t857
			} else {
				var _t858 *pb.Type
				if prediction433 == 7 {
					_t859 := p.parse_datetime_type()
					datetime_type441 := _t859
					_t860 := &pb.Type{}
					_t860.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type441}
					_t858 = _t860
				} else {
					var _t861 *pb.Type
					if prediction433 == 6 {
						_t862 := p.parse_date_type()
						date_type440 := _t862
						_t863 := &pb.Type{}
						_t863.Type = &pb.Type_DateType{DateType: date_type440}
						_t861 = _t863
					} else {
						var _t864 *pb.Type
						if prediction433 == 5 {
							_t865 := p.parse_int128_type()
							int128_type439 := _t865
							_t866 := &pb.Type{}
							_t866.Type = &pb.Type_Int128Type{Int128Type: int128_type439}
							_t864 = _t866
						} else {
							var _t867 *pb.Type
							if prediction433 == 4 {
								_t868 := p.parse_uint128_type()
								uint128_type438 := _t868
								_t869 := &pb.Type{}
								_t869.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type438}
								_t867 = _t869
							} else {
								var _t870 *pb.Type
								if prediction433 == 3 {
									_t871 := p.parse_float_type()
									float_type437 := _t871
									_t872 := &pb.Type{}
									_t872.Type = &pb.Type_FloatType{FloatType: float_type437}
									_t870 = _t872
								} else {
									var _t873 *pb.Type
									if prediction433 == 2 {
										_t874 := p.parse_int_type()
										int_type436 := _t874
										_t875 := &pb.Type{}
										_t875.Type = &pb.Type_IntType{IntType: int_type436}
										_t873 = _t875
									} else {
										var _t876 *pb.Type
										if prediction433 == 1 {
											_t877 := p.parse_string_type()
											string_type435 := _t877
											_t878 := &pb.Type{}
											_t878.Type = &pb.Type_StringType{StringType: string_type435}
											_t876 = _t878
										} else {
											var _t879 *pb.Type
											if prediction433 == 0 {
												_t880 := p.parse_unspecified_type()
												unspecified_type434 := _t880
												_t881 := &pb.Type{}
												_t881.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type434}
												_t879 = _t881
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t876 = _t879
										}
										_t873 = _t876
									}
									_t870 = _t873
								}
								_t867 = _t870
							}
							_t864 = _t867
						}
						_t861 = _t864
					}
					_t858 = _t861
				}
				_t855 = _t858
			}
			_t852 = _t855
		}
		_t849 = _t852
	}
	return _t849
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t882 := &pb.UnspecifiedType{}
	return _t882
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t883 := &pb.StringType{}
	return _t883
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t884 := &pb.IntType{}
	return _t884
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t885 := &pb.FloatType{}
	return _t885
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t886 := &pb.UInt128Type{}
	return _t886
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t887 := &pb.Int128Type{}
	return _t887
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t888 := &pb.DateType{}
	return _t888
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t889 := &pb.DateTimeType{}
	return _t889
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t890 := &pb.MissingType{}
	return _t890
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int445 := p.consumeTerminal("INT").Value.i64
	int_3446 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t891 := &pb.DecimalType{Precision: int32(int445), Scale: int32(int_3446)}
	return _t891
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t892 := &pb.BooleanType{}
	return _t892
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs447 := []*pb.Binding{}
	cond448 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond448 {
		_t893 := p.parse_binding()
		item449 := _t893
		xs447 = append(xs447, item449)
		cond448 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings450 := xs447
	return bindings450
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t894 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t895 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t895 = 0
		} else {
			var _t896 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t896 = 11
			} else {
				var _t897 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t897 = 3
				} else {
					var _t898 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t898 = 10
					} else {
						var _t899 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t899 = 9
						} else {
							var _t900 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t900 = 5
							} else {
								var _t901 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t901 = 6
								} else {
									var _t902 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t902 = 7
									} else {
										var _t903 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t903 = 1
										} else {
											var _t904 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t904 = 2
											} else {
												var _t905 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t905 = 12
												} else {
													var _t906 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t906 = 8
													} else {
														var _t907 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t907 = 4
														} else {
															var _t908 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t908 = 10
															} else {
																var _t909 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t909 = 10
																} else {
																	var _t910 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t910 = 10
																	} else {
																		var _t911 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t911 = 10
																		} else {
																			var _t912 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t912 = 10
																			} else {
																				var _t913 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t913 = 10
																				} else {
																					var _t914 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t914 = 10
																					} else {
																						var _t915 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t915 = 10
																						} else {
																							var _t916 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t916 = 10
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
	} else {
		_t894 = -1
	}
	prediction451 := _t894
	var _t917 *pb.Formula
	if prediction451 == 12 {
		_t918 := p.parse_cast()
		cast464 := _t918
		_t919 := &pb.Formula{}
		_t919.FormulaType = &pb.Formula_Cast{Cast: cast464}
		_t917 = _t919
	} else {
		var _t920 *pb.Formula
		if prediction451 == 11 {
			_t921 := p.parse_rel_atom()
			rel_atom463 := _t921
			_t922 := &pb.Formula{}
			_t922.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom463}
			_t920 = _t922
		} else {
			var _t923 *pb.Formula
			if prediction451 == 10 {
				_t924 := p.parse_primitive()
				primitive462 := _t924
				_t925 := &pb.Formula{}
				_t925.FormulaType = &pb.Formula_Primitive{Primitive: primitive462}
				_t923 = _t925
			} else {
				var _t926 *pb.Formula
				if prediction451 == 9 {
					_t927 := p.parse_pragma()
					pragma461 := _t927
					_t928 := &pb.Formula{}
					_t928.FormulaType = &pb.Formula_Pragma{Pragma: pragma461}
					_t926 = _t928
				} else {
					var _t929 *pb.Formula
					if prediction451 == 8 {
						_t930 := p.parse_atom()
						atom460 := _t930
						_t931 := &pb.Formula{}
						_t931.FormulaType = &pb.Formula_Atom{Atom: atom460}
						_t929 = _t931
					} else {
						var _t932 *pb.Formula
						if prediction451 == 7 {
							_t933 := p.parse_ffi()
							ffi459 := _t933
							_t934 := &pb.Formula{}
							_t934.FormulaType = &pb.Formula_Ffi{Ffi: ffi459}
							_t932 = _t934
						} else {
							var _t935 *pb.Formula
							if prediction451 == 6 {
								_t936 := p.parse_not()
								not458 := _t936
								_t937 := &pb.Formula{}
								_t937.FormulaType = &pb.Formula_Not{Not: not458}
								_t935 = _t937
							} else {
								var _t938 *pb.Formula
								if prediction451 == 5 {
									_t939 := p.parse_disjunction()
									disjunction457 := _t939
									_t940 := &pb.Formula{}
									_t940.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction457}
									_t938 = _t940
								} else {
									var _t941 *pb.Formula
									if prediction451 == 4 {
										_t942 := p.parse_conjunction()
										conjunction456 := _t942
										_t943 := &pb.Formula{}
										_t943.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction456}
										_t941 = _t943
									} else {
										var _t944 *pb.Formula
										if prediction451 == 3 {
											_t945 := p.parse_reduce()
											reduce455 := _t945
											_t946 := &pb.Formula{}
											_t946.FormulaType = &pb.Formula_Reduce{Reduce: reduce455}
											_t944 = _t946
										} else {
											var _t947 *pb.Formula
											if prediction451 == 2 {
												_t948 := p.parse_exists()
												exists454 := _t948
												_t949 := &pb.Formula{}
												_t949.FormulaType = &pb.Formula_Exists{Exists: exists454}
												_t947 = _t949
											} else {
												var _t950 *pb.Formula
												if prediction451 == 1 {
													_t951 := p.parse_false()
													false453 := _t951
													_t952 := &pb.Formula{}
													_t952.FormulaType = &pb.Formula_Disjunction{Disjunction: false453}
													_t950 = _t952
												} else {
													var _t953 *pb.Formula
													if prediction451 == 0 {
														_t954 := p.parse_true()
														true452 := _t954
														_t955 := &pb.Formula{}
														_t955.FormulaType = &pb.Formula_Conjunction{Conjunction: true452}
														_t953 = _t955
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t950 = _t953
												}
												_t947 = _t950
											}
											_t944 = _t947
										}
										_t941 = _t944
									}
									_t938 = _t941
								}
								_t935 = _t938
							}
							_t932 = _t935
						}
						_t929 = _t932
					}
					_t926 = _t929
				}
				_t923 = _t926
			}
			_t920 = _t923
		}
		_t917 = _t920
	}
	return _t917
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t956 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t956
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t957 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t957
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t958 := p.parse_bindings()
	bindings465 := _t958
	_t959 := p.parse_formula()
	formula466 := _t959
	p.consumeLiteral(")")
	_t960 := &pb.Abstraction{Vars: listConcat(bindings465[0].([]*pb.Binding), bindings465[1].([]*pb.Binding)), Value: formula466}
	_t961 := &pb.Exists{Body: _t960}
	return _t961
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t962 := p.parse_abstraction()
	abstraction467 := _t962
	_t963 := p.parse_abstraction()
	abstraction_3468 := _t963
	_t964 := p.parse_terms()
	terms469 := _t964
	p.consumeLiteral(")")
	_t965 := &pb.Reduce{Op: abstraction467, Body: abstraction_3468, Terms: terms469}
	return _t965
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs470 := []*pb.Term{}
	cond471 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond471 {
		_t966 := p.parse_term()
		item472 := _t966
		xs470 = append(xs470, item472)
		cond471 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms473 := xs470
	p.consumeLiteral(")")
	return terms473
}

func (p *Parser) parse_term() *pb.Term {
	var _t967 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t967 = 1
	} else {
		var _t968 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t968 = 1
		} else {
			var _t969 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t969 = 1
			} else {
				var _t970 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t970 = 1
				} else {
					var _t971 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t971 = 1
					} else {
						var _t972 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t972 = 0
						} else {
							var _t973 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t973 = 1
							} else {
								var _t974 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t974 = 1
								} else {
									var _t975 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t975 = 1
									} else {
										var _t976 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t976 = 1
										} else {
											var _t977 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t977 = 1
											} else {
												_t977 = -1
											}
											_t976 = _t977
										}
										_t975 = _t976
									}
									_t974 = _t975
								}
								_t973 = _t974
							}
							_t972 = _t973
						}
						_t971 = _t972
					}
					_t970 = _t971
				}
				_t969 = _t970
			}
			_t968 = _t969
		}
		_t967 = _t968
	}
	prediction474 := _t967
	var _t978 *pb.Term
	if prediction474 == 1 {
		_t979 := p.parse_constant()
		constant476 := _t979
		_t980 := &pb.Term{}
		_t980.TermType = &pb.Term_Constant{Constant: constant476}
		_t978 = _t980
	} else {
		var _t981 *pb.Term
		if prediction474 == 0 {
			_t982 := p.parse_var()
			var475 := _t982
			_t983 := &pb.Term{}
			_t983.TermType = &pb.Term_Var{Var: var475}
			_t981 = _t983
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t978 = _t981
	}
	return _t978
}

func (p *Parser) parse_var() *pb.Var {
	symbol477 := p.consumeTerminal("SYMBOL").Value.str
	_t984 := &pb.Var{Name: symbol477}
	return _t984
}

func (p *Parser) parse_constant() *pb.Value {
	_t985 := p.parse_value()
	value478 := _t985
	return value478
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs479 := []*pb.Formula{}
	cond480 := p.matchLookaheadLiteral("(", 0)
	for cond480 {
		_t986 := p.parse_formula()
		item481 := _t986
		xs479 = append(xs479, item481)
		cond480 = p.matchLookaheadLiteral("(", 0)
	}
	formulas482 := xs479
	p.consumeLiteral(")")
	_t987 := &pb.Conjunction{Args: formulas482}
	return _t987
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs483 := []*pb.Formula{}
	cond484 := p.matchLookaheadLiteral("(", 0)
	for cond484 {
		_t988 := p.parse_formula()
		item485 := _t988
		xs483 = append(xs483, item485)
		cond484 = p.matchLookaheadLiteral("(", 0)
	}
	formulas486 := xs483
	p.consumeLiteral(")")
	_t989 := &pb.Disjunction{Args: formulas486}
	return _t989
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t990 := p.parse_formula()
	formula487 := _t990
	p.consumeLiteral(")")
	_t991 := &pb.Not{Arg: formula487}
	return _t991
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t992 := p.parse_name()
	name488 := _t992
	_t993 := p.parse_ffi_args()
	ffi_args489 := _t993
	_t994 := p.parse_terms()
	terms490 := _t994
	p.consumeLiteral(")")
	_t995 := &pb.FFI{Name: name488, Args: ffi_args489, Terms: terms490}
	return _t995
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol491 := p.consumeTerminal("SYMBOL").Value.str
	return symbol491
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs492 := []*pb.Abstraction{}
	cond493 := p.matchLookaheadLiteral("(", 0)
	for cond493 {
		_t996 := p.parse_abstraction()
		item494 := _t996
		xs492 = append(xs492, item494)
		cond493 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions495 := xs492
	p.consumeLiteral(")")
	return abstractions495
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t997 := p.parse_relation_id()
	relation_id496 := _t997
	xs497 := []*pb.Term{}
	cond498 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond498 {
		_t998 := p.parse_term()
		item499 := _t998
		xs497 = append(xs497, item499)
		cond498 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms500 := xs497
	p.consumeLiteral(")")
	_t999 := &pb.Atom{Name: relation_id496, Terms: terms500}
	return _t999
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1000 := p.parse_name()
	name501 := _t1000
	xs502 := []*pb.Term{}
	cond503 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond503 {
		_t1001 := p.parse_term()
		item504 := _t1001
		xs502 = append(xs502, item504)
		cond503 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms505 := xs502
	p.consumeLiteral(")")
	_t1002 := &pb.Pragma{Name: name501, Terms: terms505}
	return _t1002
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1003 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1004 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1004 = 9
		} else {
			var _t1005 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1005 = 4
			} else {
				var _t1006 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1006 = 3
				} else {
					var _t1007 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1007 = 0
					} else {
						var _t1008 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1008 = 2
						} else {
							var _t1009 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1009 = 1
							} else {
								var _t1010 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1010 = 8
								} else {
									var _t1011 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1011 = 6
									} else {
										var _t1012 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1012 = 5
										} else {
											var _t1013 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1013 = 7
											} else {
												_t1013 = -1
											}
											_t1012 = _t1013
										}
										_t1011 = _t1012
									}
									_t1010 = _t1011
								}
								_t1009 = _t1010
							}
							_t1008 = _t1009
						}
						_t1007 = _t1008
					}
					_t1006 = _t1007
				}
				_t1005 = _t1006
			}
			_t1004 = _t1005
		}
		_t1003 = _t1004
	} else {
		_t1003 = -1
	}
	prediction506 := _t1003
	var _t1014 *pb.Primitive
	if prediction506 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1015 := p.parse_name()
		name516 := _t1015
		xs517 := []*pb.RelTerm{}
		cond518 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond518 {
			_t1016 := p.parse_rel_term()
			item519 := _t1016
			xs517 = append(xs517, item519)
			cond518 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms520 := xs517
		p.consumeLiteral(")")
		_t1017 := &pb.Primitive{Name: name516, Terms: rel_terms520}
		_t1014 = _t1017
	} else {
		var _t1018 *pb.Primitive
		if prediction506 == 8 {
			_t1019 := p.parse_divide()
			divide515 := _t1019
			_t1018 = divide515
		} else {
			var _t1020 *pb.Primitive
			if prediction506 == 7 {
				_t1021 := p.parse_multiply()
				multiply514 := _t1021
				_t1020 = multiply514
			} else {
				var _t1022 *pb.Primitive
				if prediction506 == 6 {
					_t1023 := p.parse_minus()
					minus513 := _t1023
					_t1022 = minus513
				} else {
					var _t1024 *pb.Primitive
					if prediction506 == 5 {
						_t1025 := p.parse_add()
						add512 := _t1025
						_t1024 = add512
					} else {
						var _t1026 *pb.Primitive
						if prediction506 == 4 {
							_t1027 := p.parse_gt_eq()
							gt_eq511 := _t1027
							_t1026 = gt_eq511
						} else {
							var _t1028 *pb.Primitive
							if prediction506 == 3 {
								_t1029 := p.parse_gt()
								gt510 := _t1029
								_t1028 = gt510
							} else {
								var _t1030 *pb.Primitive
								if prediction506 == 2 {
									_t1031 := p.parse_lt_eq()
									lt_eq509 := _t1031
									_t1030 = lt_eq509
								} else {
									var _t1032 *pb.Primitive
									if prediction506 == 1 {
										_t1033 := p.parse_lt()
										lt508 := _t1033
										_t1032 = lt508
									} else {
										var _t1034 *pb.Primitive
										if prediction506 == 0 {
											_t1035 := p.parse_eq()
											eq507 := _t1035
											_t1034 = eq507
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1032 = _t1034
									}
									_t1030 = _t1032
								}
								_t1028 = _t1030
							}
							_t1026 = _t1028
						}
						_t1024 = _t1026
					}
					_t1022 = _t1024
				}
				_t1020 = _t1022
			}
			_t1018 = _t1020
		}
		_t1014 = _t1018
	}
	return _t1014
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1036 := p.parse_term()
	term521 := _t1036
	_t1037 := p.parse_term()
	term_3522 := _t1037
	p.consumeLiteral(")")
	_t1038 := &pb.RelTerm{}
	_t1038.RelTermType = &pb.RelTerm_Term{Term: term521}
	_t1039 := &pb.RelTerm{}
	_t1039.RelTermType = &pb.RelTerm_Term{Term: term_3522}
	_t1040 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1038, _t1039}}
	return _t1040
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1041 := p.parse_term()
	term523 := _t1041
	_t1042 := p.parse_term()
	term_3524 := _t1042
	p.consumeLiteral(")")
	_t1043 := &pb.RelTerm{}
	_t1043.RelTermType = &pb.RelTerm_Term{Term: term523}
	_t1044 := &pb.RelTerm{}
	_t1044.RelTermType = &pb.RelTerm_Term{Term: term_3524}
	_t1045 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1043, _t1044}}
	return _t1045
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1046 := p.parse_term()
	term525 := _t1046
	_t1047 := p.parse_term()
	term_3526 := _t1047
	p.consumeLiteral(")")
	_t1048 := &pb.RelTerm{}
	_t1048.RelTermType = &pb.RelTerm_Term{Term: term525}
	_t1049 := &pb.RelTerm{}
	_t1049.RelTermType = &pb.RelTerm_Term{Term: term_3526}
	_t1050 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1048, _t1049}}
	return _t1050
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1051 := p.parse_term()
	term527 := _t1051
	_t1052 := p.parse_term()
	term_3528 := _t1052
	p.consumeLiteral(")")
	_t1053 := &pb.RelTerm{}
	_t1053.RelTermType = &pb.RelTerm_Term{Term: term527}
	_t1054 := &pb.RelTerm{}
	_t1054.RelTermType = &pb.RelTerm_Term{Term: term_3528}
	_t1055 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1053, _t1054}}
	return _t1055
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1056 := p.parse_term()
	term529 := _t1056
	_t1057 := p.parse_term()
	term_3530 := _t1057
	p.consumeLiteral(")")
	_t1058 := &pb.RelTerm{}
	_t1058.RelTermType = &pb.RelTerm_Term{Term: term529}
	_t1059 := &pb.RelTerm{}
	_t1059.RelTermType = &pb.RelTerm_Term{Term: term_3530}
	_t1060 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1058, _t1059}}
	return _t1060
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1061 := p.parse_term()
	term531 := _t1061
	_t1062 := p.parse_term()
	term_3532 := _t1062
	_t1063 := p.parse_term()
	term_4533 := _t1063
	p.consumeLiteral(")")
	_t1064 := &pb.RelTerm{}
	_t1064.RelTermType = &pb.RelTerm_Term{Term: term531}
	_t1065 := &pb.RelTerm{}
	_t1065.RelTermType = &pb.RelTerm_Term{Term: term_3532}
	_t1066 := &pb.RelTerm{}
	_t1066.RelTermType = &pb.RelTerm_Term{Term: term_4533}
	_t1067 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1064, _t1065, _t1066}}
	return _t1067
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1068 := p.parse_term()
	term534 := _t1068
	_t1069 := p.parse_term()
	term_3535 := _t1069
	_t1070 := p.parse_term()
	term_4536 := _t1070
	p.consumeLiteral(")")
	_t1071 := &pb.RelTerm{}
	_t1071.RelTermType = &pb.RelTerm_Term{Term: term534}
	_t1072 := &pb.RelTerm{}
	_t1072.RelTermType = &pb.RelTerm_Term{Term: term_3535}
	_t1073 := &pb.RelTerm{}
	_t1073.RelTermType = &pb.RelTerm_Term{Term: term_4536}
	_t1074 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1071, _t1072, _t1073}}
	return _t1074
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1075 := p.parse_term()
	term537 := _t1075
	_t1076 := p.parse_term()
	term_3538 := _t1076
	_t1077 := p.parse_term()
	term_4539 := _t1077
	p.consumeLiteral(")")
	_t1078 := &pb.RelTerm{}
	_t1078.RelTermType = &pb.RelTerm_Term{Term: term537}
	_t1079 := &pb.RelTerm{}
	_t1079.RelTermType = &pb.RelTerm_Term{Term: term_3538}
	_t1080 := &pb.RelTerm{}
	_t1080.RelTermType = &pb.RelTerm_Term{Term: term_4539}
	_t1081 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1078, _t1079, _t1080}}
	return _t1081
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1082 := p.parse_term()
	term540 := _t1082
	_t1083 := p.parse_term()
	term_3541 := _t1083
	_t1084 := p.parse_term()
	term_4542 := _t1084
	p.consumeLiteral(")")
	_t1085 := &pb.RelTerm{}
	_t1085.RelTermType = &pb.RelTerm_Term{Term: term540}
	_t1086 := &pb.RelTerm{}
	_t1086.RelTermType = &pb.RelTerm_Term{Term: term_3541}
	_t1087 := &pb.RelTerm{}
	_t1087.RelTermType = &pb.RelTerm_Term{Term: term_4542}
	_t1088 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1085, _t1086, _t1087}}
	return _t1088
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1089 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1089 = 1
	} else {
		var _t1090 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1090 = 1
		} else {
			var _t1091 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1091 = 1
			} else {
				var _t1092 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1092 = 1
				} else {
					var _t1093 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1093 = 0
					} else {
						var _t1094 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1094 = 1
						} else {
							var _t1095 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1095 = 1
							} else {
								var _t1096 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1096 = 1
								} else {
									var _t1097 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1097 = 1
									} else {
										var _t1098 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1098 = 1
										} else {
											var _t1099 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1099 = 1
											} else {
												var _t1100 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1100 = 1
												} else {
													_t1100 = -1
												}
												_t1099 = _t1100
											}
											_t1098 = _t1099
										}
										_t1097 = _t1098
									}
									_t1096 = _t1097
								}
								_t1095 = _t1096
							}
							_t1094 = _t1095
						}
						_t1093 = _t1094
					}
					_t1092 = _t1093
				}
				_t1091 = _t1092
			}
			_t1090 = _t1091
		}
		_t1089 = _t1090
	}
	prediction543 := _t1089
	var _t1101 *pb.RelTerm
	if prediction543 == 1 {
		_t1102 := p.parse_term()
		term545 := _t1102
		_t1103 := &pb.RelTerm{}
		_t1103.RelTermType = &pb.RelTerm_Term{Term: term545}
		_t1101 = _t1103
	} else {
		var _t1104 *pb.RelTerm
		if prediction543 == 0 {
			_t1105 := p.parse_specialized_value()
			specialized_value544 := _t1105
			_t1106 := &pb.RelTerm{}
			_t1106.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value544}
			_t1104 = _t1106
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1101 = _t1104
	}
	return _t1101
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1107 := p.parse_value()
	value546 := _t1107
	return value546
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1108 := p.parse_name()
	name547 := _t1108
	xs548 := []*pb.RelTerm{}
	cond549 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond549 {
		_t1109 := p.parse_rel_term()
		item550 := _t1109
		xs548 = append(xs548, item550)
		cond549 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms551 := xs548
	p.consumeLiteral(")")
	_t1110 := &pb.RelAtom{Name: name547, Terms: rel_terms551}
	return _t1110
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1111 := p.parse_term()
	term552 := _t1111
	_t1112 := p.parse_term()
	term_3553 := _t1112
	p.consumeLiteral(")")
	_t1113 := &pb.Cast{Input: term552, Result: term_3553}
	return _t1113
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs554 := []*pb.Attribute{}
	cond555 := p.matchLookaheadLiteral("(", 0)
	for cond555 {
		_t1114 := p.parse_attribute()
		item556 := _t1114
		xs554 = append(xs554, item556)
		cond555 = p.matchLookaheadLiteral("(", 0)
	}
	attributes557 := xs554
	p.consumeLiteral(")")
	return attributes557
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1115 := p.parse_name()
	name558 := _t1115
	xs559 := []*pb.Value{}
	cond560 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond560 {
		_t1116 := p.parse_value()
		item561 := _t1116
		xs559 = append(xs559, item561)
		cond560 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values562 := xs559
	p.consumeLiteral(")")
	_t1117 := &pb.Attribute{Name: name558, Args: values562}
	return _t1117
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs563 := []*pb.RelationId{}
	cond564 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond564 {
		_t1118 := p.parse_relation_id()
		item565 := _t1118
		xs563 = append(xs563, item565)
		cond564 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids566 := xs563
	_t1119 := p.parse_script()
	script567 := _t1119
	p.consumeLiteral(")")
	_t1120 := &pb.Algorithm{Global: relation_ids566, Body: script567}
	return _t1120
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs568 := []*pb.Construct{}
	cond569 := p.matchLookaheadLiteral("(", 0)
	for cond569 {
		_t1121 := p.parse_construct()
		item570 := _t1121
		xs568 = append(xs568, item570)
		cond569 = p.matchLookaheadLiteral("(", 0)
	}
	constructs571 := xs568
	p.consumeLiteral(")")
	_t1122 := &pb.Script{Constructs: constructs571}
	return _t1122
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1123 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1124 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1124 = 1
		} else {
			var _t1125 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1125 = 1
			} else {
				var _t1126 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1126 = 1
				} else {
					var _t1127 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1127 = 0
					} else {
						var _t1128 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1128 = 1
						} else {
							var _t1129 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1129 = 1
							} else {
								_t1129 = -1
							}
							_t1128 = _t1129
						}
						_t1127 = _t1128
					}
					_t1126 = _t1127
				}
				_t1125 = _t1126
			}
			_t1124 = _t1125
		}
		_t1123 = _t1124
	} else {
		_t1123 = -1
	}
	prediction572 := _t1123
	var _t1130 *pb.Construct
	if prediction572 == 1 {
		_t1131 := p.parse_instruction()
		instruction574 := _t1131
		_t1132 := &pb.Construct{}
		_t1132.ConstructType = &pb.Construct_Instruction{Instruction: instruction574}
		_t1130 = _t1132
	} else {
		var _t1133 *pb.Construct
		if prediction572 == 0 {
			_t1134 := p.parse_loop()
			loop573 := _t1134
			_t1135 := &pb.Construct{}
			_t1135.ConstructType = &pb.Construct_Loop{Loop: loop573}
			_t1133 = _t1135
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1130 = _t1133
	}
	return _t1130
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1136 := p.parse_init()
	init575 := _t1136
	_t1137 := p.parse_script()
	script576 := _t1137
	p.consumeLiteral(")")
	_t1138 := &pb.Loop{Init: init575, Body: script576}
	return _t1138
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs577 := []*pb.Instruction{}
	cond578 := p.matchLookaheadLiteral("(", 0)
	for cond578 {
		_t1139 := p.parse_instruction()
		item579 := _t1139
		xs577 = append(xs577, item579)
		cond578 = p.matchLookaheadLiteral("(", 0)
	}
	instructions580 := xs577
	p.consumeLiteral(")")
	return instructions580
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1140 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1141 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1141 = 1
		} else {
			var _t1142 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1142 = 4
			} else {
				var _t1143 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1143 = 3
				} else {
					var _t1144 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1144 = 2
					} else {
						var _t1145 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1145 = 0
						} else {
							_t1145 = -1
						}
						_t1144 = _t1145
					}
					_t1143 = _t1144
				}
				_t1142 = _t1143
			}
			_t1141 = _t1142
		}
		_t1140 = _t1141
	} else {
		_t1140 = -1
	}
	prediction581 := _t1140
	var _t1146 *pb.Instruction
	if prediction581 == 4 {
		_t1147 := p.parse_monus_def()
		monus_def586 := _t1147
		_t1148 := &pb.Instruction{}
		_t1148.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def586}
		_t1146 = _t1148
	} else {
		var _t1149 *pb.Instruction
		if prediction581 == 3 {
			_t1150 := p.parse_monoid_def()
			monoid_def585 := _t1150
			_t1151 := &pb.Instruction{}
			_t1151.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def585}
			_t1149 = _t1151
		} else {
			var _t1152 *pb.Instruction
			if prediction581 == 2 {
				_t1153 := p.parse_break()
				break584 := _t1153
				_t1154 := &pb.Instruction{}
				_t1154.InstrType = &pb.Instruction_Break{Break: break584}
				_t1152 = _t1154
			} else {
				var _t1155 *pb.Instruction
				if prediction581 == 1 {
					_t1156 := p.parse_upsert()
					upsert583 := _t1156
					_t1157 := &pb.Instruction{}
					_t1157.InstrType = &pb.Instruction_Upsert{Upsert: upsert583}
					_t1155 = _t1157
				} else {
					var _t1158 *pb.Instruction
					if prediction581 == 0 {
						_t1159 := p.parse_assign()
						assign582 := _t1159
						_t1160 := &pb.Instruction{}
						_t1160.InstrType = &pb.Instruction_Assign{Assign: assign582}
						_t1158 = _t1160
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1155 = _t1158
				}
				_t1152 = _t1155
			}
			_t1149 = _t1152
		}
		_t1146 = _t1149
	}
	return _t1146
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1161 := p.parse_relation_id()
	relation_id587 := _t1161
	_t1162 := p.parse_abstraction()
	abstraction588 := _t1162
	var _t1163 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1164 := p.parse_attrs()
		_t1163 = _t1164
	}
	attrs589 := _t1163
	p.consumeLiteral(")")
	_t1165 := attrs589
	if attrs589 == nil {
		_t1165 = []*pb.Attribute{}
	}
	_t1166 := &pb.Assign{Name: relation_id587, Body: abstraction588, Attrs: _t1165}
	return _t1166
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1167 := p.parse_relation_id()
	relation_id590 := _t1167
	_t1168 := p.parse_abstraction_with_arity()
	abstraction_with_arity591 := _t1168
	var _t1169 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1170 := p.parse_attrs()
		_t1169 = _t1170
	}
	attrs592 := _t1169
	p.consumeLiteral(")")
	_t1171 := attrs592
	if attrs592 == nil {
		_t1171 = []*pb.Attribute{}
	}
	_t1172 := &pb.Upsert{Name: relation_id590, Body: abstraction_with_arity591[0].(*pb.Abstraction), Attrs: _t1171, ValueArity: abstraction_with_arity591[1].(int64)}
	return _t1172
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1173 := p.parse_bindings()
	bindings593 := _t1173
	_t1174 := p.parse_formula()
	formula594 := _t1174
	p.consumeLiteral(")")
	_t1175 := &pb.Abstraction{Vars: listConcat(bindings593[0].([]*pb.Binding), bindings593[1].([]*pb.Binding)), Value: formula594}
	return []interface{}{_t1175, int64(len(bindings593[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1176 := p.parse_relation_id()
	relation_id595 := _t1176
	_t1177 := p.parse_abstraction()
	abstraction596 := _t1177
	var _t1178 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1179 := p.parse_attrs()
		_t1178 = _t1179
	}
	attrs597 := _t1178
	p.consumeLiteral(")")
	_t1180 := attrs597
	if attrs597 == nil {
		_t1180 = []*pb.Attribute{}
	}
	_t1181 := &pb.Break{Name: relation_id595, Body: abstraction596, Attrs: _t1180}
	return _t1181
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1182 := p.parse_monoid()
	monoid598 := _t1182
	_t1183 := p.parse_relation_id()
	relation_id599 := _t1183
	_t1184 := p.parse_abstraction_with_arity()
	abstraction_with_arity600 := _t1184
	var _t1185 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1186 := p.parse_attrs()
		_t1185 = _t1186
	}
	attrs601 := _t1185
	p.consumeLiteral(")")
	_t1187 := attrs601
	if attrs601 == nil {
		_t1187 = []*pb.Attribute{}
	}
	_t1188 := &pb.MonoidDef{Monoid: monoid598, Name: relation_id599, Body: abstraction_with_arity600[0].(*pb.Abstraction), Attrs: _t1187, ValueArity: abstraction_with_arity600[1].(int64)}
	return _t1188
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1189 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1190 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1190 = 3
		} else {
			var _t1191 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1191 = 0
			} else {
				var _t1192 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1192 = 1
				} else {
					var _t1193 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1193 = 2
					} else {
						_t1193 = -1
					}
					_t1192 = _t1193
				}
				_t1191 = _t1192
			}
			_t1190 = _t1191
		}
		_t1189 = _t1190
	} else {
		_t1189 = -1
	}
	prediction602 := _t1189
	var _t1194 *pb.Monoid
	if prediction602 == 3 {
		_t1195 := p.parse_sum_monoid()
		sum_monoid606 := _t1195
		_t1196 := &pb.Monoid{}
		_t1196.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid606}
		_t1194 = _t1196
	} else {
		var _t1197 *pb.Monoid
		if prediction602 == 2 {
			_t1198 := p.parse_max_monoid()
			max_monoid605 := _t1198
			_t1199 := &pb.Monoid{}
			_t1199.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid605}
			_t1197 = _t1199
		} else {
			var _t1200 *pb.Monoid
			if prediction602 == 1 {
				_t1201 := p.parse_min_monoid()
				min_monoid604 := _t1201
				_t1202 := &pb.Monoid{}
				_t1202.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid604}
				_t1200 = _t1202
			} else {
				var _t1203 *pb.Monoid
				if prediction602 == 0 {
					_t1204 := p.parse_or_monoid()
					or_monoid603 := _t1204
					_t1205 := &pb.Monoid{}
					_t1205.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid603}
					_t1203 = _t1205
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1200 = _t1203
			}
			_t1197 = _t1200
		}
		_t1194 = _t1197
	}
	return _t1194
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1206 := &pb.OrMonoid{}
	return _t1206
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1207 := p.parse_type()
	type607 := _t1207
	p.consumeLiteral(")")
	_t1208 := &pb.MinMonoid{Type: type607}
	return _t1208
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1209 := p.parse_type()
	type608 := _t1209
	p.consumeLiteral(")")
	_t1210 := &pb.MaxMonoid{Type: type608}
	return _t1210
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1211 := p.parse_type()
	type609 := _t1211
	p.consumeLiteral(")")
	_t1212 := &pb.SumMonoid{Type: type609}
	return _t1212
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1213 := p.parse_monoid()
	monoid610 := _t1213
	_t1214 := p.parse_relation_id()
	relation_id611 := _t1214
	_t1215 := p.parse_abstraction_with_arity()
	abstraction_with_arity612 := _t1215
	var _t1216 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1217 := p.parse_attrs()
		_t1216 = _t1217
	}
	attrs613 := _t1216
	p.consumeLiteral(")")
	_t1218 := attrs613
	if attrs613 == nil {
		_t1218 = []*pb.Attribute{}
	}
	_t1219 := &pb.MonusDef{Monoid: monoid610, Name: relation_id611, Body: abstraction_with_arity612[0].(*pb.Abstraction), Attrs: _t1218, ValueArity: abstraction_with_arity612[1].(int64)}
	return _t1219
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1220 := p.parse_relation_id()
	relation_id614 := _t1220
	_t1221 := p.parse_abstraction()
	abstraction615 := _t1221
	_t1222 := p.parse_functional_dependency_keys()
	functional_dependency_keys616 := _t1222
	_t1223 := p.parse_functional_dependency_values()
	functional_dependency_values617 := _t1223
	p.consumeLiteral(")")
	_t1224 := &pb.FunctionalDependency{Guard: abstraction615, Keys: functional_dependency_keys616, Values: functional_dependency_values617}
	_t1225 := &pb.Constraint{Name: relation_id614}
	_t1225.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1224}
	return _t1225
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs618 := []*pb.Var{}
	cond619 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond619 {
		_t1226 := p.parse_var()
		item620 := _t1226
		xs618 = append(xs618, item620)
		cond619 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars621 := xs618
	p.consumeLiteral(")")
	return vars621
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs622 := []*pb.Var{}
	cond623 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond623 {
		_t1227 := p.parse_var()
		item624 := _t1227
		xs622 = append(xs622, item624)
		cond623 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars625 := xs622
	p.consumeLiteral(")")
	return vars625
}

func (p *Parser) parse_data() *pb.Data {
	var _t1228 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1229 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1229 = 0
		} else {
			var _t1230 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1230 = 2
			} else {
				var _t1231 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1231 = 1
				} else {
					_t1231 = -1
				}
				_t1230 = _t1231
			}
			_t1229 = _t1230
		}
		_t1228 = _t1229
	} else {
		_t1228 = -1
	}
	prediction626 := _t1228
	var _t1232 *pb.Data
	if prediction626 == 2 {
		_t1233 := p.parse_csv_data()
		csv_data629 := _t1233
		_t1234 := &pb.Data{}
		_t1234.DataType = &pb.Data_CsvData{CsvData: csv_data629}
		_t1232 = _t1234
	} else {
		var _t1235 *pb.Data
		if prediction626 == 1 {
			_t1236 := p.parse_betree_relation()
			betree_relation628 := _t1236
			_t1237 := &pb.Data{}
			_t1237.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation628}
			_t1235 = _t1237
		} else {
			var _t1238 *pb.Data
			if prediction626 == 0 {
				_t1239 := p.parse_rel_edb()
				rel_edb627 := _t1239
				_t1240 := &pb.Data{}
				_t1240.DataType = &pb.Data_RelEdb{RelEdb: rel_edb627}
				_t1238 = _t1240
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1235 = _t1238
		}
		_t1232 = _t1235
	}
	return _t1232
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1241 := p.parse_relation_id()
	relation_id630 := _t1241
	_t1242 := p.parse_rel_edb_path()
	rel_edb_path631 := _t1242
	_t1243 := p.parse_rel_edb_types()
	rel_edb_types632 := _t1243
	p.consumeLiteral(")")
	_t1244 := &pb.RelEDB{TargetId: relation_id630, Path: rel_edb_path631, Types: rel_edb_types632}
	return _t1244
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs633 := []string{}
	cond634 := p.matchLookaheadTerminal("STRING", 0)
	for cond634 {
		item635 := p.consumeTerminal("STRING").Value.str
		xs633 = append(xs633, item635)
		cond634 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings636 := xs633
	p.consumeLiteral("]")
	return strings636
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs637 := []*pb.Type{}
	cond638 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond638 {
		_t1245 := p.parse_type()
		item639 := _t1245
		xs637 = append(xs637, item639)
		cond638 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types640 := xs637
	p.consumeLiteral("]")
	return types640
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1246 := p.parse_relation_id()
	relation_id641 := _t1246
	_t1247 := p.parse_betree_info()
	betree_info642 := _t1247
	p.consumeLiteral(")")
	_t1248 := &pb.BeTreeRelation{Name: relation_id641, RelationInfo: betree_info642}
	return _t1248
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1249 := p.parse_betree_info_key_types()
	betree_info_key_types643 := _t1249
	_t1250 := p.parse_betree_info_value_types()
	betree_info_value_types644 := _t1250
	_t1251 := p.parse_config_dict()
	config_dict645 := _t1251
	p.consumeLiteral(")")
	_t1252 := p.construct_betree_info(betree_info_key_types643, betree_info_value_types644, config_dict645)
	return _t1252
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs646 := []*pb.Type{}
	cond647 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond647 {
		_t1253 := p.parse_type()
		item648 := _t1253
		xs646 = append(xs646, item648)
		cond647 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types649 := xs646
	p.consumeLiteral(")")
	return types649
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs650 := []*pb.Type{}
	cond651 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond651 {
		_t1254 := p.parse_type()
		item652 := _t1254
		xs650 = append(xs650, item652)
		cond651 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types653 := xs650
	p.consumeLiteral(")")
	return types653
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1255 := p.parse_csvlocator()
	csvlocator654 := _t1255
	_t1256 := p.parse_csv_config()
	csv_config655 := _t1256
	_t1257 := p.parse_csv_columns()
	csv_columns656 := _t1257
	_t1258 := p.parse_csv_asof()
	csv_asof657 := _t1258
	p.consumeLiteral(")")
	_t1259 := &pb.CSVData{Locator: csvlocator654, Config: csv_config655, Columns: csv_columns656, Asof: csv_asof657}
	return _t1259
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1260 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1261 := p.parse_csv_locator_paths()
		_t1260 = _t1261
	}
	csv_locator_paths658 := _t1260
	var _t1262 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1263 := p.parse_csv_locator_inline_data()
		_t1262 = ptr(_t1263)
	}
	csv_locator_inline_data659 := _t1262
	p.consumeLiteral(")")
	_t1264 := csv_locator_paths658
	if csv_locator_paths658 == nil {
		_t1264 = []string{}
	}
	_t1265 := &pb.CSVLocator{Paths: _t1264, InlineData: []byte(deref(csv_locator_inline_data659, ""))}
	return _t1265
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs660 := []string{}
	cond661 := p.matchLookaheadTerminal("STRING", 0)
	for cond661 {
		item662 := p.consumeTerminal("STRING").Value.str
		xs660 = append(xs660, item662)
		cond661 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings663 := xs660
	p.consumeLiteral(")")
	return strings663
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string664 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string664
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1266 := p.parse_config_dict()
	config_dict665 := _t1266
	p.consumeLiteral(")")
	_t1267 := p.construct_csv_config(config_dict665)
	return _t1267
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs666 := []*pb.CSVColumn{}
	cond667 := p.matchLookaheadLiteral("(", 0)
	for cond667 {
		_t1268 := p.parse_csv_column()
		item668 := _t1268
		xs666 = append(xs666, item668)
		cond667 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns669 := xs666
	p.consumeLiteral(")")
	return csv_columns669
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string670 := p.consumeTerminal("STRING").Value.str
	_t1269 := p.parse_relation_id()
	relation_id671 := _t1269
	p.consumeLiteral("[")
	xs672 := []*pb.Type{}
	cond673 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond673 {
		_t1270 := p.parse_type()
		item674 := _t1270
		xs672 = append(xs672, item674)
		cond673 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types675 := xs672
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1271 := &pb.CSVColumn{ColumnName: string670, TargetId: relation_id671, Types: types675}
	return _t1271
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string676 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string676
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1272 := p.parse_fragment_id()
	fragment_id677 := _t1272
	p.consumeLiteral(")")
	_t1273 := &pb.Undefine{FragmentId: fragment_id677}
	return _t1273
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs678 := []*pb.RelationId{}
	cond679 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond679 {
		_t1274 := p.parse_relation_id()
		item680 := _t1274
		xs678 = append(xs678, item680)
		cond679 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids681 := xs678
	p.consumeLiteral(")")
	_t1275 := &pb.Context{Relations: relation_ids681}
	return _t1275
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1276 := p.parse_rel_edb_path()
	rel_edb_path682 := _t1276
	_t1277 := p.parse_relation_id()
	relation_id683 := _t1277
	p.consumeLiteral(")")
	_t1278 := &pb.Snapshot{DestinationPath: rel_edb_path682, SourceRelation: relation_id683}
	return _t1278
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs684 := []*pb.Read{}
	cond685 := p.matchLookaheadLiteral("(", 0)
	for cond685 {
		_t1279 := p.parse_read()
		item686 := _t1279
		xs684 = append(xs684, item686)
		cond685 = p.matchLookaheadLiteral("(", 0)
	}
	reads687 := xs684
	p.consumeLiteral(")")
	return reads687
}

func (p *Parser) parse_read() *pb.Read {
	var _t1280 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1281 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1281 = 2
		} else {
			var _t1282 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1282 = 1
			} else {
				var _t1283 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1283 = 4
				} else {
					var _t1284 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1284 = 0
					} else {
						var _t1285 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1285 = 3
						} else {
							_t1285 = -1
						}
						_t1284 = _t1285
					}
					_t1283 = _t1284
				}
				_t1282 = _t1283
			}
			_t1281 = _t1282
		}
		_t1280 = _t1281
	} else {
		_t1280 = -1
	}
	prediction688 := _t1280
	var _t1286 *pb.Read
	if prediction688 == 4 {
		_t1287 := p.parse_export()
		export693 := _t1287
		_t1288 := &pb.Read{}
		_t1288.ReadType = &pb.Read_Export{Export: export693}
		_t1286 = _t1288
	} else {
		var _t1289 *pb.Read
		if prediction688 == 3 {
			_t1290 := p.parse_abort()
			abort692 := _t1290
			_t1291 := &pb.Read{}
			_t1291.ReadType = &pb.Read_Abort{Abort: abort692}
			_t1289 = _t1291
		} else {
			var _t1292 *pb.Read
			if prediction688 == 2 {
				_t1293 := p.parse_what_if()
				what_if691 := _t1293
				_t1294 := &pb.Read{}
				_t1294.ReadType = &pb.Read_WhatIf{WhatIf: what_if691}
				_t1292 = _t1294
			} else {
				var _t1295 *pb.Read
				if prediction688 == 1 {
					_t1296 := p.parse_output()
					output690 := _t1296
					_t1297 := &pb.Read{}
					_t1297.ReadType = &pb.Read_Output{Output: output690}
					_t1295 = _t1297
				} else {
					var _t1298 *pb.Read
					if prediction688 == 0 {
						_t1299 := p.parse_demand()
						demand689 := _t1299
						_t1300 := &pb.Read{}
						_t1300.ReadType = &pb.Read_Demand{Demand: demand689}
						_t1298 = _t1300
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1295 = _t1298
				}
				_t1292 = _t1295
			}
			_t1289 = _t1292
		}
		_t1286 = _t1289
	}
	return _t1286
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1301 := p.parse_relation_id()
	relation_id694 := _t1301
	p.consumeLiteral(")")
	_t1302 := &pb.Demand{RelationId: relation_id694}
	return _t1302
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1303 := p.parse_name()
	name695 := _t1303
	_t1304 := p.parse_relation_id()
	relation_id696 := _t1304
	p.consumeLiteral(")")
	_t1305 := &pb.Output{Name: name695, RelationId: relation_id696}
	return _t1305
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1306 := p.parse_name()
	name697 := _t1306
	_t1307 := p.parse_epoch()
	epoch698 := _t1307
	p.consumeLiteral(")")
	_t1308 := &pb.WhatIf{Branch: name697, Epoch: epoch698}
	return _t1308
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1309 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1310 := p.parse_name()
		_t1309 = ptr(_t1310)
	}
	name699 := _t1309
	_t1311 := p.parse_relation_id()
	relation_id700 := _t1311
	p.consumeLiteral(")")
	_t1312 := &pb.Abort{Name: deref(name699, "abort"), RelationId: relation_id700}
	return _t1312
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1313 := p.parse_export_csv_config()
	export_csv_config701 := _t1313
	p.consumeLiteral(")")
	_t1314 := &pb.Export{}
	_t1314.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config701}
	return _t1314
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1315 := p.parse_export_csv_path()
	export_csv_path702 := _t1315
	_t1316 := p.parse_export_csv_columns()
	export_csv_columns703 := _t1316
	_t1317 := p.parse_config_dict()
	config_dict704 := _t1317
	p.consumeLiteral(")")
	_t1318 := p.export_csv_config(export_csv_path702, export_csv_columns703, config_dict704)
	return _t1318
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string705 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string705
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs706 := []*pb.ExportCSVColumn{}
	cond707 := p.matchLookaheadLiteral("(", 0)
	for cond707 {
		_t1319 := p.parse_export_csv_column()
		item708 := _t1319
		xs706 = append(xs706, item708)
		cond707 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns709 := xs706
	p.consumeLiteral(")")
	return export_csv_columns709
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string710 := p.consumeTerminal("STRING").Value.str
	_t1320 := p.parse_relation_id()
	relation_id711 := _t1320
	p.consumeLiteral(")")
	_t1321 := &pb.ExportCSVColumn{ColumnName: string710, ColumnData: relation_id711}
	return _t1321
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
