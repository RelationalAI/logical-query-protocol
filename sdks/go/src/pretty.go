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
	_t1768 := &pb.Value{}
	_t1768.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1768
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1769 := &pb.Value{}
	_t1769.Value = &pb.Value_IntValue{IntValue: v}
	return _t1769
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1770 := &pb.Value{}
	_t1770.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1770
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1771 := &pb.Value{}
	_t1771.Value = &pb.Value_StringValue{StringValue: v}
	return _t1771
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1772 := &pb.Value{}
	_t1772.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1772
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1773 := &pb.Value{}
	_t1773.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1773
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1774 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1774})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1775 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1775})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1776 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1776})
			}
		}
	}
	_t1777 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1777})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1778 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1778})
	_t1779 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1779})
	if msg.GetNewLine() != "" {
		_t1780 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1780})
	}
	_t1781 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1781})
	_t1782 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1782})
	_t1783 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1783})
	if msg.GetComment() != "" {
		_t1784 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1784})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1785 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1785})
	}
	_t1786 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1786})
	_t1787 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1787})
	_t1788 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1788})
	if msg.GetPartitionSizeMb() != 0 {
		_t1789 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1789})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1790 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1790
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1791 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1791})
	}
	if si.GetAzureSasToken() != "" {
		_t1792 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1792})
	}
	if si.GetS3Region() != "" {
		_t1793 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1793})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1794 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1794})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1795 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1795})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1796 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1796})
	_t1797 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1797})
	_t1798 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1798})
	_t1799 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1799})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1800 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1800})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1801 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1801})
		}
	}
	_t1802 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1802})
	_t1803 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1803})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1804 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1804})
	}
	if msg.Compression != nil {
		_t1805 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1805})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1806 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1806})
	}
	if msg.SyntaxMissingString != nil {
		_t1807 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1807})
	}
	if msg.SyntaxDelim != nil {
		_t1808 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1808})
	}
	if msg.SyntaxQuotechar != nil {
		_t1809 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1809})
	}
	if msg.SyntaxEscapechar != nil {
		_t1810 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1810})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1811 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1811
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1812 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1812
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1813 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1813
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1814 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1814})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1815 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1815})
	}
	if msg.GetCompression() != "" {
		_t1816 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1816})
	}
	var _t1817 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1817
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1818 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1818
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
	flat820 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1622 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1622 = _dollar_dollar.GetConfigure()
		}
		var _t1623 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1623 = _dollar_dollar.GetSync()
		}
		fields811 := []interface{}{_t1622, _t1623, _dollar_dollar.GetEpochs()}
		unwrapped_fields812 := fields811
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field813 := unwrapped_fields812[0].(*pb.Configure)
		if field813 != nil {
			p.newline()
			opt_val814 := field813
			p.pretty_configure(opt_val814)
		}
		field815 := unwrapped_fields812[1].(*pb.Sync)
		if field815 != nil {
			p.newline()
			opt_val816 := field815
			p.pretty_sync(opt_val816)
		}
		field817 := unwrapped_fields812[2].([]*pb.Epoch)
		if !(len(field817) == 0) {
			p.newline()
			for i819, elem818 := range field817 {
				if (i819 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem818)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat823 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat823 != nil {
		p.write(*flat823)
		return nil
	} else {
		_dollar_dollar := msg
		_t1624 := p.deconstruct_configure(_dollar_dollar)
		fields821 := _t1624
		unwrapped_fields822 := fields821
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields822)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat827 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat827 != nil {
		p.write(*flat827)
		return nil
	} else {
		fields824 := msg
		p.write("{")
		p.indent()
		if !(len(fields824) == 0) {
			p.newline()
			for i826, elem825 := range fields824 {
				if (i826 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem825)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat832 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat832 != nil {
		p.write(*flat832)
		return nil
	} else {
		_dollar_dollar := msg
		fields828 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields829 := fields828
		p.write(":")
		field830 := unwrapped_fields829[0].(string)
		p.write(field830)
		p.write(" ")
		field831 := unwrapped_fields829[1].(*pb.Value)
		p.pretty_raw_value(field831)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1625 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result856 := _t1625
		if deconstruct_result856 != nil {
			unwrapped857 := deconstruct_result856
			p.pretty_raw_date(unwrapped857)
		} else {
			_dollar_dollar := msg
			var _t1626 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1626 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result854 := _t1626
			if deconstruct_result854 != nil {
				unwrapped855 := deconstruct_result854
				p.pretty_raw_datetime(unwrapped855)
			} else {
				_dollar_dollar := msg
				var _t1627 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1627 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result852 := _t1627
				if deconstruct_result852 != nil {
					unwrapped853 := *deconstruct_result852
					p.write(p.formatStringValue(unwrapped853))
				} else {
					_dollar_dollar := msg
					var _t1628 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1628 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result850 := _t1628
					if deconstruct_result850 != nil {
						unwrapped851 := *deconstruct_result850
						p.write(fmt.Sprintf("%di32", unwrapped851))
					} else {
						_dollar_dollar := msg
						var _t1629 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1629 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result848 := _t1629
						if deconstruct_result848 != nil {
							unwrapped849 := *deconstruct_result848
							p.write(fmt.Sprintf("%d", unwrapped849))
						} else {
							_dollar_dollar := msg
							var _t1630 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1630 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result846 := _t1630
							if deconstruct_result846 != nil {
								unwrapped847 := *deconstruct_result846
								p.write(formatFloat32(unwrapped847))
							} else {
								_dollar_dollar := msg
								var _t1631 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1631 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result844 := _t1631
								if deconstruct_result844 != nil {
									unwrapped845 := *deconstruct_result844
									p.write(formatFloat64(unwrapped845))
								} else {
									_dollar_dollar := msg
									var _t1632 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1632 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result842 := _t1632
									if deconstruct_result842 != nil {
										unwrapped843 := *deconstruct_result842
										p.write(fmt.Sprintf("%du32", unwrapped843))
									} else {
										_dollar_dollar := msg
										var _t1633 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1633 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result840 := _t1633
										if deconstruct_result840 != nil {
											unwrapped841 := deconstruct_result840
											p.write(p.formatUint128(unwrapped841))
										} else {
											_dollar_dollar := msg
											var _t1634 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1634 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result838 := _t1634
											if deconstruct_result838 != nil {
												unwrapped839 := deconstruct_result838
												p.write(p.formatInt128(unwrapped839))
											} else {
												_dollar_dollar := msg
												var _t1635 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1635 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result836 := _t1635
												if deconstruct_result836 != nil {
													unwrapped837 := deconstruct_result836
													p.write(p.formatDecimal(unwrapped837))
												} else {
													_dollar_dollar := msg
													var _t1636 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1636 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result834 := _t1636
													if deconstruct_result834 != nil {
														unwrapped835 := *deconstruct_result834
														p.pretty_boolean_value(unwrapped835)
													} else {
														fields833 := msg
														_ = fields833
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
	flat864 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_dollar_dollar := msg
		fields859 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields860 := fields859
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field861 := unwrapped_fields860[0].(int64)
		p.write(fmt.Sprintf("%d", field861))
		p.newline()
		field862 := unwrapped_fields860[1].(int64)
		p.write(fmt.Sprintf("%d", field862))
		p.newline()
		field863 := unwrapped_fields860[2].(int64)
		p.write(fmt.Sprintf("%d", field863))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		_dollar_dollar := msg
		fields865 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields866 := fields865
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field867 := unwrapped_fields866[0].(int64)
		p.write(fmt.Sprintf("%d", field867))
		p.newline()
		field868 := unwrapped_fields866[1].(int64)
		p.write(fmt.Sprintf("%d", field868))
		p.newline()
		field869 := unwrapped_fields866[2].(int64)
		p.write(fmt.Sprintf("%d", field869))
		p.newline()
		field870 := unwrapped_fields866[3].(int64)
		p.write(fmt.Sprintf("%d", field870))
		p.newline()
		field871 := unwrapped_fields866[4].(int64)
		p.write(fmt.Sprintf("%d", field871))
		p.newline()
		field872 := unwrapped_fields866[5].(int64)
		p.write(fmt.Sprintf("%d", field872))
		field873 := unwrapped_fields866[6].(*int64)
		if field873 != nil {
			p.newline()
			opt_val874 := *field873
			p.write(fmt.Sprintf("%d", opt_val874))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1637 []interface{}
	if _dollar_dollar {
		_t1637 = []interface{}{}
	}
	deconstruct_result878 := _t1637
	if deconstruct_result878 != nil {
		unwrapped879 := deconstruct_result878
		_ = unwrapped879
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1638 []interface{}
		if !(_dollar_dollar) {
			_t1638 = []interface{}{}
		}
		deconstruct_result876 := _t1638
		if deconstruct_result876 != nil {
			unwrapped877 := deconstruct_result876
			_ = unwrapped877
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat884 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat884 != nil {
		p.write(*flat884)
		return nil
	} else {
		_dollar_dollar := msg
		fields880 := _dollar_dollar.GetFragments()
		unwrapped_fields881 := fields880
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields881) == 0) {
			p.newline()
			for i883, elem882 := range unwrapped_fields881 {
				if (i883 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem882)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		_dollar_dollar := msg
		fields885 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields886 := fields885
		p.write(":")
		p.write(unwrapped_fields886)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat894 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1639 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1639 = _dollar_dollar.GetWrites()
		}
		var _t1640 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1640 = _dollar_dollar.GetReads()
		}
		fields888 := []interface{}{_t1639, _t1640}
		unwrapped_fields889 := fields888
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field890 := unwrapped_fields889[0].([]*pb.Write)
		if field890 != nil {
			p.newline()
			opt_val891 := field890
			p.pretty_epoch_writes(opt_val891)
		}
		field892 := unwrapped_fields889[1].([]*pb.Read)
		if field892 != nil {
			p.newline()
			opt_val893 := field892
			p.pretty_epoch_reads(opt_val893)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat898 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat898 != nil {
		p.write(*flat898)
		return nil
	} else {
		fields895 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields895) == 0) {
			p.newline()
			for i897, elem896 := range fields895 {
				if (i897 > 0) {
					p.newline()
				}
				p.pretty_write(elem896)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat907 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat907 != nil {
		p.write(*flat907)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1641 = _dollar_dollar.GetDefine()
		}
		deconstruct_result905 := _t1641
		if deconstruct_result905 != nil {
			unwrapped906 := deconstruct_result905
			p.pretty_define(unwrapped906)
		} else {
			_dollar_dollar := msg
			var _t1642 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1642 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result903 := _t1642
			if deconstruct_result903 != nil {
				unwrapped904 := deconstruct_result903
				p.pretty_undefine(unwrapped904)
			} else {
				_dollar_dollar := msg
				var _t1643 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1643 = _dollar_dollar.GetContext()
				}
				deconstruct_result901 := _t1643
				if deconstruct_result901 != nil {
					unwrapped902 := deconstruct_result901
					p.pretty_context(unwrapped902)
				} else {
					_dollar_dollar := msg
					var _t1644 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1644 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result899 := _t1644
					if deconstruct_result899 != nil {
						unwrapped900 := deconstruct_result899
						p.pretty_snapshot(unwrapped900)
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
	flat910 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat910 != nil {
		p.write(*flat910)
		return nil
	} else {
		_dollar_dollar := msg
		fields908 := _dollar_dollar.GetFragment()
		unwrapped_fields909 := fields908
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields909)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields911 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields912 := fields911
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field913 := unwrapped_fields912[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field913)
		field914 := unwrapped_fields912[1].([]*pb.Declaration)
		if !(len(field914) == 0) {
			p.newline()
			for i916, elem915 := range field914 {
				if (i916 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem915)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat919 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat919 != nil {
		p.write(*flat919)
		return nil
	} else {
		fields918 := msg
		p.pretty_fragment_id(fields918)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat928 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat928 != nil {
		p.write(*flat928)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1645 = _dollar_dollar.GetDef()
		}
		deconstruct_result926 := _t1645
		if deconstruct_result926 != nil {
			unwrapped927 := deconstruct_result926
			p.pretty_def(unwrapped927)
		} else {
			_dollar_dollar := msg
			var _t1646 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1646 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result924 := _t1646
			if deconstruct_result924 != nil {
				unwrapped925 := deconstruct_result924
				p.pretty_algorithm(unwrapped925)
			} else {
				_dollar_dollar := msg
				var _t1647 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1647 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result922 := _t1647
				if deconstruct_result922 != nil {
					unwrapped923 := deconstruct_result922
					p.pretty_constraint(unwrapped923)
				} else {
					_dollar_dollar := msg
					var _t1648 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1648 = _dollar_dollar.GetData()
					}
					deconstruct_result920 := _t1648
					if deconstruct_result920 != nil {
						unwrapped921 := deconstruct_result920
						p.pretty_data(unwrapped921)
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
	flat935 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat935 != nil {
		p.write(*flat935)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1649 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1649 = _dollar_dollar.GetAttrs()
		}
		fields929 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1649}
		unwrapped_fields930 := fields929
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field931 := unwrapped_fields930[0].(*pb.RelationId)
		p.pretty_relation_id(field931)
		p.newline()
		field932 := unwrapped_fields930[1].(*pb.Abstraction)
		p.pretty_abstraction(field932)
		field933 := unwrapped_fields930[2].([]*pb.Attribute)
		if field933 != nil {
			p.newline()
			opt_val934 := field933
			p.pretty_attrs(opt_val934)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat940 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat940 != nil {
		p.write(*flat940)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1650 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1651 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1650 = ptr(_t1651)
		}
		deconstruct_result938 := _t1650
		if deconstruct_result938 != nil {
			unwrapped939 := *deconstruct_result938
			p.write(":")
			p.write(unwrapped939)
		} else {
			_dollar_dollar := msg
			_t1652 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result936 := _t1652
			if deconstruct_result936 != nil {
				unwrapped937 := deconstruct_result936
				p.write(p.formatUint128(unwrapped937))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat945 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat945 != nil {
		p.write(*flat945)
		return nil
	} else {
		_dollar_dollar := msg
		_t1653 := p.deconstruct_bindings(_dollar_dollar)
		fields941 := []interface{}{_t1653, _dollar_dollar.GetValue()}
		unwrapped_fields942 := fields941
		p.write("(")
		p.indent()
		field943 := unwrapped_fields942[0].([]interface{})
		p.pretty_bindings(field943)
		p.newline()
		field944 := unwrapped_fields942[1].(*pb.Formula)
		p.pretty_formula(field944)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat953 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat953 != nil {
		p.write(*flat953)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1654 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1654 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields946 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1654}
		unwrapped_fields947 := fields946
		p.write("[")
		p.indent()
		field948 := unwrapped_fields947[0].([]*pb.Binding)
		for i950, elem949 := range field948 {
			if (i950 > 0) {
				p.newline()
			}
			p.pretty_binding(elem949)
		}
		field951 := unwrapped_fields947[1].([]*pb.Binding)
		if field951 != nil {
			p.newline()
			opt_val952 := field951
			p.pretty_value_bindings(opt_val952)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_dollar_dollar := msg
		fields954 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields955 := fields954
		field956 := unwrapped_fields955[0].(string)
		p.write(field956)
		p.write("::")
		field957 := unwrapped_fields955[1].(*pb.Type)
		p.pretty_type(field957)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat987 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat987 != nil {
		p.write(*flat987)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1655 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result985 := _t1655
		if deconstruct_result985 != nil {
			unwrapped986 := deconstruct_result985
			p.pretty_unspecified_type(unwrapped986)
		} else {
			_dollar_dollar := msg
			var _t1656 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1656 = _dollar_dollar.GetStringType()
			}
			deconstruct_result983 := _t1656
			if deconstruct_result983 != nil {
				unwrapped984 := deconstruct_result983
				p.pretty_string_type(unwrapped984)
			} else {
				_dollar_dollar := msg
				var _t1657 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1657 = _dollar_dollar.GetIntType()
				}
				deconstruct_result981 := _t1657
				if deconstruct_result981 != nil {
					unwrapped982 := deconstruct_result981
					p.pretty_int_type(unwrapped982)
				} else {
					_dollar_dollar := msg
					var _t1658 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1658 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result979 := _t1658
					if deconstruct_result979 != nil {
						unwrapped980 := deconstruct_result979
						p.pretty_float_type(unwrapped980)
					} else {
						_dollar_dollar := msg
						var _t1659 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1659 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result977 := _t1659
						if deconstruct_result977 != nil {
							unwrapped978 := deconstruct_result977
							p.pretty_uint128_type(unwrapped978)
						} else {
							_dollar_dollar := msg
							var _t1660 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1660 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result975 := _t1660
							if deconstruct_result975 != nil {
								unwrapped976 := deconstruct_result975
								p.pretty_int128_type(unwrapped976)
							} else {
								_dollar_dollar := msg
								var _t1661 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1661 = _dollar_dollar.GetDateType()
								}
								deconstruct_result973 := _t1661
								if deconstruct_result973 != nil {
									unwrapped974 := deconstruct_result973
									p.pretty_date_type(unwrapped974)
								} else {
									_dollar_dollar := msg
									var _t1662 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1662 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result971 := _t1662
									if deconstruct_result971 != nil {
										unwrapped972 := deconstruct_result971
										p.pretty_datetime_type(unwrapped972)
									} else {
										_dollar_dollar := msg
										var _t1663 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1663 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result969 := _t1663
										if deconstruct_result969 != nil {
											unwrapped970 := deconstruct_result969
											p.pretty_missing_type(unwrapped970)
										} else {
											_dollar_dollar := msg
											var _t1664 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1664 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result967 := _t1664
											if deconstruct_result967 != nil {
												unwrapped968 := deconstruct_result967
												p.pretty_decimal_type(unwrapped968)
											} else {
												_dollar_dollar := msg
												var _t1665 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1665 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result965 := _t1665
												if deconstruct_result965 != nil {
													unwrapped966 := deconstruct_result965
													p.pretty_boolean_type(unwrapped966)
												} else {
													_dollar_dollar := msg
													var _t1666 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1666 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result963 := _t1666
													if deconstruct_result963 != nil {
														unwrapped964 := deconstruct_result963
														p.pretty_int32_type(unwrapped964)
													} else {
														_dollar_dollar := msg
														var _t1667 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1667 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result961 := _t1667
														if deconstruct_result961 != nil {
															unwrapped962 := deconstruct_result961
															p.pretty_float32_type(unwrapped962)
														} else {
															_dollar_dollar := msg
															var _t1668 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1668 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result959 := _t1668
															if deconstruct_result959 != nil {
																unwrapped960 := deconstruct_result959
																p.pretty_uint32_type(unwrapped960)
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
	fields988 := msg
	_ = fields988
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields989 := msg
	_ = fields989
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields990 := msg
	_ = fields990
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields991 := msg
	_ = fields991
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields992 := msg
	_ = fields992
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields993 := msg
	_ = fields993
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields994 := msg
	_ = fields994
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields995 := msg
	_ = fields995
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields996 := msg
	_ = fields996
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		_dollar_dollar := msg
		fields997 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields998 := fields997
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field999 := unwrapped_fields998[0].(int64)
		p.write(fmt.Sprintf("%d", field999))
		p.newline()
		field1000 := unwrapped_fields998[1].(int64)
		p.write(fmt.Sprintf("%d", field1000))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1002 := msg
	_ = fields1002
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1003 := msg
	_ = fields1003
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1004 := msg
	_ = fields1004
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1005 := msg
	_ = fields1005
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		fields1006 := msg
		p.write("|")
		if !(len(fields1006) == 0) {
			p.write(" ")
			for i1008, elem1007 := range fields1006 {
				if (i1008 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1007)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1036 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1036 != nil {
		p.write(*flat1036)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1669 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1669 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1034 := _t1669
		if deconstruct_result1034 != nil {
			unwrapped1035 := deconstruct_result1034
			p.pretty_true(unwrapped1035)
		} else {
			_dollar_dollar := msg
			var _t1670 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1670 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1032 := _t1670
			if deconstruct_result1032 != nil {
				unwrapped1033 := deconstruct_result1032
				p.pretty_false(unwrapped1033)
			} else {
				_dollar_dollar := msg
				var _t1671 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1671 = _dollar_dollar.GetExists()
				}
				deconstruct_result1030 := _t1671
				if deconstruct_result1030 != nil {
					unwrapped1031 := deconstruct_result1030
					p.pretty_exists(unwrapped1031)
				} else {
					_dollar_dollar := msg
					var _t1672 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1672 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1028 := _t1672
					if deconstruct_result1028 != nil {
						unwrapped1029 := deconstruct_result1028
						p.pretty_reduce(unwrapped1029)
					} else {
						_dollar_dollar := msg
						var _t1673 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1673 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1026 := _t1673
						if deconstruct_result1026 != nil {
							unwrapped1027 := deconstruct_result1026
							p.pretty_conjunction(unwrapped1027)
						} else {
							_dollar_dollar := msg
							var _t1674 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1674 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1024 := _t1674
							if deconstruct_result1024 != nil {
								unwrapped1025 := deconstruct_result1024
								p.pretty_disjunction(unwrapped1025)
							} else {
								_dollar_dollar := msg
								var _t1675 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1675 = _dollar_dollar.GetNot()
								}
								deconstruct_result1022 := _t1675
								if deconstruct_result1022 != nil {
									unwrapped1023 := deconstruct_result1022
									p.pretty_not(unwrapped1023)
								} else {
									_dollar_dollar := msg
									var _t1676 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1676 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1020 := _t1676
									if deconstruct_result1020 != nil {
										unwrapped1021 := deconstruct_result1020
										p.pretty_ffi(unwrapped1021)
									} else {
										_dollar_dollar := msg
										var _t1677 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1677 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1018 := _t1677
										if deconstruct_result1018 != nil {
											unwrapped1019 := deconstruct_result1018
											p.pretty_atom(unwrapped1019)
										} else {
											_dollar_dollar := msg
											var _t1678 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1678 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1016 := _t1678
											if deconstruct_result1016 != nil {
												unwrapped1017 := deconstruct_result1016
												p.pretty_pragma(unwrapped1017)
											} else {
												_dollar_dollar := msg
												var _t1679 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1679 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1014 := _t1679
												if deconstruct_result1014 != nil {
													unwrapped1015 := deconstruct_result1014
													p.pretty_primitive(unwrapped1015)
												} else {
													_dollar_dollar := msg
													var _t1680 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1680 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1012 := _t1680
													if deconstruct_result1012 != nil {
														unwrapped1013 := deconstruct_result1012
														p.pretty_rel_atom(unwrapped1013)
													} else {
														_dollar_dollar := msg
														var _t1681 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1681 = _dollar_dollar.GetCast()
														}
														deconstruct_result1010 := _t1681
														if deconstruct_result1010 != nil {
															unwrapped1011 := deconstruct_result1010
															p.pretty_cast(unwrapped1011)
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
	fields1037 := msg
	_ = fields1037
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1038 := msg
	_ = fields1038
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1043 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1043 != nil {
		p.write(*flat1043)
		return nil
	} else {
		_dollar_dollar := msg
		_t1682 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1039 := []interface{}{_t1682, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1040 := fields1039
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1041 := unwrapped_fields1040[0].([]interface{})
		p.pretty_bindings(field1041)
		p.newline()
		field1042 := unwrapped_fields1040[1].(*pb.Formula)
		p.pretty_formula(field1042)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1049 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		_dollar_dollar := msg
		fields1044 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1045 := fields1044
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1046 := unwrapped_fields1045[0].(*pb.Abstraction)
		p.pretty_abstraction(field1046)
		p.newline()
		field1047 := unwrapped_fields1045[1].(*pb.Abstraction)
		p.pretty_abstraction(field1047)
		p.newline()
		field1048 := unwrapped_fields1045[2].([]*pb.Term)
		p.pretty_terms(field1048)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1053 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1053 != nil {
		p.write(*flat1053)
		return nil
	} else {
		fields1050 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1050) == 0) {
			p.newline()
			for i1052, elem1051 := range fields1050 {
				if (i1052 > 0) {
					p.newline()
				}
				p.pretty_term(elem1051)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1058 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1058 != nil {
		p.write(*flat1058)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1683 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1683 = _dollar_dollar.GetVar()
		}
		deconstruct_result1056 := _t1683
		if deconstruct_result1056 != nil {
			unwrapped1057 := deconstruct_result1056
			p.pretty_var(unwrapped1057)
		} else {
			_dollar_dollar := msg
			var _t1684 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1684 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1054 := _t1684
			if deconstruct_result1054 != nil {
				unwrapped1055 := deconstruct_result1054
				p.pretty_value(unwrapped1055)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1061 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1061 != nil {
		p.write(*flat1061)
		return nil
	} else {
		_dollar_dollar := msg
		fields1059 := _dollar_dollar.GetName()
		unwrapped_fields1060 := fields1059
		p.write(unwrapped_fields1060)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1087 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1087 != nil {
		p.write(*flat1087)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1685 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1685 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1085 := _t1685
		if deconstruct_result1085 != nil {
			unwrapped1086 := deconstruct_result1085
			p.pretty_date(unwrapped1086)
		} else {
			_dollar_dollar := msg
			var _t1686 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1686 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1083 := _t1686
			if deconstruct_result1083 != nil {
				unwrapped1084 := deconstruct_result1083
				p.pretty_datetime(unwrapped1084)
			} else {
				_dollar_dollar := msg
				var _t1687 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1687 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1081 := _t1687
				if deconstruct_result1081 != nil {
					unwrapped1082 := *deconstruct_result1081
					p.write(p.formatStringValue(unwrapped1082))
				} else {
					_dollar_dollar := msg
					var _t1688 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1688 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1079 := _t1688
					if deconstruct_result1079 != nil {
						unwrapped1080 := *deconstruct_result1079
						p.write(fmt.Sprintf("%di32", unwrapped1080))
					} else {
						_dollar_dollar := msg
						var _t1689 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1689 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1077 := _t1689
						if deconstruct_result1077 != nil {
							unwrapped1078 := *deconstruct_result1077
							p.write(fmt.Sprintf("%d", unwrapped1078))
						} else {
							_dollar_dollar := msg
							var _t1690 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1690 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1075 := _t1690
							if deconstruct_result1075 != nil {
								unwrapped1076 := *deconstruct_result1075
								p.write(formatFloat32(unwrapped1076))
							} else {
								_dollar_dollar := msg
								var _t1691 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1691 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1073 := _t1691
								if deconstruct_result1073 != nil {
									unwrapped1074 := *deconstruct_result1073
									p.write(formatFloat64(unwrapped1074))
								} else {
									_dollar_dollar := msg
									var _t1692 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1692 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1071 := _t1692
									if deconstruct_result1071 != nil {
										unwrapped1072 := *deconstruct_result1071
										p.write(fmt.Sprintf("%du32", unwrapped1072))
									} else {
										_dollar_dollar := msg
										var _t1693 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1693 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1069 := _t1693
										if deconstruct_result1069 != nil {
											unwrapped1070 := deconstruct_result1069
											p.write(p.formatUint128(unwrapped1070))
										} else {
											_dollar_dollar := msg
											var _t1694 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1694 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1067 := _t1694
											if deconstruct_result1067 != nil {
												unwrapped1068 := deconstruct_result1067
												p.write(p.formatInt128(unwrapped1068))
											} else {
												_dollar_dollar := msg
												var _t1695 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1695 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1065 := _t1695
												if deconstruct_result1065 != nil {
													unwrapped1066 := deconstruct_result1065
													p.write(p.formatDecimal(unwrapped1066))
												} else {
													_dollar_dollar := msg
													var _t1696 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1696 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1063 := _t1696
													if deconstruct_result1063 != nil {
														unwrapped1064 := *deconstruct_result1063
														p.pretty_boolean_value(unwrapped1064)
													} else {
														fields1062 := msg
														_ = fields1062
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
	flat1093 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		_dollar_dollar := msg
		fields1088 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1089 := fields1088
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1090 := unwrapped_fields1089[0].(int64)
		p.write(fmt.Sprintf("%d", field1090))
		p.newline()
		field1091 := unwrapped_fields1089[1].(int64)
		p.write(fmt.Sprintf("%d", field1091))
		p.newline()
		field1092 := unwrapped_fields1089[2].(int64)
		p.write(fmt.Sprintf("%d", field1092))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1104 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1104 != nil {
		p.write(*flat1104)
		return nil
	} else {
		_dollar_dollar := msg
		fields1094 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1095 := fields1094
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1096 := unwrapped_fields1095[0].(int64)
		p.write(fmt.Sprintf("%d", field1096))
		p.newline()
		field1097 := unwrapped_fields1095[1].(int64)
		p.write(fmt.Sprintf("%d", field1097))
		p.newline()
		field1098 := unwrapped_fields1095[2].(int64)
		p.write(fmt.Sprintf("%d", field1098))
		p.newline()
		field1099 := unwrapped_fields1095[3].(int64)
		p.write(fmt.Sprintf("%d", field1099))
		p.newline()
		field1100 := unwrapped_fields1095[4].(int64)
		p.write(fmt.Sprintf("%d", field1100))
		p.newline()
		field1101 := unwrapped_fields1095[5].(int64)
		p.write(fmt.Sprintf("%d", field1101))
		field1102 := unwrapped_fields1095[6].(*int64)
		if field1102 != nil {
			p.newline()
			opt_val1103 := *field1102
			p.write(fmt.Sprintf("%d", opt_val1103))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		_dollar_dollar := msg
		fields1105 := _dollar_dollar.GetArgs()
		unwrapped_fields1106 := fields1105
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1106) == 0) {
			p.newline()
			for i1108, elem1107 := range unwrapped_fields1106 {
				if (i1108 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1107)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_dollar_dollar := msg
		fields1110 := _dollar_dollar.GetArgs()
		unwrapped_fields1111 := fields1110
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1111) == 0) {
			p.newline()
			for i1113, elem1112 := range unwrapped_fields1111 {
				if (i1113 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1112)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1117 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		_dollar_dollar := msg
		fields1115 := _dollar_dollar.GetArg()
		unwrapped_fields1116 := fields1115
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1116)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		fields1118 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1119 := fields1118
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1120 := unwrapped_fields1119[0].(string)
		p.pretty_name(field1120)
		p.newline()
		field1121 := unwrapped_fields1119[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1121)
		p.newline()
		field1122 := unwrapped_fields1119[2].([]*pb.Term)
		p.pretty_terms(field1122)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		fields1124 := msg
		p.write(":")
		p.write(fields1124)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1129 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		fields1126 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1126) == 0) {
			p.newline()
			for i1128, elem1127 := range fields1126 {
				if (i1128 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1127)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1136 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1136 != nil {
		p.write(*flat1136)
		return nil
	} else {
		_dollar_dollar := msg
		fields1130 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1131 := fields1130
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1132 := unwrapped_fields1131[0].(*pb.RelationId)
		p.pretty_relation_id(field1132)
		field1133 := unwrapped_fields1131[1].([]*pb.Term)
		if !(len(field1133) == 0) {
			p.newline()
			for i1135, elem1134 := range field1133 {
				if (i1135 > 0) {
					p.newline()
				}
				p.pretty_term(elem1134)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		fields1137 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1138 := fields1137
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1139 := unwrapped_fields1138[0].(string)
		p.pretty_name(field1139)
		field1140 := unwrapped_fields1138[1].([]*pb.Term)
		if !(len(field1140) == 0) {
			p.newline()
			for i1142, elem1141 := range field1140 {
				if (i1142 > 0) {
					p.newline()
				}
				p.pretty_term(elem1141)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1159 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1159 != nil {
		p.write(*flat1159)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1697 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1158 := _t1697
		if guard_result1158 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1698 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1698 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1157 := _t1698
			if guard_result1157 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1699 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1699 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1156 := _t1699
				if guard_result1156 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1700 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1700 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1155 := _t1700
					if guard_result1155 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1701 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1701 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1154 := _t1701
						if guard_result1154 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1702 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1702 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1153 := _t1702
							if guard_result1153 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1703 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1703 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1152 := _t1703
								if guard_result1152 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1704 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1704 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1151 := _t1704
									if guard_result1151 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1705 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1705 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1150 := _t1705
										if guard_result1150 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1144 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1145 := fields1144
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1146 := unwrapped_fields1145[0].(string)
											p.pretty_name(field1146)
											field1147 := unwrapped_fields1145[1].([]*pb.RelTerm)
											if !(len(field1147) == 0) {
												p.newline()
												for i1149, elem1148 := range field1147 {
													if (i1149 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1148)
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
	flat1164 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1706 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1160 := _t1706
		unwrapped_fields1161 := fields1160
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1162 := unwrapped_fields1161[0].(*pb.Term)
		p.pretty_term(field1162)
		p.newline()
		field1163 := unwrapped_fields1161[1].(*pb.Term)
		p.pretty_term(field1163)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1169 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1169 != nil {
		p.write(*flat1169)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1707 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1165 := _t1707
		unwrapped_fields1166 := fields1165
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1167 := unwrapped_fields1166[0].(*pb.Term)
		p.pretty_term(field1167)
		p.newline()
		field1168 := unwrapped_fields1166[1].(*pb.Term)
		p.pretty_term(field1168)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1708 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1708 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1170 := _t1708
		unwrapped_fields1171 := fields1170
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1172 := unwrapped_fields1171[0].(*pb.Term)
		p.pretty_term(field1172)
		p.newline()
		field1173 := unwrapped_fields1171[1].(*pb.Term)
		p.pretty_term(field1173)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1709 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1709 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1175 := _t1709
		unwrapped_fields1176 := fields1175
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1177 := unwrapped_fields1176[0].(*pb.Term)
		p.pretty_term(field1177)
		p.newline()
		field1178 := unwrapped_fields1176[1].(*pb.Term)
		p.pretty_term(field1178)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1710 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1710 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1180 := _t1710
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(*pb.Term)
		p.pretty_term(field1182)
		p.newline()
		field1183 := unwrapped_fields1181[1].(*pb.Term)
		p.pretty_term(field1183)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1711 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1185 := _t1711
		unwrapped_fields1186 := fields1185
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1187 := unwrapped_fields1186[0].(*pb.Term)
		p.pretty_term(field1187)
		p.newline()
		field1188 := unwrapped_fields1186[1].(*pb.Term)
		p.pretty_term(field1188)
		p.newline()
		field1189 := unwrapped_fields1186[2].(*pb.Term)
		p.pretty_term(field1189)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1712 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1191 := _t1712
		unwrapped_fields1192 := fields1191
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1193 := unwrapped_fields1192[0].(*pb.Term)
		p.pretty_term(field1193)
		p.newline()
		field1194 := unwrapped_fields1192[1].(*pb.Term)
		p.pretty_term(field1194)
		p.newline()
		field1195 := unwrapped_fields1192[2].(*pb.Term)
		p.pretty_term(field1195)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1713 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1197 := _t1713
		unwrapped_fields1198 := fields1197
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1199 := unwrapped_fields1198[0].(*pb.Term)
		p.pretty_term(field1199)
		p.newline()
		field1200 := unwrapped_fields1198[1].(*pb.Term)
		p.pretty_term(field1200)
		p.newline()
		field1201 := unwrapped_fields1198[2].(*pb.Term)
		p.pretty_term(field1201)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1714 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1714 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1203 := _t1714
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1205 := unwrapped_fields1204[0].(*pb.Term)
		p.pretty_term(field1205)
		p.newline()
		field1206 := unwrapped_fields1204[1].(*pb.Term)
		p.pretty_term(field1206)
		p.newline()
		field1207 := unwrapped_fields1204[2].(*pb.Term)
		p.pretty_term(field1207)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1213 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1213 != nil {
		p.write(*flat1213)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1715 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1715 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1211 := _t1715
		if deconstruct_result1211 != nil {
			unwrapped1212 := deconstruct_result1211
			p.pretty_specialized_value(unwrapped1212)
		} else {
			_dollar_dollar := msg
			var _t1716 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1716 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1209 := _t1716
			if deconstruct_result1209 != nil {
				unwrapped1210 := deconstruct_result1209
				p.pretty_term(unwrapped1210)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		fields1214 := msg
		p.write("#")
		p.pretty_raw_value(fields1214)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1222 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1222 != nil {
		p.write(*flat1222)
		return nil
	} else {
		_dollar_dollar := msg
		fields1216 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1218 := unwrapped_fields1217[0].(string)
		p.pretty_name(field1218)
		field1219 := unwrapped_fields1217[1].([]*pb.RelTerm)
		if !(len(field1219) == 0) {
			p.newline()
			for i1221, elem1220 := range field1219 {
				if (i1221 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1220)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		fields1223 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1224 := fields1223
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1225 := unwrapped_fields1224[0].(*pb.Term)
		p.pretty_term(field1225)
		p.newline()
		field1226 := unwrapped_fields1224[1].(*pb.Term)
		p.pretty_term(field1226)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		fields1228 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1228) == 0) {
			p.newline()
			for i1230, elem1229 := range fields1228 {
				if (i1230 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1229)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1238 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		_dollar_dollar := msg
		fields1232 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1233 := fields1232
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1234 := unwrapped_fields1233[0].(string)
		p.pretty_name(field1234)
		field1235 := unwrapped_fields1233[1].([]*pb.Value)
		if !(len(field1235) == 0) {
			p.newline()
			for i1237, elem1236 := range field1235 {
				if (i1237 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1236)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1247 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1717 = _dollar_dollar.GetAttrs()
		}
		fields1239 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1717}
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1241 := unwrapped_fields1240[0].([]*pb.RelationId)
		if !(len(field1241) == 0) {
			p.newline()
			for i1243, elem1242 := range field1241 {
				if (i1243 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1242)
			}
		}
		p.newline()
		field1244 := unwrapped_fields1240[1].(*pb.Script)
		p.pretty_script(field1244)
		field1245 := unwrapped_fields1240[2].([]*pb.Attribute)
		if field1245 != nil {
			p.newline()
			opt_val1246 := field1245
			p.pretty_attrs(opt_val1246)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_dollar_dollar := msg
		fields1248 := _dollar_dollar.GetConstructs()
		unwrapped_fields1249 := fields1248
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1249) == 0) {
			p.newline()
			for i1251, elem1250 := range unwrapped_fields1249 {
				if (i1251 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1250)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1718 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1718 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1255 := _t1718
		if deconstruct_result1255 != nil {
			unwrapped1256 := deconstruct_result1255
			p.pretty_loop(unwrapped1256)
		} else {
			_dollar_dollar := msg
			var _t1719 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1719 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1253 := _t1719
			if deconstruct_result1253 != nil {
				unwrapped1254 := deconstruct_result1253
				p.pretty_instruction(unwrapped1254)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1720 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1720 = _dollar_dollar.GetAttrs()
		}
		fields1258 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1720}
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1260 := unwrapped_fields1259[0].([]*pb.Instruction)
		p.pretty_init(field1260)
		p.newline()
		field1261 := unwrapped_fields1259[1].(*pb.Script)
		p.pretty_script(field1261)
		field1262 := unwrapped_fields1259[2].([]*pb.Attribute)
		if field1262 != nil {
			p.newline()
			opt_val1263 := field1262
			p.pretty_attrs(opt_val1263)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1268 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1268 != nil {
		p.write(*flat1268)
		return nil
	} else {
		fields1265 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1265) == 0) {
			p.newline()
			for i1267, elem1266 := range fields1265 {
				if (i1267 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1266)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1279 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1279 != nil {
		p.write(*flat1279)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1721 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1277 := _t1721
		if deconstruct_result1277 != nil {
			unwrapped1278 := deconstruct_result1277
			p.pretty_assign(unwrapped1278)
		} else {
			_dollar_dollar := msg
			var _t1722 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1722 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1275 := _t1722
			if deconstruct_result1275 != nil {
				unwrapped1276 := deconstruct_result1275
				p.pretty_upsert(unwrapped1276)
			} else {
				_dollar_dollar := msg
				var _t1723 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1723 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1273 := _t1723
				if deconstruct_result1273 != nil {
					unwrapped1274 := deconstruct_result1273
					p.pretty_break(unwrapped1274)
				} else {
					_dollar_dollar := msg
					var _t1724 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1724 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1271 := _t1724
					if deconstruct_result1271 != nil {
						unwrapped1272 := deconstruct_result1271
						p.pretty_monoid_def(unwrapped1272)
					} else {
						_dollar_dollar := msg
						var _t1725 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1725 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1269 := _t1725
						if deconstruct_result1269 != nil {
							unwrapped1270 := deconstruct_result1269
							p.pretty_monus_def(unwrapped1270)
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
	flat1286 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1726 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1726 = _dollar_dollar.GetAttrs()
		}
		fields1280 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1726}
		unwrapped_fields1281 := fields1280
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1282 := unwrapped_fields1281[0].(*pb.RelationId)
		p.pretty_relation_id(field1282)
		p.newline()
		field1283 := unwrapped_fields1281[1].(*pb.Abstraction)
		p.pretty_abstraction(field1283)
		field1284 := unwrapped_fields1281[2].([]*pb.Attribute)
		if field1284 != nil {
			p.newline()
			opt_val1285 := field1284
			p.pretty_attrs(opt_val1285)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1293 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1293 != nil {
		p.write(*flat1293)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1727 = _dollar_dollar.GetAttrs()
		}
		fields1287 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1727}
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1289 := unwrapped_fields1288[0].(*pb.RelationId)
		p.pretty_relation_id(field1289)
		p.newline()
		field1290 := unwrapped_fields1288[1].([]interface{})
		p.pretty_abstraction_with_arity(field1290)
		field1291 := unwrapped_fields1288[2].([]*pb.Attribute)
		if field1291 != nil {
			p.newline()
			opt_val1292 := field1291
			p.pretty_attrs(opt_val1292)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1298 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1298 != nil {
		p.write(*flat1298)
		return nil
	} else {
		_dollar_dollar := msg
		_t1728 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1294 := []interface{}{_t1728, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1295 := fields1294
		p.write("(")
		p.indent()
		field1296 := unwrapped_fields1295[0].([]interface{})
		p.pretty_bindings(field1296)
		p.newline()
		field1297 := unwrapped_fields1295[1].(*pb.Formula)
		p.pretty_formula(field1297)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1305 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1305 != nil {
		p.write(*flat1305)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1729 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1729 = _dollar_dollar.GetAttrs()
		}
		fields1299 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1729}
		unwrapped_fields1300 := fields1299
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1301 := unwrapped_fields1300[0].(*pb.RelationId)
		p.pretty_relation_id(field1301)
		p.newline()
		field1302 := unwrapped_fields1300[1].(*pb.Abstraction)
		p.pretty_abstraction(field1302)
		field1303 := unwrapped_fields1300[2].([]*pb.Attribute)
		if field1303 != nil {
			p.newline()
			opt_val1304 := field1303
			p.pretty_attrs(opt_val1304)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1313 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1313 != nil {
		p.write(*flat1313)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1730 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1730 = _dollar_dollar.GetAttrs()
		}
		fields1306 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1730}
		unwrapped_fields1307 := fields1306
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1308 := unwrapped_fields1307[0].(*pb.Monoid)
		p.pretty_monoid(field1308)
		p.newline()
		field1309 := unwrapped_fields1307[1].(*pb.RelationId)
		p.pretty_relation_id(field1309)
		p.newline()
		field1310 := unwrapped_fields1307[2].([]interface{})
		p.pretty_abstraction_with_arity(field1310)
		field1311 := unwrapped_fields1307[3].([]*pb.Attribute)
		if field1311 != nil {
			p.newline()
			opt_val1312 := field1311
			p.pretty_attrs(opt_val1312)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1322 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1731 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1320 := _t1731
		if deconstruct_result1320 != nil {
			unwrapped1321 := deconstruct_result1320
			p.pretty_or_monoid(unwrapped1321)
		} else {
			_dollar_dollar := msg
			var _t1732 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1732 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1318 := _t1732
			if deconstruct_result1318 != nil {
				unwrapped1319 := deconstruct_result1318
				p.pretty_min_monoid(unwrapped1319)
			} else {
				_dollar_dollar := msg
				var _t1733 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1733 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1316 := _t1733
				if deconstruct_result1316 != nil {
					unwrapped1317 := deconstruct_result1316
					p.pretty_max_monoid(unwrapped1317)
				} else {
					_dollar_dollar := msg
					var _t1734 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1734 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1314 := _t1734
					if deconstruct_result1314 != nil {
						unwrapped1315 := deconstruct_result1314
						p.pretty_sum_monoid(unwrapped1315)
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
	fields1323 := msg
	_ = fields1323
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1326 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1326 != nil {
		p.write(*flat1326)
		return nil
	} else {
		_dollar_dollar := msg
		fields1324 := _dollar_dollar.GetType()
		unwrapped_fields1325 := fields1324
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1325)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		fields1327 := _dollar_dollar.GetType()
		unwrapped_fields1328 := fields1327
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1328)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1332 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1332 != nil {
		p.write(*flat1332)
		return nil
	} else {
		_dollar_dollar := msg
		fields1330 := _dollar_dollar.GetType()
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1331)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1340 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1340 != nil {
		p.write(*flat1340)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1735 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1735 = _dollar_dollar.GetAttrs()
		}
		fields1333 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1735}
		unwrapped_fields1334 := fields1333
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1335 := unwrapped_fields1334[0].(*pb.Monoid)
		p.pretty_monoid(field1335)
		p.newline()
		field1336 := unwrapped_fields1334[1].(*pb.RelationId)
		p.pretty_relation_id(field1336)
		p.newline()
		field1337 := unwrapped_fields1334[2].([]interface{})
		p.pretty_abstraction_with_arity(field1337)
		field1338 := unwrapped_fields1334[3].([]*pb.Attribute)
		if field1338 != nil {
			p.newline()
			opt_val1339 := field1338
			p.pretty_attrs(opt_val1339)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1347 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1347 != nil {
		p.write(*flat1347)
		return nil
	} else {
		_dollar_dollar := msg
		fields1341 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1342 := fields1341
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1343 := unwrapped_fields1342[0].(*pb.RelationId)
		p.pretty_relation_id(field1343)
		p.newline()
		field1344 := unwrapped_fields1342[1].(*pb.Abstraction)
		p.pretty_abstraction(field1344)
		p.newline()
		field1345 := unwrapped_fields1342[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1345)
		p.newline()
		field1346 := unwrapped_fields1342[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1346)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1351 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1351 != nil {
		p.write(*flat1351)
		return nil
	} else {
		fields1348 := msg
		p.write("(")
		p.write("keys")
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

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1355 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1355 != nil {
		p.write(*flat1355)
		return nil
	} else {
		fields1352 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1352) == 0) {
			p.newline()
			for i1354, elem1353 := range fields1352 {
				if (i1354 > 0) {
					p.newline()
				}
				p.pretty_var(elem1353)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1364 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1364 != nil {
		p.write(*flat1364)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1736 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1736 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1362 := _t1736
		if deconstruct_result1362 != nil {
			unwrapped1363 := deconstruct_result1362
			p.pretty_edb(unwrapped1363)
		} else {
			_dollar_dollar := msg
			var _t1737 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1737 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1360 := _t1737
			if deconstruct_result1360 != nil {
				unwrapped1361 := deconstruct_result1360
				p.pretty_betree_relation(unwrapped1361)
			} else {
				_dollar_dollar := msg
				var _t1738 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1738 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1358 := _t1738
				if deconstruct_result1358 != nil {
					unwrapped1359 := deconstruct_result1358
					p.pretty_csv_data(unwrapped1359)
				} else {
					_dollar_dollar := msg
					var _t1739 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1739 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1356 := _t1739
					if deconstruct_result1356 != nil {
						unwrapped1357 := deconstruct_result1356
						p.pretty_iceberg_data(unwrapped1357)
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
	flat1370 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1370 != nil {
		p.write(*flat1370)
		return nil
	} else {
		_dollar_dollar := msg
		fields1365 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1366 := fields1365
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1367 := unwrapped_fields1366[0].(*pb.RelationId)
		p.pretty_relation_id(field1367)
		p.newline()
		field1368 := unwrapped_fields1366[1].([]string)
		p.pretty_edb_path(field1368)
		p.newline()
		field1369 := unwrapped_fields1366[2].([]*pb.Type)
		p.pretty_edb_types(field1369)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1374 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
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
			p.write(p.formatStringValue(elem1372))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1378 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1378 != nil {
		p.write(*flat1378)
		return nil
	} else {
		fields1375 := msg
		p.write("[")
		p.indent()
		for i1377, elem1376 := range fields1375 {
			if (i1377 > 0) {
				p.newline()
			}
			p.pretty_type(elem1376)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1383 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1383 != nil {
		p.write(*flat1383)
		return nil
	} else {
		_dollar_dollar := msg
		fields1379 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1380 := fields1379
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1381 := unwrapped_fields1380[0].(*pb.RelationId)
		p.pretty_relation_id(field1381)
		p.newline()
		field1382 := unwrapped_fields1380[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1382)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1389 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		_dollar_dollar := msg
		_t1740 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1384 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1740}
		unwrapped_fields1385 := fields1384
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1386 := unwrapped_fields1385[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1386)
		p.newline()
		field1387 := unwrapped_fields1385[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1387)
		p.newline()
		field1388 := unwrapped_fields1385[2].([][]interface{})
		p.pretty_config_dict(field1388)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1393 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1393 != nil {
		p.write(*flat1393)
		return nil
	} else {
		fields1390 := msg
		p.write("(")
		p.write("key_types")
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

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1397 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1397 != nil {
		p.write(*flat1397)
		return nil
	} else {
		fields1394 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1394) == 0) {
			p.newline()
			for i1396, elem1395 := range fields1394 {
				if (i1396 > 0) {
					p.newline()
				}
				p.pretty_type(elem1395)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1404 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1404 != nil {
		p.write(*flat1404)
		return nil
	} else {
		_dollar_dollar := msg
		fields1398 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1399 := fields1398
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1400 := unwrapped_fields1399[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1400)
		p.newline()
		field1401 := unwrapped_fields1399[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1401)
		p.newline()
		field1402 := unwrapped_fields1399[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1402)
		p.newline()
		field1403 := unwrapped_fields1399[3].(string)
		p.pretty_csv_asof(field1403)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1411 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1411 != nil {
		p.write(*flat1411)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1741 = _dollar_dollar.GetPaths()
		}
		var _t1742 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1742 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1405 := []interface{}{_t1741, _t1742}
		unwrapped_fields1406 := fields1405
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1407 := unwrapped_fields1406[0].([]string)
		if field1407 != nil {
			p.newline()
			opt_val1408 := field1407
			p.pretty_csv_locator_paths(opt_val1408)
		}
		field1409 := unwrapped_fields1406[1].(*string)
		if field1409 != nil {
			p.newline()
			opt_val1410 := *field1409
			p.pretty_csv_locator_inline_data(opt_val1410)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1415 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1415 != nil {
		p.write(*flat1415)
		return nil
	} else {
		fields1412 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1412) == 0) {
			p.newline()
			for i1414, elem1413 := range fields1412 {
				if (i1414 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1413))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		fields1416 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1416))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1423 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		_dollar_dollar := msg
		_t1743 := p.deconstruct_csv_config(_dollar_dollar)
		_t1744 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1418 := []interface{}{_t1743, _t1744}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1420 := unwrapped_fields1419[0].([][]interface{})
		p.pretty_config_dict(field1420)
		field1421 := unwrapped_fields1419[1].([][]interface{})
		if field1421 != nil {
			p.newline()
			opt_val1422 := field1421
			p.pretty__storage_integration(opt_val1422)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1425 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		fields1424 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1424)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1429 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1429 != nil {
		p.write(*flat1429)
		return nil
	} else {
		fields1426 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1426) == 0) {
			p.newline()
			for i1428, elem1427 := range fields1426 {
				if (i1428 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1427)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1438 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1438 != nil {
		p.write(*flat1438)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1745 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1745 = _dollar_dollar.GetTargetId()
		}
		fields1430 := []interface{}{_dollar_dollar.GetColumnPath(), _t1745, _dollar_dollar.GetTypes()}
		unwrapped_fields1431 := fields1430
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1432 := unwrapped_fields1431[0].([]string)
		p.pretty_gnf_column_path(field1432)
		field1433 := unwrapped_fields1431[1].(*pb.RelationId)
		if field1433 != nil {
			p.newline()
			opt_val1434 := field1433
			p.pretty_relation_id(opt_val1434)
		}
		p.newline()
		p.write("[")
		field1435 := unwrapped_fields1431[2].([]*pb.Type)
		for i1437, elem1436 := range field1435 {
			if (i1437 > 0) {
				p.newline()
			}
			p.pretty_type(elem1436)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1445 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1445 != nil {
		p.write(*flat1445)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1746 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1746 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1443 := _t1746
		if deconstruct_result1443 != nil {
			unwrapped1444 := *deconstruct_result1443
			p.write(p.formatStringValue(unwrapped1444))
		} else {
			_dollar_dollar := msg
			var _t1747 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1747 = _dollar_dollar
			}
			deconstruct_result1439 := _t1747
			if deconstruct_result1439 != nil {
				unwrapped1440 := deconstruct_result1439
				p.write("[")
				p.indent()
				for i1442, elem1441 := range unwrapped1440 {
					if (i1442 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1441))
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
	flat1447 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1447 != nil {
		p.write(*flat1447)
		return nil
	} else {
		fields1446 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1446))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1458 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1458 != nil {
		p.write(*flat1458)
		return nil
	} else {
		_dollar_dollar := msg
		_t1748 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1749 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1448 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1748, _t1749, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1449 := fields1448
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1450 := unwrapped_fields1449[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1450)
		p.newline()
		field1451 := unwrapped_fields1449[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1451)
		p.newline()
		field1452 := unwrapped_fields1449[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1452)
		field1453 := unwrapped_fields1449[3].(*string)
		if field1453 != nil {
			p.newline()
			opt_val1454 := *field1453
			p.pretty_iceberg_from_snapshot(opt_val1454)
		}
		field1455 := unwrapped_fields1449[4].(*string)
		if field1455 != nil {
			p.newline()
			opt_val1456 := *field1455
			p.pretty_iceberg_to_snapshot(opt_val1456)
		}
		p.newline()
		field1457 := unwrapped_fields1449[5].(bool)
		p.pretty_boolean_value(field1457)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		_dollar_dollar := msg
		fields1459 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1460 := fields1459
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1461 := unwrapped_fields1460[0].(string)
		p.pretty_iceberg_locator_table_name(field1461)
		p.newline()
		field1462 := unwrapped_fields1460[1].([]string)
		p.pretty_iceberg_locator_namespace(field1462)
		p.newline()
		field1463 := unwrapped_fields1460[2].(string)
		p.pretty_iceberg_locator_warehouse(field1463)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1466 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1466 != nil {
		p.write(*flat1466)
		return nil
	} else {
		fields1465 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1465))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1470 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		fields1467 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1467) == 0) {
			p.newline()
			for i1469, elem1468 := range fields1467 {
				if (i1469 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1468))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		fields1471 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1471))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		_dollar_dollar := msg
		_t1750 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1473 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1750, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1474 := fields1473
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1475 := unwrapped_fields1474[0].(string)
		p.pretty_iceberg_catalog_uri(field1475)
		field1476 := unwrapped_fields1474[1].(*string)
		if field1476 != nil {
			p.newline()
			opt_val1477 := *field1476
			p.pretty_iceberg_catalog_config_scope(opt_val1477)
		}
		p.newline()
		field1478 := unwrapped_fields1474[2].([][]interface{})
		p.pretty_iceberg_properties(field1478)
		p.newline()
		field1479 := unwrapped_fields1474[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1479)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1482 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		fields1481 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1481))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		fields1483 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1483))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1485) == 0) {
			p.newline()
			for i1487, elem1486 := range fields1485 {
				if (i1487 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1486)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1493 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1493 != nil {
		p.write(*flat1493)
		return nil
	} else {
		_dollar_dollar := msg
		fields1489 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1490 := fields1489
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1491 := unwrapped_fields1490[0].(string)
		p.write(p.formatStringValue(field1491))
		p.newline()
		field1492 := unwrapped_fields1490[1].(string)
		p.write(p.formatStringValue(field1492))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1497 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1497 != nil {
		p.write(*flat1497)
		return nil
	} else {
		fields1494 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1494) == 0) {
			p.newline()
			for i1496, elem1495 := range fields1494 {
				if (i1496 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1495)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1502 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1502 != nil {
		p.write(*flat1502)
		return nil
	} else {
		_dollar_dollar := msg
		_t1751 := p.mask_secret_value(_dollar_dollar)
		fields1498 := []interface{}{_dollar_dollar[0].(string), _t1751}
		unwrapped_fields1499 := fields1498
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1500 := unwrapped_fields1499[0].(string)
		p.write(p.formatStringValue(field1500))
		p.newline()
		field1501 := unwrapped_fields1499[1].(string)
		p.write(p.formatStringValue(field1501))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1504 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		fields1503 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1503))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1506 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1506 != nil {
		p.write(*flat1506)
		return nil
	} else {
		fields1505 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1505))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1509 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1509 != nil {
		p.write(*flat1509)
		return nil
	} else {
		_dollar_dollar := msg
		fields1507 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1508 := fields1507
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1508)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1514 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1514 != nil {
		p.write(*flat1514)
		return nil
	} else {
		_dollar_dollar := msg
		fields1510 := _dollar_dollar.GetRelations()
		unwrapped_fields1511 := fields1510
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1511) == 0) {
			p.newline()
			for i1513, elem1512 := range unwrapped_fields1511 {
				if (i1513 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1512)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		_dollar_dollar := msg
		fields1515 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1516 := fields1515
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1517 := unwrapped_fields1516[0].([]string)
		p.pretty_edb_path(field1517)
		field1518 := unwrapped_fields1516[1].([]*pb.SnapshotMapping)
		if !(len(field1518) == 0) {
			p.newline()
			for i1520, elem1519 := range field1518 {
				if (i1520 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1519)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1526 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1526 != nil {
		p.write(*flat1526)
		return nil
	} else {
		_dollar_dollar := msg
		fields1522 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1523 := fields1522
		field1524 := unwrapped_fields1523[0].([]string)
		p.pretty_edb_path(field1524)
		p.write(" ")
		field1525 := unwrapped_fields1523[1].(*pb.RelationId)
		p.pretty_relation_id(field1525)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1530 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1530 != nil {
		p.write(*flat1530)
		return nil
	} else {
		fields1527 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1527) == 0) {
			p.newline()
			for i1529, elem1528 := range fields1527 {
				if (i1529 > 0) {
					p.newline()
				}
				p.pretty_read(elem1528)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1543 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1543 != nil {
		p.write(*flat1543)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1752 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1752 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1541 := _t1752
		if deconstruct_result1541 != nil {
			unwrapped1542 := deconstruct_result1541
			p.pretty_demand(unwrapped1542)
		} else {
			_dollar_dollar := msg
			var _t1753 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1753 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1539 := _t1753
			if deconstruct_result1539 != nil {
				unwrapped1540 := deconstruct_result1539
				p.pretty_output(unwrapped1540)
			} else {
				_dollar_dollar := msg
				var _t1754 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1754 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1537 := _t1754
				if deconstruct_result1537 != nil {
					unwrapped1538 := deconstruct_result1537
					p.pretty_what_if(unwrapped1538)
				} else {
					_dollar_dollar := msg
					var _t1755 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1755 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1535 := _t1755
					if deconstruct_result1535 != nil {
						unwrapped1536 := deconstruct_result1535
						p.pretty_abort(unwrapped1536)
					} else {
						_dollar_dollar := msg
						var _t1756 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1756 = _dollar_dollar.GetExport()
						}
						deconstruct_result1533 := _t1756
						if deconstruct_result1533 != nil {
							unwrapped1534 := deconstruct_result1533
							p.pretty_export(unwrapped1534)
						} else {
							_dollar_dollar := msg
							var _t1757 *pb.ExportOutput
							if hasProtoField(_dollar_dollar, "export_output") {
								_t1757 = _dollar_dollar.GetExportOutput()
							}
							deconstruct_result1531 := _t1757
							if deconstruct_result1531 != nil {
								unwrapped1532 := deconstruct_result1531
								p.pretty_export_output(unwrapped1532)
							} else {
								panic(ParseError{msg: "No matching rule for read"})
							}
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_demand(msg *pb.Demand) interface{} {
	flat1546 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1546 != nil {
		p.write(*flat1546)
		return nil
	} else {
		_dollar_dollar := msg
		fields1544 := _dollar_dollar.GetRelationId()
		unwrapped_fields1545 := fields1544
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1545)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1551 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1551 != nil {
		p.write(*flat1551)
		return nil
	} else {
		_dollar_dollar := msg
		fields1547 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1548 := fields1547
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1549 := unwrapped_fields1548[0].(string)
		p.pretty_name(field1549)
		p.newline()
		field1550 := unwrapped_fields1548[1].(*pb.RelationId)
		p.pretty_relation_id(field1550)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1556 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1556 != nil {
		p.write(*flat1556)
		return nil
	} else {
		_dollar_dollar := msg
		fields1552 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1553 := fields1552
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1554 := unwrapped_fields1553[0].(string)
		p.pretty_name(field1554)
		p.newline()
		field1555 := unwrapped_fields1553[1].(*pb.Epoch)
		p.pretty_epoch(field1555)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1562 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1562 != nil {
		p.write(*flat1562)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1758 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1758 = ptr(_dollar_dollar.GetName())
		}
		fields1557 := []interface{}{_t1758, _dollar_dollar.GetRelationId()}
		unwrapped_fields1558 := fields1557
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1559 := unwrapped_fields1558[0].(*string)
		if field1559 != nil {
			p.newline()
			opt_val1560 := *field1559
			p.pretty_name(opt_val1560)
		}
		p.newline()
		field1561 := unwrapped_fields1558[1].(*pb.RelationId)
		p.pretty_relation_id(field1561)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1759 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1759 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1565 := _t1759
		if deconstruct_result1565 != nil {
			unwrapped1566 := deconstruct_result1565
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1566)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1760 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1760 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1563 := _t1760
			if deconstruct_result1563 != nil {
				unwrapped1564 := deconstruct_result1563
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1564)
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
	flat1578 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1578 != nil {
		p.write(*flat1578)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1761 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1761 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1573 := _t1761
		if deconstruct_result1573 != nil {
			unwrapped1574 := deconstruct_result1573
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1575 := unwrapped1574[0].(string)
			p.pretty_export_csv_path(field1575)
			p.newline()
			field1576 := unwrapped1574[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1576)
			p.newline()
			field1577 := unwrapped1574[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1577)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1762 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1763 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1762 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1763}
			}
			deconstruct_result1568 := _t1762
			if deconstruct_result1568 != nil {
				unwrapped1569 := deconstruct_result1568
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1570 := unwrapped1569[0].(string)
				p.pretty_export_csv_path(field1570)
				p.newline()
				field1571 := unwrapped1569[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1571)
				p.newline()
				field1572 := unwrapped1569[2].([][]interface{})
				p.pretty_config_dict(field1572)
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
	flat1580 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1580 != nil {
		p.write(*flat1580)
		return nil
	} else {
		fields1579 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1579))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1587 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1587 != nil {
		p.write(*flat1587)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1764 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1764 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1583 := _t1764
		if deconstruct_result1583 != nil {
			unwrapped1584 := deconstruct_result1583
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1584) == 0) {
				p.newline()
				for i1586, elem1585 := range unwrapped1584 {
					if (i1586 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1585)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1765 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1765 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1581 := _t1765
			if deconstruct_result1581 != nil {
				unwrapped1582 := deconstruct_result1581
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1582)
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
	flat1592 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1592 != nil {
		p.write(*flat1592)
		return nil
	} else {
		_dollar_dollar := msg
		fields1588 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1589 := fields1588
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1590 := unwrapped_fields1589[0].(string)
		p.write(p.formatStringValue(field1590))
		p.newline()
		field1591 := unwrapped_fields1589[1].(*pb.RelationId)
		p.pretty_relation_id(field1591)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1596 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1596 != nil {
		p.write(*flat1596)
		return nil
	} else {
		fields1593 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1593) == 0) {
			p.newline()
			for i1595, elem1594 := range fields1593 {
				if (i1595 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1594)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1605 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1605 != nil {
		p.write(*flat1605)
		return nil
	} else {
		_dollar_dollar := msg
		_t1766 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1597 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1766}
		unwrapped_fields1598 := fields1597
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1599 := unwrapped_fields1598[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1599)
		p.newline()
		field1600 := unwrapped_fields1598[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1600)
		p.newline()
		field1601 := unwrapped_fields1598[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1601)
		p.newline()
		field1602 := unwrapped_fields1598[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1602)
		field1603 := unwrapped_fields1598[4].([][]interface{})
		if field1603 != nil {
			p.newline()
			opt_val1604 := field1603
			p.pretty_config_dict(opt_val1604)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1607 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1607 != nil {
		p.write(*flat1607)
		return nil
	} else {
		fields1606 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1606)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1611 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1611 != nil {
		p.write(*flat1611)
		return nil
	} else {
		fields1608 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1608) == 0) {
			p.newline()
			for i1610, elem1609 := range fields1608 {
				if (i1610 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1609)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_output(msg *pb.ExportOutput) interface{} {
	flat1616 := p.tryFlat(msg, func() { p.pretty_export_output(msg) })
	if flat1616 != nil {
		p.write(*flat1616)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1767 []interface{}
		if hasProtoField(_dollar_dollar, "csv") {
			_t1767 = []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetCsv()}
		}
		fields1612 := _t1767
		unwrapped_fields1613 := fields1612
		p.write("(")
		p.write("export_output")
		p.indentSexp()
		p.newline()
		field1614 := unwrapped_fields1613[0].(string)
		p.pretty_name(field1614)
		p.newline()
		field1615 := unwrapped_fields1613[1].(*pb.ExportCSVOutput)
		p.pretty_export_csv_output(field1615)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_output(msg *pb.ExportCSVOutput) interface{} {
	flat1621 := p.tryFlat(msg, func() { p.pretty_export_csv_output(msg) })
	if flat1621 != nil {
		p.write(*flat1621)
		return nil
	} else {
		_dollar_dollar := msg
		fields1617 := []interface{}{_dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		unwrapped_fields1618 := fields1617
		p.write("(")
		p.write("csv")
		p.indentSexp()
		p.newline()
		field1619 := unwrapped_fields1618[0].(*pb.ExportCSVSource)
		p.pretty_export_csv_source(field1619)
		p.newline()
		field1620 := unwrapped_fields1618[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1620)
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
		_t1819 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1819)
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

func (p *PrettyPrinter) pretty_storage_integration(msg *pb.StorageIntegration) interface{} {
	p.write("(storage_integration")
	p.indentSexp()
	p.newline()
	p.write(":provider ")
	p.write(p.formatStringValue(msg.GetProvider()))
	p.newline()
	p.write(":azure_sas_token ")
	p.write(p.formatStringValue(msg.GetAzureSasToken()))
	p.newline()
	p.write(":s3_region ")
	p.write(p.formatStringValue(msg.GetS3Region()))
	p.newline()
	p.write(":s3_access_key_id ")
	p.write(p.formatStringValue(msg.GetS3AccessKeyId()))
	p.newline()
	p.write(":s3_secret_access_key ")
	p.write(p.formatStringValue(msg.GetS3SecretAccessKey()))
	p.write(")")
	p.dedent()
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
	case *pb.ExportOutput:
		p.pretty_export_output(m)
	case *pb.ExportCSVOutput:
		p.pretty_export_csv_output(m)
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
	case *pb.StorageIntegration:
		p.pretty_storage_integration(m)
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
