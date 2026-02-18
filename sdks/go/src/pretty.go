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
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// PrettyPrinter holds state for pretty printing protobuf messages.
type PrettyPrinter struct {
	w           *bytes.Buffer
	indentLevel int
	atLineStart bool
	debugInfo   map[[2]uint64]string
}

func (p *PrettyPrinter) write(s string) {
	if p.atLineStart && strings.TrimSpace(s) != "" {
		p.w.WriteString(strings.Repeat("  ", p.indentLevel))
		p.atLineStart = false
	}
	p.w.WriteString(s)
}

func (p *PrettyPrinter) newline() {
	p.w.WriteString("\n")
	p.atLineStart = true
}

func (p *PrettyPrinter) indent() {
	p.indentLevel++
}

func (p *PrettyPrinter) dedent() {
	if p.indentLevel > 0 {
		p.indentLevel--
	}
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
func (p *PrettyPrinter) relationIdToString(msg *pb.RelationId) string {
	key := [2]uint64{msg.GetIdLow(), msg.GetIdHigh()}
	if name, ok := p.debugInfo[key]; ok {
		return name
	}
	return ""
}

// relationIdToInt returns a pointer to int64 if the RelationId fits in
// signed 64-bit range, nil otherwise.
func (p *PrettyPrinter) relationIdToInt(msg *pb.RelationId) *int64 {
	if msg.GetIdHigh() == 0 && msg.GetIdLow() <= 0x7FFFFFFFFFFFFFFF {
		v := int64(msg.GetIdLow())
		return &v
	}
	return nil
}

// relationIdToUint128 converts a RelationId to a UInt128Value.
func (p *PrettyPrinter) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
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

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *Parser) _make_value_int32(v int32) *pb.Value {
	_t1844 := &pb.Value{}
	_t1844.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1844
}

func (p *Parser) _make_value_int64(v int64) *pb.Value {
	_t1845 := &pb.Value{}
	_t1845.Value = &pb.Value_IntValue{IntValue: v}
	return _t1845
}

func (p *Parser) _make_value_float64(v float64) *pb.Value {
	_t1846 := &pb.Value{}
	_t1846.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1846
}

func (p *Parser) _make_value_string(v string) *pb.Value {
	_t1847 := &pb.Value{}
	_t1847.Value = &pb.Value_StringValue{StringValue: v}
	return _t1847
}

func (p *Parser) _make_value_boolean(v bool) *pb.Value {
	_t1848 := &pb.Value{}
	_t1848.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1848
}

func (p *Parser) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1849 := &pb.Value{}
	_t1849.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1849
}

func (p *Parser) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1850 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1850})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1851 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1851})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1852 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1852})
			}
		}
	}
	_t1853 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1853})
	return listSort(result)
}

func (p *Parser) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1854 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1854})
	_t1855 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1855})
	if msg.GetNewLine() != "" {
		_t1856 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1856})
	}
	_t1857 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1857})
	_t1858 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1858})
	_t1859 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1859})
	if msg.GetComment() != "" {
		_t1860 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1860})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1861 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1861})
	}
	_t1862 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1862})
	_t1863 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1863})
	_t1864 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1864})
	return listSort(result)
}

func (p *Parser) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1865 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1865})
	_t1866 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1866})
	_t1867 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1867})
	_t1868 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1868})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1869 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1869})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1870 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1870})
		}
	}
	_t1871 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1871})
	_t1872 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1872})
	return listSort(result)
}

func (p *Parser) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1873 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1873})
	}
	if msg.Compression != nil {
		_t1874 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1874})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1875 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1875})
	}
	if msg.SyntaxMissingString != nil {
		_t1876 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1876})
	}
	if msg.SyntaxDelim != nil {
		_t1877 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1877})
	}
	if msg.SyntaxQuotechar != nil {
		_t1878 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1878})
	}
	if msg.SyntaxEscapechar != nil {
		_t1879 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1879})
	}
	return listSort(result)
}

func (p *Parser) deconstruct_relation_id_string(msg *pb.RelationId) *string {
	name := p.relationIdToString(msg)
	var _t1880 interface{}
	if name != "" {
		return ptr(name)
	}
	_ = _t1880
	return nil
}

func (p *Parser) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1881 interface{}
	if name == "" {
		return p.relationIdToUint128(msg)
	}
	_ = _t1881
	return nil
}

func (p *Parser) deconstruct_bindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *Parser) deconstruct_bindings_with_arity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

// --- Pretty-print methods ---

func (p *Parser) pretty_transaction(msg *pb.Transaction) interface{} {
	flat631 := nil
	if flat631 != nil {
		p.write(*flat631)
		return nil
	} else {
		_t1244 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1245 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1245 = _dollar_dollar.GetConfigure()
			}
			var _t1246 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1246 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1245, _t1246, _dollar_dollar.GetEpochs()}
		}
		_t1247 := _t1244(msg)
		fields622 := _t1247
		unwrapped_fields623 := fields622
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field624 := unwrapped_fields623[0].(*pb.Configure)
		if field624 != nil {
			p.newline()
			opt_val625 := field624
			_t1248 := p.pretty_configure(opt_val625)
		}
		field626 := unwrapped_fields623[1].(*pb.Sync)
		if field626 != nil {
			p.newline()
			opt_val627 := field626
			_t1249 := p.pretty_sync(opt_val627)
		}
		field628 := unwrapped_fields623[2].([]*pb.Epoch)
		if !(len(field628) == 0) {
			p.newline()
			for i630, elem629 := range field628 {
				if (i630 > 0) {
					p.newline()
				}
				_t1250 := p.pretty_epoch(elem629)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_configure(msg *pb.Configure) interface{} {
	flat634 := nil
	if flat634 != nil {
		p.write(*flat634)
		return nil
	} else {
		_t1251 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1252 := p.deconstruct_configure(_dollar_dollar)
			return _t1252
		}
		_t1253 := _t1251(msg)
		fields632 := _t1253
		unwrapped_fields633 := fields632
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		_t1254 := p.pretty_config_dict(unwrapped_fields633)
		_ = _t1254
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_config_dict(msg [][]interface{}) interface{} {
	flat638 := nil
	if flat638 != nil {
		p.write(*flat638)
		return nil
	} else {
		fields635 := msg
		p.write("{")
		p.indent()
		if !(len(fields635) == 0) {
			p.newline()
			for i637, elem636 := range fields635 {
				if (i637 > 0) {
					p.newline()
				}
				_t1255 := p.pretty_config_key_value(elem636)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *Parser) pretty_config_key_value(msg []interface{}) interface{} {
	flat643 := nil
	if flat643 != nil {
		p.write(*flat643)
		return nil
	} else {
		_t1256 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1257 := _t1256(msg)
		fields639 := _t1257
		unwrapped_fields640 := fields639
		p.write(":")
		field641 := unwrapped_fields640[0].(string)
		p.write(field641)
		p.write(" ")
		field642 := unwrapped_fields640[1].(*pb.Value)
		_t1258 := p.pretty_value(field642)
	}
	return nil
}

func (p *Parser) pretty_value(msg *pb.Value) interface{} {
	flat663 := nil
	if flat663 != nil {
		p.write(*flat663)
		return nil
	} else {
		_t1259 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1260 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1260 = _dollar_dollar.GetDateValue()
			}
			return _t1260
		}
		_t1261 := _t1259(msg)
		deconstruct_result661 := _t1261
		if deconstruct_result661 != nil {
			unwrapped662 := deconstruct_result661
			_t1262 := p.pretty_date(unwrapped662)
		} else {
			_t1263 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1264 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1264 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1264
			}
			_t1265 := _t1263(msg)
			deconstruct_result659 := _t1265
			if deconstruct_result659 != nil {
				unwrapped660 := deconstruct_result659
				_t1266 := p.pretty_datetime(unwrapped660)
			} else {
				_t1267 := func(_dollar_dollar *pb.Value) *string {
					var _t1268 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1268 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1268
				}
				_t1269 := _t1267(msg)
				deconstruct_result657 := _t1269
				if deconstruct_result657 != nil {
					unwrapped658 := *deconstruct_result657
					p.write(p.formatStringValue(unwrapped658))
				} else {
					_t1270 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1271 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1271 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1271
					}
					_t1272 := _t1270(msg)
					deconstruct_result655 := _t1272
					if deconstruct_result655 != nil {
						unwrapped656 := *deconstruct_result655
						p.write(fmt.Sprintf("%d", unwrapped656))
					} else {
						_t1273 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1274 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1274 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1274
						}
						_t1275 := _t1273(msg)
						deconstruct_result653 := _t1275
						if deconstruct_result653 != nil {
							unwrapped654 := *deconstruct_result653
							p.write(fmt.Sprintf("%g", unwrapped654))
						} else {
							_t1276 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1277 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1277 = _dollar_dollar.GetUint128Value()
								}
								return _t1277
							}
							_t1278 := _t1276(msg)
							deconstruct_result651 := _t1278
							if deconstruct_result651 != nil {
								unwrapped652 := deconstruct_result651
								p.write(p.formatUint128(unwrapped652))
							} else {
								_t1279 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1280 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1280 = _dollar_dollar.GetInt128Value()
									}
									return _t1280
								}
								_t1281 := _t1279(msg)
								deconstruct_result649 := _t1281
								if deconstruct_result649 != nil {
									unwrapped650 := deconstruct_result649
									p.write(p.formatInt128(unwrapped650))
								} else {
									_t1282 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1283 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1283 = _dollar_dollar.GetDecimalValue()
										}
										return _t1283
									}
									_t1284 := _t1282(msg)
									deconstruct_result647 := _t1284
									if deconstruct_result647 != nil {
										unwrapped648 := deconstruct_result647
										p.write(p.formatDecimal(unwrapped648))
									} else {
										_t1285 := func(_dollar_dollar *pb.Value) *bool {
											var _t1286 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1286 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1286
										}
										_t1287 := _t1285(msg)
										deconstruct_result645 := _t1287
										if deconstruct_result645 != nil {
											unwrapped646 := *deconstruct_result645
											_t1288 := p.pretty_boolean_value(unwrapped646)
										} else {
											fields644 := msg
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
	return nil
}

func (p *Parser) pretty_date(msg *pb.DateValue) interface{} {
	flat669 := nil
	if flat669 != nil {
		p.write(*flat669)
		return nil
	} else {
		_t1289 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1290 := _t1289(msg)
		fields664 := _t1290
		unwrapped_fields665 := fields664
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field666 := unwrapped_fields665[0].(int64)
		p.write(fmt.Sprintf("%d", field666))
		p.newline()
		field667 := unwrapped_fields665[1].(int64)
		p.write(fmt.Sprintf("%d", field667))
		p.newline()
		field668 := unwrapped_fields665[2].(int64)
		p.write(fmt.Sprintf("%d", field668))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat680 := nil
	if flat680 != nil {
		p.write(*flat680)
		return nil
	} else {
		_t1291 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1292 := _t1291(msg)
		fields670 := _t1292
		unwrapped_fields671 := fields670
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field672 := unwrapped_fields671[0].(int64)
		p.write(fmt.Sprintf("%d", field672))
		p.newline()
		field673 := unwrapped_fields671[1].(int64)
		p.write(fmt.Sprintf("%d", field673))
		p.newline()
		field674 := unwrapped_fields671[2].(int64)
		p.write(fmt.Sprintf("%d", field674))
		p.newline()
		field675 := unwrapped_fields671[3].(int64)
		p.write(fmt.Sprintf("%d", field675))
		p.newline()
		field676 := unwrapped_fields671[4].(int64)
		p.write(fmt.Sprintf("%d", field676))
		p.newline()
		field677 := unwrapped_fields671[5].(int64)
		p.write(fmt.Sprintf("%d", field677))
		field678 := unwrapped_fields671[6].(*int64)
		if field678 != nil {
			p.newline()
			opt_val679 := *field678
			p.write(fmt.Sprintf("%d", opt_val679))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_boolean_value(msg bool) interface{} {
	_t1293 := func(_dollar_dollar bool) []interface{} {
		var _t1294 interface{}
		if _dollar_dollar {
			_t1294 = []interface{}{}
		}
		return _t1294
	}
	_t1295 := _t1293(msg)
	deconstruct_result683 := _t1295
	if deconstruct_result683 != nil {
		unwrapped684 := deconstruct_result683
		p.write("true")
	} else {
		_t1296 := func(_dollar_dollar bool) []interface{} {
			var _t1297 interface{}
			if !(_dollar_dollar) {
				_t1297 = []interface{}{}
			}
			return _t1297
		}
		_t1298 := _t1296(msg)
		deconstruct_result681 := _t1298
		if deconstruct_result681 != nil {
			unwrapped682 := deconstruct_result681
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *Parser) pretty_sync(msg *pb.Sync) interface{} {
	flat689 := nil
	if flat689 != nil {
		p.write(*flat689)
		return nil
	} else {
		_t1299 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1300 := _t1299(msg)
		fields685 := _t1300
		unwrapped_fields686 := fields685
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields686) == 0) {
			p.newline()
			for i688, elem687 := range unwrapped_fields686 {
				if (i688 > 0) {
					p.newline()
				}
				_t1301 := p.pretty_fragment_id(elem687)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat692 := nil
	if flat692 != nil {
		p.write(*flat692)
		return nil
	} else {
		_t1302 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1303 := _t1302(msg)
		fields690 := _t1303
		unwrapped_fields691 := *fields690
		p.write(":")
		p.write(unwrapped_fields691)
	}
	return nil
}

func (p *Parser) pretty_epoch(msg *pb.Epoch) interface{} {
	flat699 := nil
	if flat699 != nil {
		p.write(*flat699)
		return nil
	} else {
		_t1304 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1305 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1305 = _dollar_dollar.GetWrites()
			}
			var _t1306 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1306 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1305, _t1306}
		}
		_t1307 := _t1304(msg)
		fields693 := _t1307
		unwrapped_fields694 := fields693
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field695 := unwrapped_fields694[0].([]*pb.Write)
		if field695 != nil {
			p.newline()
			opt_val696 := field695
			_t1308 := p.pretty_epoch_writes(opt_val696)
		}
		field697 := unwrapped_fields694[1].([]*pb.Read)
		if field697 != nil {
			p.newline()
			opt_val698 := field697
			_t1309 := p.pretty_epoch_reads(opt_val698)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat703 := nil
	if flat703 != nil {
		p.write(*flat703)
		return nil
	} else {
		fields700 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields700) == 0) {
			p.newline()
			for i702, elem701 := range fields700 {
				if (i702 > 0) {
					p.newline()
				}
				_t1310 := p.pretty_write(elem701)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_write(msg *pb.Write) interface{} {
	flat710 := nil
	if flat710 != nil {
		p.write(*flat710)
		return nil
	} else {
		_t1311 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1312 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1312 = _dollar_dollar.GetDefine()
			}
			return _t1312
		}
		_t1313 := _t1311(msg)
		deconstruct_result708 := _t1313
		if deconstruct_result708 != nil {
			unwrapped709 := deconstruct_result708
			_t1314 := p.pretty_define(unwrapped709)
		} else {
			_t1315 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1316 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1316 = _dollar_dollar.GetUndefine()
				}
				return _t1316
			}
			_t1317 := _t1315(msg)
			deconstruct_result706 := _t1317
			if deconstruct_result706 != nil {
				unwrapped707 := deconstruct_result706
				_t1318 := p.pretty_undefine(unwrapped707)
			} else {
				_t1319 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1320 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1320 = _dollar_dollar.GetContext()
					}
					return _t1320
				}
				_t1321 := _t1319(msg)
				deconstruct_result704 := _t1321
				if deconstruct_result704 != nil {
					unwrapped705 := deconstruct_result704
					_t1322 := p.pretty_context(unwrapped705)
				} else {
					panic(ParseError{msg: "No matching rule for write"})
				}
			}
		}
	}
	return nil
}

func (p *Parser) pretty_define(msg *pb.Define) interface{} {
	flat713 := nil
	if flat713 != nil {
		p.write(*flat713)
		return nil
	} else {
		_t1323 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1324 := _t1323(msg)
		fields711 := _t1324
		unwrapped_fields712 := fields711
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		_t1325 := p.pretty_fragment(unwrapped_fields712)
		_ = _t1325
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_fragment(msg *pb.Fragment) interface{} {
	flat720 := nil
	if flat720 != nil {
		p.write(*flat720)
		return nil
	} else {
		_t1326 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.start_pretty_fragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1327 := _t1326(msg)
		fields714 := _t1327
		unwrapped_fields715 := fields714
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field716 := unwrapped_fields715[0].(*pb.FragmentId)
		_t1328 := p.pretty_new_fragment_id(field716)
		_ = _t1328
		field717 := unwrapped_fields715[1].([]*pb.Declaration)
		if !(len(field717) == 0) {
			p.newline()
			for i719, elem718 := range field717 {
				if (i719 > 0) {
					p.newline()
				}
				_t1329 := p.pretty_declaration(elem718)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat722 := nil
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		fields721 := msg
		_t1330 := p.pretty_fragment_id(fields721)
	}
	return nil
}

func (p *Parser) pretty_declaration(msg *pb.Declaration) interface{} {
	flat731 := nil
	if flat731 != nil {
		p.write(*flat731)
		return nil
	} else {
		_t1331 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1332 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1332 = _dollar_dollar.GetDef()
			}
			return _t1332
		}
		_t1333 := _t1331(msg)
		deconstruct_result729 := _t1333
		if deconstruct_result729 != nil {
			unwrapped730 := deconstruct_result729
			_t1334 := p.pretty_def(unwrapped730)
		} else {
			_t1335 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1336 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1336 = _dollar_dollar.GetAlgorithm()
				}
				return _t1336
			}
			_t1337 := _t1335(msg)
			deconstruct_result727 := _t1337
			if deconstruct_result727 != nil {
				unwrapped728 := deconstruct_result727
				_t1338 := p.pretty_algorithm(unwrapped728)
			} else {
				_t1339 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1340 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1340 = _dollar_dollar.GetConstraint()
					}
					return _t1340
				}
				_t1341 := _t1339(msg)
				deconstruct_result725 := _t1341
				if deconstruct_result725 != nil {
					unwrapped726 := deconstruct_result725
					_t1342 := p.pretty_constraint(unwrapped726)
				} else {
					_t1343 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1344 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1344 = _dollar_dollar.GetData()
						}
						return _t1344
					}
					_t1345 := _t1343(msg)
					deconstruct_result723 := _t1345
					if deconstruct_result723 != nil {
						unwrapped724 := deconstruct_result723
						_t1346 := p.pretty_data(unwrapped724)
					} else {
						panic(ParseError{msg: "No matching rule for declaration"})
					}
				}
			}
		}
	}
	return nil
}

func (p *Parser) pretty_def(msg *pb.Def) interface{} {
	flat738 := nil
	if flat738 != nil {
		p.write(*flat738)
		return nil
	} else {
		_t1347 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1348 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1348 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1348}
		}
		_t1349 := _t1347(msg)
		fields732 := _t1349
		unwrapped_fields733 := fields732
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field734 := unwrapped_fields733[0].(*pb.RelationId)
		_t1350 := p.pretty_relation_id(field734)
		_ = _t1350
		p.newline()
		field735 := unwrapped_fields733[1].(*pb.Abstraction)
		_t1351 := p.pretty_abstraction(field735)
		_ = _t1351
		field736 := unwrapped_fields733[2].([]*pb.Attribute)
		if field736 != nil {
			p.newline()
			opt_val737 := field736
			_t1352 := p.pretty_attrs(opt_val737)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat743 := nil
	if flat743 != nil {
		p.write(*flat743)
		return nil
	} else {
		_t1353 := func(_dollar_dollar *pb.RelationId) *string {
			_t1354 := p.deconstruct_relation_id_string(_dollar_dollar)
			return _t1354
		}
		_t1355 := _t1353(msg)
		deconstruct_result741 := _t1355
		if deconstruct_result741 != nil {
			unwrapped742 := *deconstruct_result741
			p.write(":")
			p.write(unwrapped742)
		} else {
			_t1356 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1357 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1357
			}
			_t1358 := _t1356(msg)
			deconstruct_result739 := _t1358
			if deconstruct_result739 != nil {
				unwrapped740 := deconstruct_result739
				p.write(p.formatUint128(unwrapped740))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *Parser) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat748 := nil
	if flat748 != nil {
		p.write(*flat748)
		return nil
	} else {
		_t1359 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1360 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1360, _dollar_dollar.GetValue()}
		}
		_t1361 := _t1359(msg)
		fields744 := _t1361
		unwrapped_fields745 := fields744
		p.write("(")
		p.indent()
		field746 := unwrapped_fields745[0].([]interface{})
		_t1362 := p.pretty_bindings(field746)
		_ = _t1362
		p.newline()
		field747 := unwrapped_fields745[1].(*pb.Formula)
		_t1363 := p.pretty_formula(field747)
		_ = _t1363
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_bindings(msg []interface{}) interface{} {
	flat756 := nil
	if flat756 != nil {
		p.write(*flat756)
		return nil
	} else {
		_t1364 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1365 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1365 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1365}
		}
		_t1366 := _t1364(msg)
		fields749 := _t1366
		unwrapped_fields750 := fields749
		p.write("[")
		p.indent()
		field751 := unwrapped_fields750[0].([]*pb.Binding)
		for i753, elem752 := range field751 {
			if (i753 > 0) {
				p.newline()
			}
			_t1367 := p.pretty_binding(elem752)
		}
		field754 := unwrapped_fields750[1].([]*pb.Binding)
		if field754 != nil {
			p.newline()
			opt_val755 := field754
			_t1368 := p.pretty_value_bindings(opt_val755)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *Parser) pretty_binding(msg *pb.Binding) interface{} {
	flat761 := nil
	if flat761 != nil {
		p.write(*flat761)
		return nil
	} else {
		_t1369 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1370 := _t1369(msg)
		fields757 := _t1370
		unwrapped_fields758 := fields757
		field759 := unwrapped_fields758[0].(string)
		p.write(field759)
		p.write("::")
		field760 := unwrapped_fields758[1].(*pb.Type)
		_t1371 := p.pretty_type(field760)
	}
	return nil
}

func (p *Parser) pretty_type(msg *pb.Type) interface{} {
	flat784 := nil
	if flat784 != nil {
		p.write(*flat784)
		return nil
	} else {
		_t1372 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1373 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1373 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1373
		}
		_t1374 := _t1372(msg)
		deconstruct_result782 := _t1374
		if deconstruct_result782 != nil {
			unwrapped783 := deconstruct_result782
			_t1375 := p.pretty_unspecified_type(unwrapped783)
		} else {
			_t1376 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1377 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1377 = _dollar_dollar.GetStringType()
				}
				return _t1377
			}
			_t1378 := _t1376(msg)
			deconstruct_result780 := _t1378
			if deconstruct_result780 != nil {
				unwrapped781 := deconstruct_result780
				_t1379 := p.pretty_string_type(unwrapped781)
			} else {
				_t1380 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1381 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1381 = _dollar_dollar.GetIntType()
					}
					return _t1381
				}
				_t1382 := _t1380(msg)
				deconstruct_result778 := _t1382
				if deconstruct_result778 != nil {
					unwrapped779 := deconstruct_result778
					_t1383 := p.pretty_int_type(unwrapped779)
				} else {
					_t1384 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1385 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1385 = _dollar_dollar.GetFloatType()
						}
						return _t1385
					}
					_t1386 := _t1384(msg)
					deconstruct_result776 := _t1386
					if deconstruct_result776 != nil {
						unwrapped777 := deconstruct_result776
						_t1387 := p.pretty_float_type(unwrapped777)
					} else {
						_t1388 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1389 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1389 = _dollar_dollar.GetUint128Type()
							}
							return _t1389
						}
						_t1390 := _t1388(msg)
						deconstruct_result774 := _t1390
						if deconstruct_result774 != nil {
							unwrapped775 := deconstruct_result774
							_t1391 := p.pretty_uint128_type(unwrapped775)
						} else {
							_t1392 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1393 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1393 = _dollar_dollar.GetInt128Type()
								}
								return _t1393
							}
							_t1394 := _t1392(msg)
							deconstruct_result772 := _t1394
							if deconstruct_result772 != nil {
								unwrapped773 := deconstruct_result772
								_t1395 := p.pretty_int128_type(unwrapped773)
							} else {
								_t1396 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1397 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1397 = _dollar_dollar.GetDateType()
									}
									return _t1397
								}
								_t1398 := _t1396(msg)
								deconstruct_result770 := _t1398
								if deconstruct_result770 != nil {
									unwrapped771 := deconstruct_result770
									_t1399 := p.pretty_date_type(unwrapped771)
								} else {
									_t1400 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1401 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1401 = _dollar_dollar.GetDatetimeType()
										}
										return _t1401
									}
									_t1402 := _t1400(msg)
									deconstruct_result768 := _t1402
									if deconstruct_result768 != nil {
										unwrapped769 := deconstruct_result768
										_t1403 := p.pretty_datetime_type(unwrapped769)
									} else {
										_t1404 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1405 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1405 = _dollar_dollar.GetMissingType()
											}
											return _t1405
										}
										_t1406 := _t1404(msg)
										deconstruct_result766 := _t1406
										if deconstruct_result766 != nil {
											unwrapped767 := deconstruct_result766
											_t1407 := p.pretty_missing_type(unwrapped767)
										} else {
											_t1408 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1409 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1409 = _dollar_dollar.GetDecimalType()
												}
												return _t1409
											}
											_t1410 := _t1408(msg)
											deconstruct_result764 := _t1410
											if deconstruct_result764 != nil {
												unwrapped765 := deconstruct_result764
												_t1411 := p.pretty_decimal_type(unwrapped765)
											} else {
												_t1412 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1413 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1413 = _dollar_dollar.GetBooleanType()
													}
													return _t1413
												}
												_t1414 := _t1412(msg)
												deconstruct_result762 := _t1414
												if deconstruct_result762 != nil {
													unwrapped763 := deconstruct_result762
													_t1415 := p.pretty_boolean_type(unwrapped763)
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
	return nil
}

func (p *Parser) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields785 := msg
	p.write("UNKNOWN")
	return nil
}

func (p *Parser) pretty_string_type(msg *pb.StringType) interface{} {
	fields786 := msg
	p.write("STRING")
	return nil
}

func (p *Parser) pretty_int_type(msg *pb.IntType) interface{} {
	fields787 := msg
	p.write("INT")
	return nil
}

func (p *Parser) pretty_float_type(msg *pb.FloatType) interface{} {
	fields788 := msg
	p.write("FLOAT")
	return nil
}

func (p *Parser) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields789 := msg
	p.write("UINT128")
	return nil
}

func (p *Parser) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields790 := msg
	p.write("INT128")
	return nil
}

func (p *Parser) pretty_date_type(msg *pb.DateType) interface{} {
	fields791 := msg
	p.write("DATE")
	return nil
}

func (p *Parser) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields792 := msg
	p.write("DATETIME")
	return nil
}

func (p *Parser) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields793 := msg
	p.write("MISSING")
	return nil
}

func (p *Parser) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat798 := nil
	if flat798 != nil {
		p.write(*flat798)
		return nil
	} else {
		_t1416 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1417 := _t1416(msg)
		fields794 := _t1417
		unwrapped_fields795 := fields794
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field796 := unwrapped_fields795[0].(int64)
		p.write(fmt.Sprintf("%d", field796))
		p.newline()
		field797 := unwrapped_fields795[1].(int64)
		p.write(fmt.Sprintf("%d", field797))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields799 := msg
	p.write("BOOLEAN")
	return nil
}

func (p *Parser) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat803 := nil
	if flat803 != nil {
		p.write(*flat803)
		return nil
	} else {
		fields800 := msg
		p.write("|")
		if !(len(fields800) == 0) {
			p.write(" ")
			for i802, elem801 := range fields800 {
				if (i802 > 0) {
					p.newline()
				}
				_t1418 := p.pretty_binding(elem801)
			}
		}
	}
	return nil
}

func (p *Parser) pretty_formula(msg *pb.Formula) interface{} {
	flat830 := nil
	if flat830 != nil {
		p.write(*flat830)
		return nil
	} else {
		_t1419 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1420 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1420 = _dollar_dollar.GetConjunction()
			}
			return _t1420
		}
		_t1421 := _t1419(msg)
		deconstruct_result828 := _t1421
		if deconstruct_result828 != nil {
			unwrapped829 := deconstruct_result828
			_t1422 := p.pretty_true(unwrapped829)
		} else {
			_t1423 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1424 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1424 = _dollar_dollar.GetDisjunction()
				}
				return _t1424
			}
			_t1425 := _t1423(msg)
			deconstruct_result826 := _t1425
			if deconstruct_result826 != nil {
				unwrapped827 := deconstruct_result826
				_t1426 := p.pretty_false(unwrapped827)
			} else {
				_t1427 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1428 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1428 = _dollar_dollar.GetExists()
					}
					return _t1428
				}
				_t1429 := _t1427(msg)
				deconstruct_result824 := _t1429
				if deconstruct_result824 != nil {
					unwrapped825 := deconstruct_result824
					_t1430 := p.pretty_exists(unwrapped825)
				} else {
					_t1431 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1432 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1432 = _dollar_dollar.GetReduce()
						}
						return _t1432
					}
					_t1433 := _t1431(msg)
					deconstruct_result822 := _t1433
					if deconstruct_result822 != nil {
						unwrapped823 := deconstruct_result822
						_t1434 := p.pretty_reduce(unwrapped823)
					} else {
						_t1435 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1436 *pb.Conjunction
							if hasProtoField(_dollar_dollar, "conjunction") {
								_t1436 = _dollar_dollar.GetConjunction()
							}
							return _t1436
						}
						_t1437 := _t1435(msg)
						deconstruct_result820 := _t1437
						if deconstruct_result820 != nil {
							unwrapped821 := deconstruct_result820
							_t1438 := p.pretty_conjunction(unwrapped821)
						} else {
							_t1439 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1440 *pb.Disjunction
								if hasProtoField(_dollar_dollar, "disjunction") {
									_t1440 = _dollar_dollar.GetDisjunction()
								}
								return _t1440
							}
							_t1441 := _t1439(msg)
							deconstruct_result818 := _t1441
							if deconstruct_result818 != nil {
								unwrapped819 := deconstruct_result818
								_t1442 := p.pretty_disjunction(unwrapped819)
							} else {
								_t1443 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1444 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1444 = _dollar_dollar.GetNot()
									}
									return _t1444
								}
								_t1445 := _t1443(msg)
								deconstruct_result816 := _t1445
								if deconstruct_result816 != nil {
									unwrapped817 := deconstruct_result816
									_t1446 := p.pretty_not(unwrapped817)
								} else {
									_t1447 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1448 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1448 = _dollar_dollar.GetFfi()
										}
										return _t1448
									}
									_t1449 := _t1447(msg)
									deconstruct_result814 := _t1449
									if deconstruct_result814 != nil {
										unwrapped815 := deconstruct_result814
										_t1450 := p.pretty_ffi(unwrapped815)
									} else {
										_t1451 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1452 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1452 = _dollar_dollar.GetAtom()
											}
											return _t1452
										}
										_t1453 := _t1451(msg)
										deconstruct_result812 := _t1453
										if deconstruct_result812 != nil {
											unwrapped813 := deconstruct_result812
											_t1454 := p.pretty_atom(unwrapped813)
										} else {
											_t1455 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1456 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1456 = _dollar_dollar.GetPragma()
												}
												return _t1456
											}
											_t1457 := _t1455(msg)
											deconstruct_result810 := _t1457
											if deconstruct_result810 != nil {
												unwrapped811 := deconstruct_result810
												_t1458 := p.pretty_pragma(unwrapped811)
											} else {
												_t1459 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1460 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1460 = _dollar_dollar.GetPrimitive()
													}
													return _t1460
												}
												_t1461 := _t1459(msg)
												deconstruct_result808 := _t1461
												if deconstruct_result808 != nil {
													unwrapped809 := deconstruct_result808
													_t1462 := p.pretty_primitive(unwrapped809)
												} else {
													_t1463 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1464 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1464 = _dollar_dollar.GetRelAtom()
														}
														return _t1464
													}
													_t1465 := _t1463(msg)
													deconstruct_result806 := _t1465
													if deconstruct_result806 != nil {
														unwrapped807 := deconstruct_result806
														_t1466 := p.pretty_rel_atom(unwrapped807)
													} else {
														_t1467 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1468 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1468 = _dollar_dollar.GetCast()
															}
															return _t1468
														}
														_t1469 := _t1467(msg)
														deconstruct_result804 := _t1469
														if deconstruct_result804 != nil {
															unwrapped805 := deconstruct_result804
															_t1470 := p.pretty_cast(unwrapped805)
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

func (p *Parser) pretty_true(msg *pb.Conjunction) interface{} {
	fields831 := msg
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *Parser) pretty_false(msg *pb.Disjunction) interface{} {
	fields832 := msg
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *Parser) pretty_exists(msg *pb.Exists) interface{} {
	flat837 := nil
	if flat837 != nil {
		p.write(*flat837)
		return nil
	} else {
		_t1471 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1472 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1472, _dollar_dollar.GetBody().GetValue()}
		}
		_t1473 := _t1471(msg)
		fields833 := _t1473
		unwrapped_fields834 := fields833
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field835 := unwrapped_fields834[0].([]interface{})
		_t1474 := p.pretty_bindings(field835)
		_ = _t1474
		p.newline()
		field836 := unwrapped_fields834[1].(*pb.Formula)
		_t1475 := p.pretty_formula(field836)
		_ = _t1475
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_reduce(msg *pb.Reduce) interface{} {
	flat843 := nil
	if flat843 != nil {
		p.write(*flat843)
		return nil
	} else {
		_t1476 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1477 := _t1476(msg)
		fields838 := _t1477
		unwrapped_fields839 := fields838
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field840 := unwrapped_fields839[0].(*pb.Abstraction)
		_t1478 := p.pretty_abstraction(field840)
		_ = _t1478
		p.newline()
		field841 := unwrapped_fields839[1].(*pb.Abstraction)
		_t1479 := p.pretty_abstraction(field841)
		_ = _t1479
		p.newline()
		field842 := unwrapped_fields839[2].([]*pb.Term)
		_t1480 := p.pretty_terms(field842)
		_ = _t1480
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_terms(msg []*pb.Term) interface{} {
	flat847 := nil
	if flat847 != nil {
		p.write(*flat847)
		return nil
	} else {
		fields844 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields844) == 0) {
			p.newline()
			for i846, elem845 := range fields844 {
				if (i846 > 0) {
					p.newline()
				}
				_t1481 := p.pretty_term(elem845)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_term(msg *pb.Term) interface{} {
	flat852 := nil
	if flat852 != nil {
		p.write(*flat852)
		return nil
	} else {
		_t1482 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1483 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1483 = _dollar_dollar.GetVar()
			}
			return _t1483
		}
		_t1484 := _t1482(msg)
		deconstruct_result850 := _t1484
		if deconstruct_result850 != nil {
			unwrapped851 := deconstruct_result850
			_t1485 := p.pretty_var(unwrapped851)
		} else {
			_t1486 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1487 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1487 = _dollar_dollar.GetConstant()
				}
				return _t1487
			}
			_t1488 := _t1486(msg)
			deconstruct_result848 := _t1488
			if deconstruct_result848 != nil {
				unwrapped849 := deconstruct_result848
				_t1489 := p.pretty_constant(unwrapped849)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *Parser) pretty_var(msg *pb.Var) interface{} {
	flat855 := nil
	if flat855 != nil {
		p.write(*flat855)
		return nil
	} else {
		_t1490 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1491 := _t1490(msg)
		fields853 := _t1491
		unwrapped_fields854 := *fields853
		p.write(unwrapped_fields854)
	}
	return nil
}

func (p *Parser) pretty_constant(msg *pb.Value) interface{} {
	flat857 := nil
	if flat857 != nil {
		p.write(*flat857)
		return nil
	} else {
		fields856 := msg
		_t1492 := p.pretty_value(fields856)
	}
	return nil
}

func (p *Parser) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat862 := nil
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		_t1493 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1494 := _t1493(msg)
		fields858 := _t1494
		unwrapped_fields859 := fields858
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields859) == 0) {
			p.newline()
			for i861, elem860 := range unwrapped_fields859 {
				if (i861 > 0) {
					p.newline()
				}
				_t1495 := p.pretty_formula(elem860)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat867 := nil
	if flat867 != nil {
		p.write(*flat867)
		return nil
	} else {
		_t1496 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1497 := _t1496(msg)
		fields863 := _t1497
		unwrapped_fields864 := fields863
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields864) == 0) {
			p.newline()
			for i866, elem865 := range unwrapped_fields864 {
				if (i866 > 0) {
					p.newline()
				}
				_t1498 := p.pretty_formula(elem865)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_not(msg *pb.Not) interface{} {
	flat870 := nil
	if flat870 != nil {
		p.write(*flat870)
		return nil
	} else {
		_t1499 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1500 := _t1499(msg)
		fields868 := _t1500
		unwrapped_fields869 := fields868
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		_t1501 := p.pretty_formula(unwrapped_fields869)
		_ = _t1501
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_ffi(msg *pb.FFI) interface{} {
	flat876 := nil
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_t1502 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1503 := _t1502(msg)
		fields871 := _t1503
		unwrapped_fields872 := fields871
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field873 := unwrapped_fields872[0].(string)
		_t1504 := p.pretty_name(field873)
		_ = _t1504
		p.newline()
		field874 := unwrapped_fields872[1].([]*pb.Abstraction)
		_t1505 := p.pretty_ffi_args(field874)
		_ = _t1505
		p.newline()
		field875 := unwrapped_fields872[2].([]*pb.Term)
		_t1506 := p.pretty_terms(field875)
		_ = _t1506
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_name(msg string) interface{} {
	flat878 := nil
	if flat878 != nil {
		p.write(*flat878)
		return nil
	} else {
		fields877 := msg
		p.write(":")
		p.write(fields877)
	}
	return nil
}

func (p *Parser) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat882 := nil
	if flat882 != nil {
		p.write(*flat882)
		return nil
	} else {
		fields879 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields879) == 0) {
			p.newline()
			for i881, elem880 := range fields879 {
				if (i881 > 0) {
					p.newline()
				}
				_t1507 := p.pretty_abstraction(elem880)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_atom(msg *pb.Atom) interface{} {
	flat889 := nil
	if flat889 != nil {
		p.write(*flat889)
		return nil
	} else {
		_t1508 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1509 := _t1508(msg)
		fields883 := _t1509
		unwrapped_fields884 := fields883
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field885 := unwrapped_fields884[0].(*pb.RelationId)
		_t1510 := p.pretty_relation_id(field885)
		_ = _t1510
		field886 := unwrapped_fields884[1].([]*pb.Term)
		if !(len(field886) == 0) {
			p.newline()
			for i888, elem887 := range field886 {
				if (i888 > 0) {
					p.newline()
				}
				_t1511 := p.pretty_term(elem887)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_pragma(msg *pb.Pragma) interface{} {
	flat896 := nil
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		_t1512 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1513 := _t1512(msg)
		fields890 := _t1513
		unwrapped_fields891 := fields890
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field892 := unwrapped_fields891[0].(string)
		_t1514 := p.pretty_name(field892)
		_ = _t1514
		field893 := unwrapped_fields891[1].([]*pb.Term)
		if !(len(field893) == 0) {
			p.newline()
			for i895, elem894 := range field893 {
				if (i895 > 0) {
					p.newline()
				}
				_t1515 := p.pretty_term(elem894)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_primitive(msg *pb.Primitive) interface{} {
	flat912 := nil
	if flat912 != nil {
		p.write(*flat912)
		return nil
	} else {
		_t1516 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1517 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1517 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1517
		}
		_t1518 := _t1516(msg)
		guard_result911 := _t1518
		if guard_result911 != nil {
			_t1519 := p.pretty_eq(msg)
		} else {
			_t1520 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1521 interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1521 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
				}
				return _t1521
			}
			_t1522 := _t1520(msg)
			guard_result910 := _t1522
			if guard_result910 != nil {
				_t1523 := p.pretty_lt(msg)
			} else {
				_t1524 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1525 interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1525 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
					}
					return _t1525
				}
				_t1526 := _t1524(msg)
				guard_result909 := _t1526
				if guard_result909 != nil {
					_t1527 := p.pretty_lt_eq(msg)
				} else {
					_t1528 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1529 interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1529 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
						}
						return _t1529
					}
					_t1530 := _t1528(msg)
					guard_result908 := _t1530
					if guard_result908 != nil {
						_t1531 := p.pretty_gt(msg)
					} else {
						_t1532 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1533 interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1533 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
							}
							return _t1533
						}
						_t1534 := _t1532(msg)
						guard_result907 := _t1534
						if guard_result907 != nil {
							_t1535 := p.pretty_gt_eq(msg)
						} else {
							_t1536 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1537 interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1537 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
								}
								return _t1537
							}
							_t1538 := _t1536(msg)
							guard_result906 := _t1538
							if guard_result906 != nil {
								_t1539 := p.pretty_add(msg)
							} else {
								_t1540 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1541 interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1541 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
									}
									return _t1541
								}
								_t1542 := _t1540(msg)
								guard_result905 := _t1542
								if guard_result905 != nil {
									_t1543 := p.pretty_minus(msg)
								} else {
									_t1544 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1545 interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1545 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
										}
										return _t1545
									}
									_t1546 := _t1544(msg)
									guard_result904 := _t1546
									if guard_result904 != nil {
										_t1547 := p.pretty_multiply(msg)
									} else {
										_t1548 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1549 interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1549 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
											}
											return _t1549
										}
										_t1550 := _t1548(msg)
										guard_result903 := _t1550
										if guard_result903 != nil {
											_t1551 := p.pretty_divide(msg)
										} else {
											_t1552 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1553 := _t1552(msg)
											fields897 := _t1553
											unwrapped_fields898 := fields897
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field899 := unwrapped_fields898[0].(string)
											_t1554 := p.pretty_name(field899)
											_ = _t1554
											field900 := unwrapped_fields898[1].([]*pb.RelTerm)
											if !(len(field900) == 0) {
												p.newline()
												for i902, elem901 := range field900 {
													if (i902 > 0) {
														p.newline()
													}
													_t1555 := p.pretty_rel_term(elem901)
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

func (p *Parser) pretty_eq(msg *pb.Primitive) interface{} {
	flat917 := nil
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_t1556 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1557 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1557 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1557
		}
		_t1558 := _t1556(msg)
		fields913 := _t1558
		unwrapped_fields914 := fields913
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field915 := unwrapped_fields914[0].(*pb.Term)
		_t1559 := p.pretty_term(field915)
		_ = _t1559
		p.newline()
		field916 := unwrapped_fields914[1].(*pb.Term)
		_t1560 := p.pretty_term(field916)
		_ = _t1560
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_lt(msg *pb.Primitive) interface{} {
	flat922 := nil
	if flat922 != nil {
		p.write(*flat922)
		return nil
	} else {
		_t1561 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1562 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1562 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1562
		}
		_t1563 := _t1561(msg)
		fields918 := _t1563
		unwrapped_fields919 := fields918
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field920 := unwrapped_fields919[0].(*pb.Term)
		_t1564 := p.pretty_term(field920)
		_ = _t1564
		p.newline()
		field921 := unwrapped_fields919[1].(*pb.Term)
		_t1565 := p.pretty_term(field921)
		_ = _t1565
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat927 := nil
	if flat927 != nil {
		p.write(*flat927)
		return nil
	} else {
		_t1566 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1567 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1567 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1567
		}
		_t1568 := _t1566(msg)
		fields923 := _t1568
		unwrapped_fields924 := fields923
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field925 := unwrapped_fields924[0].(*pb.Term)
		_t1569 := p.pretty_term(field925)
		_ = _t1569
		p.newline()
		field926 := unwrapped_fields924[1].(*pb.Term)
		_t1570 := p.pretty_term(field926)
		_ = _t1570
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_gt(msg *pb.Primitive) interface{} {
	flat932 := nil
	if flat932 != nil {
		p.write(*flat932)
		return nil
	} else {
		_t1571 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1572 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1572 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1572
		}
		_t1573 := _t1571(msg)
		fields928 := _t1573
		unwrapped_fields929 := fields928
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field930 := unwrapped_fields929[0].(*pb.Term)
		_t1574 := p.pretty_term(field930)
		_ = _t1574
		p.newline()
		field931 := unwrapped_fields929[1].(*pb.Term)
		_t1575 := p.pretty_term(field931)
		_ = _t1575
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat937 := nil
	if flat937 != nil {
		p.write(*flat937)
		return nil
	} else {
		_t1576 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1577 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1577 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm()}
			}
			return _t1577
		}
		_t1578 := _t1576(msg)
		fields933 := _t1578
		unwrapped_fields934 := fields933
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field935 := unwrapped_fields934[0].(*pb.Term)
		_t1579 := p.pretty_term(field935)
		_ = _t1579
		p.newline()
		field936 := unwrapped_fields934[1].(*pb.Term)
		_t1580 := p.pretty_term(field936)
		_ = _t1580
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_add(msg *pb.Primitive) interface{} {
	flat943 := nil
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_t1581 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1582 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1582 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
			}
			return _t1582
		}
		_t1583 := _t1581(msg)
		fields938 := _t1583
		unwrapped_fields939 := fields938
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field940 := unwrapped_fields939[0].(*pb.Term)
		_t1584 := p.pretty_term(field940)
		_ = _t1584
		p.newline()
		field941 := unwrapped_fields939[1].(*pb.Term)
		_t1585 := p.pretty_term(field941)
		_ = _t1585
		p.newline()
		field942 := unwrapped_fields939[2].(*pb.Term)
		_t1586 := p.pretty_term(field942)
		_ = _t1586
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_minus(msg *pb.Primitive) interface{} {
	flat949 := nil
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		_t1587 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1588 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1588 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
			}
			return _t1588
		}
		_t1589 := _t1587(msg)
		fields944 := _t1589
		unwrapped_fields945 := fields944
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field946 := unwrapped_fields945[0].(*pb.Term)
		_t1590 := p.pretty_term(field946)
		_ = _t1590
		p.newline()
		field947 := unwrapped_fields945[1].(*pb.Term)
		_t1591 := p.pretty_term(field947)
		_ = _t1591
		p.newline()
		field948 := unwrapped_fields945[2].(*pb.Term)
		_t1592 := p.pretty_term(field948)
		_ = _t1592
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_multiply(msg *pb.Primitive) interface{} {
	flat955 := nil
	if flat955 != nil {
		p.write(*flat955)
		return nil
	} else {
		_t1593 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1594 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1594 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
			}
			return _t1594
		}
		_t1595 := _t1593(msg)
		fields950 := _t1595
		unwrapped_fields951 := fields950
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field952 := unwrapped_fields951[0].(*pb.Term)
		_t1596 := p.pretty_term(field952)
		_ = _t1596
		p.newline()
		field953 := unwrapped_fields951[1].(*pb.Term)
		_t1597 := p.pretty_term(field953)
		_ = _t1597
		p.newline()
		field954 := unwrapped_fields951[2].(*pb.Term)
		_t1598 := p.pretty_term(field954)
		_ = _t1598
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_divide(msg *pb.Primitive) interface{} {
	flat961 := nil
	if flat961 != nil {
		p.write(*flat961)
		return nil
	} else {
		_t1599 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1600 interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1600 = []interface{}{_dollar_dollar.GetTerms()[0].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[1].(*pb.RelTerm).GetTerm(), _dollar_dollar.GetTerms()[2].(*pb.RelTerm).GetTerm()}
			}
			return _t1600
		}
		_t1601 := _t1599(msg)
		fields956 := _t1601
		unwrapped_fields957 := fields956
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field958 := unwrapped_fields957[0].(*pb.Term)
		_t1602 := p.pretty_term(field958)
		_ = _t1602
		p.newline()
		field959 := unwrapped_fields957[1].(*pb.Term)
		_t1603 := p.pretty_term(field959)
		_ = _t1603
		p.newline()
		field960 := unwrapped_fields957[2].(*pb.Term)
		_t1604 := p.pretty_term(field960)
		_ = _t1604
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat966 := nil
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_t1605 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1606 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1606 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1606
		}
		_t1607 := _t1605(msg)
		deconstruct_result964 := _t1607
		if deconstruct_result964 != nil {
			unwrapped965 := deconstruct_result964
			_t1608 := p.pretty_specialized_value(unwrapped965)
		} else {
			_t1609 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1610 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1610 = _dollar_dollar.GetTerm()
				}
				return _t1610
			}
			_t1611 := _t1609(msg)
			deconstruct_result962 := _t1611
			if deconstruct_result962 != nil {
				unwrapped963 := deconstruct_result962
				_t1612 := p.pretty_term(unwrapped963)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *Parser) pretty_specialized_value(msg *pb.Value) interface{} {
	flat968 := nil
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		fields967 := msg
		p.write("#")
		_t1613 := p.pretty_value(fields967)
	}
	return nil
}

func (p *Parser) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat975 := nil
	if flat975 != nil {
		p.write(*flat975)
		return nil
	} else {
		_t1614 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1615 := _t1614(msg)
		fields969 := _t1615
		unwrapped_fields970 := fields969
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field971 := unwrapped_fields970[0].(string)
		_t1616 := p.pretty_name(field971)
		_ = _t1616
		field972 := unwrapped_fields970[1].([]*pb.RelTerm)
		if !(len(field972) == 0) {
			p.newline()
			for i974, elem973 := range field972 {
				if (i974 > 0) {
					p.newline()
				}
				_t1617 := p.pretty_rel_term(elem973)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_cast(msg *pb.Cast) interface{} {
	flat980 := nil
	if flat980 != nil {
		p.write(*flat980)
		return nil
	} else {
		_t1618 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1619 := _t1618(msg)
		fields976 := _t1619
		unwrapped_fields977 := fields976
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field978 := unwrapped_fields977[0].(*pb.Term)
		_t1620 := p.pretty_term(field978)
		_ = _t1620
		p.newline()
		field979 := unwrapped_fields977[1].(*pb.Term)
		_t1621 := p.pretty_term(field979)
		_ = _t1621
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat984 := nil
	if flat984 != nil {
		p.write(*flat984)
		return nil
	} else {
		fields981 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields981) == 0) {
			p.newline()
			for i983, elem982 := range fields981 {
				if (i983 > 0) {
					p.newline()
				}
				_t1622 := p.pretty_attribute(elem982)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_attribute(msg *pb.Attribute) interface{} {
	flat991 := nil
	if flat991 != nil {
		p.write(*flat991)
		return nil
	} else {
		_t1623 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1624 := _t1623(msg)
		fields985 := _t1624
		unwrapped_fields986 := fields985
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field987 := unwrapped_fields986[0].(string)
		_t1625 := p.pretty_name(field987)
		_ = _t1625
		field988 := unwrapped_fields986[1].([]*pb.Value)
		if !(len(field988) == 0) {
			p.newline()
			for i990, elem989 := range field988 {
				if (i990 > 0) {
					p.newline()
				}
				_t1626 := p.pretty_value(elem989)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat998 := nil
	if flat998 != nil {
		p.write(*flat998)
		return nil
	} else {
		_t1627 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1628 := _t1627(msg)
		fields992 := _t1628
		unwrapped_fields993 := fields992
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field994 := unwrapped_fields993[0].([]*pb.RelationId)
		if !(len(field994) == 0) {
			p.newline()
			for i996, elem995 := range field994 {
				if (i996 > 0) {
					p.newline()
				}
				_t1629 := p.pretty_relation_id(elem995)
			}
		}
		p.newline()
		field997 := unwrapped_fields993[1].(*pb.Script)
		_t1630 := p.pretty_script(field997)
		_ = _t1630
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_script(msg *pb.Script) interface{} {
	flat1003 := nil
	if flat1003 != nil {
		p.write(*flat1003)
		return nil
	} else {
		_t1631 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1632 := _t1631(msg)
		fields999 := _t1632
		unwrapped_fields1000 := fields999
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1000) == 0) {
			p.newline()
			for i1002, elem1001 := range unwrapped_fields1000 {
				if (i1002 > 0) {
					p.newline()
				}
				_t1633 := p.pretty_construct(elem1001)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_construct(msg *pb.Construct) interface{} {
	flat1008 := nil
	if flat1008 != nil {
		p.write(*flat1008)
		return nil
	} else {
		_t1634 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1635 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1635 = _dollar_dollar.GetLoop()
			}
			return _t1635
		}
		_t1636 := _t1634(msg)
		deconstruct_result1006 := _t1636
		if deconstruct_result1006 != nil {
			unwrapped1007 := deconstruct_result1006
			_t1637 := p.pretty_loop(unwrapped1007)
		} else {
			_t1638 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1639 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1639 = _dollar_dollar.GetInstruction()
				}
				return _t1639
			}
			_t1640 := _t1638(msg)
			deconstruct_result1004 := _t1640
			if deconstruct_result1004 != nil {
				unwrapped1005 := deconstruct_result1004
				_t1641 := p.pretty_instruction(unwrapped1005)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *Parser) pretty_loop(msg *pb.Loop) interface{} {
	flat1013 := nil
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		_t1642 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1643 := _t1642(msg)
		fields1009 := _t1643
		unwrapped_fields1010 := fields1009
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1011 := unwrapped_fields1010[0].([]*pb.Instruction)
		_t1644 := p.pretty_init(field1011)
		_ = _t1644
		p.newline()
		field1012 := unwrapped_fields1010[1].(*pb.Script)
		_t1645 := p.pretty_script(field1012)
		_ = _t1645
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_init(msg []*pb.Instruction) interface{} {
	flat1017 := nil
	if flat1017 != nil {
		p.write(*flat1017)
		return nil
	} else {
		fields1014 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1014) == 0) {
			p.newline()
			for i1016, elem1015 := range fields1014 {
				if (i1016 > 0) {
					p.newline()
				}
				_t1646 := p.pretty_instruction(elem1015)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1028 := nil
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		_t1647 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1648 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1648 = _dollar_dollar.GetAssign()
			}
			return _t1648
		}
		_t1649 := _t1647(msg)
		deconstruct_result1026 := _t1649
		if deconstruct_result1026 != nil {
			unwrapped1027 := deconstruct_result1026
			_t1650 := p.pretty_assign(unwrapped1027)
		} else {
			_t1651 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1652 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1652 = _dollar_dollar.GetUpsert()
				}
				return _t1652
			}
			_t1653 := _t1651(msg)
			deconstruct_result1024 := _t1653
			if deconstruct_result1024 != nil {
				unwrapped1025 := deconstruct_result1024
				_t1654 := p.pretty_upsert(unwrapped1025)
			} else {
				_t1655 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1656 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1656 = _dollar_dollar.GetBreak()
					}
					return _t1656
				}
				_t1657 := _t1655(msg)
				deconstruct_result1022 := _t1657
				if deconstruct_result1022 != nil {
					unwrapped1023 := deconstruct_result1022
					_t1658 := p.pretty_break(unwrapped1023)
				} else {
					_t1659 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1660 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1660 = _dollar_dollar.GetMonoidDef()
						}
						return _t1660
					}
					_t1661 := _t1659(msg)
					deconstruct_result1020 := _t1661
					if deconstruct_result1020 != nil {
						unwrapped1021 := deconstruct_result1020
						_t1662 := p.pretty_monoid_def(unwrapped1021)
					} else {
						_t1663 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1664 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1664 = _dollar_dollar.GetMonusDef()
							}
							return _t1664
						}
						_t1665 := _t1663(msg)
						deconstruct_result1018 := _t1665
						if deconstruct_result1018 != nil {
							unwrapped1019 := deconstruct_result1018
							_t1666 := p.pretty_monus_def(unwrapped1019)
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

func (p *Parser) pretty_assign(msg *pb.Assign) interface{} {
	flat1035 := nil
	if flat1035 != nil {
		p.write(*flat1035)
		return nil
	} else {
		_t1667 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1668 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1668 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1668}
		}
		_t1669 := _t1667(msg)
		fields1029 := _t1669
		unwrapped_fields1030 := fields1029
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1031 := unwrapped_fields1030[0].(*pb.RelationId)
		_t1670 := p.pretty_relation_id(field1031)
		_ = _t1670
		p.newline()
		field1032 := unwrapped_fields1030[1].(*pb.Abstraction)
		_t1671 := p.pretty_abstraction(field1032)
		_ = _t1671
		field1033 := unwrapped_fields1030[2].([]*pb.Attribute)
		if field1033 != nil {
			p.newline()
			opt_val1034 := field1033
			_t1672 := p.pretty_attrs(opt_val1034)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1042 := nil
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		_t1673 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1674 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1674 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1674}
		}
		_t1675 := _t1673(msg)
		fields1036 := _t1675
		unwrapped_fields1037 := fields1036
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1038 := unwrapped_fields1037[0].(*pb.RelationId)
		_t1676 := p.pretty_relation_id(field1038)
		_ = _t1676
		p.newline()
		field1039 := unwrapped_fields1037[1].([]interface{})
		_t1677 := p.pretty_abstraction_with_arity(field1039)
		_ = _t1677
		field1040 := unwrapped_fields1037[2].([]*pb.Attribute)
		if field1040 != nil {
			p.newline()
			opt_val1041 := field1040
			_t1678 := p.pretty_attrs(opt_val1041)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1047 := nil
	if flat1047 != nil {
		p.write(*flat1047)
		return nil
	} else {
		_t1679 := func(_dollar_dollar []interface{}) []interface{} {
			_t1680 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1680, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1681 := _t1679(msg)
		fields1043 := _t1681
		unwrapped_fields1044 := fields1043
		p.write("(")
		p.indent()
		field1045 := unwrapped_fields1044[0].([]interface{})
		_t1682 := p.pretty_bindings(field1045)
		_ = _t1682
		p.newline()
		field1046 := unwrapped_fields1044[1].(*pb.Formula)
		_t1683 := p.pretty_formula(field1046)
		_ = _t1683
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_break(msg *pb.Break) interface{} {
	flat1054 := nil
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_t1684 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1685 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1685 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1685}
		}
		_t1686 := _t1684(msg)
		fields1048 := _t1686
		unwrapped_fields1049 := fields1048
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1050 := unwrapped_fields1049[0].(*pb.RelationId)
		_t1687 := p.pretty_relation_id(field1050)
		_ = _t1687
		p.newline()
		field1051 := unwrapped_fields1049[1].(*pb.Abstraction)
		_t1688 := p.pretty_abstraction(field1051)
		_ = _t1688
		field1052 := unwrapped_fields1049[2].([]*pb.Attribute)
		if field1052 != nil {
			p.newline()
			opt_val1053 := field1052
			_t1689 := p.pretty_attrs(opt_val1053)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1062 := nil
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_t1690 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1691 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1691 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1691}
		}
		_t1692 := _t1690(msg)
		fields1055 := _t1692
		unwrapped_fields1056 := fields1055
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1057 := unwrapped_fields1056[0].(*pb.Monoid)
		_t1693 := p.pretty_monoid(field1057)
		_ = _t1693
		p.newline()
		field1058 := unwrapped_fields1056[1].(*pb.RelationId)
		_t1694 := p.pretty_relation_id(field1058)
		_ = _t1694
		p.newline()
		field1059 := unwrapped_fields1056[2].([]interface{})
		_t1695 := p.pretty_abstraction_with_arity(field1059)
		_ = _t1695
		field1060 := unwrapped_fields1056[3].([]*pb.Attribute)
		if field1060 != nil {
			p.newline()
			opt_val1061 := field1060
			_t1696 := p.pretty_attrs(opt_val1061)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1071 := nil
	if flat1071 != nil {
		p.write(*flat1071)
		return nil
	} else {
		_t1697 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1698 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1698 = _dollar_dollar.GetOrMonoid()
			}
			return _t1698
		}
		_t1699 := _t1697(msg)
		deconstruct_result1069 := _t1699
		if deconstruct_result1069 != nil {
			unwrapped1070 := deconstruct_result1069
			_t1700 := p.pretty_or_monoid(unwrapped1070)
		} else {
			_t1701 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1702 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1702 = _dollar_dollar.GetMinMonoid()
				}
				return _t1702
			}
			_t1703 := _t1701(msg)
			deconstruct_result1067 := _t1703
			if deconstruct_result1067 != nil {
				unwrapped1068 := deconstruct_result1067
				_t1704 := p.pretty_min_monoid(unwrapped1068)
			} else {
				_t1705 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1706 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1706 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1706
				}
				_t1707 := _t1705(msg)
				deconstruct_result1065 := _t1707
				if deconstruct_result1065 != nil {
					unwrapped1066 := deconstruct_result1065
					_t1708 := p.pretty_max_monoid(unwrapped1066)
				} else {
					_t1709 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1710 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1710 = _dollar_dollar.GetSumMonoid()
						}
						return _t1710
					}
					_t1711 := _t1709(msg)
					deconstruct_result1063 := _t1711
					if deconstruct_result1063 != nil {
						unwrapped1064 := deconstruct_result1063
						_t1712 := p.pretty_sum_monoid(unwrapped1064)
					} else {
						panic(ParseError{msg: "No matching rule for monoid"})
					}
				}
			}
		}
	}
	return nil
}

func (p *Parser) pretty_or_monoid(msg *pb.OrMonoid) interface{} {
	fields1072 := msg
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *Parser) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1075 := nil
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_t1713 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1714 := _t1713(msg)
		fields1073 := _t1714
		unwrapped_fields1074 := fields1073
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		_t1715 := p.pretty_type(unwrapped_fields1074)
		_ = _t1715
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1078 := nil
	if flat1078 != nil {
		p.write(*flat1078)
		return nil
	} else {
		_t1716 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1717 := _t1716(msg)
		fields1076 := _t1717
		unwrapped_fields1077 := fields1076
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		_t1718 := p.pretty_type(unwrapped_fields1077)
		_ = _t1718
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1081 := nil
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		_t1719 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1720 := _t1719(msg)
		fields1079 := _t1720
		unwrapped_fields1080 := fields1079
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		_t1721 := p.pretty_type(unwrapped_fields1080)
		_ = _t1721
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1089 := nil
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_t1722 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1723 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1723 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1723}
		}
		_t1724 := _t1722(msg)
		fields1082 := _t1724
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].(*pb.Monoid)
		_t1725 := p.pretty_monoid(field1084)
		_ = _t1725
		p.newline()
		field1085 := unwrapped_fields1083[1].(*pb.RelationId)
		_t1726 := p.pretty_relation_id(field1085)
		_ = _t1726
		p.newline()
		field1086 := unwrapped_fields1083[2].([]interface{})
		_t1727 := p.pretty_abstraction_with_arity(field1086)
		_ = _t1727
		field1087 := unwrapped_fields1083[3].([]*pb.Attribute)
		if field1087 != nil {
			p.newline()
			opt_val1088 := field1087
			_t1728 := p.pretty_attrs(opt_val1088)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1096 := nil
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_t1729 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1730 := _t1729(msg)
		fields1090 := _t1730
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1092 := unwrapped_fields1091[0].(*pb.RelationId)
		_t1731 := p.pretty_relation_id(field1092)
		_ = _t1731
		p.newline()
		field1093 := unwrapped_fields1091[1].(*pb.Abstraction)
		_t1732 := p.pretty_abstraction(field1093)
		_ = _t1732
		p.newline()
		field1094 := unwrapped_fields1091[2].([]*pb.Var)
		_t1733 := p.pretty_functional_dependency_keys(field1094)
		_ = _t1733
		p.newline()
		field1095 := unwrapped_fields1091[3].([]*pb.Var)
		_t1734 := p.pretty_functional_dependency_values(field1095)
		_ = _t1734
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1100 := nil
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		fields1097 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1097) == 0) {
			p.newline()
			for i1099, elem1098 := range fields1097 {
				if (i1099 > 0) {
					p.newline()
				}
				_t1735 := p.pretty_var(elem1098)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1104 := nil
	if flat1104 != nil {
		p.write(*flat1104)
		return nil
	} else {
		fields1101 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1101) == 0) {
			p.newline()
			for i1103, elem1102 := range fields1101 {
				if (i1103 > 0) {
					p.newline()
				}
				_t1736 := p.pretty_var(elem1102)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_data(msg *pb.Data) interface{} {
	flat1111 := nil
	if flat1111 != nil {
		p.write(*flat1111)
		return nil
	} else {
		_t1737 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
			var _t1738 *pb.RelEDB
			if hasProtoField(_dollar_dollar, "rel_edb") {
				_t1738 = _dollar_dollar.GetRelEdb()
			}
			return _t1738
		}
		_t1739 := _t1737(msg)
		deconstruct_result1109 := _t1739
		if deconstruct_result1109 != nil {
			unwrapped1110 := deconstruct_result1109
			_t1740 := p.pretty_rel_edb(unwrapped1110)
		} else {
			_t1741 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1742 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1742 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1742
			}
			_t1743 := _t1741(msg)
			deconstruct_result1107 := _t1743
			if deconstruct_result1107 != nil {
				unwrapped1108 := deconstruct_result1107
				_t1744 := p.pretty_betree_relation(unwrapped1108)
			} else {
				_t1745 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1746 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1746 = _dollar_dollar.GetCsvData()
					}
					return _t1746
				}
				_t1747 := _t1745(msg)
				deconstruct_result1105 := _t1747
				if deconstruct_result1105 != nil {
					unwrapped1106 := deconstruct_result1105
					_t1748 := p.pretty_csv_data(unwrapped1106)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *Parser) pretty_rel_edb(msg *pb.RelEDB) interface{} {
	flat1117 := nil
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		_t1749 := func(_dollar_dollar *pb.RelEDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1750 := _t1749(msg)
		fields1112 := _t1750
		unwrapped_fields1113 := fields1112
		p.write("(")
		p.write("rel_edb")
		p.indentSexp()
		p.newline()
		field1114 := unwrapped_fields1113[0].(*pb.RelationId)
		_t1751 := p.pretty_relation_id(field1114)
		_ = _t1751
		p.newline()
		field1115 := unwrapped_fields1113[1].([]string)
		_t1752 := p.pretty_rel_edb_path(field1115)
		_ = _t1752
		p.newline()
		field1116 := unwrapped_fields1113[2].([]*pb.Type)
		_t1753 := p.pretty_rel_edb_types(field1116)
		_ = _t1753
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_rel_edb_path(msg []string) interface{} {
	flat1121 := nil
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		fields1118 := msg
		p.write("[")
		p.indent()
		for i1120, elem1119 := range fields1118 {
			if (i1120 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1119))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *Parser) pretty_rel_edb_types(msg []*pb.Type) interface{} {
	flat1125 := nil
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		fields1122 := msg
		p.write("[")
		p.indent()
		for i1124, elem1123 := range fields1122 {
			if (i1124 > 0) {
				p.newline()
			}
			_t1754 := p.pretty_type(elem1123)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *Parser) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1130 := nil
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_t1755 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1756 := _t1755(msg)
		fields1126 := _t1756
		unwrapped_fields1127 := fields1126
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1128 := unwrapped_fields1127[0].(*pb.RelationId)
		_t1757 := p.pretty_relation_id(field1128)
		_ = _t1757
		p.newline()
		field1129 := unwrapped_fields1127[1].(*pb.BeTreeInfo)
		_t1758 := p.pretty_betree_info(field1129)
		_ = _t1758
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1136 := nil
	if flat1136 != nil {
		p.write(*flat1136)
		return nil
	} else {
		_t1759 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1760 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1760}
		}
		_t1761 := _t1759(msg)
		fields1131 := _t1761
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1133 := unwrapped_fields1132[0].([]*pb.Type)
		_t1762 := p.pretty_betree_info_key_types(field1133)
		_ = _t1762
		p.newline()
		field1134 := unwrapped_fields1132[1].([]*pb.Type)
		_t1763 := p.pretty_betree_info_value_types(field1134)
		_ = _t1763
		p.newline()
		field1135 := unwrapped_fields1132[2].([][]interface{})
		_t1764 := p.pretty_config_dict(field1135)
		_ = _t1764
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1140 := nil
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		fields1137 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1137) == 0) {
			p.newline()
			for i1139, elem1138 := range fields1137 {
				if (i1139 > 0) {
					p.newline()
				}
				_t1765 := p.pretty_type(elem1138)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1144 := nil
	if flat1144 != nil {
		p.write(*flat1144)
		return nil
	} else {
		fields1141 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1141) == 0) {
			p.newline()
			for i1143, elem1142 := range fields1141 {
				if (i1143 > 0) {
					p.newline()
				}
				_t1766 := p.pretty_type(elem1142)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1151 := nil
	if flat1151 != nil {
		p.write(*flat1151)
		return nil
	} else {
		_t1767 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1768 := _t1767(msg)
		fields1145 := _t1768
		unwrapped_fields1146 := fields1145
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1147 := unwrapped_fields1146[0].(*pb.CSVLocator)
		_t1769 := p.pretty_csvlocator(field1147)
		_ = _t1769
		p.newline()
		field1148 := unwrapped_fields1146[1].(*pb.CSVConfig)
		_t1770 := p.pretty_csv_config(field1148)
		_ = _t1770
		p.newline()
		field1149 := unwrapped_fields1146[2].([]*pb.CSVColumn)
		_t1771 := p.pretty_csv_columns(field1149)
		_ = _t1771
		p.newline()
		field1150 := unwrapped_fields1146[3].(string)
		_t1772 := p.pretty_csv_asof(field1150)
		_ = _t1772
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1158 := nil
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		_t1773 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1774 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1774 = _dollar_dollar.GetPaths()
			}
			var _t1775 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1775 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1774, _t1775}
		}
		_t1776 := _t1773(msg)
		fields1152 := _t1776
		unwrapped_fields1153 := fields1152
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1154 := unwrapped_fields1153[0].([]string)
		if field1154 != nil {
			p.newline()
			opt_val1155 := field1154
			_t1777 := p.pretty_csv_locator_paths(opt_val1155)
		}
		field1156 := unwrapped_fields1153[1].(*string)
		if field1156 != nil {
			p.newline()
			opt_val1157 := *field1156
			_t1778 := p.pretty_csv_locator_inline_data(opt_val1157)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_locator_paths(msg []string) interface{} {
	flat1162 := nil
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		fields1159 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1159) == 0) {
			p.newline()
			for i1161, elem1160 := range fields1159 {
				if (i1161 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1160))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1164 := nil
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		fields1163 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1163))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1167 := nil
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_t1779 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1780 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1780
		}
		_t1781 := _t1779(msg)
		fields1165 := _t1781
		unwrapped_fields1166 := fields1165
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		_t1782 := p.pretty_config_dict(unwrapped_fields1166)
		_ = _t1782
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_columns(msg []*pb.CSVColumn) interface{} {
	flat1171 := nil
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		fields1168 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1168) == 0) {
			p.newline()
			for i1170, elem1169 := range fields1168 {
				if (i1170 > 0) {
					p.newline()
				}
				_t1783 := p.pretty_csv_column(elem1169)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_column(msg *pb.CSVColumn) interface{} {
	flat1179 := nil
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_t1784 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
		}
		_t1785 := _t1784(msg)
		fields1172 := _t1785
		unwrapped_fields1173 := fields1172
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1174 := unwrapped_fields1173[0].(string)
		p.write(p.formatStringValue(field1174))
		p.newline()
		field1175 := unwrapped_fields1173[1].(*pb.RelationId)
		_t1786 := p.pretty_relation_id(field1175)
		_ = _t1786
		p.newline()
		p.write("[")
		field1176 := unwrapped_fields1173[2].([]*pb.Type)
		for i1178, elem1177 := range field1176 {
			if (i1178 > 0) {
				p.newline()
			}
			_t1787 := p.pretty_type(elem1177)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_csv_asof(msg string) interface{} {
	flat1181 := nil
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		fields1180 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1180))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1184 := nil
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_t1788 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1789 := _t1788(msg)
		fields1182 := _t1789
		unwrapped_fields1183 := fields1182
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		_t1790 := p.pretty_fragment_id(unwrapped_fields1183)
		_ = _t1790
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_context(msg *pb.Context) interface{} {
	flat1189 := nil
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_t1791 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1792 := _t1791(msg)
		fields1185 := _t1792
		unwrapped_fields1186 := fields1185
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1186) == 0) {
			p.newline()
			for i1188, elem1187 := range unwrapped_fields1186 {
				if (i1188 > 0) {
					p.newline()
				}
				_t1793 := p.pretty_relation_id(elem1187)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1193 := nil
	if flat1193 != nil {
		p.write(*flat1193)
		return nil
	} else {
		fields1190 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1190) == 0) {
			p.newline()
			for i1192, elem1191 := range fields1190 {
				if (i1192 > 0) {
					p.newline()
				}
				_t1794 := p.pretty_read(elem1191)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_read(msg *pb.Read) interface{} {
	flat1204 := nil
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		_t1795 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1796 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1796 = _dollar_dollar.GetDemand()
			}
			return _t1796
		}
		_t1797 := _t1795(msg)
		deconstruct_result1202 := _t1797
		if deconstruct_result1202 != nil {
			unwrapped1203 := deconstruct_result1202
			_t1798 := p.pretty_demand(unwrapped1203)
		} else {
			_t1799 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1800 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1800 = _dollar_dollar.GetOutput()
				}
				return _t1800
			}
			_t1801 := _t1799(msg)
			deconstruct_result1200 := _t1801
			if deconstruct_result1200 != nil {
				unwrapped1201 := deconstruct_result1200
				_t1802 := p.pretty_output(unwrapped1201)
			} else {
				_t1803 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1804 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1804 = _dollar_dollar.GetWhatIf()
					}
					return _t1804
				}
				_t1805 := _t1803(msg)
				deconstruct_result1198 := _t1805
				if deconstruct_result1198 != nil {
					unwrapped1199 := deconstruct_result1198
					_t1806 := p.pretty_what_if(unwrapped1199)
				} else {
					_t1807 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1808 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1808 = _dollar_dollar.GetAbort()
						}
						return _t1808
					}
					_t1809 := _t1807(msg)
					deconstruct_result1196 := _t1809
					if deconstruct_result1196 != nil {
						unwrapped1197 := deconstruct_result1196
						_t1810 := p.pretty_abort(unwrapped1197)
					} else {
						_t1811 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1812 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1812 = _dollar_dollar.GetExport()
							}
							return _t1812
						}
						_t1813 := _t1811(msg)
						deconstruct_result1194 := _t1813
						if deconstruct_result1194 != nil {
							unwrapped1195 := deconstruct_result1194
							_t1814 := p.pretty_export(unwrapped1195)
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

func (p *Parser) pretty_demand(msg *pb.Demand) interface{} {
	flat1207 := nil
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		_t1815 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1816 := _t1815(msg)
		fields1205 := _t1816
		unwrapped_fields1206 := fields1205
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		_t1817 := p.pretty_relation_id(unwrapped_fields1206)
		_ = _t1817
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_output(msg *pb.Output) interface{} {
	flat1212 := nil
	if flat1212 != nil {
		p.write(*flat1212)
		return nil
	} else {
		_t1818 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1819 := _t1818(msg)
		fields1208 := _t1819
		unwrapped_fields1209 := fields1208
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1210 := unwrapped_fields1209[0].(string)
		_t1820 := p.pretty_name(field1210)
		_ = _t1820
		p.newline()
		field1211 := unwrapped_fields1209[1].(*pb.RelationId)
		_t1821 := p.pretty_relation_id(field1211)
		_ = _t1821
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1217 := nil
	if flat1217 != nil {
		p.write(*flat1217)
		return nil
	} else {
		_t1822 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1823 := _t1822(msg)
		fields1213 := _t1823
		unwrapped_fields1214 := fields1213
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1215 := unwrapped_fields1214[0].(string)
		_t1824 := p.pretty_name(field1215)
		_ = _t1824
		p.newline()
		field1216 := unwrapped_fields1214[1].(*pb.Epoch)
		_t1825 := p.pretty_epoch(field1216)
		_ = _t1825
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_abort(msg *pb.Abort) interface{} {
	flat1223 := nil
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		_t1826 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1827 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1827 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1827, _dollar_dollar.GetRelationId()}
		}
		_t1828 := _t1826(msg)
		fields1218 := _t1828
		unwrapped_fields1219 := fields1218
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1220 := unwrapped_fields1219[0].(*string)
		if field1220 != nil {
			p.newline()
			opt_val1221 := *field1220
			_t1829 := p.pretty_name(opt_val1221)
		}
		p.newline()
		field1222 := unwrapped_fields1219[1].(*pb.RelationId)
		_t1830 := p.pretty_relation_id(field1222)
		_ = _t1830
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_export(msg *pb.Export) interface{} {
	flat1226 := nil
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_t1831 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1832 := _t1831(msg)
		fields1224 := _t1832
		unwrapped_fields1225 := fields1224
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		_t1833 := p.pretty_export_csv_config(unwrapped_fields1225)
		_ = _t1833
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1232 := nil
	if flat1232 != nil {
		p.write(*flat1232)
		return nil
	} else {
		_t1834 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			_t1835 := p.deconstruct_export_csv_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1835}
		}
		_t1836 := _t1834(msg)
		fields1227 := _t1836
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("export_csv_config")
		p.indentSexp()
		p.newline()
		field1229 := unwrapped_fields1228[0].(string)
		_t1837 := p.pretty_export_csv_path(field1229)
		_ = _t1837
		p.newline()
		field1230 := unwrapped_fields1228[1].([]*pb.ExportCSVColumn)
		_t1838 := p.pretty_export_csv_columns(field1230)
		_ = _t1838
		p.newline()
		field1231 := unwrapped_fields1228[2].([][]interface{})
		_t1839 := p.pretty_config_dict(field1231)
		_ = _t1839
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_export_csv_path(msg string) interface{} {
	flat1234 := nil
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		fields1233 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1233))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) interface{} {
	flat1238 := nil
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		fields1235 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1235) == 0) {
			p.newline()
			for i1237, elem1236 := range fields1235 {
				if (i1237 > 0) {
					p.newline()
				}
				_t1840 := p.pretty_export_csv_column(elem1236)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *Parser) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1243 := nil
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_t1841 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1842 := _t1841(msg)
		fields1239 := _t1842
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1241 := unwrapped_fields1240[0].(string)
		p.write(p.formatStringValue(field1241))
		p.newline()
		field1242 := unwrapped_fields1240[1].(*pb.RelationId)
		_t1843 := p.pretty_relation_id(field1242)
		_ = _t1843
		p.dedent()
		p.write(")")
	}
	return nil
}


// ProgramToStr pretty-prints a Transaction protobuf message to a string.
func ProgramToStr(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:           &buf,
		indentLevel: 0,
		atLineStart: true,
		debugInfo:   make(map[[2]uint64]string),
	}
	p.pretty_transaction(msg)
	p.newline()
	return p.getOutput()
}
