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
	_t1764 := &pb.Value{}
	_t1764.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1764
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1765 := &pb.Value{}
	_t1765.Value = &pb.Value_IntValue{IntValue: v}
	return _t1765
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1766 := &pb.Value{}
	_t1766.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1766
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1767 := &pb.Value{}
	_t1767.Value = &pb.Value_StringValue{StringValue: v}
	return _t1767
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1768 := &pb.Value{}
	_t1768.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1768
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1769 := &pb.Value{}
	_t1769.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1769
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1770 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1770})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1771 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1771})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1772 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1772})
			}
		}
	}
	_t1773 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1773})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1774 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1774})
	_t1775 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1775})
	if msg.GetNewLine() != "" {
		_t1776 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1776})
	}
	_t1777 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1777})
	_t1778 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1778})
	_t1779 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1779})
	if msg.GetComment() != "" {
		_t1780 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1780})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1781 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1781})
	}
	_t1782 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1782})
	_t1783 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1783})
	_t1784 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1784})
	if msg.GetPartitionSizeMb() != 0 {
		_t1785 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1785})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1786 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1786
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1787 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1787})
	}
	if si.GetAzureSasToken() != "" {
		_t1788 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1788})
	}
	if si.GetS3Region() != "" {
		_t1789 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1789})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1790 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1790})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1791 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1791})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1792 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1792})
	_t1793 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1793})
	_t1794 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1794})
	_t1795 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1795})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1796 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1796})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1797 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1797})
		}
	}
	_t1798 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1798})
	_t1799 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1799})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1800 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1800})
	}
	if msg.Compression != nil {
		_t1801 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1801})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1802 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1802})
	}
	if msg.SyntaxMissingString != nil {
		_t1803 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1803})
	}
	if msg.SyntaxDelim != nil {
		_t1804 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1804})
	}
	if msg.SyntaxQuotechar != nil {
		_t1805 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1805})
	}
	if msg.SyntaxEscapechar != nil {
		_t1806 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1806})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1807 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1807
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1808 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1808
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1809 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1809
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1810 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1810})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1811 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1811})
	}
	if msg.GetCompression() != "" {
		_t1812 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1812})
	}
	var _t1813 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1813
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1814 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1814
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
	flat818 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat818 != nil {
		p.write(*flat818)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1618 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1618 = _dollar_dollar.GetConfigure()
		}
		var _t1619 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1619 = _dollar_dollar.GetSync()
		}
		fields809 := []interface{}{_t1618, _t1619, _dollar_dollar.GetEpochs()}
		unwrapped_fields810 := fields809
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field811 := unwrapped_fields810[0].(*pb.Configure)
		if field811 != nil {
			p.newline()
			opt_val812 := field811
			p.pretty_configure(opt_val812)
		}
		field813 := unwrapped_fields810[1].(*pb.Sync)
		if field813 != nil {
			p.newline()
			opt_val814 := field813
			p.pretty_sync(opt_val814)
		}
		field815 := unwrapped_fields810[2].([]*pb.Epoch)
		if !(len(field815) == 0) {
			p.newline()
			for i817, elem816 := range field815 {
				if (i817 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem816)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat821 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat821 != nil {
		p.write(*flat821)
		return nil
	} else {
		_dollar_dollar := msg
		_t1620 := p.deconstruct_configure(_dollar_dollar)
		fields819 := _t1620
		unwrapped_fields820 := fields819
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields820)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat825 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat825 != nil {
		p.write(*flat825)
		return nil
	} else {
		fields822 := msg
		p.write("{")
		p.indent()
		if !(len(fields822) == 0) {
			p.newline()
			for i824, elem823 := range fields822 {
				if (i824 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem823)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat830 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat830 != nil {
		p.write(*flat830)
		return nil
	} else {
		_dollar_dollar := msg
		fields826 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields827 := fields826
		p.write(":")
		field828 := unwrapped_fields827[0].(string)
		p.write(field828)
		p.write(" ")
		field829 := unwrapped_fields827[1].(*pb.Value)
		p.pretty_raw_value(field829)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat856 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat856 != nil {
		p.write(*flat856)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1621 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1621 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result854 := _t1621
		if deconstruct_result854 != nil {
			unwrapped855 := deconstruct_result854
			p.pretty_raw_date(unwrapped855)
		} else {
			_dollar_dollar := msg
			var _t1622 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1622 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result852 := _t1622
			if deconstruct_result852 != nil {
				unwrapped853 := deconstruct_result852
				p.pretty_raw_datetime(unwrapped853)
			} else {
				_dollar_dollar := msg
				var _t1623 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1623 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result850 := _t1623
				if deconstruct_result850 != nil {
					unwrapped851 := *deconstruct_result850
					p.write(p.formatStringValue(unwrapped851))
				} else {
					_dollar_dollar := msg
					var _t1624 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1624 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result848 := _t1624
					if deconstruct_result848 != nil {
						unwrapped849 := *deconstruct_result848
						p.write(fmt.Sprintf("%di32", unwrapped849))
					} else {
						_dollar_dollar := msg
						var _t1625 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1625 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result846 := _t1625
						if deconstruct_result846 != nil {
							unwrapped847 := *deconstruct_result846
							p.write(fmt.Sprintf("%d", unwrapped847))
						} else {
							_dollar_dollar := msg
							var _t1626 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1626 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result844 := _t1626
							if deconstruct_result844 != nil {
								unwrapped845 := *deconstruct_result844
								p.write(formatFloat32(unwrapped845))
							} else {
								_dollar_dollar := msg
								var _t1627 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1627 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result842 := _t1627
								if deconstruct_result842 != nil {
									unwrapped843 := *deconstruct_result842
									p.write(formatFloat64(unwrapped843))
								} else {
									_dollar_dollar := msg
									var _t1628 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1628 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result840 := _t1628
									if deconstruct_result840 != nil {
										unwrapped841 := *deconstruct_result840
										p.write(fmt.Sprintf("%du32", unwrapped841))
									} else {
										_dollar_dollar := msg
										var _t1629 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1629 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result838 := _t1629
										if deconstruct_result838 != nil {
											unwrapped839 := deconstruct_result838
											p.write(p.formatUint128(unwrapped839))
										} else {
											_dollar_dollar := msg
											var _t1630 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1630 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result836 := _t1630
											if deconstruct_result836 != nil {
												unwrapped837 := deconstruct_result836
												p.write(p.formatInt128(unwrapped837))
											} else {
												_dollar_dollar := msg
												var _t1631 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1631 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result834 := _t1631
												if deconstruct_result834 != nil {
													unwrapped835 := deconstruct_result834
													p.write(p.formatDecimal(unwrapped835))
												} else {
													_dollar_dollar := msg
													var _t1632 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1632 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result832 := _t1632
													if deconstruct_result832 != nil {
														unwrapped833 := *deconstruct_result832
														p.pretty_boolean_value(unwrapped833)
													} else {
														fields831 := msg
														_ = fields831
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
	flat862 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		_dollar_dollar := msg
		fields857 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields858 := fields857
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field859 := unwrapped_fields858[0].(int64)
		p.write(fmt.Sprintf("%d", field859))
		p.newline()
		field860 := unwrapped_fields858[1].(int64)
		p.write(fmt.Sprintf("%d", field860))
		p.newline()
		field861 := unwrapped_fields858[2].(int64)
		p.write(fmt.Sprintf("%d", field861))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat873 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat873 != nil {
		p.write(*flat873)
		return nil
	} else {
		_dollar_dollar := msg
		fields863 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields864 := fields863
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field865 := unwrapped_fields864[0].(int64)
		p.write(fmt.Sprintf("%d", field865))
		p.newline()
		field866 := unwrapped_fields864[1].(int64)
		p.write(fmt.Sprintf("%d", field866))
		p.newline()
		field867 := unwrapped_fields864[2].(int64)
		p.write(fmt.Sprintf("%d", field867))
		p.newline()
		field868 := unwrapped_fields864[3].(int64)
		p.write(fmt.Sprintf("%d", field868))
		p.newline()
		field869 := unwrapped_fields864[4].(int64)
		p.write(fmt.Sprintf("%d", field869))
		p.newline()
		field870 := unwrapped_fields864[5].(int64)
		p.write(fmt.Sprintf("%d", field870))
		field871 := unwrapped_fields864[6].(*int64)
		if field871 != nil {
			p.newline()
			opt_val872 := *field871
			p.write(fmt.Sprintf("%d", opt_val872))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1633 []interface{}
	if _dollar_dollar {
		_t1633 = []interface{}{}
	}
	deconstruct_result876 := _t1633
	if deconstruct_result876 != nil {
		unwrapped877 := deconstruct_result876
		_ = unwrapped877
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1634 []interface{}
		if !(_dollar_dollar) {
			_t1634 = []interface{}{}
		}
		deconstruct_result874 := _t1634
		if deconstruct_result874 != nil {
			unwrapped875 := deconstruct_result874
			_ = unwrapped875
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat882 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat882 != nil {
		p.write(*flat882)
		return nil
	} else {
		_dollar_dollar := msg
		fields878 := _dollar_dollar.GetFragments()
		unwrapped_fields879 := fields878
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields879) == 0) {
			p.newline()
			for i881, elem880 := range unwrapped_fields879 {
				if (i881 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem880)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat885 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat885 != nil {
		p.write(*flat885)
		return nil
	} else {
		_dollar_dollar := msg
		fields883 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields884 := fields883
		p.write(":")
		p.write(unwrapped_fields884)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat892 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat892 != nil {
		p.write(*flat892)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1635 = _dollar_dollar.GetWrites()
		}
		var _t1636 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1636 = _dollar_dollar.GetReads()
		}
		fields886 := []interface{}{_t1635, _t1636}
		unwrapped_fields887 := fields886
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field888 := unwrapped_fields887[0].([]*pb.Write)
		if field888 != nil {
			p.newline()
			opt_val889 := field888
			p.pretty_epoch_writes(opt_val889)
		}
		field890 := unwrapped_fields887[1].([]*pb.Read)
		if field890 != nil {
			p.newline()
			opt_val891 := field890
			p.pretty_epoch_reads(opt_val891)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat896 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		fields893 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields893) == 0) {
			p.newline()
			for i895, elem894 := range fields893 {
				if (i895 > 0) {
					p.newline()
				}
				p.pretty_write(elem894)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat905 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat905 != nil {
		p.write(*flat905)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1637 = _dollar_dollar.GetDefine()
		}
		deconstruct_result903 := _t1637
		if deconstruct_result903 != nil {
			unwrapped904 := deconstruct_result903
			p.pretty_define(unwrapped904)
		} else {
			_dollar_dollar := msg
			var _t1638 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1638 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result901 := _t1638
			if deconstruct_result901 != nil {
				unwrapped902 := deconstruct_result901
				p.pretty_undefine(unwrapped902)
			} else {
				_dollar_dollar := msg
				var _t1639 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1639 = _dollar_dollar.GetContext()
				}
				deconstruct_result899 := _t1639
				if deconstruct_result899 != nil {
					unwrapped900 := deconstruct_result899
					p.pretty_context(unwrapped900)
				} else {
					_dollar_dollar := msg
					var _t1640 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1640 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result897 := _t1640
					if deconstruct_result897 != nil {
						unwrapped898 := deconstruct_result897
						p.pretty_snapshot(unwrapped898)
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
	flat908 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat908 != nil {
		p.write(*flat908)
		return nil
	} else {
		_dollar_dollar := msg
		fields906 := _dollar_dollar.GetFragment()
		unwrapped_fields907 := fields906
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields907)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat915 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat915 != nil {
		p.write(*flat915)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields909 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields910 := fields909
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field911 := unwrapped_fields910[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field911)
		field912 := unwrapped_fields910[1].([]*pb.Declaration)
		if !(len(field912) == 0) {
			p.newline()
			for i914, elem913 := range field912 {
				if (i914 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem913)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		fields916 := msg
		p.pretty_fragment_id(fields916)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat926 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat926 != nil {
		p.write(*flat926)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1641 = _dollar_dollar.GetDef()
		}
		deconstruct_result924 := _t1641
		if deconstruct_result924 != nil {
			unwrapped925 := deconstruct_result924
			p.pretty_def(unwrapped925)
		} else {
			_dollar_dollar := msg
			var _t1642 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1642 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result922 := _t1642
			if deconstruct_result922 != nil {
				unwrapped923 := deconstruct_result922
				p.pretty_algorithm(unwrapped923)
			} else {
				_dollar_dollar := msg
				var _t1643 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1643 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result920 := _t1643
				if deconstruct_result920 != nil {
					unwrapped921 := deconstruct_result920
					p.pretty_constraint(unwrapped921)
				} else {
					_dollar_dollar := msg
					var _t1644 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1644 = _dollar_dollar.GetData()
					}
					deconstruct_result918 := _t1644
					if deconstruct_result918 != nil {
						unwrapped919 := deconstruct_result918
						p.pretty_data(unwrapped919)
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
	flat933 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat933 != nil {
		p.write(*flat933)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1645 = _dollar_dollar.GetAttrs()
		}
		fields927 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1645}
		unwrapped_fields928 := fields927
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field929 := unwrapped_fields928[0].(*pb.RelationId)
		p.pretty_relation_id(field929)
		p.newline()
		field930 := unwrapped_fields928[1].(*pb.Abstraction)
		p.pretty_abstraction(field930)
		field931 := unwrapped_fields928[2].([]*pb.Attribute)
		if field931 != nil {
			p.newline()
			opt_val932 := field931
			p.pretty_attrs(opt_val932)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat938 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat938 != nil {
		p.write(*flat938)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1646 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1647 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1646 = ptr(_t1647)
		}
		deconstruct_result936 := _t1646
		if deconstruct_result936 != nil {
			unwrapped937 := *deconstruct_result936
			p.write(":")
			p.write(unwrapped937)
		} else {
			_dollar_dollar := msg
			_t1648 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result934 := _t1648
			if deconstruct_result934 != nil {
				unwrapped935 := deconstruct_result934
				p.write(p.formatUint128(unwrapped935))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat943 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_dollar_dollar := msg
		_t1649 := p.deconstruct_bindings(_dollar_dollar)
		fields939 := []interface{}{_t1649, _dollar_dollar.GetValue()}
		unwrapped_fields940 := fields939
		p.write("(")
		p.indent()
		field941 := unwrapped_fields940[0].([]interface{})
		p.pretty_bindings(field941)
		p.newline()
		field942 := unwrapped_fields940[1].(*pb.Formula)
		p.pretty_formula(field942)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat951 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat951 != nil {
		p.write(*flat951)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1650 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1650 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields944 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1650}
		unwrapped_fields945 := fields944
		p.write("[")
		p.indent()
		field946 := unwrapped_fields945[0].([]*pb.Binding)
		for i948, elem947 := range field946 {
			if (i948 > 0) {
				p.newline()
			}
			p.pretty_binding(elem947)
		}
		field949 := unwrapped_fields945[1].([]*pb.Binding)
		if field949 != nil {
			p.newline()
			opt_val950 := field949
			p.pretty_value_bindings(opt_val950)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat956 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat956 != nil {
		p.write(*flat956)
		return nil
	} else {
		_dollar_dollar := msg
		fields952 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields953 := fields952
		field954 := unwrapped_fields953[0].(string)
		p.write(field954)
		p.write("::")
		field955 := unwrapped_fields953[1].(*pb.Type)
		p.pretty_type(field955)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat985 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat985 != nil {
		p.write(*flat985)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1651 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1651 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result983 := _t1651
		if deconstruct_result983 != nil {
			unwrapped984 := deconstruct_result983
			p.pretty_unspecified_type(unwrapped984)
		} else {
			_dollar_dollar := msg
			var _t1652 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1652 = _dollar_dollar.GetStringType()
			}
			deconstruct_result981 := _t1652
			if deconstruct_result981 != nil {
				unwrapped982 := deconstruct_result981
				p.pretty_string_type(unwrapped982)
			} else {
				_dollar_dollar := msg
				var _t1653 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1653 = _dollar_dollar.GetIntType()
				}
				deconstruct_result979 := _t1653
				if deconstruct_result979 != nil {
					unwrapped980 := deconstruct_result979
					p.pretty_int_type(unwrapped980)
				} else {
					_dollar_dollar := msg
					var _t1654 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1654 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result977 := _t1654
					if deconstruct_result977 != nil {
						unwrapped978 := deconstruct_result977
						p.pretty_float_type(unwrapped978)
					} else {
						_dollar_dollar := msg
						var _t1655 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1655 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result975 := _t1655
						if deconstruct_result975 != nil {
							unwrapped976 := deconstruct_result975
							p.pretty_uint128_type(unwrapped976)
						} else {
							_dollar_dollar := msg
							var _t1656 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1656 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result973 := _t1656
							if deconstruct_result973 != nil {
								unwrapped974 := deconstruct_result973
								p.pretty_int128_type(unwrapped974)
							} else {
								_dollar_dollar := msg
								var _t1657 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1657 = _dollar_dollar.GetDateType()
								}
								deconstruct_result971 := _t1657
								if deconstruct_result971 != nil {
									unwrapped972 := deconstruct_result971
									p.pretty_date_type(unwrapped972)
								} else {
									_dollar_dollar := msg
									var _t1658 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1658 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result969 := _t1658
									if deconstruct_result969 != nil {
										unwrapped970 := deconstruct_result969
										p.pretty_datetime_type(unwrapped970)
									} else {
										_dollar_dollar := msg
										var _t1659 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1659 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result967 := _t1659
										if deconstruct_result967 != nil {
											unwrapped968 := deconstruct_result967
											p.pretty_missing_type(unwrapped968)
										} else {
											_dollar_dollar := msg
											var _t1660 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1660 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result965 := _t1660
											if deconstruct_result965 != nil {
												unwrapped966 := deconstruct_result965
												p.pretty_decimal_type(unwrapped966)
											} else {
												_dollar_dollar := msg
												var _t1661 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1661 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result963 := _t1661
												if deconstruct_result963 != nil {
													unwrapped964 := deconstruct_result963
													p.pretty_boolean_type(unwrapped964)
												} else {
													_dollar_dollar := msg
													var _t1662 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1662 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result961 := _t1662
													if deconstruct_result961 != nil {
														unwrapped962 := deconstruct_result961
														p.pretty_int32_type(unwrapped962)
													} else {
														_dollar_dollar := msg
														var _t1663 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1663 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result959 := _t1663
														if deconstruct_result959 != nil {
															unwrapped960 := deconstruct_result959
															p.pretty_float32_type(unwrapped960)
														} else {
															_dollar_dollar := msg
															var _t1664 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1664 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result957 := _t1664
															if deconstruct_result957 != nil {
																unwrapped958 := deconstruct_result957
																p.pretty_uint32_type(unwrapped958)
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
	fields986 := msg
	_ = fields986
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields987 := msg
	_ = fields987
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields988 := msg
	_ = fields988
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields989 := msg
	_ = fields989
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields990 := msg
	_ = fields990
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields991 := msg
	_ = fields991
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields992 := msg
	_ = fields992
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields993 := msg
	_ = fields993
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields994 := msg
	_ = fields994
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat999 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat999 != nil {
		p.write(*flat999)
		return nil
	} else {
		_dollar_dollar := msg
		fields995 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields996 := fields995
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field997 := unwrapped_fields996[0].(int64)
		p.write(fmt.Sprintf("%d", field997))
		p.newline()
		field998 := unwrapped_fields996[1].(int64)
		p.write(fmt.Sprintf("%d", field998))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1000 := msg
	_ = fields1000
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1001 := msg
	_ = fields1001
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1002 := msg
	_ = fields1002
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1003 := msg
	_ = fields1003
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		fields1004 := msg
		p.write("|")
		if !(len(fields1004) == 0) {
			p.write(" ")
			for i1006, elem1005 := range fields1004 {
				if (i1006 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1005)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1034 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1034 != nil {
		p.write(*flat1034)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1665 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1665 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1032 := _t1665
		if deconstruct_result1032 != nil {
			unwrapped1033 := deconstruct_result1032
			p.pretty_true(unwrapped1033)
		} else {
			_dollar_dollar := msg
			var _t1666 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1666 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1030 := _t1666
			if deconstruct_result1030 != nil {
				unwrapped1031 := deconstruct_result1030
				p.pretty_false(unwrapped1031)
			} else {
				_dollar_dollar := msg
				var _t1667 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1667 = _dollar_dollar.GetExists()
				}
				deconstruct_result1028 := _t1667
				if deconstruct_result1028 != nil {
					unwrapped1029 := deconstruct_result1028
					p.pretty_exists(unwrapped1029)
				} else {
					_dollar_dollar := msg
					var _t1668 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1668 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1026 := _t1668
					if deconstruct_result1026 != nil {
						unwrapped1027 := deconstruct_result1026
						p.pretty_reduce(unwrapped1027)
					} else {
						_dollar_dollar := msg
						var _t1669 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1669 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1024 := _t1669
						if deconstruct_result1024 != nil {
							unwrapped1025 := deconstruct_result1024
							p.pretty_conjunction(unwrapped1025)
						} else {
							_dollar_dollar := msg
							var _t1670 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1670 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1022 := _t1670
							if deconstruct_result1022 != nil {
								unwrapped1023 := deconstruct_result1022
								p.pretty_disjunction(unwrapped1023)
							} else {
								_dollar_dollar := msg
								var _t1671 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1671 = _dollar_dollar.GetNot()
								}
								deconstruct_result1020 := _t1671
								if deconstruct_result1020 != nil {
									unwrapped1021 := deconstruct_result1020
									p.pretty_not(unwrapped1021)
								} else {
									_dollar_dollar := msg
									var _t1672 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1672 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1018 := _t1672
									if deconstruct_result1018 != nil {
										unwrapped1019 := deconstruct_result1018
										p.pretty_ffi(unwrapped1019)
									} else {
										_dollar_dollar := msg
										var _t1673 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1673 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1016 := _t1673
										if deconstruct_result1016 != nil {
											unwrapped1017 := deconstruct_result1016
											p.pretty_atom(unwrapped1017)
										} else {
											_dollar_dollar := msg
											var _t1674 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1674 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1014 := _t1674
											if deconstruct_result1014 != nil {
												unwrapped1015 := deconstruct_result1014
												p.pretty_pragma(unwrapped1015)
											} else {
												_dollar_dollar := msg
												var _t1675 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1675 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1012 := _t1675
												if deconstruct_result1012 != nil {
													unwrapped1013 := deconstruct_result1012
													p.pretty_primitive(unwrapped1013)
												} else {
													_dollar_dollar := msg
													var _t1676 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1676 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1010 := _t1676
													if deconstruct_result1010 != nil {
														unwrapped1011 := deconstruct_result1010
														p.pretty_rel_atom(unwrapped1011)
													} else {
														_dollar_dollar := msg
														var _t1677 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1677 = _dollar_dollar.GetCast()
														}
														deconstruct_result1008 := _t1677
														if deconstruct_result1008 != nil {
															unwrapped1009 := deconstruct_result1008
															p.pretty_cast(unwrapped1009)
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
	fields1035 := msg
	_ = fields1035
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1036 := msg
	_ = fields1036
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1041 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1041 != nil {
		p.write(*flat1041)
		return nil
	} else {
		_dollar_dollar := msg
		_t1678 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1037 := []interface{}{_t1678, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1038 := fields1037
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1039 := unwrapped_fields1038[0].([]interface{})
		p.pretty_bindings(field1039)
		p.newline()
		field1040 := unwrapped_fields1038[1].(*pb.Formula)
		p.pretty_formula(field1040)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1047 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1047 != nil {
		p.write(*flat1047)
		return nil
	} else {
		_dollar_dollar := msg
		fields1042 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1043 := fields1042
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1044 := unwrapped_fields1043[0].(*pb.Abstraction)
		p.pretty_abstraction(field1044)
		p.newline()
		field1045 := unwrapped_fields1043[1].(*pb.Abstraction)
		p.pretty_abstraction(field1045)
		p.newline()
		field1046 := unwrapped_fields1043[2].([]*pb.Term)
		p.pretty_terms(field1046)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		fields1048 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1048) == 0) {
			p.newline()
			for i1050, elem1049 := range fields1048 {
				if (i1050 > 0) {
					p.newline()
				}
				p.pretty_term(elem1049)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1056 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1056 != nil {
		p.write(*flat1056)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1679 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1679 = _dollar_dollar.GetVar()
		}
		deconstruct_result1054 := _t1679
		if deconstruct_result1054 != nil {
			unwrapped1055 := deconstruct_result1054
			p.pretty_var(unwrapped1055)
		} else {
			_dollar_dollar := msg
			var _t1680 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1680 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1052 := _t1680
			if deconstruct_result1052 != nil {
				unwrapped1053 := deconstruct_result1052
				p.pretty_value(unwrapped1053)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1059 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1059 != nil {
		p.write(*flat1059)
		return nil
	} else {
		_dollar_dollar := msg
		fields1057 := _dollar_dollar.GetName()
		unwrapped_fields1058 := fields1057
		p.write(unwrapped_fields1058)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1085 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1085 != nil {
		p.write(*flat1085)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1681 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1681 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1083 := _t1681
		if deconstruct_result1083 != nil {
			unwrapped1084 := deconstruct_result1083
			p.pretty_date(unwrapped1084)
		} else {
			_dollar_dollar := msg
			var _t1682 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1682 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1081 := _t1682
			if deconstruct_result1081 != nil {
				unwrapped1082 := deconstruct_result1081
				p.pretty_datetime(unwrapped1082)
			} else {
				_dollar_dollar := msg
				var _t1683 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1683 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1079 := _t1683
				if deconstruct_result1079 != nil {
					unwrapped1080 := *deconstruct_result1079
					p.write(p.formatStringValue(unwrapped1080))
				} else {
					_dollar_dollar := msg
					var _t1684 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1684 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1077 := _t1684
					if deconstruct_result1077 != nil {
						unwrapped1078 := *deconstruct_result1077
						p.write(fmt.Sprintf("%di32", unwrapped1078))
					} else {
						_dollar_dollar := msg
						var _t1685 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1685 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1075 := _t1685
						if deconstruct_result1075 != nil {
							unwrapped1076 := *deconstruct_result1075
							p.write(fmt.Sprintf("%d", unwrapped1076))
						} else {
							_dollar_dollar := msg
							var _t1686 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1686 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1073 := _t1686
							if deconstruct_result1073 != nil {
								unwrapped1074 := *deconstruct_result1073
								p.write(formatFloat32(unwrapped1074))
							} else {
								_dollar_dollar := msg
								var _t1687 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1687 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1071 := _t1687
								if deconstruct_result1071 != nil {
									unwrapped1072 := *deconstruct_result1071
									p.write(formatFloat64(unwrapped1072))
								} else {
									_dollar_dollar := msg
									var _t1688 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1688 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1069 := _t1688
									if deconstruct_result1069 != nil {
										unwrapped1070 := *deconstruct_result1069
										p.write(fmt.Sprintf("%du32", unwrapped1070))
									} else {
										_dollar_dollar := msg
										var _t1689 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1689 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1067 := _t1689
										if deconstruct_result1067 != nil {
											unwrapped1068 := deconstruct_result1067
											p.write(p.formatUint128(unwrapped1068))
										} else {
											_dollar_dollar := msg
											var _t1690 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1690 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1065 := _t1690
											if deconstruct_result1065 != nil {
												unwrapped1066 := deconstruct_result1065
												p.write(p.formatInt128(unwrapped1066))
											} else {
												_dollar_dollar := msg
												var _t1691 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1691 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1063 := _t1691
												if deconstruct_result1063 != nil {
													unwrapped1064 := deconstruct_result1063
													p.write(p.formatDecimal(unwrapped1064))
												} else {
													_dollar_dollar := msg
													var _t1692 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1692 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1061 := _t1692
													if deconstruct_result1061 != nil {
														unwrapped1062 := *deconstruct_result1061
														p.pretty_boolean_value(unwrapped1062)
													} else {
														fields1060 := msg
														_ = fields1060
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
	flat1091 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1091 != nil {
		p.write(*flat1091)
		return nil
	} else {
		_dollar_dollar := msg
		fields1086 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1087 := fields1086
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1088 := unwrapped_fields1087[0].(int64)
		p.write(fmt.Sprintf("%d", field1088))
		p.newline()
		field1089 := unwrapped_fields1087[1].(int64)
		p.write(fmt.Sprintf("%d", field1089))
		p.newline()
		field1090 := unwrapped_fields1087[2].(int64)
		p.write(fmt.Sprintf("%d", field1090))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1092 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1093 := fields1092
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1094 := unwrapped_fields1093[0].(int64)
		p.write(fmt.Sprintf("%d", field1094))
		p.newline()
		field1095 := unwrapped_fields1093[1].(int64)
		p.write(fmt.Sprintf("%d", field1095))
		p.newline()
		field1096 := unwrapped_fields1093[2].(int64)
		p.write(fmt.Sprintf("%d", field1096))
		p.newline()
		field1097 := unwrapped_fields1093[3].(int64)
		p.write(fmt.Sprintf("%d", field1097))
		p.newline()
		field1098 := unwrapped_fields1093[4].(int64)
		p.write(fmt.Sprintf("%d", field1098))
		p.newline()
		field1099 := unwrapped_fields1093[5].(int64)
		p.write(fmt.Sprintf("%d", field1099))
		field1100 := unwrapped_fields1093[6].(*int64)
		if field1100 != nil {
			p.newline()
			opt_val1101 := *field1100
			p.write(fmt.Sprintf("%d", opt_val1101))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		fields1103 := _dollar_dollar.GetArgs()
		unwrapped_fields1104 := fields1103
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1104) == 0) {
			p.newline()
			for i1106, elem1105 := range unwrapped_fields1104 {
				if (i1106 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1105)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		fields1108 := _dollar_dollar.GetArgs()
		unwrapped_fields1109 := fields1108
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1109) == 0) {
			p.newline()
			for i1111, elem1110 := range unwrapped_fields1109 {
				if (i1111 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1110)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1115 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1115 != nil {
		p.write(*flat1115)
		return nil
	} else {
		_dollar_dollar := msg
		fields1113 := _dollar_dollar.GetArg()
		unwrapped_fields1114 := fields1113
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1114)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		_dollar_dollar := msg
		fields1116 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1117 := fields1116
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1118 := unwrapped_fields1117[0].(string)
		p.pretty_name(field1118)
		p.newline()
		field1119 := unwrapped_fields1117[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1119)
		p.newline()
		field1120 := unwrapped_fields1117[2].([]*pb.Term)
		p.pretty_terms(field1120)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		fields1122 := msg
		p.write(":")
		p.write(fields1122)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1127 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1127 != nil {
		p.write(*flat1127)
		return nil
	} else {
		fields1124 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1124) == 0) {
			p.newline()
			for i1126, elem1125 := range fields1124 {
				if (i1126 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1125)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		_dollar_dollar := msg
		fields1128 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1129 := fields1128
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1130 := unwrapped_fields1129[0].(*pb.RelationId)
		p.pretty_relation_id(field1130)
		field1131 := unwrapped_fields1129[1].([]*pb.Term)
		if !(len(field1131) == 0) {
			p.newline()
			for i1133, elem1132 := range field1131 {
				if (i1133 > 0) {
					p.newline()
				}
				p.pretty_term(elem1132)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1141 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1141 != nil {
		p.write(*flat1141)
		return nil
	} else {
		_dollar_dollar := msg
		fields1135 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1136 := fields1135
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1137 := unwrapped_fields1136[0].(string)
		p.pretty_name(field1137)
		field1138 := unwrapped_fields1136[1].([]*pb.Term)
		if !(len(field1138) == 0) {
			p.newline()
			for i1140, elem1139 := range field1138 {
				if (i1140 > 0) {
					p.newline()
				}
				p.pretty_term(elem1139)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1693 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1156 := _t1693
		if guard_result1156 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1694 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1694 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1155 := _t1694
			if guard_result1155 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1695 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1695 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1154 := _t1695
				if guard_result1154 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1696 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1696 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1153 := _t1696
					if guard_result1153 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1697 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1697 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1152 := _t1697
						if guard_result1152 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1698 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1698 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1151 := _t1698
							if guard_result1151 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1699 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1699 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1150 := _t1699
								if guard_result1150 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1700 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1700 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1149 := _t1700
									if guard_result1149 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1701 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1701 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1148 := _t1701
										if guard_result1148 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1142 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1143 := fields1142
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1144 := unwrapped_fields1143[0].(string)
											p.pretty_name(field1144)
											field1145 := unwrapped_fields1143[1].([]*pb.RelTerm)
											if !(len(field1145) == 0) {
												p.newline()
												for i1147, elem1146 := range field1145 {
													if (i1147 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1146)
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
	flat1162 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1702 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1702 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1158 := _t1702
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1160 := unwrapped_fields1159[0].(*pb.Term)
		p.pretty_term(field1160)
		p.newline()
		field1161 := unwrapped_fields1159[1].(*pb.Term)
		p.pretty_term(field1161)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1703 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1163 := _t1703
		unwrapped_fields1164 := fields1163
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1165 := unwrapped_fields1164[0].(*pb.Term)
		p.pretty_term(field1165)
		p.newline()
		field1166 := unwrapped_fields1164[1].(*pb.Term)
		p.pretty_term(field1166)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1704 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1704 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1168 := _t1704
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1170 := unwrapped_fields1169[0].(*pb.Term)
		p.pretty_term(field1170)
		p.newline()
		field1171 := unwrapped_fields1169[1].(*pb.Term)
		p.pretty_term(field1171)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1177 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1177 != nil {
		p.write(*flat1177)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1705 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1705 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1173 := _t1705
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1175 := unwrapped_fields1174[0].(*pb.Term)
		p.pretty_term(field1175)
		p.newline()
		field1176 := unwrapped_fields1174[1].(*pb.Term)
		p.pretty_term(field1176)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1706 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1178 := _t1706
		unwrapped_fields1179 := fields1178
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1180 := unwrapped_fields1179[0].(*pb.Term)
		p.pretty_term(field1180)
		p.newline()
		field1181 := unwrapped_fields1179[1].(*pb.Term)
		p.pretty_term(field1181)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1188 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1188 != nil {
		p.write(*flat1188)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1707 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1183 := _t1707
		unwrapped_fields1184 := fields1183
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1185 := unwrapped_fields1184[0].(*pb.Term)
		p.pretty_term(field1185)
		p.newline()
		field1186 := unwrapped_fields1184[1].(*pb.Term)
		p.pretty_term(field1186)
		p.newline()
		field1187 := unwrapped_fields1184[2].(*pb.Term)
		p.pretty_term(field1187)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1708 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1708 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1189 := _t1708
		unwrapped_fields1190 := fields1189
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1191 := unwrapped_fields1190[0].(*pb.Term)
		p.pretty_term(field1191)
		p.newline()
		field1192 := unwrapped_fields1190[1].(*pb.Term)
		p.pretty_term(field1192)
		p.newline()
		field1193 := unwrapped_fields1190[2].(*pb.Term)
		p.pretty_term(field1193)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1709 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1709 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1195 := _t1709
		unwrapped_fields1196 := fields1195
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1197 := unwrapped_fields1196[0].(*pb.Term)
		p.pretty_term(field1197)
		p.newline()
		field1198 := unwrapped_fields1196[1].(*pb.Term)
		p.pretty_term(field1198)
		p.newline()
		field1199 := unwrapped_fields1196[2].(*pb.Term)
		p.pretty_term(field1199)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1206 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1206 != nil {
		p.write(*flat1206)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1710 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1710 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1201 := _t1710
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(*pb.Term)
		p.pretty_term(field1203)
		p.newline()
		field1204 := unwrapped_fields1202[1].(*pb.Term)
		p.pretty_term(field1204)
		p.newline()
		field1205 := unwrapped_fields1202[2].(*pb.Term)
		p.pretty_term(field1205)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1711 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1209 := _t1711
		if deconstruct_result1209 != nil {
			unwrapped1210 := deconstruct_result1209
			p.pretty_specialized_value(unwrapped1210)
		} else {
			_dollar_dollar := msg
			var _t1712 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1712 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1207 := _t1712
			if deconstruct_result1207 != nil {
				unwrapped1208 := deconstruct_result1207
				p.pretty_term(unwrapped1208)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1213 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1213 != nil {
		p.write(*flat1213)
		return nil
	} else {
		fields1212 := msg
		p.write("#")
		p.pretty_raw_value(fields1212)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		fields1214 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1215 := fields1214
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1216 := unwrapped_fields1215[0].(string)
		p.pretty_name(field1216)
		field1217 := unwrapped_fields1215[1].([]*pb.RelTerm)
		if !(len(field1217) == 0) {
			p.newline()
			for i1219, elem1218 := range field1217 {
				if (i1219 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1218)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1225 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1225 != nil {
		p.write(*flat1225)
		return nil
	} else {
		_dollar_dollar := msg
		fields1221 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1222 := fields1221
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1223 := unwrapped_fields1222[0].(*pb.Term)
		p.pretty_term(field1223)
		p.newline()
		field1224 := unwrapped_fields1222[1].(*pb.Term)
		p.pretty_term(field1224)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1229 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1229 != nil {
		p.write(*flat1229)
		return nil
	} else {
		fields1226 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1226) == 0) {
			p.newline()
			for i1228, elem1227 := range fields1226 {
				if (i1228 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1227)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1236 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1236 != nil {
		p.write(*flat1236)
		return nil
	} else {
		_dollar_dollar := msg
		fields1230 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1231 := fields1230
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1232 := unwrapped_fields1231[0].(string)
		p.pretty_name(field1232)
		field1233 := unwrapped_fields1231[1].([]*pb.Value)
		if !(len(field1233) == 0) {
			p.newline()
			for i1235, elem1234 := range field1233 {
				if (i1235 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1234)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1713 = _dollar_dollar.GetAttrs()
		}
		fields1237 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1713}
		unwrapped_fields1238 := fields1237
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1239 := unwrapped_fields1238[0].([]*pb.RelationId)
		if !(len(field1239) == 0) {
			p.newline()
			for i1241, elem1240 := range field1239 {
				if (i1241 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1240)
			}
		}
		p.newline()
		field1242 := unwrapped_fields1238[1].(*pb.Script)
		p.pretty_script(field1242)
		field1243 := unwrapped_fields1238[2].([]*pb.Attribute)
		if field1243 != nil {
			p.newline()
			opt_val1244 := field1243
			p.pretty_attrs(opt_val1244)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1250 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1250 != nil {
		p.write(*flat1250)
		return nil
	} else {
		_dollar_dollar := msg
		fields1246 := _dollar_dollar.GetConstructs()
		unwrapped_fields1247 := fields1246
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1247) == 0) {
			p.newline()
			for i1249, elem1248 := range unwrapped_fields1247 {
				if (i1249 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1248)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1255 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1255 != nil {
		p.write(*flat1255)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1714 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1714 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1253 := _t1714
		if deconstruct_result1253 != nil {
			unwrapped1254 := deconstruct_result1253
			p.pretty_loop(unwrapped1254)
		} else {
			_dollar_dollar := msg
			var _t1715 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1715 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1251 := _t1715
			if deconstruct_result1251 != nil {
				unwrapped1252 := deconstruct_result1251
				p.pretty_instruction(unwrapped1252)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1716 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1716 = _dollar_dollar.GetAttrs()
		}
		fields1256 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1716}
		unwrapped_fields1257 := fields1256
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1258 := unwrapped_fields1257[0].([]*pb.Instruction)
		p.pretty_init(field1258)
		p.newline()
		field1259 := unwrapped_fields1257[1].(*pb.Script)
		p.pretty_script(field1259)
		field1260 := unwrapped_fields1257[2].([]*pb.Attribute)
		if field1260 != nil {
			p.newline()
			opt_val1261 := field1260
			p.pretty_attrs(opt_val1261)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		fields1263 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1263) == 0) {
			p.newline()
			for i1265, elem1264 := range fields1263 {
				if (i1265 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1264)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1277 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1717 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1275 := _t1717
		if deconstruct_result1275 != nil {
			unwrapped1276 := deconstruct_result1275
			p.pretty_assign(unwrapped1276)
		} else {
			_dollar_dollar := msg
			var _t1718 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1718 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1273 := _t1718
			if deconstruct_result1273 != nil {
				unwrapped1274 := deconstruct_result1273
				p.pretty_upsert(unwrapped1274)
			} else {
				_dollar_dollar := msg
				var _t1719 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1719 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1271 := _t1719
				if deconstruct_result1271 != nil {
					unwrapped1272 := deconstruct_result1271
					p.pretty_break(unwrapped1272)
				} else {
					_dollar_dollar := msg
					var _t1720 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1720 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1269 := _t1720
					if deconstruct_result1269 != nil {
						unwrapped1270 := deconstruct_result1269
						p.pretty_monoid_def(unwrapped1270)
					} else {
						_dollar_dollar := msg
						var _t1721 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1721 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1267 := _t1721
						if deconstruct_result1267 != nil {
							unwrapped1268 := deconstruct_result1267
							p.pretty_monus_def(unwrapped1268)
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
	flat1284 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1722 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1722 = _dollar_dollar.GetAttrs()
		}
		fields1278 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1722}
		unwrapped_fields1279 := fields1278
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1280 := unwrapped_fields1279[0].(*pb.RelationId)
		p.pretty_relation_id(field1280)
		p.newline()
		field1281 := unwrapped_fields1279[1].(*pb.Abstraction)
		p.pretty_abstraction(field1281)
		field1282 := unwrapped_fields1279[2].([]*pb.Attribute)
		if field1282 != nil {
			p.newline()
			opt_val1283 := field1282
			p.pretty_attrs(opt_val1283)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1723 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1723 = _dollar_dollar.GetAttrs()
		}
		fields1285 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1723}
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].(*pb.RelationId)
		p.pretty_relation_id(field1287)
		p.newline()
		field1288 := unwrapped_fields1286[1].([]interface{})
		p.pretty_abstraction_with_arity(field1288)
		field1289 := unwrapped_fields1286[2].([]*pb.Attribute)
		if field1289 != nil {
			p.newline()
			opt_val1290 := field1289
			p.pretty_attrs(opt_val1290)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		_t1724 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1292 := []interface{}{_t1724, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1293 := fields1292
		p.write("(")
		p.indent()
		field1294 := unwrapped_fields1293[0].([]interface{})
		p.pretty_bindings(field1294)
		p.newline()
		field1295 := unwrapped_fields1293[1].(*pb.Formula)
		p.pretty_formula(field1295)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1725 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1725 = _dollar_dollar.GetAttrs()
		}
		fields1297 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1725}
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1299 := unwrapped_fields1298[0].(*pb.RelationId)
		p.pretty_relation_id(field1299)
		p.newline()
		field1300 := unwrapped_fields1298[1].(*pb.Abstraction)
		p.pretty_abstraction(field1300)
		field1301 := unwrapped_fields1298[2].([]*pb.Attribute)
		if field1301 != nil {
			p.newline()
			opt_val1302 := field1301
			p.pretty_attrs(opt_val1302)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1311 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1726 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1726 = _dollar_dollar.GetAttrs()
		}
		fields1304 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1726}
		unwrapped_fields1305 := fields1304
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1306 := unwrapped_fields1305[0].(*pb.Monoid)
		p.pretty_monoid(field1306)
		p.newline()
		field1307 := unwrapped_fields1305[1].(*pb.RelationId)
		p.pretty_relation_id(field1307)
		p.newline()
		field1308 := unwrapped_fields1305[2].([]interface{})
		p.pretty_abstraction_with_arity(field1308)
		field1309 := unwrapped_fields1305[3].([]*pb.Attribute)
		if field1309 != nil {
			p.newline()
			opt_val1310 := field1309
			p.pretty_attrs(opt_val1310)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1727 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1318 := _t1727
		if deconstruct_result1318 != nil {
			unwrapped1319 := deconstruct_result1318
			p.pretty_or_monoid(unwrapped1319)
		} else {
			_dollar_dollar := msg
			var _t1728 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1728 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1316 := _t1728
			if deconstruct_result1316 != nil {
				unwrapped1317 := deconstruct_result1316
				p.pretty_min_monoid(unwrapped1317)
			} else {
				_dollar_dollar := msg
				var _t1729 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1729 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1314 := _t1729
				if deconstruct_result1314 != nil {
					unwrapped1315 := deconstruct_result1314
					p.pretty_max_monoid(unwrapped1315)
				} else {
					_dollar_dollar := msg
					var _t1730 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1730 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1312 := _t1730
					if deconstruct_result1312 != nil {
						unwrapped1313 := deconstruct_result1312
						p.pretty_sum_monoid(unwrapped1313)
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
	fields1321 := msg
	_ = fields1321
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		_dollar_dollar := msg
		fields1322 := _dollar_dollar.GetType()
		unwrapped_fields1323 := fields1322
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1323)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1327 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1327 != nil {
		p.write(*flat1327)
		return nil
	} else {
		_dollar_dollar := msg
		fields1325 := _dollar_dollar.GetType()
		unwrapped_fields1326 := fields1325
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1326)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		_dollar_dollar := msg
		fields1328 := _dollar_dollar.GetType()
		unwrapped_fields1329 := fields1328
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1329)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1338 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1338 != nil {
		p.write(*flat1338)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1731 = _dollar_dollar.GetAttrs()
		}
		fields1331 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1731}
		unwrapped_fields1332 := fields1331
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1333 := unwrapped_fields1332[0].(*pb.Monoid)
		p.pretty_monoid(field1333)
		p.newline()
		field1334 := unwrapped_fields1332[1].(*pb.RelationId)
		p.pretty_relation_id(field1334)
		p.newline()
		field1335 := unwrapped_fields1332[2].([]interface{})
		p.pretty_abstraction_with_arity(field1335)
		field1336 := unwrapped_fields1332[3].([]*pb.Attribute)
		if field1336 != nil {
			p.newline()
			opt_val1337 := field1336
			p.pretty_attrs(opt_val1337)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1345 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1345 != nil {
		p.write(*flat1345)
		return nil
	} else {
		_dollar_dollar := msg
		fields1339 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1340 := fields1339
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1341 := unwrapped_fields1340[0].(*pb.RelationId)
		p.pretty_relation_id(field1341)
		p.newline()
		field1342 := unwrapped_fields1340[1].(*pb.Abstraction)
		p.pretty_abstraction(field1342)
		p.newline()
		field1343 := unwrapped_fields1340[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1343)
		p.newline()
		field1344 := unwrapped_fields1340[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1344)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		fields1346 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1346) == 0) {
			p.newline()
			for i1348, elem1347 := range fields1346 {
				if (i1348 > 0) {
					p.newline()
				}
				p.pretty_var(elem1347)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		fields1350 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1350) == 0) {
			p.newline()
			for i1352, elem1351 := range fields1350 {
				if (i1352 > 0) {
					p.newline()
				}
				p.pretty_var(elem1351)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1362 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1362 != nil {
		p.write(*flat1362)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1732 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1732 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1360 := _t1732
		if deconstruct_result1360 != nil {
			unwrapped1361 := deconstruct_result1360
			p.pretty_edb(unwrapped1361)
		} else {
			_dollar_dollar := msg
			var _t1733 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1733 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1358 := _t1733
			if deconstruct_result1358 != nil {
				unwrapped1359 := deconstruct_result1358
				p.pretty_betree_relation(unwrapped1359)
			} else {
				_dollar_dollar := msg
				var _t1734 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1734 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1356 := _t1734
				if deconstruct_result1356 != nil {
					unwrapped1357 := deconstruct_result1356
					p.pretty_csv_data(unwrapped1357)
				} else {
					_dollar_dollar := msg
					var _t1735 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1735 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1354 := _t1735
					if deconstruct_result1354 != nil {
						unwrapped1355 := deconstruct_result1354
						p.pretty_iceberg_data(unwrapped1355)
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
	flat1368 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		fields1363 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1364 := fields1363
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1365 := unwrapped_fields1364[0].(*pb.RelationId)
		p.pretty_relation_id(field1365)
		p.newline()
		field1366 := unwrapped_fields1364[1].([]string)
		p.pretty_edb_path(field1366)
		p.newline()
		field1367 := unwrapped_fields1364[2].([]*pb.Type)
		p.pretty_edb_types(field1367)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1372 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1372 != nil {
		p.write(*flat1372)
		return nil
	} else {
		fields1369 := msg
		p.write("[")
		p.indent()
		for i1371, elem1370 := range fields1369 {
			if (i1371 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1370))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		fields1373 := msg
		p.write("[")
		p.indent()
		for i1375, elem1374 := range fields1373 {
			if (i1375 > 0) {
				p.newline()
			}
			p.pretty_type(elem1374)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1381 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1381 != nil {
		p.write(*flat1381)
		return nil
	} else {
		_dollar_dollar := msg
		fields1377 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1379 := unwrapped_fields1378[0].(*pb.RelationId)
		p.pretty_relation_id(field1379)
		p.newline()
		field1380 := unwrapped_fields1378[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1380)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		_dollar_dollar := msg
		_t1736 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1382 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1736}
		unwrapped_fields1383 := fields1382
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1384 := unwrapped_fields1383[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1384)
		p.newline()
		field1385 := unwrapped_fields1383[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1385)
		p.newline()
		field1386 := unwrapped_fields1383[2].([][]interface{})
		p.pretty_config_dict(field1386)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1391 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1391 != nil {
		p.write(*flat1391)
		return nil
	} else {
		fields1388 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1388) == 0) {
			p.newline()
			for i1390, elem1389 := range fields1388 {
				if (i1390 > 0) {
					p.newline()
				}
				p.pretty_type(elem1389)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1395 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1395 != nil {
		p.write(*flat1395)
		return nil
	} else {
		fields1392 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1392) == 0) {
			p.newline()
			for i1394, elem1393 := range fields1392 {
				if (i1394 > 0) {
					p.newline()
				}
				p.pretty_type(elem1393)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1402 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1402 != nil {
		p.write(*flat1402)
		return nil
	} else {
		_dollar_dollar := msg
		fields1396 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1397 := fields1396
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1398 := unwrapped_fields1397[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1398)
		p.newline()
		field1399 := unwrapped_fields1397[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1399)
		p.newline()
		field1400 := unwrapped_fields1397[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1400)
		p.newline()
		field1401 := unwrapped_fields1397[3].(string)
		p.pretty_csv_asof(field1401)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1409 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1409 != nil {
		p.write(*flat1409)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1737 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1737 = _dollar_dollar.GetPaths()
		}
		var _t1738 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1738 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1403 := []interface{}{_t1737, _t1738}
		unwrapped_fields1404 := fields1403
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1405 := unwrapped_fields1404[0].([]string)
		if field1405 != nil {
			p.newline()
			opt_val1406 := field1405
			p.pretty_csv_locator_paths(opt_val1406)
		}
		field1407 := unwrapped_fields1404[1].(*string)
		if field1407 != nil {
			p.newline()
			opt_val1408 := *field1407
			p.pretty_csv_locator_inline_data(opt_val1408)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		fields1410 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1410) == 0) {
			p.newline()
			for i1412, elem1411 := range fields1410 {
				if (i1412 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1411))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1415 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1415 != nil {
		p.write(*flat1415)
		return nil
	} else {
		fields1414 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1414))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1421 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1421 != nil {
		p.write(*flat1421)
		return nil
	} else {
		_dollar_dollar := msg
		_t1739 := p.deconstruct_csv_config(_dollar_dollar)
		_t1740 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1416 := []interface{}{_t1739, _t1740}
		unwrapped_fields1417 := fields1416
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1418 := unwrapped_fields1417[0].([][]interface{})
		p.pretty_config_dict(field1418)
		field1419 := unwrapped_fields1417[1].([][]interface{})
		if field1419 != nil {
			p.newline()
			opt_val1420 := field1419
			p.pretty__storage_integration(opt_val1420)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1423 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		fields1422 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1422)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1427 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1427 != nil {
		p.write(*flat1427)
		return nil
	} else {
		fields1424 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1424) == 0) {
			p.newline()
			for i1426, elem1425 := range fields1424 {
				if (i1426 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1425)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1436 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1436 != nil {
		p.write(*flat1436)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1741 = _dollar_dollar.GetTargetId()
		}
		fields1428 := []interface{}{_dollar_dollar.GetColumnPath(), _t1741, _dollar_dollar.GetTypes()}
		unwrapped_fields1429 := fields1428
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1430 := unwrapped_fields1429[0].([]string)
		p.pretty_gnf_column_path(field1430)
		field1431 := unwrapped_fields1429[1].(*pb.RelationId)
		if field1431 != nil {
			p.newline()
			opt_val1432 := field1431
			p.pretty_relation_id(opt_val1432)
		}
		p.newline()
		p.write("[")
		field1433 := unwrapped_fields1429[2].([]*pb.Type)
		for i1435, elem1434 := range field1433 {
			if (i1435 > 0) {
				p.newline()
			}
			p.pretty_type(elem1434)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1443 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1443 != nil {
		p.write(*flat1443)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1742 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1742 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1441 := _t1742
		if deconstruct_result1441 != nil {
			unwrapped1442 := *deconstruct_result1441
			p.write(p.formatStringValue(unwrapped1442))
		} else {
			_dollar_dollar := msg
			var _t1743 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1743 = _dollar_dollar
			}
			deconstruct_result1437 := _t1743
			if deconstruct_result1437 != nil {
				unwrapped1438 := deconstruct_result1437
				p.write("[")
				p.indent()
				for i1440, elem1439 := range unwrapped1438 {
					if (i1440 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1439))
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
	flat1445 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1445 != nil {
		p.write(*flat1445)
		return nil
	} else {
		fields1444 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1444))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1456 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1456 != nil {
		p.write(*flat1456)
		return nil
	} else {
		_dollar_dollar := msg
		_t1744 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1745 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1446 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1744, _t1745, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1447 := fields1446
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1448 := unwrapped_fields1447[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1448)
		p.newline()
		field1449 := unwrapped_fields1447[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1449)
		p.newline()
		field1450 := unwrapped_fields1447[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1450)
		field1451 := unwrapped_fields1447[3].(*string)
		if field1451 != nil {
			p.newline()
			opt_val1452 := *field1451
			p.pretty_iceberg_from_snapshot(opt_val1452)
		}
		field1453 := unwrapped_fields1447[4].(*string)
		if field1453 != nil {
			p.newline()
			opt_val1454 := *field1453
			p.pretty_iceberg_to_snapshot(opt_val1454)
		}
		p.newline()
		field1455 := unwrapped_fields1447[5].(bool)
		p.pretty_boolean_value(field1455)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		_dollar_dollar := msg
		fields1457 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1458 := fields1457
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1459 := unwrapped_fields1458[0].(string)
		p.pretty_iceberg_locator_table_name(field1459)
		p.newline()
		field1460 := unwrapped_fields1458[1].([]string)
		p.pretty_iceberg_locator_namespace(field1460)
		p.newline()
		field1461 := unwrapped_fields1458[2].(string)
		p.pretty_iceberg_locator_warehouse(field1461)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		fields1463 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1463))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		fields1465 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1465) == 0) {
			p.newline()
			for i1467, elem1466 := range fields1465 {
				if (i1467 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1466))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1470 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		fields1469 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1469))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1478 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1478 != nil {
		p.write(*flat1478)
		return nil
	} else {
		_dollar_dollar := msg
		_t1746 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1471 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1746, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1472 := fields1471
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1473 := unwrapped_fields1472[0].(string)
		p.pretty_iceberg_catalog_uri(field1473)
		field1474 := unwrapped_fields1472[1].(*string)
		if field1474 != nil {
			p.newline()
			opt_val1475 := *field1474
			p.pretty_iceberg_catalog_config_scope(opt_val1475)
		}
		p.newline()
		field1476 := unwrapped_fields1472[2].([][]interface{})
		p.pretty_iceberg_properties(field1476)
		p.newline()
		field1477 := unwrapped_fields1472[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1477)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		fields1479 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1479))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1482 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		fields1481 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1481))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1486 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1486 != nil {
		p.write(*flat1486)
		return nil
	} else {
		fields1483 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1483) == 0) {
			p.newline()
			for i1485, elem1484 := range fields1483 {
				if (i1485 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1484)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1491 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1491 != nil {
		p.write(*flat1491)
		return nil
	} else {
		_dollar_dollar := msg
		fields1487 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1488 := fields1487
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1489 := unwrapped_fields1488[0].(string)
		p.write(p.formatStringValue(field1489))
		p.newline()
		field1490 := unwrapped_fields1488[1].(string)
		p.write(p.formatStringValue(field1490))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1495 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1495 != nil {
		p.write(*flat1495)
		return nil
	} else {
		fields1492 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1492) == 0) {
			p.newline()
			for i1494, elem1493 := range fields1492 {
				if (i1494 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1493)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1500 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1500 != nil {
		p.write(*flat1500)
		return nil
	} else {
		_dollar_dollar := msg
		_t1747 := p.mask_secret_value(_dollar_dollar)
		fields1496 := []interface{}{_dollar_dollar[0].(string), _t1747}
		unwrapped_fields1497 := fields1496
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1498 := unwrapped_fields1497[0].(string)
		p.write(p.formatStringValue(field1498))
		p.newline()
		field1499 := unwrapped_fields1497[1].(string)
		p.write(p.formatStringValue(field1499))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1502 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1502 != nil {
		p.write(*flat1502)
		return nil
	} else {
		fields1501 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1501))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1504 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		fields1503 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1503))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1507 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1507 != nil {
		p.write(*flat1507)
		return nil
	} else {
		_dollar_dollar := msg
		fields1505 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1506 := fields1505
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1506)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1512 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1512 != nil {
		p.write(*flat1512)
		return nil
	} else {
		_dollar_dollar := msg
		fields1508 := _dollar_dollar.GetRelations()
		unwrapped_fields1509 := fields1508
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1509) == 0) {
			p.newline()
			for i1511, elem1510 := range unwrapped_fields1509 {
				if (i1511 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1510)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1519 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1519 != nil {
		p.write(*flat1519)
		return nil
	} else {
		_dollar_dollar := msg
		fields1513 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1514 := fields1513
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1515 := unwrapped_fields1514[0].([]string)
		p.pretty_edb_path(field1515)
		field1516 := unwrapped_fields1514[1].([]*pb.SnapshotMapping)
		if !(len(field1516) == 0) {
			p.newline()
			for i1518, elem1517 := range field1516 {
				if (i1518 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1517)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1524 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1524 != nil {
		p.write(*flat1524)
		return nil
	} else {
		_dollar_dollar := msg
		fields1520 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1521 := fields1520
		field1522 := unwrapped_fields1521[0].([]string)
		p.pretty_edb_path(field1522)
		p.write(" ")
		field1523 := unwrapped_fields1521[1].(*pb.RelationId)
		p.pretty_relation_id(field1523)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1528 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1528 != nil {
		p.write(*flat1528)
		return nil
	} else {
		fields1525 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1525) == 0) {
			p.newline()
			for i1527, elem1526 := range fields1525 {
				if (i1527 > 0) {
					p.newline()
				}
				p.pretty_read(elem1526)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1541 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1541 != nil {
		p.write(*flat1541)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1748 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1748 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1539 := _t1748
		if deconstruct_result1539 != nil {
			unwrapped1540 := deconstruct_result1539
			p.pretty_demand(unwrapped1540)
		} else {
			_dollar_dollar := msg
			var _t1749 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1749 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1537 := _t1749
			if deconstruct_result1537 != nil {
				unwrapped1538 := deconstruct_result1537
				p.pretty_output(unwrapped1538)
			} else {
				_dollar_dollar := msg
				var _t1750 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1750 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1535 := _t1750
				if deconstruct_result1535 != nil {
					unwrapped1536 := deconstruct_result1535
					p.pretty_what_if(unwrapped1536)
				} else {
					_dollar_dollar := msg
					var _t1751 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1751 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1533 := _t1751
					if deconstruct_result1533 != nil {
						unwrapped1534 := deconstruct_result1533
						p.pretty_abort(unwrapped1534)
					} else {
						_dollar_dollar := msg
						var _t1752 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1752 = _dollar_dollar.GetExport()
						}
						deconstruct_result1531 := _t1752
						if deconstruct_result1531 != nil {
							unwrapped1532 := deconstruct_result1531
							p.pretty_export(unwrapped1532)
						} else {
							_dollar_dollar := msg
							var _t1753 *pb.ExportOutput
							if hasProtoField(_dollar_dollar, "export_output") {
								_t1753 = _dollar_dollar.GetExportOutput()
							}
							deconstruct_result1529 := _t1753
							if deconstruct_result1529 != nil {
								unwrapped1530 := deconstruct_result1529
								p.pretty_export_output(unwrapped1530)
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
	flat1544 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1544 != nil {
		p.write(*flat1544)
		return nil
	} else {
		_dollar_dollar := msg
		fields1542 := _dollar_dollar.GetRelationId()
		unwrapped_fields1543 := fields1542
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1543)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1549 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1549 != nil {
		p.write(*flat1549)
		return nil
	} else {
		_dollar_dollar := msg
		fields1545 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1546 := fields1545
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1547 := unwrapped_fields1546[0].(string)
		p.pretty_name(field1547)
		p.newline()
		field1548 := unwrapped_fields1546[1].(*pb.RelationId)
		p.pretty_relation_id(field1548)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1554 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1554 != nil {
		p.write(*flat1554)
		return nil
	} else {
		_dollar_dollar := msg
		fields1550 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1551 := fields1550
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1552 := unwrapped_fields1551[0].(string)
		p.pretty_name(field1552)
		p.newline()
		field1553 := unwrapped_fields1551[1].(*pb.Epoch)
		p.pretty_epoch(field1553)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1560 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1560 != nil {
		p.write(*flat1560)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1754 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1754 = ptr(_dollar_dollar.GetName())
		}
		fields1555 := []interface{}{_t1754, _dollar_dollar.GetRelationId()}
		unwrapped_fields1556 := fields1555
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1557 := unwrapped_fields1556[0].(*string)
		if field1557 != nil {
			p.newline()
			opt_val1558 := *field1557
			p.pretty_name(opt_val1558)
		}
		p.newline()
		field1559 := unwrapped_fields1556[1].(*pb.RelationId)
		p.pretty_relation_id(field1559)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1565 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1565 != nil {
		p.write(*flat1565)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1755 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1755 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1563 := _t1755
		if deconstruct_result1563 != nil {
			unwrapped1564 := deconstruct_result1563
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1564)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1756 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1756 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1561 := _t1756
			if deconstruct_result1561 != nil {
				unwrapped1562 := deconstruct_result1561
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1562)
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
	flat1576 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1576 != nil {
		p.write(*flat1576)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1757 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1757 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1571 := _t1757
		if deconstruct_result1571 != nil {
			unwrapped1572 := deconstruct_result1571
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1573 := unwrapped1572[0].(string)
			p.pretty_export_csv_path(field1573)
			p.newline()
			field1574 := unwrapped1572[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1574)
			p.newline()
			field1575 := unwrapped1572[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1575)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1758 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1759 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1758 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1759}
			}
			deconstruct_result1566 := _t1758
			if deconstruct_result1566 != nil {
				unwrapped1567 := deconstruct_result1566
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1568 := unwrapped1567[0].(string)
				p.pretty_export_csv_path(field1568)
				p.newline()
				field1569 := unwrapped1567[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1569)
				p.newline()
				field1570 := unwrapped1567[2].([][]interface{})
				p.pretty_config_dict(field1570)
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
	flat1578 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1578 != nil {
		p.write(*flat1578)
		return nil
	} else {
		fields1577 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1577))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1585 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1585 != nil {
		p.write(*flat1585)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1760 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1760 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1581 := _t1760
		if deconstruct_result1581 != nil {
			unwrapped1582 := deconstruct_result1581
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1582) == 0) {
				p.newline()
				for i1584, elem1583 := range unwrapped1582 {
					if (i1584 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1583)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1761 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1761 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1579 := _t1761
			if deconstruct_result1579 != nil {
				unwrapped1580 := deconstruct_result1579
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1580)
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
	flat1590 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1590 != nil {
		p.write(*flat1590)
		return nil
	} else {
		_dollar_dollar := msg
		fields1586 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1587 := fields1586
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1588 := unwrapped_fields1587[0].(string)
		p.write(p.formatStringValue(field1588))
		p.newline()
		field1589 := unwrapped_fields1587[1].(*pb.RelationId)
		p.pretty_relation_id(field1589)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1594 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1594 != nil {
		p.write(*flat1594)
		return nil
	} else {
		fields1591 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1591) == 0) {
			p.newline()
			for i1593, elem1592 := range fields1591 {
				if (i1593 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1592)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1603 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1603 != nil {
		p.write(*flat1603)
		return nil
	} else {
		_dollar_dollar := msg
		_t1762 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1595 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1762}
		unwrapped_fields1596 := fields1595
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1597 := unwrapped_fields1596[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1597)
		p.newline()
		field1598 := unwrapped_fields1596[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1598)
		p.newline()
		field1599 := unwrapped_fields1596[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1599)
		p.newline()
		field1600 := unwrapped_fields1596[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1600)
		field1601 := unwrapped_fields1596[4].([][]interface{})
		if field1601 != nil {
			p.newline()
			opt_val1602 := field1601
			p.pretty_config_dict(opt_val1602)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1605 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1605 != nil {
		p.write(*flat1605)
		return nil
	} else {
		fields1604 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1604)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1609 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1609 != nil {
		p.write(*flat1609)
		return nil
	} else {
		fields1606 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1606) == 0) {
			p.newline()
			for i1608, elem1607 := range fields1606 {
				if (i1608 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1607)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_output(msg *pb.ExportOutput) interface{} {
	flat1612 := p.tryFlat(msg, func() { p.pretty_export_output(msg) })
	if flat1612 != nil {
		p.write(*flat1612)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1763 *pb.ExportCSVOutput
		if hasProtoField(_dollar_dollar, "csv") {
			_t1763 = _dollar_dollar.GetCsv()
		}
		fields1610 := _t1763
		unwrapped_fields1611 := fields1610
		p.write("(")
		p.write("output_export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_output(unwrapped_fields1611)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_output(msg *pb.ExportCSVOutput) interface{} {
	flat1617 := p.tryFlat(msg, func() { p.pretty_export_csv_output(msg) })
	if flat1617 != nil {
		p.write(*flat1617)
		return nil
	} else {
		_dollar_dollar := msg
		fields1613 := []interface{}{_dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		unwrapped_fields1614 := fields1613
		p.write("(")
		p.write("csv")
		p.indentSexp()
		p.newline()
		field1615 := unwrapped_fields1614[0].(*pb.ExportCSVSource)
		p.pretty_export_csv_source(field1615)
		p.newline()
		field1616 := unwrapped_fields1614[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1616)
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
		_t1815 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1815)
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
