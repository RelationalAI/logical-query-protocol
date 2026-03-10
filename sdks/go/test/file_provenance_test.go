package test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "github.com/RelationalAI/logical-query-protocol/sdks/go/src"
)

// lqpFiles returns all .lqp files in the tests/lqp directory.
func lqpFiles(t *testing.T) []string {
	t.Helper()
	root := repoRoot(t)
	dir := filepath.Join(root, "tests", "lqp")
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("Failed to read LQP directory: %v", err)
	}
	var files []string
	for _, e := range entries {
		if strings.HasSuffix(e.Name(), ".lqp") {
			files = append(files, filepath.Join(dir, e.Name()))
		}
	}
	return files
}

// lineOffsets returns 0-based byte offsets of the start of each 1-based line.
func lineOffsets(content string) []int {
	offsets := []int{0}
	for i, ch := range content {
		if ch == '\n' {
			offsets = append(offsets, i+1)
		}
	}
	return offsets
}

func TestFileProvenanceSpansValid(t *testing.T) {
	for _, file := range lqpFiles(t) {
		name := filepath.Base(file)
		t.Run(name, func(t *testing.T) {
			data, err := os.ReadFile(file)
			if err != nil {
				t.Fatalf("Failed to read %s: %v", name, err)
			}
			content := string(data)

			_, provenance, err := lqp.Parse(content)
			if err != nil {
				t.Fatalf("Failed to parse %s: %v", name, err)
			}
			if len(provenance) == 0 {
				t.Fatalf("No provenance entries for %s", name)
			}

			for offset, span := range provenance {
				if span.Start.Offset > span.Stop.Offset {
					t.Errorf("%s offset %d: start offset %d > end offset %d",
						name, offset, span.Start.Offset, span.Stop.Offset)
				}
				if span.Start.Offset < 0 || span.Start.Offset > len(content) {
					t.Errorf("%s offset %d: start offset %d out of range",
						name, offset, span.Start.Offset)
				}
				if span.Stop.Offset < 0 || span.Stop.Offset > len(content) {
					t.Errorf("%s offset %d: end offset %d out of range",
						name, offset, span.Stop.Offset)
				}
				if span.Start.Line < 1 {
					t.Errorf("%s offset %d: start line %d < 1",
						name, offset, span.Start.Line)
				}
				if span.Start.Column < 1 {
					t.Errorf("%s offset %d: start column %d < 1",
						name, offset, span.Start.Column)
				}
			}
		})
	}
}

func TestFileProvenanceRootSpansTransaction(t *testing.T) {
	for _, file := range lqpFiles(t) {
		name := filepath.Base(file)
		t.Run(name, func(t *testing.T) {
			data, err := os.ReadFile(file)
			if err != nil {
				t.Fatalf("Failed to read %s: %v", name, err)
			}
			content := string(data)

			_, provenance, err := lqp.Parse(content)
			if err != nil {
				t.Fatalf("Failed to parse %s: %v", name, err)
			}

			span, ok := findSpanByType(provenance, "Transaction")
			if !ok {
				t.Fatalf("%s: no Transaction span in provenance", name)
			}
			text := content[span.Start.Offset:span.Stop.Offset]
			if !strings.HasPrefix(text, "(transaction") {
				t.Errorf("%s: root span text starts with %q, expected '(transaction'",
					name, text[:min(30, len(text))])
			}
		})
	}
}

func TestFileProvenanceOffsetsMatchLineColumn(t *testing.T) {
	for _, file := range lqpFiles(t) {
		name := filepath.Base(file)
		t.Run(name, func(t *testing.T) {
			data, err := os.ReadFile(file)
			if err != nil {
				t.Fatalf("Failed to read %s: %v", name, err)
			}
			content := string(data)
			offsets := lineOffsets(content)

			_, provenance, err := lqp.Parse(content)
			if err != nil {
				t.Fatalf("Failed to parse %s: %v", name, err)
			}

			for offset, span := range provenance {
				loc := span.Start
				if loc.Line >= 1 && loc.Line <= len(offsets) {
					expected := offsets[loc.Line-1] + (loc.Column - 1)
					if loc.Offset != expected {
						t.Errorf("%s offset %d: offset %d != expected %d (line %d, col %d)",
							name, offset, loc.Offset, expected, loc.Line, loc.Column)
					}
				}
			}
		})
	}
}
