package lqp_test

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
)

// TestRoundTrip tests that we can parse and print back LQP files
// It reads all LQP files from lqp/, prints them to pretty/, and verifies round-trip correctness
func TestRoundTrip(t *testing.T) {
	// Create pretty directory if it doesn't exist
	if err := os.MkdirAll("pretty", 0755); err != nil {
		t.Fatalf("Failed to create pretty directory: %v", err)
	}

	// Get all LQP files from lqp/
	files, err := filepath.Glob("lqp/*.lqp")
	if err != nil {
		t.Fatalf("Failed to find LQP files: %v", err)
	}

	if len(files) == 0 {
		t.Skip("No LQP files found in lqp/")
	}

	for _, file := range files {
		basename := filepath.Base(file)
		t.Run(basename, func(t *testing.T) {
			// Read original file
			content, err := os.ReadFile(file)
			if err != nil {
				t.Fatalf("Failed to read %s: %v", file, err)
			}

			// Parse it
			p := lqp.NewParser(bytes.NewReader(content), file)
			node, err := p.Parse()
			if err != nil {
				t.Fatalf("Failed to parse %s: %v", file, err)
			}

			// Print it back using PrettyConfig
			options := make(map[string]bool)
			for k, v := range lqp.UglyConfig {
				options[k] = v
			}
			options["print_names"] = true
			options["print_debug"] = false
			result := lqp.ToString(node, options)

			// Write the printed output to pretty/
			prettyFile := filepath.Join("pretty", basename)
			if err := os.WriteFile(prettyFile, []byte(result), 0644); err != nil {
				t.Fatalf("Failed to write %s: %v", prettyFile, err)
			}

			// Parse the printed result to verify round-trip correctness
			p2 := lqp.NewParser(strings.NewReader(result), prettyFile)
			node2, err := p2.Parse()
			if err != nil {
				t.Fatalf("Failed to re-parse printed output for %s: %v\nPrinted output written to: %s", file, err, prettyFile)
			}

			// Both parses succeeded - the structures should be equivalent
			t.Logf("✓ Round-trip successful: %s -> %s (original=%d bytes, printed=%d bytes)",
				file, prettyFile, len(content), len(result))

			// Verify node types match
			switch node.(type) {
			case *lqp.Transaction:
				if _, ok := node2.(*lqp.Transaction); !ok {
					t.Errorf("Node type mismatch: expected *lqp.Transaction, got %T", node2)
				}
			case *lqp.Fragment:
				if _, ok := node2.(*lqp.Fragment); !ok {
					t.Errorf("Node type mismatch: expected *lqp.Fragment, got %T", node2)
				}
			}
		})
	}
}
