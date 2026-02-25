package test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	lqp "logical-query-protocol/src"
	pb "logical-query-protocol/src/lqp/v1"

	"google.golang.org/protobuf/proto"
)

// TestBasicParsing tests simple transaction parsing
func TestBasicParsing(t *testing.T) {
	input := `
(transaction
  (epoch
    (writes)
    (reads)))
`
	result, _, err := lqp.Parse(input)
	if err != nil {
		t.Fatalf("Failed to parse basic transaction: %v", err)
	}
	if result == nil {
		t.Fatal("Parse returned nil result")
	}
	if len(result.Epochs) != 1 {
		t.Errorf("Expected 1 epoch, got %d", len(result.Epochs))
	}
}

// TestParseLQPFiles parses all LQP files and compares against binary snapshots
func TestParseLQPFiles(t *testing.T) {
	// Get the repository root directory (go up two levels from test directory)
	testDir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("Failed to get test directory: %v", err)
	}

	// Go up to the repository root (from go/test to repo root)
	repoRoot := filepath.Join(testDir, "..", "..")

	lqpDir := filepath.Join(repoRoot, "python-tools", "tests", "test_files", "lqp")
	binDir := filepath.Join(repoRoot, "python-tools", "tests", "test_files", "bin")

	// Read all .lqp files
	entries, err := os.ReadDir(lqpDir)
	if err != nil {
		t.Fatalf("Failed to read LQP directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".lqp") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			// Read LQP file
			lqpPath := filepath.Join(lqpDir, entry.Name())
			content, err := os.ReadFile(lqpPath)
			if err != nil {
				t.Fatalf("Failed to read LQP file %s: %v", entry.Name(), err)
			}

			// Parse the LQP file
			result, _, err := lqp.Parse(string(content))
			if err != nil {
				t.Fatalf("Failed to parse LQP file %s: %v", entry.Name(), err)
			}
			if result == nil {
				t.Fatalf("Parse returned nil for %s", entry.Name())
			}

			// Serialize to binary
			generatedBinary, err := proto.Marshal(result)
			if err != nil {
				t.Fatalf("Failed to marshal parsed result for %s: %v", entry.Name(), err)
			}

			// Read expected binary
			binName := strings.Replace(entry.Name(), ".lqp", ".bin", 1)
			binPath := filepath.Join(binDir, binName)
			expectedBinary, err := os.ReadFile(binPath)
			if err != nil {
				t.Logf("Warning: No binary snapshot found for %s, skipping binary comparison", entry.Name())
				return
			}

			// Compare binaries
			if string(generatedBinary) != string(expectedBinary) {
				// If binaries don't match exactly, parse both and compare via pretty-print
				// (protobuf serialization can vary in field order, especially for maps/repeated fields)
				expectedTransaction := &pb.Transaction{}
				if err := proto.Unmarshal(expectedBinary, expectedTransaction); err != nil {
					t.Fatalf("Failed to unmarshal expected binary for %s: %v", entry.Name(), err)
				}

				// Compare via pretty-print since debug_info ordering may vary
				generatedPretty := lqp.ProgramToStr(result)
				expectedPretty := lqp.ProgramToStr(expectedTransaction)
				if generatedPretty != expectedPretty {
					t.Errorf("Parsed result does not match expected for %s\n\nParsed:\n%s\n\nExpected:\n%s", entry.Name(), generatedPretty, expectedPretty)
				}
			}
		})
	}
}
