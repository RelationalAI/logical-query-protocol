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
	_t1459 := &pb.Value{}
	_t1459.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1459
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1460 := &pb.Value{}
	_t1460.Value = &pb.Value_IntValue{IntValue: v}
	return _t1460
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1461 := &pb.Value{}
	_t1461.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1461
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1462 := &pb.Value{}
	_t1462.Value = &pb.Value_StringValue{StringValue: v}
	return _t1462
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1463 := &pb.Value{}
	_t1463.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1463
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1464 := &pb.Value{}
	_t1464.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1464
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1465 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1465})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1466 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1466})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1467 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1467})
			}
		}
	}
	_t1468 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1468})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1469 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1469})
	_t1470 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1470})
	if msg.GetNewLine() != "" {
		_t1471 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1471})
	}
	_t1472 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1472})
	_t1473 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1473})
	_t1474 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1474})
	if msg.GetComment() != "" {
		_t1475 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1475})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1476 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1476})
	}
	_t1477 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1477})
	_t1478 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1478})
	_t1479 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1479})
	if msg.GetPartitionSizeMb() != 0 {
		_t1480 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1480})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1481 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1481})
	_t1482 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1482})
	_t1483 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1483})
	_t1484 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1484})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1485 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1485})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1486 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1486})
		}
	}
	_t1487 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1487})
	_t1488 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1488})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1489 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1489})
	}
	if msg.Compression != nil {
		_t1490 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1490})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1491 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1491})
	}
	if msg.SyntaxMissingString != nil {
		_t1492 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1492})
	}
	if msg.SyntaxDelim != nil {
		_t1493 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1493})
	}
	if msg.SyntaxQuotechar != nil {
		_t1494 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1494})
	}
	if msg.SyntaxEscapechar != nil {
		_t1495 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1495})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1496 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1496
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
	flat678 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat678 != nil {
		p.write(*flat678)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1338 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1338 = _dollar_dollar.GetConfigure()
		}
		var _t1339 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1339 = _dollar_dollar.GetSync()
		}
		fields669 := []interface{}{_t1338, _t1339, _dollar_dollar.GetEpochs()}
		unwrapped_fields670 := fields669
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field671 := unwrapped_fields670[0].(*pb.Configure)
		if field671 != nil {
			p.newline()
			opt_val672 := field671
			p.pretty_configure(opt_val672)
		}
		field673 := unwrapped_fields670[1].(*pb.Sync)
		if field673 != nil {
			p.newline()
			opt_val674 := field673
			p.pretty_sync(opt_val674)
		}
		field675 := unwrapped_fields670[2].([]*pb.Epoch)
		if !(len(field675) == 0) {
			p.newline()
			for i677, elem676 := range field675 {
				if (i677 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem676)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat681 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat681 != nil {
		p.write(*flat681)
		return nil
	} else {
		_dollar_dollar := msg
		_t1340 := p.deconstruct_configure(_dollar_dollar)
		fields679 := _t1340
		unwrapped_fields680 := fields679
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields680)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat685 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat685 != nil {
		p.write(*flat685)
		return nil
	} else {
		fields682 := msg
		p.write("{")
		p.indent()
		if !(len(fields682) == 0) {
			p.newline()
			for i684, elem683 := range fields682 {
				if (i684 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem683)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat690 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat690 != nil {
		p.write(*flat690)
		return nil
	} else {
		_dollar_dollar := msg
		fields686 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields687 := fields686
		p.write(":")
		field688 := unwrapped_fields687[0].(string)
		p.write(field688)
		p.write(" ")
		field689 := unwrapped_fields687[1].(*pb.Value)
		p.pretty_value(field689)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat716 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat716 != nil {
		p.write(*flat716)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1341 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1341 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result714 := _t1341
		if deconstruct_result714 != nil {
			unwrapped715 := deconstruct_result714
			p.pretty_date(unwrapped715)
		} else {
			_dollar_dollar := msg
			var _t1342 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1342 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result712 := _t1342
			if deconstruct_result712 != nil {
				unwrapped713 := deconstruct_result712
				p.pretty_datetime(unwrapped713)
			} else {
				_dollar_dollar := msg
				var _t1343 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1343 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result710 := _t1343
				if deconstruct_result710 != nil {
					unwrapped711 := *deconstruct_result710
					p.write(p.formatStringValue(unwrapped711))
				} else {
					_dollar_dollar := msg
					var _t1344 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t1344 = ptr(_dollar_dollar.GetIntValue())
					}
					deconstruct_result708 := _t1344
					if deconstruct_result708 != nil {
						unwrapped709 := *deconstruct_result708
						p.write(fmt.Sprintf("%d", unwrapped709))
					} else {
						_dollar_dollar := msg
						var _t1345 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t1345 = ptr(_dollar_dollar.GetFloatValue())
						}
						deconstruct_result706 := _t1345
						if deconstruct_result706 != nil {
							unwrapped707 := *deconstruct_result706
							p.write(formatFloat64(unwrapped707))
						} else {
							_dollar_dollar := msg
							var _t1346 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t1346 = _dollar_dollar.GetUint128Value()
							}
							deconstruct_result704 := _t1346
							if deconstruct_result704 != nil {
								unwrapped705 := deconstruct_result704
								p.write(p.formatUint128(unwrapped705))
							} else {
								_dollar_dollar := msg
								var _t1347 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t1347 = _dollar_dollar.GetInt128Value()
								}
								deconstruct_result702 := _t1347
								if deconstruct_result702 != nil {
									unwrapped703 := deconstruct_result702
									p.write(p.formatInt128(unwrapped703))
								} else {
									_dollar_dollar := msg
									var _t1348 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t1348 = _dollar_dollar.GetDecimalValue()
									}
									deconstruct_result700 := _t1348
									if deconstruct_result700 != nil {
										unwrapped701 := deconstruct_result700
										p.write(p.formatDecimal(unwrapped701))
									} else {
										_dollar_dollar := msg
										var _t1349 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t1349 = ptr(_dollar_dollar.GetBooleanValue())
										}
										deconstruct_result698 := _t1349
										if deconstruct_result698 != nil {
											unwrapped699 := *deconstruct_result698
											p.pretty_boolean_value(unwrapped699)
										} else {
											_dollar_dollar := msg
											var _t1350 *int32
											if hasProtoField(_dollar_dollar, "int32_value") {
												_t1350 = ptr(_dollar_dollar.GetInt32Value())
											}
											deconstruct_result696 := _t1350
											if deconstruct_result696 != nil {
												unwrapped697 := *deconstruct_result696
												p.write(fmt.Sprintf("%di32", unwrapped697))
											} else {
												_dollar_dollar := msg
												var _t1351 *float32
												if hasProtoField(_dollar_dollar, "float32_value") {
													_t1351 = ptr(_dollar_dollar.GetFloat32Value())
												}
												deconstruct_result694 := _t1351
												if deconstruct_result694 != nil {
													unwrapped695 := *deconstruct_result694
													p.write(fmt.Sprintf("%sf32", strconv.FormatFloat(float64(unwrapped695), 'g', -1, 32)))
												} else {
													_dollar_dollar := msg
													var _t1352 *uint32
													if hasProtoField(_dollar_dollar, "uint32_value") {
														_t1352 = ptr(_dollar_dollar.GetUint32Value())
													}
													deconstruct_result692 := _t1352
													if deconstruct_result692 != nil {
														unwrapped693 := *deconstruct_result692
														p.write(fmt.Sprintf("%du32", unwrapped693))
													} else {
														fields691 := msg
														_ = fields691
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
	flat722 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		_dollar_dollar := msg
		fields717 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields718 := fields717
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field719 := unwrapped_fields718[0].(int64)
		p.write(fmt.Sprintf("%d", field719))
		p.newline()
		field720 := unwrapped_fields718[1].(int64)
		p.write(fmt.Sprintf("%d", field720))
		p.newline()
		field721 := unwrapped_fields718[2].(int64)
		p.write(fmt.Sprintf("%d", field721))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat733 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat733 != nil {
		p.write(*flat733)
		return nil
	} else {
		_dollar_dollar := msg
		fields723 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields724 := fields723
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field725 := unwrapped_fields724[0].(int64)
		p.write(fmt.Sprintf("%d", field725))
		p.newline()
		field726 := unwrapped_fields724[1].(int64)
		p.write(fmt.Sprintf("%d", field726))
		p.newline()
		field727 := unwrapped_fields724[2].(int64)
		p.write(fmt.Sprintf("%d", field727))
		p.newline()
		field728 := unwrapped_fields724[3].(int64)
		p.write(fmt.Sprintf("%d", field728))
		p.newline()
		field729 := unwrapped_fields724[4].(int64)
		p.write(fmt.Sprintf("%d", field729))
		p.newline()
		field730 := unwrapped_fields724[5].(int64)
		p.write(fmt.Sprintf("%d", field730))
		field731 := unwrapped_fields724[6].(*int64)
		if field731 != nil {
			p.newline()
			opt_val732 := *field731
			p.write(fmt.Sprintf("%d", opt_val732))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1353 []interface{}
	if _dollar_dollar {
		_t1353 = []interface{}{}
	}
	deconstruct_result736 := _t1353
	if deconstruct_result736 != nil {
		unwrapped737 := deconstruct_result736
		_ = unwrapped737
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1354 []interface{}
		if !(_dollar_dollar) {
			_t1354 = []interface{}{}
		}
		deconstruct_result734 := _t1354
		if deconstruct_result734 != nil {
			unwrapped735 := deconstruct_result734
			_ = unwrapped735
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat742 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat742 != nil {
		p.write(*flat742)
		return nil
	} else {
		_dollar_dollar := msg
		fields738 := _dollar_dollar.GetFragments()
		unwrapped_fields739 := fields738
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields739) == 0) {
			p.newline()
			for i741, elem740 := range unwrapped_fields739 {
				if (i741 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem740)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat745 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat745 != nil {
		p.write(*flat745)
		return nil
	} else {
		_dollar_dollar := msg
		fields743 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields744 := fields743
		p.write(":")
		p.write(unwrapped_fields744)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat752 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat752 != nil {
		p.write(*flat752)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1355 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1355 = _dollar_dollar.GetWrites()
		}
		var _t1356 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1356 = _dollar_dollar.GetReads()
		}
		fields746 := []interface{}{_t1355, _t1356}
		unwrapped_fields747 := fields746
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field748 := unwrapped_fields747[0].([]*pb.Write)
		if field748 != nil {
			p.newline()
			opt_val749 := field748
			p.pretty_epoch_writes(opt_val749)
		}
		field750 := unwrapped_fields747[1].([]*pb.Read)
		if field750 != nil {
			p.newline()
			opt_val751 := field750
			p.pretty_epoch_reads(opt_val751)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat756 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat756 != nil {
		p.write(*flat756)
		return nil
	} else {
		fields753 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields753) == 0) {
			p.newline()
			for i755, elem754 := range fields753 {
				if (i755 > 0) {
					p.newline()
				}
				p.pretty_write(elem754)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1357 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1357 = _dollar_dollar.GetDefine()
		}
		deconstruct_result763 := _t1357
		if deconstruct_result763 != nil {
			unwrapped764 := deconstruct_result763
			p.pretty_define(unwrapped764)
		} else {
			_dollar_dollar := msg
			var _t1358 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1358 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result761 := _t1358
			if deconstruct_result761 != nil {
				unwrapped762 := deconstruct_result761
				p.pretty_undefine(unwrapped762)
			} else {
				_dollar_dollar := msg
				var _t1359 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1359 = _dollar_dollar.GetContext()
				}
				deconstruct_result759 := _t1359
				if deconstruct_result759 != nil {
					unwrapped760 := deconstruct_result759
					p.pretty_context(unwrapped760)
				} else {
					_dollar_dollar := msg
					var _t1360 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1360 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result757 := _t1360
					if deconstruct_result757 != nil {
						unwrapped758 := deconstruct_result757
						p.pretty_snapshot(unwrapped758)
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
	flat768 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat768 != nil {
		p.write(*flat768)
		return nil
	} else {
		_dollar_dollar := msg
		fields766 := _dollar_dollar.GetFragment()
		unwrapped_fields767 := fields766
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields767)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat775 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat775 != nil {
		p.write(*flat775)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields769 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields770 := fields769
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field771 := unwrapped_fields770[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field771)
		field772 := unwrapped_fields770[1].([]*pb.Declaration)
		if !(len(field772) == 0) {
			p.newline()
			for i774, elem773 := range field772 {
				if (i774 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem773)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat777 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat777 != nil {
		p.write(*flat777)
		return nil
	} else {
		fields776 := msg
		p.pretty_fragment_id(fields776)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat786 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat786 != nil {
		p.write(*flat786)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1361 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1361 = _dollar_dollar.GetDef()
		}
		deconstruct_result784 := _t1361
		if deconstruct_result784 != nil {
			unwrapped785 := deconstruct_result784
			p.pretty_def(unwrapped785)
		} else {
			_dollar_dollar := msg
			var _t1362 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1362 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result782 := _t1362
			if deconstruct_result782 != nil {
				unwrapped783 := deconstruct_result782
				p.pretty_algorithm(unwrapped783)
			} else {
				_dollar_dollar := msg
				var _t1363 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1363 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result780 := _t1363
				if deconstruct_result780 != nil {
					unwrapped781 := deconstruct_result780
					p.pretty_constraint(unwrapped781)
				} else {
					_dollar_dollar := msg
					var _t1364 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1364 = _dollar_dollar.GetData()
					}
					deconstruct_result778 := _t1364
					if deconstruct_result778 != nil {
						unwrapped779 := deconstruct_result778
						p.pretty_data(unwrapped779)
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
	flat793 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat793 != nil {
		p.write(*flat793)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1365 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1365 = _dollar_dollar.GetAttrs()
		}
		fields787 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1365}
		unwrapped_fields788 := fields787
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field789 := unwrapped_fields788[0].(*pb.RelationId)
		p.pretty_relation_id(field789)
		p.newline()
		field790 := unwrapped_fields788[1].(*pb.Abstraction)
		p.pretty_abstraction(field790)
		field791 := unwrapped_fields788[2].([]*pb.Attribute)
		if field791 != nil {
			p.newline()
			opt_val792 := field791
			p.pretty_attrs(opt_val792)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat798 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat798 != nil {
		p.write(*flat798)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1366 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1367 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1366 = ptr(_t1367)
		}
		deconstruct_result796 := _t1366
		if deconstruct_result796 != nil {
			unwrapped797 := *deconstruct_result796
			p.write(":")
			p.write(unwrapped797)
		} else {
			_dollar_dollar := msg
			_t1368 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result794 := _t1368
			if deconstruct_result794 != nil {
				unwrapped795 := deconstruct_result794
				p.write(p.formatUint128(unwrapped795))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat803 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat803 != nil {
		p.write(*flat803)
		return nil
	} else {
		_dollar_dollar := msg
		_t1369 := p.deconstruct_bindings(_dollar_dollar)
		fields799 := []interface{}{_t1369, _dollar_dollar.GetValue()}
		unwrapped_fields800 := fields799
		p.write("(")
		p.indent()
		field801 := unwrapped_fields800[0].([]interface{})
		p.pretty_bindings(field801)
		p.newline()
		field802 := unwrapped_fields800[1].(*pb.Formula)
		p.pretty_formula(field802)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat811 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat811 != nil {
		p.write(*flat811)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1370 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1370 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields804 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1370}
		unwrapped_fields805 := fields804
		p.write("[")
		p.indent()
		field806 := unwrapped_fields805[0].([]*pb.Binding)
		for i808, elem807 := range field806 {
			if (i808 > 0) {
				p.newline()
			}
			p.pretty_binding(elem807)
		}
		field809 := unwrapped_fields805[1].([]*pb.Binding)
		if field809 != nil {
			p.newline()
			opt_val810 := field809
			p.pretty_value_bindings(opt_val810)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat816 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat816 != nil {
		p.write(*flat816)
		return nil
	} else {
		_dollar_dollar := msg
		fields812 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields813 := fields812
		field814 := unwrapped_fields813[0].(string)
		p.write(field814)
		p.write("::")
		field815 := unwrapped_fields813[1].(*pb.Type)
		p.pretty_type(field815)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat845 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat845 != nil {
		p.write(*flat845)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1371 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1371 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result843 := _t1371
		if deconstruct_result843 != nil {
			unwrapped844 := deconstruct_result843
			p.pretty_unspecified_type(unwrapped844)
		} else {
			_dollar_dollar := msg
			var _t1372 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1372 = _dollar_dollar.GetStringType()
			}
			deconstruct_result841 := _t1372
			if deconstruct_result841 != nil {
				unwrapped842 := deconstruct_result841
				p.pretty_string_type(unwrapped842)
			} else {
				_dollar_dollar := msg
				var _t1373 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1373 = _dollar_dollar.GetIntType()
				}
				deconstruct_result839 := _t1373
				if deconstruct_result839 != nil {
					unwrapped840 := deconstruct_result839
					p.pretty_int_type(unwrapped840)
				} else {
					_dollar_dollar := msg
					var _t1374 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1374 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result837 := _t1374
					if deconstruct_result837 != nil {
						unwrapped838 := deconstruct_result837
						p.pretty_float_type(unwrapped838)
					} else {
						_dollar_dollar := msg
						var _t1375 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1375 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result835 := _t1375
						if deconstruct_result835 != nil {
							unwrapped836 := deconstruct_result835
							p.pretty_uint128_type(unwrapped836)
						} else {
							_dollar_dollar := msg
							var _t1376 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1376 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result833 := _t1376
							if deconstruct_result833 != nil {
								unwrapped834 := deconstruct_result833
								p.pretty_int128_type(unwrapped834)
							} else {
								_dollar_dollar := msg
								var _t1377 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1377 = _dollar_dollar.GetDateType()
								}
								deconstruct_result831 := _t1377
								if deconstruct_result831 != nil {
									unwrapped832 := deconstruct_result831
									p.pretty_date_type(unwrapped832)
								} else {
									_dollar_dollar := msg
									var _t1378 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1378 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result829 := _t1378
									if deconstruct_result829 != nil {
										unwrapped830 := deconstruct_result829
										p.pretty_datetime_type(unwrapped830)
									} else {
										_dollar_dollar := msg
										var _t1379 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1379 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result827 := _t1379
										if deconstruct_result827 != nil {
											unwrapped828 := deconstruct_result827
											p.pretty_missing_type(unwrapped828)
										} else {
											_dollar_dollar := msg
											var _t1380 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1380 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result825 := _t1380
											if deconstruct_result825 != nil {
												unwrapped826 := deconstruct_result825
												p.pretty_decimal_type(unwrapped826)
											} else {
												_dollar_dollar := msg
												var _t1381 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1381 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result823 := _t1381
												if deconstruct_result823 != nil {
													unwrapped824 := deconstruct_result823
													p.pretty_boolean_type(unwrapped824)
												} else {
													_dollar_dollar := msg
													var _t1382 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1382 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result821 := _t1382
													if deconstruct_result821 != nil {
														unwrapped822 := deconstruct_result821
														p.pretty_int32_type(unwrapped822)
													} else {
														_dollar_dollar := msg
														var _t1383 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1383 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result819 := _t1383
														if deconstruct_result819 != nil {
															unwrapped820 := deconstruct_result819
															p.pretty_float32_type(unwrapped820)
														} else {
															_dollar_dollar := msg
															var _t1384 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1384 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result817 := _t1384
															if deconstruct_result817 != nil {
																unwrapped818 := deconstruct_result817
																p.pretty_uint32_type(unwrapped818)
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
	fields846 := msg
	_ = fields846
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields847 := msg
	_ = fields847
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields848 := msg
	_ = fields848
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields849 := msg
	_ = fields849
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields850 := msg
	_ = fields850
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields851 := msg
	_ = fields851
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields852 := msg
	_ = fields852
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields853 := msg
	_ = fields853
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields854 := msg
	_ = fields854
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat859 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat859 != nil {
		p.write(*flat859)
		return nil
	} else {
		_dollar_dollar := msg
		fields855 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields856 := fields855
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field857 := unwrapped_fields856[0].(int64)
		p.write(fmt.Sprintf("%d", field857))
		p.newline()
		field858 := unwrapped_fields856[1].(int64)
		p.write(fmt.Sprintf("%d", field858))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields860 := msg
	_ = fields860
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields861 := msg
	_ = fields861
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields862 := msg
	_ = fields862
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields863 := msg
	_ = fields863
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat867 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat867 != nil {
		p.write(*flat867)
		return nil
	} else {
		fields864 := msg
		p.write("|")
		if !(len(fields864) == 0) {
			p.write(" ")
			for i866, elem865 := range fields864 {
				if (i866 > 0) {
					p.newline()
				}
				p.pretty_binding(elem865)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat894 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1385 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1385 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result892 := _t1385
		if deconstruct_result892 != nil {
			unwrapped893 := deconstruct_result892
			p.pretty_true(unwrapped893)
		} else {
			_dollar_dollar := msg
			var _t1386 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1386 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result890 := _t1386
			if deconstruct_result890 != nil {
				unwrapped891 := deconstruct_result890
				p.pretty_false(unwrapped891)
			} else {
				_dollar_dollar := msg
				var _t1387 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1387 = _dollar_dollar.GetExists()
				}
				deconstruct_result888 := _t1387
				if deconstruct_result888 != nil {
					unwrapped889 := deconstruct_result888
					p.pretty_exists(unwrapped889)
				} else {
					_dollar_dollar := msg
					var _t1388 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1388 = _dollar_dollar.GetReduce()
					}
					deconstruct_result886 := _t1388
					if deconstruct_result886 != nil {
						unwrapped887 := deconstruct_result886
						p.pretty_reduce(unwrapped887)
					} else {
						_dollar_dollar := msg
						var _t1389 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1389 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result884 := _t1389
						if deconstruct_result884 != nil {
							unwrapped885 := deconstruct_result884
							p.pretty_conjunction(unwrapped885)
						} else {
							_dollar_dollar := msg
							var _t1390 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1390 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result882 := _t1390
							if deconstruct_result882 != nil {
								unwrapped883 := deconstruct_result882
								p.pretty_disjunction(unwrapped883)
							} else {
								_dollar_dollar := msg
								var _t1391 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1391 = _dollar_dollar.GetNot()
								}
								deconstruct_result880 := _t1391
								if deconstruct_result880 != nil {
									unwrapped881 := deconstruct_result880
									p.pretty_not(unwrapped881)
								} else {
									_dollar_dollar := msg
									var _t1392 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1392 = _dollar_dollar.GetFfi()
									}
									deconstruct_result878 := _t1392
									if deconstruct_result878 != nil {
										unwrapped879 := deconstruct_result878
										p.pretty_ffi(unwrapped879)
									} else {
										_dollar_dollar := msg
										var _t1393 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1393 = _dollar_dollar.GetAtom()
										}
										deconstruct_result876 := _t1393
										if deconstruct_result876 != nil {
											unwrapped877 := deconstruct_result876
											p.pretty_atom(unwrapped877)
										} else {
											_dollar_dollar := msg
											var _t1394 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1394 = _dollar_dollar.GetPragma()
											}
											deconstruct_result874 := _t1394
											if deconstruct_result874 != nil {
												unwrapped875 := deconstruct_result874
												p.pretty_pragma(unwrapped875)
											} else {
												_dollar_dollar := msg
												var _t1395 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1395 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result872 := _t1395
												if deconstruct_result872 != nil {
													unwrapped873 := deconstruct_result872
													p.pretty_primitive(unwrapped873)
												} else {
													_dollar_dollar := msg
													var _t1396 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1396 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result870 := _t1396
													if deconstruct_result870 != nil {
														unwrapped871 := deconstruct_result870
														p.pretty_rel_atom(unwrapped871)
													} else {
														_dollar_dollar := msg
														var _t1397 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1397 = _dollar_dollar.GetCast()
														}
														deconstruct_result868 := _t1397
														if deconstruct_result868 != nil {
															unwrapped869 := deconstruct_result868
															p.pretty_cast(unwrapped869)
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
	fields895 := msg
	_ = fields895
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields896 := msg
	_ = fields896
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		_dollar_dollar := msg
		_t1398 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields897 := []interface{}{_t1398, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields898 := fields897
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field899 := unwrapped_fields898[0].([]interface{})
		p.pretty_bindings(field899)
		p.newline()
		field900 := unwrapped_fields898[1].(*pb.Formula)
		p.pretty_formula(field900)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat907 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat907 != nil {
		p.write(*flat907)
		return nil
	} else {
		_dollar_dollar := msg
		fields902 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields903 := fields902
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field904 := unwrapped_fields903[0].(*pb.Abstraction)
		p.pretty_abstraction(field904)
		p.newline()
		field905 := unwrapped_fields903[1].(*pb.Abstraction)
		p.pretty_abstraction(field905)
		p.newline()
		field906 := unwrapped_fields903[2].([]*pb.Term)
		p.pretty_terms(field906)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat911 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat911 != nil {
		p.write(*flat911)
		return nil
	} else {
		fields908 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields908) == 0) {
			p.newline()
			for i910, elem909 := range fields908 {
				if (i910 > 0) {
					p.newline()
				}
				p.pretty_term(elem909)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat916 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat916 != nil {
		p.write(*flat916)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1399 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1399 = _dollar_dollar.GetVar()
		}
		deconstruct_result914 := _t1399
		if deconstruct_result914 != nil {
			unwrapped915 := deconstruct_result914
			p.pretty_var(unwrapped915)
		} else {
			_dollar_dollar := msg
			var _t1400 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1400 = _dollar_dollar.GetConstant()
			}
			deconstruct_result912 := _t1400
			if deconstruct_result912 != nil {
				unwrapped913 := deconstruct_result912
				p.pretty_constant(unwrapped913)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat919 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat919 != nil {
		p.write(*flat919)
		return nil
	} else {
		_dollar_dollar := msg
		fields917 := _dollar_dollar.GetName()
		unwrapped_fields918 := fields917
		p.write(unwrapped_fields918)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat921 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat921 != nil {
		p.write(*flat921)
		return nil
	} else {
		fields920 := msg
		p.pretty_value(fields920)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat926 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat926 != nil {
		p.write(*flat926)
		return nil
	} else {
		_dollar_dollar := msg
		fields922 := _dollar_dollar.GetArgs()
		unwrapped_fields923 := fields922
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields923) == 0) {
			p.newline()
			for i925, elem924 := range unwrapped_fields923 {
				if (i925 > 0) {
					p.newline()
				}
				p.pretty_formula(elem924)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat931 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat931 != nil {
		p.write(*flat931)
		return nil
	} else {
		_dollar_dollar := msg
		fields927 := _dollar_dollar.GetArgs()
		unwrapped_fields928 := fields927
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields928) == 0) {
			p.newline()
			for i930, elem929 := range unwrapped_fields928 {
				if (i930 > 0) {
					p.newline()
				}
				p.pretty_formula(elem929)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat934 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat934 != nil {
		p.write(*flat934)
		return nil
	} else {
		_dollar_dollar := msg
		fields932 := _dollar_dollar.GetArg()
		unwrapped_fields933 := fields932
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields933)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat940 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat940 != nil {
		p.write(*flat940)
		return nil
	} else {
		_dollar_dollar := msg
		fields935 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields936 := fields935
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field937 := unwrapped_fields936[0].(string)
		p.pretty_name(field937)
		p.newline()
		field938 := unwrapped_fields936[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field938)
		p.newline()
		field939 := unwrapped_fields936[2].([]*pb.Term)
		p.pretty_terms(field939)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat942 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat942 != nil {
		p.write(*flat942)
		return nil
	} else {
		fields941 := msg
		p.write(":")
		p.write(fields941)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		fields943 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields943) == 0) {
			p.newline()
			for i945, elem944 := range fields943 {
				if (i945 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem944)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat953 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat953 != nil {
		p.write(*flat953)
		return nil
	} else {
		_dollar_dollar := msg
		fields947 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields948 := fields947
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field949 := unwrapped_fields948[0].(*pb.RelationId)
		p.pretty_relation_id(field949)
		field950 := unwrapped_fields948[1].([]*pb.Term)
		if !(len(field950) == 0) {
			p.newline()
			for i952, elem951 := range field950 {
				if (i952 > 0) {
					p.newline()
				}
				p.pretty_term(elem951)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat960 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat960 != nil {
		p.write(*flat960)
		return nil
	} else {
		_dollar_dollar := msg
		fields954 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields955 := fields954
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field956 := unwrapped_fields955[0].(string)
		p.pretty_name(field956)
		field957 := unwrapped_fields955[1].([]*pb.Term)
		if !(len(field957) == 0) {
			p.newline()
			for i959, elem958 := range field957 {
				if (i959 > 0) {
					p.newline()
				}
				p.pretty_term(elem958)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1401 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1401 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result975 := _t1401
		if guard_result975 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1402 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1402 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result974 := _t1402
			if guard_result974 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1403 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1403 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result973 := _t1403
				if guard_result973 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1404 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1404 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result972 := _t1404
					if guard_result972 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1405 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1405 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result971 := _t1405
						if guard_result971 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1406 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1406 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result970 := _t1406
							if guard_result970 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1407 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1407 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result969 := _t1407
								if guard_result969 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1408 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1408 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result968 := _t1408
									if guard_result968 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1409 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1409 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result967 := _t1409
										if guard_result967 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields961 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields962 := fields961
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field963 := unwrapped_fields962[0].(string)
											p.pretty_name(field963)
											field964 := unwrapped_fields962[1].([]*pb.RelTerm)
											if !(len(field964) == 0) {
												p.newline()
												for i966, elem965 := range field964 {
													if (i966 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem965)
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
	flat981 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat981 != nil {
		p.write(*flat981)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1410 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1410 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields977 := _t1410
		unwrapped_fields978 := fields977
		p.write("(")
		p.write("=")
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

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat986 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat986 != nil {
		p.write(*flat986)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1411 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1411 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields982 := _t1411
		unwrapped_fields983 := fields982
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat991 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat991 != nil {
		p.write(*flat991)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1412 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1412 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields987 := _t1412
		unwrapped_fields988 := fields987
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1413 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1413 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields992 := _t1413
		unwrapped_fields993 := fields992
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field994 := unwrapped_fields993[0].(*pb.Term)
		p.pretty_term(field994)
		p.newline()
		field995 := unwrapped_fields993[1].(*pb.Term)
		p.pretty_term(field995)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1414 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1414 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields997 := _t1414
		unwrapped_fields998 := fields997
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field999 := unwrapped_fields998[0].(*pb.Term)
		p.pretty_term(field999)
		p.newline()
		field1000 := unwrapped_fields998[1].(*pb.Term)
		p.pretty_term(field1000)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1415 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1415 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1002 := _t1415
		unwrapped_fields1003 := fields1002
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1004 := unwrapped_fields1003[0].(*pb.Term)
		p.pretty_term(field1004)
		p.newline()
		field1005 := unwrapped_fields1003[1].(*pb.Term)
		p.pretty_term(field1005)
		p.newline()
		field1006 := unwrapped_fields1003[2].(*pb.Term)
		p.pretty_term(field1006)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1013 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1416 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1416 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1008 := _t1416
		unwrapped_fields1009 := fields1008
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1010 := unwrapped_fields1009[0].(*pb.Term)
		p.pretty_term(field1010)
		p.newline()
		field1011 := unwrapped_fields1009[1].(*pb.Term)
		p.pretty_term(field1011)
		p.newline()
		field1012 := unwrapped_fields1009[2].(*pb.Term)
		p.pretty_term(field1012)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1019 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1019 != nil {
		p.write(*flat1019)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1417 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1417 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1014 := _t1417
		unwrapped_fields1015 := fields1014
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1016 := unwrapped_fields1015[0].(*pb.Term)
		p.pretty_term(field1016)
		p.newline()
		field1017 := unwrapped_fields1015[1].(*pb.Term)
		p.pretty_term(field1017)
		p.newline()
		field1018 := unwrapped_fields1015[2].(*pb.Term)
		p.pretty_term(field1018)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1418 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1418 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1020 := _t1418
		unwrapped_fields1021 := fields1020
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1022 := unwrapped_fields1021[0].(*pb.Term)
		p.pretty_term(field1022)
		p.newline()
		field1023 := unwrapped_fields1021[1].(*pb.Term)
		p.pretty_term(field1023)
		p.newline()
		field1024 := unwrapped_fields1021[2].(*pb.Term)
		p.pretty_term(field1024)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1419 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1419 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1028 := _t1419
		if deconstruct_result1028 != nil {
			unwrapped1029 := deconstruct_result1028
			p.pretty_specialized_value(unwrapped1029)
		} else {
			_dollar_dollar := msg
			var _t1420 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1420 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1026 := _t1420
			if deconstruct_result1026 != nil {
				unwrapped1027 := deconstruct_result1026
				p.pretty_term(unwrapped1027)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		fields1031 := msg
		p.write("#")
		p.pretty_value(fields1031)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1039 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1039 != nil {
		p.write(*flat1039)
		return nil
	} else {
		_dollar_dollar := msg
		fields1033 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1034 := fields1033
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1035 := unwrapped_fields1034[0].(string)
		p.pretty_name(field1035)
		field1036 := unwrapped_fields1034[1].([]*pb.RelTerm)
		if !(len(field1036) == 0) {
			p.newline()
			for i1038, elem1037 := range field1036 {
				if (i1038 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1037)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1044 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1044 != nil {
		p.write(*flat1044)
		return nil
	} else {
		_dollar_dollar := msg
		fields1040 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1041 := fields1040
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1042 := unwrapped_fields1041[0].(*pb.Term)
		p.pretty_term(field1042)
		p.newline()
		field1043 := unwrapped_fields1041[1].(*pb.Term)
		p.pretty_term(field1043)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1048 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1048 != nil {
		p.write(*flat1048)
		return nil
	} else {
		fields1045 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1045) == 0) {
			p.newline()
			for i1047, elem1046 := range fields1045 {
				if (i1047 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1046)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1055 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1055 != nil {
		p.write(*flat1055)
		return nil
	} else {
		_dollar_dollar := msg
		fields1049 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1050 := fields1049
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1051 := unwrapped_fields1050[0].(string)
		p.pretty_name(field1051)
		field1052 := unwrapped_fields1050[1].([]*pb.Value)
		if !(len(field1052) == 0) {
			p.newline()
			for i1054, elem1053 := range field1052 {
				if (i1054 > 0) {
					p.newline()
				}
				p.pretty_value(elem1053)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1062 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_dollar_dollar := msg
		fields1056 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1057 := fields1056
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1058 := unwrapped_fields1057[0].([]*pb.RelationId)
		if !(len(field1058) == 0) {
			p.newline()
			for i1060, elem1059 := range field1058 {
				if (i1060 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1059)
			}
		}
		p.newline()
		field1061 := unwrapped_fields1057[1].(*pb.Script)
		p.pretty_script(field1061)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1067 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1067 != nil {
		p.write(*flat1067)
		return nil
	} else {
		_dollar_dollar := msg
		fields1063 := _dollar_dollar.GetConstructs()
		unwrapped_fields1064 := fields1063
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1064) == 0) {
			p.newline()
			for i1066, elem1065 := range unwrapped_fields1064 {
				if (i1066 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1065)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1072 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1072 != nil {
		p.write(*flat1072)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1421 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1421 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1070 := _t1421
		if deconstruct_result1070 != nil {
			unwrapped1071 := deconstruct_result1070
			p.pretty_loop(unwrapped1071)
		} else {
			_dollar_dollar := msg
			var _t1422 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1422 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1068 := _t1422
			if deconstruct_result1068 != nil {
				unwrapped1069 := deconstruct_result1068
				p.pretty_instruction(unwrapped1069)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1077 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1077 != nil {
		p.write(*flat1077)
		return nil
	} else {
		_dollar_dollar := msg
		fields1073 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1074 := fields1073
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1075 := unwrapped_fields1074[0].([]*pb.Instruction)
		p.pretty_init(field1075)
		p.newline()
		field1076 := unwrapped_fields1074[1].(*pb.Script)
		p.pretty_script(field1076)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1081 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		fields1078 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1078) == 0) {
			p.newline()
			for i1080, elem1079 := range fields1078 {
				if (i1080 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1079)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1423 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1423 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1090 := _t1423
		if deconstruct_result1090 != nil {
			unwrapped1091 := deconstruct_result1090
			p.pretty_assign(unwrapped1091)
		} else {
			_dollar_dollar := msg
			var _t1424 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1424 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1088 := _t1424
			if deconstruct_result1088 != nil {
				unwrapped1089 := deconstruct_result1088
				p.pretty_upsert(unwrapped1089)
			} else {
				_dollar_dollar := msg
				var _t1425 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1425 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1086 := _t1425
				if deconstruct_result1086 != nil {
					unwrapped1087 := deconstruct_result1086
					p.pretty_break(unwrapped1087)
				} else {
					_dollar_dollar := msg
					var _t1426 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1426 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1084 := _t1426
					if deconstruct_result1084 != nil {
						unwrapped1085 := deconstruct_result1084
						p.pretty_monoid_def(unwrapped1085)
					} else {
						_dollar_dollar := msg
						var _t1427 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1427 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1082 := _t1427
						if deconstruct_result1082 != nil {
							unwrapped1083 := deconstruct_result1082
							p.pretty_monus_def(unwrapped1083)
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
	flat1099 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1099 != nil {
		p.write(*flat1099)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1428 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1428 = _dollar_dollar.GetAttrs()
		}
		fields1093 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1428}
		unwrapped_fields1094 := fields1093
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1095 := unwrapped_fields1094[0].(*pb.RelationId)
		p.pretty_relation_id(field1095)
		p.newline()
		field1096 := unwrapped_fields1094[1].(*pb.Abstraction)
		p.pretty_abstraction(field1096)
		field1097 := unwrapped_fields1094[2].([]*pb.Attribute)
		if field1097 != nil {
			p.newline()
			opt_val1098 := field1097
			p.pretty_attrs(opt_val1098)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1106 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1106 != nil {
		p.write(*flat1106)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1429 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1429 = _dollar_dollar.GetAttrs()
		}
		fields1100 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1429}
		unwrapped_fields1101 := fields1100
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1102 := unwrapped_fields1101[0].(*pb.RelationId)
		p.pretty_relation_id(field1102)
		p.newline()
		field1103 := unwrapped_fields1101[1].([]interface{})
		p.pretty_abstraction_with_arity(field1103)
		field1104 := unwrapped_fields1101[2].([]*pb.Attribute)
		if field1104 != nil {
			p.newline()
			opt_val1105 := field1104
			p.pretty_attrs(opt_val1105)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1111 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1111 != nil {
		p.write(*flat1111)
		return nil
	} else {
		_dollar_dollar := msg
		_t1430 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1107 := []interface{}{_t1430, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1108 := fields1107
		p.write("(")
		p.indent()
		field1109 := unwrapped_fields1108[0].([]interface{})
		p.pretty_bindings(field1109)
		p.newline()
		field1110 := unwrapped_fields1108[1].(*pb.Formula)
		p.pretty_formula(field1110)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1431 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1431 = _dollar_dollar.GetAttrs()
		}
		fields1112 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1431}
		unwrapped_fields1113 := fields1112
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1114 := unwrapped_fields1113[0].(*pb.RelationId)
		p.pretty_relation_id(field1114)
		p.newline()
		field1115 := unwrapped_fields1113[1].(*pb.Abstraction)
		p.pretty_abstraction(field1115)
		field1116 := unwrapped_fields1113[2].([]*pb.Attribute)
		if field1116 != nil {
			p.newline()
			opt_val1117 := field1116
			p.pretty_attrs(opt_val1117)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1126 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1126 != nil {
		p.write(*flat1126)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1432 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1432 = _dollar_dollar.GetAttrs()
		}
		fields1119 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1432}
		unwrapped_fields1120 := fields1119
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1121 := unwrapped_fields1120[0].(*pb.Monoid)
		p.pretty_monoid(field1121)
		p.newline()
		field1122 := unwrapped_fields1120[1].(*pb.RelationId)
		p.pretty_relation_id(field1122)
		p.newline()
		field1123 := unwrapped_fields1120[2].([]interface{})
		p.pretty_abstraction_with_arity(field1123)
		field1124 := unwrapped_fields1120[3].([]*pb.Attribute)
		if field1124 != nil {
			p.newline()
			opt_val1125 := field1124
			p.pretty_attrs(opt_val1125)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1135 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1433 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1433 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1133 := _t1433
		if deconstruct_result1133 != nil {
			unwrapped1134 := deconstruct_result1133
			p.pretty_or_monoid(unwrapped1134)
		} else {
			_dollar_dollar := msg
			var _t1434 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1434 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1131 := _t1434
			if deconstruct_result1131 != nil {
				unwrapped1132 := deconstruct_result1131
				p.pretty_min_monoid(unwrapped1132)
			} else {
				_dollar_dollar := msg
				var _t1435 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1435 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1129 := _t1435
				if deconstruct_result1129 != nil {
					unwrapped1130 := deconstruct_result1129
					p.pretty_max_monoid(unwrapped1130)
				} else {
					_dollar_dollar := msg
					var _t1436 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1436 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1127 := _t1436
					if deconstruct_result1127 != nil {
						unwrapped1128 := deconstruct_result1127
						p.pretty_sum_monoid(unwrapped1128)
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
	fields1136 := msg
	_ = fields1136
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_dollar_dollar := msg
		fields1137 := _dollar_dollar.GetType()
		unwrapped_fields1138 := fields1137
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1138)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1142 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1142 != nil {
		p.write(*flat1142)
		return nil
	} else {
		_dollar_dollar := msg
		fields1140 := _dollar_dollar.GetType()
		unwrapped_fields1141 := fields1140
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1141)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		fields1143 := _dollar_dollar.GetType()
		unwrapped_fields1144 := fields1143
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1144)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1437 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1437 = _dollar_dollar.GetAttrs()
		}
		fields1146 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1437}
		unwrapped_fields1147 := fields1146
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1148 := unwrapped_fields1147[0].(*pb.Monoid)
		p.pretty_monoid(field1148)
		p.newline()
		field1149 := unwrapped_fields1147[1].(*pb.RelationId)
		p.pretty_relation_id(field1149)
		p.newline()
		field1150 := unwrapped_fields1147[2].([]interface{})
		p.pretty_abstraction_with_arity(field1150)
		field1151 := unwrapped_fields1147[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		fields1154 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1156 := unwrapped_fields1155[0].(*pb.RelationId)
		p.pretty_relation_id(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].(*pb.Abstraction)
		p.pretty_abstraction(field1157)
		p.newline()
		field1158 := unwrapped_fields1155[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1158)
		p.newline()
		field1159 := unwrapped_fields1155[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1159)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1164 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		fields1161 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1161) == 0) {
			p.newline()
			for i1163, elem1162 := range fields1161 {
				if (i1163 > 0) {
					p.newline()
				}
				p.pretty_var(elem1162)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		fields1165 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1165) == 0) {
			p.newline()
			for i1167, elem1166 := range fields1165 {
				if (i1167 > 0) {
					p.newline()
				}
				p.pretty_var(elem1166)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1438 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1438 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1173 := _t1438
		if deconstruct_result1173 != nil {
			unwrapped1174 := deconstruct_result1173
			p.pretty_edb(unwrapped1174)
		} else {
			_dollar_dollar := msg
			var _t1439 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1439 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1171 := _t1439
			if deconstruct_result1171 != nil {
				unwrapped1172 := deconstruct_result1171
				p.pretty_betree_relation(unwrapped1172)
			} else {
				_dollar_dollar := msg
				var _t1440 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1440 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1169 := _t1440
				if deconstruct_result1169 != nil {
					unwrapped1170 := deconstruct_result1169
					p.pretty_csv_data(unwrapped1170)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1181 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		_dollar_dollar := msg
		fields1176 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1177 := fields1176
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1178 := unwrapped_fields1177[0].(*pb.RelationId)
		p.pretty_relation_id(field1178)
		p.newline()
		field1179 := unwrapped_fields1177[1].([]string)
		p.pretty_edb_path(field1179)
		p.newline()
		field1180 := unwrapped_fields1177[2].([]*pb.Type)
		p.pretty_edb_types(field1180)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1185 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1185 != nil {
		p.write(*flat1185)
		return nil
	} else {
		fields1182 := msg
		p.write("[")
		p.indent()
		for i1184, elem1183 := range fields1182 {
			if (i1184 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1183))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		fields1186 := msg
		p.write("[")
		p.indent()
		for i1188, elem1187 := range fields1186 {
			if (i1188 > 0) {
				p.newline()
			}
			p.pretty_type(elem1187)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		_dollar_dollar := msg
		fields1190 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1192 := unwrapped_fields1191[0].(*pb.RelationId)
		p.pretty_relation_id(field1192)
		p.newline()
		field1193 := unwrapped_fields1191[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1193)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		_t1441 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1195 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1441}
		unwrapped_fields1196 := fields1195
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1197 := unwrapped_fields1196[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1197)
		p.newline()
		field1198 := unwrapped_fields1196[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1198)
		p.newline()
		field1199 := unwrapped_fields1196[2].([][]interface{})
		p.pretty_config_dict(field1199)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1204 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		fields1201 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1201) == 0) {
			p.newline()
			for i1203, elem1202 := range fields1201 {
				if (i1203 > 0) {
					p.newline()
				}
				p.pretty_type(elem1202)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1208 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1208 != nil {
		p.write(*flat1208)
		return nil
	} else {
		fields1205 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1205) == 0) {
			p.newline()
			for i1207, elem1206 := range fields1205 {
				if (i1207 > 0) {
					p.newline()
				}
				p.pretty_type(elem1206)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		fields1209 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1210 := fields1209
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1211 := unwrapped_fields1210[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1211)
		p.newline()
		field1212 := unwrapped_fields1210[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1212)
		p.newline()
		field1213 := unwrapped_fields1210[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1213)
		p.newline()
		field1214 := unwrapped_fields1210[3].(string)
		p.pretty_csv_asof(field1214)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1222 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1222 != nil {
		p.write(*flat1222)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1442 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1442 = _dollar_dollar.GetPaths()
		}
		var _t1443 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1443 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1216 := []interface{}{_t1442, _t1443}
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1218 := unwrapped_fields1217[0].([]string)
		if field1218 != nil {
			p.newline()
			opt_val1219 := field1218
			p.pretty_csv_locator_paths(opt_val1219)
		}
		field1220 := unwrapped_fields1217[1].(*string)
		if field1220 != nil {
			p.newline()
			opt_val1221 := *field1220
			p.pretty_csv_locator_inline_data(opt_val1221)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		fields1223 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1223) == 0) {
			p.newline()
			for i1225, elem1224 := range fields1223 {
				if (i1225 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1224))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1228 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1228 != nil {
		p.write(*flat1228)
		return nil
	} else {
		fields1227 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1227))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_dollar_dollar := msg
		_t1444 := p.deconstruct_csv_config(_dollar_dollar)
		fields1229 := _t1444
		unwrapped_fields1230 := fields1229
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1230)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		fields1232 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1232) == 0) {
			p.newline()
			for i1234, elem1233 := range fields1232 {
				if (i1234 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1233)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1445 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1445 = _dollar_dollar.GetTargetId()
		}
		fields1236 := []interface{}{_dollar_dollar.GetColumnPath(), _t1445, _dollar_dollar.GetTypes()}
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1238 := unwrapped_fields1237[0].([]string)
		p.pretty_gnf_column_path(field1238)
		field1239 := unwrapped_fields1237[1].(*pb.RelationId)
		if field1239 != nil {
			p.newline()
			opt_val1240 := field1239
			p.pretty_relation_id(opt_val1240)
		}
		p.newline()
		p.write("[")
		field1241 := unwrapped_fields1237[2].([]*pb.Type)
		for i1243, elem1242 := range field1241 {
			if (i1243 > 0) {
				p.newline()
			}
			p.pretty_type(elem1242)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1251 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1446 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1446 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1249 := _t1446
		if deconstruct_result1249 != nil {
			unwrapped1250 := *deconstruct_result1249
			p.write(p.formatStringValue(unwrapped1250))
		} else {
			_dollar_dollar := msg
			var _t1447 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1447 = _dollar_dollar
			}
			deconstruct_result1245 := _t1447
			if deconstruct_result1245 != nil {
				unwrapped1246 := deconstruct_result1245
				p.write("[")
				p.indent()
				for i1248, elem1247 := range unwrapped1246 {
					if (i1248 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1247))
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
	flat1253 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		fields1252 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1252))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		_dollar_dollar := msg
		fields1254 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1255)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		_dollar_dollar := msg
		fields1257 := _dollar_dollar.GetRelations()
		unwrapped_fields1258 := fields1257
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1258) == 0) {
			p.newline()
			for i1260, elem1259 := range unwrapped_fields1258 {
				if (i1260 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1259)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		_dollar_dollar := msg
		fields1262 := _dollar_dollar.GetMappings()
		unwrapped_fields1263 := fields1262
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1263) == 0) {
			p.newline()
			for i1265, elem1264 := range unwrapped_fields1263 {
				if (i1265 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1264)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1271 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1271 != nil {
		p.write(*flat1271)
		return nil
	} else {
		_dollar_dollar := msg
		fields1267 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1268 := fields1267
		field1269 := unwrapped_fields1268[0].([]string)
		p.pretty_edb_path(field1269)
		p.write(" ")
		field1270 := unwrapped_fields1268[1].(*pb.RelationId)
		p.pretty_relation_id(field1270)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1275 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1275 != nil {
		p.write(*flat1275)
		return nil
	} else {
		fields1272 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1272) == 0) {
			p.newline()
			for i1274, elem1273 := range fields1272 {
				if (i1274 > 0) {
					p.newline()
				}
				p.pretty_read(elem1273)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1448 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1448 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1284 := _t1448
		if deconstruct_result1284 != nil {
			unwrapped1285 := deconstruct_result1284
			p.pretty_demand(unwrapped1285)
		} else {
			_dollar_dollar := msg
			var _t1449 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1449 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1282 := _t1449
			if deconstruct_result1282 != nil {
				unwrapped1283 := deconstruct_result1282
				p.pretty_output(unwrapped1283)
			} else {
				_dollar_dollar := msg
				var _t1450 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1450 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1280 := _t1450
				if deconstruct_result1280 != nil {
					unwrapped1281 := deconstruct_result1280
					p.pretty_what_if(unwrapped1281)
				} else {
					_dollar_dollar := msg
					var _t1451 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1451 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1278 := _t1451
					if deconstruct_result1278 != nil {
						unwrapped1279 := deconstruct_result1278
						p.pretty_abort(unwrapped1279)
					} else {
						_dollar_dollar := msg
						var _t1452 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1452 = _dollar_dollar.GetExport()
						}
						deconstruct_result1276 := _t1452
						if deconstruct_result1276 != nil {
							unwrapped1277 := deconstruct_result1276
							p.pretty_export(unwrapped1277)
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
	flat1289 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		fields1287 := _dollar_dollar.GetRelationId()
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1288)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1294 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1294 != nil {
		p.write(*flat1294)
		return nil
	} else {
		_dollar_dollar := msg
		fields1290 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1291 := fields1290
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1292 := unwrapped_fields1291[0].(string)
		p.pretty_name(field1292)
		p.newline()
		field1293 := unwrapped_fields1291[1].(*pb.RelationId)
		p.pretty_relation_id(field1293)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1299 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1299 != nil {
		p.write(*flat1299)
		return nil
	} else {
		_dollar_dollar := msg
		fields1295 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1296 := fields1295
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1297 := unwrapped_fields1296[0].(string)
		p.pretty_name(field1297)
		p.newline()
		field1298 := unwrapped_fields1296[1].(*pb.Epoch)
		p.pretty_epoch(field1298)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1305 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1305 != nil {
		p.write(*flat1305)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1453 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1453 = ptr(_dollar_dollar.GetName())
		}
		fields1300 := []interface{}{_t1453, _dollar_dollar.GetRelationId()}
		unwrapped_fields1301 := fields1300
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1302 := unwrapped_fields1301[0].(*string)
		if field1302 != nil {
			p.newline()
			opt_val1303 := *field1302
			p.pretty_name(opt_val1303)
		}
		p.newline()
		field1304 := unwrapped_fields1301[1].(*pb.RelationId)
		p.pretty_relation_id(field1304)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1308 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1308 != nil {
		p.write(*flat1308)
		return nil
	} else {
		_dollar_dollar := msg
		fields1306 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1307 := fields1306
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1307)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1319 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1319 != nil {
		p.write(*flat1319)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1454 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1454 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1314 := _t1454
		if deconstruct_result1314 != nil {
			unwrapped1315 := deconstruct_result1314
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1316 := unwrapped1315[0].(string)
			p.pretty_export_csv_path(field1316)
			p.newline()
			field1317 := unwrapped1315[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1317)
			p.newline()
			field1318 := unwrapped1315[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1318)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1455 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1456 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1455 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1456}
			}
			deconstruct_result1309 := _t1455
			if deconstruct_result1309 != nil {
				unwrapped1310 := deconstruct_result1309
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1311 := unwrapped1310[0].(string)
				p.pretty_export_csv_path(field1311)
				p.newline()
				field1312 := unwrapped1310[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1312)
				p.newline()
				field1313 := unwrapped1310[2].([][]interface{})
				p.pretty_config_dict(field1313)
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
	flat1321 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1321 != nil {
		p.write(*flat1321)
		return nil
	} else {
		fields1320 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1320))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1328 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1328 != nil {
		p.write(*flat1328)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1457 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1457 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1324 := _t1457
		if deconstruct_result1324 != nil {
			unwrapped1325 := deconstruct_result1324
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1325) == 0) {
				p.newline()
				for i1327, elem1326 := range unwrapped1325 {
					if (i1327 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1326)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1458 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1458 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1322 := _t1458
			if deconstruct_result1322 != nil {
				unwrapped1323 := deconstruct_result1322
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1323)
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
	flat1333 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1333 != nil {
		p.write(*flat1333)
		return nil
	} else {
		_dollar_dollar := msg
		fields1329 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1330 := fields1329
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1331 := unwrapped_fields1330[0].(string)
		p.write(p.formatStringValue(field1331))
		p.newline()
		field1332 := unwrapped_fields1330[1].(*pb.RelationId)
		p.pretty_relation_id(field1332)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1337 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
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
				p.pretty_export_csv_column(elem1335)
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
		_t1497 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1497)
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
