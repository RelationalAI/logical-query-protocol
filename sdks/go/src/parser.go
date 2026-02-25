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
	var _t1359 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1359
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1360 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1360
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1361 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1361
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1362 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1362
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1363 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1363
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1364 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1364
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1365 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1365
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1366 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1366
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1367 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1367
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1368 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1368
	_t1369 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1369
	_t1370 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1370
	_t1371 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1371
	_t1372 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1372
	_t1373 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1373
	_t1374 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1374
	_t1375 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1375
	_t1376 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1376
	_t1377 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1377
	_t1378 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1378
	_t1379 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1379
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1380 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1380
	_t1381 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1381
	_t1382 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1382
	_t1383 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1383
	_t1384 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1384
	_t1385 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1385
	_t1386 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1386
	_t1387 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1387
	_t1388 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1388
	_t1389 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1389.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1389.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1389
	_t1390 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1390
}

func (p *Parser) default_configure() *pb.Configure {
	_t1391 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1391
	_t1392 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1392
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
	_t1393 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1393
	_t1394 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1394
	_t1395 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1395
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1396 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1396
	_t1397 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1397
	_t1398 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1398
	_t1399 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1399
	_t1400 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1400
	_t1401 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1401
	_t1402 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1402
	_t1403 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1403
}

func (p *Parser) construct_csv_column(path []string, tail []interface{}) *pb.CSVColumn {
	var _t1404 interface{}
	if tail != nil {
		t := tail
		_t1405 := &pb.CSVColumn{ColumnPath: path, TargetId: t[0].(*pb.RelationId), Types: t[1].([]*pb.Type)}
		return _t1405
	}
	_ = _t1404
	_t1406 := &pb.CSVColumn{ColumnPath: path, TargetId: nil, Types: []*pb.Type{}}
	return _t1406
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t736 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t737 := p.parse_configure()
		_t736 = _t737
	}
	configure368 := _t736
	var _t738 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t739 := p.parse_sync()
		_t738 = _t739
	}
	sync369 := _t738
	xs370 := []*pb.Epoch{}
	cond371 := p.matchLookaheadLiteral("(", 0)
	for cond371 {
		_t740 := p.parse_epoch()
		item372 := _t740
		xs370 = append(xs370, item372)
		cond371 = p.matchLookaheadLiteral("(", 0)
	}
	epochs373 := xs370
	p.consumeLiteral(")")
	_t741 := p.default_configure()
	_t742 := configure368
	if configure368 == nil {
		_t742 = _t741
	}
	_t743 := &pb.Transaction{Epochs: epochs373, Configure: _t742, Sync: sync369}
	return _t743
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t744 := p.parse_config_dict()
	config_dict374 := _t744
	p.consumeLiteral(")")
	_t745 := p.construct_configure(config_dict374)
	return _t745
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs375 := [][]interface{}{}
	cond376 := p.matchLookaheadLiteral(":", 0)
	for cond376 {
		_t746 := p.parse_config_key_value()
		item377 := _t746
		xs375 = append(xs375, item377)
		cond376 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values378 := xs375
	p.consumeLiteral("}")
	return config_key_values378
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol379 := p.consumeTerminal("SYMBOL").Value.str
	_t747 := p.parse_value()
	value380 := _t747
	return []interface{}{symbol379, value380}
}

func (p *Parser) parse_value() *pb.Value {
	var _t748 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t748 = 9
	} else {
		var _t749 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t749 = 8
		} else {
			var _t750 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t750 = 9
			} else {
				var _t751 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t752 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t752 = 1
					} else {
						var _t753 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t753 = 0
						} else {
							_t753 = -1
						}
						_t752 = _t753
					}
					_t751 = _t752
				} else {
					var _t754 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t754 = 5
					} else {
						var _t755 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t755 = 2
						} else {
							var _t756 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t756 = 6
							} else {
								var _t757 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t757 = 3
								} else {
									var _t758 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t758 = 4
									} else {
										var _t759 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t759 = 7
										} else {
											_t759 = -1
										}
										_t758 = _t759
									}
									_t757 = _t758
								}
								_t756 = _t757
							}
							_t755 = _t756
						}
						_t754 = _t755
					}
					_t751 = _t754
				}
				_t750 = _t751
			}
			_t749 = _t750
		}
		_t748 = _t749
	}
	prediction381 := _t748
	var _t760 *pb.Value
	if prediction381 == 9 {
		_t761 := p.parse_boolean_value()
		boolean_value390 := _t761
		_t762 := &pb.Value{}
		_t762.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value390}
		_t760 = _t762
	} else {
		var _t763 *pb.Value
		if prediction381 == 8 {
			p.consumeLiteral("missing")
			_t764 := &pb.MissingValue{}
			_t765 := &pb.Value{}
			_t765.Value = &pb.Value_MissingValue{MissingValue: _t764}
			_t763 = _t765
		} else {
			var _t766 *pb.Value
			if prediction381 == 7 {
				decimal389 := p.consumeTerminal("DECIMAL").Value.decimal
				_t767 := &pb.Value{}
				_t767.Value = &pb.Value_DecimalValue{DecimalValue: decimal389}
				_t766 = _t767
			} else {
				var _t768 *pb.Value
				if prediction381 == 6 {
					int128388 := p.consumeTerminal("INT128").Value.int128
					_t769 := &pb.Value{}
					_t769.Value = &pb.Value_Int128Value{Int128Value: int128388}
					_t768 = _t769
				} else {
					var _t770 *pb.Value
					if prediction381 == 5 {
						uint128387 := p.consumeTerminal("UINT128").Value.uint128
						_t771 := &pb.Value{}
						_t771.Value = &pb.Value_Uint128Value{Uint128Value: uint128387}
						_t770 = _t771
					} else {
						var _t772 *pb.Value
						if prediction381 == 4 {
							float386 := p.consumeTerminal("FLOAT").Value.f64
							_t773 := &pb.Value{}
							_t773.Value = &pb.Value_FloatValue{FloatValue: float386}
							_t772 = _t773
						} else {
							var _t774 *pb.Value
							if prediction381 == 3 {
								int385 := p.consumeTerminal("INT").Value.i64
								_t775 := &pb.Value{}
								_t775.Value = &pb.Value_IntValue{IntValue: int385}
								_t774 = _t775
							} else {
								var _t776 *pb.Value
								if prediction381 == 2 {
									string384 := p.consumeTerminal("STRING").Value.str
									_t777 := &pb.Value{}
									_t777.Value = &pb.Value_StringValue{StringValue: string384}
									_t776 = _t777
								} else {
									var _t778 *pb.Value
									if prediction381 == 1 {
										_t779 := p.parse_datetime()
										datetime383 := _t779
										_t780 := &pb.Value{}
										_t780.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime383}
										_t778 = _t780
									} else {
										var _t781 *pb.Value
										if prediction381 == 0 {
											_t782 := p.parse_date()
											date382 := _t782
											_t783 := &pb.Value{}
											_t783.Value = &pb.Value_DateValue{DateValue: date382}
											_t781 = _t783
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t778 = _t781
									}
									_t776 = _t778
								}
								_t774 = _t776
							}
							_t772 = _t774
						}
						_t770 = _t772
					}
					_t768 = _t770
				}
				_t766 = _t768
			}
			_t763 = _t766
		}
		_t760 = _t763
	}
	return _t760
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int391 := p.consumeTerminal("INT").Value.i64
	int_3392 := p.consumeTerminal("INT").Value.i64
	int_4393 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t784 := &pb.DateValue{Year: int32(int391), Month: int32(int_3392), Day: int32(int_4393)}
	return _t784
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int394 := p.consumeTerminal("INT").Value.i64
	int_3395 := p.consumeTerminal("INT").Value.i64
	int_4396 := p.consumeTerminal("INT").Value.i64
	int_5397 := p.consumeTerminal("INT").Value.i64
	int_6398 := p.consumeTerminal("INT").Value.i64
	int_7399 := p.consumeTerminal("INT").Value.i64
	var _t785 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t785 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8400 := _t785
	p.consumeLiteral(")")
	_t786 := &pb.DateTimeValue{Year: int32(int394), Month: int32(int_3395), Day: int32(int_4396), Hour: int32(int_5397), Minute: int32(int_6398), Second: int32(int_7399), Microsecond: int32(deref(int_8400, 0))}
	return _t786
}

func (p *Parser) parse_boolean_value() bool {
	var _t787 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t787 = 0
	} else {
		var _t788 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t788 = 1
		} else {
			_t788 = -1
		}
		_t787 = _t788
	}
	prediction401 := _t787
	var _t789 bool
	if prediction401 == 1 {
		p.consumeLiteral("false")
		_t789 = false
	} else {
		var _t790 bool
		if prediction401 == 0 {
			p.consumeLiteral("true")
			_t790 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t789 = _t790
	}
	return _t789
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs402 := []*pb.FragmentId{}
	cond403 := p.matchLookaheadLiteral(":", 0)
	for cond403 {
		_t791 := p.parse_fragment_id()
		item404 := _t791
		xs402 = append(xs402, item404)
		cond403 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids405 := xs402
	p.consumeLiteral(")")
	_t792 := &pb.Sync{Fragments: fragment_ids405}
	return _t792
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol406 := p.consumeTerminal("SYMBOL").Value.str
	return &pb.FragmentId{Id: []byte(symbol406)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t793 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t794 := p.parse_epoch_writes()
		_t793 = _t794
	}
	epoch_writes407 := _t793
	var _t795 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t796 := p.parse_epoch_reads()
		_t795 = _t796
	}
	epoch_reads408 := _t795
	p.consumeLiteral(")")
	_t797 := epoch_writes407
	if epoch_writes407 == nil {
		_t797 = []*pb.Write{}
	}
	_t798 := epoch_reads408
	if epoch_reads408 == nil {
		_t798 = []*pb.Read{}
	}
	_t799 := &pb.Epoch{Writes: _t797, Reads: _t798}
	return _t799
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs409 := []*pb.Write{}
	cond410 := p.matchLookaheadLiteral("(", 0)
	for cond410 {
		_t800 := p.parse_write()
		item411 := _t800
		xs409 = append(xs409, item411)
		cond410 = p.matchLookaheadLiteral("(", 0)
	}
	writes412 := xs409
	p.consumeLiteral(")")
	return writes412
}

func (p *Parser) parse_write() *pb.Write {
	var _t801 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t802 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t802 = 1
		} else {
			var _t803 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t803 = 3
			} else {
				var _t804 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t804 = 0
				} else {
					var _t805 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t805 = 2
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
	} else {
		_t801 = -1
	}
	prediction413 := _t801
	var _t806 *pb.Write
	if prediction413 == 3 {
		_t807 := p.parse_snapshot()
		snapshot417 := _t807
		_t808 := &pb.Write{}
		_t808.WriteType = &pb.Write_Snapshot{Snapshot: snapshot417}
		_t806 = _t808
	} else {
		var _t809 *pb.Write
		if prediction413 == 2 {
			_t810 := p.parse_context()
			context416 := _t810
			_t811 := &pb.Write{}
			_t811.WriteType = &pb.Write_Context{Context: context416}
			_t809 = _t811
		} else {
			var _t812 *pb.Write
			if prediction413 == 1 {
				_t813 := p.parse_undefine()
				undefine415 := _t813
				_t814 := &pb.Write{}
				_t814.WriteType = &pb.Write_Undefine{Undefine: undefine415}
				_t812 = _t814
			} else {
				var _t815 *pb.Write
				if prediction413 == 0 {
					_t816 := p.parse_define()
					define414 := _t816
					_t817 := &pb.Write{}
					_t817.WriteType = &pb.Write_Define{Define: define414}
					_t815 = _t817
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t812 = _t815
			}
			_t809 = _t812
		}
		_t806 = _t809
	}
	return _t806
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t818 := p.parse_fragment()
	fragment418 := _t818
	p.consumeLiteral(")")
	_t819 := &pb.Define{Fragment: fragment418}
	return _t819
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t820 := p.parse_new_fragment_id()
	new_fragment_id419 := _t820
	xs420 := []*pb.Declaration{}
	cond421 := p.matchLookaheadLiteral("(", 0)
	for cond421 {
		_t821 := p.parse_declaration()
		item422 := _t821
		xs420 = append(xs420, item422)
		cond421 = p.matchLookaheadLiteral("(", 0)
	}
	declarations423 := xs420
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id419, declarations423)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t822 := p.parse_fragment_id()
	fragment_id424 := _t822
	p.startFragment(fragment_id424)
	return fragment_id424
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t823 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t824 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t824 = 3
		} else {
			var _t825 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t825 = 2
			} else {
				var _t826 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t826 = 0
				} else {
					var _t827 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t827 = 3
					} else {
						var _t828 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t828 = 3
						} else {
							var _t829 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t829 = 1
							} else {
								_t829 = -1
							}
							_t828 = _t829
						}
						_t827 = _t828
					}
					_t826 = _t827
				}
				_t825 = _t826
			}
			_t824 = _t825
		}
		_t823 = _t824
	} else {
		_t823 = -1
	}
	prediction425 := _t823
	var _t830 *pb.Declaration
	if prediction425 == 3 {
		_t831 := p.parse_data()
		data429 := _t831
		_t832 := &pb.Declaration{}
		_t832.DeclarationType = &pb.Declaration_Data{Data: data429}
		_t830 = _t832
	} else {
		var _t833 *pb.Declaration
		if prediction425 == 2 {
			_t834 := p.parse_constraint()
			constraint428 := _t834
			_t835 := &pb.Declaration{}
			_t835.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint428}
			_t833 = _t835
		} else {
			var _t836 *pb.Declaration
			if prediction425 == 1 {
				_t837 := p.parse_algorithm()
				algorithm427 := _t837
				_t838 := &pb.Declaration{}
				_t838.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm427}
				_t836 = _t838
			} else {
				var _t839 *pb.Declaration
				if prediction425 == 0 {
					_t840 := p.parse_def()
					def426 := _t840
					_t841 := &pb.Declaration{}
					_t841.DeclarationType = &pb.Declaration_Def{Def: def426}
					_t839 = _t841
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t836 = _t839
			}
			_t833 = _t836
		}
		_t830 = _t833
	}
	return _t830
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t842 := p.parse_relation_id()
	relation_id430 := _t842
	_t843 := p.parse_abstraction()
	abstraction431 := _t843
	var _t844 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t845 := p.parse_attrs()
		_t844 = _t845
	}
	attrs432 := _t844
	p.consumeLiteral(")")
	_t846 := attrs432
	if attrs432 == nil {
		_t846 = []*pb.Attribute{}
	}
	_t847 := &pb.Def{Name: relation_id430, Body: abstraction431, Attrs: _t846}
	return _t847
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t848 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t848 = 0
	} else {
		var _t849 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t849 = 1
		} else {
			_t849 = -1
		}
		_t848 = _t849
	}
	prediction433 := _t848
	var _t850 *pb.RelationId
	if prediction433 == 1 {
		uint128435 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128435
		_t850 = &pb.RelationId{IdLow: uint128435.Low, IdHigh: uint128435.High}
	} else {
		var _t851 *pb.RelationId
		if prediction433 == 0 {
			p.consumeLiteral(":")
			symbol434 := p.consumeTerminal("SYMBOL").Value.str
			_t851 = p.relationIdFromString(symbol434)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t850 = _t851
	}
	return _t850
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t852 := p.parse_bindings()
	bindings436 := _t852
	_t853 := p.parse_formula()
	formula437 := _t853
	p.consumeLiteral(")")
	_t854 := &pb.Abstraction{Vars: listConcat(bindings436[0].([]*pb.Binding), bindings436[1].([]*pb.Binding)), Value: formula437}
	return _t854
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs438 := []*pb.Binding{}
	cond439 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond439 {
		_t855 := p.parse_binding()
		item440 := _t855
		xs438 = append(xs438, item440)
		cond439 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings441 := xs438
	var _t856 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t857 := p.parse_value_bindings()
		_t856 = _t857
	}
	value_bindings442 := _t856
	p.consumeLiteral("]")
	_t858 := value_bindings442
	if value_bindings442 == nil {
		_t858 = []*pb.Binding{}
	}
	return []interface{}{bindings441, _t858}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol443 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t859 := p.parse_type()
	type444 := _t859
	_t860 := &pb.Var{Name: symbol443}
	_t861 := &pb.Binding{Var: _t860, Type: type444}
	return _t861
}

func (p *Parser) parse_type() *pb.Type {
	var _t862 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t862 = 0
	} else {
		var _t863 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t863 = 4
		} else {
			var _t864 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t864 = 1
			} else {
				var _t865 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t865 = 8
				} else {
					var _t866 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t866 = 5
					} else {
						var _t867 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t867 = 2
						} else {
							var _t868 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t868 = 3
							} else {
								var _t869 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t869 = 7
								} else {
									var _t870 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t870 = 6
									} else {
										var _t871 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t871 = 10
										} else {
											var _t872 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t872 = 9
											} else {
												_t872 = -1
											}
											_t871 = _t872
										}
										_t870 = _t871
									}
									_t869 = _t870
								}
								_t868 = _t869
							}
							_t867 = _t868
						}
						_t866 = _t867
					}
					_t865 = _t866
				}
				_t864 = _t865
			}
			_t863 = _t864
		}
		_t862 = _t863
	}
	prediction445 := _t862
	var _t873 *pb.Type
	if prediction445 == 10 {
		_t874 := p.parse_boolean_type()
		boolean_type456 := _t874
		_t875 := &pb.Type{}
		_t875.Type = &pb.Type_BooleanType{BooleanType: boolean_type456}
		_t873 = _t875
	} else {
		var _t876 *pb.Type
		if prediction445 == 9 {
			_t877 := p.parse_decimal_type()
			decimal_type455 := _t877
			_t878 := &pb.Type{}
			_t878.Type = &pb.Type_DecimalType{DecimalType: decimal_type455}
			_t876 = _t878
		} else {
			var _t879 *pb.Type
			if prediction445 == 8 {
				_t880 := p.parse_missing_type()
				missing_type454 := _t880
				_t881 := &pb.Type{}
				_t881.Type = &pb.Type_MissingType{MissingType: missing_type454}
				_t879 = _t881
			} else {
				var _t882 *pb.Type
				if prediction445 == 7 {
					_t883 := p.parse_datetime_type()
					datetime_type453 := _t883
					_t884 := &pb.Type{}
					_t884.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type453}
					_t882 = _t884
				} else {
					var _t885 *pb.Type
					if prediction445 == 6 {
						_t886 := p.parse_date_type()
						date_type452 := _t886
						_t887 := &pb.Type{}
						_t887.Type = &pb.Type_DateType{DateType: date_type452}
						_t885 = _t887
					} else {
						var _t888 *pb.Type
						if prediction445 == 5 {
							_t889 := p.parse_int128_type()
							int128_type451 := _t889
							_t890 := &pb.Type{}
							_t890.Type = &pb.Type_Int128Type{Int128Type: int128_type451}
							_t888 = _t890
						} else {
							var _t891 *pb.Type
							if prediction445 == 4 {
								_t892 := p.parse_uint128_type()
								uint128_type450 := _t892
								_t893 := &pb.Type{}
								_t893.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type450}
								_t891 = _t893
							} else {
								var _t894 *pb.Type
								if prediction445 == 3 {
									_t895 := p.parse_float_type()
									float_type449 := _t895
									_t896 := &pb.Type{}
									_t896.Type = &pb.Type_FloatType{FloatType: float_type449}
									_t894 = _t896
								} else {
									var _t897 *pb.Type
									if prediction445 == 2 {
										_t898 := p.parse_int_type()
										int_type448 := _t898
										_t899 := &pb.Type{}
										_t899.Type = &pb.Type_IntType{IntType: int_type448}
										_t897 = _t899
									} else {
										var _t900 *pb.Type
										if prediction445 == 1 {
											_t901 := p.parse_string_type()
											string_type447 := _t901
											_t902 := &pb.Type{}
											_t902.Type = &pb.Type_StringType{StringType: string_type447}
											_t900 = _t902
										} else {
											var _t903 *pb.Type
											if prediction445 == 0 {
												_t904 := p.parse_unspecified_type()
												unspecified_type446 := _t904
												_t905 := &pb.Type{}
												_t905.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type446}
												_t903 = _t905
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t900 = _t903
										}
										_t897 = _t900
									}
									_t894 = _t897
								}
								_t891 = _t894
							}
							_t888 = _t891
						}
						_t885 = _t888
					}
					_t882 = _t885
				}
				_t879 = _t882
			}
			_t876 = _t879
		}
		_t873 = _t876
	}
	return _t873
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t906 := &pb.UnspecifiedType{}
	return _t906
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t907 := &pb.StringType{}
	return _t907
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t908 := &pb.IntType{}
	return _t908
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t909 := &pb.FloatType{}
	return _t909
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t910 := &pb.UInt128Type{}
	return _t910
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t911 := &pb.Int128Type{}
	return _t911
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t912 := &pb.DateType{}
	return _t912
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t913 := &pb.DateTimeType{}
	return _t913
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t914 := &pb.MissingType{}
	return _t914
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int457 := p.consumeTerminal("INT").Value.i64
	int_3458 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t915 := &pb.DecimalType{Precision: int32(int457), Scale: int32(int_3458)}
	return _t915
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t916 := &pb.BooleanType{}
	return _t916
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs459 := []*pb.Binding{}
	cond460 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond460 {
		_t917 := p.parse_binding()
		item461 := _t917
		xs459 = append(xs459, item461)
		cond460 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings462 := xs459
	return bindings462
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t918 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t919 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t919 = 0
		} else {
			var _t920 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t920 = 11
			} else {
				var _t921 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t921 = 3
				} else {
					var _t922 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t922 = 10
					} else {
						var _t923 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t923 = 9
						} else {
							var _t924 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t924 = 5
							} else {
								var _t925 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t925 = 6
								} else {
									var _t926 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t926 = 7
									} else {
										var _t927 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t927 = 1
										} else {
											var _t928 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t928 = 2
											} else {
												var _t929 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t929 = 12
												} else {
													var _t930 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t930 = 8
													} else {
														var _t931 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t931 = 4
														} else {
															var _t932 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t932 = 10
															} else {
																var _t933 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t933 = 10
																} else {
																	var _t934 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t934 = 10
																	} else {
																		var _t935 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t935 = 10
																		} else {
																			var _t936 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t936 = 10
																			} else {
																				var _t937 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t937 = 10
																				} else {
																					var _t938 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t938 = 10
																					} else {
																						var _t939 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t939 = 10
																						} else {
																							var _t940 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t940 = 10
																							} else {
																								_t940 = -1
																							}
																							_t939 = _t940
																						}
																						_t938 = _t939
																					}
																					_t937 = _t938
																				}
																				_t936 = _t937
																			}
																			_t935 = _t936
																		}
																		_t934 = _t935
																	}
																	_t933 = _t934
																}
																_t932 = _t933
															}
															_t931 = _t932
														}
														_t930 = _t931
													}
													_t929 = _t930
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
							}
							_t923 = _t924
						}
						_t922 = _t923
					}
					_t921 = _t922
				}
				_t920 = _t921
			}
			_t919 = _t920
		}
		_t918 = _t919
	} else {
		_t918 = -1
	}
	prediction463 := _t918
	var _t941 *pb.Formula
	if prediction463 == 12 {
		_t942 := p.parse_cast()
		cast476 := _t942
		_t943 := &pb.Formula{}
		_t943.FormulaType = &pb.Formula_Cast{Cast: cast476}
		_t941 = _t943
	} else {
		var _t944 *pb.Formula
		if prediction463 == 11 {
			_t945 := p.parse_rel_atom()
			rel_atom475 := _t945
			_t946 := &pb.Formula{}
			_t946.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom475}
			_t944 = _t946
		} else {
			var _t947 *pb.Formula
			if prediction463 == 10 {
				_t948 := p.parse_primitive()
				primitive474 := _t948
				_t949 := &pb.Formula{}
				_t949.FormulaType = &pb.Formula_Primitive{Primitive: primitive474}
				_t947 = _t949
			} else {
				var _t950 *pb.Formula
				if prediction463 == 9 {
					_t951 := p.parse_pragma()
					pragma473 := _t951
					_t952 := &pb.Formula{}
					_t952.FormulaType = &pb.Formula_Pragma{Pragma: pragma473}
					_t950 = _t952
				} else {
					var _t953 *pb.Formula
					if prediction463 == 8 {
						_t954 := p.parse_atom()
						atom472 := _t954
						_t955 := &pb.Formula{}
						_t955.FormulaType = &pb.Formula_Atom{Atom: atom472}
						_t953 = _t955
					} else {
						var _t956 *pb.Formula
						if prediction463 == 7 {
							_t957 := p.parse_ffi()
							ffi471 := _t957
							_t958 := &pb.Formula{}
							_t958.FormulaType = &pb.Formula_Ffi{Ffi: ffi471}
							_t956 = _t958
						} else {
							var _t959 *pb.Formula
							if prediction463 == 6 {
								_t960 := p.parse_not()
								not470 := _t960
								_t961 := &pb.Formula{}
								_t961.FormulaType = &pb.Formula_Not{Not: not470}
								_t959 = _t961
							} else {
								var _t962 *pb.Formula
								if prediction463 == 5 {
									_t963 := p.parse_disjunction()
									disjunction469 := _t963
									_t964 := &pb.Formula{}
									_t964.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction469}
									_t962 = _t964
								} else {
									var _t965 *pb.Formula
									if prediction463 == 4 {
										_t966 := p.parse_conjunction()
										conjunction468 := _t966
										_t967 := &pb.Formula{}
										_t967.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction468}
										_t965 = _t967
									} else {
										var _t968 *pb.Formula
										if prediction463 == 3 {
											_t969 := p.parse_reduce()
											reduce467 := _t969
											_t970 := &pb.Formula{}
											_t970.FormulaType = &pb.Formula_Reduce{Reduce: reduce467}
											_t968 = _t970
										} else {
											var _t971 *pb.Formula
											if prediction463 == 2 {
												_t972 := p.parse_exists()
												exists466 := _t972
												_t973 := &pb.Formula{}
												_t973.FormulaType = &pb.Formula_Exists{Exists: exists466}
												_t971 = _t973
											} else {
												var _t974 *pb.Formula
												if prediction463 == 1 {
													_t975 := p.parse_false()
													false465 := _t975
													_t976 := &pb.Formula{}
													_t976.FormulaType = &pb.Formula_Disjunction{Disjunction: false465}
													_t974 = _t976
												} else {
													var _t977 *pb.Formula
													if prediction463 == 0 {
														_t978 := p.parse_true()
														true464 := _t978
														_t979 := &pb.Formula{}
														_t979.FormulaType = &pb.Formula_Conjunction{Conjunction: true464}
														_t977 = _t979
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t974 = _t977
												}
												_t971 = _t974
											}
											_t968 = _t971
										}
										_t965 = _t968
									}
									_t962 = _t965
								}
								_t959 = _t962
							}
							_t956 = _t959
						}
						_t953 = _t956
					}
					_t950 = _t953
				}
				_t947 = _t950
			}
			_t944 = _t947
		}
		_t941 = _t944
	}
	return _t941
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t980 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t980
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t981 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t981
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t982 := p.parse_bindings()
	bindings477 := _t982
	_t983 := p.parse_formula()
	formula478 := _t983
	p.consumeLiteral(")")
	_t984 := &pb.Abstraction{Vars: listConcat(bindings477[0].([]*pb.Binding), bindings477[1].([]*pb.Binding)), Value: formula478}
	_t985 := &pb.Exists{Body: _t984}
	return _t985
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t986 := p.parse_abstraction()
	abstraction479 := _t986
	_t987 := p.parse_abstraction()
	abstraction_3480 := _t987
	_t988 := p.parse_terms()
	terms481 := _t988
	p.consumeLiteral(")")
	_t989 := &pb.Reduce{Op: abstraction479, Body: abstraction_3480, Terms: terms481}
	return _t989
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs482 := []*pb.Term{}
	cond483 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond483 {
		_t990 := p.parse_term()
		item484 := _t990
		xs482 = append(xs482, item484)
		cond483 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms485 := xs482
	p.consumeLiteral(")")
	return terms485
}

func (p *Parser) parse_term() *pb.Term {
	var _t991 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t991 = 1
	} else {
		var _t992 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t992 = 1
		} else {
			var _t993 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t993 = 1
			} else {
				var _t994 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t994 = 1
				} else {
					var _t995 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t995 = 1
					} else {
						var _t996 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t996 = 0
						} else {
							var _t997 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t997 = 1
							} else {
								var _t998 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t998 = 1
								} else {
									var _t999 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t999 = 1
									} else {
										var _t1000 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1000 = 1
										} else {
											var _t1001 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1001 = 1
											} else {
												_t1001 = -1
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
		_t991 = _t992
	}
	prediction486 := _t991
	var _t1002 *pb.Term
	if prediction486 == 1 {
		_t1003 := p.parse_constant()
		constant488 := _t1003
		_t1004 := &pb.Term{}
		_t1004.TermType = &pb.Term_Constant{Constant: constant488}
		_t1002 = _t1004
	} else {
		var _t1005 *pb.Term
		if prediction486 == 0 {
			_t1006 := p.parse_var()
			var487 := _t1006
			_t1007 := &pb.Term{}
			_t1007.TermType = &pb.Term_Var{Var: var487}
			_t1005 = _t1007
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1002 = _t1005
	}
	return _t1002
}

func (p *Parser) parse_var() *pb.Var {
	symbol489 := p.consumeTerminal("SYMBOL").Value.str
	_t1008 := &pb.Var{Name: symbol489}
	return _t1008
}

func (p *Parser) parse_constant() *pb.Value {
	_t1009 := p.parse_value()
	value490 := _t1009
	return value490
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs491 := []*pb.Formula{}
	cond492 := p.matchLookaheadLiteral("(", 0)
	for cond492 {
		_t1010 := p.parse_formula()
		item493 := _t1010
		xs491 = append(xs491, item493)
		cond492 = p.matchLookaheadLiteral("(", 0)
	}
	formulas494 := xs491
	p.consumeLiteral(")")
	_t1011 := &pb.Conjunction{Args: formulas494}
	return _t1011
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs495 := []*pb.Formula{}
	cond496 := p.matchLookaheadLiteral("(", 0)
	for cond496 {
		_t1012 := p.parse_formula()
		item497 := _t1012
		xs495 = append(xs495, item497)
		cond496 = p.matchLookaheadLiteral("(", 0)
	}
	formulas498 := xs495
	p.consumeLiteral(")")
	_t1013 := &pb.Disjunction{Args: formulas498}
	return _t1013
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1014 := p.parse_formula()
	formula499 := _t1014
	p.consumeLiteral(")")
	_t1015 := &pb.Not{Arg: formula499}
	return _t1015
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1016 := p.parse_name()
	name500 := _t1016
	_t1017 := p.parse_ffi_args()
	ffi_args501 := _t1017
	_t1018 := p.parse_terms()
	terms502 := _t1018
	p.consumeLiteral(")")
	_t1019 := &pb.FFI{Name: name500, Args: ffi_args501, Terms: terms502}
	return _t1019
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol503 := p.consumeTerminal("SYMBOL").Value.str
	return symbol503
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs504 := []*pb.Abstraction{}
	cond505 := p.matchLookaheadLiteral("(", 0)
	for cond505 {
		_t1020 := p.parse_abstraction()
		item506 := _t1020
		xs504 = append(xs504, item506)
		cond505 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions507 := xs504
	p.consumeLiteral(")")
	return abstractions507
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1021 := p.parse_relation_id()
	relation_id508 := _t1021
	xs509 := []*pb.Term{}
	cond510 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond510 {
		_t1022 := p.parse_term()
		item511 := _t1022
		xs509 = append(xs509, item511)
		cond510 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms512 := xs509
	p.consumeLiteral(")")
	_t1023 := &pb.Atom{Name: relation_id508, Terms: terms512}
	return _t1023
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1024 := p.parse_name()
	name513 := _t1024
	xs514 := []*pb.Term{}
	cond515 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond515 {
		_t1025 := p.parse_term()
		item516 := _t1025
		xs514 = append(xs514, item516)
		cond515 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms517 := xs514
	p.consumeLiteral(")")
	_t1026 := &pb.Pragma{Name: name513, Terms: terms517}
	return _t1026
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1027 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1028 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1028 = 9
		} else {
			var _t1029 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1029 = 4
			} else {
				var _t1030 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1030 = 3
				} else {
					var _t1031 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1031 = 0
					} else {
						var _t1032 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1032 = 2
						} else {
							var _t1033 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1033 = 1
							} else {
								var _t1034 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1034 = 8
								} else {
									var _t1035 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1035 = 6
									} else {
										var _t1036 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1036 = 5
										} else {
											var _t1037 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1037 = 7
											} else {
												_t1037 = -1
											}
											_t1036 = _t1037
										}
										_t1035 = _t1036
									}
									_t1034 = _t1035
								}
								_t1033 = _t1034
							}
							_t1032 = _t1033
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
	} else {
		_t1027 = -1
	}
	prediction518 := _t1027
	var _t1038 *pb.Primitive
	if prediction518 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1039 := p.parse_name()
		name528 := _t1039
		xs529 := []*pb.RelTerm{}
		cond530 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond530 {
			_t1040 := p.parse_rel_term()
			item531 := _t1040
			xs529 = append(xs529, item531)
			cond530 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms532 := xs529
		p.consumeLiteral(")")
		_t1041 := &pb.Primitive{Name: name528, Terms: rel_terms532}
		_t1038 = _t1041
	} else {
		var _t1042 *pb.Primitive
		if prediction518 == 8 {
			_t1043 := p.parse_divide()
			divide527 := _t1043
			_t1042 = divide527
		} else {
			var _t1044 *pb.Primitive
			if prediction518 == 7 {
				_t1045 := p.parse_multiply()
				multiply526 := _t1045
				_t1044 = multiply526
			} else {
				var _t1046 *pb.Primitive
				if prediction518 == 6 {
					_t1047 := p.parse_minus()
					minus525 := _t1047
					_t1046 = minus525
				} else {
					var _t1048 *pb.Primitive
					if prediction518 == 5 {
						_t1049 := p.parse_add()
						add524 := _t1049
						_t1048 = add524
					} else {
						var _t1050 *pb.Primitive
						if prediction518 == 4 {
							_t1051 := p.parse_gt_eq()
							gt_eq523 := _t1051
							_t1050 = gt_eq523
						} else {
							var _t1052 *pb.Primitive
							if prediction518 == 3 {
								_t1053 := p.parse_gt()
								gt522 := _t1053
								_t1052 = gt522
							} else {
								var _t1054 *pb.Primitive
								if prediction518 == 2 {
									_t1055 := p.parse_lt_eq()
									lt_eq521 := _t1055
									_t1054 = lt_eq521
								} else {
									var _t1056 *pb.Primitive
									if prediction518 == 1 {
										_t1057 := p.parse_lt()
										lt520 := _t1057
										_t1056 = lt520
									} else {
										var _t1058 *pb.Primitive
										if prediction518 == 0 {
											_t1059 := p.parse_eq()
											eq519 := _t1059
											_t1058 = eq519
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1056 = _t1058
									}
									_t1054 = _t1056
								}
								_t1052 = _t1054
							}
							_t1050 = _t1052
						}
						_t1048 = _t1050
					}
					_t1046 = _t1048
				}
				_t1044 = _t1046
			}
			_t1042 = _t1044
		}
		_t1038 = _t1042
	}
	return _t1038
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1060 := p.parse_term()
	term533 := _t1060
	_t1061 := p.parse_term()
	term_3534 := _t1061
	p.consumeLiteral(")")
	_t1062 := &pb.RelTerm{}
	_t1062.RelTermType = &pb.RelTerm_Term{Term: term533}
	_t1063 := &pb.RelTerm{}
	_t1063.RelTermType = &pb.RelTerm_Term{Term: term_3534}
	_t1064 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1062, _t1063}}
	return _t1064
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1065 := p.parse_term()
	term535 := _t1065
	_t1066 := p.parse_term()
	term_3536 := _t1066
	p.consumeLiteral(")")
	_t1067 := &pb.RelTerm{}
	_t1067.RelTermType = &pb.RelTerm_Term{Term: term535}
	_t1068 := &pb.RelTerm{}
	_t1068.RelTermType = &pb.RelTerm_Term{Term: term_3536}
	_t1069 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1067, _t1068}}
	return _t1069
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1070 := p.parse_term()
	term537 := _t1070
	_t1071 := p.parse_term()
	term_3538 := _t1071
	p.consumeLiteral(")")
	_t1072 := &pb.RelTerm{}
	_t1072.RelTermType = &pb.RelTerm_Term{Term: term537}
	_t1073 := &pb.RelTerm{}
	_t1073.RelTermType = &pb.RelTerm_Term{Term: term_3538}
	_t1074 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1072, _t1073}}
	return _t1074
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1075 := p.parse_term()
	term539 := _t1075
	_t1076 := p.parse_term()
	term_3540 := _t1076
	p.consumeLiteral(")")
	_t1077 := &pb.RelTerm{}
	_t1077.RelTermType = &pb.RelTerm_Term{Term: term539}
	_t1078 := &pb.RelTerm{}
	_t1078.RelTermType = &pb.RelTerm_Term{Term: term_3540}
	_t1079 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1077, _t1078}}
	return _t1079
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1080 := p.parse_term()
	term541 := _t1080
	_t1081 := p.parse_term()
	term_3542 := _t1081
	p.consumeLiteral(")")
	_t1082 := &pb.RelTerm{}
	_t1082.RelTermType = &pb.RelTerm_Term{Term: term541}
	_t1083 := &pb.RelTerm{}
	_t1083.RelTermType = &pb.RelTerm_Term{Term: term_3542}
	_t1084 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1082, _t1083}}
	return _t1084
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1085 := p.parse_term()
	term543 := _t1085
	_t1086 := p.parse_term()
	term_3544 := _t1086
	_t1087 := p.parse_term()
	term_4545 := _t1087
	p.consumeLiteral(")")
	_t1088 := &pb.RelTerm{}
	_t1088.RelTermType = &pb.RelTerm_Term{Term: term543}
	_t1089 := &pb.RelTerm{}
	_t1089.RelTermType = &pb.RelTerm_Term{Term: term_3544}
	_t1090 := &pb.RelTerm{}
	_t1090.RelTermType = &pb.RelTerm_Term{Term: term_4545}
	_t1091 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1088, _t1089, _t1090}}
	return _t1091
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1092 := p.parse_term()
	term546 := _t1092
	_t1093 := p.parse_term()
	term_3547 := _t1093
	_t1094 := p.parse_term()
	term_4548 := _t1094
	p.consumeLiteral(")")
	_t1095 := &pb.RelTerm{}
	_t1095.RelTermType = &pb.RelTerm_Term{Term: term546}
	_t1096 := &pb.RelTerm{}
	_t1096.RelTermType = &pb.RelTerm_Term{Term: term_3547}
	_t1097 := &pb.RelTerm{}
	_t1097.RelTermType = &pb.RelTerm_Term{Term: term_4548}
	_t1098 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1095, _t1096, _t1097}}
	return _t1098
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1099 := p.parse_term()
	term549 := _t1099
	_t1100 := p.parse_term()
	term_3550 := _t1100
	_t1101 := p.parse_term()
	term_4551 := _t1101
	p.consumeLiteral(")")
	_t1102 := &pb.RelTerm{}
	_t1102.RelTermType = &pb.RelTerm_Term{Term: term549}
	_t1103 := &pb.RelTerm{}
	_t1103.RelTermType = &pb.RelTerm_Term{Term: term_3550}
	_t1104 := &pb.RelTerm{}
	_t1104.RelTermType = &pb.RelTerm_Term{Term: term_4551}
	_t1105 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1102, _t1103, _t1104}}
	return _t1105
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1106 := p.parse_term()
	term552 := _t1106
	_t1107 := p.parse_term()
	term_3553 := _t1107
	_t1108 := p.parse_term()
	term_4554 := _t1108
	p.consumeLiteral(")")
	_t1109 := &pb.RelTerm{}
	_t1109.RelTermType = &pb.RelTerm_Term{Term: term552}
	_t1110 := &pb.RelTerm{}
	_t1110.RelTermType = &pb.RelTerm_Term{Term: term_3553}
	_t1111 := &pb.RelTerm{}
	_t1111.RelTermType = &pb.RelTerm_Term{Term: term_4554}
	_t1112 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1109, _t1110, _t1111}}
	return _t1112
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1113 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1113 = 1
	} else {
		var _t1114 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1114 = 1
		} else {
			var _t1115 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1115 = 1
			} else {
				var _t1116 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1116 = 1
				} else {
					var _t1117 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1117 = 0
					} else {
						var _t1118 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1118 = 1
						} else {
							var _t1119 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1119 = 1
							} else {
								var _t1120 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1120 = 1
								} else {
									var _t1121 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1121 = 1
									} else {
										var _t1122 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1122 = 1
										} else {
											var _t1123 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1123 = 1
											} else {
												var _t1124 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1124 = 1
												} else {
													_t1124 = -1
												}
												_t1123 = _t1124
											}
											_t1122 = _t1123
										}
										_t1121 = _t1122
									}
									_t1120 = _t1121
								}
								_t1119 = _t1120
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
	}
	prediction555 := _t1113
	var _t1125 *pb.RelTerm
	if prediction555 == 1 {
		_t1126 := p.parse_term()
		term557 := _t1126
		_t1127 := &pb.RelTerm{}
		_t1127.RelTermType = &pb.RelTerm_Term{Term: term557}
		_t1125 = _t1127
	} else {
		var _t1128 *pb.RelTerm
		if prediction555 == 0 {
			_t1129 := p.parse_specialized_value()
			specialized_value556 := _t1129
			_t1130 := &pb.RelTerm{}
			_t1130.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value556}
			_t1128 = _t1130
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1125 = _t1128
	}
	return _t1125
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1131 := p.parse_value()
	value558 := _t1131
	return value558
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1132 := p.parse_name()
	name559 := _t1132
	xs560 := []*pb.RelTerm{}
	cond561 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond561 {
		_t1133 := p.parse_rel_term()
		item562 := _t1133
		xs560 = append(xs560, item562)
		cond561 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms563 := xs560
	p.consumeLiteral(")")
	_t1134 := &pb.RelAtom{Name: name559, Terms: rel_terms563}
	return _t1134
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1135 := p.parse_term()
	term564 := _t1135
	_t1136 := p.parse_term()
	term_3565 := _t1136
	p.consumeLiteral(")")
	_t1137 := &pb.Cast{Input: term564, Result: term_3565}
	return _t1137
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs566 := []*pb.Attribute{}
	cond567 := p.matchLookaheadLiteral("(", 0)
	for cond567 {
		_t1138 := p.parse_attribute()
		item568 := _t1138
		xs566 = append(xs566, item568)
		cond567 = p.matchLookaheadLiteral("(", 0)
	}
	attributes569 := xs566
	p.consumeLiteral(")")
	return attributes569
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1139 := p.parse_name()
	name570 := _t1139
	xs571 := []*pb.Value{}
	cond572 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond572 {
		_t1140 := p.parse_value()
		item573 := _t1140
		xs571 = append(xs571, item573)
		cond572 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values574 := xs571
	p.consumeLiteral(")")
	_t1141 := &pb.Attribute{Name: name570, Args: values574}
	return _t1141
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs575 := []*pb.RelationId{}
	cond576 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond576 {
		_t1142 := p.parse_relation_id()
		item577 := _t1142
		xs575 = append(xs575, item577)
		cond576 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids578 := xs575
	_t1143 := p.parse_script()
	script579 := _t1143
	p.consumeLiteral(")")
	_t1144 := &pb.Algorithm{Global: relation_ids578, Body: script579}
	return _t1144
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs580 := []*pb.Construct{}
	cond581 := p.matchLookaheadLiteral("(", 0)
	for cond581 {
		_t1145 := p.parse_construct()
		item582 := _t1145
		xs580 = append(xs580, item582)
		cond581 = p.matchLookaheadLiteral("(", 0)
	}
	constructs583 := xs580
	p.consumeLiteral(")")
	_t1146 := &pb.Script{Constructs: constructs583}
	return _t1146
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1147 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1148 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1148 = 1
		} else {
			var _t1149 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1149 = 1
			} else {
				var _t1150 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1150 = 1
				} else {
					var _t1151 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1151 = 0
					} else {
						var _t1152 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1152 = 1
						} else {
							var _t1153 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1153 = 1
							} else {
								_t1153 = -1
							}
							_t1152 = _t1153
						}
						_t1151 = _t1152
					}
					_t1150 = _t1151
				}
				_t1149 = _t1150
			}
			_t1148 = _t1149
		}
		_t1147 = _t1148
	} else {
		_t1147 = -1
	}
	prediction584 := _t1147
	var _t1154 *pb.Construct
	if prediction584 == 1 {
		_t1155 := p.parse_instruction()
		instruction586 := _t1155
		_t1156 := &pb.Construct{}
		_t1156.ConstructType = &pb.Construct_Instruction{Instruction: instruction586}
		_t1154 = _t1156
	} else {
		var _t1157 *pb.Construct
		if prediction584 == 0 {
			_t1158 := p.parse_loop()
			loop585 := _t1158
			_t1159 := &pb.Construct{}
			_t1159.ConstructType = &pb.Construct_Loop{Loop: loop585}
			_t1157 = _t1159
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1154 = _t1157
	}
	return _t1154
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1160 := p.parse_init()
	init587 := _t1160
	_t1161 := p.parse_script()
	script588 := _t1161
	p.consumeLiteral(")")
	_t1162 := &pb.Loop{Init: init587, Body: script588}
	return _t1162
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs589 := []*pb.Instruction{}
	cond590 := p.matchLookaheadLiteral("(", 0)
	for cond590 {
		_t1163 := p.parse_instruction()
		item591 := _t1163
		xs589 = append(xs589, item591)
		cond590 = p.matchLookaheadLiteral("(", 0)
	}
	instructions592 := xs589
	p.consumeLiteral(")")
	return instructions592
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1164 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1165 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1165 = 1
		} else {
			var _t1166 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1166 = 4
			} else {
				var _t1167 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1167 = 3
				} else {
					var _t1168 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1168 = 2
					} else {
						var _t1169 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1169 = 0
						} else {
							_t1169 = -1
						}
						_t1168 = _t1169
					}
					_t1167 = _t1168
				}
				_t1166 = _t1167
			}
			_t1165 = _t1166
		}
		_t1164 = _t1165
	} else {
		_t1164 = -1
	}
	prediction593 := _t1164
	var _t1170 *pb.Instruction
	if prediction593 == 4 {
		_t1171 := p.parse_monus_def()
		monus_def598 := _t1171
		_t1172 := &pb.Instruction{}
		_t1172.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def598}
		_t1170 = _t1172
	} else {
		var _t1173 *pb.Instruction
		if prediction593 == 3 {
			_t1174 := p.parse_monoid_def()
			monoid_def597 := _t1174
			_t1175 := &pb.Instruction{}
			_t1175.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def597}
			_t1173 = _t1175
		} else {
			var _t1176 *pb.Instruction
			if prediction593 == 2 {
				_t1177 := p.parse_break()
				break596 := _t1177
				_t1178 := &pb.Instruction{}
				_t1178.InstrType = &pb.Instruction_Break{Break: break596}
				_t1176 = _t1178
			} else {
				var _t1179 *pb.Instruction
				if prediction593 == 1 {
					_t1180 := p.parse_upsert()
					upsert595 := _t1180
					_t1181 := &pb.Instruction{}
					_t1181.InstrType = &pb.Instruction_Upsert{Upsert: upsert595}
					_t1179 = _t1181
				} else {
					var _t1182 *pb.Instruction
					if prediction593 == 0 {
						_t1183 := p.parse_assign()
						assign594 := _t1183
						_t1184 := &pb.Instruction{}
						_t1184.InstrType = &pb.Instruction_Assign{Assign: assign594}
						_t1182 = _t1184
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1179 = _t1182
				}
				_t1176 = _t1179
			}
			_t1173 = _t1176
		}
		_t1170 = _t1173
	}
	return _t1170
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1185 := p.parse_relation_id()
	relation_id599 := _t1185
	_t1186 := p.parse_abstraction()
	abstraction600 := _t1186
	var _t1187 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1188 := p.parse_attrs()
		_t1187 = _t1188
	}
	attrs601 := _t1187
	p.consumeLiteral(")")
	_t1189 := attrs601
	if attrs601 == nil {
		_t1189 = []*pb.Attribute{}
	}
	_t1190 := &pb.Assign{Name: relation_id599, Body: abstraction600, Attrs: _t1189}
	return _t1190
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1191 := p.parse_relation_id()
	relation_id602 := _t1191
	_t1192 := p.parse_abstraction_with_arity()
	abstraction_with_arity603 := _t1192
	var _t1193 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1194 := p.parse_attrs()
		_t1193 = _t1194
	}
	attrs604 := _t1193
	p.consumeLiteral(")")
	_t1195 := attrs604
	if attrs604 == nil {
		_t1195 = []*pb.Attribute{}
	}
	_t1196 := &pb.Upsert{Name: relation_id602, Body: abstraction_with_arity603[0].(*pb.Abstraction), Attrs: _t1195, ValueArity: abstraction_with_arity603[1].(int64)}
	return _t1196
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1197 := p.parse_bindings()
	bindings605 := _t1197
	_t1198 := p.parse_formula()
	formula606 := _t1198
	p.consumeLiteral(")")
	_t1199 := &pb.Abstraction{Vars: listConcat(bindings605[0].([]*pb.Binding), bindings605[1].([]*pb.Binding)), Value: formula606}
	return []interface{}{_t1199, int64(len(bindings605[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1200 := p.parse_relation_id()
	relation_id607 := _t1200
	_t1201 := p.parse_abstraction()
	abstraction608 := _t1201
	var _t1202 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1203 := p.parse_attrs()
		_t1202 = _t1203
	}
	attrs609 := _t1202
	p.consumeLiteral(")")
	_t1204 := attrs609
	if attrs609 == nil {
		_t1204 = []*pb.Attribute{}
	}
	_t1205 := &pb.Break{Name: relation_id607, Body: abstraction608, Attrs: _t1204}
	return _t1205
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1206 := p.parse_monoid()
	monoid610 := _t1206
	_t1207 := p.parse_relation_id()
	relation_id611 := _t1207
	_t1208 := p.parse_abstraction_with_arity()
	abstraction_with_arity612 := _t1208
	var _t1209 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1210 := p.parse_attrs()
		_t1209 = _t1210
	}
	attrs613 := _t1209
	p.consumeLiteral(")")
	_t1211 := attrs613
	if attrs613 == nil {
		_t1211 = []*pb.Attribute{}
	}
	_t1212 := &pb.MonoidDef{Monoid: monoid610, Name: relation_id611, Body: abstraction_with_arity612[0].(*pb.Abstraction), Attrs: _t1211, ValueArity: abstraction_with_arity612[1].(int64)}
	return _t1212
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1213 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1214 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1214 = 3
		} else {
			var _t1215 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1215 = 0
			} else {
				var _t1216 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1216 = 1
				} else {
					var _t1217 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1217 = 2
					} else {
						_t1217 = -1
					}
					_t1216 = _t1217
				}
				_t1215 = _t1216
			}
			_t1214 = _t1215
		}
		_t1213 = _t1214
	} else {
		_t1213 = -1
	}
	prediction614 := _t1213
	var _t1218 *pb.Monoid
	if prediction614 == 3 {
		_t1219 := p.parse_sum_monoid()
		sum_monoid618 := _t1219
		_t1220 := &pb.Monoid{}
		_t1220.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid618}
		_t1218 = _t1220
	} else {
		var _t1221 *pb.Monoid
		if prediction614 == 2 {
			_t1222 := p.parse_max_monoid()
			max_monoid617 := _t1222
			_t1223 := &pb.Monoid{}
			_t1223.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid617}
			_t1221 = _t1223
		} else {
			var _t1224 *pb.Monoid
			if prediction614 == 1 {
				_t1225 := p.parse_min_monoid()
				min_monoid616 := _t1225
				_t1226 := &pb.Monoid{}
				_t1226.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid616}
				_t1224 = _t1226
			} else {
				var _t1227 *pb.Monoid
				if prediction614 == 0 {
					_t1228 := p.parse_or_monoid()
					or_monoid615 := _t1228
					_t1229 := &pb.Monoid{}
					_t1229.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid615}
					_t1227 = _t1229
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1224 = _t1227
			}
			_t1221 = _t1224
		}
		_t1218 = _t1221
	}
	return _t1218
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1230 := &pb.OrMonoid{}
	return _t1230
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1231 := p.parse_type()
	type619 := _t1231
	p.consumeLiteral(")")
	_t1232 := &pb.MinMonoid{Type: type619}
	return _t1232
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1233 := p.parse_type()
	type620 := _t1233
	p.consumeLiteral(")")
	_t1234 := &pb.MaxMonoid{Type: type620}
	return _t1234
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1235 := p.parse_type()
	type621 := _t1235
	p.consumeLiteral(")")
	_t1236 := &pb.SumMonoid{Type: type621}
	return _t1236
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1237 := p.parse_monoid()
	monoid622 := _t1237
	_t1238 := p.parse_relation_id()
	relation_id623 := _t1238
	_t1239 := p.parse_abstraction_with_arity()
	abstraction_with_arity624 := _t1239
	var _t1240 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1241 := p.parse_attrs()
		_t1240 = _t1241
	}
	attrs625 := _t1240
	p.consumeLiteral(")")
	_t1242 := attrs625
	if attrs625 == nil {
		_t1242 = []*pb.Attribute{}
	}
	_t1243 := &pb.MonusDef{Monoid: monoid622, Name: relation_id623, Body: abstraction_with_arity624[0].(*pb.Abstraction), Attrs: _t1242, ValueArity: abstraction_with_arity624[1].(int64)}
	return _t1243
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1244 := p.parse_relation_id()
	relation_id626 := _t1244
	_t1245 := p.parse_abstraction()
	abstraction627 := _t1245
	_t1246 := p.parse_functional_dependency_keys()
	functional_dependency_keys628 := _t1246
	_t1247 := p.parse_functional_dependency_values()
	functional_dependency_values629 := _t1247
	p.consumeLiteral(")")
	_t1248 := &pb.FunctionalDependency{Guard: abstraction627, Keys: functional_dependency_keys628, Values: functional_dependency_values629}
	_t1249 := &pb.Constraint{Name: relation_id626}
	_t1249.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1248}
	return _t1249
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs630 := []*pb.Var{}
	cond631 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond631 {
		_t1250 := p.parse_var()
		item632 := _t1250
		xs630 = append(xs630, item632)
		cond631 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars633 := xs630
	p.consumeLiteral(")")
	return vars633
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs634 := []*pb.Var{}
	cond635 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond635 {
		_t1251 := p.parse_var()
		item636 := _t1251
		xs634 = append(xs634, item636)
		cond635 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars637 := xs634
	p.consumeLiteral(")")
	return vars637
}

func (p *Parser) parse_data() *pb.Data {
	var _t1252 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1253 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1253 = 0
		} else {
			var _t1254 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1254 = 2
			} else {
				var _t1255 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1255 = 1
				} else {
					_t1255 = -1
				}
				_t1254 = _t1255
			}
			_t1253 = _t1254
		}
		_t1252 = _t1253
	} else {
		_t1252 = -1
	}
	prediction638 := _t1252
	var _t1256 *pb.Data
	if prediction638 == 2 {
		_t1257 := p.parse_csv_data()
		csv_data641 := _t1257
		_t1258 := &pb.Data{}
		_t1258.DataType = &pb.Data_CsvData{CsvData: csv_data641}
		_t1256 = _t1258
	} else {
		var _t1259 *pb.Data
		if prediction638 == 1 {
			_t1260 := p.parse_betree_relation()
			betree_relation640 := _t1260
			_t1261 := &pb.Data{}
			_t1261.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation640}
			_t1259 = _t1261
		} else {
			var _t1262 *pb.Data
			if prediction638 == 0 {
				_t1263 := p.parse_rel_edb()
				rel_edb639 := _t1263
				_t1264 := &pb.Data{}
				_t1264.DataType = &pb.Data_RelEdb{RelEdb: rel_edb639}
				_t1262 = _t1264
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1259 = _t1262
		}
		_t1256 = _t1259
	}
	return _t1256
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1265 := p.parse_relation_id()
	relation_id642 := _t1265
	_t1266 := p.parse_rel_edb_path()
	rel_edb_path643 := _t1266
	_t1267 := p.parse_rel_edb_types()
	rel_edb_types644 := _t1267
	p.consumeLiteral(")")
	_t1268 := &pb.RelEDB{TargetId: relation_id642, Path: rel_edb_path643, Types: rel_edb_types644}
	return _t1268
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs645 := []string{}
	cond646 := p.matchLookaheadTerminal("STRING", 0)
	for cond646 {
		item647 := p.consumeTerminal("STRING").Value.str
		xs645 = append(xs645, item647)
		cond646 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings648 := xs645
	p.consumeLiteral("]")
	return strings648
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs649 := []*pb.Type{}
	cond650 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond650 {
		_t1269 := p.parse_type()
		item651 := _t1269
		xs649 = append(xs649, item651)
		cond650 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types652 := xs649
	p.consumeLiteral("]")
	return types652
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1270 := p.parse_relation_id()
	relation_id653 := _t1270
	_t1271 := p.parse_betree_info()
	betree_info654 := _t1271
	p.consumeLiteral(")")
	_t1272 := &pb.BeTreeRelation{Name: relation_id653, RelationInfo: betree_info654}
	return _t1272
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1273 := p.parse_betree_info_key_types()
	betree_info_key_types655 := _t1273
	_t1274 := p.parse_betree_info_value_types()
	betree_info_value_types656 := _t1274
	_t1275 := p.parse_config_dict()
	config_dict657 := _t1275
	p.consumeLiteral(")")
	_t1276 := p.construct_betree_info(betree_info_key_types655, betree_info_value_types656, config_dict657)
	return _t1276
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs658 := []*pb.Type{}
	cond659 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond659 {
		_t1277 := p.parse_type()
		item660 := _t1277
		xs658 = append(xs658, item660)
		cond659 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types661 := xs658
	p.consumeLiteral(")")
	return types661
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs662 := []*pb.Type{}
	cond663 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond663 {
		_t1278 := p.parse_type()
		item664 := _t1278
		xs662 = append(xs662, item664)
		cond663 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types665 := xs662
	p.consumeLiteral(")")
	return types665
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1279 := p.parse_csvlocator()
	csvlocator666 := _t1279
	_t1280 := p.parse_csv_config()
	csv_config667 := _t1280
	_t1281 := p.parse_csv_columns()
	csv_columns668 := _t1281
	_t1282 := p.parse_csv_asof()
	csv_asof669 := _t1282
	p.consumeLiteral(")")
	_t1283 := &pb.CSVData{Locator: csvlocator666, Config: csv_config667, Columns: csv_columns668, Asof: csv_asof669}
	return _t1283
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1284 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1285 := p.parse_csv_locator_paths()
		_t1284 = _t1285
	}
	csv_locator_paths670 := _t1284
	var _t1286 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1287 := p.parse_csv_locator_inline_data()
		_t1286 = ptr(_t1287)
	}
	csv_locator_inline_data671 := _t1286
	p.consumeLiteral(")")
	_t1288 := csv_locator_paths670
	if csv_locator_paths670 == nil {
		_t1288 = []string{}
	}
	_t1289 := &pb.CSVLocator{Paths: _t1288, InlineData: []byte(deref(csv_locator_inline_data671, ""))}
	return _t1289
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs672 := []string{}
	cond673 := p.matchLookaheadTerminal("STRING", 0)
	for cond673 {
		item674 := p.consumeTerminal("STRING").Value.str
		xs672 = append(xs672, item674)
		cond673 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings675 := xs672
	p.consumeLiteral(")")
	return strings675
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string676 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string676
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1290 := p.parse_config_dict()
	config_dict677 := _t1290
	p.consumeLiteral(")")
	_t1291 := p.construct_csv_config(config_dict677)
	return _t1291
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs678 := []*pb.CSVColumn{}
	cond679 := p.matchLookaheadLiteral("(", 0)
	for cond679 {
		_t1292 := p.parse_csv_column()
		item680 := _t1292
		xs678 = append(xs678, item680)
		cond679 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns681 := xs678
	p.consumeLiteral(")")
	return csv_columns681
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1293 := p.parse_csv_column_path()
	csv_column_path682 := _t1293
	var _t1294 []interface{}
	if ((p.matchLookaheadLiteral(":", 0) || p.matchLookaheadLiteral("[", 0)) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1295 := p.parse_csv_column_tail()
		_t1294 = _t1295
	}
	csv_column_tail683 := _t1294
	p.consumeLiteral(")")
	_t1296 := p.construct_csv_column(csv_column_path682, csv_column_tail683)
	return _t1296
}

func (p *Parser) parse_csv_column_path() []string {
	var _t1297 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1297 = 1
	} else {
		var _t1298 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1298 = 0
		} else {
			_t1298 = -1
		}
		_t1297 = _t1298
	}
	prediction684 := _t1297
	var _t1299 []string
	if prediction684 == 1 {
		p.consumeLiteral("[")
		xs686 := []string{}
		cond687 := p.matchLookaheadTerminal("STRING", 0)
		for cond687 {
			item688 := p.consumeTerminal("STRING").Value.str
			xs686 = append(xs686, item688)
			cond687 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings689 := xs686
		p.consumeLiteral("]")
		_t1299 = strings689
	} else {
		var _t1300 []string
		if prediction684 == 0 {
			string685 := p.consumeTerminal("STRING").Value.str
			_ = string685
			_t1300 = []string{string685}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in csv_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1299 = _t1300
	}
	return _t1299
}

func (p *Parser) parse_csv_column_tail() []interface{} {
	var _t1301 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1301 = 1
	} else {
		var _t1302 int64
		if p.matchLookaheadLiteral(":", 0) {
			_t1302 = 0
		} else {
			var _t1303 int64
			if p.matchLookaheadTerminal("UINT128", 0) {
				_t1303 = 0
			} else {
				_t1303 = -1
			}
			_t1302 = _t1303
		}
		_t1301 = _t1302
	}
	prediction690 := _t1301
	var _t1304 []interface{}
	if prediction690 == 1 {
		p.consumeLiteral("[")
		xs696 := []*pb.Type{}
		cond697 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
		for cond697 {
			_t1305 := p.parse_type()
			item698 := _t1305
			xs696 = append(xs696, item698)
			cond697 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
		}
		types699 := xs696
		p.consumeLiteral("]")
		_t1304 = []interface{}{nil, types699}
	} else {
		var _t1306 []interface{}
		if prediction690 == 0 {
			_t1307 := p.parse_relation_id()
			relation_id691 := _t1307
			p.consumeLiteral("[")
			xs692 := []*pb.Type{}
			cond693 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
			for cond693 {
				_t1308 := p.parse_type()
				item694 := _t1308
				xs692 = append(xs692, item694)
				cond693 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
			}
			types695 := xs692
			p.consumeLiteral("]")
			_t1306 = []interface{}{relation_id691, types695}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in csv_column_tail", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1304 = _t1306
	}
	return _t1304
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string700 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string700
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1309 := p.parse_fragment_id()
	fragment_id701 := _t1309
	p.consumeLiteral(")")
	_t1310 := &pb.Undefine{FragmentId: fragment_id701}
	return _t1310
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs702 := []*pb.RelationId{}
	cond703 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond703 {
		_t1311 := p.parse_relation_id()
		item704 := _t1311
		xs702 = append(xs702, item704)
		cond703 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids705 := xs702
	p.consumeLiteral(")")
	_t1312 := &pb.Context{Relations: relation_ids705}
	return _t1312
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1313 := p.parse_rel_edb_path()
	rel_edb_path706 := _t1313
	_t1314 := p.parse_relation_id()
	relation_id707 := _t1314
	p.consumeLiteral(")")
	_t1315 := &pb.Snapshot{DestinationPath: rel_edb_path706, SourceRelation: relation_id707}
	return _t1315
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs708 := []*pb.Read{}
	cond709 := p.matchLookaheadLiteral("(", 0)
	for cond709 {
		_t1316 := p.parse_read()
		item710 := _t1316
		xs708 = append(xs708, item710)
		cond709 = p.matchLookaheadLiteral("(", 0)
	}
	reads711 := xs708
	p.consumeLiteral(")")
	return reads711
}

func (p *Parser) parse_read() *pb.Read {
	var _t1317 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1318 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1318 = 2
		} else {
			var _t1319 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1319 = 1
			} else {
				var _t1320 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1320 = 4
				} else {
					var _t1321 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1321 = 0
					} else {
						var _t1322 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1322 = 3
						} else {
							_t1322 = -1
						}
						_t1321 = _t1322
					}
					_t1320 = _t1321
				}
				_t1319 = _t1320
			}
			_t1318 = _t1319
		}
		_t1317 = _t1318
	} else {
		_t1317 = -1
	}
	prediction712 := _t1317
	var _t1323 *pb.Read
	if prediction712 == 4 {
		_t1324 := p.parse_export()
		export717 := _t1324
		_t1325 := &pb.Read{}
		_t1325.ReadType = &pb.Read_Export{Export: export717}
		_t1323 = _t1325
	} else {
		var _t1326 *pb.Read
		if prediction712 == 3 {
			_t1327 := p.parse_abort()
			abort716 := _t1327
			_t1328 := &pb.Read{}
			_t1328.ReadType = &pb.Read_Abort{Abort: abort716}
			_t1326 = _t1328
		} else {
			var _t1329 *pb.Read
			if prediction712 == 2 {
				_t1330 := p.parse_what_if()
				what_if715 := _t1330
				_t1331 := &pb.Read{}
				_t1331.ReadType = &pb.Read_WhatIf{WhatIf: what_if715}
				_t1329 = _t1331
			} else {
				var _t1332 *pb.Read
				if prediction712 == 1 {
					_t1333 := p.parse_output()
					output714 := _t1333
					_t1334 := &pb.Read{}
					_t1334.ReadType = &pb.Read_Output{Output: output714}
					_t1332 = _t1334
				} else {
					var _t1335 *pb.Read
					if prediction712 == 0 {
						_t1336 := p.parse_demand()
						demand713 := _t1336
						_t1337 := &pb.Read{}
						_t1337.ReadType = &pb.Read_Demand{Demand: demand713}
						_t1335 = _t1337
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1332 = _t1335
				}
				_t1329 = _t1332
			}
			_t1326 = _t1329
		}
		_t1323 = _t1326
	}
	return _t1323
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1338 := p.parse_relation_id()
	relation_id718 := _t1338
	p.consumeLiteral(")")
	_t1339 := &pb.Demand{RelationId: relation_id718}
	return _t1339
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1340 := p.parse_name()
	name719 := _t1340
	_t1341 := p.parse_relation_id()
	relation_id720 := _t1341
	p.consumeLiteral(")")
	_t1342 := &pb.Output{Name: name719, RelationId: relation_id720}
	return _t1342
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1343 := p.parse_name()
	name721 := _t1343
	_t1344 := p.parse_epoch()
	epoch722 := _t1344
	p.consumeLiteral(")")
	_t1345 := &pb.WhatIf{Branch: name721, Epoch: epoch722}
	return _t1345
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1346 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1347 := p.parse_name()
		_t1346 = ptr(_t1347)
	}
	name723 := _t1346
	_t1348 := p.parse_relation_id()
	relation_id724 := _t1348
	p.consumeLiteral(")")
	_t1349 := &pb.Abort{Name: deref(name723, "abort"), RelationId: relation_id724}
	return _t1349
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1350 := p.parse_export_csv_config()
	export_csv_config725 := _t1350
	p.consumeLiteral(")")
	_t1351 := &pb.Export{}
	_t1351.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config725}
	return _t1351
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1352 := p.parse_export_csv_path()
	export_csv_path726 := _t1352
	_t1353 := p.parse_export_csv_columns()
	export_csv_columns727 := _t1353
	_t1354 := p.parse_config_dict()
	config_dict728 := _t1354
	p.consumeLiteral(")")
	_t1355 := p.export_csv_config(export_csv_path726, export_csv_columns727, config_dict728)
	return _t1355
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string729 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string729
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs730 := []*pb.ExportCSVColumn{}
	cond731 := p.matchLookaheadLiteral("(", 0)
	for cond731 {
		_t1356 := p.parse_export_csv_column()
		item732 := _t1356
		xs730 = append(xs730, item732)
		cond731 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns733 := xs730
	p.consumeLiteral(")")
	return export_csv_columns733
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string734 := p.consumeTerminal("STRING").Value.str
	_t1357 := p.parse_relation_id()
	relation_id735 := _t1357
	p.consumeLiteral(")")
	_t1358 := &pb.ExportCSVColumn{ColumnName: string734, ColumnData: relation_id735}
	return _t1358
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
