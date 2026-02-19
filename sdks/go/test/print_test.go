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

// TestPrintBinaryFiles reads binary files, prints them, and compares with expected output.
// Go pretty-printer output is written to sdks/go/test/lqp_pretty_output/ for inspection.
func TestPrintBinaryFiles(t *testing.T) {
	testDir, err := filepath.Abs(".")
	if err != nil {
		t.Fatalf("Failed to get test directory: %v", err)
	}

	repoRoot := filepath.Join(testDir, "..", "..", "..")

	binDir := filepath.Join(repoRoot, "tests", "bin")
	expectedDir := filepath.Join(repoRoot, "tests", "pretty")
	outputDir := filepath.Join(testDir, "lqp_pretty_output")

	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		t.Fatalf("Failed to create output directory: %v", err)
	}

	entries, err := os.ReadDir(binDir)
	if err != nil {
		t.Fatalf("Failed to read bin directory: %v", err)
	}

	for _, entry := range entries {
		if !strings.HasSuffix(entry.Name(), ".bin") {
			continue
		}

		t.Run(entry.Name(), func(t *testing.T) {
			binPath := filepath.Join(binDir, entry.Name())
			data, err := os.ReadFile(binPath)
			if err != nil {
				t.Fatalf("Failed to read binary file %s: %v", entry.Name(), err)
			}

			transaction := &pb.Transaction{}
			if err = proto.Unmarshal(data, transaction); err != nil {
				t.Fatalf("Failed to unmarshal binary file %s: %v", entry.Name(), err)
			}

			printed := lqp.ProgramToStr(transaction)

			// Write output for inspection
			outName := strings.Replace(entry.Name(), ".bin", ".lqp", 1)
			outPath := filepath.Join(outputDir, outName)
			if err := os.WriteFile(outPath, []byte(printed), 0o644); err != nil {
				t.Fatalf("Failed to write output file %s: %v", outName, err)
			}

			// Compare against expected snapshot
			expectedPath := filepath.Join(expectedDir, outName)
			expectedData, err := os.ReadFile(expectedPath)
			if err != nil {
				t.Fatalf("Failed to read expected output file %s: %v", outName, err)
			}

			if printed != string(expectedData) {
				t.Errorf("Output mismatch for %s\n\nExpected:\n%s\n\nGot:\n%s", entry.Name(), string(expectedData), printed)
			}
		})
	}
}
