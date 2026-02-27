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
	var _t1769 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	_ = _t1769
	return int32(default_)
}

func (p *Parser) _extract_value_int64(value *pb.Value, default_ int64) int64 {
	var _t1770 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	_ = _t1770
	return default_
}

func (p *Parser) _extract_value_string(value *pb.Value, default_ string) string {
	var _t1771 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	_ = _t1771
	return default_
}

func (p *Parser) _extract_value_boolean(value *pb.Value, default_ bool) bool {
	var _t1772 interface{}
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	_ = _t1772
	return default_
}

func (p *Parser) _extract_value_string_list(value *pb.Value, default_ []string) []string {
	var _t1773 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	_ = _t1773
	return default_
}

func (p *Parser) _try_extract_value_int64(value *pb.Value) *int64 {
	var _t1774 interface{}
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	_ = _t1774
	return nil
}

func (p *Parser) _try_extract_value_float64(value *pb.Value) *float64 {
	var _t1775 interface{}
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	_ = _t1775
	return nil
}

func (p *Parser) _try_extract_value_bytes(value *pb.Value) []byte {
	var _t1776 interface{}
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	_ = _t1776
	return nil
}

func (p *Parser) _try_extract_value_uint128(value *pb.Value) *pb.UInt128Value {
	var _t1777 interface{}
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	_ = _t1777
	return nil
}

func (p *Parser) construct_csv_config(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t1778 := p._extract_value_int32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t1778
	_t1779 := p._extract_value_int64(dictGetValue(config, "csv_skip"), 0)
	skip := _t1779
	_t1780 := p._extract_value_string(dictGetValue(config, "csv_new_line"), "")
	new_line := _t1780
	_t1781 := p._extract_value_string(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t1781
	_t1782 := p._extract_value_string(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t1782
	_t1783 := p._extract_value_string(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t1783
	_t1784 := p._extract_value_string(dictGetValue(config, "csv_comment"), "")
	comment := _t1784
	_t1785 := p._extract_value_string_list(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t1785
	_t1786 := p._extract_value_string(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t1786
	_t1787 := p._extract_value_string(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t1787
	_t1788 := p._extract_value_string(dictGetValue(config, "csv_compression"), "auto")
	compression := _t1788
	_t1789 := p._extract_value_int64(dictGetValue(config, "csv_partition_size_mb"), 0)
	partition_size_mb := _t1789
	_t1790 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression, PartitionSizeMb: partition_size_mb}
	return _t1790
}

func (p *Parser) construct_betree_info(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t1791 := p._try_extract_value_float64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t1791
	_t1792 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t1792
	_t1793 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t1793
	_t1794 := p._try_extract_value_int64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t1794
	_t1795 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t1795
	_t1796 := p._try_extract_value_uint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t1796
	_t1797 := p._try_extract_value_bytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t1797
	_t1798 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t1798
	_t1799 := p._try_extract_value_int64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t1799
	_t1800 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t1800.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t1800.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t1800
	_t1801 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t1801
}

func (p *Parser) default_configure() *pb.Configure {
	_t1802 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t1802
	_t1803 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t1803
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
	_t1804 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t1804
	_t1805 := p._extract_value_int64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t1805
	_t1806 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t1806
}

func (p *Parser) construct_export_csv_config(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t1807 := p._extract_value_int64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t1807
	_t1808 := p._extract_value_string(dictGetValue(config, "compression"), "")
	compression := _t1808
	_t1809 := p._extract_value_boolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t1809
	_t1810 := p._extract_value_string(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t1810
	_t1811 := p._extract_value_string(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t1811
	_t1812 := p._extract_value_string(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t1812
	_t1813 := p._extract_value_string(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t1813
	_t1814 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t1814
}

func (p *Parser) construct_export_csv_config_with_source(path string, csv_source *pb.ExportCSVSource, csv_config *pb.CSVConfig) *pb.ExportCSVConfig {
	_t1815 := &pb.ExportCSVConfig{Path: path, CsvSource: csv_source, CsvConfig: csv_config}
	return _t1815
}

// --- Parse functions ---

func (p *Parser) parse_transaction() *pb.Transaction {
	span_start572 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("transaction")
	var _t1132 *pb.Configure
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("configure", 1)) {
		_t1133 := p.parse_configure()
		_t1132 = _t1133
	}
	configure566 := _t1132
	var _t1134 *pb.Sync
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("sync", 1)) {
		_t1135 := p.parse_sync()
		_t1134 = _t1135
	}
	sync567 := _t1134
	xs568 := []*pb.Epoch{}
	cond569 := p.matchLookaheadLiteral("(", 0)
	for cond569 {
		_t1136 := p.parse_epoch()
		item570 := _t1136
		xs568 = append(xs568, item570)
		cond569 = p.matchLookaheadLiteral("(", 0)
	}
	epochs571 := xs568
	p.consumeLiteral(")")
	_t1137 := p.default_configure()
	_t1138 := configure566
	if configure566 == nil {
		_t1138 = _t1137
	}
	_t1139 := &pb.Transaction{Epochs: epochs571, Configure: _t1138, Sync: sync567}
	result573 := _t1139
	p.recordSpan(int(span_start572), "Transaction")
	return result573
}

func (p *Parser) parse_configure() *pb.Configure {
	span_start575 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("configure")
	_t1140 := p.parse_config_dict()
	config_dict574 := _t1140
	p.consumeLiteral(")")
	_t1141 := p.construct_configure(config_dict574)
	result576 := _t1141
	p.recordSpan(int(span_start575), "Configure")
	return result576
}

func (p *Parser) parse_config_dict() [][]interface{} {
	p.consumeLiteral("{")
	xs577 := [][]interface{}{}
	cond578 := p.matchLookaheadLiteral(":", 0)
	for cond578 {
		_t1142 := p.parse_config_key_value()
		item579 := _t1142
		xs577 = append(xs577, item579)
		cond578 = p.matchLookaheadLiteral(":", 0)
	}
	config_key_values580 := xs577
	p.consumeLiteral("}")
	return config_key_values580
}

func (p *Parser) parse_config_key_value() []interface{} {
	p.consumeLiteral(":")
	symbol581 := p.consumeTerminal("SYMBOL").Value.str
	_t1143 := p.parse_value()
	value582 := _t1143
	return []interface{}{symbol581, value582}
}

func (p *Parser) parse_value() *pb.Value {
	span_start593 := int64(p.spanStart())
	var _t1144 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1144 = 9
	} else {
		var _t1145 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1145 = 8
		} else {
			var _t1146 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1146 = 9
			} else {
				var _t1147 int64
				if p.matchLookaheadLiteral("(", 0) {
					var _t1148 int64
					if p.matchLookaheadLiteral("datetime", 1) {
						_t1148 = 1
					} else {
						var _t1149 int64
						if p.matchLookaheadLiteral("date", 1) {
							_t1149 = 0
						} else {
							_t1149 = -1
						}
						_t1148 = _t1149
					}
					_t1147 = _t1148
				} else {
					var _t1150 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1150 = 5
					} else {
						var _t1151 int64
						if p.matchLookaheadTerminal("STRING", 0) {
							_t1151 = 2
						} else {
							var _t1152 int64
							if p.matchLookaheadTerminal("INT128", 0) {
								_t1152 = 6
							} else {
								var _t1153 int64
								if p.matchLookaheadTerminal("INT", 0) {
									_t1153 = 3
								} else {
									var _t1154 int64
									if p.matchLookaheadTerminal("FLOAT", 0) {
										_t1154 = 4
									} else {
										var _t1155 int64
										if p.matchLookaheadTerminal("DECIMAL", 0) {
											_t1155 = 7
										} else {
											_t1155 = -1
										}
										_t1154 = _t1155
									}
									_t1153 = _t1154
								}
								_t1152 = _t1153
							}
							_t1151 = _t1152
						}
						_t1150 = _t1151
					}
					_t1147 = _t1150
				}
				_t1146 = _t1147
			}
			_t1145 = _t1146
		}
		_t1144 = _t1145
	}
	prediction583 := _t1144
	var _t1156 *pb.Value
	if prediction583 == 9 {
		_t1157 := p.parse_boolean_value()
		boolean_value592 := _t1157
		_t1158 := &pb.Value{}
		_t1158.Value = &pb.Value_BooleanValue{BooleanValue: boolean_value592}
		_t1156 = _t1158
	} else {
		var _t1159 *pb.Value
		if prediction583 == 8 {
			p.consumeLiteral("missing")
			_t1160 := &pb.MissingValue{}
			_t1161 := &pb.Value{}
			_t1161.Value = &pb.Value_MissingValue{MissingValue: _t1160}
			_t1159 = _t1161
		} else {
			var _t1162 *pb.Value
			if prediction583 == 7 {
				decimal591 := p.consumeTerminal("DECIMAL").Value.decimal
				_t1163 := &pb.Value{}
				_t1163.Value = &pb.Value_DecimalValue{DecimalValue: decimal591}
				_t1162 = _t1163
			} else {
				var _t1164 *pb.Value
				if prediction583 == 6 {
					int128590 := p.consumeTerminal("INT128").Value.int128
					_t1165 := &pb.Value{}
					_t1165.Value = &pb.Value_Int128Value{Int128Value: int128590}
					_t1164 = _t1165
				} else {
					var _t1166 *pb.Value
					if prediction583 == 5 {
						uint128589 := p.consumeTerminal("UINT128").Value.uint128
						_t1167 := &pb.Value{}
						_t1167.Value = &pb.Value_Uint128Value{Uint128Value: uint128589}
						_t1166 = _t1167
					} else {
						var _t1168 *pb.Value
						if prediction583 == 4 {
							float588 := p.consumeTerminal("FLOAT").Value.f64
							_t1169 := &pb.Value{}
							_t1169.Value = &pb.Value_FloatValue{FloatValue: float588}
							_t1168 = _t1169
						} else {
							var _t1170 *pb.Value
							if prediction583 == 3 {
								int587 := p.consumeTerminal("INT").Value.i64
								_t1171 := &pb.Value{}
								_t1171.Value = &pb.Value_IntValue{IntValue: int587}
								_t1170 = _t1171
							} else {
								var _t1172 *pb.Value
								if prediction583 == 2 {
									string586 := p.consumeTerminal("STRING").Value.str
									_t1173 := &pb.Value{}
									_t1173.Value = &pb.Value_StringValue{StringValue: string586}
									_t1172 = _t1173
								} else {
									var _t1174 *pb.Value
									if prediction583 == 1 {
										_t1175 := p.parse_datetime()
										datetime585 := _t1175
										_t1176 := &pb.Value{}
										_t1176.Value = &pb.Value_DatetimeValue{DatetimeValue: datetime585}
										_t1174 = _t1176
									} else {
										var _t1177 *pb.Value
										if prediction583 == 0 {
											_t1178 := p.parse_date()
											date584 := _t1178
											_t1179 := &pb.Value{}
											_t1179.Value = &pb.Value_DateValue{DateValue: date584}
											_t1177 = _t1179
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in value", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1174 = _t1177
									}
									_t1172 = _t1174
								}
								_t1170 = _t1172
							}
							_t1168 = _t1170
						}
						_t1166 = _t1168
					}
					_t1164 = _t1166
				}
				_t1162 = _t1164
			}
			_t1159 = _t1162
		}
		_t1156 = _t1159
	}
	result594 := _t1156
	p.recordSpan(int(span_start593), "Value")
	return result594
}

func (p *Parser) parse_date() *pb.DateValue {
	span_start598 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("date")
	int595 := p.consumeTerminal("INT").Value.i64
	int_3596 := p.consumeTerminal("INT").Value.i64
	int_4597 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1180 := &pb.DateValue{Year: int32(int595), Month: int32(int_3596), Day: int32(int_4597)}
	result599 := _t1180
	p.recordSpan(int(span_start598), "DateValue")
	return result599
}

func (p *Parser) parse_datetime() *pb.DateTimeValue {
	span_start607 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("datetime")
	int600 := p.consumeTerminal("INT").Value.i64
	int_3601 := p.consumeTerminal("INT").Value.i64
	int_4602 := p.consumeTerminal("INT").Value.i64
	int_5603 := p.consumeTerminal("INT").Value.i64
	int_6604 := p.consumeTerminal("INT").Value.i64
	int_7605 := p.consumeTerminal("INT").Value.i64
	var _t1181 *int64
	if p.matchLookaheadTerminal("INT", 0) {
		_t1181 = ptr(p.consumeTerminal("INT").Value.i64)
	}
	int_8606 := _t1181
	p.consumeLiteral(")")
	_t1182 := &pb.DateTimeValue{Year: int32(int600), Month: int32(int_3601), Day: int32(int_4602), Hour: int32(int_5603), Minute: int32(int_6604), Second: int32(int_7605), Microsecond: int32(deref(int_8606, 0))}
	result608 := _t1182
	p.recordSpan(int(span_start607), "DateTimeValue")
	return result608
}

func (p *Parser) parse_boolean_value() bool {
	var _t1183 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1183 = 0
	} else {
		var _t1184 int64
		if p.matchLookaheadLiteral("false", 0) {
			_t1184 = 1
		} else {
			_t1184 = -1
		}
		_t1183 = _t1184
	}
	prediction609 := _t1183
	var _t1185 bool
	if prediction609 == 1 {
		p.consumeLiteral("false")
		_t1185 = false
	} else {
		var _t1186 bool
		if prediction609 == 0 {
			p.consumeLiteral("true")
			_t1186 = true
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in boolean_value", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1185 = _t1186
	}
	return _t1185
}

func (p *Parser) parse_sync() *pb.Sync {
	span_start614 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sync")
	xs610 := []*pb.FragmentId{}
	cond611 := p.matchLookaheadLiteral(":", 0)
	for cond611 {
		_t1187 := p.parse_fragment_id()
		item612 := _t1187
		xs610 = append(xs610, item612)
		cond611 = p.matchLookaheadLiteral(":", 0)
	}
	fragment_ids613 := xs610
	p.consumeLiteral(")")
	_t1188 := &pb.Sync{Fragments: fragment_ids613}
	result615 := _t1188
	p.recordSpan(int(span_start614), "Sync")
	return result615
}

func (p *Parser) parse_fragment_id() *pb.FragmentId {
	span_start617 := int64(p.spanStart())
	p.consumeLiteral(":")
	symbol616 := p.consumeTerminal("SYMBOL").Value.str
	result618 := &pb.FragmentId{Id: []byte(symbol616)}
	p.recordSpan(int(span_start617), "FragmentId")
	return result618
}

func (p *Parser) parse_epoch() *pb.Epoch {
	span_start621 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("epoch")
	var _t1189 []*pb.Write
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("writes", 1)) {
		_t1190 := p.parse_epoch_writes()
		_t1189 = _t1190
	}
	epoch_writes619 := _t1189
	var _t1191 []*pb.Read
	if p.matchLookaheadLiteral("(", 0) {
		_t1192 := p.parse_epoch_reads()
		_t1191 = _t1192
	}
	epoch_reads620 := _t1191
	p.consumeLiteral(")")
	_t1193 := epoch_writes619
	if epoch_writes619 == nil {
		_t1193 = []*pb.Write{}
	}
	_t1194 := epoch_reads620
	if epoch_reads620 == nil {
		_t1194 = []*pb.Read{}
	}
	_t1195 := &pb.Epoch{Writes: _t1193, Reads: _t1194}
	result622 := _t1195
	p.recordSpan(int(span_start621), "Epoch")
	return result622
}

func (p *Parser) parse_epoch_writes() []*pb.Write {
	p.consumeLiteral("(")
	p.consumeLiteral("writes")
	xs623 := []*pb.Write{}
	cond624 := p.matchLookaheadLiteral("(", 0)
	for cond624 {
		_t1196 := p.parse_write()
		item625 := _t1196
		xs623 = append(xs623, item625)
		cond624 = p.matchLookaheadLiteral("(", 0)
	}
	writes626 := xs623
	p.consumeLiteral(")")
	return writes626
}

func (p *Parser) parse_write() *pb.Write {
	span_start632 := int64(p.spanStart())
	var _t1197 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1198 int64
		if p.matchLookaheadLiteral("undefine", 1) {
			_t1198 = 1
		} else {
			var _t1199 int64
			if p.matchLookaheadLiteral("snapshot", 1) {
				_t1199 = 3
			} else {
				var _t1200 int64
				if p.matchLookaheadLiteral("define", 1) {
					_t1200 = 0
				} else {
					var _t1201 int64
					if p.matchLookaheadLiteral("context", 1) {
						_t1201 = 2
					} else {
						_t1201 = -1
					}
					_t1200 = _t1201
				}
				_t1199 = _t1200
			}
			_t1198 = _t1199
		}
		_t1197 = _t1198
	} else {
		_t1197 = -1
	}
	prediction627 := _t1197
	var _t1202 *pb.Write
	if prediction627 == 3 {
		_t1203 := p.parse_snapshot()
		snapshot631 := _t1203
		_t1204 := &pb.Write{}
		_t1204.WriteType = &pb.Write_Snapshot{Snapshot: snapshot631}
		_t1202 = _t1204
	} else {
		var _t1205 *pb.Write
		if prediction627 == 2 {
			_t1206 := p.parse_context()
			context630 := _t1206
			_t1207 := &pb.Write{}
			_t1207.WriteType = &pb.Write_Context{Context: context630}
			_t1205 = _t1207
		} else {
			var _t1208 *pb.Write
			if prediction627 == 1 {
				_t1209 := p.parse_undefine()
				undefine629 := _t1209
				_t1210 := &pb.Write{}
				_t1210.WriteType = &pb.Write_Undefine{Undefine: undefine629}
				_t1208 = _t1210
			} else {
				var _t1211 *pb.Write
				if prediction627 == 0 {
					_t1212 := p.parse_define()
					define628 := _t1212
					_t1213 := &pb.Write{}
					_t1213.WriteType = &pb.Write_Define{Define: define628}
					_t1211 = _t1213
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in write", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1208 = _t1211
			}
			_t1205 = _t1208
		}
		_t1202 = _t1205
	}
	result633 := _t1202
	p.recordSpan(int(span_start632), "Write")
	return result633
}

func (p *Parser) parse_define() *pb.Define {
	span_start635 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("define")
	_t1214 := p.parse_fragment()
	fragment634 := _t1214
	p.consumeLiteral(")")
	_t1215 := &pb.Define{Fragment: fragment634}
	result636 := _t1215
	p.recordSpan(int(span_start635), "Define")
	return result636
}

func (p *Parser) parse_fragment() *pb.Fragment {
	span_start642 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("fragment")
	_t1216 := p.parse_new_fragment_id()
	new_fragment_id637 := _t1216
	xs638 := []*pb.Declaration{}
	cond639 := p.matchLookaheadLiteral("(", 0)
	for cond639 {
		_t1217 := p.parse_declaration()
		item640 := _t1217
		xs638 = append(xs638, item640)
		cond639 = p.matchLookaheadLiteral("(", 0)
	}
	declarations641 := xs638
	p.consumeLiteral(")")
	result643 := p.constructFragment(new_fragment_id637, declarations641)
	p.recordSpan(int(span_start642), "Fragment")
	return result643
}

func (p *Parser) parse_new_fragment_id() *pb.FragmentId {
	span_start645 := int64(p.spanStart())
	_t1218 := p.parse_fragment_id()
	fragment_id644 := _t1218
	p.startFragment(fragment_id644)
	result646 := fragment_id644
	p.recordSpan(int(span_start645), "FragmentId")
	return result646
}

func (p *Parser) parse_declaration() *pb.Declaration {
	span_start652 := int64(p.spanStart())
	var _t1219 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1220 int64
		if p.matchLookaheadLiteral("functional_dependency", 1) {
			_t1220 = 2
		} else {
			var _t1221 int64
			if p.matchLookaheadLiteral("edb", 1) {
				_t1221 = 3
			} else {
				var _t1222 int64
				if p.matchLookaheadLiteral("def", 1) {
					_t1222 = 0
				} else {
					var _t1223 int64
					if p.matchLookaheadLiteral("csv_data", 1) {
						_t1223 = 3
					} else {
						var _t1224 int64
						if p.matchLookaheadLiteral("betree_relation", 1) {
							_t1224 = 3
						} else {
							var _t1225 int64
							if p.matchLookaheadLiteral("algorithm", 1) {
								_t1225 = 1
							} else {
								_t1225 = -1
							}
							_t1224 = _t1225
						}
						_t1223 = _t1224
					}
					_t1222 = _t1223
				}
				_t1221 = _t1222
			}
			_t1220 = _t1221
		}
		_t1219 = _t1220
	} else {
		_t1219 = -1
	}
	prediction647 := _t1219
	var _t1226 *pb.Declaration
	if prediction647 == 3 {
		_t1227 := p.parse_data()
		data651 := _t1227
		_t1228 := &pb.Declaration{}
		_t1228.DeclarationType = &pb.Declaration_Data{Data: data651}
		_t1226 = _t1228
	} else {
		var _t1229 *pb.Declaration
		if prediction647 == 2 {
			_t1230 := p.parse_constraint()
			constraint650 := _t1230
			_t1231 := &pb.Declaration{}
			_t1231.DeclarationType = &pb.Declaration_Constraint{Constraint: constraint650}
			_t1229 = _t1231
		} else {
			var _t1232 *pb.Declaration
			if prediction647 == 1 {
				_t1233 := p.parse_algorithm()
				algorithm649 := _t1233
				_t1234 := &pb.Declaration{}
				_t1234.DeclarationType = &pb.Declaration_Algorithm{Algorithm: algorithm649}
				_t1232 = _t1234
			} else {
				var _t1235 *pb.Declaration
				if prediction647 == 0 {
					_t1236 := p.parse_def()
					def648 := _t1236
					_t1237 := &pb.Declaration{}
					_t1237.DeclarationType = &pb.Declaration_Def{Def: def648}
					_t1235 = _t1237
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in declaration", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1232 = _t1235
			}
			_t1229 = _t1232
		}
		_t1226 = _t1229
	}
	result653 := _t1226
	p.recordSpan(int(span_start652), "Declaration")
	return result653
}

func (p *Parser) parse_def() *pb.Def {
	span_start657 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("def")
	_t1238 := p.parse_relation_id()
	relation_id654 := _t1238
	_t1239 := p.parse_abstraction()
	abstraction655 := _t1239
	var _t1240 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1241 := p.parse_attrs()
		_t1240 = _t1241
	}
	attrs656 := _t1240
	p.consumeLiteral(")")
	_t1242 := attrs656
	if attrs656 == nil {
		_t1242 = []*pb.Attribute{}
	}
	_t1243 := &pb.Def{Name: relation_id654, Body: abstraction655, Attrs: _t1242}
	result658 := _t1243
	p.recordSpan(int(span_start657), "Def")
	return result658
}

func (p *Parser) parse_relation_id() *pb.RelationId {
	span_start662 := int64(p.spanStart())
	var _t1244 int64
	if p.matchLookaheadLiteral(":", 0) {
		_t1244 = 0
	} else {
		var _t1245 int64
		if p.matchLookaheadTerminal("UINT128", 0) {
			_t1245 = 1
		} else {
			_t1245 = -1
		}
		_t1244 = _t1245
	}
	prediction659 := _t1244
	var _t1246 *pb.RelationId
	if prediction659 == 1 {
		uint128661 := p.consumeTerminal("UINT128").Value.uint128
		_ = uint128661
		_t1246 = &pb.RelationId{IdLow: uint128661.Low, IdHigh: uint128661.High}
	} else {
		var _t1247 *pb.RelationId
		if prediction659 == 0 {
			p.consumeLiteral(":")
			symbol660 := p.consumeTerminal("SYMBOL").Value.str
			_t1247 = p.relationIdFromString(symbol660)
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in relation_id", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1246 = _t1247
	}
	result663 := _t1246
	p.recordSpan(int(span_start662), "RelationId")
	return result663
}

func (p *Parser) parse_abstraction() *pb.Abstraction {
	span_start666 := int64(p.spanStart())
	p.consumeLiteral("(")
	_t1248 := p.parse_bindings()
	bindings664 := _t1248
	_t1249 := p.parse_formula()
	formula665 := _t1249
	p.consumeLiteral(")")
	_t1250 := &pb.Abstraction{Vars: listConcat(bindings664[0].([]*pb.Binding), bindings664[1].([]*pb.Binding)), Value: formula665}
	result667 := _t1250
	p.recordSpan(int(span_start666), "Abstraction")
	return result667
}

func (p *Parser) parse_bindings() []interface{} {
	p.consumeLiteral("[")
	xs668 := []*pb.Binding{}
	cond669 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond669 {
		_t1251 := p.parse_binding()
		item670 := _t1251
		xs668 = append(xs668, item670)
		cond669 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings671 := xs668
	var _t1252 []*pb.Binding
	if p.matchLookaheadLiteral("|", 0) {
		_t1253 := p.parse_value_bindings()
		_t1252 = _t1253
	}
	value_bindings672 := _t1252
	p.consumeLiteral("]")
	_t1254 := value_bindings672
	if value_bindings672 == nil {
		_t1254 = []*pb.Binding{}
	}
	return []interface{}{bindings671, _t1254}
}

func (p *Parser) parse_binding() *pb.Binding {
	span_start675 := int64(p.spanStart())
	symbol673 := p.consumeTerminal("SYMBOL").Value.str
	p.consumeLiteral("::")
	_t1255 := p.parse_type()
	type674 := _t1255
	_t1256 := &pb.Var{Name: symbol673}
	_t1257 := &pb.Binding{Var: _t1256, Type: type674}
	result676 := _t1257
	p.recordSpan(int(span_start675), "Binding")
	return result676
}

func (p *Parser) parse_type() *pb.Type {
	span_start689 := int64(p.spanStart())
	var _t1258 int64
	if p.matchLookaheadLiteral("UNKNOWN", 0) {
		_t1258 = 0
	} else {
		var _t1259 int64
		if p.matchLookaheadLiteral("UINT128", 0) {
			_t1259 = 4
		} else {
			var _t1260 int64
			if p.matchLookaheadLiteral("STRING", 0) {
				_t1260 = 1
			} else {
				var _t1261 int64
				if p.matchLookaheadLiteral("MISSING", 0) {
					_t1261 = 8
				} else {
					var _t1262 int64
					if p.matchLookaheadLiteral("INT128", 0) {
						_t1262 = 5
					} else {
						var _t1263 int64
						if p.matchLookaheadLiteral("INT", 0) {
							_t1263 = 2
						} else {
							var _t1264 int64
							if p.matchLookaheadLiteral("FLOAT", 0) {
								_t1264 = 3
							} else {
								var _t1265 int64
								if p.matchLookaheadLiteral("DATETIME", 0) {
									_t1265 = 7
								} else {
									var _t1266 int64
									if p.matchLookaheadLiteral("DATE", 0) {
										_t1266 = 6
									} else {
										var _t1267 int64
										if p.matchLookaheadLiteral("BOOLEAN", 0) {
											_t1267 = 10
										} else {
											var _t1268 int64
											if p.matchLookaheadLiteral("(", 0) {
												_t1268 = 9
											} else {
												_t1268 = -1
											}
											_t1267 = _t1268
										}
										_t1266 = _t1267
									}
									_t1265 = _t1266
								}
								_t1264 = _t1265
							}
							_t1263 = _t1264
						}
						_t1262 = _t1263
					}
					_t1261 = _t1262
				}
				_t1260 = _t1261
			}
			_t1259 = _t1260
		}
		_t1258 = _t1259
	}
	prediction677 := _t1258
	var _t1269 *pb.Type
	if prediction677 == 10 {
		_t1270 := p.parse_boolean_type()
		boolean_type688 := _t1270
		_t1271 := &pb.Type{}
		_t1271.Type = &pb.Type_BooleanType{BooleanType: boolean_type688}
		_t1269 = _t1271
	} else {
		var _t1272 *pb.Type
		if prediction677 == 9 {
			_t1273 := p.parse_decimal_type()
			decimal_type687 := _t1273
			_t1274 := &pb.Type{}
			_t1274.Type = &pb.Type_DecimalType{DecimalType: decimal_type687}
			_t1272 = _t1274
		} else {
			var _t1275 *pb.Type
			if prediction677 == 8 {
				_t1276 := p.parse_missing_type()
				missing_type686 := _t1276
				_t1277 := &pb.Type{}
				_t1277.Type = &pb.Type_MissingType{MissingType: missing_type686}
				_t1275 = _t1277
			} else {
				var _t1278 *pb.Type
				if prediction677 == 7 {
					_t1279 := p.parse_datetime_type()
					datetime_type685 := _t1279
					_t1280 := &pb.Type{}
					_t1280.Type = &pb.Type_DatetimeType{DatetimeType: datetime_type685}
					_t1278 = _t1280
				} else {
					var _t1281 *pb.Type
					if prediction677 == 6 {
						_t1282 := p.parse_date_type()
						date_type684 := _t1282
						_t1283 := &pb.Type{}
						_t1283.Type = &pb.Type_DateType{DateType: date_type684}
						_t1281 = _t1283
					} else {
						var _t1284 *pb.Type
						if prediction677 == 5 {
							_t1285 := p.parse_int128_type()
							int128_type683 := _t1285
							_t1286 := &pb.Type{}
							_t1286.Type = &pb.Type_Int128Type{Int128Type: int128_type683}
							_t1284 = _t1286
						} else {
							var _t1287 *pb.Type
							if prediction677 == 4 {
								_t1288 := p.parse_uint128_type()
								uint128_type682 := _t1288
								_t1289 := &pb.Type{}
								_t1289.Type = &pb.Type_Uint128Type{Uint128Type: uint128_type682}
								_t1287 = _t1289
							} else {
								var _t1290 *pb.Type
								if prediction677 == 3 {
									_t1291 := p.parse_float_type()
									float_type681 := _t1291
									_t1292 := &pb.Type{}
									_t1292.Type = &pb.Type_FloatType{FloatType: float_type681}
									_t1290 = _t1292
								} else {
									var _t1293 *pb.Type
									if prediction677 == 2 {
										_t1294 := p.parse_int_type()
										int_type680 := _t1294
										_t1295 := &pb.Type{}
										_t1295.Type = &pb.Type_IntType{IntType: int_type680}
										_t1293 = _t1295
									} else {
										var _t1296 *pb.Type
										if prediction677 == 1 {
											_t1297 := p.parse_string_type()
											string_type679 := _t1297
											_t1298 := &pb.Type{}
											_t1298.Type = &pb.Type_StringType{StringType: string_type679}
											_t1296 = _t1298
										} else {
											var _t1299 *pb.Type
											if prediction677 == 0 {
												_t1300 := p.parse_unspecified_type()
												unspecified_type678 := _t1300
												_t1301 := &pb.Type{}
												_t1301.Type = &pb.Type_UnspecifiedType{UnspecifiedType: unspecified_type678}
												_t1299 = _t1301
											} else {
												panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in type", p.lookahead(0).Type, p.lookahead(0).Value)})
											}
											_t1296 = _t1299
										}
										_t1293 = _t1296
									}
									_t1290 = _t1293
								}
								_t1287 = _t1290
							}
							_t1284 = _t1287
						}
						_t1281 = _t1284
					}
					_t1278 = _t1281
				}
				_t1275 = _t1278
			}
			_t1272 = _t1275
		}
		_t1269 = _t1272
	}
	result690 := _t1269
	p.recordSpan(int(span_start689), "Type")
	return result690
}

func (p *Parser) parse_unspecified_type() *pb.UnspecifiedType {
	span_start691 := int64(p.spanStart())
	p.consumeLiteral("UNKNOWN")
	_t1302 := &pb.UnspecifiedType{}
	result692 := _t1302
	p.recordSpan(int(span_start691), "UnspecifiedType")
	return result692
}

func (p *Parser) parse_string_type() *pb.StringType {
	span_start693 := int64(p.spanStart())
	p.consumeLiteral("STRING")
	_t1303 := &pb.StringType{}
	result694 := _t1303
	p.recordSpan(int(span_start693), "StringType")
	return result694
}

func (p *Parser) parse_int_type() *pb.IntType {
	span_start695 := int64(p.spanStart())
	p.consumeLiteral("INT")
	_t1304 := &pb.IntType{}
	result696 := _t1304
	p.recordSpan(int(span_start695), "IntType")
	return result696
}

func (p *Parser) parse_float_type() *pb.FloatType {
	span_start697 := int64(p.spanStart())
	p.consumeLiteral("FLOAT")
	_t1305 := &pb.FloatType{}
	result698 := _t1305
	p.recordSpan(int(span_start697), "FloatType")
	return result698
}

func (p *Parser) parse_uint128_type() *pb.UInt128Type {
	span_start699 := int64(p.spanStart())
	p.consumeLiteral("UINT128")
	_t1306 := &pb.UInt128Type{}
	result700 := _t1306
	p.recordSpan(int(span_start699), "UInt128Type")
	return result700
}

func (p *Parser) parse_int128_type() *pb.Int128Type {
	span_start701 := int64(p.spanStart())
	p.consumeLiteral("INT128")
	_t1307 := &pb.Int128Type{}
	result702 := _t1307
	p.recordSpan(int(span_start701), "Int128Type")
	return result702
}

func (p *Parser) parse_date_type() *pb.DateType {
	span_start703 := int64(p.spanStart())
	p.consumeLiteral("DATE")
	_t1308 := &pb.DateType{}
	result704 := _t1308
	p.recordSpan(int(span_start703), "DateType")
	return result704
}

func (p *Parser) parse_datetime_type() *pb.DateTimeType {
	span_start705 := int64(p.spanStart())
	p.consumeLiteral("DATETIME")
	_t1309 := &pb.DateTimeType{}
	result706 := _t1309
	p.recordSpan(int(span_start705), "DateTimeType")
	return result706
}

func (p *Parser) parse_missing_type() *pb.MissingType {
	span_start707 := int64(p.spanStart())
	p.consumeLiteral("MISSING")
	_t1310 := &pb.MissingType{}
	result708 := _t1310
	p.recordSpan(int(span_start707), "MissingType")
	return result708
}

func (p *Parser) parse_decimal_type() *pb.DecimalType {
	span_start711 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("DECIMAL")
	int709 := p.consumeTerminal("INT").Value.i64
	int_3710 := p.consumeTerminal("INT").Value.i64
	p.consumeLiteral(")")
	_t1311 := &pb.DecimalType{Precision: int32(int709), Scale: int32(int_3710)}
	result712 := _t1311
	p.recordSpan(int(span_start711), "DecimalType")
	return result712
}

func (p *Parser) parse_boolean_type() *pb.BooleanType {
	span_start713 := int64(p.spanStart())
	p.consumeLiteral("BOOLEAN")
	_t1312 := &pb.BooleanType{}
	result714 := _t1312
	p.recordSpan(int(span_start713), "BooleanType")
	return result714
}

func (p *Parser) parse_value_bindings() []*pb.Binding {
	p.consumeLiteral("|")
	xs715 := []*pb.Binding{}
	cond716 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond716 {
		_t1313 := p.parse_binding()
		item717 := _t1313
		xs715 = append(xs715, item717)
		cond716 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	bindings718 := xs715
	return bindings718
}

func (p *Parser) parse_formula() *pb.Formula {
	span_start733 := int64(p.spanStart())
	var _t1314 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1315 int64
		if p.matchLookaheadLiteral("true", 1) {
			_t1315 = 0
		} else {
			var _t1316 int64
			if p.matchLookaheadLiteral("relatom", 1) {
				_t1316 = 11
			} else {
				var _t1317 int64
				if p.matchLookaheadLiteral("reduce", 1) {
					_t1317 = 3
				} else {
					var _t1318 int64
					if p.matchLookaheadLiteral("primitive", 1) {
						_t1318 = 10
					} else {
						var _t1319 int64
						if p.matchLookaheadLiteral("pragma", 1) {
							_t1319 = 9
						} else {
							var _t1320 int64
							if p.matchLookaheadLiteral("or", 1) {
								_t1320 = 5
							} else {
								var _t1321 int64
								if p.matchLookaheadLiteral("not", 1) {
									_t1321 = 6
								} else {
									var _t1322 int64
									if p.matchLookaheadLiteral("ffi", 1) {
										_t1322 = 7
									} else {
										var _t1323 int64
										if p.matchLookaheadLiteral("false", 1) {
											_t1323 = 1
										} else {
											var _t1324 int64
											if p.matchLookaheadLiteral("exists", 1) {
												_t1324 = 2
											} else {
												var _t1325 int64
												if p.matchLookaheadLiteral("cast", 1) {
													_t1325 = 12
												} else {
													var _t1326 int64
													if p.matchLookaheadLiteral("atom", 1) {
														_t1326 = 8
													} else {
														var _t1327 int64
														if p.matchLookaheadLiteral("and", 1) {
															_t1327 = 4
														} else {
															var _t1328 int64
															if p.matchLookaheadLiteral(">=", 1) {
																_t1328 = 10
															} else {
																var _t1329 int64
																if p.matchLookaheadLiteral(">", 1) {
																	_t1329 = 10
																} else {
																	var _t1330 int64
																	if p.matchLookaheadLiteral("=", 1) {
																		_t1330 = 10
																	} else {
																		var _t1331 int64
																		if p.matchLookaheadLiteral("<=", 1) {
																			_t1331 = 10
																		} else {
																			var _t1332 int64
																			if p.matchLookaheadLiteral("<", 1) {
																				_t1332 = 10
																			} else {
																				var _t1333 int64
																				if p.matchLookaheadLiteral("/", 1) {
																					_t1333 = 10
																				} else {
																					var _t1334 int64
																					if p.matchLookaheadLiteral("-", 1) {
																						_t1334 = 10
																					} else {
																						var _t1335 int64
																						if p.matchLookaheadLiteral("+", 1) {
																							_t1335 = 10
																						} else {
																							var _t1336 int64
																							if p.matchLookaheadLiteral("*", 1) {
																								_t1336 = 10
																							} else {
																								_t1336 = -1
																							}
																							_t1335 = _t1336
																						}
																						_t1334 = _t1335
																					}
																					_t1333 = _t1334
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
															}
															_t1327 = _t1328
														}
														_t1326 = _t1327
													}
													_t1325 = _t1326
												}
												_t1324 = _t1325
											}
											_t1323 = _t1324
										}
										_t1322 = _t1323
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
				}
				_t1316 = _t1317
			}
			_t1315 = _t1316
		}
		_t1314 = _t1315
	} else {
		_t1314 = -1
	}
	prediction719 := _t1314
	var _t1337 *pb.Formula
	if prediction719 == 12 {
		_t1338 := p.parse_cast()
		cast732 := _t1338
		_t1339 := &pb.Formula{}
		_t1339.FormulaType = &pb.Formula_Cast{Cast: cast732}
		_t1337 = _t1339
	} else {
		var _t1340 *pb.Formula
		if prediction719 == 11 {
			_t1341 := p.parse_rel_atom()
			rel_atom731 := _t1341
			_t1342 := &pb.Formula{}
			_t1342.FormulaType = &pb.Formula_RelAtom{RelAtom: rel_atom731}
			_t1340 = _t1342
		} else {
			var _t1343 *pb.Formula
			if prediction719 == 10 {
				_t1344 := p.parse_primitive()
				primitive730 := _t1344
				_t1345 := &pb.Formula{}
				_t1345.FormulaType = &pb.Formula_Primitive{Primitive: primitive730}
				_t1343 = _t1345
			} else {
				var _t1346 *pb.Formula
				if prediction719 == 9 {
					_t1347 := p.parse_pragma()
					pragma729 := _t1347
					_t1348 := &pb.Formula{}
					_t1348.FormulaType = &pb.Formula_Pragma{Pragma: pragma729}
					_t1346 = _t1348
				} else {
					var _t1349 *pb.Formula
					if prediction719 == 8 {
						_t1350 := p.parse_atom()
						atom728 := _t1350
						_t1351 := &pb.Formula{}
						_t1351.FormulaType = &pb.Formula_Atom{Atom: atom728}
						_t1349 = _t1351
					} else {
						var _t1352 *pb.Formula
						if prediction719 == 7 {
							_t1353 := p.parse_ffi()
							ffi727 := _t1353
							_t1354 := &pb.Formula{}
							_t1354.FormulaType = &pb.Formula_Ffi{Ffi: ffi727}
							_t1352 = _t1354
						} else {
							var _t1355 *pb.Formula
							if prediction719 == 6 {
								_t1356 := p.parse_not()
								not726 := _t1356
								_t1357 := &pb.Formula{}
								_t1357.FormulaType = &pb.Formula_Not{Not: not726}
								_t1355 = _t1357
							} else {
								var _t1358 *pb.Formula
								if prediction719 == 5 {
									_t1359 := p.parse_disjunction()
									disjunction725 := _t1359
									_t1360 := &pb.Formula{}
									_t1360.FormulaType = &pb.Formula_Disjunction{Disjunction: disjunction725}
									_t1358 = _t1360
								} else {
									var _t1361 *pb.Formula
									if prediction719 == 4 {
										_t1362 := p.parse_conjunction()
										conjunction724 := _t1362
										_t1363 := &pb.Formula{}
										_t1363.FormulaType = &pb.Formula_Conjunction{Conjunction: conjunction724}
										_t1361 = _t1363
									} else {
										var _t1364 *pb.Formula
										if prediction719 == 3 {
											_t1365 := p.parse_reduce()
											reduce723 := _t1365
											_t1366 := &pb.Formula{}
											_t1366.FormulaType = &pb.Formula_Reduce{Reduce: reduce723}
											_t1364 = _t1366
										} else {
											var _t1367 *pb.Formula
											if prediction719 == 2 {
												_t1368 := p.parse_exists()
												exists722 := _t1368
												_t1369 := &pb.Formula{}
												_t1369.FormulaType = &pb.Formula_Exists{Exists: exists722}
												_t1367 = _t1369
											} else {
												var _t1370 *pb.Formula
												if prediction719 == 1 {
													_t1371 := p.parse_false()
													false721 := _t1371
													_t1372 := &pb.Formula{}
													_t1372.FormulaType = &pb.Formula_Disjunction{Disjunction: false721}
													_t1370 = _t1372
												} else {
													var _t1373 *pb.Formula
													if prediction719 == 0 {
														_t1374 := p.parse_true()
														true720 := _t1374
														_t1375 := &pb.Formula{}
														_t1375.FormulaType = &pb.Formula_Conjunction{Conjunction: true720}
														_t1373 = _t1375
													} else {
														panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in formula", p.lookahead(0).Type, p.lookahead(0).Value)})
													}
													_t1370 = _t1373
												}
												_t1367 = _t1370
											}
											_t1364 = _t1367
										}
										_t1361 = _t1364
									}
									_t1358 = _t1361
								}
								_t1355 = _t1358
							}
							_t1352 = _t1355
						}
						_t1349 = _t1352
					}
					_t1346 = _t1349
				}
				_t1343 = _t1346
			}
			_t1340 = _t1343
		}
		_t1337 = _t1340
	}
	result734 := _t1337
	p.recordSpan(int(span_start733), "Formula")
	return result734
}

func (p *Parser) parse_true() *pb.Conjunction {
	span_start735 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("true")
	p.consumeLiteral(")")
	_t1376 := &pb.Conjunction{Args: []*pb.Formula{}}
	result736 := _t1376
	p.recordSpan(int(span_start735), "Conjunction")
	return result736
}

func (p *Parser) parse_false() *pb.Disjunction {
	span_start737 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("false")
	p.consumeLiteral(")")
	_t1377 := &pb.Disjunction{Args: []*pb.Formula{}}
	result738 := _t1377
	p.recordSpan(int(span_start737), "Disjunction")
	return result738
}

func (p *Parser) parse_exists() *pb.Exists {
	span_start741 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("exists")
	_t1378 := p.parse_bindings()
	bindings739 := _t1378
	_t1379 := p.parse_formula()
	formula740 := _t1379
	p.consumeLiteral(")")
	_t1380 := &pb.Abstraction{Vars: listConcat(bindings739[0].([]*pb.Binding), bindings739[1].([]*pb.Binding)), Value: formula740}
	_t1381 := &pb.Exists{Body: _t1380}
	result742 := _t1381
	p.recordSpan(int(span_start741), "Exists")
	return result742
}

func (p *Parser) parse_reduce() *pb.Reduce {
	span_start746 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("reduce")
	_t1382 := p.parse_abstraction()
	abstraction743 := _t1382
	_t1383 := p.parse_abstraction()
	abstraction_3744 := _t1383
	_t1384 := p.parse_terms()
	terms745 := _t1384
	p.consumeLiteral(")")
	_t1385 := &pb.Reduce{Op: abstraction743, Body: abstraction_3744, Terms: terms745}
	result747 := _t1385
	p.recordSpan(int(span_start746), "Reduce")
	return result747
}

func (p *Parser) parse_terms() []*pb.Term {
	p.consumeLiteral("(")
	p.consumeLiteral("terms")
	xs748 := []*pb.Term{}
	cond749 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond749 {
		_t1386 := p.parse_term()
		item750 := _t1386
		xs748 = append(xs748, item750)
		cond749 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms751 := xs748
	p.consumeLiteral(")")
	return terms751
}

func (p *Parser) parse_term() *pb.Term {
	span_start755 := int64(p.spanStart())
	var _t1387 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1387 = 1
	} else {
		var _t1388 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1388 = 1
		} else {
			var _t1389 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1389 = 1
			} else {
				var _t1390 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1390 = 1
				} else {
					var _t1391 int64
					if p.matchLookaheadTerminal("UINT128", 0) {
						_t1391 = 1
					} else {
						var _t1392 int64
						if p.matchLookaheadTerminal("SYMBOL", 0) {
							_t1392 = 0
						} else {
							var _t1393 int64
							if p.matchLookaheadTerminal("STRING", 0) {
								_t1393 = 1
							} else {
								var _t1394 int64
								if p.matchLookaheadTerminal("INT128", 0) {
									_t1394 = 1
								} else {
									var _t1395 int64
									if p.matchLookaheadTerminal("INT", 0) {
										_t1395 = 1
									} else {
										var _t1396 int64
										if p.matchLookaheadTerminal("FLOAT", 0) {
											_t1396 = 1
										} else {
											var _t1397 int64
											if p.matchLookaheadTerminal("DECIMAL", 0) {
												_t1397 = 1
											} else {
												_t1397 = -1
											}
											_t1396 = _t1397
										}
										_t1395 = _t1396
									}
									_t1394 = _t1395
								}
								_t1393 = _t1394
							}
							_t1392 = _t1393
						}
						_t1391 = _t1392
					}
					_t1390 = _t1391
				}
				_t1389 = _t1390
			}
			_t1388 = _t1389
		}
		_t1387 = _t1388
	}
	prediction752 := _t1387
	var _t1398 *pb.Term
	if prediction752 == 1 {
		_t1399 := p.parse_constant()
		constant754 := _t1399
		_t1400 := &pb.Term{}
		_t1400.TermType = &pb.Term_Constant{Constant: constant754}
		_t1398 = _t1400
	} else {
		var _t1401 *pb.Term
		if prediction752 == 0 {
			_t1402 := p.parse_var()
			var753 := _t1402
			_t1403 := &pb.Term{}
			_t1403.TermType = &pb.Term_Var{Var: var753}
			_t1401 = _t1403
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1398 = _t1401
	}
	result756 := _t1398
	p.recordSpan(int(span_start755), "Term")
	return result756
}

func (p *Parser) parse_var() *pb.Var {
	span_start758 := int64(p.spanStart())
	symbol757 := p.consumeTerminal("SYMBOL").Value.str
	_t1404 := &pb.Var{Name: symbol757}
	result759 := _t1404
	p.recordSpan(int(span_start758), "Var")
	return result759
}

func (p *Parser) parse_constant() *pb.Value {
	span_start761 := int64(p.spanStart())
	_t1405 := p.parse_value()
	value760 := _t1405
	result762 := value760
	p.recordSpan(int(span_start761), "Value")
	return result762
}

func (p *Parser) parse_conjunction() *pb.Conjunction {
	span_start767 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("and")
	xs763 := []*pb.Formula{}
	cond764 := p.matchLookaheadLiteral("(", 0)
	for cond764 {
		_t1406 := p.parse_formula()
		item765 := _t1406
		xs763 = append(xs763, item765)
		cond764 = p.matchLookaheadLiteral("(", 0)
	}
	formulas766 := xs763
	p.consumeLiteral(")")
	_t1407 := &pb.Conjunction{Args: formulas766}
	result768 := _t1407
	p.recordSpan(int(span_start767), "Conjunction")
	return result768
}

func (p *Parser) parse_disjunction() *pb.Disjunction {
	span_start773 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	xs769 := []*pb.Formula{}
	cond770 := p.matchLookaheadLiteral("(", 0)
	for cond770 {
		_t1408 := p.parse_formula()
		item771 := _t1408
		xs769 = append(xs769, item771)
		cond770 = p.matchLookaheadLiteral("(", 0)
	}
	formulas772 := xs769
	p.consumeLiteral(")")
	_t1409 := &pb.Disjunction{Args: formulas772}
	result774 := _t1409
	p.recordSpan(int(span_start773), "Disjunction")
	return result774
}

func (p *Parser) parse_not() *pb.Not {
	span_start776 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("not")
	_t1410 := p.parse_formula()
	formula775 := _t1410
	p.consumeLiteral(")")
	_t1411 := &pb.Not{Arg: formula775}
	result777 := _t1411
	p.recordSpan(int(span_start776), "Not")
	return result777
}

func (p *Parser) parse_ffi() *pb.FFI {
	span_start781 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("ffi")
	_t1412 := p.parse_name()
	name778 := _t1412
	_t1413 := p.parse_ffi_args()
	ffi_args779 := _t1413
	_t1414 := p.parse_terms()
	terms780 := _t1414
	p.consumeLiteral(")")
	_t1415 := &pb.FFI{Name: name778, Args: ffi_args779, Terms: terms780}
	result782 := _t1415
	p.recordSpan(int(span_start781), "FFI")
	return result782
}

func (p *Parser) parse_name() string {
	p.consumeLiteral(":")
	symbol783 := p.consumeTerminal("SYMBOL").Value.str
	return symbol783
}

func (p *Parser) parse_ffi_args() []*pb.Abstraction {
	p.consumeLiteral("(")
	p.consumeLiteral("args")
	xs784 := []*pb.Abstraction{}
	cond785 := p.matchLookaheadLiteral("(", 0)
	for cond785 {
		_t1416 := p.parse_abstraction()
		item786 := _t1416
		xs784 = append(xs784, item786)
		cond785 = p.matchLookaheadLiteral("(", 0)
	}
	abstractions787 := xs784
	p.consumeLiteral(")")
	return abstractions787
}

func (p *Parser) parse_atom() *pb.Atom {
	span_start793 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("atom")
	_t1417 := p.parse_relation_id()
	relation_id788 := _t1417
	xs789 := []*pb.Term{}
	cond790 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond790 {
		_t1418 := p.parse_term()
		item791 := _t1418
		xs789 = append(xs789, item791)
		cond790 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms792 := xs789
	p.consumeLiteral(")")
	_t1419 := &pb.Atom{Name: relation_id788, Terms: terms792}
	result794 := _t1419
	p.recordSpan(int(span_start793), "Atom")
	return result794
}

func (p *Parser) parse_pragma() *pb.Pragma {
	span_start800 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("pragma")
	_t1420 := p.parse_name()
	name795 := _t1420
	xs796 := []*pb.Term{}
	cond797 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond797 {
		_t1421 := p.parse_term()
		item798 := _t1421
		xs796 = append(xs796, item798)
		cond797 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	terms799 := xs796
	p.consumeLiteral(")")
	_t1422 := &pb.Pragma{Name: name795, Terms: terms799}
	result801 := _t1422
	p.recordSpan(int(span_start800), "Pragma")
	return result801
}

func (p *Parser) parse_primitive() *pb.Primitive {
	span_start817 := int64(p.spanStart())
	var _t1423 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1424 int64
		if p.matchLookaheadLiteral("primitive", 1) {
			_t1424 = 9
		} else {
			var _t1425 int64
			if p.matchLookaheadLiteral(">=", 1) {
				_t1425 = 4
			} else {
				var _t1426 int64
				if p.matchLookaheadLiteral(">", 1) {
					_t1426 = 3
				} else {
					var _t1427 int64
					if p.matchLookaheadLiteral("=", 1) {
						_t1427 = 0
					} else {
						var _t1428 int64
						if p.matchLookaheadLiteral("<=", 1) {
							_t1428 = 2
						} else {
							var _t1429 int64
							if p.matchLookaheadLiteral("<", 1) {
								_t1429 = 1
							} else {
								var _t1430 int64
								if p.matchLookaheadLiteral("/", 1) {
									_t1430 = 8
								} else {
									var _t1431 int64
									if p.matchLookaheadLiteral("-", 1) {
										_t1431 = 6
									} else {
										var _t1432 int64
										if p.matchLookaheadLiteral("+", 1) {
											_t1432 = 5
										} else {
											var _t1433 int64
											if p.matchLookaheadLiteral("*", 1) {
												_t1433 = 7
											} else {
												_t1433 = -1
											}
											_t1432 = _t1433
										}
										_t1431 = _t1432
									}
									_t1430 = _t1431
								}
								_t1429 = _t1430
							}
							_t1428 = _t1429
						}
						_t1427 = _t1428
					}
					_t1426 = _t1427
				}
				_t1425 = _t1426
			}
			_t1424 = _t1425
		}
		_t1423 = _t1424
	} else {
		_t1423 = -1
	}
	prediction802 := _t1423
	var _t1434 *pb.Primitive
	if prediction802 == 9 {
		p.consumeLiteral("(")
		p.consumeLiteral("primitive")
		_t1435 := p.parse_name()
		name812 := _t1435
		xs813 := []*pb.RelTerm{}
		cond814 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		for cond814 {
			_t1436 := p.parse_rel_term()
			item815 := _t1436
			xs813 = append(xs813, item815)
			cond814 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
		}
		rel_terms816 := xs813
		p.consumeLiteral(")")
		_t1437 := &pb.Primitive{Name: name812, Terms: rel_terms816}
		_t1434 = _t1437
	} else {
		var _t1438 *pb.Primitive
		if prediction802 == 8 {
			_t1439 := p.parse_divide()
			divide811 := _t1439
			_t1438 = divide811
		} else {
			var _t1440 *pb.Primitive
			if prediction802 == 7 {
				_t1441 := p.parse_multiply()
				multiply810 := _t1441
				_t1440 = multiply810
			} else {
				var _t1442 *pb.Primitive
				if prediction802 == 6 {
					_t1443 := p.parse_minus()
					minus809 := _t1443
					_t1442 = minus809
				} else {
					var _t1444 *pb.Primitive
					if prediction802 == 5 {
						_t1445 := p.parse_add()
						add808 := _t1445
						_t1444 = add808
					} else {
						var _t1446 *pb.Primitive
						if prediction802 == 4 {
							_t1447 := p.parse_gt_eq()
							gt_eq807 := _t1447
							_t1446 = gt_eq807
						} else {
							var _t1448 *pb.Primitive
							if prediction802 == 3 {
								_t1449 := p.parse_gt()
								gt806 := _t1449
								_t1448 = gt806
							} else {
								var _t1450 *pb.Primitive
								if prediction802 == 2 {
									_t1451 := p.parse_lt_eq()
									lt_eq805 := _t1451
									_t1450 = lt_eq805
								} else {
									var _t1452 *pb.Primitive
									if prediction802 == 1 {
										_t1453 := p.parse_lt()
										lt804 := _t1453
										_t1452 = lt804
									} else {
										var _t1454 *pb.Primitive
										if prediction802 == 0 {
											_t1455 := p.parse_eq()
											eq803 := _t1455
											_t1454 = eq803
										} else {
											panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in primitive", p.lookahead(0).Type, p.lookahead(0).Value)})
										}
										_t1452 = _t1454
									}
									_t1450 = _t1452
								}
								_t1448 = _t1450
							}
							_t1446 = _t1448
						}
						_t1444 = _t1446
					}
					_t1442 = _t1444
				}
				_t1440 = _t1442
			}
			_t1438 = _t1440
		}
		_t1434 = _t1438
	}
	result818 := _t1434
	p.recordSpan(int(span_start817), "Primitive")
	return result818
}

func (p *Parser) parse_eq() *pb.Primitive {
	span_start821 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("=")
	_t1456 := p.parse_term()
	term819 := _t1456
	_t1457 := p.parse_term()
	term_3820 := _t1457
	p.consumeLiteral(")")
	_t1458 := &pb.RelTerm{}
	_t1458.RelTermType = &pb.RelTerm_Term{Term: term819}
	_t1459 := &pb.RelTerm{}
	_t1459.RelTermType = &pb.RelTerm_Term{Term: term_3820}
	_t1460 := &pb.Primitive{Name: "rel_primitive_eq", Terms: []*pb.RelTerm{_t1458, _t1459}}
	result822 := _t1460
	p.recordSpan(int(span_start821), "Primitive")
	return result822
}

func (p *Parser) parse_lt() *pb.Primitive {
	span_start825 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<")
	_t1461 := p.parse_term()
	term823 := _t1461
	_t1462 := p.parse_term()
	term_3824 := _t1462
	p.consumeLiteral(")")
	_t1463 := &pb.RelTerm{}
	_t1463.RelTermType = &pb.RelTerm_Term{Term: term823}
	_t1464 := &pb.RelTerm{}
	_t1464.RelTermType = &pb.RelTerm_Term{Term: term_3824}
	_t1465 := &pb.Primitive{Name: "rel_primitive_lt_monotype", Terms: []*pb.RelTerm{_t1463, _t1464}}
	result826 := _t1465
	p.recordSpan(int(span_start825), "Primitive")
	return result826
}

func (p *Parser) parse_lt_eq() *pb.Primitive {
	span_start829 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("<=")
	_t1466 := p.parse_term()
	term827 := _t1466
	_t1467 := p.parse_term()
	term_3828 := _t1467
	p.consumeLiteral(")")
	_t1468 := &pb.RelTerm{}
	_t1468.RelTermType = &pb.RelTerm_Term{Term: term827}
	_t1469 := &pb.RelTerm{}
	_t1469.RelTermType = &pb.RelTerm_Term{Term: term_3828}
	_t1470 := &pb.Primitive{Name: "rel_primitive_lt_eq_monotype", Terms: []*pb.RelTerm{_t1468, _t1469}}
	result830 := _t1470
	p.recordSpan(int(span_start829), "Primitive")
	return result830
}

func (p *Parser) parse_gt() *pb.Primitive {
	span_start833 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">")
	_t1471 := p.parse_term()
	term831 := _t1471
	_t1472 := p.parse_term()
	term_3832 := _t1472
	p.consumeLiteral(")")
	_t1473 := &pb.RelTerm{}
	_t1473.RelTermType = &pb.RelTerm_Term{Term: term831}
	_t1474 := &pb.RelTerm{}
	_t1474.RelTermType = &pb.RelTerm_Term{Term: term_3832}
	_t1475 := &pb.Primitive{Name: "rel_primitive_gt_monotype", Terms: []*pb.RelTerm{_t1473, _t1474}}
	result834 := _t1475
	p.recordSpan(int(span_start833), "Primitive")
	return result834
}

func (p *Parser) parse_gt_eq() *pb.Primitive {
	span_start837 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral(">=")
	_t1476 := p.parse_term()
	term835 := _t1476
	_t1477 := p.parse_term()
	term_3836 := _t1477
	p.consumeLiteral(")")
	_t1478 := &pb.RelTerm{}
	_t1478.RelTermType = &pb.RelTerm_Term{Term: term835}
	_t1479 := &pb.RelTerm{}
	_t1479.RelTermType = &pb.RelTerm_Term{Term: term_3836}
	_t1480 := &pb.Primitive{Name: "rel_primitive_gt_eq_monotype", Terms: []*pb.RelTerm{_t1478, _t1479}}
	result838 := _t1480
	p.recordSpan(int(span_start837), "Primitive")
	return result838
}

func (p *Parser) parse_add() *pb.Primitive {
	span_start842 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("+")
	_t1481 := p.parse_term()
	term839 := _t1481
	_t1482 := p.parse_term()
	term_3840 := _t1482
	_t1483 := p.parse_term()
	term_4841 := _t1483
	p.consumeLiteral(")")
	_t1484 := &pb.RelTerm{}
	_t1484.RelTermType = &pb.RelTerm_Term{Term: term839}
	_t1485 := &pb.RelTerm{}
	_t1485.RelTermType = &pb.RelTerm_Term{Term: term_3840}
	_t1486 := &pb.RelTerm{}
	_t1486.RelTermType = &pb.RelTerm_Term{Term: term_4841}
	_t1487 := &pb.Primitive{Name: "rel_primitive_add_monotype", Terms: []*pb.RelTerm{_t1484, _t1485, _t1486}}
	result843 := _t1487
	p.recordSpan(int(span_start842), "Primitive")
	return result843
}

func (p *Parser) parse_minus() *pb.Primitive {
	span_start847 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("-")
	_t1488 := p.parse_term()
	term844 := _t1488
	_t1489 := p.parse_term()
	term_3845 := _t1489
	_t1490 := p.parse_term()
	term_4846 := _t1490
	p.consumeLiteral(")")
	_t1491 := &pb.RelTerm{}
	_t1491.RelTermType = &pb.RelTerm_Term{Term: term844}
	_t1492 := &pb.RelTerm{}
	_t1492.RelTermType = &pb.RelTerm_Term{Term: term_3845}
	_t1493 := &pb.RelTerm{}
	_t1493.RelTermType = &pb.RelTerm_Term{Term: term_4846}
	_t1494 := &pb.Primitive{Name: "rel_primitive_subtract_monotype", Terms: []*pb.RelTerm{_t1491, _t1492, _t1493}}
	result848 := _t1494
	p.recordSpan(int(span_start847), "Primitive")
	return result848
}

func (p *Parser) parse_multiply() *pb.Primitive {
	span_start852 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("*")
	_t1495 := p.parse_term()
	term849 := _t1495
	_t1496 := p.parse_term()
	term_3850 := _t1496
	_t1497 := p.parse_term()
	term_4851 := _t1497
	p.consumeLiteral(")")
	_t1498 := &pb.RelTerm{}
	_t1498.RelTermType = &pb.RelTerm_Term{Term: term849}
	_t1499 := &pb.RelTerm{}
	_t1499.RelTermType = &pb.RelTerm_Term{Term: term_3850}
	_t1500 := &pb.RelTerm{}
	_t1500.RelTermType = &pb.RelTerm_Term{Term: term_4851}
	_t1501 := &pb.Primitive{Name: "rel_primitive_multiply_monotype", Terms: []*pb.RelTerm{_t1498, _t1499, _t1500}}
	result853 := _t1501
	p.recordSpan(int(span_start852), "Primitive")
	return result853
}

func (p *Parser) parse_divide() *pb.Primitive {
	span_start857 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("/")
	_t1502 := p.parse_term()
	term854 := _t1502
	_t1503 := p.parse_term()
	term_3855 := _t1503
	_t1504 := p.parse_term()
	term_4856 := _t1504
	p.consumeLiteral(")")
	_t1505 := &pb.RelTerm{}
	_t1505.RelTermType = &pb.RelTerm_Term{Term: term854}
	_t1506 := &pb.RelTerm{}
	_t1506.RelTermType = &pb.RelTerm_Term{Term: term_3855}
	_t1507 := &pb.RelTerm{}
	_t1507.RelTermType = &pb.RelTerm_Term{Term: term_4856}
	_t1508 := &pb.Primitive{Name: "rel_primitive_divide_monotype", Terms: []*pb.RelTerm{_t1505, _t1506, _t1507}}
	result858 := _t1508
	p.recordSpan(int(span_start857), "Primitive")
	return result858
}

func (p *Parser) parse_rel_term() *pb.RelTerm {
	span_start862 := int64(p.spanStart())
	var _t1509 int64
	if p.matchLookaheadLiteral("true", 0) {
		_t1509 = 1
	} else {
		var _t1510 int64
		if p.matchLookaheadLiteral("missing", 0) {
			_t1510 = 1
		} else {
			var _t1511 int64
			if p.matchLookaheadLiteral("false", 0) {
				_t1511 = 1
			} else {
				var _t1512 int64
				if p.matchLookaheadLiteral("(", 0) {
					_t1512 = 1
				} else {
					var _t1513 int64
					if p.matchLookaheadLiteral("#", 0) {
						_t1513 = 0
					} else {
						var _t1514 int64
						if p.matchLookaheadTerminal("UINT128", 0) {
							_t1514 = 1
						} else {
							var _t1515 int64
							if p.matchLookaheadTerminal("SYMBOL", 0) {
								_t1515 = 1
							} else {
								var _t1516 int64
								if p.matchLookaheadTerminal("STRING", 0) {
									_t1516 = 1
								} else {
									var _t1517 int64
									if p.matchLookaheadTerminal("INT128", 0) {
										_t1517 = 1
									} else {
										var _t1518 int64
										if p.matchLookaheadTerminal("INT", 0) {
											_t1518 = 1
										} else {
											var _t1519 int64
											if p.matchLookaheadTerminal("FLOAT", 0) {
												_t1519 = 1
											} else {
												var _t1520 int64
												if p.matchLookaheadTerminal("DECIMAL", 0) {
													_t1520 = 1
												} else {
													_t1520 = -1
												}
												_t1519 = _t1520
											}
											_t1518 = _t1519
										}
										_t1517 = _t1518
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
				}
				_t1511 = _t1512
			}
			_t1510 = _t1511
		}
		_t1509 = _t1510
	}
	prediction859 := _t1509
	var _t1521 *pb.RelTerm
	if prediction859 == 1 {
		_t1522 := p.parse_term()
		term861 := _t1522
		_t1523 := &pb.RelTerm{}
		_t1523.RelTermType = &pb.RelTerm_Term{Term: term861}
		_t1521 = _t1523
	} else {
		var _t1524 *pb.RelTerm
		if prediction859 == 0 {
			_t1525 := p.parse_specialized_value()
			specialized_value860 := _t1525
			_t1526 := &pb.RelTerm{}
			_t1526.RelTermType = &pb.RelTerm_SpecializedValue{SpecializedValue: specialized_value860}
			_t1524 = _t1526
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in rel_term", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1521 = _t1524
	}
	result863 := _t1521
	p.recordSpan(int(span_start862), "RelTerm")
	return result863
}

func (p *Parser) parse_specialized_value() *pb.Value {
	span_start865 := int64(p.spanStart())
	p.consumeLiteral("#")
	_t1527 := p.parse_value()
	value864 := _t1527
	result866 := value864
	p.recordSpan(int(span_start865), "Value")
	return result866
}

func (p *Parser) parse_rel_atom() *pb.RelAtom {
	span_start872 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("relatom")
	_t1528 := p.parse_name()
	name867 := _t1528
	xs868 := []*pb.RelTerm{}
	cond869 := (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond869 {
		_t1529 := p.parse_rel_term()
		item870 := _t1529
		xs868 = append(xs868, item870)
		cond869 = (((((((((((p.matchLookaheadLiteral("#", 0) || p.matchLookaheadLiteral("(", 0)) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("SYMBOL", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	rel_terms871 := xs868
	p.consumeLiteral(")")
	_t1530 := &pb.RelAtom{Name: name867, Terms: rel_terms871}
	result873 := _t1530
	p.recordSpan(int(span_start872), "RelAtom")
	return result873
}

func (p *Parser) parse_cast() *pb.Cast {
	span_start876 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("cast")
	_t1531 := p.parse_term()
	term874 := _t1531
	_t1532 := p.parse_term()
	term_3875 := _t1532
	p.consumeLiteral(")")
	_t1533 := &pb.Cast{Input: term874, Result: term_3875}
	result877 := _t1533
	p.recordSpan(int(span_start876), "Cast")
	return result877
}

func (p *Parser) parse_attrs() []*pb.Attribute {
	p.consumeLiteral("(")
	p.consumeLiteral("attrs")
	xs878 := []*pb.Attribute{}
	cond879 := p.matchLookaheadLiteral("(", 0)
	for cond879 {
		_t1534 := p.parse_attribute()
		item880 := _t1534
		xs878 = append(xs878, item880)
		cond879 = p.matchLookaheadLiteral("(", 0)
	}
	attributes881 := xs878
	p.consumeLiteral(")")
	return attributes881
}

func (p *Parser) parse_attribute() *pb.Attribute {
	span_start887 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("attribute")
	_t1535 := p.parse_name()
	name882 := _t1535
	xs883 := []*pb.Value{}
	cond884 := (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	for cond884 {
		_t1536 := p.parse_value()
		item885 := _t1536
		xs883 = append(xs883, item885)
		cond884 = (((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("false", 0)) || p.matchLookaheadLiteral("missing", 0)) || p.matchLookaheadLiteral("true", 0)) || p.matchLookaheadTerminal("DECIMAL", 0)) || p.matchLookaheadTerminal("FLOAT", 0)) || p.matchLookaheadTerminal("INT", 0)) || p.matchLookaheadTerminal("INT128", 0)) || p.matchLookaheadTerminal("STRING", 0)) || p.matchLookaheadTerminal("UINT128", 0))
	}
	values886 := xs883
	p.consumeLiteral(")")
	_t1537 := &pb.Attribute{Name: name882, Args: values886}
	result888 := _t1537
	p.recordSpan(int(span_start887), "Attribute")
	return result888
}

func (p *Parser) parse_algorithm() *pb.Algorithm {
	span_start894 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("algorithm")
	xs889 := []*pb.RelationId{}
	cond890 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond890 {
		_t1538 := p.parse_relation_id()
		item891 := _t1538
		xs889 = append(xs889, item891)
		cond890 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids892 := xs889
	_t1539 := p.parse_script()
	script893 := _t1539
	p.consumeLiteral(")")
	_t1540 := &pb.Algorithm{Global: relation_ids892, Body: script893}
	result895 := _t1540
	p.recordSpan(int(span_start894), "Algorithm")
	return result895
}

func (p *Parser) parse_script() *pb.Script {
	span_start900 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("script")
	xs896 := []*pb.Construct{}
	cond897 := p.matchLookaheadLiteral("(", 0)
	for cond897 {
		_t1541 := p.parse_construct()
		item898 := _t1541
		xs896 = append(xs896, item898)
		cond897 = p.matchLookaheadLiteral("(", 0)
	}
	constructs899 := xs896
	p.consumeLiteral(")")
	_t1542 := &pb.Script{Constructs: constructs899}
	result901 := _t1542
	p.recordSpan(int(span_start900), "Script")
	return result901
}

func (p *Parser) parse_construct() *pb.Construct {
	span_start905 := int64(p.spanStart())
	var _t1543 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1544 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1544 = 1
		} else {
			var _t1545 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1545 = 1
			} else {
				var _t1546 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1546 = 1
				} else {
					var _t1547 int64
					if p.matchLookaheadLiteral("loop", 1) {
						_t1547 = 0
					} else {
						var _t1548 int64
						if p.matchLookaheadLiteral("break", 1) {
							_t1548 = 1
						} else {
							var _t1549 int64
							if p.matchLookaheadLiteral("assign", 1) {
								_t1549 = 1
							} else {
								_t1549 = -1
							}
							_t1548 = _t1549
						}
						_t1547 = _t1548
					}
					_t1546 = _t1547
				}
				_t1545 = _t1546
			}
			_t1544 = _t1545
		}
		_t1543 = _t1544
	} else {
		_t1543 = -1
	}
	prediction902 := _t1543
	var _t1550 *pb.Construct
	if prediction902 == 1 {
		_t1551 := p.parse_instruction()
		instruction904 := _t1551
		_t1552 := &pb.Construct{}
		_t1552.ConstructType = &pb.Construct_Instruction{Instruction: instruction904}
		_t1550 = _t1552
	} else {
		var _t1553 *pb.Construct
		if prediction902 == 0 {
			_t1554 := p.parse_loop()
			loop903 := _t1554
			_t1555 := &pb.Construct{}
			_t1555.ConstructType = &pb.Construct_Loop{Loop: loop903}
			_t1553 = _t1555
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in construct", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1550 = _t1553
	}
	result906 := _t1550
	p.recordSpan(int(span_start905), "Construct")
	return result906
}

func (p *Parser) parse_loop() *pb.Loop {
	span_start909 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("loop")
	_t1556 := p.parse_init()
	init907 := _t1556
	_t1557 := p.parse_script()
	script908 := _t1557
	p.consumeLiteral(")")
	_t1558 := &pb.Loop{Init: init907, Body: script908}
	result910 := _t1558
	p.recordSpan(int(span_start909), "Loop")
	return result910
}

func (p *Parser) parse_init() []*pb.Instruction {
	p.consumeLiteral("(")
	p.consumeLiteral("init")
	xs911 := []*pb.Instruction{}
	cond912 := p.matchLookaheadLiteral("(", 0)
	for cond912 {
		_t1559 := p.parse_instruction()
		item913 := _t1559
		xs911 = append(xs911, item913)
		cond912 = p.matchLookaheadLiteral("(", 0)
	}
	instructions914 := xs911
	p.consumeLiteral(")")
	return instructions914
}

func (p *Parser) parse_instruction() *pb.Instruction {
	span_start921 := int64(p.spanStart())
	var _t1560 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1561 int64
		if p.matchLookaheadLiteral("upsert", 1) {
			_t1561 = 1
		} else {
			var _t1562 int64
			if p.matchLookaheadLiteral("monus", 1) {
				_t1562 = 4
			} else {
				var _t1563 int64
				if p.matchLookaheadLiteral("monoid", 1) {
					_t1563 = 3
				} else {
					var _t1564 int64
					if p.matchLookaheadLiteral("break", 1) {
						_t1564 = 2
					} else {
						var _t1565 int64
						if p.matchLookaheadLiteral("assign", 1) {
							_t1565 = 0
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
		}
		_t1560 = _t1561
	} else {
		_t1560 = -1
	}
	prediction915 := _t1560
	var _t1566 *pb.Instruction
	if prediction915 == 4 {
		_t1567 := p.parse_monus_def()
		monus_def920 := _t1567
		_t1568 := &pb.Instruction{}
		_t1568.InstrType = &pb.Instruction_MonusDef{MonusDef: monus_def920}
		_t1566 = _t1568
	} else {
		var _t1569 *pb.Instruction
		if prediction915 == 3 {
			_t1570 := p.parse_monoid_def()
			monoid_def919 := _t1570
			_t1571 := &pb.Instruction{}
			_t1571.InstrType = &pb.Instruction_MonoidDef{MonoidDef: monoid_def919}
			_t1569 = _t1571
		} else {
			var _t1572 *pb.Instruction
			if prediction915 == 2 {
				_t1573 := p.parse_break()
				break918 := _t1573
				_t1574 := &pb.Instruction{}
				_t1574.InstrType = &pb.Instruction_Break{Break: break918}
				_t1572 = _t1574
			} else {
				var _t1575 *pb.Instruction
				if prediction915 == 1 {
					_t1576 := p.parse_upsert()
					upsert917 := _t1576
					_t1577 := &pb.Instruction{}
					_t1577.InstrType = &pb.Instruction_Upsert{Upsert: upsert917}
					_t1575 = _t1577
				} else {
					var _t1578 *pb.Instruction
					if prediction915 == 0 {
						_t1579 := p.parse_assign()
						assign916 := _t1579
						_t1580 := &pb.Instruction{}
						_t1580.InstrType = &pb.Instruction_Assign{Assign: assign916}
						_t1578 = _t1580
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in instruction", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1575 = _t1578
				}
				_t1572 = _t1575
			}
			_t1569 = _t1572
		}
		_t1566 = _t1569
	}
	result922 := _t1566
	p.recordSpan(int(span_start921), "Instruction")
	return result922
}

func (p *Parser) parse_assign() *pb.Assign {
	span_start926 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("assign")
	_t1581 := p.parse_relation_id()
	relation_id923 := _t1581
	_t1582 := p.parse_abstraction()
	abstraction924 := _t1582
	var _t1583 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1584 := p.parse_attrs()
		_t1583 = _t1584
	}
	attrs925 := _t1583
	p.consumeLiteral(")")
	_t1585 := attrs925
	if attrs925 == nil {
		_t1585 = []*pb.Attribute{}
	}
	_t1586 := &pb.Assign{Name: relation_id923, Body: abstraction924, Attrs: _t1585}
	result927 := _t1586
	p.recordSpan(int(span_start926), "Assign")
	return result927
}

func (p *Parser) parse_upsert() *pb.Upsert {
	span_start931 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("upsert")
	_t1587 := p.parse_relation_id()
	relation_id928 := _t1587
	_t1588 := p.parse_abstraction_with_arity()
	abstraction_with_arity929 := _t1588
	var _t1589 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1590 := p.parse_attrs()
		_t1589 = _t1590
	}
	attrs930 := _t1589
	p.consumeLiteral(")")
	_t1591 := attrs930
	if attrs930 == nil {
		_t1591 = []*pb.Attribute{}
	}
	_t1592 := &pb.Upsert{Name: relation_id928, Body: abstraction_with_arity929[0].(*pb.Abstraction), Attrs: _t1591, ValueArity: abstraction_with_arity929[1].(int64)}
	result932 := _t1592
	p.recordSpan(int(span_start931), "Upsert")
	return result932
}

func (p *Parser) parse_abstraction_with_arity() []interface{} {
	p.consumeLiteral("(")
	_t1593 := p.parse_bindings()
	bindings933 := _t1593
	_t1594 := p.parse_formula()
	formula934 := _t1594
	p.consumeLiteral(")")
	_t1595 := &pb.Abstraction{Vars: listConcat(bindings933[0].([]*pb.Binding), bindings933[1].([]*pb.Binding)), Value: formula934}
	return []interface{}{_t1595, int64(len(bindings933[1].([]*pb.Binding)))}
}

func (p *Parser) parse_break() *pb.Break {
	span_start938 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("break")
	_t1596 := p.parse_relation_id()
	relation_id935 := _t1596
	_t1597 := p.parse_abstraction()
	abstraction936 := _t1597
	var _t1598 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1599 := p.parse_attrs()
		_t1598 = _t1599
	}
	attrs937 := _t1598
	p.consumeLiteral(")")
	_t1600 := attrs937
	if attrs937 == nil {
		_t1600 = []*pb.Attribute{}
	}
	_t1601 := &pb.Break{Name: relation_id935, Body: abstraction936, Attrs: _t1600}
	result939 := _t1601
	p.recordSpan(int(span_start938), "Break")
	return result939
}

func (p *Parser) parse_monoid_def() *pb.MonoidDef {
	span_start944 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monoid")
	_t1602 := p.parse_monoid()
	monoid940 := _t1602
	_t1603 := p.parse_relation_id()
	relation_id941 := _t1603
	_t1604 := p.parse_abstraction_with_arity()
	abstraction_with_arity942 := _t1604
	var _t1605 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1606 := p.parse_attrs()
		_t1605 = _t1606
	}
	attrs943 := _t1605
	p.consumeLiteral(")")
	_t1607 := attrs943
	if attrs943 == nil {
		_t1607 = []*pb.Attribute{}
	}
	_t1608 := &pb.MonoidDef{Monoid: monoid940, Name: relation_id941, Body: abstraction_with_arity942[0].(*pb.Abstraction), Attrs: _t1607, ValueArity: abstraction_with_arity942[1].(int64)}
	result945 := _t1608
	p.recordSpan(int(span_start944), "MonoidDef")
	return result945
}

func (p *Parser) parse_monoid() *pb.Monoid {
	span_start951 := int64(p.spanStart())
	var _t1609 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1610 int64
		if p.matchLookaheadLiteral("sum", 1) {
			_t1610 = 3
		} else {
			var _t1611 int64
			if p.matchLookaheadLiteral("or", 1) {
				_t1611 = 0
			} else {
				var _t1612 int64
				if p.matchLookaheadLiteral("min", 1) {
					_t1612 = 1
				} else {
					var _t1613 int64
					if p.matchLookaheadLiteral("max", 1) {
						_t1613 = 2
					} else {
						_t1613 = -1
					}
					_t1612 = _t1613
				}
				_t1611 = _t1612
			}
			_t1610 = _t1611
		}
		_t1609 = _t1610
	} else {
		_t1609 = -1
	}
	prediction946 := _t1609
	var _t1614 *pb.Monoid
	if prediction946 == 3 {
		_t1615 := p.parse_sum_monoid()
		sum_monoid950 := _t1615
		_t1616 := &pb.Monoid{}
		_t1616.Value = &pb.Monoid_SumMonoid{SumMonoid: sum_monoid950}
		_t1614 = _t1616
	} else {
		var _t1617 *pb.Monoid
		if prediction946 == 2 {
			_t1618 := p.parse_max_monoid()
			max_monoid949 := _t1618
			_t1619 := &pb.Monoid{}
			_t1619.Value = &pb.Monoid_MaxMonoid{MaxMonoid: max_monoid949}
			_t1617 = _t1619
		} else {
			var _t1620 *pb.Monoid
			if prediction946 == 1 {
				_t1621 := p.parse_min_monoid()
				min_monoid948 := _t1621
				_t1622 := &pb.Monoid{}
				_t1622.Value = &pb.Monoid_MinMonoid{MinMonoid: min_monoid948}
				_t1620 = _t1622
			} else {
				var _t1623 *pb.Monoid
				if prediction946 == 0 {
					_t1624 := p.parse_or_monoid()
					or_monoid947 := _t1624
					_t1625 := &pb.Monoid{}
					_t1625.Value = &pb.Monoid_OrMonoid{OrMonoid: or_monoid947}
					_t1623 = _t1625
				} else {
					panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in monoid", p.lookahead(0).Type, p.lookahead(0).Value)})
				}
				_t1620 = _t1623
			}
			_t1617 = _t1620
		}
		_t1614 = _t1617
	}
	result952 := _t1614
	p.recordSpan(int(span_start951), "Monoid")
	return result952
}

func (p *Parser) parse_or_monoid() *pb.OrMonoid {
	span_start953 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("or")
	p.consumeLiteral(")")
	_t1626 := &pb.OrMonoid{}
	result954 := _t1626
	p.recordSpan(int(span_start953), "OrMonoid")
	return result954
}

func (p *Parser) parse_min_monoid() *pb.MinMonoid {
	span_start956 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("min")
	_t1627 := p.parse_type()
	type955 := _t1627
	p.consumeLiteral(")")
	_t1628 := &pb.MinMonoid{Type: type955}
	result957 := _t1628
	p.recordSpan(int(span_start956), "MinMonoid")
	return result957
}

func (p *Parser) parse_max_monoid() *pb.MaxMonoid {
	span_start959 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("max")
	_t1629 := p.parse_type()
	type958 := _t1629
	p.consumeLiteral(")")
	_t1630 := &pb.MaxMonoid{Type: type958}
	result960 := _t1630
	p.recordSpan(int(span_start959), "MaxMonoid")
	return result960
}

func (p *Parser) parse_sum_monoid() *pb.SumMonoid {
	span_start962 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("sum")
	_t1631 := p.parse_type()
	type961 := _t1631
	p.consumeLiteral(")")
	_t1632 := &pb.SumMonoid{Type: type961}
	result963 := _t1632
	p.recordSpan(int(span_start962), "SumMonoid")
	return result963
}

func (p *Parser) parse_monus_def() *pb.MonusDef {
	span_start968 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("monus")
	_t1633 := p.parse_monoid()
	monoid964 := _t1633
	_t1634 := p.parse_relation_id()
	relation_id965 := _t1634
	_t1635 := p.parse_abstraction_with_arity()
	abstraction_with_arity966 := _t1635
	var _t1636 []*pb.Attribute
	if p.matchLookaheadLiteral("(", 0) {
		_t1637 := p.parse_attrs()
		_t1636 = _t1637
	}
	attrs967 := _t1636
	p.consumeLiteral(")")
	_t1638 := attrs967
	if attrs967 == nil {
		_t1638 = []*pb.Attribute{}
	}
	_t1639 := &pb.MonusDef{Monoid: monoid964, Name: relation_id965, Body: abstraction_with_arity966[0].(*pb.Abstraction), Attrs: _t1638, ValueArity: abstraction_with_arity966[1].(int64)}
	result969 := _t1639
	p.recordSpan(int(span_start968), "MonusDef")
	return result969
}

func (p *Parser) parse_constraint() *pb.Constraint {
	span_start974 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("functional_dependency")
	_t1640 := p.parse_relation_id()
	relation_id970 := _t1640
	_t1641 := p.parse_abstraction()
	abstraction971 := _t1641
	_t1642 := p.parse_functional_dependency_keys()
	functional_dependency_keys972 := _t1642
	_t1643 := p.parse_functional_dependency_values()
	functional_dependency_values973 := _t1643
	p.consumeLiteral(")")
	_t1644 := &pb.FunctionalDependency{Guard: abstraction971, Keys: functional_dependency_keys972, Values: functional_dependency_values973}
	_t1645 := &pb.Constraint{Name: relation_id970}
	_t1645.ConstraintType = &pb.Constraint_FunctionalDependency{FunctionalDependency: _t1644}
	result975 := _t1645
	p.recordSpan(int(span_start974), "Constraint")
	return result975
}

func (p *Parser) parse_functional_dependency_keys() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("keys")
	xs976 := []*pb.Var{}
	cond977 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond977 {
		_t1646 := p.parse_var()
		item978 := _t1646
		xs976 = append(xs976, item978)
		cond977 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars979 := xs976
	p.consumeLiteral(")")
	return vars979
}

func (p *Parser) parse_functional_dependency_values() []*pb.Var {
	p.consumeLiteral("(")
	p.consumeLiteral("values")
	xs980 := []*pb.Var{}
	cond981 := p.matchLookaheadTerminal("SYMBOL", 0)
	for cond981 {
		_t1647 := p.parse_var()
		item982 := _t1647
		xs980 = append(xs980, item982)
		cond981 = p.matchLookaheadTerminal("SYMBOL", 0)
	}
	vars983 := xs980
	p.consumeLiteral(")")
	return vars983
}

func (p *Parser) parse_data() *pb.Data {
	span_start988 := int64(p.spanStart())
	var _t1648 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1649 int64
		if p.matchLookaheadLiteral("edb", 1) {
			_t1649 = 0
		} else {
			var _t1650 int64
			if p.matchLookaheadLiteral("csv_data", 1) {
				_t1650 = 2
			} else {
				var _t1651 int64
				if p.matchLookaheadLiteral("betree_relation", 1) {
					_t1651 = 1
				} else {
					_t1651 = -1
				}
				_t1650 = _t1651
			}
			_t1649 = _t1650
		}
		_t1648 = _t1649
	} else {
		_t1648 = -1
	}
	prediction984 := _t1648
	var _t1652 *pb.Data
	if prediction984 == 2 {
		_t1653 := p.parse_csv_data()
		csv_data987 := _t1653
		_t1654 := &pb.Data{}
		_t1654.DataType = &pb.Data_CsvData{CsvData: csv_data987}
		_t1652 = _t1654
	} else {
		var _t1655 *pb.Data
		if prediction984 == 1 {
			_t1656 := p.parse_betree_relation()
			betree_relation986 := _t1656
			_t1657 := &pb.Data{}
			_t1657.DataType = &pb.Data_BetreeRelation{BetreeRelation: betree_relation986}
			_t1655 = _t1657
		} else {
			var _t1658 *pb.Data
			if prediction984 == 0 {
				_t1659 := p.parse_edb()
				edb985 := _t1659
				_t1660 := &pb.Data{}
				_t1660.DataType = &pb.Data_Edb{Edb: edb985}
				_t1658 = _t1660
			} else {
				panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in data", p.lookahead(0).Type, p.lookahead(0).Value)})
			}
			_t1655 = _t1658
		}
		_t1652 = _t1655
	}
	result989 := _t1652
	p.recordSpan(int(span_start988), "Data")
	return result989
}

func (p *Parser) parse_edb() *pb.EDB {
	span_start993 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("edb")
	_t1661 := p.parse_relation_id()
	relation_id990 := _t1661
	_t1662 := p.parse_edb_path()
	edb_path991 := _t1662
	_t1663 := p.parse_edb_types()
	edb_types992 := _t1663
	p.consumeLiteral(")")
	_t1664 := &pb.EDB{TargetId: relation_id990, Path: edb_path991, Types: edb_types992}
	result994 := _t1664
	p.recordSpan(int(span_start993), "EDB")
	return result994
}

func (p *Parser) parse_edb_path() []string {
	p.consumeLiteral("[")
	xs995 := []string{}
	cond996 := p.matchLookaheadTerminal("STRING", 0)
	for cond996 {
		item997 := p.consumeTerminal("STRING").Value.str
		xs995 = append(xs995, item997)
		cond996 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings998 := xs995
	p.consumeLiteral("]")
	return strings998
}

func (p *Parser) parse_edb_types() []*pb.Type {
	p.consumeLiteral("[")
	xs999 := []*pb.Type{}
	cond1000 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1000 {
		_t1665 := p.parse_type()
		item1001 := _t1665
		xs999 = append(xs999, item1001)
		cond1000 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1002 := xs999
	p.consumeLiteral("]")
	return types1002
}

func (p *Parser) parse_betree_relation() *pb.BeTreeRelation {
	span_start1005 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_relation")
	_t1666 := p.parse_relation_id()
	relation_id1003 := _t1666
	_t1667 := p.parse_betree_info()
	betree_info1004 := _t1667
	p.consumeLiteral(")")
	_t1668 := &pb.BeTreeRelation{Name: relation_id1003, RelationInfo: betree_info1004}
	result1006 := _t1668
	p.recordSpan(int(span_start1005), "BeTreeRelation")
	return result1006
}

func (p *Parser) parse_betree_info() *pb.BeTreeInfo {
	span_start1010 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("betree_info")
	_t1669 := p.parse_betree_info_key_types()
	betree_info_key_types1007 := _t1669
	_t1670 := p.parse_betree_info_value_types()
	betree_info_value_types1008 := _t1670
	_t1671 := p.parse_config_dict()
	config_dict1009 := _t1671
	p.consumeLiteral(")")
	_t1672 := p.construct_betree_info(betree_info_key_types1007, betree_info_value_types1008, config_dict1009)
	result1011 := _t1672
	p.recordSpan(int(span_start1010), "BeTreeInfo")
	return result1011
}

func (p *Parser) parse_betree_info_key_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("key_types")
	xs1012 := []*pb.Type{}
	cond1013 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1013 {
		_t1673 := p.parse_type()
		item1014 := _t1673
		xs1012 = append(xs1012, item1014)
		cond1013 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1015 := xs1012
	p.consumeLiteral(")")
	return types1015
}

func (p *Parser) parse_betree_info_value_types() []*pb.Type {
	p.consumeLiteral("(")
	p.consumeLiteral("value_types")
	xs1016 := []*pb.Type{}
	cond1017 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1017 {
		_t1674 := p.parse_type()
		item1018 := _t1674
		xs1016 = append(xs1016, item1018)
		cond1017 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1019 := xs1016
	p.consumeLiteral(")")
	return types1019
}

func (p *Parser) parse_csv_data() *pb.CSVData {
	span_start1024 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_data")
	_t1675 := p.parse_csvlocator()
	csvlocator1020 := _t1675
	_t1676 := p.parse_csv_config()
	csv_config1021 := _t1676
	_t1677 := p.parse_gnf_columns()
	gnf_columns1022 := _t1677
	_t1678 := p.parse_csv_asof()
	csv_asof1023 := _t1678
	p.consumeLiteral(")")
	_t1679 := &pb.CSVData{Locator: csvlocator1020, Config: csv_config1021, Columns: gnf_columns1022, Asof: csv_asof1023}
	result1025 := _t1679
	p.recordSpan(int(span_start1024), "CSVData")
	return result1025
}

func (p *Parser) parse_csvlocator() *pb.CSVLocator {
	span_start1028 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_locator")
	var _t1680 []string
	if (p.matchLookaheadLiteral("(", 0) && p.matchLookaheadLiteral("paths", 1)) {
		_t1681 := p.parse_csv_locator_paths()
		_t1680 = _t1681
	}
	csv_locator_paths1026 := _t1680
	var _t1682 *string
	if p.matchLookaheadLiteral("(", 0) {
		_t1683 := p.parse_csv_locator_inline_data()
		_t1682 = ptr(_t1683)
	}
	csv_locator_inline_data1027 := _t1682
	p.consumeLiteral(")")
	_t1684 := csv_locator_paths1026
	if csv_locator_paths1026 == nil {
		_t1684 = []string{}
	}
	_t1685 := &pb.CSVLocator{Paths: _t1684, InlineData: []byte(deref(csv_locator_inline_data1027, ""))}
	result1029 := _t1685
	p.recordSpan(int(span_start1028), "CSVLocator")
	return result1029
}

func (p *Parser) parse_csv_locator_paths() []string {
	p.consumeLiteral("(")
	p.consumeLiteral("paths")
	xs1030 := []string{}
	cond1031 := p.matchLookaheadTerminal("STRING", 0)
	for cond1031 {
		item1032 := p.consumeTerminal("STRING").Value.str
		xs1030 = append(xs1030, item1032)
		cond1031 = p.matchLookaheadTerminal("STRING", 0)
	}
	strings1033 := xs1030
	p.consumeLiteral(")")
	return strings1033
}

func (p *Parser) parse_csv_locator_inline_data() string {
	p.consumeLiteral("(")
	p.consumeLiteral("inline_data")
	string1034 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1034
}

func (p *Parser) parse_csv_config() *pb.CSVConfig {
	span_start1036 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("csv_config")
	_t1686 := p.parse_config_dict()
	config_dict1035 := _t1686
	p.consumeLiteral(")")
	_t1687 := p.construct_csv_config(config_dict1035)
	result1037 := _t1687
	p.recordSpan(int(span_start1036), "CSVConfig")
	return result1037
}

func (p *Parser) parse_gnf_columns() []*pb.GNFColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1038 := []*pb.GNFColumn{}
	cond1039 := p.matchLookaheadLiteral("(", 0)
	for cond1039 {
		_t1688 := p.parse_gnf_column()
		item1040 := _t1688
		xs1038 = append(xs1038, item1040)
		cond1039 = p.matchLookaheadLiteral("(", 0)
	}
	gnf_columns1041 := xs1038
	p.consumeLiteral(")")
	return gnf_columns1041
}

func (p *Parser) parse_gnf_column() *pb.GNFColumn {
	span_start1048 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	_t1689 := p.parse_gnf_column_path()
	gnf_column_path1042 := _t1689
	var _t1690 *pb.RelationId
	if (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0)) {
		_t1691 := p.parse_relation_id()
		_t1690 = _t1691
	}
	relation_id1043 := _t1690
	p.consumeLiteral("[")
	xs1044 := []*pb.Type{}
	cond1045 := ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	for cond1045 {
		_t1692 := p.parse_type()
		item1046 := _t1692
		xs1044 = append(xs1044, item1046)
		cond1045 = ((((((((((p.matchLookaheadLiteral("(", 0) || p.matchLookaheadLiteral("BOOLEAN", 0)) || p.matchLookaheadLiteral("DATE", 0)) || p.matchLookaheadLiteral("DATETIME", 0)) || p.matchLookaheadLiteral("FLOAT", 0)) || p.matchLookaheadLiteral("INT", 0)) || p.matchLookaheadLiteral("INT128", 0)) || p.matchLookaheadLiteral("MISSING", 0)) || p.matchLookaheadLiteral("STRING", 0)) || p.matchLookaheadLiteral("UINT128", 0)) || p.matchLookaheadLiteral("UNKNOWN", 0))
	}
	types1047 := xs1044
	p.consumeLiteral("]")
	p.consumeLiteral(")")
	_t1693 := &pb.GNFColumn{ColumnPath: gnf_column_path1042, TargetId: relation_id1043, Types: types1047}
	result1049 := _t1693
	p.recordSpan(int(span_start1048), "GNFColumn")
	return result1049
}

func (p *Parser) parse_gnf_column_path() []string {
	var _t1694 int64
	if p.matchLookaheadLiteral("[", 0) {
		_t1694 = 1
	} else {
		var _t1695 int64
		if p.matchLookaheadTerminal("STRING", 0) {
			_t1695 = 0
		} else {
			_t1695 = -1
		}
		_t1694 = _t1695
	}
	prediction1050 := _t1694
	var _t1696 []string
	if prediction1050 == 1 {
		p.consumeLiteral("[")
		xs1052 := []string{}
		cond1053 := p.matchLookaheadTerminal("STRING", 0)
		for cond1053 {
			item1054 := p.consumeTerminal("STRING").Value.str
			xs1052 = append(xs1052, item1054)
			cond1053 = p.matchLookaheadTerminal("STRING", 0)
		}
		strings1055 := xs1052
		p.consumeLiteral("]")
		_t1696 = strings1055
	} else {
		var _t1697 []string
		if prediction1050 == 0 {
			string1051 := p.consumeTerminal("STRING").Value.str
			_ = string1051
			_t1697 = []string{string1051}
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in gnf_column_path", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1696 = _t1697
	}
	return _t1696
}

func (p *Parser) parse_csv_asof() string {
	p.consumeLiteral("(")
	p.consumeLiteral("asof")
	string1056 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1056
}

func (p *Parser) parse_undefine() *pb.Undefine {
	span_start1058 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("undefine")
	_t1698 := p.parse_fragment_id()
	fragment_id1057 := _t1698
	p.consumeLiteral(")")
	_t1699 := &pb.Undefine{FragmentId: fragment_id1057}
	result1059 := _t1699
	p.recordSpan(int(span_start1058), "Undefine")
	return result1059
}

func (p *Parser) parse_context() *pb.Context {
	span_start1064 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("context")
	xs1060 := []*pb.RelationId{}
	cond1061 := (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	for cond1061 {
		_t1700 := p.parse_relation_id()
		item1062 := _t1700
		xs1060 = append(xs1060, item1062)
		cond1061 = (p.matchLookaheadLiteral(":", 0) || p.matchLookaheadTerminal("UINT128", 0))
	}
	relation_ids1063 := xs1060
	p.consumeLiteral(")")
	_t1701 := &pb.Context{Relations: relation_ids1063}
	result1065 := _t1701
	p.recordSpan(int(span_start1064), "Context")
	return result1065
}

func (p *Parser) parse_snapshot() *pb.Snapshot {
	span_start1070 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("snapshot")
	xs1066 := []*pb.SnapshotMapping{}
	cond1067 := p.matchLookaheadLiteral("[", 0)
	for cond1067 {
		_t1702 := p.parse_snapshot_mapping()
		item1068 := _t1702
		xs1066 = append(xs1066, item1068)
		cond1067 = p.matchLookaheadLiteral("[", 0)
	}
	snapshot_mappings1069 := xs1066
	p.consumeLiteral(")")
	_t1703 := &pb.Snapshot{Mappings: snapshot_mappings1069}
	result1071 := _t1703
	p.recordSpan(int(span_start1070), "Snapshot")
	return result1071
}

func (p *Parser) parse_snapshot_mapping() *pb.SnapshotMapping {
	span_start1074 := int64(p.spanStart())
	_t1704 := p.parse_edb_path()
	edb_path1072 := _t1704
	_t1705 := p.parse_relation_id()
	relation_id1073 := _t1705
	_t1706 := &pb.SnapshotMapping{DestinationPath: edb_path1072, SourceRelation: relation_id1073}
	result1075 := _t1706
	p.recordSpan(int(span_start1074), "SnapshotMapping")
	return result1075
}

func (p *Parser) parse_epoch_reads() []*pb.Read {
	p.consumeLiteral("(")
	p.consumeLiteral("reads")
	xs1076 := []*pb.Read{}
	cond1077 := p.matchLookaheadLiteral("(", 0)
	for cond1077 {
		_t1707 := p.parse_read()
		item1078 := _t1707
		xs1076 = append(xs1076, item1078)
		cond1077 = p.matchLookaheadLiteral("(", 0)
	}
	reads1079 := xs1076
	p.consumeLiteral(")")
	return reads1079
}

func (p *Parser) parse_read() *pb.Read {
	span_start1086 := int64(p.spanStart())
	var _t1708 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1709 int64
		if p.matchLookaheadLiteral("what_if", 1) {
			_t1709 = 2
		} else {
			var _t1710 int64
			if p.matchLookaheadLiteral("output", 1) {
				_t1710 = 1
			} else {
				var _t1711 int64
				if p.matchLookaheadLiteral("export", 1) {
					_t1711 = 4
				} else {
					var _t1712 int64
					if p.matchLookaheadLiteral("demand", 1) {
						_t1712 = 0
					} else {
						var _t1713 int64
						if p.matchLookaheadLiteral("abort", 1) {
							_t1713 = 3
						} else {
							_t1713 = -1
						}
						_t1712 = _t1713
					}
					_t1711 = _t1712
				}
				_t1710 = _t1711
			}
			_t1709 = _t1710
		}
		_t1708 = _t1709
	} else {
		_t1708 = -1
	}
	prediction1080 := _t1708
	var _t1714 *pb.Read
	if prediction1080 == 4 {
		_t1715 := p.parse_export()
		export1085 := _t1715
		_t1716 := &pb.Read{}
		_t1716.ReadType = &pb.Read_Export{Export: export1085}
		_t1714 = _t1716
	} else {
		var _t1717 *pb.Read
		if prediction1080 == 3 {
			_t1718 := p.parse_abort()
			abort1084 := _t1718
			_t1719 := &pb.Read{}
			_t1719.ReadType = &pb.Read_Abort{Abort: abort1084}
			_t1717 = _t1719
		} else {
			var _t1720 *pb.Read
			if prediction1080 == 2 {
				_t1721 := p.parse_what_if()
				what_if1083 := _t1721
				_t1722 := &pb.Read{}
				_t1722.ReadType = &pb.Read_WhatIf{WhatIf: what_if1083}
				_t1720 = _t1722
			} else {
				var _t1723 *pb.Read
				if prediction1080 == 1 {
					_t1724 := p.parse_output()
					output1082 := _t1724
					_t1725 := &pb.Read{}
					_t1725.ReadType = &pb.Read_Output{Output: output1082}
					_t1723 = _t1725
				} else {
					var _t1726 *pb.Read
					if prediction1080 == 0 {
						_t1727 := p.parse_demand()
						demand1081 := _t1727
						_t1728 := &pb.Read{}
						_t1728.ReadType = &pb.Read_Demand{Demand: demand1081}
						_t1726 = _t1728
					} else {
						panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in read", p.lookahead(0).Type, p.lookahead(0).Value)})
					}
					_t1723 = _t1726
				}
				_t1720 = _t1723
			}
			_t1717 = _t1720
		}
		_t1714 = _t1717
	}
	result1087 := _t1714
	p.recordSpan(int(span_start1086), "Read")
	return result1087
}

func (p *Parser) parse_demand() *pb.Demand {
	span_start1089 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("demand")
	_t1729 := p.parse_relation_id()
	relation_id1088 := _t1729
	p.consumeLiteral(")")
	_t1730 := &pb.Demand{RelationId: relation_id1088}
	result1090 := _t1730
	p.recordSpan(int(span_start1089), "Demand")
	return result1090
}

func (p *Parser) parse_output() *pb.Output {
	span_start1093 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("output")
	_t1731 := p.parse_name()
	name1091 := _t1731
	_t1732 := p.parse_relation_id()
	relation_id1092 := _t1732
	p.consumeLiteral(")")
	_t1733 := &pb.Output{Name: name1091, RelationId: relation_id1092}
	result1094 := _t1733
	p.recordSpan(int(span_start1093), "Output")
	return result1094
}

func (p *Parser) parse_what_if() *pb.WhatIf {
	span_start1097 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("what_if")
	_t1734 := p.parse_name()
	name1095 := _t1734
	_t1735 := p.parse_epoch()
	epoch1096 := _t1735
	p.consumeLiteral(")")
	_t1736 := &pb.WhatIf{Branch: name1095, Epoch: epoch1096}
	result1098 := _t1736
	p.recordSpan(int(span_start1097), "WhatIf")
	return result1098
}

func (p *Parser) parse_abort() *pb.Abort {
	span_start1101 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("abort")
	var _t1737 *string
	if (p.matchLookaheadLiteral(":", 0) && p.matchLookaheadTerminal("SYMBOL", 1)) {
		_t1738 := p.parse_name()
		_t1737 = ptr(_t1738)
	}
	name1099 := _t1737
	_t1739 := p.parse_relation_id()
	relation_id1100 := _t1739
	p.consumeLiteral(")")
	_t1740 := &pb.Abort{Name: deref(name1099, "abort"), RelationId: relation_id1100}
	result1102 := _t1740
	p.recordSpan(int(span_start1101), "Abort")
	return result1102
}

func (p *Parser) parse_export() *pb.Export {
	span_start1104 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("export")
	_t1741 := p.parse_export_csv_config()
	export_csv_config1103 := _t1741
	p.consumeLiteral(")")
	_t1742 := &pb.Export{}
	_t1742.ExportConfig = &pb.Export_CsvConfig{CsvConfig: export_csv_config1103}
	result1105 := _t1742
	p.recordSpan(int(span_start1104), "Export")
	return result1105
}

func (p *Parser) parse_export_csv_config() *pb.ExportCSVConfig {
	span_start1113 := int64(p.spanStart())
	var _t1743 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1744 int64
		if p.matchLookaheadLiteral("export_csv_config_v2", 1) {
			_t1744 = 0
		} else {
			var _t1745 int64
			if p.matchLookaheadLiteral("export_csv_config", 1) {
				_t1745 = 1
			} else {
				_t1745 = -1
			}
			_t1744 = _t1745
		}
		_t1743 = _t1744
	} else {
		_t1743 = -1
	}
	prediction1106 := _t1743
	var _t1746 *pb.ExportCSVConfig
	if prediction1106 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("export_csv_config")
		_t1747 := p.parse_export_csv_path()
		export_csv_path1110 := _t1747
		_t1748 := p.parse_export_csv_columns_list()
		export_csv_columns_list1111 := _t1748
		_t1749 := p.parse_config_dict()
		config_dict1112 := _t1749
		p.consumeLiteral(")")
		_t1750 := p.construct_export_csv_config(export_csv_path1110, export_csv_columns_list1111, config_dict1112)
		_t1746 = _t1750
	} else {
		var _t1751 *pb.ExportCSVConfig
		if prediction1106 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("export_csv_config_v2")
			_t1752 := p.parse_export_csv_path()
			export_csv_path1107 := _t1752
			_t1753 := p.parse_export_csv_source()
			export_csv_source1108 := _t1753
			_t1754 := p.parse_csv_config()
			csv_config1109 := _t1754
			p.consumeLiteral(")")
			_t1755 := p.construct_export_csv_config_with_source(export_csv_path1107, export_csv_source1108, csv_config1109)
			_t1751 = _t1755
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_config", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1746 = _t1751
	}
	result1114 := _t1746
	p.recordSpan(int(span_start1113), "ExportCSVConfig")
	return result1114
}

func (p *Parser) parse_export_csv_path() string {
	p.consumeLiteral("(")
	p.consumeLiteral("path")
	string1115 := p.consumeTerminal("STRING").Value.str
	p.consumeLiteral(")")
	return string1115
}

func (p *Parser) parse_export_csv_source() *pb.ExportCSVSource {
	span_start1122 := int64(p.spanStart())
	var _t1756 int64
	if p.matchLookaheadLiteral("(", 0) {
		var _t1757 int64
		if p.matchLookaheadLiteral("table_def", 1) {
			_t1757 = 1
		} else {
			var _t1758 int64
			if p.matchLookaheadLiteral("gnf_columns", 1) {
				_t1758 = 0
			} else {
				_t1758 = -1
			}
			_t1757 = _t1758
		}
		_t1756 = _t1757
	} else {
		_t1756 = -1
	}
	prediction1116 := _t1756
	var _t1759 *pb.ExportCSVSource
	if prediction1116 == 1 {
		p.consumeLiteral("(")
		p.consumeLiteral("table_def")
		_t1760 := p.parse_relation_id()
		relation_id1121 := _t1760
		p.consumeLiteral(")")
		_t1761 := &pb.ExportCSVSource{}
		_t1761.CsvSource = &pb.ExportCSVSource_TableDef{TableDef: relation_id1121}
		_t1759 = _t1761
	} else {
		var _t1762 *pb.ExportCSVSource
		if prediction1116 == 0 {
			p.consumeLiteral("(")
			p.consumeLiteral("gnf_columns")
			xs1117 := []*pb.ExportCSVColumn{}
			cond1118 := p.matchLookaheadLiteral("(", 0)
			for cond1118 {
				_t1763 := p.parse_export_csv_column()
				item1119 := _t1763
				xs1117 = append(xs1117, item1119)
				cond1118 = p.matchLookaheadLiteral("(", 0)
			}
			export_csv_columns1120 := xs1117
			p.consumeLiteral(")")
			_t1764 := &pb.ExportCSVColumns{Columns: export_csv_columns1120}
			_t1765 := &pb.ExportCSVSource{}
			_t1765.CsvSource = &pb.ExportCSVSource_GnfColumns{GnfColumns: _t1764}
			_t1762 = _t1765
		} else {
			panic(ParseError{msg: fmt.Sprintf("%s: %s=`%v`", "Unexpected token in export_csv_source", p.lookahead(0).Type, p.lookahead(0).Value)})
		}
		_t1759 = _t1762
	}
	result1123 := _t1759
	p.recordSpan(int(span_start1122), "ExportCSVSource")
	return result1123
}

func (p *Parser) parse_export_csv_column() *pb.ExportCSVColumn {
	span_start1126 := int64(p.spanStart())
	p.consumeLiteral("(")
	p.consumeLiteral("column")
	string1124 := p.consumeTerminal("STRING").Value.str
	_t1766 := p.parse_relation_id()
	relation_id1125 := _t1766
	p.consumeLiteral(")")
	_t1767 := &pb.ExportCSVColumn{ColumnName: string1124, ColumnData: relation_id1125}
	result1127 := _t1767
	p.recordSpan(int(span_start1126), "ExportCSVColumn")
	return result1127
}

func (p *Parser) parse_export_csv_columns_list() []*pb.ExportCSVColumn {
	p.consumeLiteral("(")
	p.consumeLiteral("columns")
	xs1128 := []*pb.ExportCSVColumn{}
	cond1129 := p.matchLookaheadLiteral("(", 0)
	for cond1129 {
		_t1768 := p.parse_export_csv_column()
		item1130 := _t1768
		xs1128 = append(xs1128, item1130)
		cond1129 = p.matchLookaheadLiteral("(", 0)
	}
	export_csv_columns1131 := xs1128
	p.consumeLiteral(")")
	return export_csv_columns1131
}


// ParseTransaction parses the input string and returns (result, provenance, error).
func ParseTransaction(input string) (result *pb.Transaction, provenance map[int]Span, err error) {
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

// ParseFragment parses the input string and returns (result, provenance, error).
func ParseFragment(input string) (result *pb.Fragment, provenance map[int]Span, err error) {
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
	result = parser.parse_fragment()

	// Check for unconsumed tokens (except EOF)
	if parser.pos < len(parser.tokens) {
		remainingToken := parser.lookahead(0)
		if remainingToken.Type != "$" {
			return nil, nil, ParseError{msg: fmt.Sprintf("Unexpected token at end of input: %v", remainingToken)}
		}
	}
	return result, parser.Provenance, nil
}

// Parse parses the input string and returns (result, provenance, error).
func Parse(input string) (result *pb.Transaction, provenance map[int]Span, err error) {
	return ParseTransaction(input)
}
