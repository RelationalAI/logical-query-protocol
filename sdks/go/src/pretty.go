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
	_t1679 := &pb.Value{}
	_t1679.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1679
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1680 := &pb.Value{}
	_t1680.Value = &pb.Value_IntValue{IntValue: v}
	return _t1680
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1681 := &pb.Value{}
	_t1681.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1681
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1682 := &pb.Value{}
	_t1682.Value = &pb.Value_StringValue{StringValue: v}
	return _t1682
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1683 := &pb.Value{}
	_t1683.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1683
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1684 := &pb.Value{}
	_t1684.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1684
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1685 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1685})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1686 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1686})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1687 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1687})
			}
		}
	}
	_t1688 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1688})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1689 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1689})
	_t1690 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1690})
	if msg.GetNewLine() != "" {
		_t1691 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1691})
	}
	_t1692 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1692})
	_t1693 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1693})
	_t1694 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1694})
	if msg.GetComment() != "" {
		_t1695 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1695})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1696 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1696})
	}
	_t1697 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1697})
	_t1698 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1698})
	_t1699 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1699})
	if msg.GetPartitionSizeMb() != 0 {
		_t1700 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1700})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1701 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1701})
	_t1702 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1702})
	_t1703 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1703})
	_t1704 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1704})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1705 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1705})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1706 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1706})
		}
	}
	_t1707 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1707})
	_t1708 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1708})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1709 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1709})
	}
	if msg.Compression != nil {
		_t1710 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1710})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1711 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1711})
	}
	if msg.SyntaxMissingString != nil {
		_t1712 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1712})
	}
	if msg.SyntaxDelim != nil {
		_t1713 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1713})
	}
	if msg.SyntaxQuotechar != nil {
		_t1714 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1714})
	}
	if msg.SyntaxEscapechar != nil {
		_t1715 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1715})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1716 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1716
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1717 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1717
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1718 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1718})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1719 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1719})
	}
	if msg.GetCompression() != "" {
		_t1720 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1720})
	}
	var _t1721 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1721
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1722 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1722
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
	flat779 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat779 != nil {
		p.write(*flat779)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1540 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1540 = _dollar_dollar.GetConfigure()
		}
		var _t1541 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1541 = _dollar_dollar.GetSync()
		}
		fields770 := []interface{}{_t1540, _t1541, _dollar_dollar.GetEpochs()}
		unwrapped_fields771 := fields770
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field772 := unwrapped_fields771[0].(*pb.Configure)
		if field772 != nil {
			p.newline()
			opt_val773 := field772
			p.pretty_configure(opt_val773)
		}
		field774 := unwrapped_fields771[1].(*pb.Sync)
		if field774 != nil {
			p.newline()
			opt_val775 := field774
			p.pretty_sync(opt_val775)
		}
		field776 := unwrapped_fields771[2].([]*pb.Epoch)
		if !(len(field776) == 0) {
			p.newline()
			for i778, elem777 := range field776 {
				if (i778 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem777)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat782 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat782 != nil {
		p.write(*flat782)
		return nil
	} else {
		_dollar_dollar := msg
		_t1542 := p.deconstruct_configure(_dollar_dollar)
		fields780 := _t1542
		unwrapped_fields781 := fields780
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields781)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat786 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat786 != nil {
		p.write(*flat786)
		return nil
	} else {
		fields783 := msg
		p.write("{")
		p.indent()
		if !(len(fields783) == 0) {
			p.newline()
			for i785, elem784 := range fields783 {
				if (i785 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem784)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat791 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat791 != nil {
		p.write(*flat791)
		return nil
	} else {
		_dollar_dollar := msg
		fields787 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields788 := fields787
		p.write(":")
		field789 := unwrapped_fields788[0].(string)
		p.write(field789)
		p.write(" ")
		field790 := unwrapped_fields788[1].(*pb.Value)
		p.pretty_raw_value(field790)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat817 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat817 != nil {
		p.write(*flat817)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1543 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1543 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result815 := _t1543
		if deconstruct_result815 != nil {
			unwrapped816 := deconstruct_result815
			p.pretty_raw_date(unwrapped816)
		} else {
			_dollar_dollar := msg
			var _t1544 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1544 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result813 := _t1544
			if deconstruct_result813 != nil {
				unwrapped814 := deconstruct_result813
				p.pretty_raw_datetime(unwrapped814)
			} else {
				_dollar_dollar := msg
				var _t1545 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1545 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result811 := _t1545
				if deconstruct_result811 != nil {
					unwrapped812 := *deconstruct_result811
					p.write(p.formatStringValue(unwrapped812))
				} else {
					_dollar_dollar := msg
					var _t1546 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1546 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result809 := _t1546
					if deconstruct_result809 != nil {
						unwrapped810 := *deconstruct_result809
						p.write(fmt.Sprintf("%di32", unwrapped810))
					} else {
						_dollar_dollar := msg
						var _t1547 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1547 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result807 := _t1547
						if deconstruct_result807 != nil {
							unwrapped808 := *deconstruct_result807
							p.write(fmt.Sprintf("%d", unwrapped808))
						} else {
							_dollar_dollar := msg
							var _t1548 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1548 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result805 := _t1548
							if deconstruct_result805 != nil {
								unwrapped806 := *deconstruct_result805
								p.write(formatFloat32(unwrapped806))
							} else {
								_dollar_dollar := msg
								var _t1549 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1549 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result803 := _t1549
								if deconstruct_result803 != nil {
									unwrapped804 := *deconstruct_result803
									p.write(formatFloat64(unwrapped804))
								} else {
									_dollar_dollar := msg
									var _t1550 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1550 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result801 := _t1550
									if deconstruct_result801 != nil {
										unwrapped802 := *deconstruct_result801
										p.write(fmt.Sprintf("%du32", unwrapped802))
									} else {
										_dollar_dollar := msg
										var _t1551 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1551 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result799 := _t1551
										if deconstruct_result799 != nil {
											unwrapped800 := deconstruct_result799
											p.write(p.formatUint128(unwrapped800))
										} else {
											_dollar_dollar := msg
											var _t1552 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1552 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result797 := _t1552
											if deconstruct_result797 != nil {
												unwrapped798 := deconstruct_result797
												p.write(p.formatInt128(unwrapped798))
											} else {
												_dollar_dollar := msg
												var _t1553 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1553 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result795 := _t1553
												if deconstruct_result795 != nil {
													unwrapped796 := deconstruct_result795
													p.write(p.formatDecimal(unwrapped796))
												} else {
													_dollar_dollar := msg
													var _t1554 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1554 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result793 := _t1554
													if deconstruct_result793 != nil {
														unwrapped794 := *deconstruct_result793
														p.pretty_boolean_value(unwrapped794)
													} else {
														fields792 := msg
														_ = fields792
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
	flat823 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat823 != nil {
		p.write(*flat823)
		return nil
	} else {
		_dollar_dollar := msg
		fields818 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields819 := fields818
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field820 := unwrapped_fields819[0].(int64)
		p.write(fmt.Sprintf("%d", field820))
		p.newline()
		field821 := unwrapped_fields819[1].(int64)
		p.write(fmt.Sprintf("%d", field821))
		p.newline()
		field822 := unwrapped_fields819[2].(int64)
		p.write(fmt.Sprintf("%d", field822))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat834 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat834 != nil {
		p.write(*flat834)
		return nil
	} else {
		_dollar_dollar := msg
		fields824 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields825 := fields824
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field826 := unwrapped_fields825[0].(int64)
		p.write(fmt.Sprintf("%d", field826))
		p.newline()
		field827 := unwrapped_fields825[1].(int64)
		p.write(fmt.Sprintf("%d", field827))
		p.newline()
		field828 := unwrapped_fields825[2].(int64)
		p.write(fmt.Sprintf("%d", field828))
		p.newline()
		field829 := unwrapped_fields825[3].(int64)
		p.write(fmt.Sprintf("%d", field829))
		p.newline()
		field830 := unwrapped_fields825[4].(int64)
		p.write(fmt.Sprintf("%d", field830))
		p.newline()
		field831 := unwrapped_fields825[5].(int64)
		p.write(fmt.Sprintf("%d", field831))
		field832 := unwrapped_fields825[6].(*int64)
		if field832 != nil {
			p.newline()
			opt_val833 := *field832
			p.write(fmt.Sprintf("%d", opt_val833))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1555 []interface{}
	if _dollar_dollar {
		_t1555 = []interface{}{}
	}
	deconstruct_result837 := _t1555
	if deconstruct_result837 != nil {
		unwrapped838 := deconstruct_result837
		_ = unwrapped838
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1556 []interface{}
		if !(_dollar_dollar) {
			_t1556 = []interface{}{}
		}
		deconstruct_result835 := _t1556
		if deconstruct_result835 != nil {
			unwrapped836 := deconstruct_result835
			_ = unwrapped836
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat843 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat843 != nil {
		p.write(*flat843)
		return nil
	} else {
		_dollar_dollar := msg
		fields839 := _dollar_dollar.GetFragments()
		unwrapped_fields840 := fields839
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields840) == 0) {
			p.newline()
			for i842, elem841 := range unwrapped_fields840 {
				if (i842 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem841)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat846 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat846 != nil {
		p.write(*flat846)
		return nil
	} else {
		_dollar_dollar := msg
		fields844 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields845 := fields844
		p.write(":")
		p.write(unwrapped_fields845)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat853 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat853 != nil {
		p.write(*flat853)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1557 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1557 = _dollar_dollar.GetWrites()
		}
		var _t1558 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1558 = _dollar_dollar.GetReads()
		}
		fields847 := []interface{}{_t1557, _t1558}
		unwrapped_fields848 := fields847
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field849 := unwrapped_fields848[0].([]*pb.Write)
		if field849 != nil {
			p.newline()
			opt_val850 := field849
			p.pretty_epoch_writes(opt_val850)
		}
		field851 := unwrapped_fields848[1].([]*pb.Read)
		if field851 != nil {
			p.newline()
			opt_val852 := field851
			p.pretty_epoch_reads(opt_val852)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat857 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat857 != nil {
		p.write(*flat857)
		return nil
	} else {
		fields854 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields854) == 0) {
			p.newline()
			for i856, elem855 := range fields854 {
				if (i856 > 0) {
					p.newline()
				}
				p.pretty_write(elem855)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat866 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat866 != nil {
		p.write(*flat866)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1559 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1559 = _dollar_dollar.GetDefine()
		}
		deconstruct_result864 := _t1559
		if deconstruct_result864 != nil {
			unwrapped865 := deconstruct_result864
			p.pretty_define(unwrapped865)
		} else {
			_dollar_dollar := msg
			var _t1560 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1560 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result862 := _t1560
			if deconstruct_result862 != nil {
				unwrapped863 := deconstruct_result862
				p.pretty_undefine(unwrapped863)
			} else {
				_dollar_dollar := msg
				var _t1561 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1561 = _dollar_dollar.GetContext()
				}
				deconstruct_result860 := _t1561
				if deconstruct_result860 != nil {
					unwrapped861 := deconstruct_result860
					p.pretty_context(unwrapped861)
				} else {
					_dollar_dollar := msg
					var _t1562 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1562 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result858 := _t1562
					if deconstruct_result858 != nil {
						unwrapped859 := deconstruct_result858
						p.pretty_snapshot(unwrapped859)
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
	flat869 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat869 != nil {
		p.write(*flat869)
		return nil
	} else {
		_dollar_dollar := msg
		fields867 := _dollar_dollar.GetFragment()
		unwrapped_fields868 := fields867
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields868)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat876 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields870 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields871 := fields870
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field872 := unwrapped_fields871[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field872)
		field873 := unwrapped_fields871[1].([]*pb.Declaration)
		if !(len(field873) == 0) {
			p.newline()
			for i875, elem874 := range field873 {
				if (i875 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem874)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat878 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat878 != nil {
		p.write(*flat878)
		return nil
	} else {
		fields877 := msg
		p.pretty_fragment_id(fields877)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1563 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1563 = _dollar_dollar.GetDef()
		}
		deconstruct_result885 := _t1563
		if deconstruct_result885 != nil {
			unwrapped886 := deconstruct_result885
			p.pretty_def(unwrapped886)
		} else {
			_dollar_dollar := msg
			var _t1564 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1564 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result883 := _t1564
			if deconstruct_result883 != nil {
				unwrapped884 := deconstruct_result883
				p.pretty_algorithm(unwrapped884)
			} else {
				_dollar_dollar := msg
				var _t1565 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1565 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result881 := _t1565
				if deconstruct_result881 != nil {
					unwrapped882 := deconstruct_result881
					p.pretty_constraint(unwrapped882)
				} else {
					_dollar_dollar := msg
					var _t1566 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1566 = _dollar_dollar.GetData()
					}
					deconstruct_result879 := _t1566
					if deconstruct_result879 != nil {
						unwrapped880 := deconstruct_result879
						p.pretty_data(unwrapped880)
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
	flat894 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1567 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1567 = _dollar_dollar.GetAttrs()
		}
		fields888 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1567}
		unwrapped_fields889 := fields888
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field890 := unwrapped_fields889[0].(*pb.RelationId)
		p.pretty_relation_id(field890)
		p.newline()
		field891 := unwrapped_fields889[1].(*pb.Abstraction)
		p.pretty_abstraction(field891)
		field892 := unwrapped_fields889[2].([]*pb.Attribute)
		if field892 != nil {
			p.newline()
			opt_val893 := field892
			p.pretty_attrs(opt_val893)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat899 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1568 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1569 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1568 = ptr(_t1569)
		}
		deconstruct_result897 := _t1568
		if deconstruct_result897 != nil {
			unwrapped898 := *deconstruct_result897
			p.write(":")
			p.write(unwrapped898)
		} else {
			_dollar_dollar := msg
			_t1570 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result895 := _t1570
			if deconstruct_result895 != nil {
				unwrapped896 := deconstruct_result895
				p.write(p.formatUint128(unwrapped896))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat904 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		_dollar_dollar := msg
		_t1571 := p.deconstruct_bindings(_dollar_dollar)
		fields900 := []interface{}{_t1571, _dollar_dollar.GetValue()}
		unwrapped_fields901 := fields900
		p.write("(")
		p.indent()
		field902 := unwrapped_fields901[0].([]interface{})
		p.pretty_bindings(field902)
		p.newline()
		field903 := unwrapped_fields901[1].(*pb.Formula)
		p.pretty_formula(field903)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat912 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat912 != nil {
		p.write(*flat912)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1572 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1572 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields905 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1572}
		unwrapped_fields906 := fields905
		p.write("[")
		p.indent()
		field907 := unwrapped_fields906[0].([]*pb.Binding)
		for i909, elem908 := range field907 {
			if (i909 > 0) {
				p.newline()
			}
			p.pretty_binding(elem908)
		}
		field910 := unwrapped_fields906[1].([]*pb.Binding)
		if field910 != nil {
			p.newline()
			opt_val911 := field910
			p.pretty_value_bindings(opt_val911)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_dollar_dollar := msg
		fields913 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields914 := fields913
		field915 := unwrapped_fields914[0].(string)
		p.write(field915)
		p.write("::")
		field916 := unwrapped_fields914[1].(*pb.Type)
		p.pretty_type(field916)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1573 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1573 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result944 := _t1573
		if deconstruct_result944 != nil {
			unwrapped945 := deconstruct_result944
			p.pretty_unspecified_type(unwrapped945)
		} else {
			_dollar_dollar := msg
			var _t1574 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1574 = _dollar_dollar.GetStringType()
			}
			deconstruct_result942 := _t1574
			if deconstruct_result942 != nil {
				unwrapped943 := deconstruct_result942
				p.pretty_string_type(unwrapped943)
			} else {
				_dollar_dollar := msg
				var _t1575 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1575 = _dollar_dollar.GetIntType()
				}
				deconstruct_result940 := _t1575
				if deconstruct_result940 != nil {
					unwrapped941 := deconstruct_result940
					p.pretty_int_type(unwrapped941)
				} else {
					_dollar_dollar := msg
					var _t1576 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1576 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result938 := _t1576
					if deconstruct_result938 != nil {
						unwrapped939 := deconstruct_result938
						p.pretty_float_type(unwrapped939)
					} else {
						_dollar_dollar := msg
						var _t1577 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1577 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result936 := _t1577
						if deconstruct_result936 != nil {
							unwrapped937 := deconstruct_result936
							p.pretty_uint128_type(unwrapped937)
						} else {
							_dollar_dollar := msg
							var _t1578 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1578 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result934 := _t1578
							if deconstruct_result934 != nil {
								unwrapped935 := deconstruct_result934
								p.pretty_int128_type(unwrapped935)
							} else {
								_dollar_dollar := msg
								var _t1579 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1579 = _dollar_dollar.GetDateType()
								}
								deconstruct_result932 := _t1579
								if deconstruct_result932 != nil {
									unwrapped933 := deconstruct_result932
									p.pretty_date_type(unwrapped933)
								} else {
									_dollar_dollar := msg
									var _t1580 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1580 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result930 := _t1580
									if deconstruct_result930 != nil {
										unwrapped931 := deconstruct_result930
										p.pretty_datetime_type(unwrapped931)
									} else {
										_dollar_dollar := msg
										var _t1581 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1581 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result928 := _t1581
										if deconstruct_result928 != nil {
											unwrapped929 := deconstruct_result928
											p.pretty_missing_type(unwrapped929)
										} else {
											_dollar_dollar := msg
											var _t1582 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1582 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result926 := _t1582
											if deconstruct_result926 != nil {
												unwrapped927 := deconstruct_result926
												p.pretty_decimal_type(unwrapped927)
											} else {
												_dollar_dollar := msg
												var _t1583 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1583 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result924 := _t1583
												if deconstruct_result924 != nil {
													unwrapped925 := deconstruct_result924
													p.pretty_boolean_type(unwrapped925)
												} else {
													_dollar_dollar := msg
													var _t1584 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1584 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result922 := _t1584
													if deconstruct_result922 != nil {
														unwrapped923 := deconstruct_result922
														p.pretty_int32_type(unwrapped923)
													} else {
														_dollar_dollar := msg
														var _t1585 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1585 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result920 := _t1585
														if deconstruct_result920 != nil {
															unwrapped921 := deconstruct_result920
															p.pretty_float32_type(unwrapped921)
														} else {
															_dollar_dollar := msg
															var _t1586 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1586 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result918 := _t1586
															if deconstruct_result918 != nil {
																unwrapped919 := deconstruct_result918
																p.pretty_uint32_type(unwrapped919)
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
	fields947 := msg
	_ = fields947
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields948 := msg
	_ = fields948
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields949 := msg
	_ = fields949
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields950 := msg
	_ = fields950
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields951 := msg
	_ = fields951
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields952 := msg
	_ = fields952
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields953 := msg
	_ = fields953
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields954 := msg
	_ = fields954
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields955 := msg
	_ = fields955
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat960 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat960 != nil {
		p.write(*flat960)
		return nil
	} else {
		_dollar_dollar := msg
		fields956 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields957 := fields956
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field958 := unwrapped_fields957[0].(int64)
		p.write(fmt.Sprintf("%d", field958))
		p.newline()
		field959 := unwrapped_fields957[1].(int64)
		p.write(fmt.Sprintf("%d", field959))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields961 := msg
	_ = fields961
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields962 := msg
	_ = fields962
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields963 := msg
	_ = fields963
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields964 := msg
	_ = fields964
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat968 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		fields965 := msg
		p.write("|")
		if !(len(fields965) == 0) {
			p.write(" ")
			for i967, elem966 := range fields965 {
				if (i967 > 0) {
					p.newline()
				}
				p.pretty_binding(elem966)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat995 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat995 != nil {
		p.write(*flat995)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1587 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1587 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result993 := _t1587
		if deconstruct_result993 != nil {
			unwrapped994 := deconstruct_result993
			p.pretty_true(unwrapped994)
		} else {
			_dollar_dollar := msg
			var _t1588 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1588 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result991 := _t1588
			if deconstruct_result991 != nil {
				unwrapped992 := deconstruct_result991
				p.pretty_false(unwrapped992)
			} else {
				_dollar_dollar := msg
				var _t1589 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1589 = _dollar_dollar.GetExists()
				}
				deconstruct_result989 := _t1589
				if deconstruct_result989 != nil {
					unwrapped990 := deconstruct_result989
					p.pretty_exists(unwrapped990)
				} else {
					_dollar_dollar := msg
					var _t1590 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1590 = _dollar_dollar.GetReduce()
					}
					deconstruct_result987 := _t1590
					if deconstruct_result987 != nil {
						unwrapped988 := deconstruct_result987
						p.pretty_reduce(unwrapped988)
					} else {
						_dollar_dollar := msg
						var _t1591 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1591 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result985 := _t1591
						if deconstruct_result985 != nil {
							unwrapped986 := deconstruct_result985
							p.pretty_conjunction(unwrapped986)
						} else {
							_dollar_dollar := msg
							var _t1592 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1592 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result983 := _t1592
							if deconstruct_result983 != nil {
								unwrapped984 := deconstruct_result983
								p.pretty_disjunction(unwrapped984)
							} else {
								_dollar_dollar := msg
								var _t1593 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1593 = _dollar_dollar.GetNot()
								}
								deconstruct_result981 := _t1593
								if deconstruct_result981 != nil {
									unwrapped982 := deconstruct_result981
									p.pretty_not(unwrapped982)
								} else {
									_dollar_dollar := msg
									var _t1594 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1594 = _dollar_dollar.GetFfi()
									}
									deconstruct_result979 := _t1594
									if deconstruct_result979 != nil {
										unwrapped980 := deconstruct_result979
										p.pretty_ffi(unwrapped980)
									} else {
										_dollar_dollar := msg
										var _t1595 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1595 = _dollar_dollar.GetAtom()
										}
										deconstruct_result977 := _t1595
										if deconstruct_result977 != nil {
											unwrapped978 := deconstruct_result977
											p.pretty_atom(unwrapped978)
										} else {
											_dollar_dollar := msg
											var _t1596 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1596 = _dollar_dollar.GetPragma()
											}
											deconstruct_result975 := _t1596
											if deconstruct_result975 != nil {
												unwrapped976 := deconstruct_result975
												p.pretty_pragma(unwrapped976)
											} else {
												_dollar_dollar := msg
												var _t1597 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1597 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result973 := _t1597
												if deconstruct_result973 != nil {
													unwrapped974 := deconstruct_result973
													p.pretty_primitive(unwrapped974)
												} else {
													_dollar_dollar := msg
													var _t1598 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1598 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result971 := _t1598
													if deconstruct_result971 != nil {
														unwrapped972 := deconstruct_result971
														p.pretty_rel_atom(unwrapped972)
													} else {
														_dollar_dollar := msg
														var _t1599 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1599 = _dollar_dollar.GetCast()
														}
														deconstruct_result969 := _t1599
														if deconstruct_result969 != nil {
															unwrapped970 := deconstruct_result969
															p.pretty_cast(unwrapped970)
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
	fields996 := msg
	_ = fields996
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields997 := msg
	_ = fields997
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1002 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1002 != nil {
		p.write(*flat1002)
		return nil
	} else {
		_dollar_dollar := msg
		_t1600 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields998 := []interface{}{_t1600, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields999 := fields998
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1000 := unwrapped_fields999[0].([]interface{})
		p.pretty_bindings(field1000)
		p.newline()
		field1001 := unwrapped_fields999[1].(*pb.Formula)
		p.pretty_formula(field1001)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1008 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1008 != nil {
		p.write(*flat1008)
		return nil
	} else {
		_dollar_dollar := msg
		fields1003 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1004 := fields1003
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1005 := unwrapped_fields1004[0].(*pb.Abstraction)
		p.pretty_abstraction(field1005)
		p.newline()
		field1006 := unwrapped_fields1004[1].(*pb.Abstraction)
		p.pretty_abstraction(field1006)
		p.newline()
		field1007 := unwrapped_fields1004[2].([]*pb.Term)
		p.pretty_terms(field1007)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1012 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1012 != nil {
		p.write(*flat1012)
		return nil
	} else {
		fields1009 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1009) == 0) {
			p.newline()
			for i1011, elem1010 := range fields1009 {
				if (i1011 > 0) {
					p.newline()
				}
				p.pretty_term(elem1010)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1017 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1017 != nil {
		p.write(*flat1017)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1601 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1601 = _dollar_dollar.GetVar()
		}
		deconstruct_result1015 := _t1601
		if deconstruct_result1015 != nil {
			unwrapped1016 := deconstruct_result1015
			p.pretty_var(unwrapped1016)
		} else {
			_dollar_dollar := msg
			var _t1602 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1602 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1013 := _t1602
			if deconstruct_result1013 != nil {
				unwrapped1014 := deconstruct_result1013
				p.pretty_value(unwrapped1014)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1020 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1020 != nil {
		p.write(*flat1020)
		return nil
	} else {
		_dollar_dollar := msg
		fields1018 := _dollar_dollar.GetName()
		unwrapped_fields1019 := fields1018
		p.write(unwrapped_fields1019)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1046 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1046 != nil {
		p.write(*flat1046)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1603 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1603 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1044 := _t1603
		if deconstruct_result1044 != nil {
			unwrapped1045 := deconstruct_result1044
			p.pretty_date(unwrapped1045)
		} else {
			_dollar_dollar := msg
			var _t1604 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1604 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1042 := _t1604
			if deconstruct_result1042 != nil {
				unwrapped1043 := deconstruct_result1042
				p.pretty_datetime(unwrapped1043)
			} else {
				_dollar_dollar := msg
				var _t1605 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1605 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1040 := _t1605
				if deconstruct_result1040 != nil {
					unwrapped1041 := *deconstruct_result1040
					p.write(p.formatStringValue(unwrapped1041))
				} else {
					_dollar_dollar := msg
					var _t1606 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1606 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1038 := _t1606
					if deconstruct_result1038 != nil {
						unwrapped1039 := *deconstruct_result1038
						p.write(fmt.Sprintf("%di32", unwrapped1039))
					} else {
						_dollar_dollar := msg
						var _t1607 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1607 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1036 := _t1607
						if deconstruct_result1036 != nil {
							unwrapped1037 := *deconstruct_result1036
							p.write(fmt.Sprintf("%d", unwrapped1037))
						} else {
							_dollar_dollar := msg
							var _t1608 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1608 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1034 := _t1608
							if deconstruct_result1034 != nil {
								unwrapped1035 := *deconstruct_result1034
								p.write(formatFloat32(unwrapped1035))
							} else {
								_dollar_dollar := msg
								var _t1609 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1609 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1032 := _t1609
								if deconstruct_result1032 != nil {
									unwrapped1033 := *deconstruct_result1032
									p.write(formatFloat64(unwrapped1033))
								} else {
									_dollar_dollar := msg
									var _t1610 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1610 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1030 := _t1610
									if deconstruct_result1030 != nil {
										unwrapped1031 := *deconstruct_result1030
										p.write(fmt.Sprintf("%du32", unwrapped1031))
									} else {
										_dollar_dollar := msg
										var _t1611 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1611 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1028 := _t1611
										if deconstruct_result1028 != nil {
											unwrapped1029 := deconstruct_result1028
											p.write(p.formatUint128(unwrapped1029))
										} else {
											_dollar_dollar := msg
											var _t1612 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1612 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1026 := _t1612
											if deconstruct_result1026 != nil {
												unwrapped1027 := deconstruct_result1026
												p.write(p.formatInt128(unwrapped1027))
											} else {
												_dollar_dollar := msg
												var _t1613 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1613 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1024 := _t1613
												if deconstruct_result1024 != nil {
													unwrapped1025 := deconstruct_result1024
													p.write(p.formatDecimal(unwrapped1025))
												} else {
													_dollar_dollar := msg
													var _t1614 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1614 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1022 := _t1614
													if deconstruct_result1022 != nil {
														unwrapped1023 := *deconstruct_result1022
														p.pretty_boolean_value(unwrapped1023)
													} else {
														fields1021 := msg
														_ = fields1021
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
	flat1052 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1052 != nil {
		p.write(*flat1052)
		return nil
	} else {
		_dollar_dollar := msg
		fields1047 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1048 := fields1047
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1049 := unwrapped_fields1048[0].(int64)
		p.write(fmt.Sprintf("%d", field1049))
		p.newline()
		field1050 := unwrapped_fields1048[1].(int64)
		p.write(fmt.Sprintf("%d", field1050))
		p.newline()
		field1051 := unwrapped_fields1048[2].(int64)
		p.write(fmt.Sprintf("%d", field1051))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1063 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1063 != nil {
		p.write(*flat1063)
		return nil
	} else {
		_dollar_dollar := msg
		fields1053 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1054 := fields1053
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1055 := unwrapped_fields1054[0].(int64)
		p.write(fmt.Sprintf("%d", field1055))
		p.newline()
		field1056 := unwrapped_fields1054[1].(int64)
		p.write(fmt.Sprintf("%d", field1056))
		p.newline()
		field1057 := unwrapped_fields1054[2].(int64)
		p.write(fmt.Sprintf("%d", field1057))
		p.newline()
		field1058 := unwrapped_fields1054[3].(int64)
		p.write(fmt.Sprintf("%d", field1058))
		p.newline()
		field1059 := unwrapped_fields1054[4].(int64)
		p.write(fmt.Sprintf("%d", field1059))
		p.newline()
		field1060 := unwrapped_fields1054[5].(int64)
		p.write(fmt.Sprintf("%d", field1060))
		field1061 := unwrapped_fields1054[6].(*int64)
		if field1061 != nil {
			p.newline()
			opt_val1062 := *field1061
			p.write(fmt.Sprintf("%d", opt_val1062))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1068 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1068 != nil {
		p.write(*flat1068)
		return nil
	} else {
		_dollar_dollar := msg
		fields1064 := _dollar_dollar.GetArgs()
		unwrapped_fields1065 := fields1064
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1065) == 0) {
			p.newline()
			for i1067, elem1066 := range unwrapped_fields1065 {
				if (i1067 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1066)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1073 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1073 != nil {
		p.write(*flat1073)
		return nil
	} else {
		_dollar_dollar := msg
		fields1069 := _dollar_dollar.GetArgs()
		unwrapped_fields1070 := fields1069
		p.write("(")
		p.write("or")
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

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1076 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1076 != nil {
		p.write(*flat1076)
		return nil
	} else {
		_dollar_dollar := msg
		fields1074 := _dollar_dollar.GetArg()
		unwrapped_fields1075 := fields1074
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1075)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1082 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1082 != nil {
		p.write(*flat1082)
		return nil
	} else {
		_dollar_dollar := msg
		fields1077 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1078 := fields1077
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1079 := unwrapped_fields1078[0].(string)
		p.pretty_name(field1079)
		p.newline()
		field1080 := unwrapped_fields1078[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1080)
		p.newline()
		field1081 := unwrapped_fields1078[2].([]*pb.Term)
		p.pretty_terms(field1081)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1084 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1084 != nil {
		p.write(*flat1084)
		return nil
	} else {
		fields1083 := msg
		p.write(":")
		p.write(fields1083)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		fields1085 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1085) == 0) {
			p.newline()
			for i1087, elem1086 := range fields1085 {
				if (i1087 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1086)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1095 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1095 != nil {
		p.write(*flat1095)
		return nil
	} else {
		_dollar_dollar := msg
		fields1089 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1090 := fields1089
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1091 := unwrapped_fields1090[0].(*pb.RelationId)
		p.pretty_relation_id(field1091)
		field1092 := unwrapped_fields1090[1].([]*pb.Term)
		if !(len(field1092) == 0) {
			p.newline()
			for i1094, elem1093 := range field1092 {
				if (i1094 > 0) {
					p.newline()
				}
				p.pretty_term(elem1093)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1096 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1097 := fields1096
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1098 := unwrapped_fields1097[0].(string)
		p.pretty_name(field1098)
		field1099 := unwrapped_fields1097[1].([]*pb.Term)
		if !(len(field1099) == 0) {
			p.newline()
			for i1101, elem1100 := range field1099 {
				if (i1101 > 0) {
					p.newline()
				}
				p.pretty_term(elem1100)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1615 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1615 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1117 := _t1615
		if guard_result1117 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1616 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1616 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1116 := _t1616
			if guard_result1116 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1617 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1617 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1115 := _t1617
				if guard_result1115 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1618 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1618 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1114 := _t1618
					if guard_result1114 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1619 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1619 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1113 := _t1619
						if guard_result1113 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1620 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1620 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1112 := _t1620
							if guard_result1112 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1621 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1621 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1111 := _t1621
								if guard_result1111 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1622 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1622 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1110 := _t1622
									if guard_result1110 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1623 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1623 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1109 := _t1623
										if guard_result1109 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1103 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1104 := fields1103
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1105 := unwrapped_fields1104[0].(string)
											p.pretty_name(field1105)
											field1106 := unwrapped_fields1104[1].([]*pb.RelTerm)
											if !(len(field1106) == 0) {
												p.newline()
												for i1108, elem1107 := range field1106 {
													if (i1108 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1107)
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
	flat1123 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1624 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1624 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1119 := _t1624
		unwrapped_fields1120 := fields1119
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1121 := unwrapped_fields1120[0].(*pb.Term)
		p.pretty_term(field1121)
		p.newline()
		field1122 := unwrapped_fields1120[1].(*pb.Term)
		p.pretty_term(field1122)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1128 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1128 != nil {
		p.write(*flat1128)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1625 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1124 := _t1625
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1133 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1133 != nil {
		p.write(*flat1133)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1626 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1626 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1129 := _t1626
		unwrapped_fields1130 := fields1129
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1627 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1134 := _t1627
		unwrapped_fields1135 := fields1134
		p.write("(")
		p.write(">")
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

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1628 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1628 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1139 := _t1628
		unwrapped_fields1140 := fields1139
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1149 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1149 != nil {
		p.write(*flat1149)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1629 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1629 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1144 := _t1629
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1146 := unwrapped_fields1145[0].(*pb.Term)
		p.pretty_term(field1146)
		p.newline()
		field1147 := unwrapped_fields1145[1].(*pb.Term)
		p.pretty_term(field1147)
		p.newline()
		field1148 := unwrapped_fields1145[2].(*pb.Term)
		p.pretty_term(field1148)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1155 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1155 != nil {
		p.write(*flat1155)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1630 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1630 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1150 := _t1630
		unwrapped_fields1151 := fields1150
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1152 := unwrapped_fields1151[0].(*pb.Term)
		p.pretty_term(field1152)
		p.newline()
		field1153 := unwrapped_fields1151[1].(*pb.Term)
		p.pretty_term(field1153)
		p.newline()
		field1154 := unwrapped_fields1151[2].(*pb.Term)
		p.pretty_term(field1154)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1631 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1156 := _t1631
		unwrapped_fields1157 := fields1156
		p.write("(")
		p.write("*")
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

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1632 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1632 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1162 := _t1632
		unwrapped_fields1163 := fields1162
		p.write("(")
		p.write("/")
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

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1633 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1633 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1170 := _t1633
		if deconstruct_result1170 != nil {
			unwrapped1171 := deconstruct_result1170
			p.pretty_specialized_value(unwrapped1171)
		} else {
			_dollar_dollar := msg
			var _t1634 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1634 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1168 := _t1634
			if deconstruct_result1168 != nil {
				unwrapped1169 := deconstruct_result1168
				p.pretty_term(unwrapped1169)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		fields1173 := msg
		p.write("#")
		p.pretty_raw_value(fields1173)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1181 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		_dollar_dollar := msg
		fields1175 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1176 := fields1175
		p.write("(")
		p.write("relatom")
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
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		fields1182 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1183 := fields1182
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1184 := unwrapped_fields1183[0].(*pb.Term)
		p.pretty_term(field1184)
		p.newline()
		field1185 := unwrapped_fields1183[1].(*pb.Term)
		p.pretty_term(field1185)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		fields1187 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1187) == 0) {
			p.newline()
			for i1189, elem1188 := range fields1187 {
				if (i1189 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1188)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1197 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1197 != nil {
		p.write(*flat1197)
		return nil
	} else {
		_dollar_dollar := msg
		fields1191 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1192 := fields1191
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1193 := unwrapped_fields1192[0].(string)
		p.pretty_name(field1193)
		field1194 := unwrapped_fields1192[1].([]*pb.Value)
		if !(len(field1194) == 0) {
			p.newline()
			for i1196, elem1195 := range field1194 {
				if (i1196 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1195)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1204 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		_dollar_dollar := msg
		fields1198 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1199 := fields1198
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1200 := unwrapped_fields1199[0].([]*pb.RelationId)
		if !(len(field1200) == 0) {
			p.newline()
			for i1202, elem1201 := range field1200 {
				if (i1202 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1201)
			}
		}
		p.newline()
		field1203 := unwrapped_fields1199[1].(*pb.Script)
		p.pretty_script(field1203)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_dollar_dollar := msg
		fields1205 := _dollar_dollar.GetConstructs()
		unwrapped_fields1206 := fields1205
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1206) == 0) {
			p.newline()
			for i1208, elem1207 := range unwrapped_fields1206 {
				if (i1208 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1207)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1635 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1212 := _t1635
		if deconstruct_result1212 != nil {
			unwrapped1213 := deconstruct_result1212
			p.pretty_loop(unwrapped1213)
		} else {
			_dollar_dollar := msg
			var _t1636 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1636 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1210 := _t1636
			if deconstruct_result1210 != nil {
				unwrapped1211 := deconstruct_result1210
				p.pretty_instruction(unwrapped1211)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		_dollar_dollar := msg
		fields1215 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1216 := fields1215
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1217 := unwrapped_fields1216[0].([]*pb.Instruction)
		p.pretty_init(field1217)
		p.newline()
		field1218 := unwrapped_fields1216[1].(*pb.Script)
		p.pretty_script(field1218)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1223 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		fields1220 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1220) == 0) {
			p.newline()
			for i1222, elem1221 := range fields1220 {
				if (i1222 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1221)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1637 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1232 := _t1637
		if deconstruct_result1232 != nil {
			unwrapped1233 := deconstruct_result1232
			p.pretty_assign(unwrapped1233)
		} else {
			_dollar_dollar := msg
			var _t1638 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1638 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1230 := _t1638
			if deconstruct_result1230 != nil {
				unwrapped1231 := deconstruct_result1230
				p.pretty_upsert(unwrapped1231)
			} else {
				_dollar_dollar := msg
				var _t1639 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1639 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1228 := _t1639
				if deconstruct_result1228 != nil {
					unwrapped1229 := deconstruct_result1228
					p.pretty_break(unwrapped1229)
				} else {
					_dollar_dollar := msg
					var _t1640 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1640 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1226 := _t1640
					if deconstruct_result1226 != nil {
						unwrapped1227 := deconstruct_result1226
						p.pretty_monoid_def(unwrapped1227)
					} else {
						_dollar_dollar := msg
						var _t1641 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1641 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1224 := _t1641
						if deconstruct_result1224 != nil {
							unwrapped1225 := deconstruct_result1224
							p.pretty_monus_def(unwrapped1225)
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
	flat1241 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1241 != nil {
		p.write(*flat1241)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1642 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1642 = _dollar_dollar.GetAttrs()
		}
		fields1235 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1642}
		unwrapped_fields1236 := fields1235
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1237 := unwrapped_fields1236[0].(*pb.RelationId)
		p.pretty_relation_id(field1237)
		p.newline()
		field1238 := unwrapped_fields1236[1].(*pb.Abstraction)
		p.pretty_abstraction(field1238)
		field1239 := unwrapped_fields1236[2].([]*pb.Attribute)
		if field1239 != nil {
			p.newline()
			opt_val1240 := field1239
			p.pretty_attrs(opt_val1240)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1248 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1248 != nil {
		p.write(*flat1248)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1643 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1643 = _dollar_dollar.GetAttrs()
		}
		fields1242 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1643}
		unwrapped_fields1243 := fields1242
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1244 := unwrapped_fields1243[0].(*pb.RelationId)
		p.pretty_relation_id(field1244)
		p.newline()
		field1245 := unwrapped_fields1243[1].([]interface{})
		p.pretty_abstraction_with_arity(field1245)
		field1246 := unwrapped_fields1243[2].([]*pb.Attribute)
		if field1246 != nil {
			p.newline()
			opt_val1247 := field1246
			p.pretty_attrs(opt_val1247)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_dollar_dollar := msg
		_t1644 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1249 := []interface{}{_t1644, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1250 := fields1249
		p.write("(")
		p.indent()
		field1251 := unwrapped_fields1250[0].([]interface{})
		p.pretty_bindings(field1251)
		p.newline()
		field1252 := unwrapped_fields1250[1].(*pb.Formula)
		p.pretty_formula(field1252)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1260 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1260 != nil {
		p.write(*flat1260)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1645 = _dollar_dollar.GetAttrs()
		}
		fields1254 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1645}
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1256 := unwrapped_fields1255[0].(*pb.RelationId)
		p.pretty_relation_id(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].(*pb.Abstraction)
		p.pretty_abstraction(field1257)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1268 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1268 != nil {
		p.write(*flat1268)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1646 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1646 = _dollar_dollar.GetAttrs()
		}
		fields1261 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1646}
		unwrapped_fields1262 := fields1261
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1263 := unwrapped_fields1262[0].(*pb.Monoid)
		p.pretty_monoid(field1263)
		p.newline()
		field1264 := unwrapped_fields1262[1].(*pb.RelationId)
		p.pretty_relation_id(field1264)
		p.newline()
		field1265 := unwrapped_fields1262[2].([]interface{})
		p.pretty_abstraction_with_arity(field1265)
		field1266 := unwrapped_fields1262[3].([]*pb.Attribute)
		if field1266 != nil {
			p.newline()
			opt_val1267 := field1266
			p.pretty_attrs(opt_val1267)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1277 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1647 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1275 := _t1647
		if deconstruct_result1275 != nil {
			unwrapped1276 := deconstruct_result1275
			p.pretty_or_monoid(unwrapped1276)
		} else {
			_dollar_dollar := msg
			var _t1648 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1648 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1273 := _t1648
			if deconstruct_result1273 != nil {
				unwrapped1274 := deconstruct_result1273
				p.pretty_min_monoid(unwrapped1274)
			} else {
				_dollar_dollar := msg
				var _t1649 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1649 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1271 := _t1649
				if deconstruct_result1271 != nil {
					unwrapped1272 := deconstruct_result1271
					p.pretty_max_monoid(unwrapped1272)
				} else {
					_dollar_dollar := msg
					var _t1650 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1650 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1269 := _t1650
					if deconstruct_result1269 != nil {
						unwrapped1270 := deconstruct_result1269
						p.pretty_sum_monoid(unwrapped1270)
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
	fields1278 := msg
	_ = fields1278
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		_dollar_dollar := msg
		fields1279 := _dollar_dollar.GetType()
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1280)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		_dollar_dollar := msg
		fields1282 := _dollar_dollar.GetType()
		unwrapped_fields1283 := fields1282
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1283)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1287 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1287 != nil {
		p.write(*flat1287)
		return nil
	} else {
		_dollar_dollar := msg
		fields1285 := _dollar_dollar.GetType()
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1286)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1295 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1295 != nil {
		p.write(*flat1295)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1651 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1651 = _dollar_dollar.GetAttrs()
		}
		fields1288 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1651}
		unwrapped_fields1289 := fields1288
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1290 := unwrapped_fields1289[0].(*pb.Monoid)
		p.pretty_monoid(field1290)
		p.newline()
		field1291 := unwrapped_fields1289[1].(*pb.RelationId)
		p.pretty_relation_id(field1291)
		p.newline()
		field1292 := unwrapped_fields1289[2].([]interface{})
		p.pretty_abstraction_with_arity(field1292)
		field1293 := unwrapped_fields1289[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1302 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1302 != nil {
		p.write(*flat1302)
		return nil
	} else {
		_dollar_dollar := msg
		fields1296 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1297 := fields1296
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1298 := unwrapped_fields1297[0].(*pb.RelationId)
		p.pretty_relation_id(field1298)
		p.newline()
		field1299 := unwrapped_fields1297[1].(*pb.Abstraction)
		p.pretty_abstraction(field1299)
		p.newline()
		field1300 := unwrapped_fields1297[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1300)
		p.newline()
		field1301 := unwrapped_fields1297[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1301)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1306 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1306 != nil {
		p.write(*flat1306)
		return nil
	} else {
		fields1303 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1303) == 0) {
			p.newline()
			for i1305, elem1304 := range fields1303 {
				if (i1305 > 0) {
					p.newline()
				}
				p.pretty_var(elem1304)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		fields1307 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1307) == 0) {
			p.newline()
			for i1309, elem1308 := range fields1307 {
				if (i1309 > 0) {
					p.newline()
				}
				p.pretty_var(elem1308)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1319 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1319 != nil {
		p.write(*flat1319)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1652 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1652 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1317 := _t1652
		if deconstruct_result1317 != nil {
			unwrapped1318 := deconstruct_result1317
			p.pretty_edb(unwrapped1318)
		} else {
			_dollar_dollar := msg
			var _t1653 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1653 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1315 := _t1653
			if deconstruct_result1315 != nil {
				unwrapped1316 := deconstruct_result1315
				p.pretty_betree_relation(unwrapped1316)
			} else {
				_dollar_dollar := msg
				var _t1654 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1654 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1313 := _t1654
				if deconstruct_result1313 != nil {
					unwrapped1314 := deconstruct_result1313
					p.pretty_csv_data(unwrapped1314)
				} else {
					_dollar_dollar := msg
					var _t1655 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1655 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1311 := _t1655
					if deconstruct_result1311 != nil {
						unwrapped1312 := deconstruct_result1311
						p.pretty_iceberg_data(unwrapped1312)
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
	flat1325 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1325 != nil {
		p.write(*flat1325)
		return nil
	} else {
		_dollar_dollar := msg
		fields1320 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1321 := fields1320
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1322 := unwrapped_fields1321[0].(*pb.RelationId)
		p.pretty_relation_id(field1322)
		p.newline()
		field1323 := unwrapped_fields1321[1].([]string)
		p.pretty_edb_path(field1323)
		p.newline()
		field1324 := unwrapped_fields1321[2].([]*pb.Type)
		p.pretty_edb_types(field1324)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		fields1326 := msg
		p.write("[")
		p.indent()
		for i1328, elem1327 := range fields1326 {
			if (i1328 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1327))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1333 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1333 != nil {
		p.write(*flat1333)
		return nil
	} else {
		fields1330 := msg
		p.write("[")
		p.indent()
		for i1332, elem1331 := range fields1330 {
			if (i1332 > 0) {
				p.newline()
			}
			p.pretty_type(elem1331)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1338 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1338 != nil {
		p.write(*flat1338)
		return nil
	} else {
		_dollar_dollar := msg
		fields1334 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1335 := fields1334
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1336 := unwrapped_fields1335[0].(*pb.RelationId)
		p.pretty_relation_id(field1336)
		p.newline()
		field1337 := unwrapped_fields1335[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1337)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1344 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1344 != nil {
		p.write(*flat1344)
		return nil
	} else {
		_dollar_dollar := msg
		_t1656 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1339 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1656}
		unwrapped_fields1340 := fields1339
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1341 := unwrapped_fields1340[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1341)
		p.newline()
		field1342 := unwrapped_fields1340[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1342)
		p.newline()
		field1343 := unwrapped_fields1340[2].([][]interface{})
		p.pretty_config_dict(field1343)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1348 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1348 != nil {
		p.write(*flat1348)
		return nil
	} else {
		fields1345 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1345) == 0) {
			p.newline()
			for i1347, elem1346 := range fields1345 {
				if (i1347 > 0) {
					p.newline()
				}
				p.pretty_type(elem1346)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1352 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1352 != nil {
		p.write(*flat1352)
		return nil
	} else {
		fields1349 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1349) == 0) {
			p.newline()
			for i1351, elem1350 := range fields1349 {
				if (i1351 > 0) {
					p.newline()
				}
				p.pretty_type(elem1350)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1359 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1359 != nil {
		p.write(*flat1359)
		return nil
	} else {
		_dollar_dollar := msg
		fields1353 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1354 := fields1353
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1355 := unwrapped_fields1354[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1355)
		p.newline()
		field1356 := unwrapped_fields1354[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1356)
		p.newline()
		field1357 := unwrapped_fields1354[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1357)
		p.newline()
		field1358 := unwrapped_fields1354[3].(string)
		p.pretty_csv_asof(field1358)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1366 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1366 != nil {
		p.write(*flat1366)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1657 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1657 = _dollar_dollar.GetPaths()
		}
		var _t1658 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1658 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1360 := []interface{}{_t1657, _t1658}
		unwrapped_fields1361 := fields1360
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1362 := unwrapped_fields1361[0].([]string)
		if field1362 != nil {
			p.newline()
			opt_val1363 := field1362
			p.pretty_csv_locator_paths(opt_val1363)
		}
		field1364 := unwrapped_fields1361[1].(*string)
		if field1364 != nil {
			p.newline()
			opt_val1365 := *field1364
			p.pretty_csv_locator_inline_data(opt_val1365)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1370 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1370 != nil {
		p.write(*flat1370)
		return nil
	} else {
		fields1367 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1367) == 0) {
			p.newline()
			for i1369, elem1368 := range fields1367 {
				if (i1369 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1368))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1372 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1372 != nil {
		p.write(*flat1372)
		return nil
	} else {
		fields1371 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1371))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1375 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1375 != nil {
		p.write(*flat1375)
		return nil
	} else {
		_dollar_dollar := msg
		_t1659 := p.deconstruct_csv_config(_dollar_dollar)
		fields1373 := _t1659
		unwrapped_fields1374 := fields1373
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1374)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1379 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1379 != nil {
		p.write(*flat1379)
		return nil
	} else {
		fields1376 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1376) == 0) {
			p.newline()
			for i1378, elem1377 := range fields1376 {
				if (i1378 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1377)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1388 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1388 != nil {
		p.write(*flat1388)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1660 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1660 = _dollar_dollar.GetTargetId()
		}
		fields1380 := []interface{}{_dollar_dollar.GetColumnPath(), _t1660, _dollar_dollar.GetTypes()}
		unwrapped_fields1381 := fields1380
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1382 := unwrapped_fields1381[0].([]string)
		p.pretty_gnf_column_path(field1382)
		field1383 := unwrapped_fields1381[1].(*pb.RelationId)
		if field1383 != nil {
			p.newline()
			opt_val1384 := field1383
			p.pretty_relation_id(opt_val1384)
		}
		p.newline()
		p.write("[")
		field1385 := unwrapped_fields1381[2].([]*pb.Type)
		for i1387, elem1386 := range field1385 {
			if (i1387 > 0) {
				p.newline()
			}
			p.pretty_type(elem1386)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1395 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1395 != nil {
		p.write(*flat1395)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1661 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1393 := _t1661
		if deconstruct_result1393 != nil {
			unwrapped1394 := *deconstruct_result1393
			p.write(p.formatStringValue(unwrapped1394))
		} else {
			_dollar_dollar := msg
			var _t1662 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1662 = _dollar_dollar
			}
			deconstruct_result1389 := _t1662
			if deconstruct_result1389 != nil {
				unwrapped1390 := deconstruct_result1389
				p.write("[")
				p.indent()
				for i1392, elem1391 := range unwrapped1390 {
					if (i1392 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1391))
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
	flat1397 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1397 != nil {
		p.write(*flat1397)
		return nil
	} else {
		fields1396 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1396))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		_dollar_dollar := msg
		_t1663 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1398 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1663}
		unwrapped_fields1399 := fields1398
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1400 := unwrapped_fields1399[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1400)
		p.newline()
		field1401 := unwrapped_fields1399[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1401)
		p.newline()
		field1402 := unwrapped_fields1399[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1402)
		field1403 := unwrapped_fields1399[3].(*string)
		if field1403 != nil {
			p.newline()
			opt_val1404 := *field1403
			p.pretty_iceberg_to_snapshot(opt_val1404)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		_dollar_dollar := msg
		fields1406 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1407 := fields1406
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1408 := unwrapped_fields1407[0].(string)
		p.write(p.formatStringValue(field1408))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1409 := unwrapped_fields1407[1].([]string)
		if !(len(field1409) == 0) {
			p.newline()
			for i1411, elem1410 := range field1409 {
				if (i1411 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1410))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1412 := unwrapped_fields1407[2].(string)
		p.write(p.formatStringValue(field1412))
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1425 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		_dollar_dollar := msg
		_t1664 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1414 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1664, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1415 := fields1414
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1416 := unwrapped_fields1415[0].(string)
		p.write(p.formatStringValue(field1416))
		p.dedent()
		p.write(")")
		field1417 := unwrapped_fields1415[1].(*string)
		if field1417 != nil {
			p.newline()
			opt_val1418 := *field1417
			p.pretty_iceberg_catalog_config_scope(opt_val1418)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1419 := unwrapped_fields1415[2].([][]interface{})
		if !(len(field1419) == 0) {
			p.newline()
			for i1421, elem1420 := range field1419 {
				if (i1421 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1420)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1422 := unwrapped_fields1415[3].([][]interface{})
		if !(len(field1422) == 0) {
			p.newline()
			for i1424, elem1423 := range field1422 {
				if (i1424 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1423)
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
	flat1427 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1427 != nil {
		p.write(*flat1427)
		return nil
	} else {
		fields1426 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1426))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		_dollar_dollar := msg
		fields1428 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1429 := fields1428
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1430 := unwrapped_fields1429[0].(string)
		p.write(p.formatStringValue(field1430))
		p.newline()
		field1431 := unwrapped_fields1429[1].(string)
		p.write(p.formatStringValue(field1431))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1434 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1434 != nil {
		p.write(*flat1434)
		return nil
	} else {
		fields1433 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1433))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1437 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1437 != nil {
		p.write(*flat1437)
		return nil
	} else {
		_dollar_dollar := msg
		fields1435 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1436 := fields1435
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1436)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1442 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1442 != nil {
		p.write(*flat1442)
		return nil
	} else {
		_dollar_dollar := msg
		fields1438 := _dollar_dollar.GetRelations()
		unwrapped_fields1439 := fields1438
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1439) == 0) {
			p.newline()
			for i1441, elem1440 := range unwrapped_fields1439 {
				if (i1441 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1440)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1447 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1447 != nil {
		p.write(*flat1447)
		return nil
	} else {
		_dollar_dollar := msg
		fields1443 := _dollar_dollar.GetMappings()
		unwrapped_fields1444 := fields1443
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1444) == 0) {
			p.newline()
			for i1446, elem1445 := range unwrapped_fields1444 {
				if (i1446 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1445)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1452 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1452 != nil {
		p.write(*flat1452)
		return nil
	} else {
		_dollar_dollar := msg
		fields1448 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1449 := fields1448
		field1450 := unwrapped_fields1449[0].([]string)
		p.pretty_edb_path(field1450)
		p.write(" ")
		field1451 := unwrapped_fields1449[1].(*pb.RelationId)
		p.pretty_relation_id(field1451)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1456 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1456 != nil {
		p.write(*flat1456)
		return nil
	} else {
		fields1453 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1453) == 0) {
			p.newline()
			for i1455, elem1454 := range fields1453 {
				if (i1455 > 0) {
					p.newline()
				}
				p.pretty_read(elem1454)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1467 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1467 != nil {
		p.write(*flat1467)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1665 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1665 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1465 := _t1665
		if deconstruct_result1465 != nil {
			unwrapped1466 := deconstruct_result1465
			p.pretty_demand(unwrapped1466)
		} else {
			_dollar_dollar := msg
			var _t1666 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1666 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1463 := _t1666
			if deconstruct_result1463 != nil {
				unwrapped1464 := deconstruct_result1463
				p.pretty_output(unwrapped1464)
			} else {
				_dollar_dollar := msg
				var _t1667 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1667 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1461 := _t1667
				if deconstruct_result1461 != nil {
					unwrapped1462 := deconstruct_result1461
					p.pretty_what_if(unwrapped1462)
				} else {
					_dollar_dollar := msg
					var _t1668 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1668 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1459 := _t1668
					if deconstruct_result1459 != nil {
						unwrapped1460 := deconstruct_result1459
						p.pretty_abort(unwrapped1460)
					} else {
						_dollar_dollar := msg
						var _t1669 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1669 = _dollar_dollar.GetExport()
						}
						deconstruct_result1457 := _t1669
						if deconstruct_result1457 != nil {
							unwrapped1458 := deconstruct_result1457
							p.pretty_export(unwrapped1458)
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
	flat1470 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		_dollar_dollar := msg
		fields1468 := _dollar_dollar.GetRelationId()
		unwrapped_fields1469 := fields1468
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1469)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1475 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1475 != nil {
		p.write(*flat1475)
		return nil
	} else {
		_dollar_dollar := msg
		fields1471 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1472 := fields1471
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1473 := unwrapped_fields1472[0].(string)
		p.pretty_name(field1473)
		p.newline()
		field1474 := unwrapped_fields1472[1].(*pb.RelationId)
		p.pretty_relation_id(field1474)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		_dollar_dollar := msg
		fields1476 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1477 := fields1476
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1478 := unwrapped_fields1477[0].(string)
		p.pretty_name(field1478)
		p.newline()
		field1479 := unwrapped_fields1477[1].(*pb.Epoch)
		p.pretty_epoch(field1479)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1486 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1486 != nil {
		p.write(*flat1486)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1670 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1670 = ptr(_dollar_dollar.GetName())
		}
		fields1481 := []interface{}{_t1670, _dollar_dollar.GetRelationId()}
		unwrapped_fields1482 := fields1481
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1483 := unwrapped_fields1482[0].(*string)
		if field1483 != nil {
			p.newline()
			opt_val1484 := *field1483
			p.pretty_name(opt_val1484)
		}
		p.newline()
		field1485 := unwrapped_fields1482[1].(*pb.RelationId)
		p.pretty_relation_id(field1485)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1491 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1491 != nil {
		p.write(*flat1491)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1671 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1489 := _t1671
		if deconstruct_result1489 != nil {
			unwrapped1490 := deconstruct_result1489
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1490)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1672 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1672 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1487 := _t1672
			if deconstruct_result1487 != nil {
				unwrapped1488 := deconstruct_result1487
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1488)
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
	flat1502 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1502 != nil {
		p.write(*flat1502)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1673 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1673 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1497 := _t1673
		if deconstruct_result1497 != nil {
			unwrapped1498 := deconstruct_result1497
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1499 := unwrapped1498[0].(string)
			p.pretty_export_csv_path(field1499)
			p.newline()
			field1500 := unwrapped1498[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1500)
			p.newline()
			field1501 := unwrapped1498[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1501)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1674 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1675 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1674 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1675}
			}
			deconstruct_result1492 := _t1674
			if deconstruct_result1492 != nil {
				unwrapped1493 := deconstruct_result1492
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1494 := unwrapped1493[0].(string)
				p.pretty_export_csv_path(field1494)
				p.newline()
				field1495 := unwrapped1493[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1495)
				p.newline()
				field1496 := unwrapped1493[2].([][]interface{})
				p.pretty_config_dict(field1496)
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
	flat1504 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		fields1503 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1503))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1511 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1511 != nil {
		p.write(*flat1511)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1676 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1676 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1507 := _t1676
		if deconstruct_result1507 != nil {
			unwrapped1508 := deconstruct_result1507
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1508) == 0) {
				p.newline()
				for i1510, elem1509 := range unwrapped1508 {
					if (i1510 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1509)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1677 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1677 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1505 := _t1677
			if deconstruct_result1505 != nil {
				unwrapped1506 := deconstruct_result1505
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1506)
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
	flat1516 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1516 != nil {
		p.write(*flat1516)
		return nil
	} else {
		_dollar_dollar := msg
		fields1512 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1513 := fields1512
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1514 := unwrapped_fields1513[0].(string)
		p.write(p.formatStringValue(field1514))
		p.newline()
		field1515 := unwrapped_fields1513[1].(*pb.RelationId)
		p.pretty_relation_id(field1515)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1520 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1520 != nil {
		p.write(*flat1520)
		return nil
	} else {
		fields1517 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1517) == 0) {
			p.newline()
			for i1519, elem1518 := range fields1517 {
				if (i1519 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1518)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1534 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1534 != nil {
		p.write(*flat1534)
		return nil
	} else {
		_dollar_dollar := msg
		_t1678 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1521 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1678}
		unwrapped_fields1522 := fields1521
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1523 := unwrapped_fields1522[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1523)
		p.newline()
		field1524 := unwrapped_fields1522[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1524)
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_def")
		p.newline()
		field1525 := unwrapped_fields1522[2].(*pb.RelationId)
		p.pretty_relation_id(field1525)
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("columns")
		field1526 := unwrapped_fields1522[3].([]*pb.ExportIcebergColumn)
		if !(len(field1526) == 0) {
			p.newline()
			for i1528, elem1527 := range field1526 {
				if (i1528 > 0) {
					p.newline()
				}
				p.pretty_export_iceberg_column(elem1527)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_properties")
		field1529 := unwrapped_fields1522[4].([][]interface{})
		if !(len(field1529) == 0) {
			p.newline()
			for i1531, elem1530 := range field1529 {
				if (i1531 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1530)
			}
		}
		p.dedent()
		p.write(")")
		field1532 := unwrapped_fields1522[5].([][]interface{})
		if field1532 != nil {
			p.newline()
			opt_val1533 := field1532
			p.pretty_config_dict(opt_val1533)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column(msg *pb.ExportIcebergColumn) interface{} {
	flat1539 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column(msg) })
	if flat1539 != nil {
		p.write(*flat1539)
		return nil
	} else {
		_dollar_dollar := msg
		fields1535 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetNullable()}
		unwrapped_fields1536 := fields1535
		p.write("(")
		p.write("iceberg_column")
		p.indentSexp()
		p.newline()
		field1537 := unwrapped_fields1536[0].(string)
		p.write(p.formatStringValue(field1537))
		p.newline()
		field1538 := unwrapped_fields1536[1].(bool)
		p.pretty_boolean_value(field1538)
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
		_t1723 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1723)
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
