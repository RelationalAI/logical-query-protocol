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
	_t1536 := &pb.Value{}
	_t1536.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1536
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1537 := &pb.Value{}
	_t1537.Value = &pb.Value_IntValue{IntValue: v}
	return _t1537
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1538 := &pb.Value{}
	_t1538.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1538
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1539 := &pb.Value{}
	_t1539.Value = &pb.Value_StringValue{StringValue: v}
	return _t1539
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1540 := &pb.Value{}
	_t1540.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1540
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1541 := &pb.Value{}
	_t1541.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1541
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1542 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1542})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1543 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1543})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1544 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1544})
			}
		}
	}
	_t1545 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1545})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1546 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1546})
	_t1547 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1547})
	if msg.GetNewLine() != "" {
		_t1548 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1548})
	}
	_t1549 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1549})
	_t1550 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1550})
	_t1551 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1551})
	if msg.GetComment() != "" {
		_t1552 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1552})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1553 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1553})
	}
	_t1554 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1554})
	_t1555 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1555})
	_t1556 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1556})
	if msg.GetPartitionSizeMb() != 0 {
		_t1557 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1557})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1558 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1558})
	_t1559 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1559})
	_t1560 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1560})
	_t1561 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1561})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1562 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1562})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1563 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1563})
		}
	}
	_t1564 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1564})
	_t1565 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1565})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1566 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1566})
	}
	if msg.Compression != nil {
		_t1567 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1567})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1568 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1568})
	}
	if msg.SyntaxMissingString != nil {
		_t1569 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1569})
	}
	if msg.SyntaxDelim != nil {
		_t1570 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1570})
	}
	if msg.SyntaxQuotechar != nil {
		_t1571 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1571})
	}
	if msg.SyntaxEscapechar != nil {
		_t1572 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1572})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1573 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1573
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
	flat712 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat712 != nil {
		p.write(*flat712)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1406 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1406 = _dollar_dollar.GetConfigure()
		}
		var _t1407 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1407 = _dollar_dollar.GetSync()
		}
		fields703 := []interface{}{_t1406, _t1407, _dollar_dollar.GetEpochs()}
		unwrapped_fields704 := fields703
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field705 := unwrapped_fields704[0].(*pb.Configure)
		if field705 != nil {
			p.newline()
			opt_val706 := field705
			p.pretty_configure(opt_val706)
		}
		field707 := unwrapped_fields704[1].(*pb.Sync)
		if field707 != nil {
			p.newline()
			opt_val708 := field707
			p.pretty_sync(opt_val708)
		}
		field709 := unwrapped_fields704[2].([]*pb.Epoch)
		if !(len(field709) == 0) {
			p.newline()
			for i711, elem710 := range field709 {
				if (i711 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem710)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat715 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat715 != nil {
		p.write(*flat715)
		return nil
	} else {
		_dollar_dollar := msg
		_t1408 := p.deconstruct_configure(_dollar_dollar)
		fields713 := _t1408
		unwrapped_fields714 := fields713
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields714)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat719 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat719 != nil {
		p.write(*flat719)
		return nil
	} else {
		fields716 := msg
		p.write("{")
		p.indent()
		if !(len(fields716) == 0) {
			p.newline()
			for i718, elem717 := range fields716 {
				if (i718 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem717)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat724 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat724 != nil {
		p.write(*flat724)
		return nil
	} else {
		_dollar_dollar := msg
		fields720 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields721 := fields720
		p.write(":")
		field722 := unwrapped_fields721[0].(string)
		p.write(field722)
		p.write(" ")
		field723 := unwrapped_fields721[1].(*pb.Value)
		p.pretty_raw_value(field723)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat748 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat748 != nil {
		p.write(*flat748)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1409 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1409 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result746 := _t1409
		if deconstruct_result746 != nil {
			unwrapped747 := deconstruct_result746
			p.pretty_raw_date(unwrapped747)
		} else {
			_dollar_dollar := msg
			var _t1410 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1410 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result744 := _t1410
			if deconstruct_result744 != nil {
				unwrapped745 := deconstruct_result744
				p.pretty_raw_datetime(unwrapped745)
			} else {
				_dollar_dollar := msg
				var _t1411 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1411 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result742 := _t1411
				if deconstruct_result742 != nil {
					unwrapped743 := *deconstruct_result742
					p.write(p.formatStringValue(unwrapped743))
				} else {
					_dollar_dollar := msg
					var _t1412 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1412 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result740 := _t1412
					if deconstruct_result740 != nil {
						unwrapped741 := *deconstruct_result740
						p.write(fmt.Sprintf("%di32", unwrapped741))
					} else {
						_dollar_dollar := msg
						var _t1413 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1413 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result738 := _t1413
						if deconstruct_result738 != nil {
							unwrapped739 := *deconstruct_result738
							p.write(fmt.Sprintf("%d", unwrapped739))
						} else {
							_dollar_dollar := msg
							var _t1414 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1414 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result736 := _t1414
							if deconstruct_result736 != nil {
								unwrapped737 := *deconstruct_result736
								p.write(fmt.Sprintf("%sf32", strconv.FormatFloat(float64(unwrapped737), 'g', -1, 32)))
							} else {
								_dollar_dollar := msg
								var _t1415 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1415 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result734 := _t1415
								if deconstruct_result734 != nil {
									unwrapped735 := *deconstruct_result734
									p.write(formatFloat64(unwrapped735))
								} else {
									_dollar_dollar := msg
									var _t1416 *pb.UInt128Value
									if hasProtoField(_dollar_dollar, "uint128_value") {
										_t1416 = _dollar_dollar.GetUint128Value()
									}
									deconstruct_result732 := _t1416
									if deconstruct_result732 != nil {
										unwrapped733 := deconstruct_result732
										p.write(p.formatUint128(unwrapped733))
									} else {
										_dollar_dollar := msg
										var _t1417 *pb.Int128Value
										if hasProtoField(_dollar_dollar, "int128_value") {
											_t1417 = _dollar_dollar.GetInt128Value()
										}
										deconstruct_result730 := _t1417
										if deconstruct_result730 != nil {
											unwrapped731 := deconstruct_result730
											p.write(p.formatInt128(unwrapped731))
										} else {
											_dollar_dollar := msg
											var _t1418 *pb.DecimalValue
											if hasProtoField(_dollar_dollar, "decimal_value") {
												_t1418 = _dollar_dollar.GetDecimalValue()
											}
											deconstruct_result728 := _t1418
											if deconstruct_result728 != nil {
												unwrapped729 := deconstruct_result728
												p.write(p.formatDecimal(unwrapped729))
											} else {
												_dollar_dollar := msg
												var _t1419 *bool
												if hasProtoField(_dollar_dollar, "boolean_value") {
													_t1419 = ptr(_dollar_dollar.GetBooleanValue())
												}
												deconstruct_result726 := _t1419
												if deconstruct_result726 != nil {
													unwrapped727 := *deconstruct_result726
													p.pretty_boolean_value(unwrapped727)
												} else {
													fields725 := msg
													_ = fields725
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
	return nil
}

func (p *PrettyPrinter) pretty_raw_date(msg *pb.DateValue) interface{} {
	flat754 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat754 != nil {
		p.write(*flat754)
		return nil
	} else {
		_dollar_dollar := msg
		fields749 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields750 := fields749
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field751 := unwrapped_fields750[0].(int64)
		p.write(fmt.Sprintf("%d", field751))
		p.newline()
		field752 := unwrapped_fields750[1].(int64)
		p.write(fmt.Sprintf("%d", field752))
		p.newline()
		field753 := unwrapped_fields750[2].(int64)
		p.write(fmt.Sprintf("%d", field753))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_dollar_dollar := msg
		fields755 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields756 := fields755
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field757 := unwrapped_fields756[0].(int64)
		p.write(fmt.Sprintf("%d", field757))
		p.newline()
		field758 := unwrapped_fields756[1].(int64)
		p.write(fmt.Sprintf("%d", field758))
		p.newline()
		field759 := unwrapped_fields756[2].(int64)
		p.write(fmt.Sprintf("%d", field759))
		p.newline()
		field760 := unwrapped_fields756[3].(int64)
		p.write(fmt.Sprintf("%d", field760))
		p.newline()
		field761 := unwrapped_fields756[4].(int64)
		p.write(fmt.Sprintf("%d", field761))
		p.newline()
		field762 := unwrapped_fields756[5].(int64)
		p.write(fmt.Sprintf("%d", field762))
		field763 := unwrapped_fields756[6].(*int64)
		if field763 != nil {
			p.newline()
			opt_val764 := *field763
			p.write(fmt.Sprintf("%d", opt_val764))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1420 []interface{}
	if _dollar_dollar {
		_t1420 = []interface{}{}
	}
	deconstruct_result768 := _t1420
	if deconstruct_result768 != nil {
		unwrapped769 := deconstruct_result768
		_ = unwrapped769
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1421 []interface{}
		if !(_dollar_dollar) {
			_t1421 = []interface{}{}
		}
		deconstruct_result766 := _t1421
		if deconstruct_result766 != nil {
			unwrapped767 := deconstruct_result766
			_ = unwrapped767
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat774 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat774 != nil {
		p.write(*flat774)
		return nil
	} else {
		_dollar_dollar := msg
		fields770 := _dollar_dollar.GetFragments()
		unwrapped_fields771 := fields770
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields771) == 0) {
			p.newline()
			for i773, elem772 := range unwrapped_fields771 {
				if (i773 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem772)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat777 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat777 != nil {
		p.write(*flat777)
		return nil
	} else {
		_dollar_dollar := msg
		fields775 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields776 := fields775
		p.write(":")
		p.write(unwrapped_fields776)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat784 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat784 != nil {
		p.write(*flat784)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1422 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1422 = _dollar_dollar.GetWrites()
		}
		var _t1423 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1423 = _dollar_dollar.GetReads()
		}
		fields778 := []interface{}{_t1422, _t1423}
		unwrapped_fields779 := fields778
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field780 := unwrapped_fields779[0].([]*pb.Write)
		if field780 != nil {
			p.newline()
			opt_val781 := field780
			p.pretty_epoch_writes(opt_val781)
		}
		field782 := unwrapped_fields779[1].([]*pb.Read)
		if field782 != nil {
			p.newline()
			opt_val783 := field782
			p.pretty_epoch_reads(opt_val783)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat788 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat788 != nil {
		p.write(*flat788)
		return nil
	} else {
		fields785 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields785) == 0) {
			p.newline()
			for i787, elem786 := range fields785 {
				if (i787 > 0) {
					p.newline()
				}
				p.pretty_write(elem786)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat797 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat797 != nil {
		p.write(*flat797)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1424 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1424 = _dollar_dollar.GetDefine()
		}
		deconstruct_result795 := _t1424
		if deconstruct_result795 != nil {
			unwrapped796 := deconstruct_result795
			p.pretty_define(unwrapped796)
		} else {
			_dollar_dollar := msg
			var _t1425 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1425 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result793 := _t1425
			if deconstruct_result793 != nil {
				unwrapped794 := deconstruct_result793
				p.pretty_undefine(unwrapped794)
			} else {
				_dollar_dollar := msg
				var _t1426 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1426 = _dollar_dollar.GetContext()
				}
				deconstruct_result791 := _t1426
				if deconstruct_result791 != nil {
					unwrapped792 := deconstruct_result791
					p.pretty_context(unwrapped792)
				} else {
					_dollar_dollar := msg
					var _t1427 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1427 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result789 := _t1427
					if deconstruct_result789 != nil {
						unwrapped790 := deconstruct_result789
						p.pretty_snapshot(unwrapped790)
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
	flat800 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat800 != nil {
		p.write(*flat800)
		return nil
	} else {
		_dollar_dollar := msg
		fields798 := _dollar_dollar.GetFragment()
		unwrapped_fields799 := fields798
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields799)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat807 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat807 != nil {
		p.write(*flat807)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields801 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields802 := fields801
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field803 := unwrapped_fields802[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field803)
		field804 := unwrapped_fields802[1].([]*pb.Declaration)
		if !(len(field804) == 0) {
			p.newline()
			for i806, elem805 := range field804 {
				if (i806 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem805)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat809 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat809 != nil {
		p.write(*flat809)
		return nil
	} else {
		fields808 := msg
		p.pretty_fragment_id(fields808)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat818 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat818 != nil {
		p.write(*flat818)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1428 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1428 = _dollar_dollar.GetDef()
		}
		deconstruct_result816 := _t1428
		if deconstruct_result816 != nil {
			unwrapped817 := deconstruct_result816
			p.pretty_def(unwrapped817)
		} else {
			_dollar_dollar := msg
			var _t1429 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1429 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result814 := _t1429
			if deconstruct_result814 != nil {
				unwrapped815 := deconstruct_result814
				p.pretty_algorithm(unwrapped815)
			} else {
				_dollar_dollar := msg
				var _t1430 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1430 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result812 := _t1430
				if deconstruct_result812 != nil {
					unwrapped813 := deconstruct_result812
					p.pretty_constraint(unwrapped813)
				} else {
					_dollar_dollar := msg
					var _t1431 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1431 = _dollar_dollar.GetData()
					}
					deconstruct_result810 := _t1431
					if deconstruct_result810 != nil {
						unwrapped811 := deconstruct_result810
						p.pretty_data(unwrapped811)
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
	flat825 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat825 != nil {
		p.write(*flat825)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1432 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1432 = _dollar_dollar.GetAttrs()
		}
		fields819 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1432}
		unwrapped_fields820 := fields819
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field821 := unwrapped_fields820[0].(*pb.RelationId)
		p.pretty_relation_id(field821)
		p.newline()
		field822 := unwrapped_fields820[1].(*pb.Abstraction)
		p.pretty_abstraction(field822)
		field823 := unwrapped_fields820[2].([]*pb.Attribute)
		if field823 != nil {
			p.newline()
			opt_val824 := field823
			p.pretty_attrs(opt_val824)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat830 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat830 != nil {
		p.write(*flat830)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1433 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1434 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1433 = ptr(_t1434)
		}
		deconstruct_result828 := _t1433
		if deconstruct_result828 != nil {
			unwrapped829 := *deconstruct_result828
			p.write(":")
			p.write(unwrapped829)
		} else {
			_dollar_dollar := msg
			_t1435 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result826 := _t1435
			if deconstruct_result826 != nil {
				unwrapped827 := deconstruct_result826
				p.write(p.formatUint128(unwrapped827))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat835 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat835 != nil {
		p.write(*flat835)
		return nil
	} else {
		_dollar_dollar := msg
		_t1436 := p.deconstruct_bindings(_dollar_dollar)
		fields831 := []interface{}{_t1436, _dollar_dollar.GetValue()}
		unwrapped_fields832 := fields831
		p.write("(")
		p.indent()
		field833 := unwrapped_fields832[0].([]interface{})
		p.pretty_bindings(field833)
		p.newline()
		field834 := unwrapped_fields832[1].(*pb.Formula)
		p.pretty_formula(field834)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat843 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat843 != nil {
		p.write(*flat843)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1437 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1437 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields836 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1437}
		unwrapped_fields837 := fields836
		p.write("[")
		p.indent()
		field838 := unwrapped_fields837[0].([]*pb.Binding)
		for i840, elem839 := range field838 {
			if (i840 > 0) {
				p.newline()
			}
			p.pretty_binding(elem839)
		}
		field841 := unwrapped_fields837[1].([]*pb.Binding)
		if field841 != nil {
			p.newline()
			opt_val842 := field841
			p.pretty_value_bindings(opt_val842)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat848 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat848 != nil {
		p.write(*flat848)
		return nil
	} else {
		_dollar_dollar := msg
		fields844 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields845 := fields844
		field846 := unwrapped_fields845[0].(string)
		p.write(field846)
		p.write("::")
		field847 := unwrapped_fields845[1].(*pb.Type)
		p.pretty_type(field847)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1438 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1438 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result873 := _t1438
		if deconstruct_result873 != nil {
			unwrapped874 := deconstruct_result873
			p.pretty_unspecified_type(unwrapped874)
		} else {
			_dollar_dollar := msg
			var _t1439 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1439 = _dollar_dollar.GetStringType()
			}
			deconstruct_result871 := _t1439
			if deconstruct_result871 != nil {
				unwrapped872 := deconstruct_result871
				p.pretty_string_type(unwrapped872)
			} else {
				_dollar_dollar := msg
				var _t1440 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1440 = _dollar_dollar.GetIntType()
				}
				deconstruct_result869 := _t1440
				if deconstruct_result869 != nil {
					unwrapped870 := deconstruct_result869
					p.pretty_int_type(unwrapped870)
				} else {
					_dollar_dollar := msg
					var _t1441 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1441 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result867 := _t1441
					if deconstruct_result867 != nil {
						unwrapped868 := deconstruct_result867
						p.pretty_float_type(unwrapped868)
					} else {
						_dollar_dollar := msg
						var _t1442 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1442 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result865 := _t1442
						if deconstruct_result865 != nil {
							unwrapped866 := deconstruct_result865
							p.pretty_uint128_type(unwrapped866)
						} else {
							_dollar_dollar := msg
							var _t1443 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1443 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result863 := _t1443
							if deconstruct_result863 != nil {
								unwrapped864 := deconstruct_result863
								p.pretty_int128_type(unwrapped864)
							} else {
								_dollar_dollar := msg
								var _t1444 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1444 = _dollar_dollar.GetDateType()
								}
								deconstruct_result861 := _t1444
								if deconstruct_result861 != nil {
									unwrapped862 := deconstruct_result861
									p.pretty_date_type(unwrapped862)
								} else {
									_dollar_dollar := msg
									var _t1445 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1445 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result859 := _t1445
									if deconstruct_result859 != nil {
										unwrapped860 := deconstruct_result859
										p.pretty_datetime_type(unwrapped860)
									} else {
										_dollar_dollar := msg
										var _t1446 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1446 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result857 := _t1446
										if deconstruct_result857 != nil {
											unwrapped858 := deconstruct_result857
											p.pretty_missing_type(unwrapped858)
										} else {
											_dollar_dollar := msg
											var _t1447 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1447 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result855 := _t1447
											if deconstruct_result855 != nil {
												unwrapped856 := deconstruct_result855
												p.pretty_decimal_type(unwrapped856)
											} else {
												_dollar_dollar := msg
												var _t1448 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1448 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result853 := _t1448
												if deconstruct_result853 != nil {
													unwrapped854 := deconstruct_result853
													p.pretty_boolean_type(unwrapped854)
												} else {
													_dollar_dollar := msg
													var _t1449 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1449 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result851 := _t1449
													if deconstruct_result851 != nil {
														unwrapped852 := deconstruct_result851
														p.pretty_int32_type(unwrapped852)
													} else {
														_dollar_dollar := msg
														var _t1450 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1450 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result849 := _t1450
														if deconstruct_result849 != nil {
															unwrapped850 := deconstruct_result849
															p.pretty_float32_type(unwrapped850)
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
	return nil
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields876 := msg
	_ = fields876
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields877 := msg
	_ = fields877
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields878 := msg
	_ = fields878
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields879 := msg
	_ = fields879
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields880 := msg
	_ = fields880
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields881 := msg
	_ = fields881
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields882 := msg
	_ = fields882
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields883 := msg
	_ = fields883
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields884 := msg
	_ = fields884
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat889 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat889 != nil {
		p.write(*flat889)
		return nil
	} else {
		_dollar_dollar := msg
		fields885 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields886 := fields885
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field887 := unwrapped_fields886[0].(int64)
		p.write(fmt.Sprintf("%d", field887))
		p.newline()
		field888 := unwrapped_fields886[1].(int64)
		p.write(fmt.Sprintf("%d", field888))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields890 := msg
	_ = fields890
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields891 := msg
	_ = fields891
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields892 := msg
	_ = fields892
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat896 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		fields893 := msg
		p.write("|")
		if !(len(fields893) == 0) {
			p.write(" ")
			for i895, elem894 := range fields893 {
				if (i895 > 0) {
					p.newline()
				}
				p.pretty_binding(elem894)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat923 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1451 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1451 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result921 := _t1451
		if deconstruct_result921 != nil {
			unwrapped922 := deconstruct_result921
			p.pretty_true(unwrapped922)
		} else {
			_dollar_dollar := msg
			var _t1452 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1452 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result919 := _t1452
			if deconstruct_result919 != nil {
				unwrapped920 := deconstruct_result919
				p.pretty_false(unwrapped920)
			} else {
				_dollar_dollar := msg
				var _t1453 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1453 = _dollar_dollar.GetExists()
				}
				deconstruct_result917 := _t1453
				if deconstruct_result917 != nil {
					unwrapped918 := deconstruct_result917
					p.pretty_exists(unwrapped918)
				} else {
					_dollar_dollar := msg
					var _t1454 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1454 = _dollar_dollar.GetReduce()
					}
					deconstruct_result915 := _t1454
					if deconstruct_result915 != nil {
						unwrapped916 := deconstruct_result915
						p.pretty_reduce(unwrapped916)
					} else {
						_dollar_dollar := msg
						var _t1455 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1455 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result913 := _t1455
						if deconstruct_result913 != nil {
							unwrapped914 := deconstruct_result913
							p.pretty_conjunction(unwrapped914)
						} else {
							_dollar_dollar := msg
							var _t1456 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1456 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result911 := _t1456
							if deconstruct_result911 != nil {
								unwrapped912 := deconstruct_result911
								p.pretty_disjunction(unwrapped912)
							} else {
								_dollar_dollar := msg
								var _t1457 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1457 = _dollar_dollar.GetNot()
								}
								deconstruct_result909 := _t1457
								if deconstruct_result909 != nil {
									unwrapped910 := deconstruct_result909
									p.pretty_not(unwrapped910)
								} else {
									_dollar_dollar := msg
									var _t1458 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1458 = _dollar_dollar.GetFfi()
									}
									deconstruct_result907 := _t1458
									if deconstruct_result907 != nil {
										unwrapped908 := deconstruct_result907
										p.pretty_ffi(unwrapped908)
									} else {
										_dollar_dollar := msg
										var _t1459 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1459 = _dollar_dollar.GetAtom()
										}
										deconstruct_result905 := _t1459
										if deconstruct_result905 != nil {
											unwrapped906 := deconstruct_result905
											p.pretty_atom(unwrapped906)
										} else {
											_dollar_dollar := msg
											var _t1460 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1460 = _dollar_dollar.GetPragma()
											}
											deconstruct_result903 := _t1460
											if deconstruct_result903 != nil {
												unwrapped904 := deconstruct_result903
												p.pretty_pragma(unwrapped904)
											} else {
												_dollar_dollar := msg
												var _t1461 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1461 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result901 := _t1461
												if deconstruct_result901 != nil {
													unwrapped902 := deconstruct_result901
													p.pretty_primitive(unwrapped902)
												} else {
													_dollar_dollar := msg
													var _t1462 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1462 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result899 := _t1462
													if deconstruct_result899 != nil {
														unwrapped900 := deconstruct_result899
														p.pretty_rel_atom(unwrapped900)
													} else {
														_dollar_dollar := msg
														var _t1463 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1463 = _dollar_dollar.GetCast()
														}
														deconstruct_result897 := _t1463
														if deconstruct_result897 != nil {
															unwrapped898 := deconstruct_result897
															p.pretty_cast(unwrapped898)
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
	fields924 := msg
	_ = fields924
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields925 := msg
	_ = fields925
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat930 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat930 != nil {
		p.write(*flat930)
		return nil
	} else {
		_dollar_dollar := msg
		_t1464 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields926 := []interface{}{_t1464, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields927 := fields926
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field928 := unwrapped_fields927[0].([]interface{})
		p.pretty_bindings(field928)
		p.newline()
		field929 := unwrapped_fields927[1].(*pb.Formula)
		p.pretty_formula(field929)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat936 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat936 != nil {
		p.write(*flat936)
		return nil
	} else {
		_dollar_dollar := msg
		fields931 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields932 := fields931
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field933 := unwrapped_fields932[0].(*pb.Abstraction)
		p.pretty_abstraction(field933)
		p.newline()
		field934 := unwrapped_fields932[1].(*pb.Abstraction)
		p.pretty_abstraction(field934)
		p.newline()
		field935 := unwrapped_fields932[2].([]*pb.Term)
		p.pretty_terms(field935)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat940 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat940 != nil {
		p.write(*flat940)
		return nil
	} else {
		fields937 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields937) == 0) {
			p.newline()
			for i939, elem938 := range fields937 {
				if (i939 > 0) {
					p.newline()
				}
				p.pretty_term(elem938)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat945 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat945 != nil {
		p.write(*flat945)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1465 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1465 = _dollar_dollar.GetVar()
		}
		deconstruct_result943 := _t1465
		if deconstruct_result943 != nil {
			unwrapped944 := deconstruct_result943
			p.pretty_var(unwrapped944)
		} else {
			_dollar_dollar := msg
			var _t1466 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1466 = _dollar_dollar.GetConstant()
			}
			deconstruct_result941 := _t1466
			if deconstruct_result941 != nil {
				unwrapped942 := deconstruct_result941
				p.pretty_value(unwrapped942)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat948 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat948 != nil {
		p.write(*flat948)
		return nil
	} else {
		_dollar_dollar := msg
		fields946 := _dollar_dollar.GetName()
		unwrapped_fields947 := fields946
		p.write(unwrapped_fields947)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat972 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat972 != nil {
		p.write(*flat972)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1467 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1467 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result970 := _t1467
		if deconstruct_result970 != nil {
			unwrapped971 := deconstruct_result970
			p.pretty_date(unwrapped971)
		} else {
			_dollar_dollar := msg
			var _t1468 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1468 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result968 := _t1468
			if deconstruct_result968 != nil {
				unwrapped969 := deconstruct_result968
				p.pretty_datetime(unwrapped969)
			} else {
				_dollar_dollar := msg
				var _t1469 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1469 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result966 := _t1469
				if deconstruct_result966 != nil {
					unwrapped967 := *deconstruct_result966
					p.write(p.formatStringValue(unwrapped967))
				} else {
					_dollar_dollar := msg
					var _t1470 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1470 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result964 := _t1470
					if deconstruct_result964 != nil {
						unwrapped965 := *deconstruct_result964
						p.write(fmt.Sprintf("%di32", unwrapped965))
					} else {
						_dollar_dollar := msg
						var _t1471 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1471 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result962 := _t1471
						if deconstruct_result962 != nil {
							unwrapped963 := *deconstruct_result962
							p.write(fmt.Sprintf("%d", unwrapped963))
						} else {
							_dollar_dollar := msg
							var _t1472 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1472 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result960 := _t1472
							if deconstruct_result960 != nil {
								unwrapped961 := *deconstruct_result960
								p.write(fmt.Sprintf("%sf32", strconv.FormatFloat(float64(unwrapped961), 'g', -1, 32)))
							} else {
								_dollar_dollar := msg
								var _t1473 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1473 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result958 := _t1473
								if deconstruct_result958 != nil {
									unwrapped959 := *deconstruct_result958
									p.write(formatFloat64(unwrapped959))
								} else {
									_dollar_dollar := msg
									var _t1474 *pb.UInt128Value
									if hasProtoField(_dollar_dollar, "uint128_value") {
										_t1474 = _dollar_dollar.GetUint128Value()
									}
									deconstruct_result956 := _t1474
									if deconstruct_result956 != nil {
										unwrapped957 := deconstruct_result956
										p.write(p.formatUint128(unwrapped957))
									} else {
										_dollar_dollar := msg
										var _t1475 *pb.Int128Value
										if hasProtoField(_dollar_dollar, "int128_value") {
											_t1475 = _dollar_dollar.GetInt128Value()
										}
										deconstruct_result954 := _t1475
										if deconstruct_result954 != nil {
											unwrapped955 := deconstruct_result954
											p.write(p.formatInt128(unwrapped955))
										} else {
											_dollar_dollar := msg
											var _t1476 *pb.DecimalValue
											if hasProtoField(_dollar_dollar, "decimal_value") {
												_t1476 = _dollar_dollar.GetDecimalValue()
											}
											deconstruct_result952 := _t1476
											if deconstruct_result952 != nil {
												unwrapped953 := deconstruct_result952
												p.write(p.formatDecimal(unwrapped953))
											} else {
												_dollar_dollar := msg
												var _t1477 *bool
												if hasProtoField(_dollar_dollar, "boolean_value") {
													_t1477 = ptr(_dollar_dollar.GetBooleanValue())
												}
												deconstruct_result950 := _t1477
												if deconstruct_result950 != nil {
													unwrapped951 := *deconstruct_result950
													p.pretty_boolean_value(unwrapped951)
												} else {
													fields949 := msg
													_ = fields949
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
	return nil
}

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) interface{} {
	flat978 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat978 != nil {
		p.write(*flat978)
		return nil
	} else {
		_dollar_dollar := msg
		fields973 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields974 := fields973
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field975 := unwrapped_fields974[0].(int64)
		p.write(fmt.Sprintf("%d", field975))
		p.newline()
		field976 := unwrapped_fields974[1].(int64)
		p.write(fmt.Sprintf("%d", field976))
		p.newline()
		field977 := unwrapped_fields974[2].(int64)
		p.write(fmt.Sprintf("%d", field977))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_dollar_dollar := msg
		fields979 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields980 := fields979
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field981 := unwrapped_fields980[0].(int64)
		p.write(fmt.Sprintf("%d", field981))
		p.newline()
		field982 := unwrapped_fields980[1].(int64)
		p.write(fmt.Sprintf("%d", field982))
		p.newline()
		field983 := unwrapped_fields980[2].(int64)
		p.write(fmt.Sprintf("%d", field983))
		p.newline()
		field984 := unwrapped_fields980[3].(int64)
		p.write(fmt.Sprintf("%d", field984))
		p.newline()
		field985 := unwrapped_fields980[4].(int64)
		p.write(fmt.Sprintf("%d", field985))
		p.newline()
		field986 := unwrapped_fields980[5].(int64)
		p.write(fmt.Sprintf("%d", field986))
		field987 := unwrapped_fields980[6].(*int64)
		if field987 != nil {
			p.newline()
			opt_val988 := *field987
			p.write(fmt.Sprintf("%d", opt_val988))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat994 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat994 != nil {
		p.write(*flat994)
		return nil
	} else {
		_dollar_dollar := msg
		fields990 := _dollar_dollar.GetArgs()
		unwrapped_fields991 := fields990
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields991) == 0) {
			p.newline()
			for i993, elem992 := range unwrapped_fields991 {
				if (i993 > 0) {
					p.newline()
				}
				p.pretty_formula(elem992)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat999 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat999 != nil {
		p.write(*flat999)
		return nil
	} else {
		_dollar_dollar := msg
		fields995 := _dollar_dollar.GetArgs()
		unwrapped_fields996 := fields995
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields996) == 0) {
			p.newline()
			for i998, elem997 := range unwrapped_fields996 {
				if (i998 > 0) {
					p.newline()
				}
				p.pretty_formula(elem997)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1002 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1002 != nil {
		p.write(*flat1002)
		return nil
	} else {
		_dollar_dollar := msg
		fields1000 := _dollar_dollar.GetArg()
		unwrapped_fields1001 := fields1000
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1001)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1008 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1008 != nil {
		p.write(*flat1008)
		return nil
	} else {
		_dollar_dollar := msg
		fields1003 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1004 := fields1003
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1005 := unwrapped_fields1004[0].(string)
		p.pretty_name(field1005)
		p.newline()
		field1006 := unwrapped_fields1004[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1006)
		p.newline()
		field1007 := unwrapped_fields1004[2].([]*pb.Term)
		p.pretty_terms(field1007)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1010 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1010 != nil {
		p.write(*flat1010)
		return nil
	} else {
		fields1009 := msg
		p.write(":")
		p.write(fields1009)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1014 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1014 != nil {
		p.write(*flat1014)
		return nil
	} else {
		fields1011 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1011) == 0) {
			p.newline()
			for i1013, elem1012 := range fields1011 {
				if (i1013 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1012)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1021 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1021 != nil {
		p.write(*flat1021)
		return nil
	} else {
		_dollar_dollar := msg
		fields1015 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1016 := fields1015
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1017 := unwrapped_fields1016[0].(*pb.RelationId)
		p.pretty_relation_id(field1017)
		field1018 := unwrapped_fields1016[1].([]*pb.Term)
		if !(len(field1018) == 0) {
			p.newline()
			for i1020, elem1019 := range field1018 {
				if (i1020 > 0) {
					p.newline()
				}
				p.pretty_term(elem1019)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1028 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		_dollar_dollar := msg
		fields1022 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1023 := fields1022
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1024 := unwrapped_fields1023[0].(string)
		p.pretty_name(field1024)
		field1025 := unwrapped_fields1023[1].([]*pb.Term)
		if !(len(field1025) == 0) {
			p.newline()
			for i1027, elem1026 := range field1025 {
				if (i1027 > 0) {
					p.newline()
				}
				p.pretty_term(elem1026)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1044 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1044 != nil {
		p.write(*flat1044)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1478 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1478 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1043 := _t1478
		if guard_result1043 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1479 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1479 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1042 := _t1479
			if guard_result1042 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1480 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1480 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1041 := _t1480
				if guard_result1041 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1481 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1481 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1040 := _t1481
					if guard_result1040 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1482 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1482 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1039 := _t1482
						if guard_result1039 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1483 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1483 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1038 := _t1483
							if guard_result1038 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1484 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1484 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1037 := _t1484
								if guard_result1037 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1485 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1485 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1036 := _t1485
									if guard_result1036 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1486 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1486 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1035 := _t1486
										if guard_result1035 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1029 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1030 := fields1029
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1031 := unwrapped_fields1030[0].(string)
											p.pretty_name(field1031)
											field1032 := unwrapped_fields1030[1].([]*pb.RelTerm)
											if !(len(field1032) == 0) {
												p.newline()
												for i1034, elem1033 := range field1032 {
													if (i1034 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1033)
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
	flat1049 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1487 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1487 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1045 := _t1487
		unwrapped_fields1046 := fields1045
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1047 := unwrapped_fields1046[0].(*pb.Term)
		p.pretty_term(field1047)
		p.newline()
		field1048 := unwrapped_fields1046[1].(*pb.Term)
		p.pretty_term(field1048)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1054 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1488 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1488 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1050 := _t1488
		unwrapped_fields1051 := fields1050
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1052 := unwrapped_fields1051[0].(*pb.Term)
		p.pretty_term(field1052)
		p.newline()
		field1053 := unwrapped_fields1051[1].(*pb.Term)
		p.pretty_term(field1053)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1059 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1059 != nil {
		p.write(*flat1059)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1489 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1489 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1055 := _t1489
		unwrapped_fields1056 := fields1055
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1057 := unwrapped_fields1056[0].(*pb.Term)
		p.pretty_term(field1057)
		p.newline()
		field1058 := unwrapped_fields1056[1].(*pb.Term)
		p.pretty_term(field1058)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1064 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1064 != nil {
		p.write(*flat1064)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1490 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1490 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1060 := _t1490
		unwrapped_fields1061 := fields1060
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1062 := unwrapped_fields1061[0].(*pb.Term)
		p.pretty_term(field1062)
		p.newline()
		field1063 := unwrapped_fields1061[1].(*pb.Term)
		p.pretty_term(field1063)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1069 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1069 != nil {
		p.write(*flat1069)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1491 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1491 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1065 := _t1491
		unwrapped_fields1066 := fields1065
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1067 := unwrapped_fields1066[0].(*pb.Term)
		p.pretty_term(field1067)
		p.newline()
		field1068 := unwrapped_fields1066[1].(*pb.Term)
		p.pretty_term(field1068)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1075 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1492 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1492 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1070 := _t1492
		unwrapped_fields1071 := fields1070
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1072 := unwrapped_fields1071[0].(*pb.Term)
		p.pretty_term(field1072)
		p.newline()
		field1073 := unwrapped_fields1071[1].(*pb.Term)
		p.pretty_term(field1073)
		p.newline()
		field1074 := unwrapped_fields1071[2].(*pb.Term)
		p.pretty_term(field1074)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1081 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1493 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1493 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1076 := _t1493
		unwrapped_fields1077 := fields1076
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1078 := unwrapped_fields1077[0].(*pb.Term)
		p.pretty_term(field1078)
		p.newline()
		field1079 := unwrapped_fields1077[1].(*pb.Term)
		p.pretty_term(field1079)
		p.newline()
		field1080 := unwrapped_fields1077[2].(*pb.Term)
		p.pretty_term(field1080)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1087 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1087 != nil {
		p.write(*flat1087)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1494 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1494 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1082 := _t1494
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].(*pb.Term)
		p.pretty_term(field1084)
		p.newline()
		field1085 := unwrapped_fields1083[1].(*pb.Term)
		p.pretty_term(field1085)
		p.newline()
		field1086 := unwrapped_fields1083[2].(*pb.Term)
		p.pretty_term(field1086)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1093 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1495 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1495 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1088 := _t1495
		unwrapped_fields1089 := fields1088
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1090 := unwrapped_fields1089[0].(*pb.Term)
		p.pretty_term(field1090)
		p.newline()
		field1091 := unwrapped_fields1089[1].(*pb.Term)
		p.pretty_term(field1091)
		p.newline()
		field1092 := unwrapped_fields1089[2].(*pb.Term)
		p.pretty_term(field1092)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1496 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1496 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1096 := _t1496
		if deconstruct_result1096 != nil {
			unwrapped1097 := deconstruct_result1096
			p.pretty_specialized_value(unwrapped1097)
		} else {
			_dollar_dollar := msg
			var _t1497 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1497 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1094 := _t1497
			if deconstruct_result1094 != nil {
				unwrapped1095 := deconstruct_result1094
				p.pretty_term(unwrapped1095)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		fields1099 := msg
		p.write("#")
		p.pretty_raw_value(fields1099)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1107 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1107 != nil {
		p.write(*flat1107)
		return nil
	} else {
		_dollar_dollar := msg
		fields1101 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1103 := unwrapped_fields1102[0].(string)
		p.pretty_name(field1103)
		field1104 := unwrapped_fields1102[1].([]*pb.RelTerm)
		if !(len(field1104) == 0) {
			p.newline()
			for i1106, elem1105 := range field1104 {
				if (i1106 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1105)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		fields1108 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1109 := fields1108
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1110 := unwrapped_fields1109[0].(*pb.Term)
		p.pretty_term(field1110)
		p.newline()
		field1111 := unwrapped_fields1109[1].(*pb.Term)
		p.pretty_term(field1111)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1116 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1116 != nil {
		p.write(*flat1116)
		return nil
	} else {
		fields1113 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1113) == 0) {
			p.newline()
			for i1115, elem1114 := range fields1113 {
				if (i1115 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1114)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		fields1117 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1118 := fields1117
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1119 := unwrapped_fields1118[0].(string)
		p.pretty_name(field1119)
		field1120 := unwrapped_fields1118[1].([]*pb.Value)
		if !(len(field1120) == 0) {
			p.newline()
			for i1122, elem1121 := range field1120 {
				if (i1122 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1121)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		fields1124 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1126 := unwrapped_fields1125[0].([]*pb.RelationId)
		if !(len(field1126) == 0) {
			p.newline()
			for i1128, elem1127 := range field1126 {
				if (i1128 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1127)
			}
		}
		p.newline()
		field1129 := unwrapped_fields1125[1].(*pb.Script)
		p.pretty_script(field1129)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1135 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		fields1131 := _dollar_dollar.GetConstructs()
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1132) == 0) {
			p.newline()
			for i1134, elem1133 := range unwrapped_fields1132 {
				if (i1134 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1133)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1498 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1498 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1138 := _t1498
		if deconstruct_result1138 != nil {
			unwrapped1139 := deconstruct_result1138
			p.pretty_loop(unwrapped1139)
		} else {
			_dollar_dollar := msg
			var _t1499 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1499 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1136 := _t1499
			if deconstruct_result1136 != nil {
				unwrapped1137 := deconstruct_result1136
				p.pretty_instruction(unwrapped1137)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		fields1141 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1143 := unwrapped_fields1142[0].([]*pb.Instruction)
		p.pretty_init(field1143)
		p.newline()
		field1144 := unwrapped_fields1142[1].(*pb.Script)
		p.pretty_script(field1144)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1149 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1149 != nil {
		p.write(*flat1149)
		return nil
	} else {
		fields1146 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1146) == 0) {
			p.newline()
			for i1148, elem1147 := range fields1146 {
				if (i1148 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1147)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1500 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1500 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1158 := _t1500
		if deconstruct_result1158 != nil {
			unwrapped1159 := deconstruct_result1158
			p.pretty_assign(unwrapped1159)
		} else {
			_dollar_dollar := msg
			var _t1501 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1501 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1156 := _t1501
			if deconstruct_result1156 != nil {
				unwrapped1157 := deconstruct_result1156
				p.pretty_upsert(unwrapped1157)
			} else {
				_dollar_dollar := msg
				var _t1502 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1502 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1154 := _t1502
				if deconstruct_result1154 != nil {
					unwrapped1155 := deconstruct_result1154
					p.pretty_break(unwrapped1155)
				} else {
					_dollar_dollar := msg
					var _t1503 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1503 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1152 := _t1503
					if deconstruct_result1152 != nil {
						unwrapped1153 := deconstruct_result1152
						p.pretty_monoid_def(unwrapped1153)
					} else {
						_dollar_dollar := msg
						var _t1504 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1504 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1150 := _t1504
						if deconstruct_result1150 != nil {
							unwrapped1151 := deconstruct_result1150
							p.pretty_monus_def(unwrapped1151)
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
	flat1167 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1505 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1505 = _dollar_dollar.GetAttrs()
		}
		fields1161 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1505}
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1163 := unwrapped_fields1162[0].(*pb.RelationId)
		p.pretty_relation_id(field1163)
		p.newline()
		field1164 := unwrapped_fields1162[1].(*pb.Abstraction)
		p.pretty_abstraction(field1164)
		field1165 := unwrapped_fields1162[2].([]*pb.Attribute)
		if field1165 != nil {
			p.newline()
			opt_val1166 := field1165
			p.pretty_attrs(opt_val1166)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1506 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1506 = _dollar_dollar.GetAttrs()
		}
		fields1168 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1506}
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1170 := unwrapped_fields1169[0].(*pb.RelationId)
		p.pretty_relation_id(field1170)
		p.newline()
		field1171 := unwrapped_fields1169[1].([]interface{})
		p.pretty_abstraction_with_arity(field1171)
		field1172 := unwrapped_fields1169[2].([]*pb.Attribute)
		if field1172 != nil {
			p.newline()
			opt_val1173 := field1172
			p.pretty_attrs(opt_val1173)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		_t1507 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1175 := []interface{}{_t1507, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1176 := fields1175
		p.write("(")
		p.indent()
		field1177 := unwrapped_fields1176[0].([]interface{})
		p.pretty_bindings(field1177)
		p.newline()
		field1178 := unwrapped_fields1176[1].(*pb.Formula)
		p.pretty_formula(field1178)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1508 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1508 = _dollar_dollar.GetAttrs()
		}
		fields1180 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1508}
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(*pb.RelationId)
		p.pretty_relation_id(field1182)
		p.newline()
		field1183 := unwrapped_fields1181[1].(*pb.Abstraction)
		p.pretty_abstraction(field1183)
		field1184 := unwrapped_fields1181[2].([]*pb.Attribute)
		if field1184 != nil {
			p.newline()
			opt_val1185 := field1184
			p.pretty_attrs(opt_val1185)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1509 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1509 = _dollar_dollar.GetAttrs()
		}
		fields1187 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1509}
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1189 := unwrapped_fields1188[0].(*pb.Monoid)
		p.pretty_monoid(field1189)
		p.newline()
		field1190 := unwrapped_fields1188[1].(*pb.RelationId)
		p.pretty_relation_id(field1190)
		p.newline()
		field1191 := unwrapped_fields1188[2].([]interface{})
		p.pretty_abstraction_with_arity(field1191)
		field1192 := unwrapped_fields1188[3].([]*pb.Attribute)
		if field1192 != nil {
			p.newline()
			opt_val1193 := field1192
			p.pretty_attrs(opt_val1193)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1203 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1203 != nil {
		p.write(*flat1203)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1510 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1510 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1201 := _t1510
		if deconstruct_result1201 != nil {
			unwrapped1202 := deconstruct_result1201
			p.pretty_or_monoid(unwrapped1202)
		} else {
			_dollar_dollar := msg
			var _t1511 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1511 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1199 := _t1511
			if deconstruct_result1199 != nil {
				unwrapped1200 := deconstruct_result1199
				p.pretty_min_monoid(unwrapped1200)
			} else {
				_dollar_dollar := msg
				var _t1512 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1512 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1197 := _t1512
				if deconstruct_result1197 != nil {
					unwrapped1198 := deconstruct_result1197
					p.pretty_max_monoid(unwrapped1198)
				} else {
					_dollar_dollar := msg
					var _t1513 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1513 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1195 := _t1513
					if deconstruct_result1195 != nil {
						unwrapped1196 := deconstruct_result1195
						p.pretty_sum_monoid(unwrapped1196)
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
	fields1204 := msg
	_ = fields1204
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1207 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		_dollar_dollar := msg
		fields1205 := _dollar_dollar.GetType()
		unwrapped_fields1206 := fields1205
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1206)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_dollar_dollar := msg
		fields1208 := _dollar_dollar.GetType()
		unwrapped_fields1209 := fields1208
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1209)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1213 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1213 != nil {
		p.write(*flat1213)
		return nil
	} else {
		_dollar_dollar := msg
		fields1211 := _dollar_dollar.GetType()
		unwrapped_fields1212 := fields1211
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1212)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1514 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1514 = _dollar_dollar.GetAttrs()
		}
		fields1214 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1514}
		unwrapped_fields1215 := fields1214
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1216 := unwrapped_fields1215[0].(*pb.Monoid)
		p.pretty_monoid(field1216)
		p.newline()
		field1217 := unwrapped_fields1215[1].(*pb.RelationId)
		p.pretty_relation_id(field1217)
		p.newline()
		field1218 := unwrapped_fields1215[2].([]interface{})
		p.pretty_abstraction_with_arity(field1218)
		field1219 := unwrapped_fields1215[3].([]*pb.Attribute)
		if field1219 != nil {
			p.newline()
			opt_val1220 := field1219
			p.pretty_attrs(opt_val1220)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1228 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1228 != nil {
		p.write(*flat1228)
		return nil
	} else {
		_dollar_dollar := msg
		fields1222 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1223 := fields1222
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1224 := unwrapped_fields1223[0].(*pb.RelationId)
		p.pretty_relation_id(field1224)
		p.newline()
		field1225 := unwrapped_fields1223[1].(*pb.Abstraction)
		p.pretty_abstraction(field1225)
		p.newline()
		field1226 := unwrapped_fields1223[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1226)
		p.newline()
		field1227 := unwrapped_fields1223[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1227)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1232 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1232 != nil {
		p.write(*flat1232)
		return nil
	} else {
		fields1229 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1229) == 0) {
			p.newline()
			for i1231, elem1230 := range fields1229 {
				if (i1231 > 0) {
					p.newline()
				}
				p.pretty_var(elem1230)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1236 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1236 != nil {
		p.write(*flat1236)
		return nil
	} else {
		fields1233 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1233) == 0) {
			p.newline()
			for i1235, elem1234 := range fields1233 {
				if (i1235 > 0) {
					p.newline()
				}
				p.pretty_var(elem1234)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1243 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1515 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1515 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1241 := _t1515
		if deconstruct_result1241 != nil {
			unwrapped1242 := deconstruct_result1241
			p.pretty_edb(unwrapped1242)
		} else {
			_dollar_dollar := msg
			var _t1516 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1516 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1239 := _t1516
			if deconstruct_result1239 != nil {
				unwrapped1240 := deconstruct_result1239
				p.pretty_betree_relation(unwrapped1240)
			} else {
				_dollar_dollar := msg
				var _t1517 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1517 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1237 := _t1517
				if deconstruct_result1237 != nil {
					unwrapped1238 := deconstruct_result1237
					p.pretty_csv_data(unwrapped1238)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		fields1244 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1246 := unwrapped_fields1245[0].(*pb.RelationId)
		p.pretty_relation_id(field1246)
		p.newline()
		field1247 := unwrapped_fields1245[1].([]string)
		p.pretty_edb_path(field1247)
		p.newline()
		field1248 := unwrapped_fields1245[2].([]*pb.Type)
		p.pretty_edb_types(field1248)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		fields1250 := msg
		p.write("[")
		p.indent()
		for i1252, elem1251 := range fields1250 {
			if (i1252 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1251))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		fields1254 := msg
		p.write("[")
		p.indent()
		for i1256, elem1255 := range fields1254 {
			if (i1256 > 0) {
				p.newline()
			}
			p.pretty_type(elem1255)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		_dollar_dollar := msg
		fields1258 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1260 := unwrapped_fields1259[0].(*pb.RelationId)
		p.pretty_relation_id(field1260)
		p.newline()
		field1261 := unwrapped_fields1259[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1261)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1268 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1268 != nil {
		p.write(*flat1268)
		return nil
	} else {
		_dollar_dollar := msg
		_t1518 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1263 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1518}
		unwrapped_fields1264 := fields1263
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1265 := unwrapped_fields1264[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1265)
		p.newline()
		field1266 := unwrapped_fields1264[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1266)
		p.newline()
		field1267 := unwrapped_fields1264[2].([][]interface{})
		p.pretty_config_dict(field1267)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		fields1269 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1269) == 0) {
			p.newline()
			for i1271, elem1270 := range fields1269 {
				if (i1271 > 0) {
					p.newline()
				}
				p.pretty_type(elem1270)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1276 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1276 != nil {
		p.write(*flat1276)
		return nil
	} else {
		fields1273 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1273) == 0) {
			p.newline()
			for i1275, elem1274 := range fields1273 {
				if (i1275 > 0) {
					p.newline()
				}
				p.pretty_type(elem1274)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		fields1277 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1278 := fields1277
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1279 := unwrapped_fields1278[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1279)
		p.newline()
		field1280 := unwrapped_fields1278[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1280)
		p.newline()
		field1281 := unwrapped_fields1278[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1281)
		p.newline()
		field1282 := unwrapped_fields1278[3].(string)
		p.pretty_csv_asof(field1282)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1290 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1290 != nil {
		p.write(*flat1290)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1519 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1519 = _dollar_dollar.GetPaths()
		}
		var _t1520 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1520 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1284 := []interface{}{_t1519, _t1520}
		unwrapped_fields1285 := fields1284
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1286 := unwrapped_fields1285[0].([]string)
		if field1286 != nil {
			p.newline()
			opt_val1287 := field1286
			p.pretty_csv_locator_paths(opt_val1287)
		}
		field1288 := unwrapped_fields1285[1].(*string)
		if field1288 != nil {
			p.newline()
			opt_val1289 := *field1288
			p.pretty_csv_locator_inline_data(opt_val1289)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1294 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1294 != nil {
		p.write(*flat1294)
		return nil
	} else {
		fields1291 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1291) == 0) {
			p.newline()
			for i1293, elem1292 := range fields1291 {
				if (i1293 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1292))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		fields1295 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1295))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1299 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1299 != nil {
		p.write(*flat1299)
		return nil
	} else {
		_dollar_dollar := msg
		_t1521 := p.deconstruct_csv_config(_dollar_dollar)
		fields1297 := _t1521
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1298)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		fields1300 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1300) == 0) {
			p.newline()
			for i1302, elem1301 := range fields1300 {
				if (i1302 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1301)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1312 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1312 != nil {
		p.write(*flat1312)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1522 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1522 = _dollar_dollar.GetTargetId()
		}
		fields1304 := []interface{}{_dollar_dollar.GetColumnPath(), _t1522, _dollar_dollar.GetTypes()}
		unwrapped_fields1305 := fields1304
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1306 := unwrapped_fields1305[0].([]string)
		p.pretty_gnf_column_path(field1306)
		field1307 := unwrapped_fields1305[1].(*pb.RelationId)
		if field1307 != nil {
			p.newline()
			opt_val1308 := field1307
			p.pretty_relation_id(opt_val1308)
		}
		p.newline()
		p.write("[")
		field1309 := unwrapped_fields1305[2].([]*pb.Type)
		for i1311, elem1310 := range field1309 {
			if (i1311 > 0) {
				p.newline()
			}
			p.pretty_type(elem1310)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1319 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1319 != nil {
		p.write(*flat1319)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1523 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1523 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1317 := _t1523
		if deconstruct_result1317 != nil {
			unwrapped1318 := *deconstruct_result1317
			p.write(p.formatStringValue(unwrapped1318))
		} else {
			_dollar_dollar := msg
			var _t1524 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1524 = _dollar_dollar
			}
			deconstruct_result1313 := _t1524
			if deconstruct_result1313 != nil {
				unwrapped1314 := deconstruct_result1313
				p.write("[")
				p.indent()
				for i1316, elem1315 := range unwrapped1314 {
					if (i1316 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1315))
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
	flat1321 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1321 != nil {
		p.write(*flat1321)
		return nil
	} else {
		fields1320 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1320))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		_dollar_dollar := msg
		fields1322 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1323 := fields1322
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1323)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		fields1325 := _dollar_dollar.GetRelations()
		unwrapped_fields1326 := fields1325
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1326) == 0) {
			p.newline()
			for i1328, elem1327 := range unwrapped_fields1326 {
				if (i1328 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1327)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1334 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1334 != nil {
		p.write(*flat1334)
		return nil
	} else {
		_dollar_dollar := msg
		fields1330 := _dollar_dollar.GetMappings()
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1331) == 0) {
			p.newline()
			for i1333, elem1332 := range unwrapped_fields1331 {
				if (i1333 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1332)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1339 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1339 != nil {
		p.write(*flat1339)
		return nil
	} else {
		_dollar_dollar := msg
		fields1335 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1336 := fields1335
		field1337 := unwrapped_fields1336[0].([]string)
		p.pretty_edb_path(field1337)
		p.write(" ")
		field1338 := unwrapped_fields1336[1].(*pb.RelationId)
		p.pretty_relation_id(field1338)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		fields1340 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1340) == 0) {
			p.newline()
			for i1342, elem1341 := range fields1340 {
				if (i1342 > 0) {
					p.newline()
				}
				p.pretty_read(elem1341)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1354 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1354 != nil {
		p.write(*flat1354)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1525 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1525 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1352 := _t1525
		if deconstruct_result1352 != nil {
			unwrapped1353 := deconstruct_result1352
			p.pretty_demand(unwrapped1353)
		} else {
			_dollar_dollar := msg
			var _t1526 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1526 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1350 := _t1526
			if deconstruct_result1350 != nil {
				unwrapped1351 := deconstruct_result1350
				p.pretty_output(unwrapped1351)
			} else {
				_dollar_dollar := msg
				var _t1527 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1527 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1348 := _t1527
				if deconstruct_result1348 != nil {
					unwrapped1349 := deconstruct_result1348
					p.pretty_what_if(unwrapped1349)
				} else {
					_dollar_dollar := msg
					var _t1528 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1528 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1346 := _t1528
					if deconstruct_result1346 != nil {
						unwrapped1347 := deconstruct_result1346
						p.pretty_abort(unwrapped1347)
					} else {
						_dollar_dollar := msg
						var _t1529 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1529 = _dollar_dollar.GetExport()
						}
						deconstruct_result1344 := _t1529
						if deconstruct_result1344 != nil {
							unwrapped1345 := deconstruct_result1344
							p.pretty_export(unwrapped1345)
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
	flat1357 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		_dollar_dollar := msg
		fields1355 := _dollar_dollar.GetRelationId()
		unwrapped_fields1356 := fields1355
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1356)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1362 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1362 != nil {
		p.write(*flat1362)
		return nil
	} else {
		_dollar_dollar := msg
		fields1358 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1359 := fields1358
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1360 := unwrapped_fields1359[0].(string)
		p.pretty_name(field1360)
		p.newline()
		field1361 := unwrapped_fields1359[1].(*pb.RelationId)
		p.pretty_relation_id(field1361)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1367 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1367 != nil {
		p.write(*flat1367)
		return nil
	} else {
		_dollar_dollar := msg
		fields1363 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1364 := fields1363
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1365 := unwrapped_fields1364[0].(string)
		p.pretty_name(field1365)
		p.newline()
		field1366 := unwrapped_fields1364[1].(*pb.Epoch)
		p.pretty_epoch(field1366)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1373 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1373 != nil {
		p.write(*flat1373)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1530 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1530 = ptr(_dollar_dollar.GetName())
		}
		fields1368 := []interface{}{_t1530, _dollar_dollar.GetRelationId()}
		unwrapped_fields1369 := fields1368
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1370 := unwrapped_fields1369[0].(*string)
		if field1370 != nil {
			p.newline()
			opt_val1371 := *field1370
			p.pretty_name(opt_val1371)
		}
		p.newline()
		field1372 := unwrapped_fields1369[1].(*pb.RelationId)
		p.pretty_relation_id(field1372)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		fields1374 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1375 := fields1374
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1375)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1531 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1531 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1382 := _t1531
		if deconstruct_result1382 != nil {
			unwrapped1383 := deconstruct_result1382
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1384 := unwrapped1383[0].(string)
			p.pretty_export_csv_path(field1384)
			p.newline()
			field1385 := unwrapped1383[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1385)
			p.newline()
			field1386 := unwrapped1383[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1386)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1532 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1533 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1532 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1533}
			}
			deconstruct_result1377 := _t1532
			if deconstruct_result1377 != nil {
				unwrapped1378 := deconstruct_result1377
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1379 := unwrapped1378[0].(string)
				p.pretty_export_csv_path(field1379)
				p.newline()
				field1380 := unwrapped1378[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1380)
				p.newline()
				field1381 := unwrapped1378[2].([][]interface{})
				p.pretty_config_dict(field1381)
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
	flat1389 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		fields1388 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1388))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1396 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1396 != nil {
		p.write(*flat1396)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1534 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1534 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1392 := _t1534
		if deconstruct_result1392 != nil {
			unwrapped1393 := deconstruct_result1392
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1393) == 0) {
				p.newline()
				for i1395, elem1394 := range unwrapped1393 {
					if (i1395 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1394)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1535 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1535 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1390 := _t1535
			if deconstruct_result1390 != nil {
				unwrapped1391 := deconstruct_result1390
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1391)
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
	flat1401 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1401 != nil {
		p.write(*flat1401)
		return nil
	} else {
		_dollar_dollar := msg
		fields1397 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1398 := fields1397
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1399 := unwrapped_fields1398[0].(string)
		p.write(p.formatStringValue(field1399))
		p.newline()
		field1400 := unwrapped_fields1398[1].(*pb.RelationId)
		p.pretty_relation_id(field1400)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		fields1402 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1402) == 0) {
			p.newline()
			for i1404, elem1403 := range fields1402 {
				if (i1404 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1403)
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
		_t1574 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1574)
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
