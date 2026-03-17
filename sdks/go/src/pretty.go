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
	_t1553 := &pb.Value{}
	_t1553.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1553
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1554 := &pb.Value{}
	_t1554.Value = &pb.Value_IntValue{IntValue: v}
	return _t1554
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1555 := &pb.Value{}
	_t1555.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1555
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1556 := &pb.Value{}
	_t1556.Value = &pb.Value_StringValue{StringValue: v}
	return _t1556
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1557 := &pb.Value{}
	_t1557.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1557
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1558 := &pb.Value{}
	_t1558.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1558
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1559 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1559})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1560 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1560})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1561 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1561})
			}
		}
	}
	_t1562 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1562})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1563 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1563})
	_t1564 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1564})
	if msg.GetNewLine() != "" {
		_t1565 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1565})
	}
	_t1566 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1566})
	_t1567 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1567})
	_t1568 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1568})
	if msg.GetComment() != "" {
		_t1569 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1569})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1570 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1570})
	}
	_t1571 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1571})
	_t1572 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1572})
	_t1573 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1573})
	if msg.GetPartitionSizeMb() != 0 {
		_t1574 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1574})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1575 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1575})
	_t1576 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1576})
	_t1577 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1577})
	_t1578 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1578})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1579 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1579})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1580 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1580})
		}
	}
	_t1581 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1581})
	_t1582 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1582})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1583 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1583})
	}
	if msg.Compression != nil {
		_t1584 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1584})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1585 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1585})
	}
	if msg.SyntaxMissingString != nil {
		_t1586 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1586})
	}
	if msg.SyntaxDelim != nil {
		_t1587 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1587})
	}
	if msg.SyntaxQuotechar != nil {
		_t1588 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1588})
	}
	if msg.SyntaxEscapechar != nil {
		_t1589 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1589})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1590 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1590
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
	flat719 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat719 != nil {
		p.write(*flat719)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1420 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1420 = _dollar_dollar.GetConfigure()
		}
		var _t1421 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1421 = _dollar_dollar.GetSync()
		}
		fields710 := []interface{}{_t1420, _t1421, _dollar_dollar.GetEpochs()}
		unwrapped_fields711 := fields710
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field712 := unwrapped_fields711[0].(*pb.Configure)
		if field712 != nil {
			p.newline()
			opt_val713 := field712
			p.pretty_configure(opt_val713)
		}
		field714 := unwrapped_fields711[1].(*pb.Sync)
		if field714 != nil {
			p.newline()
			opt_val715 := field714
			p.pretty_sync(opt_val715)
		}
		field716 := unwrapped_fields711[2].([]*pb.Epoch)
		if !(len(field716) == 0) {
			p.newline()
			for i718, elem717 := range field716 {
				if (i718 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem717)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat722 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		_dollar_dollar := msg
		_t1422 := p.deconstruct_configure(_dollar_dollar)
		fields720 := _t1422
		unwrapped_fields721 := fields720
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields721)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat726 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat726 != nil {
		p.write(*flat726)
		return nil
	} else {
		fields723 := msg
		p.write("{")
		p.indent()
		if !(len(fields723) == 0) {
			p.newline()
			for i725, elem724 := range fields723 {
				if (i725 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem724)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat731 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat731 != nil {
		p.write(*flat731)
		return nil
	} else {
		_dollar_dollar := msg
		fields727 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields728 := fields727
		p.write(":")
		field729 := unwrapped_fields728[0].(string)
		p.write(field729)
		p.write(" ")
		field730 := unwrapped_fields728[1].(*pb.Value)
		p.pretty_raw_value(field730)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat757 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat757 != nil {
		p.write(*flat757)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1423 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1423 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result755 := _t1423
		if deconstruct_result755 != nil {
			unwrapped756 := deconstruct_result755
			p.pretty_raw_date(unwrapped756)
		} else {
			_dollar_dollar := msg
			var _t1424 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1424 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result753 := _t1424
			if deconstruct_result753 != nil {
				unwrapped754 := deconstruct_result753
				p.pretty_raw_datetime(unwrapped754)
			} else {
				_dollar_dollar := msg
				var _t1425 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1425 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result751 := _t1425
				if deconstruct_result751 != nil {
					unwrapped752 := *deconstruct_result751
					p.write(p.formatStringValue(unwrapped752))
				} else {
					_dollar_dollar := msg
					var _t1426 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1426 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result749 := _t1426
					if deconstruct_result749 != nil {
						unwrapped750 := *deconstruct_result749
						p.write(fmt.Sprintf("%di32", unwrapped750))
					} else {
						_dollar_dollar := msg
						var _t1427 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1427 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result747 := _t1427
						if deconstruct_result747 != nil {
							unwrapped748 := *deconstruct_result747
							p.write(fmt.Sprintf("%d", unwrapped748))
						} else {
							_dollar_dollar := msg
							var _t1428 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1428 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result745 := _t1428
							if deconstruct_result745 != nil {
								unwrapped746 := *deconstruct_result745
								p.write(formatFloat32(unwrapped746))
							} else {
								_dollar_dollar := msg
								var _t1429 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1429 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result743 := _t1429
								if deconstruct_result743 != nil {
									unwrapped744 := *deconstruct_result743
									p.write(formatFloat64(unwrapped744))
								} else {
									_dollar_dollar := msg
									var _t1430 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1430 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result741 := _t1430
									if deconstruct_result741 != nil {
										unwrapped742 := *deconstruct_result741
										p.write(fmt.Sprintf("%du32", unwrapped742))
									} else {
										_dollar_dollar := msg
										var _t1431 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1431 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result739 := _t1431
										if deconstruct_result739 != nil {
											unwrapped740 := deconstruct_result739
											p.write(p.formatUint128(unwrapped740))
										} else {
											_dollar_dollar := msg
											var _t1432 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1432 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result737 := _t1432
											if deconstruct_result737 != nil {
												unwrapped738 := deconstruct_result737
												p.write(p.formatInt128(unwrapped738))
											} else {
												_dollar_dollar := msg
												var _t1433 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1433 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result735 := _t1433
												if deconstruct_result735 != nil {
													unwrapped736 := deconstruct_result735
													p.write(p.formatDecimal(unwrapped736))
												} else {
													_dollar_dollar := msg
													var _t1434 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1434 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result733 := _t1434
													if deconstruct_result733 != nil {
														unwrapped734 := *deconstruct_result733
														p.pretty_boolean_value(unwrapped734)
													} else {
														fields732 := msg
														_ = fields732
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
	flat763 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat763 != nil {
		p.write(*flat763)
		return nil
	} else {
		_dollar_dollar := msg
		fields758 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields759 := fields758
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field760 := unwrapped_fields759[0].(int64)
		p.write(fmt.Sprintf("%d", field760))
		p.newline()
		field761 := unwrapped_fields759[1].(int64)
		p.write(fmt.Sprintf("%d", field761))
		p.newline()
		field762 := unwrapped_fields759[2].(int64)
		p.write(fmt.Sprintf("%d", field762))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat774 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat774 != nil {
		p.write(*flat774)
		return nil
	} else {
		_dollar_dollar := msg
		fields764 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields765 := fields764
		p.write("(")
		p.write("datetime")
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
		p.newline()
		field769 := unwrapped_fields765[3].(int64)
		p.write(fmt.Sprintf("%d", field769))
		p.newline()
		field770 := unwrapped_fields765[4].(int64)
		p.write(fmt.Sprintf("%d", field770))
		p.newline()
		field771 := unwrapped_fields765[5].(int64)
		p.write(fmt.Sprintf("%d", field771))
		field772 := unwrapped_fields765[6].(*int64)
		if field772 != nil {
			p.newline()
			opt_val773 := *field772
			p.write(fmt.Sprintf("%d", opt_val773))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1435 []interface{}
	if _dollar_dollar {
		_t1435 = []interface{}{}
	}
	deconstruct_result777 := _t1435
	if deconstruct_result777 != nil {
		unwrapped778 := deconstruct_result777
		_ = unwrapped778
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1436 []interface{}
		if !(_dollar_dollar) {
			_t1436 = []interface{}{}
		}
		deconstruct_result775 := _t1436
		if deconstruct_result775 != nil {
			unwrapped776 := deconstruct_result775
			_ = unwrapped776
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat783 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat783 != nil {
		p.write(*flat783)
		return nil
	} else {
		_dollar_dollar := msg
		fields779 := _dollar_dollar.GetFragments()
		unwrapped_fields780 := fields779
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields780) == 0) {
			p.newline()
			for i782, elem781 := range unwrapped_fields780 {
				if (i782 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem781)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat786 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat786 != nil {
		p.write(*flat786)
		return nil
	} else {
		_dollar_dollar := msg
		fields784 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields785 := fields784
		p.write(":")
		p.write(unwrapped_fields785)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat793 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat793 != nil {
		p.write(*flat793)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1437 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1437 = _dollar_dollar.GetWrites()
		}
		var _t1438 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1438 = _dollar_dollar.GetReads()
		}
		fields787 := []interface{}{_t1437, _t1438}
		unwrapped_fields788 := fields787
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field789 := unwrapped_fields788[0].([]*pb.Write)
		if field789 != nil {
			p.newline()
			opt_val790 := field789
			p.pretty_epoch_writes(opt_val790)
		}
		field791 := unwrapped_fields788[1].([]*pb.Read)
		if field791 != nil {
			p.newline()
			opt_val792 := field791
			p.pretty_epoch_reads(opt_val792)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat797 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat797 != nil {
		p.write(*flat797)
		return nil
	} else {
		fields794 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields794) == 0) {
			p.newline()
			for i796, elem795 := range fields794 {
				if (i796 > 0) {
					p.newline()
				}
				p.pretty_write(elem795)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat806 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat806 != nil {
		p.write(*flat806)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1439 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1439 = _dollar_dollar.GetDefine()
		}
		deconstruct_result804 := _t1439
		if deconstruct_result804 != nil {
			unwrapped805 := deconstruct_result804
			p.pretty_define(unwrapped805)
		} else {
			_dollar_dollar := msg
			var _t1440 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1440 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result802 := _t1440
			if deconstruct_result802 != nil {
				unwrapped803 := deconstruct_result802
				p.pretty_undefine(unwrapped803)
			} else {
				_dollar_dollar := msg
				var _t1441 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1441 = _dollar_dollar.GetContext()
				}
				deconstruct_result800 := _t1441
				if deconstruct_result800 != nil {
					unwrapped801 := deconstruct_result800
					p.pretty_context(unwrapped801)
				} else {
					_dollar_dollar := msg
					var _t1442 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1442 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result798 := _t1442
					if deconstruct_result798 != nil {
						unwrapped799 := deconstruct_result798
						p.pretty_snapshot(unwrapped799)
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
	flat809 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat809 != nil {
		p.write(*flat809)
		return nil
	} else {
		_dollar_dollar := msg
		fields807 := _dollar_dollar.GetFragment()
		unwrapped_fields808 := fields807
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields808)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat816 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat816 != nil {
		p.write(*flat816)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields810 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields811 := fields810
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field812 := unwrapped_fields811[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field812)
		field813 := unwrapped_fields811[1].([]*pb.Declaration)
		if !(len(field813) == 0) {
			p.newline()
			for i815, elem814 := range field813 {
				if (i815 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem814)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat818 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat818 != nil {
		p.write(*flat818)
		return nil
	} else {
		fields817 := msg
		p.pretty_fragment_id(fields817)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat827 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat827 != nil {
		p.write(*flat827)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1443 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1443 = _dollar_dollar.GetDef()
		}
		deconstruct_result825 := _t1443
		if deconstruct_result825 != nil {
			unwrapped826 := deconstruct_result825
			p.pretty_def(unwrapped826)
		} else {
			_dollar_dollar := msg
			var _t1444 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1444 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result823 := _t1444
			if deconstruct_result823 != nil {
				unwrapped824 := deconstruct_result823
				p.pretty_algorithm(unwrapped824)
			} else {
				_dollar_dollar := msg
				var _t1445 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1445 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result821 := _t1445
				if deconstruct_result821 != nil {
					unwrapped822 := deconstruct_result821
					p.pretty_constraint(unwrapped822)
				} else {
					_dollar_dollar := msg
					var _t1446 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1446 = _dollar_dollar.GetData()
					}
					deconstruct_result819 := _t1446
					if deconstruct_result819 != nil {
						unwrapped820 := deconstruct_result819
						p.pretty_data(unwrapped820)
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
	flat834 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat834 != nil {
		p.write(*flat834)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1447 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1447 = _dollar_dollar.GetAttrs()
		}
		fields828 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1447}
		unwrapped_fields829 := fields828
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field830 := unwrapped_fields829[0].(*pb.RelationId)
		p.pretty_relation_id(field830)
		p.newline()
		field831 := unwrapped_fields829[1].(*pb.Abstraction)
		p.pretty_abstraction(field831)
		field832 := unwrapped_fields829[2].([]*pb.Attribute)
		if field832 != nil {
			p.newline()
			opt_val833 := field832
			p.pretty_attrs(opt_val833)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat839 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat839 != nil {
		p.write(*flat839)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1448 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1449 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1448 = ptr(_t1449)
		}
		deconstruct_result837 := _t1448
		if deconstruct_result837 != nil {
			unwrapped838 := *deconstruct_result837
			p.write(":")
			p.write(unwrapped838)
		} else {
			_dollar_dollar := msg
			_t1450 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result835 := _t1450
			if deconstruct_result835 != nil {
				unwrapped836 := deconstruct_result835
				p.write(p.formatUint128(unwrapped836))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat844 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat844 != nil {
		p.write(*flat844)
		return nil
	} else {
		_dollar_dollar := msg
		_t1451 := p.deconstruct_bindings(_dollar_dollar)
		fields840 := []interface{}{_t1451, _dollar_dollar.GetValue()}
		unwrapped_fields841 := fields840
		p.write("(")
		p.indent()
		field842 := unwrapped_fields841[0].([]interface{})
		p.pretty_bindings(field842)
		p.newline()
		field843 := unwrapped_fields841[1].(*pb.Formula)
		p.pretty_formula(field843)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat852 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat852 != nil {
		p.write(*flat852)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1452 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1452 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields845 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1452}
		unwrapped_fields846 := fields845
		p.write("[")
		p.indent()
		field847 := unwrapped_fields846[0].([]*pb.Binding)
		for i849, elem848 := range field847 {
			if (i849 > 0) {
				p.newline()
			}
			p.pretty_binding(elem848)
		}
		field850 := unwrapped_fields846[1].([]*pb.Binding)
		if field850 != nil {
			p.newline()
			opt_val851 := field850
			p.pretty_value_bindings(opt_val851)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat857 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat857 != nil {
		p.write(*flat857)
		return nil
	} else {
		_dollar_dollar := msg
		fields853 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields854 := fields853
		field855 := unwrapped_fields854[0].(string)
		p.write(field855)
		p.write("::")
		field856 := unwrapped_fields854[1].(*pb.Type)
		p.pretty_type(field856)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat886 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat886 != nil {
		p.write(*flat886)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1453 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1453 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result884 := _t1453
		if deconstruct_result884 != nil {
			unwrapped885 := deconstruct_result884
			p.pretty_unspecified_type(unwrapped885)
		} else {
			_dollar_dollar := msg
			var _t1454 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1454 = _dollar_dollar.GetStringType()
			}
			deconstruct_result882 := _t1454
			if deconstruct_result882 != nil {
				unwrapped883 := deconstruct_result882
				p.pretty_string_type(unwrapped883)
			} else {
				_dollar_dollar := msg
				var _t1455 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1455 = _dollar_dollar.GetIntType()
				}
				deconstruct_result880 := _t1455
				if deconstruct_result880 != nil {
					unwrapped881 := deconstruct_result880
					p.pretty_int_type(unwrapped881)
				} else {
					_dollar_dollar := msg
					var _t1456 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1456 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result878 := _t1456
					if deconstruct_result878 != nil {
						unwrapped879 := deconstruct_result878
						p.pretty_float_type(unwrapped879)
					} else {
						_dollar_dollar := msg
						var _t1457 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1457 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result876 := _t1457
						if deconstruct_result876 != nil {
							unwrapped877 := deconstruct_result876
							p.pretty_uint128_type(unwrapped877)
						} else {
							_dollar_dollar := msg
							var _t1458 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1458 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result874 := _t1458
							if deconstruct_result874 != nil {
								unwrapped875 := deconstruct_result874
								p.pretty_int128_type(unwrapped875)
							} else {
								_dollar_dollar := msg
								var _t1459 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1459 = _dollar_dollar.GetDateType()
								}
								deconstruct_result872 := _t1459
								if deconstruct_result872 != nil {
									unwrapped873 := deconstruct_result872
									p.pretty_date_type(unwrapped873)
								} else {
									_dollar_dollar := msg
									var _t1460 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1460 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result870 := _t1460
									if deconstruct_result870 != nil {
										unwrapped871 := deconstruct_result870
										p.pretty_datetime_type(unwrapped871)
									} else {
										_dollar_dollar := msg
										var _t1461 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1461 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result868 := _t1461
										if deconstruct_result868 != nil {
											unwrapped869 := deconstruct_result868
											p.pretty_missing_type(unwrapped869)
										} else {
											_dollar_dollar := msg
											var _t1462 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1462 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result866 := _t1462
											if deconstruct_result866 != nil {
												unwrapped867 := deconstruct_result866
												p.pretty_decimal_type(unwrapped867)
											} else {
												_dollar_dollar := msg
												var _t1463 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1463 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result864 := _t1463
												if deconstruct_result864 != nil {
													unwrapped865 := deconstruct_result864
													p.pretty_boolean_type(unwrapped865)
												} else {
													_dollar_dollar := msg
													var _t1464 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1464 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result862 := _t1464
													if deconstruct_result862 != nil {
														unwrapped863 := deconstruct_result862
														p.pretty_int32_type(unwrapped863)
													} else {
														_dollar_dollar := msg
														var _t1465 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1465 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result860 := _t1465
														if deconstruct_result860 != nil {
															unwrapped861 := deconstruct_result860
															p.pretty_float32_type(unwrapped861)
														} else {
															_dollar_dollar := msg
															var _t1466 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1466 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result858 := _t1466
															if deconstruct_result858 != nil {
																unwrapped859 := deconstruct_result858
																p.pretty_uint32_type(unwrapped859)
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
	fields887 := msg
	_ = fields887
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields888 := msg
	_ = fields888
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields889 := msg
	_ = fields889
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields890 := msg
	_ = fields890
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields891 := msg
	_ = fields891
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields892 := msg
	_ = fields892
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields893 := msg
	_ = fields893
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields894 := msg
	_ = fields894
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields895 := msg
	_ = fields895
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat900 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat900 != nil {
		p.write(*flat900)
		return nil
	} else {
		_dollar_dollar := msg
		fields896 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields897 := fields896
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field898 := unwrapped_fields897[0].(int64)
		p.write(fmt.Sprintf("%d", field898))
		p.newline()
		field899 := unwrapped_fields897[1].(int64)
		p.write(fmt.Sprintf("%d", field899))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields901 := msg
	_ = fields901
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields902 := msg
	_ = fields902
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields903 := msg
	_ = fields903
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields904 := msg
	_ = fields904
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat908 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat908 != nil {
		p.write(*flat908)
		return nil
	} else {
		fields905 := msg
		p.write("|")
		if !(len(fields905) == 0) {
			p.write(" ")
			for i907, elem906 := range fields905 {
				if (i907 > 0) {
					p.newline()
				}
				p.pretty_binding(elem906)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat935 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat935 != nil {
		p.write(*flat935)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1467 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1467 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result933 := _t1467
		if deconstruct_result933 != nil {
			unwrapped934 := deconstruct_result933
			p.pretty_true(unwrapped934)
		} else {
			_dollar_dollar := msg
			var _t1468 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1468 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result931 := _t1468
			if deconstruct_result931 != nil {
				unwrapped932 := deconstruct_result931
				p.pretty_false(unwrapped932)
			} else {
				_dollar_dollar := msg
				var _t1469 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1469 = _dollar_dollar.GetExists()
				}
				deconstruct_result929 := _t1469
				if deconstruct_result929 != nil {
					unwrapped930 := deconstruct_result929
					p.pretty_exists(unwrapped930)
				} else {
					_dollar_dollar := msg
					var _t1470 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1470 = _dollar_dollar.GetReduce()
					}
					deconstruct_result927 := _t1470
					if deconstruct_result927 != nil {
						unwrapped928 := deconstruct_result927
						p.pretty_reduce(unwrapped928)
					} else {
						_dollar_dollar := msg
						var _t1471 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1471 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result925 := _t1471
						if deconstruct_result925 != nil {
							unwrapped926 := deconstruct_result925
							p.pretty_conjunction(unwrapped926)
						} else {
							_dollar_dollar := msg
							var _t1472 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1472 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result923 := _t1472
							if deconstruct_result923 != nil {
								unwrapped924 := deconstruct_result923
								p.pretty_disjunction(unwrapped924)
							} else {
								_dollar_dollar := msg
								var _t1473 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1473 = _dollar_dollar.GetNot()
								}
								deconstruct_result921 := _t1473
								if deconstruct_result921 != nil {
									unwrapped922 := deconstruct_result921
									p.pretty_not(unwrapped922)
								} else {
									_dollar_dollar := msg
									var _t1474 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1474 = _dollar_dollar.GetFfi()
									}
									deconstruct_result919 := _t1474
									if deconstruct_result919 != nil {
										unwrapped920 := deconstruct_result919
										p.pretty_ffi(unwrapped920)
									} else {
										_dollar_dollar := msg
										var _t1475 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1475 = _dollar_dollar.GetAtom()
										}
										deconstruct_result917 := _t1475
										if deconstruct_result917 != nil {
											unwrapped918 := deconstruct_result917
											p.pretty_atom(unwrapped918)
										} else {
											_dollar_dollar := msg
											var _t1476 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1476 = _dollar_dollar.GetPragma()
											}
											deconstruct_result915 := _t1476
											if deconstruct_result915 != nil {
												unwrapped916 := deconstruct_result915
												p.pretty_pragma(unwrapped916)
											} else {
												_dollar_dollar := msg
												var _t1477 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1477 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result913 := _t1477
												if deconstruct_result913 != nil {
													unwrapped914 := deconstruct_result913
													p.pretty_primitive(unwrapped914)
												} else {
													_dollar_dollar := msg
													var _t1478 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1478 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result911 := _t1478
													if deconstruct_result911 != nil {
														unwrapped912 := deconstruct_result911
														p.pretty_rel_atom(unwrapped912)
													} else {
														_dollar_dollar := msg
														var _t1479 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1479 = _dollar_dollar.GetCast()
														}
														deconstruct_result909 := _t1479
														if deconstruct_result909 != nil {
															unwrapped910 := deconstruct_result909
															p.pretty_cast(unwrapped910)
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
	fields936 := msg
	_ = fields936
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields937 := msg
	_ = fields937
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat942 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat942 != nil {
		p.write(*flat942)
		return nil
	} else {
		_dollar_dollar := msg
		_t1480 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields938 := []interface{}{_t1480, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields939 := fields938
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field940 := unwrapped_fields939[0].([]interface{})
		p.pretty_bindings(field940)
		p.newline()
		field941 := unwrapped_fields939[1].(*pb.Formula)
		p.pretty_formula(field941)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat948 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat948 != nil {
		p.write(*flat948)
		return nil
	} else {
		_dollar_dollar := msg
		fields943 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields944 := fields943
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field945 := unwrapped_fields944[0].(*pb.Abstraction)
		p.pretty_abstraction(field945)
		p.newline()
		field946 := unwrapped_fields944[1].(*pb.Abstraction)
		p.pretty_abstraction(field946)
		p.newline()
		field947 := unwrapped_fields944[2].([]*pb.Term)
		p.pretty_terms(field947)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat952 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat952 != nil {
		p.write(*flat952)
		return nil
	} else {
		fields949 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields949) == 0) {
			p.newline()
			for i951, elem950 := range fields949 {
				if (i951 > 0) {
					p.newline()
				}
				p.pretty_term(elem950)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat957 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat957 != nil {
		p.write(*flat957)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1481 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1481 = _dollar_dollar.GetVar()
		}
		deconstruct_result955 := _t1481
		if deconstruct_result955 != nil {
			unwrapped956 := deconstruct_result955
			p.pretty_var(unwrapped956)
		} else {
			_dollar_dollar := msg
			var _t1482 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1482 = _dollar_dollar.GetConstant()
			}
			deconstruct_result953 := _t1482
			if deconstruct_result953 != nil {
				unwrapped954 := deconstruct_result953
				p.pretty_value(unwrapped954)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat960 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat960 != nil {
		p.write(*flat960)
		return nil
	} else {
		_dollar_dollar := msg
		fields958 := _dollar_dollar.GetName()
		unwrapped_fields959 := fields958
		p.write(unwrapped_fields959)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat986 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat986 != nil {
		p.write(*flat986)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1483 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1483 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result984 := _t1483
		if deconstruct_result984 != nil {
			unwrapped985 := deconstruct_result984
			p.pretty_date(unwrapped985)
		} else {
			_dollar_dollar := msg
			var _t1484 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1484 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result982 := _t1484
			if deconstruct_result982 != nil {
				unwrapped983 := deconstruct_result982
				p.pretty_datetime(unwrapped983)
			} else {
				_dollar_dollar := msg
				var _t1485 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1485 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result980 := _t1485
				if deconstruct_result980 != nil {
					unwrapped981 := *deconstruct_result980
					p.write(p.formatStringValue(unwrapped981))
				} else {
					_dollar_dollar := msg
					var _t1486 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1486 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result978 := _t1486
					if deconstruct_result978 != nil {
						unwrapped979 := *deconstruct_result978
						p.write(fmt.Sprintf("%di32", unwrapped979))
					} else {
						_dollar_dollar := msg
						var _t1487 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1487 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result976 := _t1487
						if deconstruct_result976 != nil {
							unwrapped977 := *deconstruct_result976
							p.write(fmt.Sprintf("%d", unwrapped977))
						} else {
							_dollar_dollar := msg
							var _t1488 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1488 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result974 := _t1488
							if deconstruct_result974 != nil {
								unwrapped975 := *deconstruct_result974
								p.write(formatFloat32(unwrapped975))
							} else {
								_dollar_dollar := msg
								var _t1489 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1489 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result972 := _t1489
								if deconstruct_result972 != nil {
									unwrapped973 := *deconstruct_result972
									p.write(formatFloat64(unwrapped973))
								} else {
									_dollar_dollar := msg
									var _t1490 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1490 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result970 := _t1490
									if deconstruct_result970 != nil {
										unwrapped971 := *deconstruct_result970
										p.write(fmt.Sprintf("%du32", unwrapped971))
									} else {
										_dollar_dollar := msg
										var _t1491 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1491 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result968 := _t1491
										if deconstruct_result968 != nil {
											unwrapped969 := deconstruct_result968
											p.write(p.formatUint128(unwrapped969))
										} else {
											_dollar_dollar := msg
											var _t1492 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1492 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result966 := _t1492
											if deconstruct_result966 != nil {
												unwrapped967 := deconstruct_result966
												p.write(p.formatInt128(unwrapped967))
											} else {
												_dollar_dollar := msg
												var _t1493 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1493 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result964 := _t1493
												if deconstruct_result964 != nil {
													unwrapped965 := deconstruct_result964
													p.write(p.formatDecimal(unwrapped965))
												} else {
													_dollar_dollar := msg
													var _t1494 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1494 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result962 := _t1494
													if deconstruct_result962 != nil {
														unwrapped963 := *deconstruct_result962
														p.pretty_boolean_value(unwrapped963)
													} else {
														fields961 := msg
														_ = fields961
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
	flat992 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat992 != nil {
		p.write(*flat992)
		return nil
	} else {
		_dollar_dollar := msg
		fields987 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields988 := fields987
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field989 := unwrapped_fields988[0].(int64)
		p.write(fmt.Sprintf("%d", field989))
		p.newline()
		field990 := unwrapped_fields988[1].(int64)
		p.write(fmt.Sprintf("%d", field990))
		p.newline()
		field991 := unwrapped_fields988[2].(int64)
		p.write(fmt.Sprintf("%d", field991))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1003 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1003 != nil {
		p.write(*flat1003)
		return nil
	} else {
		_dollar_dollar := msg
		fields993 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields994 := fields993
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field995 := unwrapped_fields994[0].(int64)
		p.write(fmt.Sprintf("%d", field995))
		p.newline()
		field996 := unwrapped_fields994[1].(int64)
		p.write(fmt.Sprintf("%d", field996))
		p.newline()
		field997 := unwrapped_fields994[2].(int64)
		p.write(fmt.Sprintf("%d", field997))
		p.newline()
		field998 := unwrapped_fields994[3].(int64)
		p.write(fmt.Sprintf("%d", field998))
		p.newline()
		field999 := unwrapped_fields994[4].(int64)
		p.write(fmt.Sprintf("%d", field999))
		p.newline()
		field1000 := unwrapped_fields994[5].(int64)
		p.write(fmt.Sprintf("%d", field1000))
		field1001 := unwrapped_fields994[6].(*int64)
		if field1001 != nil {
			p.newline()
			opt_val1002 := *field1001
			p.write(fmt.Sprintf("%d", opt_val1002))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1008 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1008 != nil {
		p.write(*flat1008)
		return nil
	} else {
		_dollar_dollar := msg
		fields1004 := _dollar_dollar.GetArgs()
		unwrapped_fields1005 := fields1004
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1005) == 0) {
			p.newline()
			for i1007, elem1006 := range unwrapped_fields1005 {
				if (i1007 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1006)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1013 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		_dollar_dollar := msg
		fields1009 := _dollar_dollar.GetArgs()
		unwrapped_fields1010 := fields1009
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1010) == 0) {
			p.newline()
			for i1012, elem1011 := range unwrapped_fields1010 {
				if (i1012 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1011)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1016 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1016 != nil {
		p.write(*flat1016)
		return nil
	} else {
		_dollar_dollar := msg
		fields1014 := _dollar_dollar.GetArg()
		unwrapped_fields1015 := fields1014
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1015)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1022 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1022 != nil {
		p.write(*flat1022)
		return nil
	} else {
		_dollar_dollar := msg
		fields1017 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1018 := fields1017
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1019 := unwrapped_fields1018[0].(string)
		p.pretty_name(field1019)
		p.newline()
		field1020 := unwrapped_fields1018[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1020)
		p.newline()
		field1021 := unwrapped_fields1018[2].([]*pb.Term)
		p.pretty_terms(field1021)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1024 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1024 != nil {
		p.write(*flat1024)
		return nil
	} else {
		fields1023 := msg
		p.write(":")
		p.write(fields1023)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1028 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		fields1025 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1025) == 0) {
			p.newline()
			for i1027, elem1026 := range fields1025 {
				if (i1027 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1026)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1035 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1035 != nil {
		p.write(*flat1035)
		return nil
	} else {
		_dollar_dollar := msg
		fields1029 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1030 := fields1029
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1031 := unwrapped_fields1030[0].(*pb.RelationId)
		p.pretty_relation_id(field1031)
		field1032 := unwrapped_fields1030[1].([]*pb.Term)
		if !(len(field1032) == 0) {
			p.newline()
			for i1034, elem1033 := range field1032 {
				if (i1034 > 0) {
					p.newline()
				}
				p.pretty_term(elem1033)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		_dollar_dollar := msg
		fields1036 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1037 := fields1036
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1038 := unwrapped_fields1037[0].(string)
		p.pretty_name(field1038)
		field1039 := unwrapped_fields1037[1].([]*pb.Term)
		if !(len(field1039) == 0) {
			p.newline()
			for i1041, elem1040 := range field1039 {
				if (i1041 > 0) {
					p.newline()
				}
				p.pretty_term(elem1040)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1058 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1058 != nil {
		p.write(*flat1058)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1495 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1495 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1057 := _t1495
		if guard_result1057 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1496 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1496 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1056 := _t1496
			if guard_result1056 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1497 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1497 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1055 := _t1497
				if guard_result1055 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1498 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1498 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1054 := _t1498
					if guard_result1054 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1499 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1499 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1053 := _t1499
						if guard_result1053 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1500 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1500 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1052 := _t1500
							if guard_result1052 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1501 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1501 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1051 := _t1501
								if guard_result1051 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1502 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1502 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1050 := _t1502
									if guard_result1050 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1503 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1503 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1049 := _t1503
										if guard_result1049 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1043 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1044 := fields1043
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1045 := unwrapped_fields1044[0].(string)
											p.pretty_name(field1045)
											field1046 := unwrapped_fields1044[1].([]*pb.RelTerm)
											if !(len(field1046) == 0) {
												p.newline()
												for i1048, elem1047 := range field1046 {
													if (i1048 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1047)
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
	flat1063 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1063 != nil {
		p.write(*flat1063)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1504 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1504 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1059 := _t1504
		unwrapped_fields1060 := fields1059
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1061 := unwrapped_fields1060[0].(*pb.Term)
		p.pretty_term(field1061)
		p.newline()
		field1062 := unwrapped_fields1060[1].(*pb.Term)
		p.pretty_term(field1062)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1068 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1068 != nil {
		p.write(*flat1068)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1505 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1505 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1064 := _t1505
		unwrapped_fields1065 := fields1064
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1066 := unwrapped_fields1065[0].(*pb.Term)
		p.pretty_term(field1066)
		p.newline()
		field1067 := unwrapped_fields1065[1].(*pb.Term)
		p.pretty_term(field1067)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1073 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1073 != nil {
		p.write(*flat1073)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1506 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1506 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1069 := _t1506
		unwrapped_fields1070 := fields1069
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1071 := unwrapped_fields1070[0].(*pb.Term)
		p.pretty_term(field1071)
		p.newline()
		field1072 := unwrapped_fields1070[1].(*pb.Term)
		p.pretty_term(field1072)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1078 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1078 != nil {
		p.write(*flat1078)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1507 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1507 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1074 := _t1507
		unwrapped_fields1075 := fields1074
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1076 := unwrapped_fields1075[0].(*pb.Term)
		p.pretty_term(field1076)
		p.newline()
		field1077 := unwrapped_fields1075[1].(*pb.Term)
		p.pretty_term(field1077)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1083 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1508 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1508 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1079 := _t1508
		unwrapped_fields1080 := fields1079
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1509 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1509 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1084 := _t1509
		unwrapped_fields1085 := fields1084
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1086 := unwrapped_fields1085[0].(*pb.Term)
		p.pretty_term(field1086)
		p.newline()
		field1087 := unwrapped_fields1085[1].(*pb.Term)
		p.pretty_term(field1087)
		p.newline()
		field1088 := unwrapped_fields1085[2].(*pb.Term)
		p.pretty_term(field1088)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1095 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1095 != nil {
		p.write(*flat1095)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1510 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1510 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1090 := _t1510
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1092 := unwrapped_fields1091[0].(*pb.Term)
		p.pretty_term(field1092)
		p.newline()
		field1093 := unwrapped_fields1091[1].(*pb.Term)
		p.pretty_term(field1093)
		p.newline()
		field1094 := unwrapped_fields1091[2].(*pb.Term)
		p.pretty_term(field1094)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1101 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1101 != nil {
		p.write(*flat1101)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1511 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1511 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1096 := _t1511
		unwrapped_fields1097 := fields1096
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1098 := unwrapped_fields1097[0].(*pb.Term)
		p.pretty_term(field1098)
		p.newline()
		field1099 := unwrapped_fields1097[1].(*pb.Term)
		p.pretty_term(field1099)
		p.newline()
		field1100 := unwrapped_fields1097[2].(*pb.Term)
		p.pretty_term(field1100)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1512 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1512 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1102 := _t1512
		unwrapped_fields1103 := fields1102
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1104 := unwrapped_fields1103[0].(*pb.Term)
		p.pretty_term(field1104)
		p.newline()
		field1105 := unwrapped_fields1103[1].(*pb.Term)
		p.pretty_term(field1105)
		p.newline()
		field1106 := unwrapped_fields1103[2].(*pb.Term)
		p.pretty_term(field1106)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1513 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1513 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1110 := _t1513
		if deconstruct_result1110 != nil {
			unwrapped1111 := deconstruct_result1110
			p.pretty_specialized_value(unwrapped1111)
		} else {
			_dollar_dollar := msg
			var _t1514 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1514 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1108 := _t1514
			if deconstruct_result1108 != nil {
				unwrapped1109 := deconstruct_result1108
				p.pretty_term(unwrapped1109)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		fields1113 := msg
		p.write("#")
		p.pretty_raw_value(fields1113)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		_dollar_dollar := msg
		fields1115 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1116 := fields1115
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1117 := unwrapped_fields1116[0].(string)
		p.pretty_name(field1117)
		field1118 := unwrapped_fields1116[1].([]*pb.RelTerm)
		if !(len(field1118) == 0) {
			p.newline()
			for i1120, elem1119 := range field1118 {
				if (i1120 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1119)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1126 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1126 != nil {
		p.write(*flat1126)
		return nil
	} else {
		_dollar_dollar := msg
		fields1122 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1123 := fields1122
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1124 := unwrapped_fields1123[0].(*pb.Term)
		p.pretty_term(field1124)
		p.newline()
		field1125 := unwrapped_fields1123[1].(*pb.Term)
		p.pretty_term(field1125)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		fields1127 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1127) == 0) {
			p.newline()
			for i1129, elem1128 := range fields1127 {
				if (i1129 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1128)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1137 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1137 != nil {
		p.write(*flat1137)
		return nil
	} else {
		_dollar_dollar := msg
		fields1131 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1133 := unwrapped_fields1132[0].(string)
		p.pretty_name(field1133)
		field1134 := unwrapped_fields1132[1].([]*pb.Value)
		if !(len(field1134) == 0) {
			p.newline()
			for i1136, elem1135 := range field1134 {
				if (i1136 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1135)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1144 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1144 != nil {
		p.write(*flat1144)
		return nil
	} else {
		_dollar_dollar := msg
		fields1138 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1139 := fields1138
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1140 := unwrapped_fields1139[0].([]*pb.RelationId)
		if !(len(field1140) == 0) {
			p.newline()
			for i1142, elem1141 := range field1140 {
				if (i1142 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1141)
			}
		}
		p.newline()
		field1143 := unwrapped_fields1139[1].(*pb.Script)
		p.pretty_script(field1143)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1149 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1149 != nil {
		p.write(*flat1149)
		return nil
	} else {
		_dollar_dollar := msg
		fields1145 := _dollar_dollar.GetConstructs()
		unwrapped_fields1146 := fields1145
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1146) == 0) {
			p.newline()
			for i1148, elem1147 := range unwrapped_fields1146 {
				if (i1148 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1147)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1154 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1154 != nil {
		p.write(*flat1154)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1515 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1515 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1152 := _t1515
		if deconstruct_result1152 != nil {
			unwrapped1153 := deconstruct_result1152
			p.pretty_loop(unwrapped1153)
		} else {
			_dollar_dollar := msg
			var _t1516 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1516 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1150 := _t1516
			if deconstruct_result1150 != nil {
				unwrapped1151 := deconstruct_result1150
				p.pretty_instruction(unwrapped1151)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1159 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1159 != nil {
		p.write(*flat1159)
		return nil
	} else {
		_dollar_dollar := msg
		fields1155 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1156 := fields1155
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1157 := unwrapped_fields1156[0].([]*pb.Instruction)
		p.pretty_init(field1157)
		p.newline()
		field1158 := unwrapped_fields1156[1].(*pb.Script)
		p.pretty_script(field1158)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1163 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1163 != nil {
		p.write(*flat1163)
		return nil
	} else {
		fields1160 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1160) == 0) {
			p.newline()
			for i1162, elem1161 := range fields1160 {
				if (i1162 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1161)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1517 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1517 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1172 := _t1517
		if deconstruct_result1172 != nil {
			unwrapped1173 := deconstruct_result1172
			p.pretty_assign(unwrapped1173)
		} else {
			_dollar_dollar := msg
			var _t1518 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1518 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1170 := _t1518
			if deconstruct_result1170 != nil {
				unwrapped1171 := deconstruct_result1170
				p.pretty_upsert(unwrapped1171)
			} else {
				_dollar_dollar := msg
				var _t1519 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1519 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1168 := _t1519
				if deconstruct_result1168 != nil {
					unwrapped1169 := deconstruct_result1168
					p.pretty_break(unwrapped1169)
				} else {
					_dollar_dollar := msg
					var _t1520 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1520 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1166 := _t1520
					if deconstruct_result1166 != nil {
						unwrapped1167 := deconstruct_result1166
						p.pretty_monoid_def(unwrapped1167)
					} else {
						_dollar_dollar := msg
						var _t1521 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1521 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1164 := _t1521
						if deconstruct_result1164 != nil {
							unwrapped1165 := deconstruct_result1164
							p.pretty_monus_def(unwrapped1165)
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
	flat1181 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1522 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1522 = _dollar_dollar.GetAttrs()
		}
		fields1175 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1522}
		unwrapped_fields1176 := fields1175
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1177 := unwrapped_fields1176[0].(*pb.RelationId)
		p.pretty_relation_id(field1177)
		p.newline()
		field1178 := unwrapped_fields1176[1].(*pb.Abstraction)
		p.pretty_abstraction(field1178)
		field1179 := unwrapped_fields1176[2].([]*pb.Attribute)
		if field1179 != nil {
			p.newline()
			opt_val1180 := field1179
			p.pretty_attrs(opt_val1180)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1188 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1188 != nil {
		p.write(*flat1188)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1523 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1523 = _dollar_dollar.GetAttrs()
		}
		fields1182 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1523}
		unwrapped_fields1183 := fields1182
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1184 := unwrapped_fields1183[0].(*pb.RelationId)
		p.pretty_relation_id(field1184)
		p.newline()
		field1185 := unwrapped_fields1183[1].([]interface{})
		p.pretty_abstraction_with_arity(field1185)
		field1186 := unwrapped_fields1183[2].([]*pb.Attribute)
		if field1186 != nil {
			p.newline()
			opt_val1187 := field1186
			p.pretty_attrs(opt_val1187)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1193 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1193 != nil {
		p.write(*flat1193)
		return nil
	} else {
		_dollar_dollar := msg
		_t1524 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1189 := []interface{}{_t1524, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1190 := fields1189
		p.write("(")
		p.indent()
		field1191 := unwrapped_fields1190[0].([]interface{})
		p.pretty_bindings(field1191)
		p.newline()
		field1192 := unwrapped_fields1190[1].(*pb.Formula)
		p.pretty_formula(field1192)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1525 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1525 = _dollar_dollar.GetAttrs()
		}
		fields1194 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1525}
		unwrapped_fields1195 := fields1194
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1196 := unwrapped_fields1195[0].(*pb.RelationId)
		p.pretty_relation_id(field1196)
		p.newline()
		field1197 := unwrapped_fields1195[1].(*pb.Abstraction)
		p.pretty_abstraction(field1197)
		field1198 := unwrapped_fields1195[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1526 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1526 = _dollar_dollar.GetAttrs()
		}
		fields1201 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1526}
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(*pb.Monoid)
		p.pretty_monoid(field1203)
		p.newline()
		field1204 := unwrapped_fields1202[1].(*pb.RelationId)
		p.pretty_relation_id(field1204)
		p.newline()
		field1205 := unwrapped_fields1202[2].([]interface{})
		p.pretty_abstraction_with_arity(field1205)
		field1206 := unwrapped_fields1202[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1217 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1217 != nil {
		p.write(*flat1217)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1527 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1527 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1215 := _t1527
		if deconstruct_result1215 != nil {
			unwrapped1216 := deconstruct_result1215
			p.pretty_or_monoid(unwrapped1216)
		} else {
			_dollar_dollar := msg
			var _t1528 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1528 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1213 := _t1528
			if deconstruct_result1213 != nil {
				unwrapped1214 := deconstruct_result1213
				p.pretty_min_monoid(unwrapped1214)
			} else {
				_dollar_dollar := msg
				var _t1529 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1529 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1211 := _t1529
				if deconstruct_result1211 != nil {
					unwrapped1212 := deconstruct_result1211
					p.pretty_max_monoid(unwrapped1212)
				} else {
					_dollar_dollar := msg
					var _t1530 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1530 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1209 := _t1530
					if deconstruct_result1209 != nil {
						unwrapped1210 := deconstruct_result1209
						p.pretty_sum_monoid(unwrapped1210)
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
	fields1218 := msg
	_ = fields1218
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		fields1219 := _dollar_dollar.GetType()
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1220)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		_dollar_dollar := msg
		fields1222 := _dollar_dollar.GetType()
		unwrapped_fields1223 := fields1222
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1223)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		fields1225 := _dollar_dollar.GetType()
		unwrapped_fields1226 := fields1225
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1226)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1531 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1531 = _dollar_dollar.GetAttrs()
		}
		fields1228 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1531}
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1230 := unwrapped_fields1229[0].(*pb.Monoid)
		p.pretty_monoid(field1230)
		p.newline()
		field1231 := unwrapped_fields1229[1].(*pb.RelationId)
		p.pretty_relation_id(field1231)
		p.newline()
		field1232 := unwrapped_fields1229[2].([]interface{})
		p.pretty_abstraction_with_arity(field1232)
		field1233 := unwrapped_fields1229[3].([]*pb.Attribute)
		if field1233 != nil {
			p.newline()
			opt_val1234 := field1233
			p.pretty_attrs(opt_val1234)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1242 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1242 != nil {
		p.write(*flat1242)
		return nil
	} else {
		_dollar_dollar := msg
		fields1236 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1238 := unwrapped_fields1237[0].(*pb.RelationId)
		p.pretty_relation_id(field1238)
		p.newline()
		field1239 := unwrapped_fields1237[1].(*pb.Abstraction)
		p.pretty_abstraction(field1239)
		p.newline()
		field1240 := unwrapped_fields1237[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1240)
		p.newline()
		field1241 := unwrapped_fields1237[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1241)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		fields1243 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1243) == 0) {
			p.newline()
			for i1245, elem1244 := range fields1243 {
				if (i1245 > 0) {
					p.newline()
				}
				p.pretty_var(elem1244)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1250 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1250 != nil {
		p.write(*flat1250)
		return nil
	} else {
		fields1247 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1247) == 0) {
			p.newline()
			for i1249, elem1248 := range fields1247 {
				if (i1249 > 0) {
					p.newline()
				}
				p.pretty_var(elem1248)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1532 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1532 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1255 := _t1532
		if deconstruct_result1255 != nil {
			unwrapped1256 := deconstruct_result1255
			p.pretty_edb(unwrapped1256)
		} else {
			_dollar_dollar := msg
			var _t1533 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1533 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1253 := _t1533
			if deconstruct_result1253 != nil {
				unwrapped1254 := deconstruct_result1253
				p.pretty_betree_relation(unwrapped1254)
			} else {
				_dollar_dollar := msg
				var _t1534 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1534 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1251 := _t1534
				if deconstruct_result1251 != nil {
					unwrapped1252 := deconstruct_result1251
					p.pretty_csv_data(unwrapped1252)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_dollar_dollar := msg
		fields1258 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1260 := unwrapped_fields1259[0].(*pb.RelationId)
		p.pretty_relation_id(field1260)
		p.newline()
		field1261 := unwrapped_fields1259[1].([]string)
		p.pretty_edb_path(field1261)
		p.newline()
		field1262 := unwrapped_fields1259[2].([]*pb.Type)
		p.pretty_edb_types(field1262)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1267 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1267 != nil {
		p.write(*flat1267)
		return nil
	} else {
		fields1264 := msg
		p.write("[")
		p.indent()
		for i1266, elem1265 := range fields1264 {
			if (i1266 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1265))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1271 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1271 != nil {
		p.write(*flat1271)
		return nil
	} else {
		fields1268 := msg
		p.write("[")
		p.indent()
		for i1270, elem1269 := range fields1268 {
			if (i1270 > 0) {
				p.newline()
			}
			p.pretty_type(elem1269)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1276 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1276 != nil {
		p.write(*flat1276)
		return nil
	} else {
		_dollar_dollar := msg
		fields1272 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1273 := fields1272
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1274 := unwrapped_fields1273[0].(*pb.RelationId)
		p.pretty_relation_id(field1274)
		p.newline()
		field1275 := unwrapped_fields1273[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1275)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1282 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1282 != nil {
		p.write(*flat1282)
		return nil
	} else {
		_dollar_dollar := msg
		_t1535 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1277 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1535}
		unwrapped_fields1278 := fields1277
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1279 := unwrapped_fields1278[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1279)
		p.newline()
		field1280 := unwrapped_fields1278[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1280)
		p.newline()
		field1281 := unwrapped_fields1278[2].([][]interface{})
		p.pretty_config_dict(field1281)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		fields1283 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1283) == 0) {
			p.newline()
			for i1285, elem1284 := range fields1283 {
				if (i1285 > 0) {
					p.newline()
				}
				p.pretty_type(elem1284)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1290 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1290 != nil {
		p.write(*flat1290)
		return nil
	} else {
		fields1287 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1287) == 0) {
			p.newline()
			for i1289, elem1288 := range fields1287 {
				if (i1289 > 0) {
					p.newline()
				}
				p.pretty_type(elem1288)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1297 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1297 != nil {
		p.write(*flat1297)
		return nil
	} else {
		_dollar_dollar := msg
		fields1291 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1292 := fields1291
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1293 := unwrapped_fields1292[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1293)
		p.newline()
		field1294 := unwrapped_fields1292[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1294)
		p.newline()
		field1295 := unwrapped_fields1292[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1295)
		p.newline()
		field1296 := unwrapped_fields1292[3].(string)
		p.pretty_csv_asof(field1296)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1304 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1304 != nil {
		p.write(*flat1304)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1536 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1536 = _dollar_dollar.GetPaths()
		}
		var _t1537 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1537 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1298 := []interface{}{_t1536, _t1537}
		unwrapped_fields1299 := fields1298
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1300 := unwrapped_fields1299[0].([]string)
		if field1300 != nil {
			p.newline()
			opt_val1301 := field1300
			p.pretty_csv_locator_paths(opt_val1301)
		}
		field1302 := unwrapped_fields1299[1].(*string)
		if field1302 != nil {
			p.newline()
			opt_val1303 := *field1302
			p.pretty_csv_locator_inline_data(opt_val1303)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1308 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1308 != nil {
		p.write(*flat1308)
		return nil
	} else {
		fields1305 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1305) == 0) {
			p.newline()
			for i1307, elem1306 := range fields1305 {
				if (i1307 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1306))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		fields1309 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1309))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1313 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1313 != nil {
		p.write(*flat1313)
		return nil
	} else {
		_dollar_dollar := msg
		_t1538 := p.deconstruct_csv_config(_dollar_dollar)
		fields1311 := _t1538
		unwrapped_fields1312 := fields1311
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1312)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1317 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		fields1314 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1314) == 0) {
			p.newline()
			for i1316, elem1315 := range fields1314 {
				if (i1316 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1315)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1326 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1326 != nil {
		p.write(*flat1326)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1539 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1539 = _dollar_dollar.GetTargetId()
		}
		fields1318 := []interface{}{_dollar_dollar.GetColumnPath(), _t1539, _dollar_dollar.GetTypes()}
		unwrapped_fields1319 := fields1318
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1320 := unwrapped_fields1319[0].([]string)
		p.pretty_gnf_column_path(field1320)
		field1321 := unwrapped_fields1319[1].(*pb.RelationId)
		if field1321 != nil {
			p.newline()
			opt_val1322 := field1321
			p.pretty_relation_id(opt_val1322)
		}
		p.newline()
		p.write("[")
		field1323 := unwrapped_fields1319[2].([]*pb.Type)
		for i1325, elem1324 := range field1323 {
			if (i1325 > 0) {
				p.newline()
			}
			p.pretty_type(elem1324)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1333 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1333 != nil {
		p.write(*flat1333)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1540 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1540 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1331 := _t1540
		if deconstruct_result1331 != nil {
			unwrapped1332 := *deconstruct_result1331
			p.write(p.formatStringValue(unwrapped1332))
		} else {
			_dollar_dollar := msg
			var _t1541 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1541 = _dollar_dollar
			}
			deconstruct_result1327 := _t1541
			if deconstruct_result1327 != nil {
				unwrapped1328 := deconstruct_result1327
				p.write("[")
				p.indent()
				for i1330, elem1329 := range unwrapped1328 {
					if (i1330 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1329))
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
	flat1335 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1335 != nil {
		p.write(*flat1335)
		return nil
	} else {
		fields1334 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1334))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1338 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1338 != nil {
		p.write(*flat1338)
		return nil
	} else {
		_dollar_dollar := msg
		fields1336 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1337 := fields1336
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1337)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		_dollar_dollar := msg
		fields1339 := _dollar_dollar.GetRelations()
		unwrapped_fields1340 := fields1339
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1340) == 0) {
			p.newline()
			for i1342, elem1341 := range unwrapped_fields1340 {
				if (i1342 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1341)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1348 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1348 != nil {
		p.write(*flat1348)
		return nil
	} else {
		_dollar_dollar := msg
		fields1344 := _dollar_dollar.GetMappings()
		unwrapped_fields1345 := fields1344
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1345) == 0) {
			p.newline()
			for i1347, elem1346 := range unwrapped_fields1345 {
				if (i1347 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1346)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		_dollar_dollar := msg
		fields1349 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1350 := fields1349
		field1351 := unwrapped_fields1350[0].([]string)
		p.pretty_edb_path(field1351)
		p.write(" ")
		field1352 := unwrapped_fields1350[1].(*pb.RelationId)
		p.pretty_relation_id(field1352)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1357 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		fields1354 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1354) == 0) {
			p.newline()
			for i1356, elem1355 := range fields1354 {
				if (i1356 > 0) {
					p.newline()
				}
				p.pretty_read(elem1355)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1368 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1542 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1542 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1366 := _t1542
		if deconstruct_result1366 != nil {
			unwrapped1367 := deconstruct_result1366
			p.pretty_demand(unwrapped1367)
		} else {
			_dollar_dollar := msg
			var _t1543 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1543 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1364 := _t1543
			if deconstruct_result1364 != nil {
				unwrapped1365 := deconstruct_result1364
				p.pretty_output(unwrapped1365)
			} else {
				_dollar_dollar := msg
				var _t1544 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1544 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1362 := _t1544
				if deconstruct_result1362 != nil {
					unwrapped1363 := deconstruct_result1362
					p.pretty_what_if(unwrapped1363)
				} else {
					_dollar_dollar := msg
					var _t1545 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1545 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1360 := _t1545
					if deconstruct_result1360 != nil {
						unwrapped1361 := deconstruct_result1360
						p.pretty_abort(unwrapped1361)
					} else {
						_dollar_dollar := msg
						var _t1546 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1546 = _dollar_dollar.GetExport()
						}
						deconstruct_result1358 := _t1546
						if deconstruct_result1358 != nil {
							unwrapped1359 := deconstruct_result1358
							p.pretty_export(unwrapped1359)
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
	flat1371 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		fields1369 := _dollar_dollar.GetRelationId()
		unwrapped_fields1370 := fields1369
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1370)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		fields1372 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1374 := unwrapped_fields1373[0].(string)
		p.pretty_name(field1374)
		p.newline()
		field1375 := unwrapped_fields1373[1].(*pb.RelationId)
		p.pretty_relation_id(field1375)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1381 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1381 != nil {
		p.write(*flat1381)
		return nil
	} else {
		_dollar_dollar := msg
		fields1377 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1379 := unwrapped_fields1378[0].(string)
		p.pretty_name(field1379)
		p.newline()
		field1380 := unwrapped_fields1378[1].(*pb.Epoch)
		p.pretty_epoch(field1380)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1547 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1547 = ptr(_dollar_dollar.GetName())
		}
		fields1382 := []interface{}{_t1547, _dollar_dollar.GetRelationId()}
		unwrapped_fields1383 := fields1382
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1384 := unwrapped_fields1383[0].(*string)
		if field1384 != nil {
			p.newline()
			opt_val1385 := *field1384
			p.pretty_name(opt_val1385)
		}
		p.newline()
		field1386 := unwrapped_fields1383[1].(*pb.RelationId)
		p.pretty_relation_id(field1386)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1390 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1390 != nil {
		p.write(*flat1390)
		return nil
	} else {
		_dollar_dollar := msg
		fields1388 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1389 := fields1388
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1389)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1401 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1401 != nil {
		p.write(*flat1401)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1548 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1548 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1396 := _t1548
		if deconstruct_result1396 != nil {
			unwrapped1397 := deconstruct_result1396
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1398 := unwrapped1397[0].(string)
			p.pretty_export_csv_path(field1398)
			p.newline()
			field1399 := unwrapped1397[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1399)
			p.newline()
			field1400 := unwrapped1397[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1400)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1549 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1550 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1549 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1550}
			}
			deconstruct_result1391 := _t1549
			if deconstruct_result1391 != nil {
				unwrapped1392 := deconstruct_result1391
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1393 := unwrapped1392[0].(string)
				p.pretty_export_csv_path(field1393)
				p.newline()
				field1394 := unwrapped1392[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1394)
				p.newline()
				field1395 := unwrapped1392[2].([][]interface{})
				p.pretty_config_dict(field1395)
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
	flat1403 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		fields1402 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1402))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1551 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1551 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1406 := _t1551
		if deconstruct_result1406 != nil {
			unwrapped1407 := deconstruct_result1406
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1407) == 0) {
				p.newline()
				for i1409, elem1408 := range unwrapped1407 {
					if (i1409 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1408)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1552 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1552 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1404 := _t1552
			if deconstruct_result1404 != nil {
				unwrapped1405 := deconstruct_result1404
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1405)
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
	flat1415 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1415 != nil {
		p.write(*flat1415)
		return nil
	} else {
		_dollar_dollar := msg
		fields1411 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1412 := fields1411
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1413 := unwrapped_fields1412[0].(string)
		p.write(p.formatStringValue(field1413))
		p.newline()
		field1414 := unwrapped_fields1412[1].(*pb.RelationId)
		p.pretty_relation_id(field1414)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1419 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1419 != nil {
		p.write(*flat1419)
		return nil
	} else {
		fields1416 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1416) == 0) {
			p.newline()
			for i1418, elem1417 := range fields1416 {
				if (i1418 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1417)
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
		_t1591 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1591)
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
