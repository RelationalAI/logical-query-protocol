package lqp_test

import (
	"bytes"
	"os"
	"testing"

	lqp "logical-query-protocol/src"
)

func TestPrintOuter(t *testing.T) {
	// Parse the outer.lqp file
	content, err := os.ReadFile("lqp/outer.lqp")
	if err != nil {
		t.Fatalf("Failed to read outer.lqp: %v", err)
	}

	p := lqp.NewParser(bytes.NewReader(content), "lqp/outer.lqp")
	node, err := p.Parse()
	if err != nil {
		t.Fatalf("Failed to parse outer.lqp: %v", err)
	}

	// Print it back out
	options := map[string]bool{
		"styled": false,
	}
	result := lqp.ToString(node, options)

	// Just verify we got some output
	if len(result) == 0 {
		t.Fatal("lqp.ToString produced empty output")
	}

	t.Logf("Printed output length: %d characters", len(result))
}

func TestPrintQ1Piece(t *testing.T) {
	// Parse the piece_of_q1.lqp file
	content, err := os.ReadFile("lqp/piece_of_q1.lqp")
	if err != nil {
		t.Fatalf("Failed to read piece_of_q1.lqp: %v", err)
	}

	p := lqp.NewParser(bytes.NewReader(content), "lqp/piece_of_q1.lqp")
	node, err := p.Parse()
	if err != nil {
		t.Fatalf("Failed to parse piece_of_q1.lqp: %v", err)
	}

	// Print it back out with styling
	options := map[string]bool{
		"styled": true,
	}
	result := lqp.ToString(node, options)

	// Just verify we got some output
	if len(result) == 0 {
		t.Fatal("lqp.ToString produced empty output")
	}

	t.Logf("Printed styled output length: %d characters", len(result))
}
