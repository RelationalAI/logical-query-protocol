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
	var _t1361 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1361
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1362 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1362
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1363 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1363
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1364 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1364
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1365 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1365
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1366 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1366
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1367 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1367
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1368 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1368
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1369 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1369
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1370 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1370
	_t1371 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1371
	_t1372 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1372
	_t1373 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1373
	_t1374 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1374
	_t1375 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1375
	_t1376 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1376
	_t1377 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1377
	_t1378 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1378
	_t1379 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1379
	_t1380 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1380
	_t1381 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1381
	_t1382 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1382
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1383 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1383
	_t1384 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1384
	_t1385 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1385
	_t1386 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1386
	_t1387 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1387
	_t1388 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1388
	_t1389 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1389
	_t1390 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1390
	_t1391 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1391
	_t1392 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1392.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1392.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1392
	_t1393 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1393
}

func (p *Parser) default_configure() *pb.Configure {
	_t1394 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1394
	_t1395 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1395
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
	_t1396 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1396
	_t1397 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1397
	_t1398 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1398
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1399 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1399
	_t1400 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1400
	_t1401 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1401
	_t1402 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1402
	_t1403 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1403
	_t1404 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1404
	_t1405 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1405
	_t1406 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1406
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1407 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1407
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t732 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t733 := p.parse_configure()
		_t732 = _t733
	}
	configure366 := _t732
	var _t734 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t735 := p.parse_sync()
		_t734 = _t735
	}
	sync367 := _t734
	xs368 := []*pb.Epoch{}
	cond369 := p.matchLookaheadLiteral("(", 0)
	for cond369 {
		_t736 := p.parse_epoch()
		item370 := _t736
		xs368 = append(xs368, item370)
		cond369 = p.matchLookaheadLiteral("(", 0)
	}
	epochs371 := xs368
	p.consumeLiteral(")")
	_t737 := p.default_configure()
	_t738 := configure366
	if configure366 == nil {
		_t738 = _t737
	}
	_t739 := &pb.Transaction{Epochs: epochs371, Configure: _t738, Sync: sync367}
	return _t739
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t740 := p.parse_config_dict()
	config_dict372 := _t740
	p.consumeLiteral(")")
	_t741 := p.construct_configure(config_dict372)
	return _t741
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs373 := [][]interface{}{}
	cond374 := p.matchLookaheadLiteral(":", 0)
	for cond374 {
		_t742 := p.parse_config_key_value()
		item375 := _t742
		xs373 = append(xs373, item375)
		cond374 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values376 := xs373
	p.consumeLiteral("}")
	return config_key_values376
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol377 := p.consumeTerminal("SYMBOL").Value.str
	_t743 := p.parse_value()
	value378 := _t743
	return []interface{}{symbol377, value378}
}

func (p *Parser) parse_value() *pb.Value {
	var _t744 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t744 = 9
	} else {
		var _t745 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t745 = 8
		} else {
			var _t746 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t746 = 9
			} else {
				var _t747 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t748 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t748 = 1
					} else {
						var _t749 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t749 = 0
						} else {
							_t749 = -1
						}
						_t748 = _t749
					}
					_t747 = _t748
				} else {
					var _t750 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t750 = 5
					} else {
						var _t751 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t751 = 2
						} else {
							var _t752 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t752 = 6
							} else {
								var _t753 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t753 = 3
								} else {
									var _t754 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t754 = 4
									} else {
										var _t755 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t755 = 7
										} else {
											_t755 = -1
										}
										_t754 = _t755
									}
									_t753 = _t754
								}
								_t752 = _t753
							}
							_t751 = _t752
						}
						_t750 = _t751
					}
					_t747 = _t750
				}
				_t746 = _t747
			}
			_t745 = _t746
		}
		_t744 = _t745
	}
	prediction379 := _t744
	var _t756 *pb.Value
	if prediction379 == 9 {
		_t757 := p.parse_boolean_value()
		boolean_value388 := _t757
		_t758 := &pb.Value{}
		_t758.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value388}
		_t756 = _t758
	} else {
		var _t759 *pb.Value
		if prediction379 == 8 {
			p.consumeLiteral("missing")
			_t760 := &pb.MissingValue{}
			_t761 := &pb.Value{}
			_t761.Value = &pb.Value_MissingValue{MissingValue: _t760}
			_t759 = _t761
		} else {
			var _t762 *pb.Value
			if prediction379 == 7 {
				decimal387 := p.consumeTerminal("DECIMAL").Value.decimal
				_t763 := &pb.Value{}
				_t763.Value = &pb.Value_DecimalValue{DecimalValue: decimal387}
				_t762 = _t763
			} else {
				var _t764 *pb.Value
				if prediction379 == 6 {
					int128386 := p.consumeTerminal("INT128").Value.int128
					_t765 := &pb.Value{}
					_t765.Value = &pb.Value_Int128Value{Int128Value: int128386}
					_t764 = _t765
				} else {
					var _t766 *pb.Value
					if prediction379 == 5 {
						uint128385 := p.consumeTerminal("UINT128").Value.uint128
						_t767 := &pb.Value{}
						_t767.Value = &pb.Value_Uint128Value{Uint128Value: uint128385}
						_t766 = _t767
					} else {
						var _t768 *pb.Value
						if prediction379 == 4 {
							float384 := p.consumeTerminal("FLOAT").Value.f64
							_t769 := &pb.Value{}
							_t769.Value = &pb.Value_FloatValue{FloatValue: float384}
							_t768 = _t769
						} else {
							var _t770 *pb.Value
							if prediction379 == 3 {
								int383 := p.consumeTerminal("INT").Value.i64
								_t771 := &pb.Value{}
								_t771.Value = &pb.Value_IntValue{IntValue: int383}
								_t770 = _t771
							} else {
								var _t772 *pb.Value
								if prediction379 == 2 {
									string382 := p.consumeTerminal("STRING").Value.str
									_t773 := &pb.Value{}
									_t773.Value = &pb.Value_StringValue{StringValue: string382}
									_t772 = _t773
								} else {
									var _t774 *pb.Value
									if prediction379 == 1 {
										_t775 := p.parse_datetime()
										datetime381 := _t775
										_t776 := &pb.Value{}
										_t776.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime381}
										_t774 = _t776
									} else {
										var _t777 *pb.Value
										if prediction379 == 0 {
											_t778 := p.parse_date()
											date380 := _t778
											_t779 := &pb.Value{}
											_t779.Value = &pb.Value_DateValue{DateValue: date380}
											_t777 = _t779
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t774 = _t777
									}
									_t772 = _t774
								}
								_t770 = _t772
							}
							_t768 = _t770
						}
						_t766 = _t768
					}
					_t764 = _t766
				}
				_t762 = _t764
			}
			_t759 = _t762
		}
		_t756 = _t759
	}
	return _t756
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int389 := p.consumeTerminal("INT").Value.i64
	int_3390 := p.consumeTerminal("INT").Value.i64
	int_4391 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t780 := &pb.DateValue{Year: int32(int389), Month: int32(int_3390), Day: int32(int_4391)}
	return _t780
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int392 := p.consumeTerminal("INT").Value.i64
	int_3393 := p.consumeTerminal("INT").Value.i64
	int_4394 := p.consumeTerminal("INT").Value.i64
	int_5395 := p.consumeTerminal("INT").Value.i64
	int_6396 := p.consumeTerminal("INT").Value.i64
	int_7397 := p.consumeTerminal("INT").Value.i64
	var _t781 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t781 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8398 := _t781
	p.consumeLiteral(")")
	_t782 := &pb.DateTimeValue{Year: int32(int392), Month: int32(int_3393), Day: int32(int_4394), Hour: int32(int_5395), Minute: int32(int_6396), Second: int32(int_7397), Microsecond: int32(deref(int_8398, 0))}
	return _t782
}

func (p *Parser) parse_boolean_value() bool {
	var _t783 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t783 = 0
	} else {
		var _t784 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t784 = 1
		} else {
			_t784 = -1
		}
		_t783 = _t784
	}
	prediction399 := _t783
	var _t785 bool
	if prediction399 == 1 {
		p.consumeLiteral("false")
		_t785 = false
	} else {
		var _t786 bool
		if prediction399 == 0 {
			p.consumeLiteral("true")
			_t786 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t785 = _t786
	}
	return _t785
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs400 := []*pb.FragmentId{}
	cond401 := p.matchLookaheadLiteral(":", 0)
	for cond401 {
		_t787 := p.parse_fragment_id()
		item402 := _t787
		xs400 = append(xs400, item402)
		cond401 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids403 := xs400
	p.consumeLiteral(")")
	_t788 := &pb.Sync{Fragments: fragment_ids403}
	return _t788
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol404 := p.consumeTerminal("SYMBOL").Value.str
	return &pb.FragmentId{Id: []byte(symbol404)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t789 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t790 := p.parse_epoch_writes()
		_t789 = _t790
	}
	epoch_writes405 := _t789
	var _t791 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t792 := p.parse_epoch_reads()
		_t791 = _t792
	}
	epoch_reads406 := _t791
	p.consumeLiteral(")")
	_t793 := epoch_writes405
	if epoch_writes405 == nil {
		_t793 = []*pb.Write{}
	}
	_t794 := epoch_reads406
	if epoch_reads406 == nil {
		_t794 = []*pb.Read{}
	}
	_t795 := &pb.Epoch{Writes: _t793, Reads: _t794}
	return _t795
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs407 := []*pb.Write{}
	cond408 := p.matchLookaheadLiteral("(", 0)
	for cond408 {
		_t796 := p.parse_write()
		item409 := _t796
		xs407 = append(xs407, item409)
		cond408 = p.matchLookaheadLiteral("(", 0)
	}
	writes410 := xs407
	p.consumeLiteral(")")
	return writes410
}

func (p *Parser) parse_write() *pb.Write {
	var _t797 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t798 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t798 = 1
		} else {
			var _t799 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t799 = 3
			} else {
				var _t800 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t800 = 0
				} else {
					var _t801 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t801 = 2
					} else {
						_t801 = -1
					}
					_t800 = _t801
				}
				_t799 = _t800
			}
			_t798 = _t799
		}
		_t797 = _t798
	} else {
		_t797 = -1
	}
	prediction411 := _t797
	var _t802 *pb.Write
	if prediction411 == 3 {
		_t803 := p.parse_snapshot()
		snapshot415 := _t803
		_t804 := &pb.Write{}
		_t804.WriteType = &pb.Write_Snapshot{Snapshot: snapshot415}
		_t802 = _t804
	} else {
		var _t805 *pb.Write
		if prediction411 == 2 {
			_t806 := p.parse_context()
			context414 := _t806
			_t807 := &pb.Write{}
			_t807.WriteType = &pb.Write_Context{Context: context414}
			_t805 = _t807
		} else {
			var _t808 *pb.Write
			if prediction411 == 1 {
				_t809 := p.parse_undefine()
				undefine413 := _t809
				_t810 := &pb.Write{}
				_t810.WriteType = &pb.Write_Undefine{Undefine: undefine413}
				_t808 = _t810
			} else {
				var _t811 *pb.Write
				if prediction411 == 0 {
					_t812 := p.parse_define()
					define412 := _t812
					_t813 := &pb.Write{}
					_t813.WriteType = &pb.Write_Define{Define: define412}
					_t811 = _t813
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t808 = _t811
			}
			_t805 = _t808
		}
		_t802 = _t805
	}
	return _t802
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t814 := p.parse_fragment()
	fragment416 := _t814
	p.consumeLiteral(")")
	_t815 := &pb.Define{Fragment: fragment416}
	return _t815
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t816 := p.parse_new_fragment_id()
	new_fragment_id417 := _t816
	xs418 := []*pb.Declaration{}
	cond419 := p.matchLookaheadLiteral("(", 0)
	for cond419 {
		_t817 := p.parse_declaration()
		item420 := _t817
		xs418 = append(xs418, item420)
		cond419 = p.matchLookaheadLiteral("(", 0)
	}
	declarations421 := xs418
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id417, declarations421)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t818 := p.parse_fragment_id()
	fragment_id422 := _t818
	p.startFragment(fragment_id422)
	return fragment_id422
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t819 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t820 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t820 = 3
		} else {
			var _t821 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t821 = 2
			} else {
				var _t822 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t822 = 0
				} else {
					var _t823 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t823 = 3
					} else {
						var _t824 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t824 = 3
						} else {
							var _t825 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t825 = 1
							} else {
								_t825 = -1
							}
							_t824 = _t825
						}
						_t823 = _t824
					}
					_t822 = _t823
				}
				_t821 = _t822
			}
			_t820 = _t821
		}
		_t819 = _t820
	} else {
		_t819 = -1
	}
	prediction423 := _t819
	var _t826 *pb.Declaration
	if prediction423 == 3 {
		_t827 := p.parse_data()
		data427 := _t827
		_t828 := &pb.Declaration{}
		_t828.DeclarationType = &pb.Declaration_Data{Data: data427}
		_t826 = _t828
	} else {
		var _t829 *pb.Declaration
		if prediction423 == 2 {
			_t830 := p.parse_constraint()
			constraint426 := _t830
			_t831 := &pb.Declaration{}
			_t831.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint426}
			_t829 = _t831
		} else {
			var _t832 *pb.Declaration
			if prediction423 == 1 {
				_t833 := p.parse_algorithm()
				algorithm425 := _t833
				_t834 := &pb.Declaration{}
				_t834.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm425}
				_t832 = _t834
			} else {
				var _t835 *pb.Declaration
				if prediction423 == 0 {
					_t836 := p.parse_def()
					def424 := _t836
					_t837 := &pb.Declaration{}
					_t837.DeclarationType = &pb.Declaration_Def{Def: def424}
					_t835 = _t837
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t832 = _t835
			}
			_t829 = _t832
		}
		_t826 = _t829
	}
	return _t826
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t838 := p.parse_relation_id()
	relation_id428 := _t838
	_t839 := p.parse_abstraction()
	abstraction429 := _t839
	var _t840 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t841 := p.parse_attrs()
		_t840 = _t841
	}
	attrs430 := _t840
	p.consumeLiteral(")")
	_t842 := attrs430
	if attrs430 == nil {
		_t842 = []*pb.Attribute{}
	}
	_t843 := &pb.Def{Name: relation_id428, Body: abstraction429, Attrs: _t842}
	return _t843
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t844 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t844 = 0
	} else {
		var _t845 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t845 = 1
		} else {
			_t845 = -1
		}
		_t844 = _t845
	}
	prediction431 := _t844
	var _t846 *pb.RelationId
	if prediction431 == 1 {
		uint128433 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128433
		_t846 = &pb.RelationId{IdLow: uint128433.Low, IdHigh: uint128433.High}
	} else {
		var _t847 *pb.RelationId
		if prediction431 == 0 {
			p.consumeLiteral(":")
			symbol432 := p.consumeTerminal("SYMBOL").Value.str
			_t847 = p.relationIdFromString(symbol432)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t846 = _t847
	}
	return _t846
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t848 := p.parse_bindings()
	bindings434 := _t848
	_t849 := p.parse_formula()
	formula435 := _t849
	p.consumeLiteral(")")
	_t850 := &pb.Abstraction{Vars: listConcat(bindings434[0].([]*pb.Binding), bindings434[1].([]*pb.Binding)), Value: formula435}
	return _t850
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs436 := []*pb.Binding{}
	cond437 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond437 {
		_t851 := p.parse_binding()
		item438 := _t851
		xs436 = append(xs436, item438)
		cond437 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings439 := xs436
	var _t852 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t853 := p.parse_value_bindings()
		_t852 = _t853
	}
	value_bindings440 := _t852
	p.consumeLiteral("]")
	_t854 := value_bindings440
	if value_bindings440 == nil {
		_t854 = []*pb.Binding{}
	}
	return []interface{}{bindings439, _t854}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol441 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t855 := p.parse_type()
	type442 := _t855
	_t856 := &pb.Var{Name: symbol441}
	_t857 := &pb.Binding{Var: _t856, Type: type442}
	return _t857
}

func (p *Parser) parse_type() *pb.Type {
	var _t858 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t858 = 0
	} else {
		var _t859 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t859 = 4
		} else {
			var _t860 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t860 = 1
			} else {
				var _t861 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t861 = 8
				} else {
					var _t862 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t862 = 5
					} else {
						var _t863 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t863 = 2
						} else {
							var _t864 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t864 = 3
							} else {
								var _t865 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t865 = 7
								} else {
									var _t866 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t866 = 6
									} else {
										var _t867 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t867 = 10
										} else {
											var _t868 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t868 = 9
											} else {
												_t868 = -1
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
					_t861 = _t862
				}
				_t860 = _t861
			}
			_t859 = _t860
		}
		_t858 = _t859
	}
	prediction443 := _t858
	var _t869 *pb.Type
	if prediction443 == 10 {
		_t870 := p.parse_boolean_type()
		boolean_type454 := _t870
		_t871 := &pb.Type{}
		_t871.Type = &pb.Type_BooleanType{BooleanType: boolean_type454}
		_t869 = _t871
	} else {
		var _t872 *pb.Type
		if prediction443 == 9 {
			_t873 := p.parse_decimal_type()
			decimal_type453 := _t873
			_t874 := &pb.Type{}
			_t874.Type = &pb.Type_DecimalType{DecimalType: decimal_type453}
			_t872 = _t874
		} else {
			var _t875 *pb.Type
			if prediction443 == 8 {
				_t876 := p.parse_missing_type()
				missing_type452 := _t876
				_t877 := &pb.Type{}
				_t877.Type = &pb.Type_MissingType{MissingType: missing_type452}
				_t875 = _t877
			} else {
				var _t878 *pb.Type
				if prediction443 == 7 {
					_t879 := p.parse_datetime_type()
					datetime_type451 := _t879
					_t880 := &pb.Type{}
					_t880.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type451}
					_t878 = _t880
				} else {
					var _t881 *pb.Type
					if prediction443 == 6 {
						_t882 := p.parse_date_type()
						date_type450 := _t882
						_t883 := &pb.Type{}
						_t883.Type = &pb.Type_DateType{DateType: date_type450}
						_t881 = _t883
					} else {
						var _t884 *pb.Type
						if prediction443 == 5 {
							_t885 := p.parse_int128_type()
							int128_type449 := _t885
							_t886 := &pb.Type{}
							_t886.Type = &pb.Type_Int128Type{Int128Type: int128_type449}
							_t884 = _t886
						} else {
							var _t887 *pb.Type
							if prediction443 == 4 {
								_t888 := p.parse_uint128_type()
								uint128_type448 := _t888
								_t889 := &pb.Type{}
								_t889.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type448}
								_t887 = _t889
							} else {
								var _t890 *pb.Type
								if prediction443 == 3 {
									_t891 := p.parse_float_type()
									float_type447 := _t891
									_t892 := &pb.Type{}
									_t892.Type = &pb.Type_FloatType{FloatType: float_type447}
									_t890 = _t892
								} else {
									var _t893 *pb.Type
									if prediction443 == 2 {
										_t894 := p.parse_int_type()
										int_type446 := _t894
										_t895 := &pb.Type{}
										_t895.Type = &pb.Type_IntType{IntType: int_type446}
										_t893 = _t895
									} else {
										var _t896 *pb.Type
										if prediction443 == 1 {
											_t897 := p.parse_string_type()
											string_type445 := _t897
											_t898 := &pb.Type{}
											_t898.Type = &pb.Type_StringType{StringType: string_type445}
											_t896 = _t898
										} else {
											var _t899 *pb.Type
											if prediction443 == 0 {
												_t900 := p.parse_unspecified_type()
												unspecified_type444 := _t900
												_t901 := &pb.Type{}
												_t901.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type444}
												_t899 = _t901
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t896 = _t899
										}
										_t893 = _t896
									}
									_t890 = _t893
								}
								_t887 = _t890
							}
							_t884 = _t887
						}
						_t881 = _t884
					}
					_t878 = _t881
				}
				_t875 = _t878
			}
			_t872 = _t875
		}
		_t869 = _t872
	}
	return _t869
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t902 := &pb.UnspecifiedType{}
	return _t902
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t903 := &pb.StringType{}
	return _t903
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t904 := &pb.IntType{}
	return _t904
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t905 := &pb.FloatType{}
	return _t905
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t906 := &pb.UInt128Type{}
	return _t906
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t907 := &pb.Int128Type{}
	return _t907
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t908 := &pb.DateType{}
	return _t908
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t909 := &pb.DateTimeType{}
	return _t909
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t910 := &pb.MissingType{}
	return _t910
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int455 := p.consumeTerminal("INT").Value.i64
	int_3456 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t911 := &pb.DecimalType{Precision: int32(int455), Scale: int32(int_3456)}
	return _t911
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t912 := &pb.BooleanType{}
	return _t912
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs457 := []*pb.Binding{}
	cond458 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond458 {
		_t913 := p.parse_binding()
		item459 := _t913
		xs457 = append(xs457, item459)
		cond458 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings460 := xs457
	return bindings460
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t914 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t915 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t915 = 0
		} else {
			var _t916 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t916 = 11
			} else {
				var _t917 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t917 = 3
				} else {
					var _t918 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t918 = 10
					} else {
						var _t919 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t919 = 9
						} else {
							var _t920 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t920 = 5
							} else {
								var _t921 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t921 = 6
								} else {
									var _t922 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t922 = 7
									} else {
										var _t923 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t923 = 1
										} else {
											var _t924 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t924 = 2
											} else {
												var _t925 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t925 = 12
												} else {
													var _t926 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t926 = 8
													} else {
														var _t927 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t927 = 4
														} else {
															var _t928 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t928 = 10
															} else {
																var _t929 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t929 = 10
																} else {
																	var _t930 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t930 = 10
																	} else {
																		var _t931 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t931 = 10
																		} else {
																			var _t932 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t932 = 10
																			} else {
																				var _t933 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t933 = 10
																				} else {
																					var _t934 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t934 = 10
																					} else {
																						var _t935 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t935 = 10
																						} else {
																							var _t936 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t936 = 10
																							} else {
																								_t936 = -1
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
	prediction461 := _t914
	var _t937 *pb.Formula
	if prediction461 == 12 {
		_t938 := p.parse_cast()
		cast474 := _t938
		_t939 := &pb.Formula{}
		_t939.FormulaType = &pb.Formula_Cast{Cast: cast474}
		_t937 = _t939
	} else {
		var _t940 *pb.Formula
		if prediction461 == 11 {
			_t941 := p.parse_rel_atom()
			rel_atom473 := _t941
			_t942 := &pb.Formula{}
			_t942.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom473}
			_t940 = _t942
		} else {
			var _t943 *pb.Formula
			if prediction461 == 10 {
				_t944 := p.parse_primitive()
				primitive472 := _t944
				_t945 := &pb.Formula{}
				_t945.FormulaType = &pb.Formula_Primitive{Primitive: primitive472}
				_t943 = _t945
			} else {
				var _t946 *pb.Formula
				if prediction461 == 9 {
					_t947 := p.parse_pragma()
					pragma471 := _t947
					_t948 := &pb.Formula{}
					_t948.FormulaType = &pb.Formula_Pragma{Pragma: pragma471}
					_t946 = _t948
				} else {
					var _t949 *pb.Formula
					if prediction461 == 8 {
						_t950 := p.parse_atom()
						atom470 := _t950
						_t951 := &pb.Formula{}
						_t951.FormulaType = &pb.Formula_Atom{Atom: atom470}
						_t949 = _t951
					} else {
						var _t952 *pb.Formula
						if prediction461 == 7 {
							_t953 := p.parse_ffi()
							ffi469 := _t953
							_t954 := &pb.Formula{}
							_t954.FormulaType = &pb.Formula_Ffi{Ffi: ffi469}
							_t952 = _t954
						} else {
							var _t955 *pb.Formula
							if prediction461 == 6 {
								_t956 := p.parse_not()
								not468 := _t956
								_t957 := &pb.Formula{}
								_t957.FormulaType = &pb.Formula_Not{Not: not468}
								_t955 = _t957
							} else {
								var _t958 *pb.Formula
								if prediction461 == 5 {
									_t959 := p.parse_disjunction()
									disjunction467 := _t959
									_t960 := &pb.Formula{}
									_t960.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction467}
									_t958 = _t960
								} else {
									var _t961 *pb.Formula
									if prediction461 == 4 {
										_t962 := p.parse_conjunction()
										conjunction466 := _t962
										_t963 := &pb.Formula{}
										_t963.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction466}
										_t961 = _t963
									} else {
										var _t964 *pb.Formula
										if prediction461 == 3 {
											_t965 := p.parse_reduce()
											reduce465 := _t965
											_t966 := &pb.Formula{}
											_t966.FormulaType = &pb.Formula_Reduce{Reduce: reduce465}
											_t964 = _t966
										} else {
											var _t967 *pb.Formula
											if prediction461 == 2 {
												_t968 := p.parse_exists()
												exists464 := _t968
												_t969 := &pb.Formula{}
												_t969.FormulaType = &pb.Formula_Exists{Exists: exists464}
												_t967 = _t969
											} else {
												var _t970 *pb.Formula
												if prediction461 == 1 {
													_t971 := p.parse_false()
													false463 := _t971
													_t972 := &pb.Formula{}
													_t972.FormulaType = &pb.Formula_Disjunction{Disjunction: false463}
													_t970 = _t972
												} else {
													var _t973 *pb.Formula
													if prediction461 == 0 {
														_t974 := p.parse_true()
														true462 := _t974
														_t975 := &pb.Formula{}
														_t975.FormulaType = &pb.Formula_Conjunction{Conjunction: true462}
														_t973 = _t975
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t970 = _t973
												}
												_t967 = _t970
											}
											_t964 = _t967
										}
										_t961 = _t964
									}
									_t958 = _t961
								}
								_t955 = _t958
							}
							_t952 = _t955
						}
						_t949 = _t952
					}
					_t946 = _t949
				}
				_t943 = _t946
			}
			_t940 = _t943
		}
		_t937 = _t940
	}
	return _t937
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t976 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t976
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t977 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t977
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t978 := p.parse_bindings()
	bindings475 := _t978
	_t979 := p.parse_formula()
	formula476 := _t979
	p.consumeLiteral(")")
	_t980 := &pb.Abstraction{Vars: listConcat(bindings475[0].([]*pb.Binding), bindings475[1].([]*pb.Binding)), Value: formula476}
	_t981 := &pb.Exists{Body: _t980}
	return _t981
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t982 := p.parse_abstraction()
	abstraction477 := _t982
	_t983 := p.parse_abstraction()
	abstraction_3478 := _t983
	_t984 := p.parse_terms()
	terms479 := _t984
	p.consumeLiteral(")")
	_t985 := &pb.Reduce{Op: abstraction477, Body: abstraction_3478, Terms: terms479}
	return _t985
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs480 := []*pb.Term{}
	cond481 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond481 {
		_t986 := p.parse_term()
		item482 := _t986
		xs480 = append(xs480, item482)
		cond481 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms483 := xs480
	p.consumeLiteral(")")
	return terms483
}

func (p *Parser) parse_term() *pb.Term {
	var _t987 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t987 = 1
	} else {
		var _t988 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t988 = 1
		} else {
			var _t989 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t989 = 1
			} else {
				var _t990 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t990 = 1
				} else {
					var _t991 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t991 = 1
					} else {
						var _t992 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t992 = 0
						} else {
							var _t993 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t993 = 1
							} else {
								var _t994 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t994 = 1
								} else {
									var _t995 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t995 = 1
									} else {
										var _t996 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t996 = 1
										} else {
											var _t997 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t997 = 1
											} else {
												_t997 = -1
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
					_t990 = _t991
				}
				_t989 = _t990
			}
			_t988 = _t989
		}
		_t987 = _t988
	}
	prediction484 := _t987
	var _t998 *pb.Term
	if prediction484 == 1 {
		_t999 := p.parse_constant()
		constant486 := _t999
		_t1000 := &pb.Term{}
		_t1000.TermType = &pb.Term_Constant{Constant: constant486}
		_t998 = _t1000
	} else {
		var _t1001 *pb.Term
		if prediction484 == 0 {
			_t1002 := p.parse_var()
			var485 := _t1002
			_t1003 := &pb.Term{}
			_t1003.TermType = &pb.Term_Var{Var: var485}
			_t1001 = _t1003
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t998 = _t1001
	}
	return _t998
}

func (p *Parser) parse_var() *pb.Var {
	symbol487 := p.consumeTerminal("SYMBOL").Value.str
	_t1004 := &pb.Var{Name: symbol487}
	return _t1004
}

func (p *Parser) parse_constant() *pb.Value {
	_t1005 := p.parse_value()
	value488 := _t1005
	return value488
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs489 := []*pb.Formula{}
	cond490 := p.matchLookaheadLiteral("(", 0)
	for cond490 {
		_t1006 := p.parse_formula()
		item491 := _t1006
		xs489 = append(xs489, item491)
		cond490 = p.matchLookaheadLiteral("(", 0)
	}
	formulas492 := xs489
	p.consumeLiteral(")")
	_t1007 := &pb.Conjunction{Args: formulas492}
	return _t1007
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs493 := []*pb.Formula{}
	cond494 := p.matchLookaheadLiteral("(", 0)
	for cond494 {
		_t1008 := p.parse_formula()
		item495 := _t1008
		xs493 = append(xs493, item495)
		cond494 = p.matchLookaheadLiteral("(", 0)
	}
	formulas496 := xs493
	p.consumeLiteral(")")
	_t1009 := &pb.Disjunction{Args: formulas496}
	return _t1009
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1010 := p.parse_formula()
	formula497 := _t1010
	p.consumeLiteral(")")
	_t1011 := &pb.Not{Arg: formula497}
	return _t1011
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1012 := p.parse_name()
	name498 := _t1012
	_t1013 := p.parse_ffi_args()
	ffi_args499 := _t1013
	_t1014 := p.parse_terms()
	terms500 := _t1014
	p.consumeLiteral(")")
	_t1015 := &pb.FFI{Name: name498, Args: ffi_args499, Terms: terms500}
	return _t1015
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol501 := p.consumeTerminal("SYMBOL").Value.str
	return symbol501
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs502 := []*pb.Abstraction{}
	cond503 := p.matchLookaheadLiteral("(", 0)
	for cond503 {
		_t1016 := p.parse_abstraction()
		item504 := _t1016
		xs502 = append(xs502, item504)
		cond503 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions505 := xs502
	p.consumeLiteral(")")
	return abstractions505
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1017 := p.parse_relation_id()
	relation_id506 := _t1017
	xs507 := []*pb.Term{}
	cond508 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond508 {
		_t1018 := p.parse_term()
		item509 := _t1018
		xs507 = append(xs507, item509)
		cond508 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms510 := xs507
	p.consumeLiteral(")")
	_t1019 := &pb.Atom{Name: relation_id506, Terms: terms510}
	return _t1019
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1020 := p.parse_name()
	name511 := _t1020
	xs512 := []*pb.Term{}
	cond513 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond513 {
		_t1021 := p.parse_term()
		item514 := _t1021
		xs512 = append(xs512, item514)
		cond513 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms515 := xs512
	p.consumeLiteral(")")
	_t1022 := &pb.Pragma{Name: name511, Terms: terms515}
	return _t1022
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1023 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1024 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1024 = 9
		} else {
			var _t1025 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1025 = 4
			} else {
				var _t1026 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1026 = 3
				} else {
					var _t1027 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1027 = 0
					} else {
						var _t1028 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1028 = 2
						} else {
							var _t1029 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1029 = 1
							} else {
								var _t1030 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1030 = 8
								} else {
									var _t1031 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1031 = 6
									} else {
										var _t1032 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1032 = 5
										} else {
											var _t1033 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1033 = 7
											} else {
												_t1033 = -1
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
					}
					_t1026 = _t1027
				}
				_t1025 = _t1026
			}
			_t1024 = _t1025
		}
		_t1023 = _t1024
	} else {
		_t1023 = -1
	}
	prediction516 := _t1023
	var _t1034 *pb.Primitive
	if prediction516 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1035 := p.parse_name()
		name526 := _t1035
		xs527 := []*pb.RelTerm{}
		cond528 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond528 {
			_t1036 := p.parse_rel_term()
			item529 := _t1036
			xs527 = append(xs527, item529)
			cond528 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms530 := xs527
		p.consumeLiteral(")")
		_t1037 := &pb.Primitive{Name: name526, Terms: rel_terms530}
		_t1034 = _t1037
	} else {
		var _t1038 *pb.Primitive
		if prediction516 == 8 {
			_t1039 := p.parse_divide()
			divide525 := _t1039
			_t1038 = divide525
		} else {
			var _t1040 *pb.Primitive
			if prediction516 == 7 {
				_t1041 := p.parse_multiply()
				multiply524 := _t1041
				_t1040 = multiply524
			} else {
				var _t1042 *pb.Primitive
				if prediction516 == 6 {
					_t1043 := p.parse_minus()
					minus523 := _t1043
					_t1042 = minus523
				} else {
					var _t1044 *pb.Primitive
					if prediction516 == 5 {
						_t1045 := p.parse_add()
						add522 := _t1045
						_t1044 = add522
					} else {
						var _t1046 *pb.Primitive
						if prediction516 == 4 {
							_t1047 := p.parse_gt_eq()
							gt_eq521 := _t1047
							_t1046 = gt_eq521
						} else {
							var _t1048 *pb.Primitive
							if prediction516 == 3 {
								_t1049 := p.parse_gt()
								gt520 := _t1049
								_t1048 = gt520
							} else {
								var _t1050 *pb.Primitive
								if prediction516 == 2 {
									_t1051 := p.parse_lt_eq()
									lt_eq519 := _t1051
									_t1050 = lt_eq519
								} else {
									var _t1052 *pb.Primitive
									if prediction516 == 1 {
										_t1053 := p.parse_lt()
										lt518 := _t1053
										_t1052 = lt518
									} else {
										var _t1054 *pb.Primitive
										if prediction516 == 0 {
											_t1055 := p.parse_eq()
											eq517 := _t1055
											_t1054 = eq517
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
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
				_t1040 = _t1042
			}
			_t1038 = _t1040
		}
		_t1034 = _t1038
	}
	return _t1034
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1056 := p.parse_term()
	term531 := _t1056
	_t1057 := p.parse_term()
	term_3532 := _t1057
	p.consumeLiteral(")")
	_t1058 := &pb.RelTerm{}
	_t1058.RelTermType = &pb.RelTerm_Term{Term: term531}
	_t1059 := &pb.RelTerm{}
	_t1059.RelTermType = &pb.RelTerm_Term{Term: term_3532}
	_t1060 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1058, _t1059}}
	return _t1060
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1061 := p.parse_term()
	term533 := _t1061
	_t1062 := p.parse_term()
	term_3534 := _t1062
	p.consumeLiteral(")")
	_t1063 := &pb.RelTerm{}
	_t1063.RelTermType = &pb.RelTerm_Term{Term: term533}
	_t1064 := &pb.RelTerm{}
	_t1064.RelTermType = &pb.RelTerm_Term{Term: term_3534}
	_t1065 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1063, _t1064}}
	return _t1065
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1066 := p.parse_term()
	term535 := _t1066
	_t1067 := p.parse_term()
	term_3536 := _t1067
	p.consumeLiteral(")")
	_t1068 := &pb.RelTerm{}
	_t1068.RelTermType = &pb.RelTerm_Term{Term: term535}
	_t1069 := &pb.RelTerm{}
	_t1069.RelTermType = &pb.RelTerm_Term{Term: term_3536}
	_t1070 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1068, _t1069}}
	return _t1070
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1071 := p.parse_term()
	term537 := _t1071
	_t1072 := p.parse_term()
	term_3538 := _t1072
	p.consumeLiteral(")")
	_t1073 := &pb.RelTerm{}
	_t1073.RelTermType = &pb.RelTerm_Term{Term: term537}
	_t1074 := &pb.RelTerm{}
	_t1074.RelTermType = &pb.RelTerm_Term{Term: term_3538}
	_t1075 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1073, _t1074}}
	return _t1075
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1076 := p.parse_term()
	term539 := _t1076
	_t1077 := p.parse_term()
	term_3540 := _t1077
	p.consumeLiteral(")")
	_t1078 := &pb.RelTerm{}
	_t1078.RelTermType = &pb.RelTerm_Term{Term: term539}
	_t1079 := &pb.RelTerm{}
	_t1079.RelTermType = &pb.RelTerm_Term{Term: term_3540}
	_t1080 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1078, _t1079}}
	return _t1080
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1081 := p.parse_term()
	term541 := _t1081
	_t1082 := p.parse_term()
	term_3542 := _t1082
	_t1083 := p.parse_term()
	term_4543 := _t1083
	p.consumeLiteral(")")
	_t1084 := &pb.RelTerm{}
	_t1084.RelTermType = &pb.RelTerm_Term{Term: term541}
	_t1085 := &pb.RelTerm{}
	_t1085.RelTermType = &pb.RelTerm_Term{Term: term_3542}
	_t1086 := &pb.RelTerm{}
	_t1086.RelTermType = &pb.RelTerm_Term{Term: term_4543}
	_t1087 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1084, _t1085, _t1086}}
	return _t1087
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1088 := p.parse_term()
	term544 := _t1088
	_t1089 := p.parse_term()
	term_3545 := _t1089
	_t1090 := p.parse_term()
	term_4546 := _t1090
	p.consumeLiteral(")")
	_t1091 := &pb.RelTerm{}
	_t1091.RelTermType = &pb.RelTerm_Term{Term: term544}
	_t1092 := &pb.RelTerm{}
	_t1092.RelTermType = &pb.RelTerm_Term{Term: term_3545}
	_t1093 := &pb.RelTerm{}
	_t1093.RelTermType = &pb.RelTerm_Term{Term: term_4546}
	_t1094 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1091, _t1092, _t1093}}
	return _t1094
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1095 := p.parse_term()
	term547 := _t1095
	_t1096 := p.parse_term()
	term_3548 := _t1096
	_t1097 := p.parse_term()
	term_4549 := _t1097
	p.consumeLiteral(")")
	_t1098 := &pb.RelTerm{}
	_t1098.RelTermType = &pb.RelTerm_Term{Term: term547}
	_t1099 := &pb.RelTerm{}
	_t1099.RelTermType = &pb.RelTerm_Term{Term: term_3548}
	_t1100 := &pb.RelTerm{}
	_t1100.RelTermType = &pb.RelTerm_Term{Term: term_4549}
	_t1101 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1098, _t1099, _t1100}}
	return _t1101
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1102 := p.parse_term()
	term550 := _t1102
	_t1103 := p.parse_term()
	term_3551 := _t1103
	_t1104 := p.parse_term()
	term_4552 := _t1104
	p.consumeLiteral(")")
	_t1105 := &pb.RelTerm{}
	_t1105.RelTermType = &pb.RelTerm_Term{Term: term550}
	_t1106 := &pb.RelTerm{}
	_t1106.RelTermType = &pb.RelTerm_Term{Term: term_3551}
	_t1107 := &pb.RelTerm{}
	_t1107.RelTermType = &pb.RelTerm_Term{Term: term_4552}
	_t1108 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1105, _t1106, _t1107}}
	return _t1108
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1109 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1109 = 1
	} else {
		var _t1110 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1110 = 1
		} else {
			var _t1111 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1111 = 1
			} else {
				var _t1112 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1112 = 1
				} else {
					var _t1113 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1113 = 0
					} else {
						var _t1114 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1114 = 1
						} else {
							var _t1115 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1115 = 1
							} else {
								var _t1116 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1116 = 1
								} else {
									var _t1117 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1117 = 1
									} else {
										var _t1118 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1118 = 1
										} else {
											var _t1119 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1119 = 1
											} else {
												var _t1120 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1120 = 1
												} else {
													_t1120 = -1
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
					_t1112 = _t1113
				}
				_t1111 = _t1112
			}
			_t1110 = _t1111
		}
		_t1109 = _t1110
	}
	prediction553 := _t1109
	var _t1121 *pb.RelTerm
	if prediction553 == 1 {
		_t1122 := p.parse_term()
		term555 := _t1122
		_t1123 := &pb.RelTerm{}
		_t1123.RelTermType = &pb.RelTerm_Term{Term: term555}
		_t1121 = _t1123
	} else {
		var _t1124 *pb.RelTerm
		if prediction553 == 0 {
			_t1125 := p.parse_specialized_value()
			specialized_value554 := _t1125
			_t1126 := &pb.RelTerm{}
			_t1126.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value554}
			_t1124 = _t1126
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1121 = _t1124
	}
	return _t1121
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1127 := p.parse_value()
	value556 := _t1127
	return value556
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1128 := p.parse_name()
	name557 := _t1128
	xs558 := []*pb.RelTerm{}
	cond559 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond559 {
		_t1129 := p.parse_rel_term()
		item560 := _t1129
		xs558 = append(xs558, item560)
		cond559 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms561 := xs558
	p.consumeLiteral(")")
	_t1130 := &pb.RelAtom{Name: name557, Terms: rel_terms561}
	return _t1130
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1131 := p.parse_term()
	term562 := _t1131
	_t1132 := p.parse_term()
	term_3563 := _t1132
	p.consumeLiteral(")")
	_t1133 := &pb.Cast{Input: term562, Result: term_3563}
	return _t1133
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs564 := []*pb.Attribute{}
	cond565 := p.matchLookaheadLiteral("(", 0)
	for cond565 {
		_t1134 := p.parse_attribute()
		item566 := _t1134
		xs564 = append(xs564, item566)
		cond565 = p.matchLookaheadLiteral("(", 0)
	}
	attributes567 := xs564
	p.consumeLiteral(")")
	return attributes567
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1135 := p.parse_name()
	name568 := _t1135
	xs569 := []*pb.Value{}
	cond570 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond570 {
		_t1136 := p.parse_value()
		item571 := _t1136
		xs569 = append(xs569, item571)
		cond570 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values572 := xs569
	p.consumeLiteral(")")
	_t1137 := &pb.Attribute{Name: name568, Args: values572}
	return _t1137
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs573 := []*pb.RelationId{}
	cond574 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond574 {
		_t1138 := p.parse_relation_id()
		item575 := _t1138
		xs573 = append(xs573, item575)
		cond574 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids576 := xs573
	_t1139 := p.parse_script()
	script577 := _t1139
	p.consumeLiteral(")")
	_t1140 := &pb.Algorithm{Global: relation_ids576, Body: script577}
	return _t1140
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs578 := []*pb.Construct{}
	cond579 := p.matchLookaheadLiteral("(", 0)
	for cond579 {
		_t1141 := p.parse_construct()
		item580 := _t1141
		xs578 = append(xs578, item580)
		cond579 = p.matchLookaheadLiteral("(", 0)
	}
	constructs581 := xs578
	p.consumeLiteral(")")
	_t1142 := &pb.Script{Constructs: constructs581}
	return _t1142
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1143 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1144 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1144 = 1
		} else {
			var _t1145 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1145 = 1
			} else {
				var _t1146 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1146 = 1
				} else {
					var _t1147 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1147 = 0
					} else {
						var _t1148 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1148 = 1
						} else {
							var _t1149 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1149 = 1
							} else {
								_t1149 = -1
							}
							_t1148 = _t1149
						}
						_t1147 = _t1148
					}
					_t1146 = _t1147
				}
				_t1145 = _t1146
			}
			_t1144 = _t1145
		}
		_t1143 = _t1144
	} else {
		_t1143 = -1
	}
	prediction582 := _t1143
	var _t1150 *pb.Construct
	if prediction582 == 1 {
		_t1151 := p.parse_instruction()
		instruction584 := _t1151
		_t1152 := &pb.Construct{}
		_t1152.ConstructType = &pb.Construct_Instruction{Instruction: instruction584}
		_t1150 = _t1152
	} else {
		var _t1153 *pb.Construct
		if prediction582 == 0 {
			_t1154 := p.parse_loop()
			loop583 := _t1154
			_t1155 := &pb.Construct{}
			_t1155.ConstructType = &pb.Construct_Loop{Loop: loop583}
			_t1153 = _t1155
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1150 = _t1153
	}
	return _t1150
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1156 := p.parse_init()
	init585 := _t1156
	_t1157 := p.parse_script()
	script586 := _t1157
	p.consumeLiteral(")")
	_t1158 := &pb.Loop{Init: init585, Body: script586}
	return _t1158
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs587 := []*pb.Instruction{}
	cond588 := p.matchLookaheadLiteral("(", 0)
	for cond588 {
		_t1159 := p.parse_instruction()
		item589 := _t1159
		xs587 = append(xs587, item589)
		cond588 = p.matchLookaheadLiteral("(", 0)
	}
	instructions590 := xs587
	p.consumeLiteral(")")
	return instructions590
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1160 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1161 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1161 = 1
		} else {
			var _t1162 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1162 = 4
			} else {
				var _t1163 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1163 = 3
				} else {
					var _t1164 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1164 = 2
					} else {
						var _t1165 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1165 = 0
						} else {
							_t1165 = -1
						}
						_t1164 = _t1165
					}
					_t1163 = _t1164
				}
				_t1162 = _t1163
			}
			_t1161 = _t1162
		}
		_t1160 = _t1161
	} else {
		_t1160 = -1
	}
	prediction591 := _t1160
	var _t1166 *pb.Instruction
	if prediction591 == 4 {
		_t1167 := p.parse_monus_def()
		monus_def596 := _t1167
		_t1168 := &pb.Instruction{}
		_t1168.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def596}
		_t1166 = _t1168
	} else {
		var _t1169 *pb.Instruction
		if prediction591 == 3 {
			_t1170 := p.parse_monoid_def()
			monoid_def595 := _t1170
			_t1171 := &pb.Instruction{}
			_t1171.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def595}
			_t1169 = _t1171
		} else {
			var _t1172 *pb.Instruction
			if prediction591 == 2 {
				_t1173 := p.parse_break()
				break594 := _t1173
				_t1174 := &pb.Instruction{}
				_t1174.InstrType = &pb.Instruction_Break{Break: break594}
				_t1172 = _t1174
			} else {
				var _t1175 *pb.Instruction
				if prediction591 == 1 {
					_t1176 := p.parse_upsert()
					upsert593 := _t1176
					_t1177 := &pb.Instruction{}
					_t1177.InstrType = &pb.Instruction_Upsert{Upsert: upsert593}
					_t1175 = _t1177
				} else {
					var _t1178 *pb.Instruction
					if prediction591 == 0 {
						_t1179 := p.parse_assign()
						assign592 := _t1179
						_t1180 := &pb.Instruction{}
						_t1180.InstrType = &pb.Instruction_Assign{Assign: assign592}
						_t1178 = _t1180
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1175 = _t1178
				}
				_t1172 = _t1175
			}
			_t1169 = _t1172
		}
		_t1166 = _t1169
	}
	return _t1166
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1181 := p.parse_relation_id()
	relation_id597 := _t1181
	_t1182 := p.parse_abstraction()
	abstraction598 := _t1182
	var _t1183 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1184 := p.parse_attrs()
		_t1183 = _t1184
	}
	attrs599 := _t1183
	p.consumeLiteral(")")
	_t1185 := attrs599
	if attrs599 == nil {
		_t1185 = []*pb.Attribute{}
	}
	_t1186 := &pb.Assign{Name: relation_id597, Body: abstraction598, Attrs: _t1185}
	return _t1186
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1187 := p.parse_relation_id()
	relation_id600 := _t1187
	_t1188 := p.parse_abstraction_with_arity()
	abstraction_with_arity601 := _t1188
	var _t1189 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1190 := p.parse_attrs()
		_t1189 = _t1190
	}
	attrs602 := _t1189
	p.consumeLiteral(")")
	_t1191 := attrs602
	if attrs602 == nil {
		_t1191 = []*pb.Attribute{}
	}
	_t1192 := &pb.Upsert{Name: relation_id600, Body: abstraction_with_arity601[0].(*pb.Abstraction), Attrs: _t1191, ValueArity: abstraction_with_arity601[1].(int64)}
	return _t1192
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1193 := p.parse_bindings()
	bindings603 := _t1193
	_t1194 := p.parse_formula()
	formula604 := _t1194
	p.consumeLiteral(")")
	_t1195 := &pb.Abstraction{Vars: listConcat(bindings603[0].([]*pb.Binding), bindings603[1].([]*pb.Binding)), Value: formula604}
	return []interface{}{_t1195, int64(len(bindings603[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1196 := p.parse_relation_id()
	relation_id605 := _t1196
	_t1197 := p.parse_abstraction()
	abstraction606 := _t1197
	var _t1198 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1199 := p.parse_attrs()
		_t1198 = _t1199
	}
	attrs607 := _t1198
	p.consumeLiteral(")")
	_t1200 := attrs607
	if attrs607 == nil {
		_t1200 = []*pb.Attribute{}
	}
	_t1201 := &pb.Break{Name: relation_id605, Body: abstraction606, Attrs: _t1200}
	return _t1201
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1202 := p.parse_monoid()
	monoid608 := _t1202
	_t1203 := p.parse_relation_id()
	relation_id609 := _t1203
	_t1204 := p.parse_abstraction_with_arity()
	abstraction_with_arity610 := _t1204
	var _t1205 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1206 := p.parse_attrs()
		_t1205 = _t1206
	}
	attrs611 := _t1205
	p.consumeLiteral(")")
	_t1207 := attrs611
	if attrs611 == nil {
		_t1207 = []*pb.Attribute{}
	}
	_t1208 := &pb.MonoidDef{Monoid: monoid608, Name: relation_id609, Body: abstraction_with_arity610[0].(*pb.Abstraction), Attrs: _t1207, ValueArity: abstraction_with_arity610[1].(int64)}
	return _t1208
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1209 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1210 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1210 = 3
		} else {
			var _t1211 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1211 = 0
			} else {
				var _t1212 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1212 = 1
				} else {
					var _t1213 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1213 = 2
					} else {
						_t1213 = -1
					}
					_t1212 = _t1213
				}
				_t1211 = _t1212
			}
			_t1210 = _t1211
		}
		_t1209 = _t1210
	} else {
		_t1209 = -1
	}
	prediction612 := _t1209
	var _t1214 *pb.Monoid
	if prediction612 == 3 {
		_t1215 := p.parse_sum_monoid()
		sum_monoid616 := _t1215
		_t1216 := &pb.Monoid{}
		_t1216.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid616}
		_t1214 = _t1216
	} else {
		var _t1217 *pb.Monoid
		if prediction612 == 2 {
			_t1218 := p.parse_max_monoid()
			max_monoid615 := _t1218
			_t1219 := &pb.Monoid{}
			_t1219.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid615}
			_t1217 = _t1219
		} else {
			var _t1220 *pb.Monoid
			if prediction612 == 1 {
				_t1221 := p.parse_min_monoid()
				min_monoid614 := _t1221
				_t1222 := &pb.Monoid{}
				_t1222.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid614}
				_t1220 = _t1222
			} else {
				var _t1223 *pb.Monoid
				if prediction612 == 0 {
					_t1224 := p.parse_or_monoid()
					or_monoid613 := _t1224
					_t1225 := &pb.Monoid{}
					_t1225.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid613}
					_t1223 = _t1225
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1220 = _t1223
			}
			_t1217 = _t1220
		}
		_t1214 = _t1217
	}
	return _t1214
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1226 := &pb.OrMonoid{}
	return _t1226
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1227 := p.parse_type()
	type617 := _t1227
	p.consumeLiteral(")")
	_t1228 := &pb.MinMonoid{Type: type617}
	return _t1228
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1229 := p.parse_type()
	type618 := _t1229
	p.consumeLiteral(")")
	_t1230 := &pb.MaxMonoid{Type: type618}
	return _t1230
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1231 := p.parse_type()
	type619 := _t1231
	p.consumeLiteral(")")
	_t1232 := &pb.SumMonoid{Type: type619}
	return _t1232
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1233 := p.parse_monoid()
	monoid620 := _t1233
	_t1234 := p.parse_relation_id()
	relation_id621 := _t1234
	_t1235 := p.parse_abstraction_with_arity()
	abstraction_with_arity622 := _t1235
	var _t1236 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1237 := p.parse_attrs()
		_t1236 = _t1237
	}
	attrs623 := _t1236
	p.consumeLiteral(")")
	_t1238 := attrs623
	if attrs623 == nil {
		_t1238 = []*pb.Attribute{}
	}
	_t1239 := &pb.MonusDef{Monoid: monoid620, Name: relation_id621, Body: abstraction_with_arity622[0].(*pb.Abstraction), Attrs: _t1238, ValueArity: abstraction_with_arity622[1].(int64)}
	return _t1239
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1240 := p.parse_relation_id()
	relation_id624 := _t1240
	_t1241 := p.parse_abstraction()
	abstraction625 := _t1241
	_t1242 := p.parse_functional_dependency_keys()
	functional_dependency_keys626 := _t1242
	_t1243 := p.parse_functional_dependency_values()
	functional_dependency_values627 := _t1243
	p.consumeLiteral(")")
	_t1244 := &pb.FunctionalDependency{Guard: abstraction625, Keys: functional_dependency_keys626, Values: functional_dependency_values627}
	_t1245 := &pb.Constraint{Name: relation_id624}
	_t1245.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1244}
	return _t1245
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs628 := []*pb.Var{}
	cond629 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond629 {
		_t1246 := p.parse_var()
		item630 := _t1246
		xs628 = append(xs628, item630)
		cond629 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars631 := xs628
	p.consumeLiteral(")")
	return vars631
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs632 := []*pb.Var{}
	cond633 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond633 {
		_t1247 := p.parse_var()
		item634 := _t1247
		xs632 = append(xs632, item634)
		cond633 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars635 := xs632
	p.consumeLiteral(")")
	return vars635
}

func (p *Parser) parse_data() *pb.Data {
	var _t1248 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1249 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1249 = 0
		} else {
			var _t1250 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1250 = 2
			} else {
				var _t1251 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1251 = 1
				} else {
					_t1251 = -1
				}
				_t1250 = _t1251
			}
			_t1249 = _t1250
		}
		_t1248 = _t1249
	} else {
		_t1248 = -1
	}
	prediction636 := _t1248
	var _t1252 *pb.Data
	if prediction636 == 2 {
		_t1253 := p.parse_csv_data()
		csv_data639 := _t1253
		_t1254 := &pb.Data{}
		_t1254.DataType = &pb.Data_CsvData{CsvData: csv_data639}
		_t1252 = _t1254
	} else {
		var _t1255 *pb.Data
		if prediction636 == 1 {
			_t1256 := p.parse_betree_relation()
			betree_relation638 := _t1256
			_t1257 := &pb.Data{}
			_t1257.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation638}
			_t1255 = _t1257
		} else {
			var _t1258 *pb.Data
			if prediction636 == 0 {
				_t1259 := p.parse_rel_edb()
				rel_edb637 := _t1259
				_t1260 := &pb.Data{}
				_t1260.DataType = &pb.Data_RelEdb{RelEdb: rel_edb637}
				_t1258 = _t1260
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1255 = _t1258
		}
		_t1252 = _t1255
	}
	return _t1252
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1261 := p.parse_relation_id()
	relation_id640 := _t1261
	_t1262 := p.parse_rel_edb_path()
	rel_edb_path641 := _t1262
	_t1263 := p.parse_rel_edb_types()
	rel_edb_types642 := _t1263
	p.consumeLiteral(")")
	_t1264 := &pb.RelEDB{TargetId: relation_id640, Path: rel_edb_path641, Types: rel_edb_types642}
	return _t1264
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs643 := []string{}
	cond644 := p.matchLookaheadTerminal("STRING", 0)
	for cond644 {
		item645 := p.consumeTerminal("STRING").Value.str
		xs643 = append(xs643, item645)
		cond644 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings646 := xs643
	p.consumeLiteral("]")
	return strings646
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs647 := []*pb.Type{}
	cond648 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond648 {
		_t1265 := p.parse_type()
		item649 := _t1265
		xs647 = append(xs647, item649)
		cond648 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types650 := xs647
	p.consumeLiteral("]")
	return types650
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1266 := p.parse_relation_id()
	relation_id651 := _t1266
	_t1267 := p.parse_betree_info()
	betree_info652 := _t1267
	p.consumeLiteral(")")
	_t1268 := &pb.BeTreeRelation{Name: relation_id651, RelationInfo: betree_info652}
	return _t1268
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1269 := p.parse_betree_info_key_types()
	betree_info_key_types653 := _t1269
	_t1270 := p.parse_betree_info_value_types()
	betree_info_value_types654 := _t1270
	_t1271 := p.parse_config_dict()
	config_dict655 := _t1271
	p.consumeLiteral(")")
	_t1272 := p.construct_betree_info(betree_info_key_types653, betree_info_value_types654, config_dict655)
	return _t1272
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs656 := []*pb.Type{}
	cond657 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond657 {
		_t1273 := p.parse_type()
		item658 := _t1273
		xs656 = append(xs656, item658)
		cond657 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types659 := xs656
	p.consumeLiteral(")")
	return types659
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs660 := []*pb.Type{}
	cond661 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond661 {
		_t1274 := p.parse_type()
		item662 := _t1274
		xs660 = append(xs660, item662)
		cond661 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types663 := xs660
	p.consumeLiteral(")")
	return types663
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1275 := p.parse_csvlocator()
	csvlocator664 := _t1275
	_t1276 := p.parse_csv_config()
	csv_config665 := _t1276
	_t1277 := p.parse_csv_columns()
	csv_columns666 := _t1277
	_t1278 := p.parse_csv_asof()
	csv_asof667 := _t1278
	p.consumeLiteral(")")
	_t1279 := &pb.CSVData{Locator: csvlocator664, Config: csv_config665, Columns: csv_columns666, Asof: csv_asof667}
	return _t1279
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1280 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1281 := p.parse_csv_locator_paths()
		_t1280 = _t1281
	}
	csv_locator_paths668 := _t1280
	var _t1282 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1283 := p.parse_csv_locator_inline_data()
		_t1282 = ptr(_t1283)
	}
	csv_locator_inline_data669 := _t1282
	p.consumeLiteral(")")
	_t1284 := csv_locator_paths668
	if csv_locator_paths668 == nil {
		_t1284 = []string{}
	}
	_t1285 := &pb.CSVLocator{Paths: _t1284, InlineData: []byte(deref(csv_locator_inline_data669, ""))}
	return _t1285
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs670 := []string{}
	cond671 := p.matchLookaheadTerminal("STRING", 0)
	for cond671 {
		item672 := p.consumeTerminal("STRING").Value.str
		xs670 = append(xs670, item672)
		cond671 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings673 := xs670
	p.consumeLiteral(")")
	return strings673
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string674 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string674
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1286 := p.parse_config_dict()
	config_dict675 := _t1286
	p.consumeLiteral(")")
	_t1287 := p.construct_csv_config(config_dict675)
	return _t1287
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs676 := []*pb.CSVColumn{}
	cond677 := p.matchLookaheadLiteral("(", 0)
	for cond677 {
		_t1288 := p.parse_csv_column()
		item678 := _t1288
		xs676 = append(xs676, item678)
		cond677 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns679 := xs676
	p.consumeLiteral(")")
	return csv_columns679
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string680 := p.consumeTerminal("STRING").Value.str
	_t1289 := p.parse_relation_id()
	relation_id681 := _t1289
	p.consumeLiteral("[")
	xs682 := []*pb.Type{}
	cond683 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond683 {
		_t1290 := p.parse_type()
		item684 := _t1290
		xs682 = append(xs682, item684)
		cond683 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types685 := xs682
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1291 := &pb.CSVColumn{ColumnName: string680, TargetId: relation_id681, Types: types685}
	return _t1291
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string686 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string686
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1292 := p.parse_fragment_id()
	fragment_id687 := _t1292
	p.consumeLiteral(")")
	_t1293 := &pb.Undefine{FragmentId: fragment_id687}
	return _t1293
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs688 := []*pb.RelationId{}
	cond689 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond689 {
		_t1294 := p.parse_relation_id()
		item690 := _t1294
		xs688 = append(xs688, item690)
		cond689 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids691 := xs688
	p.consumeLiteral(")")
	_t1295 := &pb.Context{Relations: relation_ids691}
	return _t1295
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1296 := p.parse_rel_edb_path()
	rel_edb_path692 := _t1296
	_t1297 := p.parse_relation_id()
	relation_id693 := _t1297
	p.consumeLiteral(")")
	_t1298 := &pb.Snapshot{DestinationPath: rel_edb_path692, SourceRelation: relation_id693}
	return _t1298
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs694 := []*pb.Read{}
	cond695 := p.matchLookaheadLiteral("(", 0)
	for cond695 {
		_t1299 := p.parse_read()
		item696 := _t1299
		xs694 = append(xs694, item696)
		cond695 = p.matchLookaheadLiteral("(", 0)
	}
	reads697 := xs694
	p.consumeLiteral(")")
	return reads697
}

func (p *Parser) parse_read() *pb.Read {
	var _t1300 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1301 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1301 = 2
		} else {
			var _t1302 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1302 = 1
			} else {
				var _t1303 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1303 = 4
				} else {
					var _t1304 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1304 = 0
					} else {
						var _t1305 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1305 = 3
						} else {
							_t1305 = -1
						}
						_t1304 = _t1305
					}
					_t1303 = _t1304
				}
				_t1302 = _t1303
			}
			_t1301 = _t1302
		}
		_t1300 = _t1301
	} else {
		_t1300 = -1
	}
	prediction698 := _t1300
	var _t1306 *pb.Read
	if prediction698 == 4 {
		_t1307 := p.parse_export()
		export703 := _t1307
		_t1308 := &pb.Read{}
		_t1308.ReadType = &pb.Read_Export{Export: export703}
		_t1306 = _t1308
	} else {
		var _t1309 *pb.Read
		if prediction698 == 3 {
			_t1310 := p.parse_abort()
			abort702 := _t1310
			_t1311 := &pb.Read{}
			_t1311.ReadType = &pb.Read_Abort{Abort: abort702}
			_t1309 = _t1311
		} else {
			var _t1312 *pb.Read
			if prediction698 == 2 {
				_t1313 := p.parse_what_if()
				what_if701 := _t1313
				_t1314 := &pb.Read{}
				_t1314.ReadType = &pb.Read_WhatIf{WhatIf: what_if701}
				_t1312 = _t1314
			} else {
				var _t1315 *pb.Read
				if prediction698 == 1 {
					_t1316 := p.parse_output()
					output700 := _t1316
					_t1317 := &pb.Read{}
					_t1317.ReadType = &pb.Read_Output{Output: output700}
					_t1315 = _t1317
				} else {
					var _t1318 *pb.Read
					if prediction698 == 0 {
						_t1319 := p.parse_demand()
						demand699 := _t1319
						_t1320 := &pb.Read{}
						_t1320.ReadType = &pb.Read_Demand{Demand: demand699}
						_t1318 = _t1320
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1315 = _t1318
				}
				_t1312 = _t1315
			}
			_t1309 = _t1312
		}
		_t1306 = _t1309
	}
	return _t1306
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1321 := p.parse_relation_id()
	relation_id704 := _t1321
	p.consumeLiteral(")")
	_t1322 := &pb.Demand{RelationId: relation_id704}
	return _t1322
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1323 := p.parse_name()
	name705 := _t1323
	_t1324 := p.parse_relation_id()
	relation_id706 := _t1324
	p.consumeLiteral(")")
	_t1325 := &pb.Output{Name: name705, RelationId: relation_id706}
	return _t1325
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1326 := p.parse_name()
	name707 := _t1326
	_t1327 := p.parse_epoch()
	epoch708 := _t1327
	p.consumeLiteral(")")
	_t1328 := &pb.WhatIf{Branch: name707, Epoch: epoch708}
	return _t1328
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1329 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1330 := p.parse_name()
		_t1329 = ptr(_t1330)
	}
	name709 := _t1329
	_t1331 := p.parse_relation_id()
	relation_id710 := _t1331
	p.consumeLiteral(")")
	_t1332 := &pb.Abort{Name: deref(name709, "abort"), RelationId: relation_id710}
	return _t1332
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1333 := p.parse_export_csv_config()
	export_csv_config711 := _t1333
	p.consumeLiteral(")")
	_t1334 := &pb.Export{}
	_t1334.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config711}
	return _t1334
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	var _t1335 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1336 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1336 = 0
		} else {
			var _t1337 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1337 = 1
			} else {
				_t1337 = -1
			}
			_t1336 = _t1337
		}
		_t1335 = _t1336
	} else {
		_t1335 = -1
	}
	prediction712 := _t1335
	var _t1338 *pb.ExportCSVConfig
	if prediction712 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1339 := p.parse_export_csv_path()
		export_csv_path716 := _t1339
		_t1340 := p.parse_export_csv_columns_list()
		export_csv_columns_list717 := _t1340
		_t1341 := p.parse_config_dict()
		config_dict718 := _t1341
		p.consumeLiteral(")")
		_t1342 := p.construct_export_csv_config(export_csv_path716, export_csv_columns_list717, config_dict718)
		_t1338 = _t1342
	} else {
		var _t1343 *pb.ExportCSVConfig
		if prediction712 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1344 := p.parse_export_csv_path()
			export_csv_path713 := _t1344
			_t1345 := p.parse_export_csv_source()
			export_csv_source714 := _t1345
			_t1346 := p.parse_csv_config()
			csv_config715 := _t1346
			p.consumeLiteral(")")
			_t1347 := p.construct_export_csv_config_with_source(export_csv_path713, export_csv_source714, csv_config715)
			_t1343 = _t1347
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1338 = _t1343
	}
	return _t1338
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string719 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string719
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	var _t1348 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1349 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1349 = 1
		} else {
			var _t1350 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1350 = 0
			} else {
				_t1350 = -1
			}
			_t1349 = _t1350
		}
		_t1348 = _t1349
	} else {
		_t1348 = -1
	}
	prediction720 := _t1348
	var _t1351 *pb.ExportCSVSource
	if prediction720 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1352 := p.parse_relation_id()
		relation_id725 := _t1352
		p.consumeLiteral(")")
		_t1353 := &pb.ExportCSVSource{}
		_t1353.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id725}
		_t1351 = _t1353
	} else {
		var _t1354 *pb.ExportCSVSource
		if prediction720 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs721 := []*pb.ExportCSVColumn{}
			cond722 := p.matchLookaheadLiteral("(", 0)
			for cond722 {
				_t1355 := p.parse_export_csv_column()
				item723 := _t1355
				xs721 = append(xs721, item723)
				cond722 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns724 := xs721
			p.consumeLiteral(")")
			_t1356 := &pb.ExportCSVColumns{Columns: export_csv_columns724}
			_t1357 := &pb.ExportCSVSource{}
			_t1357.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1356}
			_t1354 = _t1357
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1351 = _t1354
	}
	return _t1351
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string726 := p.consumeTerminal("STRING").Value.str
	_t1358 := p.parse_relation_id()
	relation_id727 := _t1358
	p.consumeLiteral(")")
	_t1359 := &pb.ExportCSVColumn{ColumnName: string726, ColumnData: relation_id727}
	return _t1359
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs728 := []*pb.ExportCSVColumn{}
	cond729 := p.matchLookaheadLiteral("(", 0)
	for cond729 {
		_t1360 := p.parse_export_csv_column()
		item730 := _t1360
		xs728 = append(xs728, item730)
		cond729 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns731 := xs728
	p.consumeLiteral(")")
	return export_csv_columns731
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
