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
	_t1447 := &pb.Value{}
	_t1447.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1447
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1448 := &pb.Value{}
	_t1448.Value = &pb.Value_IntValue{IntValue: v}
	return _t1448
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1449 := &pb.Value{}
	_t1449.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1449
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1450 := &pb.Value{}
	_t1450.Value = &pb.Value_StringValue{StringValue: v}
	return _t1450
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1451 := &pb.Value{}
	_t1451.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1451
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1452 := &pb.Value{}
	_t1452.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1452
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1453 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1453})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1454 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1454})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1455 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1455})
			}
		}
	}
	_t1456 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1456})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1457 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1457})
	_t1458 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1458})
	if msg.GetNewLine() != "" {
		_t1459 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1459})
	}
	_t1460 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1460})
	_t1461 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1461})
	_t1462 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1462})
	if msg.GetComment() != "" {
		_t1463 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1463})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1464 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1464})
	}
	_t1465 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1465})
	_t1466 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1466})
	_t1467 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1467})
	if msg.GetPartitionSizeMb() != 0 {
		_t1468 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1468})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1469 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1469})
	_t1470 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1470})
	_t1471 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1471})
	_t1472 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1472})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1473 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1473})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1474 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1474})
		}
	}
	_t1475 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1475})
	_t1476 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1476})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1477 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1477})
	}
	if msg.Compression != nil {
		_t1478 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1478})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1479 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1479})
	}
	if msg.SyntaxMissingString != nil {
		_t1480 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1480})
	}
	if msg.SyntaxDelim != nil {
		_t1481 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1481})
	}
	if msg.SyntaxQuotechar != nil {
		_t1482 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1482})
	}
	if msg.SyntaxEscapechar != nil {
		_t1483 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1483})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1484 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1484
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
	flat673 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat673 != nil {
		p.write(*flat673)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1328 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1328 = _dollar_dollar.GetConfigure()
		}
		var _t1329 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1329 = _dollar_dollar.GetSync()
		}
		fields664 := []interface{}{_t1328, _t1329, _dollar_dollar.GetEpochs()}
		unwrapped_fields665 := fields664
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field666 := unwrapped_fields665[0].(*pb.Configure)
		if field666 != nil {
			p.newline()
			opt_val667 := field666
			p.pretty_configure(opt_val667)
		}
		field668 := unwrapped_fields665[1].(*pb.Sync)
		if field668 != nil {
			p.newline()
			opt_val669 := field668
			p.pretty_sync(opt_val669)
		}
		field670 := unwrapped_fields665[2].([]*pb.Epoch)
		if !(len(field670) == 0) {
			p.newline()
			for i672, elem671 := range field670 {
				if (i672 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem671)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat676 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat676 != nil {
		p.write(*flat676)
		return nil
	} else {
		_dollar_dollar := msg
		_t1330 := p.deconstruct_configure(_dollar_dollar)
		fields674 := _t1330
		unwrapped_fields675 := fields674
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields675)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat680 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat680 != nil {
		p.write(*flat680)
		return nil
	} else {
		fields677 := msg
		p.write("{")
		p.indent()
		if !(len(fields677) == 0) {
			p.newline()
			for i679, elem678 := range fields677 {
				if (i679 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem678)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat685 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat685 != nil {
		p.write(*flat685)
		return nil
	} else {
		_dollar_dollar := msg
		fields681 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields682 := fields681
		p.write(":")
		field683 := unwrapped_fields682[0].(string)
		p.write(field683)
		p.write(" ")
		field684 := unwrapped_fields682[1].(*pb.Value)
		p.pretty_value(field684)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat709 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat709 != nil {
		p.write(*flat709)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1331 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1331 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result707 := _t1331
		if deconstruct_result707 != nil {
			unwrapped708 := deconstruct_result707
			p.pretty_date(unwrapped708)
		} else {
			_dollar_dollar := msg
			var _t1332 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1332 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result705 := _t1332
			if deconstruct_result705 != nil {
				unwrapped706 := deconstruct_result705
				p.pretty_datetime(unwrapped706)
			} else {
				_dollar_dollar := msg
				var _t1333 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1333 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result703 := _t1333
				if deconstruct_result703 != nil {
					unwrapped704 := *deconstruct_result703
					p.write(p.formatStringValue(unwrapped704))
				} else {
					_dollar_dollar := msg
					var _t1334 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t1334 = ptr(_dollar_dollar.GetIntValue())
					}
					deconstruct_result701 := _t1334
					if deconstruct_result701 != nil {
						unwrapped702 := *deconstruct_result701
						p.write(fmt.Sprintf("%d", unwrapped702))
					} else {
						_dollar_dollar := msg
						var _t1335 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t1335 = ptr(_dollar_dollar.GetFloatValue())
						}
						deconstruct_result699 := _t1335
						if deconstruct_result699 != nil {
							unwrapped700 := *deconstruct_result699
							p.write(formatFloat64(unwrapped700))
						} else {
							_dollar_dollar := msg
							var _t1336 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t1336 = _dollar_dollar.GetUint128Value()
							}
							deconstruct_result697 := _t1336
							if deconstruct_result697 != nil {
								unwrapped698 := deconstruct_result697
								p.write(p.formatUint128(unwrapped698))
							} else {
								_dollar_dollar := msg
								var _t1337 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t1337 = _dollar_dollar.GetInt128Value()
								}
								deconstruct_result695 := _t1337
								if deconstruct_result695 != nil {
									unwrapped696 := deconstruct_result695
									p.write(p.formatInt128(unwrapped696))
								} else {
									_dollar_dollar := msg
									var _t1338 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t1338 = _dollar_dollar.GetDecimalValue()
									}
									deconstruct_result693 := _t1338
									if deconstruct_result693 != nil {
										unwrapped694 := deconstruct_result693
										p.write(p.formatDecimal(unwrapped694))
									} else {
										_dollar_dollar := msg
										var _t1339 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t1339 = ptr(_dollar_dollar.GetBooleanValue())
										}
										deconstruct_result691 := _t1339
										if deconstruct_result691 != nil {
											unwrapped692 := *deconstruct_result691
											p.pretty_boolean_value(unwrapped692)
										} else {
											_dollar_dollar := msg
											var _t1340 *int32
											if hasProtoField(_dollar_dollar, "int32_value") {
												_t1340 = ptr(_dollar_dollar.GetInt32Value())
											}
											deconstruct_result689 := _t1340
											if deconstruct_result689 != nil {
												unwrapped690 := *deconstruct_result689
												p.write(fmt.Sprintf("%di32", unwrapped690))
											} else {
												_dollar_dollar := msg
												var _t1341 *float32
												if hasProtoField(_dollar_dollar, "float32_value") {
													_t1341 = ptr(_dollar_dollar.GetFloat32Value())
												}
												deconstruct_result687 := _t1341
												if deconstruct_result687 != nil {
													unwrapped688 := *deconstruct_result687
													p.write(fmt.Sprintf("%sf32", strconv.FormatFloat(float64(unwrapped688), 'g', -1, 32)))
												} else {
													fields686 := msg
													_ = fields686
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
	flat715 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat715 != nil {
		p.write(*flat715)
		return nil
	} else {
		_dollar_dollar := msg
		fields710 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields711 := fields710
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field712 := unwrapped_fields711[0].(int64)
		p.write(fmt.Sprintf("%d", field712))
		p.newline()
		field713 := unwrapped_fields711[1].(int64)
		p.write(fmt.Sprintf("%d", field713))
		p.newline()
		field714 := unwrapped_fields711[2].(int64)
		p.write(fmt.Sprintf("%d", field714))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat726 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat726 != nil {
		p.write(*flat726)
		return nil
	} else {
		_dollar_dollar := msg
		fields716 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields717 := fields716
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field718 := unwrapped_fields717[0].(int64)
		p.write(fmt.Sprintf("%d", field718))
		p.newline()
		field719 := unwrapped_fields717[1].(int64)
		p.write(fmt.Sprintf("%d", field719))
		p.newline()
		field720 := unwrapped_fields717[2].(int64)
		p.write(fmt.Sprintf("%d", field720))
		p.newline()
		field721 := unwrapped_fields717[3].(int64)
		p.write(fmt.Sprintf("%d", field721))
		p.newline()
		field722 := unwrapped_fields717[4].(int64)
		p.write(fmt.Sprintf("%d", field722))
		p.newline()
		field723 := unwrapped_fields717[5].(int64)
		p.write(fmt.Sprintf("%d", field723))
		field724 := unwrapped_fields717[6].(*int64)
		if field724 != nil {
			p.newline()
			opt_val725 := *field724
			p.write(fmt.Sprintf("%d", opt_val725))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1342 []interface{}
	if _dollar_dollar {
		_t1342 = []interface{}{}
	}
	deconstruct_result729 := _t1342
	if deconstruct_result729 != nil {
		unwrapped730 := deconstruct_result729
		_ = unwrapped730
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1343 []interface{}
		if !(_dollar_dollar) {
			_t1343 = []interface{}{}
		}
		deconstruct_result727 := _t1343
		if deconstruct_result727 != nil {
			unwrapped728 := deconstruct_result727
			_ = unwrapped728
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat735 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat735 != nil {
		p.write(*flat735)
		return nil
	} else {
		_dollar_dollar := msg
		fields731 := _dollar_dollar.GetFragments()
		unwrapped_fields732 := fields731
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields732) == 0) {
			p.newline()
			for i734, elem733 := range unwrapped_fields732 {
				if (i734 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem733)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat738 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat738 != nil {
		p.write(*flat738)
		return nil
	} else {
		_dollar_dollar := msg
		fields736 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields737 := fields736
		p.write(":")
		p.write(unwrapped_fields737)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat745 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat745 != nil {
		p.write(*flat745)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1344 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1344 = _dollar_dollar.GetWrites()
		}
		var _t1345 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1345 = _dollar_dollar.GetReads()
		}
		fields739 := []interface{}{_t1344, _t1345}
		unwrapped_fields740 := fields739
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field741 := unwrapped_fields740[0].([]*pb.Write)
		if field741 != nil {
			p.newline()
			opt_val742 := field741
			p.pretty_epoch_writes(opt_val742)
		}
		field743 := unwrapped_fields740[1].([]*pb.Read)
		if field743 != nil {
			p.newline()
			opt_val744 := field743
			p.pretty_epoch_reads(opt_val744)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat749 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat749 != nil {
		p.write(*flat749)
		return nil
	} else {
		fields746 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields746) == 0) {
			p.newline()
			for i748, elem747 := range fields746 {
				if (i748 > 0) {
					p.newline()
				}
				p.pretty_write(elem747)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat758 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat758 != nil {
		p.write(*flat758)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1346 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1346 = _dollar_dollar.GetDefine()
		}
		deconstruct_result756 := _t1346
		if deconstruct_result756 != nil {
			unwrapped757 := deconstruct_result756
			p.pretty_define(unwrapped757)
		} else {
			_dollar_dollar := msg
			var _t1347 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1347 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result754 := _t1347
			if deconstruct_result754 != nil {
				unwrapped755 := deconstruct_result754
				p.pretty_undefine(unwrapped755)
			} else {
				_dollar_dollar := msg
				var _t1348 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1348 = _dollar_dollar.GetContext()
				}
				deconstruct_result752 := _t1348
				if deconstruct_result752 != nil {
					unwrapped753 := deconstruct_result752
					p.pretty_context(unwrapped753)
				} else {
					_dollar_dollar := msg
					var _t1349 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1349 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result750 := _t1349
					if deconstruct_result750 != nil {
						unwrapped751 := deconstruct_result750
						p.pretty_snapshot(unwrapped751)
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
	flat761 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat761 != nil {
		p.write(*flat761)
		return nil
	} else {
		_dollar_dollar := msg
		fields759 := _dollar_dollar.GetFragment()
		unwrapped_fields760 := fields759
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields760)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat768 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat768 != nil {
		p.write(*flat768)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields762 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields763 := fields762
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field764 := unwrapped_fields763[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field764)
		field765 := unwrapped_fields763[1].([]*pb.Declaration)
		if !(len(field765) == 0) {
			p.newline()
			for i767, elem766 := range field765 {
				if (i767 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem766)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat770 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat770 != nil {
		p.write(*flat770)
		return nil
	} else {
		fields769 := msg
		p.pretty_fragment_id(fields769)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat779 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat779 != nil {
		p.write(*flat779)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1350 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1350 = _dollar_dollar.GetDef()
		}
		deconstruct_result777 := _t1350
		if deconstruct_result777 != nil {
			unwrapped778 := deconstruct_result777
			p.pretty_def(unwrapped778)
		} else {
			_dollar_dollar := msg
			var _t1351 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1351 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result775 := _t1351
			if deconstruct_result775 != nil {
				unwrapped776 := deconstruct_result775
				p.pretty_algorithm(unwrapped776)
			} else {
				_dollar_dollar := msg
				var _t1352 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1352 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result773 := _t1352
				if deconstruct_result773 != nil {
					unwrapped774 := deconstruct_result773
					p.pretty_constraint(unwrapped774)
				} else {
					_dollar_dollar := msg
					var _t1353 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1353 = _dollar_dollar.GetData()
					}
					deconstruct_result771 := _t1353
					if deconstruct_result771 != nil {
						unwrapped772 := deconstruct_result771
						p.pretty_data(unwrapped772)
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
	flat786 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat786 != nil {
		p.write(*flat786)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1354 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1354 = _dollar_dollar.GetAttrs()
		}
		fields780 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1354}
		unwrapped_fields781 := fields780
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field782 := unwrapped_fields781[0].(*pb.RelationId)
		p.pretty_relation_id(field782)
		p.newline()
		field783 := unwrapped_fields781[1].(*pb.Abstraction)
		p.pretty_abstraction(field783)
		field784 := unwrapped_fields781[2].([]*pb.Attribute)
		if field784 != nil {
			p.newline()
			opt_val785 := field784
			p.pretty_attrs(opt_val785)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat791 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat791 != nil {
		p.write(*flat791)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1355 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1356 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1355 = ptr(_t1356)
		}
		deconstruct_result789 := _t1355
		if deconstruct_result789 != nil {
			unwrapped790 := *deconstruct_result789
			p.write(":")
			p.write(unwrapped790)
		} else {
			_dollar_dollar := msg
			_t1357 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result787 := _t1357
			if deconstruct_result787 != nil {
				unwrapped788 := deconstruct_result787
				p.write(p.formatUint128(unwrapped788))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat796 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat796 != nil {
		p.write(*flat796)
		return nil
	} else {
		_dollar_dollar := msg
		_t1358 := p.deconstruct_bindings(_dollar_dollar)
		fields792 := []interface{}{_t1358, _dollar_dollar.GetValue()}
		unwrapped_fields793 := fields792
		p.write("(")
		p.indent()
		field794 := unwrapped_fields793[0].([]interface{})
		p.pretty_bindings(field794)
		p.newline()
		field795 := unwrapped_fields793[1].(*pb.Formula)
		p.pretty_formula(field795)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat804 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat804 != nil {
		p.write(*flat804)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1359 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1359 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields797 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1359}
		unwrapped_fields798 := fields797
		p.write("[")
		p.indent()
		field799 := unwrapped_fields798[0].([]*pb.Binding)
		for i801, elem800 := range field799 {
			if (i801 > 0) {
				p.newline()
			}
			p.pretty_binding(elem800)
		}
		field802 := unwrapped_fields798[1].([]*pb.Binding)
		if field802 != nil {
			p.newline()
			opt_val803 := field802
			p.pretty_value_bindings(opt_val803)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat809 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat809 != nil {
		p.write(*flat809)
		return nil
	} else {
		_dollar_dollar := msg
		fields805 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields806 := fields805
		field807 := unwrapped_fields806[0].(string)
		p.write(field807)
		p.write("::")
		field808 := unwrapped_fields806[1].(*pb.Type)
		p.pretty_type(field808)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat836 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat836 != nil {
		p.write(*flat836)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1360 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1360 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result834 := _t1360
		if deconstruct_result834 != nil {
			unwrapped835 := deconstruct_result834
			p.pretty_unspecified_type(unwrapped835)
		} else {
			_dollar_dollar := msg
			var _t1361 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1361 = _dollar_dollar.GetStringType()
			}
			deconstruct_result832 := _t1361
			if deconstruct_result832 != nil {
				unwrapped833 := deconstruct_result832
				p.pretty_string_type(unwrapped833)
			} else {
				_dollar_dollar := msg
				var _t1362 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1362 = _dollar_dollar.GetIntType()
				}
				deconstruct_result830 := _t1362
				if deconstruct_result830 != nil {
					unwrapped831 := deconstruct_result830
					p.pretty_int_type(unwrapped831)
				} else {
					_dollar_dollar := msg
					var _t1363 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1363 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result828 := _t1363
					if deconstruct_result828 != nil {
						unwrapped829 := deconstruct_result828
						p.pretty_float_type(unwrapped829)
					} else {
						_dollar_dollar := msg
						var _t1364 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1364 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result826 := _t1364
						if deconstruct_result826 != nil {
							unwrapped827 := deconstruct_result826
							p.pretty_uint128_type(unwrapped827)
						} else {
							_dollar_dollar := msg
							var _t1365 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1365 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result824 := _t1365
							if deconstruct_result824 != nil {
								unwrapped825 := deconstruct_result824
								p.pretty_int128_type(unwrapped825)
							} else {
								_dollar_dollar := msg
								var _t1366 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1366 = _dollar_dollar.GetDateType()
								}
								deconstruct_result822 := _t1366
								if deconstruct_result822 != nil {
									unwrapped823 := deconstruct_result822
									p.pretty_date_type(unwrapped823)
								} else {
									_dollar_dollar := msg
									var _t1367 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1367 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result820 := _t1367
									if deconstruct_result820 != nil {
										unwrapped821 := deconstruct_result820
										p.pretty_datetime_type(unwrapped821)
									} else {
										_dollar_dollar := msg
										var _t1368 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1368 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result818 := _t1368
										if deconstruct_result818 != nil {
											unwrapped819 := deconstruct_result818
											p.pretty_missing_type(unwrapped819)
										} else {
											_dollar_dollar := msg
											var _t1369 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1369 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result816 := _t1369
											if deconstruct_result816 != nil {
												unwrapped817 := deconstruct_result816
												p.pretty_decimal_type(unwrapped817)
											} else {
												_dollar_dollar := msg
												var _t1370 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1370 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result814 := _t1370
												if deconstruct_result814 != nil {
													unwrapped815 := deconstruct_result814
													p.pretty_boolean_type(unwrapped815)
												} else {
													_dollar_dollar := msg
													var _t1371 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1371 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result812 := _t1371
													if deconstruct_result812 != nil {
														unwrapped813 := deconstruct_result812
														p.pretty_int32_type(unwrapped813)
													} else {
														_dollar_dollar := msg
														var _t1372 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1372 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result810 := _t1372
														if deconstruct_result810 != nil {
															unwrapped811 := deconstruct_result810
															p.pretty_float32_type(unwrapped811)
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
	fields837 := msg
	_ = fields837
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields838 := msg
	_ = fields838
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields839 := msg
	_ = fields839
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields840 := msg
	_ = fields840
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields841 := msg
	_ = fields841
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields842 := msg
	_ = fields842
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields843 := msg
	_ = fields843
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields844 := msg
	_ = fields844
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields845 := msg
	_ = fields845
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat850 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat850 != nil {
		p.write(*flat850)
		return nil
	} else {
		_dollar_dollar := msg
		fields846 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields847 := fields846
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field848 := unwrapped_fields847[0].(int64)
		p.write(fmt.Sprintf("%d", field848))
		p.newline()
		field849 := unwrapped_fields847[1].(int64)
		p.write(fmt.Sprintf("%d", field849))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields851 := msg
	_ = fields851
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields852 := msg
	_ = fields852
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields853 := msg
	_ = fields853
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat857 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat857 != nil {
		p.write(*flat857)
		return nil
	} else {
		fields854 := msg
		p.write("|")
		if !(len(fields854) == 0) {
			p.write(" ")
			for i856, elem855 := range fields854 {
				if (i856 > 0) {
					p.newline()
				}
				p.pretty_binding(elem855)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat884 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat884 != nil {
		p.write(*flat884)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1373 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1373 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result882 := _t1373
		if deconstruct_result882 != nil {
			unwrapped883 := deconstruct_result882
			p.pretty_true(unwrapped883)
		} else {
			_dollar_dollar := msg
			var _t1374 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1374 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result880 := _t1374
			if deconstruct_result880 != nil {
				unwrapped881 := deconstruct_result880
				p.pretty_false(unwrapped881)
			} else {
				_dollar_dollar := msg
				var _t1375 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1375 = _dollar_dollar.GetExists()
				}
				deconstruct_result878 := _t1375
				if deconstruct_result878 != nil {
					unwrapped879 := deconstruct_result878
					p.pretty_exists(unwrapped879)
				} else {
					_dollar_dollar := msg
					var _t1376 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1376 = _dollar_dollar.GetReduce()
					}
					deconstruct_result876 := _t1376
					if deconstruct_result876 != nil {
						unwrapped877 := deconstruct_result876
						p.pretty_reduce(unwrapped877)
					} else {
						_dollar_dollar := msg
						var _t1377 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1377 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result874 := _t1377
						if deconstruct_result874 != nil {
							unwrapped875 := deconstruct_result874
							p.pretty_conjunction(unwrapped875)
						} else {
							_dollar_dollar := msg
							var _t1378 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1378 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result872 := _t1378
							if deconstruct_result872 != nil {
								unwrapped873 := deconstruct_result872
								p.pretty_disjunction(unwrapped873)
							} else {
								_dollar_dollar := msg
								var _t1379 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1379 = _dollar_dollar.GetNot()
								}
								deconstruct_result870 := _t1379
								if deconstruct_result870 != nil {
									unwrapped871 := deconstruct_result870
									p.pretty_not(unwrapped871)
								} else {
									_dollar_dollar := msg
									var _t1380 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1380 = _dollar_dollar.GetFfi()
									}
									deconstruct_result868 := _t1380
									if deconstruct_result868 != nil {
										unwrapped869 := deconstruct_result868
										p.pretty_ffi(unwrapped869)
									} else {
										_dollar_dollar := msg
										var _t1381 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1381 = _dollar_dollar.GetAtom()
										}
										deconstruct_result866 := _t1381
										if deconstruct_result866 != nil {
											unwrapped867 := deconstruct_result866
											p.pretty_atom(unwrapped867)
										} else {
											_dollar_dollar := msg
											var _t1382 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1382 = _dollar_dollar.GetPragma()
											}
											deconstruct_result864 := _t1382
											if deconstruct_result864 != nil {
												unwrapped865 := deconstruct_result864
												p.pretty_pragma(unwrapped865)
											} else {
												_dollar_dollar := msg
												var _t1383 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1383 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result862 := _t1383
												if deconstruct_result862 != nil {
													unwrapped863 := deconstruct_result862
													p.pretty_primitive(unwrapped863)
												} else {
													_dollar_dollar := msg
													var _t1384 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1384 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result860 := _t1384
													if deconstruct_result860 != nil {
														unwrapped861 := deconstruct_result860
														p.pretty_rel_atom(unwrapped861)
													} else {
														_dollar_dollar := msg
														var _t1385 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1385 = _dollar_dollar.GetCast()
														}
														deconstruct_result858 := _t1385
														if deconstruct_result858 != nil {
															unwrapped859 := deconstruct_result858
															p.pretty_cast(unwrapped859)
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
	fields885 := msg
	_ = fields885
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields886 := msg
	_ = fields886
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat891 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		_dollar_dollar := msg
		_t1386 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields887 := []interface{}{_t1386, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields888 := fields887
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field889 := unwrapped_fields888[0].([]interface{})
		p.pretty_bindings(field889)
		p.newline()
		field890 := unwrapped_fields888[1].(*pb.Formula)
		p.pretty_formula(field890)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat897 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat897 != nil {
		p.write(*flat897)
		return nil
	} else {
		_dollar_dollar := msg
		fields892 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields893 := fields892
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field894 := unwrapped_fields893[0].(*pb.Abstraction)
		p.pretty_abstraction(field894)
		p.newline()
		field895 := unwrapped_fields893[1].(*pb.Abstraction)
		p.pretty_abstraction(field895)
		p.newline()
		field896 := unwrapped_fields893[2].([]*pb.Term)
		p.pretty_terms(field896)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		fields898 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields898) == 0) {
			p.newline()
			for i900, elem899 := range fields898 {
				if (i900 > 0) {
					p.newline()
				}
				p.pretty_term(elem899)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1387 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1387 = _dollar_dollar.GetVar()
		}
		deconstruct_result904 := _t1387
		if deconstruct_result904 != nil {
			unwrapped905 := deconstruct_result904
			p.pretty_var(unwrapped905)
		} else {
			_dollar_dollar := msg
			var _t1388 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1388 = _dollar_dollar.GetConstant()
			}
			deconstruct_result902 := _t1388
			if deconstruct_result902 != nil {
				unwrapped903 := deconstruct_result902
				p.pretty_constant(unwrapped903)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat909 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat909 != nil {
		p.write(*flat909)
		return nil
	} else {
		_dollar_dollar := msg
		fields907 := _dollar_dollar.GetName()
		unwrapped_fields908 := fields907
		p.write(unwrapped_fields908)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat911 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat911 != nil {
		p.write(*flat911)
		return nil
	} else {
		fields910 := msg
		p.pretty_value(fields910)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat916 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat916 != nil {
		p.write(*flat916)
		return nil
	} else {
		_dollar_dollar := msg
		fields912 := _dollar_dollar.GetArgs()
		unwrapped_fields913 := fields912
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields913) == 0) {
			p.newline()
			for i915, elem914 := range unwrapped_fields913 {
				if (i915 > 0) {
					p.newline()
				}
				p.pretty_formula(elem914)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat921 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat921 != nil {
		p.write(*flat921)
		return nil
	} else {
		_dollar_dollar := msg
		fields917 := _dollar_dollar.GetArgs()
		unwrapped_fields918 := fields917
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields918) == 0) {
			p.newline()
			for i920, elem919 := range unwrapped_fields918 {
				if (i920 > 0) {
					p.newline()
				}
				p.pretty_formula(elem919)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat924 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat924 != nil {
		p.write(*flat924)
		return nil
	} else {
		_dollar_dollar := msg
		fields922 := _dollar_dollar.GetArg()
		unwrapped_fields923 := fields922
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields923)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat930 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat930 != nil {
		p.write(*flat930)
		return nil
	} else {
		_dollar_dollar := msg
		fields925 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields926 := fields925
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field927 := unwrapped_fields926[0].(string)
		p.pretty_name(field927)
		p.newline()
		field928 := unwrapped_fields926[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field928)
		p.newline()
		field929 := unwrapped_fields926[2].([]*pb.Term)
		p.pretty_terms(field929)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat932 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat932 != nil {
		p.write(*flat932)
		return nil
	} else {
		fields931 := msg
		p.write(":")
		p.write(fields931)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat936 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat936 != nil {
		p.write(*flat936)
		return nil
	} else {
		fields933 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields933) == 0) {
			p.newline()
			for i935, elem934 := range fields933 {
				if (i935 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem934)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat943 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_dollar_dollar := msg
		fields937 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields938 := fields937
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field939 := unwrapped_fields938[0].(*pb.RelationId)
		p.pretty_relation_id(field939)
		field940 := unwrapped_fields938[1].([]*pb.Term)
		if !(len(field940) == 0) {
			p.newline()
			for i942, elem941 := range field940 {
				if (i942 > 0) {
					p.newline()
				}
				p.pretty_term(elem941)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat950 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat950 != nil {
		p.write(*flat950)
		return nil
	} else {
		_dollar_dollar := msg
		fields944 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields945 := fields944
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field946 := unwrapped_fields945[0].(string)
		p.pretty_name(field946)
		field947 := unwrapped_fields945[1].([]*pb.Term)
		if !(len(field947) == 0) {
			p.newline()
			for i949, elem948 := range field947 {
				if (i949 > 0) {
					p.newline()
				}
				p.pretty_term(elem948)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat966 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1389 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1389 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result965 := _t1389
		if guard_result965 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1390 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1390 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result964 := _t1390
			if guard_result964 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1391 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1391 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result963 := _t1391
				if guard_result963 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1392 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1392 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result962 := _t1392
					if guard_result962 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1393 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1393 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result961 := _t1393
						if guard_result961 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1394 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1394 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result960 := _t1394
							if guard_result960 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1395 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1395 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result959 := _t1395
								if guard_result959 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1396 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1396 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result958 := _t1396
									if guard_result958 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1397 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1397 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result957 := _t1397
										if guard_result957 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields951 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields952 := fields951
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field953 := unwrapped_fields952[0].(string)
											p.pretty_name(field953)
											field954 := unwrapped_fields952[1].([]*pb.RelTerm)
											if !(len(field954) == 0) {
												p.newline()
												for i956, elem955 := range field954 {
													if (i956 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem955)
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
	flat971 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1398 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1398 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields967 := _t1398
		unwrapped_fields968 := fields967
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field969 := unwrapped_fields968[0].(*pb.Term)
		p.pretty_term(field969)
		p.newline()
		field970 := unwrapped_fields968[1].(*pb.Term)
		p.pretty_term(field970)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1399 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1399 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields972 := _t1399
		unwrapped_fields973 := fields972
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field974 := unwrapped_fields973[0].(*pb.Term)
		p.pretty_term(field974)
		p.newline()
		field975 := unwrapped_fields973[1].(*pb.Term)
		p.pretty_term(field975)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat981 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat981 != nil {
		p.write(*flat981)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1400 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1400 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields977 := _t1400
		unwrapped_fields978 := fields977
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field979 := unwrapped_fields978[0].(*pb.Term)
		p.pretty_term(field979)
		p.newline()
		field980 := unwrapped_fields978[1].(*pb.Term)
		p.pretty_term(field980)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat986 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat986 != nil {
		p.write(*flat986)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1401 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1401 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields982 := _t1401
		unwrapped_fields983 := fields982
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field984 := unwrapped_fields983[0].(*pb.Term)
		p.pretty_term(field984)
		p.newline()
		field985 := unwrapped_fields983[1].(*pb.Term)
		p.pretty_term(field985)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat991 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat991 != nil {
		p.write(*flat991)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1402 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1402 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields987 := _t1402
		unwrapped_fields988 := fields987
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field989 := unwrapped_fields988[0].(*pb.Term)
		p.pretty_term(field989)
		p.newline()
		field990 := unwrapped_fields988[1].(*pb.Term)
		p.pretty_term(field990)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1403 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1403 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields992 := _t1403
		unwrapped_fields993 := fields992
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field994 := unwrapped_fields993[0].(*pb.Term)
		p.pretty_term(field994)
		p.newline()
		field995 := unwrapped_fields993[1].(*pb.Term)
		p.pretty_term(field995)
		p.newline()
		field996 := unwrapped_fields993[2].(*pb.Term)
		p.pretty_term(field996)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1003 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1003 != nil {
		p.write(*flat1003)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1404 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1404 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields998 := _t1404
		unwrapped_fields999 := fields998
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1000 := unwrapped_fields999[0].(*pb.Term)
		p.pretty_term(field1000)
		p.newline()
		field1001 := unwrapped_fields999[1].(*pb.Term)
		p.pretty_term(field1001)
		p.newline()
		field1002 := unwrapped_fields999[2].(*pb.Term)
		p.pretty_term(field1002)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1405 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1405 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1004 := _t1405
		unwrapped_fields1005 := fields1004
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1006 := unwrapped_fields1005[0].(*pb.Term)
		p.pretty_term(field1006)
		p.newline()
		field1007 := unwrapped_fields1005[1].(*pb.Term)
		p.pretty_term(field1007)
		p.newline()
		field1008 := unwrapped_fields1005[2].(*pb.Term)
		p.pretty_term(field1008)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1015 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1015 != nil {
		p.write(*flat1015)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1406 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1406 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1010 := _t1406
		unwrapped_fields1011 := fields1010
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1012 := unwrapped_fields1011[0].(*pb.Term)
		p.pretty_term(field1012)
		p.newline()
		field1013 := unwrapped_fields1011[1].(*pb.Term)
		p.pretty_term(field1013)
		p.newline()
		field1014 := unwrapped_fields1011[2].(*pb.Term)
		p.pretty_term(field1014)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1020 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1020 != nil {
		p.write(*flat1020)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1407 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1407 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1018 := _t1407
		if deconstruct_result1018 != nil {
			unwrapped1019 := deconstruct_result1018
			p.pretty_specialized_value(unwrapped1019)
		} else {
			_dollar_dollar := msg
			var _t1408 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1408 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1016 := _t1408
			if deconstruct_result1016 != nil {
				unwrapped1017 := deconstruct_result1016
				p.pretty_term(unwrapped1017)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1022 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1022 != nil {
		p.write(*flat1022)
		return nil
	} else {
		fields1021 := msg
		p.write("#")
		p.pretty_value(fields1021)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1029 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1029 != nil {
		p.write(*flat1029)
		return nil
	} else {
		_dollar_dollar := msg
		fields1023 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1024 := fields1023
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1025 := unwrapped_fields1024[0].(string)
		p.pretty_name(field1025)
		field1026 := unwrapped_fields1024[1].([]*pb.RelTerm)
		if !(len(field1026) == 0) {
			p.newline()
			for i1028, elem1027 := range field1026 {
				if (i1028 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1027)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1034 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1034 != nil {
		p.write(*flat1034)
		return nil
	} else {
		_dollar_dollar := msg
		fields1030 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1031 := fields1030
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1032 := unwrapped_fields1031[0].(*pb.Term)
		p.pretty_term(field1032)
		p.newline()
		field1033 := unwrapped_fields1031[1].(*pb.Term)
		p.pretty_term(field1033)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1038 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1038 != nil {
		p.write(*flat1038)
		return nil
	} else {
		fields1035 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1035) == 0) {
			p.newline()
			for i1037, elem1036 := range fields1035 {
				if (i1037 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1036)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1045 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1045 != nil {
		p.write(*flat1045)
		return nil
	} else {
		_dollar_dollar := msg
		fields1039 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1040 := fields1039
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1041 := unwrapped_fields1040[0].(string)
		p.pretty_name(field1041)
		field1042 := unwrapped_fields1040[1].([]*pb.Value)
		if !(len(field1042) == 0) {
			p.newline()
			for i1044, elem1043 := range field1042 {
				if (i1044 > 0) {
					p.newline()
				}
				p.pretty_value(elem1043)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1052 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1052 != nil {
		p.write(*flat1052)
		return nil
	} else {
		_dollar_dollar := msg
		fields1046 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1047 := fields1046
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1048 := unwrapped_fields1047[0].([]*pb.RelationId)
		if !(len(field1048) == 0) {
			p.newline()
			for i1050, elem1049 := range field1048 {
				if (i1050 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1049)
			}
		}
		p.newline()
		field1051 := unwrapped_fields1047[1].(*pb.Script)
		p.pretty_script(field1051)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1057 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1057 != nil {
		p.write(*flat1057)
		return nil
	} else {
		_dollar_dollar := msg
		fields1053 := _dollar_dollar.GetConstructs()
		unwrapped_fields1054 := fields1053
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1054) == 0) {
			p.newline()
			for i1056, elem1055 := range unwrapped_fields1054 {
				if (i1056 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1055)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1062 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1409 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1409 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1060 := _t1409
		if deconstruct_result1060 != nil {
			unwrapped1061 := deconstruct_result1060
			p.pretty_loop(unwrapped1061)
		} else {
			_dollar_dollar := msg
			var _t1410 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1410 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1058 := _t1410
			if deconstruct_result1058 != nil {
				unwrapped1059 := deconstruct_result1058
				p.pretty_instruction(unwrapped1059)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1067 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1067 != nil {
		p.write(*flat1067)
		return nil
	} else {
		_dollar_dollar := msg
		fields1063 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1064 := fields1063
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1065 := unwrapped_fields1064[0].([]*pb.Instruction)
		p.pretty_init(field1065)
		p.newline()
		field1066 := unwrapped_fields1064[1].(*pb.Script)
		p.pretty_script(field1066)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1071 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1071 != nil {
		p.write(*flat1071)
		return nil
	} else {
		fields1068 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1068) == 0) {
			p.newline()
			for i1070, elem1069 := range fields1068 {
				if (i1070 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1069)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1082 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1082 != nil {
		p.write(*flat1082)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1411 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1411 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1080 := _t1411
		if deconstruct_result1080 != nil {
			unwrapped1081 := deconstruct_result1080
			p.pretty_assign(unwrapped1081)
		} else {
			_dollar_dollar := msg
			var _t1412 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1412 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1078 := _t1412
			if deconstruct_result1078 != nil {
				unwrapped1079 := deconstruct_result1078
				p.pretty_upsert(unwrapped1079)
			} else {
				_dollar_dollar := msg
				var _t1413 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1413 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1076 := _t1413
				if deconstruct_result1076 != nil {
					unwrapped1077 := deconstruct_result1076
					p.pretty_break(unwrapped1077)
				} else {
					_dollar_dollar := msg
					var _t1414 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1414 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1074 := _t1414
					if deconstruct_result1074 != nil {
						unwrapped1075 := deconstruct_result1074
						p.pretty_monoid_def(unwrapped1075)
					} else {
						_dollar_dollar := msg
						var _t1415 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1415 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1072 := _t1415
						if deconstruct_result1072 != nil {
							unwrapped1073 := deconstruct_result1072
							p.pretty_monus_def(unwrapped1073)
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
	flat1089 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1416 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1416 = _dollar_dollar.GetAttrs()
		}
		fields1083 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1416}
		unwrapped_fields1084 := fields1083
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1085 := unwrapped_fields1084[0].(*pb.RelationId)
		p.pretty_relation_id(field1085)
		p.newline()
		field1086 := unwrapped_fields1084[1].(*pb.Abstraction)
		p.pretty_abstraction(field1086)
		field1087 := unwrapped_fields1084[2].([]*pb.Attribute)
		if field1087 != nil {
			p.newline()
			opt_val1088 := field1087
			p.pretty_attrs(opt_val1088)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1417 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1417 = _dollar_dollar.GetAttrs()
		}
		fields1090 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1417}
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1092 := unwrapped_fields1091[0].(*pb.RelationId)
		p.pretty_relation_id(field1092)
		p.newline()
		field1093 := unwrapped_fields1091[1].([]interface{})
		p.pretty_abstraction_with_arity(field1093)
		field1094 := unwrapped_fields1091[2].([]*pb.Attribute)
		if field1094 != nil {
			p.newline()
			opt_val1095 := field1094
			p.pretty_attrs(opt_val1095)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1101 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1101 != nil {
		p.write(*flat1101)
		return nil
	} else {
		_dollar_dollar := msg
		_t1418 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1097 := []interface{}{_t1418, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1098 := fields1097
		p.write("(")
		p.indent()
		field1099 := unwrapped_fields1098[0].([]interface{})
		p.pretty_bindings(field1099)
		p.newline()
		field1100 := unwrapped_fields1098[1].(*pb.Formula)
		p.pretty_formula(field1100)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1108 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1108 != nil {
		p.write(*flat1108)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1419 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1419 = _dollar_dollar.GetAttrs()
		}
		fields1102 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1419}
		unwrapped_fields1103 := fields1102
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1104 := unwrapped_fields1103[0].(*pb.RelationId)
		p.pretty_relation_id(field1104)
		p.newline()
		field1105 := unwrapped_fields1103[1].(*pb.Abstraction)
		p.pretty_abstraction(field1105)
		field1106 := unwrapped_fields1103[2].([]*pb.Attribute)
		if field1106 != nil {
			p.newline()
			opt_val1107 := field1106
			p.pretty_attrs(opt_val1107)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1116 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1116 != nil {
		p.write(*flat1116)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1420 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1420 = _dollar_dollar.GetAttrs()
		}
		fields1109 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1420}
		unwrapped_fields1110 := fields1109
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1111 := unwrapped_fields1110[0].(*pb.Monoid)
		p.pretty_monoid(field1111)
		p.newline()
		field1112 := unwrapped_fields1110[1].(*pb.RelationId)
		p.pretty_relation_id(field1112)
		p.newline()
		field1113 := unwrapped_fields1110[2].([]interface{})
		p.pretty_abstraction_with_arity(field1113)
		field1114 := unwrapped_fields1110[3].([]*pb.Attribute)
		if field1114 != nil {
			p.newline()
			opt_val1115 := field1114
			p.pretty_attrs(opt_val1115)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1421 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1421 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1123 := _t1421
		if deconstruct_result1123 != nil {
			unwrapped1124 := deconstruct_result1123
			p.pretty_or_monoid(unwrapped1124)
		} else {
			_dollar_dollar := msg
			var _t1422 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1422 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1121 := _t1422
			if deconstruct_result1121 != nil {
				unwrapped1122 := deconstruct_result1121
				p.pretty_min_monoid(unwrapped1122)
			} else {
				_dollar_dollar := msg
				var _t1423 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1423 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1119 := _t1423
				if deconstruct_result1119 != nil {
					unwrapped1120 := deconstruct_result1119
					p.pretty_max_monoid(unwrapped1120)
				} else {
					_dollar_dollar := msg
					var _t1424 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1424 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1117 := _t1424
					if deconstruct_result1117 != nil {
						unwrapped1118 := deconstruct_result1117
						p.pretty_sum_monoid(unwrapped1118)
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
	fields1126 := msg
	_ = fields1126
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1129 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		_dollar_dollar := msg
		fields1127 := _dollar_dollar.GetType()
		unwrapped_fields1128 := fields1127
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1128)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1132 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_dollar_dollar := msg
		fields1130 := _dollar_dollar.GetType()
		unwrapped_fields1131 := fields1130
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1131)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1135 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		fields1133 := _dollar_dollar.GetType()
		unwrapped_fields1134 := fields1133
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1134)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1425 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1425 = _dollar_dollar.GetAttrs()
		}
		fields1136 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1425}
		unwrapped_fields1137 := fields1136
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1138 := unwrapped_fields1137[0].(*pb.Monoid)
		p.pretty_monoid(field1138)
		p.newline()
		field1139 := unwrapped_fields1137[1].(*pb.RelationId)
		p.pretty_relation_id(field1139)
		p.newline()
		field1140 := unwrapped_fields1137[2].([]interface{})
		p.pretty_abstraction_with_arity(field1140)
		field1141 := unwrapped_fields1137[3].([]*pb.Attribute)
		if field1141 != nil {
			p.newline()
			opt_val1142 := field1141
			p.pretty_attrs(opt_val1142)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		_dollar_dollar := msg
		fields1144 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1146 := unwrapped_fields1145[0].(*pb.RelationId)
		p.pretty_relation_id(field1146)
		p.newline()
		field1147 := unwrapped_fields1145[1].(*pb.Abstraction)
		p.pretty_abstraction(field1147)
		p.newline()
		field1148 := unwrapped_fields1145[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1148)
		p.newline()
		field1149 := unwrapped_fields1145[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1149)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1154 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1154 != nil {
		p.write(*flat1154)
		return nil
	} else {
		fields1151 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1151) == 0) {
			p.newline()
			for i1153, elem1152 := range fields1151 {
				if (i1153 > 0) {
					p.newline()
				}
				p.pretty_var(elem1152)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1158 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		fields1155 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1155) == 0) {
			p.newline()
			for i1157, elem1156 := range fields1155 {
				if (i1157 > 0) {
					p.newline()
				}
				p.pretty_var(elem1156)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1426 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1426 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1163 := _t1426
		if deconstruct_result1163 != nil {
			unwrapped1164 := deconstruct_result1163
			p.pretty_edb(unwrapped1164)
		} else {
			_dollar_dollar := msg
			var _t1427 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1427 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1161 := _t1427
			if deconstruct_result1161 != nil {
				unwrapped1162 := deconstruct_result1161
				p.pretty_betree_relation(unwrapped1162)
			} else {
				_dollar_dollar := msg
				var _t1428 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1428 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1159 := _t1428
				if deconstruct_result1159 != nil {
					unwrapped1160 := deconstruct_result1159
					p.pretty_csv_data(unwrapped1160)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1171 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		_dollar_dollar := msg
		fields1166 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.RelationId)
		p.pretty_relation_id(field1168)
		p.newline()
		field1169 := unwrapped_fields1167[1].([]string)
		p.pretty_edb_path(field1169)
		p.newline()
		field1170 := unwrapped_fields1167[2].([]*pb.Type)
		p.pretty_edb_types(field1170)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		fields1172 := msg
		p.write("[")
		p.indent()
		for i1174, elem1173 := range fields1172 {
			if (i1174 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1173))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		fields1176 := msg
		p.write("[")
		p.indent()
		for i1178, elem1177 := range fields1176 {
			if (i1178 > 0) {
				p.newline()
			}
			p.pretty_type(elem1177)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_dollar_dollar := msg
		fields1180 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(*pb.RelationId)
		p.pretty_relation_id(field1182)
		p.newline()
		field1183 := unwrapped_fields1181[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1183)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		_dollar_dollar := msg
		_t1429 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1185 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1429}
		unwrapped_fields1186 := fields1185
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1187 := unwrapped_fields1186[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1187)
		p.newline()
		field1188 := unwrapped_fields1186[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1188)
		p.newline()
		field1189 := unwrapped_fields1186[2].([][]interface{})
		p.pretty_config_dict(field1189)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		fields1191 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1191) == 0) {
			p.newline()
			for i1193, elem1192 := range fields1191 {
				if (i1193 > 0) {
					p.newline()
				}
				p.pretty_type(elem1192)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		fields1195 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1195) == 0) {
			p.newline()
			for i1197, elem1196 := range fields1195 {
				if (i1197 > 0) {
					p.newline()
				}
				p.pretty_type(elem1196)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		_dollar_dollar := msg
		fields1199 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1201 := unwrapped_fields1200[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1201)
		p.newline()
		field1202 := unwrapped_fields1200[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1202)
		p.newline()
		field1203 := unwrapped_fields1200[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1203)
		p.newline()
		field1204 := unwrapped_fields1200[3].(string)
		p.pretty_csv_asof(field1204)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1212 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1212 != nil {
		p.write(*flat1212)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1430 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1430 = _dollar_dollar.GetPaths()
		}
		var _t1431 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1431 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1206 := []interface{}{_t1430, _t1431}
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1208 := unwrapped_fields1207[0].([]string)
		if field1208 != nil {
			p.newline()
			opt_val1209 := field1208
			p.pretty_csv_locator_paths(opt_val1209)
		}
		field1210 := unwrapped_fields1207[1].(*string)
		if field1210 != nil {
			p.newline()
			opt_val1211 := *field1210
			p.pretty_csv_locator_inline_data(opt_val1211)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1216 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1216 != nil {
		p.write(*flat1216)
		return nil
	} else {
		fields1213 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1213) == 0) {
			p.newline()
			for i1215, elem1214 := range fields1213 {
				if (i1215 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1214))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1218 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1218 != nil {
		p.write(*flat1218)
		return nil
	} else {
		fields1217 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1217))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		_t1432 := p.deconstruct_csv_config(_dollar_dollar)
		fields1219 := _t1432
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1220)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1225 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1225 != nil {
		p.write(*flat1225)
		return nil
	} else {
		fields1222 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1222) == 0) {
			p.newline()
			for i1224, elem1223 := range fields1222 {
				if (i1224 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1223)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1433 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1433 = _dollar_dollar.GetTargetId()
		}
		fields1226 := []interface{}{_dollar_dollar.GetColumnPath(), _t1433, _dollar_dollar.GetTypes()}
		unwrapped_fields1227 := fields1226
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1228 := unwrapped_fields1227[0].([]string)
		p.pretty_gnf_column_path(field1228)
		field1229 := unwrapped_fields1227[1].(*pb.RelationId)
		if field1229 != nil {
			p.newline()
			opt_val1230 := field1229
			p.pretty_relation_id(opt_val1230)
		}
		p.newline()
		p.write("[")
		field1231 := unwrapped_fields1227[2].([]*pb.Type)
		for i1233, elem1232 := range field1231 {
			if (i1233 > 0) {
				p.newline()
			}
			p.pretty_type(elem1232)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1241 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1241 != nil {
		p.write(*flat1241)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1434 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1434 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1239 := _t1434
		if deconstruct_result1239 != nil {
			unwrapped1240 := *deconstruct_result1239
			p.write(p.formatStringValue(unwrapped1240))
		} else {
			_dollar_dollar := msg
			var _t1435 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1435 = _dollar_dollar
			}
			deconstruct_result1235 := _t1435
			if deconstruct_result1235 != nil {
				unwrapped1236 := deconstruct_result1235
				p.write("[")
				p.indent()
				for i1238, elem1237 := range unwrapped1236 {
					if (i1238 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1237))
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
	flat1243 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		fields1242 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1242))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		_dollar_dollar := msg
		fields1244 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1245)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1251 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		_dollar_dollar := msg
		fields1247 := _dollar_dollar.GetRelations()
		unwrapped_fields1248 := fields1247
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1248) == 0) {
			p.newline()
			for i1250, elem1249 := range unwrapped_fields1248 {
				if (i1250 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1249)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		_dollar_dollar := msg
		fields1252 := _dollar_dollar.GetMappings()
		unwrapped_fields1253 := fields1252
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1253) == 0) {
			p.newline()
			for i1255, elem1254 := range unwrapped_fields1253 {
				if (i1255 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1254)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		_dollar_dollar := msg
		fields1257 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1258 := fields1257
		field1259 := unwrapped_fields1258[0].([]string)
		p.pretty_edb_path(field1259)
		p.write(" ")
		field1260 := unwrapped_fields1258[1].(*pb.RelationId)
		p.pretty_relation_id(field1260)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1265 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		fields1262 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1262) == 0) {
			p.newline()
			for i1264, elem1263 := range fields1262 {
				if (i1264 > 0) {
					p.newline()
				}
				p.pretty_read(elem1263)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1276 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1276 != nil {
		p.write(*flat1276)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1436 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1436 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1274 := _t1436
		if deconstruct_result1274 != nil {
			unwrapped1275 := deconstruct_result1274
			p.pretty_demand(unwrapped1275)
		} else {
			_dollar_dollar := msg
			var _t1437 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1437 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1272 := _t1437
			if deconstruct_result1272 != nil {
				unwrapped1273 := deconstruct_result1272
				p.pretty_output(unwrapped1273)
			} else {
				_dollar_dollar := msg
				var _t1438 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1438 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1270 := _t1438
				if deconstruct_result1270 != nil {
					unwrapped1271 := deconstruct_result1270
					p.pretty_what_if(unwrapped1271)
				} else {
					_dollar_dollar := msg
					var _t1439 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1439 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1268 := _t1439
					if deconstruct_result1268 != nil {
						unwrapped1269 := deconstruct_result1268
						p.pretty_abort(unwrapped1269)
					} else {
						_dollar_dollar := msg
						var _t1440 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1440 = _dollar_dollar.GetExport()
						}
						deconstruct_result1266 := _t1440
						if deconstruct_result1266 != nil {
							unwrapped1267 := deconstruct_result1266
							p.pretty_export(unwrapped1267)
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
	flat1279 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1279 != nil {
		p.write(*flat1279)
		return nil
	} else {
		_dollar_dollar := msg
		fields1277 := _dollar_dollar.GetRelationId()
		unwrapped_fields1278 := fields1277
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1278)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		_dollar_dollar := msg
		fields1280 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1281 := fields1280
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1282 := unwrapped_fields1281[0].(string)
		p.pretty_name(field1282)
		p.newline()
		field1283 := unwrapped_fields1281[1].(*pb.RelationId)
		p.pretty_relation_id(field1283)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		fields1285 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].(string)
		p.pretty_name(field1287)
		p.newline()
		field1288 := unwrapped_fields1286[1].(*pb.Epoch)
		p.pretty_epoch(field1288)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1295 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1295 != nil {
		p.write(*flat1295)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1441 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1441 = ptr(_dollar_dollar.GetName())
		}
		fields1290 := []interface{}{_t1441, _dollar_dollar.GetRelationId()}
		unwrapped_fields1291 := fields1290
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1292 := unwrapped_fields1291[0].(*string)
		if field1292 != nil {
			p.newline()
			opt_val1293 := *field1292
			p.pretty_name(opt_val1293)
		}
		p.newline()
		field1294 := unwrapped_fields1291[1].(*pb.RelationId)
		p.pretty_relation_id(field1294)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1298 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1298 != nil {
		p.write(*flat1298)
		return nil
	} else {
		_dollar_dollar := msg
		fields1296 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1297 := fields1296
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1297)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1309 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1309 != nil {
		p.write(*flat1309)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1442 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1442 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1304 := _t1442
		if deconstruct_result1304 != nil {
			unwrapped1305 := deconstruct_result1304
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1306 := unwrapped1305[0].(string)
			p.pretty_export_csv_path(field1306)
			p.newline()
			field1307 := unwrapped1305[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1307)
			p.newline()
			field1308 := unwrapped1305[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1308)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1443 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1444 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1443 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1444}
			}
			deconstruct_result1299 := _t1443
			if deconstruct_result1299 != nil {
				unwrapped1300 := deconstruct_result1299
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1301 := unwrapped1300[0].(string)
				p.pretty_export_csv_path(field1301)
				p.newline()
				field1302 := unwrapped1300[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1302)
				p.newline()
				field1303 := unwrapped1300[2].([][]interface{})
				p.pretty_config_dict(field1303)
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
	flat1311 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		fields1310 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1310))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1318 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1318 != nil {
		p.write(*flat1318)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1445 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1445 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1314 := _t1445
		if deconstruct_result1314 != nil {
			unwrapped1315 := deconstruct_result1314
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1315) == 0) {
				p.newline()
				for i1317, elem1316 := range unwrapped1315 {
					if (i1317 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1316)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1446 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1446 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1312 := _t1446
			if deconstruct_result1312 != nil {
				unwrapped1313 := deconstruct_result1312
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1313)
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
	flat1323 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1323 != nil {
		p.write(*flat1323)
		return nil
	} else {
		_dollar_dollar := msg
		fields1319 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1320 := fields1319
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1321 := unwrapped_fields1320[0].(string)
		p.write(p.formatStringValue(field1321))
		p.newline()
		field1322 := unwrapped_fields1320[1].(*pb.RelationId)
		p.pretty_relation_id(field1322)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1327 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1327 != nil {
		p.write(*flat1327)
		return nil
	} else {
		fields1324 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1324) == 0) {
			p.newline()
			for i1326, elem1325 := range fields1324 {
				if (i1326 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1325)
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
		_t1485 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1485)
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
