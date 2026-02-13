package lqp

import (
	"bytes"
	"fmt"
	"math"
	"math/big"
	"sort"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// PrettyParams holds parameters for pretty printing
type PrettyParams struct {
	w           *bytes.Buffer
	DebugInfo   map[string]string
	indentLevel int
}

// Some helper methods for pretty printing
func (pp PrettyParams) Write(s string) { pp.w.Write([]byte(s)) }

func (pp PrettyParams) SPACE()   { pp.w.Write([]byte(" ")) }
func (pp PrettyParams) NEWLINE() { pp.w.Write([]byte("\n")) }

// Go doesn't allow hsep and vsep to be a method of pp because it is generic over T
func hsep[T any](pp PrettyParams, x []T, sep string, f func(T)) {
	for i, item := range x {
		if i > 0 {
			pp.Write(sep)
		}
		f(item)
	}
}

func (pp PrettyParams) writeEscapedString(s string) {
	escaped := strings.ReplaceAll(s, "\\", "\\\\")
	escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
	escaped = strings.ReplaceAll(escaped, "\n", "\\n")
	escaped = strings.ReplaceAll(escaped, "\r", "\\r")
	escaped = strings.ReplaceAll(escaped, "\t", "\\t")
	pp.Write("\"")
	pp.Write(escaped)
	pp.Write("\"")
}
func vsep[T any](pp PrettyParams, x []T, sep string, f func(T)) {
	for i, item := range x {
		if i > 0 {
			pp.Write(sep)
			pp.NEWLINE()
		}
		f(item)
	}
}

func (pp PrettyParams) PARENS(f func(PrettyParams)) {
	pp.Write("(")
	f(pp)
	pp.Write(")")
}
func (pp PrettyParams) BRACKET(f func(PrettyParams)) {
	pp.Write("[")
	f(pp)
	pp.Write("]")
}
func (pp PrettyParams) BRACES(f func(PrettyParams)) {
	pp.Write("{")
	f(pp)
	pp.Write("}")
}
func (pp PrettyParams) INDENT(n int, f func(PrettyParams)) {
	indent := strings.Repeat(" ", n)

	var innerBuf bytes.Buffer
	innerPP := PrettyParams{&innerBuf, pp.DebugInfo, pp.indentLevel}
	f(innerPP)

	content := innerBuf.String()
	indentStr := strings.Repeat(indent, pp.indentLevel+1)

	lines := strings.Split(content, "\n")
	for i, line := range lines {
		if i > 0 {
			pp.w.Write([]byte("\n"))
		}
		// Don't add trailing spaces for empty lines
		if line != "" {
			pp.w.Write([]byte(indentStr + line))
		}
	}
}

func (pp PrettyParams) Dump() string { return pp.w.String() }

func (pp PrettyParams) idToName(rid *pb.RelationId) string {
	idStr := relationIdToString(rid)
	// Default behavior: print_names=true (use debug names if available)
	if len(pp.DebugInfo) == 0 {
		return idStr
	}
	if name, ok := pp.DebugInfo[idStr]; ok {
		return ":" + name
	}
	return idStr
}

// Main pretty printing function
func (pp PrettyParams) pprint(node interface{}) {
	switch n := node.(type) {
	case *pb.Transaction:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("transaction")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				if n.GetConfigure() != nil {
					pp.pprint(n.GetConfigure())
					pp.NEWLINE()
				}
				if n.GetSync() != nil {
					pp.pprint(n.GetSync())
					pp.NEWLINE()
				}
				for i, epoch := range n.GetEpochs() {
					if i > 0 {
						pp.NEWLINE()
					}
					pp.pprint(epoch)
				}
			})
		})

	case *pb.Configure:
		configDict := make(map[string]interface{})
		if n != nil {
			configDict["semantics_version"] = n.GetSemanticsVersion()
			ivmConfig := n.GetIvmConfig()
			if ivmConfig != nil && ivmConfig.GetLevel() != pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED {
				levelStr := ivmConfig.GetLevel().String()
				levelStr = strings.ToLower(strings.TrimPrefix(levelStr, "MAINTENANCE_LEVEL_"))
				configDict["ivm.maintenance_level"] = levelStr
			}
		}
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("configure")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.configDictToStr(configDict)
			})
		})

	case *pb.Sync:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("sync")
			if len(n.GetFragments()) > 0 {
				pp.SPACE()
				hsep(pp, n.GetFragments(), " ", func(id *pb.FragmentId) {
					pp.pprint(id)
				})
			}
		})

	case *pb.Declaration:
		if def := n.GetDef(); def != nil {
			pp.pprint(def)
		} else if alg := n.GetAlgorithm(); alg != nil {
			pp.pprint(alg)
		} else if constraint := n.GetConstraint(); constraint != nil {
			pp.pprint(constraint)
		} else if data := n.GetData(); data != nil {
			pp.pprint(data)
		}

	case *pb.Def:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("def")
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.pprint(n.GetBody())
				})
				if len(n.GetAttrs()) != 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.Constraint:
		if fd := n.GetFunctionalDependency(); fd != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("functional_dependency")
				pp.SPACE()
				pp.pprint(n.GetName())
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(fd.GetGuard())
					})
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("keys")
						if len(fd.GetKeys()) > 0 {
							pp.SPACE()
							for i, v := range fd.GetKeys() {
								if i > 0 {
									pp.SPACE()
								}
								pp.pprint(v)
							}
						}
					})
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("values")
						if len(fd.GetValues()) > 0 {
							pp.SPACE()
							for i, v := range fd.GetValues() {
								if i > 0 {
									pp.SPACE()
								}
								pp.pprint(v)
							}
						}
					})
				})
			})
			return
		}

	case *pb.Algorithm:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("algorithm")
			if len(n.GetGlobal()) > 0 {
				pp.SPACE()
				hsep(pp, n.GetGlobal(), " ", func(id *pb.RelationId) {
					pp.pprint(id)
				})
			}
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) { pp.pprint(n.GetBody()) })
		})

	case *pb.Script:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("script")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				vsep(pp, n.GetConstructs(), "", func(id *pb.Construct) {
					pp.pprint(id)
				})
			})
		})

	case *pb.Data:
		if rel := n.GetRelEdb(); rel != nil {
			pp.pprint(rel)
		} else if betree := n.GetBetreeRelation(); betree != nil {
			pp.pprint(betree)
		} else if csv := n.GetCsvData(); csv != nil {
			pp.pprint(csv)
		}

	case *pb.RelEDB:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("rel_edb")
			pp.SPACE()
			pp.pprint(n.GetTargetId())
			pp.SPACE()
			pp.BRACKET(func(pp PrettyParams) {
				hsep(pp, n.GetPath(), " ", func(path string) {
					pp.pprint(path)
				})
			})
			pp.SPACE()
			pp.BRACKET(func(pp PrettyParams) {
				hsep(pp, n.GetTypes(), " ", func(t *pb.Type) {
					pp.pprint(t)
				})
			})
		})

	case *pb.BeTreeRelation:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("betree_relation")
			pp.SPACE()
			pp.pprint(n.GetName())
			info := n.GetRelationInfo()
			if info != nil {
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.pprint(info)
				})
			}
		})

	case *pb.BeTreeInfo:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("betree_info")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("key_types")
					if len(n.GetKeyTypes()) > 0 {
						pp.SPACE()
						hsep(pp, n.GetKeyTypes(), " ", func(t *pb.Type) {
							pp.pprint(t)
						})
					}
				})
				pp.NEWLINE()
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("value_types")
					if len(n.GetValueTypes()) > 0 {
						pp.SPACE()
						hsep(pp, n.GetValueTypes(), " ", func(t *pb.Type) {
							pp.pprint(t)
						})
					}
				})
				pp.NEWLINE()
				configDict := make(map[string]interface{})
				if storage := n.GetStorageConfig(); storage != nil {
					configDict["betree_config_epsilon"] = storage.GetEpsilon()
					configDict["betree_config_max_pivots"] = storage.GetMaxPivots()
					configDict["betree_config_max_deltas"] = storage.GetMaxDeltas()
					configDict["betree_config_max_leaf"] = storage.GetMaxLeaf()
				}
				if locator := n.GetRelationLocator(); locator != nil {
					if root := locator.GetRootPageid(); root != nil {
						configDict["betree_locator_root_pageid"] = rawString(fmt.Sprintf("0x%s", uint128ToHexString(root.GetLow(), root.GetHigh())))
					}
					inline := locator.GetInlineData()
					if len(inline) > 0 {
						configDict["betree_locator_inline_data"] = string(inline)
					}
					configDict["betree_locator_element_count"] = locator.GetElementCount()
					configDict["betree_locator_tree_height"] = locator.GetTreeHeight()
				}
				pp.configDictToStr(configDict)
			})
		})

	case *pb.CSVData:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("csv_data")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				printed := false
				printSection := func(f func()) {
					if printed {
						pp.NEWLINE()
					}
					f()
					printed = true
				}
				if locator := n.GetLocator(); locator != nil {
					printSection(func() { pp.pprint(locator) })
				}
				if config := n.GetConfig(); config != nil {
					printSection(func() { pp.pprint(config) })
				}
				printSection(func() {
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("columns")
						cols := n.GetColumns()
						if len(cols) > 0 {
							pp.NEWLINE()
							pp.INDENT(2, func(pp PrettyParams) {
								vsep(pp, cols, "", func(col *pb.CSVColumn) {
									pp.pprint(col)
								})
							})
						}
					})
				})
				printSection(func() {
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("asof")
						pp.SPACE()
						pp.pprint(n.GetAsof())
					})
				})
			})
		})

	case *pb.CSVLocator:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("csv_locator")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				if len(n.GetPaths()) > 0 {
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("paths")
						pp.SPACE()
						hsep(pp, n.GetPaths(), " ", func(path string) {
							pp.pprint(path)
						})
					})
				} else if inline := n.GetInlineData(); len(inline) > 0 {
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("inline_data")
						pp.SPACE()
						pp.pprint(string(inline))
					})
				}
			})
		})

	case *pb.CSVConfig:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("csv_config")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				configDict := make(map[string]interface{})
				configDict["csv_header_row"] = n.GetHeaderRow()
				configDict["csv_skip"] = n.GetSkip()
				if n.GetNewLine() != "" {
					configDict["csv_new_line"] = n.GetNewLine()
				}
				configDict["csv_delimiter"] = n.GetDelimiter()
				configDict["csv_quotechar"] = n.GetQuotechar()
				configDict["csv_escapechar"] = n.GetEscapechar()
				if n.GetComment() != "" {
					configDict["csv_comment"] = n.GetComment()
				}
				missingStrings := n.GetMissingStrings()
				if len(missingStrings) > 0 {
					configDict["csv_missing_strings"] = missingStrings[0]
				}
				configDict["csv_decimal_separator"] = n.GetDecimalSeparator()
				configDict["csv_encoding"] = n.GetEncoding()
				configDict["csv_compression"] = n.GetCompression()
				pp.configDictToStr(configDict)
			})
		})

	case *pb.CSVColumn:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("column")
			pp.SPACE()
			pp.pprint(n.GetColumnName())
			pp.SPACE()
			pp.pprint(n.GetTargetId())
			pp.SPACE()
			pp.BRACKET(func(pp PrettyParams) {
				hsep(pp, n.GetTypes(), " ", func(t *pb.Type) {
					pp.pprint(t)
				})
			})
		})

	case *pb.Construct:
		if loop := n.GetLoop(); loop != nil {
			pp.pprint(loop)
			return
		} else if instr := n.GetInstruction(); instr != nil {
			pp.pprint(instr)
			return
		}

	case *pb.Loop:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("loop")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("init")
					if len(n.GetInit()) > 0 {
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							vsep(pp, n.GetInit(), "", func(id *pb.Instruction) {
								pp.pprint(id)
							})
						})
					}
				})
				pp.NEWLINE()
				pp.pprint(n.GetBody())
			})
		})

	case *pb.Instruction:
		if assign := n.GetAssign(); assign != nil {
			pp.pprint(assign)
			return
		} else if upsert := n.GetUpsert(); upsert != nil {
			pp.pprint(upsert)
			return
		} else if brk := n.GetBreak(); brk != nil {
			pp.pprint(brk)
			return
		} else if monoidDef := n.GetMonoidDef(); monoidDef != nil {
			pp.pprint(monoidDef)
			return
		} else if monusDef := n.GetMonusDef(); monusDef != nil {
			pp.pprint(monusDef)
			return
		}

	case *pb.Assign:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("assign")
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.pprint(n.GetBody())
				})
				if len(n.GetAttrs()) > 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.Break:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("break")
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.pprint(n.GetBody())
				})
				if len(n.GetAttrs()) > 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.Upsert:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("upsert")
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				body := n.GetBody()
				if n.GetValueArity() == 0 {
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(body)
					})
				} else {
					partition := len(body.GetVars()) - int(n.GetValueArity())
					lvars := body.GetVars()[:partition]
					rvars := body.GetVars()[partition:]
					pp.PARENS(func(pp PrettyParams) {
						pp.BRACKET(func(pp PrettyParams) {
							hsep(pp, lvars, " ", func(x *pb.Binding) { pp.pprint(x) })
							pp.SPACE()
							pp.Write("|")
							pp.SPACE()
							hsep(pp, rvars, " ", func(x *pb.Binding) { pp.pprint(x) })
						})
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							pp.pprint(body.GetValue())
						})
					})
				}
				if len(n.GetAttrs()) > 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.MonoidDef:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("monoid")
			pp.SPACE()
			pp.pprint(n.GetMonoid())
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				body := n.GetBody()
				if n.GetValueArity() == 0 {
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(body)
					})
				} else {
					partition := len(body.GetVars()) - int(n.GetValueArity())
					lvars := body.GetVars()[:partition]
					rvars := body.GetVars()[partition:]
					pp.PARENS(func(pp PrettyParams) {
						pp.BRACKET(func(pp PrettyParams) {
							hsep(pp, lvars, " ", func(x *pb.Binding) { pp.pprint(x) })
							pp.SPACE()
							pp.Write("|")
							pp.SPACE()
							hsep(pp, rvars, " ", func(x *pb.Binding) { pp.pprint(x) })
						})
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							pp.pprint(body.GetValue())
						})
					})
				}
				if len(n.GetAttrs()) > 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.MonusDef:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("monus")
			pp.SPACE()
			pp.pprint(n.GetMonoid())
			pp.SPACE()
			pp.pprint(n.GetName())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				body := n.GetBody()
				if n.GetValueArity() == 0 {
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(body)
					})
				} else {
					partition := len(body.GetVars()) - int(n.GetValueArity())
					lvars := body.GetVars()[:partition]
					rvars := body.GetVars()[partition:]
					pp.PARENS(func(pp PrettyParams) {
						pp.BRACKET(func(pp PrettyParams) {
							hsep(pp, lvars, " ", func(x *pb.Binding) { pp.pprint(x) })
							pp.SPACE()
							pp.Write("|")
							pp.SPACE()
							hsep(pp, rvars, " ", func(x *pb.Binding) { pp.pprint(x) })
						})
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							pp.pprint(body.GetValue())
						})
					})
				}
				if len(n.GetAttrs()) > 0 {
					pp.NEWLINE()
					pp.pprint(n.GetAttrs())
				}
			})
		})

	case *pb.Monoid:
		if n.GetOrMonoid() != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("or")
			})
		} else if minMonoid := n.GetMinMonoid(); minMonoid != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("min")
				pp.SPACE()
				pp.pprint(minMonoid.GetType())
			})
		} else if maxMonoid := n.GetMaxMonoid(); maxMonoid != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("max")
				pp.SPACE()
				pp.pprint(maxMonoid.GetType())
			})
		} else if sumMonoid := n.GetSumMonoid(); sumMonoid != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("sum")
				pp.SPACE()
				pp.pprint(sumMonoid.GetType())
			})
		}

	case *pb.Type:
		switch {
		case n.GetUnspecifiedType() != nil:
			pp.Write("UNSPECIFIED")
		case n.GetStringType() != nil:
			pp.Write("STRING")
		case n.GetIntType() != nil:
			pp.Write("INT")
		case n.GetFloatType() != nil:
			pp.Write("FLOAT")
		case n.GetUint128Type() != nil:
			pp.Write("UINT128")
		case n.GetInt128Type() != nil:
			pp.Write("INT128")
		case n.GetDateType() != nil:
			pp.Write("DATE")
		case n.GetDatetimeType() != nil:
			pp.Write("DATETIME")
		case n.GetMissingType() != nil:
			pp.Write("MISSING")
		case n.GetDecimalType() != nil:
			pp.PARENS(func(pp PrettyParams) {
				decType := n.GetDecimalType()
				pp.Write("DECIMAL")
				pp.SPACE()
				pp.pprint(decType.GetPrecision())
				pp.SPACE()
				pp.pprint(decType.GetScale())
			})
		case n.GetBooleanType() != nil:
			pp.Write("BOOLEAN")
		default:
			pp.Write("UNKNOWN")
		}

	case *pb.Abstraction:
		pp.BRACKET(func(pp PrettyParams) {
			hsep(pp, n.GetVars(), " ", func(x *pb.Binding) { pp.pprint(x) })
		})
		pp.NEWLINE()
		pp.INDENT(2, func(pp PrettyParams) { pp.pprint(n.GetValue()) })
	case *pb.Formula:
		if exists := n.GetExists(); exists != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("exists")
				pp.SPACE()
				pp.BRACKET(func(pp PrettyParams) {
					hsep(pp, exists.GetBody().GetVars(), " ", func(x *pb.Binding) {
						pp.pprint(x)
					})
				})
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.pprint(exists.GetBody().GetValue())
				})
			})
		} else if reduce := n.GetReduce(); reduce != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("reduce")
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(reduce.GetOp())
					})
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.pprint(reduce.GetBody())
					})
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("terms")
						if len(reduce.GetTerms()) > 0 {
							pp.SPACE()
							hsep(pp, reduce.GetTerms(), " ", func(id *pb.Term) {
								pp.pprint(id)
							})
						}
					})
				})
			})
		} else if conj := n.GetConjunction(); conj != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("and")
				if len(conj.GetArgs()) > 0 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, conj.GetArgs(), "", func(id *pb.Formula) {
							pp.pprint(id)
						})
					})
				}
			})
		} else if disj := n.GetDisjunction(); disj != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("or")
				if len(disj.GetArgs()) > 0 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, disj.GetArgs(), "", func(id *pb.Formula) {
							pp.pprint(id)
						})
					})
				}
			})
		} else if not := n.GetNot(); not != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("not")
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.pprint(not.GetArg())
				})
			})
		} else if ffi := n.GetFfi(); ffi != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("ffi")
				pp.SPACE()
				pp.Write(":")
				pp.Write(ffi.GetName())
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("args")
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							// Wrap each abstraction in PARENS
							for i, arg := range ffi.GetArgs() {
								if i > 0 {
									pp.NEWLINE()
								}
								pp.PARENS(func(pp PrettyParams) {
									pp.pprint(arg)
								})
							}
						})
					})
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("terms")
						if len(ffi.GetTerms()) > 0 {
							pp.SPACE()
							hsep(pp, ffi.GetTerms(), " ", func(id *pb.Term) {
								pp.pprint(id)
							})
						}
					})
				})
			})
		} else if atom := n.GetAtom(); atom != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("atom")
				pp.SPACE()
				pp.pprint(atom.GetName())
				if len(atom.GetTerms()) > 4 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, atom.GetTerms(), "", func(id *pb.Term) {
							pp.pprint(id)
						})
					})
				} else {
					pp.SPACE()
					hsep(pp, atom.GetTerms(), " ", func(id *pb.Term) {
						pp.pprint(id)
					})
				}
			})
		} else if pragma := n.GetPragma(); pragma != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("pragma")
				pp.SPACE()
				pp.Write(":")
				pp.Write(pragma.GetName())
				if len(pragma.GetTerms()) > 4 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, pragma.GetTerms(), "", func(id *pb.Term) {
							pp.pprint(id)
						})
					})
				} else {
					pp.SPACE()
					hsep(pp, pragma.GetTerms(), " ", func(id *pb.Term) {
						pp.pprint(id)
					})
				}
			})
		} else if primitive := n.GetPrimitive(); primitive != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("primitive")
				pp.SPACE()
				pp.Write(":")
				pp.Write(primitive.GetName())
				if len(primitive.GetTerms()) > 4 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, primitive.GetTerms(), "", func(id *pb.RelTerm) {
							pp.pprint(id)
						})
					})
				} else {
					pp.SPACE()
					hsep(pp, primitive.GetTerms(), " ", func(id *pb.RelTerm) {
						pp.pprint(id)
					})
				}
			})
		} else if relAtom := n.GetRelAtom(); relAtom != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("relatom")
				pp.SPACE()
				pp.Write(":")
				pp.Write(relAtom.GetName())
				if len(relAtom.GetTerms()) > 4 {
					pp.NEWLINE()
					pp.INDENT(2, func(pp PrettyParams) {
						vsep(pp, relAtom.GetTerms(), "", func(id *pb.RelTerm) {
							pp.pprint(id)
						})
					})
				} else {
					pp.SPACE()
					hsep(pp, relAtom.GetTerms(), " ", func(id *pb.RelTerm) {
						pp.pprint(id)
					})
				}
			})
		} else if cast := n.GetCast(); cast != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("cast")
				pp.SPACE()
				pp.pprint(cast.GetInput())
				pp.SPACE()
				pp.pprint(cast.GetResult())
			})
		}

	case *pb.Term:
		if v := n.GetVar(); v != nil {
			pp.Write(v.GetName())
		} else if val := n.GetConstant(); val != nil {
			pp.pprint(val)
		}

	case *pb.RelTerm:
		if term := n.GetTerm(); term != nil {
			pp.pprint(term)
			return
		} else if spec := n.GetSpecializedValue(); spec != nil {
			pp.Write("#")
			pp.pprint(spec)
		}

	case *pb.Attribute:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("attribute")
			pp.SPACE()
			pp.Write(":")
			pp.Write(n.GetName())
			if len(n.GetArgs()) > 0 {
				pp.SPACE()
				hsep(pp, n.GetArgs(), " ", func(id *pb.Value) {
					pp.pprint(id)
				})
			}
		})
	case *pb.RelationId:
		name := pp.idToName(n)
		pp.Write(name)

	case *pb.Write:
		if define := n.GetDefine(); define != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("define")
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) { pp.pprint(define.GetFragment()) })
			})
		} else if undef := n.GetUndefine(); undef != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("undefine")
				pp.SPACE()
				pp.pprint(undef.GetFragmentId())
			})
		} else if ctx := n.GetContext(); ctx != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("context")
				pp.SPACE()
				pp.BRACKET(func(pp PrettyParams) {
					hsep(pp, ctx.GetRelations(), " ", func(id *pb.RelationId) {
						pp.pprint(id)
					})
				})
			})
		}

	case *pb.FragmentId:
		// Decode fragment ID as string (it's stored as UTF-8 bytes)
		idStr := string(n.GetId())
		if idStr == "" {
			idStr = "empty"
		}
		pp.Write(":")
		pp.Write(idStr)

	case *pb.Read:
		if demand := n.GetDemand(); demand != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("demand")
				pp.SPACE()
				pp.pprint(demand.GetRelationId())
			})
		} else if output := n.GetOutput(); output != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("output")
				pp.SPACE()
				pp.Write(":")
				pp.Write(output.GetName())
				pp.SPACE()
				pp.pprint(output.GetRelationId())
			})
		} else if export := n.GetExport(); export != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("export")
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					if csvConfig := export.GetCsvConfig(); csvConfig != nil {
						pp.pprint(csvConfig)
					} else if csvTableConfig := export.GetCsvTableConfig(); csvTableConfig != nil {
						pp.pprint(csvTableConfig)
					}
				})
			})
		} else if whatIf := n.GetWhatIf(); whatIf != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("whatif")
				pp.SPACE()
				pp.Write(":")
				pp.Write(whatIf.GetBranch())
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) { pp.pprint(whatIf.GetEpoch()) })
			})
		} else if abort := n.GetAbort(); abort != nil {
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("abort")
				pp.SPACE()
				pp.Write(":")
				pp.Write(abort.GetName())
				pp.SPACE()
				pp.pprint(abort.GetRelationId())
			})
		}

	case *pb.ExportCSVConfig:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("export_csv_config")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("path")
					pp.SPACE()
					pp.pprint(n.GetPath())
				})
				pp.NEWLINE()
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("columns")
					pp.SPACE()
					hsep(pp, n.GetDataColumns(), " ", func(x *pb.ExportCSVColumn) {
						pp.pprint(x)
					})
				})
				pp.NEWLINE()
				configDict := make(map[string]interface{})
				configDict["partition_size"] = n.GetPartitionSize()
				configDict["compression"] = n.GetCompression()
				if n.GetSyntaxHeaderRow() {
					configDict["syntax_header_row"] = 1
				} else {
					configDict["syntax_header_row"] = 0
				}
				configDict["syntax_missing_string"] = n.GetSyntaxMissingString()
				configDict["syntax_delim"] = n.GetSyntaxDelim()
				configDict["syntax_quotechar"] = n.GetSyntaxQuotechar()
				configDict["syntax_escapechar"] = n.GetSyntaxEscapechar()
				pp.configDictToStr(configDict)
			})
		})

	case *pb.ExportCSVColumn:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("column")
			pp.SPACE()
			pp.pprint(n.GetColumnName())
			pp.SPACE()
			pp.pprint(n.GetColumnData())
		})

	case *pb.ExportCSVTableConfig:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("export_csv_table_config")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("path")
					pp.SPACE()
					pp.pprint(n.GetPath())
				})
				pp.NEWLINE()
				pp.PARENS(func(pp PrettyParams) {
					pp.Write("export_def")
					pp.SPACE()
					pp.pprint(n.GetTableDef())
				})
				pp.NEWLINE()
				configDict := make(map[string]interface{})
				configDict["partition_size"] = n.GetPartitionSize()
				configDict["compression"] = n.GetCompression()
				if n.GetSyntaxHeaderRow() {
					configDict["syntax_header_row"] = 1
				} else {
					configDict["syntax_header_row"] = 0
				}
				configDict["syntax_missing_string"] = n.GetSyntaxMissingString()
				configDict["syntax_delim"] = n.GetSyntaxDelim()
				configDict["syntax_quotechar"] = n.GetSyntaxQuotechar()
				configDict["syntax_escapechar"] = n.GetSyntaxEscapechar()
				pp.configDictToStr(configDict)
			})
		})

	case *pb.Epoch:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("epoch")
			pp.INDENT(2, func(pp PrettyParams) {
				if len(n.GetWrites()) > 0 {
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("writes")
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							vsep(pp, n.GetWrites(), "", func(w *pb.Write) {
								pp.pprint(w)
							})
						})
					})
				}
				if len(n.GetReads()) > 0 {
					pp.NEWLINE()
					pp.PARENS(func(pp PrettyParams) {
						pp.Write("reads")
						pp.NEWLINE()
						pp.INDENT(2, func(pp PrettyParams) {
							vsep(pp, n.GetReads(), "", func(w *pb.Read) {
								pp.pprint(w)
							})
						})
					})
				}
			})
		})

	case *pb.Fragment:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("fragment")
			pp.SPACE()
			pp.pprint(n.GetId())
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				vsep(pp, n.GetDeclarations(), "", func(id *pb.Declaration) {
					pp.pprint(id)
				})
			})
		})

	case *pb.Binding:
		pp.Write(n.GetVar().GetName())
		pp.Write("::")
		pp.pprint(n.GetType())

	case *pb.Var:
		pp.Write(n.GetName())

	case *pb.Value:
		// Handle Value oneof - check the actual oneof type
		switch n.GetValue().(type) {
		case *pb.Value_StringValue:
			pp.writeEscapedString(n.GetStringValue())
		case *pb.Value_IntValue:
			pp.Write(fmt.Sprintf("%d", n.GetIntValue()))
		case *pb.Value_FloatValue:
			floatVal := n.GetFloatValue()
			if math.IsInf(floatVal, 0) {
				pp.Write("inf")
			} else if math.IsNaN(floatVal) {
				pp.Write("nan")
			} else if floatVal == float64(int64(floatVal)) {
				pp.Write(fmt.Sprintf("%.1f", floatVal))
			} else {
				pp.Write(fmt.Sprintf("%v", floatVal))
			}
		case *pb.Value_Uint128Value:
			uint128 := n.GetUint128Value()
			pp.Write("0x")
			pp.Write(uint128ToHexString(uint128.GetLow(), uint128.GetHigh()))
		case *pb.Value_Int128Value:
			int128 := n.GetInt128Value()
			result := int128ToString(int128.GetLow(), int128.GetHigh())
			pp.Write(result)
			pp.Write("i128")
		case *pb.Value_MissingValue:
			pp.Write("missing")
		case *pb.Value_DateValue:
			date := n.GetDateValue()
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("date")
				pp.SPACE()
				pp.Write(fmt.Sprintf("%d %d %d", date.GetYear(), date.GetMonth(), date.GetDay()))
			})
		case *pb.Value_DatetimeValue:
			datetime := n.GetDatetimeValue()
			pp.PARENS(func(pp PrettyParams) {
				pp.Write("datetime")
				pp.SPACE()
				pp.Write(fmt.Sprintf("%d %d %d %d %d %d %d",
					datetime.GetYear(), datetime.GetMonth(), datetime.GetDay(),
					datetime.GetHour(), datetime.GetMinute(), datetime.GetSecond(),
					datetime.GetMicrosecond()))
			})
		case *pb.Value_DecimalValue:
			decimal := n.GetDecimalValue()
			int128Val := decimal.GetValue()
			if int128Val != nil {
				// Get the raw integer value (using int128 for proper sign handling)
				rawValue := int128ToString(int128Val.GetLow(), int128Val.GetHigh())
				precision := decimal.GetPrecision()
				scale := decimal.GetScale()

				// Handle negative sign separately
				isNegative := strings.HasPrefix(rawValue, "-")
				if isNegative {
					rawValue = rawValue[1:] // Remove the negative sign temporarily
				}

				// Format as decimal with proper placement of decimal point
				// The raw value is the number * 10^scale
				// We need to insert a decimal point 'scale' digits from the right
				var decStr string
				if scale == 0 {
					// No decimal point needed
					decStr = rawValue
				} else {
					// Need to add decimal point
					if len(rawValue) <= int(scale) {
						// Need leading zeros: e.g., "5" with scale 3 -> "0.005"
						leadingZeros := int(scale) - len(rawValue)
						decStr = "0." + strings.Repeat("0", leadingZeros) + rawValue
					} else {
						// Insert decimal point: e.g., "12345" with scale 3 -> "12.345"
						insertPos := len(rawValue) - int(scale)
						decStr = rawValue[:insertPos] + "." + rawValue[insertPos:]
					}
				}

				// Add back the negative sign if needed
				if isNegative {
					decStr = "-" + decStr
				}

				pp.Write(decStr)
				pp.Write("d")
				pp.Write(fmt.Sprintf("%d", precision))
			}
		case *pb.Value_BooleanValue:
			if n.GetBooleanValue() {
				pp.Write("true")
			} else {
				pp.Write("false")
			}
		}

	case []*pb.Attribute:
		pp.PARENS(func(pp PrettyParams) {
			pp.Write("attrs")
			pp.NEWLINE()
			pp.INDENT(2, func(pp PrettyParams) {
				vsep(pp, n, "", func(id *pb.Attribute) {
					pp.pprint(id)
				})
			})
		})

	case string:
		pp.writeEscapedString(n)

	case int:
		pp.Write(fmt.Sprintf("%d", n))

	case int32:
		pp.Write(fmt.Sprintf("%d", n))

	case int64:
		pp.Write(fmt.Sprintf("%d", n))

	case uint32:
		pp.Write(fmt.Sprintf("%d", n))

	case uint64:
		pp.Write(fmt.Sprintf("%d", n))

	default:
		panic(fmt.Sprintf("pprint not implemented for %T", node))
	}
}

// Small traversal to collect DebugInfos
func collectDebugInfos(node interface{}) map[string]string {
	debugInfos := make(map[string]string)

	switch n := node.(type) {
	case *pb.Fragment:
		debugInfo := n.GetDebugInfo()
		if debugInfo != nil {
			ids := debugInfo.GetIds()
			names := debugInfo.GetOrigNames()
			for i, id := range ids {
				if i < len(names) {
					debugInfos[relationIdToString(id)] = names[i]
				}
			}
		}
	case *pb.Transaction:
		for _, epoch := range n.GetEpochs() {
			for _, write := range epoch.GetWrites() {
				if define := write.GetDefine(); define != nil {
					for k, v := range collectDebugInfos(define.GetFragment()) {
						debugInfos[k] = v
					}
				}
			}
		}
	}

	return debugInfos
}

type rawString string

func writeConfigValue(pp PrettyParams, value interface{}) {
	switch v := value.(type) {
	case rawString:
		pp.Write(string(v))
	case string:
		pp.Write(fmt.Sprintf("%q", v))
	default:
		pp.Write(fmt.Sprintf("%v", v))
	}
}

func (pp PrettyParams) configDictToStr(config map[string]interface{}) {
	keys := make([]string, 0, len(config))
	for k := range config {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	pp.BRACES(func(pp PrettyParams) {
		pp.SPACE()
		for i, k := range keys {
			if i > 0 {
				pp.NEWLINE()
				pp.INDENT(2, func(pp PrettyParams) {
					pp.Write(":")
					pp.Write(k)
					pp.SPACE()
					writeConfigValue(pp, config[k])
				})
			} else {
				pp.Write(":")
				pp.Write(k)
				pp.SPACE()
				writeConfigValue(pp, config[k])
			}
		}
	})
}

// Value-specific print functions
func uint128ToString(low, high uint64) string {
	if high == 0 {
		return fmt.Sprintf("%d", low)
	}
	// Convert to big.Int for proper display
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

func relationIdToString(rid *pb.RelationId) string {
	return "0x" + uint128ToHexString(rid.GetIdLow(), rid.GetIdHigh())
}

// Entry point
func ProgramToStr(node *pb.Transaction) string {
	debugInfo := collectDebugInfos(node)
	var buf bytes.Buffer

	pp := PrettyParams{&buf, debugInfo, 0}
	pp.pprint(node)
	pp.NEWLINE()
	return pp.Dump()
}
