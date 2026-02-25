package test

import (
	"strings"
	"testing"

	lqp "github.com/RelationalAI/logical-query-protocol/sdks/go/src"
)

const simpleInput = `(transaction
  (epoch
    (writes)
    (reads)))
`

func TestProvenanceRootTransaction(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	span, ok := provenance[""]
	if !ok {
		t.Fatal("Root path '' not found in provenance")
	}
	if span.Start.Offset != 0 {
		t.Errorf("Expected root start offset 0, got %d", span.Start.Offset)
	}
	if span.Start.Line != 1 {
		t.Errorf("Expected root start line 1, got %d", span.Start.Line)
	}
	if span.Start.Column != 1 {
		t.Errorf("Expected root start column 1, got %d", span.Start.Column)
	}
}

func TestProvenanceEpoch(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// epochs = field 1, index 0
	span, ok := provenance["1,0"]
	if !ok {
		t.Fatal("Epoch path '1,0' not found in provenance")
	}
	if span.Start.Line != 2 {
		t.Errorf("Expected epoch start line 2, got %d", span.Start.Line)
	}
}

func TestProvenanceWrites(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// epochs[0].writes = field 1 within Epoch
	span, ok := provenance["1,0,1"]
	if !ok {
		t.Fatal("Writes path '1,0,1' not found in provenance")
	}
	if span.Start.Line != 3 {
		t.Errorf("Expected writes start line 3, got %d", span.Start.Line)
	}
}

func TestProvenanceReads(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// epochs[0].reads = field 2 within Epoch
	span, ok := provenance["1,0,2"]
	if !ok {
		t.Fatal("Reads path '1,0,2' not found in provenance")
	}
	if span.Start.Line != 4 {
		t.Errorf("Expected reads start line 4, got %d", span.Start.Line)
	}
}

func TestProvenanceSpanCoversCorrectText(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	// Root transaction starts at offset 0
	rootSpan := provenance[""]
	if rootSpan.Start.Offset != 0 {
		t.Errorf("Expected root start offset 0, got %d", rootSpan.Start.Offset)
	}

	// Epoch span starts at '(' of '(epoch'
	epochSpan := provenance["1,0"]
	textAtEpoch := simpleInput[epochSpan.Start.Offset:]
	if !strings.HasPrefix(textAtEpoch, "(epoch") {
		t.Errorf("Expected text at epoch offset to start with '(epoch', got %q",
			textAtEpoch[:min(20, len(textAtEpoch))])
	}
}

func TestProvenanceSpanOrdering(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	for path, span := range provenance {
		if span.Start.Offset > span.End.Offset {
			t.Errorf("Bad span at path %q: start %d > end %d",
				path, span.Start.Offset, span.End.Offset)
		}
		if span.Start.Line > span.End.Line {
			t.Errorf("Bad line ordering at path %q: start %d > end %d",
				path, span.Start.Line, span.End.Line)
		}
	}
}

func TestProvenanceMultipleEpochs(t *testing.T) {
	input := `(transaction
  (epoch
    (writes)
    (reads))
  (epoch
    (writes)
    (reads)))
`
	_, provenance, err := lqp.Parse(input)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	span0, ok0 := provenance["1,0"]
	span1, ok1 := provenance["1,1"]
	if !ok0 {
		t.Fatal("First epoch path '1,0' not found")
	}
	if !ok1 {
		t.Fatal("Second epoch path '1,1' not found")
	}
	if span0.Start.Offset >= span1.Start.Offset {
		t.Errorf("Expected first epoch before second: %d >= %d",
			span0.Start.Offset, span1.Start.Offset)
	}
}
