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
	_t1753 := &pb.Value{}
	_t1753.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1753
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1754 := &pb.Value{}
	_t1754.Value = &pb.Value_IntValue{IntValue: v}
	return _t1754
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1755 := &pb.Value{}
	_t1755.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1755
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1756 := &pb.Value{}
	_t1756.Value = &pb.Value_StringValue{StringValue: v}
	return _t1756
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1757 := &pb.Value{}
	_t1757.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1757
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1758 := &pb.Value{}
	_t1758.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1758
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1759 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1759})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1760 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1760})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1761 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1761})
			}
		}
	}
	_t1762 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1762})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1763 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1763})
	_t1764 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1764})
	if msg.GetNewLine() != "" {
		_t1765 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1765})
	}
	_t1766 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1766})
	_t1767 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1767})
	_t1768 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1768})
	if msg.GetComment() != "" {
		_t1769 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1769})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1770 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1770})
	}
	_t1771 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1771})
	_t1772 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1772})
	_t1773 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1773})
	if msg.GetPartitionSizeMb() != 0 {
		_t1774 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1774})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1775 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1775})
	_t1776 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1776})
	_t1777 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1777})
	_t1778 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1778})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1779 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1779})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1780 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1780})
		}
	}
	_t1781 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1781})
	_t1782 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1782})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1783 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1783})
	}
	if msg.Compression != nil {
		_t1784 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1784})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1785 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1785})
	}
	if msg.SyntaxMissingString != nil {
		_t1786 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1786})
	}
	if msg.SyntaxDelim != nil {
		_t1787 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1787})
	}
	if msg.SyntaxQuotechar != nil {
		_t1788 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1788})
	}
	if msg.SyntaxEscapechar != nil {
		_t1789 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1789})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1790 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1790
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1791 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1791
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1792 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1792
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1793 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1793})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1794 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1794})
	}
	if msg.GetCompression() != "" {
		_t1795 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1795})
	}
	var _t1796 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1796
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1797 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1797
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
	flat813 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat813 != nil {
		p.write(*flat813)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1608 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1608 = _dollar_dollar.GetConfigure()
		}
		var _t1609 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1609 = _dollar_dollar.GetSync()
		}
		fields804 := []interface{}{_t1608, _t1609, _dollar_dollar.GetEpochs()}
		unwrapped_fields805 := fields804
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field806 := unwrapped_fields805[0].(*pb.Configure)
		if field806 != nil {
			p.newline()
			opt_val807 := field806
			p.pretty_configure(opt_val807)
		}
		field808 := unwrapped_fields805[1].(*pb.Sync)
		if field808 != nil {
			p.newline()
			opt_val809 := field808
			p.pretty_sync(opt_val809)
		}
		field810 := unwrapped_fields805[2].([]*pb.Epoch)
		if !(len(field810) == 0) {
			p.newline()
			for i812, elem811 := range field810 {
				if (i812 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem811)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat816 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat816 != nil {
		p.write(*flat816)
		return nil
	} else {
		_dollar_dollar := msg
		_t1610 := p.deconstruct_configure(_dollar_dollar)
		fields814 := _t1610
		unwrapped_fields815 := fields814
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields815)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat820 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		fields817 := msg
		p.write("{")
		p.indent()
		if !(len(fields817) == 0) {
			p.newline()
			for i819, elem818 := range fields817 {
				if (i819 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem818)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat825 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat825 != nil {
		p.write(*flat825)
		return nil
	} else {
		_dollar_dollar := msg
		fields821 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields822 := fields821
		p.write(":")
		field823 := unwrapped_fields822[0].(string)
		p.write(field823)
		p.write(" ")
		field824 := unwrapped_fields822[1].(*pb.Value)
		p.pretty_raw_value(field824)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat851 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat851 != nil {
		p.write(*flat851)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1611 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1611 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result849 := _t1611
		if deconstruct_result849 != nil {
			unwrapped850 := deconstruct_result849
			p.pretty_raw_date(unwrapped850)
		} else {
			_dollar_dollar := msg
			var _t1612 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1612 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result847 := _t1612
			if deconstruct_result847 != nil {
				unwrapped848 := deconstruct_result847
				p.pretty_raw_datetime(unwrapped848)
			} else {
				_dollar_dollar := msg
				var _t1613 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1613 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result845 := _t1613
				if deconstruct_result845 != nil {
					unwrapped846 := *deconstruct_result845
					p.write(p.formatStringValue(unwrapped846))
				} else {
					_dollar_dollar := msg
					var _t1614 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1614 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result843 := _t1614
					if deconstruct_result843 != nil {
						unwrapped844 := *deconstruct_result843
						p.write(fmt.Sprintf("%di32", unwrapped844))
					} else {
						_dollar_dollar := msg
						var _t1615 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1615 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result841 := _t1615
						if deconstruct_result841 != nil {
							unwrapped842 := *deconstruct_result841
							p.write(fmt.Sprintf("%d", unwrapped842))
						} else {
							_dollar_dollar := msg
							var _t1616 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1616 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result839 := _t1616
							if deconstruct_result839 != nil {
								unwrapped840 := *deconstruct_result839
								p.write(formatFloat32(unwrapped840))
							} else {
								_dollar_dollar := msg
								var _t1617 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1617 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result837 := _t1617
								if deconstruct_result837 != nil {
									unwrapped838 := *deconstruct_result837
									p.write(formatFloat64(unwrapped838))
								} else {
									_dollar_dollar := msg
									var _t1618 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1618 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result835 := _t1618
									if deconstruct_result835 != nil {
										unwrapped836 := *deconstruct_result835
										p.write(fmt.Sprintf("%du32", unwrapped836))
									} else {
										_dollar_dollar := msg
										var _t1619 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1619 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result833 := _t1619
										if deconstruct_result833 != nil {
											unwrapped834 := deconstruct_result833
											p.write(p.formatUint128(unwrapped834))
										} else {
											_dollar_dollar := msg
											var _t1620 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1620 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result831 := _t1620
											if deconstruct_result831 != nil {
												unwrapped832 := deconstruct_result831
												p.write(p.formatInt128(unwrapped832))
											} else {
												_dollar_dollar := msg
												var _t1621 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1621 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result829 := _t1621
												if deconstruct_result829 != nil {
													unwrapped830 := deconstruct_result829
													p.write(p.formatDecimal(unwrapped830))
												} else {
													_dollar_dollar := msg
													var _t1622 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1622 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result827 := _t1622
													if deconstruct_result827 != nil {
														unwrapped828 := *deconstruct_result827
														p.pretty_boolean_value(unwrapped828)
													} else {
														fields826 := msg
														_ = fields826
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
	flat857 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat857 != nil {
		p.write(*flat857)
		return nil
	} else {
		_dollar_dollar := msg
		fields852 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields853 := fields852
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field854 := unwrapped_fields853[0].(int64)
		p.write(fmt.Sprintf("%d", field854))
		p.newline()
		field855 := unwrapped_fields853[1].(int64)
		p.write(fmt.Sprintf("%d", field855))
		p.newline()
		field856 := unwrapped_fields853[2].(int64)
		p.write(fmt.Sprintf("%d", field856))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat868 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat868 != nil {
		p.write(*flat868)
		return nil
	} else {
		_dollar_dollar := msg
		fields858 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields859 := fields858
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field860 := unwrapped_fields859[0].(int64)
		p.write(fmt.Sprintf("%d", field860))
		p.newline()
		field861 := unwrapped_fields859[1].(int64)
		p.write(fmt.Sprintf("%d", field861))
		p.newline()
		field862 := unwrapped_fields859[2].(int64)
		p.write(fmt.Sprintf("%d", field862))
		p.newline()
		field863 := unwrapped_fields859[3].(int64)
		p.write(fmt.Sprintf("%d", field863))
		p.newline()
		field864 := unwrapped_fields859[4].(int64)
		p.write(fmt.Sprintf("%d", field864))
		p.newline()
		field865 := unwrapped_fields859[5].(int64)
		p.write(fmt.Sprintf("%d", field865))
		field866 := unwrapped_fields859[6].(*int64)
		if field866 != nil {
			p.newline()
			opt_val867 := *field866
			p.write(fmt.Sprintf("%d", opt_val867))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1623 []interface{}
	if _dollar_dollar {
		_t1623 = []interface{}{}
	}
	deconstruct_result871 := _t1623
	if deconstruct_result871 != nil {
		unwrapped872 := deconstruct_result871
		_ = unwrapped872
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1624 []interface{}
		if !(_dollar_dollar) {
			_t1624 = []interface{}{}
		}
		deconstruct_result869 := _t1624
		if deconstruct_result869 != nil {
			unwrapped870 := deconstruct_result869
			_ = unwrapped870
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_dollar_dollar := msg
		fields873 := _dollar_dollar.GetFragments()
		unwrapped_fields874 := fields873
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields874) == 0) {
			p.newline()
			for i876, elem875 := range unwrapped_fields874 {
				if (i876 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem875)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat880 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat880 != nil {
		p.write(*flat880)
		return nil
	} else {
		_dollar_dollar := msg
		fields878 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields879 := fields878
		p.write(":")
		p.write(unwrapped_fields879)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1625 = _dollar_dollar.GetWrites()
		}
		var _t1626 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1626 = _dollar_dollar.GetReads()
		}
		fields881 := []interface{}{_t1625, _t1626}
		unwrapped_fields882 := fields881
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field883 := unwrapped_fields882[0].([]*pb.Write)
		if field883 != nil {
			p.newline()
			opt_val884 := field883
			p.pretty_epoch_writes(opt_val884)
		}
		field885 := unwrapped_fields882[1].([]*pb.Read)
		if field885 != nil {
			p.newline()
			opt_val886 := field885
			p.pretty_epoch_reads(opt_val886)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat891 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		fields888 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields888) == 0) {
			p.newline()
			for i890, elem889 := range fields888 {
				if (i890 > 0) {
					p.newline()
				}
				p.pretty_write(elem889)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat900 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat900 != nil {
		p.write(*flat900)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1627 = _dollar_dollar.GetDefine()
		}
		deconstruct_result898 := _t1627
		if deconstruct_result898 != nil {
			unwrapped899 := deconstruct_result898
			p.pretty_define(unwrapped899)
		} else {
			_dollar_dollar := msg
			var _t1628 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1628 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result896 := _t1628
			if deconstruct_result896 != nil {
				unwrapped897 := deconstruct_result896
				p.pretty_undefine(unwrapped897)
			} else {
				_dollar_dollar := msg
				var _t1629 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1629 = _dollar_dollar.GetContext()
				}
				deconstruct_result894 := _t1629
				if deconstruct_result894 != nil {
					unwrapped895 := deconstruct_result894
					p.pretty_context(unwrapped895)
				} else {
					_dollar_dollar := msg
					var _t1630 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1630 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result892 := _t1630
					if deconstruct_result892 != nil {
						unwrapped893 := deconstruct_result892
						p.pretty_snapshot(unwrapped893)
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
	flat903 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat903 != nil {
		p.write(*flat903)
		return nil
	} else {
		_dollar_dollar := msg
		fields901 := _dollar_dollar.GetFragment()
		unwrapped_fields902 := fields901
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields902)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat910 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat910 != nil {
		p.write(*flat910)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields904 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields905 := fields904
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field906 := unwrapped_fields905[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field906)
		field907 := unwrapped_fields905[1].([]*pb.Declaration)
		if !(len(field907) == 0) {
			p.newline()
			for i909, elem908 := range field907 {
				if (i909 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem908)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat912 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat912 != nil {
		p.write(*flat912)
		return nil
	} else {
		fields911 := msg
		p.pretty_fragment_id(fields911)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat921 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat921 != nil {
		p.write(*flat921)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1631 = _dollar_dollar.GetDef()
		}
		deconstruct_result919 := _t1631
		if deconstruct_result919 != nil {
			unwrapped920 := deconstruct_result919
			p.pretty_def(unwrapped920)
		} else {
			_dollar_dollar := msg
			var _t1632 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1632 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result917 := _t1632
			if deconstruct_result917 != nil {
				unwrapped918 := deconstruct_result917
				p.pretty_algorithm(unwrapped918)
			} else {
				_dollar_dollar := msg
				var _t1633 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1633 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result915 := _t1633
				if deconstruct_result915 != nil {
					unwrapped916 := deconstruct_result915
					p.pretty_constraint(unwrapped916)
				} else {
					_dollar_dollar := msg
					var _t1634 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1634 = _dollar_dollar.GetData()
					}
					deconstruct_result913 := _t1634
					if deconstruct_result913 != nil {
						unwrapped914 := deconstruct_result913
						p.pretty_data(unwrapped914)
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
	flat928 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat928 != nil {
		p.write(*flat928)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1635 = _dollar_dollar.GetAttrs()
		}
		fields922 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1635}
		unwrapped_fields923 := fields922
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field924 := unwrapped_fields923[0].(*pb.RelationId)
		p.pretty_relation_id(field924)
		p.newline()
		field925 := unwrapped_fields923[1].(*pb.Abstraction)
		p.pretty_abstraction(field925)
		field926 := unwrapped_fields923[2].([]*pb.Attribute)
		if field926 != nil {
			p.newline()
			opt_val927 := field926
			p.pretty_attrs(opt_val927)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat933 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat933 != nil {
		p.write(*flat933)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1636 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1637 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1636 = ptr(_t1637)
		}
		deconstruct_result931 := _t1636
		if deconstruct_result931 != nil {
			unwrapped932 := *deconstruct_result931
			p.write(":")
			p.write(unwrapped932)
		} else {
			_dollar_dollar := msg
			_t1638 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result929 := _t1638
			if deconstruct_result929 != nil {
				unwrapped930 := deconstruct_result929
				p.write(p.formatUint128(unwrapped930))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat938 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat938 != nil {
		p.write(*flat938)
		return nil
	} else {
		_dollar_dollar := msg
		_t1639 := p.deconstruct_bindings(_dollar_dollar)
		fields934 := []interface{}{_t1639, _dollar_dollar.GetValue()}
		unwrapped_fields935 := fields934
		p.write("(")
		p.indent()
		field936 := unwrapped_fields935[0].([]interface{})
		p.pretty_bindings(field936)
		p.newline()
		field937 := unwrapped_fields935[1].(*pb.Formula)
		p.pretty_formula(field937)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1640 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1640 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields939 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1640}
		unwrapped_fields940 := fields939
		p.write("[")
		p.indent()
		field941 := unwrapped_fields940[0].([]*pb.Binding)
		for i943, elem942 := range field941 {
			if (i943 > 0) {
				p.newline()
			}
			p.pretty_binding(elem942)
		}
		field944 := unwrapped_fields940[1].([]*pb.Binding)
		if field944 != nil {
			p.newline()
			opt_val945 := field944
			p.pretty_value_bindings(opt_val945)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat951 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat951 != nil {
		p.write(*flat951)
		return nil
	} else {
		_dollar_dollar := msg
		fields947 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields948 := fields947
		field949 := unwrapped_fields948[0].(string)
		p.write(field949)
		p.write("::")
		field950 := unwrapped_fields948[1].(*pb.Type)
		p.pretty_type(field950)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat980 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat980 != nil {
		p.write(*flat980)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1641 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result978 := _t1641
		if deconstruct_result978 != nil {
			unwrapped979 := deconstruct_result978
			p.pretty_unspecified_type(unwrapped979)
		} else {
			_dollar_dollar := msg
			var _t1642 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1642 = _dollar_dollar.GetStringType()
			}
			deconstruct_result976 := _t1642
			if deconstruct_result976 != nil {
				unwrapped977 := deconstruct_result976
				p.pretty_string_type(unwrapped977)
			} else {
				_dollar_dollar := msg
				var _t1643 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1643 = _dollar_dollar.GetIntType()
				}
				deconstruct_result974 := _t1643
				if deconstruct_result974 != nil {
					unwrapped975 := deconstruct_result974
					p.pretty_int_type(unwrapped975)
				} else {
					_dollar_dollar := msg
					var _t1644 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1644 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result972 := _t1644
					if deconstruct_result972 != nil {
						unwrapped973 := deconstruct_result972
						p.pretty_float_type(unwrapped973)
					} else {
						_dollar_dollar := msg
						var _t1645 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1645 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result970 := _t1645
						if deconstruct_result970 != nil {
							unwrapped971 := deconstruct_result970
							p.pretty_uint128_type(unwrapped971)
						} else {
							_dollar_dollar := msg
							var _t1646 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1646 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result968 := _t1646
							if deconstruct_result968 != nil {
								unwrapped969 := deconstruct_result968
								p.pretty_int128_type(unwrapped969)
							} else {
								_dollar_dollar := msg
								var _t1647 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1647 = _dollar_dollar.GetDateType()
								}
								deconstruct_result966 := _t1647
								if deconstruct_result966 != nil {
									unwrapped967 := deconstruct_result966
									p.pretty_date_type(unwrapped967)
								} else {
									_dollar_dollar := msg
									var _t1648 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1648 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result964 := _t1648
									if deconstruct_result964 != nil {
										unwrapped965 := deconstruct_result964
										p.pretty_datetime_type(unwrapped965)
									} else {
										_dollar_dollar := msg
										var _t1649 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1649 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result962 := _t1649
										if deconstruct_result962 != nil {
											unwrapped963 := deconstruct_result962
											p.pretty_missing_type(unwrapped963)
										} else {
											_dollar_dollar := msg
											var _t1650 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1650 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result960 := _t1650
											if deconstruct_result960 != nil {
												unwrapped961 := deconstruct_result960
												p.pretty_decimal_type(unwrapped961)
											} else {
												_dollar_dollar := msg
												var _t1651 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1651 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result958 := _t1651
												if deconstruct_result958 != nil {
													unwrapped959 := deconstruct_result958
													p.pretty_boolean_type(unwrapped959)
												} else {
													_dollar_dollar := msg
													var _t1652 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1652 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result956 := _t1652
													if deconstruct_result956 != nil {
														unwrapped957 := deconstruct_result956
														p.pretty_int32_type(unwrapped957)
													} else {
														_dollar_dollar := msg
														var _t1653 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1653 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result954 := _t1653
														if deconstruct_result954 != nil {
															unwrapped955 := deconstruct_result954
															p.pretty_float32_type(unwrapped955)
														} else {
															_dollar_dollar := msg
															var _t1654 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1654 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result952 := _t1654
															if deconstruct_result952 != nil {
																unwrapped953 := deconstruct_result952
																p.pretty_uint32_type(unwrapped953)
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
	fields981 := msg
	_ = fields981
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields982 := msg
	_ = fields982
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields983 := msg
	_ = fields983
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields984 := msg
	_ = fields984
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields985 := msg
	_ = fields985
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields986 := msg
	_ = fields986
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields987 := msg
	_ = fields987
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields988 := msg
	_ = fields988
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields989 := msg
	_ = fields989
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat994 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat994 != nil {
		p.write(*flat994)
		return nil
	} else {
		_dollar_dollar := msg
		fields990 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields991 := fields990
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field992 := unwrapped_fields991[0].(int64)
		p.write(fmt.Sprintf("%d", field992))
		p.newline()
		field993 := unwrapped_fields991[1].(int64)
		p.write(fmt.Sprintf("%d", field993))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields995 := msg
	_ = fields995
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields996 := msg
	_ = fields996
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields997 := msg
	_ = fields997
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields998 := msg
	_ = fields998
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1002 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1002 != nil {
		p.write(*flat1002)
		return nil
	} else {
		fields999 := msg
		p.write("|")
		if !(len(fields999) == 0) {
			p.write(" ")
			for i1001, elem1000 := range fields999 {
				if (i1001 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1000)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1029 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1029 != nil {
		p.write(*flat1029)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1655 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1027 := _t1655
		if deconstruct_result1027 != nil {
			unwrapped1028 := deconstruct_result1027
			p.pretty_true(unwrapped1028)
		} else {
			_dollar_dollar := msg
			var _t1656 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1656 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1025 := _t1656
			if deconstruct_result1025 != nil {
				unwrapped1026 := deconstruct_result1025
				p.pretty_false(unwrapped1026)
			} else {
				_dollar_dollar := msg
				var _t1657 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1657 = _dollar_dollar.GetExists()
				}
				deconstruct_result1023 := _t1657
				if deconstruct_result1023 != nil {
					unwrapped1024 := deconstruct_result1023
					p.pretty_exists(unwrapped1024)
				} else {
					_dollar_dollar := msg
					var _t1658 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1658 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1021 := _t1658
					if deconstruct_result1021 != nil {
						unwrapped1022 := deconstruct_result1021
						p.pretty_reduce(unwrapped1022)
					} else {
						_dollar_dollar := msg
						var _t1659 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1659 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1019 := _t1659
						if deconstruct_result1019 != nil {
							unwrapped1020 := deconstruct_result1019
							p.pretty_conjunction(unwrapped1020)
						} else {
							_dollar_dollar := msg
							var _t1660 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1660 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1017 := _t1660
							if deconstruct_result1017 != nil {
								unwrapped1018 := deconstruct_result1017
								p.pretty_disjunction(unwrapped1018)
							} else {
								_dollar_dollar := msg
								var _t1661 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1661 = _dollar_dollar.GetNot()
								}
								deconstruct_result1015 := _t1661
								if deconstruct_result1015 != nil {
									unwrapped1016 := deconstruct_result1015
									p.pretty_not(unwrapped1016)
								} else {
									_dollar_dollar := msg
									var _t1662 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1662 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1013 := _t1662
									if deconstruct_result1013 != nil {
										unwrapped1014 := deconstruct_result1013
										p.pretty_ffi(unwrapped1014)
									} else {
										_dollar_dollar := msg
										var _t1663 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1663 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1011 := _t1663
										if deconstruct_result1011 != nil {
											unwrapped1012 := deconstruct_result1011
											p.pretty_atom(unwrapped1012)
										} else {
											_dollar_dollar := msg
											var _t1664 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1664 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1009 := _t1664
											if deconstruct_result1009 != nil {
												unwrapped1010 := deconstruct_result1009
												p.pretty_pragma(unwrapped1010)
											} else {
												_dollar_dollar := msg
												var _t1665 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1665 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1007 := _t1665
												if deconstruct_result1007 != nil {
													unwrapped1008 := deconstruct_result1007
													p.pretty_primitive(unwrapped1008)
												} else {
													_dollar_dollar := msg
													var _t1666 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1666 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1005 := _t1666
													if deconstruct_result1005 != nil {
														unwrapped1006 := deconstruct_result1005
														p.pretty_rel_atom(unwrapped1006)
													} else {
														_dollar_dollar := msg
														var _t1667 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1667 = _dollar_dollar.GetCast()
														}
														deconstruct_result1003 := _t1667
														if deconstruct_result1003 != nil {
															unwrapped1004 := deconstruct_result1003
															p.pretty_cast(unwrapped1004)
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
	fields1030 := msg
	_ = fields1030
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1031 := msg
	_ = fields1031
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1036 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1036 != nil {
		p.write(*flat1036)
		return nil
	} else {
		_dollar_dollar := msg
		_t1668 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1032 := []interface{}{_t1668, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1033 := fields1032
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1034 := unwrapped_fields1033[0].([]interface{})
		p.pretty_bindings(field1034)
		p.newline()
		field1035 := unwrapped_fields1033[1].(*pb.Formula)
		p.pretty_formula(field1035)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		_dollar_dollar := msg
		fields1037 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1038 := fields1037
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1039 := unwrapped_fields1038[0].(*pb.Abstraction)
		p.pretty_abstraction(field1039)
		p.newline()
		field1040 := unwrapped_fields1038[1].(*pb.Abstraction)
		p.pretty_abstraction(field1040)
		p.newline()
		field1041 := unwrapped_fields1038[2].([]*pb.Term)
		p.pretty_terms(field1041)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1046 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1046 != nil {
		p.write(*flat1046)
		return nil
	} else {
		fields1043 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1043) == 0) {
			p.newline()
			for i1045, elem1044 := range fields1043 {
				if (i1045 > 0) {
					p.newline()
				}
				p.pretty_term(elem1044)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1669 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1669 = _dollar_dollar.GetVar()
		}
		deconstruct_result1049 := _t1669
		if deconstruct_result1049 != nil {
			unwrapped1050 := deconstruct_result1049
			p.pretty_var(unwrapped1050)
		} else {
			_dollar_dollar := msg
			var _t1670 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1670 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1047 := _t1670
			if deconstruct_result1047 != nil {
				unwrapped1048 := deconstruct_result1047
				p.pretty_value(unwrapped1048)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1054 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_dollar_dollar := msg
		fields1052 := _dollar_dollar.GetName()
		unwrapped_fields1053 := fields1052
		p.write(unwrapped_fields1053)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1080 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1080 != nil {
		p.write(*flat1080)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1671 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1078 := _t1671
		if deconstruct_result1078 != nil {
			unwrapped1079 := deconstruct_result1078
			p.pretty_date(unwrapped1079)
		} else {
			_dollar_dollar := msg
			var _t1672 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1672 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1076 := _t1672
			if deconstruct_result1076 != nil {
				unwrapped1077 := deconstruct_result1076
				p.pretty_datetime(unwrapped1077)
			} else {
				_dollar_dollar := msg
				var _t1673 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1673 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1074 := _t1673
				if deconstruct_result1074 != nil {
					unwrapped1075 := *deconstruct_result1074
					p.write(p.formatStringValue(unwrapped1075))
				} else {
					_dollar_dollar := msg
					var _t1674 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1674 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1072 := _t1674
					if deconstruct_result1072 != nil {
						unwrapped1073 := *deconstruct_result1072
						p.write(fmt.Sprintf("%di32", unwrapped1073))
					} else {
						_dollar_dollar := msg
						var _t1675 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1675 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1070 := _t1675
						if deconstruct_result1070 != nil {
							unwrapped1071 := *deconstruct_result1070
							p.write(fmt.Sprintf("%d", unwrapped1071))
						} else {
							_dollar_dollar := msg
							var _t1676 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1676 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1068 := _t1676
							if deconstruct_result1068 != nil {
								unwrapped1069 := *deconstruct_result1068
								p.write(formatFloat32(unwrapped1069))
							} else {
								_dollar_dollar := msg
								var _t1677 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1677 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1066 := _t1677
								if deconstruct_result1066 != nil {
									unwrapped1067 := *deconstruct_result1066
									p.write(formatFloat64(unwrapped1067))
								} else {
									_dollar_dollar := msg
									var _t1678 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1678 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1064 := _t1678
									if deconstruct_result1064 != nil {
										unwrapped1065 := *deconstruct_result1064
										p.write(fmt.Sprintf("%du32", unwrapped1065))
									} else {
										_dollar_dollar := msg
										var _t1679 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1679 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1062 := _t1679
										if deconstruct_result1062 != nil {
											unwrapped1063 := deconstruct_result1062
											p.write(p.formatUint128(unwrapped1063))
										} else {
											_dollar_dollar := msg
											var _t1680 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1680 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1060 := _t1680
											if deconstruct_result1060 != nil {
												unwrapped1061 := deconstruct_result1060
												p.write(p.formatInt128(unwrapped1061))
											} else {
												_dollar_dollar := msg
												var _t1681 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1681 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1058 := _t1681
												if deconstruct_result1058 != nil {
													unwrapped1059 := deconstruct_result1058
													p.write(p.formatDecimal(unwrapped1059))
												} else {
													_dollar_dollar := msg
													var _t1682 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1682 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1056 := _t1682
													if deconstruct_result1056 != nil {
														unwrapped1057 := *deconstruct_result1056
														p.pretty_boolean_value(unwrapped1057)
													} else {
														fields1055 := msg
														_ = fields1055
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
	flat1086 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1086 != nil {
		p.write(*flat1086)
		return nil
	} else {
		_dollar_dollar := msg
		fields1081 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1082 := fields1081
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1083 := unwrapped_fields1082[0].(int64)
		p.write(fmt.Sprintf("%d", field1083))
		p.newline()
		field1084 := unwrapped_fields1082[1].(int64)
		p.write(fmt.Sprintf("%d", field1084))
		p.newline()
		field1085 := unwrapped_fields1082[2].(int64)
		p.write(fmt.Sprintf("%d", field1085))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1097 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1097 != nil {
		p.write(*flat1097)
		return nil
	} else {
		_dollar_dollar := msg
		fields1087 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1088 := fields1087
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1089 := unwrapped_fields1088[0].(int64)
		p.write(fmt.Sprintf("%d", field1089))
		p.newline()
		field1090 := unwrapped_fields1088[1].(int64)
		p.write(fmt.Sprintf("%d", field1090))
		p.newline()
		field1091 := unwrapped_fields1088[2].(int64)
		p.write(fmt.Sprintf("%d", field1091))
		p.newline()
		field1092 := unwrapped_fields1088[3].(int64)
		p.write(fmt.Sprintf("%d", field1092))
		p.newline()
		field1093 := unwrapped_fields1088[4].(int64)
		p.write(fmt.Sprintf("%d", field1093))
		p.newline()
		field1094 := unwrapped_fields1088[5].(int64)
		p.write(fmt.Sprintf("%d", field1094))
		field1095 := unwrapped_fields1088[6].(*int64)
		if field1095 != nil {
			p.newline()
			opt_val1096 := *field1095
			p.write(fmt.Sprintf("%d", opt_val1096))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1098 := _dollar_dollar.GetArgs()
		unwrapped_fields1099 := fields1098
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1099) == 0) {
			p.newline()
			for i1101, elem1100 := range unwrapped_fields1099 {
				if (i1101 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1100)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		fields1103 := _dollar_dollar.GetArgs()
		unwrapped_fields1104 := fields1103
		p.write("(")
		p.write("or")
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

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1110 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1110 != nil {
		p.write(*flat1110)
		return nil
	} else {
		_dollar_dollar := msg
		fields1108 := _dollar_dollar.GetArg()
		unwrapped_fields1109 := fields1108
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1109)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1116 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1116 != nil {
		p.write(*flat1116)
		return nil
	} else {
		_dollar_dollar := msg
		fields1111 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1112 := fields1111
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1113 := unwrapped_fields1112[0].(string)
		p.pretty_name(field1113)
		p.newline()
		field1114 := unwrapped_fields1112[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1114)
		p.newline()
		field1115 := unwrapped_fields1112[2].([]*pb.Term)
		p.pretty_terms(field1115)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		fields1117 := msg
		p.write(":")
		p.write(fields1117)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1122 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1122 != nil {
		p.write(*flat1122)
		return nil
	} else {
		fields1119 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1119) == 0) {
			p.newline()
			for i1121, elem1120 := range fields1119 {
				if (i1121 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1120)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1129 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		_dollar_dollar := msg
		fields1123 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1124 := fields1123
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1125 := unwrapped_fields1124[0].(*pb.RelationId)
		p.pretty_relation_id(field1125)
		field1126 := unwrapped_fields1124[1].([]*pb.Term)
		if !(len(field1126) == 0) {
			p.newline()
			for i1128, elem1127 := range field1126 {
				if (i1128 > 0) {
					p.newline()
				}
				p.pretty_term(elem1127)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1136 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1136 != nil {
		p.write(*flat1136)
		return nil
	} else {
		_dollar_dollar := msg
		fields1130 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1131 := fields1130
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1132 := unwrapped_fields1131[0].(string)
		p.pretty_name(field1132)
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

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1152 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1152 != nil {
		p.write(*flat1152)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1683 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1683 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1151 := _t1683
		if guard_result1151 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1684 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1684 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1150 := _t1684
			if guard_result1150 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1685 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1685 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1149 := _t1685
				if guard_result1149 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1686 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1686 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1148 := _t1686
					if guard_result1148 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1687 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1687 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1147 := _t1687
						if guard_result1147 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1688 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1688 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1146 := _t1688
							if guard_result1146 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1689 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1689 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1145 := _t1689
								if guard_result1145 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1690 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1690 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1144 := _t1690
									if guard_result1144 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1691 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1691 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1143 := _t1691
										if guard_result1143 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1137 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1138 := fields1137
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1139 := unwrapped_fields1138[0].(string)
											p.pretty_name(field1139)
											field1140 := unwrapped_fields1138[1].([]*pb.RelTerm)
											if !(len(field1140) == 0) {
												p.newline()
												for i1142, elem1141 := range field1140 {
													if (i1142 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1141)
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
	flat1157 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1692 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1692 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1153 := _t1692
		unwrapped_fields1154 := fields1153
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1155 := unwrapped_fields1154[0].(*pb.Term)
		p.pretty_term(field1155)
		p.newline()
		field1156 := unwrapped_fields1154[1].(*pb.Term)
		p.pretty_term(field1156)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1693 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1158 := _t1693
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1694 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1694 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1163 := _t1694
		unwrapped_fields1164 := fields1163
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1695 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1695 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1168 := _t1695
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write(">")
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

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1177 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1177 != nil {
		p.write(*flat1177)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1696 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1696 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1173 := _t1696
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1697 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1178 := _t1697
		unwrapped_fields1179 := fields1178
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1180 := unwrapped_fields1179[0].(*pb.Term)
		p.pretty_term(field1180)
		p.newline()
		field1181 := unwrapped_fields1179[1].(*pb.Term)
		p.pretty_term(field1181)
		p.newline()
		field1182 := unwrapped_fields1179[2].(*pb.Term)
		p.pretty_term(field1182)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1698 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1698 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1184 := _t1698
		unwrapped_fields1185 := fields1184
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1186 := unwrapped_fields1185[0].(*pb.Term)
		p.pretty_term(field1186)
		p.newline()
		field1187 := unwrapped_fields1185[1].(*pb.Term)
		p.pretty_term(field1187)
		p.newline()
		field1188 := unwrapped_fields1185[2].(*pb.Term)
		p.pretty_term(field1188)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1195 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1195 != nil {
		p.write(*flat1195)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1699 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1699 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1190 := _t1699
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1192 := unwrapped_fields1191[0].(*pb.Term)
		p.pretty_term(field1192)
		p.newline()
		field1193 := unwrapped_fields1191[1].(*pb.Term)
		p.pretty_term(field1193)
		p.newline()
		field1194 := unwrapped_fields1191[2].(*pb.Term)
		p.pretty_term(field1194)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1201 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1201 != nil {
		p.write(*flat1201)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1700 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1700 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1196 := _t1700
		unwrapped_fields1197 := fields1196
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1198 := unwrapped_fields1197[0].(*pb.Term)
		p.pretty_term(field1198)
		p.newline()
		field1199 := unwrapped_fields1197[1].(*pb.Term)
		p.pretty_term(field1199)
		p.newline()
		field1200 := unwrapped_fields1197[2].(*pb.Term)
		p.pretty_term(field1200)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1206 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1206 != nil {
		p.write(*flat1206)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1701 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1701 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1204 := _t1701
		if deconstruct_result1204 != nil {
			unwrapped1205 := deconstruct_result1204
			p.pretty_specialized_value(unwrapped1205)
		} else {
			_dollar_dollar := msg
			var _t1702 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1702 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1202 := _t1702
			if deconstruct_result1202 != nil {
				unwrapped1203 := deconstruct_result1202
				p.pretty_term(unwrapped1203)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		fields1207 := msg
		p.write("#")
		p.pretty_raw_value(fields1207)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		fields1209 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1210 := fields1209
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1211 := unwrapped_fields1210[0].(string)
		p.pretty_name(field1211)
		field1212 := unwrapped_fields1210[1].([]*pb.RelTerm)
		if !(len(field1212) == 0) {
			p.newline()
			for i1214, elem1213 := range field1212 {
				if (i1214 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1213)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		fields1216 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1218 := unwrapped_fields1217[0].(*pb.Term)
		p.pretty_term(field1218)
		p.newline()
		field1219 := unwrapped_fields1217[1].(*pb.Term)
		p.pretty_term(field1219)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		fields1221 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1221) == 0) {
			p.newline()
			for i1223, elem1222 := range fields1221 {
				if (i1223 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1222)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_dollar_dollar := msg
		fields1225 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1226 := fields1225
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1227 := unwrapped_fields1226[0].(string)
		p.pretty_name(field1227)
		field1228 := unwrapped_fields1226[1].([]*pb.Value)
		if !(len(field1228) == 0) {
			p.newline()
			for i1230, elem1229 := range field1228 {
				if (i1230 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1229)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1240 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1240 != nil {
		p.write(*flat1240)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1703 = _dollar_dollar.GetAttrs()
		}
		fields1232 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1703}
		unwrapped_fields1233 := fields1232
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1234 := unwrapped_fields1233[0].([]*pb.RelationId)
		if !(len(field1234) == 0) {
			p.newline()
			for i1236, elem1235 := range field1234 {
				if (i1236 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1235)
			}
		}
		p.newline()
		field1237 := unwrapped_fields1233[1].(*pb.Script)
		p.pretty_script(field1237)
		field1238 := unwrapped_fields1233[2].([]*pb.Attribute)
		if field1238 != nil {
			p.newline()
			opt_val1239 := field1238
			p.pretty_attrs(opt_val1239)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		_dollar_dollar := msg
		fields1241 := _dollar_dollar.GetConstructs()
		unwrapped_fields1242 := fields1241
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1242) == 0) {
			p.newline()
			for i1244, elem1243 := range unwrapped_fields1242 {
				if (i1244 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1243)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1250 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1250 != nil {
		p.write(*flat1250)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1704 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1704 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1248 := _t1704
		if deconstruct_result1248 != nil {
			unwrapped1249 := deconstruct_result1248
			p.pretty_loop(unwrapped1249)
		} else {
			_dollar_dollar := msg
			var _t1705 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1705 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1246 := _t1705
			if deconstruct_result1246 != nil {
				unwrapped1247 := deconstruct_result1246
				p.pretty_instruction(unwrapped1247)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1706 = _dollar_dollar.GetAttrs()
		}
		fields1251 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1706}
		unwrapped_fields1252 := fields1251
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1253 := unwrapped_fields1252[0].([]*pb.Instruction)
		p.pretty_init(field1253)
		p.newline()
		field1254 := unwrapped_fields1252[1].(*pb.Script)
		p.pretty_script(field1254)
		field1255 := unwrapped_fields1252[2].([]*pb.Attribute)
		if field1255 != nil {
			p.newline()
			opt_val1256 := field1255
			p.pretty_attrs(opt_val1256)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		fields1258 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1258) == 0) {
			p.newline()
			for i1260, elem1259 := range fields1258 {
				if (i1260 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1259)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1707 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1270 := _t1707
		if deconstruct_result1270 != nil {
			unwrapped1271 := deconstruct_result1270
			p.pretty_assign(unwrapped1271)
		} else {
			_dollar_dollar := msg
			var _t1708 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1708 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1268 := _t1708
			if deconstruct_result1268 != nil {
				unwrapped1269 := deconstruct_result1268
				p.pretty_upsert(unwrapped1269)
			} else {
				_dollar_dollar := msg
				var _t1709 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1709 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1266 := _t1709
				if deconstruct_result1266 != nil {
					unwrapped1267 := deconstruct_result1266
					p.pretty_break(unwrapped1267)
				} else {
					_dollar_dollar := msg
					var _t1710 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1710 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1264 := _t1710
					if deconstruct_result1264 != nil {
						unwrapped1265 := deconstruct_result1264
						p.pretty_monoid_def(unwrapped1265)
					} else {
						_dollar_dollar := msg
						var _t1711 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1711 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1262 := _t1711
						if deconstruct_result1262 != nil {
							unwrapped1263 := deconstruct_result1262
							p.pretty_monus_def(unwrapped1263)
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
	flat1279 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1279 != nil {
		p.write(*flat1279)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1712 = _dollar_dollar.GetAttrs()
		}
		fields1273 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1712}
		unwrapped_fields1274 := fields1273
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1275 := unwrapped_fields1274[0].(*pb.RelationId)
		p.pretty_relation_id(field1275)
		p.newline()
		field1276 := unwrapped_fields1274[1].(*pb.Abstraction)
		p.pretty_abstraction(field1276)
		field1277 := unwrapped_fields1274[2].([]*pb.Attribute)
		if field1277 != nil {
			p.newline()
			opt_val1278 := field1277
			p.pretty_attrs(opt_val1278)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1713 = _dollar_dollar.GetAttrs()
		}
		fields1280 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1713}
		unwrapped_fields1281 := fields1280
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1282 := unwrapped_fields1281[0].(*pb.RelationId)
		p.pretty_relation_id(field1282)
		p.newline()
		field1283 := unwrapped_fields1281[1].([]interface{})
		p.pretty_abstraction_with_arity(field1283)
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

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		_dollar_dollar := msg
		_t1714 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1287 := []interface{}{_t1714, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.indent()
		field1289 := unwrapped_fields1288[0].([]interface{})
		p.pretty_bindings(field1289)
		p.newline()
		field1290 := unwrapped_fields1288[1].(*pb.Formula)
		p.pretty_formula(field1290)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1298 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1298 != nil {
		p.write(*flat1298)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1715 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1715 = _dollar_dollar.GetAttrs()
		}
		fields1292 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1715}
		unwrapped_fields1293 := fields1292
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1294 := unwrapped_fields1293[0].(*pb.RelationId)
		p.pretty_relation_id(field1294)
		p.newline()
		field1295 := unwrapped_fields1293[1].(*pb.Abstraction)
		p.pretty_abstraction(field1295)
		field1296 := unwrapped_fields1293[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1306 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1306 != nil {
		p.write(*flat1306)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1716 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1716 = _dollar_dollar.GetAttrs()
		}
		fields1299 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1716}
		unwrapped_fields1300 := fields1299
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1301 := unwrapped_fields1300[0].(*pb.Monoid)
		p.pretty_monoid(field1301)
		p.newline()
		field1302 := unwrapped_fields1300[1].(*pb.RelationId)
		p.pretty_relation_id(field1302)
		p.newline()
		field1303 := unwrapped_fields1300[2].([]interface{})
		p.pretty_abstraction_with_arity(field1303)
		field1304 := unwrapped_fields1300[3].([]*pb.Attribute)
		if field1304 != nil {
			p.newline()
			opt_val1305 := field1304
			p.pretty_attrs(opt_val1305)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1315 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1315 != nil {
		p.write(*flat1315)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1717 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1313 := _t1717
		if deconstruct_result1313 != nil {
			unwrapped1314 := deconstruct_result1313
			p.pretty_or_monoid(unwrapped1314)
		} else {
			_dollar_dollar := msg
			var _t1718 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1718 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1311 := _t1718
			if deconstruct_result1311 != nil {
				unwrapped1312 := deconstruct_result1311
				p.pretty_min_monoid(unwrapped1312)
			} else {
				_dollar_dollar := msg
				var _t1719 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1719 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1309 := _t1719
				if deconstruct_result1309 != nil {
					unwrapped1310 := deconstruct_result1309
					p.pretty_max_monoid(unwrapped1310)
				} else {
					_dollar_dollar := msg
					var _t1720 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1720 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1307 := _t1720
					if deconstruct_result1307 != nil {
						unwrapped1308 := deconstruct_result1307
						p.pretty_sum_monoid(unwrapped1308)
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
	fields1316 := msg
	_ = fields1316
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1319 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1319 != nil {
		p.write(*flat1319)
		return nil
	} else {
		_dollar_dollar := msg
		fields1317 := _dollar_dollar.GetType()
		unwrapped_fields1318 := fields1317
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1318)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1322 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		fields1320 := _dollar_dollar.GetType()
		unwrapped_fields1321 := fields1320
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1321)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1325 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1325 != nil {
		p.write(*flat1325)
		return nil
	} else {
		_dollar_dollar := msg
		fields1323 := _dollar_dollar.GetType()
		unwrapped_fields1324 := fields1323
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1324)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1333 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1333 != nil {
		p.write(*flat1333)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1721 = _dollar_dollar.GetAttrs()
		}
		fields1326 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1721}
		unwrapped_fields1327 := fields1326
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1328 := unwrapped_fields1327[0].(*pb.Monoid)
		p.pretty_monoid(field1328)
		p.newline()
		field1329 := unwrapped_fields1327[1].(*pb.RelationId)
		p.pretty_relation_id(field1329)
		p.newline()
		field1330 := unwrapped_fields1327[2].([]interface{})
		p.pretty_abstraction_with_arity(field1330)
		field1331 := unwrapped_fields1327[3].([]*pb.Attribute)
		if field1331 != nil {
			p.newline()
			opt_val1332 := field1331
			p.pretty_attrs(opt_val1332)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1340 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1340 != nil {
		p.write(*flat1340)
		return nil
	} else {
		_dollar_dollar := msg
		fields1334 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1335 := fields1334
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1336 := unwrapped_fields1335[0].(*pb.RelationId)
		p.pretty_relation_id(field1336)
		p.newline()
		field1337 := unwrapped_fields1335[1].(*pb.Abstraction)
		p.pretty_abstraction(field1337)
		p.newline()
		field1338 := unwrapped_fields1335[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1338)
		p.newline()
		field1339 := unwrapped_fields1335[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1339)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1344 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1344 != nil {
		p.write(*flat1344)
		return nil
	} else {
		fields1341 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1341) == 0) {
			p.newline()
			for i1343, elem1342 := range fields1341 {
				if (i1343 > 0) {
					p.newline()
				}
				p.pretty_var(elem1342)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1348 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1348 != nil {
		p.write(*flat1348)
		return nil
	} else {
		fields1345 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1345) == 0) {
			p.newline()
			for i1347, elem1346 := range fields1345 {
				if (i1347 > 0) {
					p.newline()
				}
				p.pretty_var(elem1346)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1357 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1722 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1722 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1355 := _t1722
		if deconstruct_result1355 != nil {
			unwrapped1356 := deconstruct_result1355
			p.pretty_edb(unwrapped1356)
		} else {
			_dollar_dollar := msg
			var _t1723 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1723 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1353 := _t1723
			if deconstruct_result1353 != nil {
				unwrapped1354 := deconstruct_result1353
				p.pretty_betree_relation(unwrapped1354)
			} else {
				_dollar_dollar := msg
				var _t1724 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1724 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1351 := _t1724
				if deconstruct_result1351 != nil {
					unwrapped1352 := deconstruct_result1351
					p.pretty_csv_data(unwrapped1352)
				} else {
					_dollar_dollar := msg
					var _t1725 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1725 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1349 := _t1725
					if deconstruct_result1349 != nil {
						unwrapped1350 := deconstruct_result1349
						p.pretty_iceberg_data(unwrapped1350)
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
	flat1363 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1363 != nil {
		p.write(*flat1363)
		return nil
	} else {
		_dollar_dollar := msg
		fields1358 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1359 := fields1358
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1360 := unwrapped_fields1359[0].(*pb.RelationId)
		p.pretty_relation_id(field1360)
		p.newline()
		field1361 := unwrapped_fields1359[1].([]string)
		p.pretty_edb_path(field1361)
		p.newline()
		field1362 := unwrapped_fields1359[2].([]*pb.Type)
		p.pretty_edb_types(field1362)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1367 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1367 != nil {
		p.write(*flat1367)
		return nil
	} else {
		fields1364 := msg
		p.write("[")
		p.indent()
		for i1366, elem1365 := range fields1364 {
			if (i1366 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1365))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		fields1368 := msg
		p.write("[")
		p.indent()
		for i1370, elem1369 := range fields1368 {
			if (i1370 > 0) {
				p.newline()
			}
			p.pretty_type(elem1369)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		fields1372 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1374 := unwrapped_fields1373[0].(*pb.RelationId)
		p.pretty_relation_id(field1374)
		p.newline()
		field1375 := unwrapped_fields1373[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1375)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		_dollar_dollar := msg
		_t1726 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1377 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1726}
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1379 := unwrapped_fields1378[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1379)
		p.newline()
		field1380 := unwrapped_fields1378[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1380)
		p.newline()
		field1381 := unwrapped_fields1378[2].([][]interface{})
		p.pretty_config_dict(field1381)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1386 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1386 != nil {
		p.write(*flat1386)
		return nil
	} else {
		fields1383 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1383) == 0) {
			p.newline()
			for i1385, elem1384 := range fields1383 {
				if (i1385 > 0) {
					p.newline()
				}
				p.pretty_type(elem1384)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1390 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1390 != nil {
		p.write(*flat1390)
		return nil
	} else {
		fields1387 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1387) == 0) {
			p.newline()
			for i1389, elem1388 := range fields1387 {
				if (i1389 > 0) {
					p.newline()
				}
				p.pretty_type(elem1388)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1397 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1397 != nil {
		p.write(*flat1397)
		return nil
	} else {
		_dollar_dollar := msg
		fields1391 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1392 := fields1391
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1393 := unwrapped_fields1392[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1393)
		p.newline()
		field1394 := unwrapped_fields1392[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1394)
		p.newline()
		field1395 := unwrapped_fields1392[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1395)
		p.newline()
		field1396 := unwrapped_fields1392[3].(string)
		p.pretty_csv_asof(field1396)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1404 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1404 != nil {
		p.write(*flat1404)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1727 = _dollar_dollar.GetPaths()
		}
		var _t1728 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1728 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1398 := []interface{}{_t1727, _t1728}
		unwrapped_fields1399 := fields1398
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1400 := unwrapped_fields1399[0].([]string)
		if field1400 != nil {
			p.newline()
			opt_val1401 := field1400
			p.pretty_csv_locator_paths(opt_val1401)
		}
		field1402 := unwrapped_fields1399[1].(*string)
		if field1402 != nil {
			p.newline()
			opt_val1403 := *field1402
			p.pretty_csv_locator_inline_data(opt_val1403)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1408 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1408 != nil {
		p.write(*flat1408)
		return nil
	} else {
		fields1405 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1405) == 0) {
			p.newline()
			for i1407, elem1406 := range fields1405 {
				if (i1407 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1406))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		fields1409 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1409))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		_dollar_dollar := msg
		_t1729 := p.deconstruct_csv_config(_dollar_dollar)
		fields1411 := _t1729
		unwrapped_fields1412 := fields1411
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1412)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		fields1414 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1414) == 0) {
			p.newline()
			for i1416, elem1415 := range fields1414 {
				if (i1416 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1415)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1426 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1730 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1730 = _dollar_dollar.GetTargetId()
		}
		fields1418 := []interface{}{_dollar_dollar.GetColumnPath(), _t1730, _dollar_dollar.GetTypes()}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1420 := unwrapped_fields1419[0].([]string)
		p.pretty_gnf_column_path(field1420)
		field1421 := unwrapped_fields1419[1].(*pb.RelationId)
		if field1421 != nil {
			p.newline()
			opt_val1422 := field1421
			p.pretty_relation_id(opt_val1422)
		}
		p.newline()
		p.write("[")
		field1423 := unwrapped_fields1419[2].([]*pb.Type)
		for i1425, elem1424 := range field1423 {
			if (i1425 > 0) {
				p.newline()
			}
			p.pretty_type(elem1424)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1433 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1433 != nil {
		p.write(*flat1433)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1731 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1431 := _t1731
		if deconstruct_result1431 != nil {
			unwrapped1432 := *deconstruct_result1431
			p.write(p.formatStringValue(unwrapped1432))
		} else {
			_dollar_dollar := msg
			var _t1732 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1732 = _dollar_dollar
			}
			deconstruct_result1427 := _t1732
			if deconstruct_result1427 != nil {
				unwrapped1428 := deconstruct_result1427
				p.write("[")
				p.indent()
				for i1430, elem1429 := range unwrapped1428 {
					if (i1430 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1429))
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
	flat1435 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1435 != nil {
		p.write(*flat1435)
		return nil
	} else {
		fields1434 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1434))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1733 []*pb.GNFColumn
		if !(len(_dollar_dollar.GetColumns()) == 0) {
			_t1733 = _dollar_dollar.GetColumns()
		}
		var _t1734 *pb.IcebergTarget
		if hasProtoField(_dollar_dollar, "target") {
			_t1734 = _dollar_dollar.GetTarget()
		}
		_t1735 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1736 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1436 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1733, _t1734, _t1735, _t1736, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1437 := fields1436
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1438 := unwrapped_fields1437[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1438)
		p.newline()
		field1439 := unwrapped_fields1437[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1439)
		field1440 := unwrapped_fields1437[2].([]*pb.GNFColumn)
		if field1440 != nil {
			p.newline()
			opt_val1441 := field1440
			p.pretty_gnf_columns(opt_val1441)
		}
		field1442 := unwrapped_fields1437[3].(*pb.IcebergTarget)
		if field1442 != nil {
			p.newline()
			opt_val1443 := field1442
			p.pretty_full_table(opt_val1443)
		}
		field1444 := unwrapped_fields1437[4].(*string)
		if field1444 != nil {
			p.newline()
			opt_val1445 := *field1444
			p.pretty_iceberg_from_snapshot(opt_val1445)
		}
		field1446 := unwrapped_fields1437[5].(*string)
		if field1446 != nil {
			p.newline()
			opt_val1447 := *field1446
			p.pretty_iceberg_to_snapshot(opt_val1447)
		}
		p.newline()
		field1448 := unwrapped_fields1437[6].(bool)
		p.pretty_boolean_value(field1448)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1455 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1455 != nil {
		p.write(*flat1455)
		return nil
	} else {
		_dollar_dollar := msg
		fields1450 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1451 := fields1450
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1452 := unwrapped_fields1451[0].(string)
		p.pretty_iceberg_locator_table_name(field1452)
		p.newline()
		field1453 := unwrapped_fields1451[1].([]string)
		p.pretty_iceberg_locator_namespace(field1453)
		p.newline()
		field1454 := unwrapped_fields1451[2].(string)
		p.pretty_iceberg_locator_warehouse(field1454)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		fields1456 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1456))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1461 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1461 != nil {
		p.write(*flat1461)
		return nil
	} else {
		fields1458 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1458) == 0) {
			p.newline()
			for i1460, elem1459 := range fields1458 {
				if (i1460 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1459))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1463 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1463 != nil {
		p.write(*flat1463)
		return nil
	} else {
		fields1462 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1462))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1471 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		_dollar_dollar := msg
		_t1737 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1464 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1737, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1465 := fields1464
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1466 := unwrapped_fields1465[0].(string)
		p.pretty_iceberg_catalog_uri(field1466)
		field1467 := unwrapped_fields1465[1].(*string)
		if field1467 != nil {
			p.newline()
			opt_val1468 := *field1467
			p.pretty_iceberg_catalog_config_scope(opt_val1468)
		}
		p.newline()
		field1469 := unwrapped_fields1465[2].([][]interface{})
		p.pretty_iceberg_properties(field1469)
		p.newline()
		field1470 := unwrapped_fields1465[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1470)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1473 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1473 != nil {
		p.write(*flat1473)
		return nil
	} else {
		fields1472 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1472))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1475 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1475 != nil {
		p.write(*flat1475)
		return nil
	} else {
		fields1474 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1474))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1479 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1479 != nil {
		p.write(*flat1479)
		return nil
	} else {
		fields1476 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1476) == 0) {
			p.newline()
			for i1478, elem1477 := range fields1476 {
				if (i1478 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1477)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		_dollar_dollar := msg
		fields1480 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1481 := fields1480
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1482 := unwrapped_fields1481[0].(string)
		p.write(p.formatStringValue(field1482))
		p.newline()
		field1483 := unwrapped_fields1481[1].(string)
		p.write(p.formatStringValue(field1483))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1485) == 0) {
			p.newline()
			for i1487, elem1486 := range fields1485 {
				if (i1487 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1486)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1493 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1493 != nil {
		p.write(*flat1493)
		return nil
	} else {
		_dollar_dollar := msg
		_t1738 := p.mask_secret_value(_dollar_dollar)
		fields1489 := []interface{}{_dollar_dollar[0].(string), _t1738}
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

func (p *PrettyPrinter) pretty_full_table(msg *pb.IcebergTarget) interface{} {
	flat1500 := p.tryFlat(msg, func() { p.pretty_full_table(msg) })
	if flat1500 != nil {
		p.write(*flat1500)
		return nil
	} else {
		_dollar_dollar := msg
		fields1494 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
		unwrapped_fields1495 := fields1494
		p.write("(")
		p.write("full_table")
		p.indentSexp()
		p.newline()
		field1496 := unwrapped_fields1495[0].(*pb.RelationId)
		p.pretty_relation_id(field1496)
		p.newline()
		p.write("[")
		field1497 := unwrapped_fields1495[1].([]*pb.Type)
		for i1499, elem1498 := range field1497 {
			if (i1499 > 0) {
				p.newline()
			}
			p.pretty_type(elem1498)
		}
		p.write("]")
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
	flat1539 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1539 != nil {
		p.write(*flat1539)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1739 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1739 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1537 := _t1739
		if deconstruct_result1537 != nil {
			unwrapped1538 := deconstruct_result1537
			p.pretty_demand(unwrapped1538)
		} else {
			_dollar_dollar := msg
			var _t1740 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1740 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1535 := _t1740
			if deconstruct_result1535 != nil {
				unwrapped1536 := deconstruct_result1535
				p.pretty_output(unwrapped1536)
			} else {
				_dollar_dollar := msg
				var _t1741 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1741 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1533 := _t1741
				if deconstruct_result1533 != nil {
					unwrapped1534 := deconstruct_result1533
					p.pretty_what_if(unwrapped1534)
				} else {
					_dollar_dollar := msg
					var _t1742 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1742 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1531 := _t1742
					if deconstruct_result1531 != nil {
						unwrapped1532 := deconstruct_result1531
						p.pretty_abort(unwrapped1532)
					} else {
						_dollar_dollar := msg
						var _t1743 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1743 = _dollar_dollar.GetExport()
						}
						deconstruct_result1529 := _t1743
						if deconstruct_result1529 != nil {
							unwrapped1530 := deconstruct_result1529
							p.pretty_export(unwrapped1530)
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
	flat1542 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1542 != nil {
		p.write(*flat1542)
		return nil
	} else {
		_dollar_dollar := msg
		fields1540 := _dollar_dollar.GetRelationId()
		unwrapped_fields1541 := fields1540
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1541)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1547 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1547 != nil {
		p.write(*flat1547)
		return nil
	} else {
		_dollar_dollar := msg
		fields1543 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1544 := fields1543
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1545 := unwrapped_fields1544[0].(string)
		p.pretty_name(field1545)
		p.newline()
		field1546 := unwrapped_fields1544[1].(*pb.RelationId)
		p.pretty_relation_id(field1546)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1552 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1552 != nil {
		p.write(*flat1552)
		return nil
	} else {
		_dollar_dollar := msg
		fields1548 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1549 := fields1548
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1550 := unwrapped_fields1549[0].(string)
		p.pretty_name(field1550)
		p.newline()
		field1551 := unwrapped_fields1549[1].(*pb.Epoch)
		p.pretty_epoch(field1551)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1558 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1558 != nil {
		p.write(*flat1558)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1744 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1744 = ptr(_dollar_dollar.GetName())
		}
		fields1553 := []interface{}{_t1744, _dollar_dollar.GetRelationId()}
		unwrapped_fields1554 := fields1553
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1555 := unwrapped_fields1554[0].(*string)
		if field1555 != nil {
			p.newline()
			opt_val1556 := *field1555
			p.pretty_name(opt_val1556)
		}
		p.newline()
		field1557 := unwrapped_fields1554[1].(*pb.RelationId)
		p.pretty_relation_id(field1557)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1563 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1563 != nil {
		p.write(*flat1563)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1745 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1745 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1561 := _t1745
		if deconstruct_result1561 != nil {
			unwrapped1562 := deconstruct_result1561
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1562)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1746 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1746 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1559 := _t1746
			if deconstruct_result1559 != nil {
				unwrapped1560 := deconstruct_result1559
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1560)
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
	flat1574 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1574 != nil {
		p.write(*flat1574)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1747 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1747 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1569 := _t1747
		if deconstruct_result1569 != nil {
			unwrapped1570 := deconstruct_result1569
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1571 := unwrapped1570[0].(string)
			p.pretty_export_csv_path(field1571)
			p.newline()
			field1572 := unwrapped1570[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1572)
			p.newline()
			field1573 := unwrapped1570[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1573)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1748 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1749 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1748 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1749}
			}
			deconstruct_result1564 := _t1748
			if deconstruct_result1564 != nil {
				unwrapped1565 := deconstruct_result1564
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1566 := unwrapped1565[0].(string)
				p.pretty_export_csv_path(field1566)
				p.newline()
				field1567 := unwrapped1565[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1567)
				p.newline()
				field1568 := unwrapped1565[2].([][]interface{})
				p.pretty_config_dict(field1568)
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
	flat1576 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1576 != nil {
		p.write(*flat1576)
		return nil
	} else {
		fields1575 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1575))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1583 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1583 != nil {
		p.write(*flat1583)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1750 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1750 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1579 := _t1750
		if deconstruct_result1579 != nil {
			unwrapped1580 := deconstruct_result1579
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1580) == 0) {
				p.newline()
				for i1582, elem1581 := range unwrapped1580 {
					if (i1582 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1581)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1751 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1751 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1577 := _t1751
			if deconstruct_result1577 != nil {
				unwrapped1578 := deconstruct_result1577
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1578)
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
	flat1588 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1588 != nil {
		p.write(*flat1588)
		return nil
	} else {
		_dollar_dollar := msg
		fields1584 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1585 := fields1584
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1586 := unwrapped_fields1585[0].(string)
		p.write(p.formatStringValue(field1586))
		p.newline()
		field1587 := unwrapped_fields1585[1].(*pb.RelationId)
		p.pretty_relation_id(field1587)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1592 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1592 != nil {
		p.write(*flat1592)
		return nil
	} else {
		fields1589 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1589) == 0) {
			p.newline()
			for i1591, elem1590 := range fields1589 {
				if (i1591 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1590)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1601 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1601 != nil {
		p.write(*flat1601)
		return nil
	} else {
		_dollar_dollar := msg
		_t1752 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1593 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1752}
		unwrapped_fields1594 := fields1593
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1595 := unwrapped_fields1594[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1595)
		p.newline()
		field1596 := unwrapped_fields1594[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1596)
		p.newline()
		field1597 := unwrapped_fields1594[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1597)
		p.newline()
		field1598 := unwrapped_fields1594[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1598)
		field1599 := unwrapped_fields1594[4].([][]interface{})
		if field1599 != nil {
			p.newline()
			opt_val1600 := field1599
			p.pretty_config_dict(opt_val1600)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1603 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1603 != nil {
		p.write(*flat1603)
		return nil
	} else {
		fields1602 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1602)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1607 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1607 != nil {
		p.write(*flat1607)
		return nil
	} else {
		fields1604 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1604) == 0) {
			p.newline()
			for i1606, elem1605 := range fields1604 {
				if (i1606 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1605)
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
		_t1798 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1798)
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
	case *pb.IcebergTarget:
		p.pretty_full_table(m)
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
