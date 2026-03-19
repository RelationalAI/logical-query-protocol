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
	_t1597 := &pb.Value{}
	_t1597.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1597
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1598 := &pb.Value{}
	_t1598.Value = &pb.Value_IntValue{IntValue: v}
	return _t1598
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1599 := &pb.Value{}
	_t1599.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1599
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1600 := &pb.Value{}
	_t1600.Value = &pb.Value_StringValue{StringValue: v}
	return _t1600
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1601 := &pb.Value{}
	_t1601.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1601
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1602 := &pb.Value{}
	_t1602.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1602
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1603 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1603})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1604 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1604})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1605 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1605})
			}
		}
	}
	_t1606 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1606})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1607 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1607})
	_t1608 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1608})
	if msg.GetNewLine() != "" {
		_t1609 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1609})
	}
	_t1610 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1610})
	_t1611 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1611})
	_t1612 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1612})
	if msg.GetComment() != "" {
		_t1613 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1613})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1614 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1614})
	}
	_t1615 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1615})
	_t1616 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1616})
	_t1617 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1617})
	if msg.GetPartitionSizeMb() != 0 {
		_t1618 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1618})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1619 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1619})
	_t1620 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1620})
	_t1621 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1621})
	_t1622 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1622})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1623 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1623})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1624 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1624})
		}
	}
	_t1625 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1625})
	_t1626 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1626})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1627 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1627})
	}
	if msg.Compression != nil {
		_t1628 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1628})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1629 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1629})
	}
	if msg.SyntaxMissingString != nil {
		_t1630 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1630})
	}
	if msg.SyntaxDelim != nil {
		_t1631 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1631})
	}
	if msg.SyntaxQuotechar != nil {
		_t1632 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1632})
	}
	if msg.SyntaxEscapechar != nil {
		_t1633 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1633})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1634 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1634})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1635 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1635})
	}
	if msg.GetCompression() != "" {
		_t1636 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1636})
	}
	var _t1637 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1637
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_properties_optional(msg *pb.IcebergCatalogProperties) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Token != "" {
		_t1638 := p._make_value_string(*msg.Token)
		result = append(result, []interface{}{"token", _t1638})
	}
	if *msg.Credential != "" {
		_t1639 := p._make_value_string(*msg.Credential)
		result = append(result, []interface{}{"credential", _t1639})
	}
	var _t1640 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1640
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1641 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1641
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
	flat739 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat739 != nil {
		p.write(*flat739)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1460 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1460 = _dollar_dollar.GetConfigure()
		}
		var _t1461 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1461 = _dollar_dollar.GetSync()
		}
		fields730 := []interface{}{_t1460, _t1461, _dollar_dollar.GetEpochs()}
		unwrapped_fields731 := fields730
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field732 := unwrapped_fields731[0].(*pb.Configure)
		if field732 != nil {
			p.newline()
			opt_val733 := field732
			p.pretty_configure(opt_val733)
		}
		field734 := unwrapped_fields731[1].(*pb.Sync)
		if field734 != nil {
			p.newline()
			opt_val735 := field734
			p.pretty_sync(opt_val735)
		}
		field736 := unwrapped_fields731[2].([]*pb.Epoch)
		if !(len(field736) == 0) {
			p.newline()
			for i738, elem737 := range field736 {
				if (i738 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem737)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat742 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat742 != nil {
		p.write(*flat742)
		return nil
	} else {
		_dollar_dollar := msg
		_t1462 := p.deconstruct_configure(_dollar_dollar)
		fields740 := _t1462
		unwrapped_fields741 := fields740
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields741)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat746 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat746 != nil {
		p.write(*flat746)
		return nil
	} else {
		fields743 := msg
		p.write("{")
		p.indent()
		if !(len(fields743) == 0) {
			p.newline()
			for i745, elem744 := range fields743 {
				if (i745 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem744)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat751 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat751 != nil {
		p.write(*flat751)
		return nil
	} else {
		_dollar_dollar := msg
		fields747 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields748 := fields747
		p.write(":")
		field749 := unwrapped_fields748[0].(string)
		p.write(field749)
		p.write(" ")
		field750 := unwrapped_fields748[1].(*pb.Value)
		p.pretty_raw_value(field750)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat777 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat777 != nil {
		p.write(*flat777)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1463 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1463 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result775 := _t1463
		if deconstruct_result775 != nil {
			unwrapped776 := deconstruct_result775
			p.pretty_raw_date(unwrapped776)
		} else {
			_dollar_dollar := msg
			var _t1464 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1464 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result773 := _t1464
			if deconstruct_result773 != nil {
				unwrapped774 := deconstruct_result773
				p.pretty_raw_datetime(unwrapped774)
			} else {
				_dollar_dollar := msg
				var _t1465 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1465 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result771 := _t1465
				if deconstruct_result771 != nil {
					unwrapped772 := *deconstruct_result771
					p.write(p.formatStringValue(unwrapped772))
				} else {
					_dollar_dollar := msg
					var _t1466 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1466 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result769 := _t1466
					if deconstruct_result769 != nil {
						unwrapped770 := *deconstruct_result769
						p.write(fmt.Sprintf("%di32", unwrapped770))
					} else {
						_dollar_dollar := msg
						var _t1467 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1467 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result767 := _t1467
						if deconstruct_result767 != nil {
							unwrapped768 := *deconstruct_result767
							p.write(fmt.Sprintf("%d", unwrapped768))
						} else {
							_dollar_dollar := msg
							var _t1468 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1468 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result765 := _t1468
							if deconstruct_result765 != nil {
								unwrapped766 := *deconstruct_result765
								p.write(formatFloat32(unwrapped766))
							} else {
								_dollar_dollar := msg
								var _t1469 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1469 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result763 := _t1469
								if deconstruct_result763 != nil {
									unwrapped764 := *deconstruct_result763
									p.write(formatFloat64(unwrapped764))
								} else {
									_dollar_dollar := msg
									var _t1470 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1470 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result761 := _t1470
									if deconstruct_result761 != nil {
										unwrapped762 := *deconstruct_result761
										p.write(fmt.Sprintf("%du32", unwrapped762))
									} else {
										_dollar_dollar := msg
										var _t1471 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1471 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result759 := _t1471
										if deconstruct_result759 != nil {
											unwrapped760 := deconstruct_result759
											p.write(p.formatUint128(unwrapped760))
										} else {
											_dollar_dollar := msg
											var _t1472 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1472 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result757 := _t1472
											if deconstruct_result757 != nil {
												unwrapped758 := deconstruct_result757
												p.write(p.formatInt128(unwrapped758))
											} else {
												_dollar_dollar := msg
												var _t1473 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1473 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result755 := _t1473
												if deconstruct_result755 != nil {
													unwrapped756 := deconstruct_result755
													p.write(p.formatDecimal(unwrapped756))
												} else {
													_dollar_dollar := msg
													var _t1474 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1474 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result753 := _t1474
													if deconstruct_result753 != nil {
														unwrapped754 := *deconstruct_result753
														p.pretty_boolean_value(unwrapped754)
													} else {
														fields752 := msg
														_ = fields752
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
	flat783 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat783 != nil {
		p.write(*flat783)
		return nil
	} else {
		_dollar_dollar := msg
		fields778 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields779 := fields778
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field780 := unwrapped_fields779[0].(int64)
		p.write(fmt.Sprintf("%d", field780))
		p.newline()
		field781 := unwrapped_fields779[1].(int64)
		p.write(fmt.Sprintf("%d", field781))
		p.newline()
		field782 := unwrapped_fields779[2].(int64)
		p.write(fmt.Sprintf("%d", field782))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat794 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat794 != nil {
		p.write(*flat794)
		return nil
	} else {
		_dollar_dollar := msg
		fields784 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields785 := fields784
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field786 := unwrapped_fields785[0].(int64)
		p.write(fmt.Sprintf("%d", field786))
		p.newline()
		field787 := unwrapped_fields785[1].(int64)
		p.write(fmt.Sprintf("%d", field787))
		p.newline()
		field788 := unwrapped_fields785[2].(int64)
		p.write(fmt.Sprintf("%d", field788))
		p.newline()
		field789 := unwrapped_fields785[3].(int64)
		p.write(fmt.Sprintf("%d", field789))
		p.newline()
		field790 := unwrapped_fields785[4].(int64)
		p.write(fmt.Sprintf("%d", field790))
		p.newline()
		field791 := unwrapped_fields785[5].(int64)
		p.write(fmt.Sprintf("%d", field791))
		field792 := unwrapped_fields785[6].(*int64)
		if field792 != nil {
			p.newline()
			opt_val793 := *field792
			p.write(fmt.Sprintf("%d", opt_val793))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1475 []interface{}
	if _dollar_dollar {
		_t1475 = []interface{}{}
	}
	deconstruct_result797 := _t1475
	if deconstruct_result797 != nil {
		unwrapped798 := deconstruct_result797
		_ = unwrapped798
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1476 []interface{}
		if !(_dollar_dollar) {
			_t1476 = []interface{}{}
		}
		deconstruct_result795 := _t1476
		if deconstruct_result795 != nil {
			unwrapped796 := deconstruct_result795
			_ = unwrapped796
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat803 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat803 != nil {
		p.write(*flat803)
		return nil
	} else {
		_dollar_dollar := msg
		fields799 := _dollar_dollar.GetFragments()
		unwrapped_fields800 := fields799
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields800) == 0) {
			p.newline()
			for i802, elem801 := range unwrapped_fields800 {
				if (i802 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem801)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat806 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat806 != nil {
		p.write(*flat806)
		return nil
	} else {
		_dollar_dollar := msg
		fields804 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields805 := fields804
		p.write(":")
		p.write(unwrapped_fields805)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat813 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat813 != nil {
		p.write(*flat813)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1477 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1477 = _dollar_dollar.GetWrites()
		}
		var _t1478 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1478 = _dollar_dollar.GetReads()
		}
		fields807 := []interface{}{_t1477, _t1478}
		unwrapped_fields808 := fields807
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field809 := unwrapped_fields808[0].([]*pb.Write)
		if field809 != nil {
			p.newline()
			opt_val810 := field809
			p.pretty_epoch_writes(opt_val810)
		}
		field811 := unwrapped_fields808[1].([]*pb.Read)
		if field811 != nil {
			p.newline()
			opt_val812 := field811
			p.pretty_epoch_reads(opt_val812)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat817 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat817 != nil {
		p.write(*flat817)
		return nil
	} else {
		fields814 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields814) == 0) {
			p.newline()
			for i816, elem815 := range fields814 {
				if (i816 > 0) {
					p.newline()
				}
				p.pretty_write(elem815)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat826 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat826 != nil {
		p.write(*flat826)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1479 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1479 = _dollar_dollar.GetDefine()
		}
		deconstruct_result824 := _t1479
		if deconstruct_result824 != nil {
			unwrapped825 := deconstruct_result824
			p.pretty_define(unwrapped825)
		} else {
			_dollar_dollar := msg
			var _t1480 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1480 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result822 := _t1480
			if deconstruct_result822 != nil {
				unwrapped823 := deconstruct_result822
				p.pretty_undefine(unwrapped823)
			} else {
				_dollar_dollar := msg
				var _t1481 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1481 = _dollar_dollar.GetContext()
				}
				deconstruct_result820 := _t1481
				if deconstruct_result820 != nil {
					unwrapped821 := deconstruct_result820
					p.pretty_context(unwrapped821)
				} else {
					_dollar_dollar := msg
					var _t1482 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1482 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result818 := _t1482
					if deconstruct_result818 != nil {
						unwrapped819 := deconstruct_result818
						p.pretty_snapshot(unwrapped819)
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
	flat829 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat829 != nil {
		p.write(*flat829)
		return nil
	} else {
		_dollar_dollar := msg
		fields827 := _dollar_dollar.GetFragment()
		unwrapped_fields828 := fields827
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields828)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat836 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat836 != nil {
		p.write(*flat836)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields830 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields831 := fields830
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field832 := unwrapped_fields831[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field832)
		field833 := unwrapped_fields831[1].([]*pb.Declaration)
		if !(len(field833) == 0) {
			p.newline()
			for i835, elem834 := range field833 {
				if (i835 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem834)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat838 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat838 != nil {
		p.write(*flat838)
		return nil
	} else {
		fields837 := msg
		p.pretty_fragment_id(fields837)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat847 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat847 != nil {
		p.write(*flat847)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1483 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1483 = _dollar_dollar.GetDef()
		}
		deconstruct_result845 := _t1483
		if deconstruct_result845 != nil {
			unwrapped846 := deconstruct_result845
			p.pretty_def(unwrapped846)
		} else {
			_dollar_dollar := msg
			var _t1484 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1484 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result843 := _t1484
			if deconstruct_result843 != nil {
				unwrapped844 := deconstruct_result843
				p.pretty_algorithm(unwrapped844)
			} else {
				_dollar_dollar := msg
				var _t1485 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1485 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result841 := _t1485
				if deconstruct_result841 != nil {
					unwrapped842 := deconstruct_result841
					p.pretty_constraint(unwrapped842)
				} else {
					_dollar_dollar := msg
					var _t1486 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1486 = _dollar_dollar.GetData()
					}
					deconstruct_result839 := _t1486
					if deconstruct_result839 != nil {
						unwrapped840 := deconstruct_result839
						p.pretty_data(unwrapped840)
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
	flat854 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1487 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1487 = _dollar_dollar.GetAttrs()
		}
		fields848 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1487}
		unwrapped_fields849 := fields848
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field850 := unwrapped_fields849[0].(*pb.RelationId)
		p.pretty_relation_id(field850)
		p.newline()
		field851 := unwrapped_fields849[1].(*pb.Abstraction)
		p.pretty_abstraction(field851)
		field852 := unwrapped_fields849[2].([]*pb.Attribute)
		if field852 != nil {
			p.newline()
			opt_val853 := field852
			p.pretty_attrs(opt_val853)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat859 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat859 != nil {
		p.write(*flat859)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1488 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1489 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1488 = ptr(_t1489)
		}
		deconstruct_result857 := _t1488
		if deconstruct_result857 != nil {
			unwrapped858 := *deconstruct_result857
			p.write(":")
			p.write(unwrapped858)
		} else {
			_dollar_dollar := msg
			_t1490 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result855 := _t1490
			if deconstruct_result855 != nil {
				unwrapped856 := deconstruct_result855
				p.write(p.formatUint128(unwrapped856))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_dollar_dollar := msg
		_t1491 := p.deconstruct_bindings(_dollar_dollar)
		fields860 := []interface{}{_t1491, _dollar_dollar.GetValue()}
		unwrapped_fields861 := fields860
		p.write("(")
		p.indent()
		field862 := unwrapped_fields861[0].([]interface{})
		p.pretty_bindings(field862)
		p.newline()
		field863 := unwrapped_fields861[1].(*pb.Formula)
		p.pretty_formula(field863)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat872 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat872 != nil {
		p.write(*flat872)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1492 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1492 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields865 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1492}
		unwrapped_fields866 := fields865
		p.write("[")
		p.indent()
		field867 := unwrapped_fields866[0].([]*pb.Binding)
		for i869, elem868 := range field867 {
			if (i869 > 0) {
				p.newline()
			}
			p.pretty_binding(elem868)
		}
		field870 := unwrapped_fields866[1].([]*pb.Binding)
		if field870 != nil {
			p.newline()
			opt_val871 := field870
			p.pretty_value_bindings(opt_val871)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_dollar_dollar := msg
		fields873 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields874 := fields873
		field875 := unwrapped_fields874[0].(string)
		p.write(field875)
		p.write("::")
		field876 := unwrapped_fields874[1].(*pb.Type)
		p.pretty_type(field876)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1493 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1493 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result904 := _t1493
		if deconstruct_result904 != nil {
			unwrapped905 := deconstruct_result904
			p.pretty_unspecified_type(unwrapped905)
		} else {
			_dollar_dollar := msg
			var _t1494 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1494 = _dollar_dollar.GetStringType()
			}
			deconstruct_result902 := _t1494
			if deconstruct_result902 != nil {
				unwrapped903 := deconstruct_result902
				p.pretty_string_type(unwrapped903)
			} else {
				_dollar_dollar := msg
				var _t1495 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1495 = _dollar_dollar.GetIntType()
				}
				deconstruct_result900 := _t1495
				if deconstruct_result900 != nil {
					unwrapped901 := deconstruct_result900
					p.pretty_int_type(unwrapped901)
				} else {
					_dollar_dollar := msg
					var _t1496 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1496 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result898 := _t1496
					if deconstruct_result898 != nil {
						unwrapped899 := deconstruct_result898
						p.pretty_float_type(unwrapped899)
					} else {
						_dollar_dollar := msg
						var _t1497 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1497 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result896 := _t1497
						if deconstruct_result896 != nil {
							unwrapped897 := deconstruct_result896
							p.pretty_uint128_type(unwrapped897)
						} else {
							_dollar_dollar := msg
							var _t1498 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1498 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result894 := _t1498
							if deconstruct_result894 != nil {
								unwrapped895 := deconstruct_result894
								p.pretty_int128_type(unwrapped895)
							} else {
								_dollar_dollar := msg
								var _t1499 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1499 = _dollar_dollar.GetDateType()
								}
								deconstruct_result892 := _t1499
								if deconstruct_result892 != nil {
									unwrapped893 := deconstruct_result892
									p.pretty_date_type(unwrapped893)
								} else {
									_dollar_dollar := msg
									var _t1500 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1500 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result890 := _t1500
									if deconstruct_result890 != nil {
										unwrapped891 := deconstruct_result890
										p.pretty_datetime_type(unwrapped891)
									} else {
										_dollar_dollar := msg
										var _t1501 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1501 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result888 := _t1501
										if deconstruct_result888 != nil {
											unwrapped889 := deconstruct_result888
											p.pretty_missing_type(unwrapped889)
										} else {
											_dollar_dollar := msg
											var _t1502 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1502 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result886 := _t1502
											if deconstruct_result886 != nil {
												unwrapped887 := deconstruct_result886
												p.pretty_decimal_type(unwrapped887)
											} else {
												_dollar_dollar := msg
												var _t1503 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1503 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result884 := _t1503
												if deconstruct_result884 != nil {
													unwrapped885 := deconstruct_result884
													p.pretty_boolean_type(unwrapped885)
												} else {
													_dollar_dollar := msg
													var _t1504 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1504 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result882 := _t1504
													if deconstruct_result882 != nil {
														unwrapped883 := deconstruct_result882
														p.pretty_int32_type(unwrapped883)
													} else {
														_dollar_dollar := msg
														var _t1505 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1505 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result880 := _t1505
														if deconstruct_result880 != nil {
															unwrapped881 := deconstruct_result880
															p.pretty_float32_type(unwrapped881)
														} else {
															_dollar_dollar := msg
															var _t1506 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1506 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result878 := _t1506
															if deconstruct_result878 != nil {
																unwrapped879 := deconstruct_result878
																p.pretty_uint32_type(unwrapped879)
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
	fields907 := msg
	_ = fields907
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields908 := msg
	_ = fields908
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields909 := msg
	_ = fields909
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields910 := msg
	_ = fields910
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields911 := msg
	_ = fields911
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields912 := msg
	_ = fields912
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields913 := msg
	_ = fields913
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields914 := msg
	_ = fields914
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields915 := msg
	_ = fields915
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat920 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat920 != nil {
		p.write(*flat920)
		return nil
	} else {
		_dollar_dollar := msg
		fields916 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields917 := fields916
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field918 := unwrapped_fields917[0].(int64)
		p.write(fmt.Sprintf("%d", field918))
		p.newline()
		field919 := unwrapped_fields917[1].(int64)
		p.write(fmt.Sprintf("%d", field919))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields921 := msg
	_ = fields921
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields922 := msg
	_ = fields922
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields923 := msg
	_ = fields923
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields924 := msg
	_ = fields924
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat928 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat928 != nil {
		p.write(*flat928)
		return nil
	} else {
		fields925 := msg
		p.write("|")
		if !(len(fields925) == 0) {
			p.write(" ")
			for i927, elem926 := range fields925 {
				if (i927 > 0) {
					p.newline()
				}
				p.pretty_binding(elem926)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat955 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat955 != nil {
		p.write(*flat955)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1507 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1507 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result953 := _t1507
		if deconstruct_result953 != nil {
			unwrapped954 := deconstruct_result953
			p.pretty_true(unwrapped954)
		} else {
			_dollar_dollar := msg
			var _t1508 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1508 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result951 := _t1508
			if deconstruct_result951 != nil {
				unwrapped952 := deconstruct_result951
				p.pretty_false(unwrapped952)
			} else {
				_dollar_dollar := msg
				var _t1509 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1509 = _dollar_dollar.GetExists()
				}
				deconstruct_result949 := _t1509
				if deconstruct_result949 != nil {
					unwrapped950 := deconstruct_result949
					p.pretty_exists(unwrapped950)
				} else {
					_dollar_dollar := msg
					var _t1510 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1510 = _dollar_dollar.GetReduce()
					}
					deconstruct_result947 := _t1510
					if deconstruct_result947 != nil {
						unwrapped948 := deconstruct_result947
						p.pretty_reduce(unwrapped948)
					} else {
						_dollar_dollar := msg
						var _t1511 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1511 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result945 := _t1511
						if deconstruct_result945 != nil {
							unwrapped946 := deconstruct_result945
							p.pretty_conjunction(unwrapped946)
						} else {
							_dollar_dollar := msg
							var _t1512 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1512 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result943 := _t1512
							if deconstruct_result943 != nil {
								unwrapped944 := deconstruct_result943
								p.pretty_disjunction(unwrapped944)
							} else {
								_dollar_dollar := msg
								var _t1513 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1513 = _dollar_dollar.GetNot()
								}
								deconstruct_result941 := _t1513
								if deconstruct_result941 != nil {
									unwrapped942 := deconstruct_result941
									p.pretty_not(unwrapped942)
								} else {
									_dollar_dollar := msg
									var _t1514 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1514 = _dollar_dollar.GetFfi()
									}
									deconstruct_result939 := _t1514
									if deconstruct_result939 != nil {
										unwrapped940 := deconstruct_result939
										p.pretty_ffi(unwrapped940)
									} else {
										_dollar_dollar := msg
										var _t1515 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1515 = _dollar_dollar.GetAtom()
										}
										deconstruct_result937 := _t1515
										if deconstruct_result937 != nil {
											unwrapped938 := deconstruct_result937
											p.pretty_atom(unwrapped938)
										} else {
											_dollar_dollar := msg
											var _t1516 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1516 = _dollar_dollar.GetPragma()
											}
											deconstruct_result935 := _t1516
											if deconstruct_result935 != nil {
												unwrapped936 := deconstruct_result935
												p.pretty_pragma(unwrapped936)
											} else {
												_dollar_dollar := msg
												var _t1517 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1517 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result933 := _t1517
												if deconstruct_result933 != nil {
													unwrapped934 := deconstruct_result933
													p.pretty_primitive(unwrapped934)
												} else {
													_dollar_dollar := msg
													var _t1518 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1518 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result931 := _t1518
													if deconstruct_result931 != nil {
														unwrapped932 := deconstruct_result931
														p.pretty_rel_atom(unwrapped932)
													} else {
														_dollar_dollar := msg
														var _t1519 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1519 = _dollar_dollar.GetCast()
														}
														deconstruct_result929 := _t1519
														if deconstruct_result929 != nil {
															unwrapped930 := deconstruct_result929
															p.pretty_cast(unwrapped930)
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
	fields956 := msg
	_ = fields956
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields957 := msg
	_ = fields957
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat962 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat962 != nil {
		p.write(*flat962)
		return nil
	} else {
		_dollar_dollar := msg
		_t1520 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields958 := []interface{}{_t1520, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields959 := fields958
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field960 := unwrapped_fields959[0].([]interface{})
		p.pretty_bindings(field960)
		p.newline()
		field961 := unwrapped_fields959[1].(*pb.Formula)
		p.pretty_formula(field961)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat968 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		_dollar_dollar := msg
		fields963 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields964 := fields963
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field965 := unwrapped_fields964[0].(*pb.Abstraction)
		p.pretty_abstraction(field965)
		p.newline()
		field966 := unwrapped_fields964[1].(*pb.Abstraction)
		p.pretty_abstraction(field966)
		p.newline()
		field967 := unwrapped_fields964[2].([]*pb.Term)
		p.pretty_terms(field967)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat972 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat972 != nil {
		p.write(*flat972)
		return nil
	} else {
		fields969 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields969) == 0) {
			p.newline()
			for i971, elem970 := range fields969 {
				if (i971 > 0) {
					p.newline()
				}
				p.pretty_term(elem970)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat977 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat977 != nil {
		p.write(*flat977)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1521 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1521 = _dollar_dollar.GetVar()
		}
		deconstruct_result975 := _t1521
		if deconstruct_result975 != nil {
			unwrapped976 := deconstruct_result975
			p.pretty_var(unwrapped976)
		} else {
			_dollar_dollar := msg
			var _t1522 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1522 = _dollar_dollar.GetConstant()
			}
			deconstruct_result973 := _t1522
			if deconstruct_result973 != nil {
				unwrapped974 := deconstruct_result973
				p.pretty_value(unwrapped974)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat980 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat980 != nil {
		p.write(*flat980)
		return nil
	} else {
		_dollar_dollar := msg
		fields978 := _dollar_dollar.GetName()
		unwrapped_fields979 := fields978
		p.write(unwrapped_fields979)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1006 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1006 != nil {
		p.write(*flat1006)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1523 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1523 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1004 := _t1523
		if deconstruct_result1004 != nil {
			unwrapped1005 := deconstruct_result1004
			p.pretty_date(unwrapped1005)
		} else {
			_dollar_dollar := msg
			var _t1524 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1524 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1002 := _t1524
			if deconstruct_result1002 != nil {
				unwrapped1003 := deconstruct_result1002
				p.pretty_datetime(unwrapped1003)
			} else {
				_dollar_dollar := msg
				var _t1525 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1525 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1000 := _t1525
				if deconstruct_result1000 != nil {
					unwrapped1001 := *deconstruct_result1000
					p.write(p.formatStringValue(unwrapped1001))
				} else {
					_dollar_dollar := msg
					var _t1526 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1526 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result998 := _t1526
					if deconstruct_result998 != nil {
						unwrapped999 := *deconstruct_result998
						p.write(fmt.Sprintf("%di32", unwrapped999))
					} else {
						_dollar_dollar := msg
						var _t1527 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1527 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result996 := _t1527
						if deconstruct_result996 != nil {
							unwrapped997 := *deconstruct_result996
							p.write(fmt.Sprintf("%d", unwrapped997))
						} else {
							_dollar_dollar := msg
							var _t1528 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1528 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result994 := _t1528
							if deconstruct_result994 != nil {
								unwrapped995 := *deconstruct_result994
								p.write(formatFloat32(unwrapped995))
							} else {
								_dollar_dollar := msg
								var _t1529 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1529 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result992 := _t1529
								if deconstruct_result992 != nil {
									unwrapped993 := *deconstruct_result992
									p.write(formatFloat64(unwrapped993))
								} else {
									_dollar_dollar := msg
									var _t1530 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1530 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result990 := _t1530
									if deconstruct_result990 != nil {
										unwrapped991 := *deconstruct_result990
										p.write(fmt.Sprintf("%du32", unwrapped991))
									} else {
										_dollar_dollar := msg
										var _t1531 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1531 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result988 := _t1531
										if deconstruct_result988 != nil {
											unwrapped989 := deconstruct_result988
											p.write(p.formatUint128(unwrapped989))
										} else {
											_dollar_dollar := msg
											var _t1532 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1532 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result986 := _t1532
											if deconstruct_result986 != nil {
												unwrapped987 := deconstruct_result986
												p.write(p.formatInt128(unwrapped987))
											} else {
												_dollar_dollar := msg
												var _t1533 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1533 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result984 := _t1533
												if deconstruct_result984 != nil {
													unwrapped985 := deconstruct_result984
													p.write(p.formatDecimal(unwrapped985))
												} else {
													_dollar_dollar := msg
													var _t1534 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1534 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result982 := _t1534
													if deconstruct_result982 != nil {
														unwrapped983 := *deconstruct_result982
														p.pretty_boolean_value(unwrapped983)
													} else {
														fields981 := msg
														_ = fields981
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
	flat1012 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1012 != nil {
		p.write(*flat1012)
		return nil
	} else {
		_dollar_dollar := msg
		fields1007 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1008 := fields1007
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1009 := unwrapped_fields1008[0].(int64)
		p.write(fmt.Sprintf("%d", field1009))
		p.newline()
		field1010 := unwrapped_fields1008[1].(int64)
		p.write(fmt.Sprintf("%d", field1010))
		p.newline()
		field1011 := unwrapped_fields1008[2].(int64)
		p.write(fmt.Sprintf("%d", field1011))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1023 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1023 != nil {
		p.write(*flat1023)
		return nil
	} else {
		_dollar_dollar := msg
		fields1013 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1014 := fields1013
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1015 := unwrapped_fields1014[0].(int64)
		p.write(fmt.Sprintf("%d", field1015))
		p.newline()
		field1016 := unwrapped_fields1014[1].(int64)
		p.write(fmt.Sprintf("%d", field1016))
		p.newline()
		field1017 := unwrapped_fields1014[2].(int64)
		p.write(fmt.Sprintf("%d", field1017))
		p.newline()
		field1018 := unwrapped_fields1014[3].(int64)
		p.write(fmt.Sprintf("%d", field1018))
		p.newline()
		field1019 := unwrapped_fields1014[4].(int64)
		p.write(fmt.Sprintf("%d", field1019))
		p.newline()
		field1020 := unwrapped_fields1014[5].(int64)
		p.write(fmt.Sprintf("%d", field1020))
		field1021 := unwrapped_fields1014[6].(*int64)
		if field1021 != nil {
			p.newline()
			opt_val1022 := *field1021
			p.write(fmt.Sprintf("%d", opt_val1022))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1028 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		_dollar_dollar := msg
		fields1024 := _dollar_dollar.GetArgs()
		unwrapped_fields1025 := fields1024
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1025) == 0) {
			p.newline()
			for i1027, elem1026 := range unwrapped_fields1025 {
				if (i1027 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1026)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1033 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1033 != nil {
		p.write(*flat1033)
		return nil
	} else {
		_dollar_dollar := msg
		fields1029 := _dollar_dollar.GetArgs()
		unwrapped_fields1030 := fields1029
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1030) == 0) {
			p.newline()
			for i1032, elem1031 := range unwrapped_fields1030 {
				if (i1032 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1031)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1036 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1036 != nil {
		p.write(*flat1036)
		return nil
	} else {
		_dollar_dollar := msg
		fields1034 := _dollar_dollar.GetArg()
		unwrapped_fields1035 := fields1034
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1035)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		_dollar_dollar := msg
		fields1037 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1038 := fields1037
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1039 := unwrapped_fields1038[0].(string)
		p.pretty_name(field1039)
		p.newline()
		field1040 := unwrapped_fields1038[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1040)
		p.newline()
		field1041 := unwrapped_fields1038[2].([]*pb.Term)
		p.pretty_terms(field1041)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1044 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1044 != nil {
		p.write(*flat1044)
		return nil
	} else {
		fields1043 := msg
		p.write(":")
		p.write(fields1043)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1048 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1048 != nil {
		p.write(*flat1048)
		return nil
	} else {
		fields1045 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1045) == 0) {
			p.newline()
			for i1047, elem1046 := range fields1045 {
				if (i1047 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1046)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1055 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1055 != nil {
		p.write(*flat1055)
		return nil
	} else {
		_dollar_dollar := msg
		fields1049 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1050 := fields1049
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1051 := unwrapped_fields1050[0].(*pb.RelationId)
		p.pretty_relation_id(field1051)
		field1052 := unwrapped_fields1050[1].([]*pb.Term)
		if !(len(field1052) == 0) {
			p.newline()
			for i1054, elem1053 := range field1052 {
				if (i1054 > 0) {
					p.newline()
				}
				p.pretty_term(elem1053)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1062 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_dollar_dollar := msg
		fields1056 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1057 := fields1056
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1058 := unwrapped_fields1057[0].(string)
		p.pretty_name(field1058)
		field1059 := unwrapped_fields1057[1].([]*pb.Term)
		if !(len(field1059) == 0) {
			p.newline()
			for i1061, elem1060 := range field1059 {
				if (i1061 > 0) {
					p.newline()
				}
				p.pretty_term(elem1060)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1078 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1078 != nil {
		p.write(*flat1078)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1535 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1535 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1077 := _t1535
		if guard_result1077 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1536 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1536 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1076 := _t1536
			if guard_result1076 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1537 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1537 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1075 := _t1537
				if guard_result1075 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1538 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1538 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1074 := _t1538
					if guard_result1074 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1539 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1539 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1073 := _t1539
						if guard_result1073 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1540 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1540 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1072 := _t1540
							if guard_result1072 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1541 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1541 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1071 := _t1541
								if guard_result1071 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1542 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1542 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1070 := _t1542
									if guard_result1070 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1543 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1543 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1069 := _t1543
										if guard_result1069 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1063 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1064 := fields1063
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1065 := unwrapped_fields1064[0].(string)
											p.pretty_name(field1065)
											field1066 := unwrapped_fields1064[1].([]*pb.RelTerm)
											if !(len(field1066) == 0) {
												p.newline()
												for i1068, elem1067 := range field1066 {
													if (i1068 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1067)
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
	flat1083 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1544 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1544 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1079 := _t1544
		unwrapped_fields1080 := fields1079
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1081 := unwrapped_fields1080[0].(*pb.Term)
		p.pretty_term(field1081)
		p.newline()
		field1082 := unwrapped_fields1080[1].(*pb.Term)
		p.pretty_term(field1082)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1545 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1545 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1084 := _t1545
		unwrapped_fields1085 := fields1084
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1086 := unwrapped_fields1085[0].(*pb.Term)
		p.pretty_term(field1086)
		p.newline()
		field1087 := unwrapped_fields1085[1].(*pb.Term)
		p.pretty_term(field1087)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1093 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1546 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1546 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1089 := _t1546
		unwrapped_fields1090 := fields1089
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1091 := unwrapped_fields1090[0].(*pb.Term)
		p.pretty_term(field1091)
		p.newline()
		field1092 := unwrapped_fields1090[1].(*pb.Term)
		p.pretty_term(field1092)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1547 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1547 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1094 := _t1547
		unwrapped_fields1095 := fields1094
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1096 := unwrapped_fields1095[0].(*pb.Term)
		p.pretty_term(field1096)
		p.newline()
		field1097 := unwrapped_fields1095[1].(*pb.Term)
		p.pretty_term(field1097)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1103 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1103 != nil {
		p.write(*flat1103)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1548 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1548 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1099 := _t1548
		unwrapped_fields1100 := fields1099
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1101 := unwrapped_fields1100[0].(*pb.Term)
		p.pretty_term(field1101)
		p.newline()
		field1102 := unwrapped_fields1100[1].(*pb.Term)
		p.pretty_term(field1102)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1549 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1549 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1104 := _t1549
		unwrapped_fields1105 := fields1104
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1106 := unwrapped_fields1105[0].(*pb.Term)
		p.pretty_term(field1106)
		p.newline()
		field1107 := unwrapped_fields1105[1].(*pb.Term)
		p.pretty_term(field1107)
		p.newline()
		field1108 := unwrapped_fields1105[2].(*pb.Term)
		p.pretty_term(field1108)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1115 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1115 != nil {
		p.write(*flat1115)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1550 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1550 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1110 := _t1550
		unwrapped_fields1111 := fields1110
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1112 := unwrapped_fields1111[0].(*pb.Term)
		p.pretty_term(field1112)
		p.newline()
		field1113 := unwrapped_fields1111[1].(*pb.Term)
		p.pretty_term(field1113)
		p.newline()
		field1114 := unwrapped_fields1111[2].(*pb.Term)
		p.pretty_term(field1114)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1551 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1551 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1116 := _t1551
		unwrapped_fields1117 := fields1116
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1118 := unwrapped_fields1117[0].(*pb.Term)
		p.pretty_term(field1118)
		p.newline()
		field1119 := unwrapped_fields1117[1].(*pb.Term)
		p.pretty_term(field1119)
		p.newline()
		field1120 := unwrapped_fields1117[2].(*pb.Term)
		p.pretty_term(field1120)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1127 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1127 != nil {
		p.write(*flat1127)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1552 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1552 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1122 := _t1552
		unwrapped_fields1123 := fields1122
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1124 := unwrapped_fields1123[0].(*pb.Term)
		p.pretty_term(field1124)
		p.newline()
		field1125 := unwrapped_fields1123[1].(*pb.Term)
		p.pretty_term(field1125)
		p.newline()
		field1126 := unwrapped_fields1123[2].(*pb.Term)
		p.pretty_term(field1126)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1132 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1553 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1553 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1130 := _t1553
		if deconstruct_result1130 != nil {
			unwrapped1131 := deconstruct_result1130
			p.pretty_specialized_value(unwrapped1131)
		} else {
			_dollar_dollar := msg
			var _t1554 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1554 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1128 := _t1554
			if deconstruct_result1128 != nil {
				unwrapped1129 := deconstruct_result1128
				p.pretty_term(unwrapped1129)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		fields1133 := msg
		p.write("#")
		p.pretty_raw_value(fields1133)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1141 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1141 != nil {
		p.write(*flat1141)
		return nil
	} else {
		_dollar_dollar := msg
		fields1135 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1136 := fields1135
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1137 := unwrapped_fields1136[0].(string)
		p.pretty_name(field1137)
		field1138 := unwrapped_fields1136[1].([]*pb.RelTerm)
		if !(len(field1138) == 0) {
			p.newline()
			for i1140, elem1139 := range field1138 {
				if (i1140 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1139)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1146 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		_dollar_dollar := msg
		fields1142 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1143 := fields1142
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1144 := unwrapped_fields1143[0].(*pb.Term)
		p.pretty_term(field1144)
		p.newline()
		field1145 := unwrapped_fields1143[1].(*pb.Term)
		p.pretty_term(field1145)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		fields1147 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1147) == 0) {
			p.newline()
			for i1149, elem1148 := range fields1147 {
				if (i1149 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1148)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		fields1151 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1152 := fields1151
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1153 := unwrapped_fields1152[0].(string)
		p.pretty_name(field1153)
		field1154 := unwrapped_fields1152[1].([]*pb.Value)
		if !(len(field1154) == 0) {
			p.newline()
			for i1156, elem1155 := range field1154 {
				if (i1156 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1155)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1164 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		_dollar_dollar := msg
		fields1158 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1160 := unwrapped_fields1159[0].([]*pb.RelationId)
		if !(len(field1160) == 0) {
			p.newline()
			for i1162, elem1161 := range field1160 {
				if (i1162 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1161)
			}
		}
		p.newline()
		field1163 := unwrapped_fields1159[1].(*pb.Script)
		p.pretty_script(field1163)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1169 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1169 != nil {
		p.write(*flat1169)
		return nil
	} else {
		_dollar_dollar := msg
		fields1165 := _dollar_dollar.GetConstructs()
		unwrapped_fields1166 := fields1165
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1166) == 0) {
			p.newline()
			for i1168, elem1167 := range unwrapped_fields1166 {
				if (i1168 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1167)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1555 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1555 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1172 := _t1555
		if deconstruct_result1172 != nil {
			unwrapped1173 := deconstruct_result1172
			p.pretty_loop(unwrapped1173)
		} else {
			_dollar_dollar := msg
			var _t1556 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1556 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1170 := _t1556
			if deconstruct_result1170 != nil {
				unwrapped1171 := deconstruct_result1170
				p.pretty_instruction(unwrapped1171)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		fields1175 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1176 := fields1175
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1177 := unwrapped_fields1176[0].([]*pb.Instruction)
		p.pretty_init(field1177)
		p.newline()
		field1178 := unwrapped_fields1176[1].(*pb.Script)
		p.pretty_script(field1178)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		fields1180 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1180) == 0) {
			p.newline()
			for i1182, elem1181 := range fields1180 {
				if (i1182 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1181)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1557 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1557 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1192 := _t1557
		if deconstruct_result1192 != nil {
			unwrapped1193 := deconstruct_result1192
			p.pretty_assign(unwrapped1193)
		} else {
			_dollar_dollar := msg
			var _t1558 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1558 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1190 := _t1558
			if deconstruct_result1190 != nil {
				unwrapped1191 := deconstruct_result1190
				p.pretty_upsert(unwrapped1191)
			} else {
				_dollar_dollar := msg
				var _t1559 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1559 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1188 := _t1559
				if deconstruct_result1188 != nil {
					unwrapped1189 := deconstruct_result1188
					p.pretty_break(unwrapped1189)
				} else {
					_dollar_dollar := msg
					var _t1560 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1560 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1186 := _t1560
					if deconstruct_result1186 != nil {
						unwrapped1187 := deconstruct_result1186
						p.pretty_monoid_def(unwrapped1187)
					} else {
						_dollar_dollar := msg
						var _t1561 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1561 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1184 := _t1561
						if deconstruct_result1184 != nil {
							unwrapped1185 := deconstruct_result1184
							p.pretty_monus_def(unwrapped1185)
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
	flat1201 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1201 != nil {
		p.write(*flat1201)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1562 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1562 = _dollar_dollar.GetAttrs()
		}
		fields1195 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1562}
		unwrapped_fields1196 := fields1195
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1197 := unwrapped_fields1196[0].(*pb.RelationId)
		p.pretty_relation_id(field1197)
		p.newline()
		field1198 := unwrapped_fields1196[1].(*pb.Abstraction)
		p.pretty_abstraction(field1198)
		field1199 := unwrapped_fields1196[2].([]*pb.Attribute)
		if field1199 != nil {
			p.newline()
			opt_val1200 := field1199
			p.pretty_attrs(opt_val1200)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1563 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1563 = _dollar_dollar.GetAttrs()
		}
		fields1202 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1563}
		unwrapped_fields1203 := fields1202
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1204 := unwrapped_fields1203[0].(*pb.RelationId)
		p.pretty_relation_id(field1204)
		p.newline()
		field1205 := unwrapped_fields1203[1].([]interface{})
		p.pretty_abstraction_with_arity(field1205)
		field1206 := unwrapped_fields1203[2].([]*pb.Attribute)
		if field1206 != nil {
			p.newline()
			opt_val1207 := field1206
			p.pretty_attrs(opt_val1207)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1213 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1213 != nil {
		p.write(*flat1213)
		return nil
	} else {
		_dollar_dollar := msg
		_t1564 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1209 := []interface{}{_t1564, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1210 := fields1209
		p.write("(")
		p.indent()
		field1211 := unwrapped_fields1210[0].([]interface{})
		p.pretty_bindings(field1211)
		p.newline()
		field1212 := unwrapped_fields1210[1].(*pb.Formula)
		p.pretty_formula(field1212)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1565 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1565 = _dollar_dollar.GetAttrs()
		}
		fields1214 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1565}
		unwrapped_fields1215 := fields1214
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1216 := unwrapped_fields1215[0].(*pb.RelationId)
		p.pretty_relation_id(field1216)
		p.newline()
		field1217 := unwrapped_fields1215[1].(*pb.Abstraction)
		p.pretty_abstraction(field1217)
		field1218 := unwrapped_fields1215[2].([]*pb.Attribute)
		if field1218 != nil {
			p.newline()
			opt_val1219 := field1218
			p.pretty_attrs(opt_val1219)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1228 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1228 != nil {
		p.write(*flat1228)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1566 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1566 = _dollar_dollar.GetAttrs()
		}
		fields1221 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1566}
		unwrapped_fields1222 := fields1221
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1223 := unwrapped_fields1222[0].(*pb.Monoid)
		p.pretty_monoid(field1223)
		p.newline()
		field1224 := unwrapped_fields1222[1].(*pb.RelationId)
		p.pretty_relation_id(field1224)
		p.newline()
		field1225 := unwrapped_fields1222[2].([]interface{})
		p.pretty_abstraction_with_arity(field1225)
		field1226 := unwrapped_fields1222[3].([]*pb.Attribute)
		if field1226 != nil {
			p.newline()
			opt_val1227 := field1226
			p.pretty_attrs(opt_val1227)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1237 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1237 != nil {
		p.write(*flat1237)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1567 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1567 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1235 := _t1567
		if deconstruct_result1235 != nil {
			unwrapped1236 := deconstruct_result1235
			p.pretty_or_monoid(unwrapped1236)
		} else {
			_dollar_dollar := msg
			var _t1568 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1568 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1233 := _t1568
			if deconstruct_result1233 != nil {
				unwrapped1234 := deconstruct_result1233
				p.pretty_min_monoid(unwrapped1234)
			} else {
				_dollar_dollar := msg
				var _t1569 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1569 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1231 := _t1569
				if deconstruct_result1231 != nil {
					unwrapped1232 := deconstruct_result1231
					p.pretty_max_monoid(unwrapped1232)
				} else {
					_dollar_dollar := msg
					var _t1570 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1570 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1229 := _t1570
					if deconstruct_result1229 != nil {
						unwrapped1230 := deconstruct_result1229
						p.pretty_sum_monoid(unwrapped1230)
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
	fields1238 := msg
	_ = fields1238
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1241 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1241 != nil {
		p.write(*flat1241)
		return nil
	} else {
		_dollar_dollar := msg
		fields1239 := _dollar_dollar.GetType()
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1240)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		fields1242 := _dollar_dollar.GetType()
		unwrapped_fields1243 := fields1242
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1243)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1247 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_dollar_dollar := msg
		fields1245 := _dollar_dollar.GetType()
		unwrapped_fields1246 := fields1245
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1246)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1255 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1255 != nil {
		p.write(*flat1255)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1571 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1571 = _dollar_dollar.GetAttrs()
		}
		fields1248 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1571}
		unwrapped_fields1249 := fields1248
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1250 := unwrapped_fields1249[0].(*pb.Monoid)
		p.pretty_monoid(field1250)
		p.newline()
		field1251 := unwrapped_fields1249[1].(*pb.RelationId)
		p.pretty_relation_id(field1251)
		p.newline()
		field1252 := unwrapped_fields1249[2].([]interface{})
		p.pretty_abstraction_with_arity(field1252)
		field1253 := unwrapped_fields1249[3].([]*pb.Attribute)
		if field1253 != nil {
			p.newline()
			opt_val1254 := field1253
			p.pretty_attrs(opt_val1254)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		_dollar_dollar := msg
		fields1256 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1257 := fields1256
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1258 := unwrapped_fields1257[0].(*pb.RelationId)
		p.pretty_relation_id(field1258)
		p.newline()
		field1259 := unwrapped_fields1257[1].(*pb.Abstraction)
		p.pretty_abstraction(field1259)
		p.newline()
		field1260 := unwrapped_fields1257[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1260)
		p.newline()
		field1261 := unwrapped_fields1257[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1261)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		fields1263 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1263) == 0) {
			p.newline()
			for i1265, elem1264 := range fields1263 {
				if (i1265 > 0) {
					p.newline()
				}
				p.pretty_var(elem1264)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1270 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1270 != nil {
		p.write(*flat1270)
		return nil
	} else {
		fields1267 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1267) == 0) {
			p.newline()
			for i1269, elem1268 := range fields1267 {
				if (i1269 > 0) {
					p.newline()
				}
				p.pretty_var(elem1268)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1277 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1572 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1572 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1275 := _t1572
		if deconstruct_result1275 != nil {
			unwrapped1276 := deconstruct_result1275
			p.pretty_edb(unwrapped1276)
		} else {
			_dollar_dollar := msg
			var _t1573 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1573 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1273 := _t1573
			if deconstruct_result1273 != nil {
				unwrapped1274 := deconstruct_result1273
				p.pretty_betree_relation(unwrapped1274)
			} else {
				_dollar_dollar := msg
				var _t1574 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1574 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1271 := _t1574
				if deconstruct_result1271 != nil {
					unwrapped1272 := deconstruct_result1271
					p.pretty_csv_data(unwrapped1272)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		fields1278 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1279 := fields1278
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1280 := unwrapped_fields1279[0].(*pb.RelationId)
		p.pretty_relation_id(field1280)
		p.newline()
		field1281 := unwrapped_fields1279[1].([]string)
		p.pretty_edb_path(field1281)
		p.newline()
		field1282 := unwrapped_fields1279[2].([]*pb.Type)
		p.pretty_edb_types(field1282)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1287 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1287 != nil {
		p.write(*flat1287)
		return nil
	} else {
		fields1284 := msg
		p.write("[")
		p.indent()
		for i1286, elem1285 := range fields1284 {
			if (i1286 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1285))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		fields1288 := msg
		p.write("[")
		p.indent()
		for i1290, elem1289 := range fields1288 {
			if (i1290 > 0) {
				p.newline()
			}
			p.pretty_type(elem1289)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		fields1292 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1293 := fields1292
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1294 := unwrapped_fields1293[0].(*pb.RelationId)
		p.pretty_relation_id(field1294)
		p.newline()
		field1295 := unwrapped_fields1293[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1295)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1302 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1302 != nil {
		p.write(*flat1302)
		return nil
	} else {
		_dollar_dollar := msg
		_t1575 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1297 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1575}
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1299 := unwrapped_fields1298[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1299)
		p.newline()
		field1300 := unwrapped_fields1298[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1300)
		p.newline()
		field1301 := unwrapped_fields1298[2].([][]interface{})
		p.pretty_config_dict(field1301)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1306 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1306 != nil {
		p.write(*flat1306)
		return nil
	} else {
		fields1303 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1303) == 0) {
			p.newline()
			for i1305, elem1304 := range fields1303 {
				if (i1305 > 0) {
					p.newline()
				}
				p.pretty_type(elem1304)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		fields1307 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1307) == 0) {
			p.newline()
			for i1309, elem1308 := range fields1307 {
				if (i1309 > 0) {
					p.newline()
				}
				p.pretty_type(elem1308)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1317 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		_dollar_dollar := msg
		fields1311 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1312 := fields1311
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1313 := unwrapped_fields1312[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1313)
		p.newline()
		field1314 := unwrapped_fields1312[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1314)
		p.newline()
		field1315 := unwrapped_fields1312[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1315)
		p.newline()
		field1316 := unwrapped_fields1312[3].(string)
		p.pretty_csv_asof(field1316)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1576 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1576 = _dollar_dollar.GetPaths()
		}
		var _t1577 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1577 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1318 := []interface{}{_t1576, _t1577}
		unwrapped_fields1319 := fields1318
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1320 := unwrapped_fields1319[0].([]string)
		if field1320 != nil {
			p.newline()
			opt_val1321 := field1320
			p.pretty_csv_locator_paths(opt_val1321)
		}
		field1322 := unwrapped_fields1319[1].(*string)
		if field1322 != nil {
			p.newline()
			opt_val1323 := *field1322
			p.pretty_csv_locator_inline_data(opt_val1323)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1328 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1328 != nil {
		p.write(*flat1328)
		return nil
	} else {
		fields1325 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1325) == 0) {
			p.newline()
			for i1327, elem1326 := range fields1325 {
				if (i1327 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1326))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		fields1329 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1329))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1333 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1333 != nil {
		p.write(*flat1333)
		return nil
	} else {
		_dollar_dollar := msg
		_t1578 := p.deconstruct_csv_config(_dollar_dollar)
		fields1331 := _t1578
		unwrapped_fields1332 := fields1331
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1332)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1337 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1337 != nil {
		p.write(*flat1337)
		return nil
	} else {
		fields1334 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1334) == 0) {
			p.newline()
			for i1336, elem1335 := range fields1334 {
				if (i1336 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1335)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1346 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1346 != nil {
		p.write(*flat1346)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1579 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1579 = _dollar_dollar.GetTargetId()
		}
		fields1338 := []interface{}{_dollar_dollar.GetColumnPath(), _t1579, _dollar_dollar.GetTypes()}
		unwrapped_fields1339 := fields1338
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1340 := unwrapped_fields1339[0].([]string)
		p.pretty_gnf_column_path(field1340)
		field1341 := unwrapped_fields1339[1].(*pb.RelationId)
		if field1341 != nil {
			p.newline()
			opt_val1342 := field1341
			p.pretty_relation_id(opt_val1342)
		}
		p.newline()
		p.write("[")
		field1343 := unwrapped_fields1339[2].([]*pb.Type)
		for i1345, elem1344 := range field1343 {
			if (i1345 > 0) {
				p.newline()
			}
			p.pretty_type(elem1344)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1580 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1580 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1351 := _t1580
		if deconstruct_result1351 != nil {
			unwrapped1352 := *deconstruct_result1351
			p.write(p.formatStringValue(unwrapped1352))
		} else {
			_dollar_dollar := msg
			var _t1581 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1581 = _dollar_dollar
			}
			deconstruct_result1347 := _t1581
			if deconstruct_result1347 != nil {
				unwrapped1348 := deconstruct_result1347
				p.write("[")
				p.indent()
				for i1350, elem1349 := range unwrapped1348 {
					if (i1350 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1349))
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
	flat1355 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1355 != nil {
		p.write(*flat1355)
		return nil
	} else {
		fields1354 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1354))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1358 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1358 != nil {
		p.write(*flat1358)
		return nil
	} else {
		_dollar_dollar := msg
		fields1356 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1357 := fields1356
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1357)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1363 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1363 != nil {
		p.write(*flat1363)
		return nil
	} else {
		_dollar_dollar := msg
		fields1359 := _dollar_dollar.GetRelations()
		unwrapped_fields1360 := fields1359
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1360) == 0) {
			p.newline()
			for i1362, elem1361 := range unwrapped_fields1360 {
				if (i1362 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1361)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1368 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		fields1364 := _dollar_dollar.GetMappings()
		unwrapped_fields1365 := fields1364
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1365) == 0) {
			p.newline()
			for i1367, elem1366 := range unwrapped_fields1365 {
				if (i1367 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1366)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1373 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1373 != nil {
		p.write(*flat1373)
		return nil
	} else {
		_dollar_dollar := msg
		fields1369 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1370 := fields1369
		field1371 := unwrapped_fields1370[0].([]string)
		p.pretty_edb_path(field1371)
		p.write(" ")
		field1372 := unwrapped_fields1370[1].(*pb.RelationId)
		p.pretty_relation_id(field1372)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1377 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1377 != nil {
		p.write(*flat1377)
		return nil
	} else {
		fields1374 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1374) == 0) {
			p.newline()
			for i1376, elem1375 := range fields1374 {
				if (i1376 > 0) {
					p.newline()
				}
				p.pretty_read(elem1375)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1388 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1388 != nil {
		p.write(*flat1388)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1582 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1582 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1386 := _t1582
		if deconstruct_result1386 != nil {
			unwrapped1387 := deconstruct_result1386
			p.pretty_demand(unwrapped1387)
		} else {
			_dollar_dollar := msg
			var _t1583 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1583 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1384 := _t1583
			if deconstruct_result1384 != nil {
				unwrapped1385 := deconstruct_result1384
				p.pretty_output(unwrapped1385)
			} else {
				_dollar_dollar := msg
				var _t1584 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1584 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1382 := _t1584
				if deconstruct_result1382 != nil {
					unwrapped1383 := deconstruct_result1382
					p.pretty_what_if(unwrapped1383)
				} else {
					_dollar_dollar := msg
					var _t1585 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1585 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1380 := _t1585
					if deconstruct_result1380 != nil {
						unwrapped1381 := deconstruct_result1380
						p.pretty_abort(unwrapped1381)
					} else {
						_dollar_dollar := msg
						var _t1586 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1586 = _dollar_dollar.GetExport()
						}
						deconstruct_result1378 := _t1586
						if deconstruct_result1378 != nil {
							unwrapped1379 := deconstruct_result1378
							p.pretty_export(unwrapped1379)
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
	flat1391 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1391 != nil {
		p.write(*flat1391)
		return nil
	} else {
		_dollar_dollar := msg
		fields1389 := _dollar_dollar.GetRelationId()
		unwrapped_fields1390 := fields1389
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1390)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1396 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1396 != nil {
		p.write(*flat1396)
		return nil
	} else {
		_dollar_dollar := msg
		fields1392 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1393 := fields1392
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1394 := unwrapped_fields1393[0].(string)
		p.pretty_name(field1394)
		p.newline()
		field1395 := unwrapped_fields1393[1].(*pb.RelationId)
		p.pretty_relation_id(field1395)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1401 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1401 != nil {
		p.write(*flat1401)
		return nil
	} else {
		_dollar_dollar := msg
		fields1397 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1398 := fields1397
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1399 := unwrapped_fields1398[0].(string)
		p.pretty_name(field1399)
		p.newline()
		field1400 := unwrapped_fields1398[1].(*pb.Epoch)
		p.pretty_epoch(field1400)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1407 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1587 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1587 = ptr(_dollar_dollar.GetName())
		}
		fields1402 := []interface{}{_t1587, _dollar_dollar.GetRelationId()}
		unwrapped_fields1403 := fields1402
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1404 := unwrapped_fields1403[0].(*string)
		if field1404 != nil {
			p.newline()
			opt_val1405 := *field1404
			p.pretty_name(opt_val1405)
		}
		p.newline()
		field1406 := unwrapped_fields1403[1].(*pb.RelationId)
		p.pretty_relation_id(field1406)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1412 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1412 != nil {
		p.write(*flat1412)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1588 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1588 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1410 := _t1588
		if deconstruct_result1410 != nil {
			unwrapped1411 := deconstruct_result1410
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1411)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1589 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1589 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1408 := _t1589
			if deconstruct_result1408 != nil {
				unwrapped1409 := deconstruct_result1408
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1409)
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
	flat1423 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1590 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1590 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1418 := _t1590
		if deconstruct_result1418 != nil {
			unwrapped1419 := deconstruct_result1418
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1420 := unwrapped1419[0].(string)
			p.pretty_export_csv_path(field1420)
			p.newline()
			field1421 := unwrapped1419[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1421)
			p.newline()
			field1422 := unwrapped1419[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1422)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1591 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1592 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1591 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1592}
			}
			deconstruct_result1413 := _t1591
			if deconstruct_result1413 != nil {
				unwrapped1414 := deconstruct_result1413
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1415 := unwrapped1414[0].(string)
				p.pretty_export_csv_path(field1415)
				p.newline()
				field1416 := unwrapped1414[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1416)
				p.newline()
				field1417 := unwrapped1414[2].([][]interface{})
				p.pretty_config_dict(field1417)
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
	flat1425 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		fields1424 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1424))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1593 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1593 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1428 := _t1593
		if deconstruct_result1428 != nil {
			unwrapped1429 := deconstruct_result1428
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1429) == 0) {
				p.newline()
				for i1431, elem1430 := range unwrapped1429 {
					if (i1431 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1430)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1594 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1594 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1426 := _t1594
			if deconstruct_result1426 != nil {
				unwrapped1427 := deconstruct_result1426
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1427)
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
	flat1437 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1437 != nil {
		p.write(*flat1437)
		return nil
	} else {
		_dollar_dollar := msg
		fields1433 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1434 := fields1433
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1435 := unwrapped_fields1434[0].(string)
		p.write(p.formatStringValue(field1435))
		p.newline()
		field1436 := unwrapped_fields1434[1].(*pb.RelationId)
		p.pretty_relation_id(field1436)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1441 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1441 != nil {
		p.write(*flat1441)
		return nil
	} else {
		fields1438 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1438) == 0) {
			p.newline()
			for i1440, elem1439 := range fields1438 {
				if (i1440 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1439)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1453 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1453 != nil {
		p.write(*flat1453)
		return nil
	} else {
		_dollar_dollar := msg
		_t1595 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1442 := []interface{}{_dollar_dollar.GetCatalogUri(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetTableName(), _dollar_dollar.GetCatalogProperties(), _dollar_dollar.GetSchema(), _t1595}
		unwrapped_fields1443 := fields1442
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1444 := unwrapped_fields1443[0].(string)
		p.write(p.formatStringValue(field1444))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1445 := unwrapped_fields1443[1].([]string)
		if !(len(field1445) == 0) {
			p.newline()
			for i1447, elem1446 := range field1445 {
				if (i1447 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1446))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1448 := unwrapped_fields1443[2].(string)
		p.write(p.formatStringValue(field1448))
		p.dedent()
		p.write(")")
		p.newline()
		field1449 := unwrapped_fields1443[3].(*pb.IcebergCatalogProperties)
		p.pretty_export_iceberg_catalog_properties(field1449)
		p.newline()
		p.write("(")
		p.newline()
		p.write("schema")
		p.newline()
		field1450 := unwrapped_fields1443[4].(string)
		p.write(p.formatStringValue(field1450))
		p.dedent()
		p.write(")")
		field1451 := unwrapped_fields1443[5].([][]interface{})
		if field1451 != nil {
			p.newline()
			opt_val1452 := field1451
			p.pretty_config_dict(opt_val1452)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_catalog_properties(msg *pb.IcebergCatalogProperties) interface{} {
	flat1459 := p.tryFlat(msg, func() { p.pretty_export_iceberg_catalog_properties(msg) })
	if flat1459 != nil {
		p.write(*flat1459)
		return nil
	} else {
		_dollar_dollar := msg
		_t1596 := p.deconstruct_iceberg_catalog_properties_optional(_dollar_dollar)
		fields1454 := []interface{}{_dollar_dollar.GetWarehouse(), _t1596}
		unwrapped_fields1455 := fields1454
		p.write("(")
		p.write("catalog_properties")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1456 := unwrapped_fields1455[0].(string)
		p.write(p.formatStringValue(field1456))
		p.dedent()
		p.write(")")
		field1457 := unwrapped_fields1455[1].([][]interface{})
		if field1457 != nil {
			p.newline()
			opt_val1458 := field1457
			p.pretty_config_dict(opt_val1458)
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
		_t1642 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1642)
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
	case *pb.IcebergCatalogProperties:
		p.pretty_export_iceberg_catalog_properties(m)
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
