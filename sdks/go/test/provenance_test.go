package test

import (
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

func TestProvenanceSpanOrdering(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	for path, span := range provenance {
		if span.Start.Offset > span.Stop.Offset {
			t.Errorf("Bad span at path %q: start %d > end %d",
				path, span.Start.Offset, span.Stop.Offset)
		}
		if span.Start.Line > span.Stop.Line {
			t.Errorf("Bad line ordering at path %q: start %d > end %d",
				path, span.Start.Line, span.Stop.Line)
		}
	}
}
