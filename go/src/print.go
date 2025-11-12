package lqp

import (
	"fmt"
	"math"
	"sort"
	"strings"
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

// ToString converts an LQP node to its string representation
func ToString(node LqpNode, options map[string]bool) string {
	if options == nil {
		options = make(map[string]bool)
	}

	switch n := node.(type) {
	case *Transaction:
		return programToStr(n, options)
	case *Fragment:
		return fragmentToStr(n, 0, make(map[string]string), options)
	default:
		panic(fmt.Sprintf("ToString not implemented for top-level node type %T", node))
	}
}

func programToStr(node *Transaction, options map[string]bool) string {
	conf := styleConfig(options)
	s := conf.Indentation(0) + conf.LPAREN() + conf.Kw("transaction")

	// Build configure section
	configDict := make(map[string]interface{})
	config := node.Configure
	configDict["semantics_version"] = config.SemanticsVersion
	if config.IvmConfig.Level != MaintenanceLevelUnspecified {
		configDict["ivm.maintenance_level"] = strings.ToLower(config.IvmConfig.Level.String())
	}

	s += "\n" + conf.Indentation(1) + conf.LPAREN() + conf.Kw("configure") + "\n"
	s += configDictToStr(configDict, 2, options, conf)
	s += conf.RPAREN()

	// Build epochs
	debugInfo := collectDebugInfos(node)

	for _, epoch := range node.Epochs {
		s += "\n" + conf.Indentation(1) + conf.LPAREN() + conf.Kw("epoch")

		if len(epoch.Writes) > 0 {
			s += "\n" + conf.Indentation(2) + conf.LPAREN() + conf.Kw("writes") + "\n"
			s += writeList(epoch.Writes, 3, "\n", options, debugInfo, conf)
			s += conf.RPAREN()
		}

		if len(epoch.Reads) > 0 {
			s += "\n" + conf.Indentation(2) + conf.LPAREN() + conf.Kw("reads") + "\n"
			s += readList(epoch.Reads, 3, "\n", options, debugInfo, conf)
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

func debugStr(node LqpNode) string {
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
	case *Fragment:
		for k, v := range n.DebugInfo.IdToOrigName {
			debugInfos[k] = v
		}
	case *Transaction:
		for _, epoch := range n.Epochs {
			for _, write := range epoch.Writes {
				if define, ok := write.WriteType.(*Define); ok {
					for k, v := range collectDebugInfos(define.Fragment) {
						debugInfos[k] = v
					}
				}
			}
		}
	case []Write:
		for _, w := range n {
			for k, v := range collectDebugInfos(w) {
				debugInfos[k] = v
			}
		}
	case *Write:
		for k, v := range collectDebugInfos(n.WriteType) {
			debugInfos[k] = v
		}
	case *Define:
		for k, v := range collectDebugInfos(n.Fragment) {
			debugInfos[k] = v
		}
	}

	return debugInfos
}

func fragmentToStr(node *Fragment, indentLevel int, debugInfo map[string]string, options map[string]bool) string {
	conf := styleConfig(options)
	ind := conf.Indentation(indentLevel)

	// Merge debug info
	for k, v := range node.DebugInfo.IdToOrigName {
		debugInfo[k] = v
	}

	declarationsStr := declarationList(node.Declarations, indentLevel+1, "\n", options, debugInfo, conf)

	return ind + conf.LPAREN() + conf.Kw("fragment") + " " +
		toStr(node.Id, 0, options, debugInfo, conf) + "\n" +
		declarationsStr +
		conf.RPAREN()
}

func toStr(node interface{}, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)
	lqp := ""

	switch n := node.(type) {
	case *Def:
		lqp += ind + conf.LPAREN() + conf.Kw("def") + " " + toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf)
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *Algorithm:
		lqp += ind + conf.LPAREN() + conf.Kw("algorithm")
		if len(n.Global) > 4 {
			lqp += "\n" + ind + conf.SIND() + relationIdList(n.Global, indentLevel+2, "\n", options, debugInfo, conf) + "\n"
		} else {
			lqp += " " + relationIdList(n.Global, 0, " ", options, debugInfo, conf) + "\n"
		}
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *Script:
		lqp += ind + conf.LPAREN() + conf.Kw("script") + "\n"
		lqp += constructList(n.Constructs, indentLevel+1, "\n", options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *Loop:
		lqp += ind + conf.LPAREN() + conf.Kw("loop") + "\n"
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("init")
		if len(n.Init) > 0 {
			lqp += "\n" + instructionList(n.Init, indentLevel+2, "\n", options, debugInfo, conf)
		}
		lqp += conf.RPAREN() + "\n"
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf)
		lqp += conf.RPAREN()

	case *Assign:
		lqp += ind + conf.LPAREN() + conf.Kw("assign") + " " + toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf)
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *Break:
		lqp += ind + conf.LPAREN() + conf.Kw("break") + " " + toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf)
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *Upsert:
		lqp += ind + conf.LPAREN() + conf.Kw("upsert") + " " + toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		body := n.Body
		if n.ValueArity == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.Vars) - int(n.ValueArity)
			lvars := body.Vars[:partition]
			rvars := body.Vars[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.Value, indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *MonoidDef:
		lqp += ind + conf.LPAREN() + conf.Kw("monoid") + " " +
			toStr(n.Monoid, 0, options, debugInfo, conf) + " " +
			toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		body := n.Body
		if n.ValueArity == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.Vars) - int(n.ValueArity)
			lvars := body.Vars[:partition]
			rvars := body.Vars[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.Value, indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *MonusDef:
		lqp += ind + conf.LPAREN() + conf.Kw("monus") + " " +
			toStr(n.Monoid, 0, options, debugInfo, conf) + " " +
			toStr(n.Name, 0, options, debugInfo, conf) + "\n"
		body := n.Body
		if n.ValueArity == 0 {
			lqp += toStr(body, indentLevel+1, options, debugInfo, conf)
		} else {
			partition := len(body.Vars) - int(n.ValueArity)
			lvars := body.Vars[:partition]
			rvars := body.Vars[partition:]
			lqp += ind + conf.Indentation(1) + conf.LPAREN() + conf.LBRACKET()
			lqp += varsToStr(lvars, options, debugInfo, conf)
			lqp += " | "
			lqp += varsToStr(rvars, options, debugInfo, conf)
			lqp += conf.RBRACKET() + "\n"
			lqp += toStr(body.Value, indentLevel+2, options, debugInfo, conf) + conf.RPAREN()
		}
		if len(n.Attrs) == 0 {
			lqp += conf.RPAREN()
		} else {
			lqp += "\n" + conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("attrs") + "\n"
			lqp += attributeList(n.Attrs, indentLevel+2, "\n", options, debugInfo, conf)
			lqp += conf.RPAREN() + conf.RPAREN()
		}

	case *OrMonoid:
		lqp += "BOOL::OR"

	case *MinMonoid:
		lqp += typeToStr(n.Type, 0, options, debugInfo, conf) + "::MIN"

	case *MaxMonoid:
		lqp += typeToStr(n.Type, 0, options, debugInfo, conf) + "::MAX"

	case *SumMonoid:
		lqp += typeToStr(n.Type, 0, options, debugInfo, conf) + "::SUM"

	case *Type:
		if len(n.Parameters) == 0 {
			lqp += conf.TypeAnno(n.TypeName.String())
		} else {
			lqp += conf.LPAREN() + conf.TypeAnno(n.TypeName.String()) + " "
			params := make([]string, len(n.Parameters))
			for i, p := range n.Parameters {
				params[i] = valueToStr(p, 0, options, debugInfo, conf)
			}
			lqp += strings.Join(params, " ")
			lqp += conf.RPAREN()
		}

	case *Abstraction:
		lqp += ind + conf.LPAREN() + conf.LBRACKET()
		lqp += varsToStr(n.Vars, options, debugInfo, conf)
		lqp += conf.RBRACKET() + "\n"
		lqp += toStr(n.Value, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Exists:
		lqp += ind + conf.LPAREN() + conf.Kw("exists") + " " + conf.LBRACKET()
		lqp += varsToStr(n.Body.Vars, options, debugInfo, conf)
		lqp += conf.RBRACKET() + "\n"
		lqp += toStr(n.Body.Value, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Reduce:
		lqp += ind + conf.LPAREN() + conf.Kw("reduce") + "\n"
		lqp += toStr(n.Op, indentLevel+1, options, debugInfo, conf) + "\n"
		lqp += toStr(n.Body, indentLevel+1, options, debugInfo, conf) + "\n"
		lqp += termListToStr(n.Terms, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Conjunction:
		if len(n.Args) == 0 {
			lqp += ind + conf.LPAREN() + conf.Kw("and") + conf.RPAREN()
		} else {
			lqp += ind + conf.LPAREN() + conf.Kw("and") + "\n"
			lqp += formulaList(n.Args, indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
		}

	case *Disjunction:
		if len(n.Args) == 0 {
			lqp += ind + conf.LPAREN() + conf.Kw("or") + conf.RPAREN()
		} else {
			lqp += ind + conf.LPAREN() + conf.Kw("or") + "\n"
			lqp += formulaList(n.Args, indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
		}

	case *Not:
		lqp += ind + conf.LPAREN() + conf.Kw("not") + "\n"
		lqp += toStr(n.Arg, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *FFI:
		lqp += ind + conf.LPAREN() + conf.Kw("ffi") + " :" + n.Name + "\n"
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("args") + "\n"
		lqp += abstractionList(n.Args, indentLevel+2, "\n", options, debugInfo, conf)
		lqp += conf.RPAREN() + "\n"
		lqp += termListToStr(n.Terms, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Atom:
		if len(n.Terms) > 4 {
			lqp += ind + conf.LPAREN() + conf.Kw("atom") + " " + toStr(n.Name, 0, options, debugInfo, conf) + "\n"
			lqp += termList(n.Terms, indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
		} else {
			lqp += ind + conf.LPAREN() + conf.Kw("atom") + " " + toStr(n.Name, 0, options, debugInfo, conf) + " "
			lqp += termList(n.Terms, 0, " ", options, debugInfo, conf) + conf.RPAREN()
		}

	case *Pragma:
		terms := termList(n.Terms, 0, " ", options, debugInfo, conf)
		lqp += ind + conf.LPAREN() + conf.Kw("pragma") + " :" + conf.Uname(n.Name) + " " + terms + conf.RPAREN()

	case *Primitive:
		if len(n.Terms) > 4 {
			lqp += ind + conf.LPAREN() + conf.Kw("primitive") + " :" + conf.Uname(n.Name) + "\n"
			lqp += relTermList(n.Terms, indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
		} else {
			lqp += ind + conf.LPAREN() + conf.Kw("primitive") + " :" + conf.Uname(n.Name) + " "
			lqp += relTermList(n.Terms, 0, " ", options, debugInfo, conf) + conf.RPAREN()
		}

	case *RelAtom:
		if len(n.Terms) > 4 {
			lqp += ind + conf.LPAREN() + conf.Kw("relatom") + " :" + n.Name + "\n"
			lqp += relTermList(n.Terms, indentLevel+1, "\n", options, debugInfo, conf) + conf.RPAREN()
		} else {
			lqp += ind + conf.LPAREN() + conf.Kw("relatom") + " :" + n.Name + " "
			lqp += relTermList(n.Terms, 0, " ", options, debugInfo, conf) + conf.RPAREN()
		}

	case *Cast:
		lqp += ind + conf.LPAREN() + conf.Kw("cast") + " " +
			toStr(n.Input, 0, options, debugInfo, conf) + " " +
			toStr(n.Result, 0, options, debugInfo, conf) + conf.RPAREN()

	case *Var:
		lqp += ind + conf.Uname(n.Name)

	case *Value:
		lqp += valueToStr(n.Value, indentLevel, options, debugInfo, conf)

	case *SpecializedValue:
		lqp += "#" + toStr(n.Value, 0, options, make(map[string]string), conf)

	case *Attribute:
		argsStr := valueList(n.Args, 0, " ", options, debugInfo, conf)
		space := ""
		if argsStr != "" {
			space = " "
		}
		lqp += ind + conf.LPAREN() + conf.Kw("attribute") + " :" + n.Name + space + argsStr + conf.RPAREN()

	case *RelationId:
		name := idToName(options, debugInfo, n)
		lqp += ind + conf.Uname(name)

	case *Write:
		lqp += toStr(n.WriteType, indentLevel, options, debugInfo, conf)

	case *Define:
		lqp += ind + conf.LPAREN() + conf.Kw("define") + "\n" +
			toStr(n.Fragment, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Undefine:
		lqp += ind + conf.LPAREN() + conf.Kw("undefine") + " " +
			toStr(n.FragmentId, 0, options, debugInfo, conf) + conf.RPAREN()

	case *Context:
		lqp += ind + conf.LPAREN() + conf.Kw("context") + " " +
			relationIdList(n.Relations, 0, " ", options, debugInfo, conf) + conf.RPAREN()

	case *Sync:
		lqp += ind + conf.LPAREN() + conf.Kw("sync") + " " +
			fragmentIdList(n.Fragments, 0, " ", options, debugInfo, conf) + conf.RPAREN()

	case *FragmentId:
		lqp += ind + ":" + conf.Uname(string(n.Id))

	case *Read:
		lqp += toStr(n.ReadType, indentLevel, options, debugInfo, conf)

	case *Demand:
		lqp += ind + conf.LPAREN() + conf.Kw("demand") + " " +
			toStr(n.RelationId, 0, options, debugInfo, conf) + conf.RPAREN()

	case *Output:
		nameStr := ""
		if n.Name != nil && *n.Name != "" {
			nameStr = ":" + conf.Uname(*n.Name) + " "
		}
		lqp += ind + conf.LPAREN() + conf.Kw("output") + " " + nameStr +
			toStr(n.RelationId, 0, options, debugInfo, conf) + conf.RPAREN()

	case *Export:
		lqp += ind + conf.LPAREN() + conf.Kw("export") + "\n" +
			toStr(n.Config, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *ExportCSVConfig:
		lqp += ind + conf.LPAREN() + conf.Kw("export_csv_config") + "\n"

		pathValue := n.Path
		if !hasOption(options, PRINT_CSV_FILENAME) {
			pathValue = "<hidden filename>"
		}
		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("path") + " " +
			valueToStr(pathValue, 0, options, debugInfo, conf) + conf.RPAREN() + "\n"

		lqp += ind + conf.SIND() + conf.LPAREN() + conf.Kw("columns") + " " +
			exportCSVColumnList(n.DataColumns, 0, " ", options, debugInfo, conf) + conf.RPAREN() + "\n"

		configDict := make(map[string]interface{})
		if n.PartitionSize != nil {
			configDict["partition_size"] = *n.PartitionSize
		} else {
			configDict["partition_size"] = 0
		}
		if n.Compression != nil {
			configDict["compression"] = *n.Compression
		} else {
			configDict["compression"] = ""
		}
		if n.SyntaxHeaderRow != nil {
			configDict["syntax_header_row"] = *n.SyntaxHeaderRow
		} else {
			configDict["syntax_header_row"] = 1
		}
		if n.SyntaxMissingString != nil {
			configDict["syntax_missing_string"] = *n.SyntaxMissingString
		} else {
			configDict["syntax_missing_string"] = ""
		}
		if n.SyntaxDelim != nil {
			configDict["syntax_delim"] = *n.SyntaxDelim
		} else {
			configDict["syntax_delim"] = ","
		}
		if n.SyntaxQuotechar != nil {
			configDict["syntax_quotechar"] = *n.SyntaxQuotechar
		} else {
			configDict["syntax_quotechar"] = "\""
		}
		if n.SyntaxEscapechar != nil {
			configDict["syntax_escapechar"] = *n.SyntaxEscapechar
		} else {
			configDict["syntax_escapechar"] = "\\"
		}

		lqp += configDictToStr(configDict, indentLevel+1, options, conf)
		lqp += conf.RPAREN()

	case *ExportCSVColumn:
		lqp += ind + conf.LPAREN() + conf.Kw("column") + " " +
			valueToStr(n.ColumnName, 0, options, debugInfo, conf) + " " +
			toStr(n.ColumnData, 0, options, debugInfo, conf) + conf.RPAREN()

	case *Abort:
		nameStr := ""
		if n.Name != nil && *n.Name != "" {
			nameStr = ":" + conf.Uname(*n.Name) + " "
		}
		lqp += ind + conf.LPAREN() + conf.Kw("abort") + " " + nameStr +
			toStr(n.RelationId, 0, options, debugInfo, conf) + conf.RPAREN()

	case *WhatIf:
		branchStr := ""
		if n.Branch != nil && *n.Branch != "" {
			branchStr = ":" + conf.Uname(*n.Branch) + " "
		}
		lqp += ind + conf.LPAREN() + conf.Kw("what_if") + " " + branchStr +
			toStr(n.Epoch, indentLevel+1, options, debugInfo, conf) + conf.RPAREN()

	case *Epoch:
		epochContent := ""
		if len(n.Writes) > 0 {
			epochContent += conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("writes") + "\n"
			epochContent += writeList(n.Writes, indentLevel+2, "\n", options, debugInfo, conf)
			epochContent += conf.RPAREN() + "\n"
		}
		if len(n.Reads) > 0 {
			epochContent += conf.Indentation(indentLevel+1) + conf.LPAREN() + conf.Kw("reads") + "\n"
			epochContent += readList(n.Reads, indentLevel+2, "\n", options, debugInfo, conf)
			epochContent += conf.RPAREN() + "\n"
		}
		lqp += ind + conf.LPAREN() + conf.Kw("epoch") + "\n" + epochContent + conf.RPAREN()

	case *Fragment:
		lqp += fragmentToStr(n, indentLevel, debugInfo, options)

	default:
		panic(fmt.Sprintf("toStr not implemented for %T", node))
	}

	return lqp
}

func valueToStr(value interface{}, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)

	switch v := value.(type) {
	case *Value:
		// Unwrap Value and recurse on its ValueData
		return valueToStr(v.Value, indentLevel, options, debugInfo, conf)
	case string:
		// Escape string (for config values and other raw strings)
		escaped := strings.ReplaceAll(v, "\\", "\\\\")
		escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
		return ind + "\"" + escaped + "\""
	case StringValue:
		// Escape string (for StringValue types)
		escaped := strings.ReplaceAll(string(v), "\\", "\\\\")
		escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
		return ind + "\"" + escaped + "\""
	case int:
		return ind + fmt.Sprintf("%d", v)
	case int64:
		return ind + fmt.Sprintf("%d", v)
	case Int64Value:
		return ind + fmt.Sprintf("%d", int64(v))
	case Float64Value:
		if math.IsInf(float64(v), 0) {
			return ind + "inf"
		}
		if math.IsNaN(float64(v)) {
			return ind + "nan"
		}
		// If the float is a whole number, we add a trailing zero
		// to bring to parity with Julia and Python.
		if float64(v) == float64(int64(v)) {
			return ind + fmt.Sprintf("%.1f", float64(v))
		}
		return ind + fmt.Sprintf("%v", float64(v))
	case *UInt128Value:
		return ind + "0x" + v.Value.Text(16)
	case *Int128Value:
		return ind + v.Value.String() + "i128"
	case *MissingValue:
		return ind + "missing"
	case *DecimalValue:
		// Format decimal with proper scale
		// Convert Decimal to string representation
		decStr := v.Value.Coefficient.String()
		if v.Value.Sign != 0 {
			decStr = "-" + decStr
		}

		// Insert decimal point Scale digits from the end
		scale := int(v.Scale)
		if scale > 0 && scale < len(decStr) {
			// Insert decimal point at the correct position
			pos := len(decStr) - scale
			decStr = decStr[:pos] + "." + decStr[pos:]
		} else if scale >= len(decStr) {
			// Need to pad with leading zeros
			zerosNeeded := scale - len(decStr)
			decStr = "0." + strings.Repeat("0", zerosNeeded) + decStr
		}
		// If scale == 0, no decimal point needed

		return ind + decStr + "d" + fmt.Sprintf("%d", v.Precision)
	case *DateValue:
		return ind + conf.LPAREN() + conf.Kw("date") + " " +
			fmt.Sprintf("%d %d %d", v.Value.Year(), v.Value.Month(), v.Value.Day()) + conf.RPAREN()
	case *DateTimeValue:
		return ind + conf.LPAREN() + conf.Kw("datetime") + " " +
			fmt.Sprintf("%d %d %d %d %d %d %d",
				v.Value.Year(), v.Value.Month(), v.Value.Day(),
				v.Value.Hour(), v.Value.Minute(), v.Value.Second(),
				v.Value.Nanosecond()/1000) + conf.RPAREN()
	case *BooleanValue:
		if v.Value {
			return ind + "true"
		}
		return ind + "false"
	default:
		return ind + fmt.Sprintf("%v", v)
	}
}

func typeToStr(t *Type, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	if len(t.Parameters) == 0 {
		return conf.TypeAnno(t.TypeName.String())
	}

	result := conf.LPAREN() + conf.TypeAnno(t.TypeName.String()) + " "
	params := make([]string, len(t.Parameters))
	for i, p := range t.Parameters {
		params[i] = valueToStr(p, 0, options, debugInfo, conf)
	}
	result += strings.Join(params, " ")
	result += conf.RPAREN()
	return result
}

func varsToStr(vars []*Binding, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(vars))
	for i, binding := range vars {
		parts[i] = conf.Uname(binding.Var.Name) + conf.TypeAnno("::") + typeToStr(binding.Type, 0, options, debugInfo, conf)
	}
	return strings.Join(parts, " ")
}

func termListToStr(terms []Term, indentLevel int, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	ind := conf.Indentation(indentLevel)

	if len(terms) == 0 {
		return ind + conf.LPAREN() + conf.Kw("terms") + conf.RPAREN()
	}

	return ind + conf.LPAREN() + conf.Kw("terms") + " " +
		termList(terms, 0, " ", options, debugInfo, conf) + conf.RPAREN()
}

func idToName(options map[string]bool, debugInfo map[string]string, rid *RelationId) string {
	if !hasOption(options, PRINT_NAMES) {
		return rid.Id.String()
	}
	if len(debugInfo) == 0 {
		return rid.Id.String()
	}
	if name, ok := debugInfo[rid.Id.String()]; ok {
		return ":" + name
	}
	return rid.Id.String()
}

// Helper functions for list formatting
func declarationList(items []Declaration, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func constructList(items []Construct, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func instructionList(items []Instruction, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func formulaList(items []Formula, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func relTermList(items []RelTerm, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func termList(items []Term, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func valueList(items []*Value, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func attributeList(items []*Attribute, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func abstractionList(items []*Abstraction, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func relationIdList(items []*RelationId, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func fragmentIdList(items []*FragmentId, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func writeList(items []*Write, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func readList(items []*Read, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}

func exportCSVColumnList(items []*ExportCSVColumn, indentLevel int, delim string, options map[string]bool, debugInfo map[string]string, conf StyleConfig) string {
	parts := make([]string, len(items))
	for i, item := range items {
		parts[i] = toStr(item, indentLevel, options, debugInfo, conf)
	}
	return strings.Join(parts, delim)
}
