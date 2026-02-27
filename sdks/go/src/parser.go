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
	var _t1389 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1389
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1390 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1390
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1391 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1391
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1392 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1392
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1393 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1393
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1394 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1394
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1395 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1395
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1396 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1396
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1397 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1397
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1398 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1398
	_t1399 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1399
	_t1400 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1400
	_t1401 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1401
	_t1402 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1402
	_t1403 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1403
	_t1404 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1404
	_t1405 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1405
	_t1406 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1406
	_t1407 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1407
	_t1408 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1408
	_t1409 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1409
	_t1410 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1410
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1411 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1411
	_t1412 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1412
	_t1413 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1413
	_t1414 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1414
	_t1415 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1415
	_t1416 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1416
	_t1417 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1417
	_t1418 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1418
	_t1419 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1419
	_t1420 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1420.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1420.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1420
	_t1421 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1421
}

func (p *Parser) default_configure() *pb.Configure {
	_t1422 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1422
	_t1423 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1423
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
	_t1424 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1424
	_t1425 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1425
	_t1426 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1426
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1427 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1427
	_t1428 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1428
	_t1429 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1429
	_t1430 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1430
	_t1431 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1431
	_t1432 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1432
	_t1433 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1433
	_t1434 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1434
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1435 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1435
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t752 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t753 := p.parse_configure()
		_t752 = _t753
	}
	configure376 := _t752
	var _t754 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t755 := p.parse_sync()
		_t754 = _t755
	}
	sync377 := _t754
	xs378 := []*pb.Epoch{}
	cond379 := p.matchLookaheadLiteral("(", 0)
	for cond379 {
		_t756 := p.parse_epoch()
		item380 := _t756
		xs378 = append(xs378, item380)
		cond379 = p.matchLookaheadLiteral("(", 0)
	}
	epochs381 := xs378
	p.consumeLiteral(")")
	_t757 := p.default_configure()
	_t758 := configure376
	if configure376 == nil {
		_t758 = _t757
	}
	_t759 := &pb.Transaction{Epochs: epochs381, Configure: _t758, Sync: sync377}
	return _t759
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t760 := p.parse_config_dict()
	config_dict382 := _t760
	p.consumeLiteral(")")
	_t761 := p.construct_configure(config_dict382)
	return _t761
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs383 := [][]interface{}{}
	cond384 := p.matchLookaheadLiteral(":", 0)
	for cond384 {
		_t762 := p.parse_config_key_value()
		item385 := _t762
		xs383 = append(xs383, item385)
		cond384 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values386 := xs383
	p.consumeLiteral("}")
	return config_key_values386
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol387 := p.consumeTerminal("SYMBOL").Value.str
	_t763 := p.parse_value()
	value388 := _t763
	return []interface{}{symbol387, value388}
}

func (p *Parser) parse_value() *pb.Value {
	var _t764 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t764 = 9
	} else {
		var _t765 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t765 = 8
		} else {
			var _t766 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t766 = 9
			} else {
				var _t767 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t768 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t768 = 1
					} else {
						var _t769 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t769 = 0
						} else {
							_t769 = -1
						}
						_t768 = _t769
					}
					_t767 = _t768
				} else {
					var _t770 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t770 = 5
					} else {
						var _t771 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t771 = 2
						} else {
							var _t772 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t772 = 6
							} else {
								var _t773 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t773 = 3
								} else {
									var _t774 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t774 = 4
									} else {
										var _t775 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t775 = 7
										} else {
											_t775 = -1
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
					}
					_t767 = _t770
				}
				_t766 = _t767
			}
			_t765 = _t766
		}
		_t764 = _t765
	}
	prediction389 := _t764
	var _t776 *pb.Value
	if prediction389 == 9 {
		_t777 := p.parse_boolean_value()
		boolean_value398 := _t777
		_t778 := &pb.Value{}
		_t778.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value398}
		_t776 = _t778
	} else {
		var _t779 *pb.Value
		if prediction389 == 8 {
			p.consumeLiteral("missing")
			_t780 := &pb.MissingValue{}
			_t781 := &pb.Value{}
			_t781.Value = &pb.Value_MissingValue{MissingValue: _t780}
			_t779 = _t781
		} else {
			var _t782 *pb.Value
			if prediction389 == 7 {
				decimal397 := p.consumeTerminal("DECIMAL").Value.decimal
				_t783 := &pb.Value{}
				_t783.Value = &pb.Value_DecimalValue{DecimalValue: decimal397}
				_t782 = _t783
			} else {
				var _t784 *pb.Value
				if prediction389 == 6 {
					int128396 := p.consumeTerminal("INT128").Value.int128
					_t785 := &pb.Value{}
					_t785.Value = &pb.Value_Int128Value{Int128Value: int128396}
					_t784 = _t785
				} else {
					var _t786 *pb.Value
					if prediction389 == 5 {
						uint128395 := p.consumeTerminal("UINT128").Value.uint128
						_t787 := &pb.Value{}
						_t787.Value = &pb.Value_Uint128Value{Uint128Value: uint128395}
						_t786 = _t787
					} else {
						var _t788 *pb.Value
						if prediction389 == 4 {
							float394 := p.consumeTerminal("FLOAT").Value.f64
							_t789 := &pb.Value{}
							_t789.Value = &pb.Value_FloatValue{FloatValue: float394}
							_t788 = _t789
						} else {
							var _t790 *pb.Value
							if prediction389 == 3 {
								int393 := p.consumeTerminal("INT").Value.i64
								_t791 := &pb.Value{}
								_t791.Value = &pb.Value_IntValue{IntValue: int393}
								_t790 = _t791
							} else {
								var _t792 *pb.Value
								if prediction389 == 2 {
									string392 := p.consumeTerminal("STRING").Value.str
									_t793 := &pb.Value{}
									_t793.Value = &pb.Value_StringValue{StringValue: string392}
									_t792 = _t793
								} else {
									var _t794 *pb.Value
									if prediction389 == 1 {
										_t795 := p.parse_datetime()
										datetime391 := _t795
										_t796 := &pb.Value{}
										_t796.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime391}
										_t794 = _t796
									} else {
										var _t797 *pb.Value
										if prediction389 == 0 {
											_t798 := p.parse_date()
											date390 := _t798
											_t799 := &pb.Value{}
											_t799.Value = &pb.Value_DateValue{DateValue: date390}
											_t797 = _t799
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t794 = _t797
									}
									_t792 = _t794
								}
								_t790 = _t792
							}
							_t788 = _t790
						}
						_t786 = _t788
					}
					_t784 = _t786
				}
				_t782 = _t784
			}
			_t779 = _t782
		}
		_t776 = _t779
	}
	return _t776
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int399 := p.consumeTerminal("INT").Value.i64
	int_3400 := p.consumeTerminal("INT").Value.i64
	int_4401 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t800 := &pb.DateValue{Year: int32(int399), Month: int32(int_3400), Day: int32(int_4401)}
	return _t800
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int402 := p.consumeTerminal("INT").Value.i64
	int_3403 := p.consumeTerminal("INT").Value.i64
	int_4404 := p.consumeTerminal("INT").Value.i64
	int_5405 := p.consumeTerminal("INT").Value.i64
	int_6406 := p.consumeTerminal("INT").Value.i64
	int_7407 := p.consumeTerminal("INT").Value.i64
	var _t801 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t801 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8408 := _t801
	p.consumeLiteral(")")
	_t802 := &pb.DateTimeValue{Year: int32(int402), Month: int32(int_3403), Day: int32(int_4404), Hour: int32(int_5405), Minute: int32(int_6406), Second: int32(int_7407), Microsecond: int32(deref(int_8408, 0))}
	return _t802
}

func (p *Parser) parse_boolean_value() bool {
	var _t803 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t803 = 0
	} else {
		var _t804 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t804 = 1
		} else {
			_t804 = -1
		}
		_t803 = _t804
	}
	prediction409 := _t803
	var _t805 bool
	if prediction409 == 1 {
		p.consumeLiteral("false")
		_t805 = false
	} else {
		var _t806 bool
		if prediction409 == 0 {
			p.consumeLiteral("true")
			_t806 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t805 = _t806
	}
	return _t805
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs410 := []*pb.FragmentId{}
	cond411 := p.matchLookaheadLiteral(":", 0)
	for cond411 {
		_t807 := p.parse_fragment_id()
		item412 := _t807
		xs410 = append(xs410, item412)
		cond411 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids413 := xs410
	p.consumeLiteral(")")
	_t808 := &pb.Sync{Fragments: fragment_ids413}
	return _t808
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol414 := p.consumeTerminal("SYMBOL").Value.str
	return &pb.FragmentId{Id: []byte(symbol414)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t809 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t810 := p.parse_epoch_writes()
		_t809 = _t810
	}
	epoch_writes415 := _t809
	var _t811 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t812 := p.parse_epoch_reads()
		_t811 = _t812
	}
	epoch_reads416 := _t811
	p.consumeLiteral(")")
	_t813 := epoch_writes415
	if epoch_writes415 == nil {
		_t813 = []*pb.Write{}
	}
	_t814 := epoch_reads416
	if epoch_reads416 == nil {
		_t814 = []*pb.Read{}
	}
	_t815 := &pb.Epoch{Writes: _t813, Reads: _t814}
	return _t815
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs417 := []*pb.Write{}
	cond418 := p.matchLookaheadLiteral("(", 0)
	for cond418 {
		_t816 := p.parse_write()
		item419 := _t816
		xs417 = append(xs417, item419)
		cond418 = p.matchLookaheadLiteral("(", 0)
	}
	writes420 := xs417
	p.consumeLiteral(")")
	return writes420
}

func (p *Parser) parse_write() *pb.Write {
	var _t817 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t818 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t818 = 1
		} else {
			var _t819 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t819 = 3
			} else {
				var _t820 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t820 = 0
				} else {
					var _t821 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t821 = 2
					} else {
						_t821 = -1
					}
					_t820 = _t821
				}
				_t819 = _t820
			}
			_t818 = _t819
		}
		_t817 = _t818
	} else {
		_t817 = -1
	}
	prediction421 := _t817
	var _t822 *pb.Write
	if prediction421 == 3 {
		_t823 := p.parse_snapshot()
		snapshot425 := _t823
		_t824 := &pb.Write{}
		_t824.WriteType = &pb.Write_Snapshot{Snapshot: snapshot425}
		_t822 = _t824
	} else {
		var _t825 *pb.Write
		if prediction421 == 2 {
			_t826 := p.parse_context()
			context424 := _t826
			_t827 := &pb.Write{}
			_t827.WriteType = &pb.Write_Context{Context: context424}
			_t825 = _t827
		} else {
			var _t828 *pb.Write
			if prediction421 == 1 {
				_t829 := p.parse_undefine()
				undefine423 := _t829
				_t830 := &pb.Write{}
				_t830.WriteType = &pb.Write_Undefine{Undefine: undefine423}
				_t828 = _t830
			} else {
				var _t831 *pb.Write
				if prediction421 == 0 {
					_t832 := p.parse_define()
					define422 := _t832
					_t833 := &pb.Write{}
					_t833.WriteType = &pb.Write_Define{Define: define422}
					_t831 = _t833
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t828 = _t831
			}
			_t825 = _t828
		}
		_t822 = _t825
	}
	return _t822
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t834 := p.parse_fragment()
	fragment426 := _t834
	p.consumeLiteral(")")
	_t835 := &pb.Define{Fragment: fragment426}
	return _t835
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t836 := p.parse_new_fragment_id()
	new_fragment_id427 := _t836
	xs428 := []*pb.Declaration{}
	cond429 := p.matchLookaheadLiteral("(", 0)
	for cond429 {
		_t837 := p.parse_declaration()
		item430 := _t837
		xs428 = append(xs428, item430)
		cond429 = p.matchLookaheadLiteral("(", 0)
	}
	declarations431 := xs428
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id427, declarations431)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t838 := p.parse_fragment_id()
	fragment_id432 := _t838
	p.startFragment(fragment_id432)
	return fragment_id432
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t839 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t840 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t840 = 2
		} else {
			var _t841 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t841 = 3
			} else {
				var _t842 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t842 = 0
				} else {
					var _t843 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t843 = 3
					} else {
						var _t844 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t844 = 3
						} else {
							var _t845 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t845 = 1
							} else {
								_t845 = -1
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
	} else {
		_t839 = -1
	}
	prediction433 := _t839
	var _t846 *pb.Declaration
	if prediction433 == 3 {
		_t847 := p.parse_data()
		data437 := _t847
		_t848 := &pb.Declaration{}
		_t848.DeclarationType = &pb.Declaration_Data{Data: data437}
		_t846 = _t848
	} else {
		var _t849 *pb.Declaration
		if prediction433 == 2 {
			_t850 := p.parse_constraint()
			constraint436 := _t850
			_t851 := &pb.Declaration{}
			_t851.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint436}
			_t849 = _t851
		} else {
			var _t852 *pb.Declaration
			if prediction433 == 1 {
				_t853 := p.parse_algorithm()
				algorithm435 := _t853
				_t854 := &pb.Declaration{}
				_t854.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm435}
				_t852 = _t854
			} else {
				var _t855 *pb.Declaration
				if prediction433 == 0 {
					_t856 := p.parse_def()
					def434 := _t856
					_t857 := &pb.Declaration{}
					_t857.DeclarationType = &pb.Declaration_Def{Def: def434}
					_t855 = _t857
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t852 = _t855
			}
			_t849 = _t852
		}
		_t846 = _t849
	}
	return _t846
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t858 := p.parse_relation_id()
	relation_id438 := _t858
	_t859 := p.parse_abstraction()
	abstraction439 := _t859
	var _t860 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t861 := p.parse_attrs()
		_t860 = _t861
	}
	attrs440 := _t860
	p.consumeLiteral(")")
	_t862 := attrs440
	if attrs440 == nil {
		_t862 = []*pb.Attribute{}
	}
	_t863 := &pb.Def{Name: relation_id438, Body: abstraction439, Attrs: _t862}
	return _t863
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t864 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t864 = 0
	} else {
		var _t865 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t865 = 1
		} else {
			_t865 = -1
		}
		_t864 = _t865
	}
	prediction441 := _t864
	var _t866 *pb.RelationId
	if prediction441 == 1 {
		uint128443 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128443
		_t866 = &pb.RelationId{IdLow: uint128443.Low, IdHigh: uint128443.High}
	} else {
		var _t867 *pb.RelationId
		if prediction441 == 0 {
			p.consumeLiteral(":")
			symbol442 := p.consumeTerminal("SYMBOL").Value.str
			_t867 = p.relationIdFromString(symbol442)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t866 = _t867
	}
	return _t866
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t868 := p.parse_bindings()
	bindings444 := _t868
	_t869 := p.parse_formula()
	formula445 := _t869
	p.consumeLiteral(")")
	_t870 := &pb.Abstraction{Vars: listConcat(bindings444[0].([]*pb.Binding), bindings444[1].([]*pb.Binding)), Value: formula445}
	return _t870
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs446 := []*pb.Binding{}
	cond447 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond447 {
		_t871 := p.parse_binding()
		item448 := _t871
		xs446 = append(xs446, item448)
		cond447 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings449 := xs446
	var _t872 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t873 := p.parse_value_bindings()
		_t872 = _t873
	}
	value_bindings450 := _t872
	p.consumeLiteral("]")
	_t874 := value_bindings450
	if value_bindings450 == nil {
		_t874 = []*pb.Binding{}
	}
	return []interface{}{bindings449, _t874}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol451 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t875 := p.parse_type()
	type452 := _t875
	_t876 := &pb.Var{Name: symbol451}
	_t877 := &pb.Binding{Var: _t876, Type: type452}
	return _t877
}

func (p *Parser) parse_type() *pb.Type {
	var _t878 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t878 = 0
	} else {
		var _t879 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t879 = 4
		} else {
			var _t880 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t880 = 1
			} else {
				var _t881 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t881 = 8
				} else {
					var _t882 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t882 = 5
					} else {
						var _t883 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t883 = 2
						} else {
							var _t884 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t884 = 3
							} else {
								var _t885 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t885 = 7
								} else {
									var _t886 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t886 = 6
									} else {
										var _t887 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t887 = 10
										} else {
											var _t888 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t888 = 9
											} else {
												_t888 = -1
											}
											_t887 = _t888
										}
										_t886 = _t887
									}
									_t885 = _t886
								}
								_t884 = _t885
							}
							_t883 = _t884
						}
						_t882 = _t883
					}
					_t881 = _t882
				}
				_t880 = _t881
			}
			_t879 = _t880
		}
		_t878 = _t879
	}
	prediction453 := _t878
	var _t889 *pb.Type
	if prediction453 == 10 {
		_t890 := p.parse_boolean_type()
		boolean_type464 := _t890
		_t891 := &pb.Type{}
		_t891.Type = &pb.Type_BooleanType{BooleanType: boolean_type464}
		_t889 = _t891
	} else {
		var _t892 *pb.Type
		if prediction453 == 9 {
			_t893 := p.parse_decimal_type()
			decimal_type463 := _t893
			_t894 := &pb.Type{}
			_t894.Type = &pb.Type_DecimalType{DecimalType: decimal_type463}
			_t892 = _t894
		} else {
			var _t895 *pb.Type
			if prediction453 == 8 {
				_t896 := p.parse_missing_type()
				missing_type462 := _t896
				_t897 := &pb.Type{}
				_t897.Type = &pb.Type_MissingType{MissingType: missing_type462}
				_t895 = _t897
			} else {
				var _t898 *pb.Type
				if prediction453 == 7 {
					_t899 := p.parse_datetime_type()
					datetime_type461 := _t899
					_t900 := &pb.Type{}
					_t900.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type461}
					_t898 = _t900
				} else {
					var _t901 *pb.Type
					if prediction453 == 6 {
						_t902 := p.parse_date_type()
						date_type460 := _t902
						_t903 := &pb.Type{}
						_t903.Type = &pb.Type_DateType{DateType: date_type460}
						_t901 = _t903
					} else {
						var _t904 *pb.Type
						if prediction453 == 5 {
							_t905 := p.parse_int128_type()
							int128_type459 := _t905
							_t906 := &pb.Type{}
							_t906.Type = &pb.Type_Int128Type{Int128Type: int128_type459}
							_t904 = _t906
						} else {
							var _t907 *pb.Type
							if prediction453 == 4 {
								_t908 := p.parse_uint128_type()
								uint128_type458 := _t908
								_t909 := &pb.Type{}
								_t909.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type458}
								_t907 = _t909
							} else {
								var _t910 *pb.Type
								if prediction453 == 3 {
									_t911 := p.parse_float_type()
									float_type457 := _t911
									_t912 := &pb.Type{}
									_t912.Type = &pb.Type_FloatType{FloatType: float_type457}
									_t910 = _t912
								} else {
									var _t913 *pb.Type
									if prediction453 == 2 {
										_t914 := p.parse_int_type()
										int_type456 := _t914
										_t915 := &pb.Type{}
										_t915.Type = &pb.Type_IntType{IntType: int_type456}
										_t913 = _t915
									} else {
										var _t916 *pb.Type
										if prediction453 == 1 {
											_t917 := p.parse_string_type()
											string_type455 := _t917
											_t918 := &pb.Type{}
											_t918.Type = &pb.Type_StringType{StringType: string_type455}
											_t916 = _t918
										} else {
											var _t919 *pb.Type
											if prediction453 == 0 {
												_t920 := p.parse_unspecified_type()
												unspecified_type454 := _t920
												_t921 := &pb.Type{}
												_t921.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type454}
												_t919 = _t921
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t916 = _t919
										}
										_t913 = _t916
									}
									_t910 = _t913
								}
								_t907 = _t910
							}
							_t904 = _t907
						}
						_t901 = _t904
					}
					_t898 = _t901
				}
				_t895 = _t898
			}
			_t892 = _t895
		}
		_t889 = _t892
	}
	return _t889
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t922 := &pb.UnspecifiedType{}
	return _t922
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t923 := &pb.StringType{}
	return _t923
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t924 := &pb.IntType{}
	return _t924
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t925 := &pb.FloatType{}
	return _t925
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t926 := &pb.UInt128Type{}
	return _t926
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t927 := &pb.Int128Type{}
	return _t927
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t928 := &pb.DateType{}
	return _t928
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t929 := &pb.DateTimeType{}
	return _t929
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t930 := &pb.MissingType{}
	return _t930
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int465 := p.consumeTerminal("INT").Value.i64
	int_3466 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t931 := &pb.DecimalType{Precision: int32(int465), Scale: int32(int_3466)}
	return _t931
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t932 := &pb.BooleanType{}
	return _t932
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs467 := []*pb.Binding{}
	cond468 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond468 {
		_t933 := p.parse_binding()
		item469 := _t933
		xs467 = append(xs467, item469)
		cond468 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings470 := xs467
	return bindings470
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t934 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t935 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t935 = 0
		} else {
			var _t936 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t936 = 11
			} else {
				var _t937 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t937 = 3
				} else {
					var _t938 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t938 = 10
					} else {
						var _t939 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t939 = 9
						} else {
							var _t940 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t940 = 5
							} else {
								var _t941 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t941 = 6
								} else {
									var _t942 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t942 = 7
									} else {
										var _t943 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t943 = 1
										} else {
											var _t944 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t944 = 2
											} else {
												var _t945 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t945 = 12
												} else {
													var _t946 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t946 = 8
													} else {
														var _t947 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t947 = 4
														} else {
															var _t948 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t948 = 10
															} else {
																var _t949 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t949 = 10
																} else {
																	var _t950 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t950 = 10
																	} else {
																		var _t951 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t951 = 10
																		} else {
																			var _t952 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t952 = 10
																			} else {
																				var _t953 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t953 = 10
																				} else {
																					var _t954 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t954 = 10
																					} else {
																						var _t955 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t955 = 10
																						} else {
																							var _t956 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t956 = 10
																							} else {
																								_t956 = -1
																							}
																							_t955 = _t956
																						}
																						_t954 = _t955
																					}
																					_t953 = _t954
																				}
																				_t952 = _t953
																			}
																			_t951 = _t952
																		}
																		_t950 = _t951
																	}
																	_t949 = _t950
																}
																_t948 = _t949
															}
															_t947 = _t948
														}
														_t946 = _t947
													}
													_t945 = _t946
												}
												_t944 = _t945
											}
											_t943 = _t944
										}
										_t942 = _t943
									}
									_t941 = _t942
								}
								_t940 = _t941
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
	} else {
		_t934 = -1
	}
	prediction471 := _t934
	var _t957 *pb.Formula
	if prediction471 == 12 {
		_t958 := p.parse_cast()
		cast484 := _t958
		_t959 := &pb.Formula{}
		_t959.FormulaType = &pb.Formula_Cast{Cast: cast484}
		_t957 = _t959
	} else {
		var _t960 *pb.Formula
		if prediction471 == 11 {
			_t961 := p.parse_rel_atom()
			rel_atom483 := _t961
			_t962 := &pb.Formula{}
			_t962.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom483}
			_t960 = _t962
		} else {
			var _t963 *pb.Formula
			if prediction471 == 10 {
				_t964 := p.parse_primitive()
				primitive482 := _t964
				_t965 := &pb.Formula{}
				_t965.FormulaType = &pb.Formula_Primitive{Primitive: primitive482}
				_t963 = _t965
			} else {
				var _t966 *pb.Formula
				if prediction471 == 9 {
					_t967 := p.parse_pragma()
					pragma481 := _t967
					_t968 := &pb.Formula{}
					_t968.FormulaType = &pb.Formula_Pragma{Pragma: pragma481}
					_t966 = _t968
				} else {
					var _t969 *pb.Formula
					if prediction471 == 8 {
						_t970 := p.parse_atom()
						atom480 := _t970
						_t971 := &pb.Formula{}
						_t971.FormulaType = &pb.Formula_Atom{Atom: atom480}
						_t969 = _t971
					} else {
						var _t972 *pb.Formula
						if prediction471 == 7 {
							_t973 := p.parse_ffi()
							ffi479 := _t973
							_t974 := &pb.Formula{}
							_t974.FormulaType = &pb.Formula_Ffi{Ffi: ffi479}
							_t972 = _t974
						} else {
							var _t975 *pb.Formula
							if prediction471 == 6 {
								_t976 := p.parse_not()
								not478 := _t976
								_t977 := &pb.Formula{}
								_t977.FormulaType = &pb.Formula_Not{Not: not478}
								_t975 = _t977
							} else {
								var _t978 *pb.Formula
								if prediction471 == 5 {
									_t979 := p.parse_disjunction()
									disjunction477 := _t979
									_t980 := &pb.Formula{}
									_t980.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction477}
									_t978 = _t980
								} else {
									var _t981 *pb.Formula
									if prediction471 == 4 {
										_t982 := p.parse_conjunction()
										conjunction476 := _t982
										_t983 := &pb.Formula{}
										_t983.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction476}
										_t981 = _t983
									} else {
										var _t984 *pb.Formula
										if prediction471 == 3 {
											_t985 := p.parse_reduce()
											reduce475 := _t985
											_t986 := &pb.Formula{}
											_t986.FormulaType = &pb.Formula_Reduce{Reduce: reduce475}
											_t984 = _t986
										} else {
											var _t987 *pb.Formula
											if prediction471 == 2 {
												_t988 := p.parse_exists()
												exists474 := _t988
												_t989 := &pb.Formula{}
												_t989.FormulaType = &pb.Formula_Exists{Exists: exists474}
												_t987 = _t989
											} else {
												var _t990 *pb.Formula
												if prediction471 == 1 {
													_t991 := p.parse_false()
													false473 := _t991
													_t992 := &pb.Formula{}
													_t992.FormulaType = &pb.Formula_Disjunction{Disjunction: false473}
													_t990 = _t992
												} else {
													var _t993 *pb.Formula
													if prediction471 == 0 {
														_t994 := p.parse_true()
														true472 := _t994
														_t995 := &pb.Formula{}
														_t995.FormulaType = &pb.Formula_Conjunction{Conjunction: true472}
														_t993 = _t995
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t990 = _t993
												}
												_t987 = _t990
											}
											_t984 = _t987
										}
										_t981 = _t984
									}
									_t978 = _t981
								}
								_t975 = _t978
							}
							_t972 = _t975
						}
						_t969 = _t972
					}
					_t966 = _t969
				}
				_t963 = _t966
			}
			_t960 = _t963
		}
		_t957 = _t960
	}
	return _t957
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t996 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t996
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t997 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t997
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t998 := p.parse_bindings()
	bindings485 := _t998
	_t999 := p.parse_formula()
	formula486 := _t999
	p.consumeLiteral(")")
	_t1000 := &pb.Abstraction{Vars: listConcat(bindings485[0].([]*pb.Binding), bindings485[1].([]*pb.Binding)), Value: formula486}
	_t1001 := &pb.Exists{Body: _t1000}
	return _t1001
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1002 := p.parse_abstraction()
	abstraction487 := _t1002
	_t1003 := p.parse_abstraction()
	abstraction_3488 := _t1003
	_t1004 := p.parse_terms()
	terms489 := _t1004
	p.consumeLiteral(")")
	_t1005 := &pb.Reduce{Op: abstraction487, Body: abstraction_3488, Terms: terms489}
	return _t1005
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs490 := []*pb.Term{}
	cond491 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond491 {
		_t1006 := p.parse_term()
		item492 := _t1006
		xs490 = append(xs490, item492)
		cond491 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms493 := xs490
	p.consumeLiteral(")")
	return terms493
}

func (p *Parser) parse_term() *pb.Term {
	var _t1007 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1007 = 1
	} else {
		var _t1008 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1008 = 1
		} else {
			var _t1009 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1009 = 1
			} else {
				var _t1010 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1010 = 1
				} else {
					var _t1011 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1011 = 1
					} else {
						var _t1012 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1012 = 0
						} else {
							var _t1013 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1013 = 1
							} else {
								var _t1014 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1014 = 1
								} else {
									var _t1015 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1015 = 1
									} else {
										var _t1016 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1016 = 1
										} else {
											var _t1017 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1017 = 1
											} else {
												_t1017 = -1
											}
											_t1016 = _t1017
										}
										_t1015 = _t1016
									}
									_t1014 = _t1015
								}
								_t1013 = _t1014
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
	prediction494 := _t1007
	var _t1018 *pb.Term
	if prediction494 == 1 {
		_t1019 := p.parse_constant()
		constant496 := _t1019
		_t1020 := &pb.Term{}
		_t1020.TermType = &pb.Term_Constant{Constant: constant496}
		_t1018 = _t1020
	} else {
		var _t1021 *pb.Term
		if prediction494 == 0 {
			_t1022 := p.parse_var()
			var495 := _t1022
			_t1023 := &pb.Term{}
			_t1023.TermType = &pb.Term_Var{Var: var495}
			_t1021 = _t1023
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1018 = _t1021
	}
	return _t1018
}

func (p *Parser) parse_var() *pb.Var {
	symbol497 := p.consumeTerminal("SYMBOL").Value.str
	_t1024 := &pb.Var{Name: symbol497}
	return _t1024
}

func (p *Parser) parse_constant() *pb.Value {
	_t1025 := p.parse_value()
	value498 := _t1025
	return value498
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs499 := []*pb.Formula{}
	cond500 := p.matchLookaheadLiteral("(", 0)
	for cond500 {
		_t1026 := p.parse_formula()
		item501 := _t1026
		xs499 = append(xs499, item501)
		cond500 = p.matchLookaheadLiteral("(", 0)
	}
	formulas502 := xs499
	p.consumeLiteral(")")
	_t1027 := &pb.Conjunction{Args: formulas502}
	return _t1027
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs503 := []*pb.Formula{}
	cond504 := p.matchLookaheadLiteral("(", 0)
	for cond504 {
		_t1028 := p.parse_formula()
		item505 := _t1028
		xs503 = append(xs503, item505)
		cond504 = p.matchLookaheadLiteral("(", 0)
	}
	formulas506 := xs503
	p.consumeLiteral(")")
	_t1029 := &pb.Disjunction{Args: formulas506}
	return _t1029
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1030 := p.parse_formula()
	formula507 := _t1030
	p.consumeLiteral(")")
	_t1031 := &pb.Not{Arg: formula507}
	return _t1031
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1032 := p.parse_name()
	name508 := _t1032
	_t1033 := p.parse_ffi_args()
	ffi_args509 := _t1033
	_t1034 := p.parse_terms()
	terms510 := _t1034
	p.consumeLiteral(")")
	_t1035 := &pb.FFI{Name: name508, Args: ffi_args509, Terms: terms510}
	return _t1035
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol511 := p.consumeTerminal("SYMBOL").Value.str
	return symbol511
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs512 := []*pb.Abstraction{}
	cond513 := p.matchLookaheadLiteral("(", 0)
	for cond513 {
		_t1036 := p.parse_abstraction()
		item514 := _t1036
		xs512 = append(xs512, item514)
		cond513 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions515 := xs512
	p.consumeLiteral(")")
	return abstractions515
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1037 := p.parse_relation_id()
	relation_id516 := _t1037
	xs517 := []*pb.Term{}
	cond518 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond518 {
		_t1038 := p.parse_term()
		item519 := _t1038
		xs517 = append(xs517, item519)
		cond518 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms520 := xs517
	p.consumeLiteral(")")
	_t1039 := &pb.Atom{Name: relation_id516, Terms: terms520}
	return _t1039
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1040 := p.parse_name()
	name521 := _t1040
	xs522 := []*pb.Term{}
	cond523 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond523 {
		_t1041 := p.parse_term()
		item524 := _t1041
		xs522 = append(xs522, item524)
		cond523 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms525 := xs522
	p.consumeLiteral(")")
	_t1042 := &pb.Pragma{Name: name521, Terms: terms525}
	return _t1042
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1043 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1044 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1044 = 9
		} else {
			var _t1045 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1045 = 4
			} else {
				var _t1046 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1046 = 3
				} else {
					var _t1047 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1047 = 0
					} else {
						var _t1048 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1048 = 2
						} else {
							var _t1049 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1049 = 1
							} else {
								var _t1050 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1050 = 8
								} else {
									var _t1051 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1051 = 6
									} else {
										var _t1052 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1052 = 5
										} else {
											var _t1053 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1053 = 7
											} else {
												_t1053 = -1
											}
											_t1052 = _t1053
										}
										_t1051 = _t1052
									}
									_t1050 = _t1051
								}
								_t1049 = _t1050
							}
							_t1048 = _t1049
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
	prediction526 := _t1043
	var _t1054 *pb.Primitive
	if prediction526 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1055 := p.parse_name()
		name536 := _t1055
		xs537 := []*pb.RelTerm{}
		cond538 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond538 {
			_t1056 := p.parse_rel_term()
			item539 := _t1056
			xs537 = append(xs537, item539)
			cond538 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms540 := xs537
		p.consumeLiteral(")")
		_t1057 := &pb.Primitive{Name: name536, Terms: rel_terms540}
		_t1054 = _t1057
	} else {
		var _t1058 *pb.Primitive
		if prediction526 == 8 {
			_t1059 := p.parse_divide()
			divide535 := _t1059
			_t1058 = divide535
		} else {
			var _t1060 *pb.Primitive
			if prediction526 == 7 {
				_t1061 := p.parse_multiply()
				multiply534 := _t1061
				_t1060 = multiply534
			} else {
				var _t1062 *pb.Primitive
				if prediction526 == 6 {
					_t1063 := p.parse_minus()
					minus533 := _t1063
					_t1062 = minus533
				} else {
					var _t1064 *pb.Primitive
					if prediction526 == 5 {
						_t1065 := p.parse_add()
						add532 := _t1065
						_t1064 = add532
					} else {
						var _t1066 *pb.Primitive
						if prediction526 == 4 {
							_t1067 := p.parse_gt_eq()
							gt_eq531 := _t1067
							_t1066 = gt_eq531
						} else {
							var _t1068 *pb.Primitive
							if prediction526 == 3 {
								_t1069 := p.parse_gt()
								gt530 := _t1069
								_t1068 = gt530
							} else {
								var _t1070 *pb.Primitive
								if prediction526 == 2 {
									_t1071 := p.parse_lt_eq()
									lt_eq529 := _t1071
									_t1070 = lt_eq529
								} else {
									var _t1072 *pb.Primitive
									if prediction526 == 1 {
										_t1073 := p.parse_lt()
										lt528 := _t1073
										_t1072 = lt528
									} else {
										var _t1074 *pb.Primitive
										if prediction526 == 0 {
											_t1075 := p.parse_eq()
											eq527 := _t1075
											_t1074 = eq527
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1072 = _t1074
									}
									_t1070 = _t1072
								}
								_t1068 = _t1070
							}
							_t1066 = _t1068
						}
						_t1064 = _t1066
					}
					_t1062 = _t1064
				}
				_t1060 = _t1062
			}
			_t1058 = _t1060
		}
		_t1054 = _t1058
	}
	return _t1054
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1076 := p.parse_term()
	term541 := _t1076
	_t1077 := p.parse_term()
	term_3542 := _t1077
	p.consumeLiteral(")")
	_t1078 := &pb.RelTerm{}
	_t1078.RelTermType = &pb.RelTerm_Term{Term: term541}
	_t1079 := &pb.RelTerm{}
	_t1079.RelTermType = &pb.RelTerm_Term{Term: term_3542}
	_t1080 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1078, _t1079}}
	return _t1080
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1081 := p.parse_term()
	term543 := _t1081
	_t1082 := p.parse_term()
	term_3544 := _t1082
	p.consumeLiteral(")")
	_t1083 := &pb.RelTerm{}
	_t1083.RelTermType = &pb.RelTerm_Term{Term: term543}
	_t1084 := &pb.RelTerm{}
	_t1084.RelTermType = &pb.RelTerm_Term{Term: term_3544}
	_t1085 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1083, _t1084}}
	return _t1085
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1086 := p.parse_term()
	term545 := _t1086
	_t1087 := p.parse_term()
	term_3546 := _t1087
	p.consumeLiteral(")")
	_t1088 := &pb.RelTerm{}
	_t1088.RelTermType = &pb.RelTerm_Term{Term: term545}
	_t1089 := &pb.RelTerm{}
	_t1089.RelTermType = &pb.RelTerm_Term{Term: term_3546}
	_t1090 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1088, _t1089}}
	return _t1090
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1091 := p.parse_term()
	term547 := _t1091
	_t1092 := p.parse_term()
	term_3548 := _t1092
	p.consumeLiteral(")")
	_t1093 := &pb.RelTerm{}
	_t1093.RelTermType = &pb.RelTerm_Term{Term: term547}
	_t1094 := &pb.RelTerm{}
	_t1094.RelTermType = &pb.RelTerm_Term{Term: term_3548}
	_t1095 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1093, _t1094}}
	return _t1095
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1096 := p.parse_term()
	term549 := _t1096
	_t1097 := p.parse_term()
	term_3550 := _t1097
	p.consumeLiteral(")")
	_t1098 := &pb.RelTerm{}
	_t1098.RelTermType = &pb.RelTerm_Term{Term: term549}
	_t1099 := &pb.RelTerm{}
	_t1099.RelTermType = &pb.RelTerm_Term{Term: term_3550}
	_t1100 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1098, _t1099}}
	return _t1100
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1101 := p.parse_term()
	term551 := _t1101
	_t1102 := p.parse_term()
	term_3552 := _t1102
	_t1103 := p.parse_term()
	term_4553 := _t1103
	p.consumeLiteral(")")
	_t1104 := &pb.RelTerm{}
	_t1104.RelTermType = &pb.RelTerm_Term{Term: term551}
	_t1105 := &pb.RelTerm{}
	_t1105.RelTermType = &pb.RelTerm_Term{Term: term_3552}
	_t1106 := &pb.RelTerm{}
	_t1106.RelTermType = &pb.RelTerm_Term{Term: term_4553}
	_t1107 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1104, _t1105, _t1106}}
	return _t1107
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1108 := p.parse_term()
	term554 := _t1108
	_t1109 := p.parse_term()
	term_3555 := _t1109
	_t1110 := p.parse_term()
	term_4556 := _t1110
	p.consumeLiteral(")")
	_t1111 := &pb.RelTerm{}
	_t1111.RelTermType = &pb.RelTerm_Term{Term: term554}
	_t1112 := &pb.RelTerm{}
	_t1112.RelTermType = &pb.RelTerm_Term{Term: term_3555}
	_t1113 := &pb.RelTerm{}
	_t1113.RelTermType = &pb.RelTerm_Term{Term: term_4556}
	_t1114 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1111, _t1112, _t1113}}
	return _t1114
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1115 := p.parse_term()
	term557 := _t1115
	_t1116 := p.parse_term()
	term_3558 := _t1116
	_t1117 := p.parse_term()
	term_4559 := _t1117
	p.consumeLiteral(")")
	_t1118 := &pb.RelTerm{}
	_t1118.RelTermType = &pb.RelTerm_Term{Term: term557}
	_t1119 := &pb.RelTerm{}
	_t1119.RelTermType = &pb.RelTerm_Term{Term: term_3558}
	_t1120 := &pb.RelTerm{}
	_t1120.RelTermType = &pb.RelTerm_Term{Term: term_4559}
	_t1121 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1118, _t1119, _t1120}}
	return _t1121
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1122 := p.parse_term()
	term560 := _t1122
	_t1123 := p.parse_term()
	term_3561 := _t1123
	_t1124 := p.parse_term()
	term_4562 := _t1124
	p.consumeLiteral(")")
	_t1125 := &pb.RelTerm{}
	_t1125.RelTermType = &pb.RelTerm_Term{Term: term560}
	_t1126 := &pb.RelTerm{}
	_t1126.RelTermType = &pb.RelTerm_Term{Term: term_3561}
	_t1127 := &pb.RelTerm{}
	_t1127.RelTermType = &pb.RelTerm_Term{Term: term_4562}
	_t1128 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1125, _t1126, _t1127}}
	return _t1128
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1129 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1129 = 1
	} else {
		var _t1130 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1130 = 1
		} else {
			var _t1131 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1131 = 1
			} else {
				var _t1132 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1132 = 1
				} else {
					var _t1133 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1133 = 0
					} else {
						var _t1134 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1134 = 1
						} else {
							var _t1135 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1135 = 1
							} else {
								var _t1136 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1136 = 1
								} else {
									var _t1137 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1137 = 1
									} else {
										var _t1138 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1138 = 1
										} else {
											var _t1139 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1139 = 1
											} else {
												var _t1140 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1140 = 1
												} else {
													_t1140 = -1
												}
												_t1139 = _t1140
											}
											_t1138 = _t1139
										}
										_t1137 = _t1138
									}
									_t1136 = _t1137
								}
								_t1135 = _t1136
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
		}
		_t1129 = _t1130
	}
	prediction563 := _t1129
	var _t1141 *pb.RelTerm
	if prediction563 == 1 {
		_t1142 := p.parse_term()
		term565 := _t1142
		_t1143 := &pb.RelTerm{}
		_t1143.RelTermType = &pb.RelTerm_Term{Term: term565}
		_t1141 = _t1143
	} else {
		var _t1144 *pb.RelTerm
		if prediction563 == 0 {
			_t1145 := p.parse_specialized_value()
			specialized_value564 := _t1145
			_t1146 := &pb.RelTerm{}
			_t1146.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value564}
			_t1144 = _t1146
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1141 = _t1144
	}
	return _t1141
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1147 := p.parse_value()
	value566 := _t1147
	return value566
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1148 := p.parse_name()
	name567 := _t1148
	xs568 := []*pb.RelTerm{}
	cond569 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond569 {
		_t1149 := p.parse_rel_term()
		item570 := _t1149
		xs568 = append(xs568, item570)
		cond569 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms571 := xs568
	p.consumeLiteral(")")
	_t1150 := &pb.RelAtom{Name: name567, Terms: rel_terms571}
	return _t1150
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1151 := p.parse_term()
	term572 := _t1151
	_t1152 := p.parse_term()
	term_3573 := _t1152
	p.consumeLiteral(")")
	_t1153 := &pb.Cast{Input: term572, Result: term_3573}
	return _t1153
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs574 := []*pb.Attribute{}
	cond575 := p.matchLookaheadLiteral("(", 0)
	for cond575 {
		_t1154 := p.parse_attribute()
		item576 := _t1154
		xs574 = append(xs574, item576)
		cond575 = p.matchLookaheadLiteral("(", 0)
	}
	attributes577 := xs574
	p.consumeLiteral(")")
	return attributes577
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1155 := p.parse_name()
	name578 := _t1155
	xs579 := []*pb.Value{}
	cond580 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond580 {
		_t1156 := p.parse_value()
		item581 := _t1156
		xs579 = append(xs579, item581)
		cond580 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values582 := xs579
	p.consumeLiteral(")")
	_t1157 := &pb.Attribute{Name: name578, Args: values582}
	return _t1157
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs583 := []*pb.RelationId{}
	cond584 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond584 {
		_t1158 := p.parse_relation_id()
		item585 := _t1158
		xs583 = append(xs583, item585)
		cond584 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids586 := xs583
	_t1159 := p.parse_script()
	script587 := _t1159
	p.consumeLiteral(")")
	_t1160 := &pb.Algorithm{Global: relation_ids586, Body: script587}
	return _t1160
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs588 := []*pb.Construct{}
	cond589 := p.matchLookaheadLiteral("(", 0)
	for cond589 {
		_t1161 := p.parse_construct()
		item590 := _t1161
		xs588 = append(xs588, item590)
		cond589 = p.matchLookaheadLiteral("(", 0)
	}
	constructs591 := xs588
	p.consumeLiteral(")")
	_t1162 := &pb.Script{Constructs: constructs591}
	return _t1162
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1163 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1164 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1164 = 1
		} else {
			var _t1165 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1165 = 1
			} else {
				var _t1166 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1166 = 1
				} else {
					var _t1167 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1167 = 0
					} else {
						var _t1168 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1168 = 1
						} else {
							var _t1169 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1169 = 1
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
		}
		_t1163 = _t1164
	} else {
		_t1163 = -1
	}
	prediction592 := _t1163
	var _t1170 *pb.Construct
	if prediction592 == 1 {
		_t1171 := p.parse_instruction()
		instruction594 := _t1171
		_t1172 := &pb.Construct{}
		_t1172.ConstructType = &pb.Construct_Instruction{Instruction: instruction594}
		_t1170 = _t1172
	} else {
		var _t1173 *pb.Construct
		if prediction592 == 0 {
			_t1174 := p.parse_loop()
			loop593 := _t1174
			_t1175 := &pb.Construct{}
			_t1175.ConstructType = &pb.Construct_Loop{Loop: loop593}
			_t1173 = _t1175
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1170 = _t1173
	}
	return _t1170
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1176 := p.parse_init()
	init595 := _t1176
	_t1177 := p.parse_script()
	script596 := _t1177
	p.consumeLiteral(")")
	_t1178 := &pb.Loop{Init: init595, Body: script596}
	return _t1178
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs597 := []*pb.Instruction{}
	cond598 := p.matchLookaheadLiteral("(", 0)
	for cond598 {
		_t1179 := p.parse_instruction()
		item599 := _t1179
		xs597 = append(xs597, item599)
		cond598 = p.matchLookaheadLiteral("(", 0)
	}
	instructions600 := xs597
	p.consumeLiteral(")")
	return instructions600
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1180 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1181 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1181 = 1
		} else {
			var _t1182 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1182 = 4
			} else {
				var _t1183 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1183 = 3
				} else {
					var _t1184 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1184 = 2
					} else {
						var _t1185 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1185 = 0
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
	prediction601 := _t1180
	var _t1186 *pb.Instruction
	if prediction601 == 4 {
		_t1187 := p.parse_monus_def()
		monus_def606 := _t1187
		_t1188 := &pb.Instruction{}
		_t1188.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def606}
		_t1186 = _t1188
	} else {
		var _t1189 *pb.Instruction
		if prediction601 == 3 {
			_t1190 := p.parse_monoid_def()
			monoid_def605 := _t1190
			_t1191 := &pb.Instruction{}
			_t1191.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def605}
			_t1189 = _t1191
		} else {
			var _t1192 *pb.Instruction
			if prediction601 == 2 {
				_t1193 := p.parse_break()
				break604 := _t1193
				_t1194 := &pb.Instruction{}
				_t1194.InstrType = &pb.Instruction_Break{Break: break604}
				_t1192 = _t1194
			} else {
				var _t1195 *pb.Instruction
				if prediction601 == 1 {
					_t1196 := p.parse_upsert()
					upsert603 := _t1196
					_t1197 := &pb.Instruction{}
					_t1197.InstrType = &pb.Instruction_Upsert{Upsert: upsert603}
					_t1195 = _t1197
				} else {
					var _t1198 *pb.Instruction
					if prediction601 == 0 {
						_t1199 := p.parse_assign()
						assign602 := _t1199
						_t1200 := &pb.Instruction{}
						_t1200.InstrType = &pb.Instruction_Assign{Assign: assign602}
						_t1198 = _t1200
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1195 = _t1198
				}
				_t1192 = _t1195
			}
			_t1189 = _t1192
		}
		_t1186 = _t1189
	}
	return _t1186
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1201 := p.parse_relation_id()
	relation_id607 := _t1201
	_t1202 := p.parse_abstraction()
	abstraction608 := _t1202
	var _t1203 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1204 := p.parse_attrs()
		_t1203 = _t1204
	}
	attrs609 := _t1203
	p.consumeLiteral(")")
	_t1205 := attrs609
	if attrs609 == nil {
		_t1205 = []*pb.Attribute{}
	}
	_t1206 := &pb.Assign{Name: relation_id607, Body: abstraction608, Attrs: _t1205}
	return _t1206
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1207 := p.parse_relation_id()
	relation_id610 := _t1207
	_t1208 := p.parse_abstraction_with_arity()
	abstraction_with_arity611 := _t1208
	var _t1209 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1210 := p.parse_attrs()
		_t1209 = _t1210
	}
	attrs612 := _t1209
	p.consumeLiteral(")")
	_t1211 := attrs612
	if attrs612 == nil {
		_t1211 = []*pb.Attribute{}
	}
	_t1212 := &pb.Upsert{Name: relation_id610, Body: abstraction_with_arity611[0].(*pb.Abstraction), Attrs: _t1211, ValueArity: abstraction_with_arity611[1].(int64)}
	return _t1212
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1213 := p.parse_bindings()
	bindings613 := _t1213
	_t1214 := p.parse_formula()
	formula614 := _t1214
	p.consumeLiteral(")")
	_t1215 := &pb.Abstraction{Vars: listConcat(bindings613[0].([]*pb.Binding), bindings613[1].([]*pb.Binding)), Value: formula614}
	return []interface{}{_t1215, int64(len(bindings613[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1216 := p.parse_relation_id()
	relation_id615 := _t1216
	_t1217 := p.parse_abstraction()
	abstraction616 := _t1217
	var _t1218 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1219 := p.parse_attrs()
		_t1218 = _t1219
	}
	attrs617 := _t1218
	p.consumeLiteral(")")
	_t1220 := attrs617
	if attrs617 == nil {
		_t1220 = []*pb.Attribute{}
	}
	_t1221 := &pb.Break{Name: relation_id615, Body: abstraction616, Attrs: _t1220}
	return _t1221
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1222 := p.parse_monoid()
	monoid618 := _t1222
	_t1223 := p.parse_relation_id()
	relation_id619 := _t1223
	_t1224 := p.parse_abstraction_with_arity()
	abstraction_with_arity620 := _t1224
	var _t1225 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1226 := p.parse_attrs()
		_t1225 = _t1226
	}
	attrs621 := _t1225
	p.consumeLiteral(")")
	_t1227 := attrs621
	if attrs621 == nil {
		_t1227 = []*pb.Attribute{}
	}
	_t1228 := &pb.MonoidDef{Monoid: monoid618, Name: relation_id619, Body: abstraction_with_arity620[0].(*pb.Abstraction), Attrs: _t1227, ValueArity: abstraction_with_arity620[1].(int64)}
	return _t1228
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1229 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1230 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1230 = 3
		} else {
			var _t1231 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1231 = 0
			} else {
				var _t1232 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1232 = 1
				} else {
					var _t1233 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1233 = 2
					} else {
						_t1233 = -1
					}
					_t1232 = _t1233
				}
				_t1231 = _t1232
			}
			_t1230 = _t1231
		}
		_t1229 = _t1230
	} else {
		_t1229 = -1
	}
	prediction622 := _t1229
	var _t1234 *pb.Monoid
	if prediction622 == 3 {
		_t1235 := p.parse_sum_monoid()
		sum_monoid626 := _t1235
		_t1236 := &pb.Monoid{}
		_t1236.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid626}
		_t1234 = _t1236
	} else {
		var _t1237 *pb.Monoid
		if prediction622 == 2 {
			_t1238 := p.parse_max_monoid()
			max_monoid625 := _t1238
			_t1239 := &pb.Monoid{}
			_t1239.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid625}
			_t1237 = _t1239
		} else {
			var _t1240 *pb.Monoid
			if prediction622 == 1 {
				_t1241 := p.parse_min_monoid()
				min_monoid624 := _t1241
				_t1242 := &pb.Monoid{}
				_t1242.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid624}
				_t1240 = _t1242
			} else {
				var _t1243 *pb.Monoid
				if prediction622 == 0 {
					_t1244 := p.parse_or_monoid()
					or_monoid623 := _t1244
					_t1245 := &pb.Monoid{}
					_t1245.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid623}
					_t1243 = _t1245
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1240 = _t1243
			}
			_t1237 = _t1240
		}
		_t1234 = _t1237
	}
	return _t1234
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1246 := &pb.OrMonoid{}
	return _t1246
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1247 := p.parse_type()
	type627 := _t1247
	p.consumeLiteral(")")
	_t1248 := &pb.MinMonoid{Type: type627}
	return _t1248
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1249 := p.parse_type()
	type628 := _t1249
	p.consumeLiteral(")")
	_t1250 := &pb.MaxMonoid{Type: type628}
	return _t1250
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1251 := p.parse_type()
	type629 := _t1251
	p.consumeLiteral(")")
	_t1252 := &pb.SumMonoid{Type: type629}
	return _t1252
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1253 := p.parse_monoid()
	monoid630 := _t1253
	_t1254 := p.parse_relation_id()
	relation_id631 := _t1254
	_t1255 := p.parse_abstraction_with_arity()
	abstraction_with_arity632 := _t1255
	var _t1256 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1257 := p.parse_attrs()
		_t1256 = _t1257
	}
	attrs633 := _t1256
	p.consumeLiteral(")")
	_t1258 := attrs633
	if attrs633 == nil {
		_t1258 = []*pb.Attribute{}
	}
	_t1259 := &pb.MonusDef{Monoid: monoid630, Name: relation_id631, Body: abstraction_with_arity632[0].(*pb.Abstraction), Attrs: _t1258, ValueArity: abstraction_with_arity632[1].(int64)}
	return _t1259
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1260 := p.parse_relation_id()
	relation_id634 := _t1260
	_t1261 := p.parse_abstraction()
	abstraction635 := _t1261
	_t1262 := p.parse_functional_dependency_keys()
	functional_dependency_keys636 := _t1262
	_t1263 := p.parse_functional_dependency_values()
	functional_dependency_values637 := _t1263
	p.consumeLiteral(")")
	_t1264 := &pb.FunctionalDependency{Guard: abstraction635, Keys: functional_dependency_keys636, Values: functional_dependency_values637}
	_t1265 := &pb.Constraint{Name: relation_id634}
	_t1265.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1264}
	return _t1265
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs638 := []*pb.Var{}
	cond639 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond639 {
		_t1266 := p.parse_var()
		item640 := _t1266
		xs638 = append(xs638, item640)
		cond639 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars641 := xs638
	p.consumeLiteral(")")
	return vars641
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs642 := []*pb.Var{}
	cond643 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond643 {
		_t1267 := p.parse_var()
		item644 := _t1267
		xs642 = append(xs642, item644)
		cond643 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars645 := xs642
	p.consumeLiteral(")")
	return vars645
}

func (p *Parser) parse_data() *pb.Data {
	var _t1268 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1269 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1269 = 0
		} else {
			var _t1270 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1270 = 2
			} else {
				var _t1271 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1271 = 1
				} else {
					_t1271 = -1
				}
				_t1270 = _t1271
			}
			_t1269 = _t1270
		}
		_t1268 = _t1269
	} else {
		_t1268 = -1
	}
	prediction646 := _t1268
	var _t1272 *pb.Data
	if prediction646 == 2 {
		_t1273 := p.parse_csv_data()
		csv_data649 := _t1273
		_t1274 := &pb.Data{}
		_t1274.DataType = &pb.Data_CsvData{CsvData: csv_data649}
		_t1272 = _t1274
	} else {
		var _t1275 *pb.Data
		if prediction646 == 1 {
			_t1276 := p.parse_betree_relation()
			betree_relation648 := _t1276
			_t1277 := &pb.Data{}
			_t1277.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation648}
			_t1275 = _t1277
		} else {
			var _t1278 *pb.Data
			if prediction646 == 0 {
				_t1279 := p.parse_edb()
				edb647 := _t1279
				_t1280 := &pb.Data{}
				_t1280.DataType = &pb.Data_Edb{Edb: edb647}
				_t1278 = _t1280
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1275 = _t1278
		}
		_t1272 = _t1275
	}
	return _t1272
}

func (p *Parser) parse_edb() *pb.EDB {
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1281 := p.parse_relation_id()
	relation_id650 := _t1281
	_t1282 := p.parse_edb_path()
	edb_path651 := _t1282
	_t1283 := p.parse_edb_types()
	edb_types652 := _t1283
	p.consumeLiteral(")")
	_t1284 := &pb.EDB{TargetId: relation_id650, Path: edb_path651, Types: edb_types652}
	return _t1284
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs653 := []string{}
	cond654 := p.matchLookaheadTerminal("STRING", 0)
	for cond654 {
		item655 := p.consumeTerminal("STRING").Value.str
		xs653 = append(xs653, item655)
		cond654 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings656 := xs653
	p.consumeLiteral("]")
	return strings656
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs657 := []*pb.Type{}
	cond658 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond658 {
		_t1285 := p.parse_type()
		item659 := _t1285
		xs657 = append(xs657, item659)
		cond658 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types660 := xs657
	p.consumeLiteral("]")
	return types660
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1286 := p.parse_relation_id()
	relation_id661 := _t1286
	_t1287 := p.parse_betree_info()
	betree_info662 := _t1287
	p.consumeLiteral(")")
	_t1288 := &pb.BeTreeRelation{Name: relation_id661, RelationInfo: betree_info662}
	return _t1288
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1289 := p.parse_betree_info_key_types()
	betree_info_key_types663 := _t1289
	_t1290 := p.parse_betree_info_value_types()
	betree_info_value_types664 := _t1290
	_t1291 := p.parse_config_dict()
	config_dict665 := _t1291
	p.consumeLiteral(")")
	_t1292 := p.construct_betree_info(betree_info_key_types663, betree_info_value_types664, config_dict665)
	return _t1292
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs666 := []*pb.Type{}
	cond667 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond667 {
		_t1293 := p.parse_type()
		item668 := _t1293
		xs666 = append(xs666, item668)
		cond667 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types669 := xs666
	p.consumeLiteral(")")
	return types669
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs670 := []*pb.Type{}
	cond671 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond671 {
		_t1294 := p.parse_type()
		item672 := _t1294
		xs670 = append(xs670, item672)
		cond671 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types673 := xs670
	p.consumeLiteral(")")
	return types673
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1295 := p.parse_csvlocator()
	csvlocator674 := _t1295
	_t1296 := p.parse_csv_config()
	csv_config675 := _t1296
	_t1297 := p.parse_gnf_columns()
	gnf_columns676 := _t1297
	_t1298 := p.parse_csv_asof()
	csv_asof677 := _t1298
	p.consumeLiteral(")")
	_t1299 := &pb.CSVData{Locator: csvlocator674, Config: csv_config675, Columns: gnf_columns676, Asof: csv_asof677}
	return _t1299
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1300 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1301 := p.parse_csv_locator_paths()
		_t1300 = _t1301
	}
	csv_locator_paths678 := _t1300
	var _t1302 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1303 := p.parse_csv_locator_inline_data()
		_t1302 = ptr(_t1303)
	}
	csv_locator_inline_data679 := _t1302
	p.consumeLiteral(")")
	_t1304 := csv_locator_paths678
	if csv_locator_paths678 == nil {
		_t1304 = []string{}
	}
	_t1305 := &pb.CSVLocator{Paths: _t1304, InlineData: []byte(deref(csv_locator_inline_data679, ""))}
	return _t1305
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs680 := []string{}
	cond681 := p.matchLookaheadTerminal("STRING", 0)
	for cond681 {
		item682 := p.consumeTerminal("STRING").Value.str
		xs680 = append(xs680, item682)
		cond681 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings683 := xs680
	p.consumeLiteral(")")
	return strings683
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string684 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string684
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1306 := p.parse_config_dict()
	config_dict685 := _t1306
	p.consumeLiteral(")")
	_t1307 := p.construct_csv_config(config_dict685)
	return _t1307
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs686 := []*pb.GNFColumn{}
	cond687 := p.matchLookaheadLiteral("(", 0)
	for cond687 {
		_t1308 := p.parse_gnf_column()
		item688 := _t1308
		xs686 = append(xs686, item688)
		cond687 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns689 := xs686
	p.consumeLiteral(")")
	return gnf_columns689
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1309 := p.parse_gnf_column_path()
	gnf_column_path690 := _t1309
	var _t1310 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1311 := p.parse_relation_id()
		_t1310 = _t1311
	}
	relation_id691 := _t1310
	p.consumeLiteral("[")
	xs692 := []*pb.Type{}
	cond693 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond693 {
		_t1312 := p.parse_type()
		item694 := _t1312
		xs692 = append(xs692, item694)
		cond693 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types695 := xs692
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1313 := &pb.GNFColumn{ColumnPath: gnf_column_path690, TargetId: relation_id691, Types: types695}
	return _t1313
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1314 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1314 = 1
	} else {
		var _t1315 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1315 = 0
		} else {
			_t1315 = -1
		}
		_t1314 = _t1315
	}
	prediction696 := _t1314
	var _t1316 []string
	if prediction696 == 1 {
		p.consumeLiteral("[")
		xs698 := []string{}
		cond699 := p.matchLookaheadTerminal("STRING", 0)
		for cond699 {
			item700 := p.consumeTerminal("STRING").Value.str
			xs698 = append(xs698, item700)
			cond699 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings701 := xs698
		p.consumeLiteral("]")
		_t1316 = strings701
	} else {
		var _t1317 []string
		if prediction696 == 0 {
			string697 := p.consumeTerminal("STRING").Value.str
			_ = string697
			_t1317 = []string{string697}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1316 = _t1317
	}
	return _t1316
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string702 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string702
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1318 := p.parse_fragment_id()
	fragment_id703 := _t1318
	p.consumeLiteral(")")
	_t1319 := &pb.Undefine{FragmentId: fragment_id703}
	return _t1319
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs704 := []*pb.RelationId{}
	cond705 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond705 {
		_t1320 := p.parse_relation_id()
		item706 := _t1320
		xs704 = append(xs704, item706)
		cond705 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids707 := xs704
	p.consumeLiteral(")")
	_t1321 := &pb.Context{Relations: relation_ids707}
	return _t1321
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs708 := []*pb.SnapshotMapping{}
	cond709 := p.matchLookaheadLiteral("[", 0)
	for cond709 {
		_t1322 := p.parse_snapshot_mapping()
		item710 := _t1322
		xs708 = append(xs708, item710)
		cond709 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings711 := xs708
	p.consumeLiteral(")")
	_t1323 := &pb.Snapshot{Mappings: snapshot_mappings711}
	return _t1323
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	_t1324 := p.parse_edb_path()
	edb_path712 := _t1324
	_t1325 := p.parse_relation_id()
	relation_id713 := _t1325
	_t1326 := &pb.SnapshotMapping{DestinationPath: edb_path712, SourceRelation: relation_id713}
	return _t1326
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs714 := []*pb.Read{}
	cond715 := p.matchLookaheadLiteral("(", 0)
	for cond715 {
		_t1327 := p.parse_read()
		item716 := _t1327
		xs714 = append(xs714, item716)
		cond715 = p.matchLookaheadLiteral("(", 0)
	}
	reads717 := xs714
	p.consumeLiteral(")")
	return reads717
}

func (p *Parser) parse_read() *pb.Read {
	var _t1328 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1329 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1329 = 2
		} else {
			var _t1330 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1330 = 1
			} else {
				var _t1331 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1331 = 4
				} else {
					var _t1332 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1332 = 0
					} else {
						var _t1333 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1333 = 3
						} else {
							_t1333 = -1
						}
						_t1332 = _t1333
					}
					_t1331 = _t1332
				}
				_t1330 = _t1331
			}
			_t1329 = _t1330
		}
		_t1328 = _t1329
	} else {
		_t1328 = -1
	}
	prediction718 := _t1328
	var _t1334 *pb.Read
	if prediction718 == 4 {
		_t1335 := p.parse_export()
		export723 := _t1335
		_t1336 := &pb.Read{}
		_t1336.ReadType = &pb.Read_Export{Export: export723}
		_t1334 = _t1336
	} else {
		var _t1337 *pb.Read
		if prediction718 == 3 {
			_t1338 := p.parse_abort()
			abort722 := _t1338
			_t1339 := &pb.Read{}
			_t1339.ReadType = &pb.Read_Abort{Abort: abort722}
			_t1337 = _t1339
		} else {
			var _t1340 *pb.Read
			if prediction718 == 2 {
				_t1341 := p.parse_what_if()
				what_if721 := _t1341
				_t1342 := &pb.Read{}
				_t1342.ReadType = &pb.Read_WhatIf{WhatIf: what_if721}
				_t1340 = _t1342
			} else {
				var _t1343 *pb.Read
				if prediction718 == 1 {
					_t1344 := p.parse_output()
					output720 := _t1344
					_t1345 := &pb.Read{}
					_t1345.ReadType = &pb.Read_Output{Output: output720}
					_t1343 = _t1345
				} else {
					var _t1346 *pb.Read
					if prediction718 == 0 {
						_t1347 := p.parse_demand()
						demand719 := _t1347
						_t1348 := &pb.Read{}
						_t1348.ReadType = &pb.Read_Demand{Demand: demand719}
						_t1346 = _t1348
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1343 = _t1346
				}
				_t1340 = _t1343
			}
			_t1337 = _t1340
		}
		_t1334 = _t1337
	}
	return _t1334
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1349 := p.parse_relation_id()
	relation_id724 := _t1349
	p.consumeLiteral(")")
	_t1350 := &pb.Demand{RelationId: relation_id724}
	return _t1350
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1351 := p.parse_name()
	name725 := _t1351
	_t1352 := p.parse_relation_id()
	relation_id726 := _t1352
	p.consumeLiteral(")")
	_t1353 := &pb.Output{Name: name725, RelationId: relation_id726}
	return _t1353
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1354 := p.parse_name()
	name727 := _t1354
	_t1355 := p.parse_epoch()
	epoch728 := _t1355
	p.consumeLiteral(")")
	_t1356 := &pb.WhatIf{Branch: name727, Epoch: epoch728}
	return _t1356
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1357 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1358 := p.parse_name()
		_t1357 = ptr(_t1358)
	}
	name729 := _t1357
	_t1359 := p.parse_relation_id()
	relation_id730 := _t1359
	p.consumeLiteral(")")
	_t1360 := &pb.Abort{Name: deref(name729, "abort"), RelationId: relation_id730}
	return _t1360
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1361 := p.parse_export_csv_config()
	export_csv_config731 := _t1361
	p.consumeLiteral(")")
	_t1362 := &pb.Export{}
	_t1362.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config731}
	return _t1362
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	var _t1363 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1364 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1364 = 0
		} else {
			var _t1365 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1365 = 1
			} else {
				_t1365 = -1
			}
			_t1364 = _t1365
		}
		_t1363 = _t1364
	} else {
		_t1363 = -1
	}
	prediction732 := _t1363
	var _t1366 *pb.ExportCSVConfig
	if prediction732 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1367 := p.parse_export_csv_path()
		export_csv_path736 := _t1367
		_t1368 := p.parse_export_csv_columns_list()
		export_csv_columns_list737 := _t1368
		_t1369 := p.parse_config_dict()
		config_dict738 := _t1369
		p.consumeLiteral(")")
		_t1370 := p.construct_export_csv_config(export_csv_path736, export_csv_columns_list737, config_dict738)
		_t1366 = _t1370
	} else {
		var _t1371 *pb.ExportCSVConfig
		if prediction732 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1372 := p.parse_export_csv_path()
			export_csv_path733 := _t1372
			_t1373 := p.parse_export_csv_source()
			export_csv_source734 := _t1373
			_t1374 := p.parse_csv_config()
			csv_config735 := _t1374
			p.consumeLiteral(")")
			_t1375 := p.construct_export_csv_config_with_source(export_csv_path733, export_csv_source734, csv_config735)
			_t1371 = _t1375
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1366 = _t1371
	}
	return _t1366
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string739 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string739
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	var _t1376 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1377 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1377 = 1
		} else {
			var _t1378 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1378 = 0
			} else {
				_t1378 = -1
			}
			_t1377 = _t1378
		}
		_t1376 = _t1377
	} else {
		_t1376 = -1
	}
	prediction740 := _t1376
	var _t1379 *pb.ExportCSVSource
	if prediction740 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1380 := p.parse_relation_id()
		relation_id745 := _t1380
		p.consumeLiteral(")")
		_t1381 := &pb.ExportCSVSource{}
		_t1381.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id745}
		_t1379 = _t1381
	} else {
		var _t1382 *pb.ExportCSVSource
		if prediction740 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs741 := []*pb.ExportCSVColumn{}
			cond742 := p.matchLookaheadLiteral("(", 0)
			for cond742 {
				_t1383 := p.parse_export_csv_column()
				item743 := _t1383
				xs741 = append(xs741, item743)
				cond742 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns744 := xs741
			p.consumeLiteral(")")
			_t1384 := &pb.ExportCSVColumns{Columns: export_csv_columns744}
			_t1385 := &pb.ExportCSVSource{}
			_t1385.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1384}
			_t1382 = _t1385
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1379 = _t1382
	}
	return _t1379
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string746 := p.consumeTerminal("STRING").Value.str
	_t1386 := p.parse_relation_id()
	relation_id747 := _t1386
	p.consumeLiteral(")")
	_t1387 := &pb.ExportCSVColumn{ColumnName: string746, ColumnData: relation_id747}
	return _t1387
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs748 := []*pb.ExportCSVColumn{}
	cond749 := p.matchLookaheadLiteral("(", 0)
	for cond749 {
		_t1388 := p.parse_export_csv_column()
		item750 := _t1388
		xs748 = append(xs748, item750)
		cond749 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns751 := xs748
	p.consumeLiteral(")")
	return export_csv_columns751
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
