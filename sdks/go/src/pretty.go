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
	// Non-pointer types (e.g., RelationId passed to different wrapper nonterminals)
	// cannot be safely memoized because the same value may need different renderings
	// depending on the calling context. Always render fresh.
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
	_t1741 := &pb.Value{}
	_t1741.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1741
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1742 := &pb.Value{}
	_t1742.Value = &pb.Value_IntValue{IntValue: v}
	return _t1742
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1743 := &pb.Value{}
	_t1743.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1743
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1744 := &pb.Value{}
	_t1744.Value = &pb.Value_StringValue{StringValue: v}
	return _t1744
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1745 := &pb.Value{}
	_t1745.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1745
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1746 := &pb.Value{}
	_t1746.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1746
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1747 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1747})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1748 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1748})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1749 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1749})
			}
		}
	}
	_t1750 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1750})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1751 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1751})
	_t1752 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1752})
	if msg.GetNewLine() != "" {
		_t1753 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1753})
	}
	_t1754 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1754})
	_t1755 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1755})
	_t1756 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1756})
	if msg.GetComment() != "" {
		_t1757 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1757})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1758 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1758})
	}
	_t1759 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1759})
	_t1760 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1760})
	_t1761 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1761})
	if msg.GetPartitionSizeMb() != 0 {
		_t1762 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1762})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1763 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1763})
	_t1764 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1764})
	_t1765 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1765})
	_t1766 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1766})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1767 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1767})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1768 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1768})
		}
	}
	_t1769 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1769})
	_t1770 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1770})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1771 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1771})
	}
	if msg.Compression != nil {
		_t1772 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1772})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1773 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1773})
	}
	if msg.SyntaxMissingString != nil {
		_t1774 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1774})
	}
	if msg.SyntaxDelim != nil {
		_t1775 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1775})
	}
	if msg.SyntaxQuotechar != nil {
		_t1776 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1776})
	}
	if msg.SyntaxEscapechar != nil {
		_t1777 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1777})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1778 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1778
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1779 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1779
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1780 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1780
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1781 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1781})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1782 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1782})
	}
	if msg.GetCompression() != "" {
		_t1783 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1783})
	}
	var _t1784 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1784
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1785 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1785
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
	flat809 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat809 != nil {
		p.write(*flat809)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1600 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1600 = _dollar_dollar.GetConfigure()
		}
		var _t1601 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1601 = _dollar_dollar.GetSync()
		}
		fields800 := []interface{}{_t1600, _t1601, _dollar_dollar.GetEpochs()}
		unwrapped_fields801 := fields800
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field802 := unwrapped_fields801[0].(*pb.Configure)
		if field802 != nil {
			p.newline()
			opt_val803 := field802
			p.pretty_configure(opt_val803)
		}
		field804 := unwrapped_fields801[1].(*pb.Sync)
		if field804 != nil {
			p.newline()
			opt_val805 := field804
			p.pretty_sync(opt_val805)
		}
		field806 := unwrapped_fields801[2].([]*pb.Epoch)
		if !(len(field806) == 0) {
			p.newline()
			for i808, elem807 := range field806 {
				if (i808 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem807)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat812 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat812 != nil {
		p.write(*flat812)
		return nil
	} else {
		_dollar_dollar := msg
		_t1602 := p.deconstruct_configure(_dollar_dollar)
		fields810 := _t1602
		unwrapped_fields811 := fields810
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields811)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat816 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat816 != nil {
		p.write(*flat816)
		return nil
	} else {
		fields813 := msg
		p.write("{")
		p.indent()
		if !(len(fields813) == 0) {
			p.newline()
			for i815, elem814 := range fields813 {
				if (i815 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem814)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat821 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat821 != nil {
		p.write(*flat821)
		return nil
	} else {
		_dollar_dollar := msg
		fields817 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields818 := fields817
		p.write(":")
		field819 := unwrapped_fields818[0].(string)
		p.write(field819)
		p.write(" ")
		field820 := unwrapped_fields818[1].(*pb.Value)
		p.pretty_raw_value(field820)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat847 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat847 != nil {
		p.write(*flat847)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1603 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1603 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result845 := _t1603
		if deconstruct_result845 != nil {
			unwrapped846 := deconstruct_result845
			p.pretty_raw_date(unwrapped846)
		} else {
			_dollar_dollar := msg
			var _t1604 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1604 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result843 := _t1604
			if deconstruct_result843 != nil {
				unwrapped844 := deconstruct_result843
				p.pretty_raw_datetime(unwrapped844)
			} else {
				_dollar_dollar := msg
				var _t1605 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1605 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result841 := _t1605
				if deconstruct_result841 != nil {
					unwrapped842 := *deconstruct_result841
					p.write(p.formatStringValue(unwrapped842))
				} else {
					_dollar_dollar := msg
					var _t1606 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1606 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result839 := _t1606
					if deconstruct_result839 != nil {
						unwrapped840 := *deconstruct_result839
						p.write(fmt.Sprintf("%di32", unwrapped840))
					} else {
						_dollar_dollar := msg
						var _t1607 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1607 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result837 := _t1607
						if deconstruct_result837 != nil {
							unwrapped838 := *deconstruct_result837
							p.write(fmt.Sprintf("%d", unwrapped838))
						} else {
							_dollar_dollar := msg
							var _t1608 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1608 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result835 := _t1608
							if deconstruct_result835 != nil {
								unwrapped836 := *deconstruct_result835
								p.write(formatFloat32(unwrapped836))
							} else {
								_dollar_dollar := msg
								var _t1609 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1609 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result833 := _t1609
								if deconstruct_result833 != nil {
									unwrapped834 := *deconstruct_result833
									p.write(formatFloat64(unwrapped834))
								} else {
									_dollar_dollar := msg
									var _t1610 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1610 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result831 := _t1610
									if deconstruct_result831 != nil {
										unwrapped832 := *deconstruct_result831
										p.write(fmt.Sprintf("%du32", unwrapped832))
									} else {
										_dollar_dollar := msg
										var _t1611 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1611 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result829 := _t1611
										if deconstruct_result829 != nil {
											unwrapped830 := deconstruct_result829
											p.write(p.formatUint128(unwrapped830))
										} else {
											_dollar_dollar := msg
											var _t1612 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1612 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result827 := _t1612
											if deconstruct_result827 != nil {
												unwrapped828 := deconstruct_result827
												p.write(p.formatInt128(unwrapped828))
											} else {
												_dollar_dollar := msg
												var _t1613 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1613 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result825 := _t1613
												if deconstruct_result825 != nil {
													unwrapped826 := deconstruct_result825
													p.write(p.formatDecimal(unwrapped826))
												} else {
													_dollar_dollar := msg
													var _t1614 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1614 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result823 := _t1614
													if deconstruct_result823 != nil {
														unwrapped824 := *deconstruct_result823
														p.pretty_boolean_value(unwrapped824)
													} else {
														fields822 := msg
														_ = fields822
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
	flat853 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat853 != nil {
		p.write(*flat853)
		return nil
	} else {
		_dollar_dollar := msg
		fields848 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields849 := fields848
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field850 := unwrapped_fields849[0].(int64)
		p.write(fmt.Sprintf("%d", field850))
		p.newline()
		field851 := unwrapped_fields849[1].(int64)
		p.write(fmt.Sprintf("%d", field851))
		p.newline()
		field852 := unwrapped_fields849[2].(int64)
		p.write(fmt.Sprintf("%d", field852))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_dollar_dollar := msg
		fields854 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields855 := fields854
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field856 := unwrapped_fields855[0].(int64)
		p.write(fmt.Sprintf("%d", field856))
		p.newline()
		field857 := unwrapped_fields855[1].(int64)
		p.write(fmt.Sprintf("%d", field857))
		p.newline()
		field858 := unwrapped_fields855[2].(int64)
		p.write(fmt.Sprintf("%d", field858))
		p.newline()
		field859 := unwrapped_fields855[3].(int64)
		p.write(fmt.Sprintf("%d", field859))
		p.newline()
		field860 := unwrapped_fields855[4].(int64)
		p.write(fmt.Sprintf("%d", field860))
		p.newline()
		field861 := unwrapped_fields855[5].(int64)
		p.write(fmt.Sprintf("%d", field861))
		field862 := unwrapped_fields855[6].(*int64)
		if field862 != nil {
			p.newline()
			opt_val863 := *field862
			p.write(fmt.Sprintf("%d", opt_val863))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1615 []interface{}
	if _dollar_dollar {
		_t1615 = []interface{}{}
	}
	deconstruct_result867 := _t1615
	if deconstruct_result867 != nil {
		unwrapped868 := deconstruct_result867
		_ = unwrapped868
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1616 []interface{}
		if !(_dollar_dollar) {
			_t1616 = []interface{}{}
		}
		deconstruct_result865 := _t1616
		if deconstruct_result865 != nil {
			unwrapped866 := deconstruct_result865
			_ = unwrapped866
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat873 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat873 != nil {
		p.write(*flat873)
		return nil
	} else {
		_dollar_dollar := msg
		fields869 := _dollar_dollar.GetFragments()
		unwrapped_fields870 := fields869
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields870) == 0) {
			p.newline()
			for i872, elem871 := range unwrapped_fields870 {
				if (i872 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem871)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat876 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_dollar_dollar := msg
		fields874 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields875 := fields874
		p.write(":")
		p.write(unwrapped_fields875)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat883 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat883 != nil {
		p.write(*flat883)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1617 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1617 = _dollar_dollar.GetWrites()
		}
		var _t1618 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1618 = _dollar_dollar.GetReads()
		}
		fields877 := []interface{}{_t1617, _t1618}
		unwrapped_fields878 := fields877
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field879 := unwrapped_fields878[0].([]*pb.Write)
		if field879 != nil {
			p.newline()
			opt_val880 := field879
			p.pretty_epoch_writes(opt_val880)
		}
		field881 := unwrapped_fields878[1].([]*pb.Read)
		if field881 != nil {
			p.newline()
			opt_val882 := field881
			p.pretty_epoch_reads(opt_val882)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		fields884 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields884) == 0) {
			p.newline()
			for i886, elem885 := range fields884 {
				if (i886 > 0) {
					p.newline()
				}
				p.pretty_write(elem885)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat896 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1619 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1619 = _dollar_dollar.GetDefine()
		}
		deconstruct_result894 := _t1619
		if deconstruct_result894 != nil {
			unwrapped895 := deconstruct_result894
			p.pretty_define(unwrapped895)
		} else {
			_dollar_dollar := msg
			var _t1620 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1620 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result892 := _t1620
			if deconstruct_result892 != nil {
				unwrapped893 := deconstruct_result892
				p.pretty_undefine(unwrapped893)
			} else {
				_dollar_dollar := msg
				var _t1621 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1621 = _dollar_dollar.GetContext()
				}
				deconstruct_result890 := _t1621
				if deconstruct_result890 != nil {
					unwrapped891 := deconstruct_result890
					p.pretty_context(unwrapped891)
				} else {
					_dollar_dollar := msg
					var _t1622 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1622 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result888 := _t1622
					if deconstruct_result888 != nil {
						unwrapped889 := deconstruct_result888
						p.pretty_snapshot(unwrapped889)
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
	flat899 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		_dollar_dollar := msg
		fields897 := _dollar_dollar.GetFragment()
		unwrapped_fields898 := fields897
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields898)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields900 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields901 := fields900
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field902 := unwrapped_fields901[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field902)
		field903 := unwrapped_fields901[1].([]*pb.Declaration)
		if !(len(field903) == 0) {
			p.newline()
			for i905, elem904 := range field903 {
				if (i905 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem904)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat908 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat908 != nil {
		p.write(*flat908)
		return nil
	} else {
		fields907 := msg
		p.pretty_fragment_id(fields907)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1623 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1623 = _dollar_dollar.GetDef()
		}
		deconstruct_result915 := _t1623
		if deconstruct_result915 != nil {
			unwrapped916 := deconstruct_result915
			p.pretty_def(unwrapped916)
		} else {
			_dollar_dollar := msg
			var _t1624 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1624 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result913 := _t1624
			if deconstruct_result913 != nil {
				unwrapped914 := deconstruct_result913
				p.pretty_algorithm(unwrapped914)
			} else {
				_dollar_dollar := msg
				var _t1625 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1625 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result911 := _t1625
				if deconstruct_result911 != nil {
					unwrapped912 := deconstruct_result911
					p.pretty_constraint(unwrapped912)
				} else {
					_dollar_dollar := msg
					var _t1626 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1626 = _dollar_dollar.GetData()
					}
					deconstruct_result909 := _t1626
					if deconstruct_result909 != nil {
						unwrapped910 := deconstruct_result909
						p.pretty_data(unwrapped910)
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
	flat924 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat924 != nil {
		p.write(*flat924)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1627 = _dollar_dollar.GetAttrs()
		}
		fields918 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1627}
		unwrapped_fields919 := fields918
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field920 := unwrapped_fields919[0].(*pb.RelationId)
		p.pretty_relation_id(field920)
		p.newline()
		field921 := unwrapped_fields919[1].(*pb.Abstraction)
		p.pretty_abstraction(field921)
		field922 := unwrapped_fields919[2].([]*pb.Attribute)
		if field922 != nil {
			p.newline()
			opt_val923 := field922
			p.pretty_attrs(opt_val923)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat929 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat929 != nil {
		p.write(*flat929)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1628 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1629 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1628 = ptr(_t1629)
		}
		deconstruct_result927 := _t1628
		if deconstruct_result927 != nil {
			unwrapped928 := *deconstruct_result927
			p.write(":")
			p.write(unwrapped928)
		} else {
			_dollar_dollar := msg
			_t1630 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result925 := _t1630
			if deconstruct_result925 != nil {
				unwrapped926 := deconstruct_result925
				p.write(p.formatUint128(unwrapped926))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat934 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat934 != nil {
		p.write(*flat934)
		return nil
	} else {
		_dollar_dollar := msg
		_t1631 := p.deconstruct_bindings(_dollar_dollar)
		fields930 := []interface{}{_t1631, _dollar_dollar.GetValue()}
		unwrapped_fields931 := fields930
		p.write("(")
		p.indent()
		field932 := unwrapped_fields931[0].([]interface{})
		p.pretty_bindings(field932)
		p.newline()
		field933 := unwrapped_fields931[1].(*pb.Formula)
		p.pretty_formula(field933)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat942 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat942 != nil {
		p.write(*flat942)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1632 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1632 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields935 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1632}
		unwrapped_fields936 := fields935
		p.write("[")
		p.indent()
		field937 := unwrapped_fields936[0].([]*pb.Binding)
		for i939, elem938 := range field937 {
			if (i939 > 0) {
				p.newline()
			}
			p.pretty_binding(elem938)
		}
		field940 := unwrapped_fields936[1].([]*pb.Binding)
		if field940 != nil {
			p.newline()
			opt_val941 := field940
			p.pretty_value_bindings(opt_val941)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat947 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat947 != nil {
		p.write(*flat947)
		return nil
	} else {
		_dollar_dollar := msg
		fields943 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields944 := fields943
		field945 := unwrapped_fields944[0].(string)
		p.write(field945)
		p.write("::")
		field946 := unwrapped_fields944[1].(*pb.Type)
		p.pretty_type(field946)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1633 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1633 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result974 := _t1633
		if deconstruct_result974 != nil {
			unwrapped975 := deconstruct_result974
			p.pretty_unspecified_type(unwrapped975)
		} else {
			_dollar_dollar := msg
			var _t1634 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1634 = _dollar_dollar.GetStringType()
			}
			deconstruct_result972 := _t1634
			if deconstruct_result972 != nil {
				unwrapped973 := deconstruct_result972
				p.pretty_string_type(unwrapped973)
			} else {
				_dollar_dollar := msg
				var _t1635 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1635 = _dollar_dollar.GetIntType()
				}
				deconstruct_result970 := _t1635
				if deconstruct_result970 != nil {
					unwrapped971 := deconstruct_result970
					p.pretty_int_type(unwrapped971)
				} else {
					_dollar_dollar := msg
					var _t1636 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1636 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result968 := _t1636
					if deconstruct_result968 != nil {
						unwrapped969 := deconstruct_result968
						p.pretty_float_type(unwrapped969)
					} else {
						_dollar_dollar := msg
						var _t1637 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1637 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result966 := _t1637
						if deconstruct_result966 != nil {
							unwrapped967 := deconstruct_result966
							p.pretty_uint128_type(unwrapped967)
						} else {
							_dollar_dollar := msg
							var _t1638 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1638 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result964 := _t1638
							if deconstruct_result964 != nil {
								unwrapped965 := deconstruct_result964
								p.pretty_int128_type(unwrapped965)
							} else {
								_dollar_dollar := msg
								var _t1639 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1639 = _dollar_dollar.GetDateType()
								}
								deconstruct_result962 := _t1639
								if deconstruct_result962 != nil {
									unwrapped963 := deconstruct_result962
									p.pretty_date_type(unwrapped963)
								} else {
									_dollar_dollar := msg
									var _t1640 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1640 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result960 := _t1640
									if deconstruct_result960 != nil {
										unwrapped961 := deconstruct_result960
										p.pretty_datetime_type(unwrapped961)
									} else {
										_dollar_dollar := msg
										var _t1641 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1641 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result958 := _t1641
										if deconstruct_result958 != nil {
											unwrapped959 := deconstruct_result958
											p.pretty_missing_type(unwrapped959)
										} else {
											_dollar_dollar := msg
											var _t1642 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1642 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result956 := _t1642
											if deconstruct_result956 != nil {
												unwrapped957 := deconstruct_result956
												p.pretty_decimal_type(unwrapped957)
											} else {
												_dollar_dollar := msg
												var _t1643 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1643 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result954 := _t1643
												if deconstruct_result954 != nil {
													unwrapped955 := deconstruct_result954
													p.pretty_boolean_type(unwrapped955)
												} else {
													_dollar_dollar := msg
													var _t1644 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1644 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result952 := _t1644
													if deconstruct_result952 != nil {
														unwrapped953 := deconstruct_result952
														p.pretty_int32_type(unwrapped953)
													} else {
														_dollar_dollar := msg
														var _t1645 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1645 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result950 := _t1645
														if deconstruct_result950 != nil {
															unwrapped951 := deconstruct_result950
															p.pretty_float32_type(unwrapped951)
														} else {
															_dollar_dollar := msg
															var _t1646 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1646 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result948 := _t1646
															if deconstruct_result948 != nil {
																unwrapped949 := deconstruct_result948
																p.pretty_uint32_type(unwrapped949)
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
	fields977 := msg
	_ = fields977
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields978 := msg
	_ = fields978
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields979 := msg
	_ = fields979
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields980 := msg
	_ = fields980
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields981 := msg
	_ = fields981
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields982 := msg
	_ = fields982
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields983 := msg
	_ = fields983
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields984 := msg
	_ = fields984
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields985 := msg
	_ = fields985
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat990 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat990 != nil {
		p.write(*flat990)
		return nil
	} else {
		_dollar_dollar := msg
		fields986 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields987 := fields986
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field988 := unwrapped_fields987[0].(int64)
		p.write(fmt.Sprintf("%d", field988))
		p.newline()
		field989 := unwrapped_fields987[1].(int64)
		p.write(fmt.Sprintf("%d", field989))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields991 := msg
	_ = fields991
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields992 := msg
	_ = fields992
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields993 := msg
	_ = fields993
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields994 := msg
	_ = fields994
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat998 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat998 != nil {
		p.write(*flat998)
		return nil
	} else {
		fields995 := msg
		p.write("|")
		if !(len(fields995) == 0) {
			p.write(" ")
			for i997, elem996 := range fields995 {
				if (i997 > 0) {
					p.newline()
				}
				p.pretty_binding(elem996)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1647 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1023 := _t1647
		if deconstruct_result1023 != nil {
			unwrapped1024 := deconstruct_result1023
			p.pretty_true(unwrapped1024)
		} else {
			_dollar_dollar := msg
			var _t1648 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1648 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1021 := _t1648
			if deconstruct_result1021 != nil {
				unwrapped1022 := deconstruct_result1021
				p.pretty_false(unwrapped1022)
			} else {
				_dollar_dollar := msg
				var _t1649 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1649 = _dollar_dollar.GetExists()
				}
				deconstruct_result1019 := _t1649
				if deconstruct_result1019 != nil {
					unwrapped1020 := deconstruct_result1019
					p.pretty_exists(unwrapped1020)
				} else {
					_dollar_dollar := msg
					var _t1650 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1650 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1017 := _t1650
					if deconstruct_result1017 != nil {
						unwrapped1018 := deconstruct_result1017
						p.pretty_reduce(unwrapped1018)
					} else {
						_dollar_dollar := msg
						var _t1651 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1651 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1015 := _t1651
						if deconstruct_result1015 != nil {
							unwrapped1016 := deconstruct_result1015
							p.pretty_conjunction(unwrapped1016)
						} else {
							_dollar_dollar := msg
							var _t1652 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1652 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1013 := _t1652
							if deconstruct_result1013 != nil {
								unwrapped1014 := deconstruct_result1013
								p.pretty_disjunction(unwrapped1014)
							} else {
								_dollar_dollar := msg
								var _t1653 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1653 = _dollar_dollar.GetNot()
								}
								deconstruct_result1011 := _t1653
								if deconstruct_result1011 != nil {
									unwrapped1012 := deconstruct_result1011
									p.pretty_not(unwrapped1012)
								} else {
									_dollar_dollar := msg
									var _t1654 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1654 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1009 := _t1654
									if deconstruct_result1009 != nil {
										unwrapped1010 := deconstruct_result1009
										p.pretty_ffi(unwrapped1010)
									} else {
										_dollar_dollar := msg
										var _t1655 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1655 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1007 := _t1655
										if deconstruct_result1007 != nil {
											unwrapped1008 := deconstruct_result1007
											p.pretty_atom(unwrapped1008)
										} else {
											_dollar_dollar := msg
											var _t1656 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1656 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1005 := _t1656
											if deconstruct_result1005 != nil {
												unwrapped1006 := deconstruct_result1005
												p.pretty_pragma(unwrapped1006)
											} else {
												_dollar_dollar := msg
												var _t1657 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1657 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1003 := _t1657
												if deconstruct_result1003 != nil {
													unwrapped1004 := deconstruct_result1003
													p.pretty_primitive(unwrapped1004)
												} else {
													_dollar_dollar := msg
													var _t1658 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1658 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1001 := _t1658
													if deconstruct_result1001 != nil {
														unwrapped1002 := deconstruct_result1001
														p.pretty_rel_atom(unwrapped1002)
													} else {
														_dollar_dollar := msg
														var _t1659 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1659 = _dollar_dollar.GetCast()
														}
														deconstruct_result999 := _t1659
														if deconstruct_result999 != nil {
															unwrapped1000 := deconstruct_result999
															p.pretty_cast(unwrapped1000)
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
	fields1026 := msg
	_ = fields1026
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1027 := msg
	_ = fields1027
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		_dollar_dollar := msg
		_t1660 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1028 := []interface{}{_t1660, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1029 := fields1028
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1030 := unwrapped_fields1029[0].([]interface{})
		p.pretty_bindings(field1030)
		p.newline()
		field1031 := unwrapped_fields1029[1].(*pb.Formula)
		p.pretty_formula(field1031)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1038 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1038 != nil {
		p.write(*flat1038)
		return nil
	} else {
		_dollar_dollar := msg
		fields1033 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1034 := fields1033
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1035 := unwrapped_fields1034[0].(*pb.Abstraction)
		p.pretty_abstraction(field1035)
		p.newline()
		field1036 := unwrapped_fields1034[1].(*pb.Abstraction)
		p.pretty_abstraction(field1036)
		p.newline()
		field1037 := unwrapped_fields1034[2].([]*pb.Term)
		p.pretty_terms(field1037)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		fields1039 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1039) == 0) {
			p.newline()
			for i1041, elem1040 := range fields1039 {
				if (i1041 > 0) {
					p.newline()
				}
				p.pretty_term(elem1040)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1047 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1047 != nil {
		p.write(*flat1047)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1661 = _dollar_dollar.GetVar()
		}
		deconstruct_result1045 := _t1661
		if deconstruct_result1045 != nil {
			unwrapped1046 := deconstruct_result1045
			p.pretty_var(unwrapped1046)
		} else {
			_dollar_dollar := msg
			var _t1662 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1662 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1043 := _t1662
			if deconstruct_result1043 != nil {
				unwrapped1044 := deconstruct_result1043
				p.pretty_value(unwrapped1044)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1050 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1050 != nil {
		p.write(*flat1050)
		return nil
	} else {
		_dollar_dollar := msg
		fields1048 := _dollar_dollar.GetName()
		unwrapped_fields1049 := fields1048
		p.write(unwrapped_fields1049)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1076 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1076 != nil {
		p.write(*flat1076)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1663 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1663 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1074 := _t1663
		if deconstruct_result1074 != nil {
			unwrapped1075 := deconstruct_result1074
			p.pretty_date(unwrapped1075)
		} else {
			_dollar_dollar := msg
			var _t1664 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1664 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1072 := _t1664
			if deconstruct_result1072 != nil {
				unwrapped1073 := deconstruct_result1072
				p.pretty_datetime(unwrapped1073)
			} else {
				_dollar_dollar := msg
				var _t1665 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1665 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1070 := _t1665
				if deconstruct_result1070 != nil {
					unwrapped1071 := *deconstruct_result1070
					p.write(p.formatStringValue(unwrapped1071))
				} else {
					_dollar_dollar := msg
					var _t1666 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1666 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1068 := _t1666
					if deconstruct_result1068 != nil {
						unwrapped1069 := *deconstruct_result1068
						p.write(fmt.Sprintf("%di32", unwrapped1069))
					} else {
						_dollar_dollar := msg
						var _t1667 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1667 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1066 := _t1667
						if deconstruct_result1066 != nil {
							unwrapped1067 := *deconstruct_result1066
							p.write(fmt.Sprintf("%d", unwrapped1067))
						} else {
							_dollar_dollar := msg
							var _t1668 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1668 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1064 := _t1668
							if deconstruct_result1064 != nil {
								unwrapped1065 := *deconstruct_result1064
								p.write(formatFloat32(unwrapped1065))
							} else {
								_dollar_dollar := msg
								var _t1669 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1669 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1062 := _t1669
								if deconstruct_result1062 != nil {
									unwrapped1063 := *deconstruct_result1062
									p.write(formatFloat64(unwrapped1063))
								} else {
									_dollar_dollar := msg
									var _t1670 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1670 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1060 := _t1670
									if deconstruct_result1060 != nil {
										unwrapped1061 := *deconstruct_result1060
										p.write(fmt.Sprintf("%du32", unwrapped1061))
									} else {
										_dollar_dollar := msg
										var _t1671 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1671 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1058 := _t1671
										if deconstruct_result1058 != nil {
											unwrapped1059 := deconstruct_result1058
											p.write(p.formatUint128(unwrapped1059))
										} else {
											_dollar_dollar := msg
											var _t1672 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1672 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1056 := _t1672
											if deconstruct_result1056 != nil {
												unwrapped1057 := deconstruct_result1056
												p.write(p.formatInt128(unwrapped1057))
											} else {
												_dollar_dollar := msg
												var _t1673 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1673 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1054 := _t1673
												if deconstruct_result1054 != nil {
													unwrapped1055 := deconstruct_result1054
													p.write(p.formatDecimal(unwrapped1055))
												} else {
													_dollar_dollar := msg
													var _t1674 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1674 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1052 := _t1674
													if deconstruct_result1052 != nil {
														unwrapped1053 := *deconstruct_result1052
														p.pretty_boolean_value(unwrapped1053)
													} else {
														fields1051 := msg
														_ = fields1051
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
	flat1082 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1082 != nil {
		p.write(*flat1082)
		return nil
	} else {
		_dollar_dollar := msg
		fields1077 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1078 := fields1077
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1079 := unwrapped_fields1078[0].(int64)
		p.write(fmt.Sprintf("%d", field1079))
		p.newline()
		field1080 := unwrapped_fields1078[1].(int64)
		p.write(fmt.Sprintf("%d", field1080))
		p.newline()
		field1081 := unwrapped_fields1078[2].(int64)
		p.write(fmt.Sprintf("%d", field1081))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1093 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		_dollar_dollar := msg
		fields1083 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1084 := fields1083
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1085 := unwrapped_fields1084[0].(int64)
		p.write(fmt.Sprintf("%d", field1085))
		p.newline()
		field1086 := unwrapped_fields1084[1].(int64)
		p.write(fmt.Sprintf("%d", field1086))
		p.newline()
		field1087 := unwrapped_fields1084[2].(int64)
		p.write(fmt.Sprintf("%d", field1087))
		p.newline()
		field1088 := unwrapped_fields1084[3].(int64)
		p.write(fmt.Sprintf("%d", field1088))
		p.newline()
		field1089 := unwrapped_fields1084[4].(int64)
		p.write(fmt.Sprintf("%d", field1089))
		p.newline()
		field1090 := unwrapped_fields1084[5].(int64)
		p.write(fmt.Sprintf("%d", field1090))
		field1091 := unwrapped_fields1084[6].(*int64)
		if field1091 != nil {
			p.newline()
			opt_val1092 := *field1091
			p.write(fmt.Sprintf("%d", opt_val1092))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		_dollar_dollar := msg
		fields1094 := _dollar_dollar.GetArgs()
		unwrapped_fields1095 := fields1094
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1095) == 0) {
			p.newline()
			for i1097, elem1096 := range unwrapped_fields1095 {
				if (i1097 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1096)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1103 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1103 != nil {
		p.write(*flat1103)
		return nil
	} else {
		_dollar_dollar := msg
		fields1099 := _dollar_dollar.GetArgs()
		unwrapped_fields1100 := fields1099
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1100) == 0) {
			p.newline()
			for i1102, elem1101 := range unwrapped_fields1100 {
				if (i1102 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1101)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1106 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1106 != nil {
		p.write(*flat1106)
		return nil
	} else {
		_dollar_dollar := msg
		fields1104 := _dollar_dollar.GetArg()
		unwrapped_fields1105 := fields1104
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1105)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		fields1107 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1108 := fields1107
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1109 := unwrapped_fields1108[0].(string)
		p.pretty_name(field1109)
		p.newline()
		field1110 := unwrapped_fields1108[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1110)
		p.newline()
		field1111 := unwrapped_fields1108[2].([]*pb.Term)
		p.pretty_terms(field1111)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		fields1113 := msg
		p.write(":")
		p.write(fields1113)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		fields1115 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1115) == 0) {
			p.newline()
			for i1117, elem1116 := range fields1115 {
				if (i1117 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1116)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		_dollar_dollar := msg
		fields1119 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1120 := fields1119
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1121 := unwrapped_fields1120[0].(*pb.RelationId)
		p.pretty_relation_id(field1121)
		field1122 := unwrapped_fields1120[1].([]*pb.Term)
		if !(len(field1122) == 0) {
			p.newline()
			for i1124, elem1123 := range field1122 {
				if (i1124 > 0) {
					p.newline()
				}
				p.pretty_term(elem1123)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1132 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_dollar_dollar := msg
		fields1126 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1127 := fields1126
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1128 := unwrapped_fields1127[0].(string)
		p.pretty_name(field1128)
		field1129 := unwrapped_fields1127[1].([]*pb.Term)
		if !(len(field1129) == 0) {
			p.newline()
			for i1131, elem1130 := range field1129 {
				if (i1131 > 0) {
					p.newline()
				}
				p.pretty_term(elem1130)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1148 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1148 != nil {
		p.write(*flat1148)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1675 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1675 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1147 := _t1675
		if guard_result1147 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1676 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1676 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1146 := _t1676
			if guard_result1146 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1677 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1677 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1145 := _t1677
				if guard_result1145 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1678 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1678 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1144 := _t1678
					if guard_result1144 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1679 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1679 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1143 := _t1679
						if guard_result1143 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1680 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1680 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1142 := _t1680
							if guard_result1142 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1681 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1681 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1141 := _t1681
								if guard_result1141 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1682 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1682 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1140 := _t1682
									if guard_result1140 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1683 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1683 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1139 := _t1683
										if guard_result1139 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1133 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1134 := fields1133
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1135 := unwrapped_fields1134[0].(string)
											p.pretty_name(field1135)
											field1136 := unwrapped_fields1134[1].([]*pb.RelTerm)
											if !(len(field1136) == 0) {
												p.newline()
												for i1138, elem1137 := range field1136 {
													if (i1138 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1137)
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
	flat1153 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1684 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1684 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1149 := _t1684
		unwrapped_fields1150 := fields1149
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1151 := unwrapped_fields1150[0].(*pb.Term)
		p.pretty_term(field1151)
		p.newline()
		field1152 := unwrapped_fields1150[1].(*pb.Term)
		p.pretty_term(field1152)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1158 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1685 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1685 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1154 := _t1685
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1156 := unwrapped_fields1155[0].(*pb.Term)
		p.pretty_term(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].(*pb.Term)
		p.pretty_term(field1157)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1163 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1163 != nil {
		p.write(*flat1163)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1686 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1686 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1159 := _t1686
		unwrapped_fields1160 := fields1159
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1161 := unwrapped_fields1160[0].(*pb.Term)
		p.pretty_term(field1161)
		p.newline()
		field1162 := unwrapped_fields1160[1].(*pb.Term)
		p.pretty_term(field1162)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1687 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1687 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1164 := _t1687
		unwrapped_fields1165 := fields1164
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1166 := unwrapped_fields1165[0].(*pb.Term)
		p.pretty_term(field1166)
		p.newline()
		field1167 := unwrapped_fields1165[1].(*pb.Term)
		p.pretty_term(field1167)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1688 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1688 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1169 := _t1688
		unwrapped_fields1170 := fields1169
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1171 := unwrapped_fields1170[0].(*pb.Term)
		p.pretty_term(field1171)
		p.newline()
		field1172 := unwrapped_fields1170[1].(*pb.Term)
		p.pretty_term(field1172)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1689 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1689 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1174 := _t1689
		unwrapped_fields1175 := fields1174
		p.write("(")
		p.write("+")
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

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1185 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1185 != nil {
		p.write(*flat1185)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1690 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1690 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1180 := _t1690
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(*pb.Term)
		p.pretty_term(field1182)
		p.newline()
		field1183 := unwrapped_fields1181[1].(*pb.Term)
		p.pretty_term(field1183)
		p.newline()
		field1184 := unwrapped_fields1181[2].(*pb.Term)
		p.pretty_term(field1184)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1191 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1191 != nil {
		p.write(*flat1191)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1691 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1691 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1186 := _t1691
		unwrapped_fields1187 := fields1186
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1188 := unwrapped_fields1187[0].(*pb.Term)
		p.pretty_term(field1188)
		p.newline()
		field1189 := unwrapped_fields1187[1].(*pb.Term)
		p.pretty_term(field1189)
		p.newline()
		field1190 := unwrapped_fields1187[2].(*pb.Term)
		p.pretty_term(field1190)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1197 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1197 != nil {
		p.write(*flat1197)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1692 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1692 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1192 := _t1692
		unwrapped_fields1193 := fields1192
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1194 := unwrapped_fields1193[0].(*pb.Term)
		p.pretty_term(field1194)
		p.newline()
		field1195 := unwrapped_fields1193[1].(*pb.Term)
		p.pretty_term(field1195)
		p.newline()
		field1196 := unwrapped_fields1193[2].(*pb.Term)
		p.pretty_term(field1196)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1693 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1200 := _t1693
		if deconstruct_result1200 != nil {
			unwrapped1201 := deconstruct_result1200
			p.pretty_specialized_value(unwrapped1201)
		} else {
			_dollar_dollar := msg
			var _t1694 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1694 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1198 := _t1694
			if deconstruct_result1198 != nil {
				unwrapped1199 := deconstruct_result1198
				p.pretty_term(unwrapped1199)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1204 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		fields1203 := msg
		p.write("#")
		p.pretty_raw_value(fields1203)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		_dollar_dollar := msg
		fields1205 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1206 := fields1205
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1207 := unwrapped_fields1206[0].(string)
		p.pretty_name(field1207)
		field1208 := unwrapped_fields1206[1].([]*pb.RelTerm)
		if !(len(field1208) == 0) {
			p.newline()
			for i1210, elem1209 := range field1208 {
				if (i1210 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1209)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1216 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1216 != nil {
		p.write(*flat1216)
		return nil
	} else {
		_dollar_dollar := msg
		fields1212 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1213 := fields1212
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1214 := unwrapped_fields1213[0].(*pb.Term)
		p.pretty_term(field1214)
		p.newline()
		field1215 := unwrapped_fields1213[1].(*pb.Term)
		p.pretty_term(field1215)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		fields1217 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1217) == 0) {
			p.newline()
			for i1219, elem1218 := range fields1217 {
				if (i1219 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1218)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		fields1221 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1222 := fields1221
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1223 := unwrapped_fields1222[0].(string)
		p.pretty_name(field1223)
		field1224 := unwrapped_fields1222[1].([]*pb.Value)
		if !(len(field1224) == 0) {
			p.newline()
			for i1226, elem1225 := range field1224 {
				if (i1226 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1225)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		_dollar_dollar := msg
		fields1228 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1230 := unwrapped_fields1229[0].([]*pb.RelationId)
		if !(len(field1230) == 0) {
			p.newline()
			for i1232, elem1231 := range field1230 {
				if (i1232 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1231)
			}
		}
		p.newline()
		field1233 := unwrapped_fields1229[1].(*pb.Script)
		p.pretty_script(field1233)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1239 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1239 != nil {
		p.write(*flat1239)
		return nil
	} else {
		_dollar_dollar := msg
		fields1235 := _dollar_dollar.GetConstructs()
		unwrapped_fields1236 := fields1235
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1236) == 0) {
			p.newline()
			for i1238, elem1237 := range unwrapped_fields1236 {
				if (i1238 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1237)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1695 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1695 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1242 := _t1695
		if deconstruct_result1242 != nil {
			unwrapped1243 := deconstruct_result1242
			p.pretty_loop(unwrapped1243)
		} else {
			_dollar_dollar := msg
			var _t1696 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1696 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1240 := _t1696
			if deconstruct_result1240 != nil {
				unwrapped1241 := deconstruct_result1240
				p.pretty_instruction(unwrapped1241)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		fields1245 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1246 := fields1245
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1247 := unwrapped_fields1246[0].([]*pb.Instruction)
		p.pretty_init(field1247)
		p.newline()
		field1248 := unwrapped_fields1246[1].(*pb.Script)
		p.pretty_script(field1248)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		fields1250 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1250) == 0) {
			p.newline()
			for i1252, elem1251 := range fields1250 {
				if (i1252 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1251)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1697 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1262 := _t1697
		if deconstruct_result1262 != nil {
			unwrapped1263 := deconstruct_result1262
			p.pretty_assign(unwrapped1263)
		} else {
			_dollar_dollar := msg
			var _t1698 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1698 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1260 := _t1698
			if deconstruct_result1260 != nil {
				unwrapped1261 := deconstruct_result1260
				p.pretty_upsert(unwrapped1261)
			} else {
				_dollar_dollar := msg
				var _t1699 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1699 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1258 := _t1699
				if deconstruct_result1258 != nil {
					unwrapped1259 := deconstruct_result1258
					p.pretty_break(unwrapped1259)
				} else {
					_dollar_dollar := msg
					var _t1700 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1700 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1256 := _t1700
					if deconstruct_result1256 != nil {
						unwrapped1257 := deconstruct_result1256
						p.pretty_monoid_def(unwrapped1257)
					} else {
						_dollar_dollar := msg
						var _t1701 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1701 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1254 := _t1701
						if deconstruct_result1254 != nil {
							unwrapped1255 := deconstruct_result1254
							p.pretty_monus_def(unwrapped1255)
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
	flat1271 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1271 != nil {
		p.write(*flat1271)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1702 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1702 = _dollar_dollar.GetAttrs()
		}
		fields1265 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1702}
		unwrapped_fields1266 := fields1265
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1267 := unwrapped_fields1266[0].(*pb.RelationId)
		p.pretty_relation_id(field1267)
		p.newline()
		field1268 := unwrapped_fields1266[1].(*pb.Abstraction)
		p.pretty_abstraction(field1268)
		field1269 := unwrapped_fields1266[2].([]*pb.Attribute)
		if field1269 != nil {
			p.newline()
			opt_val1270 := field1269
			p.pretty_attrs(opt_val1270)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1703 = _dollar_dollar.GetAttrs()
		}
		fields1272 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1703}
		unwrapped_fields1273 := fields1272
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1274 := unwrapped_fields1273[0].(*pb.RelationId)
		p.pretty_relation_id(field1274)
		p.newline()
		field1275 := unwrapped_fields1273[1].([]interface{})
		p.pretty_abstraction_with_arity(field1275)
		field1276 := unwrapped_fields1273[2].([]*pb.Attribute)
		if field1276 != nil {
			p.newline()
			opt_val1277 := field1276
			p.pretty_attrs(opt_val1277)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		_t1704 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1279 := []interface{}{_t1704, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.indent()
		field1281 := unwrapped_fields1280[0].([]interface{})
		p.pretty_bindings(field1281)
		p.newline()
		field1282 := unwrapped_fields1280[1].(*pb.Formula)
		p.pretty_formula(field1282)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1290 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1290 != nil {
		p.write(*flat1290)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1705 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1705 = _dollar_dollar.GetAttrs()
		}
		fields1284 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1705}
		unwrapped_fields1285 := fields1284
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1286 := unwrapped_fields1285[0].(*pb.RelationId)
		p.pretty_relation_id(field1286)
		p.newline()
		field1287 := unwrapped_fields1285[1].(*pb.Abstraction)
		p.pretty_abstraction(field1287)
		field1288 := unwrapped_fields1285[2].([]*pb.Attribute)
		if field1288 != nil {
			p.newline()
			opt_val1289 := field1288
			p.pretty_attrs(opt_val1289)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1298 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1298 != nil {
		p.write(*flat1298)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1706 = _dollar_dollar.GetAttrs()
		}
		fields1291 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1706}
		unwrapped_fields1292 := fields1291
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1293 := unwrapped_fields1292[0].(*pb.Monoid)
		p.pretty_monoid(field1293)
		p.newline()
		field1294 := unwrapped_fields1292[1].(*pb.RelationId)
		p.pretty_relation_id(field1294)
		p.newline()
		field1295 := unwrapped_fields1292[2].([]interface{})
		p.pretty_abstraction_with_arity(field1295)
		field1296 := unwrapped_fields1292[3].([]*pb.Attribute)
		if field1296 != nil {
			p.newline()
			opt_val1297 := field1296
			p.pretty_attrs(opt_val1297)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1707 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1305 := _t1707
		if deconstruct_result1305 != nil {
			unwrapped1306 := deconstruct_result1305
			p.pretty_or_monoid(unwrapped1306)
		} else {
			_dollar_dollar := msg
			var _t1708 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1708 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1303 := _t1708
			if deconstruct_result1303 != nil {
				unwrapped1304 := deconstruct_result1303
				p.pretty_min_monoid(unwrapped1304)
			} else {
				_dollar_dollar := msg
				var _t1709 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1709 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1301 := _t1709
				if deconstruct_result1301 != nil {
					unwrapped1302 := deconstruct_result1301
					p.pretty_max_monoid(unwrapped1302)
				} else {
					_dollar_dollar := msg
					var _t1710 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1710 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1299 := _t1710
					if deconstruct_result1299 != nil {
						unwrapped1300 := deconstruct_result1299
						p.pretty_sum_monoid(unwrapped1300)
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
	fields1308 := msg
	_ = fields1308
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1311 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		_dollar_dollar := msg
		fields1309 := _dollar_dollar.GetType()
		unwrapped_fields1310 := fields1309
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1310)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1314 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1314 != nil {
		p.write(*flat1314)
		return nil
	} else {
		_dollar_dollar := msg
		fields1312 := _dollar_dollar.GetType()
		unwrapped_fields1313 := fields1312
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1313)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1317 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		_dollar_dollar := msg
		fields1315 := _dollar_dollar.GetType()
		unwrapped_fields1316 := fields1315
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1316)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1325 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1325 != nil {
		p.write(*flat1325)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1711 = _dollar_dollar.GetAttrs()
		}
		fields1318 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1711}
		unwrapped_fields1319 := fields1318
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1320 := unwrapped_fields1319[0].(*pb.Monoid)
		p.pretty_monoid(field1320)
		p.newline()
		field1321 := unwrapped_fields1319[1].(*pb.RelationId)
		p.pretty_relation_id(field1321)
		p.newline()
		field1322 := unwrapped_fields1319[2].([]interface{})
		p.pretty_abstraction_with_arity(field1322)
		field1323 := unwrapped_fields1319[3].([]*pb.Attribute)
		if field1323 != nil {
			p.newline()
			opt_val1324 := field1323
			p.pretty_attrs(opt_val1324)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1332 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1332 != nil {
		p.write(*flat1332)
		return nil
	} else {
		_dollar_dollar := msg
		fields1326 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1327 := fields1326
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1328 := unwrapped_fields1327[0].(*pb.RelationId)
		p.pretty_relation_id(field1328)
		p.newline()
		field1329 := unwrapped_fields1327[1].(*pb.Abstraction)
		p.pretty_abstraction(field1329)
		p.newline()
		field1330 := unwrapped_fields1327[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1330)
		p.newline()
		field1331 := unwrapped_fields1327[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1331)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1336 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1336 != nil {
		p.write(*flat1336)
		return nil
	} else {
		fields1333 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1333) == 0) {
			p.newline()
			for i1335, elem1334 := range fields1333 {
				if (i1335 > 0) {
					p.newline()
				}
				p.pretty_var(elem1334)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1340 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1340 != nil {
		p.write(*flat1340)
		return nil
	} else {
		fields1337 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1337) == 0) {
			p.newline()
			for i1339, elem1338 := range fields1337 {
				if (i1339 > 0) {
					p.newline()
				}
				p.pretty_var(elem1338)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1712 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1347 := _t1712
		if deconstruct_result1347 != nil {
			unwrapped1348 := deconstruct_result1347
			p.pretty_edb(unwrapped1348)
		} else {
			_dollar_dollar := msg
			var _t1713 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1713 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1345 := _t1713
			if deconstruct_result1345 != nil {
				unwrapped1346 := deconstruct_result1345
				p.pretty_betree_relation(unwrapped1346)
			} else {
				_dollar_dollar := msg
				var _t1714 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1714 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1343 := _t1714
				if deconstruct_result1343 != nil {
					unwrapped1344 := deconstruct_result1343
					p.pretty_csv_data(unwrapped1344)
				} else {
					_dollar_dollar := msg
					var _t1715 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1715 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1341 := _t1715
					if deconstruct_result1341 != nil {
						unwrapped1342 := deconstruct_result1341
						p.pretty_iceberg_data(unwrapped1342)
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
	flat1355 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1355 != nil {
		p.write(*flat1355)
		return nil
	} else {
		_dollar_dollar := msg
		fields1350 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1351 := fields1350
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1352 := unwrapped_fields1351[0].(*pb.RelationId)
		p.pretty_relation_id(field1352)
		p.newline()
		field1353 := unwrapped_fields1351[1].([]string)
		p.pretty_edb_path(field1353)
		p.newline()
		field1354 := unwrapped_fields1351[2].([]*pb.Type)
		p.pretty_edb_types(field1354)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1359 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1359 != nil {
		p.write(*flat1359)
		return nil
	} else {
		fields1356 := msg
		p.write("[")
		p.indent()
		for i1358, elem1357 := range fields1356 {
			if (i1358 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1357))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1363 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1363 != nil {
		p.write(*flat1363)
		return nil
	} else {
		fields1360 := msg
		p.write("[")
		p.indent()
		for i1362, elem1361 := range fields1360 {
			if (i1362 > 0) {
				p.newline()
			}
			p.pretty_type(elem1361)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1368 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		fields1364 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1365 := fields1364
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1366 := unwrapped_fields1365[0].(*pb.RelationId)
		p.pretty_relation_id(field1366)
		p.newline()
		field1367 := unwrapped_fields1365[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1367)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1374 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1374 != nil {
		p.write(*flat1374)
		return nil
	} else {
		_dollar_dollar := msg
		_t1716 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1369 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1716}
		unwrapped_fields1370 := fields1369
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1371 := unwrapped_fields1370[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1371)
		p.newline()
		field1372 := unwrapped_fields1370[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1372)
		p.newline()
		field1373 := unwrapped_fields1370[2].([][]interface{})
		p.pretty_config_dict(field1373)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1378 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1378 != nil {
		p.write(*flat1378)
		return nil
	} else {
		fields1375 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1375) == 0) {
			p.newline()
			for i1377, elem1376 := range fields1375 {
				if (i1377 > 0) {
					p.newline()
				}
				p.pretty_type(elem1376)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		fields1379 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1379) == 0) {
			p.newline()
			for i1381, elem1380 := range fields1379 {
				if (i1381 > 0) {
					p.newline()
				}
				p.pretty_type(elem1380)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1389 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		_dollar_dollar := msg
		fields1383 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1384 := fields1383
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1385 := unwrapped_fields1384[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1385)
		p.newline()
		field1386 := unwrapped_fields1384[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1386)
		p.newline()
		field1387 := unwrapped_fields1384[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1387)
		p.newline()
		field1388 := unwrapped_fields1384[3].(string)
		p.pretty_csv_asof(field1388)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1396 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1396 != nil {
		p.write(*flat1396)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1717 = _dollar_dollar.GetPaths()
		}
		var _t1718 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1718 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1390 := []interface{}{_t1717, _t1718}
		unwrapped_fields1391 := fields1390
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1392 := unwrapped_fields1391[0].([]string)
		if field1392 != nil {
			p.newline()
			opt_val1393 := field1392
			p.pretty_csv_locator_paths(opt_val1393)
		}
		field1394 := unwrapped_fields1391[1].(*string)
		if field1394 != nil {
			p.newline()
			opt_val1395 := *field1394
			p.pretty_csv_locator_inline_data(opt_val1395)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		fields1397 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1397) == 0) {
			p.newline()
			for i1399, elem1398 := range fields1397 {
				if (i1399 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1398))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1402 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1402 != nil {
		p.write(*flat1402)
		return nil
	} else {
		fields1401 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1401))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		_dollar_dollar := msg
		_t1719 := p.deconstruct_csv_config(_dollar_dollar)
		fields1403 := _t1719
		unwrapped_fields1404 := fields1403
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1404)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1409 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1409 != nil {
		p.write(*flat1409)
		return nil
	} else {
		fields1406 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1406) == 0) {
			p.newline()
			for i1408, elem1407 := range fields1406 {
				if (i1408 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1407)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1418 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1418 != nil {
		p.write(*flat1418)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1720 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1720 = _dollar_dollar.GetTargetId()
		}
		fields1410 := []interface{}{_dollar_dollar.GetColumnPath(), _t1720, _dollar_dollar.GetTypes()}
		unwrapped_fields1411 := fields1410
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1412 := unwrapped_fields1411[0].([]string)
		p.pretty_gnf_column_path(field1412)
		field1413 := unwrapped_fields1411[1].(*pb.RelationId)
		if field1413 != nil {
			p.newline()
			opt_val1414 := field1413
			p.pretty_relation_id(opt_val1414)
		}
		p.newline()
		p.write("[")
		field1415 := unwrapped_fields1411[2].([]*pb.Type)
		for i1417, elem1416 := range field1415 {
			if (i1417 > 0) {
				p.newline()
			}
			p.pretty_type(elem1416)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1425 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1721 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1423 := _t1721
		if deconstruct_result1423 != nil {
			unwrapped1424 := *deconstruct_result1423
			p.write(p.formatStringValue(unwrapped1424))
		} else {
			_dollar_dollar := msg
			var _t1722 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1722 = _dollar_dollar
			}
			deconstruct_result1419 := _t1722
			if deconstruct_result1419 != nil {
				unwrapped1420 := deconstruct_result1419
				p.write("[")
				p.indent()
				for i1422, elem1421 := range unwrapped1420 {
					if (i1422 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1421))
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
	flat1427 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1427 != nil {
		p.write(*flat1427)
		return nil
	} else {
		fields1426 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1426))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1438 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1438 != nil {
		p.write(*flat1438)
		return nil
	} else {
		_dollar_dollar := msg
		_t1723 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1724 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1428 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1723, _t1724, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1429 := fields1428
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1430 := unwrapped_fields1429[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1430)
		p.newline()
		field1431 := unwrapped_fields1429[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1431)
		p.newline()
		field1432 := unwrapped_fields1429[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1432)
		field1433 := unwrapped_fields1429[3].(*string)
		if field1433 != nil {
			p.newline()
			opt_val1434 := *field1433
			p.pretty_iceberg_from_snapshot(opt_val1434)
		}
		field1435 := unwrapped_fields1429[4].(*string)
		if field1435 != nil {
			p.newline()
			opt_val1436 := *field1435
			p.pretty_iceberg_to_snapshot(opt_val1436)
		}
		p.newline()
		field1437 := unwrapped_fields1429[5].(bool)
		p.pretty_boolean_value(field1437)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1444 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1444 != nil {
		p.write(*flat1444)
		return nil
	} else {
		_dollar_dollar := msg
		fields1439 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1440 := fields1439
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1441 := unwrapped_fields1440[0].(string)
		p.pretty_iceberg_locator_table_name(field1441)
		p.newline()
		field1442 := unwrapped_fields1440[1].([]string)
		p.pretty_iceberg_locator_namespace(field1442)
		p.newline()
		field1443 := unwrapped_fields1440[2].(string)
		p.pretty_iceberg_locator_warehouse(field1443)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1446 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1446 != nil {
		p.write(*flat1446)
		return nil
	} else {
		fields1445 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1445))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1450 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1450 != nil {
		p.write(*flat1450)
		return nil
	} else {
		fields1447 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1447) == 0) {
			p.newline()
			for i1449, elem1448 := range fields1447 {
				if (i1449 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1448))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1452 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1452 != nil {
		p.write(*flat1452)
		return nil
	} else {
		fields1451 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1451))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1460 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1460 != nil {
		p.write(*flat1460)
		return nil
	} else {
		_dollar_dollar := msg
		_t1725 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1453 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1725, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1454 := fields1453
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1455 := unwrapped_fields1454[0].(string)
		p.pretty_iceberg_catalog_uri(field1455)
		field1456 := unwrapped_fields1454[1].(*string)
		if field1456 != nil {
			p.newline()
			opt_val1457 := *field1456
			p.pretty_iceberg_catalog_config_scope(opt_val1457)
		}
		p.newline()
		field1458 := unwrapped_fields1454[2].([][]interface{})
		p.pretty_iceberg_properties(field1458)
		p.newline()
		field1459 := unwrapped_fields1454[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1459)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		fields1461 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1461))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		fields1463 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1463))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		fields1465 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1465) == 0) {
			p.newline()
			for i1467, elem1466 := range fields1465 {
				if (i1467 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1466)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1473 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1473 != nil {
		p.write(*flat1473)
		return nil
	} else {
		_dollar_dollar := msg
		fields1469 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1470 := fields1469
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1471 := unwrapped_fields1470[0].(string)
		p.write(p.formatStringValue(field1471))
		p.newline()
		field1472 := unwrapped_fields1470[1].(string)
		p.write(p.formatStringValue(field1472))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1477 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1477 != nil {
		p.write(*flat1477)
		return nil
	} else {
		fields1474 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1474) == 0) {
			p.newline()
			for i1476, elem1475 := range fields1474 {
				if (i1476 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1475)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1482 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		_dollar_dollar := msg
		_t1726 := p.mask_secret_value(_dollar_dollar)
		fields1478 := []interface{}{_dollar_dollar[0].(string), _t1726}
		unwrapped_fields1479 := fields1478
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1480 := unwrapped_fields1479[0].(string)
		p.write(p.formatStringValue(field1480))
		p.newline()
		field1481 := unwrapped_fields1479[1].(string)
		p.write(p.formatStringValue(field1481))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		fields1483 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1483))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1486 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1486 != nil {
		p.write(*flat1486)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1485))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1489 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1489 != nil {
		p.write(*flat1489)
		return nil
	} else {
		_dollar_dollar := msg
		fields1487 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1488 := fields1487
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1488)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1494 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1494 != nil {
		p.write(*flat1494)
		return nil
	} else {
		_dollar_dollar := msg
		fields1490 := _dollar_dollar.GetRelations()
		unwrapped_fields1491 := fields1490
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1491) == 0) {
			p.newline()
			for i1493, elem1492 := range unwrapped_fields1491 {
				if (i1493 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1492)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1501 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1501 != nil {
		p.write(*flat1501)
		return nil
	} else {
		_dollar_dollar := msg
		fields1495 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1496 := fields1495
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1497 := unwrapped_fields1496[0].([]string)
		p.pretty_edb_path(field1497)
		field1498 := unwrapped_fields1496[1].([]*pb.SnapshotMapping)
		if !(len(field1498) == 0) {
			p.newline()
			for i1500, elem1499 := range field1498 {
				if (i1500 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1499)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1506 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1506 != nil {
		p.write(*flat1506)
		return nil
	} else {
		_dollar_dollar := msg
		fields1502 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1503 := fields1502
		field1504 := unwrapped_fields1503[0].([]string)
		p.pretty_edb_path(field1504)
		p.write(" ")
		field1505 := unwrapped_fields1503[1].(*pb.RelationId)
		p.pretty_relation_id(field1505)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1510 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1510 != nil {
		p.write(*flat1510)
		return nil
	} else {
		fields1507 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1507) == 0) {
			p.newline()
			for i1509, elem1508 := range fields1507 {
				if (i1509 > 0) {
					p.newline()
				}
				p.pretty_read(elem1508)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1727 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1519 := _t1727
		if deconstruct_result1519 != nil {
			unwrapped1520 := deconstruct_result1519
			p.pretty_demand(unwrapped1520)
		} else {
			_dollar_dollar := msg
			var _t1728 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1728 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1517 := _t1728
			if deconstruct_result1517 != nil {
				unwrapped1518 := deconstruct_result1517
				p.pretty_output(unwrapped1518)
			} else {
				_dollar_dollar := msg
				var _t1729 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1729 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1515 := _t1729
				if deconstruct_result1515 != nil {
					unwrapped1516 := deconstruct_result1515
					p.pretty_what_if(unwrapped1516)
				} else {
					_dollar_dollar := msg
					var _t1730 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1730 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1513 := _t1730
					if deconstruct_result1513 != nil {
						unwrapped1514 := deconstruct_result1513
						p.pretty_abort(unwrapped1514)
					} else {
						_dollar_dollar := msg
						var _t1731 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1731 = _dollar_dollar.GetExport()
						}
						deconstruct_result1511 := _t1731
						if deconstruct_result1511 != nil {
							unwrapped1512 := deconstruct_result1511
							p.pretty_export(unwrapped1512)
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
	flat1524 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1524 != nil {
		p.write(*flat1524)
		return nil
	} else {
		_dollar_dollar := msg
		fields1522 := _dollar_dollar.GetRelationId()
		unwrapped_fields1523 := fields1522
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1523)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1529 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1529 != nil {
		p.write(*flat1529)
		return nil
	} else {
		_dollar_dollar := msg
		fields1525 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1526 := fields1525
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1527 := unwrapped_fields1526[0].(string)
		p.pretty_name(field1527)
		p.newline()
		field1528 := unwrapped_fields1526[1].(*pb.RelationId)
		p.pretty_relation_id(field1528)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1534 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1534 != nil {
		p.write(*flat1534)
		return nil
	} else {
		_dollar_dollar := msg
		fields1530 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1531 := fields1530
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1532 := unwrapped_fields1531[0].(string)
		p.pretty_name(field1532)
		p.newline()
		field1533 := unwrapped_fields1531[1].(*pb.Epoch)
		p.pretty_epoch(field1533)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1540 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1540 != nil {
		p.write(*flat1540)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1732 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1732 = ptr(_dollar_dollar.GetName())
		}
		fields1535 := []interface{}{_t1732, _dollar_dollar.GetRelationId()}
		unwrapped_fields1536 := fields1535
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1537 := unwrapped_fields1536[0].(*string)
		if field1537 != nil {
			p.newline()
			opt_val1538 := *field1537
			p.pretty_name(opt_val1538)
		}
		p.newline()
		field1539 := unwrapped_fields1536[1].(*pb.RelationId)
		p.pretty_relation_id(field1539)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1545 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1545 != nil {
		p.write(*flat1545)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1733 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1733 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1543 := _t1733
		if deconstruct_result1543 != nil {
			unwrapped1544 := deconstruct_result1543
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1544)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1734 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1734 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1541 := _t1734
			if deconstruct_result1541 != nil {
				unwrapped1542 := deconstruct_result1541
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1542)
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
	flat1556 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1556 != nil {
		p.write(*flat1556)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1735 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1735 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1551 := _t1735
		if deconstruct_result1551 != nil {
			unwrapped1552 := deconstruct_result1551
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1553 := unwrapped1552[0].(string)
			p.pretty_export_csv_path(field1553)
			p.newline()
			field1554 := unwrapped1552[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1554)
			p.newline()
			field1555 := unwrapped1552[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1555)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1736 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1737 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1736 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1737}
			}
			deconstruct_result1546 := _t1736
			if deconstruct_result1546 != nil {
				unwrapped1547 := deconstruct_result1546
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1548 := unwrapped1547[0].(string)
				p.pretty_export_csv_path(field1548)
				p.newline()
				field1549 := unwrapped1547[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1549)
				p.newline()
				field1550 := unwrapped1547[2].([][]interface{})
				p.pretty_config_dict(field1550)
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
	flat1558 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1558 != nil {
		p.write(*flat1558)
		return nil
	} else {
		fields1557 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1557))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1565 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1565 != nil {
		p.write(*flat1565)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1738 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1738 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1561 := _t1738
		if deconstruct_result1561 != nil {
			unwrapped1562 := deconstruct_result1561
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1562) == 0) {
				p.newline()
				for i1564, elem1563 := range unwrapped1562 {
					if (i1564 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1563)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1739 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1739 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1559 := _t1739
			if deconstruct_result1559 != nil {
				unwrapped1560 := deconstruct_result1559
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1560)
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
	flat1570 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1570 != nil {
		p.write(*flat1570)
		return nil
	} else {
		_dollar_dollar := msg
		fields1566 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1567 := fields1566
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1568 := unwrapped_fields1567[0].(string)
		p.write(p.formatStringValue(field1568))
		p.newline()
		field1569 := unwrapped_fields1567[1].(*pb.RelationId)
		p.pretty_relation_id(field1569)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1574 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1574 != nil {
		p.write(*flat1574)
		return nil
	} else {
		fields1571 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1571) == 0) {
			p.newline()
			for i1573, elem1572 := range fields1571 {
				if (i1573 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1572)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1584 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1584 != nil {
		p.write(*flat1584)
		return nil
	} else {
		_dollar_dollar := msg
		_t1740 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1575 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1740}
		unwrapped_fields1576 := fields1575
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1577 := unwrapped_fields1576[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1577)
		p.newline()
		field1578 := unwrapped_fields1576[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1578)
		p.newline()
		field1579 := unwrapped_fields1576[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1579)
		p.newline()
		field1580 := unwrapped_fields1576[3].([]*pb.ExportColumn)
		p.pretty_export_iceberg_columns(field1580)
		p.newline()
		field1581 := unwrapped_fields1576[4].([][]interface{})
		p.pretty_iceberg_table_properties(field1581)
		field1582 := unwrapped_fields1576[5].([][]interface{})
		if field1582 != nil {
			p.newline()
			opt_val1583 := field1582
			p.pretty_config_dict(opt_val1583)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1586 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1586 != nil {
		p.write(*flat1586)
		return nil
	} else {
		fields1585 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1585)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_columns(msg []*pb.ExportColumn) interface{} {
	flat1590 := p.tryFlat(msg, func() { p.pretty_export_iceberg_columns(msg) })
	if flat1590 != nil {
		p.write(*flat1590)
		return nil
	} else {
		fields1587 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1587) == 0) {
			p.newline()
			for i1589, elem1588 := range fields1587 {
				if (i1589 > 0) {
					p.newline()
				}
				p.pretty_export_iceberg_column(elem1588)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column(msg *pb.ExportColumn) interface{} {
	flat1595 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column(msg) })
	if flat1595 != nil {
		p.write(*flat1595)
		return nil
	} else {
		_dollar_dollar := msg
		fields1591 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetNullable()}
		unwrapped_fields1592 := fields1591
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1593 := unwrapped_fields1592[0].(string)
		p.write(p.formatStringValue(field1593))
		p.newline()
		field1594 := unwrapped_fields1592[1].(bool)
		p.pretty_boolean_value(field1594)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1599 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1599 != nil {
		p.write(*flat1599)
		return nil
	} else {
		fields1596 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1596) == 0) {
			p.newline()
			for i1598, elem1597 := range fields1596 {
				if (i1598 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1597)
			}
		}
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
		_t1786 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1786)
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
	case []*pb.ExportColumn:
		p.pretty_export_iceberg_columns(m)
	case *pb.ExportColumn:
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
