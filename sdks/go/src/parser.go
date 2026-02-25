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
	var _t1340 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1340
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1341 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1341
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1342 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1342
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1343 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1343
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1344 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1344
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1345 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1345
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1346 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1346
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1347 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1347
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1348 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1348
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1349 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1349
	_t1350 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1350
	_t1351 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1351
	_t1352 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1352
	_t1353 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1353
	_t1354 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1354
	_t1355 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1355
	_t1356 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1356
	_t1357 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1357
	_t1358 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1358
	_t1359 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1359
	_t1360 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1360
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1361 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1361
	_t1362 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1362
	_t1363 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1363
	_t1364 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1364
	_t1365 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1365
	_t1366 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1366
	_t1367 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1367
	_t1368 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1368
	_t1369 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1369
	_t1370 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1370.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1370.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1370
	_t1371 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1371
}

func (p *Parser) default_configure() *pb.Configure {
	_t1372 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1372
	_t1373 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1373
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
	_t1374 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1374
	_t1375 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1375
	_t1376 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1376
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1377 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1377
	_t1378 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1378
	_t1379 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1379
	_t1380 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1380
	_t1381 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1381
	_t1382 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1382
	_t1383 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1383
	_t1384 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1384
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t724 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t725 := p.parse_configure()
		_t724 = _t725
	}
	configure362 := _t724
	var _t726 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t727 := p.parse_sync()
		_t726 = _t727
	}
	sync363 := _t726
	xs364 := []*pb.Epoch{}
	cond365 := p.matchLookaheadLiteral("(", 0)
	for cond365 {
		_t728 := p.parse_epoch()
		item366 := _t728
		xs364 = append(xs364, item366)
		cond365 = p.matchLookaheadLiteral("(", 0)
	}
	epochs367 := xs364
	p.consumeLiteral(")")
	_t729 := p.default_configure()
	_t730 := configure362
	if configure362 == nil {
		_t730 = _t729
	}
	_t731 := &pb.Transaction{Epochs: epochs367, Configure: _t730, Sync: sync363}
	return _t731
}

func (p *Parser) parse_configure() *pb.Configure {
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t732 := p.parse_config_dict()
	config_dict368 := _t732
	p.consumeLiteral(")")
	_t733 := p.construct_configure(config_dict368)
	return _t733
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs369 := [][]interface{}{}
	cond370 := p.matchLookaheadLiteral(":", 0)
	for cond370 {
		_t734 := p.parse_config_key_value()
		item371 := _t734
		xs369 = append(xs369, item371)
		cond370 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values372 := xs369
	p.consumeLiteral("}")
	return config_key_values372
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol373 := p.consumeTerminal("SYMBOL").Value.str
	_t735 := p.parse_value()
	value374 := _t735
	return []interface{}{symbol373, value374}
}

func (p *Parser) parse_value() *pb.Value {
	var _t736 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t736 = 9
	} else {
		var _t737 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t737 = 8
		} else {
			var _t738 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t738 = 9
			} else {
				var _t739 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t740 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t740 = 1
					} else {
						var _t741 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t741 = 0
						} else {
							_t741 = -1
						}
						_t740 = _t741
					}
					_t739 = _t740
				} else {
					var _t742 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t742 = 5
					} else {
						var _t743 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t743 = 2
						} else {
							var _t744 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t744 = 6
							} else {
								var _t745 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t745 = 3
								} else {
									var _t746 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t746 = 4
									} else {
										var _t747 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t747 = 7
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
					_t739 = _t742
				}
				_t738 = _t739
			}
			_t737 = _t738
		}
		_t736 = _t737
	}
	prediction375 := _t736
	var _t748 *pb.Value
	if prediction375 == 9 {
		_t749 := p.parse_boolean_value()
		boolean_value384 := _t749
		_t750 := &pb.Value{}
		_t750.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value384}
		_t748 = _t750
	} else {
		var _t751 *pb.Value
		if prediction375 == 8 {
			p.consumeLiteral("missing")
			_t752 := &pb.MissingValue{}
			_t753 := &pb.Value{}
			_t753.Value = &pb.Value_MissingValue{MissingValue: _t752}
			_t751 = _t753
		} else {
			var _t754 *pb.Value
			if prediction375 == 7 {
				decimal383 := p.consumeTerminal("DECIMAL").Value.decimal
				_t755 := &pb.Value{}
				_t755.Value = &pb.Value_DecimalValue{DecimalValue: decimal383}
				_t754 = _t755
			} else {
				var _t756 *pb.Value
				if prediction375 == 6 {
					int128382 := p.consumeTerminal("INT128").Value.int128
					_t757 := &pb.Value{}
					_t757.Value = &pb.Value_Int128Value{Int128Value: int128382}
					_t756 = _t757
				} else {
					var _t758 *pb.Value
					if prediction375 == 5 {
						uint128381 := p.consumeTerminal("UINT128").Value.uint128
						_t759 := &pb.Value{}
						_t759.Value = &pb.Value_Uint128Value{Uint128Value: uint128381}
						_t758 = _t759
					} else {
						var _t760 *pb.Value
						if prediction375 == 4 {
							float380 := p.consumeTerminal("FLOAT").Value.f64
							_t761 := &pb.Value{}
							_t761.Value = &pb.Value_FloatValue{FloatValue: float380}
							_t760 = _t761
						} else {
							var _t762 *pb.Value
							if prediction375 == 3 {
								int379 := p.consumeTerminal("INT").Value.i64
								_t763 := &pb.Value{}
								_t763.Value = &pb.Value_IntValue{IntValue: int379}
								_t762 = _t763
							} else {
								var _t764 *pb.Value
								if prediction375 == 2 {
									string378 := p.consumeTerminal("STRING").Value.str
									_t765 := &pb.Value{}
									_t765.Value = &pb.Value_StringValue{StringValue: string378}
									_t764 = _t765
								} else {
									var _t766 *pb.Value
									if prediction375 == 1 {
										_t767 := p.parse_datetime()
										datetime377 := _t767
										_t768 := &pb.Value{}
										_t768.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime377}
										_t766 = _t768
									} else {
										var _t769 *pb.Value
										if prediction375 == 0 {
											_t770 := p.parse_date()
											date376 := _t770
											_t771 := &pb.Value{}
											_t771.Value = &pb.Value_DateValue{DateValue: date376}
											_t769 = _t771
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t766 = _t769
									}
									_t764 = _t766
								}
								_t762 = _t764
							}
							_t760 = _t762
						}
						_t758 = _t760
					}
					_t756 = _t758
				}
				_t754 = _t756
			}
			_t751 = _t754
		}
		_t748 = _t751
	}
	return _t748
}

func (p *Parser) parse_date() *pb.DateValue {
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int385 := p.consumeTerminal("INT").Value.i64
	int_3386 := p.consumeTerminal("INT").Value.i64
	int_4387 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t772 := &pb.DateValue{Year: int32(int385), Month: int32(int_3386), Day: int32(int_4387)}
	return _t772
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int388 := p.consumeTerminal("INT").Value.i64
	int_3389 := p.consumeTerminal("INT").Value.i64
	int_4390 := p.consumeTerminal("INT").Value.i64
	int_5391 := p.consumeTerminal("INT").Value.i64
	int_6392 := p.consumeTerminal("INT").Value.i64
	int_7393 := p.consumeTerminal("INT").Value.i64
	var _t773 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t773 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8394 := _t773
	p.consumeLiteral(")")
	_t774 := &pb.DateTimeValue{Year: int32(int388), Month: int32(int_3389), Day: int32(int_4390), Hour: int32(int_5391), Minute: int32(int_6392), Second: int32(int_7393), Microsecond: int32(deref(int_8394, 0))}
	return _t774
}

func (p *Parser) parse_boolean_value() bool {
	var _t775 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t775 = 0
	} else {
		var _t776 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t776 = 1
		} else {
			_t776 = -1
		}
		_t775 = _t776
	}
	prediction395 := _t775
	var _t777 bool
	if prediction395 == 1 {
		p.consumeLiteral("false")
		_t777 = false
	} else {
		var _t778 bool
		if prediction395 == 0 {
			p.consumeLiteral("true")
			_t778 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t777 = _t778
	}
	return _t777
}

func (p *Parser) parse_sync() *pb.Sync {
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs396 := []*pb.FragmentId{}
	cond397 := p.matchLookaheadLiteral(":", 0)
	for cond397 {
		_t779 := p.parse_fragment_id()
		item398 := _t779
		xs396 = append(xs396, item398)
		cond397 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids399 := xs396
	p.consumeLiteral(")")
	_t780 := &pb.Sync{Fragments: fragment_ids399}
	return _t780
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	p.consumeLiteral(":")
	symbol400 := p.consumeTerminal("SYMBOL").Value.str
	return &pb.FragmentId{Id: []byte(symbol400)}
}

func (p *Parser) parse_epoch() *pb.Epoch {
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t781 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t782 := p.parse_epoch_writes()
		_t781 = _t782
	}
	epoch_writes401 := _t781
	var _t783 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t784 := p.parse_epoch_reads()
		_t783 = _t784
	}
	epoch_reads402 := _t783
	p.consumeLiteral(")")
	_t785 := epoch_writes401
	if epoch_writes401 == nil {
		_t785 = []*pb.Write{}
	}
	_t786 := epoch_reads402
	if epoch_reads402 == nil {
		_t786 = []*pb.Read{}
	}
	_t787 := &pb.Epoch{Writes: _t785, Reads: _t786}
	return _t787
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs403 := []*pb.Write{}
	cond404 := p.matchLookaheadLiteral("(", 0)
	for cond404 {
		_t788 := p.parse_write()
		item405 := _t788
		xs403 = append(xs403, item405)
		cond404 = p.matchLookaheadLiteral("(", 0)
	}
	writes406 := xs403
	p.consumeLiteral(")")
	return writes406
}

func (p *Parser) parse_write() *pb.Write {
	var _t789 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t790 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t790 = 1
		} else {
			var _t791 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t791 = 3
			} else {
				var _t792 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t792 = 0
				} else {
					var _t793 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t793 = 2
					} else {
						_t793 = -1
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
	prediction407 := _t789
	var _t794 *pb.Write
	if prediction407 == 3 {
		_t795 := p.parse_snapshot()
		snapshot411 := _t795
		_t796 := &pb.Write{}
		_t796.WriteType = &pb.Write_Snapshot{Snapshot: snapshot411}
		_t794 = _t796
	} else {
		var _t797 *pb.Write
		if prediction407 == 2 {
			_t798 := p.parse_context()
			context410 := _t798
			_t799 := &pb.Write{}
			_t799.WriteType = &pb.Write_Context{Context: context410}
			_t797 = _t799
		} else {
			var _t800 *pb.Write
			if prediction407 == 1 {
				_t801 := p.parse_undefine()
				undefine409 := _t801
				_t802 := &pb.Write{}
				_t802.WriteType = &pb.Write_Undefine{Undefine: undefine409}
				_t800 = _t802
			} else {
				var _t803 *pb.Write
				if prediction407 == 0 {
					_t804 := p.parse_define()
					define408 := _t804
					_t805 := &pb.Write{}
					_t805.WriteType = &pb.Write_Define{Define: define408}
					_t803 = _t805
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t800 = _t803
			}
			_t797 = _t800
		}
		_t794 = _t797
	}
	return _t794
}

func (p *Parser) parse_define() *pb.Define {
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t806 := p.parse_fragment()
	fragment412 := _t806
	p.consumeLiteral(")")
	_t807 := &pb.Define{Fragment: fragment412}
	return _t807
}

func (p *Parser) parse_fragment() *pb.Fragment {
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t808 := p.parse_new_fragment_id()
	new_fragment_id413 := _t808
	xs414 := []*pb.Declaration{}
	cond415 := p.matchLookaheadLiteral("(", 0)
	for cond415 {
		_t809 := p.parse_declaration()
		item416 := _t809
		xs414 = append(xs414, item416)
		cond415 = p.matchLookaheadLiteral("(", 0)
	}
	declarations417 := xs414
	p.consumeLiteral(")")
	return p.constructFragment(new_fragment_id413, declarations417)
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	_t810 := p.parse_fragment_id()
	fragment_id418 := _t810
	p.startFragment(fragment_id418)
	return fragment_id418
}

func (p *Parser) parse_declaration() *pb.Declaration {
	var _t811 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t812 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t812 = 2
		} else {
			var _t813 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t813 = 3
			} else {
				var _t814 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t814 = 0
				} else {
					var _t815 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t815 = 3
					} else {
						var _t816 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t816 = 3
						} else {
							var _t817 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t817 = 1
							} else {
								_t817 = -1
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
		_t811 = _t812
	} else {
		_t811 = -1
	}
	prediction419 := _t811
	var _t818 *pb.Declaration
	if prediction419 == 3 {
		_t819 := p.parse_data()
		data423 := _t819
		_t820 := &pb.Declaration{}
		_t820.DeclarationType = &pb.Declaration_Data{Data: data423}
		_t818 = _t820
	} else {
		var _t821 *pb.Declaration
		if prediction419 == 2 {
			_t822 := p.parse_constraint()
			constraint422 := _t822
			_t823 := &pb.Declaration{}
			_t823.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint422}
			_t821 = _t823
		} else {
			var _t824 *pb.Declaration
			if prediction419 == 1 {
				_t825 := p.parse_algorithm()
				algorithm421 := _t825
				_t826 := &pb.Declaration{}
				_t826.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm421}
				_t824 = _t826
			} else {
				var _t827 *pb.Declaration
				if prediction419 == 0 {
					_t828 := p.parse_def()
					def420 := _t828
					_t829 := &pb.Declaration{}
					_t829.DeclarationType = &pb.Declaration_Def{Def: def420}
					_t827 = _t829
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t824 = _t827
			}
			_t821 = _t824
		}
		_t818 = _t821
	}
	return _t818
}

func (p *Parser) parse_def() *pb.Def {
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t830 := p.parse_relation_id()
	relation_id424 := _t830
	_t831 := p.parse_abstraction()
	abstraction425 := _t831
	var _t832 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t833 := p.parse_attrs()
		_t832 = _t833
	}
	attrs426 := _t832
	p.consumeLiteral(")")
	_t834 := attrs426
	if attrs426 == nil {
		_t834 = []*pb.Attribute{}
	}
	_t835 := &pb.Def{Name: relation_id424, Body: abstraction425, Attrs: _t834}
	return _t835
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	var _t836 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t836 = 0
	} else {
		var _t837 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t837 = 1
		} else {
			_t837 = -1
		}
		_t836 = _t837
	}
	prediction427 := _t836
	var _t838 *pb.RelationId
	if prediction427 == 1 {
		uint128429 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128429
		_t838 = &pb.RelationId{IdLow: uint128429.Low, IdHigh: uint128429.High}
	} else {
		var _t839 *pb.RelationId
		if prediction427 == 0 {
			p.consumeLiteral(":")
			symbol428 := p.consumeTerminal("SYMBOL").Value.str
			_t839 = p.relationIdFromString(symbol428)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t838 = _t839
	}
	return _t838
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	p.consumeLiteral("(")
	_t840 := p.parse_bindings()
	bindings430 := _t840
	_t841 := p.parse_formula()
	formula431 := _t841
	p.consumeLiteral(")")
	_t842 := &pb.Abstraction{Vars: listConcat(bindings430[0].([]*pb.Binding), bindings430[1].([]*pb.Binding)), Value: formula431}
	return _t842
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs432 := []*pb.Binding{}
	cond433 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond433 {
		_t843 := p.parse_binding()
		item434 := _t843
		xs432 = append(xs432, item434)
		cond433 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings435 := xs432
	var _t844 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t845 := p.parse_value_bindings()
		_t844 = _t845
	}
	value_bindings436 := _t844
	p.consumeLiteral("]")
	_t846 := value_bindings436
	if value_bindings436 == nil {
		_t846 = []*pb.Binding{}
	}
	return []interface{}{bindings435, _t846}
}

func (p *Parser) parse_binding() *pb.Binding {
	symbol437 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t847 := p.parse_type()
	type438 := _t847
	_t848 := &pb.Var{Name: symbol437}
	_t849 := &pb.Binding{Var: _t848, Type: type438}
	return _t849
}

func (p *Parser) parse_type() *pb.Type {
	var _t850 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t850 = 0
	} else {
		var _t851 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t851 = 4
		} else {
			var _t852 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t852 = 1
			} else {
				var _t853 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t853 = 8
				} else {
					var _t854 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t854 = 5
					} else {
						var _t855 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t855 = 2
						} else {
							var _t856 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t856 = 3
							} else {
								var _t857 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t857 = 7
								} else {
									var _t858 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t858 = 6
									} else {
										var _t859 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t859 = 10
										} else {
											var _t860 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t860 = 9
											} else {
												_t860 = -1
											}
											_t859 = _t860
										}
										_t858 = _t859
									}
									_t857 = _t858
								}
								_t856 = _t857
							}
							_t855 = _t856
						}
						_t854 = _t855
					}
					_t853 = _t854
				}
				_t852 = _t853
			}
			_t851 = _t852
		}
		_t850 = _t851
	}
	prediction439 := _t850
	var _t861 *pb.Type
	if prediction439 == 10 {
		_t862 := p.parse_boolean_type()
		boolean_type450 := _t862
		_t863 := &pb.Type{}
		_t863.Type = &pb.Type_BooleanType{BooleanType: boolean_type450}
		_t861 = _t863
	} else {
		var _t864 *pb.Type
		if prediction439 == 9 {
			_t865 := p.parse_decimal_type()
			decimal_type449 := _t865
			_t866 := &pb.Type{}
			_t866.Type = &pb.Type_DecimalType{DecimalType: decimal_type449}
			_t864 = _t866
		} else {
			var _t867 *pb.Type
			if prediction439 == 8 {
				_t868 := p.parse_missing_type()
				missing_type448 := _t868
				_t869 := &pb.Type{}
				_t869.Type = &pb.Type_MissingType{MissingType: missing_type448}
				_t867 = _t869
			} else {
				var _t870 *pb.Type
				if prediction439 == 7 {
					_t871 := p.parse_datetime_type()
					datetime_type447 := _t871
					_t872 := &pb.Type{}
					_t872.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type447}
					_t870 = _t872
				} else {
					var _t873 *pb.Type
					if prediction439 == 6 {
						_t874 := p.parse_date_type()
						date_type446 := _t874
						_t875 := &pb.Type{}
						_t875.Type = &pb.Type_DateType{DateType: date_type446}
						_t873 = _t875
					} else {
						var _t876 *pb.Type
						if prediction439 == 5 {
							_t877 := p.parse_int128_type()
							int128_type445 := _t877
							_t878 := &pb.Type{}
							_t878.Type = &pb.Type_Int128Type{Int128Type: int128_type445}
							_t876 = _t878
						} else {
							var _t879 *pb.Type
							if prediction439 == 4 {
								_t880 := p.parse_uint128_type()
								uint128_type444 := _t880
								_t881 := &pb.Type{}
								_t881.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type444}
								_t879 = _t881
							} else {
								var _t882 *pb.Type
								if prediction439 == 3 {
									_t883 := p.parse_float_type()
									float_type443 := _t883
									_t884 := &pb.Type{}
									_t884.Type = &pb.Type_FloatType{FloatType: float_type443}
									_t882 = _t884
								} else {
									var _t885 *pb.Type
									if prediction439 == 2 {
										_t886 := p.parse_int_type()
										int_type442 := _t886
										_t887 := &pb.Type{}
										_t887.Type = &pb.Type_IntType{IntType: int_type442}
										_t885 = _t887
									} else {
										var _t888 *pb.Type
										if prediction439 == 1 {
											_t889 := p.parse_string_type()
											string_type441 := _t889
											_t890 := &pb.Type{}
											_t890.Type = &pb.Type_StringType{StringType: string_type441}
											_t888 = _t890
										} else {
											var _t891 *pb.Type
											if prediction439 == 0 {
												_t892 := p.parse_unspecified_type()
												unspecified_type440 := _t892
												_t893 := &pb.Type{}
												_t893.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type440}
												_t891 = _t893
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t870 = _t873
				}
				_t867 = _t870
			}
			_t864 = _t867
		}
		_t861 = _t864
	}
	return _t861
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	p.consumeLiteral("UNKNOWN")
	_t894 := &pb.UnspecifiedType{}
	return _t894
}

func (p *Parser) parse_string_type() *pb.StringType {
	p.consumeLiteral("STRING")
	_t895 := &pb.StringType{}
	return _t895
}

func (p *Parser) parse_int_type() *pb.IntType {
	p.consumeLiteral("INT")
	_t896 := &pb.IntType{}
	return _t896
}

func (p *Parser) parse_float_type() *pb.FloatType {
	p.consumeLiteral("FLOAT")
	_t897 := &pb.FloatType{}
	return _t897
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	p.consumeLiteral("UINT128")
	_t898 := &pb.UInt128Type{}
	return _t898
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	p.consumeLiteral("INT128")
	_t899 := &pb.Int128Type{}
	return _t899
}

func (p *Parser) parse_date_type() *pb.DateType {
	p.consumeLiteral("DATE")
	_t900 := &pb.DateType{}
	return _t900
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	p.consumeLiteral("DATETIME")
	_t901 := &pb.DateTimeType{}
	return _t901
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	p.consumeLiteral("MISSING")
	_t902 := &pb.MissingType{}
	return _t902
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int451 := p.consumeTerminal("INT").Value.i64
	int_3452 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t903 := &pb.DecimalType{Precision: int32(int451), Scale: int32(int_3452)}
	return _t903
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	p.consumeLiteral("BOOLEAN")
	_t904 := &pb.BooleanType{}
	return _t904
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs453 := []*pb.Binding{}
	cond454 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond454 {
		_t905 := p.parse_binding()
		item455 := _t905
		xs453 = append(xs453, item455)
		cond454 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings456 := xs453
	return bindings456
}

func (p *Parser) parse_formula() *pb.Formula {
	var _t906 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t907 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t907 = 0
		} else {
			var _t908 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t908 = 11
			} else {
				var _t909 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t909 = 3
				} else {
					var _t910 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t910 = 10
					} else {
						var _t911 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t911 = 9
						} else {
							var _t912 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t912 = 5
							} else {
								var _t913 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t913 = 6
								} else {
									var _t914 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t914 = 7
									} else {
										var _t915 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t915 = 1
										} else {
											var _t916 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t916 = 2
											} else {
												var _t917 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t917 = 12
												} else {
													var _t918 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t918 = 8
													} else {
														var _t919 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t919 = 4
														} else {
															var _t920 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t920 = 10
															} else {
																var _t921 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t921 = 10
																} else {
																	var _t922 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t922 = 10
																	} else {
																		var _t923 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t923 = 10
																		} else {
																			var _t924 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t924 = 10
																			} else {
																				var _t925 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t925 = 10
																				} else {
																					var _t926 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t926 = 10
																					} else {
																						var _t927 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t927 = 10
																						} else {
																							var _t928 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t928 = 10
																							} else {
																								_t928 = -1
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
	} else {
		_t906 = -1
	}
	prediction457 := _t906
	var _t929 *pb.Formula
	if prediction457 == 12 {
		_t930 := p.parse_cast()
		cast470 := _t930
		_t931 := &pb.Formula{}
		_t931.FormulaType = &pb.Formula_Cast{Cast: cast470}
		_t929 = _t931
	} else {
		var _t932 *pb.Formula
		if prediction457 == 11 {
			_t933 := p.parse_rel_atom()
			rel_atom469 := _t933
			_t934 := &pb.Formula{}
			_t934.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom469}
			_t932 = _t934
		} else {
			var _t935 *pb.Formula
			if prediction457 == 10 {
				_t936 := p.parse_primitive()
				primitive468 := _t936
				_t937 := &pb.Formula{}
				_t937.FormulaType = &pb.Formula_Primitive{Primitive: primitive468}
				_t935 = _t937
			} else {
				var _t938 *pb.Formula
				if prediction457 == 9 {
					_t939 := p.parse_pragma()
					pragma467 := _t939
					_t940 := &pb.Formula{}
					_t940.FormulaType = &pb.Formula_Pragma{Pragma: pragma467}
					_t938 = _t940
				} else {
					var _t941 *pb.Formula
					if prediction457 == 8 {
						_t942 := p.parse_atom()
						atom466 := _t942
						_t943 := &pb.Formula{}
						_t943.FormulaType = &pb.Formula_Atom{Atom: atom466}
						_t941 = _t943
					} else {
						var _t944 *pb.Formula
						if prediction457 == 7 {
							_t945 := p.parse_ffi()
							ffi465 := _t945
							_t946 := &pb.Formula{}
							_t946.FormulaType = &pb.Formula_Ffi{Ffi: ffi465}
							_t944 = _t946
						} else {
							var _t947 *pb.Formula
							if prediction457 == 6 {
								_t948 := p.parse_not()
								not464 := _t948
								_t949 := &pb.Formula{}
								_t949.FormulaType = &pb.Formula_Not{Not: not464}
								_t947 = _t949
							} else {
								var _t950 *pb.Formula
								if prediction457 == 5 {
									_t951 := p.parse_disjunction()
									disjunction463 := _t951
									_t952 := &pb.Formula{}
									_t952.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction463}
									_t950 = _t952
								} else {
									var _t953 *pb.Formula
									if prediction457 == 4 {
										_t954 := p.parse_conjunction()
										conjunction462 := _t954
										_t955 := &pb.Formula{}
										_t955.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction462}
										_t953 = _t955
									} else {
										var _t956 *pb.Formula
										if prediction457 == 3 {
											_t957 := p.parse_reduce()
											reduce461 := _t957
											_t958 := &pb.Formula{}
											_t958.FormulaType = &pb.Formula_Reduce{Reduce: reduce461}
											_t956 = _t958
										} else {
											var _t959 *pb.Formula
											if prediction457 == 2 {
												_t960 := p.parse_exists()
												exists460 := _t960
												_t961 := &pb.Formula{}
												_t961.FormulaType = &pb.Formula_Exists{Exists: exists460}
												_t959 = _t961
											} else {
												var _t962 *pb.Formula
												if prediction457 == 1 {
													_t963 := p.parse_false()
													false459 := _t963
													_t964 := &pb.Formula{}
													_t964.FormulaType = &pb.Formula_Disjunction{Disjunction: false459}
													_t962 = _t964
												} else {
													var _t965 *pb.Formula
													if prediction457 == 0 {
														_t966 := p.parse_true()
														true458 := _t966
														_t967 := &pb.Formula{}
														_t967.FormulaType = &pb.Formula_Conjunction{Conjunction: true458}
														_t965 = _t967
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
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
					_t938 = _t941
				}
				_t935 = _t938
			}
			_t932 = _t935
		}
		_t929 = _t932
	}
	return _t929
}

func (p *Parser) parse_true() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t968 := &pb.Conjunction{Args: []*pb.Formula{}}
	return _t968
}

func (p *Parser) parse_false() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t969 := &pb.Disjunction{Args: []*pb.Formula{}}
	return _t969
}

func (p *Parser) parse_exists() *pb.Exists {
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t970 := p.parse_bindings()
	bindings471 := _t970
	_t971 := p.parse_formula()
	formula472 := _t971
	p.consumeLiteral(")")
	_t972 := &pb.Abstraction{Vars: listConcat(bindings471[0].([]*pb.Binding), bindings471[1].([]*pb.Binding)), Value: formula472}
	_t973 := &pb.Exists{Body: _t972}
	return _t973
}

func (p *Parser) parse_reduce() *pb.Reduce {
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t974 := p.parse_abstraction()
	abstraction473 := _t974
	_t975 := p.parse_abstraction()
	abstraction_3474 := _t975
	_t976 := p.parse_terms()
	terms475 := _t976
	p.consumeLiteral(")")
	_t977 := &pb.Reduce{Op: abstraction473, Body: abstraction_3474, Terms: terms475}
	return _t977
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs476 := []*pb.Term{}
	cond477 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond477 {
		_t978 := p.parse_term()
		item478 := _t978
		xs476 = append(xs476, item478)
		cond477 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms479 := xs476
	p.consumeLiteral(")")
	return terms479
}

func (p *Parser) parse_term() *pb.Term {
	var _t979 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t979 = 1
	} else {
		var _t980 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t980 = 1
		} else {
			var _t981 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t981 = 1
			} else {
				var _t982 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t982 = 1
				} else {
					var _t983 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t983 = 1
					} else {
						var _t984 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t984 = 0
						} else {
							var _t985 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t985 = 1
							} else {
								var _t986 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t986 = 1
								} else {
									var _t987 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t987 = 1
									} else {
										var _t988 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t988 = 1
										} else {
											var _t989 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t989 = 1
											} else {
												_t989 = -1
											}
											_t988 = _t989
										}
										_t987 = _t988
									}
									_t986 = _t987
								}
								_t985 = _t986
							}
							_t984 = _t985
						}
						_t983 = _t984
					}
					_t982 = _t983
				}
				_t981 = _t982
			}
			_t980 = _t981
		}
		_t979 = _t980
	}
	prediction480 := _t979
	var _t990 *pb.Term
	if prediction480 == 1 {
		_t991 := p.parse_constant()
		constant482 := _t991
		_t992 := &pb.Term{}
		_t992.TermType = &pb.Term_Constant{Constant: constant482}
		_t990 = _t992
	} else {
		var _t993 *pb.Term
		if prediction480 == 0 {
			_t994 := p.parse_var()
			var481 := _t994
			_t995 := &pb.Term{}
			_t995.TermType = &pb.Term_Var{Var: var481}
			_t993 = _t995
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t990 = _t993
	}
	return _t990
}

func (p *Parser) parse_var() *pb.Var {
	symbol483 := p.consumeTerminal("SYMBOL").Value.str
	_t996 := &pb.Var{Name: symbol483}
	return _t996
}

func (p *Parser) parse_constant() *pb.Value {
	_t997 := p.parse_value()
	value484 := _t997
	return value484
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs485 := []*pb.Formula{}
	cond486 := p.matchLookaheadLiteral("(", 0)
	for cond486 {
		_t998 := p.parse_formula()
		item487 := _t998
		xs485 = append(xs485, item487)
		cond486 = p.matchLookaheadLiteral("(", 0)
	}
	formulas488 := xs485
	p.consumeLiteral(")")
	_t999 := &pb.Conjunction{Args: formulas488}
	return _t999
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs489 := []*pb.Formula{}
	cond490 := p.matchLookaheadLiteral("(", 0)
	for cond490 {
		_t1000 := p.parse_formula()
		item491 := _t1000
		xs489 = append(xs489, item491)
		cond490 = p.matchLookaheadLiteral("(", 0)
	}
	formulas492 := xs489
	p.consumeLiteral(")")
	_t1001 := &pb.Disjunction{Args: formulas492}
	return _t1001
}

func (p *Parser) parse_not() *pb.Not {
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1002 := p.parse_formula()
	formula493 := _t1002
	p.consumeLiteral(")")
	_t1003 := &pb.Not{Arg: formula493}
	return _t1003
}

func (p *Parser) parse_ffi() *pb.FFI {
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1004 := p.parse_name()
	name494 := _t1004
	_t1005 := p.parse_ffi_args()
	ffi_args495 := _t1005
	_t1006 := p.parse_terms()
	terms496 := _t1006
	p.consumeLiteral(")")
	_t1007 := &pb.FFI{Name: name494, Args: ffi_args495, Terms: terms496}
	return _t1007
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol497 := p.consumeTerminal("SYMBOL").Value.str
	return symbol497
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs498 := []*pb.Abstraction{}
	cond499 := p.matchLookaheadLiteral("(", 0)
	for cond499 {
		_t1008 := p.parse_abstraction()
		item500 := _t1008
		xs498 = append(xs498, item500)
		cond499 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions501 := xs498
	p.consumeLiteral(")")
	return abstractions501
}

func (p *Parser) parse_atom() *pb.Atom {
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1009 := p.parse_relation_id()
	relation_id502 := _t1009
	xs503 := []*pb.Term{}
	cond504 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond504 {
		_t1010 := p.parse_term()
		item505 := _t1010
		xs503 = append(xs503, item505)
		cond504 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms506 := xs503
	p.consumeLiteral(")")
	_t1011 := &pb.Atom{Name: relation_id502, Terms: terms506}
	return _t1011
}

func (p *Parser) parse_pragma() *pb.Pragma {
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1012 := p.parse_name()
	name507 := _t1012
	xs508 := []*pb.Term{}
	cond509 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond509 {
		_t1013 := p.parse_term()
		item510 := _t1013
		xs508 = append(xs508, item510)
		cond509 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms511 := xs508
	p.consumeLiteral(")")
	_t1014 := &pb.Pragma{Name: name507, Terms: terms511}
	return _t1014
}

func (p *Parser) parse_primitive() *pb.Primitive {
	var _t1015 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1016 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1016 = 9
		} else {
			var _t1017 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1017 = 4
			} else {
				var _t1018 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1018 = 3
				} else {
					var _t1019 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1019 = 0
					} else {
						var _t1020 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1020 = 2
						} else {
							var _t1021 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1021 = 1
							} else {
								var _t1022 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1022 = 8
								} else {
									var _t1023 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1023 = 6
									} else {
										var _t1024 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1024 = 5
										} else {
											var _t1025 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1025 = 7
											} else {
												_t1025 = -1
											}
											_t1024 = _t1025
										}
										_t1023 = _t1024
									}
									_t1022 = _t1023
								}
								_t1021 = _t1022
							}
							_t1020 = _t1021
						}
						_t1019 = _t1020
					}
					_t1018 = _t1019
				}
				_t1017 = _t1018
			}
			_t1016 = _t1017
		}
		_t1015 = _t1016
	} else {
		_t1015 = -1
	}
	prediction512 := _t1015
	var _t1026 *pb.Primitive
	if prediction512 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1027 := p.parse_name()
		name522 := _t1027
		xs523 := []*pb.RelTerm{}
		cond524 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond524 {
			_t1028 := p.parse_rel_term()
			item525 := _t1028
			xs523 = append(xs523, item525)
			cond524 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms526 := xs523
		p.consumeLiteral(")")
		_t1029 := &pb.Primitive{Name: name522, Terms: rel_terms526}
		_t1026 = _t1029
	} else {
		var _t1030 *pb.Primitive
		if prediction512 == 8 {
			_t1031 := p.parse_divide()
			divide521 := _t1031
			_t1030 = divide521
		} else {
			var _t1032 *pb.Primitive
			if prediction512 == 7 {
				_t1033 := p.parse_multiply()
				multiply520 := _t1033
				_t1032 = multiply520
			} else {
				var _t1034 *pb.Primitive
				if prediction512 == 6 {
					_t1035 := p.parse_minus()
					minus519 := _t1035
					_t1034 = minus519
				} else {
					var _t1036 *pb.Primitive
					if prediction512 == 5 {
						_t1037 := p.parse_add()
						add518 := _t1037
						_t1036 = add518
					} else {
						var _t1038 *pb.Primitive
						if prediction512 == 4 {
							_t1039 := p.parse_gt_eq()
							gt_eq517 := _t1039
							_t1038 = gt_eq517
						} else {
							var _t1040 *pb.Primitive
							if prediction512 == 3 {
								_t1041 := p.parse_gt()
								gt516 := _t1041
								_t1040 = gt516
							} else {
								var _t1042 *pb.Primitive
								if prediction512 == 2 {
									_t1043 := p.parse_lt_eq()
									lt_eq515 := _t1043
									_t1042 = lt_eq515
								} else {
									var _t1044 *pb.Primitive
									if prediction512 == 1 {
										_t1045 := p.parse_lt()
										lt514 := _t1045
										_t1044 = lt514
									} else {
										var _t1046 *pb.Primitive
										if prediction512 == 0 {
											_t1047 := p.parse_eq()
											eq513 := _t1047
											_t1046 = eq513
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1044 = _t1046
									}
									_t1042 = _t1044
								}
								_t1040 = _t1042
							}
							_t1038 = _t1040
						}
						_t1036 = _t1038
					}
					_t1034 = _t1036
				}
				_t1032 = _t1034
			}
			_t1030 = _t1032
		}
		_t1026 = _t1030
	}
	return _t1026
}

func (p *Parser) parse_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1048 := p.parse_term()
	term527 := _t1048
	_t1049 := p.parse_term()
	term_3528 := _t1049
	p.consumeLiteral(")")
	_t1050 := &pb.RelTerm{}
	_t1050.RelTermType = &pb.RelTerm_Term{Term: term527}
	_t1051 := &pb.RelTerm{}
	_t1051.RelTermType = &pb.RelTerm_Term{Term: term_3528}
	_t1052 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1050, _t1051}}
	return _t1052
}

func (p *Parser) parse_lt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1053 := p.parse_term()
	term529 := _t1053
	_t1054 := p.parse_term()
	term_3530 := _t1054
	p.consumeLiteral(")")
	_t1055 := &pb.RelTerm{}
	_t1055.RelTermType = &pb.RelTerm_Term{Term: term529}
	_t1056 := &pb.RelTerm{}
	_t1056.RelTermType = &pb.RelTerm_Term{Term: term_3530}
	_t1057 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1055, _t1056}}
	return _t1057
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1058 := p.parse_term()
	term531 := _t1058
	_t1059 := p.parse_term()
	term_3532 := _t1059
	p.consumeLiteral(")")
	_t1060 := &pb.RelTerm{}
	_t1060.RelTermType = &pb.RelTerm_Term{Term: term531}
	_t1061 := &pb.RelTerm{}
	_t1061.RelTermType = &pb.RelTerm_Term{Term: term_3532}
	_t1062 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1060, _t1061}}
	return _t1062
}

func (p *Parser) parse_gt() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1063 := p.parse_term()
	term533 := _t1063
	_t1064 := p.parse_term()
	term_3534 := _t1064
	p.consumeLiteral(")")
	_t1065 := &pb.RelTerm{}
	_t1065.RelTermType = &pb.RelTerm_Term{Term: term533}
	_t1066 := &pb.RelTerm{}
	_t1066.RelTermType = &pb.RelTerm_Term{Term: term_3534}
	_t1067 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1065, _t1066}}
	return _t1067
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1068 := p.parse_term()
	term535 := _t1068
	_t1069 := p.parse_term()
	term_3536 := _t1069
	p.consumeLiteral(")")
	_t1070 := &pb.RelTerm{}
	_t1070.RelTermType = &pb.RelTerm_Term{Term: term535}
	_t1071 := &pb.RelTerm{}
	_t1071.RelTermType = &pb.RelTerm_Term{Term: term_3536}
	_t1072 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1070, _t1071}}
	return _t1072
}

func (p *Parser) parse_add() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1073 := p.parse_term()
	term537 := _t1073
	_t1074 := p.parse_term()
	term_3538 := _t1074
	_t1075 := p.parse_term()
	term_4539 := _t1075
	p.consumeLiteral(")")
	_t1076 := &pb.RelTerm{}
	_t1076.RelTermType = &pb.RelTerm_Term{Term: term537}
	_t1077 := &pb.RelTerm{}
	_t1077.RelTermType = &pb.RelTerm_Term{Term: term_3538}
	_t1078 := &pb.RelTerm{}
	_t1078.RelTermType = &pb.RelTerm_Term{Term: term_4539}
	_t1079 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1076, _t1077, _t1078}}
	return _t1079
}

func (p *Parser) parse_minus() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1080 := p.parse_term()
	term540 := _t1080
	_t1081 := p.parse_term()
	term_3541 := _t1081
	_t1082 := p.parse_term()
	term_4542 := _t1082
	p.consumeLiteral(")")
	_t1083 := &pb.RelTerm{}
	_t1083.RelTermType = &pb.RelTerm_Term{Term: term540}
	_t1084 := &pb.RelTerm{}
	_t1084.RelTermType = &pb.RelTerm_Term{Term: term_3541}
	_t1085 := &pb.RelTerm{}
	_t1085.RelTermType = &pb.RelTerm_Term{Term: term_4542}
	_t1086 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1083, _t1084, _t1085}}
	return _t1086
}

func (p *Parser) parse_multiply() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1087 := p.parse_term()
	term543 := _t1087
	_t1088 := p.parse_term()
	term_3544 := _t1088
	_t1089 := p.parse_term()
	term_4545 := _t1089
	p.consumeLiteral(")")
	_t1090 := &pb.RelTerm{}
	_t1090.RelTermType = &pb.RelTerm_Term{Term: term543}
	_t1091 := &pb.RelTerm{}
	_t1091.RelTermType = &pb.RelTerm_Term{Term: term_3544}
	_t1092 := &pb.RelTerm{}
	_t1092.RelTermType = &pb.RelTerm_Term{Term: term_4545}
	_t1093 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1090, _t1091, _t1092}}
	return _t1093
}

func (p *Parser) parse_divide() *pb.Primitive {
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1094 := p.parse_term()
	term546 := _t1094
	_t1095 := p.parse_term()
	term_3547 := _t1095
	_t1096 := p.parse_term()
	term_4548 := _t1096
	p.consumeLiteral(")")
	_t1097 := &pb.RelTerm{}
	_t1097.RelTermType = &pb.RelTerm_Term{Term: term546}
	_t1098 := &pb.RelTerm{}
	_t1098.RelTermType = &pb.RelTerm_Term{Term: term_3547}
	_t1099 := &pb.RelTerm{}
	_t1099.RelTermType = &pb.RelTerm_Term{Term: term_4548}
	_t1100 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1097, _t1098, _t1099}}
	return _t1100
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	var _t1101 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1101 = 1
	} else {
		var _t1102 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1102 = 1
		} else {
			var _t1103 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1103 = 1
			} else {
				var _t1104 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1104 = 1
				} else {
					var _t1105 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1105 = 0
					} else {
						var _t1106 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1106 = 1
						} else {
							var _t1107 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1107 = 1
							} else {
								var _t1108 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1108 = 1
								} else {
									var _t1109 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1109 = 1
									} else {
										var _t1110 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1110 = 1
										} else {
											var _t1111 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1111 = 1
											} else {
												var _t1112 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1112 = 1
												} else {
													_t1112 = -1
												}
												_t1111 = _t1112
											}
											_t1110 = _t1111
										}
										_t1109 = _t1110
									}
									_t1108 = _t1109
								}
								_t1107 = _t1108
							}
							_t1106 = _t1107
						}
						_t1105 = _t1106
					}
					_t1104 = _t1105
				}
				_t1103 = _t1104
			}
			_t1102 = _t1103
		}
		_t1101 = _t1102
	}
	prediction549 := _t1101
	var _t1113 *pb.RelTerm
	if prediction549 == 1 {
		_t1114 := p.parse_term()
		term551 := _t1114
		_t1115 := &pb.RelTerm{}
		_t1115.RelTermType = &pb.RelTerm_Term{Term: term551}
		_t1113 = _t1115
	} else {
		var _t1116 *pb.RelTerm
		if prediction549 == 0 {
			_t1117 := p.parse_specialized_value()
			specialized_value550 := _t1117
			_t1118 := &pb.RelTerm{}
			_t1118.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value550}
			_t1116 = _t1118
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1113 = _t1116
	}
	return _t1113
}

func (p *Parser) parse_specialized_value() *pb.Value {
	p.consumeLiteral("#")
	_t1119 := p.parse_value()
	value552 := _t1119
	return value552
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1120 := p.parse_name()
	name553 := _t1120
	xs554 := []*pb.RelTerm{}
	cond555 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond555 {
		_t1121 := p.parse_rel_term()
		item556 := _t1121
		xs554 = append(xs554, item556)
		cond555 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms557 := xs554
	p.consumeLiteral(")")
	_t1122 := &pb.RelAtom{Name: name553, Terms: rel_terms557}
	return _t1122
}

func (p *Parser) parse_cast() *pb.Cast {
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1123 := p.parse_term()
	term558 := _t1123
	_t1124 := p.parse_term()
	term_3559 := _t1124
	p.consumeLiteral(")")
	_t1125 := &pb.Cast{Input: term558, Result: term_3559}
	return _t1125
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs560 := []*pb.Attribute{}
	cond561 := p.matchLookaheadLiteral("(", 0)
	for cond561 {
		_t1126 := p.parse_attribute()
		item562 := _t1126
		xs560 = append(xs560, item562)
		cond561 = p.matchLookaheadLiteral("(", 0)
	}
	attributes563 := xs560
	p.consumeLiteral(")")
	return attributes563
}

func (p *Parser) parse_attribute() *pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1127 := p.parse_name()
	name564 := _t1127
	xs565 := []*pb.Value{}
	cond566 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond566 {
		_t1128 := p.parse_value()
		item567 := _t1128
		xs565 = append(xs565, item567)
		cond566 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values568 := xs565
	p.consumeLiteral(")")
	_t1129 := &pb.Attribute{Name: name564, Args: values568}
	return _t1129
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs569 := []*pb.RelationId{}
	cond570 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond570 {
		_t1130 := p.parse_relation_id()
		item571 := _t1130
		xs569 = append(xs569, item571)
		cond570 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids572 := xs569
	_t1131 := p.parse_script()
	script573 := _t1131
	p.consumeLiteral(")")
	_t1132 := &pb.Algorithm{Global: relation_ids572, Body: script573}
	return _t1132
}

func (p *Parser) parse_script() *pb.Script {
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs574 := []*pb.Construct{}
	cond575 := p.matchLookaheadLiteral("(", 0)
	for cond575 {
		_t1133 := p.parse_construct()
		item576 := _t1133
		xs574 = append(xs574, item576)
		cond575 = p.matchLookaheadLiteral("(", 0)
	}
	constructs577 := xs574
	p.consumeLiteral(")")
	_t1134 := &pb.Script{Constructs: constructs577}
	return _t1134
}

func (p *Parser) parse_construct() *pb.Construct {
	var _t1135 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1136 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1136 = 1
		} else {
			var _t1137 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1137 = 1
			} else {
				var _t1138 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1138 = 1
				} else {
					var _t1139 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1139 = 0
					} else {
						var _t1140 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1140 = 1
						} else {
							var _t1141 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1141 = 1
							} else {
								_t1141 = -1
							}
							_t1140 = _t1141
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
	} else {
		_t1135 = -1
	}
	prediction578 := _t1135
	var _t1142 *pb.Construct
	if prediction578 == 1 {
		_t1143 := p.parse_instruction()
		instruction580 := _t1143
		_t1144 := &pb.Construct{}
		_t1144.ConstructType = &pb.Construct_Instruction{Instruction: instruction580}
		_t1142 = _t1144
	} else {
		var _t1145 *pb.Construct
		if prediction578 == 0 {
			_t1146 := p.parse_loop()
			loop579 := _t1146
			_t1147 := &pb.Construct{}
			_t1147.ConstructType = &pb.Construct_Loop{Loop: loop579}
			_t1145 = _t1147
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1142 = _t1145
	}
	return _t1142
}

func (p *Parser) parse_loop() *pb.Loop {
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1148 := p.parse_init()
	init581 := _t1148
	_t1149 := p.parse_script()
	script582 := _t1149
	p.consumeLiteral(")")
	_t1150 := &pb.Loop{Init: init581, Body: script582}
	return _t1150
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs583 := []*pb.Instruction{}
	cond584 := p.matchLookaheadLiteral("(", 0)
	for cond584 {
		_t1151 := p.parse_instruction()
		item585 := _t1151
		xs583 = append(xs583, item585)
		cond584 = p.matchLookaheadLiteral("(", 0)
	}
	instructions586 := xs583
	p.consumeLiteral(")")
	return instructions586
}

func (p *Parser) parse_instruction() *pb.Instruction {
	var _t1152 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1153 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1153 = 1
		} else {
			var _t1154 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1154 = 4
			} else {
				var _t1155 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1155 = 3
				} else {
					var _t1156 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1156 = 2
					} else {
						var _t1157 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1157 = 0
						} else {
							_t1157 = -1
						}
						_t1156 = _t1157
					}
					_t1155 = _t1156
				}
				_t1154 = _t1155
			}
			_t1153 = _t1154
		}
		_t1152 = _t1153
	} else {
		_t1152 = -1
	}
	prediction587 := _t1152
	var _t1158 *pb.Instruction
	if prediction587 == 4 {
		_t1159 := p.parse_monus_def()
		monus_def592 := _t1159
		_t1160 := &pb.Instruction{}
		_t1160.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def592}
		_t1158 = _t1160
	} else {
		var _t1161 *pb.Instruction
		if prediction587 == 3 {
			_t1162 := p.parse_monoid_def()
			monoid_def591 := _t1162
			_t1163 := &pb.Instruction{}
			_t1163.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def591}
			_t1161 = _t1163
		} else {
			var _t1164 *pb.Instruction
			if prediction587 == 2 {
				_t1165 := p.parse_break()
				break590 := _t1165
				_t1166 := &pb.Instruction{}
				_t1166.InstrType = &pb.Instruction_Break{Break: break590}
				_t1164 = _t1166
			} else {
				var _t1167 *pb.Instruction
				if prediction587 == 1 {
					_t1168 := p.parse_upsert()
					upsert589 := _t1168
					_t1169 := &pb.Instruction{}
					_t1169.InstrType = &pb.Instruction_Upsert{Upsert: upsert589}
					_t1167 = _t1169
				} else {
					var _t1170 *pb.Instruction
					if prediction587 == 0 {
						_t1171 := p.parse_assign()
						assign588 := _t1171
						_t1172 := &pb.Instruction{}
						_t1172.InstrType = &pb.Instruction_Assign{Assign: assign588}
						_t1170 = _t1172
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1167 = _t1170
				}
				_t1164 = _t1167
			}
			_t1161 = _t1164
		}
		_t1158 = _t1161
	}
	return _t1158
}

func (p *Parser) parse_assign() *pb.Assign {
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1173 := p.parse_relation_id()
	relation_id593 := _t1173
	_t1174 := p.parse_abstraction()
	abstraction594 := _t1174
	var _t1175 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1176 := p.parse_attrs()
		_t1175 = _t1176
	}
	attrs595 := _t1175
	p.consumeLiteral(")")
	_t1177 := attrs595
	if attrs595 == nil {
		_t1177 = []*pb.Attribute{}
	}
	_t1178 := &pb.Assign{Name: relation_id593, Body: abstraction594, Attrs: _t1177}
	return _t1178
}

func (p *Parser) parse_upsert() *pb.Upsert {
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1179 := p.parse_relation_id()
	relation_id596 := _t1179
	_t1180 := p.parse_abstraction_with_arity()
	abstraction_with_arity597 := _t1180
	var _t1181 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1182 := p.parse_attrs()
		_t1181 = _t1182
	}
	attrs598 := _t1181
	p.consumeLiteral(")")
	_t1183 := attrs598
	if attrs598 == nil {
		_t1183 = []*pb.Attribute{}
	}
	_t1184 := &pb.Upsert{Name: relation_id596, Body: abstraction_with_arity597[0].(*pb.Abstraction), Attrs: _t1183, ValueArity: abstraction_with_arity597[1].(int64)}
	return _t1184
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1185 := p.parse_bindings()
	bindings599 := _t1185
	_t1186 := p.parse_formula()
	formula600 := _t1186
	p.consumeLiteral(")")
	_t1187 := &pb.Abstraction{Vars: listConcat(bindings599[0].([]*pb.Binding), bindings599[1].([]*pb.Binding)), Value: formula600}
	return []interface{}{_t1187, int64(len(bindings599[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1188 := p.parse_relation_id()
	relation_id601 := _t1188
	_t1189 := p.parse_abstraction()
	abstraction602 := _t1189
	var _t1190 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1191 := p.parse_attrs()
		_t1190 = _t1191
	}
	attrs603 := _t1190
	p.consumeLiteral(")")
	_t1192 := attrs603
	if attrs603 == nil {
		_t1192 = []*pb.Attribute{}
	}
	_t1193 := &pb.Break{Name: relation_id601, Body: abstraction602, Attrs: _t1192}
	return _t1193
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1194 := p.parse_monoid()
	monoid604 := _t1194
	_t1195 := p.parse_relation_id()
	relation_id605 := _t1195
	_t1196 := p.parse_abstraction_with_arity()
	abstraction_with_arity606 := _t1196
	var _t1197 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1198 := p.parse_attrs()
		_t1197 = _t1198
	}
	attrs607 := _t1197
	p.consumeLiteral(")")
	_t1199 := attrs607
	if attrs607 == nil {
		_t1199 = []*pb.Attribute{}
	}
	_t1200 := &pb.MonoidDef{Monoid: monoid604, Name: relation_id605, Body: abstraction_with_arity606[0].(*pb.Abstraction), Attrs: _t1199, ValueArity: abstraction_with_arity606[1].(int64)}
	return _t1200
}

func (p *Parser) parse_monoid() *pb.Monoid {
	var _t1201 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1202 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1202 = 3
		} else {
			var _t1203 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1203 = 0
			} else {
				var _t1204 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1204 = 1
				} else {
					var _t1205 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1205 = 2
					} else {
						_t1205 = -1
					}
					_t1204 = _t1205
				}
				_t1203 = _t1204
			}
			_t1202 = _t1203
		}
		_t1201 = _t1202
	} else {
		_t1201 = -1
	}
	prediction608 := _t1201
	var _t1206 *pb.Monoid
	if prediction608 == 3 {
		_t1207 := p.parse_sum_monoid()
		sum_monoid612 := _t1207
		_t1208 := &pb.Monoid{}
		_t1208.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid612}
		_t1206 = _t1208
	} else {
		var _t1209 *pb.Monoid
		if prediction608 == 2 {
			_t1210 := p.parse_max_monoid()
			max_monoid611 := _t1210
			_t1211 := &pb.Monoid{}
			_t1211.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid611}
			_t1209 = _t1211
		} else {
			var _t1212 *pb.Monoid
			if prediction608 == 1 {
				_t1213 := p.parse_min_monoid()
				min_monoid610 := _t1213
				_t1214 := &pb.Monoid{}
				_t1214.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid610}
				_t1212 = _t1214
			} else {
				var _t1215 *pb.Monoid
				if prediction608 == 0 {
					_t1216 := p.parse_or_monoid()
					or_monoid609 := _t1216
					_t1217 := &pb.Monoid{}
					_t1217.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid609}
					_t1215 = _t1217
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1212 = _t1215
			}
			_t1209 = _t1212
		}
		_t1206 = _t1209
	}
	return _t1206
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1218 := &pb.OrMonoid{}
	return _t1218
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1219 := p.parse_type()
	type613 := _t1219
	p.consumeLiteral(")")
	_t1220 := &pb.MinMonoid{Type: type613}
	return _t1220
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1221 := p.parse_type()
	type614 := _t1221
	p.consumeLiteral(")")
	_t1222 := &pb.MaxMonoid{Type: type614}
	return _t1222
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1223 := p.parse_type()
	type615 := _t1223
	p.consumeLiteral(")")
	_t1224 := &pb.SumMonoid{Type: type615}
	return _t1224
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1225 := p.parse_monoid()
	monoid616 := _t1225
	_t1226 := p.parse_relation_id()
	relation_id617 := _t1226
	_t1227 := p.parse_abstraction_with_arity()
	abstraction_with_arity618 := _t1227
	var _t1228 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1229 := p.parse_attrs()
		_t1228 = _t1229
	}
	attrs619 := _t1228
	p.consumeLiteral(")")
	_t1230 := attrs619
	if attrs619 == nil {
		_t1230 = []*pb.Attribute{}
	}
	_t1231 := &pb.MonusDef{Monoid: monoid616, Name: relation_id617, Body: abstraction_with_arity618[0].(*pb.Abstraction), Attrs: _t1230, ValueArity: abstraction_with_arity618[1].(int64)}
	return _t1231
}

func (p *Parser) parse_constraint() *pb.Constraint {
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1232 := p.parse_relation_id()
	relation_id620 := _t1232
	_t1233 := p.parse_abstraction()
	abstraction621 := _t1233
	_t1234 := p.parse_functional_dependency_keys()
	functional_dependency_keys622 := _t1234
	_t1235 := p.parse_functional_dependency_values()
	functional_dependency_values623 := _t1235
	p.consumeLiteral(")")
	_t1236 := &pb.FunctionalDependency{Guard: abstraction621, Keys: functional_dependency_keys622, Values: functional_dependency_values623}
	_t1237 := &pb.Constraint{Name: relation_id620}
	_t1237.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1236}
	return _t1237
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs624 := []*pb.Var{}
	cond625 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond625 {
		_t1238 := p.parse_var()
		item626 := _t1238
		xs624 = append(xs624, item626)
		cond625 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars627 := xs624
	p.consumeLiteral(")")
	return vars627
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs628 := []*pb.Var{}
	cond629 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond629 {
		_t1239 := p.parse_var()
		item630 := _t1239
		xs628 = append(xs628, item630)
		cond629 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars631 := xs628
	p.consumeLiteral(")")
	return vars631
}

func (p *Parser) parse_data() *pb.Data {
	var _t1240 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1241 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1241 = 0
		} else {
			var _t1242 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1242 = 2
			} else {
				var _t1243 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1243 = 1
				} else {
					_t1243 = -1
				}
				_t1242 = _t1243
			}
			_t1241 = _t1242
		}
		_t1240 = _t1241
	} else {
		_t1240 = -1
	}
	prediction632 := _t1240
	var _t1244 *pb.Data
	if prediction632 == 2 {
		_t1245 := p.parse_csv_data()
		csv_data635 := _t1245
		_t1246 := &pb.Data{}
		_t1246.DataType = &pb.Data_CsvData{CsvData: csv_data635}
		_t1244 = _t1246
	} else {
		var _t1247 *pb.Data
		if prediction632 == 1 {
			_t1248 := p.parse_betree_relation()
			betree_relation634 := _t1248
			_t1249 := &pb.Data{}
			_t1249.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation634}
			_t1247 = _t1249
		} else {
			var _t1250 *pb.Data
			if prediction632 == 0 {
				_t1251 := p.parse_edb()
				edb633 := _t1251
				_t1252 := &pb.Data{}
				_t1252.DataType = &pb.Data_Edb{Edb: edb633}
				_t1250 = _t1252
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1247 = _t1250
		}
		_t1244 = _t1247
	}
	return _t1244
}

func (p *Parser) parse_edb() *pb.EDB {
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1253 := p.parse_relation_id()
	relation_id636 := _t1253
	_t1254 := p.parse_edb_path()
	edb_path637 := _t1254
	_t1255 := p.parse_edb_types()
	edb_types638 := _t1255
	p.consumeLiteral(")")
	_t1256 := &pb.EDB{TargetId: relation_id636, Path: edb_path637, Types: edb_types638}
	return _t1256
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs639 := []string{}
	cond640 := p.matchLookaheadTerminal("STRING", 0)
	for cond640 {
		item641 := p.consumeTerminal("STRING").Value.str
		xs639 = append(xs639, item641)
		cond640 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings642 := xs639
	p.consumeLiteral("]")
	return strings642
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs643 := []*pb.Type{}
	cond644 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond644 {
		_t1257 := p.parse_type()
		item645 := _t1257
		xs643 = append(xs643, item645)
		cond644 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types646 := xs643
	p.consumeLiteral("]")
	return types646
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1258 := p.parse_relation_id()
	relation_id647 := _t1258
	_t1259 := p.parse_betree_info()
	betree_info648 := _t1259
	p.consumeLiteral(")")
	_t1260 := &pb.BeTreeRelation{Name: relation_id647, RelationInfo: betree_info648}
	return _t1260
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1261 := p.parse_betree_info_key_types()
	betree_info_key_types649 := _t1261
	_t1262 := p.parse_betree_info_value_types()
	betree_info_value_types650 := _t1262
	_t1263 := p.parse_config_dict()
	config_dict651 := _t1263
	p.consumeLiteral(")")
	_t1264 := p.construct_betree_info(betree_info_key_types649, betree_info_value_types650, config_dict651)
	return _t1264
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs652 := []*pb.Type{}
	cond653 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond653 {
		_t1265 := p.parse_type()
		item654 := _t1265
		xs652 = append(xs652, item654)
		cond653 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types655 := xs652
	p.consumeLiteral(")")
	return types655
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs656 := []*pb.Type{}
	cond657 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond657 {
		_t1266 := p.parse_type()
		item658 := _t1266
		xs656 = append(xs656, item658)
		cond657 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types659 := xs656
	p.consumeLiteral(")")
	return types659
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1267 := p.parse_csvlocator()
	csvlocator660 := _t1267
	_t1268 := p.parse_csv_config()
	csv_config661 := _t1268
	_t1269 := p.parse_gnf_columns()
	gnf_columns662 := _t1269
	_t1270 := p.parse_csv_asof()
	csv_asof663 := _t1270
	p.consumeLiteral(")")
	_t1271 := &pb.CSVData{Locator: csvlocator660, Config: csv_config661, Columns: gnf_columns662, Asof: csv_asof663}
	return _t1271
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1272 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1273 := p.parse_csv_locator_paths()
		_t1272 = _t1273
	}
	csv_locator_paths664 := _t1272
	var _t1274 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1275 := p.parse_csv_locator_inline_data()
		_t1274 = ptr(_t1275)
	}
	csv_locator_inline_data665 := _t1274
	p.consumeLiteral(")")
	_t1276 := csv_locator_paths664
	if csv_locator_paths664 == nil {
		_t1276 = []string{}
	}
	_t1277 := &pb.CSVLocator{Paths: _t1276, InlineData: []byte(deref(csv_locator_inline_data665, ""))}
	return _t1277
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs666 := []string{}
	cond667 := p.matchLookaheadTerminal("STRING", 0)
	for cond667 {
		item668 := p.consumeTerminal("STRING").Value.str
		xs666 = append(xs666, item668)
		cond667 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings669 := xs666
	p.consumeLiteral(")")
	return strings669
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string670 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string670
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1278 := p.parse_config_dict()
	config_dict671 := _t1278
	p.consumeLiteral(")")
	_t1279 := p.construct_csv_config(config_dict671)
	return _t1279
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs672 := []*pb.GNFColumn{}
	cond673 := p.matchLookaheadLiteral("(", 0)
	for cond673 {
		_t1280 := p.parse_gnf_column()
		item674 := _t1280
		xs672 = append(xs672, item674)
		cond673 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns675 := xs672
	p.consumeLiteral(")")
	return gnf_columns675
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1281 := p.parse_gnf_column_path()
	gnf_column_path676 := _t1281
	var _t1282 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1283 := p.parse_relation_id()
		_t1282 = _t1283
	}
	relation_id677 := _t1282
	p.consumeLiteral("[")
	xs678 := []*pb.Type{}
	cond679 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond679 {
		_t1284 := p.parse_type()
		item680 := _t1284
		xs678 = append(xs678, item680)
		cond679 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types681 := xs678
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1285 := &pb.GNFColumn{ColumnPath: gnf_column_path676, TargetId: relation_id677, Types: types681}
	return _t1285
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1286 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1286 = 1
	} else {
		var _t1287 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1287 = 0
		} else {
			_t1287 = -1
		}
		_t1286 = _t1287
	}
	prediction682 := _t1286
	var _t1288 []string
	if prediction682 == 1 {
		p.consumeLiteral("[")
		xs684 := []string{}
		cond685 := p.matchLookaheadTerminal("STRING", 0)
		for cond685 {
			item686 := p.consumeTerminal("STRING").Value.str
			xs684 = append(xs684, item686)
			cond685 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings687 := xs684
		p.consumeLiteral("]")
		_t1288 = strings687
	} else {
		var _t1289 []string
		if prediction682 == 0 {
			string683 := p.consumeTerminal("STRING").Value.str
			_ = string683
			_t1289 = []string{string683}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1288 = _t1289
	}
	return _t1288
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string688 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string688
}

func (p *Parser) parse_undefine() *pb.Undefine {
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1290 := p.parse_fragment_id()
	fragment_id689 := _t1290
	p.consumeLiteral(")")
	_t1291 := &pb.Undefine{FragmentId: fragment_id689}
	return _t1291
}

func (p *Parser) parse_context() *pb.Context {
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs690 := []*pb.RelationId{}
	cond691 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond691 {
		_t1292 := p.parse_relation_id()
		item692 := _t1292
		xs690 = append(xs690, item692)
		cond691 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids693 := xs690
	p.consumeLiteral(")")
	_t1293 := &pb.Context{Relations: relation_ids693}
	return _t1293
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1294 := p.parse_edb_path()
	edb_path694 := _t1294
	_t1295 := p.parse_relation_id()
	relation_id695 := _t1295
	p.consumeLiteral(")")
	_t1296 := &pb.Snapshot{DestinationPath: edb_path694, SourceRelation: relation_id695}
	return _t1296
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs696 := []*pb.Read{}
	cond697 := p.matchLookaheadLiteral("(", 0)
	for cond697 {
		_t1297 := p.parse_read()
		item698 := _t1297
		xs696 = append(xs696, item698)
		cond697 = p.matchLookaheadLiteral("(", 0)
	}
	reads699 := xs696
	p.consumeLiteral(")")
	return reads699
}

func (p *Parser) parse_read() *pb.Read {
	var _t1298 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1299 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1299 = 2
		} else {
			var _t1300 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1300 = 1
			} else {
				var _t1301 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1301 = 4
				} else {
					var _t1302 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1302 = 0
					} else {
						var _t1303 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1303 = 3
						} else {
							_t1303 = -1
						}
						_t1302 = _t1303
					}
					_t1301 = _t1302
				}
				_t1300 = _t1301
			}
			_t1299 = _t1300
		}
		_t1298 = _t1299
	} else {
		_t1298 = -1
	}
	prediction700 := _t1298
	var _t1304 *pb.Read
	if prediction700 == 4 {
		_t1305 := p.parse_export()
		export705 := _t1305
		_t1306 := &pb.Read{}
		_t1306.ReadType = &pb.Read_Export{Export: export705}
		_t1304 = _t1306
	} else {
		var _t1307 *pb.Read
		if prediction700 == 3 {
			_t1308 := p.parse_abort()
			abort704 := _t1308
			_t1309 := &pb.Read{}
			_t1309.ReadType = &pb.Read_Abort{Abort: abort704}
			_t1307 = _t1309
		} else {
			var _t1310 *pb.Read
			if prediction700 == 2 {
				_t1311 := p.parse_what_if()
				what_if703 := _t1311
				_t1312 := &pb.Read{}
				_t1312.ReadType = &pb.Read_WhatIf{WhatIf: what_if703}
				_t1310 = _t1312
			} else {
				var _t1313 *pb.Read
				if prediction700 == 1 {
					_t1314 := p.parse_output()
					output702 := _t1314
					_t1315 := &pb.Read{}
					_t1315.ReadType = &pb.Read_Output{Output: output702}
					_t1313 = _t1315
				} else {
					var _t1316 *pb.Read
					if prediction700 == 0 {
						_t1317 := p.parse_demand()
						demand701 := _t1317
						_t1318 := &pb.Read{}
						_t1318.ReadType = &pb.Read_Demand{Demand: demand701}
						_t1316 = _t1318
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1313 = _t1316
				}
				_t1310 = _t1313
			}
			_t1307 = _t1310
		}
		_t1304 = _t1307
	}
	return _t1304
}

func (p *Parser) parse_demand() *pb.Demand {
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1319 := p.parse_relation_id()
	relation_id706 := _t1319
	p.consumeLiteral(")")
	_t1320 := &pb.Demand{RelationId: relation_id706}
	return _t1320
}

func (p *Parser) parse_output() *pb.Output {
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1321 := p.parse_name()
	name707 := _t1321
	_t1322 := p.parse_relation_id()
	relation_id708 := _t1322
	p.consumeLiteral(")")
	_t1323 := &pb.Output{Name: name707, RelationId: relation_id708}
	return _t1323
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1324 := p.parse_name()
	name709 := _t1324
	_t1325 := p.parse_epoch()
	epoch710 := _t1325
	p.consumeLiteral(")")
	_t1326 := &pb.WhatIf{Branch: name709, Epoch: epoch710}
	return _t1326
}

func (p *Parser) parse_abort() *pb.Abort {
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1327 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1328 := p.parse_name()
		_t1327 = ptr(_t1328)
	}
	name711 := _t1327
	_t1329 := p.parse_relation_id()
	relation_id712 := _t1329
	p.consumeLiteral(")")
	_t1330 := &pb.Abort{Name: deref(name711, "abort"), RelationId: relation_id712}
	return _t1330
}

func (p *Parser) parse_export() *pb.Export {
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1331 := p.parse_export_csv_config()
	export_csv_config713 := _t1331
	p.consumeLiteral(")")
	_t1332 := &pb.Export{}
	_t1332.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config713}
	return _t1332
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1333 := p.parse_export_csv_path()
	export_csv_path714 := _t1333
	_t1334 := p.parse_export_csv_columns()
	export_csv_columns715 := _t1334
	_t1335 := p.parse_config_dict()
	config_dict716 := _t1335
	p.consumeLiteral(")")
	_t1336 := p.export_csv_config(export_csv_path714, export_csv_columns715, config_dict716)
	return _t1336
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string717 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string717
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs718 := []*pb.ExportCSVColumn{}
	cond719 := p.matchLookaheadLiteral("(", 0)
	for cond719 {
		_t1337 := p.parse_export_csv_column()
		item720 := _t1337
		xs718 = append(xs718, item720)
		cond719 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns721 := xs718
	p.consumeLiteral(")")
	return export_csv_columns721
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string722 := p.consumeTerminal("STRING").Value.str
	_t1338 := p.parse_relation_id()
	relation_id723 := _t1338
	p.consumeLiteral(")")
	_t1339 := &pb.ExportCSVColumn{ColumnName: string722, ColumnData: relation_id723}
	return _t1339
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
