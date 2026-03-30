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
	_t1701 := &pb.Value{}
	_t1701.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1701
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1702 := &pb.Value{}
	_t1702.Value = &pb.Value_IntValue{IntValue: v}
	return _t1702
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1703 := &pb.Value{}
	_t1703.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1703
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1704 := &pb.Value{}
	_t1704.Value = &pb.Value_StringValue{StringValue: v}
	return _t1704
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1705 := &pb.Value{}
	_t1705.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1705
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1706 := &pb.Value{}
	_t1706.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1706
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1707 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1707})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1708 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1708})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1709 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1709})
			}
		}
	}
	_t1710 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1710})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1711 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1711})
	_t1712 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1712})
	if msg.GetNewLine() != "" {
		_t1713 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1713})
	}
	_t1714 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1714})
	_t1715 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1715})
	_t1716 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1716})
	if msg.GetComment() != "" {
		_t1717 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1717})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1718 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1718})
	}
	_t1719 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1719})
	_t1720 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1720})
	_t1721 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1721})
	if msg.GetPartitionSizeMb() != 0 {
		_t1722 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1722})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1723 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1723})
	_t1724 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1724})
	_t1725 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1725})
	_t1726 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1726})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1727 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1727})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1728 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1728})
		}
	}
	_t1729 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1729})
	_t1730 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1730})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1731 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1731})
	}
	if msg.Compression != nil {
		_t1732 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1732})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1733 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1733})
	}
	if msg.SyntaxMissingString != nil {
		_t1734 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1734})
	}
	if msg.SyntaxDelim != nil {
		_t1735 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1735})
	}
	if msg.SyntaxQuotechar != nil {
		_t1736 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1736})
	}
	if msg.SyntaxEscapechar != nil {
		_t1737 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1737})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1738 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1738
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_locator_from_snapshot_optional(msg *pb.IcebergLocator) *string {
	var _t1739 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1739
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_locator_to_snapshot_optional(msg *pb.IcebergLocator) *string {
	var _t1740 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1740
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1741 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1741})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1742 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1742})
	}
	if msg.GetCompression() != "" {
		_t1743 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1743})
	}
	var _t1744 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1744
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1745 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1745
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
	flat789 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat789 != nil {
		p.write(*flat789)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1560 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1560 = _dollar_dollar.GetConfigure()
		}
		var _t1561 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1561 = _dollar_dollar.GetSync()
		}
		fields780 := []interface{}{_t1560, _t1561, _dollar_dollar.GetEpochs()}
		unwrapped_fields781 := fields780
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field782 := unwrapped_fields781[0].(*pb.Configure)
		if field782 != nil {
			p.newline()
			opt_val783 := field782
			p.pretty_configure(opt_val783)
		}
		field784 := unwrapped_fields781[1].(*pb.Sync)
		if field784 != nil {
			p.newline()
			opt_val785 := field784
			p.pretty_sync(opt_val785)
		}
		field786 := unwrapped_fields781[2].([]*pb.Epoch)
		if !(len(field786) == 0) {
			p.newline()
			for i788, elem787 := range field786 {
				if (i788 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem787)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat792 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat792 != nil {
		p.write(*flat792)
		return nil
	} else {
		_dollar_dollar := msg
		_t1562 := p.deconstruct_configure(_dollar_dollar)
		fields790 := _t1562
		unwrapped_fields791 := fields790
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields791)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat796 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat796 != nil {
		p.write(*flat796)
		return nil
	} else {
		fields793 := msg
		p.write("{")
		p.indent()
		if !(len(fields793) == 0) {
			p.newline()
			for i795, elem794 := range fields793 {
				if (i795 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem794)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat801 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat801 != nil {
		p.write(*flat801)
		return nil
	} else {
		_dollar_dollar := msg
		fields797 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields798 := fields797
		p.write(":")
		field799 := unwrapped_fields798[0].(string)
		p.write(field799)
		p.write(" ")
		field800 := unwrapped_fields798[1].(*pb.Value)
		p.pretty_raw_value(field800)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat827 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat827 != nil {
		p.write(*flat827)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1563 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1563 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result825 := _t1563
		if deconstruct_result825 != nil {
			unwrapped826 := deconstruct_result825
			p.pretty_raw_date(unwrapped826)
		} else {
			_dollar_dollar := msg
			var _t1564 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1564 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result823 := _t1564
			if deconstruct_result823 != nil {
				unwrapped824 := deconstruct_result823
				p.pretty_raw_datetime(unwrapped824)
			} else {
				_dollar_dollar := msg
				var _t1565 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1565 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result821 := _t1565
				if deconstruct_result821 != nil {
					unwrapped822 := *deconstruct_result821
					p.write(p.formatStringValue(unwrapped822))
				} else {
					_dollar_dollar := msg
					var _t1566 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1566 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result819 := _t1566
					if deconstruct_result819 != nil {
						unwrapped820 := *deconstruct_result819
						p.write(fmt.Sprintf("%di32", unwrapped820))
					} else {
						_dollar_dollar := msg
						var _t1567 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1567 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result817 := _t1567
						if deconstruct_result817 != nil {
							unwrapped818 := *deconstruct_result817
							p.write(fmt.Sprintf("%d", unwrapped818))
						} else {
							_dollar_dollar := msg
							var _t1568 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1568 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result815 := _t1568
							if deconstruct_result815 != nil {
								unwrapped816 := *deconstruct_result815
								p.write(formatFloat32(unwrapped816))
							} else {
								_dollar_dollar := msg
								var _t1569 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1569 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result813 := _t1569
								if deconstruct_result813 != nil {
									unwrapped814 := *deconstruct_result813
									p.write(formatFloat64(unwrapped814))
								} else {
									_dollar_dollar := msg
									var _t1570 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1570 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result811 := _t1570
									if deconstruct_result811 != nil {
										unwrapped812 := *deconstruct_result811
										p.write(fmt.Sprintf("%du32", unwrapped812))
									} else {
										_dollar_dollar := msg
										var _t1571 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1571 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result809 := _t1571
										if deconstruct_result809 != nil {
											unwrapped810 := deconstruct_result809
											p.write(p.formatUint128(unwrapped810))
										} else {
											_dollar_dollar := msg
											var _t1572 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1572 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result807 := _t1572
											if deconstruct_result807 != nil {
												unwrapped808 := deconstruct_result807
												p.write(p.formatInt128(unwrapped808))
											} else {
												_dollar_dollar := msg
												var _t1573 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1573 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result805 := _t1573
												if deconstruct_result805 != nil {
													unwrapped806 := deconstruct_result805
													p.write(p.formatDecimal(unwrapped806))
												} else {
													_dollar_dollar := msg
													var _t1574 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1574 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result803 := _t1574
													if deconstruct_result803 != nil {
														unwrapped804 := *deconstruct_result803
														p.pretty_boolean_value(unwrapped804)
													} else {
														fields802 := msg
														_ = fields802
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
	flat833 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat833 != nil {
		p.write(*flat833)
		return nil
	} else {
		_dollar_dollar := msg
		fields828 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields829 := fields828
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field830 := unwrapped_fields829[0].(int64)
		p.write(fmt.Sprintf("%d", field830))
		p.newline()
		field831 := unwrapped_fields829[1].(int64)
		p.write(fmt.Sprintf("%d", field831))
		p.newline()
		field832 := unwrapped_fields829[2].(int64)
		p.write(fmt.Sprintf("%d", field832))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat844 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat844 != nil {
		p.write(*flat844)
		return nil
	} else {
		_dollar_dollar := msg
		fields834 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields835 := fields834
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field836 := unwrapped_fields835[0].(int64)
		p.write(fmt.Sprintf("%d", field836))
		p.newline()
		field837 := unwrapped_fields835[1].(int64)
		p.write(fmt.Sprintf("%d", field837))
		p.newline()
		field838 := unwrapped_fields835[2].(int64)
		p.write(fmt.Sprintf("%d", field838))
		p.newline()
		field839 := unwrapped_fields835[3].(int64)
		p.write(fmt.Sprintf("%d", field839))
		p.newline()
		field840 := unwrapped_fields835[4].(int64)
		p.write(fmt.Sprintf("%d", field840))
		p.newline()
		field841 := unwrapped_fields835[5].(int64)
		p.write(fmt.Sprintf("%d", field841))
		field842 := unwrapped_fields835[6].(*int64)
		if field842 != nil {
			p.newline()
			opt_val843 := *field842
			p.write(fmt.Sprintf("%d", opt_val843))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1575 []interface{}
	if _dollar_dollar {
		_t1575 = []interface{}{}
	}
	deconstruct_result847 := _t1575
	if deconstruct_result847 != nil {
		unwrapped848 := deconstruct_result847
		_ = unwrapped848
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1576 []interface{}
		if !(_dollar_dollar) {
			_t1576 = []interface{}{}
		}
		deconstruct_result845 := _t1576
		if deconstruct_result845 != nil {
			unwrapped846 := deconstruct_result845
			_ = unwrapped846
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat853 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat853 != nil {
		p.write(*flat853)
		return nil
	} else {
		_dollar_dollar := msg
		fields849 := _dollar_dollar.GetFragments()
		unwrapped_fields850 := fields849
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields850) == 0) {
			p.newline()
			for i852, elem851 := range unwrapped_fields850 {
				if (i852 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem851)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat856 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat856 != nil {
		p.write(*flat856)
		return nil
	} else {
		_dollar_dollar := msg
		fields854 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields855 := fields854
		p.write(":")
		p.write(unwrapped_fields855)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1577 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1577 = _dollar_dollar.GetWrites()
		}
		var _t1578 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1578 = _dollar_dollar.GetReads()
		}
		fields857 := []interface{}{_t1577, _t1578}
		unwrapped_fields858 := fields857
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field859 := unwrapped_fields858[0].([]*pb.Write)
		if field859 != nil {
			p.newline()
			opt_val860 := field859
			p.pretty_epoch_writes(opt_val860)
		}
		field861 := unwrapped_fields858[1].([]*pb.Read)
		if field861 != nil {
			p.newline()
			opt_val862 := field861
			p.pretty_epoch_reads(opt_val862)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat867 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat867 != nil {
		p.write(*flat867)
		return nil
	} else {
		fields864 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields864) == 0) {
			p.newline()
			for i866, elem865 := range fields864 {
				if (i866 > 0) {
					p.newline()
				}
				p.pretty_write(elem865)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat876 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1579 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1579 = _dollar_dollar.GetDefine()
		}
		deconstruct_result874 := _t1579
		if deconstruct_result874 != nil {
			unwrapped875 := deconstruct_result874
			p.pretty_define(unwrapped875)
		} else {
			_dollar_dollar := msg
			var _t1580 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1580 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result872 := _t1580
			if deconstruct_result872 != nil {
				unwrapped873 := deconstruct_result872
				p.pretty_undefine(unwrapped873)
			} else {
				_dollar_dollar := msg
				var _t1581 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1581 = _dollar_dollar.GetContext()
				}
				deconstruct_result870 := _t1581
				if deconstruct_result870 != nil {
					unwrapped871 := deconstruct_result870
					p.pretty_context(unwrapped871)
				} else {
					_dollar_dollar := msg
					var _t1582 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1582 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result868 := _t1582
					if deconstruct_result868 != nil {
						unwrapped869 := deconstruct_result868
						p.pretty_snapshot(unwrapped869)
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
	flat879 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat879 != nil {
		p.write(*flat879)
		return nil
	} else {
		_dollar_dollar := msg
		fields877 := _dollar_dollar.GetFragment()
		unwrapped_fields878 := fields877
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields878)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat886 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat886 != nil {
		p.write(*flat886)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields880 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields881 := fields880
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field882 := unwrapped_fields881[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field882)
		field883 := unwrapped_fields881[1].([]*pb.Declaration)
		if !(len(field883) == 0) {
			p.newline()
			for i885, elem884 := range field883 {
				if (i885 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem884)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat888 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat888 != nil {
		p.write(*flat888)
		return nil
	} else {
		fields887 := msg
		p.pretty_fragment_id(fields887)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat897 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat897 != nil {
		p.write(*flat897)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1583 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1583 = _dollar_dollar.GetDef()
		}
		deconstruct_result895 := _t1583
		if deconstruct_result895 != nil {
			unwrapped896 := deconstruct_result895
			p.pretty_def(unwrapped896)
		} else {
			_dollar_dollar := msg
			var _t1584 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1584 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result893 := _t1584
			if deconstruct_result893 != nil {
				unwrapped894 := deconstruct_result893
				p.pretty_algorithm(unwrapped894)
			} else {
				_dollar_dollar := msg
				var _t1585 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1585 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result891 := _t1585
				if deconstruct_result891 != nil {
					unwrapped892 := deconstruct_result891
					p.pretty_constraint(unwrapped892)
				} else {
					_dollar_dollar := msg
					var _t1586 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1586 = _dollar_dollar.GetData()
					}
					deconstruct_result889 := _t1586
					if deconstruct_result889 != nil {
						unwrapped890 := deconstruct_result889
						p.pretty_data(unwrapped890)
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
	flat904 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1587 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1587 = _dollar_dollar.GetAttrs()
		}
		fields898 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1587}
		unwrapped_fields899 := fields898
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field900 := unwrapped_fields899[0].(*pb.RelationId)
		p.pretty_relation_id(field900)
		p.newline()
		field901 := unwrapped_fields899[1].(*pb.Abstraction)
		p.pretty_abstraction(field901)
		field902 := unwrapped_fields899[2].([]*pb.Attribute)
		if field902 != nil {
			p.newline()
			opt_val903 := field902
			p.pretty_attrs(opt_val903)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat909 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat909 != nil {
		p.write(*flat909)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1588 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1589 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1588 = ptr(_t1589)
		}
		deconstruct_result907 := _t1588
		if deconstruct_result907 != nil {
			unwrapped908 := *deconstruct_result907
			p.write(":")
			p.write(unwrapped908)
		} else {
			_dollar_dollar := msg
			_t1590 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result905 := _t1590
			if deconstruct_result905 != nil {
				unwrapped906 := deconstruct_result905
				p.write(p.formatUint128(unwrapped906))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat914 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat914 != nil {
		p.write(*flat914)
		return nil
	} else {
		_dollar_dollar := msg
		_t1591 := p.deconstruct_bindings(_dollar_dollar)
		fields910 := []interface{}{_t1591, _dollar_dollar.GetValue()}
		unwrapped_fields911 := fields910
		p.write("(")
		p.indent()
		field912 := unwrapped_fields911[0].([]interface{})
		p.pretty_bindings(field912)
		p.newline()
		field913 := unwrapped_fields911[1].(*pb.Formula)
		p.pretty_formula(field913)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat922 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat922 != nil {
		p.write(*flat922)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1592 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1592 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields915 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1592}
		unwrapped_fields916 := fields915
		p.write("[")
		p.indent()
		field917 := unwrapped_fields916[0].([]*pb.Binding)
		for i919, elem918 := range field917 {
			if (i919 > 0) {
				p.newline()
			}
			p.pretty_binding(elem918)
		}
		field920 := unwrapped_fields916[1].([]*pb.Binding)
		if field920 != nil {
			p.newline()
			opt_val921 := field920
			p.pretty_value_bindings(opt_val921)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat927 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat927 != nil {
		p.write(*flat927)
		return nil
	} else {
		_dollar_dollar := msg
		fields923 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields924 := fields923
		field925 := unwrapped_fields924[0].(string)
		p.write(field925)
		p.write("::")
		field926 := unwrapped_fields924[1].(*pb.Type)
		p.pretty_type(field926)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat956 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat956 != nil {
		p.write(*flat956)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1593 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1593 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result954 := _t1593
		if deconstruct_result954 != nil {
			unwrapped955 := deconstruct_result954
			p.pretty_unspecified_type(unwrapped955)
		} else {
			_dollar_dollar := msg
			var _t1594 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1594 = _dollar_dollar.GetStringType()
			}
			deconstruct_result952 := _t1594
			if deconstruct_result952 != nil {
				unwrapped953 := deconstruct_result952
				p.pretty_string_type(unwrapped953)
			} else {
				_dollar_dollar := msg
				var _t1595 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1595 = _dollar_dollar.GetIntType()
				}
				deconstruct_result950 := _t1595
				if deconstruct_result950 != nil {
					unwrapped951 := deconstruct_result950
					p.pretty_int_type(unwrapped951)
				} else {
					_dollar_dollar := msg
					var _t1596 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1596 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result948 := _t1596
					if deconstruct_result948 != nil {
						unwrapped949 := deconstruct_result948
						p.pretty_float_type(unwrapped949)
					} else {
						_dollar_dollar := msg
						var _t1597 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1597 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result946 := _t1597
						if deconstruct_result946 != nil {
							unwrapped947 := deconstruct_result946
							p.pretty_uint128_type(unwrapped947)
						} else {
							_dollar_dollar := msg
							var _t1598 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1598 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result944 := _t1598
							if deconstruct_result944 != nil {
								unwrapped945 := deconstruct_result944
								p.pretty_int128_type(unwrapped945)
							} else {
								_dollar_dollar := msg
								var _t1599 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1599 = _dollar_dollar.GetDateType()
								}
								deconstruct_result942 := _t1599
								if deconstruct_result942 != nil {
									unwrapped943 := deconstruct_result942
									p.pretty_date_type(unwrapped943)
								} else {
									_dollar_dollar := msg
									var _t1600 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1600 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result940 := _t1600
									if deconstruct_result940 != nil {
										unwrapped941 := deconstruct_result940
										p.pretty_datetime_type(unwrapped941)
									} else {
										_dollar_dollar := msg
										var _t1601 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1601 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result938 := _t1601
										if deconstruct_result938 != nil {
											unwrapped939 := deconstruct_result938
											p.pretty_missing_type(unwrapped939)
										} else {
											_dollar_dollar := msg
											var _t1602 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1602 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result936 := _t1602
											if deconstruct_result936 != nil {
												unwrapped937 := deconstruct_result936
												p.pretty_decimal_type(unwrapped937)
											} else {
												_dollar_dollar := msg
												var _t1603 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1603 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result934 := _t1603
												if deconstruct_result934 != nil {
													unwrapped935 := deconstruct_result934
													p.pretty_boolean_type(unwrapped935)
												} else {
													_dollar_dollar := msg
													var _t1604 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1604 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result932 := _t1604
													if deconstruct_result932 != nil {
														unwrapped933 := deconstruct_result932
														p.pretty_int32_type(unwrapped933)
													} else {
														_dollar_dollar := msg
														var _t1605 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1605 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result930 := _t1605
														if deconstruct_result930 != nil {
															unwrapped931 := deconstruct_result930
															p.pretty_float32_type(unwrapped931)
														} else {
															_dollar_dollar := msg
															var _t1606 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1606 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result928 := _t1606
															if deconstruct_result928 != nil {
																unwrapped929 := deconstruct_result928
																p.pretty_uint32_type(unwrapped929)
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
	fields957 := msg
	_ = fields957
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields958 := msg
	_ = fields958
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields959 := msg
	_ = fields959
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields960 := msg
	_ = fields960
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields961 := msg
	_ = fields961
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields962 := msg
	_ = fields962
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields963 := msg
	_ = fields963
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields964 := msg
	_ = fields964
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields965 := msg
	_ = fields965
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat970 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat970 != nil {
		p.write(*flat970)
		return nil
	} else {
		_dollar_dollar := msg
		fields966 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields967 := fields966
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field968 := unwrapped_fields967[0].(int64)
		p.write(fmt.Sprintf("%d", field968))
		p.newline()
		field969 := unwrapped_fields967[1].(int64)
		p.write(fmt.Sprintf("%d", field969))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields971 := msg
	_ = fields971
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields972 := msg
	_ = fields972
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields973 := msg
	_ = fields973
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields974 := msg
	_ = fields974
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat978 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat978 != nil {
		p.write(*flat978)
		return nil
	} else {
		fields975 := msg
		p.write("|")
		if !(len(fields975) == 0) {
			p.write(" ")
			for i977, elem976 := range fields975 {
				if (i977 > 0) {
					p.newline()
				}
				p.pretty_binding(elem976)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1005 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1005 != nil {
		p.write(*flat1005)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1607 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1607 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1003 := _t1607
		if deconstruct_result1003 != nil {
			unwrapped1004 := deconstruct_result1003
			p.pretty_true(unwrapped1004)
		} else {
			_dollar_dollar := msg
			var _t1608 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1608 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1001 := _t1608
			if deconstruct_result1001 != nil {
				unwrapped1002 := deconstruct_result1001
				p.pretty_false(unwrapped1002)
			} else {
				_dollar_dollar := msg
				var _t1609 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1609 = _dollar_dollar.GetExists()
				}
				deconstruct_result999 := _t1609
				if deconstruct_result999 != nil {
					unwrapped1000 := deconstruct_result999
					p.pretty_exists(unwrapped1000)
				} else {
					_dollar_dollar := msg
					var _t1610 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1610 = _dollar_dollar.GetReduce()
					}
					deconstruct_result997 := _t1610
					if deconstruct_result997 != nil {
						unwrapped998 := deconstruct_result997
						p.pretty_reduce(unwrapped998)
					} else {
						_dollar_dollar := msg
						var _t1611 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1611 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result995 := _t1611
						if deconstruct_result995 != nil {
							unwrapped996 := deconstruct_result995
							p.pretty_conjunction(unwrapped996)
						} else {
							_dollar_dollar := msg
							var _t1612 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1612 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result993 := _t1612
							if deconstruct_result993 != nil {
								unwrapped994 := deconstruct_result993
								p.pretty_disjunction(unwrapped994)
							} else {
								_dollar_dollar := msg
								var _t1613 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1613 = _dollar_dollar.GetNot()
								}
								deconstruct_result991 := _t1613
								if deconstruct_result991 != nil {
									unwrapped992 := deconstruct_result991
									p.pretty_not(unwrapped992)
								} else {
									_dollar_dollar := msg
									var _t1614 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1614 = _dollar_dollar.GetFfi()
									}
									deconstruct_result989 := _t1614
									if deconstruct_result989 != nil {
										unwrapped990 := deconstruct_result989
										p.pretty_ffi(unwrapped990)
									} else {
										_dollar_dollar := msg
										var _t1615 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1615 = _dollar_dollar.GetAtom()
										}
										deconstruct_result987 := _t1615
										if deconstruct_result987 != nil {
											unwrapped988 := deconstruct_result987
											p.pretty_atom(unwrapped988)
										} else {
											_dollar_dollar := msg
											var _t1616 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1616 = _dollar_dollar.GetPragma()
											}
											deconstruct_result985 := _t1616
											if deconstruct_result985 != nil {
												unwrapped986 := deconstruct_result985
												p.pretty_pragma(unwrapped986)
											} else {
												_dollar_dollar := msg
												var _t1617 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1617 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result983 := _t1617
												if deconstruct_result983 != nil {
													unwrapped984 := deconstruct_result983
													p.pretty_primitive(unwrapped984)
												} else {
													_dollar_dollar := msg
													var _t1618 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1618 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result981 := _t1618
													if deconstruct_result981 != nil {
														unwrapped982 := deconstruct_result981
														p.pretty_rel_atom(unwrapped982)
													} else {
														_dollar_dollar := msg
														var _t1619 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1619 = _dollar_dollar.GetCast()
														}
														deconstruct_result979 := _t1619
														if deconstruct_result979 != nil {
															unwrapped980 := deconstruct_result979
															p.pretty_cast(unwrapped980)
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
	fields1006 := msg
	_ = fields1006
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1007 := msg
	_ = fields1007
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1012 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1012 != nil {
		p.write(*flat1012)
		return nil
	} else {
		_dollar_dollar := msg
		_t1620 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1008 := []interface{}{_t1620, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1009 := fields1008
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1010 := unwrapped_fields1009[0].([]interface{})
		p.pretty_bindings(field1010)
		p.newline()
		field1011 := unwrapped_fields1009[1].(*pb.Formula)
		p.pretty_formula(field1011)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1018 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1018 != nil {
		p.write(*flat1018)
		return nil
	} else {
		_dollar_dollar := msg
		fields1013 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1014 := fields1013
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1015 := unwrapped_fields1014[0].(*pb.Abstraction)
		p.pretty_abstraction(field1015)
		p.newline()
		field1016 := unwrapped_fields1014[1].(*pb.Abstraction)
		p.pretty_abstraction(field1016)
		p.newline()
		field1017 := unwrapped_fields1014[2].([]*pb.Term)
		p.pretty_terms(field1017)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1022 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1022 != nil {
		p.write(*flat1022)
		return nil
	} else {
		fields1019 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1019) == 0) {
			p.newline()
			for i1021, elem1020 := range fields1019 {
				if (i1021 > 0) {
					p.newline()
				}
				p.pretty_term(elem1020)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1027 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1027 != nil {
		p.write(*flat1027)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1621 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1621 = _dollar_dollar.GetVar()
		}
		deconstruct_result1025 := _t1621
		if deconstruct_result1025 != nil {
			unwrapped1026 := deconstruct_result1025
			p.pretty_var(unwrapped1026)
		} else {
			_dollar_dollar := msg
			var _t1622 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1622 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1023 := _t1622
			if deconstruct_result1023 != nil {
				unwrapped1024 := deconstruct_result1023
				p.pretty_value(unwrapped1024)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_dollar_dollar := msg
		fields1028 := _dollar_dollar.GetName()
		unwrapped_fields1029 := fields1028
		p.write(unwrapped_fields1029)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1056 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1056 != nil {
		p.write(*flat1056)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1623 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1623 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1054 := _t1623
		if deconstruct_result1054 != nil {
			unwrapped1055 := deconstruct_result1054
			p.pretty_date(unwrapped1055)
		} else {
			_dollar_dollar := msg
			var _t1624 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1624 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1052 := _t1624
			if deconstruct_result1052 != nil {
				unwrapped1053 := deconstruct_result1052
				p.pretty_datetime(unwrapped1053)
			} else {
				_dollar_dollar := msg
				var _t1625 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1625 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1050 := _t1625
				if deconstruct_result1050 != nil {
					unwrapped1051 := *deconstruct_result1050
					p.write(p.formatStringValue(unwrapped1051))
				} else {
					_dollar_dollar := msg
					var _t1626 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1626 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1048 := _t1626
					if deconstruct_result1048 != nil {
						unwrapped1049 := *deconstruct_result1048
						p.write(fmt.Sprintf("%di32", unwrapped1049))
					} else {
						_dollar_dollar := msg
						var _t1627 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1627 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1046 := _t1627
						if deconstruct_result1046 != nil {
							unwrapped1047 := *deconstruct_result1046
							p.write(fmt.Sprintf("%d", unwrapped1047))
						} else {
							_dollar_dollar := msg
							var _t1628 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1628 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1044 := _t1628
							if deconstruct_result1044 != nil {
								unwrapped1045 := *deconstruct_result1044
								p.write(formatFloat32(unwrapped1045))
							} else {
								_dollar_dollar := msg
								var _t1629 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1629 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1042 := _t1629
								if deconstruct_result1042 != nil {
									unwrapped1043 := *deconstruct_result1042
									p.write(formatFloat64(unwrapped1043))
								} else {
									_dollar_dollar := msg
									var _t1630 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1630 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1040 := _t1630
									if deconstruct_result1040 != nil {
										unwrapped1041 := *deconstruct_result1040
										p.write(fmt.Sprintf("%du32", unwrapped1041))
									} else {
										_dollar_dollar := msg
										var _t1631 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1631 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1038 := _t1631
										if deconstruct_result1038 != nil {
											unwrapped1039 := deconstruct_result1038
											p.write(p.formatUint128(unwrapped1039))
										} else {
											_dollar_dollar := msg
											var _t1632 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1632 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1036 := _t1632
											if deconstruct_result1036 != nil {
												unwrapped1037 := deconstruct_result1036
												p.write(p.formatInt128(unwrapped1037))
											} else {
												_dollar_dollar := msg
												var _t1633 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1633 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1034 := _t1633
												if deconstruct_result1034 != nil {
													unwrapped1035 := deconstruct_result1034
													p.write(p.formatDecimal(unwrapped1035))
												} else {
													_dollar_dollar := msg
													var _t1634 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1634 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1032 := _t1634
													if deconstruct_result1032 != nil {
														unwrapped1033 := *deconstruct_result1032
														p.pretty_boolean_value(unwrapped1033)
													} else {
														fields1031 := msg
														_ = fields1031
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
	flat1062 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_dollar_dollar := msg
		fields1057 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1058 := fields1057
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1059 := unwrapped_fields1058[0].(int64)
		p.write(fmt.Sprintf("%d", field1059))
		p.newline()
		field1060 := unwrapped_fields1058[1].(int64)
		p.write(fmt.Sprintf("%d", field1060))
		p.newline()
		field1061 := unwrapped_fields1058[2].(int64)
		p.write(fmt.Sprintf("%d", field1061))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1073 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1073 != nil {
		p.write(*flat1073)
		return nil
	} else {
		_dollar_dollar := msg
		fields1063 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1064 := fields1063
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1065 := unwrapped_fields1064[0].(int64)
		p.write(fmt.Sprintf("%d", field1065))
		p.newline()
		field1066 := unwrapped_fields1064[1].(int64)
		p.write(fmt.Sprintf("%d", field1066))
		p.newline()
		field1067 := unwrapped_fields1064[2].(int64)
		p.write(fmt.Sprintf("%d", field1067))
		p.newline()
		field1068 := unwrapped_fields1064[3].(int64)
		p.write(fmt.Sprintf("%d", field1068))
		p.newline()
		field1069 := unwrapped_fields1064[4].(int64)
		p.write(fmt.Sprintf("%d", field1069))
		p.newline()
		field1070 := unwrapped_fields1064[5].(int64)
		p.write(fmt.Sprintf("%d", field1070))
		field1071 := unwrapped_fields1064[6].(*int64)
		if field1071 != nil {
			p.newline()
			opt_val1072 := *field1071
			p.write(fmt.Sprintf("%d", opt_val1072))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1078 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1078 != nil {
		p.write(*flat1078)
		return nil
	} else {
		_dollar_dollar := msg
		fields1074 := _dollar_dollar.GetArgs()
		unwrapped_fields1075 := fields1074
		p.write("(")
		p.write("and")
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

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1083 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_dollar_dollar := msg
		fields1079 := _dollar_dollar.GetArgs()
		unwrapped_fields1080 := fields1079
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1080) == 0) {
			p.newline()
			for i1082, elem1081 := range unwrapped_fields1080 {
				if (i1082 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1081)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1086 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1086 != nil {
		p.write(*flat1086)
		return nil
	} else {
		_dollar_dollar := msg
		fields1084 := _dollar_dollar.GetArg()
		unwrapped_fields1085 := fields1084
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1085)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		fields1087 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1088 := fields1087
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1089 := unwrapped_fields1088[0].(string)
		p.pretty_name(field1089)
		p.newline()
		field1090 := unwrapped_fields1088[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1090)
		p.newline()
		field1091 := unwrapped_fields1088[2].([]*pb.Term)
		p.pretty_terms(field1091)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1094 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1094 != nil {
		p.write(*flat1094)
		return nil
	} else {
		fields1093 := msg
		p.write(":")
		p.write(fields1093)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		fields1095 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1095) == 0) {
			p.newline()
			for i1097, elem1096 := range fields1095 {
				if (i1097 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1096)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_dollar_dollar := msg
		fields1099 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1100 := fields1099
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1101 := unwrapped_fields1100[0].(*pb.RelationId)
		p.pretty_relation_id(field1101)
		field1102 := unwrapped_fields1100[1].([]*pb.Term)
		if !(len(field1102) == 0) {
			p.newline()
			for i1104, elem1103 := range field1102 {
				if (i1104 > 0) {
					p.newline()
				}
				p.pretty_term(elem1103)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		fields1106 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1107 := fields1106
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1108 := unwrapped_fields1107[0].(string)
		p.pretty_name(field1108)
		field1109 := unwrapped_fields1107[1].([]*pb.Term)
		if !(len(field1109) == 0) {
			p.newline()
			for i1111, elem1110 := range field1109 {
				if (i1111 > 0) {
					p.newline()
				}
				p.pretty_term(elem1110)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1128 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1128 != nil {
		p.write(*flat1128)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1635 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1127 := _t1635
		if guard_result1127 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1636 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1636 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1126 := _t1636
			if guard_result1126 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1637 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1637 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1125 := _t1637
				if guard_result1125 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1638 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1638 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1124 := _t1638
					if guard_result1124 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1639 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1639 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1123 := _t1639
						if guard_result1123 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1640 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1640 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1122 := _t1640
							if guard_result1122 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1641 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1641 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1121 := _t1641
								if guard_result1121 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1642 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1642 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1120 := _t1642
									if guard_result1120 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1643 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1643 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1119 := _t1643
										if guard_result1119 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1113 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1114 := fields1113
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1115 := unwrapped_fields1114[0].(string)
											p.pretty_name(field1115)
											field1116 := unwrapped_fields1114[1].([]*pb.RelTerm)
											if !(len(field1116) == 0) {
												p.newline()
												for i1118, elem1117 := range field1116 {
													if (i1118 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1117)
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
	flat1133 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1133 != nil {
		p.write(*flat1133)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1644 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1644 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1129 := _t1644
		unwrapped_fields1130 := fields1129
		p.write("(")
		p.write("=")
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

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1645 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1134 := _t1645
		unwrapped_fields1135 := fields1134
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1646 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1646 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1139 := _t1646
		unwrapped_fields1140 := fields1139
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1148 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1148 != nil {
		p.write(*flat1148)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1647 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1144 := _t1647
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write(">")
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

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1648 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1648 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1149 := _t1648
		unwrapped_fields1150 := fields1149
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1159 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1159 != nil {
		p.write(*flat1159)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1649 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1649 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1154 := _t1649
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1156 := unwrapped_fields1155[0].(*pb.Term)
		p.pretty_term(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].(*pb.Term)
		p.pretty_term(field1157)
		p.newline()
		field1158 := unwrapped_fields1155[2].(*pb.Term)
		p.pretty_term(field1158)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1650 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1650 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1160 := _t1650
		unwrapped_fields1161 := fields1160
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1162 := unwrapped_fields1161[0].(*pb.Term)
		p.pretty_term(field1162)
		p.newline()
		field1163 := unwrapped_fields1161[1].(*pb.Term)
		p.pretty_term(field1163)
		p.newline()
		field1164 := unwrapped_fields1161[2].(*pb.Term)
		p.pretty_term(field1164)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1171 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1651 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1651 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1166 := _t1651
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.Term)
		p.pretty_term(field1168)
		p.newline()
		field1169 := unwrapped_fields1167[1].(*pb.Term)
		p.pretty_term(field1169)
		p.newline()
		field1170 := unwrapped_fields1167[2].(*pb.Term)
		p.pretty_term(field1170)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1177 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1177 != nil {
		p.write(*flat1177)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1652 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1652 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1172 := _t1652
		unwrapped_fields1173 := fields1172
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1174 := unwrapped_fields1173[0].(*pb.Term)
		p.pretty_term(field1174)
		p.newline()
		field1175 := unwrapped_fields1173[1].(*pb.Term)
		p.pretty_term(field1175)
		p.newline()
		field1176 := unwrapped_fields1173[2].(*pb.Term)
		p.pretty_term(field1176)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1653 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1653 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1180 := _t1653
		if deconstruct_result1180 != nil {
			unwrapped1181 := deconstruct_result1180
			p.pretty_specialized_value(unwrapped1181)
		} else {
			_dollar_dollar := msg
			var _t1654 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1654 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1178 := _t1654
			if deconstruct_result1178 != nil {
				unwrapped1179 := deconstruct_result1178
				p.pretty_term(unwrapped1179)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		fields1183 := msg
		p.write("#")
		p.pretty_raw_value(fields1183)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1191 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1191 != nil {
		p.write(*flat1191)
		return nil
	} else {
		_dollar_dollar := msg
		fields1185 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1186 := fields1185
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1187 := unwrapped_fields1186[0].(string)
		p.pretty_name(field1187)
		field1188 := unwrapped_fields1186[1].([]*pb.RelTerm)
		if !(len(field1188) == 0) {
			p.newline()
			for i1190, elem1189 := range field1188 {
				if (i1190 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1189)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		_dollar_dollar := msg
		fields1192 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1193 := fields1192
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1194 := unwrapped_fields1193[0].(*pb.Term)
		p.pretty_term(field1194)
		p.newline()
		field1195 := unwrapped_fields1193[1].(*pb.Term)
		p.pretty_term(field1195)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		fields1197 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1197) == 0) {
			p.newline()
			for i1199, elem1198 := range fields1197 {
				if (i1199 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1198)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1207 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		_dollar_dollar := msg
		fields1201 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(string)
		p.pretty_name(field1203)
		field1204 := unwrapped_fields1202[1].([]*pb.Value)
		if !(len(field1204) == 0) {
			p.newline()
			for i1206, elem1205 := range field1204 {
				if (i1206 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1205)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_dollar_dollar := msg
		fields1208 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1209 := fields1208
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1210 := unwrapped_fields1209[0].([]*pb.RelationId)
		if !(len(field1210) == 0) {
			p.newline()
			for i1212, elem1211 := range field1210 {
				if (i1212 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1211)
			}
		}
		p.newline()
		field1213 := unwrapped_fields1209[1].(*pb.Script)
		p.pretty_script(field1213)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		_dollar_dollar := msg
		fields1215 := _dollar_dollar.GetConstructs()
		unwrapped_fields1216 := fields1215
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1216) == 0) {
			p.newline()
			for i1218, elem1217 := range unwrapped_fields1216 {
				if (i1218 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1217)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1655 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1222 := _t1655
		if deconstruct_result1222 != nil {
			unwrapped1223 := deconstruct_result1222
			p.pretty_loop(unwrapped1223)
		} else {
			_dollar_dollar := msg
			var _t1656 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1656 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1220 := _t1656
			if deconstruct_result1220 != nil {
				unwrapped1221 := deconstruct_result1220
				p.pretty_instruction(unwrapped1221)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1229 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1229 != nil {
		p.write(*flat1229)
		return nil
	} else {
		_dollar_dollar := msg
		fields1225 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1226 := fields1225
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1227 := unwrapped_fields1226[0].([]*pb.Instruction)
		p.pretty_init(field1227)
		p.newline()
		field1228 := unwrapped_fields1226[1].(*pb.Script)
		p.pretty_script(field1228)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1233 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1233 != nil {
		p.write(*flat1233)
		return nil
	} else {
		fields1230 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1230) == 0) {
			p.newline()
			for i1232, elem1231 := range fields1230 {
				if (i1232 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1231)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1657 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1657 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1242 := _t1657
		if deconstruct_result1242 != nil {
			unwrapped1243 := deconstruct_result1242
			p.pretty_assign(unwrapped1243)
		} else {
			_dollar_dollar := msg
			var _t1658 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1658 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1240 := _t1658
			if deconstruct_result1240 != nil {
				unwrapped1241 := deconstruct_result1240
				p.pretty_upsert(unwrapped1241)
			} else {
				_dollar_dollar := msg
				var _t1659 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1659 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1238 := _t1659
				if deconstruct_result1238 != nil {
					unwrapped1239 := deconstruct_result1238
					p.pretty_break(unwrapped1239)
				} else {
					_dollar_dollar := msg
					var _t1660 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1660 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1236 := _t1660
					if deconstruct_result1236 != nil {
						unwrapped1237 := deconstruct_result1236
						p.pretty_monoid_def(unwrapped1237)
					} else {
						_dollar_dollar := msg
						var _t1661 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1661 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1234 := _t1661
						if deconstruct_result1234 != nil {
							unwrapped1235 := deconstruct_result1234
							p.pretty_monus_def(unwrapped1235)
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
	flat1251 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1662 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1662 = _dollar_dollar.GetAttrs()
		}
		fields1245 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1662}
		unwrapped_fields1246 := fields1245
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1247 := unwrapped_fields1246[0].(*pb.RelationId)
		p.pretty_relation_id(field1247)
		p.newline()
		field1248 := unwrapped_fields1246[1].(*pb.Abstraction)
		p.pretty_abstraction(field1248)
		field1249 := unwrapped_fields1246[2].([]*pb.Attribute)
		if field1249 != nil {
			p.newline()
			opt_val1250 := field1249
			p.pretty_attrs(opt_val1250)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1663 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1663 = _dollar_dollar.GetAttrs()
		}
		fields1252 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1663}
		unwrapped_fields1253 := fields1252
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1254 := unwrapped_fields1253[0].(*pb.RelationId)
		p.pretty_relation_id(field1254)
		p.newline()
		field1255 := unwrapped_fields1253[1].([]interface{})
		p.pretty_abstraction_with_arity(field1255)
		field1256 := unwrapped_fields1253[2].([]*pb.Attribute)
		if field1256 != nil {
			p.newline()
			opt_val1257 := field1256
			p.pretty_attrs(opt_val1257)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_dollar_dollar := msg
		_t1664 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1259 := []interface{}{_t1664, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.indent()
		field1261 := unwrapped_fields1260[0].([]interface{})
		p.pretty_bindings(field1261)
		p.newline()
		field1262 := unwrapped_fields1260[1].(*pb.Formula)
		p.pretty_formula(field1262)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1270 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1270 != nil {
		p.write(*flat1270)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1665 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1665 = _dollar_dollar.GetAttrs()
		}
		fields1264 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1665}
		unwrapped_fields1265 := fields1264
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1266 := unwrapped_fields1265[0].(*pb.RelationId)
		p.pretty_relation_id(field1266)
		p.newline()
		field1267 := unwrapped_fields1265[1].(*pb.Abstraction)
		p.pretty_abstraction(field1267)
		field1268 := unwrapped_fields1265[2].([]*pb.Attribute)
		if field1268 != nil {
			p.newline()
			opt_val1269 := field1268
			p.pretty_attrs(opt_val1269)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1666 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1666 = _dollar_dollar.GetAttrs()
		}
		fields1271 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1666}
		unwrapped_fields1272 := fields1271
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1273 := unwrapped_fields1272[0].(*pb.Monoid)
		p.pretty_monoid(field1273)
		p.newline()
		field1274 := unwrapped_fields1272[1].(*pb.RelationId)
		p.pretty_relation_id(field1274)
		p.newline()
		field1275 := unwrapped_fields1272[2].([]interface{})
		p.pretty_abstraction_with_arity(field1275)
		field1276 := unwrapped_fields1272[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1287 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1287 != nil {
		p.write(*flat1287)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1667 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1667 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1285 := _t1667
		if deconstruct_result1285 != nil {
			unwrapped1286 := deconstruct_result1285
			p.pretty_or_monoid(unwrapped1286)
		} else {
			_dollar_dollar := msg
			var _t1668 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1668 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1283 := _t1668
			if deconstruct_result1283 != nil {
				unwrapped1284 := deconstruct_result1283
				p.pretty_min_monoid(unwrapped1284)
			} else {
				_dollar_dollar := msg
				var _t1669 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1669 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1281 := _t1669
				if deconstruct_result1281 != nil {
					unwrapped1282 := deconstruct_result1281
					p.pretty_max_monoid(unwrapped1282)
				} else {
					_dollar_dollar := msg
					var _t1670 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1670 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1279 := _t1670
					if deconstruct_result1279 != nil {
						unwrapped1280 := deconstruct_result1279
						p.pretty_sum_monoid(unwrapped1280)
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
	fields1288 := msg
	_ = fields1288
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		_dollar_dollar := msg
		fields1289 := _dollar_dollar.GetType()
		unwrapped_fields1290 := fields1289
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1290)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1294 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1294 != nil {
		p.write(*flat1294)
		return nil
	} else {
		_dollar_dollar := msg
		fields1292 := _dollar_dollar.GetType()
		unwrapped_fields1293 := fields1292
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1293)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1297 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1297 != nil {
		p.write(*flat1297)
		return nil
	} else {
		_dollar_dollar := msg
		fields1295 := _dollar_dollar.GetType()
		unwrapped_fields1296 := fields1295
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1296)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1305 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1305 != nil {
		p.write(*flat1305)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1671 = _dollar_dollar.GetAttrs()
		}
		fields1298 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1671}
		unwrapped_fields1299 := fields1298
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1300 := unwrapped_fields1299[0].(*pb.Monoid)
		p.pretty_monoid(field1300)
		p.newline()
		field1301 := unwrapped_fields1299[1].(*pb.RelationId)
		p.pretty_relation_id(field1301)
		p.newline()
		field1302 := unwrapped_fields1299[2].([]interface{})
		p.pretty_abstraction_with_arity(field1302)
		field1303 := unwrapped_fields1299[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1312 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1312 != nil {
		p.write(*flat1312)
		return nil
	} else {
		_dollar_dollar := msg
		fields1306 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1307 := fields1306
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1308 := unwrapped_fields1307[0].(*pb.RelationId)
		p.pretty_relation_id(field1308)
		p.newline()
		field1309 := unwrapped_fields1307[1].(*pb.Abstraction)
		p.pretty_abstraction(field1309)
		p.newline()
		field1310 := unwrapped_fields1307[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1310)
		p.newline()
		field1311 := unwrapped_fields1307[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1311)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1316 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1316 != nil {
		p.write(*flat1316)
		return nil
	} else {
		fields1313 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1313) == 0) {
			p.newline()
			for i1315, elem1314 := range fields1313 {
				if (i1315 > 0) {
					p.newline()
				}
				p.pretty_var(elem1314)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		fields1317 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1317) == 0) {
			p.newline()
			for i1319, elem1318 := range fields1317 {
				if (i1319 > 0) {
					p.newline()
				}
				p.pretty_var(elem1318)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1672 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1672 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1327 := _t1672
		if deconstruct_result1327 != nil {
			unwrapped1328 := deconstruct_result1327
			p.pretty_edb(unwrapped1328)
		} else {
			_dollar_dollar := msg
			var _t1673 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1673 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1325 := _t1673
			if deconstruct_result1325 != nil {
				unwrapped1326 := deconstruct_result1325
				p.pretty_betree_relation(unwrapped1326)
			} else {
				_dollar_dollar := msg
				var _t1674 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1674 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1323 := _t1674
				if deconstruct_result1323 != nil {
					unwrapped1324 := deconstruct_result1323
					p.pretty_csv_data(unwrapped1324)
				} else {
					_dollar_dollar := msg
					var _t1675 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1675 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1321 := _t1675
					if deconstruct_result1321 != nil {
						unwrapped1322 := deconstruct_result1321
						p.pretty_iceberg_data(unwrapped1322)
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
	flat1335 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1335 != nil {
		p.write(*flat1335)
		return nil
	} else {
		_dollar_dollar := msg
		fields1330 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1332 := unwrapped_fields1331[0].(*pb.RelationId)
		p.pretty_relation_id(field1332)
		p.newline()
		field1333 := unwrapped_fields1331[1].([]string)
		p.pretty_edb_path(field1333)
		p.newline()
		field1334 := unwrapped_fields1331[2].([]*pb.Type)
		p.pretty_edb_types(field1334)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1339 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1339 != nil {
		p.write(*flat1339)
		return nil
	} else {
		fields1336 := msg
		p.write("[")
		p.indent()
		for i1338, elem1337 := range fields1336 {
			if (i1338 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1337))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		fields1340 := msg
		p.write("[")
		p.indent()
		for i1342, elem1341 := range fields1340 {
			if (i1342 > 0) {
				p.newline()
			}
			p.pretty_type(elem1341)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1348 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1348 != nil {
		p.write(*flat1348)
		return nil
	} else {
		_dollar_dollar := msg
		fields1344 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1345 := fields1344
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1346 := unwrapped_fields1345[0].(*pb.RelationId)
		p.pretty_relation_id(field1346)
		p.newline()
		field1347 := unwrapped_fields1345[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1347)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1354 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1354 != nil {
		p.write(*flat1354)
		return nil
	} else {
		_dollar_dollar := msg
		_t1676 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1349 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1676}
		unwrapped_fields1350 := fields1349
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1351 := unwrapped_fields1350[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1351)
		p.newline()
		field1352 := unwrapped_fields1350[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1352)
		p.newline()
		field1353 := unwrapped_fields1350[2].([][]interface{})
		p.pretty_config_dict(field1353)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1358 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1358 != nil {
		p.write(*flat1358)
		return nil
	} else {
		fields1355 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1355) == 0) {
			p.newline()
			for i1357, elem1356 := range fields1355 {
				if (i1357 > 0) {
					p.newline()
				}
				p.pretty_type(elem1356)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1362 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1362 != nil {
		p.write(*flat1362)
		return nil
	} else {
		fields1359 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1359) == 0) {
			p.newline()
			for i1361, elem1360 := range fields1359 {
				if (i1361 > 0) {
					p.newline()
				}
				p.pretty_type(elem1360)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1369 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1369 != nil {
		p.write(*flat1369)
		return nil
	} else {
		_dollar_dollar := msg
		fields1363 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1364 := fields1363
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1365 := unwrapped_fields1364[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1365)
		p.newline()
		field1366 := unwrapped_fields1364[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1366)
		p.newline()
		field1367 := unwrapped_fields1364[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1367)
		p.newline()
		field1368 := unwrapped_fields1364[3].(string)
		p.pretty_csv_asof(field1368)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1677 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1677 = _dollar_dollar.GetPaths()
		}
		var _t1678 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1678 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1370 := []interface{}{_t1677, _t1678}
		unwrapped_fields1371 := fields1370
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1372 := unwrapped_fields1371[0].([]string)
		if field1372 != nil {
			p.newline()
			opt_val1373 := field1372
			p.pretty_csv_locator_paths(opt_val1373)
		}
		field1374 := unwrapped_fields1371[1].(*string)
		if field1374 != nil {
			p.newline()
			opt_val1375 := *field1374
			p.pretty_csv_locator_inline_data(opt_val1375)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1380 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1380 != nil {
		p.write(*flat1380)
		return nil
	} else {
		fields1377 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1377) == 0) {
			p.newline()
			for i1379, elem1378 := range fields1377 {
				if (i1379 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1378))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		fields1381 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1381))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		_dollar_dollar := msg
		_t1679 := p.deconstruct_csv_config(_dollar_dollar)
		fields1383 := _t1679
		unwrapped_fields1384 := fields1383
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1384)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1389 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		fields1386 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1386) == 0) {
			p.newline()
			for i1388, elem1387 := range fields1386 {
				if (i1388 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1387)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1398 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1398 != nil {
		p.write(*flat1398)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1680 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1680 = _dollar_dollar.GetTargetId()
		}
		fields1390 := []interface{}{_dollar_dollar.GetColumnPath(), _t1680, _dollar_dollar.GetTypes()}
		unwrapped_fields1391 := fields1390
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1392 := unwrapped_fields1391[0].([]string)
		p.pretty_gnf_column_path(field1392)
		field1393 := unwrapped_fields1391[1].(*pb.RelationId)
		if field1393 != nil {
			p.newline()
			opt_val1394 := field1393
			p.pretty_relation_id(opt_val1394)
		}
		p.newline()
		p.write("[")
		field1395 := unwrapped_fields1391[2].([]*pb.Type)
		for i1397, elem1396 := range field1395 {
			if (i1397 > 0) {
				p.newline()
			}
			p.pretty_type(elem1396)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1681 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1681 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1403 := _t1681
		if deconstruct_result1403 != nil {
			unwrapped1404 := *deconstruct_result1403
			p.write(p.formatStringValue(unwrapped1404))
		} else {
			_dollar_dollar := msg
			var _t1682 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1682 = _dollar_dollar
			}
			deconstruct_result1399 := _t1682
			if deconstruct_result1399 != nil {
				unwrapped1400 := deconstruct_result1399
				p.write("[")
				p.indent()
				for i1402, elem1401 := range unwrapped1400 {
					if (i1402 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1401))
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
	flat1407 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		fields1406 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1406))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1414 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1414 != nil {
		p.write(*flat1414)
		return nil
	} else {
		_dollar_dollar := msg
		fields1408 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1409 := fields1408
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1410 := unwrapped_fields1409[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1410)
		p.newline()
		field1411 := unwrapped_fields1409[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1411)
		p.newline()
		field1412 := unwrapped_fields1409[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1412)
		p.newline()
		field1413 := unwrapped_fields1409[3].(bool)
		p.pretty_boolean_value(field1413)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1426 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		_t1683 := p.deconstruct_iceberg_locator_from_snapshot_optional(_dollar_dollar)
		_t1684 := p.deconstruct_iceberg_locator_to_snapshot_optional(_dollar_dollar)
		fields1415 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse(), _t1683, _t1684}
		unwrapped_fields1416 := fields1415
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1417 := unwrapped_fields1416[0].(string)
		p.write(p.formatStringValue(field1417))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1418 := unwrapped_fields1416[1].([]string)
		if !(len(field1418) == 0) {
			p.newline()
			for i1420, elem1419 := range field1418 {
				if (i1420 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1419))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1421 := unwrapped_fields1416[2].(string)
		p.write(p.formatStringValue(field1421))
		p.dedent()
		p.write(")")
		field1422 := unwrapped_fields1416[3].(*string)
		if field1422 != nil {
			p.newline()
			opt_val1423 := *field1422
			p.pretty_iceberg_from_snapshot(opt_val1423)
		}
		field1424 := unwrapped_fields1416[4].(*string)
		if field1424 != nil {
			p.newline()
			opt_val1425 := *field1424
			p.pretty_iceberg_to_snapshot(opt_val1425)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1428 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1428 != nil {
		p.write(*flat1428)
		return nil
	} else {
		fields1427 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1427))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1430 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1430 != nil {
		p.write(*flat1430)
		return nil
	} else {
		fields1429 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1429))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1442 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1442 != nil {
		p.write(*flat1442)
		return nil
	} else {
		_dollar_dollar := msg
		_t1685 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1431 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1685, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1432 := fields1431
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1433 := unwrapped_fields1432[0].(string)
		p.write(p.formatStringValue(field1433))
		p.dedent()
		p.write(")")
		field1434 := unwrapped_fields1432[1].(*string)
		if field1434 != nil {
			p.newline()
			opt_val1435 := *field1434
			p.pretty_iceberg_catalog_config_scope(opt_val1435)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1436 := unwrapped_fields1432[2].([][]interface{})
		if !(len(field1436) == 0) {
			p.newline()
			for i1438, elem1437 := range field1436 {
				if (i1438 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1437)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1439 := unwrapped_fields1432[3].([][]interface{})
		if !(len(field1439) == 0) {
			p.newline()
			for i1441, elem1440 := range field1439 {
				if (i1441 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1440)
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
	flat1444 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1444 != nil {
		p.write(*flat1444)
		return nil
	} else {
		fields1443 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1443))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		_dollar_dollar := msg
		fields1445 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1446 := fields1445
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1447 := unwrapped_fields1446[0].(string)
		p.write(p.formatStringValue(field1447))
		p.newline()
		field1448 := unwrapped_fields1446[1].(string)
		p.write(p.formatStringValue(field1448))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1454 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1454 != nil {
		p.write(*flat1454)
		return nil
	} else {
		_dollar_dollar := msg
		_t1686 := p.mask_secret_value(_dollar_dollar)
		fields1450 := []interface{}{_dollar_dollar[0].(string), _t1686}
		unwrapped_fields1451 := fields1450
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1452 := unwrapped_fields1451[0].(string)
		p.write(p.formatStringValue(field1452))
		p.newline()
		field1453 := unwrapped_fields1451[1].(string)
		p.write(p.formatStringValue(field1453))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		_dollar_dollar := msg
		fields1455 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1456 := fields1455
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1456)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		_dollar_dollar := msg
		fields1458 := _dollar_dollar.GetRelations()
		unwrapped_fields1459 := fields1458
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1459) == 0) {
			p.newline()
			for i1461, elem1460 := range unwrapped_fields1459 {
				if (i1461 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1460)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1467 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1467 != nil {
		p.write(*flat1467)
		return nil
	} else {
		_dollar_dollar := msg
		fields1463 := _dollar_dollar.GetMappings()
		unwrapped_fields1464 := fields1463
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1464) == 0) {
			p.newline()
			for i1466, elem1465 := range unwrapped_fields1464 {
				if (i1466 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1465)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		_dollar_dollar := msg
		fields1468 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1469 := fields1468
		field1470 := unwrapped_fields1469[0].([]string)
		p.pretty_edb_path(field1470)
		p.write(" ")
		field1471 := unwrapped_fields1469[1].(*pb.RelationId)
		p.pretty_relation_id(field1471)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1476 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1476 != nil {
		p.write(*flat1476)
		return nil
	} else {
		fields1473 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1473) == 0) {
			p.newline()
			for i1475, elem1474 := range fields1473 {
				if (i1475 > 0) {
					p.newline()
				}
				p.pretty_read(elem1474)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1487 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1487 != nil {
		p.write(*flat1487)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1687 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1687 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1485 := _t1687
		if deconstruct_result1485 != nil {
			unwrapped1486 := deconstruct_result1485
			p.pretty_demand(unwrapped1486)
		} else {
			_dollar_dollar := msg
			var _t1688 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1688 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1483 := _t1688
			if deconstruct_result1483 != nil {
				unwrapped1484 := deconstruct_result1483
				p.pretty_output(unwrapped1484)
			} else {
				_dollar_dollar := msg
				var _t1689 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1689 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1481 := _t1689
				if deconstruct_result1481 != nil {
					unwrapped1482 := deconstruct_result1481
					p.pretty_what_if(unwrapped1482)
				} else {
					_dollar_dollar := msg
					var _t1690 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1690 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1479 := _t1690
					if deconstruct_result1479 != nil {
						unwrapped1480 := deconstruct_result1479
						p.pretty_abort(unwrapped1480)
					} else {
						_dollar_dollar := msg
						var _t1691 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1691 = _dollar_dollar.GetExport()
						}
						deconstruct_result1477 := _t1691
						if deconstruct_result1477 != nil {
							unwrapped1478 := deconstruct_result1477
							p.pretty_export(unwrapped1478)
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
	flat1490 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1490 != nil {
		p.write(*flat1490)
		return nil
	} else {
		_dollar_dollar := msg
		fields1488 := _dollar_dollar.GetRelationId()
		unwrapped_fields1489 := fields1488
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1489)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1495 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1495 != nil {
		p.write(*flat1495)
		return nil
	} else {
		_dollar_dollar := msg
		fields1491 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1492 := fields1491
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1493 := unwrapped_fields1492[0].(string)
		p.pretty_name(field1493)
		p.newline()
		field1494 := unwrapped_fields1492[1].(*pb.RelationId)
		p.pretty_relation_id(field1494)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1500 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1500 != nil {
		p.write(*flat1500)
		return nil
	} else {
		_dollar_dollar := msg
		fields1496 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1497 := fields1496
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1498 := unwrapped_fields1497[0].(string)
		p.pretty_name(field1498)
		p.newline()
		field1499 := unwrapped_fields1497[1].(*pb.Epoch)
		p.pretty_epoch(field1499)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1506 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1506 != nil {
		p.write(*flat1506)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1692 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1692 = ptr(_dollar_dollar.GetName())
		}
		fields1501 := []interface{}{_t1692, _dollar_dollar.GetRelationId()}
		unwrapped_fields1502 := fields1501
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1503 := unwrapped_fields1502[0].(*string)
		if field1503 != nil {
			p.newline()
			opt_val1504 := *field1503
			p.pretty_name(opt_val1504)
		}
		p.newline()
		field1505 := unwrapped_fields1502[1].(*pb.RelationId)
		p.pretty_relation_id(field1505)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1511 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1511 != nil {
		p.write(*flat1511)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1693 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1509 := _t1693
		if deconstruct_result1509 != nil {
			unwrapped1510 := deconstruct_result1509
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1510)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1694 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1694 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1507 := _t1694
			if deconstruct_result1507 != nil {
				unwrapped1508 := deconstruct_result1507
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1508)
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
	flat1522 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1522 != nil {
		p.write(*flat1522)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1695 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1695 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1517 := _t1695
		if deconstruct_result1517 != nil {
			unwrapped1518 := deconstruct_result1517
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1519 := unwrapped1518[0].(string)
			p.pretty_export_csv_path(field1519)
			p.newline()
			field1520 := unwrapped1518[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1520)
			p.newline()
			field1521 := unwrapped1518[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1521)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1696 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1697 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1696 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1697}
			}
			deconstruct_result1512 := _t1696
			if deconstruct_result1512 != nil {
				unwrapped1513 := deconstruct_result1512
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1514 := unwrapped1513[0].(string)
				p.pretty_export_csv_path(field1514)
				p.newline()
				field1515 := unwrapped1513[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1515)
				p.newline()
				field1516 := unwrapped1513[2].([][]interface{})
				p.pretty_config_dict(field1516)
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
	flat1524 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1524 != nil {
		p.write(*flat1524)
		return nil
	} else {
		fields1523 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1523))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1531 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1531 != nil {
		p.write(*flat1531)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1698 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1698 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1527 := _t1698
		if deconstruct_result1527 != nil {
			unwrapped1528 := deconstruct_result1527
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1528) == 0) {
				p.newline()
				for i1530, elem1529 := range unwrapped1528 {
					if (i1530 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1529)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1699 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1699 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1525 := _t1699
			if deconstruct_result1525 != nil {
				unwrapped1526 := deconstruct_result1525
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1526)
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
	flat1536 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1536 != nil {
		p.write(*flat1536)
		return nil
	} else {
		_dollar_dollar := msg
		fields1532 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1533 := fields1532
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1534 := unwrapped_fields1533[0].(string)
		p.write(p.formatStringValue(field1534))
		p.newline()
		field1535 := unwrapped_fields1533[1].(*pb.RelationId)
		p.pretty_relation_id(field1535)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1540 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1540 != nil {
		p.write(*flat1540)
		return nil
	} else {
		fields1537 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1537) == 0) {
			p.newline()
			for i1539, elem1538 := range fields1537 {
				if (i1539 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1538)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1554 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1554 != nil {
		p.write(*flat1554)
		return nil
	} else {
		_dollar_dollar := msg
		_t1700 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1541 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1700}
		unwrapped_fields1542 := fields1541
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1543 := unwrapped_fields1542[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1543)
		p.newline()
		field1544 := unwrapped_fields1542[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1544)
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_def")
		p.newline()
		field1545 := unwrapped_fields1542[2].(*pb.RelationId)
		p.pretty_relation_id(field1545)
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("columns")
		field1546 := unwrapped_fields1542[3].([]*pb.ExportGNFColumn)
		if !(len(field1546) == 0) {
			p.newline()
			for i1548, elem1547 := range field1546 {
				if (i1548 > 0) {
					p.newline()
				}
				p.pretty_export_gnf_column(elem1547)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_properties")
		field1549 := unwrapped_fields1542[4].([][]interface{})
		if !(len(field1549) == 0) {
			p.newline()
			for i1551, elem1550 := range field1549 {
				if (i1551 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1550)
			}
		}
		p.dedent()
		p.write(")")
		field1552 := unwrapped_fields1542[5].([][]interface{})
		if field1552 != nil {
			p.newline()
			opt_val1553 := field1552
			p.pretty_config_dict(opt_val1553)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_gnf_column(msg *pb.ExportGNFColumn) interface{} {
	flat1559 := p.tryFlat(msg, func() { p.pretty_export_gnf_column(msg) })
	if flat1559 != nil {
		p.write(*flat1559)
		return nil
	} else {
		_dollar_dollar := msg
		fields1555 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetNullable()}
		unwrapped_fields1556 := fields1555
		p.write("(")
		p.write("gnf_column")
		p.indentSexp()
		p.newline()
		field1557 := unwrapped_fields1556[0].(string)
		p.write(p.formatStringValue(field1557))
		p.newline()
		field1558 := unwrapped_fields1556[1].(bool)
		p.pretty_boolean_value(field1558)
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
		_t1746 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1746)
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
	case *pb.ExportGNFColumn:
		p.pretty_export_gnf_column(m)
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
