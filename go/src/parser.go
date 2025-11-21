package lqp

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"math"
	"math/big"
	"strconv"
	"strings"
	"time"
)

// Parser data structure
type Parser struct {
	lex     *Lexer
	file    string
	current Token
	peek    Token

	// Debug info tracking
	idToDebugInfo     map[*FragmentId]map[*RelationId]string
	currentFragmentId *FragmentId
}

func NewParser(r io.Reader, file string) *Parser {
	return &Parser{
		lex:           NewLexer(r, file),
		file:          file,
		idToDebugInfo: make(map[*FragmentId]map[*RelationId]string),
	}
}

func (p *Parser) nextToken() Token {
	if p.peek.Type != 0 {
		p.current = p.peek
		p.peek = Token{}
	} else {
		p.current = p.lex.Next()
	}
	return p.current
}

func (p *Parser) peekToken() Token {
	if p.peek.Type == 0 {
		p.peek = p.lex.Next()
	}
	return p.peek
}

func (p *Parser) expect(typ TokenType) error {
	tok := p.nextToken()
	if tok.Type != typ {
		return fmt.Errorf("%s:%d:%d: expected %s, got %s (%s)",
			p.file, tok.Line, tok.Column, typ, tok.Type, tok.Value)
	}
	return nil
}

func (p *Parser) expectSymbol(expected string) error {
	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != expected {
		return fmt.Errorf("%s:%d:%d: expected '%s', got %s (%s)",
			p.file, tok.Line, tok.Column, expected, tok.Type, tok.Value)
	}
	return nil
}

// -----------------------------------------------------------------
// Entry points

func ParseLQP(r io.Reader, file string) (LqpNode, error) {
	parser := NewParser(r, file)
	return parser.Parse()
}

func (p *Parser) Parse() (LqpNode, error) {
	// Expect opening '('
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected 'transaction' or 'fragment', got %s", tok.Value)
	}

	switch tok.Value {
	case "transaction":
		return p.parseTransaction(tok)
	case "fragment":
		return p.parseFragment(tok)
	default:
		return nil, fmt.Errorf("expected 'transaction' or 'fragment', got '%s'", tok.Value)
	}
}

// -----------------------------------------------------------------
// Recursive descent-style parser.

// Recursive descent was used because:
// 1. Lark (our Python parser generator) is not in Go
// 2. goyacc (Go's inbuilt parser) is not well maintained
// 3. S-expression syntax is amenable to recursive descent.

func (p *Parser) parseTransaction(tok Token) (*Transaction, error) {
	var configure *Configure
	var sync *Sync
	var epochs []*Epoch

	// Parse optional configure and epochs
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		if next.Type != TokenLParen {
			return nil, fmt.Errorf("expected '(' or ')', got %s", next.Type)
		}
		p.nextToken() // consume '('

		tok := p.nextToken()
		if tok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol, got %s", tok.Type)
		}

		switch tok.Value {
		case "configure":
			config, err := p.parseConfigure(tok)
			if err != nil {
				return nil, err
			}
			configure = config
		case "sync":
			s, err := p.parseSync(tok)
			if err != nil {
				return nil, err
			}
			sync = s
		case "epoch":
			epoch, err := p.parseEpoch(tok)
			if err != nil {
				return nil, err
			}
			epochs = append(epochs, epoch)
		default:
			return nil, fmt.Errorf("unexpected element in transaction: %s", tok.Value)
		}
	}

	// Default configure if not provided
	if configure == nil {
		configure = &Configure{
			SemanticsVersion: 0,
			IvmConfig: &IVMConfig{
				Level: MaintenanceLevelOff,
			},
		}
	}

	return &Transaction{
		Epochs:    epochs,
		Configure: configure,
		Sync:      sync,
	}, nil
}
func (p *Parser) parseSync(tok Token) (*Sync, error) {
	fragIds, err := p.parseFragmentIdList()

	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Sync{
		Fragments: fragIds,
	}, nil
}

func (p *Parser) parseConfigure(tok Token) (*Configure, error) {
	// Parse config_dict
	configDict, err := p.parseConfigDict()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	// Construct Configure from config dict
	semanticsVersion := int64(0)
	if sv, ok := configDict["semantics_version"]; ok {
		if val, ok := sv.Value.(Int64Value); ok {
			semanticsVersion = int64(val)
		}
	}

	maintenanceLevel := MaintenanceLevelOff
	if ml, ok := configDict["ivm.maintenance_level"]; ok {
		if val, ok := ml.Value.(StringValue); ok {
			switch strings.ToUpper(string(val)) {
			case "OFF":
				maintenanceLevel = MaintenanceLevelOff
			case "AUTO":
				maintenanceLevel = MaintenanceLevelAuto
			case "ALL":
				maintenanceLevel = MaintenanceLevelAll
			case "UNSPECIFIED":
				maintenanceLevel = MaintenanceLevelUnspecified
			}
		}
	}

	return &Configure{
		SemanticsVersion: semanticsVersion,
		IvmConfig: &IVMConfig{
			Level: maintenanceLevel,
		},
	}, nil
}

func (p *Parser) parseConfigDict() (map[string]*Value, error) {
	if err := p.expect(TokenLBrace); err != nil {
		return nil, err
	}

	result := make(map[string]*Value)

	for {
		next := p.peekToken()
		if next.Type == TokenRBrace {
			p.nextToken()
			break
		}

		// Parse key (:SYMBOL)
		if err := p.expect(TokenColon); err != nil {
			return nil, err
		}
		keyTok := p.nextToken()
		if keyTok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol for config key, got %s", keyTok.Type)
		}

		// Parse value
		val, err := p.parseValue()
		if err != nil {
			return nil, err
		}

		result[keyTok.Value] = val
	}

	return result, nil
}

func (p *Parser) parseEpoch(tok Token) (*Epoch, error) {
	var writes []*Write
	var reads []*Read

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		if next.Type != TokenLParen {
			return nil, fmt.Errorf("expected '(' or ')', got %s", next.Type)
		}
		p.nextToken() // consume '('

		tok := p.nextToken()
		if tok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol, got %s", tok.Type)
		}

		switch tok.Value {
		case "writes":
			ws, err := p.parseWrites()
			if err != nil {
				return nil, err
			}
			writes = ws
		case "reads":
			rs, err := p.parseReads()
			if err != nil {
				return nil, err
			}
			reads = rs
		default:
			return nil, fmt.Errorf("unexpected element in epoch: %s", tok.Value)
		}
	}

	return &Epoch{
		Writes: writes,
		Reads:  reads,
	}, nil
}

func (p *Parser) parseWrites() ([]*Write, error) {
	var writes []*Write

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		w, err := p.parseWrite()
		if err != nil {
			return nil, err
		}
		writes = append(writes, w)
	}

	return writes, nil
}

func (p *Parser) parseWrite() (*Write, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected write type, got %s", tok.Type)
	}

	var writeType WriteType

	switch tok.Value {
	case "define":
		// Expect (fragment ...)
		if err := p.expect(TokenLParen); err != nil {
			return nil, err
		}
		fragTok := p.nextToken()
		if fragTok.Type != TokenSymbol || fragTok.Value != "fragment" {
			return nil, fmt.Errorf("expected 'fragment', got %s", fragTok.Value)
		}
		frag, err := p.parseFragment(fragTok)
		if err != nil {
			return nil, err
		}
		writeType = &Define{

			Fragment: frag.(*Fragment),
		}
	case "undefine":
		fragId, err := p.parseFragmentId()
		if err != nil {
			return nil, err
		}
		writeType = &Undefine{

			FragmentId: fragId,
		}
	case "context":
		relIds, err := p.parseRelationIdList()
		if err != nil {
			return nil, err
		}
		writeType = &Context{

			Relations: relIds,
		}
	default:
		return nil, fmt.Errorf("unknown write type: %s", tok.Value)
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Write{

		WriteType: writeType,
	}, nil
}

func (p *Parser) parseReads() ([]*Read, error) {
	var reads []*Read

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		r, err := p.parseRead()
		if err != nil {
			return nil, err
		}
		reads = append(reads, r)
	}

	return reads, nil
}

func (p *Parser) parseRead() (*Read, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected read type, got %s", tok.Type)
	}

	var readType ReadType
	var err error

	switch tok.Value {
	case "demand":
		relId, err := p.parseRelationId()
		if err != nil {
			return nil, err
		}
		readType = &Demand{

			RelationId: relId,
		}
	case "output":
		var name *string
		var relId *RelationId

		// Check if first element is a name or relation_id
		next := p.peekToken()
		if next.Type == TokenColon {
			// Could be name or relation_id
			p.nextToken() // consume ':'
			nameTok := p.nextToken()
			if nameTok.Type != TokenSymbol && nameTok.Type != TokenNumber {
				return nil, fmt.Errorf("expected symbol or number after ':'")
			}

			// Check if there's another relation_id (meaning the first was a name)
			next2 := p.peekToken()
			if next2.Type == TokenColon || next2.Type == TokenNumber {
				// This is a name, parse the relation_id next
				nameStr := nameTok.Value
				name = &nameStr
				relId, err = p.parseRelationId()
				if err != nil {
					return nil, err
				}
			} else {
				// This is a relation_id (no name)
				relId, err = p.parseRelationIdFromToken(nameTok)
				if err != nil {
					return nil, err
				}
			}
		} else {
			return nil, fmt.Errorf("expected ':' for output name/relation_id")
		}

		readType = &Output{

			Name:       name,
			RelationId: relId,
		}
	case "export":
		config, err := p.parseExportCSVConfig()
		if err != nil {
			return nil, err
		}
		readType = &Export{

			Config: config,
		}
	case "abort":
		var name *string
		var relId *RelationId

		// Similar logic to output
		next := p.peekToken()
		if next.Type == TokenColon {
			p.nextToken() // consume ':'
			nameTok := p.nextToken()
			if nameTok.Type != TokenSymbol && nameTok.Type != TokenNumber {
				return nil, fmt.Errorf("expected symbol or number after ':'")
			}

			// Check if there's another relation_id (meaning the first was a name)
			next2 := p.peekToken()
			if next2.Type == TokenColon || next2.Type == TokenNumber {
				// This is a name, parse the relation_id next
				nameStr := nameTok.Value
				name = &nameStr
				relId, err = p.parseRelationId()
				if err != nil {
					return nil, err
				}
			} else {
				// This is a relation_id (no name)
				relId, err = p.parseRelationIdFromToken(nameTok)
				if err != nil {
					return nil, err
				}
			}
		}

		readType = &Abort{

			Name:       name,
			RelationId: relId,
		}
	default:
		return nil, fmt.Errorf("unknown read type: %s", tok.Value)
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Read{
		ReadType: readType,
	}, nil
}

func (p *Parser) parseExportCSVConfig() (*ExportCSVConfig, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "export_csv_config" {
		return nil, fmt.Errorf("expected 'export_csv_config', got %s", tok.Value)
	}

	// Parse path
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	if err := p.expectSymbol("path"); err != nil {
		return nil, err
	}
	pathTok := p.nextToken()
	if pathTok.Type != TokenString {
		return nil, fmt.Errorf("expected string for path, got %s", pathTok.Type)
	}
	path := pathTok.Value
	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	// Parse columns
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	if err := p.expectSymbol("columns"); err != nil {
		return nil, err
	}

	var columns []*ExportCSVColumn
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		col, err := p.parseExportColumn()
		if err != nil {
			return nil, err
		}
		columns = append(columns, col)
	}

	// Parse optional config dict
	configDict := make(map[string]*Value)
	next := p.peekToken()
	if next.Type == TokenLBrace {
		var err error
		configDict, err = p.parseConfigDict()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	// Build ExportCSVConfig from dict
	config := &ExportCSVConfig{
		Path:        path,
		DataColumns: columns,
	}

	// Process config options
	for k, v := range configDict {
		switch k {
		case "partition_size":
			if iv, ok := v.Value.(Int64Value); ok {
				val := int64(iv)
				config.PartitionSize = &val
			}
		case "compression":
			if sv, ok := v.Value.(StringValue); ok {
				val := string(sv)
				config.Compression = &val
			}
		case "syntax_header_row":
			if bv, ok := v.Value.(*BooleanValue); ok {
				config.SyntaxHeaderRow = &bv.Value
			}
		case "syntax_missing_string":
			if sv, ok := v.Value.(StringValue); ok {
				val := string(sv)
				config.SyntaxMissingString = &val
			}
		case "syntax_delim":
			if sv, ok := v.Value.(StringValue); ok {
				val := string(sv)
				config.SyntaxDelim = &val
			}
		case "syntax_quotechar":
			if sv, ok := v.Value.(StringValue); ok {
				val := string(sv)
				config.SyntaxQuotechar = &val
			}
		case "syntax_escapechar":
			if sv, ok := v.Value.(StringValue); ok {
				val := string(sv)
				config.SyntaxEscapechar = &val
			}
		}
	}

	return config, nil
}

func (p *Parser) parseExportColumn() (*ExportCSVColumn, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "column" {
		return nil, fmt.Errorf("expected 'column', got %s", tok.Value)
	}

	nameTok := p.nextToken()
	if nameTok.Type != TokenString {
		return nil, fmt.Errorf("expected string for column name, got %s", nameTok.Type)
	}

	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &ExportCSVColumn{

		ColumnName: nameTok.Value,
		ColumnData: relId,
	}, nil
}

func (p *Parser) parseFragment(tok Token) (LqpNode, error) {
	// Parse fragment_id
	fragId, err := p.parseFragmentId()
	if err != nil {
		return nil, err
	}

	// Set current fragment for debug info tracking
	p.currentFragmentId = fragId
	if _, ok := p.idToDebugInfo[fragId]; !ok {
		p.idToDebugInfo[fragId] = make(map[*RelationId]string)
	}

	// Parse declarations
	var declarations []Declaration
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		decl, err := p.parseDeclaration()
		if err != nil {
			return nil, err
		}
		declarations = append(declarations, decl)
	}

	// Create debug info - convert map key
	debugMap := make(map[string]string)
	for relId, name := range p.idToDebugInfo[fragId] {
		debugMap[relId.Id.String()] = name
	}
	debugInfo := &DebugInfo{

		IdToOrigName: debugMap,
	}

	p.currentFragmentId = nil

	return &Fragment{

		Id:           fragId,
		Declarations: declarations,
		DebugInfo:    debugInfo,
	}, nil
}

func (p *Parser) parseFragmentId() (*FragmentId, error) {
	if err := p.expect(TokenColon); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected symbol for fragment id, got %s", tok.Type)
	}

	return &FragmentId{
		Id: []byte(tok.Value),
	}, nil
}

func (p *Parser) parseFragmentIdList() ([]*FragmentId, error) {
	var fragIds []*FragmentId

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			break
		}

		fragId, err := p.parseFragmentId()
		if err != nil {
			return nil, err
		}
		fragIds = append(fragIds, fragId)
	}

	return fragIds, nil
}

func (p *Parser) parseRelationIdList() ([]*RelationId, error) {
	var relIds []*RelationId

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			break
		}

		relId, err := p.parseRelationId()
		if err != nil {
			return nil, err
		}
		relIds = append(relIds, relId)
	}

	return relIds, nil
}

func (p *Parser) parseDeclaration() (Declaration, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected declaration type, got %s", tok.Type)
	}

	switch tok.Value {
	case "def":
		return p.parseDef()
	case "algorithm":
		return p.parseAlgorithm()
	case "functional_dependency":
		return p.parseFunctionalDependency()
	default:
		return nil, fmt.Errorf("unknown declaration type: %s", tok.Value)
	}
}

func (p *Parser) parseDef() (*Def, error) {
	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	if arity != 0 {
		return nil, fmt.Errorf("def should not have value arity")
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Def{
		Name:  relId,
		Body:  abs,
		Attrs: attrs,
	}, nil
}

func (p *Parser) parseFunctionalDependency() (*FunctionalDependency, error) {
	// Parse the guard abstraction
	guard, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	if arity != 0 {
		return nil, fmt.Errorf("functional_dependency guard should not have value arity")
	}

	// Parse (keys ...)
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	if err := p.expectSymbol("keys"); err != nil {
		return nil, err
	}

	var keys []*Var
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		if next.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol for key variable, got %s", next.Type)
		}

		tok := p.nextToken()
		keys = append(keys, &Var{
			Name: tok.Value,
		})
	}

	// Parse (values ...)
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	if err := p.expectSymbol("values"); err != nil {
		return nil, err
	}

	var values []*Var
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		if next.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol for value variable, got %s", next.Type)
		}

		tok := p.nextToken()
		values = append(values, &Var{
			Name: tok.Value,
		})
	}

	// Expect closing paren for functional_dependency
	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &FunctionalDependency{

		Guard:  guard,
		Keys:   keys,
		Values: values,
	}, nil
}

func (p *Parser) parseAlgorithm() (*Algorithm, error) {
	var globals []*RelationId

	// Parse global relation ids until we hit a script
	for {
		next := p.peekToken()
		if next.Type == TokenLParen {
			// Check if it's a script
			p.nextToken() // consume '('
			scriptTok := p.nextToken()
			if scriptTok.Value == "script" {
				// It's the script, parse it
				script, err := p.parseScript(scriptTok)
				if err != nil {
					return nil, err
				}

				if err := p.expect(TokenRParen); err != nil {
					return nil, err
				}

				// Consume closing paren for algorithm
				if err := p.expect(TokenRParen); err != nil {
					return nil, err
				}

				return &Algorithm{

					Global: globals,
					Body:   script,
				}, nil
			}
			return nil, fmt.Errorf("expected script in algorithm, got %s", scriptTok.Value)
		}

		// Parse relation id
		relId, err := p.parseRelationId()
		if err != nil {
			return nil, err
		}
		globals = append(globals, relId)
	}
}

func (p *Parser) parseScript(tok Token) (*Script, error) {

	var constructs []Construct

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			break
		}

		construct, err := p.parseConstruct()
		if err != nil {
			return nil, err
		}
		constructs = append(constructs, construct)
	}

	return &Script{

		Constructs: constructs,
	}, nil
}

func (p *Parser) parseConstruct() (Construct, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected construct type, got %s", tok.Type)
	}

	switch tok.Value {
	case "loop":
		return p.parseLoop()
	case "assign":
		return p.parseAssign()
	case "upsert":
		return p.parseUpsert()
	case "break":
		return p.parseBreak()
	case "monoid":
		return p.parseMonoidDef()
	case "monus":
		return p.parseMonusDef()
	default:
		return nil, fmt.Errorf("unknown construct type: %s", tok.Value)
	}
}

func (p *Parser) parseLoop() (*Loop, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	if err := p.expectSymbol("init"); err != nil {
		return nil, err
	}

	var init []Instruction
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		instr, err := p.parseInstruction()
		if err != nil {
			return nil, err
		}
		init = append(init, instr)
	}

	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}
	scriptTok := p.nextToken()
	if scriptTok.Type != TokenSymbol || scriptTok.Value != "script" {
		return nil, fmt.Errorf("expected 'script', got %s", scriptTok.Value)
	}

	script, err := p.parseScript(scriptTok)
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Loop{

		Init: init,
		Body: script,
	}, nil
}

func (p *Parser) parseInstruction() (Instruction, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected instruction type, got %s", tok.Type)
	}

	switch tok.Value {
	case "assign":
		return p.parseAssign()
	case "upsert":
		return p.parseUpsert()
	case "break":
		return p.parseBreak()
	case "monoid":
		return p.parseMonoidDef()
	case "monus":
		return p.parseMonusDef()
	default:
		return nil, fmt.Errorf("unknown instruction type: %s", tok.Value)
	}
}

func (p *Parser) parseAssign() (*Assign, error) {
	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	if arity != 0 {
		return nil, fmt.Errorf("assign should not have value arity")
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Assign{
		Name:  relId,
		Body:  abs,
		Attrs: attrs,
	}, nil
}

func (p *Parser) parseUpsert() (*Upsert, error) {
	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Upsert{

		ValueArity: arity,
		Name:       relId,
		Body:       abs,
		Attrs:      attrs,
	}, nil
}

func (p *Parser) parseBreak() (*Break, error) {
	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	if arity != 0 {
		return nil, fmt.Errorf("break should not have value arity")
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Break{

		Name:  relId,
		Body:  abs,
		Attrs: attrs,
	}, nil
}

func (p *Parser) parseMonoidDef() (*MonoidDef, error) {
	monoid, err := p.parseMonoid()
	if err != nil {
		return nil, err
	}

	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &MonoidDef{

		ValueArity: arity,
		Monoid:     monoid,
		Name:       relId,
		Body:       abs,
		Attrs:      attrs,
	}, nil
}

func (p *Parser) parseMonusDef() (*MonusDef, error) {
	monoid, err := p.parseMonoid()
	if err != nil {
		return nil, err
	}

	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	abs, arity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	var attrs []*Attribute
	next := p.peekToken()
	if next.Type == TokenLParen {
		attrs, err = p.parseAttrs()
		if err != nil {
			return nil, err
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &MonusDef{

		ValueArity: arity,
		Monoid:     monoid,
		Name:       relId,
		Body:       abs,
		Attrs:      attrs,
	}, nil
}

func (p *Parser) parseMonoid() (Monoid, error) {
	typeTok := p.nextToken()
	if typeTok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected type name for monoid, got %s", typeTok.Type)
	}

	if err := p.expect(TokenBinding); err != nil {
		return nil, err
	}

	opTok := p.nextToken()
	if opTok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected monoid operator, got %s", opTok.Type)
	}

	switch opTok.Value {
	case "OR":
		return &OrMonoid{}, nil
	case "MIN":
		typ, err := p.makeType(typeTok.Value)
		if err != nil {
			return nil, err
		}
		return &MinMonoid{Type: typ}, nil
	case "MAX":
		typ, err := p.makeType(typeTok.Value)
		if err != nil {
			return nil, err
		}
		return &MaxMonoid{Type: typ}, nil
	case "SUM":
		typ, err := p.makeType(typeTok.Value)
		if err != nil {
			return nil, err
		}
		return &SumMonoid{Type: typ}, nil
	default:
		return nil, fmt.Errorf("unknown monoid operator: %s", opTok.Value)
	}
}

func (p *Parser) makeType(name string) (*Type, error) {
	var typeName TypeName
	switch strings.ToUpper(name) {
	case "STRING":
		typeName = TypeNameString
	case "INT":
		typeName = TypeNameInt
	case "FLOAT":
		typeName = TypeNameFloat
	case "UINT128":
		typeName = TypeNameUInt128
	case "INT128":
		typeName = TypeNameInt128
	case "DATE":
		typeName = TypeNameDate
	case "DATETIME":
		typeName = TypeNameDateTime
	case "MISSING":
		typeName = TypeNameMissing
	case "DECIMAL":
		typeName = TypeNameDecimal
	case "BOOLEAN":
		typeName = TypeNameBoolean
	case "BOOL":
		typeName = TypeNameBoolean
	default:
		return nil, fmt.Errorf("unknown type name: %s", name)
	}

	return &Type{

		TypeName:   typeName,
		Parameters: nil,
	}, nil
}

func (p *Parser) parseAbstraction() (*Abstraction, int64, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, 0, err
	}

	// Parse bindings
	bindings, arity, err := p.parseBindings()
	if err != nil {
		return nil, 0, err
	}

	// Parse formula
	formula, err := p.parseFormula()
	if err != nil {
		return nil, 0, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, 0, err
	}

	return &Abstraction{

		Vars:  bindings,
		Value: formula,
	}, arity, nil
}

func (p *Parser) parseBindings() ([]*Binding, int64, error) {
	if err := p.expect(TokenLBracket); err != nil {
		return nil, 0, err
	}

	var leftBindings []*Binding
	var rightBindings []*Binding

	// Parse left bindings
	for {
		next := p.peekToken()
		if next.Type == TokenPipe || next.Type == TokenRBracket {
			break
		}

		binding, err := p.parseBinding()
		if err != nil {
			return nil, 0, err
		}
		leftBindings = append(leftBindings, binding)
	}

	next := p.peekToken()
	if next.Type == TokenPipe {
		p.nextToken()

		// Parse right bindings
		for {
			next := p.peekToken()
			if next.Type == TokenRBracket {
				break
			}

			binding, err := p.parseBinding()
			if err != nil {
				return nil, 0, err
			}
			rightBindings = append(rightBindings, binding)
		}
	}

	if err := p.expect(TokenRBracket); err != nil {
		return nil, 0, err
	}

	allBindings := append(leftBindings, rightBindings...)
	arity := int64(len(rightBindings))

	return allBindings, arity, nil
}

func (p *Parser) parseBinding() (*Binding, error) {
	nameTok := p.nextToken()
	if nameTok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected symbol for binding name, got %s", nameTok.Type)
	}

	if err := p.expect(TokenBinding); err != nil {
		return nil, err
	}

	typ, err := p.parseType()
	if err != nil {
		return nil, err
	}

	return &Binding{
		Var: &Var{
			Name: nameTok.Value,
		},
		Type: typ,
	}, nil
}

func (p *Parser) parseType() (*Type, error) {
	next := p.peekToken()

	if next.Type == TokenLParen {
		// Parameterized type: (TYPE_NAME value*)
		p.nextToken() // consume '('

		nameTok := p.nextToken()
		if nameTok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected type name, got %s", nameTok.Type)
		}

		var params []*Value
		for {
			next := p.peekToken()
			if next.Type == TokenRParen {
				p.nextToken()
				break
			}

			val, err := p.parseValue()
			if err != nil {
				return nil, err
			}
			params = append(params, val)
		}

		typeName, err := p.parseTypeName(nameTok.Value)
		if err != nil {
			return nil, err
		}

		return &Type{

			TypeName:   typeName,
			Parameters: params,
		}, nil
	}

	// Simple type: TYPE_NAME
	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected type name, got %s", tok.Type)
	}

	typeName, err := p.parseTypeName(tok.Value)
	if err != nil {
		return nil, err
	}

	return &Type{

		TypeName:   typeName,
		Parameters: nil,
	}, nil
}

func (p *Parser) parseTypeName(name string) (TypeName, error) {
	switch strings.ToUpper(name) {
	case "STRING":
		return TypeNameString, nil
	case "INT":
		return TypeNameInt, nil
	case "FLOAT":
		return TypeNameFloat, nil
	case "UINT128":
		return TypeNameUInt128, nil
	case "INT128":
		return TypeNameInt128, nil
	case "DATE":
		return TypeNameDate, nil
	case "DATETIME":
		return TypeNameDateTime, nil
	case "MISSING":
		return TypeNameMissing, nil
	case "DECIMAL":
		return TypeNameDecimal, nil
	case "BOOLEAN", "BOOL":
		return TypeNameBoolean, nil
	default:
		return TypeNameUnspecified, fmt.Errorf("unknown type name: %s", name)
	}
}

func (p *Parser) parseFormula() (Formula, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return nil, fmt.Errorf("expected formula type, got %s", tok.Type)
	}

	switch tok.Value {
	case "exists":
		return p.parseExists()
	case "reduce":
		return p.parseReduce()
	case "and":
		return p.parseConjunction()
	case "or":
		return p.parseDisjunction()
	case "not":
		return p.parseNot()
	case "ffi":
		return p.parseFFI()
	case "atom":
		return p.parseAtom()
	case "relatom":
		return p.parseRelAtom()
	case "primitive":
		return p.parseRawPrimitive()
	case "pragma":
		return p.parsePragma()
	case "cast":
		return p.parseCast()
	case "true":
		if err := p.expect(TokenRParen); err != nil {
			return nil, err
		}
		return &Conjunction{Args: nil}, nil
	case "false":
		if err := p.expect(TokenRParen); err != nil {
			return nil, err
		}
		return &Disjunction{Args: nil}, nil
	case "=":
		return p.parseEq()
	case "<":
		return p.parseLt()
	case "<=":
		return p.parseLtEq()
	case ">":
		return p.parseGt()
	case ">=":
		return p.parseGtEq()
	case "+":
		return p.parseAdd()
	case "-":
		return p.parseMinus()
	case "*":
		return p.parseMultiply()
	case "/":
		return p.parseDivide()
	default:
		return nil, fmt.Errorf("unknown formula type: %s", tok.Value)
	}
}

func (p *Parser) parseExists() (*Exists, error) {
	bindings, arity, err := p.parseBindings()
	if err != nil {
		return nil, err
	}

	if arity != 0 {
		return nil, fmt.Errorf("exists should not have value arity")
	}

	formula, err := p.parseFormula()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Exists{

		Body: &Abstraction{

			Vars:  bindings,
			Value: formula,
		},
	}, nil
}

func (p *Parser) parseReduce() (*Reduce, error) {
	op, opArity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	body, bodyArity, err := p.parseAbstraction()
	if err != nil {
		return nil, err
	}

	if opArity != 0 || bodyArity != 0 {
		return nil, fmt.Errorf("abstractions in reduce should not have value arities")
	}

	terms, err := p.parseTerms()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Reduce{

		Op:    op,
		Body:  body,
		Terms: terms,
	}, nil
}

func (p *Parser) parseConjunction() (*Conjunction, error) {
	var args []Formula

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		formula, err := p.parseFormula()
		if err != nil {
			return nil, err
		}
		args = append(args, formula)
	}

	return &Conjunction{

		Args: args,
	}, nil
}

func (p *Parser) parseDisjunction() (*Disjunction, error) {
	var args []Formula

	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		formula, err := p.parseFormula()
		if err != nil {
			return nil, err
		}
		args = append(args, formula)
	}

	return &Disjunction{

		Args: args,
	}, nil
}

func (p *Parser) parseNot() (*Not, error) {
	formula, err := p.parseFormula()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Not{

		Arg: formula,
	}, nil
}

func (p *Parser) parseFFI() (*FFI, error) {
	name, err := p.parseName()
	if err != nil {
		return nil, err
	}

	args, err := p.parseArgs()
	if err != nil {
		return nil, err
	}

	terms, err := p.parseTerms()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &FFI{

		Name:  name,
		Args:  args,
		Terms: terms,
	}, nil
}

func (p *Parser) parseAtom() (*Atom, error) {
	relId, err := p.parseRelationId()
	if err != nil {
		return nil, err
	}

	var terms []Term
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		term, err := p.parseTerm()
		if err != nil {
			return nil, err
		}
		terms = append(terms, term)
	}

	return &Atom{

		Name:  relId,
		Terms: terms,
	}, nil
}

func (p *Parser) parseRelAtom() (*RelAtom, error) {
	name, err := p.parseName()
	if err != nil {
		return nil, err
	}

	var terms []RelTerm
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		term, err := p.parseRelTerm()
		if err != nil {
			return nil, err
		}
		terms = append(terms, term)
	}

	return &RelAtom{

		Name:  name,
		Terms: terms,
	}, nil
}

func (p *Parser) parseRawPrimitive() (*Primitive, error) {
	name, err := p.parseName()
	if err != nil {
		return nil, err
	}

	var terms []RelTerm
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		term, err := p.parseRelTerm()
		if err != nil {
			return nil, err
		}
		terms = append(terms, term)
	}

	return &Primitive{

		Name:  name,
		Terms: terms,
	}, nil
}

func (p *Parser) parsePragma() (*Pragma, error) {
	name, err := p.parseName()
	if err != nil {
		return nil, err
	}

	var terms []Term
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		term, err := p.parseTerm()
		if err != nil {
			return nil, err
		}
		terms = append(terms, term)
	}

	return &Pragma{

		Name:  name,
		Terms: terms,
	}, nil
}

func (p *Parser) parseCast() (*Cast, error) {
	input, err := p.parseTerm()
	if err != nil {
		return nil, err
	}

	result, err := p.parseTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Cast{

		Input:  input,
		Result: result,
	}, nil
}

// Primitive operations (desugared)
func (p *Parser) parseEq() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_eq",
		Terms: []RelTerm{term1, term2},
	}, nil
}

func (p *Parser) parseLt() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_lt_monotype",
		Terms: []RelTerm{term1, term2},
	}, nil
}

func (p *Parser) parseLtEq() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_lt_eq_monotype",
		Terms: []RelTerm{term1, term2},
	}, nil
}

func (p *Parser) parseGt() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_gt_monotype",
		Terms: []RelTerm{term1, term2},
	}, nil
}

func (p *Parser) parseGtEq() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_gt_eq_monotype",
		Terms: []RelTerm{term1, term2},
	}, nil
}

func (p *Parser) parseAdd() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term3, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_add_monotype",
		Terms: []RelTerm{term1, term2, term3},
	}, nil
}

func (p *Parser) parseMinus() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term3, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_subtract_monotype",
		Terms: []RelTerm{term1, term2, term3},
	}, nil
}

func (p *Parser) parseMultiply() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term3, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_multiply_monotype",
		Terms: []RelTerm{term1, term2, term3},
	}, nil
}

func (p *Parser) parseDivide() (*Primitive, error) {
	term1, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term2, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	term3, err := p.parseRelTerm()
	if err != nil {
		return nil, err
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	return &Primitive{

		Name:  "rel_primitive_divide_monotype",
		Terms: []RelTerm{term1, term2, term3},
	}, nil
}

func (p *Parser) parseName() (string, error) {
	if err := p.expect(TokenColon); err != nil {
		return "", err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol {
		return "", fmt.Errorf("expected symbol for name, got %s", tok.Type)
	}

	return tok.Value, nil
}

func (p *Parser) parseArgs() ([]*Abstraction, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "args" {
		return nil, fmt.Errorf("expected 'args', got %s", tok.Value)
	}

	var args []*Abstraction
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		abs, _, err := p.parseAbstraction()
		if err != nil {
			return nil, err
		}
		args = append(args, abs)
	}

	return args, nil
}

func (p *Parser) parseTerms() ([]Term, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "terms" {
		return nil, fmt.Errorf("expected 'terms', got %s", tok.Value)
	}

	var terms []Term
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		term, err := p.parseTerm()
		if err != nil {
			return nil, err
		}
		terms = append(terms, term)
	}

	return terms, nil
}

func (p *Parser) parseRelTerm() (RelTerm, error) {
	next := p.peekToken()

	if next.Type == TokenSpecialized {
		// SpecializedValue
		p.nextToken() // consume '#'

		val, err := p.parseValue()
		if err != nil {
			return nil, err
		}

		return &SpecializedValue{

			Value: val,
		}, nil
	}

	term, err := p.parseTerm()
	if err != nil {
		return nil, err
	}
	return term.(RelTerm), nil
}

func (p *Parser) parseTerm() (Term, error) {
	next := p.peekToken()

	if next.Type == TokenSymbol {
		tok := p.nextToken()
		return &Var{
			Name: tok.Value,
		}, nil
	}

	return p.parseValue()
}

func (p *Parser) parseValue() (*Value, error) {
	tok := p.nextToken()

	switch tok.Type {
	case TokenString:
		return &Value{

			Value: StringValue(tok.Value),
		}, nil

	case TokenNumber:
		val, err := strconv.ParseInt(tok.Value, 10, 64)
		if err != nil {
			return nil, fmt.Errorf("invalid number: %s", tok.Value)
		}
		return &Value{

			Value: Int64Value(val),
		}, nil

	case TokenFloat:
		var val float64
		switch tok.Value {
		case "inf":
			val = math.Inf(1)
		case "nan":
			val = math.NaN()
		default:
			var err error
			val, err = strconv.ParseFloat(tok.Value, 64)
			if err != nil {
				return nil, fmt.Errorf("invalid float: %s", tok.Value)
			}
		}
		return &Value{

			Value: Float64Value(val),
		}, nil

	case TokenUInt128:
		val := new(big.Int)
		_, ok := val.SetString(tok.Value[2:], 16)
		if !ok {
			return nil, fmt.Errorf("invalid uint128: %s", tok.Value)
		}
		return &Value{

			Value: &UInt128Value{

				Value: val,
			},
		}, nil

	case TokenInt128:
		valStr := tok.Value[:len(tok.Value)-4]
		val := new(big.Int)
		_, ok := val.SetString(valStr, 10)
		if !ok {
			return nil, fmt.Errorf("invalid int128: %s", tok.Value)
		}
		return &Value{

			Value: &Int128Value{

				Value: val,
			},
		}, nil

	case TokenDecimal:
		parts := strings.Split(tok.Value, "d")
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid decimal format: %s", tok.Value)
		}

		decParts := strings.Split(parts[0], ".")
		if len(decParts) != 2 {
			return nil, fmt.Errorf("invalid decimal format: %s", tok.Value)
		}

		scale := int32(len(decParts[1]))
		precision, err := strconv.ParseInt(parts[1], 10, 32)
		if err != nil {
			return nil, fmt.Errorf("invalid decimal precision: %s", tok.Value)
		}

		coefficient := new(big.Int)
		_, ok := coefficient.SetString(decParts[0]+decParts[1], 10)
		if !ok {
			return nil, fmt.Errorf("invalid decimal coefficient: %s", tok.Value)
		}

		sign := 0
		if coefficient.Sign() < 0 {
			sign = 1
			coefficient.Abs(coefficient)
		}

		return &Value{

			Value: &DecimalValue{

				Precision: int32(precision),
				Scale:     scale,
				Value: &Decimal{
					Sign:        sign,
					Coefficient: coefficient,
					Exponent:    -int(scale),
				},
			},
		}, nil

	case TokenBoolean:
		val := tok.Value == "true"
		return &Value{

			Value: &BooleanValue{

				Value: val,
			},
		}, nil

	case TokenMissing:
		return &Value{

			Value: &MissingValue{},
		}, nil

	// Date or datetime
	case TokenLParen:
		typeTok := p.nextToken()
		if typeTok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected date or datetime, got %s", typeTok.Type)
		}

		switch typeTok.Value {
		case "date":
			return p.parseDate()
		case "datetime":
			return p.parseDateTime()
		default:
			return nil, fmt.Errorf("unexpected value type: %s", typeTok.Value)
		}

	default:
		return nil, fmt.Errorf("unexpected token for value: %s (%s)", tok.Type, tok.Value)
	}
}

func (p *Parser) parseDate() (*Value, error) {
	// (date YYYY MM DD)
	yearTok := p.nextToken()
	monthTok := p.nextToken()
	dayTok := p.nextToken()

	year, err := strconv.Atoi(yearTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid year: %s", yearTok.Value)
	}

	month, err := strconv.Atoi(monthTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid month: %s", monthTok.Value)
	}

	day, err := strconv.Atoi(dayTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid day: %s", dayTok.Value)
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	date := time.Date(year, time.Month(month), day, 0, 0, 0, 0, time.UTC)

	return &Value{

		Value: &DateValue{

			Value: date,
		},
	}, nil
}

func (p *Parser) parseDateTime() (*Value, error) {
	// (datetime YYYY MM DD HH MM SS [MS])
	yearTok := p.nextToken()
	monthTok := p.nextToken()
	dayTok := p.nextToken()
	hourTok := p.nextToken()
	minuteTok := p.nextToken()
	secondTok := p.nextToken()

	year, err := strconv.Atoi(yearTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid year: %s", yearTok.Value)
	}

	month, err := strconv.Atoi(monthTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid month: %s", monthTok.Value)
	}

	day, err := strconv.Atoi(dayTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid day: %s", dayTok.Value)
	}

	hour, err := strconv.Atoi(hourTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid hour: %s", hourTok.Value)
	}

	minute, err := strconv.Atoi(minuteTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid minute: %s", minuteTok.Value)
	}

	second, err := strconv.Atoi(secondTok.Value)
	if err != nil {
		return nil, fmt.Errorf("invalid second: %s", secondTok.Value)
	}

	// Check for optional microsecond
	microsecond := 0
	next := p.peekToken()
	if next.Type == TokenNumber {
		microTok := p.nextToken()
		microsecond, err = strconv.Atoi(microTok.Value)
		if err != nil {
			return nil, fmt.Errorf("invalid microsecond: %s", microTok.Value)
		}
	}

	if err := p.expect(TokenRParen); err != nil {
		return nil, err
	}

	dt := time.Date(year, time.Month(month), day, hour, minute, second, microsecond*1000, time.UTC)

	return &Value{

		Value: &DateTimeValue{

			Value: dt,
		},
	}, nil
}

func (p *Parser) parseAttrs() ([]*Attribute, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "attrs" {
		return nil, fmt.Errorf("expected 'attrs', got %s", tok.Value)
	}

	var attrs []*Attribute
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		attr, err := p.parseAttribute()
		if err != nil {
			return nil, err
		}
		attrs = append(attrs, attr)
	}

	return attrs, nil
}

func (p *Parser) parseAttribute() (*Attribute, error) {
	if err := p.expect(TokenLParen); err != nil {
		return nil, err
	}

	tok := p.nextToken()
	if tok.Type != TokenSymbol || tok.Value != "attribute" {
		return nil, fmt.Errorf("expected 'attribute', got %s", tok.Value)
	}

	name, err := p.parseName()
	if err != nil {
		return nil, err
	}

	var args []*Value
	for {
		next := p.peekToken()
		if next.Type == TokenRParen {
			p.nextToken()
			break
		}

		val, err := p.parseValue()
		if err != nil {
			return nil, err
		}
		args = append(args, val)
	}

	return &Attribute{

		Name: name,
		Args: args,
	}, nil
}

func (p *Parser) parseRelationId() (*RelationId, error) {
	next := p.peekToken()

	// RelationId can be a number directly
	if next.Type == TokenNumber {
		tok := p.nextToken()
		return p.parseRelationIdFromToken(tok)
	}

	// RelationId can be a symbol (prefixed with :)
	if next.Type == TokenColon {
		p.nextToken() // Consume :
		tok := p.nextToken()
		if tok.Type != TokenSymbol {
			return nil, fmt.Errorf("expected symbol for relation id, got %s", tok.Type)
		}
		return p.parseRelationIdFromToken(tok)
	}

	return nil, fmt.Errorf("expected relation id, got %s", next.Type)
}

// parseRelationIdFromToken parses a relation ID from an already-consumed token
func (p *Parser) parseRelationIdFromToken(tok Token) (*RelationId, error) {
	if tok.Type != TokenSymbol && tok.Type != TokenNumber {
		return nil, fmt.Errorf("expected symbol or number for relation id, got %s", tok.Type)
	}

	if tok.Type == TokenNumber {
		// Numeric relation_id
		id := new(big.Int)
		_, ok := id.SetString(tok.Value, 10)
		if !ok {
			return nil, fmt.Errorf("invalid relation id: %s", tok.Value)
		}
		return &RelationId{
			Id: id,
		}, nil
	}

	// Symbolic relation_id
	return p.makeRelationIdFromSymbol(tok.Value), nil
}

func (p *Parser) makeRelationIdFromSymbol(symbol string) *RelationId {
	// Hash the symbol to get the ID (first 16 hex chars of SHA-256)
	hash := sha256.Sum256([]byte(symbol))
	hashStr := hex.EncodeToString(hash[:])
	idVal := new(big.Int)
	idVal.SetString(hashStr[:16], 16)

	relId := &RelationId{

		Id: idVal,
	}

	// Store debug info
	if p.currentFragmentId != nil {
		if p.idToDebugInfo[p.currentFragmentId] == nil {
			p.idToDebugInfo[p.currentFragmentId] = make(map[*RelationId]string)
		}
		p.idToDebugInfo[p.currentFragmentId][relId] = symbol
	}

	return relId
}
