package lqp

import (
	"encoding/hex"
	"fmt"
	"math"
	"math/big"
	"sort"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// StyleConfig defines interface for styling LQP output
type StyleConfig interface {
	SIND() string
	LPAREN() string
	RPAREN() string
	LBRACKET() string
	RBRACKET() string
	Indentation(level int) string
	Kw(x string) string
	Uname(x string) string
	TypeAnno(x string) string
}

// Unstyled provides basic unstyled output
type Unstyled struct{}

func (u *Unstyled) SIND() string                 { return "  " }
func (u *Unstyled) LPAREN() string               { return "(" }
func (u *Unstyled) RPAREN() string               { return ")" }
func (u *Unstyled) LBRACKET() string             { return "[" }
func (u *Unstyled) RBRACKET() string             { return "]" }
func (u *Unstyled) Indentation(level int) string { return strings.Repeat(u.SIND(), level) }
func (u *Unstyled) Kw(x string) string           { return x }
func (u *Unstyled) Uname(x string) string        { return x }
func (u *Unstyled) TypeAnno(x string) string     { return x }

// Styled provides ANSI-styled output (simplified - no colorama in Go stdlib)
type Styled struct{}

func (s *Styled) SIND() string                 { return "  " }
func (s *Styled) LPAREN() string               { return "\033[2m(\033[0m" } // Dim
func (s *Styled) RPAREN() string               { return "\033[2m)\033[0m" } // Dim
func (s *Styled) LBRACKET() string             { return "\033[2m[\033[0m" } // Dim
func (s *Styled) RBRACKET() string             { return "\033[2m]\033[0m" } // Dim
func (s *Styled) Indentation(level int) string { return strings.Repeat(s.SIND(), level) }
func (s *Styled) Kw(x string) string           { return "\033[33m" + x + "\033[0m" } // Yellow
func (s *Styled) Uname(x string) string        { return "\033[37m" + x + "\033[0m" } // White
func (s *Styled) TypeAnno(x string) string     { return "\033[2m" + x + "\033[0m" }  // Dim

// PrettyOption represents formatting options
type PrettyOption int

const (
	STYLED PrettyOption = iota
	PRINT_NAMES
	PRINT_DEBUG
	PRINT_CSV_FILENAME
)

var optionToKey = map[PrettyOption]string{
	STYLED:             "styled",
	PRINT_NAMES:        "print_names",
	PRINT_DEBUG:        "print_debug",
	PRINT_CSV_FILENAME: "print_csv_filename",
}

var optionToDefault = map[PrettyOption]bool{
	STYLED:             false,
	PRINT_NAMES:        false,
	PRINT_DEBUG:        true,
	PRINT_CSV_FILENAME: true,
}

// UglyConfig for precise testing
var UglyConfig = map[string]bool{
	"styled":             false,
	"print_names":        false,
	"print_debug":        true,
	"print_csv_filename": true,
}

// PrettyConfig for human-readable output
var PrettyConfig = map[string]bool{
	"styled":             true,
	"print_names":        true,
	"print_debug":        false,
	"print_csv_filename": true,
}

func styleConfig(options map[string]bool) StyleConfig {
	if hasOption(options, STYLED) {
		return &Styled{}
	}
	return &Unstyled{}
}

func hasOption(options map[string]bool, opt PrettyOption) bool {
	key := optionToKey[opt]
	if val, ok := options[key]; ok {
		return val
	}
	return optionToDefault[opt]
}

// Helper to convert uint128 (represented as two uint64s) to string
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

// Convert uint128 to hex string (32 hex digits, zero-padded)
func uint128ToHexString(low, high uint64) string {
	return fmt.Sprintf("%016x%016x", high, low)
}

// Helper to convert relation ID to string
func relationIdToString(rid *pb.RelationId) string {
	return uint128ToString(rid.GetIdLow(), rid.GetIdHigh())
}

// ToString converts an LQP node to its string representation
func ToString(node LqpNode, options map[string]bool) string {
	if options == nil {
		options = make(map[string]bool)
	}

	switch n := node.(type) {
	case *pb.Transaction:
		return programToStr(n, options)
	case *pb.Fragment:
		return fragmentToStr(n, 0, make(map[string]string), options)
	default:
		panic(fmt.Sprintf("ToString not implemented for top-level node type %T", node))
	}
}

func programToStr(node *pb.Transaction, options map[string]bool) string {
	conf := styleConfig(options)
	s := conf.Indentation(0) + conf.LPAREN() + conf.Kw("transaction")

	// Build configure section
	configDict := make(map[string]interface{})
	config := node.GetConfigure()
	if config != nil {
		configDict["semantics_version"] = config.GetSemanticsVersion()
		ivmConfig := config.GetIvmConfig()
		if ivmConfig != nil && ivmConfig.GetLevel() != pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED {
			levelStr := ivmConfig.GetLevel().String()
			// Convert MAINTENANCE_LEVEL_OFF to "off"
			levelStr = strings.ToLower(strings.TrimPrefix(levelStr, "MAINTENANCE_LEVEL_"))
			configDict["ivm.maintenance_level"] = levelStr
		}
	}

	s += "\n" + conf.Indentation(1) + conf.LPAREN() + conf.Kw("configure") + "\n"
	s += configDictToStr(configDict, 2, options, conf)
	s += conf.RPAREN()

	// Build epochs
	debugInfo := collectDebugInfos(node)

	sync := node.GetSync()
	if sync != nil && len(sync.GetFragments()) > 0 {
		s += "\n" + conf.Indentation(1) + conf.LPAREN() + conf.Kw("sync") + " "
		s += fragmentIdList(sync.GetFragments(), 0, " ", options, debugInfo, conf)
		s += conf.RPAREN()
	}

	for _, epoch := range node.GetEpochs() {
		s += "\n" + conf.Indentation(1) + conf.LPAREN() + conf.Kw("epoch")

		if len(epoch.GetWrites()) > 0 {
			s += "\n" + conf.Indentation(2) + conf.LPAREN() + conf.Kw("writes") + "\n"
			s += writeList(epoch.GetWrites(), 3, "\n", options, debugInfo, conf)
			s += conf.RPAREN()
		}

		if len(epoch.GetReads()) > 0 {
			s += "\n" + conf.Indentation(2) + conf.LPAREN() + conf.Kw("reads") + "\n"
			s += readList(epoch.GetReads(), 3, "\n", options, debugInfo, conf)
			s += conf.RPAREN()
		}

		s += conf.RPAREN()
	}
	s += conf.RPAREN()

	if hasOption(options, PRINT_DEBUG) {
		s += debugStr(node)
	} else {
		s += "\n"
	}

	return s
}

func configDictToStr(config map[string]interface{}, indentLevel int, options map[string]bool, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)

	if len(config) == 0 {
		return ind + "{}"
	}

	// Sort keys for deterministic output
	keys := make([]string, 0, len(config))
	for k := range config {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	configStr := ind + "{" + conf.SIND()[1:]
	for i, k := range keys {
		if i > 0 {
			configStr += "\n" + ind + conf.SIND()
		}
		configStr += fmt.Sprintf(":%s %s", k, valueToStr(config[k], 0, options, make(map[string]string), conf))
	}
	configStr += "}"

	return configStr
}

func debugStr(node interface{}) string {
	debugInfos := collectDebugInfos(node)
	if len(debugInfos) == 0 {
		return ""
	}

	debugStr := "\n\n"
	debugStr += ";; Debug information\n"
	debugStr += ";; -----------------------\n"
	debugStr += ";; Original names\n"

	// Sort by ID for deterministic output
	type entry struct {
		id   string
		name string
	}
	entries := make([]entry, 0, len(debugInfos))
	for id, name := range debugInfos {
		entries = append(entries, entry{id: id, name: name})
	}
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].id < entries[j].id
	})

	for _, e := range entries {
		debugStr += fmt.Sprintf(";; \t ID `%s` -> `%s`\n", e.id, e.name)
	}
	return debugStr
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
	case []*pb.Write:
		for _, w := range n {
			for k, v := range collectDebugInfos(w) {
				debugInfos[k] = v
			}
		}
	case *pb.Write:
		if define := n.GetDefine(); define != nil {
			for k, v := range collectDebugInfos(define.GetFragment()) {
				debugInfos[k] = v
			}
		}
	}

	return debugInfos
}

func fragmentToStr(node *pb.Fragment, indentLevel int, debugInfo map[string]string, options map[string]bool) string {
	conf := styleConfig(options)
	ind := conf.Indentation(indentLevel)

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

	declarationsStr := declarationList(node.GetDeclarations(), indentLevel+1, "\n", options, debugInfo, conf)

	return ind + conf.LPAREN() + conf.Kw("fragment") + " " +
		toStr(node.GetId(), 0, options, debugInfo, conf) + "\n" +
		declarationsStr +
		conf.RPAREN()
}

func toStr(node interface{}, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)
	lqp := ""

	switch n := node.(type) {
	case *pb.Declaration:
		// Handle Declaration oneof
		if def := n.GetDef(); def != nil {
			return toStr(def, indentLevel, options, debugInfo, conf)
		} else if alg := n.GetAlgorithm(); alg != nil {
			return toStr(alg, indentLevel, options, debugInfo, conf)
		} else if constraint := n.GetConstraint(); constraint != nil {
			return toStr(constraint, indentLevel, options, debugInfo, conf)
		}

	case *pb.Def:
		lqp += ind + conf.LPAREN() + conf.Kw("def") + " " + toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, options, debugInfo, conf)
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.Constraint:
		if fd := n.GetFunctionalDependency(); fd != nil {
			return toStr(fd, indentLevel, options, debugInfo, conf)
		}

	case *pb.FunctionalDependency:
		lqp += ind + conf.LPAREN() + conf.Kw("functional_dependency") + "\n"
		lqp += toStr(n.GetGuard(), indentLevel+1, options, debugInfo, conf) + "\n"
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("keys")
		if len(n.GetKeys()) > 0 {
			lqp += " "
			for i, v := range n.GetKeys() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(v, 0, options, debugInfo, conf)
			}
		}
		lqp += conf.RPAREN() + "\n"
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("values")
		if len(n.GetValues()) > 0 {
			lqp += " "
			for i, v := range n.GetValues() {
				if i > 0 {
					lqp += " "
				}
				lqp += toStr(v, 0, options, debugInfo, conf)
			}
		}
		lqp += conf.RPAREN() + conf.RPAREN()

	case *pb.Algorithm:
		lqp += ind + conf.LPAREN() + conf.Kw("algorithm")
		if len(n.GetGlobal()) > 4 {
			lqp += "\n" + ind + conf.SIND() + relationIdList(n.GetGlobal(), indentLevel+2, "\n", options, debugInfo, conf) + "\n"
		} else {
			lqp += " " + relationIdList(n.GetGlobal(), 0, " ", options, debugInfo, conf) + "\n"
		}
		lqp += toStr(n.GetBody(), indentLevel+1, options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *pb.Script:
		lqp += ind + conf.LPAREN() + conf.Kw("script") + "\n"
		lqp += constructList(n.GetConstructs(), indentLevel+1, "\n", options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *pb.Construct:
		if loop := n.GetLoop(); loop != nil {
			return toStr(loop, indentLevel, options, debugInfo, conf)
		} else if instr := n.GetInstruction(); instr != nil {
			return toStr(instr, indentLevel, options, debugInfo, conf)
		}

	case *pb.Loop:
		lqp += ind + conf.LPAREN() + conf.Kw("loop") + "\n"
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("init")
		if len(n.GetInit()) > 0 {
			lqp += "\n" + instructionList(n.GetInit(), indentLevel+2, "\n", options, debugInfo, conf)
		}
		lqp += conf.RPAREN() + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *pb.Instruction:
		if assign := n.GetAssign(); assign != nil {
			return toStr(assign, indentLevel, options, debugInfo, conf)
		} else if upsert := n.GetUpsert(); upsert != nil {
			return toStr(upsert, indentLevel, options, debugInfo, conf)
		} else if brk := n.GetBreak(); brk != nil {
			return toStr(brk, indentLevel, options, debugInfo, conf)
		} else if monoidDef := n.GetMonoidDef(); monoidDef != nil {
			return toStr(monoidDef, indentLevel, options, debugInfo, conf)
		} else if monusDef := n.GetMonusDef(); monusDef != nil {
			return toStr(monusDef, indentLevel, options, debugInfo, conf)
		}

	case *pb.Assign:
		lqp += ind + conf.LPAREN() + conf.Kw("assign") + " " + toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, options, debugInfo, conf)
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.Break:
		lqp += ind + conf.LPAREN() + conf.Kw("break") + " " + toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.GetBody(), indentLevel+1, options, debugInfo, conf)
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.Upsert:
		lqp += ind + conf.LPAREN() + conf.Kw("upsert") + " " + toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.MonoidDef:
		lqp += ind + conf.LPAREN() + conf.Kw("monoid") + " " +
			toStr(n.GetMonoid(), 0, options, debugInfo, conf) + " " +
			toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.MonusDef:
		lqp += ind + conf.LPAREN() + conf.Kw("monus") + " " +
			toStr(n.GetMonoid(), 0, options, debugInfo, conf) + " " +
			toStr(n.GetName(), 0, options, debugInfo, conf) + "\n"
		body := n.GetBody()
		if n.GetValueArity() == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.GetVars()) - int(n.GetValueArity())
			lvars := body.GetVars()[:partition]
			rvars := body.GetVars()[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.GetValue(), indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.GetAttrs()) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.GetAttrs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *pb.Monoid:
		if n.GetOrMonoid() != nil {
			lqp += "BOOL::OR"
		} else if minMonoid := n.GetMinMonoid(); minMonoid != nil {
			lqp += typeToStr(minMonoid.GetType(), 0, options, debugInfo, conf) + "::MIN"
		} else if maxMonoid := n.GetMaxMonoid(); maxMonoid != nil {
			lqp += typeToStr(maxMonoid.GetType(), 0, options, debugInfo, conf) + "::MAX"
		} else if sumMonoid := n.GetSumMonoid(); sumMonoid != nil {
			lqp += typeToStr(sumMonoid.GetType(), 0, options, debugInfo, conf) + "::SUM"
		}

	case *pb.Type:
		// Get the type name as string
		typeName := getTypeName(n)
		params := getTypeParameters(n)

		if len(params) == 0 {
			lqp += conf.TypeAnno(typeName)
		} else {
			lqp += conf.LPAREN() + conf.TypeAnno(typeName) + " "
			paramStrs := make([]string, len(params))
			for i, p := range params {
				paramStrs[i] = fmt.Sprintf("%d", p)
			}
			lqp += strings.Join(paramStrs, " ")
			lqp += conf.RPAREN()
		}

	case *pb.Abstraction:
		lqp += ind + conf.LPAREN() + conf.LBRACKET()
		lqp += varsToStr(n.GetVars(), options, debugInfo, conf)
		lqp += conf.RBRACKET() + "\n"
		lqp += toStr(n.GetValue(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *pb.Formula:
		if exists := n.GetExists(); exists != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("exists") + " " + conf.LBRACKET()
			lqp += varsToStr(exists.GetBody().GetVars(), options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(exists.GetBody().GetValue(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if reduce := n.GetReduce(); reduce != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("reduce") + "\n"
			lqp += toStr(reduce.GetOp(), indentLevel+1, options, debugInfo, conf) + "\n"
			lqp += toStr(reduce.GetBody(), indentLevel+1, options, debugInfo, conf) + "\n"
			lqp += termListToStr(reduce.GetTerms(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if conj := n.GetConjunction(); conj != nil {
			if len(conj.GetArgs()) == 0 {
				lqp += ind + conf.LPAREN() + conf.Kw("and") + conf.RPAREN()
			} else {
				lqp += ind + conf.LPAREN() + conf.Kw("and") + "\n"
				lqp += formulaList(conj.GetArgs(), indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
			}
		} else if disj := n.GetDisjunction(); disj != nil {
			if len(disj.GetArgs()) == 0 {
				lqp += ind + conf.LPAREN() + conf.Kw("or") + conf.RPAREN()
			} else {
				lqp += ind + conf.LPAREN() + conf.Kw("or") + "\n"
				lqp += formulaList(disj.GetArgs(), indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
			}
		} else if not := n.GetNot(); not != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("not") + "\n"
			lqp += toStr(not.GetArg(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if ffi := n.GetFfi(); ffi != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("ffi") + " :" + ffi.GetName() + "\n"
			lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("args") + "\n"
			lqp += abstractionList(ffi.GetArgs(), indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + "\n"
			lqp += termListToStr(ffi.GetTerms(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if atom := n.GetAtom(); atom != nil {
			if len(atom.GetTerms()) > 4 {
				lqp += ind + conf.LPAREN() + conf.Kw("atom") + " " + toStr(atom.GetName(), 0, options, debugInfo, conf) + "\n"
				lqp += termList(atom.GetTerms(), indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
			} else {
				lqp += ind + conf.LPAREN() + conf.Kw("atom") + " " + toStr(atom.GetName(), 0, options, debugInfo, conf) + " "
				lqp += termList(atom.GetTerms(), 0, " ", options, debugInfo, conf) + conf.RPAREN()
			}
		} else if pragma := n.GetPragma(); pragma != nil {
			terms := termList(pragma.GetTerms(), 0, " ", options, debugInfo, conf)
			lqp += ind + conf.LPAREN() + conf.Kw("pragma") + " :" + conf.Uname(pragma.GetName()) + " " + terms + conf.RPAREN()
		} else if primitive := n.GetPrimitive(); primitive != nil {
			if len(primitive.GetTerms()) > 4 {
				lqp += ind + conf.LPAREN() + conf.Kw("primitive") + " :" + conf.Uname(primitive.GetName()) + "\n"
				lqp += relTermList(primitive.GetTerms(), indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
			} else {
				lqp += ind + conf.LPAREN() + conf.Kw("primitive") + " :" + conf.Uname(primitive.GetName()) + " "
				lqp += relTermList(primitive.GetTerms(), 0, " ", options, debugInfo, conf) + conf.RPAREN()
			}
		} else if relAtom := n.GetRelAtom(); relAtom != nil {
			if len(relAtom.GetTerms()) > 4 {
				lqp += ind + conf.LPAREN() + conf.Kw("relatom") + " :" + relAtom.GetName() + "\n"
				lqp += relTermList(relAtom.GetTerms(), indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
			} else {
				lqp += ind + conf.LPAREN() + conf.Kw("relatom") + " :" + relAtom.GetName() + " "
				lqp += relTermList(relAtom.GetTerms(), 0, " ", options, debugInfo, conf) + conf.RPAREN()
			}
		} else if cast := n.GetCast(); cast != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("cast") + " " +
				toStr(cast.GetInput(), 0, options, debugInfo, conf) + " " +
				toStr(cast.GetResult(), 0, options, debugInfo, conf) + conf.RPAREN()
		}

	case *pb.Term:
		if v := n.GetVar(); v != nil {
			lqp += ind + conf.Uname(v.GetName())
		} else if val := n.GetConstant(); val != nil {
			lqp += valueToStr(val, indentLevel, options, debugInfo, conf)
		}

	case *pb.RelTerm:
		if term := n.GetTerm(); term != nil {
			return toStr(term, indentLevel, options, debugInfo, conf)
		} else if spec := n.GetSpecializedValue(); spec != nil {
			lqp += "#" + valueToStr(spec, 0, options, make(map[string]string), conf)
		}

	case *pb.Attribute:
		argsStr := valueList(n.GetArgs(), 0, " ", options, debugInfo, conf)
		space := ""
		if argsStr != "" {
			space = " "
		}
		lqp += ind + conf.LPAREN() + conf.Kw("attribute") + " :" + n.GetName() + space + argsStr + conf.RPAREN()

	case *pb.RelationId:
		name := idToName(options, debugInfo, n)
		lqp += ind + conf.Uname(name)

	case *pb.Write:
		if define := n.GetDefine(); define != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("define") + "\n" +
				toStr(define.GetFragment(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if undef := n.GetUndefine(); undef != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("undefine") + " " +
				toStr(undef.GetFragmentId(), 0, options, debugInfo, conf) + conf.RPAREN()
		} else if ctx := n.GetContext(); ctx != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("context") + " " +
				relationIdList(ctx.GetRelations(), 0, " ", options, debugInfo, conf) + conf.RPAREN()
		}

	case *pb.FragmentId:
		// Encode fragment ID as hex, but prefix with 'f' to ensure it's always a symbol
		hexId := hex.EncodeToString(n.GetId())
		if hexId == "" {
			hexId = "empty"
		}
		lqp += ind + ":" + conf.Uname("f"+hexId)

	case *pb.Read:
		if demand := n.GetDemand(); demand != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("demand") + " " +
				toStr(demand.GetRelationId(), 0, options, debugInfo, conf) + conf.RPAREN()
		} else if output := n.GetOutput(); output != nil {
			nameStr := ""
			if output.GetName() != "" {
				nameStr = ":" + conf.Uname(output.GetName()) + " "
			}
			lqp += ind + conf.LPAREN() + conf.Kw("output") + " " + nameStr +
				toStr(output.GetRelationId(), 0, options, debugInfo, conf) + conf.RPAREN()
		} else if export := n.GetExport(); export != nil {
			lqp += ind + conf.LPAREN() + conf.Kw("export") + "\n" +
				toStr(export.GetCsvConfig(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if whatIf := n.GetWhatIf(); whatIf != nil {
			branchStr := ""
			if whatIf.GetBranch() != "" {
				branchStr = ":" + conf.Uname(whatIf.GetBranch()) + " "
			}
			lqp += ind + conf.LPAREN() + conf.Kw("what_if") + " " + branchStr +
				toStr(whatIf.GetEpoch(), indentLevel+1, options, debugInfo, conf) + conf.RPAREN()
		} else if abort := n.GetAbort(); abort != nil {
			nameStr := ""
			if abort.GetName() != "" {
				nameStr = ":" + conf.Uname(abort.GetName()) + " "
			}
			lqp += ind + conf.LPAREN() + conf.Kw("abort") + " " + nameStr +
				toStr(abort.GetRelationId(), 0, options, debugInfo, conf) + conf.RPAREN()
		}

	case *pb.ExportCSVConfig:
		lqp += ind + conf.LPAREN() + conf.Kw("export_csv_config") + "\n"

		pathValue := n.GetPath()
		if !hasOption(options, PRINT_CSV_FILENAME) {
			pathValue = "<hidden filename>"
		}
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("path") + " " +
			valueToStr(pathValue, 0, options, debugInfo, conf) + conf.RPAREN() + "\n"

		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("columns") + " " +
			exportCSVColumnList(n.GetDataColumns(), 0, " ", options, debugInfo, conf) + conf.RPAREN() + "\n"

		configDict := make(map[string]interface{})
		configDict["partition_size"] = n.GetPartitionSize()
		configDict["compression"] = n.GetCompression()
		configDict["syntax_header_row"] = n.GetSyntaxHeaderRow()
		configDict["syntax_missing_string"] = n.GetSyntaxMissingString()
		configDict["syntax_delim"] = n.GetSyntaxDelim()
		configDict["syntax_quotechar"] = n.GetSyntaxQuotechar()
		configDict["syntax_escapechar"] = n.GetSyntaxEscapechar()

		lqp += configDictToStr(configDict, indentLevel+1, options, conf)
		lqp += conf.RPAREN()

	case *pb.ExportCSVColumn:
		lqp += ind + conf.LPAREN() + conf.Kw("column") + " " +
			valueToStr(n.GetColumnName(), 0, options, debugInfo, conf) + " " +
			toStr(n.GetColumnData(), 0, options, debugInfo, conf) + conf.RPAREN()

	case *pb.Epoch:
		epochContent := ""
		if len(n.GetWrites()) > 0 {
			epochContent += conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("writes") + "\n"
			epochContent += writeList(n.GetWrites(), indentLevel+2, "\n", options, debugInfo, conf)
			epochContent += conf.RPAREN() + "\n"
		}
		if len(n.GetReads()) > 0 {
			epochContent += conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("reads") + "\n"
			epochContent += readList(n.GetReads(), indentLevel+2, "\n", options, debugInfo, conf)
			epochContent += conf.RPAREN() + "\n"
		}
		lqp += ind + conf.LPAREN() + conf.Kw("epoch") + "\n" + epochContent + conf.RPAREN()

	case *pb.Fragment:
		lqp += fragmentToStr(n, indentLevel, debugInfo, options)

	case *pb.Var:
		lqp += ind + conf.Uname(n.GetName())

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
		return "BOOL"
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

func valueToStr(value interface{}, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)

	switch v := value.(type) {
	case *pb.Value:
		// Handle Value oneof - check the actual oneof type
		switch v.GetValue().(type) {
		case *pb.Value_StringValue:
			str := v.GetStringValue()
			escaped := strings.ReplaceAll(str, "\\", "\\\\")
			escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
			return ind + "\"" + escaped + "\""
		case *pb.Value_IntValue:
			return ind + fmt.Sprintf("%d", v.GetIntValue())
		case *pb.Value_FloatValue:
			floatVal := v.GetFloatValue()
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
			uint128 := v.GetUint128Value()
			return ind + "0x" + uint128ToHexString(uint128.GetLow(), uint128.GetHigh())
		case *pb.Value_Int128Value:
			int128 := v.GetInt128Value()
			result := uint128ToString(int128.GetLow(), int128.GetHigh())
			return ind + result + "i128"
		case *pb.Value_MissingValue:
			return ind + "missing"
		case *pb.Value_DateValue:
			date := v.GetDateValue()
			return ind + conf.LPAREN() + conf.Kw("date") + " " +
				fmt.Sprintf("%d %d %d", date.GetYear(), date.GetMonth(), date.GetDay()) + conf.RPAREN()
		case *pb.Value_DatetimeValue:
			datetime := v.GetDatetimeValue()
			return ind + conf.LPAREN() + conf.Kw("datetime") + " " +
				fmt.Sprintf("%d %d %d %d %d %d %d",
					datetime.GetYear(), datetime.GetMonth(), datetime.GetDay(),
					datetime.GetHour(), datetime.GetMinute(), datetime.GetSecond(),
					datetime.GetMicrosecond()) + conf.RPAREN()
		case *pb.Value_DecimalValue:
			decimal := v.GetDecimalValue()
			int128Val := decimal.GetValue()
			if int128Val != nil {
				// Get the raw integer value
				rawValue := uint128ToString(int128Val.GetLow(), int128Val.GetHigh())
				precision := decimal.GetPrecision()
				scale := decimal.GetScale()

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
				return ind + decStr + "d" + fmt.Sprintf("%d", precision)
			}
		case *pb.Value_BooleanValue:
			if v.GetBooleanValue() {
				return ind + "true"
			}
			return ind + "false"
		}
	case string:
		escaped := strings.ReplaceAll(v, "\\", "\\\\")
		escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
		return ind + "\"" + escaped + "\""
	case int:
		return ind + fmt.Sprintf("%d", v)
	case int32:
		return ind + fmt.Sprintf("%d", v)
	case int64:
		return ind + fmt.Sprintf("%d", v)
	case uint32:
		return ind + fmt.Sprintf("%d", v)
	case uint64:
		return ind + fmt.Sprintf("%d", v)
	default:
		return ind + fmt.Sprintf("%v", v)
	}
	return ind
}

func typeToStr(t *pb.Type, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	typeName := getTypeName(t)
	params := getTypeParameters(t)

	if len(params) == 0 {
		return conf.TypeAnno(typeName)
	}

	result := conf.LPAREN() + conf.TypeAnno(typeName) + " "
	paramStrs := make([]string, len(params))
	for i, p := range params {
		paramStrs[i] = fmt.Sprintf("%d", p)
	}
	result += strings.Join(paramStrs, " ")
	result += conf.RPAREN()
	return result
}

func varsToStr(vars []*pb.Binding, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(vars))
	for i, binding := range vars {
		parts[i] = conf.Uname(binding.GetVar().GetName()) + conf.TypeAnno("::") + typeToStr(binding.GetType(), 0, options, debugInfo, conf)
	}
	return strings.Join(parts, " ")
}

func termListToStr(terms []*pb.Term, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)

	if len(terms) == 0 {
		return ind + conf.LPAREN() + conf.Kw("terms") + conf.RPAREN()
	}

	return ind + conf.LPAREN() + conf.Kw("terms") + " " +
		termList(terms, 0, " ", options, debugInfo, conf) + conf.RPAREN()
}

func idToName(options map[string]bool, debugInfo map[string]string, rid *pb.RelationId) string {
	idStr := relationIdToString(rid)
	if !hasOption(options, PRINT_NAMES) {
		return idStr
	}
	if len(debugInfo) == 0 {
		return idStr
	}
	if name, ok := debugInfo[idStr]; ok {
		return ":" + name
	}
	return idStr
}

// Helper functions for list formatting
func declarationList(items []*pb.Declaration, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func constructList(items []*pb.Construct, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func instructionList(items []*pb.Instruction, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func formulaList(items []*pb.Formula, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func relTermList(items []*pb.RelTerm, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func termList(items []*pb.Term, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func valueList(items []*pb.Value, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = valueToStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func attributeList(items []*pb.Attribute, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func abstractionList(items []*pb.Abstraction, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func relationIdList(items []*pb.RelationId, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func fragmentIdList(items []*pb.FragmentId, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func writeList(items []*pb.Write, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func readList(items []*pb.Read, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func exportCSVColumnList(items []*pb.ExportCSVColumn, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}
