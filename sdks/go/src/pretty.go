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

func (p *PrettyPrinter) deconstruct_relation_keys(msg *pb.TargetRelations) []interface{} {
	return []interface{}{msg.GetKeys(), msg.GetSyntheticKey()}
}

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1854 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1854
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.TargetRelations {
	var _t1855 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1855
	return nil
}

func (p *PrettyPrinter) deconstruct_export_csv_output_location(msg *pb.ExportCSVConfig) []interface{} {
	return []interface{}{msg.GetPath(), msg.GetTransactionOutputName()}
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1856 := &pb.Value{}
	_t1856.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1856
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1857 := &pb.Value{}
	_t1857.Value = &pb.Value_IntValue{IntValue: v}
	return _t1857
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1858 := &pb.Value{}
	_t1858.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1858
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1859 := &pb.Value{}
	_t1859.Value = &pb.Value_StringValue{StringValue: v}
	return _t1859
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1860 := &pb.Value{}
	_t1860.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1860
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1861 := &pb.Value{}
	_t1861.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1861
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1862 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1862})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1863 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1863})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1864 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1864})
			}
		}
	}
	_t1865 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1865})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1866 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1866})
	_t1867 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1867})
	if msg.GetNewLine() != "" {
		_t1868 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1868})
	}
	_t1869 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1869})
	_t1870 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1870})
	_t1871 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1871})
	if msg.GetComment() != "" {
		_t1872 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1872})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1873 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1873})
	}
	_t1874 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1874})
	_t1875 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1875})
	_t1876 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1876})
	if msg.GetPartitionSizeMb() != 0 {
		_t1877 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1877})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1878 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1878
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1879 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1879})
	}
	if si.GetAzureSasToken() != "" {
		_t1880 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1880})
	}
	if si.GetS3Region() != "" {
		_t1881 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1881})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1882 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1882})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1883 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1883})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1884 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1884})
	_t1885 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1885})
	_t1886 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1886})
	_t1887 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1887})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1888 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1888})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1889 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1889})
		}
	}
	_t1890 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1890})
	_t1891 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1891})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1892 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1892})
	}
	if msg.Compression != nil {
		_t1893 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1893})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1894 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1894})
	}
	if msg.SyntaxMissingString != nil {
		_t1895 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1895})
	}
	if msg.SyntaxDelim != nil {
		_t1896 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1896})
	}
	if msg.SyntaxQuotechar != nil {
		_t1897 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1897})
	}
	if msg.SyntaxEscapechar != nil {
		_t1898 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1898})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1899 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1899
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1900 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1900
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1901 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1901
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1902 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1902})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1903 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1903})
	}
	if msg.GetCompression() != "" {
		_t1904 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1904})
	}
	var _t1905 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1905
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1906 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1906
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
	flat859 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat859 != nil {
		p.write(*flat859)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1700 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1700 = _dollar_dollar.GetConfigure()
		}
		var _t1701 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1701 = _dollar_dollar.GetSync()
		}
		fields850 := []interface{}{_t1700, _t1701, _dollar_dollar.GetEpochs()}
		unwrapped_fields851 := fields850
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field852 := unwrapped_fields851[0].(*pb.Configure)
		if field852 != nil {
			p.newline()
			opt_val853 := field852
			p.pretty_configure(opt_val853)
		}
		field854 := unwrapped_fields851[1].(*pb.Sync)
		if field854 != nil {
			p.newline()
			opt_val855 := field854
			p.pretty_sync(opt_val855)
		}
		field856 := unwrapped_fields851[2].([]*pb.Epoch)
		if !(len(field856) == 0) {
			p.newline()
			for i858, elem857 := range field856 {
				if (i858 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem857)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat862 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		_dollar_dollar := msg
		_t1702 := p.deconstruct_configure(_dollar_dollar)
		fields860 := _t1702
		unwrapped_fields861 := fields860
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields861)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat866 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat866 != nil {
		p.write(*flat866)
		return nil
	} else {
		fields863 := msg
		p.write("{")
		p.indent()
		if !(len(fields863) == 0) {
			p.newline()
			for i865, elem864 := range fields863 {
				if (i865 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem864)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		fields867 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields868 := fields867
		p.write(":")
		field869 := unwrapped_fields868[0].(string)
		p.write(field869)
		p.write(" ")
		field870 := unwrapped_fields868[1].(*pb.Value)
		p.pretty_raw_value(field870)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat897 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat897 != nil {
		p.write(*flat897)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1703 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result895 := _t1703
		if deconstruct_result895 != nil {
			unwrapped896 := deconstruct_result895
			p.pretty_raw_date(unwrapped896)
		} else {
			_dollar_dollar := msg
			var _t1704 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1704 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result893 := _t1704
			if deconstruct_result893 != nil {
				unwrapped894 := deconstruct_result893
				p.pretty_raw_datetime(unwrapped894)
			} else {
				_dollar_dollar := msg
				var _t1705 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1705 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result891 := _t1705
				if deconstruct_result891 != nil {
					unwrapped892 := *deconstruct_result891
					p.write(p.formatStringValue(unwrapped892))
				} else {
					_dollar_dollar := msg
					var _t1706 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1706 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result889 := _t1706
					if deconstruct_result889 != nil {
						unwrapped890 := *deconstruct_result889
						p.write(fmt.Sprintf("%di32", unwrapped890))
					} else {
						_dollar_dollar := msg
						var _t1707 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1707 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result887 := _t1707
						if deconstruct_result887 != nil {
							unwrapped888 := *deconstruct_result887
							p.write(fmt.Sprintf("%d", unwrapped888))
						} else {
							_dollar_dollar := msg
							var _t1708 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1708 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result885 := _t1708
							if deconstruct_result885 != nil {
								unwrapped886 := *deconstruct_result885
								p.write(formatFloat32(unwrapped886))
							} else {
								_dollar_dollar := msg
								var _t1709 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1709 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result883 := _t1709
								if deconstruct_result883 != nil {
									unwrapped884 := *deconstruct_result883
									p.write(formatFloat64(unwrapped884))
								} else {
									_dollar_dollar := msg
									var _t1710 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1710 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result881 := _t1710
									if deconstruct_result881 != nil {
										unwrapped882 := *deconstruct_result881
										p.write(fmt.Sprintf("%du32", unwrapped882))
									} else {
										_dollar_dollar := msg
										var _t1711 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1711 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result879 := _t1711
										if deconstruct_result879 != nil {
											unwrapped880 := deconstruct_result879
											p.write(p.formatUint128(unwrapped880))
										} else {
											_dollar_dollar := msg
											var _t1712 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1712 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result877 := _t1712
											if deconstruct_result877 != nil {
												unwrapped878 := deconstruct_result877
												p.write(p.formatInt128(unwrapped878))
											} else {
												_dollar_dollar := msg
												var _t1713 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1713 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result875 := _t1713
												if deconstruct_result875 != nil {
													unwrapped876 := deconstruct_result875
													p.write(p.formatDecimal(unwrapped876))
												} else {
													_dollar_dollar := msg
													var _t1714 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1714 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result873 := _t1714
													if deconstruct_result873 != nil {
														unwrapped874 := *deconstruct_result873
														p.pretty_boolean_value(unwrapped874)
													} else {
														fields872 := msg
														_ = fields872
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
	flat903 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat903 != nil {
		p.write(*flat903)
		return nil
	} else {
		_dollar_dollar := msg
		fields898 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields899 := fields898
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field900 := unwrapped_fields899[0].(int64)
		p.write(fmt.Sprintf("%d", field900))
		p.newline()
		field901 := unwrapped_fields899[1].(int64)
		p.write(fmt.Sprintf("%d", field901))
		p.newline()
		field902 := unwrapped_fields899[2].(int64)
		p.write(fmt.Sprintf("%d", field902))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat914 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat914 != nil {
		p.write(*flat914)
		return nil
	} else {
		_dollar_dollar := msg
		fields904 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields905 := fields904
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field906 := unwrapped_fields905[0].(int64)
		p.write(fmt.Sprintf("%d", field906))
		p.newline()
		field907 := unwrapped_fields905[1].(int64)
		p.write(fmt.Sprintf("%d", field907))
		p.newline()
		field908 := unwrapped_fields905[2].(int64)
		p.write(fmt.Sprintf("%d", field908))
		p.newline()
		field909 := unwrapped_fields905[3].(int64)
		p.write(fmt.Sprintf("%d", field909))
		p.newline()
		field910 := unwrapped_fields905[4].(int64)
		p.write(fmt.Sprintf("%d", field910))
		p.newline()
		field911 := unwrapped_fields905[5].(int64)
		p.write(fmt.Sprintf("%d", field911))
		field912 := unwrapped_fields905[6].(*int64)
		if field912 != nil {
			p.newline()
			opt_val913 := *field912
			p.write(fmt.Sprintf("%d", opt_val913))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1715 []interface{}
	if _dollar_dollar {
		_t1715 = []interface{}{}
	}
	deconstruct_result917 := _t1715
	if deconstruct_result917 != nil {
		unwrapped918 := deconstruct_result917
		_ = unwrapped918
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1716 []interface{}
		if !(_dollar_dollar) {
			_t1716 = []interface{}{}
		}
		deconstruct_result915 := _t1716
		if deconstruct_result915 != nil {
			unwrapped916 := deconstruct_result915
			_ = unwrapped916
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat923 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		fields919 := _dollar_dollar.GetFragments()
		unwrapped_fields920 := fields919
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields920) == 0) {
			p.newline()
			for i922, elem921 := range unwrapped_fields920 {
				if (i922 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem921)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat926 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat926 != nil {
		p.write(*flat926)
		return nil
	} else {
		_dollar_dollar := msg
		fields924 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields925 := fields924
		p.write(":")
		p.write(unwrapped_fields925)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat933 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat933 != nil {
		p.write(*flat933)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1717 = _dollar_dollar.GetWrites()
		}
		var _t1718 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1718 = _dollar_dollar.GetReads()
		}
		fields927 := []interface{}{_t1717, _t1718}
		unwrapped_fields928 := fields927
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field929 := unwrapped_fields928[0].([]*pb.Write)
		if field929 != nil {
			p.newline()
			opt_val930 := field929
			p.pretty_epoch_writes(opt_val930)
		}
		field931 := unwrapped_fields928[1].([]*pb.Read)
		if field931 != nil {
			p.newline()
			opt_val932 := field931
			p.pretty_epoch_reads(opt_val932)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat937 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat937 != nil {
		p.write(*flat937)
		return nil
	} else {
		fields934 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields934) == 0) {
			p.newline()
			for i936, elem935 := range fields934 {
				if (i936 > 0) {
					p.newline()
				}
				p.pretty_write(elem935)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1719 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1719 = _dollar_dollar.GetDefine()
		}
		deconstruct_result944 := _t1719
		if deconstruct_result944 != nil {
			unwrapped945 := deconstruct_result944
			p.pretty_define(unwrapped945)
		} else {
			_dollar_dollar := msg
			var _t1720 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1720 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result942 := _t1720
			if deconstruct_result942 != nil {
				unwrapped943 := deconstruct_result942
				p.pretty_undefine(unwrapped943)
			} else {
				_dollar_dollar := msg
				var _t1721 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1721 = _dollar_dollar.GetContext()
				}
				deconstruct_result940 := _t1721
				if deconstruct_result940 != nil {
					unwrapped941 := deconstruct_result940
					p.pretty_context(unwrapped941)
				} else {
					_dollar_dollar := msg
					var _t1722 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1722 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result938 := _t1722
					if deconstruct_result938 != nil {
						unwrapped939 := deconstruct_result938
						p.pretty_snapshot(unwrapped939)
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
	flat949 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		_dollar_dollar := msg
		fields947 := _dollar_dollar.GetFragment()
		unwrapped_fields948 := fields947
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields948)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat956 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat956 != nil {
		p.write(*flat956)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields950 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields951 := fields950
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field952 := unwrapped_fields951[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field952)
		field953 := unwrapped_fields951[1].([]*pb.Declaration)
		if !(len(field953) == 0) {
			p.newline()
			for i955, elem954 := range field953 {
				if (i955 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem954)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		fields957 := msg
		p.pretty_fragment_id(fields957)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat967 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat967 != nil {
		p.write(*flat967)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1723 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1723 = _dollar_dollar.GetDef()
		}
		deconstruct_result965 := _t1723
		if deconstruct_result965 != nil {
			unwrapped966 := deconstruct_result965
			p.pretty_def(unwrapped966)
		} else {
			_dollar_dollar := msg
			var _t1724 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1724 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result963 := _t1724
			if deconstruct_result963 != nil {
				unwrapped964 := deconstruct_result963
				p.pretty_algorithm(unwrapped964)
			} else {
				_dollar_dollar := msg
				var _t1725 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1725 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result961 := _t1725
				if deconstruct_result961 != nil {
					unwrapped962 := deconstruct_result961
					p.pretty_constraint(unwrapped962)
				} else {
					_dollar_dollar := msg
					var _t1726 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1726 = _dollar_dollar.GetData()
					}
					deconstruct_result959 := _t1726
					if deconstruct_result959 != nil {
						unwrapped960 := deconstruct_result959
						p.pretty_data(unwrapped960)
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
	flat974 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat974 != nil {
		p.write(*flat974)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1727 = _dollar_dollar.GetAttrs()
		}
		fields968 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1727}
		unwrapped_fields969 := fields968
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field970 := unwrapped_fields969[0].(*pb.RelationId)
		p.pretty_relation_id(field970)
		p.newline()
		field971 := unwrapped_fields969[1].(*pb.Abstraction)
		p.pretty_abstraction(field971)
		field972 := unwrapped_fields969[2].([]*pb.Attribute)
		if field972 != nil {
			p.newline()
			opt_val973 := field972
			p.pretty_attrs(opt_val973)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat979 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat979 != nil {
		p.write(*flat979)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1728 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1729 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1728 = ptr(_t1729)
		}
		deconstruct_result977 := _t1728
		if deconstruct_result977 != nil {
			unwrapped978 := *deconstruct_result977
			p.write(":")
			p.write(unwrapped978)
		} else {
			_dollar_dollar := msg
			_t1730 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result975 := _t1730
			if deconstruct_result975 != nil {
				unwrapped976 := deconstruct_result975
				p.write(p.formatUint128(unwrapped976))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat984 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat984 != nil {
		p.write(*flat984)
		return nil
	} else {
		_dollar_dollar := msg
		_t1731 := p.deconstruct_bindings(_dollar_dollar)
		fields980 := []interface{}{_t1731, _dollar_dollar.GetValue()}
		unwrapped_fields981 := fields980
		p.write("(")
		p.indent()
		field982 := unwrapped_fields981[0].([]interface{})
		p.pretty_bindings(field982)
		p.newline()
		field983 := unwrapped_fields981[1].(*pb.Formula)
		p.pretty_formula(field983)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat992 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat992 != nil {
		p.write(*flat992)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1732 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1732 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields985 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1732}
		unwrapped_fields986 := fields985
		p.write("[")
		p.indent()
		field987 := unwrapped_fields986[0].([]*pb.Binding)
		for i989, elem988 := range field987 {
			if (i989 > 0) {
				p.newline()
			}
			p.pretty_binding(elem988)
		}
		field990 := unwrapped_fields986[1].([]*pb.Binding)
		if field990 != nil {
			p.newline()
			opt_val991 := field990
			p.pretty_value_bindings(opt_val991)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		_dollar_dollar := msg
		fields993 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields994 := fields993
		field995 := unwrapped_fields994[0].(string)
		p.write(field995)
		p.write("::")
		field996 := unwrapped_fields994[1].(*pb.Type)
		p.pretty_type(field996)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1026 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1026 != nil {
		p.write(*flat1026)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1733 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1733 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1024 := _t1733
		if deconstruct_result1024 != nil {
			unwrapped1025 := deconstruct_result1024
			p.pretty_unspecified_type(unwrapped1025)
		} else {
			_dollar_dollar := msg
			var _t1734 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1734 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1022 := _t1734
			if deconstruct_result1022 != nil {
				unwrapped1023 := deconstruct_result1022
				p.pretty_string_type(unwrapped1023)
			} else {
				_dollar_dollar := msg
				var _t1735 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1735 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1020 := _t1735
				if deconstruct_result1020 != nil {
					unwrapped1021 := deconstruct_result1020
					p.pretty_int_type(unwrapped1021)
				} else {
					_dollar_dollar := msg
					var _t1736 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1736 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1018 := _t1736
					if deconstruct_result1018 != nil {
						unwrapped1019 := deconstruct_result1018
						p.pretty_float_type(unwrapped1019)
					} else {
						_dollar_dollar := msg
						var _t1737 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1737 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1016 := _t1737
						if deconstruct_result1016 != nil {
							unwrapped1017 := deconstruct_result1016
							p.pretty_uint128_type(unwrapped1017)
						} else {
							_dollar_dollar := msg
							var _t1738 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1738 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1014 := _t1738
							if deconstruct_result1014 != nil {
								unwrapped1015 := deconstruct_result1014
								p.pretty_int128_type(unwrapped1015)
							} else {
								_dollar_dollar := msg
								var _t1739 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1739 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1012 := _t1739
								if deconstruct_result1012 != nil {
									unwrapped1013 := deconstruct_result1012
									p.pretty_date_type(unwrapped1013)
								} else {
									_dollar_dollar := msg
									var _t1740 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1740 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1010 := _t1740
									if deconstruct_result1010 != nil {
										unwrapped1011 := deconstruct_result1010
										p.pretty_datetime_type(unwrapped1011)
									} else {
										_dollar_dollar := msg
										var _t1741 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1741 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1008 := _t1741
										if deconstruct_result1008 != nil {
											unwrapped1009 := deconstruct_result1008
											p.pretty_missing_type(unwrapped1009)
										} else {
											_dollar_dollar := msg
											var _t1742 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1742 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result1006 := _t1742
											if deconstruct_result1006 != nil {
												unwrapped1007 := deconstruct_result1006
												p.pretty_decimal_type(unwrapped1007)
											} else {
												_dollar_dollar := msg
												var _t1743 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1743 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result1004 := _t1743
												if deconstruct_result1004 != nil {
													unwrapped1005 := deconstruct_result1004
													p.pretty_boolean_type(unwrapped1005)
												} else {
													_dollar_dollar := msg
													var _t1744 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1744 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result1002 := _t1744
													if deconstruct_result1002 != nil {
														unwrapped1003 := deconstruct_result1002
														p.pretty_int32_type(unwrapped1003)
													} else {
														_dollar_dollar := msg
														var _t1745 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1745 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result1000 := _t1745
														if deconstruct_result1000 != nil {
															unwrapped1001 := deconstruct_result1000
															p.pretty_float32_type(unwrapped1001)
														} else {
															_dollar_dollar := msg
															var _t1746 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1746 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result998 := _t1746
															if deconstruct_result998 != nil {
																unwrapped999 := deconstruct_result998
																p.pretty_uint32_type(unwrapped999)
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
	fields1027 := msg
	_ = fields1027
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1028 := msg
	_ = fields1028
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1029 := msg
	_ = fields1029
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1030 := msg
	_ = fields1030
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1031 := msg
	_ = fields1031
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1032 := msg
	_ = fields1032
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1033 := msg
	_ = fields1033
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1034 := msg
	_ = fields1034
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1035 := msg
	_ = fields1035
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1040 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1040 != nil {
		p.write(*flat1040)
		return nil
	} else {
		_dollar_dollar := msg
		fields1036 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1037 := fields1036
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1038 := unwrapped_fields1037[0].(int64)
		p.write(fmt.Sprintf("%d", field1038))
		p.newline()
		field1039 := unwrapped_fields1037[1].(int64)
		p.write(fmt.Sprintf("%d", field1039))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1041 := msg
	_ = fields1041
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1042 := msg
	_ = fields1042
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1043 := msg
	_ = fields1043
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1044 := msg
	_ = fields1044
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1048 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1048 != nil {
		p.write(*flat1048)
		return nil
	} else {
		fields1045 := msg
		p.write("|")
		if !(len(fields1045) == 0) {
			p.write(" ")
			for i1047, elem1046 := range fields1045 {
				if (i1047 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1046)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1075 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1747 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1747 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1073 := _t1747
		if deconstruct_result1073 != nil {
			unwrapped1074 := deconstruct_result1073
			p.pretty_true(unwrapped1074)
		} else {
			_dollar_dollar := msg
			var _t1748 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1748 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1071 := _t1748
			if deconstruct_result1071 != nil {
				unwrapped1072 := deconstruct_result1071
				p.pretty_false(unwrapped1072)
			} else {
				_dollar_dollar := msg
				var _t1749 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1749 = _dollar_dollar.GetExists()
				}
				deconstruct_result1069 := _t1749
				if deconstruct_result1069 != nil {
					unwrapped1070 := deconstruct_result1069
					p.pretty_exists(unwrapped1070)
				} else {
					_dollar_dollar := msg
					var _t1750 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1750 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1067 := _t1750
					if deconstruct_result1067 != nil {
						unwrapped1068 := deconstruct_result1067
						p.pretty_reduce(unwrapped1068)
					} else {
						_dollar_dollar := msg
						var _t1751 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1751 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1065 := _t1751
						if deconstruct_result1065 != nil {
							unwrapped1066 := deconstruct_result1065
							p.pretty_conjunction(unwrapped1066)
						} else {
							_dollar_dollar := msg
							var _t1752 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1752 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1063 := _t1752
							if deconstruct_result1063 != nil {
								unwrapped1064 := deconstruct_result1063
								p.pretty_disjunction(unwrapped1064)
							} else {
								_dollar_dollar := msg
								var _t1753 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1753 = _dollar_dollar.GetNot()
								}
								deconstruct_result1061 := _t1753
								if deconstruct_result1061 != nil {
									unwrapped1062 := deconstruct_result1061
									p.pretty_not(unwrapped1062)
								} else {
									_dollar_dollar := msg
									var _t1754 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1754 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1059 := _t1754
									if deconstruct_result1059 != nil {
										unwrapped1060 := deconstruct_result1059
										p.pretty_ffi(unwrapped1060)
									} else {
										_dollar_dollar := msg
										var _t1755 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1755 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1057 := _t1755
										if deconstruct_result1057 != nil {
											unwrapped1058 := deconstruct_result1057
											p.pretty_atom(unwrapped1058)
										} else {
											_dollar_dollar := msg
											var _t1756 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1756 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1055 := _t1756
											if deconstruct_result1055 != nil {
												unwrapped1056 := deconstruct_result1055
												p.pretty_pragma(unwrapped1056)
											} else {
												_dollar_dollar := msg
												var _t1757 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1757 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1053 := _t1757
												if deconstruct_result1053 != nil {
													unwrapped1054 := deconstruct_result1053
													p.pretty_primitive(unwrapped1054)
												} else {
													_dollar_dollar := msg
													var _t1758 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1758 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1051 := _t1758
													if deconstruct_result1051 != nil {
														unwrapped1052 := deconstruct_result1051
														p.pretty_rel_atom(unwrapped1052)
													} else {
														_dollar_dollar := msg
														var _t1759 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1759 = _dollar_dollar.GetCast()
														}
														deconstruct_result1049 := _t1759
														if deconstruct_result1049 != nil {
															unwrapped1050 := deconstruct_result1049
															p.pretty_cast(unwrapped1050)
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
	fields1076 := msg
	_ = fields1076
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1077 := msg
	_ = fields1077
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1082 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1082 != nil {
		p.write(*flat1082)
		return nil
	} else {
		_dollar_dollar := msg
		_t1760 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1078 := []interface{}{_t1760, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1079 := fields1078
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1080 := unwrapped_fields1079[0].([]interface{})
		p.pretty_bindings(field1080)
		p.newline()
		field1081 := unwrapped_fields1079[1].(*pb.Formula)
		p.pretty_formula(field1081)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		_dollar_dollar := msg
		fields1083 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1084 := fields1083
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1085 := unwrapped_fields1084[0].(*pb.Abstraction)
		p.pretty_abstraction(field1085)
		p.newline()
		field1086 := unwrapped_fields1084[1].(*pb.Abstraction)
		p.pretty_abstraction(field1086)
		p.newline()
		field1087 := unwrapped_fields1084[2].([]*pb.Term)
		p.pretty_terms(field1087)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		fields1089 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1089) == 0) {
			p.newline()
			for i1091, elem1090 := range fields1089 {
				if (i1091 > 0) {
					p.newline()
				}
				p.pretty_term(elem1090)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1097 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1097 != nil {
		p.write(*flat1097)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1761 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1761 = _dollar_dollar.GetVar()
		}
		deconstruct_result1095 := _t1761
		if deconstruct_result1095 != nil {
			unwrapped1096 := deconstruct_result1095
			p.pretty_var(unwrapped1096)
		} else {
			_dollar_dollar := msg
			var _t1762 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1762 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1093 := _t1762
			if deconstruct_result1093 != nil {
				unwrapped1094 := deconstruct_result1093
				p.pretty_value(unwrapped1094)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		_dollar_dollar := msg
		fields1098 := _dollar_dollar.GetName()
		unwrapped_fields1099 := fields1098
		p.write(unwrapped_fields1099)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1126 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1126 != nil {
		p.write(*flat1126)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1763 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1763 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1124 := _t1763
		if deconstruct_result1124 != nil {
			unwrapped1125 := deconstruct_result1124
			p.pretty_date(unwrapped1125)
		} else {
			_dollar_dollar := msg
			var _t1764 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1764 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1122 := _t1764
			if deconstruct_result1122 != nil {
				unwrapped1123 := deconstruct_result1122
				p.pretty_datetime(unwrapped1123)
			} else {
				_dollar_dollar := msg
				var _t1765 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1765 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1120 := _t1765
				if deconstruct_result1120 != nil {
					unwrapped1121 := *deconstruct_result1120
					p.write(p.formatStringValue(unwrapped1121))
				} else {
					_dollar_dollar := msg
					var _t1766 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1766 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1118 := _t1766
					if deconstruct_result1118 != nil {
						unwrapped1119 := *deconstruct_result1118
						p.write(fmt.Sprintf("%di32", unwrapped1119))
					} else {
						_dollar_dollar := msg
						var _t1767 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1767 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1116 := _t1767
						if deconstruct_result1116 != nil {
							unwrapped1117 := *deconstruct_result1116
							p.write(fmt.Sprintf("%d", unwrapped1117))
						} else {
							_dollar_dollar := msg
							var _t1768 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1768 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1114 := _t1768
							if deconstruct_result1114 != nil {
								unwrapped1115 := *deconstruct_result1114
								p.write(formatFloat32(unwrapped1115))
							} else {
								_dollar_dollar := msg
								var _t1769 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1769 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1112 := _t1769
								if deconstruct_result1112 != nil {
									unwrapped1113 := *deconstruct_result1112
									p.write(formatFloat64(unwrapped1113))
								} else {
									_dollar_dollar := msg
									var _t1770 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1770 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1110 := _t1770
									if deconstruct_result1110 != nil {
										unwrapped1111 := *deconstruct_result1110
										p.write(fmt.Sprintf("%du32", unwrapped1111))
									} else {
										_dollar_dollar := msg
										var _t1771 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1771 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1108 := _t1771
										if deconstruct_result1108 != nil {
											unwrapped1109 := deconstruct_result1108
											p.write(p.formatUint128(unwrapped1109))
										} else {
											_dollar_dollar := msg
											var _t1772 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1772 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1106 := _t1772
											if deconstruct_result1106 != nil {
												unwrapped1107 := deconstruct_result1106
												p.write(p.formatInt128(unwrapped1107))
											} else {
												_dollar_dollar := msg
												var _t1773 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1773 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1104 := _t1773
												if deconstruct_result1104 != nil {
													unwrapped1105 := deconstruct_result1104
													p.write(p.formatDecimal(unwrapped1105))
												} else {
													_dollar_dollar := msg
													var _t1774 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1774 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1102 := _t1774
													if deconstruct_result1102 != nil {
														unwrapped1103 := *deconstruct_result1102
														p.pretty_boolean_value(unwrapped1103)
													} else {
														fields1101 := msg
														_ = fields1101
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
	flat1132 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_dollar_dollar := msg
		fields1127 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1128 := fields1127
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1129 := unwrapped_fields1128[0].(int64)
		p.write(fmt.Sprintf("%d", field1129))
		p.newline()
		field1130 := unwrapped_fields1128[1].(int64)
		p.write(fmt.Sprintf("%d", field1130))
		p.newline()
		field1131 := unwrapped_fields1128[2].(int64)
		p.write(fmt.Sprintf("%d", field1131))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		fields1133 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1134 := fields1133
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1135 := unwrapped_fields1134[0].(int64)
		p.write(fmt.Sprintf("%d", field1135))
		p.newline()
		field1136 := unwrapped_fields1134[1].(int64)
		p.write(fmt.Sprintf("%d", field1136))
		p.newline()
		field1137 := unwrapped_fields1134[2].(int64)
		p.write(fmt.Sprintf("%d", field1137))
		p.newline()
		field1138 := unwrapped_fields1134[3].(int64)
		p.write(fmt.Sprintf("%d", field1138))
		p.newline()
		field1139 := unwrapped_fields1134[4].(int64)
		p.write(fmt.Sprintf("%d", field1139))
		p.newline()
		field1140 := unwrapped_fields1134[5].(int64)
		p.write(fmt.Sprintf("%d", field1140))
		field1141 := unwrapped_fields1134[6].(*int64)
		if field1141 != nil {
			p.newline()
			opt_val1142 := *field1141
			p.write(fmt.Sprintf("%d", opt_val1142))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1148 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1148 != nil {
		p.write(*flat1148)
		return nil
	} else {
		_dollar_dollar := msg
		fields1144 := _dollar_dollar.GetArgs()
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1145) == 0) {
			p.newline()
			for i1147, elem1146 := range unwrapped_fields1145 {
				if (i1147 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1146)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		fields1149 := _dollar_dollar.GetArgs()
		unwrapped_fields1150 := fields1149
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1150) == 0) {
			p.newline()
			for i1152, elem1151 := range unwrapped_fields1150 {
				if (i1152 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1151)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1156 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1156 != nil {
		p.write(*flat1156)
		return nil
	} else {
		_dollar_dollar := msg
		fields1154 := _dollar_dollar.GetArg()
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1155)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		fields1157 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1158 := fields1157
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1159 := unwrapped_fields1158[0].(string)
		p.pretty_name(field1159)
		p.newline()
		field1160 := unwrapped_fields1158[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1160)
		p.newline()
		field1161 := unwrapped_fields1158[2].([]*pb.Term)
		p.pretty_terms(field1161)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1164 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		fields1163 := msg
		p.write(":")
		p.write(fields1163)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		fields1165 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1165) == 0) {
			p.newline()
			for i1167, elem1166 := range fields1165 {
				if (i1167 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1166)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		_dollar_dollar := msg
		fields1169 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1170 := fields1169
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1171 := unwrapped_fields1170[0].(*pb.RelationId)
		p.pretty_relation_id(field1171)
		field1172 := unwrapped_fields1170[1].([]*pb.Term)
		if !(len(field1172) == 0) {
			p.newline()
			for i1174, elem1173 := range field1172 {
				if (i1174 > 0) {
					p.newline()
				}
				p.pretty_term(elem1173)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		_dollar_dollar := msg
		fields1176 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1177 := fields1176
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1178 := unwrapped_fields1177[0].(string)
		p.pretty_name(field1178)
		field1179 := unwrapped_fields1177[1].([]*pb.Term)
		if !(len(field1179) == 0) {
			p.newline()
			for i1181, elem1180 := range field1179 {
				if (i1181 > 0) {
					p.newline()
				}
				p.pretty_term(elem1180)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1775 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1775 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1197 := _t1775
		if guard_result1197 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1776 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1776 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1196 := _t1776
			if guard_result1196 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1777 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1777 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1195 := _t1777
				if guard_result1195 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1778 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1778 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1194 := _t1778
					if guard_result1194 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1779 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1779 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1193 := _t1779
						if guard_result1193 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1780 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1780 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1192 := _t1780
							if guard_result1192 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1781 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1781 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1191 := _t1781
								if guard_result1191 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1782 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1782 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1190 := _t1782
									if guard_result1190 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1783 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1783 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1189 := _t1783
										if guard_result1189 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1183 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1184 := fields1183
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1185 := unwrapped_fields1184[0].(string)
											p.pretty_name(field1185)
											field1186 := unwrapped_fields1184[1].([]*pb.RelTerm)
											if !(len(field1186) == 0) {
												p.newline()
												for i1188, elem1187 := range field1186 {
													if (i1188 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1187)
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
	flat1203 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1203 != nil {
		p.write(*flat1203)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1784 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1784 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1199 := _t1784
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1201 := unwrapped_fields1200[0].(*pb.Term)
		p.pretty_term(field1201)
		p.newline()
		field1202 := unwrapped_fields1200[1].(*pb.Term)
		p.pretty_term(field1202)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1785 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1785 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1204 := _t1785
		unwrapped_fields1205 := fields1204
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1206 := unwrapped_fields1205[0].(*pb.Term)
		p.pretty_term(field1206)
		p.newline()
		field1207 := unwrapped_fields1205[1].(*pb.Term)
		p.pretty_term(field1207)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1213 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1213 != nil {
		p.write(*flat1213)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1786 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1786 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1209 := _t1786
		unwrapped_fields1210 := fields1209
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1211 := unwrapped_fields1210[0].(*pb.Term)
		p.pretty_term(field1211)
		p.newline()
		field1212 := unwrapped_fields1210[1].(*pb.Term)
		p.pretty_term(field1212)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1218 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1218 != nil {
		p.write(*flat1218)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1787 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1787 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1214 := _t1787
		unwrapped_fields1215 := fields1214
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1216 := unwrapped_fields1215[0].(*pb.Term)
		p.pretty_term(field1216)
		p.newline()
		field1217 := unwrapped_fields1215[1].(*pb.Term)
		p.pretty_term(field1217)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1223 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1788 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1788 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1219 := _t1788
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1229 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1229 != nil {
		p.write(*flat1229)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1789 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1789 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1224 := _t1789
		unwrapped_fields1225 := fields1224
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1226 := unwrapped_fields1225[0].(*pb.Term)
		p.pretty_term(field1226)
		p.newline()
		field1227 := unwrapped_fields1225[1].(*pb.Term)
		p.pretty_term(field1227)
		p.newline()
		field1228 := unwrapped_fields1225[2].(*pb.Term)
		p.pretty_term(field1228)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1790 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1790 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1230 := _t1790
		unwrapped_fields1231 := fields1230
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1232 := unwrapped_fields1231[0].(*pb.Term)
		p.pretty_term(field1232)
		p.newline()
		field1233 := unwrapped_fields1231[1].(*pb.Term)
		p.pretty_term(field1233)
		p.newline()
		field1234 := unwrapped_fields1231[2].(*pb.Term)
		p.pretty_term(field1234)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1241 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1241 != nil {
		p.write(*flat1241)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1791 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1791 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1236 := _t1791
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1238 := unwrapped_fields1237[0].(*pb.Term)
		p.pretty_term(field1238)
		p.newline()
		field1239 := unwrapped_fields1237[1].(*pb.Term)
		p.pretty_term(field1239)
		p.newline()
		field1240 := unwrapped_fields1237[2].(*pb.Term)
		p.pretty_term(field1240)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1247 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1792 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1792 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1242 := _t1792
		unwrapped_fields1243 := fields1242
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1244 := unwrapped_fields1243[0].(*pb.Term)
		p.pretty_term(field1244)
		p.newline()
		field1245 := unwrapped_fields1243[1].(*pb.Term)
		p.pretty_term(field1245)
		p.newline()
		field1246 := unwrapped_fields1243[2].(*pb.Term)
		p.pretty_term(field1246)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1793 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1793 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1250 := _t1793
		if deconstruct_result1250 != nil {
			unwrapped1251 := deconstruct_result1250
			p.pretty_specialized_value(unwrapped1251)
		} else {
			_dollar_dollar := msg
			var _t1794 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1794 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1248 := _t1794
			if deconstruct_result1248 != nil {
				unwrapped1249 := deconstruct_result1248
				p.pretty_term(unwrapped1249)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1254 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1254 != nil {
		p.write(*flat1254)
		return nil
	} else {
		fields1253 := msg
		p.write("#")
		p.pretty_raw_value(fields1253)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		_dollar_dollar := msg
		fields1255 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1256 := fields1255
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1257 := unwrapped_fields1256[0].(string)
		p.pretty_name(field1257)
		field1258 := unwrapped_fields1256[1].([]*pb.RelTerm)
		if !(len(field1258) == 0) {
			p.newline()
			for i1260, elem1259 := range field1258 {
				if (i1260 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1259)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		_dollar_dollar := msg
		fields1262 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1263 := fields1262
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1264 := unwrapped_fields1263[0].(*pb.Term)
		p.pretty_term(field1264)
		p.newline()
		field1265 := unwrapped_fields1263[1].(*pb.Term)
		p.pretty_term(field1265)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1270 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1270 != nil {
		p.write(*flat1270)
		return nil
	} else {
		fields1267 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1267) == 0) {
			p.newline()
			for i1269, elem1268 := range fields1267 {
				if (i1269 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1268)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1277 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		_dollar_dollar := msg
		fields1271 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1272 := fields1271
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1273 := unwrapped_fields1272[0].(string)
		p.pretty_name(field1273)
		field1274 := unwrapped_fields1272[1].([]*pb.Value)
		if !(len(field1274) == 0) {
			p.newline()
			for i1276, elem1275 := range field1274 {
				if (i1276 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1275)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1795 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1795 = _dollar_dollar.GetAttrs()
		}
		fields1278 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1795}
		unwrapped_fields1279 := fields1278
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1280 := unwrapped_fields1279[0].([]*pb.RelationId)
		if !(len(field1280) == 0) {
			p.newline()
			for i1282, elem1281 := range field1280 {
				if (i1282 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1281)
			}
		}
		p.newline()
		field1283 := unwrapped_fields1279[1].(*pb.Script)
		p.pretty_script(field1283)
		field1284 := unwrapped_fields1279[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		_dollar_dollar := msg
		fields1287 := _dollar_dollar.GetConstructs()
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1288) == 0) {
			p.newline()
			for i1290, elem1289 := range unwrapped_fields1288 {
				if (i1290 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1289)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1796 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1796 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1294 := _t1796
		if deconstruct_result1294 != nil {
			unwrapped1295 := deconstruct_result1294
			p.pretty_loop(unwrapped1295)
		} else {
			_dollar_dollar := msg
			var _t1797 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1797 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1292 := _t1797
			if deconstruct_result1292 != nil {
				unwrapped1293 := deconstruct_result1292
				p.pretty_instruction(unwrapped1293)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1798 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1798 = _dollar_dollar.GetAttrs()
		}
		fields1297 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1798}
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1299 := unwrapped_fields1298[0].([]*pb.Instruction)
		p.pretty_init(field1299)
		p.newline()
		field1300 := unwrapped_fields1298[1].(*pb.Script)
		p.pretty_script(field1300)
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

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		fields1304 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1304) == 0) {
			p.newline()
			for i1306, elem1305 := range fields1304 {
				if (i1306 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1305)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1318 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1318 != nil {
		p.write(*flat1318)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1799 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1799 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1316 := _t1799
		if deconstruct_result1316 != nil {
			unwrapped1317 := deconstruct_result1316
			p.pretty_assign(unwrapped1317)
		} else {
			_dollar_dollar := msg
			var _t1800 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1800 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1314 := _t1800
			if deconstruct_result1314 != nil {
				unwrapped1315 := deconstruct_result1314
				p.pretty_upsert(unwrapped1315)
			} else {
				_dollar_dollar := msg
				var _t1801 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1801 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1312 := _t1801
				if deconstruct_result1312 != nil {
					unwrapped1313 := deconstruct_result1312
					p.pretty_break(unwrapped1313)
				} else {
					_dollar_dollar := msg
					var _t1802 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1802 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1310 := _t1802
					if deconstruct_result1310 != nil {
						unwrapped1311 := deconstruct_result1310
						p.pretty_monoid_def(unwrapped1311)
					} else {
						_dollar_dollar := msg
						var _t1803 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1803 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1308 := _t1803
						if deconstruct_result1308 != nil {
							unwrapped1309 := deconstruct_result1308
							p.pretty_monus_def(unwrapped1309)
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
	flat1325 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1325 != nil {
		p.write(*flat1325)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1804 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1804 = _dollar_dollar.GetAttrs()
		}
		fields1319 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1804}
		unwrapped_fields1320 := fields1319
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1321 := unwrapped_fields1320[0].(*pb.RelationId)
		p.pretty_relation_id(field1321)
		p.newline()
		field1322 := unwrapped_fields1320[1].(*pb.Abstraction)
		p.pretty_abstraction(field1322)
		field1323 := unwrapped_fields1320[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1332 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1332 != nil {
		p.write(*flat1332)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1805 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1805 = _dollar_dollar.GetAttrs()
		}
		fields1326 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1805}
		unwrapped_fields1327 := fields1326
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1328 := unwrapped_fields1327[0].(*pb.RelationId)
		p.pretty_relation_id(field1328)
		p.newline()
		field1329 := unwrapped_fields1327[1].([]interface{})
		p.pretty_abstraction_with_arity(field1329)
		field1330 := unwrapped_fields1327[2].([]*pb.Attribute)
		if field1330 != nil {
			p.newline()
			opt_val1331 := field1330
			p.pretty_attrs(opt_val1331)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1337 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1337 != nil {
		p.write(*flat1337)
		return nil
	} else {
		_dollar_dollar := msg
		_t1806 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1333 := []interface{}{_t1806, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1334 := fields1333
		p.write("(")
		p.indent()
		field1335 := unwrapped_fields1334[0].([]interface{})
		p.pretty_bindings(field1335)
		p.newline()
		field1336 := unwrapped_fields1334[1].(*pb.Formula)
		p.pretty_formula(field1336)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1344 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1344 != nil {
		p.write(*flat1344)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1807 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1807 = _dollar_dollar.GetAttrs()
		}
		fields1338 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1807}
		unwrapped_fields1339 := fields1338
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1340 := unwrapped_fields1339[0].(*pb.RelationId)
		p.pretty_relation_id(field1340)
		p.newline()
		field1341 := unwrapped_fields1339[1].(*pb.Abstraction)
		p.pretty_abstraction(field1341)
		field1342 := unwrapped_fields1339[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1352 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1352 != nil {
		p.write(*flat1352)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1808 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1808 = _dollar_dollar.GetAttrs()
		}
		fields1345 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1808}
		unwrapped_fields1346 := fields1345
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1347 := unwrapped_fields1346[0].(*pb.Monoid)
		p.pretty_monoid(field1347)
		p.newline()
		field1348 := unwrapped_fields1346[1].(*pb.RelationId)
		p.pretty_relation_id(field1348)
		p.newline()
		field1349 := unwrapped_fields1346[2].([]interface{})
		p.pretty_abstraction_with_arity(field1349)
		field1350 := unwrapped_fields1346[3].([]*pb.Attribute)
		if field1350 != nil {
			p.newline()
			opt_val1351 := field1350
			p.pretty_attrs(opt_val1351)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1361 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1361 != nil {
		p.write(*flat1361)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1809 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1809 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1359 := _t1809
		if deconstruct_result1359 != nil {
			unwrapped1360 := deconstruct_result1359
			p.pretty_or_monoid(unwrapped1360)
		} else {
			_dollar_dollar := msg
			var _t1810 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1810 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1357 := _t1810
			if deconstruct_result1357 != nil {
				unwrapped1358 := deconstruct_result1357
				p.pretty_min_monoid(unwrapped1358)
			} else {
				_dollar_dollar := msg
				var _t1811 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1811 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1355 := _t1811
				if deconstruct_result1355 != nil {
					unwrapped1356 := deconstruct_result1355
					p.pretty_max_monoid(unwrapped1356)
				} else {
					_dollar_dollar := msg
					var _t1812 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1812 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1353 := _t1812
					if deconstruct_result1353 != nil {
						unwrapped1354 := deconstruct_result1353
						p.pretty_sum_monoid(unwrapped1354)
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
	fields1362 := msg
	_ = fields1362
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1365 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1365 != nil {
		p.write(*flat1365)
		return nil
	} else {
		_dollar_dollar := msg
		fields1363 := _dollar_dollar.GetType()
		unwrapped_fields1364 := fields1363
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1364)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1368 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		fields1366 := _dollar_dollar.GetType()
		unwrapped_fields1367 := fields1366
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1367)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		fields1369 := _dollar_dollar.GetType()
		unwrapped_fields1370 := fields1369
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1370)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1379 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1379 != nil {
		p.write(*flat1379)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1813 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1813 = _dollar_dollar.GetAttrs()
		}
		fields1372 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1813}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1374 := unwrapped_fields1373[0].(*pb.Monoid)
		p.pretty_monoid(field1374)
		p.newline()
		field1375 := unwrapped_fields1373[1].(*pb.RelationId)
		p.pretty_relation_id(field1375)
		p.newline()
		field1376 := unwrapped_fields1373[2].([]interface{})
		p.pretty_abstraction_with_arity(field1376)
		field1377 := unwrapped_fields1373[3].([]*pb.Attribute)
		if field1377 != nil {
			p.newline()
			opt_val1378 := field1377
			p.pretty_attrs(opt_val1378)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1386 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1386 != nil {
		p.write(*flat1386)
		return nil
	} else {
		_dollar_dollar := msg
		fields1380 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1381 := fields1380
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1382 := unwrapped_fields1381[0].(*pb.RelationId)
		p.pretty_relation_id(field1382)
		p.newline()
		field1383 := unwrapped_fields1381[1].(*pb.Abstraction)
		p.pretty_abstraction(field1383)
		p.newline()
		field1384 := unwrapped_fields1381[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1384)
		p.newline()
		field1385 := unwrapped_fields1381[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1385)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1390 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1390 != nil {
		p.write(*flat1390)
		return nil
	} else {
		fields1387 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1387) == 0) {
			p.newline()
			for i1389, elem1388 := range fields1387 {
				if (i1389 > 0) {
					p.newline()
				}
				p.pretty_var(elem1388)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1394 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1394 != nil {
		p.write(*flat1394)
		return nil
	} else {
		fields1391 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1391) == 0) {
			p.newline()
			for i1393, elem1392 := range fields1391 {
				if (i1393 > 0) {
					p.newline()
				}
				p.pretty_var(elem1392)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1403 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1814 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1814 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1401 := _t1814
		if deconstruct_result1401 != nil {
			unwrapped1402 := deconstruct_result1401
			p.pretty_edb(unwrapped1402)
		} else {
			_dollar_dollar := msg
			var _t1815 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1815 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1399 := _t1815
			if deconstruct_result1399 != nil {
				unwrapped1400 := deconstruct_result1399
				p.pretty_betree_relation(unwrapped1400)
			} else {
				_dollar_dollar := msg
				var _t1816 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1816 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1397 := _t1816
				if deconstruct_result1397 != nil {
					unwrapped1398 := deconstruct_result1397
					p.pretty_csv_data(unwrapped1398)
				} else {
					_dollar_dollar := msg
					var _t1817 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1817 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1395 := _t1817
					if deconstruct_result1395 != nil {
						unwrapped1396 := deconstruct_result1395
						p.pretty_iceberg_data(unwrapped1396)
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
	flat1409 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1409 != nil {
		p.write(*flat1409)
		return nil
	} else {
		_dollar_dollar := msg
		fields1404 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1405 := fields1404
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1406 := unwrapped_fields1405[0].(*pb.RelationId)
		p.pretty_relation_id(field1406)
		p.newline()
		field1407 := unwrapped_fields1405[1].([]string)
		p.pretty_edb_path(field1407)
		p.newline()
		field1408 := unwrapped_fields1405[2].([]*pb.Type)
		p.pretty_edb_types(field1408)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		fields1410 := msg
		p.write("[")
		p.indent()
		for i1412, elem1411 := range fields1410 {
			if (i1412 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1411))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		fields1414 := msg
		p.write("[")
		p.indent()
		for i1416, elem1415 := range fields1414 {
			if (i1416 > 0) {
				p.newline()
			}
			p.pretty_type(elem1415)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1422 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1422 != nil {
		p.write(*flat1422)
		return nil
	} else {
		_dollar_dollar := msg
		fields1418 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1420 := unwrapped_fields1419[0].(*pb.RelationId)
		p.pretty_relation_id(field1420)
		p.newline()
		field1421 := unwrapped_fields1419[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1421)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1428 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1428 != nil {
		p.write(*flat1428)
		return nil
	} else {
		_dollar_dollar := msg
		_t1818 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1423 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1818}
		unwrapped_fields1424 := fields1423
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1425 := unwrapped_fields1424[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1425)
		p.newline()
		field1426 := unwrapped_fields1424[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1426)
		p.newline()
		field1427 := unwrapped_fields1424[2].([][]interface{})
		p.pretty_config_dict(field1427)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		fields1429 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1429) == 0) {
			p.newline()
			for i1431, elem1430 := range fields1429 {
				if (i1431 > 0) {
					p.newline()
				}
				p.pretty_type(elem1430)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1436 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1436 != nil {
		p.write(*flat1436)
		return nil
	} else {
		fields1433 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1433) == 0) {
			p.newline()
			for i1435, elem1434 := range fields1433 {
				if (i1435 > 0) {
					p.newline()
				}
				p.pretty_type(elem1434)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1446 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1446 != nil {
		p.write(*flat1446)
		return nil
	} else {
		_dollar_dollar := msg
		_t1819 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1820 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1437 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1819, _t1820, _dollar_dollar.GetAsof()}
		unwrapped_fields1438 := fields1437
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1439 := unwrapped_fields1438[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1439)
		p.newline()
		field1440 := unwrapped_fields1438[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1440)
		field1441 := unwrapped_fields1438[2].([]*pb.GNFColumn)
		if field1441 != nil {
			p.newline()
			opt_val1442 := field1441
			p.pretty_gnf_columns(opt_val1442)
		}
		field1443 := unwrapped_fields1438[3].(*pb.TargetRelations)
		if field1443 != nil {
			p.newline()
			opt_val1444 := field1443
			p.pretty_target_relations(opt_val1444)
		}
		p.newline()
		field1445 := unwrapped_fields1438[4].(string)
		p.pretty_csv_asof(field1445)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1453 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1453 != nil {
		p.write(*flat1453)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1821 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1821 = _dollar_dollar.GetPaths()
		}
		var _t1822 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1822 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1447 := []interface{}{_t1821, _t1822}
		unwrapped_fields1448 := fields1447
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1449 := unwrapped_fields1448[0].([]string)
		if field1449 != nil {
			p.newline()
			opt_val1450 := field1449
			p.pretty_csv_locator_paths(opt_val1450)
		}
		field1451 := unwrapped_fields1448[1].(*string)
		if field1451 != nil {
			p.newline()
			opt_val1452 := *field1451
			p.pretty_csv_locator_inline_data(opt_val1452)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		fields1454 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1454) == 0) {
			p.newline()
			for i1456, elem1455 := range fields1454 {
				if (i1456 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1455))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1459 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1459 != nil {
		p.write(*flat1459)
		return nil
	} else {
		fields1458 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1458))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1465 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1465 != nil {
		p.write(*flat1465)
		return nil
	} else {
		_dollar_dollar := msg
		_t1823 := p.deconstruct_csv_config(_dollar_dollar)
		_t1824 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1460 := []interface{}{_t1823, _t1824}
		unwrapped_fields1461 := fields1460
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1462 := unwrapped_fields1461[0].([][]interface{})
		p.pretty_config_dict(field1462)
		field1463 := unwrapped_fields1461[1].([][]interface{})
		if field1463 != nil {
			p.newline()
			opt_val1464 := field1463
			p.pretty__storage_integration(opt_val1464)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1467 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1467 != nil {
		p.write(*flat1467)
		return nil
	} else {
		fields1466 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1466)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1471 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		fields1468 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1468) == 0) {
			p.newline()
			for i1470, elem1469 := range fields1468 {
				if (i1470 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1469)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1825 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1825 = _dollar_dollar.GetTargetId()
		}
		fields1472 := []interface{}{_dollar_dollar.GetColumnPath(), _t1825, _dollar_dollar.GetTypes()}
		unwrapped_fields1473 := fields1472
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1474 := unwrapped_fields1473[0].([]string)
		p.pretty_gnf_column_path(field1474)
		field1475 := unwrapped_fields1473[1].(*pb.RelationId)
		if field1475 != nil {
			p.newline()
			opt_val1476 := field1475
			p.pretty_relation_id(opt_val1476)
		}
		p.newline()
		p.write("[")
		field1477 := unwrapped_fields1473[2].([]*pb.Type)
		for i1479, elem1478 := range field1477 {
			if (i1479 > 0) {
				p.newline()
			}
			p.pretty_type(elem1478)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1487 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1487 != nil {
		p.write(*flat1487)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1826 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1826 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1485 := _t1826
		if deconstruct_result1485 != nil {
			unwrapped1486 := *deconstruct_result1485
			p.write(p.formatStringValue(unwrapped1486))
		} else {
			_dollar_dollar := msg
			var _t1827 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1827 = _dollar_dollar
			}
			deconstruct_result1481 := _t1827
			if deconstruct_result1481 != nil {
				unwrapped1482 := deconstruct_result1481
				p.write("[")
				p.indent()
				for i1484, elem1483 := range unwrapped1482 {
					if (i1484 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1483))
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

func (p *PrettyPrinter) pretty_target_relations(msg *pb.TargetRelations) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_target_relations(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		_dollar_dollar := msg
		_t1828 := p.deconstruct_relation_keys(_dollar_dollar)
		fields1488 := []interface{}{_t1828, _dollar_dollar}
		unwrapped_fields1489 := fields1488
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1490 := unwrapped_fields1489[0].([]interface{})
		p.pretty_relation_keys(field1490)
		p.newline()
		field1491 := unwrapped_fields1489[1].(*pb.TargetRelations)
		p.pretty_relation_body(field1491)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []interface{}) interface{} {
	flat1499 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1499 != nil {
		p.write(*flat1499)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1829 []*pb.NamedColumn
		if !(_dollar_dollar[1].(bool)) {
			_t1829 = _dollar_dollar[0].([]*pb.NamedColumn)
		}
		deconstruct_result1495 := _t1829
		if deconstruct_result1495 != nil {
			unwrapped1496 := deconstruct_result1495
			p.write("(")
			p.write("keys")
			p.indentSexp()
			if !(len(unwrapped1496) == 0) {
				p.newline()
				for i1498, elem1497 := range unwrapped1496 {
					if (i1498 > 0) {
						p.newline()
					}
					p.pretty_named_column(elem1497)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1830 *string
			if _dollar_dollar[1].(bool) {
				_t1830 = ptr("synthetic_key")
			}
			deconstruct_result1493 := _t1830
			if deconstruct_result1493 != nil {
				unwrapped1494 := *deconstruct_result1493
				p.write("(")
				p.write("keys")
				p.indentSexp()
				p.newline()
				p.write(":")
				p.write(unwrapped1494)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for relation_keys"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_named_column(msg *pb.NamedColumn) interface{} {
	flat1504 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		_dollar_dollar := msg
		fields1500 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1501 := fields1500
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1502 := unwrapped_fields1501[0].(string)
		p.write(p.formatStringValue(field1502))
		p.newline()
		field1503 := unwrapped_fields1501[1].(*pb.Type)
		p.pretty_type(field1503)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.TargetRelations) interface{} {
	flat1511 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1511 != nil {
		p.write(*flat1511)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1831 []*pb.TargetRelation
		if hasProtoField(_dollar_dollar, "plain") {
			_t1831 = _dollar_dollar.GetPlain().GetTargets()
		}
		deconstruct_result1509 := _t1831
		if deconstruct_result1509 != nil {
			unwrapped1510 := deconstruct_result1509
			p.pretty_non_cdc_relations(unwrapped1510)
		} else {
			_dollar_dollar := msg
			var _t1832 []interface{}
			if hasProtoField(_dollar_dollar, "cdc") {
				_t1832 = []interface{}{_dollar_dollar.GetCdc().GetInserts(), _dollar_dollar.GetCdc().GetDeletes()}
			}
			deconstruct_result1505 := _t1832
			if deconstruct_result1505 != nil {
				unwrapped1506 := deconstruct_result1505
				field1507 := unwrapped1506[0].([]*pb.TargetRelation)
				p.pretty_cdc_inserts(field1507)
				p.write(" ")
				field1508 := unwrapped1506[1].([]*pb.TargetRelation)
				p.pretty_cdc_deletes(field1508)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.TargetRelation) interface{} {
	flat1515 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1515 != nil {
		p.write(*flat1515)
		return nil
	} else {
		fields1512 := msg
		for i1514, elem1513 := range fields1512 {
			if (i1514 > 0) {
				p.newline()
			}
			p.pretty_target_relation(elem1513)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relation(msg *pb.TargetRelation) interface{} {
	flat1522 := p.tryFlat(msg, func() { p.pretty_target_relation(msg) })
	if flat1522 != nil {
		p.write(*flat1522)
		return nil
	} else {
		_dollar_dollar := msg
		fields1516 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1517 := fields1516
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1518 := unwrapped_fields1517[0].(*pb.RelationId)
		p.pretty_relation_id(field1518)
		field1519 := unwrapped_fields1517[1].([]*pb.NamedColumn)
		if !(len(field1519) == 0) {
			p.newline()
			for i1521, elem1520 := range field1519 {
				if (i1521 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1520)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.TargetRelation) interface{} {
	flat1526 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1526 != nil {
		p.write(*flat1526)
		return nil
	} else {
		fields1523 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1523) == 0) {
			p.newline()
			for i1525, elem1524 := range fields1523 {
				if (i1525 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1524)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.TargetRelation) interface{} {
	flat1530 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1530 != nil {
		p.write(*flat1530)
		return nil
	} else {
		fields1527 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1527) == 0) {
			p.newline()
			for i1529, elem1528 := range fields1527 {
				if (i1529 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1528)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1532 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1532 != nil {
		p.write(*flat1532)
		return nil
	} else {
		fields1531 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1531))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1543 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1543 != nil {
		p.write(*flat1543)
		return nil
	} else {
		_dollar_dollar := msg
		_t1833 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1834 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1533 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1833, _t1834, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1534 := fields1533
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1535 := unwrapped_fields1534[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1535)
		p.newline()
		field1536 := unwrapped_fields1534[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1536)
		p.newline()
		field1537 := unwrapped_fields1534[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1537)
		field1538 := unwrapped_fields1534[3].(*string)
		if field1538 != nil {
			p.newline()
			opt_val1539 := *field1538
			p.pretty_iceberg_from_snapshot(opt_val1539)
		}
		field1540 := unwrapped_fields1534[4].(*string)
		if field1540 != nil {
			p.newline()
			opt_val1541 := *field1540
			p.pretty_iceberg_to_snapshot(opt_val1541)
		}
		p.newline()
		field1542 := unwrapped_fields1534[5].(bool)
		p.pretty_boolean_value(field1542)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1549 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1549 != nil {
		p.write(*flat1549)
		return nil
	} else {
		_dollar_dollar := msg
		fields1544 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1545 := fields1544
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1546 := unwrapped_fields1545[0].(string)
		p.pretty_iceberg_locator_table_name(field1546)
		p.newline()
		field1547 := unwrapped_fields1545[1].([]string)
		p.pretty_iceberg_locator_namespace(field1547)
		p.newline()
		field1548 := unwrapped_fields1545[2].(string)
		p.pretty_iceberg_locator_warehouse(field1548)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1551 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1551 != nil {
		p.write(*flat1551)
		return nil
	} else {
		fields1550 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1550))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1555 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1555 != nil {
		p.write(*flat1555)
		return nil
	} else {
		fields1552 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1552) == 0) {
			p.newline()
			for i1554, elem1553 := range fields1552 {
				if (i1554 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1553))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1557 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1557 != nil {
		p.write(*flat1557)
		return nil
	} else {
		fields1556 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1556))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1565 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1565 != nil {
		p.write(*flat1565)
		return nil
	} else {
		_dollar_dollar := msg
		_t1835 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1558 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1835, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1559 := fields1558
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1560 := unwrapped_fields1559[0].(string)
		p.pretty_iceberg_catalog_uri(field1560)
		field1561 := unwrapped_fields1559[1].(*string)
		if field1561 != nil {
			p.newline()
			opt_val1562 := *field1561
			p.pretty_iceberg_catalog_config_scope(opt_val1562)
		}
		p.newline()
		field1563 := unwrapped_fields1559[2].([][]interface{})
		p.pretty_iceberg_properties(field1563)
		p.newline()
		field1564 := unwrapped_fields1559[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1564)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		fields1566 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1566))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1569 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1569 != nil {
		p.write(*flat1569)
		return nil
	} else {
		fields1568 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1568))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1573 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1573 != nil {
		p.write(*flat1573)
		return nil
	} else {
		fields1570 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1570) == 0) {
			p.newline()
			for i1572, elem1571 := range fields1570 {
				if (i1572 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1571)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1578 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1578 != nil {
		p.write(*flat1578)
		return nil
	} else {
		_dollar_dollar := msg
		fields1574 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1575 := fields1574
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1576 := unwrapped_fields1575[0].(string)
		p.write(p.formatStringValue(field1576))
		p.newline()
		field1577 := unwrapped_fields1575[1].(string)
		p.write(p.formatStringValue(field1577))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1582 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1582 != nil {
		p.write(*flat1582)
		return nil
	} else {
		fields1579 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1579) == 0) {
			p.newline()
			for i1581, elem1580 := range fields1579 {
				if (i1581 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1580)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1587 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1587 != nil {
		p.write(*flat1587)
		return nil
	} else {
		_dollar_dollar := msg
		_t1836 := p.mask_secret_value(_dollar_dollar)
		fields1583 := []interface{}{_dollar_dollar[0].(string), _t1836}
		unwrapped_fields1584 := fields1583
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1585 := unwrapped_fields1584[0].(string)
		p.write(p.formatStringValue(field1585))
		p.newline()
		field1586 := unwrapped_fields1584[1].(string)
		p.write(p.formatStringValue(field1586))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1589 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1589 != nil {
		p.write(*flat1589)
		return nil
	} else {
		fields1588 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1588))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1591 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1591 != nil {
		p.write(*flat1591)
		return nil
	} else {
		fields1590 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1590))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1594 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1594 != nil {
		p.write(*flat1594)
		return nil
	} else {
		_dollar_dollar := msg
		fields1592 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1593 := fields1592
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1593)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1599 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1599 != nil {
		p.write(*flat1599)
		return nil
	} else {
		_dollar_dollar := msg
		fields1595 := _dollar_dollar.GetRelations()
		unwrapped_fields1596 := fields1595
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1596) == 0) {
			p.newline()
			for i1598, elem1597 := range unwrapped_fields1596 {
				if (i1598 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1597)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1606 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1606 != nil {
		p.write(*flat1606)
		return nil
	} else {
		_dollar_dollar := msg
		fields1600 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1601 := fields1600
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1602 := unwrapped_fields1601[0].([]string)
		p.pretty_edb_path(field1602)
		field1603 := unwrapped_fields1601[1].([]*pb.SnapshotMapping)
		if !(len(field1603) == 0) {
			p.newline()
			for i1605, elem1604 := range field1603 {
				if (i1605 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1604)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1611 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1611 != nil {
		p.write(*flat1611)
		return nil
	} else {
		_dollar_dollar := msg
		fields1607 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1608 := fields1607
		field1609 := unwrapped_fields1608[0].([]string)
		p.pretty_edb_path(field1609)
		p.write(" ")
		field1610 := unwrapped_fields1608[1].(*pb.RelationId)
		p.pretty_relation_id(field1610)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1615 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1615 != nil {
		p.write(*flat1615)
		return nil
	} else {
		fields1612 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1612) == 0) {
			p.newline()
			for i1614, elem1613 := range fields1612 {
				if (i1614 > 0) {
					p.newline()
				}
				p.pretty_read(elem1613)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1626 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1626 != nil {
		p.write(*flat1626)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1837 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1837 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1624 := _t1837
		if deconstruct_result1624 != nil {
			unwrapped1625 := deconstruct_result1624
			p.pretty_demand(unwrapped1625)
		} else {
			_dollar_dollar := msg
			var _t1838 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1838 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1622 := _t1838
			if deconstruct_result1622 != nil {
				unwrapped1623 := deconstruct_result1622
				p.pretty_output(unwrapped1623)
			} else {
				_dollar_dollar := msg
				var _t1839 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1839 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1620 := _t1839
				if deconstruct_result1620 != nil {
					unwrapped1621 := deconstruct_result1620
					p.pretty_what_if(unwrapped1621)
				} else {
					_dollar_dollar := msg
					var _t1840 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1840 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1618 := _t1840
					if deconstruct_result1618 != nil {
						unwrapped1619 := deconstruct_result1618
						p.pretty_abort(unwrapped1619)
					} else {
						_dollar_dollar := msg
						var _t1841 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1841 = _dollar_dollar.GetExport()
						}
						deconstruct_result1616 := _t1841
						if deconstruct_result1616 != nil {
							unwrapped1617 := deconstruct_result1616
							p.pretty_export(unwrapped1617)
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
	flat1629 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1629 != nil {
		p.write(*flat1629)
		return nil
	} else {
		_dollar_dollar := msg
		fields1627 := _dollar_dollar.GetRelationId()
		unwrapped_fields1628 := fields1627
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1628)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1634 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1634 != nil {
		p.write(*flat1634)
		return nil
	} else {
		_dollar_dollar := msg
		fields1630 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1631 := fields1630
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1632 := unwrapped_fields1631[0].(string)
		p.pretty_name(field1632)
		p.newline()
		field1633 := unwrapped_fields1631[1].(*pb.RelationId)
		p.pretty_relation_id(field1633)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1639 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1639 != nil {
		p.write(*flat1639)
		return nil
	} else {
		_dollar_dollar := msg
		fields1635 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1636 := fields1635
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1637 := unwrapped_fields1636[0].(string)
		p.pretty_name(field1637)
		p.newline()
		field1638 := unwrapped_fields1636[1].(*pb.Epoch)
		p.pretty_epoch(field1638)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1645 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1645 != nil {
		p.write(*flat1645)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1842 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1842 = ptr(_dollar_dollar.GetName())
		}
		fields1640 := []interface{}{_t1842, _dollar_dollar.GetRelationId()}
		unwrapped_fields1641 := fields1640
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1642 := unwrapped_fields1641[0].(*string)
		if field1642 != nil {
			p.newline()
			opt_val1643 := *field1642
			p.pretty_name(opt_val1643)
		}
		p.newline()
		field1644 := unwrapped_fields1641[1].(*pb.RelationId)
		p.pretty_relation_id(field1644)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1650 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1650 != nil {
		p.write(*flat1650)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1843 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1843 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1648 := _t1843
		if deconstruct_result1648 != nil {
			unwrapped1649 := deconstruct_result1648
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1649)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1844 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1844 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1646 := _t1844
			if deconstruct_result1646 != nil {
				unwrapped1647 := deconstruct_result1646
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1647)
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
	flat1661 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1661 != nil {
		p.write(*flat1661)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1845 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1846 := p.deconstruct_export_csv_output_location(_dollar_dollar)
			_t1845 = []interface{}{_t1846, _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1656 := _t1845
		if deconstruct_result1656 != nil {
			unwrapped1657 := deconstruct_result1656
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1658 := unwrapped1657[0].([]interface{})
			p.pretty_export_csv_output_location(field1658)
			p.newline()
			field1659 := unwrapped1657[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1659)
			p.newline()
			field1660 := unwrapped1657[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1660)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1847 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1848 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1847 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1848}
			}
			deconstruct_result1651 := _t1847
			if deconstruct_result1651 != nil {
				unwrapped1652 := deconstruct_result1651
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1653 := unwrapped1652[0].(string)
				p.pretty_export_csv_path(field1653)
				p.newline()
				field1654 := unwrapped1652[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1654)
				p.newline()
				field1655 := unwrapped1652[2].([][]interface{})
				p.pretty_config_dict(field1655)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_config"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_output_location(msg []interface{}) interface{} {
	flat1666 := p.tryFlat(msg, func() { p.pretty_export_csv_output_location(msg) })
	if flat1666 != nil {
		p.write(*flat1666)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1849 *string
		if _dollar_dollar[0].(string) != "" {
			_t1849 = ptr(_dollar_dollar[0].(string))
		}
		deconstruct_result1664 := _t1849
		if deconstruct_result1664 != nil {
			unwrapped1665 := *deconstruct_result1664
			p.write("(")
			p.write("path")
			p.indentSexp()
			p.newline()
			p.write(p.formatStringValue(unwrapped1665))
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1850 *string
			if _dollar_dollar[1].(string) != "" {
				_t1850 = ptr(_dollar_dollar[1].(string))
			}
			deconstruct_result1662 := _t1850
			if deconstruct_result1662 != nil {
				unwrapped1663 := *deconstruct_result1662
				p.write("(")
				p.write("transaction_output_name")
				p.indentSexp()
				p.newline()
				p.pretty_name(unwrapped1663)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_output_location"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1673 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1673 != nil {
		p.write(*flat1673)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1851 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1851 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1669 := _t1851
		if deconstruct_result1669 != nil {
			unwrapped1670 := deconstruct_result1669
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1670) == 0) {
				p.newline()
				for i1672, elem1671 := range unwrapped1670 {
					if (i1672 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1671)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1852 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1852 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1667 := _t1852
			if deconstruct_result1667 != nil {
				unwrapped1668 := deconstruct_result1667
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1668)
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
	flat1678 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1678 != nil {
		p.write(*flat1678)
		return nil
	} else {
		_dollar_dollar := msg
		fields1674 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1675 := fields1674
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1676 := unwrapped_fields1675[0].(string)
		p.write(p.formatStringValue(field1676))
		p.newline()
		field1677 := unwrapped_fields1675[1].(*pb.RelationId)
		p.pretty_relation_id(field1677)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1680 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1680 != nil {
		p.write(*flat1680)
		return nil
	} else {
		fields1679 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1679))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1684 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1684 != nil {
		p.write(*flat1684)
		return nil
	} else {
		fields1681 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1681) == 0) {
			p.newline()
			for i1683, elem1682 := range fields1681 {
				if (i1683 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1682)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1693 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1693 != nil {
		p.write(*flat1693)
		return nil
	} else {
		_dollar_dollar := msg
		_t1853 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1685 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1853}
		unwrapped_fields1686 := fields1685
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1687 := unwrapped_fields1686[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1687)
		p.newline()
		field1688 := unwrapped_fields1686[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1688)
		p.newline()
		field1689 := unwrapped_fields1686[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1689)
		p.newline()
		field1690 := unwrapped_fields1686[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1690)
		field1691 := unwrapped_fields1686[4].([][]interface{})
		if field1691 != nil {
			p.newline()
			opt_val1692 := field1691
			p.pretty_config_dict(opt_val1692)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1695 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1695 != nil {
		p.write(*flat1695)
		return nil
	} else {
		fields1694 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1694)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1699 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1699 != nil {
		p.write(*flat1699)
		return nil
	} else {
		fields1696 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1696) == 0) {
			p.newline()
			for i1698, elem1697 := range fields1696 {
				if (i1698 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1697)
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
		_t1907 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1907)
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

func (p *PrettyPrinter) pretty_cdc_targets(msg *pb.CDCTargets) interface{} {
	p.write("(cdc_targets")
	p.indentSexp()
	p.newline()
	p.write(":inserts ")
	p.write("(")
	for _idx, _elem := range msg.GetInserts() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.newline()
	p.write(":deletes ")
	p.write("(")
	for _idx, _elem := range msg.GetDeletes() {
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

func (p *PrettyPrinter) pretty_plain_targets(msg *pb.PlainTargets) interface{} {
	p.write("(plain_targets")
	p.indentSexp()
	p.newline()
	p.write(":targets ")
	p.write("(")
	for _idx, _elem := range msg.GetTargets() {
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
	case *pb.TargetRelations:
		p.pretty_target_relations(m)
	case *pb.NamedColumn:
		p.pretty_named_column(m)
	case []*pb.TargetRelation:
		p.pretty_non_cdc_relations(m)
	case *pb.TargetRelation:
		p.pretty_target_relation(m)
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
	case *pb.CDCTargets:
		p.pretty_cdc_targets(m)
	case *pb.DecimalValue:
		p.pretty_decimal_value(m)
	case *pb.FunctionalDependency:
		p.pretty_functional_dependency(m)
	case *pb.Int128Value:
		p.pretty_int128_value(m)
	case *pb.MissingValue:
		p.pretty_missing_value(m)
	case *pb.PlainTargets:
		p.pretty_plain_targets(m)
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
