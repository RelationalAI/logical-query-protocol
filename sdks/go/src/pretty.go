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
	_t1705 := &pb.Value{}
	_t1705.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1705
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1706 := &pb.Value{}
	_t1706.Value = &pb.Value_IntValue{IntValue: v}
	return _t1706
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1707 := &pb.Value{}
	_t1707.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1707
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1708 := &pb.Value{}
	_t1708.Value = &pb.Value_StringValue{StringValue: v}
	return _t1708
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1709 := &pb.Value{}
	_t1709.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1709
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1710 := &pb.Value{}
	_t1710.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1710
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1711 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1711})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1712 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1712})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1713 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1713})
			}
		}
	}
	_t1714 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1714})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1715 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1715})
	_t1716 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1716})
	if msg.GetNewLine() != "" {
		_t1717 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1717})
	}
	_t1718 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1718})
	_t1719 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1719})
	_t1720 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1720})
	if msg.GetComment() != "" {
		_t1721 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1721})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1722 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1722})
	}
	_t1723 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1723})
	_t1724 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1724})
	_t1725 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1725})
	if msg.GetPartitionSizeMb() != 0 {
		_t1726 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1726})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1727 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1727})
	_t1728 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1728})
	_t1729 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1729})
	_t1730 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1730})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1731 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1731})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1732 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1732})
		}
	}
	_t1733 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1733})
	_t1734 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1734})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1735 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1735})
	}
	if msg.Compression != nil {
		_t1736 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1736})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1737 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1737})
	}
	if msg.SyntaxMissingString != nil {
		_t1738 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1738})
	}
	if msg.SyntaxDelim != nil {
		_t1739 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1739})
	}
	if msg.SyntaxQuotechar != nil {
		_t1740 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1740})
	}
	if msg.SyntaxEscapechar != nil {
		_t1741 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1741})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1742 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1742
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1743 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1743
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1744 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1744})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1745 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1745})
	}
	if msg.GetCompression() != "" {
		_t1746 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1746})
	}
	var _t1747 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1747
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1748 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1748
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
	flat791 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat791 != nil {
		p.write(*flat791)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1564 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1564 = _dollar_dollar.GetConfigure()
		}
		var _t1565 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1565 = _dollar_dollar.GetSync()
		}
		fields782 := []interface{}{_t1564, _t1565, _dollar_dollar.GetEpochs()}
		unwrapped_fields783 := fields782
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field784 := unwrapped_fields783[0].(*pb.Configure)
		if field784 != nil {
			p.newline()
			opt_val785 := field784
			p.pretty_configure(opt_val785)
		}
		field786 := unwrapped_fields783[1].(*pb.Sync)
		if field786 != nil {
			p.newline()
			opt_val787 := field786
			p.pretty_sync(opt_val787)
		}
		field788 := unwrapped_fields783[2].([]*pb.Epoch)
		if !(len(field788) == 0) {
			p.newline()
			for i790, elem789 := range field788 {
				if (i790 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem789)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat794 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat794 != nil {
		p.write(*flat794)
		return nil
	} else {
		_dollar_dollar := msg
		_t1566 := p.deconstruct_configure(_dollar_dollar)
		fields792 := _t1566
		unwrapped_fields793 := fields792
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields793)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat798 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat798 != nil {
		p.write(*flat798)
		return nil
	} else {
		fields795 := msg
		p.write("{")
		p.indent()
		if !(len(fields795) == 0) {
			p.newline()
			for i797, elem796 := range fields795 {
				if (i797 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem796)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat803 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat803 != nil {
		p.write(*flat803)
		return nil
	} else {
		_dollar_dollar := msg
		fields799 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields800 := fields799
		p.write(":")
		field801 := unwrapped_fields800[0].(string)
		p.write(field801)
		p.write(" ")
		field802 := unwrapped_fields800[1].(*pb.Value)
		p.pretty_raw_value(field802)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat829 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat829 != nil {
		p.write(*flat829)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1567 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1567 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result827 := _t1567
		if deconstruct_result827 != nil {
			unwrapped828 := deconstruct_result827
			p.pretty_raw_date(unwrapped828)
		} else {
			_dollar_dollar := msg
			var _t1568 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1568 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result825 := _t1568
			if deconstruct_result825 != nil {
				unwrapped826 := deconstruct_result825
				p.pretty_raw_datetime(unwrapped826)
			} else {
				_dollar_dollar := msg
				var _t1569 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1569 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result823 := _t1569
				if deconstruct_result823 != nil {
					unwrapped824 := *deconstruct_result823
					p.write(p.formatStringValue(unwrapped824))
				} else {
					_dollar_dollar := msg
					var _t1570 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1570 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result821 := _t1570
					if deconstruct_result821 != nil {
						unwrapped822 := *deconstruct_result821
						p.write(fmt.Sprintf("%di32", unwrapped822))
					} else {
						_dollar_dollar := msg
						var _t1571 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1571 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result819 := _t1571
						if deconstruct_result819 != nil {
							unwrapped820 := *deconstruct_result819
							p.write(fmt.Sprintf("%d", unwrapped820))
						} else {
							_dollar_dollar := msg
							var _t1572 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1572 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result817 := _t1572
							if deconstruct_result817 != nil {
								unwrapped818 := *deconstruct_result817
								p.write(formatFloat32(unwrapped818))
							} else {
								_dollar_dollar := msg
								var _t1573 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1573 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result815 := _t1573
								if deconstruct_result815 != nil {
									unwrapped816 := *deconstruct_result815
									p.write(formatFloat64(unwrapped816))
								} else {
									_dollar_dollar := msg
									var _t1574 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1574 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result813 := _t1574
									if deconstruct_result813 != nil {
										unwrapped814 := *deconstruct_result813
										p.write(fmt.Sprintf("%du32", unwrapped814))
									} else {
										_dollar_dollar := msg
										var _t1575 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1575 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result811 := _t1575
										if deconstruct_result811 != nil {
											unwrapped812 := deconstruct_result811
											p.write(p.formatUint128(unwrapped812))
										} else {
											_dollar_dollar := msg
											var _t1576 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1576 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result809 := _t1576
											if deconstruct_result809 != nil {
												unwrapped810 := deconstruct_result809
												p.write(p.formatInt128(unwrapped810))
											} else {
												_dollar_dollar := msg
												var _t1577 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1577 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result807 := _t1577
												if deconstruct_result807 != nil {
													unwrapped808 := deconstruct_result807
													p.write(p.formatDecimal(unwrapped808))
												} else {
													_dollar_dollar := msg
													var _t1578 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1578 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result805 := _t1578
													if deconstruct_result805 != nil {
														unwrapped806 := *deconstruct_result805
														p.pretty_boolean_value(unwrapped806)
													} else {
														fields804 := msg
														_ = fields804
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
	flat835 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat835 != nil {
		p.write(*flat835)
		return nil
	} else {
		_dollar_dollar := msg
		fields830 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields831 := fields830
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field832 := unwrapped_fields831[0].(int64)
		p.write(fmt.Sprintf("%d", field832))
		p.newline()
		field833 := unwrapped_fields831[1].(int64)
		p.write(fmt.Sprintf("%d", field833))
		p.newline()
		field834 := unwrapped_fields831[2].(int64)
		p.write(fmt.Sprintf("%d", field834))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat846 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat846 != nil {
		p.write(*flat846)
		return nil
	} else {
		_dollar_dollar := msg
		fields836 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields837 := fields836
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field838 := unwrapped_fields837[0].(int64)
		p.write(fmt.Sprintf("%d", field838))
		p.newline()
		field839 := unwrapped_fields837[1].(int64)
		p.write(fmt.Sprintf("%d", field839))
		p.newline()
		field840 := unwrapped_fields837[2].(int64)
		p.write(fmt.Sprintf("%d", field840))
		p.newline()
		field841 := unwrapped_fields837[3].(int64)
		p.write(fmt.Sprintf("%d", field841))
		p.newline()
		field842 := unwrapped_fields837[4].(int64)
		p.write(fmt.Sprintf("%d", field842))
		p.newline()
		field843 := unwrapped_fields837[5].(int64)
		p.write(fmt.Sprintf("%d", field843))
		field844 := unwrapped_fields837[6].(*int64)
		if field844 != nil {
			p.newline()
			opt_val845 := *field844
			p.write(fmt.Sprintf("%d", opt_val845))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1579 []interface{}
	if _dollar_dollar {
		_t1579 = []interface{}{}
	}
	deconstruct_result849 := _t1579
	if deconstruct_result849 != nil {
		unwrapped850 := deconstruct_result849
		_ = unwrapped850
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1580 []interface{}
		if !(_dollar_dollar) {
			_t1580 = []interface{}{}
		}
		deconstruct_result847 := _t1580
		if deconstruct_result847 != nil {
			unwrapped848 := deconstruct_result847
			_ = unwrapped848
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat855 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat855 != nil {
		p.write(*flat855)
		return nil
	} else {
		_dollar_dollar := msg
		fields851 := _dollar_dollar.GetFragments()
		unwrapped_fields852 := fields851
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields852) == 0) {
			p.newline()
			for i854, elem853 := range unwrapped_fields852 {
				if (i854 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem853)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		_dollar_dollar := msg
		fields856 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields857 := fields856
		p.write(":")
		p.write(unwrapped_fields857)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat865 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat865 != nil {
		p.write(*flat865)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1581 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1581 = _dollar_dollar.GetWrites()
		}
		var _t1582 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1582 = _dollar_dollar.GetReads()
		}
		fields859 := []interface{}{_t1581, _t1582}
		unwrapped_fields860 := fields859
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field861 := unwrapped_fields860[0].([]*pb.Write)
		if field861 != nil {
			p.newline()
			opt_val862 := field861
			p.pretty_epoch_writes(opt_val862)
		}
		field863 := unwrapped_fields860[1].([]*pb.Read)
		if field863 != nil {
			p.newline()
			opt_val864 := field863
			p.pretty_epoch_reads(opt_val864)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat869 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat869 != nil {
		p.write(*flat869)
		return nil
	} else {
		fields866 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields866) == 0) {
			p.newline()
			for i868, elem867 := range fields866 {
				if (i868 > 0) {
					p.newline()
				}
				p.pretty_write(elem867)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat878 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat878 != nil {
		p.write(*flat878)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1583 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1583 = _dollar_dollar.GetDefine()
		}
		deconstruct_result876 := _t1583
		if deconstruct_result876 != nil {
			unwrapped877 := deconstruct_result876
			p.pretty_define(unwrapped877)
		} else {
			_dollar_dollar := msg
			var _t1584 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1584 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result874 := _t1584
			if deconstruct_result874 != nil {
				unwrapped875 := deconstruct_result874
				p.pretty_undefine(unwrapped875)
			} else {
				_dollar_dollar := msg
				var _t1585 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1585 = _dollar_dollar.GetContext()
				}
				deconstruct_result872 := _t1585
				if deconstruct_result872 != nil {
					unwrapped873 := deconstruct_result872
					p.pretty_context(unwrapped873)
				} else {
					_dollar_dollar := msg
					var _t1586 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1586 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result870 := _t1586
					if deconstruct_result870 != nil {
						unwrapped871 := deconstruct_result870
						p.pretty_snapshot(unwrapped871)
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
	flat881 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat881 != nil {
		p.write(*flat881)
		return nil
	} else {
		_dollar_dollar := msg
		fields879 := _dollar_dollar.GetFragment()
		unwrapped_fields880 := fields879
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields880)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat888 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat888 != nil {
		p.write(*flat888)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields882 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields883 := fields882
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field884 := unwrapped_fields883[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field884)
		field885 := unwrapped_fields883[1].([]*pb.Declaration)
		if !(len(field885) == 0) {
			p.newline()
			for i887, elem886 := range field885 {
				if (i887 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem886)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat890 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat890 != nil {
		p.write(*flat890)
		return nil
	} else {
		fields889 := msg
		p.pretty_fragment_id(fields889)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat899 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1587 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1587 = _dollar_dollar.GetDef()
		}
		deconstruct_result897 := _t1587
		if deconstruct_result897 != nil {
			unwrapped898 := deconstruct_result897
			p.pretty_def(unwrapped898)
		} else {
			_dollar_dollar := msg
			var _t1588 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1588 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result895 := _t1588
			if deconstruct_result895 != nil {
				unwrapped896 := deconstruct_result895
				p.pretty_algorithm(unwrapped896)
			} else {
				_dollar_dollar := msg
				var _t1589 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1589 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result893 := _t1589
				if deconstruct_result893 != nil {
					unwrapped894 := deconstruct_result893
					p.pretty_constraint(unwrapped894)
				} else {
					_dollar_dollar := msg
					var _t1590 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1590 = _dollar_dollar.GetData()
					}
					deconstruct_result891 := _t1590
					if deconstruct_result891 != nil {
						unwrapped892 := deconstruct_result891
						p.pretty_data(unwrapped892)
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
	flat906 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1591 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1591 = _dollar_dollar.GetAttrs()
		}
		fields900 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1591}
		unwrapped_fields901 := fields900
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field902 := unwrapped_fields901[0].(*pb.RelationId)
		p.pretty_relation_id(field902)
		p.newline()
		field903 := unwrapped_fields901[1].(*pb.Abstraction)
		p.pretty_abstraction(field903)
		field904 := unwrapped_fields901[2].([]*pb.Attribute)
		if field904 != nil {
			p.newline()
			opt_val905 := field904
			p.pretty_attrs(opt_val905)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat911 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat911 != nil {
		p.write(*flat911)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1592 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1593 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1592 = ptr(_t1593)
		}
		deconstruct_result909 := _t1592
		if deconstruct_result909 != nil {
			unwrapped910 := *deconstruct_result909
			p.write(":")
			p.write(unwrapped910)
		} else {
			_dollar_dollar := msg
			_t1594 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result907 := _t1594
			if deconstruct_result907 != nil {
				unwrapped908 := deconstruct_result907
				p.write(p.formatUint128(unwrapped908))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat916 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat916 != nil {
		p.write(*flat916)
		return nil
	} else {
		_dollar_dollar := msg
		_t1595 := p.deconstruct_bindings(_dollar_dollar)
		fields912 := []interface{}{_t1595, _dollar_dollar.GetValue()}
		unwrapped_fields913 := fields912
		p.write("(")
		p.indent()
		field914 := unwrapped_fields913[0].([]interface{})
		p.pretty_bindings(field914)
		p.newline()
		field915 := unwrapped_fields913[1].(*pb.Formula)
		p.pretty_formula(field915)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat924 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat924 != nil {
		p.write(*flat924)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1596 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1596 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields917 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1596}
		unwrapped_fields918 := fields917
		p.write("[")
		p.indent()
		field919 := unwrapped_fields918[0].([]*pb.Binding)
		for i921, elem920 := range field919 {
			if (i921 > 0) {
				p.newline()
			}
			p.pretty_binding(elem920)
		}
		field922 := unwrapped_fields918[1].([]*pb.Binding)
		if field922 != nil {
			p.newline()
			opt_val923 := field922
			p.pretty_value_bindings(opt_val923)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat929 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat929 != nil {
		p.write(*flat929)
		return nil
	} else {
		_dollar_dollar := msg
		fields925 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields926 := fields925
		field927 := unwrapped_fields926[0].(string)
		p.write(field927)
		p.write("::")
		field928 := unwrapped_fields926[1].(*pb.Type)
		p.pretty_type(field928)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1597 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1597 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result956 := _t1597
		if deconstruct_result956 != nil {
			unwrapped957 := deconstruct_result956
			p.pretty_unspecified_type(unwrapped957)
		} else {
			_dollar_dollar := msg
			var _t1598 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1598 = _dollar_dollar.GetStringType()
			}
			deconstruct_result954 := _t1598
			if deconstruct_result954 != nil {
				unwrapped955 := deconstruct_result954
				p.pretty_string_type(unwrapped955)
			} else {
				_dollar_dollar := msg
				var _t1599 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1599 = _dollar_dollar.GetIntType()
				}
				deconstruct_result952 := _t1599
				if deconstruct_result952 != nil {
					unwrapped953 := deconstruct_result952
					p.pretty_int_type(unwrapped953)
				} else {
					_dollar_dollar := msg
					var _t1600 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1600 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result950 := _t1600
					if deconstruct_result950 != nil {
						unwrapped951 := deconstruct_result950
						p.pretty_float_type(unwrapped951)
					} else {
						_dollar_dollar := msg
						var _t1601 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1601 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result948 := _t1601
						if deconstruct_result948 != nil {
							unwrapped949 := deconstruct_result948
							p.pretty_uint128_type(unwrapped949)
						} else {
							_dollar_dollar := msg
							var _t1602 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1602 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result946 := _t1602
							if deconstruct_result946 != nil {
								unwrapped947 := deconstruct_result946
								p.pretty_int128_type(unwrapped947)
							} else {
								_dollar_dollar := msg
								var _t1603 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1603 = _dollar_dollar.GetDateType()
								}
								deconstruct_result944 := _t1603
								if deconstruct_result944 != nil {
									unwrapped945 := deconstruct_result944
									p.pretty_date_type(unwrapped945)
								} else {
									_dollar_dollar := msg
									var _t1604 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1604 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result942 := _t1604
									if deconstruct_result942 != nil {
										unwrapped943 := deconstruct_result942
										p.pretty_datetime_type(unwrapped943)
									} else {
										_dollar_dollar := msg
										var _t1605 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1605 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result940 := _t1605
										if deconstruct_result940 != nil {
											unwrapped941 := deconstruct_result940
											p.pretty_missing_type(unwrapped941)
										} else {
											_dollar_dollar := msg
											var _t1606 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1606 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result938 := _t1606
											if deconstruct_result938 != nil {
												unwrapped939 := deconstruct_result938
												p.pretty_decimal_type(unwrapped939)
											} else {
												_dollar_dollar := msg
												var _t1607 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1607 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result936 := _t1607
												if deconstruct_result936 != nil {
													unwrapped937 := deconstruct_result936
													p.pretty_boolean_type(unwrapped937)
												} else {
													_dollar_dollar := msg
													var _t1608 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1608 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result934 := _t1608
													if deconstruct_result934 != nil {
														unwrapped935 := deconstruct_result934
														p.pretty_int32_type(unwrapped935)
													} else {
														_dollar_dollar := msg
														var _t1609 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1609 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result932 := _t1609
														if deconstruct_result932 != nil {
															unwrapped933 := deconstruct_result932
															p.pretty_float32_type(unwrapped933)
														} else {
															_dollar_dollar := msg
															var _t1610 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1610 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result930 := _t1610
															if deconstruct_result930 != nil {
																unwrapped931 := deconstruct_result930
																p.pretty_uint32_type(unwrapped931)
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
	fields959 := msg
	_ = fields959
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields960 := msg
	_ = fields960
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields961 := msg
	_ = fields961
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields962 := msg
	_ = fields962
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields963 := msg
	_ = fields963
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields964 := msg
	_ = fields964
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields965 := msg
	_ = fields965
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields966 := msg
	_ = fields966
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields967 := msg
	_ = fields967
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat972 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat972 != nil {
		p.write(*flat972)
		return nil
	} else {
		_dollar_dollar := msg
		fields968 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields969 := fields968
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field970 := unwrapped_fields969[0].(int64)
		p.write(fmt.Sprintf("%d", field970))
		p.newline()
		field971 := unwrapped_fields969[1].(int64)
		p.write(fmt.Sprintf("%d", field971))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields973 := msg
	_ = fields973
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields974 := msg
	_ = fields974
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields975 := msg
	_ = fields975
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields976 := msg
	_ = fields976
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat980 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat980 != nil {
		p.write(*flat980)
		return nil
	} else {
		fields977 := msg
		p.write("|")
		if !(len(fields977) == 0) {
			p.write(" ")
			for i979, elem978 := range fields977 {
				if (i979 > 0) {
					p.newline()
				}
				p.pretty_binding(elem978)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1611 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1611 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1005 := _t1611
		if deconstruct_result1005 != nil {
			unwrapped1006 := deconstruct_result1005
			p.pretty_true(unwrapped1006)
		} else {
			_dollar_dollar := msg
			var _t1612 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1612 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1003 := _t1612
			if deconstruct_result1003 != nil {
				unwrapped1004 := deconstruct_result1003
				p.pretty_false(unwrapped1004)
			} else {
				_dollar_dollar := msg
				var _t1613 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1613 = _dollar_dollar.GetExists()
				}
				deconstruct_result1001 := _t1613
				if deconstruct_result1001 != nil {
					unwrapped1002 := deconstruct_result1001
					p.pretty_exists(unwrapped1002)
				} else {
					_dollar_dollar := msg
					var _t1614 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1614 = _dollar_dollar.GetReduce()
					}
					deconstruct_result999 := _t1614
					if deconstruct_result999 != nil {
						unwrapped1000 := deconstruct_result999
						p.pretty_reduce(unwrapped1000)
					} else {
						_dollar_dollar := msg
						var _t1615 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1615 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result997 := _t1615
						if deconstruct_result997 != nil {
							unwrapped998 := deconstruct_result997
							p.pretty_conjunction(unwrapped998)
						} else {
							_dollar_dollar := msg
							var _t1616 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1616 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result995 := _t1616
							if deconstruct_result995 != nil {
								unwrapped996 := deconstruct_result995
								p.pretty_disjunction(unwrapped996)
							} else {
								_dollar_dollar := msg
								var _t1617 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1617 = _dollar_dollar.GetNot()
								}
								deconstruct_result993 := _t1617
								if deconstruct_result993 != nil {
									unwrapped994 := deconstruct_result993
									p.pretty_not(unwrapped994)
								} else {
									_dollar_dollar := msg
									var _t1618 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1618 = _dollar_dollar.GetFfi()
									}
									deconstruct_result991 := _t1618
									if deconstruct_result991 != nil {
										unwrapped992 := deconstruct_result991
										p.pretty_ffi(unwrapped992)
									} else {
										_dollar_dollar := msg
										var _t1619 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1619 = _dollar_dollar.GetAtom()
										}
										deconstruct_result989 := _t1619
										if deconstruct_result989 != nil {
											unwrapped990 := deconstruct_result989
											p.pretty_atom(unwrapped990)
										} else {
											_dollar_dollar := msg
											var _t1620 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1620 = _dollar_dollar.GetPragma()
											}
											deconstruct_result987 := _t1620
											if deconstruct_result987 != nil {
												unwrapped988 := deconstruct_result987
												p.pretty_pragma(unwrapped988)
											} else {
												_dollar_dollar := msg
												var _t1621 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1621 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result985 := _t1621
												if deconstruct_result985 != nil {
													unwrapped986 := deconstruct_result985
													p.pretty_primitive(unwrapped986)
												} else {
													_dollar_dollar := msg
													var _t1622 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1622 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result983 := _t1622
													if deconstruct_result983 != nil {
														unwrapped984 := deconstruct_result983
														p.pretty_rel_atom(unwrapped984)
													} else {
														_dollar_dollar := msg
														var _t1623 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1623 = _dollar_dollar.GetCast()
														}
														deconstruct_result981 := _t1623
														if deconstruct_result981 != nil {
															unwrapped982 := deconstruct_result981
															p.pretty_cast(unwrapped982)
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
	fields1008 := msg
	_ = fields1008
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1009 := msg
	_ = fields1009
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1014 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1014 != nil {
		p.write(*flat1014)
		return nil
	} else {
		_dollar_dollar := msg
		_t1624 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1010 := []interface{}{_t1624, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1011 := fields1010
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1012 := unwrapped_fields1011[0].([]interface{})
		p.pretty_bindings(field1012)
		p.newline()
		field1013 := unwrapped_fields1011[1].(*pb.Formula)
		p.pretty_formula(field1013)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1020 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1020 != nil {
		p.write(*flat1020)
		return nil
	} else {
		_dollar_dollar := msg
		fields1015 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1016 := fields1015
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1017 := unwrapped_fields1016[0].(*pb.Abstraction)
		p.pretty_abstraction(field1017)
		p.newline()
		field1018 := unwrapped_fields1016[1].(*pb.Abstraction)
		p.pretty_abstraction(field1018)
		p.newline()
		field1019 := unwrapped_fields1016[2].([]*pb.Term)
		p.pretty_terms(field1019)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1024 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1024 != nil {
		p.write(*flat1024)
		return nil
	} else {
		fields1021 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1021) == 0) {
			p.newline()
			for i1023, elem1022 := range fields1021 {
				if (i1023 > 0) {
					p.newline()
				}
				p.pretty_term(elem1022)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1029 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1029 != nil {
		p.write(*flat1029)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1625 = _dollar_dollar.GetVar()
		}
		deconstruct_result1027 := _t1625
		if deconstruct_result1027 != nil {
			unwrapped1028 := deconstruct_result1027
			p.pretty_var(unwrapped1028)
		} else {
			_dollar_dollar := msg
			var _t1626 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1626 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1025 := _t1626
			if deconstruct_result1025 != nil {
				unwrapped1026 := deconstruct_result1025
				p.pretty_value(unwrapped1026)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		_dollar_dollar := msg
		fields1030 := _dollar_dollar.GetName()
		unwrapped_fields1031 := fields1030
		p.write(unwrapped_fields1031)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1058 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1058 != nil {
		p.write(*flat1058)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1627 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1056 := _t1627
		if deconstruct_result1056 != nil {
			unwrapped1057 := deconstruct_result1056
			p.pretty_date(unwrapped1057)
		} else {
			_dollar_dollar := msg
			var _t1628 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1628 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1054 := _t1628
			if deconstruct_result1054 != nil {
				unwrapped1055 := deconstruct_result1054
				p.pretty_datetime(unwrapped1055)
			} else {
				_dollar_dollar := msg
				var _t1629 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1629 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1052 := _t1629
				if deconstruct_result1052 != nil {
					unwrapped1053 := *deconstruct_result1052
					p.write(p.formatStringValue(unwrapped1053))
				} else {
					_dollar_dollar := msg
					var _t1630 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1630 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1050 := _t1630
					if deconstruct_result1050 != nil {
						unwrapped1051 := *deconstruct_result1050
						p.write(fmt.Sprintf("%di32", unwrapped1051))
					} else {
						_dollar_dollar := msg
						var _t1631 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1631 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1048 := _t1631
						if deconstruct_result1048 != nil {
							unwrapped1049 := *deconstruct_result1048
							p.write(fmt.Sprintf("%d", unwrapped1049))
						} else {
							_dollar_dollar := msg
							var _t1632 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1632 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1046 := _t1632
							if deconstruct_result1046 != nil {
								unwrapped1047 := *deconstruct_result1046
								p.write(formatFloat32(unwrapped1047))
							} else {
								_dollar_dollar := msg
								var _t1633 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1633 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1044 := _t1633
								if deconstruct_result1044 != nil {
									unwrapped1045 := *deconstruct_result1044
									p.write(formatFloat64(unwrapped1045))
								} else {
									_dollar_dollar := msg
									var _t1634 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1634 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1042 := _t1634
									if deconstruct_result1042 != nil {
										unwrapped1043 := *deconstruct_result1042
										p.write(fmt.Sprintf("%du32", unwrapped1043))
									} else {
										_dollar_dollar := msg
										var _t1635 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1635 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1040 := _t1635
										if deconstruct_result1040 != nil {
											unwrapped1041 := deconstruct_result1040
											p.write(p.formatUint128(unwrapped1041))
										} else {
											_dollar_dollar := msg
											var _t1636 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1636 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1038 := _t1636
											if deconstruct_result1038 != nil {
												unwrapped1039 := deconstruct_result1038
												p.write(p.formatInt128(unwrapped1039))
											} else {
												_dollar_dollar := msg
												var _t1637 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1637 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1036 := _t1637
												if deconstruct_result1036 != nil {
													unwrapped1037 := deconstruct_result1036
													p.write(p.formatDecimal(unwrapped1037))
												} else {
													_dollar_dollar := msg
													var _t1638 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1638 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1034 := _t1638
													if deconstruct_result1034 != nil {
														unwrapped1035 := *deconstruct_result1034
														p.pretty_boolean_value(unwrapped1035)
													} else {
														fields1033 := msg
														_ = fields1033
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
	flat1064 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1064 != nil {
		p.write(*flat1064)
		return nil
	} else {
		_dollar_dollar := msg
		fields1059 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1060 := fields1059
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1061 := unwrapped_fields1060[0].(int64)
		p.write(fmt.Sprintf("%d", field1061))
		p.newline()
		field1062 := unwrapped_fields1060[1].(int64)
		p.write(fmt.Sprintf("%d", field1062))
		p.newline()
		field1063 := unwrapped_fields1060[2].(int64)
		p.write(fmt.Sprintf("%d", field1063))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1075 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_dollar_dollar := msg
		fields1065 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1066 := fields1065
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1067 := unwrapped_fields1066[0].(int64)
		p.write(fmt.Sprintf("%d", field1067))
		p.newline()
		field1068 := unwrapped_fields1066[1].(int64)
		p.write(fmt.Sprintf("%d", field1068))
		p.newline()
		field1069 := unwrapped_fields1066[2].(int64)
		p.write(fmt.Sprintf("%d", field1069))
		p.newline()
		field1070 := unwrapped_fields1066[3].(int64)
		p.write(fmt.Sprintf("%d", field1070))
		p.newline()
		field1071 := unwrapped_fields1066[4].(int64)
		p.write(fmt.Sprintf("%d", field1071))
		p.newline()
		field1072 := unwrapped_fields1066[5].(int64)
		p.write(fmt.Sprintf("%d", field1072))
		field1073 := unwrapped_fields1066[6].(*int64)
		if field1073 != nil {
			p.newline()
			opt_val1074 := *field1073
			p.write(fmt.Sprintf("%d", opt_val1074))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1080 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1080 != nil {
		p.write(*flat1080)
		return nil
	} else {
		_dollar_dollar := msg
		fields1076 := _dollar_dollar.GetArgs()
		unwrapped_fields1077 := fields1076
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1077) == 0) {
			p.newline()
			for i1079, elem1078 := range unwrapped_fields1077 {
				if (i1079 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1078)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1085 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1085 != nil {
		p.write(*flat1085)
		return nil
	} else {
		_dollar_dollar := msg
		fields1081 := _dollar_dollar.GetArgs()
		unwrapped_fields1082 := fields1081
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1082) == 0) {
			p.newline()
			for i1084, elem1083 := range unwrapped_fields1082 {
				if (i1084 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1083)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		_dollar_dollar := msg
		fields1086 := _dollar_dollar.GetArg()
		unwrapped_fields1087 := fields1086
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1087)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1094 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1094 != nil {
		p.write(*flat1094)
		return nil
	} else {
		_dollar_dollar := msg
		fields1089 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1090 := fields1089
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1091 := unwrapped_fields1090[0].(string)
		p.pretty_name(field1091)
		p.newline()
		field1092 := unwrapped_fields1090[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1092)
		p.newline()
		field1093 := unwrapped_fields1090[2].([]*pb.Term)
		p.pretty_terms(field1093)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		fields1095 := msg
		p.write(":")
		p.write(fields1095)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		fields1097 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1097) == 0) {
			p.newline()
			for i1099, elem1098 := range fields1097 {
				if (i1099 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1098)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		fields1101 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1103 := unwrapped_fields1102[0].(*pb.RelationId)
		p.pretty_relation_id(field1103)
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

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_dollar_dollar := msg
		fields1108 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1109 := fields1108
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1110 := unwrapped_fields1109[0].(string)
		p.pretty_name(field1110)
		field1111 := unwrapped_fields1109[1].([]*pb.Term)
		if !(len(field1111) == 0) {
			p.newline()
			for i1113, elem1112 := range field1111 {
				if (i1113 > 0) {
					p.newline()
				}
				p.pretty_term(elem1112)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1639 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1639 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1129 := _t1639
		if guard_result1129 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1640 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1640 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1128 := _t1640
			if guard_result1128 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1641 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1641 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1127 := _t1641
				if guard_result1127 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1642 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1642 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1126 := _t1642
					if guard_result1126 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1643 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1643 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1125 := _t1643
						if guard_result1125 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1644 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1644 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1124 := _t1644
							if guard_result1124 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1645 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1645 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1123 := _t1645
								if guard_result1123 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1646 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1646 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1122 := _t1646
									if guard_result1122 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1647 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1647 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1121 := _t1647
										if guard_result1121 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1115 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1116 := fields1115
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1117 := unwrapped_fields1116[0].(string)
											p.pretty_name(field1117)
											field1118 := unwrapped_fields1116[1].([]*pb.RelTerm)
											if !(len(field1118) == 0) {
												p.newline()
												for i1120, elem1119 := range field1118 {
													if (i1120 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1119)
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
	flat1135 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1648 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1648 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1131 := _t1648
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1133 := unwrapped_fields1132[0].(*pb.Term)
		p.pretty_term(field1133)
		p.newline()
		field1134 := unwrapped_fields1132[1].(*pb.Term)
		p.pretty_term(field1134)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1649 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1649 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1136 := _t1649
		unwrapped_fields1137 := fields1136
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1138 := unwrapped_fields1137[0].(*pb.Term)
		p.pretty_term(field1138)
		p.newline()
		field1139 := unwrapped_fields1137[1].(*pb.Term)
		p.pretty_term(field1139)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1650 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1650 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1141 := _t1650
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1143 := unwrapped_fields1142[0].(*pb.Term)
		p.pretty_term(field1143)
		p.newline()
		field1144 := unwrapped_fields1142[1].(*pb.Term)
		p.pretty_term(field1144)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1651 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1651 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1146 := _t1651
		unwrapped_fields1147 := fields1146
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1148 := unwrapped_fields1147[0].(*pb.Term)
		p.pretty_term(field1148)
		p.newline()
		field1149 := unwrapped_fields1147[1].(*pb.Term)
		p.pretty_term(field1149)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1155 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1155 != nil {
		p.write(*flat1155)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1652 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1652 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1151 := _t1652
		unwrapped_fields1152 := fields1151
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1153 := unwrapped_fields1152[0].(*pb.Term)
		p.pretty_term(field1153)
		p.newline()
		field1154 := unwrapped_fields1152[1].(*pb.Term)
		p.pretty_term(field1154)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1653 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1653 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1156 := _t1653
		unwrapped_fields1157 := fields1156
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1158 := unwrapped_fields1157[0].(*pb.Term)
		p.pretty_term(field1158)
		p.newline()
		field1159 := unwrapped_fields1157[1].(*pb.Term)
		p.pretty_term(field1159)
		p.newline()
		field1160 := unwrapped_fields1157[2].(*pb.Term)
		p.pretty_term(field1160)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1654 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1654 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1162 := _t1654
		unwrapped_fields1163 := fields1162
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1164 := unwrapped_fields1163[0].(*pb.Term)
		p.pretty_term(field1164)
		p.newline()
		field1165 := unwrapped_fields1163[1].(*pb.Term)
		p.pretty_term(field1165)
		p.newline()
		field1166 := unwrapped_fields1163[2].(*pb.Term)
		p.pretty_term(field1166)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1655 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1168 := _t1655
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1170 := unwrapped_fields1169[0].(*pb.Term)
		p.pretty_term(field1170)
		p.newline()
		field1171 := unwrapped_fields1169[1].(*pb.Term)
		p.pretty_term(field1171)
		p.newline()
		field1172 := unwrapped_fields1169[2].(*pb.Term)
		p.pretty_term(field1172)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1656 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1656 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1174 := _t1656
		unwrapped_fields1175 := fields1174
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1176 := unwrapped_fields1175[0].(*pb.Term)
		p.pretty_term(field1176)
		p.newline()
		field1177 := unwrapped_fields1175[1].(*pb.Term)
		p.pretty_term(field1177)
		p.newline()
		field1178 := unwrapped_fields1175[2].(*pb.Term)
		p.pretty_term(field1178)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1657 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1657 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1182 := _t1657
		if deconstruct_result1182 != nil {
			unwrapped1183 := deconstruct_result1182
			p.pretty_specialized_value(unwrapped1183)
		} else {
			_dollar_dollar := msg
			var _t1658 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1658 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1180 := _t1658
			if deconstruct_result1180 != nil {
				unwrapped1181 := deconstruct_result1180
				p.pretty_term(unwrapped1181)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		fields1185 := msg
		p.write("#")
		p.pretty_raw_value(fields1185)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1193 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1193 != nil {
		p.write(*flat1193)
		return nil
	} else {
		_dollar_dollar := msg
		fields1187 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1189 := unwrapped_fields1188[0].(string)
		p.pretty_name(field1189)
		field1190 := unwrapped_fields1188[1].([]*pb.RelTerm)
		if !(len(field1190) == 0) {
			p.newline()
			for i1192, elem1191 := range field1190 {
				if (i1192 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1191)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		_dollar_dollar := msg
		fields1194 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1195 := fields1194
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1196 := unwrapped_fields1195[0].(*pb.Term)
		p.pretty_term(field1196)
		p.newline()
		field1197 := unwrapped_fields1195[1].(*pb.Term)
		p.pretty_term(field1197)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		fields1199 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1199) == 0) {
			p.newline()
			for i1201, elem1200 := range fields1199 {
				if (i1201 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1200)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_dollar_dollar := msg
		fields1203 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1205 := unwrapped_fields1204[0].(string)
		p.pretty_name(field1205)
		field1206 := unwrapped_fields1204[1].([]*pb.Value)
		if !(len(field1206) == 0) {
			p.newline()
			for i1208, elem1207 := range field1206 {
				if (i1208 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1207)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1216 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1216 != nil {
		p.write(*flat1216)
		return nil
	} else {
		_dollar_dollar := msg
		fields1210 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1211 := fields1210
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1212 := unwrapped_fields1211[0].([]*pb.RelationId)
		if !(len(field1212) == 0) {
			p.newline()
			for i1214, elem1213 := range field1212 {
				if (i1214 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1213)
			}
		}
		p.newline()
		field1215 := unwrapped_fields1211[1].(*pb.Script)
		p.pretty_script(field1215)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		fields1217 := _dollar_dollar.GetConstructs()
		unwrapped_fields1218 := fields1217
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1218) == 0) {
			p.newline()
			for i1220, elem1219 := range unwrapped_fields1218 {
				if (i1220 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1219)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1659 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1659 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1224 := _t1659
		if deconstruct_result1224 != nil {
			unwrapped1225 := deconstruct_result1224
			p.pretty_loop(unwrapped1225)
		} else {
			_dollar_dollar := msg
			var _t1660 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1660 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1222 := _t1660
			if deconstruct_result1222 != nil {
				unwrapped1223 := deconstruct_result1222
				p.pretty_instruction(unwrapped1223)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_dollar_dollar := msg
		fields1227 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1229 := unwrapped_fields1228[0].([]*pb.Instruction)
		p.pretty_init(field1229)
		p.newline()
		field1230 := unwrapped_fields1228[1].(*pb.Script)
		p.pretty_script(field1230)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		fields1232 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1232) == 0) {
			p.newline()
			for i1234, elem1233 := range fields1232 {
				if (i1234 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1233)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1661 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1244 := _t1661
		if deconstruct_result1244 != nil {
			unwrapped1245 := deconstruct_result1244
			p.pretty_assign(unwrapped1245)
		} else {
			_dollar_dollar := msg
			var _t1662 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1662 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1242 := _t1662
			if deconstruct_result1242 != nil {
				unwrapped1243 := deconstruct_result1242
				p.pretty_upsert(unwrapped1243)
			} else {
				_dollar_dollar := msg
				var _t1663 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1663 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1240 := _t1663
				if deconstruct_result1240 != nil {
					unwrapped1241 := deconstruct_result1240
					p.pretty_break(unwrapped1241)
				} else {
					_dollar_dollar := msg
					var _t1664 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1664 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1238 := _t1664
					if deconstruct_result1238 != nil {
						unwrapped1239 := deconstruct_result1238
						p.pretty_monoid_def(unwrapped1239)
					} else {
						_dollar_dollar := msg
						var _t1665 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1665 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1236 := _t1665
						if deconstruct_result1236 != nil {
							unwrapped1237 := deconstruct_result1236
							p.pretty_monus_def(unwrapped1237)
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
	flat1253 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1666 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1666 = _dollar_dollar.GetAttrs()
		}
		fields1247 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1666}
		unwrapped_fields1248 := fields1247
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1249 := unwrapped_fields1248[0].(*pb.RelationId)
		p.pretty_relation_id(field1249)
		p.newline()
		field1250 := unwrapped_fields1248[1].(*pb.Abstraction)
		p.pretty_abstraction(field1250)
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

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1260 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1260 != nil {
		p.write(*flat1260)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1667 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1667 = _dollar_dollar.GetAttrs()
		}
		fields1254 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1667}
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1256 := unwrapped_fields1255[0].(*pb.RelationId)
		p.pretty_relation_id(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].([]interface{})
		p.pretty_abstraction_with_arity(field1257)
		field1258 := unwrapped_fields1255[2].([]*pb.Attribute)
		if field1258 != nil {
			p.newline()
			opt_val1259 := field1258
			p.pretty_attrs(opt_val1259)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1265 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		_dollar_dollar := msg
		_t1668 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1261 := []interface{}{_t1668, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1262 := fields1261
		p.write("(")
		p.indent()
		field1263 := unwrapped_fields1262[0].([]interface{})
		p.pretty_bindings(field1263)
		p.newline()
		field1264 := unwrapped_fields1262[1].(*pb.Formula)
		p.pretty_formula(field1264)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1669 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1669 = _dollar_dollar.GetAttrs()
		}
		fields1266 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1669}
		unwrapped_fields1267 := fields1266
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1268 := unwrapped_fields1267[0].(*pb.RelationId)
		p.pretty_relation_id(field1268)
		p.newline()
		field1269 := unwrapped_fields1267[1].(*pb.Abstraction)
		p.pretty_abstraction(field1269)
		field1270 := unwrapped_fields1267[2].([]*pb.Attribute)
		if field1270 != nil {
			p.newline()
			opt_val1271 := field1270
			p.pretty_attrs(opt_val1271)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1280 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1280 != nil {
		p.write(*flat1280)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1670 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1670 = _dollar_dollar.GetAttrs()
		}
		fields1273 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1670}
		unwrapped_fields1274 := fields1273
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1275 := unwrapped_fields1274[0].(*pb.Monoid)
		p.pretty_monoid(field1275)
		p.newline()
		field1276 := unwrapped_fields1274[1].(*pb.RelationId)
		p.pretty_relation_id(field1276)
		p.newline()
		field1277 := unwrapped_fields1274[2].([]interface{})
		p.pretty_abstraction_with_arity(field1277)
		field1278 := unwrapped_fields1274[3].([]*pb.Attribute)
		if field1278 != nil {
			p.newline()
			opt_val1279 := field1278
			p.pretty_attrs(opt_val1279)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1671 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1287 := _t1671
		if deconstruct_result1287 != nil {
			unwrapped1288 := deconstruct_result1287
			p.pretty_or_monoid(unwrapped1288)
		} else {
			_dollar_dollar := msg
			var _t1672 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1672 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1285 := _t1672
			if deconstruct_result1285 != nil {
				unwrapped1286 := deconstruct_result1285
				p.pretty_min_monoid(unwrapped1286)
			} else {
				_dollar_dollar := msg
				var _t1673 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1673 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1283 := _t1673
				if deconstruct_result1283 != nil {
					unwrapped1284 := deconstruct_result1283
					p.pretty_max_monoid(unwrapped1284)
				} else {
					_dollar_dollar := msg
					var _t1674 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1674 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1281 := _t1674
					if deconstruct_result1281 != nil {
						unwrapped1282 := deconstruct_result1281
						p.pretty_sum_monoid(unwrapped1282)
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
	fields1290 := msg
	_ = fields1290
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1293 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1293 != nil {
		p.write(*flat1293)
		return nil
	} else {
		_dollar_dollar := msg
		fields1291 := _dollar_dollar.GetType()
		unwrapped_fields1292 := fields1291
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1292)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		fields1294 := _dollar_dollar.GetType()
		unwrapped_fields1295 := fields1294
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1295)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1299 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1299 != nil {
		p.write(*flat1299)
		return nil
	} else {
		_dollar_dollar := msg
		fields1297 := _dollar_dollar.GetType()
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1298)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1675 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1675 = _dollar_dollar.GetAttrs()
		}
		fields1300 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1675}
		unwrapped_fields1301 := fields1300
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1302 := unwrapped_fields1301[0].(*pb.Monoid)
		p.pretty_monoid(field1302)
		p.newline()
		field1303 := unwrapped_fields1301[1].(*pb.RelationId)
		p.pretty_relation_id(field1303)
		p.newline()
		field1304 := unwrapped_fields1301[2].([]interface{})
		p.pretty_abstraction_with_arity(field1304)
		field1305 := unwrapped_fields1301[3].([]*pb.Attribute)
		if field1305 != nil {
			p.newline()
			opt_val1306 := field1305
			p.pretty_attrs(opt_val1306)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1314 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1314 != nil {
		p.write(*flat1314)
		return nil
	} else {
		_dollar_dollar := msg
		fields1308 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1309 := fields1308
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1310 := unwrapped_fields1309[0].(*pb.RelationId)
		p.pretty_relation_id(field1310)
		p.newline()
		field1311 := unwrapped_fields1309[1].(*pb.Abstraction)
		p.pretty_abstraction(field1311)
		p.newline()
		field1312 := unwrapped_fields1309[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1312)
		p.newline()
		field1313 := unwrapped_fields1309[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1313)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1318 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1318 != nil {
		p.write(*flat1318)
		return nil
	} else {
		fields1315 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1315) == 0) {
			p.newline()
			for i1317, elem1316 := range fields1315 {
				if (i1317 > 0) {
					p.newline()
				}
				p.pretty_var(elem1316)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1322 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		fields1319 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1319) == 0) {
			p.newline()
			for i1321, elem1320 := range fields1319 {
				if (i1321 > 0) {
					p.newline()
				}
				p.pretty_var(elem1320)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1331 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1331 != nil {
		p.write(*flat1331)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1676 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1676 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1329 := _t1676
		if deconstruct_result1329 != nil {
			unwrapped1330 := deconstruct_result1329
			p.pretty_edb(unwrapped1330)
		} else {
			_dollar_dollar := msg
			var _t1677 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1677 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1327 := _t1677
			if deconstruct_result1327 != nil {
				unwrapped1328 := deconstruct_result1327
				p.pretty_betree_relation(unwrapped1328)
			} else {
				_dollar_dollar := msg
				var _t1678 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1678 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1325 := _t1678
				if deconstruct_result1325 != nil {
					unwrapped1326 := deconstruct_result1325
					p.pretty_csv_data(unwrapped1326)
				} else {
					_dollar_dollar := msg
					var _t1679 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1679 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1323 := _t1679
					if deconstruct_result1323 != nil {
						unwrapped1324 := deconstruct_result1323
						p.pretty_iceberg_data(unwrapped1324)
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
	flat1337 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1337 != nil {
		p.write(*flat1337)
		return nil
	} else {
		_dollar_dollar := msg
		fields1332 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1333 := fields1332
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1334 := unwrapped_fields1333[0].(*pb.RelationId)
		p.pretty_relation_id(field1334)
		p.newline()
		field1335 := unwrapped_fields1333[1].([]string)
		p.pretty_edb_path(field1335)
		p.newline()
		field1336 := unwrapped_fields1333[2].([]*pb.Type)
		p.pretty_edb_types(field1336)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1341 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1341 != nil {
		p.write(*flat1341)
		return nil
	} else {
		fields1338 := msg
		p.write("[")
		p.indent()
		for i1340, elem1339 := range fields1338 {
			if (i1340 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1339))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1345 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1345 != nil {
		p.write(*flat1345)
		return nil
	} else {
		fields1342 := msg
		p.write("[")
		p.indent()
		for i1344, elem1343 := range fields1342 {
			if (i1344 > 0) {
				p.newline()
			}
			p.pretty_type(elem1343)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1350 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1350 != nil {
		p.write(*flat1350)
		return nil
	} else {
		_dollar_dollar := msg
		fields1346 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1347 := fields1346
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1348 := unwrapped_fields1347[0].(*pb.RelationId)
		p.pretty_relation_id(field1348)
		p.newline()
		field1349 := unwrapped_fields1347[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1349)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1356 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1356 != nil {
		p.write(*flat1356)
		return nil
	} else {
		_dollar_dollar := msg
		_t1680 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1351 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1680}
		unwrapped_fields1352 := fields1351
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1353 := unwrapped_fields1352[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1353)
		p.newline()
		field1354 := unwrapped_fields1352[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1354)
		p.newline()
		field1355 := unwrapped_fields1352[2].([][]interface{})
		p.pretty_config_dict(field1355)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1360 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1360 != nil {
		p.write(*flat1360)
		return nil
	} else {
		fields1357 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1357) == 0) {
			p.newline()
			for i1359, elem1358 := range fields1357 {
				if (i1359 > 0) {
					p.newline()
				}
				p.pretty_type(elem1358)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1364 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1364 != nil {
		p.write(*flat1364)
		return nil
	} else {
		fields1361 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1361) == 0) {
			p.newline()
			for i1363, elem1362 := range fields1361 {
				if (i1363 > 0) {
					p.newline()
				}
				p.pretty_type(elem1362)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		fields1365 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1366 := fields1365
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1367 := unwrapped_fields1366[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1367)
		p.newline()
		field1368 := unwrapped_fields1366[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1368)
		p.newline()
		field1369 := unwrapped_fields1366[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1369)
		p.newline()
		field1370 := unwrapped_fields1366[3].(string)
		p.pretty_csv_asof(field1370)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1378 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1378 != nil {
		p.write(*flat1378)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1681 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1681 = _dollar_dollar.GetPaths()
		}
		var _t1682 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1682 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1372 := []interface{}{_t1681, _t1682}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1374 := unwrapped_fields1373[0].([]string)
		if field1374 != nil {
			p.newline()
			opt_val1375 := field1374
			p.pretty_csv_locator_paths(opt_val1375)
		}
		field1376 := unwrapped_fields1373[1].(*string)
		if field1376 != nil {
			p.newline()
			opt_val1377 := *field1376
			p.pretty_csv_locator_inline_data(opt_val1377)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		fields1379 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1379) == 0) {
			p.newline()
			for i1381, elem1380 := range fields1379 {
				if (i1381 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1380))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1384 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1384 != nil {
		p.write(*flat1384)
		return nil
	} else {
		fields1383 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1383))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		_dollar_dollar := msg
		_t1683 := p.deconstruct_csv_config(_dollar_dollar)
		fields1385 := _t1683
		unwrapped_fields1386 := fields1385
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1386)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1391 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1391 != nil {
		p.write(*flat1391)
		return nil
	} else {
		fields1388 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1388) == 0) {
			p.newline()
			for i1390, elem1389 := range fields1388 {
				if (i1390 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1389)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1684 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1684 = _dollar_dollar.GetTargetId()
		}
		fields1392 := []interface{}{_dollar_dollar.GetColumnPath(), _t1684, _dollar_dollar.GetTypes()}
		unwrapped_fields1393 := fields1392
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1394 := unwrapped_fields1393[0].([]string)
		p.pretty_gnf_column_path(field1394)
		field1395 := unwrapped_fields1393[1].(*pb.RelationId)
		if field1395 != nil {
			p.newline()
			opt_val1396 := field1395
			p.pretty_relation_id(opt_val1396)
		}
		p.newline()
		p.write("[")
		field1397 := unwrapped_fields1393[2].([]*pb.Type)
		for i1399, elem1398 := range field1397 {
			if (i1399 > 0) {
				p.newline()
			}
			p.pretty_type(elem1398)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1407 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1685 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1685 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1405 := _t1685
		if deconstruct_result1405 != nil {
			unwrapped1406 := *deconstruct_result1405
			p.write(p.formatStringValue(unwrapped1406))
		} else {
			_dollar_dollar := msg
			var _t1686 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1686 = _dollar_dollar
			}
			deconstruct_result1401 := _t1686
			if deconstruct_result1401 != nil {
				unwrapped1402 := deconstruct_result1401
				p.write("[")
				p.indent()
				for i1404, elem1403 := range unwrapped1402 {
					if (i1404 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1403))
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
	flat1409 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1409 != nil {
		p.write(*flat1409)
		return nil
	} else {
		fields1408 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1408))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		_dollar_dollar := msg
		_t1687 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1410 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1687}
		unwrapped_fields1411 := fields1410
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1412 := unwrapped_fields1411[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1412)
		p.newline()
		field1413 := unwrapped_fields1411[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1413)
		p.newline()
		field1414 := unwrapped_fields1411[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1414)
		field1415 := unwrapped_fields1411[3].(*string)
		if field1415 != nil {
			p.newline()
			opt_val1416 := *field1415
			p.pretty_iceberg_to_snapshot(opt_val1416)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1425 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		_dollar_dollar := msg
		fields1418 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1420 := unwrapped_fields1419[0].(string)
		p.write(p.formatStringValue(field1420))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1421 := unwrapped_fields1419[1].([]string)
		if !(len(field1421) == 0) {
			p.newline()
			for i1423, elem1422 := range field1421 {
				if (i1423 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1422))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1424 := unwrapped_fields1419[2].(string)
		p.write(p.formatStringValue(field1424))
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1437 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1437 != nil {
		p.write(*flat1437)
		return nil
	} else {
		_dollar_dollar := msg
		_t1688 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1426 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1688, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1427 := fields1426
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1428 := unwrapped_fields1427[0].(string)
		p.write(p.formatStringValue(field1428))
		p.dedent()
		p.write(")")
		field1429 := unwrapped_fields1427[1].(*string)
		if field1429 != nil {
			p.newline()
			opt_val1430 := *field1429
			p.pretty_iceberg_catalog_config_scope(opt_val1430)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1431 := unwrapped_fields1427[2].([][]interface{})
		if !(len(field1431) == 0) {
			p.newline()
			for i1433, elem1432 := range field1431 {
				if (i1433 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1432)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1434 := unwrapped_fields1427[3].([][]interface{})
		if !(len(field1434) == 0) {
			p.newline()
			for i1436, elem1435 := range field1434 {
				if (i1436 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1435)
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
	flat1439 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1439 != nil {
		p.write(*flat1439)
		return nil
	} else {
		fields1438 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1438))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1444 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1444 != nil {
		p.write(*flat1444)
		return nil
	} else {
		_dollar_dollar := msg
		fields1440 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1441 := fields1440
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1442 := unwrapped_fields1441[0].(string)
		p.write(p.formatStringValue(field1442))
		p.newline()
		field1443 := unwrapped_fields1441[1].(string)
		p.write(p.formatStringValue(field1443))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1446 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1446 != nil {
		p.write(*flat1446)
		return nil
	} else {
		fields1445 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1445))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		_dollar_dollar := msg
		fields1447 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1448 := fields1447
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1448)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1454 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1454 != nil {
		p.write(*flat1454)
		return nil
	} else {
		_dollar_dollar := msg
		fields1450 := _dollar_dollar.GetRelations()
		unwrapped_fields1451 := fields1450
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1451) == 0) {
			p.newline()
			for i1453, elem1452 := range unwrapped_fields1451 {
				if (i1453 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1452)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1459 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1459 != nil {
		p.write(*flat1459)
		return nil
	} else {
		_dollar_dollar := msg
		fields1455 := _dollar_dollar.GetMappings()
		unwrapped_fields1456 := fields1455
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1456) == 0) {
			p.newline()
			for i1458, elem1457 := range unwrapped_fields1456 {
				if (i1458 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1457)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		_dollar_dollar := msg
		fields1460 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1461 := fields1460
		field1462 := unwrapped_fields1461[0].([]string)
		p.pretty_edb_path(field1462)
		p.write(" ")
		field1463 := unwrapped_fields1461[1].(*pb.RelationId)
		p.pretty_relation_id(field1463)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		fields1465 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1465) == 0) {
			p.newline()
			for i1467, elem1466 := range fields1465 {
				if (i1467 > 0) {
					p.newline()
				}
				p.pretty_read(elem1466)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1479 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1479 != nil {
		p.write(*flat1479)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1689 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1689 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1477 := _t1689
		if deconstruct_result1477 != nil {
			unwrapped1478 := deconstruct_result1477
			p.pretty_demand(unwrapped1478)
		} else {
			_dollar_dollar := msg
			var _t1690 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1690 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1475 := _t1690
			if deconstruct_result1475 != nil {
				unwrapped1476 := deconstruct_result1475
				p.pretty_output(unwrapped1476)
			} else {
				_dollar_dollar := msg
				var _t1691 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1691 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1473 := _t1691
				if deconstruct_result1473 != nil {
					unwrapped1474 := deconstruct_result1473
					p.pretty_what_if(unwrapped1474)
				} else {
					_dollar_dollar := msg
					var _t1692 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1692 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1471 := _t1692
					if deconstruct_result1471 != nil {
						unwrapped1472 := deconstruct_result1471
						p.pretty_abort(unwrapped1472)
					} else {
						_dollar_dollar := msg
						var _t1693 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1693 = _dollar_dollar.GetExport()
						}
						deconstruct_result1469 := _t1693
						if deconstruct_result1469 != nil {
							unwrapped1470 := deconstruct_result1469
							p.pretty_export(unwrapped1470)
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
	flat1482 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		_dollar_dollar := msg
		fields1480 := _dollar_dollar.GetRelationId()
		unwrapped_fields1481 := fields1480
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1481)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1487 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1487 != nil {
		p.write(*flat1487)
		return nil
	} else {
		_dollar_dollar := msg
		fields1483 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1484 := fields1483
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1485 := unwrapped_fields1484[0].(string)
		p.pretty_name(field1485)
		p.newline()
		field1486 := unwrapped_fields1484[1].(*pb.RelationId)
		p.pretty_relation_id(field1486)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		_dollar_dollar := msg
		fields1488 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1489 := fields1488
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1490 := unwrapped_fields1489[0].(string)
		p.pretty_name(field1490)
		p.newline()
		field1491 := unwrapped_fields1489[1].(*pb.Epoch)
		p.pretty_epoch(field1491)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1498 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1498 != nil {
		p.write(*flat1498)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1694 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1694 = ptr(_dollar_dollar.GetName())
		}
		fields1493 := []interface{}{_t1694, _dollar_dollar.GetRelationId()}
		unwrapped_fields1494 := fields1493
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1495 := unwrapped_fields1494[0].(*string)
		if field1495 != nil {
			p.newline()
			opt_val1496 := *field1495
			p.pretty_name(opt_val1496)
		}
		p.newline()
		field1497 := unwrapped_fields1494[1].(*pb.RelationId)
		p.pretty_relation_id(field1497)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1503 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1503 != nil {
		p.write(*flat1503)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1695 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1695 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1501 := _t1695
		if deconstruct_result1501 != nil {
			unwrapped1502 := deconstruct_result1501
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1502)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1696 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1696 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1499 := _t1696
			if deconstruct_result1499 != nil {
				unwrapped1500 := deconstruct_result1499
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1500)
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
	flat1514 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1514 != nil {
		p.write(*flat1514)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1697 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1509 := _t1697
		if deconstruct_result1509 != nil {
			unwrapped1510 := deconstruct_result1509
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1511 := unwrapped1510[0].(string)
			p.pretty_export_csv_path(field1511)
			p.newline()
			field1512 := unwrapped1510[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1512)
			p.newline()
			field1513 := unwrapped1510[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1513)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1698 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1699 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1698 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1699}
			}
			deconstruct_result1504 := _t1698
			if deconstruct_result1504 != nil {
				unwrapped1505 := deconstruct_result1504
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1506 := unwrapped1505[0].(string)
				p.pretty_export_csv_path(field1506)
				p.newline()
				field1507 := unwrapped1505[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1507)
				p.newline()
				field1508 := unwrapped1505[2].([][]interface{})
				p.pretty_config_dict(field1508)
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
	flat1516 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1516 != nil {
		p.write(*flat1516)
		return nil
	} else {
		fields1515 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1515))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1523 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1523 != nil {
		p.write(*flat1523)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1700 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1700 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1519 := _t1700
		if deconstruct_result1519 != nil {
			unwrapped1520 := deconstruct_result1519
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1520) == 0) {
				p.newline()
				for i1522, elem1521 := range unwrapped1520 {
					if (i1522 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1521)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1701 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1701 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1517 := _t1701
			if deconstruct_result1517 != nil {
				unwrapped1518 := deconstruct_result1517
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1518)
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
	flat1528 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1528 != nil {
		p.write(*flat1528)
		return nil
	} else {
		_dollar_dollar := msg
		fields1524 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1525 := fields1524
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1526 := unwrapped_fields1525[0].(string)
		p.write(p.formatStringValue(field1526))
		p.newline()
		field1527 := unwrapped_fields1525[1].(*pb.RelationId)
		p.pretty_relation_id(field1527)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1532 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1532 != nil {
		p.write(*flat1532)
		return nil
	} else {
		fields1529 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1529) == 0) {
			p.newline()
			for i1531, elem1530 := range fields1529 {
				if (i1531 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1530)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1543 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1543 != nil {
		p.write(*flat1543)
		return nil
	} else {
		_dollar_dollar := msg
		_t1702 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1533 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1702}
		unwrapped_fields1534 := fields1533
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1535 := unwrapped_fields1534[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1535)
		p.newline()
		field1536 := unwrapped_fields1534[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1536)
		p.newline()
		field1537 := unwrapped_fields1534[2].(*pb.ExportIcebergColumns)
		p.pretty_export_iceberg_columns(field1537)
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_properties")
		field1538 := unwrapped_fields1534[3].([][]interface{})
		if !(len(field1538) == 0) {
			p.newline()
			for i1540, elem1539 := range field1538 {
				if (i1540 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1539)
			}
		}
		p.dedent()
		p.write(")")
		field1541 := unwrapped_fields1534[4].([][]interface{})
		if field1541 != nil {
			p.newline()
			opt_val1542 := field1541
			p.pretty_config_dict(opt_val1542)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_columns(msg *pb.ExportIcebergColumns) interface{} {
	flat1550 := p.tryFlat(msg, func() { p.pretty_export_iceberg_columns(msg) })
	if flat1550 != nil {
		p.write(*flat1550)
		return nil
	} else {
		_dollar_dollar := msg
		fields1544 := []interface{}{_dollar_dollar, _dollar_dollar.GetTargetColumns()}
		unwrapped_fields1545 := fields1544
		p.write("(")
		p.write("columns")
		p.indentSexp()
		p.newline()
		field1546 := unwrapped_fields1545[0].(*pb.ExportIcebergColumns)
		p.pretty_export_iceberg_column_source(field1546)
		p.newline()
		p.write("(")
		p.newline()
		p.write("target_columns")
		field1547 := unwrapped_fields1545[1].([]*pb.ExportIcebergColumn)
		if !(len(field1547) == 0) {
			p.newline()
			for i1549, elem1548 := range field1547 {
				if (i1549 > 0) {
					p.newline()
				}
				p.pretty_export_iceberg_column(elem1548)
			}
		}
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column_source(msg *pb.ExportIcebergColumns) interface{} {
	flat1557 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column_source(msg) })
	if flat1557 != nil {
		p.write(*flat1557)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []*pb.RelationId
		if hasProtoField(_dollar_dollar, "source_gnf_defs") {
			_t1703 = _dollar_dollar.GetSourceGnfDefs().GetDefs()
		}
		deconstruct_result1553 := _t1703
		if deconstruct_result1553 != nil {
			unwrapped1554 := deconstruct_result1553
			p.write("(")
			p.write("source_gnf_defs")
			p.indentSexp()
			if !(len(unwrapped1554) == 0) {
				p.newline()
				for i1556, elem1555 := range unwrapped1554 {
					if (i1556 > 0) {
						p.newline()
					}
					p.pretty_relation_id(elem1555)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1704 *pb.RelationId
			if hasProtoField(_dollar_dollar, "source_table_def") {
				_t1704 = _dollar_dollar.GetSourceTableDef()
			}
			deconstruct_result1551 := _t1704
			if deconstruct_result1551 != nil {
				unwrapped1552 := deconstruct_result1551
				p.write("(")
				p.write("source_table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1552)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_iceberg_column_source"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column(msg *pb.ExportIcebergColumn) interface{} {
	flat1563 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column(msg) })
	if flat1563 != nil {
		p.write(*flat1563)
		return nil
	} else {
		_dollar_dollar := msg
		fields1558 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType(), _dollar_dollar.GetNullable()}
		unwrapped_fields1559 := fields1558
		p.write("(")
		p.write("iceberg_column")
		p.indentSexp()
		p.newline()
		field1560 := unwrapped_fields1559[0].(string)
		p.write(p.formatStringValue(field1560))
		p.newline()
		field1561 := unwrapped_fields1559[1].(*pb.Type)
		p.pretty_type(field1561)
		p.newline()
		field1562 := unwrapped_fields1559[2].(bool)
		p.pretty_boolean_value(field1562)
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
		_t1749 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1749)
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

func (p *PrettyPrinter) pretty_export_iceberg_gnf_defs(msg *pb.ExportIcebergGnfDefs) interface{} {
	p.write("(export_iceberg_gnf_defs")
	p.indentSexp()
	p.newline()
	p.write(":defs ")
	p.write("(")
	for _idx, _elem := range msg.GetDefs() {
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
	case *pb.ExportIcebergGnfDefs:
		p.pretty_export_iceberg_gnf_defs(m)
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
