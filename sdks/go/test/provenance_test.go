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

func findSpanByType(provenance map[int]lqp.Span, typeName string) (lqp.Span, bool) {
	for _, span := range provenance {
		if span.TypeName == typeName {
			return span, true
		}
	}
	return lqp.Span{}, false
}

func TestProvenanceRootTransaction(t *testing.T) {
	_, provenance, err := lqp.Parse(simpleInput)
	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	span, ok := findSpanByType(provenance, "Transaction")
	if !ok {
		t.Fatal("No Transaction span found in provenance")
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

	for offset, span := range provenance {
		if span.Start.Offset > span.Stop.Offset {
			t.Errorf("Bad span at offset %d: start %d > end %d",
				offset, span.Start.Offset, span.Stop.Offset)
		}
		if span.Start.Line > span.Stop.Line {
			t.Errorf("Bad line ordering at offset %d: start %d > end %d",
				offset, span.Start.Line, span.Stop.Line)
		}
	}
}
