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

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1556 := &pb.Value{}
	_t1556.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1556
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1557 := &pb.Value{}
	_t1557.Value = &pb.Value_IntValue{IntValue: v}
	return _t1557
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1558 := &pb.Value{}
	_t1558.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1558
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1559 := &pb.Value{}
	_t1559.Value = &pb.Value_StringValue{StringValue: v}
	return _t1559
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1560 := &pb.Value{}
	_t1560.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1560
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1561 := &pb.Value{}
	_t1561.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1561
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1562 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1562})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1563 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1563})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1564 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1564})
			}
		}
	}
	_t1565 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1565})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1566 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1566})
	_t1567 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1567})
	if msg.GetNewLine() != "" {
		_t1568 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1568})
	}
	_t1569 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1569})
	_t1570 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1570})
	_t1571 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1571})
	if msg.GetComment() != "" {
		_t1572 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1572})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1573 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1573})
	}
	_t1574 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1574})
	_t1575 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1575})
	_t1576 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1576})
	if msg.GetPartitionSizeMb() != 0 {
		_t1577 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1577})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1578 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1578})
	_t1579 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1579})
	_t1580 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1580})
	_t1581 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1581})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1582 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1582})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1583 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1583})
		}
	}
	_t1584 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1584})
	_t1585 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1585})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1586 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1586})
	}
	if msg.Compression != nil {
		_t1587 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1587})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1588 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1588})
	}
	if msg.SyntaxMissingString != nil {
		_t1589 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1589})
	}
	if msg.SyntaxDelim != nil {
		_t1590 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1590})
	}
	if msg.SyntaxQuotechar != nil {
		_t1591 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1591})
	}
	if msg.SyntaxEscapechar != nil {
		_t1592 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1592})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1593 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1593
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
	flat725 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat725 != nil {
		p.write(*flat725)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1432 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1432 = _dollar_dollar.GetConfigure()
		}
		var _t1433 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1433 = _dollar_dollar.GetSync()
		}
		fields716 := []interface{}{_t1432, _t1433, _dollar_dollar.GetEpochs()}
		unwrapped_fields717 := fields716
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field718 := unwrapped_fields717[0].(*pb.Configure)
		if field718 != nil {
			p.newline()
			opt_val719 := field718
			p.pretty_configure(opt_val719)
		}
		field720 := unwrapped_fields717[1].(*pb.Sync)
		if field720 != nil {
			p.newline()
			opt_val721 := field720
			p.pretty_sync(opt_val721)
		}
		field722 := unwrapped_fields717[2].([]*pb.Epoch)
		if !(len(field722) == 0) {
			p.newline()
			for i724, elem723 := range field722 {
				if (i724 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem723)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat728 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat728 != nil {
		p.write(*flat728)
		return nil
	} else {
		_dollar_dollar := msg
		_t1434 := p.deconstruct_configure(_dollar_dollar)
		fields726 := _t1434
		unwrapped_fields727 := fields726
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields727)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat732 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat732 != nil {
		p.write(*flat732)
		return nil
	} else {
		fields729 := msg
		p.write("{")
		p.indent()
		if !(len(fields729) == 0) {
			p.newline()
			for i731, elem730 := range fields729 {
				if (i731 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem730)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat737 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat737 != nil {
		p.write(*flat737)
		return nil
	} else {
		_dollar_dollar := msg
		fields733 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields734 := fields733
		p.write(":")
		field735 := unwrapped_fields734[0].(string)
		p.write(field735)
		p.write(" ")
		field736 := unwrapped_fields734[1].(*pb.Value)
		p.pretty_value(field736)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat763 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat763 != nil {
		p.write(*flat763)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1435 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1435 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result761 := _t1435
		if deconstruct_result761 != nil {
			unwrapped762 := deconstruct_result761
			p.pretty_date(unwrapped762)
		} else {
			_dollar_dollar := msg
			var _t1436 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1436 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result759 := _t1436
			if deconstruct_result759 != nil {
				unwrapped760 := deconstruct_result759
				p.pretty_datetime(unwrapped760)
			} else {
				_dollar_dollar := msg
				var _t1437 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1437 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result757 := _t1437
				if deconstruct_result757 != nil {
					unwrapped758 := *deconstruct_result757
					p.write(p.formatStringValue(unwrapped758))
				} else {
					_dollar_dollar := msg
					var _t1438 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t1438 = ptr(_dollar_dollar.GetIntValue())
					}
					deconstruct_result755 := _t1438
					if deconstruct_result755 != nil {
						unwrapped756 := *deconstruct_result755
						p.write(fmt.Sprintf("%d", unwrapped756))
					} else {
						_dollar_dollar := msg
						var _t1439 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t1439 = ptr(_dollar_dollar.GetFloatValue())
						}
						deconstruct_result753 := _t1439
						if deconstruct_result753 != nil {
							unwrapped754 := *deconstruct_result753
							p.write(formatFloat64(unwrapped754))
						} else {
							_dollar_dollar := msg
							var _t1440 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t1440 = _dollar_dollar.GetUint128Value()
							}
							deconstruct_result751 := _t1440
							if deconstruct_result751 != nil {
								unwrapped752 := deconstruct_result751
								p.write(p.formatUint128(unwrapped752))
							} else {
								_dollar_dollar := msg
								var _t1441 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t1441 = _dollar_dollar.GetInt128Value()
								}
								deconstruct_result749 := _t1441
								if deconstruct_result749 != nil {
									unwrapped750 := deconstruct_result749
									p.write(p.formatInt128(unwrapped750))
								} else {
									_dollar_dollar := msg
									var _t1442 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t1442 = _dollar_dollar.GetDecimalValue()
									}
									deconstruct_result747 := _t1442
									if deconstruct_result747 != nil {
										unwrapped748 := deconstruct_result747
										p.write(p.formatDecimal(unwrapped748))
									} else {
										_dollar_dollar := msg
										var _t1443 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t1443 = ptr(_dollar_dollar.GetBooleanValue())
										}
										deconstruct_result745 := _t1443
										if deconstruct_result745 != nil {
											unwrapped746 := *deconstruct_result745
											p.pretty_boolean_value(unwrapped746)
										} else {
											_dollar_dollar := msg
											var _t1444 *int32
											if hasProtoField(_dollar_dollar, "int32_value") {
												_t1444 = ptr(_dollar_dollar.GetInt32Value())
											}
											deconstruct_result743 := _t1444
											if deconstruct_result743 != nil {
												unwrapped744 := *deconstruct_result743
												p.write(fmt.Sprintf("%di32", unwrapped744))
											} else {
												_dollar_dollar := msg
												var _t1445 *float32
												if hasProtoField(_dollar_dollar, "float32_value") {
													_t1445 = ptr(_dollar_dollar.GetFloat32Value())
												}
												deconstruct_result741 := _t1445
												if deconstruct_result741 != nil {
													unwrapped742 := *deconstruct_result741
													p.write(fmt.Sprintf("%sf32", strconv.FormatFloat(float64(unwrapped742), 'g', -1, 32)))
												} else {
													_dollar_dollar := msg
													var _t1446 *uint32
													if hasProtoField(_dollar_dollar, "uint32_value") {
														_t1446 = ptr(_dollar_dollar.GetUint32Value())
													}
													deconstruct_result739 := _t1446
													if deconstruct_result739 != nil {
														unwrapped740 := *deconstruct_result739
														p.write(fmt.Sprintf("%du32", unwrapped740))
													} else {
														fields738 := msg
														_ = fields738
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
	flat769 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat769 != nil {
		p.write(*flat769)
		return nil
	} else {
		_dollar_dollar := msg
		fields764 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields765 := fields764
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field766 := unwrapped_fields765[0].(int64)
		p.write(fmt.Sprintf("%d", field766))
		p.newline()
		field767 := unwrapped_fields765[1].(int64)
		p.write(fmt.Sprintf("%d", field767))
		p.newline()
		field768 := unwrapped_fields765[2].(int64)
		p.write(fmt.Sprintf("%d", field768))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat780 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat780 != nil {
		p.write(*flat780)
		return nil
	} else {
		_dollar_dollar := msg
		fields770 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields771 := fields770
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field772 := unwrapped_fields771[0].(int64)
		p.write(fmt.Sprintf("%d", field772))
		p.newline()
		field773 := unwrapped_fields771[1].(int64)
		p.write(fmt.Sprintf("%d", field773))
		p.newline()
		field774 := unwrapped_fields771[2].(int64)
		p.write(fmt.Sprintf("%d", field774))
		p.newline()
		field775 := unwrapped_fields771[3].(int64)
		p.write(fmt.Sprintf("%d", field775))
		p.newline()
		field776 := unwrapped_fields771[4].(int64)
		p.write(fmt.Sprintf("%d", field776))
		p.newline()
		field777 := unwrapped_fields771[5].(int64)
		p.write(fmt.Sprintf("%d", field777))
		field778 := unwrapped_fields771[6].(*int64)
		if field778 != nil {
			p.newline()
			opt_val779 := *field778
			p.write(fmt.Sprintf("%d", opt_val779))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1447 []interface{}
	if _dollar_dollar {
		_t1447 = []interface{}{}
	}
	deconstruct_result783 := _t1447
	if deconstruct_result783 != nil {
		unwrapped784 := deconstruct_result783
		_ = unwrapped784
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1448 []interface{}
		if !(_dollar_dollar) {
			_t1448 = []interface{}{}
		}
		deconstruct_result781 := _t1448
		if deconstruct_result781 != nil {
			unwrapped782 := deconstruct_result781
			_ = unwrapped782
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat789 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat789 != nil {
		p.write(*flat789)
		return nil
	} else {
		_dollar_dollar := msg
		fields785 := _dollar_dollar.GetFragments()
		unwrapped_fields786 := fields785
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields786) == 0) {
			p.newline()
			for i788, elem787 := range unwrapped_fields786 {
				if (i788 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem787)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat792 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat792 != nil {
		p.write(*flat792)
		return nil
	} else {
		_dollar_dollar := msg
		fields790 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields791 := fields790
		p.write(":")
		p.write(unwrapped_fields791)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat799 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat799 != nil {
		p.write(*flat799)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1449 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1449 = _dollar_dollar.GetWrites()
		}
		var _t1450 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1450 = _dollar_dollar.GetReads()
		}
		fields793 := []interface{}{_t1449, _t1450}
		unwrapped_fields794 := fields793
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field795 := unwrapped_fields794[0].([]*pb.Write)
		if field795 != nil {
			p.newline()
			opt_val796 := field795
			p.pretty_epoch_writes(opt_val796)
		}
		field797 := unwrapped_fields794[1].([]*pb.Read)
		if field797 != nil {
			p.newline()
			opt_val798 := field797
			p.pretty_epoch_reads(opt_val798)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat803 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat803 != nil {
		p.write(*flat803)
		return nil
	} else {
		fields800 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields800) == 0) {
			p.newline()
			for i802, elem801 := range fields800 {
				if (i802 > 0) {
					p.newline()
				}
				p.pretty_write(elem801)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat812 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat812 != nil {
		p.write(*flat812)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1451 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1451 = _dollar_dollar.GetDefine()
		}
		deconstruct_result810 := _t1451
		if deconstruct_result810 != nil {
			unwrapped811 := deconstruct_result810
			p.pretty_define(unwrapped811)
		} else {
			_dollar_dollar := msg
			var _t1452 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1452 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result808 := _t1452
			if deconstruct_result808 != nil {
				unwrapped809 := deconstruct_result808
				p.pretty_undefine(unwrapped809)
			} else {
				_dollar_dollar := msg
				var _t1453 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1453 = _dollar_dollar.GetContext()
				}
				deconstruct_result806 := _t1453
				if deconstruct_result806 != nil {
					unwrapped807 := deconstruct_result806
					p.pretty_context(unwrapped807)
				} else {
					_dollar_dollar := msg
					var _t1454 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1454 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result804 := _t1454
					if deconstruct_result804 != nil {
						unwrapped805 := deconstruct_result804
						p.pretty_snapshot(unwrapped805)
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
	flat815 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat815 != nil {
		p.write(*flat815)
		return nil
	} else {
		_dollar_dollar := msg
		fields813 := _dollar_dollar.GetFragment()
		unwrapped_fields814 := fields813
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields814)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat822 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat822 != nil {
		p.write(*flat822)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields816 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields817 := fields816
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field818 := unwrapped_fields817[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field818)
		field819 := unwrapped_fields817[1].([]*pb.Declaration)
		if !(len(field819) == 0) {
			p.newline()
			for i821, elem820 := range field819 {
				if (i821 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem820)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat824 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat824 != nil {
		p.write(*flat824)
		return nil
	} else {
		fields823 := msg
		p.pretty_fragment_id(fields823)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat833 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat833 != nil {
		p.write(*flat833)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1455 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1455 = _dollar_dollar.GetDef()
		}
		deconstruct_result831 := _t1455
		if deconstruct_result831 != nil {
			unwrapped832 := deconstruct_result831
			p.pretty_def(unwrapped832)
		} else {
			_dollar_dollar := msg
			var _t1456 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1456 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result829 := _t1456
			if deconstruct_result829 != nil {
				unwrapped830 := deconstruct_result829
				p.pretty_algorithm(unwrapped830)
			} else {
				_dollar_dollar := msg
				var _t1457 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1457 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result827 := _t1457
				if deconstruct_result827 != nil {
					unwrapped828 := deconstruct_result827
					p.pretty_constraint(unwrapped828)
				} else {
					_dollar_dollar := msg
					var _t1458 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1458 = _dollar_dollar.GetData()
					}
					deconstruct_result825 := _t1458
					if deconstruct_result825 != nil {
						unwrapped826 := deconstruct_result825
						p.pretty_data(unwrapped826)
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
	flat840 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat840 != nil {
		p.write(*flat840)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1459 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1459 = _dollar_dollar.GetAttrs()
		}
		fields834 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1459}
		unwrapped_fields835 := fields834
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field836 := unwrapped_fields835[0].(*pb.RelationId)
		p.pretty_relation_id(field836)
		p.newline()
		field837 := unwrapped_fields835[1].(*pb.Abstraction)
		p.pretty_abstraction(field837)
		field838 := unwrapped_fields835[2].([]*pb.Attribute)
		if field838 != nil {
			p.newline()
			opt_val839 := field838
			p.pretty_attrs(opt_val839)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat845 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat845 != nil {
		p.write(*flat845)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1460 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1461 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1460 = ptr(_t1461)
		}
		deconstruct_result843 := _t1460
		if deconstruct_result843 != nil {
			unwrapped844 := *deconstruct_result843
			p.write(":")
			p.write(unwrapped844)
		} else {
			_dollar_dollar := msg
			_t1462 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result841 := _t1462
			if deconstruct_result841 != nil {
				unwrapped842 := deconstruct_result841
				p.write(p.formatUint128(unwrapped842))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat850 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat850 != nil {
		p.write(*flat850)
		return nil
	} else {
		_dollar_dollar := msg
		_t1463 := p.deconstruct_bindings(_dollar_dollar)
		fields846 := []interface{}{_t1463, _dollar_dollar.GetValue()}
		unwrapped_fields847 := fields846
		p.write("(")
		p.indent()
		field848 := unwrapped_fields847[0].([]interface{})
		p.pretty_bindings(field848)
		p.newline()
		field849 := unwrapped_fields847[1].(*pb.Formula)
		p.pretty_formula(field849)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1464 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1464 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields851 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1464}
		unwrapped_fields852 := fields851
		p.write("[")
		p.indent()
		field853 := unwrapped_fields852[0].([]*pb.Binding)
		for i855, elem854 := range field853 {
			if (i855 > 0) {
				p.newline()
			}
			p.pretty_binding(elem854)
		}
		field856 := unwrapped_fields852[1].([]*pb.Binding)
		if field856 != nil {
			p.newline()
			opt_val857 := field856
			p.pretty_value_bindings(opt_val857)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		fields859 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields860 := fields859
		field861 := unwrapped_fields860[0].(string)
		p.write(field861)
		p.write("::")
		field862 := unwrapped_fields860[1].(*pb.Type)
		p.pretty_type(field862)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat892 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat892 != nil {
		p.write(*flat892)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1465 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1465 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result890 := _t1465
		if deconstruct_result890 != nil {
			unwrapped891 := deconstruct_result890
			p.pretty_unspecified_type(unwrapped891)
		} else {
			_dollar_dollar := msg
			var _t1466 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1466 = _dollar_dollar.GetStringType()
			}
			deconstruct_result888 := _t1466
			if deconstruct_result888 != nil {
				unwrapped889 := deconstruct_result888
				p.pretty_string_type(unwrapped889)
			} else {
				_dollar_dollar := msg
				var _t1467 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1467 = _dollar_dollar.GetIntType()
				}
				deconstruct_result886 := _t1467
				if deconstruct_result886 != nil {
					unwrapped887 := deconstruct_result886
					p.pretty_int_type(unwrapped887)
				} else {
					_dollar_dollar := msg
					var _t1468 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1468 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result884 := _t1468
					if deconstruct_result884 != nil {
						unwrapped885 := deconstruct_result884
						p.pretty_float_type(unwrapped885)
					} else {
						_dollar_dollar := msg
						var _t1469 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1469 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result882 := _t1469
						if deconstruct_result882 != nil {
							unwrapped883 := deconstruct_result882
							p.pretty_uint128_type(unwrapped883)
						} else {
							_dollar_dollar := msg
							var _t1470 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1470 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result880 := _t1470
							if deconstruct_result880 != nil {
								unwrapped881 := deconstruct_result880
								p.pretty_int128_type(unwrapped881)
							} else {
								_dollar_dollar := msg
								var _t1471 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1471 = _dollar_dollar.GetDateType()
								}
								deconstruct_result878 := _t1471
								if deconstruct_result878 != nil {
									unwrapped879 := deconstruct_result878
									p.pretty_date_type(unwrapped879)
								} else {
									_dollar_dollar := msg
									var _t1472 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1472 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result876 := _t1472
									if deconstruct_result876 != nil {
										unwrapped877 := deconstruct_result876
										p.pretty_datetime_type(unwrapped877)
									} else {
										_dollar_dollar := msg
										var _t1473 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1473 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result874 := _t1473
										if deconstruct_result874 != nil {
											unwrapped875 := deconstruct_result874
											p.pretty_missing_type(unwrapped875)
										} else {
											_dollar_dollar := msg
											var _t1474 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1474 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result872 := _t1474
											if deconstruct_result872 != nil {
												unwrapped873 := deconstruct_result872
												p.pretty_decimal_type(unwrapped873)
											} else {
												_dollar_dollar := msg
												var _t1475 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1475 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result870 := _t1475
												if deconstruct_result870 != nil {
													unwrapped871 := deconstruct_result870
													p.pretty_boolean_type(unwrapped871)
												} else {
													_dollar_dollar := msg
													var _t1476 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1476 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result868 := _t1476
													if deconstruct_result868 != nil {
														unwrapped869 := deconstruct_result868
														p.pretty_int32_type(unwrapped869)
													} else {
														_dollar_dollar := msg
														var _t1477 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1477 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result866 := _t1477
														if deconstruct_result866 != nil {
															unwrapped867 := deconstruct_result866
															p.pretty_float32_type(unwrapped867)
														} else {
															_dollar_dollar := msg
															var _t1478 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1478 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result864 := _t1478
															if deconstruct_result864 != nil {
																unwrapped865 := deconstruct_result864
																p.pretty_uint32_type(unwrapped865)
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
	fields893 := msg
	_ = fields893
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields894 := msg
	_ = fields894
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields895 := msg
	_ = fields895
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields896 := msg
	_ = fields896
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields897 := msg
	_ = fields897
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields898 := msg
	_ = fields898
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields899 := msg
	_ = fields899
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields900 := msg
	_ = fields900
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields901 := msg
	_ = fields901
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		fields902 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields903 := fields902
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field904 := unwrapped_fields903[0].(int64)
		p.write(fmt.Sprintf("%d", field904))
		p.newline()
		field905 := unwrapped_fields903[1].(int64)
		p.write(fmt.Sprintf("%d", field905))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields907 := msg
	_ = fields907
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields908 := msg
	_ = fields908
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields909 := msg
	_ = fields909
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields910 := msg
	_ = fields910
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat914 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat914 != nil {
		p.write(*flat914)
		return nil
	} else {
		fields911 := msg
		p.write("|")
		if !(len(fields911) == 0) {
			p.write(" ")
			for i913, elem912 := range fields911 {
				if (i913 > 0) {
					p.newline()
				}
				p.pretty_binding(elem912)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat941 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1479 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1479 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result939 := _t1479
		if deconstruct_result939 != nil {
			unwrapped940 := deconstruct_result939
			p.pretty_true(unwrapped940)
		} else {
			_dollar_dollar := msg
			var _t1480 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1480 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result937 := _t1480
			if deconstruct_result937 != nil {
				unwrapped938 := deconstruct_result937
				p.pretty_false(unwrapped938)
			} else {
				_dollar_dollar := msg
				var _t1481 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1481 = _dollar_dollar.GetExists()
				}
				deconstruct_result935 := _t1481
				if deconstruct_result935 != nil {
					unwrapped936 := deconstruct_result935
					p.pretty_exists(unwrapped936)
				} else {
					_dollar_dollar := msg
					var _t1482 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1482 = _dollar_dollar.GetReduce()
					}
					deconstruct_result933 := _t1482
					if deconstruct_result933 != nil {
						unwrapped934 := deconstruct_result933
						p.pretty_reduce(unwrapped934)
					} else {
						_dollar_dollar := msg
						var _t1483 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1483 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result931 := _t1483
						if deconstruct_result931 != nil {
							unwrapped932 := deconstruct_result931
							p.pretty_conjunction(unwrapped932)
						} else {
							_dollar_dollar := msg
							var _t1484 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1484 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result929 := _t1484
							if deconstruct_result929 != nil {
								unwrapped930 := deconstruct_result929
								p.pretty_disjunction(unwrapped930)
							} else {
								_dollar_dollar := msg
								var _t1485 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1485 = _dollar_dollar.GetNot()
								}
								deconstruct_result927 := _t1485
								if deconstruct_result927 != nil {
									unwrapped928 := deconstruct_result927
									p.pretty_not(unwrapped928)
								} else {
									_dollar_dollar := msg
									var _t1486 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1486 = _dollar_dollar.GetFfi()
									}
									deconstruct_result925 := _t1486
									if deconstruct_result925 != nil {
										unwrapped926 := deconstruct_result925
										p.pretty_ffi(unwrapped926)
									} else {
										_dollar_dollar := msg
										var _t1487 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1487 = _dollar_dollar.GetAtom()
										}
										deconstruct_result923 := _t1487
										if deconstruct_result923 != nil {
											unwrapped924 := deconstruct_result923
											p.pretty_atom(unwrapped924)
										} else {
											_dollar_dollar := msg
											var _t1488 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1488 = _dollar_dollar.GetPragma()
											}
											deconstruct_result921 := _t1488
											if deconstruct_result921 != nil {
												unwrapped922 := deconstruct_result921
												p.pretty_pragma(unwrapped922)
											} else {
												_dollar_dollar := msg
												var _t1489 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1489 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result919 := _t1489
												if deconstruct_result919 != nil {
													unwrapped920 := deconstruct_result919
													p.pretty_primitive(unwrapped920)
												} else {
													_dollar_dollar := msg
													var _t1490 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1490 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result917 := _t1490
													if deconstruct_result917 != nil {
														unwrapped918 := deconstruct_result917
														p.pretty_rel_atom(unwrapped918)
													} else {
														_dollar_dollar := msg
														var _t1491 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1491 = _dollar_dollar.GetCast()
														}
														deconstruct_result915 := _t1491
														if deconstruct_result915 != nil {
															unwrapped916 := deconstruct_result915
															p.pretty_cast(unwrapped916)
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
	fields942 := msg
	_ = fields942
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields943 := msg
	_ = fields943
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat948 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat948 != nil {
		p.write(*flat948)
		return nil
	} else {
		_dollar_dollar := msg
		_t1492 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields944 := []interface{}{_t1492, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields945 := fields944
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field946 := unwrapped_fields945[0].([]interface{})
		p.pretty_bindings(field946)
		p.newline()
		field947 := unwrapped_fields945[1].(*pb.Formula)
		p.pretty_formula(field947)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat954 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat954 != nil {
		p.write(*flat954)
		return nil
	} else {
		_dollar_dollar := msg
		fields949 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields950 := fields949
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field951 := unwrapped_fields950[0].(*pb.Abstraction)
		p.pretty_abstraction(field951)
		p.newline()
		field952 := unwrapped_fields950[1].(*pb.Abstraction)
		p.pretty_abstraction(field952)
		p.newline()
		field953 := unwrapped_fields950[2].([]*pb.Term)
		p.pretty_terms(field953)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		fields955 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields955) == 0) {
			p.newline()
			for i957, elem956 := range fields955 {
				if (i957 > 0) {
					p.newline()
				}
				p.pretty_term(elem956)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat963 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat963 != nil {
		p.write(*flat963)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1493 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1493 = _dollar_dollar.GetVar()
		}
		deconstruct_result961 := _t1493
		if deconstruct_result961 != nil {
			unwrapped962 := deconstruct_result961
			p.pretty_var(unwrapped962)
		} else {
			_dollar_dollar := msg
			var _t1494 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1494 = _dollar_dollar.GetConstant()
			}
			deconstruct_result959 := _t1494
			if deconstruct_result959 != nil {
				unwrapped960 := deconstruct_result959
				p.pretty_constant(unwrapped960)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat966 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_dollar_dollar := msg
		fields964 := _dollar_dollar.GetName()
		unwrapped_fields965 := fields964
		p.write(unwrapped_fields965)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat968 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		fields967 := msg
		p.pretty_value(fields967)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat973 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat973 != nil {
		p.write(*flat973)
		return nil
	} else {
		_dollar_dollar := msg
		fields969 := _dollar_dollar.GetArgs()
		unwrapped_fields970 := fields969
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields970) == 0) {
			p.newline()
			for i972, elem971 := range unwrapped_fields970 {
				if (i972 > 0) {
					p.newline()
				}
				p.pretty_formula(elem971)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat978 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat978 != nil {
		p.write(*flat978)
		return nil
	} else {
		_dollar_dollar := msg
		fields974 := _dollar_dollar.GetArgs()
		unwrapped_fields975 := fields974
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields975) == 0) {
			p.newline()
			for i977, elem976 := range unwrapped_fields975 {
				if (i977 > 0) {
					p.newline()
				}
				p.pretty_formula(elem976)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat981 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat981 != nil {
		p.write(*flat981)
		return nil
	} else {
		_dollar_dollar := msg
		fields979 := _dollar_dollar.GetArg()
		unwrapped_fields980 := fields979
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields980)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat987 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat987 != nil {
		p.write(*flat987)
		return nil
	} else {
		_dollar_dollar := msg
		fields982 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields983 := fields982
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field984 := unwrapped_fields983[0].(string)
		p.pretty_name(field984)
		p.newline()
		field985 := unwrapped_fields983[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field985)
		p.newline()
		field986 := unwrapped_fields983[2].([]*pb.Term)
		p.pretty_terms(field986)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		fields988 := msg
		p.write(":")
		p.write(fields988)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat993 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat993 != nil {
		p.write(*flat993)
		return nil
	} else {
		fields990 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields990) == 0) {
			p.newline()
			for i992, elem991 := range fields990 {
				if (i992 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem991)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1000 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1000 != nil {
		p.write(*flat1000)
		return nil
	} else {
		_dollar_dollar := msg
		fields994 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields995 := fields994
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field996 := unwrapped_fields995[0].(*pb.RelationId)
		p.pretty_relation_id(field996)
		field997 := unwrapped_fields995[1].([]*pb.Term)
		if !(len(field997) == 0) {
			p.newline()
			for i999, elem998 := range field997 {
				if (i999 > 0) {
					p.newline()
				}
				p.pretty_term(elem998)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		_dollar_dollar := msg
		fields1001 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1002 := fields1001
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1003 := unwrapped_fields1002[0].(string)
		p.pretty_name(field1003)
		field1004 := unwrapped_fields1002[1].([]*pb.Term)
		if !(len(field1004) == 0) {
			p.newline()
			for i1006, elem1005 := range field1004 {
				if (i1006 > 0) {
					p.newline()
				}
				p.pretty_term(elem1005)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1023 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1023 != nil {
		p.write(*flat1023)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1495 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1495 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1022 := _t1495
		if guard_result1022 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1496 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1496 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1021 := _t1496
			if guard_result1021 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1497 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1497 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1020 := _t1497
				if guard_result1020 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1498 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1498 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1019 := _t1498
					if guard_result1019 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1499 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1499 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1018 := _t1499
						if guard_result1018 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1500 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1500 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1017 := _t1500
							if guard_result1017 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1501 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1501 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1016 := _t1501
								if guard_result1016 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1502 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1502 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1015 := _t1502
									if guard_result1015 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1503 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1503 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1014 := _t1503
										if guard_result1014 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1008 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1009 := fields1008
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1010 := unwrapped_fields1009[0].(string)
											p.pretty_name(field1010)
											field1011 := unwrapped_fields1009[1].([]*pb.RelTerm)
											if !(len(field1011) == 0) {
												p.newline()
												for i1013, elem1012 := range field1011 {
													if (i1013 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1012)
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
	flat1028 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1504 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1504 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1024 := _t1504
		unwrapped_fields1025 := fields1024
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1026 := unwrapped_fields1025[0].(*pb.Term)
		p.pretty_term(field1026)
		p.newline()
		field1027 := unwrapped_fields1025[1].(*pb.Term)
		p.pretty_term(field1027)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1033 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1033 != nil {
		p.write(*flat1033)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1505 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1505 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1029 := _t1505
		unwrapped_fields1030 := fields1029
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1031 := unwrapped_fields1030[0].(*pb.Term)
		p.pretty_term(field1031)
		p.newline()
		field1032 := unwrapped_fields1030[1].(*pb.Term)
		p.pretty_term(field1032)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1038 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1038 != nil {
		p.write(*flat1038)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1506 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1506 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1034 := _t1506
		unwrapped_fields1035 := fields1034
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1036 := unwrapped_fields1035[0].(*pb.Term)
		p.pretty_term(field1036)
		p.newline()
		field1037 := unwrapped_fields1035[1].(*pb.Term)
		p.pretty_term(field1037)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1043 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1043 != nil {
		p.write(*flat1043)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1507 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1507 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1039 := _t1507
		unwrapped_fields1040 := fields1039
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1041 := unwrapped_fields1040[0].(*pb.Term)
		p.pretty_term(field1041)
		p.newline()
		field1042 := unwrapped_fields1040[1].(*pb.Term)
		p.pretty_term(field1042)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1048 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1048 != nil {
		p.write(*flat1048)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1508 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1508 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1044 := _t1508
		unwrapped_fields1045 := fields1044
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1046 := unwrapped_fields1045[0].(*pb.Term)
		p.pretty_term(field1046)
		p.newline()
		field1047 := unwrapped_fields1045[1].(*pb.Term)
		p.pretty_term(field1047)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1054 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1509 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1509 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1049 := _t1509
		unwrapped_fields1050 := fields1049
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1051 := unwrapped_fields1050[0].(*pb.Term)
		p.pretty_term(field1051)
		p.newline()
		field1052 := unwrapped_fields1050[1].(*pb.Term)
		p.pretty_term(field1052)
		p.newline()
		field1053 := unwrapped_fields1050[2].(*pb.Term)
		p.pretty_term(field1053)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1060 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1060 != nil {
		p.write(*flat1060)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1510 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1510 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1055 := _t1510
		unwrapped_fields1056 := fields1055
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1057 := unwrapped_fields1056[0].(*pb.Term)
		p.pretty_term(field1057)
		p.newline()
		field1058 := unwrapped_fields1056[1].(*pb.Term)
		p.pretty_term(field1058)
		p.newline()
		field1059 := unwrapped_fields1056[2].(*pb.Term)
		p.pretty_term(field1059)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1066 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1066 != nil {
		p.write(*flat1066)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1511 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1511 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1061 := _t1511
		unwrapped_fields1062 := fields1061
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1063 := unwrapped_fields1062[0].(*pb.Term)
		p.pretty_term(field1063)
		p.newline()
		field1064 := unwrapped_fields1062[1].(*pb.Term)
		p.pretty_term(field1064)
		p.newline()
		field1065 := unwrapped_fields1062[2].(*pb.Term)
		p.pretty_term(field1065)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1072 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1072 != nil {
		p.write(*flat1072)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1512 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1512 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1067 := _t1512
		unwrapped_fields1068 := fields1067
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1069 := unwrapped_fields1068[0].(*pb.Term)
		p.pretty_term(field1069)
		p.newline()
		field1070 := unwrapped_fields1068[1].(*pb.Term)
		p.pretty_term(field1070)
		p.newline()
		field1071 := unwrapped_fields1068[2].(*pb.Term)
		p.pretty_term(field1071)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1077 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1077 != nil {
		p.write(*flat1077)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1513 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1513 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1075 := _t1513
		if deconstruct_result1075 != nil {
			unwrapped1076 := deconstruct_result1075
			p.pretty_specialized_value(unwrapped1076)
		} else {
			_dollar_dollar := msg
			var _t1514 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1514 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1073 := _t1514
			if deconstruct_result1073 != nil {
				unwrapped1074 := deconstruct_result1073
				p.pretty_term(unwrapped1074)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		fields1078 := msg
		p.write("#")
		p.pretty_value(fields1078)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1086 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1086 != nil {
		p.write(*flat1086)
		return nil
	} else {
		_dollar_dollar := msg
		fields1080 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1081 := fields1080
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1082 := unwrapped_fields1081[0].(string)
		p.pretty_name(field1082)
		field1083 := unwrapped_fields1081[1].([]*pb.RelTerm)
		if !(len(field1083) == 0) {
			p.newline()
			for i1085, elem1084 := range field1083 {
				if (i1085 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1084)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1091 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1091 != nil {
		p.write(*flat1091)
		return nil
	} else {
		_dollar_dollar := msg
		fields1087 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1088 := fields1087
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1089 := unwrapped_fields1088[0].(*pb.Term)
		p.pretty_term(field1089)
		p.newline()
		field1090 := unwrapped_fields1088[1].(*pb.Term)
		p.pretty_term(field1090)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1095 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1095 != nil {
		p.write(*flat1095)
		return nil
	} else {
		fields1092 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1092) == 0) {
			p.newline()
			for i1094, elem1093 := range fields1092 {
				if (i1094 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1093)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1096 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1097 := fields1096
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1098 := unwrapped_fields1097[0].(string)
		p.pretty_name(field1098)
		field1099 := unwrapped_fields1097[1].([]*pb.Value)
		if !(len(field1099) == 0) {
			p.newline()
			for i1101, elem1100 := range field1099 {
				if (i1101 > 0) {
					p.newline()
				}
				p.pretty_value(elem1100)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		_dollar_dollar := msg
		fields1103 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1104 := fields1103
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1105 := unwrapped_fields1104[0].([]*pb.RelationId)
		if !(len(field1105) == 0) {
			p.newline()
			for i1107, elem1106 := range field1105 {
				if (i1107 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1106)
			}
		}
		p.newline()
		field1108 := unwrapped_fields1104[1].(*pb.Script)
		p.pretty_script(field1108)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_dollar_dollar := msg
		fields1110 := _dollar_dollar.GetConstructs()
		unwrapped_fields1111 := fields1110
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1111) == 0) {
			p.newline()
			for i1113, elem1112 := range unwrapped_fields1111 {
				if (i1113 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1112)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1119 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1119 != nil {
		p.write(*flat1119)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1515 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1515 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1117 := _t1515
		if deconstruct_result1117 != nil {
			unwrapped1118 := deconstruct_result1117
			p.pretty_loop(unwrapped1118)
		} else {
			_dollar_dollar := msg
			var _t1516 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1516 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1115 := _t1516
			if deconstruct_result1115 != nil {
				unwrapped1116 := deconstruct_result1115
				p.pretty_instruction(unwrapped1116)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1124 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1124 != nil {
		p.write(*flat1124)
		return nil
	} else {
		_dollar_dollar := msg
		fields1120 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1121 := fields1120
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1122 := unwrapped_fields1121[0].([]*pb.Instruction)
		p.pretty_init(field1122)
		p.newline()
		field1123 := unwrapped_fields1121[1].(*pb.Script)
		p.pretty_script(field1123)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1128 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1128 != nil {
		p.write(*flat1128)
		return nil
	} else {
		fields1125 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1125) == 0) {
			p.newline()
			for i1127, elem1126 := range fields1125 {
				if (i1127 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1126)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1517 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1517 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1137 := _t1517
		if deconstruct_result1137 != nil {
			unwrapped1138 := deconstruct_result1137
			p.pretty_assign(unwrapped1138)
		} else {
			_dollar_dollar := msg
			var _t1518 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1518 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1135 := _t1518
			if deconstruct_result1135 != nil {
				unwrapped1136 := deconstruct_result1135
				p.pretty_upsert(unwrapped1136)
			} else {
				_dollar_dollar := msg
				var _t1519 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1519 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1133 := _t1519
				if deconstruct_result1133 != nil {
					unwrapped1134 := deconstruct_result1133
					p.pretty_break(unwrapped1134)
				} else {
					_dollar_dollar := msg
					var _t1520 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1520 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1131 := _t1520
					if deconstruct_result1131 != nil {
						unwrapped1132 := deconstruct_result1131
						p.pretty_monoid_def(unwrapped1132)
					} else {
						_dollar_dollar := msg
						var _t1521 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1521 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1129 := _t1521
						if deconstruct_result1129 != nil {
							unwrapped1130 := deconstruct_result1129
							p.pretty_monus_def(unwrapped1130)
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
	flat1146 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1522 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1522 = _dollar_dollar.GetAttrs()
		}
		fields1140 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1522}
		unwrapped_fields1141 := fields1140
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1142 := unwrapped_fields1141[0].(*pb.RelationId)
		p.pretty_relation_id(field1142)
		p.newline()
		field1143 := unwrapped_fields1141[1].(*pb.Abstraction)
		p.pretty_abstraction(field1143)
		field1144 := unwrapped_fields1141[2].([]*pb.Attribute)
		if field1144 != nil {
			p.newline()
			opt_val1145 := field1144
			p.pretty_attrs(opt_val1145)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1523 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1523 = _dollar_dollar.GetAttrs()
		}
		fields1147 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1523}
		unwrapped_fields1148 := fields1147
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1149 := unwrapped_fields1148[0].(*pb.RelationId)
		p.pretty_relation_id(field1149)
		p.newline()
		field1150 := unwrapped_fields1148[1].([]interface{})
		p.pretty_abstraction_with_arity(field1150)
		field1151 := unwrapped_fields1148[2].([]*pb.Attribute)
		if field1151 != nil {
			p.newline()
			opt_val1152 := field1151
			p.pretty_attrs(opt_val1152)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1158 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		_dollar_dollar := msg
		_t1524 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1154 := []interface{}{_t1524, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.indent()
		field1156 := unwrapped_fields1155[0].([]interface{})
		p.pretty_bindings(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].(*pb.Formula)
		p.pretty_formula(field1157)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1525 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1525 = _dollar_dollar.GetAttrs()
		}
		fields1159 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1525}
		unwrapped_fields1160 := fields1159
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1161 := unwrapped_fields1160[0].(*pb.RelationId)
		p.pretty_relation_id(field1161)
		p.newline()
		field1162 := unwrapped_fields1160[1].(*pb.Abstraction)
		p.pretty_abstraction(field1162)
		field1163 := unwrapped_fields1160[2].([]*pb.Attribute)
		if field1163 != nil {
			p.newline()
			opt_val1164 := field1163
			p.pretty_attrs(opt_val1164)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1526 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1526 = _dollar_dollar.GetAttrs()
		}
		fields1166 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1526}
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.Monoid)
		p.pretty_monoid(field1168)
		p.newline()
		field1169 := unwrapped_fields1167[1].(*pb.RelationId)
		p.pretty_relation_id(field1169)
		p.newline()
		field1170 := unwrapped_fields1167[2].([]interface{})
		p.pretty_abstraction_with_arity(field1170)
		field1171 := unwrapped_fields1167[3].([]*pb.Attribute)
		if field1171 != nil {
			p.newline()
			opt_val1172 := field1171
			p.pretty_attrs(opt_val1172)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1527 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1527 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1180 := _t1527
		if deconstruct_result1180 != nil {
			unwrapped1181 := deconstruct_result1180
			p.pretty_or_monoid(unwrapped1181)
		} else {
			_dollar_dollar := msg
			var _t1528 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1528 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1178 := _t1528
			if deconstruct_result1178 != nil {
				unwrapped1179 := deconstruct_result1178
				p.pretty_min_monoid(unwrapped1179)
			} else {
				_dollar_dollar := msg
				var _t1529 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1529 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1176 := _t1529
				if deconstruct_result1176 != nil {
					unwrapped1177 := deconstruct_result1176
					p.pretty_max_monoid(unwrapped1177)
				} else {
					_dollar_dollar := msg
					var _t1530 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1530 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1174 := _t1530
					if deconstruct_result1174 != nil {
						unwrapped1175 := deconstruct_result1174
						p.pretty_sum_monoid(unwrapped1175)
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
	fields1183 := msg
	_ = fields1183
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		fields1184 := _dollar_dollar.GetType()
		unwrapped_fields1185 := fields1184
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1185)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_dollar_dollar := msg
		fields1187 := _dollar_dollar.GetType()
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1188)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		_dollar_dollar := msg
		fields1190 := _dollar_dollar.GetType()
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1191)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1531 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1531 = _dollar_dollar.GetAttrs()
		}
		fields1193 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1531}
		unwrapped_fields1194 := fields1193
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1195 := unwrapped_fields1194[0].(*pb.Monoid)
		p.pretty_monoid(field1195)
		p.newline()
		field1196 := unwrapped_fields1194[1].(*pb.RelationId)
		p.pretty_relation_id(field1196)
		p.newline()
		field1197 := unwrapped_fields1194[2].([]interface{})
		p.pretty_abstraction_with_arity(field1197)
		field1198 := unwrapped_fields1194[3].([]*pb.Attribute)
		if field1198 != nil {
			p.newline()
			opt_val1199 := field1198
			p.pretty_attrs(opt_val1199)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1207 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		_dollar_dollar := msg
		fields1201 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(*pb.RelationId)
		p.pretty_relation_id(field1203)
		p.newline()
		field1204 := unwrapped_fields1202[1].(*pb.Abstraction)
		p.pretty_abstraction(field1204)
		p.newline()
		field1205 := unwrapped_fields1202[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1205)
		p.newline()
		field1206 := unwrapped_fields1202[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1206)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		fields1208 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1208) == 0) {
			p.newline()
			for i1210, elem1209 := range fields1208 {
				if (i1210 > 0) {
					p.newline()
				}
				p.pretty_var(elem1209)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		fields1212 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1212) == 0) {
			p.newline()
			for i1214, elem1213 := range fields1212 {
				if (i1214 > 0) {
					p.newline()
				}
				p.pretty_var(elem1213)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1532 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1532 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1222 := _t1532
		if deconstruct_result1222 != nil {
			unwrapped1223 := deconstruct_result1222
			p.pretty_edb(unwrapped1223)
		} else {
			_dollar_dollar := msg
			var _t1533 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1533 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1220 := _t1533
			if deconstruct_result1220 != nil {
				unwrapped1221 := deconstruct_result1220
				p.pretty_betree_relation(unwrapped1221)
			} else {
				_dollar_dollar := msg
				var _t1534 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1534 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1218 := _t1534
				if deconstruct_result1218 != nil {
					unwrapped1219 := deconstruct_result1218
					p.pretty_csv_data(unwrapped1219)
				} else {
					_dollar_dollar := msg
					var _t1535 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1535 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1216 := _t1535
					if deconstruct_result1216 != nil {
						unwrapped1217 := deconstruct_result1216
						p.pretty_iceberg_data(unwrapped1217)
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
	flat1230 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1230 != nil {
		p.write(*flat1230)
		return nil
	} else {
		_dollar_dollar := msg
		fields1225 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1226 := fields1225
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1227 := unwrapped_fields1226[0].(*pb.RelationId)
		p.pretty_relation_id(field1227)
		p.newline()
		field1228 := unwrapped_fields1226[1].([]string)
		p.pretty_edb_path(field1228)
		p.newline()
		field1229 := unwrapped_fields1226[2].([]*pb.Type)
		p.pretty_edb_types(field1229)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		fields1231 := msg
		p.write("[")
		p.indent()
		for i1233, elem1232 := range fields1231 {
			if (i1233 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1232))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1238 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		fields1235 := msg
		p.write("[")
		p.indent()
		for i1237, elem1236 := range fields1235 {
			if (i1237 > 0) {
				p.newline()
			}
			p.pretty_type(elem1236)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1243 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_dollar_dollar := msg
		fields1239 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1241 := unwrapped_fields1240[0].(*pb.RelationId)
		p.pretty_relation_id(field1241)
		p.newline()
		field1242 := unwrapped_fields1240[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1242)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		_t1536 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1244 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1536}
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1246 := unwrapped_fields1245[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1246)
		p.newline()
		field1247 := unwrapped_fields1245[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1247)
		p.newline()
		field1248 := unwrapped_fields1245[2].([][]interface{})
		p.pretty_config_dict(field1248)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		fields1250 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1250) == 0) {
			p.newline()
			for i1252, elem1251 := range fields1250 {
				if (i1252 > 0) {
					p.newline()
				}
				p.pretty_type(elem1251)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		fields1254 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1254) == 0) {
			p.newline()
			for i1256, elem1255 := range fields1254 {
				if (i1256 > 0) {
					p.newline()
				}
				p.pretty_type(elem1255)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		_dollar_dollar := msg
		fields1258 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1260 := unwrapped_fields1259[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1260)
		p.newline()
		field1261 := unwrapped_fields1259[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1261)
		p.newline()
		field1262 := unwrapped_fields1259[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1262)
		p.newline()
		field1263 := unwrapped_fields1259[3].(string)
		p.pretty_csv_asof(field1263)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1271 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1271 != nil {
		p.write(*flat1271)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1537 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1537 = _dollar_dollar.GetPaths()
		}
		var _t1538 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1538 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1265 := []interface{}{_t1537, _t1538}
		unwrapped_fields1266 := fields1265
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1267 := unwrapped_fields1266[0].([]string)
		if field1267 != nil {
			p.newline()
			opt_val1268 := field1267
			p.pretty_csv_locator_paths(opt_val1268)
		}
		field1269 := unwrapped_fields1266[1].(*string)
		if field1269 != nil {
			p.newline()
			opt_val1270 := *field1269
			p.pretty_csv_locator_inline_data(opt_val1270)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1275 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1275 != nil {
		p.write(*flat1275)
		return nil
	} else {
		fields1272 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1272) == 0) {
			p.newline()
			for i1274, elem1273 := range fields1272 {
				if (i1274 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1273))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1277 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		fields1276 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1276))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1280 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1280 != nil {
		p.write(*flat1280)
		return nil
	} else {
		_dollar_dollar := msg
		_t1539 := p.deconstruct_csv_config(_dollar_dollar)
		fields1278 := _t1539
		unwrapped_fields1279 := fields1278
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1279)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		fields1281 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1281) == 0) {
			p.newline()
			for i1283, elem1282 := range fields1281 {
				if (i1283 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1282)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1293 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1293 != nil {
		p.write(*flat1293)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1540 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1540 = _dollar_dollar.GetTargetId()
		}
		fields1285 := []interface{}{_dollar_dollar.GetColumnPath(), _t1540, _dollar_dollar.GetTypes()}
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].([]string)
		p.pretty_gnf_column_path(field1287)
		field1288 := unwrapped_fields1286[1].(*pb.RelationId)
		if field1288 != nil {
			p.newline()
			opt_val1289 := field1288
			p.pretty_relation_id(opt_val1289)
		}
		p.newline()
		p.write("[")
		field1290 := unwrapped_fields1286[2].([]*pb.Type)
		for i1292, elem1291 := range field1290 {
			if (i1292 > 0) {
				p.newline()
			}
			p.pretty_type(elem1291)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1300 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1300 != nil {
		p.write(*flat1300)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1541 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1541 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1298 := _t1541
		if deconstruct_result1298 != nil {
			unwrapped1299 := *deconstruct_result1298
			p.write(p.formatStringValue(unwrapped1299))
		} else {
			_dollar_dollar := msg
			var _t1542 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1542 = _dollar_dollar
			}
			deconstruct_result1294 := _t1542
			if deconstruct_result1294 != nil {
				unwrapped1295 := deconstruct_result1294
				p.write("[")
				p.indent()
				for i1297, elem1296 := range unwrapped1295 {
					if (i1297 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1296))
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
	flat1302 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1302 != nil {
		p.write(*flat1302)
		return nil
	} else {
		fields1301 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1301))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		_dollar_dollar := msg
		fields1303 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.ToSnapshot}
		unwrapped_fields1304 := fields1303
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1305 := unwrapped_fields1304[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1305)
		p.newline()
		field1306 := unwrapped_fields1304[1].(*pb.IcebergConfig)
		p.pretty_iceberg_config(field1306)
		p.newline()
		field1307 := unwrapped_fields1304[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1307)
		field1308 := unwrapped_fields1304[3].(*string)
		if field1308 != nil {
			p.newline()
			opt_val1309 := *field1308
			p.pretty_iceberg_to_snapshot(opt_val1309)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1316 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1316 != nil {
		p.write(*flat1316)
		return nil
	} else {
		_dollar_dollar := msg
		fields1311 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1312 := fields1311
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1313 := unwrapped_fields1312[0].(string)
		p.write(p.formatStringValue(field1313))
		p.newline()
		field1314 := unwrapped_fields1312[1].([]string)
		p.pretty_iceberg_locator_namespace(field1314)
		p.newline()
		field1315 := unwrapped_fields1312[2].(string)
		p.write(p.formatStringValue(field1315))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		fields1317 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1317) == 0) {
			p.newline()
			for i1319, elem1318 := range fields1317 {
				if (i1319 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1318))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config(msg *pb.IcebergConfig) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_iceberg_config(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1543 *string
		if _dollar_dollar.Scope != "" {
			_t1543 = _dollar_dollar.Scope
		}
		var _t1544 [][]interface{}
		if !(len(dictToPairs(_dollar_dollar.GetProperties())) == 0) {
			_t1544 = dictToPairs(_dollar_dollar.GetProperties())
		}
		fields1321 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1543, _t1544, nil}
		unwrapped_fields1322 := fields1321
		p.write("(")
		p.write("iceberg_config")
		p.indentSexp()
		p.newline()
		field1323 := unwrapped_fields1322[0].(string)
		p.write(p.formatStringValue(field1323))
		field1324 := unwrapped_fields1322[1].(*string)
		if field1324 != nil {
			p.newline()
			opt_val1325 := *field1324
			p.pretty_iceberg_config_scope(opt_val1325)
		}
		field1326 := unwrapped_fields1322[2].([][]interface{})
		if field1326 != nil {
			p.newline()
			opt_val1327 := field1326
			p.pretty_iceberg_config_properties(opt_val1327)
		}
		field1328 := unwrapped_fields1322[3].(interface{})
		if field1328 != nil {
			p.newline()
			opt_val1329 := field1328
			p.pretty_iceberg_config_credentials(opt_val1329)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config_scope(msg string) interface{} {
	flat1332 := p.tryFlat(msg, func() { p.pretty_iceberg_config_scope(msg) })
	if flat1332 != nil {
		p.write(*flat1332)
		return nil
	} else {
		fields1331 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1331))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config_properties(msg [][]interface{}) interface{} {
	flat1336 := p.tryFlat(msg, func() { p.pretty_iceberg_config_properties(msg) })
	if flat1336 != nil {
		p.write(*flat1336)
		return nil
	} else {
		fields1333 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1333) == 0) {
			p.newline()
			for i1335, elem1334 := range fields1333 {
				if (i1335 > 0) {
					p.newline()
				}
				p.pretty_iceberg_kv_pair(elem1334)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_kv_pair(msg []interface{}) interface{} {
	flat1341 := p.tryFlat(msg, func() { p.pretty_iceberg_kv_pair(msg) })
	if flat1341 != nil {
		p.write(*flat1341)
		return nil
	} else {
		_dollar_dollar := msg
		fields1337 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1338 := fields1337
		p.write("(")
		p.indent()
		field1339 := unwrapped_fields1338[0].(string)
		p.write(p.formatStringValue(field1339))
		p.newline()
		field1340 := unwrapped_fields1338[1].(string)
		p.write(p.formatStringValue(field1340))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config_credentials(msg [][]interface{}) interface{} {
	flat1345 := p.tryFlat(msg, func() { p.pretty_iceberg_config_credentials(msg) })
	if flat1345 != nil {
		p.write(*flat1345)
		return nil
	} else {
		fields1342 := msg
		p.write("(")
		p.write("credentials")
		p.indentSexp()
		if !(len(fields1342) == 0) {
			p.newline()
			for i1344, elem1343 := range fields1342 {
				if (i1344 > 0) {
					p.newline()
				}
				p.pretty_iceberg_kv_pair(elem1343)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1347 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1347 != nil {
		p.write(*flat1347)
		return nil
	} else {
		fields1346 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1346))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1350 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1350 != nil {
		p.write(*flat1350)
		return nil
	} else {
		_dollar_dollar := msg
		fields1348 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1349 := fields1348
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1349)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1355 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1355 != nil {
		p.write(*flat1355)
		return nil
	} else {
		_dollar_dollar := msg
		fields1351 := _dollar_dollar.GetRelations()
		unwrapped_fields1352 := fields1351
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1352) == 0) {
			p.newline()
			for i1354, elem1353 := range unwrapped_fields1352 {
				if (i1354 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1353)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1360 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1360 != nil {
		p.write(*flat1360)
		return nil
	} else {
		_dollar_dollar := msg
		fields1356 := _dollar_dollar.GetMappings()
		unwrapped_fields1357 := fields1356
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1357) == 0) {
			p.newline()
			for i1359, elem1358 := range unwrapped_fields1357 {
				if (i1359 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1358)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1365 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1365 != nil {
		p.write(*flat1365)
		return nil
	} else {
		_dollar_dollar := msg
		fields1361 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1362 := fields1361
		field1363 := unwrapped_fields1362[0].([]string)
		p.pretty_edb_path(field1363)
		p.write(" ")
		field1364 := unwrapped_fields1362[1].(*pb.RelationId)
		p.pretty_relation_id(field1364)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1369 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1369 != nil {
		p.write(*flat1369)
		return nil
	} else {
		fields1366 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1366) == 0) {
			p.newline()
			for i1368, elem1367 := range fields1366 {
				if (i1368 > 0) {
					p.newline()
				}
				p.pretty_read(elem1367)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1380 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1380 != nil {
		p.write(*flat1380)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1545 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1545 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1378 := _t1545
		if deconstruct_result1378 != nil {
			unwrapped1379 := deconstruct_result1378
			p.pretty_demand(unwrapped1379)
		} else {
			_dollar_dollar := msg
			var _t1546 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1546 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1376 := _t1546
			if deconstruct_result1376 != nil {
				unwrapped1377 := deconstruct_result1376
				p.pretty_output(unwrapped1377)
			} else {
				_dollar_dollar := msg
				var _t1547 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1547 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1374 := _t1547
				if deconstruct_result1374 != nil {
					unwrapped1375 := deconstruct_result1374
					p.pretty_what_if(unwrapped1375)
				} else {
					_dollar_dollar := msg
					var _t1548 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1548 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1372 := _t1548
					if deconstruct_result1372 != nil {
						unwrapped1373 := deconstruct_result1372
						p.pretty_abort(unwrapped1373)
					} else {
						_dollar_dollar := msg
						var _t1549 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1549 = _dollar_dollar.GetExport()
						}
						deconstruct_result1370 := _t1549
						if deconstruct_result1370 != nil {
							unwrapped1371 := deconstruct_result1370
							p.pretty_export(unwrapped1371)
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
	flat1383 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1383 != nil {
		p.write(*flat1383)
		return nil
	} else {
		_dollar_dollar := msg
		fields1381 := _dollar_dollar.GetRelationId()
		unwrapped_fields1382 := fields1381
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1382)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1388 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1388 != nil {
		p.write(*flat1388)
		return nil
	} else {
		_dollar_dollar := msg
		fields1384 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1385 := fields1384
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1386 := unwrapped_fields1385[0].(string)
		p.pretty_name(field1386)
		p.newline()
		field1387 := unwrapped_fields1385[1].(*pb.RelationId)
		p.pretty_relation_id(field1387)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1393 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1393 != nil {
		p.write(*flat1393)
		return nil
	} else {
		_dollar_dollar := msg
		fields1389 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1390 := fields1389
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1391 := unwrapped_fields1390[0].(string)
		p.pretty_name(field1391)
		p.newline()
		field1392 := unwrapped_fields1390[1].(*pb.Epoch)
		p.pretty_epoch(field1392)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1399 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1399 != nil {
		p.write(*flat1399)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1550 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1550 = ptr(_dollar_dollar.GetName())
		}
		fields1394 := []interface{}{_t1550, _dollar_dollar.GetRelationId()}
		unwrapped_fields1395 := fields1394
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1396 := unwrapped_fields1395[0].(*string)
		if field1396 != nil {
			p.newline()
			opt_val1397 := *field1396
			p.pretty_name(opt_val1397)
		}
		p.newline()
		field1398 := unwrapped_fields1395[1].(*pb.RelationId)
		p.pretty_relation_id(field1398)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1402 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1402 != nil {
		p.write(*flat1402)
		return nil
	} else {
		_dollar_dollar := msg
		fields1400 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1401 := fields1400
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1401)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1551 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1551 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1408 := _t1551
		if deconstruct_result1408 != nil {
			unwrapped1409 := deconstruct_result1408
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1410 := unwrapped1409[0].(string)
			p.pretty_export_csv_path(field1410)
			p.newline()
			field1411 := unwrapped1409[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1411)
			p.newline()
			field1412 := unwrapped1409[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1412)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1552 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1553 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1552 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1553}
			}
			deconstruct_result1403 := _t1552
			if deconstruct_result1403 != nil {
				unwrapped1404 := deconstruct_result1403
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1405 := unwrapped1404[0].(string)
				p.pretty_export_csv_path(field1405)
				p.newline()
				field1406 := unwrapped1404[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1406)
				p.newline()
				field1407 := unwrapped1404[2].([][]interface{})
				p.pretty_config_dict(field1407)
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
	flat1415 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1415 != nil {
		p.write(*flat1415)
		return nil
	} else {
		fields1414 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1414))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1422 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1422 != nil {
		p.write(*flat1422)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1554 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1554 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1418 := _t1554
		if deconstruct_result1418 != nil {
			unwrapped1419 := deconstruct_result1418
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1419) == 0) {
				p.newline()
				for i1421, elem1420 := range unwrapped1419 {
					if (i1421 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1420)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1555 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1555 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1416 := _t1555
			if deconstruct_result1416 != nil {
				unwrapped1417 := deconstruct_result1416
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1417)
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
	flat1427 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1427 != nil {
		p.write(*flat1427)
		return nil
	} else {
		_dollar_dollar := msg
		fields1423 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1424 := fields1423
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1425 := unwrapped_fields1424[0].(string)
		p.write(p.formatStringValue(field1425))
		p.newline()
		field1426 := unwrapped_fields1424[1].(*pb.RelationId)
		p.pretty_relation_id(field1426)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1431 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1431 != nil {
		p.write(*flat1431)
		return nil
	} else {
		fields1428 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1428) == 0) {
			p.newline()
			for i1430, elem1429 := range fields1428 {
				if (i1430 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1429)
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
		_t1594 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1594)
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
		p.pretty_date(m)
	case *pb.DateTimeValue:
		p.pretty_datetime(m)
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
	case *pb.IcebergConfig:
		p.pretty_iceberg_config(m)
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
