package lqp

import (
	"fmt"
	"math"
	"math/big"
	"sort"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// Some helper functions for pretty
func SIND() string                 { return "  " }
func LPAREN() string               { return "(" }
func RPAREN() string               { return ")" }
func LBRACKET() string             { return "[" }
func RBRACKET() string             { return "]" }
func Indentation(level int) string { return strings.Repeat(SIND(), level) }

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
	return uint128ToString(rid.GetIdLow(), rid.GetIdHigh())
}

func ProgramToStr(node *pb.Transaction) string {
	s := LPAREN() + "transaction"

	// Build configure section
	configDict := make(map[string]interface{})
	config := node.GetConfigure()
	if config != nil {
		configDict["semantics_version"] = config.GetSemanticsVersion()
		ivmConfig := config.GetIvmConfig()
		if ivmConfig != nil && ivmConfig.GetLevel() != pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED {
			levelStr := ivmConfig.GetLevel().String()
			levelStr = strings.ToLower(strings.TrimPrefix(levelStr, "MAINTENANCE_LEVEL_"))
			configDict["ivm.maintenance_level"] = levelStr
		}
	}

	s += "\n" + Indentation(1) + LPAREN() + "configure" + "\n"
	s += configDictToStr(configDict, 2)
	s += RPAREN()

	debugInfo := collectDebugInfos(node)

	sync := node.GetSync()
	if sync != nil {
		s += "\n" + Indentation(1) + LPAREN() + "sync"
		if len(sync.GetFragments()) > 0 {
			s += " " + fragmentIdList(sync.GetFragments(), 0, " ", debugInfo)
		}
		s += RPAREN()
	}

	for _, epoch := range node.GetEpochs() {
		s += "\n" + Indentation(1) + LPAREN() + "epoch"

		if len(epoch.GetWrites()) > 0 {
			s += "\n" + Indentation(2) + LPAREN() + "writes" + "\n"
			s += writeList(epoch.GetWrites(), 3, "\n", debugInfo)
			s += RPAREN()
		}

		if len(epoch.GetReads()) > 0 {
			s += "\n" + Indentation(2) + LPAREN() + "reads" + "\n"
			s += readList(epoch.GetReads(), 3, "\n", debugInfo)
			s += RPAREN()
		}

		s += RPAREN()
	}
	s += RPAREN()
	s += "\n"

	return s
}

func configDictToStr(config map[string]interface{}, indentLevel int) string {
	ind := Indentation(indentLevel)

	if len(config) == 0 {
		return ind + "{}"
	}

	// Sort keys for deterministic output
	keys := make([]string, 0, len(config))
	for k := range config {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	configStr := ind + "{" + SIND()[1:]
	for i, k := range keys {
		if i > 0 {
			configStr += "\n" + ind + SIND()
		}
		configStr += fmt.Sprintf(":%s %s", k, valueToStr(config[k], 0, make(map[string]string)))
	}
	configStr += "}"

	return configStr
}

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

func fragmentToStr(node *pb.Fragment, indentLevel int, debugInfo map[string]string) string {
	ind := Indentation(indentLevel)

	// Merge debug info
	dbgInfo := node.GetDebugInfo()
	if dbgInfo != nil {
		ids := dbgInfo.GetIds()
		names := dbgInfo.GetOrigNames()
		for i, id := range ids {
			if i < len(names) {
				debugInfo[relationIdToString(id)] = names[i]
			}
		}
	}

	declarationsStr := declarationList(node.GetDeclarations(), indentLevel+1, "\n", debugInfo)

	return ind + LPAREN() + "fragment" + " " +
		toStr(node.GetId(), 0, debugInfo) + "\n" +
		declarationsStr +
		RPAREN()
}

func toStr(node interface{}, indentLevel int, debugInfo map[string]string) string {
	ind := Indentation(indentLevel)
	lqp := ""

	switch n := node.(type) {
	case *pb.Declaration:
		// Handle Declaration oneof
		if def := n.GetDef(); def != nil {
			return toStr(def, indentLevel, debugInfo)
		} else if alg := n.GetAlgorithm(); alg != nil {
			return toStr(alg, indentLevel, debugInfo)
		} else if constraint := n.GetConstraint(); constraint != nil {
			return toStr(constraint, indentLevel, debugInfo)
		}

	case *pb.Def:
		lqp += ind + LPAREN() + "def" + " " + toStr(n.GetName(), 0, debugInfo) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, debugInfo)
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.Constraint:
		if fd := n.GetFunctionalDependency(); fd != nil {
			return toStr(fd, indentLevel, debugInfo)
		}

	case *pb.FunctionalDependency:
		lqp += ind + LPAREN() + "functional_dependency" + "\n"
		lqp += toStr(n.GetGuard(), indentLevel+1, debugInfo) + "\n"
		lqp += ind + SIND() + LPAREN() + "keys"
		if len(n.GetKeys()) > 0 {
			lqp += " "
			for i, v := range n.GetKeys() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(v, 0, debugInfo)
			}
		}
		lqp += RPAREN() + "\n"
		lqp += ind + SIND() + LPAREN() + "values"
		if len(n.GetValues()) > 0 {
			lqp += " "
			for i, v := range n.GetValues() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(v, 0, debugInfo)
			}
		}
		lqp += RPAREN() + RPAREN()

	case *pb.Algorithm:
		lqp += ind + LPAREN() + "algorithm"
		if len(n.GetGlobal()) > 4 {
			lqp += "\n" + ind + SIND() + relationIdList(n.GetGlobal(), indentLevel+2, "\n", debugInfo) + "\n"
		} else {
			lqp += " " + relationIdList(n.GetGlobal(), 0, " ", debugInfo) + "\n"
		}
		lqp += toStr(n.GetBody(), indentLevel+1, debugInfo)
		lqp += RPAREN()

	case *pb.Script:
		lqp += ind + LPAREN() + "script" + "\n"
		lqp += constructList(n.GetConstructs(), indentLevel+1, "\n", debugInfo)
		lqp += RPAREN()

	case *pb.Construct:
		if loop := n.GetLoop(); loop != nil {
			return toStr(loop, indentLevel, debugInfo)
		} else if instr := n.GetInstruction(); instr != nil {
			return toStr(instr, indentLevel, debugInfo)
		}

	case *pb.Loop:
		lqp += ind + LPAREN() + "loop" + "\n"
		lqp += ind + SIND() + LPAREN() + "init"
		if len(n.GetInit()) > 0 {
			lqp += "\n" + instructionList(n.GetInit(), indentLevel+2, "\n", debugInfo)
		}
		lqp += RPAREN() + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, debugInfo)
		lqp += RPAREN()

	case *pb.Instruction:
		if assign := n.GetAssign(); assign != nil {
			return toStr(assign, indentLevel, debugInfo)
		} else if upsert := n.GetUpsert(); upsert != nil {
			return toStr(upsert, indentLevel, debugInfo)
		} else if brk := n.GetBreak(); brk != nil {
			return toStr(brk, indentLevel, debugInfo)
		} else if monoidDef := n.GetMonoidDef(); monoidDef != nil {
			return toStr(monoidDef, indentLevel, debugInfo)
		} else if monusDef := n.GetMonusDef(); monusDef != nil {
			return toStr(monusDef, indentLevel, debugInfo)
		}

	case *pb.Assign:
		lqp += ind + LPAREN() + "assign" + " " + toStr(n.GetName(), 0, debugInfo) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, debugInfo)
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.Break:
		lqp += ind + LPAREN() + "break" + " " + toStr(n.GetName(), 0, debugInfo) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, debugInfo)
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.Upsert:
		lqp += ind + LPAREN() + "upsert" + " " + toStr(n.GetName(), 0, debugInfo) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, debugInfo)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + Indentation(1) + LPAREN() + LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, debugInfo) + RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.MonoidDef:
		lqp += ind + LPAREN() + "monoid" + " " +
			toStr(n.GetMonoid(), 0, debugInfo) + " " +
			toStr(n.GetName(), 0, debugInfo) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, debugInfo)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + Indentation(1) + LPAREN() + LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, debugInfo) + RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.MonusDef:
		lqp += ind + LPAREN() + "monus" + " " +
			toStr(n.GetMonoid(), 0, debugInfo) + " " +
			toStr(n.GetName(), 0, debugInfo) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, debugInfo)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + Indentation(1) + LPAREN() + LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, debugInfo) + RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += RPAREN()
		} else {
			lqp += "\n" + Indentation(indentLevel+1) + LPAREN() + "attrs" + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + RPAREN()
		}

	case *pb.Monoid:
		if n.GetOrMonoid() != nil {
			lqp += "BOOL::OR"
		} else if minMonoid := n.GetMinMonoid(); minMonoid != nil {
			lqp += typeToStr(minMonoid.GetType()) + "::MIN"
		} else if maxMonoid := n.GetMaxMonoid(); maxMonoid != nil {
			lqp += typeToStr(maxMonoid.GetType()) + "::MAX"
		} else if sumMonoid := n.GetSumMonoid(); sumMonoid != nil {
			lqp += typeToStr(sumMonoid.GetType()) + "::SUM"
		}

	case *pb.Type:
		// Get the type name as string
		typeName := getTypeName(n)
		params := getTypeParameters(n)

		if len(params) == 0 {
			lqp += typeName
		} else {
			lqp += LPAREN() + typeName + " "
			paramStrs := make([]string, len(params))
			for i, p := range params {
				paramStrs[i] = fmt.Sprintf("%d", p)
			}
			lqp += strings.Join(paramStrs, " ")
			lqp += RPAREN()
		}

	case *pb.Abstraction:
		lqp += ind + LPAREN() + LBRACKET()
		lqp += varsToStr(n.GetVars())
		lqp += RBRACKET() + "\n"
		lqp += toStr(n.GetValue(), indentLevel+1, debugInfo) + RPAREN()

	case *pb.Formula:
		if exists := n.GetExists(); exists != nil {
			lqp += ind + LPAREN() + "exists" + " " + LBRACKET()
			lqp += varsToStr(exists.GetBody().GetVars())
			lqp += RBRACKET() + "\n"
			lqp += toStr(exists.GetBody().GetValue(), indentLevel+1, debugInfo) + RPAREN()
		} else if reduce := n.GetReduce(); reduce != nil {
			lqp += ind + LPAREN() + "reduce" + "\n"
			lqp += toStr(reduce.GetOp(), indentLevel+1, debugInfo) + "\n"
			lqp += toStr(reduce.GetBody(), indentLevel+1, debugInfo) + "\n"
			lqp += termListToStr(reduce.GetTerms(), indentLevel+1, debugInfo) + RPAREN()
		} else if conj := n.GetConjunction(); conj != nil {
			if len(conj.GetArgs()) == 0 {
				lqp += ind + LPAREN() + "and" + RPAREN()
			} else {
				lqp += ind + LPAREN() + "and" + "\n"
				lqp += formulaList(conj.GetArgs(), indentLevel+1, "\n", debugInfo) + RPAREN()
			}
		} else if disj := n.GetDisjunction(); disj != nil {
			if len(disj.GetArgs()) == 0 {
				lqp += ind + LPAREN() + "or" + RPAREN()
			} else {
				lqp += ind + LPAREN() + "or" + "\n"
				lqp += formulaList(disj.GetArgs(), indentLevel+1, "\n", debugInfo) + RPAREN()
			}
		} else if not := n.GetNot(); not != nil {
			lqp += ind + LPAREN() + "not" + "\n"
			lqp += toStr(not.GetArg(), indentLevel+1, debugInfo) + RPAREN()
		} else if ffi := n.GetFfi(); ffi != nil {
			lqp += ind + LPAREN() + "ffi" + " :" + ffi.GetName() + "\n"
			lqp += ind + SIND() + LPAREN() + "args" + "\n"
			lqp += abstractionList(ffi.GetArgs(), indentLevel+2, "\n", debugInfo)
			lqp += RPAREN() + "\n"
			lqp += termListToStr(ffi.GetTerms(), indentLevel+1, debugInfo) + RPAREN()
		} else if atom := n.GetAtom(); atom != nil {
			if len(atom.GetTerms()) > 4 {
				lqp += ind + LPAREN() + "atom" + " " + toStr(atom.GetName(), 0, debugInfo) + "\n"
				lqp += termList(atom.GetTerms(), indentLevel+1, "\n", debugInfo) + RPAREN()
			} else {
				lqp += ind + LPAREN() + "atom" + " " + toStr(atom.GetName(), 0, debugInfo) + " "
				lqp += termList(atom.GetTerms(), 0, " ", debugInfo) + RPAREN()
			}
		} else if pragma := n.GetPragma(); pragma != nil {
			terms := termList(pragma.GetTerms(), 0, " ", debugInfo)
			lqp += ind + LPAREN() + "pragma" + " :" + pragma.GetName() + " " + terms + RPAREN()
		} else if primitive := n.GetPrimitive(); primitive != nil {
			if len(primitive.GetTerms()) > 4 {
				lqp += ind + LPAREN() + "primitive" + " :" + primitive.GetName() + "\n"
				lqp += relTermList(primitive.GetTerms(), indentLevel+1, "\n", debugInfo) + RPAREN()
			} else {
				lqp += ind + LPAREN() + "primitive" + " :" + primitive.GetName() + " "
				lqp += relTermList(primitive.GetTerms(), 0, " ", debugInfo) + RPAREN()
			}
		} else if relAtom := n.GetRelAtom(); relAtom != nil {
			if len(relAtom.GetTerms()) > 4 {
				lqp += ind + LPAREN() + "relatom" + " :" + relAtom.GetName() + "\n"
				lqp += relTermList(relAtom.GetTerms(), indentLevel+1, "\n", debugInfo) + RPAREN()
			} else {
				lqp += ind + LPAREN() + "relatom" + " :" + relAtom.GetName() + " "
				lqp += relTermList(relAtom.GetTerms(), 0, " ", debugInfo) + RPAREN()
			}
		} else if cast := n.GetCast(); cast != nil {
			lqp += ind + LPAREN() + "cast" + " " +
				toStr(cast.GetInput(), 0, debugInfo) + " " +
				toStr(cast.GetResult(), 0, debugInfo) + RPAREN()
		}

	case *pb.Term:
		if v := n.GetVar(); v != nil {
			lqp += ind + v.GetName()
		} else if val := n.GetConstant(); val != nil {
			lqp += toStr(val, indentLevel, debugInfo)
		}

	case *pb.RelTerm:
		if term := n.GetTerm(); term != nil {
			return toStr(term, indentLevel, debugInfo)
		} else if spec := n.GetSpecializedValue(); spec != nil {
			lqp += "#" + toStr(spec, 0, make(map[string]string))
		}

	case *pb.Attribute:
		argsStr := valueList(n.GetArgs(), 0, " ", debugInfo)
		space := ""
		if argsStr != "" {
			space = " "
		}
		lqp += ind + LPAREN() + "attribute" + " :" + n.GetName() + space + argsStr + RPAREN()

	case *pb.RelationId:
		name := idToName(debugInfo, n)
		lqp += ind + name

	case *pb.Write:
		if define := n.GetDefine(); define != nil {
			lqp += ind + LPAREN() + "define" + "\n" +
				toStr(define.GetFragment(), indentLevel+1, debugInfo) + RPAREN()
		} else if undef := n.GetUndefine(); undef != nil {
			lqp += ind + LPAREN() + "undefine" + " " +
				toStr(undef.GetFragmentId(), 0, debugInfo) + RPAREN()
		} else if ctx := n.GetContext(); ctx != nil {
			lqp += ind + LPAREN() + "context" + " " +
				relationIdList(ctx.GetRelations(), 0, " ", debugInfo) + RPAREN()
		}

	case *pb.FragmentId:
		// Decode fragment ID as string (it's stored as UTF-8 bytes)
		idStr := string(n.GetId())
		if idStr == "" {
			idStr = "empty"
		}
		lqp += ind + ":" + idStr

	case *pb.Read:
		if demand := n.GetDemand(); demand != nil {
			lqp += ind + LPAREN() + "demand" + " " +
				toStr(demand.GetRelationId(), 0, debugInfo) + RPAREN()
		} else if output := n.GetOutput(); output != nil {
			nameStr := ""
			if output.GetName() != "" {
				nameStr = ":" + output.GetName() + " "
			}
			lqp += ind + LPAREN() + "output" + " " + nameStr +
				toStr(output.GetRelationId(), 0, debugInfo) + RPAREN()
		} else if export := n.GetExport(); export != nil {
			lqp += ind + LPAREN() + "export" + "\n" +
				toStr(export.GetCsvConfig(), indentLevel+1, debugInfo) + RPAREN()
		} else if whatIf := n.GetWhatIf(); whatIf != nil {
			branchStr := ""
			if whatIf.GetBranch() != "" {
				branchStr = ":" + whatIf.GetBranch() + " "
			}
			lqp += ind + LPAREN() + "what_if" + " " + branchStr +
				toStr(whatIf.GetEpoch(), indentLevel+1, debugInfo) + RPAREN()
		} else if abort := n.GetAbort(); abort != nil {
			nameStr := ""
			if abort.GetName() != "" {
				nameStr = ":" + abort.GetName() + " "
			}
			lqp += ind + LPAREN() + "abort" + " " + nameStr +
				toStr(abort.GetRelationId(), 0, debugInfo) + RPAREN()
		}

	case *pb.ExportCSVConfig:
		lqp += ind + LPAREN() + "export_csv_config" + "\n"

		// Default behavior: print_csv_filename=true (show the actual path)
		pathValue := n.GetPath()
		lqp += ind + SIND() + LPAREN() + "path" + " " +
			valueToStr(pathValue, 0, debugInfo) + RPAREN() + "\n"

		lqp += ind + SIND() + LPAREN() + "columns" + " " +
			exportCSVColumnList(n.GetDataColumns(), 0, " ", debugInfo) + RPAREN() + "\n"

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

		lqp += configDictToStr(configDict, indentLevel+1)
		lqp += RPAREN()

	case *pb.ExportCSVColumn:
		lqp += ind + LPAREN() + "column" + " " +
			valueToStr(n.GetColumnName(), 0, debugInfo) + " " +
			toStr(n.GetColumnData(), 0, debugInfo) + RPAREN()

	case *pb.Epoch:
		epochContent := ""
		if len(n.GetWrites()) > 0 {
			epochContent += Indentation(indentLevel+1) + LPAREN() + "writes" + "\n"
			epochContent += writeList(n.GetWrites(), indentLevel+2, "\n", debugInfo)
			epochContent += RPAREN() + "\n"
		}
		if len(n.GetReads()) > 0 {
			epochContent += Indentation(indentLevel+1) + LPAREN() + "reads" + "\n"
			epochContent += readList(n.GetReads(), indentLevel+2, "\n", debugInfo)
			epochContent += RPAREN() + "\n"
		}
		lqp += ind + LPAREN() + "epoch" + "\n" + epochContent + RPAREN()

	case *pb.Fragment:
		lqp += fragmentToStr(n, indentLevel, debugInfo)

	case *pb.Var:
		lqp += ind + n.GetName()

	case *pb.Value:
		// Handle Value oneof - check the actual oneof type
		switch n.GetValue().(type) {
		case *pb.Value_StringValue:
			str := n.GetStringValue()
			escaped := strings.ReplaceAll(str, "\\", "\\\\")
			escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
			return ind + "\"" + escaped + "\""
		case *pb.Value_IntValue:
			return ind + fmt.Sprintf("%d", n.GetIntValue())
		case *pb.Value_FloatValue:
			floatVal := n.GetFloatValue()
			if math.IsInf(floatVal, 0) {
				return ind + "inf"
			}
			if math.IsNaN(floatVal) {
				return ind + "nan"
			}
			if floatVal == float64(int64(floatVal)) {
				return ind + fmt.Sprintf("%.1f", floatVal)
			}
			return ind + fmt.Sprintf("%v", floatVal)
		case *pb.Value_Uint128Value:
			uint128 := n.GetUint128Value()
			return ind + "0x" + uint128ToHexString(uint128.GetLow(), uint128.GetHigh())
		case *pb.Value_Int128Value:
			int128 := n.GetInt128Value()
			result := int128ToString(int128.GetLow(), int128.GetHigh())
			return ind + result + "i128"
		case *pb.Value_MissingValue:
			return ind + "missing"
		case *pb.Value_DateValue:
			date := n.GetDateValue()
			return ind + LPAREN() + "date" + " " +
				fmt.Sprintf("%d %d %d", date.GetYear(), date.GetMonth(), date.GetDay()) + RPAREN()
		case *pb.Value_DatetimeValue:
			datetime := n.GetDatetimeValue()
			return ind + LPAREN() + "datetime" + " " +
				fmt.Sprintf("%d %d %d %d %d %d %d",
					datetime.GetYear(), datetime.GetMonth(), datetime.GetDay(),
					datetime.GetHour(), datetime.GetMinute(), datetime.GetSecond(),
					datetime.GetMicrosecond()) + RPAREN()
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

				return ind + decStr + "d" + fmt.Sprintf("%d", precision)
			}
		case *pb.Value_BooleanValue:
			if n.GetBooleanValue() {
				return ind + "true"
			}
			return ind + "false"
		}

	case string:
		escaped := strings.ReplaceAll(n, "\\", "\\\\")
		escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
		return ind + "\"" + escaped + "\""
	case int:
		return ind + fmt.Sprintf("%d", n)
	case int32:
		return ind + fmt.Sprintf("%d", n)
	case int64:
		return ind + fmt.Sprintf("%d", n)
	case uint32:
		return ind + fmt.Sprintf("%d", n)
	case uint64:
		return ind + fmt.Sprintf("%d", n)

	default:
		panic(fmt.Sprintf("toStr not implemented for %T", node))
	}

	return lqp
}

// Helper function to get type name as string
func getTypeName(t *pb.Type) string {
	switch {
	case t.GetUnspecifiedType() != nil:
		return "UNSPECIFIED"
	case t.GetStringType() != nil:
		return "STRING"
	case t.GetIntType() != nil:
		return "INT"
	case t.GetFloatType() != nil:
		return "FLOAT"
	case t.GetUint128Type() != nil:
		return "UINT128"
	case t.GetInt128Type() != nil:
		return "INT128"
	case t.GetDateType() != nil:
		return "DATE"
	case t.GetDatetimeType() != nil:
		return "DATETIME"
	case t.GetMissingType() != nil:
		return "MISSING"
	case t.GetDecimalType() != nil:
		return "DECIMAL"
	case t.GetBooleanType() != nil:
		return "BOOLEAN"
	default:
		return "UNKNOWN"
	}
}

// Helper function to get type parameters
func getTypeParameters(t *pb.Type) []int32 {
	if decType := t.GetDecimalType(); decType != nil {
		return []int32{decType.GetPrecision(), decType.GetScale()}
	}
	return nil
}

func valueToStr(value interface{}, indentLevel int, debugInfo map[string]string) string {
	// valueToStr now just delegates to toStr for all supported types
	// It exists for backward compatibility and for handling the default case
	switch value.(type) {
	case *pb.Value, string, int, int32, int64, uint32, uint64:
		return toStr(value, indentLevel, debugInfo)
	default:
		// Fallback for any other types (e.g., from config maps)
		return Indentation(indentLevel) + fmt.Sprintf("%v", value)
	}
}

func typeToStr(t *pb.Type) string {
	typeName := getTypeName(t)

	params := getTypeParameters(t)

	if len(params) == 0 {
		return typeName
	}

	result := LPAREN() + typeName + " "
	paramStrs := make([]string, len(params))
	for i, p := range params {
		paramStrs[i] = fmt.Sprintf("%d", p)
	}
	result += strings.Join(paramStrs, " ")
	result += RPAREN()
	return result
}

func varsToStr(vars []*pb.Binding) string {
	parts := make([]string, len(vars))
	for i, binding := range vars {
		parts[i] = binding.GetVar().GetName() + "::" + typeToStr(binding.GetType())
	}
	return strings.Join(parts, " ")
}

func termListToStr(terms []*pb.Term, indentLevel int, debugInfo map[string]string) string {
	ind := Indentation(indentLevel)

	if len(terms) == 0 {
		return ind + LPAREN() + "terms" + RPAREN()
	}

	return ind + LPAREN() + "terms" + " " +
		termList(terms, 0, " ", debugInfo) + RPAREN()
}

func idToName(debugInfo map[string]string, rid *pb.RelationId) string {
	idStr := relationIdToString(rid)
	// Default behavior: print_names=true (use debug names if available)
	if len(debugInfo) == 0 {
		return idStr
	}
	if name, ok := debugInfo[idStr]; ok {
		return ":" + name
	}
	return idStr
}

// Helper functions for list formatting
// Generic list-to-string converter that works with any type
// The formatter function determines how each item is converted to a string
func listToStr[T any](items []T, indentLevel int, delim string, debugInfo map[string]string, formatter func(T, int, map[string]string) string) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = formatter(item, indentLevel, debugInfo)
	}
	return strings.Join(parts, delim)
}

// Convenience wrappers for backward compatibility
func declarationList(items []*pb.Declaration, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Declaration, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func constructList(items []*pb.Construct, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Construct, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func instructionList(items []*pb.Instruction, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Instruction, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func formulaList(items []*pb.Formula, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Formula, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func relTermList(items []*pb.RelTerm, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.RelTerm, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func termList(items []*pb.Term, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Term, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func valueList(items []*pb.Value, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Value, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func attributeList(items []*pb.Attribute, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Attribute, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func abstractionList(items []*pb.Abstraction, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Abstraction, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func relationIdList(items []*pb.RelationId, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.RelationId, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func fragmentIdList(items []*pb.FragmentId, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.FragmentId, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func writeList(items []*pb.Write, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Write, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func readList(items []*pb.Read, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.Read, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}

func exportCSVColumnList(items []*pb.ExportCSVColumn, indentLevel int, delim string, debugInfo map[string]string) string {
	return listToStr(items, indentLevel, delim, debugInfo, func(item *pb.ExportCSVColumn, level int, debug map[string]string) string {
		return toStr(item, level, debug)
	})
}
