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

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1832 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1832
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.Relations {
	var _t1833 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1833
	return nil
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1834 := &pb.Value{}
	_t1834.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1834
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1835 := &pb.Value{}
	_t1835.Value = &pb.Value_IntValue{IntValue: v}
	return _t1835
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1836 := &pb.Value{}
	_t1836.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1836
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1837 := &pb.Value{}
	_t1837.Value = &pb.Value_StringValue{StringValue: v}
	return _t1837
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1838 := &pb.Value{}
	_t1838.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1838
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1839 := &pb.Value{}
	_t1839.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1839
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1840 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1840})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1841 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1841})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1842 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1842})
			}
		}
	}
	_t1843 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1843})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1844 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1844})
	_t1845 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1845})
	if msg.GetNewLine() != "" {
		_t1846 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1846})
	}
	_t1847 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1847})
	_t1848 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1848})
	_t1849 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1849})
	if msg.GetComment() != "" {
		_t1850 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1850})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1851 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1851})
	}
	_t1852 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1852})
	_t1853 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1853})
	_t1854 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1854})
	if msg.GetPartitionSizeMb() != 0 {
		_t1855 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1855})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1856 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1856
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1857 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1857})
	}
	if si.GetAzureSasToken() != "" {
		_t1858 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1858})
	}
	if si.GetS3Region() != "" {
		_t1859 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1859})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1860 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1860})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1861 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1861})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1862 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1862})
	_t1863 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1863})
	_t1864 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1864})
	_t1865 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1865})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1866 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1866})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1867 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1867})
		}
	}
	_t1868 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1868})
	_t1869 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1869})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1870 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1870})
	}
	if msg.Compression != nil {
		_t1871 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1871})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1872 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1872})
	}
	if msg.SyntaxMissingString != nil {
		_t1873 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1873})
	}
	if msg.SyntaxDelim != nil {
		_t1874 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1874})
	}
	if msg.SyntaxQuotechar != nil {
		_t1875 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1875})
	}
	if msg.SyntaxEscapechar != nil {
		_t1876 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1876})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1877 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1877
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1878 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1878
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1879 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1879
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1880 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1880})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1881 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1881})
	}
	if msg.GetCompression() != "" {
		_t1882 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1882})
	}
	var _t1883 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1883
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1884 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1884
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
	flat851 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat851 != nil {
		p.write(*flat851)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1684 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1684 = _dollar_dollar.GetConfigure()
		}
		var _t1685 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1685 = _dollar_dollar.GetSync()
		}
		fields842 := []interface{}{_t1684, _t1685, _dollar_dollar.GetEpochs()}
		unwrapped_fields843 := fields842
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field844 := unwrapped_fields843[0].(*pb.Configure)
		if field844 != nil {
			p.newline()
			opt_val845 := field844
			p.pretty_configure(opt_val845)
		}
		field846 := unwrapped_fields843[1].(*pb.Sync)
		if field846 != nil {
			p.newline()
			opt_val847 := field846
			p.pretty_sync(opt_val847)
		}
		field848 := unwrapped_fields843[2].([]*pb.Epoch)
		if !(len(field848) == 0) {
			p.newline()
			for i850, elem849 := range field848 {
				if (i850 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem849)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat854 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		_dollar_dollar := msg
		_t1686 := p.deconstruct_configure(_dollar_dollar)
		fields852 := _t1686
		unwrapped_fields853 := fields852
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields853)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		fields855 := msg
		p.write("{")
		p.indent()
		if !(len(fields855) == 0) {
			p.newline()
			for i857, elem856 := range fields855 {
				if (i857 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem856)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		fields859 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields860 := fields859
		p.write(":")
		field861 := unwrapped_fields860[0].(string)
		p.write(field861)
		p.write(" ")
		field862 := unwrapped_fields860[1].(*pb.Value)
		p.pretty_raw_value(field862)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat889 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat889 != nil {
		p.write(*flat889)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1687 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1687 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result887 := _t1687
		if deconstruct_result887 != nil {
			unwrapped888 := deconstruct_result887
			p.pretty_raw_date(unwrapped888)
		} else {
			_dollar_dollar := msg
			var _t1688 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1688 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result885 := _t1688
			if deconstruct_result885 != nil {
				unwrapped886 := deconstruct_result885
				p.pretty_raw_datetime(unwrapped886)
			} else {
				_dollar_dollar := msg
				var _t1689 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1689 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result883 := _t1689
				if deconstruct_result883 != nil {
					unwrapped884 := *deconstruct_result883
					p.write(p.formatStringValue(unwrapped884))
				} else {
					_dollar_dollar := msg
					var _t1690 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1690 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result881 := _t1690
					if deconstruct_result881 != nil {
						unwrapped882 := *deconstruct_result881
						p.write(fmt.Sprintf("%di32", unwrapped882))
					} else {
						_dollar_dollar := msg
						var _t1691 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1691 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result879 := _t1691
						if deconstruct_result879 != nil {
							unwrapped880 := *deconstruct_result879
							p.write(fmt.Sprintf("%d", unwrapped880))
						} else {
							_dollar_dollar := msg
							var _t1692 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1692 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result877 := _t1692
							if deconstruct_result877 != nil {
								unwrapped878 := *deconstruct_result877
								p.write(formatFloat32(unwrapped878))
							} else {
								_dollar_dollar := msg
								var _t1693 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1693 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result875 := _t1693
								if deconstruct_result875 != nil {
									unwrapped876 := *deconstruct_result875
									p.write(formatFloat64(unwrapped876))
								} else {
									_dollar_dollar := msg
									var _t1694 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1694 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result873 := _t1694
									if deconstruct_result873 != nil {
										unwrapped874 := *deconstruct_result873
										p.write(fmt.Sprintf("%du32", unwrapped874))
									} else {
										_dollar_dollar := msg
										var _t1695 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1695 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result871 := _t1695
										if deconstruct_result871 != nil {
											unwrapped872 := deconstruct_result871
											p.write(p.formatUint128(unwrapped872))
										} else {
											_dollar_dollar := msg
											var _t1696 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1696 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result869 := _t1696
											if deconstruct_result869 != nil {
												unwrapped870 := deconstruct_result869
												p.write(p.formatInt128(unwrapped870))
											} else {
												_dollar_dollar := msg
												var _t1697 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1697 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result867 := _t1697
												if deconstruct_result867 != nil {
													unwrapped868 := deconstruct_result867
													p.write(p.formatDecimal(unwrapped868))
												} else {
													_dollar_dollar := msg
													var _t1698 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1698 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result865 := _t1698
													if deconstruct_result865 != nil {
														unwrapped866 := *deconstruct_result865
														p.pretty_boolean_value(unwrapped866)
													} else {
														fields864 := msg
														_ = fields864
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
	flat895 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat895 != nil {
		p.write(*flat895)
		return nil
	} else {
		_dollar_dollar := msg
		fields890 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields891 := fields890
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field892 := unwrapped_fields891[0].(int64)
		p.write(fmt.Sprintf("%d", field892))
		p.newline()
		field893 := unwrapped_fields891[1].(int64)
		p.write(fmt.Sprintf("%d", field893))
		p.newline()
		field894 := unwrapped_fields891[2].(int64)
		p.write(fmt.Sprintf("%d", field894))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		fields896 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields897 := fields896
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field898 := unwrapped_fields897[0].(int64)
		p.write(fmt.Sprintf("%d", field898))
		p.newline()
		field899 := unwrapped_fields897[1].(int64)
		p.write(fmt.Sprintf("%d", field899))
		p.newline()
		field900 := unwrapped_fields897[2].(int64)
		p.write(fmt.Sprintf("%d", field900))
		p.newline()
		field901 := unwrapped_fields897[3].(int64)
		p.write(fmt.Sprintf("%d", field901))
		p.newline()
		field902 := unwrapped_fields897[4].(int64)
		p.write(fmt.Sprintf("%d", field902))
		p.newline()
		field903 := unwrapped_fields897[5].(int64)
		p.write(fmt.Sprintf("%d", field903))
		field904 := unwrapped_fields897[6].(*int64)
		if field904 != nil {
			p.newline()
			opt_val905 := *field904
			p.write(fmt.Sprintf("%d", opt_val905))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1699 []interface{}
	if _dollar_dollar {
		_t1699 = []interface{}{}
	}
	deconstruct_result909 := _t1699
	if deconstruct_result909 != nil {
		unwrapped910 := deconstruct_result909
		_ = unwrapped910
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1700 []interface{}
		if !(_dollar_dollar) {
			_t1700 = []interface{}{}
		}
		deconstruct_result907 := _t1700
		if deconstruct_result907 != nil {
			unwrapped908 := deconstruct_result907
			_ = unwrapped908
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat915 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat915 != nil {
		p.write(*flat915)
		return nil
	} else {
		_dollar_dollar := msg
		fields911 := _dollar_dollar.GetFragments()
		unwrapped_fields912 := fields911
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields912) == 0) {
			p.newline()
			for i914, elem913 := range unwrapped_fields912 {
				if (i914 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem913)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat918 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat918 != nil {
		p.write(*flat918)
		return nil
	} else {
		_dollar_dollar := msg
		fields916 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields917 := fields916
		p.write(":")
		p.write(unwrapped_fields917)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat925 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat925 != nil {
		p.write(*flat925)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1701 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1701 = _dollar_dollar.GetWrites()
		}
		var _t1702 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1702 = _dollar_dollar.GetReads()
		}
		fields919 := []interface{}{_t1701, _t1702}
		unwrapped_fields920 := fields919
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field921 := unwrapped_fields920[0].([]*pb.Write)
		if field921 != nil {
			p.newline()
			opt_val922 := field921
			p.pretty_epoch_writes(opt_val922)
		}
		field923 := unwrapped_fields920[1].([]*pb.Read)
		if field923 != nil {
			p.newline()
			opt_val924 := field923
			p.pretty_epoch_reads(opt_val924)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat929 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat929 != nil {
		p.write(*flat929)
		return nil
	} else {
		fields926 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields926) == 0) {
			p.newline()
			for i928, elem927 := range fields926 {
				if (i928 > 0) {
					p.newline()
				}
				p.pretty_write(elem927)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat938 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat938 != nil {
		p.write(*flat938)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1703 = _dollar_dollar.GetDefine()
		}
		deconstruct_result936 := _t1703
		if deconstruct_result936 != nil {
			unwrapped937 := deconstruct_result936
			p.pretty_define(unwrapped937)
		} else {
			_dollar_dollar := msg
			var _t1704 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1704 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result934 := _t1704
			if deconstruct_result934 != nil {
				unwrapped935 := deconstruct_result934
				p.pretty_undefine(unwrapped935)
			} else {
				_dollar_dollar := msg
				var _t1705 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1705 = _dollar_dollar.GetContext()
				}
				deconstruct_result932 := _t1705
				if deconstruct_result932 != nil {
					unwrapped933 := deconstruct_result932
					p.pretty_context(unwrapped933)
				} else {
					_dollar_dollar := msg
					var _t1706 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1706 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result930 := _t1706
					if deconstruct_result930 != nil {
						unwrapped931 := deconstruct_result930
						p.pretty_snapshot(unwrapped931)
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
	flat941 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		_dollar_dollar := msg
		fields939 := _dollar_dollar.GetFragment()
		unwrapped_fields940 := fields939
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields940)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat948 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat948 != nil {
		p.write(*flat948)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields942 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields943 := fields942
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field944 := unwrapped_fields943[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field944)
		field945 := unwrapped_fields943[1].([]*pb.Declaration)
		if !(len(field945) == 0) {
			p.newline()
			for i947, elem946 := range field945 {
				if (i947 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem946)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat950 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat950 != nil {
		p.write(*flat950)
		return nil
	} else {
		fields949 := msg
		p.pretty_fragment_id(fields949)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat959 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat959 != nil {
		p.write(*flat959)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1707 = _dollar_dollar.GetDef()
		}
		deconstruct_result957 := _t1707
		if deconstruct_result957 != nil {
			unwrapped958 := deconstruct_result957
			p.pretty_def(unwrapped958)
		} else {
			_dollar_dollar := msg
			var _t1708 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1708 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result955 := _t1708
			if deconstruct_result955 != nil {
				unwrapped956 := deconstruct_result955
				p.pretty_algorithm(unwrapped956)
			} else {
				_dollar_dollar := msg
				var _t1709 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1709 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result953 := _t1709
				if deconstruct_result953 != nil {
					unwrapped954 := deconstruct_result953
					p.pretty_constraint(unwrapped954)
				} else {
					_dollar_dollar := msg
					var _t1710 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1710 = _dollar_dollar.GetData()
					}
					deconstruct_result951 := _t1710
					if deconstruct_result951 != nil {
						unwrapped952 := deconstruct_result951
						p.pretty_data(unwrapped952)
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
	flat966 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1711 = _dollar_dollar.GetAttrs()
		}
		fields960 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1711}
		unwrapped_fields961 := fields960
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field962 := unwrapped_fields961[0].(*pb.RelationId)
		p.pretty_relation_id(field962)
		p.newline()
		field963 := unwrapped_fields961[1].(*pb.Abstraction)
		p.pretty_abstraction(field963)
		field964 := unwrapped_fields961[2].([]*pb.Attribute)
		if field964 != nil {
			p.newline()
			opt_val965 := field964
			p.pretty_attrs(opt_val965)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat971 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1713 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1712 = ptr(_t1713)
		}
		deconstruct_result969 := _t1712
		if deconstruct_result969 != nil {
			unwrapped970 := *deconstruct_result969
			p.write(":")
			p.write(unwrapped970)
		} else {
			_dollar_dollar := msg
			_t1714 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result967 := _t1714
			if deconstruct_result967 != nil {
				unwrapped968 := deconstruct_result967
				p.write(p.formatUint128(unwrapped968))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		_t1715 := p.deconstruct_bindings(_dollar_dollar)
		fields972 := []interface{}{_t1715, _dollar_dollar.GetValue()}
		unwrapped_fields973 := fields972
		p.write("(")
		p.indent()
		field974 := unwrapped_fields973[0].([]interface{})
		p.pretty_bindings(field974)
		p.newline()
		field975 := unwrapped_fields973[1].(*pb.Formula)
		p.pretty_formula(field975)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat984 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat984 != nil {
		p.write(*flat984)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1716 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1716 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields977 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1716}
		unwrapped_fields978 := fields977
		p.write("[")
		p.indent()
		field979 := unwrapped_fields978[0].([]*pb.Binding)
		for i981, elem980 := range field979 {
			if (i981 > 0) {
				p.newline()
			}
			p.pretty_binding(elem980)
		}
		field982 := unwrapped_fields978[1].([]*pb.Binding)
		if field982 != nil {
			p.newline()
			opt_val983 := field982
			p.pretty_value_bindings(opt_val983)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_dollar_dollar := msg
		fields985 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields986 := fields985
		field987 := unwrapped_fields986[0].(string)
		p.write(field987)
		p.write("::")
		field988 := unwrapped_fields986[1].(*pb.Type)
		p.pretty_type(field988)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1018 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1018 != nil {
		p.write(*flat1018)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1717 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1016 := _t1717
		if deconstruct_result1016 != nil {
			unwrapped1017 := deconstruct_result1016
			p.pretty_unspecified_type(unwrapped1017)
		} else {
			_dollar_dollar := msg
			var _t1718 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1718 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1014 := _t1718
			if deconstruct_result1014 != nil {
				unwrapped1015 := deconstruct_result1014
				p.pretty_string_type(unwrapped1015)
			} else {
				_dollar_dollar := msg
				var _t1719 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1719 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1012 := _t1719
				if deconstruct_result1012 != nil {
					unwrapped1013 := deconstruct_result1012
					p.pretty_int_type(unwrapped1013)
				} else {
					_dollar_dollar := msg
					var _t1720 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1720 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1010 := _t1720
					if deconstruct_result1010 != nil {
						unwrapped1011 := deconstruct_result1010
						p.pretty_float_type(unwrapped1011)
					} else {
						_dollar_dollar := msg
						var _t1721 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1721 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1008 := _t1721
						if deconstruct_result1008 != nil {
							unwrapped1009 := deconstruct_result1008
							p.pretty_uint128_type(unwrapped1009)
						} else {
							_dollar_dollar := msg
							var _t1722 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1722 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1006 := _t1722
							if deconstruct_result1006 != nil {
								unwrapped1007 := deconstruct_result1006
								p.pretty_int128_type(unwrapped1007)
							} else {
								_dollar_dollar := msg
								var _t1723 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1723 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1004 := _t1723
								if deconstruct_result1004 != nil {
									unwrapped1005 := deconstruct_result1004
									p.pretty_date_type(unwrapped1005)
								} else {
									_dollar_dollar := msg
									var _t1724 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1724 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1002 := _t1724
									if deconstruct_result1002 != nil {
										unwrapped1003 := deconstruct_result1002
										p.pretty_datetime_type(unwrapped1003)
									} else {
										_dollar_dollar := msg
										var _t1725 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1725 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1000 := _t1725
										if deconstruct_result1000 != nil {
											unwrapped1001 := deconstruct_result1000
											p.pretty_missing_type(unwrapped1001)
										} else {
											_dollar_dollar := msg
											var _t1726 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1726 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result998 := _t1726
											if deconstruct_result998 != nil {
												unwrapped999 := deconstruct_result998
												p.pretty_decimal_type(unwrapped999)
											} else {
												_dollar_dollar := msg
												var _t1727 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1727 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result996 := _t1727
												if deconstruct_result996 != nil {
													unwrapped997 := deconstruct_result996
													p.pretty_boolean_type(unwrapped997)
												} else {
													_dollar_dollar := msg
													var _t1728 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1728 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result994 := _t1728
													if deconstruct_result994 != nil {
														unwrapped995 := deconstruct_result994
														p.pretty_int32_type(unwrapped995)
													} else {
														_dollar_dollar := msg
														var _t1729 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1729 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result992 := _t1729
														if deconstruct_result992 != nil {
															unwrapped993 := deconstruct_result992
															p.pretty_float32_type(unwrapped993)
														} else {
															_dollar_dollar := msg
															var _t1730 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1730 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result990 := _t1730
															if deconstruct_result990 != nil {
																unwrapped991 := deconstruct_result990
																p.pretty_uint32_type(unwrapped991)
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
	fields1019 := msg
	_ = fields1019
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1020 := msg
	_ = fields1020
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1021 := msg
	_ = fields1021
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1022 := msg
	_ = fields1022
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1023 := msg
	_ = fields1023
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1024 := msg
	_ = fields1024
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1025 := msg
	_ = fields1025
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1026 := msg
	_ = fields1026
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1027 := msg
	_ = fields1027
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		_dollar_dollar := msg
		fields1028 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1029 := fields1028
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1030 := unwrapped_fields1029[0].(int64)
		p.write(fmt.Sprintf("%d", field1030))
		p.newline()
		field1031 := unwrapped_fields1029[1].(int64)
		p.write(fmt.Sprintf("%d", field1031))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1033 := msg
	_ = fields1033
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1034 := msg
	_ = fields1034
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1035 := msg
	_ = fields1035
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1036 := msg
	_ = fields1036
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1040 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1040 != nil {
		p.write(*flat1040)
		return nil
	} else {
		fields1037 := msg
		p.write("|")
		if !(len(fields1037) == 0) {
			p.write(" ")
			for i1039, elem1038 := range fields1037 {
				if (i1039 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1038)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1067 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1067 != nil {
		p.write(*flat1067)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1731 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1065 := _t1731
		if deconstruct_result1065 != nil {
			unwrapped1066 := deconstruct_result1065
			p.pretty_true(unwrapped1066)
		} else {
			_dollar_dollar := msg
			var _t1732 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1732 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1063 := _t1732
			if deconstruct_result1063 != nil {
				unwrapped1064 := deconstruct_result1063
				p.pretty_false(unwrapped1064)
			} else {
				_dollar_dollar := msg
				var _t1733 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1733 = _dollar_dollar.GetExists()
				}
				deconstruct_result1061 := _t1733
				if deconstruct_result1061 != nil {
					unwrapped1062 := deconstruct_result1061
					p.pretty_exists(unwrapped1062)
				} else {
					_dollar_dollar := msg
					var _t1734 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1734 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1059 := _t1734
					if deconstruct_result1059 != nil {
						unwrapped1060 := deconstruct_result1059
						p.pretty_reduce(unwrapped1060)
					} else {
						_dollar_dollar := msg
						var _t1735 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1735 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1057 := _t1735
						if deconstruct_result1057 != nil {
							unwrapped1058 := deconstruct_result1057
							p.pretty_conjunction(unwrapped1058)
						} else {
							_dollar_dollar := msg
							var _t1736 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1736 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1055 := _t1736
							if deconstruct_result1055 != nil {
								unwrapped1056 := deconstruct_result1055
								p.pretty_disjunction(unwrapped1056)
							} else {
								_dollar_dollar := msg
								var _t1737 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1737 = _dollar_dollar.GetNot()
								}
								deconstruct_result1053 := _t1737
								if deconstruct_result1053 != nil {
									unwrapped1054 := deconstruct_result1053
									p.pretty_not(unwrapped1054)
								} else {
									_dollar_dollar := msg
									var _t1738 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1738 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1051 := _t1738
									if deconstruct_result1051 != nil {
										unwrapped1052 := deconstruct_result1051
										p.pretty_ffi(unwrapped1052)
									} else {
										_dollar_dollar := msg
										var _t1739 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1739 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1049 := _t1739
										if deconstruct_result1049 != nil {
											unwrapped1050 := deconstruct_result1049
											p.pretty_atom(unwrapped1050)
										} else {
											_dollar_dollar := msg
											var _t1740 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1740 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1047 := _t1740
											if deconstruct_result1047 != nil {
												unwrapped1048 := deconstruct_result1047
												p.pretty_pragma(unwrapped1048)
											} else {
												_dollar_dollar := msg
												var _t1741 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1741 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1045 := _t1741
												if deconstruct_result1045 != nil {
													unwrapped1046 := deconstruct_result1045
													p.pretty_primitive(unwrapped1046)
												} else {
													_dollar_dollar := msg
													var _t1742 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1742 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1043 := _t1742
													if deconstruct_result1043 != nil {
														unwrapped1044 := deconstruct_result1043
														p.pretty_rel_atom(unwrapped1044)
													} else {
														_dollar_dollar := msg
														var _t1743 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1743 = _dollar_dollar.GetCast()
														}
														deconstruct_result1041 := _t1743
														if deconstruct_result1041 != nil {
															unwrapped1042 := deconstruct_result1041
															p.pretty_cast(unwrapped1042)
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
	fields1068 := msg
	_ = fields1068
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1069 := msg
	_ = fields1069
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1074 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1074 != nil {
		p.write(*flat1074)
		return nil
	} else {
		_dollar_dollar := msg
		_t1744 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1070 := []interface{}{_t1744, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1071 := fields1070
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1072 := unwrapped_fields1071[0].([]interface{})
		p.pretty_bindings(field1072)
		p.newline()
		field1073 := unwrapped_fields1071[1].(*pb.Formula)
		p.pretty_formula(field1073)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1080 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1080 != nil {
		p.write(*flat1080)
		return nil
	} else {
		_dollar_dollar := msg
		fields1075 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1076 := fields1075
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1077 := unwrapped_fields1076[0].(*pb.Abstraction)
		p.pretty_abstraction(field1077)
		p.newline()
		field1078 := unwrapped_fields1076[1].(*pb.Abstraction)
		p.pretty_abstraction(field1078)
		p.newline()
		field1079 := unwrapped_fields1076[2].([]*pb.Term)
		p.pretty_terms(field1079)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1084 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1084 != nil {
		p.write(*flat1084)
		return nil
	} else {
		fields1081 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1081) == 0) {
			p.newline()
			for i1083, elem1082 := range fields1081 {
				if (i1083 > 0) {
					p.newline()
				}
				p.pretty_term(elem1082)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1745 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1745 = _dollar_dollar.GetVar()
		}
		deconstruct_result1087 := _t1745
		if deconstruct_result1087 != nil {
			unwrapped1088 := deconstruct_result1087
			p.pretty_var(unwrapped1088)
		} else {
			_dollar_dollar := msg
			var _t1746 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1746 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1085 := _t1746
			if deconstruct_result1085 != nil {
				unwrapped1086 := deconstruct_result1085
				p.pretty_value(unwrapped1086)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		fields1090 := _dollar_dollar.GetName()
		unwrapped_fields1091 := fields1090
		p.write(unwrapped_fields1091)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1747 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1747 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1116 := _t1747
		if deconstruct_result1116 != nil {
			unwrapped1117 := deconstruct_result1116
			p.pretty_date(unwrapped1117)
		} else {
			_dollar_dollar := msg
			var _t1748 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1748 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1114 := _t1748
			if deconstruct_result1114 != nil {
				unwrapped1115 := deconstruct_result1114
				p.pretty_datetime(unwrapped1115)
			} else {
				_dollar_dollar := msg
				var _t1749 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1749 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1112 := _t1749
				if deconstruct_result1112 != nil {
					unwrapped1113 := *deconstruct_result1112
					p.write(p.formatStringValue(unwrapped1113))
				} else {
					_dollar_dollar := msg
					var _t1750 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1750 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1110 := _t1750
					if deconstruct_result1110 != nil {
						unwrapped1111 := *deconstruct_result1110
						p.write(fmt.Sprintf("%di32", unwrapped1111))
					} else {
						_dollar_dollar := msg
						var _t1751 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1751 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1108 := _t1751
						if deconstruct_result1108 != nil {
							unwrapped1109 := *deconstruct_result1108
							p.write(fmt.Sprintf("%d", unwrapped1109))
						} else {
							_dollar_dollar := msg
							var _t1752 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1752 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1106 := _t1752
							if deconstruct_result1106 != nil {
								unwrapped1107 := *deconstruct_result1106
								p.write(formatFloat32(unwrapped1107))
							} else {
								_dollar_dollar := msg
								var _t1753 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1753 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1104 := _t1753
								if deconstruct_result1104 != nil {
									unwrapped1105 := *deconstruct_result1104
									p.write(formatFloat64(unwrapped1105))
								} else {
									_dollar_dollar := msg
									var _t1754 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1754 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1102 := _t1754
									if deconstruct_result1102 != nil {
										unwrapped1103 := *deconstruct_result1102
										p.write(fmt.Sprintf("%du32", unwrapped1103))
									} else {
										_dollar_dollar := msg
										var _t1755 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1755 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1100 := _t1755
										if deconstruct_result1100 != nil {
											unwrapped1101 := deconstruct_result1100
											p.write(p.formatUint128(unwrapped1101))
										} else {
											_dollar_dollar := msg
											var _t1756 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1756 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1098 := _t1756
											if deconstruct_result1098 != nil {
												unwrapped1099 := deconstruct_result1098
												p.write(p.formatInt128(unwrapped1099))
											} else {
												_dollar_dollar := msg
												var _t1757 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1757 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1096 := _t1757
												if deconstruct_result1096 != nil {
													unwrapped1097 := deconstruct_result1096
													p.write(p.formatDecimal(unwrapped1097))
												} else {
													_dollar_dollar := msg
													var _t1758 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1758 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1094 := _t1758
													if deconstruct_result1094 != nil {
														unwrapped1095 := *deconstruct_result1094
														p.pretty_boolean_value(unwrapped1095)
													} else {
														fields1093 := msg
														_ = fields1093
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
	flat1124 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1124 != nil {
		p.write(*flat1124)
		return nil
	} else {
		_dollar_dollar := msg
		fields1119 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1120 := fields1119
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1121 := unwrapped_fields1120[0].(int64)
		p.write(fmt.Sprintf("%d", field1121))
		p.newline()
		field1122 := unwrapped_fields1120[1].(int64)
		p.write(fmt.Sprintf("%d", field1122))
		p.newline()
		field1123 := unwrapped_fields1120[2].(int64)
		p.write(fmt.Sprintf("%d", field1123))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1135 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		fields1125 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1126 := fields1125
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1127 := unwrapped_fields1126[0].(int64)
		p.write(fmt.Sprintf("%d", field1127))
		p.newline()
		field1128 := unwrapped_fields1126[1].(int64)
		p.write(fmt.Sprintf("%d", field1128))
		p.newline()
		field1129 := unwrapped_fields1126[2].(int64)
		p.write(fmt.Sprintf("%d", field1129))
		p.newline()
		field1130 := unwrapped_fields1126[3].(int64)
		p.write(fmt.Sprintf("%d", field1130))
		p.newline()
		field1131 := unwrapped_fields1126[4].(int64)
		p.write(fmt.Sprintf("%d", field1131))
		p.newline()
		field1132 := unwrapped_fields1126[5].(int64)
		p.write(fmt.Sprintf("%d", field1132))
		field1133 := unwrapped_fields1126[6].(*int64)
		if field1133 != nil {
			p.newline()
			opt_val1134 := *field1133
			p.write(fmt.Sprintf("%d", opt_val1134))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		fields1136 := _dollar_dollar.GetArgs()
		unwrapped_fields1137 := fields1136
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1137) == 0) {
			p.newline()
			for i1139, elem1138 := range unwrapped_fields1137 {
				if (i1139 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1138)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		fields1141 := _dollar_dollar.GetArgs()
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1142) == 0) {
			p.newline()
			for i1144, elem1143 := range unwrapped_fields1142 {
				if (i1144 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1143)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1148 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1148 != nil {
		p.write(*flat1148)
		return nil
	} else {
		_dollar_dollar := msg
		fields1146 := _dollar_dollar.GetArg()
		unwrapped_fields1147 := fields1146
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1147)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1154 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1154 != nil {
		p.write(*flat1154)
		return nil
	} else {
		_dollar_dollar := msg
		fields1149 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1150 := fields1149
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1151 := unwrapped_fields1150[0].(string)
		p.pretty_name(field1151)
		p.newline()
		field1152 := unwrapped_fields1150[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1152)
		p.newline()
		field1153 := unwrapped_fields1150[2].([]*pb.Term)
		p.pretty_terms(field1153)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1156 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1156 != nil {
		p.write(*flat1156)
		return nil
	} else {
		fields1155 := msg
		p.write(":")
		p.write(fields1155)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		fields1157 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1157) == 0) {
			p.newline()
			for i1159, elem1158 := range fields1157 {
				if (i1159 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1158)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		fields1161 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1163 := unwrapped_fields1162[0].(*pb.RelationId)
		p.pretty_relation_id(field1163)
		field1164 := unwrapped_fields1162[1].([]*pb.Term)
		if !(len(field1164) == 0) {
			p.newline()
			for i1166, elem1165 := range field1164 {
				if (i1166 > 0) {
					p.newline()
				}
				p.pretty_term(elem1165)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		_dollar_dollar := msg
		fields1168 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1170 := unwrapped_fields1169[0].(string)
		p.pretty_name(field1170)
		field1171 := unwrapped_fields1169[1].([]*pb.Term)
		if !(len(field1171) == 0) {
			p.newline()
			for i1173, elem1172 := range field1171 {
				if (i1173 > 0) {
					p.newline()
				}
				p.pretty_term(elem1172)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1759 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1759 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1189 := _t1759
		if guard_result1189 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1760 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1760 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1188 := _t1760
			if guard_result1188 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1761 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1761 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1187 := _t1761
				if guard_result1187 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1762 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1762 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1186 := _t1762
					if guard_result1186 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1763 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1763 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1185 := _t1763
						if guard_result1185 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1764 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1764 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1184 := _t1764
							if guard_result1184 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1765 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1765 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1183 := _t1765
								if guard_result1183 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1766 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1766 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1182 := _t1766
									if guard_result1182 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1767 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1767 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1181 := _t1767
										if guard_result1181 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1175 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1176 := fields1175
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1177 := unwrapped_fields1176[0].(string)
											p.pretty_name(field1177)
											field1178 := unwrapped_fields1176[1].([]*pb.RelTerm)
											if !(len(field1178) == 0) {
												p.newline()
												for i1180, elem1179 := range field1178 {
													if (i1180 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1179)
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
	flat1195 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1195 != nil {
		p.write(*flat1195)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1768 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1768 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1191 := _t1768
		unwrapped_fields1192 := fields1191
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1193 := unwrapped_fields1192[0].(*pb.Term)
		p.pretty_term(field1193)
		p.newline()
		field1194 := unwrapped_fields1192[1].(*pb.Term)
		p.pretty_term(field1194)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1769 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1769 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1196 := _t1769
		unwrapped_fields1197 := fields1196
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1198 := unwrapped_fields1197[0].(*pb.Term)
		p.pretty_term(field1198)
		p.newline()
		field1199 := unwrapped_fields1197[1].(*pb.Term)
		p.pretty_term(field1199)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1770 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1770 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1201 := _t1770
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(*pb.Term)
		p.pretty_term(field1203)
		p.newline()
		field1204 := unwrapped_fields1202[1].(*pb.Term)
		p.pretty_term(field1204)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1771 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1771 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1206 := _t1771
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1208 := unwrapped_fields1207[0].(*pb.Term)
		p.pretty_term(field1208)
		p.newline()
		field1209 := unwrapped_fields1207[1].(*pb.Term)
		p.pretty_term(field1209)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1772 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1772 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1211 := _t1772
		unwrapped_fields1212 := fields1211
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1213 := unwrapped_fields1212[0].(*pb.Term)
		p.pretty_term(field1213)
		p.newline()
		field1214 := unwrapped_fields1212[1].(*pb.Term)
		p.pretty_term(field1214)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1773 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1773 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1216 := _t1773
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1218 := unwrapped_fields1217[0].(*pb.Term)
		p.pretty_term(field1218)
		p.newline()
		field1219 := unwrapped_fields1217[1].(*pb.Term)
		p.pretty_term(field1219)
		p.newline()
		field1220 := unwrapped_fields1217[2].(*pb.Term)
		p.pretty_term(field1220)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1774 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1774 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1222 := _t1774
		unwrapped_fields1223 := fields1222
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1224 := unwrapped_fields1223[0].(*pb.Term)
		p.pretty_term(field1224)
		p.newline()
		field1225 := unwrapped_fields1223[1].(*pb.Term)
		p.pretty_term(field1225)
		p.newline()
		field1226 := unwrapped_fields1223[2].(*pb.Term)
		p.pretty_term(field1226)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1233 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1233 != nil {
		p.write(*flat1233)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1775 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1775 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1228 := _t1775
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1230 := unwrapped_fields1229[0].(*pb.Term)
		p.pretty_term(field1230)
		p.newline()
		field1231 := unwrapped_fields1229[1].(*pb.Term)
		p.pretty_term(field1231)
		p.newline()
		field1232 := unwrapped_fields1229[2].(*pb.Term)
		p.pretty_term(field1232)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1239 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1239 != nil {
		p.write(*flat1239)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1776 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1776 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1234 := _t1776
		unwrapped_fields1235 := fields1234
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1236 := unwrapped_fields1235[0].(*pb.Term)
		p.pretty_term(field1236)
		p.newline()
		field1237 := unwrapped_fields1235[1].(*pb.Term)
		p.pretty_term(field1237)
		p.newline()
		field1238 := unwrapped_fields1235[2].(*pb.Term)
		p.pretty_term(field1238)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1777 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1777 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1242 := _t1777
		if deconstruct_result1242 != nil {
			unwrapped1243 := deconstruct_result1242
			p.pretty_specialized_value(unwrapped1243)
		} else {
			_dollar_dollar := msg
			var _t1778 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1778 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1240 := _t1778
			if deconstruct_result1240 != nil {
				unwrapped1241 := deconstruct_result1240
				p.pretty_term(unwrapped1241)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		fields1245 := msg
		p.write("#")
		p.pretty_raw_value(fields1245)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_dollar_dollar := msg
		fields1247 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1248 := fields1247
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1249 := unwrapped_fields1248[0].(string)
		p.pretty_name(field1249)
		field1250 := unwrapped_fields1248[1].([]*pb.RelTerm)
		if !(len(field1250) == 0) {
			p.newline()
			for i1252, elem1251 := range field1250 {
				if (i1252 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1251)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_dollar_dollar := msg
		fields1254 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1256 := unwrapped_fields1255[0].(*pb.Term)
		p.pretty_term(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].(*pb.Term)
		p.pretty_term(field1257)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		fields1259 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1259) == 0) {
			p.newline()
			for i1261, elem1260 := range fields1259 {
				if (i1261 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1260)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1269 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_dollar_dollar := msg
		fields1263 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1264 := fields1263
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1265 := unwrapped_fields1264[0].(string)
		p.pretty_name(field1265)
		field1266 := unwrapped_fields1264[1].([]*pb.Value)
		if !(len(field1266) == 0) {
			p.newline()
			for i1268, elem1267 := range field1266 {
				if (i1268 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1267)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1779 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1779 = _dollar_dollar.GetAttrs()
		}
		fields1270 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1779}
		unwrapped_fields1271 := fields1270
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1272 := unwrapped_fields1271[0].([]*pb.RelationId)
		if !(len(field1272) == 0) {
			p.newline()
			for i1274, elem1273 := range field1272 {
				if (i1274 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1273)
			}
		}
		p.newline()
		field1275 := unwrapped_fields1271[1].(*pb.Script)
		p.pretty_script(field1275)
		field1276 := unwrapped_fields1271[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		fields1279 := _dollar_dollar.GetConstructs()
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1280) == 0) {
			p.newline()
			for i1282, elem1281 := range unwrapped_fields1280 {
				if (i1282 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1281)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1288 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1288 != nil {
		p.write(*flat1288)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1780 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1780 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1286 := _t1780
		if deconstruct_result1286 != nil {
			unwrapped1287 := deconstruct_result1286
			p.pretty_loop(unwrapped1287)
		} else {
			_dollar_dollar := msg
			var _t1781 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1781 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1284 := _t1781
			if deconstruct_result1284 != nil {
				unwrapped1285 := deconstruct_result1284
				p.pretty_instruction(unwrapped1285)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1295 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1295 != nil {
		p.write(*flat1295)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1782 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1782 = _dollar_dollar.GetAttrs()
		}
		fields1289 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1782}
		unwrapped_fields1290 := fields1289
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1291 := unwrapped_fields1290[0].([]*pb.Instruction)
		p.pretty_init(field1291)
		p.newline()
		field1292 := unwrapped_fields1290[1].(*pb.Script)
		p.pretty_script(field1292)
		field1293 := unwrapped_fields1290[2].([]*pb.Attribute)
		if field1293 != nil {
			p.newline()
			opt_val1294 := field1293
			p.pretty_attrs(opt_val1294)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1299 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1299 != nil {
		p.write(*flat1299)
		return nil
	} else {
		fields1296 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1296) == 0) {
			p.newline()
			for i1298, elem1297 := range fields1296 {
				if (i1298 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1297)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1783 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1783 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1308 := _t1783
		if deconstruct_result1308 != nil {
			unwrapped1309 := deconstruct_result1308
			p.pretty_assign(unwrapped1309)
		} else {
			_dollar_dollar := msg
			var _t1784 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1784 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1306 := _t1784
			if deconstruct_result1306 != nil {
				unwrapped1307 := deconstruct_result1306
				p.pretty_upsert(unwrapped1307)
			} else {
				_dollar_dollar := msg
				var _t1785 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1785 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1304 := _t1785
				if deconstruct_result1304 != nil {
					unwrapped1305 := deconstruct_result1304
					p.pretty_break(unwrapped1305)
				} else {
					_dollar_dollar := msg
					var _t1786 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1786 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1302 := _t1786
					if deconstruct_result1302 != nil {
						unwrapped1303 := deconstruct_result1302
						p.pretty_monoid_def(unwrapped1303)
					} else {
						_dollar_dollar := msg
						var _t1787 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1787 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1300 := _t1787
						if deconstruct_result1300 != nil {
							unwrapped1301 := deconstruct_result1300
							p.pretty_monus_def(unwrapped1301)
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
	flat1317 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1788 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1788 = _dollar_dollar.GetAttrs()
		}
		fields1311 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1788}
		unwrapped_fields1312 := fields1311
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1313 := unwrapped_fields1312[0].(*pb.RelationId)
		p.pretty_relation_id(field1313)
		p.newline()
		field1314 := unwrapped_fields1312[1].(*pb.Abstraction)
		p.pretty_abstraction(field1314)
		field1315 := unwrapped_fields1312[2].([]*pb.Attribute)
		if field1315 != nil {
			p.newline()
			opt_val1316 := field1315
			p.pretty_attrs(opt_val1316)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1789 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1789 = _dollar_dollar.GetAttrs()
		}
		fields1318 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1789}
		unwrapped_fields1319 := fields1318
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1320 := unwrapped_fields1319[0].(*pb.RelationId)
		p.pretty_relation_id(field1320)
		p.newline()
		field1321 := unwrapped_fields1319[1].([]interface{})
		p.pretty_abstraction_with_arity(field1321)
		field1322 := unwrapped_fields1319[2].([]*pb.Attribute)
		if field1322 != nil {
			p.newline()
			opt_val1323 := field1322
			p.pretty_attrs(opt_val1323)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		_t1790 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1325 := []interface{}{_t1790, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1326 := fields1325
		p.write("(")
		p.indent()
		field1327 := unwrapped_fields1326[0].([]interface{})
		p.pretty_bindings(field1327)
		p.newline()
		field1328 := unwrapped_fields1326[1].(*pb.Formula)
		p.pretty_formula(field1328)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1336 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1336 != nil {
		p.write(*flat1336)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1791 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1791 = _dollar_dollar.GetAttrs()
		}
		fields1330 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1791}
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1332 := unwrapped_fields1331[0].(*pb.RelationId)
		p.pretty_relation_id(field1332)
		p.newline()
		field1333 := unwrapped_fields1331[1].(*pb.Abstraction)
		p.pretty_abstraction(field1333)
		field1334 := unwrapped_fields1331[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1344 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1344 != nil {
		p.write(*flat1344)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1792 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1792 = _dollar_dollar.GetAttrs()
		}
		fields1337 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1792}
		unwrapped_fields1338 := fields1337
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1339 := unwrapped_fields1338[0].(*pb.Monoid)
		p.pretty_monoid(field1339)
		p.newline()
		field1340 := unwrapped_fields1338[1].(*pb.RelationId)
		p.pretty_relation_id(field1340)
		p.newline()
		field1341 := unwrapped_fields1338[2].([]interface{})
		p.pretty_abstraction_with_arity(field1341)
		field1342 := unwrapped_fields1338[3].([]*pb.Attribute)
		if field1342 != nil {
			p.newline()
			opt_val1343 := field1342
			p.pretty_attrs(opt_val1343)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1793 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1793 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1351 := _t1793
		if deconstruct_result1351 != nil {
			unwrapped1352 := deconstruct_result1351
			p.pretty_or_monoid(unwrapped1352)
		} else {
			_dollar_dollar := msg
			var _t1794 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1794 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1349 := _t1794
			if deconstruct_result1349 != nil {
				unwrapped1350 := deconstruct_result1349
				p.pretty_min_monoid(unwrapped1350)
			} else {
				_dollar_dollar := msg
				var _t1795 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1795 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1347 := _t1795
				if deconstruct_result1347 != nil {
					unwrapped1348 := deconstruct_result1347
					p.pretty_max_monoid(unwrapped1348)
				} else {
					_dollar_dollar := msg
					var _t1796 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1796 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1345 := _t1796
					if deconstruct_result1345 != nil {
						unwrapped1346 := deconstruct_result1345
						p.pretty_sum_monoid(unwrapped1346)
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
	fields1354 := msg
	_ = fields1354
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1357 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		_dollar_dollar := msg
		fields1355 := _dollar_dollar.GetType()
		unwrapped_fields1356 := fields1355
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1356)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1360 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1360 != nil {
		p.write(*flat1360)
		return nil
	} else {
		_dollar_dollar := msg
		fields1358 := _dollar_dollar.GetType()
		unwrapped_fields1359 := fields1358
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1359)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1363 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1363 != nil {
		p.write(*flat1363)
		return nil
	} else {
		_dollar_dollar := msg
		fields1361 := _dollar_dollar.GetType()
		unwrapped_fields1362 := fields1361
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1362)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1797 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1797 = _dollar_dollar.GetAttrs()
		}
		fields1364 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1797}
		unwrapped_fields1365 := fields1364
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1366 := unwrapped_fields1365[0].(*pb.Monoid)
		p.pretty_monoid(field1366)
		p.newline()
		field1367 := unwrapped_fields1365[1].(*pb.RelationId)
		p.pretty_relation_id(field1367)
		p.newline()
		field1368 := unwrapped_fields1365[2].([]interface{})
		p.pretty_abstraction_with_arity(field1368)
		field1369 := unwrapped_fields1365[3].([]*pb.Attribute)
		if field1369 != nil {
			p.newline()
			opt_val1370 := field1369
			p.pretty_attrs(opt_val1370)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1378 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1378 != nil {
		p.write(*flat1378)
		return nil
	} else {
		_dollar_dollar := msg
		fields1372 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1374 := unwrapped_fields1373[0].(*pb.RelationId)
		p.pretty_relation_id(field1374)
		p.newline()
		field1375 := unwrapped_fields1373[1].(*pb.Abstraction)
		p.pretty_abstraction(field1375)
		p.newline()
		field1376 := unwrapped_fields1373[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1376)
		p.newline()
		field1377 := unwrapped_fields1373[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1377)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		fields1379 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1379) == 0) {
			p.newline()
			for i1381, elem1380 := range fields1379 {
				if (i1381 > 0) {
					p.newline()
				}
				p.pretty_var(elem1380)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1386 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1386 != nil {
		p.write(*flat1386)
		return nil
	} else {
		fields1383 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1383) == 0) {
			p.newline()
			for i1385, elem1384 := range fields1383 {
				if (i1385 > 0) {
					p.newline()
				}
				p.pretty_var(elem1384)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1395 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1395 != nil {
		p.write(*flat1395)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1798 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1798 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1393 := _t1798
		if deconstruct_result1393 != nil {
			unwrapped1394 := deconstruct_result1393
			p.pretty_edb(unwrapped1394)
		} else {
			_dollar_dollar := msg
			var _t1799 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1799 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1391 := _t1799
			if deconstruct_result1391 != nil {
				unwrapped1392 := deconstruct_result1391
				p.pretty_betree_relation(unwrapped1392)
			} else {
				_dollar_dollar := msg
				var _t1800 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1800 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1389 := _t1800
				if deconstruct_result1389 != nil {
					unwrapped1390 := deconstruct_result1389
					p.pretty_csv_data(unwrapped1390)
				} else {
					_dollar_dollar := msg
					var _t1801 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1801 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1387 := _t1801
					if deconstruct_result1387 != nil {
						unwrapped1388 := deconstruct_result1387
						p.pretty_iceberg_data(unwrapped1388)
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
	flat1401 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1401 != nil {
		p.write(*flat1401)
		return nil
	} else {
		_dollar_dollar := msg
		fields1396 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1397 := fields1396
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1398 := unwrapped_fields1397[0].(*pb.RelationId)
		p.pretty_relation_id(field1398)
		p.newline()
		field1399 := unwrapped_fields1397[1].([]string)
		p.pretty_edb_path(field1399)
		p.newline()
		field1400 := unwrapped_fields1397[2].([]*pb.Type)
		p.pretty_edb_types(field1400)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		fields1402 := msg
		p.write("[")
		p.indent()
		for i1404, elem1403 := range fields1402 {
			if (i1404 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1403))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1409 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1409 != nil {
		p.write(*flat1409)
		return nil
	} else {
		fields1406 := msg
		p.write("[")
		p.indent()
		for i1408, elem1407 := range fields1406 {
			if (i1408 > 0) {
				p.newline()
			}
			p.pretty_type(elem1407)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1414 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1414 != nil {
		p.write(*flat1414)
		return nil
	} else {
		_dollar_dollar := msg
		fields1410 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1411 := fields1410
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1412 := unwrapped_fields1411[0].(*pb.RelationId)
		p.pretty_relation_id(field1412)
		p.newline()
		field1413 := unwrapped_fields1411[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1413)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1420 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1420 != nil {
		p.write(*flat1420)
		return nil
	} else {
		_dollar_dollar := msg
		_t1802 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1415 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1802}
		unwrapped_fields1416 := fields1415
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1417 := unwrapped_fields1416[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1417)
		p.newline()
		field1418 := unwrapped_fields1416[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1418)
		p.newline()
		field1419 := unwrapped_fields1416[2].([][]interface{})
		p.pretty_config_dict(field1419)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1424 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1424 != nil {
		p.write(*flat1424)
		return nil
	} else {
		fields1421 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1421) == 0) {
			p.newline()
			for i1423, elem1422 := range fields1421 {
				if (i1423 > 0) {
					p.newline()
				}
				p.pretty_type(elem1422)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1428 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1428 != nil {
		p.write(*flat1428)
		return nil
	} else {
		fields1425 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1425) == 0) {
			p.newline()
			for i1427, elem1426 := range fields1425 {
				if (i1427 > 0) {
					p.newline()
				}
				p.pretty_type(elem1426)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1438 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1438 != nil {
		p.write(*flat1438)
		return nil
	} else {
		_dollar_dollar := msg
		_t1803 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1804 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1429 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1803, _t1804, _dollar_dollar.GetAsof()}
		unwrapped_fields1430 := fields1429
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1431 := unwrapped_fields1430[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1431)
		p.newline()
		field1432 := unwrapped_fields1430[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1432)
		field1433 := unwrapped_fields1430[2].([]*pb.GNFColumn)
		if field1433 != nil {
			p.newline()
			opt_val1434 := field1433
			p.pretty_gnf_columns(opt_val1434)
		}
		field1435 := unwrapped_fields1430[3].(*pb.Relations)
		if field1435 != nil {
			p.newline()
			opt_val1436 := field1435
			p.pretty_relations(opt_val1436)
		}
		p.newline()
		field1437 := unwrapped_fields1430[4].(string)
		p.pretty_csv_asof(field1437)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1445 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1445 != nil {
		p.write(*flat1445)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1805 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1805 = _dollar_dollar.GetPaths()
		}
		var _t1806 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1806 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1439 := []interface{}{_t1805, _t1806}
		unwrapped_fields1440 := fields1439
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1441 := unwrapped_fields1440[0].([]string)
		if field1441 != nil {
			p.newline()
			opt_val1442 := field1441
			p.pretty_csv_locator_paths(opt_val1442)
		}
		field1443 := unwrapped_fields1440[1].(*string)
		if field1443 != nil {
			p.newline()
			opt_val1444 := *field1443
			p.pretty_csv_locator_inline_data(opt_val1444)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		fields1446 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1446) == 0) {
			p.newline()
			for i1448, elem1447 := range fields1446 {
				if (i1448 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1447))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1451 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1451 != nil {
		p.write(*flat1451)
		return nil
	} else {
		fields1450 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1450))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		_dollar_dollar := msg
		_t1807 := p.deconstruct_csv_config(_dollar_dollar)
		_t1808 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1452 := []interface{}{_t1807, _t1808}
		unwrapped_fields1453 := fields1452
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1454 := unwrapped_fields1453[0].([][]interface{})
		p.pretty_config_dict(field1454)
		field1455 := unwrapped_fields1453[1].([][]interface{})
		if field1455 != nil {
			p.newline()
			opt_val1456 := field1455
			p.pretty__storage_integration(opt_val1456)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1459 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1459 != nil {
		p.write(*flat1459)
		return nil
	} else {
		fields1458 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1458)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1463 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1463 != nil {
		p.write(*flat1463)
		return nil
	} else {
		fields1460 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1460) == 0) {
			p.newline()
			for i1462, elem1461 := range fields1460 {
				if (i1462 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1461)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1809 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1809 = _dollar_dollar.GetTargetId()
		}
		fields1464 := []interface{}{_dollar_dollar.GetColumnPath(), _t1809, _dollar_dollar.GetTypes()}
		unwrapped_fields1465 := fields1464
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1466 := unwrapped_fields1465[0].([]string)
		p.pretty_gnf_column_path(field1466)
		field1467 := unwrapped_fields1465[1].(*pb.RelationId)
		if field1467 != nil {
			p.newline()
			opt_val1468 := field1467
			p.pretty_relation_id(opt_val1468)
		}
		p.newline()
		p.write("[")
		field1469 := unwrapped_fields1465[2].([]*pb.Type)
		for i1471, elem1470 := range field1469 {
			if (i1471 > 0) {
				p.newline()
			}
			p.pretty_type(elem1470)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1479 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1479 != nil {
		p.write(*flat1479)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1810 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1810 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1477 := _t1810
		if deconstruct_result1477 != nil {
			unwrapped1478 := *deconstruct_result1477
			p.write(p.formatStringValue(unwrapped1478))
		} else {
			_dollar_dollar := msg
			var _t1811 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1811 = _dollar_dollar
			}
			deconstruct_result1473 := _t1811
			if deconstruct_result1473 != nil {
				unwrapped1474 := deconstruct_result1473
				p.write("[")
				p.indent()
				for i1476, elem1475 := range unwrapped1474 {
					if (i1476 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1475))
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

func (p *PrettyPrinter) pretty_relations(msg *pb.Relations) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_relations(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		_dollar_dollar := msg
		fields1480 := []interface{}{_dollar_dollar.GetKeys(), _dollar_dollar}
		unwrapped_fields1481 := fields1480
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1482 := unwrapped_fields1481[0].([]*pb.NamedColumn)
		p.pretty_relation_keys(field1482)
		p.newline()
		field1483 := unwrapped_fields1481[1].(*pb.Relations)
		p.pretty_relation_body(field1483)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []*pb.NamedColumn) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1485) == 0) {
			p.newline()
			for i1487, elem1486 := range fields1485 {
				if (i1487 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1486)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_named_column(msg *pb.NamedColumn) interface{} {
	flat1493 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1493 != nil {
		p.write(*flat1493)
		return nil
	} else {
		_dollar_dollar := msg
		fields1489 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1490 := fields1489
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1491 := unwrapped_fields1490[0].(string)
		p.write(p.formatStringValue(field1491))
		p.newline()
		field1492 := unwrapped_fields1490[1].(*pb.Type)
		p.pretty_type(field1492)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.Relations) interface{} {
	flat1500 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1500 != nil {
		p.write(*flat1500)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1812 []*pb.OutputRelation
		if (len(_dollar_dollar.GetInserts()) == 0 && len(_dollar_dollar.GetDeletes()) == 0) {
			_t1812 = _dollar_dollar.GetRelations()
		}
		deconstruct_result1498 := _t1812
		if deconstruct_result1498 != nil {
			unwrapped1499 := deconstruct_result1498
			p.pretty_non_cdc_relations(unwrapped1499)
		} else {
			_dollar_dollar := msg
			var _t1813 []interface{}
			if !((len(_dollar_dollar.GetInserts()) == 0 && len(_dollar_dollar.GetDeletes()) == 0)) {
				_t1813 = []interface{}{_dollar_dollar.GetInserts(), _dollar_dollar.GetDeletes()}
			}
			deconstruct_result1494 := _t1813
			if deconstruct_result1494 != nil {
				unwrapped1495 := deconstruct_result1494
				field1496 := unwrapped1495[0].([]*pb.OutputRelation)
				p.pretty_cdc_inserts(field1496)
				p.write(" ")
				field1497 := unwrapped1495[1].([]*pb.OutputRelation)
				p.pretty_cdc_deletes(field1497)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.OutputRelation) interface{} {
	flat1504 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		fields1501 := msg
		for i1503, elem1502 := range fields1501 {
			if (i1503 > 0) {
				p.newline()
			}
			p.pretty_output_relation(elem1502)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_output_relation(msg *pb.OutputRelation) interface{} {
	flat1511 := p.tryFlat(msg, func() { p.pretty_output_relation(msg) })
	if flat1511 != nil {
		p.write(*flat1511)
		return nil
	} else {
		_dollar_dollar := msg
		fields1505 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1506 := fields1505
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1507 := unwrapped_fields1506[0].(*pb.RelationId)
		p.pretty_relation_id(field1507)
		field1508 := unwrapped_fields1506[1].([]*pb.NamedColumn)
		if !(len(field1508) == 0) {
			p.newline()
			for i1510, elem1509 := range field1508 {
				if (i1510 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1509)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.OutputRelation) interface{} {
	flat1515 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1515 != nil {
		p.write(*flat1515)
		return nil
	} else {
		fields1512 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1512) == 0) {
			p.newline()
			for i1514, elem1513 := range fields1512 {
				if (i1514 > 0) {
					p.newline()
				}
				p.pretty_output_relation(elem1513)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.OutputRelation) interface{} {
	flat1519 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1519 != nil {
		p.write(*flat1519)
		return nil
	} else {
		fields1516 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1516) == 0) {
			p.newline()
			for i1518, elem1517 := range fields1516 {
				if (i1518 > 0) {
					p.newline()
				}
				p.pretty_output_relation(elem1517)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		fields1520 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1520))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1532 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1532 != nil {
		p.write(*flat1532)
		return nil
	} else {
		_dollar_dollar := msg
		_t1814 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1815 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1522 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1814, _t1815, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1523 := fields1522
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1524 := unwrapped_fields1523[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1524)
		p.newline()
		field1525 := unwrapped_fields1523[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1525)
		p.newline()
		field1526 := unwrapped_fields1523[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1526)
		field1527 := unwrapped_fields1523[3].(*string)
		if field1527 != nil {
			p.newline()
			opt_val1528 := *field1527
			p.pretty_iceberg_from_snapshot(opt_val1528)
		}
		field1529 := unwrapped_fields1523[4].(*string)
		if field1529 != nil {
			p.newline()
			opt_val1530 := *field1529
			p.pretty_iceberg_to_snapshot(opt_val1530)
		}
		p.newline()
		field1531 := unwrapped_fields1523[5].(bool)
		p.pretty_boolean_value(field1531)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1538 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1538 != nil {
		p.write(*flat1538)
		return nil
	} else {
		_dollar_dollar := msg
		fields1533 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1534 := fields1533
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1535 := unwrapped_fields1534[0].(string)
		p.pretty_iceberg_locator_table_name(field1535)
		p.newline()
		field1536 := unwrapped_fields1534[1].([]string)
		p.pretty_iceberg_locator_namespace(field1536)
		p.newline()
		field1537 := unwrapped_fields1534[2].(string)
		p.pretty_iceberg_locator_warehouse(field1537)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1540 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1540 != nil {
		p.write(*flat1540)
		return nil
	} else {
		fields1539 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1539))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1544 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1544 != nil {
		p.write(*flat1544)
		return nil
	} else {
		fields1541 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1541) == 0) {
			p.newline()
			for i1543, elem1542 := range fields1541 {
				if (i1543 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1542))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1546 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1546 != nil {
		p.write(*flat1546)
		return nil
	} else {
		fields1545 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1545))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1554 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1554 != nil {
		p.write(*flat1554)
		return nil
	} else {
		_dollar_dollar := msg
		_t1816 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1547 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1816, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1548 := fields1547
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1549 := unwrapped_fields1548[0].(string)
		p.pretty_iceberg_catalog_uri(field1549)
		field1550 := unwrapped_fields1548[1].(*string)
		if field1550 != nil {
			p.newline()
			opt_val1551 := *field1550
			p.pretty_iceberg_catalog_config_scope(opt_val1551)
		}
		p.newline()
		field1552 := unwrapped_fields1548[2].([][]interface{})
		p.pretty_iceberg_properties(field1552)
		p.newline()
		field1553 := unwrapped_fields1548[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1553)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1556 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1556 != nil {
		p.write(*flat1556)
		return nil
	} else {
		fields1555 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1555))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1558 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1558 != nil {
		p.write(*flat1558)
		return nil
	} else {
		fields1557 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1557))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1562 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1562 != nil {
		p.write(*flat1562)
		return nil
	} else {
		fields1559 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1559) == 0) {
			p.newline()
			for i1561, elem1560 := range fields1559 {
				if (i1561 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1560)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		_dollar_dollar := msg
		fields1563 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1564 := fields1563
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1565 := unwrapped_fields1564[0].(string)
		p.write(p.formatStringValue(field1565))
		p.newline()
		field1566 := unwrapped_fields1564[1].(string)
		p.write(p.formatStringValue(field1566))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1571 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1571 != nil {
		p.write(*flat1571)
		return nil
	} else {
		fields1568 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1568) == 0) {
			p.newline()
			for i1570, elem1569 := range fields1568 {
				if (i1570 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1569)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1576 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1576 != nil {
		p.write(*flat1576)
		return nil
	} else {
		_dollar_dollar := msg
		_t1817 := p.mask_secret_value(_dollar_dollar)
		fields1572 := []interface{}{_dollar_dollar[0].(string), _t1817}
		unwrapped_fields1573 := fields1572
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1574 := unwrapped_fields1573[0].(string)
		p.write(p.formatStringValue(field1574))
		p.newline()
		field1575 := unwrapped_fields1573[1].(string)
		p.write(p.formatStringValue(field1575))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1578 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1578 != nil {
		p.write(*flat1578)
		return nil
	} else {
		fields1577 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1577))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1580 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1580 != nil {
		p.write(*flat1580)
		return nil
	} else {
		fields1579 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1579))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1583 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1583 != nil {
		p.write(*flat1583)
		return nil
	} else {
		_dollar_dollar := msg
		fields1581 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1582 := fields1581
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1582)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1588 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1588 != nil {
		p.write(*flat1588)
		return nil
	} else {
		_dollar_dollar := msg
		fields1584 := _dollar_dollar.GetRelations()
		unwrapped_fields1585 := fields1584
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1585) == 0) {
			p.newline()
			for i1587, elem1586 := range unwrapped_fields1585 {
				if (i1587 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1586)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1595 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1595 != nil {
		p.write(*flat1595)
		return nil
	} else {
		_dollar_dollar := msg
		fields1589 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1590 := fields1589
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1591 := unwrapped_fields1590[0].([]string)
		p.pretty_edb_path(field1591)
		field1592 := unwrapped_fields1590[1].([]*pb.SnapshotMapping)
		if !(len(field1592) == 0) {
			p.newline()
			for i1594, elem1593 := range field1592 {
				if (i1594 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1593)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1600 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1600 != nil {
		p.write(*flat1600)
		return nil
	} else {
		_dollar_dollar := msg
		fields1596 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1597 := fields1596
		field1598 := unwrapped_fields1597[0].([]string)
		p.pretty_edb_path(field1598)
		p.write(" ")
		field1599 := unwrapped_fields1597[1].(*pb.RelationId)
		p.pretty_relation_id(field1599)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1604 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1604 != nil {
		p.write(*flat1604)
		return nil
	} else {
		fields1601 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1601) == 0) {
			p.newline()
			for i1603, elem1602 := range fields1601 {
				if (i1603 > 0) {
					p.newline()
				}
				p.pretty_read(elem1602)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1615 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1615 != nil {
		p.write(*flat1615)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1818 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1818 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1613 := _t1818
		if deconstruct_result1613 != nil {
			unwrapped1614 := deconstruct_result1613
			p.pretty_demand(unwrapped1614)
		} else {
			_dollar_dollar := msg
			var _t1819 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1819 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1611 := _t1819
			if deconstruct_result1611 != nil {
				unwrapped1612 := deconstruct_result1611
				p.pretty_output(unwrapped1612)
			} else {
				_dollar_dollar := msg
				var _t1820 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1820 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1609 := _t1820
				if deconstruct_result1609 != nil {
					unwrapped1610 := deconstruct_result1609
					p.pretty_what_if(unwrapped1610)
				} else {
					_dollar_dollar := msg
					var _t1821 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1821 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1607 := _t1821
					if deconstruct_result1607 != nil {
						unwrapped1608 := deconstruct_result1607
						p.pretty_abort(unwrapped1608)
					} else {
						_dollar_dollar := msg
						var _t1822 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1822 = _dollar_dollar.GetExport()
						}
						deconstruct_result1605 := _t1822
						if deconstruct_result1605 != nil {
							unwrapped1606 := deconstruct_result1605
							p.pretty_export(unwrapped1606)
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
	flat1618 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1618 != nil {
		p.write(*flat1618)
		return nil
	} else {
		_dollar_dollar := msg
		fields1616 := _dollar_dollar.GetRelationId()
		unwrapped_fields1617 := fields1616
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1617)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1623 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1623 != nil {
		p.write(*flat1623)
		return nil
	} else {
		_dollar_dollar := msg
		fields1619 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1620 := fields1619
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1621 := unwrapped_fields1620[0].(string)
		p.pretty_name(field1621)
		p.newline()
		field1622 := unwrapped_fields1620[1].(*pb.RelationId)
		p.pretty_relation_id(field1622)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1628 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1628 != nil {
		p.write(*flat1628)
		return nil
	} else {
		_dollar_dollar := msg
		fields1624 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1625 := fields1624
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1626 := unwrapped_fields1625[0].(string)
		p.pretty_name(field1626)
		p.newline()
		field1627 := unwrapped_fields1625[1].(*pb.Epoch)
		p.pretty_epoch(field1627)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1634 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1634 != nil {
		p.write(*flat1634)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1823 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1823 = ptr(_dollar_dollar.GetName())
		}
		fields1629 := []interface{}{_t1823, _dollar_dollar.GetRelationId()}
		unwrapped_fields1630 := fields1629
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1631 := unwrapped_fields1630[0].(*string)
		if field1631 != nil {
			p.newline()
			opt_val1632 := *field1631
			p.pretty_name(opt_val1632)
		}
		p.newline()
		field1633 := unwrapped_fields1630[1].(*pb.RelationId)
		p.pretty_relation_id(field1633)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1639 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1639 != nil {
		p.write(*flat1639)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1824 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1824 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1637 := _t1824
		if deconstruct_result1637 != nil {
			unwrapped1638 := deconstruct_result1637
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1638)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1825 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1825 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1635 := _t1825
			if deconstruct_result1635 != nil {
				unwrapped1636 := deconstruct_result1635
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1636)
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
	flat1650 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1650 != nil {
		p.write(*flat1650)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1826 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1826 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1645 := _t1826
		if deconstruct_result1645 != nil {
			unwrapped1646 := deconstruct_result1645
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1647 := unwrapped1646[0].(string)
			p.pretty_export_csv_path(field1647)
			p.newline()
			field1648 := unwrapped1646[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1648)
			p.newline()
			field1649 := unwrapped1646[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1649)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1827 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1828 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1827 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1828}
			}
			deconstruct_result1640 := _t1827
			if deconstruct_result1640 != nil {
				unwrapped1641 := deconstruct_result1640
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1642 := unwrapped1641[0].(string)
				p.pretty_export_csv_path(field1642)
				p.newline()
				field1643 := unwrapped1641[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1643)
				p.newline()
				field1644 := unwrapped1641[2].([][]interface{})
				p.pretty_config_dict(field1644)
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
	flat1652 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1652 != nil {
		p.write(*flat1652)
		return nil
	} else {
		fields1651 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1651))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1659 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1659 != nil {
		p.write(*flat1659)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1829 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1829 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1655 := _t1829
		if deconstruct_result1655 != nil {
			unwrapped1656 := deconstruct_result1655
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1656) == 0) {
				p.newline()
				for i1658, elem1657 := range unwrapped1656 {
					if (i1658 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1657)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1830 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1830 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1653 := _t1830
			if deconstruct_result1653 != nil {
				unwrapped1654 := deconstruct_result1653
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1654)
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
	flat1664 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1664 != nil {
		p.write(*flat1664)
		return nil
	} else {
		_dollar_dollar := msg
		fields1660 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1661 := fields1660
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1662 := unwrapped_fields1661[0].(string)
		p.write(p.formatStringValue(field1662))
		p.newline()
		field1663 := unwrapped_fields1661[1].(*pb.RelationId)
		p.pretty_relation_id(field1663)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1668 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1668 != nil {
		p.write(*flat1668)
		return nil
	} else {
		fields1665 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1665) == 0) {
			p.newline()
			for i1667, elem1666 := range fields1665 {
				if (i1667 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1666)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1677 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1677 != nil {
		p.write(*flat1677)
		return nil
	} else {
		_dollar_dollar := msg
		_t1831 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1669 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1831}
		unwrapped_fields1670 := fields1669
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1671 := unwrapped_fields1670[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1671)
		p.newline()
		field1672 := unwrapped_fields1670[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1672)
		p.newline()
		field1673 := unwrapped_fields1670[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1673)
		p.newline()
		field1674 := unwrapped_fields1670[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1674)
		field1675 := unwrapped_fields1670[4].([][]interface{})
		if field1675 != nil {
			p.newline()
			opt_val1676 := field1675
			p.pretty_config_dict(opt_val1676)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1679 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1679 != nil {
		p.write(*flat1679)
		return nil
	} else {
		fields1678 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1678)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1683 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1683 != nil {
		p.write(*flat1683)
		return nil
	} else {
		fields1680 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1680) == 0) {
			p.newline()
			for i1682, elem1681 := range fields1680 {
				if (i1682 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1681)
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
		_t1885 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1885)
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
	case *pb.Relations:
		p.pretty_relations(m)
	case []*pb.NamedColumn:
		p.pretty_relation_keys(m)
	case *pb.NamedColumn:
		p.pretty_named_column(m)
	case []*pb.OutputRelation:
		p.pretty_non_cdc_relations(m)
	case *pb.OutputRelation:
		p.pretty_output_relation(m)
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
