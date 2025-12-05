package lqp

import (
	"fmt"
	"math"
	"math/big"
	"sort"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// PrettyParams holds parameters for pretty printing
type PrettyParams struct {
	DebugInfo map[string]string
	indent    int
}

// Some helper methods for pretty printing
func (p PrettyParams) SIND() string      { return "  " }
func (p PrettyParams) LPAREN() string    { return "(" }
func (p PrettyParams) RPAREN() string    { return ")" }
func (p PrettyParams) LBRACKET() string  { return "[" }
func (p PrettyParams) RBRACKET() string  { return "]" }
func (p PrettyParams) INDENT() string    { return strings.Repeat("  ", p.indent) }
func (p PrettyParams) INC() PrettyParams { return PrettyParams{p.DebugInfo, p.indent + 1} }

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
	return uint128ToString(rid.GetIdLow(), rid.GetIdHigh())
}

// Entry point
func ProgramToStr(node *pb.Transaction) string {
	debugInfo := collectDebugInfos(node)
	pp := PrettyParams{debugInfo, 0}
	return toStr(pp, node)
}

func configDictToStr(pp PrettyParams, config map[string]interface{}) string {
	ind := pp.INDENT()

	if len(config) == 0 {
		return ind + "{}"
	}

	// Sort keys for deterministic output
	keys := make([]string, 0, len(config))
	for k := range config {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	configStr := ind + "{" + pp.SIND()[1:]
	for i, k := range keys {
		if i > 0 {
			configStr += "\n" + ind + pp.SIND()
		}
		configStr += fmt.Sprintf(":%s %s", k, valueToStr(PrettyParams{make(map[string]string), 0}, config[k]))
	}
	configStr += "}"

	return configStr
}

func toStr(pp PrettyParams, node interface{}) string {
	ind := pp.INDENT()
	lqp := ""

	switch n := node.(type) {
	case *pb.Transaction:
		lqp += pp.LPAREN() + "transaction"
		lqp += toStr(pp.INC(), n.GetConfigure())
		lqp += toStr(pp.INC(), n.GetSync())
		for _, epoch := range n.GetEpochs() {
			lqp += toStr(pp.INC(), epoch)
		}

		lqp += pp.RPAREN()
		lqp += "\n"

		return lqp

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

		lqp += "\n" + pp.INDENT() + pp.LPAREN() + "configure" + "\n"
		lqp += configDictToStr(pp.INC(), configDict)
		lqp += pp.RPAREN()
		return lqp

	case *pb.Sync:
		if n == nil {
			return ""
		}

		lqp += "\n" + pp.INDENT() + pp.LPAREN() + "sync"
		if len(n.GetFragments()) > 0 {
			lqp += " " + fragmentIdList(PrettyParams{pp.DebugInfo, 0}, n.GetFragments(), " ")
		}
		lqp += pp.RPAREN()
		return lqp

	case *pb.Declaration:
		if def := n.GetDef(); def != nil {
			return toStr(pp, def)
		} else if alg := n.GetAlgorithm(); alg != nil {
			return toStr(pp, alg)
		} else if constraint := n.GetConstraint(); constraint != nil {
			return toStr(pp, constraint)
		}

	case *pb.Def:
		pp_ind := pp.INC()
		lqp += ind + pp_ind.LPAREN() + "def" + " " + toStr(PrettyParams{pp_ind.DebugInfo, 0}, n.GetName()) + "\n"
		lqp += toStr(pp_ind, n.GetBody())
		if len(n.GetAttrs()) == 0 {
			lqp += pp_ind.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp_ind.LPAREN() + "attrs" + "\n"
			lqp += attributeList(pp_ind.INC(), n.GetAttrs(), "\n")
			lqp += pp_ind.RPAREN() + pp_ind.RPAREN()
		}

	case *pb.Constraint:
		if fd := n.GetFunctionalDependency(); fd != nil {
			return toStr(pp, fd)
		}

	case *pb.FunctionalDependency:
		lqp += ind + pp.LPAREN() + "functional_dependency" + "\n"
		lqp += toStr(pp.INC(), n.GetGuard()) + "\n"
		lqp += ind + pp.SIND() + pp.LPAREN() + "keys"
		if len(n.GetKeys()) > 0 {
			lqp += " "
			for i, v := range n.GetKeys() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(PrettyParams{pp.DebugInfo, 0}, v)
			}
		}
		lqp += pp.RPAREN() + "\n"
		lqp += ind + pp.SIND() + pp.LPAREN() + "values"
		if len(n.GetValues()) > 0 {
			lqp += " "
			for i, v := range n.GetValues() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(PrettyParams{pp.DebugInfo, 0}, v)
			}
		}
		lqp += pp.RPAREN() + pp.RPAREN()

	case *pb.Algorithm:
		lqp += ind + pp.LPAREN() + "algorithm"
		if len(n.GetGlobal()) > 4 {
			lqp += "\n" + ind + pp.SIND() + relationIdList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetGlobal(), "\n") + "\n"
		} else {
			lqp += " " + relationIdList(PrettyParams{pp.DebugInfo, 0}, n.GetGlobal(), " ") + "\n"
		}
		lqp += toStr(pp.INC(), n.GetBody())
		lqp += pp.RPAREN()

	case *pb.Script:
		lqp += ind + pp.LPAREN() + "script" + "\n"
		lqp += constructList(pp.INC(), n.GetConstructs(), "\n")
		lqp += pp.RPAREN()

	case *pb.Construct:
		if loop := n.GetLoop(); loop != nil {
			return toStr(pp, loop)
		} else if instr := n.GetInstruction(); instr != nil {
			return toStr(pp, instr)
		}

	case *pb.Loop:
		lqp += ind + pp.LPAREN() + "loop" + "\n"
		lqp += ind + pp.SIND() + pp.LPAREN() + "init"
		if len(n.GetInit()) > 0 {
			lqp += "\n" + instructionList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetInit(), "\n")
		}
		lqp += pp.RPAREN() + "\n"
		lqp += toStr(pp.INC(), n.GetBody())
		lqp += pp.RPAREN()

	case *pb.Instruction:
		if assign := n.GetAssign(); assign != nil {
			return toStr(pp, assign)
		} else if upsert := n.GetUpsert(); upsert != nil {
			return toStr(pp, upsert)
		} else if brk := n.GetBreak(); brk != nil {
			return toStr(pp, brk)
		} else if monoidDef := n.GetMonoidDef(); monoidDef != nil {
			return toStr(pp, monoidDef)
		} else if monusDef := n.GetMonusDef(); monusDef != nil {
			return toStr(pp, monusDef)
		}

	case *pb.Assign:
		pp_ind := pp.INC()
		lqp += ind + pp_ind.LPAREN() + "assign" + " " + toStr(PrettyParams{pp_ind.DebugInfo, 0}, n.GetName()) + "\n"
		lqp += toStr(pp_ind, n.GetBody())
		if len(n.GetAttrs()) == 0 {
			lqp += pp_ind.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp_ind.LPAREN() + "attrs" + "\n"
			lqp += attributeList(pp_ind.INC(), n.GetAttrs(), "\n")
			lqp += pp_ind.RPAREN() + pp_ind.RPAREN()
		}

	case *pb.Break:
		lqp += ind + pp.LPAREN() + "break" + " " + toStr(PrettyParams{pp.DebugInfo, 0}, n.GetName()) + "\n"
		pp_ind := pp.INC()
		lqp += toStr(pp_ind, n.GetBody())
		if len(n.GetAttrs()) == 0 {
			lqp += pp.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp.LPAREN() + "attrs" + "\n"
			lqp += attributeList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetAttrs(), "\n")
			lqp += pp.RPAREN() + pp.RPAREN()
		}

	case *pb.Upsert:
		lqp += ind + pp.LPAREN() + "upsert" + " " + toStr(PrettyParams{pp.DebugInfo, 0}, n.GetName()) + "\n"
		body := n.GetBody()
		pp_ind := pp.INC()
		if n.GetValueArity() == 0 {
			lqp += toStr(pp_ind, body)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + PrettyParams{pp.DebugInfo, 1}.INDENT() + pp.LPAREN() + pp.LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += pp.RBRACKET() + "\n"
			lqp += toStr(PrettyParams{pp.DebugInfo, pp.indent + 2}, body.GetValue()) + pp.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += pp.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp.LPAREN() + "attrs" + "\n"
			lqp += attributeList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetAttrs(), "\n")
			lqp += pp.RPAREN() + pp.RPAREN()
		}

	case *pb.MonoidDef:
		lqp += ind + pp.LPAREN() + "monoid" + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetMonoid()) + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetName()) + "\n"
		body := n.GetBody()
		pp_ind := pp.INC()
		if n.GetValueArity() == 0 {
			lqp += toStr(pp_ind, body)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + PrettyParams{pp.DebugInfo, 1}.INDENT() + pp.LPAREN() + pp.LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += pp.RBRACKET() + "\n"
			lqp += toStr(PrettyParams{pp.DebugInfo, pp.indent + 2}, body.GetValue()) + pp.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += pp.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp.LPAREN() + "attrs" + "\n"
			lqp += attributeList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetAttrs(), "\n")
			lqp += pp.RPAREN() + pp.RPAREN()
		}

	case *pb.MonusDef:
		lqp += ind + pp.LPAREN() + "monus" + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetMonoid()) + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetName()) + "\n"
		body := n.GetBody()
		pp_ind := pp.INC()
		if n.GetValueArity() == 0 {
			lqp += toStr(pp_ind, body)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + PrettyParams{pp.DebugInfo, 1}.INDENT() + pp.LPAREN() + pp.LBRACKET()
			lqp += varsToStr(lvars)
			lqp += " | "
			lqp += varsToStr(rvars)
			lqp += pp.RBRACKET() + "\n"
			lqp += toStr(PrettyParams{pp.DebugInfo, pp.indent + 2}, body.GetValue()) + pp.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += pp.RPAREN()
		} else {
			lqp += "\n" + pp_ind.INDENT() + pp.LPAREN() + "attrs" + "\n"
			lqp += attributeList(PrettyParams{pp.DebugInfo, pp.indent + 2}, n.GetAttrs(), "\n")
			lqp += pp.RPAREN() + pp.RPAREN()
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
			lqp += pp.LPAREN() + typeName + " "
			paramStrs := make([]string, len(params))
			for i, p := range params {
				paramStrs[i] = fmt.Sprintf("%d", p)
			}
			lqp += strings.Join(paramStrs, " ")
			lqp += pp.RPAREN()
		}

	case *pb.Abstraction:
		lqp += ind + pp.LPAREN() + pp.LBRACKET()
		lqp += varsToStr(n.GetVars())
		lqp += pp.RBRACKET() + "\n"
		lqp += toStr(pp.INC(), n.GetValue()) + pp.RPAREN()

	case *pb.Formula:
		pp_ind := pp.INC()
		if exists := n.GetExists(); exists != nil {
			lqp += ind + pp.LPAREN() + "exists" + " " + pp.LBRACKET()
			lqp += varsToStr(exists.GetBody().GetVars())
			lqp += pp.RBRACKET() + "\n"
			lqp += toStr(pp_ind, exists.GetBody().GetValue()) + pp.RPAREN()
		} else if reduce := n.GetReduce(); reduce != nil {
			lqp += ind + pp.LPAREN() + "reduce" + "\n"
			lqp += toStr(pp_ind, reduce.GetOp()) + "\n"
			lqp += toStr(pp_ind, reduce.GetBody()) + "\n"
			lqp += termListToStr(pp_ind, reduce.GetTerms()) + pp.RPAREN()
		} else if conj := n.GetConjunction(); conj != nil {
			if len(conj.GetArgs()) == 0 {
				lqp += ind + pp.LPAREN() + "and" + pp.RPAREN()
			} else {
				lqp += ind + pp.LPAREN() + "and" + "\n"
				lqp += formulaList(pp_ind, conj.GetArgs(), "\n") + pp.RPAREN()
			}
		} else if disj := n.GetDisjunction(); disj != nil {
			if len(disj.GetArgs()) == 0 {
				lqp += ind + pp.LPAREN() + "or" + pp.RPAREN()
			} else {
				lqp += ind + pp.LPAREN() + "or" + "\n"
				lqp += formulaList(pp_ind, disj.GetArgs(), "\n") + pp.RPAREN()
			}
		} else if not := n.GetNot(); not != nil {
			lqp += ind + pp.LPAREN() + "not" + "\n"
			lqp += toStr(pp_ind, not.GetArg()) + pp.RPAREN()
		} else if ffi := n.GetFfi(); ffi != nil {
			lqp += ind + pp.LPAREN() + "ffi" + " :" + ffi.GetName() + "\n"
			lqp += ind + pp.SIND() + pp.LPAREN() + "args" + "\n"
			lqp += abstractionList(PrettyParams{pp.DebugInfo, pp.indent + 2}, ffi.GetArgs(), "\n")
			lqp += pp.RPAREN() + "\n"
			lqp += termListToStr(pp_ind, ffi.GetTerms()) + pp.RPAREN()
		} else if atom := n.GetAtom(); atom != nil {
			if len(atom.GetTerms()) > 4 {
				lqp += ind + pp.LPAREN() + "atom" + " " + toStr(PrettyParams{pp.DebugInfo, 0}, atom.GetName()) + "\n"
				lqp += termList(pp_ind, atom.GetTerms(), "\n") + pp.RPAREN()
			} else {
				lqp += ind + pp.LPAREN() + "atom" + " " + toStr(PrettyParams{pp.DebugInfo, 0}, atom.GetName()) + " "
				lqp += termList(PrettyParams{pp.DebugInfo, 0}, atom.GetTerms(), " ") + pp.RPAREN()
			}
		} else if pragma := n.GetPragma(); pragma != nil {
			terms := termList(PrettyParams{pp.DebugInfo, 0}, pragma.GetTerms(), " ")
			lqp += ind + pp.LPAREN() + "pragma" + " :" + pragma.GetName() + " " + terms + pp.RPAREN()
		} else if primitive := n.GetPrimitive(); primitive != nil {
			if len(primitive.GetTerms()) > 4 {
				lqp += ind + pp.LPAREN() + "primitive" + " :" + primitive.GetName() + "\n"
				lqp += relTermList(pp_ind, primitive.GetTerms(), "\n") + pp.RPAREN()
			} else {
				lqp += ind + pp.LPAREN() + "primitive" + " :" + primitive.GetName() + " "
				lqp += relTermList(PrettyParams{pp.DebugInfo, 0}, primitive.GetTerms(), " ") + pp.RPAREN()
			}
		} else if relAtom := n.GetRelAtom(); relAtom != nil {
			if len(relAtom.GetTerms()) > 4 {
				lqp += ind + pp.LPAREN() + "relatom" + " :" + relAtom.GetName() + "\n"
				lqp += relTermList(pp_ind, relAtom.GetTerms(), "\n") + pp.RPAREN()
			} else {
				lqp += ind + pp.LPAREN() + "relatom" + " :" + relAtom.GetName() + " "
				lqp += relTermList(PrettyParams{pp.DebugInfo, 0}, relAtom.GetTerms(), " ") + pp.RPAREN()
			}
		} else if cast := n.GetCast(); cast != nil {
			lqp += ind + pp.LPAREN() + "cast" + " " +
				toStr(PrettyParams{pp.DebugInfo, 0}, cast.GetInput()) + " " +
				toStr(PrettyParams{pp.DebugInfo, 0}, cast.GetResult()) + pp.RPAREN()
		}

	case *pb.Term:
		if v := n.GetVar(); v != nil {
			lqp += ind + v.GetName()
		} else if val := n.GetConstant(); val != nil {
			lqp += toStr(pp, val)
		}

	case *pb.RelTerm:
		if term := n.GetTerm(); term != nil {
			return toStr(pp, term)
		} else if spec := n.GetSpecializedValue(); spec != nil {
			lqp += "#" + toStr(PrettyParams{make(map[string]string), 0}, spec)
		}

	case *pb.Attribute:
		argsStr := valueList(PrettyParams{pp.DebugInfo, 0}, n.GetArgs(), " ")
		space := ""
		if argsStr != "" {
			space = " "
		}
		lqp += ind + pp.LPAREN() + "attribute" + " :" + n.GetName() + space + argsStr + pp.RPAREN()

	case *pb.RelationId:
		name := idToName(pp, n)
		lqp += ind + name

	case *pb.Write:
		if define := n.GetDefine(); define != nil {
			lqp += ind + pp.LPAREN() + "define" + "\n" +
				toStr(pp.INC(), define.GetFragment()) + pp.RPAREN()
		} else if undef := n.GetUndefine(); undef != nil {
			lqp += ind + pp.LPAREN() + "undefine" + " " +
				toStr(PrettyParams{pp.DebugInfo, 0}, undef.GetFragmentId()) + pp.RPAREN()
		} else if ctx := n.GetContext(); ctx != nil {
			lqp += ind + pp.LPAREN() + "context" + " " +
				relationIdList(PrettyParams{pp.DebugInfo, 0}, ctx.GetRelations(), " ") + pp.RPAREN()
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
			lqp += ind + pp.LPAREN() + "demand" + " " +
				toStr(PrettyParams{pp.DebugInfo, 0}, demand.GetRelationId()) + pp.RPAREN()
		} else if output := n.GetOutput(); output != nil {
			nameStr := ""
			if output.GetName() != "" {
				nameStr = ":" + output.GetName() + " "
			}
			lqp += ind + pp.LPAREN() + "output" + " " + nameStr +
				toStr(PrettyParams{pp.DebugInfo, 0}, output.GetRelationId()) + pp.RPAREN()
		} else if export := n.GetExport(); export != nil {
			lqp += ind + pp.LPAREN() + "export" + "\n" +
				toStr(pp.INC(), export.GetCsvConfig()) + pp.RPAREN()
		} else if whatIf := n.GetWhatIf(); whatIf != nil {
			branchStr := ""
			if whatIf.GetBranch() != "" {
				branchStr = ":" + whatIf.GetBranch() + " "
			}
			lqp += ind + pp.LPAREN() + "what_if" + " " + branchStr +
				toStr(pp.INC(), whatIf.GetEpoch()) + pp.RPAREN()
		} else if abort := n.GetAbort(); abort != nil {
			nameStr := ""
			if abort.GetName() != "" {
				nameStr = ":" + abort.GetName() + " "
			}
			lqp += ind + pp.LPAREN() + "abort" + " " + nameStr +
				toStr(PrettyParams{pp.DebugInfo, 0}, abort.GetRelationId()) + pp.RPAREN()
		}

	case *pb.ExportCSVConfig:
		lqp += ind + pp.LPAREN() + "export_csv_config" + "\n"

		// Default behavior: print_csv_filename=true (show the actual path)
		pathValue := n.GetPath()
		lqp += ind + pp.SIND() + pp.LPAREN() + "path" + " " +
			valueToStr(PrettyParams{pp.DebugInfo, 0}, pathValue) + pp.RPAREN() + "\n"

		lqp += ind + pp.SIND() + pp.LPAREN() + "columns" + " " +
			exportCSVColumnList(PrettyParams{pp.DebugInfo, 0}, n.GetDataColumns(), " ") + pp.RPAREN() + "\n"

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

		lqp += configDictToStr(pp.INC(), configDict)
		lqp += pp.RPAREN()

	case *pb.ExportCSVColumn:
		lqp += ind + pp.LPAREN() + "column" + " " +
			valueToStr(PrettyParams{pp.DebugInfo, 0}, n.GetColumnName()) + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetColumnData()) + pp.RPAREN()

	case *pb.Epoch:
		if n == nil {
			return ""
		}

		lqp += "\n" + pp.INDENT() + pp.LPAREN() + "epoch"

		pp_ind := pp.INC()
		if len(n.GetWrites()) > 0 {
			lqp += "\n" + pp_ind.INDENT() + pp_ind.LPAREN() + "writes" + "\n"
			lqp += writeList(pp_ind.INC(), n.GetWrites(), "\n")
			lqp += pp_ind.RPAREN()
		}

		if len(n.GetReads()) > 0 {
			lqp += "\n" + pp_ind.INDENT() + pp_ind.LPAREN() + "reads" + "\n"
			lqp += readList(pp_ind.INC(), n.GetReads(), "\n")
			lqp += pp_ind.RPAREN()
		}

		lqp += pp.RPAREN()
		return lqp

	case *pb.Fragment:
		ind := pp.INDENT()

		declarationsStr := declarationList(pp.INC(), n.GetDeclarations(), "\n")

		lqp += ind + pp.LPAREN() + "fragment" + " " +
			toStr(PrettyParams{pp.DebugInfo, 0}, n.GetId()) + "\n" +
			declarationsStr +
			pp.RPAREN()

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
			return ind + pp.LPAREN() + "date" + " " +
				fmt.Sprintf("%d %d %d", date.GetYear(), date.GetMonth(), date.GetDay()) + pp.RPAREN()
		case *pb.Value_DatetimeValue:
			datetime := n.GetDatetimeValue()
			return ind + pp.LPAREN() + "datetime" + " " +
				fmt.Sprintf("%d %d %d %d %d %d %d",
					datetime.GetYear(), datetime.GetMonth(), datetime.GetDay(),
					datetime.GetHour(), datetime.GetMinute(), datetime.GetSecond(),
					datetime.GetMicrosecond()) + pp.RPAREN()
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

func valueToStr(pp PrettyParams, value interface{}) string {
	// valueToStr now just delegates to toStr for all supported types
	// It exists for backward compatibility and for handling the default case
	switch value.(type) {
	case *pb.Value, string, int, int32, int64, uint32, uint64:
		return toStr(pp, value)
	default:
		// Fallback for any other types (e.g., from config maps)
		return pp.INDENT() + fmt.Sprintf("%v", value)
	}
}

func typeToStr(t *pb.Type) string {
	typeName := getTypeName(t)

	params := getTypeParameters(t)

	if len(params) == 0 {
		return typeName
	}

	result := "(" + typeName + " "
	paramStrs := make([]string, len(params))
	for i, p := range params {
		paramStrs[i] = fmt.Sprintf("%d", p)
	}
	result += strings.Join(paramStrs, " ")
	result += ")"
	return result
}

func varsToStr(vars []*pb.Binding) string {
	parts := make([]string, len(vars))
	for i, binding := range vars {
		parts[i] = binding.GetVar().GetName() + "::" + typeToStr(binding.GetType())
	}
	return strings.Join(parts, " ")
}

func termListToStr(pp PrettyParams, terms []*pb.Term) string {
	ind := pp.INDENT()

	if len(terms) == 0 {
		return ind + pp.LPAREN() + "terms" + pp.RPAREN()
	}

	return ind + pp.LPAREN() + "terms" + " " +
		termList(PrettyParams{pp.DebugInfo, 0}, terms, " ") + pp.RPAREN()
}

func idToName(pp PrettyParams, rid *pb.RelationId) string {
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
func declarationList(pp PrettyParams, items []*pb.Declaration, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Declaration, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func constructList(pp PrettyParams, items []*pb.Construct, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Construct, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func instructionList(pp PrettyParams, items []*pb.Instruction, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Instruction, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func formulaList(pp PrettyParams, items []*pb.Formula, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Formula, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func relTermList(pp PrettyParams, items []*pb.RelTerm, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.RelTerm, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func termList(pp PrettyParams, items []*pb.Term, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Term, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func valueList(pp PrettyParams, items []*pb.Value, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Value, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func attributeList(pp PrettyParams, items []*pb.Attribute, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Attribute, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func abstractionList(pp PrettyParams, items []*pb.Abstraction, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Abstraction, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func relationIdList(pp PrettyParams, items []*pb.RelationId, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.RelationId, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func fragmentIdList(pp PrettyParams, items []*pb.FragmentId, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.FragmentId, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func writeList(pp PrettyParams, items []*pb.Write, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Write, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func readList(pp PrettyParams, items []*pb.Read, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.Read, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}

func exportCSVColumnList(pp PrettyParams, items []*pb.ExportCSVColumn, delim string) string {
	return listToStr(items, pp.indent, delim, pp.DebugInfo, func(item *pb.ExportCSVColumn, level int, debug map[string]string) string {
		return toStr(PrettyParams{debug, level}, item)
	})
}
