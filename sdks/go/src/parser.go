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

// Location represents a source location (1-based line/column, 0-based byte offset).
type Location struct {
	Line   int
	Column int
	Offset int
}

// Span represents a source span from start to stop location.
type Span struct {
	Start    Location
	Stop     Location
	TypeName string
}

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
	Type     string
	Value    TokenValue
	StartPos int
	EndPos   int
}

// Pos returns the start position for backwards compatibility.
func (t Token) Pos() int { return t.StartPos }

func (t Token) String() string {
	return fmt.Sprintf("Token(%s, %v, %d)", t.Type, t.Value, t.StartPos)
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
			Type:     best.tokenType,
			Value:    best.action(best.value),
			StartPos: l.pos,
			EndPos:   best.endPos,
		})
		l.pos = best.endPos
	}

	l.tokens = append(l.tokens, Token{Type: "$", Value: TokenValue{}, StartPos: l.pos, EndPos: l.pos})
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

func computeLineStarts(text string) []int {
	starts := []int{0}
	for i, ch := range text {
		if ch == '\n' {
			starts = append(starts, i+1)
		}
	}
	return starts
}

// Parser is an LL(k) recursive-descent parser
type Parser struct {
	tokens            []Token
	pos               int
	idToDebugInfo     map[string]map[relationIdKey]string
	currentFragmentID []byte
	Provenance        map[int]Span
	lineStarts        []int
}

// NewParser creates a new parser
func NewParser(tokens []Token, input string) *Parser {
	return &Parser{
		tokens:            tokens,
		pos:               0,
		idToDebugInfo:     make(map[string]map[relationIdKey]string),
		currentFragmentID: nil,
		Provenance:        make(map[int]Span),
		lineStarts:        computeLineStarts(input),
	}
}

func (p *Parser) makeLocation(offset int) Location {
	lo, hi := 0, len(p.lineStarts)
	for lo < hi {
		mid := (lo + hi) / 2
		if p.lineStarts[mid] <= offset {
			lo = mid + 1
		} else {
			hi = mid
		}
	}
	lineIdx := lo - 1
	col := offset - p.lineStarts[lineIdx]
	return Location{Line: lineIdx + 1, Column: col + 1, Offset: offset}
}

func (p *Parser) spanStart() int {
	return p.lookahead(0).StartPos
}

func (p *Parser) recordSpan(startOffset int, typeName string) {
	// First-wins: innermost parse function records first; outer wrappers
	// that share the same offset do not overwrite.
	if _, exists := p.Provenance[startOffset]; exists {
		return
	}
	endOffset := startOffset
	if p.pos > 0 {
		endOffset = p.tokens[p.pos-1].EndPos
	}
	s := Span{
		Start:    p.makeLocation(startOffset),
		Stop:     p.makeLocation(endOffset),
		TypeName: typeName,
	}
	p.Provenance[startOffset] = s
}

func (p *Parser) lookahead(k int) Token {
	idx := p.pos + k
	if idx < len(p.tokens) {
		return p.tokens[idx]
	}
	return Token{Type: "$", Value: TokenValue{}, StartPos: -1, EndPos: -1}
}

func (p *Parser) consumeLiteral(expected string) {
	if !p.matchLookaheadLiteral(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected literal %q but got %s=`%v` at position %d", expected, token.Type, token.Value, token.StartPos)})
	}
	p.pos++
}

func (p *Parser) consumeTerminal(expected string) Token {
	if !p.matchLookaheadTerminal(expected, 0) {
		token := p.lookahead(0)
		panic(ParseError{msg: fmt.Sprintf("Expected terminal %s but got %s=`%v` at position %d", expected, token.Type, token.Value, token.StartPos)})
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
	var _t1694 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1694
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1695 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1695
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1696 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1696
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1697 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1697
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1698 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1698
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1699 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1699
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1700 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1700
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1701 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1701
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1702 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1702
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1703 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1703
	_t1704 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1704
	_t1705 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1705
	_t1706 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1706
	_t1707 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1707
	_t1708 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1708
	_t1709 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1709
	_t1710 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1710
	_t1711 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1711
	_t1712 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1712
	_t1713 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1713
	_t1714 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t1714
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1715 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1715
	_t1716 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1716
	_t1717 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1717
	_t1718 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1718
	_t1719 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1719
	_t1720 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1720
	_t1721 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1721
	_t1722 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1722
	_t1723 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1723
	_t1724 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1724.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1724.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1724
	_t1725 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1725
}

func (p *Parser) default_configure() *pb.Configure {
	_t1726 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1726
	_t1727 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1727
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
	_t1728 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1728
	_t1729 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1729
	_t1730 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1730
}

func (p *Parser) export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1731 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1731
	_t1732 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1732
	_t1733 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1733
	_t1734 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1734
	_t1735 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1735
	_t1736 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1736
	_t1737 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1737
	_t1738 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1738
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start548 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1084 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1085 := p.parse_configure()
		_t1084 = _t1085
	}
	configure542 := _t1084
	var _t1086 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1087 := p.parse_sync()
		_t1086 = _t1087
	}
	sync543 := _t1086
	xs544 := []*pb.Epoch{}
	cond545 := p.matchLookaheadLiteral("(", 0)
	for cond545 {
		_t1088 := p.parse_epoch()
		item546 := _t1088
		xs544 = append(xs544, item546)
		cond545 = p.matchLookaheadLiteral("(", 0)
	}
	epochs547 := xs544
	p.consumeLiteral(")")
	_t1089 := p.default_configure()
	_t1090 := configure542
	if configure542 == nil {
		_t1090 = _t1089
	}
	_t1091 := &pb.Transaction{Epochs: epochs547, Configure: _t1090, Sync: sync543}
	result549 := _t1091
	p.recordSpan(int(span_start548), "Transaction")
	return result549
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start551 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1092 := p.parse_config_dict()
	config_dict550 := _t1092
	p.consumeLiteral(")")
	_t1093 := p.construct_configure(config_dict550)
	result552 := _t1093
	p.recordSpan(int(span_start551), "Configure")
	return result552
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs553 := [][]interface{}{}
	cond554 := p.matchLookaheadLiteral(":", 0)
	for cond554 {
		_t1094 := p.parse_config_key_value()
		item555 := _t1094
		xs553 = append(xs553, item555)
		cond554 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values556 := xs553
	p.consumeLiteral("}")
	return config_key_values556
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol557 := p.consumeTerminal("SYMBOL").Value.str
	_t1095 := p.parse_value()
	value558 := _t1095
	return []interface{}{symbol557, value558}
}

func (p *Parser) parse_value() *pb.Value {
	span_start569 := int64(p.spanStart())
	var _t1096 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1096 = 9
	} else {
		var _t1097 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1097 = 8
		} else {
			var _t1098 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1098 = 9
			} else {
				var _t1099 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1100 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1100 = 1
					} else {
						var _t1101 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1101 = 0
						} else {
							_t1101 = -1
						}
						_t1100 = _t1101
					}
					_t1099 = _t1100
				} else {
					var _t1102 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1102 = 5
					} else {
						var _t1103 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1103 = 2
						} else {
							var _t1104 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1104 = 6
							} else {
								var _t1105 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1105 = 3
								} else {
									var _t1106 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1106 = 4
									} else {
										var _t1107 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1107 = 7
										} else {
											_t1107 = -1
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
					_t1099 = _t1102
				}
				_t1098 = _t1099
			}
			_t1097 = _t1098
		}
		_t1096 = _t1097
	}
	prediction559 := _t1096
	var _t1108 *pb.Value
	if prediction559 == 9 {
		_t1109 := p.parse_boolean_value()
		boolean_value568 := _t1109
		_t1110 := &pb.Value{}
		_t1110.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value568}
		_t1108 = _t1110
	} else {
		var _t1111 *pb.Value
		if prediction559 == 8 {
			p.consumeLiteral("missing")
			_t1112 := &pb.MissingValue{}
			_t1113 := &pb.Value{}
			_t1113.Value = &pb.Value_MissingValue{MissingValue: _t1112}
			_t1111 = _t1113
		} else {
			var _t1114 *pb.Value
			if prediction559 == 7 {
				decimal567 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1115 := &pb.Value{}
				_t1115.Value = &pb.Value_DecimalValue{DecimalValue: decimal567}
				_t1114 = _t1115
			} else {
				var _t1116 *pb.Value
				if prediction559 == 6 {
					int128566 := p.consumeTerminal("INT128").Value.int128
					_t1117 := &pb.Value{}
					_t1117.Value = &pb.Value_Int128Value{Int128Value: int128566}
					_t1116 = _t1117
				} else {
					var _t1118 *pb.Value
					if prediction559 == 5 {
						uint128565 := p.consumeTerminal("UINT128").Value.uint128
						_t1119 := &pb.Value{}
						_t1119.Value = &pb.Value_Uint128Value{Uint128Value: uint128565}
						_t1118 = _t1119
					} else {
						var _t1120 *pb.Value
						if prediction559 == 4 {
							float564 := p.consumeTerminal("FLOAT").Value.f64
							_t1121 := &pb.Value{}
							_t1121.Value = &pb.Value_FloatValue{FloatValue: float564}
							_t1120 = _t1121
						} else {
							var _t1122 *pb.Value
							if prediction559 == 3 {
								int563 := p.consumeTerminal("INT").Value.i64
								_t1123 := &pb.Value{}
								_t1123.Value = &pb.Value_IntValue{IntValue: int563}
								_t1122 = _t1123
							} else {
								var _t1124 *pb.Value
								if prediction559 == 2 {
									string562 := p.consumeTerminal("STRING").Value.str
									_t1125 := &pb.Value{}
									_t1125.Value = &pb.Value_StringValue{StringValue: string562}
									_t1124 = _t1125
								} else {
									var _t1126 *pb.Value
									if prediction559 == 1 {
										_t1127 := p.parse_datetime()
										datetime561 := _t1127
										_t1128 := &pb.Value{}
										_t1128.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime561}
										_t1126 = _t1128
									} else {
										var _t1129 *pb.Value
										if prediction559 == 0 {
											_t1130 := p.parse_date()
											date560 := _t1130
											_t1131 := &pb.Value{}
											_t1131.Value = &pb.Value_DateValue{DateValue: date560}
											_t1129 = _t1131
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1126 = _t1129
									}
									_t1124 = _t1126
								}
								_t1122 = _t1124
							}
							_t1120 = _t1122
						}
						_t1118 = _t1120
					}
					_t1116 = _t1118
				}
				_t1114 = _t1116
			}
			_t1111 = _t1114
		}
		_t1108 = _t1111
	}
	result570 := _t1108
	p.recordSpan(int(span_start569), "Value")
	return result570
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start574 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int571 := p.consumeTerminal("INT").Value.i64
	int_3572 := p.consumeTerminal("INT").Value.i64
	int_4573 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1132 := &pb.DateValue{Year: int32(int571), Month: int32(int_3572), Day: int32(int_4573)}
	result575 := _t1132
	p.recordSpan(int(span_start574), "DateValue")
	return result575
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start583 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int576 := p.consumeTerminal("INT").Value.i64
	int_3577 := p.consumeTerminal("INT").Value.i64
	int_4578 := p.consumeTerminal("INT").Value.i64
	int_5579 := p.consumeTerminal("INT").Value.i64
	int_6580 := p.consumeTerminal("INT").Value.i64
	int_7581 := p.consumeTerminal("INT").Value.i64
	var _t1133 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1133 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8582 := _t1133
	p.consumeLiteral(")")
	_t1134 := &pb.DateTimeValue{Year: int32(int576), Month: int32(int_3577), Day: int32(int_4578), Hour: int32(int_5579), Minute: int32(int_6580), Second: int32(int_7581), Microsecond: int32(deref(int_8582, 0))}
	result584 := _t1134
	p.recordSpan(int(span_start583), "DateTimeValue")
	return result584
}

func (p *Parser) parse_boolean_value() bool {
	var _t1135 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1135 = 0
	} else {
		var _t1136 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1136 = 1
		} else {
			_t1136 = -1
		}
		_t1135 = _t1136
	}
	prediction585 := _t1135
	var _t1137 bool
	if prediction585 == 1 {
		p.consumeLiteral("false")
		_t1137 = false
	} else {
		var _t1138 bool
		if prediction585 == 0 {
			p.consumeLiteral("true")
			_t1138 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1137 = _t1138
	}
	return _t1137
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start590 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs586 := []*pb.FragmentId{}
	cond587 := p.matchLookaheadLiteral(":", 0)
	for cond587 {
		_t1139 := p.parse_fragment_id()
		item588 := _t1139
		xs586 = append(xs586, item588)
		cond587 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids589 := xs586
	p.consumeLiteral(")")
	_t1140 := &pb.Sync{Fragments: fragment_ids589}
	result591 := _t1140
	p.recordSpan(int(span_start590), "Sync")
	return result591
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start593 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol592 := p.consumeTerminal("SYMBOL").Value.str
	result594 := &pb.FragmentId{Id: []byte(symbol592)}
	p.recordSpan(int(span_start593), "FragmentId")
	return result594
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start597 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1141 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1142 := p.parse_epoch_writes()
		_t1141 = _t1142
	}
	epoch_writes595 := _t1141
	var _t1143 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1144 := p.parse_epoch_reads()
		_t1143 = _t1144
	}
	epoch_reads596 := _t1143
	p.consumeLiteral(")")
	_t1145 := epoch_writes595
	if epoch_writes595 == nil {
		_t1145 = []*pb.Write{}
	}
	_t1146 := epoch_reads596
	if epoch_reads596 == nil {
		_t1146 = []*pb.Read{}
	}
	_t1147 := &pb.Epoch{Writes: _t1145, Reads: _t1146}
	result598 := _t1147
	p.recordSpan(int(span_start597), "Epoch")
	return result598
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs599 := []*pb.Write{}
	cond600 := p.matchLookaheadLiteral("(", 0)
	for cond600 {
		_t1148 := p.parse_write()
		item601 := _t1148
		xs599 = append(xs599, item601)
		cond600 = p.matchLookaheadLiteral("(", 0)
	}
	writes602 := xs599
	p.consumeLiteral(")")
	return writes602
}

func (p *Parser) parse_write() *pb.Write {
	span_start608 := int64(p.spanStart())
	var _t1149 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1150 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1150 = 1
		} else {
			var _t1151 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1151 = 3
			} else {
				var _t1152 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1152 = 0
				} else {
					var _t1153 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1153 = 2
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
	} else {
		_t1149 = -1
	}
	prediction603 := _t1149
	var _t1154 *pb.Write
	if prediction603 == 3 {
		_t1155 := p.parse_snapshot()
		snapshot607 := _t1155
		_t1156 := &pb.Write{}
		_t1156.WriteType = &pb.Write_Snapshot{Snapshot: snapshot607}
		_t1154 = _t1156
	} else {
		var _t1157 *pb.Write
		if prediction603 == 2 {
			_t1158 := p.parse_context()
			context606 := _t1158
			_t1159 := &pb.Write{}
			_t1159.WriteType = &pb.Write_Context{Context: context606}
			_t1157 = _t1159
		} else {
			var _t1160 *pb.Write
			if prediction603 == 1 {
				_t1161 := p.parse_undefine()
				undefine605 := _t1161
				_t1162 := &pb.Write{}
				_t1162.WriteType = &pb.Write_Undefine{Undefine: undefine605}
				_t1160 = _t1162
			} else {
				var _t1163 *pb.Write
				if prediction603 == 0 {
					_t1164 := p.parse_define()
					define604 := _t1164
					_t1165 := &pb.Write{}
					_t1165.WriteType = &pb.Write_Define{Define: define604}
					_t1163 = _t1165
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1160 = _t1163
			}
			_t1157 = _t1160
		}
		_t1154 = _t1157
	}
	result609 := _t1154
	p.recordSpan(int(span_start608), "Write")
	return result609
}

func (p *Parser) parse_define() *pb.Define {
	span_start611 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1166 := p.parse_fragment()
	fragment610 := _t1166
	p.consumeLiteral(")")
	_t1167 := &pb.Define{Fragment: fragment610}
	result612 := _t1167
	p.recordSpan(int(span_start611), "Define")
	return result612
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start618 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1168 := p.parse_new_fragment_id()
	new_fragment_id613 := _t1168
	xs614 := []*pb.Declaration{}
	cond615 := p.matchLookaheadLiteral("(", 0)
	for cond615 {
		_t1169 := p.parse_declaration()
		item616 := _t1169
		xs614 = append(xs614, item616)
		cond615 = p.matchLookaheadLiteral("(", 0)
	}
	declarations617 := xs614
	p.consumeLiteral(")")
	result619 := p.constructFragment(new_fragment_id613, declarations617)
	p.recordSpan(int(span_start618), "Fragment")
	return result619
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start621 := int64(p.spanStart())
	_t1170 := p.parse_fragment_id()
	fragment_id620 := _t1170
	p.startFragment(fragment_id620)
	result622 := fragment_id620
	p.recordSpan(int(span_start621), "FragmentId")
	return result622
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start628 := int64(p.spanStart())
	var _t1171 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1172 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1172 = 3
		} else {
			var _t1173 int64
			if p.matchLookaheadLiteral("functional_dependency", 1) {
				_t1173 = 2
			} else {
				var _t1174 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1174 = 0
				} else {
					var _t1175 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1175 = 3
					} else {
						var _t1176 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1176 = 3
						} else {
							var _t1177 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1177 = 1
							} else {
								_t1177 = -1
							}
							_t1176 = _t1177
						}
						_t1175 = _t1176
					}
					_t1174 = _t1175
				}
				_t1173 = _t1174
			}
			_t1172 = _t1173
		}
		_t1171 = _t1172
	} else {
		_t1171 = -1
	}
	prediction623 := _t1171
	var _t1178 *pb.Declaration
	if prediction623 == 3 {
		_t1179 := p.parse_data()
		data627 := _t1179
		_t1180 := &pb.Declaration{}
		_t1180.DeclarationType = &pb.Declaration_Data{Data: data627}
		_t1178 = _t1180
	} else {
		var _t1181 *pb.Declaration
		if prediction623 == 2 {
			_t1182 := p.parse_constraint()
			constraint626 := _t1182
			_t1183 := &pb.Declaration{}
			_t1183.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint626}
			_t1181 = _t1183
		} else {
			var _t1184 *pb.Declaration
			if prediction623 == 1 {
				_t1185 := p.parse_algorithm()
				algorithm625 := _t1185
				_t1186 := &pb.Declaration{}
				_t1186.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm625}
				_t1184 = _t1186
			} else {
				var _t1187 *pb.Declaration
				if prediction623 == 0 {
					_t1188 := p.parse_def()
					def624 := _t1188
					_t1189 := &pb.Declaration{}
					_t1189.DeclarationType = &pb.Declaration_Def{Def: def624}
					_t1187 = _t1189
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1184 = _t1187
			}
			_t1181 = _t1184
		}
		_t1178 = _t1181
	}
	result629 := _t1178
	p.recordSpan(int(span_start628), "Declaration")
	return result629
}

func (p *Parser) parse_def() *pb.Def {
	span_start633 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1190 := p.parse_relation_id()
	relation_id630 := _t1190
	_t1191 := p.parse_abstraction()
	abstraction631 := _t1191
	var _t1192 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1193 := p.parse_attrs()
		_t1192 = _t1193
	}
	attrs632 := _t1192
	p.consumeLiteral(")")
	_t1194 := attrs632
	if attrs632 == nil {
		_t1194 = []*pb.Attribute{}
	}
	_t1195 := &pb.Def{Name: relation_id630, Body: abstraction631, Attrs: _t1194}
	result634 := _t1195
	p.recordSpan(int(span_start633), "Def")
	return result634
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start638 := int64(p.spanStart())
	var _t1196 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1196 = 0
	} else {
		var _t1197 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1197 = 1
		} else {
			_t1197 = -1
		}
		_t1196 = _t1197
	}
	prediction635 := _t1196
	var _t1198 *pb.RelationId
	if prediction635 == 1 {
		uint128637 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128637
		_t1198 = &pb.RelationId{IdLow: uint128637.Low, IdHigh: uint128637.High}
	} else {
		var _t1199 *pb.RelationId
		if prediction635 == 0 {
			p.consumeLiteral(":")
			symbol636 := p.consumeTerminal("SYMBOL").Value.str
			_t1199 = p.relationIdFromString(symbol636)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1198 = _t1199
	}
	result639 := _t1198
	p.recordSpan(int(span_start638), "RelationId")
	return result639
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start642 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1200 := p.parse_bindings()
	bindings640 := _t1200
	_t1201 := p.parse_formula()
	formula641 := _t1201
	p.consumeLiteral(")")
	_t1202 := &pb.Abstraction{Vars: listConcat(bindings640[0].([]*pb.Binding), bindings640[1].([]*pb.Binding)), Value: formula641}
	result643 := _t1202
	p.recordSpan(int(span_start642), "Abstraction")
	return result643
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs644 := []*pb.Binding{}
	cond645 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond645 {
		_t1203 := p.parse_binding()
		item646 := _t1203
		xs644 = append(xs644, item646)
		cond645 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings647 := xs644
	var _t1204 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1205 := p.parse_value_bindings()
		_t1204 = _t1205
	}
	value_bindings648 := _t1204
	p.consumeLiteral("]")
	_t1206 := value_bindings648
	if value_bindings648 == nil {
		_t1206 = []*pb.Binding{}
	}
	return []interface{}{bindings647, _t1206}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start651 := int64(p.spanStart())
	symbol649 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1207 := p.parse_type()
	type650 := _t1207
	_t1208 := &pb.Var{Name: symbol649}
	_t1209 := &pb.Binding{Var: _t1208, Type: type650}
	result652 := _t1209
	p.recordSpan(int(span_start651), "Binding")
	return result652
}

func (p *Parser) parse_type() *pb.Type {
	span_start665 := int64(p.spanStart())
	var _t1210 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1210 = 0
	} else {
		var _t1211 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1211 = 4
		} else {
			var _t1212 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1212 = 1
			} else {
				var _t1213 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1213 = 8
				} else {
					var _t1214 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1214 = 5
					} else {
						var _t1215 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1215 = 2
						} else {
							var _t1216 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1216 = 3
							} else {
								var _t1217 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1217 = 7
								} else {
									var _t1218 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1218 = 6
									} else {
										var _t1219 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1219 = 10
										} else {
											var _t1220 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1220 = 9
											} else {
												_t1220 = -1
											}
											_t1219 = _t1220
										}
										_t1218 = _t1219
									}
									_t1217 = _t1218
								}
								_t1216 = _t1217
							}
							_t1215 = _t1216
						}
						_t1214 = _t1215
					}
					_t1213 = _t1214
				}
				_t1212 = _t1213
			}
			_t1211 = _t1212
		}
		_t1210 = _t1211
	}
	prediction653 := _t1210
	var _t1221 *pb.Type
	if prediction653 == 10 {
		_t1222 := p.parse_boolean_type()
		boolean_type664 := _t1222
		_t1223 := &pb.Type{}
		_t1223.Type = &pb.Type_BooleanType{BooleanType: boolean_type664}
		_t1221 = _t1223
	} else {
		var _t1224 *pb.Type
		if prediction653 == 9 {
			_t1225 := p.parse_decimal_type()
			decimal_type663 := _t1225
			_t1226 := &pb.Type{}
			_t1226.Type = &pb.Type_DecimalType{DecimalType: decimal_type663}
			_t1224 = _t1226
		} else {
			var _t1227 *pb.Type
			if prediction653 == 8 {
				_t1228 := p.parse_missing_type()
				missing_type662 := _t1228
				_t1229 := &pb.Type{}
				_t1229.Type = &pb.Type_MissingType{MissingType: missing_type662}
				_t1227 = _t1229
			} else {
				var _t1230 *pb.Type
				if prediction653 == 7 {
					_t1231 := p.parse_datetime_type()
					datetime_type661 := _t1231
					_t1232 := &pb.Type{}
					_t1232.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type661}
					_t1230 = _t1232
				} else {
					var _t1233 *pb.Type
					if prediction653 == 6 {
						_t1234 := p.parse_date_type()
						date_type660 := _t1234
						_t1235 := &pb.Type{}
						_t1235.Type = &pb.Type_DateType{DateType: date_type660}
						_t1233 = _t1235
					} else {
						var _t1236 *pb.Type
						if prediction653 == 5 {
							_t1237 := p.parse_int128_type()
							int128_type659 := _t1237
							_t1238 := &pb.Type{}
							_t1238.Type = &pb.Type_Int128Type{Int128Type: int128_type659}
							_t1236 = _t1238
						} else {
							var _t1239 *pb.Type
							if prediction653 == 4 {
								_t1240 := p.parse_uint128_type()
								uint128_type658 := _t1240
								_t1241 := &pb.Type{}
								_t1241.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type658}
								_t1239 = _t1241
							} else {
								var _t1242 *pb.Type
								if prediction653 == 3 {
									_t1243 := p.parse_float_type()
									float_type657 := _t1243
									_t1244 := &pb.Type{}
									_t1244.Type = &pb.Type_FloatType{FloatType: float_type657}
									_t1242 = _t1244
								} else {
									var _t1245 *pb.Type
									if prediction653 == 2 {
										_t1246 := p.parse_int_type()
										int_type656 := _t1246
										_t1247 := &pb.Type{}
										_t1247.Type = &pb.Type_IntType{IntType: int_type656}
										_t1245 = _t1247
									} else {
										var _t1248 *pb.Type
										if prediction653 == 1 {
											_t1249 := p.parse_string_type()
											string_type655 := _t1249
											_t1250 := &pb.Type{}
											_t1250.Type = &pb.Type_StringType{StringType: string_type655}
											_t1248 = _t1250
										} else {
											var _t1251 *pb.Type
											if prediction653 == 0 {
												_t1252 := p.parse_unspecified_type()
												unspecified_type654 := _t1252
												_t1253 := &pb.Type{}
												_t1253.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type654}
												_t1251 = _t1253
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t1248 = _t1251
										}
										_t1245 = _t1248
									}
									_t1242 = _t1245
								}
								_t1239 = _t1242
							}
							_t1236 = _t1239
						}
						_t1233 = _t1236
					}
					_t1230 = _t1233
				}
				_t1227 = _t1230
			}
			_t1224 = _t1227
		}
		_t1221 = _t1224
	}
	result666 := _t1221
	p.recordSpan(int(span_start665), "Type")
	return result666
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start667 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1254 := &pb.UnspecifiedType{}
	result668 := _t1254
	p.recordSpan(int(span_start667), "UnspecifiedType")
	return result668
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start669 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1255 := &pb.StringType{}
	result670 := _t1255
	p.recordSpan(int(span_start669), "StringType")
	return result670
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start671 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1256 := &pb.IntType{}
	result672 := _t1256
	p.recordSpan(int(span_start671), "IntType")
	return result672
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start673 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1257 := &pb.FloatType{}
	result674 := _t1257
	p.recordSpan(int(span_start673), "FloatType")
	return result674
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start675 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1258 := &pb.UInt128Type{}
	result676 := _t1258
	p.recordSpan(int(span_start675), "UInt128Type")
	return result676
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start677 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1259 := &pb.Int128Type{}
	result678 := _t1259
	p.recordSpan(int(span_start677), "Int128Type")
	return result678
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start679 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1260 := &pb.DateType{}
	result680 := _t1260
	p.recordSpan(int(span_start679), "DateType")
	return result680
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start681 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1261 := &pb.DateTimeType{}
	result682 := _t1261
	p.recordSpan(int(span_start681), "DateTimeType")
	return result682
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start683 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1262 := &pb.MissingType{}
	result684 := _t1262
	p.recordSpan(int(span_start683), "MissingType")
	return result684
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start687 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int685 := p.consumeTerminal("INT").Value.i64
	int_3686 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1263 := &pb.DecimalType{Precision: int32(int685), Scale: int32(int_3686)}
	result688 := _t1263
	p.recordSpan(int(span_start687), "DecimalType")
	return result688
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start689 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1264 := &pb.BooleanType{}
	result690 := _t1264
	p.recordSpan(int(span_start689), "BooleanType")
	return result690
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs691 := []*pb.Binding{}
	cond692 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond692 {
		_t1265 := p.parse_binding()
		item693 := _t1265
		xs691 = append(xs691, item693)
		cond692 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings694 := xs691
	return bindings694
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start709 := int64(p.spanStart())
	var _t1266 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1267 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1267 = 0
		} else {
			var _t1268 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1268 = 11
			} else {
				var _t1269 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1269 = 3
				} else {
					var _t1270 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1270 = 10
					} else {
						var _t1271 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1271 = 9
						} else {
							var _t1272 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1272 = 5
							} else {
								var _t1273 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1273 = 6
								} else {
									var _t1274 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1274 = 7
									} else {
										var _t1275 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1275 = 1
										} else {
											var _t1276 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1276 = 2
											} else {
												var _t1277 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1277 = 12
												} else {
													var _t1278 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1278 = 8
													} else {
														var _t1279 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1279 = 4
														} else {
															var _t1280 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1280 = 10
															} else {
																var _t1281 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1281 = 10
																} else {
																	var _t1282 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1282 = 10
																	} else {
																		var _t1283 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1283 = 10
																		} else {
																			var _t1284 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1284 = 10
																			} else {
																				var _t1285 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1285 = 10
																				} else {
																					var _t1286 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1286 = 10
																					} else {
																						var _t1287 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1287 = 10
																						} else {
																							var _t1288 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1288 = 10
																							} else {
																								_t1288 = -1
																							}
																							_t1287 = _t1288
																						}
																						_t1286 = _t1287
																					}
																					_t1285 = _t1286
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
															}
															_t1279 = _t1280
														}
														_t1278 = _t1279
													}
													_t1277 = _t1278
												}
												_t1276 = _t1277
											}
											_t1275 = _t1276
										}
										_t1274 = _t1275
									}
									_t1273 = _t1274
								}
								_t1272 = _t1273
							}
							_t1271 = _t1272
						}
						_t1270 = _t1271
					}
					_t1269 = _t1270
				}
				_t1268 = _t1269
			}
			_t1267 = _t1268
		}
		_t1266 = _t1267
	} else {
		_t1266 = -1
	}
	prediction695 := _t1266
	var _t1289 *pb.Formula
	if prediction695 == 12 {
		_t1290 := p.parse_cast()
		cast708 := _t1290
		_t1291 := &pb.Formula{}
		_t1291.FormulaType = &pb.Formula_Cast{Cast: cast708}
		_t1289 = _t1291
	} else {
		var _t1292 *pb.Formula
		if prediction695 == 11 {
			_t1293 := p.parse_rel_atom()
			rel_atom707 := _t1293
			_t1294 := &pb.Formula{}
			_t1294.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom707}
			_t1292 = _t1294
		} else {
			var _t1295 *pb.Formula
			if prediction695 == 10 {
				_t1296 := p.parse_primitive()
				primitive706 := _t1296
				_t1297 := &pb.Formula{}
				_t1297.FormulaType = &pb.Formula_Primitive{Primitive: primitive706}
				_t1295 = _t1297
			} else {
				var _t1298 *pb.Formula
				if prediction695 == 9 {
					_t1299 := p.parse_pragma()
					pragma705 := _t1299
					_t1300 := &pb.Formula{}
					_t1300.FormulaType = &pb.Formula_Pragma{Pragma: pragma705}
					_t1298 = _t1300
				} else {
					var _t1301 *pb.Formula
					if prediction695 == 8 {
						_t1302 := p.parse_atom()
						atom704 := _t1302
						_t1303 := &pb.Formula{}
						_t1303.FormulaType = &pb.Formula_Atom{Atom: atom704}
						_t1301 = _t1303
					} else {
						var _t1304 *pb.Formula
						if prediction695 == 7 {
							_t1305 := p.parse_ffi()
							ffi703 := _t1305
							_t1306 := &pb.Formula{}
							_t1306.FormulaType = &pb.Formula_Ffi{Ffi: ffi703}
							_t1304 = _t1306
						} else {
							var _t1307 *pb.Formula
							if prediction695 == 6 {
								_t1308 := p.parse_not()
								not702 := _t1308
								_t1309 := &pb.Formula{}
								_t1309.FormulaType = &pb.Formula_Not{Not: not702}
								_t1307 = _t1309
							} else {
								var _t1310 *pb.Formula
								if prediction695 == 5 {
									_t1311 := p.parse_disjunction()
									disjunction701 := _t1311
									_t1312 := &pb.Formula{}
									_t1312.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction701}
									_t1310 = _t1312
								} else {
									var _t1313 *pb.Formula
									if prediction695 == 4 {
										_t1314 := p.parse_conjunction()
										conjunction700 := _t1314
										_t1315 := &pb.Formula{}
										_t1315.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction700}
										_t1313 = _t1315
									} else {
										var _t1316 *pb.Formula
										if prediction695 == 3 {
											_t1317 := p.parse_reduce()
											reduce699 := _t1317
											_t1318 := &pb.Formula{}
											_t1318.FormulaType = &pb.Formula_Reduce{Reduce: reduce699}
											_t1316 = _t1318
										} else {
											var _t1319 *pb.Formula
											if prediction695 == 2 {
												_t1320 := p.parse_exists()
												exists698 := _t1320
												_t1321 := &pb.Formula{}
												_t1321.FormulaType = &pb.Formula_Exists{Exists: exists698}
												_t1319 = _t1321
											} else {
												var _t1322 *pb.Formula
												if prediction695 == 1 {
													_t1323 := p.parse_false()
													false697 := _t1323
													_t1324 := &pb.Formula{}
													_t1324.FormulaType = &pb.Formula_Disjunction{Disjunction: false697}
													_t1322 = _t1324
												} else {
													var _t1325 *pb.Formula
													if prediction695 == 0 {
														_t1326 := p.parse_true()
														true696 := _t1326
														_t1327 := &pb.Formula{}
														_t1327.FormulaType = &pb.Formula_Conjunction{Conjunction: true696}
														_t1325 = _t1327
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1322 = _t1325
												}
												_t1319 = _t1322
											}
											_t1316 = _t1319
										}
										_t1313 = _t1316
									}
									_t1310 = _t1313
								}
								_t1307 = _t1310
							}
							_t1304 = _t1307
						}
						_t1301 = _t1304
					}
					_t1298 = _t1301
				}
				_t1295 = _t1298
			}
			_t1292 = _t1295
		}
		_t1289 = _t1292
	}
	result710 := _t1289
	p.recordSpan(int(span_start709), "Formula")
	return result710
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1328 := &pb.Conjunction{Args: []*pb.Formula{}}
	result712 := _t1328
	p.recordSpan(int(span_start711), "Conjunction")
	return result712
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1329 := &pb.Disjunction{Args: []*pb.Formula{}}
	result714 := _t1329
	p.recordSpan(int(span_start713), "Disjunction")
	return result714
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start717 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1330 := p.parse_bindings()
	bindings715 := _t1330
	_t1331 := p.parse_formula()
	formula716 := _t1331
	p.consumeLiteral(")")
	_t1332 := &pb.Abstraction{Vars: listConcat(bindings715[0].([]*pb.Binding), bindings715[1].([]*pb.Binding)), Value: formula716}
	_t1333 := &pb.Exists{Body: _t1332}
	result718 := _t1333
	p.recordSpan(int(span_start717), "Exists")
	return result718
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start722 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1334 := p.parse_abstraction()
	abstraction719 := _t1334
	_t1335 := p.parse_abstraction()
	abstraction_3720 := _t1335
	_t1336 := p.parse_terms()
	terms721 := _t1336
	p.consumeLiteral(")")
	_t1337 := &pb.Reduce{Op: abstraction719, Body: abstraction_3720, Terms: terms721}
	result723 := _t1337
	p.recordSpan(int(span_start722), "Reduce")
	return result723
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs724 := []*pb.Term{}
	cond725 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond725 {
		_t1338 := p.parse_term()
		item726 := _t1338
		xs724 = append(xs724, item726)
		cond725 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms727 := xs724
	p.consumeLiteral(")")
	return terms727
}

func (p *Parser) parse_term() *pb.Term {
	span_start731 := int64(p.spanStart())
	var _t1339 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1339 = 1
	} else {
		var _t1340 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1340 = 1
		} else {
			var _t1341 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1341 = 1
			} else {
				var _t1342 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1342 = 1
				} else {
					var _t1343 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1343 = 1
					} else {
						var _t1344 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1344 = 0
						} else {
							var _t1345 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1345 = 1
							} else {
								var _t1346 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1346 = 1
								} else {
									var _t1347 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1347 = 1
									} else {
										var _t1348 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1348 = 1
										} else {
											var _t1349 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1349 = 1
											} else {
												_t1349 = -1
											}
											_t1348 = _t1349
										}
										_t1347 = _t1348
									}
									_t1346 = _t1347
								}
								_t1345 = _t1346
							}
							_t1344 = _t1345
						}
						_t1343 = _t1344
					}
					_t1342 = _t1343
				}
				_t1341 = _t1342
			}
			_t1340 = _t1341
		}
		_t1339 = _t1340
	}
	prediction728 := _t1339
	var _t1350 *pb.Term
	if prediction728 == 1 {
		_t1351 := p.parse_constant()
		constant730 := _t1351
		_t1352 := &pb.Term{}
		_t1352.TermType = &pb.Term_Constant{Constant: constant730}
		_t1350 = _t1352
	} else {
		var _t1353 *pb.Term
		if prediction728 == 0 {
			_t1354 := p.parse_var()
			var729 := _t1354
			_t1355 := &pb.Term{}
			_t1355.TermType = &pb.Term_Var{Var: var729}
			_t1353 = _t1355
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1350 = _t1353
	}
	result732 := _t1350
	p.recordSpan(int(span_start731), "Term")
	return result732
}

func (p *Parser) parse_var() *pb.Var {
	span_start734 := int64(p.spanStart())
	symbol733 := p.consumeTerminal("SYMBOL").Value.str
	_t1356 := &pb.Var{Name: symbol733}
	result735 := _t1356
	p.recordSpan(int(span_start734), "Var")
	return result735
}

func (p *Parser) parse_constant() *pb.Value {
	span_start737 := int64(p.spanStart())
	_t1357 := p.parse_value()
	value736 := _t1357
	result738 := value736
	p.recordSpan(int(span_start737), "Value")
	return result738
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start743 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs739 := []*pb.Formula{}
	cond740 := p.matchLookaheadLiteral("(", 0)
	for cond740 {
		_t1358 := p.parse_formula()
		item741 := _t1358
		xs739 = append(xs739, item741)
		cond740 = p.matchLookaheadLiteral("(", 0)
	}
	formulas742 := xs739
	p.consumeLiteral(")")
	_t1359 := &pb.Conjunction{Args: formulas742}
	result744 := _t1359
	p.recordSpan(int(span_start743), "Conjunction")
	return result744
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start749 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs745 := []*pb.Formula{}
	cond746 := p.matchLookaheadLiteral("(", 0)
	for cond746 {
		_t1360 := p.parse_formula()
		item747 := _t1360
		xs745 = append(xs745, item747)
		cond746 = p.matchLookaheadLiteral("(", 0)
	}
	formulas748 := xs745
	p.consumeLiteral(")")
	_t1361 := &pb.Disjunction{Args: formulas748}
	result750 := _t1361
	p.recordSpan(int(span_start749), "Disjunction")
	return result750
}

func (p *Parser) parse_not() *pb.Not {
	span_start752 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1362 := p.parse_formula()
	formula751 := _t1362
	p.consumeLiteral(")")
	_t1363 := &pb.Not{Arg: formula751}
	result753 := _t1363
	p.recordSpan(int(span_start752), "Not")
	return result753
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start757 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1364 := p.parse_name()
	name754 := _t1364
	_t1365 := p.parse_ffi_args()
	ffi_args755 := _t1365
	_t1366 := p.parse_terms()
	terms756 := _t1366
	p.consumeLiteral(")")
	_t1367 := &pb.FFI{Name: name754, Args: ffi_args755, Terms: terms756}
	result758 := _t1367
	p.recordSpan(int(span_start757), "FFI")
	return result758
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol759 := p.consumeTerminal("SYMBOL").Value.str
	return symbol759
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs760 := []*pb.Abstraction{}
	cond761 := p.matchLookaheadLiteral("(", 0)
	for cond761 {
		_t1368 := p.parse_abstraction()
		item762 := _t1368
		xs760 = append(xs760, item762)
		cond761 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions763 := xs760
	p.consumeLiteral(")")
	return abstractions763
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start769 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1369 := p.parse_relation_id()
	relation_id764 := _t1369
	xs765 := []*pb.Term{}
	cond766 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond766 {
		_t1370 := p.parse_term()
		item767 := _t1370
		xs765 = append(xs765, item767)
		cond766 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms768 := xs765
	p.consumeLiteral(")")
	_t1371 := &pb.Atom{Name: relation_id764, Terms: terms768}
	result770 := _t1371
	p.recordSpan(int(span_start769), "Atom")
	return result770
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1372 := p.parse_name()
	name771 := _t1372
	xs772 := []*pb.Term{}
	cond773 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond773 {
		_t1373 := p.parse_term()
		item774 := _t1373
		xs772 = append(xs772, item774)
		cond773 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms775 := xs772
	p.consumeLiteral(")")
	_t1374 := &pb.Pragma{Name: name771, Terms: terms775}
	result777 := _t1374
	p.recordSpan(int(span_start776), "Pragma")
	return result777
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start793 := int64(p.spanStart())
	var _t1375 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1376 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1376 = 9
		} else {
			var _t1377 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1377 = 4
			} else {
				var _t1378 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1378 = 3
				} else {
					var _t1379 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1379 = 0
					} else {
						var _t1380 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1380 = 2
						} else {
							var _t1381 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1381 = 1
							} else {
								var _t1382 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1382 = 8
								} else {
									var _t1383 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1383 = 6
									} else {
										var _t1384 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1384 = 5
										} else {
											var _t1385 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1385 = 7
											} else {
												_t1385 = -1
											}
											_t1384 = _t1385
										}
										_t1383 = _t1384
									}
									_t1382 = _t1383
								}
								_t1381 = _t1382
							}
							_t1380 = _t1381
						}
						_t1379 = _t1380
					}
					_t1378 = _t1379
				}
				_t1377 = _t1378
			}
			_t1376 = _t1377
		}
		_t1375 = _t1376
	} else {
		_t1375 = -1
	}
	prediction778 := _t1375
	var _t1386 *pb.Primitive
	if prediction778 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1387 := p.parse_name()
		name788 := _t1387
		xs789 := []*pb.RelTerm{}
		cond790 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond790 {
			_t1388 := p.parse_rel_term()
			item791 := _t1388
			xs789 = append(xs789, item791)
			cond790 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms792 := xs789
		p.consumeLiteral(")")
		_t1389 := &pb.Primitive{Name: name788, Terms: rel_terms792}
		_t1386 = _t1389
	} else {
		var _t1390 *pb.Primitive
		if prediction778 == 8 {
			_t1391 := p.parse_divide()
			divide787 := _t1391
			_t1390 = divide787
		} else {
			var _t1392 *pb.Primitive
			if prediction778 == 7 {
				_t1393 := p.parse_multiply()
				multiply786 := _t1393
				_t1392 = multiply786
			} else {
				var _t1394 *pb.Primitive
				if prediction778 == 6 {
					_t1395 := p.parse_minus()
					minus785 := _t1395
					_t1394 = minus785
				} else {
					var _t1396 *pb.Primitive
					if prediction778 == 5 {
						_t1397 := p.parse_add()
						add784 := _t1397
						_t1396 = add784
					} else {
						var _t1398 *pb.Primitive
						if prediction778 == 4 {
							_t1399 := p.parse_gt_eq()
							gt_eq783 := _t1399
							_t1398 = gt_eq783
						} else {
							var _t1400 *pb.Primitive
							if prediction778 == 3 {
								_t1401 := p.parse_gt()
								gt782 := _t1401
								_t1400 = gt782
							} else {
								var _t1402 *pb.Primitive
								if prediction778 == 2 {
									_t1403 := p.parse_lt_eq()
									lt_eq781 := _t1403
									_t1402 = lt_eq781
								} else {
									var _t1404 *pb.Primitive
									if prediction778 == 1 {
										_t1405 := p.parse_lt()
										lt780 := _t1405
										_t1404 = lt780
									} else {
										var _t1406 *pb.Primitive
										if prediction778 == 0 {
											_t1407 := p.parse_eq()
											eq779 := _t1407
											_t1406 = eq779
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1404 = _t1406
									}
									_t1402 = _t1404
								}
								_t1400 = _t1402
							}
							_t1398 = _t1400
						}
						_t1396 = _t1398
					}
					_t1394 = _t1396
				}
				_t1392 = _t1394
			}
			_t1390 = _t1392
		}
		_t1386 = _t1390
	}
	result794 := _t1386
	p.recordSpan(int(span_start793), "Primitive")
	return result794
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start797 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1408 := p.parse_term()
	term795 := _t1408
	_t1409 := p.parse_term()
	term_3796 := _t1409
	p.consumeLiteral(")")
	_t1410 := &pb.RelTerm{}
	_t1410.RelTermType = &pb.RelTerm_Term{Term: term795}
	_t1411 := &pb.RelTerm{}
	_t1411.RelTermType = &pb.RelTerm_Term{Term: term_3796}
	_t1412 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1410, _t1411}}
	result798 := _t1412
	p.recordSpan(int(span_start797), "Primitive")
	return result798
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start801 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1413 := p.parse_term()
	term799 := _t1413
	_t1414 := p.parse_term()
	term_3800 := _t1414
	p.consumeLiteral(")")
	_t1415 := &pb.RelTerm{}
	_t1415.RelTermType = &pb.RelTerm_Term{Term: term799}
	_t1416 := &pb.RelTerm{}
	_t1416.RelTermType = &pb.RelTerm_Term{Term: term_3800}
	_t1417 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1415, _t1416}}
	result802 := _t1417
	p.recordSpan(int(span_start801), "Primitive")
	return result802
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start805 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1418 := p.parse_term()
	term803 := _t1418
	_t1419 := p.parse_term()
	term_3804 := _t1419
	p.consumeLiteral(")")
	_t1420 := &pb.RelTerm{}
	_t1420.RelTermType = &pb.RelTerm_Term{Term: term803}
	_t1421 := &pb.RelTerm{}
	_t1421.RelTermType = &pb.RelTerm_Term{Term: term_3804}
	_t1422 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1420, _t1421}}
	result806 := _t1422
	p.recordSpan(int(span_start805), "Primitive")
	return result806
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start809 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1423 := p.parse_term()
	term807 := _t1423
	_t1424 := p.parse_term()
	term_3808 := _t1424
	p.consumeLiteral(")")
	_t1425 := &pb.RelTerm{}
	_t1425.RelTermType = &pb.RelTerm_Term{Term: term807}
	_t1426 := &pb.RelTerm{}
	_t1426.RelTermType = &pb.RelTerm_Term{Term: term_3808}
	_t1427 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1425, _t1426}}
	result810 := _t1427
	p.recordSpan(int(span_start809), "Primitive")
	return result810
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start813 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1428 := p.parse_term()
	term811 := _t1428
	_t1429 := p.parse_term()
	term_3812 := _t1429
	p.consumeLiteral(")")
	_t1430 := &pb.RelTerm{}
	_t1430.RelTermType = &pb.RelTerm_Term{Term: term811}
	_t1431 := &pb.RelTerm{}
	_t1431.RelTermType = &pb.RelTerm_Term{Term: term_3812}
	_t1432 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1430, _t1431}}
	result814 := _t1432
	p.recordSpan(int(span_start813), "Primitive")
	return result814
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start818 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1433 := p.parse_term()
	term815 := _t1433
	_t1434 := p.parse_term()
	term_3816 := _t1434
	_t1435 := p.parse_term()
	term_4817 := _t1435
	p.consumeLiteral(")")
	_t1436 := &pb.RelTerm{}
	_t1436.RelTermType = &pb.RelTerm_Term{Term: term815}
	_t1437 := &pb.RelTerm{}
	_t1437.RelTermType = &pb.RelTerm_Term{Term: term_3816}
	_t1438 := &pb.RelTerm{}
	_t1438.RelTermType = &pb.RelTerm_Term{Term: term_4817}
	_t1439 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1436, _t1437, _t1438}}
	result819 := _t1439
	p.recordSpan(int(span_start818), "Primitive")
	return result819
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start823 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1440 := p.parse_term()
	term820 := _t1440
	_t1441 := p.parse_term()
	term_3821 := _t1441
	_t1442 := p.parse_term()
	term_4822 := _t1442
	p.consumeLiteral(")")
	_t1443 := &pb.RelTerm{}
	_t1443.RelTermType = &pb.RelTerm_Term{Term: term820}
	_t1444 := &pb.RelTerm{}
	_t1444.RelTermType = &pb.RelTerm_Term{Term: term_3821}
	_t1445 := &pb.RelTerm{}
	_t1445.RelTermType = &pb.RelTerm_Term{Term: term_4822}
	_t1446 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1443, _t1444, _t1445}}
	result824 := _t1446
	p.recordSpan(int(span_start823), "Primitive")
	return result824
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start828 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1447 := p.parse_term()
	term825 := _t1447
	_t1448 := p.parse_term()
	term_3826 := _t1448
	_t1449 := p.parse_term()
	term_4827 := _t1449
	p.consumeLiteral(")")
	_t1450 := &pb.RelTerm{}
	_t1450.RelTermType = &pb.RelTerm_Term{Term: term825}
	_t1451 := &pb.RelTerm{}
	_t1451.RelTermType = &pb.RelTerm_Term{Term: term_3826}
	_t1452 := &pb.RelTerm{}
	_t1452.RelTermType = &pb.RelTerm_Term{Term: term_4827}
	_t1453 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1450, _t1451, _t1452}}
	result829 := _t1453
	p.recordSpan(int(span_start828), "Primitive")
	return result829
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start833 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1454 := p.parse_term()
	term830 := _t1454
	_t1455 := p.parse_term()
	term_3831 := _t1455
	_t1456 := p.parse_term()
	term_4832 := _t1456
	p.consumeLiteral(")")
	_t1457 := &pb.RelTerm{}
	_t1457.RelTermType = &pb.RelTerm_Term{Term: term830}
	_t1458 := &pb.RelTerm{}
	_t1458.RelTermType = &pb.RelTerm_Term{Term: term_3831}
	_t1459 := &pb.RelTerm{}
	_t1459.RelTermType = &pb.RelTerm_Term{Term: term_4832}
	_t1460 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1457, _t1458, _t1459}}
	result834 := _t1460
	p.recordSpan(int(span_start833), "Primitive")
	return result834
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start838 := int64(p.spanStart())
	var _t1461 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1461 = 1
	} else {
		var _t1462 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1462 = 1
		} else {
			var _t1463 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1463 = 1
			} else {
				var _t1464 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1464 = 1
				} else {
					var _t1465 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1465 = 0
					} else {
						var _t1466 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1466 = 1
						} else {
							var _t1467 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1467 = 1
							} else {
								var _t1468 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1468 = 1
								} else {
									var _t1469 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1469 = 1
									} else {
										var _t1470 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1470 = 1
										} else {
											var _t1471 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1471 = 1
											} else {
												var _t1472 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1472 = 1
												} else {
													_t1472 = -1
												}
												_t1471 = _t1472
											}
											_t1470 = _t1471
										}
										_t1469 = _t1470
									}
									_t1468 = _t1469
								}
								_t1467 = _t1468
							}
							_t1466 = _t1467
						}
						_t1465 = _t1466
					}
					_t1464 = _t1465
				}
				_t1463 = _t1464
			}
			_t1462 = _t1463
		}
		_t1461 = _t1462
	}
	prediction835 := _t1461
	var _t1473 *pb.RelTerm
	if prediction835 == 1 {
		_t1474 := p.parse_term()
		term837 := _t1474
		_t1475 := &pb.RelTerm{}
		_t1475.RelTermType = &pb.RelTerm_Term{Term: term837}
		_t1473 = _t1475
	} else {
		var _t1476 *pb.RelTerm
		if prediction835 == 0 {
			_t1477 := p.parse_specialized_value()
			specialized_value836 := _t1477
			_t1478 := &pb.RelTerm{}
			_t1478.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value836}
			_t1476 = _t1478
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1473 = _t1476
	}
	result839 := _t1473
	p.recordSpan(int(span_start838), "RelTerm")
	return result839
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start841 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1479 := p.parse_value()
	value840 := _t1479
	result842 := value840
	p.recordSpan(int(span_start841), "Value")
	return result842
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start848 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1480 := p.parse_name()
	name843 := _t1480
	xs844 := []*pb.RelTerm{}
	cond845 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond845 {
		_t1481 := p.parse_rel_term()
		item846 := _t1481
		xs844 = append(xs844, item846)
		cond845 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms847 := xs844
	p.consumeLiteral(")")
	_t1482 := &pb.RelAtom{Name: name843, Terms: rel_terms847}
	result849 := _t1482
	p.recordSpan(int(span_start848), "RelAtom")
	return result849
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1483 := p.parse_term()
	term850 := _t1483
	_t1484 := p.parse_term()
	term_3851 := _t1484
	p.consumeLiteral(")")
	_t1485 := &pb.Cast{Input: term850, Result: term_3851}
	result853 := _t1485
	p.recordSpan(int(span_start852), "Cast")
	return result853
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs854 := []*pb.Attribute{}
	cond855 := p.matchLookaheadLiteral("(", 0)
	for cond855 {
		_t1486 := p.parse_attribute()
		item856 := _t1486
		xs854 = append(xs854, item856)
		cond855 = p.matchLookaheadLiteral("(", 0)
	}
	attributes857 := xs854
	p.consumeLiteral(")")
	return attributes857
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start863 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1487 := p.parse_name()
	name858 := _t1487
	xs859 := []*pb.Value{}
	cond860 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond860 {
		_t1488 := p.parse_value()
		item861 := _t1488
		xs859 = append(xs859, item861)
		cond860 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values862 := xs859
	p.consumeLiteral(")")
	_t1489 := &pb.Attribute{Name: name858, Args: values862}
	result864 := _t1489
	p.recordSpan(int(span_start863), "Attribute")
	return result864
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start870 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs865 := []*pb.RelationId{}
	cond866 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond866 {
		_t1490 := p.parse_relation_id()
		item867 := _t1490
		xs865 = append(xs865, item867)
		cond866 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids868 := xs865
	_t1491 := p.parse_script()
	script869 := _t1491
	p.consumeLiteral(")")
	_t1492 := &pb.Algorithm{Global: relation_ids868, Body: script869}
	result871 := _t1492
	p.recordSpan(int(span_start870), "Algorithm")
	return result871
}

func (p *Parser) parse_script() *pb.Script {
	span_start876 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs872 := []*pb.Construct{}
	cond873 := p.matchLookaheadLiteral("(", 0)
	for cond873 {
		_t1493 := p.parse_construct()
		item874 := _t1493
		xs872 = append(xs872, item874)
		cond873 = p.matchLookaheadLiteral("(", 0)
	}
	constructs875 := xs872
	p.consumeLiteral(")")
	_t1494 := &pb.Script{Constructs: constructs875}
	result877 := _t1494
	p.recordSpan(int(span_start876), "Script")
	return result877
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start881 := int64(p.spanStart())
	var _t1495 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1496 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1496 = 1
		} else {
			var _t1497 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1497 = 1
			} else {
				var _t1498 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1498 = 1
				} else {
					var _t1499 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1499 = 0
					} else {
						var _t1500 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1500 = 1
						} else {
							var _t1501 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1501 = 1
							} else {
								_t1501 = -1
							}
							_t1500 = _t1501
						}
						_t1499 = _t1500
					}
					_t1498 = _t1499
				}
				_t1497 = _t1498
			}
			_t1496 = _t1497
		}
		_t1495 = _t1496
	} else {
		_t1495 = -1
	}
	prediction878 := _t1495
	var _t1502 *pb.Construct
	if prediction878 == 1 {
		_t1503 := p.parse_instruction()
		instruction880 := _t1503
		_t1504 := &pb.Construct{}
		_t1504.ConstructType = &pb.Construct_Instruction{Instruction: instruction880}
		_t1502 = _t1504
	} else {
		var _t1505 *pb.Construct
		if prediction878 == 0 {
			_t1506 := p.parse_loop()
			loop879 := _t1506
			_t1507 := &pb.Construct{}
			_t1507.ConstructType = &pb.Construct_Loop{Loop: loop879}
			_t1505 = _t1507
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1502 = _t1505
	}
	result882 := _t1502
	p.recordSpan(int(span_start881), "Construct")
	return result882
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start885 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1508 := p.parse_init()
	init883 := _t1508
	_t1509 := p.parse_script()
	script884 := _t1509
	p.consumeLiteral(")")
	_t1510 := &pb.Loop{Init: init883, Body: script884}
	result886 := _t1510
	p.recordSpan(int(span_start885), "Loop")
	return result886
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs887 := []*pb.Instruction{}
	cond888 := p.matchLookaheadLiteral("(", 0)
	for cond888 {
		_t1511 := p.parse_instruction()
		item889 := _t1511
		xs887 = append(xs887, item889)
		cond888 = p.matchLookaheadLiteral("(", 0)
	}
	instructions890 := xs887
	p.consumeLiteral(")")
	return instructions890
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start897 := int64(p.spanStart())
	var _t1512 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1513 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1513 = 1
		} else {
			var _t1514 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1514 = 4
			} else {
				var _t1515 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1515 = 3
				} else {
					var _t1516 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1516 = 2
					} else {
						var _t1517 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1517 = 0
						} else {
							_t1517 = -1
						}
						_t1516 = _t1517
					}
					_t1515 = _t1516
				}
				_t1514 = _t1515
			}
			_t1513 = _t1514
		}
		_t1512 = _t1513
	} else {
		_t1512 = -1
	}
	prediction891 := _t1512
	var _t1518 *pb.Instruction
	if prediction891 == 4 {
		_t1519 := p.parse_monus_def()
		monus_def896 := _t1519
		_t1520 := &pb.Instruction{}
		_t1520.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def896}
		_t1518 = _t1520
	} else {
		var _t1521 *pb.Instruction
		if prediction891 == 3 {
			_t1522 := p.parse_monoid_def()
			monoid_def895 := _t1522
			_t1523 := &pb.Instruction{}
			_t1523.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def895}
			_t1521 = _t1523
		} else {
			var _t1524 *pb.Instruction
			if prediction891 == 2 {
				_t1525 := p.parse_break()
				break894 := _t1525
				_t1526 := &pb.Instruction{}
				_t1526.InstrType = &pb.Instruction_Break{Break: break894}
				_t1524 = _t1526
			} else {
				var _t1527 *pb.Instruction
				if prediction891 == 1 {
					_t1528 := p.parse_upsert()
					upsert893 := _t1528
					_t1529 := &pb.Instruction{}
					_t1529.InstrType = &pb.Instruction_Upsert{Upsert: upsert893}
					_t1527 = _t1529
				} else {
					var _t1530 *pb.Instruction
					if prediction891 == 0 {
						_t1531 := p.parse_assign()
						assign892 := _t1531
						_t1532 := &pb.Instruction{}
						_t1532.InstrType = &pb.Instruction_Assign{Assign: assign892}
						_t1530 = _t1532
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1527 = _t1530
				}
				_t1524 = _t1527
			}
			_t1521 = _t1524
		}
		_t1518 = _t1521
	}
	result898 := _t1518
	p.recordSpan(int(span_start897), "Instruction")
	return result898
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start902 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1533 := p.parse_relation_id()
	relation_id899 := _t1533
	_t1534 := p.parse_abstraction()
	abstraction900 := _t1534
	var _t1535 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1536 := p.parse_attrs()
		_t1535 = _t1536
	}
	attrs901 := _t1535
	p.consumeLiteral(")")
	_t1537 := attrs901
	if attrs901 == nil {
		_t1537 = []*pb.Attribute{}
	}
	_t1538 := &pb.Assign{Name: relation_id899, Body: abstraction900, Attrs: _t1537}
	result903 := _t1538
	p.recordSpan(int(span_start902), "Assign")
	return result903
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start907 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1539 := p.parse_relation_id()
	relation_id904 := _t1539
	_t1540 := p.parse_abstraction_with_arity()
	abstraction_with_arity905 := _t1540
	var _t1541 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1542 := p.parse_attrs()
		_t1541 = _t1542
	}
	attrs906 := _t1541
	p.consumeLiteral(")")
	_t1543 := attrs906
	if attrs906 == nil {
		_t1543 = []*pb.Attribute{}
	}
	_t1544 := &pb.Upsert{Name: relation_id904, Body: abstraction_with_arity905[0].(*pb.Abstraction), Attrs: _t1543, ValueArity: abstraction_with_arity905[1].(int64)}
	result908 := _t1544
	p.recordSpan(int(span_start907), "Upsert")
	return result908
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1545 := p.parse_bindings()
	bindings909 := _t1545
	_t1546 := p.parse_formula()
	formula910 := _t1546
	p.consumeLiteral(")")
	_t1547 := &pb.Abstraction{Vars: listConcat(bindings909[0].([]*pb.Binding), bindings909[1].([]*pb.Binding)), Value: formula910}
	return []interface{}{_t1547, int64(len(bindings909[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start914 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1548 := p.parse_relation_id()
	relation_id911 := _t1548
	_t1549 := p.parse_abstraction()
	abstraction912 := _t1549
	var _t1550 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1551 := p.parse_attrs()
		_t1550 = _t1551
	}
	attrs913 := _t1550
	p.consumeLiteral(")")
	_t1552 := attrs913
	if attrs913 == nil {
		_t1552 = []*pb.Attribute{}
	}
	_t1553 := &pb.Break{Name: relation_id911, Body: abstraction912, Attrs: _t1552}
	result915 := _t1553
	p.recordSpan(int(span_start914), "Break")
	return result915
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start920 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1554 := p.parse_monoid()
	monoid916 := _t1554
	_t1555 := p.parse_relation_id()
	relation_id917 := _t1555
	_t1556 := p.parse_abstraction_with_arity()
	abstraction_with_arity918 := _t1556
	var _t1557 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1558 := p.parse_attrs()
		_t1557 = _t1558
	}
	attrs919 := _t1557
	p.consumeLiteral(")")
	_t1559 := attrs919
	if attrs919 == nil {
		_t1559 = []*pb.Attribute{}
	}
	_t1560 := &pb.MonoidDef{Monoid: monoid916, Name: relation_id917, Body: abstraction_with_arity918[0].(*pb.Abstraction), Attrs: _t1559, ValueArity: abstraction_with_arity918[1].(int64)}
	result921 := _t1560
	p.recordSpan(int(span_start920), "MonoidDef")
	return result921
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start927 := int64(p.spanStart())
	var _t1561 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1562 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1562 = 3
		} else {
			var _t1563 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1563 = 0
			} else {
				var _t1564 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1564 = 1
				} else {
					var _t1565 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1565 = 2
					} else {
						_t1565 = -1
					}
					_t1564 = _t1565
				}
				_t1563 = _t1564
			}
			_t1562 = _t1563
		}
		_t1561 = _t1562
	} else {
		_t1561 = -1
	}
	prediction922 := _t1561
	var _t1566 *pb.Monoid
	if prediction922 == 3 {
		_t1567 := p.parse_sum_monoid()
		sum_monoid926 := _t1567
		_t1568 := &pb.Monoid{}
		_t1568.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid926}
		_t1566 = _t1568
	} else {
		var _t1569 *pb.Monoid
		if prediction922 == 2 {
			_t1570 := p.parse_max_monoid()
			max_monoid925 := _t1570
			_t1571 := &pb.Monoid{}
			_t1571.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid925}
			_t1569 = _t1571
		} else {
			var _t1572 *pb.Monoid
			if prediction922 == 1 {
				_t1573 := p.parse_min_monoid()
				min_monoid924 := _t1573
				_t1574 := &pb.Monoid{}
				_t1574.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid924}
				_t1572 = _t1574
			} else {
				var _t1575 *pb.Monoid
				if prediction922 == 0 {
					_t1576 := p.parse_or_monoid()
					or_monoid923 := _t1576
					_t1577 := &pb.Monoid{}
					_t1577.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid923}
					_t1575 = _t1577
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1572 = _t1575
			}
			_t1569 = _t1572
		}
		_t1566 = _t1569
	}
	result928 := _t1566
	p.recordSpan(int(span_start927), "Monoid")
	return result928
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start929 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1578 := &pb.OrMonoid{}
	result930 := _t1578
	p.recordSpan(int(span_start929), "OrMonoid")
	return result930
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start932 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1579 := p.parse_type()
	type931 := _t1579
	p.consumeLiteral(")")
	_t1580 := &pb.MinMonoid{Type: type931}
	result933 := _t1580
	p.recordSpan(int(span_start932), "MinMonoid")
	return result933
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start935 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1581 := p.parse_type()
	type934 := _t1581
	p.consumeLiteral(")")
	_t1582 := &pb.MaxMonoid{Type: type934}
	result936 := _t1582
	p.recordSpan(int(span_start935), "MaxMonoid")
	return result936
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start938 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1583 := p.parse_type()
	type937 := _t1583
	p.consumeLiteral(")")
	_t1584 := &pb.SumMonoid{Type: type937}
	result939 := _t1584
	p.recordSpan(int(span_start938), "SumMonoid")
	return result939
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start944 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1585 := p.parse_monoid()
	monoid940 := _t1585
	_t1586 := p.parse_relation_id()
	relation_id941 := _t1586
	_t1587 := p.parse_abstraction_with_arity()
	abstraction_with_arity942 := _t1587
	var _t1588 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1589 := p.parse_attrs()
		_t1588 = _t1589
	}
	attrs943 := _t1588
	p.consumeLiteral(")")
	_t1590 := attrs943
	if attrs943 == nil {
		_t1590 = []*pb.Attribute{}
	}
	_t1591 := &pb.MonusDef{Monoid: monoid940, Name: relation_id941, Body: abstraction_with_arity942[0].(*pb.Abstraction), Attrs: _t1590, ValueArity: abstraction_with_arity942[1].(int64)}
	result945 := _t1591
	p.recordSpan(int(span_start944), "MonusDef")
	return result945
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start950 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1592 := p.parse_relation_id()
	relation_id946 := _t1592
	_t1593 := p.parse_abstraction()
	abstraction947 := _t1593
	_t1594 := p.parse_functional_dependency_keys()
	functional_dependency_keys948 := _t1594
	_t1595 := p.parse_functional_dependency_values()
	functional_dependency_values949 := _t1595
	p.consumeLiteral(")")
	_t1596 := &pb.FunctionalDependency{Guard: abstraction947, Keys: functional_dependency_keys948, Values: functional_dependency_values949}
	_t1597 := &pb.Constraint{Name: relation_id946}
	_t1597.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1596}
	result951 := _t1597
	p.recordSpan(int(span_start950), "Constraint")
	return result951
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs952 := []*pb.Var{}
	cond953 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond953 {
		_t1598 := p.parse_var()
		item954 := _t1598
		xs952 = append(xs952, item954)
		cond953 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars955 := xs952
	p.consumeLiteral(")")
	return vars955
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs956 := []*pb.Var{}
	cond957 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond957 {
		_t1599 := p.parse_var()
		item958 := _t1599
		xs956 = append(xs956, item958)
		cond957 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars959 := xs956
	p.consumeLiteral(")")
	return vars959
}

func (p *Parser) parse_data() *pb.Data {
	span_start964 := int64(p.spanStart())
	var _t1600 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1601 int64
		if p.matchLookaheadLiteral("rel_edb", 1) {
			_t1601 = 0
		} else {
			var _t1602 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1602 = 2
			} else {
				var _t1603 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1603 = 1
				} else {
					_t1603 = -1
				}
				_t1602 = _t1603
			}
			_t1601 = _t1602
		}
		_t1600 = _t1601
	} else {
		_t1600 = -1
	}
	prediction960 := _t1600
	var _t1604 *pb.Data
	if prediction960 == 2 {
		_t1605 := p.parse_csv_data()
		csv_data963 := _t1605
		_t1606 := &pb.Data{}
		_t1606.DataType = &pb.Data_CsvData{CsvData: csv_data963}
		_t1604 = _t1606
	} else {
		var _t1607 *pb.Data
		if prediction960 == 1 {
			_t1608 := p.parse_betree_relation()
			betree_relation962 := _t1608
			_t1609 := &pb.Data{}
			_t1609.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation962}
			_t1607 = _t1609
		} else {
			var _t1610 *pb.Data
			if prediction960 == 0 {
				_t1611 := p.parse_rel_edb()
				rel_edb961 := _t1611
				_t1612 := &pb.Data{}
				_t1612.DataType = &pb.Data_RelEdb{RelEdb: rel_edb961}
				_t1610 = _t1612
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1607 = _t1610
		}
		_t1604 = _t1607
	}
	result965 := _t1604
	p.recordSpan(int(span_start964), "Data")
	return result965
}

func (p *Parser) parse_rel_edb() *pb.RelEDB {
	span_start969 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("rel_edb")
	_t1613 := p.parse_relation_id()
	relation_id966 := _t1613
	_t1614 := p.parse_rel_edb_path()
	rel_edb_path967 := _t1614
	_t1615 := p.parse_rel_edb_types()
	rel_edb_types968 := _t1615
	p.consumeLiteral(")")
	_t1616 := &pb.RelEDB{TargetId: relation_id966, Path: rel_edb_path967, Types: rel_edb_types968}
	result970 := _t1616
	p.recordSpan(int(span_start969), "RelEDB")
	return result970
}

func (p *Parser) parse_rel_edb_path() []string {
	p.consumeLiteral("[")
	xs971 := []string{}
	cond972 := p.matchLookaheadTerminal("STRING", 0)
	for cond972 {
		item973 := p.consumeTerminal("STRING").Value.str
		xs971 = append(xs971, item973)
		cond972 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings974 := xs971
	p.consumeLiteral("]")
	return strings974
}

func (p *Parser) parse_rel_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs975 := []*pb.Type{}
	cond976 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond976 {
		_t1617 := p.parse_type()
		item977 := _t1617
		xs975 = append(xs975, item977)
		cond976 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types978 := xs975
	p.consumeLiteral("]")
	return types978
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start981 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1618 := p.parse_relation_id()
	relation_id979 := _t1618
	_t1619 := p.parse_betree_info()
	betree_info980 := _t1619
	p.consumeLiteral(")")
	_t1620 := &pb.BeTreeRelation{Name: relation_id979, RelationInfo: betree_info980}
	result982 := _t1620
	p.recordSpan(int(span_start981), "BeTreeRelation")
	return result982
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start986 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1621 := p.parse_betree_info_key_types()
	betree_info_key_types983 := _t1621
	_t1622 := p.parse_betree_info_value_types()
	betree_info_value_types984 := _t1622
	_t1623 := p.parse_config_dict()
	config_dict985 := _t1623
	p.consumeLiteral(")")
	_t1624 := p.construct_betree_info(betree_info_key_types983, betree_info_value_types984, config_dict985)
	result987 := _t1624
	p.recordSpan(int(span_start986), "BeTreeInfo")
	return result987
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs988 := []*pb.Type{}
	cond989 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond989 {
		_t1625 := p.parse_type()
		item990 := _t1625
		xs988 = append(xs988, item990)
		cond989 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types991 := xs988
	p.consumeLiteral(")")
	return types991
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs992 := []*pb.Type{}
	cond993 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond993 {
		_t1626 := p.parse_type()
		item994 := _t1626
		xs992 = append(xs992, item994)
		cond993 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types995 := xs992
	p.consumeLiteral(")")
	return types995
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1000 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1627 := p.parse_csvlocator()
	csvlocator996 := _t1627
	_t1628 := p.parse_csv_config()
	csv_config997 := _t1628
	_t1629 := p.parse_csv_columns()
	csv_columns998 := _t1629
	_t1630 := p.parse_csv_asof()
	csv_asof999 := _t1630
	p.consumeLiteral(")")
	_t1631 := &pb.CSVData{Locator: csvlocator996, Config: csv_config997, Columns: csv_columns998, Asof: csv_asof999}
	result1001 := _t1631
	p.recordSpan(int(span_start1000), "CSVData")
	return result1001
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1004 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1632 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1633 := p.parse_csv_locator_paths()
		_t1632 = _t1633
	}
	csv_locator_paths1002 := _t1632
	var _t1634 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1635 := p.parse_csv_locator_inline_data()
		_t1634 = ptr(_t1635)
	}
	csv_locator_inline_data1003 := _t1634
	p.consumeLiteral(")")
	_t1636 := csv_locator_paths1002
	if csv_locator_paths1002 == nil {
		_t1636 = []string{}
	}
	_t1637 := &pb.CSVLocator{Paths: _t1636, InlineData: []byte(deref(csv_locator_inline_data1003, ""))}
	result1005 := _t1637
	p.recordSpan(int(span_start1004), "CSVLocator")
	return result1005
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1006 := []string{}
	cond1007 := p.matchLookaheadTerminal("STRING", 0)
	for cond1007 {
		item1008 := p.consumeTerminal("STRING").Value.str
		xs1006 = append(xs1006, item1008)
		cond1007 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1009 := xs1006
	p.consumeLiteral(")")
	return strings1009
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1010 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1010
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1012 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1638 := p.parse_config_dict()
	config_dict1011 := _t1638
	p.consumeLiteral(")")
	_t1639 := p.construct_csv_config(config_dict1011)
	result1013 := _t1639
	p.recordSpan(int(span_start1012), "CSVConfig")
	return result1013
}

func (p *Parser) parse_csv_columns() []*pb.CSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1014 := []*pb.CSVColumn{}
	cond1015 := p.matchLookaheadLiteral("(", 0)
	for cond1015 {
		_t1640 := p.parse_csv_column()
		item1016 := _t1640
		xs1014 = append(xs1014, item1016)
		cond1015 = p.matchLookaheadLiteral("(", 0)
	}
	csv_columns1017 := xs1014
	p.consumeLiteral(")")
	return csv_columns1017
}

func (p *Parser) parse_csv_column() *pb.CSVColumn {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1018 := p.consumeTerminal("STRING").Value.str
	_t1641 := p.parse_relation_id()
	relation_id1019 := _t1641
	p.consumeLiteral("[")
	xs1020 := []*pb.Type{}
	cond1021 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1021 {
		_t1642 := p.parse_type()
		item1022 := _t1642
		xs1020 = append(xs1020, item1022)
		cond1021 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1023 := xs1020
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1643 := &pb.CSVColumn{ColumnName: string1018, TargetId: relation_id1019, Types: types1023}
	result1025 := _t1643
	p.recordSpan(int(span_start1024), "CSVColumn")
	return result1025
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1026 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1026
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1644 := p.parse_fragment_id()
	fragment_id1027 := _t1644
	p.consumeLiteral(")")
	_t1645 := &pb.Undefine{FragmentId: fragment_id1027}
	result1029 := _t1645
	p.recordSpan(int(span_start1028), "Undefine")
	return result1029
}

func (p *Parser) parse_context() *pb.Context {
	span_start1034 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1030 := []*pb.RelationId{}
	cond1031 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1031 {
		_t1646 := p.parse_relation_id()
		item1032 := _t1646
		xs1030 = append(xs1030, item1032)
		cond1031 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1033 := xs1030
	p.consumeLiteral(")")
	_t1647 := &pb.Context{Relations: relation_ids1033}
	result1035 := _t1647
	p.recordSpan(int(span_start1034), "Context")
	return result1035
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1038 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	_t1648 := p.parse_rel_edb_path()
	rel_edb_path1036 := _t1648
	_t1649 := p.parse_relation_id()
	relation_id1037 := _t1649
	p.consumeLiteral(")")
	_t1650 := &pb.Snapshot{DestinationPath: rel_edb_path1036, SourceRelation: relation_id1037}
	result1039 := _t1650
	p.recordSpan(int(span_start1038), "Snapshot")
	return result1039
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1040 := []*pb.Read{}
	cond1041 := p.matchLookaheadLiteral("(", 0)
	for cond1041 {
		_t1651 := p.parse_read()
		item1042 := _t1651
		xs1040 = append(xs1040, item1042)
		cond1041 = p.matchLookaheadLiteral("(", 0)
	}
	reads1043 := xs1040
	p.consumeLiteral(")")
	return reads1043
}

func (p *Parser) parse_read() *pb.Read {
	span_start1050 := int64(p.spanStart())
	var _t1652 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1653 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1653 = 2
		} else {
			var _t1654 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1654 = 1
			} else {
				var _t1655 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1655 = 4
				} else {
					var _t1656 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1656 = 0
					} else {
						var _t1657 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1657 = 3
						} else {
							_t1657 = -1
						}
						_t1656 = _t1657
					}
					_t1655 = _t1656
				}
				_t1654 = _t1655
			}
			_t1653 = _t1654
		}
		_t1652 = _t1653
	} else {
		_t1652 = -1
	}
	prediction1044 := _t1652
	var _t1658 *pb.Read
	if prediction1044 == 4 {
		_t1659 := p.parse_export()
		export1049 := _t1659
		_t1660 := &pb.Read{}
		_t1660.ReadType = &pb.Read_Export{Export: export1049}
		_t1658 = _t1660
	} else {
		var _t1661 *pb.Read
		if prediction1044 == 3 {
			_t1662 := p.parse_abort()
			abort1048 := _t1662
			_t1663 := &pb.Read{}
			_t1663.ReadType = &pb.Read_Abort{Abort: abort1048}
			_t1661 = _t1663
		} else {
			var _t1664 *pb.Read
			if prediction1044 == 2 {
				_t1665 := p.parse_what_if()
				what_if1047 := _t1665
				_t1666 := &pb.Read{}
				_t1666.ReadType = &pb.Read_WhatIf{WhatIf: what_if1047}
				_t1664 = _t1666
			} else {
				var _t1667 *pb.Read
				if prediction1044 == 1 {
					_t1668 := p.parse_output()
					output1046 := _t1668
					_t1669 := &pb.Read{}
					_t1669.ReadType = &pb.Read_Output{Output: output1046}
					_t1667 = _t1669
				} else {
					var _t1670 *pb.Read
					if prediction1044 == 0 {
						_t1671 := p.parse_demand()
						demand1045 := _t1671
						_t1672 := &pb.Read{}
						_t1672.ReadType = &pb.Read_Demand{Demand: demand1045}
						_t1670 = _t1672
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1667 = _t1670
				}
				_t1664 = _t1667
			}
			_t1661 = _t1664
		}
		_t1658 = _t1661
	}
	result1051 := _t1658
	p.recordSpan(int(span_start1050), "Read")
	return result1051
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1053 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1673 := p.parse_relation_id()
	relation_id1052 := _t1673
	p.consumeLiteral(")")
	_t1674 := &pb.Demand{RelationId: relation_id1052}
	result1054 := _t1674
	p.recordSpan(int(span_start1053), "Demand")
	return result1054
}

func (p *Parser) parse_output() *pb.Output {
	span_start1057 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1675 := p.parse_name()
	name1055 := _t1675
	_t1676 := p.parse_relation_id()
	relation_id1056 := _t1676
	p.consumeLiteral(")")
	_t1677 := &pb.Output{Name: name1055, RelationId: relation_id1056}
	result1058 := _t1677
	p.recordSpan(int(span_start1057), "Output")
	return result1058
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1061 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1678 := p.parse_name()
	name1059 := _t1678
	_t1679 := p.parse_epoch()
	epoch1060 := _t1679
	p.consumeLiteral(")")
	_t1680 := &pb.WhatIf{Branch: name1059, Epoch: epoch1060}
	result1062 := _t1680
	p.recordSpan(int(span_start1061), "WhatIf")
	return result1062
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1065 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1681 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1682 := p.parse_name()
		_t1681 = ptr(_t1682)
	}
	name1063 := _t1681
	_t1683 := p.parse_relation_id()
	relation_id1064 := _t1683
	p.consumeLiteral(")")
	_t1684 := &pb.Abort{Name: deref(name1063, "abort"), RelationId: relation_id1064}
	result1066 := _t1684
	p.recordSpan(int(span_start1065), "Abort")
	return result1066
}

func (p *Parser) parse_export() *pb.Export {
	span_start1068 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1685 := p.parse_export_csv_config()
	export_csv_config1067 := _t1685
	p.consumeLiteral(")")
	_t1686 := &pb.Export{}
	_t1686.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1067}
	result1069 := _t1686
	p.recordSpan(int(span_start1068), "Export")
	return result1069
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1073 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export_csv_config")
	_t1687 := p.parse_export_csv_path()
	export_csv_path1070 := _t1687
	_t1688 := p.parse_export_csv_columns()
	export_csv_columns1071 := _t1688
	_t1689 := p.parse_config_dict()
	config_dict1072 := _t1689
	p.consumeLiteral(")")
	_t1690 := p.export_csv_config(export_csv_path1070, export_csv_columns1071, config_dict1072)
	result1074 := _t1690
	p.recordSpan(int(span_start1073), "ExportCSVConfig")
	return result1074
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1075 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1075
}

func (p *Parser) parse_export_csv_columns() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1076 := []*pb.ExportCSVColumn{}
	cond1077 := p.matchLookaheadLiteral("(", 0)
	for cond1077 {
		_t1691 := p.parse_export_csv_column()
		item1078 := _t1691
		xs1076 = append(xs1076, item1078)
		cond1077 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1079 := xs1076
	p.consumeLiteral(")")
	return export_csv_columns1079
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1082 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1080 := p.consumeTerminal("STRING").Value.str
	_t1692 := p.parse_relation_id()
	relation_id1081 := _t1692
	p.consumeLiteral(")")
	_t1693 := &pb.ExportCSVColumn{ColumnName: string1080, ColumnData: relation_id1081}
	result1083 := _t1693
	p.recordSpan(int(span_start1082), "ExportCSVColumn")
	return result1083
}


// Parse parses the input string and returns (result, provenance, error).
func Parse(input string) (result *pb.Transaction, provenance map[int]Span, err error) {
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
	parser := NewParser(lexer.tokens, input)
	result = parser.parse_transaction()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, parser.Provenance, nil
}
