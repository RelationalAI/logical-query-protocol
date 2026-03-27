// Auto-generated pretty printer.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the pretty printer, edit the generator code
// in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
//
// Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer go

package lqp

import (
	"bytes"
	"fmt"
	"math"
	"math/big"
	"reflect"
	"sort"
	"strconv"
	"strings"

	pb "github.com/RelationalAI/logical-query-protocol/sdks/go/src/lqp/v1"
)

const maxWidth = 92

// PrettyPrinter holds state for pretty printing protobuf messages.
type PrettyPrinter struct {
	w                       *bytes.Buffer
	indentStack             []int
	column                  int
	atLineStart             bool
	separator               string
	maxWidth                int
	computing               map[uintptr]bool
	memo                    map[uintptr]string
	memoRefs                []interface{}
	debugInfo               map[[2]uint64]string
	printSymbolicRelationIds bool
}

func (p *PrettyPrinter) indentLevel() int {
	if len(p.indentStack) > 0 {
		return p.indentStack[len(p.indentStack)-1]
	}
	return 0
}

func (p *PrettyPrinter) write(s string) {
	if p.separator == "\n" && p.atLineStart && strings.TrimSpace(s) != "" {
		spaces := p.indentLevel()
		p.w.WriteString(strings.Repeat(" ", spaces))
		p.column = spaces
		p.atLineStart = false
	}
	p.w.WriteString(s)
	if idx := strings.LastIndex(s, "\n"); idx >= 0 {
		p.column = len(s) - idx - 1
	} else {
		p.column += len(s)
	}
}

func (p *PrettyPrinter) newline() {
	p.w.WriteString(p.separator)
	if p.separator == "\n" {
		p.atLineStart = true
		p.column = 0
	}
}

func (p *PrettyPrinter) indent() {
	if p.separator == "\n" {
		p.indentStack = append(p.indentStack, p.column)
	}
}

func (p *PrettyPrinter) indentSexp() {
	if p.separator == "\n" {
		p.indentStack = append(p.indentStack, p.indentLevel()+2)
	}
}

func (p *PrettyPrinter) dedent() {
	if p.separator == "\n" && len(p.indentStack) > 1 {
		p.indentStack = p.indentStack[:len(p.indentStack)-1]
	}
}

func (p *PrettyPrinter) tryFlat(msg interface{}, prettyFn func()) *string {
	v := reflect.ValueOf(msg)
	// Only memoize pointer types. Slices share underlying array
	// pointers (especially nil/empty slices), causing collisions.
	canMemo := v.Kind() == reflect.Ptr
	if canMemo {
		key := v.Pointer()
		if _, ok := p.memo[key]; !ok && !p.computing[key] {
			p.computing[key] = true
			flat := p.renderFlat(prettyFn)
			p.memo[key] = flat
			p.memoRefs = append(p.memoRefs, msg)
			delete(p.computing, key)
		}
		if flat, ok := p.memo[key]; ok {
			return p.fitsWidth(flat)
		}
		return nil
	}
	// If already in flat mode, return nil to prevent infinite recursion.
	if p.separator != "\n" {
		return nil
	}
	flat := p.renderFlat(prettyFn)
	return p.fitsWidth(flat)
}

func (p *PrettyPrinter) renderFlat(prettyFn func()) string {
	savedW := p.w
	savedSep := p.separator
	savedIndent := p.indentStack
	savedCol := p.column
	savedAtLineStart := p.atLineStart
	var buf bytes.Buffer
	p.w = &buf
	p.separator = " "
	p.indentStack = []int{0}
	p.column = 0
	p.atLineStart = false
	prettyFn()
	result := buf.String()
	p.w = savedW
	p.separator = savedSep
	p.indentStack = savedIndent
	p.column = savedCol
	p.atLineStart = savedAtLineStart
	return result
}

func (p *PrettyPrinter) fitsWidth(flat string) *string {
	if p.separator != "\n" {
		return &flat
	}
	effectiveCol := p.column
	if p.atLineStart {
		effectiveCol = p.indentLevel()
	}
	if len(flat)+effectiveCol <= p.maxWidth {
		return &flat
	}
	return nil
}

func (p *PrettyPrinter) getOutput() string {
	return p.w.String()
}

// formatDecimal formats a DecimalValue as "<digits>d<precision>".
func (p *PrettyPrinter) formatDecimal(msg *pb.DecimalValue) string {
	low := msg.GetValue().GetLow()
	high := msg.GetValue().GetHigh()

	// Compute 128-bit signed integer from high/low
	intVal := new(big.Int).SetUint64(high)
	intVal.Lsh(intVal, 64)
	intVal.Add(intVal, new(big.Int).SetUint64(low))
	if high&(1<<63) != 0 {
		// Negative: subtract 2^128
		twoTo128 := new(big.Int).Lsh(big.NewInt(1), 128)
		intVal.Sub(intVal, twoTo128)
	}

	sign := ""
	if intVal.Sign() < 0 {
		sign = "-"
		intVal.Neg(intVal)
	}

	digits := intVal.String()
	scale := int(msg.GetScale())
	precision := msg.GetPrecision()

	var decimalStr string
	if scale <= 0 {
		decimalStr = digits + "." + strings.Repeat("0", -scale)
	} else if scale >= len(digits) {
		decimalStr = "0." + strings.Repeat("0", scale-len(digits)) + digits
	} else {
		decimalStr = digits[:len(digits)-scale] + "." + digits[len(digits)-scale:]
	}

	return fmt.Sprintf("%s%sd%d", sign, decimalStr, precision)
}

// formatInt128 formats an Int128Value as "<value>i128".
func (p *PrettyPrinter) formatInt128(msg *pb.Int128Value) string {
	return int128ToString(msg.GetLow(), msg.GetHigh()) + "i128"
}

// formatUint128 formats a UInt128Value as "0x<hex>".
func (p *PrettyPrinter) formatUint128(msg *pb.UInt128Value) string {
	return "0x" + uint128ToHexString(msg.GetLow(), msg.GetHigh())
}

// formatStringValue escapes and quotes a string for LQP output.
func (p *PrettyPrinter) formatStringValue(s string) string {
	escaped := strings.ReplaceAll(s, "\\", "\\\\")
	escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
	escaped = strings.ReplaceAll(escaped, "\n", "\\n")
	escaped = strings.ReplaceAll(escaped, "\r", "\\r")
	escaped = strings.ReplaceAll(escaped, "\t", "\\t")
	return "\"" + escaped + "\""
}

// fragmentIdToString decodes a FragmentId's bytes to a string.
func (p *PrettyPrinter) fragmentIdToString(msg *pb.FragmentId) string {
	if msg.GetId() == nil {
		return ""
	}
	return string(msg.GetId())
}

// startPrettyFragment extracts debug info from a Fragment for relation ID lookup.
func (p *PrettyPrinter) startPrettyFragment(msg *pb.Fragment) {
	debugInfo := msg.GetDebugInfo()
	if debugInfo == nil {
		return
	}
	ids := debugInfo.GetIds()
	names := debugInfo.GetOrigNames()
	for i, rid := range ids {
		if i < len(names) {
			key := [2]uint64{rid.GetIdLow(), rid.GetIdHigh()}
			p.debugInfo[key] = names[i]
		}
	}
}

// relationIdToString looks up a RelationId in the debug info map.
func (p *PrettyPrinter) relationIdToString(msg *pb.RelationId) *string {
	if !p.printSymbolicRelationIds {
		return nil
	}
	key := [2]uint64{msg.GetIdLow(), msg.GetIdHigh()}
	if name, ok := p.debugInfo[key]; ok {
		return &name
	}
	return nil
}

// relationIdToUint128 converts a RelationId to a UInt128Value.
func (p *PrettyPrinter) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
}

// listSort sorts a slice of []interface{} pairs by their first element (string key).
func listSort(pairs [][]interface{}) [][]interface{} {
	sort.Slice(pairs, func(i, j int) bool {
		ki, _ := pairs[i][0].(string)
		kj, _ := pairs[j][0].(string)
		return ki < kj
	})
	return pairs
}

// dictToPairs converts map[string]string to sorted key/value rows for pretty printing.
func dictToPairs(m map[string]string) [][]interface{} {
	if len(m) == 0 {
		return nil
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([][]interface{}, 0, len(keys))
	for _, k := range keys {
		out = append(out, []interface{}{k, m[k]})
	}
	return out
}

// --- Free functions ---

func uint128ToString(low, high uint64) string {
	if high == 0 {
		return fmt.Sprintf("%d", low)
	}
	result := new(big.Int).SetUint64(high)
	result.Lsh(result, 64)
	result.Add(result, new(big.Int).SetUint64(low))
	return result.String()
}

func int128ToString(low, high uint64) string {
	isNegative := (high & 0x8000000000000000) != 0
	if !isNegative {
		return uint128ToString(low, high)
	}
	result := new(big.Int).SetUint64(^high)
	result.Lsh(result, 64)
	result.Add(result, new(big.Int).SetUint64(^low))
	result.Add(result, big.NewInt(1))
	return "-" + result.String()
}

func uint128ToHexString(low, high uint64) string {
	if high == 0 {
		return fmt.Sprintf("%x", low)
	}
	return fmt.Sprintf("%x%016x", high, low)
}

func formatFloat64(v float64) string {
	s := fmt.Sprintf("%g", v)
	// Match Python's str(float) output: lowercase, no leading +.
	s = strings.ToLower(s)
	s = strings.TrimPrefix(s, "+")
	if !strings.ContainsAny(s, ".einn") {
		s += ".0"
	}
	return s
}

func formatFloat32(v float32) string {
	if math.IsInf(float64(v), 0) {
		return "inf32"
	}
	if math.IsNaN(float64(v)) {
		return "nan32"
	}
	return fmt.Sprintf("%sf32", strconv.FormatFloat(float64(v), 'g', -1, 32))
}

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1689 := &pb.Value{}
	_t1689.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1689
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1690 := &pb.Value{}
	_t1690.Value = &pb.Value_IntValue{IntValue: v}
	return _t1690
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1691 := &pb.Value{}
	_t1691.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1691
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1692 := &pb.Value{}
	_t1692.Value = &pb.Value_StringValue{StringValue: v}
	return _t1692
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1693 := &pb.Value{}
	_t1693.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1693
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1694 := &pb.Value{}
	_t1694.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1694
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1695 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1695})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1696 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1696})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1697 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1697})
			}
		}
	}
	_t1698 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1698})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1699 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1699})
	_t1700 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1700})
	if msg.GetNewLine() != "" {
		_t1701 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1701})
	}
	_t1702 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1702})
	_t1703 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1703})
	_t1704 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1704})
	if msg.GetComment() != "" {
		_t1705 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1705})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1706 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1706})
	}
	_t1707 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1707})
	_t1708 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1708})
	_t1709 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1709})
	if msg.GetPartitionSizeMb() != 0 {
		_t1710 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1710})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1711 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1711})
	_t1712 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1712})
	_t1713 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1713})
	_t1714 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1714})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1715 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1715})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1716 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1716})
		}
	}
	_t1717 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1717})
	_t1718 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1718})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1719 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1719})
	}
	if msg.Compression != nil {
		_t1720 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1720})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1721 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1721})
	}
	if msg.SyntaxMissingString != nil {
		_t1722 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1722})
	}
	if msg.SyntaxDelim != nil {
		_t1723 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1723})
	}
	if msg.SyntaxQuotechar != nil {
		_t1724 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1724})
	}
	if msg.SyntaxEscapechar != nil {
		_t1725 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1725})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1726 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1726
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1727 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1727
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1728 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1728})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1729 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1729})
	}
	if msg.GetCompression() != "" {
		_t1730 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1730})
	}
	var _t1731 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1731
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1732 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1732
	return nil
}

func (p *PrettyPrinter) deconstruct_bindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *PrettyPrinter) deconstruct_bindings_with_arity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

// --- Pretty-print methods ---

func (p *PrettyPrinter) pretty_transaction(msg *pb.Transaction) interface{} {
	flat784 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat784 != nil {
		p.write(*flat784)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1550 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1550 = _dollar_dollar.GetConfigure()
		}
		var _t1551 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1551 = _dollar_dollar.GetSync()
		}
		fields775 := []interface{}{_t1550, _t1551, _dollar_dollar.GetEpochs()}
		unwrapped_fields776 := fields775
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field777 := unwrapped_fields776[0].(*pb.Configure)
		if field777 != nil {
			p.newline()
			opt_val778 := field777
			p.pretty_configure(opt_val778)
		}
		field779 := unwrapped_fields776[1].(*pb.Sync)
		if field779 != nil {
			p.newline()
			opt_val780 := field779
			p.pretty_sync(opt_val780)
		}
		field781 := unwrapped_fields776[2].([]*pb.Epoch)
		if !(len(field781) == 0) {
			p.newline()
			for i783, elem782 := range field781 {
				if (i783 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem782)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat787 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat787 != nil {
		p.write(*flat787)
		return nil
	} else {
		_dollar_dollar := msg
		_t1552 := p.deconstruct_configure(_dollar_dollar)
		fields785 := _t1552
		unwrapped_fields786 := fields785
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields786)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat791 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat791 != nil {
		p.write(*flat791)
		return nil
	} else {
		fields788 := msg
		p.write("{")
		p.indent()
		if !(len(fields788) == 0) {
			p.newline()
			for i790, elem789 := range fields788 {
				if (i790 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem789)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat796 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat796 != nil {
		p.write(*flat796)
		return nil
	} else {
		_dollar_dollar := msg
		fields792 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields793 := fields792
		p.write(":")
		field794 := unwrapped_fields793[0].(string)
		p.write(field794)
		p.write(" ")
		field795 := unwrapped_fields793[1].(*pb.Value)
		p.pretty_raw_value(field795)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat822 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat822 != nil {
		p.write(*flat822)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1553 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1553 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result820 := _t1553
		if deconstruct_result820 != nil {
			unwrapped821 := deconstruct_result820
			p.pretty_raw_date(unwrapped821)
		} else {
			_dollar_dollar := msg
			var _t1554 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1554 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result818 := _t1554
			if deconstruct_result818 != nil {
				unwrapped819 := deconstruct_result818
				p.pretty_raw_datetime(unwrapped819)
			} else {
				_dollar_dollar := msg
				var _t1555 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1555 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result816 := _t1555
				if deconstruct_result816 != nil {
					unwrapped817 := *deconstruct_result816
					p.write(p.formatStringValue(unwrapped817))
				} else {
					_dollar_dollar := msg
					var _t1556 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1556 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result814 := _t1556
					if deconstruct_result814 != nil {
						unwrapped815 := *deconstruct_result814
						p.write(fmt.Sprintf("%di32", unwrapped815))
					} else {
						_dollar_dollar := msg
						var _t1557 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1557 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result812 := _t1557
						if deconstruct_result812 != nil {
							unwrapped813 := *deconstruct_result812
							p.write(fmt.Sprintf("%d", unwrapped813))
						} else {
							_dollar_dollar := msg
							var _t1558 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1558 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result810 := _t1558
							if deconstruct_result810 != nil {
								unwrapped811 := *deconstruct_result810
								p.write(formatFloat32(unwrapped811))
							} else {
								_dollar_dollar := msg
								var _t1559 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1559 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result808 := _t1559
								if deconstruct_result808 != nil {
									unwrapped809 := *deconstruct_result808
									p.write(formatFloat64(unwrapped809))
								} else {
									_dollar_dollar := msg
									var _t1560 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1560 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result806 := _t1560
									if deconstruct_result806 != nil {
										unwrapped807 := *deconstruct_result806
										p.write(fmt.Sprintf("%du32", unwrapped807))
									} else {
										_dollar_dollar := msg
										var _t1561 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1561 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result804 := _t1561
										if deconstruct_result804 != nil {
											unwrapped805 := deconstruct_result804
											p.write(p.formatUint128(unwrapped805))
										} else {
											_dollar_dollar := msg
											var _t1562 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1562 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result802 := _t1562
											if deconstruct_result802 != nil {
												unwrapped803 := deconstruct_result802
												p.write(p.formatInt128(unwrapped803))
											} else {
												_dollar_dollar := msg
												var _t1563 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1563 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result800 := _t1563
												if deconstruct_result800 != nil {
													unwrapped801 := deconstruct_result800
													p.write(p.formatDecimal(unwrapped801))
												} else {
													_dollar_dollar := msg
													var _t1564 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1564 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result798 := _t1564
													if deconstruct_result798 != nil {
														unwrapped799 := *deconstruct_result798
														p.pretty_boolean_value(unwrapped799)
													} else {
														fields797 := msg
														_ = fields797
														p.write("missing")
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_date(msg *pb.DateValue) interface{} {
	flat828 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat828 != nil {
		p.write(*flat828)
		return nil
	} else {
		_dollar_dollar := msg
		fields823 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields824 := fields823
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field825 := unwrapped_fields824[0].(int64)
		p.write(fmt.Sprintf("%d", field825))
		p.newline()
		field826 := unwrapped_fields824[1].(int64)
		p.write(fmt.Sprintf("%d", field826))
		p.newline()
		field827 := unwrapped_fields824[2].(int64)
		p.write(fmt.Sprintf("%d", field827))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat839 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat839 != nil {
		p.write(*flat839)
		return nil
	} else {
		_dollar_dollar := msg
		fields829 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields830 := fields829
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field831 := unwrapped_fields830[0].(int64)
		p.write(fmt.Sprintf("%d", field831))
		p.newline()
		field832 := unwrapped_fields830[1].(int64)
		p.write(fmt.Sprintf("%d", field832))
		p.newline()
		field833 := unwrapped_fields830[2].(int64)
		p.write(fmt.Sprintf("%d", field833))
		p.newline()
		field834 := unwrapped_fields830[3].(int64)
		p.write(fmt.Sprintf("%d", field834))
		p.newline()
		field835 := unwrapped_fields830[4].(int64)
		p.write(fmt.Sprintf("%d", field835))
		p.newline()
		field836 := unwrapped_fields830[5].(int64)
		p.write(fmt.Sprintf("%d", field836))
		field837 := unwrapped_fields830[6].(*int64)
		if field837 != nil {
			p.newline()
			opt_val838 := *field837
			p.write(fmt.Sprintf("%d", opt_val838))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1565 []interface{}
	if _dollar_dollar {
		_t1565 = []interface{}{}
	}
	deconstruct_result842 := _t1565
	if deconstruct_result842 != nil {
		unwrapped843 := deconstruct_result842
		_ = unwrapped843
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1566 []interface{}
		if !(_dollar_dollar) {
			_t1566 = []interface{}{}
		}
		deconstruct_result840 := _t1566
		if deconstruct_result840 != nil {
			unwrapped841 := deconstruct_result840
			_ = unwrapped841
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat848 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat848 != nil {
		p.write(*flat848)
		return nil
	} else {
		_dollar_dollar := msg
		fields844 := _dollar_dollar.GetFragments()
		unwrapped_fields845 := fields844
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields845) == 0) {
			p.newline()
			for i847, elem846 := range unwrapped_fields845 {
				if (i847 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem846)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat851 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat851 != nil {
		p.write(*flat851)
		return nil
	} else {
		_dollar_dollar := msg
		fields849 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields850 := fields849
		p.write(":")
		p.write(unwrapped_fields850)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1567 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1567 = _dollar_dollar.GetWrites()
		}
		var _t1568 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1568 = _dollar_dollar.GetReads()
		}
		fields852 := []interface{}{_t1567, _t1568}
		unwrapped_fields853 := fields852
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field854 := unwrapped_fields853[0].([]*pb.Write)
		if field854 != nil {
			p.newline()
			opt_val855 := field854
			p.pretty_epoch_writes(opt_val855)
		}
		field856 := unwrapped_fields853[1].([]*pb.Read)
		if field856 != nil {
			p.newline()
			opt_val857 := field856
			p.pretty_epoch_reads(opt_val857)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat862 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		fields859 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields859) == 0) {
			p.newline()
			for i861, elem860 := range fields859 {
				if (i861 > 0) {
					p.newline()
				}
				p.pretty_write(elem860)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1569 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1569 = _dollar_dollar.GetDefine()
		}
		deconstruct_result869 := _t1569
		if deconstruct_result869 != nil {
			unwrapped870 := deconstruct_result869
			p.pretty_define(unwrapped870)
		} else {
			_dollar_dollar := msg
			var _t1570 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1570 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result867 := _t1570
			if deconstruct_result867 != nil {
				unwrapped868 := deconstruct_result867
				p.pretty_undefine(unwrapped868)
			} else {
				_dollar_dollar := msg
				var _t1571 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1571 = _dollar_dollar.GetContext()
				}
				deconstruct_result865 := _t1571
				if deconstruct_result865 != nil {
					unwrapped866 := deconstruct_result865
					p.pretty_context(unwrapped866)
				} else {
					_dollar_dollar := msg
					var _t1572 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1572 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result863 := _t1572
					if deconstruct_result863 != nil {
						unwrapped864 := deconstruct_result863
						p.pretty_snapshot(unwrapped864)
					} else {
						panic(ParseError{msg: "No matching rule for write"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_define(msg *pb.Define) interface{} {
	flat874 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat874 != nil {
		p.write(*flat874)
		return nil
	} else {
		_dollar_dollar := msg
		fields872 := _dollar_dollar.GetFragment()
		unwrapped_fields873 := fields872
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields873)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat881 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat881 != nil {
		p.write(*flat881)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields875 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields876 := fields875
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field877 := unwrapped_fields876[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field877)
		field878 := unwrapped_fields876[1].([]*pb.Declaration)
		if !(len(field878) == 0) {
			p.newline()
			for i880, elem879 := range field878 {
				if (i880 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem879)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat883 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat883 != nil {
		p.write(*flat883)
		return nil
	} else {
		fields882 := msg
		p.pretty_fragment_id(fields882)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat892 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat892 != nil {
		p.write(*flat892)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1573 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1573 = _dollar_dollar.GetDef()
		}
		deconstruct_result890 := _t1573
		if deconstruct_result890 != nil {
			unwrapped891 := deconstruct_result890
			p.pretty_def(unwrapped891)
		} else {
			_dollar_dollar := msg
			var _t1574 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1574 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result888 := _t1574
			if deconstruct_result888 != nil {
				unwrapped889 := deconstruct_result888
				p.pretty_algorithm(unwrapped889)
			} else {
				_dollar_dollar := msg
				var _t1575 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1575 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result886 := _t1575
				if deconstruct_result886 != nil {
					unwrapped887 := deconstruct_result886
					p.pretty_constraint(unwrapped887)
				} else {
					_dollar_dollar := msg
					var _t1576 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1576 = _dollar_dollar.GetData()
					}
					deconstruct_result884 := _t1576
					if deconstruct_result884 != nil {
						unwrapped885 := deconstruct_result884
						p.pretty_data(unwrapped885)
					} else {
						panic(ParseError{msg: "No matching rule for declaration"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_def(msg *pb.Def) interface{} {
	flat899 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1577 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1577 = _dollar_dollar.GetAttrs()
		}
		fields893 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1577}
		unwrapped_fields894 := fields893
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field895 := unwrapped_fields894[0].(*pb.RelationId)
		p.pretty_relation_id(field895)
		p.newline()
		field896 := unwrapped_fields894[1].(*pb.Abstraction)
		p.pretty_abstraction(field896)
		field897 := unwrapped_fields894[2].([]*pb.Attribute)
		if field897 != nil {
			p.newline()
			opt_val898 := field897
			p.pretty_attrs(opt_val898)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat904 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1578 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1579 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1578 = ptr(_t1579)
		}
		deconstruct_result902 := _t1578
		if deconstruct_result902 != nil {
			unwrapped903 := *deconstruct_result902
			p.write(":")
			p.write(unwrapped903)
		} else {
			_dollar_dollar := msg
			_t1580 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result900 := _t1580
			if deconstruct_result900 != nil {
				unwrapped901 := deconstruct_result900
				p.write(p.formatUint128(unwrapped901))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat909 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat909 != nil {
		p.write(*flat909)
		return nil
	} else {
		_dollar_dollar := msg
		_t1581 := p.deconstruct_bindings(_dollar_dollar)
		fields905 := []interface{}{_t1581, _dollar_dollar.GetValue()}
		unwrapped_fields906 := fields905
		p.write("(")
		p.indent()
		field907 := unwrapped_fields906[0].([]interface{})
		p.pretty_bindings(field907)
		p.newline()
		field908 := unwrapped_fields906[1].(*pb.Formula)
		p.pretty_formula(field908)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1582 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1582 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields910 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1582}
		unwrapped_fields911 := fields910
		p.write("[")
		p.indent()
		field912 := unwrapped_fields911[0].([]*pb.Binding)
		for i914, elem913 := range field912 {
			if (i914 > 0) {
				p.newline()
			}
			p.pretty_binding(elem913)
		}
		field915 := unwrapped_fields911[1].([]*pb.Binding)
		if field915 != nil {
			p.newline()
			opt_val916 := field915
			p.pretty_value_bindings(opt_val916)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat922 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat922 != nil {
		p.write(*flat922)
		return nil
	} else {
		_dollar_dollar := msg
		fields918 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields919 := fields918
		field920 := unwrapped_fields919[0].(string)
		p.write(field920)
		p.write("::")
		field921 := unwrapped_fields919[1].(*pb.Type)
		p.pretty_type(field921)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat951 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat951 != nil {
		p.write(*flat951)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1583 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1583 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result949 := _t1583
		if deconstruct_result949 != nil {
			unwrapped950 := deconstruct_result949
			p.pretty_unspecified_type(unwrapped950)
		} else {
			_dollar_dollar := msg
			var _t1584 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1584 = _dollar_dollar.GetStringType()
			}
			deconstruct_result947 := _t1584
			if deconstruct_result947 != nil {
				unwrapped948 := deconstruct_result947
				p.pretty_string_type(unwrapped948)
			} else {
				_dollar_dollar := msg
				var _t1585 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1585 = _dollar_dollar.GetIntType()
				}
				deconstruct_result945 := _t1585
				if deconstruct_result945 != nil {
					unwrapped946 := deconstruct_result945
					p.pretty_int_type(unwrapped946)
				} else {
					_dollar_dollar := msg
					var _t1586 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1586 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result943 := _t1586
					if deconstruct_result943 != nil {
						unwrapped944 := deconstruct_result943
						p.pretty_float_type(unwrapped944)
					} else {
						_dollar_dollar := msg
						var _t1587 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1587 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result941 := _t1587
						if deconstruct_result941 != nil {
							unwrapped942 := deconstruct_result941
							p.pretty_uint128_type(unwrapped942)
						} else {
							_dollar_dollar := msg
							var _t1588 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1588 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result939 := _t1588
							if deconstruct_result939 != nil {
								unwrapped940 := deconstruct_result939
								p.pretty_int128_type(unwrapped940)
							} else {
								_dollar_dollar := msg
								var _t1589 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1589 = _dollar_dollar.GetDateType()
								}
								deconstruct_result937 := _t1589
								if deconstruct_result937 != nil {
									unwrapped938 := deconstruct_result937
									p.pretty_date_type(unwrapped938)
								} else {
									_dollar_dollar := msg
									var _t1590 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1590 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result935 := _t1590
									if deconstruct_result935 != nil {
										unwrapped936 := deconstruct_result935
										p.pretty_datetime_type(unwrapped936)
									} else {
										_dollar_dollar := msg
										var _t1591 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1591 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result933 := _t1591
										if deconstruct_result933 != nil {
											unwrapped934 := deconstruct_result933
											p.pretty_missing_type(unwrapped934)
										} else {
											_dollar_dollar := msg
											var _t1592 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1592 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result931 := _t1592
											if deconstruct_result931 != nil {
												unwrapped932 := deconstruct_result931
												p.pretty_decimal_type(unwrapped932)
											} else {
												_dollar_dollar := msg
												var _t1593 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1593 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result929 := _t1593
												if deconstruct_result929 != nil {
													unwrapped930 := deconstruct_result929
													p.pretty_boolean_type(unwrapped930)
												} else {
													_dollar_dollar := msg
													var _t1594 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1594 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result927 := _t1594
													if deconstruct_result927 != nil {
														unwrapped928 := deconstruct_result927
														p.pretty_int32_type(unwrapped928)
													} else {
														_dollar_dollar := msg
														var _t1595 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1595 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result925 := _t1595
														if deconstruct_result925 != nil {
															unwrapped926 := deconstruct_result925
															p.pretty_float32_type(unwrapped926)
														} else {
															_dollar_dollar := msg
															var _t1596 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1596 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result923 := _t1596
															if deconstruct_result923 != nil {
																unwrapped924 := deconstruct_result923
																p.pretty_uint32_type(unwrapped924)
															} else {
																panic(ParseError{msg: "No matching rule for type"})
															}
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields952 := msg
	_ = fields952
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields953 := msg
	_ = fields953
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields954 := msg
	_ = fields954
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields955 := msg
	_ = fields955
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields956 := msg
	_ = fields956
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields957 := msg
	_ = fields957
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields958 := msg
	_ = fields958
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields959 := msg
	_ = fields959
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields960 := msg
	_ = fields960
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat965 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat965 != nil {
		p.write(*flat965)
		return nil
	} else {
		_dollar_dollar := msg
		fields961 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields962 := fields961
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field963 := unwrapped_fields962[0].(int64)
		p.write(fmt.Sprintf("%d", field963))
		p.newline()
		field964 := unwrapped_fields962[1].(int64)
		p.write(fmt.Sprintf("%d", field964))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields966 := msg
	_ = fields966
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields967 := msg
	_ = fields967
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields968 := msg
	_ = fields968
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields969 := msg
	_ = fields969
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat973 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat973 != nil {
		p.write(*flat973)
		return nil
	} else {
		fields970 := msg
		p.write("|")
		if !(len(fields970) == 0) {
			p.write(" ")
			for i972, elem971 := range fields970 {
				if (i972 > 0) {
					p.newline()
				}
				p.pretty_binding(elem971)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1000 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1000 != nil {
		p.write(*flat1000)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1597 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1597 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result998 := _t1597
		if deconstruct_result998 != nil {
			unwrapped999 := deconstruct_result998
			p.pretty_true(unwrapped999)
		} else {
			_dollar_dollar := msg
			var _t1598 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1598 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result996 := _t1598
			if deconstruct_result996 != nil {
				unwrapped997 := deconstruct_result996
				p.pretty_false(unwrapped997)
			} else {
				_dollar_dollar := msg
				var _t1599 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1599 = _dollar_dollar.GetExists()
				}
				deconstruct_result994 := _t1599
				if deconstruct_result994 != nil {
					unwrapped995 := deconstruct_result994
					p.pretty_exists(unwrapped995)
				} else {
					_dollar_dollar := msg
					var _t1600 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1600 = _dollar_dollar.GetReduce()
					}
					deconstruct_result992 := _t1600
					if deconstruct_result992 != nil {
						unwrapped993 := deconstruct_result992
						p.pretty_reduce(unwrapped993)
					} else {
						_dollar_dollar := msg
						var _t1601 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1601 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result990 := _t1601
						if deconstruct_result990 != nil {
							unwrapped991 := deconstruct_result990
							p.pretty_conjunction(unwrapped991)
						} else {
							_dollar_dollar := msg
							var _t1602 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1602 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result988 := _t1602
							if deconstruct_result988 != nil {
								unwrapped989 := deconstruct_result988
								p.pretty_disjunction(unwrapped989)
							} else {
								_dollar_dollar := msg
								var _t1603 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1603 = _dollar_dollar.GetNot()
								}
								deconstruct_result986 := _t1603
								if deconstruct_result986 != nil {
									unwrapped987 := deconstruct_result986
									p.pretty_not(unwrapped987)
								} else {
									_dollar_dollar := msg
									var _t1604 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1604 = _dollar_dollar.GetFfi()
									}
									deconstruct_result984 := _t1604
									if deconstruct_result984 != nil {
										unwrapped985 := deconstruct_result984
										p.pretty_ffi(unwrapped985)
									} else {
										_dollar_dollar := msg
										var _t1605 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1605 = _dollar_dollar.GetAtom()
										}
										deconstruct_result982 := _t1605
										if deconstruct_result982 != nil {
											unwrapped983 := deconstruct_result982
											p.pretty_atom(unwrapped983)
										} else {
											_dollar_dollar := msg
											var _t1606 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1606 = _dollar_dollar.GetPragma()
											}
											deconstruct_result980 := _t1606
											if deconstruct_result980 != nil {
												unwrapped981 := deconstruct_result980
												p.pretty_pragma(unwrapped981)
											} else {
												_dollar_dollar := msg
												var _t1607 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1607 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result978 := _t1607
												if deconstruct_result978 != nil {
													unwrapped979 := deconstruct_result978
													p.pretty_primitive(unwrapped979)
												} else {
													_dollar_dollar := msg
													var _t1608 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1608 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result976 := _t1608
													if deconstruct_result976 != nil {
														unwrapped977 := deconstruct_result976
														p.pretty_rel_atom(unwrapped977)
													} else {
														_dollar_dollar := msg
														var _t1609 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1609 = _dollar_dollar.GetCast()
														}
														deconstruct_result974 := _t1609
														if deconstruct_result974 != nil {
															unwrapped975 := deconstruct_result974
															p.pretty_cast(unwrapped975)
														} else {
															panic(ParseError{msg: "No matching rule for formula"})
														}
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_true(msg *pb.Conjunction) interface{} {
	fields1001 := msg
	_ = fields1001
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1002 := msg
	_ = fields1002
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		_dollar_dollar := msg
		_t1610 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1003 := []interface{}{_t1610, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1004 := fields1003
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1005 := unwrapped_fields1004[0].([]interface{})
		p.pretty_bindings(field1005)
		p.newline()
		field1006 := unwrapped_fields1004[1].(*pb.Formula)
		p.pretty_formula(field1006)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1013 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		_dollar_dollar := msg
		fields1008 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1009 := fields1008
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1010 := unwrapped_fields1009[0].(*pb.Abstraction)
		p.pretty_abstraction(field1010)
		p.newline()
		field1011 := unwrapped_fields1009[1].(*pb.Abstraction)
		p.pretty_abstraction(field1011)
		p.newline()
		field1012 := unwrapped_fields1009[2].([]*pb.Term)
		p.pretty_terms(field1012)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1017 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1017 != nil {
		p.write(*flat1017)
		return nil
	} else {
		fields1014 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1014) == 0) {
			p.newline()
			for i1016, elem1015 := range fields1014 {
				if (i1016 > 0) {
					p.newline()
				}
				p.pretty_term(elem1015)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1022 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1022 != nil {
		p.write(*flat1022)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1611 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1611 = _dollar_dollar.GetVar()
		}
		deconstruct_result1020 := _t1611
		if deconstruct_result1020 != nil {
			unwrapped1021 := deconstruct_result1020
			p.pretty_var(unwrapped1021)
		} else {
			_dollar_dollar := msg
			var _t1612 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1612 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1018 := _t1612
			if deconstruct_result1018 != nil {
				unwrapped1019 := deconstruct_result1018
				p.pretty_value(unwrapped1019)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_dollar_dollar := msg
		fields1023 := _dollar_dollar.GetName()
		unwrapped_fields1024 := fields1023
		p.write(unwrapped_fields1024)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1613 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1613 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1049 := _t1613
		if deconstruct_result1049 != nil {
			unwrapped1050 := deconstruct_result1049
			p.pretty_date(unwrapped1050)
		} else {
			_dollar_dollar := msg
			var _t1614 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1614 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1047 := _t1614
			if deconstruct_result1047 != nil {
				unwrapped1048 := deconstruct_result1047
				p.pretty_datetime(unwrapped1048)
			} else {
				_dollar_dollar := msg
				var _t1615 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1615 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1045 := _t1615
				if deconstruct_result1045 != nil {
					unwrapped1046 := *deconstruct_result1045
					p.write(p.formatStringValue(unwrapped1046))
				} else {
					_dollar_dollar := msg
					var _t1616 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1616 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1043 := _t1616
					if deconstruct_result1043 != nil {
						unwrapped1044 := *deconstruct_result1043
						p.write(fmt.Sprintf("%di32", unwrapped1044))
					} else {
						_dollar_dollar := msg
						var _t1617 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1617 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1041 := _t1617
						if deconstruct_result1041 != nil {
							unwrapped1042 := *deconstruct_result1041
							p.write(fmt.Sprintf("%d", unwrapped1042))
						} else {
							_dollar_dollar := msg
							var _t1618 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1618 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1039 := _t1618
							if deconstruct_result1039 != nil {
								unwrapped1040 := *deconstruct_result1039
								p.write(formatFloat32(unwrapped1040))
							} else {
								_dollar_dollar := msg
								var _t1619 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1619 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1037 := _t1619
								if deconstruct_result1037 != nil {
									unwrapped1038 := *deconstruct_result1037
									p.write(formatFloat64(unwrapped1038))
								} else {
									_dollar_dollar := msg
									var _t1620 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1620 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1035 := _t1620
									if deconstruct_result1035 != nil {
										unwrapped1036 := *deconstruct_result1035
										p.write(fmt.Sprintf("%du32", unwrapped1036))
									} else {
										_dollar_dollar := msg
										var _t1621 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1621 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1033 := _t1621
										if deconstruct_result1033 != nil {
											unwrapped1034 := deconstruct_result1033
											p.write(p.formatUint128(unwrapped1034))
										} else {
											_dollar_dollar := msg
											var _t1622 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1622 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1031 := _t1622
											if deconstruct_result1031 != nil {
												unwrapped1032 := deconstruct_result1031
												p.write(p.formatInt128(unwrapped1032))
											} else {
												_dollar_dollar := msg
												var _t1623 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1623 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1029 := _t1623
												if deconstruct_result1029 != nil {
													unwrapped1030 := deconstruct_result1029
													p.write(p.formatDecimal(unwrapped1030))
												} else {
													_dollar_dollar := msg
													var _t1624 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1624 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1027 := _t1624
													if deconstruct_result1027 != nil {
														unwrapped1028 := *deconstruct_result1027
														p.pretty_boolean_value(unwrapped1028)
													} else {
														fields1026 := msg
														_ = fields1026
														p.write("missing")
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) interface{} {
	flat1057 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1057 != nil {
		p.write(*flat1057)
		return nil
	} else {
		_dollar_dollar := msg
		fields1052 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1053 := fields1052
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1054 := unwrapped_fields1053[0].(int64)
		p.write(fmt.Sprintf("%d", field1054))
		p.newline()
		field1055 := unwrapped_fields1053[1].(int64)
		p.write(fmt.Sprintf("%d", field1055))
		p.newline()
		field1056 := unwrapped_fields1053[2].(int64)
		p.write(fmt.Sprintf("%d", field1056))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1068 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1068 != nil {
		p.write(*flat1068)
		return nil
	} else {
		_dollar_dollar := msg
		fields1058 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1059 := fields1058
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1060 := unwrapped_fields1059[0].(int64)
		p.write(fmt.Sprintf("%d", field1060))
		p.newline()
		field1061 := unwrapped_fields1059[1].(int64)
		p.write(fmt.Sprintf("%d", field1061))
		p.newline()
		field1062 := unwrapped_fields1059[2].(int64)
		p.write(fmt.Sprintf("%d", field1062))
		p.newline()
		field1063 := unwrapped_fields1059[3].(int64)
		p.write(fmt.Sprintf("%d", field1063))
		p.newline()
		field1064 := unwrapped_fields1059[4].(int64)
		p.write(fmt.Sprintf("%d", field1064))
		p.newline()
		field1065 := unwrapped_fields1059[5].(int64)
		p.write(fmt.Sprintf("%d", field1065))
		field1066 := unwrapped_fields1059[6].(*int64)
		if field1066 != nil {
			p.newline()
			opt_val1067 := *field1066
			p.write(fmt.Sprintf("%d", opt_val1067))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1073 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1073 != nil {
		p.write(*flat1073)
		return nil
	} else {
		_dollar_dollar := msg
		fields1069 := _dollar_dollar.GetArgs()
		unwrapped_fields1070 := fields1069
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1070) == 0) {
			p.newline()
			for i1072, elem1071 := range unwrapped_fields1070 {
				if (i1072 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1071)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1078 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1078 != nil {
		p.write(*flat1078)
		return nil
	} else {
		_dollar_dollar := msg
		fields1074 := _dollar_dollar.GetArgs()
		unwrapped_fields1075 := fields1074
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1075) == 0) {
			p.newline()
			for i1077, elem1076 := range unwrapped_fields1075 {
				if (i1077 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1076)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1081 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		_dollar_dollar := msg
		fields1079 := _dollar_dollar.GetArg()
		unwrapped_fields1080 := fields1079
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1080)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1087 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1087 != nil {
		p.write(*flat1087)
		return nil
	} else {
		_dollar_dollar := msg
		fields1082 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].(string)
		p.pretty_name(field1084)
		p.newline()
		field1085 := unwrapped_fields1083[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1085)
		p.newline()
		field1086 := unwrapped_fields1083[2].([]*pb.Term)
		p.pretty_terms(field1086)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		fields1088 := msg
		p.write(":")
		p.write(fields1088)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1093 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		fields1090 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1090) == 0) {
			p.newline()
			for i1092, elem1091 := range fields1090 {
				if (i1092 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1091)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		_dollar_dollar := msg
		fields1094 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1095 := fields1094
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1096 := unwrapped_fields1095[0].(*pb.RelationId)
		p.pretty_relation_id(field1096)
		field1097 := unwrapped_fields1095[1].([]*pb.Term)
		if !(len(field1097) == 0) {
			p.newline()
			for i1099, elem1098 := range field1097 {
				if (i1099 > 0) {
					p.newline()
				}
				p.pretty_term(elem1098)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		fields1101 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1103 := unwrapped_fields1102[0].(string)
		p.pretty_name(field1103)
		field1104 := unwrapped_fields1102[1].([]*pb.Term)
		if !(len(field1104) == 0) {
			p.newline()
			for i1106, elem1105 := range field1104 {
				if (i1106 > 0) {
					p.newline()
				}
				p.pretty_term(elem1105)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1625 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1122 := _t1625
		if guard_result1122 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1626 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1626 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1121 := _t1626
			if guard_result1121 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1627 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1627 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1120 := _t1627
				if guard_result1120 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1628 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1628 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1119 := _t1628
					if guard_result1119 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1629 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1629 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1118 := _t1629
						if guard_result1118 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1630 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1630 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1117 := _t1630
							if guard_result1117 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1631 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1631 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1116 := _t1631
								if guard_result1116 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1632 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1632 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1115 := _t1632
									if guard_result1115 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1633 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1633 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1114 := _t1633
										if guard_result1114 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1108 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1109 := fields1108
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1110 := unwrapped_fields1109[0].(string)
											p.pretty_name(field1110)
											field1111 := unwrapped_fields1109[1].([]*pb.RelTerm)
											if !(len(field1111) == 0) {
												p.newline()
												for i1113, elem1112 := range field1111 {
													if (i1113 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1112)
												}
											}
											p.dedent()
											p.write(")")
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_eq(msg *pb.Primitive) interface{} {
	flat1128 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1128 != nil {
		p.write(*flat1128)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1634 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1634 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1124 := _t1634
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1126 := unwrapped_fields1125[0].(*pb.Term)
		p.pretty_term(field1126)
		p.newline()
		field1127 := unwrapped_fields1125[1].(*pb.Term)
		p.pretty_term(field1127)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1133 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1133 != nil {
		p.write(*flat1133)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1635 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1129 := _t1635
		unwrapped_fields1130 := fields1129
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1131 := unwrapped_fields1130[0].(*pb.Term)
		p.pretty_term(field1131)
		p.newline()
		field1132 := unwrapped_fields1130[1].(*pb.Term)
		p.pretty_term(field1132)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1636 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1636 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1134 := _t1636
		unwrapped_fields1135 := fields1134
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1136 := unwrapped_fields1135[0].(*pb.Term)
		p.pretty_term(field1136)
		p.newline()
		field1137 := unwrapped_fields1135[1].(*pb.Term)
		p.pretty_term(field1137)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1637 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1139 := _t1637
		unwrapped_fields1140 := fields1139
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1141 := unwrapped_fields1140[0].(*pb.Term)
		p.pretty_term(field1141)
		p.newline()
		field1142 := unwrapped_fields1140[1].(*pb.Term)
		p.pretty_term(field1142)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1148 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1148 != nil {
		p.write(*flat1148)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1638 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1638 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1144 := _t1638
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1146 := unwrapped_fields1145[0].(*pb.Term)
		p.pretty_term(field1146)
		p.newline()
		field1147 := unwrapped_fields1145[1].(*pb.Term)
		p.pretty_term(field1147)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1154 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1154 != nil {
		p.write(*flat1154)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1639 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1639 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1149 := _t1639
		unwrapped_fields1150 := fields1149
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1151 := unwrapped_fields1150[0].(*pb.Term)
		p.pretty_term(field1151)
		p.newline()
		field1152 := unwrapped_fields1150[1].(*pb.Term)
		p.pretty_term(field1152)
		p.newline()
		field1153 := unwrapped_fields1150[2].(*pb.Term)
		p.pretty_term(field1153)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1640 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1640 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1155 := _t1640
		unwrapped_fields1156 := fields1155
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1157 := unwrapped_fields1156[0].(*pb.Term)
		p.pretty_term(field1157)
		p.newline()
		field1158 := unwrapped_fields1156[1].(*pb.Term)
		p.pretty_term(field1158)
		p.newline()
		field1159 := unwrapped_fields1156[2].(*pb.Term)
		p.pretty_term(field1159)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1166 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1166 != nil {
		p.write(*flat1166)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1641 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1161 := _t1641
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1163 := unwrapped_fields1162[0].(*pb.Term)
		p.pretty_term(field1163)
		p.newline()
		field1164 := unwrapped_fields1162[1].(*pb.Term)
		p.pretty_term(field1164)
		p.newline()
		field1165 := unwrapped_fields1162[2].(*pb.Term)
		p.pretty_term(field1165)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1642 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1642 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1167 := _t1642
		unwrapped_fields1168 := fields1167
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1169 := unwrapped_fields1168[0].(*pb.Term)
		p.pretty_term(field1169)
		p.newline()
		field1170 := unwrapped_fields1168[1].(*pb.Term)
		p.pretty_term(field1170)
		p.newline()
		field1171 := unwrapped_fields1168[2].(*pb.Term)
		p.pretty_term(field1171)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1177 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1177 != nil {
		p.write(*flat1177)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1643 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1643 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1175 := _t1643
		if deconstruct_result1175 != nil {
			unwrapped1176 := deconstruct_result1175
			p.pretty_specialized_value(unwrapped1176)
		} else {
			_dollar_dollar := msg
			var _t1644 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1644 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1173 := _t1644
			if deconstruct_result1173 != nil {
				unwrapped1174 := deconstruct_result1173
				p.pretty_term(unwrapped1174)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		fields1178 := msg
		p.write("#")
		p.pretty_raw_value(fields1178)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		fields1180 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(string)
		p.pretty_name(field1182)
		field1183 := unwrapped_fields1181[1].([]*pb.RelTerm)
		if !(len(field1183) == 0) {
			p.newline()
			for i1185, elem1184 := range field1183 {
				if (i1185 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1184)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1191 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1191 != nil {
		p.write(*flat1191)
		return nil
	} else {
		_dollar_dollar := msg
		fields1187 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1189 := unwrapped_fields1188[0].(*pb.Term)
		p.pretty_term(field1189)
		p.newline()
		field1190 := unwrapped_fields1188[1].(*pb.Term)
		p.pretty_term(field1190)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1195 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1195 != nil {
		p.write(*flat1195)
		return nil
	} else {
		fields1192 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1192) == 0) {
			p.newline()
			for i1194, elem1193 := range fields1192 {
				if (i1194 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1193)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_dollar_dollar := msg
		fields1196 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1197 := fields1196
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1198 := unwrapped_fields1197[0].(string)
		p.pretty_name(field1198)
		field1199 := unwrapped_fields1197[1].([]*pb.Value)
		if !(len(field1199) == 0) {
			p.newline()
			for i1201, elem1200 := range field1199 {
				if (i1201 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1200)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_dollar_dollar := msg
		fields1203 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1205 := unwrapped_fields1204[0].([]*pb.RelationId)
		if !(len(field1205) == 0) {
			p.newline()
			for i1207, elem1206 := range field1205 {
				if (i1207 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1206)
			}
		}
		p.newline()
		field1208 := unwrapped_fields1204[1].(*pb.Script)
		p.pretty_script(field1208)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_dollar_dollar := msg
		fields1210 := _dollar_dollar.GetConstructs()
		unwrapped_fields1211 := fields1210
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1211) == 0) {
			p.newline()
			for i1213, elem1212 := range unwrapped_fields1211 {
				if (i1213 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1212)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1645 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1217 := _t1645
		if deconstruct_result1217 != nil {
			unwrapped1218 := deconstruct_result1217
			p.pretty_loop(unwrapped1218)
		} else {
			_dollar_dollar := msg
			var _t1646 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1646 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1215 := _t1646
			if deconstruct_result1215 != nil {
				unwrapped1216 := deconstruct_result1215
				p.pretty_instruction(unwrapped1216)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		_dollar_dollar := msg
		fields1220 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1221 := fields1220
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1222 := unwrapped_fields1221[0].([]*pb.Instruction)
		p.pretty_init(field1222)
		p.newline()
		field1223 := unwrapped_fields1221[1].(*pb.Script)
		p.pretty_script(field1223)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1228 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1228 != nil {
		p.write(*flat1228)
		return nil
	} else {
		fields1225 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1225) == 0) {
			p.newline()
			for i1227, elem1226 := range fields1225 {
				if (i1227 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1226)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1239 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1239 != nil {
		p.write(*flat1239)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1647 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1237 := _t1647
		if deconstruct_result1237 != nil {
			unwrapped1238 := deconstruct_result1237
			p.pretty_assign(unwrapped1238)
		} else {
			_dollar_dollar := msg
			var _t1648 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1648 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1235 := _t1648
			if deconstruct_result1235 != nil {
				unwrapped1236 := deconstruct_result1235
				p.pretty_upsert(unwrapped1236)
			} else {
				_dollar_dollar := msg
				var _t1649 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1649 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1233 := _t1649
				if deconstruct_result1233 != nil {
					unwrapped1234 := deconstruct_result1233
					p.pretty_break(unwrapped1234)
				} else {
					_dollar_dollar := msg
					var _t1650 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1650 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1231 := _t1650
					if deconstruct_result1231 != nil {
						unwrapped1232 := deconstruct_result1231
						p.pretty_monoid_def(unwrapped1232)
					} else {
						_dollar_dollar := msg
						var _t1651 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1651 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1229 := _t1651
						if deconstruct_result1229 != nil {
							unwrapped1230 := deconstruct_result1229
							p.pretty_monus_def(unwrapped1230)
						} else {
							panic(ParseError{msg: "No matching rule for instruction"})
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_assign(msg *pb.Assign) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1652 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1652 = _dollar_dollar.GetAttrs()
		}
		fields1240 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1652}
		unwrapped_fields1241 := fields1240
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1242 := unwrapped_fields1241[0].(*pb.RelationId)
		p.pretty_relation_id(field1242)
		p.newline()
		field1243 := unwrapped_fields1241[1].(*pb.Abstraction)
		p.pretty_abstraction(field1243)
		field1244 := unwrapped_fields1241[2].([]*pb.Attribute)
		if field1244 != nil {
			p.newline()
			opt_val1245 := field1244
			p.pretty_attrs(opt_val1245)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1653 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1653 = _dollar_dollar.GetAttrs()
		}
		fields1247 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1653}
		unwrapped_fields1248 := fields1247
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1249 := unwrapped_fields1248[0].(*pb.RelationId)
		p.pretty_relation_id(field1249)
		p.newline()
		field1250 := unwrapped_fields1248[1].([]interface{})
		p.pretty_abstraction_with_arity(field1250)
		field1251 := unwrapped_fields1248[2].([]*pb.Attribute)
		if field1251 != nil {
			p.newline()
			opt_val1252 := field1251
			p.pretty_attrs(opt_val1252)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_dollar_dollar := msg
		_t1654 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1254 := []interface{}{_t1654, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.indent()
		field1256 := unwrapped_fields1255[0].([]interface{})
		p.pretty_bindings(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].(*pb.Formula)
		p.pretty_formula(field1257)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1265 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1655 = _dollar_dollar.GetAttrs()
		}
		fields1259 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1655}
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1261 := unwrapped_fields1260[0].(*pb.RelationId)
		p.pretty_relation_id(field1261)
		p.newline()
		field1262 := unwrapped_fields1260[1].(*pb.Abstraction)
		p.pretty_abstraction(field1262)
		field1263 := unwrapped_fields1260[2].([]*pb.Attribute)
		if field1263 != nil {
			p.newline()
			opt_val1264 := field1263
			p.pretty_attrs(opt_val1264)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1273 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1273 != nil {
		p.write(*flat1273)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1656 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1656 = _dollar_dollar.GetAttrs()
		}
		fields1266 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1656}
		unwrapped_fields1267 := fields1266
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1268 := unwrapped_fields1267[0].(*pb.Monoid)
		p.pretty_monoid(field1268)
		p.newline()
		field1269 := unwrapped_fields1267[1].(*pb.RelationId)
		p.pretty_relation_id(field1269)
		p.newline()
		field1270 := unwrapped_fields1267[2].([]interface{})
		p.pretty_abstraction_with_arity(field1270)
		field1271 := unwrapped_fields1267[3].([]*pb.Attribute)
		if field1271 != nil {
			p.newline()
			opt_val1272 := field1271
			p.pretty_attrs(opt_val1272)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1282 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1282 != nil {
		p.write(*flat1282)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1657 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1657 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1280 := _t1657
		if deconstruct_result1280 != nil {
			unwrapped1281 := deconstruct_result1280
			p.pretty_or_monoid(unwrapped1281)
		} else {
			_dollar_dollar := msg
			var _t1658 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1658 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1278 := _t1658
			if deconstruct_result1278 != nil {
				unwrapped1279 := deconstruct_result1278
				p.pretty_min_monoid(unwrapped1279)
			} else {
				_dollar_dollar := msg
				var _t1659 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1659 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1276 := _t1659
				if deconstruct_result1276 != nil {
					unwrapped1277 := deconstruct_result1276
					p.pretty_max_monoid(unwrapped1277)
				} else {
					_dollar_dollar := msg
					var _t1660 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1660 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1274 := _t1660
					if deconstruct_result1274 != nil {
						unwrapped1275 := deconstruct_result1274
						p.pretty_sum_monoid(unwrapped1275)
					} else {
						panic(ParseError{msg: "No matching rule for monoid"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_or_monoid(msg *pb.OrMonoid) interface{} {
	fields1283 := msg
	_ = fields1283
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		fields1284 := _dollar_dollar.GetType()
		unwrapped_fields1285 := fields1284
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1285)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		fields1287 := _dollar_dollar.GetType()
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1288)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1292 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1292 != nil {
		p.write(*flat1292)
		return nil
	} else {
		_dollar_dollar := msg
		fields1290 := _dollar_dollar.GetType()
		unwrapped_fields1291 := fields1290
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1291)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1300 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1300 != nil {
		p.write(*flat1300)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1661 = _dollar_dollar.GetAttrs()
		}
		fields1293 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1661}
		unwrapped_fields1294 := fields1293
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1295 := unwrapped_fields1294[0].(*pb.Monoid)
		p.pretty_monoid(field1295)
		p.newline()
		field1296 := unwrapped_fields1294[1].(*pb.RelationId)
		p.pretty_relation_id(field1296)
		p.newline()
		field1297 := unwrapped_fields1294[2].([]interface{})
		p.pretty_abstraction_with_arity(field1297)
		field1298 := unwrapped_fields1294[3].([]*pb.Attribute)
		if field1298 != nil {
			p.newline()
			opt_val1299 := field1298
			p.pretty_attrs(opt_val1299)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		_dollar_dollar := msg
		fields1301 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1302 := fields1301
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1303 := unwrapped_fields1302[0].(*pb.RelationId)
		p.pretty_relation_id(field1303)
		p.newline()
		field1304 := unwrapped_fields1302[1].(*pb.Abstraction)
		p.pretty_abstraction(field1304)
		p.newline()
		field1305 := unwrapped_fields1302[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1305)
		p.newline()
		field1306 := unwrapped_fields1302[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1306)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1311 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		fields1308 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1308) == 0) {
			p.newline()
			for i1310, elem1309 := range fields1308 {
				if (i1310 > 0) {
					p.newline()
				}
				p.pretty_var(elem1309)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1315 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1315 != nil {
		p.write(*flat1315)
		return nil
	} else {
		fields1312 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1312) == 0) {
			p.newline()
			for i1314, elem1313 := range fields1312 {
				if (i1314 > 0) {
					p.newline()
				}
				p.pretty_var(elem1313)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1662 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1662 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1322 := _t1662
		if deconstruct_result1322 != nil {
			unwrapped1323 := deconstruct_result1322
			p.pretty_edb(unwrapped1323)
		} else {
			_dollar_dollar := msg
			var _t1663 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1663 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1320 := _t1663
			if deconstruct_result1320 != nil {
				unwrapped1321 := deconstruct_result1320
				p.pretty_betree_relation(unwrapped1321)
			} else {
				_dollar_dollar := msg
				var _t1664 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1664 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1318 := _t1664
				if deconstruct_result1318 != nil {
					unwrapped1319 := deconstruct_result1318
					p.pretty_csv_data(unwrapped1319)
				} else {
					_dollar_dollar := msg
					var _t1665 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1665 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1316 := _t1665
					if deconstruct_result1316 != nil {
						unwrapped1317 := deconstruct_result1316
						p.pretty_iceberg_data(unwrapped1317)
					} else {
						panic(ParseError{msg: "No matching rule for data"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		_dollar_dollar := msg
		fields1325 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1326 := fields1325
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1327 := unwrapped_fields1326[0].(*pb.RelationId)
		p.pretty_relation_id(field1327)
		p.newline()
		field1328 := unwrapped_fields1326[1].([]string)
		p.pretty_edb_path(field1328)
		p.newline()
		field1329 := unwrapped_fields1326[2].([]*pb.Type)
		p.pretty_edb_types(field1329)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1334 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1334 != nil {
		p.write(*flat1334)
		return nil
	} else {
		fields1331 := msg
		p.write("[")
		p.indent()
		for i1333, elem1332 := range fields1331 {
			if (i1333 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1332))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1338 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1338 != nil {
		p.write(*flat1338)
		return nil
	} else {
		fields1335 := msg
		p.write("[")
		p.indent()
		for i1337, elem1336 := range fields1335 {
			if (i1337 > 0) {
				p.newline()
			}
			p.pretty_type(elem1336)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		_dollar_dollar := msg
		fields1339 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1340 := fields1339
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1341 := unwrapped_fields1340[0].(*pb.RelationId)
		p.pretty_relation_id(field1341)
		p.newline()
		field1342 := unwrapped_fields1340[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1342)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		_dollar_dollar := msg
		_t1666 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1344 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1666}
		unwrapped_fields1345 := fields1344
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1346 := unwrapped_fields1345[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1346)
		p.newline()
		field1347 := unwrapped_fields1345[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1347)
		p.newline()
		field1348 := unwrapped_fields1345[2].([][]interface{})
		p.pretty_config_dict(field1348)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		fields1350 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1350) == 0) {
			p.newline()
			for i1352, elem1351 := range fields1350 {
				if (i1352 > 0) {
					p.newline()
				}
				p.pretty_type(elem1351)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1357 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		fields1354 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1354) == 0) {
			p.newline()
			for i1356, elem1355 := range fields1354 {
				if (i1356 > 0) {
					p.newline()
				}
				p.pretty_type(elem1355)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1364 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1364 != nil {
		p.write(*flat1364)
		return nil
	} else {
		_dollar_dollar := msg
		fields1358 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1359 := fields1358
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1360 := unwrapped_fields1359[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1360)
		p.newline()
		field1361 := unwrapped_fields1359[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1361)
		p.newline()
		field1362 := unwrapped_fields1359[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1362)
		p.newline()
		field1363 := unwrapped_fields1359[3].(string)
		p.pretty_csv_asof(field1363)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1667 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1667 = _dollar_dollar.GetPaths()
		}
		var _t1668 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1668 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1365 := []interface{}{_t1667, _t1668}
		unwrapped_fields1366 := fields1365
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1367 := unwrapped_fields1366[0].([]string)
		if field1367 != nil {
			p.newline()
			opt_val1368 := field1367
			p.pretty_csv_locator_paths(opt_val1368)
		}
		field1369 := unwrapped_fields1366[1].(*string)
		if field1369 != nil {
			p.newline()
			opt_val1370 := *field1369
			p.pretty_csv_locator_inline_data(opt_val1370)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1375 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1375 != nil {
		p.write(*flat1375)
		return nil
	} else {
		fields1372 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1372) == 0) {
			p.newline()
			for i1374, elem1373 := range fields1372 {
				if (i1374 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1373))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1377 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1377 != nil {
		p.write(*flat1377)
		return nil
	} else {
		fields1376 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1376))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1380 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1380 != nil {
		p.write(*flat1380)
		return nil
	} else {
		_dollar_dollar := msg
		_t1669 := p.deconstruct_csv_config(_dollar_dollar)
		fields1378 := _t1669
		unwrapped_fields1379 := fields1378
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1379)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1384 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1384 != nil {
		p.write(*flat1384)
		return nil
	} else {
		fields1381 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1381) == 0) {
			p.newline()
			for i1383, elem1382 := range fields1381 {
				if (i1383 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1382)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1393 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1393 != nil {
		p.write(*flat1393)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1670 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1670 = _dollar_dollar.GetTargetId()
		}
		fields1385 := []interface{}{_dollar_dollar.GetColumnPath(), _t1670, _dollar_dollar.GetTypes()}
		unwrapped_fields1386 := fields1385
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1387 := unwrapped_fields1386[0].([]string)
		p.pretty_gnf_column_path(field1387)
		field1388 := unwrapped_fields1386[1].(*pb.RelationId)
		if field1388 != nil {
			p.newline()
			opt_val1389 := field1388
			p.pretty_relation_id(opt_val1389)
		}
		p.newline()
		p.write("[")
		field1390 := unwrapped_fields1386[2].([]*pb.Type)
		for i1392, elem1391 := range field1390 {
			if (i1392 > 0) {
				p.newline()
			}
			p.pretty_type(elem1391)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1671 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1398 := _t1671
		if deconstruct_result1398 != nil {
			unwrapped1399 := *deconstruct_result1398
			p.write(p.formatStringValue(unwrapped1399))
		} else {
			_dollar_dollar := msg
			var _t1672 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1672 = _dollar_dollar
			}
			deconstruct_result1394 := _t1672
			if deconstruct_result1394 != nil {
				unwrapped1395 := deconstruct_result1394
				p.write("[")
				p.indent()
				for i1397, elem1396 := range unwrapped1395 {
					if (i1397 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1396))
				}
				p.dedent()
				p.write("]")
			} else {
				panic(ParseError{msg: "No matching rule for gnf_column_path"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1402 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1402 != nil {
		p.write(*flat1402)
		return nil
	} else {
		fields1401 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1401))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		_dollar_dollar := msg
		_t1673 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1403 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1673}
		unwrapped_fields1404 := fields1403
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1405 := unwrapped_fields1404[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1405)
		p.newline()
		field1406 := unwrapped_fields1404[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1406)
		p.newline()
		field1407 := unwrapped_fields1404[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1407)
		field1408 := unwrapped_fields1404[3].(*string)
		if field1408 != nil {
			p.newline()
			opt_val1409 := *field1408
			p.pretty_iceberg_to_snapshot(opt_val1409)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1418 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1418 != nil {
		p.write(*flat1418)
		return nil
	} else {
		_dollar_dollar := msg
		fields1411 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1412 := fields1411
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1413 := unwrapped_fields1412[0].(string)
		p.write(p.formatStringValue(field1413))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1414 := unwrapped_fields1412[1].([]string)
		if !(len(field1414) == 0) {
			p.newline()
			for i1416, elem1415 := range field1414 {
				if (i1416 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1415))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1417 := unwrapped_fields1412[2].(string)
		p.write(p.formatStringValue(field1417))
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1430 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1430 != nil {
		p.write(*flat1430)
		return nil
	} else {
		_dollar_dollar := msg
		_t1674 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1419 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1674, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1420 := fields1419
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1421 := unwrapped_fields1420[0].(string)
		p.write(p.formatStringValue(field1421))
		p.dedent()
		p.write(")")
		field1422 := unwrapped_fields1420[1].(*string)
		if field1422 != nil {
			p.newline()
			opt_val1423 := *field1422
			p.pretty_iceberg_catalog_config_scope(opt_val1423)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1424 := unwrapped_fields1420[2].([][]interface{})
		if !(len(field1424) == 0) {
			p.newline()
			for i1426, elem1425 := range field1424 {
				if (i1426 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1425)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1427 := unwrapped_fields1420[3].([][]interface{})
		if !(len(field1427) == 0) {
			p.newline()
			for i1429, elem1428 := range field1427 {
				if (i1429 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1428)
			}
		}
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		fields1431 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1431))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1437 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1437 != nil {
		p.write(*flat1437)
		return nil
	} else {
		_dollar_dollar := msg
		fields1433 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1434 := fields1433
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1435 := unwrapped_fields1434[0].(string)
		p.write(p.formatStringValue(field1435))
		p.newline()
		field1436 := unwrapped_fields1434[1].(string)
		p.write(p.formatStringValue(field1436))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1439 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1439 != nil {
		p.write(*flat1439)
		return nil
	} else {
		fields1438 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1438))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1442 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1442 != nil {
		p.write(*flat1442)
		return nil
	} else {
		_dollar_dollar := msg
		fields1440 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1441 := fields1440
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1441)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1447 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1447 != nil {
		p.write(*flat1447)
		return nil
	} else {
		_dollar_dollar := msg
		fields1443 := _dollar_dollar.GetRelations()
		unwrapped_fields1444 := fields1443
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1444) == 0) {
			p.newline()
			for i1446, elem1445 := range unwrapped_fields1444 {
				if (i1446 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1445)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1452 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1452 != nil {
		p.write(*flat1452)
		return nil
	} else {
		_dollar_dollar := msg
		fields1448 := _dollar_dollar.GetMappings()
		unwrapped_fields1449 := fields1448
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1449) == 0) {
			p.newline()
			for i1451, elem1450 := range unwrapped_fields1449 {
				if (i1451 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1450)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		_dollar_dollar := msg
		fields1453 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1454 := fields1453
		field1455 := unwrapped_fields1454[0].([]string)
		p.pretty_edb_path(field1455)
		p.write(" ")
		field1456 := unwrapped_fields1454[1].(*pb.RelationId)
		p.pretty_relation_id(field1456)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1461 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1461 != nil {
		p.write(*flat1461)
		return nil
	} else {
		fields1458 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1458) == 0) {
			p.newline()
			for i1460, elem1459 := range fields1458 {
				if (i1460 > 0) {
					p.newline()
				}
				p.pretty_read(elem1459)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1675 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1675 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1470 := _t1675
		if deconstruct_result1470 != nil {
			unwrapped1471 := deconstruct_result1470
			p.pretty_demand(unwrapped1471)
		} else {
			_dollar_dollar := msg
			var _t1676 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1676 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1468 := _t1676
			if deconstruct_result1468 != nil {
				unwrapped1469 := deconstruct_result1468
				p.pretty_output(unwrapped1469)
			} else {
				_dollar_dollar := msg
				var _t1677 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1677 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1466 := _t1677
				if deconstruct_result1466 != nil {
					unwrapped1467 := deconstruct_result1466
					p.pretty_what_if(unwrapped1467)
				} else {
					_dollar_dollar := msg
					var _t1678 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1678 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1464 := _t1678
					if deconstruct_result1464 != nil {
						unwrapped1465 := deconstruct_result1464
						p.pretty_abort(unwrapped1465)
					} else {
						_dollar_dollar := msg
						var _t1679 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1679 = _dollar_dollar.GetExport()
						}
						deconstruct_result1462 := _t1679
						if deconstruct_result1462 != nil {
							unwrapped1463 := deconstruct_result1462
							p.pretty_export(unwrapped1463)
						} else {
							panic(ParseError{msg: "No matching rule for read"})
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_demand(msg *pb.Demand) interface{} {
	flat1475 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1475 != nil {
		p.write(*flat1475)
		return nil
	} else {
		_dollar_dollar := msg
		fields1473 := _dollar_dollar.GetRelationId()
		unwrapped_fields1474 := fields1473
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1474)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		_dollar_dollar := msg
		fields1476 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1477 := fields1476
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1478 := unwrapped_fields1477[0].(string)
		p.pretty_name(field1478)
		p.newline()
		field1479 := unwrapped_fields1477[1].(*pb.RelationId)
		p.pretty_relation_id(field1479)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1485 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1485 != nil {
		p.write(*flat1485)
		return nil
	} else {
		_dollar_dollar := msg
		fields1481 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1482 := fields1481
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1483 := unwrapped_fields1482[0].(string)
		p.pretty_name(field1483)
		p.newline()
		field1484 := unwrapped_fields1482[1].(*pb.Epoch)
		p.pretty_epoch(field1484)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1491 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1491 != nil {
		p.write(*flat1491)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1680 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1680 = ptr(_dollar_dollar.GetName())
		}
		fields1486 := []interface{}{_t1680, _dollar_dollar.GetRelationId()}
		unwrapped_fields1487 := fields1486
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1488 := unwrapped_fields1487[0].(*string)
		if field1488 != nil {
			p.newline()
			opt_val1489 := *field1488
			p.pretty_name(opt_val1489)
		}
		p.newline()
		field1490 := unwrapped_fields1487[1].(*pb.RelationId)
		p.pretty_relation_id(field1490)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1496 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1496 != nil {
		p.write(*flat1496)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1681 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1681 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1494 := _t1681
		if deconstruct_result1494 != nil {
			unwrapped1495 := deconstruct_result1494
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1495)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1682 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1682 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1492 := _t1682
			if deconstruct_result1492 != nil {
				unwrapped1493 := deconstruct_result1492
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1493)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1507 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1507 != nil {
		p.write(*flat1507)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1683 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1683 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1502 := _t1683
		if deconstruct_result1502 != nil {
			unwrapped1503 := deconstruct_result1502
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1504 := unwrapped1503[0].(string)
			p.pretty_export_csv_path(field1504)
			p.newline()
			field1505 := unwrapped1503[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1505)
			p.newline()
			field1506 := unwrapped1503[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1506)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1684 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1685 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1684 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1685}
			}
			deconstruct_result1497 := _t1684
			if deconstruct_result1497 != nil {
				unwrapped1498 := deconstruct_result1497
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1499 := unwrapped1498[0].(string)
				p.pretty_export_csv_path(field1499)
				p.newline()
				field1500 := unwrapped1498[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1500)
				p.newline()
				field1501 := unwrapped1498[2].([][]interface{})
				p.pretty_config_dict(field1501)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_config"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1509 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1509 != nil {
		p.write(*flat1509)
		return nil
	} else {
		fields1508 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1508))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1516 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1516 != nil {
		p.write(*flat1516)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1686 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1686 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1512 := _t1686
		if deconstruct_result1512 != nil {
			unwrapped1513 := deconstruct_result1512
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1513) == 0) {
				p.newline()
				for i1515, elem1514 := range unwrapped1513 {
					if (i1515 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1514)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1687 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1687 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1510 := _t1687
			if deconstruct_result1510 != nil {
				unwrapped1511 := deconstruct_result1510
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1511)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_source"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		_dollar_dollar := msg
		fields1517 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1518 := fields1517
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1519 := unwrapped_fields1518[0].(string)
		p.write(p.formatStringValue(field1519))
		p.newline()
		field1520 := unwrapped_fields1518[1].(*pb.RelationId)
		p.pretty_relation_id(field1520)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1525 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1525 != nil {
		p.write(*flat1525)
		return nil
	} else {
		fields1522 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1522) == 0) {
			p.newline()
			for i1524, elem1523 := range fields1522 {
				if (i1524 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1523)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1536 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1536 != nil {
		p.write(*flat1536)
		return nil
	} else {
		_dollar_dollar := msg
		_t1688 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1526 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1688}
		unwrapped_fields1527 := fields1526
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1528 := unwrapped_fields1527[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1528)
		p.newline()
		field1529 := unwrapped_fields1527[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1529)
		p.newline()
		field1530 := unwrapped_fields1527[2].(*pb.ExportIcebergColumns)
		p.pretty_export_iceberg_columns(field1530)
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_properties")
		field1531 := unwrapped_fields1527[3].([][]interface{})
		if !(len(field1531) == 0) {
			p.newline()
			for i1533, elem1532 := range field1531 {
				if (i1533 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1532)
			}
		}
		p.dedent()
		p.write(")")
		field1534 := unwrapped_fields1527[4].([][]interface{})
		if field1534 != nil {
			p.newline()
			opt_val1535 := field1534
			p.pretty_config_dict(opt_val1535)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_columns(msg *pb.ExportIcebergColumns) interface{} {
	flat1543 := p.tryFlat(msg, func() { p.pretty_export_iceberg_columns(msg) })
	if flat1543 != nil {
		p.write(*flat1543)
		return nil
	} else {
		_dollar_dollar := msg
		fields1537 := []interface{}{_dollar_dollar.GetSourceTableDef(), _dollar_dollar.GetTargetColumns()}
		unwrapped_fields1538 := fields1537
		p.write("(")
		p.write("columns")
		p.indentSexp()
		p.newline()
		field1539 := unwrapped_fields1538[0].(*pb.RelationId)
		p.pretty_relation_id(field1539)
		p.newline()
		p.write("(")
		p.newline()
		p.write("target_columns")
		field1540 := unwrapped_fields1538[1].([]*pb.ExportIcebergColumn)
		if !(len(field1540) == 0) {
			p.newline()
			for i1542, elem1541 := range field1540 {
				if (i1542 > 0) {
					p.newline()
				}
				p.pretty_export_iceberg_column(elem1541)
			}
		}
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column(msg *pb.ExportIcebergColumn) interface{} {
	flat1549 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column(msg) })
	if flat1549 != nil {
		p.write(*flat1549)
		return nil
	} else {
		_dollar_dollar := msg
		fields1544 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType(), _dollar_dollar.GetNullable()}
		unwrapped_fields1545 := fields1544
		p.write("(")
		p.write("iceberg_column")
		p.indentSexp()
		p.newline()
		field1546 := unwrapped_fields1545[0].(string)
		p.write(p.formatStringValue(field1546))
		p.newline()
		field1547 := unwrapped_fields1545[1].(*pb.Type)
		p.pretty_type(field1547)
		p.newline()
		field1548 := unwrapped_fields1545[2].(bool)
		p.pretty_boolean_value(field1548)
		p.dedent()
		p.write(")")
	}
	return nil
}


// --- Auto-generated printers for uncovered proto types ---

func (p *PrettyPrinter) pretty_debug_info(msg *pb.DebugInfo) interface{} {
	p.write("(debug_info")
	p.indentSexp()
	for _idx, _rid := range msg.GetIds() {
		p.newline()
		p.write("(")
		_t1733 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1733)
		p.write(" ")
		p.write(p.formatStringValue(msg.GetOrigNames()[_idx]))
		p.write(")")
	}
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_be_tree_config(msg *pb.BeTreeConfig) interface{} {
	p.write("(be_tree_config")
	p.indentSexp()
	p.newline()
	p.write(":epsilon ")
	p.write(formatFloat64(msg.GetEpsilon()))
	p.newline()
	p.write(":max_pivots ")
	p.write(fmt.Sprintf("%d", msg.GetMaxPivots()))
	p.newline()
	p.write(":max_deltas ")
	p.write(fmt.Sprintf("%d", msg.GetMaxDeltas()))
	p.newline()
	p.write(":max_leaf ")
	p.write(fmt.Sprintf("%d", msg.GetMaxLeaf()))
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_be_tree_locator(msg *pb.BeTreeLocator) interface{} {
	p.write("(be_tree_locator")
	p.indentSexp()
	p.newline()
	p.write(":element_count ")
	p.write(fmt.Sprintf("%d", msg.GetElementCount()))
	p.newline()
	p.write(":tree_height ")
	p.write(fmt.Sprintf("%d", msg.GetTreeHeight()))
	p.newline()
	p.write(":location ")
	if hasProtoField(msg, "root_pageid") {
		p.write("(:root_pageid ")
		p.pprintDispatch(msg.GetRootPageid())
		p.write(")")
	} else {
		if hasProtoField(msg, "inline_data") {
			p.write("(:inline_data ")
			p.write(fmt.Sprintf("0x%x", msg.GetInlineData()))
			p.write(")")
		} else {
			p.write("nothing")
		}
	}
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_decimal_value(msg *pb.DecimalValue) interface{} {
	p.write(p.formatDecimal(msg))
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency(msg *pb.FunctionalDependency) interface{} {
	p.write("(functional_dependency")
	p.indentSexp()
	p.newline()
	p.write(":guard ")
	p.pprintDispatch(msg.GetGuard())
	p.newline()
	p.write(":keys ")
	p.write("(")
	for _idx, _elem := range msg.GetKeys() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.newline()
	p.write(":values ")
	p.write("(")
	for _idx, _elem := range msg.GetValues() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_int128_value(msg *pb.Int128Value) interface{} {
	p.write(p.formatInt128(msg))
	return nil
}

func (p *PrettyPrinter) pretty_missing_value(msg *pb.MissingValue) interface{} {
	p.write("missing")
	return nil
}

func (p *PrettyPrinter) pretty_u_int128_value(msg *pb.UInt128Value) interface{} {
	p.write(p.formatUint128(msg))
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg *pb.ExportCSVColumns) interface{} {
	p.write("(export_csv_columns")
	p.indentSexp()
	p.newline()
	p.write(":columns ")
	p.write("(")
	for _idx, _elem := range msg.GetColumns() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_ivm_config(msg *pb.IVMConfig) interface{} {
	p.write("(ivm_config")
	p.indentSexp()
	p.newline()
	p.write(":level ")
	p.pprintDispatch(msg.GetLevel())
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_maintenance_level(x pb.MaintenanceLevel) interface{} {
	if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED {
		p.write("unspecified")
	} else {
		if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
			p.write("off")
		} else {
			if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
				p.write("auto")
			} else {
				if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
					p.write("all")
				}
			}
		}
	}
	return nil
}

// --- Dispatch function ---
func (p *PrettyPrinter) pprintDispatch(msg interface{}) {
	switch m := msg.(type) {
	case *pb.Transaction:
		p.pretty_transaction(m)
	case *pb.Configure:
		p.pretty_configure(m)
	case [][]interface{}:
		p.pretty_config_dict(m)
	case []interface{}:
		p.pretty_config_key_value(m)
	case *pb.Value:
		p.pretty_value(m)
	case *pb.DateValue:
		p.pretty_raw_date(m)
	case *pb.DateTimeValue:
		p.pretty_raw_datetime(m)
	case bool:
		p.pretty_boolean_value(m)
	case *pb.Sync:
		p.pretty_sync(m)
	case *pb.FragmentId:
		p.pretty_fragment_id(m)
	case *pb.Epoch:
		p.pretty_epoch(m)
	case []*pb.Write:
		p.pretty_epoch_writes(m)
	case *pb.Write:
		p.pretty_write(m)
	case *pb.Define:
		p.pretty_define(m)
	case *pb.Fragment:
		p.pretty_fragment(m)
	case *pb.Declaration:
		p.pretty_declaration(m)
	case *pb.Def:
		p.pretty_def(m)
	case *pb.RelationId:
		p.pretty_relation_id(m)
	case *pb.Abstraction:
		p.pretty_abstraction(m)
	case *pb.Binding:
		p.pretty_binding(m)
	case *pb.Type:
		p.pretty_type(m)
	case *pb.UnspecifiedType:
		p.pretty_unspecified_type(m)
	case *pb.StringType:
		p.pretty_string_type(m)
	case *pb.IntType:
		p.pretty_int_type(m)
	case *pb.FloatType:
		p.pretty_float_type(m)
	case *pb.UInt128Type:
		p.pretty_uint128_type(m)
	case *pb.Int128Type:
		p.pretty_int128_type(m)
	case *pb.DateType:
		p.pretty_date_type(m)
	case *pb.DateTimeType:
		p.pretty_datetime_type(m)
	case *pb.MissingType:
		p.pretty_missing_type(m)
	case *pb.DecimalType:
		p.pretty_decimal_type(m)
	case *pb.BooleanType:
		p.pretty_boolean_type(m)
	case *pb.Int32Type:
		p.pretty_int32_type(m)
	case *pb.Float32Type:
		p.pretty_float32_type(m)
	case *pb.UInt32Type:
		p.pretty_uint32_type(m)
	case []*pb.Binding:
		p.pretty_value_bindings(m)
	case *pb.Formula:
		p.pretty_formula(m)
	case *pb.Conjunction:
		p.pretty_conjunction(m)
	case *pb.Disjunction:
		p.pretty_disjunction(m)
	case *pb.Exists:
		p.pretty_exists(m)
	case *pb.Reduce:
		p.pretty_reduce(m)
	case []*pb.Term:
		p.pretty_terms(m)
	case *pb.Term:
		p.pretty_term(m)
	case *pb.Var:
		p.pretty_var(m)
	case *pb.Not:
		p.pretty_not(m)
	case *pb.FFI:
		p.pretty_ffi(m)
	case string:
		p.pretty_name(m)
	case []*pb.Abstraction:
		p.pretty_ffi_args(m)
	case *pb.Atom:
		p.pretty_atom(m)
	case *pb.Pragma:
		p.pretty_pragma(m)
	case *pb.Primitive:
		p.pretty_primitive(m)
	case *pb.RelTerm:
		p.pretty_rel_term(m)
	case *pb.RelAtom:
		p.pretty_rel_atom(m)
	case *pb.Cast:
		p.pretty_cast(m)
	case []*pb.Attribute:
		p.pretty_attrs(m)
	case *pb.Attribute:
		p.pretty_attribute(m)
	case *pb.Algorithm:
		p.pretty_algorithm(m)
	case *pb.Script:
		p.pretty_script(m)
	case *pb.Construct:
		p.pretty_construct(m)
	case *pb.Loop:
		p.pretty_loop(m)
	case []*pb.Instruction:
		p.pretty_init(m)
	case *pb.Instruction:
		p.pretty_instruction(m)
	case *pb.Assign:
		p.pretty_assign(m)
	case *pb.Upsert:
		p.pretty_upsert(m)
	case *pb.Break:
		p.pretty_break(m)
	case *pb.MonoidDef:
		p.pretty_monoid_def(m)
	case *pb.Monoid:
		p.pretty_monoid(m)
	case *pb.OrMonoid:
		p.pretty_or_monoid(m)
	case *pb.MinMonoid:
		p.pretty_min_monoid(m)
	case *pb.MaxMonoid:
		p.pretty_max_monoid(m)
	case *pb.SumMonoid:
		p.pretty_sum_monoid(m)
	case *pb.MonusDef:
		p.pretty_monus_def(m)
	case *pb.Constraint:
		p.pretty_constraint(m)
	case []*pb.Var:
		p.pretty_functional_dependency_keys(m)
	case *pb.Data:
		p.pretty_data(m)
	case *pb.EDB:
		p.pretty_edb(m)
	case []string:
		p.pretty_edb_path(m)
	case []*pb.Type:
		p.pretty_edb_types(m)
	case *pb.BeTreeRelation:
		p.pretty_betree_relation(m)
	case *pb.BeTreeInfo:
		p.pretty_betree_info(m)
	case *pb.CSVData:
		p.pretty_csv_data(m)
	case *pb.CSVLocator:
		p.pretty_csvlocator(m)
	case *pb.CSVConfig:
		p.pretty_csv_config(m)
	case []*pb.GNFColumn:
		p.pretty_gnf_columns(m)
	case *pb.GNFColumn:
		p.pretty_gnf_column(m)
	case *pb.IcebergData:
		p.pretty_iceberg_data(m)
	case *pb.IcebergLocator:
		p.pretty_iceberg_locator(m)
	case *pb.IcebergCatalogConfig:
		p.pretty_iceberg_catalog_config(m)
	case *pb.Undefine:
		p.pretty_undefine(m)
	case *pb.Context:
		p.pretty_context(m)
	case *pb.Snapshot:
		p.pretty_snapshot(m)
	case *pb.SnapshotMapping:
		p.pretty_snapshot_mapping(m)
	case []*pb.Read:
		p.pretty_epoch_reads(m)
	case *pb.Read:
		p.pretty_read(m)
	case *pb.Demand:
		p.pretty_demand(m)
	case *pb.Output:
		p.pretty_output(m)
	case *pb.WhatIf:
		p.pretty_what_if(m)
	case *pb.Abort:
		p.pretty_abort(m)
	case *pb.Export:
		p.pretty_export(m)
	case *pb.ExportCSVConfig:
		p.pretty_export_csv_config(m)
	case *pb.ExportCSVSource:
		p.pretty_export_csv_source(m)
	case *pb.ExportCSVColumn:
		p.pretty_export_csv_column(m)
	case []*pb.ExportCSVColumn:
		p.pretty_export_csv_columns_list(m)
	case *pb.ExportIcebergConfig:
		p.pretty_export_iceberg_config(m)
	case *pb.ExportIcebergColumns:
		p.pretty_export_iceberg_columns(m)
	case *pb.ExportIcebergColumn:
		p.pretty_export_iceberg_column(m)
	case *pb.DebugInfo:
		p.pretty_debug_info(m)
	case *pb.BeTreeConfig:
		p.pretty_be_tree_config(m)
	case *pb.BeTreeLocator:
		p.pretty_be_tree_locator(m)
	case *pb.DecimalValue:
		p.pretty_decimal_value(m)
	case *pb.FunctionalDependency:
		p.pretty_functional_dependency(m)
	case *pb.Int128Value:
		p.pretty_int128_value(m)
	case *pb.MissingValue:
		p.pretty_missing_value(m)
	case *pb.UInt128Value:
		p.pretty_u_int128_value(m)
	case *pb.ExportCSVColumns:
		p.pretty_export_csv_columns(m)
	case *pb.IVMConfig:
		p.pretty_ivm_config(m)
	case pb.MaintenanceLevel:
		p.pretty_maintenance_level(m)
	default:
		panic(fmt.Sprintf("no pretty printer for %T", msg))
	}
}

// writeDebugInfo writes accumulated debug info as comments at the end of the output.
func (p *PrettyPrinter) writeDebugInfo() {
	if len(p.debugInfo) == 0 {
		return
	}
	// Collect and sort entries by name for deterministic output.
	type debugEntry struct {
		key  [2]uint64
		name string
	}
	entries := make([]debugEntry, 0, len(p.debugInfo))
	for key, name := range p.debugInfo {
		entries = append(entries, debugEntry{key, name})
	}
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].name < entries[j].name
	})
	p.w.WriteString("\n;; Debug information\n")
	p.w.WriteString(";; -----------------------\n")
	p.w.WriteString(";; Original names\n")
	for _, e := range entries {
		value := new(big.Int).SetUint64(e.key[1])
		value.Lsh(value, 64)
		value.Or(value, new(big.Int).SetUint64(e.key[0]))
		p.w.WriteString(fmt.Sprintf(";; \t ID `0x%x` -> `%s`\n", value, e.name))
	}
}


// ProgramToStr pretty-prints a Transaction protobuf message to a string.
func ProgramToStr(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:                       &buf,
		indentStack:             []int{0},
		column:                  0,
		atLineStart:             true,
		separator:               "\n",
		maxWidth:                maxWidth,
		computing:               make(map[uintptr]bool),
		memo:                    make(map[uintptr]string),
		debugInfo:               make(map[[2]uint64]string),
		printSymbolicRelationIds: true,
	}
	p.pretty_transaction(msg)
	p.newline()
	return p.getOutput()
}

// ProgramToStrDebug pretty-prints with raw relation IDs and debug info appended as comments.
func ProgramToStrDebug(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:                       &buf,
		indentStack:             []int{0},
		column:                  0,
		atLineStart:             true,
		separator:               "\n",
		maxWidth:                maxWidth,
		computing:               make(map[uintptr]bool),
		memo:                    make(map[uintptr]string),
		debugInfo:               make(map[[2]uint64]string),
		printSymbolicRelationIds: false,
	}
	p.pretty_transaction(msg)
	p.newline()
	p.writeDebugInfo()
	return p.getOutput()
}
