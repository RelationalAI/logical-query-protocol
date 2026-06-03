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
	_t1759 := &pb.Value{}
	_t1759.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1759
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1760 := &pb.Value{}
	_t1760.Value = &pb.Value_IntValue{IntValue: v}
	return _t1760
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1761 := &pb.Value{}
	_t1761.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1761
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1762 := &pb.Value{}
	_t1762.Value = &pb.Value_StringValue{StringValue: v}
	return _t1762
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1763 := &pb.Value{}
	_t1763.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1763
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1764 := &pb.Value{}
	_t1764.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1764
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1765 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1765})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1766 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1766})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1767 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1767})
			}
		}
	}
	_t1768 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1768})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1769 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1769})
	_t1770 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1770})
	if msg.GetNewLine() != "" {
		_t1771 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1771})
	}
	_t1772 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1772})
	_t1773 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1773})
	_t1774 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1774})
	if msg.GetComment() != "" {
		_t1775 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1775})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1776 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1776})
	}
	_t1777 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1777})
	_t1778 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1778})
	_t1779 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1779})
	if msg.GetPartitionSizeMb() != 0 {
		_t1780 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1780})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1781 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1781})
	_t1782 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1782})
	_t1783 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1783})
	_t1784 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1784})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1785 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1785})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1786 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1786})
		}
	}
	_t1787 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1787})
	_t1788 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1788})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1789 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1789})
	}
	if msg.Compression != nil {
		_t1790 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1790})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1791 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1791})
	}
	if msg.SyntaxMissingString != nil {
		_t1792 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1792})
	}
	if msg.SyntaxDelim != nil {
		_t1793 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1793})
	}
	if msg.SyntaxQuotechar != nil {
		_t1794 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1794})
	}
	if msg.SyntaxEscapechar != nil {
		_t1795 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1795})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1796 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1796
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1797 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1797
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1798 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1798
	return nil
}

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1799 interface{}
	if !(hasProtoField(msg, "target")) {
		return msg.GetColumns()
	}
	_ = _t1799
	return nil
}

func (p *PrettyPrinter) deconstruct_csv_data_target_optional(msg *pb.CSVData) *pb.CSVTarget {
	var _t1800 interface{}
	if hasProtoField(msg, "target") {
		return msg.GetTarget()
	}
	_ = _t1800
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1801 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1801})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1802 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1802})
	}
	if msg.GetCompression() != "" {
		_t1803 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1803})
	}
	var _t1804 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1804
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1805 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1805
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
	flat816 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat816 != nil {
		p.write(*flat816)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1614 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1614 = _dollar_dollar.GetConfigure()
		}
		var _t1615 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1615 = _dollar_dollar.GetSync()
		}
		fields807 := []interface{}{_t1614, _t1615, _dollar_dollar.GetEpochs()}
		unwrapped_fields808 := fields807
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field809 := unwrapped_fields808[0].(*pb.Configure)
		if field809 != nil {
			p.newline()
			opt_val810 := field809
			p.pretty_configure(opt_val810)
		}
		field811 := unwrapped_fields808[1].(*pb.Sync)
		if field811 != nil {
			p.newline()
			opt_val812 := field811
			p.pretty_sync(opt_val812)
		}
		field813 := unwrapped_fields808[2].([]*pb.Epoch)
		if !(len(field813) == 0) {
			p.newline()
			for i815, elem814 := range field813 {
				if (i815 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem814)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat819 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat819 != nil {
		p.write(*flat819)
		return nil
	} else {
		_dollar_dollar := msg
		_t1616 := p.deconstruct_configure(_dollar_dollar)
		fields817 := _t1616
		unwrapped_fields818 := fields817
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields818)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat823 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat823 != nil {
		p.write(*flat823)
		return nil
	} else {
		fields820 := msg
		p.write("{")
		p.indent()
		if !(len(fields820) == 0) {
			p.newline()
			for i822, elem821 := range fields820 {
				if (i822 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem821)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat828 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat828 != nil {
		p.write(*flat828)
		return nil
	} else {
		_dollar_dollar := msg
		fields824 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields825 := fields824
		p.write(":")
		field826 := unwrapped_fields825[0].(string)
		p.write(field826)
		p.write(" ")
		field827 := unwrapped_fields825[1].(*pb.Value)
		p.pretty_raw_value(field827)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat854 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1617 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1617 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result852 := _t1617
		if deconstruct_result852 != nil {
			unwrapped853 := deconstruct_result852
			p.pretty_raw_date(unwrapped853)
		} else {
			_dollar_dollar := msg
			var _t1618 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1618 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result850 := _t1618
			if deconstruct_result850 != nil {
				unwrapped851 := deconstruct_result850
				p.pretty_raw_datetime(unwrapped851)
			} else {
				_dollar_dollar := msg
				var _t1619 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1619 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result848 := _t1619
				if deconstruct_result848 != nil {
					unwrapped849 := *deconstruct_result848
					p.write(p.formatStringValue(unwrapped849))
				} else {
					_dollar_dollar := msg
					var _t1620 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1620 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result846 := _t1620
					if deconstruct_result846 != nil {
						unwrapped847 := *deconstruct_result846
						p.write(fmt.Sprintf("%di32", unwrapped847))
					} else {
						_dollar_dollar := msg
						var _t1621 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1621 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result844 := _t1621
						if deconstruct_result844 != nil {
							unwrapped845 := *deconstruct_result844
							p.write(fmt.Sprintf("%d", unwrapped845))
						} else {
							_dollar_dollar := msg
							var _t1622 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1622 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result842 := _t1622
							if deconstruct_result842 != nil {
								unwrapped843 := *deconstruct_result842
								p.write(formatFloat32(unwrapped843))
							} else {
								_dollar_dollar := msg
								var _t1623 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1623 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result840 := _t1623
								if deconstruct_result840 != nil {
									unwrapped841 := *deconstruct_result840
									p.write(formatFloat64(unwrapped841))
								} else {
									_dollar_dollar := msg
									var _t1624 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1624 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result838 := _t1624
									if deconstruct_result838 != nil {
										unwrapped839 := *deconstruct_result838
										p.write(fmt.Sprintf("%du32", unwrapped839))
									} else {
										_dollar_dollar := msg
										var _t1625 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1625 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result836 := _t1625
										if deconstruct_result836 != nil {
											unwrapped837 := deconstruct_result836
											p.write(p.formatUint128(unwrapped837))
										} else {
											_dollar_dollar := msg
											var _t1626 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1626 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result834 := _t1626
											if deconstruct_result834 != nil {
												unwrapped835 := deconstruct_result834
												p.write(p.formatInt128(unwrapped835))
											} else {
												_dollar_dollar := msg
												var _t1627 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1627 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result832 := _t1627
												if deconstruct_result832 != nil {
													unwrapped833 := deconstruct_result832
													p.write(p.formatDecimal(unwrapped833))
												} else {
													_dollar_dollar := msg
													var _t1628 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1628 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result830 := _t1628
													if deconstruct_result830 != nil {
														unwrapped831 := *deconstruct_result830
														p.pretty_boolean_value(unwrapped831)
													} else {
														fields829 := msg
														_ = fields829
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
	flat860 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat860 != nil {
		p.write(*flat860)
		return nil
	} else {
		_dollar_dollar := msg
		fields855 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields856 := fields855
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field857 := unwrapped_fields856[0].(int64)
		p.write(fmt.Sprintf("%d", field857))
		p.newline()
		field858 := unwrapped_fields856[1].(int64)
		p.write(fmt.Sprintf("%d", field858))
		p.newline()
		field859 := unwrapped_fields856[2].(int64)
		p.write(fmt.Sprintf("%d", field859))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		fields861 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields862 := fields861
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field863 := unwrapped_fields862[0].(int64)
		p.write(fmt.Sprintf("%d", field863))
		p.newline()
		field864 := unwrapped_fields862[1].(int64)
		p.write(fmt.Sprintf("%d", field864))
		p.newline()
		field865 := unwrapped_fields862[2].(int64)
		p.write(fmt.Sprintf("%d", field865))
		p.newline()
		field866 := unwrapped_fields862[3].(int64)
		p.write(fmt.Sprintf("%d", field866))
		p.newline()
		field867 := unwrapped_fields862[4].(int64)
		p.write(fmt.Sprintf("%d", field867))
		p.newline()
		field868 := unwrapped_fields862[5].(int64)
		p.write(fmt.Sprintf("%d", field868))
		field869 := unwrapped_fields862[6].(*int64)
		if field869 != nil {
			p.newline()
			opt_val870 := *field869
			p.write(fmt.Sprintf("%d", opt_val870))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1629 []interface{}
	if _dollar_dollar {
		_t1629 = []interface{}{}
	}
	deconstruct_result874 := _t1629
	if deconstruct_result874 != nil {
		unwrapped875 := deconstruct_result874
		_ = unwrapped875
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1630 []interface{}
		if !(_dollar_dollar) {
			_t1630 = []interface{}{}
		}
		deconstruct_result872 := _t1630
		if deconstruct_result872 != nil {
			unwrapped873 := deconstruct_result872
			_ = unwrapped873
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat880 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat880 != nil {
		p.write(*flat880)
		return nil
	} else {
		_dollar_dollar := msg
		fields876 := _dollar_dollar.GetFragments()
		unwrapped_fields877 := fields876
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields877) == 0) {
			p.newline()
			for i879, elem878 := range unwrapped_fields877 {
				if (i879 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem878)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat883 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat883 != nil {
		p.write(*flat883)
		return nil
	} else {
		_dollar_dollar := msg
		fields881 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields882 := fields881
		p.write(":")
		p.write(unwrapped_fields882)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat890 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat890 != nil {
		p.write(*flat890)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1631 = _dollar_dollar.GetWrites()
		}
		var _t1632 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1632 = _dollar_dollar.GetReads()
		}
		fields884 := []interface{}{_t1631, _t1632}
		unwrapped_fields885 := fields884
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field886 := unwrapped_fields885[0].([]*pb.Write)
		if field886 != nil {
			p.newline()
			opt_val887 := field886
			p.pretty_epoch_writes(opt_val887)
		}
		field888 := unwrapped_fields885[1].([]*pb.Read)
		if field888 != nil {
			p.newline()
			opt_val889 := field888
			p.pretty_epoch_reads(opt_val889)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat894 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		fields891 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields891) == 0) {
			p.newline()
			for i893, elem892 := range fields891 {
				if (i893 > 0) {
					p.newline()
				}
				p.pretty_write(elem892)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat903 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat903 != nil {
		p.write(*flat903)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1633 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1633 = _dollar_dollar.GetDefine()
		}
		deconstruct_result901 := _t1633
		if deconstruct_result901 != nil {
			unwrapped902 := deconstruct_result901
			p.pretty_define(unwrapped902)
		} else {
			_dollar_dollar := msg
			var _t1634 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1634 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result899 := _t1634
			if deconstruct_result899 != nil {
				unwrapped900 := deconstruct_result899
				p.pretty_undefine(unwrapped900)
			} else {
				_dollar_dollar := msg
				var _t1635 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1635 = _dollar_dollar.GetContext()
				}
				deconstruct_result897 := _t1635
				if deconstruct_result897 != nil {
					unwrapped898 := deconstruct_result897
					p.pretty_context(unwrapped898)
				} else {
					_dollar_dollar := msg
					var _t1636 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1636 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result895 := _t1636
					if deconstruct_result895 != nil {
						unwrapped896 := deconstruct_result895
						p.pretty_snapshot(unwrapped896)
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
	flat906 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		fields904 := _dollar_dollar.GetFragment()
		unwrapped_fields905 := fields904
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields905)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat913 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat913 != nil {
		p.write(*flat913)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields907 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields908 := fields907
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field909 := unwrapped_fields908[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field909)
		field910 := unwrapped_fields908[1].([]*pb.Declaration)
		if !(len(field910) == 0) {
			p.newline()
			for i912, elem911 := range field910 {
				if (i912 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem911)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat915 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat915 != nil {
		p.write(*flat915)
		return nil
	} else {
		fields914 := msg
		p.pretty_fragment_id(fields914)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat924 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat924 != nil {
		p.write(*flat924)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1637 = _dollar_dollar.GetDef()
		}
		deconstruct_result922 := _t1637
		if deconstruct_result922 != nil {
			unwrapped923 := deconstruct_result922
			p.pretty_def(unwrapped923)
		} else {
			_dollar_dollar := msg
			var _t1638 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1638 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result920 := _t1638
			if deconstruct_result920 != nil {
				unwrapped921 := deconstruct_result920
				p.pretty_algorithm(unwrapped921)
			} else {
				_dollar_dollar := msg
				var _t1639 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1639 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result918 := _t1639
				if deconstruct_result918 != nil {
					unwrapped919 := deconstruct_result918
					p.pretty_constraint(unwrapped919)
				} else {
					_dollar_dollar := msg
					var _t1640 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1640 = _dollar_dollar.GetData()
					}
					deconstruct_result916 := _t1640
					if deconstruct_result916 != nil {
						unwrapped917 := deconstruct_result916
						p.pretty_data(unwrapped917)
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
	flat931 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat931 != nil {
		p.write(*flat931)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1641 = _dollar_dollar.GetAttrs()
		}
		fields925 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1641}
		unwrapped_fields926 := fields925
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field927 := unwrapped_fields926[0].(*pb.RelationId)
		p.pretty_relation_id(field927)
		p.newline()
		field928 := unwrapped_fields926[1].(*pb.Abstraction)
		p.pretty_abstraction(field928)
		field929 := unwrapped_fields926[2].([]*pb.Attribute)
		if field929 != nil {
			p.newline()
			opt_val930 := field929
			p.pretty_attrs(opt_val930)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat936 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat936 != nil {
		p.write(*flat936)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1642 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1643 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1642 = ptr(_t1643)
		}
		deconstruct_result934 := _t1642
		if deconstruct_result934 != nil {
			unwrapped935 := *deconstruct_result934
			p.write(":")
			p.write(unwrapped935)
		} else {
			_dollar_dollar := msg
			_t1644 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result932 := _t1644
			if deconstruct_result932 != nil {
				unwrapped933 := deconstruct_result932
				p.write(p.formatUint128(unwrapped933))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat941 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		_dollar_dollar := msg
		_t1645 := p.deconstruct_bindings(_dollar_dollar)
		fields937 := []interface{}{_t1645, _dollar_dollar.GetValue()}
		unwrapped_fields938 := fields937
		p.write("(")
		p.indent()
		field939 := unwrapped_fields938[0].([]interface{})
		p.pretty_bindings(field939)
		p.newline()
		field940 := unwrapped_fields938[1].(*pb.Formula)
		p.pretty_formula(field940)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat949 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1646 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1646 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields942 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1646}
		unwrapped_fields943 := fields942
		p.write("[")
		p.indent()
		field944 := unwrapped_fields943[0].([]*pb.Binding)
		for i946, elem945 := range field944 {
			if (i946 > 0) {
				p.newline()
			}
			p.pretty_binding(elem945)
		}
		field947 := unwrapped_fields943[1].([]*pb.Binding)
		if field947 != nil {
			p.newline()
			opt_val948 := field947
			p.pretty_value_bindings(opt_val948)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat954 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat954 != nil {
		p.write(*flat954)
		return nil
	} else {
		_dollar_dollar := msg
		fields950 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields951 := fields950
		field952 := unwrapped_fields951[0].(string)
		p.write(field952)
		p.write("::")
		field953 := unwrapped_fields951[1].(*pb.Type)
		p.pretty_type(field953)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat983 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1647 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result981 := _t1647
		if deconstruct_result981 != nil {
			unwrapped982 := deconstruct_result981
			p.pretty_unspecified_type(unwrapped982)
		} else {
			_dollar_dollar := msg
			var _t1648 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1648 = _dollar_dollar.GetStringType()
			}
			deconstruct_result979 := _t1648
			if deconstruct_result979 != nil {
				unwrapped980 := deconstruct_result979
				p.pretty_string_type(unwrapped980)
			} else {
				_dollar_dollar := msg
				var _t1649 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1649 = _dollar_dollar.GetIntType()
				}
				deconstruct_result977 := _t1649
				if deconstruct_result977 != nil {
					unwrapped978 := deconstruct_result977
					p.pretty_int_type(unwrapped978)
				} else {
					_dollar_dollar := msg
					var _t1650 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1650 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result975 := _t1650
					if deconstruct_result975 != nil {
						unwrapped976 := deconstruct_result975
						p.pretty_float_type(unwrapped976)
					} else {
						_dollar_dollar := msg
						var _t1651 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1651 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result973 := _t1651
						if deconstruct_result973 != nil {
							unwrapped974 := deconstruct_result973
							p.pretty_uint128_type(unwrapped974)
						} else {
							_dollar_dollar := msg
							var _t1652 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1652 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result971 := _t1652
							if deconstruct_result971 != nil {
								unwrapped972 := deconstruct_result971
								p.pretty_int128_type(unwrapped972)
							} else {
								_dollar_dollar := msg
								var _t1653 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1653 = _dollar_dollar.GetDateType()
								}
								deconstruct_result969 := _t1653
								if deconstruct_result969 != nil {
									unwrapped970 := deconstruct_result969
									p.pretty_date_type(unwrapped970)
								} else {
									_dollar_dollar := msg
									var _t1654 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1654 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result967 := _t1654
									if deconstruct_result967 != nil {
										unwrapped968 := deconstruct_result967
										p.pretty_datetime_type(unwrapped968)
									} else {
										_dollar_dollar := msg
										var _t1655 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1655 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result965 := _t1655
										if deconstruct_result965 != nil {
											unwrapped966 := deconstruct_result965
											p.pretty_missing_type(unwrapped966)
										} else {
											_dollar_dollar := msg
											var _t1656 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1656 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result963 := _t1656
											if deconstruct_result963 != nil {
												unwrapped964 := deconstruct_result963
												p.pretty_decimal_type(unwrapped964)
											} else {
												_dollar_dollar := msg
												var _t1657 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1657 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result961 := _t1657
												if deconstruct_result961 != nil {
													unwrapped962 := deconstruct_result961
													p.pretty_boolean_type(unwrapped962)
												} else {
													_dollar_dollar := msg
													var _t1658 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1658 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result959 := _t1658
													if deconstruct_result959 != nil {
														unwrapped960 := deconstruct_result959
														p.pretty_int32_type(unwrapped960)
													} else {
														_dollar_dollar := msg
														var _t1659 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1659 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result957 := _t1659
														if deconstruct_result957 != nil {
															unwrapped958 := deconstruct_result957
															p.pretty_float32_type(unwrapped958)
														} else {
															_dollar_dollar := msg
															var _t1660 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1660 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result955 := _t1660
															if deconstruct_result955 != nil {
																unwrapped956 := deconstruct_result955
																p.pretty_uint32_type(unwrapped956)
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
	fields984 := msg
	_ = fields984
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields985 := msg
	_ = fields985
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields986 := msg
	_ = fields986
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields987 := msg
	_ = fields987
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields988 := msg
	_ = fields988
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields989 := msg
	_ = fields989
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields990 := msg
	_ = fields990
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields991 := msg
	_ = fields991
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields992 := msg
	_ = fields992
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		_dollar_dollar := msg
		fields993 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields994 := fields993
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field995 := unwrapped_fields994[0].(int64)
		p.write(fmt.Sprintf("%d", field995))
		p.newline()
		field996 := unwrapped_fields994[1].(int64)
		p.write(fmt.Sprintf("%d", field996))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields998 := msg
	_ = fields998
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields999 := msg
	_ = fields999
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1000 := msg
	_ = fields1000
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1001 := msg
	_ = fields1001
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1005 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1005 != nil {
		p.write(*flat1005)
		return nil
	} else {
		fields1002 := msg
		p.write("|")
		if !(len(fields1002) == 0) {
			p.write(" ")
			for i1004, elem1003 := range fields1002 {
				if (i1004 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1003)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1661 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1030 := _t1661
		if deconstruct_result1030 != nil {
			unwrapped1031 := deconstruct_result1030
			p.pretty_true(unwrapped1031)
		} else {
			_dollar_dollar := msg
			var _t1662 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1662 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1028 := _t1662
			if deconstruct_result1028 != nil {
				unwrapped1029 := deconstruct_result1028
				p.pretty_false(unwrapped1029)
			} else {
				_dollar_dollar := msg
				var _t1663 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1663 = _dollar_dollar.GetExists()
				}
				deconstruct_result1026 := _t1663
				if deconstruct_result1026 != nil {
					unwrapped1027 := deconstruct_result1026
					p.pretty_exists(unwrapped1027)
				} else {
					_dollar_dollar := msg
					var _t1664 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1664 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1024 := _t1664
					if deconstruct_result1024 != nil {
						unwrapped1025 := deconstruct_result1024
						p.pretty_reduce(unwrapped1025)
					} else {
						_dollar_dollar := msg
						var _t1665 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1665 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1022 := _t1665
						if deconstruct_result1022 != nil {
							unwrapped1023 := deconstruct_result1022
							p.pretty_conjunction(unwrapped1023)
						} else {
							_dollar_dollar := msg
							var _t1666 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1666 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1020 := _t1666
							if deconstruct_result1020 != nil {
								unwrapped1021 := deconstruct_result1020
								p.pretty_disjunction(unwrapped1021)
							} else {
								_dollar_dollar := msg
								var _t1667 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1667 = _dollar_dollar.GetNot()
								}
								deconstruct_result1018 := _t1667
								if deconstruct_result1018 != nil {
									unwrapped1019 := deconstruct_result1018
									p.pretty_not(unwrapped1019)
								} else {
									_dollar_dollar := msg
									var _t1668 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1668 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1016 := _t1668
									if deconstruct_result1016 != nil {
										unwrapped1017 := deconstruct_result1016
										p.pretty_ffi(unwrapped1017)
									} else {
										_dollar_dollar := msg
										var _t1669 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1669 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1014 := _t1669
										if deconstruct_result1014 != nil {
											unwrapped1015 := deconstruct_result1014
											p.pretty_atom(unwrapped1015)
										} else {
											_dollar_dollar := msg
											var _t1670 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1670 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1012 := _t1670
											if deconstruct_result1012 != nil {
												unwrapped1013 := deconstruct_result1012
												p.pretty_pragma(unwrapped1013)
											} else {
												_dollar_dollar := msg
												var _t1671 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1671 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1010 := _t1671
												if deconstruct_result1010 != nil {
													unwrapped1011 := deconstruct_result1010
													p.pretty_primitive(unwrapped1011)
												} else {
													_dollar_dollar := msg
													var _t1672 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1672 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1008 := _t1672
													if deconstruct_result1008 != nil {
														unwrapped1009 := deconstruct_result1008
														p.pretty_rel_atom(unwrapped1009)
													} else {
														_dollar_dollar := msg
														var _t1673 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1673 = _dollar_dollar.GetCast()
														}
														deconstruct_result1006 := _t1673
														if deconstruct_result1006 != nil {
															unwrapped1007 := deconstruct_result1006
															p.pretty_cast(unwrapped1007)
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
	fields1033 := msg
	_ = fields1033
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1034 := msg
	_ = fields1034
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1039 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1039 != nil {
		p.write(*flat1039)
		return nil
	} else {
		_dollar_dollar := msg
		_t1674 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1035 := []interface{}{_t1674, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1036 := fields1035
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1037 := unwrapped_fields1036[0].([]interface{})
		p.pretty_bindings(field1037)
		p.newline()
		field1038 := unwrapped_fields1036[1].(*pb.Formula)
		p.pretty_formula(field1038)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1045 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1045 != nil {
		p.write(*flat1045)
		return nil
	} else {
		_dollar_dollar := msg
		fields1040 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1041 := fields1040
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1042 := unwrapped_fields1041[0].(*pb.Abstraction)
		p.pretty_abstraction(field1042)
		p.newline()
		field1043 := unwrapped_fields1041[1].(*pb.Abstraction)
		p.pretty_abstraction(field1043)
		p.newline()
		field1044 := unwrapped_fields1041[2].([]*pb.Term)
		p.pretty_terms(field1044)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1049 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		fields1046 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1046) == 0) {
			p.newline()
			for i1048, elem1047 := range fields1046 {
				if (i1048 > 0) {
					p.newline()
				}
				p.pretty_term(elem1047)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1054 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1675 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1675 = _dollar_dollar.GetVar()
		}
		deconstruct_result1052 := _t1675
		if deconstruct_result1052 != nil {
			unwrapped1053 := deconstruct_result1052
			p.pretty_var(unwrapped1053)
		} else {
			_dollar_dollar := msg
			var _t1676 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1676 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1050 := _t1676
			if deconstruct_result1050 != nil {
				unwrapped1051 := deconstruct_result1050
				p.pretty_value(unwrapped1051)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1057 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1057 != nil {
		p.write(*flat1057)
		return nil
	} else {
		_dollar_dollar := msg
		fields1055 := _dollar_dollar.GetName()
		unwrapped_fields1056 := fields1055
		p.write(unwrapped_fields1056)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1083 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1677 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1677 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1081 := _t1677
		if deconstruct_result1081 != nil {
			unwrapped1082 := deconstruct_result1081
			p.pretty_date(unwrapped1082)
		} else {
			_dollar_dollar := msg
			var _t1678 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1678 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1079 := _t1678
			if deconstruct_result1079 != nil {
				unwrapped1080 := deconstruct_result1079
				p.pretty_datetime(unwrapped1080)
			} else {
				_dollar_dollar := msg
				var _t1679 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1679 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1077 := _t1679
				if deconstruct_result1077 != nil {
					unwrapped1078 := *deconstruct_result1077
					p.write(p.formatStringValue(unwrapped1078))
				} else {
					_dollar_dollar := msg
					var _t1680 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1680 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1075 := _t1680
					if deconstruct_result1075 != nil {
						unwrapped1076 := *deconstruct_result1075
						p.write(fmt.Sprintf("%di32", unwrapped1076))
					} else {
						_dollar_dollar := msg
						var _t1681 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1681 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1073 := _t1681
						if deconstruct_result1073 != nil {
							unwrapped1074 := *deconstruct_result1073
							p.write(fmt.Sprintf("%d", unwrapped1074))
						} else {
							_dollar_dollar := msg
							var _t1682 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1682 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1071 := _t1682
							if deconstruct_result1071 != nil {
								unwrapped1072 := *deconstruct_result1071
								p.write(formatFloat32(unwrapped1072))
							} else {
								_dollar_dollar := msg
								var _t1683 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1683 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1069 := _t1683
								if deconstruct_result1069 != nil {
									unwrapped1070 := *deconstruct_result1069
									p.write(formatFloat64(unwrapped1070))
								} else {
									_dollar_dollar := msg
									var _t1684 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1684 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1067 := _t1684
									if deconstruct_result1067 != nil {
										unwrapped1068 := *deconstruct_result1067
										p.write(fmt.Sprintf("%du32", unwrapped1068))
									} else {
										_dollar_dollar := msg
										var _t1685 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1685 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1065 := _t1685
										if deconstruct_result1065 != nil {
											unwrapped1066 := deconstruct_result1065
											p.write(p.formatUint128(unwrapped1066))
										} else {
											_dollar_dollar := msg
											var _t1686 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1686 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1063 := _t1686
											if deconstruct_result1063 != nil {
												unwrapped1064 := deconstruct_result1063
												p.write(p.formatInt128(unwrapped1064))
											} else {
												_dollar_dollar := msg
												var _t1687 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1687 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1061 := _t1687
												if deconstruct_result1061 != nil {
													unwrapped1062 := deconstruct_result1061
													p.write(p.formatDecimal(unwrapped1062))
												} else {
													_dollar_dollar := msg
													var _t1688 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1688 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1059 := _t1688
													if deconstruct_result1059 != nil {
														unwrapped1060 := *deconstruct_result1059
														p.pretty_boolean_value(unwrapped1060)
													} else {
														fields1058 := msg
														_ = fields1058
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
	flat1089 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_dollar_dollar := msg
		fields1084 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1085 := fields1084
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1086 := unwrapped_fields1085[0].(int64)
		p.write(fmt.Sprintf("%d", field1086))
		p.newline()
		field1087 := unwrapped_fields1085[1].(int64)
		p.write(fmt.Sprintf("%d", field1087))
		p.newline()
		field1088 := unwrapped_fields1085[2].(int64)
		p.write(fmt.Sprintf("%d", field1088))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		_dollar_dollar := msg
		fields1090 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1092 := unwrapped_fields1091[0].(int64)
		p.write(fmt.Sprintf("%d", field1092))
		p.newline()
		field1093 := unwrapped_fields1091[1].(int64)
		p.write(fmt.Sprintf("%d", field1093))
		p.newline()
		field1094 := unwrapped_fields1091[2].(int64)
		p.write(fmt.Sprintf("%d", field1094))
		p.newline()
		field1095 := unwrapped_fields1091[3].(int64)
		p.write(fmt.Sprintf("%d", field1095))
		p.newline()
		field1096 := unwrapped_fields1091[4].(int64)
		p.write(fmt.Sprintf("%d", field1096))
		p.newline()
		field1097 := unwrapped_fields1091[5].(int64)
		p.write(fmt.Sprintf("%d", field1097))
		field1098 := unwrapped_fields1091[6].(*int64)
		if field1098 != nil {
			p.newline()
			opt_val1099 := *field1098
			p.write(fmt.Sprintf("%d", opt_val1099))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_dollar_dollar := msg
		fields1101 := _dollar_dollar.GetArgs()
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1102) == 0) {
			p.newline()
			for i1104, elem1103 := range unwrapped_fields1102 {
				if (i1104 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1103)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1110 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1110 != nil {
		p.write(*flat1110)
		return nil
	} else {
		_dollar_dollar := msg
		fields1106 := _dollar_dollar.GetArgs()
		unwrapped_fields1107 := fields1106
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1107) == 0) {
			p.newline()
			for i1109, elem1108 := range unwrapped_fields1107 {
				if (i1109 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1108)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1113 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1113 != nil {
		p.write(*flat1113)
		return nil
	} else {
		_dollar_dollar := msg
		fields1111 := _dollar_dollar.GetArg()
		unwrapped_fields1112 := fields1111
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1112)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1119 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1119 != nil {
		p.write(*flat1119)
		return nil
	} else {
		_dollar_dollar := msg
		fields1114 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1115 := fields1114
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1116 := unwrapped_fields1115[0].(string)
		p.pretty_name(field1116)
		p.newline()
		field1117 := unwrapped_fields1115[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1117)
		p.newline()
		field1118 := unwrapped_fields1115[2].([]*pb.Term)
		p.pretty_terms(field1118)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		fields1120 := msg
		p.write(":")
		p.write(fields1120)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		fields1122 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1122) == 0) {
			p.newline()
			for i1124, elem1123 := range fields1122 {
				if (i1124 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1123)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1132 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_dollar_dollar := msg
		fields1126 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1127 := fields1126
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1128 := unwrapped_fields1127[0].(*pb.RelationId)
		p.pretty_relation_id(field1128)
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

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_dollar_dollar := msg
		fields1133 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1134 := fields1133
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1135 := unwrapped_fields1134[0].(string)
		p.pretty_name(field1135)
		field1136 := unwrapped_fields1134[1].([]*pb.Term)
		if !(len(field1136) == 0) {
			p.newline()
			for i1138, elem1137 := range field1136 {
				if (i1138 > 0) {
					p.newline()
				}
				p.pretty_term(elem1137)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1155 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1155 != nil {
		p.write(*flat1155)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1689 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1689 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1154 := _t1689
		if guard_result1154 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1690 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1690 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1153 := _t1690
			if guard_result1153 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1691 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1691 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1152 := _t1691
				if guard_result1152 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1692 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1692 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1151 := _t1692
					if guard_result1151 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1693 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1693 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1150 := _t1693
						if guard_result1150 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1694 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1694 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1149 := _t1694
							if guard_result1149 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1695 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1695 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1148 := _t1695
								if guard_result1148 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1696 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1696 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1147 := _t1696
									if guard_result1147 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1697 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1697 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1146 := _t1697
										if guard_result1146 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1140 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1141 := fields1140
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1142 := unwrapped_fields1141[0].(string)
											p.pretty_name(field1142)
											field1143 := unwrapped_fields1141[1].([]*pb.RelTerm)
											if !(len(field1143) == 0) {
												p.newline()
												for i1145, elem1144 := range field1143 {
													if (i1145 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1144)
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
	flat1160 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1698 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1698 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1156 := _t1698
		unwrapped_fields1157 := fields1156
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1158 := unwrapped_fields1157[0].(*pb.Term)
		p.pretty_term(field1158)
		p.newline()
		field1159 := unwrapped_fields1157[1].(*pb.Term)
		p.pretty_term(field1159)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1699 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1699 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1161 := _t1699
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1163 := unwrapped_fields1162[0].(*pb.Term)
		p.pretty_term(field1163)
		p.newline()
		field1164 := unwrapped_fields1162[1].(*pb.Term)
		p.pretty_term(field1164)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1170 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1170 != nil {
		p.write(*flat1170)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1700 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1700 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1166 := _t1700
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.Term)
		p.pretty_term(field1168)
		p.newline()
		field1169 := unwrapped_fields1167[1].(*pb.Term)
		p.pretty_term(field1169)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1701 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1701 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1171 := _t1701
		unwrapped_fields1172 := fields1171
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1173 := unwrapped_fields1172[0].(*pb.Term)
		p.pretty_term(field1173)
		p.newline()
		field1174 := unwrapped_fields1172[1].(*pb.Term)
		p.pretty_term(field1174)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1180 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1180 != nil {
		p.write(*flat1180)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1702 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1702 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1176 := _t1702
		unwrapped_fields1177 := fields1176
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1178 := unwrapped_fields1177[0].(*pb.Term)
		p.pretty_term(field1178)
		p.newline()
		field1179 := unwrapped_fields1177[1].(*pb.Term)
		p.pretty_term(field1179)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1703 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1181 := _t1703
		unwrapped_fields1182 := fields1181
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1183 := unwrapped_fields1182[0].(*pb.Term)
		p.pretty_term(field1183)
		p.newline()
		field1184 := unwrapped_fields1182[1].(*pb.Term)
		p.pretty_term(field1184)
		p.newline()
		field1185 := unwrapped_fields1182[2].(*pb.Term)
		p.pretty_term(field1185)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1704 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1704 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1187 := _t1704
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1189 := unwrapped_fields1188[0].(*pb.Term)
		p.pretty_term(field1189)
		p.newline()
		field1190 := unwrapped_fields1188[1].(*pb.Term)
		p.pretty_term(field1190)
		p.newline()
		field1191 := unwrapped_fields1188[2].(*pb.Term)
		p.pretty_term(field1191)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1705 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1705 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1193 := _t1705
		unwrapped_fields1194 := fields1193
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1195 := unwrapped_fields1194[0].(*pb.Term)
		p.pretty_term(field1195)
		p.newline()
		field1196 := unwrapped_fields1194[1].(*pb.Term)
		p.pretty_term(field1196)
		p.newline()
		field1197 := unwrapped_fields1194[2].(*pb.Term)
		p.pretty_term(field1197)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1204 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1706 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1199 := _t1706
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1201 := unwrapped_fields1200[0].(*pb.Term)
		p.pretty_term(field1201)
		p.newline()
		field1202 := unwrapped_fields1200[1].(*pb.Term)
		p.pretty_term(field1202)
		p.newline()
		field1203 := unwrapped_fields1200[2].(*pb.Term)
		p.pretty_term(field1203)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1707 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1207 := _t1707
		if deconstruct_result1207 != nil {
			unwrapped1208 := deconstruct_result1207
			p.pretty_specialized_value(unwrapped1208)
		} else {
			_dollar_dollar := msg
			var _t1708 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1708 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1205 := _t1708
			if deconstruct_result1205 != nil {
				unwrapped1206 := deconstruct_result1205
				p.pretty_term(unwrapped1206)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		fields1210 := msg
		p.write("#")
		p.pretty_raw_value(fields1210)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1218 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1218 != nil {
		p.write(*flat1218)
		return nil
	} else {
		_dollar_dollar := msg
		fields1212 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1213 := fields1212
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1214 := unwrapped_fields1213[0].(string)
		p.pretty_name(field1214)
		field1215 := unwrapped_fields1213[1].([]*pb.RelTerm)
		if !(len(field1215) == 0) {
			p.newline()
			for i1217, elem1216 := range field1215 {
				if (i1217 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1216)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1223 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		_dollar_dollar := msg
		fields1219 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1221 := unwrapped_fields1220[0].(*pb.Term)
		p.pretty_term(field1221)
		p.newline()
		field1222 := unwrapped_fields1220[1].(*pb.Term)
		p.pretty_term(field1222)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		fields1224 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1224) == 0) {
			p.newline()
			for i1226, elem1225 := range fields1224 {
				if (i1226 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1225)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		_dollar_dollar := msg
		fields1228 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1230 := unwrapped_fields1229[0].(string)
		p.pretty_name(field1230)
		field1231 := unwrapped_fields1229[1].([]*pb.Value)
		if !(len(field1231) == 0) {
			p.newline()
			for i1233, elem1232 := range field1231 {
				if (i1233 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1232)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1243 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1709 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1709 = _dollar_dollar.GetAttrs()
		}
		fields1235 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1709}
		unwrapped_fields1236 := fields1235
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1237 := unwrapped_fields1236[0].([]*pb.RelationId)
		if !(len(field1237) == 0) {
			p.newline()
			for i1239, elem1238 := range field1237 {
				if (i1239 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1238)
			}
		}
		p.newline()
		field1240 := unwrapped_fields1236[1].(*pb.Script)
		p.pretty_script(field1240)
		field1241 := unwrapped_fields1236[2].([]*pb.Attribute)
		if field1241 != nil {
			p.newline()
			opt_val1242 := field1241
			p.pretty_attrs(opt_val1242)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1248 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1248 != nil {
		p.write(*flat1248)
		return nil
	} else {
		_dollar_dollar := msg
		fields1244 := _dollar_dollar.GetConstructs()
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1245) == 0) {
			p.newline()
			for i1247, elem1246 := range unwrapped_fields1245 {
				if (i1247 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1246)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1710 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1710 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1251 := _t1710
		if deconstruct_result1251 != nil {
			unwrapped1252 := deconstruct_result1251
			p.pretty_loop(unwrapped1252)
		} else {
			_dollar_dollar := msg
			var _t1711 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1711 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1249 := _t1711
			if deconstruct_result1249 != nil {
				unwrapped1250 := deconstruct_result1249
				p.pretty_instruction(unwrapped1250)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1260 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1260 != nil {
		p.write(*flat1260)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1712 = _dollar_dollar.GetAttrs()
		}
		fields1254 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1712}
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1256 := unwrapped_fields1255[0].([]*pb.Instruction)
		p.pretty_init(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].(*pb.Script)
		p.pretty_script(field1257)
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

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		fields1261 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1261) == 0) {
			p.newline()
			for i1263, elem1262 := range fields1261 {
				if (i1263 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1262)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1275 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1275 != nil {
		p.write(*flat1275)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1713 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1273 := _t1713
		if deconstruct_result1273 != nil {
			unwrapped1274 := deconstruct_result1273
			p.pretty_assign(unwrapped1274)
		} else {
			_dollar_dollar := msg
			var _t1714 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1714 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1271 := _t1714
			if deconstruct_result1271 != nil {
				unwrapped1272 := deconstruct_result1271
				p.pretty_upsert(unwrapped1272)
			} else {
				_dollar_dollar := msg
				var _t1715 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1715 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1269 := _t1715
				if deconstruct_result1269 != nil {
					unwrapped1270 := deconstruct_result1269
					p.pretty_break(unwrapped1270)
				} else {
					_dollar_dollar := msg
					var _t1716 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1716 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1267 := _t1716
					if deconstruct_result1267 != nil {
						unwrapped1268 := deconstruct_result1267
						p.pretty_monoid_def(unwrapped1268)
					} else {
						_dollar_dollar := msg
						var _t1717 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1717 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1265 := _t1717
						if deconstruct_result1265 != nil {
							unwrapped1266 := deconstruct_result1265
							p.pretty_monus_def(unwrapped1266)
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
	flat1282 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1282 != nil {
		p.write(*flat1282)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1718 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1718 = _dollar_dollar.GetAttrs()
		}
		fields1276 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1718}
		unwrapped_fields1277 := fields1276
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1278 := unwrapped_fields1277[0].(*pb.RelationId)
		p.pretty_relation_id(field1278)
		p.newline()
		field1279 := unwrapped_fields1277[1].(*pb.Abstraction)
		p.pretty_abstraction(field1279)
		field1280 := unwrapped_fields1277[2].([]*pb.Attribute)
		if field1280 != nil {
			p.newline()
			opt_val1281 := field1280
			p.pretty_attrs(opt_val1281)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1719 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1719 = _dollar_dollar.GetAttrs()
		}
		fields1283 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1719}
		unwrapped_fields1284 := fields1283
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1285 := unwrapped_fields1284[0].(*pb.RelationId)
		p.pretty_relation_id(field1285)
		p.newline()
		field1286 := unwrapped_fields1284[1].([]interface{})
		p.pretty_abstraction_with_arity(field1286)
		field1287 := unwrapped_fields1284[2].([]*pb.Attribute)
		if field1287 != nil {
			p.newline()
			opt_val1288 := field1287
			p.pretty_attrs(opt_val1288)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1294 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1294 != nil {
		p.write(*flat1294)
		return nil
	} else {
		_dollar_dollar := msg
		_t1720 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1290 := []interface{}{_t1720, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1291 := fields1290
		p.write("(")
		p.indent()
		field1292 := unwrapped_fields1291[0].([]interface{})
		p.pretty_bindings(field1292)
		p.newline()
		field1293 := unwrapped_fields1291[1].(*pb.Formula)
		p.pretty_formula(field1293)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1301 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1301 != nil {
		p.write(*flat1301)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1721 = _dollar_dollar.GetAttrs()
		}
		fields1295 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1721}
		unwrapped_fields1296 := fields1295
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1297 := unwrapped_fields1296[0].(*pb.RelationId)
		p.pretty_relation_id(field1297)
		p.newline()
		field1298 := unwrapped_fields1296[1].(*pb.Abstraction)
		p.pretty_abstraction(field1298)
		field1299 := unwrapped_fields1296[2].([]*pb.Attribute)
		if field1299 != nil {
			p.newline()
			opt_val1300 := field1299
			p.pretty_attrs(opt_val1300)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1309 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1309 != nil {
		p.write(*flat1309)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1722 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1722 = _dollar_dollar.GetAttrs()
		}
		fields1302 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1722}
		unwrapped_fields1303 := fields1302
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1304 := unwrapped_fields1303[0].(*pb.Monoid)
		p.pretty_monoid(field1304)
		p.newline()
		field1305 := unwrapped_fields1303[1].(*pb.RelationId)
		p.pretty_relation_id(field1305)
		p.newline()
		field1306 := unwrapped_fields1303[2].([]interface{})
		p.pretty_abstraction_with_arity(field1306)
		field1307 := unwrapped_fields1303[3].([]*pb.Attribute)
		if field1307 != nil {
			p.newline()
			opt_val1308 := field1307
			p.pretty_attrs(opt_val1308)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1318 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1318 != nil {
		p.write(*flat1318)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1723 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1723 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1316 := _t1723
		if deconstruct_result1316 != nil {
			unwrapped1317 := deconstruct_result1316
			p.pretty_or_monoid(unwrapped1317)
		} else {
			_dollar_dollar := msg
			var _t1724 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1724 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1314 := _t1724
			if deconstruct_result1314 != nil {
				unwrapped1315 := deconstruct_result1314
				p.pretty_min_monoid(unwrapped1315)
			} else {
				_dollar_dollar := msg
				var _t1725 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1725 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1312 := _t1725
				if deconstruct_result1312 != nil {
					unwrapped1313 := deconstruct_result1312
					p.pretty_max_monoid(unwrapped1313)
				} else {
					_dollar_dollar := msg
					var _t1726 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1726 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1310 := _t1726
					if deconstruct_result1310 != nil {
						unwrapped1311 := deconstruct_result1310
						p.pretty_sum_monoid(unwrapped1311)
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
	fields1319 := msg
	_ = fields1319
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1322 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		fields1320 := _dollar_dollar.GetType()
		unwrapped_fields1321 := fields1320
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1321)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1325 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1325 != nil {
		p.write(*flat1325)
		return nil
	} else {
		_dollar_dollar := msg
		fields1323 := _dollar_dollar.GetType()
		unwrapped_fields1324 := fields1323
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1324)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1328 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1328 != nil {
		p.write(*flat1328)
		return nil
	} else {
		_dollar_dollar := msg
		fields1326 := _dollar_dollar.GetType()
		unwrapped_fields1327 := fields1326
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1327)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1336 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1336 != nil {
		p.write(*flat1336)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1727 = _dollar_dollar.GetAttrs()
		}
		fields1329 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1727}
		unwrapped_fields1330 := fields1329
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1331 := unwrapped_fields1330[0].(*pb.Monoid)
		p.pretty_monoid(field1331)
		p.newline()
		field1332 := unwrapped_fields1330[1].(*pb.RelationId)
		p.pretty_relation_id(field1332)
		p.newline()
		field1333 := unwrapped_fields1330[2].([]interface{})
		p.pretty_abstraction_with_arity(field1333)
		field1334 := unwrapped_fields1330[3].([]*pb.Attribute)
		if field1334 != nil {
			p.newline()
			opt_val1335 := field1334
			p.pretty_attrs(opt_val1335)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		_dollar_dollar := msg
		fields1337 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1338 := fields1337
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1339 := unwrapped_fields1338[0].(*pb.RelationId)
		p.pretty_relation_id(field1339)
		p.newline()
		field1340 := unwrapped_fields1338[1].(*pb.Abstraction)
		p.pretty_abstraction(field1340)
		p.newline()
		field1341 := unwrapped_fields1338[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1341)
		p.newline()
		field1342 := unwrapped_fields1338[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1342)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1347 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1347 != nil {
		p.write(*flat1347)
		return nil
	} else {
		fields1344 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1344) == 0) {
			p.newline()
			for i1346, elem1345 := range fields1344 {
				if (i1346 > 0) {
					p.newline()
				}
				p.pretty_var(elem1345)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1351 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1351 != nil {
		p.write(*flat1351)
		return nil
	} else {
		fields1348 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1348) == 0) {
			p.newline()
			for i1350, elem1349 := range fields1348 {
				if (i1350 > 0) {
					p.newline()
				}
				p.pretty_var(elem1349)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1360 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1360 != nil {
		p.write(*flat1360)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1728 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1728 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1358 := _t1728
		if deconstruct_result1358 != nil {
			unwrapped1359 := deconstruct_result1358
			p.pretty_edb(unwrapped1359)
		} else {
			_dollar_dollar := msg
			var _t1729 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1729 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1356 := _t1729
			if deconstruct_result1356 != nil {
				unwrapped1357 := deconstruct_result1356
				p.pretty_betree_relation(unwrapped1357)
			} else {
				_dollar_dollar := msg
				var _t1730 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1730 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1354 := _t1730
				if deconstruct_result1354 != nil {
					unwrapped1355 := deconstruct_result1354
					p.pretty_csv_data(unwrapped1355)
				} else {
					_dollar_dollar := msg
					var _t1731 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1731 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1352 := _t1731
					if deconstruct_result1352 != nil {
						unwrapped1353 := deconstruct_result1352
						p.pretty_iceberg_data(unwrapped1353)
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
	flat1366 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1366 != nil {
		p.write(*flat1366)
		return nil
	} else {
		_dollar_dollar := msg
		fields1361 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1362 := fields1361
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1363 := unwrapped_fields1362[0].(*pb.RelationId)
		p.pretty_relation_id(field1363)
		p.newline()
		field1364 := unwrapped_fields1362[1].([]string)
		p.pretty_edb_path(field1364)
		p.newline()
		field1365 := unwrapped_fields1362[2].([]*pb.Type)
		p.pretty_edb_types(field1365)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1370 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1370 != nil {
		p.write(*flat1370)
		return nil
	} else {
		fields1367 := msg
		p.write("[")
		p.indent()
		for i1369, elem1368 := range fields1367 {
			if (i1369 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1368))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1374 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1374 != nil {
		p.write(*flat1374)
		return nil
	} else {
		fields1371 := msg
		p.write("[")
		p.indent()
		for i1373, elem1372 := range fields1371 {
			if (i1373 > 0) {
				p.newline()
			}
			p.pretty_type(elem1372)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1379 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1379 != nil {
		p.write(*flat1379)
		return nil
	} else {
		_dollar_dollar := msg
		fields1375 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1376 := fields1375
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1377 := unwrapped_fields1376[0].(*pb.RelationId)
		p.pretty_relation_id(field1377)
		p.newline()
		field1378 := unwrapped_fields1376[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1378)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		_dollar_dollar := msg
		_t1732 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1380 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1732}
		unwrapped_fields1381 := fields1380
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1382 := unwrapped_fields1381[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1382)
		p.newline()
		field1383 := unwrapped_fields1381[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1383)
		p.newline()
		field1384 := unwrapped_fields1381[2].([][]interface{})
		p.pretty_config_dict(field1384)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1389 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		fields1386 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1386) == 0) {
			p.newline()
			for i1388, elem1387 := range fields1386 {
				if (i1388 > 0) {
					p.newline()
				}
				p.pretty_type(elem1387)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1393 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1393 != nil {
		p.write(*flat1393)
		return nil
	} else {
		fields1390 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1390) == 0) {
			p.newline()
			for i1392, elem1391 := range fields1390 {
				if (i1392 > 0) {
					p.newline()
				}
				p.pretty_type(elem1391)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1403 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		_dollar_dollar := msg
		_t1733 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1734 := p.deconstruct_csv_data_target_optional(_dollar_dollar)
		fields1394 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1733, _t1734, _dollar_dollar.GetAsof()}
		unwrapped_fields1395 := fields1394
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1396 := unwrapped_fields1395[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1396)
		p.newline()
		field1397 := unwrapped_fields1395[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1397)
		field1398 := unwrapped_fields1395[2].([]*pb.GNFColumn)
		if field1398 != nil {
			p.newline()
			opt_val1399 := field1398
			p.pretty_gnf_columns(opt_val1399)
		}
		field1400 := unwrapped_fields1395[3].(*pb.CSVTarget)
		if field1400 != nil {
			p.newline()
			opt_val1401 := field1400
			p.pretty_csv_table(opt_val1401)
		}
		p.newline()
		field1402 := unwrapped_fields1395[4].(string)
		p.pretty_csv_asof(field1402)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1735 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1735 = _dollar_dollar.GetPaths()
		}
		var _t1736 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1736 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1404 := []interface{}{_t1735, _t1736}
		unwrapped_fields1405 := fields1404
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1406 := unwrapped_fields1405[0].([]string)
		if field1406 != nil {
			p.newline()
			opt_val1407 := field1406
			p.pretty_csv_locator_paths(opt_val1407)
		}
		field1408 := unwrapped_fields1405[1].(*string)
		if field1408 != nil {
			p.newline()
			opt_val1409 := *field1408
			p.pretty_csv_locator_inline_data(opt_val1409)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1414 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1414 != nil {
		p.write(*flat1414)
		return nil
	} else {
		fields1411 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1411) == 0) {
			p.newline()
			for i1413, elem1412 := range fields1411 {
				if (i1413 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1412))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1416 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1416 != nil {
		p.write(*flat1416)
		return nil
	} else {
		fields1415 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1415))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1419 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1419 != nil {
		p.write(*flat1419)
		return nil
	} else {
		_dollar_dollar := msg
		_t1737 := p.deconstruct_csv_config(_dollar_dollar)
		fields1417 := _t1737
		unwrapped_fields1418 := fields1417
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1418)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1423 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		fields1420 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1420) == 0) {
			p.newline()
			for i1422, elem1421 := range fields1420 {
				if (i1422 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1421)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1738 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1738 = _dollar_dollar.GetTargetId()
		}
		fields1424 := []interface{}{_dollar_dollar.GetColumnPath(), _t1738, _dollar_dollar.GetTypes()}
		unwrapped_fields1425 := fields1424
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1426 := unwrapped_fields1425[0].([]string)
		p.pretty_gnf_column_path(field1426)
		field1427 := unwrapped_fields1425[1].(*pb.RelationId)
		if field1427 != nil {
			p.newline()
			opt_val1428 := field1427
			p.pretty_relation_id(opt_val1428)
		}
		p.newline()
		p.write("[")
		field1429 := unwrapped_fields1425[2].([]*pb.Type)
		for i1431, elem1430 := range field1429 {
			if (i1431 > 0) {
				p.newline()
			}
			p.pretty_type(elem1430)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1439 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1439 != nil {
		p.write(*flat1439)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1739 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1739 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1437 := _t1739
		if deconstruct_result1437 != nil {
			unwrapped1438 := *deconstruct_result1437
			p.write(p.formatStringValue(unwrapped1438))
		} else {
			_dollar_dollar := msg
			var _t1740 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1740 = _dollar_dollar
			}
			deconstruct_result1433 := _t1740
			if deconstruct_result1433 != nil {
				unwrapped1434 := deconstruct_result1433
				p.write("[")
				p.indent()
				for i1436, elem1435 := range unwrapped1434 {
					if (i1436 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1435))
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

func (p *PrettyPrinter) pretty_csv_table(msg *pb.CSVTarget) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_csv_table(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		_dollar_dollar := msg
		fields1440 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetColumnNames(), _dollar_dollar.GetTypes()}
		unwrapped_fields1441 := fields1440
		p.write("(")
		p.write("table")
		p.indentSexp()
		p.newline()
		field1442 := unwrapped_fields1441[0].(*pb.RelationId)
		p.pretty_relation_id(field1442)
		p.newline()
		p.write("[")
		field1443 := unwrapped_fields1441[1].([]string)
		for i1445, elem1444 := range field1443 {
			if (i1445 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1444))
		}
		p.write("]")
		p.newline()
		p.write("[")
		field1446 := unwrapped_fields1441[2].([]*pb.Type)
		for i1448, elem1447 := range field1446 {
			if (i1448 > 0) {
				p.newline()
			}
			p.pretty_type(elem1447)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1451 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1451 != nil {
		p.write(*flat1451)
		return nil
	} else {
		fields1450 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1450))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		_dollar_dollar := msg
		_t1741 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1742 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1452 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1741, _t1742, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1453 := fields1452
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1454 := unwrapped_fields1453[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1454)
		p.newline()
		field1455 := unwrapped_fields1453[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1455)
		p.newline()
		field1456 := unwrapped_fields1453[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1456)
		field1457 := unwrapped_fields1453[3].(*string)
		if field1457 != nil {
			p.newline()
			opt_val1458 := *field1457
			p.pretty_iceberg_from_snapshot(opt_val1458)
		}
		field1459 := unwrapped_fields1453[4].(*string)
		if field1459 != nil {
			p.newline()
			opt_val1460 := *field1459
			p.pretty_iceberg_to_snapshot(opt_val1460)
		}
		p.newline()
		field1461 := unwrapped_fields1453[5].(bool)
		p.pretty_boolean_value(field1461)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		_dollar_dollar := msg
		fields1463 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1464 := fields1463
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1465 := unwrapped_fields1464[0].(string)
		p.pretty_iceberg_locator_table_name(field1465)
		p.newline()
		field1466 := unwrapped_fields1464[1].([]string)
		p.pretty_iceberg_locator_namespace(field1466)
		p.newline()
		field1467 := unwrapped_fields1464[2].(string)
		p.pretty_iceberg_locator_warehouse(field1467)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1470 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		fields1469 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1469))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1474 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1474 != nil {
		p.write(*flat1474)
		return nil
	} else {
		fields1471 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1471) == 0) {
			p.newline()
			for i1473, elem1472 := range fields1471 {
				if (i1473 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1472))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1476 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1476 != nil {
		p.write(*flat1476)
		return nil
	} else {
		fields1475 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1475))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		_dollar_dollar := msg
		_t1743 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1477 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1743, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1478 := fields1477
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1479 := unwrapped_fields1478[0].(string)
		p.pretty_iceberg_catalog_uri(field1479)
		field1480 := unwrapped_fields1478[1].(*string)
		if field1480 != nil {
			p.newline()
			opt_val1481 := *field1480
			p.pretty_iceberg_catalog_config_scope(opt_val1481)
		}
		p.newline()
		field1482 := unwrapped_fields1478[2].([][]interface{})
		p.pretty_iceberg_properties(field1482)
		p.newline()
		field1483 := unwrapped_fields1478[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1483)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1486 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1486 != nil {
		p.write(*flat1486)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1485))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		fields1487 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1487))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		fields1489 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1489) == 0) {
			p.newline()
			for i1491, elem1490 := range fields1489 {
				if (i1491 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1490)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1497 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1497 != nil {
		p.write(*flat1497)
		return nil
	} else {
		_dollar_dollar := msg
		fields1493 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1494 := fields1493
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1495 := unwrapped_fields1494[0].(string)
		p.write(p.formatStringValue(field1495))
		p.newline()
		field1496 := unwrapped_fields1494[1].(string)
		p.write(p.formatStringValue(field1496))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1501 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1501 != nil {
		p.write(*flat1501)
		return nil
	} else {
		fields1498 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1498) == 0) {
			p.newline()
			for i1500, elem1499 := range fields1498 {
				if (i1500 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1499)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1506 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1506 != nil {
		p.write(*flat1506)
		return nil
	} else {
		_dollar_dollar := msg
		_t1744 := p.mask_secret_value(_dollar_dollar)
		fields1502 := []interface{}{_dollar_dollar[0].(string), _t1744}
		unwrapped_fields1503 := fields1502
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1504 := unwrapped_fields1503[0].(string)
		p.write(p.formatStringValue(field1504))
		p.newline()
		field1505 := unwrapped_fields1503[1].(string)
		p.write(p.formatStringValue(field1505))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1508 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1508 != nil {
		p.write(*flat1508)
		return nil
	} else {
		fields1507 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1507))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1510 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1510 != nil {
		p.write(*flat1510)
		return nil
	} else {
		fields1509 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1509))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1513 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1513 != nil {
		p.write(*flat1513)
		return nil
	} else {
		_dollar_dollar := msg
		fields1511 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1512 := fields1511
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1512)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1518 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1518 != nil {
		p.write(*flat1518)
		return nil
	} else {
		_dollar_dollar := msg
		fields1514 := _dollar_dollar.GetRelations()
		unwrapped_fields1515 := fields1514
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1515) == 0) {
			p.newline()
			for i1517, elem1516 := range unwrapped_fields1515 {
				if (i1517 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1516)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1525 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1525 != nil {
		p.write(*flat1525)
		return nil
	} else {
		_dollar_dollar := msg
		fields1519 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1520 := fields1519
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1521 := unwrapped_fields1520[0].([]string)
		p.pretty_edb_path(field1521)
		field1522 := unwrapped_fields1520[1].([]*pb.SnapshotMapping)
		if !(len(field1522) == 0) {
			p.newline()
			for i1524, elem1523 := range field1522 {
				if (i1524 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1523)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1530 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1530 != nil {
		p.write(*flat1530)
		return nil
	} else {
		_dollar_dollar := msg
		fields1526 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1527 := fields1526
		field1528 := unwrapped_fields1527[0].([]string)
		p.pretty_edb_path(field1528)
		p.write(" ")
		field1529 := unwrapped_fields1527[1].(*pb.RelationId)
		p.pretty_relation_id(field1529)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1534 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1534 != nil {
		p.write(*flat1534)
		return nil
	} else {
		fields1531 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1531) == 0) {
			p.newline()
			for i1533, elem1532 := range fields1531 {
				if (i1533 > 0) {
					p.newline()
				}
				p.pretty_read(elem1532)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1545 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1545 != nil {
		p.write(*flat1545)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1745 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1745 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1543 := _t1745
		if deconstruct_result1543 != nil {
			unwrapped1544 := deconstruct_result1543
			p.pretty_demand(unwrapped1544)
		} else {
			_dollar_dollar := msg
			var _t1746 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1746 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1541 := _t1746
			if deconstruct_result1541 != nil {
				unwrapped1542 := deconstruct_result1541
				p.pretty_output(unwrapped1542)
			} else {
				_dollar_dollar := msg
				var _t1747 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1747 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1539 := _t1747
				if deconstruct_result1539 != nil {
					unwrapped1540 := deconstruct_result1539
					p.pretty_what_if(unwrapped1540)
				} else {
					_dollar_dollar := msg
					var _t1748 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1748 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1537 := _t1748
					if deconstruct_result1537 != nil {
						unwrapped1538 := deconstruct_result1537
						p.pretty_abort(unwrapped1538)
					} else {
						_dollar_dollar := msg
						var _t1749 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1749 = _dollar_dollar.GetExport()
						}
						deconstruct_result1535 := _t1749
						if deconstruct_result1535 != nil {
							unwrapped1536 := deconstruct_result1535
							p.pretty_export(unwrapped1536)
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
	flat1548 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1548 != nil {
		p.write(*flat1548)
		return nil
	} else {
		_dollar_dollar := msg
		fields1546 := _dollar_dollar.GetRelationId()
		unwrapped_fields1547 := fields1546
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1547)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1553 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1553 != nil {
		p.write(*flat1553)
		return nil
	} else {
		_dollar_dollar := msg
		fields1549 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1550 := fields1549
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1551 := unwrapped_fields1550[0].(string)
		p.pretty_name(field1551)
		p.newline()
		field1552 := unwrapped_fields1550[1].(*pb.RelationId)
		p.pretty_relation_id(field1552)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1558 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1558 != nil {
		p.write(*flat1558)
		return nil
	} else {
		_dollar_dollar := msg
		fields1554 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1555 := fields1554
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1556 := unwrapped_fields1555[0].(string)
		p.pretty_name(field1556)
		p.newline()
		field1557 := unwrapped_fields1555[1].(*pb.Epoch)
		p.pretty_epoch(field1557)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1564 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1564 != nil {
		p.write(*flat1564)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1750 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1750 = ptr(_dollar_dollar.GetName())
		}
		fields1559 := []interface{}{_t1750, _dollar_dollar.GetRelationId()}
		unwrapped_fields1560 := fields1559
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1561 := unwrapped_fields1560[0].(*string)
		if field1561 != nil {
			p.newline()
			opt_val1562 := *field1561
			p.pretty_name(opt_val1562)
		}
		p.newline()
		field1563 := unwrapped_fields1560[1].(*pb.RelationId)
		p.pretty_relation_id(field1563)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1569 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1569 != nil {
		p.write(*flat1569)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1751 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1751 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1567 := _t1751
		if deconstruct_result1567 != nil {
			unwrapped1568 := deconstruct_result1567
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1568)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1752 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1752 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1565 := _t1752
			if deconstruct_result1565 != nil {
				unwrapped1566 := deconstruct_result1565
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1566)
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
	flat1580 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1580 != nil {
		p.write(*flat1580)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1753 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1753 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1575 := _t1753
		if deconstruct_result1575 != nil {
			unwrapped1576 := deconstruct_result1575
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1577 := unwrapped1576[0].(string)
			p.pretty_export_csv_path(field1577)
			p.newline()
			field1578 := unwrapped1576[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1578)
			p.newline()
			field1579 := unwrapped1576[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1579)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1754 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1755 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1754 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1755}
			}
			deconstruct_result1570 := _t1754
			if deconstruct_result1570 != nil {
				unwrapped1571 := deconstruct_result1570
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1572 := unwrapped1571[0].(string)
				p.pretty_export_csv_path(field1572)
				p.newline()
				field1573 := unwrapped1571[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1573)
				p.newline()
				field1574 := unwrapped1571[2].([][]interface{})
				p.pretty_config_dict(field1574)
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
	flat1582 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1582 != nil {
		p.write(*flat1582)
		return nil
	} else {
		fields1581 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1581))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1589 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1589 != nil {
		p.write(*flat1589)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1756 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1756 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1585 := _t1756
		if deconstruct_result1585 != nil {
			unwrapped1586 := deconstruct_result1585
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1586) == 0) {
				p.newline()
				for i1588, elem1587 := range unwrapped1586 {
					if (i1588 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1587)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1757 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1757 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1583 := _t1757
			if deconstruct_result1583 != nil {
				unwrapped1584 := deconstruct_result1583
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1584)
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
	flat1594 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1594 != nil {
		p.write(*flat1594)
		return nil
	} else {
		_dollar_dollar := msg
		fields1590 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1591 := fields1590
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1592 := unwrapped_fields1591[0].(string)
		p.write(p.formatStringValue(field1592))
		p.newline()
		field1593 := unwrapped_fields1591[1].(*pb.RelationId)
		p.pretty_relation_id(field1593)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1598 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1598 != nil {
		p.write(*flat1598)
		return nil
	} else {
		fields1595 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1595) == 0) {
			p.newline()
			for i1597, elem1596 := range fields1595 {
				if (i1597 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1596)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1607 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1607 != nil {
		p.write(*flat1607)
		return nil
	} else {
		_dollar_dollar := msg
		_t1758 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1599 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1758}
		unwrapped_fields1600 := fields1599
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1601 := unwrapped_fields1600[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1601)
		p.newline()
		field1602 := unwrapped_fields1600[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1602)
		p.newline()
		field1603 := unwrapped_fields1600[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1603)
		p.newline()
		field1604 := unwrapped_fields1600[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1604)
		field1605 := unwrapped_fields1600[4].([][]interface{})
		if field1605 != nil {
			p.newline()
			opt_val1606 := field1605
			p.pretty_config_dict(opt_val1606)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1609 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1609 != nil {
		p.write(*flat1609)
		return nil
	} else {
		fields1608 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1608)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1613 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1613 != nil {
		p.write(*flat1613)
		return nil
	} else {
		fields1610 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1610) == 0) {
			p.newline()
			for i1612, elem1611 := range fields1610 {
				if (i1612 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1611)
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
		_t1806 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1806)
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
	case *pb.CSVTarget:
		p.pretty_csv_table(m)
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
